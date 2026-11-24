import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { setFlagsFromString } from "node:v8";

setFlagsFromString("--wasm-max-mem-pages=64");

const glb = readFileSync(`${process.argv[2]}/monitor.glb`);
const json = JSON.parse(glb.subarray(20, 20 + glb.readUInt32LE(12)).toString());
const binary = 28 + glb.readUInt32LE(12);
const view = json.bufferViews[json.extensions.VOICE_program.bufferView];
const program = glb.subarray(binary + view.byteOffset, binary + view.byteOffset + view.byteLength);
const node = (name) => json.nodes.findIndex((entry) => entry.name === name);

function update(cores) {
  const processes = 8;
  const bytes = Buffer.alloc(8 + 8 * 4 + cores * 12 + processes * 28);
  bytes.writeUInt32LE(cores, 0);
  bytes.writeUInt32LE(processes, 4);
  [32e9, 16e9, 0.5, 4e9, 1e9, 2e9, 60, 50].forEach((value, at) => bytes.writeFloatLE(value, 8 + at * 4));
  for (let core = 0; core < cores; core++) {
    [0.75, 2e9, 4e9].forEach((value, at) => bytes.writeFloatLE(value, 40 + core * 12 + at * 4));
  }
  for (let row = 0; row < processes; row++) {
    const at = 40 + cores * 12 + row * 28;
    [1.5, 1e9, 0.25].forEach((value, k) => bytes.writeFloatLE(value, at + k * 4));
    bytes.write("worker", at + 12);
  }
  return bytes;
}

const { instance: { exports } } = await WebAssembly.instantiate(program);
const deliver = (bytes) => {
  const at = exports.data(bytes.length);
  if (at !== 0) new Uint8Array(exports.memory.buffer, at, bytes.length).set(bytes);
  return at;
};
const record = (at, index) => new Float32Array(exports.memory.buffer, at + index * 40, 10);

const unshown = [];
for (const cores of [8, 64, 128, 8192]) {
  const bytes = update(cores);
  const at = deliver(bytes) && exports.tick(0, 0, 0, 0, 0);
  if (!at || !(record(at, node("core0_busy"))[8] > 0) || !(record(at, node("row4_fill0"))[7] > 0)) {
    unshown.push(`${cores} cores (${bytes.length} bytes)`);
  } else {
    console.log(`${cores} cores: ${bytes.length} bytes shown`);
  }
}
assert.deepEqual(unshown, [], "updates the monitor did not show");

const size = exports.memory.buffer.byteLength;
assert.notEqual(exports.data(0), 0, "an empty update was refused");
exports.tick(0, 0, 0, 0, 0);
assert.equal(exports.data(-1), 0);
assert.equal(exports.data(2 ** 31 - 1), 0, "an update past the memory the host allows was accepted");
assert.equal(exports.memory.buffer.byteLength, size);
assert.equal(exports.tick(0, 0, 0, 0, 0), 0, "a refused update reached the program");
console.log("an update past the memory the host allows is refused");
