"""MCP server. Run: python mcp_server.py --port 8001"""

from __future__ import annotations

import argparse
import json
import socket
import sys

from mcp.server.fastmcp import FastMCP

from look_at_pdf import convert_to_markdown
from look_at_pdf.errors import ERR_PORT_OCCUPIED

TOOL_NAME = "look_at_pdf"


def build_server(host: str, port: int) -> FastMCP:
    mcp = FastMCP(
        "look_at_pdf",
        instructions="Convert local scanned PDF/image files to standard Markdown.",
        host=host,
        port=port,
        streamable_http_path="/mcp",
        json_response=True,
        stateless_http=False,
    )

    @mcp.tool(name=TOOL_NAME, description="扫描版 PDF 或图片转 Markdown。")
    def look_at_pdf_skill(file_path: str, enhance_img: bool = True, fix_table: bool = True) -> dict:
        return convert_to_markdown(file_path=file_path, enhance_img=enhance_img, fix_table=fix_table)

    return mcp


def port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="look_at_pdf MCP server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()

    if not port_available(args.host, args.port):
        payload = {
            "code": ERR_PORT_OCCUPIED,
            "msg": f"MCP server port is occupied: {args.host}:{args.port}",
            "md_content": "",
            "stat": {"page_num": 0, "table_num": 0, "avg_accuracy": 0.0},
        }
        print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        return ERR_PORT_OCCUPIED

    server = build_server(args.host, args.port)
    try:
        server.run(transport="streamable-http")
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
