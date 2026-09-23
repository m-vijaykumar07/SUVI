import cv2
import time
import base64
from pathlib import Path
from typing import Dict, Any, Generator, Optional
from backend.config import settings

class CameraService:
    """Manages system camera access, photo capture, and live HUD streaming via OpenCV."""

    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self._cap: Optional[cv2.VideoCapture] = None

    def _get_capture(self) -> cv2.VideoCapture:
        """Initialize or retrieve camera capture device safely."""
        if self._cap is None or not self._cap.isOpened():
            self._cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            # Optimize camera resolution and speed
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self._cap.set(cv2.CAP_PROP_FPS, 30)
        return self._cap

    def release(self):
        """Release camera hardware resources."""
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None

    def capture_photo(self) -> Dict[str, Any]:
        """Capture a high-quality snapshot and save to captures directory."""
        try:
            cap = self._get_capture()
            if not cap.isOpened():
                return {"success": False, "error": "Camera hardware not accessible or in use by another app."}

            # Warm up camera sensor with a couple frame discards
            for _ in range(3):
                cap.read()

            ret, frame = cap.read()
            if not ret or frame is None:
                return {"success": False, "error": "Failed to read image frame from camera."}

            timestamp = int(time.time())
            filename = f"suvi_cam_{timestamp}.jpg"
            filepath = settings.CAPTURES_DIR / filename

            # Add futuristic timestamp/HUD overlay
            hud_text = f"SUVI OPTICS | {time.strftime('%Y-%m-%d %H:%M:%S')}"
            cv2.putText(frame, hud_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 243, 255), 2)
            cv2.rectangle(frame, (10, 10), (frame.shape[1] - 10, frame.shape[0] - 10), (0, 243, 255), 1)

            cv2.imwrite(str(filepath), frame)

            # Encode as base64 for direct JSON display
            _, buffer = cv2.imencode('.jpg', frame)
            b64_str = base64.b64encode(buffer).decode('utf-8')

            return {
                "success": True,
                "filename": filename,
                "path": str(filepath),
                "url": f"/api/captures/{filename}",
                "base64": f"data:image/jpeg;base64,{b64_str}",
                "message": f"Photo captured successfully: {filename}"
            }
        except Exception as e:
            return {"success": False, "error": f"Camera error: {str(e)}"}
        finally:
            self.release()

    def generate_mjpeg_stream(self) -> Generator[bytes, None, None]:
        """Generate MJPEG video stream for live HUD display."""
        cap = self._get_capture()
        try:
            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    break

                # Add futuristic HUD crosshair & scanline effect
                h, w, _ = frame.shape
                cx, cy = w // 2, h // 2
                cv2.circle(frame, (cx, cy), 40, (0, 243, 255), 1)
                cv2.line(frame, (cx - 50, cy), (cx + 50, cy), (0, 243, 255), 1)
                cv2.line(frame, (cx, cy - 50), (cx, cy + 50), (0, 243, 255), 1)
                cv2.putText(frame, "LIVE RECON FEED", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 243, 255), 1)

                ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 65])
                if not ret:
                    continue
                frame_bytes = buffer.tobytes()

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                time.sleep(0.04)  # ~25 FPS
        finally:
            self.release()

camera_service = CameraService()
