# County primary writer invocation ownership (source candidate)

This opt-in adds invocation-time Army ownership to the existing actual4 loss
writer journal. It does not reclassify R216 or change its global ring gap.
Executable identity remains `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`.

The held callback `24E23E0..24E2A6F` saves incoming RCX in R13 at `24E240F`
(`4c8be9`). R13 is not assigned again before `24E25E9` (`e8a21b1500`) calls
writer `2634190`, returning to `24E25EE`. Windows x64 callees preserve R13.
R14 initially held old Province, but has become a divisor by `24E25DC`.
This implementation captures R13 only. It publishes no inferred Province.
Held span SHA: `6aa9b70a241d6dfbeac6841493f93b8a138f4dca0c58f7523165ef8844ac562f`.
Held instruction-document SHA: `22c412e446eb966298646f63c60215edd0cbf725c630854e9e7960e3ebb79573`.

`XAR_ENABLE_ACTUAL_COUNTY_PRIMARY_OWNER_12004` defaults OFF. ON changes the
destination of the existing 15-byte `2634190` detour to one MASM entry thunk;
it adds no game patch site. The thunk preserves the incoming return slot and
R13 before a C++ prologue can reuse registers. Its four arguments use ordinary
x64 RCX/RDX/R8/R9, 32-byte shadow space plus alignment, and declared unwind
allocation. The existing producer still calls the original writer once.
The original supply/residual TLS is neither pushed nor masked by this addition.

Bridge owns pre-date TLS; Runtime receives an explicitly bound synchronous
callback instead of linking to a second copy of that TLS. When natural-phase
sampling is OFF, the callback returns no scope. ON copies only the currently
active scope and advances its existing process event clock. At the writer,
guarded reads bind actual R13 CArmy full IDs and magic, public CUnit ID, original
ArRg array occurrence, writer RCX full ArRg ID/magic, current GameState, literal
prefix CDate64, TID, and actual pre-date roster occurrence. Army0 is valid.
Unknown, nested foreign, cross-thread or unmatched context stays absent or
incomplete. Query-selected Army/ArRg membership never supplies missing ownership.

The optional event child is `county_primary_owner_at_writer_v1` (schema 1).
Its `writer_invocation_token` identifies this writer invocation, not the whole
county callback. `phase_entry_event`, `phase_prefix_roster_event` and
`writer_event` use the actual shared clock/TID; the independent returned phase
must match the exact entry token and satisfy entry < prefix < writer < return.
The Python consumer also requires the existing complete physical writer fact,
actual source PC, captured IDs, unique token, roster occurrence and prefix date.
It returns target-scoped individual positive/zero facts separately.

Global window coverage remains independent. An overwritten ring still means
`whole_window_complete=false`; the old classifier remains unchanged. This
consumer always leaves `complete_army_loss_history=false` and
`county_total_debit=null`. It cannot infer all missing writers or close R04 from
equal endpoint sums. A new captured positive may establish a particular
county-primary physical debit for an invocation-owned Army; wider research,
dynamic footage and whole-window claims need their own evidence.

Future Root qualification after adopting the patch into a new admitted build:

```text
cmake -S ck3_autonomous_player/native_bridge -B <new-admitted-build> <all-existing-explicit-profile-flags> -DXAR_ENABLE_ACTUAL_COUNTY_PRIMARY_OWNER_12004=ON -DXAR_NATIVE71_ARMY_NATURAL_PHASE_12004=ON -DBUILD_TESTING=ON
cmake --build <new-admitted-build> --config Release --parallel 16 --target xar_ck3_bridge xar_ck3_bridge_injector xar_ck3_bridge_host xar_test_county_primary_owner_12004
ctest --test-dir <new-admitted-build> -C Release -R ^xar_test_county_primary_owner_12004$ --output-on-failure
tools/.venv/Scripts/python.exe -B -O -X utf8 ck3_autonomous_player/tests/unit/test_county_primary_owner_12004.py --repo . --output <new-small-result.json>
```

These are existing CMake build/ctest interfaces, with one new cold target.
The fixture uses owned synthetic memory, a synthetic image base and a local
assembly caller. It never loads or patches CK3. It tests the actual new thunk,
original exactly once, serialization, Army0, physical debit, wrong TID, foreign
roster and foreign caller. Native compilation/execution has not occurred in
this candidate lane. Source adoption changes compiled inputs and one explicit
option; it requires new DLL/output hashes, exact SYSTEM EXE readback and focused
cold success before live use. Old a36 bytes gain no capability from this patch.
The default OFF profile must remain OFF unless Root explicitly admits ON.

For the next entry experiment, Root can use a late paused baseline and retain
fresh writer/natural-phase cursors before one real entry day. Only that single
clock owner enables the existing natural-phase sampling, makes the ordinary
move/day, queries full evidence before OFF/clear, then saves and closes normally.
This source candidate authorizes none of those live actions. A day with more
than 512 global writers can still yield qualified retained individual facts,
but cannot become a complete global window by changing a boolean.
