# Ox Here 1.0.1 Release QA

This document records the evidence boundary for the standalone `ox_here` CK3 mod. It is a release checklist, not a claim
that every gate below has the same validation strength.

## Release Identity

- Mod: `Ox Here! / 牛来`
- Version: `1.0.1`
- Supported and live-tested engine baseline: CK3 `1.19.0.6`
- Formal package: the deterministic 22-file staging produced by `tools/build_ox_here_release.py`
- Git identity: commit `5e93fe5a73cbcce206aa31268f3ef601408d4d3d`, annotated tag `ox-here-v1.0.1`
- Public GitHub release: `https://github.com/XenoAmess/ck3_eternal_recurrence/releases/tag/ox-here-v1.0.1`
- Public Workshop item: `3790635143`, title `Ox Here! / 牛来`,
  `https://steamcommunity.com/sharedfiles/filedetails/?id=3790635143`
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

## Automated And Package Checks

Final release snapshot recorded on 2026-08-27:

| Check | Result | Evidence |
|---|---|---|
| MiniMax caller unit tests | GREEN, 19 tests | `tools/.venv/Scripts/python.exe tools/test_translate_localization_minimax.py` |
| Ox Here release-builder tests | GREEN, 7 tests | `tools/.venv/Scripts/python.exe tools/test_build_ox_here_release.py` |
| Nine-language structure audit | GREEN | UTF-8 BOM, identical order of 18 keys per language, CK3 bracket-scope and escaped-newline token parity |
| Clean-tag deterministic release | GREEN, 22 files | Formal manifest SHA-256 `601cde2d39365230e226b71c6c22220000cd6230ec42fe19b1009f1f377681ae`; ZIP SHA-256 `4611c13c7165841a7de204c4bc11a51e119496217a3b97f94d310fed195aef8a` |
| Workshop-ID sidecar | GREEN, 22 files | Sidecar manifest SHA-256 `4acd11a741de3d088d1e4f9afb5079e9e3303aabeb8f5f3b93b1dd9852a3c13b`; binds item `3790635143` without changing the product ZIP |
| Fresh Workshop cache verification | GREEN, 22/22 files | The item cache was moved aside, downloaded into an absent path, and strictly verified against the ID-bearing sidecar with only the launcher's canonical descriptor normalization permitted |
| Commit-pinned screenshot fetch | GREEN, 4 images | Media commit `f0f6066e44c76f3f78fd10bc28e2c90e45681df7`; HTTP 200 `image/jpeg`, byte length and SHA-256 matched all four local files |
| Official tag CI | GREEN | Run `33013156110` on tag `ox-here-v1.0.1`, head `5e93fe5a73cbcce206aa31268f3ef601408d4d3d`; artifact `release-candidate-ox-here-v1.0.1-33013156110`, 701,529-byte Actions archive, artifact digest `sha256:6cf45327d15a6e5fad848c215752371abe63eaef0f285cc04b81e14a1ad8d07b` |

The Actions artifact digest identifies GitHub's outer artifact archive; it is not the deterministic product ZIP hash. The
formal manifest and product ZIP hashes above identify the clean tagged release. Rerun
`tools/build_ox_here_release.py --check` after any later localization, descriptor, thumbnail or runtime edit and replace
the release hashes for the next version.

The public GitHub release exposes the two canonical clean-tag deliverables: `ox_here-v1.0.1.manifest.json` (4,026 bytes,
SHA-256 `601cde2d39365230e226b71c6c22220000cd6230ec42fe19b1009f1f377681ae`) and
`ox_here-v1.0.1.zip` (701,751 bytes, SHA-256
`4611c13c7165841a7de204c4bc11a51e119496217a3b97f94d310fed195aef8a`). The item-ID sidecar remains verification
evidence only and is not substituted for the canonical public manifest.

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

## Published Workshop-Copy Functional Evidence

After strict 22/22 fresh-cache verification, the downloaded item was normalized into a disposable runtime copy and passed
the same non-debug functional scenario:

- Artifact: `C:\Users\xenoa\AppData\Local\Temp\oxa_workshop_3790635143_green_20260827`
- Top-level `report.json` SHA-256:
  `2bb66729773dec95a333323664527675c51d0c54ec005f43d843c28242363b1c`
- Result: `GREEN`; cell duration: 255.448 seconds
- Product runtime tree SHA-256 before and after:
  `cbf393d4201c31a0d8e73ff9d9811ba6304e395800ccb73673d73519729488e8`
- The normalized runtime contained all 22 formal files, including nine localization files and the thumbnail; its product
  and fixture trees remained unchanged, project diagnostics were empty, and protected real player storage remained
  unchanged through the five-second postflight.
- The functional markers again passed decline, exact one-character delivery, warrior identity/Prowess, Knight and Champion
  appointment, affairs/secret, incompatible-orientation Seduce, and zero Champion salary.

This is real execution of a copy derived from the newly downloaded Workshop cache. It does not turn the descriptor's
remote-ID/line-ending normalization into a repository change, and it does not prove Steam CDN availability outside the
network and time observed during this release.

## Workshop Publication Result

The Steam-started PDX launcher logged `Publishing mod succeeded` at `2026-08-26T21:14:08.252Z`. Anonymous Steam API and
public-page checks then established:

- item `3790635143`, title `Ox Here! / 牛来`, public `visibility: 0`;
- content manifest `7196545944095046595` and API `file_size: 716112`;
- preview URL
  `https://images.steamusercontent.com/ugc/13157177357891033813/768F75FE6A133ED324B0E52746240C69EAE8C9AB/`;
- the query-free preview response is the expected 640×640 RGB PNG, 686,490 bytes, SHA-256
  `330bf1fb1330fd817b46b47ac3345e4e5f32472152b18d4277790c0c0c767b59`, byte-identical to the clean-tag thumbnail;
- the public HTML contains exactly four `highlight_strip_item` screenshots in the ledger order;
- the published description contains exactly the four commit-pinned GitHub raw image URLs from
  `workshop/ox_here_description.bbcode`.

The same four Steam CDN screenshot originals were anonymously fetched as `image/jpeg`; dimensions, byte counts and hashes
matched the four tracked Workshop JPEGs exactly. Their final CDN bases are recorded in
`workshop/ox_here_screenshots.md`.

## Honest Boundary

The original GREEN artifact mounted the then-current source projection; the later Workshop-copy artifact closes the
important gap by executing a normalized copy of the final 22-file fresh download. The nine-language structure, key order,
protected-token parity and model-led semantic review are GREEN, and the full package loads without project diagnostics.
There is still no nine-cell visual matrix that opens both UI surfaces under every game language, so this release does
**not** claim native-speaker certification or per-language proof against every possible font-specific truncation.

The live AI scheduler was not held until it happened to choose the decision, so the published-cache run does not add an
empirical AI choice-frequency distribution. It confirms that the exact production policy loaded and that the shared
recruitment path executes; the 12-month checks, low weights and exact one-year cooldown remain code-contract evidence.
