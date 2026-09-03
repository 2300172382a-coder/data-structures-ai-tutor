# 数据结构 AI 助教

基于 Open WebUI 的课程专属 AI 应用，已在 Windows 本机使用 Open WebUI 0.11.3、Qwen2.5-3B-Instruct、中文 BGE 向量模型完成实际部署和对话验收。

## 完成内容

- 28 份分类知识资料：17 份历年试题、6 份讲义、2 份实验、3 份示例/辨析资料。
- 两层 RAG：28 份完整档案库用于留存和查询，11 份教学核心库作为课程模型默认检索源，避免真题片段污染概念回答。
- 218 道结构化真题，覆盖 2009–2025 年、六个核心章节；184 道客观题带标准答案与解析。
- 一个可在 Open WebUI 对话中真实调用的 Workspace Tool，提供随机抽题、客观题判分、题库搜索、章节统计和先修关系 5 个函数。
- 系统提示词包含身份、范围、输出格式、分层解释、引用、查无资料处理和学术诚信约束。
- 15 项 Open WebUI 实际验收、5 项优化前后对比、13 项工具单元测试和数据质量检查。

## 当前机器直接启动（不需要 Docker）

在本目录打开 PowerShell：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-native.ps1
```

等待出现 `Ready: http://127.0.0.1:3000` 后访问该地址，使用已创建的本机管理员账号登录并选择“数据结构 AI 助教”。停止服务：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop-native.ps1
```

首次在另一台 Windows 机器部署时，先运行 `scripts/setup-native.ps1` 下载运行环境，再按 [部署手册](docs/DEPLOYMENT.md) 执行一次初始化。Docker Compose 只是可选方案，题目没有要求必须使用 Docker。

## 验证命令

```powershell
python -m unittest discover -s tests -v
python scripts/validate_data.py
python scripts/render_acceptance_report.py
```

实际大模型结果见 `test-results/acceptance-results.json` 和 `test-results/acceptance-test-report.md`。

将仓库发布到 GitHub/Gitee 的两条命令和 bundle 恢复方法见 [Git 仓库发布说明](docs/GIT_PUBLISHING.md)。

## 目录

```text
bank/                  结构化题库及分年数据
config/                已验证的 RAG 配置
knowledge/             可上传到 Open WebUI 的四类资料
openwebui-tools/       Workspace Tool 源码
prompts/               基线和优化版系统提示词
scripts/               安装、启动、初始化、验收与数据脚本
tests/                 自动化单元测试
test-results/          实际验收证据与优化对比
docs/                  架构、部署、项目报告和交互记录
```

## 数据边界

历年题来自教师提供的项目压缩包。综合题的权威评分点不完整，因此工具只对客观题自动判分；综合题由 AI 提供形成性反馈。含原图但图像缺失的题目必须明确说明无法确认，不伪造题图或答案。
