# Security

Experimental research software. Do not use production keys, custody real
funds, or expose the local engine port or Anvil JSON-RPC to the Internet.
This is not a trading execution service. Mainnet broadcast is not supported.

The separate offline trace reader executes no report code or chain writes. It
checks bounded JSON, content integrity and reported receipt/nonce consistency;
it does not verify recovered senders, signatures, transaction/header hashes,
archive authenticity or EVM truth. An attacker can forge internally consistent
data and reseal it. Preserve the report's source and limitations when sharing
results. It adds no trace HTTP endpoint or arbitrary agent execution.

The observed-price reader is also offline and executes no report code. It
accepts one fixed profile and finite diagnostic fields, caps regular-file input
and raw observations, and validates the nested trace and reported classification.
Checksums, ABI consistency and recorded price dependence do not authenticate
providers, deployed contracts or a signed strategy. Never treat a complete price
view as profit or financial advice. The wrapper's original scope is preserved.

The engine runs only built-in policies. A Python import or a subprocess is
not a security sandbox for untrusted agent code. Container/process sandboxing,
egress controls, authenticated multi-tenancy and a production job queue remain
release gates before any hosted service is made available.

Do not post secrets or exploit details in public issues. Use GitHub private
vulnerability reporting where enabled. If it is not yet enabled, ask the
maintainers in an issue to enable a private channel without disclosing details.
RPC URLs can contain secrets: never include them in reports, commands in
screenshots, logs, pull requests, or issue bodies. The optional fork URL may
be visible to other processes owned by your OS user; run on a trusted machine.
