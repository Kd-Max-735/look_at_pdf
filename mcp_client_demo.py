"""MCP client demo for screenshots and manual verification."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def call_tool(url: str, file_path: str) -> dict:
    async with streamablehttp_client(url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(
                "look_at_pdf",
                arguments={"file_path": file_path, "enhance_img": True, "fix_table": True},
            )
            if result.structuredContent:
                return result.structuredContent
            if result.content and hasattr(result.content[0], "text"):
                return json.loads(result.content[0].text)
            return {"code": 1999, "msg": "empty MCP response", "md_content": "", "stat": {}}


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="look_at_pdf MCP client demo")
    parser.add_argument("--url", default="http://127.0.0.1:8001/mcp")
    parser.add_argument("--file", default=str(Path("samples/sample_scanned.pdf").resolve()))
    args = parser.parse_args()

    result = asyncio.run(call_tool(args.url, str(Path(args.file).resolve())))
    preview = {
        "code": result.get("code"),
        "msg": result.get("msg"),
        "stat": result.get("stat"),
        "md_preview": str(result.get("md_content", ""))[:500],
    }
    print(json.dumps(preview, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
