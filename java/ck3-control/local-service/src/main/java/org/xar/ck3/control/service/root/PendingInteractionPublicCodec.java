package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativePendingInteraction;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.PendingId;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.PendingSummary;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionRules.Action;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionPostcondition;
import org.xar.ck3.control.application.planning.events.NativeEventPostconditionPort;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedInteger;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;

/** Public pending notifications have signed generation-bearing IDs; event-option identity is a different contract. */
public final class PendingInteractionPublicCodec {
    public static final String SCHEMA="xar.java-public-pending-interaction/v1";
    public static final int MAXIMUM_REQUEST_BYTES=16384,MAXIMUM_RESULT_BYTES=8*1024*1024;
    private static final BigInteger SAFE=BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER);
    private PendingInteractionPublicCodec() { }
    public enum Presence { MISSING,NULL,VALUE }
    public record Field<T>(Presence presence,T value) {
        public Field { Objects.requireNonNull(presence);require((presence==Presence.VALUE)==(value!=null),"pending public field presence/value differs"); }
        public static <T> Field<T> missing(){return new Field<>(Presence.MISSING,null);}
        public static <T> Field<T> nullValue(){return new Field<>(Presence.NULL,null);}
        public static <T> Field<T> of(T value){return new Field<>(Presence.VALUE,Objects.requireNonNull(value));}
        public Optional<T> optional(){return Optional.ofNullable(value);}
    }
    public sealed interface Request permits Reply,Acknowledge {
        Field<BigInteger> expectedRevision();Action action();Optional<PendingId> requestedInstance();
    }
    public record Reply(boolean accept,Field<PendingId> instance,Field<BigInteger> expectedRevision) implements Request {
        public Reply { Objects.requireNonNull(instance);revision(expectedRevision); }
        @Override public Action action(){return accept?Action.ACCEPT:Action.REJECT;}
        @Override public Optional<PendingId> requestedInstance(){return instance.optional();}
    }
    public record Acknowledge(PendingId instance,Field<BigInteger> expectedRevision) implements Request {
        public Acknowledge { Objects.requireNonNull(instance);revision(expectedRevision); }
        @Override public Action action(){return Action.ACKNOWLEDGE;}
        @Override public Optional<PendingId> requestedInstance(){return Optional.of(instance);}
    }
    public static Reply decodeReply(PublicBindings.Arguments arguments) {
        ObjectNode row=request(arguments,Set.of("accept","interaction_instance_id","expected_revision"));
        JsonNode accept=row.get("accept");require(accept!=null&&accept.isBoolean(),"reply accept must be an exact boolean");
        Field<PendingId> instance=!row.has("interaction_instance_id")?Field.missing():row.get("interaction_instance_id").isNull()?Field.nullValue():Field.of(pending(row.get("interaction_instance_id")));
        return new Reply(accept.booleanValue(),instance,revisionField(row));
    }
    public static Acknowledge decodeAcknowledge(PublicBindings.Arguments arguments) {
        ObjectNode row=request(arguments,Set.of("interaction_instance_id","expected_revision"));
        return new Acknowledge(pending(row.get("interaction_instance_id")),revisionField(row));
    }
    public static RawJson encodeRequest(Request request) {
        Objects.requireNonNull(request);ObjectNode row=StrictJson.object();
        if(request instanceof Reply reply){row.put("accept",reply.accept());putInstance(row,reply.instance());}
        else row.put("interaction_instance_id",((Acknowledge)request).instance().value());
        switch(request.expectedRevision().presence()) {case MISSING->{}case NULL->row.putNull("expected_revision");case VALUE->row.put("expected_revision",request.expectedRevision().value().toString());}
        return new RawJson(StrictJson.canonical(row,MAXIMUM_REQUEST_BYTES));
    }
    /** Same canonical receipt and replay-verified material are provided by the actual installer, never by ACK interpretation here. */
    public static RawJson result(ActionReceipt receipt,ActionPorts.OutcomeArchive archive,Optional<RawJson> verified,
            PendingSummary sameObservedPending,Action requested) {
        Objects.requireNonNull(receipt);Objects.requireNonNull(archive);Objects.requireNonNull(verified);Objects.requireNonNull(sameObservedPending);Objects.requireNonNull(requested);
        require(originalInstance(receipt.command()).equals(sameObservedPending.instance()),"public pending receipt changed the observed generation-bearing instance");
        require(sameObservedPending.autoAcceptNotification()==(requested==Action.ACKNOWLEDGE),"pending public reply channel differs from its actual notification");
        ExactRef reference=archive.receiptReferenceOf(receipt);require(receipt.equals(archive.loadReceipt(reference)),"pending public receipt differs from its sole archive");
        boolean applied=receipt.applied().isPresent();require(applied==verified.isPresent(),"only Applied has verified pending business material");
        ObjectNode result=verified.map(raw->tree(raw.bytes())).orElseGet(StrictJson::object);
        require(!result.has("action_receipt")&&!result.has("pending_interaction_public_schema"),"pending original conflicts with public receipt fields");
        if(applied) {
            require(receipt.command().operation().value().equals(requested.step()),"a different retained action cannot supply requested pending business material");
            ObjectNode interaction=object(result.get("interaction_result"));
            String status=switch(requested){case ACCEPT->"accepted";case REJECT->"rejected";case ACKNOWLEDGE->"acknowledged";};
            require(status.equals(text(interaction.get("status")))&&integer(interaction.get("instance_id")).equals(BigInteger.valueOf(sameObservedPending.instance().value())),"pending business result did not prove the exact requested instance advancement");
            require(integer(interaction.get("sender_character_id")).equals(BigInteger.valueOf(sameObservedPending.sender().value())),"pending public sender differs from original native material");
            if(receipt.command().expected().observerSchema().equals(NativeEventPostconditionPort.PENDING_SCHEMA)) {
                // This sole producer's v3 schema carries the proof inside selection, unlike the known-rule producer.
                // Validate its actual original pair before adding the public convenience leaf; never rewrite archived material.
                require("xar.java-native-event-result/v3".equals(text(result.get("event_result_projection_schema"))),"current fallback public material requires its explicit native result version");
                ObjectNode selection=object(result.get("pending_character_interaction_selection"));
                var after=receipt.applied().orElseThrow().observation().after().frame();
                require(selection.path("postcondition_verified").isBoolean()&&selection.path("postcondition_verified").booleanValue()
                        &&receipt.command().before().frame().snapshotId().equals(text(selection.get("starting_snapshot_id")))
                        &&after.snapshotId().equals(text(selection.get("ending_snapshot_id")))
                        &&after.snapshotId().equals(text(result.get("snapshot_id")))
                        &&after.revision().equals(integer(result.get("revision")))
                        &&result.path("paused").isBoolean()&&result.path("paused").booleanValue(),"fallback public material differs from its independently archived original pair");
                JsonNode remaining=result.get("remaining_pending_character_interaction");require(remaining!=null,"fallback public material requires the explicit original remaining observation");
                var pendingAfter=NativePendingInteraction.decode(remaining);
                require(pendingAfter.isEmpty()||pendingAfter.orElseThrow().instanceId()!=sameObservedPending.instance().value(),"fallback public material still contains its original native window");
                if(result.has("postcondition_verified"))require(result.get("postcondition_verified").isBoolean()&&result.get("postcondition_verified").booleanValue(),"conflicting fallback public proof field");
                result.put("postcondition_verified",true);
            }else require(result.get("postcondition_verified")!=null&&result.get("postcondition_verified").isBoolean()
                    &&result.get("postcondition_verified").booleanValue(),"public pending result requires independent native advancement");
        }else result.put("step",receipt.command().operation().value()).put("status",receipt.settled()?"pending_action_not_applied":"pending_action_state_unknown");
        result.put("pending_interaction_public_schema",SCHEMA).put("interaction_instance_id",sameObservedPending.instance().value())
                .put("sender_character_id",sameObservedPending.sender().value()).put("requested_step",requested.step()).put("replay_allowed",false);
        if(requested==Action.ACKNOWLEDGE){result.put("requested_acknowledgement",true);if(applied)result.put("acknowledged",true);else result.putNull("acknowledged");}
        else {result.put("requested_accept",requested==Action.ACCEPT);if(applied)result.put("accepted",requested==Action.ACCEPT);else result.putNull("accepted");}
        ObjectNode descriptor=result.putObject("action_receipt").put("action_id",receipt.command().actionId()).put("command_body_sha256",receipt.bodySha256())
                .put("original_step",receipt.command().operation().value()).put("sequence",Long.toString(receipt.sequence())).put("canonical_outcome",receipt.outcome().name())
                .put("settled",receipt.settled()).put("native_ack_received",receipt.ack().isPresent()).put("postcondition_verified",applied)
                .put("machine_id",receipt.command().before().machineId()).put("session_id",receipt.command().sessionId());
        if(receipt.ack().isPresent())descriptor.put("native_ok",receipt.ack().orElseThrow().nativeOk());else descriptor.putNull("native_ok");
        descriptor.set("original_receipt",reference.toJson());
        // These exact root leaves are the nonnegative uint64 fields emitted by the existing pending effect producer.
        for(String field:List.of("revision","native_revision"))wide(result,field);
        wide(result,"observed_player_gold_increase_raw");safeNumbers(result);
        byte[] encoded=DriverJson.encodeNode(result);require(encoded.length<=MAXIMUM_RESULT_BYTES,"bounded pending public result required");
        return new RawJson(encoded);
    }
    public static PendingId pending(JsonNode value) { require(value!=null&&value.isIntegralNumber(),"pending interaction ID must be an exact signed int32");BigInteger n=value.bigIntegerValue();require(n.compareTo(BigInteger.valueOf(Integer.MIN_VALUE))>=0&&n.compareTo(BigInteger.valueOf(Integer.MAX_VALUE))<=0,"pending interaction ID exceeds signed int32");return new PendingId(n.intValueExact()); }
    public static boolean supports(OperationKey operation) {return Set.of("accept-pending-character-interaction","reject-pending-character-interaction","acknowledge-pending-character-interaction","block-pending-character-interaction").contains(Objects.requireNonNull(operation).value());}
    public static PendingId originalInstance(ActionCommand command) {
        Objects.requireNonNull(command);require(supports(command.operation()),"exact pending operation required");
        if(command.expected().observerSchema().equals(KnownPendingInteractionPostcondition.SCHEMA))
            return pending(DriverJson.toNode(command.arguments()).get("pending_id"));
        require(command.expected().observerSchema().equals(NativeEventPostconditionPort.PENDING_SCHEMA),"registered pending observer schema required");
        var values=command.expected().values().stream().filter(ExpectedInteger.class::isInstance).map(ExpectedInteger.class::cast)
                .filter(value->value.field().value().equals("old_instance_id")).map(ExpectedInteger::value).toList();
        require(values.size()==1,"one exact original pending instance required");
        return pending(com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.numberNode(values.getFirst()));
    }
    private static Field<BigInteger> revisionField(ObjectNode row) {return !row.has("expected_revision")?Field.missing():row.get("expected_revision").isNull()?Field.nullValue():Field.of(decimal(row.get("expected_revision")));}
    private static void revision(Field<BigInteger> field) {Objects.requireNonNull(field);field.optional().ifPresent(value->require(value.signum()>=0&&value.bitLength()<=64,"pending expected revision must be uint64"));}
    private static BigInteger decimal(JsonNode value) {require(value!=null&&value.isTextual()&&value.textValue().matches("0|[1-9][0-9]*")&&value.textValue().length()<=20,"expected_revision requires a canonical uint64 decimal string");BigInteger n=new BigInteger(value.textValue());require(n.bitLength()<=64,"expected_revision exceeds uint64");return n;}
    private static ObjectNode request(PublicBindings.Arguments arguments,Set<String> fields) {require(arguments instanceof PublicBindings.Value,"pending interaction arguments must be a present object");ObjectNode row=object(StrictJson.parse(((PublicBindings.Value)arguments).original().bytes(),MAXIMUM_REQUEST_BYTES));for(var entry:row.properties())require(fields.contains(entry.getKey()),"unknown pending interaction argument");return row;}
    private static void putInstance(ObjectNode row,Field<PendingId> value) {switch(value.presence()){case MISSING->{}case NULL->row.putNull("interaction_instance_id");case VALUE->row.put("interaction_instance_id",value.value().value());}}
    private static void wide(ObjectNode root,String name) {if(!root.has(name)||root.get(name).isNull())return;BigInteger n=integer(root.get(name));require(n.signum()>=0&&n.bitLength()<=64,"pending original wide integer differs");root.put(name,n.toString());}
    private static void safeNumbers(JsonNode value) {if(value.isIntegralNumber())require(value.bigIntegerValue().abs().compareTo(SAFE)<=0,"undeclared unsafe pending public numeric role");else if(value.isFloatingPointNumber())throw new IllegalArgumentException("untyped pending public floating-point field");else if(value.isContainerNode())value.forEach(PendingInteractionPublicCodec::safeNumbers);}
    private static ObjectNode tree(byte[] bytes){return object(DriverJson.toNode(DriverJson.object(bytes,MAXIMUM_RESULT_BYTES)));}
    private static ObjectNode object(JsonNode value){require(value!=null&&value.isObject(),"pending public object required");return (ObjectNode)value;}
    private static String text(JsonNode value){require(value!=null&&value.isTextual(),"pending public text required");return value.textValue();}
    private static BigInteger integer(JsonNode value){require(value!=null&&value.isIntegralNumber(),"pending public integer required");return value.bigIntegerValue();}
    private static void require(boolean condition,String reason){StrictJson.require(condition,reason);}
}
