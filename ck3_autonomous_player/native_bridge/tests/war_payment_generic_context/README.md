# Generic wallet context focused fixture

The C++ source is byte-for-byte equal to the actually compiled a04 fixture:
136 checks /16 cases /0 failures. It tests actual candidate passive observer and
serializer with synthetic guarded memory and Win64 callbacks. It does not launch
CK3 or call a game getter; its synthetic stack provider is not live unwind proof.
ACTUAL-COMPILE-LINK-RUN.json preserves original exact MSVC compile/link/run argv,
original source pins and the verified exact EXE Defender receipt reference.
Historical absolute paths in that JSON are provenance, never executable inputs.

After the default-OFF source patch is applied, from repository root use an explicitly
verified Python interpreter (normally tools/.venv/Scripts/python.exe):

    python -B ck3_autonomous_player/native_bridge/tests/war_payment_generic_context/run_focused.py --build-dir <new-external-build-dir>

The runner resolves this repository from its own location, freezes reached headers
and source bytes into a new append-only build, initializes the installed MSVC tools,
compiles3 TUs and syntax-checks runtime with the optional flag OFF and ON. It records
all actual argv/stdout/stderr and uses the project exact-EXE Defender hook before
executing the synthetic fixture. A missing/nonverified registration stops execution.
Choose a project build root already admitted by the installed broker; the runner
does not change its policy or request elevation. Outputs and Python caches stay in
the named new build. No complete bridge/DLL is built or deployed.

--repo <path> explicitly selects another checkout. --source-overlay <repo-shaped-path>
allows an explicitly named source candidate while keeping fallback headers in that
checkout. --plan-only prints scope and paths without creating outputs or invoking
tools. A plan-only pass is not a compiler/test pass.

The portable runner's path adaptation was syntax/plan checked only. Its exact
underlying fixture already passed in a04; no repeated native build was performed
merely to adapt repository-relative paths. The corresponding Python production
consumer regression and frozen wire live under tests/unit/ and its fixtures/.

maintenance_attribution remains unclosed; runtime OS unwind, raw producer names
and military-only paid component require separate actual observation.
