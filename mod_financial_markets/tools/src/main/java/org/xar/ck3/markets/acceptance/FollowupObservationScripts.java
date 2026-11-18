package org.xar.ck3.markets.acceptance;

import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.markets.acceptance.FollowupContracts.Profile;
import org.xar.ck3.markets.acceptance.FollowupContracts.Request;

/** Bounded, watched-object observations. Never calls product effects or supplies business state. */
public final class FollowupObservationScripts {
    private FollowupObservationScripts() { }

    public static Map<String, byte[]> render(Request request) {
        String prefix = request.prefix();
        Map<String, String> scripts = new LinkedHashMap<>();
        scripts.put("descriptor.mod", "name=\"Financial market follow-up read-only observer\"\nversion=\"2\"\nsupported_version=\"1.21.*\"\n");
        scripts.put("common/scripted_guis/" + prefix + ".txt", """
                ${P}_arm_gui = {
                    scope = character
                    is_valid = { is_ai = no is_alive = yes ${ACTOR} NOT = { has_variable = ${P}_armed } NOT = { exists = var:${P}_story } }
                    effect = { ${P}_arm_effect = yes }
                }
                ${P}_refresh_gui = {
                    scope = character
                    is_valid = { is_ai = no is_alive = yes exists = var:${P}_story }
                    effect = { var:${P}_story = { ${P}_observe_effect = yes } }
                }
                """);
        scripts.put("gui/scripted_widgets/" + prefix + ".txt", "gui/" + prefix + ".gui = xfma_observer_widget\n");
        scripts.put("gui/" + prefix + ".gui", """
                window = {
                    name = "xfma_observer_widget"
                    parentanchor = top|right
                    position = { -290 130 }
                    size = { 220 82 }
                    layer = middle
                    visible = "[GetPlayer.IsValid]"
                    button_standard = {
                        name = "xfma_arm_observer"
                        size = { 220 40 }
                        text = "xfma_followup_arm_label"
                        enabled = "[GetScriptedGui( '${P}_arm_gui' ).IsValid( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
                        onclick = "[GetScriptedGui( '${P}_arm_gui' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
                    }
                    button_standard = {
                        name = "xfma_refresh_observer"
                        position = { 0 42 }
                        size = { 220 40 }
                        text = "xfma_followup_refresh_label"
                        enabled = "[GetScriptedGui( '${P}_refresh_gui' ).IsValid( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
                        onclick = "[GetScriptedGui( '${P}_refresh_gui' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
                    }
                }
                """);
        scripts.put("localization/english/" + prefix + "_l_english.yml", """
                l_english:
                 xfma_followup_arm_label:0 "Record observation baseline"
                 xfma_followup_refresh_label:0 "Read watched market facts"
                """);
        scripts.put("localization/simp_chinese/" + prefix + "_l_simp_chinese.yml", """
                l_simp_chinese:
                 xfma_followup_arm_label:0 "记录只读观察基线"
                 xfma_followup_refresh_label:0 "读回所观察的市场事实"
                """);
        scripts.put("common/story_cycles/" + prefix + ".txt", "${P}_observer = {\n visible = no\n on_owner_death = {\n"
                + ownerDeath(request) + "\n }\n effect_group = { days = 1 triggered_effect = { trigger = { exists = story_owner } effect = { ${P}_observe_effect = yes } } }\n}\n");
        scripts.put("common/scripted_triggers/" + prefix + ".txt", "${P}_associations_trigger = {\n" + associations(request) + "\n}\n");
        if (request.caseId() == Profile.DERIVATIVES || request.caseId() == Profile.NEWS_CRISIS) {
            scripts.put("common/script_values/" + prefix + ".txt", """
                    # Debt-story scope. Pure sums preserve exact accounting without equality-to-block dispatch.
                    ${P}_claim_split_value = { value = var:xfm_winner_unpaid_cents add = var:xfm_fund_recourse_cents }
                    ${P}_claim_principal_value = { value = var:xfm_outstanding_cents add = var:xfm_repaid_cents add = var:xfm_written_off_cents }
                    """);
        }
        scripts.put("common/scripted_effects/" + prefix + "_observe.txt", common(request) + profile(request));
        Map<String, byte[]> result = new LinkedHashMap<>();
        scripts.forEach((name, source) -> result.put(name, ("\ufeff" + source.replace("${P}", prefix)
                .replace("${ACTOR}", actorCondition(request))).getBytes(StandardCharsets.UTF_8)));
        return Map.copyOf(result);
    }

