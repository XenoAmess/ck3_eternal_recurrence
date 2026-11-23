package org.xar.ck3.markets.acceptance;

import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Declared isolated L2 world inputs. Original production APIs own every financial mutation.
 * Rendering never starts Game and never certifies an actual outcome. */
public final class ControlledFuturesRiskFixture {
    public static final String CASE_ID = "futures-risk-engine-fixture";
    private ControlledFuturesRiskFixture() { }
    public record Request(int schemaVersion, String caseId, boolean controlledFixtureOnly) {
        public Request {
            if (schemaVersion != 3 || !CASE_ID.equals(caseId) || !controlledFixtureOnly)
                throw new IllegalArgumentException("explicit schema3 isolated risk fixture required");
        }
    }
    public static List<String> markers() {
        return List.of("XFMAT: TEST PASS controlled_risk_seed_capture",
            "XFMAT: TEST PASS controlled_risk_book_and_world_capture",
            "XFMAT: TEST PASS controlled_risk_day1_capture",
            "XFMAT: TEST PASS controlled_risk_second_world_capture",
            "XFMAT: TEST PASS controlled_risk_day2_capture",
            "XFMAT: TEST PASS controlled_risk_same_day_retry_capture");
    }
    public static Map<String, byte[]> render(Request request) {
        Objects.requireNonNull(request, "explicit request");
        Map<String,String> scripts = new LinkedHashMap<>();
        scripts.put("descriptor.mod", "name=\"Controlled county-input futures risk fixture\"\nversion=\"1\"\nsupported_version=\"1.21.*\"\n");
        scripts.put("common/script_values/xfmr_values.txt", """
            # These are county input deltas, never a financial mark setter.
            xfmr_target_prosperity_value = {
             value = global_var:xfm_exchange.var:xfm_oracle_war_bps multiply = 0.5
             add = 5000 divide = 80 ceiling = yes
            }
            xfmr_control_prepare_delta_value = { value = 100 subtract = county_control }
            xfmr_prosperity_prepare_delta_value = {
             value = global_var:xfmr_fixture_owner.var:xfmr_target_prosperity subtract = prosperity_level
            }
            xfmr_control_shock_delta_value = { value = county_control multiply = -1 }
            """);
        scripts.put("common/scripted_triggers/xfmr_guards.txt", """
            xfmr_owner_trigger = {
             trigger_if = { limit = { exists = global_var:xfmr_fixture_owner }
              this = global_var:xfmr_fixture_owner is_ai = no is_alive = yes is_adult = yes }
             trigger_else = { always = no }
            }
            xfmr_fresh_trigger = {
             is_ai = no is_alive = yes is_adult = yes exists = capital_province
             NOT = { exists = global_var:xfmr_fixture_owner }
             trigger_if = { limit = { exists = global_var:xfm_exchange }
              global_var:xfm_exchange = {
               story_type = xfm_finance_exchange has_variable = xfm_day var:xfm_day = 0
               NOT = { any_in_list = { variable = xfm_futures_contracts always = yes } }
               trigger_if = { limit = { has_variable = xfm_next_futures_position_id } var:xfm_next_futures_position_id = 0 }
               trigger_if = { limit = { has_variable = xfm_next_futures_order_id } var:xfm_next_futures_order_id = 0 }
               trigger_if = { limit = { has_variable = xfm_debt_counter } var:xfm_debt_counter = 0 }
              }
             }
            }
            xfmr_world_trigger = {
             trigger_if = { limit = { exists = global_var:xfm_exchange }
              global_var:xfm_exchange = {
               has_variable = xfm_oracle_basket_count has_variable = xfm_oracle_war_bps
               var:xfm_oracle_basket_count >= 8 var:xfm_oracle_basket_count <= 32
               var:xfm_oracle_war_bps >= 0 var:xfm_oracle_war_bps <= 6000
              }
             }
             trigger_else = { always = no }
            }
            xfmr_actor_trigger = {
             trigger_if = { limit = { exists = var:xfmr_owner exists = var:xfm_account }
              is_ai = yes is_alive = yes is_adult = yes var:xfmr_owner = global_var:xfmr_fixture_owner
              var:xfm_account = { xfm_finance_account_usable_trigger = yes
               has_variable = xfm_account_id has_variable = xfm_system_account has_variable = xfm_free_cents
               has_variable = xfm_reserved_cents has_variable = xfm_account_frozen has_variable = xfm_inheritance_state
               exists = var:xfm_holder exists = var:xfm_beneficial_owner
               var:xfm_system_account = 0 var:xfm_inheritance_state = 0
               var:xfm_holder = prev var:xfm_beneficial_owner = prev NOT = { has_variable = xfm_legal_entity } }
             }
             trigger_else = { always = no }
            }
            xfmr_mark_trigger = {
             trigger_if = { limit = { exists = global_var:xfm_trade_index }
              global_var:xfm_trade_index = {
               story_type = xfm_oracle_index has_variable = xfm_index_id var:xfm_index_id = 3
               has_variable = xfm_model_quote_divisor var:xfm_model_quote_divisor = 100
               has_variable = xfm_index_cents has_variable = xfm_mark_cents
               var:xfm_index_cents = $MARK$ var:xfm_mark_cents = $MARK$
               has_variable = xfm_oracle_day has_variable = xfm_oracle_quality has_variable = xfm_max_leverage
               has_variable = xfm_derivatives_reduce_only
               var:xfm_oracle_day = global_var:xfm_exchange.var:xfm_day
               var:xfm_oracle_quality = 3 var:xfm_max_leverage = 5 var:xfm_derivatives_reduce_only = 0
              }
             }
             trigger_else = { always = no }
            }
            xfmr_book_trigger = {
             xfmr_owner_trigger = yes has_variable = xfmr_seeded
             NOT = { has_variable = xfmr_book_attempted }
             var:xfmr_seed_day = global_var:xfm_exchange.var:xfm_day
             xfmr_mark_trigger = { MARK = 150 }
             var:xfmr_long = { xfmr_actor_trigger = yes }
             var:xfmr_short = { xfmr_actor_trigger = yes }
             var:xfmr_maker = { xfmr_actor_trigger = yes }
            }
            xfmr_second_trigger = {
             xfmr_owner_trigger = yes has_variable = xfmr_day1_version
             has_variable = xfmr_shock1_qualified NOT = { has_variable = xfmr_second_attempted }
             global_var:xfm_exchange.var:xfm_day = { value = var:xfmr_book_day add = 1 }
             xfmr_mark_trigger = { MARK = 120 }
             exists = var:xfmr_gap_position
             var:xfmr_gap_position = { story_type = xfm_futures_position
              has_variable = xfm_status has_variable = xfm_mark_cents has_variable = xfm_last_settled_day
              exists = var:xfm_long_reservation exists = var:xfm_short_reservation
              var:xfm_status = 0 var:xfm_mark_cents = 120
              var:xfm_last_settled_day = global_var:xfm_exchange.var:xfm_day
              var:xfm_long_reservation = { story_type = xfm_finance_reservation has_variable = xfm_remaining_cents var:xfm_remaining_cents = 0 }
              NOT = { has_variable = xfm_pending_payment } }
            }
            """);
        scripts.put("common/scripted_effects/xfmr_seed.txt", """
            xfmr_create_actor_effect = {
             clear_saved_scope = xfmr_created_actor
             create_character = { name = "Controlled futures risk fixture" gender = male age = 30 random_traits = no
              location = root.capital_province culture = root.culture faith = root.faith save_scope_as = xfmr_created_actor }
             if = { limit = { exists = scope:xfmr_created_actor }
              set_variable = { name = xfmr_$ROLE$ value = scope:xfmr_created_actor }
              add_to_variable_list = { name = xfmr_actors target = scope:xfmr_created_actor }
              scope:xfmr_created_actor = {
               set_variable = { name = xfmr_owner value = global_var:xfmr_fixture_owner }
               set_variable = { name = xfmr_gold_before value = gold }
               add_gold = 20000
               set_variable = { name = xfmr_gold_after_seed value = gold }
               xfm_finance_ensure_account_effect = yes
               set_variable = { name = xfm_request_cents value = 100000 }
               xfm_finance_deposit_effect = yes
               if = { limit = { var:xfm_result = 1 xfmr_actor_trigger = yes }
                set_variable = { name = xfmr_gold_after_deposit value = gold }
                set_variable = { name = xfmr_seed_primary value = var:xfm_account }
                set_variable = { name = xfmr_seed_version value = 1 }
               }
              }
             }
             clear_saved_scope = xfmr_created_actor
            }
            xfmr_setup_effect = {
             if = { limit = { xfmr_fresh_trigger = yes }
              # Consume before any world input, actor creation or cash operation. No partial retry.
              set_global_variable = { name = xfmr_fixture_owner value = this }
              set_variable = { name = xfmr_setup_attempted value = 1 }
              xfm_finance_ensure_effect = yes
              global_var:xfm_exchange = { xfm_oracle_index_bootstrap_effect = yes xfm_oracle_index_daily_effect = yes }
              if = { limit = { xfmr_world_trigger = yes }
               set_variable = { name = xfmr_seed_day value = global_var:xfm_exchange.var:xfm_day }
               xfmr_prepare_world_inputs_effect = yes
               if = { limit = { xfmr_mark_trigger = { MARK = 150 } }
                xfmr_create_actor_effect = { ROLE = long }
                xfmr_create_actor_effect = { ROLE = short }
                xfmr_create_actor_effect = { ROLE = maker }
                if = { limit = {
                 var:xfmr_long = { xfmr_actor_trigger = yes has_variable = xfmr_seed_version }
                 var:xfmr_short = { xfmr_actor_trigger = yes has_variable = xfmr_seed_version }
                 var:xfmr_maker = { xfmr_actor_trigger = yes has_variable = xfmr_seed_version }
                 var:xfmr_long != var:xfmr_short var:xfmr_long != var:xfmr_maker var:xfmr_short != var:xfmr_maker
                }
                 var:xfmr_maker = {
                  set_variable = { name = xfm_ui_fund_donation_cents value = 100 }
                  set_variable = { name = xfmr_fund_before_donation value = global_var:xfm_exchange.var:xfm_default_fund_account.var:xfm_free_cents }
                  xfm_debt_donate_fund_effect = yes
                  if = { limit = { var:xfm_result = 1 var:xfm_last_fund_donation_cents = 100 }
                   set_variable = { name = xfmr_fund_after_donation value = global_var:xfm_exchange.var:xfm_default_fund_account.var:xfm_free_cents }
                   global_var:xfmr_fixture_owner = { set_variable = { name = xfmr_seeded value = 1 }
                    debug_log = "XFMAT: TEST PASS controlled_risk_seed_capture" }
                  }
                 }
                }
               }
              }
             }
            }
            """);
        scripts.put("common/scripted_effects/xfmr_world.txt", worldScripts());
        scripts.put("common/scripted_effects/xfmr_book.txt", """
            xfmr_submit_effect = {
             set_variable = { name = xfm_selected_coin value = global_var:xfm_trade_index }
             set_variable = { name = xfm_futures_perpetual value = 0 }
             set_variable = { name = xfm_futures_expiry_day value = { value = global_var:xfmr_fixture_owner.var:xfmr_seed_day add = $EXPIRY$ } }
             xfm_futures_ensure_market_effect = yes
             if = { limit = { var:xfm_futures_result = 1 exists = var:xfm_futures_contract }
              set_variable = { name = xfm_futures_side value = $SIDE$ }
              set_variable = { name = xfm_futures_lots value = $LOTS$ }
              set_variable = { name = xfm_futures_leverage value = $LEV$ }
              set_variable = { name = xfm_futures_limit_cents value = $PRICE$ }
              xfm_futures_submit_effect = yes
              if = { limit = { var:xfm_futures_result = 1 exists = scope:xfm_fut_incoming }
               global_var:xfmr_fixture_owner = { set_variable = { name = xfmr_$ROLE$_order value = scope:xfm_fut_incoming } }
              }
             }
            }
            xfmr_bind_pair_effect = {
             set_variable = { name = xfmr_binding_count value = 0 }
             var:xfmr_short.var:xfm_account = { every_in_list = { variable = xfm_positions
              limit = { story_type = xfm_futures_position var:xfm_status = 0 var:xfm_lots = $LOTS$
               var:xfm_long_account = global_var:xfmr_fixture_owner.var:xfmr_long.var:xfm_account
               var:xfm_short_account = global_var:xfmr_fixture_owner.var:xfmr_short.var:xfm_account
               var:xfm_fill_receipt_version = 1 var:xfm_fill_buy_intent = 0 var:xfm_fill_sell_intent = 0
               var:xfm_fill_buy_order_id = global_var:xfmr_fixture_owner.var:xfmr_$PAIR$_buy_order.var:xfm_order_id
               var:xfm_fill_sell_order_id = global_var:xfmr_fixture_owner.var:xfmr_$PAIR$_sell_order.var:xfm_order_id
              }
              save_scope_as = xfmr_bound_position
              global_var:xfmr_fixture_owner = { change_variable = { name = xfmr_binding_count add = 1 } }
             } }
             if = { limit = { var:xfmr_binding_count = 1 exists = scope:xfmr_bound_position }
              set_variable = { name = xfmr_$PAIR$_position value = scope:xfmr_bound_position }
              scope:xfmr_bound_position = { xfmr_position_capture_effect = { PHASE = entry } }
             }
             clear_saved_scope = xfmr_bound_position
            }
            xfmr_book_effect = {
             if = { limit = { xfmr_book_trigger = yes }
              set_variable = { name = xfmr_book_attempted value = 1 }
              set_variable = { name = xfmr_book_day value = global_var:xfm_exchange.var:xfm_day }
              var:xfmr_long = { xfmr_submit_effect = { ROLE = stop_buy EXPIRY = 30 SIDE = 1 LOTS = 1 LEV = 1 PRICE = 150 } }
              var:xfmr_short = { xfmr_submit_effect = { ROLE = stop_sell EXPIRY = 30 SIDE = 2 LOTS = 1 LEV = 1 PRICE = 150 } }
              xfmr_bind_pair_effect = { PAIR = stop LOTS = 1 }
              var:xfmr_long = { xfmr_submit_effect = { ROLE = liquidate_buy EXPIRY = 31 SIDE = 1 LOTS = 1 LEV = 5 PRICE = 150 } }
              var:xfmr_short = { xfmr_submit_effect = { ROLE = liquidate_sell EXPIRY = 31 SIDE = 2 LOTS = 1 LEV = 5 PRICE = 150 } }
              xfmr_bind_pair_effect = { PAIR = liquidate LOTS = 1 }
              var:xfmr_long = { xfmr_submit_effect = { ROLE = gap_buy EXPIRY = 32 SIDE = 1 LOTS = 100 LEV = 5 PRICE = 150 } }
              var:xfmr_short = { xfmr_submit_effect = { ROLE = gap_sell EXPIRY = 32 SIDE = 2 LOTS = 100 LEV = 5 PRICE = 150 } }
              xfmr_bind_pair_effect = { PAIR = gap LOTS = 100 }
              if = { limit = { exists = var:xfmr_stop_position exists = var:xfmr_liquidate_position exists = var:xfmr_gap_position }
               var:xfmr_long = {
                set_variable = { name = xfm_futures_selected_position value = global_var:xfmr_fixture_owner.var:xfmr_stop_position }
                set_variable = { name = xfm_futures_stop_cents value = 135 }
                set_variable = { name = xfm_futures_take_profit_cents value = 0 }
                xfm_futures_set_stops_effect = yes
               }
               if = { limit = { var:xfmr_stop_position.var:xfm_long_stop_cents = 135 }
                set_variable = { name = xfmr_booked value = 1 }
                xfmr_first_world_shock_effect = yes
               }
              }
             }
            }
            xfmr_first_world_shock_effect = {
             if = { limit = { xfmr_owner_trigger = yes has_variable = xfmr_booked
              NOT = { has_variable = xfmr_shock1_attempted } xfmr_mark_trigger = { MARK = 150 } }
              set_variable = { name = xfmr_shock1_attempted value = 1 }
              global_var:xfm_exchange = { every_in_list = { variable = xfm_oracle_counties limit = { exists = holder }
               change_county_control = xfmr_control_shock_delta_value
              } xfm_oracle_index_daily_effect = yes }
              xfmr_world_capture_effect = { PHASE = shock1 }
              if = { limit = { xfmr_mark_trigger = { MARK = 120 } }
               set_variable = { name = xfmr_shock1_qualified value = 1 }
               # Distinct dated contracts prevent the 120 bid consuming the stop contract's 110 bid.
               var:xfmr_maker = { xfmr_submit_effect = { ROLE = stop_replacement EXPIRY = 30 SIDE = 1 LOTS = 1 LEV = 1 PRICE = 110 } }
               var:xfmr_maker = { xfmr_submit_effect = { ROLE = liquidation_replacement EXPIRY = 31 SIDE = 1 LOTS = 1 LEV = 1 PRICE = 120 } }
               debug_log = "XFMAT: TEST PASS controlled_risk_book_and_world_capture"
              }
             }
            }
            """);
        scripts.put("common/scripted_effects/xfmr_observe.txt", observationScripts());
        scripts.put("common/on_action/xfmr_after_finance.txt", """
            xfm_finance_daily_observation_on_action = { on_actions = { xfmr_after_finance_on_action } }
            xfmr_after_finance_on_action = { effect = { xfmr_after_finance_effect = yes } }
            """);
        scripts.put("common/scripted_guis/xfmr_fixture.txt", """
            xfmr_setup_gui = { scope = character is_valid = { xfmr_fresh_trigger = yes } effect = { xfmr_setup_effect = yes } }
            xfmr_book_gui = { scope = character is_valid = { xfmr_book_trigger = yes } effect = { xfmr_book_effect = yes } }
            xfmr_second_gui = { scope = character is_valid = { xfmr_second_trigger = yes } effect = { xfmr_second_world_shock_effect = yes } }
            xfmr_retry_gui = { scope = character is_valid = { xfmr_owner_trigger = yes has_variable = xfmr_day2_version
             NOT = { has_variable = xfmr_retry_attempted } } effect = { xfmr_retry_effect = yes } }
            """);
        scripts.put("gui/scripted_widgets/xfmr_fixture.txt", "gui/xfmr_fixture.gui = xfmr_risk_fixture_widget\n");
        StringBuilder gui = new StringBuilder("window = { name = \"xfmr_risk_fixture_widget\" parentanchor = top|right position = { -330 130 } size = { 270 168 } layer = middle visible = \"[GetPlayer.IsValid]\"\n");
        int y=0; for(String action:List.of("setup","book","second","retry")) {
            gui.append("button_standard = { name = \"xfmr_").append(action).append("\" position = { 0 ").append(y).append(" } size = { 270 40 } text = \"xfmr_").append(action).append("_label\"\n")
                .append("enabled = \"[GetScriptedGui( 'xfmr_").append(action).append("_gui' ).IsValid( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]\"\n")
                .append("onclick = \"[GetScriptedGui( 'xfmr_").append(action).append("_gui' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]\" }\n"); y+=42;
        }
        scripts.put("gui/xfmr_fixture.gui",gui.append("}\n").toString());
        for(String language:List.of("english","simp_chinese")) scripts.put("localization/"+language+"/xfmr_l_"+language+".yml",
            "l_"+language+":\n xfmr_setup_label:0 \"Risk fixture: seed / county preparation\"\n xfmr_book_label:0 \"Risk fixture: real orders / control shock\"\n xfmr_second_label:0 \"Risk fixture: day1 prosperity shock\"\n xfmr_retry_label:0 \"Risk fixture: day2 original retry capture\"\n");
        Map<String,byte[]> result=new LinkedHashMap<>();
        scripts.forEach((path,text)->result.put(path,("\ufeff"+text).getBytes(StandardCharsets.UTF_8)));
        return Map.copyOf(result);
    }

