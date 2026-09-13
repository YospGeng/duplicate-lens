# Duplicate Lens

A browser-based duplicate file checker. Files are processed locally using SHA-256; the application does not upload, delete, or move them.

**[Try the live demo](https://duplicate-lens-yospgeng.lospgeng.chatgpt.site)** · **[Request customization](https://github.com/YospGeng/duplicate-lens/issues/new?template=customization.yml)**

For a larger software task, see the **[fixed-scope services: $60 / $120 / $200](SERVICES.md)** and **[send a work brief](https://github.com/YospGeng/duplicate-lens/issues/new?template=paid-work.yml)**. Work is delivered with source and verification notes. The introductory offer below remains available on its original terms.

## Ready-to-use data tool

**[CSV Keyed Diff](https://postera.dev/post/77918c1d-6e32-4285-adbc-31fb3af46af2)** compares two CSV exports by business keys and reports inserted, deleted and edited rows, schema changes and input hashes. Complete offline Python source and 13 tests are available for free evaluation. Commercial use of v1 is licensed for **2 USDC**, paid directly on Base under the included licence; the post's read access is free.

[See fictional inputs and the actual output](https://gist.github.com/YospGeng/406bdde4c5a53398f699dc51077bc614) · [Ask about the tool or request a licence receipt](https://github.com/YospGeng/duplicate-lens/issues/new?template=csv-tool.yml). Built and tested by Codex for YospGeng; no prior sales or customer endorsements are claimed.

## First customization: 1 USDC

The first accepted customization order includes a title change, two theme colors, a report heading, source files, and one agreed revision. Open a customization issue with your requirements. We agree scope and delivery timing before work begins; payment follows acceptance, in USDC on Ethereum mainnet. An inquiry is not a confirmed order. Do not post personal files, bank details, or wallet secrets.

首单定制价为 **1 USDC**：修改标题、两种主题颜色和报告标题，交付源码，并包含一次约定范围内的修改。请在本仓库创建需求 Issue；双方确认范围和交付时间后开工，验收后付款。

## Use

Download `index.html` and `core.js` into the same directory, or use the live demo. Select a folder or multiple files, then export a text report. Folder selection depends on browser support. Local file opening has not been separately verified; the hosted and local HTTP versions have been tested.

- Groups equal-size files by SHA-256; matching names alone are not considered duplicates.
- Reads files sequentially, with a 64 MiB per-file limit. Skipped and failed files are listed explicitly.
- Duplicate bytes mean the redundant copies if one copy per group were retained, not freed disk space.
- Scans only files exposed by the browser's picker; inaccessible files and links may be omitted.
- Does not persist results in browser storage. Demo files are synthetic.

## Validation

With Node.js installed:

```sh
node --test test-core.cjs
```

Nine automated tests cover grouping, empty files, limits, read failures, cancellation, report escaping, and invalid inputs. Browser checks covered demo scanning, selected synthetic files, and report export. No customer outcome or payment is implied by these checks.

## Usage permission

Copyright (c) 2026 YospGeng. You may download and use this published version for personal or internal evaluation. Redistribution and commercial customization licensing are agreed separately with the author. This software is provided as-is, without warranty. Paid customization covers the agreed work; it is not a charge for using the demo.
