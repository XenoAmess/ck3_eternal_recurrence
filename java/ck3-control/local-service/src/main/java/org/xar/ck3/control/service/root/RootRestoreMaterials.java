package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.NativeCandidate;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.Request;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialStore;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.driver.DriverBootstrap;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.RestoreCapabilityAdoption;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.ImmutableArtifactStore;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.JavaGameLifecycle;
import org.xar.ck3.control.platform.ManagedGameSession;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual physical source/cold reducer adapter. Root alone stages, prepares, commits and adopts. */
public final class RootRestoreMaterials implements RootRestoreAdapters.MaterialPort {
    private static final int DOCUMENT_LIMIT=Math.min(DriverJson.MAX_NATIVE_BYTES,ImmutableArtifactStore.MAXIMUM_ARTIFACT_BYTES);
    private static final int DRIVER_LIMIT=Math.min(DriverCheckpointStore.MAX_DRIVER_BYTES,ImmutableArtifactStore.MAXIMUM_ARTIFACT_BYTES);
    private static final int LIFECYCLE_LIMIT=65536;
    private record Originals(RootRestoreMaterialProjection.Input projection, Obj auxiliary,
            FileWitness savedMaterial, List<WriterContracts.Pin> pins) {
        private Originals { Objects.requireNonNull(projection);Objects.requireNonNull(auxiliary);Objects.requireNonNull(savedMaterial);pins=List.copyOf(pins); }
    }
    private record Capture(Request request,NativeCandidate nativeCandidate,DriverSnapshotFacts.Stamp abandoned,
            Originals originals,RootRestoreMaterialProjection.Reduced reduced,RootRestoreAdapters.Materials materials,
            DriverStateSnapshot.Complete saved,DriverSnapshotFacts.Known originalAbandoned) { }
    /** Actual cold capture only. No serialized form, public constructor or borrowed Session is retained. */
    public static final class ColdAdoption {
        private final RootRestoreMaterials issuer;private final String requestId;private final DriverBootstrap.Seed seed;
        private ColdAdoption(RootRestoreMaterials issuer,String requestId,DriverBootstrap.Seed seed) {
            this.issuer=issuer;this.requestId=requestId;this.seed=seed;
        }
        /** Reuses the original writer and real cold reducer; this does not connect, query or mutate the Game. */
        public void requireCurrent(Session same,DriverBootstrap.Seed exact,NativeGameTransport actual)throws IOException {
            issuer.requireColdAdoption(same,this,exact,actual);
        }
        /** The real retained policy selects projection; public null DATA cannot issue this private ticket. */
        public boolean hasNativeCampaignProjection(Session same,DriverBootstrap.Seed exact,NativeGameTransport actual)throws IOException {
            return issuer.requireNativeCampaignProjection(same,this,exact,actual,false);
        }
        public RootFrozenRunProfile.FrozenRunProfile requireNativeCampaignProjection(Session same,
                DriverBootstrap.Seed exact,NativeGameTransport actual)throws IOException {
            issuer.requireNativeCampaignProjection(same,this,exact,actual,true);
            return issuer.originalFrozen.orElseThrow(()->new IOException("ordinary restore has no native campaign profile"));
        }
        public ManagedGameSession requireNativeCampaignGame(Session same,DriverBootstrap.Seed exact,
                NativeGameTransport actual)throws IOException {
            issuer.requireNativeCampaignProjection(same,this,exact,actual,true);
            return issuer.captures.get(requestId).materials().replacement();
        }
    }
    private final ContinuityWriter writer;
    private final NativeOutcomeArchive archive;
    private final JavaGameLifecycle lifecycle;
    private final CheckpointFiles files;
    private final DriverCheckpointStore drivers;
    private final SavedCheckpointMaterialStore savedSources;
    private final DriverBootstrap.Adopted previous;
    private final RestoreCapabilityAdoption capabilities;
    private final ExactRef producerSource;
    private final int retainedFrames;
    private final Optional<RootFrozenRunProfile.FrozenRunProfile> originalFrozen;
    private final Optional<ManagedGameSession> ordinaryPrevious;
    private final Map<String,Capture> captures=new LinkedHashMap<>();

    public RootRestoreMaterials(ContinuityWriter writer,NativeOutcomeArchive archive,JavaGameLifecycle lifecycle,
            CheckpointFiles files,DriverCheckpointStore drivers,SavedCheckpointMaterialStore savedSources,
            DriverBootstrap.Adopted previous,ExactRef producerSource,int retainedFrames,
            RootFrozenRunProfile.FrozenRunProfile originalFrozen) {
        this(writer,archive,lifecycle,files,drivers,savedSources,previous,producerSource,retainedFrames,
                Optional.of(originalFrozen),Optional.empty());
    }

