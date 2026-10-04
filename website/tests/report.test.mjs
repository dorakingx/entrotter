import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createHash, webcrypto } from "node:crypto";
import vm from "node:vm";
import { File } from "node:buffer";

// No browser/network needed: exercise the exact production hash/number functions.
const context = vm.createContext({
  document: {
    getElementById: () => ({
      value: "not-an-allowed-sample",
      addEventListener: () => {},
    }),
  },
  crypto: webcrypto,
  TextEncoder,
  URL,
  URLSearchParams,
  fetch: () => {
    throw new Error("Unit tests must not contact the network");
  },
});
const productionCode = readFileSync(
  new URL("../app.js", import.meta.url),
  "utf8",
);
vm.runInContext(productionCode, context);
const sample = () =>
  JSON.parse(
    readFileSync(
      new URL("../reports/liquidity-shock.json", import.meta.url),
      "utf8",
    ),
  );
test("CLI copying uses only verified recipes and keeps pending feedback isolated", async () => {
  const elements = new Map();
  const writes = [];
  const element = (id) => {
    if (!elements.has(id))
      elements.set(id, {
        value: "not-an-allowed-sample",
        textContent: "",
        disabled: false,
        hidden: false,
        addEventListener() {},
        setAttribute(name) {
          if (name === "disabled") this.disabled = true;
        },
        removeAttribute(name) {
          if (name === "disabled") this.disabled = false;
        },
        replaceChildren() {},
      });
    return elements.get(id);
  };
  let finish;
  const pending = new Promise((resolve) => {
    finish = resolve;
  });
  const copyContext = vm.createContext({
    document: { getElementById: element },
    navigator: {
      clipboard: {
        writeText: (text) => {
          writes.push(text);
          return pending;
        },
      },
    },
  });
  vm.runInContext(productionCode, copyContext);
  await copyContext.copyCliRecipe("command");
  assert.deepEqual(writes, []);
  vm.runInContext(
    'cliRecipe = reportCliRecipe("aave-borrow-actions")',
    copyContext,
  );
  element("cli-setup").textContent = "private injected DOM text";
  const task = copyContext.copyCliRecipe("setup");
  assert.equal(
    writes[0],
    copyContext.reportCliRecipe("aave-borrow-actions").setup,
  );
  assert.equal(element("cli-copy-setup").disabled, true);
  copyContext.clearReport("Loading");
  vm.runInContext('cliRecipe = reportCliRecipe("recovery-trap")', copyContext);
  await copyContext.copyCliRecipe("command");
  assert.equal(writes.length, 1, "Pending clipboard writes must not overlap");
  finish();
  await task;
  assert.equal(element("cli-copy-status").textContent, "");
  assert.equal(element("cli-copy-command").disabled, false);
  copyContext.navigator.clipboard.writeText = async () => {
    throw new Error("Private browser error");
  };
  await copyContext.copyCliRecipe("command");
  assert.match(element("cli-copy-status").textContent, /^Copy unavailable\./);
  assert.doesNotMatch(element("cli-copy-status").textContent, /Private/);
  copyContext.navigator.clipboard = undefined;
  await copyContext.copyCliRecipe("setup");
  assert.match(element("cli-copy-status").textContent, /copy them manually/);
  copyContext.clearReport("Local report");
  await copyContext.copyCliRecipe("command");
  assert.equal(writes.length, 1);
  assert.equal(element("cli-copy-command").disabled, true);
});
test("CLI inspection recipe uses pinned sources and fixed report filenames", () => {
  for (const name of [
    "liquidity-shock",
    "recovery-trap",
    "depeg-stress",
    "ethereum-uniswap-slippage",
    "agent-local-codex",
    "aave-borrow-actions",
  ]) {
    const recipe = context.reportCliRecipe(name);
    assert.match(
      recipe.setup,
      /checkout --detach 23f2bf0c53ff3c9a50348d038d78eeaaf927f059/,
    );
    assert.match(
      recipe.setup,
      /git clone https:\/\/github\.com\/dorakingx\/entrotter\.git entrotter/,
    );
    assert.equal(
      recipe.command,
      `PYTHONPATH=entrotter/cli/src:entrotter/sdk-python/src python3 -m entrotter_cli inspect ./${name}.json --format text`,
    );
  }
  for (const name of [
    null,
    {},
    "private-wallet-report",
    "../private",
    "aave-borrow-actions; echo x",
    "https://example.com/x",
  ])
    assert.equal(context.reportCliRecipe(name), null);
});
test("local CLI guidance copies a fixed path and clears before another report", async () => {
  const elements = new Map();
  const writes = [];
  const element = (id) => {
    if (!elements.has(id))
      elements.set(id, {
        value: "not-an-allowed-sample",
        textContent: "",
        hidden: true,
        disabled: true,
        addEventListener() {},
        setAttribute() {},
        removeAttribute() {},
        replaceChildren() {},
      });
    return elements.get(id);
  };
  const local = vm.createContext({
    URLSearchParams,
    document: { getElementById: element },
    navigator: {
      clipboard: {
        writeText: async (text) => {
          writes.push(text);
        },
      },
    },
  });
  vm.runInContext(productionCode, local);
  local.showCliRecipe("local-report");
  assert.equal(element("cli-recipe").hidden, false);
  assert.match(
    element("cli-file-help").textContent,
    /copy.*local-report\.json/,
  );
  assert.match(element("cli-file-help").textContent, /original file unchanged/);
  element("cli-command").textContent = "private injected filename";
  await local.copyCliRecipe("command");
  assert.deepEqual(writes, [
    "PYTHONPATH=entrotter/cli/src:entrotter/sdk-python/src python3 -m entrotter_cli inspect ./local-report.json --format text",
  ]);
  assert.equal(local.reportFromQuery("?report=local-report"), null);
  local.clearReport("Loading");
  assert.equal(element("cli-recipe").hidden, true);
  assert.equal(element("cli-file-help").textContent, "");
  assert.equal(element("cli-command").textContent, "");
  await local.copyCliRecipe("command");
  assert.equal(writes.length, 1);
});
function localSaveHarness() {
  const elements = new Map(),
    created = [],
    revoked = [],
    clicks = [];
  let removed = 0;
  const element = (id) => {
    if (!elements.has(id))
      elements.set(id, {
        value: "not-an-allowed-sample",
        hidden: true,
        disabled: true,
        textContent: "",
        addEventListener() {},
        setAttribute() {},
        removeAttribute() {},
        replaceChildren() {},
      });
    return elements.get(id);
  };
  const url = {
    createObjectURL(file) {
      created.push(file);
      return "blob:local-test";
    },
    revokeObjectURL(value) {
      revoked.push(value);
    },
  };
  const document = {
    getElementById: element,
    body: { appendChild() {} },
    createElement(tag) {
      assert.equal(tag, "a");
      return {
        href: "",
        download: "",
        click() {
          clicks.push({ href: this.href, download: this.download });
        },
        remove() {
          removed++;
        },
      };
    },
  };
  const context = vm.createContext({ document, URL: url });
  vm.runInContext(productionCode, context);
  return {
    context,
    element,
    url,
    created,
    revoked,
    clicks,
    removed: () => removed,
  };
}
test("local CLI save uses the original File and a bounded fixed-name URL", async () => {
  const h = localSaveHarness();
  h.context.saveLocalCliInput();
  assert.equal(h.created.length, 0);
  const raw = '  {\n  "private": "<tag> $(never-execute)"\n}\n';
  const file = new File([raw], "private-wallet-$(never-execute).json");
  h.context.file = file;
  vm.runInContext("localCliFile = file", h.context);
  h.element("cli-command").textContent = "private injected DOM";
  h.context.saveLocalCliInput();
  h.context.saveLocalCliInput();
  assert.equal(
    h.created.length,
    1,
    "Repeated clicks reuse one current File URL",
  );
  assert.equal(h.created[0], file, "Do not reserialize the imported JSON");
  assert.equal(await h.created[0].text(), raw);
  assert.deepEqual(h.clicks, [
    { href: "blob:local-test", download: "local-report.json" },
    { href: "blob:local-test", download: "local-report.json" },
  ]);
  assert.equal(h.removed(), 2);
  assert.doesNotMatch(
    h.element("cli-save-status").textContent,
    /private|never-execute/,
  );
  h.context.clearReport("Loading");
  assert.deepEqual(h.revoked, ["blob:local-test"]);
  assert.equal(h.element("cli-save-input").hidden, true);
  assert.equal(h.element("cli-save-input").disabled, true);
  assert.equal(h.element("cli-save-status").textContent, "");
  h.context.saveLocalCliInput();
  h.context.clearReport("Invalid");
  assert.equal(h.created.length, 1);
  assert.equal(h.clicks.length, 2);
  assert.equal(h.revoked.length, 1);
});
test("local CLI save failures keep manual copying and do not reveal browser errors", () => {
  const h = localSaveHarness();
  h.context.file = new File(["{}"], "private.json");
  vm.runInContext("localCliFile = file", h.context);
  h.url.createObjectURL = () => {
    throw new Error("private browser error");
  };
  h.context.saveLocalCliInput();
  assert.match(
    h.element("cli-save-status").textContent,
    /Save a local copy.*local-report\.json/,
  );
  assert.doesNotMatch(
    h.element("cli-save-status").textContent,
    /private browser error/,
  );
  assert.equal(h.clicks.length, 0);
  h.url.createObjectURL = (file) => {
    h.created.push(file);
    return "blob:retry";
  };
  h.context.document.createElement = () => ({
    click() {
      throw new Error("private click error");
    },
    remove() {},
  });
  h.context.saveLocalCliInput();
  assert.deepEqual(h.revoked, ["blob:retry"]);
  assert.doesNotMatch(
    h.element("cli-save-status").textContent,
    /private click error/,
  );
});
for (const name of ["liquidity-shock", "recovery-trap", "depeg-stress"]) {
  test(`production JS verifies Python artifact: ${name}`, async () => {
    await context.checkHash(
      JSON.parse(
        readFileSync(
          new URL(`../reports/${name}.json`, import.meta.url),
          "utf8",
        ),
      ),
    );
  });
}
test("tampered metric fails integrity validation", async () => {
  const r = sample();
  r.candidate.metrics.final_equity = "999999";
  await assert.rejects(context.checkHash(r), /mismatch/);
});
test("unknown schema is not accepted", async () => {
  const r = sample();
  r.schema_version = "9";
  await assert.rejects(context.checkHash(r), /Unsupported/);
});
test("canonical ASCII escaping includes supplementary Unicode", () => {
  assert.equal(
    context.canonical({ x: "🛸", a: "é" }),
    '\x7b"a":"\\u00e9","x":"\\ud83d\\udef8"\x7d',
  );
});
test("finite numerical display validation", () => {
  assert.equal(context.finite("8557.0516"), 8557.0516);
  assert.throws(() => context.finite("Infinity"), /Invalid metric/);
  assert.throws(() => context.finite(2), /Invalid metric/);
});
test("JS re-canonicalization matches exported content hash", () => {
  const { artifact_id, ...r } = sample();
  assert.equal(
    createHash("sha256").update(context.canonical(r)).digest("hex"),
    artifact_id,
  );
});
const evm = () =>
  JSON.parse(
    readFileSync(
      new URL("../reports/ethereum-uniswap-slippage.json", import.meta.url),
      "utf8",
    ),
  );
