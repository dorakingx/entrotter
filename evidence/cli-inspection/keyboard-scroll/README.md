# Keep keyboard scrolling failures diagnosable

The original published recipe candidate2f83987 passed local49 groups/62 raw axe
scans, but its GitHub Linux browser job passed48/49 groups and failed320px
liquidity-shock: ArrowRight did not satisfy positive scrollLeft within5000ms.
The61 complete raw scans and original failure logs/metadata/artifact ZIPs remain
retained. Code, quality and documentation jobs succeeded. No cause was established.

A separate actual Chromium probe exercised the unchanged liquidity keyboard flow
at320px and390px once each. Both scrolled successfully with trusted ArrowRight
and the expected focused overflowing element. This did not reproduce or explain
the original Linux failure, and supports no production-code fix or reliability rate.

The development-only scroll helper now asserts the exact focused element and a
real overflow range, retains native ArrowRight and the original5000ms/positive
movement assertion, and saves bounded before/after focus, layout and scroll values
on failure. It saves no report contents, filenames or URLs. Diagnostic capture
failure preserves both primary and secondary exceptions in the check JSON.
[Actual checks](checks.json) bind four fault controls and the full current browser
result. The blocked-key control still fails; a subsequent real key scrolls;
incorrect focus fails before a key is sent; forced diagnostic-write failure keeps
the original timeout. There is no helper retry, simulated scroll or relaxed bound.

Initial private fault harness runs retained an ineffective last injection on a
reused scrolling page and a file-versus-directory setup error. The corrected
fresh-page injection records outcomes before assertions; originals remain retained.
150 existing security reasons match their exact original source spans; one added
local diagnostic write has an explicit review reason. Source19JS/20typed checks
pass with151 full findings and no suppressions. Production sources, original
reports, fixed recipes, workflow/locks and earlier evidence keep their versions.

Current-head GitHub CI and independent protected-human main approval/Pages remain
separate. No chain, model, advisory, timing, execution-authenticity or performance
claim follows from this diagnostic change. Contrast incompletes remain explicit.
