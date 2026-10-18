# V5 duration profile candidate

V5 adds an explicit 3240-second (54-minute), 168-segment planning profile. The
legacy default remains 1860 seconds and the measured V4 padding profile remains
2101 seconds. Geometry, frame rate, 3 Mbps VBV, 192 kbps audio, CRF and preset are
unchanged. Selecting this profile is not capacity admission. The actual approved
voice clock, native ProjectConfig limit and same-batch fresh storage admission
must still bind the eventual build; the full theoretical limit is not a grant.

The same existing nondefault path requires the canonical repository music and
selected ProjectConfig. It retains actual music mixing, the corrected zero-lag
music proof, grouped subtitles and 30 fps clock. This patch does not change these
functions, start any provider or create media. Use the actual new voice duration
to narrow the later request; do not revive the closed V4 reservation.
