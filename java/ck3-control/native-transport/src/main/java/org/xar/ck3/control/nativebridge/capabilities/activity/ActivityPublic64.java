package org.xar.ck3.control.nativebridge.capabilities.activity;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.nativebridge.capabilities.activity.ActivityJson.*;

/** Public projection only. Native receipts, ActivityPayload.original and archive encodings stay
 * numeric. Each declared path comes from the existing native typed schema; arbitrary raw/ID fields
 * are never widened. The original business decoder still validates shape and semantics. */
public final class ActivityPublic64 {
    private ActivityPublic64(){ }
    private enum Width { U64,I64 }
    private record Field(List<String> path,Width width) { Field {path=List.copyOf(path);} }
    private static final BigInteger SAFE=BigInteger.valueOf(9_007_199_254_740_991L);
    private static final BigInteger MAX_U64=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static final BigInteger MIN_I64=BigInteger.ONE.shiftLeft(63).negate(),MAX_I64=BigInteger.ONE.shiftLeft(63).subtract(BigInteger.ONE);

    public static RawJson encode(ActivityNativeContracts.Query query,RawJson nativeValue) {
        ObjectNode value=parse(Objects.requireNonNull(nativeValue).bytes());
        for(Field field:fields(Objects.requireNonNull(query)))transform(value,field,0,true);
        ActivityNativeContracts.publicSafeNumbers(value);return raw(value);
    }
    /** Inverse representation conversion, not source qualification or an alternative business parser. */
    public static RawJson decode(ActivityNativeContracts.Query query,RawJson publicValue) {
        ObjectNode value=parse(Objects.requireNonNull(publicValue).bytes());
        // Undeclared integers retain their existing safe numeric domain on public input.
        ActivityNativeContracts.publicSafeNumbers(value);
        for(Field field:fields(Objects.requireNonNull(query)))transform(value,field,0,false);
        return raw(value);
    }
    public static BigInteger positiveRevision(JsonNode value) {
        BigInteger result;
        if(value!=null&&value.isTextual())result=decimal(value.textValue(),Width.U64);
        else {need(value!=null&&value.isIntegralNumber(),"expected_revision must be an exact positive integer");result=value.bigIntegerValue();need(result.compareTo(SAFE)<=0,"numeric expected_revision exceeds the public safe integer range");}
        need(result.signum()>0&&result.compareTo(MAX_U64)<=0,"expected_revision must be positive uint64");return result;
    }
    private static BigInteger decimal(String text,Width width) {
        need(text!=null&&text.length()<=20&&text.matches(width==Width.I64?"(?:0|-[1-9][0-9]*|[1-9][0-9]*)":"(?:0|[1-9][0-9]*)"),"canonical Activity decimal required");
        BigInteger value=new BigInteger(text);range(value,width);return value;
    }
    private static void range(BigInteger value,Width width) {
        need(value.compareTo(width==Width.U64?BigInteger.ZERO:MIN_I64)>=0&&value.compareTo(width==Width.U64?MAX_U64:MAX_I64)<=0,"Activity decimal exceeds its exact native width");
    }
    private static void transform(JsonNode current,Field field,int offset,boolean encode) {
        if(current==null||current.isNull())return;String part=field.path().get(offset);
        if(part.equals("*")) {need(current.isArray(),"Activity declared row path must be an array");for(JsonNode row:current)transform(row,field,offset+1,encode);return;}
        need(current.isObject(),"Activity declared field path must be an object");JsonNode item=current.get(part);
        if(item==null||item.isNull())return;
        if(offset+1<field.path().size()){transform(item,field,offset+1,encode);return;}
        ObjectNode parent=(ObjectNode)current;
        if(encode){need(item.isIntegralNumber(),"native Activity wide field must be an integer");range(item.bigIntegerValue(),field.width());parent.put(part,item.bigIntegerValue().toString());}
        else {need(item.isTextual(),"public Activity wide field must be a canonical decimal string");parent.put(part,decimal(item.textValue(),field.width()));}
    }
    private static void add(List<Field> fields,Width width,String... paths){for(String path:paths)fields.add(new Field(List.of(path.split("/")),width));}
    private static List<Field> fields(ActivityNativeContracts.Query query) {
        var result=new ArrayList<Field>();add(result,Width.U64,"snapshot_revision","queried_revision","queried_native_revision","normal_refresh_sequence");
        switch(query) {
            case GUEST_CANDIDATE -> add(result,Width.I64,"candidate/planner_join_raw");
            case GUEST_OPINION -> add(result,Width.U64,"activity_target/attending_count");
            case GUEST_TARGET -> add(result,Width.I64,"planner_join_raw");
            case GUEST_ROUTE_PROOF -> add(result,Width.I64,"selected_nonhost_rows/*/planner_join_raw","pre_invitation_candidate/planner_join_raw");
            case FULL_COST -> {add(result,Width.I64,"actor_gold_raw");resources(result,true,false);}
            case START_INPUTS -> {
                resources(result,true,true);hosted(result);outcomes(result);
                add(result,Width.U64,"ordinary_guest_route/provenance_refresh_sequence","ordinary_guest_route/candidate/snapshot_revision","ordinary_guest_route/candidate/normal_refresh_sequence");
                add(result,Width.I64,"ordinary_guest_route/candidate/planner_join_raw");
            }
            case HOSTED -> {resources(result,false,true);hosted(result);outcomes(result);journals(result);}
            case GOLD -> add(result,Width.I64,"configured_cost/raw","resource_value/raw");
            case GUEST_RULE -> add(result,Width.U64,"native_key_hash","ordered_rule_count","active_rule_count","filtered_group_count","filtered_character_count");
            case DIAGNOSTIC,STAGE1_OPTION,STAGE2_OPTION,STAGE2_GATE,STAGE2_LOCATION,GUEST_RULE_PROVENANCE -> { }
        }
        return List.copyOf(result);
    }
    private static void resources(List<Field> fields,boolean costs,boolean balances) {
        for(String resource:List.of("gold","treasury","piety","barter_goods")) {
            if(costs)add(fields,Width.I64,"resources/"+resource+"/configured_cost_raw");
            if(balances)add(fields,Width.I64,"balances/"+resource+"/raw");
        }
    }
    private static void hosted(List<Field> fields){add(fields,Width.U64,"hosted_activities/*/native_completion_stamp_raw");}
    private static void outcomes(List<Field> fields){add(fields,Width.I64,"outcome_values/prestige_raw","outcome_values/reveler_xp_raw");}
    private static void journals(List<Field> fields) {
        String terminal="native_terminal_observations/",calls="native_completion_effect_counter_observations/";
        for(String root:List.of(terminal,calls))for(String field:List.of("earliest_retained_sequence_u64","latest_capture_sequence_u64","overflow_dropped_count_u64"))add(fields,Width.U64,root+field);
        add(fields,Width.U64,calls+"pairing_dropped_count_u64");
        for(String field:List.of("capture_sequence_u64","source_cut_rva_u64","manager_identity_u64","activity_identity_u64","type_identity_u64","native_completion_stamp_raw_u64"))add(fields,Width.U64,terminal+"records/*/"+field);
        add(fields,Width.I64,terminal+"records/*/capture_frame/date_raw_i64");
        for(String field:List.of("capture_sequence_u64","observer_invocation_sequence_u64","source_call_rva_u64","source_callee_rva_u64","source_return_rva_u64","activity_identity_u64","participant_identity_u64","effect_identity_u64","native_context_identity_u64","original_parent_rsp_u64","source_after_cut_rva_u64","intervening_call_rva_u64","intervening_callee_rva_u64"))add(fields,Width.U64,calls+"records/*/"+field);
        for(String face:List.of("before","after")) {
            String root=calls+"records/*/"+face+"/";
            add(fields,Width.U64,root+"type_identity_u64",root+"resource_extension_identity_u64");
            add(fields,Width.I64,root+"prestige_raw_i64",root+"reveler_xp_raw_i64",root+"frame/date_raw_i64");
        }
    }
}
