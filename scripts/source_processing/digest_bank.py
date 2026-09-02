# -*- coding: utf-8 -*-
"""校验 bank/years/*.json 并生成紧凑题目标清单，供人工核对后填写答案键
输出: bank/digest.txt
"""
import json
import glob
import os
import re

out_lines = []
total = 0
errors = []

for path in sorted(glob.glob("bank/years/*.json")):
    year = re.search(r"(\d{4})", os.path.basename(path)).group(1)
    with open(path, encoding="utf-8") as f:
        qs = json.load(f)
    singles = [q for q in qs if q["type"] == "single"]
    comps = [q for q in qs if q["type"] == "comprehensive"]
    out_lines.append(f"\n===== {year}  单选{len(singles)}题 综合{len(comps)}题 =====")
    for q in qs:
        # 字段完整性检查
        for field in ("id", "year", "number", "type", "chapter", "topic", "difficulty", "question"):
            if q.get(field) is None:
                errors.append(f"{q.get('id', '?')}: 缺字段 {field}")
        if q["type"] == "single" and (not q.get("options") or len(q["options"]) != 4):
            errors.append(f"{q['id']}: 选项不是4个")
        if q.get("answer") is not None:
            errors.append(f"{q['id']}: answer 不为 null（应无答案）")
        total += 1
        qtext = re.sub(r"\s+", "", q["question"])[:55]
        line = f"[{q['id']}] {q['chapter']}|d{q['difficulty']} {qtext}"
        if q["type"] == "single":
            opts = " ".join(f"{k}:{re.sub(chr(10), '', str(v))[:22]}" for k, v in q["options"].items())
            line += f"\n    {opts}"
        else:
            line += f" ({q.get('score')}分)"
        out_lines.append(line)

out_lines.append(f"\n总计: {total} 题")
if errors:
    out_lines.append("发现问题:")
    out_lines.extend("  " + e for e in errors)
else:
    out_lines.append("字段完整性检查: 全部通过")

with open("bank/digest.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))
print(f"digest 写入 bank/digest.txt，共 {total} 题，{len(errors)} 个问题")
