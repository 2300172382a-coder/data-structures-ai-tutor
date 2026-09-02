# -*- coding: utf-8 -*-
"""合并 bank/years/*.json 与答案键，生成 bank/questions.json 和 bank/考点频次.json/.md

用法: python -B tools\\merge_bank.py
"""
import json
import os
import sys
from collections import Counter, defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YEARS_DIR = os.path.join(BASE, "bank", "years")
BANK_DIR = os.path.join(BASE, "bank")

CHAPTER_ORDER = ["线性表", "栈队列和数组", "树与二叉树", "图", "查找", "排序"]


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    # 1. 加载所有年份文件
    questions = []
    for name in sorted(os.listdir(YEARS_DIR)):
        if name.endswith(".json"):
            questions.extend(load_json(os.path.join(YEARS_DIR, name)))

    # 2. 加载答案键
    keys = {}
    for fn in ("answer_key_2010-2017.json", "answer_key_2018-2025.json"):
        keys.update(load_json(os.path.join(BANK_DIR, fn)))

    # 3. 合并答案 + 校验
    problems = []
    used_key_ids = set()
    for q in questions:
        qid = q["id"]
        if q.get("answer") in (None, "") or q.get("explanation") in (None, ""):
            if qid in keys:
                ans, expl = keys[qid]
                if q.get("answer") in (None, ""):
                    q["answer"] = ans
                if q.get("explanation") in (None, ""):
                    q["explanation"] = expl
            used_key_ids.add(qid)
        else:
            used_key_ids.add(qid)  # 已含答案(如2009)
        # 单选题必须有字母答案；综合题答案为null属正常（要点在explanation）
        if q["type"] == "single" and q.get("answer") not in ("A", "B", "C", "D"):
            problems.append(f"[单选答案异常] {qid} answer={q.get('answer')!r}")
        if not q.get("explanation"):
            problems.append(f"[缺失解析] {qid}")

    orphan = set(keys) - used_key_ids
    for oid in sorted(orphan):
        problems.append(f"[答案键多余] {oid}")

    # 4. 排序输出 questions.json
    questions.sort(key=lambda q: (q["year"], 0 if q["type"] == "single" else 1, q["number"]))
    out_path = os.path.join(BANK_DIR, "questions.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    # 5. 考点频次统计
    chapter_count = Counter(q["chapter"] for q in questions)
    topic_count = Counter(q["topic"] for q in questions)
    topic_by_chapter = defaultdict(Counter)
    for q in questions:
        topic_by_chapter[q["chapter"]][q["topic"]] += 1

    freq = {
        "total": len(questions),
        "by_year": dict(Counter(q["year"] for q in questions)),
        "by_chapter": {c: chapter_count[c] for c in CHAPTER_ORDER if c in chapter_count},
        "topics": {c: dict(topic_by_chapter[c].most_common()) for c in CHAPTER_ORDER if c in topic_by_chapter},
    }
    freq_path = os.path.join(BANK_DIR, "考点频次.json")
    with open(freq_path, "w", encoding="utf-8") as f:
        json.dump(freq, f, ensure_ascii=False, indent=2)

    # 6. 可读版 Markdown（供 RAG / 人工核对）
    md = ["# 408 数据结构真题考点频次（2009-2025）", "",
          f"总题量：{len(questions)} 题", "",
          "| 章节 | 题数 |", "|---|---|"]
    for c in CHAPTER_ORDER:
        if c in chapter_count:
            md.append(f"| {c} | {chapter_count[c]} |")
    md.append("")
    for c in CHAPTER_ORDER:
        if c not in topic_by_chapter:
            continue
        md.append(f"## {c}（{chapter_count[c]}题）")
        md.append("")
        md.append("| 考点 | 题数 | 出现年份 |")
        md.append("|---|---|---|")
        year_by_topic = defaultdict(list)
        for q in questions:
            if q["chapter"] == c:
                year_by_topic[q["topic"]].append(str(q["year"]))
        for t, n in topic_by_chapter[c].most_common():
            md.append(f"| {t} | {n} | {', '.join(sorted(set(year_by_topic[t])))} |")
        md.append("")
    md_path = os.path.join(BANK_DIR, "考点频次.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    # 7. 报告
    print(f"总题量: {len(questions)}")
    print("按年份:", dict(sorted(Counter(q['year'] for q in questions).items())))
    print("按题型:", dict(Counter(q['type'] for q in questions)))
    print("按章节:", {c: chapter_count[c] for c in CHAPTER_ORDER if c in chapter_count})
    print(f"\n输出: {out_path}")
    print(f"输出: {freq_path}")
    print(f"输出: {md_path}")
    if problems:
        print(f"\n=== 发现 {len(problems)} 个问题 ===")
        for p in problems:
            print(" ", p)
        sys.exit(1)
    print("\n校验通过：无缺失答案/解析，无多余答案键。")


if __name__ == "__main__":
    main()
