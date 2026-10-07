"""Generate 10,000 reproducible synthetic API metrics, not real API/CVE findings."""
import csv
import random
from pathlib import Path

folder = Path(__file__).resolve().parent
rng = random.Random(20261008)
platforms = ['AWS', 'Azure', 'Google Cloud', '阿里云', '腾讯云', '私有云', '本地部署']
services = ['users', 'orders', 'payments', 'inventory', 'search', 'notifications',
            'authentication', 'analytics', 'shipping', 'billing']
with (folder / 'api_metrics.csv').open('w', encoding='utf-8-sig', newline='') as handle:
    writer = csv.writer(handle)
    writer.writerow(['api 名字', 'api major version', 'api的平台', 'api的流量',
                     'api的错误率', 'api 的cve数量'])
    for index in range(10000):
        traffic = 0 if index % 250 == 0 else rng.randint(1, 5_000_000)
        error_rate = 0 if traffic == 0 else rng.choices(
            [0, rng.randint(1, 100) / 10000, rng.randint(101, 500) / 10000,
             rng.randint(501, 3000) / 10000], weights=[15, 60, 20, 5])[0]
        cves = rng.choices([0, 1, 2, 3, 5, 8, 13], weights=[55, 20, 10, 7, 4, 3, 1])[0]
        writer.writerow([f'{services[index % len(services)]}-api-{index + 1:05d}',
                         rng.randint(1, 5), platforms[index % len(platforms)],
                         traffic, f'{error_rate:.4f}', cves])
print('已生成 api_metrics.csv：10,000 条模拟记录。')
