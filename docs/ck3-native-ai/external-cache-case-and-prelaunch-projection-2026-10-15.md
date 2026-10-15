# External catalogs and failed prelaunch projections

Source: the More Tenets Slots investigation in the independent project's
`docs/bugfix-plan-2026-10-15.md` and native attempt
`bf-202609141645-5434332d4d--more-tenets-slots--R0015`.

An external product catalog may omit `workshop_cache_case`. Selection now reuses
the framework's canonical cache case, binding that catalog as an exact checked
input. An explicitly supplied case retains its previous behavior. This avoids
copying the shared cache contract into each mod. Cache loading remains separate
from source business acceptance.

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

Validation: 29 offline tests in `test_ck3_mod_acceptance` and
`test_ck3_mod_acceptance_prelaunch_host_failure` passed. They include changed
fallback catalog rejection, existing explicit case compatibility, recognized
projection failure, unknown failure rejection and native-report exclusion.
