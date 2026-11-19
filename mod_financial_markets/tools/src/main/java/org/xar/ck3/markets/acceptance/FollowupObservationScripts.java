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
                """ + spotScopeProbeGuis(request));
        scripts.put("gui/scripted_widgets/" + prefix + ".txt", "gui/" + prefix + ".gui = xfma_observer_widget\n");
        scripts.put("gui/" + prefix + ".gui", """
                window = {
                    name = "xfma_observer_widget"
                    parentanchor = top|right
                    position = { -290 130 }
                    size = { 220 ${SCOPE_PROBE_HEIGHT} }
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
                    ${SCOPE_VALUE_PROBE}
                }
                """);
        scripts.put("localization/english/" + prefix + "_l_english.yml", """
                l_english:
                 xfma_followup_arm_label:0 "Record observation baseline"
                 xfma_followup_refresh_label:0 "Read watched market facts"
                 xfma_scope_probe_positive_label:0 "Read-only ID > 0"
                 xfma_scope_probe_negative_label:0 "Read-only ID < 0"
                """);
        scripts.put("localization/simp_chinese/" + prefix + "_l_simp_chinese.yml", """
                l_simp_chinese:
                 xfma_followup_arm_label:0 "记录只读观察基线"
                 xfma_followup_refresh_label:0 "读回所观察的市场事实"
                 xfma_scope_probe_positive_label:0 "只读 ID > 0"
                 xfma_scope_probe_negative_label:0 "只读 ID < 0"
                """);
        scripts.put("common/story_cycles/" + prefix + ".txt", "${P}_observer = {\n visible = no\n on_owner_death = {\n"
                + ownerDeath(request) + "\n }\n effect_group = { days = 1 triggered_effect = { trigger = { exists = story_owner } effect = { ${P}_observe_effect = yes } } }\n}\n"
                + passiveCompatibilityStories(request.prefix() + "_observer"));
        scripts.put("common/scripted_triggers/" + prefix + ".txt", "${P}_associations_trigger = {\n" + associations(request) + "\n}\n");
        if (request.caseId() == Profile.DERIVATIVES || request.caseId() == Profile.NEWS_CRISIS) {
            scripts.put("common/script_values/" + prefix + ".txt", """
                    # Debt-story scope. Pure sums preserve exact accounting without equality-to-block dispatch.
                    ${P}_claim_split_value = { value = var:xfm_winner_unpaid_cents add = var:xfm_fund_recourse_cents }
                    ${P}_claim_principal_value = { value = var:xfm_outstanding_cents add = var:xfm_repaid_cents add = var:xfm_written_off_cents }
                    """);
        }
        if (request.caseId() == Profile.SPOT) scripts.put("common/script_values/" + prefix + ".txt", """
                ${P}_next_sample_day_value = { value = var:xfma_last_sample_day add = 1 }
                ${P}_spot_expected_fee_value = { value = var:xfm_filled_notional_cents multiply = 0.003 ceiling = yes min = 1 }
                """);
        if (request.caseId() == Profile.MARKET_EVOLUTION)
            scripts.put("common/script_values/" + prefix + ".txt", Evolution.values());
        scripts.put("common/scripted_effects/" + prefix + "_observe.txt", common(request) + profile(request)
                + (request.caseId() == Profile.MARKET_EVOLUTION ? Evolution.effects() : ""));
        Map<String, byte[]> result = new LinkedHashMap<>();
        scripts.forEach((name, source) -> result.put(name, ("\ufeff" + source.replace("${P}", prefix)
                .replace("${ACTOR}", actorCondition(request))
                .replace("${SCOPE_PROBE_HEIGHT}", request.caseId() == Profile.SPOT ? "560" : "82")
                .replace("${SCOPE_VALUE_PROBE}", spotScopeProbeWidget(request).replace("${P}", prefix))
                .replace("${NEXT_SAMPLE_DAY}", request.caseId() == Profile.SPOT || request.caseId() == Profile.MARKET_EVOLUTION
                        ? prefix + "_next_sample_day_value" : "{ value = var:xfma_last_sample_day add = 1 }")).getBytes(StandardCharsets.UTF_8)));
        return Map.copyOf(result);
    }

    /**
     * Diagnostic only: emit the numeric MakeScopeValue chain in a real GetList item.
     * Neither branch has an effect. Actual parser/validity evidence must precede any product use.
     */
    private static String spotScopeProbeGuis(Request request) {
        if (request.caseId() != Profile.SPOT) return "";
        return """
                ${P}_scope_id_positive_gui = {
                    scope = character
                    saved_scopes = { xfma_probe_order_id }
                    is_valid = { is_ai = no is_alive = yes exists = scope:xfma_probe_order_id scope:xfma_probe_order_id > 0 }
                }
                ${P}_scope_id_negative_gui = {
                    scope = character
                    saved_scopes = { xfma_probe_order_id }
                    is_valid = { is_ai = no is_alive = yes exists = scope:xfma_probe_order_id scope:xfma_probe_order_id < 0 }
                }
                """;
    }

    private static String spotScopeProbeWidget(Request request) {
        if (request.caseId() != Profile.SPOT) return "";
        return """
                vbox = {
                    name = "xfma_scope_value_probe"
                    position = { 0 86 }
                    size = { 220 470 }
                    spacing = 2
                    datamodel = "[DataModelSubSpan( GetPlayer.MakeScope.Var( 'xfm_active_account' ).GetList( 'xfm_order_history' ), Min_int32( FixedPointToInt( GetPlayer.MakeScope.Var( 'xfm_ui_history_offset' ).GetValue ), GetDataModelSize( GetPlayer.MakeScope.Var( 'xfm_active_account' ).GetList( 'xfm_order_history' ) ) ), Max_int32( '(int32)0', Min_int32( '(int32)16', Subtract_int32( GetDataModelSize( GetPlayer.MakeScope.Var( 'xfm_active_account' ).GetList( 'xfm_order_history' ) ), Min_int32( FixedPointToInt( GetPlayer.MakeScope.Var( 'xfm_ui_history_offset' ).GetValue ), GetDataModelSize( GetPlayer.MakeScope.Var( 'xfm_active_account' ).GetList( 'xfm_order_history' ) ) ) ) ) ) )]"
                    item = {
                        hbox = {
                            size = { 220 26 }
                            spacing = 4
                            button_standard = {
                                name = "xfma_scope_probe_positive"
                                size = { 108 24 }
                                text = "xfma_scope_probe_positive_label"
                                enabled = "[GetScriptedGui( '${P}_scope_id_positive_gui' ).IsValid( GuiScope.SetRoot( GetPlayer.MakeScope ).AddScope( 'xfma_probe_order_id', MakeScopeValue( Scope.Var( 'xfm_order_id' ).GetValue ) ).End )]"
                            }
                            button_standard = {
                                name = "xfma_scope_probe_negative"
                                size = { 108 24 }
                                text = "xfma_scope_probe_negative_label"
                                enabled = "[GetScriptedGui( '${P}_scope_id_negative_gui' ).IsValid( GuiScope.SetRoot( GetPlayer.MakeScope ).AddScope( 'xfma_probe_order_id', MakeScopeValue( Scope.Var( 'xfm_order_id' ).GetValue ) ).End )]"
                            }
                        }
                    }
                }
                """;
    }

    /**
     * Retain core and the known finite schema-two epochs: spot one through three, other profiles one/two.
     * Passive declarations deliberately have no callbacks, markers, writes, or end_story operation.
     * This finite compatibility catalog does not claim to cover arbitrary historical epochs.
     */
    private static String passiveCompatibilityStories(String activeType) {
        StringBuilder source = new StringBuilder("# Passive compatibility: preserve old observation data without running an old case.\n"
                + "xfma_observer = { visible = no }\n");
        for (Profile profile : Profile.values()) {
            for (int epoch : profile == Profile.SPOT ? List.of(1, 2, 3) : List.of(1, 2)) {
                String type = "xfma_" + profile.scriptKey() + "_e" + epoch + "_observer";
                if (!type.equals(activeType)) source.append(type).append(" = { visible = no }\n");
            }
        }
        for (String type : marketEvolutionRecordTypes()) source.append(type).append(" = { visible = no }\n");
        return source.toString();
    }

    static List<String> marketEvolutionRecordTypes() {
        return List.of("xfma_market_evolution_day_record", "xfma_market_evolution_coin_record");
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
        if (request.caseId() == Profile.SPOT) required += "global_var:xfm_exchange = { has_variable = xfm_next_order_id }\n"
                + "var:xfma_coin = { story_type = xfm_finance_coin has_variable = xfm_supply_units has_variable = xfm_actual_trades var:xfm_trading_open = 1 var:xfm_listing_state >= 1 var:xfm_listing_state < 5 }\n"
                + "var:xfma_account.var:xfm_holder = story_owner\n";
        if (request.caseId() == Profile.MARKET_EVOLUTION) {
            required += "var:xfma_account = { var:xfm_system_account = 0 var:xfm_holder = scope:xfma_context.story_owner }\n"
                    + "var:xfma_coin = { story_type = xfm_finance_coin has_variable = xfm_coin_id }\n";
            if (request.targets().contractId() != null)
                required += "var:xfma_contract = { story_type = xfm_futures_contract has_variable = xfm_contract_id has_variable = xfm_expiry_day var:xfm_perpetual = 0 }\n";
        }
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
                + spotArm(request)
                + (request.caseId() == Profile.MARKET_EVOLUTION ? Evolution.arm() : "")
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
                            if = { limit = { global_var:xfm_exchange.var:xfm_day > ${NEXT_SAMPLE_DAY} } set_variable = { name = xfma_sample_gap value = 1 } }
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
        String assetContract = asset && request.caseId() != Profile.MARKET_EVOLUTION
                ? "var:xfm_coin = scope:xfma_context.var:xfma_coin\n" : "";
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
            case SPOT, COLD_RELOAD, AI_CAPACITY, MARKET_EVOLUTION -> "always = yes\n";
        };
        return result + "OR = { NOT = { exists = var:xfma_debt } var:xfma_debt = { " + debt + " } }\n";
    }

    private static String spotArm(Request request) {
        if (request.caseId() != Profile.SPOT) return "";
        return """
                set_variable = { name = xfma_start_order_id value = global_var:xfm_exchange.var:xfm_next_order_id }
                set_variable = { name = xfma_start_supply_units value = var:xfma_coin.var:xfm_supply_units }
                set_variable = { name = xfma_start_actual_trades value = var:xfma_coin.var:xfm_actual_trades }
                set_variable = { name = xfma_start_free_cents value = var:xfma_account.var:xfm_free_cents }
                set_variable = { name = xfma_start_reserved_cents value = var:xfma_account.var:xfm_reserved_cents }
                """;
    }

    private static String spotOrderGuard() {
        return """
                story_type = xfm_spot_order
                has_variable = xfm_order_id var:xfm_order_id > scope:xfma_context.var:xfma_start_order_id
                var:xfm_account = scope:xfma_context.var:xfma_account
                var:xfm_coin = scope:xfma_context.var:xfma_coin
                """;
    }

    private static String spot(Request request) {
        StringBuilder source = new StringBuilder();
        // No result=0 marker: a repeated identical rejection has no production sequence to distinguish it from saved state.
        for (String input : List.of("xfm_result_order", "xfm_selected_order")) {
            for (int side = 1; side <= 2; side++) {
                String target = side == 1 ? "xfma_buy_order" : "xfma_sell_order";
                source.append("if = { limit = { NOT = { exists = var:").append(target)
                        .append(" } exists = story_owner.var:").append(input).append(" story_owner.var:").append(input).append(" = {\n")
                        .append(spotOrderGuard()).append("has_variable = xfm_side var:xfm_side = ").append(side)
                        .append(" has_variable = xfm_filled_lots var:xfm_filled_lots > 0\n} }\n")
                        .append("set_variable = { name = ").append(target).append(" value = story_owner.var:").append(input).append(" } }\n");
            }
            source.append("if = { limit = { NOT = { exists = var:xfma_partial_order } exists = story_owner.var:")
                    .append(input).append(" story_owner.var:").append(input).append(" = {\n").append(spotOrderGuard())
                    .append(fields("xfm_original_lots", "xfm_filled_lots", "xfm_cancelled_lots", "xfm_remaining_lots", "xfm_status", "xfm_finalized"))
                    .append("var:xfm_filled_lots > 0 var:xfm_original_lots > var:xfm_filled_lots var:xfm_cancelled_lots > 0 var:xfm_remaining_lots = 0 var:xfm_status = 3 var:xfm_finalized = 1\n} }\n")
                    .append("set_variable = { name = xfma_partial_order value = story_owner.var:").append(input).append(" } }\n");
        }
        source.append(once(request, "watched_sample_readback", """
                has_variable = xfma_start_supply_units
                var:xfma_account = { has_variable = xfm_free_cents has_variable = xfm_reserved_cents var:xfm_free_cents >= 0 var:xfm_reserved_cents >= 0 }
                var:xfma_coin = { has_variable = xfm_supply_units var:xfm_supply_units = scope:xfma_context.var:xfma_start_supply_units }
                """));
        source.append(once(request, "new_buy_filled_readback", "exists = var:xfma_buy_order\nvar:xfma_buy_order = {\n" + spotOrderGuard()
                + "has_variable = xfm_side var:xfm_side = 1 has_variable = xfm_filled_lots var:xfm_filled_lots > 0\n}\n"));
        source.append(once(request, "new_sell_filled_readback", "exists = var:xfma_sell_order\nvar:xfma_sell_order = {\n" + spotOrderGuard()
                + "has_variable = xfm_side var:xfm_side = 2 has_variable = xfm_filled_lots var:xfm_filled_lots > 0\n}\n"));
        source.append(once(request, "partial_cancelled_readback", "exists = var:xfma_partial_order\nvar:xfma_partial_order = {\n" + spotOrderGuard()
                + fields("xfm_original_lots", "xfm_filled_lots", "xfm_cancelled_lots", "xfm_remaining_lots", "xfm_status", "xfm_finalized")
                + "var:xfm_filled_lots > 0 var:xfm_original_lots > var:xfm_filled_lots var:xfm_cancelled_lots > 0 var:xfm_remaining_lots = 0 var:xfm_status = 3 var:xfm_finalized = 1\n}\n"));
        String fee = "has_variable = xfm_filled_notional_cents has_variable = xfm_fee_paid_cents var:xfm_filled_notional_cents > 0\n"
                + "var:xfm_fee_paid_cents >= ${P}_spot_expected_fee_value\nvar:xfm_fee_paid_cents <= ${P}_spot_expected_fee_value\n";
        source.append(once(request, "original_order_fee_readback", "exists = var:xfma_buy_order exists = var:xfma_sell_order\nvar:xfma_buy_order = { "
                + fee + " }\nvar:xfma_sell_order = { " + fee + " }\n"));
        return source.toString();
    }

    private static String profile(Request request) {
        String body = switch (request.caseId()) {
            case SPOT -> spot(request);
            case DERIVATIVES -> derivatives(request);
            case LIFECYCLE -> lifecycle(request);
            case INHERITANCE -> inheritance(request);
            case COLD_RELOAD -> cold(request);
            case NEWS_CRISIS -> news(request);
            case AI_CAPACITY -> capacity(request);
            case MARKET_EVOLUTION -> Evolution.profile(request);
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

    /** Observation records are bounded, passive and never become product accounts or instruments. */
    private static final class Evolution {
        private Evolution() { }
        static String values() {
            return """
                    ${P}_next_sample_day_value = { value = var:xfma_last_sample_day add = 1 }
                    ${P}_end_day_value = { value = var:xfma_start_day add = 35 }
                    """;
        }
        static String arm() {
            return """
                    set_variable = { name = xfma_evolution_coin_cursor value = 0 }
                    set_variable = { name = xfma_evolution_coin_records value = 0 }
                    set_variable = { name = xfma_evolution_day_records value = 0 }
                    set_variable = { name = xfma_expiry_source_count value = 0 }
                    set_variable = { name = xfma_expiry_due_occurred value = 0 }
                    set_variable = { name = xfma_expiry_closed_readback_occurred value = 0 }
                    set_variable = { name = xfma_evolution_start_coin_id_available value = 0 }
                    if = {
                        limit = { global_var:xfm_exchange = { has_variable = xfm_next_coin_id } }
                        set_variable = { name = xfma_evolution_start_coin_id value = global_var:xfm_exchange.var:xfm_next_coin_id }
                        set_variable = { name = xfma_evolution_start_coin_id_available value = 1 }
                    }
                    """;
        }
        static String profile(Request request) {
            return """
                    # All feature flags mean observed witnesses, never automatic feature acceptance.
                    ${P}_evolution_day_effect = yes
                    ${P}_evolution_discover_effect = yes
                    set_variable = { name = xfma_new_ai_issues_observed value = 0 }
                    set_variable = { name = xfma_new_landless_ai_issues_observed value = 0 }
                    set_variable = { name = xfma_new_low_tier_ai_issues_observed value = 0 }
                    set_variable = { name = xfma_new_listings_observed value = 0 }
                    set_variable = { name = xfma_offer_refunds_observed value = 0 }
                    set_variable = { name = xfma_fundraise_failures_observed value = 0 }
                    set_variable = { name = xfma_new_notices_observed value = 0 }
                    set_variable = { name = xfma_ai_issue_available value = var:xfma_coin_coverage_complete }
                    set_variable = { name = xfma_listing_available value = var:xfma_coin_coverage_complete }
                    set_variable = { name = xfma_refund_available value = var:xfma_coin_coverage_complete }
                    set_variable = { name = xfma_fundraise_failure_available value = var:xfma_coin_coverage_complete }
                    set_variable = { name = xfma_notice_available value = var:xfma_coin_coverage_complete }
                    if = { limit = { var:xfma_evolution_start_coin_id_available = 0 } set_variable = { name = xfma_ai_issue_available value = 0 } }
                    every_in_list = {
                        variable = xfma_evolution_coins
                        ${P}_evolution_coin_effect = yes
                        if = { limit = { OR = { var:xfma_first_issuer_available = 0 var:xfma_first_registration_paid_cents_available = 0 } } scope:xfma_context = { set_variable = { name = xfma_ai_issue_available value = 0 } } }
                        if = { limit = { var:xfma_latest_listing_state_available = 0 } scope:xfma_context = { set_variable = { name = xfma_listing_available value = 0 } set_variable = { name = xfma_notice_available value = 0 } set_variable = { name = xfma_fundraise_failure_available value = 0 } } }
                        if = { limit = { var:xfma_latest_listing_state_available = 1 var:xfma_latest_listing_state >= 1 var:xfma_latest_listing_state <= 3 var:xfma_latest_listed_day_available = 0 } scope:xfma_context = { set_variable = { name = xfma_listing_available value = 0 } } }
                        if = { limit = { var:xfma_subscriptions_available = 0 } scope:xfma_context = { set_variable = { name = xfma_refund_available value = 0 } } }
                        if = { limit = { var:xfma_new_ai_issue_occurred = 1 } scope:xfma_context = { change_variable = { name = xfma_new_ai_issues_observed add = 1 } } }
                        if = { limit = { var:xfma_new_ai_issue_occurred = 1 var:xfma_first_issuer_landless = 1 } scope:xfma_context = { change_variable = { name = xfma_new_landless_ai_issues_observed add = 1 } } }
                        if = { limit = { var:xfma_new_ai_issue_occurred = 1 var:xfma_first_issuer_rank_available = 1 var:xfma_first_issuer_rank <= 2 } scope:xfma_context = { change_variable = { name = xfma_new_low_tier_ai_issues_observed add = 1 } } }
                        if = { limit = { var:xfma_new_listing_occurred = 1 } scope:xfma_context = { change_variable = { name = xfma_new_listings_observed add = 1 } } }
                        if = { limit = { var:xfma_refund_readback_occurred = 1 } scope:xfma_context = { change_variable = { name = xfma_offer_refunds_observed add = 1 } } }
                        if = { limit = { var:xfma_fundraise_failed_occurred = 1 } scope:xfma_context = { change_variable = { name = xfma_fundraise_failures_observed add = 1 } } }
                        if = { limit = { var:xfma_new_notice_occurred = 1 } scope:xfma_context = { change_variable = { name = xfma_new_notices_observed add = 1 } } }
                    }
                    set_variable = { name = xfma_ai_issue_occurred value = 0 }
                    set_variable = { name = xfma_listing_occurred value = 0 }
                    set_variable = { name = xfma_refund_occurred value = 0 }
                    set_variable = { name = xfma_notice_occurred value = 0 }
                    set_variable = { name = xfma_fundraise_failure_occurred value = 0 }
                    if = { limit = { var:xfma_new_ai_issues_observed > 0 } set_variable = { name = xfma_ai_issue_occurred value = 1 } }
                    if = { limit = { var:xfma_new_listings_observed > 0 } set_variable = { name = xfma_listing_occurred value = 1 } }
                    if = { limit = { var:xfma_offer_refunds_observed > 0 } set_variable = { name = xfma_refund_occurred value = 1 } }
                    if = { limit = { var:xfma_fundraise_failures_observed > 0 } set_variable = { name = xfma_fundraise_failure_occurred value = 1 } }
                    if = { limit = { var:xfma_new_notices_observed > 0 } set_variable = { name = xfma_notice_occurred value = 1 } }
                    ${P}_evolution_expiry_effect = yes
                    set_variable = { name = xfma_fact_summary_available value = 1 }
                    """ + once(request, "baseline_inventory_captured", "var:xfma_baseline_inventory_available = 1\n")
                    + once(request, "availability_summary_recorded", "var:xfma_fact_summary_available = 1\nhas_variable = xfma_coin_coverage_complete\nhas_variable = xfma_ai_issue_available\nhas_variable = xfma_ai_issue_occurred\nhas_variable = xfma_listing_available\nhas_variable = xfma_listing_occurred\nhas_variable = xfma_refund_available\nhas_variable = xfma_refund_occurred\nhas_variable = xfma_notice_available\nhas_variable = xfma_notice_occurred\nhas_variable = xfma_expiry_available\nhas_variable = xfma_expiry_contract_available\nhas_variable = xfma_expiry_positions_available\n")
                    + once(request, "35_daily_samples_observed", """
                    var:xfma_baseline_inventory_available = 1
                    NOT = { has_variable = xfma_sample_gap }
                    NOT = { has_variable = xfma_record_allocation_failed }
                    var:xfma_daily_samples >= 35
                    var:xfma_evolution_day_records = 36
                    global_var:xfm_exchange.var:xfm_day >= ${P}_end_day_value
                    global_var:xfm_exchange.var:xfm_day <= ${P}_end_day_value
                    """);
        }
        static String effects() {
            return dayEffect() + discoverEffect() + coinEffect() + expiryEffect();
        }
        private static String copy(String source, String field, String destination) {
            return "set_variable = { name = " + destination + "_available value = 0 }\nremove_variable = " + destination + "\n"
                    + "if = { limit = { " + source + " = { has_variable = " + field + " } }\n"
                    + "set_variable = { name = " + destination + " value = " + source + ".var:" + field + " }\n"
                    + "set_variable = { name = " + destination + "_available value = 1 }\n}\n";
        }
        private static String copies(String source, String prefix, String... fields) {
            StringBuilder result = new StringBuilder();
            for (String field : fields) result.append(copy(source, "xfm_" + field, prefix + field));
            return result.toString();
        }
        private static String dayEffect() {
            return """
                    ${P}_evolution_day_effect = {
                        clear_saved_scope = xfma_evolution_day_record
                        if = {
                            limit = { exists = var:xfma_evolution_latest_day var:xfma_evolution_latest_day = { var:xfma_financial_day = global_var:xfm_exchange.var:xfm_day } }
                            var:xfma_evolution_latest_day = { save_scope_as = xfma_evolution_day_record }
                        }
                        else_if = {
                            limit = { var:xfma_evolution_day_records < 36 global_var:xfm_exchange.var:xfm_day <= ${P}_end_day_value }
                            story_owner = { create_story = { type = xfma_market_evolution_day_record save_scope_as = xfma_evolution_day_record } }
                            if = {
                                limit = { exists = scope:xfma_evolution_day_record scope:xfma_evolution_day_record = { story_type = xfma_market_evolution_day_record } }
                                change_variable = { name = xfma_evolution_day_records add = 1 }
                                set_variable = { name = xfma_evolution_latest_day value = scope:xfma_evolution_day_record }
                                add_to_variable_list = { name = xfma_evolution_days target = scope:xfma_evolution_day_record }
                                scope:xfma_evolution_day_record = {
                                    set_variable = { name = xfma_observer value = scope:xfma_context }
                                    set_variable = { name = xfma_record_id value = scope:xfma_context.var:xfma_evolution_day_records }
                                    set_variable = { name = xfma_financial_day value = global_var:xfm_exchange.var:xfm_day }
                                    set_variable = { name = xfma_first_native_date value = current_date }
                    """ + copies("global_var:xfm_exchange", "xfma_first_", "next_coin_id", "registered_coin_count", "pending_coin_count", "active_coin_count", "fee_cents")
                    + """
                                }
                            }
                            else = { set_variable = { name = xfma_record_allocation_failed value = 1 } debug_log = "XFMAT: TEST FAIL evolution_day_record_allocation_failed" }
                        }
                        if = {
                            limit = { exists = scope:xfma_evolution_day_record }
                            scope:xfma_evolution_day_record = {
                                set_variable = { name = xfma_latest_native_date value = current_date }
                    """ + copies("global_var:xfm_exchange", "xfma_", "next_coin_id", "registered_coin_count", "pending_coin_count", "active_coin_count", "new_listings_today", "fee_cents", "ai_work_today", "ai_decisions_today", "ai_count", "futures_open_positions_count")
                    + copy("global_var:xfm_exchange.var:xfm_default_fund_account", "xfm_free_cents", "xfma_fund_free_cents")
                    + """
                                if = {
                                    limit = { var:xfma_record_id = 1 }
                                    scope:xfma_context = {
                                        set_variable = { name = xfma_baseline_inventory_available value = 0 }
                                        if = {
                                            limit = { scope:xfma_evolution_day_record = { var:xfma_first_next_coin_id_available = 1 var:xfma_first_registered_coin_count_available = 1 var:xfma_first_pending_coin_count_available = 1 var:xfma_first_active_coin_count_available = 1 } }
                                            set_variable = { name = xfma_baseline_inventory_available value = 1 }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    """;
        }
        private static String discoverEffect() {
            return """
                    ${P}_evolution_discover_effect = {
                        ordered_in_global_list = {
                            variable = xfm_coin_registry
                            limit = { story_type = xfm_finance_coin has_variable = xfm_coin_id var:xfm_coin_id > scope:xfma_context.var:xfma_evolution_coin_cursor scope:xfma_context = { var:xfma_evolution_coin_records < 64 } }
                            order_by = { value = 0 subtract = var:xfm_coin_id }
                            max = 64
                            check_range_bounds = no
                            if = {
                            limit = { scope:xfma_context.var:xfma_evolution_coin_records < 64 }
                            save_scope_as = xfma_evolution_source_coin
                            clear_saved_scope = xfma_evolution_coin_record
                            scope:xfma_context.story_owner = { create_story = { type = xfma_market_evolution_coin_record save_scope_as = xfma_evolution_coin_record } }
                            if = {
                                limit = { exists = scope:xfma_evolution_coin_record scope:xfma_evolution_coin_record = { story_type = xfma_market_evolution_coin_record } }
                                scope:xfma_context = {
                                    change_variable = { name = xfma_evolution_coin_records add = 1 }
                                    add_to_variable_list = { name = xfma_evolution_coins target = scope:xfma_evolution_coin_record }
                                    set_variable = { name = xfma_evolution_coin_cursor value = scope:xfma_evolution_source_coin.var:xfm_coin_id }
                                }
                                scope:xfma_evolution_coin_record = {
                                    set_variable = { name = xfma_observer value = scope:xfma_context }
                                    set_variable = { name = xfma_record_id value = scope:xfma_context.var:xfma_evolution_coin_records }
                                    set_variable = { name = xfma_coin_source value = scope:xfma_evolution_source_coin }
                                    set_variable = { name = xfma_first_financial_day value = global_var:xfm_exchange.var:xfm_day }
                                    set_variable = { name = xfma_first_native_date value = current_date }
                                    set_variable = { name = xfma_new_ai_issue_occurred value = 0 }
                                    set_variable = { name = xfma_new_listing_occurred value = 0 }
                                    set_variable = { name = xfma_refund_readback_occurred value = 0 }
                                    set_variable = { name = xfma_fundraise_failed_occurred value = 0 }
                                    set_variable = { name = xfma_new_notice_occurred value = 0 }
                                    set_variable = { name = xfma_actual_registration_transfer_verified value = 0 }
                                    set_variable = { name = xfma_subscriptions_max_seen value = 0 }
                    """ + copies("var:xfma_coin_source", "xfma_first_", "coin_id", "listing_state", "notice_day", "original_issuer", "issuer_account", "service_tier", "entity_type", "bound_entity", "controller", "registration_paid_cents", "minimum_raised_cents")
                    + issuerFirstSnapshot()
                    + """
                                }
                            }
                            else = { scope:xfma_context = { set_variable = { name = xfma_record_allocation_failed value = 1 } } debug_log = "XFMAT: TEST FAIL evolution_coin_record_allocation_failed" }
                            }
                        }
                        set_variable = { name = xfma_coin_coverage_complete value = 1 }
                        if = {
                            limit = { any_in_global_list = { variable = xfm_coin_registry OR = { NOT = { story_type = xfm_finance_coin } NOT = { has_variable = xfm_coin_id } var:xfm_coin_id > scope:xfma_context.var:xfma_evolution_coin_cursor } } }
                            set_variable = { name = xfma_coin_coverage_complete value = 0 }
                        }
                    }
                    """;
        }
        private static String issuerFirstSnapshot() {
            return """
                    set_variable = { name = xfma_first_issuer_available value = 0 }
                    set_variable = { name = xfma_first_issuer_rank_available value = 0 }
                    if = {
                        limit = { exists = var:xfma_first_original_issuer }
                        set_variable = { name = xfma_first_issuer_available value = 1 }
                        set_variable = { name = xfma_first_issuer_ai value = 0 }
                        set_variable = { name = xfma_first_issuer_adult value = 0 }
                        set_variable = { name = xfma_first_issuer_landless value = 0 }
                        var:xfma_first_original_issuer = {
                            save_scope_as = xfma_evolution_issuer
                            if = { limit = { is_ai = yes } scope:xfma_evolution_coin_record = { set_variable = { name = xfma_first_issuer_ai value = 1 } } }
                            if = { limit = { is_adult = yes } scope:xfma_evolution_coin_record = { set_variable = { name = xfma_first_issuer_adult value = 1 } } }
                            if = { limit = { is_landed = no } scope:xfma_evolution_coin_record = { set_variable = { name = xfma_first_issuer_landless value = 1 } set_variable = { name = xfma_first_issuer_rank value = 0 } set_variable = { name = xfma_first_issuer_rank_available value = 1 } } }
                            else = {
                    """ + rankBranches()
                    + """
                            }
                            if = { limit = { exists = primary_title } scope:xfma_evolution_coin_record = { set_variable = { name = xfma_first_issuer_primary_title value = scope:xfma_evolution_issuer.primary_title } } }
                            if = {
                                limit = { exists = var:xfm_account var:xfm_account = { story_type = xfm_finance_account var:xfm_system_account = 0 var:xfm_holder = scope:xfma_evolution_issuer } }
                                scope:xfma_evolution_coin_record = { set_variable = { name = xfma_first_issuer_private_account value = scope:xfma_evolution_issuer.var:xfm_account } }
                            }
                        }
                        set_variable = { name = xfma_first_issuer_gold value = var:xfma_first_original_issuer.gold }
                    }
                    """ + copies("var:xfma_first_issuer_private_account", "xfma_first_private_", "account_id", "free_cents", "reserved_cents")
                    + """
                    if = {
                        limit = { scope:xfma_context.var:xfma_evolution_start_coin_id_available = 1 var:xfma_first_coin_id_available = 1 var:xfma_first_coin_id > scope:xfma_context.var:xfma_evolution_start_coin_id var:xfma_first_issuer_available = 1 var:xfma_first_issuer_ai = 1 var:xfma_first_issuer_adult = 1 var:xfma_first_registration_paid_cents_available = 1 var:xfma_first_registration_paid_cents > 0 }
                        set_variable = { name = xfma_new_ai_issue_occurred value = 1 }
                    }
                    """;
        }
        private static String rankBranches() {
            StringBuilder source = new StringBuilder();
            String[] tiers = {"barony", "county", "duchy", "kingdom", "empire"};
            for (int i = 0; i < tiers.length; i++) source.append("if = { limit = { highest_held_title_tier = tier_").append(tiers[i])
                    .append(" } scope:xfma_evolution_coin_record = { set_variable = { name = xfma_first_issuer_rank value = ").append(i + 1)
                    .append(" } set_variable = { name = xfma_first_issuer_rank_available value = 1 } } }\n");
            source.append("if = { limit = { highest_held_title_tier > tier_empire } scope:xfma_evolution_coin_record = { set_variable = { name = xfma_first_issuer_rank value = 6 } set_variable = { name = xfma_first_issuer_rank_available value = 1 } } }\n");
            return source.toString();
        }
        private static String coinEffect() {
            return """
                    ${P}_evolution_coin_effect = {
                        save_scope_as = xfma_evolution_coin_record
                        set_variable = { name = xfma_latest_financial_day value = global_var:xfm_exchange.var:xfm_day }
                        set_variable = { name = xfma_latest_native_date value = current_date }
                    """ + copies("var:xfma_coin_source", "xfma_latest_", "coin_id", "supply_units", "listing_state", "trading_open", "asset_age", "offer_age", "listed_day", "registration_paid_cents", "actual_raised_cents", "external_raised_cents", "minimum_raised_cents", "issuer_account", "controller", "notice_day", "delisting_age", "termination_requested", "settlement_price_pending", "termination_price_certified", "unresolved_claim_count")
                    + copies("var:xfma_latest_issuer_account", "xfma_latest_project_", "account_id", "free_cents", "reserved_cents")
                    + """
                        set_variable = { name = xfma_subscriptions_available value = 1 }
                        if = { limit = { NOT = { exists = var:xfma_coin_source } } set_variable = { name = xfma_subscriptions_available value = 0 } }
                        set_variable = { name = xfma_subscriptions_sampled value = 0 }
                        set_variable = { name = xfma_subscriptions_held_cents value = 0 }
                        set_variable = { name = xfma_subscriptions_refunded value = 0 }
                        clear_variable_list = xfma_subscription_sources
                        var:xfma_coin_source = {
                            ordered_in_list = {
                                variable = xfm_subscriptions
                                order_by = { value = 0 }
                                max = 100
                                check_range_bounds = no
                                if = {
                                    limit = { scope:xfma_evolution_coin_record.var:xfma_subscriptions_sampled < 100 }
                                    save_scope_as = xfma_evolution_subscription
                                    scope:xfma_evolution_coin_record = {
                                        add_to_variable_list = { name = xfma_subscription_sources target = scope:xfma_evolution_subscription }
                                        change_variable = { name = xfma_subscriptions_sampled add = 1 }
                                    }
                                    if = {
                                        limit = { has_variable = xfm_reservation_id has_variable = xfm_subscription_state has_variable = xfm_subscription_paid_cents has_variable = xfm_remaining_cents exists = var:xfm_account var:xfm_account = { has_variable = xfm_account_id has_variable = xfm_free_cents has_variable = xfm_reserved_cents } }
                                        scope:xfma_evolution_coin_record = { change_variable = { name = xfma_subscriptions_held_cents add = scope:xfma_evolution_subscription.var:xfm_remaining_cents } }
                                        if = { limit = { var:xfm_subscription_state = 3 var:xfm_remaining_cents = 0 } scope:xfma_evolution_coin_record = { change_variable = { name = xfma_subscriptions_refunded add = 1 } } }
                                    }
                                    else = { scope:xfma_evolution_coin_record = { set_variable = { name = xfma_subscriptions_available value = 0 } } }
                                }
                                else = { scope:xfma_evolution_coin_record = { set_variable = { name = xfma_subscriptions_available value = 0 } } }
                            }
                            if = {
                                limit = { any_in_list = { variable = xfm_subscriptions NOT = { scope:xfma_evolution_coin_record = { is_target_in_variable_list = { name = xfma_subscription_sources target = prev } } } } }
                                scope:xfma_evolution_coin_record = { set_variable = { name = xfma_subscriptions_available value = 0 } }
                            }
                        }
                        if = { limit = { var:xfma_subscriptions_sampled < var:xfma_subscriptions_max_seen } set_variable = { name = xfma_subscriptions_available value = 0 } }
                        else = { set_variable = { name = xfma_subscriptions_max_seen value = var:xfma_subscriptions_sampled } }
                        if = {
                            limit = { var:xfma_latest_listing_state_available = 1 var:xfma_latest_listing_state >= 1 var:xfma_latest_listing_state <= 3 var:xfma_latest_listed_day_available = 1 var:xfma_latest_listed_day >= scope:xfma_context.var:xfma_start_day OR = { AND = { var:xfma_first_listing_state_available = 1 var:xfma_first_listing_state = 0 } AND = { scope:xfma_context.var:xfma_evolution_start_coin_id_available = 1 var:xfma_first_coin_id > scope:xfma_context.var:xfma_evolution_start_coin_id } } }
                            set_variable = { name = xfma_new_listing_occurred value = 1 }
                        }
                        if = {
                            limit = { var:xfma_latest_listing_state_available = 1 var:xfma_latest_listing_state = 6 var:xfma_coin_source = { has_variable = xfm_refund_news_recorded } OR = { var:xfma_first_listing_state = 0 AND = { scope:xfma_context.var:xfma_evolution_start_coin_id_available = 1 var:xfma_first_coin_id > scope:xfma_context.var:xfma_evolution_start_coin_id } } }
                            set_variable = { name = xfma_fundraise_failed_occurred value = 1 }
                        }
                        if = {
                            limit = { var:xfma_latest_listing_state_available = 1 var:xfma_latest_listing_state = 6 var:xfma_coin_source = { has_variable = xfm_refund_news_recorded } var:xfma_subscriptions_available = 1 var:xfma_subscriptions_sampled > 0 var:xfma_subscriptions_refunded >= var:xfma_subscriptions_sampled var:xfma_subscriptions_refunded <= var:xfma_subscriptions_sampled OR = { var:xfma_first_listing_state = 0 AND = { scope:xfma_context.var:xfma_evolution_start_coin_id_available = 1 var:xfma_first_coin_id > scope:xfma_context.var:xfma_evolution_start_coin_id } } }
                            set_variable = { name = xfma_refund_readback_occurred value = 1 }
                        }
                        if = {
                            limit = { var:xfma_latest_notice_day_available = 1 var:xfma_latest_notice_day >= scope:xfma_context.var:xfma_start_day OR = { var:xfma_first_notice_day_available = 0 var:xfma_latest_notice_day > var:xfma_first_notice_day } }
                            set_variable = { name = xfma_new_notice_occurred value = 1 }
                        }
                    }
                    """;
        }
        private static String expiryEffect() {
            return """
                    ${P}_evolution_expiry_effect = {
                        set_variable = { name = xfma_expiry_available value = 0 }
                        set_variable = { name = xfma_expiry_contract_available value = 0 }
                        set_variable = { name = xfma_expiry_positions_available value = 0 }
                        set_variable = { name = xfma_expiry_positions_sampled value = 0 }
                        set_variable = { name = xfma_expiry_open_positions value = 0 }
                        set_variable = { name = xfma_expiry_pending_positions value = 0 }
                        set_variable = { name = xfma_expiry_terminal_positions value = 0 }
                        if = {
                            limit = { exists = var:xfma_contract var:xfma_contract = { story_type = xfm_futures_contract has_variable = xfm_contract_id has_variable = xfm_perpetual has_variable = xfm_expiry_day var:xfm_perpetual = 0 } }
                            set_variable = { name = xfma_expiry_contract_available value = 1 }
                            set_variable = { name = xfma_expiry_positions_available value = 1 }
                    """ + copies("var:xfma_contract", "xfma_watched_", "contract_id", "perpetual", "expiry_day", "status", "coin")
                    + copies("var:xfma_watched_coin", "xfma_watched_asset_", "oracle_quality", "oracle_day", "mark_cents", "index_cents", "termination_requested", "settlement_price_pending", "termination_price_certified")
                    + """
                            var:xfma_contract = {
                                ordered_in_list = {
                                    variable = xfm_positions
                                    limit = { story_type = xfm_futures_position has_variable = xfm_position_id NOT = { scope:xfma_context = { is_target_in_variable_list = { name = xfma_expiry_position_sources target = prev } } } scope:xfma_context.var:xfma_expiry_source_count < 64 }
                                    order_by = { value = 0 subtract = var:xfm_position_id }
                                    max = 64
                                    check_range_bounds = no
                                    if = {
                                        limit = { scope:xfma_context.var:xfma_expiry_source_count < 64 }
                                        save_scope_as = xfma_evolution_expiry_position
                                        scope:xfma_context = { add_to_variable_list = { name = xfma_expiry_position_sources target = scope:xfma_evolution_expiry_position } change_variable = { name = xfma_expiry_source_count add = 1 } }
                                    }
                                }
                            }
                            if = { limit = { exists = var:xfma_position NOT = { is_target_in_variable_list = { name = xfma_expiry_position_sources target = var:xfma_position } } var:xfma_expiry_source_count < 64 } add_to_variable_list = { name = xfma_expiry_position_sources target = var:xfma_position } change_variable = { name = xfma_expiry_source_count add = 1 } }
                            if = {
                                limit = { var:xfma_contract = { any_in_list = { variable = xfm_positions NOT = { scope:xfma_context = { is_target_in_variable_list = { name = xfma_expiry_position_sources target = prev } } } } } }
                                set_variable = { name = xfma_expiry_positions_available value = 0 }
                            }
                            if = {
                                limit = { var:xfma_watched_expiry_day <= global_var:xfm_exchange.var:xfm_day }
                                set_variable = { name = xfma_expiry_due_occurred value = 1 }
                            }
                            every_in_list = {
                                variable = xfma_expiry_position_sources
                                if = {
                                    limit = { story_type = xfm_futures_position has_variable = xfm_position_id var:xfm_contract = scope:xfma_context.var:xfma_contract has_variable = xfm_status has_variable = xfm_last_settled_day }
                                    scope:xfma_context = { change_variable = { name = xfma_expiry_positions_sampled add = 1 } }
                                    if = { limit = { var:xfm_status = 0 } scope:xfma_context = { change_variable = { name = xfma_expiry_open_positions add = 1 } } }
                                    if = { limit = { has_variable = xfm_pending_payment } scope:xfma_context = { change_variable = { name = xfma_expiry_pending_positions add = 1 } } }
                                    if = { limit = { OR = { var:xfm_status = 2 var:xfm_status = 3 } } scope:xfma_context = { change_variable = { name = xfma_expiry_terminal_positions add = 1 } } }
                                    if = {
                                        limit = { OR = { var:xfm_status = 2 var:xfm_status = 3 } var:xfm_pending_kind = 4 NOT = { has_variable = xfm_pending_payment } var:xfm_last_settled_day >= scope:xfma_context.var:xfma_watched_expiry_day var:xfm_long_account = { has_variable = xfm_account_id } var:xfm_short_account = { has_variable = xfm_account_id } var:xfm_long_reservation = { has_variable = xfm_remaining_cents var:xfm_remaining_cents = 0 } var:xfm_short_reservation = { has_variable = xfm_remaining_cents var:xfm_remaining_cents = 0 } }
                                        scope:xfma_context = {
                                            set_variable = { name = xfma_expiry_closed_readback_occurred value = 1 }
                                            if = {
                                                limit = { NOT = { has_variable = xfma_expiry_closed_position_id } }
                                                set_variable = { name = xfma_expiry_closed_position value = prev }
                                                set_variable = { name = xfma_expiry_closed_position_id value = prev.var:xfm_position_id }
                                                set_variable = { name = xfma_expiry_closed_observed_day value = global_var:xfm_exchange.var:xfm_day }
                                            }
                                        }
                                    }
                                }
                                else = { scope:xfma_context = { set_variable = { name = xfma_expiry_positions_available value = 0 } } }
                            }
                            if = { limit = { OR = { var:xfma_expiry_positions_sampled = 0 var:xfma_expiry_positions_sampled < var:xfma_expiry_source_count var:xfma_watched_status_available = 0 } } set_variable = { name = xfma_expiry_positions_available value = 0 } }
                            set_variable = { name = xfma_expiry_available value = var:xfma_expiry_positions_available }
                        }
                    }
                    """;
        }
    }

    private static String once(Request request, String observation, String predicate) {
        return "if = { limit = { NOT = { has_variable = xfma_seen_" + observation + " }\n" + predicate
                + "}\nset_variable = { name = xfma_seen_" + observation + " value = 1 }\ndebug_log = \"" + marker(request, observation) + "\"\n}\n";
    }
    private static String marker(Request request, String observation) { return "XFMAT: TEST PASS " + request.caseId().scriptKey() + "_" + observation; }
    private static String fields(String... fields) { return String.join("\n", List.of(fields).stream().map(field -> "has_variable = " + field).toList()) + "\n"; }
    private static String eq(String field, long value) { return "has_variable = " + field + " var:" + field + " = " + value + "\n"; }
}
