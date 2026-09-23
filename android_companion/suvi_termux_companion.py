"""
SUVI Standalone Android Termux Companion Service
Runs on your Android phone inside Termux to receive commands over Wi-Fi from SUVI PC.
Requires Termux:API app installed from F-Droid or GitHub.
"""

import subprocess
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8085

def run_termux_cmd(cmd):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return "", str(e)

class CompanionHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8')
        try:
            payload = json.loads(body) if body else {}
        except Exception:
            payload = {}

        path = self.path

        if path == "/call":
            num = payload.get("number", "")
            if num:
                out, err = run_termux_cmd(f"termux-telephony-call {num}")
                self._send_json(200, {"success": True, "message": f"Calling {num} via Termux."})
            else:
                self._send_json(400, {"error": "Missing number"})

        elif path == "/sms":
            num = payload.get("number", "")
            msg = payload.get("message", "")
            out, err = run_termux_cmd(f'termux-sms-send -n "{num}" "{msg}"')
            self._send_json(200, {"success": True, "message": "SMS dispatched."})

        elif path == "/notify":
            title = payload.get("title", "SUVI Alert")
            content = payload.get("content", "")
            run_termux_cmd(f'termux-notification -t "{title}" -c "{content}"')
            self._send_json(200, {"success": True})

        elif path == "/tts":
            text = payload.get("text", "")
            run_termux_cmd(f'termux-tts-speak "{text}"')
            self._send_json(200, {"success": True})

        elif path == "/battery":
            out, _ = run_termux_cmd("termux-battery-status")
            try:
                data = json.loads(out)
                self._send_json(200, data)
            except Exception:
                self._send_json(200, {"raw": out})
        else:
            self._send_json(404, {"error": "Endpoint not found"})

    def do_GET(self):
        if self.path == "/ping":
            self._send_json(200, {"status": "alive", "service": "SUVI Android Companion"})
        else:
            self._send_json(404, {"error": "Not found"})

def main():
    print(f"[*] SUVI Android Termux Companion starting on port {PORT}...")
    server = HTTPServer(('0.0.0.0', PORT), CompanionHandler)
    print(f"[+] Service is active! Connect SUVI PC to this phone's IP on port {PORT}.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping companion service.")

if __name__ == "__main__":
    main()
