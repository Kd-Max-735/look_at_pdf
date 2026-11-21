"""Generate demo screenshots from actual local and MCP command outputs."""

from __future__ import annotations

import socket
import subprocess
import sys
import textwrap
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = ROOT / "demo"


def run_local_demo() -> str:
    completed = subprocess.run(
        [sys.executable, "local_demo.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return _format_command("python local_demo.py", completed.stdout, completed.stderr, completed.returncode)


def run_mcp_demo() -> str:
    server = subprocess.Popen(
        [sys.executable, "mcp_server.py", "--port", "8001"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
    )
    try:
        _wait_for_port("127.0.0.1", 8001, timeout=10)
        completed = subprocess.run(
            [sys.executable, "mcp_client_demo.py", "--url", "http://127.0.0.1:8001/mcp"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return _format_command(
            "python mcp_client_demo.py --url http://127.0.0.1:8001/mcp",
            completed.stdout,
            completed.stderr,
            completed.returncode,
        )
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)


def _wait_for_port(host: str, port: int, timeout: int) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            if sock.connect_ex((host, port)) == 0:
                return
        time.sleep(0.2)
    raise RuntimeError(f"server did not listen on {host}:{port}")


def _format_command(command: str, stdout: str, stderr: str, code: int) -> str:
    text = f"PS {ROOT}> {command}\n{stdout}"
    if stderr:
        text += f"\n[stderr]\n{stderr}"
    text += f"\n[exit code] {code}\n"
    return text


def render_terminal_png(text: str, output_path: Path) -> None:
    font = _load_font(22)
    padding = 26
    width = 1320
    max_text_width = width - padding * 2
    probe = Image.new("RGB", (width, 120), (18, 22, 28))
    probe_draw = ImageDraw.Draw(probe)

    wrapped_lines: list[str] = []
    for line in text.splitlines():
        wrapped_lines.extend(_wrap_by_pixels(line, font, probe_draw, max_text_width) or [""])

    line_height = 31
    height = max(520, padding * 2 + line_height * len(wrapped_lines))
    image = Image.new("RGB", (width, height), (18, 22, 28))
    draw = ImageDraw.Draw(image)

    y = padding
    for idx, line in enumerate(wrapped_lines):
        color = (153, 224, 170) if idx == 0 else (230, 236, 245)
        draw.text((padding, y), line, font=font, fill=color)
        y += line_height

    output_path.parent.mkdir(exist_ok=True)
    image.save(output_path)


def _wrap_by_pixels(
    line: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    draw: ImageDraw.ImageDraw,
    max_width: int,
) -> list[str]:
    if not line:
        return [""]

    rough_lines = textwrap.wrap(line, width=130, break_long_words=False, break_on_hyphens=False) or [line]
    wrapped: list[str] = []
    for rough in rough_lines:
        current = ""
        for char in rough:
            candidate = current + char
            if current and draw.textlength(candidate, font=font) > max_width:
                wrapped.append(current)
                current = char
            else:
                current = candidate
        if current:
            wrapped.append(current)
    return wrapped


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def main() -> None:
    local_text = run_local_demo()
    mcp_text = run_mcp_demo()
    DEMO_DIR.mkdir(exist_ok=True)
    (DEMO_DIR / "local_demo_output.txt").write_text(local_text, encoding="utf-8")
    (DEMO_DIR / "mcp_call_output.txt").write_text(mcp_text, encoding="utf-8")
    render_terminal_png(local_text, DEMO_DIR / "local_demo_screenshot.png")
    render_terminal_png(mcp_text, DEMO_DIR / "mcp_call_screenshot.png")
    print((DEMO_DIR / "local_demo_screenshot.png").resolve())
    print((DEMO_DIR / "mcp_call_screenshot.png").resolve())


if __name__ == "__main__":
    main()
