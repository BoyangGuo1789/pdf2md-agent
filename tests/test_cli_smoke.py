from pathlib import Path

import pytest
from typer.testing import CliRunner

from pdf2md_agent.cli import app


pytest.importorskip("fitz")
pytest.importorskip("reportlab")


def _make_pdf(path: Path) -> None:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path), pagesize=letter)
    c.drawString(72, 720, "Hello PDF to Markdown")
    c.drawString(72, 700, "This is a smoke test page.")
    c.showPage()
    c.drawString(72, 720, "Second page")
    c.save()


def test_cli_smoke_convert_text_engine(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    out_dir = tmp_path / "out"
    _make_pdf(pdf_path)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "convert",
            str(pdf_path),
            "--out",
            str(out_dir),
            "--engine",
            "text",
            "--ocr",
            "never",
            "--render-pages",
            "--chunk",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (out_dir / "document.md").exists()
    assert (out_dir / "manifest.json").exists()
    assert (out_dir / "logs" / "preflight.json").exists()
    assert (out_dir / "logs" / "validation.json").exists()
    assert (out_dir / "chunks" / "chunks.jsonl").exists()
    assert (out_dir / "pages" / "page_0001.png").exists()