test("real archived-state artifact passes hash and receipt view validation", async () => {
  const r = evm();
  await context.checkHash(r);
  const view = context.evmViewModel(r);
  assert.equal(view.traces.length, 6);
  assert.equal(view.traces.at(-1)[2], "reverted");
  assert.match(view.source, /19000000/);
  assert.equal(
    view.rows.find((r) => r[0] === "USDC final token units")[1],
    "2556.134769",
  );
});
test("token units preserve integers beyond Number safe precision", () => {
  assert.equal(
    context.tokenUnits("123456789012345678901", 18),
    "123.456789012345678901",
  );
  assert.equal(context.tokenUnits("-1", 6), "-0.000001");
  assert.equal(context.tokenUnits("42", 0), "42");
  assert.throws(() => context.tokenUnits("1e18", 18), /Invalid/);
  assert.throws(() => context.tokenUnits("1", 1000), /Invalid/);
});
test("missing source hash cannot appear as a historical report", () => {
  const r = evm();
  delete r.source.block_hash;
  assert.throws(() => context.evmViewModel(r), /source pin/);
});
test("mismatched token addresses cannot share a comparison row", () => {
  const r = evm();
  r.candidate.tokens[0].address = "0x" + "f".repeat(40);
  assert.throws(() => context.evmViewModel(r), /metadata/);
});
test("malformed receipt state and oversized traces fail closed", () => {
  const r = evm();
  r.candidate.trace[0].status = "<img>";
  assert.throws(() => context.evmViewModel(r), /step/);
  const many = evm();
  many.baseline.trace = Array(33).fill(many.baseline.trace[0]);
  assert.throws(() => context.evmViewModel(many), /trace/);
});

