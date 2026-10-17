# R197 military reinforcement request admission defect

machine_id: `desktop-3fevhd2-1c74096080`
Source: `85eb547cca4fddaec4b8a89ec9dd203e6935299c`
Observed: 2026-10-17 UTC; this package is offline source work, not a live toggle result.

The two advertised military reinforcement actions were missing from production `GameAdapter::supports_step`. The native bridge therefore rejects the exact action name before reaching its existing action handler. The patch adds the two exact step-to-capability mappings; it preserves each capability's independent admission and the existing default-OFF build flag.

At this source revision:

| Source | Evidence |
| --- | --- |
| `ck3_12004_adapter.cpp:90–93` | The ON descriptor advertises both action capabilities. |
| `game_adapter.cpp:482–485` | The map goes straight from the military opener to decisions. Neither reinforcement action is mapped anywhere in this function. |
| `game_adapter.cpp:745` | An empty mapped capability returns false, even when the descriptor advertises the capability. |
| `bridge.cpp:15976–16231` | The outer unsupported gate checks `!game.supports_step(step)` and has no exception for these two steps. It emits `unsupported native gameplay step`. |
| `bridge.cpp:18827–18876` | The fixed reinforcement handler is in the subsequent dispatch block. Its main-thread mailbox submission is at 18852. |
| `bridge.cpp:15311–15493` | The same generic error string also exists in the terminal fallback lambda. The SDK error text alone does not identify which C++ return site actually executed. |

Python has both exact step routes and forwards the step unchanged. The real SDK rejection is evidence of a returned native `ok=false` result, not a Python unsupported-capability exception. The supplied public revision 4 is not the native revision. The old adapter did not preserve the exception's native packet fields, so the outer SDK response alone does not recover that native revision or a dynamic C++ instruction trace.

The source control flow proves that this version's exact action cannot pass the outer admission gate to its original GUI handler. There is no positive evidence that R197 invoked that handler or the GUI primitive. This is a source-backed explanation of the observed error; a real command-entry trace or native packet would be needed to label a particular return instruction as dynamically observed. No replay is authorized or needed in the still-active scene.

## Candidate and focused verification

Apply `native-admission.relative.patch` to exact base 85eb. Only `game_adapter.cpp` and its existing `game_adapter_test.cpp` change. No CMake option, target, bridge gate, handler, source selector, callback or build flag changes. No full source copies are stored.

The new focused case calls the real production `GameAdapter::supports_step` through the existing `StubAdapter`. It checks the actual .4 ON/OFF descriptor, independent enable-only and disable-only descriptors, disabled adapter, opener-only descriptor, exact-name rejection and older actual descriptors. The pre-fix implementation fails the first actual ON descriptor check and also the single-capability cases. The case neither invokes the GUI nor asserts a toggle.

Root's future native build target: `xar_ck3_adapter_registry_test`
Run only: `xar_ck3_adapter_registry_test.exe --military-reinforcement-admission-only`
Expected ON output: `PASS: military reinforcement production admission checks=24 feature=1; no GUI dispatch or toggle claimed`

Native compile/run: **NOTRUN**, forbidden in this lane. `git apply --check`: PASS against 85eb. Do not substitute the old serializer fixture for this newly required production-admission case. After a new qualified DLL and fresh scene, one authorized action still needs an independent later military tree and actual desired switch byte before receiving toggle credit. Actual refill ADD remains unqualified.

The optional independent Python delta `python-lane/failure-evidence.relative.patch` preserves a rejected primitive's request/result frames in `.failure.json`; it retains the unknown claim and blocks a second send in either direction. Its one new production-primitive behavior case passed. This diagnostic delta does not repair native admission and cannot restore packets absent from the historical R197 response.

## Boundary

No SDK, game, desktop, EXE read, native compile, native execution or main-tree mutation occurred here. The real initial R197 source-owner byte was 1; this failed action provides no observed 1→0 transition, provider invocation, selected receiver, variable-table resolution or soldier ADD. Keep the historical failure and its unknown claim intact; use a fresh qualified scene rather than clearing it for a retry.
