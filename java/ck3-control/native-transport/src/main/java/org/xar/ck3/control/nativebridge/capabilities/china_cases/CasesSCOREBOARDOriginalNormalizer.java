package org.xar.ck3.control.nativebridge.capabilities.china_cases;
import java.util.*;
import static org.xar.ck3.control.nativebridge.capabilities.china_cases.CasesNormalizerValues.*;
/** Pure Java port of zhongguo_scoreboard_state_contract.py; original SHA-256 afe199408d36dfc28980e3588e1832aa27715a3a90572ae7200bbbd6a935d9bd. No Python runtime. */
final class CasesSCOREBOARDOriginalNormalizer {
    private CasesSCOREBOARDOriginalNormalizer() {}
    private static final Map<String,V> GLOBALS=globals();
    private static Map<String,V> globals(){
        E e=new E(Map.of(),CasesSCOREBOARDOriginalNormalizer::dispatch);
        e.put("ZHONGGUO_SCOREBOARD_STATE_KIND_V1",s("zhongguo.scoreboard.named-state-acl"));
        e.put("ZHONGGUO_SCOREBOARD_STATE_V1_GAME_VERSION",s("1.19.0.6"));
        e.put("ZHONGGUO_SCOREBOARD_STATE_V1_EXECUTABLE_SHA256",s("2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"));
        e.put("ZHONGGUO_SCOREBOARD_STATE_V1_BACKEND_ID",s("ck3-1.19.0.6-native-zhongguo-scoreboard-state-v1"));
        e.put("ZHONGGUO_SCOREBOARD_STATE_V1_CONSUMER_ID",s("xar-autoplayer-zhongguo-scoreboard-state-v1"));
        e.put("ZHONGGUO_SCOREBOARD_STATE_V1_ALLOWLIST_ID",s("zg361-scoreboard-fixed-widget-acl-v1"));
        e.put("_POINTER_RE",regex(text(s("0x[0-9A-F]+\\Z"))));
        e.put("_FINGERPRINT_RE",regex(text(s("[0-9A-F]{64}\\Z"))));
        e.put("_PROVIDER_SESSION_RE",regex(text(s("[0-9A-F]{32}\\Z"))));
        e.put("_WIDGET_IDENTITIES",seq(true,p(seq(true,p(s("zg361_open_scoreboard")),p(s("zg361_scoreboard_toggle")))),p(seq(true,p(s("zg361_scoreboard_window")),p(s("zg361_scoreboard_window")))),p(seq(true,p(s("zg361_scoreboard_modal")),p(s("zg361_scoreboard_modal")))),p(seq(true,p(s("zg361_scoreboard_panel")),p(s("zg361_scoreboard_panel")))),p(seq(true,p(s("zg361_scoreboard_entry_managed")),p(s("zg361_scoreboard_entry_managed")))),p(seq(true,p(s("zg361_scoreboard_entry_received")),p(s("zg361_scoreboard_entry_received")))),p(seq(true,p(s("zg361_scoreboard_entry_system")),p(s("zg361_scoreboard_entry_system")))),p(seq(true,p(s("zg361_scoreboard_tab_managed")),p(s("zg361_scoreboard_tab_managed")))),p(seq(true,p(s("zg361_scoreboard_tab_received")),p(s("zg361_scoreboard_tab_received")))),p(seq(true,p(s("zg361_scoreboard_tab_system")),p(s("zg361_scoreboard_tab_system")))),p(seq(true,p(s("zg361_scoreboard_page_managed")),p(s("zg361_scoreboard_page_managed")))),p(seq(true,p(s("zg361_scoreboard_page_received")),p(s("zg361_scoreboard_page_received")))),p(seq(true,p(s("zg361_scoreboard_page_system")),p(s("zg361_scoreboard_page_system")))),p(seq(true,p(s("zg361_scoreboard_modal_backdrop_close")),p(s("zg361_scoreboard_modal_backdrop_close")))),p(seq(true,p(s("zg361_scoreboard_header_close")),p(s("zg361_scoreboard_header_close"))))));
        e.put("_TYPED_KEYS",set(p(s("status")),p(s("value")),p(s("unavailable_reason"))));
        e.put("_TYPED_REASONS",set(p(s("snapshot_unavailable")),p(s("widget_not_instantiated")),p(s("named_clickable_child_not_stable")),p(s("enabled_state_abi_not_frozen")),p(s("focus_owner_abi_not_frozen")),p(s("modal_blocking_abi_not_frozen")),p(s("screen_rect_abi_not_frozen")),p(s("scroll_area_extent_abi_not_frozen")),p(s("surface_not_available")),p(s("variable_absent")),p(s("value_type_mismatch")),p(s("value_out_of_range")),p(s("read_only_provider_action_not_exposed")),p(s("state_projection_unavailable"))));
        e.put("_TOP_REASONS",set(p(s("unsupported_build")),p(s("requires_application_main")),p(s("requires_paused")),p(s("map_not_ready")),p(s("gui_root_unavailable")),p(s("state_projection_unavailable")),p(s("widget_state_unavailable")),p(s("widget_not_instantiated")),p(s("acl_inconsistent")),p(s("state_changed")),p(s("provider_revision_unavailable")),p(s("internal_error"))));
        e.put("_WIDGET_KEYS",set(p(s("stable_identity")),p(s("runtime_name")),p(s("instance_pointer")),p(s("vtable_pointer")),p(s("exists")),p(s("local_visible")),p(s("effective_visible")),p(s("enabled")),p(s("focused")),p(s("modal_blocking")),p(s("screen_x")),p(s("screen_y")),p(s("screen_width")),p(s("screen_height")),p(s("scroll_min")),p(s("scroll_max")),p(s("scroll_value"))));
        e.put("_MANAGED_KEYS",set(p(s("surface_available")),p(s("current_player_can_assess_others")),p(s("owner_character_id")),p(s("first_subject_character_id"))));
        e.put("_RECEIVED_KEYS",set(p(s("surface_available")),p(s("current_player_is_subject")),p(s("first_row_character_id")),p(s("owner_character_id")),p(s("subject_character_id")),p(s("cycle_serial")),p(s("result_case_serial")),p(s("b1_case_serial")),p(s("disclosure_acl_mode")),p(s("disclosure_policy_available")),p(s("disclosure_policy_id")),p(s("disclosure_self_mode")),p(s("disclosure_team_mode")),p(s("disclosure_evaluator_identity_mode")),p(s("disclosure_blackbox_risk"))));
        e.put("_READINESS_KEYS",set(p(s("player_binding_ready")),p(s("gui_root_ready")),p(s("entry_window_state_ready")),p(s("acl_ready")),p(s("same_frame_ready")),p(s("state_acl_query_ready")),p(s("full_widget_gate_ready")),p(s("production_live_ready"))));
        e.put("_PROVENANCE_VALUES",dict(new Item(s("game_version"),e.get("ZHONGGUO_SCOREBOARD_STATE_V1_GAME_VERSION")),new Item(s("executable_sha256"),e.get("ZHONGGUO_SCOREBOARD_STATE_V1_EXECUTABLE_SHA256")),new Item(s("backend_id"),e.get("ZHONGGUO_SCOREBOARD_STATE_V1_BACKEND_ID")),new Item(s("consumer_id"),e.get("ZHONGGUO_SCOREBOARD_STATE_V1_CONSUMER_ID")),new Item(s("allowlist_id"),e.get("ZHONGGUO_SCOREBOARD_STATE_V1_ALLOWLIST_ID")),new Item(s("gui_global_slot_rva"),s("0x576CC68")),new Item(s("find_top_level_widget_rva"),s("0x36D0B20")),new Item(s("widget_hidden_flags_offset"),s("0xD0")),new Item(s("widget_local_hidden_mask"),s("0x10")),new Item(s("widget_effective_hidden_mask"),s("0x08")),new Item(s("widget_local_disabled_mask"),s("0x04")),new Item(s("widget_effective_disabled_mask"),s("0x02")),new Item(s("widget_parent_offset"),s("0xE8")),new Item(s("widget_children_offset"),s("0xF0")),new Item(s("widget_name_offset"),s("0x1B8")),new Item(s("modal_receivers_offset"),s("0x290")),new Item(s("modal_receiver_count_offset"),s("0x29C")),new Item(s("tree_fingerprint_domain"),s("XAR/ZG361/SCOREBOARD/TREE/V1\u0000")),new Item(s("semantic_fingerprint_domain"),s("XAR/ZG361/SCOREBOARD/SEMANTIC/V1\u0000")),new Item(s("state_digest_domain"),s("XAR/ZG361/SCOREBOARD/STATE/V1\u0000")),new Item(s("query_scope"),s("fixed_scoreboard_instances_and_player_frozen_acl")),new Item(s("contract_stage"),s("static_provider_observed_revision_live_unverified"))));
        e.put("_FRAME_KEYS",set(p(s("schema_version")),p(s("status")),p(s("case_kind")),p(s("request_nonce")),p(s("snapshot_revision")),p(s("date_raw")),p(s("paused")),p(s("player_character_id")),p(s("tree_fingerprint_v1")),p(s("semantic_fingerprint_v1")),p(s("provider_session_id")),p(s("observation_sequence")),p(s("observed_state_revision")),p(s("widgets")),p(s("acl")),p(s("actions")),p(s("readiness")),p(s("unavailable_reason")),p(s("provenance"))));
        return Map.copyOf(e.locals);
    }
    static V run(Args args){return dispatch("normalize_native_zhongguo_scoreboard_state_v1",args);}
    private static V dispatch(String name,Args args){
        return switch(name){
            case "_exact" -> f_exact(bind(GLOBALS,CasesSCOREBOARDOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("keys",REQUIRED),new Param("label",REQUIRED)),List.of(),null),args));
            case "_integer" -> f_integer(bind(GLOBALS,CasesSCOREBOARDOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("label",REQUIRED),new Param("minimum",REQUIRED),new Param("maximum",REQUIRED)),List.of(),null),args));
            case "_typed" -> f_typed(bind(GLOBALS,CasesSCOREBOARDOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("label",REQUIRED)),List.of(new Param("kind",REQUIRED)),null),args));
            case "normalize_native_zhongguo_scoreboard_state_v1" -> fnormalize_native_zhongguo_scoreboard_state_v1(bind(GLOBALS,CasesSCOREBOARDOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED)),List.of(new Param("expected_query",REQUIRED),new Param("expected_snapshot_revision",REQUIRED),new Param("expected_date_raw",REQUIRED),new Param("expected_player_character_id",REQUIRED)),null),args));
            default -> throw new IllegalStateException("unlowered original function: "+name);
        };
    }
    // Original zhongguo_scoreboard_state_contract.py:208..211
    private static V f_exact(E e){
        if(truth(or(e,q1->b(!truth(call(q1,"isinstance",args(new Part[]{p(q1.get("value")),p(q1.get("dict"))})))),q2->compare(q2,call(q2,"set",args(new Part[]{p(q2.get("value"))})),new Comparison(Cmp.NE,q3->q3.get("keys")))))) {
            throw new Rejected(py(joined(s(py(e.get("label"))),s(" has unexpected fields"))));
        }
        return e.get("value");
    }
    // Original zhongguo_scoreboard_state_contract.py:214..219
    private static V f_integer(E e){
        if(truth(or(e,q4->call(q4,"isinstance",args(new Part[]{p(q4.get("value")),p(q4.get("bool"))})),q5->b(!truth(call(q5,"isinstance",args(new Part[]{p(q5.get("value")),p(q5.get("int"))}))))))) {
            throw new Rejected(py(joined(s(py(e.get("label"))),s(" must be an integer"))));
        }
        if(truth(b(!truth(compare(e,e.get("minimum"),new Comparison(Cmp.LE,q6->q6.get("value")),new Comparison(Cmp.LE,q7->q7.get("maximum"))))))) {
            throw new Rejected(py(joined(s(py(e.get("label"))),s(" is out of range"))));
        }
        return e.get("value");
    }
    // Original zhongguo_scoreboard_state_contract.py:222..252
    private static V f_typed(E e){
        assign(e,new NameTarget("field"),call(e,"_exact",args(new Part[]{p(e.get("value")),p(e.get("_TYPED_KEYS")),p(e.get("label"))})));
        assign(e,new NameTarget("status"),get(e.get("field"),s("status")));
        assign(e,new NameTarget("raw"),get(e.get("field"),s("value")));
        assign(e,new NameTarget("reason"),get(e.get("field"),s("unavailable_reason")));
        if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q8->s("available"))))) {
            if(truth(compare(e,e.get("reason"),new Comparison(Cmp.IS_NOT,q9->NONE)))) {
                throw new Rejected(py(joined(s(py(e.get("label"))),s(" available value has a reason"))));
            }
            if(truth(compare(e,e.get("kind"),new Comparison(Cmp.EQ,q10->s("bool"))))) {
                if(truth(b(!truth(call(e,"isinstance",args(new Part[]{p(e.get("raw")),p(e.get("bool"))})))))) {
                    throw new Rejected(py(joined(s(py(e.get("label"))),s(" must contain a boolean"))));
                }
            } else {
                if(truth(compare(e,e.get("kind"),new Comparison(Cmp.EQ,q11->s("int"))))) {
                    call(e,"_integer",args(new Part[]{p(e.get("raw")),p(e.get("label")),p(negate(binary(Op.POW,n("2"),n("63")))),p(binary(Op.SUB,binary(Op.POW,n("2"),n("63")),n("1")))}));
                } else {
                    if(truth(compare(e,e.get("kind"),new Comparison(Cmp.EQ,q12->s("pointer"))))) {
                        if(truth(or(e,q13->b(!truth(call(q13,"isinstance",args(new Part[]{p(q13.get("raw")),p(q13.get("str"))})))),q14->compare(q14,method(q14.get("_POINTER_RE"),"fullmatch",args(new Part[]{p(q14.get("raw"))})),new Comparison(Cmp.IS,q15->NONE))))) {
                            throw new Rejected(py(joined(s(py(e.get("label"))),s(" must contain an uppercase hex pointer"))));
                        }
                    } else {
                        throw new AssertionError(py(e.get("kind")));
                    }
                }
            }
        } else {
            if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q16->s("unavailable"))))) {
                if(truth(or(e,q17->compare(q17,q17.get("raw"),new Comparison(Cmp.IS_NOT,q18->NONE)),q19->compare(q19,q19.get("reason"),new Comparison(Cmp.NOT_IN,q20->q20.get("_TYPED_REASONS")))))) {
                    throw new Rejected(py(joined(s(py(e.get("label"))),s(" malformed unavailable value"))));
                }
            } else {
                throw new Rejected(py(joined(s(py(e.get("label"))),s(" has an invalid status"))));
            }
        }
        return call(e,"dict",args(new Part[]{p(e.get("field"))}));
    }
    // Original zhongguo_scoreboard_state_contract.py:276..487
    private static V fnormalize_native_zhongguo_scoreboard_state_v1(E e){
        assign(e,new NameTarget("frame"),call(e,"_exact",args(new Part[]{p(e.get("value")),p(e.get("_FRAME_KEYS")),p(s("scoreboard_state"))})));
        if(truth(compare(e,get(e.get("frame"),s("schema_version")),new Comparison(Cmp.NE,q21->n("1"))))) {
            throw new Rejected(py(s("scoreboard_state schema_version is not 1")));
        }
        if(truth(compare(e,get(e.get("frame"),s("case_kind")),new Comparison(Cmp.NE,q22->q22.get("ZHONGGUO_SCOREBOARD_STATE_KIND_V1"))))) {
            throw new Rejected(py(s("scoreboard_state case kind drifted")));
        }
        if(truth(compare(e,get(e.get("frame"),s("request_nonce")),new Comparison(Cmp.NE,q23->attribute(q23.get("expected_query"),"request_nonce"))))) {
            throw new Rejected(py(s("scoreboard_state nonce mismatch")));
        }
        if(truth(compare(e,get(e.get("frame"),s("snapshot_revision")),new Comparison(Cmp.NE,q24->q24.get("expected_snapshot_revision"))))) {
            throw new Rejected(py(s("scoreboard_state native revision mismatch")));
        }
        if(truth(or(e,q25->compare(q25,get(q25.get("frame"),s("date_raw")),new Comparison(Cmp.NE,q26->q26.get("expected_date_raw"))),q27->compare(q27,get(q27.get("frame"),s("paused")),new Comparison(Cmp.IS_NOT,q28->TRUE))))) {
            throw new Rejected(py(s("scoreboard_state is not bound to the paused date")));
        }
        if(truth(compare(e,get(e.get("frame"),s("player_character_id")),new Comparison(Cmp.NE,q29->q29.get("expected_player_character_id"))))) {
            throw new Rejected(py(s("scoreboard_state player mismatch")));
        }
        assign(e,new NameTarget("status"),get(e.get("frame"),s("status")));
        if(truth(compare(e,e.get("status"),new Comparison(Cmp.NOT_IN,q30->set(p(s("available")),p(s("unavailable"))))))) {
            throw new Rejected(py(s("scoreboard_state status is invalid")));
        }
        assign(e,new NameTarget("reason"),get(e.get("frame"),s("unavailable_reason")));
        if(truth(or(e,q31->and(q31,q32->compare(q32,q32.get("status"),new Comparison(Cmp.EQ,q33->s("available"))),q34->compare(q34,q34.get("reason"),new Comparison(Cmp.IS_NOT,q35->NONE))),q36->and(q36,q37->compare(q37,q37.get("status"),new Comparison(Cmp.EQ,q38->s("unavailable"))),q39->compare(q39,q39.get("reason"),new Comparison(Cmp.NOT_IN,q40->q40.get("_TOP_REASONS"))))))) {
            throw new Rejected(py(s("scoreboard_state top-level reason is invalid")));
        }
        assign(e,new NameTarget("tree_fingerprint"),get(e.get("frame"),s("tree_fingerprint_v1")));
        assign(e,new NameTarget("semantic_fingerprint"),get(e.get("frame"),s("semantic_fingerprint_v1")));
        assign(e,new NameTarget("provider_session_id"),get(e.get("frame"),s("provider_session_id")));
        assign(e,new NameTarget("observation_sequence"),call(e,"_integer",args(new Part[]{p(get(e.get("frame"),s("observation_sequence"))),p(s("scoreboard_state observation_sequence")),p(n("0")),p(binary(Op.SUB,binary(Op.POW,n("2"),n("64")),n("1")))})));
        assign(e,new NameTarget("observed_state_revision"),call(e,"_integer",args(new Part[]{p(get(e.get("frame"),s("observed_state_revision"))),p(s("scoreboard_state observed_state_revision")),p(n("0")),p(binary(Op.SUB,binary(Op.POW,n("2"),n("64")),n("1")))})));
        if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q41->s("available"))))) {
            if(truth(or(e,q42->b(!truth(call(q42,"isinstance",args(new Part[]{p(q42.get("tree_fingerprint")),p(q42.get("str"))})))),q43->compare(q43,method(q43.get("_FINGERPRINT_RE"),"fullmatch",args(new Part[]{p(q43.get("tree_fingerprint"))})),new Comparison(Cmp.IS,q44->NONE)),q45->b(!truth(call(q45,"isinstance",args(new Part[]{p(q45.get("semantic_fingerprint")),p(q45.get("str"))})))),q46->compare(q46,method(q46.get("_FINGERPRINT_RE"),"fullmatch",args(new Part[]{p(q46.get("semantic_fingerprint"))})),new Comparison(Cmp.IS,q47->NONE)),q48->b(!truth(call(q48,"isinstance",args(new Part[]{p(q48.get("provider_session_id")),p(q48.get("str"))})))),q49->compare(q49,method(q49.get("_PROVIDER_SESSION_RE"),"fullmatch",args(new Part[]{p(q49.get("provider_session_id"))})),new Comparison(Cmp.IS,q50->NONE)),q51->compare(q51,q51.get("observation_sequence"),new Comparison(Cmp.LT,q52->n("1"))),q53->compare(q53,q53.get("observed_state_revision"),new Comparison(Cmp.LT,q54->n("1")))))) {
                throw new Rejected(py(s("available scoreboard_state lacks provider observation binding")));
            }
        } else {
            assign(e,new NameTarget("tree_fingerprint_valid"),and(e,q55->call(q55,"isinstance",args(new Part[]{p(q55.get("tree_fingerprint")),p(q55.get("str"))})),q56->or(q56,q57->compare(q57,q57.get("tree_fingerprint"),new Comparison(Cmp.EQ,q58->s(""))),q59->compare(q59,method(q59.get("_FINGERPRINT_RE"),"fullmatch",args(new Part[]{p(q59.get("tree_fingerprint"))})),new Comparison(Cmp.IS_NOT,q60->NONE)))));
            assign(e,new NameTarget("semantic_fingerprint_valid"),and(e,q61->call(q61,"isinstance",args(new Part[]{p(q61.get("semantic_fingerprint")),p(q61.get("str"))})),q62->or(q62,q63->compare(q63,q63.get("semantic_fingerprint"),new Comparison(Cmp.EQ,q64->s(""))),q65->compare(q65,method(q65.get("_FINGERPRINT_RE"),"fullmatch",args(new Part[]{p(q65.get("semantic_fingerprint"))})),new Comparison(Cmp.IS_NOT,q66->NONE)))));
            assign(e,new NameTarget("provider_valid"),and(e,q67->call(q67,"isinstance",args(new Part[]{p(q67.get("provider_session_id")),p(q67.get("str"))})),q68->or(q68,q69->compare(q69,q69.get("provider_session_id"),new Comparison(Cmp.EQ,q70->s(""))),q71->compare(q71,method(q71.get("_PROVIDER_SESSION_RE"),"fullmatch",args(new Part[]{p(q71.get("provider_session_id"))})),new Comparison(Cmp.IS_NOT,q72->NONE)))));
            if(truth(or(e,q73->b(!truth(q73.get("tree_fingerprint_valid"))),q74->b(!truth(q74.get("semantic_fingerprint_valid"))),q75->b(!truth(q75.get("provider_valid")))))) {
                throw new Rejected(py(s("unavailable scoreboard_state diagnostics are malformed")));
            }
        }
        assign(e,new NameTarget("widgets"),get(e.get("frame"),s("widgets")));
        if(truth(or(e,q76->b(!truth(call(q76,"isinstance",args(new Part[]{p(q76.get("widgets")),p(q76.get("list"))})))),q77->compare(q77,call(q77,"len",args(new Part[]{p(q77.get("widgets"))})),new Comparison(Cmp.NE,q78->call(q78,"len",args(new Part[]{p(q78.get("_WIDGET_IDENTITIES"))}))))))) {
            throw new Rejected(py(s("scoreboard_state widgets are incomplete")));
        }
        assign(e,new NameTarget("normalized_widgets"),seq(false));
        for(V q79:iter(call(e,"enumerate",args(new Part[]{p(e.get("_WIDGET_IDENTITIES"))})))) {
            assign(e,new TupleTarget(List.of(new NameTarget("index"),new NameTarget("expected"))),q79);
            assign(e,new NameTarget("widget"),call(e,"_exact",args(new Part[]{p(get(e.get("widgets"),e.get("index"))),p(e.get("_WIDGET_KEYS")),p(joined(s("widget["),s(py(e.get("index"))),s("]")))})));
            if(truth(compare(e,seq(true,p(get(e.get("widget"),s("stable_identity"))),p(get(e.get("widget"),s("runtime_name")))),new Comparison(Cmp.NE,q80->q80.get("expected"))))) {
                throw new Rejected(py(joined(s("widget["),s(py(e.get("index"))),s("] identity drifted"))));
            }
            assign(e,new NameTarget("normalized"),dict(new Item(s("stable_identity"),get(e.get("widget"),s("stable_identity"))),new Item(s("runtime_name"),get(e.get("widget"),s("runtime_name"))),new Item(s("instance_pointer"),call(e,"_typed",args(new Part[]{p(get(e.get("widget"),s("instance_pointer"))),p(joined(s("widget["),s(py(e.get("index"))),s("].instance_pointer")))},new Kw("kind",s("pointer"))))),new Item(s("vtable_pointer"),call(e,"_typed",args(new Part[]{p(get(e.get("widget"),s("vtable_pointer"))),p(joined(s("widget["),s(py(e.get("index"))),s("].vtable_pointer")))},new Kw("kind",s("pointer")))))));
            for(V q81:iter(seq(true,p(s("exists")),p(s("local_visible")),p(s("effective_visible")),p(s("enabled")),p(s("focused")),p(s("modal_blocking"))))) {
                assign(e,new NameTarget("key"),q81);
                put(e.get("normalized"),e.get("key"),call(e,"_typed",args(new Part[]{p(get(e.get("widget"),e.get("key"))),p(joined(s("widget["),s(py(e.get("index"))),s("]."),s(py(e.get("key")))))},new Kw("kind",s("bool")))));
            }
            for(V q82:iter(seq(true,p(s("screen_x")),p(s("screen_y")),p(s("screen_width")),p(s("screen_height")),p(s("scroll_min")),p(s("scroll_max")),p(s("scroll_value"))))) {
                assign(e,new NameTarget("key"),q82);
                put(e.get("normalized"),e.get("key"),call(e,"_typed",args(new Part[]{p(get(e.get("widget"),e.get("key"))),p(joined(s("widget["),s(py(e.get("index"))),s("]."),s(py(e.get("key")))))},new Kw("kind",s("int")))));
            }
            method(e.get("normalized_widgets"),"append",args(new Part[]{p(e.get("normalized"))}));
            if(truth(and(e,q83->compare(q83,q83.get("status"),new Comparison(Cmp.EQ,q84->s("available"))),q85->or(q85,q86->compare(q86,get(get(q86.get("normalized"),s("instance_pointer")),s("status")),new Comparison(Cmp.NE,q87->s("available"))),q88->compare(q88,get(get(q88.get("normalized"),s("vtable_pointer")),s("status")),new Comparison(Cmp.NE,q89->s("available"))))))) {
                throw new Rejected(py(joined(s("widget["),s(py(e.get("index"))),s("] lacks paused probe pointers"))));
            }
        }
        assign(e,new NameTarget("acl"),call(e,"_exact",args(new Part[]{p(get(e.get("frame"),s("acl"))),p(set(p(s("managed")),p(s("received_self")))),p(s("acl"))})));
        assign(e,new NameTarget("managed"),call(e,"_exact",args(new Part[]{p(get(e.get("acl"),s("managed"))),p(e.get("_MANAGED_KEYS")),p(s("acl.managed"))})));
        assign(e,new NameTarget("received"),call(e,"_exact",args(new Part[]{p(get(e.get("acl"),s("received_self"))),p(e.get("_RECEIVED_KEYS")),p(s("acl.received_self"))})));
        for(V q90:iter(seq(true,p(s("surface_available")),p(s("current_player_can_assess_others"))))) {
            assign(e,new NameTarget("key"),q90);
            if(truth(b(!truth(call(e,"isinstance",args(new Part[]{p(get(e.get("managed"),e.get("key"))),p(e.get("bool"))})))))) {
                throw new Rejected(py(joined(s("acl.managed."),s(py(e.get("key"))),s(" must be boolean"))));
            }
        }
        assign(e,new NameTarget("normalized_managed"),dict(new Expansion(e.get("managed")),new Item(s("owner_character_id"),call(e,"_typed",args(new Part[]{p(get(e.get("managed"),s("owner_character_id"))),p(s("acl.managed.owner_character_id"))},new Kw("kind",s("int"))))),new Item(s("first_subject_character_id"),call(e,"_typed",args(new Part[]{p(get(e.get("managed"),s("first_subject_character_id"))),p(s("acl.managed.first_subject_character_id"))},new Kw("kind",s("int")))))));
        for(V q91:iter(seq(true,p(s("surface_available")),p(s("current_player_is_subject"))))) {
            assign(e,new NameTarget("key"),q91);
            if(truth(b(!truth(call(e,"isinstance",args(new Part[]{p(get(e.get("received"),e.get("key"))),p(e.get("bool"))})))))) {
                throw new Rejected(py(joined(s("acl.received_self."),s(py(e.get("key"))),s(" must be boolean"))));
            }
        }
        assign(e,new NameTarget("normalized_received"),call(e,"dict",args(new Part[]{p(e.get("received"))})));
        for(V q92:iter(binary(Op.SUB,e.get("_RECEIVED_KEYS"),set(p(s("surface_available")),p(s("current_player_is_subject")))))) {
            assign(e,new NameTarget("key"),q92);
            put(e.get("normalized_received"),e.get("key"),call(e,"_typed",args(new Part[]{p(get(e.get("received"),e.get("key"))),p(joined(s("acl.received_self."),s(py(e.get("key")))))},new Kw("kind",s("int")))));
        }
        if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q93->s("available"))))) {
            if(truth(compare(e,get(e.get("managed"),s("current_player_can_assess_others")),new Comparison(Cmp.IS_NOT,q94->get(q94.get("managed"),s("surface_available")))))) {
                throw new Rejected(py(s("managed ACL is not surface-derived")));
            }
            if(truth(and(e,q95->compare(q95,get(q95.get("received"),s("current_player_is_subject")),new Comparison(Cmp.IS,q96->TRUE)),q97->compare(q97,get(q97.get("received"),s("surface_available")),new Comparison(Cmp.IS_NOT,q98->TRUE))))) {
                throw new Rejected(py(s("received-self subject lacks its list surface")));
            }
        }
        assign(e,new NameTarget("actions"),call(e,"_exact",args(new Part[]{p(get(e.get("frame"),s("actions"))),p(set(p(s("activate")),p(s("close")),p(s("reopen")))),p(s("actions"))})));
        assign(e,new NameTarget("normalized_actions"),dictFrom(iter(generator(e,q99->seq(true,p(q99.get("key")),p(call(q99,"_typed",args(new Part[]{p(get(q99.get("actions"),q99.get("key"))),p(joined(s("actions."),s(py(q99.get("key")))))},new Kw("kind",s("bool")))))),new Clause(new NameTarget("key"),q100->seq(true,p(s("activate")),p(s("close")),p(s("reopen"))),List.of())))));
        for(V q101:iter(method(e.get("normalized_actions"),"items",args(new Part[]{})))) {
            assign(e,new TupleTarget(List.of(new NameTarget("key"),new NameTarget("action"))),q101);
            if(truth(or(e,q102->compare(q102,get(q102.get("action"),s("status")),new Comparison(Cmp.NE,q103->s("unavailable"))),q104->compare(q104,get(q104.get("action"),s("unavailable_reason")),new Comparison(Cmp.NE,q105->s("read_only_provider_action_not_exposed")))))) {
                throw new Rejected(py(joined(s("actions."),s(py(e.get("key"))),s(" falsely advertises a write"))));
            }
        }
        assign(e,new NameTarget("readiness"),call(e,"_exact",args(new Part[]{p(get(e.get("frame"),s("readiness"))),p(e.get("_READINESS_KEYS")),p(s("readiness"))})));
        if(truth(call(e,"any",args(new Part[]{p(generator(e,q106->b(!truth(call(q106,"isinstance",args(new Part[]{p(get(q106.get("readiness"),q106.get("key"))),p(q106.get("bool"))})))),new Clause(new NameTarget("key"),q107->q107.get("_READINESS_KEYS"),List.of())))})))) {
            throw new Rejected(py(s("scoreboard_state readiness must be boolean")));
        }
        if(truth(or(e,q108->get(q108.get("readiness"),s("full_widget_gate_ready")),q109->get(q109.get("readiness"),s("production_live_ready"))))) {
            throw new Rejected(py(s("static v1 must not claim full/live readiness")));
        }
        if(truth(and(e,q110->compare(q110,q110.get("status"),new Comparison(Cmp.EQ,q111->s("available"))),q112->b(!truth(get(q112.get("readiness"),s("state_acl_query_ready"))))))) {
            throw new Rejected(py(s("available scoreboard_state lacks minimal readiness")));
        }
        assign(e,new NameTarget("provenance"),call(e,"_exact",args(new Part[]{p(get(e.get("frame"),s("provenance"))),p(call(e,"set",args(new Part[]{p(e.get("_PROVENANCE_VALUES"))}))),p(s("provenance"))})));
        if(truth(compare(e,e.get("provenance"),new Comparison(Cmp.NE,q113->q113.get("_PROVENANCE_VALUES"))))) {
            throw new Rejected(py(s("scoreboard_state provenance drifted")));
        }
        return dict(new Expansion(e.get("frame")),new Item(s("widgets"),e.get("normalized_widgets")),new Item(s("acl"),dict(new Item(s("managed"),e.get("normalized_managed")),new Item(s("received_self"),e.get("normalized_received")))),new Item(s("actions"),e.get("normalized_actions")),new Item(s("readiness"),call(e,"dict",args(new Part[]{p(e.get("readiness"))}))),new Item(s("provenance"),call(e,"dict",args(new Part[]{p(e.get("provenance"))}))));
    }
}
