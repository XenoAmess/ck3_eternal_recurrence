# Ox Here 1.0.1 Release QA

This document records the evidence boundary for the standalone `ox_here` CK3 mod. It is a release checklist, not a claim
that every gate below has the same validation strength.

## Release Identity

- Mod: `Ox Here! / 牛来`
- Version: `1.0.1`
- Supported and live-tested engine baseline: CK3 `1.19.0.6`
- Formal package: the deterministic 22-file staging produced by `tools/build_ox_here_release.py`
- Thumbnail: `ox_here/thumbnail.png`, projected from `images/ox_here_key_art.png` by
  `tools/compose_ox_here_key_art.py`
- Workshop copy: `workshop/ox_here_description.bbcode`
- Screenshot ledger: `workshop/ox_here_screenshots.md`

## Internationalization Pipeline

The release carries 18 localization keys in each of nine languages:

- English
- Simplified Chinese
- French
- German
- Japanese
- Korean
- Polish
- Russian
- Spanish

English and Simplified Chinese are the reviewed source/reference pair. For the other seven languages, MiniMax-M3 produced
small, caller-selected key-value candidate batches: 7 languages × 18 keys = 126 candidate strings. The API key was read
only from `MINIMAX_API_KEY`; only its presence was checked, and neither the key nor its value belongs in a command log,
artifact, source file, or report.

The reusable caller is `tools/translate_localization_minimax.py`. Its responsibility is deliberately narrow:

- send only the selected key-value payload, target language, short task context, reference values and protected tokens;
- request MiniMax-M3 through the current OpenAI-compatible Chat Completions endpoint;
- require one strict JSON object, reject duplicate or changed key sets, and reject protected-token drift;
- preserve CK3 scopes/scripted localization, icon and formatting codes, escapes, URLs, common placeholders and balanced ICU
  plural/select blocks;
- retry a finite maximum of two attempts per target and report safe diagnostics;
- print candidate JSON only; never write localization files or decide what belongs in the project.

The current model then reviewed every candidate and applied corrections for meaning, UI length, consistent CK3 realm and
court terminology, the localized `Ox, come!` / `The ox arrived!` wordplay, grammar, protected scopes, escaped newlines and
file syntax. This is a model-led release review performed on the user's behalf. It is explicitly **not** native-speaker
certification, and no second call to MiniMax is counted as independent semantic verification.

## Current Automated Checks

Snapshot recorded on 2026-08-27 before the final Workshop upload:

| Check | Result | Evidence |
|---|---|---|
| MiniMax caller unit tests | GREEN, 19 tests | `tools/.venv/Scripts/python.exe tools/test_translate_localization_minimax.py` |
| Ox Here release-builder tests | GREEN, 7 tests | `tools/.venv/Scripts/python.exe tools/test_build_ox_here_release.py` |
| Nine-language structure audit | GREEN | UTF-8 BOM, identical order of 18 keys per language, CK3 bracket-scope and escaped-newline token parity |
| Deterministic release check | GREEN, 22 files | Manifest SHA-256 `08ec997424d4d3d161e789ae455979a49427d23b6c696a10a66b164e6e3616d2`; ZIP SHA-256 `4611c13c7165841a7de204c4bc11a51e119496217a3b97f94d310fed195aef8a` |
| Commit-pinned screenshot fetch | GREEN, 4 images | Media commit `f0f6066e44c76f3f78fd10bc28e2c90e45681df7`; HTTP 200 `image/jpeg`, byte length and SHA-256 matched all four local files |

The manifest and ZIP hashes identify this snapshot only. Rerun `tools/build_ox_here_release.py --check` after any later
localization, descriptor, thumbnail or runtime edit and replace the hashes before tagging.

## Real CK3 Functional Evidence

Final functional acceptance artifact:

`C:\Users\xenoa\AppData\Local\Temp\oxa_20260827_035146_f80a6f08`

- `report.json` SHA-256:
  `f02254dc0504695158d1a1800801d1285153681378f7c8b9bb0ebc2131e2a34c`
- Result: `GREEN`
- Duration: 208.106 seconds
- Engine: CK3 `1.19.0.6`
- Executable SHA-256 before and after:
  `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`
- Non-debug game, isolated one-use userdir, verified product-before-fixture mount order
- Product and fixture runtime trees remained unchanged during the run
- Protected real player storage remained unchanged
- Project diagnostics: empty

The fixture markers and scenario evidence prove:

- the decline option has zero side effects;
- recruitment delivers exactly one character;
- the warrior identity and final Prowess range are 46–66;
- the character becomes a courtier and forced Knight;
- a vacant Champion position is filled when eligible, at zero salary;
- adult consort affairs and `secret_lover` secrets are applied;
- a Seduce scheme starts even for the fixture's incompatible orientation;
- the human arrival event explicitly attributes the character to the decision;
- the human production path and all shared recruitment effects load and execute without project diagnostics.

The run did not wait for the AI scheduler to make a random decision. AI availability, 12-month checks, low
decision/recruit weights and the exact one-year cooldown are exact production-script contracts that loaded without parser
or runtime diagnostics; they are not presented as an observed AI choice-frequency test.

Rendered African appearance and blond hair were manually reviewed in the captured PNG. That is visual evidence, not a
script-level phenotype assertion; the report says CK3 exposes no reliable live trigger for generated phenotype or rendered
hair color.

## Honest Boundary And Remaining Publication Gates

The GREEN functional artifact mounted a 14-file source-runtime projection containing English and Simplified Chinese. It
predates the seven added language files, the release thumbnail, and the final 22-file package. Therefore it proves the
gameplay implementation and the captured Chinese presentation path, but it does **not** by itself prove that all nine
language files load without visual truncation or that a Steam-downloaded copy matches the final staging.

Before making the Workshop item public:

1. Rerun the localization/unit/builder checks and create the formal staging from a clean tagged commit.
2. Upload the package while hidden; keep `remote_file_id` only in the outer user-directory `.mod` and rebuild staging after
   the launcher temporarily writes it into the inner descriptor.
3. The four GitHub raw URLs pinned to media commit
   `f0f6066e44c76f3f78fd10bc28e2c90e45681df7` already match their recorded SHA-256 values. Upload the same JPEGs to Steam,
   record the actual Steam CDN bases, and anonymously verify the media strip and description.
4. Download into a fresh empty Workshop cache, verify its tree against the rebuilt canonical staging, and boot that copy.
5. Inspect the decision and arrival text in all nine game languages for raw keys, broken scopes and visible truncation.
   Structural/model review must not be reported as native-speaker certification.
6. Only after those checks are GREEN should visibility be changed to public and the final item ID, URL, package hashes and
   fresh-cache evidence be appended here.
