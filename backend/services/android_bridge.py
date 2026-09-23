import shutil
import subprocess
import urllib.parse
from typing import Dict, Any, List, Optional
from backend.config import settings
from backend.security import sanitize_phone_number

class AndroidBridge:
    """Provides unified Android device connectivity via ADB (USB & Wireless) and Mobile Web Intents."""

    COMMON_ANDROID_PACKAGES = {
        "whatsapp": "com.whatsapp",
        "youtube": "com.google.android.youtube",
        "chrome": "com.android.chrome",
        "camera": "com.android.camera2",
        "settings": "com.android.settings",
        "maps": "com.google.android.apps.maps",
        "spotify": "com.spotify.music",
        "instagram": "com.instagram.android",
        "phone": "com.google.android.dialer",
        "messages": "com.google.android.apps.messaging",
        "telegram": "org.telegram.messenger"
    }

    def __init__(self):
        self.adb_bin = self._find_adb()

    def _find_adb(self) -> Optional[str]:
        """Locate ADB executable on system."""
        # Check configured path or standard PATH
        found = shutil.which(settings.ADB_PATH)
        if found:
            return found
        # Common Android SDK paths on Windows
        import os
        sdk_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"),
            r"C:\platform-tools\adb.exe"
        ]
        for p in sdk_paths:
            if os.path.exists(p):
                return p
        return None

    def is_adb_ready(self) -> bool:
        """Check if ADB is found on system."""
        return self.adb_bin is not None

    def run_adb_command(self, args: List[str]) -> Dict[str, Any]:
        """Execute arbitrary ADB shell command with device target."""
        if not self.adb_bin:
            return {
                "success": False,
                "error": "ADB (Android Debug Bridge) is not installed or not in PATH. See scripts/android_setup.py."
            }

        cmd = [self.adb_bin]
        if settings.ANDROID_DEVICE_IP:
            cmd.extend(["-s", settings.ANDROID_DEVICE_IP])
        cmd.extend(args)

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return {
                "success": res.returncode == 0,
                "output": res.stdout.strip(),
                "error": res.stderr.strip() if res.returncode != 0 else None
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "ADB command timed out."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_connected_devices(self) -> List[Dict[str, str]]:
        """List active connected Android devices."""
        if not self.adb_bin:
            return []
        try:
            res = subprocess.run([self.adb_bin, "devices"], capture_output=True, text=True, timeout=5)
            devices = []
            lines = res.stdout.strip().split("\n")[1:]
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    devices.append({"id": parts[0], "status": parts[1]})
            return devices
        except Exception:
            return []

    def connect_wireless(self, ip_port: str) -> Dict[str, Any]:
        """Connect to an Android device wirelessly via ADB (e.g. 192.168.1.105:5555)."""
        if not self.adb_bin:
            return {"success": False, "error": "ADB is not available."}
        res = self.run_adb_command(["connect", ip_port])
        if res["success"]:
            settings.ANDROID_DEVICE_IP = ip_port
        return res

    def initiate_phone_call(self, phone_number: str) -> Dict[str, Any]:
        """Initiate a phone call on Android or generate mobile dial intent."""
        clean_num = sanitize_phone_number(phone_number)
        if not clean_num:
            return {"success": False, "error": "Invalid phone number specified."}

        # Mobile Web intent link (for Android phone browser)
        tel_link = f"tel:{clean_num}"

        # If ADB connected, trigger direct Android system intent
        if self.is_adb_ready() and self.get_connected_devices():
            adb_res = self.run_adb_command([
                "shell", "am", "start",
                "-a", "android.intent.action.CALL",
                "-d", f"tel:{clean_num}"
            ])
            if adb_res["success"]:
                return {
                    "success": True,
                    "method": "adb",
                    "number": clean_num,
                    "message": f"Calling {clean_num} on connected Android phone."
                }

        # Fallback to direct dial intent URL
        return {
            "success": True,
            "method": "intent_url",
            "url": tel_link,
            "number": clean_num,
            "message": f"Ready to call {clean_num}. Tap to dial or connect ADB."
        }

    def send_whatsapp_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send a WhatsApp message via Android ADB intent or universal wa.me link."""
        clean_num = sanitize_phone_number(phone_number)
        encoded_msg = urllib.parse.quote(message)
        wa_url = f"https://api.whatsapp.com/send?phone={clean_num}&text={encoded_msg}" if clean_num else f"https://api.whatsapp.com/send?text={encoded_msg}"

        if self.is_adb_ready() and self.get_connected_devices():
            intent_url = f"whatsapp://send?phone={clean_num}&text={encoded_msg}" if clean_num else f"whatsapp://send?text={encoded_msg}"
            adb_res = self.run_adb_command([
                "shell", "am", "start",
                "-a", "android.intent.action.VIEW",
                "-d", intent_url
            ])
            if adb_res["success"]:
                return {
                    "success": True,
                    "method": "adb",
                    "message": f"Dispatched WhatsApp message to {clean_num or 'contact'} on Android."
                }

        return {
            "success": True,
            "method": "intent_url",
            "url": wa_url,
            "message": f"WhatsApp message prepared for {clean_num or 'recipient'}."
        }

    def launch_android_app(self, app_name: str) -> Dict[str, Any]:
        """Launch an Android application by name or package."""
        clean_name = app_name.lower().strip()
        package = self.COMMON_ANDROID_PACKAGES.get(clean_name, clean_name)

        if self.is_adb_ready() and self.get_connected_devices():
            adb_res = self.run_adb_command([
                "shell", "monkey",
                "-p", package,
                "-c", "android.intent.category.LAUNCHER",
                "1"
            ])
            if adb_res["success"]:
                return {"success": True, "message": f"Launched Android app: {app_name}"}

        return {
            "success": False,
            "error": f"Cannot launch '{app_name}' on Android: No active ADB device connected."
        }

    def get_android_battery(self) -> Dict[str, Any]:
        """Retrieve Android battery level via ADB."""
        if not self.is_adb_ready() or not self.get_connected_devices():
            return {"connected": False, "level": None}

        res = self.run_adb_command(["shell", "dumpsys", "battery"])
        if not res["success"]:
            return {"connected": False, "level": None}

        level = None
        for line in res["output"].split("\n"):
            if "level:" in line:
                try:
                    level = int(line.split(":")[1].strip())
                except Exception:
                    pass
        return {"connected": True, "level": level}

android_bridge = AndroidBridge()
