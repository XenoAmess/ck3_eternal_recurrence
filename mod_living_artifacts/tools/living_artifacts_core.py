"""Generate the native CK3 lifecycle and management of living artifacts.

All returned text is BOM-free; the release generator owns file encoding.  The
runtime has no Python dependency.  Source bindings are recorded next to the
product design; no callback name is inferred from its English description.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import Literal

from living_artifacts_model import AFFIX_IDS, CURSE_IDS, FEEDING_XP, LIVING_NAME_PREFIX, PERSONAL_TYPES, Language, SourcePatch

PERSONAL_SLOTS = PERSONAL_TYPES
AFFIX_COUNT = len(AFFIX_IDS)
CURSE_COUNT = len(CURSE_IDS)


def _block(name: str, body: str) -> str:
    return f"{name} = {{\n" + "\n".join("\t" + line if line else "" for line in dedent(body).strip().splitlines()) + "\n}\n"


def _set(name: str, value: str | int) -> str:
    return f"set_variable = {{ name = xalw_{name} value = {value} }}"


def _change(name: str, value: str | int) -> str:
    return f"change_variable = {{ name = xalw_{name} add = {value} }}"


def _optional_condition(fields: tuple[str, ...], condition: str, *, missing_allowed: bool = False) -> str:
    """Preserve missing-value semantics behind a real lazy trigger boundary."""
    present = " ".join(f"has_variable = {field}" for field in fields)
    return _block("AND", _block("trigger_if", _block("limit", present) + condition)
                  + _block("trigger_else", "always = " + ("yes" if missing_allowed else "no")))


def _not_duplicate(kind: Literal["affix", "curse"], candidate: int) -> str:
    slots = 6 if kind == "affix" else 2
    return "NOR = { " + " ".join(f"var:xalw_{kind}_{slot} ?= {candidate}" for slot in range(1, slots + 1)) + " }"


def get_core_patches(game: Path) -> tuple[SourcePatch, ...]:
    """Return reviewed vanilla projections, currently none.

    InventoryView equip/unequip methods are native functions, not overridable
    scripted effects. A source patch is only added after a real source anchor
    is established; an empty list does not certify immediate dynamic refresh.
    """
    if not game.is_dir():
        raise ValueError("Game source directory does not exist")
    return ()


def _growth_choices(low_level: bool) -> str:
    weights = (45, 25, 20, 10) if low_level else (25, 20, 30, 25)
    effects = ("xalw_add_affix_effect", "xalw_upgrade_affix_effect", "xalw_mutate_affix_effect", "xalw_grow_curse_effect")
    return "\n".join(_block(str(weight), f"{effect} = yes") for weight, effect in zip(weights, effects, strict=True))


def _feeding_diet_match() -> str:
    return "OR = { " + " ".join(
        f"AND = {{ scope:xalw_artifact.var:xalw_diet ?= flag:{slot} scope:xalw_material = {{ artifact_slot_type = {slot} }} }}"
        for slot in PERSONAL_SLOTS
    ) + " }"


def render_core_triggers() -> str:
    """Return independently named predicates shared with content scripts."""
    personal = "OR = { " + " ".join(f"artifact_slot_type = {slot}" for slot in PERSONAL_SLOTS) + " }"
    return "\n".join([
        _block("xalw_is_personal_trigger", personal),
        _block("xalw_is_living_trigger", "var:xalw_schema_version ?= 2\nvar:xalw_kind ?= flag:living"),
        _block("xalw_is_growth_suppressed_trigger", _optional_condition(("xalw_growth_suppressed_until",), "var:xalw_growth_suppressed_until > current_date")),
        _block("xalw_can_renew_suppression_trigger", _optional_condition(("xalw_growth_suppressed_until",), """
            xalw_is_growth_suppressed_trigger = yes
            var:xalw_growth_suppressed_until <= xalw_renewal_window_ends_value
        """)),
        _block("xalw_owner_needs_monthly_trigger", """
            OR = {
                any_character_artifact = { xalw_is_living_trigger = yes }
                any_character_artifact = { xalw_is_personal_trigger = yes NOT = { has_variable = xalw_schema_version } }
                AND = {
                    trigger_if = { limit = { has_variable = xalw_content_loan_periods } var:xalw_content_loan_periods > 0 }
                    trigger_else = { always = no }
                }
                AND = {
                    trigger_if = { limit = { has_variable = xalw_content_loan_arrears } var:xalw_content_loan_arrears > 0 }
                    trigger_else = { always = no }
                }
            }
        """),
        _block("xalw_can_gain_xp_trigger", """
            xalw_is_living_trigger = yes
            xalw_is_personal_trigger = yes
            is_equipped = yes
            artifact_owner ?= { is_alive = yes }
            NOT = { xalw_is_growth_suppressed_trigger = yes }
        """),
        _block("xalw_is_safe_feed_material_trigger", """
            xalw_is_personal_trigger = yes
            is_unique = no
            var:xalw_schema_version ?= 2
            var:xalw_kind ?= flag:ordinary
            is_equipped = no
            has_none_of_variables = {
                name = xalw_keep
                name = 1025_treasure_map
                name = is_tribute_mission_artifact
                name = mandala_capital_05_unconfirmed_talisman
                name = artifact_prevent_transfer
                name = ungiftable
                name = banner_house
                name = banner_dynasty
                name = relic
                name = relic_religion
                name = historical_artifact
                name = artifact_succession_title
                name = pam_saint_relic_saint
            }
            NOT = { is_holy_relic_for = artifact_owner.faith }
        """),
    ])


def render_core_script_values() -> str:
    """Return values, including the one explicitly overridden vanilla AI hook."""
    month = "value = current_year\nmultiply = 12\n" + "\n".join(
        f"if = {{ limit = {{ current_month = {month} }} add = {month} }}" for month in range(1, 13)
    )
    adjustment = """
        value = 0
        if = {
            limit = { xalw_is_living_trigger = yes }
            add = 60
            add = { value = xalw_base_hunger_value multiply = -15 }
            if = { limit = { artifact_owner ?= { health < 4 } } add = { value = xalw_base_hunger_value multiply = -45 } }
    """
    for slot in range(1, 7):
        adjustment += f"\nif = {{ limit = {{ has_variable = xalw_affix_{slot} has_variable = xalw_affix_rank_{slot} }} add = {{ value = var:xalw_affix_rank_{slot} multiply = 12 }} }}"
    for slot in (1, 2):
        adjustment += f"\nif = {{ limit = {{ has_variable = xalw_curse_{slot} has_variable = xalw_curse_rank_{slot} }} add = {{ value = var:xalw_curse_rank_{slot} multiply = -30 }} }}"
        adjustment += f"\nif = {{ limit = {{ has_variable = xalw_curse_{slot} has_variable = xalw_curse_rank_{slot} var:xalw_curse_{slot} ?= 1 }} add = {{ value = var:xalw_curse_rank_{slot} multiply = -45 }} }}"
        adjustment += f"\nif = {{ limit = {{ var:xalw_curse_{slot} ?= 2 artifact_owner ?= {{ gold < 100 }} }} add = -300 }}"
    adjustment += "\nif = { limit = { artifact_owner ?= { has_trait = brave } } add = 20 }\nif = { limit = { artifact_owner ?= { has_trait = craven } } add = -20 }\n}"
    ai = """
        value = 0
        if = {
            limit = { scope:artifact = { has_variable = cursed_artifact } }
            add = -10000
        }
        if = {
            limit = { scope:artifact = { xalw_is_living_trigger = yes } }
            add = scope:artifact.xalw_ai_living_adjustment_value
        }
    """
    return "\n".join([
        _block("xalw_current_month_value", month),
        _block("xalw_next_level_xp_value", "value = var:xalw_level\nmultiply = 100"),
        _block("xalw_suppression_cost_value", "value = 20\nadd = { value = var:xalw_level multiply = 5 }\nadd = { value = var:xalw_suppression_chain multiply = 20 }"),
        _block("xalw_base_hunger_value", "value = var:xalw_level\nsubtract = 10\nmin = 0\nmax = 5"),
        _block("xalw_actual_hunger_value", """
            value = xalw_base_hunger_value
            if = { limit = {
                trigger_if = { limit = { has_variable = xalw_appeased_until } var:xalw_appeased_until > current_date }
                trigger_else = { always = no }
            } subtract = 1 }
            min = 0
            if = { limit = { xalw_is_growth_suppressed_trigger = yes } add = 1 }
            max = 5
        """),
        _block("xalw_appease_cost_value", "value = xalw_base_hunger_value\nmultiply = 25"),
        _block("xalw_suppression_remaining_days_value", "value = 0\nif = { limit = { xalw_is_growth_suppressed_trigger = yes } add = var:xalw_growth_suppressed_until subtract = current_date }"),
        _block("xalw_suppression_timer_sequence_value", "value = 0\nif = { limit = { has_variable = xalw_suppression_timer_sequence } add = var:xalw_suppression_timer_sequence }"),
        _block("xalw_renewal_window_ends_value", "value = current_date\nadd = 30"),
        _block("xalw_feed_base_xp_value", "value = 0\n" + "\n".join(
            f"{'if' if index == 0 else 'else_if'} = {{ limit = {{ rarity = {rarity} }} add = {experience} }}"
            for index, (rarity, experience) in enumerate(FEEDING_XP.items())
        )),
        _block("xalw_selected_feed_xp_value", "value = scope:xalw_material.xalw_feed_base_xp_value\nif = { limit = { " + _feeding_diet_match() + " } multiply = 1.25 }\nfloor = yes"),
        _block("xalw_ai_living_adjustment_value", adjustment),
        _block("xalw_ai_equipment_value", """
            value = rarity_level
            multiply = 100
            if = { limit = { has_variable = quality } add = var:quality }
            if = { limit = { has_variable = wealth } add = var:wealth }
            add = { value = artifact_durability multiply = 0.01 }
            add = xalw_ai_living_adjustment_value
            if = { limit = { has_variable = cursed_artifact } add = -10000 }
        """),
        _block("artifact_ai_will_equip_score", ai),
    ])


def _render_affix_effects() -> str:
    candidate_entries: list[str] = []
    for affix in range(1, AFFIX_COUNT + 1):
        personality = (affix - 1) % 6 + 1
        diet = PERSONAL_SLOTS[(affix - 1) % len(PERSONAL_SLOTS)]
        candidate_entries.append(_block("1", f"""
            trigger = {{ {_not_duplicate('affix', affix)} }}
            modifier = {{
                factor = 2
                var:xalw_weighted_roll ?= yes
                OR = {{
                    var:xalw_personality ?= {personality}
                    var:xalw_diet ?= flag:{diet}
                    var:xalw_feeding_imprint ?= flag:{diet}
                }}
            }}
            {_set('candidate_affix', affix)}
        """))
    candidate = _block("xalw_roll_affix_effect", "random_list = {\n40 = { remove_variable = xalw_weighted_roll }\n60 = { " + _set("weighted_roll", "yes") + " }\n}\nrandom_list = {\n" + "\n".join(candidate_entries) + "\n}\nremove_variable = xalw_weighted_roll")
    insert: list[str] = []
    for slot in range(1, 7):
        insert.append(_block("if" if slot == 1 else "else_if", f"""
            limit = {{ NOT = {{ has_variable = xalw_affix_{slot} }} }}
            xalw_roll_affix_effect = yes
            {_set(f'affix_{slot}', 'var:xalw_candidate_affix')}
            {_set(f'affix_rank_{slot}', 1)}
        """))
    insert.append("else = { xalw_mutate_affix_effect = yes }")
    mutation_entries: list[str] = []
    for slot in range(1, 7):
        mutation_entries.append(_block("1", f"""
            trigger = {{
                has_variable = xalw_affix_{slot}
                OR = {{
                    NOT = {{ has_variable = xalw_content_preferred_mutation_slot }}
                    var:xalw_content_preferred_mutation_slot ?= {slot}
                }}
            }}
            xalw_roll_affix_effect = yes
            {_set(f'affix_{slot}', 'var:xalw_candidate_affix')}
            random_list = {{
                60 = {{ {_set(f'affix_rank_{slot}', 1)} }}
                30 = {{ {_set(f'affix_rank_{slot}', 2)} }}
                10 = {{ {_set(f'affix_rank_{slot}', 3)} }}
            }}
        """))
    upgrade_entries: list[str] = []
    for slot in range(1, 7):
        condition = _optional_condition((f"xalw_affix_{slot}", f"xalw_affix_rank_{slot}"), f"var:xalw_affix_rank_{slot} < 3")
        upgrade_entries.append(_block("1", f"""
            trigger = {{ {condition} }}
            {_change(f'affix_rank_{slot}', 1)}
        """))
    eligible = "OR = { " + " ".join(_optional_condition((f"xalw_affix_{slot}", f"xalw_affix_rank_{slot}"), f"var:xalw_affix_rank_{slot} < 3") for slot in range(1, 7)) + " }"
    return "\n".join([
        candidate,
        _block("xalw_add_affix_effect", "\n".join(insert) + "\nremove_variable = xalw_candidate_affix"),
        _block("xalw_mutate_affix_effect", "xalw_content_prepare_mutation_effect = yes\nrandom_list = {\n" + "\n".join(mutation_entries) + "\n}\nrandom = { chance = 10 xalw_roll_personality_effect = yes }\nremove_variable = xalw_candidate_affix\nremove_variable = xalw_content_preferred_mutation_slot"),
        _block("xalw_upgrade_affix_effect", f"if = {{ limit = {{ {eligible} }} random_list = {{\n" + "\n".join(upgrade_entries) + "\n} }\nelse = { xalw_mutate_affix_effect = yes }"),
    ])


def _render_curse_effects() -> str:
    candidate = "random_list = {\n" + "\n".join(
        _block("1", f"trigger = {{ {_not_duplicate('curse', curse)} }}\n{_set('candidate_curse', curse)}")
        for curse in range(1, CURSE_COUNT + 1)
    ) + "\n}"
    match: list[str] = []
    for slot in (1, 2):
        match.append(_block("if" if slot == 1 else "else_if", f"""
            limit = {{ var:xalw_curse_{slot} ?= var:xalw_candidate_curse }}
            if = {{
                limit = {{ var:xalw_curse_rank_{slot} < 3 }}
                {_change(f'curse_rank_{slot}', 1)}
            }}
            else = {{
                xalw_roll_different_curse_effect = yes
                {_set(f'curse_{slot}', 'var:xalw_candidate_curse')}
            }}
        """))
    for slot in (1, 2):
        match.append(_block("else_if", f"""
            limit = {{ NOT = {{ has_variable = xalw_curse_{slot} }} }}
            {_set(f'curse_{slot}', 'var:xalw_candidate_curse')}
            {_set(f'curse_rank_{slot}', 1)}
        """))
    replacement = "random_list = {\n" + "\n".join(
        _block("1", f"{_set(f'curse_{slot}', 'var:xalw_candidate_curse')}\n# Keep this slot's rank unchanged.") for slot in (1, 2)
    ) + "\n}"
    match.append(_block("else", replacement))
    raw_candidate = "random_list = {\n" + "\n".join(_block("1", _set("candidate_curse", curse)) for curse in range(1, CURSE_COUNT + 1)) + "\n}"
    return "\n".join([
        _block("xalw_roll_different_curse_effect", candidate),
        _block("xalw_grow_curse_effect", raw_candidate + "\n" + "\n".join(match) + "\nremove_variable = xalw_candidate_curse"),
    ])


def render_core_effects() -> str:
    """Return lifecycle, growth, ownership, feeding and AI native effects."""
    effects: list[str] = [_render_affix_effects(), _render_curse_effects()]
    effects.append(_block("xalw_roll_personality_effect", "random_list = {\n" + "\n".join(_block("1", _set("personality", value)) for value in range(1, 7)) + "\n}"))
    effects.append(_block("xalw_roll_diet_effect", "random_list = {\n" + "\n".join(_block("1", _set("diet", f"flag:{slot}")) for slot in PERSONAL_SLOTS) + "\n}"))
    # Vanilla sanctify_artifact_flavor_effect resolves GetNameNoTooltip before
    # replacing the stored name. The persisted marker makes refresh/transfer
    # idempotent and also migrates living artifacts from earlier saves.
    effects.append(_block("xalw_ensure_star_name_effect", """
        if = {
            limit = { xalw_is_living_trigger = yes NOT = { has_variable = xalw_star_named } }
            save_scope_as = xalw_named_artifact
            set_artifact_name = xalw_star_name
            set_variable = { name = xalw_star_named value = yes }
        }
    """))
    initial: list[str] = [_set("kind", "flag:living")]
    for key, value in (("level", 1), ("xp_in_level", 0), ("pending_xp", 0), ("growth_sequence", 0), ("last_notified_sequence", 0), ("resonance", 20), ("suppression_chain", 0), ("unsuppressed_equipped_months", 0)):
        initial.append(_set(key, value))
    initial.extend([
        _set("attuned_character", "artifact_owner"),
        _set("last_settled_month", "xalw_current_month_value"),
        "xalw_roll_personality_effect = yes", "xalw_roll_diet_effect = yes", "xalw_add_affix_effect = yes",
        "xalw_refresh_artifact_effect = yes",
        "save_scope_as = xalw_artifact\nartifact_owner ?= { if = { limit = { is_ai = no } send_interface_toast = { type = event_toast_effect_good title = xalw_awakened_title left_icon = this right_icon = scope:xalw_artifact custom_tooltip = xalw_awakened_text } } }",
    ])
    effects.append(_block("xalw_awaken_artifact_effect", "\n".join(initial)))
    effects.append(_block("xalw_discover_artifact_effect", """
        if = {
            limit = { xalw_is_personal_trigger = yes NOT = { has_variable = xalw_schema_version } }
            set_variable = { name = xalw_schema_version value = 2 }
            set_variable = { name = xalw_kind value = flag:ordinary }
            if = { limit = { has_game_rule = xalw_awakening_none } }
            else_if = { limit = { has_game_rule = xalw_awakening_rare } random = { chance = 1 xalw_awaken_artifact_effect = yes } }
            else_if = { limit = { has_game_rule = xalw_awakening_frequent } random = { chance = 15 xalw_awaken_artifact_effect = yes } }
            else = { random = { chance = 5 xalw_awaken_artifact_effect = yes } }
        }
    """))
    effects.append(_block("xalw_discover_owner_effect", """
        save_scope_as = owner
        set_variable = { name = xalw_discovery_budget value = 50 }
        every_character_artifact = {
            limit = {
                xalw_is_personal_trigger = yes
                NOT = { has_variable = xalw_schema_version }
                scope:owner.var:xalw_discovery_budget > 0
            }
            xalw_discover_artifact_effect = yes
            scope:owner = { change_variable = { name = xalw_discovery_budget add = -1 } }
        }
        remove_variable = xalw_discovery_budget
        if = {
            limit = { xalw_owner_needs_monthly_trigger = yes NOT = { has_variable = xalw_monthly_chain } }
            set_variable = { name = xalw_monthly_chain value = yes }
            set_variable = { name = xalw_last_owner_month value = xalw_current_month_value }
            trigger_event = { id = xalw.1 days = 1 }
            if = { limit = { is_ai = yes any_character_artifact = { xalw_is_living_trigger = yes } } xalw_queue_ai_review_effect = yes }
        }
    """))
    effects.append(_block("xalw_settle_xp_effect", """
        if = {
            limit = { xalw_can_gain_xp_trigger = yes var:xalw_pending_xp > 0 }
            change_variable = { name = xalw_xp_in_level add = var:xalw_pending_xp }
            set_variable = { name = xalw_pending_xp value = 0 }
            while = {
                limit = { var:xalw_xp_in_level >= xalw_next_level_xp_value }
                change_variable = { name = xalw_xp_in_level subtract = xalw_next_level_xp_value }
                change_variable = { name = xalw_level add = 1 }
                change_variable = { name = xalw_growth_sequence add = 1 }
                if = {
                    limit = { var:xalw_level <= 10 }
                    random_list = {
    """ + _growth_choices(True) + "\n}\n} else = { random_list = {\n" + _growth_choices(False) + "\n} }\n}\nxalw_refresh_artifact_effect = yes\nxalw_notify_growth_effect = yes\n}\n"))
    effects.append(_block("xalw_notify_growth_effect", """
        if = {
            limit = { var:xalw_growth_sequence > var:xalw_last_notified_sequence }
            set_variable = { name = xalw_last_notified_sequence value = var:xalw_growth_sequence }
            save_scope_as = xalw_artifact
            artifact_owner ?= {
                if = {
                    limit = { is_ai = no }
                    send_interface_toast = {
                        type = event_toast_effect_neutral
                        title = xalw_growth_title
                        left_icon = this
                        right_icon = scope:xalw_artifact
                        custom_tooltip = xalw_growth_text
                    }
                }
            }
        }
    """))
    refresh_hunger = "\n".join(f"remove_artifact_modifier = xalw_hunger_{points}_modifier" for points in range(1, 6))
    refresh_hunger += "\n" + "\n".join(f"if = {{ limit = {{ NOT = {{ has_game_rule = xalw_backlash_mild }} xalw_actual_hunger_value = {points} }} add_artifact_modifier = xalw_hunger_{points}_modifier }}" for points in range(1, 6))
    effects.append(_block("xalw_refresh_artifact_effect", "xalw_ensure_star_name_effect = yes\nxalw_content_refresh_artifact_effect = yes\n" + refresh_hunger))
    effects.append(_block("xalw_artifact_monthly_effect", """
        xalw_ensure_star_name_effect = yes
        if = {
            limit = { xalw_is_living_trigger = yes var:xalw_last_settled_month != xalw_current_month_value }
            set_variable = { name = xalw_last_settled_month value = xalw_current_month_value }
            if = {
                limit = { is_equipped = yes xalw_is_personal_trigger = yes }
                change_variable = { name = xalw_resonance add = 5 }
                if = { limit = { var:xalw_resonance > 100 } set_variable = { name = xalw_resonance value = 100 } }
                if = {
                    limit = { xalw_can_gain_xp_trigger = yes }
                    change_variable = { name = xalw_pending_xp add = 8 }
                    xalw_settle_xp_effect = yes
                    change_variable = { name = xalw_unsuppressed_equipped_months add = 1 }
                    if = {
                        limit = { var:xalw_unsuppressed_equipped_months >= 6 }
                        set_variable = { name = xalw_unsuppressed_equipped_months value = 6 }
                        set_variable = { name = xalw_suppression_chain value = 0 }
                    }
                }
                if = {
                    limit = { NOT = { has_variable = xalw_seen_equipped } }
                    set_variable = { name = xalw_seen_equipped value = yes }
                    xalw_content_on_equip_effect = yes
                }
                if = {
                    limit = { OR = { current_month = 1 current_month = 4 current_month = 7 current_month = 10 } }
                    save_scope_value_as = { name = xalw_quarterly_hunger_stress value = { value = xalw_actual_hunger_value multiply = 2 } }
                    artifact_owner = { add_stress = scope:xalw_quarterly_hunger_stress }
                }
            }
            else = { remove_variable = xalw_seen_equipped }
        }
    """))
    effects.append(_block("xalw_owner_monthly_effect", """
        save_scope_as = owner
        xalw_discover_owner_effect = yes
        every_character_artifact = { limit = { xalw_is_living_trigger = yes } xalw_artifact_monthly_effect = yes }
        xalw_content_monthly_effect = yes
        if = { limit = { is_ai = yes } xalw_ai_cultivate_effect = yes }
    """))
    effects.append(_block("xalw_owner_changed_effect", """
        xalw_discover_artifact_effect = yes
        if = {
            limit = { xalw_is_living_trigger = yes }
            remove_variable = xalw_seen_equipped
            if = {
                limit = { exists = scope:owner }
                set_variable = { name = xalw_attuned_character value = scope:owner }
                set_variable = { name = xalw_resonance value = 20 }
            }
            else = {
                remove_variable = xalw_attuned_character
                set_variable = { name = xalw_resonance value = 0 }
            }
            xalw_content_on_owner_changed_effect = yes
            xalw_refresh_artifact_effect = yes
        }
        scope:owner ?= {
            xalw_discover_owner_effect = yes
            if = { limit = { is_ai = yes any_character_artifact = { xalw_is_living_trigger = yes } } xalw_queue_ai_review_effect = yes }
        }
    """))
    effects.extend(_render_management_effects())
    return "\n".join(effects)


def _render_management_effects() -> list[str]:
    effects: list[str] = []
    effects.append(_block("xalw_choose_feed_rarity_effect", """
        save_scope_as = owner
        if = {
            limit = {
                scope:xalw_artifact ?= { xalw_can_gain_xp_trigger = yes artifact_owner = root }
                any_character_artifact = { xalw_is_safe_feed_material_trigger = yes rarity = $RARITY$ }
            }
            ordered_character_artifact = {
                limit = { xalw_is_safe_feed_material_trigger = yes rarity = $RARITY$ }
                order_by = { value = artifact_durability multiply = -1 }
                max = 1
                save_scope_as = xalw_material
            }
            trigger_event = xalw.11
        }
    """))
    ai_equipment: list[str] = []
    for slot in PERSONAL_SLOTS:
        ai_equipment.append(f"""
            ordered_character_artifact = {{
                limit = {{
                    artifact_slot_type = {slot}
                    save_temporary_scope_as = xalw_ai_candidate
                    scope:owner = {{ can_equip_artifact = scope:xalw_ai_candidate can_benefit_from_artifact = scope:xalw_ai_candidate }}
                }}
                order_by = xalw_ai_equipment_value
                if = {{
                    limit = {{ is_equipped = no xalw_ai_equipment_value > 0 }}
                    equip_artifact_to_owner_replace = yes
                }}
            }}
        """)
    ai_reserve: list[str] = [
        "every_character_artifact = { remove_variable = xalw_ai_keep }",
    ]
    for slot in PERSONAL_SLOTS:
        for _ in range(4 if slot == "miscellaneous" else 1):
            ai_reserve.append(f"""
                ordered_character_artifact = {{
                    limit = {{
                        artifact_slot_type = {slot}
                        is_equipped = no
                        NOT = {{ has_variable = xalw_ai_keep }}
                    }}
                    order_by = {{ value = rarity_level multiply = 1000 add = artifact_durability }}
                    set_variable = {{ name = xalw_ai_keep value = yes }}
                }}
            """)
    ai_materials: list[str] = []
    for slot in PERSONAL_SLOTS:
        ai_materials.append(f"""
            every_character_artifact = {{
                limit = {{
                    artifact_slot_type = {slot}
                    xalw_is_safe_feed_material_trigger = yes
                    NOT = {{ has_variable = xalw_ai_keep }}
                    artifact_owner = {{ any_equipped_character_artifact = {{ artifact_slot_type = {slot} }} }}
                }}
                add_to_list = xalw_ai_feed_materials
            }}
        """)
    # Called in owner scope, with scope:xalw_artifact and scope:xalw_material.
    # The destructive effect runs in owner scope: never dereference a destroyed
    # artifact by continuing an effect rooted on that artifact.
    imprint = "\n".join(
        f"if = {{ limit = {{ scope:xalw_material = {{ artifact_slot_type = {slot} }} }} scope:xalw_artifact = {{ set_variable = {{ name = xalw_pending_feed_imprint value = flag:{slot} }} }} }}" for slot in PERSONAL_SLOTS
    )
    effects.append(_block("xalw_feed_material_effect", f"""
        if = {{
            limit = {{
                scope:xalw_artifact ?= {{ xalw_can_gain_xp_trigger = yes artifact_owner = scope:owner }}
                scope:xalw_material ?= {{ xalw_is_safe_feed_material_trigger = yes artifact_owner = scope:owner }}
                scope:xalw_material != scope:xalw_artifact
            }}
            save_scope_value_as = {{ name = xalw_feed_xp value = xalw_selected_feed_xp_value }}
            {imprint}
            destroy_artifact = scope:xalw_material
            if = {{
                limit = {{ NOT = {{ exists = scope:xalw_material }} }}
                scope:xalw_artifact = {{
                    set_variable = {{ name = xalw_feeding_imprint value = var:xalw_pending_feed_imprint days = 90 }}
                    change_variable = {{ name = xalw_pending_xp add = scope:xalw_feed_xp }}
                    xalw_settle_xp_effect = yes
                }}
            }}
            scope:xalw_artifact = {{ remove_variable = xalw_pending_feed_imprint }}
        }}
    """))
    effects.append(_block("xalw_train_effect", """
        save_scope_as = owner
        if = {
            limit = {
                prestige >= 50
                NOT = { has_variable = xalw_training_cooldown }
                scope:xalw_artifact ?= { xalw_can_gain_xp_trigger = yes artifact_owner = scope:owner }
            }
            add_prestige = -50
            add_stress = 10
            set_variable = { name = xalw_training_cooldown value = yes days = 365 }
            scope:xalw_artifact = { change_variable = { name = xalw_pending_xp add = 25 } xalw_settle_xp_effect = yes }
        }
    """))
    effects.append(_block("xalw_suppress_effect", """
        save_scope_as = owner
        if = {
            limit = {
                prestige >= 50
                scope:xalw_artifact ?= {
                    xalw_is_living_trigger = yes artifact_owner = scope:owner
                    OR = {
                        NOT = { xalw_is_growth_suppressed_trigger = yes }
                        xalw_can_renew_suppression_trigger = yes
                    }
                }
                gold >= scope:xalw_artifact.xalw_suppression_cost_value
            }
            remove_short_term_gold = scope:xalw_artifact.xalw_suppression_cost_value
            add_prestige = -50
            add_stress = 10
            scope:xalw_artifact = {
                if = {
                    limit = { xalw_is_growth_suppressed_trigger = yes }
                    change_variable = { name = xalw_growth_suppressed_until add = 90 }
                }
                else = { xalw_begin_suppression_timer_effect = yes }
                change_variable = { name = xalw_suppression_chain add = 1 }
                set_variable = { name = xalw_unsuppressed_equipped_months value = 0 }
                xalw_refresh_artifact_effect = yes
            }
        }
    """))
    effects.append(_block("xalw_begin_suppression_timer_effect", """
        # Vanilla 00_custom_loc_effects explicitly states date arithmetic is days.
        # Keep the single deadline on the artifact; ownership never resets it.
        set_variable = { name = xalw_growth_suppressed_until value = { value = current_date add = 90 } }
        if = { limit = { NOT = { has_variable = xalw_suppression_timer_sequence } } set_variable = { name = xalw_suppression_timer_sequence value = 0 } }
        change_variable = { name = xalw_suppression_timer_sequence add = 1 }
        save_scope_value_as = { name = xalw_suppression_timer_sequence value = xalw_suppression_timer_sequence_value }
        trigger_event = { id = xalw.4 days = 90 }
    """))
    effects.append(_block("xalw_appease_effect", """
        save_scope_as = owner
        if = {
            limit = {
                scope:xalw_artifact ?= {
                    xalw_is_living_trigger = yes artifact_owner = scope:owner
                    xalw_base_hunger_value > 0
                    trigger_if = { limit = { has_variable = xalw_appease_available_on } var:xalw_appease_available_on <= current_date }
                    trigger_else = { always = yes }
                }
                gold >= scope:xalw_artifact.xalw_appease_cost_value
            }
            remove_short_term_gold = scope:xalw_artifact.xalw_appease_cost_value
            add_stress = 10
            scope:xalw_artifact = {
                set_variable = { name = xalw_appeased_until value = { value = current_date add = 365 } }
                set_variable = { name = xalw_appease_available_on value = { value = current_date add = 365 } }
                trigger_event = { id = xalw.5 days = 365 }
                xalw_refresh_artifact_effect = yes
            }
        }
    """))
    effects.append(_block("xalw_queue_ai_review_effect", """
        # Defer out of the artifact ownership callback before any destruction.
        # A new acquisition can queue another review as soon as this one ran.
        if = {
            limit = { NOT = { has_variable = xalw_ai_review_queued } }
            set_variable = { name = xalw_ai_review_queued value = yes }
            trigger_event = { id = xalw.2 days = 1 }
        }
    """))
    # Native eligibility, benefit and real score drive equipment selection. This
    # does not alter rarity, bypass can_benefit, or conjure feed material.
    effects.append(_block("xalw_ai_cultivate_effect", """
        save_scope_as = owner
    """ + "\n".join(ai_equipment) + """
        ordered_character_artifact = {
            limit = { xalw_can_gain_xp_trigger = yes }
            order_by = { value = var:xalw_level multiply = 10 add = rarity_level }
            save_scope_as = xalw_artifact
        }
        if = {
            limit = { scope:xalw_artifact ?= { artifact_owner = scope:owner xalw_can_gain_xp_trigger = yes } }
    """ + "\n".join(ai_reserve + ai_materials) + """
            every_in_list = {
                list = xalw_ai_feed_materials
                save_scope_as = xalw_material
                scope:owner = { xalw_feed_material_effect = yes }
            }
            if = { limit = { prestige >= 200 stress < 70 } xalw_train_effect = yes }
            if = {
                limit = { gold >= 300 prestige >= 100 health < 4 scope:xalw_artifact.var:xalw_level >= 10 }
                xalw_suppress_effect = yes
            }
            if = {
                limit = { gold >= 300 health < 4 scope:xalw_artifact.xalw_base_hunger_value > 0 }
                xalw_appease_effect = yes
            }
        }
    """))
    return effects


def render_core_on_actions() -> str:
    """Append child actions, preserving vanilla on_action effects."""
    return dedent("""
        on_game_start_after_lobby = { on_actions = { xalw_bootstrap_on_action } }
        random_yearly_everyone_pulse = { on_actions = { xalw_discovery_on_action } }
        on_artifact_changed_owner = { on_actions = { xalw_owner_changed_on_action } }
        xalw_bootstrap_on_action = {
            effect = {
                every_living_character = {
                    limit = { xalw_owner_needs_monthly_trigger = yes }
                    xalw_discover_owner_effect = yes
                }
            }
        }
        xalw_discovery_on_action = {
            trigger = { is_alive = yes has_any_artifact = yes }
            effect = { xalw_discover_owner_effect = yes }
        }
        xalw_owner_changed_on_action = { effect = { xalw_owner_changed_effect = yes } }
    """).strip() + "\n"


def render_core_events() -> str:
    """Return monthly timers and the native, read-after-commit management page."""
    feeding_options = "\n".join(_block("option", f"""
        name = xalw.10.feed_{rarity}
        trigger = {{
            scope:xalw_artifact = {{ xalw_can_gain_xp_trigger = yes }}
            any_character_artifact = {{ xalw_is_safe_feed_material_trigger = yes rarity = {rarity} }}
        }}
        xalw_choose_feed_rarity_effect = {{ RARITY = {rarity} }}
    """) for rarity in FEEDING_XP)
    return dedent("""
        namespace = xalw
        xalw.1 = {
            type = character_event
            hidden = yes
            trigger = { is_alive = yes }
            immediate = {
                if = {
                    limit = { var:xalw_last_owner_month != xalw_current_month_value }
                    set_variable = { name = xalw_last_owner_month value = xalw_current_month_value }
                    xalw_owner_monthly_effect = yes
                }
                if = {
                    limit = { xalw_owner_needs_monthly_trigger = yes }
                    trigger_event = { id = xalw.1 days = 1 }
                }
                else = { remove_variable = xalw_monthly_chain }
            }
        }
        xalw.2 = {
            type = character_event
            hidden = yes
            trigger = { is_alive = yes is_ai = yes }
            immediate = { remove_variable = xalw_ai_review_queued xalw_ai_cultivate_effect = yes }
        }
        xalw.4 = {
            scope = artifact
            hidden = yes
            trigger = { var:xalw_suppression_timer_sequence = scope:xalw_suppression_timer_sequence }
            immediate = {
                if = {
                    limit = { xalw_is_growth_suppressed_trigger = yes }
                    trigger_event = { id = xalw.4 days = xalw_suppression_remaining_days_value }
                }
                else = {
                    remove_variable = xalw_growth_suppressed_until
                }
                xalw_refresh_artifact_effect = yes
            }
        }
        xalw.5 = {
            scope = artifact
            hidden = yes
            immediate = {
                if = { limit = {
                    trigger_if = { limit = { has_variable = xalw_appeased_until } var:xalw_appeased_until <= current_date }
                    trigger_else = { always = no }
                } remove_variable = xalw_appeased_until }
                xalw_refresh_artifact_effect = yes
            }
        }
        xalw.10 = {
            type = character_event
            title = xalw.10.t
            desc = xalw.10.desc
            theme = learning
            override_background = { reference = throne_room }
            trigger = { scope:xalw_artifact ?= { xalw_is_living_trigger = yes artifact_owner = root } }
            immediate = {
                set_variable = { name = xalw_selected_artifact value = scope:xalw_artifact }
                save_scope_as = owner
            }
            option = {
                name = xalw.10.feed
                custom_tooltip = xalw_feed_selector_help
            }
            __XALW_FEED_RARITY_OPTIONS__
            option = {
                name = xalw.10.train
                trigger = { scope:xalw_artifact = { xalw_can_gain_xp_trigger = yes } }
                show_as_unavailable = { OR = { prestige < 50 has_variable = xalw_training_cooldown } }
                xalw_train_effect = yes
            }
            option = {
                name = xalw.10.suppress
                trigger = { scope:xalw_artifact = { NOT = { xalw_is_growth_suppressed_trigger = yes } } }
                show_as_unavailable = { OR = { gold < scope:xalw_artifact.xalw_suppression_cost_value prestige < 50 } }
                xalw_suppress_effect = yes
            }
            option = {
                name = xalw.10.renew
                trigger = { scope:xalw_artifact = { xalw_can_renew_suppression_trigger = yes } }
                show_as_unavailable = { OR = { gold < scope:xalw_artifact.xalw_suppression_cost_value prestige < 50 } }
                xalw_suppress_effect = yes
            }
            option = {
                name = xalw.10.appease
                trigger = { scope:xalw_artifact = { xalw_base_hunger_value > 0
                    trigger_if = { limit = { has_variable = xalw_appease_available_on } var:xalw_appease_available_on <= current_date }
                    trigger_else = { always = yes }
                } }
                show_as_unavailable = { gold < scope:xalw_artifact.xalw_appease_cost_value }
                xalw_appease_effect = yes
            }
            option = { name = xalw.10.close }
        }
        xalw.11 = {
            type = character_event
            title = xalw.11.t
            desc = xalw.11.desc
            theme = learning
            trigger = {
                scope:xalw_artifact ?= { xalw_can_gain_xp_trigger = yes artifact_owner = root }
                scope:xalw_material ?= { xalw_is_safe_feed_material_trigger = yes artifact_owner = root }
            }
            immediate = { save_scope_as = owner }
            option = {
                name = xalw.11.confirm
                xalw_feed_material_effect = yes
                if = { limit = { scope:xalw_artifact ?= { xalw_is_living_trigger = yes artifact_owner = root } } trigger_event = xalw.10 }
            }
            option = {
                name = xalw.11.cancel
                if = { limit = { scope:xalw_artifact ?= { xalw_is_living_trigger = yes artifact_owner = root } } trigger_event = xalw.10 }
            }
        }
        xalw.12 = {
            type = character_event
            title = xalw.12.t
            desc = xalw.12.desc
            theme = learning
            immediate = {
                ordered_character_artifact = {
                    limit = { xalw_is_living_trigger = yes is_equipped = yes }
                    order_by = var:xalw_level
                    max = 1
                    save_scope_as = xalw_artifact
                }
            }
            option = {
                name = xalw.12.open
                trigger = { scope:xalw_artifact ?= { xalw_is_living_trigger = yes is_equipped = yes artifact_owner = root } }
                trigger_event = xalw.10
            }
            option = { name = xalw.10.close }
        }
    """).strip().replace("__XALW_FEED_RARITY_OPTIONS__", feeding_options) + "\n"


def render_core_decisions() -> str:
    """Return the small entry decision; artifact picking uses vanilla selectors."""
    return _block("xalw_manage_decision", """
        picture = { reference = "gfx/interface/illustrations/decisions/decision_smith.dds" }
        desc = xalw_manage_decision_desc
        selection_tooltip = xalw_manage_decision_tooltip
        confirm_text = xalw_manage_decision_confirm
        sort_order = 35
        ai_check_interval = 0
        is_shown = { is_ai = no }
        is_valid = { is_alive = yes }
        effect = { xalw_discover_owner_effect = yes trigger_event = xalw.12 }
        ai_will_do = { base = 0 }
    """)


def render_core_game_rules() -> str:
    """Return world-wide rules; changing awakening never freezes existing items."""
    return "\n".join([
        _block("xalw_awakening", """
            categories = { game_modes }
            default = xalw_awakening_normal
            xalw_awakening_none = { }
            xalw_awakening_rare = { }
            xalw_awakening_normal = { }
            xalw_awakening_frequent = { }
        """),
        _block("xalw_backlash", """
            categories = { game_modes }
            default = xalw_backlash_standard
            xalw_backlash_standard = { }
            xalw_backlash_mild = { }
        """),
    ])


def render_core_interactions() -> str:
    """Return self interactions with the game's exact artifact selector contract."""
    common = """
        category = interaction_category_friendly
        common_interaction = yes
        interface_priority = 90
        icon = artifact
        target_type = artifact
        target_filter = actor_artifacts
        show_all_targets = no
        ai_targets = { ai_recipients = self }
        ai_frequency = 0
        is_shown = { scope:recipient = scope:actor }
        auto_accept = yes
        ai_will_do = { base = 0 }
    """
    manage = common + """
        desc = xalw_manage_interaction_desc
        is_available = { any_character_artifact = { xalw_is_living_trigger = yes } }
        can_be_picked_artifact = { scope:target = { xalw_is_living_trigger = yes } }
        on_accept = {
            scope:target = { save_scope_as = xalw_artifact }
            scope:actor = { trigger_event = xalw.10 }
        }
    """
    feed = common + """
        desc = xalw_feed_interaction_desc
        is_available = { var:xalw_selected_artifact ?= { xalw_can_gain_xp_trigger = yes artifact_owner = prev } }
        can_be_picked_artifact = { scope:target = { xalw_is_safe_feed_material_trigger = yes } }
        on_accept = {
            scope:target = { save_scope_as = xalw_material }
            scope:actor = {
                var:xalw_selected_artifact = { save_scope_as = xalw_artifact }
                trigger_event = xalw.11
            }
        }
    """
    protect = common + """
        desc = xalw_keep_interaction_desc
        is_available = { has_any_artifact = yes }
        can_be_picked_artifact = { scope:target = { xalw_is_personal_trigger = yes } }
        on_accept = {
            scope:target = {
                if = { limit = { has_variable = xalw_keep } remove_variable = xalw_keep }
                else = { set_variable = { name = xalw_keep value = yes } }
            }
        }
    """
    return "\n".join([
        _block("xalw_manage_interaction", manage),
        _block("xalw_feed_interaction", feed),
        _block("xalw_keep_interaction", protect),
    ])


def render_core_modifiers() -> str:
    """Return only core hunger modifiers; content owns its own named modifiers."""
    return "\n".join(_block(f"xalw_hunger_{points}_modifier", f"health = {-0.1 * points:.1f}") for points in range(1, 6))


def render_core_localization(language: Language) -> dict[str, str]:
    """Return localized core text; reject an accidental unregistered language."""
    if language not in ("simp_chinese", "english"):
        raise ValueError(f"unsupported language: {language}")
    chinese = language == "simp_chinese"
    pairs: dict[str, tuple[str, str]] = {
        "xalw_star_name": (LIVING_NAME_PREFIX + "[xalw_named_artifact.GetNameNoTooltip]", LIVING_NAME_PREFIX + "[xalw_named_artifact.GetNameNoTooltip]"),
        "xalw_manage_decision": ("倾听活武器", "Listen to Living Artifacts"),
        "xalw_manage_decision_desc": ("有些宝物会呼吸、记忆，也会索取代价。查看活武器的状态与培养方法。", "Some treasures breathe, remember, and demand a price. Learn how to inspect and cultivate them."),
        "xalw_manage_decision_tooltip": ("打开活武器管理指引", "Open living artifact management guidance"),
        "xalw_manage_decision_confirm": ("听听它们的声音", "Listen"),
        "xalw_manage_interaction": ("管理活武器", "Manage Living Artifact"),
        "xalw_manage_interaction_desc": ("选择自己的活武器，查看其成长、异能、诅咒与培养选项。", "Choose your living artifact to inspect its growth, powers, curses, and cultivation options."),
        "xalw_feed_interaction": ("喂养选定的活武器", "Feed Selected Living Artifact"),
        "xalw_feed_interaction_desc": ("选择一件未装备、非活且未保留的个人装备作为食物。按实际四档稀有度给经验，无冷却。确认后销毁材料。", "Choose an unequipped, ordinary, unprotected personal artifact as food. Its actual rarity determines experience. No cooldown. Confirmation destroys the material."),
        "xalw_keep_interaction": ("切换喂养保护", "Toggle Feeding Protection"),
        "xalw_keep_interaction_desc": ("将个人装备标为保留，或解除保留；保留物品不会进入喂养清单。", "Mark a personal artifact as protected, or release that protection. Protected artifacts cannot be consumed."),
        "xalw_awakened_title": ("宝物睁开了眼睛", "A Treasure Opens Its Eyes"),
        "xalw_awakened_text": ("[xalw_artifact.GetName]已觉醒为活武器。装备时自动成长；卸下同时失去活武器效果并停止成长。", "[xalw_artifact.GetName] has awakened. It grows automatically while equipped; unequipping stops its growth and living effects."),
        "xalw_growth_title": ("活武器自行成长", "A Living Artifact Has Grown"),
        "xalw_growth_text": ("[xalw_artifact.GetName]已自动达到[xalw_artifact.MakeScope.Var('xalw_level').GetValue|0]级。新的异能或诅咒已经生效。", "[xalw_artifact.GetName] automatically reached level [xalw_artifact.MakeScope.Var('xalw_level').GetValue|0]. Its new powers or curses have already taken effect."),
        "xalw.10.t": ("[xalw_artifact.GetName]：活物的低语", "[xalw_artifact.GetName]: A Living Whisper"),
        "xalw.10.desc": ("等级：#V [xalw_artifact.MakeScope.Var('xalw_level').GetValue|0]#!　经验：#V [xalw_artifact.MakeScope.Var('xalw_xp_in_level').GetValue|0]#! / [xalw_artifact.MakeScope.ScriptValue('xalw_next_level_xp_value')|0]\\n共鸣：#V [xalw_artifact.MakeScope.Var('xalw_resonance').GetValue|0]#!/100\\n\\n[xalw_artifact.Custom('XalwAffixes')]\\n[xalw_artifact.Custom('XalwCurses')]\\n\\n装备时每月自动获得8经验。达到门槛就升级，无须确认。卸下免费停级，同时停止活武器持续效果。喂养无冷却。\\n镇压报价：[xalw_artifact.MakeScope.ScriptValue('xalw_suppression_cost_value')|0]金币、50威望、10压力；安抚报价：[xalw_artifact.MakeScope.ScriptValue('xalw_appease_cost_value')|0]金币、10压力。", "Level: #V [xalw_artifact.MakeScope.Var('xalw_level').GetValue|0]#!  XP: #V [xalw_artifact.MakeScope.Var('xalw_xp_in_level').GetValue|0]#! / [xalw_artifact.MakeScope.ScriptValue('xalw_next_level_xp_value')|0]\\nResonance: #V [xalw_artifact.MakeScope.Var('xalw_resonance').GetValue|0]#!/100\\n\\n[xalw_artifact.Custom('XalwAffixes')]\\n[xalw_artifact.Custom('XalwCurses')]\\n\\nEquipped artifacts gain 8 XP monthly and level automatically. Unequipping stops growth and ongoing effects. Feeding has no cooldown.\\nSuppression: [xalw_artifact.MakeScope.ScriptValue('xalw_suppression_cost_value')|0] gold, 50 prestige, 10 stress. Appeasement: [xalw_artifact.MakeScope.ScriptValue('xalw_appease_cost_value')|0] gold, 10 stress."),
        "xalw.10.feed": ("把它设为喂养目标", "Select it as the Feeding Target"),
        "xalw.10.feed_common": ("挑选一件普通装备喂养", "Choose Common Equipment as Food"),
        "xalw.10.feed_masterwork": ("挑选一件大师级装备喂养", "Choose Masterwork Equipment as Food"),
        "xalw.10.feed_famed": ("挑选一件名作级装备喂养", "Choose Famed Equipment as Food"),
        "xalw.10.feed_illustrious": ("挑选一件卓越级装备喂养", "Choose Illustrious Equipment as Food"),
        "xalw.12.open": ("倾听[xalw_artifact.GetName]", "Listen to [xalw_artifact.GetName]"),
        "xalw_feed_selector_help": ("已选定此物。右键自己的头像，使用“喂养选定的活武器”，再选择材料。材料销毁前可取消。", "Target selected. Right-click your portrait, choose Feed Selected Living Artifact, then choose its food. You may cancel before destruction."),
        "xalw.10.train": ("共鸣训练（50威望，10压力，+25经验）", "Resonance Training (50 prestige, 10 stress, +25 XP)"),
        "xalw.10.suppress": ("付费镇压成长三个月", "Pay to Suppress Growth for Three Months"),
        "xalw.10.renew": ("付费续镇90日", "Pay to Extend Suppression by 90 Days"),
        "xalw.10.appease": ("安抚基础饥渴365日", "Appease Base Hunger for 365 Days"),
        "xalw.10.close": ("我知道了", "Understood"),
        "xalw.11.t": ("喂养确认：材料将永久消失", "Feeding: The Material Will Be Destroyed"),
        "xalw.11.desc": ("将#V [xalw_material.GetName]#!喂给#V [xalw_artifact.GetName]#!？\\n\\n材料基础经验：[xalw_material.MakeScope.ScriptValue('xalw_feed_base_xp_value')|0]；符合食性再乘1.25。\\n材料真实销毁后经验立即到账，可能自动跨越多个等级并产生诅咒。喂养没有冷却；材料消费才是此处的选择，升级不会征求许可。", "Feed #V [xalw_material.GetName]#! to #V [xalw_artifact.GetName]#!?\\n\\nBase material XP: [xalw_material.MakeScope.ScriptValue('xalw_feed_base_xp_value')|0], multiplied by 1.25 if it matches the diet.\\nExperience arrives after actual destruction, immediately resolving every level and curse. Feeding has no cooldown. This choice authorizes material consumption; leveling requires no consent."),
        "xalw.11.confirm": ("让它吞下这件装备", "Let It Devour the Material"),
        "xalw.11.cancel": ("保留材料", "Keep the Material"),
        "xalw.12.t": ("活武器管理", "Living Artifact Management"),
        "xalw.12.desc": ("右键自己的头像，选择#V 管理活武器#!，使用原生宝物选择器挑选物品。\\n选定目标后可训练、付费镇压、安抚，也可用#V 喂养选定的活武器#!选择材料。\\n所有在世持有者，包括AI、男爵、无地廷臣与骑士，遵守相同成长与代价。\\n#warning 活武器装备时会自行成长；不查看通知也照常升级。卸下免费停级，同时失去活武器效果。#!", "Right-click your own portrait and choose #V Manage Living Artifact#! to select an artifact with the native picker.\\nThen train, pay for suppression, appease, or use #V Feed Selected Living Artifact#! to choose material.\\nLiving owners including AI, barons, unlanded courtiers, and knights share the same growth and costs.\\n#warning Equipped artifacts grow automatically, even without reading notices. Unequipping stops growth and living effects for free.#!"),
        "xalw_empty_affixes": ("异能：无", "Powers: none"),
        "xalw_empty_curses": ("诅咒：无", "Curses: none"),
    }
    result = {key: pair[0 if chinese else 1] for key, pair in pairs.items()}
    result["xalw.10.desc"] += (
        "\\n\\n下方四档喂养会挑选同稀有度中耐久最低的安全材料，先显示具体物品，再由你确认销毁。可取消并将不愿喂掉的物品设为保留；也可通过宝物自选交互精确挑选。"
        if chinese else
        "\\n\\nRarity feeding picks the safe material with the least durability in that rarity. Review the exact item before confirming destruction. Cancel and protect anything you want to keep, or use the artifact picker for a specific choice."
    )
    result["xalw.12.desc"] += (
        "\\n\\n下方可直接倾听一件已装备的活武器（优先等级最高者）；若要指定其他物品，仍可使用自己的宝物选择交互。"
        if chinese else
        "\\n\\nBelow, listen directly to an equipped living artifact, prioritizing the highest level. Use your artifact interaction to select another specific item."
    )
    result["xalw.10.suppress"] = "付费镇压成长90日" if chinese else "Pay to Suppress Growth for 90 Days"
    detail_line = (
        "性格：[xalw_artifact.Custom('XalwPersonality')]　食性：[xalw_artifact.Custom('XalwDiet')]\\n镇压剩余：[xalw_artifact.MakeScope.ScriptValue('xalw_suppression_remaining_days_value')|0]日\\n\\n"
        if chinese else
        "Personality: [xalw_artifact.Custom('XalwPersonality')]  Diet: [xalw_artifact.Custom('XalwDiet')]\\nSuppression remaining: [xalw_artifact.MakeScope.ScriptValue('xalw_suppression_remaining_days_value')|0] days\\n\\n"
    )
    result["xalw.10.desc"] = detail_line + result["xalw.10.desc"]
    result["xalw.11.desc"] = (
        "本次经验（已含食性）：#V [SCOPE.ScriptValue('xalw_selected_feed_xp_value')|0]#!\\n\\n"
        if chinese else
        "Experience including diet: #V [SCOPE.ScriptValue('xalw_selected_feed_xp_value')|0]#!\\n\\n"
    ) + result["xalw.11.desc"]
    personalities = (("护主", "Protective"), ("嗜战", "Warlike"), ("傲慢", "Proud"), ("贪婪", "Greedy"), ("好奇", "Curious"), ("阴郁", "Gloomy"))
    for number, names in enumerate(personalities, start=1):
        result[f"xalw_personality_{number}"] = names[0 if chinese else 1]
    for diet_slot, names in zip(PERSONAL_SLOTS, (("冠冕", "Crowns"), ("礼器", "Regalia"), ("甲胄", "Armor"), ("武器", "Weapons"), ("胸针", "Brooches"), ("饰品", "Trinkets"), ("私人日志", "Journals")), strict=True):
        result[f"xalw_diet_{diet_slot}"] = names[0 if chinese else 1]
    rules: dict[str, tuple[str, str]] = {
        "rule_xalw_awakening": ("活武器：新觉醒概率", "Living Artifacts: Awakening Chance"),
        "setting_xalw_awakening_none": ("关闭新觉醒（0%）", "No New Awakenings (0%)"),
        "setting_xalw_awakening_none_desc": ("新装备不再觉醒。已有活武器仍按正常规则成长。", "No new awakenings. Existing living artifacts continue to grow normally."),
        "setting_xalw_awakening_rare": ("罕见（1%）", "Rare (1%)"),
        "setting_xalw_awakening_rare_desc": ("每件合格个人装备首次发现时有1%概率觉醒，全世界同规则。", "Each eligible personal artifact has a 1% awakening chance on first discovery, for every owner."),
        "setting_xalw_awakening_normal": ("标准（5%）", "Standard (5%)"),
        "setting_xalw_awakening_normal_desc": ("每件合格个人装备首次发现时有5%概率觉醒，全世界同规则。", "Each eligible personal artifact has a 5% awakening chance on first discovery, for every owner."),
        "setting_xalw_awakening_frequent": ("常见（15%）", "Frequent (15%)"),
        "setting_xalw_awakening_frequent_desc": ("每件合格个人装备首次发现时有15%概率觉醒，全世界同规则。", "Each eligible personal artifact has a 15% awakening chance on first discovery, for every owner."),
        "rule_xalw_backlash": ("活武器：基础饥渴", "Living Artifacts: Base Hunger"),
        "setting_xalw_backlash_standard": ("标准", "Standard"),
        "setting_xalw_backlash_standard_desc": ("每件基础饥渴造成健康与季度压力代价。多件叠加；具体诅咒另算。", "Each artifact's base hunger costs health and quarterly stress. Multiple artifacts stack; curses add their own costs."),
        "setting_xalw_backlash_mild": ("温和", "Mild"),
        "setting_xalw_backlash_mild_desc": ("基础饥渴仅增加季度压力，不减少健康。具体诅咒不受减轻。", "Base hunger only adds quarterly stress. Curses remain fully active."),
    }
    result.update({key: pair[0 if chinese else 1] for key, pair in rules.items()})
    for points in range(1, 6):
        result[f"xalw_hunger_{points}_modifier"] = f"活武器饥渴（{points}）" if chinese else f"Living Hunger ({points})"
    # Nested custom localization composes all six ordered slots, rather than
    # returning only the first matching entry in the artifact's random loadout.
    result["xalw_affix_summary"] = "\\n".join(f"[ROOT.Artifact.Custom('XalwAffix{slot}')]" for slot in range(1, 7))
    result["xalw_curse_summary"] = "\\n".join(f"[ROOT.Artifact.Custom('XalwCurse{slot}')]" for slot in (1, 2))
    for kind, slots, count in (("affix", 6, AFFIX_COUNT), ("curse", 2, CURSE_COUNT)):
        for slot in range(1, slots + 1):
            result[f"xalw_{kind}_{slot}_empty"] = ""
            for item in range(1, count + 1):
                label = "异能" if kind == "affix" else "诅咒"
                result[f"xalw_{kind}_{slot}_{item}_line"] = f"{label if chinese else kind.title()}：$xalw_{kind}_{item}_name$（[ROOT.Artifact.MakeScope.Var('xalw_{kind}_rank_{slot}').GetValue|0]）\\n$xalw_{kind}_{item}_desc$"
    return result


def render_core_custom_localization() -> str:
    """Return artifact-scoped dynamic summaries without replacing vanilla GUI."""
    blocks = [
        _block("XalwAffixes", "type = artifact\ntext = { localization_key = xalw_affix_summary }"),
        _block("XalwCurses", "type = artifact\ntext = { localization_key = xalw_curse_summary }"),
    ]
    blocks.append(_block("XalwPersonality", "type = artifact\n" + "\n".join(
        f"text = {{ trigger = {{ var:xalw_personality ?= {number} }} localization_key = xalw_personality_{number} }}" for number in range(1, 7)
    )))
    blocks.append(_block("XalwDiet", "type = artifact\n" + "\n".join(
        f"text = {{ trigger = {{ var:xalw_diet ?= flag:{slot} }} localization_key = xalw_diet_{slot} }}" for slot in PERSONAL_SLOTS
    )))
    for kind, slots, count in (("affix", 6, AFFIX_COUNT), ("curse", 2, CURSE_COUNT)):
        for slot in range(1, slots + 1):
            entries = ["type = artifact"]
            for item in range(1, count + 1):
                entries.append(f"text = {{ trigger = {{ var:xalw_{kind}_{slot} ?= {item} }} localization_key = xalw_{kind}_{slot}_{item}_line }}")
            entries.append(f"text = {{ fallback = yes localization_key = xalw_{kind}_{slot}_empty }}")
            blocks.append(_block(f"Xalw{kind.title()}{slot}", "\n".join(entries)))
    return "\n".join(blocks)


def render_fixture_effects() -> str:
    """Return initial-state producers for an external acceptance fixture only.

    These helpers create real artifacts and native equipment/material input.
    They never assign a post-action level, payment, destroyed state, or PASS.
    The caller selects existing baron/courtier scopes from a native snapshot;
    the fixture does not invent NPC titles or pretend an AI action occurred.
    """
    effects: list[str] = []
    for rarity, score in (("common", 10), ("masterwork", 40), ("famed", 75), ("illustrious", 100)):
        effects.append(_block(f"xalw_test_create_{rarity}_material_effect", f"""
            create_artifact = {{
                name = xalw_test_material_{rarity}_name
                description = xalw_test_material_description
                type = sword
                visuals = sword
                modifier = artifact_prowess_1_modifier
                wealth = {score}
                quality = {score}
                save_scope_as = xalw_test_material_{rarity}
                history = {{ type = created_before_history }}
            }}
            scope:xalw_test_material_{rarity} = {{
                set_variable = {{ name = xalw_schema_version value = 2 }}
                set_variable = {{ name = xalw_kind value = flag:ordinary }}
                set_variable = {{ name = xalw_test_fixture_input value = yes }}
            }}
        """))
    effects.append(_block("xalw_test_prepare_owner_effect", """
        create_artifact = {
            name = xalw_test_living_name
            description = xalw_test_living_description
            type = sword
            visuals = sword
            modifier = artifact_prowess_1_modifier
            wealth = 40
            quality = 40
            save_scope_as = xalw_test_living
            history = { type = created_before_history }
        }
        scope:xalw_test_living = {
            set_variable = { name = xalw_schema_version value = 2 }
            xalw_awaken_artifact_effect = yes
            set_variable = { name = xalw_test_fixture_input value = yes }
        }
        xalw_test_create_common_material_effect = yes
        xalw_test_create_masterwork_material_effect = yes
        xalw_test_create_famed_material_effect = yes
        xalw_test_create_illustrious_material_effect = yes
        xalw_discover_owner_effect = yes
    """))
    effects.append(_block("xalw_test_prepare_level_ten_boundary_effect", """
        xalw_test_prepare_owner_effect = yes
        scope:xalw_test_living = {
            set_variable = { name = xalw_level value = 10 }
            set_variable = { name = xalw_xp_in_level value = 900 }
            xalw_refresh_artifact_effect = yes
        }
    """))
    effects.append(_block("xalw_test_prepare_npc_inputs_effect", """
        scope:xalw_test_baron ?= { xalw_test_prepare_owner_effect = yes }
        scope:xalw_test_courtier ?= { xalw_test_prepare_owner_effect = yes }
    """))
    return "\n".join(effects)


def render_fixture_localization(language: Language) -> dict[str, str]:
    """Return external-fixture text; the release inventory excludes this output."""
    if language not in ("simp_chinese", "english"):
        raise ValueError(f"unsupported language: {language}")
    chinese = language == "simp_chinese"
    entries = {
        "xalw_test_living_name": "待测活武器" if chinese else "Living Artifact Under Test",
        "xalw_test_living_description": "仅用于验收的初始物品。" if chinese else "An initial input used only for acceptance.",
        "xalw_test_material_description": "实际原生稀有度由品质与财富生成，喂养读取原生rarity。" if chinese else "Native rarity derives from quality and wealth; feeding reads actual rarity.",
    }
    for rarity, translated in (("common", "普通"), ("masterwork", "大师级"), ("famed", "名作级"), ("illustrious", "卓越级")):
        entries[f"xalw_test_material_{rarity}_name"] = f"待测食材：{translated}" if chinese else f"Test Food: {rarity.title()}"
    return entries