test("display metrics reject coercible non-decimal strings", () => {
  for (const value of ["", " ", "\t", "0x10", "0b11", "0o10"]) {
    assert.throws(() => context.finite(value), /Invalid metric/);
  }
});

test("decimal metrics preserve supported signed/exponent values and reject overflow", () => {
  assert.equal(context.finite("-1.25"), -1.25);
  assert.equal(context.finite("1e2"), 100);
  for (const value of ["1e999", "1\n", "1 ", "NaN", "1".repeat(101)])
    assert.throws(() => context.finite(value), /Invalid metric/);
  assert.throws(() => context.rawInteger("1\n"), /Invalid raw integer/);
});
test("hash verification rejects non-object or non-finite parsed JSON", async () => {
  for (const value of [null, [], true, 42, "report"])
    await assert.rejects(context.checkHash(value), /Invalid report object/);
  assert.throws(() => context.canonical(Infinity), /Invalid JSON number/);
});

test("local EVM reports accept null/absent source while forks require their pin", () => {
  const r = evm();
  r.mode = "evm-local";
  r.scenario.provenance.kind = "local-evm";
  r.source = null;
  assert.match(context.evmViewModel(r).source, /Local disposable chain/);
  delete r.source;
  assert.match(context.evmViewModel(r).source, /Local disposable chain/);
  const fork = evm();
  fork.source = null;
  assert.throws(() => context.evmViewModel(fork), /source pin/);
});

