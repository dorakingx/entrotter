// Separate trace_version family. Imported bytes never select code or an RPC URL.
export const MAX_TRACE_BYTES = 8 * 1024 * 1024;
const MAX_INPUT_BYTES = 256 * 1024;
const RECEIPT_KEYS = [
  "gasUsed",
  "cumulativeGasUsed",
  "effectiveGasPrice",
  "transactionIndex",
  "type",
  "status",
  "transactionHash",
  "from",
  "logsBloom",
  "to",
  "contractAddress",
  "logs",
];
/** @param {unknown} value @returns {Record<string, unknown>} */
function object(value) {
  if (!value || typeof value !== "object" || Array.isArray(value))
    fail("object");
  return /** @type {Record<string, unknown>} */ (value);
}
/** @returns {never} */
function fail(detail) {
  throw new Error(`Invalid transaction-prefix report: ${detail}.`);
}
/** @param {unknown} value @param {string[]} keys */
function exact(value, keys) {
  const result = object(value);
  if (
    Object.keys(result).length !== keys.length ||
    keys.some((k) => !Object.hasOwn(result, k))
  )
    fail("unexpected or missing fields");
  return result;
}
/** @param {unknown} value @param {number} [min] @param {number} [max] @returns {number} */
function integer(value, min = 0, max = Number.MAX_SAFE_INTEGER) {
  if (
    typeof value !== "number" ||
    !Number.isSafeInteger(value) ||
    value < min ||
    value > max
  )
    fail("integer outside exact browser range");
  return /** @type {number} */ (value);
}
/** @param {unknown} value @param {number} max @param {number} [min] @returns {unknown[]} */
function array(value, max, min = 0) {
  if (!Array.isArray(value) || value.length < min || value.length > max)
    fail("array limit");
  return /** @type {unknown[]} */ (value);
}
/** @param {unknown} value @param {number} [size] @param {number} [limit] @returns {string} */
function bytes(value, size, limit = 65536) {
  if (
    typeof value !== "string" ||
    !/^0x(?:[0-9a-fA-F]{2})*$/.test(value) ||
    (value.length - 2) / 2 > limit ||
    (size !== undefined && value.length !== size * 2 + 2)
  )
    fail("hex bytes");
  return /** @type {string} */ (value);
}
/** @param {unknown} value @returns {bigint} */
function quantity(value) {
  if (
    typeof value !== "string" ||
    !/^0x(?:0|[1-9a-fA-F][0-9a-fA-F]{0,63})$/.test(value)
  )
    fail("hex quantity");
  return BigInt(/** @type {string} */ (value));
}
/** Python's finite float JSON spelling for the runtime metadata field. @param {number} value */
function pythonFloat(value) {
  if (value === 0) return Object.is(value, -0) ? "-0.0" : "0.0";
  const magnitude = Math.abs(value);
  if (magnitude < 1e-4 || magnitude >= 1e16) {
    const [mantissa, exponent] = value.toExponential().split("e");
    const power = Number(exponent);
    return (
      mantissa +
      "e" +
      (power < 0 ? "-" : "+") +
      String(Math.abs(power)).padStart(2, "0")
    );
  }
  const decimal = String(value);
  return decimal.includes(".") ? decimal : decimal + ".0";
}

