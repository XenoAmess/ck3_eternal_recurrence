"""Single source for development-only long-run balance telemetry fields."""


FIELD_SPECS = (
    ("kind", "global_var:xa_balance_sample_kind", 1, 3, False),
    ("fixture", "global_var:xa_balance_fixture_code", 1, 3, False),
    ("elapsed", "{ value = current_date subtract = global_var:xa_balance_start_date }", 1, 16, False),
    ("pair", "global_var:xa_bless_count", 1, 8, False),
    ("reject", "global_var:xa_bless_reject_count", 1, 8, False),
    ("score", "global_var:xa_run_score", 100, 31, False),
    ("absolute", "global_var:xa_absolute_score", 100, 31, False),
    ("baseline", "global_var:xa_score_baseline", 100, 31, False),
    ("bless", "global_var:xa_bless_a", 1, 7, False),
    ("br", "global_var:xa_selected_bless_rarity", 1, 2, False),
    ("curse", "global_var:xa_curse_a", 1, 7, False),
    ("cr", "global_var:xa_curse_a_rarity", 1, 2, False),
    ("reroll", "global_var:xa_reroll_tokens", 1, 8, False),
    ("seal", "global_var:xa_seal_tokens", 1, 8, False),
    ("life", "global_var:xa_lifespan_bought", 1, 6, False),
    ("dip", "global_var:xa_a_dip", 1, 10, False),
    ("mar", "global_var:xa_a_mar", 1, 10, False),
    ("ste", "global_var:xa_a_ste", 1, 10, False),
    ("int", "global_var:xa_a_int", 1, 10, False),
    ("lea", "global_var:xa_a_lea", 1, 10, False),
    ("pro", "global_var:xa_a_pro", 1, 10, False),
    ("gold", "global_var:xa_a_gold", 100, 31, True),
    ("prestige", "global_var:xa_a_pres", 100, 31, True),
    ("piety", "global_var:xa_a_pie", 100, 31, True),
    ("influence", "global_var:xa_a_inf", 100, 31, True),
    ("counties", "global_var:xa_n_t1", 1, 10, False),
    ("duchies", "global_var:xa_n_t2", 1, 10, False),
    ("kingdoms", "global_var:xa_n_t3", 1, 10, False),
    ("empires", "global_var:xa_n_t4", 1, 10, False),
    ("realm", "global_var:xa_a_realm", 1, 20, False),
    ("dynasty", "global_var:xa_a_dyn", 1, 20, False),
    ("house", "global_var:xa_a_hou", 1, 20, False),
    ("contract", "global_var:xa_contract_id", 1, 3, False),
    ("progress", "global_var:xa_contract_progress", 1, 4, False),
)


FIELD_SCALES = {name: scale for name, _, scale, _, _ in FIELD_SPECS}
