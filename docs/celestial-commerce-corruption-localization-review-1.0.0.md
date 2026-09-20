# Celestial Commerce & Corruption 1.0.0 localization review

## Scope

The release projection contains 31 keys in each of nine CK3 languages: English, French, German, Japanese, Korean, Polish, Russian, Simplified Chinese, and Spanish. English and Simplified Chinese are the authored source languages. The other 217 values form the release translation scope.

## Candidate and review record

- `MINIMAX_API_KEY` presence was checked without printing or recording its value.
- The repository's `translate_localization_minimax.py` caller sent only the selected localization keys, the two source-language files where useful, short UI context, and protected CK3 tokens to `MiniMax-M3`.
- Requests were split between decision/trait copy and event copy. MiniMax output was treated only as candidate JSON; it never selected files, edited the repository, or judged acceptance.
- French, German, Japanese, Polish, Russian, and Spanish supplied usable drafts for all 31 keys after human review. Chinese leakage, English placeholders, malformed Japanese phrases, mixed-language Polish phrases, and terminology errors were rejected or corrected.
- Korean candidates repeatedly failed the caller's protected-token or target-script checks. None of those failed values were accepted; the Korean file was written and reviewed manually against the English behavior contract and current vanilla CK3 terminology.

Current vanilla terms were consulted for the relevant concepts, including Japanese `天朝制政府` / `物々交換品` / `功徳`, Korean `천조 정부` / `물물 교환 상품` / `공덕`, Russian `Мандатное правление`, and their French, German, Polish, and Spanish equivalents.

## Automated audit

The product static gate requires, for every language:

- UTF-8 with BOM and the correct CK3 language header;
- the exact 31-key inventory with no blanks or duplicate rows;
- exact preservation of CK3 concept links, scripted character expressions, and escaped newlines;
- identical numeric contracts for the 5, 10, 15, and 25 percentage-point tiers;
- no whole-file English placeholder copy; and
- expected Japanese, Korean, Russian, and Simplified Chinese script presence.

## Honest limitation

This is a structural and editorial review, not a native-speaker sign-off or a nine-language in-game truncation pass. The product's explicit release boundary is Simplified-Chinese-only live gameplay/UI acceptance; English and the other seven translations receive the static key, token, numeric, script, terminology, and format audits above. They are not launched as CK3 live-test locales, and no automated translation or static check is represented as human approval.
