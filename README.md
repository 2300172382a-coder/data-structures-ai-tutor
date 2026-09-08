# 数据结构 AI 助教

> **课程作业状态：教师任务书中的功能要求和成果提交要求均已完成。**

本项目基于 Open WebUI 构建“数据结构 AI 助教”，已经在 Windows 本机连接 Qwen2.5-3B-Instruct，完成课程知识库、RAG、系统提示词、自定义题库工具、实际对话测试和优化前后对比。

- GitHub 公开仓库：<https://github.com/2300172382a-coder/data-structures-ai-tutor>
- **最终材料下载：[`submission/数据结构AI助教-最终提交包.zip`](submission/数据结构AI助教-最终提交包.zip)**
- 完整要求映射：[题目要求完成清单](docs/REQUIREMENT_CHECKLIST.md)

## 一、教师任务完成情况

| 教师要求 | 本项目完成结果 | 验收证据 | 状态 |
|---|---|---|:---:|
| 部署 Open WebUI，并连接至少一种大语言模型 | Open WebUI 0.11.3 + llama-server + Qwen2.5-3B-Instruct 已在本机实际运行 | [部署与运行手册](docs/DEPLOYMENT.md) | ✅ 完成 |
| 建设课程知识库：不少于 8 个文件或 30 页、至少 3 类资料 | 28 份资料，包含 17 份历年试题、6 份讲义、2 份实验指导、3 份示例/辨析，共 4 类 | [`knowledge/`](knowledge/)；[数据校验脚本](scripts/validate_data.py) | ✅ 完成 |
| 创建课程专属 AI 助教，支持问答、解释、代码、练习、批改、引用和越界提示 | 创建“数据结构 AI 助教”课程模型；系统提示词覆盖身份、课程范围、回答格式、分层解释、引用、资料缺失和学术诚信 | [优化版系统提示词](prompts/system-prompt.md) | ✅ 完成 |
| 至少完成一个可在对话中调用的真实自定义扩展 | 实现 Python Workspace Tool，包含随机抽题、客观题判分、题库搜索、章节统计、先修关系 5 个函数 | [工具源码](openwebui-tools/data_structures_question_bank.py)；[工具测试](tests/test_question_bank_tool.py) | ✅ 完成 |
| 不少于 15 个测试问题，并记录实际输出、引用、正确性、问题和改进 | 已完成 15/15 项 Open WebUI 实际验收，覆盖题目要求的全部类别 | [验收报告](test-results/acceptance-test-report.md)；[原始结果 JSON](test-results/acceptance-results.json) | ✅ 完成 |
| 至少进行一次优化前后对比 | 使用相同问题完成 5 组基线/优化对比：基线 0/5，优化后 5/5 | [验收报告：优化前后对比](test-results/acceptance-test-report.md#优化前后对比) | ✅ 完成 |
| 源码、Git 提交记录及仓库链接 | 源码已公开，保留分阶段提交记录；提交包内另有完整 Git bundle | 当前公开仓库；[Git 发布说明](docs/GIT_PUBLISHING.md) | ✅ 完成 |
| 与 Codex 的交互记录 | 已记录需求分析、实现决策、失败定位、修复过程和最终验证，且移除密码、令牌等敏感信息 | [Codex 交互记录](docs/CODEX_INTERACTION_LOG.md) | ✅ 完成 |
| 项目总结报告 | 已完成项目概述、架构、知识库、工具、RAG 优化、测试结果、局限和运行方法 | [项目总结报告](docs/PROJECT_REPORT.md) | ✅ 完成 |

## 二、核心成果数字

| 指标 | 结果 |
|---|---:|
| 分类知识资料 | 28 份、4 类 |
| 教学核心 RAG 资料 | 11 份 |
| 结构化历年题 | 218 道（2009–2025） |
| 可自动判分客观题 | 184 道 |
| 自定义工具函数 | 5 个 |
| Open WebUI 实际验收 | 15/15 通过 |
| 优化前后对比 | 基线 0/5 → 优化后 5/5 |
| 自动化单元测试 | 14/14 通过 |

## 三、建议老师按此顺序验收

1. 查看 [教师题目要求摘录](docs/ASSIGNMENT_REQUIREMENTS.md) 和 [逐项完成清单](docs/REQUIREMENT_CHECKLIST.md)。
2. 查看 [项目总结报告](docs/PROJECT_REPORT.md) 和 [系统架构](docs/ARCHITECTURE.md)。
3. 查看 [15 项实际验收报告](test-results/acceptance-test-report.md)，其中保留 AI 实际输出和优化前后数据。
4. 查看 [Codex 交互记录](docs/CODEX_INTERACTION_LOG.md) 和 Git 提交历史。
5. 下载 [最终提交包](submission/数据结构AI助教-最终提交包.zip)，其中包含 Word/PDF 报告、源码 ZIP 和 Git 历史 bundle。

## 四、实现方案

### 1. 两层知识库与 RAG

- 完整档案库：28 份课程资料，用于归档和扩展检索。
- 教学核心库：11 份讲义、实验和示例，作为课程模型默认 RAG 来源。
- 精确真题查询、抽题和判分使用结构化题库工具，避免无关真题片段干扰概念回答。
- RAG 使用中文 BGE、混合检索、`TOP_K=2`、BM25 权重 `0.7`。

### 2. 真实题库扩展

[`openwebui-tools/data_structures_question_bank.py`](openwebui-tools/data_structures_question_bank.py) 是可由 Open WebUI 服务端执行的真实 Workspace Tool，不是用提示词模拟工具结果。它提供：

- `random_questions`：按章节、难度、题型和随机种子抽题；
- `grade_objective_answer`：客观题自动判分；
- `search_questions`：按题干、选项和考点检索；
- `chapter_statistics`：统计章节、题型、难度和年份覆盖；
- `prerequisite_path`：查询知识点先修关系。

## 五、Docker 说明

教师题目要求部署 Open WebUI 并连接至少一个大模型，**没有规定必须使用 Docker**。本项目已经用 Windows 原生方式完成实际部署和全部验收；[`docker-compose.yml`](docker-compose.yml) 仅作为可选的跨平台部署方案。

## 六、当前机器运行

在项目根目录打开 PowerShell：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-native.ps1
```

看到 `Ready: http://127.0.0.1:3000` 后，访问 <http://127.0.0.1:3000>，使用本机管理员账号登录并选择“数据结构 AI 助教”。停止服务：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop-native.ps1
```

在另一台 Windows 机器首次部署时，先运行 `scripts/setup-native.ps1`，再按照 [部署与运行手册](docs/DEPLOYMENT.md) 完成初始化。模型文件和运行数据库体积较大，不包含在 Git 仓库中。

## 七、自动验证

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1
```

脚本会执行 14 项单元测试、数据校验、Python 语法检查和验收报告重渲染。

## 八、目录说明

```text
bank/                  218 道结构化题及分年数据
config/                已验证的 RAG 配置
knowledge/             28 份四类课程资料
openwebui-tools/       Open WebUI Workspace Tool 源码
prompts/               基线和优化版系统提示词
scripts/               安装、启动、初始化、验收与校验脚本
tests/                 自动化单元测试
test-results/          15 项实际验收证据与优化对比
docs/                  题目要求、架构、部署、报告和交互记录
submission/            最终作业提交包
```

## 九、数据与安全边界

历年题来自教师提供的课程资料包。综合题缺少完整权威评分点时，系统只给形成性反馈，不伪造教师评分标准；依赖缺失原图的题目会明确要求补充图片。仓库不包含本地模型、Open WebUI 数据库、账号密码、访问令牌或 `.env`。
