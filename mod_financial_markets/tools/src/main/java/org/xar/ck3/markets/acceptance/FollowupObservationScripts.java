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
                    is_valid = { is_ai = no is_alive = yes ${ACTOR} NOT = { has_variable = ${P}_armed } NOT = { exists = var:${P}_story } ${OBSERVATION_CLOCK_READY} }
                    effect = { ${P}_arm_effect = yes }
                }
                ${P}_refresh_gui = {
                    scope = character
                    is_valid = { is_ai = no is_alive = yes exists = var:${P}_story ${OBSERVATION_CLOCK_READY} }
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
        String periodicObservation = afterFinance(request) ? ""
                : " effect_group = { days = 1 triggered_effect = { trigger = { exists = story_owner } effect = { ${P}_observe_effect = yes } } }\n";
        scripts.put("common/story_cycles/" + prefix + ".txt", "${P}_observer = {\n visible = no\n on_owner_death = {\n"
                + ownerDeath(request) + "\n }\n" + periodicObservation + "}\n"
                + passiveCompatibilityStories(request.prefix() + "_observer"));
        if (afterFinance(request))
            scripts.put("common/on_action/" + prefix + ".txt", """
                    # The financial clock fires this only after its daily modules and AI have returned.
                    # Its root is a technical custodian; the watched observer belongs to the real player.
                    xfm_finance_daily_observation_on_action = {
                        on_actions = { ${P}_after_finance_daily_on_action }
                    }
                    ${P}_after_finance_daily_on_action = {
                        effect = {
                            every_player = {
                                limit = { is_alive = yes exists = var:${P}_story }
                                var:${P}_story = {
                                    if = {
                                        limit = { story_type = ${P}_observer story_owner = prev }
                                        ${P}_observe_effect = yes
                                    }
                                }
                            }
                        }
                    }
                    """);
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
        if (request.caseId() == Profile.AI_CAPACITY)
            scripts.put("common/script_values/" + prefix + ".txt", Capacity.values());
        if (request.caseId() == Profile.DELISTING_GUI)
            scripts.put("common/script_values/" + prefix + ".txt", Delisting.values());
        scripts.put("common/scripted_effects/" + prefix + "_observe.txt", common(request) + profile(request)
                + (request.caseId() == Profile.MARKET_EVOLUTION ? Evolution.effects() : "")
                + (request.caseId() == Profile.AI_CAPACITY ? Capacity.effects() : "")
                + (request.caseId() == Profile.DELISTING_GUI ? Delisting.effects() : ""));
        Map<String, byte[]> result = new LinkedHashMap<>();
        scripts.forEach((name, source) -> result.put(name, ("\ufeff" + source.replace("${P}", prefix)
                .replace("${ACTOR}", actorCondition(request))
                .replace("${OBSERVATION_CLOCK_READY}", observationClockReady(request))
                .replace("${CAPACITY_PROTOCOL_ENTER}", request.caseId() == Profile.AI_CAPACITY ? "if = { limit = { has_variable = xfma_capacity_protocol } if = { limit = { var:xfma_capacity_protocol = 1 }" : "")
                .replace("${CAPACITY_PROTOCOL_LEAVE}", request.caseId() == Profile.AI_CAPACITY ? "} }" : "")
                .replace("${SCOPE_PROBE_HEIGHT}", request.caseId() == Profile.SPOT ? "560" : "82")
                .replace("${SCOPE_VALUE_PROBE}", spotScopeProbeWidget(request).replace("${P}", prefix))
                .replace("${NEXT_SAMPLE_DAY}", request.caseId() == Profile.SPOT || request.caseId() == Profile.MARKET_EVOLUTION || request.caseId() == Profile.DELISTING_GUI || request.caseId() == Profile.AI_CAPACITY
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
     * Retain core and finite schema-two epochs: evolution one through five, spot one through three, others one/two.
     * Passive declarations deliberately have no callbacks, markers, writes, or end_story operation.
     * This finite compatibility catalog does not claim to cover arbitrary historical epochs.
     */
    private static String passiveCompatibilityStories(String activeType) {
        StringBuilder source = new StringBuilder("# Passive compatibility: preserve old observation data without running an old case.\n"
                + "xfma_observer = { visible = no }\n");
        for (Profile profile : Profile.values()) {
            List<Integer> retainedEpochs = profile == Profile.MARKET_EVOLUTION ? List.of(1, 2, 3, 4, 5)
                    : profile == Profile.SPOT ? List.of(1, 2, 3) : List.of(1, 2);
            for (int epoch : retainedEpochs) {
                String type = "xfma_" + profile.scriptKey() + "_e" + epoch + "_observer";
                if (!type.equals(activeType)) source.append(type).append(" = { visible = no }\n");
            }
        }
        for (String type : marketEvolutionRecordTypes()) source.append(type).append(" = { visible = no }\n");
        for (String type : capacityRecordTypes()) source.append(type).append(" = { visible = no }\n");
        return source.toString();
    }

    private static String observationClockReady(Request request) {
        if (!afterFinance(request)) return "";
        // Refuse a new-date/manual read until the exchange has dispatched that actual date.
        // Never backfill, infer, or rewrite native dates from a financial-day counter.
        return "exists = global_var:xfm_exchange global_var:xfm_exchange = { has_variable = xfm_last_date "
                + "var:xfm_last_date >= current_date var:xfm_last_date <= current_date }";
    }

    private static boolean afterFinance(Request request) {
        return request.caseId() == Profile.MARKET_EVOLUTION || request.caseId() == Profile.AI_CAPACITY;
    }

    static List<String> capacityRecordTypes() { return List.of("xfma_ai_capacity_day_record"); }

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
        if (request.caseId() == Profile.DELISTING_GUI) {
            required += Delisting.required();
            if (request.targets().debtId() != null) required += "var:xfma_debt = { story_type = xfm_debt_claim has_variable = xfm_original_cents var:xfm_original_cents > 0 exists = var:xfm_source exists = var:xfm_debtor_account exists = var:xfm_creditor_account }\n";
        }
        required += "${P}_associations_trigger = yes\n";
        return """
                # Only xfma_ observation state is written. No product effect is invoked.
                ${P}_arm_effect = {
                    if = {
                        limit = { is_ai = no is_alive = yes ${ACTOR} NOT = { has_variable = ${P}_armed } NOT = { exists = var:${P}_story } exists = global_var:xfm_exchange ${OBSERVATION_CLOCK_READY} }
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
                + (request.caseId() == Profile.AI_CAPACITY ? Capacity.arm() : "")
                + (request.caseId() == Profile.DELISTING_GUI ? Delisting.arm() : "")
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
                    ${CAPACITY_PROTOCOL_ENTER}
                    if = {
                        limit = { var:xfma_ready = 1 exists = global_var:xfm_exchange ${OBSERVATION_CLOCK_READY} }
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
                    ${CAPACITY_PROTOCOL_LEAVE}
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
            case LIFECYCLE, DELISTING_GUI -> "var:xfm_coin = scope:xfma_context.var:xfma_coin\n";
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
            case DELISTING_GUI -> Delisting.profile(request);
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

    /** One ordinary GUI notice plus readback. No production transition is invoked here. */
    private static final class Delisting {
        private Delisting() { }

        static String externalHolderGuard() {
            return """
                    story_type = xfm_finance_position
                    has_variable = xfm_quantity_units has_variable = xfm_reserved_units
                    var:xfm_quantity_units > 0 var:xfm_reserved_units >= 0
                    var:xfm_coin = scope:xfma_context.var:xfma_coin
                    exists = var:xfm_account
                    var:xfm_account = {
                        story_type = xfm_finance_account
                        has_variable = xfm_account_id has_variable = xfm_system_account
                        var:xfm_system_account = 0 exists = var:xfm_holder
                        var:xfm_holder != scope:xfma_context.var:xfma_account.var:xfm_holder
                    }
                    """;
        }

        static String required() {
            return """
                    story_owner = { is_ai = no is_alive = yes is_adult = yes }
                    global_var:xfm_exchange = { has_variable = xfm_news_counter }
                    var:xfma_account = {
                        var:xfm_holder = scope:xfma_context.story_owner
                        has_variable = xfm_system_account var:xfm_system_account = 0
                        has_variable = xfm_account_frozen var:xfm_account_frozen = 0
                    }
                    var:xfma_coin = {
                        story_type = xfm_finance_coin
                        has_variable = xfm_coin_id has_variable = xfm_supply_units var:xfm_supply_units > 0
                        has_variable = xfm_news_fact_counter
                        has_variable = xfm_listing_state has_variable = xfm_trading_open
                        has_variable = xfm_derivatives_reduce_only
                        var:xfm_controller = scope:xfma_context.story_owner
                        OR = { var:xfm_listing_state = 1 var:xfm_listing_state = 2 var:xfm_listing_state = 4 }
                        any_in_list = { variable = xfm_holders
                    """ + externalHolderGuard() + "\n}\n}\n";
        }

        static String arm() {
            return """
                    set_variable = { name = xfma_start_coin_id value = var:xfma_coin.var:xfm_coin_id }
                    set_variable = { name = xfma_start_account_id value = var:xfma_account.var:xfm_account_id }
                    set_variable = { name = xfma_start_supply_units value = var:xfma_coin.var:xfm_supply_units }
                    set_variable = { name = xfma_start_coin_fact value = var:xfma_coin.var:xfm_news_fact_counter }
                    set_variable = { name = xfma_notice_actor value = var:xfma_coin.var:xfm_controller }
                    set_variable = { name = xfma_contract_sources_count value = 0 }
                    set_variable = { name = xfma_contract_sources_complete value = 1 }
                    var:xfma_coin = {
                        if = {
                            limit = {
                                any_in_list = {
                                    variable = xfm_futures_contracts
                                    NOT = { story_type = xfm_futures_contract has_variable = xfm_contract_id var:xfm_coin = scope:xfma_context.var:xfma_coin }
                                }
                            }
                            scope:xfma_context = { set_variable = { name = xfma_contract_sources_complete value = 0 } }
                        }
                        ordered_in_list = {
                            variable = xfm_holders
                            limit = {
                    """ + externalHolderGuard() + """
                            }
                            order_by = var:xfm_account.var:xfm_account_id
                            max = 1 check_range_bounds = no
                            scope:xfma_context = {
                                set_variable = { name = xfma_external_holding value = prev }
                                set_variable = { name = xfma_external_account value = prev.var:xfm_account }
                                set_variable = { name = xfma_external_account_id value = prev.var:xfm_account.var:xfm_account_id }
                                set_variable = { name = xfma_start_external_units value = prev.var:xfm_quantity_units }
                                set_variable = { name = xfma_start_external_reserved_units value = prev.var:xfm_reserved_units }
                            }
                        }
                        ordered_in_list = {
                            variable = xfm_futures_contracts
                            limit = { story_type = xfm_futures_contract has_variable = xfm_contract_id var:xfm_coin = scope:xfma_context.var:xfma_coin }
                            order_by = var:xfm_contract_id
                            max = 65 check_range_bounds = no
                            scope:xfma_context = {
                                if = {
                                    limit = { var:xfma_contract_sources_count < 64 }
                                    add_to_variable_list = { name = xfma_delisting_contract_sources target = prev }
                                    change_variable = { name = xfma_contract_sources_count add = 1 }
                                }
                                else = { set_variable = { name = xfma_contract_sources_complete value = 0 } }
                            }
                        }
                    }
                    if = {
                        limit = { exists = var:xfma_debt }
                        set_variable = { name = xfma_debt_source_before value = var:xfma_debt.var:xfm_source }
                        set_variable = { name = xfma_debtor_before value = var:xfma_debt.var:xfm_debtor_account }
                        set_variable = { name = xfma_creditor_before value = var:xfma_debt.var:xfm_creditor_account }
                        set_variable = { name = xfma_debt_original_before value = var:xfma_debt.var:xfm_original_cents }
                    }
                    """;
        }

        static String values() {
            return """
                    ${P}_next_sample_day_value = { value = var:xfma_last_sample_day add = 1 }
                    ${P}_notice_day14_value = { value = var:xfma_notice_day add = 14 }
                    ${P}_notice_day21_value = { value = var:xfma_notice_day add = 21 }
                    ${P}_notice_day30_value = { value = var:xfma_notice_day add = 30 }
                    # The following values run in the watched coin scope with the observer alias intact.
                    ${P}_notice_window_start_value = { value = scope:xfma_context.var:xfma_notice_day add = 15 }
                    ${P}_notice_window_end_value = { value = scope:xfma_context.var:xfma_notice_day add = 20 }
                    ${P}_terminal_average_value = { value = var:xfm_termination_price_sum_cents divide = var:xfm_termination_samples floor = yes }
                    """;
        }

        static String newsGuard() {
            return """
                    story_type = xfm_news_entry
                    has_variable = xfm_news_id var:xfm_news_id > scope:xfma_context.var:xfma_start_news_counter
                    var:xfm_news_source = scope:xfma_context.var:xfma_coin
                    has_variable = xfm_news_event_id var:xfm_news_event_id > scope:xfma_context.var:xfma_start_coin_fact
                    has_variable = xfm_news_kind var:xfm_news_kind = 8
                    has_variable = xfm_news_day var:xfm_news_day = scope:xfma_context.var:xfma_coin.var:xfm_notice_day
                    var:xfm_news_day = scope:xfma_context.var:xfma_start_day
                    var:xfm_news_actor = scope:xfma_context.var:xfma_notice_actor
                    """;
        }

        static String sameNotice() {
            return """
                    has_variable = xfma_notice_day
                    var:xfma_coin = {
                        story_type = xfm_finance_coin
                        has_variable = xfm_coin_id var:xfm_coin_id = scope:xfma_context.var:xfma_start_coin_id
                        has_variable = xfm_notice_day var:xfm_notice_day = scope:xfma_context.var:xfma_notice_day
                    }
                    """;
        }

        static String profile(Request request) {
            String result = "${P}_delisting_readback_effect = yes\n";
            result += once(request, "new_notice_kind8_readback", """
                    exists = var:xfma_news
                    var:xfma_news = {
                    """ + newsGuard() + """
                    }
                    """ + sameNotice() + """
                    var:xfma_notice_day > var:xfma_start_notice_day
                    var:xfma_notice_day = var:xfma_start_day
                    var:xfma_coin = {
                        has_variable = xfm_listing_state has_variable = xfm_trading_open has_variable = xfm_derivatives_reduce_only
                        var:xfm_listing_state = 3 var:xfm_trading_open = 1 var:xfm_derivatives_reduce_only = 1
                    }
                    """);
            result += once(request, "day14_exit_window_readback", """
                    has_variable = xfma_seen_new_notice_kind8_readback
                    """ + sameNotice() + """
                    global_var:xfm_exchange.var:xfm_day >= ${P}_notice_day14_value
                    var:xfma_coin = {
                        has_variable = xfm_delisting_age var:xfm_delisting_age >= 14 var:xfm_delisting_age < 21
                        has_variable = xfm_listing_state has_variable = xfm_trading_open has_variable = xfm_derivatives_reduce_only
                        var:xfm_listing_state = 3 var:xfm_trading_open = 1 var:xfm_derivatives_reduce_only = 1
                    }
                    """);
            result += once(request, "termination_state_readback", """
                    has_variable = xfma_seen_new_notice_kind8_readback
                    """ + sameNotice() + """
                    global_var:xfm_exchange.var:xfm_day >= ${P}_notice_day21_value
                    var:xfma_coin = {
                        has_variable = xfm_delisting_age var:xfm_delisting_age >= 21
                        var:xfm_termination_price_source_coin = this
                        has_variable = xfm_termination_source_notice_day var:xfm_termination_source_notice_day = scope:xfma_context.var:xfma_notice_day
                        has_variable = xfm_termination_window_start_day
                        var:xfm_termination_window_start_day >= ${P}_notice_window_start_value
                        var:xfm_termination_window_start_day <= ${P}_notice_window_start_value
                        has_variable = xfm_termination_window_end_day
                        var:xfm_termination_window_end_day >= ${P}_notice_window_end_value
                        var:xfm_termination_window_end_day <= ${P}_notice_window_end_value
                        has_variable = xfm_termination_samples has_variable = xfm_termination_price_certified
                        has_variable = xfm_termination_requested has_variable = xfm_settlement_price_pending
                        OR = {
                            AND = {
                                var:xfm_termination_samples >= 3 var:xfm_termination_samples <= 6
                                var:xfm_termination_price_certified = 1 var:xfm_termination_requested = 1
                                var:xfm_settlement_price_pending = 0
                                has_variable = xfm_termination_price_sum_cents var:xfm_termination_price_sum_cents > 0
                                has_variable = xfm_termination_price_cents var:xfm_termination_price_cents > 0
                                var:xfm_termination_price_cents >= ${P}_terminal_average_value
                                var:xfm_termination_price_cents <= ${P}_terminal_average_value
                            }
                            AND = {
                                var:xfm_termination_samples >= 0 var:xfm_termination_samples < 3
                                var:xfm_termination_price_certified = 0 var:xfm_termination_requested = 0
                                var:xfm_settlement_price_pending = 1
                            }
                        }
                    }
                    """);
            result += once(request, "day30_venue_exit_readback", """
                    has_variable = xfma_seen_day14_exit_window_readback
                    has_variable = xfma_seen_termination_state_readback
                    """ + sameNotice() + """
                    global_var:xfm_exchange.var:xfm_day >= ${P}_notice_day30_value
                    var:xfma_coin = {
                        has_variable = xfm_delisting_age var:xfm_delisting_age >= 30
                        has_variable = xfm_listing_state has_variable = xfm_trading_open has_variable = xfm_derivatives_reduce_only
                        var:xfm_listing_state = 5 var:xfm_trading_open = 0 var:xfm_derivatives_reduce_only = 1
                    }
                    """);
            String optional = "";
            if (request.targets().contractId() != null) optional += """
                    var:xfma_contract = {
                        story_type = xfm_futures_contract has_variable = xfm_contract_id
                        var:xfm_contract_id = ${CONTRACT} var:xfm_coin = scope:xfma_context.var:xfma_coin
                    }
                    """.replace("${CONTRACT}", request.targets().contractId());
            if (request.targets().positionId() != null) optional += """
                    var:xfma_position = {
                        story_type = xfm_futures_position has_variable = xfm_position_id
                        var:xfm_position_id = ${POSITION}
                        var:xfm_coin = scope:xfma_context.var:xfma_coin
                        var:xfm_contract = scope:xfma_context.var:xfma_contract
                    }
                    """.replace("${POSITION}", request.targets().positionId());
            if (request.targets().debtId() != null) optional += """
                    var:xfma_debt = {
                        story_type = xfm_debt_claim has_variable = xfm_debt_id var:xfm_debt_id = ${DEBT}
                        var:xfm_coin = scope:xfma_context.var:xfma_coin
                        var:xfm_source = scope:xfma_context.var:xfma_debt_source_before
                        var:xfm_debtor_account = scope:xfma_context.var:xfma_debtor_before
                        var:xfm_creditor_account = scope:xfma_context.var:xfma_creditor_before
                        has_variable = xfm_original_cents var:xfm_original_cents = scope:xfma_context.var:xfma_debt_original_before
                        has_variable = xfm_outstanding_cents var:xfm_outstanding_cents >= 0
                    }
                    """.replace("${DEBT}", request.targets().debtId());
            return result + once(request, "rights_sources_after_exit_readback", """
                    has_variable = xfma_seen_day30_venue_exit_readback
                    """ + sameNotice() + """
                    var:xfma_coin = { var:xfm_listing_state = 5 has_variable = xfm_supply_units var:xfm_supply_units = scope:xfma_context.var:xfma_start_supply_units }
                    var:xfma_account = { story_type = xfm_finance_account has_variable = xfm_account_id var:xfm_account_id = scope:xfma_context.var:xfma_start_account_id }
                    has_variable = xfma_start_external_units var:xfma_start_external_units > 0
                    exists = var:xfma_external_account exists = var:xfma_external_holding
                    var:xfma_external_account = { story_type = xfm_finance_account has_variable = xfm_account_id var:xfm_account_id = scope:xfma_context.var:xfma_external_account_id }
                    var:xfma_external_holding = {
                        story_type = xfm_finance_position
                        var:xfm_coin = scope:xfma_context.var:xfma_coin
                        var:xfm_account = scope:xfma_context.var:xfma_external_account
                        has_variable = xfm_quantity_units var:xfm_quantity_units >= 0
                        has_variable = xfm_reserved_units var:xfm_reserved_units >= 0
                    }
                    """ + optional);
        }

        static String effects() {
            StringBuilder source = new StringBuilder("""
                    ${P}_delisting_readback_effect = {
                        # Discover the real immutable fact; never enqueue it or create product state.
                        if = {
                            limit = {
                                NOT = { exists = var:xfma_news }
                                var:xfma_coin = { has_variable = xfm_notice_day var:xfm_notice_day = scope:xfma_context.var:xfma_start_day }
                            }
                            ordered_in_global_list = {
                                variable = xfm_news_entries
                                limit = {
                    """ + newsGuard() + """
                                }
                                order_by = var:xfm_news_id max = 1 check_range_bounds = no
                                scope:xfma_context = {
                                    set_variable = { name = xfma_news value = prev }
                                    set_variable = { name = xfma_notice_day value = prev.var:xfm_news_day }
                                    set_variable = { name = xfma_notice_event_id value = prev.var:xfm_news_event_id }
                                }
                            }
                        }
                        # A cursor is send progress only. No render or all-human claim is made.
                        set_variable = { name = xfma_delivery_confirmed value = 0 }
                        set_variable = { name = xfma_all_human_delivery_confirmed value = 0 }
                    """);
            for (String field : List.of("xfm_news_delivery_day", "xfm_news_sent_today", "xfm_news_cursor")) {
                String read = "xfma_" + field.substring(4) + "_readback";
                source.append("remove_variable = ").append(read).append("\nset_variable = { name = ").append(read).append("_available value = 0 }\n")
                        .append("if = { limit = { story_owner = { has_variable = ").append(field).append(" } }\n")
                        .append("set_variable = { name = ").append(read).append(" value = story_owner.var:").append(field).append(" }\n")
                        .append("set_variable = { name = ").append(read).append("_available value = 1 } }\n");
            }
            for (String field : List.of("xfm_news_next", "xfm_news_urgent_next")) {
                String read = "xfma_" + field.substring(4) + "_readback";
                source.append("remove_variable = ").append(read).append("\nif = { limit = { exists = story_owner.var:").append(field)
                        .append(" } set_variable = { name = ").append(read).append(" value = story_owner.var:").append(field).append(" } }\n");
            }
            return source.append("}\n").toString();
        }
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
        return "${P}_capacity_day_effect = yes\n" + """
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
                var:xfma_capacity_protocol = 1
                var:xfma_capacity_day_records = 395 var:xfma_capacity_warmup_records = 30 var:xfma_capacity_measured_records = 365
                var:xfma_capacity_skipped_financial_days = 0 var:xfma_capacity_missing_source_days = 0 var:xfma_capacity_invalid_work_days = 0
                NOT = { has_variable = xfma_capacity_record_allocation_failed }
                global_var:xfm_exchange.var:xfm_day >= { value = var:xfma_start_day add = 395 }
                global_var:xfm_exchange.var:xfm_day <= ${P}_capacity_end_day_value
                has_variable = xfma_seen_declared_inventory_readback
                """);
    }

    /** Finite post-settlement observations; script counters never represent wall-clock time. */
    private static final class Capacity {
        private Capacity() { }
        static final List<String> FIELDS = List.of("registered_coin_count", "resident_coin_count", "pending_coin_count", "active_coin_count",
                "new_listings_today", "active_orders_count", "futures_open_positions_count", "ai_count", "attention_count",
                "ai_work_today", "attention_work_today", "ai_decisions_today", "ai_queue_schema", "attention_queue_schema",
                "ai_queue_dirty", "attention_queue_dirty", "ai_queue_repair_count", "ai_queue_last_repair_date",
                "daily_attempt_count", "daily_attempt_script_date", "daily_attempt_prev_date", "daily_attempt_prev_date_present",
                "daily_attempt_entered_dispatch", "daily_rejected_count", "daily_raw_attempt_count", "daily_raw_script_date",
                "last_date", "fee_cents");
        static final List<String> REQUIRED = List.of("registered_coin_count", "resident_coin_count", "pending_coin_count", "active_coin_count",
                "active_orders_count", "futures_open_positions_count", "ai_count", "attention_work_today", "ai_work_today", "ai_decisions_today", "last_date");
        static String values() {
            return "${P}_next_sample_day_value = { value = var:xfma_last_sample_day add = 1 }\n"
                    + "${P}_capacity_end_day_value = { value = var:xfma_start_day add = 395 }\n";
        }
        static String arm() {
            return """
                    set_variable = { name = xfma_capacity_protocol value = 1 }
                    set_variable = { name = xfma_capacity_day_records value = 0 }
                    set_variable = { name = xfma_capacity_warmup_records value = 0 }
                    set_variable = { name = xfma_capacity_measured_records value = 0 }
                    set_variable = { name = xfma_capacity_skipped_financial_days value = 0 }
                    set_variable = { name = xfma_capacity_missing_source_days value = 0 }
                    set_variable = { name = xfma_capacity_invalid_work_days value = 0 }
                    set_variable = { name = xfma_capacity_last_record_day value = var:xfma_start_day }
                    set_variable = { name = xfma_capacity_last_attempt_day value = var:xfma_start_day }
                    set_variable = { name = xfma_capacity_last_source_date value = var:xfma_start_date }
                    """;
        }
        static String effects() {
            StringBuilder required = new StringBuilder("AND = {\n");
            for (String field : REQUIRED) required.append("var:xfma_").append(field).append("_available = 1\n");
            required.append("}\n");
            return """
                    ${P}_capacity_day_effect = {
                        if = {
                            limit = {
                                global_var:xfm_exchange.var:xfm_day > var:xfma_capacity_last_attempt_day
                                global_var:xfm_exchange.var:xfm_day <= ${P}_capacity_end_day_value
                                var:xfma_capacity_day_records < 395
                            }
                            # An allocation failure is retained; explicit same-day refresh never retries it.
                            set_variable = { name = xfma_capacity_last_attempt_day value = global_var:xfm_exchange.var:xfm_day }
                            clear_saved_scope = xfma_capacity_day_record
                            story_owner = { create_story = { type = xfma_ai_capacity_day_record save_scope_as = xfma_capacity_day_record } }
                            if = {
                                limit = { exists = scope:xfma_capacity_day_record scope:xfma_capacity_day_record = { story_type = xfma_ai_capacity_day_record } }
                                change_variable = { name = xfma_capacity_day_records add = 1 }
                                set_variable = { name = xfma_capacity_latest_day value = scope:xfma_capacity_day_record }
                                add_to_variable_list = { name = xfma_capacity_days target = scope:xfma_capacity_day_record }
                                scope:xfma_capacity_day_record = {
                                    set_variable = { name = xfma_record_protocol value = 1 }
                                    set_variable = { name = xfma_observer value = scope:xfma_context }
                                    set_variable = { name = xfma_exchange_source value = global_var:xfm_exchange }
                                    set_variable = { name = xfma_record_id value = scope:xfma_context.var:xfma_capacity_day_records }
                                    set_variable = { name = xfma_financial_day value = global_var:xfm_exchange.var:xfm_day }
                                    set_variable = { name = xfma_source_script_date value = current_date }
                                    set_variable = { name = xfma_previous_source_script_date value = scope:xfma_context.var:xfma_capacity_last_source_date }
                                    set_variable = { name = xfma_previous_record_financial_day value = scope:xfma_context.var:xfma_capacity_last_record_day }
                                    set_variable = { name = xfma_window_day value = { value = global_var:xfm_exchange.var:xfm_day subtract = scope:xfma_context.var:xfma_start_day } }
                                    set_variable = { name = xfma_measured_sample value = 0 }
                                    if = { limit = { var:xfma_window_day > 30 } set_variable = { name = xfma_measured_sample value = 1 } }
                                    set_variable = { name = xfma_skipped_financial_days_before value = { value = global_var:xfm_exchange.var:xfm_day subtract = scope:xfma_context.var:xfma_capacity_last_record_day subtract = 1 } }
                    """ + Evolution.copies("global_var:xfm_exchange", "xfma_", FIELDS.toArray(String[]::new)) + """
                                    set_variable = { name = xfma_required_sources_complete value = 0 }
                                    if = {
                                        limit = {
                    """ + required + """
                                        }
                                        set_variable = { name = xfma_required_sources_complete value = 1 }
                                    }
                                    else = { scope:xfma_context = { change_variable = { name = xfma_capacity_missing_source_days add = 1 } } }
                                    set_variable = { name = xfma_work_without_decision_available value = 0 }
                                    if = {
                                        limit = { var:xfma_ai_work_today_available = 1 var:xfma_ai_decisions_today_available = 1 }
                                        if = {
                                            limit = { var:xfma_ai_work_today >= var:xfma_ai_decisions_today }
                                            set_variable = { name = xfma_work_without_decision value = { value = var:xfma_ai_work_today subtract = var:xfma_ai_decisions_today } }
                                            set_variable = { name = xfma_work_without_decision_available value = 1 }
                                        }
                                        else = { scope:xfma_context = { change_variable = { name = xfma_capacity_invalid_work_days add = 1 } } }
                                    }
                                    if = {
                                        limit = { var:xfma_skipped_financial_days_before > 0 }
                                        scope:xfma_context = {
                                            change_variable = { name = xfma_capacity_skipped_financial_days add = scope:xfma_capacity_day_record.var:xfma_skipped_financial_days_before }
                                        }
                                    }
                                    if = { limit = { var:xfma_measured_sample = 0 } scope:xfma_context = { change_variable = { name = xfma_capacity_warmup_records add = 1 } } }
                                    else = { scope:xfma_context = { change_variable = { name = xfma_capacity_measured_records add = 1 } } }
                                }
                                set_variable = { name = xfma_capacity_last_record_day value = global_var:xfm_exchange.var:xfm_day }
                                set_variable = { name = xfma_capacity_last_source_date value = current_date }
                            }
                            else = {
                                set_variable = { name = xfma_capacity_record_allocation_failed value = 1 }
                                debug_log = "XFMAT: TEST FAIL ai_capacity_day_record_allocation_failed"
                            }
                            clear_saved_scope = xfma_capacity_day_record
                        }
                    }
                    """;
        }
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

    /** Explicit schema3 controlled engine fixture; schema1/2 remain read-only. */
    public static Map<String, byte[]> renderControlledFunding(FollowupContracts.ControlledFundingRequest request) {
        java.util.Objects.requireNonNull(request, "explicit controlled funding request");
        Map<String, String> scripts = new LinkedHashMap<>();
        scripts.put("common/on_action/xfmf_after_finance.txt", """
                xfm_finance_daily_observation_on_action = { on_actions = { xfmf_after_finance_on_action } }
                xfmf_after_finance_on_action = { effect = { xfmf_after_finance_effect = yes } }
                """);
        scripts.put("common/script_values/xfmf_values.txt", """
                xfmf_positive_quote_value = {
                value = var:xfmf_p_asset.var:xfm_index_cents multiply = 1.1 ceiling = yes
                }
                xfmf_negative_quote_value = {
                value = var:xfmf_n_asset.var:xfm_index_cents multiply = 0.9 floor = yes
                }
                """);
        scripts.put("common/scripted_effects/xfmf_book.txt", """
                xfmf_submit_effect = {
                set_variable = { name = xfm_selected_coin value = global_var:xfmf_fixture_owner.var:xfmf_$ASSET$_asset }
                set_variable = { name = xfm_futures_perpetual value = 1 }
                set_variable = { name = xfm_futures_expiry_day value = 0 }
                xfm_futures_ensure_market_effect = yes
                if = {
                 limit = { var:xfm_futures_result = 1 exists = var:xfm_futures_contract }
                 set_variable = { name = xfm_futures_side value = $SIDE$ }
                 set_variable = { name = xfm_futures_lots value = $LOTS$ }
                 set_variable = { name = xfm_futures_leverage value = 1 }
                 set_variable = { name = xfm_futures_limit_cents value = global_var:xfmf_fixture_owner.var:xfmf_$ASSET$_quote }
                 xfm_futures_submit_effect = yes
                 if = {
                  limit = { var:xfm_futures_result = 1 exists = scope:xfm_fut_incoming }
                  set_variable = { name = xfmf_open_order value = scope:xfm_fut_incoming }
                  set_variable = { name = xfmf_open_contract value = var:xfm_futures_contract }
                 }
                }
                }
                xfmf_bind_pair_effect = {
                clear_saved_scope = xfmf_bound_position
                var:xfmf_$SHORT$ = {
                 if = {
                  limit = { exists = var:xfm_account exists = var:xfmf_open_order }
                  var:xfm_account = {
                   every_in_list = {
                    variable = xfm_positions
                    limit = {
                     story_type = xfm_futures_position var:xfm_status = 0 var:xfm_lots = $LOTS$
                     var:xfm_long_account = global_var:xfmf_fixture_owner.var:xfmf_$LONG$.var:xfm_account
                     var:xfm_short_account = global_var:xfmf_fixture_owner.var:xfmf_$SHORT$.var:xfm_account
                    }
                    save_scope_as = xfmf_bound_position
                   }
                  }
                 }
                }
                if = {
                 limit = { exists = scope:xfmf_bound_position }
                 set_variable = { name = xfmf_$PAIR$_position value = scope:xfmf_bound_position }
                 add_to_variable_list = { name = xfmf_positions target = scope:xfmf_bound_position }
                 scope:xfmf_bound_position = {
                  set_variable = { name = xfmf_owner value = global_var:xfmf_fixture_owner }
                  xfmf_snapshot_effect = { PHASE = entry }
                 }
                }
                clear_saved_scope = xfmf_bound_position
                }
                xfmf_book_effect = {
                if = {
                 limit = { xfmf_book_trigger = yes }
                 set_variable = { name = xfmf_book_attempted value = 1 }
                 clear_saved_scope = xfmf_positive_asset
                 clear_saved_scope = xfmf_negative_asset
                 every_in_global_list = {
                  variable = xfm_index_registry
                  limit = { xfmf_asset_trigger = yes }
                  if = { limit = { var:xfm_index_id = 1 } save_scope_as = xfmf_positive_asset }
                  if = { limit = { var:xfm_index_id = 2 } save_scope_as = xfmf_negative_asset }
                 }
                 if = {
                  limit = { exists = scope:xfmf_positive_asset exists = scope:xfmf_negative_asset }
                  set_variable = { name = xfmf_p_asset value = scope:xfmf_positive_asset }
                  set_variable = { name = xfmf_n_asset value = scope:xfmf_negative_asset }
                  set_variable = { name = xfmf_book_day value = global_var:xfm_exchange.var:xfm_day }
                  set_variable = { name = xfmf_p_quote value = xfmf_positive_quote_value }
                  set_variable = { name = xfmf_n_quote value = xfmf_negative_quote_value }
                  var:xfmf_p_long = { xfmf_submit_effect = { ASSET = p SIDE = 1 LOTS = 128 } }
                  var:xfmf_p_short = { xfmf_submit_effect = { ASSET = p SIDE = 2 LOTS = 128 } }
                  xfmf_bind_pair_effect = { PAIR = p LONG = p_long SHORT = p_short LOTS = 128 }
                  var:xfmf_n_long = { xfmf_submit_effect = { ASSET = n SIDE = 1 LOTS = 128 } }
                  var:xfmf_n_short = { xfmf_submit_effect = { ASSET = n SIDE = 2 LOTS = 128 } }
                  xfmf_bind_pair_effect = { PAIR = n LONG = n_long SHORT = n_short LOTS = 128 }
                  var:xfmf_s_long = { xfmf_submit_effect = { ASSET = p SIDE = 1 LOTS = 1 } }
                  var:xfmf_s_short = { xfmf_submit_effect = { ASSET = p SIDE = 2 LOTS = 1 } }
                  xfmf_bind_pair_effect = { PAIR = s LONG = s_long SHORT = s_short LOTS = 1 }
                  if = {
                   limit = {
                    exists = var:xfmf_p_position
                    var:xfmf_p_position = { has_variable = xfmf_entry_version var:xfmf_entry_version = 1 }
                    exists = var:xfmf_n_position
                    var:xfmf_n_position = { has_variable = xfmf_entry_version var:xfmf_entry_version = 1 }
                    exists = var:xfmf_s_position
                    var:xfmf_s_position = { has_variable = xfmf_entry_version var:xfmf_entry_version = 1 }
                   }
                   set_variable = { name = xfmf_booked value = 1 }
                   debug_log = "XFMAT: TEST PASS controlled_funding_real_pairs_registered"
                  }
                 }
                 clear_saved_scope = xfmf_positive_asset
                 clear_saved_scope = xfmf_negative_asset
                }
                }
                """);
        scripts.put("common/scripted_effects/xfmf_close.txt", """
                xfmf_close_pair_effect = {
                var:xfmf_$PAIR$_position = { xfmf_snapshot_effect = { PHASE = close_before } }
                var:xfmf_$LONG$ = {
                 set_variable = { name = xfm_futures_selected_position value = global_var:xfmf_fixture_owner.var:xfmf_$PAIR$_position }
                 set_variable = { name = xfm_futures_reduce_lots value = $LOTS$ }
                 set_variable = { name = xfm_futures_limit_cents value = global_var:xfmf_fixture_owner.var:xfmf_$PAIR$_position.var:xfm_coin.var:xfm_mark_cents }
                 xfm_futures_reduce_effect = yes
                }
                var:xfmf_$SHORT$ = {
                 set_variable = { name = xfm_futures_selected_position value = global_var:xfmf_fixture_owner.var:xfmf_$PAIR$_position }
                 set_variable = { name = xfm_futures_reduce_lots value = $LOTS$ }
                 set_variable = { name = xfm_futures_limit_cents value = global_var:xfmf_fixture_owner.var:xfmf_$PAIR$_position.var:xfm_coin.var:xfm_mark_cents }
                 xfm_futures_reduce_effect = yes
                }
                var:xfmf_$PAIR$_position = { xfmf_snapshot_effect = { PHASE = closed } }
                }
                xfmf_close_effect = {
                if = {
                 limit = { xfmf_owner_trigger = yes has_variable = xfmf_next_recorded NOT = { has_variable = xfmf_close_attempted } }
                 set_variable = { name = xfmf_close_attempted value = 1 }
                 xfmf_close_pair_effect = { PAIR = p LONG = p_long SHORT = p_short LOTS = 128 }
                 xfmf_close_pair_effect = { PAIR = n LONG = n_long SHORT = n_short LOTS = 128 }
                 xfmf_close_pair_effect = { PAIR = s LONG = s_long SHORT = s_short LOTS = 1 }
                 set_variable = { name = xfmf_close_recorded value = 1 }
                 debug_log = "XFMAT: TEST PASS controlled_funding_closed_rights_recorded"
                }
                }
                """);
        scripts.put("common/scripted_effects/xfmf_observe.txt", """
                xfmf_snapshot_effect = {
                if = {
                 limit = { xfmf_snapshot_ready_trigger = yes NOT = { has_variable = xfmf_$PHASE$_version } }
                 set_variable = { name = xfmf_$PHASE$_day value = global_var:xfm_exchange.var:xfm_day }
                 set_variable = { name = xfmf_$PHASE$_script_date value = current_date }
                 set_variable = { name = xfmf_$PHASE$_position_id value = var:xfm_position_id }
                 set_variable = { name = xfmf_$PHASE$_contract_id value = var:xfm_contract_id }
                 set_variable = { name = xfmf_$PHASE$_lots value = var:xfm_lots }
                 set_variable = { name = xfmf_$PHASE$_status value = var:xfm_status }
                 set_variable = { name = xfmf_$PHASE$_mark_cents value = var:xfm_mark_cents }
                 set_variable = { name = xfmf_$PHASE$_index_cents value = var:xfm_coin.var:xfm_index_cents }
                 set_variable = { name = xfmf_$PHASE$_oracle_day value = var:xfm_coin.var:xfm_oracle_day }
                 set_variable = { name = xfmf_$PHASE$_oracle_quality value = var:xfm_coin.var:xfm_oracle_quality }
                 set_variable = { name = xfmf_$PHASE$_execution_day value = var:xfm_contract.var:xfm_execution_day }
                 set_variable = { name = xfmf_$PHASE$_execution_lots value = var:xfm_contract.var:xfm_execution_lots }
                 set_variable = { name = xfmf_$PHASE$_execution_volume_cents value = var:xfm_contract.var:xfm_execution_volume_cents }
                 set_variable = { name = xfmf_$PHASE$_execution_vwap_cents value = var:xfm_contract.var:xfm_last_execution_cents }
                 set_variable = { name = xfmf_$PHASE$_long_account_id value = var:xfm_long_account.var:xfm_account_id }
                 set_variable = { name = xfmf_$PHASE$_long_free_cents value = var:xfm_long_account.var:xfm_free_cents }
                 set_variable = { name = xfmf_$PHASE$_long_reserved_cents value = var:xfm_long_account.var:xfm_reserved_cents }
                 set_variable = { name = xfmf_$PHASE$_long_reservation_id value = var:xfm_long_reservation.var:xfm_reservation_id }
                 set_variable = { name = xfmf_$PHASE$_long_margin_cents value = var:xfm_long_reservation.var:xfm_remaining_cents }
                 set_variable = { name = xfmf_$PHASE$_long_account value = var:xfm_long_account }
                 set_variable = { name = xfmf_$PHASE$_long_reservation value = var:xfm_long_reservation }
                 set_variable = { name = xfmf_$PHASE$_long_holder value = var:xfm_long_account.var:xfm_holder }
                 set_variable = { name = xfmf_$PHASE$_short_account_id value = var:xfm_short_account.var:xfm_account_id }
                 set_variable = { name = xfmf_$PHASE$_short_free_cents value = var:xfm_short_account.var:xfm_free_cents }
                 set_variable = { name = xfmf_$PHASE$_short_reserved_cents value = var:xfm_short_account.var:xfm_reserved_cents }
                 set_variable = { name = xfmf_$PHASE$_short_reservation_id value = var:xfm_short_reservation.var:xfm_reservation_id }
                 set_variable = { name = xfmf_$PHASE$_short_margin_cents value = var:xfm_short_reservation.var:xfm_remaining_cents }
                 set_variable = { name = xfmf_$PHASE$_short_account value = var:xfm_short_account }
                 set_variable = { name = xfmf_$PHASE$_short_reservation value = var:xfm_short_reservation }
                 set_variable = { name = xfmf_$PHASE$_short_holder value = var:xfm_short_account.var:xfm_holder }
                 set_variable = { name = xfmf_$PHASE$_last_settled_day_present value = 0 }
                 if = { limit = { has_variable = xfm_last_settled_day } set_variable = { name = xfmf_$PHASE$_last_settled_day_present value = 1 } set_variable = { name = xfmf_$PHASE$_last_settled_day value = var:xfm_last_settled_day } }
                 set_variable = { name = xfmf_$PHASE$_last_funding_day_present value = 0 }
                 if = { limit = { has_variable = xfm_last_funding_day } set_variable = { name = xfmf_$PHASE$_last_funding_day_present value = 1 } set_variable = { name = xfmf_$PHASE$_last_funding_day value = var:xfm_last_funding_day } }
                 set_variable = { name = xfmf_$PHASE$_funding_rate_present value = 0 }
                 if = { limit = { has_variable = xfm_funding_rate } set_variable = { name = xfmf_$PHASE$_funding_rate_present value = 1 } set_variable = { name = xfmf_$PHASE$_funding_rate value = var:xfm_funding_rate } }
                 set_variable = { name = xfmf_$PHASE$_pending_payment_present value = 0 }
                 if = { limit = { has_variable = xfm_pending_payment } set_variable = { name = xfmf_$PHASE$_pending_payment_present value = 1 } set_variable = { name = xfmf_$PHASE$_pending_payment value = var:xfm_pending_payment } }
                 set_variable = { name = xfmf_$PHASE$_pending_kind_present value = 0 }
                 if = { limit = { has_variable = xfm_pending_kind } set_variable = { name = xfmf_$PHASE$_pending_kind_present value = 1 } set_variable = { name = xfmf_$PHASE$_pending_kind value = var:xfm_pending_kind } }
                 set_variable = { name = xfmf_$PHASE$_pending_day_present value = 0 }
                 if = { limit = { has_variable = xfm_pending_day } set_variable = { name = xfmf_$PHASE$_pending_day_present value = 1 } set_variable = { name = xfmf_$PHASE$_pending_day value = var:xfm_pending_day } }
                 set_variable = { name = xfmf_$PHASE$_pending_amount_present value = 0 }
                 if = { limit = { has_variable = xfm_pending_amount } set_variable = { name = xfmf_$PHASE$_pending_amount_present value = 1 } set_variable = { name = xfmf_$PHASE$_pending_amount value = var:xfm_pending_amount } }
                 set_variable = { name = xfmf_$PHASE$_pending_paid_present value = 0 }
                 if = { limit = { has_variable = xfm_pending_paid } set_variable = { name = xfmf_$PHASE$_pending_paid_present value = 1 } set_variable = { name = xfmf_$PHASE$_pending_paid value = var:xfm_pending_paid } }
                 set_variable = { name = xfmf_$PHASE$_pay_now_present value = 0 }
                 if = { limit = { has_variable = xfm_pay_now } set_variable = { name = xfmf_$PHASE$_pay_now_present value = 1 } set_variable = { name = xfmf_$PHASE$_pay_now value = var:xfm_pay_now } }
                 set_variable = { name = xfmf_$PHASE$_version value = 1 }
                }
                }
                xfmf_retry_effect = {
                if = {
                 limit = { xfmf_snapshot_ready_trigger = yes has_variable = xfm_last_settled_day has_variable = xfm_last_funding_day }
                 if = {
                 limit = { var:xfm_status = 0 var:xfm_last_settled_day = global_var:xfm_exchange.var:xfm_day var:xfm_last_funding_day = global_var:xfm_exchange.var:xfm_day NOT = { has_variable = xfm_pending_payment } }
                 xfmf_snapshot_effect = { PHASE = retry_before }
                 xfm_futures_position_daily_effect = yes
                 xfmf_snapshot_effect = { PHASE = retry_after }
                 }
                }
                }
                xfmf_after_finance_effect = {
                if = {
                 limit = { exists = global_var:xfmf_fixture_owner }
                 global_var:xfmf_fixture_owner = {
                  if = {
                   limit = { is_alive = yes has_variable = xfmf_booked }
                   if = {
                    limit = { NOT = { has_variable = xfmf_funding_recorded } global_var:xfm_exchange.var:xfm_day > var:xfmf_book_day }
                    var:xfmf_p_position = { xfmf_snapshot_effect = { PHASE = funding } }
                    var:xfmf_n_position = { xfmf_snapshot_effect = { PHASE = funding } }
                    var:xfmf_s_position = { xfmf_snapshot_effect = { PHASE = funding } }
                    set_variable = { name = xfmf_funding_recorded value = global_var:xfm_exchange.var:xfm_day }
                    debug_log = "XFMAT: TEST PASS controlled_funding_funding_capture_recorded"
                    var:xfmf_p_position = { xfmf_retry_effect = yes }
                    var:xfmf_n_position = { xfmf_retry_effect = yes }
                    var:xfmf_s_position = { xfmf_retry_effect = yes }
                    if = {
                     limit = {
                      var:xfmf_p_position = { has_variable = xfmf_retry_after_version var:xfmf_retry_after_version = 1 }
                      var:xfmf_n_position = { has_variable = xfmf_retry_after_version var:xfmf_retry_after_version = 1 }
                      var:xfmf_s_position = { has_variable = xfmf_retry_after_version var:xfmf_retry_after_version = 1 }
                     }
                     set_variable = { name = xfmf_retry_recorded value = 1 }
                     debug_log = "XFMAT: TEST PASS controlled_funding_same_day_retry_recorded"
                    }
                   }
                   if = {
                    limit = { has_variable = xfmf_funding_recorded NOT = { has_variable = xfmf_next_recorded } global_var:xfm_exchange.var:xfm_day > var:xfmf_funding_recorded }
                    var:xfmf_p_position = { xfmf_snapshot_effect = { PHASE = next } }
                    var:xfmf_n_position = { xfmf_snapshot_effect = { PHASE = next } }
                    var:xfmf_s_position = { xfmf_snapshot_effect = { PHASE = next } }
                    set_variable = { name = xfmf_next_recorded value = global_var:xfm_exchange.var:xfm_day }
                    debug_log = "XFMAT: TEST PASS controlled_funding_next_settlement_recorded"
                   }
                  }
                 }
                }
                }
                """);
        scripts.put("common/scripted_effects/xfmf_seed.txt", """
                xfmf_create_actor_effect = {
                clear_saved_scope = xfmf_new_actor
                create_character = {
                 name = "Controlled funding fixture"
                 gender = male age = 30 random_traits = no
                 location = root.capital_province culture = root.culture faith = root.faith
                 save_scope_as = xfmf_new_actor
                }
                if = {
                 limit = { exists = scope:xfmf_new_actor }
                 set_variable = { name = xfmf_$ROLE$ value = scope:xfmf_new_actor }
                 add_to_variable_list = { name = xfmf_actors target = scope:xfmf_new_actor }
                 scope:xfmf_new_actor = {
                  set_variable = { name = xfmf_fixture_actor value = 1 }
                  set_variable = { name = xfmf_owner value = global_var:xfmf_fixture_owner }
                  set_variable = { name = xfmf_seed_gold_before value = gold }
                  add_gold = 20000
                  set_variable = { name = xfmf_seed_gold_after value = gold }
                  xfm_finance_ensure_account_effect = yes
                  set_variable = { name = xfm_request_cents value = 100000 }
                  xfm_finance_deposit_effect = yes
                  if = {
                   limit = { var:xfm_result = 1 xfmf_actor_trigger = yes }
                   set_variable = { name = xfmf_seed_primary value = var:xfm_account }
                   set_variable = { name = xfmf_seed_primary_id value = var:xfm_account.var:xfm_account_id }
                   set_variable = { name = xfmf_seed_deposit_cents value = 100000 }
                   set_variable = { name = xfmf_seed_gold_after_deposit value = gold }
                   var:xfm_account = {
                    set_variable = { name = xfmf_seed_free_cents value = var:xfm_free_cents }
                    set_variable = { name = xfmf_seed_reserved_cents value = var:xfm_reserved_cents }
                   }
                   set_variable = { name = xfmf_seed_version value = 1 }
                  }
                 }
                }
                clear_saved_scope = xfmf_new_actor
                }
                xfmf_setup_effect = {
                if = {
                 limit = { xfmf_start_trigger = yes }
                 # Consume before the first setup effect. A partial failure never reseeds.
                 set_global_variable = { name = xfmf_fixture_owner value = this }
                 set_variable = { name = xfmf_setup_attempted value = 1 }
                 xfm_finance_ensure_effect = yes
                 # Explicit fresh-day0 fixture initialization from actual production world samples.
                 global_var:xfm_exchange = { xfm_oracle_index_bootstrap_effect = yes xfm_oracle_index_daily_effect = yes }
                 set_variable = { name = xfmf_seed_financial_day value = global_var:xfm_exchange.var:xfm_day }
                 set_variable = { name = xfmf_seed_script_date value = current_date }
                 xfmf_create_actor_effect = { ROLE = p_long }
                 xfmf_create_actor_effect = { ROLE = p_short }
                 xfmf_create_actor_effect = { ROLE = n_long }
                 xfmf_create_actor_effect = { ROLE = n_short }
                 xfmf_create_actor_effect = { ROLE = s_long }
                 xfmf_create_actor_effect = { ROLE = s_short }
                 if = {
                 limit = {
                  exists = var:xfmf_p_long
                  var:xfmf_p_long = { has_variable = xfmf_seed_version var:xfmf_seed_version = 1 xfmf_actor_trigger = yes }
                  exists = var:xfmf_p_short
                  var:xfmf_p_short = { has_variable = xfmf_seed_version var:xfmf_seed_version = 1 xfmf_actor_trigger = yes }
                  exists = var:xfmf_n_long
                  var:xfmf_n_long = { has_variable = xfmf_seed_version var:xfmf_seed_version = 1 xfmf_actor_trigger = yes }
                  exists = var:xfmf_n_short
                  var:xfmf_n_short = { has_variable = xfmf_seed_version var:xfmf_seed_version = 1 xfmf_actor_trigger = yes }
                  exists = var:xfmf_s_long
                  var:xfmf_s_long = { has_variable = xfmf_seed_version var:xfmf_seed_version = 1 xfmf_actor_trigger = yes }
                  exists = var:xfmf_s_short
                  var:xfmf_s_short = { has_variable = xfmf_seed_version var:xfmf_seed_version = 1 xfmf_actor_trigger = yes }
                 }
                 set_variable = { name = xfmf_seeded value = 1 }
                 debug_log = "XFMAT: TEST PASS controlled_funding_seeded_baseline"
                 }
                }
                }
                """);
        scripts.put("common/scripted_guis/xfmf_fixture.txt", """
                xfmf_setup_gui = {
                scope = character
                is_valid = { xfmf_start_trigger = yes }
                effect = { xfmf_setup_effect = yes }
                }
                xfmf_book_gui = {
                scope = character
                is_valid = { xfmf_book_trigger = yes }
                effect = { xfmf_book_effect = yes }
                }
                xfmf_close_gui = {
                scope = character
                is_valid = { xfmf_owner_trigger = yes has_variable = xfmf_next_recorded NOT = { has_variable = xfmf_close_attempted } }
                effect = { xfmf_close_effect = yes }
                }
                """);
        scripts.put("common/scripted_triggers/xfmf_guards.txt", """
                xfmf_owner_trigger = {
                trigger_if = {
                 limit = { exists = global_var:xfmf_fixture_owner }
                 is_ai = no is_alive = yes is_adult = yes this = global_var:xfmf_fixture_owner
                }
                trigger_else = { always = no }
                }
                xfmf_start_trigger = {
                is_ai = no is_alive = yes is_adult = yes
                exists = capital_province
                NOT = { exists = global_var:xfmf_fixture_owner }
                trigger_if = {
                 limit = { exists = global_var:xfm_exchange }
                 global_var:xfm_exchange = {
                  story_type = xfm_finance_exchange has_variable = xfm_day var:xfm_day = 0
                  NOT = { any_in_list = { variable = xfm_futures_contracts always = yes } }
                  trigger_if = { limit = { has_variable = xfm_next_futures_position_id } var:xfm_next_futures_position_id = 0 }
                  trigger_if = { limit = { has_variable = xfm_next_futures_order_id } var:xfm_next_futures_order_id = 0 }
                 }
                }
                }
                xfmf_actor_trigger = {
                trigger_if = {
                 limit = { has_variable = xfmf_fixture_actor exists = var:xfmf_owner exists = var:xfm_account }
                 is_alive = yes is_adult = yes is_ai = yes
                 var:xfmf_owner = global_var:xfmf_fixture_owner
                 var:xfm_account = {
                  xfm_finance_account_usable_trigger = yes
                  var:xfm_system_account = 0 var:xfm_holder = prev
                  NOT = { has_variable = xfm_legal_entity }
                 }
                }
                trigger_else = { always = no }
                }
                xfmf_asset_trigger = {
                story_type = xfm_oracle_index
                trigger_if = {
                 limit = { has_variable = xfm_index_id has_variable = xfm_index_cents has_variable = xfm_mark_cents has_variable = xfm_oracle_day has_variable = xfm_oracle_quality has_variable = xfm_max_leverage has_variable = xfm_derivatives_reduce_only }
                 var:xfm_index_cents >= 90 var:xfm_index_cents <= 500
                 var:xfm_mark_cents > 0 var:xfm_oracle_quality > 0
                 var:xfm_oracle_day = global_var:xfm_exchange.var:xfm_day
                 var:xfm_max_leverage >= 1 var:xfm_derivatives_reduce_only = 0
                 NOT = { any_in_list = { variable = xfm_futures_contracts always = yes } }
                }
                trigger_else = { always = no }
                }
                xfmf_snapshot_ready_trigger = {
                story_type = xfm_futures_position
                trigger_if = {
                 limit = { exists = var:xfm_long_account exists = var:xfm_short_account exists = var:xfm_long_reservation exists = var:xfm_short_reservation exists = var:xfm_coin exists = var:xfm_contract }
                 has_variable = xfm_position_id has_variable = xfm_contract_id has_variable = xfm_lots has_variable = xfm_status has_variable = xfm_mark_cents
                 var:xfm_long_account = { story_type = xfm_finance_account has_variable = xfm_free_cents has_variable = xfm_reserved_cents has_variable = xfm_account_id exists = var:xfm_holder }
                 var:xfm_short_account = { story_type = xfm_finance_account has_variable = xfm_free_cents has_variable = xfm_reserved_cents has_variable = xfm_account_id exists = var:xfm_holder }
                 var:xfm_long_reservation = { story_type = xfm_finance_reservation has_variable = xfm_remaining_cents has_variable = xfm_reservation_id }
                 var:xfm_short_reservation = { story_type = xfm_finance_reservation has_variable = xfm_remaining_cents has_variable = xfm_reservation_id }
                 var:xfm_coin = { has_variable = xfm_index_cents has_variable = xfm_mark_cents has_variable = xfm_oracle_day has_variable = xfm_oracle_quality }
                 var:xfm_contract = { has_variable = xfm_execution_day has_variable = xfm_execution_volume_cents has_variable = xfm_execution_lots has_variable = xfm_last_execution_cents }
                }
                trigger_else = { always = no }
                }
                xfmf_book_trigger = {
                xfmf_owner_trigger = yes
                trigger_if = {
                 limit = { has_variable = xfmf_seeded NOT = { has_variable = xfmf_book_attempted }
                 exists = var:xfmf_p_long
                 exists = var:xfmf_p_short
                 exists = var:xfmf_n_long
                 exists = var:xfmf_n_short
                 exists = var:xfmf_s_long
                 exists = var:xfmf_s_short
                 }
                 var:xfmf_p_long = { xfmf_actor_trigger = yes }
                 var:xfmf_p_short = { xfmf_actor_trigger = yes }
                 var:xfmf_n_long = { xfmf_actor_trigger = yes }
                 var:xfmf_n_short = { xfmf_actor_trigger = yes }
                 var:xfmf_s_long = { xfmf_actor_trigger = yes }
                 var:xfmf_s_short = { xfmf_actor_trigger = yes }
                }
                trigger_else = { always = no }
                }
                """);
        scripts.put("descriptor.mod", """
                name="Controlled perpetual funding engine fixture (synthetic seed)"
                version="1"
                supported_version="1.21.*"
                """);
        scripts.put("gui/scripted_widgets/xfmf_fixture.txt", """
                gui/xfmf_fixture.gui = xfmf_funding_fixture_widget
                """);
        scripts.put("gui/xfmf_fixture.gui", """
                window = {
                 name = "xfmf_funding_fixture_widget"
                 parentanchor = top|right
                 position = { -300 130 }
                 size = { 240 126 }
                 layer = middle
                 visible = "[GetPlayer.IsValid]"
                 button_standard = {
                 name = "xfmf_setup"
                 position = { 0 0 }
                 size = { 240 40 }
                 text = "xfmf_setup_label"
                 enabled = "[GetScriptedGui( 'xfmf_setup_gui' ).IsValid( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
                 onclick = "[GetScriptedGui( 'xfmf_setup_gui' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
                 }
                 button_standard = {
                 name = "xfmf_book"
                 position = { 0 42 }
                 size = { 240 40 }
                 text = "xfmf_book_label"
                 enabled = "[GetScriptedGui( 'xfmf_book_gui' ).IsValid( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
                 onclick = "[GetScriptedGui( 'xfmf_book_gui' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
                 }
                 button_standard = {
                 name = "xfmf_close"
                 position = { 0 84 }
                 size = { 240 40 }
                 text = "xfmf_close_label"
                 enabled = "[GetScriptedGui( 'xfmf_close_gui' ).IsValid( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
                 onclick = "[GetScriptedGui( 'xfmf_close_gui' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
                 }
                }
                """);
        scripts.put("localization/english/xfmf_l_english.yml", """
                l_english:
                 xfmf_setup_label:0 "Fixture: seed six new actors once"
                 xfmf_book_label:0 "Fixture: submit original real orders once"
                 xfmf_close_label:0 "Fixture: request both real closes once"
                """);
        scripts.put("localization/simp_chinese/xfmf_l_simp_chinese.yml", """
                l_simp_chinese:
                 xfmf_setup_label:0 "受控验收：一次创建六个种子角色"
                 xfmf_book_label:0 "受控验收：一次提交原生产订单"
                 xfmf_close_label:0 "受控验收：一次请求双方真实减仓"
                """);
        Map<String, byte[]> result = new LinkedHashMap<>();
        scripts.forEach((name, text) -> result.put(name, ("\ufeff" + text).getBytes(StandardCharsets.UTF_8)));
        return Map.copyOf(result);
    }

    /** Controlled obligations only; no synthetic cash, artificial crisis maturity or death calls. */
    public static Map<String, byte[]> renderControlledDebtAidNews(FollowupContracts.ControlledDebtAidNewsRequest request) {
        java.util.Objects.requireNonNull(request, "explicit controlled debt request");
        Map<String, String> scripts = new LinkedHashMap<>();
        scripts.put("descriptor.mod", """
                name="Controlled debt aid and local news engine fixture (declared API liabilities)"
                version="1"
                supported_version="1.21.*"
                """);
        scripts.put("common/story_cycles/xfmd_sources.txt", "xfmd_claim_source = { }\n");
        scripts.put("common/scripted_triggers/xfmd_guards.txt", """
                xfmd_private_account_trigger = {
                 story_type = xfm_finance_account
                 trigger_if = {
                  limit = { has_variable = xfm_account_id has_variable = xfm_free_cents has_variable = xfm_reserved_cents has_variable = xfm_system_account has_variable = xfm_inheritance_state has_variable = xfm_account_frozen exists = var:xfm_holder exists = var:xfm_beneficial_owner }
                  xfm_finance_account_usable_trigger = yes
                  var:xfm_system_account = 0 var:xfm_inheritance_state = 0 var:xfm_holder = var:xfm_beneficial_owner
                  NOT = { has_variable = xfm_legal_entity }
                 }
                 trigger_else = { always = no }
                }
                xfmd_seed_actor_trigger = {
                 trigger_if = {
                  limit = { exists = var:xfmf_owner exists = var:xfm_account has_variable = xfmf_seed_version has_variable = xfmf_fixture_actor }
                  is_ai = yes is_alive = yes is_adult = yes var:xfmf_seed_version = 1 var:xfmf_fixture_actor = 1
                  var:xfmf_owner = global_var:xfmf_fixture_owner
                  var:xfm_account = { xfmd_private_account_trigger = yes var:xfm_holder = prev }
                 }
                 trigger_else = { always = no }
                }
                xfmd_role_trigger = {
                 trigger_if = {
                  limit = { exists = var:xfmf_$ROLE$ }
                  var:xfmf_$ROLE$ = { xfmd_seed_actor_trigger = yes var:xfm_account = { var:xfm_account_id = $ID$ } }
                 }
                 trigger_else = { always = no }
                }
                xfmd_available_role_trigger = {
                 OR = {
                  xfmd_role_trigger = { ROLE = p_long ID = $ID$ } xfmd_role_trigger = { ROLE = p_short ID = $ID$ }
                  xfmd_role_trigger = { ROLE = n_long ID = $ID$ } xfmd_role_trigger = { ROLE = n_short ID = $ID$ }
                  xfmd_role_trigger = { ROLE = s_long ID = $ID$ } xfmd_role_trigger = { ROLE = s_short ID = $ID$ }
                 }
                }
                xfmd_start_trigger = {
                 is_ai = no is_alive = yes is_adult = yes
                 NOT = { exists = global_var:xfmd_fixture_owner }
                 NOT = { has_variable = xfmd_setup_attempted }
                 trigger_if = {
                  limit = { exists = global_var:xfm_exchange exists = global_var:xfmf_fixture_owner exists = var:xfm_account exists = var:xfm_active_account }
                  this = global_var:xfmf_fixture_owner
                  var:xfm_active_account = var:xfm_account
                  has_variable = xfmf_seeded var:xfmf_seeded = 1 has_variable = xfmf_close_recorded var:xfmf_close_recorded = 1
                  global_var:xfm_exchange = { story_type = xfm_finance_exchange has_variable = xfm_day }
                  var:xfm_account = { xfmd_private_account_trigger = yes var:xfm_holder = root var:xfm_account_id = ${PLAYER} var:xfm_free_cents >= 2000 }
                  xfmd_available_role_trigger = { ID = ${DEBTOR} }
                  xfmd_available_role_trigger = { ID = ${CREDITOR} }
                 }
                 trigger_else = { always = no }
                }
                xfmd_owner_trigger = {
                 trigger_if = {
                  limit = { exists = global_var:xfmd_fixture_owner }
                  this = global_var:xfmd_fixture_owner is_ai = no is_alive = yes is_adult = yes
                 }
                 trigger_else = { always = no }
                }
                xfmd_review_trigger = {
                 xfmd_owner_trigger = yes
                 NOT = { has_variable = xfmd_review_attempted }
                 trigger_if = {
                  limit = { has_variable = xfmd_seeded exists = var:xfmd_a_claim exists = var:xfmd_b_claim exists = var:xfmd_payer }
                  var:xfmd_seeded = 1 has_variable = xfmd_seed_day var:xfmd_seed_day = global_var:xfm_exchange.var:xfm_day
                  var:xfmd_payer = { xfmd_private_account_trigger = yes var:xfm_holder = root var:xfm_account_id = ${PLAYER} }
                  var:xfmd_a_claim = {
                   story_type = xfm_debt_claim var:xfm_source = root.var:xfmd_a_source
                   var:xfm_debtor_account = root.var:xfmd_debtor var:xfm_creditor_account = root.var:xfmd_creditor
                   var:xfm_original_cents = 2000 var:xfm_repaid_cents = 1000 var:xfm_outstanding_cents = 1000
                   has_variable = xfm_request_operation exists = var:xfm_request_payer
                   var:xfm_request_payer = root.var:xfmd_payer
                   var:xfm_request_operation = root.var:xfmd_payer.var:xfm_last_debt_payment_operation
                  }
                  var:xfmd_b_claim = {
                   story_type = xfm_debt_claim var:xfm_source = root.var:xfmd_b_source
                   var:xfm_debtor_account = root.var:xfmd_debtor
                   var:xfm_original_cents = 1000 var:xfm_written_off_cents = 100 var:xfm_outstanding_cents = 900
                   var:xfm_creditor_account = root.var:xfmd_payer has_variable = xfm_creditor_haircut_done has_variable = xfm_extension_granted
                  }
                 }
                 trigger_else = { always = no }
                }
                """);
        scripts.put("common/scripted_effects/xfmd_seed.txt", """
                xfmd_consider_role_effect = {
                 if = {
                  limit = { exists = var:xfmf_$ROLE$ }
                  var:xfmf_$ROLE$ = {
                   if = {
                    limit = { xfmd_seed_actor_trigger = yes }
                    if = { limit = { var:xfm_account = { var:xfm_account_id = ${DEBTOR} } } var:xfm_account = { save_scope_as = xfmd_debtor } }
                    if = { limit = { var:xfm_account = { var:xfm_account_id = ${CREDITOR} } } var:xfm_account = { save_scope_as = xfmd_creditor } }
                   }
                  }
                 }
                }
                xfmd_make_claim_effect = {
                 global_var:xfm_exchange.story_owner = { create_story = { type = xfmd_claim_source save_scope_as = xfmd_source_$KEY$ } }
                 if = {
                  limit = { exists = scope:xfmd_source_$KEY$ }
                  set_variable = { name = xfmd_$KEY$_source value = scope:xfmd_source_$KEY$ }
                  scope:xfmd_source_$KEY$ = {
                   set_variable = { name = xfmd_controlled_api_input value = 1 }
                   set_variable = { name = xfmd_owner value = root }
                   set_variable = { name = xfm_request_debtor value = scope:xfmd_debtor }
                   set_variable = { name = xfm_request_creditor value = scope:$CREDITOR$ }
                   set_variable = { name = xfm_request_cents value = $CENTS$ }
                   set_variable = { name = xfm_request_day value = global_var:xfm_exchange.var:xfm_day }
                   set_variable = { name = xfm_request_kind value = 1 }
                   set_variable = { name = xfm_request_fund_eligible value = 0 }
                   xfm_debt_cover_shortfall_effect = yes
                   if = {
                    limit = { var:xfm_result = 1 exists = scope:xfm_debt_receipt }
                    scope:xfm_debt_receipt = { save_scope_as = xfmd_$KEY$_claim xfmd_snapshot_effect = { PHASE = baseline } }
                    set_variable = { name = xfmd_source_version value = 1 }
                   }
                  }
                  if = { limit = { exists = scope:xfmd_$KEY$_claim } set_variable = { name = xfmd_$KEY$_claim value = scope:xfmd_$KEY$_claim } }
                 }
                }
                xfmd_setup_effect = {
                 if = {
                  limit = { xfmd_start_trigger = yes }
                  set_variable = { name = xfmd_setup_attempted value = 1 }
                  set_global_variable = { name = xfmd_fixture_owner value = this }
                  clear_saved_scope = xfmd_debtor clear_saved_scope = xfmd_creditor clear_saved_scope = xfmd_payer
                  clear_saved_scope = xfmd_source_a clear_saved_scope = xfmd_source_b clear_saved_scope = xfmd_a_claim clear_saved_scope = xfmd_b_claim
                  var:xfm_account = { save_scope_as = xfmd_payer }
                  set_variable = { name = xfmd_payer value = scope:xfmd_payer }
                  xfmd_consider_role_effect = { ROLE = p_long } xfmd_consider_role_effect = { ROLE = p_short }
                  xfmd_consider_role_effect = { ROLE = n_long } xfmd_consider_role_effect = { ROLE = n_short }
                  xfmd_consider_role_effect = { ROLE = s_long } xfmd_consider_role_effect = { ROLE = s_short }
                  if = {
                   limit = { exists = scope:xfmd_debtor exists = scope:xfmd_creditor }
                   set_variable = { name = xfmd_debtor value = scope:xfmd_debtor }
                   set_variable = { name = xfmd_creditor value = scope:xfmd_creditor }
                   xfmd_make_claim_effect = { KEY = a CREDITOR = xfmd_creditor CENTS = 2000 }
                   xfmd_make_claim_effect = { KEY = b CREDITOR = xfmd_payer CENTS = 1000 }
                   if = {
                    limit = { exists = var:xfmd_a_claim exists = var:xfmd_b_claim }
                    set_variable = { name = xfmd_seed_day value = global_var:xfm_exchange.var:xfm_day }
                    set_variable = { name = xfmd_seeded value = 1 }
                    debug_log = "XFMAT: TEST PASS controlled_debt_api_claims_recorded"
                   }
                  }
                 }
                }
                """);
        scripts.put("common/scripted_effects/xfmd_observe.txt", """
                xfmd_snapshot_effect = {
                 if = {
                  limit = { NOT = { has_variable = xfmd_$PHASE$_version } }
                  set_variable = { name = xfmd_$PHASE$_day value = global_var:xfm_exchange.var:xfm_day }
                  set_variable = { name = xfmd_$PHASE$_debt_id value = var:xfm_debt_id }
                  set_variable = { name = xfmd_$PHASE$_original value = var:xfm_original_cents }
                  set_variable = { name = xfmd_$PHASE$_outstanding value = var:xfm_outstanding_cents }
                  set_variable = { name = xfmd_$PHASE$_repaid value = var:xfm_repaid_cents }
                  set_variable = { name = xfmd_$PHASE$_written_off value = var:xfm_written_off_cents }
                  set_variable = { name = xfmd_$PHASE$_due_day value = var:xfm_due_day }
                  set_variable = { name = xfmd_$PHASE$_debtor_id value = var:xfm_debtor_account.var:xfm_account_id }
                  set_variable = { name = xfmd_$PHASE$_creditor_id value = var:xfm_creditor_account.var:xfm_account_id }
                  set_variable = { name = xfmd_$PHASE$_debtor_free value = var:xfm_debtor_account.var:xfm_free_cents }
                  set_variable = { name = xfmd_$PHASE$_debtor_reserved value = var:xfm_debtor_account.var:xfm_reserved_cents }
                  set_variable = { name = xfmd_$PHASE$_creditor_free value = var:xfm_creditor_account.var:xfm_free_cents }
                  set_variable = { name = xfmd_$PHASE$_creditor_reserved value = var:xfm_creditor_account.var:xfm_reserved_cents }
                  set_variable = { name = xfmd_$PHASE$_payer_free value = global_var:xfmd_fixture_owner.var:xfmd_payer.var:xfm_free_cents }
                  set_variable = { name = xfmd_$PHASE$_payer_reserved value = global_var:xfmd_fixture_owner.var:xfmd_payer.var:xfm_reserved_cents }
                  set_variable = { name = xfmd_$PHASE$_version value = 1 }
                 }
                }
                xfmd_review_effect = {
                 if = {
                  limit = { xfmd_review_trigger = yes }
                  set_variable = { name = xfmd_review_attempted value = 1 }
                  var:xfmd_a_claim = {
                   xfmd_snapshot_effect = { PHASE = help }
                   xfm_debt_repay_effect = yes
                   set_variable = { name = xfmd_retry_result value = var:xfm_result }
                   xfmd_snapshot_effect = { PHASE = retry }
                  }
                  var:xfmd_b_claim = { xfmd_snapshot_effect = { PHASE = consent } }
                  clear_saved_scope = xfmd_previous_selection
                  if = { limit = { exists = var:xfm_selected_debt } var:xfm_selected_debt = { save_scope_as = xfmd_previous_selection } }
                  set_variable = { name = xfm_selected_debt value = var:xfmd_b_claim }
                  xfm_debt_restructure_selected_effect = yes
                  if = { limit = { exists = scope:xfmd_previous_selection } set_variable = { name = xfm_selected_debt value = scope:xfmd_previous_selection } }
                  else = { remove_variable = xfm_selected_debt }
                  clear_saved_scope = xfmd_previous_selection
                  var:xfmd_b_claim = { xfmd_snapshot_effect = { PHASE = consent_retry } }
                  if = {
                   limit = { var:xfmd_a_claim = { var:xfmd_retry_result = 0 } }
                   set_variable = { name = xfmd_review_recorded value = 1 }
                   debug_log = "XFMAT: TEST PASS controlled_debt_gui_help_and_retry_recorded"
                  }
                 }
                }
                """);
        scripts.put("common/scripted_guis/xfmd_fixture.txt", """
                xfmd_setup_gui = { scope = character is_valid = { xfmd_start_trigger = yes } effect = { xfmd_setup_effect = yes } }
                xfmd_review_gui = { scope = character is_valid = { xfmd_review_trigger = yes } effect = { xfmd_review_effect = yes } }
                """);
        scripts.put("gui/scripted_widgets/xfmd_widget.txt", "gui/xfmd_widget.gui = xfmd_widget\n");
        scripts.put("gui/xfmd_widget.gui", """
                window = {
                 name = xfmd_widget parentanchor = bottom|right position = { -300 130 } size = { 240 84 } layer = middle
                 visible = "[GetPlayer.IsValid]"
                 button_standard = {
                  name = "xfmd_setup" position = { 0 0 } size = { 240 40 } text = "xfmd_setup_label"
                  enabled = "[GetScriptedGui( 'xfmd_setup_gui' ).IsValid( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
                  onclick = "[GetScriptedGui( 'xfmd_setup_gui' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
                 }
                 button_standard = {
                  name = "xfmd_review" position = { 0 42 } size = { 240 40 } text = "xfmd_review_label"
                  enabled = "[GetScriptedGui( 'xfmd_review_gui' ).IsValid( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
                  onclick = "[GetScriptedGui( 'xfmd_review_gui' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
                 }
                }
                """);
        scripts.put("localization/english/xfmd_l_english.yml", """
                l_english:
                 xfmd_setup_label:0 "Controlled API claims: create once"
                 xfmd_review_label:0 "Capture real help; one declared API retry"
                """);
        scripts.put("localization/simp_chinese/xfmd_l_simp_chinese.yml", """
                l_simp_chinese:
                 xfmd_setup_label:0 "受控验收：一次建立声明债权"
                 xfmd_review_label:0 "记录真实援助并一次声明重入"
                """);
        Map<String, byte[]> result = new LinkedHashMap<>();
        var participants = request.participants();
        scripts.forEach((name, text) -> result.put(name, ("\ufeff" + text
                .replace("${PLAYER}", participants.playerAccountId())
                .replace("${DEBTOR}", participants.debtorAccountId())
                .replace("${CREDITOR}", participants.aidCreditorAccountId())).getBytes(StandardCharsets.UTF_8)));
        return Map.copyOf(result);
    }

    /** Independent synthetic load, deliberately not a natural issuance/395-day capacity observer. */
    public static Map<String, byte[]> renderControlledLoad(FollowupContracts.ControlledLoadRequest request) {
        java.util.Objects.requireNonNull(request, "explicit synthetic load request");
        Map<String, String> scripts = new LinkedHashMap<>();
        scripts.put("descriptor.mod", "name=\"SYNTHETIC Financial market controlled load\"\nversion=\"1\"\nsupported_version=\"1.21.*\"\n");
        scripts.put("common/on_action/xfmcl_after_finance.txt", """
                xfm_finance_daily_observation_on_action = { on_actions = { xfmcl_after_finance_on_action } }
                xfmcl_after_finance_on_action = { effect = { xfmcl_after_finance_effect = yes } }
                """);
        scripts.put("common/scripted_triggers/xfmcl_guards.txt", """
                # Explicit synthetic-only independent-world controls. No natural AI qualification.
                xfmcl_rules_trigger = {
                 has_game_rule = xfm_capacity_standard
                 has_game_rule = xfm_ai_standard
                 has_game_rule = xfm_ai_issuance_disabled
                 has_game_rule = xfm_futures_disabled
                 has_game_rule = xfm_spot_enabled
                 xfm_config_coin_capacity_value = 4096
                 xfm_config_registration_capacity_value = 16384
                 xfm_config_ai_budget_value = 512
                }
                xfmcl_owner_trigger = {
                 is_ai = no is_alive = yes is_adult = yes
                 exists = global_var:xfmcl_fixture_owner this = global_var:xfmcl_fixture_owner
                 xfmcl_rules_trigger = yes
                 NOT = { has_variable = xfmcl_failed }
                }
                xfmcl_start_trigger = {
                 is_ai = no is_alive = yes is_adult = yes exists = capital_province
                 NOT = { exists = global_var:xfmcl_fixture_owner }
                 xfmcl_rules_trigger = yes
                 trigger_if = {
                  limit = { exists = global_var:xfm_exchange }
                  global_var:xfm_exchange = {
                   has_variable = xfm_day
                  var:xfm_day = 0
                   has_variable = xfm_registered_coin_count var:xfm_registered_coin_count = 0
                   has_variable = xfm_active_coin_count var:xfm_active_coin_count = 0
                   has_variable = xfm_pending_coin_count var:xfm_pending_coin_count = 0
                   NOT = { any_in_list = { variable = xfm_futures_contracts always = yes } }
                   trigger_if = { limit = { has_variable = xfm_next_futures_order_id } var:xfm_next_futures_order_id = 0 }
                   trigger_if = { limit = { has_variable = xfm_next_futures_position_id } var:xfm_next_futures_position_id = 0 }
                   NOT = { any_in_list = { variable = xfm_debts always = yes } }
                   trigger_if = { limit = { has_variable = xfm_debt_counter } var:xfm_debt_counter = 0 }
                  }
                 }
                }
                xfmcl_batch_trigger = {
                 xfmcl_owner_trigger = yes has_variable = xfmcl_seeded var:xfmcl_seeded = 1
                 var:xfmcl_count < var:xfmcl_target
                 NOT = { has_variable = xfmcl_batch_in_progress }
                }
                xfmcl_grow_trigger = {
                 xfmcl_owner_trigger = yes
                 var:xfmcl_count = 2048 var:xfmcl_hot_books = 64
                 has_variable = xfmcl_window1_ready var:xfmcl_window1_ready = 1
                 NOT = { has_variable = xfmcl_grow_attempted }
                 NOT = { has_variable = xfmcl_gap }
                }
                """);
        scripts.put("common/scripted_effects/xfmcl_seed.txt", """
                # SYNTHETIC GENESIS only. Deposit/transfer/reserve/mint/submit are production bodies.
                xfmcl_fail_effect = {
                 global_var:xfmcl_fixture_owner = {
                  if = { limit = { NOT = { has_variable = xfmcl_failed } }
                   set_variable = { name = xfmcl_failed value = 1 }
                   debug_log = "XFMAT: TEST FAIL synthetic_controlled_load_partial"
                  }
                 }
                }
                xfmcl_create_actor_effect = {
                 clear_saved_scope = xfmcl_new_actor
                 create_character = {
                  name = "SYNTHETIC market load fixture" gender = male age = 30 random_traits = no
                  location = root.capital_province culture = root.culture faith = root.faith
                  save_scope_as = xfmcl_new_actor
                 }
                 if = {
                  limit = { exists = scope:xfmcl_new_actor }
                  set_variable = { name = xfmcl_$ROLE$ value = scope:xfmcl_new_actor }
                  scope:xfmcl_new_actor = {
                   set_variable = { name = xfmcl_owner value = global_var:xfmcl_fixture_owner }
                   set_variable = { name = xfmcl_genesis_gold_before value = gold }
                   add_gold = 20000
                   set_variable = { name = xfmcl_genesis_gold_added value = 20000 }
                   set_variable = { name = xfmcl_genesis_gold_after value = gold }
                   xfm_finance_ensure_account_effect = yes
                   set_variable = { name = xfm_request_cents value = $CENTS$ }
                   xfm_finance_deposit_effect = yes
                   if = {
                    limit = { var:xfm_result = 1 exists = var:xfm_account }
                    set_variable = { name = xfmcl_deposit_cents value = $CENTS$ }
                    set_variable = { name = xfmcl_gold_after_deposit value = gold }
                    set_variable = { name = xfmcl_primary value = var:xfm_account }
                    set_variable = { name = xfmcl_role_ready value = 1 }
                    global_var:xfmcl_fixture_owner = {
                    change_variable = { name = xfmcl_genesis_deposited_cents add = $CENTS$ }
                    # Finite birth snapshots on the owner: no eight-actor selector expansion.
                    set_variable = { name = xfmcl_$ROLE$_gold_before value = scope:xfmcl_new_actor.var:xfmcl_genesis_gold_before }
                    set_variable = { name = xfmcl_$ROLE$_gold_after_add value = scope:xfmcl_new_actor.var:xfmcl_genesis_gold_after }
                    set_variable = { name = xfmcl_$ROLE$_gold_after_deposit value = scope:xfmcl_new_actor.var:xfmcl_gold_after_deposit }
                    set_variable = { name = xfmcl_$ROLE$_deposit_cents value = $CENTS$ }
                    set_variable = { name = xfmcl_$ROLE$_primary value = scope:xfmcl_new_actor.var:xfmcl_primary }
                   }
                   }
                   else = { xfmcl_fail_effect = yes }
                  }
                 }
                 else = { xfmcl_fail_effect = yes }
                 clear_saved_scope = xfmcl_new_actor
                }
                xfmcl_setup_effect = {
                 if = {
                  limit = { xfmcl_start_trigger = yes }
                  set_global_variable = { name = xfmcl_fixture_owner value = this }
                  set_variable = { name = xfmcl_setup_attempted value = 1 }
                  set_variable = { name = xfmcl_genesis_deposited_cents value = 0 }
                  set_variable = { name = xfmcl_count value = 0 }
                  set_variable = { name = xfmcl_hot_books value = 0 }
                  set_variable = { name = xfmcl_target value = 2048 }
                  set_variable = { name = xfmcl_role_cursor value = 1 }
                  set_variable = { name = xfmcl_batch_attempts value = 0 }
                  xfm_finance_bootstrap_effect = yes
                  xfmcl_create_actor_effect = { ROLE = buyer1 CENTS = 100000 }
                  xfmcl_create_actor_effect = { ROLE = buyer2 CENTS = 100000 }
                  xfmcl_create_actor_effect = { ROLE = buyer3 CENTS = 100000 }
                  xfmcl_create_actor_effect = { ROLE = buyer4 CENTS = 100000 }
                  xfmcl_create_actor_effect = { ROLE = seller1 CENTS = 1200000 }
                  xfmcl_create_actor_effect = { ROLE = seller2 CENTS = 1200000 }
                  xfmcl_create_actor_effect = { ROLE = seller3 CENTS = 1200000 }
                  xfmcl_create_actor_effect = { ROLE = seller4 CENTS = 1200000 }
                  if = {
                   limit = {
                    NOT = { has_variable = xfmcl_failed }
                    var:xfmcl_genesis_deposited_cents = 5200000
                    var:xfmcl_buyer1 = { var:xfmcl_role_ready = 1 }
                    var:xfmcl_buyer2 = { var:xfmcl_role_ready = 1 }
                    var:xfmcl_buyer3 = { var:xfmcl_role_ready = 1 }
                    var:xfmcl_buyer4 = { var:xfmcl_role_ready = 1 }
                    var:xfmcl_seller1 = { var:xfmcl_role_ready = 1 }
                    var:xfmcl_seller2 = { var:xfmcl_role_ready = 1 }
                    var:xfmcl_seller3 = { var:xfmcl_role_ready = 1 }
                    var:xfmcl_seller4 = { var:xfmcl_role_ready = 1 }
                   }
                   set_variable = { name = xfmcl_seeded value = 1 }
                  }
                  else = { xfmcl_fail_effect = yes }
                 }
                }
                xfmcl_reserve_effect = {
                 var:xfm_issuer_account = {
                  set_variable = { name = xfm_request_cents value = $CENTS$ }
                  xfm_finance_reserve_effect = yes
                  if = {
                   limit = { var:xfm_result = 1 exists = scope:xfm_reservation }
                   scope:xfm_offer_new_coin = { set_variable = { name = $FIELD$ value = scope:xfm_reservation } }
                  }
                  else = { xfmcl_fail_effect = yes }
                 }
                }
                xfmcl_make_coin_effect = {
                 if = { limit = { var:xfmcl_role_cursor = 1 } set_variable = { name = xfmcl_seller value = var:xfmcl_seller1 } set_variable = { name = xfmcl_buyer value = var:xfmcl_buyer1 } }
                 if = { limit = { var:xfmcl_role_cursor = 2 } set_variable = { name = xfmcl_seller value = var:xfmcl_seller2 } set_variable = { name = xfmcl_buyer value = var:xfmcl_buyer2 } }
                 if = { limit = { var:xfmcl_role_cursor = 3 } set_variable = { name = xfmcl_seller value = var:xfmcl_seller3 } set_variable = { name = xfmcl_buyer value = var:xfmcl_buyer3 } }
                 if = { limit = { var:xfmcl_role_cursor = 4 } set_variable = { name = xfmcl_seller value = var:xfmcl_seller4 } set_variable = { name = xfmcl_buyer value = var:xfmcl_buyer4 } }
                 clear_saved_scope = xfm_offer_new_coin
                 var:xfmcl_seller = {
                  save_scope_as = xfm_offer_applicant
                  set_variable = { name = xfm_requested_entity_type value = 1 }
                  set_variable = { name = xfm_requested_tier value = 1 }
                  set_variable = { name = xfm_requested_funding value = 20 }
                  xfm_finance_create_coin_effect = yes
                  if = {
                   limit = { var:xfm_result = 1 exists = scope:xfm_coin }
                   scope:xfm_coin = { save_scope_as = xfm_offer_new_coin }
                  }
                  else = { xfmcl_fail_effect = yes }
                 }
                 if = {
                  limit = { exists = scope:xfm_offer_new_coin NOT = { has_variable = xfmcl_failed } }
                  set_variable = { name = xfmcl_new_coin value = scope:xfm_offer_new_coin }
                  global_var:xfm_exchange = {
                   clear_saved_scope = xfm_created_account
                   xfm_finance_create_account_effect = yes
                   if = { limit = { var:xfm_result = 1 exists = scope:xfm_created_account } scope:xfm_offer_new_coin = { set_variable = { name = xfm_issuer_account value = scope:xfm_created_account } } }
                   else = { xfmcl_fail_effect = yes }
                   clear_saved_scope = xfm_created_account
                   xfm_finance_create_account_effect = yes
                   if = { limit = { var:xfm_result = 1 exists = scope:xfm_created_account } scope:xfm_offer_new_coin = { set_variable = { name = xfm_founder_account value = scope:xfm_created_account } } }
                   else = { xfmcl_fail_effect = yes }
                  }
                  if = {
                   limit = { NOT = { has_variable = xfmcl_failed } }
                   scope:xfm_offer_new_coin = {
                    xfm_issuer_initialize_effect = yes
                    # Initialization/defaults/mint are reused, not the public fee/IPO API.
                    set_variable = { name = xfm_registration_paid_cents value = 0 }
                    set_variable = { name = xfmcl_synthetic value = 1 }
                    set_variable = { name = xfmcl_owner value = global_var:xfmcl_fixture_owner }
                   }
                   var:xfmcl_seller.var:xfm_account = {
                    set_variable = { name = xfm_request_target value = scope:xfm_offer_new_coin.var:xfm_issuer_account }
                    set_variable = { name = xfm_request_cents value = 1000 }
                    xfm_finance_transfer_effect = yes
                    if = { limit = { NOT = { var:xfm_result = 1 } } xfmcl_fail_effect = yes }
                   }
                   scope:xfm_offer_new_coin = {
                    xfmcl_reserve_effect = { CENTS = 60 FIELD = xfm_maintenance_reservation }
                    xfmcl_reserve_effect = { CENTS = 100 FIELD = xfm_bond_reservation }
                    xfmcl_reserve_effect = { CENTS = 200 FIELD = xfm_maker_reservation }
                   }
                   if = {
                    limit = { NOT = { has_variable = xfmcl_failed } scope:xfm_offer_new_coin = { var:xfm_supply_units = 15000 exists = var:xfm_maintenance_reservation exists = var:xfm_bond_reservation exists = var:xfm_maker_reservation } }
                    scope:xfm_offer_new_coin = {
                     set_variable = { name = xfm_listing_state value = 1 }
                     set_variable = { name = xfm_trading_open value = 1 }
                     set_variable = { name = xfm_active_listing_counted value = 1 }
                     set_variable = { name = xfm_offer_counted value = 0 }
                     set_variable = { name = xfm_listing_allocated value = 1 }
                     set_variable = { name = xfm_listing_fee_collected value = 0 }
                     set_variable = { name = xfm_maintenance_age value = 0 }
                     set_variable = { name = xfm_last_price_cents value = 100 }
                    }
                    global_var:xfm_exchange = {
                     change_variable = { name = xfm_pending_coin_count subtract = 1 }
                     change_variable = { name = xfm_active_coin_count add = 1 }
                    }
                    change_variable = { name = xfmcl_count add = 1 }
                    add_to_variable_list = { name = xfmcl_coins target = scope:xfm_offer_new_coin }
                    if = { limit = { var:xfmcl_count = 1 } set_variable = { name = xfmcl_first_coin value = scope:xfm_offer_new_coin } }
                    if = { limit = { var:xfmcl_count <= 64 } xfmcl_hot_book_effect = yes }
                    change_variable = { name = xfmcl_role_cursor add = 1 }
                    if = { limit = { var:xfmcl_role_cursor > 4 } set_variable = { name = xfmcl_role_cursor value = 1 } }
                   }
                   else = { xfmcl_fail_effect = yes }
                  }
                 }
                }
                xfmcl_hot_book_effect = {
                 scope:xfm_offer_new_coin.var:xfm_issuer_account = {
                  set_variable = { name = xfm_request_coin value = scope:xfm_offer_new_coin }
                  set_variable = { name = xfm_request_target value = global_var:xfmcl_fixture_owner.var:xfmcl_seller.var:xfm_account }
                  set_variable = { name = xfm_request_units value = 100 }
                  xfm_finance_transfer_coin_effect = yes
                  if = { limit = { NOT = { var:xfm_result = 1 } } xfmcl_fail_effect = yes }
                 }
                 var:xfmcl_seller = {
                  set_variable = { name = xfm_selected_coin value = scope:xfm_offer_new_coin }
                  set_variable = { name = xfm_order_side value = 2 }
                  set_variable = { name = xfm_order_lots value = 1 }
                  set_variable = { name = xfm_order_limit_cents value = 101 }
                  set_variable = { name = xfm_order_ioc value = 0 }
                  xfm_spot_submit_effect = yes
                  if = { limit = { var:xfm_result = 1 exists = var:xfm_result_order var:xfm_result_order = { var:xfm_status = 1 var:xfm_remaining_lots = 1 var:xfm_filled_lots = 0 } } }
                  else = { xfmcl_fail_effect = yes }
                 }
                 var:xfmcl_buyer = {
                  set_variable = { name = xfm_selected_coin value = scope:xfm_offer_new_coin }
                  set_variable = { name = xfm_order_side value = 1 }
                  set_variable = { name = xfm_order_lots value = 1 }
                  set_variable = { name = xfm_order_limit_cents value = 99 }
                  set_variable = { name = xfm_order_ioc value = 0 }
                  xfm_spot_submit_effect = yes
                  if = { limit = { var:xfm_result = 1 exists = var:xfm_result_order var:xfm_result_order = { var:xfm_status = 1 var:xfm_remaining_lots = 1 var:xfm_filled_lots = 0 } } }
                  else = { xfmcl_fail_effect = yes }
                 }
                 if = { limit = { NOT = { has_variable = xfmcl_failed } } change_variable = { name = xfmcl_hot_books add = 1 } }
                }
                xfmcl_batch_effect = {
                 if = {
                  limit = { xfmcl_batch_trigger = yes }
                  set_variable = { name = xfmcl_batch_in_progress value = 1 }
                  change_variable = { name = xfmcl_batch_attempts add = 1 }
                  set_variable = { name = xfmcl_batch_left value = 32 }
                  while = {
                   limit = { var:xfmcl_batch_left > 0 var:xfmcl_count < var:xfmcl_target NOT = { has_variable = xfmcl_failed } }
                   change_variable = { name = xfmcl_batch_left subtract = 1 }
                   xfmcl_make_coin_effect = yes
                  }
                  remove_variable = xfmcl_batch_in_progress
                  if = {
                   limit = { var:xfmcl_count = 2048 NOT = { has_variable = xfmcl_complete2048 } NOT = { has_variable = xfmcl_failed } }
                   set_variable = { name = xfmcl_complete2048 value = 1 }
                   set_variable = { name = xfmcl_start1 value = current_date }
                   set_variable = { name = xfmcl_last_financial value = global_var:xfm_exchange.var:xfm_day }
                   set_variable = { name = xfmcl_samples1 value = 0 }
                   debug_log = "XFMAT: TEST PASS synthetic_load_2048_built"
                  }
                  if = {
                   limit = { var:xfmcl_count = 4096 NOT = { has_variable = xfmcl_complete4096 } NOT = { has_variable = xfmcl_failed } }
                   set_variable = { name = xfmcl_complete4096 value = 1 }
                   set_variable = { name = xfmcl_start2 value = current_date }
                   set_variable = { name = xfmcl_last_financial value = global_var:xfm_exchange.var:xfm_day }
                   set_variable = { name = xfmcl_samples2 value = 0 }
                   debug_log = "XFMAT: TEST PASS synthetic_load_4096_built"
                  }
                 }
                }
                xfmcl_grow_effect = {
                 if = {
                  limit = { xfmcl_grow_trigger = yes }
                  set_variable = { name = xfmcl_grow_attempted value = 1 }
                  set_variable = { name = xfmcl_target value = 4096 }
                 }
                }
                """);
        scripts.put("common/scripted_effects/xfmcl_observe.txt", """
                # Only the original current financial-tail observation hook invokes this recorder.
                xfmcl_after_finance_effect = {
                 if = {
                  limit = { exists = global_var:xfmcl_fixture_owner exists = global_var:xfm_exchange }
                  global_var:xfmcl_fixture_owner = {
                   if = { limit = { xfmcl_owner_trigger = yes has_variable = xfmcl_complete2048 NOT = { has_variable = xfmcl_window1_ready } } xfmcl_observe_stage_effect = { STAGE = 1 TARGET = 2048 } }
                   if = { limit = { xfmcl_owner_trigger = yes has_variable = xfmcl_complete4096 NOT = { has_variable = xfmcl_window2_ready } } xfmcl_observe_stage_effect = { STAGE = 2 TARGET = 4096 } }
                  }
                 }
                }
                xfmcl_observe_stage_effect = {
                 set_variable = { name = xfmcl_offset value = { value = current_date subtract = var:xfmcl_start$STAGE$ } }
                 if = {
                  limit = { var:xfmcl_offset >= 1 var:xfmcl_offset <= 8 }
                  if = {
                   limit = { NOT = { var:xfmcl_last_sample_date = current_date } }
                   # Presence is checked BEFORE any arithmetic. Missing is unknown and never a qualified zero.
                   if = {
                    limit = {
                     has_variable = xfmcl_last_financial
                     global_var:xfm_exchange = { has_variable = xfm_day }
                     var:xfmcl_offset = { value = var:xfmcl_samples$STAGE$ add = 1 }
                     global_var:xfm_exchange.var:xfm_day = { value = var:xfmcl_last_financial add = 1 }
                     var:xfmcl_count = $TARGET$
                     global_var:xfm_exchange = { var:xfm_active_coin_count = $TARGET$ var:xfm_resident_coin_count = $TARGET$ var:xfm_pending_coin_count = 0 }
                    }
                    change_variable = { name = xfmcl_samples$STAGE$ add = 1 }
                    set_variable = { name = xfmcl_last_sample_date value = current_date }
                    set_variable = { name = xfmcl_last_financial value = global_var:xfm_exchange.var:xfm_day }
                    if = { limit = { var:xfmcl_offset = 1 NOT = { has_variable = xfmcl_s$STAGE$_d1_recorded } } xfmcl_store_day_effect = { STAGE = $STAGE$ SLOT = 1 } }
                    if = { limit = { var:xfmcl_offset = 2 NOT = { has_variable = xfmcl_s$STAGE$_d2_recorded } } xfmcl_store_day_effect = { STAGE = $STAGE$ SLOT = 2 } }
                    if = { limit = { var:xfmcl_offset = 3 NOT = { has_variable = xfmcl_s$STAGE$_d3_recorded } } xfmcl_store_day_effect = { STAGE = $STAGE$ SLOT = 3 } }
                    if = { limit = { var:xfmcl_offset = 4 NOT = { has_variable = xfmcl_s$STAGE$_d4_recorded } } xfmcl_store_day_effect = { STAGE = $STAGE$ SLOT = 4 } }
                    if = { limit = { var:xfmcl_offset = 5 NOT = { has_variable = xfmcl_s$STAGE$_d5_recorded } } xfmcl_store_day_effect = { STAGE = $STAGE$ SLOT = 5 } }
                    if = { limit = { var:xfmcl_offset = 6 NOT = { has_variable = xfmcl_s$STAGE$_d6_recorded } } xfmcl_store_day_effect = { STAGE = $STAGE$ SLOT = 6 } }
                    if = { limit = { var:xfmcl_offset = 7 NOT = { has_variable = xfmcl_s$STAGE$_d7_recorded } } xfmcl_store_day_effect = { STAGE = $STAGE$ SLOT = 7 } }
                    if = { limit = { var:xfmcl_offset = 8 NOT = { has_variable = xfmcl_s$STAGE$_d8_recorded } } xfmcl_store_day_effect = { STAGE = $STAGE$ SLOT = 8 } }
                    if = {
                     limit = { var:xfmcl_samples$STAGE$ = 8 NOT = { has_variable = xfmcl_gap } }
                     set_variable = { name = xfmcl_window$STAGE$_ready value = 1 }
                     if = { limit = { var:xfmcl_count = 2048 } debug_log = "XFMAT: TEST PASS synthetic_load_2048_window_recorded" }
                     if = { limit = { var:xfmcl_count = 4096 } debug_log = "XFMAT: TEST PASS synthetic_load_4096_window_recorded" }
                    }
                   }
                   else = { set_variable = { name = xfmcl_gap value = 1 } }
                  }
                 }
                }
                xfmcl_store_day_effect = {
                 set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_date value = current_date }
                 set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_day_present value = 0 }
                 if = { limit = { global_var:xfm_exchange = { has_variable = xfm_day } }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_day value = global_var:xfm_exchange.var:xfm_day }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_day_present value = 1 }
                 }
                 set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_daily_raw_attempt_count_present value = 0 }
                 if = { limit = { global_var:xfm_exchange = { has_variable = xfm_daily_raw_attempt_count } }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_daily_raw_attempt_count value = global_var:xfm_exchange.var:xfm_daily_raw_attempt_count }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_daily_raw_attempt_count_present value = 1 }
                 }
                 set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_daily_attempt_count_present value = 0 }
                 if = { limit = { global_var:xfm_exchange = { has_variable = xfm_daily_attempt_count } }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_daily_attempt_count value = global_var:xfm_exchange.var:xfm_daily_attempt_count }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_daily_attempt_count_present value = 1 }
                 }
                 set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_daily_rejected_count_present value = 0 }
                 if = { limit = { global_var:xfm_exchange = { has_variable = xfm_daily_rejected_count } }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_daily_rejected_count value = global_var:xfm_exchange.var:xfm_daily_rejected_count }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_daily_rejected_count_present value = 1 }
                 }
                 set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_calendar_recovery_present value = 0 }
                 if = { limit = { global_var:xfm_exchange = { has_variable = xfm_calendar_recovery } }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_calendar_recovery value = global_var:xfm_exchange.var:xfm_calendar_recovery }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_calendar_recovery_present value = 1 }
                 }
                 set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_calendar_backlog_present value = 0 }
                 if = { limit = { global_var:xfm_exchange = { has_variable = xfm_calendar_backlog } }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_calendar_backlog value = global_var:xfm_exchange.var:xfm_calendar_backlog }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_calendar_backlog_present value = 1 }
                 }
                 set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_active_coin_count_present value = 0 }
                 if = { limit = { global_var:xfm_exchange = { has_variable = xfm_active_coin_count } }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_active_coin_count value = global_var:xfm_exchange.var:xfm_active_coin_count }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_active_coin_count_present value = 1 }
                 }
                 set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_resident_coin_count_present value = 0 }
                 if = { limit = { global_var:xfm_exchange = { has_variable = xfm_resident_coin_count } }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_resident_coin_count value = global_var:xfm_exchange.var:xfm_resident_coin_count }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_resident_coin_count_present value = 1 }
                 }
                 set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_registered_coin_count_present value = 0 }
                 if = { limit = { global_var:xfm_exchange = { has_variable = xfm_registered_coin_count } }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_registered_coin_count value = global_var:xfm_exchange.var:xfm_registered_coin_count }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_registered_coin_count_present value = 1 }
                 }
                 set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_pending_coin_count_present value = 0 }
                 if = { limit = { global_var:xfm_exchange = { has_variable = xfm_pending_coin_count } }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_pending_coin_count value = global_var:xfm_exchange.var:xfm_pending_coin_count }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_pending_coin_count_present value = 1 }
                 }
                 set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_ai_work_remaining_present value = 0 }
                 if = { limit = { global_var:xfm_exchange = { has_variable = xfm_ai_work_remaining } }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_ai_work_remaining value = global_var:xfm_exchange.var:xfm_ai_work_remaining }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_ai_work_remaining_present value = 1 }
                 }
                 set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_ai_decisions_today_present value = 0 }
                 if = { limit = { global_var:xfm_exchange = { has_variable = xfm_ai_decisions_today } }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_ai_decisions_today value = global_var:xfm_exchange.var:xfm_ai_decisions_today }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_ai_decisions_today_present value = 1 }
                 }
                 set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_ai_repair_work_today_present value = 0 }
                 if = { limit = { global_var:xfm_exchange = { has_variable = xfm_ai_repair_work_today } }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_ai_repair_work_today value = global_var:xfm_exchange.var:xfm_ai_repair_work_today }
                  set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_ai_repair_work_today_present value = 1 }
                 }
                 set_variable = { name = xfmcl_s$STAGE$_d$SLOT$_recorded value = 1 }
                }
                """);
        scripts.put("common/scripted_guis/xfmcl_controls.txt", """
                xfmcl_setup_gui = { scope = character is_shown = { is_ai = no } is_valid = { xfmcl_start_trigger = yes } effect = { xfmcl_setup_effect = yes } }
                xfmcl_batch_gui = { scope = character is_shown = { is_ai = no } is_valid = { xfmcl_batch_trigger = yes } effect = { xfmcl_batch_effect = yes } }
                xfmcl_grow_gui = { scope = character is_shown = { is_ai = no } is_valid = { xfmcl_grow_trigger = yes } effect = { xfmcl_grow_effect = yes } }
                """);
        scripts.put("gui/scripted_widgets/xfmcl_fixture.txt", """
                gui/xfmcl_fixture.gui = xfmcl_load_fixture_widget
                """);
        scripts.put("gui/xfmcl_fixture.gui", """
                window = {
                 name = "xfmcl_load_fixture_widget" parentanchor = top|right position = { -300 130 } size = { 260 150 } layer = middle
                 visible = "[GetPlayer.IsValid]"
                 button_standard = { name = "xfmcl_setup" position = { 10 10 } size = { 240 36 } text = "xfmcl_setup_label"
                  enabled = "[GetScriptedGui( 'xfmcl_setup_gui' ).IsValid( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
                  onclick = "[GetScriptedGui( 'xfmcl_setup_gui' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
                 }
                 button_standard = { name = "xfmcl_batch" position = { 10 52 } size = { 240 36 } text = "xfmcl_batch_label"
                  enabled = "[GetScriptedGui( 'xfmcl_batch_gui' ).IsValid( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
                  onclick = "[GetScriptedGui( 'xfmcl_batch_gui' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
                 }
                 button_standard = { name = "xfmcl_grow" position = { 10 94 } size = { 240 36 } text = "xfmcl_grow_label"
                  enabled = "[GetScriptedGui( 'xfmcl_grow_gui' ).IsValid( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
                  onclick = "[GetScriptedGui( 'xfmcl_grow_gui' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
                 }
                }
                """);
        scripts.put("localization/english/xfmcl_fixture_l_english.yml", """
                l_english:
                 xfmcl_setup_label:0 "SYNTHETIC: Genesis once"
                 xfmcl_batch_label:0 "SYNTHETIC: next 32 coins"
                 xfmcl_grow_label:0 "SYNTHETIC: enable 4096 stage"
                """);
        scripts.put("localization/simp_chinese/xfmcl_fixture_l_simp_chinese.yml", """
                l_simp_chinese:
                 xfmcl_setup_label:0 "SYNTHETIC: Genesis once"
                 xfmcl_batch_label:0 "SYNTHETIC: next 32 coins"
                 xfmcl_grow_label:0 "SYNTHETIC: enable 4096 stage"
                """);
        Map<String, byte[]> result = new LinkedHashMap<>();
        scripts.forEach((path, text) -> result.put(path,
                ("\ufeff" + text).getBytes(StandardCharsets.UTF_8)));
        return Map.copyOf(result);
    }
}
