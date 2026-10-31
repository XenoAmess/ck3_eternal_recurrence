package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import org.xar.ck3.control.application.action.ActionSnapshotReader;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.history.DriverRestoreHistoryProducer;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.SavedContinuityAttachment;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.ManagedGameSession;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.*;

/** One actual stage/prepare/commit/adopt chain; retry never creates another native replacement or writer event. */
public final class RootRestoreAdapters implements AttachmentPort, PublicationPort {
    private static final int ARCHIVED_DRIVER_BYTES = Math.min(DriverCheckpointStore.MAX_DRIVER_BYTES, ImmutableArtifactStore.MAXIMUM_ARTIFACT_BYTES);
    /** A real cold reducer plus the completed managed lifecycle row must supply these original artifacts. */
    public record Materials(DriverBootstrap.Seed provisional, ManagedGameSession replacement,
            ExactRef completedRow, Optional<Obj> abandonedSnapshot, DriverBootstrap.HistoryCoverageReader coverage,
            int retainedFrames,ExactRef producerSource,RootRestoreMaterials.ColdAdoption coldAdoption) {
        public Materials {
            Objects.requireNonNull(provisional); Objects.requireNonNull(replacement); Objects.requireNonNull(completedRow);
            Objects.requireNonNull(abandonedSnapshot);Objects.requireNonNull(coverage);Objects.requireNonNull(producerSource);
            Objects.requireNonNull(coldAdoption);
            StrictJson.require(retainedFrames >= 2 && retainedFrames <= 4096 && completedRow.bytes() > 0 && producerSource.bytes() > 0,
                    "bounded actual cold reducer, managed completed row and full history coverage required");
        }
    }
    public interface MaterialPort {
        Materials capture(ContinuityStorePort.Session borrowed, Request request, NativeCandidate actual,
                DriverStateSnapshot.Complete saved, DriverSnapshotFacts.Known abandoned) throws IOException;
        /** Re-derive solely from the original immutable artifacts. No Game action or cold reducer mutation. */
        Materials replay(ContinuityStorePort.Session borrowed, Request request, NativeCandidate actual,
                DriverStateSnapshot.Complete saved, DriverSnapshotFacts.Known abandoned, Materials original) throws IOException;
    }
    public interface PostAdoptionPort {
        /** Only the existing raw physical producer may capture the first source-qualified four-original SEM. */
        RootLifecycleAuthority physical(ContinuityStorePort.Session borrowed, DriverBootstrap.Adopted adopted,
                ManagedGameSession replacement, Request original,ReadWindow reads) throws IOException;
        /** Actual domain imports and the full runtime are legal only after the original service minted admission. */
        RestoredRuntime create(ContinuityStorePort.Session borrowed, DriverBootstrap.Adopted adopted,
                ManagedGameSession replacement, Request original, RestoreCheckpointService actualIssuer,
                RestoreBinding actualBinding, SavedAttachmentSourceStore actualSources) throws IOException;
    }
    /** These exact instances survive publication and the later ordinary-host handoff. */
    public record RestoredRuntime(NativeReadinessCollector collector, DriverCapabilityRuntime capabilities,
            org.xar.ck3.control.application.action.RootExecutableBindings bindings, RootPlanningReads reads,
            NativeReadinessCollector.PlanningInputsPort planningInputs,RootInstalledCatalog catalog) {
        public RestoredRuntime {
            Objects.requireNonNull(collector); Objects.requireNonNull(capabilities); Objects.requireNonNull(bindings);
            Objects.requireNonNull(reads);Objects.requireNonNull(planningInputs);Objects.requireNonNull(catalog);
            StrictJson.require(catalog.context().collector()==collector&&catalog.bindings()==bindings
                    &&catalog.context().reads()==reads,"restored runtime must retain its identical actual catalog/collector/bindings/reads");
        }
    }
    private static final class Stage {
        final Request request; final NativeCandidate nativeCandidate; final DriverStateSnapshot.Complete saved;
        final DriverSnapshotFacts.Known abandoned; final Materials material; final DriverBootstrap.Staged staged;
        final DriverBootstrap.Seed finalSeed; final Attachment attachment;
        DriverBootstrap.Adopted adopted; RootLifecycleAuthority physical; RestoredRuntime runtime; PublishedDriver published;
        ReadWindow reads;
        boolean physicalEntered; boolean runtimeEntered;
        Stage(Request request, NativeCandidate nativeCandidate, DriverStateSnapshot.Complete saved, DriverSnapshotFacts.Known abandoned,
                Materials material, DriverBootstrap.Staged staged, DriverBootstrap.Seed finalSeed, Attachment attachment,ReadWindow reads) {
            this.request = request; this.nativeCandidate = nativeCandidate; this.saved = saved; this.abandoned = abandoned;
            this.material = material; this.staged = staged; this.finalSeed = finalSeed; this.attachment = attachment;this.reads=Objects.requireNonNull(reads);
        }
    }
    private final ContinuityWriter writer;
    private final NativeOutcomeArchive archive;
    private final ActionSnapshotReader actions;
    private final DriverBootstrap.Adopted previous;
    private final SavedAttachmentSourceStore sources;
    private final SavedCheckpointMaterialStore savedMaterials;
    private final MaterialPort materials;
    private final PostAdoptionPort publications;
    private final ConcurrentHashMap<String, Stage> stages = new ConcurrentHashMap<>();
    public RootRestoreAdapters(ContinuityWriter writer, NativeOutcomeArchive archive, ActionSnapshotReader actions,
            DriverBootstrap.Adopted previous, SavedAttachmentSourceStore sources,SavedCheckpointMaterialStore savedMaterials,
            MaterialPort materials, PostAdoptionPort publications) {
        this.writer = Objects.requireNonNull(writer); this.archive = Objects.requireNonNull(archive); this.actions = Objects.requireNonNull(actions);
        this.previous = Objects.requireNonNull(previous); this.sources = Objects.requireNonNull(sources);
        this.savedMaterials=Objects.requireNonNull(savedMaterials);
        this.materials = Objects.requireNonNull(materials); this.publications = Objects.requireNonNull(publications);
        StrictJson.require(archive.writer() == writer && !materials.getClass().isSynthetic() && !materials.getClass().isAnonymousClass()
                && !publications.getClass().isSynthetic() && !publications.getClass().isAnonymousClass(),
                "same original writer/archive and named actual restore producers required");
    }
    @Override public synchronized Attachment prepare(Request request, NativeCandidate actual, DriverStateSnapshot.Complete saved,ReadWindow reads) throws IOException {
        Objects.requireNonNull(reads).requireOriginal(request);
        ContinuityStorePort.Session borrowed = writer.borrowedSession(); writer.requireSession(borrowed);
        Stage retained = stages.get(request.requestId());
        if (retained != null) { sameAttempt(retained, request, actual);retained.reads=reads; verifyAttachmentSource(borrowed, borrowed.head().state(), retained.attachment.request()); return retained.attachment; }
        StrictJson.require(stages.size() < 64, "bounded restore attempts require original reconciliation");
        DriverSnapshotFacts.Known abandoned = previous.authority().withFrozenFacts(borrowed, frozen -> {
            if (!(frozen.state() instanceof DriverSnapshotFacts.Known known)) throw new IOException("actual abandoned complete Driver unavailable");
            return known;
        });
        Materials material = materials.capture(borrowed, request, actual, saved, abandoned); material.replacement().verify();
        StrictJson.require(material.replacement().generation().equals(actual.actual().session().game())
                && material.provisional().expectedSession().equals(actual.actual().session()), "cold restore material crossed actual replacement native owner");
        DriverBootstrap.Staged staged;
        try {
            staged = DriverBootstrap.stageRestored(material.provisional(), abandoned.stamp(), borrowed, actions,
                    material.replacement().nativeTransport(), actual.source(), archive,
                    (ref, maximum) -> RootOriginalArtifacts.read(writer, archive, borrowed, ref, maximum, actual.source().sourceRef()), material.coverage(), material.retainedFrames(), reads.deadline(),material.coldAdoption());
        } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IOException("restore staging interrupted; original replacement retained", interrupted); }
        DriverStateSnapshot.Complete completed = archive.inSession(borrowed, bound -> {
            DriverStateSnapshot.Complete provisional = DriverStateSnapshot.decodeComplete(bound.loadMaterial(material.provisional().fullDriver()).bytes());
            DriverRestoreHistoryProducer.Binding binding = new DriverRestoreHistoryProducer.Binding(request.requestId(), request.current().observed().game(),
                    actual.actual().session().game(), provisional.session(), request.pair().frame().frame().identity().dateRaw());
            var candidate = DriverRestoreHistoryProducer.prepare(bound, saved, material.provisional().fullDriver(), material.completedRow(), binding);
            return DriverRollbackFailurePublication.project(candidate.driver(), abandoned.driver(), staged.first().semantic(), material.abandonedSnapshot(), 64);
        });
        ExactRef finalDriver = archive.preserveArtifact(borrowed, completed.encode(), ARCHIVED_DRIVER_BYTES);
        DriverBootstrap.Seed seed = new DriverBootstrap.Seed(finalDriver, material.provisional().originalHistoryBasis(),
                Math.addExact(abandoned.stamp().driverVersion(), 1), material.provisional().episodeEpoch(), actual.actual().session(),
                material.provisional().auxiliary(), material.provisional().loop());
        savedMaterials.requireOwn(request.savedMaterial());request.savedMaterial().requirePhysical(borrowed);
        Attachment physical = savedMaterials.prepare(request, actual, saved);
        var details = physical.request().detailsObject().deepCopy(); var delta = details.putObject("driver_snapshot");
        delta.put("expected_version", abandoned.stamp().driverVersion()); delta.put("expected_epoch", abandoned.stamp().episodeEpoch());
        delta.put("next_epoch", seed.episodeEpoch()); delta.put("before_sha256", abandoned.stamp().driverSha256()); delta.put("after_sha256", finalDriver.sha256());
        details.set("driver_after_game", actual.actual().session().game().toJson());
        details.set("restored_full_driver", finalDriver.toJson()); details.set("restored_staged_driver", material.provisional().fullDriver().toJson());
        details.set("restored_completed_row", material.completedRow().toJson());
        LinkedHashSet<ExactRef> evidence = new LinkedHashSet<>(physical.request().evidence());
        evidence.addAll(java.util.List.of(finalDriver, material.provisional().fullDriver(), material.completedRow(), material.producerSource()));
        WriterContracts.Request event = new WriterContracts.Request(physical.request().kind(), ContinuityJson.canonical(details), java.util.List.copyOf(evidence));
        SavedContinuityAttachment.Input original = physical.input();
        Attachment attachment = new Attachment(event, new SavedContinuityAttachment.Input(original.predecessor(), event.details(), original.basis(), original.game(), original.opening(), original.progress()),physical.material());
        Stage created = new Stage(request, actual, saved, abandoned, material, staged, seed, attachment,reads); stages.put(request.requestId(), created);
        verifyAttachmentSource(borrowed, borrowed.head().state(), event); return attachment;
    }
    /** Additional reducer qualification used together with the sole physical SavedAttachmentSourceStore loader. */
    public void verifyAttachmentSource(ContinuityStorePort.Session borrowed, ContinuityState predecessor, WriterContracts.Request event) throws IOException {
        writer.requireSession(borrowed); Stage stage = required(StrictJson.text(event.detailsObject().get("evidence_id")));
        StrictJson.require(stage.attachment.request().identity().equals(event.identity())
                && ContinuityJson.same(predecessor.toJson(), stage.attachment.input().predecessor().toJson()), "restored full Driver belongs to another actual attachment");
        Materials replay = materials.replay(borrowed, stage.request, stage.nativeCandidate, stage.saved, stage.abandoned, stage.material);
        requireSameMaterials(stage.material, replay);
        var details = event.detailsObject(); var delta = details.get("driver_snapshot");
        StrictJson.require(delta != null && delta.equals(stage.attachment.request().detailsObject().get("driver_snapshot"))
                && stage.finalSeed.fullDriver().equals(ExactRef.fromJson(details.get("restored_full_driver")))
                && stage.material.provisional().fullDriver().equals(ExactRef.fromJson(details.get("restored_staged_driver")))
                && stage.material.completedRow().equals(ExactRef.fromJson(details.get("restored_completed_row"))), "exact staged/final Driver source or delta changed");
        for (ExactRef reference : java.util.List.of(stage.finalSeed.fullDriver(), stage.material.provisional().fullDriver(), stage.material.completedRow()))
            readOriginal(borrowed, reference, ARCHIVED_DRIVER_BYTES);
    }
    @Override public PublishedDriver publish(Request request, NativeCandidate actual, DriverStateSnapshot.Complete saved,
            WriterContracts.Prepared prepared, WriterContracts.Receipt committed,ReadWindow reads) throws IOException {
        Objects.requireNonNull(reads).requireOriginal(request);
        Stage stage = required(request.requestId()); synchronized (stage) {
            sameAttempt(stage, request, actual);stage.reads=reads;
            return writer.locked(borrowed -> {
                writer.requireSession(borrowed);
                StrictJson.require(stage.attachment.request().identity().equals(prepared.request().identity())
                        && committed.eventIdentity().equals(prepared.request().identity()), "publication lacks its original real prepared/committed attachment");
                if (stage.adopted == null) {
                    try { stage.adopted = DriverBootstrap.adoptRestored(stage.staged, stage.finalSeed, prepared, committed, borrowed,
                            (ref, maximum) -> RootOriginalArtifacts.read(writer, archive, borrowed, ref, maximum, actual.source().sourceRef()), stage.material.coverage(), reads.deadline()); }
                    catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IOException("actual committed restore adoption interrupted; no event replay", interrupted); }
                }
                if (stage.physical == null) {
                    if (stage.physicalEntered) throw new IOException("original physical restore construction failed; inspect retained outcome without rebuilding its owner");
                    stage.physicalEntered = true;
                    stage.physical = Objects.requireNonNull(publications.physical(borrowed, stage.adopted, stage.material.replacement(), request,reads));
                }
                stage.published = fresh(stage, borrowed,actual); return stage.published;
            });
        }
    }
    @Override public void requireCurrent(PublishedDriver published, NativeCandidate actual, WriterContracts.Receipt committed,ReadWindow reads) throws IOException {
        ContinuityStorePort.Session borrowed = writer.borrowedSession(); writer.requireSession(borrowed);
        Stage stage = stages.values().stream().filter(value -> value.published == published).findFirst().orElseThrow(() -> new IOException("publication is not from this actual restore adapter"));
        Objects.requireNonNull(reads).requireOriginal(stage.request);stage.reads=reads;
        sameAttempt(stage, stage.request, actual);
        StrictJson.require(committed.eventIdentity().equals(stage.attachment.request().identity()), "fresh publication crossed canonical restore commit");
        PublishedDriver current = fresh(stage, borrowed,actual);
        requireCurrentPublicationData(published,current,actual);
        StrictJson.require(Arrays.equals(archive.readArtifact(borrowed,current.semantic().originalNativePacket(),DriverJson.MAX_NATIVE_BYTES+4),
                actual.actual().originalPacket()),"current restored SEM does not retain this exact independent READ packet");
    }
    private PublishedDriver fresh(Stage stage, ContinuityStorePort.Session borrowed,NativeCandidate actual) throws IOException {
        stage.reads.requireOriginal(stage.request);
        SessionIdentity identity = new SessionIdentity(stage.adopted.session().machineId(), stage.adopted.session().game(), stage.adopted.session().sessionId());
        if (stage.physical == null) throw new IOException("the actual restore physical observation owner is unavailable");
        return stage.physical.withReceivedSnapshot(borrowed, stage.reads.deadline(), actual.actual(),lease -> {
            lease.assertCurrent(borrowed);
            var frame = lease.ordinary().orElseThrow(() -> new IOException("actual restored living Driver cannot be joined to its physical frame"));
            var semantic = frame.semantic();
            var proof = stage.physical.semantic(borrowed, identity, lease);
            boolean map = org.xar.ck3.control.planning.opportunity.OpportunityJson.bool(semantic.get("map_ready"), "map_ready");
            boolean paused = org.xar.ck3.control.planning.opportunity.OpportunityJson.bool(semantic.get("paused"), "paused");
            boolean eligible = map && paused && NativeReadinessCollector.checkpointEligibility(semantic)
                    == org.xar.ck3.control.application.session.SessionPorts.CheckpointEligibility.SAFE;
            CheckpointRequest.Readiness readiness = new CheckpointRequest.Readiness(frame.identity(), frame.source(), frame.sessionId(), stage.request.pair().lineageId(),
                    map, paused, eligible, "actual committed restored Driver and source-qualified raw physical SEM", proof.originalNativePacket(), frame.observedAt());
            requireRestoredPhysicalIdentity(stage.finalSeed,stage.adopted.session(),stage.material.replacement().nativeTransport().pipeName(),
                    lease.fullSnapshot(),lease.factsKnown(),frame);
            StrictJson.require(proof.frame().equals(frame.identity())&&frame.source().equals(stage.nativeCandidate.source()),
                    "actual restored semantic proof or source differs from its current physical frame");
            lease.assertCurrent(borrowed);
            stage.reads.requireOriginal(stage.request);
            return new PublishedDriver(lease.factsKnown().driver(), lease.factsKnown().stamp().episodeEpoch(), stage.finalSeed.originalHistoryBasis(), readiness, proof);
        });
    }
    /** Pure comparison of retained publication and the exact later READ; no source or restoration admission. */
    static void requireCurrentPublicationData(PublishedDriver published,PublishedDriver current,NativeCandidate actual) {
        Objects.requireNonNull(published);Objects.requireNonNull(current);Objects.requireNonNull(actual);
        var before=published.readiness();var after=current.readiness();var old=before.observed();var frame=after.observed();
        var raw=actual.actual();
        StrictJson.require(Arrays.equals(current.driver().encode(),published.driver().encode())
                &&current.episodeEpoch()==published.episodeEpoch()
                &&current.originalHistoryBasis().equals(published.originalHistoryBasis())
                &&old.machineId().equals(frame.machineId())&&old.game().equals(frame.game())
                &&old.observationVersion()==frame.observationVersion()
                &&before.sessionId().equals(after.sessionId())&&before.lineageId().equals(after.lineageId())
                &&before.source().equals(after.source())&&after.source().equals(actual.source())
                &&after.lineageId().equals(actual.lineageId())
                &&old.frame().episodeRunId().equals(frame.frame().episodeRunId())
                &&old.frame().identity().player().equals(frame.frame().identity().player())
                &&old.frame().identity().dateRaw().equals(frame.frame().identity().dateRaw())
                &&frame.frame().identity().nativeRevision().compareTo(old.frame().identity().nativeRevision())>0
                &&after.mapReady()&&after.paused()&&after.saveEligible(),"restored authority/state changed after actual publication");
        StrictJson.require(raw.session().machineId().equals(frame.machineId())&&raw.session().game().equals(frame.game())
                &&raw.session().sessionId().equals(after.sessionId())
                &&raw.snapshotId().equals(frame.frame().snapshotId())
                &&raw.nativeRevision().equals(frame.frame().identity().nativeRevision())
                &&raw.observedAt().equals(after.observedAt())&&raw.observedAt().equals(current.semantic().observedAt())
                &&current.semantic().frame().equals(frame)
                &&after.nativeEvidence().equals(current.semantic().originalNativePacket())
                &&current.semantic().originalNativePacket().bytes()==raw.originalPacket().length
                &&current.semantic().originalNativePacket().sha256().equals(DriverJson.sha256(raw.originalPacket())),
                "current restored publication differs from this exact independent READ");
    }
    /** DATA coherence only; the caller still owns the private live physical lease and source qualification. */
    static void requireRestoredPhysicalIdentity(DriverBootstrap.Seed expected,
            org.xar.ck3.control.application.action.NativeObservationPort.TransportSession adopted,String actualPipe,
            DriverObservationAssembler.FullSnapshot full,DriverSnapshotFacts.Known known,DriverObservationAssembler.Complete frame) {
        Objects.requireNonNull(expected);Objects.requireNonNull(adopted);Objects.requireNonNull(full);Objects.requireNonNull(known);Objects.requireNonNull(frame);
        StrictJson.text(actualPipe);var transport=expected.expectedSession();var driver=known.driver().session();var raw=full.actual();
        StrictJson.require(adopted.equals(transport)&&raw.session().equals(transport)&&full.facts().transport().equals(transport)
                &&frame.identity().machineId().equals(transport.machineId())&&frame.identity().game().equals(transport.game())
                &&frame.sessionId().equals(transport.sessionId())&&frame.connectionGeneration().equals(transport.connectionGeneration()),
                "restored current frame crossed its exact transport/full Game birth/session/connection");
        StrictJson.require(driver.bridgePid()==transport.game().pid()&&driver.pipeName().equals(actualPipe)
                &&driver.actorId().equals(frame.identity().frame().identity().player())
                &&driver.episodeRunId().equals(frame.identity().frame().episodeRunId())
                &&known.stamp().game().equals(transport.game())&&known.stamp().episodeEpoch()==expected.episodeEpoch()
                &&known.stamp().driverVersion()==expected.driverVersion()&&known.stamp().driverSha256().equals(expected.fullDriver().sha256())
                &&known.originalHistoryBasis().equals(expected.originalHistoryBasis()),
                "restored full Driver process/pipe/actor/episode/epoch/version/original history changed before publication");
        StrictJson.require(Arrays.equals(full.facts().driver().encode(),known.driver().encode())
                &&frame.identity().frame().snapshotId().equals(raw.snapshotId())
                &&frame.identity().frame().identity().nativeRevision().equals(raw.nativeRevision())
                &&frame.originalEvidence().equals(full.originalEvidence())&&frame.observedAt().equals(raw.observedAt())
                &&frame.fullBindingSha256().equals(full.fullBindingSha256())&&frame.semantic().equals(full.semantic()),
                "restored original raw/Driver/full semantic join differs from the current physical frame");
    }
    public DriverBootstrap.Adopted adopted(RestoreBinding actual) throws IOException {
        Stage stage = stages.values().stream().filter(value -> value.attachment.request().identity().equals(actual.attachment().eventIdentity()))
                .findFirst().orElseThrow(() -> new IOException("original private restore attachment not retained"));
        if (stage.adopted == null || !stage.adopted.session().game().equals(actual.session().game())) throw new IOException("actual restore adoption not retained"); return stage.adopted;
    }
    public RestoredRuntime runtime(ContinuityStorePort.Session borrowed, RestoreCheckpointService issuer, RestoreBinding actual) throws IOException {
        writer.requireSession(borrowed); Objects.requireNonNull(issuer).requireRetainedOriginal(borrowed, actual);
        DriverBootstrap.Adopted adopted = adopted(actual);
        Stage stage = stages.values().stream().filter(value -> value.adopted == adopted && value.published != null).findFirst()
                .orElseThrow(() -> new IOException("actual source-qualified restore runtime not retained"));
        synchronized (stage) {
            stage.reads=actual.readWindow();stage.reads.requireOriginal(stage.request);
            if (stage.runtime == null) {
                if (stage.runtimeEntered) throw new IOException("original admitted restore runtime construction failed; no second binding or replacement is authorized");
                stage.runtimeEntered = true;
                stage.runtime = Objects.requireNonNull(publications.create(borrowed, adopted, stage.material.replacement(), stage.request, issuer, actual, sources));
            }
            stage.runtime.capabilities().requireOwner(adopted.authority(), archive, stage.runtime.bindings());
            issuer.requireRetainedOriginal(borrowed, actual); return stage.runtime;
        }
    }
    private Stage required(String requestId) throws IOException {
        Stage stage = stages.get(requestId); if (stage == null) throw new IOException("original restore stage unavailable; native replacement must not be replayed"); return stage;
    }
    private byte[] readOriginal(ContinuityStorePort.Session borrowed, ExactRef reference, int maximum) throws IOException {
        int supported = Math.min(maximum, ImmutableArtifactStore.MAXIMUM_ARTIFACT_BYTES);
        if (reference.bytes() > supported) throw new IOException("actual restored Driver exceeds the immutable archive's qualified byte boundary");
        return archive.readArtifact(borrowed, reference, supported);
    }
    private static void sameAttempt(Stage stage, Request request, NativeCandidate actual) {
        StrictJson.require(stage.request.equals(request) && stage.nativeCandidate.actual().session().equals(actual.actual().session())
                && actual.actual().nativeRevision().compareTo(stage.nativeCandidate.actual().nativeRevision())>=0
                &&!actual.actual().observedAt().isBefore(stage.nativeCandidate.actual().observedAt())
                &&stage.nativeCandidate.source().equals(actual.source())&&stage.nativeCandidate.lineageId().equals(actual.lineageId())
                && RestoreCheckpointService.sameStableReadState(stage.nativeCandidate.actual(),actual.actual()), "same restore request changed actual original source");
    }
    private static void requireSameMaterials(Materials expected, Materials actual) {
        StrictJson.require(expected.provisional().equals(actual.provisional()) && expected.replacement() == actual.replacement()
                && expected.completedRow().equals(actual.completedRow()) && expected.abandonedSnapshot().equals(actual.abandonedSnapshot())
                && expected.coverage() == actual.coverage() && expected.retainedFrames() == actual.retainedFrames()
                && expected.producerSource().equals(actual.producerSource()) && expected.coldAdoption()==actual.coldAdoption(),
                "actual immutable cold/lifecycle material replay or private adoption issuer changed");
    }
}
