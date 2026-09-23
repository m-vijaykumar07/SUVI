import os
import sys
import subprocess
import shutil
import ctypes
from pathlib import Path
from typing import Dict, Any, List, Optional
import psutil
from PIL import ImageGrab
from backend.config import settings

class WindowsController:
    """Controls Windows OS operations, application launches, audio, and hardware telemetry."""

    # Common application mappings for fast resolution
    APP_ALIASES = {
        "chrome": ["chrome.exe", "google chrome"],
        "google chrome": ["chrome.exe"],
        "edge": ["msedge.exe", "microsoft edge"],
        "browser": ["msedge.exe", "chrome.exe"],
        "notepad": ["notepad.exe"],
        "calculator": ["calc.exe"],
        "calc": ["calc.exe"],
        "cmd": ["cmd.exe"],
        "terminal": ["wt.exe", "powershell.exe", "cmd.exe"],
        "powershell": ["powershell.exe"],
        "explorer": ["explorer.exe"],
        "files": ["explorer.exe"],
        "file manager": ["explorer.exe"],
        "task manager": ["taskmgr.exe"],
        "taskmgr": ["taskmgr.exe"],
        "paint": ["mspaint.exe"],
        "settings": ["ms-settings:"],
        "control panel": ["control.exe"],
        "vs code": ["code.cmd", "Code.exe"],
        "vscode": ["code.cmd", "Code.exe"],
        "code": ["code.cmd", "Code.exe"],
        "spotify": ["spotify.exe"],
        "word": ["winword.exe"],
        "excel": ["excel.exe"],
        "powerpoint": ["powerpnt.exe"],
        "discord": ["discord.exe"],
        "whatsapp": ["whatsapp.exe", "whatsapp:"],
        "camera": ["microsoft.windows.camera:"],
    }

    @staticmethod
    def get_system_telemetry() -> Dict[str, Any]:
        """Collect real-time CPU, RAM, Disk, and Battery hardware metrics."""
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_count = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        cpu_freq_current = round(cpu_freq.current, 1) if cpu_freq else 0

        # Memory metrics
        mem = psutil.virtual_memory()
        ram_percent = mem.percent
        ram_used_gb = round(mem.used / (1024 ** 3), 2)
        ram_total_gb = round(mem.total / (1024 ** 3), 2)

        # Disk metrics
        disk = psutil.disk_usage('C:\\')
        disk_percent = disk.percent
        disk_free_gb = round(disk.free / (1024 ** 3), 1)

        # Battery metrics
        battery = psutil.sensors_battery()
        battery_data = {
            "percent": battery.percent if battery else 100,
            "power_plugged": battery.power_plugged if battery else True,
            "has_battery": battery is not None
        }

        return {
            "status": "online",
            "cpu": {
                "percent": cpu_percent,
                "cores": cpu_count,
                "frequency_mhz": cpu_freq_current
            },
            "ram": {
                "percent": ram_percent,
                "used_gb": ram_used_gb,
                "total_gb": ram_total_gb
            },
            "disk": {
                "percent": disk_percent,
                "free_gb": disk_free_gb
            },
            "battery": battery_data,
            "os": "Windows"
        }

    @classmethod
    def launch_app(cls, app_name: str) -> Dict[str, Any]:
        """Launch any installed Windows application by name or alias."""
        clean_name = app_name.lower().strip()
        
        # Check alias table first
        target_execs = cls.APP_ALIASES.get(clean_name, [clean_name])

        for target in target_execs:
            # Protocol handler like ms-settings: or whatsapp:
            if ":" in target:
                try:
                    os.system(f'start {target}')
                    return {"success": True, "message": f"Launched {app_name} via Windows protocol."}
                except Exception as e:
                    continue

            # Standard executable in PATH
            if shutil.which(target):
                try:
                    subprocess.Popen([target], shell=True)
                    return {"success": True, "message": f"Successfully launched {app_name}."}
                except Exception as e:
                    pass

            # Try direct start command (Windows shell resolution)
            try:
                subprocess.Popen(f'start "" "{target}"', shell=True)
                return {"success": True, "message": f"Initiated launch of {app_name}."}
            except Exception:
                continue

        # Common directories search (Program Files, LocalAppData)
        search_dirs = [
            os.environ.get("ProgramFiles", "C:\\Program Files"),
            os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs"),
        ]

        for base_dir in search_dirs:
            if not os.path.exists(base_dir):
                continue
            for root, _, files in os.walk(base_dir):
                for file in files:
                    if file.lower().endswith(".exe") and clean_name in file.lower():
                        full_path = os.path.join(root, file)
                        try:
                            subprocess.Popen([full_path])
                            return {"success": True, "message": f"Found and launched {file}."}
                        except Exception as e:
                            return {"success": False, "error": str(e)}

        return {"success": False, "error": f"Could not locate application '{app_name}' on this system."}

    @staticmethod
    def adjust_volume(action: str, value: Optional[int] = None) -> Dict[str, Any]:
        """Adjust master volume or mute using Windows PowerShell / VBScript fallback."""
        action = action.lower()
        try:
            if action == "mute":
                # Toggle mute via PowerShell WScript.Shell SendKeys
                ps_cmd = "$w = New-Object -ComObject WScript.Shell; $w.SendKeys([char]173)"
                subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, check=True)
                return {"success": True, "message": "Volume muted/unmuted."}
            elif action == "up":
                # Volume up key
                ps_cmd = "$w = New-Object -ComObject WScript.Shell; for($i=0;$i -lt 5;$i++){$w.SendKeys([char]175)}"
                subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, check=True)
                return {"success": True, "message": "Volume increased."}
            elif action == "down":
                # Volume down key
                ps_cmd = "$w = New-Object -ComObject WScript.Shell; for($i=0;$i -lt 5;$i++){$w.SendKeys([char]174)}"
                subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, check=True)
                return {"success": True, "message": "Volume decreased."}
            else:
                return {"success": False, "error": f"Unknown volume action: {action}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to adjust volume: {str(e)}"}

    @staticmethod
    def take_screenshot() -> Dict[str, Any]:
        """Capture screenshot and save to captures directory."""
        try:
            import time
            timestamp = int(time.time())
            filename = f"screenshot_{timestamp}.png"
            filepath = settings.CAPTURES_DIR / filename
            
            img = ImageGrab.grab()
            img.save(str(filepath), "PNG")
            
            return {
                "success": True,
                "filename": filename,
                "path": str(filepath),
                "url": f"/api/captures/{filename}",
                "message": f"Screenshot captured successfully: {filename}"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to take screenshot: {str(e)}"}

    @staticmethod
    def lock_workstation() -> Dict[str, Any]:
        """Lock the Windows workstation."""
        try:
            ctypes.windll.user32.LockWorkStation()
            return {"success": True, "message": "Workstation locked successfully."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def power_action(action: str) -> Dict[str, Any]:
        """Execute power action (sleep, restart, shutdown). Requires security PIN."""
        action = action.lower()
        if action == "sleep":
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
            return {"success": True, "message": "System entering sleep mode."}
        elif action == "restart":
            subprocess.run(["shutdown", "/r", "/t", "10"])
            return {"success": True, "message": "System will restart in 10 seconds."}
        elif action == "shutdown":
            subprocess.run(["shutdown", "/s", "/t", "10"])
            return {"success": True, "message": "System will shut down in 10 seconds."}
        return {"success": False, "error": f"Invalid power action: {action}"}

windows_controller = WindowsController()
