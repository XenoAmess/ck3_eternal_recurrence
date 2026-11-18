package org.xar.ck3.markets.acceptance;

import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Independent observers. No production mutation, production effect call or artificial counterparty. */
public final class ObservationScripts {
    private ObservationScripts() { }
    public static final List<String> MARKERS = List.of("XFMAT: TEST PASS fixture_ready",
            "XFMAT: TEST PASS registered_owned_coin", "XFMAT: TEST PASS selected_coin_supply_conserved",
            "XFMAT: TEST PASS selected_coin_two_trades", "XFMAT: TEST PASS nonnegative_accounts");

    public static Map<String, byte[]> render(AcceptanceContracts.Request request) {
        Map<String, String> scripts = new LinkedHashMap<>();
        scripts.put("descriptor.mod", "name=\"Financial market read-only acceptance observer\"\nversion=\"1\"\nsupported_version=\"1.21.*\"\n");
        scripts.put("common/on_action/xfma_start.txt", """
                # Observer state uses xfma_ only. The product itself performs all business.
                on_game_start_after_lobby = { on_actions = { xfma_start } }
                xfma_start = {
                    effect = {
                        every_player = {
                            if = {
                                limit = { this = character:${ACTOR} NOT = { has_variable = xfma_armed } }
                                xfma_arm_observer_effect = yes
                            }
                            else = { debug_log = "XFMAT: TEST FAIL wrong_actor_or_repeated_fresh_start" }
                        }
                    }
                }
                """);
        scripts.put("common/scripted_guis/xfma_observer.txt", """
                # Ordinary observation-only arming permits a converted SavedGame without inventing after_lobby.
                xfma_arm_observer_gui = {
                    scope = character
                    is_valid = { is_ai = no is_alive = yes this = character:${ACTOR} NOT = { has_variable = xfma_armed } }
                    effect = { xfma_arm_observer_effect = yes }
                }
                """);
        scripts.put("gui/scripted_widgets/xfma_observer.txt", "gui/xfma_observer.gui = xfma_observer_widget\n");
        scripts.put("gui/xfma_observer.gui", """
                window = {
                    name = "xfma_observer_widget"
                    parentanchor = top|right
                    position = { -290 130 }
                    size = { 220 40 }
                    layer = middle
                    visible = "[GetPlayer.IsValid]"
                    button_standard = {
                        name = "xfma_arm_observer"
                        size = { 220 40 }
                        text = "xfma_arm_observer_label"
                        tooltip = "xfma_arm_observer_tooltip"
                        enabled = "[GetScriptedGui( 'xfma_arm_observer_gui' ).IsValid( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
                        onclick = "[GetScriptedGui( 'xfma_arm_observer_gui' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
                    }
                }
                """);
        scripts.put("localization/english/xfma_observer_l_english.yml", """
                l_english:
                 xfma_arm_observer_label:0 "Start market observation"
                 xfma_arm_observer_tooltip:0 "Record the current player's baseline. This observer changes no money, coins, orders or positions."
                """);
        scripts.put("localization/simp_chinese/xfma_observer_l_simp_chinese.yml", """
                l_simp_chinese:
                 xfma_arm_observer_label:0 "开始市场验收观察"
                 xfma_arm_observer_tooltip:0 "记录当前角色的验收基线。观察器不修改金钱、币、订单或仓位。"
                """);
        scripts.put("common/script_values/xfma_values.txt", """
                xfma_gold_cents = { value = gold multiply = 100 floor = yes }
                """);
        scripts.put("common/story_cycles/xfma_observer.txt", """
                xfma_observer = {
                    on_owner_death = { debug_log = "XFMAT: TEST FAIL observer_actor_died" }
                    effect_group = {
                        days = 1
                        trigger = { NOT = { has_variable = xfma_complete } }
                        triggered_effect = {
                            trigger = { exists = story_owner }
                            effect = {
                                save_scope_as = xfma_observer_story
                                story_owner = { xfma_observe_effect = yes }
                            }
                        }
                    }
                }
                """);
        scripts.put("common/scripted_effects/xfma_observe.txt", """
                # Observation-only effects. Never calls an xfm_ production effect or writes its business state.
                xfma_arm_observer_effect = {
                    if = {
                        limit = { this = character:${ACTOR} NOT = { has_variable = xfma_armed } }
                        set_variable = { name = xfma_armed value = 1 }
                        set_variable = { name = xfma_start_gold_cents value = xfma_gold_cents }
                        set_variable = { name = xfma_start_date value = current_date }
                        create_story = { type = xfma_observer }
                        debug_log = "XFMAT: TEST PASS fixture_ready"
                    }
                }
                xfma_observe_effect = {
                    save_scope_as = xfma_actor
                    if = {
                        limit = {
                            NOT = { has_variable = xfma_registration_seen }
                            exists = var:xfm_personal_coin
                            var:xfm_personal_coin = {
                                story_type = xfm_finance_coin
                                var:xfm_original_issuer = scope:xfma_actor
                                var:xfm_registration_paid_cents > 0
                                exists = var:xfm_issuer_account
                                exists = var:xfm_founder_account
                            }
                        }
                        set_variable = { name = xfma_registration_seen value = 1 }
                        debug_log = "XFMAT: TEST PASS registered_owned_coin"
                    }
                    if = {
                        limit = { exists = var:xfm_selected_coin var:xfm_selected_coin = { story_type = xfm_finance_coin } }
                        if = {
                            limit = { NOT = { exists = var:xfma_observed_coin } }
                            set_variable = { name = xfma_observed_coin value = var:xfm_selected_coin }
                        }
                        set_variable = { name = xfma_units_total value = 0 }
                        set_variable = { name = xfma_position_error value = 0 }
                        var:xfma_observed_coin = {
                            every_in_list = {
                                variable = xfm_holders
                                if = {
                                    limit = {
                                        story_type = xfm_finance_position
                                        var:xfm_coin = scope:xfma_actor.var:xfma_observed_coin
                                        var:xfm_quantity_units >= 0
                                        var:xfm_reserved_units >= 0
                                        var:xfm_reserved_units <= var:xfm_quantity_units
                                    }
                                    scope:xfma_actor = { change_variable = { name = xfma_units_total add = prev.var:xfm_quantity_units } }
                                }
                                else = { scope:xfma_actor = { set_variable = { name = xfma_position_error value = 1 } } }
                            }
                        }
                        if = {
                            limit = {
                                NOT = { has_variable = xfma_supply_seen }
                                var:xfma_position_error = 0
                                var:xfma_observed_coin = { var:xfm_supply_units = scope:xfma_actor.var:xfma_units_total var:xfm_supply_units > 0 }
                            }
                            set_variable = { name = xfma_supply_seen value = 1 }
                            debug_log = "XFMAT: TEST PASS selected_coin_supply_conserved"
                        }
                        if = {
                            limit = { NOT = { has_variable = xfma_two_trades_seen } var:xfma_observed_coin = { var:xfm_actual_trades >= 2 } }
                            set_variable = { name = xfma_two_trades_seen value = 1 }
                            debug_log = "XFMAT: TEST PASS selected_coin_two_trades"
                        }
                    }
                    xfma_observe_accounts_effect = yes
                    if = {
                        limit = { has_variable = xfma_registration_seen has_variable = xfma_supply_seen has_variable = xfma_two_trades_seen has_variable = xfma_accounts_seen }
                        scope:xfma_observer_story = { set_variable = { name = xfma_complete value = 1 } }
                    }
                }
                xfma_observe_accounts_effect = {
                    if = {
                        limit = { NOT = { has_variable = xfma_accounts_seen } exists = global_var:xfm_exchange exists = var:xfm_account }
                        set_variable = { name = xfma_account_error value = 0 }
                        every_in_global_list = {
                            variable = xfm_account_registry
                            if = {
                                limit = { OR = { NOT = { story_type = xfm_finance_account } var:xfm_free_cents < 0 var:xfm_reserved_cents < 0 } }
                                scope:xfma_actor = { set_variable = { name = xfma_account_error value = 1 } }
                            }
                        }
                        if = {
                            limit = { var:xfma_account_error = 0 var:xfm_account = { story_type = xfm_finance_account var:xfm_holder = scope:xfma_actor var:xfm_system_account = 0 } }
                            set_variable = { name = xfma_accounts_seen value = 1 }
                            debug_log = "XFMAT: TEST PASS nonnegative_accounts"
                        }
                        else = { debug_log = "XFMAT: TEST FAIL account_identity_or_negative_cash" }
                    }
                }
                """);
        Map<String, byte[]> result = new LinkedHashMap<>();
        scripts.forEach((name, text) -> result.put(name, ("\ufeff" + text.replace("${ACTOR}", request.actorHistoryId())).getBytes(StandardCharsets.UTF_8)));
        return Map.copyOf(result);
    }
}
