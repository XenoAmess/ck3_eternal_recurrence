package org.xar.ck3.control.application.planning.governance;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;

/** Persisted opening lifecycle identities are exact; unavailable state cannot decode as a completed gate. */
public final class GovernanceOpeningDocument {
    private GovernanceOpeningDocument() { }
    public static final String SCHEMA="xar.java-opening-gate/v2";
    public record Document(ObservationIdentity observed,G2Source source,String sessionId,OpeningStage stage,
            Optional<ExactRef> actionReceipt,Optional<CheckpointFact> checkpoint,List<ExactRef> originals,
            Optional<ExactRef> preparedCommand,Optional<ObservationIdentity> existingObserved) {
        public Document(ObservationIdentity observed,G2Source source,String sessionId,OpeningStage stage,Optional<ExactRef> actionReceipt,
                Optional<CheckpointFact> checkpoint,List<ExactRef> originals) {this(observed,source,sessionId,stage,actionReceipt,checkpoint,originals,Optional.empty(),Optional.empty());}
        public Document {
            Objects.requireNonNull(observed);Objects.requireNonNull(source);StrictJson.text(sessionId);Objects.requireNonNull(stage);
            Objects.requireNonNull(actionReceipt);Objects.requireNonNull(checkpoint);Objects.requireNonNull(preparedCommand);Objects.requireNonNull(existingObserved);originals=List.copyOf(originals);
            StrictJson.require(observed.machineId().equals(source.machineId()) && !originals.isEmpty() && originals.size()<=64
                    && originals.stream().allMatch(ref->ref.bytes()>0) && originals.stream().distinct().count()==originals.size(),
                    "full opening observation/source and original evidence required");
            StrictJson.require(stage==OpeningStage.AWAIT_SUBMIT || stage==OpeningStage.COMPLETE || actionReceipt.isPresent() || preparedCommand.isPresent(),
                    "pending opening lifecycle requires its original authoritative action receipt");
            StrictJson.require(stage!=OpeningStage.AWAIT_SUBMIT || actionReceipt.isEmpty() && preparedCommand.isEmpty() && checkpoint.isEmpty(),
                    "fresh opening gate cannot discard or contain a prior action/checkpoint");
            StrictJson.require(stage!=OpeningStage.COMPLETE || actionReceipt.isPresent()
                    && (checkpoint.isPresent() || preparedCommand.isPresent()) || existingObserved.isPresent(),
                    "complete opening needs its consumed original action/command, checkpoint or following-turn existing-focus evidence");
            StrictJson.require(stage!=OpeningStage.AWAIT_CONSUMPTION || actionReceipt.isPresent(),
                    "opening consumption requires its actual settled focus receipt; a prepared command is insufficient");
            if(existingObserved.isPresent()) {
                var value=existingObserved.orElseThrow();
                StrictJson.require(actionReceipt.isEmpty() && preparedCommand.isEmpty() && checkpoint.isEmpty()
                        && (stage==OpeningStage.AWAIT_SUBMIT || stage==OpeningStage.COMPLETE),
                        "existing-focus observation cannot substitute for a submitted focus receipt/checkpoint");
                StrictJson.require(value.machineId().equals(observed.machineId())
                        && value.frame().episodeRunId().equals(observed.frame().episodeRunId())
                        && value.frame().identity().player().equals(observed.frame().identity().player())
                        && value.frame().identity().dateRaw().compareTo(observed.frame().identity().dateRaw())>=0,
                        "existing-focus observation crossed its actual machine/episode/actor or moved backwards");
            }
            checkpoint.ifPresent(value->StrictJson.require(actionReceipt.isPresent()
                    && value.observed().machineId().equals(observed.machineId()) && value.observed().game().equals(observed.game())
                    && value.observed().frame().episodeRunId().equals(observed.frame().episodeRunId())
                    && value.observed().frame().identity().player().equals(observed.frame().identity().player()),
                    "opening checkpoint crossed its actual physical Game/episode/actor"));
        }
    }
    public static byte[] encode(Document document) {
        ObjectNode row=StrictJson.object().put("schema",SCHEMA).put("session_id",document.sessionId()).put("stage",document.stage().name());
        row.set("observation",ProposalLifecycleCodec.observation(document.observed()));row.set("source",ProposalLifecycleCodec.source(document.source()));
        row.set("action_receipt",document.actionReceipt().map(ExactRef::toJson).orElse(null));
        row.set("prepared_command",document.preparedCommand().map(ExactRef::toJson).orElse(null));
        row.set("existing_observed",document.existingObserved().map(ProposalLifecycleCodec::observation).orElse(null));
        if(document.checkpoint().isEmpty())row.putNull("checkpoint");
        else {
            CheckpointFact checkpoint=document.checkpoint().orElseThrow();ObjectNode value=row.putObject("checkpoint").put("action_id",checkpoint.actionId());
            value.set("observation",ProposalLifecycleCodec.observation(checkpoint.observed()));value.set("actual_receipt",checkpoint.actualReceipt().toJson());
        }
        var originals=row.putArray("originals");document.originals().forEach(ref->originals.add(ref.toJson()));return StrictJson.canonical(row);
    }
    public static Document decode(byte[] original) {
        ObjectNode row=StrictJson.object(StrictJson.parse(original),Set.of("schema","session_id","stage","observation","source","action_receipt","checkpoint","originals","prepared_command","existing_observed"));
        StrictJson.require(StrictJson.text(row.get("schema")).equals(SCHEMA),"explicit opening document schema required");
        Optional<ExactRef> action=row.get("action_receipt").isNull()?Optional.empty():Optional.of(ExactRef.fromJson(row.get("action_receipt")));
        Optional<CheckpointFact> checkpoint=Optional.empty();
        if(!row.get("checkpoint").isNull()) {
            ObjectNode value=StrictJson.object(row.get("checkpoint"),Set.of("action_id","observation","actual_receipt"));
            checkpoint=Optional.of(new CheckpointFact(StrictJson.text(value.get("action_id")),
                    ProposalLifecycleCodec.decodeObservation(value.get("observation")),ExactRef.fromJson(value.get("actual_receipt"))));
        }
        StrictJson.require(row.get("originals").isArray(),"opening original evidence must be an array");List<ExactRef> originals=new ArrayList<>();
        row.get("originals").forEach(value->originals.add(ExactRef.fromJson(value)));
        return new Document(ProposalLifecycleCodec.decodeObservation(row.get("observation")),G2Wire.source(row.get("source")),
                StrictJson.text(row.get("session_id")),OpeningStage.valueOf(StrictJson.text(row.get("stage"))),action,checkpoint,originals,row.get("prepared_command").isNull()?Optional.empty():Optional.of(ExactRef.fromJson(row.get("prepared_command"))),
                row.get("existing_observed").isNull()?Optional.empty():Optional.of(ProposalLifecycleCodec.decodeObservation(row.get("existing_observed"))));
    }
    public static void requireSameEpisode(Document document,ObservationIdentity actual,G2Source source) {
        StrictJson.require(document.source().equals(source) && document.observed().machineId().equals(actual.machineId())
                && document.observed().frame().episodeRunId().equals(actual.frame().episodeRunId())
                && document.observed().frame().identity().player().equals(actual.frame().identity().player())
                && document.observed().frame().identity().dateRaw().compareTo(actual.frame().identity().dateRaw())<=0,
                "opening document crossed its full source/episode/actor or moved backwards in date");
    }
}
