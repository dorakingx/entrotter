# Native keyboard chooser diagnostics

The optional browser runner keeps chooser interception subscribed before page
navigation. Every keyboard import still awaits the actual native file chooser
within the existing5000ms limit and verifies its input ID. There is no retry,
programmatic upload fallback or relaxed timeout. Failure JSON contains only
bounded focus/input state and Enter completion; it contains no report contents
or URLs. If diagnostic capture also fails, the final check record includes the
primary and capture exceptions, each bounded4096 characters.

[Local checks](local-checks.json) distinguish nine passing targeted baseline
activations from the full initial candidate's actual320px timeout. At that failure,
the correct file input was focused, enabled, connected and visible; Enter had
completed. This does not identify why the native chooser event was absent.
The early-subscription candidate passes all49 groups/62 raw axe scans with zero
violations or JavaScript errors. These are single execution results, not a
measured reliability rate or proof of the original cause.

[Four real browser controls](fault-controls.json) deliberately prevent Enter,
recover through an actual chooser, rename its input before activation and make
the diagnostic target a directory. The last control uses the real check
serialization and proves the original5000ms timeout and EISDIR error remain in
the final record. Before the serialization fix, that assertion failed. Deliberate
DOM/filesystem mutations are diagnostic tests, not original-failure reproduction.
Public error paths use `<local-checkout>`; complete raw originals remain private.

The full passing runner snapshot is retained. Pinned Prettier3.9.8 transforms it
byte-for-byte to the current source; the current formatted helper also passes the
four controls. All149 earlier security reasons match exact finding source spans,
and one new local diagnostic-write finding has an explicit rationale. Production
app/report bytes, schemas, locks, workflows and older evidence are unchanged.
Current-head CI, independent review, protected human main approval and live Pages
remain separate. No new chain/model/package/performance/user run is claimed.
