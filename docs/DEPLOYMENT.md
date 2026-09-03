# 部署与运行手册

## 结论：不需要 Docker

题目要求部署 Open WebUI 并连接至少一个大模型，没有要求必须使用 Docker。本项目已用 Windows 原生方式完整跑通；Docker Compose 仅作为可选的跨平台部署方案。

## A. 当前机器直接运行

运行环境和 Open WebUI 数据库已经配置好。在项目根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-native.ps1
```

脚本会在后台启动：

- Qwen2.5-3B-Instruct GGUF：`127.0.0.1:11435`
- Open WebUI：`127.0.0.1:3000`
- 中文向量模型：本地 `bge-small-zh-v1.5`
- 模型上下文：单槽 16384 tokens，避免 RAG 请求被并行槽均分为 4096

打开 <http://127.0.0.1:3000>，使用已创建的本机管理员账号登录，选择“数据结构 AI 助教”。日志位于脚本所选运行目录的 `logs/`；当前机器通过被 Git 忽略的 `.runtime-path` 指向已安装运行环境。停止：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop-native.ps1
```

## B. 新机器原生部署

前置条件：Windows 10/11、至少 8 GB 内存（推荐 16 GB）、Git、[uv](https://docs.astral.sh/uv/)。还需一个 `llama-server` 可执行文件；脚本会优先使用 `LLAMA_SERVER_PATH`，其次寻找 Docker Desktop 随附的本地 llama-server。这里即使借用 Docker Desktop 的二进制，也没有使用容器。

1. 准备约 5 GB 可用空间：

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\setup-native.ps1
   ```

2. 启动服务：

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\start-native.ps1
   ```

3. 首次初始化 Open WebUI。把示例账号改成自己的本地账号；若数据库为空，脚本会自动注册第一个管理员，否则用现有管理员登录：

   ```powershell
   .\.runtime\openwebui-venv\Scripts\python.exe .\scripts\bootstrap_openwebui.py `
     --email admin@example.local `
     --password "请换成强密码"
   ```

初始化脚本可重复运行：它创建/复用 28 份完整知识库和 11 份教学核心库，导入题库工具、设置 Valve 题库路径、创建课程模型并应用 `config/rag-config.json`。

## C. 可选 Docker Compose

如果团队更习惯容器，可执行：

```powershell
Copy-Item .env.example .env
# 修改 .env 中的 WEBUI_SECRET_KEY
docker compose up -d
docker compose ps
docker compose logs -f model-init
```

访问 <http://localhost:3000>。容器方案默认通过 Ollama 使用 `.env` 中的模型；首次启动需下载镜像、模型和向量模型。随后可按界面手动上传 `knowledge/`、导入 `openwebui-tools/data_structures_question_bank.py` 并粘贴 `prompts/system-prompt.md`，也可从宿主机运行初始化脚本并把 `--bank-path` 设为 `/app/backend/data-structures-bank/questions.json`。

不要把服务直接暴露到公网。共享部署应配置 TLS、关闭公开注册并为普通学生仅授予知识库和工具读取/调用权限。

## 课程模型配置

- 基础模型：`qwen2.5-3b-instruct`
- Function calling：`legacy`（让 Open WebUI 在服务端执行自定义工具）
- Temperature：`0.1`
- Top-p：`0.8`
- Max tokens：`800`
- RAG：混合检索，`TOP_K=2`、BM25 权重 `0.7`
- 默认知识：11 份教学核心库
- 精确真题：题库工具

完整的 28 份资料仍保留在“数据结构课程知识库”中；把默认检索限制到核心库是经过失败复测后的设计，能避免同关键词的历年题干覆盖课程讲义。

## 验收复现

```powershell
$env:OPENWEBUI_EMAIL = 'admin@example.local'
$env:OPENWEBUI_PASSWORD = '你的密码'
.\.runtime\openwebui-venv\Scripts\python.exe .\scripts\run_acceptance.py `
  --output .\test-results\acceptance-results.json
.\.runtime\openwebui-venv\Scripts\python.exe .\scripts\render_acceptance_report.py
```

验收脚本按顺序运行 15 项，避免本地小模型并发时共享缓存导致串题。结构化 JSON 中保存输入、实际输出、来源证据、正确性、问题和改进方式。

## 常见问题

- 端口占用：给 `start-native.ps1` 传入 `-WebPort` 或 `-ModelPort`，并保持两端配置一致。
- 启动较慢：Open WebUI 首次加载中文向量模型约需 1–2 分钟。
- 出现 `request (...) exceeds the available context size`：先执行停止脚本，再重新运行最新版启动脚本；可用 `http://127.0.0.1:11435/props` 确认 `n_ctx` 为 16384、`total_slots` 为 1。
- 无法下载：ModelScope 下载可断点重试；确认 Git LFS 能获取 BGE 权重。
- 工具找不到题库：在 Workspace > Tools > Valves 检查 `bank_path`。
- 修改知识文件后：重新运行初始化脚本或在 Workspace > Knowledge 中重传对应文件。
