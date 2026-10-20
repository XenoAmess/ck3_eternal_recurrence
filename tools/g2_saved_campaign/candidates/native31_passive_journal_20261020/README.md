# Native31 passive time-command source package

This package preserves the actual Native31 source inputs and cold journal reader.
Creation machine: `xenoamess-full-tower-eb9d2c1186`; observation time and exact
input/output pins are in `MANIFEST.json`. Evidence records retain their original
machine IDs, timestamps, paths and hashes. Their old D paths are provenance,
not a requirement to create another copy of those directories.

The root MCP wrapper and A14 factory are separate integration sources. This
package grants no runtime admission and does not deploy a DLL. The original
artifact/fixture qualifications were offline; any later live scene requires its
own actual loader, Game and source binding.

## Verify source bytes in RAM

From the repository root:

```text
py -B tools/g2_saved_campaign/candidates/native31_passive_journal_20261020/recompose.py --repo .
py -B -m unittest discover -s tools/g2_saved_campaign/candidates/native31_passive_journal_20261020 -p test_recompose.py
```

The verifier reads exactly three immutable Git blobs from commit
`704bdd3362bdc282ed5f5f8cf31fd3f50b90d747`, verifies every preserved input, and
recomposes thirteen source outputs in memory. It writes no generated sources,
build objects or binaries and never calls the Game. The final core and two
fixtures replace earlier draft inputs in the historical candidate package.
The 807-byte Native30 macro restoration is retained unchanged.

A shallow checkout can lack these old objects. The verifier then fails closed;
it never fetches, substitutes current HEAD, installs a package or changes CI
fetch depth. The optional history-dependent test reports a skip when those
objects are absent; the CLI still rejects verification.

An operator can obtain a narrow blob pack from an authorized clone that already
contains the history. On that source clone, pass the three `blob` IDs listed in
`MANIFEST.json`, one per line, to `git pack-objects --stdout` and preserve the
resulting pack. The receiving operator can explicitly import it with
`git unpack-objects` under their own storage authorization. Re-run this verifier;
all three byte lengths and SHA-256 values must match. No such export/import is
performed by this package, and no full-history CI fetch is required.

## Qualification boundaries

- `historical_inputs/prepare_producer.py` and `candidate-package.json` preserve
  their original bytes. The package's draft core/test are historical inputs;
  `native/src/native_time_command_observer_12004.cpp` (14,322 bytes) and the
  two `native/tests/` files are the actual later qualified inputs.
- `historical_inputs/production_producer.py` is preserved unchanged. Its original
  postcheck failed because an optimized/inlined `CommitInsertion` symbol was
  absent. Its four compilations, linker and export tool had returned zero.
  The FAILED record remains in `evidence/`.
- `POSTCHECK01.json` and `PRODUCTION-RESULT01.json` preserve the later independent
  COFF/relocation/linked-byte proof. They do not turn the old producer into a
  successful rerunnable producer. The actual 32 C++ fixture results are retained;
  verification of this package does not repeat them.
- The historical production recipe reused 336 Native30 objects and an existing
  runtime archive. This package proves source recomposition, not a clean,
  portable or byte-identical native build. It contains no DLL or EXE.
- The installer fixture preserves its original absolute default include.
  A future qualified build must explicitly supply the existing
  `NATIVE31_INSTALLER_SOURCE` macro for the actual installer source location.
- The four `cold/` Python files are bound to `evidence/QUALIFICATION02.json`.
  Observer connection counters remain independent of protocol generations.
  Journal observations do not prove the current failed request completed, absence
  is not nonexecution, and there is no drain fence or automatic recovery grant.

The original evidence's offline status refers to its original observation time.
Current live deployment state is outside this package's claims.

