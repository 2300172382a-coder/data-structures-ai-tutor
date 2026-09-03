import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = ROOT / "openwebui-tools" / "data_structures_question_bank.py"
SPEC = importlib.util.spec_from_file_location("data_structures_question_bank", TOOL_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class QuestionBankToolTests(unittest.TestCase):
    def setUp(self):
        self.tool = MODULE.Tools()
        self.tool.valves.bank_path = str(ROOT / "bank" / "questions.json")

    def call(self, method, *args, **kwargs):
        return json.loads(method(*args, **kwargs))

    def test_loads_all_questions(self):
        self.assertEqual(218, len(self.tool._load()))

    def test_random_questions_are_reproducible_and_filtered(self):
        result = self.call(
            self.tool.random_questions,
            chapter="图",
            difficulty=2,
            question_type="single",
            count=3,
            seed=42,
        )
        self.assertEqual(3, result["returned"])
        self.assertTrue(all(q["chapter"] == "图" for q in result["questions"]))
        self.assertTrue(all(q["difficulty"] == 2 for q in result["questions"]))
        self.assertTrue(all("answer" not in q for q in result["questions"]))

    def test_random_question_can_include_answer(self):
        result = self.call(self.tool.random_questions, count=1, include_answer=True, seed=7)
        self.assertIn("answer", result["questions"][0])
        self.assertIn("source", result["questions"][0])

    def test_grades_correct_answer(self):
        result = self.call(self.tool.grade_objective_answer, "2009-s01", " b ")
        self.assertTrue(result["correct"])
        self.assertEqual("B", result["expected_answer"])

    def test_grades_incorrect_answer(self):
        result = self.call(self.tool.grade_objective_answer, "2009-s01", "A")
        self.assertFalse(result["correct"])
        self.assertTrue(result["explanation"])

    def test_rejects_unknown_question(self):
        result = self.call(self.tool.grade_objective_answer, "2099-s99", "A")
        self.assertIn("error", result)

    def test_does_not_auto_grade_comprehensive_question(self):
        result = self.call(self.tool.grade_objective_answer, "2010-c41", "test")
        self.assertIn("error", result)
        self.assertIn("分步反馈", result["suggestion"])

    def test_search_requires_keyword(self):
        result = self.call(self.tool.search_questions, "")
        self.assertIn("error", result)

    def test_search_returns_sources(self):
        result = self.call(self.tool.search_questions, "哈夫曼", limit=3)
        self.assertGreater(result["matched"], 0)
        self.assertTrue(all(q["source"].startswith("bank/") for q in result["questions"]))

    def test_statistics(self):
        result = self.call(self.tool.chapter_statistics)
        self.assertEqual(218, result["total"])
        self.assertEqual(57, result["chapters"]["树与二叉树"])
        self.assertEqual("树与二叉树", result["max_chapter"])
        self.assertEqual(57, result["max_count"])
        self.assertEqual([2009, 2025], result["year_range"])

    def test_prerequisite_path(self):
        result = self.call(self.tool.prerequisite_path, "哈夫曼树")
        self.assertEqual("哈夫曼树", result["topic"])
        self.assertIn("二叉树", result["prerequisites"])

    def test_invalid_difficulty_is_structured_error(self):
        result = self.call(self.tool.random_questions, difficulty=9)
        self.assertIn("error", result)

    def test_unknown_chapter_is_structured_error(self):
        result = self.call(self.tool.random_questions, chapter="不存在章节", difficulty=2, count=3)
        self.assertEqual("没有符合条件的题目", result["error"])
        self.assertEqual("不存在章节", result["chapter"])
        self.assertEqual("completed", result["status"])
        self.assertFalse(result["has_results"])
        self.assertIn("请调整筛选条件后重试", result["message_to_user"])


if __name__ == "__main__":
    unittest.main()