    static RootRestoreMaterials ordinary(ContinuityWriter writer,NativeOutcomeArchive archive,JavaGameLifecycle lifecycle,
            CheckpointFiles files,DriverCheckpointStore drivers,SavedCheckpointMaterialStore savedSources,
            DriverBootstrap.Adopted previous,ExactRef producerSource,int retainedFrames,ManagedGameSession actualOriginal)throws IOException {
        Objects.requireNonNull(lifecycle);Objects.requireNonNull(actualOriginal);Objects.requireNonNull(previous);
        actualOriginal.verify();
        if(lifecycle.currentSession().orElseThrow(()->new IOException("actual managed owner unavailable"))!=actualOriginal
                ||!previous.session().machineId().equals(actualOriginal.machineId())
                ||!previous.session().game().equals(actualOriginal.generation())
                ||!previous.session().sessionId().equals(actualOriginal.sessionId()))
            throw new IOException("ordinary restore materials require this actual current Driver and managed owner");
        previous.producer().requireSameTransport(actualOriginal.nativeTransport(),previous.source());
        return new RootRestoreMaterials(writer,archive,lifecycle,files,drivers,savedSources,previous,producerSource,retainedFrames,
                Optional.empty(),Optional.of(actualOriginal));
    }

    private RootRestoreMaterials(ContinuityWriter writer,NativeOutcomeArchive archive,JavaGameLifecycle lifecycle,
            CheckpointFiles files,DriverCheckpointStore drivers,SavedCheckpointMaterialStore savedSources,
            DriverBootstrap.Adopted previous,ExactRef producerSource,int retainedFrames,
            Optional<RootFrozenRunProfile.FrozenRunProfile> originalFrozen,Optional<ManagedGameSession> ordinaryPrevious) {
        this.writer=Objects.requireNonNull(writer);this.archive=Objects.requireNonNull(archive);this.lifecycle=Objects.requireNonNull(lifecycle);
        this.files=Objects.requireNonNull(files);this.drivers=Objects.requireNonNull(drivers);this.savedSources=Objects.requireNonNull(savedSources);
        this.previous=Objects.requireNonNull(previous);this.producerSource=Objects.requireNonNull(producerSource);this.retainedFrames=retainedFrames;
        this.originalFrozen=Objects.requireNonNull(originalFrozen);this.ordinaryPrevious=Objects.requireNonNull(ordinaryPrevious);
        StrictJson.require(originalFrozen.isPresent()!=ordinaryPrevious.isPresent(),"one actual restore material branch required");
        StrictJson.require(archive.writer()==writer&&producerSource.bytes()>0&&retainedFrames>=2&&retainedFrames<=4096,
                "same original writer/archive and bounded source-qualified retention required");
        capabilities=new RestoreCapabilityAdoption(archive);
    }
    @Override public synchronized RootRestoreAdapters.Materials capture(Session borrowed,Request request,NativeCandidate actual,
            DriverStateSnapshot.Complete saved,DriverSnapshotFacts.Known abandoned) throws IOException {
        try {
        requireHead(borrowed,request);Capture existing=captures.get(request.requestId());
        if(existing!=null)return replay(borrowed,request,actual,saved,abandoned,existing.materials());
        StrictJson.require(captures.size()<64,"bounded original restore material retention exhausted");
        ManagedGameSession replacement=replacement(request,actual);
        replacement.launchPlan().sources().requireLoadedClass(RootRestoreMaterials.class);
        replacement.launchPlan().sources().requireLoadedClass(RootRestoreMaterialProjection.class);
        Originals originals=readOriginals(borrowed,request,actual,saved,abandoned,replacement);
        var reduced=RootRestoreMaterialProjection.reduce(originals.projection());
        ExactRef full=archive.preserveArtifact(borrowed,reduced.provisional().encode(),DRIVER_LIMIT);
        ExactRef completed=archive.preserveArtifact(borrowed,OpportunityJson.encode(reduced.completedRow()),DOCUMENT_LIMIT);
        var seed=new DriverBootstrap.Seed(full,abandoned.originalHistoryBasis(),abandoned.stamp().driverVersion(),
                abandoned.stamp().episodeEpoch(),actual.actual().session(),originals.auxiliary(),abandoned.loop());
        var material=new RootRestoreAdapters.Materials(seed,replacement,completed,originals.projection().abandonedSnapshot(),
                new OriginalCoverage(abandoned),retainedFrames,producerSource,new ColdAdoption(this,request.requestId(),seed));
        verifyReduced(borrowed,reduced,material);for(var pin:originals.pins())borrowed.verifyPin(pin);
        captures.put(request.requestId(),new Capture(request,actual,abandoned.stamp(),originals,reduced,material,saved,abandoned));return material;
        } catch(UncheckedIOException originalUnavailable) { throw originalUnavailable.getCause(); }
    }
    @Override public synchronized RootRestoreAdapters.Materials replay(Session borrowed,Request request,NativeCandidate actual,
            DriverStateSnapshot.Complete saved,DriverSnapshotFacts.Known abandoned,RootRestoreAdapters.Materials original) throws IOException {
        try {
        requireHead(borrowed,request);Capture retained=captures.get(request.requestId());
        StrictJson.require(retained!=null&&retained.materials()==original&&retained.request().equals(request)
                &&retained.abandoned().equals(abandoned.stamp())&&sameRaw(retained.nativeCandidate(),actual),
                "restore material must be replayed against its exact original capture");
        for(var pin:retained.originals().pins())borrowed.verifyPin(pin);
        ManagedGameSession current=replacement(request,actual);
        StrictJson.require(current==original.replacement(),"actual original replacement owner changed");
        // All operations below reread retained physical sources. No native query, artifact publication or mutation runs here.
        Originals reread=readOriginals(borrowed,request,retained.nativeCandidate(),saved,abandoned,current);
        StrictJson.require(sameProjectionSources(reread.projection(),retained.originals().projection())&&reread.auxiliary().equals(retained.originals().auxiliary())
                &&reread.savedMaterial().equals(retained.originals().savedMaterial())&&reread.pins().equals(retained.originals().pins()),
                "same-lock actual cold source replay differs from its original physical witness");
        var reduced=RootRestoreMaterialProjection.reduce(reread.projection());
        StrictJson.require(Arrays.equals(reduced.provisional().encode(),retained.reduced().provisional().encode())
                &&reduced.completedRow().equals(retained.reduced().completedRow())&&reduced.restoredSemantic().equals(retained.reduced().restoredSemantic()),
                "real cold reducer replay changed the original complete projection");
        verifyReduced(borrowed,reduced,original);for(var pin:retained.originals().pins())borrowed.verifyPin(pin);return original;
        } catch(UncheckedIOException originalUnavailable) { throw originalUnavailable.getCause(); }
    }
    private synchronized void requireColdAdoption(Session same,ColdAdoption ticket,DriverBootstrap.Seed exact,
            NativeGameTransport actual)throws IOException {
        Objects.requireNonNull(ticket);Objects.requireNonNull(exact);Objects.requireNonNull(actual);writer.requireSession(same);
        Capture retained=captures.get(ticket.requestId);
        StrictJson.require(ticket.issuer==this&&ticket.seed==exact&&retained!=null
                &&retained.materials().coldAdoption()==ticket&&retained.materials().provisional()==exact,
                "cold adoption requires this issuer's exact original private capture and Seed");
        requireHead(same,retained.request());ManagedGameSession owner=retained.materials().replacement();owner.verify();
        StrictJson.require(owner.nativeTransport()==actual,"cold adoption transport differs from the actual replacement owner");
        var received=actual.diagnostics();
        StrictJson.require(received.receivedState()==NativeGameTransport.ReceivedState.HELLO_VERIFIED
                &&received.originalHello().isPresent()&&received.session().equals(Optional.of(exact.expectedSession()))
                &&actual.pipeName().equals(retained.originals().projection().actualPipe()),
                "cold adoption lost its actual received replacement HELLO or original pipe/session");
        replay(same,retained.request(),retained.nativeCandidate(),retained.saved(),retained.originalAbandoned(),retained.materials());
        owner.verify();writer.requireSession(same);requireHead(same,retained.request());
    }
    private synchronized boolean requireNativeCampaignProjection(Session same,ColdAdoption ticket,DriverBootstrap.Seed exact,
            NativeGameTransport actual,boolean required)throws IOException {
        requireColdAdoption(same,ticket,exact,actual);
        if (originalFrozen.isEmpty()) {
            if (required) {
                throw new IOException("ordinary restore cannot issue native campaign ticket");
            }
            return false;
        }
        
        var frozen = originalFrozen.get();
        boolean selected=switch(frozen.initialPolicy().kind()) {
            case NATIVE_CAMPAIGN_FIXTURE,NATIVE_CAMPAIGN_SAVED -> true;
            case ROGUE_ONE_LIFE,ORDINARY_CAMPAIGN_SUCCESSION -> false;
        };
        StrictJson.require(!required||selected,"actual original policy has no explicit native campaign projection");
        if(!selected)return false;
        // This Frozen belongs to the original run. Never qualify it against the replacement Saved plan.
        frozen.requireExplicitNativeCampaign();
        previous.producer().requireNativeCampaignProjectionOrigin(frozen);
        Capture retained=captures.get(ticket.requestId);
        requireSavedNativeCampaign(same,retained);
        ManagedGameSession owner=replacement(retained.request(),retained.nativeCandidate());
        StrictJson.require(owner==retained.materials().replacement()&&owner.nativeTransport()==actual
                &&retained.reduced().provisional().successionLifecycle() instanceof DriverStateSnapshot.NullValue,
                "native campaign restore crossed its genuine Saved replacement or lost the original null lifecycle");
        requireColdAdoption(same,ticket,exact,actual);return true;
    }
    private void requireSavedNativeCampaign(Session same,Capture retained)throws IOException {
        SavedCheckpointMaterial material=requireRetainedSource(same,savedSources,retained.request(),retained.saved());
        requireNativeCampaignSavedOriginals(same,archive,material.session(),material.sourceSemantic(),material.savedDriver());
        material.requireRetained(same);files.verify(material.witness());
    }
    /** Archived DATA consistency only. Only the private capture above may choose the live producer branch. */
    static void requireNativeCampaignSavedOriginals(Session same,NativeOutcomeArchive archive,
            org.xar.ck3.control.application.session.SessionPorts.SessionIdentity savedOwner,
            org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence original,
            DriverStateSnapshot.Complete savedDriver)throws IOException {
        Objects.requireNonNull(archive).writer().requireSession(same);
        Objects.requireNonNull(savedOwner);Objects.requireNonNull(original);Objects.requireNonNull(savedDriver);
        StrictJson.require(original.frame().observationVersion()
                    ==org.xar.ck3.control.application.driver.DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION
                &&savedDriver.successionLifecycle() instanceof DriverStateSnapshot.NullValue,
                "explicit native campaign restore requires its actual saved profile-four SEM and explicit null Driver lifecycle");
        StrictJson.require(Arrays.equals(savedDriver.encode(),archive.readArtifact(same,original.originalDriver(),DRIVER_LIMIT)),
                "native campaign saved proof differs from its actual complete original Driver");
        new org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier(archive::readArtifact)
                .verify(same,savedOwner,original);
        archive.writer().requireSession(same);
    }
    private Originals readOriginals(Session borrowed,Request request,NativeCandidate actual,DriverStateSnapshot.Complete saved,
            DriverSnapshotFacts.Known abandoned,ManagedGameSession replacement) throws IOException {
        requireHead(borrowed,request);var pins=new ArrayList<WriterContracts.Pin>();
        pin(borrowed,producerSource,DOCUMENT_LIMIT,pins);
        if(originalFrozen.isPresent())
            for(ExactRef ref:originalFrozen.orElseThrow().originalReferences())pin(borrowed,ref,WriterContracts.MAX_PIN_BYTES,pins);
        SavedCheckpointMaterial material=requireRetainedSource(borrowed,savedSources,request,saved);
        files.verify(material.witness());
        StrictJson.require(Arrays.equals(saved.encode(),drivers.readVerifiedOriginal(request.pair(),saved.session()).encode()),"cold source differs from the actual physical saved Driver");
        pin(borrowed,request.pair().save().reference(),WriterContracts.MAX_PIN_BYTES,pins);
        pin(borrowed,request.pair().driver().reference(),DRIVER_LIMIT,pins);
        pin(borrowed,material.reference(),DOCUMENT_LIMIT,pins);
        for(ExactRef source:material.sourceSemantic().references())pin(borrowed,source,WriterContracts.MAX_PIN_BYTES,pins);
        Obj savedSemantic=DriverJson.object(archive.readArtifact(borrowed,material.sourceSemantic().semantic(),DOCUMENT_LIMIT),DOCUMENT_LIMIT);
        pin(borrowed,DriverObservationEvidenceReader.reference(savedSemantic.get("java_driver_facts_evidence")),DOCUMENT_LIMIT,pins);
        StrictJson.require(abandoned.stamp().game().equals(request.current().observed().game())
                &&abandoned.stamp().episodeRunId().equals(request.current().observed().frame().episodeRunId())
                &&abandoned.driver().session().actorId().equals(request.current().observed().frame().identity().player()),
                "abandoned original Driver crossed current restore request");
        // Retain the complete canonical basis even when the saved prefix contains UNKNOWN rows.
        byte[] basis=archive.readArtifact(borrowed,abandoned.originalHistoryBasis(),DRIVER_LIMIT);
        DriverStateSnapshot.decodeComplete(basis);pin(borrowed,abandoned.originalHistoryBasis(),DRIVER_LIMIT,pins);
        ExactRef abandonedDriver=archive.inSession(borrowed,bound->bound.materialReferenceOf(RawJson.fullMaterial(abandoned.driver().encode())));
        StrictJson.require(Arrays.equals(archive.readArtifact(borrowed,abandonedDriver,DRIVER_LIMIT),abandoned.driver().encode()),"actual abandoned full Driver source drift");
        pin(borrowed,abandonedDriver,DRIVER_LIMIT,pins);
        if(abandoned.loop().isPresent())pin(borrowed,abandoned.loop().orElseThrow().originalFacts(),DOCUMENT_LIMIT,pins);
        org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete before;
        try { before=previous.observations().requireRetained(request.current().observed(),request.current().nativeEvidence()); }
        catch(IllegalStateException missingOriginal) { throw new IOException("actual original abandoned frame unavailable; no replacement observation or fabricated before snapshot",missingOriginal); }
        StrictJson.require(before.source().equals(request.current().source())&&before.sessionId().equals(request.current().sessionId())
                &&before.identity().game().equals(abandoned.stamp().game()),"actual retained abandoned native frame differs from original request");
        byte[] beforePacket=archive.readArtifact(borrowed,before.originalEvidence(),DOCUMENT_LIMIT);
        var decodedBefore=NativeWire.decode(beforePacket);
        StrictJson.require(decodedBefore instanceof NativeWire.Snapshot,"actual abandoned original native snapshot missing");
        var originalBefore=(NativeWire.Snapshot)decodedBefore;
        StrictJson.require(originalBefore.snapshotId().equals(before.identity().frame().snapshotId())
                &&originalBefore.revision().equals(before.identity().frame().identity().nativeRevision()),"retained abandoned original packet belongs to another frame");
        pin(borrowed,before.originalEvidence(),DOCUMENT_LIMIT,pins);
        var replaced=(JavaGameLifecycle.Replaced)lifecycle.queryReplacement(request.requestId());
        Obj control=readObject(borrowed,replaced.lifecycleEvidence(),LIFECYCLE_LIMIT,pins);
        StrictJson.require(control.members().keySet().equals(Set.of("schema","parentLifecycleIntentId","phase","oldPid","oldBirthDecimal","save","stopEvidence","launchEvidence"))
                &&reference(control.get("save")).equals(request.pair().save().reference()),"original lifecycle physical SAVE/control field contract drift");
        ExactRef stopped=reference(control.get("stopEvidence")),launched=reference(control.get("launchEvidence"));
        StrictJson.require(launched.equals(replaced.replacement().launchEvidence()),"retained launch evidence differs from original replacement control");
        Obj stop=readObject(borrowed,stopped,LIFECYCLE_LIMIT,pins),launch=readObject(borrowed,launched,LIFECYCLE_LIMIT,pins);
        requireLifecycleRows(stop,launch,new LifecycleJoin(request.current().observed().machineId(),request.current().sessionId(),
                replacement.sessionId(),request.current().observed().game(),replacement.generation(),JavaGameLifecycle.replacementRequestId(request.requestId())));
        var helloDocument=readPinned(borrowed,files,replaced.replacement().nativeHello(),DOCUMENT_LIMIT);pins.add(helloDocument.pin());
        var decodedHello=NativeWire.decode(helloDocument.contents());
        StrictJson.require(decodedHello instanceof NativeWire.Hello,"retained actual lifecycle HELLO packet unavailable");
        var hello=(NativeWire.Hello)decodedHello;
        StrictJson.require(hello.pid()==actual.actual().session().game().pid()&&hello.connectionGeneration().equals(actual.actual().session().connectionGeneration()),
                "original lifecycle HELLO packet crossed actual native session");
        byte[] packet=archive.readArtifact(borrowed,actual.originalNativePacket(),DOCUMENT_LIMIT);
        StrictJson.require(Arrays.equals(packet,actual.actual().originalPacket()),"actual native replacement packet differs from archived original");
        requireNativePacket(actual,packet);
        pin(borrowed,actual.originalNativePacket(),DOCUMENT_LIMIT,pins);
        Obj nativeState=DriverJson.object(actual.actual().state().bytes(),DriverJson.MAX_NATIVE_BYTES);
        // Replay the sole capability state producer from saved SEM, then reduce the actual original private fields.
        var recovered=capabilities.replay(borrowed,material.sourceSemantic(),saved);
        pin(borrowed,recovered.stateSource(),DOCUMENT_LIMIT,pins);
        // state/v2 replay is the complete private owner auxiliary, including noncache fields and deletions.
        // An older semantic_source can be a valid mint predecessor, but cannot supply the saved owner's current fields.
        Obj auxiliary=capabilities.requireReduced(recovered,RootRestoreMaterialProjection.reduceAuxiliary(recovered.ownerAuxiliary(),nativeState));
        var input=new RootRestoreMaterialProjection.Input(request.requestId(),request.current().observed().game(),actual.actual().session(),
                replacement.nativeTransport().pipeName(),actual.actual().snapshotId(),actual.actual().nativeRevision(),saved,abandoned.driver(),nativeState,
                control,replaced.lifecycleEvidence(),actual.originalNativePacket(),Optional.of(before.semantic()));
        material.requireRetained(borrowed);files.verify(material.witness());drivers.verifyOriginal(request.pair(),saved.session());
        for(var pin:pins)borrowed.verifyPin(pin);return new Originals(input,auxiliary,material.witness(),pins);
    }
    /** Same configured aggregate and original issuer only. Retained source validation grants no replacement Game or physical reload. */
    public static SavedCheckpointMaterial requireRetainedSource(Session same,SavedCheckpointMaterialStore actualSources,
            Request request,DriverStateSnapshot.Complete actualSaved)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(actualSources);Objects.requireNonNull(request);Objects.requireNonNull(actualSaved);
        SavedCheckpointMaterial material=request.savedMaterial();actualSources.requireOwn(material);material.requireRetained(same);
        StrictJson.require(material.pair().equals(request.pair())&&Arrays.equals(material.savedDriver().encode(),actualSaved.encode()),
                "actual restore request and original complete saved Driver differ from the private typed material");
        return material;
    }
    private ManagedGameSession replacement(Request request,NativeCandidate actual) throws IOException {
        var retained=lifecycle.queryReplacement(request.requestId());
        if(!(retained instanceof JavaGameLifecycle.Replaced replaced))throw new IOException("actual original lifecycle replacement is unresolved; material cannot mint Game authority");
        ManagedGameSession replacement=replaced.replacement().session();replacement.verify();
        StrictJson.require(lifecycle.currentSession().orElseThrow(()->new IOException("actual managed owner unavailable"))==replacement
                &&replaced.previous().equals(request.current().observed().game())&&replacement.generation().equals(actual.actual().session().game())
                &&replacement.machineId().equals(actual.actual().session().machineId())&&replacement.sessionId().equals(actual.actual().session().sessionId())
                &&replacement.launchPlan().requestId().equals(JavaGameLifecycle.replacementRequestId(request.requestId()))
                &&replacement.launchPlan().load() instanceof NativeLaunchPlan.SavedGame,"original saved replacement owner/session differs");
        if(ordinaryPrevious.isPresent()) {
            ManagedGameSession original=ordinaryPrevious.orElseThrow();
            StrictJson.require(original.generation().equals(replaced.previous())
                    &&original.generation().equals(request.current().observed().game())
                    &&original.machineId().equals(request.current().observed().machineId())
                    &&original.sessionId().equals(request.current().sessionId()),
                    "ordinary restore crossed its actual retained previous managed owner");
            RootRestoreMaterialFactory.requireOrdinaryConfiguration(original.launchPlan(),replacement.launchPlan());
        }
        var launchSave=((NativeLaunchPlan.SavedGame)replacement.launchPlan().load()).save();
        StrictJson.require(launchSave.path().equals(request.pair().save().reference().path())&&launchSave.bytes()==request.pair().save().reference().bytes()
                &&launchSave.sha256().equals(request.pair().save().reference().sha256()),"actual lifecycle loaded another physical saved source");return replacement;
    }
    private void requireHead(Session borrowed,Request request) throws IOException {
        writer.requireSession(borrowed);StrictJson.require(borrowed.head().digest().equals(request.expectedHeadDigest()),"restore material requires original unchanged writer head");
    }
    private void verifyReduced(Session borrowed,RootRestoreMaterialProjection.Reduced reduced,RootRestoreAdapters.Materials material) throws IOException {
        StrictJson.require(Arrays.equals(archive.readArtifact(borrowed,material.provisional().fullDriver(),DRIVER_LIMIT),reduced.provisional().encode())
                &&DriverJson.object(archive.readArtifact(borrowed,material.completedRow(),DOCUMENT_LIMIT),DriverJson.MAX_NATIVE_BYTES).equals(reduced.completedRow()),
                "actual full cold Driver/completed row differs from original archived result");
    }
    /** Same writer plus CheckpointFiles physical witness; equal bytes alone never erase a replaced FileID. */
    public record PinnedDocument(WriterContracts.Pin pin,byte[] contents) {
        public PinnedDocument { Objects.requireNonNull(pin);Objects.requireNonNull(contents);contents=contents.clone(); }
        @Override public byte[] contents(){return contents.clone();}
    }
    public static PinnedDocument readPinned(Session borrowed,CheckpointFiles files,ExactRef ref,int maximumBytes) throws IOException {
        Objects.requireNonNull(borrowed);Objects.requireNonNull(files);Objects.requireNonNull(ref);
        StrictJson.require(maximumBytes>0&&maximumBytes<=WriterContracts.MAX_PIN_BYTES&&ref.bytes()>0&&ref.bytes()<=maximumBytes,"bounded actual physical source required");
        var captured=borrowed.capturePin(ref,maximumBytes);
        var witness=files.observe(Path.of(ref.path())).orElseThrow(()->new IOException("actual original restore source missing"));
        StrictJson.require(witness.reference().equals(ref),"actual physical source content differs");
        byte[] bytes=files.read(witness,maximumBytes);files.verify(witness);borrowed.verifyPin(captured);
        StrictJson.require(bytes.length==ref.bytes()&&DriverJson.sha256(bytes).equals(ref.sha256()),"physical source read differs from exact original reference");
        return new PinnedDocument(captured,bytes);
    }
    private void pin(Session borrowed,ExactRef ref,int maximum,List<WriterContracts.Pin> pins) throws IOException {
        pins.add(readPinned(borrowed,files,ref,maximum).pin());
    }
    private Obj readObject(Session borrowed,ExactRef ref,int maximum,List<WriterContracts.Pin> pins) throws IOException {
        var original=readPinned(borrowed,files,ref,maximum);pins.add(original.pin());return DriverJson.object(original.contents(),maximum);
    }
    /** Verify real terminal/accounting and HELLO source separately from actual paused-map proof. */
    public record LifecycleJoin(String machineId,String previousSessionId,String replacementSessionId,
            GameGeneration previous,GameGeneration replacement,String launchRequestId) {
        public LifecycleJoin {
            StrictJson.text(machineId);StrictJson.text(previousSessionId);StrictJson.text(replacementSessionId);StrictJson.text(launchRequestId);
            Objects.requireNonNull(previous);Objects.requireNonNull(replacement);
            StrictJson.require(!previous.equals(replacement),"physical replacement generation must differ");
        }
    }
    public static void requireLifecycleRows(Obj stopped,Obj launched,LifecycleJoin expected) {
        requireEvent(stopped,"STOPPED",expected.machineId(),expected.previousSessionId(),expected.previous());
        requireEvent(launched,"HELLO",expected.machineId(),expected.replacementSessionId(),expected.replacement());
        StrictJson.require(text(launched.get("requestId"),expected.launchRequestId()),"original HELLO child request differs");
        Obj accounting=OpportunityJson.object(stopped.get("accounting"),"actual stopped Job accounting");
        Obj terminal=OpportunityJson.object(stopped.get("terminal"),"actual stopped inner terminal");
        Obj terminalAccounting=OpportunityJson.object(terminal.get("accounting"),"actual inner Job accounting");
        StrictJson.require(OpportunityJson.integer(accounting.get("activeProcesses"),"actual active Job count").signum()==0
                &&OpportunityJson.integer(terminalAccounting.get("activeProcesses"),"actual inner Job count").signum()==0
                &&terminal.get("stopReason")==Nil.INSTANCE,"original stopped root and Job0 terminal not proved");
        // Actual OWNER_STOP can return exit125, and a real natural exit259 remains nonzero; neither is an ACK.
        OpportunityJson.integer(terminal.get("exitCode"),"actual consumed inner exit code");
    }
    private static void requireEvent(Obj row,String event,String machine,String session,GameGeneration generation) {
        Obj game=OpportunityJson.object(row.get("game"),"actual lifecycle process identity");
        StrictJson.require(text(row.get("schema"),"xar.java-game-lifecycle-event/v1")&&text(row.get("event"),event)
                &&text(row.get("machineId"),machine)&&text(row.get("sessionId"),session)
                &&OpportunityJson.integer(game.get("pid"),"actual lifecycle PID").longValueExact()==generation.pid()
                &&text(game.get("creationFiletimeDecimal"),generation.creationFiletime().value().toString()),"actual lifecycle terminal/HELLO identity drift");
        java.time.Instant.parse(OpportunityJson.text(row.get("observedAtUtc"),"actual lifecycle observation time"));
    }
    public static void requireNativePacket(NativeCandidate actual,byte[] original) throws IOException {
        var decoded=NativeWire.decode(original);
        StrictJson.require(decoded instanceof NativeWire.Snapshot,"actual restore original native snapshot required");
        var snapshot=(NativeWire.Snapshot)decoded;
        StrictJson.require(snapshot.snapshotId().equals(actual.actual().snapshotId())&&snapshot.revision().equals(actual.actual().nativeRevision())
                &&Arrays.equals(snapshot.state().value(),actual.actual().state().bytes())&&Arrays.equals(original,actual.actual().originalPacket()),
                "actual restore native envelope/state/source differs");
    }
    private final class OriginalCoverage implements DriverBootstrap.HistoryCoverageReader {
        private final DriverSnapshotFacts.Known original;
        private OriginalCoverage(DriverSnapshotFacts.Known original){this.original=original;}
        @Override public Optional<? extends DriverBootstrap.ArchivedActionCoverage> originalFor(ActionReceipt receipt) throws IOException {
            Session borrowed=writer.borrowedSession();writer.requireSession(borrowed);String head=borrowed.head().digest();
            var matching=original.actionRows().stream().filter(row->row.actionId().equals(receipt.command().actionId())).findFirst();
            if(matching.isEmpty())return Optional.empty();var row=matching.orElseThrow();
            StrictJson.require(receipt.settled()&&row.bodySha256().equals(receipt.bodySha256())&&row.durableSequence()==receipt.sequence(),
                    "original history coverage crossed actual canonical receipt");
            ExactRef receiptSource=archive.inSession(borrowed,bound->bound.receiptReferenceOf(receipt));
            DriverBootstrap.ArchivedActionCoverage result=switch(row.coverageSource()) {
                case DriverSnapshotFacts.LegacyHistoryRow legacy -> {
                    Obj archived=DriverJson.object(archive.readArtifact(borrowed,legacy.originalRow(),DOCUMENT_LIMIT),DriverJson.MAX_NATIVE_BYTES);
                    Obj full=DriverJson.object(original.driver().commandHistory().get(Math.toIntExact(legacy.historyIndex()-1)).originalRow().json(),DriverJson.MAX_NATIVE_BYTES);
                    StrictJson.require(archived.equals(full),"original action row source differs from complete original Driver history");
                    yield new DriverBootstrap.ArchivedHistoryRow(receiptSource,legacy.historyIndex(),legacy.originalRow());
                }
                case DriverSnapshotFacts.CanonicalOnly canonical -> {
                    // The original private Known supplies this exact source. Sole codec replays its original
                    // material/record/receipt and proves membership in the actual borrowed writer's history.
                    DriverActionHistoryCodec.verifyCanonicalOnly(borrowed,receipt,canonical.originalSource(),archive.withSession(borrowed));
                    yield new DriverBootstrap.ArchivedCanonicalOnly(receiptSource,canonical.originalSource());
                }
            };
            writer.requireSession(borrowed);StrictJson.require(borrowed.head().digest().equals(head),"original action coverage changed its actual writer Head");
            return Optional.of(result);
        }
    }

    private static boolean sameRaw(NativeCandidate first,NativeCandidate second) {
        return first.actual().session().equals(second.actual().session())&&first.actual().snapshotId().equals(second.actual().snapshotId())
                &&first.actual().nativeRevision().equals(second.actual().nativeRevision())&&first.originalNativePacket().equals(second.originalNativePacket())
                &&Arrays.equals(first.actual().state().bytes(),second.actual().state().bytes())&&first.source().equals(second.source())&&first.lineageId().equals(second.lineageId());
    }
    private static boolean sameProjectionSources(RootRestoreMaterialProjection.Input first,RootRestoreMaterialProjection.Input second) {
        return first.requestId().equals(second.requestId())&&first.previous().equals(second.previous())&&first.replacement().equals(second.replacement())
                &&first.actualPipe().equals(second.actualPipe())&&first.snapshotId().equals(second.snapshotId())&&first.nativeRevision().equals(second.nativeRevision())
                &&Arrays.equals(first.saved().encode(),second.saved().encode())&&Arrays.equals(first.abandoned().encode(),second.abandoned().encode())
                &&first.actualNativeState().equals(second.actualNativeState())&&first.actualLifecycleControl().equals(second.actualLifecycleControl())
                &&first.lifecycleSource().equals(second.lifecycleSource())&&first.nativeSource().equals(second.nativeSource())
                &&first.abandonedSnapshot().equals(second.abandonedSnapshot());
    }
    private static ExactRef reference(Value value){return DriverObservationEvidenceReader.reference(value);}
    private static boolean text(Value value,String expected){return value instanceof Text word&&word.value().equals(expected);}
}