const agent = () =>
  JSON.parse(
    readFileSync(
      new URL("../reports/agent-local-codex.json", import.meta.url),
      "utf8",
    ),
  );
test("recorded agent decisions join causal steps to exact candidate outcomes", async () => {
  const r = agent();
  await context.checkHash(r);
  const view = await context.agentViewModel(r);
  assert.equal(view.rows.length, 2);
  assert.deepEqual(Array.from(view.rows[0]), [
    "0",
    "success",
    "21000 / 2000000",
    "execute",
    r.agent.exchanges[0].response.reason,
    "success",
    "21000",
  ]);
  assert.deepEqual(Array.from(view.rows[1]).slice(0, 4), [
    "1",
    "rejected",
    "50000 / 1979000",
    "hold",
  ]);
  assert.match(view.provenance, /gpt-5.6-sol/);
  assert.match(view.provenance, /requested alias/);
  assert.match(view.provenance, /Nondeterministic/);
  assert.match(view.provenance, /Original generation cost.*Unavailable/);
  assert.equal(await context.agentViewModel(evm()), null);
});
test("agent recording rejects forged steps, responses, IDs, outcomes and future history", async () => {
  const mutations = [
    (r) => {
      r.agent.exchanges[0].response.step = 31;
    },
    (r) => {
      r.agent.exchanges[0].request.observation.step = 31;
    },
    (r) => {
      r.agent.exchanges[0].request.request_id = "a".repeat(64);
    },
    (r) => {
      r.candidate.trace[0].agent_decision.reason = "unrelated";
    },
    (r) => {
      r.candidate.trace[1].action =
        r.agent.exchanges[1].request.proposed_action;
    },
    (r) => {
      r.agent.exchanges[0].request.observation.completed_actions.push({
        step: 1,
        status: "noop",
        gas_used: "0",
      });
    },
    (r) => {
      r.agent.exchanges = Array(33).fill(r.agent.exchanges[0]);
    },
  ];
  for (const mutate of mutations) {
    const r = agent();
    mutate(r);
    await assert.rejects(
      context.agentViewModel(r),
      /agent|Agent|observation|Observation/,
    );
  }
});
test("agent metadata preserves built-in determinism and known generation cost", async () => {
  const r = agent();
  r.agent.provider = {
    provider: "builtin",
    model: "preflight-risk-v1",
    deterministic: true,
    cost_usd: "0",
  };
  assert.match((await context.agentViewModel(r)).provenance, /Deterministic/);
  assert.match(
    (await context.agentViewModel(r)).provenance,
    /Original generation cost.*0/,
  );
  r.agent.provider.cost_usd = " ";
  await assert.rejects(context.agentViewModel(r), /metric/);
});

