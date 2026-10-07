# 机制与执行指南

## 向用户解释原理

Excel 工作表像一张可编辑的网格；数据库把选定的数据区域存成有字段和类型的表。一个工作簿可以映射为多张数据库表，但映射取决于业务粒度，并非机械地每个 Sheet 都导入。

SQLite 是嵌入式数据库引擎，程序通过库调用读取本地文件，无需常驻数据库服务器。SQL 描述筛选、关联和聚合，由引擎执行。agent 根据自然语言生成查询并调用程序，把真实执行结果解释给用户。数据库文件不包含模型，也不自动连接 agent。

这样能减少将完整表格反复放入模型上下文的需要，适合重复查询和可复核统计。原文件更新后需重新导入或执行明确的增量同步，数据库不会自行更新。

## 可落地的操作顺序

1. 读取工作簿结构，先少量抽样检查格式，再对全量数据进行类型和异常验证。
2. 确定数据区域和表头，跳过规则明确的标题、空白和合计；记录源行号。
3. 定义字段映射并显式建表，不依赖样本自动推断决定最终类型。
4. 将金额以 Decimal 按币种规则转换为整数最小单位；将日期规范化；以参数化 `executemany` 分批插入。
5. 通过事务控制成功与失败。写入失败时回滚，不发布临时库。大文件分批读取，避免整份工作簿驻留内存。
6. 核对源数据与数据库的记录数、异常数及核心指标，完成完整性检查。
7. 保存数据字典和导入报告，关闭连接后交付新的数据库快照。
8. 使用只读连接检查 schema，再执行分析查询并验证结果。

常用数据库检查：

```sql
SELECT name, sql
FROM sqlite_schema
WHERE type = 'table' AND name NOT LIKE 'sqlite_%';

-- 表名来自已确认的 schema；此处 sales 为教学示例。
PRAGMA table_info("sales");
PRAGMA integrity_check;
```

Python 只读连接示意，`db_path` 必须替换为实际绝对路径：

```python
from pathlib import Path
import sqlite3

db_path = Path("/absolute/path/analysis.db")
uri = db_path.resolve().as_uri() + "?mode=ro"
with sqlite3.connect(uri, uri=True) as conn:
    conn.execute("PRAGMA query_only=ON")
    rows = conn.execute(
        'SELECT region, SUM(amount_minor) FROM "sales" '
        'WHERE order_date >= ? AND order_date < ? GROUP BY region',
        ("2026-09-01", "2026-10-01"),
    ).fetchall()
```

以上代码展示连接和参数传递，不是完整转换器；只有真实数据库含有示例字段时才能执行。sqlite3 的连接上下文管理器管理事务，长流程还应显式 `close()` 或使用 `contextlib.closing` 及时关闭连接。

## 指标核验

| 问题 | 核验方式 |
|---|---|
| 销售额按地区汇总 | 分组之和等于同口径总额；检查币种、退货和 NULL |
| 订单数量 | 明确一行订单还是明细；核对 DISTINCT 业务键 |
| 客单价 | 同范围销售额除以订单数，分母为零时返回 NULL 并解释 |
| 多表汇总 | 核对关联前后的行数、唯一键和未匹配记录 |
| 月度趋势 | 使用起始包含、结束不包含的时间区间；说明缺失月份是否补零 |

## 导入报告最小内容

记录源路径和哈希、导入时间、依赖版本、Sheet 与范围、字段映射、业务粒度、类型和单位规则、公式缓存状态、各类记录数、异常及源行位置、关键指标对账、完整性检查结果和输出路径。按实际需要采用 Markdown 或 JSON，不要求创建无用途的附属文件。

## 官方参考

- [SQLite 单文件数据库](https://www.sqlite.org/onefile.html)
- [SQLite 数据库文件格式](https://www.sqlite.org/fileformat.html)
- [openpyxl 工作簿读取教程](https://openpyxl.readthedocs.io/en/3.1/tutorial.html)

实现时按本机安装版本核对 API；可用环境没有依赖时说明安装需求，不声称已经运行。
