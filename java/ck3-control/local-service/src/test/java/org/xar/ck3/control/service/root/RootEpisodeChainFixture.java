package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.io.IOException;
import java.time.Instant;
import java.util.EnumSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.checkpoint.FirstCheckpointVerifier;
import org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs;
import org.xar.ck3.control.application.session.ContinuityBatchJournal;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;

/**
 * Test-only choreography of the actual retained Core producers. This class cannot create a ManagedGameSession,
 * lifecycle parent, proof, checkpoint verifier, coordinator, Controller, writer or Host. Its initial inputs must
 * already come from the real startup and canonical lifecycle path. A software pipe peer alone is insufficient.
 */
public final class RootEpisodeChainFixture {
    /** Assertions return no admission decision. Each callback must leave the actual canonical Head unchanged. */
    public interface Assertions {
        void beforeDomainImports(BeforeImports actual) throws IOException;
        void afterDomainImports(Imported actual) throws IOException;
        void afterPublication(Published actual) throws IOException;
    }

    private final RootApplicationAssembly.Core core;
    private final RootStartupNextResources.Prepared resourceProducer;
    private RootApplicationSession current;
    private boolean entered;
    private boolean failed;

    private RootEpisodeChainFixture(RootApplicationAssembly.Core actualCore, RootApplicationSession original,
            RootStartupNextResources.Prepared actualProducer) throws IOException {
        core = Objects.requireNonNull(actualCore); current = Objects.requireNonNull(original);
        resourceProducer = Objects.requireNonNull(actualProducer); resourceProducer.requireCore(core);
        require(current.ownedBy(core) && current.writer() == core.writer() && current.archive() == core.archive(),
                "Root chain fixture requires the real original Core/session/writer/archive");
    }

    /** Retains actual producer objects. This factory grants no launch, source or lifecycle qualification. */
    public static RootEpisodeChainFixture attach(RootApplicationAssembly.Core actualCore,
            RootApplicationSession original, RootStartupNextResources.Prepared actualProducer) throws IOException {
        return new RootEpisodeChainFixture(actualCore, original, actualProducer);
    }

    public RootApplicationAssembly.Core core() { return core; }
    public synchronized RootApplicationSession current() { return current; }

    /**
     * The canonical NEXT must already have retired the real predecessor and created its actual replacement.
     * Repeat only with the next genuinely produced parent after that new current session has itself retired.
     * A failure is retained for diagnosis; this test helper never retries a partially entered production chain.
     */
    public synchronized Published advance(ActionReceipt canonicalNextParent, Instant deadline, Assertions assertions)
            throws IOException, InterruptedException {
        Objects.requireNonNull(canonicalNextParent); Objects.requireNonNull(deadline); Objects.requireNonNull(assertions);
        require(!entered && !failed, "a running or failed actual Root fixture chain cannot be replayed");
        RootApplicationSession previous = current;
        require(previous.isRetired(), "actual canonical lifecycle NEXT must retire the predecessor before fixture staging");
        resourceProducer.requireCore(core); entered = true;
        try {
            var resources = resourceProducer.prepare(previous, canonicalNextParent, deadline);
            require(resources.core() == core, "actual resource producer changed the original Core");
            var catalog = resources.catalog();
            var stage = core.nextEpisodeStage(previous, canonicalNextParent, catalog.context().game(),
                    catalog.context().source(), catalog, resources.retainedFrames(), deadline);
            Published result = previous.withRetiredRootStage(core, () -> core.withBorrowed(() -> {
                var same = core.writer().borrowedSession();
                var inputs = RootNextEpisodeAssemblyInputs.create(same, stage, resources);
                var paths = inputs.checkpoints(); inputs.prepareDirectories(same);
                var checkpointStage = core.nextCheckpointStage(stage, inputs.policy(same), paths.freshness(),
                        paths.files(), paths.driverCheckpointPath(), paths.checkpointEvidence(), paths.attachmentEvidence(),
                        paths.seeds(), paths.lineageId(), paths.savePath());
                var dispatchInputs = inputs.dispatcher(same, checkpointStage);
                var dispatcher = checkpointStage.prepareDispatcher(dispatchInputs.authorityId(), dispatchInputs.bindings(),
                        dispatchInputs.frontend(), dispatchInputs.lifecycle(), dispatchInputs.reconciliation(),
                        dispatchInputs.closeAdmission(), dispatchInputs.derivedChildren(), dispatchInputs.derivedReplay(),
                        dispatchInputs.capabilities(), dispatchInputs.readHistory(), dispatchInputs.pending(),
                        dispatchInputs.requiredPending(), dispatchInputs.actualLifeFrames());

                // These calls mint the private tokens through the production reducers and original physical SAVE.
                var begun = core.beginNextEpisode(same, stage, deadline);
                var first = core.firstNextCheckpoint(same, begun, checkpointStage, deadline);
                var baseline = core.baselineNextEpisode(same, stage);
                var binding = core.captureNextBaseline(same, stage, deadline);
                var proof = core.nextEpisodeDomainProof(same, stage);
                require(first == baseline.firstCheckpoint() && first == binding.firstCheckpoint(),
                        "actual BASELINE and saved binding must retain the identical verified first SAVE");
                proof.requireCurrent(same, catalog.context()); binding.requireCurrent(same);
                var before = new BeforeImports(same, core, resources, stage, checkpointStage, dispatcher,
                        begun, first, baseline, binding, proof, same.head());
                assertUnchanged(same, () -> assertions.beforeDomainImports(before));
                proof.requireCurrent(same, catalog.context());

                // Exactly one production initializer owns each domain import; callbacks never rerun it.
                var importedBodies = core.initializeNextDomains(same, stage);
                requireImported(same, before, importedBodies); proof.requireCurrent(same, catalog.context());
                var imported = new Imported(before, importedBodies, same.head());
                assertUnchanged(same, () -> assertions.afterDomainImports(imported));
                proof.requireCurrent(same, catalog.context());
                var rebound = core.rebindNextBaseline(same, stage);
                var finish = inputs.finish(same, checkpointStage, baseline);
                var successor = checkpointStage.finish(finish.authorityId(), finish.bindings(), finish.frontend(),
                        finish.lifecycle(), finish.reconciliation(), finish.closeAdmission(), finish.terminalDecisions(),
                        finish.actualLifecycleRuntime(), finish.derivedChildren(), finish.derivedReplay(), finish.capabilities(),
                        finish.readHistory(), finish.actualLifeFrames(), finish.planningInputs(), finish.pipeline(), finish.pending(),
                        finish.requiredPending(), finish.cyclePolicy(), finish.offline(), finish.sessionClock(), finish.baseline(),
                        finish.admittedSavedDays(), finish.completion(), finish.episodes(), finish.savedCaptureFactory(),
                        finish.restoreMaterials(), finish.restorePublication());

                // The actual production publisher performs readiness, source rechecks and the original Host CAS.
                core.publishNextSession(same, stage, successor, deadline);
                require(successor.hasInstalledHost() && core.sessionAccess().current() == successor
                        && successor.ownedBy(core) && successor.writer() == core.writer() && successor.archive() == core.archive()
                        && !successor.identity().equals(previous.identity()),
                        "actual Controller/View/Host publication did not install the distinct same-Core successor");
                current = successor;
                var published = new Published(imported, rebound, successor, same.head());
                assertUnchanged(same, () -> assertions.afterPublication(published));
                return published;
            }));
            entered = false; return result;
        } catch (IOException | InterruptedException | RuntimeException | Error original) {
            failed = true; entered = false; throw original;
        }
    }