/** @param {unknown} value @param {boolean} runtimeFloat @returns {string} */
export function traceCanonical(value, runtimeFloat = true) {
  if (Array.isArray(value))
    return (
      "[" +
      value.map((item) => traceCanonical(item, runtimeFloat)).join(",") +
      "]"
    );
  if (value !== null && typeof value === "object")
    return (
      "{" +
      Object.keys(value)
        .sort()
        .map((k) => {
          const item = object(value)[k];
          return (
            traceCanonical(k, runtimeFloat) +
            ":" +
            (k === "runtime_seconds" && typeof item === "number" && runtimeFloat
              ? pythonFloat(item)
              : traceCanonical(item, runtimeFloat))
          );
        })
        .join(",") +
      "}"
    );
  if (typeof value === "number" && !Number.isFinite(value))
    fail("non-finite number");
  const result = JSON.stringify(value);
  if (result === undefined) fail("JSON value");
  return /** @type {string} */ (result).replace(
    /[\u007f-\uffff]/g,
    (c) => "\\u" + c.charCodeAt(0).toString(16).padStart(4, "0"),
  );
}
function equal(a, b) {
  return traceCanonical(a) === traceCanonical(b);
}
function identity(a, b) {
  return a === null || b === null
    ? a === b
    : typeof a === "string" &&
        typeof b === "string" &&
        a.toLowerCase() === b.toLowerCase();
}
function byteSize(value) {
  return new TextEncoder().encode(traceCanonical(value)).byteLength;
}
/** Match Python/JSON Schema codepoint limits without unbounded allocation. @param {unknown} value @param {number} limit */
function boundedText(value, limit) {
  if (typeof value !== "string" || !value.length || value.length > 2 * limit)
    return false;
  let count = 0;
  const iterator = value[Symbol.iterator]();
  while (!iterator.next().done) if (++count > limit) return false;
  return true;
}
/** @param {unknown} value */
function source(value, parent = false) {
  const s = exact(value, ["chain_id", "block_number", "block_hash"]);
  if (s.chain_id !== 1) fail("Ethereum mainnet source required");
  integer(s.block_number, parent ? 0 : 1);
  bytes(s.block_hash, 32);
  return s;
}

// Decode the signed wire envelope to bind type/nonce/destination to displayed data.
// This is not signature recovery, Keccak authentication or consensus execution.
/** @param {string} raw */
function envelope(raw) {
  const wire = Uint8Array.from(raw.slice(2).match(/../g) || [], (b) =>
    parseInt(b, 16),
  );
  if (!wire.length) fail("empty signed transaction");
  const kind = wire[0] <= 2 ? wire[0] : 0;
  if (wire[0] <= 2 && kind === 0) fail("unsupported typed transaction");
  let at = kind ? 1 : 0;
  /** @typedef {Uint8Array | RLPItem[]} RLPItem */
  /** @returns {RLPItem} */
  function decode(depth = 0) {
    if (depth > 4 || at >= wire.length) fail("RLP depth or truncation");
    const prefix = wire[at++];
    if (prefix < 128) return Uint8Array.of(prefix);
    const list = prefix >= 192;
    const short = list ? 192 : 128;
    const long = list ? 247 : 183;
    let length = prefix - short;
    if (prefix > long) {
      const n = prefix - long;
      if (n > 3 || at + n > wire.length || wire[at] === 0) fail("RLP length");
      length = 0;
      for (let i = 0; i < n; i++) length = length * 256 + wire[at++];
      if (length < 56) fail("noncanonical RLP length");
    }
    const end = at + length;
    if (end > wire.length) fail("RLP truncation");
    if (!list) {
      const part = wire.slice(at, end);
      at = end;
      if (part.length === 1 && part[0] < 128) fail("noncanonical RLP string");
      return part;
    }
    const result = [];
    while (at < end) result.push(decode(depth + 1));
    if (at !== end) fail("RLP list boundary");
    return result;
  }
  const decoded = decode();
  if (
    at !== wire.length ||
    !Array.isArray(decoded) ||
    decoded.length !== (kind === 0 ? 9 : kind === 1 ? 11 : 12)
  )
    fail("signed envelope");
  /** @param {unknown} part @returns {Uint8Array} */
  function scalar(part) {
    if (!(part instanceof Uint8Array)) fail("RLP scalar");
    return /** @type {Uint8Array} */ (part);
  }
  function number(part) {
    const b = scalar(part);
    if (b.length > 32 || (b.length && b[0] === 0)) fail("RLP integer");
    return b.reduce((n, v) => n * 256n + BigInt(v), 0n);
  }
  const nonce = number(decoded[kind ? 1 : 0]);
  const gas = number(decoded[kind === 0 ? 2 : kind === 1 ? 3 : 4]);
  if (gas < 21000n || gas > 30000000n) fail("signed gas limit");
  number(decoded[kind === 0 ? 1 : 2]);
  if (kind === 2) number(decoded[3]);
  number(decoded[kind === 0 ? 4 : kind === 1 ? 5 : 6]);
  const dest = scalar(decoded[kind === 0 ? 3 : kind === 1 ? 4 : 5]);
  if (dest.length !== 0 && dest.length !== 20) fail("signed destination");
  const payload = scalar(decoded[kind === 0 ? 5 : kind === 1 ? 6 : 7]);
  if (payload.length > 65536) fail("calldata limit");
  if (kind && number(decoded[0]) !== 1n) fail("signed chain ID");
  const v = number(decoded[decoded.length - 3]);
  if (!(kind ? [0n, 1n] : [27n, 28n, 37n, 38n]).includes(v))
    fail("signature parity/chain");
  const r = number(decoded[decoded.length - 2]),
    s = number(decoded[decoded.length - 1]);
  const curve =
    0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141n;
  if (r === 0n || r >= curve || s === 0n || s > curve / 2n)
    fail("signature scalars");
  if (kind) {
    const access = decoded[kind === 1 ? 7 : 8];
    if (!Array.isArray(access) || access.length > 256) fail("access list");
    let keys = 0;
    for (const row of access) {
      if (
        !Array.isArray(row) ||
        row.length !== 2 ||
        scalar(row[0]).length !== 20 ||
        !Array.isArray(row[1])
      )
        fail("access entry");
      for (const key of /** @type {unknown[]} */ (row[1])) {
        if (scalar(key).length !== 32) fail("access key");
        keys++;
      }
    }
    if (keys > 256) fail("access key limit");
    if (kind === 2 && number(decoded[2]) > number(decoded[3]))
      fail("priority fee");
  }
  return {
    type: "0x" + kind.toString(16),
    nonce,
    gas,
    to: dest.length
      ? "0x" + Array.from(dest, (b) => b.toString(16).padStart(2, "0")).join("")
      : null,
  };
}

