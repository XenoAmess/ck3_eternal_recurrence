package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.prisoners.*;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.family.PrisonerNativeQueries;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import java.util.OptionalLong;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerOptionIntent;

/** Core-owned domain registrations. Only stored original producers are replayed; attachment grants no Game/readiness authority. */
public final class PrisonersRuntimeDefinitions {
    private static final String INPUT = "xar.java.prisoner-domain-input/v3";
    private final List<ExactRef> sources;
    private final List<DomainBodies.Registration> registrations;
    private RootApplicationAssembly.Core core;
    private final List<Runtime> attached=new ArrayList<>();
    private final ThreadLocal<NextImport> nextImport=new ThreadLocal<>();
    private RetainedNext retainedNext;
    public PrisonersRuntimeDefinitions(List<ExactRef> actualProducerClosure) {
        sources=List.copyOf(actualProducerClosure);
        StrictJson.require(!sources.isEmpty() && sources.size()<=64 && sources.stream().allMatch(ref->ref.bytes()>0), "exact prisoner producer closure required");
        registrations=java.util.Arrays.stream(PrisonerPlanningPorts.Family.values()).map(family->
                new DomainBodies.Registration(PrisonerLegacyBinding12004.slot(family),schema(family),1_048_576,sources,new DomainVerifier(family))).toList();
    }
    public List<DomainBodies.Registration> registrations() { return registrations; }
    public synchronized void bindCore(RootApplicationAssembly.Core actual) {
        Objects.requireNonNull(actual);StrictJson.require(core==null || core==actual,"prisoner definitions cannot change their original Core");
        core=actual;
    }
    public synchronized void attachCurrent(RootRuntimeContext actual,PrisonerActionBinding12004 actualPreparation,ReadContract<RawJson> actualCollection) {
        Objects.requireNonNull(actual);Objects.requireNonNull(actualPreparation);Objects.requireNonNull(actualCollection);
        StrictJson.require(actualCollection.operation().value().equals(PrisonerNativeQueries.STEP)&&actualCollection.hasPureReplay(),"identical explicit-pure ordinal-zero prisoner collection required");
        StrictJson.require(core!=null && actual.core()==core && actual.archive()==core.archive(),"prisoner runtime must attach to its original Core");
        for(var previous:attached) {
            if(previous.context()==actual) {
                StrictJson.require(previous.preparation()==actualPreparation&&previous.collection()==actualCollection,"one physical prisoner runtime cannot replace its original products");return;
            }
            StrictJson.require(!previous.context().game().generation().equals(actual.game().generation())
                    ||!previous.context().game().sessionId().equals(actual.game().sessionId()),"two prisoner runtimes cannot claim one physical Game/session");
        }
        attached.add(new Runtime(actual,actualPreparation,actualCollection));
    }
    /** Construction never chooses the current owner. Only the Core's actually installed Root may do so. */
    private Runtime runtime() {
        RootApplicationAssembly.Core actualCore;List<Runtime> copies;
        synchronized(this){actualCore=core;copies=List.copyOf(attached);}
        StrictJson.require(actualCore!=null&&!copies.isEmpty(),"actual prisoner Core/runtime has not been attached");
        try {
            var actual=actualCore.sessionAccess().current().identity();
            return copies.stream().filter(value->value.context().game().generation().equals(actual.game())
                    &&value.context().game().sessionId().equals(actual.sessionId())&&value.context().game().machineId().equals(actual.machineId()))
                    .findFirst().orElseThrow(()->new IOException("the actual installed Root has no identical prisoner products"));
        }catch(IOException unavailable){throw new UncheckedIOException("actual installed prisoner runtime unavailable",unavailable);}
    }
    /** Fixed Core-owned pure replay dependencies; attaching a candidate cannot replace historical decoders. */
    private synchronized Runtime historicalRuntime() {
        StrictJson.require(core!=null&&!attached.isEmpty(),"original prisoner replay dependencies unavailable");return attached.getFirst();
    }
    private synchronized Runtime initializationRuntime(RootInitialEpisodeProof actual) {
        Objects.requireNonNull(actual);
        return attached.stream().filter(value->value.context().game().generation().equals(actual.currentObservation().game())
                &&value.context().game().sessionId().equals(actual.sessionId())&&value.context().source().equals(actual.source()))
                .findFirst().orElseThrow(()->new IllegalArgumentException("actual fresh-entry proof has no matching physical prisoner products"));
    }
    private synchronized Runtime initializationRuntime(FreshCampaignContext actual) {
        Objects.requireNonNull(actual);
        return attached.stream().filter(value->value.context()==actual.context()
                &&value.context().game().generation().equals(actual.currentObservation().game())
                &&value.context().game().sessionId().equals(actual.sessionId())&&value.context().source().equals(actual.source()))
                .findFirst().orElseThrow(()->new IllegalArgumentException("actual fresh campaign has no matching physical prisoner products"));
    }
    private record Runtime(RootRuntimeContext context,PrisonerActionBinding12004 preparation,ReadContract<RawJson> collection) { }
    private record NextImport(ContinuityStorePort.Session session,RootApplicationAssembly.EpisodeDomainInitializationProof proof,
            Runtime runtime,RootNextEpisodeDomainReads.Captured<RawJson> captured,PlanningReadResult.Known<RawJson> collection) { }
    /** At most one private attempt is retained. A borrowed writer Session never escapes its ThreadLocal import scope. */
    private record RetainedNext(RootApplicationAssembly.EpisodeDomainInitializationProof proof,Runtime runtime,
            RootNextEpisodeDomainReads.Captured<RawJson> captured,PlanningReadResult.Known<RawJson> collection) { }
    private record PriorEvidence(PrisonerEpisodeLedger12004.PriorInitialization original,List<ExactRef> evidence) {
        private PriorEvidence {Objects.requireNonNull(original);evidence=List.copyOf(evidence);}
    }
    public void initialize(ContinuityStorePort.Session borrowed,RootInitialEpisodeProof actualFreshEntry)throws IOException {
        Runtime actual=initializationRuntime(actualFreshEntry);actual.context().writer().requireSession(borrowed);
        ExactRef basis=Objects.requireNonNull(actualFreshEntry).preserveOriginal(borrowed);
        for(var family:PrisonerPlanningPorts.Family.values()) {
            actualFreshEntry.requireInitializationPredecessor(borrowed,borrowed.head());
            DomainBodies.Read previous=borrowed.readDomain(PrisonerLegacyBinding12004.slot(family));
            StrictJson.require(previous instanceof DomainBodies.Unavailable unavailable && unavailable.reason()==DomainBodies.Reason.UNIMPORTED,
                    "fresh-entry initialization cannot replace an imported or invalid original body");
            ObjectNode input=input(family,"initialize");input.set("initial_basis",basis.toJson());
            var refs=new LinkedHashSet<ExactRef>(actualFreshEntry.evidence());refs.add(basis);
            commit(actual,borrowed,family,fresh(family,actualFreshEntry.currentObservation(),actualFreshEntry.source(),actualFreshEntry.sessionId(),basis),input,List.copyOf(refs));
        }
    }
    /** The real observed day-zero campaign is a separate input, never an old ENTRY receipt. */
    public void initialize(ContinuityStorePort.Session borrowed,FreshCampaignContext actualFresh)throws IOException {
        Runtime actual=initializationRuntime(actualFresh);actual.context().writer().requireSession(borrowed);
        actualFresh.requireCurrent(borrowed);
        for(var family:PrisonerPlanningPorts.Family.values()) {
            actualFresh.requireInitializationPredecessor(borrowed,borrowed.head());
            DomainBodies.Read previous=borrowed.readDomain(PrisonerLegacyBinding12004.slot(family));
            if(previous instanceof DomainBodies.Available available) {
                StrictJson.require(available.head().equals(borrowed.persistedHead()),"available prisoner body head mismatch");
                var reference=available.reference();
                StrictJson.require(reference.contractSchema().equals(schema(family)),"available prisoner body schema mismatch");
                var decoded=PrisonerEpisodeLedger12004.decode(family,new RawJson(available.canonicalBody()));
                decoded.epoch().owner().require(actualFresh.currentObservation(),actualFresh.source(),actualFresh.sessionId());
                actualFresh.requireCurrent(borrowed);
                continue;
            }
            StrictJson.require(previous instanceof DomainBodies.Unavailable unavailable&&unavailable.reason()==DomainBodies.Reason.UNIMPORTED,
                    "fresh campaign initialization cannot replace an imported or invalid prisoner body");
            ExactRef basis=actualFresh.preserveOriginal(borrowed);
            ObjectNode input=input(family,"initialize");input.set("initial_basis",basis.toJson());
            var refs=new LinkedHashSet<ExactRef>(actualFresh.evidence());refs.add(basis);
            commit(actual,borrowed,family,fresh(family,actualFresh.currentObservation(),actualFresh.source(),actualFresh.sessionId(),basis),input,List.copyOf(refs));
            actualFresh.requireCurrent(borrowed);
        }
    }
    /** Both real slots are rebased from the private actual first-BASELINE proof, without replaying any old pending action. */
    public List<DomainBodies.BodyRef> initializeNext(ContinuityStorePort.Session same,RootApplicationAssembly.EpisodeDomainInitializationProof proof)throws IOException {
        Objects.requireNonNull(proof);Runtime actual;
        synchronized(this){actual=attached.stream().filter(value->value.context().game().generation().equals(proof.afterSession().game())
                &&value.context().game().sessionId().equals(proof.afterSession().sessionId())&&value.context().source().equals(proof.source()))
                .findFirst().orElseThrow(()->new IOException("actual NEXT prisoner products are not attached"));}
        proof.requireCurrent(same,actual.context());StrictJson.require(nextImport.get()==null,"prisoner NEXT import is not reentrant");
        RetainedNext retained;
        synchronized(this){
            if(retainedNext==null||retainedNext.proof()!=proof){
                var arguments=PrisonerNativeQueries.arguments(new PrisonerOptionIntent.Unconditional(),OptionalLong.empty());
                var observed=proof.read(same,actual.context(),actual.collection(),arguments,proof.deadline());
                observed.requireOriginals(same,actual.context(),proof);
                if(!(observed.result() instanceof PlanningReadResult.Known<RawJson> known))throw new IOException("actual current NEXT prisoner collection unavailable; no empty body imported");
                retainedNext=new RetainedNext(proof,actual,observed,known);
            }
            retained=retainedNext;
        }
        StrictJson.require(retained.runtime()==actual,"retained NEXT read cannot move to another physical installer");
        var captured=retained.captured();var known=retained.collection();captured.requireOriginals(same,actual.context(),proof);
        var scope=new NextImport(same,proof,actual,captured,known);nextImport.set(scope);
        try {
            var result=new ArrayList<DomainBodies.BodyRef>();
            for(var family:PrisonerPlanningPorts.Family.values()){
                proof.requireCurrent(same,actual.context());var current=requireAvailable(same,family);
                var previous=baselineOriginal(same,proof,family);var previousBody=readOriginal(same,previous);
                var epoch=nextEpoch(scope,family,previous,previousBody);var old=PrisonerEpisodeLedger12004.decode(family,previousBody);
                RawJson body=PrisonerEpisodeLedger12004.next(family,previousBody,old.epoch().owner(),previous,epoch);
                Optional<PriorEvidence> displaced=Optional.empty();
                if(!current.reference().equals(previous)){
                    StrictJson.require(current.reference().contractSchema().equals(schema(family))&&current.reference().producerSources().equals(sources),"current prisoner source/schema closure differs");
                    if(Arrays.equals(current.canonicalBody(),body.bytes())){
                        captured.requireOriginals(same,actual.context(),proof);proof.requireCurrent(same,actual.context());result.add(current.reference());continue;
                    }
                    displaced=Optional.of(requirePriorInitializedBody(scope,family,previous,previousBody,current.reference(),new RawJson(current.canonicalBody())));
                }
                ObjectNode input=input(family,"initialize_next");input.set("previous_body",current.reference().payload().toJson());input.set("previous_domain",current.reference().toJson());input.set("old_domain",previous.toJson());input.set("epoch",PrisonerEpisodeLedger12004.epoch(epoch));
                if(displaced.isPresent())input.set("prior_initialization",PrisonerEpisodeLedger12004.prior(displaced.orElseThrow().original()));else input.putNull("prior_initialization");
                input.set("origins",PrisonerEpisodeLedger12004.origins(origins(proof)));
                input.set("baseline_witness",CheckpointPairCodec.fileWitnessToJson(proof.baselineMaterial().witness()));
                input.set("saved_semantic",OrdinaryCycleTransitions.semanticToJson(proof.savedSemantic()));
                var savedDriver=actual.context().archive().preserveArtifact(same,proof.firstSavedDriver().encode(),DriverCheckpointStore.MAX_DRIVER_BYTES);
                var predecessorDriver=actual.context().archive().preserveArtifact(same,proof.predecessorDriver().encode(),DriverCheckpointStore.MAX_DRIVER_BYTES);
                var currentDriver=actual.context().archive().preserveArtifact(same,proof.currentDriver().encode(),DriverCheckpointStore.MAX_DRIVER_BYTES);
                input.set("saved_driver",savedDriver.toJson());input.set("predecessor_driver",predecessorDriver.toJson());
                input.set("current_driver",currentDriver.toJson());input.set("current_semantic",OrdinaryCycleTransitions.semanticToJson(proof.currentSemantic()));
                input.set("query_semantic",OrdinaryCycleTransitions.semanticToJson(captured.semantic()));input.set("query_source_proof",ExactRef.optionalToJson(captured.sourceProof()));
                var evidence=new LinkedHashSet<ExactRef>(proof.savedSemantic().references());evidence.add(proof.baselineMaterial().reference());
                evidence.add(previous.payload());evidence.add(current.reference().payload());displaced.ifPresent(value->evidence.addAll(value.evidence()));evidence.add(known.originalReceipt());
                evidence.add(savedDriver);evidence.add(predecessorDriver);evidence.add(currentDriver);evidence.addAll(proof.currentSemantic().references());
                evidence.addAll(captured.semantic().references());captured.sourceProof().ifPresent(evidence::add);
                for(var guard:List.of(known.receipt().before(),known.receipt().after())){evidence.add(guard.binding().nativeEvidence());evidence.add(guard.binding().capabilityEvidence());evidence.addAll(guard.binding().supportingEvidence());}
                result.add(commit(actual,same,family,body,input,List.copyOf(evidence)));proof.requireCurrent(same,actual.context());
            }
            return List.copyOf(result);
        }finally{nextImport.remove();}
    }
    private PrisonerEpisodeLedger12004.Epoch nextEpoch(NextImport scope,PrisonerPlanningPorts.Family family,DomainBodies.BodyRef previousReference,RawJson previousBody)throws IOException {
        var proof=scope.proof();var actual=scope.runtime();var same=scope.session();proof.requireCurrent(same,actual.context());
        StrictJson.require(baselineOriginal(same,proof,family).equals(previousReference),"NEXT must reduce the immutable original BASELINE slot, not an intervening import");
        scope.captured().requireOriginals(same,actual.context(),proof);
        var old=PrisonerEpisodeLedger12004.decode(family,previousBody);var prior=old.epoch().owner();
        var before=proof.predecessorDriver().session();var after=proof.currentDriver().session();
        StrictJson.require(prior.session().equals(proof.beforeSession())&&BigInteger.valueOf(prior.player()).equals(before.actorId())
                &&prior.episodeRunId().equals(before.episodeRunId()),"old prisoner body differs from the actual original episode Driver");
        var owner=new PrisonerEpisodeLedger12004.Owner(proof.afterSession(),after.actorId().longValueExact(),after.episodeRunId(),proof.source());
        owner.require(proof.currentSemantic().frame(),proof.source(),proof.afterSession().sessionId());
        StrictJson.require(origins(proof).currentOwner().equals(owner),"current restored physical owner differs from its dual originals");
        var read=scope.collection().receipt();var archive=actual.context().archive().withSession(same);
        StrictJson.require(actual.context().readCatalog().containsIdentity(actual.collection())&&archive.readReferenceOf(read).equals(scope.collection().originalReceipt())
                &&archive.loadRead(scope.collection().originalReceipt()).equals(read),"NEXT collection is not the identical installed original product");
        NativeRecordedEvidenceVerifier.requireRead(read,archive);RawJson replayed=actual.collection().replay(read);
        StrictJson.require(replayed.equals(scope.collection().value())&&read.request().origin() instanceof CommandOrigin.Gameplay
                &&read.request().operation().equals(actual.collection().operation())&&read.request().arguments().equals(PrisonerNativeQueries.arguments(new PrisonerOptionIntent.Unconditional(),OptionalLong.empty())),"NEXT collection original source/arguments differ");
        owner.require(read.request().before(),read.request().source(),read.request().sessionId());
        StrictJson.require(read.request().before().frame().identity().dateRaw().equals(proof.currentSemantic().frame().frame().identity().dateRaw())
                &&read.request().before().frame().identity().nativeRevision().compareTo(proof.currentSemantic().frame().frame().identity().nativeRevision())>=0,
                "current custody changed actual day or regressed within the current physical Game");
        for(var guard:List.of(read.before(),read.after())){var frame=RootGuardEvidence.loadFrame(guard.binding(),archive,actual.context().frameLoader());
            StrictJson.require(frame.identity().equals(read.request().before())&&frame.source().equals(proof.source())&&frame.sessionId().equals(proof.afterSession().sessionId()),"NEXT collection full original frame/source differs");}
        var decoded=PrisonerNativeQueries.decode(read,0);StrictJson.require(decoded.status()==PrisonerNativeQueries.CollectionStatus.AVAILABLE,"unavailable collection is not a complete empty collection");
        var sequence=StrictJson.integer(StrictJson.parse(replayed.bytes(),1_048_576).get("query_sequence"),BigInteger.ONE,StrictJson.UINT64_MAX);
        var collection=new PrisonerEpisodeLedger12004.Collection(scope.collection().originalReceipt(),read.request().before(),sequence,decoded.prisonerIds());
        var material=proof.baselineMaterial();proof.requireCurrent(same,actual.context());
        return new PrisonerEpisodeLedger12004.Epoch(PrisonerEpisodeLedger12004.Kind.NEXT,owner,material.reference(),
                Optional.of(new PrisonerEpisodeLedger12004.Baseline(material.originalHeadSequence(),material.originalHeadDigest())),
                Optional.of(new PrisonerEpisodeLedger12004.Predecessor(prior,previousReference)),Optional.of(collection));
    }
    private DomainBodies.BodyRef baselineOriginal(ContinuityStorePort.Session same,RootApplicationAssembly.EpisodeDomainInitializationProof proof,PrisonerPlanningPorts.Family family)throws IOException {
        var material=proof.baselineMaterial();material.requireRetained(same);
        var reference=proof.oldDomain(PrisonerLegacyBinding12004.slot(family));
        StrictJson.require(reference.contractSchema().equals(schema(family))&&reference.producerSources().equals(sources),"BASELINE prisoner body has a different explicit source/schema closure");
        return reference;
    }
    private static PrisonerEpisodeLedger12004.InitializationOrigins origins(RootApplicationAssembly.EpisodeDomainInitializationProof proof) {
        var current=proof.currentDriver().session();
        var owner=new PrisonerEpisodeLedger12004.Owner(proof.afterSession(),current.actorId().longValueExact(),current.episodeRunId(),proof.source());
        return new PrisonerEpisodeLedger12004.InitializationOrigins(PrisonerEpisodeLedger12004.InitializationKind.valueOf(proof.kind().name()),
                proof.baselineMaterial().session(),proof.savedSemantic().frame(),owner,proof.currentSemantic().frame(),
                new PrisonerEpisodeLedger12004.Baseline(proof.initializationHeadSequence(),proof.initializationHeadDigest()));
    }
    /** An exact prior initialization is historical provenance, never old-actor pending or current restored custody. */
    private PriorEvidence requirePriorInitializedBody(NextImport scope,PrisonerPlanningPorts.Family family,DomainBodies.BodyRef oldReference,
            RawJson oldBody,DomainBodies.BodyRef displacedReference,RawJson displacedBody)throws IOException {
        var proof=scope.proof();var actual=scope.runtime();var same=scope.session();proof.requireCurrent(same,actual.context());
        StrictJson.require(proof.kind()==RootApplicationAssembly.EpisodeDomainInitializationProof.Kind.RESTORED_FIRST
                &&displacedReference.contractSchema().equals(schema(family))&&displacedReference.producerSources().equals(sources),"only a real restored-FIRST proof can displace prior saved-Game initialization");
        var saved=PrisonerEpisodeLedger12004.decode(family,displacedBody);var savedOwner=saved.epoch().owner();
        var originalSaved=proof.firstSavedDriver().session();
        StrictJson.require(!savedOwner.session().game().equals(proof.afterSession().game())
                &&savedOwner.session().machineId().equals(proof.baselineMaterial().session().machineId())
                &&BigInteger.valueOf(savedOwner.player()).equals(originalSaved.actorId())&&savedOwner.episodeRunId().equals(originalSaved.episodeRunId()),
                "prior initialization must retain the actual saved-FIRST lineage on a distinct earlier physical Game");
        var collection=saved.epoch().collection().orElseThrow(()->new IOException("prior NEXT body has no actual saved-Game collection original"));
        var archive=actual.context().archive().withSession(same);var read=archive.loadRead(collection.originalReceipt());
        StrictJson.require(archive.readReferenceOf(read).equals(collection.originalReceipt())&&read.request().before().equals(collection.observed())
                &&read.request().origin() instanceof CommandOrigin.Gameplay&&read.request().operation().equals(actual.collection().operation())
                &&read.request().arguments().equals(PrisonerNativeQueries.arguments(new PrisonerOptionIntent.Unconditional(),OptionalLong.empty())),"displaced saved collection lost its original contract/args/frame");
        savedOwner.require(read.request().before(),read.request().source(),read.request().sessionId());NativeRecordedEvidenceVerifier.requireRead(read,archive);
        var normalized=actual.collection().replay(read);var decoded=PrisonerNativeQueries.decode(read,0);
        StrictJson.require(decoded.status()==PrisonerNativeQueries.CollectionStatus.AVAILABLE&&decoded.prisonerIds().equals(collection.prisonerIds())
                &&StrictJson.integer(StrictJson.parse(normalized.bytes(),1_048_576).get("query_sequence"),BigInteger.ONE,StrictJson.UINT64_MAX).equals(collection.querySequence())
                &&read.request().before().frame().identity().dateRaw().equals(proof.savedSemantic().frame().frame().identity().dateRaw())
                &&(!savedOwner.session().equals(proof.baselineMaterial().session())
                    ||read.request().before().frame().identity().nativeRevision().compareTo(proof.savedSemantic().frame().frame().identity().nativeRevision())>=0),
                "saved-Game collection is unavailable or its exact original values changed");
        var evidence=new LinkedHashSet<ExactRef>();var sourceProofs=new LinkedHashSet<ExactRef>();evidence.add(displacedReference.payload());evidence.add(collection.originalReceipt());
        for(var guard:List.of(read.before(),read.after())){
            RootGuardEvidence.requireHistory(guard.binding(),archive,same);var frame=RootGuardEvidence.loadFrame(guard.binding(),archive,actual.context().frameLoader());
            StrictJson.require(frame.identity().equals(collection.observed())&&frame.source().equals(savedOwner.source())&&frame.sessionId().equals(savedOwner.session().sessionId()),"saved collection full original source/Driver frame differs");
            var sourceProof=RootGuardEvidence.sourceQualification(guard.binding(),archive);if(sourceProof.isPresent()){var ref=sourceProof.orElseThrow();same.verifyPin(same.capturePin(ref,16<<20));sourceProofs.add(ref);evidence.add(ref);}
            evidence.add(guard.binding().nativeEvidence());evidence.add(guard.binding().capabilityEvidence());evidence.addAll(guard.binding().supportingEvidence());
        }
        var old=PrisonerEpisodeLedger12004.decode(family,oldBody);var material=proof.baselineMaterial();
        var expectedEpoch=new PrisonerEpisodeLedger12004.Epoch(PrisonerEpisodeLedger12004.Kind.NEXT,savedOwner,material.reference(),
                Optional.of(new PrisonerEpisodeLedger12004.Baseline(material.originalHeadSequence(),material.originalHeadDigest())),
                Optional.of(new PrisonerEpisodeLedger12004.Predecessor(old.epoch().owner(),oldReference)),Optional.of(collection));
        RawJson expected=PrisonerEpisodeLedger12004.next(family,oldBody,old.epoch().owner(),oldReference,expectedEpoch);
        StrictJson.require(Arrays.equals(expected.bytes(),displacedBody.bytes()),"displaced body is not the exact original NEXT reducer result; UNKNOWN/current mutations cannot be discarded");
        proof.requireCurrent(same,actual.context());return new PriorEvidence(new PrisonerEpisodeLedger12004.PriorInitialization(displacedReference,savedOwner,collection,List.copyOf(sourceProofs)),List.copyOf(evidence));
    }
    private static RawJson readOriginal(ContinuityStorePort.Session same,DomainBodies.BodyRef reference)throws IOException {
        var pin=new WriterContracts.Pin(reference.payload(),reference.identity());same.verifyPin(pin);
        byte[] raw=same.readPinned(pin,PrisonerEpisodeLedger12004.MAX_BYTES);same.verifyPin(pin);
        return new RawJson(raw);
    }
    /** Called before the sole coordinator's first durable INTENT, inside that exact writer scope. */
    public void prepare(ContinuityStorePort.Session borrowed,ActionCommand command) {
        try {
            Runtime actual=runtime();var context=actual.context();context.writer().requireSession(borrowed);
            StrictJson.require(command.source().equals(context.source()) && command.sessionId().equals(context.game().sessionId())
                    && command.before().game().equals(context.game().generation()),"pending preparation crossed the current physical Game");
            context.requireCurrent(command.deadline());
            context.readiness().current(borrowed,command.before(),command.deadline(),lease->{
                var archive=context.archive().withSession(borrowed);var bound=actual.preparation().withArchive(archive);
                bound.prepare(command);var selected=bound.selected(command);requireOriginalRead(selected,command,archive,context.frameLoader());
                if(PrisonerActionBinding12004.isPublic(command))for(var guard:List.of(selected.receipt().before(),selected.receipt().after()))
                    StrictJson.require(context.clock().instant().isBefore(guard.binding().validUntil()),"public prisoner collection original expired before INTENT");
                var family=family(command);var previous=requireAvailable(borrowed,family);
                RawJson next=PrisonerLedgerReducer12004.prepare(family,new RawJson(previous.canonicalBody()),command,selected);
                ExactRef commandRef=archive.preserveMaterial(new RawJson(ActionCodec.encodeCommand(command)));
                ObjectNode input=input(family,"prepare");input.set("previous_body",previous.reference().payload().toJson());input.set("command",commandRef.toJson());
                commit(actual,borrowed,family,next,input,List.of(previous.reference().payload(),commandRef,selected.reference()));
                return null;
            });
        } catch(IOException failure) { throw new UncheckedIOException("original prisoner pending preparation unavailable",failure); }
    }
    public void resolve(ContinuityStorePort.Session borrowed,PrisonerLegacyBinding12004.Bound original)throws IOException {
        Runtime actual=runtime();var context=actual.context();context.writer().requireSession(borrowed);
        var family=original.pending().family();var previous=requireAvailable(borrowed,family);
        StrictJson.require(previous.reference().payload().equals(original.originalBody()),"pending body changed before canonical settlement import");
        var archive=context.archive().withSession(borrowed);ActionReceipt receipt=archive.loadReceipt(original.originalReceipt());
        PrisonerLegacyBinding12004.verifyOriginal(borrowed.head(),archive,actual.preparation(),family,new RawJson(previous.canonicalBody()),receipt);
        RawJson material=replayTerminal(borrowed.head(),receipt,archive,context);
        RawJson next=PrisonerLedgerReducer12004.resolve(family,new RawJson(previous.canonicalBody()),receipt,material);
        ObjectNode input=input(family,"resolve");input.set("previous_body",original.originalBody().toJson());input.set("receipt",original.originalReceipt().toJson());
        input.set("material",archive.materialReferenceOf(material).toJson());
        var refs=new LinkedHashSet<ExactRef>(original.lineage());refs.add(original.originalBody());refs.add(original.originalReceipt());
        refs.add(original.originalSubmission());refs.add(original.selectedCollectionRead());refs.add(archive.materialReferenceOf(material));
        commit(actual,borrowed,family,next,input,List.copyOf(refs));
    }
    /** Only an actual same-writer canonical BEFORE_WRITE/0 receipt can clear its own modern unsubmitted pending. */
    public void resolveZeroBeforeDispatch(ContinuityStorePort.Session same,ActionReceipt original)throws IOException {
        Runtime actual=runtime();var context=actual.context();context.writer().requireSession(same);
        StrictJson.require(original.state() instanceof ActionState.RejectedBeforeDispatch&&original.command().source().equals(context.source())
                &&original.command().sessionId().equals(context.game().sessionId())&&original.command().before().game().equals(context.game().generation()),"zero cleanup requires its current actual physical owner");
        var archive=context.archive().withSession(same);var canonical=ContinuityActionJournal.lookup(same.head().state(),original.command().actionId(),archive)
                .orElseThrow(()->new IOException("canonical zero-dispatch action is absent"));
        StrictJson.require(canonical.equals(original),"zero cleanup cannot use caller-assembled receipt data");
        var family=family(original.command());var previous=requireAvailable(same,family);RawJson previousBody=new RawJson(previous.canonicalBody());
        if(StrictJson.parse(previousBody.bytes()).get("pending").isNull())return;
        PrisonerLegacyBinding12004.verifyOriginal(same.head(),archive,actual.preparation(),family,previousBody,canonical);
        var material=replayTerminal(same.head(),canonical,archive,context);var materialRef=archive.preserveMaterial(material);
        var receiptRef=archive.receiptReferenceOf(canonical);var selected=actual.preparation().withArchive(archive).selected(canonical.command());
        var next=PrisonerLedgerReducer12004.resolve(family,previousBody,canonical,material);ObjectNode input=input(family,"resolve");
        input.set("previous_body",previous.reference().payload().toJson());input.set("receipt",receiptRef.toJson());input.set("material",materialRef.toJson());
        var refs=new LinkedHashSet<ExactRef>(PrisonerLegacyBinding12004.originalLineage(same.head(),archive,canonical));
        refs.add(previous.reference().payload());refs.add(receiptRef);refs.add(materialRef);refs.add(selected.reference());
        refs.add(archive.referenceOf(((ActionState.RejectedBeforeDispatch)canonical.state()).dispatch()));
        commit(actual,same,family,next,input,List.copyOf(refs));
    }
    private final class DomainVerifier implements DomainBodies.Verifier {
        private final PrisonerPlanningPorts.Family family;
        private DomainVerifier(PrisonerPlanningPorts.Family family) { this.family=family; }
        @Override public String verify(ContinuityState detached,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] body)throws IOException {
            throw new IOException("prisoner verification requires the actual original writer Head");
        }
        @Override public String verify(WriterContracts.Head head,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] body)throws IOException {
            Runtime actual=historicalRuntime();var context=actual.context();var borrowed=core.writer().borrowedSession();core.writer().requireSession(borrowed);
            StrictJson.require(head.state().machineId().equals(context.game().machineId()) && request.slot()==PrisonerLegacyBinding12004.slot(family)
                    && request.contractSchema().equals(schema(family)),"original prisoner domain head/contract differs");
            var archive=context.archive().withSession(borrowed);
            JsonNode parsed=StrictJson.parse(request.producerInput(),1_048_576);
            StrictJson.require(parsed instanceof ObjectNode,"actual prisoner producer object required");ObjectNode row=(ObjectNode)parsed;
            StrictJson.require(INPUT.equals(StrictJson.text(row.get("schema"))) && family.name().equals(StrictJson.text(row.get("family"))),"prisoner input schema/family differs");
            String operation=StrictJson.text(row.get("operation"));RawJson expected;
            if(operation.equals("initialize")) {
                StrictJson.object(row,Set.of("schema","family","operation","initial_basis"));
                StrictJson.require(previous.isEmpty(),"initializer cannot overwrite an original body");
                ExactRef basis=ExactRef.fromJson(row.get("initial_basis"));
                if(FreshCampaignContext.isOriginal(context,borrowed,basis)) {
                    var original=FreshCampaignContext.replayOriginal(context,borrowed,basis);
                    original.requireInitializationPredecessor(borrowed,head);
                    StrictJson.require(request.evidence().contains(basis)&&request.evidence().containsAll(original.evidence()),
                            "fresh campaign prisoner initializer evidence closure is missing");
                    expected=fresh(family,original.observation(),original.source(),original.sessionId(),original.basis());
                } else {
                    var original=RootInitialEpisodeProof.replayOriginal(context,borrowed,basis);
                    original.requireInitializationPredecessor(borrowed,head);
                    StrictJson.require(request.evidence().containsAll(original.evidence()),"actual initializer evidence closure is missing");
                    expected=fresh(family,original.observation(),original.source(),original.sessionId(),original.basis());
                }
            } else {
                StrictJson.require(previous.isPresent(),"previous full prisoner body is absent");
                ExactRef prior=ExactRef.fromJson(row.get("previous_body"));
                StrictJson.require(previous.orElseThrow().payload().equals(prior) && request.evidence().contains(prior),"actual previous body identity differs");
                RawJson previousBody=archive.loadMaterial(prior);PrisonerLedgerReducer12004.validate(family,StrictJson.parse(previousBody.bytes(),1_048_576));
                if(operation.equals("initialize_next")) {
                    StrictJson.object(row,Set.of("schema","family","operation","previous_body","previous_domain","old_domain","prior_initialization","epoch","origins","baseline_witness","saved_semantic","saved_driver","predecessor_driver","current_driver","current_semantic","query_semantic"),Set.of("query_source_proof"));
                    NextImport scope=nextImport.get();StrictJson.require(scope!=null&&scope.session()==borrowed,"NEXT prisoner import requires the private same-thread Core proof, not serialized DATA");
                    scope.proof().requireCurrent(borrowed,scope.runtime().context());
                    var proof=scope.proof();var oldReference=baselineOriginal(borrowed,proof,family);var oldBody=readOriginal(borrowed,oldReference);
                    StrictJson.require(oldReference.equals(DomainBodies.BodyRef.fromJson(row.get("old_domain")))&&request.evidence().contains(oldReference.payload()),"original immutable FIRST domain differs");
                    StrictJson.require(previous.orElseThrow().equals(DomainBodies.BodyRef.fromJson(row.get("previous_domain"))),"actual displaced native BodyRef differs");
                    if(!previous.orElseThrow().equals(oldReference)){
                        var priorInitialization=requirePriorInitializedBody(scope,family,oldReference,oldBody,previous.orElseThrow(),previousBody);
                        StrictJson.require(priorInitialization.original().equals(PrisonerEpisodeLedger12004.prior(row.get("prior_initialization")))
                                &&request.evidence().containsAll(priorInitialization.evidence()),"exact displaced initialization/sourceproof provenance missing");
                    }else StrictJson.require(row.get("prior_initialization").isNull(),"original old domain cannot fabricate prior physical initialization provenance");
                    var epoch=nextEpoch(scope,family,oldReference,oldBody);
                    StrictJson.require(sameJson(PrisonerEpisodeLedger12004.epoch(epoch),row.get("epoch"))
                            &&PrisonerEpisodeLedger12004.origins(row.get("origins")).equals(origins(proof))
                            &&sameJson(CheckpointPairCodec.fileWitnessToJson(proof.baselineMaterial().witness()),row.get("baseline_witness"))
                            &&sameJson(OrdinaryCycleTransitions.semanticToJson(proof.savedSemantic()),row.get("saved_semantic"))
                            &&Arrays.equals(proof.firstSavedDriver().encode(),scope.runtime().context().archive().readArtifact(borrowed,ExactRef.fromJson(row.get("saved_driver")),DriverCheckpointStore.MAX_DRIVER_BYTES))
                            &&Arrays.equals(proof.predecessorDriver().encode(),scope.runtime().context().archive().readArtifact(borrowed,ExactRef.fromJson(row.get("predecessor_driver")),DriverCheckpointStore.MAX_DRIVER_BYTES))
                            &&Arrays.equals(proof.currentDriver().encode(),scope.runtime().context().archive().readArtifact(borrowed,ExactRef.fromJson(row.get("current_driver")),DriverCheckpointStore.MAX_DRIVER_BYTES))
                            &&sameJson(OrdinaryCycleTransitions.semanticToJson(proof.currentSemantic()),row.get("current_semantic"))
                            &&sameJson(OrdinaryCycleTransitions.semanticToJson(scope.captured().semantic()),row.get("query_semantic"))
                            &&ExactRef.optionalFromJson(row.get("query_source_proof")).equals(scope.captured().sourceProof()),"NEXT serialized source DATA differs from actual private originals");
                    StrictJson.require(request.evidence().containsAll(proof.savedSemantic().references())&&request.evidence().contains(proof.baselineMaterial().reference())
                            &&request.evidence().contains(scope.collection().originalReceipt())&&request.evidence().containsAll(scope.captured().semantic().references())
                            &&(scope.captured().sourceProof().isPresent()?request.evidence().contains(scope.captured().sourceProof().orElseThrow()):true)&&request.evidence().contains(ExactRef.fromJson(row.get("saved_driver")))
                            &&request.evidence().contains(ExactRef.fromJson(row.get("predecessor_driver")))&&request.evidence().contains(ExactRef.fromJson(row.get("current_driver")))
                            &&request.evidence().containsAll(proof.currentSemantic().references()),"original saved and current physical evidence closure is incomplete");
                    expected=PrisonerEpisodeLedger12004.next(family,oldBody,PrisonerEpisodeLedger12004.decode(family,oldBody).epoch().owner(),oldReference,epoch);
                    scope.proof().requireCurrent(borrowed,scope.runtime().context());
                } else if(operation.equals("prepare")) {
                    StrictJson.object(row,Set.of("schema","family","operation","previous_body","command"));
                    ExactRef commandRef=ExactRef.fromJson(row.get("command"));ActionCommand command=ActionCodec.decodeCommand(archive.loadMaterial(commandRef).bytes());
                    StrictJson.require(family(command)==family && command.source().machineId().equals(head.state().machineId())
                            && request.evidence().contains(commandRef),"original pending command differs");
                    var bound=actual.preparation().withArchive(archive);bound.prepare(command);var selected=bound.selected(command);
                    requireOriginalRead(selected,command,archive,context.frameLoader());
                    StrictJson.require(request.evidence().contains(selected.reference()),"original selected read missing from producer input evidence");
                    expected=PrisonerLedgerReducer12004.prepare(family,previousBody,command,selected);
                } else {
                    StrictJson.require(operation.equals("resolve"),"unsupported prisoner domain producer operation");
                    StrictJson.object(row,Set.of("schema","family","operation","previous_body","receipt","material"));
                    ExactRef receiptRef=ExactRef.fromJson(row.get("receipt"));ActionReceipt receipt=archive.loadReceipt(receiptRef);
                    StrictJson.require(archive.receiptReferenceOf(receipt).equals(receiptRef) && request.evidence().contains(receiptRef),"canonical original receipt bytes differ");
                    PrisonerLegacyBinding12004.verifyOriginal(head,archive,actual.preparation(),family,previousBody,receipt);
                    RawJson material=replayTerminal(head,receipt,archive,context);ExactRef materialRef=ExactRef.fromJson(row.get("material"));
                    StrictJson.require(archive.materialReferenceOf(material).equals(materialRef) && request.evidence().contains(materialRef),"original terminal material differs");
                    expected=PrisonerLedgerReducer12004.resolve(family,previousBody,receipt,material);
                }
            }
            StrictJson.require(Arrays.equals(expected.bytes(),body),"full prisoner body differs from actual original producer/reducer");
            return ActionCodec.sha256(expected.bytes());
        }
    }
    private static RawJson replayTerminal(WriterContracts.Head head,ActionReceipt receipt,ActionPorts.OutcomeArchive archive,RootRuntimeContext context)throws IOException {
        if(receipt.state() instanceof ActionState.RejectedBeforeDispatch)return PrisonerLedgerReducer12004.zeroMaterial(receipt);
        StrictJson.require(receipt.state() instanceof ActionState.Settled,"only a canonical independently observed terminal can clear pending");
        var settled=(ActionState.Settled)receipt.state();
        StrictJson.require(settled.settlement() instanceof ActionState.Applied || settled.settlement() instanceof ActionState.NonAppliedTerminal,
                "ACK/generic RED/other control result cannot resolve prisoner material");
        context.bindings().actualArchivedVerifier(receipt.command().operation()).orElseThrow(()->new IOException("actual prisoner domain replay is not installed"))
                .verifier().verify(head,receipt,archive);
        if(settled.settlement() instanceof ActionState.Applied) return NativeEffectEvidence.load(receipt,archive,context.frameLoader()).compatibleResult();
        return PrisonerTerminalEvidence12004.load(receipt,archive,context.frameLoader()).compatible();
    }
    private static void requireOriginalRead(PrisonerActionBinding12004.SelectedRead selected,ActionCommand command,
            ActionPorts.OutcomeArchive archive,NativeEffectEvidence.FrameLoader frames) {
        PlanningReadReceipt read=selected.receipt();
        StrictJson.require(archive.loadRead(selected.reference()).equals(read) && archive.readReferenceOf(read).equals(selected.reference())
                && PrisonerActionBinding12004.selectedFrameMatches(command,read) && read.request().source().equals(command.source())
                && read.request().sessionId().equals(command.sessionId()),"original selected read source/frame changed");
        StrictJson.require(read.original().equals(archive.load(archive.referenceOf(read.original()))),"original selected native dispatch changed");
        try {
            var actual=NativeWire.decode(read.original().originalPacket());
            StrictJson.require(actual instanceof NativeWire.CommandResult,"original selected packet is not a native command result");
            var result=(NativeWire.CommandResult)actual;
            StrictJson.require(result.requestId().equals(read.requestId()) && result.nativeOk()==read.original().nativeOk()
                    && Arrays.equals(result.payload().value(),read.original().originalFrame().bytes())
                    && result.result().token().map(NativeWire.Bytes::value).map(RawJson::new).equals(read.original().originalResultToken()),
                    "selected native response envelope/token differs from actual archived packet");
            var outbound=NativeWire.decodeExecuteRequest(read.original().outbound().orElseThrow(()->new IllegalArgumentException("selected original outgoing packet missing")).originalPacket());
            StrictJson.require(outbound.requestId().equals(read.requestId()) && outbound.step().equals(read.request().operation().value())
                    && outbound.expectedRevision().equals(Optional.of(command.before().frame().identity().nativeRevision()))
                    && outbound.expectedSnapshotRevision().isEmpty(),"selected original outgoing route/frame differs");
            ObjectNode fields=StrictJson.object();
            if(selected.intent().options() instanceof PrisonerOptionIntent.Negotiated negotiated)fields.put("release_option_mask_bits",negotiated.mask());
            selected.intent().materialTarget().ifPresent(target->fields.put("release_material_target_character_id",target));
            StrictJson.require(StrictJson.parse(outbound.normalizedAdditionalFields().value()).equals(fields),"selected original outgoing option/target fields differ");
        } catch(IOException failure) { throw new UncheckedIOException("original selected native packet is unreadable",failure); }
        for(PlanningReadGuard guard:List.of(read.before(),read.after())) {
            var frame=RootGuardEvidence.loadFrame(guard.binding(),archive,frames);
            StrictJson.require(frame.identity().equals(read.request().before()) && frame.source().equals(command.source())
                    && frame.sessionId().equals(command.sessionId()),"selected original guard reconstruction differs");
        }
    }
    private DomainBodies.BodyRef commit(Runtime actual,ContinuityStorePort.Session borrowed,PrisonerPlanningPorts.Family family,RawJson body,ObjectNode input,List<ExactRef> evidence)throws IOException {
        var archive=actual.context().archive().withSession(borrowed);
        ExactRef ref=archive.preserveMaterial(body);byte[] encoded=StrictJson.canonical(input,1_048_576);
        var request=new DomainBodies.ImportRequest(PrisonerLegacyBinding12004.slot(family),schema(family),ref,encoded,evidence,
                "prisoner:"+ActionCodec.sha256(encoded));
        NextImport scope=nextImport.get();if(scope!=null){scope.proof().requireCurrent(borrowed,scope.runtime().context());scope.captured().requireOriginals(borrowed,scope.runtime().context(),scope.proof());}
        var prepared=borrowed.previewImport(request);
        if(scope!=null){scope.proof().requireCurrent(borrowed,scope.runtime().context());scope.captured().requireOriginals(borrowed,scope.runtime().context(),scope.proof());}
        borrowed.commitImport(prepared);
        if(scope!=null){scope.proof().requireCurrent(borrowed,scope.runtime().context());scope.captured().requireOriginals(borrowed,scope.runtime().context(),scope.proof());}
        var observed=requireAvailable(borrowed,family);
        StrictJson.require(observed.reference().payload().equals(ref) && Arrays.equals(observed.canonicalBody(),body.bytes()),"actual prisoner domain writer readback differs");
        return observed.reference();
    }
    private static DomainBodies.Available requireAvailable(ContinuityStorePort.Session borrowed,PrisonerPlanningPorts.Family family)throws IOException {
        var read=borrowed.readDomain(PrisonerLegacyBinding12004.slot(family));
        if(!(read instanceof DomainBodies.Available available))throw new IOException("actual original prisoner body is unavailable; no implicit clear");
        return available;
    }
    private static ObjectNode input(PrisonerPlanningPorts.Family family,String operation) {
        return StrictJson.object().put("schema",INPUT).put("family",family.name()).put("operation",operation);
    }
    private static boolean sameJson(JsonNode left,JsonNode right){return Arrays.equals(StrictJson.canonical(left,1_048_576),StrictJson.canonical(right,1_048_576));}
    public static String schema(PrisonerPlanningPorts.Family family) {
        return PrisonerEpisodeLedger12004.contractSchema(family);
    }
    private static RawJson fresh(PrisonerPlanningPorts.Family family,org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity observed,
            org.xar.ck3.control.g2.common.G2Source source,String session,ExactRef basis) {
        var owner=new PrisonerEpisodeLedger12004.Owner(new SessionIdentity(observed.machineId(),observed.game(),session),observed.frame().identity().player().longValueExact(),observed.frame().episodeRunId(),source);
        return PrisonerEpisodeLedger12004.fresh(family,owner,basis);
    }
    private static PrisonerPlanningPorts.Family family(ActionCommand command) {
        PrisonerActionBinding12004.requireOperation(command.operation());
        return command.operation().equals(PrisonerOrdinaryPolicy12004.RELEASE)?PrisonerPlanningPorts.Family.RELEASE:PrisonerPlanningPorts.Family.RANSOM;
    }
}


