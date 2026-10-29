package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.PersonCurrentJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;

/** Exact ten current-person normalizers; no unknown leaf or unvalidated object is forwarded. */
public final class BattlePersonCurrentExternalCodec {
    private BattlePersonCurrentExternalCodec() { }
    public static JsonNode normalize(BattlePersonExternalCodec.Leaf leaf,JsonNode raw,String field) {
        java.util.Objects.requireNonNull(leaf);java.util.Objects.requireNonNull(raw);java.util.Objects.requireNonNull(field);
        if(raw.isNull())return nil();
        return switch(leaf) {
            case CARRIER_1C8_B70_DIRECT -> carrier(raw,field);
            case FOLLOWING_2921A90 -> following(raw,field);
            case FOLLOWING_2921A90_CONDITIONAL -> PersonConditionalCodec.conditional(raw,field);
            case FOLLOWING_2921A90_OPINION -> PersonConditionalCodec.opinion(raw,field);
            case FOLLOWING_2921A90_SCOPE_WEIGHTS -> PersonConditionalCodec.scope(raw,field);
            case FOLLOWING_2922680 -> PersonSourceCodec.following(raw,field);
            case FOLLOWING_291CE01_GOVERNMENT_GATE -> government(raw,field);
            case FOLLOWING_291E3A0_LOCAL_TITLES -> PersonTitleCodec.local(raw,field);
            case FOLLOWING_291E3A0_FIRST_TITLE_VECTOR -> PersonTitleCodec.vector(raw,field);
            case FOLLOWING_291E3A0_CAPTURED_TAIL -> PersonTitleCodec.tail(raw,field);
            default -> throw new IllegalArgumentException("leaf outside the ten current Person contracts: "+leaf);
        };
    }
    private static ObjectNode carrier(JsonNode raw,String field) {
        Row r=base(raw,field,"xar.ck3.person-carrier-direct-12004-v1").booleans(false,"ready").booleans(true,"carrier_present")
            .strings(true,"reason selected_model_identity destination_pc_identity character_identity carrier_identity definition_identity table_identity selected_pc_identity")
            .strings(false,"selection").numbers(32,true,true,"character_id definition_magic_u32 source_occurrence_count")
            .numbers(32,false,true,"rank_i32 row_count_i32 default_guard_raw selected_pc_count_i32").numbers(64,false,false,"weight_q100000").child("properties",PersonCurrentJson::pcValues);
        ObjectNode n=r.done();need(selected(s(n,"selection"),"none","mapped_row","static_default_5d71200","unavailable"),field+" unknown selection");
        BigInteger occurrences=i(n,"source_occurrence_count");need(occurrences==null||occurrences.signum()==0||occurrences.equals(BigInteger.ONE),field+" source occurrence count");need(UNIT.equals(i(n,"weight_q100000")),field+" unit append weight changed");
        if(yes(n,"ready")){need(occurrences!=null,field+" ready source lacks occurrence admission");if(BigInteger.ONE.equals(occurrences)){
            BigInteger count=i(n,"selected_pc_count_i32");JsonNode pc=n.get("properties");need(count!=null&&count.signum()>0&&!pc.isNull()&&exists(pc,"keys_u16")&&exists(pc,"values_q64")
                &&eq(count,BigInteger.valueOf(pc.get("keys_u16").size()))&&eq(count,BigInteger.valueOf(pc.get("values_q64").size()))&&exists(n,"selected_pc_identity"),field+" source lacks actual numerical PC");}}
        return n;
    }
    private static JsonNode directRow(JsonNode raw,String field) {
        Row r=new Row(raw,field).numbers(32,true,false,"native_index").booleans(false,"ready").strings(true,"reason object_identity source_pc_identity")
            .numbers(32,false,true,"pc_count_i32").numbers(64,false,false,"weight_q100000").child("properties",PersonCurrentJson::pcValues);
        ObjectNode n=r.done();need(UNIT.equals(i(n,"weight_q100000")),field+" native unit weight differs");state(n,"ready","reason",field);
        if(yes(n,"ready")){JsonNode pc=n.get("properties");BigInteger count=i(n,"pc_count_i32");need(nonnegative(count)&&exists(n,"object_identity")&&exists(n,"source_pc_identity")&&!pc.isNull()&&exists(pc,"keys_u16")&&exists(pc,"values_q64")
            &&eq(count,BigInteger.valueOf(pc.get("keys_u16").size()))&&eq(count,BigInteger.valueOf(pc.get("values_q64").size())),field+" complete direct row lacks actual PC operands");}return n;
    }
    private static ObjectNode following(JsonNode raw,String field) {
        Row r=base(raw,field,"xar.ck3.person-following-2921a90-12004-v1").strings(false,"resolution_selection")
            .booleans(false,"ready direct_ready conditional_ready").booleans(true,"carrier_present admitted")
            .strings(true,"reason direct_reason conditional_reason selected_model_identity character_identity destination_pc_identity carrier_identity registry_identity registry_slots_identity selected_object_identity direct_array_identity conditional_definition_identity")
            .numbers(32,true,true,"character_id requested_full_id_u32 registry_count_u32 selected_full_id_u32 selected_magic_u32 conditional_occurrence_count")
            .numbers(32,false,true,"direct_count_i32 conditional_b8c_count_i32 conditional_bbc_count_i32").children("direct_rows",BattlePersonCurrentExternalCodec::directRow,true);
        ObjectNode n=r.done();need(selected(s(n,"resolution_selection"),"mapped_id","fallback","unavailable"),field+" unknown registry selection");
        state(n,"ready","reason",field);state(n,"direct_ready","direct_reason",field);state(n,"conditional_ready","conditional_reason",field);
        need(yes(n,"ready")== (yes(n,"direct_ready")&&yes(n,"conditional_ready")),field+" whole family readiness mismatch");
        need(i(n,"conditional_occurrence_count")==null||num(n,"conditional_occurrence_count",0),field+" unobserved conditional occurrences supplied");
        need(yes(n,"conditional_ready")==num(n,"conditional_occurrence_count",0),field+" conditional empty-family admission mismatch");
        Boolean admitted=b(n,"admitted");BigInteger magic=i(n,"selected_magic_u32"),full=i(n,"selected_full_id_u32");
        if(Boolean.FALSE.equals(admitted)){
            need(magic!=null&&!magic.equals(BigInteger.valueOf(0x446f6d69L))||num(n,"selected_magic_u32",0x446f6d69L)&&num(n,"selected_full_id_u32",0xffffffffL),field+" known-zero gate not actually failed");need(yes(n,"ready")&&n.get("direct_rows").isEmpty(),field+" known-zero helper carries rows");
        }else if(Boolean.TRUE.equals(admitted)){
            need(num(n,"selected_magic_u32",0x446f6d69L)&&full!=null&&!num(n,"selected_full_id_u32",0xffffffffL),field+" admitted native magic/full ID differs");
            BigInteger count=i(n,"direct_count_i32");int rows=n.get("direct_rows").size();if(yes(n,"direct_ready"))need(nonnegative(count)&&eq(count,BigInteger.valueOf(rows))&&allReady(n.get("direct_rows")),field+" direct family incomplete");
            if(count!=null)need(count.signum()<0?rows==0:BigInteger.valueOf(rows).compareTo(count)<=0,field+" rows exceed physical count");
            BigInteger a=i(n,"conditional_b8c_count_i32"),c=i(n,"conditional_bbc_count_i32");if(a!=null&&a.signum()!=0)need(c==null,field+" BBC undemanded after B8C");
            if(yes(n,"conditional_ready"))need(BigInteger.ZERO.equals(a)&&BigInteger.ZERO.equals(c),field+" known empty family lacks both zeros");
            if(a!=null&&(a.signum()!=0||c!=null&&c.signum()!=0))need(!yes(n,"conditional_ready")&&"conditional_modifier_2a38030_2872300_unobserved".equals(s(n,"conditional_reason")),field+" demanded family lost named gap");
        }else need(!yes(n,"direct_ready")&&!yes(n,"conditional_ready"),field+" unread admission cannot release a family");
        return n;
    }
    private static ObjectNode government(JsonNode raw,String field) {
        Row r=base(raw,field,"xar.ck3.person-government-gate-12004-v1").booleans(false,"ready").strings(true,"reason character_identity selected_model_identity registry_identity character_fallback_identity government_identity")
            .numbers(32,true,true,"character_id flags_40_u32").strings(false,"selection").booleans(true,"model_owner_matches bit19_set branch_admitted known_no_contribution")
            .children("steps",(v,f)->{
                ObjectNode step=new Row(v,f).numbers(32,true,false,"native_index").strings(false,"resolution_selection")
                    .strings(true,"character_identity death_context_identity living_context_identity related_context_identity registry_slots_identity candidate_identity selected_character_identity")
                    .numbers(32,true,true,"magic_u32 full_id_u32 related_full_id_u32 registry_count_u32 candidate_full_id_u32").done();
                need(selected(s(step,"resolution_selection"),"unavailable","mapped","fallback"),f+" unknown Character resolution");return step;
            },true);
        ObjectNode n=r.done();need(selected(s(n,"selection"),"unavailable","living_context","death_context","invalid_character_fallback","selected_null_fallback"),field+" unknown Government selection");
        if(yes(n,"ready")){need(i(n,"flags_40_u32")!=null&&exists(n,"government_identity")&&s(n,"reason")==null,field+" ready Government lacks literal flags");boolean admitted=i(n,"flags_40_u32").testBit(19);need(eq(b(n,"bit19_set"),admitted)&&eq(b(n,"branch_admitted"),admitted)&&eq(b(n,"known_no_contribution"),!admitted),field+" DWORD40 bit19 admission differs");}return n;
    }
}
