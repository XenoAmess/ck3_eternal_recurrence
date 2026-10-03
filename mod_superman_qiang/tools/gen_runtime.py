"""Generate runtime scripts and pinned, narrowly scoped vanilla projections."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct

from runtime_data import (EN, EXE_SHA256, GAME_VERSION, HOOKS, MINIMUM_AGE,
                          ROMANCE_SOURCE_SHA256, SEX_EXPERIENCE_MAXIMUM,
                          SEX_EXPERIENCE_VARIABLE, SKILL_BALANCE_MAXIMUM, SKILLS, ZH)

MOD_ROOT = Path(__file__).resolve().parents[1]
PINNED_ROOT = Path(__file__).resolve().parent / "vanilla_hooks"
HEADER = "# GENERATED FILE - do not edit. Regenerate with tools/gen_runtime.py\n"
INSERT_BEGIN = "\t# SXAD_HOOK_BEGIN\n"
INSERT_END = "\t# SXAD_HOOK_END\n"
DEFAULT_GAME_ROOT = Path("C:/SteamLibrary/steamapps/common/Crusader Kings III")


def encode(text: str) -> bytes:
    return text.replace("\r\n", "\n").encode("utf-8-sig")


def extract_effect(source: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)}\s*=\s*\{{", source)
    if match is None:
        raise ValueError(f"Vanilla hook not found: {name}")
    start = match.start()
    depth = 0
    quoted = comment = escaped = False
    for pos in range(source.index("{", start), len(source)):
        char = source[pos]
        if comment:
            comment = char != "\n"
            continue
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == "#":
            comment = True
        elif char == '"':
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start:pos + 1].replace("\r\n", "\n") + "\n"
    raise ValueError(f"Unbalanced vanilla hook: {name}")


def refresh_vanilla(game_root: Path) -> None:
    source_path = game_root / "game/common/scripted_effects/00_romance_effects.txt"
    raw = source_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ROMANCE_SOURCE_SHA256:
        raise ValueError("Refusing non-pinned romance source; review a new game version first")
    source = raw.decode("utf-8-sig").replace("\r\n", "\n")
    PINNED_ROOT.mkdir(parents=True, exist_ok=True)
    entries = {}
    for name in HOOKS:
        body = encode(extract_effect(source, name))
        (PINNED_ROOT / f"{name}.txt").write_bytes(body)
        entries[name] = hashlib.sha256(body).hexdigest()
    metadata = {"game_version": GAME_VERSION, "exe_sha256": EXE_SHA256,
                "romance_source_sha256": ROMANCE_SOURCE_SHA256, "hooks": entries}
    (PINNED_ROOT / "sources.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


def hook_outputs() -> dict[str, bytes]:
    metadata = json.loads((PINNED_ROOT / "sources.json").read_text(encoding="utf-8"))
    if metadata.get("romance_source_sha256") != ROMANCE_SOURCE_SHA256:
        raise ValueError("Pinned romance identity differs from runtime_data")
    outputs = {}
    for name, helper in HOOKS.items():
        raw = (PINNED_ROOT / f"{name}.txt").read_bytes()
        if hashlib.sha256(raw).hexdigest() != metadata["hooks"].get(name):
            raise ValueError(f"Pinned vanilla hook bytes changed: {name}")
        original = raw.decode("utf-8-sig")
        if extract_effect(original, name) != original:
            raise ValueError(f"Pinned input must contain exactly one hook: {name}")
        insertion = INSERT_BEGIN + f"\thidden_effect = {{ {helper} }}\n" + INSERT_END
        # Paired hook needs the two vanilla saved scopes; unknown hook has no partner.
        if name == "had_sex_with_effect":
            anchor = "\t$CHARACTER$ = { save_scope_as = had_sex_with_effect_partner }\n"
            if original.count(anchor) != 1:
                raise ValueError("Paired hook anchor changed")
            projected = original.replace(anchor, anchor + insertion, 1)
        else:
            projected = original.replace("had_sex_with_unknown_effect = {\n",
                                         "had_sex_with_unknown_effect = {\n" + insertion, 1)
        outputs[f"common/scripted_effects/zz_sxad_{name}.txt"] = encode(
            HEADER + f"# Controlled CK3 {GAME_VERSION} projection; strip SXAD_HOOK block to recover pinned input.\n" + projected)
    return outputs


def experience_effects() -> str:
    var = SEX_EXPERIENCE_VARIABLE
    return HEADER + f"""
# Current scope is a living, eligible participant. No experience query writes state.
sxad_increment_experience_effect = {{
    if = {{
        limit = {{ has_variable = {var} }}
        if = {{
            limit = {{ var:{var} < {SEX_EXPERIENCE_MAXIMUM} }}
            change_variable = {{ name = {var} add = 1 }}
        }}
    }}
    else = {{ set_variable = {{ name = {var} value = 1 }} }}
    if = {{
        limit = {{ NOT = {{ has_trait = sxad_sex_experience }} }}
        add_trait = sxad_sex_experience
    }}
}}

