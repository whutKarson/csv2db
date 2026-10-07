import csv
import json
import sqlite3
import tempfile
import unittest
import subprocess
import sys
from unittest.mock import patch
from pathlib import Path
from openpyxl import Workbook
from csv2db import import_file, query_file, convert


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.config = json.loads((Path(__file__).resolve().parents[1] / 'examples/sales.schema.json').read_text())
        self.header = ['订单编号', '日期', '地区', '金额（元）']
        self.rows = [['0001', '2026-09-01', '华东', '0.10'],
                     ['0002', '2026-09-30', '华东', '0.20'],
                     ['0003', '2026-10-01', '华南', '99.00']]
        self.db = self.folder / 'test.db'

    def csv_source(self, rows=None):
        path = self.folder / 'source.csv'
        with path.open('w', encoding='utf-8-sig', newline='') as handle:
            csv.writer(handle).writerows([self.header] + (self.rows if rows is None else rows))
        return path

    def imported(self):
        return import_file(self.csv_source(), self.db, self.config)

    def test_exact_money_id_date_range_and_metadata(self):
        self.imported()
        result = query_file(self.db, 'SELECT SUM(amount_minor), COUNT(*) FROM sales WHERE order_date >= :a AND order_date < :b',
                            {'a': '2026-09-01', 'b': '2026-10-01'})
        self.assertEqual(result['rows'], [(30, 2)])
        self.assertEqual(query_file(self.db, 'SELECT order_id FROM sales ORDER BY order_id')['rows'][0], ('0001',))
        report = json.loads(query_file(self.db, 'SELECT report_json FROM _import_metadata')['rows'][0][0])
        self.assertEqual(report['integrity_check'], 'ok')
        self.assertEqual(report['numeric_checks']['amount_minor'], [9930, 3])

    def test_xlsx_matches_csv(self):
        source = self.folder / 'source.xlsx'
        wb = Workbook(); ws = wb.active; ws.title = '销售明细'
        for row in [self.header] + self.rows:
            ws.append(row)
        wb.save(source); wb.close()
        import_file(source, self.db, self.config)
        self.assertEqual(query_file(self.db, 'SELECT SUM(amount_minor) FROM sales')['rows'], [(9930,)])

    def test_failure_no_published_or_temporary_database(self):
        rows = self.rows + [['0004', '2026-09-01', '华东', 'oops']]
        with self.assertRaisesRegex(ValueError, '源行 5'):
            import_file(self.csv_source(rows), self.db, self.config)
        self.assertFalse(self.db.exists())
        self.assertEqual(list(self.folder.glob('.import-*')), [])

    def test_duplicate_business_key_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            import_file(self.csv_source(self.rows + [self.rows[0]]), self.db, self.config)
        self.assertFalse(self.db.exists())

    def test_existing_output_preserved(self):
        self.imported(); before = self.db.read_bytes()
        with self.assertRaises(FileExistsError):
            self.imported()
        self.assertEqual(self.db.read_bytes(), before)

    def test_blank_balance(self):
        report = import_file(self.csv_source(self.rows + [['', '', '', '']]), self.db, self.config)
        self.assertEqual((report['read'], report['imported'], report['excluded_blank']), (4, 3, 1))

    def test_replace_applies_add_edit_delete_and_refreshes_report(self):
        old_report = self.imported()
        updated = [['0001', '2026-09-01', '华北', '12.34'],
                   ['0004', '2026-09-02', '华南', '5.00']]
        report = import_file(self.csv_source(updated), self.db, self.config, replace=True)
        self.assertEqual(query_file(self.db, 'SELECT order_id, region, amount_minor FROM sales ORDER BY order_id')['rows'],
                         [('0001', '华北', 1234), ('0004', '华南', 500)])
        self.assertNotEqual(report['source_sha256'], old_report['source_sha256'])
        saved = json.loads(query_file(self.db, 'SELECT report_json FROM _import_metadata')['rows'][0][0])
        self.assertEqual(saved['publish_mode'], 'replace')
        self.assertEqual(saved['imported'], 2)
        self.assertEqual(list(self.folder.glob('.import-*')), [])

    def test_failed_replace_keeps_old_database(self):
        self.imported(); before = self.db.read_bytes()
        with self.assertRaises(ValueError):
            import_file(self.csv_source([['0001', 'bad-date', '华东', '1.00']]),
                        self.db, self.config, replace=True)
        self.assertEqual(self.db.read_bytes(), before)
        self.assertEqual(query_file(self.db, 'SELECT COUNT(*) FROM sales')['rows'], [(3,)])
        self.assertEqual(list(self.folder.glob('.import-*')), [])

    def test_publish_failure_keeps_old_database(self):
        self.imported(); before = self.db.read_bytes()
        with patch('csv2db.os.replace', side_effect=PermissionError('busy')):
            with self.assertRaises(PermissionError):
                import_file(self.csv_source(), self.db, self.config, replace=True)
        self.assertEqual(self.db.read_bytes(), before)
        self.assertEqual(list(self.folder.glob('.import-*')), [])

    def test_replace_creates_missing_target(self):
        report = import_file(self.csv_source(), self.db, self.config, replace=True)
        self.assertEqual(report['imported'], 3)
        self.assertTrue(self.db.exists())

    def test_replace_rejects_transaction_sidecars(self):
        self.imported(); before = self.db.read_bytes()
        for suffix in ('-wal', '-shm', '-journal'):
            sidecar = Path(str(self.db) + suffix)
            sidecar.write_bytes(b'active')
            try:
                with self.assertRaisesRegex(ValueError, '事务配套文件'):
                    import_file(self.csv_source(), self.db, self.config, replace=True)
                self.assertEqual(self.db.read_bytes(), before)
            finally:
                sidecar.unlink()

    def test_replace_cannot_overwrite_source(self):
        source = self.csv_source(); before = source.read_bytes()
        with self.assertRaisesRegex(ValueError, '源文件相同'):
            import_file(source, source, self.config, replace=True)
        self.assertEqual(source.read_bytes(), before)

    def test_cli_replace(self):
        self.imported()
        source = self.csv_source([['0008', '2026-09-01', '华东', '7.00']])
        schema = self.folder / 'schema.json'
        schema.write_text(json.dumps(self.config), encoding='utf-8')
        script = Path(__file__).resolve().parents[1] / 'csv2db.py'
        result = subprocess.run([sys.executable, str(script), 'import', str(source),
                                 str(self.db), '--schema', str(schema), '--replace'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['imported'], 1)
        self.assertEqual(query_file(self.db, 'SELECT order_id, amount_minor FROM sales')['rows'], [('0008', 700)])

    def test_cli_reuses_saved_schema(self):
        self.imported()
        source = self.csv_source([['0009', '2026-09-01', '华南', '8.50']])
        script = Path(__file__).resolve().parents[1] / 'csv2db.py'
        result = subprocess.run([sys.executable, str(script), 'import', str(source),
                                 str(self.db), '--replace'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['config_source'], 'database')
        self.assertEqual(report['config'], self.config)
        self.assertEqual(query_file(self.db, 'SELECT order_id, amount_minor FROM sales')['rows'], [('0009', 850)])

    def test_first_import_requires_schema(self):
        for replace in (False, True):
            with self.assertRaisesRegex(ValueError, '首次导入'):
                import_file(self.csv_source(), self.db, replace=replace)
        self.assertFalse(self.db.exists())

    def test_reused_schema_mismatch_preserves_database(self):
        self.imported(); before = self.db.read_bytes()
        self.header[-1] = '新金额列'
        with self.assertRaisesRegex(ValueError, '源字段缺失'):
            import_file(self.csv_source(), self.db, replace=True)
        self.assertEqual(self.db.read_bytes(), before)
        self.assertEqual(list(self.folder.glob('.import-*')), [])

    def test_explicit_schema_overrides_saved_schema(self):
        self.imported()
        self.header[-1] = '新金额列'
        self.config['columns'][-1]['source'] = '新金额列'
        report = import_file(self.csv_source(), self.db, self.config, replace=True)
        self.assertEqual(report['config_source'], 'explicit')
        self.assertEqual(query_file(self.db, 'SELECT SUM(amount_minor) FROM sales')['rows'], [(9930,)])

    def test_missing_or_corrupt_metadata_requires_explicit_schema(self):
        for payload in (None, 'not-json', '{}', '{"config":null}', '{"config":{"table":"sales","columns":[null]}}'):
            with self.subTest(payload=payload):
                self.imported()
                with sqlite3.connect(self.db) as conn:
                    if payload is None:
                        conn.execute('DROP TABLE _import_metadata')
                    else:
                        conn.execute('UPDATE _import_metadata SET report_json=?', (payload,))
                before = self.db.read_bytes()
                with self.assertRaisesRegex(ValueError, '显式提供 --schema'):
                    import_file(self.csv_source(), self.db, replace=True)
                self.assertEqual(self.db.read_bytes(), before)
                self.db.unlink()

    def test_formula_rejected(self):
        source = self.folder / 'formula.xlsx'
        wb = Workbook(); ws = wb.active; ws.title = '销售明细'
        ws.append(self.header); ws.append(['0001', '2026-09-01', '华东', '=1+2'])
        wb.save(source); wb.close()
        with self.assertRaisesRegex(ValueError, '公式'):
            import_file(source, self.db, self.config)
        self.assertFalse(self.db.exists())

    def test_invalid_values(self):
        for value, kind in [('2026-02-30', 'date'), ('1.001', 'money'), ('NaN', 'real'), (123, 'text'), ('9223372036854775808', 'integer')]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                convert(value, {'type': kind})

    def test_required_missing(self):
        with self.assertRaises(ValueError):
            import_file(self.csv_source([['', '2026-09-01', '华东', '1']]), self.db, self.config)

    def test_write_attach_pragma_and_multiple_statements_denied(self):
        self.imported()
        for sql in ['DELETE FROM sales', 'DROP TABLE sales', "ATTACH DATABASE ':memory:' AS other", 'PRAGMA query_only=OFF', 'SELECT 1; SELECT 2', "SELECT load_extension('x')"]:
            with self.subTest(sql=sql), self.assertRaises((sqlite3.Error, ValueError)):
                query_file(self.db, sql)
        self.assertEqual(query_file(self.db, 'SELECT COUNT(*) FROM sales')['rows'], [(3,)])

    def test_parameter_injection_is_literal(self):
        self.imported()
        self.assertEqual(query_file(self.db, 'SELECT * FROM sales WHERE region = :r',
                                    {'r': "华东' OR 1=1 --"})['rows'], [])

    def test_truncation_and_aggregate(self):
        self.imported()
        result = query_file(self.db, 'SELECT * FROM sales', limit=1)
        self.assertTrue(result['truncated']); self.assertEqual(len(result['rows']), 1)
        self.assertEqual(query_file(self.db, 'SELECT COUNT(*) FROM sales', limit=1)['rows'], [(3,)])

    def test_query_timeout(self):
        self.imported()
        with self.assertRaises(sqlite3.OperationalError):
            query_file(self.db, 'WITH RECURSIVE t(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM t) SELECT SUM(x) FROM t', timeout=0.01)

    def test_empty_and_duplicate_header(self):
        for rows, header in [([], self.header), (self.rows, ['订单编号', '日期', '地区', '订单编号'])]:
            self.header = header
            with self.assertRaises(ValueError):
                import_file(self.csv_source(rows), self.db, self.config)

    def test_nullable_numeric_all_null(self):
        self.config['columns'][-1]['required'] = False
        report = import_file(self.csv_source([['0001', '2026-09-01', '华东', '']]), self.db, self.config)
        self.assertEqual(report['numeric_checks']['amount_minor'], (None, 0))
        self.assertEqual(query_file(self.db, 'SELECT amount_minor FROM sales')['rows'], [(None,)])

    def test_failure_after_batch_insert_rolls_back(self):
        rows = [[str(i).zfill(5), '2026-09-01', '华东', '1.00'] for i in range(1001)]
        rows.append(['bad', 'invalid-date', '华东', '1.00'])
        with self.assertRaises(ValueError):
            import_file(self.csv_source(rows), self.db, self.config)
        self.assertFalse(self.db.exists())
        self.assertEqual(list(self.folder.glob('.import-*')), [])


if __name__ == '__main__':
    unittest.main()
