# Native verification recipe preparation

`prepare_verification_recipe.py` prepares the existing Native 748/750 metadata
profile for one production TU, one JUnit Test TU, and explicit new method names.
It never starts a process or JVM, runs Tests, acquires a lease, creates a runner,
or grants SDK qualification. Native remains the sole execution owner.

The public request and external Native SDK declaration are specified in
`API-CONTRACT.json`. Pins have exactly `path`, `bytes`, and `sha256`. Inputs must
use existing absolute ASCII paths without quotes, semicolons, traversal or
symlink redirection. The new output root must be an absent D directory whose
parent already exists. The supported JVM paths and VM limits are those of the
verified Windows profile; other profiles fail by name.

1. Obtain the source owners' frozen production/Test SourceReady documents and
   Native's declaration for those exact source bytes. The declaration identifies
   a previously verified SDK config, argfile, ACTUAL and VERIFIED, preserves its
   ordered 316 entries including duplicates, and names the reviewed API families.
   An old green SDK or binary hash alone does not establish source/ABI suitability.
2. Call `prepare_production(request_path)`. It returns the pin of
   `output_root/production/PREPARED-READY.json`. The generated CONFIG and PROD.args
   use the existing runner schema. Native validates them with its original guard
   and performs the necessary first production compilation under its own lease.
3. Pass that Ready pin and the actual production ACTUAL/VERIFIED pins to
   `prepare_tests(...)`. It checks their generated CONFIG/command identity, exact
   current class manifest and selected top-level production class. Only then does
   it create the Test/JUnit CONFIG and args. Native retains ownership of their
   compilation, explicit method execution and XML verification.

When the source owner's SourceReady directory differs from the new recipe output,
the Native execution adapter must pass the pinned CONFIG's `fixture.task_root` to
the existing temp-directory preflight. The old 750 runner used the SourceReady's
parent because both roots coincided there. Keep the original within-root check;
do not create temp directories in another source owner's tree.

Test compilation classpath prefixes are actual production output then standalone
JUnit jar. JUnit execution prefixes are new Test output then actual production
output. Both retain the original SDK tail byte order. Compilation keeps explicit
empty sourcepath, no implicit compilation, strict lint/Werror, and direct javac VM
caps. JUnit retains fail-if-no-tests and isolated reports/tmp. Class selectors,
scanning, additional TUs and missing qualification are rejected rather than
expanded into another build mode.

Named family declarations record the Native-reviewed finite API origins. They do
not establish every nested companion or transitive linkage dependency. The first
real compilation and selected method execution retain that validation boundary;
missing concrete families are handled by Native without rebuilding old green
sources or treating the whole SDK as approved.

The CLI supports `production --request ABSOLUTE_REQUEST_JSON`. Its `tests` stage
accepts three JSON pin objects through `--production-ready`, `--actual` and
`--verified`; callers should use structured argv or the public Python functions,
without shell-built JSON commands. All generation uses create-only output files.
A partial preparation has no Prepared-READY and is not executable readiness.

`tests/test_prepare_verification_recipe_data.py` contains four DATA tests. The
original three use semantics frozen before the public API; the fourth checks
standalone JUnit jar drift before and after production preparation. Their fake
classes, jar and Native receipts are local DATA, never real execution evidence.
The suite requires an isolated D checkout and exercises this Windows profile.
Native owns software execution. Keep the Test in the module child directory.

Original 748/750 evidence is a metadata comparison basis; this tool does not rerun
it. Preparation wall time and Native compilation/Test time are recorded separately.
No preparation saving or execution success is inferred until a new actual unit
uses the tool and Native returns its receipts.