    private static String actorCondition(Request request) {
        return request.actor().mode() == FollowupContracts.ActorMode.HISTORY_CHARACTER
                ? "this = character:" + request.actor().historyId() : "is_ai = no";
    }

    private static String common(Request request) {
        String required = "exists = var:xfma_account\nvar:xfma_account = { story_type = xfm_finance_account exists = var:xfm_holder has_variable = xfm_account_id has_variable = xfm_free_cents has_variable = xfm_reserved_cents }\n";
        if (request.targets().coinId() != null || request.targets().indexId() != null) required += "exists = var:xfma_coin\n";
        if (request.targets().contractId() != null) required += "exists = var:xfma_contract\n";
        if (request.targets().positionId() != null) required += "exists = var:xfma_position\n";
        if (request.targets().debtId() != null) required += "exists = var:xfma_debt\n";
        if (request.targets().newsId() != null) required += "exists = var:xfma_news\n";
        if (request.caseId() == Profile.INHERITANCE) required += "var:xfma_account.var:xfm_holder = { is_alive = yes }\n";
        if (request.caseId() == Profile.NEWS_CRISIS) required += "global_var:xfm_exchange = { has_variable = xfm_news_counter }\n";
        required += "${P}_associations_trigger = yes\n";
        return """
                # Only xfma_ observation state is written. No product effect is invoked.
                ${P}_arm_effect = {
                    if = {
                        limit = { is_ai = no is_alive = yes ${ACTOR} NOT = { has_variable = ${P}_armed } NOT = { exists = var:${P}_story } exists = global_var:xfm_exchange }
                        save_scope_as = xfma_operator
                        clear_saved_scope = xfma_context
                        create_story = { type = ${P}_observer save_scope_as = xfma_context }
                        if = {
                            limit = { exists = scope:xfma_context }
                            set_variable = { name = ${P}_armed value = 1 }
                            set_variable = { name = ${P}_story value = scope:xfma_context }
                            scope:xfma_context = {
                                set_variable = { name = xfma_start_day value = global_var:xfm_exchange.var:xfm_day }
                                set_variable = { name = xfma_last_sample_day value = var:xfma_start_day }
                                set_variable = { name = xfma_start_date value = current_date }
                                set_variable = { name = xfma_daily_samples value = 0 }
                                set_variable = { name = xfma_measured_samples value = 0 }
                                set_variable = { name = xfma_refreshes value = 0 }
                                set_variable = { name = xfma_start_news_counter value = 0 }
                                if = { limit = { global_var:xfm_exchange = { has_variable = xfm_news_counter } } set_variable = { name = xfma_start_news_counter value = global_var:xfm_exchange.var:xfm_news_counter } }
                                ${P}_bind_effect = yes
                """ + "if = { limit = {\n" + required + "}\n"
                + "set_variable = { name = xfma_ready value = 1 }\n"
                + "set_variable = { name = xfma_holder_before value = var:xfma_account.var:xfm_holder }\n"
                + "if = { limit = { exists = var:xfma_holder_before.primary_heir } set_variable = { name = xfma_heir_before value = var:xfma_holder_before.primary_heir } }\n"
                + "if = { limit = { exists = var:xfma_debt } set_variable = { name = xfma_debt_before value = var:xfma_debt } }\n"
                + "if = { limit = { exists = var:xfma_coin } set_variable = { name = xfma_start_notice_day value = -1 } if = { limit = { var:xfma_coin = { has_variable = xfm_notice_day } } set_variable = { name = xfma_start_notice_day value = var:xfma_coin.var:xfm_notice_day } } }\n"
                + "debug_log = \"" + marker(request, "observation_ready") + "\"\n${P}_observe_effect = yes\n"
                + "} else = { debug_log = \"XFMAT: TEST FAIL followup_target_missing_or_not_predeath\" }\n"
                + "} } else = { debug_log = \"XFMAT: TEST FAIL followup_observer_allocation_failed\" }\n} }\n"
                + "${P}_bind_effect = {\n save_scope_as = xfma_context\n" + bindings(request) + "\n}\n"
                + """
                ${P}_observe_effect = {
                    save_scope_as = xfma_context
                    if = {
                        limit = { var:xfma_ready = 1 exists = global_var:xfm_exchange }
                        ${P}_bind_effect = yes
                        change_variable = { name = xfma_refreshes add = 1 }
                        if = {
                            limit = { global_var:xfm_exchange.var:xfm_day > var:xfma_last_sample_day }
                            if = { limit = { global_var:xfm_exchange.var:xfm_day > { value = var:xfma_last_sample_day add = 1 } } set_variable = { name = xfma_sample_gap value = 1 } }
                            change_variable = { name = xfma_daily_samples add = 1 }
                            if = { limit = { var:xfma_daily_samples > 30 } change_variable = { name = xfma_measured_samples add = 1 } }
                            set_variable = { name = xfma_last_sample_day value = global_var:xfm_exchange.var:xfm_day }
                        }
                        if = { limit = { exists = var:xfma_account } set_variable = { name = xfma_account_free_readback value = var:xfma_account.var:xfm_free_cents } set_variable = { name = xfma_account_reserved_readback value = var:xfma_account.var:xfm_reserved_cents } }
                        if = { limit = { ${P}_associations_trigger = yes } ${P}_profile_effect = yes }
                        else = { set_variable = { name = xfma_bad_target_association value = 1 } debug_log = "XFMAT: TEST FAIL followup_target_association_mismatch" }
                    }
                }
                """;
    }

