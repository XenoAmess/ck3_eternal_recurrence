package org.xar.ck3.control.application.planning.campaign;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.LifecycleIdentity;
import org.xar.ck3.control.application.action.LifecycleIdentityCodec;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Canonical one-life state import. Initial entry and actual terminal phase have distinct source contracts. */
public final class CrossRunPlanningDomain implements DomainBodies.Verifier {
    public static final String CONTRACT_SCHEMA="xar.ck3.cross-run-planning-state/v1";
    public static final String INPUT_SCHEMA="xar.ck3.cross-run-planning-input/v2";
    public static final int MAX_INPUT_BYTES=64<<10;
    public enum Mode { INITIAL_ENTRY, CANONICAL_TERMINAL }
    public sealed interface Origin permits EntryOrigin,TerminalOrigin {
        Mode mode();G2Source source();String machineId();String episodeRunId();List<ExactRef> evidence();
    }
    /** Source file absence is a real configured-path observation, usable only with the private initial entry proof. */
    public record EntryOrigin(ObservationIdentity frame,G2Source source,ExactRef entryBasis,Path originalStrategy,
            Optional<FileWitness> sourceFile) implements Origin {
        public EntryOrigin {
            Objects.requireNonNull(frame);Objects.requireNonNull(source);nonempty(entryBasis);absolute(originalStrategy);Objects.requireNonNull(sourceFile);
            StrictJson.require(frame.machineId().equals(source.machineId()),"initial strategy source machine differs");
            sourceFile.ifPresent(witness->{nonempty(witness.reference());StrictJson.require(Path.of(witness.reference().path()).equals(originalStrategy),"original strategy file differs from configured source path");});
        }
        @Override public Mode mode(){return Mode.INITIAL_ENTRY;}
        @Override public String machineId(){return frame.machineId();}
        @Override public String episodeRunId(){return frame.frame().episodeRunId();}
        @Override public List<ExactRef> evidence(){var refs=new LinkedHashSet<ExactRef>();refs.add(entryBasis);sourceFile.ifPresent(value->refs.add(value.reference()));return List.copyOf(refs);}
    }
    /** These are independently bound actual originals, not an ACK interpreted as death or score. */
    public record TerminalReferences(ExactRef terminal,ExactRef score,ExactRef history,ExactRef nativeSnapshot,ExactRef currentDriver) {
        public TerminalReferences{for(ExactRef ref:List.of(terminal,score,history,nativeSnapshot,currentDriver))nonempty(ref);}
        public List<ExactRef> evidence(){return List.of(terminal,score,history,nativeSnapshot,currentDriver);}
    }
    public record TerminalOrigin(LifecycleIdentity identity,G2Source source,String actionId,TerminalReferences references) implements Origin {
        public TerminalOrigin{Objects.requireNonNull(identity);Objects.requireNonNull(source);StrictJson.text(actionId);Objects.requireNonNull(references);StrictJson.require(identity.machineId().equals(source.machineId()),"terminal source machine differs");}
        @Override public Mode mode(){return Mode.CANONICAL_TERMINAL;}
        @Override public String machineId(){return identity.machineId();}
        @Override public String episodeRunId(){return identity.subject().episodeRunId();}
        @Override public List<ExactRef> evidence(){return references.evidence();}
    }
    public record Input(String evidenceId,Origin origin,ExactRef previousState,Instant producedAt) {
        public Input{StrictJson.text(evidenceId);Objects.requireNonNull(origin);nonempty(previousState);Objects.requireNonNull(producedAt);}
        public Mode mode(){return origin.mode();}
        public String episodeRunId(){return origin.episodeRunId();}
        public List<ExactRef> evidence(){var refs=new LinkedHashSet<ExactRef>();refs.add(previousState);refs.addAll(origin.evidence());return List.copyOf(refs);}
    }
    public record StateDocument(ExactRef reference,byte[] bytes) {
        public StateDocument{nonempty(reference);bytes=Objects.requireNonNull(bytes).clone();StrictJson.require(bytes.length<=CrossRunPlanning.MAX_BYTES&&reference.bytes()==bytes.length&&reference.sha256().equals(ActionCodec.sha256(bytes)),"exact bounded original strategy state required");CrossRunPlanning.decodeState(bytes);}
        @Override public byte[] bytes(){return bytes.clone();}
        public CrossRunPlanning.State state(){return CrossRunPlanning.decodeState(bytes);}
    }
    public sealed interface Captured permits Initialized,Recorded {Input input();StateDocument previous();}
    /** Actual existing file, or actual configured absence plus the canonical private fresh-entry original. */
    public record Initialized(Input input,StateDocument previous) implements Captured {
        public Initialized{capture(input,previous,Mode.INITIAL_ENTRY);}
    }
    /** Complete pre-terminal history is replayed by the sole shared reducer; the actual result is published once. */
    public record Recorded(Input input,StateDocument previous,List<OpportunityJson.Obj> completeOriginalRows,
            OpportunityJson.Obj actualTerminal) implements Captured {
        public Recorded{capture(input,previous,Mode.CANONICAL_TERMINAL);completeOriginalRows=List.copyOf(completeOriginalRows);Objects.requireNonNull(actualTerminal);CrossRunStrategySource.terminal(previous.state(),input.episodeRunId(),completeOriginalRows,actualTerminal,input.producedAt());}
    }
    @FunctionalInterface public interface ActualCapturePort {
        Captured capture(ContinuityStorePort.Session originalSession,WriterContracts.Head actualHead,Input input)throws IOException;
    }
    @FunctionalInterface public interface BorrowedSessionPort {ContinuityStorePort.Session current()throws IOException;}
    public sealed interface StateRead permits KnownState,MissingState { }
    public record KnownState(CrossRunPlanning.State state,DomainBodies.BodyRef body,ExactRef canonicalHead) implements StateRead {
        public KnownState{Objects.requireNonNull(state);Objects.requireNonNull(body);nonempty(canonicalHead);requireSlot(body.slot(),body.contractSchema());}
        public CrossRunPlanning.Plan nextPlan(){return state.nextRunPlan();}
    }
    public record MissingState(DomainBodies.Unavailable original) implements StateRead {public MissingState{Objects.requireNonNull(original);}}
    private final BorrowedSessionPort sessions;private final ActualCapturePort actual;
    /** Runtime construction uses the concrete RootCrossRunPlanning.Prepared. Tests may exercise this verifier seam independently. */
    public CrossRunPlanningDomain(BorrowedSessionPort sessions,ActualCapturePort actual){this.sessions=Objects.requireNonNull(sessions);this.actual=Objects.requireNonNull(actual);}
    public DomainBodies.Registration registration(List<ExactRef> actualProducerSources){return new DomainBodies.Registration(DomainBodies.Slot.CROSS_RUN_PLANNING,CONTRACT_SCHEMA,CrossRunPlanning.MAX_BYTES,actualProducerSources,this);}
    public StateRead read(ContinuityStorePort.Session originalSession)throws IOException{
        Objects.requireNonNull(originalSession);DomainBodies.Read read=originalSession.readDomain(DomainBodies.Slot.CROSS_RUN_PLANNING);
        if(read instanceof DomainBodies.Unavailable missing)return new MissingState(missing);var known=(DomainBodies.Available)read;requireSlot(known.reference().slot(),known.reference().contractSchema());return new KnownState(CrossRunPlanning.decodeState(known.canonicalBody()),known.reference(),known.head());
    }
    public static CrossRunPlanning.State produce(Captured actual){Objects.requireNonNull(actual);return switch(actual){case Initialized value->value.previous().state();case Recorded value->CrossRunStrategySource.terminal(value.previous().state(),value.input().episodeRunId(),value.completeOriginalRows(),value.actualTerminal(),value.input().producedAt());};}
    @Override public String verify(ContinuityState predecessor,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] original)throws IOException{throw new IOException("cross-run source verification requires the original same-lock Head");}
    @Override public String verify(WriterContracts.Head head,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] original)throws IOException{
        Objects.requireNonNull(head);Objects.requireNonNull(previous);Objects.requireNonNull(request);var same=Objects.requireNonNull(sessions.current());var current=same.head();
        StrictJson.require(current.digest().equals(head.digest())&&current.documents().equals(head.documents())&&current.absent().equals(head.absent())&&current.indexRepairs().equals(head.indexRepairs())&&current.snapshotNeedsRecovery()==head.snapshotNeedsRecovery(),"cross-run same-writer source Head changed");
        requireSlot(request.slot(),request.contractSchema());StrictJson.require(previous.equals(DomainBodies.reference(current.state(),DomainBodies.Slot.CROSS_RUN_PLANNING)),"actual cross-run predecessor differs");Input input=decodeInput(request.producerInput());
        StrictJson.require(head.state().machineId().equals(input.origin().machineId())&&request.evidenceId().equals(input.evidenceId())&&request.evidence().equals(input.evidence()),"cross-run request crossed exact source/evidence closure");
        if(input.mode()==Mode.INITIAL_ENTRY)StrictJson.require(previous.isEmpty(),"known cross-run state cannot be initialized or reset again");
        else{var before=previous.orElseThrow(()->new IllegalArgumentException("missing state is not an empty prior life"));requireSlot(before.slot(),before.contractSchema());StrictJson.require(before.payload().equals(input.previousState()),"canonical terminal does not reduce the actual prior strategy body");}
        Captured captured=Objects.requireNonNull(actual.capture(same,current,input));StrictJson.require(captured.input().equals(input),"actual cross-run capture changed original input");var expected=produce(captured);var candidate=new StateDocument(request.originalBody(),original);StrictJson.require(candidate.state().equals(expected),"actual original producer state differs from canonical candidate");
        ObjectNode proof=StrictJson.object().put("canonical_head",head.digest());proof.set("input",inputJson(input));proof.put("expected_state_sha256",ActionCodec.sha256(CrossRunPlanning.encodeState(expected)));return ContinuityJson.digest(proof);
    }
    public static byte[] encodeInput(Input input){return StrictJson.canonical(inputJson(input),MAX_INPUT_BYTES);}
    public static Input decodeInput(byte[] original){ObjectNode row=StrictJson.object(StrictJson.parse(original,MAX_INPUT_BYTES),Set.of("schema","evidence_id","origin","previous_state","produced_at"));StrictJson.require(INPUT_SCHEMA.equals(StrictJson.text(row.get("schema"))),"exact cross-run input/v2 required");return new Input(StrictJson.text(row.get("evidence_id")),origin(row.get("origin")),ExactRef.fromJson(row.get("previous_state")),Instant.parse(StrictJson.text(row.get("produced_at"))));}
    private static ObjectNode inputJson(Input input){Objects.requireNonNull(input);ObjectNode row=StrictJson.object().put("schema",INPUT_SCHEMA).put("evidence_id",input.evidenceId()).put("produced_at",input.producedAt().toString());row.set("origin",originJson(input.origin()));row.set("previous_state",input.previousState().toJson());return row;}
    private static ObjectNode originJson(Origin origin){ObjectNode row=StrictJson.object().put("mode",origin.mode().name());row.set("source",ProposalLifecycleCodec.source(origin.source()));if(origin instanceof EntryOrigin entry){row.set("frame",ProposalLifecycleCodec.observation(entry.frame()));row.set("entry_basis",entry.entryBasis().toJson());row.put("original_strategy_path",entry.originalStrategy().toString());if(entry.sourceFile().isPresent()){var witness=entry.sourceFile().orElseThrow();ObjectNode file=StrictJson.object();file.set("ref",witness.reference().toJson());file.put("identity_schema",FileStatIdentity.SCHEMA);file.set("identity",witness.identity().toJson());row.set("source_file",file);}else row.putNull("source_file");}else{TerminalOrigin terminal=(TerminalOrigin)origin;row.set("identity",LifecycleIdentityCodec.encode(terminal.identity()));row.put("action_id",terminal.actionId());ObjectNode refs=row.putObject("references");var value=terminal.references();refs.set("terminal",value.terminal().toJson());refs.set("score",value.score().toJson());refs.set("history",value.history().toJson());refs.set("native_snapshot",value.nativeSnapshot().toJson());refs.set("current_driver",value.currentDriver().toJson());}return row;}
    private static Origin origin(com.fasterxml.jackson.databind.JsonNode raw){StrictJson.require(raw instanceof ObjectNode,"cross-run origin object required");Mode mode=Mode.valueOf(StrictJson.text(raw.get("mode")));if(mode==Mode.INITIAL_ENTRY){ObjectNode row=StrictJson.object(raw,Set.of("mode","source","frame","entry_basis","original_strategy_path","source_file"));Optional<FileWitness> file=Optional.empty();if(!row.get("source_file").isNull()){ObjectNode witness=StrictJson.object(row.get("source_file"),Set.of("ref","identity_schema","identity"));file=Optional.of(new FileWitness(ExactRef.fromJson(witness.get("ref")),FileStatIdentity.fromJson(witness.get("identity"),StrictJson.text(witness.get("identity_schema")))));}return new EntryOrigin(ProposalLifecycleCodec.decodeObservation(row.get("frame")),G2Wire.source(row.get("source")),ExactRef.fromJson(row.get("entry_basis")),Path.of(StrictJson.text(row.get("original_strategy_path"))),file);}ObjectNode row=StrictJson.object(raw,Set.of("mode","source","identity","action_id","references"));ObjectNode refs=StrictJson.object(row.get("references"),Set.of("terminal","score","history","native_snapshot","current_driver"));return new TerminalOrigin(LifecycleIdentityCodec.decode(row.get("identity")),G2Wire.source(row.get("source")),StrictJson.text(row.get("action_id")),new TerminalReferences(ExactRef.fromJson(refs.get("terminal")),ExactRef.fromJson(refs.get("score")),ExactRef.fromJson(refs.get("history")),ExactRef.fromJson(refs.get("native_snapshot")),ExactRef.fromJson(refs.get("current_driver"))));}
    private static void capture(Input input,StateDocument previous,Mode expected){Objects.requireNonNull(input);Objects.requireNonNull(previous);StrictJson.require(input.mode()==expected&&input.previousState().equals(previous.reference()),"actual source state/capture origin differs");}
    private static void requireSlot(DomainBodies.Slot slot,String schema){StrictJson.require(slot==DomainBodies.Slot.CROSS_RUN_PLANNING&&CONTRACT_SCHEMA.equals(schema),"exact cross-run domain contract required");}
    private static void nonempty(ExactRef ref){Objects.requireNonNull(ref);StrictJson.require(ref.bytes()>0,"nonempty original evidence required");}
    private static void absolute(Path path){Objects.requireNonNull(path);StrictJson.require(path.isAbsolute()&&path.normalize().equals(path),"absolute normalized configured strategy path required");}
}
