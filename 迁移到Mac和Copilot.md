# 通过 GitHub 迁移到另一台 Mac

## 仓库与本机登录

项目已初始化并发布到公开仓库 [whutKarson/csv2db](https://github.com/whutKarson/csv2db)，默认分支 main，origin 指向该仓库。本机 GitHub CLI 安装在 ~/.local/bin/gh；GitHub 登录凭证保存在 macOS 钥匙串，并已配置 Git 使用 gh 凭证。

新终端可直接运行 gh；当前终端尚未更新 PATH 时使用 ~/.local/bin/gh。可用 gh auth status 验证登录，不要运行输出完整 token 的命令或将凭证写入仓库。

`.venv`、缓存、旧 ZIP、环境变量文件和 `data/` 下的业务数据被忽略；examples/ 仅包含虚构测试数据。

## 新 Mac clone 后使用

准备 Python 3.9+、Git、VS Code 和 GitHub Copilot。在新 Mac 执行：

```sh
git clone https://github.com/whutKarson/csv2db.git
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

新 Mac 使用私有仓库或需要推送时，另行安装 GitHub CLI 并运行 gh auth login，通过自己的浏览器登录；本机钥匙串凭证不会随 clone 迁移。这个仓库是公开的，只读 clone 不需要 Token。
