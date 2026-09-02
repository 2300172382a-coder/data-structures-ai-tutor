# 数据结构 AI 助教

基于 Open WebUI、Ollama、课程知识库和自定义 Workspace Tool 的课程专属 AI 助教。项目使用 2009–2025 年数据结构真题和自编课程资料，支持知识问答、分层解释、例题与思路、练习生成、答案分析、资料引用和越界提示。

## 已实现内容

- Docker Compose 一键启动 Open WebUI 与 Ollama，默认模型为 `qwen3:4b`。
- 17 份历年试题知识文档，以及讲义、实验、示例代码和常见错误等分类资料。
- 严格的课程助教系统提示词：优先检索、强制标注来源、不确定时拒绝编造、遵守学术诚信。
- 自定义题库工具：随机抽题、客观题判分、题库搜索、章节统计、先修关系查询。
- 218 道结构化题目，覆盖六个核心章节；184 道客观题含答案与解析。
- 单元测试、数据质量检查、15 项验收测试矩阵和优化前后对比方案。

## 快速启动

1. 启动 Docker Desktop。
2. 将 `.env.example` 复制为 `.env`，修改 `WEBUI_SECRET_KEY`；内存不足时可将模型改为 `qwen3:1.7b`。
3. 在本目录运行：

   ```powershell
   docker compose up -d
   docker compose ps
   ```

4. 首次启动会下载镜像、语言模型和多语言嵌入模型。完成后访问 <http://localhost:3000>。
5. 按 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) 创建知识库、导入工具并创建课程模型。

## 本地验证

项目代码仅依赖 Python 标准库；Open WebUI 导入工具时会提供 Pydantic。

```powershell
python -m unittest discover -s tests -v
python scripts/validate_data.py
docker compose config
```

如果系统没有全局 Python，可使用 Codex 工作区附带的 Python 3.11 运行上述命令。

## 目录说明

```text
bank/                  结构化题库及各年份源数据
knowledge/             可上传到 Open WebUI 的分类知识资料
openwebui-tools/       可直接粘贴导入的 Workspace Tool
prompts/               课程模型系统提示词
scripts/               数据校验与源资料处理脚本
tests/                 自动化单元测试
test-results/          15 项验收矩阵与测试说明
docs/                  部署、设计和项目总结
```

## 数据来源与边界

题库与历年试题来自教师提供的“数据结构项目.zip”。课程讲义、实验指导、示例代码和常见错误说明由本项目基于通用数据结构课程大纲整理。综合题的标准答案在原始数据中不完整，因此工具只自动判分客观题；综合题由 AI 依据知识库给出分步反馈，避免伪造唯一答案。

