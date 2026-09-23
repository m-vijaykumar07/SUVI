import webbrowser
import urllib.parse
from typing import Dict, Any, Optional
from backend.services.android_bridge import android_bridge
from backend.security import sanitize_phone_number

class WhatsAppSocialService:
    """Manages WhatsApp messaging, automated message replying, and social media interactions."""

    SOCIAL_LINKS = {
        "instagram": "https://instagram.com",
        "twitter": "https://x.com",
        "x": "https://x.com",
        "telegram": "https://web.telegram.org",
        "youtube": "https://youtube.com",
        "discord": "https://discord.com/app",
        "linkedin": "https://linkedin.com",
        "reddit": "https://reddit.com"
    }

    @staticmethod
    def send_whatsapp(recipient: str, message: str, use_android: bool = False) -> Dict[str, Any]:
        """Send or prepare a WhatsApp message for a phone number or contact."""
        clean_num = sanitize_phone_number(recipient)
        encoded_msg = urllib.parse.quote(message)

        # 1. If user requested Android or ADB is connected with active phone
        if use_android or (android_bridge.is_adb_ready() and android_bridge.get_connected_devices()):
            android_res = android_bridge.send_whatsapp_message(clean_num, message)
            if android_res.get("method") == "adb":
                return android_res

        # 2. Desktop Windows WhatsApp URI or WhatsApp Web fallback
        if clean_num:
            direct_uri = f"whatsapp://send?phone={clean_num}&text={encoded_msg}"
            web_url = f"https://web.whatsapp.com/send?phone={clean_num}&text={encoded_msg}"
        else:
            direct_uri = f"whatsapp://send?text={encoded_msg}"
            web_url = f"https://web.whatsapp.com/send?text={encoded_msg}"

        # Attempt to open WhatsApp Desktop client or browser
        try:
            opened = webbrowser.open(direct_uri)
            if not opened:
                webbrowser.open(web_url)
        except Exception:
            webbrowser.open(web_url)

        return {
            "success": True,
            "recipient": recipient,
            "message": message,
            "url": web_url,
            "status": "dispatched",
            "info": f"WhatsApp opened for {recipient or 'contact'} with your message ready."
        }

    @classmethod
    def open_social(cls, platform: str) -> Dict[str, Any]:
        """Open specified social media platform."""
        clean = platform.lower().strip()
        url = cls.SOCIAL_LINKS.get(clean)
        if url:
            webbrowser.open(url)
            return {"success": True, "platform": clean, "url": url, "message": f"Opening {clean.capitalize()}."}
        return {"success": False, "error": f"Social platform '{platform}' not recognized."}

whatsapp_social_service = WhatsAppSocialService()
