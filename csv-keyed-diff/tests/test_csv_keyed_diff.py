import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from csv_keyed_diff import InvalidCSV, compare, load_csv, main


class KeyedDiffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def file(self, name, content):
        path = self.root / name
        path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
        return path

    def diff(self, old, new, keys=None, delimiter=","):
        keys = keys or ["id"]
        a = load_csv(self.file("old.csv", old), keys, delimiter)
        b = load_csv(self.file("new.csv", new), keys, delimiter)
        return compare(a, b, keys)

    def test_insert_delete_edit_and_unchanged(self):
        r = self.diff("id,v\n1,old\n2,delete\n4,same\n", "id,v\n1,new\n3,insert\n4,same\n")
        self.assertEqual(r["summary"], dict(before_rows=3, after_rows=3, added=1, removed=1, changed=1, unchanged=1))
        self.assertEqual(r["changed"][0]["fields"]["v"], {"before": "old", "after": "new"})

    def test_reordering_records_and_headers_is_not_a_change(self):
        r = self.diff("id,v\n2,B\n1,A\n", "v,id\nA,1\nB,2\n")
        self.assertEqual(r["summary"]["unchanged"], 2)
        self.assertEqual(r["changed"], [])

    def test_leading_zero_keys_and_numeric_strings_stay_distinct(self):
        r = self.diff("id,v\n001,1.00\n1,1\n", "id,v\n1,1\n001,1.0\n")
        self.assertEqual(r["changed"][0]["key"], ["001"])
        self.assertEqual(r["summary"]["unchanged"], 1)

    def test_composite_keys_cannot_collide_by_separator(self):
        text = "a,b,v\nx|y,z,one\nx,y|z,two\n"
        r = self.diff(text, text, ["a", "b"])
        self.assertEqual(r["summary"]["unchanged"], 2)

    def test_utf8_bom_quotes_comma_and_multiline(self):
        text = '\ufeffid,v\n猫,"hello,\n""世界"""\n'
        r = self.diff(text, text)
        self.assertEqual(r["summary"]["unchanged"], 1)
        self.assertEqual(r["before"]["sha256"], hashlib.sha256(text.encode()).hexdigest())

    def test_schema_added_empty_cell_differs_from_absent(self):
        r = self.diff("id,old\n1,\n", "id,new\n1,\n")
        self.assertEqual(r["schema"], {"added": ["new"], "removed": ["old"]})
        self.assertEqual(r["changed"][0]["fields"]["new"], {"before": None, "after": ""})

    def test_empty_data_is_valid_but_empty_file_is_not(self):
        self.assertEqual(self.diff("id,v\n", "id,v\n")["summary"]["before_rows"], 0)
        with self.assertRaises(InvalidCSV):
            load_csv(self.file("empty.csv", ""), ["id"])

    def test_reject_duplicate_headers_keys_missing_and_blank_keys(self):
        for text in ["id,id\n1,2\n", "id,v\n1,a\n1,b\n", "x,v\n1,a\n", "id,v\n,a\n", "id,\n1,a\n"]:
            with self.subTest(text=text), self.assertRaises(InvalidCSV):
                load_csv(self.file("bad.csv", text), ["id"])

    def test_reject_short_long_blank_and_unclosed_records(self):
        for text in ["id,v\n1\n", "id,v\n1,a,b\n", "id,v\n\n", 'id,v\n1,"unclosed']:
            with self.subTest(text=text), self.assertRaises(InvalidCSV):
                load_csv(self.file("bad.csv", text), ["id"])

    def test_limits_encoding_and_duplicate_key_arguments(self):
        p = self.file("in.csv", "id,v\n1,a\n2,b\n")
        for kwargs in [{"max_bytes": 3}, {"max_rows": 1}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(InvalidCSV):
                load_csv(p, ["id"], **kwargs)
        with self.assertRaises(InvalidCSV):
            load_csv(p, ["id", "id"])
        with self.assertRaises(InvalidCSV):
            load_csv(self.file("encoding.csv", b"id,v\n1,\xff"), ["id"])

    def test_tabs_and_whitespace_are_preserved(self):
        r = self.diff("id\tv\n1\t x\n", "id\tv\n1\tx\n", delimiter="\t")
        self.assertEqual(r["changed"][0]["fields"]["v"]["before"], " x")

    def test_cli_new_file_and_no_overwrite(self):
        a = self.file("before.csv", "id,v\n1,a\n")
        b = self.file("after.csv", "id,v\n1,b\n")
        out = self.root / "result.json"
        argv = [str(a), str(b), "--key", "id", "--out", str(out)]
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(argv), 0)
            first = out.read_bytes()
            self.assertEqual(main(argv), 2)
        self.assertEqual(out.read_bytes(), first)
        self.assertEqual(json.loads(first)["summary"]["changed"], 1)

    def test_invalid_input_creates_no_report(self):
        a = self.file("before.csv", "id,v\n1,a\n1,b\n")
        b = self.file("after.csv", "id,v\n1,b\n")
        out = self.root / "never.json"
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main([str(a), str(b), "--key", "id", "--out", str(out)]), 2)
        self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