# The vanilla paired hook runs this once, before changing either experience count.
sxad_record_pair_effect = {{
    if = {{
        limit = {{ is_alive = yes age >= {MINIMUM_AGE} }}
        if = {{
            limit = {{ exists = $PARTNER$ }}
            if = {{
                limit = {{
                    $PARTNER$ = {{ is_alive = yes age >= {MINIMUM_AGE} }}
                    NOT = {{ this = $PARTNER$ }}
                }}
                save_temporary_scope_as = sxad_first
                $PARTNER$ = {{ save_temporary_scope_as = sxad_second }}
                if = {{
                    limit = {{ has_variable = {var} }}
                    if = {{
                        limit = {{ $PARTNER$ = {{ has_variable = {var} }} }}
                        if = {{
                            limit = {{ var:{var} > scope:sxad_second.var:{var} }}
                            sxad_select_transfer_effect = {{ DONOR = scope:sxad_second }}
                        }}
                        else_if = {{
                            limit = {{ var:{var} < scope:sxad_second.var:{var} }}
                            scope:sxad_second = {{ sxad_select_transfer_effect = {{ DONOR = scope:sxad_first }} }}
                        }}
                    }}
                    else_if = {{
                        limit = {{ var:{var} > 0 }}
                        sxad_select_transfer_effect = {{ DONOR = scope:sxad_second }}
                    }}
                }}
                else_if = {{
                    limit = {{ $PARTNER$ = {{ has_variable = {var} }} }}
                    if = {{
                        limit = {{ scope:sxad_second = {{ var:{var} > 0 }} }}
                        scope:sxad_second = {{ sxad_select_transfer_effect = {{ DONOR = scope:sxad_first }} }}
                    }}
                }}
                sxad_increment_experience_effect = yes
                scope:sxad_second = {{ sxad_increment_experience_effect = yes }}
            }}
        }}
    }}
}}

# Vanilla explicitly describes this partner as not an actual character.
sxad_record_unknown_effect = {{
    if = {{
        limit = {{ is_alive = yes age >= {MINIMUM_AGE} }}
        sxad_increment_experience_effect = yes
    }}
}}
"""


def scoped_compare(value_name: str, expression: str) -> str:
    # Tooltip simulation may not materialize preceding temporary values.
    return (f"trigger_if = {{ limit = {{ exists = scope:{value_name} }} {expression} }}\n"
            "trigger_else = { always = no }")


def probe_effects() -> str:
    chunks = [HEADER, "# Eligibility checks only read character skills/balances and set temporary flags.\n",
              "# Transfer balances are original modifier points; base skills are never changed.\n"]
    for skill in SKILLS:
        balance = f"sxad_{skill}_balance"
        chunks.append(f"""
sxad_probe_{skill}_effect = {{
    save_temporary_scope_value_as = {{ name = sxad_can_{skill} value = 0 }}
    if = {{
        limit = {{
            trigger_if = {{
                limit = {{ has_variable = {balance} }}
                var:{balance} >= -{SKILL_BALANCE_MAXIMUM}
                var:{balance} < {SKILL_BALANCE_MAXIMUM}
            }}
            trigger_else = {{ always = yes }}
            scope:sxad_donor = {{
                {skill} > 0
                trigger_if = {{
                    limit = {{ has_variable = {balance} }}
                    var:{balance} > -{SKILL_BALANCE_MAXIMUM}
                    var:{balance} <= {SKILL_BALANCE_MAXIMUM}
                }}
                trigger_else = {{ always = yes }}
            }}
        }}
        save_temporary_scope_value_as = {{ name = sxad_can_{skill} value = 1 }}
    }}
}}

# Current character owns the signed balance. Scale is sampled when assigned.
sxad_rebuild_{skill}_modifier_effect = {{
    remove_character_modifier = sxad_{skill}_gain_modifier
    remove_character_modifier = sxad_{skill}_loss_modifier
    if = {{
        limit = {{ has_variable = {balance} }}
        if = {{
            limit = {{ var:{balance} > 0 }}
            add_character_modifier = sxad_{skill}_gain_modifier
        }}
        else_if = {{
            limit = {{ var:{balance} < 0 }}
            add_character_modifier = sxad_{skill}_loss_modifier
        }}
    }}
    force_character_skill_recalculation = yes
}}
""")
    chunks.append("\nsxad_rebuild_skill_modifiers_effect = {\n")
    for skill in SKILLS:
        chunks.append(f"    sxad_rebuild_{skill}_modifier_effect = yes\n")
    chunks.append("}\n")
    return "".join(chunks)


def transfer_effects() -> str:
    chunks = [HEADER]
    for skill in SKILLS:
        balance = f"sxad_{skill}_balance"
        chunks.append(f"""
