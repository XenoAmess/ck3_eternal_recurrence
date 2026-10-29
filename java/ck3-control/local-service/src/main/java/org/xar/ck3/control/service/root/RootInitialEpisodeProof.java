package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.readiness.ReadinessArchive;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** The canonical fresh-entry proof only initializes new domain state. It grants no gameplay or restore admission. */
public final class RootInitialEpisodeProof {
    private final RootRuntimeContext context;
    private final GameplayEntryService.Admitted admitted;
    private final FrontendGameplayObservation observation;
    private final ObjectNode canonicalEntry;
    private final List<ExactRef> evidence;
    private RootInitialEpisodeProof(RootRuntimeContext context,GameplayEntryService.Admitted admitted,
            FrontendGameplayObservation observation,ObjectNode canonicalEntry,List<ExactRef> evidence) {
        this.context=context;this.admitted=admitted;this.observation=observation;
        this.canonicalEntry=canonicalEntry.deepCopy();this.evidence=List.copyOf(evidence);
    }
    public static RootInitialEpisodeProof require(RootRuntimeContext context,ContinuityStorePort.Session borrowed,
            GameplayEntryService.Admitted actual)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(actual);context.writer().requireSession(borrowed);
        StrictJson.require(actual.actual().state() instanceof ActionState.Settled settled
                && settled.settlement() instanceof ActionState.GameplayEntered,"actual settled initial GameplayEntered is required");
        var observation=((ActionState.GameplayEntered)((ActionState.Settled)actual.actual().state()).settlement()).observation();
        ObjectNode entry=borrowed.head().state().toJson().get(WriterContracts.GAMEPLAY_ENTRY_FIELD) instanceof ObjectNode value?value:null;
        StrictJson.require(entry!=null,"canonical committed fresh entry is absent");
        var refs=new LinkedHashSet<ExactRef>(observation.references());
        refs.add(ExactRef.fromJson(entry.get("start_receipt")));refs.add(ExactRef.fromJson(entry.get("entry_basis")));
        refs.add(ExactRef.fromJson(entry.get("full_driver")));refs.add(ExactRef.fromJson(entry.get("driver_facts")));
        ObjectNode source=StrictJson.object(entry.get("source"),java.util.Set.of("implementation","policy","environment","machine_id"));
        for(String key:List.of("implementation","policy","environment"))refs.add(ExactRef.fromJson(source.get(key)));
        var result=new RootInitialEpisodeProof(context,actual,observation,entry,List.copyOf(refs));result.requireCurrent(borrowed);return result;
    }
    public ObservationIdentity currentObservation() { return observation.after(); }
    public DriverObservationAssembler.Complete frame() { return admitted.driver().first(); }
    public G2Source source() { return context.source(); }
    public String sessionId() { return context.game().sessionId(); }
    public List<ExactRef> evidence() { return evidence; }
    public ActionReceipt actualStart() { return admitted.actual(); }
    public WriterContracts.Receipt actualEntry() { return admitted.entry(); }
    public DriverBootstrap.Adopted adopted() { return admitted.driver(); }
    public String episodeId() { return observation.after().frame().episodeRunId(); }
    public void requireInitializationPredecessor(ContinuityStorePort.Session same,WriterContracts.Head actual)throws IOException {
        requireCurrent(same);context.writer().requireSession(same);
        StrictJson.require(actual.digest().equals(same.head().digest()),"live initialization requires the actual current import predecessor");
        requireInitialShape(admitted.entry().head(),actual.state());
    }
    /** Durable original input for a domain initializer. Replaying this never asserts that the old Game is still live. */
    public ExactRef preserveOriginal(ContinuityStorePort.Session borrowed)throws IOException {
        requireCurrent(borrowed);var row=StrictJson.object();row.put("schema","xar.java.initial-domain-originals/v1");
        row.put("machine_id",context.game().machineId());row.set("canonical_entry",canonicalEntry.deepCopy());
        row.set("entry_head",admitted.entry().head().toJson());row.put("entry_event_identity",admitted.entry().eventIdentity());
        row.set("start_receipt",context.archive().withSession(borrowed).receiptReferenceOf(actualStart()).toJson());
        row.set("full_driver",admitted.driver().seed().fullDriver().toJson());
        return context.archive().withSession(borrowed).preserveMaterial(new RawJson(ContinuityJson.canonical(row)));
    }
    public static Original replayOriginal(RootRuntimeContext context,ContinuityStorePort.Session borrowed,ExactRef basis)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(basis);context.writer().requireSession(borrowed);
        var archive=context.archive().withSession(borrowed);RawJson raw=archive.loadMaterial(basis);
        StrictJson.require(archive.materialReferenceOf(raw).equals(basis),"initial original basis bytes differ");
        ObjectNode row=StrictJson.object(ContinuityJson.parseObject(raw.bytes(),WriterContracts.MAX_PIN_BYTES),
                java.util.Set.of("schema","machine_id","canonical_entry","entry_head","entry_event_identity","start_receipt","full_driver"));
        StrictJson.require("xar.java.initial-domain-originals/v1".equals(StrictJson.text(row.get("schema")))
                && context.game().machineId().equals(StrictJson.text(row.get("machine_id"))),"original initializer belongs to another schema or machine");
        StrictJson.require(row.get("canonical_entry") instanceof ObjectNode,"complete original canonical entry required");
        ObjectNode entry=(ObjectNode)row.get("canonical_entry");
        var head=org.xar.ck3.control.continuity.ContinuityState.fromJson(row.get("entry_head"),context.game().machineId());
        borrowed.requireHistoricalState(head.sequence(),ContinuityJson.digest(head.toJson()));
        StrictJson.require(ContinuityJson.same(entry,head.toJson().get(WriterContracts.GAMEPLAY_ENTRY_FIELD))
                && ContinuityJson.same(entry,borrowed.head().state().toJson().get(WriterContracts.GAMEPLAY_ENTRY_FIELD))
                && StrictJson.text(row.get("entry_event_identity")).equals(StrictJson.text(head.toJson().get("last_event_identity"))),
                "original initializer is not the surviving canonical first-entry commit");
        WriterContracts.requireDigest(StrictJson.text(row.get("entry_event_identity")));
        ExactRef receiptRef=ExactRef.fromJson(row.get("start_receipt"));ActionReceipt start=archive.loadReceipt(receiptRef);
        var canonical=ContinuityActionJournal.lookup(borrowed.head().state(),start.command().actionId(),archive)
                .orElseThrow(()->new IOException("original initializer Start is absent from the surviving action chain"));
        StrictJson.require(archive.receiptReferenceOf(start).equals(receiptRef) && receiptRef.equals(ExactRef.fromJson(entry.get("start_receipt")))
                && Arrays.equals(ActionReceiptCodec.encodeReceipt(start,archive),ActionReceiptCodec.encodeReceipt(canonical,archive))
                && start.command().actionId().equals(StrictJson.text(entry.get("action_id")))
                && start.bodySha256().equals(StrictJson.text(entry.get("action_body_sha256")))
                && start.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.GameplayEntered,
                "original initializer lacks its exact surviving settled Start");
        var settled=(ActionState.Settled)start.state();var observation=((ActionState.GameplayEntered)settled.settlement()).observation();
        ActionEffects.validate(start.command(),settled.attempt(),settled.settlement());
        context.bindings().actualArchivedVerifier(start.command().operation()).orElseThrow(()->new IOException("original Start replay is not installed"))
                .verifier().verify(borrowed.head(),start,archive);
        context.semanticVerifier().verify(borrowed,new SessionIdentity(start.command().source().machineId(),start.command().origin().game(),start.command().sessionId()),observation.semanticEvidence());
        ExactRef full=ExactRef.fromJson(row.get("full_driver"));
        StrictJson.require(full.equals(ExactRef.fromJson(entry.get("full_driver")))
                && full.equals(ExactRef.fromJson(head.toJson().get(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD))),"original initial Driver baseline differs");
        var driver=org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.decodeComplete(
                context.archive().readArtifact(borrowed,full,ReadinessArchive.Role.DRIVER.maximumBytes()));
        StrictJson.require(driver.commandHistory().isEmpty() && driver.session().bridgePid()==start.command().origin().game().pid()
                && driver.session().actorId().equals(observation.after().frame().identity().player())
                && driver.session().episodeRunId().equals(observation.after().frame().episodeRunId()),"original first Driver is not the actual empty fresh branch");
        var refs=new LinkedHashSet<ExactRef>(observation.references());refs.add(basis);refs.add(receiptRef);refs.add(full);
        for(ExactRef ref:refs){var pin=borrowed.capturePin(ref,WriterContracts.MAX_PIN_BYTES);borrowed.verifyPin(pin);}
        return new Original(context,basis,start,observation,full,List.copyOf(refs),head);
    }
    public static final class Original {
        private final RootRuntimeContext context;
        private final ExactRef basis,firstDriver;
        private final ActionReceipt start;
        private final FrontendGameplayObservation observation;
        private final List<ExactRef> evidence;
        private final org.xar.ck3.control.continuity.ContinuityState entryHead;
        private Original(RootRuntimeContext context,ExactRef basis,ActionReceipt start,FrontendGameplayObservation observation,ExactRef firstDriver,List<ExactRef> evidence,
                org.xar.ck3.control.continuity.ContinuityState entryHead) {
            this.context=context;this.basis=basis;this.start=start;this.observation=observation;this.firstDriver=firstDriver;this.evidence=evidence;this.entryHead=entryHead;
        }
        public ExactRef basis() { return basis; }
        public ActionReceipt actualStart() { return start; }
        public ObservationIdentity observation() { return observation.after(); }
        public G2Source source() { return start.command().source(); }
        public String sessionId() { return start.command().sessionId(); }
        public String episodeId() { return observation.after().frame().episodeRunId(); }
        public ExactRef firstDriver() { return firstDriver; }
        public List<ExactRef> evidence() { return evidence; }
        public org.xar.ck3.control.continuity.ContinuityState entryHead() { return entryHead; }
        /** Validate the actual import predecessor, including historical reducer replay, rather than requiring the old Game to be alive. */
        public void requireInitializationPredecessor(ContinuityStorePort.Session same,WriterContracts.Head actual)throws IOException {
            context.writer().requireSession(same);Objects.requireNonNull(actual);
            var state=actual.state();
            same.requireHistoricalState(state.sequence(),ContinuityJson.digest(state.toJson()));
            requireInitialShape(entryHead,state);
        }
    }
    public void requireCurrent(ContinuityStorePort.Session borrowed)throws IOException {
        context.writer().requireSession(borrowed);ActionReceipt start=admitted.actual();var command=start.command();
        context.requireCurrent(command.deadline());
        StrictJson.require(command.source().equals(context.source()) && command.sessionId().equals(sessionId())
                && command.origin() instanceof CommandOrigin.Frontend && command.origin().game().equals(context.game().generation())
                && admitted.driver().source().equals(source()) && admitted.driver().session().game().equals(context.game().generation())
                && admitted.driver().session().sessionId().equals(sessionId())
                && admitted.driver().first().identity().equals(currentObservation()),"initialization crossed the actual initial physical Game");
        var state=borrowed.head().state().toJson();var original=admitted.entry().head().toJson();
        var originalState=admitted.entry().head();
        borrowed.requireHistoricalState(originalState.sequence(),ContinuityJson.digest(original));
        StrictJson.require(initialImportShape(originalState).equals(initialImportShape(borrowed.head().state())),
                "fresh domain initialization followed a non-initial state transition");
        StrictJson.require(admitted.entry().disposition()!=WriterContracts.Disposition.NO_CHANGE
                && original.get("last_event_identity")!=null
                && admitted.entry().eventIdentity().equals(StrictJson.text(original.get("last_event_identity")))
                && ContinuityJson.same(canonicalEntry,state.get(WriterContracts.GAMEPLAY_ENTRY_FIELD))
                && ContinuityJson.same(canonicalEntry,original.get(WriterContracts.GAMEPLAY_ENTRY_FIELD))
                && admitted.driver().seed().fullDriver().equals(ExactRef.fromJson(state.get(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD)))
                && admitted.driver().seed().fullDriver().equals(ExactRef.fromJson(canonicalEntry.get("full_driver")))
                && command.actionId().equals(StrictJson.text(canonicalEntry.get("action_id")))
                && start.bodySha256().equals(StrictJson.text(canonicalEntry.get("action_body_sha256"))),
                "fresh initializer does not hold the surviving canonical initial-entry commit");
        var archive=context.archive().withSession(borrowed);
        var canonical=ContinuityActionJournal.lookup(borrowed.head().state(),command.actionId(),archive)
                .orElseThrow(()->new IOException("original initial Start is not in the canonical action chain"));
        StrictJson.require(Arrays.equals(ActionReceiptCodec.encodeReceipt(start,archive),ActionReceiptCodec.encodeReceipt(canonical,archive))
                && archive.receiptReferenceOf(start).equals(ExactRef.fromJson(canonicalEntry.get("start_receipt"))),
                "fresh initializer cites another action receipt");
        var settled=(ActionState.Settled)start.state();ActionEffects.validate(command,settled.attempt(),settled.settlement());
        context.bindings().actualArchivedVerifier(command.operation()).orElseThrow(()->new IOException("actual initial Start replay is not installed"))
                .verifier().verify(borrowed.head(),start,archive);
        context.semanticVerifier().verify(borrowed,new SessionIdentity(context.game().machineId(),context.game().generation(),sessionId()),observation.semanticEvidence());
        var actual=context.transport().latestObservedSnapshot().orElseThrow(()->new IOException("actual initial native snapshot disappeared"));
        byte[] originalPacket=context.archive().readArtifact(borrowed,observation.semanticEvidence().originalNativePacket(),ReadinessArchive.Role.NATIVE_PACKET.maximumBytes());
        StrictJson.require(actual.session().equals(admitted.driver().session()) && Arrays.equals(actual.originalPacket(),originalPacket),
                "actual initial native state changed before fresh domain initialization");
        for(ExactRef ref:evidence){var pin=borrowed.capturePin(ref,WriterContracts.MAX_PIN_BYTES);borrowed.verifyPin(pin);}
    }
    private static ObjectNode initialImportShape(org.xar.ck3.control.continuity.ContinuityState state) {
        ObjectNode result=state.toJson().deepCopy();
        result.remove(java.util.Set.of("sequence","last_event_identity",DomainBodies.FIELD));return result;
    }
    private static void requireInitialShape(org.xar.ck3.control.continuity.ContinuityState entry,
            org.xar.ck3.control.continuity.ContinuityState actual) {
        StrictJson.require(actual.sequence()>=entry.sequence() && initialImportShape(entry).equals(initialImportShape(actual)),
                "fresh initializer is outside the original entry and initial domain import chain");
    }
}