/** @type {Array<[string, (r: ReturnType<typeof agent>) => void]>} */
const contradictoryAgents = [
  [
    "array choice disguised as hold",
    (r) => {
      r.agent.exchanges[0].response.choice = ["hold"];
      r.candidate.trace[0].agent_decision.choice = ["hold"];
    },
  ],
  [
    "held action claiming successful gas use",
    (r) => {
      r.candidate.trace[1].status = "success";
      r.candidate.trace[1].gas_used = "21000";
    },
  ],
  [
    "proposal unrelated to scenario",
    (r) => {
      r.agent.exchanges[0].request.proposed_action.to = "0x" + "f".repeat(40);
      r.candidate.trace[0].action.to = "0x" + "f".repeat(40);
    },
  ],
  [
    "receipt contradicting outcome",
    (r) => {
      r.candidate.trace[0].receipt.status = "0x0";
    },
  ],
];
for (const [name, mutate] of contradictoryAgents)
  test(`resealed agent refuses ${name}`, async () => {
    const r = agent();
    mutate(r);
    for (const exchange of r.agent.exchanges) {
      const { request_id, ...request } = exchange.request;
      const id = createHash("sha256")
        .update(context.canonical(request))
        .digest("hex");
      exchange.request.request_id = id;
      exchange.response.request_id = id;
      r.candidate.trace[request.observation.step].agent_decision.request_id =
        id;
    }
    const { artifact_id, ...body } = r;
    r.artifact_id = createHash("sha256")
      .update(context.canonical(body))
      .digest("hex");
    await context.checkHash(r);
    await assert.rejects(context.agentViewModel(r), /agent|Agent/);
  });

const aaveActions = () =>
  JSON.parse(
    readFileSync(
      new URL("../reports/aave-borrow-actions.json", import.meta.url),
      "utf8",
    ),
  );
const balanceRow = (view, label) =>
  Array.from(view.balanceRows.find((row) => row[0] === label));