    private static String bindings(Request request) {
        var targets = request.targets();
        StringBuilder source = new StringBuilder();
        source.append(lookup("account", "every_in_global_list", "xfm_account_registry", "xfm_account_id", targets.accountId(), null));
        source.append(lookup("coin", "every_in_global_list", "xfm_coin_registry", "xfm_coin_id", targets.coinId(), null));
        source.append(lookup("coin", "every_in_global_list", "xfm_index_registry", "xfm_index_id", targets.indexId(), null));
        source.append(lookup("contract", "every_in_list", "xfm_futures_contracts", "xfm_contract_id", targets.contractId(), "global_var:xfm_exchange"));
        if (targets.positionId() != null) {
            source.append(lookup("position", "every_in_list", "xfm_positions", "xfm_position_id", targets.positionId(), "var:xfma_account"));
            source.append(lookup("position", "every_in_list", "xfm_futures_position_history", "xfm_position_id", targets.positionId(), "var:xfma_account"));
        } else if (request.caseId() == Profile.DERIVATIVES) {
            String selectedContract = targets.contractId() == null ? "" : "var:xfm_contract = scope:xfma_context.var:xfma_contract ";
            source.append("""
                    if = {
                        limit = { NOT = { exists = var:xfma_position } exists = story_owner.var:xfm_futures_selected_position }
                        story_owner.var:xfm_futures_selected_position = {
                            if = {
                                limit = { story_type = xfm_futures_position var:xfm_coin = scope:xfma_context.var:xfma_coin ${SELECTED_CONTRACT} OR = { var:xfm_long_account = scope:xfma_context.var:xfma_account var:xfm_short_account = scope:xfma_context.var:xfma_account } }
                                scope:xfma_context = { set_variable = { name = xfma_position value = prev } ${BIND_CONTRACT} }
                            }
                        }
                    }
                    """.replace("${SELECTED_CONTRACT}", selectedContract).replace("${BIND_CONTRACT}", targets.contractId() == null ? "set_variable = { name = xfma_contract value = prev.var:xfm_contract }" : ""));
        }
        source.append(lookup("debt", "every_in_global_list", "xfm_debts_archive", "xfm_debt_id", targets.debtId(), null));
        if (targets.debtId() == null && request.caseId() == Profile.DERIVATIVES) {
            for (int kind = 1; kind <= 4; kind++) source.append("if = { limit = { NOT = { exists = var:xfma_debt } exists = var:xfma_position.var:xfm_debt_receipt_")
                    .append(kind).append(" } set_variable = { name = xfma_debt value = var:xfma_position.var:xfm_debt_receipt_").append(kind).append(" } }\n");
        }
        source.append(lookup("news", "every_in_global_list", "xfm_news_entries", "xfm_news_id", targets.newsId(), null));
        if (targets.newsId() == null && request.caseId() == Profile.NEWS_CRISIS) source.append("""
                if = {
                    limit = { NOT = { exists = var:xfma_news } has_variable = xfma_start_news_counter global_var:xfm_exchange.var:xfm_news_counter > var:xfma_start_news_counter }
                    ordered_in_global_list = {
                        variable = xfm_news_entries
                        limit = { var:xfm_news_id > scope:xfma_context.var:xfma_start_news_counter }
                        order_by = var:xfm_news_id
                        max = 1
                        check_range_bounds = no
                        scope:xfma_context = { set_variable = { name = xfma_news value = prev } }
                    }
                }
                """);
        return source.toString();
    }

