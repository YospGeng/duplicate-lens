"""Keyed CSV comparison. Python 3.10+, standard library only. No network calls."""
import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

VERSION = "1.0.0"
MAX_BYTES = 20 * 1024 * 1024
MAX_ROWS = 100_000
MAX_FIELD = 1024 * 1024


class InvalidCSV(ValueError):
    pass


def load_csv(path, keys, delimiter=",", max_bytes=MAX_BYTES, max_rows=MAX_ROWS):
    path = Path(path)
    if not keys or len(set(keys)) != len(keys):
        raise InvalidCSV("Specify at least one distinct --key column")
    if len(delimiter) != 1 or delimiter in '\r\n"':
        raise InvalidCSV("Delimiter must be one character other than CR, LF or quote")
    with path.open("rb") as stream:
        raw = stream.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise InvalidCSV(f"{path.name}: exceeds {max_bytes} input bytes")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InvalidCSV(f"{path.name}: input must be UTF-8 (BOM allowed)") from exc
    previous_limit = csv.field_size_limit(MAX_FIELD)
    rows = {}
    try:
        reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter, strict=True)
        headers = next(reader, None)
        if not headers or any(h == "" for h in headers):
            raise InvalidCSV(f"{path.name}: missing or empty header")
        if len(set(headers)) != len(headers):
            raise InvalidCSV(f"{path.name}: duplicate headers")
        absent = [key for key in keys if key not in headers]
        if absent:
            raise InvalidCSV(f"{path.name}: missing key columns {absent!r}")
        for count, cells in enumerate(reader, 1):
            if count > max_rows:
                raise InvalidCSV(f"{path.name}: exceeds {max_rows} data records")
            if len(cells) != len(headers):
                raise InvalidCSV(f"{path.name}: wrong column count at CSV line {reader.line_num}")
            row = dict(zip(headers, cells))
            key = tuple(row[column] for column in keys)
            if any(value == "" for value in key):
                raise InvalidCSV(f"{path.name}: empty key at CSV line {reader.line_num}")
            if key in rows:
                raise InvalidCSV(f"{path.name}: duplicate key at CSV line {reader.line_num}")
            rows[key] = row
    except csv.Error as exc:
        raise InvalidCSV(f"{path.name}: invalid CSV: {exc}") from exc
    finally:
        csv.field_size_limit(previous_limit)
    return {"name": path.name, "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw), "headers": headers, "rows": rows}


def compare(before, after, keys):
    old, new = before["rows"], after["rows"]
    added = [{"key": list(k), "row": new[k]} for k in sorted(new.keys() - old.keys())]
    removed = [{"key": list(k), "row": old[k]} for k in sorted(old.keys() - new.keys())]
    changed = []
    unchanged = 0
    fields = sorted(set(before["headers"]) | set(after["headers"]))
    for key in sorted(old.keys() & new.keys()):
        changes = {f: {"before": old[key].get(f), "after": new[key].get(f)}
                   for f in fields if old[key].get(f) != new[key].get(f)}
        if changes:
            changed.append({"key": list(key), "fields": changes})
        else:
            unchanged += 1
    schema = {"added": sorted(set(after["headers"]) - set(before["headers"])),
              "removed": sorted(set(before["headers"]) - set(after["headers"]))}
    def source(data):
        return {k: data[k] for k in ("name", "sha256", "bytes", "headers")}
    return {"format": "csv-keyed-diff/v1", "tool_version": VERSION,
            "keys": keys, "before": source(before), "after": source(after),
            "schema": schema,
            "summary": {"before_rows": len(old), "after_rows": len(new),
                        "added": len(added), "removed": len(removed),
                        "changed": len(changed), "unchanged": unchanged},
            "added": added, "removed": removed, "changed": changed}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--key", action="append", required=True,
                        help="Exact header; repeat for a composite key")
    parser.add_argument("--delimiter", default=",", help="One character, or 'tab'")
    parser.add_argument("--out", type=Path, required=True, help="New JSON output file; never overwritten")
    args = parser.parse_args(argv)
    delimiter = "\t" if args.delimiter == "tab" else args.delimiter
    try:
        before = load_csv(args.before, args.key, delimiter)
        after = load_csv(args.after, args.key, delimiter)
        report = compare(before, after, args.key)
        rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        with args.out.open("x", encoding="utf-8", newline="\n") as output:
            output.write(rendered)
    except (InvalidCSV, OSError) as exc:
        print(f"Cannot compare: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
