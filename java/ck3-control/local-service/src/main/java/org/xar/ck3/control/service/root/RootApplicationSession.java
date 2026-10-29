package org.xar.ck3.control.service.root;

import java.io.IOException;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import java.time.Clock;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.locks.ReentrantLock;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.CheckpointService;
import org.xar.ck3.control.application.checkpoint.CheckpointRequest;
import org.xar.ck3.control.application.checkpoint.PublicCheckpointMaterialCapture;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentAuthority;
import org.xar.ck3.control.application.checkpoint.CheckpointRequestFactory;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.checkpoint.CheckpointResult;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialStore;
import org.xar.ck3.control.application.driver.DriverBootstrap;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.ManagedGameSession;
import org.xar.ck3.control.service.OrdinarySessionHost;

/** Private-minted session owner. External callers cannot install a PID, replace its writer or clear quarantine. */
public final class RootApplicationSession implements ActionCoordinatorPort {
    private final RootApplicationAssembly.Core owner;
    private final RootSessionSwitchboard submissions;
    private final RootSessionSwitchboard.View authorityView;
    private final ContinuityBatchJournal batchJournal;
    private final RootSavedAttachmentLoader savedLoader;
    private final SavedAttachmentAuthority.SourceLoader ownSavedLoader;
    private final RootApplicationAssembly.Restoration restoration;
    private final RootApplicationAssembly.NextEpisodeStage nextEpisode;
    private final ContinuityWriter writer;
    private final NativeOutcomeArchive archive;
    private final ManagedGameSession game;
    private final DriverBootstrap.Adopted driver;
    private final NativeReadinessCollector readiness;
    private final RootLifecycleAuthority physical;
    private final ActionCoordinatorPort coordinator;
    private final PlanningReadCoordinator queries;
    private final OrdinaryCycleTransitions cycles;
    private final CheckpointService checkpoints;
    private final CheckpointRequestFactory checkpointRequests;
    private final DriverCheckpointStore checkpointDrivers;
    private CheckpointResult retainedPublicSave;
    private CheckpointRequest retainedPublicSaveRequest;
    private PublicCheckpointMaterialCapture.Pending pendingPublicSaveMaterial;
    private PublicCheckpointMaterialCapture.Captured capturedPublicSave;
    private boolean publicSaveControllerAdopted;
    private final PublicCheckpointMaterialCapture publicSaveMaterials;
    private final java.util.LinkedHashMap<String,PlannedCheckpoint> plannedCheckpoints=new java.util.LinkedHashMap<>();
    private static final class PlannedCheckpoint {
        private final RootSaveCheckpointCommandProducer.Prepared original;
        private PublicCheckpointMaterialCapture.Pending material;
        private CheckpointResult result;
        private PublicCheckpointMaterialCapture.Captured captured;
        private boolean controllerAdopted;
        private PlannedCheckpoint(RootSaveCheckpointCommandProducer.Prepared original){this.original=original;}
    }
    private final SavedAttachmentSourceStore sources;
    private final SavedCheckpointMaterialStore savedMaterials;
    private final RootRestoreAdapters restores;
    private final org.xar.ck3.control.application.driver.DriverCapabilityRuntime capabilities;
    private final org.xar.ck3.control.application.driver.DriverReadHistoryPublisher readHistory;
    private final RootReadPublicationCompletion readCompletion;
    private final SessionController controller;
    private final RootInstalledCatalog resourceCatalog;
    private final Clock clock;
    private final ReentrantLock calls = new ReentrantLock();
    private volatile OrdinarySessionHost installedHost;
    private boolean rebindAttempted;
    private ContinuityBatchJournal.ReboundCycle rebound;
    private boolean autoPresentationActive;
    private record RetainedNextAuto(ActionReceipt parent, org.xar.ck3.control.contracts.ExactRef parentReference,
            org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known originalFacts) { }
    private RetainedNextAuto retainedNextAuto;
    RootApplicationSession(RootApplicationAssembly.Core owner, RootSessionSwitchboard submissions,
            RootSessionSwitchboard.View authorityView, ContinuityBatchJournal batchJournal,
            RootSavedAttachmentLoader savedLoader, SavedAttachmentAuthority.SourceLoader ownSavedLoader,
            RootApplicationAssembly.Restoration restoration,RootApplicationAssembly.NextEpisodeStage nextEpisode,
            ContinuityWriter writer, NativeOutcomeArchive archive, ManagedGameSession game,
            DriverBootstrap.Adopted driver, NativeReadinessCollector readiness,RootLifecycleAuthority physical,ActionCoordinatorPort coordinator,
            PlanningReadCoordinator queries, OrdinaryCycleTransitions cycles, CheckpointService checkpoints,
            CheckpointRequestFactory checkpointRequests,DriverCheckpointStore checkpointDrivers,
            SavedAttachmentSourceStore sources,SavedCheckpointMaterialStore savedMaterials,RootRestoreAdapters restores,
            org.xar.ck3.control.application.driver.DriverCapabilityRuntime capabilities,
            org.xar.ck3.control.application.driver.DriverReadHistoryPublisher readHistory,
            RootReadPublicationCompletion readCompletion, SessionController controller,RootInstalledCatalog resourceCatalog, Clock clock) {
        this.owner = Objects.requireNonNull(owner); this.submissions = Objects.requireNonNull(submissions);
        this.authorityView = Objects.requireNonNull(authorityView); this.batchJournal = Objects.requireNonNull(batchJournal);
        this.savedLoader = Objects.requireNonNull(savedLoader); this.ownSavedLoader = Objects.requireNonNull(ownSavedLoader);
        this.restoration = restoration;
        this.nextEpisode=nextEpisode;
        this.writer = Objects.requireNonNull(writer); this.archive = Objects.requireNonNull(archive); this.game = Objects.requireNonNull(game);
        this.driver = Objects.requireNonNull(driver); this.readiness = Objects.requireNonNull(readiness); this.coordinator = Objects.requireNonNull(coordinator);
        this.physical=Objects.requireNonNull(physical);
        this.queries = Objects.requireNonNull(queries); this.cycles = Objects.requireNonNull(cycles); this.checkpoints = Objects.requireNonNull(checkpoints);
        this.checkpointRequests=Objects.requireNonNull(checkpointRequests);this.checkpointDrivers=Objects.requireNonNull(checkpointDrivers);
        this.sources = Objects.requireNonNull(sources); this.controller = Objects.requireNonNull(controller); this.clock = Objects.requireNonNull(clock);
        this.resourceCatalog=Objects.requireNonNull(resourceCatalog);
        StrictJson.require(resourceCatalog.context().core()==owner&&resourceCatalog.context().game()==game
                &&resourceCatalog.context().adopted()==driver,"session cleanup must retain its identical actual installed catalog");
        controller.bindRetainedIncidents(resourceCatalog.offline());
        controller.bindRestartDriver(driver.authority());
        driver.authority().bindPresentationSource(resourceCatalog.physicalActions());
        this.savedMaterials=Objects.requireNonNull(savedMaterials);
        this.publicSaveMaterials=new PublicCheckpointMaterialCapture(writer,batchJournal,savedMaterials,owner.actions());
        this.restores = Objects.requireNonNull(restores);
        this.capabilities = Objects.requireNonNull(capabilities);
        this.readHistory=Objects.requireNonNull(readHistory);this.readCompletion=Objects.requireNonNull(readCompletion);
        StrictJson.require(archive.writer() == writer && readiness.identity().equals(controller.identity())
                && game.generation().equals(controller.identity().game()) && game.sessionId().equals(controller.identity().sessionId()),
                "session must retain the identical writer/archive/Game/loop owner");
    }
    public RawJson automaticCameraStatus(){return resourceCatalog.additionalDomains().gui().automaticCamera().status();}
    public SessionPorts.SessionIdentity identity() { return controller.identity(); }
    public RootInstalledCatalog installedCatalog() { return resourceCatalog; }
    public ContinuityWriter writer() { return writer; }
    public NativeOutcomeArchive archive() { return archive; }
    public DriverBootstrap.Adopted driver() { return driver; }
    public NativeReadinessCollector readiness() { return readiness; }
    public org.xar.ck3.control.nativebridge.NativeGameTransport nativeTransport() throws IOException { return game.nativeTransport(); }
    public OrdinaryCycleTransitions cycles() { return cycles; }
    public ContinuityBatchJournal batchJournal(){return batchJournal;}
    public SavedAttachmentSourceStore savedSources() { return sources; }
    public SavedCheckpointMaterialStore savedMaterials(){return savedMaterials;}
    public RootRestoreAdapters restoreAdapters() { return restores; }
    public org.xar.ck3.control.application.driver.DriverCapabilityRuntime capabilityRuntime() { return capabilities; }
    public CheckpointService checkpoints() { return checkpoints; }
    /** Same configured producer only. This getter supplies no current frame, command or submit permission. */
    public CheckpointRequestFactory checkpointRequestFactory(){return checkpointRequests;}
    /** Only the actual same-root command producer can retain a SAVE proposal; this does not submit it. */
    public void retainPlannedCheckpoint(RootSaveCheckpointCommandProducer.Prepared actual)throws IOException {
        if(!calls.isHeldByCurrentThread())throw new IOException("planned SAVE preparation requires the original Root calls lock");
        requireInstalled();var same=writer.borrowedSession();actual.requireOwner(resourceCatalog.context(),this,same);
        var command=actual.command();PlannedCheckpoint previous=plannedCheckpoints.get(command.actionId());
        if(previous!=null){StrictJson.require(previous.original==actual,"planned SAVE identity cannot replace its private original request");return;}
        plannedCheckpoints.entrySet().removeIf(row->row.getValue().controllerAdopted);
        if(plannedCheckpoints.size()>=64)throw new IOException("bounded unresolved planned SAVE originals exhausted");
        plannedCheckpoints.put(command.actionId(),new PlannedCheckpoint(actual));
    }
    private ActionReceipt executePlannedCheckpoint(ContinuityStorePort.Session same,ActionCommand command,boolean query)throws IOException,InterruptedException {
        PlannedCheckpoint held=plannedCheckpoints.get(command.actionId());
        if(held==null)throw new IOException("actual planned SAVE request producer is unavailable");
        if(query&&held.material==null)throw new IOException("original planned SAVE has no launched service context; reconciliation cannot submit it");
        StrictJson.require(java.util.Arrays.equals(ActionCodec.encodeCommand(command),ActionCodec.encodeCommand(held.original.command()))
                &&command.operation().value().equals("save-checkpoint"),"planned SAVE changed its original strong command");
        if(held.material==null){
            requireInstalled();requireCommand(command);held.original.requireOwner(resourceCatalog.context(),this,same);
            var publication=readCompletion.flushInSession(same);
            if(publication.isPresent())throw new org.xar.ck3.control.application.session.ReadPublicationRefreshException(command,
                    Optional.empty(),publication.orElseThrow(),Optional.empty());
            held.material=publicSaveMaterials.begin(same,identity(),held.original.semantic(),held.original.request());
            held.result=checkpoints.checkpoint(held.original.request());
        }else if(!(held.result instanceof CheckpointResult.Confirmed)){
            requireOwner();
            held.result=checkpoints.queryOriginal(command.actionId(),clock.instant().plus(ActionObservationWindow.MAXIMUM_WINDOW));
        }
        if(held.result instanceof CheckpointResult.Confirmed confirmed){
            held.captured=publicSaveMaterials.confirm(same,held.material,confirmed);
            if(!held.controllerAdopted){
                Instant adoptionDeadline=query?clock.instant().plus(ActionObservationWindow.MAXIMUM_WINDOW):command.deadline();
                controller.acceptPublicCheckpoint(same,held.captured,adoptionDeadline);
                held.controllerAdopted=true;
            }
        }
        return RootCheckpointPublicCalls.action(Objects.requireNonNull(held.result))
                .orElseThrow(()->new IOException("original planned SAVE has no canonical action receipt; no new SAVE was submitted"));
    }
    /** Runs the existing Controller's identical complete planner inside the caller's actual captured planning scope. */
    public org.xar.ck3.control.application.planning.PlanningResult planPublic(org.xar.ck3.control.application.planning.PlanningRequest original)throws IOException {
        if(!calls.isHeldByCurrentThread())throw new IOException("public PLAN requires the original Root call scope");
        requireInstalled();return controller.planPublic(Objects.requireNonNull(original));
    }
    /** The installed private source owns origin, physical originals and canonical operator identity. */
    RootSetPlayedCharacterRuntime.Completed executeOperatorCharacter(RootOperatorCharacterAuthority.Installed actual,
            org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch.Request request,Instant deadline)throws IOException,InterruptedException {
        Objects.requireNonNull(actual);Objects.requireNonNull(request);calls.lockInterruptibly();
        try{
            requireOwner();requireDeadline(deadline);actual.requireOwner(resourceCatalog.context());
            if(!actual.hasOriginalPending(this)){requireNoPendingCheckpointAdoption();controller.requireOperatorBefore();}
            var result=owner.withBorrowed(()->actual.executeCurrent(this,request,deadline,owner.activeBorrowedSession()));
            // The Controller's journal acquires the original writer only after the operator's borrowed scope has closed.
            controller.acceptOperatorRebound(result.receipt(),deadline);actual.accepted(result);return result.completed();
        }finally{calls.unlock();}
    }
    ActionReceipt operatorCanonical(RootOperatorCharacterAuthority.Installed actual,ContinuityStorePort.Session same,
            ActionCommand original,boolean query)throws IOException {
        if(!calls.isHeldByCurrentThread())throw new IOException("operator canonical route escaped the original Root calls lock");
        requireOwner();actual.requireOwner(resourceCatalog.context());actual.requireCanonicalScope(this,same,original);
        StrictJson.require(original.expectation() instanceof CommandExpectation.OperatorRebind,"private operator route cannot submit an ordinary command");
        return query?coordinator.reconcile(same,original.actionId()):coordinator.execute(same,original);
    }
    /** An explicit public SAVE retains its genuine cycle frontier and the existing saved-material commit boundary. */
    public RootCheckpointPublicCalls.SaveCall saveCheckpointPublic(RootCheckpointPublicCalls.Request request,Instant deadline)
            throws IOException,InterruptedException {
        Objects.requireNonNull(request);calls.lockInterruptibly();
        try {
            boolean retained=pendingPublicSaveMaterial!=null&&!publicSaveControllerAdopted
                    &&!(retainedPublicSave instanceof CheckpointResult.Rejected);
            // Only this private original attempt may be queried or have its material confirmed under quarantine.
            if(retained)requireOwner();else requireInstalled();
            requireDeadline(deadline);
            var result=owner.withBorrowed(()->{
                var same=owner.activeBorrowedSession();
                if(retained) {
                    if(!(retainedPublicSave instanceof CheckpointResult.Confirmed))
                        retainedPublicSave=checkpoints.queryOriginal(Objects.requireNonNull(retainedPublicSaveRequest).saveCommand().actionId(),deadline);
                } else {
                    record Preparation(org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame,
                            SemanticEvidence semantic) { }
                    var actual=readiness.currentOwned(same,identity(),deadline,lease->{
                        request.effectiveExpectedRevision().ifPresent(expected->{if(!expected.equals(lease.frame().identity().frame().revision()))
                            throw new org.xar.ck3.control.service.mcp.PublicServiceFailure(org.xar.ck3.control.service.mcp.PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,
                                    "explicit public SAVE revision is stale",Optional.empty());});
                        return new Preparation(lease.frame(),lease.semantic());
                    });
                    var changed=readCompletion.flushInSession(same);
                    if(changed.isPresent())throw new IOException("READ_PUBLICATION_REFRESH_REQUIRED: actual public SAVE preparation changed its source frame; zero dispatch");
                    var frame=actual.frame();
                    var prepared=checkpointRequests.prepare(frame.identity(),frame.source(),frame.sessionId(),Optional.empty(),deadline);
                    var pending=publicSaveMaterials.begin(same,identity(),actual.semantic(),prepared);
                    retainedPublicSaveRequest=prepared;pendingPublicSaveMaterial=pending;retainedPublicSave=null;
                    capturedPublicSave=null;publicSaveControllerAdopted=false;
                    retainedPublicSave=checkpoints.checkpoint(prepared);
                }
                var actual=Objects.requireNonNull(retainedPublicSave);
                if(actual instanceof CheckpointResult.Confirmed confirmed)
                    capturedPublicSave=publicSaveMaterials.confirm(same,Objects.requireNonNull(pendingPublicSaveMaterial),confirmed);
                Optional<org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Complete> saved=actual instanceof CheckpointResult.Confirmed confirmed
                        ?Optional.of(checkpointDrivers.readVerified(confirmed.pair())):Optional.empty();
                var action=RootCheckpointPublicCalls.action(actual);
                return new RootCheckpointPublicCalls.SaveCall(actual,saved,action.map(receipt->archive.withSession(same).receiptReferenceOf(receipt)));
            });
            if(capturedPublicSave!=null&&!publicSaveControllerAdopted){
                // The Controller's idle path enters its own original writer only after this borrowed scope has ended.
                controller.acceptPublicCheckpoint(capturedPublicSave,deadline);
                publicSaveControllerAdopted=true;
            }
            return result;
        }finally{calls.unlock();}
    }
    /** The original call lock spans replacement, private material adoption and actual Host publication. */
    public RootCheckpointPublicCalls.RestoreCall restoreCheckpointPublic(RootCheckpointPublicCalls.Request request,Instant deadline)
            throws IOException,InterruptedException {
        Objects.requireNonNull(request);Objects.requireNonNull(deadline);calls.lockInterruptibly();
        try {
            requireDeadline(deadline);var actual=owner.publicRestoreRuntime(this);
            requirePublicRestoreCall(actual);return actual.restore(this,request,deadline);
        }finally{calls.unlock();}
    }
    void requirePublicRestoreCall(RootPublicRestoreRuntime actual)throws IOException {
        if(!calls.isHeldByCurrentThread())throw new IOException("public restoration requires this original Root call lock");
        owner.requirePublicRestoreCall(this,Objects.requireNonNull(actual));
    }
    /** Captures actual physical material once; no caller supplies a checkpoint path, pair or material qualification. */
    RootPublicRestoreRuntime.Captured capturePublicRestore(RootCheckpointPublicCalls.Request request,Instant deadline)
            throws IOException,InterruptedException {
        var runtime=owner.publicRestoreRuntime(this);requirePublicRestoreCall(runtime);requireOwner();requireDeadline(deadline);
        return owner.withBorrowed(()->{
            var same=owner.activeBorrowedSession();writer.requireSession(same);
            var material=publicSaveMaterials.currentPhysical(same,controller.savedPair());
            var pair=material.pair();
            // Restore consumes physical source-qualified DATA, including an UNKNOWN Root whose ordinary planner is quarantined.
            // No ordinary capability projection, Ready, action or SAVE admission is requested by this capture.
            var current=physical.withSnapshot(same,deadline,lease->{
                lease.assertCurrent(same);
                var frame=lease.ordinary().orElseThrow(()->new IOException("actual public RESTORE actor/episode cannot join its retained Driver"));
                var semantic=frame.semantic();var original=physical.semantic(same,identity(),lease);
                boolean map=org.xar.ck3.control.planning.opportunity.OpportunityJson.bool(semantic.get("map_ready"),"map_ready");
                boolean paused=org.xar.ck3.control.planning.opportunity.OpportunityJson.bool(semantic.get("paused"),"paused");
                boolean eligible=map&&paused&&NativeReadinessCollector.checkpointEligibility(semantic)==SessionPorts.CheckpointEligibility.SAFE;
                request.effectiveExpectedRevision().ifPresent(expected->{if(!expected.equals(frame.identity().frame().revision()))
                    throw new org.xar.ck3.control.service.mcp.PublicServiceFailure(org.xar.ck3.control.service.mcp.PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,
                            "explicit public RESTORE revision is stale",Optional.empty());});
                lease.assertCurrent(same);
                return new org.xar.ck3.control.application.checkpoint.CheckpointRequest.Readiness(frame.identity(),frame.source(),frame.sessionId(),
                        pair.lineageId(),map,paused,eligible,"actual current physical RESTORE source; no ordinary planning or SAVE admission",original.originalNativePacket(),frame.observedAt());
            });
            StrictJson.require(current.observed().game().equals(identity().game())&&current.observed().machineId().equals(identity().machineId())
                    &&current.sessionId().equals(identity().sessionId()),"public restoration capture crossed its physical current Root");
            var changed=readCompletion.flushInSession(same);
            if(changed.isPresent())throw new IOException("READ_PUBLICATION_REFRESH_REQUIRED: public RESTORE preparation changed its source frame; zero replacement");
            savedMaterials.requireOwn(material);material.requirePhysical(same);
            requirePublicRestoreCall(runtime);requireDeadline(deadline);
            String head=same.head().digest();String requestId=RootPublicRestoreRuntime.requestIdentity(identity(),head,pair);
            var original=new org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.Request(requestId,pair,current,head,deadline,material);
            return new RootPublicRestoreRuntime.Captured(original,checkpointDrivers);
        });
    }
    /** The public adapter cannot bypass the Controller's actual terminal transition and episode publication. */
    public <T>T executePublicLifecycle(RootLifecycleRuntimeFactory.Installed actual,
            LifecycleExpectedPostcondition.Operation desired,Optional<java.math.BigInteger> expectedRevision,Instant deadline,
            PublicActionResult<T> present)throws IOException,InterruptedException {
        Objects.requireNonNull(actual);Objects.requireNonNull(desired);Objects.requireNonNull(expectedRevision);Objects.requireNonNull(present);
        calls.lockInterruptibly();
        try {
            requireOwner();requireNoPendingCheckpointAdoption();requireDeadline(deadline);
            StrictJson.require(actual.physical()==physical,"public lifecycle crossed the actual current physical terminal authority");
            StrictJson.require(desired==LifecycleExpectedPostcondition.Operation.DEATH_TERMINAL
                    ||desired==LifecycleExpectedPostcondition.Operation.START_NEXT_EPISODE
                    ||desired==LifecycleExpectedPostcondition.Operation.CONTINUE_SUCCESSOR,"public lifecycle operation is not admitted");
            expectedRevision.ifPresent(value->StrictJson.require(value.signum()>=0&&value.bitLength()<=64,"public lifecycle revision must be uint64"));
            // The real Controller owns its writer scopes, operation/revision checks and terminal command issuer.
            var turn=controller.terminalTurn(desired,expectedRevision,deadline);var execution=turn.execution();
            if(execution.lifecycleTurns().size()!=1)throw new IOException("actual Controller did not submit the requested lifecycle operation: "+execution.terminal());
            var receipt=execution.lifecycleTurns().getFirst().receipt();
            StrictJson.require(receipt.command().origin() instanceof CommandOrigin.LifecycleTerminal
                    &&receipt.command().operation().equals(desired.key()),"actual Controller lifecycle result differs from the requested operation");
            owner.afterTurn(this,execution,deadline);
            // NEXT can retire this Root. Present its original canonical receipt from the same retained archive.
            return writer.locked(same->{
                var scoped=archive.withSession(same);var reference=scoped.receiptReferenceOf(receipt);
                StrictJson.require(scoped.loadReceipt(reference).equals(receipt),"public lifecycle lost its actual original canonical result");
                return present.present(receipt,scoped,same);
            });
        }finally{calls.unlock();}
    }
    public boolean isRetired() { return controller.isRetired(); }
    boolean hasInstalledHost() { return installedHost!=null&&installedHost.current().orElse(null)==controller&&!controller.isRetired(); }
    boolean ownedBy(RootApplicationAssembly.Core expected) { return owner == expected; }
    void commitInstalledHost(OrdinarySessionHost actual){installedHost=actual;}
    SessionController controllerForPublication(){return controller;}
    RootSessionSwitchboard.View viewForPublication(){return authorityView;}
    SavedAttachmentAuthority.SourceLoader loaderForPublication(){return ownSavedLoader;}
    org.xar.ck3.control.application.driver.DriverReadHistoryPublisher readsForPublication(){return readHistory;}
    OrdinarySessionHost hostForPublication(){return installedHost;}
    /** Publication does not run another turn or SAVE; it consumes only the complete privately constructed successor. */
    public void publishNext(Instant deadline)throws IOException,InterruptedException {
        calls.lockInterruptibly();
        try {
            StrictJson.require(nextEpisode!=null&&restoration==null&&installedHost==null,
                    "only a privately staged next episode may publish through this branch");requireDeadline(deadline);
            nextEpisode.previous().withRetiredRootStage(owner,()->owner.withBorrowed(()->{
                var same=owner.activeBorrowedSession();owner.publishNextSession(same,nextEpisode,this,deadline);return null;
            }));
            prepareTransportContinuity(deadline);
        }finally{calls.unlock();}
    }
    /** A closed physical predecessor still retains its actual writer/Driver custody for one private next transfer. */
    <T> T withRetiredRootStage(RootApplicationAssembly.Core expected,
            org.xar.ck3.control.application.planning.OrdinaryPlanCompletion.ScopeWork<T> work) throws IOException, InterruptedException {
        calls.lockInterruptibly();
        try {
            StrictJson.require(owner == expected && installedHost != null && controller.isRetired()
                    && !controller.isRunning() && !controller.isQuarantined(),
                    "next episode staging requires the actual idle retired Root, without clearing UNKNOWN");
            expected.requireRetiredStageAccess(this);closeResourcesForRetirement();return Objects.requireNonNull(work).run();
        } finally { calls.unlock(); }
    }
    @FunctionalInterface public interface PublicObservationWork<T> {
        T read(org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame,
                org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known known,
                org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed) throws IOException;
    }
    public interface SnapshotWork<T> {
        T ordinary(org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete actual,
                org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known known,
                org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same)throws IOException;
        T terminal(org.xar.ck3.control.application.driver.DriverObservationAssembler.FullSnapshot actual,
                LifecycleIdentity identity,org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known known,
                org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same)throws IOException;
    }
    /** One source-qualified physical capture. Snapshot data remains readable after UNKNOWN without granting another action. */
    public <T>T withPublicSnapshot(Instant deadline,SnapshotWork<T> work)throws IOException,InterruptedException {
        Objects.requireNonNull(work);calls.lockInterruptibly();
        try {
            requireOwner();requireDeadline(deadline);
            return owner.withBorrowed(()->{
                var same=writer.borrowedSession();
                return physical.withSnapshot(same,deadline,lease->{
                    lease.assertCurrent(same);requireDeadline(deadline);
                    T result;
                    if(lease.ordinary().isPresent())result=work.ordinary(lease.ordinary().orElseThrow(),lease.factsKnown(),same);
                    else if(lease.terminalIdentity().isPresent())result=work.terminal(lease.fullSnapshot(),lease.terminalIdentity().orElseThrow(),lease.factsKnown(),same);
                    else throw new IOException("actual physical snapshot has no verified living or terminal source branch");
                    lease.assertCurrent(same);requireDeadline(deadline);return result;
                });
            });
        }finally{calls.unlock();}
    }
    /** State and capability endpoints consume this same current native/Driver/source scope. */
    public <T> T withPublicObservation(Instant deadline, PublicObservationWork<T> work) throws IOException, InterruptedException {
        Objects.requireNonNull(work); calls.lockInterruptibly();
        try {
            requireInstalled(); requireDeadline(deadline);
            return owner.withBorrowed(()->{
                var borrowed=writer.borrowedSession();
                Throwable originalFailure=null;
                try {
                    return readiness.currentOwned(borrowed, identity(), deadline,
                        lease -> { requireDeadline(deadline); T value = work.read(lease.frame(), lease.driver(), borrowed); requireDeadline(deadline); return value; });
                } catch(IOException|RuntimeException|Error failure) {
                    originalFailure=failure;throw failure;
                } finally {
                    // The actual readiness/Driver freeze has exited before any queued failure row is committed.
                    try {readCompletion.flushInSession(borrowed);}
                    catch(IOException|RuntimeException|Error publicationFailure) {
                        if(originalFailure!=null){if(publicationFailure!=originalFailure)originalFailure.addSuppressed(publicationFailure);}
                        else throw publicationFailure;
                    }
                }
            });
        } finally { calls.unlock(); }
    }
    @FunctionalInterface public interface PublicCapabilitiesWork<T> {
        T read(org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame,
                org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known known,
                org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed,
                org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj actualReceivedCapabilities) throws IOException;
    }
    public <T> T withPublicCapabilitiesObservation(Instant deadline, PublicCapabilitiesWork<T> work) throws IOException, InterruptedException {
        Objects.requireNonNull(work); calls.lockInterruptibly();
        try {
            requireInstalled(); requireDeadline(deadline);
            return owner.withBorrowed(()->{
                var borrowed=writer.borrowedSession();
                Throwable originalFailure=null;
                try {
                    return readiness.currentOwned(borrowed, identity(), deadline,
                        lease -> { requireDeadline(deadline); T value = work.read(lease.frame(), lease.driver(), borrowed, lease.capabilities()); requireDeadline(deadline); return value; });
                } catch(IOException|RuntimeException|Error failure) {
                    originalFailure=failure;throw failure;
                } finally {
                    try {readCompletion.flushInSession(borrowed);}
                    catch(IOException|RuntimeException|Error publicationFailure) {
                        if(originalFailure!=null){if(publicationFailure!=originalFailure)originalFailure.addSuppressed(publicationFailure);}
                        else throw publicationFailure;
                    }
                }
            });
        } finally { calls.unlock(); }
    }
    public <T> PlanningReadResult<T> readCurrent(ReadContract<T> contract, java.math.BigInteger expectedPublicRevision,
            org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj arguments, Instant deadline) throws IOException, InterruptedException {
        return readCurrent(contract, Optional.of(Objects.requireNonNull(expectedPublicRevision)), arguments, deadline);
    }
    public <T> PlanningReadResult<T> readCurrent(ReadContract<T> contract, Optional<java.math.BigInteger> expectedPublicRevision,
            org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj arguments, Instant deadline) throws IOException, InterruptedException {
        Objects.requireNonNull(contract); Objects.requireNonNull(expectedPublicRevision); Objects.requireNonNull(arguments);
        return withPublicObservation(deadline, (frame, known, borrowed) -> {
            expectedPublicRevision.ifPresent(expected -> StrictJson.require(frame.identity().frame().revision().equals(expected),
                    "public query crossed actual public revision"));
            PlanningReadRequest request = new PlanningReadRequest(frame.identity(), frame.source(), frame.sessionId(), contract.operation(), arguments, deadline);
            return queries.read(borrowed, contract, request);
        });
    }
    @FunctionalInterface public interface PublicActionPreparation {
        ActionCommand prepare(org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete actualFrame,
                org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known actualDriver,
                org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed) throws IOException;
    }
    @FunctionalInterface public interface PublicPlanningActionPreparation {
        ActionCommand prepare(org.xar.ck3.control.application.planning.PlanningRequest original,
                org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete actualFrame,
                org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known actualDriver,
                org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed) throws IOException;
    }
    @FunctionalInterface private interface PublicActionScope {
        ActionCommand prepare(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same) throws IOException;
    }
    @FunctionalInterface public interface PublicActionResult<T> {
        T present(ActionReceipt actual, ActionPorts.OutcomeArchive sameScopedArchive,
                org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed) throws IOException;
    }
    public interface PublicDecisionVisitor<T, R> {
        R submit(ActionCommand actual) throws IOException;
        R reconcile(String originalActionId, org.xar.ck3.control.contracts.ExactRef originalReceipt) throws IOException;
        R retain(T actualResult) throws IOException;
    }
    public sealed interface PublicActionDecision<T> permits SubmitPublicAction, ReconcilePublicAction, RetainPublicResult {
        <R> R visit(PublicDecisionVisitor<T, R> visitor) throws IOException;
    }
    public record SubmitPublicAction<T>(ActionCommand command) implements PublicActionDecision<T> {
        public SubmitPublicAction { Objects.requireNonNull(command); }
        @Override public <R> R visit(PublicDecisionVisitor<T, R> visitor) throws IOException { return visitor.submit(command); }
    }
    public record ReconcilePublicAction<T>(String originalActionId, org.xar.ck3.control.contracts.ExactRef originalReceipt)
            implements PublicActionDecision<T> {
        public ReconcilePublicAction { StrictJson.text(originalActionId); Objects.requireNonNull(originalReceipt); }
        @Override public <R> R visit(PublicDecisionVisitor<T, R> visitor) throws IOException { return visitor.reconcile(originalActionId, originalReceipt); }
    }
    public record RetainPublicResult<T>(T result) implements PublicActionDecision<T> {
        public RetainPublicResult { Objects.requireNonNull(result); }
        @Override public <R> R visit(PublicDecisionVisitor<T, R> visitor) throws IOException { return visitor.retain(result); }
    }
    @FunctionalInterface public interface PublicDecisionPreparation<T> {
        PublicActionDecision<T> prepare(org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete actualFrame,
                org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known actualDriver,
                org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed) throws IOException;
    }
    /** Read-only decisions and existing UNKNOWN reconciliation never acquire a new command or identity. */
    public <T> T executePublicDecision(Instant deadline, PublicDecisionPreparation<T> preparation, PublicActionResult<T> result)
            throws IOException, InterruptedException {
        Objects.requireNonNull(deadline); Objects.requireNonNull(preparation); Objects.requireNonNull(result);
        calls.lockInterruptibly();
        try {
            requireOwner(); requireNoPendingCheckpointAdoption(); requireDeadline(deadline);
            return owner.withBorrowed(() -> {
                var same = owner.activeBorrowedSession(); Throwable originalFailure = null;
                try {
                    PublicActionDecision<T> choice = readiness.currentOwned(same, identity(), deadline, lease -> {
                        PublicActionDecision<T> actual = Objects.requireNonNull(preparation.prepare(lease.frame(), lease.driver(), same));
                        actual.visit(new PublicDecisionVisitor<T, Void>() {
                            @Override public Void submit(ActionCommand command) throws IOException {
                                requirePublicCommand(command, lease.frame(), deadline); return null;
                            }
                            @Override public Void reconcile(String actionId, org.xar.ck3.control.contracts.ExactRef receipt) throws IOException {
                                requireOriginalPublicReconciliation(same, actionId, receipt); return null;
                            }
                            @Override public Void retain(T actualResult) { return null; }
                        });
                        return actual;
                    });
                    var published = readCompletion.flushInSession(same);
                    requireDeadline(deadline);
                    return choice.visit(new PublicDecisionVisitor<T, T>() {
                        private void requireNoRefresh(ActionCommand command) {
                            if (published.isPresent()) throw new ReadPublicationRefreshException(command,
                                    Optional.empty(), published.orElseThrow(), Optional.empty());
                        }
                        @Override public T submit(ActionCommand command) throws IOException {
                            requireNoRefresh(command); requireInstalled(); requireCommand(command);
                            return result.present(coordinator.execute(same, command), archive.withSession(same), same);
                        }
                        @Override public T reconcile(String actionId, org.xar.ck3.control.contracts.ExactRef reference) throws IOException {
                            ActionReceipt original = requireOriginalPublicReconciliation(same, actionId, reference);
                            requireNoRefresh(original.command());
                            return result.present(coordinator.reconcile(same, actionId), archive.withSession(same), same);
                        }
                        @Override public T retain(T actualResult) { return actualResult; }
                    });
                } catch (IOException | RuntimeException | Error failure) {
                    originalFailure = failure; throw failure;
                } finally {
                    try { readCompletion.flushInSession(same); }
                    catch (IOException | RuntimeException publicationFailure) {
                        if (originalFailure != null) { if (publicationFailure != originalFailure) originalFailure.addSuppressed(publicationFailure); }
                        else throw publicationFailure;
                    }
                }
            });
        } finally { calls.unlock(); }
    }
    /** Clears only the caller's retained choice DATA while the original Root call lock is still held. */
    public <T>T executePublicDecision(Instant deadline,PublicDecisionPreparation<T> preparation,PublicActionResult<T> result,
            Runnable dataCleanup)throws IOException,InterruptedException {
        Objects.requireNonNull(dataCleanup);calls.lockInterruptibly();Throwable originalFailure=null;
        try {return executePublicDecision(deadline,preparation,result);}
        catch(IOException|InterruptedException|RuntimeException|Error failure){originalFailure=failure;throw failure;}
        finally {
            try {dataCleanup.run();}
            catch(RuntimeException|Error cleanupFailure){
                if(originalFailure!=null){if(cleanupFailure!=originalFailure)originalFailure.addSuppressed(cleanupFailure);}
                else throw cleanupFailure;
            }finally{calls.unlock();}
        }
    }
    private ActionReceipt requireOriginalPublicReconciliation(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            String actionId, org.xar.ck3.control.contracts.ExactRef reference) throws IOException {
        writer.requireSession(same); var scoped = archive.withSession(same);
        ActionReceipt original = ContinuityActionJournal.lookup(same.head().state(), actionId, scoped)
                .orElseThrow(() -> new IOException("original public reconciliation intent is absent from the actual canonical writer"));
        StrictJson.require(original.command().sessionId().equals(identity().sessionId())
                && original.command().origin().game().equals(identity().game())
                && original.command().origin().machineId().equals(identity().machineId())
                && scoped.receiptReferenceOf(original).equals(reference) && scoped.loadReceipt(reference).equals(original),
                "public reconciliation must retain its exact canonical original Game/session/receipt without rebuilding a command");
        return original;
    }
    /** Captures the real public command, leaves its Driver freeze, publishes actual READs, and submits only through the sole coordinator. */
    public ActionReceipt executePublicAction(Instant deadline, PublicActionPreparation preparation) throws IOException, InterruptedException {
        return executePublicAction(deadline, preparation, (actual, scoped, same) -> actual);
    }
    /** Encoding runs after the one actual execution while its original archive/writer scope remains held. An encoding failure never repeats it. */
    public <T> T executePublicAction(Instant deadline, PublicActionPreparation preparation, PublicActionResult<T> result) throws IOException, InterruptedException {
        Objects.requireNonNull(preparation);
        return executePreparedPublicAction(deadline, same -> readiness.currentOwned(same, identity(), deadline, lease -> {
            ActionCommand actual = Objects.requireNonNull(preparation.prepare(lease.frame(), lease.driver(), same));
            requirePublicCommand(actual, lease.frame(), deadline);
            return actual;
        }), result);
    }
    @FunctionalInterface public interface PublicPlanningWork<T> {
        T read(org.xar.ck3.control.application.readiness.NativeReadinessCollector.PublicPlanningObservation actual,
                ContinuityStorePort.Session borrowed) throws IOException;
    }
    @FunctionalInterface public interface StandaloneRead<T> {
        T read(ContinuityStorePort.Session borrowed) throws IOException,InterruptedException;
    }
    /** Native diagnostic readers retain the real Root/writer without refreshing a world observation or granting actions. */
    public <T> T withPublicStandaloneRead(Instant deadline,StandaloneRead<T> reader)throws IOException,InterruptedException {
        Objects.requireNonNull(reader);calls.lockInterruptibly();
        try {
            requireOwner();requireDeadline(deadline);
            return owner.withBorrowed(()->{
                var same=owner.activeBorrowedSession();writer.requireSession(same);
                T result=reader.read(same);writer.requireSession(same);requireDeadline(deadline);return result;
            });
        }finally{calls.unlock();}
    }
    @FunctionalInterface public interface PublicSuppliedAction<T> {
        T call()throws IOException,InterruptedException;
    }
    /** Existing supplied services open their own original writer scope under this Root's outer call lock. */
    public <T>T withPublicSuppliedAction(Instant deadline,PublicSuppliedAction<T> action)throws IOException,InterruptedException {
        Objects.requireNonNull(action);calls.lockInterruptibly();Throwable originalFailure=null;boolean entered=false;
        try{requireInstalled();requireDeadline(deadline);entered=true;T result=action.call();requireDeadline(deadline);return result;}
        catch(IOException|InterruptedException|RuntimeException|Error failure){originalFailure=failure;throw failure;}
        finally {
            try{if(entered)owner.withBorrowed(()->{var same=owner.activeBorrowedSession();readCompletion.flushInSession(same);return null;});}
            catch(IOException|InterruptedException|RuntimeException|Error publicationFailure){
                if(originalFailure!=null){if(publicationFailure!=originalFailure)originalFailure.addSuppressed(publicationFailure);}else throw publicationFailure;
            }finally{calls.unlock();}
        }
    }
    /** A standalone read may publish its actual queued READ only after its own held observation scope has ended. */
    public <T>T withPublicStandalonePublication(Instant deadline,StandaloneRead<T> reader)throws IOException,InterruptedException {
        Objects.requireNonNull(reader);
        return withPublicStandaloneRead(deadline,same->{
            Throwable originalFailure=null;
            try{return reader.read(same);}
            catch(IOException|InterruptedException|RuntimeException|Error failure){originalFailure=failure;throw failure;}
            finally {
                try{readCompletion.flushInSession(same);}
                catch(IOException|RuntimeException|Error publicationFailure){
                    if(originalFailure!=null){if(publicationFailure!=originalFailure)originalFailure.addSuppressed(publicationFailure);}else throw publicationFailure;
                }
            }
        });
    }
    /** The complete planning producer is captured once; any actual READ publication flushes after its scope ends. */
    public <T> T withPublicPlanning(Instant deadline, PublicPlanningWork<T> work) throws IOException, InterruptedException {
        Objects.requireNonNull(work);calls.lockInterruptibly();
        try {
            requireInstalled();requireDeadline(deadline);
            prepareTransportContinuity(deadline);
            return owner.withBorrowed(()->{
                var same=owner.activeBorrowedSession();Throwable originalFailure=null;
                try {
                    return readiness.withOwnedPublicPlanning(same,identity(),deadline,actual->{
                        requireDeadline(deadline);actual.assertCurrent(same);
                        T result=work.read(actual,same);
                        actual.assertCurrent(same);requireDeadline(deadline);return result;
                    });
                } catch(IOException|RuntimeException|Error failure){originalFailure=failure;throw failure;}
                finally {
                    try{readCompletion.flushInSession(same);}
                    catch(IOException|RuntimeException cleanup){if(originalFailure!=null)originalFailure.addSuppressed(cleanup);else throw cleanup;}
                }
            });
        } finally{calls.unlock();}
    }
    /** Event and policy-dependent public actions consume the collector's actual complete planning request in its original lease. */
    public ActionReceipt executePublicPlanningAction(Instant deadline, PublicPlanningActionPreparation preparation)
            throws IOException, InterruptedException {
        return executePublicPlanningAction(deadline, preparation, (actual, scoped, same) -> actual);
    }
    public <T> T executePublicPlanningAction(Instant deadline, PublicPlanningActionPreparation preparation,
            PublicActionResult<T> result) throws IOException, InterruptedException {
        Objects.requireNonNull(preparation);
        return executePreparedPublicAction(deadline, same -> readiness.withOwnedPlanning(same, identity(), deadline, (original, lease) -> {
            StrictJson.require(original.before().equals(lease.frame().identity())
                    && original.source().equals(lease.frame().source())
                    && original.sessionId().equals(lease.frame().sessionId())
                    && !original.deadline().isAfter(deadline),
                    "public preparation requires the collector's same complete planning request and lease");
            ActionCommand actual = Objects.requireNonNull(preparation.prepare(original, lease.frame(), lease.driver(), same));
            requirePublicCommand(actual, lease.frame(), original.deadline());
            return actual;
        }), result);
    }
    private void requirePublicCommand(ActionCommand actual,
            org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame, Instant deadline) throws IOException {
        StrictJson.require(actual.origin() instanceof CommandOrigin.Gameplay
                && actual.before().equals(frame.identity()) && actual.source().equals(frame.source())
                && actual.sessionId().equals(frame.sessionId()) && !actual.deadline().isAfter(deadline),
                "public action must retain the exact actual captured origin, source, session and caller deadline");
        requireCommand(actual);
    }
    private <T> T executePreparedPublicAction(Instant deadline, PublicActionScope preparation, PublicActionResult<T> result)
            throws IOException, InterruptedException {
        Objects.requireNonNull(deadline); Objects.requireNonNull(preparation); Objects.requireNonNull(result); calls.lockInterruptibly();
        try {
            requireInstalled(); requireDeadline(deadline);
            prepareTransportContinuity(deadline);
            return owner.withBorrowed(() -> {
                var same = owner.activeBorrowedSession(); Throwable originalFailure = null;
                try {
                    ActionCommand command = preparation.prepare(same);
                    var published = readCompletion.flushInSession(same);
                    if (published.isPresent()) throw new org.xar.ck3.control.application.session.ReadPublicationRefreshException(command,
                            Optional.empty(), published.orElseThrow(), Optional.empty());
                    ActionReceipt actual = coordinator.execute(same, command);
                    return result.present(actual, archive.withSession(same), same);
                } catch (IOException | RuntimeException | Error failure) {
                    originalFailure = failure; throw failure;
                } finally {
                    // The preparation callback has unwound every physical/Driver freeze before this actual same-Session flush.
                    try { readCompletion.flushInSession(same); }
                    catch (IOException | RuntimeException publicationFailure) {
                        if (originalFailure != null) { if (publicationFailure != originalFailure) originalFailure.addSuppressed(publicationFailure); }
                        else throw publicationFailure;
                    }
                }
            });
        } finally { calls.unlock(); }
    }

