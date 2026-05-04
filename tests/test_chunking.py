from pdf2md_agent.chunking import build_chunks


def test_chunking_preserves_page_spans() -> None:
    md = """
<a id="page-1"></a>

## Page 1

First page paragraph.

<a id="page-2"></a>

## Page 2

Second page paragraph.
"""
    chunks = build_chunks(md, "paper.pdf", "hash", chunk_size=1200, chunk_overlap=150)
    assert [chunk["page_start"] for chunk in chunks] == [1, 2]
    assert [chunk["page_end"] for chunk in chunks] == [1, 2]
    assert chunks[0]["anchors"] == ["page-1"]
    assert chunks[1]["anchors"] == ["page-2"]
