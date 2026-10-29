package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.planning.governance.GovernanceOpeningDocument;
import org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.OpeningStage;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** One OPENING_GATE registration, bound once to Core, with actual canonical fresh-entry initialization. */
public final class GovernanceOpeningRuntime implements DomainBodies.Verifier {
    public record Sources(List<ExactRef> producers) {
        public Sources {
            producers=List.copyOf(producers);StrictJson.require(!producers.isEmpty() && producers.size()<=32
                    && producers.stream().allMatch(ref->ref.bytes()>0) && producers.stream().distinct().count()==producers.size(),
                    "exact bounded opening producer source closure required");
        }
    }
    @FunctionalInterface private interface CurrentInitial {void requireCurrent(ContinuityStorePort.Session same)throws IOException;}
    private record InitialData(ExactRef basis,org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity observation,
            org.xar.ck3.control.g2.common.G2Source source,String sessionId,List<ExactRef> evidence) {
        private InitialData {evidence=List.copyOf(evidence);}
    }
    private final Sources sources;
    private final DomainBodies.Registration registration;
    private RootApplicationAssembly.Core core;
    private RootRuntimeContext context;
    private OpeningTransitions transitions;
    private GovernanceNextInitialization nextVerifier;
    public void bindNextVerifier(GovernanceNextInitialization actual){nextVerifier=Objects.requireNonNull(actual);}
    public GovernanceOpeningRuntime(Sources sources) { this.sources=Objects.requireNonNull(sources); this.registration=new DomainBodies.Registration(DomainBodies.Slot.OPENING_GATE,GovernanceOpeningDocument.SCHEMA,1_048_576,sources.producers(),this); }
    public Sources sources() { return sources; }
    public DomainBodies.Registration registration() { return registration; }
    public synchronized void bind(RootApplicationAssembly.Core actual) {
        Objects.requireNonNull(actual);StrictJson.require(core==null,"opening runtime must bind the one Core exactly once");
        StrictJson.require(actual.archive().writer()==actual.writer(),"opening must retain the original writer/archive");core=actual;
    }
    private synchronized RootApplicationAssembly.Core core()throws IOException {
        if(core==null)throw new IOException("opening registration is not yet bound to the actual Core");return core;
    }
    public synchronized void installContext(RootRuntimeContext actual)throws IOException {
        StrictJson.require(Objects.requireNonNull(actual).core()==core(),"opening source cannot bind another Core/writer");context=actual;transitions=new OpeningTransitions(actual,sources.producers());
    }
    public synchronized OpeningTransitions transitions() throws IOException {if(transitions==null)throw new IOException("actual opening transition producer not installed");return transitions;}
    private synchronized RootRuntimeContext context()throws IOException {
        if(context==null)throw new IOException("opening source lacks the actual installed context for durable original replay");return context;
    }
    /** Both observed day-zero and legacy initial entry use this same import algorithm; restore never clears the slot. */
    public WriterContracts.Receipt initialize(ContinuityStorePort.Session borrowed,RootInitialEpisodeProof actual)throws IOException {
        Objects.requireNonNull(actual);core().writer().requireSession(borrowed);actual.requireCurrent(borrowed);
        return initialize(borrowed,actual.preserveOriginal(borrowed),actual::requireCurrent);
    }
    public WriterContracts.Receipt initialize(ContinuityStorePort.Session borrowed,FreshCampaignContext actual)throws IOException {
        Objects.requireNonNull(actual);core().writer().requireSession(borrowed);
        StrictJson.require(actual.context()==context(),"fresh opening belongs to another installed Game");actual.requireCurrent(borrowed);
        return initialize(borrowed,actual.preserveOriginal(borrowed),actual::requireCurrent);
    }
    private WriterContracts.Receipt initialize(ContinuityStorePort.Session borrowed,ExactRef basis,CurrentInitial actual)throws IOException {
        var owner=core();owner.writer().requireSession(borrowed);actual.requireCurrent(borrowed);
        var old=borrowed.readDomain(DomainBodies.Slot.OPENING_GATE);
        if(!(old instanceof DomainBodies.Unavailable unavailable) || unavailable.reason()!=DomainBodies.Reason.UNIMPORTED)
            throw new IOException("fresh opening initialization requires the actual registered, never-imported slot; existing pending/restored state is preserved");
        var originalEntry=initial(borrowed,basis,borrowed.head());
        {
            var document=fresh(originalEntry);byte[] body=GovernanceOpeningDocument.encode(document);
            ExactRef original=owner.archive().preserveArtifact(borrowed,body,1_048_576);
            var request=request(originalEntry,original);var head=borrowed.head();var prepared=borrowed.previewImport(request);
            StrictJson.require(prepared.predecessor().digest().equals(head.digest()),"opening initialization crossed the actual locked head");
            actual.requireCurrent(borrowed);var committed=borrowed.commitImport(prepared);
            var read=borrowed.readDomain(DomainBodies.Slot.OPENING_GATE);
            StrictJson.require(read instanceof DomainBodies.Available available && available.reference().payload().equals(original)
                    && Arrays.equals(available.canonicalBody(),body) && committed.disposition()!=WriterContracts.Disposition.NO_CHANGE,
                    "opening initialization requires actual import and exact immutable body readback");return committed;
        }
    }
    private InitialData initial(ContinuityStorePort.Session same,ExactRef basis,WriterContracts.Head head)throws IOException {
        if(FreshCampaignContext.isOriginal(context(),same,basis)) {
            var actual=FreshCampaignContext.replayOriginal(context(),same,basis);actual.requireInitializationPredecessor(same,head);
            return new InitialData(actual.basis(),actual.observation(),actual.source(),actual.sessionId(),actual.evidence());
        }
        var actual=RootInitialEpisodeProof.replayOriginal(context(),same,basis);actual.requireInitializationPredecessor(same,head);
        return new InitialData(actual.basis(),actual.observation(),actual.source(),actual.sessionId(),actual.evidence());
    }
    private static GovernanceOpeningDocument.Document fresh(InitialData actual) {
        return new GovernanceOpeningDocument.Document(actual.observation(),actual.source(),actual.sessionId(),OpeningStage.AWAIT_SUBMIT,
                Optional.empty(),Optional.empty(),actual.evidence().stream().distinct().toList());
    }
    private DomainBodies.ImportRequest request(InitialData actual,ExactRef body) {
        var input=StrictJson.object().put("schema","xar.java-opening-initial-entry/v1");
        input.set("opening",StrictJson.parse(GovernanceOpeningDocument.encode(fresh(actual))));
        input.set("initial_basis",actual.basis().toJson());
        var evidence=actual.evidence().stream().distinct().toList();var refs=input.putArray("entry_evidence");evidence.forEach(ref->refs.add(ref.toJson()));
        byte[] bytes=StrictJson.canonical(input);
        return new DomainBodies.ImportRequest(DomainBodies.Slot.OPENING_GATE,GovernanceOpeningDocument.SCHEMA,body,bytes,evidence,
                "opening-initial-"+ActionCodec.sha256(bytes));
    }
    @Override public String verify(ContinuityState ignored,Optional<DomainBodies.BodyRef> previous,
            DomainBodies.ImportRequest request,byte[] original)throws IOException {
        throw new IOException("opening initialization requires the actual same-writer Head and private canonical initial-entry proof");
    }
    @Override public String verify(WriterContracts.Head head,Optional<DomainBodies.BodyRef> previous,
            DomainBodies.ImportRequest requested,byte[] original)throws IOException {
        var owner=core();var borrowed=owner.writer().borrowedSession();owner.writer().requireSession(borrowed);
        if(GovernanceNextInitialization.SCHEMA.equals(StrictJson.text(StrictJson.parse(requested.producerInput()).get("schema")))) {
            if(nextVerifier==null)throw new IOException("actual NEXT governance initializer is not installed");return nextVerifier.verify(head,previous,requested,original);
        }
        if(OpeningTransitions.PRODUCER_SCHEMA.equals(StrictJson.text(StrictJson.parse(requested.producerInput()).get("schema"))))return transitions().verify(head,previous,requested,original);
        var input=StrictJson.object(StrictJson.parse(requested.producerInput()),Set.of("schema","opening","initial_basis","entry_evidence"));
        var actual=initial(borrowed,ExactRef.fromJson(input.get("initial_basis")),head);
        StrictJson.require(previous.isEmpty() && borrowed.head().digest().equals(head.digest()),"opening fresh producer cannot replace existing state or cross its head");
        var expected=request(actual,requested.originalBody());
        StrictJson.require(requested.slot()==expected.slot() && requested.contractSchema().equals(expected.contractSchema())
                && requested.evidence().equals(expected.evidence()) && requested.evidenceId().equals(expected.evidenceId())
                && Arrays.equals(requested.producerInput(),expected.producerInput())
                && Arrays.equals(original,GovernanceOpeningDocument.encode(fresh(actual))),"actual canonical entry differs from proposed opening initialization");
        return ActionCodec.sha256(StrictJson.canonical(StrictJson.object().put("head",head.digest())
                .put("input",ActionCodec.sha256(expected.producerInput())).put("body",ActionCodec.sha256(original))));
    }
    public RootGovernanceOpeningInputs inputs() { return new RootGovernanceOpeningInputs(sources.producers()); }
}
