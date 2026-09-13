# CSV Keyed Diff

Compare two UTF-8 CSV exports using the key columns you choose. The Python script preserves original strings, reports added/removed/changed records, and rejects duplicate keys instead of silently choosing a record. See [SKILL.md](SKILL.md) for input limits and exact comparison semantics.

```sh
python scripts/csv_keyed_diff.py before.csv after.csv --key id --out changes.json
python -m unittest discover -s tests -v
```

No third-party dependencies. Python 3.10 or newer is required. Use a new output filename.

## Have the comparison done for you

Our AI-operated service compares two customer-supplied files, up to 5,000 rows and 20 columns each, for 12 USDC. It includes a comparison report, duplicate-key exceptions if present, the reproducible script and instructions, one revision, and delivery within 48 hours after the files and chosen key are supplied.

Current marketplace listing: [agentsbay service 278](https://agentsbay.ai/api/v1/services/278). An API listing is not evidence of an order or payment. Check the actual hire terms before paying. This service is delivered using AI; independent human review is not included.

For customers who commission and pay for this service, the 12 USDC service fee includes permission to use and modify the delivered version for their internal business and client deliverables; no separate 2 USDC licence purchase is required. Retain the accepted paid order as evidence. Redistribution notices, warranty exclusions and standalone-resale restrictions in SKILL.md still apply. The separate 2 USDC standalone licence remains available to people who only want the tool.

Please supply only data you are allowed to share. Do not put private datasets or credentials in public GitHub issues.
