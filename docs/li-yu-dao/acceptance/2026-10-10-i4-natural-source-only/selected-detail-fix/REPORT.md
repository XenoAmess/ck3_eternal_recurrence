# Selected-detail completion correction

Source09 native_driver.py6831-6859 preserves the original native ACK. It independently reads the later actual selected model, then sets postcondition_verified=true/status=verified_selected_detail/verification_pending=false. selected_after_verified can remain false from the original pending ACK. The former adapter incorrectly required that old ACK bit to become true.

The minimal adapter guard now consumes the official final completion plus its actual later selected key/actor/frame, and the existing subsequent independent selected model. It never rewrites the ACK. Unverified, pending, absent later proof, wrong target/actor/frame or a wrong subsequent target reject. No runtime/native/GUI provider change. The existing same-paused model sandwich remains the tree's evidence level; the tree has no own frame IDs.

Actual new subset: 3 tests exit0 at d74b2c880aa1edc8af6fce8245b7b7275843c59c, source unchanged during tests. Prior17 class AST and old17 receipt remain exact; no historical suite rerun. Only adapter/test/doc changed. STATIC_READY remains source-only; no game/SDK/process/desktop/save body or new live identity/action.

Storage: small create-only external packet, <=64KiB; policy1.0.0. Derived runner/patch review48h; records review180days; no indefinite retention. Root owns commit/push and live preflight.
