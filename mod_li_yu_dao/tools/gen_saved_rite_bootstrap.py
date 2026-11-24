"""Bounded old-save catalogue materialization; Source does not qualify CK3 effects.

Current859 create_rite_from_type creates within the scoped character's Faith.
The character must actually follow confucian_faith. convert=no did not preserve
the caller Rite in a1528; capture actual original context and restore only a
proved newly created target. Stock conversion callbacks are never suppressed.
"""
from __future__ import annotations

from content_data import ACTIVE_RITES, PARENT_FAITH

HEADER = '# GENERATED FILE: edit tools/gen_saved_rite_bootstrap.py and run tools/gen_runtime.py.\n'
CHECKED = 'lyd_catalogue_013_bootstrapped'
NEW_RUNTIME_PATHS = frozenset({
    'common/scripted_effects/lyd_saved_rite_bootstrap_effects.txt',
    'common/scripted_guis/lyd_saved_rite_bootstrap.txt',
    'gui/lyd_saved_rite_bootstrap.gui',
    'gui/scripted_widgets/lyd_saved_rite_bootstrap.txt',
})


def catalogue_gate() -> str:
    """Missing objects must never be dereferenced, even under eager AND/OR."""
    branches = []
    for rite in ACTIVE_RITES:
        branches.append(f'''        AND = {{
            trigger_if = {{
                limit = {{ exists = rite:{rite.script_id} }}
                rite = rite:{rite.script_id}
            }}
            trigger_else = {{ always = no }}
        }}''')
    return 'OR = {\n' + '\n'.join(branches) + '\n    }'


def catalogue_ready_gate() -> str:
    """Postcondition: every named instance exists in the intended actual Faith."""
    exists = '\n'.join(f'            exists = rite:{r.script_id}' for r in ACTIVE_RITES)
    parents = '\n'.join(f'        faith = rite:{r.script_id}.faith' for r in ACTIVE_RITES)
    return f'''trigger_if = {{
        limit = {{
{exists}
        }}
        faith = faith:{PARENT_FAITH}
{parents}
    }}
    trigger_else = {{ always = no }}'''



ORIGINAL_RITE = 'lyd_bootstrap_original_rite'
ORIGINAL_FAITH = 'lyd_bootstrap_original_faith'
ORIGINAL_MAIN = 'lyd_bootstrap_original_main'
CREATED_RITE = 'lyd_bootstrap_created_rite'


def original_context_gate(*, require_rite: bool = True) -> str:
    rite_guard = f'        rite = scope:{ORIGINAL_RITE}' if require_rite else ''
    return f'''trigger_if = {{
        limit = {{
            exists = scope:{ORIGINAL_RITE}
            exists = scope:{ORIGINAL_FAITH}
            exists = scope:{ORIGINAL_MAIN}
            exists = faith.main_rite
        }}
        faith = scope:{ORIGINAL_FAITH}
        faith = scope:{ORIGINAL_RITE}.faith
        faith = {{ main_rite = {{ this = scope:{ORIGINAL_MAIN} }} }}
{rite_guard}
    }}
    trigger_else = {{ always = no }}'''


def build_outputs() -> dict[str, bytes]:
    create_missing = '\n'.join(f'''        if = {{
            limit = {{
                NOT = {{ exists = rite:{r.script_id} }}
                {original_context_gate()}
            }}
            clear_saved_scope = {CREATED_RITE}
            create_rite_from_type = {{ type = {r.script_id} convert = no save_scope_as = {CREATED_RITE} }}
            if = {{
                limit = {{ exists = scope:{CREATED_RITE} exists = rite:{r.script_id} }}
                if = {{
                    limit = {{
                        {original_context_gate(require_rite=False)}
                        scope:{CREATED_RITE} = {{ this = rite:{r.script_id} }}
                        rite = scope:{CREATED_RITE}
                        NOT = {{ rite = scope:{ORIGINAL_RITE} }}
                    }}
                    set_character_rite = scope:{ORIGINAL_RITE}
                }}
            }}
        }}''' for r in ACTIVE_RITES)
    effect = f'''lyd_materialize_missing_catalogue_rites_effect = {{
    if = {{
        limit = {{
            is_ai = no
            is_alive = yes
            exists = rite
            faith = faith:{PARENT_FAITH}
            faith = {{ exists = main_rite }}
            NOT = {{ has_global_variable = {CHECKED} }}
        }}
        clear_saved_scope = {ORIGINAL_RITE}
        clear_saved_scope = {ORIGINAL_FAITH}
        clear_saved_scope = {ORIGINAL_MAIN}
        rite = {{ save_scope_as = {ORIGINAL_RITE} }}
        faith = {{
            save_scope_as = {ORIGINAL_FAITH}
            main_rite = {{ save_scope_as = {ORIGINAL_MAIN} }}
        }}
{create_missing}
        if = {{
            limit = {{
                {original_context_gate()}
                lyd_catalogue_instances_ready_trigger = yes
            }}
            set_global_variable = {{ name = {CHECKED} value = yes }}
        }}
    }}
}}
'''
    sgui = f'''lyd_saved_rite_bootstrap_gui = {{
    scope = character
    is_shown = {{
        is_ai = no
        is_alive = yes
        exists = rite
        faith = faith:{PARENT_FAITH}
        faith = {{ exists = main_rite }}
        NOT = {{ has_global_variable = {CHECKED} }}
    }}
    effect = {{ lyd_materialize_missing_catalogue_rites_effect = yes }}
}}
'''
    gui = '''window = {
    name = "lyd_saved_rite_bootstrap_window"
    size = { 1 1 }
    layer = tutorial
    position = { 0 0 }
    visible = "[GetPlayer.IsValid]"
    alwaystransparent = yes
    state = {
        name = "lyd_saved_rite_bootstrap"
        trigger_when = "[GetScriptedGui('lyd_saved_rite_bootstrap_gui').IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
        on_start = "[GetScriptedGui('lyd_saved_rite_bootstrap_gui').Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
    }
}
'''
    widget = 'gui/lyd_saved_rite_bootstrap.gui = lyd_saved_rite_bootstrap_window\n'
    outputs = {
        'common/scripted_effects/lyd_saved_rite_bootstrap_effects.txt': effect,
        'common/scripted_guis/lyd_saved_rite_bootstrap.txt': sgui,
        'gui/lyd_saved_rite_bootstrap.gui': gui,
        'gui/scripted_widgets/lyd_saved_rite_bootstrap.txt': widget,
    }
    return {p: (HEADER + text).encode('utf-8-sig') for p, text in outputs.items()}
