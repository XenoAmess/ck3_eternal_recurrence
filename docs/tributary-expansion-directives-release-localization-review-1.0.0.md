# Tributary Expansion Directives 1.0.0 localization review

Date: 2026-09-14

## Scope

The release contains 25 player-visible keys in English, Simplified Chinese,
French, German, Japanese, Korean, Polish, Russian, and Spanish. Dynamic CK3
tokens, icon markup, formatting tags, scope calls, script-value calls, and war
name placeholders are required to remain byte-identical across languages.

## Candidate generation and human review

MiniMax-M3 received only the English key/value inventory, the Simplified
Chinese reference inventory, short product context, and protected tokens. The
caller printed JSON candidates and did not grant the model filesystem or
project access.

The first Korean candidate copied Simplified Chinese text and was rejected. A
second Korean-only request still mixed Chinese fragments and raw English nouns;
it was also rejected. Korean was then rewritten as Korean UI text by the
maintainer. Human review also corrected:

- German `Expansionsexpansion` and a mistranslation of “free” as “independent”;
- Polish uses of feudal-vassal terminology instead of tributary terminology;
- Russian gender/case errors around Prestige;
- Japanese CK3 terminology for Prestige and imprisonment;
- Spanish suzerain and target wording;
- capitalization and concise UI phrasing across all candidate languages.

French candidates were retained after terminology/token review. All final
files differ from the English inventory and retain the complete protected-token
set. Static validation is necessary but does not claim native-speaker literary
review for every language.
