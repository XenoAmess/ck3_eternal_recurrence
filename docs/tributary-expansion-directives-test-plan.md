# Tributary Expansion Directives 1.0.0 test plan

## Product contract

The player suzerain right-clicks a direct AI tributary, chooses an eligible
foreign neighboring county, and spends 150 Prestige to issue an expansion
directive. The tributary may refuse. If it accepts, a second legality check
must bind that tributary as primary attacker, the selected foreign ruler as
defender, and the selected county as the sole target of
`ted_directed_county_expansion_cb`.

The optional subsidy is `ceil(clamp(12 × recipient monthly income, 50, 500) / 5) × 5`
Gold. It moves from suzerain to tributary only after a valid acceptance. A
valid refusal spends Prestige, transfers no Gold, starts no war, and retains
the five-year recipient cooldown. A same-frame invalidation refunds Prestige,
transfers no Gold, and removes the cooldown.

## L0 static and build gate

- All four CK3 script files and nine localization files parse as UTF-8 BOM;
  `descriptor.mod` is UTF-8 without BOM or `remote_file_id`.
- Every new top-level runtime key uses the `ted_` namespace.
- Static contract checks the 150 Prestige cost, five-year recipient cooldown,
  subsidy formula/reference vectors, exact second `can_declare_war`, single
  `start_war`, refund paths, and county transfer to `scope:attacker`.
- Every language has the same key and protected-token inventory; no English
  placeholder file remains.
- Thumbnail is a deterministic 640×640 RGB PNG below 1 MB.
- The exact 16-file allowlist builds twice to byte-identical manifest and ZIP;
  source-only README/research files never enter staging.

Commands:

```text
py tools/test_build_tributary_expansion_directives_release.py
py tools/validate_tributary_expansion_directives_static.py
py tools/compose_tributary_expansion_directives_key_art.py --check
py tools/build_tributary_expansion_directives_release.py --check
```

Open Kaishek must be run before CK3. Its generic root parser can prove balanced
syntax, but its current fixture catalogue does not model character
interactions or CB directories; that validator result is `not-applicable`, not
a product failure or a live-game pass.

## L1/L2 live gate

Use a unique isolated `-userdir`, cloud saves disabled, exactly two mounted
mods in order: the 16-file production projection and an external acceptance
fixture. Preserve the exact CK3 version, executable SHA-256, runtime tree hash,
mount order, logs, screenshot, and controlled process shutdown.

The initial-release live cell must establish and read back a deterministic
suzerain and direct AI tributary, then select a neighboring county for which
the engine's exact production `can_declare_war` check succeeds. It executes the
same production response effects and records exact-once markers for:

- load/bootstrap and the real direct tributary relationship;
- valid refusal: Prestige -150, Gold unchanged, no war;
- valid subsidized acceptance: Prestige -150, exact subsidy transfer, one war;
- war binding: tributary attacker, chosen defender, and the dedicated CB.

The dedicated CB's victory, white-peace, defeat, truce, inheritance, and title
transfer definitions remain mandatory L0 contracts. They are not described as
executed live unless a later artifact contains their explicit outcome markers.
The first-release cell likewise does not claim production interaction-selector
UI coverage, an invalidated-response cooldown-refund scenario, save/reload, or
post-war tribute-delta coverage. Those gaps must be listed in its machine report
and the release acceptance record instead of being silently promoted to GREEN.

Any `ted`-attributed parser/runtime diagnostic, missing marker, second war,
unexpected resource delta, source/runtime mutation, protected-profile change,
or untracked CK3 process is RED.

## L3 player-path and release gate

Fixture calls alone must not be described as production interaction UI-path
coverage. When a production selector smoke is executed, it must separately
prove that the interaction is visible on a direct AI tributary, opens the
secondary-ruler/county selector, shows the dynamic subsidy, and can be sent.

Before an initial Workshop release, at least one clean real gameplay screenshot
must be projected from a GREEN candidate artifact, entered in
`workshop/tributary_expansion_directives_screenshots.md`, uploaded to the Steam
media strip, and publicly read back. Thumbnail art and fixture/test UI cannot
substitute for this screenshot.

After publishing, rebuild an ID-bearing manifest, download to a fresh empty
Workshop cache, strictly verify every runtime byte (allowing only the launcher's
final canonical `remote_file_id` line), and rerun the required isolated live
cell from that read-only cache. Publication is incomplete until the public item
page and full Change Notes are anonymously read back and the final changelog is
committed and pushed.
