package org.xar.ck3.control.nativebridge.capabilities.china_cases;
import java.util.*;
import static org.xar.ck3.control.nativebridge.capabilities.china_cases.CasesNormalizerValues.*;
/** Pure Java port of zhongguo_promotion_compensation_postcondition_contract.py; original SHA-256 9a155b821ec4d9e7c27eca014d381dbd5ea48401de52db3112d045ad569b1f04. No Python runtime. */
final class CasesPROMOTIONOriginalNormalizer {
    private CasesPROMOTIONOriginalNormalizer() {}
    private static final Map<String,V> GLOBALS=globals();
    private static Map<String,V> globals(){
        E e=new E(Map.of(),CasesPROMOTIONOriginalNormalizer::dispatch);
        e.put("QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY",s("game.command.query-zhongguo-promotion-compensation-postcondition-v1"));
        e.put("_TYPED_KEYS",set(p(s("status")),p(s("value")),p(s("unavailable_reason"))));
        e.put("_IDENTITY_KEYS",set(p(s("owner_character_id")),p(s("subject_character_id")),p(s("cycle_serial")),p(s("case_serial")),p(s("revision"))));
        e.put("_READINESS_KEYS",set(p(s("player_owner_binding_ready")),p(s("portfolio_subject_binding_ready")),p(s("source_identity_ready")),p(s("result_identity_ready")),p(s("frozen_case_identity_ready")),p(s("promotion_choice_receipt_ready")),p(s("compensation_receipt_posted")),p(s("same_case_identity_ready")),p(s("revision_binding_ready")),p(s("receipt_serials_ready")),p(s("same_frame_ready")),p(s("ready"))));
        return Map.copyOf(e.locals);
    }
    static V run(Args args){return dispatch("normalize_native_zhongguo_promotion_compensation_v1",args);}
    private static V dispatch(String name,Args args){
        return switch(name){
            case "_exact" -> f_exact(bind(GLOBALS,CasesPROMOTIONOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("keys",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_identity" -> f_identity(bind(GLOBALS,CasesPROMOTIONOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_positive" -> f_positive(bind(GLOBALS,CasesPROMOTIONOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED)),List.of(),null),args));
            case "_typed" -> f_typed(bind(GLOBALS,CasesPROMOTIONOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED),new Param("name",REQUIRED),new Param("kind",REQUIRED)),List.of(),null),args));
            case "normalize_native_zhongguo_promotion_compensation_v1" -> fnormalize_native_zhongguo_promotion_compensation_v1(bind(GLOBALS,CasesPROMOTIONOriginalNormalizer::dispatch,new Sig(List.of(new Param("value",REQUIRED)),List.of(new Param("expected_query",REQUIRED),new Param("expected_snapshot_revision",REQUIRED),new Param("expected_date_raw",REQUIRED),new Param("expected_player_character_id",REQUIRED)),null),args));
            default -> throw new IllegalStateException("unlowered original function: "+name);
        };
    }
    // Original zhongguo_promotion_compensation_postcondition_contract.py:90..93
    private static V f_exact(E e){
        if(truth(or(e,q1->b(!truth(call(q1,"isinstance",args(new Part[]{p(q1.get("value")),p(q1.get("dict"))})))),q2->compare(q2,call(q2,"set",args(new Part[]{p(q2.get("value"))})),new Comparison(Cmp.NE,q3->q3.get("keys")))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must contain exactly the v1 fields"))));
        }
        return e.get("value");
    }
    // Original zhongguo_promotion_compensation_postcondition_contract.py:114..116
    private static V f_identity(E e){
        assign(e,new NameTarget("raw"),call(e,"_exact",args(new Part[]{p(e.get("value")),p(e.get("_IDENTITY_KEYS")),p(e.get("name"))})));
        return dictFrom(iter(generator(e,q4->seq(true,p(q4.get("key")),p(call(q4,"_typed",args(new Part[]{p(get(q4.get("raw"),q4.get("key"))),p(joined(s(py(q4.get("name"))),s("."),s(py(q4.get("key"))))),p(q4.get("int"))})))),new Clause(new NameTarget("key"),q5->q5.get("raw"),List.of()))));
    }
    // Original zhongguo_promotion_compensation_postcondition_contract.py:41..44
    private static V f_positive(E e){
        if(truth(or(e,q6->call(q6,"isinstance",args(new Part[]{p(q6.get("value")),p(q6.get("bool"))})),q7->b(!truth(call(q7,"isinstance",args(new Part[]{p(q7.get("value")),p(q7.get("int"))})))),q8->compare(q8,q8.get("value"),new Comparison(Cmp.LE,q9->n("0")))))) {
            throw new Rejected(py(joined(s(py(e.get("name"))),s(" must be a positive integer"))));
        }
        return e.get("value");
    }
    // Original zhongguo_promotion_compensation_postcondition_contract.py:96..111
    private static V f_typed(E e){
        assign(e,new NameTarget("field"),call(e,"_exact",args(new Part[]{p(e.get("value")),p(e.get("_TYPED_KEYS")),p(e.get("name"))})));
        if(truth(compare(e,get(e.get("field"),s("status")),new Comparison(Cmp.EQ,q10->s("available"))))) {
            assign(e,new NameTarget("raw"),get(e.get("field"),s("value")));
            if(truth(or(e,q11->compare(q11,get(q11.get("field"),s("unavailable_reason")),new Comparison(Cmp.IS_NOT,q12->NONE)),q13->compare(q13,call(q13,"isinstance",args(new Part[]{p(q13.get("raw")),p(q13.get("bool"))})),new Comparison(Cmp.NE,q14->compare(q14,q14.get("kind"),new Comparison(Cmp.IS,q15->q15.get("bool"))))),q16->b(!truth(call(q16,"isinstance",args(new Part[]{p(q16.get("raw")),p(q16.get("kind"))}))))))) {
                throw new Rejected(py(joined(s(py(e.get("name"))),s(" has an invalid available value"))));
            }
        } else {
            if(truth(compare(e,get(e.get("field"),s("status")),new Comparison(Cmp.EQ,q17->s("unavailable"))))) {
                if(truth(or(e,q18->compare(q18,get(q18.get("field"),s("value")),new Comparison(Cmp.IS_NOT,q19->NONE)),q20->b(!truth(call(q20,"isinstance",args(new Part[]{p(get(q20.get("field"),s("unavailable_reason"))),p(q20.get("str"))}))))))) {
                    throw new Rejected(py(joined(s(py(e.get("name"))),s(" has invalid typed unavailability"))));
                }
            } else {
                throw new Rejected(py(joined(s(py(e.get("name"))),s(" has invalid status"))));
            }
        }
        return call(e,"dict",args(new Part[]{p(e.get("field"))}));
    }
    // Original zhongguo_promotion_compensation_postcondition_contract.py:119..201
    private static V fnormalize_native_zhongguo_promotion_compensation_v1(E e){
        assign(e,new NameTarget("keys"),set(p(s("schema_version")),p(s("status")),p(s("capability")),p(s("source_backend_id")),p(s("request_nonce")),p(s("snapshot_revision")),p(s("date_raw")),p(s("paused")),p(s("player_character_id")),p(s("subject_character_id")),p(s("promotion_compensation")),p(s("readiness")),p(s("unavailable_reason"))));
        assign(e,new NameTarget("frame"),call(e,"_exact",args(new Part[]{p(e.get("value")),p(e.get("keys")),p(s("promotion_compensation_frame"))})));
        if(truth(or(e,q21->compare(q21,get(q21.get("frame"),s("schema_version")),new Comparison(Cmp.NE,q22->n("1"))),q23->compare(q23,get(q23.get("frame"),s("capability")),new Comparison(Cmp.NE,q24->q24.get("QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY"))),q25->compare(q25,get(q25.get("frame"),s("source_backend_id")),new Comparison(Cmp.NE,q26->s("ck3-1.19.0.6-native-zhongguo-promotion-compensation-postcondition-v1")))))) {
            throw new Rejected(py(s("provider provenance changed")));
        }
        if(truth(compare(e,get(e.get("frame"),s("request_nonce")),new Comparison(Cmp.NE,q27->attribute(q27.get("expected_query"),"request_nonce"))))) {
            throw new Rejected(py(s("request nonce changed")));
        }
        if(truth(or(e,q28->compare(q28,get(q28.get("frame"),s("snapshot_revision")),new Comparison(Cmp.NE,q29->q29.get("expected_snapshot_revision"))),q30->compare(q30,get(q30.get("frame"),s("date_raw")),new Comparison(Cmp.NE,q31->q31.get("expected_date_raw"))),q32->compare(q32,get(q32.get("frame"),s("paused")),new Comparison(Cmp.IS_NOT,q33->TRUE))))) {
            throw new Rejected(py(s("paused native frame changed")));
        }
        if(truth(or(e,q34->compare(q34,get(q34.get("frame"),s("player_character_id")),new Comparison(Cmp.NE,q35->q35.get("expected_player_character_id"))),q36->compare(q36,attribute(q36.get("expected_query"),"owner_character_id"),new Comparison(Cmp.NE,q37->q37.get("expected_player_character_id")))))) {
            throw new Rejected(py(s("played owner binding changed")));
        }
        call(e,"_positive",args(new Part[]{p(get(e.get("frame"),s("subject_character_id"))),p(s("subject_character_id"))}));
        assign(e,new NameTarget("payload"),call(e,"_exact",args(new Part[]{p(get(e.get("frame"),s("promotion_compensation"))),p(set(p(s("source_identity")),p(s("result_identity")),p(s("frozen_case")),p(s("promotion_choice")),p(s("compensation_receipt")))),p(s("promotion_compensation"))})));
        assign(e,new NameTarget("source"),call(e,"_identity",args(new Part[]{p(get(e.get("payload"),s("source_identity"))),p(s("source_identity"))})));
        assign(e,new NameTarget("result"),call(e,"_identity",args(new Part[]{p(get(e.get("payload"),s("result_identity"))),p(s("result_identity"))})));
        assign(e,new NameTarget("frozen_raw"),call(e,"_exact",args(new Part[]{p(get(e.get("payload"),s("frozen_case"))),p(set(p(s("identity")),p(s("frozen")))),p(s("frozen_case"))})));
        if(truth(compare(e,get(e.get("frozen_raw"),s("frozen")),new Comparison(Cmp.IS_NOT,q38->TRUE)))) {
            throw new Rejected(py(s("frozen case is not frozen")));
        }
        assign(e,new NameTarget("frozen"),call(e,"_identity",args(new Part[]{p(get(e.get("frozen_raw"),s("identity"))),p(s("frozen_case.identity"))})));
        assign(e,new NameTarget("choice_raw"),call(e,"_exact",args(new Part[]{p(get(e.get("payload"),s("promotion_choice"))),p(set(p(s("identity")),p(s("option_number")),p(s("receipt_serial")),p(s("active")),p(s("consumed")))),p(s("promotion_choice"))})));
        assign(e,new NameTarget("choice"),dict(new Expansion(e.get("choice_raw")),new Item(s("identity"),call(e,"_identity",args(new Part[]{p(get(e.get("choice_raw"),s("identity"))),p(s("promotion_choice.identity"))})))));
        for(V q39:iter(seq(true,p(s("option_number")),p(s("receipt_serial"))))) {
            assign(e,new NameTarget("key"),q39);
            put(e.get("choice"),e.get("key"),call(e,"_typed",args(new Part[]{p(get(e.get("choice_raw"),e.get("key"))),p(joined(s("promotion_choice."),s(py(e.get("key"))))),p(e.get("int"))})));
        }
        for(V q40:iter(seq(true,p(s("active")),p(s("consumed"))))) {
            assign(e,new NameTarget("key"),q40);
            put(e.get("choice"),e.get("key"),call(e,"_typed",args(new Part[]{p(get(e.get("choice_raw"),e.get("key"))),p(joined(s("promotion_choice."),s(py(e.get("key"))))),p(e.get("bool"))})));
        }
        assign(e,new NameTarget("receipt_raw"),call(e,"_exact",args(new Part[]{p(get(e.get("payload"),s("compensation_receipt"))),p(set(p(s("identity")),p(s("operation_id")),p(s("option_number")),p(s("receipt_serial")),p(s("active")),p(s("consumed")),p(s("posted")))),p(s("compensation_receipt"))})));
        assign(e,new NameTarget("receipt"),dict(new Expansion(e.get("receipt_raw")),new Item(s("identity"),call(e,"_identity",args(new Part[]{p(get(e.get("receipt_raw"),s("identity"))),p(s("compensation_receipt.identity"))})))));
        for(V q41:iter(seq(true,p(s("operation_id")),p(s("option_number")),p(s("receipt_serial"))))) {
            assign(e,new NameTarget("key"),q41);
            put(e.get("receipt"),e.get("key"),call(e,"_typed",args(new Part[]{p(get(e.get("receipt_raw"),e.get("key"))),p(joined(s("compensation_receipt."),s(py(e.get("key"))))),p(e.get("int"))})));
        }
        for(V q42:iter(seq(true,p(s("active")),p(s("consumed")),p(s("posted"))))) {
            assign(e,new NameTarget("key"),q42);
            put(e.get("receipt"),e.get("key"),call(e,"_typed",args(new Part[]{p(get(e.get("receipt_raw"),e.get("key"))),p(joined(s("compensation_receipt."),s(py(e.get("key"))))),p(e.get("bool"))})));
        }
        assign(e,new NameTarget("readiness_raw"),call(e,"_exact",args(new Part[]{p(get(e.get("frame"),s("readiness"))),p(e.get("_READINESS_KEYS")),p(s("readiness"))})));
        if(truth(call(e,"any",args(new Part[]{p(generator(e,q43->b(!truth(call(q43,"isinstance",args(new Part[]{p(q43.get("value")),p(q43.get("bool"))})))),new Clause(new NameTarget("value"),q44->method(q44.get("readiness_raw"),"values",args(new Part[]{})),List.of())))})))) {
            throw new Rejected(py(s("readiness values must be boolean")));
        }
        assign(e,new NameTarget("expected_ready"),call(e,"all",args(new Part[]{p(generator(e,q45->get(q45.get("readiness_raw"),q45.get("key")),new Clause(new NameTarget("key"),q46->binary(Op.SUB,q46.get("_READINESS_KEYS"),set(p(s("ready")))),List.of())))})));
        if(truth(compare(e,get(e.get("readiness_raw"),s("ready")),new Comparison(Cmp.IS_NOT,q47->q47.get("expected_ready"))))) {
            throw new Rejected(py(s("readiness aggregate disagrees")));
        }
        if(truth(compare(e,get(e.get("frame"),s("status")),new Comparison(Cmp.NOT_IN,q48->set(p(s("available")),p(s("unavailable"))))))) {
            throw new Rejected(py(s("invalid provider status")));
        }
        if(truth(and(e,q49->compare(q49,get(q49.get("frame"),s("status")),new Comparison(Cmp.EQ,q50->s("unavailable"))),q51->b(!truth(call(q51,"isinstance",args(new Part[]{p(get(q51.get("frame"),s("unavailable_reason"))),p(q51.get("str"))}))))))) {
            throw new Rejected(py(s("unavailable provider lacks reason")));
        }
        return dict(new Expansion(e.get("frame")),new Item(s("promotion_compensation"),dict(new Item(s("source_identity"),e.get("source")),new Item(s("result_identity"),e.get("result")),new Item(s("frozen_case"),dict(new Item(s("identity"),e.get("frozen")),new Item(s("frozen"),TRUE))),new Item(s("promotion_choice"),e.get("choice")),new Item(s("compensation_receipt"),e.get("receipt")))),new Item(s("readiness"),call(e,"dict",args(new Part[]{p(e.get("readiness_raw"))}))));
    }
}