    /** Binds the host; each actual business turn obtains its own current full observation before planning. */
    public void install(OrdinarySessionHost host, Instant deadline) throws IOException, InterruptedException {
        Objects.requireNonNull(host); calls.lockInterruptibly();
        try {
            StrictJson.require(restoration == null && nextEpisode == null && installedHost == null && !controller.isRetired() && !controller.isRunning(), "initial Root session already installed, retired or requires actual successor publication");
            requireDeadline(deadline);
            game.verify();
            host.install(controller);
            installedHost = host;
            host.bindRoot(owner.sessionAccess());
            prepareTransportContinuity(deadline);
        } finally {
            calls.unlock();
        }
    }
    /** Publish the retained actual restore once; an uncertain rebind is never repeated as another transaction. */
    public void publishRestored(Instant deadline) throws IOException, InterruptedException {
        if (restoration == null) throw new IOException("this owner was not minted from an actual restored Driver");
        RootApplicationSession previous = restoration.previous(); previous.calls.lockInterruptibly();
        try {
            calls.lockInterruptibly();
            try {
                requireDeadline(deadline);
                StrictJson.require(installedHost == null && previous.owner == owner && previous.writer == writer
                        && previous.archive == archive && previous.submissions == submissions && previous.savedLoader == savedLoader
                        && previous.cycles == cycles && previous.installedHost != null && previous.controller.isRetired()
                        && !previous.controller.isRunning() && !controller.isRunning() && !controller.isRetired() && !controller.isQuarantined(),
                        "actual retired predecessor, identical Root custody and idle successor are required");
                synchronized(owner){owner.requireRestorePublication(previous,this);}
                if(rebound==null){
                    owner.captureRestoredFirstKernel(this,deadline);
                    writer.locked(same->{owner.initializeRestoredDomains(same,this,deadline);return null;});
                }
                if (rebound == null) {
                    if (rebindAttempted) throw new IOException("original restored-cycle rebind returned without an admission; inspect its original durable outcome, never replay it");
                    rebindAttempted = true;
                    rebound = batchJournal.rebindAfterDomainImports(restoration.service(), restoration.binding());
                }
                ContinuityBatchJournal.ReboundCycle actualRebound = rebound;
                OrdinarySessionHost host=previous.installedHost;
                writer.locked(same->{owner.warmRestoredCheckpoint(same,this,deadline);return null;});
                writer.locked(borrowed -> readiness.currentOwned(borrowed, identity(), deadline, lease -> {
                    requireDeadline(deadline); batchJournal.requireCurrent(borrowed, actualRebound);
                    StrictJson.require(lease.frame().sessionId().equals(identity().sessionId())
                            && lease.frame().identity().game().equals(identity().game()), "restored publication source scope crossed actual physical owner");
                    synchronized (owner) {
                        owner.requireRestorePublication(previous, this);
                        submissions.publishRestored(borrowed, previous.authorityView, authorityView, restoration.binding(), actualRebound,
                                host, previous.controller, controller, savedLoader, previous.ownSavedLoader, ownSavedLoader,
                                owner.readHistoryAuthority(),previous.readHistory,readHistory);
                        installedHost = host; owner.publishRestored(previous, this);
                    }
                    return true;
                }));
                prepareTransportContinuity(deadline);
            } finally { calls.unlock(); }
        } finally { previous.calls.unlock(); }
    }
    /** Metadata continuity is installed only after actual Host publication and before a Controller turn. */
    private void prepareTransportContinuity(Instant deadline)throws IOException,InterruptedException {
        requireInstalled();requireDeadline(deadline);
        StrictJson.require(!controller.isRunning()&&!controller.isRetired(),"transport continuity requires the actual idle current Controller");
        owner.withBorrowed(()->{
            var same=owner.activeBorrowedSession();writer.requireSession(same);
            var actual=resourceCatalog.remainingDomains().lifecycle();actual.installTransportContinuity(same);
            // New-Game restore/NEXT use their original distinct private adoption; this source is only same-Game transport continuity.
            if(restoration==null&&nextEpisode==null)actual.rebindPendingTransport(same,identity(),deadline);
            return null;
        });
    }
    /** A failed transport entry still drains the identical Controller's retained incident DATA once. */
    private void prepareTransportBeforeController(Instant deadline)throws IOException,InterruptedException {
        try {prepareTransportContinuity(deadline);}
        catch(IOException|InterruptedException|RuntimeException|Error failure) {
            try {controller.enqueueRetainedIncidentData();}
            catch(IOException|RuntimeException|Error completionFailure) {
                if(completionFailure!=failure)failure.addSuppressed(completionFailure);
            }
            throw failure;
        }
    }
    public BatchReport batch(BatchLimits limits)throws IOException,InterruptedException {
        Objects.requireNonNull(limits);calls.lockInterruptibly();
        try {
            requireOwner();requireNoPendingCheckpointAdoption();Instant deadline=clock.instant().plus(limits.wallTime());
            prepareTransportBeforeController(deadline);
            BatchReport actual=controller.runBatch(limits);
            owner.afterTurn(this,actual,deadline);return actual;
        }finally{calls.unlock();}
    }
    /** Clean same-Game worker restart only. Drains actual analysis before entering the original writer scope. */
    public ContinuityBatchJournal.CleanRestartTicket captureCleanRestart(String batchPrefix,long nextSequence,Instant deadline)
            throws IOException,InterruptedException {
        calls.lockInterruptibly();
        try {
            requireOwner();requireNoPendingCheckpointAdoption();requireDeadline(deadline);
            controller.drainForCleanRestart(deadline);
            return owner.withBorrowed(()->controller.captureCleanRestart(owner.activeBorrowedSession(),batchPrefix,nextSequence));
        } finally {calls.unlock();}
    }
    /** Actual clean Driver/new HELLO adoption precedes this one restoration of the original Controller counters. */
    public void restoreCleanRestart(ContinuityBatchJournal.CleanRestartAdmission actual)throws IOException,InterruptedException {
        calls.lockInterruptibly();
        try {
            owner.withBorrowed(()->{restoreCleanRestart(owner.activeBorrowedSession(),actual);return null;});
        } finally {calls.unlock();}
    }
    /** Core construction already holds this writer. Never acquire a second byte-zero lock during restoration. */
    public void restoreCleanRestart(ContinuityStorePort.Session same,ContinuityBatchJournal.CleanRestartAdmission actual)throws IOException,InterruptedException {
        calls.lockInterruptibly();
        try {
            writer.requireSession(same);
            owner.requirePublicWork(this);requireNoPendingCheckpointAdoption();
            StrictJson.require(installedHost==null&&!controller.isRetired()&&!controller.isRunning(),"restart DATA requires this actual unused pre-Host Root owner");
            driver.requireCleanRestart(actual);
            StrictJson.require(driver.session().machineId().equals(actual.controller().owner().machineId())
                    &&driver.session().game().equals(actual.controller().owner().game())&&driver.session().sessionId().equals(actual.controller().owner().sessionId()),
                    "clean restart crossed the actual replacement Driver owner");
            controller.restoreCleanRestart(same,actual);
        } finally {calls.unlock();}
    }
    /** Core holds the original writer while the actual journal repair is consumed before Host installation. */
    public void restoreInitialNoDispatchRecovery(ContinuityStorePort.Session same,
            ContinuityBatchJournal.InitialNoDispatchRecovery actual)throws IOException,InterruptedException {
        calls.lockInterruptibly();
        try {
            writer.requireSession(same);owner.requirePublicWork(this);requireNoPendingCheckpointAdoption();
            StrictJson.require(installedHost==null&&!controller.isRetired()&&!controller.isRunning(),
                    "initial interruption recovery requires the actual unused pre-Host Root owner");
            driver.requireInitialNoDispatchRecovery(actual);
            StrictJson.require(driver.session().machineId().equals(actual.owner().machineId())
                    &&driver.session().game().equals(actual.owner().game())&&driver.session().sessionId().equals(actual.owner().sessionId()),
                    "initial interruption recovery crossed the actual replacement Driver owner");
            controller.restoreInitialNoDispatchRecovery(same,actual);
        } finally {calls.unlock();}
    }


