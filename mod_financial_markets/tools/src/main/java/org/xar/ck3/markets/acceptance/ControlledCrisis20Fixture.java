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
    /** Explicit readonly diagnostic rendering. Default render above is unchanged. */
    public static Map<String,byte[]> renderDiscovery(ControlledCrisis20Request request, String selectorSource, String guardSource) {
        return renderDiscoveryVersion(request,selectorSource,guardSource,false);
    }
    /** Explicit successor diagnostic; never resets or consumes the retained xfmc20d_ attempt. */
    public static Map<String,byte[]> renderDiscoveryV2(ControlledCrisis20Request request, String selectorSource, String guardSource) {
        return renderDiscoveryVersion(request,selectorSource,guardSource,true);
    }
    private static Map<String,byte[]> renderDiscoveryVersion(ControlledCrisis20Request request, String selectorSource, String guardSource, boolean successor) {
        java.util.Objects.requireNonNull(request);
        var original=org.xar.ck3.save.Clausewitz.parse(guardSource).block("xfm_crisis_terminal_review_trigger");
        var wallets=original.named("var:xfm_holder").stream()
            .filter(e->e.value() instanceof org.xar.ck3.save.Clausewitz.Block b && !b.named("any_in_list").isEmpty()).toList();
        if(wallets.size()!=1 || !(wallets.getFirst().value() instanceof org.xar.ck3.save.Clausewitz.Block wallet)
                || wallet.entries().size()!=2 || !wallet.entries().getFirst().key().equals("any_in_list")
                || !wallet.entries().getLast().key().equals("NOT"))throw new IllegalArgumentException("original complete holder-wallet guard required");
        Map<String,byte[]> result=new LinkedHashMap<>();
        var contexts=CrisisSceneBranchFixture.render(selectorSource);
        result.put("common/scripted_triggers/xfmc20_contexts.txt",successor
                ? guardedDiscoveryContexts(contexts.get("common/scripted_triggers/xfmc20_contexts.txt"))
                : contexts.get("common/scripted_triggers/xfmc20_contexts.txt"));
        String[] roles=new String[26];
        for(int i=0;i<20;i++)roles[i]="s"+suffix(i+1);
        System.arraycopy(new String[]{"child","estate","asset","aid","restructure","creditor"},0,roles,20,6);
        StringBuilder guards=new StringBuilder("""
            xfmc20d_start_trigger = {
             is_alive = yes is_adult = yes is_ai = no
             NOT = { has_variable = xfmc20d_attempted }
             NOT = { has_variable = xfmc20_setup_attempted }
             NOT = { exists = global_var:xfmc20_owner }
             exists = global_var:xfm_exchange exists = var:xfm_account
             trigger_if = { limit = { exists = global_var:xfm_exchange }
              global_var:xfm_exchange = { has_variable = xfm_day has_variable = xfm_next_account_id var:xfm_next_account_id >= 0 var:xfm_next_account_id <= 65536 }
             }
             trigger_if = { limit = { exists = var:xfm_account }
              var:xfm_account = { story_type = xfm_finance_account var:xfm_holder = root var:xfm_account_id = ${PLAYER} var:xfm_system_account = 0 }
             }
            }
            xfmc20d_account_trigger = {
             story_type = xfm_finance_account has_variable = xfm_account_id
             var:xfm_account_id > 0 var:xfm_account_id <= 1000000000
             var:xfm_system_account = 0 exists = var:xfm_holder
             var:xfm_holder = { is_alive = yes }
            }
            xfmc20d_primary_trigger = {
             var:xfm_holder = { var:xfm_account = prev }
            }
            xfmc20d_all_wallets_empty_trigger = {
             xfm_crisis_account_known_empty_trigger = yes
            """);
        // Exact source-derived holder/any_in_list/NOT block retains both prev levels.
        guards.append(wallets.getFirst().key()).append(" = ").append(wallet.render()).append("\n}\n");
        guards.append("""
            xfmc20d_positive_trigger = {
             xfmc20d_primary_trigger = yes var:xfm_inheritance_state = 0 var:xfm_account_frozen = 0
             var:xfm_holder = { is_ai = yes is_adult = yes gold <= 0 }
             NOT = { has_variable = xfm_crisis_terminal }
             trigger_if = { limit = { has_variable = xfm_total_debt_cents } var:xfm_total_debt_cents = 0 }
             xfm_debt_income_threshold_value < 1000000
             root.var:xfmc20d_current_wallets_empty = 1
            }
            xfmc20d_direct_asset_trigger = { OR = {
            """);
        for(String field:new String[]{"xfm_free_cents","xfm_reserved_cents","xfm_holdings_count","xfm_open_orders_count","xfm_open_positions_count"})
            guards.append("AND = { has_variable = ").append(field).append(" trigger_if = { limit = { has_variable = ")
                .append(field).append(" } var:").append(field).append(" > 0 } }\n");
        guards.append("} }\n");
        StringBuilder effect=new StringBuilder("""
            xfmc20d_discover_effect = {
             if = { limit = { xfmc20d_start_trigger = yes }
              set_variable = { name = xfmc20d_attempted value = 1 }
              set_variable = { name = xfmc20d_source_financial_day value = global_var:xfm_exchange.var:xfm_day }
              set_variable = { name = xfmc20d_source_script_date value = current_date }
              set_variable = { name = xfmc20d_source_account_counter value = global_var:xfm_exchange.var:xfm_next_account_id }
              set_variable = { name = xfmc20d_visited value = 0 }
              set_variable = { name = xfmc20d_candidate_count value = 0 }
              set_variable = { name = xfmc20d_primary_count value = 0 }
              set_variable = { name = xfmc20d_spare_count value = 0 }
            """);
        for(String role:roles)effect.append("set_variable = { name = xfmc20d_").append(role).append("_count value = 0 }\nset_variable = { name = xfmc20d_").append(role)
            .append("_index_1 value = 0 }\nset_variable = { name = xfmc20d_").append(role).append("_index_2 value = 0 }\n");
        effect.append("""
              every_in_global_list = { variable = xfm_account_registry
               root = { change_variable = { name = xfmc20d_visited add = 1 } }
               if = { limit = { root.var:xfmc20d_visited <= 65536 xfmc20d_account_trigger = yes }
                save_scope_as = xfmc20d_account
                var:xfm_holder = { save_scope_as = xfm_crisis_actor }
                root = {
                 set_variable = { name = xfmc20d_current_slot value = 0 }
                 set_variable = { name = xfmc20d_current_predicates value = 0 }
                 set_variable = { name = xfmc20d_current_contexts value = 0 }
                 set_variable = { name = xfmc20d_current_positive value = 0 }
                 set_variable = { name = xfmc20d_current_wallets_empty value = 0 }
                 set_variable = { name = xfmc20d_current_checked value = 447 }
                 set_variable = { name = xfmc20d_current_pick_role value = 0 }
                 set_variable = { name = xfmc20d_current_pick_kind value = 0 }
                 set_variable = { name = xfmc20d_current_duplicate_actor value = 0 }
                }
            """);
        // Predicate bitmap is only the exact true/false return of these engine
        // checks. A false all-wallet trigger does not establish nonzero wealth.
        String[] predicates={"xfmc20d_primary_trigger = yes","var:xfm_holder = { is_ai = yes }",
            "var:xfm_holder = { is_adult = yes }","var:xfm_holder = { gold <= 0 }",
            "NOT = { has_variable = xfm_crisis_terminal }",
            "trigger_if = { limit = { has_variable = xfm_total_debt_cents } var:xfm_total_debt_cents = 0 }",
            "xfmc20d_primary_trigger = yes xfmc20d_all_wallets_empty_trigger = yes","xfmc20d_direct_asset_trigger = yes",
            "OR = { var:xfm_inheritance_state = 1 var:xfm_inheritance_state = 2 }"};
        effect.append("if = { limit = { xfmc20d_primary_trigger = yes } root = { change_variable = { name = xfmc20d_current_checked add = 64 } } if = { limit = { xfmc20d_all_wallets_empty_trigger = yes } root = { set_variable = { name = xfmc20d_current_wallets_empty value = 1 } change_variable = { name = xfmc20d_current_predicates add = 64 } } } }\n");
        for(int i=0;i<predicates.length;i++)if(i!=6)effect.append("if = { limit = { ").append(predicates[i])
            .append(" } root = { change_variable = { name = xfmc20d_current_predicates add = ").append(1<<i).append(" } } }\n");
        effect.append("if = { limit = { xfmc20d_positive_trigger = yes } root = { set_variable = { name = xfmc20d_current_positive value = 1 } } }\n");
        for(int i=1;i<=20;i++) {
            String role="s"+suffix(i);
            effect.append("root = { set_variable = { name = xfmc20d_match_").append(role).append(" value = 0 } }\n")
                .append("if = { limit = { xfmc20_context_").append(suffix(i)).append("_trigger = yes } root = { change_variable = { name = xfmc20d_current_contexts add = ")
                .append(1<<(i-1)).append(" } if = { limit = { var:xfmc20d_current_positive = 1 } set_variable = { name = xfmc20d_match_")
                .append(role).append(" value = 1 } } } }\n");
        }
        String aiPrimary="xfmc20d_primary_trigger = yes var:xfm_holder = { is_ai = yes is_adult = yes }";
        String[] controlPredicates={successor ? "var:xfm_holder = { is_ai = yes is_adult = no }"
                : "xfmc20d_primary_trigger = yes var:xfm_holder = { is_ai = yes is_adult = no }",
            "OR = { var:xfm_inheritance_state = 1 var:xfm_inheritance_state = 2 }",
            aiPrimary+" xfmc20d_direct_asset_trigger = yes",
            "root.var:xfmc20d_current_positive = 1","root.var:xfmc20d_current_positive = 1",aiPrimary};
        for(int i=0;i<6;i++)effect.append("root = { set_variable = { name = xfmc20d_match_").append(roles[i+20]).append(" value = 0 } }\nif = { limit = { ")
            .append(controlPredicates[i]).append(" } root = { set_variable = { name = xfmc20d_match_").append(roles[i+20]).append(" value = 1 } } }\n");
        if(successor) {
            effect.append("root = { set_variable = { name = xfmc20d_current_role_mask value = 0 }\n");
            for(int i=0;i<roles.length;i++)effect.append("if = { limit = { var:xfmc20d_match_").append(roles[i])
                .append(" = 1 } change_variable = { name = xfmc20d_current_role_mask add = ").append(1L<<i).append(" } }\n");
            effect.append("}\n");
        }
        effect.append("root = {\n");
        // One reserved primary and one spare per role. Common early candidates
        // cannot consume any rare role's reserved primary or spare slot.
        for(int i=0;i<roles.length;i++)effect.append("if = { limit = { var:xfmc20d_current_pick_role = 0 var:xfmc20d_match_").append(roles[i])
            .append(" = 1 var:xfmc20d_").append(roles[i]).append("_index_1 = 0 } set_variable = { name = xfmc20d_current_pick_role value = ")
            .append(i+1).append(" } set_variable = { name = xfmc20d_current_pick_kind value = 1 } }\n");
        for(int i=0;i<roles.length;i++)effect.append("if = { limit = { var:xfmc20d_current_pick_role = 0 var:xfmc20d_match_").append(roles[i])
            .append(" = 1 var:xfmc20d_").append(roles[i]).append("_index_2 = 0 } set_variable = { name = xfmc20d_current_pick_role value = ")
            .append(i+1).append(" } set_variable = { name = xfmc20d_current_pick_kind value = 2 } }\n");
        effect.append("if = { limit = { var:xfmc20d_current_pick_role > 0 } xfmc20d_capture_candidate_effect = yes }\n");
        for(int i=0;i<roles.length;i++)effect.append("if = { limit = { var:xfmc20d_current_slot > 0 var:xfmc20d_current_pick_role = ")
            .append(i+1).append(" } xfmc20d_add_role_effect = { ROLE = ").append(roles[i]).append(" } }\n");
        effect.append("""
                }
               }
              }
              if = { limit = {
               var:xfmc20d_visited <= 65536
               var:xfmc20d_source_financial_day = global_var:xfm_exchange.var:xfm_day
               var:xfmc20d_source_script_date = current_date
               var:xfmc20d_source_account_counter = global_var:xfm_exchange.var:xfm_next_account_id
              } set_variable = { name = xfmc20d_scan_completed value = 1 } }
              clear_saved_scope = xfmc20d_account clear_saved_scope = xfm_crisis_actor
              debug_log = "XFMAT: OBSERVE controlled_crisis20_discovery_recorded"
             }
            }
            xfmc20d_record_entry_effect = {
             set_variable = { name = xfmc20d_entry_$ENTRY$_account value = scope:xfmc20d_account }
             set_variable = { name = xfmc20d_entry_$ENTRY$_actor value = scope:xfm_crisis_actor }
             set_variable = { name = xfmc20d_entry_$ENTRY$_account_id value = scope:xfmc20d_account.var:xfm_account_id }
             set_variable = { name = xfmc20d_entry_$ENTRY$_predicates value = var:xfmc20d_current_predicates }
             set_variable = { name = xfmc20d_entry_$ENTRY$_contexts value = var:xfmc20d_current_contexts }
             set_variable = { name = xfmc20d_entry_$ENTRY$_checked value = var:xfmc20d_current_checked }
            """);
        if(successor)effect.append("set_variable = { name = xfmc20d_entry_$ENTRY$_role_mask value = var:xfmc20d_current_role_mask }\nset_variable = { name = xfmc20d_entry_$ENTRY$_positive value = var:xfmc20d_current_positive }\n");
        effect.append("""
             set_variable = { name = xfmc20d_current_slot value = $ENTRY$ }
             set_variable = { name = xfmc20d_candidate_count value = $ENTRY$ }
            }
            xfmc20d_capture_candidate_effect = {
            """);
        for(int i=1;i<=52;i++)effect.append("if = { limit = { has_variable = xfmc20d_entry_").append(i).append("_actor trigger_if = { limit = { has_variable = xfmc20d_entry_")
            .append(i).append("_actor } var:xfmc20d_entry_").append(i).append("_actor = scope:xfm_crisis_actor } } set_variable = { name = xfmc20d_current_duplicate_actor value = 1 } }\n");
        for(int i=1;i<=52;i++)effect.append("if = { limit = { var:xfmc20d_current_duplicate_actor = 0 var:xfmc20d_current_slot = 0 var:xfmc20d_candidate_count = ").append(i-1)
            .append(" } xfmc20d_record_entry_effect = { ENTRY = ").append(i).append(" } }\n");
        effect.append("if = { limit = { var:xfmc20d_current_duplicate_actor = 0 var:xfmc20d_current_slot = 0 } set_variable = { name = xfmc20d_capacity_reached value = 1 } }\n}\nxfmc20d_add_role_effect = {\n");
        for(int i=1;i<=2;i++)effect.append(i==1?"if":"else_if").append(" = { limit = { var:xfmc20d_current_pick_kind = ").append(i)
            .append(" } set_variable = { name = xfmc20d_$ROLE$_index_").append(i).append(" value = var:xfmc20d_current_slot } change_variable = { name = xfmc20d_$ROLE$_count add = 1 } change_variable = { name = xfmc20d_")
            .append(i==1?"primary":"spare").append("_count add = 1 } }\n");
        effect.append("}\n");
        discoveryPut(result,"descriptor.mod","name=\"Crisis20 readonly discovery only\"\nversion=\"1\"\nsupported_version=\"1.21.*\"\n");
        discoveryPut(result,"common/scripted_triggers/xfmc20d_guards.txt",guards.toString().replace("${PLAYER}",request.playerAccountId()));
        discoveryPut(result,"common/scripted_effects/xfmc20d_discover.txt",effect.toString());
        discoveryPut(result,"common/scripted_guis/xfmc20d_gui.txt","xfmc20d_discover_gui = { scope = character is_valid = { xfmc20d_start_trigger = yes } effect = { xfmc20d_discover_effect = yes } }\n");
        discoveryPut(result,"gui/scripted_widgets/xfmc20d_widget.txt","gui/xfmc20d_widget.gui = xfmc20d_widget\n");
        discoveryPut(result,"gui/xfmc20d_widget.gui","widget = { name = xfmc20d_widget parentanchor = bottom|right position = { -310 100 } size = { 300 50 } layer = middle\n button_standard = { name = \"xfmc20d_discover\" size = { 300 38 } text = \"xfmc20d_discover_label\" enabled = \"[GetScriptedGui( 'xfmc20d_discover_gui' ).IsValid( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]\" onclick = \"[GetScriptedGui( 'xfmc20d_discover_gui' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]\" } }\n");
        for(String language:new String[]{"english","simp_chinese"})discoveryPut(result,"localization/"+language+"/xfmc20d_l_"+language+".yml","l_"+language+":\n xfmc20d_discover_label:0 \"Crisis20: readonly discovery\"\n");
        if(successor) {
            String guardPath="common/scripted_triggers/xfmc20d_guards.txt";
            String guarded=new String(result.get(guardPath),StandardCharsets.UTF_8);
            String unsafe="var:xfm_holder = { var:xfm_account = prev }";
            if(guarded.indexOf(unsafe)<0 || guarded.indexOf(unsafe)!=guarded.lastIndexOf(unsafe))throw new IllegalStateException("one original PRIMARY comparison required");
            guarded=guarded.replace(unsafe,"trigger_if = { limit = { exists = var:xfm_holder } var:xfm_holder = { trigger_if = { limit = { exists = var:xfm_account } var:xfm_account = prev } trigger_else = { always = no } } } trigger_else = { always = no }");
            result.put(guardPath,guarded.getBytes(StandardCharsets.UTF_8));
            Map<String,byte[]> successorFiles=new LinkedHashMap<>();
            result.forEach((path,bytes)->successorFiles.put(path.replace("xfmc20d_","xfmc20e_"),
                    new String(bytes,StandardCharsets.UTF_8).replace("xfmc20d_","xfmc20e_").getBytes(StandardCharsets.UTF_8)));
            return Map.copyOf(successorFiles);
        }
        return Map.copyOf(result);
    }
    /** Source-derived contexts behind conditional existence gates; no eager sibling AND guard. */
    private static byte[] guardedDiscoveryContexts(byte[] source) {
        var parsed=org.xar.ck3.save.Clausewitz.parse(new String(source,StandardCharsets.UTF_8));
        StringBuilder output=new StringBuilder("\ufeff");
        for(var entry:parsed.entries()) {
            if(!(entry.value() instanceof org.xar.ck3.save.Clausewitz.Block block))throw new IllegalArgumentException("context block");
            boolean location=block.entries().stream().anyMatch(e->e.key().equals("scope:xfm_crisis_actor.location"));
            String body=block.render();body=body.substring(1,body.length()-1);
            output.append(entry.key()).append(" = { trigger_if = { limit = { exists = scope:xfm_crisis_actor }\n");
            if(location)output.append("trigger_if = { limit = { scope:xfm_crisis_actor = { exists = location } }\n");
            output.append(body).append('\n');
            if(location)output.append("} trigger_else = { always = no }\n");
            output.append("} trigger_else = { always = no } }\n");
        }
        return output.toString().getBytes(StandardCharsets.UTF_8);
    }
    private static void discoveryPut(Map<String,byte[]> files,String name,String value) {
        files.put(name,("\ufeff"+value).getBytes(StandardCharsets.UTF_8));
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
