"""Create synthetic sales data; contains no real customer information."""
import csv
from pathlib import Path
from openpyxl import Workbook

folder = Path(__file__).resolve().parent
rows = [
    ['订单编号', '日期', '地区', '金额（元）'],
    ['0001', '2026-09-01', '华东', '100.10'],
    ['0002', '2026-09-15', '华东', '200.20'],
    ['0003', '2026-09-30', '华南', '50.00'],
    ['0004', '2026-10-01', '华东', '999.00'],
    ['0005', '2026-09-20', '华南', '-10.00'],
    ['0006', '2026-08-31', '华北', '888.00'],
    ['0007', '2026-09-21', '华北', '0.00'],
]
workbook = Workbook()
sheet = workbook.active
sheet.title = '销售明细'
for row in rows:
    sheet.append(row)
workbook.save(folder / 'sales.xlsx')
with (folder / 'sales.csv').open('w', encoding='utf-8-sig', newline='') as handle:
    csv.writer(handle).writerows(rows)
print('已生成 sales.xlsx 和 sales.csv；9 月总额应为 340.30 元，5 笔订单。')