test("Aave action balances preserve original exact units and all differences", async () => {
  const r = aaveActions();
  await context.checkHash(r);
  await context.agentViewModel(r);
  const v = context.evmViewModel(r);
  assert.deepEqual(balanceRow(v, "Native ETH · Final"), [
    "Native ETH · Final",
    "9.988827559170319712",
    "9.9912499816031695",
    "+0.002422422432849788",
  ]);
  assert.deepEqual(balanceRow(v, "WETH · Initial"), [
    "WETH · Initial",
    "0",
    "0",
    "0",
  ]);
  assert.deepEqual(balanceRow(v, "AWETH · Final"), [
    "AWETH · Final",
    "10.000000094454558462",
    "10.000000094454558462",
    "0",
  ]);
  assert.deepEqual(balanceRow(v, "VWETH · Change"), [
    "VWETH · Change",
    "+1",
    "+1",
    "0",
  ]);
  assert.deepEqual(balanceRow(v, "Gas used"), [
    "Gas used",
    "723131",
    "560326",
    "-162805",
  ]);
  assert.match(v.tokenIdentities, /0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2/);
});
test("missing tracked token observations are unavailable rather than zero", () => {
  const r = aaveActions();
  r.candidate.tokens = [];
  assert.deepEqual(balanceRow(context.evmViewModel(r), "WETH · Final"), [
    "WETH · Final",
    "1",
    "Unavailable",
    "Unavailable",
  ]);
  delete r.baseline.tokens;
  assert.deepEqual(balanceRow(context.evmViewModel(r), "WETH · Initial"), [
    "WETH · Initial",
    "Unavailable",
    "Unavailable",
    "Unavailable",
  ]);
});
test("resealed contradictory scenario units and accounting fail display validation", async () => {
  const mutations = [
    (r) => {
      r.scenario.tracked_tokens = null;
    },
    (r) => {
      r.scenario.tracked_tokens[0].decimals = true;
    },
    (r) => {
      for (const b of ["baseline", "candidate"]) r[b].tokens[0].decimals = 6;
    },
    (r) => {
      for (const b of ["baseline", "candidate"])
        r[b].tokens[0].symbol = "WRONG";
    },
    (r) => {
      r.baseline.tokens[0].balance_delta_raw = "2";
    },
    (r) => {
      r.baseline.metrics.balance_delta_wei = "-1";
    },
    (r) => {
      r.comparison.final_balance_delta_wei = "1";
    },
    (r) => {
      r.candidate.tokens.push(r.candidate.tokens[0]);
    },
    (r) => {
      r.scenario.tracked_tokens.push(r.scenario.tracked_tokens[0]);
    },
    (r) => {
      r.candidate.tokens[0].initial_balance_raw = "-1";
    },
    (r) => {
      r.candidate.tokens[0].final_balance_raw = (2n ** 256n).toString();
    },
    (r) => {
      r.candidate.tokens[0].balance_delta_raw = "-0";
    },
  ];
  for (const mutate of mutations) {
    const r = aaveActions();
    mutate(r);
    const { artifact_id, ...body } = r;
    r.artifact_id = await context.hashValue(body);
    await context.checkHash(r);
    assert.throws(() => context.evmViewModel(r), /Invalid|Mismatched/);
  }
});
test("36-decimal changes and uint256 values never pass through Number", () => {
  const r = aaveActions();
  const max = (2n ** 256n - 1n).toString();
  r.scenario.tracked_tokens[0].decimals = 36;
  for (const branch of ["baseline", "candidate"]) {
    const t = r[branch].tokens[0];
    t.decimals = 36;
    t.initial_balance_raw = max;
    t.final_balance_raw = (BigInt(max) - 1n).toString();
    t.balance_delta_raw = "-1";
  }
  assert.equal(
    balanceRow(context.evmViewModel(r), "WETH · Change")[1],
    "-0.000000000000000000000000000000000001",
  );
  r.candidate.tokens[0].address = r.candidate.tokens[0].address
    .toUpperCase()
    .replace("0X", "0x");
  assert.equal(balanceRow(context.evmViewModel(r), "WETH · Change")[3], "0");
});

test("duplicate symbols keep distinct addresses in each balance row", () => {
  const r = aaveActions();
  r.scenario.tracked_tokens[1].symbol = "WETH";
  for (const branch of ["baseline", "candidate"])
    r[branch].tokens[1].symbol = "WETH";
  const v = context.evmViewModel(r);
  assert.equal(
    balanceRow(
      v,
      "WETH (0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2) · Final",
    )[1],
    "1",
  );
  assert.equal(
    balanceRow(
      v,
      "WETH (0x4d5f47fa6a74757f35c14fd3a6ef8e3c9bc514e8) · Final",
    )[1],
    "10.000000094454558462",
  );
});

