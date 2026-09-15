# User picture corpus v8 native r9

This is an append-only environment/transport RED run against repository commit
`f9ffe5e4b797acf5618a57e139c4dd8aee7c250c`.

The first structured framebuffer preparation reached the correct CK3 designer
route, but Windows rejected the initial `SetForegroundWindow` call. The MCP
preparation function propagated that Win32 exception before entering its
existing `AttachThreadInput` fallback. The v3 calibration therefore had no
begin frame and correctly failed closed; no framebuffer comparisons or native
crops were produced.

All seven large sources still completed native Apply/Copy. Pictures 01, 03,
04, and 06 passed strict semantic sequence comparison. Pictures 02, 05, and 07
retained the separately tracked native Copy fractional-rotation normalization
mismatch.

Steam remained offline. The managed CK3 process was stopped and its process
tree was proven gone before the shared slot was released. `summary.json`
contains the compact reviewable receipt. The raw report remains local and is
identified by byte count and SHA-256 in the summary.

The superseding fix catches a direct Win32 activation exception and proceeds
through the already bounded thread-attachment fallback. A unit test reproduces
the exact sequence: direct activation raises, attached activation succeeds,
the attachment is detached, and the exact route-bound CK3 root is verified as
foreground. r10 supersedes r9 for framebuffer evidence.
