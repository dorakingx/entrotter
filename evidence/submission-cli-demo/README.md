# Exact CLI inspection in the product demo

[Watch the edited 2:36.80 review cut](../../submission/media/entrotter-demo-cli.mp4),
with unchanged [VTT](../../submission/media/entrotter-demo-cli.vtt) and
[SRT](../../submission/media/entrotter-demo-cli.srt). It adds actual current CLI
output to the [October 3 account recording](../submission-account-demo/README.md).
All 13 prior media/probe files remain byte-exact; this is additional review
material, not an owner-approved replacement, merged release, Pages deployment,
supported-host upload or submitted entry.

Three picture-only intervals show why a developer can use the same records from
the command line and in scripts:

| Interval | Actual output | Explanation |
| --- | --- | --- |
| 49.72–58.88 seconds | [Whole price text](price-text.txt) | The separate original 32-transaction WETH case: exact after prices and +7.89973126 USD difference, not profit |
| 84.56–94.92 seconds | [Whole account text](account-text.txt) | Original 13-transaction account, all six metrics, exact +816.28966124 USD capacity and +0.003852169807877337 health-factor differences, aggregate prefix effects |
| 136.00–146.12 seconds | [Complete JSON](complete.json), [incomplete JSON](incomplete.json), [actual stderr](incomplete.stderr) | The same account verifies with exit0; an explicitly labelled [synthetic removed-view control](synthetic-missing-account.json) keeps internal integrity but returns3 with unavailable comparison differences |

The price32 and account13 records are distinct cases. They are not new historical
executions or proof of consumer strategy, profit, full-block state or provider
authenticity. The synthetic control removes only account observation1's data,
adds its explicit timeout, makes comparison fields unavailable and reseals the
outer content identifier. Other account fields, nested price/trace records and
original receipts are preserved. This does not invent an observed historical
failure. The gate display extracts two fields from the saved whole JSON; it is
not a replacement for the complete report.

Four real offline command calls use installed CLI
[24bbb91](https://github.com/entrotter/cli/tree/24bbb916555ef18528300f995e127d50ff29167e)
and SDK [ba4af51](https://github.com/entrotter/sdk-python/tree/ba4af512784119f23b6dea63fd24c7f5d1fdde44).
Every installed Python source byte matches all13 immutable source modules.
The isolated interpreter removes PYTHONPATH, lacks Engine, and rejects socket,
SDK HTTP and execution/export attempts. Price and account stdout match the entire
reviewed goldens; the complete JSON retains its earlier exact hash. Full outputs
and return codes are saved before assertions in [execution](execution.json).
The original footage still binds viewer8aa0/CLI6965/Engine88c6 and contains its
earlier two local-EVM calls. Reusing that footage does not rerun those calls or
turn it into a fresh viewer422d recording. No new EVM/model/archive/API call occurs.

Chromium displays saved actual stdout in clearly labelled recording aids, without
simulated terminal typing. [Capture](capture.json) records three loopback GETs,
three served HTML hashes, exact text equality, non-overflow bounds and zero JS
errors. The [price](frame-price.png), [account](frame-account.png) and
[script gate](frame-gate.png) frames show the final encoded picture and captions.

The [cut list](cut-list.json), [filter graph](filter-graph.txt),
[exact render argv](render-command.json) and gzip producer sources preserve the
three overlay ranges. Audio is mapped once and copied: every one of7331 packet
data hashes, PTS/DTS/duration/size/flags matches the source, and VTT/SRT are
byte-identical. [Audio/caption proof](audio-caption-proof.json) and compressed
whole packet inventories retain that evidence. Burned captions retain content,
placement and timing; the picture is reencoded, so pixel equality is not claimed.

The final MP4 has3920 frames, H2641600×90025fps and one48kHz AAC stream. It fully
decodes with zero errors, as recorded in [probe](probe.json) and the empty compressed
decode log. [Boundary proof](boundary-proof.json) checks the frame immediately
before/start/end-minus-one/end of all three overlays against the expected picture
and original caption region. Minimum picture SSIM is0.989736 and caption SSIM
is0.998429; these are lossy picture-fidelity checks, not performance metrics or
human auditory approval. Source [before](frame-before-price.png),
[after](frame-after-price.png) and [closing](frame-end.png) frames retain continuity.

[Manifest](manifest.json) binds media, public evidence, retained raw originals,
source helpers, earlier-media preservation and failed authoring attempts. Public
execution/render JSON and encode logs normalize only absolute workspace paths;
their raw originals/hashes remain local. Source producer gzip files are one-off
authoring helpers, not newly quality-gated product modules or a supported portable
generation command. Initial account overflow, unsupported FFmpeg option and
malformed boundary filter failures remain retained; none is selected successful
proof. Human auditory review and supported-host delivery remain pending. Existing
independent approval and required CI cannot be replaced by this media check.
