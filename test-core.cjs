const test = require("node:test");
const assert = require("node:assert/strict");
const { webcrypto } = require("node:crypto");
const { scan, reportText } = require("./core.js");
const file = (name, content) => ({name, size: Buffer.byteLength(content), arrayBuffer: async () => Uint8Array.from(Buffer.from(content)).buffer});
const digest = async buffer => Buffer.from(await webcrypto.subtle.digest("SHA-256", buffer)).toString("hex");
test("groups contents across names and counts only redundant copies", async () => {
  const r = await scan([file("one", "abc"), file("two", "abc"), file("three", "abc")], {digest});
  assert.equal(r.groups.length, 1); assert.equal(r.duplicateFiles, 2); assert.equal(r.redundantBytes, 6);
});
test("same size and filename with different bytes are not duplicates", async () => {
  const r = await scan([file("same", "abc"), file("same", "def")], {digest}); assert.equal(r.groups.length, 0);
});
test("empty files and empty selections are handled", async () => {
  assert.equal((await scan([], {digest})).totalFiles, 0);
  const r = await scan([file("a", ""), file("b", "")], {digest}); assert.equal(r.groups.length, 1); assert.equal(r.redundantBytes, 0);
});
test("oversized files are never read and are reported", async () => {
  const big = {name:"big",size:5,arrayBuffer:async()=>{throw new Error("must not read")}};
  const r = await scan([big, {...big,name:"other"}], {maxBytes:4,digest}); assert.equal(r.skipped.length, 2); assert.equal(r.readErrors, 0); assert.equal(r.hashedFiles, 0);
});
test("failed reads cannot produce a false successful comparison", async () => {
  const bad = {name:"bad",size:3,arrayBuffer:async()=>{throw new Error("unreadable")}};
  const r = await scan([bad,file("good","abc")], {digest}); assert.equal(r.readErrors, 1); assert.equal(r.groups.length, 0); assert.equal(r.skipped[0].path,"bad");
});
test("unique file sizes do not require reading", async () => {
  const r = await scan([{name:"single",size:123,arrayBuffer:async()=>{throw new Error("must not read")}}], {digest}); assert.equal(r.hashedFiles, 0); assert.equal(r.skipped.length, 0);
});
test("cancelled scans do not return partial reports", async () => {
  const c = new AbortController(); c.abort(); await assert.rejects(scan([file("a","a")], {digest,signal:c.signal}), {name:"AbortError"});
});
test("report preserves paths without allowing multiline filename spoofing", async () => {
  const a=file("a\nforged result","abc"); a.webkitRelativePath="root/a\nforged result";
  const r=await scan([a,file("copy","abc")],{digest}); const text=reportText(r);
  assert.ok(text.includes('"root/a\\nforged result"')); assert.ok(text.includes("对应重复字节数：3"));
});
test("unexpected read length and malformed digest are reported", async () => {
  const bad={name:"bad-length",size:3,arrayBuffer:async()=>new ArrayBuffer(2)};
  const r=await scan([bad,file("good","abc")],{digest:async()=>"invalid"}); assert.equal(r.readErrors,2); assert.equal(r.groups.length,0);
});
