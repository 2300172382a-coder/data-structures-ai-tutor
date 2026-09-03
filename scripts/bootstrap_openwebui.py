#!/usr/bin/env python3
"""Idempotently configure Open WebUI with both knowledge bases, tool, and course model."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests


TOOL_ID = "data_structures_question_bank"
MODEL_ID = "data-structures-ai-tutor"
FULL_KB_NAME = "数据结构课程知识库"
CORE_KB_NAME = "数据结构教学核心库"


class Client:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "data-structures-ai-tutor-bootstrap/1.0"})

    def request(self, method: str, path: str, **kwargs):
        response = self.session.request(method, f"{self.base_url}{path}", timeout=300, **kwargs)
        if not response.ok:
            raise RuntimeError(f"{method} {path} -> HTTP {response.status_code}: {response.text}")
        return response.json() if response.content else None

    def authenticate(self, name: str, email: str, password: str) -> dict:
        response = self.session.post(
            f"{self.base_url}/api/v1/auths/signin",
            json={"email": email, "password": password},
            timeout=30,
        )
        if not response.ok:
            response = self.session.post(
                f"{self.base_url}/api/v1/auths/signup",
                json={"name": name, "email": email, "password": password},
                timeout=30,
            )
        if not response.ok:
            raise RuntimeError(f"登录/首次注册失败：HTTP {response.status_code}: {response.text}")
        auth = response.json()
        self.session.headers.update({"Authorization": f"Bearer {auth['token']}"})
        return auth


def get_or_create_knowledge(client: Client, name: str, description: str) -> dict:
    listing = client.request("GET", "/api/v1/knowledge/")
    found = next((item for item in listing["items"] if item["name"] == name), None)
    if found:
        return found
    return client.request(
        "POST",
        "/api/v1/knowledge/create",
        json={"name": name, "description": description, "access_grants": []},
    )


def list_knowledge_files(client: Client, knowledge_id: str) -> list[dict]:
    return client.request("GET", f"/api/v1/knowledge/{knowledge_id}/files?page=1&limit=100")["items"]


def upload_knowledge(client: Client, project_root: Path, full_kb: dict, core_kb: dict) -> tuple[int, int]:
    existing_full = {item["filename"]: item for item in list_knowledge_files(client, full_kb["id"])}
    existing_core_ids = {item["id"] for item in list_knowledge_files(client, core_kb["id"])}
    markdown_files = sorted((project_root / "knowledge").rglob("*.md"))
    core_files = [path for path in markdown_files if "exams" not in path.parts]

    for index, path in enumerate(markdown_files, start=1):
        item = existing_full.get(path.name)
        if item is None:
            relative_name = path.relative_to(project_root / "knowledge").as_posix()
            metadata = json.dumps({"name": relative_name, "knowledge_id": full_kb["id"]}, ensure_ascii=False)
            with path.open("rb") as stream:
                item = client.request(
                    "POST",
                    "/api/v1/files/?process=true&process_in_background=false",
                    files={"file": (path.name, stream, "text/markdown")},
                    data={"metadata": metadata},
                )
            existing_full[path.name] = item
            print(f"[{index:02d}/{len(markdown_files)}] 上传 {relative_name}", flush=True)

        if path in core_files and item["id"] not in existing_core_ids:
            client.request(
                "POST",
                f"/api/v1/knowledge/{core_kb['id']}/file/add",
                json={"file_id": item["id"]},
            )
            existing_core_ids.add(item["id"])

    return len(markdown_files), len(core_files)


def configure_tool(client: Client, project_root: Path, bank_path: str) -> None:
    content = (project_root / "openwebui-tools" / "data_structures_question_bank.py").read_text(encoding="utf-8")
    payload = {
        "id": TOOL_ID,
        "name": "数据结构题库工具",
        "content": content,
        "meta": {"description": "随机抽题、客观题判分、题库检索、章节统计和先修关系查询"},
        "access_grants": [],
    }
    exists = client.session.get(f"{client.base_url}/api/v1/tools/id/{TOOL_ID}", timeout=30).ok
    endpoint = f"/api/v1/tools/id/{TOOL_ID}/update" if exists else "/api/v1/tools/create"
    client.request("POST", endpoint, json=payload)
    client.request("POST", f"/api/v1/tools/id/{TOOL_ID}/valves/update", json={"valves": {"bank_path": bank_path, "max_results": 10}})


def configure_model(client: Client, project_root: Path, core_kb: dict, base_model: str) -> None:
    system_prompt = (project_root / "prompts" / "system-prompt.md").read_text(encoding="utf-8")
    payload = {
        "id": MODEL_ID,
        "base_model_id": base_model,
        "name": "数据结构 AI 助教",
        "params": {
            "system": system_prompt,
            "temperature": 0.1,
            "top_p": 0.8,
            "repeat_penalty": 1.12,
            "max_tokens": 800,
            "function_calling": "legacy",
        },
        "meta": {
            "description": "基于核心教学资料、完整真题档案和结构化题库的数据结构课程助教",
            "capabilities": {"builtin_tools": False, "file_context": True, "citations": True},
            "knowledge": [{"name": CORE_KB_NAME, "type": "collection", "id": core_kb["id"]}],
            "toolIds": [TOOL_ID],
            "tags": [{"name": "数据结构"}, {"name": "课程助教"}],
            "builtinTools": {"knowledge": True},
        },
        "access_grants": [],
        "is_active": True,
    }
    exists = client.session.get(f"{client.base_url}/api/v1/models/model?id={MODEL_ID}", timeout=30).ok
    endpoint = "/api/v1/models/model/update" if exists else "/api/v1/models/create"
    client.request("POST", endpoint, json=payload)


def configure_model_defaults(client: Client) -> None:
    """Prefer the course model and avoid expensive hidden tools on local CPU inference."""
    config = client.request("GET", "/api/v1/configs/models")
    default_metadata = dict(config.get("DEFAULT_MODEL_METADATA") or {})
    capabilities = dict(default_metadata.get("capabilities") or {})
    capabilities["builtin_tools"] = False
    default_metadata["capabilities"] = capabilities

    client.request(
        "POST",
        "/api/v1/configs/models",
        json={
            **config,
            "DEFAULT_MODELS": MODEL_ID,
            "DEFAULT_MODEL_METADATA": default_metadata,
        },
    )
    client.request("GET", "/api/models?refresh=true")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:3000")
    parser.add_argument("--name", default="课程项目管理员")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--base-model", default="qwen2.5-3b-instruct")
    parser.add_argument("--bank-path", default="")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    bank_path = args.bank_path or str((project_root / "bank" / "questions.json").resolve())
    client = Client(args.base_url)
    auth = client.authenticate(args.name, args.email, args.password)
    if auth.get("role") != "admin":
        raise RuntimeError("初始化必须使用 Open WebUI 管理员账号")

    full_kb = get_or_create_knowledge(
        client,
        FULL_KB_NAME,
        "课程讲义、实验、示例、辨析卡与 2009–2025 历年试题的完整分类档案。",
    )
    core_kb = get_or_create_knowledge(
        client,
        CORE_KB_NAME,
        "课程模型默认检索的讲义、实验、示例和关键辨析卡；精确真题通过结构化工具查询。",
    )
    full_count, core_count = upload_knowledge(client, project_root, full_kb, core_kb)
    configure_tool(client, project_root, bank_path)
    configure_model(client, project_root, core_kb, args.base_model)
    configure_model_defaults(client)
    rag_config = json.loads((project_root / "config" / "rag-config.json").read_text(encoding="utf-8"))
    client.request("POST", "/api/v1/retrieval/config/update", json=rag_config)

    print(f"初始化完成：完整库 {full_count} 份，核心库 {core_count} 份，课程模型 {MODEL_ID}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"初始化失败：{error}", file=sys.stderr)
        sys.exit(1)
