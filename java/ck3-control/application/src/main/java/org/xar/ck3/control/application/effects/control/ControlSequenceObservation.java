package org.xar.ck3.control.application.effects.control;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Closed control-only DATA. Only the installed Root verifier can qualify the referenced physical originals.
 * This value never grants a retry, ordinary readiness, gameplay effect, elapsed-day credit or SAVE eligibility.
 */
public record ControlSequenceObservation(ActionCommand parent,Mode mode,ObservationIdentity after,ExactRef proof,
        List<Child> children,List<ExactRef> originals) {
    public static final String SCHEMA="xar.java.source-bound-pause-control-sequence/v1";
    public static final String OBSERVER="xar.java.public-pause-control/v1";
    public static final OperationKey OPERATION=new OperationKey("public-pause-with-recovery");
    public static final String MAP_UNAVAILABLE="CK3 map state is unavailable";
    public enum Kind { PAUSE_WITH_SOURCE_BOUND_RETRY }
    public enum Mode { DIRECT_PAUSE,ALREADY_PAUSED_AFTER_REJECTION,RETRIED_PAUSE }
    public record Child(String actionId,String bodySha256,ExactRef canonicalReceipt) {
        public Child {
            StrictJson.text(actionId);Objects.requireNonNull(canonicalReceipt);
            require(bodySha256!=null&&bodySha256.matches("[0-9a-f]{64}")&&canonicalReceipt.bytes()>0,"actual canonical child locator required");
        }
    }
    public ControlSequenceObservation {
        Objects.requireNonNull(parent);Objects.requireNonNull(mode);Objects.requireNonNull(after);Objects.requireNonNull(proof);
        children=List.copyOf(children);originals=List.copyOf(originals);validateParent(parent);
        require(proof.bytes()>0&&children.size()==(mode==Mode.RETRIED_PAUSE?2:1),"closed finite original pause children required");
        require(children.stream().map(Child::actionId).distinct().count()==children.size(),"a canonical pause child cannot be reused");
        require(originals.size()<=64&&new HashSet<>(originals).size()==originals.size(),"bounded unique control originals required");
        originals.forEach(ref->require(ref.bytes()>0,"actual nonempty control original required"));
        var before=parent.before();
        require(after.machineId().equals(before.machineId())&&after.game().equals(before.game())
                &&after.frame().episodeRunId().equals(before.frame().episodeRunId())
                &&after.frame().identity().player().equals(before.frame().identity().player())
                &&after.frame().revision().compareTo(before.frame().revision())>=0
                &&after.frame().identity().nativeRevision().compareTo(before.frame().identity().nativeRevision())>=0
                &&after.frame().identity().dateRaw().compareTo(before.frame().identity().dateRaw())>=0,
                "control ending frame left its original owner or regressed; no inferred days credit");
    }
    public Kind kind(){return Kind.PAUSE_WITH_SOURCE_BOUND_RETRY;}
    public static List<ExpectedValue> expected(){return List.of(
            new ExpectedBoolean(new FieldKey("native.gameplay_verified"),false),
            new ExpectedBoolean(new FieldKey("timeline.advance_verified"),false),
            new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"),false),
            new ExpectedBoolean(new FieldKey("control.paused"),true));}
    public static void validateParent(ActionCommand command){
        Objects.requireNonNull(command);
        require(command.origin() instanceof CommandOrigin.Gameplay&&command.operation().equals(OPERATION)
                &&command.arguments().members().isEmpty()&&command.expected().observerSchema().equals(OBSERVER)
                &&command.expected().values().equals(expected()),"only the exact original public pause Java parent is allowed");
        var claims=ActionCodec.claims(command.claims());
        claims.elements().forEachRemaining(value->require(value.isArray()&&value.isEmpty(),"control cannot claim world resources"));
    }
    /** Canonical children are supplied by the coordinator, never decoded from the proof and treated as ledger authority. */
    public void validateChildren(CompositeExecution execution,List<ActionReceipt> actualCanonical){
        Objects.requireNonNull(execution);actualCanonical=List.copyOf(actualCanonical);
        require(execution.children().size()==children.size()&&actualCanonical.size()==children.size(),"control child roster changed");
        require(execution.guard().source().equals(parent.source())&&execution.guard().sessionId().equals(parent.sessionId())
                &&execution.guard().operation().equals(parent.operation())&&execution.guard().observed().equals(parent.before()),"control parent guard changed");
        for(int i=0;i<children.size();i++){
            Child child=children.get(i);var receipt=actualCanonical.get(i);var reserved=execution.children().get(i);
            require(receipt.settled()&&reserved.actionId().equals(child.actionId())&&reserved.bodySha256().equals(child.bodySha256())
                    &&receipt.command().actionId().equals(child.actionId())&&receipt.bodySha256().equals(child.bodySha256())
                    &&receipt.command().operation().value().equals("pause-map")&&receipt.command().arguments().members().isEmpty()
                    &&receipt.command().source().equals(parent.source())&&receipt.command().sessionId().equals(parent.sessionId())
                    &&receipt.command().before().game().equals(parent.before().game())
                    &&receipt.command().before().frame().episodeRunId().equals(parent.before().frame().episodeRunId())
                    &&receipt.command().before().frame().identity().player().equals(parent.before().frame().identity().player()),
                    "control requires its actual reserved original pause child under the same owner");
        }
        var first=actualCanonical.getFirst();
        if(mode==Mode.DIRECT_PAUSE)requireControl(first);
        else requireMapUnavailable(first);
        if(mode==Mode.RETRIED_PAUSE){
            var second=actualCanonical.getLast();
            requireControl(second);
            require(second.command().before().frame().revision().compareTo(first.command().before().frame().revision())>0
                    &&second.command().before().frame().identity().nativeRevision().compareTo(first.command().before().frame().identity().nativeRevision())>0,
                    "one retry needs its actually fresh source-bound paused result, never an UNKNOWN replay");
        }
    }
    private static void requireControl(ActionReceipt child){
        require(child.state() instanceof ActionState.Settled settled&&(settled.settlement() instanceof ActionState.ControlApplied || settled.settlement() instanceof ActionState.PauseConfirmed),
                "a source-bound pause needs actual independent control completion, never ordinary Applied/gameplay credit");
    }
    public static void requireMapUnavailable(ActionReceipt first){
        require(first.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.Rejected rejected
                &&rejected.reason().equals(MAP_UNAVAILABLE),"only original terminal map-unavailable rejection permits the bounded recovery branch");
        var ack=first.ack().orElseThrow(()->new IllegalArgumentException("terminal pause rejection lacks its actual original ACK"));
        require(!ack.nativeOk()&&ack.outbound().isPresent(),"a transport absence or UNKNOWN is never a zero-enqueue native rejection");
        JsonNode raw=StrictJson.parse(ack.originalFrame().bytes());
        require(raw.has("error")&&raw.get("error").isTextual()&&raw.get("error").textValue().equals(MAP_UNAVAILABLE),"original native error differs");
    }
    public List<ExactRef> references(){
        var all=new ArrayList<ExactRef>();all.add(proof);children.forEach(child->all.add(child.canonicalReceipt()));all.addAll(originals);
        return all.stream().distinct().toList();
    }
    public byte[] encode(){
        ObjectNode row=StrictJson.object().put("schema",SCHEMA).put("kind",kind().name()).put("mode",mode.name());
        row.put("parent_command_base64",Base64.getEncoder().encodeToString(ActionCodec.encodeCommand(parent)));row.set("after",ProposalLifecycleCodec.observation(after));row.set("proof",proof.toJson());
        var list=row.putArray("children");for(Child child:children){var c=list.addObject().put("action_id",child.actionId()).put("body_sha256",child.bodySha256());c.set("canonical_receipt",child.canonicalReceipt().toJson());}
        var refs=row.putArray("originals");originals.forEach(ref->refs.add(ref.toJson()));byte[] result=StrictJson.canonical(row);
        require(result.length<=2*1024*1024,"finite original control DATA exceeded");return result;
    }
    public static ControlSequenceObservation decode(byte[] bytes){
        require(bytes!=null&&bytes.length<=2*1024*1024,"bounded control DATA required");
        ObjectNode row=StrictJson.object(StrictJson.parse(bytes),Set.of("schema","kind","mode","parent_command_base64","after","proof","children","originals"));
        require(SCHEMA.equals(StrictJson.text(row.get("schema")))&&Kind.PAUSE_WITH_SOURCE_BOUND_RETRY.name().equals(StrictJson.text(row.get("kind"))),"unsupported control sequence kind");
        require(row.get("children").isArray()&&row.get("children").size()<=2&&row.get("originals").isArray()&&row.get("originals").size()<=64,"finite control locator lists required");
        var children=new ArrayList<Child>();for(JsonNode node:row.get("children")){
            var child=StrictJson.object(node,Set.of("action_id","body_sha256","canonical_receipt"));children.add(new Child(StrictJson.text(child.get("action_id")),StrictJson.text(child.get("body_sha256")),ExactRef.fromJson(child.get("canonical_receipt"))));}
        var refs=new ArrayList<ExactRef>();row.get("originals").forEach(ref->refs.add(ExactRef.fromJson(ref)));
        String encoded=StrictJson.text(row.get("parent_command_base64"));byte[] parentBytes=Base64.getDecoder().decode(encoded);
        require(Base64.getEncoder().encodeToString(parentBytes).equals(encoded),"single canonical original command encoding required");
        return new ControlSequenceObservation(ActionCodec.decodeCommand(parentBytes),Mode.valueOf(StrictJson.text(row.get("mode"))),
                ProposalLifecycleCodec.decodeObservation(row.get("after")),ExactRef.fromJson(row.get("proof")),children,refs);
    }
}
