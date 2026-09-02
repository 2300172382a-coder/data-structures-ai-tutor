# 部署与配置手册

## 1. 前置条件

- Windows、macOS 或 Linux；推荐 Docker Desktop / Docker Engine + Compose。
- 建议至少 8 GB 内存；`qwen3:4b` 体验更好，资源不足可在 `.env` 改成 `qwen3:1.7b`。
- 首次启动需要联网下载 Open WebUI、Ollama 模型和多语言嵌入模型。

## 2. 启动服务

在项目根目录执行：

```powershell
Copy-Item .env.example .env
# 编辑 .env，把 WEBUI_SECRET_KEY 换成长随机字符串
docker compose up -d
docker compose ps
docker compose logs -f model-init
```

`model-init` 成功退出后，在浏览器打开 <http://localhost:3000>。首次注册的账号作为管理员。不要把实例直接暴露到公网；如需共享，配置 TLS、访问控制并关闭公开注册。

若端口冲突，在 `.env` 修改 `WEBUI_PORT`。若模型下载失败，可手动运行：

```powershell
docker compose exec ollama ollama pull qwen3:4b
```

## 3. 创建课程知识库

1. 进入 `Workspace > Knowledge`，创建“数据结构课程知识库”。
2. 描述填写：“课程讲义、实验指导、示例代码、常见错误与 2009–2025 历年试题”。
3. 上传 `knowledge` 目录中的全部 27 份 Markdown。若界面支持目录同步，直接同步整个目录并保留四类子目录。
4. 等待每个文件处理完成。抽查“哈夫曼树”“Dijkstra”“循环队列”等关键词是否能检索。
5. 检索模式选择 Focused Retrieval/RAG；启用混合检索。资料较短且需要逐字读取时，可临时使用 Full Context，不要把所有 27 份资料同时完整注入。

## 4. 导入自定义工具

1. 进入 `Workspace > Tools`，新建工具。
2. 将 `openwebui-tools/data_structures_question_bank.py` 全文粘贴并保存。
3. 在工具 Valves 中确认 `bank_path` 为 `/app/backend/data-structures-bank/questions.json`。
4. 先手动测试 `chapter_statistics()`，预期总题数为 218。
5. 只授予课程用户读取/调用权限，不授予普通用户编辑工具权限。

## 5. 创建课程模型

1. 进入 `Workspace > Models`，创建模型“数据结构 AI 助教”。
2. 基础模型选择 `.env` 中拉取的模型（默认 `qwen3:4b`）。
3. 把 `prompts/system-prompt.md` 的正文放入 System Prompt。
4. 附加“数据结构课程知识库”和“数据结构题库工具”。
5. 保持 Native 工具调用模式；启用知识、工具和引用能力。
6. 保存后新建对话，输入：“请先查询题库统计，再从图章节抽一道中等选择题，不显示答案。”确认界面出现两次工具调用。

## 6. 验收和留证

按 `test-results/acceptance-test-matrix.md` 逐条测试，把 Open WebUI 实际输出、引用和截图路径填入“运行记录”。然后使用基线提示词和优化提示词分别运行同一组 5 个对比问题，记录引用率、正确率、拒答诚实性和工具调用成功率。

推荐保留以下截图：

- Compose 服务正常状态和模型列表。
- 知识库文件数量与分类。
- 课程模型的系统提示词、知识和工具绑定。
- 正确引用回答、资料缺失拒答、随机抽题、自动判分。
- 优化前后同一问题的对比。

## 7. 常用维护命令

```powershell
docker compose ps
docker compose logs --tail 100 open-webui
docker compose restart open-webui
docker compose down
```

`docker compose down` 会保留命名卷。不要运行 `docker compose down -v`，除非明确要删除全部 Open WebUI 数据和本地模型。

