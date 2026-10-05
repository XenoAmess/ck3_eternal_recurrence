R9 explicit direct-native checkpoint reader (source HEAD54457b371).

Run with the pinned Python313 executable and -B:
read_r9_native_c2.py --request REQUEST.actual-0058-attempt002.json
Supplement: supplement_selected_protections_native.py REQUEST.selected-protections-0058.json

The new request v2 distinguishes SDK_SAVE_RECEIPT from NATIVE_PROFILE_SAVE_RECEIPT. Raw native JSON cannot enter the SDK branch. Native mode requires original direct native receipt, immutable saved bytes, exact metadata, source/profile/guard process identity and frame, ROOT preservation and actual ERROR_NO_RETRY dispatch receipt. It emits after_sdk=null and sdk_success_credit=false. Only the independently parsed saved AST supports business facts.

The saved-state projector, product details, numeric/typed sourcefields, frame and dependency ASTs are unchanged. Legacy cached projection reuse is pinned to cfee520a... original reader plus exact BINDINGS3475ca7a..., actual source HEAD, saved and SDK refs. All artifact hashes are rechecked after analysis.

11 focused actual metadata/negative challenges passed. 20 actual DETACH conditions matched; positive protections checked separately. Attempt001 refused a writable checkpoint, ROOT corrected its attribute with unchanged bytes, and attempt002 parsed the preserved real save. Both attempts remain. This package changes no game/SDK/registry or old package and grants no full cycle or second JOIN credit.
