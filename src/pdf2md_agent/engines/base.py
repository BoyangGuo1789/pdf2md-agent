from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass
class ConversionResult:
    markdown: str
    document_json: dict[str, Any]
    engine: str
    warnings: list[str]


class ConversionEngine(Protocol):
    name: str

    def is_available(self) -> bool:
        ...

    def convert(self, pdf_path: Path, out_dir: Path, config: dict[str, Any]) -> ConversionResult:
        ...
