from pathlib import Path

from pdf2md_agent.validation import validate_bundle


def _preflight() -> dict:
    return {
        "page_count": 2,
        "pages": [
            {"page": 1, "char_count": 1000, "is_probably_scanned": False},
            {"page": 2, "char_count": 100, "is_probably_scanned": False},
        ],
    }


def test_validation_catches_missing_page_anchors(tmp_path: Path) -> None:
    md = '<a id="page-1"></a>\n\n## Page 1\n\nOnly one page.'
    result = validate_bundle(tmp_path, md, _preflight(), None)
    page_check = next(check for check in result["checks"] if check["name"] == "page_count")
    assert page_check["status"] == "fail"
    assert result["status"] == "fail"


def test_validation_catches_missing_asset_links(tmp_path: Path) -> None:
    md = """
<a id="page-1"></a>

## Page 1

Enough text to avoid empty-page warnings.

<a id="page-2"></a>

## Page 2

![Missing](figures/nope.png)
"""
    result = validate_bundle(tmp_path, md, _preflight(), None)
    link_check = next(check for check in result["checks"] if check["name"] == "asset_links")
    assert link_check["status"] == "fail"
    assert "figures/nope.png" in link_check["missing_links"]
