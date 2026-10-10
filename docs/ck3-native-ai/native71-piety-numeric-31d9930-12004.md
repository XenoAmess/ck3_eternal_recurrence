# Actual 31D9930 raw numeric input

The complete 288-byte CK3 1.20.0.4 body selects `definition + 0x760`, passes it to `1233A40` at `31D99C5`, saves the returned EAX in EBX and returns the same raw 32 bits at `31D9A39`. Its original inputs are the full ordered definition pointer in RCX and current Rite pointer in RDX. Create calls it at `2C64309`; edit calls it at `2C64867`. The callers own sign extension, multiplication by 100000 and ordered low-64-bit addition.

The readonly leaf delegates to the unique `1233A40` projection, which delegates to the unique `A0F0B0` projection. Actual `A0F0DE` checks DWORD `expression + 0xB8`; mode zero immediately reads DWORD `expression + 0x98` at `A0F0E7` and skips context, name, frame initializer and profiling demands. Thus this supported numeric path reads definition DWORD `+0x818` followed by signed DWORD `+0x7F8`. It preserves negative and zero values without inventing units, clamping or cached price fallback.

The observation carries the exact definition, current Rite and full unchanged revision, selected expression, source pin and complete evaluator diagnostic. It describes a software projection; `actual_original_consumed_values` stays false. Mode zero does not require readable current Rite or nonzero module base or revision. Exact-build binding and guarded reads remain required. Reached dynamic branches and failed raw reads return absent EAX with a concrete reason. No native evaluator, constructor, getter, query or game call is made.

The numeric core owns an additional narrow recopy of mode and value. Both copied bookends must be available and equal before it emits EAX. These extra copies guard the conditional copied-input result; they are not additional native instructions and do not prove freshness or native consumption. This leaf preserves the complete first/after witnesses without implementing another reader.

The original native body also builds a name tuple and Rite context before invoking the evaluator. Their production projections are separate source-owned dependencies. They are not demanded by the closed mode-zero numerical branch. Dynamic R9 consumers remain unresolved; `3F79B00` and `3F79DD0` are not expanded until an actual numerical demand is proved.

The existing edit scalar callback uses `ReadPietyPriceNumeric31D9930Adapter12004`. It forwards the same readonly access, definition, current Rite and full revision to the production reader and changes its output only on an available raw EAX. The new no-main cases exercise the connected 22 → 11 → 40 production path; central 49/10 executes them once with the new price packet. No local compile or test has run.

Exact source and dependency pins are in the external continuation-22e `SOURCE-PROOF.json`, `SOURCE-NUMERIC-DEMAND.json` and `CANDIDATE-PINS.json`. Owned files remain D-only. The old Sway, Title, predicate and validator validations are not repeated.
