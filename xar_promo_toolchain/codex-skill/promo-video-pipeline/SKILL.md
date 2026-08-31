---
name: promo-video-pipeline
description: Orchestrate reproducible promotional and demo video production through the local xar-promo CLI, from project/run setup and read-only planning through build, automated audit, pending human review, explicit signoff, and offline export. Use when a repository needs retained source/process artifacts and evidence-bound release handoff; do not use for unrelated one-off media edits.
---

# Promo Video Pipeline

Treat the checked-in project config as the source of project-specific capture adapters, presets, languages, voice, duration, and presentation rules. Keep those choices out of this skill.

Read [references/workflow.md](references/workflow.md) before starting or resuming a run. Read [references/manifest.md](references/manifest.md) when creating or inspecting config, run state, artifacts, audits, signoffs, or export readiness.

Use the installed `xar-promo` command as the orchestration boundary. Confirm `--version`, top-level `--help`, and relevant subcommand help before acting. The frozen 0.1 command set is `init`, `start-run`, `validate`, `preserve`, `plan`, `build`, `audit`, `review`, `signoff`, and `export`. Do not invent another subcommand or reimplement the media engine in Skill scripts.

Drive the lifecycle in this order while reporting the highest state actually reached:

1. Validate project intent and create a fresh, snapshot-bound run.
2. Use `plan` for an always-read-only composition check. It must not create its proposed work directory or invoke production providers.
3. Use `build` with the project-supplied `MODULE:ATTRIBUTE` composer and a fresh work directory. Let config-selected adapter/preset registrations control capture, narration, subtitle, and render behavior.
4. Use `audit` only against an exact preserved subject artifact and a real evidence bundle. Its result is automated evidence, never approval.
5. Produce a v1 exact-byte-bound media probe with the public `probe_and_write_bound_media` API, then use `review --plan-only` for a zero-process/zero-write frame plan or `review` to create a pending, byte-bound human-review package. Bare, stale, or mismatched probe JSON is RED. Preserve the probe, package, frames, and command audit material in the run.
6. Use `signoff` only after a named human explicitly provides an `approved` or `rejected` decision for the exact preserved artifact.
7. Validate the release profile, then use `export` with an explicit allowlist policy to create a new offline bundle. Export never publishes or uploads.

Before a phase and after each mutation, fully validate both `promo-project.json` and the selected `runs/<run-id>/run-manifest.json`. Use file/hash validation by default; use `--structure-only` only when the requested result is explicitly structural. Exit code `0` is success; syntax, contract, integrity, and operational failures use `2`.

Keep every attempt in a distinct run/work directory. Preserve raw capture, scripts, narration, subtitle sources, intermediate renders, tool versions, stdout/stderr, partial and failed outputs, manifests and history, audit evidence/reports, review packages, frame samples, and exports. Never delete, overwrite, or repoint retained process material unless the user explicitly names what to remove; changed bytes require a new run or artifact ID.

Only when `config.adapter` is `ck3`, or the user explicitly asks to reuse a CK3 acceptance capture bundle, read [references/ck3-capture-adapter.md](references/ck3-capture-adapter.md). Do not load or apply CK3 evidence rules to other projects.

Automated audit, a pending review package, and human signoff are three different states. Never infer or fabricate human approval. Publishing is outside this skill: even a GREEN export does not authorize uploading, replacing, or deleting external media.
