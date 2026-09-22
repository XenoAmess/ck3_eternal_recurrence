# Epsilon-Q v14 sealed programmatic holdout

This report contains 16 sealed deterministic cases: four each for flat
contours, fine detail, color overlap, and texture/gradient structure. Every
case uses a distinct programmatic family and native-shape proxy assets.

- 16/16 cases improved.
- Median relative J improvement: 21.696%.
- 96/230/512px non-regression: 16/16.
- Instance budget respected: 16/16.
- Total elapsed time: 3,957.40 seconds.
- Category medians: 16.593%, 18.917%, 30.098%, and 30.310% respectively.

The benchmark persists progress after every case and resumes from the exact
checkpoint contract. This is a synthetic holdout and does **not** establish
external real-image generalization or native CK3 compatibility.

`report.json` SHA-256 is
`46C154EAB56C409B0C5E0F72476DC716CE5D15E07F6A3C007EA2F809F220A2A9`.
