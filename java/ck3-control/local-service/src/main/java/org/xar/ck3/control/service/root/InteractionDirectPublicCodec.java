package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;

/** Exact original public query projections. Native decoders remain the sole business field validators. */
public final class InteractionDirectPublicCodec {
    private static final BigInteger SAFE=BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER);
    private static final Set<String> MIRRORS=Set.of("schema","schema_version","date_raw","pending_interaction_id","reason","build","definition","roles","target","send_options","routing","deadline","auto_accept","legality","terms","readiness","provenance");
    private InteractionDirectPublicCodec() { }
    public record PendingQuery(PendingId instance,BigInteger expectedRevision) {
        public PendingQuery { Objects.requireNonNull(instance);revision(expectedRevision); }
    }
    public record Ordinary(InteractionKey interaction,CharacterId recipient,BigInteger expectedRevision) {
        public Ordinary { Objects.requireNonNull(interaction);Objects.requireNonNull(recipient);revision(expectedRevision); }
        /** The actual public MCP tool exposes no education pair/options extension. */
        public OrdinaryRequest nativeRequest(){return new OrdinaryRequest(interaction,recipient,java.util.Optional.empty());}
    }
    public enum Kind { PENDING_QUERY,ORDINARY_QUERY,ORDINARY_INITIATION,ORDINARY_UNKNOWN }
    public record Reply(Kind kind,RawJson internal) {
        public Reply { Objects.requireNonNull(kind);Objects.requireNonNull(internal); }
    }
    public static PendingQuery pendingRequest(PublicBindings.Arguments arguments) {
        ObjectNode row=arguments(arguments,Set.of("pending_interaction_id","expected_revision"));
        PendingId instance=PendingInteractionPublicCodec.pending(row.get("pending_interaction_id"));
        return new PendingQuery(instance,decimal(row.get("expected_revision")));
    }
    public static Ordinary ordinaryRequest(PublicBindings.Arguments arguments) {
        ObjectNode row=arguments(arguments,Set.of("interaction_key","recipient_id","expected_revision"));
        JsonNode key=row.get("interaction_key");require(key!=null&&key.isTextual(),"interaction_key must be a string");
        InteractionKey interaction=new InteractionKey(key.textValue());
        JsonNode recipient=row.get("recipient_id");BigInteger id=StrictJson.integer(recipient,BigInteger.ONE,new BigInteger("4294967294"));
        return new Ordinary(interaction,new CharacterId(id.longValueExact()),decimal(row.get("expected_revision")));
    }
    public static RawJson encodeRequest(PendingQuery request) {
        return raw(StrictJson.object().put("pending_interaction_id",request.instance().value()).put("expected_revision",request.expectedRevision().toString()));
    }
    public static RawJson encodeRequest(Ordinary request) {
        return raw(StrictJson.object().put("interaction_key",request.interaction().value()).put("recipient_id",request.recipient().value()).put("expected_revision",request.expectedRevision().toString()));
    }
    public static Reply pending(PlanningReadResult.Known<PendingContext> known,Context current,Complete frame) {
        requireFrame(known.receipt(),current);require(current.before().equals(frame.identity()),"pending public projection lost its held frame");
        PendingContext replay=PendingContextCodec.decode(known.receipt().original().originalResultToken().orElseThrow(),current,known.value().instance());
        require(replay.equals(known.value()),"pending public projection differs from sole native typed decoder");
        ObjectNode row=object(DriverJson.toNode(InteractionReadPublications.pending(known)));
        ObjectNode context=object(row.get("pending_character_interaction_context"));
        for(String field:MIRRORS){require(context.has(field),"complete original pending mirror required");row.set(field,context.get(field).deepCopy());}
        row.put("schema_version",1).put("scope","exact-pending-character-interaction-context");
        row.put("pending_character_interaction_context_ready",replay.readiness().semanticDecision());
        var identity=current.before().frame();
        JsonNode backend=DriverJson.toNode(frame.semantic()).get("backend_id");require(backend!=null&&backend.isTextual()&&!backend.textValue().isEmpty(),"actual snapshot source backend required");
        row.putObject("source").put("game_version",current.build().version()).put("executable_sha256",current.build().sha256())
                .put("snapshot_id",identity.snapshotId()).put("revision",identity.revision()).put("native_revision",current.revision())
                .put("date_raw",current.date()).put("paused",true).put("backend_id",backend.textValue());
        row.putObject("binding").put("snapshot_id",identity.snapshotId()).put("revision",identity.revision()).put("native_revision",current.revision())
                .put("date_raw",current.date()).put("pending_interaction_id",replay.instance().value()).put("expected_revision",identity.revision());
        return new Reply(Kind.PENDING_QUERY,raw(row));
    }
    public static Reply ordinary(PlanningReadResult.Known<OrdinaryContext> known,Context current,Ordinary request) {
        requireFrame(known.receipt(),current);
        OrdinaryContext replay=OrdinaryInteractionCodec.query(known.receipt().original().originalResultToken().orElseThrow(),current,request.nativeRequest());
        require(replay.equals(known.value()),"ordinary public projection differs from its sole native typed decoder");
        ObjectNode row=object(DriverJson.toNode(InteractionReadPublications.ordinary(known)));
        // An available context can truthfully report unsupported/not-ready terms. Public queries do not apply planner selection.
        row.put("ordinary_interaction_context_ready",replay.availability().available());
        return new Reply(Kind.ORDINARY_QUERY,raw(row));
    }
    public static Reply initiation(ActionReceipt original,ActionPorts.OutcomeArchive archive,RawJson originalPublicData) {
        require(!original.settled()&&original.applied().isEmpty(),"ordinary queue DATA cannot become an Applied business result");
        var reference=archive.receiptReferenceOf(original);require(archive.loadReceipt(reference).equals(original),"ordinary canonical pending receipt changed");
        ObjectNode row=object(DriverJson.toNode(DriverJson.object(originalPublicData.bytes(),DriverJson.MAX_NATIVE_BYTES)));
        require(row.path("business_effects_verified").isBoolean()&&!row.path("business_effects_verified").booleanValue()
                &&row.path("full_product_acceptance_credit").isBoolean()&&!row.path("full_product_acceptance_credit").booleanValue(),"ordinary native queue cannot claim business acceptance credit");
        require(!row.has("action_receipt")&&!row.has("replay_allowed"),"original ordinary publication conflicts with Java receipt metadata");
        ObjectNode descriptor=row.putObject("action_receipt").put("action_id",original.command().actionId()).put("canonical_outcome",original.outcome().name())
                .put("native_ack_received",original.ack().isPresent()).put("postcondition_verified",false).put("settled",false);
        descriptor.set("original_receipt",reference.toJson());row.put("replay_allowed",false);
        return new Reply(Kind.ORDINARY_INITIATION,raw(row));
    }
    public static Reply unknown(ActionReceipt original,ActionPorts.OutcomeArchive archive) {
        require(!original.settled(),"ordinary native publication absence cannot replace a settled domain result");
        var ref=archive.receiptReferenceOf(original);require(original.equals(archive.loadReceipt(ref)),"ordinary original canonical receipt changed");
        ObjectNode row=StrictJson.object().put("step",original.command().operation().value()).put("status","ordinary_interaction_state_unknown")
                .put("native_publication_available",false).put("business_effects_verified",false).put("full_product_acceptance_credit",false).put("replay_allowed",false);
        row.set("original_receipt",ref.toJson());row.put("action_id",original.command().actionId()).put("native_ack_received",original.ack().isPresent());
        return new Reply(Kind.ORDINARY_UNKNOWN,raw(row));
    }
    /** Only declared original uint64/int64 paths become decimal strings. IDs and bounded counters stay numeric. */
    public static RawJson encode(Reply reply) {
        ObjectNode row=object(DriverJson.toNode(DriverJson.object(reply.internal().bytes(),DriverJson.MAX_NATIVE_BYTES)));
        for(String field:List.of("query_sequence","snapshot_revision","connection_generation","queried_revision","queried_native_revision","after_revision","after_native_revision"))wide(row,field,false);
        if(reply.kind()==Kind.PENDING_QUERY){
            for(String group:List.of("source","binding"))if(row.get(group) instanceof ObjectNode child)
                for(String field:List.of("revision","native_revision","expected_revision"))wide(child,field,false);
            pendingContext(row,false);if(row.get("pending_character_interaction_context") instanceof ObjectNode child)pendingContext(child,true);
        }else{
            if(row.get("character_interaction_ordinary_context") instanceof ObjectNode child)ordinaryContext(child);
            if(row.get("character_interaction_ordinary_initiation") instanceof ObjectNode child){ordinaryContext(child);
                if(child.get("preflight_context") instanceof ObjectNode preflight)ordinaryContext(preflight);}
        }
        safe(row);return raw(row);
    }
    private static void pendingContext(ObjectNode node,boolean includeFrame){
        if(includeFrame)wide(node,"snapshot_revision",false);
        JsonNode entries=node.path("terms").path("structured_costs").path("value").path("entries");
        if(entries.isArray())for(JsonNode entry:entries)wide(object(entry),"raw",true);
        if(node.path("terms").path("ransom_quote").path("value") instanceof ObjectNode ransom)wide(ransom,"gold_raw",true);
    }
    private static void ordinaryContext(ObjectNode node){
        for(String field:List.of("snapshot_revision","connection_generation","owner_pump_epoch"))wide(node,field,false);
        for(String field:List.of("recipient_score_raw","intermediary_score_raw"))wide(node,field,true);
        if(node.get("costs_raw") instanceof com.fasterxml.jackson.databind.node.ArrayNode costs)
            for(int i=0;i<costs.size();i++)costs.set(i,com.fasterxml.jackson.databind.node.TextNode.valueOf(wideInteger(costs.get(i),true).toString()));
    }
    private static void requireFrame(PlanningReadReceipt receipt,Context current){
        require(receipt.request().before().equals(current.before())&&receipt.request().source().equals(current.source())&&receipt.request().sessionId().equals(current.sessionId())
                &&receipt.before().binding().observed().equals(current.before())&&receipt.after().binding().observed().equals(current.before())
                &&receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),"public interaction query crossed the original stable complete frame");
    }
    private static void wide(ObjectNode row,String field,boolean signed){if(row.has(field)&&!row.get(field).isNull())row.put(field,wideInteger(row.get(field),signed).toString());}
    private static BigInteger wideInteger(JsonNode value,boolean signed){return StrictJson.integer(value,signed?BigInteger.ONE.shiftLeft(63).negate():BigInteger.ZERO,signed?BigInteger.ONE.shiftLeft(63).subtract(BigInteger.ONE):StrictJson.UINT64_MAX);}
    private static void safe(JsonNode value){if(value.isIntegralNumber())require(value.bigIntegerValue().abs().compareTo(SAFE)<=0,"undeclared unsafe public interaction integer");else if(value.isFloatingPointNumber())throw new IllegalArgumentException("undeclared floating public interaction field");else if(value.isContainerNode())value.forEach(InteractionDirectPublicCodec::safe);}
    private static ObjectNode arguments(PublicBindings.Arguments arguments,Set<String> fields){require(arguments instanceof PublicBindings.Value,"named public interaction arguments required");ObjectNode row=object(StrictJson.parse(((PublicBindings.Value)arguments).original().bytes(),16384));for(var field:row.properties())require(fields.contains(field.getKey()),"unknown public interaction argument");return row;}
    private static BigInteger decimal(JsonNode value){require(value!=null&&value.isTextual()&&value.textValue().matches("0|[1-9][0-9]*")&&value.textValue().length()<=20,"expected_revision must be canonical uint64 decimal");BigInteger result=new BigInteger(value.textValue());revision(result);return result;}
    private static void revision(BigInteger value){require(value!=null&&value.signum()>=0&&value.compareTo(StrictJson.UINT64_MAX)<=0,"expected revision must be uint64");}
    private static ObjectNode object(JsonNode value){require(value instanceof ObjectNode,"original public interaction object required");return (ObjectNode)value;}
    private static RawJson raw(JsonNode row){return new RawJson(DriverJson.encodeNode(row));}
    private static void require(boolean value,String message){StrictJson.require(value,message);}
}
