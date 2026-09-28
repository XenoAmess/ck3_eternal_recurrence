# E2-05 a02 postrun media audit (2026-09-29 CST)

The sealed E2-05 a02 recording was audited after FFmpeg exited naturally and the
`ck3-screen` lease was released (task-bus seq 2007). This is a machine media and
evidence-link result, not a clean-span or human review decision. The capture
identity and single day-26 to day-27 action are recorded in
[the sealed capture outcome](e2-05-a02-capture-outcome-20260929.md).

The append-only audit attempt is
`D:/workspace/ck3_native_war_ai_promo_work/e2-05-a02-postrun-audit-20260929-a01/`.
Its `pts-audit.json` is 1,694 bytes, SHA-256
`A3A9243E48D987134664F1A0E951938E17A0CA36D86B50750AFAA6CA4BD8645A`;
`postrun-links.json` is SHA-256
`213988D4278A26EFD4AA93BD8FE8DA2A56234D9B5EC3B1AE019EB53212B0EB0C`.
The auditor used isolated script commit `8cb8dcb79`, subsequently incorporated
into the episode branch. An independent reviewer rehashed the small reports and
sidecars and confirmed the recorded references without opening the raw video or
full ffprobe again.

The full PTS audit binds the original 2,451,530,594-byte MKV to SHA-256
`7FC3D614C50AD958DA57359248A196A230BD2B0B5B511EF242596837042C1C0F`
and the 12,044,180-byte ffprobe to SHA-256
`06A9C1FB92983390F6EE5FA48352732B09E01C4336B4D956F9CECC19F7C3A1FB`.
All 12,656 video frames have PTS from 0.000 to 599.967 seconds. Missing PTS,
nonmonotonic PTS, and gaps greater than 0.2 seconds are each zero. The raw
video was fully hashed once; the link audit checked its stable size and mtime.

The link audit matched recorder intent/start/end/final, ordered marks and their
small screenshots/control reports, the managed session cleanup, and the capture
report. It recorded `PTS_CONTINUOUS_UNREVIEWED` and
`MEDIA_PTS_CANDIDATE_UNREVIEWED`. The three navigation marks are `d26-before`
at about +190.884 seconds, `d27-after` at +304.990 seconds, and
`d27-player-knights` at +388.113 seconds; those wall-clock offsets are not
video PTS or proof that a target event is visible.

The audit leaves `target_event_visual_verified=false`,
`adapter_bundle_validated=false`, `clean_spans_certified=false`,
`human_1x_review_performed=false`, and `film_signoff_granted=false`.
The day-27 trace is separately under fact review; this PTS result cannot prove
a death, a full native write set, or a usable scene.
