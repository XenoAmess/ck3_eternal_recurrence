# Native normal-exit GUI source verification

R0019 exposed a mismatch between the two production source verifiers. Python
accepted unrelated GUI files after checking the stock exit dependency closure;
`normal_exit_map_source_v1.cpp` still rejected every `.gui` file. The same
inventory SHA reached both verifiers. Native rejected before inspecting loaded
exit targets, so its false source flags did not establish damaged stock files
or a wrong DLL. R0019 used the official GUI to exit; that result does not qualify
the native exit action.

The correction keeps the existing exact executable, process owner, full file
census, descriptor and byte/SHA checks. Native now checks unrelated GUI files
against the same stock namespace used by Python: the original six stock files,
12 additional dependency files, 99 global type/template names and three fixed
exit roots. Using a protected widget is supported; redefining its type/template,
overriding a protected source path, redefining an exit root or referencing an
exit callback remains rejected. GUI mods also require the exact dependency
inventory and actual dependency bytes. There is no new MCP action or caller
supplied admission flag.

`tools/gen_normal_exit_gui_source_contract_v1.py` derives the C++ data header and
JSON contract from an explicit exact-build game root using the existing Python
closure reader. Generated data contains identifiers and digests, not stock GUI
text or machine paths. The current data binds CK3 1.20.0.4 and executable SHA
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`.
Regenerate and review this source contract when its supported stock inputs
change; it is not an admission policy for an arbitrary future build.

The production Win32 wrapper still obtains its own command line and executable
path. It delegates filesystem verification to
`VerifyNormalExitMapInventoryForContextV1`, which is also exercised by an offline
native fixture. This C++ helper does not add a protocol path input.
`tools/qualify_normal_exit_gui_sources_v1.py` takes an explicit prepared profile,
fixture EXE, output directory and machine ID. It creates separate corpus roots,
never modifies the supplied profile or product, and compares the production
Python and C++ decisions. An explicit settings source can replay the inventoried
startup bytes after a completed game has rewritten its own settings.

On machine `bf-202609141645-5434332d4d`, 2026-10-15, five generator tests and all
16 production source-verifier parity cases passed. The corpus includes the
external MTS candidate's actual 48 files/two GUI files, a supported unrelated
declaration, protected type/template/root/path/callback collisions, changed GUI
bytes, added/missing files and missing/changed dependency records. Product files
and concrete campaign evidence remain in the independent product repository;
the reusable verifier, contract generator and fixture belong here.

Actual local evidence is under the external group
`C:/workspace/ck3-common-runtime/normal-exit-gui-source-20261015-001`, with the
16-case corpus at `C:/workspace/ck3-common-runtime/q/gui7-001/RESULT.actual.json`.
The build reused the predecessor's source/object chain and recompiled one
production translation unit. Archive, DLL link and fixture link succeeded.
The original build driver remains `failed` because the fixture's Defender WMI
registration returned `settings_failed`; registration was not retried or
reported successful. The separately authorized offline fixture execution passed.
Machine-local receipts include observation times and this machine ID. Earlier
receipts without machine IDs remain historical records with unverified machine
identity; this note does not relabel them.

These checks qualify source verification only. The next live run must separately
observe `stock_files_verified` and `loaded_source_binding_verified`, then verify
the actual exit controls, autosave=false readback and orderly process exit.
No game was started by this package, and no native GUI Quit, OS0 or product
business result is claimed. `open_kaishek` is not applicable to filesystem,
Win32 identity and GUI declaration namespace checks.
