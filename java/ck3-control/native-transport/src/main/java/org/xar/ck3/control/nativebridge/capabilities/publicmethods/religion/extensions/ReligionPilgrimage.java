package org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions;

import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionTemporalFinance.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionContract;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerReligionContext.Build;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** The finite original pilgrimage planner and hosted-identity contract; absence never means completion. */
public final class ReligionPilgrimage {
    public static final String ACTIVITIES_METHOD="ck3_query_player_pilgrimage_activities_v1",QUERY_METHOD="ck3_query_player_pilgrimage_planner_v1",SUBMIT_METHOD="ck3_submit_player_pilgrimage_planner_v1";
    public static final String ACTIVITIES_STEP="query-player-pilgrimage-activities-v1-private",QUERY_STEP="query-player-pilgrimage-planner-v1-private",SUBMIT_STEP="submit-player-pilgrimage-planner-v1-private";
    public static final String PERMISSION="allow_private_player_pilgrimage_execution",ACTIVITIES_PERMISSION="allow_private_player_pilgrimage_activities_query";
    private static final String ACTIVITY="activity_pilgrimage",PLANNER_SCHEMA="ck3_12004_player_pilgrimage_planner_v1",ACTIVITIES_SCHEMA="ck3_12004_player_pilgrimage_activities_v1";
    private ReligionPilgrimage(){ }
    public enum Operation {
        READ,CAN_SELECT,QUOTE,POST,OPEN,CONFIRM,SELECT,START;
        public String wire(){return name().toLowerCase(Locale.ROOT);}public boolean submit(){return ordinal()>=OPEN.ordinal();}
        public static Operation parse(String text){return Arrays.stream(values()).filter(v->v.wire().equals(text)).findFirst().orElseThrow(()->new IllegalArgumentException("unlisted pilgrimage planner operation"));}
    }
    public enum Option {
        PIOUS("pilgrimage_type_pious"),WORLDLY("pilgrimage_type_worldly"),HAJJ("pilgrimage_type_hajj");
        private final String key;Option(String key){this.key=key;}public String key(){return key;}
        public static Option parse(String key){return Arrays.stream(values()).filter(v->v.key.equals(key)).findFirst().orElseThrow(()->new IllegalArgumentException("unsupported original pilgrimage option"));}
    }
    public record Reserves(BigInteger gold,BigInteger treasury,BigInteger piety,BigInteger barterGoods){
        public Reserves{for(BigInteger value:List.of(gold,treasury,piety,barterGoods))range(value,BigInteger.ZERO,I64_MAX);}
        public static Reserves zero(){return new Reserves(BigInteger.ZERO,BigInteger.ZERO,BigInteger.ZERO,BigInteger.ZERO);}public boolean empty(){return equals(zero());}
        public List<BigInteger> values(){return List.of(gold,treasury,piety,barterGoods);}
    }
    public record Request(Operation operation,BigInteger expectedRevision,BigInteger province,int readStage,Option option,
            boolean policyPositive,Reserves reserves,BigDecimal timeoutSeconds){
        public Request{
            Objects.requireNonNull(operation);Objects.requireNonNull(option);Objects.requireNonNull(reserves);Objects.requireNonNull(timeoutSeconds);range(expectedRevision,BigInteger.ONE,U64);range(province,BigInteger.ZERO,U32.subtract(BigInteger.ONE));
            need(Set.of(Operation.CAN_SELECT,Operation.SELECT,Operation.START).contains(operation)?province.signum()>0:province.signum()==0,"pilgrimage province does not match operation");
            need(readStage>=0&&readStage<=5&&(operation==Operation.READ||readStage==0),"read_stage is only a read-only0..5 filter");
            need(!operation.submit()||policyPositive,"each pilgrimage submit requires policy_positive=true");need(operation==Operation.START||reserves.empty(),"reserves only apply to Start");
            need(timeoutSeconds.signum()>0&&timeoutSeconds.compareTo(BigDecimal.valueOf(120))<=0,"finite positive pilgrimage timeout required");
        }
        public String step(){return operation.submit()?SUBMIT_STEP:QUERY_STEP;}
        public static Request from(ReligionContract.Request request){
            String name=request.method().name();need(name.equals(QUERY_METHOD)||name.equals(SUBMIT_METHOD),"not an original pilgrimage planner request");
            Operation operation=Operation.parse(textArgument(request,ReligionContract.Field.OPERATION,"read"));need(operation.submit()==name.equals(SUBMIT_METHOD),"pilgrimage public query/submit operation differs");
            return new Request(operation,request.expectedRevision(),ReligionCodec.optionalInteger(request,ReligionContract.Field.PROVINCE_ID,BigInteger.ZERO),name.equals(SUBMIT_METHOD)?0:ReligionCodec.optionalInteger(request,ReligionContract.Field.READ_STAGE,BigInteger.ZERO).intValueExact(),Option.parse(textArgument(request,ReligionContract.Field.OPTION_KEY,Option.PIOUS.key())),
                    name.equals(SUBMIT_METHOD)&&booleanArgument(request,ReligionContract.Field.POLICY_POSITIVE,false),name.equals(SUBMIT_METHOD)?new Reserves(ReligionCodec.optionalInteger(request,ReligionContract.Field.RESERVE_GOLD_RAW,BigInteger.ZERO),ReligionCodec.optionalInteger(request,ReligionContract.Field.RESERVE_TREASURY_RAW,BigInteger.ZERO),ReligionCodec.optionalInteger(request,ReligionContract.Field.RESERVE_PIETY_RAW,BigInteger.ZERO),ReligionCodec.optionalInteger(request,ReligionContract.Field.RESERVE_BARTER_GOODS_RAW,BigInteger.ZERO)):Reserves.zero(),decimalArgument(request,ReligionContract.Field.TIMEOUT_SECONDS,BigDecimal.valueOf(30)));
        }
    }
    public record NativeSubmit(Operation operation,BigInteger province,Option option,Reserves reserves,BigInteger expectedDate,BigInteger expectedActor){
        public NativeSubmit{need(operation.submit(),"private mutation needs original submit operation");Objects.requireNonNull(option);Objects.requireNonNull(reserves);range(province,BigInteger.ZERO,U32.subtract(BigInteger.ONE));need(Set.of(Operation.SELECT,Operation.START).contains(operation)?province.signum()>0:province.signum()==0,"private pilgrimage province differs");need(operation==Operation.START||reserves.empty(),"private reserves only apply to Start");range(expectedDate,I32_MIN,I32_MAX);range(expectedActor,BigInteger.ONE,U32.subtract(BigInteger.ONE));}
        public Request at(Frame before){need(before.date().equals(expectedDate)&&before.actor().equals(expectedActor),"private pilgrimage request source frame differs");return new Request(operation,before.publicRevision(),province,0,option,true,reserves,BigDecimal.valueOf(30));}
    }
    public static NativeSubmit validateSubmit(NativeRequest request){need(request.step().equals(SUBMIT_STEP)&&request.requiredCapability().isEmpty(),"fixed private pilgrimage mutation required");var n=obj(request.additionalFields());exact(n,"operation expected_date_raw expected_actor_character_id expected_activity_key expected_option_key province_id read_stage policy_positive reserve_gold_raw reserve_treasury_raw reserve_piety_raw reserve_barter_goods_raw");eq(n,"expected_activity_key",ACTIVITY);eq(n,"read_stage",BigInteger.ZERO);yes(n,"policy_positive");return new NativeSubmit(Operation.parse(text(n,"operation")),integer(n,"province_id",BigInteger.ZERO,U32.subtract(BigInteger.ONE)),Option.parse(text(n,"expected_option_key")),new Reserves(integer(n,"reserve_gold_raw",BigInteger.ZERO,I64_MAX),integer(n,"reserve_treasury_raw",BigInteger.ZERO,I64_MAX),integer(n,"reserve_piety_raw",BigInteger.ZERO,I64_MAX),integer(n,"reserve_barter_goods_raw",BigInteger.ZERO,I64_MAX)),integer(n,"expected_date_raw",I32_MIN,I32_MAX),integer(n,"expected_actor_character_id",BigInteger.ONE,U32.subtract(BigInteger.ONE)));}
    public sealed interface ReadSelection permits Activities,PlannerRead{String step();String permission();BigInteger expectedRevision();}
    public record Activities(BigInteger expectedRevision)implements ReadSelection{
        public Activities{range(expectedRevision,BigInteger.ONE,U64);}public String step(){return ACTIVITIES_STEP;}public String permission(){return ACTIVITIES_PERMISSION;}
    }
    public record PlannerRead(Request request)implements ReadSelection{
        public PlannerRead{Objects.requireNonNull(request);need(!request.operation().submit(),"read cannot submit a pilgrimage operation");}
        public String step(){return QUERY_STEP;}public String permission(){return PERMISSION;}public BigInteger expectedRevision(){return request.expectedRevision();}
    }
    public record Observed(ReadSelection selection,Frame frame,String requestId,String postSnapshotId,RawJson nativeEnvelope,RawJson normalized){
        public Observed{Objects.requireNonNull(selection);Objects.requireNonNull(frame);Objects.requireNonNull(requestId);Objects.requireNonNull(postSnapshotId);Objects.requireNonNull(nativeEnvelope);Objects.requireNonNull(normalized);}
        public ObjectNode publicResult(){ObjectNode value=obj(normalized);value.put("exact_ck3_build",frame.build().version()).put("exe_sha256",frame.build().sha256());metadata(value,frame);value.put("post_snapshot_id",postSnapshotId);if(selection instanceof PlannerRead)value.put("request_id",requestId).put("automatic_retry",false).put("business_outcome_observed",false).put("action_ready",false);publicWidths(value,selection instanceof Activities);return value;}
    }
    private static final String[] RESOURCES={"gold","treasury","piety","barter_goods"};
    public static ReadContract<Observed> contract(ReadSelection selection,Sources sources,Admission admission){
        java.util.function.Function<PlanningReadReceipt,Observed> decode=receipt->decode(receipt,atRevision(selection,receipt.request().before().frame().revision()));
        return new ReadContract<>("religion.extension.pilgrimage."+selection.step()+"."+ActionCodec.sha256(raw(selectionFields(selection)).bytes()),new OperationKey(selection.step()),Optional.empty(),selection.permission(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,sources.definition(),(request,id)->{
            admission.verify(request);
            var scope=request.before();
            ObjectNode fields=fields(selection,scope.frame().identity().nativeRevision(),scope.frame().identity().dateRaw(),scope.frame().identity().player());
            need(request.arguments().equals(OpportunityJson.object(OpportunityJson.parse(raw(selectionFields(selection)).bytes()),"pilgrimage read arguments")),"pilgrimage original request fields changed");return new NativeRequest(selection.step(),Optional.empty(),raw(fields));
        },decode,decode);
    }
    public static ObjectNode fields(ReadSelection selection,BigInteger nativeRevision,BigInteger date,BigInteger actor){
        ObjectNode n=StrictJson.object().put("expected_date_raw",date).put("expected_actor_character_id",actor).put("expected_activity_key",ACTIVITY);
        if(selection instanceof PlannerRead planner)n.put("operation",planner.request().operation().wire()).put("expected_option_key",planner.request().option().key()).put("province_id",planner.request().province()).put("read_stage",planner.request().readStage());return n;
    }
    public static ObjectNode submitFields(Request request,Frame frame){
        need(request.operation().submit()&&frame.build()==Build.CROZIER4&&frame.publicRevision().equals(request.expectedRevision()),"qualified same-frame actual4 pilgrimage submission required");
        ObjectNode n=StrictJson.object().put("operation",request.operation().wire()).put("expected_date_raw",frame.date()).put("expected_actor_character_id",frame.actor()).put("expected_activity_key",ACTIVITY).put("expected_option_key",request.option().key()).put("province_id",request.province()).put("read_stage",0).put("policy_positive",request.policyPositive());
        for(int i=0;i<RESOURCES.length;i++)n.put("reserve_"+RESOURCES[i]+"_raw",request.reserves().values().get(i));return n;
    }
    public static Observed decode(PlanningReadReceipt receipt,ReadSelection selected){
        requireGuards(receipt);Frame frame=Frame.from(receipt);need(frame.build()==Build.CROZIER4&&frame.publicRevision().equals(selected.expectedRevision()),"pilgrimage requires exact actual4 queried frame");
        return normalizeEnvelope(selected,frame,originalResult(receipt),receipt.requestId(),receipt.after().binding().observed().frame().snapshotId());
    }
    public static Observed normalizeEnvelope(ReadSelection selected,Frame frame,ObjectNode original,String requestId,String postSnapshotId){
        need(frame.build()==Build.CROZIER4&&frame.publicRevision().equals(selected.expectedRevision()),"pilgrimage requires exact actual4 queried frame");ObjectNode result=original.deepCopy();String nested=selected instanceof Activities?"player_pilgrimage_activities":"player_pilgrimage_planner";
        envelope(result,selected.step(),nested,false);ObjectNode value=selected instanceof Activities?normalizeActivities(object(result.get(nested)),frame):normalizePlanner(object(result.get(nested)),frame,((PlannerRead)selected).request());
        return new Observed(selected,frame,requestId,postSnapshotId,raw(result),raw(value));
    }
    public static ObjectNode submissionResult(RawJson originalResult,Frame before,Request request){ObjectNode result=obj(originalResult);envelope(result,SUBMIT_STEP,"player_pilgrimage_planner",true);return normalizePlanner(object(result.get("player_pilgrimage_planner")),before,request);}
    public static ObjectNode publicSubmission(RawJson actualEnvelope,Frame before,Request request,String requestId,String postSnapshotId){var value=submissionResult(actualEnvelope,before,request);need(requestId!=null&&!requestId.isEmpty()&&postSnapshotId!=null&&!postSnapshotId.isEmpty(),"actual original request/post snapshot labels required");value.put("exact_ck3_build",before.build().version()).put("exe_sha256",before.build().sha256());metadata(value,before);value.put("request_id",requestId).put("post_snapshot_id",postSnapshotId).put("automatic_retry",false).put("business_outcome_observed",false).put("action_ready",false);publicWidths(value,false);return value;}
    public enum Readback { UI_OBSERVED,START_IDENTITY_OBSERVED,REJECTED,PENDING }
    /** Pure DATA classification used only after Root verifies custody, original read and chronology. */
    public static Readback classifyReadback(RawJson actualSubmit,Frame before,Request request,Observed independent){
        Frame after=independent.frame();need(independent.selection() instanceof PlannerRead,"independent pilgrimage planner result required");
        var selected=((PlannerRead)independent.selection()).request();need(selected.operation()==(request.operation()==Operation.START?Operation.POST:Operation.READ)&&selected.option()==request.option(),"independent pilgrimage operation/option differs");
        need(after.actor().equals(before.actor())&&after.date().equals(before.date())&&after.pid()==before.pid()&&after.generation().equals(before.generation())&&after.episode().equals(before.episode())&&after.nativeRevision().compareTo(before.nativeRevision())>=0&&after.publicRevision().compareTo(before.publicRevision())>=0,"pilgrimage independent source frame differs or regressed");
        var submitted=submissionResult(actualSubmit,before,request);var post=obj(independent.normalized());
        if(text(submitted,"operation_status").equals("rejected")&&!bool(submitted,"invoked")&&!bool(submitted,"needs_recovery"))return Readback.REJECTED;
        if(bool(submitted,"needs_recovery"))return Readback.PENDING;
        if(request.operation()==Operation.START)return bool(submitted,"invoked")&&text(post,"ledger_state").equals("identity_observed")&&text(post,"operation_status").equals("identity_observed")&&post.hasNonNull("new_identity")?Readback.START_IDENTITY_OBSERVED:Readback.PENDING;
        if(text(submitted,"operation_status").equals("observed")&&text(post,"operation_status").equals("observed")&&post.hasNonNull("planner")&&post.get("planner").equals(submitted.get("planner"))&&object(post.get("planner")).hasNonNull("selected_option_key")&&text(object(post.get("planner")),"selected_option_key").equals(request.option().key())){
            if(request.operation()!=Operation.SELECT||object(post.get("planner")).hasNonNull("destination_province_id")&&integer(object(post.get("planner")),"destination_province_id",BigInteger.ZERO,U32).equals(request.province()))return Readback.UI_OBSERVED;
        }
        return Readback.PENDING;
    }
    private static void envelope(ObjectNode result,String step,String nested,boolean submit){exact(result,"step accepted status private_build read_only advertised "+nested+" backend_id");eq(result,"step",step);yes(result,"accepted");eq(result,"status","available");yes(result,"private_build");need(bool(result,"read_only")==!submit,"pilgrimage envelope read_only differs");no(result,"advertised");eq(result,"backend_id","native-headless");}
    public static ObjectNode normalizeActivities(ObjectNode original,Frame f){
        need(f.build()==Build.CROZIER4,"pilgrimage requires exact actual4");ObjectNode n=original.deepCopy();exact(n,"schema read_only snapshot_revision date_raw played_character_id scope activity_type_key activity_count activities absence_is_completion raw_pointer_fields_persisted");eq(n,"schema",ACTIVITIES_SCHEMA);yes(n,"read_only");scope(n,f,"played_character_id");eq(n,"scope","currently-hosted-by-current-player");eq(n,"activity_type_key",ACTIVITY);no(n,"absence_is_completion");no(n,"raw_pointer_fields_persisted");JsonNode rows=field(n,"activities");need(rows.isArray()&&rows.size()<=64&&integer(n,"activity_count",BigInteger.ZERO,BigInteger.valueOf(64)).equals(BigInteger.valueOf(rows.size())),"pilgrimage activities/count malformed");var seen=new HashSet<BigInteger>();for(JsonNode row:rows){ObjectNode activity=object(row);activity(activity,f);need(seen.add(integer(activity,"activity_id",BigInteger.ZERO,U32.subtract(BigInteger.ONE))),"duplicate hosted pilgrimage identity");}return n;
    }
    private static void activity(ObjectNode n,Frame f){
        exact(n,"activity_id host_character_id type_key terminal_flags_observed native_completed native_invalidated native_completion_stamp_observed native_completion_stamp_raw");integer(n,"activity_id",BigInteger.ZERO,U32.subtract(BigInteger.ONE));eq(n,"host_character_id",f.actor());eq(n,"type_key",ACTIVITY);boolean flags=bool(n,"terminal_flags_observed");for(String key:List.of("native_completed","native_invalidated")){if(flags)bool(n,key);else need(field(n,key).isNull(),"unobserved pilgrimage terminal flag must remain null");}if(bool(n,"native_completion_stamp_observed"))integer(n,"native_completion_stamp_raw",BigInteger.ZERO,U64);else need(field(n,"native_completion_stamp_raw").isNull(),"unobserved pilgrimage completion stamp must remain null");
    }
    public static ObjectNode normalizePlanner(ObjectNode original,Frame f,Request request){
        need(f.build()==Build.CROZIER4,"pilgrimage requires exact actual4");ObjectNode n=original.deepCopy();exact(n,"schema read_only snapshot_revision date_raw played_character_id activity_type_key special_option_key operation operation_status invoked needs_recovery ledger_state failure planner quote new_identity absence_is_completion raw_pointer_fields_persisted");eq(n,"schema",PLANNER_SCHEMA);need(bool(n,"read_only")==!request.operation().submit(),"pilgrimage body read_only differs");scope(n,f,"played_character_id");eq(n,"activity_type_key",ACTIVITY);eq(n,"special_option_key",request.option().key());eq(n,"operation",request.operation().wire());
        need(Set.of("observed","rejected","submitted_pending","submission_outcome_unknown","needs_recovery","unavailable","identity_observed","post_pending","ambiguous").contains(text(n,"operation_status")),"pilgrimage operation_status malformed");need(Set.of("idle","submitted_pending","submission_outcome_unknown","identity_observed").contains(text(n,"ledger_state")),"pilgrimage ledger_state malformed");no(n,"absence_is_completion");no(n,"raw_pointer_fields_persisted");bool(n,"invoked");bool(n,"needs_recovery");need(request.operation().submit()||!bool(n,"invoked"),"read-only pilgrimage reports invocation");String failure=text(n,"failure");need(failure.codePointCount(0,failure.length())<=4096,"pilgrimage failure exceeds4096codepoints");
        if(!n.get("planner").isNull())plannerState(object(n.get("planner")));if(!n.get("quote").isNull())normalizeQuote(object(n.get("quote")),f,request.option());if(!n.get("new_identity").isNull())activity(object(n.get("new_identity")),f);return n;
    }
    private static void plannerState(ObjectNode n){exact(n,"stage selected_option_key destination_province_id can_select can_progress");integer(n,"stage",BigInteger.ZERO,BigInteger.valueOf(5));if(!n.get("selected_option_key").isNull())Option.parse(text(n,"selected_option_key"));if(!n.get("destination_province_id").isNull())integer(n,"destination_province_id",BigInteger.ZERO,U32.subtract(BigInteger.ONE));for(String key:List.of("can_select","can_progress"))if(!n.get(key).isNull())bool(n,key);}
    public static ObjectNode normalizeQuote(ObjectNode original,Frame f,Option option){
        ObjectNode n=original.deepCopy();exact(n,"schema activity_key special_option_key observed read_only raw_pointer_fields_persisted snapshot_revision date_raw actor_character_id application_main_thread paused map_ready actor_alive planning_stage scale normal_refresh_sequence configuration_fingerprint selected_option known_cost_names known_name_resource_indices configured_cost_raw diagnostic_aggregate_raw named_cost_verified unknown_positive_configured_cost final_can_start_observed final_can_start failure_display_known failure_display failure_display_unknown_reason");eq(n,"schema","activity-pilgrimage-configured-full10-cost-v1");eq(n,"activity_key",ACTIVITY);eq(n,"special_option_key",option.key());scope(n,f,"actor_character_id");
        for(String key:List.of("observed","read_only","application_main_thread","paused","map_ready","actor_alive","final_can_start_observed"))yes(n,key);for(String key:List.of("raw_pointer_fields_persisted","failure_display_known"))no(n,key);need(n.get("failure_display").isNull(),"pilgrimage quote invents failure display");eq(n,"failure_display_unknown_reason","final_canstart_tooltip_getter_unbound");eq(n,"planning_stage",BigInteger.valueOf(5));eq(n,"scale",BigInteger.valueOf(100000));integer(n,"normal_refresh_sequence",BigInteger.ONE,U64);integer(n,"configuration_fingerprint",BigInteger.ZERO,U64);bool(n,"final_can_start");
        var selected=object(n.get("selected_option"));exact(selected,"native_option_id key");integer(selected,"native_option_id",BigInteger.ZERO,U32.subtract(BigInteger.ONE));eq(selected,"key",option.key());JsonNode names=field(n,"known_cost_names");need(names.isArray()&&names.size()==4,"pilgrimage cost names malformed");for(int i=0;i<4;i++)need(names.get(i).isTextual()&&names.get(i).textValue().equals(RESOURCES[i]),"pilgrimage cost names changed");
        JsonNode indices=field(n,"known_name_resource_indices");need(indices.isArray()&&indices.size()==4,"pilgrimage cost indices malformed");var known=new HashSet<Integer>();for(JsonNode index:indices){need(index.isIntegralNumber(),"pilgrimage cost index must be integer");known.add(range(index.bigIntegerValue(),BigInteger.ZERO,BigInteger.valueOf(9)).intValueExact());}need(known.size()==4,"pilgrimage duplicate resource indices");
        for(String key:List.of("configured_cost_raw","diagnostic_aggregate_raw")){var vector=field(n,key);need(vector.isArray()&&vector.size()==10,"pilgrimage requires full10 resource vector");for(JsonNode raw:vector){need(raw.isIntegralNumber(),"pilgrimage resource cost must be integer");range(raw.bigIntegerValue(),I64_MIN,I64_MAX);}}
        var mask=field(n,"named_cost_verified");need(mask.isArray()&&mask.size()==10,"pilgrimage resource verification mask malformed");boolean unknown=false;for(int i=0;i<10;i++){need(mask.get(i).isBoolean()&&mask.get(i).booleanValue()==known.contains(i),"pilgrimage resource mask disagrees with dynamic indices");if(!known.contains(i)&&n.get("configured_cost_raw").get(i).bigIntegerValue().signum()>0)unknown=true;}need(bool(n,"unknown_positive_configured_cost")==unknown,"pilgrimage unknown-positive cost flag differs");return n;
    }
    private static void scope(ObjectNode n,Frame f,String actor){eq(n,"snapshot_revision",f.nativeRevision());eq(n,"date_raw",f.date());eq(n,actor,f.actor());}
    public static ObjectNode selectionFields(ReadSelection selection){ObjectNode n=StrictJson.object();if(selection instanceof PlannerRead p){n.put("operation",p.request().operation().wire()).put("province_id",p.request().province()).put("read_stage",p.request().readStage()).put("option_key",p.request().option().key());}return n;}
    /** Reuse only the installed contract recipe; each real read still binds and sends its new original guarded frame. */
    private static ReadSelection atRevision(ReadSelection selection,BigInteger revision){if(selection instanceof Activities)return new Activities(revision);var r=((PlannerRead)selection).request();return new PlannerRead(new Request(r.operation(),revision,r.province(),r.readStage(),r.option(),false,Reserves.zero(),r.timeoutSeconds()));}
    public static void publicWidths(ObjectNode n,boolean activities){u64(n,"snapshot_revision",1);if(activities){for(JsonNode row:field(n,"activities"))activityWidths(object(row));return;}if(n.hasNonNull("new_identity"))activityWidths(object(n.get("new_identity")));if(n.hasNonNull("quote")){var quote=object(n.get("quote"));u64(quote,"snapshot_revision",1);u64(quote,"normal_refresh_sequence",1);u64(quote,"configuration_fingerprint",0);for(String key:List.of("configured_cost_raw","diagnostic_aggregate_raw")){var values=quote.putArray(key+"_temporary");for(JsonNode cost:field(quote,key)){need(cost.isIntegralNumber(),"native cost integer required");values.add(range(cost.bigIntegerValue(),I64_MIN,I64_MAX).toString());}quote.set(key,values);quote.remove(key+"_temporary");}}}
    private static void activityWidths(ObjectNode n){if(bool(n,"native_completion_stamp_observed"))u64(n,"native_completion_stamp_raw",0);}
    private static String textArgument(ReligionContract.Request request,ReligionContract.Field field,String fallback){var value=request.value(field);return value instanceof ReligionContract.TextValue text?text.value():fallback;}
    private static boolean booleanArgument(ReligionContract.Request request,ReligionContract.Field field,boolean fallback){var value=request.value(field);return value instanceof ReligionContract.BooleanValue flag?flag.value():fallback;}
    private static BigDecimal decimalArgument(ReligionContract.Request request,ReligionContract.Field field,BigDecimal fallback){var value=request.value(field);return value instanceof ReligionContract.DecimalValue decimal?decimal.value():fallback;}
}
