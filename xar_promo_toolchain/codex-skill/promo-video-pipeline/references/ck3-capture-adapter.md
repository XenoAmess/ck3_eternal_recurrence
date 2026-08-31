# CK3 capture bundle adapter

Use `xar_promo.adapters.ck3.load_capture_bundle` when a promo project wants to
reuse a CK3 acceptance-run recording. The adapter is a read-only integrity and
timeline projection layer. It does not capture the desktop, invoke OCR, decide
which characters may appear, or enforce project-specific text policy.

## Input layout

The artifact root has three fixed control files and one timeline-selected raw
recording:

```text
<artifact-root>/
  report.json
  evidence-index.json
  cell/promo/capture-timeline.json
  ... timeline.raw_path ...
```

The evidence index does not index itself. The loader therefore verifies the
indexed bytes and SHA-256 values for the report, timeline, raw recording and
clean-frame evidence, then independently computes the index file's own bytes
and SHA-256 for downstream manifest binding.

## Stable entry point

```python
from xar_promo.adapters.ck3 import load_capture_bundle

bundle = load_capture_bundle(
    artifact_root,
    required_span_ids=("feature_overview", "result_screen"),
    required_mark_labels=("feature_overview_clean_begin",),
)
```

The return value is an immutable `CaptureBundle` projection:

- `report`, `timeline`, `evidence_index`, and `raw_capture` are verified
  `CaptureFile` records.
- `marks` preserves the producer's ordered timeline marks.
- `clean_spans` contains positive begin/end windows plus all hash-bound frame
  evidence referenced by their gate records.
- `mark(label)` and `clean_span(span_id)` provide stable lookup helpers.
- `recording_start_seconds` and `recording_stop_seconds` bound every projected
  clean span.

Project vocabulary belongs in the optional `required_*` arguments or a higher
policy layer, never in the adapter.

## Fail-closed contract

Loading is rejected when any of these conditions fail:

- report root and cell are not schema v1 GREEN;
- the evidence index is not schema v1 GREEN or names another artifact root;
- the report's `cell.promo_capture` is not exactly the timeline object;
- an indexed or inline evidence record has missing, escaped, duplicate,
  byte-mismatched, or SHA-mismatched content;
- the raw recording is outside the run or disagrees with timeline bytes/hash;
- the timeline does not attest `exclude_ck3_loading=true`, classify itself as
  real CK3 after the gameplay HUD, and begin with
  `recording_started_after_gameplay_hud`;
- marks are negative, unordered, duplicated, missing the stop mark, or produce
  a non-positive recording window;
- clean capture is incomplete, a clean span is missing, non-positive, outside
  the recording window, non-GREEN, or lacks exact begin/end frame gate proof;
- caller-required marks or spans are absent.

The HUD check is an attestation boundary, not a new pixel inspection: the
producer must establish a clean gameplay HUD before recording and emit the
start mark. The adapter verifies the declaration, order and time bounds. It
does not claim to independently recognize the HUD.

All failures raise `CK3CaptureError`. The loader never deletes, repairs,
renames, or rewrites the run, so RED and incomplete attempts remain available
for diagnosis and later comparison.