# Current scope is receiver. This independently checked helper is also the random branch.
sxad_transfer_{skill}_effect = {{
    save_temporary_scope_as = sxad_receiver
    $DONOR$ = {{ save_temporary_scope_as = sxad_donor }}
    force_character_skill_recalculation = yes
    scope:sxad_donor = {{ force_character_skill_recalculation = yes }}
    sxad_probe_{skill}_effect = yes
    if = {{
        limit = {{ {scoped_compare(f'sxad_can_{skill}', f'scope:sxad_can_{skill} = 1')} }}
        if = {{
            limit = {{ has_variable = {balance} }}
            change_variable = {{ name = {balance} add = 1 }}
        }}
        else = {{ set_variable = {{ name = {balance} value = 1 }} }}
        scope:sxad_donor = {{
            if = {{
                limit = {{ has_variable = {balance} }}
                change_variable = {{ name = {balance} add = -1 }}
            }}
            else = {{ set_variable = {{ name = {balance} value = -1 }} }}
        }}
        sxad_rebuild_{skill}_modifier_effect = yes
        scope:sxad_donor = {{ sxad_rebuild_{skill}_modifier_effect = yes }}
    }}
}}
""")
    chunks.append("\nsxad_select_transfer_effect = {\n"
                  "    save_temporary_scope_as = sxad_receiver\n"
                  "    $DONOR$ = { save_temporary_scope_as = sxad_donor }\n"
                  "    force_character_skill_recalculation = yes\n"
                  "    scope:sxad_donor = { force_character_skill_recalculation = yes }\n")
    for skill in SKILLS:
        chunks.append(f"    sxad_probe_{skill}_effect = yes\n")
    chunks.append("    if = {\n        limit = {\n            OR = {\n")
    for skill in SKILLS:
        chunks.append(f"                AND = {{ {scoped_compare(f'sxad_can_{skill}', f'scope:sxad_can_{skill} = 1')} }}\n")
    chunks.append("            }\n        }\n        random_list = {\n")
    for skill in SKILLS:
        chunks.append(f"""            1 = {{
                trigger = {{ {scoped_compare(f'sxad_can_{skill}', f'scope:sxad_can_{skill} = 1')} }}
                sxad_transfer_{skill}_effect = {{ DONOR = scope:sxad_donor }}
            }}
""")
    chunks.append("        }\n    }\n}\n")
    return "".join(chunks)


def values() -> str:
    result = HEADER + f"""
# Pure guarded read. Missing variables represent zero and are never initialized here.
sxad_experience_value = {{
    value = 0
    if = {{
        limit = {{ has_variable = {SEX_EXPERIENCE_VARIABLE} }}
        add = var:{SEX_EXPERIENCE_VARIABLE}
    }}
}}
"""
    for skill in SKILLS:
        result += f"\nsxad_{skill}_value = {{ value = {skill} }}\n"
        balance = f"sxad_{skill}_balance"
        result += f"""
sxad_{skill}_balance_value = {{
    value = 0
    if = {{
        limit = {{ has_variable = {balance} }}
        add = var:{balance}
    }}
}}

sxad_{skill}_gain_scale = {{
    value = 0
    if = {{
        limit = {{ has_variable = {balance} }}
        if = {{
            limit = {{ var:{balance} > 0 }}
            add = var:{balance}
        }}
    }}
}}

sxad_{skill}_loss_scale = {{
    value = 0
    if = {{
        limit = {{ has_variable = {balance} }}
        if = {{
            limit = {{ var:{balance} < 0 }}
            add = var:{balance}
            multiply = -1
        }}
    }}
}}
"""
    return result


def skill_balance_modifiers() -> str:
    result = HEADER + "# Definition-local scale is evaluated in the receiving character scope.\n"
    for skill in SKILLS:
        result += f"""
sxad_{skill}_gain_modifier = {{
    {skill} = 1
    scale = {{
        value = sxad_{skill}_gain_scale
        desc = sxad_absorbed_skill_modifier
    }}
}}

sxad_{skill}_loss_modifier = {{
    {skill} = -1
    scale = {{
        value = sxad_{skill}_loss_scale
        desc = sxad_drained_skill_modifier
    }}
}}
"""
    return result


def trait() -> str:
    return HEADER + """
sxad_sex_experience = {
    icon = sxad_sex_experience.dds
    minimum_age = 18
    birth = 0
    random_creation = 0
    inherit_chance = 0
    desc = {
        first_valid = {
            triggered_desc = {
                trigger = { NOT = { exists = this } }
                desc = trait_sxad_sex_experience_desc
            }
            desc = trait_sxad_sex_experience_character_desc
        }
    }
}
"""


def interaction() -> str:
    return HEADER + """
