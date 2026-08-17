# -*- coding: utf-8 -*-
"""Static loc validation for the XAR mod.

Catches the class of bug where a customizable_localization key, its target key,
or a modifier name is missing from a non-English yml file. CK3 does not fall back
to English for these keys, so every supported language needs its own entry.

Called by run_acceptance.py before launching the game so loc issues fail fast
instead of being masked by error.log whitelists.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MOD = ROOT / "XenoAmess_s_Eternal_Recurrence"
LANGS = ["english", "simp_chinese", "french", "german", "japanese",
         "korean", "polish", "russian", "spanish"]


def read_text(path):
    return path.read_text(encoding="utf-8-sig", errors="replace")


def collect_yml_keys():
    """Return {lang: set(keys)} for all mod yml files."""
    keys = {lang: set() for lang in LANGS}
    for lang in LANGS:
        d = MOD / "localization" / lang
        if not d.exists():
            continue
        for p in d.glob("*.yml"):
            text = read_text(p)
            for m in re.finditer(r"(?m)^\s*([\w.]+):\d+", text):
                keys[lang].add(m.group(1))
    return keys


def collect_event_option_keys():
    """All `name = key` values used in event option blocks."""
    keys = set()
    text = read_text(MOD / "events" / "xar_events.txt")
    for m in re.finditer(r"(?m)^\s*name\s*=\s*([^\s#]+)", text):
        keys.add(m.group(1))
    return keys


def collect_custom_loc():
    """Return (defined_keys, referenced_keys) from customizable localization."""
    defined = set()
    referenced = set()
    text = read_text(MOD / "common" / "customizable_localization" / "xar_generated_pool_loc.txt")
    for m in re.finditer(r"(?m)^(xar_\w+)\s*=\s*{", text):
        defined.add(m.group(1))
    for m in re.finditer(r"localization_key\s*=\s*(xar_\w+)", text):
        referenced.add(m.group(1))
    return defined, referenced


def collect_modifier_keys():
    """Modifier IDs defined in generated pool modifiers."""
    keys = set()
    text = read_text(MOD / "common" / "modifiers" / "xar_generated_pool_modifiers.txt")
    for m in re.finditer(r"(?m)^(xar_\w+)\s*=\s*{", text):
        keys.add(m.group(1))
    return keys


def main():
    yml_keys = collect_yml_keys()
    option_keys = collect_event_option_keys()
    custom_defined, custom_referenced = collect_custom_loc()
    modifiers = collect_modifier_keys()

    errors = []

    # 1) Every event option name must be localizable in every language.
    #    It can be a plain yml key, or a custom-loc key that has a static entry.
    for key in sorted(option_keys):
        if key.startswith("xar."):
            # plain event loc keys live in xar_l_<lang>.yml
            for lang in LANGS:
                if key not in yml_keys[lang]:
                    errors.append(f"event option '{key}' missing in {lang} yml")
        elif key.startswith("xar_"):
            # custom-loc keys need a static entry to be recognized by CEventOptionDesc
            for lang in LANGS:
                if key not in yml_keys[lang]:
                    errors.append(f"custom-loc option '{key}' missing in {lang} yml")
        # vanilla/base-game keys are ignored

    # 2) Custom localization keys themselves need a static yml entry per language.
    for key in sorted(custom_defined):
        for lang in LANGS:
            if key not in yml_keys[lang]:
                errors.append(f"custom localization '{key}' missing in {lang} yml")

    # 3) Keys referenced *inside* custom localization must exist per language.
    for key in sorted(custom_referenced):
        for lang in LANGS:
            if key not in yml_keys[lang]:
                errors.append(f"custom-loc target '{key}' missing in {lang} yml")

    # 4) Modifier IDs need a name key per language.
    for key in sorted(modifiers):
        for lang in LANGS:
            if key not in yml_keys[lang]:
                errors.append(f"modifier '{key}' missing in {lang} yml")

    if errors:
        print("LOC VALIDATION FAILED")
        for e in errors:
            print(f"  {e}")
        return 1
    print(f"LOC VALIDATION OK: {len(option_keys)} option keys, "
          f"{len(custom_defined)} custom loc, {len(modifiers)} modifiers, "
          f"{len(LANGS)} languages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
