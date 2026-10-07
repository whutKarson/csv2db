# API 模拟测试数据

`api_metrics.csv` 包含 10,000 条记录及 6 个指定字段；`api_metrics.db` 中对应表名为 `api_metrics`。这些 API 和 CVE 数量完全虚构，不代表真实漏洞扫描结果。

| CSV 字段 | 数据库字段 | 含义 |
|---|---|---|
| api 名字 | api_name | 唯一模拟 API 名称 |
| api major version | major_version | 主版本号，1–5 |
| api的平台 | platform | 7 类部署平台 |
| api的流量 | traffic | 同一模拟日内的请求次数，0–5,000,000 |
| api的错误率 | error_rate | 错误请求比例，0–1；0.01 表示 1% |
| api 的cve数量 | cve_count | 模拟关联 CVE 数量，0–13 |

无请求的 API 错误率约定为 0。数据包含零流量、零错误率、高错误率和不同 CVE 数量，方便筛选、排序和聚合。汇总错误率应使用 `SUM(traffic * error_rate) / SUM(traffic)`，不要把 API 错误率简单平均当作全平台请求错误率。错误率保留四位小数，推算错误请求数只是估算，可能不是整数。

生成脚本 `make_api_data.py` 使用固定随机种子 20261008，可复现。

```sh
.venv/bin/python examples/make_api_data.py
.venv/bin/python csv2db.py import examples/api_metrics.csv examples/api_metrics.db --schema examples/api_metrics.schema.json

# 此后重新生成或更新 CSV，复用数据库里的配置
.venv/bin/python csv2db.py import examples/api_metrics.csv examples/api_metrics.db --replace
```

数据库额外的 `_source_row` 字段用于追溯 CSV 行号，`_import_metadata` 表保存导入报告。
