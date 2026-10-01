# Recorded submission review cuts

Recorded September 20, 2026. The [submission index](../../submission/README.md)
links both actual MP4 files and captions. `manifest.json` records exact source
pins, output and evidence SHA-256 hashes, local-only raw capture/audio/model hashes,
measured durations, actual execution, cleanup and explicit remaining limits.

The demo continuously captures real Chromium interaction with the unchanged
website review branch, including a previous Ethereum/Uniswap adverse report,
a new bounded local risk run and exact replay, importing its generated JSON,
rejecting a deliberately incorrect hash and recovering. `actual-execution.log`
is the actual subprocess output, not a simulated terminal. `agent-replay.json`
is exactly equal to the original public local model artifact. The invalid copy
is an intentional negative input, not a successful result.

`production-*.gz` are byte-for-byte archives of the one-off local recording aids,
not installed product modules or newly quality-gated production sources. They
retain the precise executed harness, including its fixed workspace paths and
assertions. Their original-byte hashes are in the manifest. They must not be
mistaken for a portable supported media-generation command. The unused
`ENTROTTER_EXPORT_STATE` setting in the recorder was not recognized by the engine;
the real export used the normal shared default ledger. No quota ledger was reset.

To inspect any archive without executing it:

```bash
python3 -c 'import gzip; print(gzip.open("evidence/submission-media/production-live_run.py.gz", "rt").read())'
```

Production used local Piper synthesis (32 narration cues), then continuous
Playwright captures, then FFmpeg 9.0.1 H.264/AAC encoding with loudness normalization
and 48 kHz output audio. The raw WebM files and WAV tracks are retained locally;
the final MP4s and exact timelines are committed. No cut or speed change conceals
execution. The viewer branch and worker image pins are distinct from the live
site and frozen benchmark implementation.

Both full MP4 decodes exited zero with no error output. FFprobe records one
1600×900/25 fps H.264 stream and one mono AAC stream per file. Every caption ends
within its video's duration. Final sample frames show readable UI and captions;
all eight pitch cards passed the captured overflow check. Chromium requests were
only same-origin loopback GETs (eight pitch, nine demo), with zero page errors.
These observations cover the recorded session, not every browser or accessibility
technology. Audio analysis reports pitch −16.8 LUFS/−1.1 dBFS peak and demo
−16.7 LUFS/−1.2 dBFS peak. Human listening approval remains pending.

The media venv's complete eight-package inventory, including pip, passed strict
advisory audit without reported findings at capture time. This optional authoring
toolchain is not a product dependency and does not claim a fully hash-locked
installer. The pinned voice LFS digest was checked; weights are not redistributed.
See [disclosure and credits](../../submission/DISCLOSURE.md).

A read-only event-account inspection reached the account-creation page without
entering any fields. This does not establish whether the owner registered in a
different session. No terms acceptance, registration, outreach, submission or
video-platform upload occurred. No owned containers remained after execution;
the dedicated VM, preview server and browsers were stopped/closed. Both Colima
profiles are stopped and the default Docker context is unchanged.

Independent code approval, owner facts/video review and three genuine user
sessions remain open. This evidence advances G5; it does not complete the goal.
