import { MAX_TRACE_BYTES, validateTraceReport } from "./trace-report.mjs";

/** @param {string} id */
function element(id) {
  const node = document.getElementById(id);
  if (!node) throw new Error(`Missing trace interface: ${id}`);
  return node;
}
let generation = 0;
function clear() {
  element("trace-results").hidden = true;
  for (const id of [
    "trace-pins",
    "trace-inputs",
    "trace-outcomes",
    "trace-receipts",
    "trace-assumptions",
    "trace-raw",
    "trace-hash",
    "trace-origin",
  ])
    element(id).replaceChildren();
  element("trace-download").hidden = true;
  element("trace-download").removeAttribute("href");
}
function status(text, error = false) {
  element("trace-status").textContent = text;
  element("trace-status").classList.toggle("error", error);
}
function rows(id, values) {
  const target = element(id);
  for (const valuesRow of values) {
    const tr = document.createElement("tr");
    valuesRow.forEach((text, index) => {
      const cell = document.createElement(index ? "td" : "th");
      if (cell instanceof HTMLTableCellElement && index === 0)
        cell.scope = "row";
      cell.textContent = String(text);
      tr.append(cell);
    });
    target.append(tr);
  }
}
function gas(receipt) {
  return receipt ? BigInt(receipt.gasUsed).toString() : "—";
}
function logs(receipt) {
  return receipt ? String(receipt.logs.length) : "—";
}
function outcome(row) {
  return row.status === "nonce_conflict"
    ? `nonce_conflict · expected ${row.expected_nonce}, original ${row.original_nonce}`
    : row.status === "executed"
      ? `executed · ${row.receipt.status === "0x1" ? "success" : "revert"}`
      : row.status;
}
/** @param {unknown} input @param {number} seq @param {boolean} recorded */
async function render(input, seq, recorded) {
  const view = await validateTraceReport(input);
  if (seq !== generation) return;
  const {
    report,
    pin,
    parent,
    header,
    inputs,
    baseline,
    candidate,
    assumptions,
  } = view;
  element("trace-origin").textContent = recorded
    ? "Recorded technical case · exact engine #30 Docker report. Different native/Docker environments are not a speed comparison."
    : "Local import · author and execution provenance are not authenticated. This file remains in your browser.";
  element("trace-pins").textContent = JSON.stringify(
    {
      source: pin,
      parent,
      header,
      through_index: inputs.length - 1,
      skip_indices: /** @type {Record<string, unknown>} */ (report.plan)
        .skip_indices,
      baseline_verified: baseline.matches,
      candidate_matches_original_receipts: candidate.matches,
      runtime_seconds: report.runtime_seconds,
      baseline_anvil: baseline.anvil_version,
      candidate_anvil: candidate.anvil_version,
    },
    null,
    2,
  );
  rows(
    "trace-inputs",
    inputs.map((tx) => [
      tx.index,
      tx.hash,
      tx.sender,
      tx.nonce,
      tx.signed.type,
      tx.signed.to ?? "Contract creation",
    ]),
  );
  rows(
    "trace-outcomes",
    inputs.map((tx, i) => [
      tx.index,
      `${gas(tx.original_receipt)} / ${logs(tx.original_receipt)}`,
      outcome(baseline.rows[i]),
      `${gas(baseline.rows[i].receipt)} / ${logs(baseline.rows[i].receipt)}`,
      outcome(candidate.rows[i]),
      `${gas(candidate.rows[i].receipt)} / ${logs(candidate.rows[i].receipt)}`,
      candidate.rows[i].differing_fields.join(", ") || "—",
    ]),
  );
  inputs.forEach((tx, i) => {
    const details = document.createElement("details"),
      summary = document.createElement("summary"),
      pre = document.createElement("pre");
    summary.textContent = `Transaction ${i}: exact original, baseline and candidate receipt fields`;
    pre.textContent = JSON.stringify(
      {
        original: tx.original_receipt,
        baseline: baseline.rows[i].receipt,
        baseline_differing_fields: baseline.rows[i].differing_fields,
        candidate: candidate.rows[i].receipt,
        candidate_differing_fields: candidate.rows[i].differing_fields,
      },
      null,
      2,
    );
    pre.tabIndex = 0;
    pre.setAttribute("role", "region");
    pre.setAttribute("aria-label", `Transaction ${i} exact receipt comparison`);
    details.append(summary, pre);
    element("trace-receipts").append(details);
  });
  for (const assumption of assumptions) {
    const li = document.createElement("li");
    li.textContent = assumption;
    element("trace-assumptions").append(li);
  }
  element("trace-raw").textContent = JSON.stringify(report, null, 2);
  element("trace-hash").textContent = String(report.artifact_id);
  status(
    `Integrity and display consistency checked locally · baseline ${baseline.matches ? "matches all original projected receipts" : "UNVERIFIED: original projected receipts do not all match"}. This is not authenticity or EVM proof.`,
  );
  element("trace-results").hidden = false;
  if (recorded) {
    element("trace-download").setAttribute(
      "href",
      "reports/trace-mainnet-prefix-four.json",
    );
    element("trace-download").hidden = false;
  }
}
element("trace-sample").addEventListener("click", async () => {
  const seq = ++generation;
  clear();
  status("Loading the recorded signed-prefix case…");
  try {
    const response = await fetch("reports/trace-mainnet-prefix-four.json");
    if (!response.ok)
      throw new Error("The signed-prefix example could not be loaded.");
    const text = await response.text();
    if (new TextEncoder().encode(text).byteLength > MAX_TRACE_BYTES)
      throw new Error("Trace report limit is 8 MiB.");
    await render(JSON.parse(text), seq, true);
  } catch (error) {
    if (seq === generation) {
      clear();
      status(
        error instanceof Error ? error.message : "Invalid trace report.",
        true,
      );
    }
  }
});
element("trace-import").addEventListener("change", async (event) => {
  if (!(event.target instanceof HTMLInputElement)) return;
  const file = event.target.files?.[0];
  if (!file) return;
  const seq = ++generation;
  clear();
  status("Checking local signed-prefix report…");
  try {
    if (file.size > MAX_TRACE_BYTES)
      throw new Error("Local trace report limit is 8 MiB.");
    await render(JSON.parse(await file.text()), seq, false);
  } catch (error) {
    if (seq === generation) {
      clear();
      status(
        error instanceof Error ? error.message : "Invalid trace report.",
        true,
      );
    }
  }
});
