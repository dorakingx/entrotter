# Security

Experimental research software. Do not use production keys, custody real
funds, or expose the local engine port or Anvil JSON-RPC to the Internet.
This is not a trading execution service. Mainnet broadcast is not supported.

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

CLI export accounting assumes cooperating versions sharing one private operator
state directory. Pending reservations survive abrupt process death and remain
charged. Never reset the ledger while retaining its outputs. Operator file moves,
other applications, old clients and distinct state roots are outside this budget;
this is not a whole-filesystem quota. Inspect usage with the exports command.


Agent CLI execution uses only the matching engine's bounded `run_agent` primitive:
built-in risk policy or JSON-only replay. It never imports a provider named by a
recording, selects a command/model/image/RPC from metadata, or offers a native
fallback. Inspection does not require an engine. Replay verifies the reference
hash and complete output equality before the existing private/quota-protected
export; these hashes detect corruption, not dishonest producer assumptions.
The engine validates causal request/response bindings and enforces its existing
worker limits. Fork egress, trusted installed packages/images and host overhead
retain the engine's documented boundaries. Do not publish private recordings.


Recorded price inspection delegates bounded file parsing and observation validation
to the pinned standalone SDK. It never instantiates an API client, imports the
engine, executes a report, consumes provider metadata as configuration or writes
an export. SHA-256 and consistency checks establish internal record integrity,
not provider authentication or economic correctness. Valid incomplete views keep
null differences and explicit reasons; status 0 does not mean complete price proof.
