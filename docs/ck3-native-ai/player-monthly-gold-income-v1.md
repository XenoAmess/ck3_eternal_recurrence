# CK3 player monthly gold income v1

## Status and scope

- **[static-ready, live pending]** `campaign-root-context-v1` now publishes
  `player_monthly_gold_income` as signed Q100000 `{raw, scale}` data for the
  exact played Character.
- The binding is frozen to CK3 `1.19.0.6`, `ck3.exe` SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`,
  evaluator RVA `0x28DBE90`.
- This is current economic state, so an original AI decision tree is N/A.
  Planner policy remains outside this observation package.

## Why this evaluator is authoritative

The existing war-exit observer already calls the same native signature:

```cpp
int64_t *monthly_gold_income(
    int64_t *output,
    CCharacter *character,
    void *optional_breakdown,
    void *evaluation_context);
```

Both optional arguments are null for the complete current result. The call is
accepted only when it returns the caller's output pointer. The earlier paused
war evidence observed `570772` from this evaluator while the cached
`CCharacter` extension leaf at `+0x2B0` still held `551588`. That leaf can lag
and remains diagnostic only; it is never a readiness or equality gate.

## Publication contract

After resolving the played full-generation CharacterID, the reader:

1. invokes `module+0x28DBE90` on the resolved Character;
2. requires the returned pointer to equal its local `int64_t` output;
3. resolves the same full CharacterID through Character storage again and
   requires the identical Character pointer;
4. repeats the complete campaign-root observation and requires both signed
   Q100000 income values and all other fields to match;
5. requires the final paused frame to equal the starting frame.

An available frame therefore carries:

```json
"player_monthly_gold_income": {"raw": 570772, "scale": 100000}
```

The value may be negative. It is never nullable in an available frame. A bad
return pointer, identity drift or unavailable evaluator fails the entire frame
as `player_monthly_gold_income_unavailable`; unavailable frames publish null
and set every readiness flag false.

## Product effect

`ck3_query_turn_bundle_v1` now publishes this value as
`ruler_state.value.income`. Its `ruler_resources_ready` gate becomes true only
when the same aggregate also has valid current gold from the cached normalized
snapshot. Health, domain, council, faction and partition gaps still keep the
full bundle at `status=partial` and `readiness.ready=false`.

The Python native-driver mirror now also carries the already published
`primary_title_succession_character_ids`; this closes an interface omission
that could otherwise drop that field between the native frame and service.

## Focused verification

- Release DLL compile/link: GREEN, `2,636,800` bytes, SHA-256
  `98FC243165EB0E136AE6160A6F665856C3AFF01E971E4F01B1D5BCD1FF0566C2`.
- Direct campaign-root reader fixture: GREEN, including two evaluator calls,
  exact Q100000 publication and typed evaluator failure.
- Source-contract executable: GREEN.
- Focused campaign-root, live-harness and turn-bundle Python suites: normal and
  optimized modes GREEN.

No CK3 process or desktop input was used. The field remains `live=false` until
one already required bounded paused G2 session samples campaign root and turn
bundle together. It does not justify a dedicated long run.
