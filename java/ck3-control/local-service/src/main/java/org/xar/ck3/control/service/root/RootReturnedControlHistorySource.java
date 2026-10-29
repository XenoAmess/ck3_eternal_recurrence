package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial;
import org.xar.ck3.control.application.history.DriverReturnedControlHistoryRowProducer;
import org.xar.ck3.control.application.history.DriverReturnedControlHistoryRowProducer.*;
import org.xar.ck3.control.build.OriginalMcpCapture;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyObserverSampling;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTransportPublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTransportPublicCodec.SamplingSet;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual public sampling invocation custody. Recording its original return never settles the action. */
public final class RootReturnedControlHistorySource {
    private RootReturnedControlHistorySource() { }

    /** The selected public source owner supplies every implementation and the captured original policy. */
    public static Installed install(RootPublicHandlerProductsFactory.Context selected,RootInstalledCatalog catalog,
            RootDriverTransportRuntimeFactory.Runtime runtime)throws IOException {
        Objects.requireNonNull(selected);Objects.requireNonNull(catalog);Objects.requireNonNull(runtime);
        RootRuntimeContext actual=catalog.context();runtime.requireContext(actual);
        StrictJson.require(catalog.additionalDomains().driverRegistry().product(RootDriverRegistryPublicProducts.Kind.TRANSPORT,
                RootDriverTransportRuntimeFactory.Runtime.class)==runtime,"returned sampling source lost its actual installed transport product");
        var sources=new LinkedHashSet<ExactRef>();
        for(Class<?> type:List.of(RootReturnedControlHistorySource.class,RootDriverTransportPublicSupplier.class,
                RootDriverTransportRuntimeFactory.class))sources.add(selected.source(type));
        for(Class<?> type:List.of(DriverReturnedControlHistoryRowProducer.class,DriverReadHistoryRichMaterial.class))
            sources.add(selected.source(RootRuntimeSelectedSources.Module.APPLICATION,type));
        for(Class<?> type:List.of(ArmyObserverSampling.class,ArmyTransportPublicCodec.class))
            sources.add(selected.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,type));
        sources.addAll(runtime.historySources());
        ExactRef policy=selected.originalMcp(OriginalMcpCapture.OriginalModule.ARMY_OBSERVER_RESEARCH_SAMPLING_CONTROL);
        StrictJson.require(policy.bytes()==13969&&policy.sha256().equals("927fdbb94ae5c07a14f4039595c865af3b28eac0ecdb0fb629ead9b38016b5ae"),
                "actual original sampling RETURNED recording policy differs");sources.add(policy);
        for(Class<?> type:List.of(RootReturnedControlHistorySource.class,RootDriverTransportPublicSupplier.class,
                RootDriverTransportRuntimeFactory.class,DriverReturnedControlHistoryRowProducer.class,
                DriverReadHistoryRichMaterial.class,ArmyObserverSampling.class,ArmyTransportPublicCodec.class))
            actual.game().launchPlan().sources().requireLoadedClass(type);
        Installed result=new Installed(catalog,runtime,List.copyOf(sources));
        result.requireOwner(actual.adopted().authority(),actual.core().journal(),actual.archive(),actual.readCatalog());
        return result;
    }

    /** Only this live owner can create Before and Returned. Their JSON originals grant no current qualification. */
    public static final class Installed implements Source {
        private final RootInstalledCatalog catalog;
        private final RootRuntimeContext context;
        private final RootDriverTransportRuntimeFactory.Runtime runtime;
        private final DriverStateAssembler authority;
        private final ActionJournal journal;
        private final ActionPorts.OutcomeArchive archive;
        private final RootReadContractCatalog readCatalog;
        private final List<ExactRef> sources;
        private Installed(RootInstalledCatalog catalog,RootDriverTransportRuntimeFactory.Runtime runtime,List<ExactRef> sources){
            this.catalog=catalog;context=catalog.context();this.runtime=runtime;
            authority=context.adopted().authority();journal=context.core().journal();archive=context.archive();readCatalog=context.readCatalog();
            this.sources=List.copyOf(sources);
        }
        @Override public void requireOwner(DriverStateAssembler same,ActionJournal sameJournal,ActionPorts.OutcomeArchive sameArchive,
                RootReadContractCatalog sameCatalog){
            StrictJson.require(authority==same&&journal==sameJournal&&archive==sameArchive&&readCatalog==sameCatalog
                    &&context.adopted().authority()==same&&catalog.context()==context&&catalog.bindings()==context.bindings(),
                    "returned control source crossed its actual Driver/journal/archive/catalog owner");
            requireInstalledRuntime();
        }
        @Override public void requireCatalog(RootReadContractCatalog identical){
            StrictJson.require(identical==readCatalog,"returned control cold replay crossed its installed catalog");
        }
        @Override public List<ExactRef> sources(){return sources;}
        @Override public ActionJournal journal(){return journal;}
        private void requireInstalledRuntime(){
            try{
                runtime.requireContext(context);
                StrictJson.require(catalog.additionalDomains().driverRegistry().product(RootDriverRegistryPublicProducts.Kind.TRANSPORT,
                        RootDriverTransportRuntimeFactory.Runtime.class)==runtime,"returned source lost its identical installed Runtime");
            }catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
            for(var action:List.of(runtime.enableAction(),runtime.disableAction())){
                StrictJson.require(catalog.bindings().actualActionBinding(action.effect().operation()).orElseThrow()==action.effect(),
                        "returned sampling binding is not the actual installed action object");
                StrictJson.require(runtime.installation().actions().stream().filter(value->value==action).count()==1,
                        "returned sampling actual action installation membership differs");
                var replay=catalog.bindings().actualArchivedVerifier(action.effect().operation()).orElseThrow();
                StrictJson.require(runtime.installation().archived().stream().filter(value->value==replay).count()==1,
                        "returned sampling lost its identical installed archived verifier");
            }
        }
        public Before prepare(Session same,DriverObservationAssembler.Complete frame,Known known,ActionCommand command,
                SamplingSet input,Instant deadline)throws IOException {
            context.writer().requireSession(same);context.requireCurrent(deadline);
            requireOwner(authority,journal,archive,readCatalog);requireCommand(command);
            StrictJson.require(command.before().equals(frame.identity())&&command.source().equals(frame.source())
                    &&command.sessionId().equals(frame.sessionId())&&known.observation().isPresent()
                    &&Arrays.equals(known.driver().encode(),known.observation().orElseThrow().driver().encode()),
                    "returned invocation must capture the actual preparation lease frame and Known");
            StrictJson.require(input.revision().value().equals(frame.identity().frame().revision())
                    &&input.enabled()==command.operation().value().equals(ArmyObserverSampling.ENABLE)
                    &&input.selection().equals(ArmyObserverSampling.selection(command.arguments())),
                    "returned original typed public arguments differ from the exact prepared command");
            var qualification=context.sources().optionalCurrentMetadata(same);if(qualification.isPresent())qualification.orElseThrow().requireCurrent(same);
            List<SharedSourceFiles.Witness> pins=witness(sources);
            Obj caller=new Obj(Map.of("step",new Text(command.operation().value()),"arguments",
                    OpportunityJson.object(OpportunityJson.parse(ArmyTransportPublicCodec.encode(input).bytes()),"actual public sampling arguments")));
            return new Before(this,same,frame,known,command,input,caller,qualification,pins,deadline);
        }
        public OriginalReturned returned(Session same,Before original,ActionReceipt actual,ActionPorts.OutcomeArchive bound)throws IOException {
            requireBefore(same,original);Objects.requireNonNull(actual);Objects.requireNonNull(bound);
            StrictJson.require(actual.command().equals(original.command),"returned receipt changed the original public command");
            var attempt=DriverReturnedControlHistoryRowProducer.requireIncomplete(actual);
            var basis=RootGuardEvidence.frameBasis(attempt.guard(),bound);
            Known guardKnown=authority.withFrozenFacts(same,frozen->{
                StrictJson.require(frozen.state() instanceof Known,"actual returned guard Known is unavailable");
                Known retained=(Known)frozen.state();
                StrictJson.require(retained.observation().isPresent()
                        &&retained.observation().orElseThrow().semanticFactsEvidence().equals(basis.driverFacts())
                        &&DriverObservationEvidenceReader.reference(retained.auxiliary().get("capability_observed_native_source")).equals(basis.nativeFrame())
                        &&Arrays.equals(retained.driver().encode(),original.known.driver().encode()),
                        "actual frozen guard Known/Native/manifest or complete preparation Driver changed");
                return retained;
            });
            ExactRef expectedFacts=guardKnown.observation().orElseThrow().semanticFactsEvidence();
            ExactRef expectedNative=DriverObservationEvidenceReader.reference(guardKnown.auxiliary().get("capability_observed_native_source"));
            StrictJson.require(basis.driverFacts().equals(expectedFacts)&&basis.nativeFrame().equals(expectedNative),
                    "returned attempt before Native and full Driver manifest differ from the original preparation lease");
            ExactRef receipt=bound.receiptReferenceOf(actual);
            ExactRef record=ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),actual,bound);
            DriverReturnedControlHistoryRowProducer.requireCanonical(same,bound,actual,receipt,record);
            project(actual,bound); // The original complete report is validated before retaining any invocation material.
            ExactRef beforeDriver=bound.preserveMaterial(RawJson.fullMaterial(guardKnown.driver().encode()));
            ExactRef knownOriginal=bound.preserveMaterial(DriverSnapshotFacts.encodeKnownOriginal(guardKnown));
            ExactRef caller=bound.preserveMaterial(new RawJson(DriverJson.encode(original.caller)));
            long sequence=same.head().state().sequence();String digest=same.head().digest();
            var data=new InvocationData(actual.command().operation(),receipt,record,beforeDriver,knownOriginal,expectedNative,
                    expectedFacts,caller,original.qualification.map(RootNativeSourceAuthority.QualifiedMetadata::epochManifest),sequence,digest,sources);
            ExactRef invocation=bound.preserveMaterial(DriverReturnedControlHistoryRowProducer.invocationJson(data));
            var originals=new Originals(actual,receipt,record,guardKnown,beforeDriver,knownOriginal,expectedNative,expectedFacts,
                    invocation,caller,original.qualification.map(RootNativeSourceAuthority.QualifiedMetadata::epochManifest),sequence,digest,sources);
            Returned token=new Returned(this,original,guardKnown,originals);
            requireOriginal(same,authority,bound,token);return token;
        }
        @Override public Originals requireOriginal(Session same,DriverStateAssembler actualAuthority,ActionPorts.OutcomeArchive bound,
                OriginalReturned identical)throws IOException {
            requireOwner(actualAuthority,journal,archive,readCatalog);
            StrictJson.require(identical instanceof Returned&&identical.issuer()==this,"actual returned invocation was not issued by this Root owner");
            Returned actual=(Returned)identical;requireBefore(same,actual.before);
            StrictJson.require(!actual.released,"returned invocation was already released after a definite publication disposition");
            Originals retained=actual.originals;
            StrictJson.require(retained.before()==actual.guardKnown&&retained.actual().command().equals(actual.before.command)
                    &&retained.headSequence()==same.head().state().sequence()&&retained.headDigest().equals(same.head().digest()),
                    "returned private original escaped its actual session, beforeKnown or canonical head");
            DriverReturnedControlHistoryRowProducer.requireCanonical(same,bound,retained.actual(),retained.canonicalReceipt(),retained.canonicalRecord());
            requireMaterial(bound,retained.beforeDriver(),RawJson.fullMaterial(retained.before().driver().encode()));
            requireMaterial(bound,retained.originalKnown(),DriverSnapshotFacts.encodeKnownOriginal(retained.before()));
            requireMaterial(bound,retained.caller(),new RawJson(DriverJson.encode(actual.before.caller)));
            requireMaterial(bound,retained.invocation(),DriverReturnedControlHistoryRowProducer.invocationJson(
                    DriverReturnedControlHistoryRowProducer.invocationData(retained)));
            StrictJson.require(retained.epochManifest().equals(actual.before.qualification.map(RootNativeSourceAuthority.QualifiedMetadata::epochManifest)),"returned source epoch differs");
            project(retained.actual(),bound);return retained;
        }
        /** Publication completion/cancellation drops only this live token. It never changes its canonical UNKNOWN. */
        @Override public synchronized void release(OriginalReturned identical){
            StrictJson.require(identical instanceof Returned&&identical.issuer()==this,"returned release crossed its actual private issuer");
            ((Returned)identical).released=true;
        }
        /** Replays only the original ACK through the sole owning NT decoder and numeric/public formatters. */
        @Override public Projection project(ActionReceipt actual,ActionPorts.OutcomeArchive bound)throws IOException {
            Objects.requireNonNull(bound);var attempt=DriverReturnedControlHistoryRowProducer.requireIncomplete(actual);
            var ack=(NativeActionPort.AckReceived)((ActionState.Unknown)actual.state()).dispatch().orElseThrow();
            StrictJson.require(bound.load(bound.referenceOf(ack)).equals(ack),"returned original ACK archive changed");
            var decoded=ArmyObserverSampling.incompleteOriginal(actual.command(),attempt,ack);
            RawJson numeric=ArmyObserverSampling.driverResult(decoded,actual.command().before(),attempt.guard().connectionGeneration());
            RawJson publicResult=ArmyObserverSampling.publicResult(decoded,actual.command().before(),attempt.guard().connectionGeneration());
            return new Projection(numeric,PublicNumbers.fromResults(numeric,publicResult),sources);
        }
        private void requireBefore(Session same,Before original)throws IOException {
            context.writer().requireSession(same);
            StrictJson.require(original!=null&&original.owner==this&&original.session==same,"returned preparation escaped its exact private owner/session");
            context.requireCurrent(original.deadline);if(original.qualification.isPresent())original.qualification.orElseThrow().requireCurrent(same);
            for(var pin:original.pins)SharedSourceFiles.assertUnchanged(pin);requireCommand(original.command);
        }
        private void requireCommand(ActionCommand command){
            StrictJson.require(command.origin() instanceof CommandOrigin.Gameplay&&command.before().game().equals(context.game().generation())
                    &&command.before().machineId().equals(context.game().machineId())&&command.source().equals(context.source())
                    &&command.sessionId().equals(context.game().sessionId())
                    &&Set.of(ArmyObserverSampling.ENABLE,ArmyObserverSampling.DISABLE).contains(command.operation().value()),
                    "returned sampling invocation crossed its real physical source/Game/session/finite operation");
        }
    }
    public static final class Before {
        private final Installed owner;private final Session session;private final DriverObservationAssembler.Complete frame;
        private final Known known;private final ActionCommand command;private final SamplingSet input;private final Obj caller;
        private final Optional<RootNativeSourceAuthority.QualifiedMetadata> qualification;private final List<SharedSourceFiles.Witness> pins;
        private final Instant deadline;
        private Before(Installed owner,Session session,DriverObservationAssembler.Complete frame,Known known,ActionCommand command,
                SamplingSet input,Obj caller,Optional<RootNativeSourceAuthority.QualifiedMetadata> qualification,List<SharedSourceFiles.Witness> pins,Instant deadline){
            this.owner=owner;this.session=session;this.frame=frame;this.known=known;this.command=command;this.input=input;this.caller=caller;
            this.qualification=qualification;this.pins=List.copyOf(pins);this.deadline=deadline;
        }
    }
    private static final class Returned implements OriginalReturned {
        private final Installed owner;private final Before before;private final Known guardKnown;private final Originals originals;
        private volatile boolean released;
        private Returned(Installed owner,Before before,Known guardKnown,Originals originals){this.owner=owner;this.before=before;this.guardKnown=guardKnown;this.originals=originals;}
        @Override public Source issuer(){return owner;}
    }
    private static List<SharedSourceFiles.Witness> witness(List<ExactRef> sources)throws IOException {
        var result=new ArrayList<SharedSourceFiles.Witness>();
        for(ExactRef ref:sources){var pin=SharedSourceFiles.observe(Path.of(ref.path()));
            StrictJson.require(pin.source().bytes()==ref.bytes()&&pin.source().sha256().equals(ref.sha256()),"returned control producer source changed");result.add(pin);}
        return List.copyOf(result);
    }
    private static void requireMaterial(ActionPorts.OutcomeArchive bound,ExactRef reference,RawJson expected){
        StrictJson.require(Arrays.equals(bound.loadFullMaterial(reference).bytes(),expected.bytes())
                &&bound.materialReferenceOf(expected).equals(reference),"returned control retained original material changed");
    }
}
