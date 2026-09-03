# 题目要求完成清单

| 要求 | 实现 | 验证证据 | 状态 |
|---|---|---|---|
| 部署 Open WebUI，连接至少一个大模型 | Windows 原生 Open WebUI 0.11.3 + llama-server + Qwen2.5-3B；另保留可选 Compose | `scripts/start-native.ps1`、`docs/DEPLOYMENT.md`、实际 15 项 API 结果 | 完成 |
| 课程知识库不少于 8 文件/30 页，分类且至少 3 种 | 28 份：真题、讲义、实验、示例/辨析四类；默认核心库 11 份 | `knowledge/`、`scripts/validate_data.py`、Open WebUI 来源元数据 | 完成 |
| 优先知识库、有引用、未知信息明确说明 | 混合 RAG、课程系统提示词、固定拒答句、API `sources` 证据 | `config/rag-config.json`、`prompts/system-prompt.md`、测试 #1–#10 | 完成 |
| 课程问答、分层解释、示例/代码、练习、反馈、越界提示 | 提示词定义全部行为；知识和工具共同支持 | 系统提示词、示例资料、测试矩阵 | 完成 |
| 学术诚信：不直接完成整份作业 | 默认先给提示、关键步骤和形成性反馈 | `prompts/system-prompt.md` 第 8–9 条 | 完成 |
| 至少一个真实自定义扩展可在对话调用 | 一个 Workspace Tool，含 5 个真实函数 | `openwebui-tools/data_structures_question_bank.py`、测试 #11–#15 | 完成 |
| 至少 15 项测试：5 知识、3 分析、2 无答案、2 练习/批改、2 工具、1 非法 | 按要求正好覆盖 15 项，保存实际输出、来源、判定、问题和改进 | `test-results/acceptance-results.json`、`acceptance-test-report.md` | 完成 |
| 至少一组优化前后对比 | 对 #2、#6、#9、#11、#12 运行基线与优化版 | 验收 JSON 的 `comparison` 与可读报告 | 完成 |
| 源码与 Git 开发记录 | 源码齐全，分阶段提交，另生成可克隆 bundle | 项目 `.git`、`data-structures-ai-tutor-history.bundle` | 完成 |
| Codex 交互记录 | 记录需求、决策、失败与修复、证据路径 | `docs/CODEX_INTERACTION_LOG.md` | 完成 |
| 项目报告 | 架构、数据、实现、测试、局限与复现说明 | `docs/PROJECT_REPORT.md` | 完成 |
| Git 托管仓库链接 | 私有 GitHub 仓库，完整 `main` 历史 | <https://github.com/2300172382a-coder/data-structures-ai-tutor>；提交前添加老师为协作者或确认后公开 | 完成 |

## Docker 判断

Docker 不是题目硬性要求。本项目原生部署已经满足“Open WebUI + 至少一个大模型”的验收条件；Compose 文件仅作为替代方案保留。
