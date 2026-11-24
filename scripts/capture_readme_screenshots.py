#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Capture 5 English LTR high-res screenshots of Urmia Lake Observatory via local Chrome/Edge CDP."""

import base64
import json
import os
import shutil
import socket
import struct
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_ROOT / "docs" / "screenshots"
TARGET_URL = "https://urmia-lake-observatory.pages.dev/"
CDP_PORT = 9333


def find_browser() -> str:
    candidates = [
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    raise RuntimeError("Neither Google Chrome nor Microsoft Edge was found on this machine.")


def recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("WebSocket closed unexpectedly")
        buf.extend(chunk)
    return bytes(buf)


class SimpleCDP:
    def __init__(self, ws_url: str):
        rest = ws_url.replace("ws://", "")
        host_port, path = rest.split("/", 1)
        host, port = host_port.split(":")
        self.sock = socket.create_connection((host, int(port)), timeout=40)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        req = (
            f"GET /{path} HTTP/1.1\r\n"
            f"Host: {host_port}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(req.encode("ascii"))
        resp = b""
        while b"\r\n\r\n" not in resp:
            resp += self.sock.recv(1024)
        self.msg_id = 0

    def send_frame(self, text: str) -> None:
        data = text.encode("utf-8")
        mask = os.urandom(4)
        header = bytearray([0x81])
        ln = len(data)
        if ln < 126:
            header.append(0x80 | ln)
        elif ln < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", ln))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", ln))
        header.extend(mask)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        self.sock.sendall(bytes(header) + masked)

    def recv_message(self) -> str:
        chunks = []
        while True:
            b1, b2 = recv_exact(self.sock, 2)
            fin = (b1 & 0x80) != 0
            opcode = b1 & 0x0F
            ln = b2 & 0x7F
            if ln == 126:
                ln = struct.unpack("!H", recv_exact(self.sock, 2))[0]
            elif ln == 127:
                ln = struct.unpack("!Q", recv_exact(self.sock, 8))[0]
            payload = recv_exact(self.sock, ln)
            if opcode == 0x8:
                raise ConnectionError("WebSocket closed")
            if opcode in (0x9, 0xA):
                continue
            chunks.append(payload)
            if fin:
                return b"".join(chunks).decode("utf-8", errors="replace")

    def call(self, method: str, params: dict | None = None) -> dict:
        self.msg_id += 1
        cid = self.msg_id
        self.send_frame(json.dumps({"id": cid, "method": method, "params": params or {}}))
        while True:
            msg = json.loads(self.recv_message())
            if msg.get("id") == cid:
                return msg.get("result", {})

    def close(self) -> None:
        try:
            self.sock.close()
        except Exception:
            pass


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    browser = find_browser()
    print(f"  Using browser: {browser}")
    profile_dir = tempfile.mkdtemp(prefix="ulo_cdp_")

    proc = subprocess.Popen(
        [
            browser,
            "--headless=new",
            f"--remote-debugging-port={CDP_PORT}",
            "--remote-allow-origins=*",
            "--window-size=1440,920",
            "--disable-gpu-sandbox",
            "--use-gl=angle",
            "--use-angle=swiftshader",
            "--enable-webgl",
            "--ignore-gpu-blocklist",
            "--hide-scrollbars",
            f"--user-data-dir={profile_dir}",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    cdp = None
    try:
        ws_url = None
        for _ in range(30):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json", timeout=2) as resp:
                    targets = json.loads(resp.read().decode("utf-8"))
                    page = next((t for t in targets if t.get("type") == "page" and t.get("webSocketDebuggerUrl")), None)
                    if page:
                        ws_url = page["webSocketDebuggerUrl"]
                        break
            except Exception:
                time.sleep(0.4)

        if not ws_url:
            raise RuntimeError("Could not connect to browser DevTools endpoint.")

        cdp = SimpleCDP(ws_url)
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")
        cdp.call("Emulation.setDeviceMetricsOverride", {
            "width": 1440,
            "height": 920,
            "deviceScaleFactor": 1.25,
            "mobile": False,
        })

        print(f"  Loading live observatory: {TARGET_URL}")
        cdp.call("Page.navigate", {"url": TARGET_URL})
        time.sleep(7.0)

        # Switch UI to English (LTR) so GitHub README screenshots match English documentation
        cdp.call("Runtime.evaluate", {
            "expression": """
                (() => {
                  const btn = Array.from(document.querySelectorAll('button')).find(
                    b => (b.textContent || '').includes('English')
                  );
                  if (btn) btn.click();
                  window.scrollTo(0, 0);
                })();
            """
        })
        time.sleep(3.5)

        shots = [
            (
                "01-overview-kpis.png",
                "window.scrollTo(0, 0);",
                1.5,
            ),
            (
                "02-webgis-map.png",
                """
                const mapEl = document.querySelector('.maplibregl-map') || document.querySelector('[class*="map"]');
                if (mapEl) mapEl.scrollIntoView({ behavior: 'instant', block: 'center' });
                """,
                4.5,
            ),
            (
                "03-hydrology-climate-charts.png",
                """
                const charts = Array.from(document.querySelectorAll('canvas')).filter(c => !c.closest('.maplibregl-map') && c.getBoundingClientRect().height > 120); if (charts.length === 0) { window.scrollTo(0, 1750); }
                if (charts.length > 0) {
                  const rectTop = charts[0].getBoundingClientRect().top + window.scrollY - 120; window.scrollTo(0, Math.max(1650, rectTop)); const box = null;
                  if (box) { const top = box.getBoundingClientRect().top + window.scrollY - 90;  }
                  
                }
                """,
                2.0,
            ),
            (
                "04-research-center-dss.png",
                """
                const el = document.getElementById('scientific-research-center');
                if (el) {
                  const top = el.getBoundingClientRect().top + window.scrollY - 16;
                  
                }
                """,
                2.0,
            ),
            (
                "05-data-management-pdf.png",
                """
                const el = document.getElementById('data-management-reports');
                if (el) {
                  const top = el.getBoundingClientRect().top + window.scrollY - 16;
                  
                }
                """,
                2.0,
            ),
        ]

        for filename, js, wait_s in shots:
            cdp.call("Runtime.evaluate", {"expression": f"(() => {{ {js} }})();"})
            time.sleep(wait_s)
            res = cdp.call("Page.captureScreenshot", {"format": "png", "fromSurface": True})
            img_bytes = base64.b64decode(res["data"])
            out_file = OUT_DIR / filename
            out_file.write_bytes(img_bytes)
            print(f"  [OK] Captured {out_file.relative_to(PROJECT_ROOT)} ({round(len(img_bytes)/1024, 1)} KB)")
    finally:
        if cdp:
            cdp.close()
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        shutil.rmtree(profile_dir, ignore_errors=True)


if __name__ == "__main__":
    main()