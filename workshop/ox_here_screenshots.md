# Ox Here Workshop Screenshots

The four Workshop images are deterministic crops of real CK3 `1.19.0.6` captures from the final functional acceptance
artifact. They are not generated illustrations and must not be placed in the 22-file mod staging. The immutable media-bearing
commit is `f0f6066e44c76f3f78fd10bc28e2c90e45681df7`; `workshop/ox_here_description.bbcode` embeds all four images through
direct raw URLs pinned to that commit.

## Evidence Source

- Artifact root: `C:\Users\xenoa\AppData\Local\Temp\oxa_20260827_035146_f80a6f08`
- Report: `report.json`
- Report SHA-256: `f02254dc0504695158d1a1800801d1285153681378f7c8b9bb0ebc2131e2a34c`
- Result: `GREEN`
- Engine: CK3 `1.19.0.6`, non-debug, isolated userdir, 2560×1440
- CK3 executable SHA-256 before and after the run:
  `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`
- Renderer: `tools/compose_ox_here_workshop_media.py`, Pillow quality 90, optimized progressive JPEG, 4:4:4
  (`subsampling=0`), each output below 2,000,000 bytes

## Upload Order And Projections

| Order | Feature / 功能 | Acceptance source | Source SHA-256 | Crop `(left, top, right, bottom)` | Workshop upload | Dimensions | Bytes | Output SHA-256 | Steam CDN base |
|---|---|---|---|---|---|---:|---:|---|---|
| 1 | Decision and both options / 决议与两个选项 | `cell/07_recruit_option.png` | `794970a18d4441c369e98c1a22ebc6c2561547cb6a986e54b3ea20f7984d8336` | `900,90,1720,1380` | `workshop/ox_here_media/01_decision_options.jpg` | 820×1290 | 197,819 | `774d7578390ec42871fcf5a78703bf580986b13b5a3ef75f0ead87355f5c9b4e` | `https://images.steamusercontent.com/ugc/14676299510730740084/A2DFFFF78D45BC2B7A2FFA407EC30493838E2601/` |
| 2 | Explicit decision-attributed arrival / 明确归因于决议的到庭事件 | `cell/08_ox_here_arrival_event.png` | `eaaecba75bbb1b49f87b69a4bb6240e0c5f2ee1a0b411862192012e0d30d9f65` | `575,270,1980,1085` | `workshop/ox_here_media/02_arrival_event.jpg` | 1405×815 | 224,387 | `8c9e2b3b5dd3f2a8f932b58b811345a7d8a2d3f43489916fb613187dd3306827` | `https://images.steamusercontent.com/ugc/15580944339241781652/1113EBCBC41D7F17F629F71FCBB03871C3D27503/` |
| 3 | Generated warrior portrait / 生成勇士肖像 | `cell/08_ox_here_arrival_event.png` | `eaaecba75bbb1b49f87b69a4bb6240e0c5f2ee1a0b411862192012e0d30d9f65` | `1160,300,1880,1085` | `workshop/ox_here_media/03_warrior_portrait.jpg` | 720×785 | 114,307 | `4240c8cd8a5c33c3a15baafa4c3d43edb822e2c096f65de03e6cfb6e4e181d82` | `https://images.steamusercontent.com/ugc/15182171612751900735/B72229006A3B3B10E93806C61A69B2D95310E3B0/` |
| 4 | Champion appointment notification / 勇士任命通知 | `cell/08_ox_here_arrival_event_closed.png` | `9de019db1ce46311c3bc950c8fcb7b4f124dc50bde3b8cd827fdcf292498ee65` | `635,55,1740,300` | `workshop/ox_here_media/04_champion_appointment.jpg` | 1105×245 | 88,909 | `f3496b7d2c2f80382d23a8bca2e71c6334b8827d64c19721a75948e1da5b37fa` | `https://images.steamusercontent.com/ugc/12510709279365474505/84B7CB663BB9236E3D198B1E1AE0607C940D6FD2/` |

