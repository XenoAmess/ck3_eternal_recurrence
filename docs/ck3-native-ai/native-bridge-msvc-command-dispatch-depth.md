# MSVC command dispatcher nesting: actual C1061

On 2026-10-02, the exact `1a0a3ca0027face9e10714ec70bf3ca4eafc8469`
native bridge build failed with `bridge.cpp(24062): fatal error C1061`.
The explicit configuration was 63 feature flags ON and six OFF, `/W4 /WX`,
with 64 build jobs. The original failed build remains in
`artifacts/g2-maintainer-2026-10-02/resume-12003/native-build-county-finance-v18/`.
Official static CI success for this commit did not qualify a production DLL.

The affected code was the terminal portion of the long command dispatcher.
The fix moves its existing merge, assault, event-option and fixed-speed handlers
into a local capturing lambda declared beside `step`, and invokes that lambda
from the original terminal `else`. Handler conditions, order, result frames and
snapshot publication stay in their original relative order. This is a compiler
structure change; it introduces no new game action or feature flag.

The exact production translation unit compiled once with the unchanged feature
flags and `/W4 /WX` after this patch. The receipt is
`native-build-county-finance-v18/c1061-command-tail-fix-01/RESULT.json`,
SHA-256 `4031c0c64565cbfc850c9619c06012f377867b7957573db70d5fb885a1e8cf3d`.
Complete DLL linkage and real paused-query qualification remain separate checks.
