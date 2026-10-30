package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.wave2.finance.giftpending.GiftColdRecovery;
import org.xar.ck3.control.wave2.finance.giftpending.GiftColdRecoveryCodec;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.PendingAction;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel;

/** The existing independent faction/recipient/wallet read, never a submit or a targeting-vector fallback. */
public final class GiftColdReadService {
    public static final OperationKey OPERATION=new OperationKey("private-query-faction-gift-cold-recovery-v1");
    private static final String CONTRACT="ordinary-finance-gift-cold-read/v1";
    private static final String EXE="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    private static final Set<String> ARGUMENTS=Set.of("source_faction_id","recipient_character_id");
    private static final BigInteger UINT32=new BigInteger("4294967295"),UINT64=new BigInteger("18446744073709551615");
    private static final Set<String> POST_FIELDS=Set.of("available","paused","snapshot_revision","native_snapshot_revision",
            "observed_date_raw","date_raw","player_resources_query_complete","player_character_id","player_gold_raw","player_gold_scale",
            "source_faction_requery_complete","queried_source_faction_id","source_faction_present","source_faction_target_character_id",
            "source_faction_targeting_player","source_faction_at_war","source_faction_metrics_available","source_faction_power_raw",
            "source_faction_discontent_raw","source_faction_metric_scale","recipient_identity_resolved","recipient_character_id",
            "recipient_alive","recipient_is_ai","recipient_is_direct_landed_vassal","recipient_opinion_query_complete",
            "recipient_opinion_of_player","gift_opinion_present","gift_opinion_modifier_value","source_faction_leader_character_id",
            "source_faction_member_character_ids","gift_preview");
    private final ReadContract<Observation> contract;
    public GiftColdReadService(FinanceReadContracts.Registration actual) {
        Objects.requireNonNull(actual);var permission=actual.permission();
        require(permission.mode()==ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE
                &&permission.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP&&permission.capability().isEmpty(),
                "cold Gift uses the exact existing source-qualified private execute-step route");
        contract=new ReadContract<>(CONTRACT,OPERATION,permission.capability(),permission.permissionKey(),permission.mode(),
                permission.wireProfile(),ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,actual.definitionSource(),
                (request,id)->{
                    ids(request.arguments());
                    Obj fields=request.arguments().with("expected_date_raw",new IntegerValue(request.before().frame().identity().dateRaw()))
                            .with("expected_player_character_id",new IntegerValue(GiftPendingModel.rawCharacterIdFromPublic(request.before().frame().identity().player())));
                    return new NativeRequest(OPERATION.value(),permission.capability(),new RawJson(encode(fields)));
                },GiftColdReadService::decode,GiftColdReadService::decode,GiftColdReadService::requireReuse);
    }
    /** Business DATA opt-in; only the sole publisher may prove actual READ-only ancestry. */
    private static void requireReuse(PlanningReadReceipt original,Observation decoded,PlanningReadRequest current,Obj semantic) {
        require(decoded.receipt().equals(original)&&CONTRACT.equals(original.contractId())
                &&original.request().operation().equals(OPERATION)&&current.operation().equals(OPERATION)
                &&original.request().arguments().equals(current.arguments()),"cold Gift canonical reuse changed the actual pair request");
        ids(current.arguments());
        var before=original.request().before();var after=current.before();
        var old=before.frame();var fresh=after.frame();
        require(original.request().source().equals(current.source())&&original.request().sessionId().equals(current.sessionId())
                &&before.machineId().equals(after.machineId())&&before.game().equals(after.game())
                &&before.observationVersion()==after.observationVersion()&&old.snapshotId().equals(fresh.snapshotId())
                &&old.episodeRunId().equals(fresh.episodeRunId())&&old.identity().equals(fresh.identity())
                &&java.time.Instant.now().isBefore(current.deadline()),"cold Gift reuse crossed actual native/Game/source/session/deadline");
        require(new Text(fresh.snapshotId()).equals(semantic.get("snapshot_id"))
                &&new IntegerValue(fresh.revision()).equals(semantic.get("revision"))
                &&new Text(fresh.episodeRunId()).equals(semantic.get("episode_run_id"))
                &&new IntegerValue(fresh.identity().nativeRevision()).equals(semantic.get("native_revision"))
                &&new IntegerValue(fresh.identity().dateRaw()).equals(semantic.get("date_raw"))
                &&new IntegerValue(fresh.identity().player()).equals(object(semantic.get("played_character"),"actual current Gift player").get("character_id")),
                "cold Gift reuse lacks complete actual current SEM identity");
        require(decode(original).originalResult().equals(decoded.originalResult()),"cold Gift owning original packet replay changed");
    }
    public ReadContract<Observation> contract() { return contract; }
    public PlanningReadRequest request(PlanningRequest current,PendingAction pending) {
        require(current.before().frame().episodeRunId().equals(pending.episodeRunId())
                &&GiftPendingModel.rawCharacterIdFromPublic(current.before().frame().identity().player()).equals(pending.baseline().playerCharacterId()),
                "cold read cannot move an old Gift to another episode or actor");
        return new PlanningReadRequest(current.before(),current.source(),current.sessionId(),OPERATION,
                obj("source_faction_id",new IntegerValue(pending.baseline().sourceFactionId()),
                    "recipient_character_id",new IntegerValue(pending.baseline().recipientCharacterId())),current.deadline());
    }
    public static final class Observation {
        private final PlanningReadReceipt receipt;private final Obj originalResult,post;
        private final GiftColdRecovery.PostObservation material;
        private Observation(PlanningReadReceipt receipt,Obj originalResult,Obj post,GiftColdRecovery.PostObservation material) {
            this.receipt=receipt;this.originalResult=originalResult;this.post=post;this.material=material;
        }
        public PlanningReadReceipt receipt() { return receipt; }
        public Obj originalResult() { return originalResult; }
        public Obj originalPost() { return post; }
        public GiftColdRecovery.PostObservation material() { return material; }
    }
    private static Observation decode(PlanningReadReceipt receipt) {
        require(receipt.contractId().equals(CONTRACT)&&receipt.request().operation().equals(OPERATION),"exact cold read contract required");
        ids(receipt.request().arguments());
        byte[] packet=receipt.original().originalPacket(),raw=receipt.original().originalFrame().bytes();
        require(receipt.original().nativeOk()&&receipt.original().requestId().equals(receipt.requestId())&&packet.length>=5
                &&ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt()==packet.length-4
                &&Arrays.equals(Arrays.copyOfRange(packet,4,packet.length),raw),"original cold Gift packet/frame/request changed");
        Obj frame=DriverJson.object(raw,RawJson.MAXIMUM_BYTES);
        require(new Text("command_result").equals(frame.get("type"))&&new IntegerValue(BigInteger.ONE).equals(frame.get("protocol_version"))
                &&new Text(receipt.requestId()).equals(frame.get("request_id"))&&new Bool(true).equals(frame.get("ok")),"cold Gift command-result envelope changed");
        Obj result=object(frame.get("result"),"actual cold Gift result");
        require(receipt.original().originalResultToken().isPresent()
                &&DriverJson.object(receipt.original().originalResultToken().orElseThrow().bytes(),RawJson.MAXIMUM_BYTES).equals(result),
                "cold Gift result token differs from the original full packet");
        Validated validated=validateResult(result,receipt.request().arguments(),receipt.request().before());
        return new Observation(receipt,result,validated.post(),validated.material());
    }
    /** Sole owning schema for archived history DATA; this grants no archive, source or live-frame authority. */
    public static Obj requireHistoryResult(Obj result,Obj arguments,ObservationIdentity originalFrame) {
        return validateResult(result,arguments,originalFrame).result();
    }
    private record Validated(Obj result,Obj post,GiftColdRecovery.PostObservation material) { }
    private static Validated validateResult(Obj result,Obj arguments,ObservationIdentity originalFrame) {
        Objects.requireNonNull(result);Objects.requireNonNull(originalFrame);ids(arguments);
        var identity=originalFrame.frame().identity();
        require(result.members().keySet().equals(Set.of("step","accepted","private_build","advertised","status","native","receipt"))
                &&new Text(OPERATION.value()).equals(result.get("step"))&&new Bool(true).equals(result.get("accepted"))
                &&new Bool(true).equals(result.get("private_build"))&&new Bool(false).equals(result.get("advertised"))
                &&new Text("independent_read_complete").equals(result.get("status"))&&result.get("receipt")==Nil.INSTANCE,
                "actual independent cold Gift result required; ACK cannot supply wallet facts");
        Obj nativeResult=object(result.get("native"),"actual independent native Gift result");
        require(new IntegerValue(BigInteger.ONE).equals(nativeResult.get("schema_version"))&&new Bool(true).equals(nativeResult.get("private"))
                &&new Text("1.20.0.4").equals(nativeResult.get("game_version"))
                &&EXE.equalsIgnoreCase(text(nativeResult.get("executable_sha256"),"actual native build"))
                &&new Text("ck3-1.20.0.4-private-faction-gift-mitigation-action-v1").equals(nativeResult.get("backend_id"))
                &&new Text("exact_build_private_action_source_static_ready_live_pending").equals(nativeResult.get("contract_stage"))
                &&new IntegerValue(BigInteger.ZERO).equals(nativeResult.get("failure_flags"))
                &&new Text("none").equals(nativeResult.get("frame_failure_stage"))
                &&new Text("none").equals(nativeResult.get("direct_source_failure"))
                &&new Arr(List.of()).equals(nativeResult.get("typed_reds"))
                &&new Bool(false).equals(nativeResult.get("receipt_pending"))&&nativeResult.get("ack")==Nil.INSTANCE
                &&nativeResult.get("preflight")==Nil.INSTANCE&&new IntegerValue(BigInteger.ONE).equals(nativeResult.get("executor_invocations")),
                "cold Gift exact native build/source completed without failure required");
        Obj post=object(nativeResult.get("observation"),"actual independent Gift post observation");
        validatePost(post);
        require(arguments.get("source_faction_id").equals(nativeResult.get("source_faction_id"))
                &&arguments.get("recipient_character_id").equals(nativeResult.get("recipient_character_id"))
                &&arguments.get("source_faction_id").equals(post.get("queried_source_faction_id"))
                &&arguments.get("recipient_character_id").equals(post.get("recipient_character_id")),"cold Gift queried a different original faction or recipient");
        require(new Bool(true).equals(post.get("available"))&&new Bool(true).equals(post.get("paused"))
                &&new IntegerValue(identity.nativeRevision()).equals(post.get("snapshot_revision"))
                &&new IntegerValue(identity.dateRaw()).equals(post.get("date_raw"))
                &&new IntegerValue(identity.dateRaw()).equals(post.get("observed_date_raw"))
                &&new IntegerValue(GiftPendingModel.rawCharacterIdFromPublic(identity.player())).equals(post.get("player_character_id"))
                &&new IntegerValue(identity.nativeRevision()).equals(post.get("native_snapshot_revision"))
                &&new IntegerValue(BigInteger.valueOf(100000)).equals(post.get("player_gold_scale")),
                "cold Gift post observation is outside the actual held paused frame");
        boundedInteger(post.get("player_gold_raw"),BigInteger.valueOf(Long.MIN_VALUE),BigInteger.valueOf(Long.MAX_VALUE),"native wallet");
        boundedInteger(post.get("recipient_opinion_of_player"),BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE),"native recipient opinion");
        if(new Bool(true).equals(post.get("source_faction_present"))&&new Bool(true).equals(post.get("source_faction_metrics_available")))
            require(new IntegerValue(BigInteger.valueOf(100000)).equals(post.get("source_faction_metric_scale")),"native faction metric denomination changed");
        GiftColdRecovery.Recovery projected=GiftColdRecoveryCodec.decodeRecovery(encode(obj("post_observation",post)));
        return new Validated(result,post,projected.postObservation().value());
    }
    /** Exact SerializeObservation ABI of the pinned .4 producer, before any optional classifier projection. */
    private static void validatePost(Obj post) {
        require(post.members().keySet().equals(POST_FIELDS),"cold Gift requires every actual native observation field exactly once");
        for(String field:List.of("available","paused","player_resources_query_complete","source_faction_requery_complete",
                "source_faction_present","source_faction_targeting_player","source_faction_at_war","source_faction_metrics_available",
                "recipient_identity_resolved","recipient_alive","recipient_is_ai","recipient_is_direct_landed_vassal",
                "recipient_opinion_query_complete","gift_opinion_present"))
            require(post.get(field) instanceof Bool,"actual native Gift boolean required: "+field);
        for(String field:List.of("snapshot_revision","native_snapshot_revision"))boundedInteger(post.get(field),BigInteger.ONE,UINT64,field);
        for(String field:List.of("observed_date_raw","date_raw","recipient_opinion_of_player"))
            boundedInteger(post.get(field),BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE),field);
        for(String field:List.of("player_gold_scale","source_faction_metric_scale"))boundedInteger(post.get(field),BigInteger.ZERO,UINT32,field);
        GiftPendingModel.rawSourceFactionId(integer(post.get("queried_source_faction_id"),"queried_source_faction_id"));
        for(String field:List.of("player_character_id","source_faction_target_character_id","recipient_character_id"))
            GiftPendingModel.rawCharacterId(integer(post.get(field),field));
        for(String field:List.of("player_gold_raw","source_faction_power_raw","source_faction_discontent_raw"))
            boundedInteger(post.get(field),BigInteger.valueOf(Long.MIN_VALUE),BigInteger.valueOf(Long.MAX_VALUE),field);
        if(post.get("gift_opinion_modifier_value")!=Nil.INSTANCE)
            boundedInteger(post.get("gift_opinion_modifier_value"),BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE),"gift_opinion_modifier_value");
        if(post.get("source_faction_leader_character_id")!=Nil.INSTANCE)
            GiftPendingModel.rawCharacterId(integer(post.get("source_faction_leader_character_id"),"source_faction_leader_character_id"));
        require(post.get("source_faction_member_character_ids") instanceof Arr,"actual native Gift member array required");
        GiftPendingModel.rawMemberCharacterIds(((Arr)post.get("source_faction_member_character_ids")).items().stream()
                .map(id->integer(id,"source_faction_member_character_ids[]")).toList());
        Obj preview=object(post.get("gift_preview"),"actual native Gift preview");
        require(preview.members().keySet().equals(Set.of("available","definition_key","definition_stable_hash","interaction_legal","auto_accept",
                "gold_cost_raw","gold_scale","opinion_delta")),"cold Gift preview fields differ from the actual native producer");
        for(String field:List.of("available","interaction_legal","auto_accept"))require(preview.get(field) instanceof Bool,"actual native Gift preview boolean required: "+field);
        require(preview.get("definition_key") instanceof Text,"actual native Gift preview definition string required");
        boundedInteger(preview.get("definition_stable_hash"),BigInteger.ZERO,UINT64,"definition_stable_hash");
        boundedInteger(preview.get("gold_cost_raw"),BigInteger.valueOf(Long.MIN_VALUE),BigInteger.valueOf(Long.MAX_VALUE),"gold_cost_raw");
        boundedInteger(preview.get("gold_scale"),BigInteger.ZERO,UINT32,"gold_scale");
        boundedInteger(preview.get("opinion_delta"),BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE),"opinion_delta");
    }
    private static void boundedInteger(Value value,BigInteger minimum,BigInteger maximum,String field) {
        BigInteger number=integer(value,field);require(number.compareTo(minimum)>=0&&number.compareTo(maximum)<=0,"native Gift integer outside its source ABI: "+field);
    }
    private static void ids(Obj arguments) {
        require(arguments.members().keySet().equals(ARGUMENTS),"exact original faction/recipient read arguments required");
        GiftPendingModel.rawSourceFactionId(integer(arguments.get("source_faction_id"),"source_faction_id"));
        GiftPendingModel.rawCharacterId(integer(arguments.get("recipient_character_id"),"recipient_character_id"));
    }
}
