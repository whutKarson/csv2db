# csv2db

将 Excel / CSV 导入持久化 SQLite 文件，通过 GitHub Copilot Agent 使用自然语言查询。脚本提供导入、校验和只读 SQL 执行，Copilot 负责理解问题与生成 SQL。

## Clone 后配置

需要 Python 3.9+、Git、VS Code 和可用的 GitHub Copilot。SQLite 随 Python 提供，无需数据库服务器。

```sh
git clone <你的仓库地址>
cd csv2db
bash setup.sh
```

进入实际 clone 目录（取决于仓库名）。setup.sh 创建本机 `.venv`、安装依赖、运行测试，并在示例数据缺失时生成数据；已有示例数据不会被覆盖。

## Copilot 操作

在 VS Code 打开整个项目文件夹，进入 Copilot Chat 的本地 Agent 模式，输入 `/skills` 检查 `excel-to-sqlite`。

> 使用 excel-to-sqlite 技能，实际查询 examples/api_metrics.db，找出阿里云平台错误率最高的 10 个 API，按百分数展示，并附 SQL。

首次导入自己的文件：

> 检查 data/my.csv 的列名和样例，生成字段配置并导入 data/my.db，核对行数和关键汇总。

更新：

> 用最新的 data/my.csv 完整更新 data/my.db，复用原配置。

自己的业务数据放入 `data/`，该目录已被 Git 忽略。`examples/` 全部为虚构测试数据，可随代码上传。

## 命令行

```sh
.venv/bin/python csv2db.py query examples/api_metrics.db 'SELECT COUNT(*) FROM api_metrics'
.venv/bin/python csv2db.py import data/my.csv data/my.db --schema data/my.schema.json
.venv/bin/python csv2db.py import data/my.csv data/my.db --replace
.venv/bin/python -m unittest discover -s tests -v
```

当前不内置自然语言 ask 命令或模型 API，Copilot Agent 调用本地脚本即可。数据库留在本地，但传给 Copilot 的字段、问题和结果会进入模型上下文。

技能入口：`.github/skills/excel-to-sqlite/SKILL.md`。详细指南见 [使用说明](使用说明.md)、[GitHub 迁移指南](迁移到Mac和Copilot.md) 和 [模拟数据说明](examples/API数据说明.md)。
