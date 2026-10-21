# Early operator reviewer admission (source candidate)

Machine: desktop-3fevhd2-1c74096080. Exact master base:
9592cefdda846fc0242430d8fef1fef1f58c81a0. This is an unapplied source fix.

An allocated adapter run previously launched its host before the CaseClient
constructor rejected a missing reviewer. The candidate calls the unchanged
canonical resolver during contextual adapter preflight and again immediately
before invoking the reviewed launcher. The latter read rejects persisted
reviewer/delegation drift after an earlier successful preflight. Preparation
without a context and cases without an adapter keep their existing scope.
The client constructor, verify, normal cleanup, and delegation identity rules
remain unchanged; no constructor is moved before launch.

The final patch changes four repository paths: the entry's two small hunks;
six frozen-context fixture lines in the existing operator_quit finally test;
one new eight-method test; and two CI lines invoking that test. Only the three
mapped candidate sources and the workflow hunk are publication inputs. Exact
9592 client/native-day/background-types files are immutable test support and
must not overwrite newer upstream files during integration.

Actual checks: eight new methods PASS (real resolver, actual public preflight
and run, actual CaseClient constructor, harmless Python marker child only).
Missing/null/blank reviewer, bad/cross-run delegation, persisted identity drift,
and drift after successful preflight produce zero child/case-output. Valid
Root, non-Root and explicitly delegated operators retain their actual identity.
The existing modified finally method also PASSes, extracted from its exact
candidate AST and using the exact existing pure unavailable-receipt functions.
The exact old entry's missing-reviewer test FAILed as expected before any child.

Mypy was initially unavailable in D/tools/.venv; both original failures remain.
With the existing immutable mypy tool and identical candidate support MYPYPATH,
baseline and candidate each report eleven identical normalized diagnostics:
seven legacy typing errors and four intentionally unmaterialized sibling
imports in this bounded fixture. No diagnostic was introduced; this is not a
whole-repository or strict clean typecheck. AST syntax checks cover all three
modified Python sources. Git --numstat only parsed the final patch: it was not
applied to a repository or represented as an exact-tree apply check.

All test TMP/TEMP files were confined to this lane and removed by their owned
TemporaryDirectory context. No real game/host, native EXE, SDK, Steam probe,
desktop input, D/W edit, Git mutation or qualification was performed. The
current live R225 and every frozen runtime were left unchanged. A future
runtime must bind the newly published entry bytes before using the fix.
