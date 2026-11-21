"""Local import demo. Run: python local_demo.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from look_at_pdf import convert_to_markdown


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    sample = Path("samples/sample_scanned.pdf").resolve()
    result = convert_to_markdown(str(sample), enhance_img=True, fix_table=True)

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "local_demo_output.md"
    if result["code"] == 0:
        output_path.write_text(result["md_content"], encoding="utf-8")

    preview = {
        "code": result["code"],
        "msg": result["msg"],
        "stat": result["stat"],
        "saved_to": str(output_path.resolve()) if result["code"] == 0 else "",
        "md_preview": result["md_content"][:500],
    }
    print(json.dumps(preview, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
