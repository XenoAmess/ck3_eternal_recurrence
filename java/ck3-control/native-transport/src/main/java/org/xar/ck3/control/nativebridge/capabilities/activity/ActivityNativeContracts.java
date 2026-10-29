package org.xar.ck3.control.nativebridge.capabilities.activity;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.BiFunction;
import java.util.function.Function;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.OriginalReadDecodeFailure;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.activity.ActivityConfigurationModels.Frame;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.wave2.finance.feastterminal.CompletionCallJournal;
import static org.xar.ck3.control.nativebridge.capabilities.activity.ActivityJson.*;

/** Actual private routes, all serialized through the Root's one held planning read coordinator. */
public final class ActivityNativeContracts {
    private ActivityNativeContracts() { }
    public enum Query {
        DIAGNOSTIC("query-activity-planner-diag-v1-private","activity_planner_diag","allow_private_activity_planner_diag_query"),
        STAGE1_OPTION("query-activity-stage1-option-v1-private","activity_stage1_option","private_activity_feast_stage1_option_read"),
        STAGE2_OPTION("query-activity-feast-stage2-option-v1-private","activity_stage2_option","private_activity_feast_stage2_option_read"),
        STAGE2_GATE("query-activity-feast-stage2-gate-v1-private","activity_stage2_gate","private_activity_feast_stage2_gate_read"),
        STAGE2_LOCATION("query-activity-feast-stage2-location-v1-private","activity_stage2_location","private_activity_feast_stage2_location_read"),
        GOLD("query-activity-stage5-gold-cost-v1-private","activity_stage5_gold_cost","allow_private_activity_stage5_gold_query"),
        FULL_COST("query-activity-stage5-feast-full-cost-v1-private","activity_stage5_feast_full_cost","allow_private_activity_stage5_feast_full_cost_query"),
        START_INPUTS("query-activity-feast-stage5-start-inputs-v1-private","activity_feast_stage5_start_inputs","allow_private_activity_feast_stage5_start_query"),
        HOSTED("query-activity-feast-hosted-post-v1-private","activity_feast_hosted_post","allow_private_activity_feast_stage5_start_query"),
        GUEST_CANDIDATE("query-activity-feast-guest-candidate-v1","activity_feast_guest_candidate","allow_private_activity_feast_guest_candidate_query"),
        GUEST_OPINION("query-activity-feast-guest-opinion-v1","activity_feast_guest_opinion","allow_private_activity_feast_guest_opinion_query"),
        GUEST_TARGET("query-activity-feast-stage5-guest-target-v1-private","activity_feast_guest_target","allow_private_activity_feast_guest_target_query"),
        GUEST_ROUTE_PROOF("query-activity-feast-stage5-guest-route-proof-v1-private","activity_feast_guest_route_proof","allow_private_activity_feast_guest_route_proof_query"),
        GUEST_RULE("query-activity-feast-guest-rule-v1","activity_feast_guest_rule","allow_private_activity_feast_guest_rule_query"),
        GUEST_RULE_PROVENANCE("query-activity-feast-guest-rule-provenance-v1","activity_feast_guest_rule_provenance","allow_private_activity_feast_guest_rule_provenance_query");
        private final String step,payloadKey,permission;
        Query(String step,String payloadKey,String permission) { this.step=step; this.payloadKey=payloadKey; this.permission=permission; }
        public String step() { return step; }
        public String payloadKey() { return payloadKey; }
        public String permissionKey() { return permission; }
        public OperationKey operation() { return new OperationKey(step); }
    }
    public record Source(Query query,ExactRef producer) { public Source { Objects.requireNonNull(query); Objects.requireNonNull(producer); need(producer.bytes()>0,"actual activity producer source required"); } }
    /** Root checks exact build, this source's actual installed permission and fresh same-session readiness. */
    @FunctionalInterface public interface Admission { void verify(Query query,PlanningReadRequest request); }
    public static final class Packet {
        private final PlanningReadReceipt receipt;
        private final Obj result;
        private final ActivityPayload payload;
        private Packet(PlanningReadReceipt receipt,Obj result,ActivityPayload payload) { this.receipt=receipt; this.result=result; this.payload=payload; }
        public PlanningReadReceipt receipt() { return receipt; }
        public Obj result() { return result; }
        public ActivityPayload payload() { return payload; }
        /** Complete retained value comparison for the actual archive/replay consumer; no source qualification is granted. */
        @Override public boolean equals(Object other) {
            return other instanceof Packet value&&receipt.equals(value.receipt)&&result.equals(value.result)&&payload.equals(value.payload);
        }
        @Override public int hashCode() {return Objects.hash(receipt,result,payload);}
    }
    public static final class Installation {
        private final EnumMap<Query,ReadContract<Packet>> installed=new EnumMap<>(Query.class);
        public Installation(List<Source> sources,Admission admission) {
            Objects.requireNonNull(admission); sources=List.copyOf(sources); need(sources.size()==Query.values().length && sources.stream().map(Source::query).distinct().count()==sources.size(),"one exact producer source per Activity query required");
            for(Source source:sources) {
                Query query=source.query();
                BiFunction<PlanningReadRequest,String,NativeRequest> prepare=(request,requestId)->{
                    verifySource(source.producer());admission.verify(query,request);
                    return new NativeRequest(query.step(),Optional.empty(),requestFields(query,request));
                };
                Function<PlanningReadReceipt,Packet> decoder=receipt->decodeLive(query,receipt);
                Function<PlanningReadReceipt,Packet> archived=receipt->decode(query,receipt);
                String id="activity/native/"+query.name().toLowerCase(java.util.Locale.ROOT);
                // NEXT reads the retained HOSTED original through this identical installed contract.
                // The archival decoder reads its actual original Hello/result; it never prepares or dispatches a query.
                ReadContract<Packet> contract=query==Query.HOSTED
                    ?new ReadContract<>(id,query.operation(),Optional.empty(),query.permissionKey(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                        ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source.producer(),prepare,decoder,archived)
                    :new ReadContract<>(id,query.operation(),Optional.empty(),query.permissionKey(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                        ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source.producer(),prepare,decoder);
                installed.put(query,contract);
            }
        }
        public ReadContract<Packet> contract(Query query) { return Objects.requireNonNull(installed.get(Objects.requireNonNull(query))); }
        private Packet decodeLive(Query query,PlanningReadReceipt original) {
            try{return decode(query,original);}
            catch(ActivityReadCodec.MalformedPayload malformed){throw new LivePayloadFailure(this,query,contract(query),original,malformed);}
        }
        public List<ReadContract<?>> contracts() { return List.copyOf(installed.values()); }
        public PlanningReadResult<Packet> read(Query query,PlanningReadPort reads,PlanningRequest request,Obj arguments) { return reads.read(contract(query),request(query,request,arguments)); }
        public PlanningReadResult<Packet> read(Session borrowed,Query query,PlanningReadPort reads,PlanningRequest request,Obj arguments) { return reads.read(Objects.requireNonNull(borrowed),contract(query),request(query,request,arguments)); }
        private static PlanningReadRequest request(Query query,PlanningRequest request,Obj arguments) { return new PlanningReadRequest(request.before(),request.source(),request.sessionId(),query.operation(),arguments,request.deadline()); }
    }
    /** Minted only by this installed live decoder. Pure historical replay cannot create live
     * failure custody, and exception objects never become persisted source evidence. */
    public static final class LivePayloadFailure extends IllegalArgumentException implements OriginalReadDecodeFailure {
        private static final long serialVersionUID=1L;
        private final transient Installation installation;
        private final Query query;
        private final transient ReadContract<Packet> contract;
        private final transient PlanningReadReceipt original;
        private LivePayloadFailure(Installation installation,Query query,ReadContract<Packet> contract,PlanningReadReceipt original,ActivityReadCodec.MalformedPayload malformed){
            super(malformed.getMessage(),malformed);this.installation=installation;this.query=query;this.contract=contract;this.original=original;
        }
        @Override public void requireOriginal(ReadContract<?> identicalInstalled,PlanningReadRequest actualRequest,PlanningReadReceipt actualReceipt){
            need(installation!=null&&original!=null&&installation.contract(query)==contract&&contract==identicalInstalled
                    &&original==actualReceipt&&original.request()==actualRequest,"Activity live payload failure lost identical installed decoder/request/receipt");
        }
        public void requirePublic(Query requested,NativeActionPort.DispatchOutcome actualOriginal){
            need(query==requested&&original!=null&&original.original()==actualOriginal,"Activity public payload failure belongs to another query/original ACK");
            requireOriginal(contract,original.request(),original);
        }
    }
    /** Only these actual fields reach execute_step. Source identities are derived from the held request. */
    public static RawJson requestFields(Query query,PlanningReadRequest request) {
        JsonNode args=argument(request.arguments()); ObjectNode fields=StrictJson.object(); var identity=request.before().frame().identity();
        if(query!=Query.DIAGNOSTIC && query!=Query.STAGE1_OPTION) { fields.put("expected_date_raw",identity.dateRaw()); fields.put("expected_actor_character_id",identity.player()); }
        switch(query) {
            case DIAGNOSTIC,STAGE1_OPTION,HOSTED -> exact(args,"");
            case STAGE2_OPTION,STAGE2_GATE -> { exact(args,""); typeOption(fields); }
            case STAGE2_LOCATION -> { exact(args,"candidate_province_ids"); typeOption(fields); var array=fields.putArray("candidate_province_ids"); candidates(args).forEach(array::add); }
            case GUEST_OPINION -> { allowed(args,"guest_character_id","activity_id"); long guest=number(args,"guest_character_id",BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE)).longValueExact(); need(guest!=identity.player().longValueExact(),"guest cannot be played host"); fields.put("guest_character_id",guest); if(args.has("activity_id"))fields.put("activity_id",number(args,"activity_id",BigInteger.ONE,U32.subtract(BigInteger.ONE))); }
            case GUEST_TARGET -> { exact(args,"target_character_id"); long target=number(args,"target_character_id",BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE)).longValueExact(); need(target!=identity.player().longValueExact(),"target cannot be played host"); stageFive(fields); fields.put("target_character_id",target); }
            case GUEST_RULE -> { exact(args,"authored_rule_key"); String rule=text(args,"authored_rule_key"); ActivityJson.rule(rule); stageFive(fields); fields.put("authored_rule_key",rule); }
            case GUEST_RULE_PROVENANCE -> { exact(args,"authored_rule_key candidate_character_id"); String rule=text(args,"authored_rule_key"); ActivityJson.rule(rule); stageFive(fields); fields.put("authored_rule_key",rule); fields.put("candidate_character_id",id(args,"candidate_character_id")); }
            case GOLD,FULL_COST,GUEST_CANDIDATE,GUEST_ROUTE_PROOF -> { exact(args,""); stageFive(fields); }
            case START_INPUTS -> { exact(args,""); stageFive(fields); fields.put("expected_option_key","feast_type_generic"); }
        }
        return raw(fields);
    }
    public static List<Integer> candidates(JsonNode args) { JsonNode entries=args.get("candidate_province_ids"); need(entries!=null && entries.isArray() && entries.size()>=1 && entries.size()<=8,"one to eight explicit native candidate IDs required"); List<Integer> result=new ArrayList<>(); for(JsonNode entry:entries) { int id=(int)StrictJson.integer(entry,1,Integer.MAX_VALUE); need(!result.contains(id),"duplicate candidate ID"); result.add(id); } return List.copyOf(result); }
    private static void typeOption(ObjectNode fields) { fields.put("expected_activity_key","activity_feast").put("expected_option_key","feast_type_generic"); }
    private static void stageFive(ObjectNode fields) { fields.put("expected_activity_key","activity_feast").put("expected_planning_stage",5); }
    private static Packet decode(Query query,PlanningReadReceipt receipt) {
        need(receipt.original().nativeOk() && receipt.original().requestId().equals(receipt.requestId()),"Activity native ACK mismatch");
        ObjectNode frame=parse(receipt.original().originalFrame().bytes()); eq(frame,"type","command_result"); need(integer(frame,"protocol_version",1,1)==1,"Activity protocol"); eq(frame,"request_id",receipt.requestId()); yes(frame,"ok");
        ObjectNode result=parse(receipt.original().originalResultToken().orElseThrow(()->new IllegalArgumentException("actual Activity result token missing")).bytes()); need(frame.get("result").equals(result),"Activity original complete frame/result token differs");
        exact(result,"step accepted status private_build read_only advertised "+query.payloadKey()+" backend_id"); eq(result,"step",query.step()); yes(result,"accepted"); yes(result,"private_build"); yes(result,"read_only"); no(result,"advertised"); eq(result,"backend_id","native-headless");
        for(var guard:List.of(receipt.before(),receipt.after()))need(guard.binding().observed().equals(receipt.request().before()) && guard.binding().source().equals(receipt.request().source()) && guard.binding().sessionId().equals(receipt.request().sessionId()) && guard.paused() && guard.mapReady() && guard.playerAlive(),"Activity read crossed held living paused frame");
        need(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()) && receipt.before().binding().connectionGeneration().equals(receipt.after().binding().connectionGeneration()),"Activity frame/connection drift");
        NativeWire.Hello hello=actualHello(receipt); var identity=receipt.request().before().frame().identity(); Frame bound=new Frame(identity.nativeRevision(),identity.dateRaw(),identity.player()); CompletionCallJournal.Source journal=null;
        if(hello.gameSha256().equalsIgnoreCase(CompletionCallJournal.EXE))journal=new CompletionCallJournal.Source(receipt.request().before().machineId(),receipt.request().before().game().pid(),receipt.request().before().game().creationFiletime().value().toString(),identity.nativeRevision(),identity.dateRaw().intValueExact(),identity.player().longValueExact(),CompletionCallJournal.BUILD,hello.gameSha256());
        ActivityPayload payload=ActivityReadCodec.decode(query,raw(result.get(query.payloadKey())).bytes(),bound,receipt.request().arguments(),text(result,"status"),journal);
        return new Packet(receipt,app(result),payload);
    }
    /** Existing flattened Python DTO, derived from the same validated receipt; never a second query. */
    public static RawJson normalizedForPublic(Packet packet) {
        Objects.requireNonNull(packet);
        Query query=java.util.Arrays.stream(Query.values()).filter(value->value.operation().equals(packet.receipt().request().operation()))
                .findFirst().orElseThrow(()->new IllegalArgumentException("Activity packet has no exact native query family"));
        return ActivityPublic64.encode(query,normalizedNumeric(packet));
    }
    /** Exact original internal numeric DTO. Never expose this representation directly at a public
     * JavaScript boundary. Native receipts and payload/archive codecs continue to use their old domain. */
    public static RawJson normalizedNumeric(Packet packet) {
        Objects.requireNonNull(packet); ObjectNode published=argument(packet.payload().original()); NativeWire.Hello hello=actualHello(packet.receipt());
        String version=null; for(var build:org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels.Build.values())if(build.sha256().equalsIgnoreCase(hello.gameSha256()))version=build.version(); need(version!=null,"Activity exact published build unavailable"); published.put("exact_ck3_build",version); if(!version.equals("1.19.0.6"))published.put("exe_sha256",hello.gameSha256().toUpperCase(java.util.Locale.ROOT));
        var frame=packet.receipt().request().before().frame(); published.put("queried_snapshot_id",frame.snapshotId()).put("queried_revision",frame.revision()).put("queried_native_revision",frame.identity().nativeRevision()).put("post_snapshot_id",packet.receipt().after().binding().observed().frame().snapshotId());
        if(packet.payload() instanceof ActivityPayload.Gold)published.put("total_cost_state","unknown");
        if(packet.payload() instanceof ActivityPayload.Opinion opinion && opinion.activityTarget().isPresent())published.put("activity_target_ready",opinion.activityTarget().orElseThrow().get("status").equals(new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text("observed")));
        if(packet.payload() instanceof ActivityPayload.Hosted hosted) {
            if(hosted.terminalJournal().filter(value->value instanceof ActivityTerminalJournal.Rejected).isPresent())published.putNull("native_terminal_observations");
            if(hosted.completionCalls().filter(value->value instanceof ActivityPayload.JournalRejected).isPresent())published.putNull("native_completion_effect_counter_observations");
        }
        return raw(published);
    }
    static void publicSafeNumbers(JsonNode node) {
        if(node.isIntegralNumber())need(node.bigIntegerValue().abs().compareTo(BigInteger.valueOf(9_007_199_254_740_991L))<=0,"numeric Activity public DTO exceeds JavaScript safe integer range; retained original receipt requires exact recovery");
        else if(node.isContainerNode())for(JsonNode item:node)publicSafeNumbers(item);
    }
    /** Actual source of a private-minted typed packet; this does not publish or round any raw 64-bit fields. */
    public static NativeWire.Hello actualSource(Packet packet) { return actualHello(Objects.requireNonNull(packet).receipt()); }

    private static NativeWire.Hello actualHello(PlanningReadReceipt receipt) {
        ExactRef source=receipt.before().binding().capabilityEvidence(); need(source.bytes()>0 && source.bytes()<=NativeWire.MAXIMUM_FRAME_BYTES+4L,"bounded actual hello source required");
        try { SharedSourceFiles.Witness witness=SharedSourceFiles.observe(Path.of(source.path())); need(witness.source().bytes()==source.bytes() && witness.source().sha256().equals(source.sha256()),"Activity original hello bytes/SHA drift"); byte[] bytes=Files.readAllBytes(Path.of(source.path())); need(bytes.length==source.bytes() && digest(bytes).equals(source.sha256()),"Activity original hello changed while reading"); SharedSourceFiles.assertUnchanged(witness); var decoded=NativeWire.decode(bytes); need(decoded instanceof NativeWire.Hello,"actual original hello required"); NativeWire.Hello hello=(NativeWire.Hello)decoded;
            need(hello.pid()==receipt.request().before().game().pid() && hello.connectionGeneration().equals(receipt.before().binding().connectionGeneration()) && hello.buildMatch() && hello.adapterStatus().equals("ready"),"Activity native hello identity/session differs");
            boolean known=false; for(var build:org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels.Build.values())if(build.sha256().equalsIgnoreCase(hello.gameSha256())) { need(hello.adapterId().equals("ck3-"+build.version()+"-msvc-x64"),"Activity adapter exact build differs"); known=true; } need(known,"unknown Activity exact executable"); return hello;
        } catch(IOException invalid) { throw new IllegalArgumentException("Activity actual hello unavailable",invalid); }
    }
    static void verifySource(ExactRef source) { try { var witness=SharedSourceFiles.observe(Path.of(source.path())); need(witness.source().bytes()==source.bytes() && witness.source().sha256().equals(source.sha256()),"Activity producer bytes/SHA drift"); SharedSourceFiles.assertUnchanged(witness); } catch(IOException invalid) { throw new IllegalArgumentException("Activity exact producer unavailable",invalid); } }
    private static String digest(byte[] bytes) { try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); } catch(NoSuchAlgorithmException missing) { throw new IllegalStateException(missing); } }
}
