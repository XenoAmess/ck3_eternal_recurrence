# R06 scope fixture reviewer repair

Machine: desktop-3fevhd2-1c74096080. Base: 58d6058d9aa202f91f1046753bb5d0df23e55c77.

The complete exact-source local baseline runs five tests and fails four assertions because the R06 reviewed-context fixture has no reviewer. The real new preflight reviewer resolver rejects it before the intended valid run or missing/null/empty Steam-receipt checks. The initial local sparse-worktree import failure is separate, ran no tests, and is preserved rather than attributed to the official CI failure. The official job log traceback was unavailable; this is an actual local reproduction of a definite failure in that exact test source.

Only tools/test_ck3_mod_acceptance_r06_scope.py changes. The fixture supplies an explicit synthetic non-Root reviewer, directly exercises the unchanged canonical resolver, and tests missing/null/empty and persisted-identity drift through real public run dispatch with zero launcher, CaseClient or business dispatch. Production entry/client/allocator, reviewer identity, 1050s, once/no-retry and SDK/game guards are unchanged. Signature annotations make the modified fixture helpers checkable without Any/cast/ignore shortcuts.

The candidate passes all six tests once. Actual strict checking of the fixture and two external helpers reduces the baseline 35 diagnostics to one pre-existing dynamic crossed-scope lambda call. Its AST and source-line mapping are recorded; no new diagnostic is introduced. This is not whole-fixture or whole-repository strict PASS. The two external helpers have no diagnostics in that actual combined check.

The exact minimal 26-file source/config shadow is 644705B and is local test support only. It is not included in publication; its exact source pins and canonical Git commit reconstruct the inputs. The candidate source is executed with its repository-resource __file__ mapped to that immutable shadow; compile/traceback filename and source pins remain the external candidate. All native/SDK/Game/Steam/host launch and screen/process boundaries are mocked, profile inputs and CK3 executable are tiny test files, and ID allocation stays in the isolated task temporary root. No Game/SDK/native execution or D/W/Git mutation occurred.

Original waits/stdout/stderr are preserved, including the sparse import failure and both strict failures. All process births are canonical decimal strings. No official CI green or live qualification is claimed; a subsequent official CI run must verify publication.
