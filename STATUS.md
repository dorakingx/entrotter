# SDK status

The trace-reader candidate adds offline typed inspection of the original signed
transaction-prefix family while retaining the v0.1 HTTP client. All36 local tests,
5-source lint/format/types and full unsuppressed Bandit checks pass; a fresh
isolated wheel reads the exact original engine817 four-prefix gas/nonce data.
Independent review found four metadata/receipt consistency gaps; fixes and
focused regression vectors pass and independent follow-up found no remaining
actionable finding. Remote CI and protected-main approval remain separate. See [retained evidence](evidence/trace-reader/README.md).

Content integrity and internal consistency do not authenticate signatures,
source state or EVM truth. Broader core/release gates remain in the coordination
repository. Packages remain unpublished; protected-main approval remains open.
