# Workshop external-operation timeout defaults

The 2026-10-16 user instruction sets a 1800-second default for the publication path, fresh download and anonymous publication readback. These defaults share `DEFAULT_WORKSHOP_TIMEOUT_SECONDS` in [timeouts.py](../ck3_workshop_mcp/src/ck3_workshop_mcp/timeouts.py).

| Operation | Effective default | Boundary |
| --- | --- | --- |
| Native Steam API callback wait | 1800 seconds | Each callback, including create/update publication and preview queries |
| Native download API, MCP tool and both CLIs | 1800 seconds | Existing isolated worker deadline; supervisor retains the extra 15-second collection margin |
| Anonymous publication verifier CLI | 1800 seconds | Each item/changelog HTTP request |

`workshop_native_publish` still accepts exactly `dll_path`, `plan_file` and `receipt_file`. Its plan does not gain a timeout field. The native callback wait is internal; it is not a whole-publication wall-time guarantee. The existing MCP client does not set a shorter request deadline. A client deadline of exactly 1800 seconds would incorrectly consume the time needed for callback completion and receipt handling, so no such wrapper deadline was added.

Download and HTTP callers can retain explicit custom budgets; the download range remains finite, greater than zero and at most 3600 seconds. This change updates defaults rather than rewriting historical receipts or silently clamping explicit test budgets. New operation arguments copied from historical recipes with `timeout_seconds=300` or `--timeout 30` must be bound to 1800 when the caller intends the current default. Polling intervals, callback IDs, uncertain-result handling and once-only publication behavior are unchanged.

The existing cache case remains a separate menu-only boundary. Its public Selection applies the readiness floor (400 requested -> 1800 effective), while its hold900, command300, overall3600 and poll0.5 budgets retain their existing values. This publication package does not change them, repeat gameplay, mount a fixture or alter a frozen runtime/DLL. After menu loading, the original CaseClient retains the real process handle and proves normal OS0/native0; the original public-run and allocation parent waits remain the lifecycle evidence.

Source and ownership: the More Tenets Slots publication preparation exposed the old 180/300/30-second defaults after the user's 1800-second policy. These external-operation defaults benefit every Workshop product and belong to the shared framework; product copies and frozen runtime007 remain untouched. Product case budgets are recorded separately in the [MTS budget change](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/master/docs/native-main-cold-budget-policy-2026-10-15.md).

Validation: 40 offline tests passed, including a fake callback completing at 600 seconds, expiry at 1800, both download CLIs/API/MCP schema forwarding, preserved three-field publish signature, exact publication readback and explicit longer HTTP timeout forwarding. The tests load no Steam DLL and perform no Steam, HTTP, GUI or game actions. These are implementation checks, not a publication/cache signoff.
