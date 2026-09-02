# -*- coding: utf-8 -*-
"""把扫描版 PDF 每页渲染成 PNG 图片，供阅读/OCR 用
用法: python -B tools\render_pdf.py "2009题.pdf" [起始页] [结束页]
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "libs"))

import pypdfium2 as pdfium

pdf_path = sys.argv[1]
start = int(sys.argv[2]) if len(sys.argv) > 2 else 1
end = int(sys.argv[3]) if len(sys.argv) > 3 else None

year = os.path.splitext(os.path.basename(pdf_path))[0].replace("题", "")
out_dir = os.path.join("images", year)
os.makedirs(out_dir, exist_ok=True)

pdf = pdfium.PdfDocument(pdf_path)
n = len(pdf)
end = end or n
# scale=2 约 144 DPI，公式和图表清晰度够用
for i in range(start - 1, min(end, n)):
    page = pdf[i]
    bitmap = page.render(scale=2)
    img = bitmap.to_pil()
    out = os.path.join(out_dir, f"page-{i+1}.png")
    img.save(out)
    print(f"{out}  ({img.width}x{img.height})")
