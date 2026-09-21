# Delta-Q anonymous A/B review sheet

[`contact-sheet.png`](contact-sheet.png) places the frozen input beside two
unlabelled candidates for each of the seven real cases. A/B assignment is
deterministic from `SHA-256("delta-q-ab-v1:<case-id>")[0]` parity; the sealed
role and byte hashes are recorded in [`mapping.json`](mapping.json).

The sheet SHA-256 is
`819712307D3E7EFA3C136925283E89F19F8192D592535E2DB68948FA7C0F1F7D`.
It compares the v14 quality-priority baseline with the Delta-Q v9
quality-first result at canonical 230px. This is review material with status
`pending-human-review`; its generation does not create or imply a human
preference, approval, or signoff.

Rebuild deterministically from the checked-in inputs and candidate previews:

```bat
cd coat_of_arms_editer_of_ck3
..\tools\.venv\Scripts\python.exe tools\build-delta-q-contact-sheet.py --repository .. --output ..\docs\coat-of-arms-fit-artifacts\delta-q-ab-contact-sheet-v1
```
