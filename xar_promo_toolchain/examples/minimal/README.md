# Minimal authoring example

This directory is an authoring-only ProjectConfig/schema example. After
installing the package as described in the root README, run its real executable
check from the `xar_promo_toolchain` root:

```powershell
xar-promo validate examples/minimal/promo-project.json
```

The `generic` adapter and `minimal-bilingual` preset names are illustrative;
this distribution does not install entry points for either ID.
`authoring-settings.json` is supporting project input and currently has no
direct CLI consumer. Running `plan` or `build` therefore requires a separately
installed integration plugin that registers the chosen adapter and preset,
plus a project-owned `PipelineComposer` supplied through `--composer`.

`release-export-policy.example.json` is likewise a contract example. This
directory contains no release-ready RunManifest, preserved deliverable, or
human approval, so the policy cannot be used to claim or export a ready run.
