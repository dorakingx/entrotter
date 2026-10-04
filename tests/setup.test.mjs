import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { webcrypto } from "node:crypto";
import {
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { delimiter, join } from "node:path";
import vm from "node:vm";

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
    throw new Error("Setup tests must not contact the network");
  },
});
vm.runInContext(
  readFileSync(new URL("../app.js", import.meta.url), "utf8"),
  context,
);

test("copied setup stops at each failed Git operation and preserves its status", () => {
  const setup = context.reportCliRecipe("aave-borrow-actions").setup;
  const expected = [
    "clone https://github.com/entrotter/cli.git entrotter-cli",
    "-C entrotter-cli checkout --detach 169b759aff9280ce44fb0d15569c7ae0a4a40889",
    "clone https://github.com/entrotter/sdk-python.git entrotter-sdk",
    "-C entrotter-sdk checkout --detach ba4af512784119f23b6dea63fd24c7f5d1fdde44",
  ];
  for (const name of [
    "liquidity-shock",
    "recovery-trap",
    "depeg-stress",
    "ethereum-uniswap-slippage",
    "agent-local-codex",
  ])
    assert.equal(context.reportCliRecipe(name).setup, setup);

  const directory = mkdtempSync(join(tmpdir(), "entrotter-setup-"));
  try {
    const bin = join(directory, "bin");
    mkdirSync(bin);
    // A finite Git stand-in records argv and returns a distinct failure status.
    // The actual copied shell text executes; no clone or network is performed.
    writeFileSync(
      join(bin, "git"),
      '#!/bin/sh\nprintf "%s\\n" "$*" >> "$STEP_LOG"\n' +
        'step=$(wc -l < "$STEP_LOG")\n' +
        'if [ "$step" -eq "$FAIL_AT" ]; then exit "$((40 + step))"; fi\nexit 0\n',
      { mode: 0o700 },
    );
    for (const failure of [1, 2, 3, 4, 0]) {
      const log = join(directory, `steps-${failure}.txt`);
      const result = spawnSync("sh", ["-c", setup], {
        cwd: directory,
        encoding: "utf8",
        timeout: 5000,
        env: {
          ...process.env,
          PATH: `${bin}${delimiter}${process.env.PATH ?? ""}`,
          STEP_LOG: log,
          FAIL_AT: String(failure),
        },
      });
      assert.equal(result.error, undefined);
      assert.equal(result.status, failure === 0 ? 0 : 40 + failure);
      assert.equal(result.stdout, "");
      assert.equal(result.stderr, "");
      assert.deepEqual(
        readFileSync(log, "utf8").trim().split("\n"),
        expected.slice(0, failure || expected.length),
      );
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});
