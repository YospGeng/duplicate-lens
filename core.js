(function (root) {
  "use strict";
  const DEFAULT_LIMIT = 64 * 1024 * 1024;
  const abort = () => { const error = new Error("扫描已取消"); error.name = "AbortError"; throw error; };
  async function scan(files, options = {}) {
    const list = Array.from(files);
    const maxBytes = options.maxBytes ?? DEFAULT_LIMIT;
    if (!Number.isSafeInteger(maxBytes) || maxBytes < 0) throw new Error("单文件限制无效");
    const digest = options.digest || (async (buffer) => {
      const hash = await globalThis.crypto.subtle.digest("SHA-256", buffer);
      return Array.from(new Uint8Array(hash), b => b.toString(16).padStart(2, "0")).join("");
    });
    const sizes = new Map();
    const skipped = [];
    const groups = new Map();
    let processed = 0;
    let hashed = 0;
    let inputBytes = 0;
    let readErrors = 0;
    for (const [index, file] of list.entries()) {
      if (!Number.isSafeInteger(file.size) || file.size < 0) throw new Error("文件大小无效");
      inputBytes += file.size;
      if (!Number.isSafeInteger(inputBytes)) throw new Error("所选文件总大小超出安全计数范围");
      const item = { file, index, path: file.webkitRelativePath || file.name || `file-${index + 1}`, size: file.size };
      if (file.size > maxBytes) skipped.push({ path: item.path, size: item.size, reason: "超过单文件大小限制" });
      else {
        if (!sizes.has(file.size)) sizes.set(file.size, []);
        sizes.get(file.size).push(item);
      }
    }
    processed = skipped.length;
    const progress = () => options.onProgress?.({ processed, total: list.length, hashed });
    progress();
    for (const bucket of sizes.values()) {
      if (options.signal?.aborted) abort();
      if (bucket.length === 1) { processed++; progress(); continue; }
      for (const item of bucket) {
        if (options.signal?.aborted) abort();
        try {
          const bytes = await item.file.arrayBuffer();
          if (bytes.byteLength !== item.size) throw new Error("读取长度与文件大小不符");
          if (options.signal?.aborted) abort();
          const hash = await digest(bytes);
          if (typeof hash !== "string" || !/^[0-9a-f]{64}$/i.test(hash)) throw new Error("SHA-256 结果无效");
          const key = `${item.size}:${hash.toLowerCase()}`;
          if (!groups.has(key)) groups.set(key, { sha256: hash.toLowerCase(), size: item.size, files: [] });
          groups.get(key).files.push({ path: item.path, size: item.size, selectionIndex: item.index });
          hashed++;
        } catch (error) {
          if (error.name === "AbortError") throw error;
          readErrors++;
          skipped.push({ path: item.path, size: item.size, reason: "读取或校验失败" });
        }
        processed++; progress();
      }
    }
    if (options.signal?.aborted) abort();
    const duplicates = Array.from(groups.values()).filter(group => group.files.length > 1);
    duplicates.sort((a, b) => b.size * (b.files.length - 1) - a.size * (a.files.length - 1));
    return {
      version: "1.0.0", totalFiles: list.length, totalBytes: inputBytes, hashedFiles: hashed,
      maxBytes, readErrors, skipped, groups: duplicates,
      duplicateFiles: duplicates.reduce((sum, group) => sum + group.files.length - 1, 0),
      redundantBytes: duplicates.reduce((sum, group) => sum + group.size * (group.files.length - 1), 0),
    };
  }
  function reportText(result) {
    const lines = ["Duplicate Lens 1.0.0 — 离线文件重复检测报告", "",
      `所选文件：${result.totalFiles}`, `所选文件总字节数：${result.totalBytes}`,
      `完成 SHA-256 的文件：${result.hashedFiles}`, `重复组数：${result.groups.length}`,
      `各组保留一份时的重复份数：${result.duplicateFiles}`, `对应重复字节数：${result.redundantBytes}`,
      `跳过文件：${result.skipped.length}`, `单文件读取上限：${result.maxBytes} 字节`, "",
      "分组依据是大小与 SHA-256 相同；文件名相同不代表内容相同。",
      "本工具只读取所选文件，不删除、移动或上传文件。跳过的文件未参与比较。",
      "重复字节数不是已释放空间；不要据此自动删除程序文件或备份。", ""];
    result.groups.forEach((group, index) => {
      lines.push(`组 ${index + 1} | 每份 ${group.size} 字节 | ${group.files.length} 份`, `SHA-256: ${group.sha256}`);
      group.files.forEach(file => lines.push(`  ${JSON.stringify(file.path)} [选择序号 ${file.selectionIndex + 1}]`));
      lines.push("");
    });
    if (result.skipped.length) {
      lines.push("未参与比较：");
      result.skipped.forEach(file => lines.push(`  ${JSON.stringify(file.path)} | ${file.size} 字节 | ${file.reason}`));
    }
    return lines.join("\n");
  }
  const api = { scan, reportText, DEFAULT_LIMIT };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.DuplicateLens = api;
})(globalThis);
