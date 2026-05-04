from pathlib import Path

from pdf2md_agent.utils import sha256_file


def test_sha256_file_stable(tmp_path: Path) -> None:
    target = tmp_path / "sample.txt"
    target.write_text("abc", encoding="utf-8")
    assert sha256_file(target) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
