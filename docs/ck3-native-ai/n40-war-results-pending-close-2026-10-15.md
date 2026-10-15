# Deferred native war-results close observation

Actual N40 P02 AUTO47 returned pending: the owner callback returned without
exception and handled the request, while immediate post-observation still saw
the window visible. The old classifier allowed only a callback that had not
yet run and halted this valid pending form.

FINAL05 adds the exact owner-completed, callback-returned pending form, requiring
the existing actor/date/generation binding, completed owner ticket, visible
post-observation and closure_verified=false. It grants no closure or material
credit and authorizes no repeat close. Control48 installed the classifier;
control49 reconsumed original AUTO47 locally, with zero new MCP/Native calls.

The next ordinary read, AUTO52, observed the window hidden. Root also reviewed
the actual recording scene ROOT-POST-PENDING-CLOSE47-SCENE.png captured at
2026-10-15T05:20:59Z. The game date remained 1076-12-08, within the user's weak
ten-game-day target. The original AUTO47 remains pending in immutable evidence.

The external package is p19-war-result-close-pending under the current Robert
demonstration output root. Fifteen focused checks pass, covering ACK-only,
wrong-scope and false-credit rejection. The later hidden read remains readonly.
All other classifier functions are AST-identical to FINAL04.

The tracked n40-classifier-final04-to-final05 patch and JSON under
tools/g2_saved_campaign/patches retain exact base/candidate SHA-256 values.
Apply only to exact FINAL04 using the recorded argv, explicitly normalize the
output to UTF-8 LF, then verify FINAL05. This normalization is required because
FINAL04 was CRLF and FINAL05 is LF. Isolated replay verified complete bytes.
