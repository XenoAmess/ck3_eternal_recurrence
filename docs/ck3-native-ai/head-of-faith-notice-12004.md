# Exact .4 head-of-faith announcement knowledge

## Plan and ownership

Register stock `head_of_faith.0100` for CK3 1.20.0.4 / Steam25734779 / EXE
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
Reuse the external source-reviewed leaf, register its public query/source-index
row, and exercise one compound founder/HoF projection case. Add only the actual
eight-scope `faith_creation.1021` variant containing `converted_ruler_capital`;
reuse the existing option/effect analysis. Preserve the seven-scope contract,
older builds, inherited source rows and blocked generic automatic policy.

No native build, runtime007 deployment, new game action or general religion AI
is part of this package. `open_kaishek` prevalidation is not applicable: the
change registers source metadata and tests existing Python projection guards,
without adding a CK3 effect evaluator, parser or finite-runtime scenario.

## Original evidence

Machine `bf-202609141645-5434332d4d`, actual event context at
2026-10-15T15:42:03.353126Z. The product repository
`ck3_mod_more_tenant_slots` owns
`artifacts/bugfix-20261015/r22-hof0100-candidate-001/proof.json`, SHA256
`717793ab32cbc5624d17b46a9b0ade0d850272274c06875e5f1158c7a88b1618`.
It pins seven original stock files matching cached Steam depot1158311 manifest
5078208590259867811 sizes/SHA1s, actual context/action and the first external test.
This is cached-file corroboration, not online/full-installation verification.
Product raw UI, identities and save bytes remain there; no private fixture is
copied into framework code or tests.

`head_of_faith_events.txt:896–956` has two options. Native0 adds a decaying
`repentant_opinion` component of 25 from HoF toward root, not root toward HoF.
The modifier has monthly_change0.1 and no fixed duration authored. Native1 adds
`wishes_to_schism_caliphate_flag`; later antipope eligibility can use that flag as
one alternative condition, without performing an immediate schism. Neither
option directly changes Rite/Faith/tenets/doctrines/resources/stress, and no
after or explicit event reschedule is authored. Native0 does not clear a
pre-existing schism flag. The actual selection advances instance1 to null;
independent total-opinion gain was not observed.

`on_rite_created` raises `.0100` immediately if a religious head exists. The
next-day `.1021` announcement is separate. R22's `.1021` carries an extra
landed-title scope `converted_ruler_capital`, matching its save in
`faith_conversion_events.txt:15–17` and the on-action ordering of `.0001` before
`.1020`. This is a distinct, explicitly named variant, not permission for any
extra scopes or inferred opaque Rite/Faith/Tenet IDs. Existing option semantics
and the body/widget distinction remain in [the rite announcement note](rite-creation-notice-12004.md).

Both occurrences are product-live primitives. The product's
`docs/native-main-r22-2026-10-16.md` and `docs/evidence/native-main-r22.json` own
R22 MAIN's scoped acceptance and
the original host RED caused by an unpaused read-only query are owned by the
product's separate report; this knowledge package does not relabel the full
host GREEN. Earlier observations and frozen runtime007 retain their original
status.

## Validation

Three focused compound cases passed on the recorded machine at
2026-10-15T17:25:04–17:25:06Z (2026-10-16 Asia/Shanghai): new public HoF knowledge
and negative scope/options (0.172 s unittest), extended rite scope variant
(0.214 s), and affected source migration (0.179 s). Actual commands/output are
committed under `artifacts/enrichment-20261016/hof0100-001/`:

- `test_head_of_faith0100_12004.py.actual.json`, LF SHA256
  `4996ff8464a90883713c59813126c78313552804ed0c6247739b3be07415f3f3`;
- `test_faith_creation1021_12004.py.actual.json`, LF SHA256
  `3b9a8fa478f44366aed13361704c69852b7fb0747c6257c2c55d618a30ad7689`;
- `test_vanilla_event_migration_12004.py.actual.json`, LF SHA256
  `8ab8636a26a192478d15a524d6d84e82c9ec2924db2fc990a1eb3cd932aba44c`.

The .4 source index is now 195 rows: original193 plus the previously registered
rite notice and this HoF notice. All inherited rows, .3 dataset bytes and older
builds remain unchanged. Public queries return detached JSON; wrong scope types,
self-HoF, missing scope, disabled option and wrong native mapping are rejected
by the tested projection guards. Generic automatic selection remains blocked;
no opinion material credit, new runtime deployment or observer credit is granted.