    private static String lookup(String target, String iterator, String list, String field, String id, String parent) {
        if (id == null) return "";
        return "if = { limit = { NOT = { exists = var:xfma_" + target + " } }\n"
                + (parent == null ? "" : parent + " = {\n")
                + iterator + " = { variable = " + list + " limit = { has_variable = " + field + " var:" + field + " = " + id + " }\n"
                + "scope:xfma_context = { set_variable = { name = xfma_" + target + " value = prev } }\n}\n"
                + (parent == null ? "" : "}\n") + "}\n";
    }

    private static String ownerDeath(Request request) {
        if (request.caseId() != Profile.INHERITANCE) return "debug_log = \"XFMAT: TEST FAIL followup_operator_died\"";
        return """
                save_scope_as = xfma_context
                clear_saved_scope = xfma_next_operator
                story_owner = {
                    if = { limit = { exists = primary_heir primary_heir != this primary_heir = { is_alive = yes } } primary_heir = { save_scope_as = xfma_next_operator } }
                }
                if = {
                    limit = { exists = scope:xfma_next_operator }
                    make_story_owner = scope:xfma_next_operator
                    scope:xfma_next_operator = { set_variable = { name = ${P}_story value = scope:xfma_context } set_variable = { name = ${P}_armed value = 1 } }
                    set_variable = { name = xfma_operator_succeeded value = 1 }
                }
                else = { set_variable = { name = xfma_operator_ended_without_heir value = 1 } }
                """;
    }

    private static String associations(Request request) {
        boolean asset = request.targets().coinId() != null || request.targets().indexId() != null;
        String assetContract = asset ? "var:xfm_coin = scope:xfma_context.var:xfma_coin\n" : "";
        String result = "OR = { NOT = { exists = var:xfma_contract } var:xfma_contract = { " + assetContract + " } }\n"
                + "OR = { NOT = { exists = var:xfma_position } var:xfma_position = {\n"
                + "story_type = xfm_futures_position var:xfm_contract = scope:xfma_context.var:xfma_contract\n" + assetContract
                + "OR = { var:xfm_long_account = scope:xfma_context.var:xfma_account var:xfm_short_account = scope:xfma_context.var:xfma_account }\n} }\n";
        String debt = switch (request.caseId()) {
            case DERIVATIVES -> "var:xfm_source = scope:xfma_context.var:xfma_position\nvar:xfm_coin = scope:xfma_context.var:xfma_coin\n"
                    + "OR = { AND = { var:xfm_debtor_account = scope:xfma_context.var:xfma_position.var:xfm_long_account var:xfm_creditor_account = scope:xfma_context.var:xfma_position.var:xfm_short_account } AND = { var:xfm_debtor_account = scope:xfma_context.var:xfma_position.var:xfm_short_account var:xfm_creditor_account = scope:xfma_context.var:xfma_position.var:xfm_long_account } }\n";
            case LIFECYCLE -> "var:xfm_coin = scope:xfma_context.var:xfma_coin\n";
            case INHERITANCE -> "OR = { var:xfm_debtor_account = scope:xfma_context.var:xfma_account var:xfm_creditor_account = scope:xfma_context.var:xfma_account }\n";
            case NEWS_CRISIS -> "var:xfm_debtor_account = scope:xfma_context.var:xfma_account\n";
            case COLD_RELOAD, AI_CAPACITY -> "always = yes\n";
        };
        return result + "OR = { NOT = { exists = var:xfma_debt } var:xfma_debt = { " + debt + " } }\n";
    }

    private static String profile(Request request) {
        String body = switch (request.caseId()) {
            case DERIVATIVES -> derivatives(request);
            case LIFECYCLE -> lifecycle(request);
            case INHERITANCE -> inheritance(request);
            case COLD_RELOAD -> cold(request);
            case NEWS_CRISIS -> news(request);
            case AI_CAPACITY -> capacity(request);
        };
        return "${P}_profile_effect = {\n" + body + "\n}\n";
    }

