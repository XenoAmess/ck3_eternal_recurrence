# G2 private Raiktor truce diagnostic seam (2026-09-02)

This change retains the native `RaiktorSurrenderTruceFailureV1` value between
the private `ReadRaiktorSurrenderTruceDuration` reader and its
`ReadWarTerminationTerms` caller only when
`XAR_CK3_WAR_EXIT_TERMS_OFFLINE_RE_TEST` is defined.  A thread-local enum and
the `LastRaiktorSurrenderTruceFailureForOfflineReFixture` accessor are compiled
into the offline C++ test target only.

The seam is diagnostic-only: it adds no `WarRaiktorSurrenderTermsSnapshot`
field, public v1 wire/schema key, readiness change, offset, or production ABI
symbol.  It does not start CK3 and does not claim live truce or action
readiness.  The existing pointer fixture intentionally fails exact-build
environment validation, so its focused assertion expects
`RaiktorSurrenderTruceFailureV1::unsupported_build`.

Validation: the freshly built `xar_ck3_game_access_test` fixture passed in the
offline CTest run (no CK3/live run).  The same build exposed 15 pre-existing
repository-wide source-contract/runtime-test failures on this older checkout;
they are outside this seam and are retained as a baseline RED rather than
being relabeled as a seam failure.
