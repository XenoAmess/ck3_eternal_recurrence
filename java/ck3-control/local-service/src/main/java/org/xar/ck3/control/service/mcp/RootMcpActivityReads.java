package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityPublic64;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts.Packet;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts.Query;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.RootSessionAccess;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** The original eight private Activity public queries use the already installed domain contracts. */
public final class RootMcpActivityReads {
    public enum FailureStage { NATIVE_RED,PAYLOAD_MALFORMED,READ_UNAVAILABLE }
    public record FailureEvidence(Query query,FailureStage stage,String diagnostic,java.util.Optional<NativeActionPort.DispatchOutcome> original) {
        public FailureEvidence{Objects.requireNonNull(query);Objects.requireNonNull(stage);Objects.requireNonNull(diagnostic);Objects.requireNonNull(original);}
    }
    /** Preserve the exact actual read diagnosis/outcome under the existing public typed error;
     * no class is guessed from reason text and no side registry or result replay is involved. */
    public static final class ActualReadFailure extends RuntimeException {
        private static final long serialVersionUID=1L;private final transient FailureEvidence evidence;
        public ActualReadFailure(FailureEvidence evidence){super(Objects.requireNonNull(evidence).diagnostic());this.evidence=evidence;}
        public FailureEvidence evidence(){return evidence;}
    }
    public record Request(Query query,BigInteger expectedRevision,OpportunityJson.Obj arguments) {
        public Request {Objects.requireNonNull(query);Objects.requireNonNull(expectedRevision);Objects.requireNonNull(arguments);publicName(query);McpJson.require(expectedRevision.signum()>0&&expectedRevision.bitLength()<=(query==Query.GUEST_RULE_PROVENANCE?32:64),"positive exact expected revision exceeds its original Activity query width");}
    }
    private final RootSessionAccess sessions;
    private final ActivityNativeContracts.Installation installation;
    private final Clock clock;
    private final Duration timeout;
    public RootMcpActivityReads(RootSessionAccess sessions,ActivityNativeContracts.Installation actualInstallation,Clock clock,Duration timeout) {
        this.sessions=Objects.requireNonNull(sessions);installation=Objects.requireNonNull(actualInstallation);this.clock=Objects.requireNonNull(clock);this.timeout=Objects.requireNonNull(timeout);
        McpJson.require(!timeout.isNegative() && !timeout.isZero() && timeout.compareTo(Duration.ofMinutes(2))<=0,"finite positive Activity timeout required");
    }
    public RawJson read(Request request) throws InterruptedException {
        final PlanningReadResult<Packet> result;
        var deadline=clock.instant().plus(timeout);
        try { result=sessions.withCurrent(root -> root.withPublicObservation(deadline,(frame,known,same)->{
            validateCurrent(request,frame.identity().frame().revision(),frame.identity().frame().identity().player());
            var contract=installation.contract(request.query());
            return root.read(same,contract,new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),contract.operation(),request.arguments(),deadline));
        })); }
        catch(PublicServiceFailure original){throw original;}
        catch(IOException|IllegalArgumentException failure) {
            // This catch belongs only to the actual source/read stage. Public formatting below
            // cannot be reclassified as a native or ordinary business failure.
            throw bridge(request.query()," source unavailable: "+String.valueOf(failure.getMessage()),failure);
        }
        return present(request.query(),result);
    }
    @FunctionalInterface public interface Reader {RawJson read(Request request)throws InterruptedException;}
    public List<McpExecutableDirectory.DirectBinding<?,?>> actualMethods(ExactRef actualThisSource) {
        return componentMethods(this::read,actualThisSource);
    }
    /** Same production binder is usable in an explicitly software-only Directory test. A Reader
     * does not construct RootSessionAccess or acquire a native permission. */
    public static List<McpExecutableDirectory.DirectBinding<?,?>> componentMethods(Reader reader,ExactRef actualThisSource) {
        Objects.requireNonNull(reader);Objects.requireNonNull(actualThisSource);
        List<McpExecutableDirectory.DirectBinding<?,?>> bindings=new ArrayList<>();
        for(Query query:List.of(Query.START_INPUTS,Query.HOSTED,Query.FULL_COST,Query.GUEST_CANDIDATE,Query.GUEST_OPINION,Query.GUEST_TARGET,Query.GUEST_ROUTE_PROOF,Query.GUEST_RULE_PROVENANCE)) {
            String name=publicName(query);
            bindings.add(new McpExecutableDirectory.DirectBinding<>(name,PublicMcpBindings.Kind.DRIVER_DIRECT,Request.class,RawJson.class,
                    reader::read,call -> decode(query,call.arguments()),CallResult::fromBusinessJson,
                    new PublicRoutes.Target(RootMcpActivityReads.class.getName(),"read",actualThisSource)));
        }
        return List.copyOf(bindings);
    }
    public static RawJson encodeRequest(Request request) {
        Objects.requireNonNull(request);ObjectNode row=(ObjectNode)McpJson.parse(OpportunityJson.encode(request.arguments()));
        McpJson.require(!row.has("expected_revision"),"native Activity arguments cannot contain the public revision");
        row.put("expected_revision",request.expectedRevision().toString());return new RawJson(McpJson.encode(row));
    }
    /** Own request order after real source observation, before the identical installed read. */
    public static void validateCurrent(Request request,BigInteger actualRevision,BigInteger host) {
        if(!request.expectedRevision().equals(actualRevision))throw bridge(request.query(),switch(request.query()){case START_INPUTS,HOSTED->" query revision changed";case FULL_COST->" read requires a living paused actor";default->" revision changed";},null);
        String field=request.query()==Query.GUEST_OPINION?"guest_character_id":request.query()==Query.GUEST_TARGET?"target_character_id":null;
        if(field!=null&&OpportunityJson.integer(request.arguments().get(field),field).equals(host))
            throw new PublicServiceFailure(PublicServiceFailure.Kind.VALUE_ERROR,field.equals("guest_character_id")?"guest_character_id must differ from the host":"target guest cannot be the played host",java.util.Optional.empty());
    }
    public static RawJson present(Query query,PlanningReadResult<Packet> result) {
        publicName(query);Objects.requireNonNull(result);
        if(result instanceof PlanningReadResult.Known<Packet> known) {
            McpJson.require(known.value().receipt().equals(known.receipt())&&known.receipt().request().operation().equals(query.operation()),"Activity public result belongs to another actual native query");
            return ActivityNativeContracts.normalizedForPublic(known.value());
        }
        var unavailable=(PlanningReadResult.Unavailable<Packet>)result;
        if(unavailable.decodeFailure().orElse(null) instanceof ActivityNativeContracts.LivePayloadFailure malformed){
            malformed.requirePublic(query,unavailable.original().orElseThrow());
            var evidence=new ActualReadFailure(new FailureEvidence(query,FailureStage.PAYLOAD_MALFORMED,unavailable.reason(),unavailable.original()));
            evidence.initCause(malformed);
            var failure=new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,malformed.getMessage(),java.util.Optional.empty());
            failure.initCause(evidence);throw failure;
        }
        if(unavailable.original().orElse(null) instanceof NativeActionPort.AckReceived ack&&!ack.nativeOk()) {
            try {
                var frame=NativeWire.decode(ack.originalPacket());
                if(frame instanceof NativeWire.CommandResult returned&&!returned.nativeOk()&&returned.requestId().equals(ack.requestId())) {
                    String error="unknown";
                    if(returned.error().presence()!=NativeWire.Presence.ABSENT) {
                        var actual=McpJson.parse(returned.error().token().orElseThrow().value());
                        error=actual.isTextual()?actual.textValue():actual.isNull()?"None":actual.toString();
                    }
                    throw bridge(query," native RED: "+error,new ActualReadFailure(new FailureEvidence(query,FailureStage.NATIVE_RED,unavailable.reason(),unavailable.original())));
                }
            }catch(IOException malformed){throw bridge(query," result unavailable",malformed);}
        }
        // Every original Activity read classifies unavailable native/read results as BridgeUnavailable.
        // Keep the real coordinator diagnosis; never infer an exception class from its reason text.
        throw bridge(query," result unavailable: "+unavailable.reason(),new ActualReadFailure(new FailureEvidence(query,FailureStage.READ_UNAVAILABLE,unavailable.reason(),unavailable.original())));
    }
    private static PublicServiceFailure bridge(Query query,String suffix,Throwable cause) {
        String prefix=switch(query) {
            case START_INPUTS,HOSTED->"private feast Start";
            case FULL_COST->"private feast full-cost";
            case GUEST_CANDIDATE->"private feast guest candidate";
            case GUEST_OPINION->"private feast guest opinion";
            case GUEST_TARGET->"private feast target";
            case GUEST_ROUTE_PROOF->"private feast guest route proof";
            case GUEST_RULE_PROVENANCE->"private feast rule provenance";
            default->throw new IllegalArgumentException("Activity query has no public error profile");
        };
        var original=new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,prefix+suffix,java.util.Optional.empty());
        if(cause!=null)original.initCause(cause);return original;
    }
    public static String publicName(Query query) {return switch(query) {
        case START_INPUTS -> "ck3_query_activity_feast_stage5_start_inputs_private_v1";
        case HOSTED -> "ck3_query_activity_feast_hosted_post_private_v1";
        case FULL_COST -> "ck3_query_activity_stage5_feast_full_cost_private_v1";
        case GUEST_CANDIDATE -> "ck3_query_activity_feast_guest_candidate_private_v1";
        case GUEST_OPINION -> "ck3_query_activity_feast_guest_opinion_private_v1";
        case GUEST_TARGET -> "ck3_query_activity_feast_guest_target_private_v1";
        case GUEST_ROUTE_PROOF -> "ck3_query_activity_feast_guest_route_proof_private_v1";
        case GUEST_RULE_PROVENANCE -> "ck3_query_activity_feast_guest_rule_provenance_private_v1";
        default -> throw new IllegalArgumentException("Activity private query has no original public MCP declaration");};}
    public static Request decode(Query query,Arguments arguments) {
        publicName(query);
        ObjectNode row=McpJson.object(McpJson.parse(arguments.objectOrEmpty().bytes()));McpJson.publicNumbers(row);
        Set<String> extra=switch(query) {case GUEST_OPINION -> Set.of("guest_character_id","activity_id");case GUEST_TARGET -> Set.of("target_character_id");case GUEST_RULE_PROVENANCE -> Set.of("authored_rule_key","candidate_character_id");default -> Set.of();};
        var allowed=new java.util.HashSet<>(extra);allowed.add("expected_revision");var required=new java.util.HashSet<>(allowed);required.remove("activity_id");McpJson.fields(row,allowed,required);
        BigInteger revision=query==Query.GUEST_RULE_PROVENANCE?null:revision(query,row.get("expected_revision"));
        ObjectNode nativeArguments=row.deepCopy();nativeArguments.remove("expected_revision");
        if(nativeArguments.has("activity_id") && nativeArguments.get("activity_id").isNull()) nativeArguments.remove("activity_id");
        if(nativeArguments.has("authored_rule_key")&&!(nativeArguments.get("authored_rule_key").isTextual() && nativeArguments.get("authored_rule_key").textValue().length()<=96 && nativeArguments.get("authored_rule_key").textValue().matches("activity_invite_rule_[a-z0-9_]+")))
            throw new PublicServiceFailure(PublicServiceFailure.Kind.VALUE_ERROR,"authored_rule_key must be a bounded feast invitation rule",java.util.Optional.empty());
        for(String field:List.of("guest_character_id","target_character_id","candidate_character_id")) if(nativeArguments.has(field)) positive(nativeArguments,field,field.equals("candidate_character_id")?new BigInteger("4294967295"):BigInteger.valueOf(Integer.MAX_VALUE));
        if(nativeArguments.has("activity_id")) positive(nativeArguments,"activity_id",new BigInteger("4294967294"));
        if(revision==null)revision=revision(query,row.get("expected_revision"));
        return new Request(query,revision,OpportunityJson.object(OpportunityJson.parse(McpJson.encode(nativeArguments)),"Activity arguments"));
    }
    private static void positive(ObjectNode row,String field,BigInteger maximum) {
        var value=row.get(field);
        if(value!=null&&value.isIntegralNumber()&&value.bigIntegerValue().signum()>0&&value.bigIntegerValue().compareTo(maximum)<=0)return;
        String message=switch(field){case "guest_character_id"->"guest_character_id must be a positive full CharacterID";case "target_character_id"->"target_character_id must be a positive full int32 ID";case "activity_id"->"activity_id must be a positive nonempty full ActivityID";case "candidate_character_id"->"candidate_character_id must be a full positive CharacterID";default->throw new IllegalArgumentException("unexpected Activity public identity field");};
        throw new PublicServiceFailure(PublicServiceFailure.Kind.VALUE_ERROR,message,java.util.Optional.empty());
    }
    private static BigInteger revision(Query query,com.fasterxml.jackson.databind.JsonNode value){try{var actual=ActivityPublic64.positiveRevision(value);McpJson.require(query!=Query.GUEST_RULE_PROVENANCE||actual.bitLength()<=32,"original rule provenance revision is uint32");return actual;}catch(IllegalArgumentException invalid){throw new PublicServiceFailure(PublicServiceFailure.Kind.VALUE_ERROR,query==Query.GUEST_RULE_PROVENANCE?"private feast rule provenance frame or timeout invalid":"expected_revision must be positive",java.util.Optional.empty());}}
}
