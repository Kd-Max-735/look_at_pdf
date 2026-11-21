"""Input and output schemas shared by local calls and MCP calls."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ConvertRequest:
    file_path: str
    enhance_img: bool = True
    fix_table: bool = True

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ConvertRequest":
        return cls(
            file_path=str(payload.get("file_path", "")),
            enhance_img=bool(payload.get("enhance_img", True)),
            fix_table=bool(payload.get("fix_table", True)),
        )


@dataclass
class Stat:
    page_num: int = 0
    table_num: int = 0
    avg_accuracy: float = 0.0


@dataclass
class ConvertResult:
    code: int
    msg: str
    md_content: str = ""
    stat: Stat = field(default_factory=Stat)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["stat"]["avg_accuracy"] = round(float(data["stat"]["avg_accuracy"]), 2)
        return data
