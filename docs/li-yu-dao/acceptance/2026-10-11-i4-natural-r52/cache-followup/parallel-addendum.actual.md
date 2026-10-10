# ROOT facts addendum

Source: ROOT's actual read/projection notice; this agent did not reread originals.

R51/CASE2 and R52/CASE3 prepared objects both lack top-level `graphics_cache`. O10/O11 manifests both have `profile_features.shader_cache_reuse=true`; both runtime graphics_cache values are null. Selection.prepare calls prepare_graphics_cache only when inputs contain `shader_cache_seed`. ROOT's actual CASE3 input search found no such field. Thus permission was enabled but no seed was explicitly selected/injected. This does not prove cache deletion or an attempted key rejection.

ROOT reviewed _origin305-366: eight exact references bind frozen/prepared/runtime/native/host-start/host-exit/keeper/release, previous-session closure, completed lease/event sequence, exact prelaunch business bytes and current runtime/profile keys. previous_session_closure31-36 admits closed_session(finished/thread/cleanup) plus native_cleanup_closed without requiring public business PASS or a normal-close field. Administrative closed-RED is therefore not independently forbidden by that closure gate. Complete _origin/current-key validation was not executed: R51/R52 actual eligibility and promotion remain UNPROVEN.

Next: design a bounded origin/key validation and new seed storage admission for R52's limited-retention cache. The runtime key hashes source/native/EXE inputs, so its cost must be addressed before invoking it. No freeze/promotion/cache walk or budget renewal occurred here. Original report/INDEX remain the earlier knowledge state; this addendum supersedes only their selection/closure unknowns.