    /** Actual outputs after physical SAVE/BASELINE and before any domain initializer or cycle rebind. */
    public static final class BeforeImports {
        private final ContinuityStorePort.Session same;
        private final RootApplicationAssembly.Core core;
        private final RootNextEpisodeAssemblyInputs.SessionResources resources;
        private final RootApplicationAssembly.NextEpisodeStage stage;
        private final RootApplicationAssembly.Staged checkpointStage;
        private final RootRuntimeDispatcherFactory.Installed dispatcher;
        private final RootNextEpisodeWindowRuntime.Begun begun;
        private final FirstCheckpointVerifier.VerifiedFirstCheckpoint first;
        private final RootNextEpisodeWindowRuntime.Baselined baseline;
        private final LifecycleEpisodeInputs.NextBaselineBinding binding;
        private final RootApplicationAssembly.NextEpisodeDomainProof proof;
        private final WriterContracts.Head head;
        private BeforeImports(ContinuityStorePort.Session same, RootApplicationAssembly.Core core,
                RootNextEpisodeAssemblyInputs.SessionResources resources, RootApplicationAssembly.NextEpisodeStage stage,
                RootApplicationAssembly.Staged checkpointStage, RootRuntimeDispatcherFactory.Installed dispatcher,
                RootNextEpisodeWindowRuntime.Begun begun, FirstCheckpointVerifier.VerifiedFirstCheckpoint first,
                RootNextEpisodeWindowRuntime.Baselined baseline, LifecycleEpisodeInputs.NextBaselineBinding binding,
                RootApplicationAssembly.NextEpisodeDomainProof proof, WriterContracts.Head head) {
            this.same = same; this.core = core; this.resources = resources; this.stage = stage;
            this.checkpointStage = checkpointStage; this.dispatcher = dispatcher; this.begun = begun;
            this.first = first; this.baseline = baseline; this.binding = binding; this.proof = proof; this.head = head;
        }
        public ContinuityStorePort.Session sameWriter() { return same; }
        public RootApplicationAssembly.Core core() { return core; }
        public RootRuntimeContext context() { return resources.catalog().context(); }
        public RootInstalledCatalog catalog() { return resources.catalog(); }
        public RootApplicationAssembly.NextEpisodeStage stage() { return stage; }
        public RootApplicationAssembly.Staged checkpointStage() { return checkpointStage; }
        public RootRuntimeDispatcherFactory.Installed dispatcher() { return dispatcher; }
        public RootNextEpisodeWindowRuntime.Begun begun() { return begun; }
        public FirstCheckpointVerifier.VerifiedFirstCheckpoint firstCheckpoint() { return first; }
        public RootNextEpisodeWindowRuntime.Baselined baseline() { return baseline; }
        public LifecycleEpisodeInputs.NextBaselineBinding baselineBinding() { return binding; }
        public RootApplicationAssembly.NextEpisodeDomainProof nextProof() { return proof; }
        public RootCrossRunPlanning.Prepared preparedCrossRun() { return resources.catalogs().sources().crossRun(); }
        public RootCheckpointVerifier.SavedCaptureFactory savedCaptureFactory() { return resources.savedCaptureFactory(); }
        public WriterContracts.Head head() { return head; }
    }

