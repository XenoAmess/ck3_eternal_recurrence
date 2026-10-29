package org.xar.ck3.control.service.sway;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.sway.*;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.*;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** Concrete per-Game Sway products. Prepared retains only the one Core, never a Game or borrowed Session. */
public final class SwayRuntimeInstaller {
    public record SharedRootSelection(String contractId,org.xar.ck3.control.application.planning.finance.FinanceReadContracts.Registration registration) {
        public SharedRootSelection {StrictJson.require(org.xar.ck3.control.application.planning.finance.FinanceReadContracts.ROOT_CONTRACT_ID.equals(contractId),"exact Finance ROOT contract ID required");Objects.requireNonNull(registration);}
        public SwaySharedRoot resolve(org.xar.ck3.control.application.planning.finance.FinanceRuntimeServices actual) {
            var contract=actual.definitions().contract(org.xar.ck3.control.application.planning.finance.FinanceReadContracts.Query.ROOT);var permission=registration.permission();
            // Trace metadata only: sourceRef equality removed; contractId and all capability/key/mode/wire checks preserved.
            StrictJson.require(contract.contractId().equals(contractId)
                    &&contract.requiredCapability().equals(permission.capability())&&contract.permissionKey().equals(permission.permissionKey())
                    &&contract.permissionMode()==permission.mode()&&contract.wireProfile()==permission.wireProfile(),"installed Finance ROOT differs from the preCore selected original definition");
            return SwaySharedRoot.finance(contract,actual.readPort());
        }
    }
    public sealed interface RuntimeConfiguration permits Configuration,OrdinaryConfiguration {
        Path originalWriterLock();
        Path originalLegacyLedger();
        OrdinarySwayService.Capabilities capabilities();
        boolean invalidationReasonQuery();
        String rootContractId();
        SwaySharedRoot resolveRoot(org.xar.ck3.control.application.planning.finance.FinanceRuntimeServices actual);
    }
    public record Configuration(Path originalWriterLock, Path originalLegacyLedger,
            OrdinarySwayService.Capabilities capabilities, SharedRootSelection sharedRoot,boolean invalidationReasonQuery) implements RuntimeConfiguration {
        public Configuration { originalWriterLock = Objects.requireNonNull(originalWriterLock).toAbsolutePath().normalize(); originalLegacyLedger = Objects.requireNonNull(originalLegacyLedger).toAbsolutePath().normalize(); Objects.requireNonNull(capabilities); Objects.requireNonNull(sharedRoot); }
        @Override public String rootContractId(){return sharedRoot.contractId();}
        @Override public SwaySharedRoot resolveRoot(org.xar.ck3.control.application.planning.finance.FinanceRuntimeServices actual){return sharedRoot.resolve(actual);}
    }
    /** Plain ordinary values. The ROOT query is resolved from the same installed Finance service. */
    public record OrdinaryConfiguration(Path originalWriterLock,Path originalLegacyLedger,
            OrdinarySwayService.Capabilities capabilities,boolean invalidationReasonQuery) implements RuntimeConfiguration {
        public OrdinaryConfiguration {
            originalWriterLock=Objects.requireNonNull(originalWriterLock).toAbsolutePath().normalize();
            originalLegacyLedger=Objects.requireNonNull(originalLegacyLedger).toAbsolutePath().normalize();Objects.requireNonNull(capabilities);
        }
        @Override public String rootContractId(){return org.xar.ck3.control.application.planning.finance.FinanceReadContracts.ROOT_CONTRACT_ID;}
        @Override public SwaySharedRoot resolveRoot(org.xar.ck3.control.application.planning.finance.FinanceRuntimeServices actual){
            var contract=actual.definitions().contract(org.xar.ck3.control.application.planning.finance.FinanceReadContracts.Query.ROOT);
            return SwaySharedRoot.finance(contract,actual.readPort());
        }
    }
    public static Prepared prepareOrdinary(OrdinaryConfiguration configuration,Sources sources) {
        return new Prepared(Objects.requireNonNull(configuration),Objects.requireNonNull(sources));
    }
    public record Sources(SwayRootReads.Sources reads, SwayRootActions.Sources actions, ExactRef policy,
            ExactRef executor, ExactRef composite, ExactRef pendingProducer, List<ExactRef> completeDomainClosure) {
        public Sources { Objects.requireNonNull(reads); Objects.requireNonNull(actions); Objects.requireNonNull(policy); Objects.requireNonNull(executor); Objects.requireNonNull(composite); Objects.requireNonNull(pendingProducer); completeDomainClosure = List.copyOf(completeDomainClosure); StrictJson.require(!completeDomainClosure.isEmpty() && completeDomainClosure.size() <= 64 && completeDomainClosure.stream().allMatch(value -> value.bytes() > 0) && completeDomainClosure.containsAll(List.of(policy,executor,composite,pendingProducer)), "complete actual Sway domain source closure required"); }
    }
    public static final class Prepared {
        private final RuntimeConfiguration configuration; private final Sources sources; private final DomainBodies.Registration registration;
        private RootApplicationAssembly.Core core; private SwayCanonicalDomain domain;
        public Prepared(Configuration configuration, Sources sources) {this((RuntimeConfiguration)configuration,sources);}
        public Prepared(OrdinaryConfiguration configuration, Sources sources) {this((RuntimeConfiguration)configuration,sources);}
        private Prepared(RuntimeConfiguration configuration, Sources sources) {
            this.configuration = Objects.requireNonNull(configuration); this.sources = Objects.requireNonNull(sources);
            registration = new DomainBodies.Registration(DomainBodies.Slot.SWAY, SwayFormalState.SCHEMA, SwayFormalCodec.MAX, sources.completeDomainClosure(),
                    (head, previous, request, body) -> domain().registration().verifier().verify(head, previous, request, body));
        }
        public DomainBodies.Registration registration() { return registration; }
        public synchronized void bindCore(RootApplicationAssembly.Core actual) {
            StrictJson.require(core == null && actual.archive().writer() == actual.writer(), "Sway Core linkage is once-bound to the original writer/archive"); core = Objects.requireNonNull(actual);
        }
        public synchronized SwayCanonicalDomain domain() {
            StrictJson.require(core != null, "actual Sway Core services have not been bound");
            if (domain == null) domain = new SwayCanonicalDomain(configuration.originalWriterLock(), configuration.originalLegacyLedger(), core.archive(), sources.completeDomainClosure(), new SwaySchedulerReplay(core.frameLoader(), configuration.capabilities(), configuration.rootContractId()), core.frameLoader()); return domain;
        }
    }
    private final RootRuntimeContext context; private final Prepared prepared; private final Supplier<OrdinaryPlanner> planner;
    private SwayOrdinaryExecutor executor; private RootDomainInstallation installation;
    private SwayRootReads actualReads; private SwaySelectedFinish selectedFinish;private SwaySelectedJournal selectedJournal;private SwaySelectedObservation selectedObservation;
    private SwaySharedRoot sharedRoot;private SwaySelectedStart selectedStart;private SwayRootActions actualActions;
    public SwayRuntimeInstaller(RootRuntimeContext context, Prepared prepared, Supplier<OrdinaryPlanner> actualFullPlanner) {
        this.context = Objects.requireNonNull(context); this.prepared = Objects.requireNonNull(prepared); planner = Objects.requireNonNull(actualFullPlanner);
    }
    /** Same private actual first-SAVE/BASELINE proof as every other NEXT domain. No old actor state becomes new Ready. */
    public DomainBodies.BodyRef initializeNext(ContinuityStorePort.Session same,RootApplicationAssembly.EpisodeDomainInitializationProof proof)throws IOException {
        Objects.requireNonNull(proof);proof.requireCurrent(same,context);context.writer().requireSession(same);
        var domain=prepared.domain();var originals=context.archive().withSession(same);var current=domain.load(same);
        String nextEpisode=proof.currentDriver().session().episodeRunId();
        var kind=switch(proof.kind()){case NEXT->SwayNextEpisodeImport.Kind.NEXT;case RESTORED_FIRST->SwayNextEpisodeImport.Kind.RESTORED_FIRST;};
        if(current.ledger().episodeRunId().equals(nextEpisode)) {
            var origin=current.ledger().originalMigrationInput();var basis=SwayNextEpisodeImport.decode(originals.loadMaterial(origin).bytes());
            StrictJson.require(basis.kind()==kind&&basis.predecessor().equals(proof.oldDomain(DomainBodies.Slot.SWAY))
                    &&basis.savedSession().equals(proof.baselineMaterial().session())&&basis.beforeSession().equals(proof.beforeSession())&&basis.afterSession().equals(proof.afterSession())
                    &&basis.originalBaselineMaterial().equals(proof.baselineMaterial().reference())&&basis.source().equals(proof.source())
                    &&basis.baseline().equals(proof.baselineMaterial().baseline())&&basis.savedSemantic().equals(proof.savedSemantic())
                    &&basis.currentSemantic().equals(proof.currentSemantic())&&basis.initializationHeadSequence()==proof.initializationHeadSequence()
                    &&basis.initializationHeadDigest().equals(proof.initializationHeadDigest()),"existing NEXT SWAY body belongs to another private baseline");
            StrictJson.require(basis.canonicalParent().equals(originals.receiptReferenceOf(proof.parent()))
                    &&java.util.Arrays.equals(originals.loadMaterial(basis.lifecycleProof()).bytes(),proof.lifecycleProof().encode())
                    &&java.util.Arrays.equals(originals.loadMaterial(basis.predecessorDriver()).bytes(),proof.predecessorDriver().encode())
                    &&java.util.Arrays.equals(originals.loadMaterial(basis.firstSavedDriver()).bytes(),proof.firstSavedDriver().encode())
                    &&java.util.Arrays.equals(originals.loadMaterial(basis.currentDriver()).bytes(),proof.currentDriver().encode()),"retained Sway initialization changed actual private original/current Driver or lifecycle source bytes");
            var old=SwayFormalCodec.decode(originals.loadMaterial(basis.predecessor().payload()).bytes());
            var expected=SwayNextEpisodeImport.replay(same.head().state(),old,basis,origin,originals,context.frameLoader());
            StrictJson.require(java.util.Arrays.equals(SwayFormalCodec.encode(expected),current.original().canonicalBody()),"NEXT SWAY changed after its actual baseline initialization");
            proof.requireCurrent(same,context);return current.original().reference();
        }
        StrictJson.require(current.original().reference().equals(proof.oldDomain(DomainBodies.Slot.SWAY)),"initial Sway transformation needs the exact original BASELINE body, not a retained other-restore body");
        var material=proof.baselineMaterial().reference();var pin=same.capturePin(material,SwayFormalCodec.MAX);
        var archivedMaterial=originals.preserveMaterial(new RawJson(same.readPinned(pin,SwayFormalCodec.MAX)));same.verifyPin(pin);
        var beforeDriver=originals.preserveMaterial(new RawJson(proof.predecessorDriver().encode()));
        var afterDriver=originals.preserveMaterial(new RawJson(proof.firstSavedDriver().encode()));
        var currentDriver=originals.preserveMaterial(new RawJson(proof.currentDriver().encode()));
        var parent=originals.receiptReferenceOf(proof.parent());
        var lifecycle=originals.preserveMaterial(new RawJson(proof.lifecycleProof().encode()));
        var basis=new SwayNextEpisodeImport.Basis(SwayNextEpisodeImport.Format.CURRENT,kind,proof.oldDomain(DomainBodies.Slot.SWAY),proof.beforeSession(),proof.baselineMaterial().session(),proof.afterSession(),beforeDriver,afterDriver,currentDriver,
                material,archivedMaterial,proof.baselineMaterial().baseline(),proof.savedSemantic(),proof.currentSemantic(),proof.source(),parent,lifecycle,proof.initializationHeadSequence(),proof.initializationHeadDigest());
        var origin=originals.preserveMaterial(new RawJson(SwayNextEpisodeImport.encode(basis)));
        proof.requireCurrent(same,context);var preview=domain.previewNext(same,basis,origin);
        proof.requireCurrent(same,context);var committed=domain.commitNext(same,preview);
        proof.requireCurrent(same,context);same.verifyPin(pin);return committed;
    }
    public synchronized RootDomainInstallation install() {
        StrictJson.require(installation == null, "per-Game Sway products are installed once"); SwayCanonicalDomain domain = prepared.domain();
        sharedRoot=prepared.configuration.resolveRoot(context.finance());
        SwayRootReads nativeReads = new SwayRootReads(prepared.sources.reads(),prepared.configuration.invalidationReasonQuery());
        actualReads=nativeReads;
        SwayActionLifecycle.RegisteredReads registered = new SwayActionLifecycle.RegisteredReads() {
            private void attach() { nativeReads.attach(context.readCatalog()); }
            @Override public ReadContract<SwayNativeWire.TargetRead> target(long target) { attach(); return nativeReads.target(target); }
            @Override public ReadContract<SwayNativeWire.AppliedReceipt> receipt(long target, String action, java.math.BigInteger epoch) { attach(); return nativeReads.receipt(target, action, epoch); }
            @Override public ReadContract<SwayObservationReads.Plane> plane(SwayObservationReads.Kind kind, Identity identity) { attach(); return nativeReads.plane(kind, identity); }
        };
        SwayActionLifecycle lifecycle = new SwayActionLifecycle(domain, context.archive(), context.reads(), registered, this::session,
                command -> { PlanningRequest actual = fresh(command); return new SwayActionLifecycle.View(actual.before(), actual.source(), actual.sessionId(), actual.deadline()); }, context.frameLoader());
        SwayRootActions nativeActions = new SwayRootActions(lifecycle, prepared.sources.actions());
        actualActions=nativeActions;
        selectedStart=new SwaySelectedStart(domain,context.archive(),context.reads(),registered,nativeActions,(same,current,deadline)->{
            try {var actual=context.requireRestoration(deadline);SwayRestorationProof.requireBinding(actual,same.head().state(),current,context.archive().withSession(same));return List.of(SwayRestorationProof.material(same.head().state()));}
            catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("actual public Sway cold recovery interrupted",interrupted);}
        });
        selectedFinish=new SwaySelectedFinish(domain,context.archive(),context.reads(),registered,
                ()->"stop-sway-"+java.util.UUID.randomUUID().toString().replace("-",""));
        selectedJournal=new SwaySelectedJournal(domain,context.archive(),context.reads(),nativeReads);
        selectedObservation=new SwaySelectedObservation(domain,context.archive(),context.reads(),nativeReads);
        SwaySessionInputs inputs = new SwaySessionInputs(domain, this::session);
        executor = new SwayOrdinaryExecutor(domain, context.archive(), context.reads(), sharedRoot, registered, nativeActions,
                context::bindings, this::session, this::captureFresh, this::independentFinal, context::requireRestoration, planner);
        var composite = new SwayOrdinaryComposite(executor, domain, this::session);
        var parent = new RootExecutableBindings.CompositeBinding(composite, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, Optional.empty(), prepared.sources.composite(), prepared.sources.composite());
        OrdinarySwayPolicy policy = OrdinarySwayPolicyFactory.create(prepared.sources.policy(), context.reads(), sharedRoot, inputs,
                request -> prepared.configuration.capabilities(), SwayOrdinaryComposite::expected);
        RootDomainIntentPreparation.Binding pending = new RootDomainIntentPreparation.Binding("sway-original-native-intent/v2", prepared.sources.pendingProducer(), command -> {
            String operation = command.operation().value();
            if (operation.equals(SwayNativeWire.STOP)) return true;
            if (!operation.startsWith(SwayNativeWire.START)) return false;
            String target = operation.substring(SwayNativeWire.START.length());
            try { long full = Long.parseLong(target); return target.equals(Long.toString(full)) && full > 0 && full <= 0xffff_ffffL
                    && context.bindings().actualFamily(command.operation()).filter(value -> value == nativeActions.startFamily()).isPresent(); }
            catch (NumberFormatException invalid) { return false; }
        }, lifecycle.pendingProducer());
        installation = new RootDomainInstallation("sway-actual-native-and-ordinary/v2", List.of(prepared.registration()), List.of(), nativeReads.families(),
                List.of(nativeActions.selectedStop()), List.of(parent), List.of(nativeActions.selectedStopReplay(), composite.recorded(prepared.sources.composite())), List.of(nativeActions.startFamily()), List.of(), List.of(),
                List.of(pending), Set.of(new OperationKey(SwayNativeWire.STOP)), List.of(policy), List.of(followingCompletion()),
                List.of(new RootDomainInstallation.FixedDomain(nativeActions.selectedStop(), Domain.diplomacy)), List.of(new RootDomainInstallation.FamilyDomain(nativeActions.startFamily(), Domain.diplomacy)), List.of(new RootDomainInstallation.CompositeDomain(parent, Domain.diplomacy)));
        return installation;
    }
    /** Actual consumer for the shared optional-parent implementation once that contract is installed. */
    public synchronized SwayOrdinaryExecutor executor() { StrictJson.require(executor != null, "actual Sway products not installed"); return executor; }
    public void requireOwner(RootApplicationSession actual) {StrictJson.require(context.actions()==Objects.requireNonNull(actual),"Sway public handler must use its actual per-Game Root session");}
    /** Root's public decision callback already owns the one currentOwned frame and original writer. No dispatch occurs here. */
    public SwaySelectedFinish.Decision prepareFinish(ContinuityStorePort.Session same,
            org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame,
            SwaySelectedFinish.Request request,java.time.Instant deadline)throws IOException {
        context.requireCurrent(deadline);context.writer().requireSession(same);requirePublicFrame(frame);
        StrictJson.require(selectedFinish!=null,"actual Sway Finish producer has not been installed");
        return selectedFinish.prepare(same,new SwayActionLifecycle.View(frame.identity(),frame.source(),frame.sessionId(),deadline),request);
    }
    /** Exact installed observation contract. Public cursor is preserved; ordinary callers still explicitly choose cursor0. */
    public PlanningReadResult<SwayObservationReads.Plane> readObservation(ContinuityStorePort.Session same,
            org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame,
            SwayObservationReads.Query query,java.time.Instant deadline)throws IOException {
        context.requireCurrent(deadline);context.writer().requireSession(same);requirePublicFrame(frame);
        StrictJson.require(actualReads!=null,"actual Sway read products have not been installed");actualReads.attach(context.readCatalog());
        var contract=actualReads.observation(query);var result=context.reads().read(same,contract,
                new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),contract.operation(),SwayObservationReads.arguments(query),deadline));
        if(result instanceof PlanningReadResult.Known<SwayObservationReads.Plane> known) {
            var ledger=prepared.domain().load(same).ledger();
            if(ledger.resolved().filter(value->value.identity().equals(query.identity())&&value.lifecycle().origin().game().equals(frame.identity().game())).isPresent()) {
                var episode=ledger.resolved().orElseThrow();var normalized=known.value().normalized();
                var inputs=new org.xar.ck3.control.g2.m6.M6TerminalSourceComposition.Inputs(
                        query.kind()==SwayObservationReads.Kind.COMPLETION?Optional.of(normalized):Optional.empty(),
                        query.kind()==SwayObservationReads.Kind.EXECUTION?Optional.of(normalized):Optional.empty(),
                        query.kind()==SwayObservationReads.Kind.TERMINATION?Optional.of(normalized):Optional.empty(),
                        query.kind()==SwayObservationReads.Kind.OPINION?Optional.of(normalized):Optional.empty());
                var observed=org.xar.ck3.control.g2.m6.SwayLifecycle.observe(episode.lifecycle(),SwayFormalCodec.m6Episode(episode),inputs,frame.identity());
                prepared.domain().commit(same,new SwayFormalState.LifecycleObserved(observed),new SwayTransitionCodec.Proofs(
                        List.of(context.archive().withSession(same).readReferenceOf(known.receipt())),Optional.empty(),Optional.empty()));
            }
        }
        return result;
    }
    private void requirePublicFrame(org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame) {
        StrictJson.require(frame.identity().machineId().equals(context.game().machineId())&&frame.identity().game().equals(context.game().generation())
                &&frame.source().equals(context.source())&&frame.sessionId().equals(context.game().sessionId()),"Sway public producer crossed actual per-Game source/frame/session");
    }
    /** Public journals name an actual native subject without allocating a submitted action identity. */
    public PlanningReadResult<SwayObservationReads.JournalPlane> readJournal(ContinuityStorePort.Session same,
            org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame,
            SwayObservationReads.JournalQuery query,java.time.Instant deadline)throws IOException {
        context.requireCurrent(deadline);context.writer().requireSession(same);requirePublicFrame(frame);
        StrictJson.require(actualReads!=null,"actual Sway journal products have not been installed");actualReads.attach(context.readCatalog());
        var contract=actualReads.journal(query);return context.reads().read(same,contract,
                new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),contract.operation(),SwayObservationReads.arguments(query),deadline));
    }
    /** Original Service journals have independent sequence domains: the other plane starts at its own cursor0. */
    public SwayObservationReads.JournalBatch readJournalBatch(ContinuityStorePort.Session same,
            org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame,
            SwayObservationReads.JournalQuery query,java.time.Instant deadline)throws IOException {
        context.requireCurrent(deadline);context.writer().requireSession(same);requirePublicFrame(frame);
        StrictJson.require(selectedJournal!=null&&actualReads!=null,"actual Sway Service journal producer has not been installed");actualReads.attach(context.readCatalog());
        return selectedJournal.read(same,new SwayActionLifecycle.View(frame.identity(),frame.source(),frame.sessionId(),deadline),query);
    }
    public void requirePublicObservationSources(ExactRef actualDecoder,ExactRef actualProducer) {
        // Trace metadata only: implementation ref equality and closure membership removed; nonnull checks preserved.
        Objects.requireNonNull(actualDecoder);
        Objects.requireNonNull(actualProducer);
    }
    /** Public completion/opinion preserve their actual actionless subject; no fake action or instance identity. */
    public SwayObservationReads.DirectBatch readDirectObservation(ContinuityStorePort.Session same,
            org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame,
            SwayObservationReads.DirectQuery query,java.time.Instant deadline)throws IOException {
        context.requireCurrent(deadline);context.writer().requireSession(same);requirePublicFrame(frame);
        StrictJson.require(selectedObservation!=null&&actualReads!=null,"actual direct Sway observer has not been installed");actualReads.attach(context.readCatalog());
        return selectedObservation.read(same,new SwayActionLifecycle.View(frame.identity(),frame.source(),frame.sessionId(),deadline),query);
    }
    /** Actual original notification source query. It neither mutates Sway lifecycle nor clears pending/UNKNOWN. */
    public SwayObservationReads.InvalidationPlane readInvalidation(ContinuityStorePort.Session same,
            org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame,
            SwayObservationReads.InvalidationQuery query,java.time.Instant deadline)throws IOException {
        context.requireCurrent(deadline);context.writer().requireSession(same);requirePublicFrame(frame);
        StrictJson.require(prepared.configuration.invalidationReasonQuery()&&actualReads!=null,"selected Sway invalidation private observation is explicitly disabled");
        actualReads.attach(context.readCatalog());var contract=actualReads.invalidation(query);
        var result=context.reads().read(same,contract,new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),contract.operation(),SwayObservationReads.arguments(query),deadline));
        if(!(result instanceof PlanningReadResult.Known<SwayObservationReads.InvalidationPlane> known))throw new IOException("actual selected Sway notification observation unavailable");
        NativeRecordedEvidenceVerifier.requireRead(known.receipt(),context.archive().withSession(same));
        StrictJson.require(known.receipt().request().before().equals(frame.identity())&&known.receipt().request().source().equals(frame.source())&&known.receipt().request().sessionId().equals(frame.sessionId()),"selected notification read crossed its original full frame/source/session");
        return known.value();
    }
    /** Pure retained interpretation through the identical installed family; no observe, dispatch or lifecycle reduction. */
    public SwayObservationReads.InvalidationPlane replayInvalidation(ContinuityStorePort.Session same,
            SwayObservationReads.InvalidationQuery query,PlanningReadReceipt original,java.time.Instant deadline)throws IOException {
        context.requireCurrent(deadline);context.writer().requireSession(same);
        StrictJson.require(actualReads!=null&&original.request().source().equals(context.source())&&original.request().sessionId().equals(context.game().sessionId()),"retained notification belongs to another actual source/session");
        NativeRecordedEvidenceVerifier.requireRead(original,context.archive().withSession(same));actualReads.attach(context.readCatalog());
        return actualReads.invalidation(query).replay(original);
    }
    /** DATA lookup of the identical already installed archive verifier. It never issues a family or observes native state. */
    public Optional<NativeRecordedEvidenceVerifier.Binding> retainedArchived(ActionReceipt original) {
        Objects.requireNonNull(original);StrictJson.require(installation!=null&&actualActions!=null,"actual Sway installation unavailable");var operation=original.command().operation();String key=operation.value();
        ExactRef expected;
        if(key.equals(OrdinarySwayPolicy.OPERATION.value()))expected=prepared.sources.composite();
        else if(key.equals(SwayNativeWire.STOP))expected=prepared.sources.actions().observerAndReplay();
        else if(key.startsWith(SwayNativeWire.START)) {
            if(context.bindings().actualFamily(operation).filter(family->family==actualActions.startFamily()).isEmpty())return Optional.empty();expected=prepared.sources.actions().observerAndReplay();
        } else return Optional.empty();
        var retained=context.bindings().actualArchivedVerifier(operation);retained.ifPresent(binding->StrictJson.require(binding.definitionSource().equals(expected),"retained Sway archive verifier differs from identical installed source"));return retained;
    }
    /** Source DATA for the installed products; callers must still run their actual canonical archive verifier. */
    public List<ExactRef> historyProducerSources(){return prepared.sources.completeDomainClosure();}
    public void requirePublicDriverSources(ExactRef decoder,ExactRef producer) {
        // Trace metadata only: code closure membership removed; nonnull checks preserved.
        Objects.requireNonNull(decoder);
        Objects.requireNonNull(producer);
    }
    public RawJson readPublicTarget(ContinuityStorePort.Session same,org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame,SwayDriverCodec.TargetRequest request,java.time.Instant deadline)throws IOException {
        context.requireCurrent(deadline);context.writer().requireSession(same);requirePublicFrame(frame);
        StrictJson.require(prepared.configuration.capabilities().formalQuery()&&selectedStart!=null,"current configured private Sway target query is disabled");
        return selectedStart.target(same,frame,request,deadline);
    }
    public SwaySelectedStart.Decision prepareStart(ContinuityStorePort.Session same,org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame,SwayDriverCodec.StartRequest request,java.time.Instant deadline)throws IOException {
        context.requireCurrent(deadline);context.writer().requireSession(same);requirePublicFrame(frame);
        StrictJson.require(prepared.configuration.capabilities().formalAction()&&selectedStart!=null&&actualActions!=null,"current configured private Sway action is disabled");actualActions.attach(context.bindings());
        return selectedStart.prepare(same,frame,request,deadline);
    }
    public RawJson readPublicReceipt(ContinuityStorePort.Session same,org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame,SwayDriverCodec.ReceiptRequest request,java.time.Instant deadline)throws IOException {
        context.requireCurrent(deadline);context.writer().requireSession(same);requirePublicFrame(frame);
        StrictJson.require(prepared.configuration.capabilities().formalAction()&&selectedStart!=null,"current configured private Sway receipt is disabled");
        return selectedStart.receipt(same,frame,request,deadline);
    }
    /** Root calls from its original writer lease with the selected physical source witnesses and actual guarded origin read. */
    public SwayFormalState.Ledger initializeFresh(ContinuityStorePort.Session same, RootInitialEpisodeProof actual) throws IOException {
        context.writer().requireSession(same); Objects.requireNonNull(actual); actual.requireCurrent(same);
        actual.requireInitializationPredecessor(same, same.head());
        StrictJson.require(java.nio.file.Files.notExists(prepared.configuration.originalLegacyLedger(), java.nio.file.LinkOption.NOFOLLOW_LINKS)
                && java.nio.file.Files.notExists(prepared.configuration.originalLegacyLedger().resolveSibling("ordinary-sway-schedule-v1.json"), java.nio.file.LinkOption.NOFOLLOW_LINKS),
                "fresh Sway initialization cannot silently discard an existing or unavailable legacy ledger/scheduler");
        var basis = actual.preserveOriginal(same);
        var result = prepared.domain().initializeFresh(same, basis, (head, originalEntry, originals) -> {
            context.writer().requireSession(same); actual.requireCurrent(same);
            StrictJson.require(head.toJson().equals(same.head().state().toJson()) && originalEntry.equals(basis), "fresh Sway producer crossed its actual entry/head");
            var original = RootInitialEpisodeProof.replayOriginal(context, same, originalEntry);
            original.requireInitializationPredecessor(same, same.head());
            StrictJson.require(original.source().equals(context.source()) && original.sessionId().equals(context.game().sessionId())
                    && original.observation().equals(actual.currentObservation()), "fresh Sway initializer changed its actual source/session/Driver");
            return new SwayCanonicalDomain.FreshVerified(original.observation().machineId(), original.episodeId(), original.evidence());
        });
        actual.requireCurrent(same); return result;
    }
    /** A real observed fresh campaign starts new automation history, without borrowing legacy entry receipts. */
    public SwayFormalState.Ledger initializeFresh(ContinuityStorePort.Session same, org.xar.ck3.control.service.root.FreshCampaignContext actual) throws IOException {
        context.writer().requireSession(same);actual.requireCurrent(same);actual.requireInitializationPredecessor(same,same.head());
        StrictJson.require(actual.context()==context,"fresh Sway belongs to another physical context");
        var existing=same.readDomain(DomainBodies.Slot.SWAY);
        if(existing instanceof DomainBodies.Available known){
            var retained=prepared.domain().load(same);
            StrictJson.require(retained.original().reference().equals(known.reference())&&retained.ledger().episodeRunId().equals(actual.episodeId()),
                    "retained Sway domain differs from the actual fresh campaign");
            actual.requireCurrent(same);return retained.ledger();
        }
        if(!(existing instanceof DomainBodies.Unavailable missing)||missing.reason()!=DomainBodies.Reason.UNIMPORTED)
            throw new IOException("fresh Sway cannot replace an unavailable existing body");
        var basis=actual.preserveOriginal(same);
        var result=prepared.domain().initializeFresh(same,basis,(head,originalEntry,originals)->{
            var original=org.xar.ck3.control.service.root.FreshCampaignContext.replayOriginal(context,same,originalEntry);
            original.requireInitializationPredecessor(same,same.head());
            StrictJson.require(head.toJson().equals(same.head().state().toJson())&&originalEntry.equals(basis)
                    &&original.observation().equals(actual.currentObservation()),"fresh Sway input crossed its actual observed campaign");
            return new SwayCanonicalDomain.FreshVerified(original.observation().machineId(),original.episodeId(),original.evidence());
        });
        actual.requireCurrent(same);return result;
    }
    /** Root calls from its original writer lease with the selected physical source witnesses and actual guarded origin read. */
    public SwayFormalState.Ledger importOriginal(ExactRef selectedFormal, Optional<ExactRef> selectedScheduler, ExactRef originRead) throws IOException {
        var borrowed = context.borrowedSession(); var originals = context.archive().withSession(borrowed);
        var formalPin = borrowed.capturePin(selectedFormal, SwayFormalCodec.MAX); byte[] formal = borrowed.readPinned(formalPin, SwayFormalCodec.MAX);
        ExactRef archived = originals.preserveMaterial(new RawJson(formal)); Optional<SwayCanonicalDomain.SchedulerOriginal> schedule = Optional.empty();
        if (selectedScheduler.isPresent()) {
            ExactRef source = selectedScheduler.orElseThrow(); var pin = borrowed.capturePin(source, SwayFormalCodec.MAX); ExactRef body = originals.preserveMaterial(new RawJson(borrowed.readPinned(pin, SwayFormalCodec.MAX))); borrowed.verifyPin(pin); schedule = Optional.of(new SwayCanonicalDomain.SchedulerOriginal(source, body));
        }
        var imported = prepared.domain().importOriginal(borrowed, selectedFormal, archived, originRead, schedule); borrowed.verifyPin(formalPin); return imported;
    }
    public List<String> missingOrdinaryBindings() { return List.of(); }
    private SwayOrdinaryExecutor.FinalRead independentFinal(ActionCommand parent) {
        try {
            context.requireCurrent(context.clock().instant().plusSeconds(30)); var session = context.borrowedSession();
            var physical = new SessionPorts.SessionIdentity(context.game().machineId(), context.game().generation(), context.game().sessionId()); var deadline = context.clock().instant().plusSeconds(30);
            return context.collector().currentOwned(session, physical, deadline, lease -> {
                var frame = lease.frame(); var root = Objects.requireNonNull(sharedRoot);var arguments=root.arguments();
                var observed = root.read(context.reads(),session,new PlanningReadRequest(frame.identity(), frame.source(), frame.sessionId(), root.operation(), arguments, deadline));
                if (!(observed instanceof PlanningReadResult.Known<OpportunityJson.Obj> known)) throw new IOException("actual independently guarded final root read unavailable");
                return new SwayOrdinaryExecutor.FinalRead(NativeEffectEvidence.basis(frame), context.archive().withSession(session).readReferenceOf(known.receipt()));
            });
        } catch (IOException failure) { throw new OrdinarySwayService.Unavailable(failure.getMessage()); }
    }
    /** Shared ordinary completion invokes this for every genuinely confirmed gameplay result, including Root's continuation. */
    public OrdinaryPlanCompletion.ExecutionDisposition consumeFollowing(ActionReceipt actual) {
        if (!actual.settled() || !actual.visibleGameplay()) return new OrdinaryPlanCompletion.Unchanged("actual gameplay result required before consuming Sway observations");
        try { return context.withSession(session -> SwayFollowingConsumption.consume(session, prepared.domain(), context.archive(), context.game().generation(), context.frameLoader(), actual,
                (same, canonical) -> new NativeRecordedEvidenceVerifier(context.archive(), this::session, context.originals(), context.frameLoader(), context.bindings()).verify(same.head(), canonical),
                this::independentFinal)); } catch (ReadPublicationRequiredException required) { throw required; }
        catch (IOException | UncheckedIOException | IllegalArgumentException | IllegalStateException | OrdinarySwayService.Unavailable failure) { return new OrdinaryPlanCompletion.Blocked("actual Sway following-turn consumption unavailable: " + failure.getMessage(), List.of()); }
    }
    private OrdinaryPlanCompletion followingCompletion() {
        return new OrdinaryPlanCompletion() {
            @Override public PlanningDisposition afterPlanning(PlanningRequest original, PlanningResult planned) { return new Unchanged("Sway scheduler is published only by its actual registered parent"); }
            @Override public ExecutionDisposition afterExecution(ActionReceipt actual) { return consumeFollowing(actual); }
        };
    }
    private ContinuityStorePort.Session session() { try { context.requireCurrent(context.clock().instant().plusSeconds(30)); return context.borrowedSession(); } catch (IOException failure) { throw new UncheckedIOException(failure); } }
    private PlanningRequest fresh(ActionCommand parent) { return captureFresh(parent).request(); }
    private SwayOrdinaryExecutor.Fresh captureFresh(ActionCommand parent) {
        try {
            context.requireCurrent(parent.deadline()); var expected = new SessionPorts.SessionIdentity(context.game().machineId(), context.game().generation(), context.game().sessionId());
            SessionPorts.Observation observed = context.collector().observe(expected, parent.deadline());
            if (!(observed instanceof SessionPorts.Ready ready)) throw new OrdinarySwayService.Unavailable("actual fresh ordinary readiness unavailable: " + observed.getClass().getSimpleName());
            PlanningRequest request = ready.request(); StrictJson.require(request.before().game().equals(context.game().generation()) && request.sessionId().equals(context.game().sessionId()) && request.source().equals(context.source()), "fresh ordinary request crossed current managed Game");
            var evidence = ready.semanticEvidence().orElseThrow(() -> new OrdinarySwayService.Unavailable("actual complete final SEM evidence unavailable")); var originals = context.archive().withSession(context.borrowedSession());
            var semantic = DriverJson.object(originals.loadMaterial(evidence.semantic()).bytes(), DriverJson.MAX_NATIVE_BYTES);
            var facts = semantic.get("java_driver_facts_evidence"); StrictJson.require(facts != null && facts != OpportunityJson.Nil.INSTANCE, "actual final Driver facts manifest unavailable");
            var basis = new NativeEffectEvidence.FrameBasis(evidence.originalNativePacket(), ExactRef.fromJson(OpportunityJson.toNode(facts))); var rebuilt = context.frameLoader().load(basis, originals);
            StrictJson.require(rebuilt.identity().equals(request.before()) && rebuilt.source().equals(request.source()) && rebuilt.sessionId().equals(request.sessionId()) && rebuilt.observedAt().equals(evidence.observedAt()), "actual final SEM/Driver/native rebuild differs from fresh Ready");
            return new SwayOrdinaryExecutor.Fresh(request, basis);
        } catch (IOException failure) { throw new OrdinarySwayService.Unavailable(failure.getMessage()); }
        catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new OrdinarySwayService.Unavailable("actual fresh ordinary observation interrupted"); }
    }
}
