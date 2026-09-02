# -*- coding: utf-8 -*-
"""探测 PDF 结构：页数、每页文字量、题目分布预览"""
import sys
from pypdf import PdfReader

path = sys.argv[1] if len(sys.argv) > 1 else "2009题.pdf"
reader = PdfReader(path)
print(f"文件: {path}")
print(f"总页数: {len(reader.pages)}")
print("=" * 60)

# 打印前2页文字预览（判断是否文字版、看题目编号格式）
for i in range(min(2, len(reader.pages))):
    text = reader.pages[i].extract_text() or ""
    print(f"--- 第 {i+1} 页（{len(text)} 字符）---")
    print(text[:800])
    print()

# 统计每页字符量，找出有文字的页
print("=" * 60)
print("每页字符量:")
for i, page in enumerate(reader.pages):
    text = page.extract_text() or ""
    mark = " <-- 空白/扫描页" if len(text.strip()) < 20 else ""
    print(f"  P{i+1}: {len(text)}{mark}")