test("recorded report queries accept only one allowlisted example", () => {
  for (const name of [
    "liquidity-shock",
    "recovery-trap",
    "depeg-stress",
    "ethereum-uniswap-slippage",
    "agent-local-codex",
    "aave-borrow-actions",
  ])
    assert.equal(context.reportFromQuery("?report=" + name), name);
  assert.equal(
    context.reportFromQuery(
      "?token=irrelevant&report=ethereum%2Duniswap-slippage",
    ),
    "ethereum-uniswap-slippage",
  );
  for (const query of [
    undefined,
    null,
    3,
    "",
    "?report=",
    "?report=local-report",
    "?report=loading",
    "?report=no-report",
    "?report=../private",
    "?report=https://example.invalid/data",
    "?report=AAVE-BORROW-ACTIONS",
    "?report=aave-borrow-actions&report=liquidity-shock",
    "?report=aave-borrow-actions&report=aave-borrow-actions",
    "?report=%FF",
    "?" + "x".repeat(2048),
  ])
    assert.equal(context.reportFromQuery(query), null);
});

test("example links discard unrelated query, fragment and URL credentials", () => {
  assert.equal(
    context.reportExampleUrl(
      "aave-borrow-actions",
      "https://name:password@entrotter.github.io/sub/index.html?token=not-a-secret&report=local-report#private-file",
    ),
    "https://entrotter.github.io/sub/index.html?report=aave-borrow-actions#report-explorer",
  );
  assert.equal(
    context.reportExampleUrl("liquidity-shock", "http://127.0.0.1:8000/"),
    "http://127.0.0.1:8000/?report=liquidity-shock#report-explorer",
  );
  for (const name of [
    "local-report",
    "../private",
    "no-report",
    "loading",
    "unknown",
  ])
    assert.equal(
      context.reportExampleUrl(name, "https://entrotter.github.io/"),
      null,
    );
  for (const url of [
    "",
    "bad url",
    "file:///private/report.json",
    ["javascript", "alert(1)"].join(":"),
    "data:text/html,private",
  ])
    assert.equal(context.reportExampleUrl("aave-borrow-actions", url), null);
});

test("actual startup opens a direct example and rejects ambiguous query selection", () => {
  for (const [query, wanted, opens] of [
    ["?report=aave-borrow-actions", "aave-borrow-actions", true],
    ["?report=local-report", "liquidity-shock", false],
    [
      "?report=aave-borrow-actions&report=liquidity-shock",
      "liquidity-shock",
      false,
    ],
    ["", "liquidity-shock", false],
  ]) {
    const requests = [];
    class Element {
      value = "liquidity-shock";
      hidden = false;
      textContent = "";
      classList = { add() {}, remove() {} };
      addEventListener() {}
      setAttribute() {}
      removeAttribute() {}
      replaceChildren() {}
    }
    class Details extends Element {
      open = false;
      scrolls = 0;
      scrollIntoView() {
        this.scrolls++;
      }
    }
    const selector = new Element(),
      explorer = new Details(),
      other = new Element();
    const startup = vm.createContext({
      document: {
        getElementById: (id) =>
          id === "scenario"
            ? selector
            : id === "report-explorer"
              ? explorer
              : other,
      },
      HTMLSelectElement: Element,
      HTMLDetailsElement: Details,
      crypto: webcrypto,
      TextEncoder,
      URL,
      URLSearchParams,
      location: { search: query, href: "https://entrotter.github.io/" + query },
      fetch: (path) => {
        requests.push(path);
        return new Promise(() => {});
      },
    });
    vm.runInContext(productionCode, startup, { timeout: 2000 });
    assert.deepEqual(requests, ["reports/" + wanted + ".json"]);
    assert.equal(explorer.open, opens);
    assert.equal(explorer.scrolls, Number(opens));
  }
});
