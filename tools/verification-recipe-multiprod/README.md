# Coherent two-source verification metadata

This version prepares exactly two ordered production Java files for one strict
`javac` invocation and one output directory, then one JUnit Test file with
explicit method selectors. It does not launch a process, approve SDK support,
obtain a resource lease, or change runtime sources. The completed single-source
version remains separate.

`prepare_production(request_path)` accepts the pinned v2 request described in
`API-CONTRACT.v2.json`. Each `production_sources` entry contains `source`,
`class_name`, and `source_ready`. A common SourceReady can bind both files.
The external Native declaration must bind the same ordered pair and the Test
source. The original verified 316-entry SDK tail retains its order and duplicates.
Both selected classes and their explicitly required nested classes belong to the
new coherent output, so an old SDK pin cannot qualify those classes.

Production preparation returns a pin for `production/PREPARED-READY.json`.
Its CONFIG contains one command, two ordered sources, and a 14-token compiler
argfile derived from the admitted original 13-token template. At this stage
co-produced class names have planned relative paths only; no future class hash
is created.

After Native executes that exact command successfully, call
`prepare_tests(production_ready_pin, actual_pin, verified_pin)`. It requires a
successful two-TU ACTUAL linked to the prepared CONFIG/command and VERIFIED,
plus the exact existing output manifest. Both top-level classes and every
explicitly required co-produced nested family must be present before the Test
directory is created. All such Test dependencies then bind to that actual
shared output at classpath index 0. The tool prepares one new Test TU and only
the requested method selectors.

The optional JNA fixture profile is explicitly declared by Native using pinned
`basis` CONFIG and `helper` source metadata. It preserves the existing
`software_jvm_fixture308` contract: owned existing absolute temp directories,
bounded arguments, and the admitted 128 MiB/one-processor JUnit command. New
`java.io.tmpdir` and `jna.tmpdir` directories stay within the new task root.
Absence of this option retains the original no-JNA profile. This metadata check
does not load JNA or grant Java, OS-child, or Game behavior credit.

All outputs are isolated create-only D directories. Existing outputs are
refused; failed or partial attempts are preserved. Class selectors, scans,
different production counts, unsupported template shapes, missing declarations,
and unresolved output families are refused by name. Native retains sole
execution and resource ownership. `CONFIG.fixture.task_root` supplies the new
output root to the Native adapter when source and output roots differ.

The four new DATA methods cover the ordered coherent command/shared actual
prefix, unsupported cardinality/duplicates/old-SDK substitution, missing
top-level or nested manifest entries and single-TU receipts, and the pinned JNA
profile. Synthetic class/jar/Native receipts are DATA only. No old successful
Test or business phase is rerun for this version. Actual results and timing are
recorded separately from source readiness.
