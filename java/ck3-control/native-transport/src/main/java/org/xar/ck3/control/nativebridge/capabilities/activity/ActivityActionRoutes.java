package org.xar.ck3.control.nativebridge.capabilities.activity;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.activity.ActivityConfigurationCodec;
import org.xar.ck3.control.governance.activity.ActivityConfigurationModels.Frame;
import org.xar.ck3.control.governance.activity.ActivityPlannerDiagnostic;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import static org.xar.ck3.control.nativebridge.capabilities.activity.ActivityJson.*;

/** Pure request preparation. Actual submission belongs exclusively to the Root ActionCoordinator. */
public final class ActivityActionRoutes implements ActionPorts.PreparationPort {
    public enum Kind {
        OPEN("open-activity-feast-planner-v1-private","private_activity_feast_planner_open","activity_feast_planner_open"),
        CONFIRM("confirm-activity-feast-stage1-v1-private","private_activity_feast_stage1_confirm","activity_stage1_confirm"),
        DESTINATION("select-activity-feast-stage2-destination-v1-private","private_activity_feast_stage2_destination_select","activity_stage2_destination_select"),
        START("start-activity-feast-stage5-v1-private","allow_private_activity_feast_stage5_start_action","activity_feast_stage5_start"),
        ACTIVATE_RULE("activate-activity-feast-guest-rule-v1","allow_private_activity_feast_guest_rule_action","activity_feast_guest_rule");
        private final String step,permission,payloadKey;
        Kind(String step,String permission,String payloadKey) { this.step=step; this.permission=permission; this.payloadKey=payloadKey; }
        public String step() { return step; }
        public String permissionKey() { return permission; }
        public String payloadKey() { return payloadKey; }
        public static Kind exact(OperationKey operation) { for(Kind kind:values())if(kind.step.equals(operation.value()))return kind; throw new IllegalArgumentException("unregistered Activity mutation"); }
    }
    public record Source(Kind kind,ExactRef producer,NativePrivateActionPermission.QualificationVerifier qualifier) {
        public Source { Objects.requireNonNull(kind); Objects.requireNonNull(producer); Objects.requireNonNull(qualifier); need(producer.bytes()>0,"actual mutation producer source required"); }
    }
    /** Must re-run actual original policy inputs under the same writer Session immediately before INTENT. */
    @FunctionalInterface public interface Admission { void verify(Kind kind,ActionCommand command); }
    private final List<Source> sources;
    private final Admission admission;
    public ActivityActionRoutes(List<Source> sources,Admission admission) {
        this.sources=List.copyOf(sources); this.admission=Objects.requireNonNull(admission);
        need(sources.size()==Kind.values().length && sources.stream().map(Source::kind).distinct().count()==sources.size(),"one source/qualifier per actual Activity mutation");
    }
    public boolean supports(ActionCommand command) { for(Kind kind:Kind.values())if(kind.step().equals(command.operation().value()))return true; return false; }
    public List<NativePrivateActionPermission> privatePermissions() {
        List<NativePrivateActionPermission> result=new ArrayList<>(); for(Source source:sources)result.add(new NativePrivateActionPermission(new OperationKey(source.kind().step()),source.kind().permissionKey(),source.producer(),request->{ try { validateWire(source.kind(),request); } catch(IllegalArgumentException invalid) { throw new IOException("invalid typed Activity native request",invalid); } },source.qualifier())); return List.copyOf(result);
    }
    @Override public NativeRequest prepare(ActionCommand command) {
        Kind kind=Kind.exact(command.operation()); Source source=sources.stream().filter(value->value.kind()==kind).findFirst().orElseThrow(); ActivityNativeContracts.verifySource(source.producer());
        ObjectNode args=argument(command.arguments()); Frame frame=frame(command); sourceFrame(args.get("source_frame"),command); ObjectNode fields;
        if(kind==Kind.START)fields=start(args,frame);
        else {
            allowed(args,"native_arguments planner_observation source_frame activity_phase","stage1_option stage2_option stage2_location hosted_observation campaign_root preflight_read rule_observation"); fields=exact(args.get("native_arguments"),fields(kind));
            String phase=switch(kind) { case OPEN -> "open"; case CONFIRM -> "confirm"; case DESTINATION -> "destination"; case ACTIVATE_RULE -> "rule"; case START -> throw new IllegalStateException(); }; eq(args,"activity_phase",phase);
            var planner=ActivityPlannerDiagnostic.decode(raw(args.get("planner_observation")).bytes(),new ActivityPlannerDiagnostic.Frame(frame.nativeRevision(),frame.dateRaw(),frame.actorId()));
            switch(kind) {
                case OPEN -> need(planner.kind()==ActivityPlannerDiagnostic.Kind.ABSENT,"Open must use an actually absent planner");
                case CONFIRM -> { need(planner.kind()==ActivityPlannerDiagnostic.Kind.FEAST_STAGE_ONE,"Confirm actual planner stage"); need(args.has("stage1_option") && args.get("stage1_option").isObject(),"actual stage one read required"); need(ActivityConfigurationCodec.stageOne(raw(args.get("stage1_option")).bytes(),frame).ready(),"actual native option not Confirm-ready"); }
                case DESTINATION -> { need(planner.kind()==ActivityPlannerDiagnostic.Kind.FEAST_STAGE_TWO,"Destination actual planner stage"); need(args.has("stage2_option") && args.get("stage2_option").isObject() && args.has("stage2_location") && args.get("stage2_location").isObject(),"actual stage two option/location reads required"); ActivityConfigurationCodec.stageTwo(raw(args.get("stage2_option")).bytes(),frame); JsonNode location=args.get("stage2_location"); JsonNode entries=location.get("candidates"); need(entries!=null && entries.isArray(),"actual candidate source required"); List<Integer> candidates=new ArrayList<>(); for(JsonNode row:entries)candidates.add(integer(row,"province_id",1,Integer.MAX_VALUE)); var observed=ActivityConfigurationCodec.location(raw(location).bytes(),frame,candidates); int province=integer(fields,"province_id",1,Integer.MAX_VALUE);
                    need(observed.singleLocation() && observed.previousStage()==1 && observed.activeRowIndex().orElse(-1)==0 && observed.rows().size()==2 && observed.rows().stream().allMatch(row->row.provinceId()==0) && !observed.canProgress() && observed.candidates().stream().anyMatch(row->row.provinceId()==province && row.canSelect()),"destination lacks exact native legal first selection"); }
                case ACTIVATE_RULE -> { need(planner.kind()==ActivityPlannerDiagnostic.Kind.FEAST_STAGE_FIVE,"rule activation planner stage"); need(args.has("rule_observation") && args.get("rule_observation").isObject(),"actual rule observation required"); ActivityPayload.Rule observed=ActivityReadCodec.ruleRead(args.get("rule_observation"),frame,text(fields,"authored_rule_key"),"available",false); need(observed.active().filter(active->!active).isPresent(),"only observed inactive rule may activate"); }
                case START -> throw new IllegalStateException();
            }
        }
        if(kind!=Kind.OPEN)bind(fields,frame); NativeRequest prepared=new NativeRequest(kind.step(),Optional.empty(),raw(fields)); validateWire(kind,prepared); admission.verify(kind,command); return prepared;
    }
    private static ObjectNode start(JsonNode args,Frame frame) {
        exact(args,"inputs assessment source_frame new_attempt"); yes(args,"new_attempt"); ActivityPayload payload=ActivityReadCodec.decode(ActivityNativeContracts.Query.START_INPUTS,raw(args.get("inputs")).bytes(),frame,app(StrictJson.object()),"available",null); ActivityPayload.Inputs input=(ActivityPayload.Inputs)payload;
        need(input.finalCanStart() && input.guestRouteQualified(),"actual Start requires final native legality and guest route"); JsonNode assessment=args.get("assessment"); exact(assessment,"policy decision status reason positive_value_supported benefit_if_successful resource_keys scale configured_cost_raw resource_commitment_raw submit_reserve_raw"); eq(assessment,"policy","g2-feast-stage5-value-policy-v1"); eq(assessment,"decision","start"); eq(assessment,"status","ready"); yes(assessment,"positive_value_supported"); StrictJson.text(assessment.get("reason")); StrictJson.text(assessment.get("benefit_if_successful")); integer(assessment,"scale",100000,100000);
        JsonNode keys=assessment.get("resource_keys"),costs=assessment.get("configured_cost_raw"),commitments=assessment.get("resource_commitment_raw"),reserves=assessment.get("submit_reserve_raw"); need(keys.isArray() && keys.size()==4 && costs.isArray() && costs.size()==4 && commitments.isArray() && commitments.size()==4 && reserves.isArray() && reserves.size()==4,"four exact native Start resources required"); ObjectNode fields=StrictJson.object().put("expected_date_raw",frame.dateRaw()).put("expected_actor_character_id",frame.actorId()).put("expected_activity_key","activity_feast").put("expected_option_key","feast_type_generic").put("expected_planning_stage",5).put("policy_positive",true).put("previous_submit_pending",false);
        for(int index=0;index<4;index++) { ActivityPayload.Resource resource=ActivityPayload.Resource.values()[index]; String key=resource.name().toLowerCase(java.util.Locale.ROOT); need(StrictJson.text(keys.get(index)).equals(key),"Start resource order differs"); BigInteger cost=StrictJson.integer(costs.get(index),BigInteger.ZERO,I64_MAX); need(cost.equals(input.resources().get(index).configuredRaw()),"Start assessment actual native cost differs"); StrictJson.integer(commitments.get(index),BigInteger.ZERO,I64_MAX); fields.put("reserve_"+key+"_raw",StrictJson.integer(reserves.get(index),BigInteger.ZERO,I64_MAX)); }
        return fields;
    }
    private static Frame frame(ActionCommand command) { var identity=command.before().frame().identity(); return new Frame(identity.nativeRevision(),identity.dateRaw(),identity.player()); }
    private static void sourceFrame(JsonNode source,ActionCommand command) { exact(source,"played_character_id native_revision date_raw snapshot_id revision episode_run_id"); var before=command.before().frame(); need(number(source,"played_character_id",BigInteger.ONE,U32).equals(before.identity().player()) && positive(source,"native_revision").equals(before.identity().nativeRevision()) && number(source,"date_raw",BigInteger.ZERO,BigInteger.valueOf(Integer.MAX_VALUE)).equals(before.identity().dateRaw()) && text(source,"snapshot_id").equals(before.snapshotId()) && positive(source,"revision").equals(before.revision()) && text(source,"episode_run_id").equals(before.episodeRunId()),"Activity action source frame differs"); }
    private static void bind(JsonNode fields,Frame frame) { need(number(fields,"expected_date_raw",BigInteger.ZERO,BigInteger.valueOf(Integer.MAX_VALUE)).equals(frame.dateRaw()) && number(fields,"expected_actor_character_id",BigInteger.ONE,U32).equals(frame.actorId()),"Activity native action frame differs"); }
    private static String fields(Kind kind) { return switch(kind) { case OPEN -> ""; case CONFIRM -> "expected_date_raw expected_actor_character_id expected_activity_key expected_option_key"; case DESTINATION -> "expected_date_raw expected_actor_character_id expected_activity_key expected_option_key province_id"; case START -> "expected_date_raw expected_actor_character_id expected_activity_key expected_option_key expected_planning_stage policy_positive previous_submit_pending reserve_gold_raw reserve_treasury_raw reserve_piety_raw reserve_barter_goods_raw"; case ACTIVATE_RULE -> "expected_date_raw expected_actor_character_id expected_activity_key expected_planning_stage authored_rule_key policy_approved"; }; }
    public static void validateWire(Kind kind,NativeRequest request) { need(request.step().equals(kind.step()) && request.requiredCapability().isEmpty(),"private Activity operation/capability differs"); JsonNode fields=parse(request.additionalFields().bytes()); exact(fields,fields(kind)); if(kind==Kind.OPEN)return; number(fields,"expected_date_raw",BigInteger.ZERO,BigInteger.valueOf(Integer.MAX_VALUE)); number(fields,"expected_actor_character_id",BigInteger.ONE,U32); eq(fields,"expected_activity_key","activity_feast"); if(kind!=Kind.ACTIVATE_RULE)eq(fields,"expected_option_key","feast_type_generic"); if(kind==Kind.DESTINATION)integer(fields,"province_id",1,Integer.MAX_VALUE); if(kind==Kind.START || kind==Kind.ACTIVATE_RULE)integer(fields,"expected_planning_stage",5,5); if(kind==Kind.ACTIVATE_RULE) { ActivityJson.rule(text(fields,"authored_rule_key")); yes(fields,"policy_approved"); } if(kind==Kind.START) { yes(fields,"policy_positive"); no(fields,"previous_submit_pending"); for(String resource:List.of("gold","treasury","piety","barter_goods"))number(fields,"reserve_"+resource+"_raw",BigInteger.ZERO,I64_MAX); } }
}
