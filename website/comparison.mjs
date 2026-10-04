import { validate, decimal } from "./report-validation.mjs";
/** @param {string} id */
function $(id) {
  const node = document.getElementById("c-" + id);
  if (!node) throw new Error(`Missing console element: ${id}`);
  return node;
}
/** @param {string} id */
function input(id) {
  const node = $(id);
  if (!(node instanceof HTMLInputElement)) throw new Error("Expected input");
  return node;
}
function downloadButton() {
  const node = $("download");
  if (!(node instanceof HTMLButtonElement)) throw new Error("Expected button");
  return node;
}
const download = downloadButton();
/** @type {Record<string, string>} */
const titles = {
  proposed: "Proposed swap",
  reduced: "Reduce the size",
  "strict-minimum": "Raise the minimum",
  hold: "Keep the position",
};
/** @type {unknown} */
let current;
let generation = 0;
/** @template {keyof HTMLElementTagNameMap} T @param {T} tag @param {string} text @param {string} [cls] */
function el(tag, text, cls) {
  const n = document.createElement(tag);
  n.textContent = text;
  if (cls) n.className = cls;
  return n;
}
/** @param {Awaited<ReturnType<typeof validate>>} r @param {unknown} envelope @param {string} label */
function display(r, envelope, label) {
  current = envelope;
  $("mode").textContent = label;
  $("source-summary").textContent =
    `Ethereum block ${r.source.blockNumber.toLocaleString()} · WETH → USDC · 0.30% pool · Local Anvil execution`;
  $("message").textContent = "";
  $("constraints").replaceChildren(
    ...[
      `Spend cap: ${decimal(r.constraints.maxSpend, 18)} WETH`,
      `Minimum rate: ${decimal(r.constraints.minRateUSDCPerWETH, 6)} USDC / WETH`,
      `Gas cap: ${r.constraints.maxGas.toLocaleString()} units`,
      "Setup funding + approval excluded from trial gas",
    ].map((s) => el("span", s)),
  );
  $("cards").replaceChildren();
  for (const [i, t] of r.trials.entries()) {
    const card = el(
      "article",
      "",
      "card" + (t.verdict === "PROCEED" ? " recommended" : ""),
    );
    const top = el("div", "", "card-top");
    top.append(
      el(
        "span",
        `0${i + 1} / ${t.id === "hold" ? "NO TRANSACTION" : "LOCAL TRIAL"}`,
      ),
      el("span", t.status, "status " + t.status),
    );
    card.append(top, el("h3", titles[t.id]));
    const amount = el("div", decimal(t.delta.USDC, 6), "amount");
    amount.append(el("small", "USDC"));
    card.append(amount, el("div", "Actual token balance change", "label"));
    const dl = el("dl", "");
    for (const [label, value] of [
      ["WETH change", decimal(t.delta.WETH, 18) + " WETH"],
      ["Gas used", t.gasUsed.toLocaleString() + " units"],
      ["Native gas cost", decimal(t.gasCostWei, 18) + " ETH"],
      ["Minimum output", decimal(t.minimumOut, 6) + " USDC"],
    ]) {
      const row = el("div", "");
      row.append(el("dt", label), el("dd", value));
      dl.append(row);
    }
    card.append(
      dl,
      el(
        "div",
        t.verdict === "PROCEED"
          ? "WITHIN YOUR CONSTRAINTS"
          : "HOLD / DO NOT PROCEED",
        "verdict",
      ),
      el("p", t.reason, "reason"),
    );
    const d = el("details", "");
    d.append(
      el(
        "summary",
        t.execution
          ? "Inspect receipt & exact balances"
          : "Inspect zero-change evidence",
      ),
      el(
        "pre",
        JSON.stringify(
          {
            initialStateFingerprint: t.initialStateFingerprint,
            initialObservation: t.initialObservation,
            before: t.before,
            after: t.after,
            delta: t.delta,
            execution: t.execution,
          },
          null,
          2,
        ),
      ),
    );
    card.append(d);
    $("cards").append(card);
  }
  const good = r.trials.filter((t) => t.verdict === "PROCEED");
  $("takeaway").textContent = good.length
    ? `${good.map((t) => titles[t.id]).join(" and ")} meets the supplied constraints in this recorded run. Success alone is not permission: check the spending cap, minimum output and gas together. Holding spends no execution gas.`
    : "None of the tested swaps meets every constraint. Holding leaves balances unchanged and spends no execution gas.";
  $("pins").textContent = JSON.stringify(
    {
      source: r.source,
      contracts: r.contracts,
      decimals: r.decimals,
      overrides: r.overrides,
      tools: r.tools,
      sha256:
        typeof envelope === "object" &&
        envelope !== null &&
        "sha256" in envelope
          ? envelope.sha256
          : null,
      nodeCleanedUp: r.nodeCleanedUp,
      limitations: r.limitations,
    },
    null,
    2,
  );
  $("setup").textContent = JSON.stringify(r.setup, null, 2);
  $("results").hidden = false;
  download.disabled = false;
}
/** @param {() => Promise<unknown>} read @param {string} label */
async function load(read, label) {
  const token = ++generation;
  $("results").hidden = true;
  download.disabled = true;
  current = null;
  $("mode").textContent = "Validating report…";
  $("message").textContent = "";
  $("source-summary").textContent = "";
  for (const id of ["cards", "constraints", "takeaway", "pins", "setup"])
    $(id).replaceChildren();
  try {
    const envelope = await read();
    const report = await validate(envelope);
    if (token !== generation) return;
    display(report, envelope, label);
  } catch (error) {
    if (token !== generation) return;
    $("mode").textContent = "Report rejected";
    $("message").textContent =
      "Could not load report: " +
      (error instanceof Error ? error.message : String(error));
  }
}
async function sample() {
  await load(async () => {
    const response = await fetch("./assets/examples/action-comparison.json");
    if (!response.ok) throw Error("Example unavailable");
    return response.json();
  }, "Recorded local execution · not a live run");
}
$("sample").onclick = sample;
input("report-file").onchange = async () => {
  const chooser = input("report-file");
  const file = chooser.files?.[0];
  if (!file) return;
  chooser.value = "";
  await load(async () => {
    if (file.size > 2_000_000) throw Error("Maximum report size is 2 MB");
    return JSON.parse(await file.text());
  }, "Imported local report · validated in your browser");
};
$("download").onclick = () => {
  if (!current) return;
  const u = URL.createObjectURL(
    new Blob([JSON.stringify(current, null, 2)], { type: "application/json" }),
  );
  const a = el("a", "");
  a.href = u;
  a.download = "entrotter-comparison.json";
  a.click();
  setTimeout(() => URL.revokeObjectURL(u), 1000);
};
$("command-form").onsubmit = (e) => {
  e.preventDefault();
  const values = ["amount", "spend", "rate"].map((id) => input(id).value);
  if (
    values.some(
      (v) =>
        v.length > 13 || !/^\d{1,6}(\.\d{1,6})?$/.test(v) || Number(v) <= 0,
    )
  ) {
    $("command").textContent =
      "Enter positive decimal amounts (up to six decimal places).";
    return;
  }
  $("command").textContent =
    `python3 compare.py --amount ${values[0]} --max-spend ${values[1]} --min-rate ${values[2]} --output report.json`;
};
sample();