    private static String derivatives(Request request) {
        return once(request, "paired_position_readback", """
                exists = var:xfma_position
                var:xfma_position = {
                    story_type = xfm_futures_position
                    has_variable = xfm_position_id has_variable = xfm_contract_id
                    var:xfm_position_id > 0 var:xfm_contract_id > 0 var:xfm_lots > 0
                    var:xfm_contract = scope:xfma_context.var:xfma_contract
                    exists = var:xfm_long_account exists = var:xfm_short_account
                    var:xfm_long_account != var:xfm_short_account
                    exists = var:xfm_long_reservation exists = var:xfm_short_reservation
                    var:xfm_long_reservation.var:xfm_account = var:xfm_long_account
                    var:xfm_short_reservation.var:xfm_account = var:xfm_short_account
                    var:xfm_long_reservation.var:xfm_remaining_cents > 0
                    var:xfm_short_reservation.var:xfm_remaining_cents > 0
                }
                """) + once(request, "settled_after_baseline", """
                has_variable = xfma_seen_paired_position_readback
                var:xfma_position = { has_variable = xfm_last_settled_day var:xfm_last_settled_day > scope:xfma_context.var:xfma_start_day }
                """) + claim(request);
    }

    private static String claim(Request request) {
        return once(request, "claim_accounting_readback", "exists = var:xfma_debt\nvar:xfma_debt = {\nstory_type = xfm_debt_claim\n"
                + fields("xfm_original_cents", "xfm_outstanding_cents", "xfm_winner_unpaid_cents", "xfm_fund_recourse_cents", "xfm_repaid_cents", "xfm_written_off_cents", "xfm_source_day", "xfm_source_kind")
                + """
                var:xfm_original_cents > 0
                var:xfm_outstanding_cents >= 0 var:xfm_winner_unpaid_cents >= 0 var:xfm_fund_recourse_cents >= 0
                var:xfm_outstanding_cents >= ${P}_claim_split_value
                var:xfm_outstanding_cents <= ${P}_claim_split_value
                var:xfm_original_cents >= ${P}_claim_principal_value
                var:xfm_original_cents <= ${P}_claim_principal_value
                exists = var:xfm_debtor_account exists = var:xfm_creditor_account exists = var:xfm_source
                }
                """);
    }

    private static String lifecycle(Request request) {
        return once(request, "new_notice_readback", """
                var:xfma_coin = {
                    has_variable = xfm_notice_day var:xfm_notice_day > scope:xfma_context.var:xfma_start_notice_day
                    var:xfm_notice_day >= scope:xfma_context.var:xfma_start_day
                    var:xfm_listing_state = 3 var:xfm_derivatives_reduce_only = 1
                }
                """) + once(request, "exit_state_after_notice", """
                has_variable = xfma_seen_new_notice_readback
                var:xfma_coin = {
                    var:xfm_delisting_age >= 21 var:xfm_trading_open = 0
                    OR = { var:xfm_listing_state = 5 var:xfm_listing_state = 6 var:xfm_listing_state = 7 var:xfm_listing_state = 8 }
                }
                """) + once(request, "surviving_claim_readback", """
                has_variable = xfma_seen_exit_state_after_notice
                exists = var:xfma_debt
                var:xfma_debt = { var:xfm_coin = scope:xfma_context.var:xfma_coin var:xfm_outstanding_cents > 0 }
                var:xfma_coin = { var:xfm_unresolved_claim_count > 0 NOT = { var:xfm_listing_state = 7 } }
                """);
    }

    private static String inheritance(Request request) {
        return once(request, "original_holder_died", "exists = var:xfma_holder_before\nvar:xfma_holder_before = { is_alive = no }\n")
                + once(request, "account_inherited_or_frozen", """
                has_variable = xfma_seen_original_holder_died
                var:xfma_account = {
                    OR = {
                        AND = { var:xfm_inheritance_state = 1 var:xfm_holder = scope:xfma_context.var:xfma_heir_before }
                        AND = { var:xfm_inheritance_state = 2 var:xfm_account_frozen = 1 var:xfm_holder = scope:xfma_context.var:xfma_holder_before }
                    }
                }
                """) + once(request, "original_claim_reference_survives", """
                has_variable = xfma_seen_account_inherited_or_frozen
                exists = var:xfma_debt_before var:xfma_debt = var:xfma_debt_before
                var:xfma_debt = {
                    has_variable = xfm_debt_id has_variable = xfm_source_day exists = var:xfm_source
                    OR = { var:xfm_debtor_account = scope:xfma_context.var:xfma_account var:xfm_creditor_account = scope:xfma_context.var:xfma_account }
                }
                """);
    }

