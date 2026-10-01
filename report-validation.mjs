/**
 * @typedef {Record<"ETH"|"WETH"|"USDC", string>} Balances
 * @typedef {{status:string, transactionHash:string, blockHash:string, gasUsed:string, effectiveGasPrice:string}} Receipt
 * @typedef {{receipt:Receipt, transaction:{to:string, data:string}}} Execution
 * @typedef {{id:string, status:string, verdict:string, reason:string, amountIn:string, minimumOut:string, gasUsed:number, gasCostWei:string, before:Balances, after:Balances, delta:Balances, initialStateRoot:string, initialBlockHash:string, initialStateFingerprint:string, initialObservation:Record<string,unknown>, execution:Execution|null}} Trial
 * @typedef {{format:string, mode:string, source:{chainId:number, blockNumber:number, blockHash:string, stateRoot:string}, decimals:Record<string,number>, constraints:{amountIn:string, maxSpend:string, minRateUSDCPerWETH:string, maxGas:number}, contracts:{router:string}, trials:Trial[], setup:{receipt:Receipt}[], nodeCleanedUp:boolean, overrides:unknown, tools:unknown, limitations:unknown}} Report
 */
/** @param {unknown} value @returns {Record<string, unknown>} */
function record(value) {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new Error("Expected report object");
  return /** @type {Record<string, unknown>} */ (value);
}
/** @param {Record<string, unknown>} value @param {string[]} keys @param {"string"|"number"} type */
function fields(value, keys, type) {
  ensure(
    keys.every((key) => typeof value[key] === type),
    "Invalid field type",
  );
}
/** Validate accessed shapes before giving imported JSON a static type. @param {unknown} value @returns {Report} */
function shapedReport(value) {
  const r = record(value);
  fields(r, ["format", "mode"], "string");
  const source = record(r.source);
  fields(source, ["chainId", "blockNumber"], "number");
  fields(source, ["blockHash", "stateRoot"], "string");
  fields(record(r.decimals), ["ETH", "WETH", "USDC"], "number");
  fields(
    record(r.constraints),
    ["amountIn", "maxSpend", "minRateUSDCPerWETH"],
    "string",
  );
  fields(record(r.constraints), ["maxGas"], "number");
  fields(record(r.contracts), ["router", "WETH", "USDC", "pool"], "string");
  ensure(
    Array.isArray(r.trials) && r.trials.length === 4,
    "Expected four alternatives",
  );
  for (const value of /** @type {unknown[]} */ (r.trials)) {
    const t = record(value);
    fields(
      t,
      [
        "id",
        "status",
        "verdict",
        "reason",
        "amountIn",
        "minimumOut",
        "gasCostWei",
        "initialStateRoot",
        "initialBlockHash",
        "initialStateFingerprint",
      ],
      "string",
    );
    fields(t, ["gasUsed"], "number");
    for (const name of ["before", "after", "delta"])
      fields(record(t[name]), ["ETH", "WETH", "USDC"], "string");
    record(record(t.initialObservation).balances);
    if (t.execution !== null) {
      const e = record(t.execution);
      fields(
        record(e.receipt),
        [
          "status",
          "transactionHash",
          "blockHash",
          "gasUsed",
          "effectiveGasPrice",
        ],
        "string",
      );
      fields(record(e.transaction), ["to", "data"], "string");
    }
  }
  ensure(
    Array.isArray(r.setup) && r.setup.length === 2,
    "Missing setup receipts",
  );
  for (const value of /** @type {unknown[]} */ (r.setup))
    fields(record(record(value).receipt), ["status"], "string");
  ensure(typeof r.nodeCleanedUp === "boolean", "Missing cleanup flag");
  return /** @type {Report} */ (/** @type {unknown} */ (r));
}
/** @param {unknown} x @returns {string} */
export function canonical(x) {
  if (Array.isArray(x)) return "[" + x.map(canonical).join(",") + "]";
  if (x && typeof x === "object")
    return (
      "{" +
      Object.keys(x)
        .sort()
        .map((k) => JSON.stringify(k) + ":" + canonical(record(x)[k]))
        .join(",") +
      "}"
    );
  const serialized = JSON.stringify(x);
  if (
    serialized === undefined ||
    (typeof x === "number" && !Number.isFinite(x))
  )
    throw new Error("Invalid JSON value");
  return serialized;
}
/** @param {unknown} ok @param {string} message */
const ensure = (ok, message) => {
  if (!ok) throw new Error(message);
};
/** @param {unknown} x */
const integer = (x) => typeof x === "string" && /^-?\d{1,78}$/.test(x);
/** @param {unknown} x */
const hash = (x) => typeof x === "string" && /^0x[\da-f]{64}$/i.test(x);
/** @param {unknown} input */
export async function validate(input) {
  const envelope = record(input);
  const r = shapedReport(envelope.report);
  ensure(
    r &&
      r.format === "tokyo-compare/1" &&
      r.mode === "archived-state-local-execution",
    "Unsupported report format or mode",
  );
  const bytes = new TextEncoder().encode(canonical(r));
  ensure(bytes.length < 2_000_000, "Report too large");
  const actual = [
    ...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)),
  ]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  ensure(actual === envelope.sha256, "Report hash mismatch");
  ensure(
    r.source?.chainId === 1 &&
      Number.isSafeInteger(r.source.blockNumber) &&
      r.source.blockNumber > 0 &&
      hash(r.source.blockHash) &&
      hash(r.source.stateRoot),
    "Invalid chain / block pin",
  );
  ensure(
    r.decimals?.ETH === 18 && r.decimals.WETH === 18 && r.decimals.USDC === 6,
    "Unsupported decimals",
  );
  ensure(
    integer(r.constraints?.amountIn) &&
      BigInt(r.constraints.amountIn) > 0n &&
      integer(r.constraints.maxSpend) &&
      BigInt(r.constraints.maxSpend) > 0n &&
      integer(r.constraints.minRateUSDCPerWETH) &&
      BigInt(r.constraints.minRateUSDCPerWETH) > 0n &&
      Number.isSafeInteger(r.constraints.maxGas) &&
      r.constraints.maxGas >= 21000 &&
      r.constraints.maxGas <= 500000,
    "Invalid constraints",
  );
  ensure(
    Array.isArray(r.trials) && r.trials.length === 4,
    "Expected four alternatives",
  );
  ensure(
    Array.isArray(r.setup) &&
      r.setup.length === 2 &&
      r.setup.every((t) => t?.receipt?.status === "0x1"),
    "Missing successful setup receipts",
  );
  ensure(
    r.contracts?.router?.toLowerCase() ===
      "0xe592427a0aece92de3edee1f18e0157c05861564",
    "Unexpected router",
  );
  const contracts = record(r.contracts);
  ensure(
    String(contracts.WETH).toLowerCase() ===
      "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2" &&
      String(contracts.USDC).toLowerCase() ===
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48" &&
      String(contracts.pool).toLowerCase() ===
        "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8",
    "Unexpected token or pool",
  );
  ensure(r.nodeCleanedUp === true, "Node cleanup not confirmed");
  const names = ["proposed", "reduced", "strict-minimum", "hold"];
  const first = r.trials[0];
  for (let i = 0; i < 4; i++) {
    const t = r.trials[i];
    ensure(
      t.id === names[i] && ["success", "revert", "hold"].includes(t.status),
      "Invalid trial identity or status",
    );
    ensure(
      hash(t.initialStateRoot) &&
        hash(t.initialBlockHash) &&
        t.initialStateRoot === first.initialStateRoot &&
        t.initialBlockHash === first.initialBlockHash &&
        canonical(t.before) === canonical(first.before) &&
        canonical(t.initialObservation) === canonical(first.initialObservation),
      "Alternatives have different initial states",
    );
    const fp = [
      ...new Uint8Array(
        await crypto.subtle.digest(
          "SHA-256",
          new TextEncoder().encode(canonical(t.initialObservation)),
        ),
      ),
    ]
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
    ensure(
      fp === t.initialStateFingerprint &&
        canonical(t.initialObservation.balances) === canonical(t.before),
      "Initial observation fingerprint mismatch",
    );
    ensure(
      integer(t.amountIn) &&
        BigInt(t.amountIn) >= 0n &&
        integer(t.minimumOut) &&
        BigInt(t.minimumOut) >= 0n,
      "Invalid swap amount",
    );
    ensure(
      Number.isSafeInteger(t.gasUsed) &&
        t.gasUsed >= 0 &&
        t.gasUsed <= 500000 &&
        integer(t.gasCostWei),
      "Invalid gas",
    );
    for (const k of ["ETH", "WETH", "USDC"]) {
      ensure(
        integer(t.before?.[k]) &&
          integer(t.after?.[k]) &&
          integer(t.delta?.[k]),
        "Invalid balance",
      );
      ensure(
        BigInt(t.before[k]) >= 0n &&
          BigInt(t.after[k]) >= 0n &&
          BigInt(t.after[k]) - BigInt(t.before[k]) === BigInt(t.delta[k]),
        "Balance delta mismatch",
      );
    }
    ensure(
      BigInt(t.delta.ETH) === -BigInt(t.gasCostWei),
      "Native fee mismatch",
    );
    if (t.id === "hold") {
      ensure(
        t.status === "hold" &&
          t.execution === null &&
          t.gasUsed === 0 &&
          t.gasCostWei === "0" &&
          t.amountIn === "0" &&
          Object.values(t.delta).every((v) => v === "0"),
        "Hold must have no execution or balance change",
      );
    } else {
      const e = t.execution;
      if (!e) throw new Error("Missing execution");
      const receipt = e.receipt;
      ensure(
        receipt && hash(receipt.transactionHash) && hash(receipt.blockHash),
        "Missing receipt",
      );
      ensure(
        receipt.status === (t.status === "success" ? "0x1" : "0x0") &&
          t.status !== "hold",
        "Receipt status mismatch",
      );
      ensure(
        /^0x[0-9a-f]+$/i.test(receipt.gasUsed) &&
          /^0x[0-9a-f]+$/i.test(receipt.effectiveGasPrice),
        "Invalid receipt gas",
      );
      ensure(
        BigInt(receipt.gasUsed) === BigInt(t.gasUsed) &&
          BigInt(receipt.gasUsed) * BigInt(receipt.effectiveGasPrice) ===
            BigInt(t.gasCostWei),
        "Receipt gas mismatch",
      );
      ensure(
        e.transaction?.to?.toLowerCase() === r.contracts.router.toLowerCase() &&
          typeof e.transaction.data === "string" &&
          /^0x[0-9a-f]+$/i.test(e.transaction.data) &&
          e.transaction.data.length === 522,
        "Invalid swap calldata",
      );
      const data = e.transaction.data.toLowerCase();
      ensure(
        data.slice(10, 74) ===
          "000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2" &&
          data.slice(74, 138) ===
            "000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48" &&
          BigInt("0x" + data.slice(138, 202)) === 3000n,
        "Swap token or fee mismatch",
      );
      ensure(
        data.slice(0, 10) === "0x414bf389" &&
          BigInt("0x" + data.slice(330, 394)) === BigInt(t.amountIn) &&
          BigInt("0x" + data.slice(394, 458)) === BigInt(t.minimumOut),
        "Swap calldata disagrees with action",
      );
      if (t.status === "revert")
        ensure(
          t.delta.WETH === "0" && t.delta.USDC === "0",
          "Revert changed token balances",
        );
      else
        ensure(
          BigInt(t.delta.WETH) === -BigInt(t.amountIn) &&
            BigInt(t.delta.USDC) >= BigInt(t.minimumOut),
          "Successful swap violates amounts",
        );
    }
    const proceed =
      t.status === "success" &&
      BigInt(t.amountIn) <= BigInt(r.constraints.maxSpend) &&
      BigInt(t.delta.USDC) >= BigInt(t.minimumOut) &&
      t.gasUsed <= r.constraints.maxGas;
    ensure(
      t.verdict === (proceed ? "PROCEED" : "HOLD"),
      "Decision inconsistent with constraints",
    );
    ensure(
      typeof t.reason === "string" && t.reason.length < 1000,
      "Invalid decision explanation",
    );
  }
  ensure(
    first.amountIn === r.constraints.amountIn &&
      r.trials[2].amountIn === first.amountIn,
    "Proposed amount mismatch",
  );
  const reduced =
    BigInt(first.amountIn) / 2n < BigInt(r.constraints.maxSpend)
      ? BigInt(first.amountIn) / 2n
      : BigInt(r.constraints.maxSpend);
  ensure(BigInt(r.trials[1].amountIn) === reduced, "Reduced amount mismatch");
  for (const t of r.trials.slice(0, 2))
    ensure(
      BigInt(t.minimumOut) ===
        (BigInt(t.amountIn) * BigInt(r.constraints.minRateUSDCPerWETH)) /
          10n ** 18n,
      "Minimum rate mismatch",
    );
  return r;
}
/** @param {string} raw @param {number} places */
export function decimal(raw, places) {
  const n = BigInt(raw),
    sign = n < 0n ? "-" : "",
    a = (n < 0n ? -n : n).toString().padStart(places + 1, "0");
  return (
    sign +
    a.slice(0, -places) +
    (a.slice(-places).replace(/0+$/, "")
      ? "." + a.slice(-places).replace(/0+$/, "")
      : "")
  );
}
