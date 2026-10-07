# 通过 GitHub 迁移到另一台 Mac

## 上传当前项目

当前文件夹尚未初始化为 Git 仓库。在 GitHub 创建空仓库，例如 csv2db，不自动生成 README、License 或 .gitignore（项目已有 README 和 .gitignore）。然后在项目根目录运行，将 URL 换成你的仓库地址：

```sh
git init
git branch -M main
git add .
git status --short
git commit -m "Add SQLite tools and Copilot skill"
git remote add origin https://github.com/YOUR_ACCOUNT/csv2db.git
git push -u origin main
```

检查 git status 中的提交清单。`.venv`、缓存、旧 ZIP、环境变量文件和 `data/` 下的业务数据被忽略；`examples/` 的模拟 CSV 与数据库可随项目上传。真实业务数据请放 data/，不要放 examples/。

`.github` 是隐藏目录，Git 会包含它；Finder 可按 Command + Shift + . 显示。push 身份验证使用你配置的 GitHub 凭证。

## 新 Mac clone 后使用

准备 Python 3.9+、Git、VS Code 和 GitHub Copilot。在新 Mac 执行：

```sh
git clone https://github.com/YOUR_ACCOUNT/csv2db.git
cd csv2db
bash setup.sh
```

进入实际 clone 目录。setup.sh 创建本机虚拟环境、安装 requirements.txt、运行测试并查询示例库；已有示例 CSV 和数据库不会被覆盖。SQLite 随 Python 提供，无需另装数据库服务器。没有 Python 时从 [Python macOS 下载页](https://www.python.org/downloads/macos/) 安装仍受维护的 Python 3。

用 VS Code 打开整个项目文件夹，登录 Copilot，选择本地 Agent 模式。输入 /skills 检查 excel-to-sqlite，或用 /excel-to-sqlite 明确调用。执行终端命令时按 VS Code 的权限提示处理。

> 使用 excel-to-sqlite 技能，实际查询 examples/api_metrics.db，找出阿里云错误率最高的 10 个 API，并附 SQL。

示例数据有 10,000 行，第一名为 shipping-api-06129，错误率 29.65%。首次导入自己的文件时由 agent 生成 schema；更新时使用 --replace 复用配置。

## 后续同步

代码修改后 commit、push，另一台 Mac 执行 git pull。依赖变化后重新运行 bash setup.sh。data/ 不随 Git 同步，业务 CSV 和数据库需单独共享。

技能入口为 `.github/skills/excel-to-sqlite/SKILL.md`，其引用文件也在该目录中。不识别技能时检查打开的项目目录、更新 VS Code/Copilot，也可直接让 Copilot 读取这个文件和使用说明。

原数据库报告中的旧路径只是历史来源，不影响查询；新导入会记录新机器路径。不要复制旧 .venv，在新机器重建。

Copilot 提供模型能力，脚本不需要额外模型 API Key；但发送给 Copilot 的字段信息和查询结果会进入模型上下文，并非全部离线。

参考：[VS Code Agent Skills](https://code.visualstudio.com/docs/agent-customization/agent-skills)。
