package org.xar.ck3.control.nativebridge.capabilities.china_cases;
import java.util.*;
import static org.xar.ck3.control.nativebridge.capabilities.china_cases.CasesNormalizerValues.*;
/** Pure Java port of zhongguo_b1_cycle_snapshot_contract.py; original SHA-256 247729b653d2ecca49a894024c9ab6e6450fb74fe17bd559174eca166291f06d. No Python runtime. */
final class CasesB1OriginalNormalizer {
    private CasesB1OriginalNormalizer() {}
    private static final Map<String,V> GLOBALS=globals();
    private static Map<String,V> globals(){
        E e=new E(Map.of(),CasesB1OriginalNormalizer::dispatch);
        e.put("ZHONGGUO_B1_CYCLE_CASE_KIND_V1",s("zhongguo.b1.cycle"));
        e.put("ZHONGGUO_B1_CYCLE_GAME_VERSION_V1",s("1.19.0.6"));
        e.put("ZHONGGUO_B1_CYCLE_EXE_SHA256_V1",s("2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"));
        e.put("ZHONGGUO_B1_CYCLE_BACKEND_ID_V1",s("ck3-1.19.0.6-native-zhongguo-b1-cycle-snapshot-v1"));
        e.put("ZHONGGUO_B1_CYCLE_CONSUMER_ID_V1",s("xar-autoplayer-zhongguo-b1-cycle-snapshot-v1"));
        e.put("ZHONGGUO_B1_CYCLE_ALLOWLIST_ID_V1",s("zg361-b1-cycle-manager-v1"));
        e.put("_TYPED",set(p(s("status")),p(s("value")),p(s("unavailable_reason"))));
        e.put("_FIELD_REASONS",set(p(s("cycle_unavailable")),p(s("variable_absent")),p(s("value_type_mismatch")),p(s("value_out_of_range")),p(s("lifecycle_not_reached"))));
        e.put("_TOP_REASONS",set(p(s("unsupported_build")),p(s("requires_application_main")),p(s("requires_paused")),p(s("map_not_ready")),p(s("cycle_not_found")),p(s("cycle_inconsistent")),p(s("variable_identifier_unavailable")),p(s("variable_context_unavailable")),p(s("state_changed")),p(s("internal_error"))));
        e.put("_GROUPS",dict(new Item(s("cycle"),dict(new Item(s("cycle_serial"),s("int")),new Item(s("case_serial"),s("int")),new Item(s("state"),s("int")),new Item(s("open_year"),s("int")),new Item(s("runtime_schema"),s("int")),new Item(s("active"),s("bool")))),new Item(s("roster"),dict(new Item(s("subject_count"),s("int")),new Item(s("before_prune_count"),s("int")),new Item(s("pruned_count"),s("int")),new Item(s("amendment_count"),s("int")),new Item(s("audit_version"),s("int")),new Item(s("reopen_required"),s("bool")))),new Item(s("processing"),dict(new Item(s("count"),s("int")),new Item(s("agenda_count"),s("int")),new Item(s("local_candidate_count"),s("int")),new Item(s("pre_calibration_valid_count"),s("int")))),new Item(s("quota"),dict(new Item(s("rebuild_generation"),s("int")),new Item(s("built_case_serial"),s("int")),new Item(s("book_version"),s("int")),new Item(s("target_top"),s("int")),new Item(s("target_middle"),s("int")),new Item(s("target_bottom"),s("int")),new Item(s("recount_top"),s("int")),new Item(s("recount_middle"),s("int")),new Item(s("recount_bottom"),s("int")),new Item(s("pre_calibration_expected_count"),s("int")),new Item(s("pre_calibration_mismatch"),s("bool")),new Item(s("pool_membership"),s("bool")))),new Item(s("closure"),dict(new Item(s("calibration_finalized"),s("bool")),new Item(s("state"),s("int")),new Item(s("rewards_issued"),s("bool")),new Item(s("publication_blocked"),s("bool")))),new Item(s("pending"),dict(new Item(s("open_count"),s("int")),new Item(s("slot_used"),s("int")),new Item(s("reward_expected_count"),s("int")),new Item(s("rewards_paid_count"),s("int")),new Item(s("rewards_committed"),s("bool")),new Item(s("watchdog_cancelled_count"),s("int")),new Item(s("watchdog_orphan_count"),s("int"))))));
        e.put("_READINESS",set(p(s("manager_binding_ready")),p(s("cycle_identity_ready")),p(s("roster_ready")),p(s("processing_ready")),p(s("quota_ready")),p(s("closure_ready")),p(s("pending_ready")),p(s("same_frame_ready")),p(s("ready"))));
        e.put("_PROVENANCE",dict(new Item(s("game_version"),e.get("ZHONGGUO_B1_CYCLE_GAME_VERSION_V1")),new Item(s("executable_sha256"),e.get("ZHONGGUO_B1_CYCLE_EXE_SHA256_V1")),new Item(s("backend_id"),e.get("ZHONGGUO_B1_CYCLE_BACKEND_ID_V1")),new Item(s("consumer_id"),e.get("ZHONGGUO_B1_CYCLE_CONSUMER_ID_V1")),new Item(s("allowlist_id"),e.get("ZHONGGUO_B1_CYCLE_ALLOWLIST_ID_V1")),new Item(s("variable_context_for_scope_rva"),s("0x3329A40")),new Item(s("variable_identifier_table_rva"),s("0x3B971A0")),new Item(s("variable_identifier_lookup_rva"),s("0x3B97020")),new Item(s("variable_identifier_name_rva"),s("0x3B97090")),new Item(s("character_storage_slot_rva"),s("0x570C130"))));
        e.put("_FRAME",set(p(s("schema_version")),p(s("status")),p(s("case_kind")),p(s("request_nonce")),p(s("snapshot_revision")),p(s("date_raw")),p(s("paused")),p(s("player_character_id")),p(s("manager_character_id")),spread(e.get("_GROUPS")),p(s("readiness")),p(s("unavailable_reason")),p(s("provenance"))));
        e.put("_NORMALIZED_FRAME",binary(Op.OR,e.get("_FRAME"),set(p(s("invariants")),p(s("anomalies")))));
        return Map.copyOf(e.locals);
    }
    static V run(Args args){return dispatch("normalize_native_zhongguo_b1_cycle_snapshot_v1",args);}
    private static V dispatch(String name,Args args){
        return switch(name){
            case "_derive" -> f_derive(bind(GLOBALS,CasesB1OriginalNormalizer::dispatch,new Sig(List.of(new Param("groups",REQUIRED)),List.of(),null),args));
            case "_exact" -> f_exact(bind(GLOBALS,CasesB1OriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("keys",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_typed" -> f_typed(bind(GLOBALS,CasesB1OriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("kind",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_uint" -> f_uint(bind(GLOBALS,CasesB1OriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED)),List.of(new Param("positive",FALSE)),null),args));
            case "_value" -> f_value(bind(GLOBALS,CasesB1OriginalNormalizer::dispatch,new Sig(List.of(new Param("groups",REQUIRED),new Param("group",REQUIRED),new Param("key",REQUIRED)),List.of(),null),args));
            case "normalize_native_zhongguo_b1_cycle_snapshot_v1" -> fnormalize_native_zhongguo_b1_cycle_snapshot_v1(bind(GLOBALS,CasesB1OriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED)),List.of(new Param("expected_query",REQUIRED),new Param("expected_snapshot_revision",REQUIRED),new Param("expected_date_raw",REQUIRED),new Param("expected_player_character_id",REQUIRED)),null),args));
            default -> throw new IllegalStateException("unlowered original function: "+name);
        };
    }
    // Original zhongguo_b1_cycle_snapshot_contract.py:207..298
    private static V f_derive(E e){
        assign(e,new NameTarget("state"),call(e,"_value",args(new Part[]{p(e.get("groups")),p(s("cycle")),p(s("state"))})));
        assign(e,new NameTarget("active"),call(e,"_value",args(new Part[]{p(e.get("groups")),p(s("cycle")),p(s("active"))})));
        assign(e,new NameTarget("subject_n"),call(e,"_value",args(new Part[]{p(e.get("groups")),p(s("roster")),p(s("subject_count"))})));
        assign(e,new NameTarget("processing_n"),call(e,"_value",args(new Part[]{p(e.get("groups")),p(s("processing")),p(s("count"))})));
        assign(e,new NameTarget("target"),call(e,"list",args(new Part[]{p(generator(e,q1->call(q1,"_value",args(new Part[]{p(q1.get("groups")),p(s("quota")),p(joined(s("target_"),s(py(q1.get("band")))))})),new Clause(new NameTarget("band"),q2->seq(true,p(s("top")),p(s("middle")),p(s("bottom"))),List.of())))})));
        assign(e,new NameTarget("recount"),call(e,"list",args(new Part[]{p(generator(e,q3->call(q3,"_value",args(new Part[]{p(q3.get("groups")),p(s("quota")),p(joined(s("recount_"),s(py(q3.get("band")))))})),new Clause(new NameTarget("band"),q4->seq(true,p(s("top")),p(s("middle")),p(s("bottom"))),List.of())))})));
        assign(e,new NameTarget("open_n"),call(e,"_value",args(new Part[]{p(e.get("groups")),p(s("pending")),p(s("open_count"))})));
        assign(e,new NameTarget("closure"),call(e,"_value",args(new Part[]{p(e.get("groups")),p(s("closure")),p(s("state"))})));
        assign(e,new NameTarget("finalized"),call(e,"_value",args(new Part[]{p(e.get("groups")),p(s("closure")),p(s("calibration_finalized"))})));
        assign(e,new NameTarget("rewards"),call(e,"_value",args(new Part[]{p(e.get("groups")),p(s("closure")),p(s("rewards_issued"))})));
        assign(e,new NameTarget("generation"),call(e,"_value",args(new Part[]{p(e.get("groups")),p(s("quota")),p(s("rebuild_generation"))})));
        assign(e,new NameTarget("counted"),seq(true,p(e.get("subject_n")),p(e.get("processing_n")),p(e.get("open_n")),p(e.get("generation")),spread(e.get("target")),spread(e.get("recount"))));
        if(truth(compare(e,e.get("state"),new Comparison(Cmp.IS,q5->NONE)))) {
            assign(e,new NameTarget("closed_coherent"),NONE);
        } else {
            if(truth(compare(e,e.get("state"),new Comparison(Cmp.NE,q6->n("8"))))) {
                assign(e,new NameTarget("closed_coherent"),TRUE);
            } else {
                if(truth(or(e,q7->compare(q7,q7.get("closure"),new Comparison(Cmp.IS,q8->NONE)),q9->compare(q9,q9.get("finalized"),new Comparison(Cmp.IS,q10->NONE)),q11->compare(q11,q11.get("rewards"),new Comparison(Cmp.IS,q12->NONE))))) {
                    assign(e,new NameTarget("closed_coherent"),NONE);
                } else {
                    assign(e,new NameTarget("closed_coherent"),and(e,q13->compare(q13,q13.get("closure"),new Comparison(Cmp.EQ,q14->n("4"))),q15->compare(q15,q15.get("finalized"),new Comparison(Cmp.IS,q16->TRUE)),q17->compare(q17,q17.get("rewards"),new Comparison(Cmp.IS,q18->TRUE))));
                }
            }
        }
        assign(e,new NameTarget("invariants"),dict(new Item(s("active_matches_state"),(truth(or(e,q19->compare(q19,q19.get("state"),new Comparison(Cmp.IS,q20->NONE)),q21->compare(q21,q21.get("active"),new Comparison(Cmp.IS,q22->NONE))))?NONE:compare(e,e.get("active"),new Comparison(Cmp.IS,q23->compare(q23,q23.get("state"),new Comparison(Cmp.LT,q24->n("8"))))))),new Item(s("counts_nonnegative"),(truth(call(e,"any",args(new Part[]{p(generator(e,q25->compare(q25,q25.get("value"),new Comparison(Cmp.IS,q27->NONE)),new Clause(new NameTarget("value"),q26->q26.get("counted"),List.of())))})))?NONE:call(e,"all",args(new Part[]{p(generator(e,q28->compare(q28,q28.get("value"),new Comparison(Cmp.GE,q30->n("0"))),new Clause(new NameTarget("value"),q29->q29.get("counted"),List.of())))})))),new Item(s("processing_within_roster"),(truth(or(e,q31->compare(q31,q31.get("subject_n"),new Comparison(Cmp.IS,q32->NONE)),q33->compare(q33,q33.get("processing_n"),new Comparison(Cmp.IS,q34->NONE))))?NONE:compare(e,e.get("processing_n"),new Comparison(Cmp.LE,q35->q35.get("subject_n"))))),new Item(s("quota_target_conserved"),(truth(or(e,q36->compare(q36,q36.get("processing_n"),new Comparison(Cmp.IS,q37->NONE)),q38->call(q38,"any",args(new Part[]{p(generator(q38,q39->compare(q39,q39.get("v"),new Comparison(Cmp.IS,q41->NONE)),new Clause(new NameTarget("v"),q40->q40.get("target"),List.of())))}))))?NONE:compare(e,call(e,"sum",args(new Part[]{p(e.get("target"))})),new Comparison(Cmp.EQ,q42->q42.get("processing_n"))))),new Item(s("quota_recount_conserved"),(truth(or(e,q43->compare(q43,q43.get("processing_n"),new Comparison(Cmp.IS,q44->NONE)),q45->call(q45,"any",args(new Part[]{p(generator(q45,q46->compare(q46,q46.get("v"),new Comparison(Cmp.IS,q48->NONE)),new Clause(new NameTarget("v"),q47->q47.get("recount"),List.of())))}))))?NONE:compare(e,call(e,"sum",args(new Part[]{p(e.get("recount"))})),new Comparison(Cmp.EQ,q49->q49.get("processing_n"))))),new Item(s("quota_target_matches_recount"),(truth(call(e,"any",args(new Part[]{p(generator(e,q50->compare(q50,q50.get("v"),new Comparison(Cmp.IS,q52->NONE)),new Clause(new NameTarget("v"),q51->seq(true,spread(q51.get("target")),spread(q51.get("recount"))),List.of())))})))?NONE:compare(e,e.get("target"),new Comparison(Cmp.EQ,q53->q53.get("recount"))))),new Item(s("closed_state_coherent"),e.get("closed_coherent"))));
        assign(e,new NameTarget("anomalies"),seq(false));
        if(truth(and(e,q54->compare(q54,q54.get("state"),new Comparison(Cmp.IS_NOT,q55->NONE)),q56->compare(q56,q56.get("active"),new Comparison(Cmp.IS_NOT,q57->compare(q57,q57.get("state"),new Comparison(Cmp.LT,q58->n("8")))))))) {
            method(e.get("anomalies"),"append",args(new Part[]{p(s("active_state_mismatch"))}));
        }
        if(truth(and(e,q59->compare(q59,q59.get("subject_n"),new Comparison(Cmp.EQ,q60->n("0"))),q61->compare(q61,q61.get("active"),new Comparison(Cmp.IS,q62->TRUE))))) {
            method(e.get("anomalies"),"append",args(new Part[]{p(s("active_zero_roster"))}));
        }
        if(truth(and(e,q63->compare(q63,q63.get("subject_n"),new Comparison(Cmp.IS_NOT,q64->NONE)),q65->compare(q65,q65.get("processing_n"),new Comparison(Cmp.IS_NOT,q66->NONE)),q67->compare(q67,q67.get("processing_n"),new Comparison(Cmp.GT,q68->q68.get("subject_n")))))) {
            method(e.get("anomalies"),"append",args(new Part[]{p(s("processing_exceeds_roster"))}));
        }
        if(truth(and(e,q69->call(q69,"all",args(new Part[]{p(generator(q69,q70->compare(q70,q70.get("v"),new Comparison(Cmp.IS_NOT,q72->NONE)),new Clause(new NameTarget("v"),q71->q71.get("target"),List.of())))})),q73->compare(q73,q73.get("processing_n"),new Comparison(Cmp.IS_NOT,q74->NONE)),q75->compare(q75,call(q75,"sum",args(new Part[]{p(q75.get("target"))})),new Comparison(Cmp.NE,q76->q76.get("processing_n")))))) {
            method(e.get("anomalies"),"append",args(new Part[]{p(s("quota_target_processing_mismatch"))}));
        }
        if(truth(and(e,q77->call(q77,"all",args(new Part[]{p(generator(q77,q78->compare(q78,q78.get("v"),new Comparison(Cmp.IS_NOT,q80->NONE)),new Clause(new NameTarget("v"),q79->q79.get("recount"),List.of())))})),q81->compare(q81,q81.get("processing_n"),new Comparison(Cmp.IS_NOT,q82->NONE)),q83->compare(q83,call(q83,"sum",args(new Part[]{p(q83.get("recount"))})),new Comparison(Cmp.NE,q84->q84.get("processing_n")))))) {
            method(e.get("anomalies"),"append",args(new Part[]{p(s("quota_recount_processing_mismatch"))}));
        }
        if(truth(and(e,q85->call(q85,"all",args(new Part[]{p(generator(q85,q86->compare(q86,q86.get("v"),new Comparison(Cmp.IS_NOT,q88->NONE)),new Clause(new NameTarget("v"),q87->seq(true,spread(q87.get("target")),spread(q87.get("recount"))),List.of())))})),q89->compare(q89,q89.get("target"),new Comparison(Cmp.NE,q90->q90.get("recount")))))) {
            method(e.get("anomalies"),"append",args(new Part[]{p(s("quota_target_recount_mismatch"))}));
        }
        if(truth(and(e,q91->compare(q91,q91.get("generation"),new Comparison(Cmp.IS_NOT,q92->NONE)),q93->compare(q93,q93.get("generation"),new Comparison(Cmp.GT,q94->n("0"))),q95->compare(q95,call(q95,"_value",args(new Part[]{p(q95.get("groups")),p(s("quota")),p(s("built_case_serial"))})),new Comparison(Cmp.NE,q96->call(q96,"_value",args(new Part[]{p(q96.get("groups")),p(s("cycle")),p(s("case_serial"))}))))))) {
            method(e.get("anomalies"),"append",args(new Part[]{p(s("quota_generation_case_mismatch"))}));
        }
        if(truth(and(e,q97->compare(q97,q97.get("open_n"),new Comparison(Cmp.IS_NOT,q98->NONE)),q99->compare(q99,q99.get("open_n"),new Comparison(Cmp.LT,q100->n("0")))))) {
            method(e.get("anomalies"),"append",args(new Part[]{p(s("negative_pending_count"))}));
        }
        if(truth(and(e,q101->compare(q101,q101.get("state"),new Comparison(Cmp.EQ,q102->n("8"))),q103->compare(q103,get(q103.get("invariants"),s("closed_state_coherent")),new Comparison(Cmp.IS,q104->FALSE))))) {
            method(e.get("anomalies"),"append",args(new Part[]{p(s("closed_state_incomplete"))}));
        }
        return seq(true,p(e.get("invariants")),p(e.get("anomalies")));
    }
    // Original zhongguo_b1_cycle_snapshot_contract.py:174..177
    private static V f_exact(E e){
        if(truth(or(e,q105->b(!truth(call(q105,"isinstance",args(new Part[]{p(q105.get("value")),p(q105.get("dict"))})))),q106->compare(q106,call(q106,"set",args(new Part[]{p(q106.get("value"))})),new Comparison(Cmp.NE,q107->q107.get("keys")))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must contain exactly the v1 fields"))));
        }
        return e.get("value");
    }
    // Original zhongguo_b1_cycle_snapshot_contract.py:186..199
    private static V f_typed(E e){
        assign(e,new NameTarget("field"),call(e,"_exact",args(new Part[]{p(e.get("value")),p(e.get("_TYPED")),p(e.get("name"))})));
        assign(e,new TupleTarget(List.of(new NameTarget("status"),new NameTarget("raw"),new NameTarget("reason"))),seq(true,p(get(e.get("field"),s("status"))),p(get(e.get("field"),s("value"))),p(get(e.get("field"),s("unavailable_reason")))));
        if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q108->s("available"))))) {
            if(truth(or(e,q109->compare(q109,q109.get("reason"),new Comparison(Cmp.IS_NOT,q110->NONE)),q111->and(q111,q112->compare(q112,q112.get("kind"),new Comparison(Cmp.EQ,q113->s("bool"))),q114->b(!truth(call(q114,"isinstance",args(new Part[]{p(q114.get("raw")),p(q114.get("bool"))}))))),q115->and(q115,q116->compare(q116,q116.get("kind"),new Comparison(Cmp.EQ,q117->s("int"))),q118->or(q118,q119->call(q119,"isinstance",args(new Part[]{p(q119.get("raw")),p(q119.get("bool"))})),q120->b(!truth(call(q120,"isinstance",args(new Part[]{p(q120.get("raw")),p(q120.get("int"))}))))))))) {
                throw new Rejected(py(joined(s(py(e.get("name"))),s(" has invalid available value"))));
            }
        } else {
            if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q121->s("unavailable"))))) {
                if(truth(or(e,q122->compare(q122,q122.get("raw"),new Comparison(Cmp.IS_NOT,q123->NONE)),q124->compare(q124,q124.get("reason"),new Comparison(Cmp.NOT_IN,q125->q125.get("_FIELD_REASONS")))))) {
                    throw new Rejected(py(joined(s(py(e.get("name"))),s(" has invalid unavailable value"))));
                }
            } else {
                throw new Rejected(py(joined(s(py(e.get("name"))),s(".status is invalid"))));
            }
        }
        return call(e,"dict",args(new Part[]{p(e.get("field"))}));
    }
    // Original zhongguo_b1_cycle_snapshot_contract.py:180..183
    private static V f_uint(E e){
        if(truth(or(e,q126->call(q126,"isinstance",args(new Part[]{p(q126.get("value")),p(q126.get("bool"))})),q127->b(!truth(call(q127,"isinstance",args(new Part[]{p(q127.get("value")),p(q127.get("int"))})))),q128->compare(q128,q128.get("value"),new Comparison(Cmp.LT,q129->call(q129,"int",args(new Part[]{p(q129.get("positive"))}))))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must be a bounded integer"))));
        }
        return e.get("value");
    }
    // Original zhongguo_b1_cycle_snapshot_contract.py:202..204
    private static V f_value(E e){
        assign(e,new NameTarget("field"),get(get(e.get("groups"),e.get("group")),e.get("key")));
        return (truth(compare(e,get(e.get("field"),s("status")),new Comparison(Cmp.EQ,q130->s("available"))))?get(e.get("field"),s("value")):NONE);
    }
    // Original zhongguo_b1_cycle_snapshot_contract.py:301..400
    private static V fnormalize_native_zhongguo_b1_cycle_snapshot_v1(E e){
        assign(e,new NameTarget("already_normalized"),and(e,q131->call(q131,"isinstance",args(new Part[]{p(q131.get("value")),p(q131.get("dict"))})),q132->compare(q132,call(q132,"set",args(new Part[]{p(q132.get("value"))})),new Comparison(Cmp.EQ,q133->q133.get("_NORMALIZED_FRAME")))));
        if(truth(e.get("already_normalized"))) {
            assign(e,new NameTarget("supplied_invariants"),get(e.get("value"),s("invariants")));
            assign(e,new NameTarget("supplied_anomalies"),get(e.get("value"),s("anomalies")));
            assign(e,new NameTarget("frame"),dictFrom(iter(generator(e,q134->seq(true,p(q134.get("key")),p(get(q134.get("value"),q134.get("key")))),new Clause(new NameTarget("key"),q135->q135.get("_FRAME"),List.of())))));
        } else {
            assign(e,new NameTarget("supplied_invariants"),NONE);
            assign(e,new NameTarget("supplied_anomalies"),NONE);
            assign(e,new NameTarget("frame"),call(e,"_exact",args(new Part[]{p(e.get("value")),p(e.get("_FRAME")),p(s("b1_cycle_snapshot"))})));
        }
        if(truth(or(e,q136->compare(q136,get(q136.get("frame"),s("schema_version")),new Comparison(Cmp.NE,q137->n("1"))),q138->compare(q138,get(q138.get("frame"),s("case_kind")),new Comparison(Cmp.NE,q139->q139.get("ZHONGGUO_B1_CYCLE_CASE_KIND_V1")))))) {
            throw new Rejected(py(s("B1 cycle schema/case binding changed")));
        }
        if(truth(compare(e,get(e.get("frame"),s("request_nonce")),new Comparison(Cmp.NE,q140->attribute(q140.get("expected_query"),"request_nonce"))))) {
            throw new Rejected(py(s("request nonce binding changed")));
        }
        if(truth(compare(e,call(e,"_uint",args(new Part[]{p(get(e.get("frame"),s("snapshot_revision"))),p(s("snapshot_revision"))},new Kw("positive",TRUE))),new Comparison(Cmp.NE,q141->q141.get("expected_snapshot_revision"))))) {
            throw new Rejected(py(s("snapshot revision binding changed")));
        }
        if(truth(or(e,q142->compare(q142,get(q142.get("frame"),s("date_raw")),new Comparison(Cmp.NE,q143->q143.get("expected_date_raw"))),q144->compare(q144,get(q144.get("frame"),s("paused")),new Comparison(Cmp.IS_NOT,q145->TRUE))))) {
            throw new Rejected(py(s("paused date binding changed")));
        }
        assign(e,new NameTarget("player"),call(e,"_uint",args(new Part[]{p(get(e.get("frame"),s("player_character_id"))),p(s("player_character_id"))},new Kw("positive",TRUE))));
        assign(e,new NameTarget("manager"),call(e,"_uint",args(new Part[]{p(get(e.get("frame"),s("manager_character_id"))),p(s("manager_character_id"))},new Kw("positive",TRUE))));
        if(truth(or(e,q146->compare(q146,q146.get("player"),new Comparison(Cmp.NE,q147->q147.get("expected_player_character_id"))),q148->compare(q148,q148.get("manager"),new Comparison(Cmp.NE,q149->q149.get("player")))))) {
            throw new Rejected(py(s("played-manager binding changed")));
        }
        assign(e,new NameTarget("groups"),dictFrom(iter(generator(e,q150->seq(true,p(q150.get("group")),p(dictFrom(iter(generator(q150,q152->seq(true,p(q152.get("key")),p(call(q152,"_typed",args(new Part[]{p(get(call(q152,"_exact",args(new Part[]{p(get(q152.get("frame"),q152.get("group"))),p(call(q152,"set",args(new Part[]{p(q152.get("spec"))}))),p(q152.get("group"))})),q152.get("key"))),p(q152.get("kind")),p(joined(s(py(q152.get("group"))),s("."),s(py(q152.get("key")))))})))),new Clause(new TupleTarget(List.of(new NameTarget("key"),new NameTarget("kind"))),q153->method(q153.get("spec"),"items",args(new Part[]{})),List.of())))))),new Clause(new TupleTarget(List.of(new NameTarget("group"),new NameTarget("spec"))),q151->method(q151.get("_GROUPS"),"items",args(new Part[]{})),List.of())))));
        assign(e,new NameTarget("readiness"),call(e,"_exact",args(new Part[]{p(get(e.get("frame"),s("readiness"))),p(e.get("_READINESS")),p(s("readiness"))})));
        if(truth(b(!truth(call(e,"all",args(new Part[]{p(generator(e,q154->call(q154,"isinstance",args(new Part[]{p(q154.get("value")),p(q154.get("bool"))})),new Clause(new NameTarget("value"),q155->method(q155.get("readiness"),"values",args(new Part[]{})),List.of())))})))))) {
            throw new Rejected(py(s("readiness must be boolean")));
        }
        assign(e,new NameTarget("provenance"),call(e,"_exact",args(new Part[]{p(get(e.get("frame"),s("provenance"))),p(call(e,"set",args(new Part[]{p(e.get("_PROVENANCE"))}))),p(s("provenance"))})));
        if(truth(compare(e,e.get("provenance"),new Comparison(Cmp.NE,q156->q156.get("_PROVENANCE"))))) {
            throw new Rejected(py(s("exact-build provenance changed")));
        }
        assign(e,new TupleTarget(List.of(new NameTarget("status"),new NameTarget("reason"))),seq(true,p(get(e.get("frame"),s("status"))),p(get(e.get("frame"),s("unavailable_reason")))));
        if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q157->s("available"))))) {
            if(truth(or(e,q158->compare(q158,q158.get("reason"),new Comparison(Cmp.IS_NOT,q159->NONE)),q160->b(!truth(get(q160.get("readiness"),s("ready"))))))) {
                throw new Rejected(py(s("available B1 cycle is not ready")));
            }
            assign(e,new NameTarget("cycle"),get(e.get("groups"),s("cycle")));
            if(truth(call(e,"any",args(new Part[]{p(generator(e,q161->compare(q161,get(get(q161.get("cycle"),q161.get("key")),s("status")),new Comparison(Cmp.NE,q163->s("available"))),new Clause(new NameTarget("key"),q162->seq(true,p(s("cycle_serial")),p(s("case_serial")),p(s("state")),p(s("active"))),List.of())))})))) {
                throw new Rejected(py(s("available B1 cycle identity is partial")));
            }
            if(truth(b(!truth(compare(e,n("1"),new Comparison(Cmp.LE,q164->get(get(q164.get("cycle"),s("state")),s("value"))),new Comparison(Cmp.LE,q165->n("8"))))))) {
                throw new Rejected(py(s("B1 cycle state is out of range")));
            }
        } else {
            if(truth(compare(e,e.get("status"),new Comparison(Cmp.EQ,q166->s("unavailable"))))) {
                if(truth(or(e,q167->compare(q167,q167.get("reason"),new Comparison(Cmp.NOT_IN,q168->q168.get("_TOP_REASONS"))),q169->get(q169.get("readiness"),s("ready"))))) {
                    throw new Rejected(py(s("unavailable B1 cycle leaks readiness")));
                }
            } else {
                throw new Rejected(py(s("invalid B1 cycle status")));
            }
        }
        assign(e,new TupleTarget(List.of(new NameTarget("invariants"),new NameTarget("anomalies"))),call(e,"_derive",args(new Part[]{p(e.get("groups"))})));
        if(truth(e.get("already_normalized"))) {
            assign(e,new NameTarget("prior_invariants"),call(e,"_exact",args(new Part[]{p(e.get("supplied_invariants")),p(call(e,"set",args(new Part[]{p(e.get("invariants"))}))),p(s("b1_cycle_snapshot.invariants"))})));
            if(truth(call(e,"any",args(new Part[]{p(generator(e,q170->or(q170,q172->compare(q172,call(q172,"type",args(new Part[]{p(get(q172.get("prior_invariants"),q172.get("key")))})),new Comparison(Cmp.IS_NOT,q173->call(q173,"type",args(new Part[]{p(q173.get("expected"))})))),q174->compare(q174,get(q174.get("prior_invariants"),q174.get("key")),new Comparison(Cmp.NE,q175->q175.get("expected")))),new Clause(new TupleTarget(List.of(new NameTarget("key"),new NameTarget("expected"))),q171->method(q171.get("invariants"),"items",args(new Part[]{})),List.of())))})))) {
                throw new Rejected(py(s("B1 cycle derived invariants changed")));
            }
            if(truth(or(e,q176->b(!truth(call(q176,"isinstance",args(new Part[]{p(q176.get("supplied_anomalies")),p(q176.get("list"))})))),q177->call(q177,"any",args(new Part[]{p(generator(q177,q178->b(!truth(call(q178,"isinstance",args(new Part[]{p(q178.get("item")),p(q178.get("str"))})))),new Clause(new NameTarget("item"),q179->q179.get("supplied_anomalies"),List.of())))})),q180->compare(q180,q180.get("supplied_anomalies"),new Comparison(Cmp.NE,q181->q181.get("anomalies")))))) {
                throw new Rejected(py(s("B1 cycle derived anomalies changed")));
            }
        }
        return dict(new Expansion(e.get("frame")),new Expansion(e.get("groups")),new Item(s("readiness"),call(e,"dict",args(new Part[]{p(e.get("readiness"))}))),new Item(s("provenance"),call(e,"dict",args(new Part[]{p(e.get("provenance"))}))),new Item(s("invariants"),e.get("invariants")),new Item(s("anomalies"),e.get("anomalies")));
    }
}
