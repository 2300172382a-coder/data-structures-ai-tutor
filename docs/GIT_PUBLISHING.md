# Git 仓库发布说明

项目已经发布到公开 GitHub 仓库：<https://github.com/2300172382a-coder/data-structures-ai-tutor>。`main` 分支包含完整的分阶段提交，无需登录即可查看和克隆。

仓库已按项目提交需要由私有改为公开。提交时直接填写仓库首页 URL；如以后不再需要公开展示，可在课程验收结束后根据教师要求调整可见性。

## 后续从当前项目推送

远程地址已经配置为 `origin`。后续更新只需在项目根目录执行：

```powershell
git push
```

如需重新配置远程地址，使用：

```powershell
git remote set-url origin https://github.com/2300172382a-coder/data-structures-ai-tutor.git
git push -u origin main
```

Gitee 的操作相同，只需改成 Gitee 提供的 HTTPS 或 SSH 地址。

## 从交付 bundle 恢复后推送

`data-structures-ai-tutor-history.bundle` 是可离线克隆的完整 Git 仓库。将它放在当前目录后执行：

```powershell
git clone .\data-structures-ai-tutor-history.bundle data-structures-ai-tutor
cd .\data-structures-ai-tutor
git remote remove origin
git remote add origin https://github.com/2300172382a-coder/data-structures-ai-tutor.git
git push -u origin main
```

## 发布后检查

```powershell
git remote -v
git log --oneline -5
git status --short
```

确认网页仓库能看到 README、项目报告、15 项验收报告和完整提交历史，然后把仓库首页 URL 填入课程提交材料。不要上传 `.runtime/`、`.runtime-path`、Open WebUI 数据库、模型文件、`.env` 或任何账号密码；这些内容已经被排除在提交包之外。
