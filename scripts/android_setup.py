"""
SUVI Android Device Bridge Setup & Diagnostics Tool
Configures USB and Wireless ADB connections for Phone Calls, WhatsApp, and App Automation.
"""

import sys
import subprocess
import shutil

def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return res.stdout.strip(), res.stderr.strip(), res.returncode
    except Exception as e:
        return "", str(e), 1

def main():
    print("=" * 60)
    print("       SUVI (Smart Unified Voice Intelligence)")
    print("           Android Device Bridge Setup")
    print("=" * 60)

    # 1. Check ADB
    adb_path = shutil.which("adb")
    if not adb_path:
        print("\n[!] WARNING: 'adb' was not found in your system PATH.")
        print("    To install ADB on Windows:")
        print("    1. Download SDK Platform-Tools from:")
        print("       https://developer.android.com/tools/releases/platform-tools")
        print("    2. Extract to C:\\platform-tools")
        print("    3. Add C:\\platform-tools to your Windows PATH environment variable.\n")
        input("Press Enter once installed or to exit...")
        return

    print(f"\n[+] ADB found at: {adb_path}")

    # 2. Check connected devices
    stdout, _, _ = run_cmd("adb devices")
    print("\nConnected Devices Status:")
    print(stdout)

    lines = stdout.splitlines()[1:]
    devices = [l.split()[0] for l in lines if len(l.split()) >= 2 and l.split()[1] == "device"]

    if not devices:
        print("\n[!] No authorized Android devices detected.")
        print("Steps to connect your Android phone:")
        print("  1. On your phone: Settings -> About Phone -> Tap 'Build Number' 7 times.")
        print("  2. Go to Settings -> System / Developer Options.")
        print("  3. Enable 'USB Debugging'.")
        print("  4. Connect phone via USB cable.")
        print("  5. On your phone screen, check 'Always allow from this computer' and tap 'Allow'.")
        print("\nRun this setup tool again after allowing debugging.")
        input("\nPress Enter to exit...")
        return

    print(f"\n[+] Detected {len(devices)} active Android device(s): {', '.join(devices)}")

    # 3. Setup Wireless ADB Option
    print("\n--- Wireless ADB Setup ---")
    setup_wireless = input("Would you like to enable Wireless ADB so you don't need a USB cable? (y/n): ").strip().lower()
    if setup_wireless == 'y':
        print("\nConfiguring device for TCP/IP mode on port 5555...")
        out, err, code = run_cmd("adb tcpip 5555")
        if code == 0:
            print("[+] TCP/IP mode enabled!")
            print("Now find your phone's Wi-Fi IP address:")
            print("  (Settings -> Wi-Fi -> Your Network -> IP Address, e.g., 192.168.1.105)")
            phone_ip = input("Enter your phone's IP address: ").strip()
            if phone_ip:
                conn_out, _, _ = run_cmd(f"adb connect {phone_ip}:5555")
                print(f"[+] Result: {conn_out}")
                print("\nYou can now unplug the USB cable! SUVI will connect over your Wi-Fi.")
        else:
            print(f"[!] Failed to set tcpip mode: {err}")

    # 4. Diagnostics Test
    print("\n--- Diagnostic Tests ---")
    test_choice = input("Would you like to run a test call or test launch an app? (y/n): ").strip().lower()
    if test_choice == 'y':
        print("1. Test Phone Call")
        print("2. Test Launch WhatsApp")
        print("3. Query Battery Status")
        choice = input("Select option (1-3): ").strip()
        if choice == '1':
            num = input("Enter phone number to dial: ").strip()
            if num:
                run_cmd(f'adb shell am start -a android.intent.action.DIAL -d tel:{num}')
                print(f"[+] Sent dial intent for {num} to Android.")
        elif choice == '2':
            run_cmd('adb shell monkey -p com.whatsapp -c android.intent.category.LAUNCHER 1')
            print("[+] Sent launch intent for WhatsApp to Android.")
        elif choice == '3':
            batt, _, _ = run_cmd('adb shell dumpsys battery')
            print("\nBattery Information:")
            for l in batt.splitlines():
                if any(k in l for k in ["level", "scale", "status", "temperature"]):
                    print("  " + l.strip())

    print("\n" + "=" * 60)
    print("Android setup complete! SUVI is ready to control your phone.")
    print("=" * 60)

if __name__ == "__main__":
    main()