    private static String cold(Request request) {
        var baseline = request.coldBaseline();
        var account = baseline.account();
        StringBuilder checks = new StringBuilder("global_var:xfm_exchange.var:xfm_day = " + baseline.day() + "\nvar:xfma_start_date = current_date\n");
        checks.append("var:xfma_account = {\n").append(eq("xfm_account_id", Long.parseLong(request.targets().accountId())))
                .append(eq("xfm_free_cents", account.freeCents())).append(eq("xfm_reserved_cents", account.reservedCents()))
                .append(eq("xfm_system_account", account.systemAccount())).append(eq("xfm_inheritance_state", account.inheritanceState()))
                .append(eq("xfm_account_frozen", account.frozen())).append("}\n");
        if (baseline.coin() != null) checks.append("var:xfma_coin = {\n")
                .append(eq("xfm_coin_id", Long.parseLong(request.targets().coinId()))).append(eq("xfm_supply_units", baseline.coin().supplyUnits()))
                .append(eq("xfm_listing_state", baseline.coin().listingState())).append(eq("xfm_price_version", baseline.coin().priceVersion())).append("}\n");
        if (baseline.position() != null) {
            var position = baseline.position();
            checks.append("var:xfma_position = {\n").append(eq("xfm_position_id", Long.parseLong(request.targets().positionId())))
                    .append(eq("xfm_contract_id", Long.parseLong(request.targets().contractId()))).append(eq("xfm_lots", position.lots()))
                    .append(eq("xfm_mark_cents", position.markCents())).append(eq("xfm_status", position.status()))
                    .append(eq("xfm_created_day", position.createdDay())).append(eq("xfm_last_settled_day", position.settledDay()))
                    .append("var:xfm_long_account = { ").append(eq("xfm_account_id", Long.parseLong(position.longAccountId()))).append(" }\n")
                    .append("var:xfm_short_account = { ").append(eq("xfm_account_id", Long.parseLong(position.shortAccountId()))).append(" }\n")
                    .append("var:xfm_long_reservation = { ").append(eq("xfm_reservation_id", position.longReservationId())).append(eq("xfm_remaining_cents", position.longRemainingCents())).append(" }\n")
                    .append("var:xfm_short_reservation = { ").append(eq("xfm_reservation_id", position.shortReservationId())).append(eq("xfm_remaining_cents", position.shortRemainingCents())).append(" }\n}\n");
        }
        if (baseline.debt() != null) {
            var debt = baseline.debt();
            checks.append("var:xfma_debt = {\n").append(eq("xfm_debt_id", Long.parseLong(request.targets().debtId())))
                    .append(eq("xfm_original_cents", debt.originalCents())).append(eq("xfm_outstanding_cents", debt.outstandingCents()))
                    .append(eq("xfm_winner_unpaid_cents", debt.winnerUnpaidCents())).append(eq("xfm_fund_recourse_cents", debt.fundRecourseCents()))
                    .append(eq("xfm_fund_paid_cents", debt.fundPaidCents())).append(eq("xfm_repaid_cents", debt.repaidCents()))
                    .append(eq("xfm_written_off_cents", debt.writtenOffCents())).append(eq("xfm_source_day", debt.sourceDay()))
                    .append(eq("xfm_source_kind", debt.sourceKind())).append(eq("xfm_due_day", debt.dueDay()))
                    .append("var:xfm_debtor_account = { ").append(eq("xfm_account_id", Long.parseLong(debt.debtorAccountId()))).append(" }\n")
                    .append("var:xfm_creditor_account = { ").append(eq("xfm_account_id", Long.parseLong(debt.creditorAccountId()))).append(" }\n}\n");
        }
        return "if = { limit = {\n" + checks + "} } else = { debug_log = \"XFMAT: TEST FAIL cold_watched_sample_mismatch_or_date_advanced\" }\n"
                + once(request, "loaded_sample_matches_baseline", checks.toString())
                + once(request, "same_day_refresh_sample_unchanged", "var:xfma_refreshes >= 2\n" + checks);
    }

