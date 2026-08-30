#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the shared CK3 case/receipt/deadline/transaction kernel for 361.

The kernel is deliberately mechanism-agnostic.  Domain generators bind its
parameterized helpers to fixed variable names; a numbered mechanism still
needs a real domain consumer before it may claim gameplay readiness.
"""

from __future__ import annotations

from pathlib import Path

from zg361_domain_data import DOMAIN_SPECS


MOD_ROOT = Path(__file__).resolve().parents[1]
EFFECTS_PATH = MOD_ROOT / "common" / "scripted_effects" / "zg361_case_kernel_effects.txt"
TRIGGERS_PATH = MOD_ROOT / "common" / "scripted_triggers" / "zg361_case_kernel_triggers.txt"


def _domain_slug(code: str) -> str:
    return code.lower()


def _domain_variables(code: str) -> dict[str, str]:
    slug = _domain_slug(code)
    prefix = f"zg361_case_{slug}"
    return {
        "owner": f"{prefix}_owner",
        "subject": f"{prefix}_subject",
        "cycle": f"{prefix}_cycle_serial",
        "case": f"{prefix}_case_serial",
        "state": f"{prefix}_state",
        "revision": f"{prefix}_revision",
        "active": f"{prefix}_active",
        "cursor": f"{prefix}_cursor",
        "timeline": f"{prefix}_timeline_serial",
        "feedback": f"{prefix}_feedback_revision",
        "last_operation": f"{prefix}_last_operation",
        "last_choice": f"{prefix}_last_choice",
        "last_hook": f"{prefix}_last_hook",
    }


def render_triggers() -> str:
    return r'''# GENERATED FILE — edit tools/gen_361_case_kernel.py
# Shared guards deliberately put every var: read behind one existence gate.

zg361_case_kernel_can_open_trigger = {
	root = {
		zg361_is_celestial_liege_trigger = yes
		has_variable = $MANAGER_CYCLE_VAR$
	}
	zg361_is_reviewable_vassal_trigger = yes
	liege = root
	trigger_if = {
		limit = { has_variable = $ACTIVE_VAR$ }
		var:$ACTIVE_VAR$ = 0
	}
	trigger_else = { always = yes }
}

zg361_case_kernel_full_guard_trigger = {
	trigger_if = {
		limit = {
			has_variable = $OWNER_VAR$
			has_variable = $SUBJECT_VAR$
			has_variable = $CYCLE_VAR$
			has_variable = $CASE_VAR$
			has_variable = $STATE_VAR$
			has_variable = $ACTIVE_VAR$
		}
		var:$OWNER_VAR$ = $EXPECTED_OWNER$
		var:$SUBJECT_VAR$ = $EXPECTED_SUBJECT$
		var:$CYCLE_VAR$ = $EXPECTED_CYCLE$
		var:$CASE_VAR$ = $EXPECTED_CASE$
		var:$STATE_VAR$ = $EXPECTED_STATE$
		var:$ACTIVE_VAR$ = 1
	}
	trigger_else = { always = no }
}

zg361_case_kernel_receipt_is_current_trigger = {
	trigger_if = {
		limit = {
			has_variable = $RECEIPT_OWNER_VAR$
			has_variable = $RECEIPT_SUBJECT_VAR$
			has_variable = $RECEIPT_CYCLE_VAR$
			has_variable = $RECEIPT_CASE_VAR$
			has_variable = $RECEIPT_STATE_VAR$
			has_variable = $RECEIPT_CHOICE_VAR$
		}
		var:$RECEIPT_OWNER_VAR$ = $EXPECTED_OWNER$
		var:$RECEIPT_SUBJECT_VAR$ = $EXPECTED_SUBJECT$
		var:$RECEIPT_CYCLE_VAR$ = $EXPECTED_CYCLE$
		var:$RECEIPT_CASE_VAR$ = $EXPECTED_CASE$
		var:$RECEIPT_STATE_VAR$ = $EXPECTED_STATE$
		var:$RECEIPT_CHOICE_VAR$ = $EXPECTED_CHOICE$
	}
	trigger_else = { always = no }
}

zg361_case_kernel_deadline_is_current_trigger = {
	trigger_if = {
		limit = {
			has_variable = $OWNER_VAR$
			has_variable = $SUBJECT_VAR$
			has_variable = $CYCLE_VAR$
			has_variable = $CASE_VAR$
			has_variable = $STATE_VAR$
			has_variable = $ACTIVE_VAR$
			has_variable = $DEADLINE_OWNER_VAR$
			has_variable = $DEADLINE_SUBJECT_VAR$
			has_variable = $DEADLINE_CYCLE_VAR$
			has_variable = $DEADLINE_CASE_VAR$
			has_variable = $DEADLINE_STATE_VAR$
			has_variable = $DEADLINE_PENDING_VAR$
		}
		var:$ACTIVE_VAR$ = 1
		var:$DEADLINE_PENDING_VAR$ = 1
		var:$OWNER_VAR$ = var:$DEADLINE_OWNER_VAR$
		var:$SUBJECT_VAR$ = var:$DEADLINE_SUBJECT_VAR$
		var:$CYCLE_VAR$ = var:$DEADLINE_CYCLE_VAR$
		var:$CASE_VAR$ = var:$DEADLINE_CASE_VAR$
		var:$STATE_VAR$ = var:$DEADLINE_STATE_VAR$
	}
	trigger_else = { always = no }
}

# Counts/barons may consume only their own frozen case.  This trigger grants no
# manager, calibration, PIP-owner, HC or allocation authority.
zg361_case_kernel_subject_self_guard_trigger = {
	trigger_if = {
		limit = {
			has_variable = $SUBJECT_VAR$
			has_variable = $ACTIVE_VAR$
		}
		var:$SUBJECT_VAR$ = this
		var:$ACTIVE_VAR$ = 1
	}
	trigger_else = { always = no }
}

zg361_case_kernel_positive_amount_trigger = {
	save_temporary_scope_value_as = {
		name = zg361_case_kernel_amount
		value = $AMOUNT$
	}
	scope:zg361_case_kernel_amount > 0
}
'''


def render_effect_helpers() -> str:
    return r'''# GENERATED FILE — edit tools/gen_361_case_kernel.py
# Shared 361 case kernel.  Callers must pass fixed variable names and frozen
# ticket values; numbered domain behavior remains owned by domain generators.

zg361_case_kernel_initialize_case_effect = {
	remove_variable = zg361_case_kernel_applied
	if = {
		limit = {
			zg361_case_kernel_can_open_trigger = {
				MANAGER_CYCLE_VAR = $MANAGER_CYCLE_VAR$
				ACTIVE_VAR = $ACTIVE_VAR$
			}
		}
		root = {
			if = {
				limit = { NOT = { has_variable = $MANAGER_CASE_CURSOR_VAR$ } }
				set_variable = { name = $MANAGER_CASE_CURSOR_VAR$ value = 0 }
			}
			change_variable = { name = $MANAGER_CASE_CURSOR_VAR$ add = 1 }
		}
		set_variable = { name = $OWNER_VAR$ value = root }
		set_variable = { name = $SUBJECT_VAR$ value = this }
		set_variable = { name = $CYCLE_VAR$ value = root.var:$MANAGER_CYCLE_VAR$ }
		set_variable = { name = $CASE_VAR$ value = root.var:$MANAGER_CASE_CURSOR_VAR$ }
		set_variable = { name = $STATE_VAR$ value = $ENTRY_STATE$ }
		set_variable = { name = $REVISION_VAR$ value = 1 }
		set_variable = { name = $ACTIVE_VAR$ value = 1 }
		set_variable = { name = $TIMELINE_VAR$ value = 1 }
		set_variable = { name = $FEEDBACK_VAR$ value = 1 }
		set_variable = { name = $LAST_OPERATION_VAR$ value = 0 }
		set_variable = { name = $LAST_CHOICE_VAR$ value = 0 }
		set_variable = { name = $LAST_HOOK_VAR$ value = 0 }
		set_variable = { name = zg361_case_kernel_applied value = 1 }
	}
}

# Record one typed domain operation while the owning stage remains unchanged.
# Each mechanism/route supplies its own six receipt variable names.
zg361_case_kernel_record_operation_effect = {
	remove_variable = zg361_case_kernel_applied
	if = {
		limit = {
			zg361_case_kernel_full_guard_trigger = {
				OWNER_VAR = $OWNER_VAR$
				SUBJECT_VAR = $SUBJECT_VAR$
				CYCLE_VAR = $CYCLE_VAR$
				CASE_VAR = $CASE_VAR$
				STATE_VAR = $STATE_VAR$
				ACTIVE_VAR = $ACTIVE_VAR$
				EXPECTED_OWNER = $TICKET_OWNER$
				EXPECTED_SUBJECT = $TICKET_SUBJECT$
				EXPECTED_CYCLE = $TICKET_CYCLE$
				EXPECTED_CASE = $TICKET_CASE$
				EXPECTED_STATE = $TICKET_STATE$
			}
			NOT = {
				zg361_case_kernel_receipt_is_current_trigger = {
					RECEIPT_OWNER_VAR = $RECEIPT_OWNER_VAR$
					RECEIPT_SUBJECT_VAR = $RECEIPT_SUBJECT_VAR$
					RECEIPT_CYCLE_VAR = $RECEIPT_CYCLE_VAR$
					RECEIPT_CASE_VAR = $RECEIPT_CASE_VAR$
					RECEIPT_STATE_VAR = $RECEIPT_STATE_VAR$
					RECEIPT_CHOICE_VAR = $RECEIPT_CHOICE_VAR$
					EXPECTED_OWNER = $TICKET_OWNER$
					EXPECTED_SUBJECT = $TICKET_SUBJECT$
					EXPECTED_CYCLE = $TICKET_CYCLE$
					EXPECTED_CASE = $TICKET_CASE$
					EXPECTED_STATE = $TICKET_STATE$
					EXPECTED_CHOICE = $CHOICE$
				}
			}
		}
		set_variable = { name = $RECEIPT_OWNER_VAR$ value = $TICKET_OWNER$ }
		set_variable = { name = $RECEIPT_SUBJECT_VAR$ value = $TICKET_SUBJECT$ }
		set_variable = { name = $RECEIPT_CYCLE_VAR$ value = $TICKET_CYCLE$ }
		set_variable = { name = $RECEIPT_CASE_VAR$ value = $TICKET_CASE$ }
		set_variable = { name = $RECEIPT_STATE_VAR$ value = $TICKET_STATE$ }
		set_variable = { name = $RECEIPT_CHOICE_VAR$ value = $CHOICE$ }
		set_variable = { name = $LAST_OPERATION_VAR$ value = $OPERATION_ID$ }
		set_variable = { name = $LAST_CHOICE_VAR$ value = $CHOICE$ }
		change_variable = { name = $REVISION_VAR$ add = 1 }
		change_variable = { name = $TIMELINE_VAR$ add = 1 }
		change_variable = { name = $FEEDBACK_VAR$ add = 1 }
		set_variable = { name = zg361_case_kernel_applied value = 1 }
	}
}

# Only the shared stage dispatcher calls this helper.  Per-mechanism operations
# record receipts but cannot advance the case by themselves.
zg361_case_kernel_transition_effect = {
	remove_variable = zg361_case_kernel_applied
	if = {
		limit = {
			zg361_case_kernel_full_guard_trigger = {
				OWNER_VAR = $OWNER_VAR$
				SUBJECT_VAR = $SUBJECT_VAR$
				CYCLE_VAR = $CYCLE_VAR$
				CASE_VAR = $CASE_VAR$
				STATE_VAR = $STATE_VAR$
				ACTIVE_VAR = $ACTIVE_VAR$
				EXPECTED_OWNER = $TICKET_OWNER$
				EXPECTED_SUBJECT = $TICKET_SUBJECT$
				EXPECTED_CYCLE = $TICKET_CYCLE$
				EXPECTED_CASE = $TICKET_CASE$
				EXPECTED_STATE = $TICKET_STATE$
			}
		}
		set_variable = { name = $STATE_VAR$ value = $NEXT_STATE$ }
		set_variable = { name = $LAST_HOOK_VAR$ value = $HOOK_ID$ }
		change_variable = { name = $REVISION_VAR$ add = 1 }
		change_variable = { name = $TIMELINE_VAR$ add = 1 }
		change_variable = { name = $FEEDBACK_VAR$ add = 1 }
		if = {
			limit = { always = $CLOSE_CASE$ }
			set_variable = { name = $ACTIVE_VAR$ value = 0 }
		}
		set_variable = { name = zg361_case_kernel_applied value = 1 }
	}
}

# Bind a real delayed event to the frozen five-field identity.  The event must
# call the expire helper before it invokes any domain due resolver.
zg361_case_kernel_schedule_deadline_effect = {
	remove_variable = zg361_case_kernel_applied
	if = {
		limit = {
			zg361_case_kernel_full_guard_trigger = {
				OWNER_VAR = $OWNER_VAR$
				SUBJECT_VAR = $SUBJECT_VAR$
				CYCLE_VAR = $CYCLE_VAR$
				CASE_VAR = $CASE_VAR$
				STATE_VAR = $STATE_VAR$
				ACTIVE_VAR = $ACTIVE_VAR$
				EXPECTED_OWNER = $TICKET_OWNER$
				EXPECTED_SUBJECT = $TICKET_SUBJECT$
				EXPECTED_CYCLE = $TICKET_CYCLE$
				EXPECTED_CASE = $TICKET_CASE$
				EXPECTED_STATE = $TICKET_STATE$
			}
			trigger_if = {
				limit = { has_variable = $DEADLINE_PENDING_VAR$ }
				var:$DEADLINE_PENDING_VAR$ = 0
			}
			trigger_else = { always = yes }
		}
		set_variable = { name = $DEADLINE_OWNER_VAR$ value = $TICKET_OWNER$ }
		set_variable = { name = $DEADLINE_SUBJECT_VAR$ value = $TICKET_SUBJECT$ }
		set_variable = { name = $DEADLINE_CYCLE_VAR$ value = $TICKET_CYCLE$ }
		set_variable = { name = $DEADLINE_CASE_VAR$ value = $TICKET_CASE$ }
		set_variable = { name = $DEADLINE_STATE_VAR$ value = $TICKET_STATE$ }
		set_variable = { name = $DEADLINE_DAYS_VAR$ value = $DAYS$ }
		set_variable = { name = $DEADLINE_PENDING_VAR$ value = 1 }
		set_variable = { name = $DEADLINE_EXPIRED_VAR$ value = 0 }
		trigger_event = { id = $EVENT$ days = $DAYS$ }
		set_variable = { name = zg361_case_kernel_applied value = 1 }
	}
}

zg361_case_kernel_expire_deadline_effect = {
	remove_variable = zg361_case_kernel_applied
	if = {
		limit = {
			zg361_case_kernel_deadline_is_current_trigger = {
				OWNER_VAR = $OWNER_VAR$
				SUBJECT_VAR = $SUBJECT_VAR$
				CYCLE_VAR = $CYCLE_VAR$
				CASE_VAR = $CASE_VAR$
				STATE_VAR = $STATE_VAR$
				ACTIVE_VAR = $ACTIVE_VAR$
				DEADLINE_OWNER_VAR = $DEADLINE_OWNER_VAR$
				DEADLINE_SUBJECT_VAR = $DEADLINE_SUBJECT_VAR$
				DEADLINE_CYCLE_VAR = $DEADLINE_CYCLE_VAR$
				DEADLINE_CASE_VAR = $DEADLINE_CASE_VAR$
				DEADLINE_STATE_VAR = $DEADLINE_STATE_VAR$
				DEADLINE_PENDING_VAR = $DEADLINE_PENDING_VAR$
			}
		}
		set_variable = { name = $DEADLINE_PENDING_VAR$ value = 0 }
		set_variable = { name = $DEADLINE_EXPIRED_VAR$ value = 1 }
		change_variable = { name = $REVISION_VAR$ add = 1 }
		change_variable = { name = $TIMELINE_VAR$ add = 1 }
		change_variable = { name = $FEEDBACK_VAR$ add = 1 }
		set_variable = { name = zg361_case_kernel_applied value = 1 }
	}
}

# Resource journals are amount-agnostic: gold, HC, capacity, quota and vote
# ledgers all use the same atomic reserve -> settle/refund contract.  Domain
# consumers remain responsible for applying the matching CK3 gameplay effect.
zg361_case_kernel_reserve_transaction_effect = {
	remove_variable = zg361_case_kernel_applied
	if = {
		limit = {
			zg361_case_kernel_full_guard_trigger = {
				OWNER_VAR = $OWNER_VAR$
				SUBJECT_VAR = $SUBJECT_VAR$
				CYCLE_VAR = $CYCLE_VAR$
				CASE_VAR = $CASE_VAR$
				STATE_VAR = $STATE_VAR$
				ACTIVE_VAR = $ACTIVE_VAR$
				EXPECTED_OWNER = $TICKET_OWNER$
				EXPECTED_SUBJECT = $TICKET_SUBJECT$
				EXPECTED_CYCLE = $TICKET_CYCLE$
				EXPECTED_CASE = $TICKET_CASE$
				EXPECTED_STATE = $TICKET_STATE$
			}
			has_variable = $AVAILABLE_VAR$
			var:$AVAILABLE_VAR$ >= $AMOUNT$
			zg361_case_kernel_positive_amount_trigger = { AMOUNT = $AMOUNT$ }
			trigger_if = {
				limit = { has_variable = $RECEIPT_STATUS_VAR$ }
				var:$RECEIPT_STATUS_VAR$ = 0
			}
			trigger_else = { always = yes }
		}
		if = {
			limit = { NOT = { has_variable = $RESERVED_VAR$ } }
			set_variable = { name = $RESERVED_VAR$ value = 0 }
		}
		change_variable = { name = $AVAILABLE_VAR$ add = { value = 0 subtract = $AMOUNT$ } }
		change_variable = { name = $RESERVED_VAR$ add = $AMOUNT$ }
		set_variable = { name = $RECEIPT_AMOUNT_VAR$ value = $AMOUNT$ }
		set_variable = { name = $RECEIPT_STATUS_VAR$ value = 1 }
		set_variable = { name = $RECEIPT_OWNER_VAR$ value = $TICKET_OWNER$ }
		set_variable = { name = $RECEIPT_CYCLE_VAR$ value = $TICKET_CYCLE$ }
		set_variable = { name = $RECEIPT_CASE_VAR$ value = $TICKET_CASE$ }
		change_variable = { name = $REVISION_VAR$ add = 1 }
		set_variable = { name = zg361_case_kernel_applied value = 1 }
	}
}

zg361_case_kernel_settle_transaction_effect = {
	remove_variable = zg361_case_kernel_applied
	if = {
		limit = {
			zg361_case_kernel_full_guard_trigger = {
				OWNER_VAR = $OWNER_VAR$
				SUBJECT_VAR = $SUBJECT_VAR$
				CYCLE_VAR = $CYCLE_VAR$
				CASE_VAR = $CASE_VAR$
				STATE_VAR = $STATE_VAR$
				ACTIVE_VAR = $ACTIVE_VAR$
				EXPECTED_OWNER = $TICKET_OWNER$
				EXPECTED_SUBJECT = $TICKET_SUBJECT$
				EXPECTED_CYCLE = $TICKET_CYCLE$
				EXPECTED_CASE = $TICKET_CASE$
				EXPECTED_STATE = $TICKET_STATE$
			}
			has_variable = $RESERVED_VAR$
			has_variable = $RECEIPT_AMOUNT_VAR$
			has_variable = $RECEIPT_STATUS_VAR$
			var:$RECEIPT_STATUS_VAR$ = 1
			var:$RESERVED_VAR$ >= var:$RECEIPT_AMOUNT_VAR$
		}
		if = {
			limit = { NOT = { has_variable = $SETTLED_VAR$ } }
			set_variable = { name = $SETTLED_VAR$ value = 0 }
		}
		change_variable = { name = $RESERVED_VAR$ add = { value = 0 subtract = var:$RECEIPT_AMOUNT_VAR$ } }
		change_variable = { name = $SETTLED_VAR$ add = var:$RECEIPT_AMOUNT_VAR$ }
		set_variable = { name = $RECEIPT_STATUS_VAR$ value = 2 }
		change_variable = { name = $REVISION_VAR$ add = 1 }
		set_variable = { name = zg361_case_kernel_applied value = 1 }
	}
}

zg361_case_kernel_refund_transaction_effect = {
	remove_variable = zg361_case_kernel_applied
	if = {
		limit = {
			zg361_case_kernel_full_guard_trigger = {
				OWNER_VAR = $OWNER_VAR$
				SUBJECT_VAR = $SUBJECT_VAR$
				CYCLE_VAR = $CYCLE_VAR$
				CASE_VAR = $CASE_VAR$
				STATE_VAR = $STATE_VAR$
				ACTIVE_VAR = $ACTIVE_VAR$
				EXPECTED_OWNER = $TICKET_OWNER$
				EXPECTED_SUBJECT = $TICKET_SUBJECT$
				EXPECTED_CYCLE = $TICKET_CYCLE$
				EXPECTED_CASE = $TICKET_CASE$
				EXPECTED_STATE = $TICKET_STATE$
			}
			has_variable = $AVAILABLE_VAR$
			has_variable = $RECEIPT_AMOUNT_VAR$
			has_variable = $RECEIPT_STATUS_VAR$
			OR = {
				var:$RECEIPT_STATUS_VAR$ = 1
				var:$RECEIPT_STATUS_VAR$ = 2
			}
		}
		if = {
			limit = { var:$RECEIPT_STATUS_VAR$ = 1 }
			change_variable = { name = $RESERVED_VAR$ add = { value = 0 subtract = var:$RECEIPT_AMOUNT_VAR$ } }
		}
		else = {
			change_variable = { name = $SETTLED_VAR$ add = { value = 0 subtract = var:$RECEIPT_AMOUNT_VAR$ } }
		}
		change_variable = { name = $AVAILABLE_VAR$ add = var:$RECEIPT_AMOUNT_VAR$ }
		set_variable = { name = $RECEIPT_STATUS_VAR$ value = 3 }
		change_variable = { name = $REVISION_VAR$ add = 1 }
		set_variable = { name = zg361_case_kernel_applied value = 1 }
	}
}
'''


def render_domain_wrappers() -> str:
    chunks: list[str] = []
    for domain in DOMAIN_SPECS:
        slug = _domain_slug(domain.code)
        variables = _domain_variables(domain.code)
        chunks.append(
            f'''\n# {domain.code}: {domain.object_type}; state 1 = {domain.states[0]}\n'''
            f'''zg361_case_{slug}_open_effect = {{\n'''
            f'''\tzg361_case_kernel_initialize_case_effect = {{\n'''
            f'''\t\tMANAGER_CYCLE_VAR = zg361_review_serial\n'''
            f'''\t\tMANAGER_CASE_CURSOR_VAR = {variables["cursor"]}\n'''
            f'''\t\tOWNER_VAR = {variables["owner"]}\n'''
            f'''\t\tSUBJECT_VAR = {variables["subject"]}\n'''
            f'''\t\tCYCLE_VAR = {variables["cycle"]}\n'''
            f'''\t\tCASE_VAR = {variables["case"]}\n'''
            f'''\t\tSTATE_VAR = {variables["state"]}\n'''
            f'''\t\tREVISION_VAR = {variables["revision"]}\n'''
            f'''\t\tACTIVE_VAR = {variables["active"]}\n'''
            f'''\t\tTIMELINE_VAR = {variables["timeline"]}\n'''
            f'''\t\tFEEDBACK_VAR = {variables["feedback"]}\n'''
            f'''\t\tLAST_OPERATION_VAR = {variables["last_operation"]}\n'''
            f'''\t\tLAST_CHOICE_VAR = {variables["last_choice"]}\n'''
            f'''\t\tLAST_HOOK_VAR = {variables["last_hook"]}\n'''
            f'''\t\tENTRY_STATE = 1\n'''
            f'''\t}}\n'''
            f'''}}\n'''
        )
        for index, (old_state, new_state, hook) in enumerate(domain.transitions, start=1):
            close = "yes" if index == len(domain.transitions) else "no"
            chunks.append(
                f'''\n# {domain.code} stage {index}: {old_state} -> {new_state} on {hook}\n'''
                f'''zg361_case_{slug}_advance_{index:02d}_effect = {{\n'''
                f'''\tzg361_case_kernel_transition_effect = {{\n'''
                f'''\t\tOWNER_VAR = {variables["owner"]}\n'''
                f'''\t\tSUBJECT_VAR = {variables["subject"]}\n'''
                f'''\t\tCYCLE_VAR = {variables["cycle"]}\n'''
                f'''\t\tCASE_VAR = {variables["case"]}\n'''
                f'''\t\tSTATE_VAR = {variables["state"]}\n'''
                f'''\t\tREVISION_VAR = {variables["revision"]}\n'''
                f'''\t\tACTIVE_VAR = {variables["active"]}\n'''
                f'''\t\tTIMELINE_VAR = {variables["timeline"]}\n'''
                f'''\t\tFEEDBACK_VAR = {variables["feedback"]}\n'''
                f'''\t\tLAST_HOOK_VAR = {variables["last_hook"]}\n'''
                f'''\t\tTICKET_OWNER = $TICKET_OWNER$\n'''
                f'''\t\tTICKET_SUBJECT = $TICKET_SUBJECT$\n'''
                f'''\t\tTICKET_CYCLE = $TICKET_CYCLE$\n'''
                f'''\t\tTICKET_CASE = $TICKET_CASE$\n'''
                f'''\t\tTICKET_STATE = {index}\n'''
                f'''\t\tNEXT_STATE = {index + 1}\n'''
                f'''\t\tHOOK_ID = {index}\n'''
                f'''\t\tCLOSE_CASE = {close}\n'''
                f'''\t}}\n'''
                f'''}}\n'''
            )
    return "".join(chunks)


def outputs() -> dict[Path, str]:
    return {
        EFFECTS_PATH: render_effect_helpers() + render_domain_wrappers(),
        TRIGGERS_PATH: render_triggers(),
    }


def main() -> None:
    for path, text in outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8-sig", newline="\n")
        print(f"wrote {path.relative_to(MOD_ROOT)}")


if __name__ == "__main__":
    main()
