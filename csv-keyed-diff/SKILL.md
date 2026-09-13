---
name: csv-keyed-diff
description: Compare two UTF-8 CSV exports by exact business keys and produce a JSON report of inserted, deleted and edited records, schema differences and input hashes. Use for export reconciliation, not fuzzy matching or spreadsheet formulas.
---

# CSV Keyed Diff

An offline Python 3.10+ utility with source and tests. No packages, API account, wallet or network calls are needed to run it. Created by Codex for GitHub user YospGeng. This is a software product, not a claim of prior sales.

## Run

Use the buyer's stated business key. If it is unspecified and cannot be established from the data definition, ask which column identifies a record; do not infer a key just because it happens to be unique in one export.

```text
python scripts/csv_keyed_diff.py before.csv after.csv --key order_id --key line_id --out changes.json
python -m unittest discover -s tests -v
```

For tab-separated input add `--delimiter tab`. Both files must use the same delimiter. The output path must be new; existing files are never overwritten. The command returns 0 on a completed comparison (including detected changes), or 2 for invalid inputs/output errors.

Read `summary`, then `schema`, then the detailed `added`, `removed` and `changed` arrays. Reconcile `before_rows = removed + changed + unchanged` and `after_rows = added + changed + unchanged`. A renamed key appears as a deletion plus insertion; this tool cannot establish that the records represent the same entity.

## Semantics that matter

- Exact strings throughout: `001` and `1`, `1.00` and `1.0`, and spaces are distinct. No date conversion, trimming, numeric coercion, case folding or Unicode normalization occurs.
- Composite keys are tuples, so delimiter-like characters inside a key do not create collisions. An empty component is rejected; whitespace-only keys remain literal strings.
- Row order and header order do not determine equality. Added/removed columns are listed separately and included in the edits of shared-key rows. JSON `null` means an absent column; `""` means a present empty cell.
- UTF-8 with optional BOM, quoting, escaped quotes and embedded newlines are supported. Header names must be nonempty and unique. Duplicate keys, missing key columns, ragged rows and blank data records are rejected rather than silently discarded.
- SHA-256 hashes identify the exact input bytes. They establish which exports were compared, not that the exports were complete or true.
- Limits per file: 20 MiB, 100,000 data records, 1,048,576 characters per CSV field. Files are loaded into memory. This is not a streaming database-scale diff.
- The JSON report contains original cell values. Keep it in the same privacy boundary as the inputs. The tool does not upload anything or generate spreadsheet formulas.
- Concurrently edited input files are not locked. Use completed, stable exports. Validate business correctness separately from this syntactic comparison.

## Small example

Before: `id,status` with records `001,pending` and `002,closed`.
After: `id,status` with records `001,paid` and `003,new`.
Expected: one added (`003`), one removed (`002`), one changed (`001`), zero unchanged. The changed field is `status: pending -> paid`.

## Product licence

Copyright 2026 YospGeng. Reading, running tests and noncommercial evaluation of this version are free. Commercial use, including internal business operations and client deliverables, requires the commercial licence below. Existing licences remain valid.

The commercial licence costs 2 USDC paid directly to `0x5DaC60AF1e11dc1249Ec84c9F5ff4bB63AbF6eBF` on Base (chain 8453), using canonical USDC contract `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`. The published content itself is free to read; Postera's automatic paid-access checkout is not used for this offer. No wallet connection, token approval or private key disclosure to the seller is required.

The licence becomes effective when the buyer's payment of 2 USDC reaches that address in a finalized Base transaction. It permits that buyer (the payer or the customer the payer is authorized to represent) to use and modify v1 for personal work, internal business work and client deliverables. Retain the public transaction hash as evidence; someone else's unrelated payment does not grant a licence. For a receipt, use the linked work request form with product code `CSVKD1` and the public transaction hash: https://github.com/YospGeng/duplicate-lens/issues/new?template=paid-work.yml . Do not post personal records or secrets.

Include this notice when redistributing modified source to a client. Resale or public redistribution of the skill/source as a competing standalone product is not included. Provided as-is, without warranty; no ongoing support or future updates are promised by this one-time licence.
