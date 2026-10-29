package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.io.IOException;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial;
import org.xar.ck3.control.application.checkpoint.SavedFirstCheckpointMaterialStore;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.planning.finance.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Core-lifetime actual original-proof producer; a physical Game is held only in its current scoped transition. */
public final class RootConstructionDomainOriginals implements ConstructionDomainLifecycle.OriginalBodyProducer {
    private static final String SCHEMA = "xar.java.construction-original-proof-input/v1";
    private static final int NEXT_DRIVER_LIMIT = Math.min(org.xar.ck3.control.application.checkpoint.DriverCheckpointStore.MAX_DRIVER_BYTES,
            ImmutableArtifactStore.MAXIMUM_ARTIFACT_BYTES);
    private final RootApplicationAssembly.Core core;
    private final ConstructionDomainLifecycle.Prepared domain;
    private final ExactRef source;
    private final ThreadLocal<Transition> active = new ThreadLocal<>();
    public RootConstructionDomainOriginals(RootApplicationAssembly.Core core, ConstructionDomainLifecycle.Prepared domain, ExactRef source) {
        this.core = Objects.requireNonNull(core); this.domain = Objects.requireNonNull(domain); this.source = Objects.requireNonNull(source);
        StrictJson.require(core.archive().writer() == core.writer() && source.bytes() > 0, "actual one Core writer/archive and original producer source required");
        domain.bindOriginals(source, this);
    }
    public void requireCore(RootApplicationAssembly.Core actual, ExactRef actualSource) {
        StrictJson.require(actual == core && source.equals(actualSource), "construction original-proof owner cannot be rebound to another Core or source");
    }
    public Optional<ConstructionDomainLifecycle.Publication> initializeFresh(RootRuntimeContext context, Session same, RootInitialEpisodeProof actual) throws IOException {
        requireContext(context, same); Objects.requireNonNull(actual).requireCurrent(same);
        StrictJson.require(actual.adopted() == context.adopted() && actual.source().equals(context.source())
                && actual.sessionId().equals(context.game().sessionId()), "construction fresh proof belongs to another installed physical Game");
        ExactRef basis = actual.preserveOriginal(same);
        RootInitialEpisodeProof.replayOriginal(context, same, basis).requireInitializationPredecessor(same, same.head());
        if (consumed(same, "java_fresh_initialization_v2", "original_basis", basis)) return Optional.empty();
        return Optional.of(publish(same, new Fresh(context, actual, basis)));
    }
    public Optional<ConstructionDomainLifecycle.Publication> initializeFresh(RootRuntimeContext context, Session same, FreshCampaignContext actual) throws IOException {
        requireContext(context,same);actual.requireCurrent(same);
        ExactRef basis=actual.preserveOriginal(same);
        FreshCampaignContext.replayOriginal(context,same,basis).requireInitializationPredecessor(same,same.head());
        if(consumed(same,"java_fresh_initialization_v2","original_basis",basis))return Optional.empty();
        return Optional.of(publish(same,new CampaignFresh(context,actual,basis)));
    }
    public Optional<ConstructionDomainLifecycle.Publication> restore(RootRuntimeContext context, Session same, RootRestorationOriginalProof actual) throws IOException {
        requireContext(context, same); Objects.requireNonNull(actual);
        ExactRef basis = actual.preserveOriginal(same);
        var original = RootRestorationOriginalProof.replayOriginal(context, same, basis);
        requireRestoredGame(context, original);
        original.requireImportPredecessor(same, same.head());
        if (consumed(same, "java_restored_construction_originals_v1", "restore_basis", basis)) return Optional.empty();
        return Optional.of(publish(same, new Restore(context, basis)));
    }
    public ConstructionNextEpisodeReducer.Initialization initializeNext(RootRuntimeContext context, Session same,
            RootApplicationAssembly.EpisodeDomainInitializationProof proof) throws IOException {
        requireContext(context, same); Objects.requireNonNull(proof).requireCurrent(same, context);
        var current = same.readDomain(DomainBodies.Slot.CONSTRUCTION);
        if (current instanceof DomainBodies.Available known) {
            Obj old = ConstructionLedgerCodec.decodeLedger(known.canonicalBody()).original();
            if (old.get(ConstructionNextEpisodeReducer.FIELD) instanceof Obj audit
                    && new Text(proof.kind().name()).equals(audit.get("origin"))
                    && json(org.xar.ck3.control.application.checkpoint.CheckpointPairCodec.fileWitnessToJson(proof.baselineMaterial().witness())).equals(audit.get("baseline_material_witness"))
                    && new Text(proof.baselineMaterial().originalHeadDigest()).equals(audit.get("baseline_sha256"))
                    && new IntegerValue(java.math.BigInteger.valueOf(proof.initializationHeadSequence())).equals(audit.get("initialization_sequence"))
                    && new Text(proof.initializationHeadDigest()).equals(audit.get("initialization_sha256"))
                    && json(org.xar.ck3.control.application.session.OrdinaryCycleTransitions.sessionToJson(proof.afterSession())).equals(audit.get("after_owner"))) {
                proof.requireCurrent(same, context);
                verifyNextProjectAudit(context, same, proof, audit);
                proof.requireCurrent(same, context);
                return new ConstructionNextEpisodeReducer.Initialization(Optional.empty(), known.reference(),
                        qualification(audit));
            }
        }
        var projectCapture = captureNextProjects(context, same, proof);
        var projects = projectCapture.projects();
        Next next = new Next(context, proof, nextBasis(context, same, proof), projectCapture);
        proof.requireCurrent(same, context);
        var publication = publish(same, next);
        proof.requireCurrent(same, context);
        var published = same.readDomain(DomainBodies.Slot.CONSTRUCTION);
        StrictJson.require(published instanceof DomainBodies.Available, "episode construction actual BodyRef was not committed");
        return new ConstructionNextEpisodeReducer.Initialization(Optional.of(publication), ((DomainBodies.Available) published).reference(),
                projects instanceof ConstructionNextEpisodeReducer.ObservedProjects
                        ? ConstructionNextEpisodeReducer.Qualification.CURRENT_PROJECTS_OBSERVED : ConstructionNextEpisodeReducer.Qualification.CURRENT_PROJECTS_UNAVAILABLE);
    }
    private static ConstructionNextEpisodeReducer.Qualification qualification(Obj audit) {
        Obj projects = object(audit.get("current_projects"), "actual current project qualification");
        if (new Text("observed").equals(projects.get("status"))) return ConstructionNextEpisodeReducer.Qualification.CURRENT_PROJECTS_OBSERVED;
        StrictJson.require(new Text("unavailable").equals(projects.get("status")), "unknown construction NEXT qualification");
        return ConstructionNextEpisodeReducer.Qualification.CURRENT_PROJECTS_UNAVAILABLE;
    }
    private void verifyNextProjectAudit(RootRuntimeContext context, Session same, RootApplicationAssembly.EpisodeDomainInitializationProof proof,
            Obj audit) throws IOException {
        Obj projects = object(audit.get("current_projects"), "actual current project qualification");
        Value reference = projects.get("original_read_receipt");
        if (reference != Nil.INSTANCE) {
            ExactRef original = ExactRef.fromJson(StrictJson.parse(encode(object(reference, "actual original NEXT project receipt"))));
            StrictJson.require(replayNextProjects(context, same, proof, original).toJson().equals(projects),
                    "already imported NEXT project observation differs from its surviving actual original");
        } else StrictJson.require(new Text("unavailable").equals(projects.get("status")), "an observed NEXT project requires its original read receipt");
    }
    private record NextProjectCapture(ConstructionNextEpisodeReducer.CurrentProjects projects,
            Optional<RootNextEpisodeDomainReads.Captured<FinanceReadContracts.Packet>> originals) {
        private NextProjectCapture { Objects.requireNonNull(projects); Objects.requireNonNull(originals); }
    }
    private NextProjectCapture captureNextProjects(RootRuntimeContext context, Session same,
            RootApplicationAssembly.EpisodeDomainInitializationProof proof) throws IOException {
        var captured = proof.read(same, context, context.finance().definitions().contract(FinanceReadContracts.Query.CONSTRUCTION), obj(),
                proof.deadline());
        var actual = captured.result();
        proof.requireCurrent(same, context);
        if (actual instanceof PlanningReadResult.Unavailable<FinanceReadContracts.Packet> missing)
            return new NextProjectCapture(new ConstructionNextEpisodeReducer.ProjectsUnavailable(missing.reason(), Optional.empty()), Optional.empty());
        captured.requireOriginals(same, context, proof);
        var known = (PlanningReadResult.Known<FinanceReadContracts.Packet>) actual;
        StrictJson.require(known.value().receipt().equals(known.receipt()), "actual episode construction packet changed its original receipt");
        return new NextProjectCapture(replayNextProjects(context, same, proof, known.originalReceipt()), Optional.of(captured));
    }
    private ConstructionNextEpisodeReducer.CurrentProjects replayNextProjects(RootRuntimeContext context, Session same,
            RootApplicationAssembly.EpisodeDomainInitializationProof proof, ExactRef original) throws IOException {
        var archive = core.archive().withSession(same); var receipt = archive.loadRead(original);
        NativeRecordedEvidenceVerifier.requireRead(receipt, archive);
        StrictJson.require(archive.readReferenceOf(receipt).equals(original)
                && receipt.contractId().equals(context.finance().definitions().contract(FinanceReadContracts.Query.CONSTRUCTION).contractId())
                && receipt.request().operation().equals(FinanceReadContracts.Query.CONSTRUCTION.operation())
                && receipt.request().source().equals(proof.source()) && receipt.request().sessionId().equals(proof.afterSession().sessionId())
                && receipt.request().before().game().equals(proof.afterSession().game()), "episode construction original read crossed the actual private contract/Game/session");
        for (PlanningReadGuard guard : List.of(receipt.before(), receipt.after())) {
            RootGuardEvidence.requireHistory(guard.binding(), archive, same);
            var point = RootGuardEvidence.writerPoint(guard.binding(), archive);
            StrictJson.require(point.sequence() >= proof.initializationHeadSequence(),
                    "construction current project query predates its actual BASELINE/RESTORED initialization anchor");
            same.requireHistoricalState(proof.initializationHeadSequence(), proof.initializationHeadDigest());
        }
        var before = RootGuardEvidence.loadFrame(receipt.before().binding(), archive, core.frameLoader());
        var after = RootGuardEvidence.loadFrame(receipt.after().binding(), archive, core.frameLoader());
        var currentFrame = proof.currentSemantic().frame().frame();
        for (var observed : List.of(before.semantic(), after.semantic())) StrictJson.require(
                text(observed.get("episode_run_id"), "current project episode").equals(currentFrame.episodeRunId())
                && integer(object(observed.get("played_character"), "current project player").get("character_id"), "current project actor").equals(currentFrame.identity().player())
                && integer(observed.get("date_raw"), "current project date").equals(currentFrame.identity().dateRaw()),
                "construction project read crossed the current physical initialization semantics");
        var packet = context.finance().definitions().decodeOriginal(FinanceReadContracts.Query.CONSTRUCTION, receipt, before.semantic());
        Obj input = obj("schema", new Text(org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryCodec.SCHEMA),
                "starting_snapshot", before.semantic(), "ending_snapshot", after.semantic(),
                "native_envelope", org.xar.ck3.control.application.driver.DriverJson.object(packet.originalFrame(),
                        org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryCodec.MAX_BYTES),
                "expected_revision", new IntegerValue(receipt.request().before().frame().revision()), "native_query_request_id", new Text(receipt.requestId()),
                "material_receipt", new Bool(true), "wartime_observation", new Bool(false));
        try {
            Obj finalized = org.xar.ck3.control.application.driver.DriverJson.object(
                    org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryCodec.finalizeObservation(encode(input)),
                    org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryCodec.MAX_BYTES);
            if (!new Text("material_source").equals(finalized.get("status")))
                return new ConstructionNextEpisodeReducer.ProjectsUnavailable("actual native material finalizer: " + finalized.get("status"), Optional.of(original));
            return new ConstructionNextEpisodeReducer.ObservedProjects(original, finalized);
        } catch (IllegalArgumentException invalidMaterial) {
            return new ConstructionNextEpisodeReducer.ProjectsUnavailable("actual native material fields rejected: " + invalidMaterial.getMessage(), Optional.of(original));
        }
    }
    private ConstructionNextEpisodeReducer.Basis nextBasis(RootRuntimeContext context, Session same,
            RootApplicationAssembly.EpisodeDomainInitializationProof proof) throws IOException {
        proof.requireCurrent(same, context);
        var material = proof.baselineMaterial();
        var head = same.requireHistoricalState(material.originalHeadSequence(), material.originalHeadDigest());
        var oldDomain = proof.oldDomain(DomainBodies.Slot.CONSTRUCTION);
        var original = ConstructionSavedBody.read(same, head, oldDomain.producerSources());
        StrictJson.require(original.reference().equals(oldDomain), "construction original BodyRef/FileID differs from private baseline custody");
        var before = proof.predecessorDriver(); var first = proof.firstSavedDriver(); var current = proof.currentDriver();
        ExactRef beforeRef = core.archive().preserveArtifact(same, before.encode(), NEXT_DRIVER_LIMIT);
        ExactRef firstRef = core.archive().preserveArtifact(same, first.encode(), NEXT_DRIVER_LIMIT);
        ExactRef currentRef = core.archive().preserveArtifact(same, current.encode(), NEXT_DRIVER_LIMIT);
        var result = new ConstructionNextEpisodeReducer.Basis(ConstructionNextEpisodeReducer.Origin.valueOf(proof.kind().name()),
                proof.beforeSession(), material.session(), proof.afterSession(), proof.source(), material.witness(),
                material.baseline().eventRef(), material.originalHeadSequence(), material.originalHeadDigest(),
                proof.initializationHeadSequence(), proof.initializationHeadDigest(), original.reference(), beforeRef, firstRef, proof.savedSemantic(), currentRef, proof.currentSemantic());
        original.requireUnchanged(same); proof.requireCurrent(same, context); return result;
    }
    private boolean consumed(Session same, String field, String key, ExactRef basis) throws IOException {
        var actual = same.readDomain(DomainBodies.Slot.CONSTRUCTION);
        if (actual instanceof DomainBodies.Available known) {
            Obj body = ConstructionLedgerCodec.decodeLedger(known.canonicalBody()).original();
            return body.get(field) instanceof Obj row && ref(basis).equals(row.get(key));
        }
        StrictJson.require(actual instanceof DomainBodies.Unavailable missing && missing.reason() == DomainBodies.Reason.UNIMPORTED,
                "construction original body is unavailable; missing/corrupt identity cannot become an empty initialization");
        return false;
    }
    private ConstructionDomainLifecycle.Publication publish(Session same, Transition actual) throws IOException {
        core.writer().requireSession(same);
        StrictJson.require(active.get() == null, "actual construction original-proof publication cannot nest");
        active.set(actual);
        try {
            Optional<ConstructionLedgerCodec.Ledger> previous = current(same);
            var original = actual.replay(same, same.head(), previous);
            return domain.publishOriginal(same, actual.kind(), actual.input(), original.evidence());
        } finally { active.remove(); }
    }
    @Override public ConstructionDomainLifecycle.OriginalBody replay(Session same, WriterContracts.Head head, ConstructionDomainLifecycle.Kind kind,
            Obj input, Optional<ConstructionLedgerCodec.Ledger> previous) throws IOException {
        core.writer().requireSession(same); Transition actual = active.get();
        if (actual == null) throw new IOException("only the actual scoped Root fresh/restore producer may import construction originals");
        StrictJson.require(head.digest().equals(same.head().digest()) && actual.kind() == kind && actual.input().equals(input),
                "construction original-proof kind/input/head differs from the actual producer");
        return actual.replay(same, head, previous);
    }
    private sealed interface Transition permits Fresh, CampaignFresh, Restore, Next {
        ConstructionDomainLifecycle.Kind kind();
        Obj input();
        ConstructionDomainLifecycle.OriginalBody replay(Session same, WriterContracts.Head actual, Optional<ConstructionLedgerCodec.Ledger> previous) throws IOException;
    }
    private final class Next implements Transition {
        private final RootRuntimeContext context;
        private final RootApplicationAssembly.EpisodeDomainInitializationProof proof;
        private final ConstructionNextEpisodeReducer.Basis basis;
        private final NextProjectCapture projectCapture;
        private Next(RootRuntimeContext context, RootApplicationAssembly.EpisodeDomainInitializationProof proof, ConstructionNextEpisodeReducer.Basis basis,
                NextProjectCapture projectCapture) {
            this.context = context; this.proof = proof; this.basis = basis; this.projectCapture = projectCapture;
        }
        @Override public ConstructionDomainLifecycle.Kind kind() { return ConstructionDomainLifecycle.Kind.NEXT_EPISODE; }
        @Override public Obj input() { return obj("schema", new Text(SCHEMA), "origin", new Text("actual_first_material_initialization"),
                "basis", basis.toJson(), "current_projects", projectCapture.projects().toJson(),
                "project_source_proof", projectCapture.originals().flatMap(value -> value.sourceProof()).<Value>map(value->ref(value)).orElse(Nil.INSTANCE),
                "project_read_semantic", projectCapture.originals().<Value>map(value -> json(
                        org.xar.ck3.control.application.session.OrdinaryCycleTransitions.semanticToJson(value.semantic()))).orElse(Nil.INSTANCE)); }
        @Override public ConstructionDomainLifecycle.OriginalBody replay(Session same, WriterContracts.Head actual,
                Optional<ConstructionLedgerCodec.Ledger> previous) throws IOException {
            requireContext(context, same); proof.requireCurrent(same, context);
            if (projectCapture.originals().isPresent()) projectCapture.originals().orElseThrow().requireOriginals(same, context, proof);
            var rereadBasis = nextBasis(context, same, proof);
            StrictJson.require(rereadBasis.equals(basis), "episode construction original BodyRef, material witness or source changed");
            var savedHead = same.requireHistoricalState(basis.baselineSequence(), basis.baselineDigest());
            var saved = ConstructionSavedBody.read(same, savedHead, basis.originalBody().producerSources());
            StrictJson.require(saved.reference().equals(basis.originalBody()) && saved.reference().equals(proof.oldDomain(DomainBodies.Slot.CONSTRUCTION)),
                    "construction initialization replay changed the original BodyRef/native FileID");
            if (previous.isPresent()) StrictJson.require(previous.orElseThrow().original().equals(saved.ledger().original()),
                    "episode construction cannot replace another current full body or discard a newer pending original");
            context.semanticVerifier().verify(same, basis.savedOwner(), basis.savedSemantic());
            context.semanticVerifier().verify(same, basis.afterOwner(), basis.currentSemantic());
            Obj savedSnapshot = org.xar.ck3.control.application.driver.DriverJson.object(core.archive().readArtifact(same,
                    basis.savedSemantic().semantic(), org.xar.ck3.control.application.readiness.ReadinessArchive.Role.SEMANTIC.maximumBytes()),
                    org.xar.ck3.control.application.readiness.ReadinessArchive.Role.SEMANTIC.maximumBytes());
            Obj currentSnapshot = org.xar.ck3.control.application.driver.DriverJson.object(core.archive().readArtifact(same,
                    basis.currentSemantic().semantic(), org.xar.ck3.control.application.readiness.ReadinessArchive.Role.SEMANTIC.maximumBytes()),
                    org.xar.ck3.control.application.readiness.ReadinessArchive.Role.SEMANTIC.maximumBytes());
            var before = org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.decodeComplete(core.archive().readArtifact(same, basis.predecessorDriver(), NEXT_DRIVER_LIMIT));
            var first = org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.decodeComplete(core.archive().readArtifact(same, basis.firstSavedDriver(), NEXT_DRIVER_LIMIT));
            var currentDriver = org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.decodeComplete(core.archive().readArtifact(same, basis.currentDriver(), NEXT_DRIVER_LIMIT));
            var projects = projectCapture.projects();
            Optional<ExactRef> projectReceipt = projects instanceof ConstructionNextEpisodeReducer.ObservedProjects observed
                    ? Optional.of(observed.originalReceipt()) : ((ConstructionNextEpisodeReducer.ProjectsUnavailable) projects).originalReceipt();
            var currentProjects = projectReceipt.isPresent() ? replayNextProjects(context, same, proof, projectReceipt.orElseThrow()) : projects;
            StrictJson.require(currentProjects.equals(projects), "actual episode construction material query replay changed");
            var reduced = ConstructionNextEpisodeReducer.reduce(new ConstructionNextEpisodeReducer.Input(saved.ledger(), before, first, savedSnapshot,
                    currentDriver, currentSnapshot, basis, currentProjects));
            var evidence = new LinkedHashSet<ExactRef>(basis.evidence()); evidence.addAll(saved.evidence());
            if (projectCapture.originals().isPresent()) {
                var captured = projectCapture.originals().orElseThrow();
                captured.sourceProof().ifPresent(evidence::add);
                evidence.addAll(captured.semantic().references());
            }
            projectReceipt.ifPresent(evidence::add);
            saved.requireUnchanged(same);
            if (projectCapture.originals().isPresent()) projectCapture.originals().orElseThrow().requireOriginals(same, context, proof);
            proof.requireCurrent(same, context);
            return new ConstructionDomainLifecycle.OriginalBody(reduced.body(), List.copyOf(evidence));
        }
    }
    private final class Fresh implements Transition {
        private final RootRuntimeContext context;
        private final RootInitialEpisodeProof live;
        private final ExactRef basis;
        private Fresh(RootRuntimeContext context, RootInitialEpisodeProof live, ExactRef basis) { this.context = context; this.live = live; this.basis = basis; }
        @Override public ConstructionDomainLifecycle.Kind kind() { return ConstructionDomainLifecycle.Kind.FRESH; }
        @Override public Obj input() { return obj("schema", new Text(SCHEMA), "origin", new Text("actual_initial_entry"), "basis", ref(basis)); }
        @Override public ConstructionDomainLifecycle.OriginalBody replay(Session same, WriterContracts.Head actual, Optional<ConstructionLedgerCodec.Ledger> previous) throws IOException {
            requireContext(context, same); live.requireCurrent(same);
            var original = RootInitialEpisodeProof.replayOriginal(context, same, basis);
            original.requireInitializationPredecessor(same, actual);
            StrictJson.require(previous.isEmpty() && original.source().equals(context.source())
                    && original.sessionId().equals(context.game().sessionId())
                    && original.actualStart().command().origin().game().equals(context.game().generation()),
                    "fresh construction cannot replace a body or borrow an old physical Game initializer");
            return freshBody(basis,original.episodeId(),original.observation().frame().identity().player(),original.evidence());
        }
    }
    private final class CampaignFresh implements Transition {
        private final RootRuntimeContext context;
        private final FreshCampaignContext live;
        private final ExactRef basis;
        private CampaignFresh(RootRuntimeContext context,FreshCampaignContext live,ExactRef basis) {
            this.context=context;this.live=live;this.basis=basis;
        }
        @Override public ConstructionDomainLifecycle.Kind kind(){return ConstructionDomainLifecycle.Kind.FRESH;}
        @Override public Obj input(){return obj("schema",new Text(SCHEMA),"origin",new Text("actual_fresh_campaign"),"basis",ref(basis));}
        @Override public ConstructionDomainLifecycle.OriginalBody replay(Session same,WriterContracts.Head actual,
                Optional<ConstructionLedgerCodec.Ledger> previous)throws IOException {
            requireContext(context,same);live.requireCurrent(same);
            var original=FreshCampaignContext.replayOriginal(context,same,basis);
            original.requireInitializationPredecessor(same,actual);
            StrictJson.require(previous.isEmpty()&&original.source().equals(context.source())
                    &&original.sessionId().equals(context.game().sessionId())
                    &&original.observation().game().equals(context.game().generation()),
                    "fresh construction cannot replace pending history or cross its real Game");
            return freshBody(basis,original.episodeId(),original.observation().frame().identity().player(),original.evidence());
        }
    }
    private static ConstructionDomainLifecycle.OriginalBody freshBody(ExactRef basis,String episode,
            java.math.BigInteger actor,List<ExactRef> evidence) {
        var audit=obj("original_basis",ref(basis),"episode_run_id",new Text(episode),"actor_character_id",new IntegerValue(actor));
        Obj body=obj("schema",new Text(ConstructionLedgerCodec.SCHEMA),"pending",Nil.INSTANCE,
                "applied",Nil.INSTANCE,"applied_prior",new Arr(List.of()),"java_fresh_initialization_v2",audit);
        ConstructionLedgerCodec.decodeLedger(encode(body));
        return new ConstructionDomainLifecycle.OriginalBody(body,evidence);
    }
    private final class Restore implements Transition {
        private final RootRuntimeContext context;
        private final ExactRef basis;
        private Restore(RootRuntimeContext context, ExactRef basis) { this.context = context; this.basis = basis; }
        @Override public ConstructionDomainLifecycle.Kind kind() { return ConstructionDomainLifecycle.Kind.RESTORE; }
        @Override public Obj input() { return obj("schema", new Text(SCHEMA), "origin", new Text("actual_qualified_saved_restore"), "basis", ref(basis)); }
        @Override public ConstructionDomainLifecycle.OriginalBody replay(Session same, WriterContracts.Head actual, Optional<ConstructionLedgerCodec.Ledger> previous) throws IOException {
            requireContext(context, same);
            var original = RootRestorationOriginalProof.replayOriginal(context, same, basis);
            requireRestoredGame(context, original);
            original.requireImportPredecessor(same, actual);
            SavedCheckpointMaterial savedMaterial = original.material();
            savedMaterial.requireRetained(same);
            switch (savedMaterial.kind()) {
                case ORDINARY -> StrictJson.require(savedMaterial instanceof SavedAttachmentSourceStore.SavedMaterial,
                        "ordinary construction restoration requires the actual private completed-cycle material");
                case FIRST_BASELINE -> StrictJson.require(savedMaterial instanceof SavedFirstCheckpointMaterialStore.BaselinedMaterial,
                        "FIRST construction restoration requires the actual private BASELINE material, never first DATA or a zero-cycle proof");
            }
            var savedHead = same.requireHistoricalState(savedMaterial.originalHeadSequence(), savedMaterial.originalHeadDigest());
            StrictJson.require(ContinuityJson.same(savedHead.toJson(), savedMaterial.originalHead().toJson()),
                    "construction restoration material differs from its complete original canonical head");
            var saved = ConstructionSavedBody.read(same, savedHead, domain.registration().producerSources());
            var pair = savedMaterial.pair(); var frame = pair.frame().frame().identity();
            var restoredFrame = original.semantic().frame().frame();
            StrictJson.require(pair.frame().machineId().equals(context.game().machineId())
                    && pair.frame().frame().episodeRunId().equals(restoredFrame.episodeRunId())
                    && frame.player().equals(restoredFrame.identity().player()), "saved construction crossed the actual restored player/episode");
            var archive = core.archive().withSession(same);
            List<ConstructionRestoreReducer.Canonical> guards = core.actions().withFrozen(same, lease -> {
                var rows = lease.snapshot().actions().stream().filter(receipt -> !receipt.settled()
                        && receipt.command().operation().equals(OrdinaryConstructionPolicy.OPERATION))
                        .map(receipt -> new ConstructionRestoreReducer.Canonical(receipt, archive.receiptReferenceOf(receipt))).toList();
                lease.assertCurrent(); return rows;
            });
            var audit = new ConstructionRestoreProvenance(basis, savedMaterial.reference(), saved.reference().payload(),
                    savedHead.sequence(), ContinuityJson.digest(savedHead.toJson()), pair.frame().frame().episodeRunId(), frame.player(),
                    context.game().generation(), context.game().sessionId());
            Obj body = ConstructionRestoreReducer.reduce(saved.ledger(), previous, guards, audit);
            var evidence = new LinkedHashSet<ExactRef>(original.evidence());
            evidence.addAll(saved.evidence()); guards.forEach(row -> evidence.add(row.originalReceipt()));
            DomainBodies.reference(actual.state(), DomainBodies.Slot.CONSTRUCTION).ifPresent(row -> evidence.add(row.payload()));
            saved.requireUnchanged(same);
            savedMaterial.requireRetained(same);
            return new ConstructionDomainLifecycle.OriginalBody(body, List.copyOf(evidence));
        }
    }
    private Optional<ConstructionLedgerCodec.Ledger> current(Session same) throws IOException {
        var actual = same.readDomain(DomainBodies.Slot.CONSTRUCTION);
        if (actual instanceof DomainBodies.Available known) return Optional.of(ConstructionLedgerCodec.decodeLedger(known.canonicalBody()));
        StrictJson.require(actual instanceof DomainBodies.Unavailable missing && missing.reason() == DomainBodies.Reason.UNIMPORTED,
                "construction current body is not an authentic imported body or true UNIMPORTED state");
        return Optional.empty();
    }
    private void requireContext(RootRuntimeContext context, Session same) throws IOException {
        StrictJson.require(context.core() == core && context.writer() == core.writer() && context.archive() == core.archive(),
                "construction original producer crossed the actual Core/writer/archive");
        core.writer().requireSession(same); context.game().verify();
        context.game().launchPlan().sources().requireLoadedClass(RootConstructionDomainOriginals.class);
        context.game().launchPlan().sources().requireLoadedClass(ConstructionSavedBody.class);
        context.game().launchPlan().sources().requireLoadedClass(ConstructionRestoreReducer.class);
        context.game().launchPlan().sources().requireLoadedClass(ConstructionRestoreProvenance.class);
        context.game().launchPlan().sources().requireLoadedClass(ConstructionNextEpisodeReducer.class);
    }
    private static void requireRestoredGame(RootRuntimeContext context, RootRestorationOriginalProof.Original original) {
        StrictJson.require(original.game().equals(context.game().generation())
                && original.sessionId().equals(context.game().sessionId()) && original.source().equals(context.source()),
                "construction restore proof belongs to another installed replacement Game/session/source");
    }
    private static Obj ref(ExactRef value) { return object(parse(StrictJson.canonical(value.toJson())), "actual original proof reference"); }
    private static Obj json(com.fasterxml.jackson.databind.JsonNode value) { return object(parse(StrictJson.canonical(value)), "actual original typed metadata"); }
}
