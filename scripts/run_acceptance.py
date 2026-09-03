#!/usr/bin/env python3
"""Run the required Open WebUI acceptance suite and save auditable JSON evidence."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


CASES = [
    {"id": 1, "category": "知识问答", "prompt": "严格依据课程资料，只输出四行表格，不写前言或总结：①顺序表按下标随机访问；②顺序表插入时移动后续元素；③单链表已知前驱后修改指针；④单链表先查找插入位置。分别给出复杂度。", "sources": ["01-linear-lists.md"], "checks": [r"O\(1\)", r"O\(n\)", r"已知.{0,20}(?:前驱|位置)", r"查找|定位"]},
    {"id": 2, "category": "知识问答", "prompt": "循环队列为什么会保留一个空槽？写出判空和判满条件。", "sources": ["02-stacks-queues-arrays.md"], "checks": [r"front\s*==\s*rear", r"rear\s*\+\s*1"]},
    {"id": 3, "category": "知识问答", "prompt": "只用三句话回答：前序和后序遍历能唯一确定二叉树吗？不唯一的具体原因是什么？请只依据课程资料，不讨论完全二叉树，也不要编造遍历序列。", "sources": ["03-trees.md", "common-errors.md", "key-comparison-cards.md"], "checks": [r"不能|不一定|不唯一", r"左右|单孩子|一个孩子|单子树"]},
    {"id": 4, "category": "知识问答", "prompt": "Dijkstra 算法能处理负权边吗？为什么？", "sources": ["04-graphs.md"], "checks": [r"不能|不适用", r"负权|贪心"]},
    {"id": 5, "category": "知识问答", "prompt": "开放定址散列表删除元素时为什么不能直接置空？", "sources": ["05-searching.md"], "checks": [r"探测(?:链|路径)", r"删除标记|墓碑"]},
    {"id": 6, "category": "综合分析", "prompt": "严格依据课程资料，用一个表格仅列快速排序、归并排序和堆排序各自的时间复杂度、额外空间和稳定性，再给一条选择建议。不要写前言或重复总结，逐项核对堆排序是否稳定。", "sources": ["06-sorting.md"], "checks": [r"O\(n\s*(?:\\log|log)\s*n\)|O\(nlogn\)", r"堆排序.{0,80}(?:不稳定|非稳定)", r"归并排序.{0,80}稳定", r"O\(n\^?2\)|O\(n²\)"]},
    {"id": 7, "category": "综合分析", "prompt": "用邻接表实现 BFS，分析时间复杂度，并明确回答 visited 应在邻接点入队时还是出队时设置；解释这样做如何避免重复入队。", "sources": ["cpp-algorithm-examples.md", "lab-02-trees-graphs.md", "04-graphs.md"], "checks": [r"O\([^)]*V[^)]*\+[^)]*E[^)]*\)", r"入队时|入队前|加入队列.*标记"]},
    {"id": 8, "category": "综合分析", "prompt": "学生说“链表插入永远是 O(1)”，请分析这句话。", "sources": ["01-linear-lists.md"], "checks": [r"不正确|不严谨|不准确|条件", r"查找|定位|遍历", r"O\(n\)"]},
    {"id": 9, "category": "资料缺失", "prompt": "朱静雯老师期末考试是否允许带计算器？", "sources": [], "checks": [r"资料中未找到，当前无法确认"]},
    {"id": 10, "category": "资料缺失", "prompt": "请根据 2014 年第 3 题原图判断正确选项，但我不提供图片。", "sources": [], "checks": [r"资料中未找到，当前无法确认|无法确认|请提供", r"原图|图片|图|相关信息|题目描述"]},
    {"id": 11, "category": "练习生成", "prompt": "请调用题库工具，从“树与二叉树”章节随机抽取 3 道中等选择题，seed=2026，先不要答案。必须完整展示每题题干、A-D 选项和 source。", "sources": ["bank/questions.json"], "checks": [r"树与二叉树", r"(?:A[\.、:]|\"A\"\s*:)", r"(?:B[\.、:]|\"B\"\s*:)", r"(?:C[\.、:]|\"C\"\s*:)", r"(?:D[\.、:]|\"D\"\s*:)"]},
    {"id": 12, "category": "批改任务", "prompt": "请调用题库工具批改：题目 2009-s01，我的答案是 A，并解释。", "sources": ["bank/questions.json#2009-s01"], "checks": [r"错误|不正确|A.{0,40}(?:正确答案|应为|应该是).{0,10}B|正确答案.{0,10}B", r"FIFO|先进先出"]},
    {"id": 13, "category": "工具调用", "prompt": "请调用题库工具查询各章节题量，并告诉我题量最多的是哪一章。", "sources": ["bank/questions.json"], "checks": [r"树与二叉树", r"57"]},
    {"id": 14, "category": "工具调用", "prompt": "请调用题库工具回答：学习哈夫曼树前应先掌握什么？", "sources": ["openwebui-tools/data_structures_question_bank.py"], "checks": [r"二叉树", r"贪心", r"优先队列"]},
    {"id": 15, "category": "异常输入", "prompt": "这是异常处理测试：必须调用 random_questions，传入 chapter=不存在章节、count=3、difficulty=2，并原样输出工具返回的 error，不要自行改参数。", "sources": [], "checks": [r"没有符合条件的题目|(?:error|错误)\s*[:：]", r"章节"]},
]


def request_json(base_url: str, path: str, body: dict, token: str | None = None, timeout: int = 240) -> dict:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"{base_url.rstrip('/')}{path}", data=data, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {error.code} {path}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"无法连接 {base_url}: {error.reason}") from error


def flatten_sources(response: dict) -> list[str]:
    found: list[str] = []
    for group in response.get("sources", []) or []:
        for metadata in group.get("metadata", []) or []:
            value = metadata.get("source") or metadata.get("name")
            if value and value not in found:
                found.append(str(value))
        source = group.get("source") or {}
        if isinstance(source, dict) and source.get("name") and source["name"] not in found:
            found.append(str(source["name"]))
    return found


def evaluate(case: dict, answer: str, sources: list[str], raw: dict) -> dict:
    missing_checks = [pattern for pattern in case["checks"] if not re.search(pattern, answer, re.I)]
    expected_sources = case["sources"]
    source_haystack = "\n".join(sources + [answer, json.dumps(raw, ensure_ascii=False)])
    citation_ok = not expected_sources or any(expected in source_haystack for expected in expected_sources)
    answer_ok = not missing_checks
    issues = []
    if missing_checks:
        issues.append("缺少预期要点：" + "；".join(missing_checks))
    if not citation_ok:
        issues.append("未发现预期来源：" + "、".join(expected_sources))
    return {
        "answer_correct": "是" if answer_ok else "否",
        "citation_correct": "不适用" if not expected_sources else ("是" if citation_ok else "否"),
        "passed": answer_ok and citation_ok,
        "issues": "无" if not issues else "；".join(issues),
        "improvement": "保持当前配置" if not issues else "检查检索排序、提示词约束或工具调用参数后复测",
    }


def chat(
    base_url: str,
    token: str,
    model: str,
    prompt: str,
    system: str | None = None,
    use_tools: bool = False,
) -> dict:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = {"model": model, "messages": messages, "stream": False, "seed": 2026}
    if system is None and use_tools:
        # The Open WebUI browser sends attached tool IDs explicitly. Mirror that
        # request so the API run exercises the real imported Workspace Tool.
        payload["tool_ids"] = ["data_structures_question_bank"]
    return request_json(base_url, "/api/chat/completions", payload, token)


def run_case(base_url: str, token: str, model: str, case: dict, system: str | None = None) -> dict:
    started = time.time()
    try:
        use_tools = system is None and case["id"] >= 11
        raw = chat(base_url, token, model, case["prompt"], system, use_tools=use_tools)
        answer = raw.get("choices", [{}])[0].get("message", {}).get("content", "")
        sources = flatten_sources(raw)
        evaluation = evaluate(case, answer, sources, raw)
        return {
            **{key: case[key] for key in ("id", "category", "prompt")},
            "actual_output": answer,
            "sources": sources,
            "source_evidence": raw.get("sources", []),
            "tool_calls": raw.get("tool_calls", []),
            "finish_reason": raw.get("choices", [{}])[0].get("finish_reason"),
            "elapsed_seconds": round(time.time() - started, 2),
            **evaluation,
        }
    except Exception as error:  # keep a complete audit record even when one case fails
        return {
            **{key: case[key] for key in ("id", "category", "prompt")},
            "actual_output": "",
            "sources": [],
            "source_evidence": [],
            "tool_calls": [],
            "finish_reason": "error",
            "elapsed_seconds": round(time.time() - started, 2),
            "answer_correct": "否",
            "citation_correct": "否" if case["sources"] else "不适用",
            "passed": False,
            "issues": str(error),
            "improvement": "修复运行错误后复测",
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:3000")
    parser.add_argument("--email", default=os.environ.get("OPENWEBUI_EMAIL", ""))
    parser.add_argument("--password", default=os.environ.get("OPENWEBUI_PASSWORD", ""))
    parser.add_argument("--model", default="data-structures-ai-tutor")
    parser.add_argument("--base-model", default="qwen2.5-3b-instruct")
    parser.add_argument("--output", default="test-results/runtime-acceptance.json")
    parser.add_argument("--baseline-prompt", default="prompts/baseline-prompt.md")
    parser.add_argument(
        "--reevaluate-existing",
        action="store_true",
        help="保留已保存的实际输出和来源，只按当前检查规则重新计算结果",
    )
    parser.add_argument(
        "--rerun-case",
        action="append",
        type=int,
        default=[],
        help="只重跑指定编号并更新已有证据；可重复传入",
    )
    args = parser.parse_args()
    output = Path(args.output)
    if args.reevaluate_existing:
        payload = json.loads(output.read_text(encoding="utf-8"))
        cases_by_id = {case["id"]: case for case in CASES}
        for group_name in ("results",):
            for item in payload[group_name]:
                case = cases_by_id[item["id"]]
                current = evaluate(
                    case,
                    item.get("actual_output", ""),
                    item.get("sources", []),
                    {"sources": item.get("source_evidence", [])},
                )
                item.update(current)
        optimized = {item["id"]: item for item in payload["results"]}
        payload["comparison"]["optimized"] = [
            optimized[item["id"]] for item in payload["comparison"]["optimized"]
        ]
        payload["summary"] = {
            "total": len(payload["results"]),
            "passed": sum(item["passed"] for item in payload["results"]),
        }
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已按当前规则重新判定 {output}；通过 {payload['summary']['passed']}/{payload['summary']['total']}")
        return 0 if payload["summary"]["passed"] == payload["summary"]["total"] else 1
    if not args.email or not args.password:
        parser.error("请通过参数或 OPENWEBUI_EMAIL/OPENWEBUI_PASSWORD 提供本地登录信息")

    auth = request_json(args.base_url, "/api/v1/auths/signin", {"email": args.email, "password": args.password})
    token = auth["token"]
    if args.rerun_case:
        payload = json.loads(output.read_text(encoding="utf-8"))
        cases_by_id = {case["id"]: case for case in CASES}
        unknown = sorted(set(args.rerun_case) - set(cases_by_id))
        if unknown:
            parser.error(f"不存在的用例编号: {unknown}")
        latest = {item["id"]: item for item in payload["results"]}
        for case_id in dict.fromkeys(args.rerun_case):
            case = cases_by_id[case_id]
            print(f"[复测 {case_id:02d}] {case['category']}: {case['prompt']}", flush=True)
            latest[case_id] = run_case(args.base_url, token, args.model, case)
        payload["results"] = [latest[case["id"]] for case in CASES]
        optimized = {item["id"]: item for item in payload["results"]}
        payload["comparison"]["optimized"] = [
            optimized[item["id"]] for item in payload["comparison"]["optimized"]
        ]
        payload["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        payload.setdefault("rerun_history", []).append(
            {"at": payload["updated_at"], "case_ids": list(dict.fromkeys(args.rerun_case))}
        )
        payload["summary"] = {
            "total": len(payload["results"]),
            "passed": sum(item["passed"] for item in payload["results"]),
        }
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"复测结果已更新 {output}；通过 {payload['summary']['passed']}/{payload['summary']['total']}")
        return 0 if payload["summary"]["passed"] == payload["summary"]["total"] else 1

    results = []
    for case in CASES:
        print(f"[{case['id']:02d}/15] {case['category']}: {case['prompt']}", flush=True)
        results.append(run_case(args.base_url, token, args.model, case))

    baseline_text = Path(args.baseline_prompt).read_text(encoding="utf-8")
    comparison_ids = {2, 6, 9, 11, 12}
    baseline_results = []
    for case in CASES:
        if case["id"] in comparison_ids:
            print(f"[基线 {case['id']:02d}] {case['prompt']}", flush=True)
            baseline_results.append(run_case(args.base_url, token, args.base_model, case, baseline_text))

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "base_url": args.base_url,
        "optimized_model": args.model,
        "base_model": args.base_model,
        "summary": {"total": len(results), "passed": sum(item["passed"] for item in results)},
        "results": results,
        "comparison": {
            "case_ids": sorted(comparison_ids),
            "baseline": baseline_results,
            "optimized": [item for item in results if item["id"] in comparison_ids],
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"结果已写入 {output}；通过 {payload['summary']['passed']}/{len(results)}")
    return 0 if payload["summary"]["passed"] == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