    private static String news(Request request) {
        return claim(request) + once(request, "crisis_or_relief_readback", """
                var:xfma_account = {
                    OR = { AND = { has_variable = xfm_crisis_state var:xfm_crisis_state >= 1 } AND = { has_variable = xfm_crisis_relief_until var:xfm_crisis_relief_until > global_var:xfm_exchange.var:xfm_day } }
                }
                """) + once(request, "new_world_fact_after_baseline", """
                exists = var:xfma_news
                var:xfma_news = {
                    has_variable = xfm_news_id var:xfm_news_id > scope:xfma_context.var:xfma_start_news_counter
                    exists = var:xfm_news_source exists = var:xfm_news_actor
                    has_variable = xfm_news_event_id has_variable = xfm_news_kind has_variable = xfm_news_day
                    var:xfm_news_day >= scope:xfma_context.var:xfma_start_day
                }
                """) + """
                set_variable = { name = xfma_human_count value = 0 }
                set_variable = { name = xfma_delivery_errors value = 0 }
                every_player = {
                    scope:xfma_context = { change_variable = { name = xfma_human_count add = 1 } }
                    if = {
                        limit = { OR = { NOT = { has_variable = xfm_news_delivery_day } NOT = { has_variable = xfm_news_sent_today } var:xfm_news_sent_today < 0 var:xfm_news_sent_today > 3 } }
                        scope:xfma_context = { change_variable = { name = xfma_delivery_errors add = 1 } }
                    }
                }
                """ + once(request, "delivery_state_bounded_readback", "var:xfma_human_count > 0\nvar:xfma_delivery_errors = 0\nhas_variable = xfma_seen_new_world_fact_after_baseline\n");
    }

    private static String capacity(Request request) {
        return """
                if = { limit = { global_var:xfm_exchange = { has_variable = xfm_active_coin_count } } set_variable = { name = xfma_active_coins_readback value = global_var:xfm_exchange.var:xfm_active_coin_count } }
                if = { limit = { global_var:xfm_exchange = { has_variable = xfm_futures_open_positions_count } } set_variable = { name = xfma_open_positions_readback value = global_var:xfm_exchange.var:xfm_futures_open_positions_count } }
                if = { limit = { global_var:xfm_exchange = { has_variable = xfm_ai_count } } set_variable = { name = xfma_ai_queue_readback value = global_var:xfm_exchange.var:xfm_ai_count } }
                """ + once(request, "declared_inventory_readback", "global_var:xfm_exchange = { has_variable = xfm_active_coin_count has_variable = xfm_futures_open_positions_count var:xfm_active_coin_count >= "
                + request.scaleTier().coins() + " var:xfm_futures_open_positions_count >= " + request.scaleTier().positions() + " }\n")
                + once(request, "ai_paid_issuance_readback", """
                var:xfma_coin = { var:xfm_original_issuer = { is_ai = yes is_adult = yes } has_variable = xfm_registration_paid_cents var:xfm_registration_paid_cents > 0 exists = var:xfm_issuer_account }
                """) + once(request, "365_daily_samples_after_warmup", """
                NOT = { has_variable = xfma_sample_gap }
                var:xfma_daily_samples >= 395 var:xfma_measured_samples >= 365
                global_var:xfm_exchange.var:xfm_day >= { value = var:xfma_start_day add = 395 }
                has_variable = xfma_seen_declared_inventory_readback
                """);
    }

    private static String once(Request request, String observation, String predicate) {
        return "if = { limit = { NOT = { has_variable = xfma_seen_" + observation + " }\n" + predicate
                + "}\nset_variable = { name = xfma_seen_" + observation + " value = 1 }\ndebug_log = \"" + marker(request, observation) + "\"\n}\n";
    }
    private static String marker(Request request, String observation) { return "XFMAT: TEST PASS " + request.caseId().scriptKey() + "_" + observation; }
    private static String fields(String... fields) { return String.join("\n", List.of(fields).stream().map(field -> "has_variable = " + field).toList()) + "\n"; }
    private static String eq(String field, long value) { return "has_variable = " + field + " var:" + field + " = " + value + "\n"; }
}