    private static String worldScripts() {
        StringBuilder out=new StringBuilder("""
            xfmr_prepare_world_inputs_effect = {
             if = { limit = { xfmr_owner_trigger = yes xfmr_world_trigger = yes
              NOT = { has_variable = xfmr_world_prepare_attempted } }
              set_variable = { name = xfmr_world_prepare_attempted value = 1 }
              set_variable = { name = xfmr_target_prosperity value = xfmr_target_prosperity_value }
              xfmr_world_capture_effect = { PHASE = original }
              global_var:xfm_exchange = { every_in_list = { variable = xfm_oracle_counties limit = { exists = holder }
               change_county_control = xfmr_control_prepare_delta_value
               change_prosperity_level = xfmr_prosperity_prepare_delta_value
              } xfm_oracle_index_daily_effect = yes }
              xfmr_world_capture_effect = { PHASE = prepared }
             }
            }
            xfmr_world_capture_effect = {
             if = { limit = { NOT = { has_variable = xfmr_$PHASE$_world_version } }
              set_variable = { name = xfmr_county_slot value = 0 }
              global_var:xfm_exchange = { every_in_list = { variable = xfm_oracle_counties limit = { exists = holder }
               global_var:xfmr_fixture_owner = { change_variable = { name = xfmr_county_slot add = 1 } }
               xfmr_capture_county_effect = { PHASE = $PHASE$ }
              } }
              set_variable = { name = xfmr_$PHASE$_world_day value = global_var:xfm_exchange.var:xfm_day }
              set_variable = { name = xfmr_$PHASE$_world_script_date value = current_date }
              set_variable = { name = xfmr_$PHASE$_county_count value = var:xfmr_county_slot }
              set_variable = { name = xfmr_$PHASE$_world_version value = 1 }
            """);
        for(String field:List.of("xfm_oracle_basket_count","xfm_oracle_war_count","xfm_oracle_war_bps","xfm_oracle_average_prosperity","xfm_oracle_average_control","xfm_oracle_trade_value"))
            out.append(capture("global_var:xfm_exchange",field,"xfmr_$PHASE$_"+field));
        for(String field:List.of("xfm_index_id","xfm_model_quote_divisor","xfm_index_cents","xfm_mark_cents","xfm_oracle_day","xfm_oracle_quality","xfm_max_leverage"))
            out.append(capture("global_var:xfm_trade_index",field,"xfmr_$PHASE$_"+field));
        out.append("} }\nxfmr_capture_county_effect = {\n");
        for(int i=1;i<=32;i++) out.append("if = { limit = { global_var:xfmr_fixture_owner.var:xfmr_county_slot = "+i+" }\n")
            .append("save_scope_as = xfmr_actual_county\nsave_scope_value_as = { name = xfmr_actual_control value = county_control }\n")
            .append("save_scope_value_as = { name = xfmr_actual_prosperity value = prosperity_level }\n")
            .append("global_var:xfmr_fixture_owner = { set_variable = { name = xfmr_$PHASE$_county"+i+" value = scope:xfmr_actual_county }\n")
            .append("set_variable = { name = xfmr_$PHASE$_holder"+i+" value = scope:xfmr_actual_county.holder }\n")
            .append("set_variable = { name = xfmr_$PHASE$_control"+i+" value = scope:xfmr_actual_control }\n")
            .append("set_variable = { name = xfmr_$PHASE$_prosperity"+i+" value = scope:xfmr_actual_prosperity }\n")
            .append("set_variable = { name = xfmr_$PHASE$_war"+i+" value = 0 } }\n")
            .append("if = { limit = { holder = { is_at_war = yes } } global_var:xfmr_fixture_owner = { set_variable = { name = xfmr_$PHASE$_war"+i+" value = 1 } } } }\n");
        return out.append("clear_saved_scope = xfmr_actual_county\n}\n").toString();
    }
    private static String capture(String scope,String field,String name) {
        return "set_variable = { name = "+name+"_present value = 0 }\nif = { limit = { "+scope+" = { has_variable = "+field+" } }\n"
            +"set_variable = { name = "+name+"_present value = 1 } set_variable = { name = "+name+" value = "+scope+".var:"+field+" } }\n";
    }
    private static String observationScripts() {
        StringBuilder out=new StringBuilder("xfmr_position_capture_effect = { if = { limit = { NOT = { has_variable = xfmr_$PHASE$_version } }\n");
        out.append("set_variable = { name = xfmr_$PHASE$_day value = global_var:xfm_exchange.var:xfm_day }\n");
        for(String field:List.of("xfm_position_id","xfm_contract_id","xfm_contract","xfm_coin","xfm_lots","xfm_status","xfm_mark_cents","xfm_created_day",
            "xfm_long_account","xfm_short_account","xfm_long_reservation","xfm_short_reservation","xfm_long_leverage","xfm_short_leverage",
            "xfm_long_stop_cents","xfm_long_exit_requested","xfm_source_position","xfm_last_settled_day","xfm_pending_payment","xfm_pending_kind",
            "xfm_pending_amount","xfm_pending_paid","xfm_pay_now","xfm_shortfall","xfm_defaulted","xfm_debt_receipt_1","xfm_debt_receipt_3",
            "xfm_fill_receipt_version","xfm_fill_day","xfm_fill_lots","xfm_fill_mark_cents","xfm_fill_buy_order_id","xfm_fill_sell_order_id",
            "xfm_fill_buy_account_id","xfm_fill_sell_account_id","xfm_fill_buy_intent","xfm_fill_sell_intent","xfm_fill_buy_close_source_id",
            "xfm_fill_sell_close_source_id","xfm_fill_slice_source_position_id")) out.append(capture("this",field,"xfmr_$PHASE$_"+field));
        for(String side:List.of("long","short")) {
            for(String field:List.of("xfm_account_id","xfm_holder","xfm_beneficial_owner","xfm_free_cents","xfm_reserved_cents"))
                out.append(capture("var:xfm_"+side+"_account",field,"xfmr_$PHASE$_"+side+"_"+field));
            for(String field:List.of("xfm_reservation_id","xfm_remaining_cents","xfm_status"))
                out.append(capture("var:xfm_"+side+"_reservation",field,"xfmr_$PHASE$_"+side+"_"+field));
        }
        for(String kind:List.of("1","3")) for(String field:List.of("xfm_debt_id","xfm_source","xfm_source_day","xfm_source_kind",
            "xfm_debtor_account","xfm_creditor_account","xfm_original_cents","xfm_outstanding_cents","xfm_winner_unpaid_cents",
            "xfm_fund_paid_cents","xfm_fund_recourse_cents","xfm_repaid_cents","xfm_written_off_cents","xfm_fund_eligible"))
            out.append(capture("var:xfm_debt_receipt_"+kind,field,"xfmr_$PHASE$_claim"+kind+"_"+field));
        out.append("set_variable = { name = xfmr_$PHASE$_version value = 1 } } }\n");
        out.append("""
            xfmr_capture_all_effect = {
             if = { limit = { NOT = { has_variable = xfmr_$PHASE$_version } }
              xfmr_world_capture_effect = { PHASE = $PHASE$ }
              var:xfmr_stop_position = { xfmr_position_capture_effect = { PHASE = $PHASE$ } }
              var:xfmr_liquidate_position = { xfmr_position_capture_effect = { PHASE = $PHASE$ } }
              var:xfmr_gap_position = { xfmr_position_capture_effect = { PHASE = $PHASE$ } }
              set_variable = { name = xfmr_$PHASE$_fee_cents value = global_var:xfm_exchange.var:xfm_fee_cents }
              set_variable = { name = xfmr_$PHASE$_fund_free_cents value = global_var:xfm_exchange.var:xfm_default_fund_account.var:xfm_free_cents }
              set_variable = { name = xfmr_$PHASE$_fund_allocated_present value = 0 }
              if = { limit = { global_var:xfm_exchange = { has_variable = xfm_default_fund_allocated_cents } }
               set_variable = { name = xfmr_$PHASE$_fund_allocated_present value = 1 }
               set_variable = { name = xfmr_$PHASE$_fund_allocated value = global_var:xfm_exchange.var:xfm_default_fund_allocated_cents } }
              set_variable = { name = xfmr_$PHASE$_version value = 1 }
             }
            }
            xfmr_after_finance_effect = {
             if = { limit = { exists = global_var:xfmr_fixture_owner }
              global_var:xfmr_fixture_owner = {
               if = { limit = { has_variable = xfmr_shock1_qualified
                global_var:xfm_exchange.var:xfm_day = { value = var:xfmr_book_day add = 1 }
                NOT = { has_variable = xfmr_day1_version } }
                xfmr_capture_all_effect = { PHASE = day1 }
                debug_log = "XFMAT: TEST PASS controlled_risk_day1_capture"
               }
               if = { limit = { has_variable = xfmr_shock2_qualified
                global_var:xfm_exchange.var:xfm_day = { value = var:xfmr_book_day add = 2 }
                NOT = { has_variable = xfmr_day2_version } }
                xfmr_capture_all_effect = { PHASE = day2 }
                debug_log = "XFMAT: TEST PASS controlled_risk_day2_capture"
               }
              }
             }
            }
            xfmr_second_world_shock_effect = {
             if = { limit = { xfmr_second_trigger = yes }
              set_variable = { name = xfmr_second_attempted value = 1 }
              global_var:xfm_exchange = { every_in_list = { variable = xfm_oracle_counties limit = { exists = holder }
               change_prosperity_level = -25
              } xfm_oracle_index_daily_effect = yes }
              xfmr_world_capture_effect = { PHASE = shock2 }
              if = { limit = { xfmr_mark_trigger = { MARK = 100 } }
               set_variable = { name = xfmr_shock2_qualified value = 1 }
               debug_log = "XFMAT: TEST PASS controlled_risk_second_world_capture"
              }
             }
            }
            xfmr_retry_effect = {
             if = { limit = { xfmr_owner_trigger = yes has_variable = xfmr_day2_version
              NOT = { has_variable = xfmr_retry_attempted }
              global_var:xfm_exchange.var:xfm_day = { value = var:xfmr_book_day add = 2 } }
              set_variable = { name = xfmr_retry_attempted value = 1 }
              xfmr_capture_all_effect = { PHASE = retry_before }
              var:xfmr_stop_position = { xfm_futures_position_daily_effect = yes }
              var:xfmr_liquidate_position = { xfm_futures_position_daily_effect = yes }
              var:xfmr_gap_position = { xfm_futures_position_daily_effect = yes }
              # Retry only the retained original source/day/kind/amount tuple, never author a new claim.
              var:xfmr_gap_position = {
               if = { limit = { exists = var:xfm_debt_receipt_1 has_variable = xfm_request_cents
                exists = var:xfm_request_debtor exists = var:xfm_request_creditor
                has_variable = xfm_request_day var:xfm_request_kind = 1
                var:xfm_debt_receipt_1 = { var:xfm_source = prev
                 var:xfm_source_day = prev.var:xfm_request_day var:xfm_original_cents = prev.var:xfm_request_cents
                 var:xfm_debtor_account = prev.var:xfm_request_debtor var:xfm_creditor_account = prev.var:xfm_request_creditor }
               }
                xfm_debt_cover_shortfall_effect = yes
                set_variable = { name = xfmr_retry_cover_result value = var:xfm_result }
               }
              }
              xfmr_capture_all_effect = { PHASE = retry_after }
              debug_log = "XFMAT: TEST PASS controlled_risk_same_day_retry_capture"
             }
            }
            """);
        return out.toString();
    }
}