sxad_view_experience_interaction = {
    category = interaction_category_friendly
    common_interaction = yes
    interface_priority = 200
    icon = icon_scheme_seduce
    desc = sxad_view_experience_interaction_desc
    use_diplomatic_range = no
    ignores_pending_interaction_block = yes
    auto_accept = yes
    is_shown = {
        scope:actor = { is_ai = no }
        scope:recipient = { is_alive = yes age >= 18 }
    }
    is_valid_showing_failures_only = {
        scope:actor = { is_ai = no }
        scope:recipient = { is_alive = yes age >= 18 }
    }
    on_accept = {
        custom_tooltip = sxad_view_experience_interaction_accept_tt
        hidden_effect = {
            scope:recipient = { save_scope_as = sxad_view_subject }
            scope:actor = { trigger_event = sxad.1 }
        }
    }
    ai_will_do = { base = 0 }
}
"""


def events() -> str:
    return HEADER + """
namespace = sxad

# Read-only detail event: no immediate, after, experience effect or variable write.
sxad.1 = {
    type = character_event
    title = sxad.1.t
    desc = sxad.1.desc
    theme = intrigue
    left_portrait = { character = scope:sxad_view_subject animation = idle }
    option = { name = sxad.1.a }
}
"""


def localization(language: str, entries: dict[str, str]) -> str:
    lines = [f"l_{language}:\n", " # GENERATED FILE - do not edit. Regenerate with tools/gen_runtime.py\n"]
    for key, value in entries.items():
        escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        lines.append(f' {key}:0 "{escaped}"\n')
    return "".join(lines)


def trait_icon() -> bytes:
    width = height = 120
    pixels = bytearray()
    for y in range(height):
        for x in range(width):
            px, py = x - 59.5, y - 59.5
            radius = math.hypot(px, py)
            alpha = max(0, min(255, round((56.0 - radius) * 255)))
            red, green, blue = 31, 18, 51
            ring_a = abs(math.hypot(px + 15, py) - 23) < 5
            ring_b = abs(math.hypot(px - 15, py) - 23) < 5
            border = 50 < radius < 54
            if ring_a or ring_b or border:
                red, green, blue = 224, 186, 95
            if abs(px) < 4 and -43 < py < -30:
                red, green, blue = 255, 234, 161
            pixels.extend((red, green, blue, alpha))
    flags = 0x100F
    pixel_format = struct.pack("<8I", 32, 0x41, 0, 32, 0x000000FF, 0x0000FF00, 0x00FF0000, 0xFF000000)
    header = struct.pack("<7I", 124, flags, height, width, width * 4, 0, 0) + bytes(44)
    header += pixel_format + struct.pack("<5I", 0x1000, 0, 0, 0, 0)
    return b"DDS " + header + pixels


def render_outputs(game_root: Path | None = None) -> dict[str, bytes]:
    # game_root is accepted for API stability; read-only rendering uses pinned inputs.
    outputs = hook_outputs()
    text_outputs = {
        "common/scripted_effects/sxad_experience_effects.txt": experience_effects(),
        "common/scripted_effects/sxad_probe_skill_effects.txt": probe_effects(),
        "common/scripted_effects/sxad_transfer_effects.txt": transfer_effects(),
        "common/script_values/sxad_values.txt": values(),
        "common/modifiers/sxad_skill_balance_modifiers.txt": skill_balance_modifiers(),
        "common/traits/sxad_traits.txt": trait(),
        "common/character_interactions/sxad_interactions.txt": interaction(),
        "events/sxad_events.txt": events(),
        "localization/simp_chinese/sxad_l_simp_chinese.yml": localization("simp_chinese", ZH),
        "localization/english/sxad_l_english.yml": localization("english", EN),
    }
    outputs.update({name: encode(body) for name, body in text_outputs.items()})
    outputs["gfx/interface/icons/traits/sxad_sex_experience.dds"] = trait_icon()
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Read-only byte parity check")
    parser.add_argument("--refresh-vanilla", action="store_true", help="Extract the two pinned vanilla hooks after source SHA validation")
    parser.add_argument("--game-root", type=Path, default=DEFAULT_GAME_ROOT)
    args = parser.parse_args()
    if args.check and args.refresh_vanilla:
        parser.error("--check cannot refresh inputs")
    if args.refresh_vanilla:
        refresh_vanilla(args.game_root)
    outputs = render_outputs()
    errors = []
    for relative, expected in outputs.items():
        target = MOD_ROOT / relative
        if args.check:
            if not target.is_file() or target.read_bytes() != expected:
                errors.append(relative)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(expected)
    if errors:
        raise RuntimeError("Generated bytes differ: " + ", ".join(errors))
    print(f"{'Checked' if args.check else 'Generated'} {len(outputs)} runtime files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
