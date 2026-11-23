package org.xar.ck3.markets.acceptance;

import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;
import org.xar.ck3.markets.acceptance.FollowupContracts.ControlledCrisis20Request;

/** Explicit controlled inputs only. Roles, identity and context are never invented.
 * One bounded registry binding; no daily fixture callback, new clock, cash seed or direct death/news.
 */
public final class ControlledCrisis20Fixture {
    private ControlledCrisis20Fixture() { }
    public static Map<String, byte[]> render(ControlledCrisis20Request request, String selectorSource) {
        java.util.Objects.requireNonNull(request);
        Map<String, byte[]> result = new LinkedHashMap<>(CrisisSceneBranchFixture.render(selectorSource));
        Map<String, String> text = new LinkedHashMap<>();
        text.put("descriptor.mod", "name=\"Controlled crisis20 fixture (not natural probability)\"\nversion=\"1\"\nsupported_version=\"1.21.*\"\n");
        text.put("common/story_cycles/xfmc20_sources.txt", "xfmd_claim_source = { visible = no }\n");
        text.put("common/script_values/xfmc20_values.txt", "xfmc20_source_day_value = { value = global_var:xfm_exchange.var:xfm_day subtract = 30 }\n");
        StringBuilder guards = new StringBuilder("""
            xfmc20_owner_trigger = {
             exists = global_var:xfmc20_owner
             trigger_if = { limit = { exists = global_var:xfmc20_owner } this = global_var:xfmc20_owner }
             is_alive = yes is_adult = yes is_ai = no
            }
            xfmc20_account_trigger = {
             story_type = xfm_finance_account exists = var:xfm_holder
             var:xfm_system_account = 0
             var:xfm_holder = { is_alive = yes }
            }
            xfmc20_empty_primary_trigger = {
             xfmc20_account_trigger = yes var:xfm_inheritance_state = 0 var:xfm_account_frozen = 0
             var:xfm_holder = { is_ai = yes is_adult = yes gold <= 0 var:xfm_account = prev }
             xfm_crisis_account_known_empty_trigger = yes
             NOT = { has_variable = xfm_crisis_terminal }
             OR = { NOT = { has_variable = xfm_total_debt_cents } var:xfm_total_debt_cents = 0 }
             xfm_debt_income_threshold_value < 1000000
            }
            xfmc20_start_trigger = {
             is_alive = yes is_adult = yes is_ai = no exists = global_var:xfm_exchange
             NOT = { exists = global_var:xfmc20_owner }
             NOT = { has_variable = xfmc20_setup_attempted }
             trigger_if = { limit = { exists = global_var:xfm_exchange }
              global_var:xfm_exchange = { has_variable = xfm_day var:xfm_day >= 30 has_variable = xfm_next_account_id var:xfm_next_account_id <= 65536 }
             }
             exists = var:xfm_account
             trigger_if = { limit = { exists = var:xfm_account }
              var:xfm_account = { xfmc20_account_trigger = yes var:xfm_holder = root var:xfm_account_id = ${PLAYER} }
             }
            }
            xfmc20_controls_ready_trigger = {
             exists = var:xfmc20_aid_claim exists = var:xfmc20_restructure_claim
             trigger_if = { limit = { exists = var:xfmc20_aid_claim exists = var:xfmc20_restructure_claim }
              var:xfmc20_aid_claim = { var:xfm_repaid_cents >= 1000 var:xfm_request_payer = root.var:xfm_account }
              var:xfmc20_restructure_claim = { has_variable = xfm_creditor_haircut_done has_variable = xfm_extension_granted var:xfm_written_off_cents > 0 var:xfm_creditor_account = root.var:xfm_account }
              var:xfmc20_aid = { has_variable = xfm_crisis_relief_until trigger_if = { limit = { has_variable = xfm_crisis_relief_until } var:xfm_crisis_relief_until > global_var:xfm_exchange.var:xfm_day } NOT = { xfm_crisis_terminal_review_trigger = yes } }
              var:xfmc20_restructure = { has_variable = xfm_crisis_relief_until trigger_if = { limit = { has_variable = xfm_crisis_relief_until } var:xfm_crisis_relief_until > global_var:xfm_exchange.var:xfm_day } NOT = { xfm_crisis_terminal_review_trigger = yes } }
             }
            }
            """);
        StringBuilder binding = new StringBuilder("""
            xfmc20_setup_effect = {
             if = { limit = { xfmc20_start_trigger = yes }
              set_variable = { name = xfmc20_setup_attempted value = 1 }
              set_global_variable = { name = xfmc20_owner value = this }
              set_variable = { name = xfmc20_seed_day value = global_var:xfm_exchange.var:xfm_day }
              set_variable = { name = xfmc20_bound_count value = 0 }
              every_in_global_list = { variable = xfm_account_registry
            """);
        bind(binding, "player", request.playerAccountId());
        bind(binding, "creditor", request.aidCreditorAccountId());
        for (var scene : request.scenes()) bind(binding, key(scene.sceneId()), scene.accountId());
        var controls = request.controls();
        bind(binding, "child", controls.childAccountId()); bind(binding, "estate", controls.inheritedAccountId());
        bind(binding, "asset", controls.assetAccountId()); bind(binding, "aid", controls.aidAccountId());
        bind(binding, "restructure", controls.restructureAccountId());
        binding.append(" }\n if = { limit = { xfmc20_bound_trigger = yes }\n");
        for (var scene : request.scenes()) seed(binding, key(scene.sceneId()), "player");
        for (String role : new String[]{"player", "child", "estate", "asset", "restructure"}) seed(binding, role, role.equals("player") ? "creditor" : "player");
        seed(binding, "aid", "creditor");
        binding.append(" if = { limit = { NOT = { has_variable = xfmc20_setup_failed } } set_variable = { name = xfmc20_seeded value = 1 } debug_log = \"XFMAT: TEST PASS controlled_crisis20_setup_recorded\" }\n }\n }\n}\n");
        guards.append("xfmc20_bound_trigger = { var:xfmc20_bound_count = 27\n");
        guards.append("var:xfmc20_player = { xfmc20_account_trigger = yes var:xfm_holder = root var:xfm_account_id = ${PLAYER} }\n");
        guards.append("var:xfmc20_creditor = { xfmc20_account_trigger = yes var:xfm_holder = { is_ai = yes is_adult = yes } }\n");
        for (var scene : request.scenes()) {
            String role = key(scene.sceneId());
            guards.append("var:xfmc20_creditor.var:xfm_holder != var:xfmc20_").append(role).append(".var:xfm_holder\n");
            guards.append("var:xfmc20_").append(role).append(" = { xfmc20_empty_primary_trigger = yes var:xfm_holder = { save_temporary_scope_as = xfm_crisis_actor } xfmc20_context_")
                .append(suffix(scene.sceneId())).append("_trigger = yes }\n");
        }
        for (String role : new String[]{"aid", "restructure"}) guards.append("var:xfmc20_").append(role).append(" = { xfmc20_empty_primary_trigger = yes }\n");
        guards.append("""
            var:xfmc20_child = { xfmc20_account_trigger = yes var:xfm_holder = { is_ai = yes is_adult = no } }
            var:xfmc20_estate = { xfmc20_account_trigger = yes OR = { var:xfm_inheritance_state = 1 var:xfm_inheritance_state = 2 } }
            var:xfmc20_asset = { xfmc20_account_trigger = yes OR = { var:xfm_free_cents > 0 var:xfm_reserved_cents > 0 var:xfm_holdings_count > 0 var:xfm_open_orders_count > 0 var:xfm_open_positions_count > 0 } }
            }
            xfmc20_execute_trigger = {
             xfmc20_owner_trigger = yes has_variable = xfmc20_seeded NOT = { has_variable = xfmc20_dispatch_attempted }
             has_variable = xfmc20_seed_day
             trigger_if = { limit = { has_variable = xfmc20_seeded has_variable = xfmc20_seed_day exists = global_var:xfm_exchange }
              var:xfmc20_seed_day = global_var:xfm_exchange.var:xfm_day xfmc20_controls_ready_trigger = yes
             }
            }
            xfmc20_retry_trigger = {
             xfmc20_owner_trigger = yes has_variable = xfmc20_dispatch_attempted NOT = { has_variable = xfmc20_retry_attempted }
             has_variable = xfmc20_seed_day
             trigger_if = { limit = { has_variable = xfmc20_dispatch_attempted has_variable = xfmc20_seed_day exists = global_var:xfm_exchange }
              var:xfmc20_seed_day = global_var:xfm_exchange.var:xfm_day
             }
            }
            """);
        // A trigger cannot save scope. Context checks are performed in the binding effect below.
        String guardText = guards.toString().replace("var:xfm_holder = { save_temporary_scope_as = xfm_crisis_actor } xfmc20_context_", "xfmc20_bound_context_");
        StringBuilder contextChecks = new StringBuilder();
        for (var scene : request.scenes()) {
            String role = key(scene.sceneId()), suffix = suffix(scene.sceneId());
            guardText = guardText.replace("xfmc20_bound_context_" + suffix + "_trigger = yes", "var:xfmc20_context_" + suffix + " = 1");
            contextChecks.append("if = { limit = { exists = var:xfmc20_").append(role).append(" } var:xfmc20_").append(role)
                .append(" = { var:xfm_holder = { save_scope_as = xfm_crisis_actor } if = { limit = { xfmc20_context_").append(suffix)
                .append("_trigger = yes } set_variable = { name = xfmc20_context_").append(suffix).append(" value = 1 } } } }\n");
        }
        String bindingText = binding.toString().replace(" }\n if = { limit = { xfmc20_bound_trigger = yes }", " }\n" + contextChecks + " if = { limit = { xfmc20_bound_trigger = yes }");
        int bindStart=bindingText.indexOf(" every_in_global_list = {");
        int bindEnd=bindingText.indexOf(" if = { limit = { xfmc20_bound_trigger = yes }");
        if(bindStart<0 || bindEnd<bindStart) throw new IllegalStateException("closed binder boundary");
        bindingText="xfmc20_bind_accounts_effect = {\n"+bindingText.substring(bindStart,bindEnd)+"}\n"
                +bindingText.substring(0,bindStart)+" xfmc20_bind_accounts_effect = yes\n"+bindingText.substring(bindEnd);
        text.put("common/scripted_triggers/xfmc20_guards.txt", guardText);
        text.put("common/scripted_effects/xfmc20_setup.txt", bindingText);
        text.put("common/scripted_effects/xfmc20_seed.txt", """
            xfmc20_seed_role_effect = {
             clear_saved_scope = xfmc20_new_source clear_saved_scope = xfm_debt_receipt
             global_var:xfm_exchange.story_owner = { create_story = { type = xfmd_claim_source save_scope_as = xfmc20_new_source } }
             if = { limit = { exists = scope:xfmc20_new_source }
              set_variable = { name = xfmc20_$ROLE$_source value = scope:xfmc20_new_source }
              scope:xfmc20_new_source = {
               set_variable = { name = xfmc20_controlled_input value = 1 }
               set_variable = { name = xfm_request_debtor value = root.var:xfmc20_$ROLE$ }
               set_variable = { name = xfm_request_creditor value = root.var:xfmc20_$CREDITOR$ }
               set_variable = { name = xfm_request_cents value = 1000000 }
               set_variable = { name = xfm_request_day value = xfmc20_source_day_value }
               set_variable = { name = xfm_request_kind value = 1 }
               set_variable = { name = xfm_request_fund_eligible value = 0 }
               xfm_debt_cover_shortfall_effect = yes
              }
              if = { limit = { exists = scope:xfm_debt_receipt scope:xfmc20_new_source = { var:xfm_result = 1 } }
               set_variable = { name = xfmc20_$ROLE$_claim value = scope:xfm_debt_receipt }
               scope:xfm_debt_receipt = { set_variable = { name = xfm_overdue_days value = 30 } }
               var:xfmc20_$ROLE$ = {
                set_variable = { name = xfm_max_overdue_days value = 30 }
                var:xfm_holder = { if = { limit = { is_ai = yes is_adult = yes } add_stress = 400 } }
                xfm_crisis_begin_effect = yes
                # Synthetic maturity only; real aid/extension relief is never removed.
                set_variable = { name = xfm_crisis_started_day value = xfm_crisis_mature_day_value }
                set_variable = { name = xfm_crisis_reviews value = 2 }
                set_variable = { name = xfm_next_crisis_review value = global_var:xfm_exchange.var:xfm_day }
                change_variable = { name = xfm_next_crisis_review add = 7 }
               }
              }
              else = { set_variable = { name = xfmc20_setup_failed value = 1 } }
             }
             else = { set_variable = { name = xfmc20_setup_failed value = 1 } }
             clear_saved_scope = xfmc20_new_source clear_saved_scope = xfm_debt_receipt
            }
            """);
        StringBuilder dispatch = new StringBuilder("xfmc20_execute_effect = { if = { limit = { xfmc20_execute_trigger = yes }\nset_variable = { name = xfmc20_dispatch_attempted value = 1 }\n");
        for (var scene : request.scenes()) dispatch.append("var:xfmc20_").append(key(scene.sceneId())).append(" = { xfmc20_attempt_").append(suffix(scene.sceneId())).append("_effect = yes }\n");
        for (String role : new String[]{"player","child","estate","asset","aid","restructure"}) dispatch.append("var:xfmc20_").append(role).append(" = { xfmc20_negative_effect = yes }\n");
        dispatch.append("debug_log = \"XFMAT: TEST PASS controlled_crisis20_dispatch_recorded\"\n } }\nxfmc20_retry_effect = { if = { limit = { xfmc20_retry_trigger = yes }\nset_variable = { name = xfmc20_retry_attempted value = 1 }\n");
        for (var scene : request.scenes()) dispatch.append("var:xfmc20_").append(key(scene.sceneId())).append(" = { xfmc20_negative_effect = yes }\n");
        dispatch.append("debug_log = \"XFMAT: TEST PASS controlled_crisis20_reentry_recorded\"\n } }\n");
        dispatch.append("""
            xfmc20_negative_effect = {
             # Do not kill a protected control even if a regression makes its guard unexpectedly true.
             if = { limit = { NOT = { xfm_crisis_terminal_review_trigger = yes } }
              xfm_crisis_terminal_effect = yes
              set_variable = { name = xfmc20_rejected_call_recorded value = 1 }
             }
             else = { set_variable = { name = xfmc20_negative_failed value = 1 } }
            }
            """);
        text.put("common/scripted_effects/xfmc20_dispatch.txt", dispatch.toString());
        StringBuilder gui = new StringBuilder(), widget = new StringBuilder("widget = { name = xfmc20_widget parentanchor = bottom|right position = { -310 100 } size = { 300 210 } layer = middle\n");
        String[][] buttons = {{"setup","xfmc20_start_trigger","xfmc20_setup_effect"},{"execute","xfmc20_execute_trigger","xfmc20_execute_effect"},{"retry","xfmc20_retry_trigger","xfmc20_retry_effect"}};
        int y=0;
        for (String[] button : buttons) { gui.append("xfmc20_").append(button[0]).append("_gui = { scope = character is_valid = { ").append(button[1]).append(" = yes } effect = { ").append(button[2]).append(" = yes } }\n"); widget(widget,button[0],y); y+=40; }
        for (String role : new String[]{"aid","restructure"}) {
            gui.append("xfmc20_select_").append(role).append("_gui = { scope = character is_valid = { xfmc20_owner_trigger = yes exists = var:xfmc20_").append(role).append("_claim NOT = { has_variable = xfmc20_dispatch_attempted } } effect = { set_variable = { name = xfm_selected_debt value = var:xfmc20_").append(role).append("_claim } set_variable = { name = xfm_ui_debt_pay_cents value = 1000 } } }\n");
            widget(widget,"select_"+role,y); y+=40;
        }
        widget.append("}\n"); text.put("common/scripted_guis/xfmc20_gui.txt",gui.toString());
        text.put("gui/scripted_widgets/xfmc20_widget.txt","gui/xfmc20_widget.gui = xfmc20_widget\n"); text.put("gui/xfmc20_widget.gui",widget.toString());
        for (String language : new String[]{"english","simp_chinese"}) {
            StringBuilder loc=new StringBuilder("l_"+language+":\n");
            for (String name : new String[]{"setup","execute","retry","select_aid","select_restructure"}) loc.append(" xfmc20_").append(name).append("_label:0 \"Controlled crisis20: ").append(name).append("\"\n");
            text.put("localization/"+language+"/xfmc20_l_"+language+".yml",loc.toString());
        }
        text.forEach((name,value)->result.put(name,("\ufeff"+value.replace("${PLAYER}",request.playerAccountId())).getBytes(StandardCharsets.UTF_8)));
        return Map.copyOf(result);
    }
    private static void bind(StringBuilder out,String role,String id) {
        out.append("if = { limit = { var:xfm_account_id = ").append(id).append(" } root = { set_variable = { name = xfmc20_").append(role)
            .append(" value = prev } change_variable = { name = xfmc20_bound_count add = 1 } } }\n");
    }
    private static void seed(StringBuilder out,String role,String creditor) { out.append("xfmc20_seed_role_effect = { ROLE = ").append(role).append(" CREDITOR = ").append(creditor).append(" }\n"); }
    private static String suffix(int id) { return String.format(java.util.Locale.ROOT,"%02d",id); }
    private static String key(int id) { return "s"+suffix(id); }
    private static void widget(StringBuilder out,String name,int y) {
        out.append("button_standard = { name = \"xfmc20_").append(name).append("\" position = { 0 ").append(y)
            .append(" } size = { 300 38 } text = \"xfmc20_").append(name).append("_label\" enabled = \"[GetScriptedGui( 'xfmc20_").append(name)
            .append("_gui' ).IsValid( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]\" onclick = \"[GetScriptedGui( 'xfmc20_").append(name)
            .append("_gui' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]\" }\n");
    }
}
