# -*- coding: utf-8 -*-
"""将 bank/questions.json 的答案与解析，回填到 knowledge/exams/*.md 每道题下。

用法: python -B tools\\backfill_answers.py
策略：
- Markdown 里单选按 "### N." 或 "### N、" 匹配编号 N → 对应 id = "{year}-s{N:02d}"
- Markdown 里综合题按 "### N.（X分）" 或 "### N、（X分）" 匹配 → id = "{year}-c{N}"
- 在每个题目块（下一个"###"之前、或下一题之前）的末尾追加：

  > ✅ **答案**：B
  > 📖 **解析**：外层i到√n...

- 若题目块已有 "> ✅ **答案**" 标记则跳过（幂等）。
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK_PATH = os.path.join(BASE, "bank", "questions.json")
EXAMS_DIR = os.path.join(BASE, "knowledge", "exams")


def load_questions():
    with open(BANK_PATH, "r", encoding="utf-8") as f:
        qs = json.load(f)
    return {q["id"]: q for q in qs}


def split_blocks(lines):
    """按 '### ' 切分成（标题行号，标题文本，体行列表）三元组，不含非题目块。"""
    blocks = []
    n = len(lines)
    i = 0
    while i < n:
        line = lines[i]
        if line.startswith("### "):
            # 收集体行直到下一个 ### 或 ## 节结束
            start = i
            body = []
            j = i + 1
            while j < n and not lines[j].startswith("### ") and not lines[j].startswith("## "):
                body.append(lines[j])
                j += 1
            blocks.append((start, line.strip(), body))
            i = j
        else:
            i += 1
    return blocks


# 匹配 ### 1.  或  ### 1、  或  ### 41.（13分）
NUM_RE = re.compile(r"###\s+(\d+)([\.、])")


def build_backfill(q):
    ans = q.get("answer")
    expl = q.get("explanation") or ""
    if q["type"] == "single":
        return [
            f"> ✅ **答案**：{ans}",
            f"> 📖 **解析**：{expl}",
            "",
        ]
    else:
        # 综合题
        ans_line = f"> ✅ **参考答案**：见要点解析" if ans is None else f"> ✅ **参考答案**：{ans}"
        return [
            ans_line,
            f"> 📖 **参考解析**：{expl}",
            "",
        ]


def backfill_one(filepath, qmap):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    # 提取年份：文件名 YYYY-数据结构.md
    basename = os.path.basename(filepath)
    year = int(re.match(r"(\d{4})", basename).group(1))

    blocks = split_blocks(lines)
    inserts = 0
    # 自底向上插入，避免行号偏移
    work = list(lines)
    for start, title, body in reversed(blocks):
        m = NUM_RE.match(title)
        if not m:
            continue
        num = int(m.group(1))
        if num <= 20:
            qid = f"{year}-s{num:02d}"
        else:
            qid = f"{year}-c{num}"
        if qid not in qmap:
            print(f"  [缺失题库条目] {qid} ← {title[:40]}")
            continue
        q = qmap[qid]
        already = any("> ✅ **答案**" in l or "> ✅ **参考答案**" in l for l in body)
        if already:
            continue
        # 找到体段中最后一个非空行的插入位置（去掉尾空行再回插，保持版式干净）
        trailing_empty = 0
        for l in reversed(body):
            if l == "":
                trailing_empty += 1
            else:
                break
        # 插入位置 = start + 1 + (len(body) - trailing_empty)
        # 即：在标题行之后、最后一个非空体行之后、再附加；尾部再保留与原来一致的空行数（通常1）
        pos = start + 1 + (len(body) - trailing_empty)
        chunk = build_backfill(q)
        # chunk 末尾已有 1 个空行；抵消 trailing_empty，确保最终空行与原来等价
        if trailing_empty == 0:
            # 没有尾空行 → 不需要额外空行
            pass
        elif trailing_empty == 1:
            # 保持：chunk 末尾已经有一个空行
            pass
        else:
            # 原尾空行 > 1 → 补加
            chunk.extend([""] * (trailing_empty - 1))
        for line in reversed(chunk):
            work.insert(pos, line)
        inserts += 1

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(work) + "\n")
    return inserts


def main():
    qmap = load_questions()
    files = sorted(os.path.join(EXAMS_DIR, n) for n in os.listdir(EXAMS_DIR) if n.endswith(".md"))
    total = 0
    for fp in files:
        c = backfill_one(fp, qmap)
        print(f"{os.path.basename(fp)}: 回填 {c} 题")
        total += c
    print(f"\n共回填 {total} 题，涉及 {len(files)} 份 Markdown。")

    # 快速校验：题目块中是否都带了答案
    missing = 0
    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        blocks = split_blocks(lines)
        basename = os.path.basename(fp)
        year = int(re.match(r"(\d{4})", basename).group(1))
        for _, title, body in blocks:
            m = NUM_RE.match(title)
            if not m:
                continue
            num = int(m.group(1))
            qid = (f"{year}-s{num:02d}") if num <= 20 else (f"{year}-c{num}")
            if qid not in qmap:
                continue
            has = any("> ✅ **答案**" in l or "> ✅ **参考答案**" in l for l in body)
            if not has:
                print(f"  [仍缺失答案块] {qid}")
                missing += 1
    if missing:
        print(f"\n[!] 还有 {missing} 题未找到答案块，需人工核对。")
        sys.exit(1)
    print("[OK] 校验通过：所有题库中存在的题目，在 Markdown 中均已嵌入答案/解析。")


if __name__ == "__main__":
    main()