/** @param {unknown} value */
function receipt(value) {
  const r = exact(value, RECEIPT_KEYS);
  for (const key of [
    "gasUsed",
    "cumulativeGasUsed",
    "effectiveGasPrice",
    "transactionIndex",
  ])
    quantity(r[key]);
  if (
    !["0x0", "0x1", "0x2"].includes(/** @type {string} */ (r.type)) ||
    !["0x0", "0x1"].includes(/** @type {string} */ (r.status))
  )
    fail("receipt type/status");
  bytes(r.transactionHash, 32);
  bytes(r.from, 20);
  bytes(r.logsBloom, 256);
  for (const key of ["to", "contractAddress"])
    if (r[key] !== null) bytes(r[key], 20);
  for (const item of array(r.logs, 512)) {
    const log = exact(item, ["address", "topics", "data"]);
    bytes(log.address, 20);
    bytes(log.data);
    for (const topic of array(log.topics, 4)) bytes(topic, 32);
  }
  if (byteSize(r) > MAX_INPUT_BYTES) fail("receipt byte limit");
  if (
    quantity(r.gasUsed) < 21000n ||
    quantity(r.gasUsed) > quantity(r.cumulativeGasUsed) ||
    (r.to !== null && r.contractAddress !== null) ||
    (r.status === "0x0" &&
      (r.contractAddress !== null ||
        array(r.logs, 512).length ||
        r.logsBloom !== "0x" + "00".repeat(256)))
  )
    fail("receipt contradictions");
  return r;
}

