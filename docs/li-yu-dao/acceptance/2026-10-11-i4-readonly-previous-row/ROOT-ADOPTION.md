# ROOT adoption

ROOT applied the reviewed production patch and affected six-test delta after R54 CAS release4647 and reservation008 closure. The original once-executed 9 new + 6 affected tests passed. The repository entry reads actual repository source; external candidate-author mode is optional test tooling.

The proposed source-only CI patch was not applied verbatim: inserting the new command before the old batch command’s error check would mask a failed old batch command. ROOT preserved that check and added the new command with its own immediate error check. No production or test assertion changed for this CI correction; the integrated syntax/CI entry check passed. See [integration receipt](../2026-10-11-i4-natural-r54/ROOT-INTEGRATION.actual.json). The check’s first invocation assumed the existing grant command omitted `-v`; its assertion was corrected to recognize the actual command, with no workflow change for that checker error.

Actual live speedup and expiry remain UNKNOWN. The source-only original CI patch and earlier author failures remain historical external objects; no old successful tests were replayed during adoption. The forthcoming exact-head CI independently executes the permanent entries.
