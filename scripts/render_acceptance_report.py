#!/usr/bin/env python3
"""Render the Open WebUI acceptance JSON as a submission-ready Markdown report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def safe_fence(text: str) -> str:
    return text.replace("```", "~~~")


def rate(items: list[dict], predicate) -> str:
    return f"{sum(1 for item in items if predicate(item))}/{len(items)}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", default="test-results/acceptance-results.json")
    parser.add_argument("output", nargs="?", default="test-results/acceptance-test-report.md")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    results = data["results"]
    baseline = data["comparison"]["baseline"]
    optimized = data["comparison"]["optimized"]
    baseline_by_id = {item["id"]: item for item in baseline}
    optimized_by_id = {item["id"]: item for item in optimized}

    lines = [
        "# Open WebUI 实际验收报告",
        "",
        f"- 完整运行时间：`{data['generated_at']}`",
        *([f"- 最近定向复测：`{data['updated_at']}`；复测历史保存在 JSON 中"] if data.get("updated_at") else []),
        f"- 课程模型：`{data['optimized_model']}`（基座 `{data['base_model']}`）",
        f"- 实际通过：**{data['summary']['passed']}/{data['summary']['total']}**",
        "- 判定说明：引用依据为 Open WebUI API 返回的 `sources` 元数据；工具题同时保留工具来源与返回文档，不把预期回答冒充实测输出。",
        "",
        "## 分类汇总",
        "",
        "| 类别 | 通过/总数 |",
        "|---|---:|",
    ]
    categories = []
    for item in results:
        if item["category"] not in categories:
            categories.append(item["category"])
    for category in categories:
        items = [item for item in results if item["category"] == category]
        lines.append(f"| {category} | {rate(items, lambda row: row['passed'])} |")

    lines.extend(["", "## 15 项运行记录", ""])
    for item in results:
        lines.extend(
            [
                f"### #{item['id']} {item['category']}",
                "",
                f"- 测试输入：{item['prompt']}",
                f"- 调用的知识/工具：{'、'.join(item['sources']) if item['sources'] else '无'}",
                f"- 引用是否正确：{item['citation_correct']}",
                f"- 回答是否正确：{item['answer_correct']}",
                f"- 测试判定：{'通过' if item['passed'] else '未通过'}",
                f"- 存在的问题：{item['issues']}",
                f"- 改进方式：{item['improvement']}",
                f"- 用时：{item['elapsed_seconds']} 秒",
                "",
                "AI 实际输出：",
                "",
                "```text",
                safe_fence(item["actual_output"]),
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "## 优化前后对比",
            "",
            "基线使用原始基础模型和 `prompts/baseline-prompt.md`，不附加知识库或题库工具；优化版使用课程模型、分层知识库、RAG 模板和真实 Workspace Tool。",
            "",
            "| 用例 | 基线正确 | 基线引用 | 优化正确 | 优化引用 |",
            "|---:|---|---|---|---|",
        ]
    )
    for case_id in data["comparison"]["case_ids"]:
        before = baseline_by_id[case_id]
        after = optimized_by_id[case_id]
        lines.append(
            f"| #{case_id} | {before['answer_correct']} | {before['citation_correct']} | "
            f"{after['answer_correct']} | {after['citation_correct']} |"
        )

    lines.extend(
        [
            "",
            "| 指标 | 基线 | 优化版 |",
            "|---|---:|---:|",
            f"| 回答正确率 | {rate(baseline, lambda row: row['answer_correct'] == '是')} | {rate(optimized, lambda row: row['answer_correct'] == '是')} |",
            f"| 应引用用例的有效引用率 | {rate([row for row in baseline if row['citation_correct'] != '不适用'], lambda row: row['citation_correct'] == '是')} | {rate([row for row in optimized if row['citation_correct'] != '不适用'], lambda row: row['citation_correct'] == '是')} |",
            f"| 查无资料诚实拒答（#9） | {'是' if '资料中未找到' in baseline_by_id[9]['actual_output'] else '否'} | {'是' if '资料中未找到' in optimized_by_id[9]['actual_output'] else '否'} |",
            f"| 工具任务成功（#11、#12） | {rate([baseline_by_id[11], baseline_by_id[12]], lambda row: row['passed'])} | {rate([optimized_by_id[11], optimized_by_id[12]], lambda row: row['passed'])} |",
            "",
            "完整结构化证据（包括 `source_evidence`）见 `test-results/acceptance-results.json`。",
            "",
        ]
    )
    Path(args.output).write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
