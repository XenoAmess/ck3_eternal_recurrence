# External catalogs and failed prelaunch projections

Source: the More Tenets Slots investigation in the independent project's
`docs/bugfix-plan-2026-10-15.md` and native attempt
`bf-202609141645-5434332d4d--more-tenets-slots--R0015`.

An external product catalog may omit `workshop_cache_case`. Selection now reuses
the framework's canonical cache case, binding that catalog as an exact checked
input. An explicitly supplied case retains its previous behavior. This avoids
copying the shared cache contract into each mod. Cache loading remains separate
from source business acceptance.

R0016 subsequently reached normal-exit source inventory admission, which rejected
enabled mod GUI files before game launch. That exact validation error is also
recognized by the resource-only closure. A separate native inventory work package
handles safe GUI-mod support; this closure does not bypass inventory validation.

If readiness reports an original host exit before its first native report, closure
can use that failure immediately instead of requiring a full readiness timeout.
The early result must bind the same original host start/exit/stderr pins and exit
code, with native report, native0, normal exit and business credit all false. The
existing known-cause, public RED, keeper, process and absence requirements remain.

The original R0015 shared host exited 1 before launching CK3 because its effective
Python projection failed its SHA check. The prelaunch resource closure now admits
this exact recorded validation error alongside the existing prepared-profile
validation error. All original requirements remain: retained host exit, original
public RED and readiness timeout, stopped keeper and CAS release, no native report
or game/control evidence, and no running controller. Unknown causes are rejected.
This route grants neither native cleanup nor game normal-exit nor business credit.

Ownership: shared case selection and failed-host resource admission belong to the
framework; product code, selected baseline and concrete business results remain
in the independent mod. The runtime projection newline repair is a separate
framework package. No source or live acceptance is inferred from these checks.

Validation: the initial 29 offline tests in `test_ck3_mod_acceptance` and
`test_ck3_mod_acceptance_prelaunch_host_failure` passed. Follow-up closure tests
also cover the GUI-inventory error, bound early exit and receipt substitution.
The original tests include changed
fallback catalog rejection, existing explicit case compatibility, recognized
projection failure, unknown failure rejection and native-report exclusion.

The current shared release builder emits manifest format 2 with the same exact
file inventory fields. Cache admission now accepts formats 1 and 2 while retaining
tagged identity, canonical item, safe unique paths, file sizes and SHA checks.
Boolean, string and unknown versions remain rejected. All 11 cache seam tests
passed, including format-2 preparation and rejection of changed cached bytes.
