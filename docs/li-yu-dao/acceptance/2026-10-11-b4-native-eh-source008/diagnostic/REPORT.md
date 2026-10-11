# Fixture008: actual empty-state success; collision remains unresolved

The nine original waits completed without timeout: six `FIXTURE_CASE_PASS`, one `NEGATIVE_CONTROL_OBSERVED`, and two process failures. This is standalone fixture evidence; CK3 and formal B4 qualification remain NULL. The executable pin comes from the original mode INDEX, not another PE read.

`inplace-empty` and `no-language-empty` both returned 0 with actual marker_state=-1, projected_call_state=-1, original_flags=2, original_codes=3, cleanup_count=1, removed=true, pinned_failure=false. The forwarded case had one handler call/return; the handler-free case had none. This closes the specific empty admission/layout failure. It proves these concrete continuations, not general permission to omit language handlers.

`inplace-collided` ended 3762467842 (0xE042B402, kCollision). Its last durable record is seq5/cleanup_entry: actual and forwarded dispatcher are identical and ScopeIndex is 1/1. No later arrival, outer filter, handler return or removal record exists. This proves progress through cleanup with the actual ScopeIndex updated; it does not identify the subsequent Windows dispatch path or prove successful collided unwind.

`copy-control-collided` ended 3221226505 (0xC0000409). Cleanup seq5 records distinct dispatchers and ScopeIndex 0/1. Seq6 then records a new handler arrival with kCollision, flags=0; seq7 records handler_validation_failure. Both checks in source lines195-198 and201-209 emit kind9, so the particular rejected predicate is UNKNOWN. Flags0 is not EXCEPTION_COLLIDED_UNWIND. The process failure does not earn the intended copy-control qualification, and unload remains UNKNOWN.

`TRACE.future.diff` is an unbuilt diagnostic-only successor. It persists identity fields already captured in Event, records the actual metadata DWORD after the existing read, distinguishes the two unchanged rejection branches, and adds a record immediately before the existing collision RaiseException. It changes neither forwarding/restoration nor predicates, disposition, exception routing or PASS criteria. Existing Kind values1-10 remain stable; new kinds11-14 are data rejection, identity rejection, data read and collision raise. It does not claim to fix either crash.

No new PE read is needed for these findings. No mode, compiler or test was executed by this diagnostic. Original006/007/008 failures remain unchanged. A semantic collision patch is not justified by the current ambiguous rejection trace; the proposed discriminator is the smallest next observation.