    /** The same live private proof after all actual registered domain imports, before rebind/Controller. */
    public static final class Imported {
        private final BeforeImports before;
        private final List<DomainBodies.BodyRef> bodies;
        private final WriterContracts.Head head;
        private Imported(BeforeImports before, List<DomainBodies.BodyRef> bodies, WriterContracts.Head head) {
            this.before = before; this.bodies = List.copyOf(bodies); this.head = head;
        }
        public BeforeImports before() { return before; }
        public ContinuityStorePort.Session sameWriter() { return before.sameWriter(); }
        public RootRuntimeContext context() { return before.context(); }
        public RootApplicationAssembly.NextEpisodeDomainProof nextProof() { return before.nextProof(); }
        public List<DomainBodies.BodyRef> bodies() { return bodies; }
        public WriterContracts.Head head() { return head; }
    }

    /** Publication data, not a claim of ordinary cycle completion, saved days, or any Game business success. */
    public static final class Published {
        private final Imported imported;
        private final ContinuityBatchJournal.ReboundNextBaseline rebound;
        private final RootApplicationSession session;
        private final WriterContracts.Head head;
        private Published(Imported imported, ContinuityBatchJournal.ReboundNextBaseline rebound,
                RootApplicationSession session, WriterContracts.Head head) {
            this.imported = imported; this.rebound = rebound; this.session = session; this.head = head;
        }
        public Imported imported() { return imported; }
        public ContinuityStorePort.Session sameWriter() { return imported.sameWriter(); }
        public ContinuityBatchJournal.ReboundNextBaseline rebound() { return rebound; }
        public RootApplicationSession session() { return session; }
        public WriterContracts.Head head() { return head; }
    }

    private static void requireImported(ContinuityStorePort.Session same, BeforeImports before, List<DomainBodies.BodyRef> bodies) throws IOException {
        var riteRuntime = before.catalog().remainingDomains().riteCreation();
        var riteRegistration = riteRuntime.registration();
        require(riteRegistration == riteRuntime.registration()
                && riteRegistration.slot() == DomainBodies.Slot.RITE_CREATION
                && !riteRegistration.producerSources().isEmpty(),
                "Rite import must use the identical actual installed runtime registration and source closure");
        var expected = EnumSet.of(DomainBodies.Slot.FAMILY, DomainBodies.Slot.CHILD_MATRILINEAL,
                DomainBodies.Slot.DEFAULT_MARRIAGE, DomainBodies.Slot.SWAY, DomainBodies.Slot.CONSTRUCTION,
                DomainBodies.Slot.MERCENARY, DomainBodies.Slot.FACTION, DomainBodies.Slot.OPENING_GATE,
                DomainBodies.Slot.FEAST, DomainBodies.Slot.OPTIONAL_CADENCE,
                DomainBodies.Slot.PRISONER_RELEASE, DomainBodies.Slot.PRISONER_RANSOM);
        expected.add(riteRegistration.slot());
        var actual = EnumSet.noneOf(DomainBodies.Slot.class);
        for (var body : bodies) {
            require(actual.add(body.slot()), "actual Root initializer returned a duplicate domain body");
            if (body.slot() == riteRegistration.slot())
                require(body.contractSchema().equals(riteRegistration.contractSchema()),
                        "actual Rite initializer returned another contract than its installed provider");
            var current = same.readDomain(body.slot());
            require(current instanceof DomainBodies.Available known && known.reference().equals(body),
                    "actual Root import did not retain its canonical registered body");
        }
        require(actual.equals(expected), "actual Root chain requires all thirteen actual registered new-episode domain bodies");
    }

    @FunctionalInterface private interface AssertionWork { void run() throws IOException; }
    private static void assertUnchanged(ContinuityStorePort.Session same, AssertionWork work) throws IOException {
        WriterContracts.Head before = same.head();
        try { work.run(); }
        catch (IOException | RuntimeException | Error original) {
            try { requireSameHead(same.head(), before); } catch (IOException | RuntimeException | Error changed) { original.addSuppressed(changed); }
            throw original;
        }
        requireSameHead(same.head(), before);
    }
    private static void requireSameHead(WriterContracts.Head actual, WriterContracts.Head before) throws IOException {
        if (!actual.digest().equals(before.digest()) || !actual.documents().equals(before.documents())
                || !actual.absent().equals(before.absent()) || !actual.indexRepairs().equals(before.indexRepairs())
                || actual.snapshotNeedsRecovery() != before.snapshotNeedsRecovery())
            throw new IOException("a Root chain assertion changed the actual canonical Head");
    }
}
