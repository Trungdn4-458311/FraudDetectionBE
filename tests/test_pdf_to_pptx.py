"""Integration test for the slides PDF -> PPTX converter (slides/pdf_to_pptx.py)."""
import fitz  # PyMuPDF
from pptx import Presentation

import pdf_to_pptx


def test_convert_preserves_page_count_and_ratio(tmp_path):
    pdf = tmp_path / "deck.pdf"
    pptx = tmp_path / "deck.pptx"

    # build a tiny 3-page 16:9 PDF
    doc = fitz.open()
    for i in range(3):
        page = doc.new_page(width=960, height=540)  # 16:9
        page.insert_text((72, 72), f"slide {i}")
    doc.save(pdf)
    doc.close()

    pdf_to_pptx.convert(str(pdf), str(pptx), dpi=96)

    assert pptx.exists()
    prs = Presentation(str(pptx))
    assert len(prs.slides._sldIdLst) == 3
    # 16:9 aspect preserved (within rounding)
    ratio = prs.slide_width / prs.slide_height
    assert abs(ratio - 16 / 9) < 0.02
