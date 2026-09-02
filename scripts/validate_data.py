"""Validate the course question bank and knowledge inventory."""

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "bank" / "questions.json"


def main() -> int:
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    errors = []
    required = {"id", "year", "number", "type", "chapter", "difficulty", "question"}
    ids = [item.get("id") for item in questions]
    duplicates = [key for key, count in Counter(ids).items() if count > 1]
    if duplicates:
        errors.append(f"duplicate ids: {duplicates}")
    for index, item in enumerate(questions):
        missing = required - item.keys()
        if missing:
            errors.append(f"row {index} missing {sorted(missing)}")
        if item.get("type") == "single":
            if not item.get("options") or not item.get("answer"):
                errors.append(f"{item.get('id')} single question lacks options/answer")
            elif item["answer"] not in item["options"]:
                errors.append(f"{item.get('id')} answer is not an option")
        if item.get("difficulty") not in (1, 2, 3):
            errors.append(f"{item.get('id')} invalid difficulty")

    knowledge_files = list((ROOT / "knowledge").rglob("*.md"))
    categories = sorted({path.parent.name for path in knowledge_files})
    print(f"questions={len(questions)}")
    print(f"objective={sum(q.get('type') == 'single' for q in questions)}")
    print(f"comprehensive={sum(q.get('type') == 'comprehensive' for q in questions)}")
    print(f"knowledge_files={len(knowledge_files)}")
    print(f"knowledge_categories={','.join(categories)}")
    if len(knowledge_files) < 8:
        errors.append("knowledge base has fewer than 8 Markdown files")
    if len(categories) < 3:
        errors.append("knowledge base has fewer than 3 categories")
    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

