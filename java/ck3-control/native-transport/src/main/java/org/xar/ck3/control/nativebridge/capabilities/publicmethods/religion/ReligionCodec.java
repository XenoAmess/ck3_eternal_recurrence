package org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionContract.*;

/** Strict single public JSON boundary. Native operands are encoded separately and retain native integer tokens. */
public final class ReligionCodec {
    private ReligionCodec() { }
    private static final BigInteger U32_LAST=new BigInteger("4294967294");
    public static List<Method> methods() { return METHODS; }
    public static Method method(String name) { return METHODS.stream().filter(m->m.name().equals(name)).findFirst().orElseThrow(()->new IllegalArgumentException("not an original Religion MCP method: "+name)); }
    public static Request decode(String name, RawJson original) {
        Method method=method(name);ObjectNode row=object(original);Set<String> allowed=method.fields().stream().map(Field::wire).collect(java.util.stream.Collectors.toSet());
        row.fieldNames().forEachRemaining(key->StrictJson.require(allowed.contains(key),"unexpected Religion argument: "+key));
        var arguments=new ArrayList<Argument>();
        for(Field field:method.fields()) {
            JsonNode n=row.get(field.wire());
            if(n==null) { StrictJson.require(!method.required().contains(field),"missing Religion argument: "+field.wire());arguments.add(new Argument(field,new Absent(Presence.MISSING))); }
            else if(n.isNull()) { StrictJson.require(nullable(field)&&!method.required().contains(field),"null Religion argument: "+field.wire());arguments.add(new Argument(field,new Absent(Presence.NULL))); }
            else arguments.add(new Argument(field,decodeValue(field,n,method)));
        }
        Request result=new Request(method,arguments);validateCombinations(result);return result;
    }
    private static Value decodeValue(Field field,JsonNode n,Method method) {
        return switch(field) {
            case EXPECTED_REVISION -> new IntegerValue(PublicUnsigned64.parse(n,PublicUnsigned64.Minimum.ONE,PublicUnsigned64.NumericInput.SAFE_INTEGER_OR_DECIMAL));
            case FAITH_FULL_IDS -> {
                StrictJson.require(n.isArray()&&n.size()>=1&&n.size()<=8,"one to eight native Faith full IDs required");var ids=new ArrayList<BigInteger>();
                for(JsonNode id:n)ids.add(integer(id,BigInteger.ZERO,U32_LAST));StrictJson.require(ids.stream().distinct().count()==ids.size(),"duplicate Faith selectors");yield new IdsValue(ids);
            }
            case REPLACE_EXISTING_TASK, INCLUDE_KNOWLEDGE_CATALOGUE, POLICY_POSITIVE -> { StrictJson.require(n.isBoolean(),"strict Boolean required: "+field.wire());yield new BooleanValue(n.booleanValue()); }
            case TIMEOUT_SECONDS -> { StrictJson.require(n.isNumber(),"finite numeric timeout required");BigDecimal value=n.decimalValue();StrictJson.require(value.signum()>0&&value.compareTo(BigDecimal.valueOf(120))<=0,"finite positive Religion timeout required");yield new DecimalValue(value); }
            case ACTION, CK3_BUILD, ACTION_ID, REQUEST_ID, SUBMITTED_REQUEST_ID, DOCTRINE_KEY, TENET_KEY, OPERATION, OPTION_KEY, EXPECTED_PREVIEW_IDENTITY_SHA256, TYPE_KEY -> {
                StrictJson.require(n.isTextual(),"strict text required: "+field.wire());String value=n.textValue();
                switch(field) {
                    case EXPECTED_PREVIEW_IDENTITY_SHA256 -> StrictJson.require(value.matches("[0-9a-f]{64}"),"observed lowercase preview SHA256 required");
                    case TYPE_KEY -> StrictJson.require(value.getBytes(java.nio.charset.StandardCharsets.UTF_8).length>=1&&value.getBytes(java.nio.charset.StandardCharsets.UTF_8).length<=160&&value.indexOf('\0')<0,"original creation type key length required");
                    case ACTION_ID, REQUEST_ID, SUBMITTED_REQUEST_ID -> StrictJson.require(!value.isEmpty()&&value.getBytes(java.nio.charset.StandardCharsets.UTF_8).length<=63,"original request/action identity must retain 1..63 UTF-8 bytes");
                    case ACTION -> StrictJson.require((method.name().equals("ck3_query_holy_site_planning_knowledge_v1")?Set.of("adopt","create","promote","demote","abandon","enshrine_relic","remove_relic"):Set.of("adopt","promote","demote","abandon")).contains(value),"original HolySite action required");
                    case OPERATION -> StrictJson.require((method.name().startsWith("ck3_submit_")?Set.of("open","confirm","select","start"):Set.of("read","can_select","quote","post")).contains(value),"original pilgrimage operation required");
                    default -> { }
                }
                yield new TextValue(value);
            }
            case BASE_AMOUNT -> new IntegerValue(integer(n,BigInteger.valueOf(-300),BigInteger.valueOf(300)));
            case EXPECTED_EVENT_INSTANCE_ID -> new IntegerValue(integer(n,BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE)));
            case READ_STAGE -> new IntegerValue(integer(n,BigInteger.ZERO,BigInteger.valueOf(Integer.MAX_VALUE)));
            case EXPECTED_ACTIVE_TASK_ID, EXPECTED_INCUMBENT_CHARACTER_ID -> new IntegerValue(integer(n,BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE)));
            case REQUESTED_TITLE_ID -> new IntegerValue(integer(n,BigInteger.ZERO,BigInteger.valueOf(Integer.MAX_VALUE)));
            case PROVINCE_ID -> new IntegerValue(integer(n,BigInteger.ZERO,isPilgrimage(method)?U32_LAST:BigInteger.valueOf(Integer.MAX_VALUE)));
            case MAX_PIETY_COST_RAW, RESERVE_GOLD_RAW, RESERVE_TREASURY_RAW, RESERVE_PIETY_RAW, RESERVE_BARTER_GOODS_RAW -> {
                BigInteger exact=PublicUnsigned64.parse(n,PublicUnsigned64.Minimum.ZERO,PublicUnsigned64.NumericInput.SAFE_INTEGER_OR_DECIMAL);StrictJson.require(exact.compareTo(BigInteger.valueOf(Long.MAX_VALUE))<=0,"original nonnegative signed64 resource amount required");yield new IntegerValue(exact);
            }
            case TARGET_RITE_ID -> new IntegerValue(integer(n,BigInteger.ZERO,Set.of("ck3_query_player_religion_hostility_v1","ck3_query_player_religion_tenets_v1","ck3_query_player_religion_conversion_inputs_v1","ck3_query_player_religion_conversion_terms_v1","ck3_query_player_religion_conversion_reasons_v1").contains(method.name())?U32_LAST.add(BigInteger.ONE):U32_LAST));
            case HOLY_SITE_ID, RECIPIENT_CHARACTER_ID, CANDIDATE_CHARACTER_ID, BARONY_TITLE_ID -> new IntegerValue(integer(n,BigInteger.ZERO,U32_LAST));
        };
    }
    private static boolean nullable(Field f) { return Set.of(Field.HOLY_SITE_ID,Field.DOCTRINE_KEY,Field.TARGET_RITE_ID,Field.TENET_KEY,Field.EXPECTED_EVENT_INSTANCE_ID).contains(f); }
    private static boolean isPilgrimage(Method method) {return method.name().equals("ck3_query_player_pilgrimage_planner_v1")||method.name().equals("ck3_submit_player_pilgrimage_planner_v1");}
    private static BigInteger integer(JsonNode n,BigInteger low,BigInteger high) { StrictJson.require(n.isIntegralNumber(),"strict integral JSON token required");BigInteger x=n.bigIntegerValue();StrictJson.require(x.compareTo(low)>=0&&x.compareTo(high)<=0,"native integer argument outside range");return x; }
    private static void validateCombinations(Request request) {
        if(request.method().name().equals("ck3_query_player_religion_doctrine_knowledge_v1")&&request.value(Field.DOCTRINE_KEY) instanceof TextValue text)StrictJson.require(!text.value().isEmpty(),"original doctrine key cannot be empty");
        if(request.method().name().equals("ck3_query_player_religion_tenets_v1")) {
            boolean rite=request.value(Field.TARGET_RITE_ID) instanceof IntegerValue,tenet=request.value(Field.TENET_KEY) instanceof TextValue;
            StrictJson.require(rite==tenet,"target Rite and tenet key must be supplied together");
            if(tenet){String value=((TextValue)request.value(Field.TENET_KEY)).value();StrictJson.require(!value.isEmpty()&&value.getBytes(java.nio.charset.StandardCharsets.UTF_8).length<=128,"original nonempty tenet key must retain at most128 UTF-8 bytes");}
        }
        if(request.method().name().equals("ck3_query_player_epidemic_recovery_private_v1")) {
            BigInteger title=optionalInteger(request,Field.REQUESTED_TITLE_ID,BigInteger.ZERO);Value event=request.value(Field.EXPECTED_EVENT_INSTANCE_ID);
            StrictJson.require(title.signum()==0?event instanceof IntegerValue:event instanceof Absent,"epidemic list needs the actual event; explicit title must omit the event");
        }
    }
    public static BigInteger optionalInteger(Request request,Field field,BigInteger defaultValue) { Value v=request.value(field);return v instanceof IntegerValue i?i.value():defaultValue; }
    public static ObjectNode nativeArguments(Request request) {
        ObjectNode row=StrictJson.object();
        for(Argument a:request.arguments()) {
            Value v=a.value();if(v instanceof Absent absent) { if(absent.presence()==Presence.NULL)row.putNull(a.field().wire());continue; }
            if(v instanceof IntegerValue i)row.put(a.field().wire(),i.value());
            else if(v instanceof TextValue t)row.put(a.field().wire(),t.value());
            else if(v instanceof BooleanValue b)row.put(a.field().wire(),b.value());
            else if(v instanceof DecimalValue d)row.put(a.field().wire(),d.value());
            else if(v instanceof IdsValue ids) {var array=row.putArray(a.field().wire());ids.values().forEach(array::add);}
        }
        return row;
    }
    public static RawJson encode(Request request) {
        ObjectNode row=nativeArguments(request);if(row.has("expected_revision"))row.put("expected_revision",PublicUnsigned64.canonical(request.expectedRevision(),PublicUnsigned64.Minimum.ONE));
        for(Field field:List.of(Field.MAX_PIETY_COST_RAW,Field.RESERVE_GOLD_RAW,Field.RESERVE_TREASURY_RAW,Field.RESERVE_PIETY_RAW,Field.RESERVE_BARTER_GOODS_RAW))if(row.hasNonNull(field.wire()))row.put(field.wire(),PublicUnsigned64.canonical(row.get(field.wire()).bigIntegerValue(),PublicUnsigned64.Minimum.ZERO));
        return raw(row);
    }
    public static RawJson encode(Response response) { object(response.business());return response.business(); }
    public enum OutputCondition { ALWAYS, QUEUED_CONVERSION }
    public record ResultIntegerPath(List<String> path,PublicUnsigned64.Minimum minimum,OutputCondition condition) {
        public ResultIntegerPath { path=List.copyOf(path);StrictJson.require(!path.isEmpty(),"explicit result JSON path required");java.util.Objects.requireNonNull(minimum);java.util.Objects.requireNonNull(condition); }
    }
    /** Exact schema paths, never recursive field-name matching. Missing optional native extensions are preserved. */
    public static List<ResultIntegerPath> resultIntegerPaths(Method method) {
        var paths=new ArrayList<ResultIntegerPath>();String name=method.name();
        boolean conversion=name.equals("ck3_query_player_religion_conversion_result_private_v1"),county=name.equals("ck3_query_county_conversion_task_result");
        if(conversion||county) {
            add(paths,PublicUnsigned64.Minimum.ONE,OutputCondition.ALWAYS,"owner_submission.native_revision","owner_submission.capture_epoch","owner_submission.request.expected_revision");
            if(county)add(paths,PublicUnsigned64.Minimum.ZERO,OutputCondition.ALWAYS,"before_task.capture_epoch","after_task.capture_epoch","owner_submission.before.capture_epoch","owner_result.after.capture_epoch");
            else {
                for(String root:List.of("before_outcome","after_outcome","owner_submission.before","owner_result.after"))add(paths,PublicUnsigned64.Minimum.ONE,OutputCondition.QUEUED_CONVERSION,root+".capture_epoch",root+".actor.capture_epoch",root+".actor.current_religion.capture_epoch",root+".state.capture_epoch");
                add(paths,PublicUnsigned64.Minimum.ONE,OutputCondition.QUEUED_CONVERSION,"owner_submission.paid_terms.capture_epoch","owner_submission.paid_terms.final_gate.capture_epoch","owner_submission.paid_terms.cost.capture_epoch");
            }
            return List.copyOf(paths);
        }
        if(!ReligionService.actualReadNames().contains(name))return List.of();
        add(paths,PublicUnsigned64.Minimum.ONE,OutputCondition.ALWAYS,"queried_revision","queried_native_revision");
        if(name.startsWith("ck3_query_confucian_")) {
            String suffix=name.substring("ck3_query_confucian_".length(),name.length()-3);
            add(paths,PublicUnsigned64.Minimum.ONE,OutputCondition.ALWAYS,"connection_generation","native_result.snapshot_revision","native_result.confucian_"+suffix+".capture_epoch");
        }else if(name.equals("ck3_query_current_actor_stress_adjustment_v1")) {
            add(paths,PublicUnsigned64.Minimum.ONE,OutputCondition.ALWAYS,"query_sequence","snapshot_revision","connection_generation","current_actor_stress_adjustment.snapshot_revision","current_actor_stress_adjustment.connection_generation");
            add(paths,PublicUnsigned64.Minimum.ZERO,OutputCondition.ALWAYS,"current_actor_stress_adjustment.owner_pump_epoch");
        }else {
            add(paths,PublicUnsigned64.Minimum.ONE,OutputCondition.ALWAYS,"snapshot_revision");
            add(paths,name.equals("ck3_query_player_ghw_permissions_v1")?PublicUnsigned64.Minimum.ZERO:PublicUnsigned64.Minimum.ONE,OutputCondition.ALWAYS,"capture_epoch");
        }
        return List.copyOf(paths);
    }
    private static void add(List<ResultIntegerPath> paths,PublicUnsigned64.Minimum minimum,OutputCondition condition,String... fields) {for(String field:fields)paths.add(new ResultIntegerPath(List.of(field.split("\\.")),minimum,condition));}
    public static ObjectNode publicResult(Method method,ObjectNode originalBusiness) {
        ObjectNode result=originalBusiness.deepCopy();boolean queued=Set.of("converted_material_verified","submitted_verification_pending").contains(result.path("status").textValue());
        for(ResultIntegerPath selected:resultIntegerPaths(method)) {
            if(selected.condition()==OutputCondition.QUEUED_CONVERSION&&!queued)continue;
            JsonNode parent=result;var path=selected.path();
            for(int i=0;i<path.size()-1;i++){parent=parent.get(path.get(i));StrictJson.require(parent!=null&&parent.isObject(),"missing typed Religion result parent: "+path);}
            JsonNode value=parent.get(path.getLast());StrictJson.require(value!=null,"missing typed Religion result u64: "+path);
            BigInteger exact;
            // Native component values can legitimately occupy the entire u64 domain before this public boundary.
            if(value.isIntegralNumber())exact=value.bigIntegerValue();
            else exact=PublicUnsigned64.parse(value,selected.minimum(),PublicUnsigned64.NumericInput.DECIMAL_ONLY);
            ((ObjectNode)parent).put(path.getLast(),PublicUnsigned64.canonical(exact,selected.minimum()));
        }
        return result;
    }
    public static ObjectNode object(RawJson original) { try {JsonNode value=NativeWire.parse(original.bytes());StrictJson.require(value instanceof ObjectNode,"Religion object required");return (ObjectNode)value;}catch(IOException failure){throw new IllegalArgumentException("invalid Religion JSON",failure);} }
    public static RawJson raw(ObjectNode row) { try{return new RawJson(new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsBytes(row));}catch(IOException failure){throw new IllegalArgumentException("Religion JSON encoding failed",failure);} }
    // METHODS are the exact original MCP declarations and argument order, source-pinned in SOURCE-MAP01.
    private static final List<Method> METHODS=List.of(
        new Method("ck3_confirm_holy_site_adoption_decision_v1",List.of(Field.HOLY_SITE_ID,Field.EXPECTED_REVISION),List.of(Field.HOLY_SITE_ID,Field.EXPECTED_REVISION)),
        new Method("ck3_confirm_holy_site_decision_v1",List.of(Field.ACTION,Field.HOLY_SITE_ID,Field.EXPECTED_REVISION),List.of(Field.ACTION,Field.HOLY_SITE_ID,Field.EXPECTED_REVISION)),
        new Method("ck3_convert_player_religion_private_v1",List.of(Field.EXPECTED_REVISION,Field.TARGET_RITE_ID,Field.MAX_PIETY_COST_RAW,Field.ACTION_ID),List.of(Field.EXPECTED_REVISION,Field.TARGET_RITE_ID,Field.MAX_PIETY_COST_RAW,Field.ACTION_ID)),
        new Method("ck3_create_holy_site_once_v1",List.of(Field.EXPECTED_PREVIEW_IDENTITY_SHA256,Field.EXPECTED_REVISION),List.of(Field.EXPECTED_PREVIEW_IDENTITY_SHA256,Field.EXPECTED_REVISION)),
        new Method("ck3_open_holy_site_adoption_decision_v1",List.of(Field.HOLY_SITE_ID,Field.EXPECTED_REVISION),List.of(Field.HOLY_SITE_ID,Field.EXPECTED_REVISION)),
        new Method("ck3_open_holy_site_creation_window_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_open_holy_site_decision_v1",List.of(Field.ACTION,Field.HOLY_SITE_ID,Field.EXPECTED_REVISION),List.of(Field.ACTION,Field.HOLY_SITE_ID,Field.EXPECTED_REVISION)),
        new Method("ck3_open_holy_site_window_v1",List.of(Field.HOLY_SITE_ID,Field.EXPECTED_REVISION),List.of(Field.HOLY_SITE_ID,Field.EXPECTED_REVISION)),
        new Method("ck3_query_confucian_assembly_predicates_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_confucian_challenger_graph_v1",List.of(Field.EXPECTED_REVISION,Field.FAITH_FULL_IDS),List.of(Field.EXPECTED_REVISION,Field.FAITH_FULL_IDS)),
        new Method("ck3_query_confucian_religious_title_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_county_conversion_task_result",List.of(Field.EXPECTED_REVISION,Field.SUBMITTED_REQUEST_ID,Field.ACTION_ID),List.of(Field.EXPECTED_REVISION,Field.SUBMITTED_REQUEST_ID,Field.ACTION_ID)),
        new Method("ck3_query_current_actor_stress_adjustment_v1",List.of(Field.BASE_AMOUNT,Field.EXPECTED_REVISION),List.of(Field.BASE_AMOUNT,Field.EXPECTED_REVISION)),
        new Method("ck3_query_holy_site_planning_knowledge_v1",List.of(Field.ACTION,Field.CK3_BUILD),List.of(Field.ACTION)),
        new Method("ck3_query_player_clergy_appointment_v1",List.of(Field.EXPECTED_REVISION,Field.CANDIDATE_CHARACTER_ID),List.of(Field.EXPECTED_REVISION,Field.CANDIDATE_CHARACTER_ID)),
        new Method("ck3_query_player_epidemic_recovery_private_v1",List.of(Field.EXPECTED_REVISION,Field.REQUESTED_TITLE_ID,Field.EXPECTED_EVENT_INSTANCE_ID),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_ghw_permissions_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_head_of_faith_gold_context_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_holy_order_context_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_holy_order_loan_context_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_holy_order_selected_title_terms_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_holy_site_adoption_detail_v1",List.of(Field.EXPECTED_REVISION,Field.HOLY_SITE_ID),List.of(Field.EXPECTED_REVISION,Field.HOLY_SITE_ID)),
        new Method("ck3_query_player_holy_site_creation_context_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_holy_site_decision_cooldown_v1",List.of(Field.ACTION,Field.EXPECTED_REVISION),List.of(Field.ACTION,Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_holy_site_decision_detail_v1",List.of(Field.ACTION,Field.HOLY_SITE_ID,Field.EXPECTED_REVISION),List.of(Field.ACTION,Field.HOLY_SITE_ID,Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_holy_site_v1",List.of(Field.EXPECTED_REVISION,Field.HOLY_SITE_ID),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_pilgrimage_activities_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_pilgrimage_planner_v1",List.of(Field.EXPECTED_REVISION,Field.OPERATION,Field.PROVINCE_ID,Field.READ_STAGE,Field.OPTION_KEY,Field.TIMEOUT_SECONDS),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_religion_ai_reform_inputs_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_religion_context_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_religion_conversion_choices_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_religion_conversion_inputs_v1",List.of(Field.EXPECTED_REVISION,Field.TARGET_RITE_ID),List.of(Field.EXPECTED_REVISION,Field.TARGET_RITE_ID)),
        new Method("ck3_query_player_religion_conversion_outcome_v1",List.of(Field.EXPECTED_REVISION,Field.TARGET_RITE_ID),List.of(Field.EXPECTED_REVISION,Field.TARGET_RITE_ID)),
        new Method("ck3_query_player_religion_conversion_reasons_v1",List.of(Field.EXPECTED_REVISION,Field.TARGET_RITE_ID),List.of(Field.EXPECTED_REVISION,Field.TARGET_RITE_ID)),
        new Method("ck3_query_player_religion_conversion_result_private_v1",List.of(Field.EXPECTED_REVISION,Field.REQUEST_ID,Field.ACTION_ID),List.of(Field.EXPECTED_REVISION,Field.REQUEST_ID,Field.ACTION_ID)),
        new Method("ck3_query_player_religion_conversion_terms_v1",List.of(Field.EXPECTED_REVISION,Field.TARGET_RITE_ID),List.of(Field.EXPECTED_REVISION,Field.TARGET_RITE_ID)),
        new Method("ck3_query_player_religion_doctrine_catalogue_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_religion_doctrine_knowledge_v1",List.of(Field.EXPECTED_REVISION,Field.DOCTRINE_KEY),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_religion_doctrines_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_religion_draft_doctrine_choices_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_religion_draft_groups_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_religion_draft_resource_costs_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_religion_draft_tenet_choices_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_religion_hostility_v1",List.of(Field.EXPECTED_REVISION,Field.TARGET_RITE_ID),List.of(Field.EXPECTED_REVISION,Field.TARGET_RITE_ID)),
        new Method("ck3_query_player_religion_numeric_special_parameters_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_religion_personal_parameters_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_religion_reform_context_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_religion_tenets_v1",List.of(Field.EXPECTED_REVISION,Field.TARGET_RITE_ID,Field.TENET_KEY,Field.INCLUDE_KNOWLEDGE_CATALOGUE),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_repentance_context_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_rite_governance_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_rite_members_v1",List.of(Field.EXPECTED_REVISION),List.of(Field.EXPECTED_REVISION)),
        new Method("ck3_query_player_seek_indulgences_terms_v1",List.of(Field.EXPECTED_REVISION,Field.RECIPIENT_CHARACTER_ID),List.of(Field.EXPECTED_REVISION,Field.RECIPIENT_CHARACTER_ID)),
        new Method("ck3_select_holy_site_creation_barony_v1",List.of(Field.BARONY_TITLE_ID,Field.EXPECTED_REVISION),List.of(Field.BARONY_TITLE_ID,Field.EXPECTED_REVISION)),
        new Method("ck3_select_holy_site_creation_type_v1",List.of(Field.TYPE_KEY,Field.EXPECTED_REVISION),List.of(Field.TYPE_KEY,Field.EXPECTED_REVISION)),
        new Method("ck3_submit_county_conversion_task",List.of(Field.EXPECTED_REVISION,Field.EXPECTED_ACTIVE_TASK_ID,Field.EXPECTED_INCUMBENT_CHARACTER_ID,Field.PROVINCE_ID,Field.REPLACE_EXISTING_TASK,Field.ACTION_ID),List.of(Field.EXPECTED_REVISION,Field.EXPECTED_ACTIVE_TASK_ID,Field.EXPECTED_INCUMBENT_CHARACTER_ID,Field.PROVINCE_ID,Field.REPLACE_EXISTING_TASK,Field.ACTION_ID)),
        new Method("ck3_submit_player_pilgrimage_planner_v1",List.of(Field.EXPECTED_REVISION,Field.OPERATION,Field.PROVINCE_ID,Field.POLICY_POSITIVE,Field.RESERVE_GOLD_RAW,Field.RESERVE_TREASURY_RAW,Field.RESERVE_PIETY_RAW,Field.RESERVE_BARTER_GOODS_RAW,Field.OPTION_KEY,Field.TIMEOUT_SECONDS),List.of(Field.EXPECTED_REVISION,Field.OPERATION))
    );
}
