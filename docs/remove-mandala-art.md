# Mandala Purge Art Assets

## Art direction

The key art depicts an ornate golden Mandala halo breaking apart above a grounded Southeast Asian castle and village at dawn. The dissolving celestial geometry represents the removal of false divinity; the stone settlement and returning daylight represent the world restored to ordinary rule.

The source was generated specifically for this mod as an original text-free bitmap. The prompt requested a CK3-compatible grand-strategy mood without copying a real person, a logo, or an existing game asset.

## Canonical files

| Role | Path | Contract |
|---|---|---|
| Editable/generated source | `images/remove_mandala_key_art.png` | 1254×1254 RGB PNG; SHA-256 `77873470ff67d3fb787a63dc59ca3aa77ab40ca2a0c1b845705a88c5927905d0` |
| Deterministic renderer | `tools/compose_remove_mandala_key_art.py` | center-crop/resize and bounded PNG compression |
| Launcher/Workshop thumbnail | `mod_remove_mandala/thumbnail.png` | 640×640 RGB PNG, below 1 MB; SHA-256 `e25dec879bf83fec2960a0c194e2f623cc2127902929a6e402ea2daf11e0415c` |
| Live-media renderer | `tools/compose_remove_mandala_workshop_media.py` | creates two sub-2 MB JPEG projections from the final real CK3 acceptance capture |

Run `py tools/compose_remove_mandala_key_art.py --check` to prove the tracked thumbnail is byte-identical to a fresh render. The source PNG and renderers are repository assets; only `thumbnail.png` belongs to the exact 15-file mod release.

The Workshop JPEG inventory and hashes are recorded separately in `workshop/remove_mandala_screenshots.md` after the final live run and upload.