    public SessionController.TurnReport autoTurn(Instant deadline)throws IOException,InterruptedException {
        calls.lockInterruptibly();
        try {
            requireOwner();requireNoPendingCheckpointAdoption();requireDeadline(deadline);prepareTransportBeforeController(deadline);
            var actual=controller.autoTurn(deadline);
            owner.afterTurn(this,actual.execution(),deadline);return actual;
        }finally{calls.unlock();}
    }
    /** The actual Controller consumes only its private pending UI source and finishes the original episode continuation. */
    public SessionController.TurnReport pendingSuccessorUiTurn(Instant deadline)throws IOException,InterruptedException {
        calls.lockInterruptibly();
        try {
            requireOwner();requireNoPendingCheckpointAdoption();requireDeadline(deadline);
            prepareTransportBeforeController(deadline);
            var actual=controller.pendingSuccessorUiTurn(deadline);
            owner.afterTurn(this,actual.execution(),deadline);return actual;
        }finally{calls.unlock();}
    }
    @FunctionalInterface public interface AutoPresentationWork<T> {
        T present(SessionController.TurnReport actual,
                org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known known,
                ActionPorts.OutcomeArchive sameScopedArchive,
                org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed) throws IOException;
    }
    /** Called only by this Core's private NEXT path with the lifecycle issuer's actual retained old terminal facts. */
    void retainNextAutoPresentation(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            ActionReceipt parent, org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known originalFacts) throws IOException {
        writer.requireSession(same);
        if (!autoPresentationActive) return;
        StrictJson.require(calls.isHeldByCurrentThread() && !controller.isRunning() && controller.isRetired()
                && parent.command().origin() instanceof CommandOrigin.LifecycleTerminal
                && parent.command().sessionId().equals(identity().sessionId())
                && parent.command().origin().game().equals(identity().game())
                && parent.state() instanceof ActionState.CompositeSettled settled
                && settled.settlement() instanceof ActionState.LifecycleApplied applied
                && applied.proof().kind() == org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof.Kind.NEXT_EPISODE,
                "only this active AUTO's actual committed NEXT parent can retain old presentation data");
        var before = parent.command().lifecycleBefore();
        StrictJson.require(originalFacts.stamp().game().equals(identity().game())
                && originalFacts.driver().session().bridgePid() == identity().game().pid()
                && before.evidence().originalDriver().bytes() == originalFacts.driver().encode().length
                && before.evidence().originalDriver().sha256().equals(originalFacts.stamp().driverSha256()),
                "retained AUTO facts must be the actual original terminal Driver, not the replacement Game");
        var scoped = archive.withSession(same);
        var reference = scoped.receiptReferenceOf(parent);
        StrictJson.require(scoped.loadReceipt(reference).equals(parent), "retained AUTO requires its exact canonical original receipt");
        RetainedNextAuto actual = new RetainedNextAuto(parent, reference, originalFacts);
        if (retainedNextAuto != null) StrictJson.require(retainedNextAuto.equals(actual), "one AUTO cannot switch its retained NEXT parent or old Driver");
        else retainedNextAuto = actual;
    }
    /** Exactly one actual turn, then the original frozen Driver result; quarantine still permits presenting that outcome. */
    public <T> T autoTurnPresented(Instant deadline, AutoPresentationWork<T> work) throws IOException, InterruptedException {
        Objects.requireNonNull(work); calls.lockInterruptibly();
        try {
            // The actual Controller alone admits its private pending-UI continuation before the ordinary quarantine gate.
            requireOwner(); requireNoPendingCheckpointAdoption(); requireDeadline(deadline);
            StrictJson.require(!autoPresentationActive, "one actual AUTO presentation may enter this Root at a time");
            prepareTransportBeforeController(deadline);
            autoPresentationActive = true; retainedNextAuto = null;
            resourceCatalog.additionalDomains().gui().automaticCamera().begin();
            SessionController.TurnReport actual = controller.autoTurn(deadline);
            owner.afterTurn(this,actual.execution(),deadline);
            if(!controller.isRetired())writer.locked(same->{
                var known=driver.authority().withFrozenFacts(same,frozen->frozen.state());
                if(known instanceof org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known complete)
                    resourceCatalog.additionalDomains().gui().automaticCamera().afterTurn(same,complete,deadline);
                return true;
            });
            RetainedNextAuto retained = retainedNextAuto;
            if (retained != null) return writer.locked(borrowed -> {
                var report = actual.execution(); var scoped = archive.withSession(borrowed);
                StrictJson.require(report.session().equals(identity()) && report.terminal() == BatchReport.Terminal.EPISODE_HANDOFF
                        && report.lifecycleTurns().size() == 1 && report.turns().isEmpty() && report.reconciliations().isEmpty()
                        && report.readPublicationReconciliations().isEmpty()
                        && scoped.receiptReferenceOf(report.lifecycleTurns().getFirst().receipt()).equals(retained.parentReference())
                        && scoped.loadReceipt(retained.parentReference()).equals(retained.parent()),
                        "retired AUTO presentation must retain the original one NEXT report and receipt ancestry");
                return work.present(actual, retained.originalFacts(), scoped, borrowed);
            });
            return writer.locked(borrowed -> driver.authority().withFrozenFacts(borrowed, frozen -> {
                requireOwner();
                if (!(frozen.state() instanceof org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known known))
                    throw new IOException("actual Driver is incomplete after the original turn; no action replay");
                return work.present(actual, known, archive.withSession(borrowed), borrowed);
            }));
        } finally { resourceCatalog.additionalDomains().gui().automaticCamera().end(); autoPresentationActive = false; calls.unlock(); }
    }
    @Override public ActionReceipt execute(ActionCommand command) {
        calls.lock(); try {
            if(plannedCheckpoints.containsKey(command.actionId())){
                try{return owner.withBorrowed(()->executePlannedCheckpoint(owner.activeBorrowedSession(),command,false));}
                catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
                catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IllegalStateException("planned SAVE interrupted; original request retained",interrupted);}
            }
            requireInstalled(); requireCommand(command); return coordinator.execute(command);
        } finally { calls.unlock(); }
    }
    @Override public ActionReceipt execute(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed, ActionCommand command) {
        calls.lock(); try {
            if(plannedCheckpoints.containsKey(command.actionId()))return executePlannedCheckpoint(borrowed,command,false);
            requireInstalled(); requireCommand(command); writer.requireSession(borrowed); return coordinator.execute(borrowed, command);
        } catch (IOException failure) { throw new java.io.UncheckedIOException(failure); }
        catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IllegalStateException("planned SAVE interrupted; original request retained",interrupted);}
        finally { calls.unlock(); }
    }
    @Override public ActionReceipt reconcile(String actionId) {
        calls.lock(); try {
            requireOwner();var held=plannedCheckpoints.get(actionId);
            if(held!=null){
                try{return owner.withBorrowed(()->executePlannedCheckpoint(owner.activeBorrowedSession(),held.original.command(),true));}
                catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
                catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IllegalStateException("original planned SAVE query interrupted; no replay",interrupted);}
            }
            return coordinator.reconcile(actionId); }
        finally { calls.unlock(); }
    }
    @Override public ActionReceipt reconcile(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed, String actionId) {
        calls.lock(); try {
            requireOwner();writer.requireSession(borrowed);var held=plannedCheckpoints.get(actionId);
            if(held!=null)return executePlannedCheckpoint(borrowed,held.original.command(),true);
            return coordinator.reconcile(borrowed, actionId); }
        catch (IOException failure) { throw new java.io.UncheckedIOException(failure); }
        catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IllegalStateException("original planned SAVE query interrupted; no replay",interrupted);}
        finally { calls.unlock(); }
    }
    /** Uses only this Root call's existing ordinary observation lease and original borrowed writer.
     * The outer observation scope publishes queued reads after its freeze ends. */
    public <T> PlanningReadResult<T> read(ContinuityStorePort.Session same,ReadContract<T> identical,
            PlanningReadRequest actual)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(identical);Objects.requireNonNull(actual);
        if(!calls.isHeldByCurrentThread())throw new IOException("borrowed public read requires the original active Root call");
        requireOwner();writer.requireSession(same);requireDeadline(actual.deadline());
        if(owner.activeBorrowedSession()!=same)throw new IOException("borrowed public read escaped its original Core writer");
        StrictJson.require(actual.origin() instanceof CommandOrigin.Gameplay
                &&actual.origin().game().equals(identity().game())
                &&actual.sessionId().equals(identity().sessionId())
                &&resourceCatalog!=null&&resourceCatalog.context().actions()==this
                &&actual.source().equals(resourceCatalog.context().source())
                &&identical.operation().equals(actual.operation()),
                "borrowed ordinary read crossed its actual Root/source/session/operation");
        return readiness.currentHeldRead(same,actual,lease->queries.read(same,identical,actual));
    }
    public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) throws IOException {
        calls.lock(); try {
            requireInstalled(); requireDeadline(request.deadline());
            StrictJson.require(request.sessionId().equals(identity().sessionId()) && request.origin().game().equals(identity().game()), "public read crossed owned session");
            try {
                return owner.journal().locked(locked->{
                    var borrowed=locked.writerSession();var result=queries.read(borrowed,contract,request);
                    try{readCompletion.flushInSession(borrowed);}catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
                    return result;
                });
            }catch(java.io.UncheckedIOException failure){throw failure.getCause();}
        } finally { calls.unlock(); }
    }
    /** A registered source may finish only its original pending parent; generic reconciliation remains read-only. */
    @Override public CompositeContinuationReport continueOriginalComposite(CompositeContinuationToken token)throws IOException {
        calls.lock();
        try {requireOwnedContinuation(token);return coordinator.continueOriginalComposite(token);}
        finally {calls.unlock();}
    }
    @Override public CompositeContinuationReport continueOriginalComposite(ContinuityStorePort.Session same,CompositeContinuationToken token)throws IOException {
        calls.lock();
        try {writer.requireSession(same);requireOwnedContinuation(token);return coordinator.continueOriginalComposite(same,token);}
        finally {calls.unlock();}
    }
    private void requireOwnedContinuation(CompositeContinuationToken token){
        requireOwner();Objects.requireNonNull(token);requireDeadline(token.deadline());var parent=Objects.requireNonNull(token.originalParent());
        StrictJson.require(parent.origin() instanceof CommandOrigin.LifecycleTerminal&&parent.operation().value().equals("continue-as-reconciled-successor")
                &&parent.origin().machineId().equals(identity().machineId())&&parent.origin().game().equals(identity().game())
                &&parent.sessionId().equals(identity().sessionId()),"continuation crossed its original terminal Continue parent or owned Game/session");
    }
    public void requestStop() { controller.requestStop(); }
    /** Physical Game cleanup is owned by ManagedGameSession; retirement only revokes this application owner. */
    public void retire() {
        calls.lock();
        try {
            StrictJson.require(installedHost!=null&&installedHost.current().orElseThrow()==controller&&!controller.isRetired()&&!controller.isRunning(),
                    "only the actual installed original controller can retire its public Host");
            try {closeResourcesForRetirement();}
            catch(IOException failure){throw new java.io.UncheckedIOException("actual per-Game resource disposal failed",failure);}
            finally {installedHost.retire(controller);}
        }finally {calls.unlock();}
    }
    /** Cleanup retains archive/writer custody and supplies no normal-exit evidence or Game termination permission. */
    void closeResourcesForRetirement()throws IOException {
        calls.lock();
        try {owner.releaseCatalogResources(resourceCatalog);}
        finally {calls.unlock();}
    }
    private void requireInstalled() {
        requireOwner();requireNoPendingCheckpointAdoption(); StrictJson.require(!controller.isQuarantined(), "original ordinary session is quarantined; read-only original reconciliation is required");
    }
    private void requireNoPendingCheckpointAdoption() {
        StrictJson.require((capturedPublicSave==null||publicSaveControllerAdopted)
                &&plannedCheckpoints.values().stream().noneMatch(held->held.captured!=null&&!held.controllerAdopted),
                "original confirmed SAVE still awaits its private Controller adoption; query that original SAVE before new work");
    }
    private void requireOwner() {
        owner.requirePublicWork(this);
        StrictJson.require(installedHost != null && installedHost.current().orElseThrow() == controller
                && !controller.isRetired(), "original installed session authority is unavailable or retired");
    }
    private void requireCommand(ActionCommand command) {
        Objects.requireNonNull(command); requireDeadline(command.deadline());
        StrictJson.require(command.sessionId().equals(identity().sessionId()) && command.origin().game().equals(identity().game())
                && command.origin().machineId().equals(identity().machineId()), "action crossed owned Root Game/session");
    }
    private void requireDeadline(Instant deadline) { StrictJson.require(clock.instant().isBefore(Objects.requireNonNull(deadline)), "Root request deadline expired"); }
}

