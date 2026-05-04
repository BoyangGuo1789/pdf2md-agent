from __future__ import annotations

from .base import ConversionEngine
from .docling_engine import DoclingEngine
from .marker_engine import MarkerEngine
from .pymupdf4llm_engine import PyMuPDF4LLMEngine
from .text_engine import TextEngine


ENGINE_CLASSES = {
    "pymupdf4llm": PyMuPDF4LLMEngine,
    "docling": DoclingEngine,
    "marker": MarkerEngine,
    "text": TextEngine,
}


def get_engine(name: str, prefer: list[str] | None = None) -> ConversionEngine:
    if name == "auto":
        for candidate in prefer or ["pymupdf4llm", "docling", "text"]:
            engine = get_engine(candidate)
            if engine.is_available():
                return engine
        raise RuntimeError("No PDF conversion engine is available. Install at least PyMuPDF.")

    cls = ENGINE_CLASSES.get(name)
    if cls is None:
        known = ", ".join(["auto", *ENGINE_CLASSES])
        raise ValueError(f"Unknown engine '{name}'. Expected one of: {known}")
    return cls()
