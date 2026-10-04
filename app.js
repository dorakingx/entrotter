"use strict";
/** @param {string} id */
function $(id) {
  const element = document.getElementById(id);
  if (!element) throw new Error(`Missing interface element: ${id}`);
  return element;
}
/** @param {unknown} value @returns {Record<string, unknown>} */
function record(value) {
  if (value === null || typeof value !== "object" || Array.isArray(value))
    throw new Error("Invalid report object.");
  return /** @type {Record<string, unknown>} */ (value);
}
const allowedSamples = new Set([
  "liquidity-shock",
  "recovery-trap",
  "depeg-stress",
  "ethereum-uniswap-slippage",
  "agent-local-codex",
  "aave-borrow-actions",
]);
/** @param {unknown} name */
function reportCliRecipe(name) {
  if (typeof name !== "string" || !allowedSamples.has(name)) return null;
  return {
    setup:
      "git clone https://github.com/entrotter/cli.git entrotter-cli &&\n" +
      "git -C entrotter-cli checkout --detach 169b759aff9280ce44fb0d15569c7ae0a4a40889 &&\n" +
      "git clone https://github.com/entrotter/sdk-python.git entrotter-sdk &&\n" +
      "git -C entrotter-sdk checkout --detach ba4af512784119f23b6dea63fd24c7f5d1fdde44",
    command:
      "PYTHONPATH=entrotter-cli/src:entrotter-sdk/src python3 -m entrotter_cli inspect ./" +
      name +
      ".json --format text",
  };
}
/** @param {unknown} search */
function reportFromQuery(search) {
  if (typeof search !== "string" || !search || search.length > 2048)
    return null;
  const names = new URLSearchParams(search).getAll("report");
  return names.length === 1 && allowedSamples.has(names[0]) ? names[0] : null;
}
/** @param {unknown} name @param {unknown} href */
function reportExampleUrl(name, href) {
  if (
    typeof name !== "string" ||
    !allowedSamples.has(name) ||
    typeof href !== "string"
  )
    return null;
  try {
    const url = new URL(href);
    if (!["http:", "https:"].includes(url.protocol)) return null;
    url.username = "";
    url.password = "";
    url.search = "";
    url.hash = "report-explorer";
    url.searchParams.set("report", name);
    return url.href;
  } catch {
    return null;
  }
}
let generation = 0;
/** @type {ReturnType<typeof reportCliRecipe>} */
let cliRecipe = null;
let cliCopySequence = 0;
let cliCopyInFlight = false;
/** @param {boolean} disabled */
function disableCliCopy(disabled) {
  for (const id of ["cli-copy-setup", "cli-copy-command"]) {
    if (disabled) $(id).setAttribute("disabled", "");
    else $(id).removeAttribute("disabled");
  }
}
/** @param {"setup" | "command"} kind */
async function copyCliRecipe(kind) {
  if (cliCopyInFlight || !cliRecipe || !["setup", "command"].includes(kind))
    return;
  const text = kind === "setup" ? cliRecipe.setup : cliRecipe.command;
  const seq = generation;
  const copy = ++cliCopySequence;
  const current = () => seq === generation && copy === cliCopySequence;
  cliCopyInFlight = true;
  disableCliCopy(true);
  $("cli-copy-status").textContent = "Copying…";
  try {
    if (typeof navigator === "undefined" || !navigator.clipboard?.writeText)
      throw new Error("Clipboard unavailable.");
    await navigator.clipboard.writeText(text);
    if (current())
      $("cli-copy-status").textContent =
        kind === "setup" ? "CLI setup copied." : "Inspection command copied.";
  } catch {
    if (current())
      $("cli-copy-status").textContent =
        "Copy unavailable. Select the commands above and copy them manually.";
  } finally {
    cliCopyInFlight = false;
    if (!current() && cliRecipe) $("cli-copy-status").textContent = "";
    disableCliCopy(!cliRecipe);
  }
}
// The backend canonicalizes JSON with sorted keys and ensure_ascii=True.
/** @param {unknown} value @returns {string} */
function canonical(value) {
  if (Array.isArray(value)) return "[" + value.map(canonical).join(",") + "]";
  if (value !== null && typeof value === "object")
    return (
      "{" +
      Object.keys(value)
        .sort()
        .map((k) => canonical(k) + ":" + canonical(record(value)[k]))
        .join(",") +
      "}"
    );
  if (typeof value === "number" && !Number.isFinite(value))
    throw new Error("Invalid JSON number.");
  const serialized = JSON.stringify(value);
  if (serialized === undefined) throw new Error("Invalid JSON value.");
  return serialized.replace(
    /[\u0080-\uffff]/g,
    (c) => "\\u" + c.charCodeAt(0).toString(16).padStart(4, "0"),
  );
}
/** @param {unknown} input */
async function checkHash(input) {
  const report = record(input);
  if (
    report.schema_version !== "0.1.0" ||
    typeof report.artifact_id !== "string" ||
    !/^[a-f0-9]{64}$/.test(report.artifact_id)
  )
    throw new Error("Unsupported schema or missing hash.");
  const { artifact_id, ...body } = report;
  const actual = await hashValue(body);
  if (actual !== artifact_id)
    throw new Error(
      "Content hash mismatch. The result was changed or damaged.",
    );
}
/** @param {unknown} value */
async function hashValue(value) {
  const hash = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(canonical(value)),
  );
  return Array.from(new Uint8Array(hash), (b) =>
    b.toString(16).padStart(2, "0"),
  ).join("");
}
/** @param {unknown} value */
function finite(value) {
  if (
    typeof value !== "string" ||
    value.length > 100 ||
    value.trim() !== value ||
    !/^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?$/.test(value) ||
    !Number.isFinite(Number(value))
  )
    throw new Error("Invalid metric.");
  return Number(value);
}
/** @param {unknown} value @param {number} [digits] */
function fmt(value, digits = 2) {
  return finite(value).toLocaleString("en-US", {
    maximumFractionDigits: digits,
  });
}
/** @param {unknown} value */
function rawInteger(value) {
  if (
    typeof value !== "string" ||
    value.trim() !== value ||
    !/^-?(0|[1-9][0-9]{0,79})$/.test(value)
  )
    throw new Error("Invalid raw integer.");
  return value;
}
/** @param {unknown} input @param {unknown} decimals */
function tokenUnits(input, decimals) {
  const value = rawInteger(input);
  if (
    typeof decimals !== "number" ||
    !Number.isInteger(decimals) ||
    decimals < 0 ||
    decimals > 36
  )
    throw new Error("Invalid token decimals.");
  const negative = value.startsWith("-"),
    digits = (negative ? value.slice(1) : value).padStart(decimals + 1, "0");
  return (
    (negative ? "-" : "") +
    (decimals
      ? digits.slice(0, -decimals) + "." + digits.slice(-decimals)
      : digits)
  );
}
/** @param {unknown} value @param {boolean} [signed] */
function balanceInteger(value, signed = false) {
  if (
    typeof value !== "string" ||
    !/^-?(0|[1-9][0-9]{0,77})$/.test(value) ||
    value === "-0"
  )
    throw new Error("Invalid balance integer.");
  const integer = BigInt(value),
    max = 2n ** 256n - 1n;
  if ((!signed && integer < 0n) || integer > max || integer < -max)
    throw new Error("Invalid balance range.");
  return integer;
}
/** @param {bigint} value @param {number} decimals @param {boolean} [signed] */
function balanceUnits(value, decimals, signed = false) {
  let text = tokenUnits(String(value), decimals);
  if (text.includes(".")) text = text.replace(/0+$/, "").replace(/\.$/, "");
  return signed && value > 0n ? "+" + text : text;
}
/** @param {unknown} input */
function balanceMetadata(input) {
  const token = record(input);
  if (
    typeof token.address !== "string" ||
    !/^0x[0-9a-fA-F]{40}$/.test(token.address) ||
    typeof token.symbol !== "string" ||
    !/^[A-Z0-9_-]{1,12}$/.test(token.symbol) ||
    typeof token.decimals !== "number" ||
    !Number.isInteger(token.decimals) ||
    token.decimals < 0 ||
    token.decimals > 36
  )
    throw new Error("Invalid token metadata.");
  return {
    address: token.address.toLowerCase(),
    symbol: token.symbol,
    decimals: token.decimals,
  };
}
/** @param {Record<string, unknown>} report */
function exactBalanceView(report) {
  const declared = record(report.scenario).tracked_tokens;
  const supplied = declared === undefined ? [] : declared;
  if (!Array.isArray(supplied) || supplied.length > 8)
    throw new Error("Invalid tracked tokens.");
  const metadata = supplied.map(balanceMetadata);
  const pinned = new Map(metadata.map((token) => [token.address, token]));
  if (pinned.size !== metadata.length)
    throw new Error("Invalid duplicate token identity.");
  /** @type {Map<string, bigint[]>[]} */
  const states = [];
  for (const branch of [report.baseline, report.candidate]) {
    const tokens = record(branch).tokens ?? [];
    if (!Array.isArray(tokens) || tokens.length > 8)
      throw new Error("Invalid token observations.");
    const state = new Map();
    for (const input of tokens) {
      const token = record(input),
        unit = balanceMetadata(token),
        expected = pinned.get(unit.address);
      if (
        !expected ||
        state.has(unit.address) ||
        unit.symbol !== expected.symbol ||
        unit.decimals !== expected.decimals
      )
        throw new Error("Mismatched token metadata.");
      const initial = balanceInteger(token.initial_balance_raw),
        final = balanceInteger(token.final_balance_raw),
        change = balanceInteger(token.balance_delta_raw, true);
      if (final - initial !== change)
        throw new Error("Invalid token balance accounting.");
      state.set(unit.address, [initial, final, change]);
    }
    states.push(state);
  }
  const metrics = [
    record(record(report.baseline).metrics),
    record(record(report.candidate).metrics),
  ];
  const native = metrics.map((m) => [
    balanceInteger(m.initial_balance_wei),
    balanceInteger(m.final_balance_wei),
    balanceInteger(m.balance_delta_wei, true),
  ]);
  if (
    native.some((values) => values[1] - values[0] !== values[2]) ||
    balanceInteger(record(report.comparison).final_balance_delta_wei, true) !==
      native[1][1] - native[0][1]
  )
    throw new Error("Invalid native balance accounting.");
  /** @type {string[][]} */
  const rows = [];
  /** @param {string} label @param {bigint|undefined} baseline @param {bigint|undefined} candidate @param {number} decimals @param {boolean} [signed] */
  function row(label, baseline, candidate, decimals, signed = false) {
    rows.push([
      label,
      baseline === undefined
        ? "Unavailable"
        : balanceUnits(baseline, decimals, signed),
      candidate === undefined
        ? "Unavailable"
        : balanceUnits(candidate, decimals, signed),
      baseline === undefined || candidate === undefined
        ? "Unavailable"
        : balanceUnits(candidate - baseline, decimals, true),
    ]);
  }
  for (const [index, label] of ["Initial", "Final", "Change"].entries())
    row(
      "Native ETH · " + label,
      native[0][index],
      native[1][index],
      18,
      index === 2,
    );
  for (const [key, label, decimals] of [
    ["gas_cost_wei", "Gas cost (ETH)", 18],
    ["gas_used", "Gas used", 0],
    ["reverted_transactions", "Reverted transactions", 0],
    ["rejected_transactions", "Rejected transactions", 0],
  ]) {
    const values = metrics.map((m) =>
      m[String(key)] === undefined
        ? undefined
        : balanceInteger(
            typeof m[String(key)] === "number" &&
              Number.isSafeInteger(m[String(key)])
              ? String(m[String(key)])
              : m[String(key)],
          ),
    );
    row(String(label), values[0], values[1], Number(decimals));
  }
  for (const token of metadata) {
    const assetLabel =
      metadata.filter((other) => other.symbol === token.symbol).length > 1
        ? `${token.symbol} (${token.address})`
        : token.symbol;
    for (const [index, label] of ["Initial", "Final", "Change"].entries())
      row(
        assetLabel + " · " + label,
        states[0].get(token.address)?.[index],
        states[1].get(token.address)?.[index],
        token.decimals,
        index === 2,
      );
  }
  return {
    balanceRows: rows,
    tokenIdentities: metadata
      .map(
        (token) =>
          `${token.symbol} · ${token.address} · ${token.decimals} decimals`,
      )
      .join("\n"),
    native,
  };
}
/** @param {unknown} input */
function evmViewModel(input) {
  const report = record(input);
  if (report.mode !== "evm-local" && report.mode !== "evm-fork")
    throw new Error("Unsupported EVM report.");
  if (
    record(record(report.scenario).provenance).kind !==
    (report.mode === "evm-fork" ? "historical-fork" : "local-evm")
  )
    throw new Error("Invalid EVM provenance.");
  const source =
    report.source === undefined || report.source === null
      ? null
      : record(report.source);
  const baseline = record(report.baseline),
    candidate = record(report.candidate);
  const bm = record(baseline.metrics),
    cm = record(candidate.metrics);
  if (
    report.mode === "evm-fork" &&
    (source === null ||
      typeof source.chain_id !== "number" ||
      !Number.isSafeInteger(source.chain_id) ||
      source.chain_id < 1 ||
      typeof source.block_number !== "number" ||
      !Number.isSafeInteger(source.block_number) ||
      source.block_number < 1 ||
      typeof source.block_hash !== "string" ||
      !/^0x[0-9a-fA-F]{64}$/.test(source.block_hash))
  )
    throw new Error("Missing historical source pin.");
  const rows = [],
    traces = [];
  for (const key of [
    "initial_balance_wei",
    "final_balance_wei",
    "balance_delta_wei",
    "gas_used",
  ]) {
    rows.push([
      key.replaceAll("_", " "),
      rawInteger(bm[key]),
      rawInteger(cm[key]),
    ]);
  }
  if (bm.gas_cost_wei !== undefined || cm.gas_cost_wei !== undefined)
    rows.push([
      "Gas cost (wei)",
      rawInteger(bm.gas_cost_wei),
      rawInteger(cm.gas_cost_wei),
    ]);
  for (const { name, branch } of [
    { name: "Baseline", branch: baseline },
    { name: "Candidate", branch: candidate },
  ]) {
    if (
      !Array.isArray(branch.trace) ||
      branch.trace.length < 1 ||
      branch.trace.length > 32
    )
      throw new Error("Invalid EVM trace.");
    for (const inputStep of branch.trace) {
      const step = record(inputStep);
      if (
        typeof step.step !== "number" ||
        !Number.isInteger(step.step) ||
        step.step < 0 ||
        step.step > 31 ||
        typeof step.status !== "string" ||
        !["noop", "success", "reverted", "rejected"].includes(step.status)
      )
        throw new Error("Invalid EVM step.");
      traces.push([
        name,
        String(step.step),
        step.status,
        rawInteger(step.gas_used),
        rawInteger(step.actor_balance_wei),
      ]);
    }
  }
  const balances = exactBalanceView(report);
  for (const row of balances.balanceRows.filter(
    (row) => row[0].endsWith(" · Final") && !row[0].startsWith("Native"),
  ))
    rows.push([
      row[0].replace(" · Final", " final token units"),
      row[1],
      row[2],
    ]);
  return {
    ...balances,
    rows,
    traces,
    source: source
      ? `Chain ${source.chain_id} · Block ${source.block_number}\n${source.block_hash}`
      : "Local disposable chain; no historical source",
  };
}
/** @param {unknown} input */
async function agentViewModel(input) {
  const report = record(input);
  if (report.agent === undefined) return null;
  const agent = record(report.agent);
  if (
    !["evm-local", "evm-fork"].includes(String(report.mode)) ||
    agent.agent_version !== "0.1.0" ||
    !Array.isArray(agent.exchanges) ||
    agent.exchanges.length < 1 ||
    agent.exchanges.length > 32
  )
    throw new Error("Invalid agent recording.");
  evmViewModel(report);
  const candidate = record(report.candidate);
  const trace = /** @type {unknown[]} */ (candidate.trace).map(record);
  const scenario = record(report.scenario);
  if (!Array.isArray(scenario.steps) || scenario.steps.length !== trace.length)
    throw new Error("Invalid agent scenario steps.");
  if (trace.some((point, index) => point.step !== index))
    throw new Error("Invalid agent candidate order.");
  const rows = [];
  let previous = -1;
  for (const value of agent.exchanges) {
    const exchange = record(value),
      request = record(exchange.request),
      response = record(exchange.response),
      observation = record(request.observation),
      proposal = record(request.proposed_action),
      limits = record(request.limits),
      preflight = record(request.preflight);
    const step = observation.step;
    if (
      request.agent_version !== "0.1.0" ||
      typeof step !== "number" ||
      !Number.isInteger(step) ||
      step <= previous ||
      step >= trace.length ||
      typeof request.request_id !== "string" ||
      !/^[a-f0-9]{64}$/.test(request.request_id) ||
      Object.keys(response).sort().join(",") !== "choice,reason,request_id" ||
      response.request_id !== request.request_id ||
      typeof response.choice !== "string" ||
      !["execute", "hold"].includes(String(response.choice)) ||
      typeof response.reason !== "string" ||
      [...response.reason].length < 1 ||
      [...response.reason].length > 1000 ||
      typeof preflight.status !== "string" ||
      !["success", "rejected"].includes(String(preflight.status))
    )
      throw new Error("Invalid agent observation or response.");
    const { request_id, ...body } = request;
    if ((await hashValue(body)) !== request_id)
      throw new Error("Agent observation digest mismatch.");
    const outcome = trace[step];
    const history = trace.slice(0, step).map((point) => ({
      step: point.step,
      status: point.status,
      gas_used: point.gas_used,
    }));
    if (
      canonical(observation.completed_actions) !== canonical(history) ||
      canonical(proposal) !==
        canonical(record(scenario.steps[step]).candidate) ||
      canonical(outcome.agent_decision) !== canonical(response) ||
      canonical(outcome.action) !==
        canonical(response.choice === "hold" ? null : proposal)
    )
      throw new Error("Agent recording and candidate outcome disagree.");
    if (response.choice === "hold" || outcome.status === "rejected") {
      if (
        (response.choice === "hold" && outcome.status !== "noop") ||
        outcome.gas_used !== "0" ||
        outcome.receipt !== undefined ||
        outcome.transaction_hash !== undefined
      )
        throw new Error("Invalid agent held or rejected outcome.");
    } else {
      const receipt = record(outcome.receipt);
      if (
        !["success", "reverted"].includes(String(outcome.status)) ||
        receipt.status !== (outcome.status === "success" ? "0x1" : "0x0") ||
        typeof receipt.gasUsed !== "string" ||
        !/^0x[0-9a-fA-F]{1,16}$/.test(receipt.gasUsed) ||
        BigInt(receipt.gasUsed) !== BigInt(rawInteger(outcome.gas_used)) ||
        receipt.transactionHash !== outcome.transaction_hash
      )
        throw new Error("Agent receipt and outcome disagree.");
    }
    const requested = proposal.gas ?? 21000,
      remaining = limits.remaining_requested_gas;
    if (
      typeof requested !== "number" ||
      !Number.isSafeInteger(requested) ||
      requested < 1 ||
      typeof remaining !== "number" ||
      !Number.isSafeInteger(remaining) ||
      remaining < 0 ||
      (response.choice === "execute" && requested > remaining)
    )
      throw new Error("Invalid agent gas budget.");
    rows.push([
      String(step),
      String(preflight.status),
      `${requested} / ${remaining}`,
      String(response.choice),
      response.reason,
      String(outcome.status),
      rawInteger(outcome.gas_used),
    ]);
    previous = step;
  }
  if (
    trace.filter((point) => point.agent_decision !== undefined).length !==
    rows.length
  )
    throw new Error("Missing agent exchange for a candidate decision.");
  const provider = record(agent.provider);
  /** @param {unknown} value */
  function metadata(value) {
    if (value === undefined || value === null) return "Unavailable";
    if (typeof value !== "string" || value.length > 1000)
      throw new Error("Invalid agent provenance.");
    return value;
  }
  if (
    provider.deterministic !== undefined &&
    typeof provider.deterministic !== "boolean"
  )
    throw new Error("Invalid agent determinism metadata.");
  const cost = provider.cost_usd;
  if (cost !== undefined && cost !== null && finite(cost) < 0)
    throw new Error("Invalid agent generation cost.");
  const seed = provider.seed;
  if (
    seed !== undefined &&
    seed !== null &&
    !(typeof seed === "number" && Number.isFinite(seed)) &&
    !(typeof seed === "string" && seed.length <= 1000)
  )
    throw new Error("Invalid agent seed.");
  return {
    rows,
    provenance: [
      `Provider: ${metadata(provider.provider)}`,
      `Original model/policy: ${metadata(provider.model)}`,
      `Model identity scope: ${metadata(provider.model_identity_scope)}`,
      `Prompt version: ${metadata(provider.prompt_version)}`,
      `Generation: ${provider.deterministic === true ? "Deterministic" : provider.deterministic === false ? "Nondeterministic" : "Unspecified"}`,
      `Seed: ${seed === undefined || seed === null ? "Unavailable" : String(seed)}`,
      `Original generation cost (USD): ${cost === undefined || cost === null ? "Unavailable" : String(cost)}`,
      `Cost note: ${metadata(provider.cost_note)}`,
    ].join("\n"),
  };
}
/** @param {string} id @param {string[][]} rows @param {boolean} [rowHeaders] */
function tableRows(id, rows, rowHeaders = false) {
  $(id).replaceChildren();
  for (const row of rows) {
    const tr = document.createElement("tr");
    row.forEach((value, index) => {
      const cell = document.createElement(
        rowHeaders && index === 0 ? "th" : "td",
      );
      if (rowHeaders && index === 0) cell.scope = "row";
      cell.textContent = value;
      tr.appendChild(cell);
    });
    $(id).appendChild(tr);
  }
}
/** @param {string} value */
function selectSource(value) {
  const selection = $("scenario");
  if (!(selection instanceof HTMLSelectElement))
    throw new Error("Missing scenario selector.");
  selection.value = value;
}
/** @param {string} message */
function clearReport(message) {
  $("report-status").textContent = message;
  ["baseline-value", "candidate-value", "delta-value", "hash"].forEach(
    (id) => ($(id).textContent = "—"),
  );
  $("baseline-line").setAttribute("points", "");
  $("candidate-line").setAttribute("points", "");
  $("metric-table").hidden = true;
  $("metric-rows").replaceChildren();
  $("assumptions").replaceChildren();
  $("raw-report").textContent = "";
  $("download").hidden = true;
  $("example-link").hidden = true;
  $("example-link").removeAttribute("href");
  $("cli-recipe").hidden = true;
  $("cli-setup").textContent = "";
  $("cli-command").textContent = "";
  cliRecipe = null;
  cliCopySequence++;
  disableCliCopy(true);
  $("cli-copy-status").textContent = "";
  $("evm-details").hidden = true;
  $("evm-traces").replaceChildren();
  $("source-pin").textContent = "";
  $("balance-rows").replaceChildren();
  $("token-identities").textContent = "";
  $("fixture-chart").hidden = true;
  $("equity-rows").replaceChildren();
  $("chart-description").textContent = "";
  $("agent-details").hidden = true;
  $("agent-rows").replaceChildren();
  $("agent-provenance").textContent = "";
}
/** @param {string} message */
function setError(message) {
  clearReport(message);
  $("report-status").classList.add("error");
  selectSource("no-report");
}
/** @param {string} message */
function startLoading(message) {
  clearReport(message);
  $("report-status").classList.remove("error");
  selectSource("loading");
}
/** @param {unknown} input @param {number} seq */
async function render(input, seq) {
  const report = record(input);
  await checkHash(report);
  const agent = await agentViewModel(report);
  if (seq !== generation) return;
  const baseline = record(report.baseline),
    candidate = record(report.candidate);
  const bm = record(baseline.metrics),
    cm = record(candidate.metrics);
  const comparison = record(report.comparison);
  const scenario = record(report.scenario);
  const evm = report.mode !== "fixture";
  $("agent-details").hidden = agent === null;
  tableRows("agent-rows", agent?.rows ?? []);
  $("agent-provenance").textContent = agent?.provenance ?? "";
  $("fixture-chart").hidden = evm;
  $("evm-details").hidden = !evm;
  $("baseline-label").textContent = evm ? "Baseline actions" : "Hold baseline";
  $("candidate-label").textContent = evm
    ? "Changed actions"
    : "Circuit-breaker policy";
  $("baseline-unit").textContent = $("candidate-unit").textContent = evm
    ? "Exact native balance (ETH)"
    : "Final model equity";
  $("delta-unit").textContent = evm
    ? "Exact ETH; not profit"
    : "Model quote units, not USD";
  if (evm) {
    const view = evmViewModel(report);
    $("baseline-value").textContent = balanceUnits(view.native[0][1], 18);
    $("candidate-value").textContent = balanceUnits(view.native[1][1], 18);
    $("delta-value").textContent = balanceUnits(
      view.native[1][1] - view.native[0][1],
      18,
      true,
    );
    tableRows("balance-rows", view.balanceRows, true);
    $("token-identities").textContent =
      view.tokenIdentities || "No tracked ERC-20 tokens.";
    tableRows("metric-rows", view.rows, true);
    tableRows("evm-traces", view.traces);
    $("equity-rows").replaceChildren();
    $("chart-description").textContent = "";
    $("source-pin").textContent = view.source;
  } else {
    if (record(record(report.scenario).provenance).kind !== "synthetic")
      throw new Error("A fixture must be labelled synthetic.");
    const b = baseline,
      c = candidate;
    if (
      !Array.isArray(b?.trace) ||
      !Array.isArray(c?.trace) ||
      b.trace.length !== c.trace.length ||
      b.trace.length < 2 ||
      b.trace.length > 4096
    )
      throw new Error("Invalid trace.");
    const bt = b.trace.map(record),
      ct = c.trace.map(record);
    const yb = bt.map((x) => finite(x.equity)),
      yc = ct.map((x) => finite(x.equity));
    const values = [...yb, ...yc],
      min = Math.min(...values),
      max = Math.max(...values),
      spread = max - min || 1;
    /** @param {number[]} ys */
    function line(ys) {
      return ys
        .map(
          (y, i) =>
            `${45 + (i / (ys.length - 1)) * 925},${210 - ((y - min) / spread) * 165}`,
        )
        .join(" ");
    }
    $("baseline-line").setAttribute("points", line(yb));
    $("candidate-line").setAttribute("points", line(yc));
    $("chart-description").textContent =
      `${yb.length} observations, in recorded order. Dashed line: baseline. Solid line: candidate. Open Equity values by observation for every exact value.`;
    tableRows(
      "equity-rows",
      bt.map((point, i) => [
        String(i + 1),
        String(point.equity),
        String(ct[i].equity),
      ]),
      true,
    );
    $("baseline-value").textContent = fmt(bm.final_equity);
    $("candidate-value").textContent = fmt(cm.final_equity);
    const delta = finite(comparison.final_equity_delta);
    $("delta-value").textContent =
      (delta > 0 ? "+" : "") + fmt(comparison.final_equity_delta);
    $("metric-rows").replaceChildren();
    for (const [label, key, suffix] of [
      ["Model return", "return_pct", "%"],
      ["Maximum drawdown", "max_drawdown_pct", "%"],
      ["Fees (quote units)", "fees", ""],
      ["Number of trades", "trades", ""],
    ]) {
      const tr = document.createElement("tr");
      [
        label,
        key === "trades" ? String(bm[key]) : fmt(bm[key]) + suffix,
        key === "trades" ? String(cm[key]) : fmt(cm[key]) + suffix,
      ].forEach((text, index) => {
        const cell = document.createElement(index === 0 ? "th" : "td");
        if (index === 0) cell.scope = "row";
        cell.textContent = text;
        tr.appendChild(cell);
      });
      $("metric-rows").appendChild(tr);
    }
  }
  if (!Array.isArray(report.assumptions) || report.assumptions.length > 32)
    throw new Error("Invalid assumptions.");
  $("assumptions").replaceChildren();
  for (const text of report.assumptions) {
    if (typeof text !== "string" || text.length > 4000)
      throw new Error("Invalid assumption.");
    const li = document.createElement("li");
    li.textContent = text;
    $("assumptions").appendChild(li);
  }
  $("hash").textContent = String(report.artifact_id);
  $("raw-report").textContent = JSON.stringify(report, null, 2);
  $("report-status").classList.remove("error");
  $("report-status").textContent =
    "Integrity verified locally · " +
    (evm
      ? report.mode === "evm-fork"
        ? "Archived-state actions; not historical replay"
        : "Local EVM actions"
      : "Synthetic fixture") +
    " · " +
    String(scenario.title).slice(0, 120);
  $("metric-table").hidden = false;
  $("download").hidden = false;
}
async function loadSample() {
  const selection = $("scenario");
  if (!("value" in selection) || typeof selection.value !== "string")
    throw new Error("Missing scenario selector.");
  const name = selection.value;
  if (!allowedSamples.has(name)) return;
  const seq = ++generation;
  startLoading("Loading and verifying recorded example…");
  try {
    const response = await fetch("reports/" + name + ".json");
    if (!response.ok)
      throw new Error("The recorded sample could not be loaded.");
    const text = await response.text();
    if (text.length > 4 * 1024 * 1024) throw new Error("Report too large.");
    await render(JSON.parse(text), seq);
    if (seq === generation) {
      selectSource(name);
      $("download").setAttribute("href", "reports/" + name + ".json");
      $("download").setAttribute("download", name + ".json");
      const recipe = reportCliRecipe(name);
      if (recipe) {
        cliRecipe = recipe;
        $("cli-setup").textContent = recipe.setup;
        $("cli-command").textContent = recipe.command;
        $("cli-recipe").hidden = false;
        disableCliCopy(cliCopyInFlight);
        if (cliCopyInFlight)
          $("cli-copy-status").textContent =
            "Waiting for the previous copy request. You can still select and copy these commands manually.";
      }
      const href = reportExampleUrl(
        name,
        typeof location === "undefined" ? "" : location.href,
      );
      if (href) {
        $("example-link").setAttribute("href", href);
        $("example-link").hidden = false;
      }
    }
  } catch (error) {
    if (seq === generation)
      setError(
        error instanceof Error ? error.message : "Could not load this report.",
      );
  }
}
$("scenario").addEventListener("change", loadSample);
$("cli-copy-setup").addEventListener("click", () => copyCliRecipe("setup"));
$("cli-copy-command").addEventListener("click", () => copyCliRecipe("command"));
$("import").addEventListener("change", async (event) => {
  if (!(event.target instanceof HTMLInputElement)) return;
  const file = event.target.files?.[0];
  if (!file) return;
  const seq = ++generation;
  startLoading("Reading and verifying local report…");
  try {
    if (file.size > 4 * 1024 * 1024)
      throw new Error("Local report limit is 4 MiB.");
    await render(JSON.parse(await file.text()), seq);
    // No blob links or network upload are needed for an already-local file.
    if (seq === generation) {
      selectSource("local-report");
      $("download").hidden = true;
    }
  } catch (error) {
    if (seq === generation)
      setError(error instanceof Error ? error.message : "Invalid report file.");
  }
});
function initializeReportSource() {
  const name = reportFromQuery(
    typeof location === "undefined" ? "" : location.search,
  );
  if (name) {
    selectSource(name);
    const explorer = $("report-explorer");
    if (!(explorer instanceof HTMLDetailsElement))
      throw new Error("Missing report explorer.");
    explorer.open = true;
    explorer.scrollIntoView({ block: "start" });
  }
  return loadSample();
}
initializeReportSource();
