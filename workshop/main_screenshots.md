# Main Workshop Screenshots

The README uses all ten focused screenshots. The Steam Workshop description uses eight because Steam's documented
description limit is 8,000 UTF-8 bytes, while the Steam-hosted media strip keeps six broad feature previews. Description
images use direct `raw.githubusercontent.com` URLs pinned to image-only commit
`bdc87ac77a3207945343ccdf277d6c4259bce65c`; blob, redirecting raw and release-asset URLs are forbidden.

## Sources And Uses

| Order | Feature | Acceptance source | Crop `(left, top, right, bottom)` | Tracked JPEG | README | BBCode | Steam media |
|---|---|---|---|---|---|---|---|
| 1 | Opening pact | `xar_terminal_observer_nondebug3_20260821/05_pact_window.png` | `450,250,2050,1150` | `screenshots/gallery/01_pact.jpg` | yes | yes | yes |
| 2 | Reincarnation shop | `xar_terminal_observer_nondebug3_20260821/05_shop_window.png` | `450,250,2050,1150` | `screenshots/gallery/02_reincarnation_shop.jpg` | yes | yes | yes |
| 3 | Blessing choice | `xar_terminal_observer_nondebug3_20260821/05_bless_window.png` | `450,250,2050,1150` | `screenshots/gallery/03_blessing_choice.jpg` | yes | yes | yes |
| 4 | Curse choice | `xar_terminal_observer_nondebug3_20260821/05_curse_window.png` | `450,250,2050,1150` | `screenshots/gallery/04_curse_choice.jpg` | yes | yes | no |
| 5 | Glassfire Ledger | `xar_terminal_observer_nondebug3_20260821/06_ledger_event.png` | `450,250,2050,1150` | `screenshots/gallery/05_glassfire_ledger.jpg` | yes | yes | no |
| 6 | Lifetime contracts | `xar_terminal_observer_nondebug3_20260821/06_contract_event.png` | `450,250,2050,1150` | `screenshots/gallery/06_lifetime_contracts.jpg` | yes | yes | yes |
| 7 | Glassfire Gaze | `xar_terminal_observer_nondebug3_20260821/07_trait_hover.png` | `0,150,1225,1230` | `screenshots/gallery/07_glassfire_gaze.jpg` | yes | no | no |
| 8 | Courtier essentials | `xar_final85_courtier_creator_20260821/11_cc_numeric_profile.png` | `325,120,2185,1265` | `screenshots/gallery/08_courtier_essentials.jpg` | yes | yes | yes |
| 9 | Courtier origin | `xar_final85_courtier_creator_20260821/17_cc_origin_render.png` | `325,120,2185,1265` | `screenshots/gallery/09_courtier_origin.jpg` | yes | no | no |
| 10 | Death settlement | `xar_terminal_observer_nondebug3_20260821/04_end_state.png` | `450,250,2050,1150` | `screenshots/gallery/10_death_settlement.jpg` | yes | yes | yes |

Orders 1-7 and 10 come from a GREEN isolated non-debug CK3 `1.19.0.6` acceptance run. Orders 8-9 are focused crops of
the final main-mod courtier-creator acceptance run; the crop contains only the shipped creator modal and removes all
debug-mode chrome outside it. The tracked JPEGs use Pillow quality 90, optimization and 4:2:2 subsampling. Their focused
dimensions are 1600x900, except Gaze at 1225x1080 and the two courtier views at 1860x1145; every file is below 0.5 MB.

The original orders 5-7 captured CK3's native 100x100 software cursor at screen center. For orders 5-6, image-only commit
`bdc87ac77a3207945343ccdf277d6c4259bce65c` restores `(1230,670,1330,770)` from the same run's clean
`05_bless_window.png`; these events share the same fixed `xar_glassfire` background, and pixels immediately outside the
cursor differ by at most ordinary render noise. Order 7 uses the tighter crop above to exclude the cursor. No gameplay
state, event text or shipped artwork was altered.

These are presentation derivatives of already-reviewed acceptance evidence, not a new gameplay test. Updating README,
BBCode and these JPEGs does not change either mod source tree, release manifest, runtime script or shipped asset, so it
requires image/URL/description validation rather than another CK3 acceptance run. The four original root-level
`screenshots/01.jpg` through `04.jpg` remain historical files but are no longer embedded or present in the Steam media
strip.

## Live Verification

On 2026-08-21, item `3784706360` was updated without uploading a new mod content package. Steam's published-file API
returned a description that matched `workshop/description.bbcode` after normalizing CRLF to LF. Its public HTML contained
eight distinct gallery raw URLs and eight matching `crossorigin="anonymous"` image elements; scrolling the description in
the desktop Steam client showed all eight rendered without broken placeholders.

The four historical Steam-hosted screenshots were replaced with orders 1, 2, 3, 6, 8 and 10 above. After saving, the
public page contained exactly six `highlight_strip_item` elements and the desktop client showed the same six previews.