Recommended bilingual captions, with English first:

1. `The decision: recruit the ox, or walk away / 牛来决议：招募勇士，或者转身离开`
2. `“Did I just hear you say, ‘Ox, come?’” / “我听到你刚刚说，牛来？”`
3. `One formidable African-blond Kanuri warrior / 一名强悍的非洲金发卡努里勇士`
4. `Forced Knight; vacant Champion appointed at zero salary / 强制骑士；职位空缺时零薪担任勇士`

## Commit-Pinned Description URLs

The image URLs in the Workshop description use the same immutable, two-commit pattern as the main mod. It was completed as
follows:

1. All four media files were committed and pushed in
   `f0f6066e44c76f3f78fd10bc28e2c90e45681df7` while the BBCode used four unique sentinels.
2. Each sentinel was replaced with the matching direct
   `raw.githubusercontent.com/XenoAmess/ck3_eternal_recurrence/f0f6066.../workshop/ox_here_media/<FILE>.jpg` URL.
3. The URL-bearing BBCode and this ledger belong in a follow-up commit. The URLs must continue to point at the first media
   commit, never the follow-up commit, a branch, a GitHub blob page, a redirect, or a release asset.
4. On 2026-08-27, all four URLs were fetched without credentials. Every response was HTTP 200 with `image/jpeg`; the body
   length and SHA-256 matched the corresponding byte count and output hash in the projection table.

The four exact pinned URLs are:

| File | Commit-pinned raw URL |
|---|---|
| `01_decision_options.jpg` | `https://raw.githubusercontent.com/XenoAmess/ck3_eternal_recurrence/f0f6066e44c76f3f78fd10bc28e2c90e45681df7/workshop/ox_here_media/01_decision_options.jpg` |
| `02_arrival_event.jpg` | `https://raw.githubusercontent.com/XenoAmess/ck3_eternal_recurrence/f0f6066e44c76f3f78fd10bc28e2c90e45681df7/workshop/ox_here_media/02_arrival_event.jpg` |
| `03_warrior_portrait.jpg` | `https://raw.githubusercontent.com/XenoAmess/ck3_eternal_recurrence/f0f6066e44c76f3f78fd10bc28e2c90e45681df7/workshop/ox_here_media/03_warrior_portrait.jpg` |
| `04_champion_appointment.jpg` | `https://raw.githubusercontent.com/XenoAmess/ck3_eternal_recurrence/f0f6066e44c76f3f78fd10bc28e2c90e45681df7/workshop/ox_here_media/04_champion_appointment.jpg` |

## Evidence Boundary

The JPEGs are presentation derivatives of acceptance PNGs, not a new gameplay run. The crop and JPEG conversion do not
alter gameplay text or state. The report proves the decision flow, zero-effect decline, one-character delivery, final
Prowess range, courtier/Knight/Champion behavior, affairs and secret, orientation-independent Seduce scheme, zero Champion
salary, quiet project diagnostics, and unchanged protected player storage. Rendered ethnicity and hair are visual-review
evidence only because CK3 exposes no reliable live script trigger for those rendered phenotype details.

On 2026-08-27, public item `3790635143`
(`https://steamcommunity.com/sharedfiles/filedetails/?id=3790635143`) exposed exactly four
`highlight_strip_item` screenshots in table order. Each query-free Steam CDN base above was fetched anonymously as
`image/jpeg`; its dimensions, byte count and SHA-256 matched the corresponding tracked JPEG exactly. The public description
also contained exactly the four commit-pinned raw URLs listed above, so the description gallery and Steam media strip are
two independently hosted copies of the same accepted images.

Description images remain pinned to the first Git commit; the Steam CDN bases document the separately uploaded media-strip
copies. If any crop rectangle or JPEG setting changes, the dimensions, byte counts and hashes above must be replaced rather
than treated as equivalent evidence.
