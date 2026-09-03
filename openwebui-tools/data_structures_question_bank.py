"""
title: 数据结构题库工具
author: 课程项目组
version: 1.0.0
description: 从结构化题库随机抽题、自动判分、检索题目、统计章节并查询先修关系。
required_open_webui_version: 0.10.0
"""

import json
import random
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Tools:
    """Open WebUI Workspace Tool for the data structures course."""

    class Valves(BaseModel):
        bank_path: str = Field(
            default="/app/backend/data-structures-bank/questions.json",
            description="题库 questions.json 在 Open WebUI 容器内的绝对路径",
        )
        max_results: int = Field(
            default=10,
            ge=1,
            le=30,
            description="单次调用允许返回的最大题目数",
        )

    def __init__(self) -> None:
        self.valves = self.Valves()
        self._cache_path: Optional[str] = None
        self._cache: list[dict] = []

    def _load(self) -> list[dict]:
        configured = Path(self.valves.bank_path)
        fallbacks = [
            configured,
            Path(__file__).resolve().parents[1] / "bank" / "questions.json",
            Path.cwd() / "bank" / "questions.json",
        ]
        path = next((item for item in fallbacks if item.is_file()), None)
        if path is None:
            checked = ", ".join(str(item) for item in fallbacks)
            raise FileNotFoundError(f"未找到题库文件。已检查: {checked}")
        path_key = str(path.resolve())
        if self._cache_path != path_key:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError("题库顶层必须是 JSON 数组")
            self._cache = data
            self._cache_path = path_key
        return self._cache

    @staticmethod
    def _normalize_answer(value: str) -> str:
        return "".join(str(value).upper().split()).replace("，", ",")

    @staticmethod
    def _public_question(item: dict, include_answer: bool) -> dict:
        result = {
            "id": item.get("id"),
            "year": item.get("year"),
            "number": item.get("number"),
            "type": item.get("type"),
            "chapter": item.get("chapter"),
            "topic": item.get("topic"),
            "difficulty": item.get("difficulty"),
            "question": item.get("question"),
            "options": item.get("options"),
            "source": f"bank/questions.json#{item.get('id')}",
        }
        if include_answer:
            result["answer"] = item.get("answer")
            result["explanation"] = item.get("explanation")
        return result

    def random_questions(
        self,
        chapter: str = "",
        difficulty: int = 0,
        question_type: Literal["all", "single", "comprehensive"] = "single",
        count: int = 1,
        include_answer: bool = False,
        seed: int = 0,
    ) -> str:
        """按章节、难度和题型随机抽题。

        :param chapter: 章节名或其中一部分；留空表示全部章节。
        :param difficulty: 0 表示不限，1/2/3 分别表示基础/中等/较难。
        :param question_type: all、single 或 comprehensive。
        :param count: 返回题数，受管理员设置的最大值限制。
        :param include_answer: 是否同时返回答案与解析；自测时应设为 false。
        :param seed: 可复现随机种子；0 表示使用系统随机数。
        :return: JSON 字符串，包含筛选条件、匹配数、题目及来源。
        """
        if difficulty not in (0, 1, 2, 3):
            return json.dumps({"error": "difficulty 只能是 0、1、2 或 3"}, ensure_ascii=False)
        if count < 1:
            return json.dumps({"error": "count 必须大于等于 1"}, ensure_ascii=False)
        items = self._load()
        candidates = [
            item
            for item in items
            if (not chapter or chapter in str(item.get("chapter", "")))
            and (difficulty == 0 or item.get("difficulty") == difficulty)
            and (question_type == "all" or item.get("type") == question_type)
        ]
        if not candidates:
            return json.dumps(
                {
                    "status": "completed",
                    "has_results": False,
                    "error": "没有符合条件的题目",
                    "message_to_user": f"没有符合条件的题目（章节：{chapter or '全部章节'}，难度：{difficulty}）。请调整筛选条件后重试。",
                    "chapter": chapter,
                    "difficulty": difficulty,
                },
                ensure_ascii=False,
            )
        size = min(count, self.valves.max_results, len(candidates))
        rng = random.Random(seed) if seed else random.SystemRandom()
        selected = rng.sample(candidates, size)
        return json.dumps(
            {
                "matched": len(candidates),
                "returned": size,
                "questions": [self._public_question(item, include_answer) for item in selected],
            },
            ensure_ascii=False,
            indent=2,
        )

    def grade_objective_answer(self, question_id: str, student_answer: str) -> str:
        """对一道客观题自动判分并返回解析和来源。

        :param question_id: 题目 ID，例如 2024-s01。
        :param student_answer: 学生答案，例如 A。
        :return: JSON 字符串，包含是否正确、标准答案、解析和来源。
        """
        item = next((q for q in self._load() if q.get("id") == question_id.strip()), None)
        if item is None:
            return json.dumps({"error": f"未找到题目: {question_id}"}, ensure_ascii=False)
        if item.get("type") != "single" or not item.get("answer"):
            return json.dumps(
                {
                    "error": "该题不是可自动判分的客观题",
                    "suggestion": "请让 AI 依据评分要点进行分步反馈，不要宣称自动判分。",
                    "source": f"bank/questions.json#{question_id}",
                },
                ensure_ascii=False,
            )
        expected = self._normalize_answer(item["answer"])
        actual = self._normalize_answer(student_answer)
        return json.dumps(
            {
                "question_id": question_id,
                "student_answer": actual,
                "correct": actual == expected,
                "expected_answer": expected,
                "explanation": item.get("explanation") or "原始题库未提供解析。",
                "source": f"bank/questions.json#{question_id}",
            },
            ensure_ascii=False,
            indent=2,
        )

    def search_questions(self, keyword: str, chapter: str = "", limit: int = 5) -> str:
        """按关键词和章节检索题目。

        :param keyword: 在题干、考点和选项中查找的关键词。
        :param chapter: 可选章节筛选条件。
        :param limit: 最大返回数量。
        :return: JSON 字符串，包含匹配题目和稳定来源标识。
        """
        keyword = keyword.strip()
        if not keyword:
            return json.dumps({"error": "keyword 不能为空"}, ensure_ascii=False)
        result = []
        for item in self._load():
            haystack = " ".join(
                [
                    str(item.get("question", "")),
                    str(item.get("topic", "")),
                    " ".join((item.get("options") or {}).values()),
                ]
            )
            if keyword.lower() in haystack.lower() and (
                not chapter or chapter in str(item.get("chapter", ""))
            ):
                result.append(self._public_question(item, include_answer=False))
        size = min(max(limit, 1), self.valves.max_results)
        return json.dumps(
            {"matched": len(result), "returned": min(len(result), size), "questions": result[:size]},
            ensure_ascii=False,
            indent=2,
        )

    def chapter_statistics(self, chapter: str = "") -> str:
        """统计题库章节、题型和难度分布。

        :param chapter: 留空返回全库章节统计；填写时返回该章节详细统计。
        :return: JSON 字符串，包含题量、题型、难度和年份范围。
        """
        items = [q for q in self._load() if not chapter or chapter in str(q.get("chapter", ""))]
        if not items:
            return json.dumps({"error": f"没有匹配章节: {chapter}"}, ensure_ascii=False)

        def counts(field: str) -> dict[str, int]:
            result: dict[str, int] = {}
            for item in items:
                key = str(item.get(field))
                result[key] = result.get(key, 0) + 1
            return dict(sorted(result.items()))

        years = sorted({q.get("year") for q in items if q.get("year")})
        chapter_counts = counts("chapter")
        max_chapter, max_count = max(chapter_counts.items(), key=lambda entry: entry[1])
        return json.dumps(
            {
                "scope": chapter or "全部章节",
                "total": len(items),
                "chapters": chapter_counts,
                "max_chapter": max_chapter,
                "max_count": max_count,
                "types": counts("type"),
                "difficulty": counts("difficulty"),
                "year_range": [years[0], years[-1]] if years else [],
                "source": "bank/questions.json",
            },
            ensure_ascii=False,
            indent=2,
        )

    def prerequisite_path(self, topic: str) -> str:
        """查询数据结构知识点的建议先修路径。

        :param topic: 知识点，例如 哈夫曼树、最短路径、快速排序、哈希表。
        :return: JSON 字符串，包含匹配主题、先修路径和建议复习顺序。
        """
        graph = {
            "线性表": ["算法复杂度", "数组与指针"],
            "栈": ["线性表", "顺序存储与链式存储"],
            "队列": ["线性表", "循环数组"],
            "二叉树": ["树的基本概念", "递归"],
            "哈夫曼树": ["二叉树", "贪心思想", "优先队列"],
            "图遍历": ["图的表示", "队列与栈"],
            "最短路径": ["图遍历", "带权图", "贪心与动态规划基础"],
            "最小生成树": ["图的表示", "并查集", "贪心思想"],
            "哈希表": ["线性表", "取模运算", "冲突处理"],
            "二叉排序树": ["二叉树", "有序查找"],
            "快速排序": ["顺序表", "分治", "递归"],
            "堆排序": ["完全二叉树", "大根堆与小根堆"],
        }
        topic = topic.strip()
        exact = next((name for name in graph if name == topic), None)
        matched = exact or next((name for name in graph if topic in name or name in topic), None)
        if matched is None:
            return json.dumps(
                {"error": f"先修关系表中未找到: {topic}", "available_topics": sorted(graph)},
                ensure_ascii=False,
            )
        return json.dumps(
            {
                "topic": matched,
                "prerequisites": graph[matched],
                "recommended_order": graph[matched] + [matched],
                "source": "openwebui-tools/data_structures_question_bank.py#prerequisite_path",
            },
            ensure_ascii=False,
            indent=2,
        )