/** Validate every displayed field and its relationships, before computing integrity. @param {unknown} input */
export function traceViewModel(input) {
  const report = exact(input, [
    "trace_version",
    "execution_kind",
    "plan",
    "source",
    "baseline",
    "candidate",
    "baseline_verified",
    "runtime_seconds",
    "assumptions",
    "artifact_id",
  ]);
  if (
    report.trace_version !== "0.1.0" ||
    report.execution_kind !== "canonical_transaction_prefix_replay" ||
    typeof report.artifact_id !== "string" ||
    !/^[a-f0-9]{64}$/.test(report.artifact_id)
  )
    fail("version or digest");
  if (byteSize(report) > MAX_TRACE_BYTES) fail("8 MiB report limit");
  const plan = exact(report.plan, [
    "trace_version",
    "source",
    "through_index",
    "skip_indices",
  ]);
  if (plan.trace_version !== "0.1.0") fail("plan version");
  const pin = source(plan.source),
    last = integer(plan.through_index, 0, 31);
  const skipped = array(plan.skip_indices, 32).map((i) => integer(i, 0, last));
  if (skipped.some((i, n) => n > 0 && i <= skipped[n - 1]))
    fail("sorted unique skip indices");
  const captured = exact(report.source, [
    "parent",
    "header",
    "inputs",
    "block_transaction_count",
  ]);
  const parent = source(captured.parent, true);
  if (parent.block_number !== /** @type {number} */ (pin.block_number) - 1)
    fail("pinned parent number");
  const header = exact(captured.header, [
    "timestamp",
    "gas_limit",
    "base_fee",
    "coinbase",
    "prevrandao",
  ]);
  integer(header.timestamp, 1681338455, 1710338134);
  integer(header.gas_limit, 21000, 30000000);
  integer(header.base_fee);
  bytes(header.coinbase, 20);
  bytes(header.prevrandao, 32);
  integer(captured.block_transaction_count, last + 1);
  const inputs = array(captured.inputs, 32, 1).map((item, index) => {
    const tx = exact(item, [
      "index",
      "hash",
      "sender",
      "nonce",
      "raw",
      "original_receipt",
    ]);
    if (integer(tx.index, 0, 31) !== index) fail("original prefix order");
    bytes(tx.hash, 32);
    bytes(tx.sender, 20);
    integer(tx.nonce);
    const raw = bytes(tx.raw, undefined, 131071),
      signed = envelope(raw),
      original = receipt(tx.original_receipt);
    if (
      BigInt(/** @type {number} */ (tx.nonce)) !== signed.nonce ||
      original.type !== signed.type ||
      !identity(original.to, signed.to) ||
      !identity(original.transactionHash, tx.hash) ||
      !identity(original.from, tx.sender) ||
      quantity(original.transactionIndex) !== BigInt(index)
    )
      fail("original signed receipt binding");
    return {
      ...tx,
      index,
      hash: bytes(tx.hash, 32),
      sender: bytes(tx.sender, 20),
      nonce: integer(tx.nonce),
      original_receipt: original,
      signed,
    };
  });
  if (inputs.length !== last + 1 || byteSize(captured.inputs) > MAX_INPUT_BYTES)
    fail("prefix/input byte limit");
  if (
    new Set(inputs.map((tx) => String(tx.hash).toLowerCase())).size !==
    inputs.length
  )
    fail("duplicate transaction identity");
  const originalNonces = new Map();
  let originalGas = 0n;
  for (const tx of inputs) {
    if (
      originalNonces.has(tx.sender.toLowerCase()) &&
      tx.nonce !== originalNonces.get(tx.sender.toLowerCase())
    )
      fail("original sender nonce sequence");
    originalNonces.set(
      tx.sender.toLowerCase(),
      integer(/** @type {number} */ (tx.nonce) + 1),
    );
    originalGas += quantity(tx.original_receipt.gasUsed);
    if (
      quantity(tx.original_receipt.gasUsed) > tx.signed.gas ||
      quantity(tx.original_receipt.cumulativeGasUsed) !== originalGas ||
      originalGas > BigInt(/** @type {number} */ (header.gas_limit))
    )
      fail("original cumulative gas");
  }
  if (
    typeof report.runtime_seconds !== "number" ||
    !Number.isFinite(report.runtime_seconds) ||
    report.runtime_seconds < 0 ||
    typeof report.baseline_verified !== "boolean"
  )
    fail("runtime/verification flag");
  const assumptions = array(report.assumptions, 32, 1).map((s) => {
    if (!boundedText(s, 4000)) fail("assumption");
    return /** @type {string} */ (s);
  });
  const initial = new Map();
  function branch(value, candidate) {
    const b = exact(value, [
      "anvil_version",
      "outcomes",
      "matches_original_receipts",
    ]);
    if (
      !boundedText(b.anvil_version, 1000) ||
      typeof b.matches_original_receipts !== "boolean"
    )
      fail("branch metadata");
    const outcomes = array(b.outcomes, 32, 1);
    if (outcomes.length !== inputs.length) fail("outcome prefix length");
    const nonces = new Map(initial);
    let minedIndex = 0,
      cumulative = 0n;
    const rows = outcomes.map((item, index) => {
      const o = object(item),
        tx = inputs[index],
        original = tx.original_receipt;
      const keys = ["index", "hash", "status"];
      if (o.status === "executed") keys.push("receipt", "differing_fields");
      else if (o.status === "nonce_conflict")
        keys.push("expected_nonce", "original_nonce");
      else if (
        !["skipped", "rejected", "not_mined"].includes(
          /** @type {string} */ (o.status),
        )
      )
        fail("terminal outcome");
      exact(o, keys);
      if (
        o.index !== index ||
        !identity(o.hash, tx.hash) ||
        (o.status === "skipped") !== (candidate && skipped.includes(index))
      )
        fail("outcome/skip binding");
      if (!nonces.has(tx.sender.toLowerCase())) {
        const start =
          o.status === "nonce_conflict" ? integer(o.expected_nonce) : tx.nonce;
        nonces.set(tx.sender.toLowerCase(), start);
        initial.set(tx.sender.toLowerCase(), start);
      }
      const expected = nonces.get(tx.sender.toLowerCase());
      if (o.status === "nonce_conflict") {
        if (
          integer(o.original_nonce) !== tx.nonce ||
          integer(o.expected_nonce) !== expected ||
          expected === tx.nonce
        )
          fail("nonce conflict");
      } else if (o.status !== "skipped") {
        if (expected !== tx.nonce) fail("missing nonce conflict");
        if (o.status !== "rejected")
          nonces.set(tx.sender.toLowerCase(), integer(expected + 1));
      }
      if (o.status !== "executed")
        return { ...o, status: o.status, receipt: null, differing_fields: [] };
      const actual = receipt(o.receipt);
      if (
        !identity(actual.transactionHash, tx.hash) ||
        !identity(actual.from, tx.sender) ||
        actual.type !== tx.signed.type ||
        !identity(actual.to, tx.signed.to) ||
        quantity(actual.transactionIndex) !== BigInt(minedIndex++)
      )
        fail("executed receipt identity/order");
      cumulative += quantity(actual.gasUsed);
      if (
        quantity(actual.gasUsed) > tx.signed.gas ||
        quantity(actual.cumulativeGasUsed) !== cumulative ||
        cumulative > BigInt(/** @type {number} */ (header.gas_limit))
      )
        fail("branch cumulative gas");
      const declared = array(o.differing_fields, 12);
      const differences = RECEIPT_KEYS.filter(
        (key) => !equal(actual[key], original[key]),
      );
      if (
        new Set(declared).size !== declared.length ||
        !equal([...declared].sort(), [...differences].sort())
      )
        fail("declared receipt differences");
      return {
        ...o,
        status: o.status,
        receipt: actual,
        differing_fields: differences,
      };
    });
    const matches = rows.every(
      (o) => o.status === "executed" && o.differing_fields.length === 0,
    );
    if (b.matches_original_receipts !== matches)
      fail("branch verification claim");
    return { anvil_version: b.anvil_version, rows, matches };
  }
  const baseline = branch(report.baseline, false),
    candidate = branch(report.candidate, true);
  if (report.baseline_verified !== baseline.matches)
    fail("baseline verification claim");
  return {
    report,
    pin,
    parent,
    header,
    inputs,
    baseline,
    candidate,
    assumptions,
  };
}

/** @param {unknown} input */
export async function validateTraceReport(input) {
  const view = traceViewModel(structuredClone(input));
  const { artifact_id, ...body } = view.report;
  const hashBody = async (runtimeFloat) => {
    const digest = await crypto.subtle.digest(
      "SHA-256",
      new TextEncoder().encode(traceCanonical(body, runtimeFloat)),
    );
    return Array.from(new Uint8Array(digest), (b) =>
      b.toString(16).padStart(2, "0"),
    ).join("");
  };
  let hash = await hashBody(true);
  // JSON.parse loses the distinction between Python's 1 and 1.0. Both exact
  // canonical encodings describe the same checked runtime numeric value.
  if (hash !== artifact_id && Number.isSafeInteger(body.runtime_seconds))
    hash = await hashBody(false);
  if (hash !== artifact_id)
    throw new Error("Transaction-prefix content hash mismatch.");
  return view;
}
