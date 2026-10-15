# Later actual R0176 runtime close append

This is a new observation at2026-10-15T19:01:28.222035+00:00 on `desktop-3fevhd2-1c74096080`. The original R13 ZIP and pre-close qualification remain unchanged. This append adds later custody facts; it does not rewrite the earlier packet's pending-close status.

The small ZIP preserves exact CLOSED, final bootstrap, terminal normal-save response, display restore and screen-release originals. Replay verifies the final main process exit0, SDK and keeper exit, screen CAS5483 -> completed5484 with no resources, and display1024x768 restoration. Historical warmup exit1 remains in the original bootstrap and is not confused with final main exit0.

The terminal checkpoint is a receipt-only identity:71305933B, SHA `31c57bc0032f0af4dcb90b4f00567cd68638e71856bbd570ee847aa644c26378`, date53146632. No save body was opened or hashed. Machine/process facts remain bound to the R0176 source machine; code and record format can be reused elsewhere.

After the R13 portable package, place this ZIP beside its index and run from the repository root with a new output filename:

```text
tools/.venv/Scripts/python.exe -B -O promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/locked_routes/verify_closed_append.py --index docs/ck3-native-ai/acceptance/2026-10-16-episode04-r13-r0176/closure-a01/ARCHIVE-INDEX.json --prior-r13 docs/ck3-native-ai/acceptance/2026-10-16-episode04-r13-r0176/QUALIFICATION.actual-a01.json --output r0176-close-new-attempt.json
```

This replay creates no new runtime evidence or human signoff. R13 endpoint arrival remains outside the45s clip; continuous clean, human approval and R09 full-card closure remain false. Original protection/review ends2026-10-16T07:45:01.597Z without renewal.
