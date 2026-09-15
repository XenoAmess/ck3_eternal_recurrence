# User picture corpus v8 native r10

This append-only environment/transport RED run used repository commit
`145c2e9d5d7abb8af21097889b588c18a374453e`.

The direct foreground exception was caught, but attaching only the MCP thread
to the then-foreground thread still did not make the exact CK3 root the stable
foreground window. The explicit preparation and the subsequent calibration
capture therefore failed closed. No framebuffer metrics or crops were emitted.

The superseding implementation also attaches the CK3 target window thread,
repeats restore/top/active/foreground while the three input queues are joined,
detaches both joins in reverse, and verifies the exact root. Framebuffer capture
can now invoke the same bounded preparation atomically if focus changes between
the separate prepare and capture MCP calls. A failed advisory prepare no longer
overrides a successful atomic calibrated capture.

All seven large Apply/Copy operations still ran. Steam remained offline, and
the managed CK3 process tree was proven gone before releasing the slot.
`summary.json` is the compact receipt; the ignored local raw report is bound by
the byte count and SHA-256 recorded there. r11 supersedes r10 for framebuffer
evidence.
