# Git 仓库发布说明

项目已经在本地完成 Git 管理，`main` 分支包含完整的分阶段提交。发布到 GitHub 或 Gitee 只需要一个由项目组账号创建的空仓库。

## 直接从当前项目推送

在项目根目录执行，把示例地址替换成真实空仓库地址：

```powershell
git remote add origin https://github.com/你的账号/data-structures-ai-tutor.git
git push -u origin main
```

如果已经存在名为 `origin` 的远程地址，使用：

```powershell
git remote set-url origin https://github.com/你的账号/data-structures-ai-tutor.git
git push -u origin main
```

Gitee 的操作相同，只需改成 Gitee 提供的 HTTPS 或 SSH 地址。

## 从交付 bundle 恢复后推送

`data-structures-ai-tutor-history.bundle` 是可离线克隆的完整 Git 仓库。将它放在当前目录后执行：

```powershell
git clone .\data-structures-ai-tutor-history.bundle data-structures-ai-tutor
cd .\data-structures-ai-tutor
git remote remove origin
git remote add origin https://github.com/你的账号/data-structures-ai-tutor.git
git push -u origin main
```

## 发布后检查

```powershell
git remote -v
git log --oneline -5
git status --short
```

确认网页仓库能看到 README、项目报告、15 项验收报告和至少 5 个提交，然后把仓库首页 URL 填入课程提交材料。不要上传 `.runtime/`、`.runtime-path`、Open WebUI 数据库、模型文件、`.env` 或任何账号密码；这些内容已经被排除在提交包之外。
