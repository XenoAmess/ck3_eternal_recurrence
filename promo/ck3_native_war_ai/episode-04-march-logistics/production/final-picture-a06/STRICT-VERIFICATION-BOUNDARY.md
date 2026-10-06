# Portable metadata admission

The original 33-file source freeze is preserved exactly, including its manifest,
Root-approved rows and `RUNNING` / NULL result fields. The original
`verify_package.py` is retained as a historical source artifact. Its assertions
can be removed by Python optimization and are not the current admission gate.

Use `python -I -S verify_package_strict.py` for a zero-read PLAN, or add `--verify`
to verify the original bounded package-relative text inventory with explicit
failure checks. These checks remain active under `-O`. The manifest is the
declared inventory; its authenticated source is the exact repository commit,
not an assertion of authenticity made by this metadata consumer.

`plan_metadata.py` reads only local small JSON to describe six chapters, 69 cues
and nine incremental rows. Both tools omit all external assets and never import
or execute the archived renderer, create media, call a provider or open a game.
Original absolute locators in source and receipts remain historical notes.
Replaying a render requires actual assets, an explicit fresh environment and
source binding, and the applicable review. This is not a one-command rendering
package for another machine.

The future sealed movie, media audit, coded-frame review, human signoff and
OneDrive transfer require separate immutable additions. The original freeze's
pending fields are not overwritten by those later facts.
