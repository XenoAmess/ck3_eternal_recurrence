package org.xar.ck3.control.application.session;

import java.io.IOException;
import org.xar.ck3.control.application.checkpoint.PublicCheckpointMaterialCapture.Captured;
import java.util.Objects;
import java.util.Optional;
import java.time.Instant;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.RestoreBinding;
import org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs;
import org.xar.ck3.control.application.lifecycle.LifecycleHistoricalPublication;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.application.session.SessionPorts.*;

/** Borrow the original writer session for both actual validation and durable mutation. */
public final class ContinuityBatchJournal implements BatchJournal {
    private final ContinuityStorePort store;
    private final OrdinaryCycleTransitions transitions;
    public ContinuityBatchJournal(ContinuityStorePort store, OrdinaryCycleTransitions transitions) {
        this.store = Objects.requireNonNull(store); this.transitions = Objects.requireNonNull(transitions);
    }
    /** Object identity only: a matching lock path or constructor value cannot replace this original writer. */
    public void requireStore(ContinuityStorePort expected) {
        StrictJson.require(store==Objects.requireNonNull(expected),"batch journal belongs to another actual writer store");
    }
    /** Only this journal can issue the original zero-dispatch interrupted-initial-batch admission. */
    public static final class InitialNoDispatchRecovery {
        private final ContinuityBatchJournal issuer;
        private final SessionIdentity owner;
        private final long sequence;
        private final String digest;
        private final java.util.List<String> consumedBatchIds;
        private final String batchPrefix;
        private final java.util.List<ExactRef> history;
        private final Optional<CleanBatchRestart> capturedManifest;
        private final Optional<ControllerRestartState> capturedController;
        private final Optional<org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known> capturedFacts;
        private final java.util.List<WriterContracts.Pin> capturedPins;
        private final Optional<ContinuityState> capturedFrontier;
        private final boolean openBatch;
        private WriterContracts.HistoricalTransition retainedRecovery;
        private boolean retainedReady;
        private WriterContracts.Receipt interrupted;
        private WriterContracts.Receipt committed;
        private InitialNoDispatchRecovery(ContinuityBatchJournal issuer,ContinuityStorePort.Session same,
                SessionIdentity owner,long sequence,String digest,java.util.List<String> consumedBatchIds,java.util.List<ExactRef> history) {
            this(issuer,same,owner,sequence,digest,consumedBatchIds,history,Optional.empty(),Optional.empty(),Optional.empty(),java.util.List.of(),Optional.empty(),false);
        }
        private InitialNoDispatchRecovery(ContinuityBatchJournal issuer,ContinuityStorePort.Session same,
                SessionIdentity owner,long sequence,String digest,java.util.List<String> consumedBatchIds,java.util.List<ExactRef> history,
                Optional<CleanBatchRestart> capturedManifest,Optional<ControllerRestartState> capturedController,
                Optional<org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known> capturedFacts,java.util.List<WriterContracts.Pin> capturedPins,
                Optional<ContinuityState> capturedFrontier,boolean openBatch) {
            this.issuer=issuer;this.owner=owner;this.sequence=sequence;this.digest=digest;
            this.capturedManifest=capturedManifest;this.capturedController=capturedController;this.capturedFacts=capturedFacts;
            this.capturedPins=java.util.List.copyOf(capturedPins);this.openBatch=openBatch;
            this.capturedFrontier=Objects.requireNonNull(capturedFrontier);
            this.consumedBatchIds=java.util.List.copyOf(consumedBatchIds);
            String first=this.consumedBatchIds.getFirst();this.batchPrefix=capturedController.map(ControllerRestartState::batchPrefix)
                    .orElseGet(()->first.substring(0,first.length()-2));
            this.history=java.util.List.copyOf(history);
        }
        public SessionIdentity owner(){return owner;}
        public String consumedBatchId(){return consumedBatchIds.getLast();}
        public java.util.List<String> consumedBatchIds(){return consumedBatchIds;}
        public String batchPrefix(){return batchPrefix;}
        public long nextBatchSequence(){return capturedController.map(captured->Math.addExact(captured.nextBatchSequence(),
                consumedBatchIds.size()-captured.usedBatches().size())).orElse((long)consumedBatchIds.size());}
        boolean fromCapturedRestart(){return capturedFrontier.isPresent();}
        public Optional<CleanBatchRestart> capturedManifest(){return capturedManifest;}
        public Optional<ControllerRestartState> capturedController(){return capturedController;}
        public Optional<org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known> capturedFacts(){return capturedFacts;}
        void requireCapturedCurrentFrame(ObservationIdentity frame) {
            var manifest=capturedManifest.orElseThrow();var facts=capturedFacts.orElseThrow();
            var identity=frame.frame().identity();var session=facts.driver().session();
            StrictJson.require(frame.machineId().equals(owner.machineId())&&frame.game().equals(owner.game())
                    &&identity.player().equals(session.actorId())&&frame.frame().episodeRunId().equals(session.episodeRunId())
                    &&identity.dateRaw().longValueExact()>=manifest.dateRaw()
                    &&identity.nativeRevision().compareTo(manifest.nativeRevision())>=0
                    &&frame.frame().revision().compareTo(manifest.publicRevision())>=0,
                    "captured recovery current observation crossed its actual retained Game/Driver frontier");
        }
        public void requireCurrent(ContinuityStorePort.Session same)throws IOException {
            issuer.store.requireSession(same);
            if(retainedReady)same.requireDomainImportContinuation(sequence,digest);
            else if(committed==null)StrictJson.require(same.head().state().sequence()==sequence()&&same.head().digest().equals(digest()),
                    "initial recovery predecessor changed");
            else same.requireDomainImportContinuation(committed.head().sequence(),ContinuityJson.digest(committed.head().toJson()));
            if(capturedFrontier.isPresent())requireCapturedBusinessUnchanged(capturedFrontier.orElseThrow(),same.head().state());
            for(var pin:capturedPins)same.verifyPin(pin);
        }
        long sequence(){return interrupted==null?sequence:interrupted.head().sequence();}
        String digest(){return interrupted==null?digest:ContinuityJson.digest(interrupted.head().toJson());}
        java.util.List<ExactRef> history(){return history;}
    }
    private static void requireCapturedBusinessUnchanged(ContinuityState captured,ContinuityState current) {
        StrictJson.require(captured.settledCycles()==current.settledCycles()&&captured.settledDateRaw()==current.settledDateRaw(),
                "zero-dispatch suffix cannot change captured saved progress");
        var before=captured.toJson();var after=current.toJson();
        var fields=new java.util.ArrayList<>(WriterContracts.PRESERVED_RUNTIME_FIELDS);
        fields.addAll(java.util.List.of(WriterContracts.ORDINARY_CYCLE_FIELD,WriterContracts.ORDINARY_CYCLE_REBIND_FIELD,
                WriterContracts.ORDINARY_SAVED_CYCLE_FIELD,WriterContracts.DRIVER_ACTION_HISTORY_FIELD,
                WriterContracts.DRIVER_READ_HISTORY_FIELD,WriterContracts.ACTION_LIFECYCLE_FIELD,
                WriterContracts.DRIVER_HISTORY_BASELINE_FIELD,WriterContracts.GAMEPLAY_ENTRY_FIELD));
        for(String field:fields)StrictJson.require(before.has(field)==after.has(field)
                &&(!before.has(field)||ContinuityJson.same(before.get(field),after.get(field))),
                "zero-dispatch suffix changed captured business state: "+field);
    }
    /** Only a real canonical capture can provide a post-restart baseline; the pointer file grants no admission. */
    private Optional<InitialNoDispatchRecovery> admitCapturedNoDispatchRecovery(ContinuityStorePort.Session same,SessionIdentity owner,WriterContracts.Head head)throws IOException {
        var state=head.state();var whole=state.toJson();
        var pins=new java.util.TreeMap<Long,WriterContracts.Pin>();
        var directory=java.nio.file.Path.of(same.persistedHead().path()).toAbsolutePath().normalize().resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS");
        for(var pin:head.documents()) {
            var p=java.nio.file.Path.of(pin.reference().path()).toAbsolutePath().normalize();
            if(p.getParent().equals(directory)&&p.getFileName().toString().matches("[0-9]{8}\\.json"))
                StrictJson.require(pins.putIfAbsent(Long.parseLong(p.getFileName().toString().substring(0,8)),pin)==null,"duplicate actual recovery event");
        }
        StrictJson.require(state.sequence()>=1&&state.sequence()<=4096,"finite canonical recovery history required");
        java.util.List<WriterContracts.Pin> requestedPins = new java.util.ArrayList<>();
        for (long sequence = state.sequence(); sequence >= 1; sequence--) {
            requestedPins.add(Objects.requireNonNull(pins.get(sequence), "missing canonical recovery event"));
        }
        java.util.List<WriterContracts.HistoricalTransition> edges = same.readHistoricalTransitions(requestedPins);
        WriterContracts.HistoricalTransition capture = null;
        var suffix = new java.util.ArrayList<WriterContracts.HistoricalTransition>();
        var history = new java.util.ArrayList<ExactRef>();
        for (int i = 0; i < edges.size(); i++) {
            var edge = edges.get(i);
            var pin = requestedPins.get(i);
            var row = ContinuityJson.parseObject(edge.details(), ContinuityJson.LEDGER_MAX_BYTES);
            if (edge.kind().equals(OrdinaryCycleTransitions.BATCH_KIND) && row.has("boundary")
                    && JournalKind.WORKER_RESTART_CAPTURE.name().equals(StrictJson.text(row.get("boundary")))) {
                capture = edge; history.add(pin.reference()); break;
            }
            suffix.add(edge); history.add(pin.reference());
        }
        if(capture==null)return Optional.empty();
        StrictJson.require(!suffix.isEmpty(),"captured recovery requires an actual unfinished zero-dispatch suffix");
        requireCapturedBusinessUnchanged(capture.after(),state);
        var originals=transitions.restartArchive(same);
        var captureDetails=ContinuityJson.parseObject(capture.details(),ContinuityJson.LEDGER_MAX_BYTES);
        StrictJson.require(OrdinaryCycleTransitions.sessionFromJson(captureDetails.get("session")).equals(owner),"captured recovery crossed owner");
        ExactRef manifestRef=ExactRef.fromJson(captureDetails.get("restart_manifest"));
        byte[] manifestBytes=originals.loadMaterial(manifestRef).bytes();var manifest=CleanBatchRestart.decode(manifestBytes);
        byte[] controllerBytes=originals.loadMaterial(manifest.controller()).bytes();var controller=ControllerRestartState.decode(controllerBytes);
        var knownOriginal=originals.loadFullMaterial(manifest.driverFacts());
        var facts=org.xar.ck3.control.application.driver.DriverSnapshotFacts.decodeKnownOriginal(knownOriginal,Optional.empty());
        byte[] full=originals.loadFullMaterial(manifest.fullDriver()).bytes();
        StrictJson.require(java.util.Arrays.equals(manifestBytes,manifest.encode())&&java.util.Arrays.equals(controllerBytes,controller.encode())
                &&sameKnownRestartOriginal(knownOriginal.bytes(),facts)&&java.util.Arrays.equals(full,facts.driver().encode()),"actual captured originals differ");
        StrictJson.require(controller.owner().equals(owner)&&manifest.previousTransport().game().equals(owner.game())
                &&manifest.previousTransport().machineId().equals(owner.machineId())&&manifest.previousTransport().sessionId().equals(owner.sessionId())
                &&facts.stamp().game().equals(owner.game()),"captured restart owner changed");
        StrictJson.require(!controller.quarantined()&&!controller.localUnresolved()&&!controller.stopRequested(),
                "captured recovery cannot clear unresolved or stopped Controller state");
        transitions.requireCapturedRestartFrame(same,capture.after(),controller,manifest);
        StrictJson.require(facts.originalHistoryBasis().equals(ExactRef.fromJson(whole.get(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD))),"captured original history basis is no longer the actual baseline");
        StrictJson.safe(controller.nextBatchSequence(),0);
        var used=new java.util.ArrayList<String>(controller.usedBatches().stream().sorted().toList());int capturedCount=used.size();
        java.util.Collections.reverse(suffix);String previous=ContinuityJson.digest(capture.after().toJson());String batch=null;int phase=1;boolean deferredClosed=false;WriterContracts.HistoricalTransition retained=null;
        same.requireHistoricalHead(capture.sequence(),previous);
        for(var edge:suffix) {
            StrictJson.require(ContinuityJson.digest(edge.before().toJson()).equals(previous),"captured suffix ancestry changed");
            var details=ContinuityJson.parseObject(edge.details(),ContinuityJson.LEDGER_MAX_BYTES);
            if(phase==3&&edge.kind().equals(OrdinaryCycleTransitions.CYCLE_KIND)) {
                transitions.requireInitialNoDispatchHistoryEdge(edge,owner,batch,controller.nextBatchSequence()+used.size()-capturedCount);retained=edge;deferredClosed=false;phase=1;
            }else if(phase==1&&edge.kind().equals(org.xar.ck3.control.continuity.writer.DomainBodies.IMPORT_KIND)) {
                // Real historical import is retained; no replayed publication is produced.
            }else {
                StrictJson.require(edge.kind().equals(OrdinaryCycleTransitions.BATCH_KIND)&&(phase==1||phase==2),"captured recovery refuses action/read/SAVE or unrelated suffix");
                var boundary=StrictJson.text(details.get("boundary"));
                StrictJson.require((phase==1?JournalKind.BATCH_STARTED.name().equals(boundary)
                        :java.util.Set.of(JournalKind.BATCH_INTERRUPTED.name(),JournalKind.BATCH_DEFERRED.name()).contains(boundary))&&details.get("checkpoint_pair").isNull()
                        &&details.get("completed_cycle_proof").isNull()&&OrdinaryCycleTransitions.sessionFromJson(details.get("session")).equals(owner),"captured suffix has another batch owner or credit");
                String actual=StrictJson.text(details.get("batch_id"));
                if(phase==1){StrictJson.require(actual.equals(controller.batchPrefix()+"-"+(controller.nextBatchSequence()+used.size()-capturedCount))&&!used.contains(actual),"captured suffix skips or reuses a batch");batch=actual;retained=null;deferredClosed=false;phase=2;}
                else {StrictJson.require(actual.equals(batch),"captured terminal batch differs");used.add(actual);
                    deferredClosed=JournalKind.BATCH_DEFERRED.name().equals(boundary);phase=deferredClosed?1:3;}
            }
            previous=ContinuityJson.digest(edge.after().toJson());
        }
        StrictJson.require(head.digest().equals(previous)&&(phase==2&&state.status()==ContinuityState.Status.RUNNING
                ||phase==3&&state.status()==ContinuityState.Status.REPAIR_REQUIRED
                ||phase==1&&(retained!=null||deferredClosed)&&state.status()==ContinuityState.Status.RUNNING),"actual captured open/interrupted suffix required");
        boolean open=phase==2;if(open)used.add(batch);
        var originalPins=new java.util.ArrayList<WriterContracts.Pin>();for(var ref:java.util.List.of(manifestRef,manifest.controller(),manifest.driverFacts(),manifest.fullDriver()))
            originalPins.add(same.capturePin(ref,WriterContracts.MAX_PIN_BYTES));
        var result=new InitialNoDispatchRecovery(this,same,owner,state.sequence(),head.digest(),used,history,
                Optional.of(manifest),Optional.of(controller),Optional.of(facts),originalPins,Optional.of(capture.after()),open);
        result.retainedRecovery=retained;return Optional.of(result);
    }

    public InitialNoDispatchRecovery admitInitialNoDispatchRecovery(ContinuityStorePort.Session same,SessionIdentity owner)throws IOException {
        store.requireSession(same);Objects.requireNonNull(owner);
        return transitions.withLocked(same,()->{
            var head=same.head();var state=head.state();var whole=state.toJson();
            var captured=admitCapturedNoDispatchRecovery(same,owner,head);if(captured.isPresent())return captured.orElseThrow();
            StrictJson.require(state.status()==ContinuityState.Status.REPAIR_REQUIRED&&state.settledCycles()==0
                    &&state.settledDateRaw()==state.origin().startDateRaw(),"only an interrupted initial zero-credit batch may recover");
            var entry=org.xar.ck3.control.continuity.ObservedGameplayEntry.decode(whole.get(WriterContracts.GAMEPLAY_ENTRY_FIELD));
            StrictJson.require(entry.machineId().equals(owner.machineId())&&entry.game().equals(owner.game())
                    &&entry.sessionId().equals(owner.sessionId())&&entry.dateRaw()==state.settledDateRaw()
                    &&entry.fullDriver().equals(ExactRef.fromJson(whole.get(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD))),
                    "initial recovery crossed its actual entry owner/Driver/date");
            for(String field:java.util.List.of(WriterContracts.ORDINARY_CYCLE_FIELD,WriterContracts.ORDINARY_CYCLE_REBIND_FIELD,
                    WriterContracts.ORDINARY_SAVED_CYCLE_FIELD,WriterContracts.DRIVER_ACTION_HISTORY_FIELD,WriterContracts.DRIVER_READ_HISTORY_FIELD))
                StrictJson.require(!whole.has(field),"initial recovery cannot rewind canonical business publication: "+field);
            for(String field:WriterContracts.PRESERVED_RUNTIME_FIELDS)if(whole.has(field))
                StrictJson.require(whole.get(field).isNull()||whole.get(field).isContainerNode()&&whole.get(field).isEmpty(),
                        "initial recovery cannot discard pending/UNKNOWN: "+field);
            var originals=transitions.restartArchive(same);
            StrictJson.require(org.xar.ck3.control.application.action.ContinuityActionJournal.receipts(state,originals).isEmpty(),
                    "initial recovery cannot discard an actual canonical action");
            var driver=org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.decodeComplete(originals.loadFullMaterial(entry.fullDriver()).bytes());
            StrictJson.require(driver.commandHistory().isEmpty()&&driver.lastCheckpoint() instanceof org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.NullValue
                    &&driver.managedRestoreTransaction() instanceof org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.NullValue
                    &&driver.successionExpectation() instanceof org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.NullValue,
                    "initial recovery cannot reset actual Driver history/checkpoint/continuation");
            var events=java.nio.file.Path.of(same.persistedHead().path()).toAbsolutePath().normalize().resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS");
            var pins=new java.util.TreeMap<Long,WriterContracts.Pin>();
            for(var pin:head.documents()){
                var path=java.nio.file.Path.of(pin.reference().path()).toAbsolutePath().normalize();
                if(path.getParent().equals(events)&&path.getFileName().toString().matches("[0-9]{8}\\.json")){
                    long sequence=Long.parseLong(path.getFileName().toString().substring(0,8));
                    StrictJson.require(pins.putIfAbsent(sequence,pin)==null,"duplicate canonical event sequence");
                }
            }
            StrictJson.require(state.sequence()>=3&&state.sequence()<=4096&&pins.size()==state.sequence(),"complete finite initial recovery history required");
            var requestedPins=new java.util.ArrayList<WriterContracts.Pin>();
            for(long sequence=1;sequence<=state.sequence();sequence++)
                requestedPins.add(Objects.requireNonNull(pins.get(sequence),"missing canonical event"));
            var edges=same.readHistoricalTransitions(requestedPins);
            String batch=null;String prefix=null;String previous=null;int phase=0;var history=new java.util.ArrayList<ExactRef>();
            var consumed=new java.util.ArrayList<String>();
            for(int i=0;i<edges.size();i++){
                long sequence=i+1L;var pin=requestedPins.get(i);
                var edge=edges.get(i);var details=ContinuityJson.parseObject(edge.details(),ContinuityJson.LEDGER_MAX_BYTES);
                StrictJson.require(edge.sequence()==sequence&&(previous==null||ContinuityJson.digest(edge.before().toJson()).equals(previous)),
                        "initial recovery canonical ancestry differs");
                if(sequence==1){StrictJson.require(edge.kind().equals(org.xar.ck3.control.continuity.ObservedGameplayEntry.KIND)
                            &&ContinuityJson.same(details,entry.toJson()),"actual first observed entry required");phase=1;}
                else if(phase==1&&edge.kind().equals(org.xar.ck3.control.continuity.writer.DomainBodies.IMPORT_KIND)){
                    // Historical reader validates the actual canonical edge; no new import is produced here.
                }else if(phase==3&&edge.kind().equals(OrdinaryCycleTransitions.CYCLE_KIND)){
                    transitions.requireInitialNoDispatchHistoryEdge(edge,owner,batch,consumed.size());
                    phase=1;
                }else{
                    StrictJson.require(edge.kind().equals(OrdinaryCycleTransitions.BATCH_KIND)&&(phase==1||phase==2),
                            "initial recovery refuses action/read/SAVE/cycle or a later mutation");
                    var expected=phase==1?JournalKind.BATCH_STARTED:JournalKind.BATCH_INTERRUPTED;
                    StrictJson.require(expected.name().equals(StrictJson.text(details.get("boundary")))
                            &&details.get("checkpoint_pair").isNull()&&details.get("completed_cycle_proof").isNull()
                            &&OrdinaryCycleTransitions.sessionFromJson(details.get("session")).equals(owner),
                            "initial recovery requires the exact failed zero-dispatch batch pair");
                    String actual=StrictJson.text(details.get("batch_id"));
                    if(phase==1){
                        if(prefix==null){StrictJson.require(actual.endsWith("-0")&&actual.length()>2,"initial batch zero identity required");prefix=actual.substring(0,actual.length()-2);}
                        StrictJson.require(actual.equals(prefix+"-"+consumed.size()),"initial failed batches must form the actual contiguous prefix");
                        batch=actual;phase=2;
                    }else {StrictJson.require(actual.equals(batch),"interrupted batch suffix changed");consumed.add(actual);phase=3;}
                }
                previous=ContinuityJson.digest(edge.after().toJson());history.add(pin.reference());
            }
            StrictJson.require(phase==3&&head.digest().equals(previous),"actual interrupted canonical suffix required");
            same.requireHistoricalHead(state.sequence(),head.digest());
            return new InitialNoDispatchRecovery(this,same,owner,state.sequence(),head.digest(),consumed,history);
        });
    }
    /** Finish this process's restoration, retaining an already committed recovery without another ledger mutation. */
    public void finishInitialNoDispatchRecovery(ContinuityStorePort.Session same,InitialNoDispatchRecovery actual,
            SemanticEvidence current)throws IOException {
        store.requireSession(same);StrictJson.require(actual!=null&&actual.issuer==this,"original initial recovery journal required");
        Objects.requireNonNull(current);
        if(actual.fromCapturedRestart()&&actual.retainedRecovery==null&&!actual.openBatch
                &&same.head().state().status()==ContinuityState.Status.RUNNING) {
            transitions.withLocked(same,()->{actual.requireCurrent(same);actual.requireCapturedCurrentFrame(current.frame());
                StrictJson.require(!actual.retainedReady&&actual.committed==null,"captured closed frontier already consumed");
                actual.retainedReady=true;actual.requireCurrent(same);return null;});return;
        }
        if(actual.retainedRecovery==null){commitInitialNoDispatchRecovery(same,actual,current);return;}
        transitions.withLocked(same,()->{
            actual.requireCurrent(same);StrictJson.require(!actual.retainedReady&&actual.committed==null,"retained recovery already consumed");
            var retained=same.readHistoricalTransition(actual.retainedRecovery.eventPin());
            transitions.requireInitialNoDispatchHistoryEdge(retained,actual.owner(),actual.consumedBatchId(),actual.nextBatchSequence());
            StrictJson.require(retained.sequence()==actual.retainedRecovery.sequence()
                    &&retained.eventIdentity().equals(actual.retainedRecovery.eventIdentity()),"retained recovery event changed");
            same.requireDomainImportContinuation(retained.sequence(),ContinuityJson.digest(retained.after().toJson()));
            var binding=StrictJson.object(same.head().state().toJson().get("latest_binding"),java.util.Set.of(
                    "date_raw","actor_character_id","episode_run_id","snapshot_id","revision","native_revision"));
            var frame=current.frame();var identity=frame.frame().identity();
            if(actual.fromCapturedRestart())actual.requireCapturedCurrentFrame(frame);
            StrictJson.require(frame.machineId().equals(actual.owner().machineId())&&frame.game().equals(actual.owner().game())
                    &&(actual.fromCapturedRestart()?identity.dateRaw().compareTo(binding.get("date_raw").bigIntegerValue())>=0
                        :identity.dateRaw().equals(binding.get("date_raw").bigIntegerValue()))
                    &&identity.player().equals(binding.get("actor_character_id").bigIntegerValue())
                    &&frame.frame().episodeRunId().equals(StrictJson.text(binding.get("episode_run_id")))
                    &&identity.nativeRevision().compareTo(binding.get("native_revision").bigIntegerValue())>=0,
                    "retained recovery current observation crossed its actual settled frontier");
            actual.retainedReady=true;actual.requireCurrent(same);return null;
        });
    }
    public WriterContracts.Receipt commitInitialNoDispatchRecovery(ContinuityStorePort.Session same,InitialNoDispatchRecovery actual,
            SemanticEvidence current)throws IOException {
        store.requireSession(same);StrictJson.require(actual!=null&&actual.issuer==this,"original initial recovery journal required");
        return transitions.withLocked(same,()->{
            actual.requireCurrent(same);StrictJson.require(actual.committed==null,"initial recovery already committed");
            if(actual.openBatch&&actual.interrupted==null) {
                var input=new JournalInput(actual.owner(),actual.consumedBatchId(),JournalKind.BATCH_INTERRUPTED,
                        Optional.empty(),Optional.empty(),Optional.empty(),actual.history());
                var prepared=same.preview(transitions.batchRequest(input));var closed=same.commit(prepared);same.requireCommitted(prepared,closed);
                actual.interrupted=closed;actual.requireCurrent(same);
            }
            var receipt=transitions.commitInitialNoDispatchRecovery(same,actual,current);actual.committed=receipt;
            actual.requireCurrent(same);return receipt;
        });
    }
    void requireInitialNoDispatchRecovery(ContinuityStorePort.Session same,InitialNoDispatchRecovery actual,SessionIdentity expected)throws IOException {
        store.requireSession(same);
        StrictJson.require(actual!=null&&actual.issuer==this&&actual.owner.equals(expected)&&(actual.committed!=null||actual.retainedReady),
                "Controller restore requires this journal's committed initial recovery");actual.requireCurrent(same);
    }

    /** Public serialized DATA; only admitCleanRestart may turn an actual canonical capture into an admission. */
    public record CleanRestartTicket(ExactRef persistedHead,long sequence,String headDigest,ExactRef manifest) {
        private static final java.util.Set<String> FIELDS=java.util.Set.of("schema","persisted_head","sequence","head_digest","manifest");
        public CleanRestartTicket {Objects.requireNonNull(persistedHead);Objects.requireNonNull(manifest);StrictJson.safe(sequence,1);WriterContracts.requireDigest(headDigest);}
        /** Mechanical ticket DATA from the exact current capture; admission remains writer-owned. */
        public static Optional<CleanRestartTicket> fromCapturedHead(WriterContracts.Head head,ExactRef persistedHead) {
            Objects.requireNonNull(head);Objects.requireNonNull(persistedHead);
            var whole=head.state().toJson();
            var retained=whole.get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD);
            if(retained==null||!retained.isObject()||!retained.has("boundary")
                    ||!JournalKind.WORKER_RESTART_CAPTURE.name().equals(StrictJson.text(retained.get("boundary"))))
                return Optional.empty();
            var boundary=StrictJson.object(retained,java.util.Set.of("evidence_id","session","batch_id","boundary","restart_manifest"));
            var details=boundary.deepCopy();details.put("source","java-ordinary-session/v1");
            details.putNull("checkpoint_pair");details.putNull("completed_cycle_proof");
            var capture=new WriterContracts.Request(OrdinaryCycleTransitions.BATCH_KIND,
                    ContinuityJson.canonical(details),java.util.List.of());
            if(!capture.identity().equals(StrictJson.text(whole.get("last_event_identity"))))return Optional.empty();
            return Optional.of(new CleanRestartTicket(persistedHead,head.state().sequence(),head.digest(),
                    ExactRef.fromJson(boundary.get("restart_manifest"))));
        }
        public byte[] encode(){var row=StrictJson.object();row.put("schema","xar.java-clean-restart-ticket/v1");row.set("persisted_head",persistedHead.toJson());
            row.put("sequence",sequence);row.put("head_digest",headDigest);row.set("manifest",manifest.toJson());return ContinuityJson.canonical(row);}
        public static CleanRestartTicket decode(byte[] bytes){var row=StrictJson.object(ContinuityJson.parseObject(bytes,ContinuityJson.DOCUMENT_MAX_BYTES),FIELDS,FIELDS);
            StrictJson.require("xar.java-clean-restart-ticket/v1".equals(StrictJson.text(row.get("schema"))),"restart ticket schema differs");
            return new CleanRestartTicket(ExactRef.fromJson(row.get("persisted_head")),StrictJson.integer(row.get("sequence"),1,StrictJson.MAX_SAFE_INTEGER),
                    StrictJson.text(row.get("head_digest")),ExactRef.fromJson(row.get("manifest")));}
    }
    /** Private-issued canonical admission. It contains no old native connection capability. */
    public static final class CleanRestartAdmission {
        private final ContinuityBatchJournal issuer;
        private final CleanRestartTicket ticket;
        private final CleanBatchRestart manifest;
        private final ControllerRestartState controller;
        private final org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known facts;
        private CleanRestartAdmission(ContinuityBatchJournal issuer,CleanRestartTicket ticket,CleanBatchRestart manifest,
                ControllerRestartState controller,org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known facts){
            this.issuer=issuer;this.ticket=ticket;this.manifest=manifest;this.controller=controller;this.facts=facts;
        }
        public CleanRestartTicket ticket(){return ticket;}
        public CleanBatchRestart manifest(){return manifest;}
        public ControllerRestartState controller(){return controller;}
        public org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known facts(){return facts;}
        public void requireCurrent(ContinuityStorePort.Session same)throws IOException {
            issuer.store.requireSession(same);
            same.requireDomainImportContinuation(ticket.sequence(),ticket.headDigest());
            issuer.transitions.withLocked(same,()->{
                issuer.requireRestartBoundary(same,ticket);issuer.transitions.requireRestartClean(same,controller.owner());
                // Retained admission already decoded original bodies once; only current writer continuity is rechecked.
                return true;
            });
        }
    }
    /** Full typed Known JSON comparison; archived bytes retain their original exact hash and identity. */
    static boolean sameKnownRestartOriginal(byte[] original,org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known expected) {
        int maximum=org.xar.ck3.control.application.driver.DriverSnapshotFacts.MAX_ORIGINAL_BYTES;
        var encoded=org.xar.ck3.control.application.driver.DriverSnapshotFacts.encodeKnownOriginal(expected).bytes();
        return org.xar.ck3.control.application.driver.DriverJson.object(original,maximum)
                .equals(org.xar.ck3.control.application.driver.DriverJson.object(encoded,maximum));
    }

    CleanRestartTicket captureCleanRestart(ContinuityStorePort.Session same,SessionController.CapturedRestart actual,
            org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known facts)throws IOException {
        store.requireSession(same);actual.requireJournal(this);
        return transitions.withLocked(same,()->transitions.captureRestart(same,actual.state(),facts));
    }
    /** Reads the current canonical marker and all original bodies under the one original writer lock. */
    public CleanRestartAdmission admitCleanRestart(ContinuityStorePort.Session same,CleanRestartTicket ticket)throws IOException {
        store.requireSession(same);Objects.requireNonNull(ticket);
        return transitions.withLocked(same,()->{
            var head=same.head();StrictJson.require(head.state().sequence()==ticket.sequence()&&head.digest().equals(ticket.headDigest())
                    &&same.persistedHead().equals(ticket.persistedHead()),"restart requires its unchanged actual canonical writer head");
            StrictJson.require(CleanRestartTicket.fromCapturedHead(head,same.persistedHead()).filter(ticket::equals).isPresent(),
                    "restart admission requires the exact current canonical capture event");
            requireRestartBoundary(same,ticket);
            var scoped=transitions.restartArchive(same);
            var manifest=CleanBatchRestart.decode(scoped.loadMaterial(ticket.manifest()).bytes());
            var controller=ControllerRestartState.decode(scoped.loadMaterial(manifest.controller()).bytes());
            var facts=org.xar.ck3.control.application.driver.DriverSnapshotFacts.decodeKnownOriginal(scoped.loadFullMaterial(manifest.driverFacts()),Optional.empty());
            byte[] full=scoped.loadFullMaterial(manifest.fullDriver()).bytes();
            StrictJson.require(java.util.Arrays.equals(full,facts.driver().encode())&&facts.stamp().game().equals(controller.owner().game())
                    &&manifest.previousTransport().game().equals(controller.owner().game())
                    &&manifest.previousTransport().machineId().equals(controller.owner().machineId())
                    &&manifest.previousTransport().sessionId().equals(controller.owner().sessionId())
                    &&!controller.quarantined()&&!controller.localUnresolved(),"restart originals crossed the resolved original Controller/Driver/Game");
            transitions.requireRestartClean(same,controller.owner());
            return new CleanRestartAdmission(this,ticket,manifest,controller,facts);
        });
    }
    private void requireRestartBoundary(ContinuityStorePort.Session same,CleanRestartTicket ticket)throws IOException {
        var boundary=same.head().state().toJson().get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD);
        StrictJson.require(boundary!=null&&boundary.isObject()&&JournalKind.WORKER_RESTART_CAPTURE.name().equals(StrictJson.text(boundary.get("boundary")))
                &&ticket.manifest().equals(ExactRef.fromJson(boundary.get("restart_manifest"))),"actual writer does not retain this clean restart capture");
    }
    void requireRestartAdmission(ContinuityStorePort.Session same,CleanRestartAdmission actual,SessionIdentity expected)throws IOException {
        StrictJson.require(actual!=null&&actual.issuer==this&&actual.controller.owner().equals(expected),"actual original journal restart admission required");actual.requireCurrent(same);
    }
    /** Construction-only installation of the actual NS/M3 producer; DATA inputs never replace this port. */
    public void bindTransportRebindPort(SameGameTransportContinuity.Port actual) {
        transitions.bindTransportRebindPort(Objects.requireNonNull(actual));
    }
    @Override public JournalCommit commit(JournalInput input) throws IOException {
        return store.locked(session -> commit(session,input));
    }
    /** Public SAVE confirmation may borrow the already held original writer; reducer/preview/commit stay identical. */
    public JournalCommit commit(ContinuityStorePort.Session original,JournalInput input)throws IOException {
        store.requireSession(Objects.requireNonNull(original));Objects.requireNonNull(input);
        return transitions.withLocked(original, () -> {
            var request = transitions.batchRequest(input);
            var committed = original.commit(original.preview(request));
            long delta = committed.head().settledDateRaw() - committed.head().origin().startDateRaw();
            StrictJson.require(delta >= 0 && delta % 24 == 0, "actual saved frontier contains whole forward game days");
            return new JournalCommit(original.persistedHead(), delta / 24);
        });
    }
    @Override public Optional<CompletedCycleProof> cycleProof(SessionIdentity owner, SemanticEvidence semantic) throws IOException {
        return store.locked(session -> cycleProof(session,owner,semantic));
    }
    /** Reads only the actual producer's proof in this identical Session. Missing proof remains absent. */
    public Optional<CompletedCycleProof> cycleProof(ContinuityStorePort.Session original,SessionIdentity owner,SemanticEvidence semantic)throws IOException {
        store.requireSession(Objects.requireNonNull(original));Objects.requireNonNull(owner);Objects.requireNonNull(semantic);
        return transitions.withLocked(original, () -> transitions.cycleProof(original,owner,semantic));
    }
    /** Pure original-cycle check under this same actual writer; grants no operator action or Ready. */
    public void requireOperatorBefore(ContinuityStorePort.Session same,SessionIdentity owner,
            org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Complete actualBeforeDriver,java.math.BigInteger actualDateRaw)throws IOException {
        store.requireSession(Objects.requireNonNull(same));
        transitions.requireOperatorBefore(same,owner,actualBeforeDriver,actualDateRaw);
    }
    @Override public JournalCommit acceptPublicCheckpoint(SessionIdentity owner,Captured actual)throws IOException {
        return store.locked(same->acceptPublicCheckpoint(same,owner,actual));
    }
    /** Read-only adoption: the private issuer revalidates its real SAVE, unchanged cycle and physical saved material. */
    @Override public JournalCommit acceptPublicCheckpoint(ContinuityStorePort.Session same,SessionIdentity owner,Captured actual)throws IOException {
        store.requireSession(Objects.requireNonNull(same));Objects.requireNonNull(owner);Objects.requireNonNull(actual);
        return actual.requireAdoption(same,owner,this);
    }
    @Override public void acceptOperatorRebound(SessionIdentity owner,ActionReceipt actual,SemanticEvidence semantic)throws IOException {
        store.locked(same->{acceptOperatorRebound(same,owner,actual,semantic);return true;});
    }
    /** Root may retain its original writer scope; the installed cycle source revalidates on both preview and commit. */
    public void acceptOperatorRebound(ContinuityStorePort.Session same,SessionIdentity owner,ActionReceipt actual,SemanticEvidence semantic)throws IOException {
        store.requireSession(Objects.requireNonNull(same));Objects.requireNonNull(owner);Objects.requireNonNull(actual);Objects.requireNonNull(semantic);
        transitions.withLocked(same,()->{transitions.rebindOperator(same,owner,actual,semantic);return true;});
    }
    @Override public void retainCycle(SessionIdentity owner, ActionReceipt receipt) throws IOException {
        store.locked(session -> transitions.withLocked(session, () -> { transitions.retain(session, owner, receipt); return true; }));
    }
    @Override public CompletedCycleProof settleCycle(SessionIdentity owner, ActionReceipt receipt, SemanticEvidence semantic) throws IOException {
        return store.locked(session -> transitions.withLocked(session, () -> transitions.settle(session, owner, receipt, semantic)));
    }
    /** Root cannot construct this admission from JSON, a SAVE ACK or a public record constructor. */
    public static final class ReboundCycle {
        private final ContinuityBatchJournal issuer;
        private final RestoreBinding restore;
        private final WriterContracts.Receipt committed;
        private final CompletedCycleProof proof;
        private ReboundCycle(ContinuityBatchJournal issuer, RestoreBinding restore, WriterContracts.Receipt committed, CompletedCycleProof proof) {
            this.issuer=issuer; this.restore=restore; this.committed=committed; this.proof=proof;
        }
        public RestoreBinding restore() { return restore; }
        public SessionIdentity session() { return restore.session(); }
        public WriterContracts.Receipt committed() { return committed; }
        public CompletedCycleProof proof() { return proof; }
        public long newSavedDayCredit() { return 0; }
    }
    /** Fresh native restore revalidation precedes the held-lock exact attachment-head CAS. No Game call occurs under this lock. */
    public ReboundCycle rebind(RestoreCheckpointService service, RestoreBinding binding, Instant deadline) throws IOException, InterruptedException {
        Objects.requireNonNull(service); Objects.requireNonNull(binding); Objects.requireNonNull(deadline);
        service.requireCurrent(binding, deadline);
        return store.locked(session -> transitions.withLocked(session, () -> {
            var committed = transitions.rebind(session, binding);
            var proof = transitions.cycleProof(session, binding.session(), binding.semantic())
                    .orElseThrow(() -> new IOException("source-bound restore did not produce a settled new cycle binding"));
            return new ReboundCycle(this, binding, committed, proof);
        }));
    }
    /** Root already admitted the private physical restore; only actual canonical domain imports may intervene before this zero-credit rebind. */
    public ReboundCycle rebindAfterDomainImports(RestoreCheckpointService service,RestoreBinding binding) throws IOException {
        Objects.requireNonNull(service);Objects.requireNonNull(binding);
        return store.locked(session->{
            service.requireRetainedOriginal(session,binding);
            session.requireDomainImportContinuation(binding.attachment().head().sequence(),ContinuityJson.digest(binding.attachment().head().toJson()));
            return transitions.withLocked(session,()->{
                var committed=transitions.rebind(session,binding);
                var proof=transitions.cycleProof(session,binding.session(),binding.semantic())
                        .orElseThrow(()->new IOException("domain-only restored source did not produce its actual settled cycle binding"));
                service.requireRetainedOriginal(session,binding);
                return new ReboundCycle(this,binding,committed,proof);
            });
        });
    }
    /** Re-read the new canonical head and exact archived proof before Root publishes its replacement controller. */
    public void requireCurrent(ReboundCycle admitted) throws IOException {
        store.locked(session -> { requireCurrent(session,admitted);return true; });
    }
    /** Root publication borrows its actual writer session; this entry never opens a nested OS lock. */
    public void requireCurrent(ContinuityStorePort.Session borrowed,ReboundCycle admitted) throws IOException {
        StrictJson.require(admitted != null && admitted.issuer == this, "original journal-issued restore cycle admission required");
        transitions.withLocked(borrowed, () -> {
            StrictJson.require(borrowed.head().digest().equals(ContinuityJson.digest(admitted.committed.head().toJson())), "canonical cycle head changed after actual restore rebind");
            var actual = transitions.cycleProof(borrowed, admitted.session(), admitted.restore.semantic())
                    .orElseThrow(() -> new IOException("restored cycle binding no longer has actual settled evidence"));
            StrictJson.require(actual.equals(admitted.proof), "actual restored cycle proof changed before Root publication"); return true;
        });
    }
    /** A constructor cannot mint this cycle admission; only the original writer transaction can. */
    public static final class ReboundEpisode {
        private final ContinuityBatchJournal issuer;
        private final LifecycleEpisodeInputs.Binding binding;
        private final WriterContracts.Receipt committed;
        private final CompletedCycleProof proof;
        private ReboundEpisode(ContinuityBatchJournal issuer,LifecycleEpisodeInputs.Binding binding,WriterContracts.Receipt committed,CompletedCycleProof proof) {
            this.issuer=issuer;this.binding=binding;this.committed=committed;this.proof=proof;
        }
        public LifecycleEpisodeInputs.Binding binding(){return binding;}
        public SessionIdentity session(){return binding.afterOwner();}
        public WriterContracts.Receipt committed(){return committed;}
        public CompletedCycleProof proof(){return proof;}
        public long newSavedDayCredit(){return 0;}
        public long newCompletedCycleCredit(){return 0;}
    }
    /** Private evidence that this journal admitted this exact canonical natural parent, not a constructible cycle DTO. */
    public static final class AdmittedEpisode {
        private final ContinuityBatchJournal issuer;
        private final SessionIdentity owner;
        private final ActionReceipt parent;
        private final String publication;
        private final ContinuityState qualifiedHead;
        private final ExactRef origin;
        private final CompletedCycleProof proof;
        private final Optional<WriterContracts.Receipt> committed;
        private final boolean checkpointRequired;
        private final Optional<CheckpointPair> savedFrontier;
        private AdmittedEpisode(ContinuityBatchJournal issuer,SessionIdentity owner,ActionReceipt parent,
                LifecycleEpisodeInputs.Binding binding,OrdinaryCycleTransitions.EpisodeEvidence actual,
                Optional<WriterContracts.Receipt> committed) {
            this(issuer,owner,parent,binding.commitDigest(),actual,committed,true,Optional.empty());
        }
        private AdmittedEpisode(ContinuityBatchJournal issuer,SessionIdentity owner,ActionReceipt parent,String publication,
                OrdinaryCycleTransitions.EpisodeEvidence actual,Optional<WriterContracts.Receipt> committed,
                boolean checkpointRequired,Optional<CheckpointPair> savedFrontier) {
            this.issuer=issuer;this.owner=owner;this.parent=parent;this.publication=publication;
            qualifiedHead=actual.head();origin=actual.origin();proof=actual.proof();this.committed=committed;
            this.checkpointRequired=checkpointRequired;this.savedFrontier=savedFrontier;
        }
        public SessionIdentity owner(){return owner;}
        public ActionReceipt parent(){return parent;}
        public CompletedCycleProof proof(){return proof;}
        public ExactRef origin(){return origin;}
        public boolean newBinding(){return committed.isPresent();}
        public boolean checkpointRequired(){return checkpointRequired;}
        /** Canonical frontier DATA only. It does not grant physical pair adoption. */
        public Optional<CheckpointPair> savedFrontier(){return savedFrontier;}
        public long newSavedDayCredit(){return 0;}
        public long newCompletedCycleCredit(){return 0;}
    }
    public AdmittedEpisode admitEpisode(LifecycleEpisodeInputs inputs,SessionIdentity owner,ActionReceipt parent,
            PostLifecycleSemanticCapture capture,Instant deadline)throws IOException {
        return store.locked(same->admitEpisode(same,inputs,owner,parent,capture,deadline));
    }
    /** A cold Controller readopts the already canonical same-parent branch with no new event or warm Receipt. */
    public AdmittedEpisode admitEpisode(ContinuityStorePort.Session same,LifecycleEpisodeInputs inputs,
            SessionIdentity owner,ActionReceipt parent,PostLifecycleSemanticCapture capture,Instant deadline)throws IOException {
        store.requireSession(Objects.requireNonNull(same));Objects.requireNonNull(inputs);Objects.requireNonNull(owner);
        Objects.requireNonNull(parent);Objects.requireNonNull(capture);Objects.requireNonNull(deadline);
        SemanticEvidence semantic=capture.capture(same,owner,parent,deadline);
        return transitions.withLocked(same,()->{
            var binding=inputs.bind(same,owner,owner,parent,semantic);
            Optional<WriterContracts.Receipt> committed=transitions.hasEpisodeAdmission(same,inputs,binding)
                    ?Optional.empty():Optional.of(transitions.rebindEpisode(same,inputs,binding));
            var actual=transitions.episodeEvidence(same,owner,parent,binding.commitDigest(),semantic);
            return new AdmittedEpisode(this,owner,parent,binding,actual,committed);
        });
    }
    public void requireHistoricalEpisodeAdoption(AdmittedEpisode actual)throws IOException {
        store.locked(same->{requireHistoricalEpisodeAdoption(same,actual);return true;});
    }
    /** Historical knowledge only: original writer replay and original full evidence, without granting current Ready. */
    public void requireHistoricalEpisodeAdoption(ContinuityStorePort.Session same,AdmittedEpisode actual)throws IOException {
        store.requireSession(Objects.requireNonNull(same));
        StrictJson.require(actual!=null&&actual.issuer==this,"episode adoption belongs to another actual journal");
        transitions.withLocked(same,()->{
            var historical=same.requireHistoricalState(actual.qualifiedHead.sequence(),ContinuityJson.digest(actual.qualifiedHead.toJson()));
            StrictJson.require(historical.toJson().equals(actual.qualifiedHead.toJson()),"episode adoption lost its canonical historical whole state");
            transitions.requireHistoricalEpisodeEvidence(same,actual.owner,actual.parent,actual.publication,
                    historical,actual.origin,actual.proof);
            return true;
        });
    }
    /** Read-only current saved-frontier DATA; it cannot adopt a pair, create an episode admission or grant Ready. */
    public static final class SavedCycleFrontier {
        private final boolean checkpointRequired;
        private final Optional<CheckpointPair> pair;
        private SavedCycleFrontier(OrdinaryCycleTransitions.SavedFrontierEvidence actual){checkpointRequired=actual.checkpointRequired();pair=actual.pair();}
        public boolean checkpointRequired(){return checkpointRequired;}
        public Optional<CheckpointPair> pair(){return pair;}
    }
    public SavedCycleFrontier currentSavedFrontier(ContinuityStorePort.Session same,SessionIdentity owner,CompletedCycleProof actual)throws IOException {
        store.requireSession(Objects.requireNonNull(same));Objects.requireNonNull(owner);Objects.requireNonNull(actual);
        return transitions.withLocked(same,()->new SavedCycleFrontier(transitions.savedFrontierEvidence(same,owner,actual)));
    }
    /** Only this identical Journal can issue canonical transport owner knowledge. It is not a current Native lease. */
    public static final class ReboundTransport {
        private final ContinuityBatchJournal issuer;
        private final OrdinaryCycleTransitions.TransportEvidence actual;
        private ReboundTransport(ContinuityBatchJournal issuer,OrdinaryCycleTransitions.TransportEvidence actual) {
            this.issuer=issuer;this.actual=actual;
        }
        public SessionIdentity beforeOwner(){return actual.evidence().beforeOwner();}
        public SessionIdentity owner(){return actual.evidence().afterOwner();}
        public ActionCommand parent(){return actual.evidence().canonicalParent().command();}
        public SameGameTransportContinuity.Purpose purpose(){return actual.evidence().purpose();}
        public ExactRef origin(){return actual.origin();}
        public CompletedCycleProof proof(){return actual.proof();}
        public boolean newBinding(){return actual.committed().isPresent();}
        public Optional<WriterContracts.Receipt> committed(){return actual.committed();}
        public boolean checkpointRequired(){return actual.checkpointRequired();}
        /** Canonical saved-frontier DATA only; this never adopts physical files. */
        public Optional<CheckpointPair> savedFrontier(){return actual.savedFrontier();}
        public long newSavedDayCredit(){return 0;}
        public long newCompletedCycleCredit(){return 0;}
        /** Historical replay only. Every current pending/current use still needs a new actual NS/M3 scope. */
        public void requireHistorical(ContinuityStorePort.Session same)throws IOException {issuer.requireHistoricalTransport(same,this);}
    }
    /** Existing writer scope only. The installed port supplies genuine prepared source custody after its physical loan closes. */
    public ReboundTransport rebindTransport(ContinuityStorePort.Session same,SessionIdentity afterOwner,
            ActionCommand exactParent,Instant deadline)throws IOException,InterruptedException {
        store.requireSession(Objects.requireNonNull(same));Objects.requireNonNull(afterOwner);Objects.requireNonNull(exactParent);Objects.requireNonNull(deadline);
        return new ReboundTransport(this,transitions.rebindTransport(same,afterOwner,exactParent,deadline));
    }
    public void requireHistoricalTransport(ReboundTransport actual)throws IOException {
        store.locked(same->{requireHistoricalTransport(same,actual);return true;});
    }
    public void requireHistoricalTransport(ContinuityStorePort.Session same,ReboundTransport actual)throws IOException {
        store.requireSession(Objects.requireNonNull(same));
        StrictJson.require(actual!=null&&actual.issuer==this,"transport admission belongs to another actual Journal");
        transitions.withLocked(same,()->{
            transitions.requireHistoricalTransportEvidence(same,actual.actual);return true;
        });
    }
    /** Genuine canonical admission history plus a specific currently validated cycle; never an exact-post Base. */
    public static final class HistoricalEpisodeAdoption {
        private final ContinuityBatchJournal issuer;
        private final SessionIdentity owner;
        private final LifecycleHistoricalPublication.Recorded recorded;
        private final OrdinaryCycleTransitions.HistoricalEpisodeEvidence actual;
        private HistoricalEpisodeAdoption(ContinuityBatchJournal issuer,SessionIdentity owner,
                LifecycleHistoricalPublication.Recorded recorded,OrdinaryCycleTransitions.HistoricalEpisodeEvidence actual) {
            this.issuer=issuer;this.owner=owner;this.recorded=recorded;this.actual=actual;
        }
        public SessionIdentity owner(){return owner;}
        public ActionReceipt parent(){return recorded.parent();}
        public LifecycleHistoricalPublication.Recorded recorded(){return recorded;}
        public ObservationIdentity frame(){return actual.frame();}
        public ExactRef origin(){return actual.origin();}
        public String admissionEventIdentity(){return actual.admission().eventIdentity();}
        public long admissionSequence(){return actual.admission().sequence();}
        /** DATA from the actual canonical transport origin; the private ticket and fresh M7 scope remain mandatory. */
        public Optional<SameGameTransportContinuity.Evidence> transportEvidence(){return actual.transportEvidence();}
        public void requireCurrent(ContinuityStorePort.Session same)throws IOException {issuer.requireHistoricalEpisodeCurrent(same,this);}
    }
    public Optional<HistoricalEpisodeAdoption> historicalEpisodeAdoption(ContinuityStorePort.Session same,
            SessionIdentity owner,LifecycleHistoricalPublication.Recorded recorded)throws IOException {
        store.requireSession(Objects.requireNonNull(same));Objects.requireNonNull(owner);Objects.requireNonNull(recorded);
        return transitions.withLocked(same,()->transitions.historicalEpisodeEvidence(same,owner,recorded)
                .map(actual->new HistoricalEpisodeAdoption(this,owner,recorded,actual)));
    }
    /** Distinct fresh-owner route. It cannot change the owner of an old private historical ticket. */
    public Optional<HistoricalEpisodeAdoption> transportedHistoricalEpisodeAdoption(ContinuityStorePort.Session same,
            SessionIdentity owner,LifecycleHistoricalPublication.Recorded recorded,ReboundTransport transport)throws IOException {
        store.requireSession(Objects.requireNonNull(same));Objects.requireNonNull(owner);Objects.requireNonNull(recorded);Objects.requireNonNull(transport);
        requireHistoricalTransport(same,transport);
        StrictJson.require(owner.equals(transport.owner())&&java.util.Arrays.equals(
                org.xar.ck3.control.application.action.ActionCodec.encodeCommand(transport.parent()),
                org.xar.ck3.control.application.action.ActionCodec.encodeCommand(recorded.parent().command())),
                "transported historical admission changed the private owner or complete original final parent");
        return transitions.withLocked(same,()->transitions.transportedHistoricalEpisodeEvidence(same,owner,recorded,transport.origin())
                .map(actual->new HistoricalEpisodeAdoption(this,owner,recorded,actual)));
    }
    private void requireHistoricalEpisodeCurrent(ContinuityStorePort.Session same,HistoricalEpisodeAdoption ticket)throws IOException {
        store.requireSession(Objects.requireNonNull(same));
        StrictJson.require(ticket!=null&&ticket.issuer==this,"historical adoption belongs to another actual journal");
        transitions.withLocked(same,()->{
            var actual=(ticket.actual.transportEvidence().isPresent()
                    ?transitions.transportedHistoricalEpisodeEvidence(same,ticket.owner,ticket.recorded,ticket.origin())
                    :transitions.historicalEpisodeEvidence(same,ticket.owner,ticket.recorded))
                    .orElseThrow(()->new IOException("actual current branch no longer carries this canonical episode adoption"));
            StrictJson.require(actual.origin().equals(ticket.actual.origin())&&actual.cycleDigest().equals(ticket.actual.cycleDigest())
                    &&actual.admission().eventIdentity().equals(ticket.admissionEventIdentity())
                    &&actual.admission().sequence()==ticket.admissionSequence(),"historical admission or actual current cycle changed");
            return true;
        });
    }
    /** Requalify the present through the private M7 current role; no event, Base or replacement origin is created. */
    public AdmittedEpisode admitCurrentEpisode(ContinuityStorePort.Session same,LifecycleEpisodeInputs.CurrentAdoptionBinding binding)throws IOException {
        store.requireSession(Objects.requireNonNull(same));Objects.requireNonNull(binding);
        var ticket=binding.historical();StrictJson.require(ticket.issuer==this,"current episode binding belongs to another journal");
        binding.requireCurrent(same);
        AdmittedEpisode result=transitions.withLocked(same,()->{
            var current=(ticket.actual.transportEvidence().isPresent()
                    ?transitions.transportedHistoricalEpisodeEvidence(same,ticket.owner,ticket.recorded,ticket.origin())
                    :transitions.historicalEpisodeEvidence(same,ticket.owner,ticket.recorded))
                    .orElseThrow(()->new IOException("original canonical adoption is unavailable at the current cycle"));
            var evidence=transitions.episodeEvidence(same,binding.owner(),binding.parent(),ticket.recorded.publication().eventIdentity(),binding.semantic());
            return new AdmittedEpisode(this,binding.owner(),binding.parent(),ticket.recorded.publication().eventIdentity(),evidence,
                    Optional.empty(),current.checkpointRequired(),current.savedFrontier());
        });
        binding.requireCurrent(same);return result;
    }
    /** Pre-window input custody only. The actual Window authority must consume this at its original head.
     * After WINDOW_BEGIN Root captures a new actual SEM and calls rebindEpisode again; this old binding is never refreshed in place. */
    public LifecycleEpisodeInputs.Binding prepareEpisode(ContinuityStorePort.Session borrowed,LifecycleEpisodeInputs inputs,
            SessionIdentity beforeOwner,SessionIdentity afterOwner,ActionReceipt parent,SemanticEvidence semantic) throws IOException {
        Objects.requireNonNull(borrowed);Objects.requireNonNull(inputs);Objects.requireNonNull(beforeOwner);
        Objects.requireNonNull(afterOwner);Objects.requireNonNull(parent);Objects.requireNonNull(semantic);
        return transitions.withLocked(borrowed,()->inputs.bind(borrowed,beforeOwner,afterOwner,parent,semantic));
    }
    public ReboundEpisode rebindEpisode(LifecycleEpisodeInputs inputs,SessionIdentity beforeOwner,SessionIdentity afterOwner,
            ActionReceipt parent,SemanticEvidence semantic) throws IOException {
        Objects.requireNonNull(inputs);
        return store.locked(session->transitions.withLocked(session,()->rebindEpisodeLocked(session,inputs,beforeOwner,afterOwner,parent,semantic)));
    }
    /** Natural succession captures its original post-SEM and consumes it before any planning query can append READ history. */
    public ReboundEpisode rebindEpisode(LifecycleEpisodeInputs inputs,SessionIdentity owner,ActionReceipt parent,
            PostLifecycleSemanticCapture actualCapture,Instant deadline) throws IOException {
        Objects.requireNonNull(inputs);Objects.requireNonNull(actualCapture);Objects.requireNonNull(deadline);
        return store.locked(session->rebindEpisode(session,inputs,owner,parent,actualCapture,deadline));
    }
    /** Core retains the original writer lock from current-Root selection through post-SEM and the actual reducer. */
    public ReboundEpisode rebindEpisode(ContinuityStorePort.Session borrowed,LifecycleEpisodeInputs inputs,
            SessionIdentity owner,ActionReceipt parent,PostLifecycleSemanticCapture actualCapture,Instant deadline) throws IOException {
        Objects.requireNonNull(borrowed);Objects.requireNonNull(inputs);Objects.requireNonNull(owner);
        Objects.requireNonNull(parent);Objects.requireNonNull(actualCapture);Objects.requireNonNull(deadline);
        store.requireSession(borrowed);
        SemanticEvidence original=actualCapture.capture(borrowed,owner,parent,deadline);
        return transitions.withLocked(borrowed,()->rebindEpisodeLocked(borrowed,inputs,owner,owner,parent,original));
    }
    private ReboundEpisode rebindEpisodeLocked(ContinuityStorePort.Session session,LifecycleEpisodeInputs inputs,
            SessionIdentity beforeOwner,SessionIdentity afterOwner,ActionReceipt parent,SemanticEvidence semantic) throws IOException {
        var binding=inputs.bind(session,beforeOwner,afterOwner,parent,semantic);
        var committed=transitions.rebindEpisode(session,inputs,binding);
        var proof=transitions.cycleProof(session,afterOwner,semantic).orElseThrow(()->new IOException("actual episode cycle rebind retained an unresolved pending cycle"));
        return new ReboundEpisode(this,binding,committed,proof);
    }
    public void requireCurrent(ReboundEpisode admitted) throws IOException {
        store.locked(session->{requireCurrent(session,admitted);return true;});
    }
    public void requireCurrent(ContinuityStorePort.Session borrowed,ReboundEpisode admitted) throws IOException {
        StrictJson.require(admitted!=null&&admitted.issuer==this,"actual original journal-issued episode admission required");
        transitions.withLocked(borrowed,()->{
            StrictJson.require(borrowed.head().digest().equals(ContinuityJson.digest(admitted.committed.head().toJson())),"episode head changed before its actual publication");
            var proof=transitions.cycleProof(borrowed,admitted.session(),admitted.binding.semantic()).orElseThrow(()->new IOException("episode binding lost its completed-cycle proof"));
            StrictJson.require(proof.equals(admitted.proof),"episode proof changed before actual publication");return true;
        });
    }
    /** Only the original writer transaction can turn a private physical first SAVE into a new cycle branch. */
    public static final class ReboundNextBaseline {
        private final ContinuityBatchJournal issuer;
        private final LifecycleEpisodeInputs inputs;
        private final LifecycleEpisodeInputs.NextBaselineBinding binding;
        private final WriterContracts.Receipt committed;
        private final CompletedCycleProof proof;
        private ReboundNextBaseline(ContinuityBatchJournal issuer,LifecycleEpisodeInputs inputs,
                LifecycleEpisodeInputs.NextBaselineBinding binding,WriterContracts.Receipt committed,CompletedCycleProof proof) {
            this.issuer=issuer;this.inputs=inputs;this.binding=binding;this.committed=committed;this.proof=proof;
        }
        public LifecycleEpisodeInputs.NextBaselineBinding binding(){return binding;}
        public SessionIdentity session(){return binding.afterOwner();}
        public WriterContracts.Receipt committed(){return committed;}
        public CompletedCycleProof proof(){return proof;}
        public long newSavedDayCredit(){return 0;}
        public long newCompletedCycleCredit(){return 0;}
    }
    /** First SAVE and BASELINE have already completed. This method sends no native action and saves nothing. */
    public ReboundNextBaseline rebindNextBaseline(LifecycleEpisodeInputs inputs,
            LifecycleEpisodeInputs.NextBaselineBinding binding) throws IOException {
        return store.locked(same->rebindNextBaseline(same,inputs,binding));
    }
    /** Root may borrow the existing sole writer lock; no nested store/OS lock is opened. */
    public ReboundNextBaseline rebindNextBaseline(ContinuityStorePort.Session borrowed,LifecycleEpisodeInputs inputs,
            LifecycleEpisodeInputs.NextBaselineBinding binding) throws IOException {
        Objects.requireNonNull(borrowed);Objects.requireNonNull(inputs);Objects.requireNonNull(binding);
        return transitions.withLocked(borrowed,()->{
            var committed=transitions.rebindNextBaseline(borrowed,inputs,binding);
            var proof=transitions.cycleProof(borrowed,binding.afterOwner(),binding.semantic())
                    .orElseThrow(()->new IOException("actual first-SAVE BASELINE retained an unresolved new-window cycle"));
            inputs.requireCurrentBaseline(borrowed,binding);
            return new ReboundNextBaseline(this,inputs,binding,committed,proof);
        });
    }
    public void requireCurrent(ReboundNextBaseline admitted) throws IOException {
        store.locked(same->{requireCurrent(same,admitted);return true;});
    }
    public void requireCurrent(ContinuityStorePort.Session borrowed,ReboundNextBaseline admitted) throws IOException {
        StrictJson.require(admitted!=null&&admitted.issuer==this,"actual original journal-issued first-SAVE cycle admission required");
        transitions.withLocked(borrowed,()->{
            StrictJson.require(borrowed.head().digest().equals(ContinuityJson.digest(admitted.committed.head().toJson())),
                    "new-window cycle head changed before actual Root publication");
            admitted.inputs.requireCurrentBaseline(borrowed,admitted.binding);
            var proof=transitions.cycleProof(borrowed,admitted.session(),admitted.binding.semantic())
                    .orElseThrow(()->new IOException("new-window cycle lost its actual first-SAVE source"));
            StrictJson.require(proof.equals(admitted.proof),"first-SAVE cycle proof changed before actual Root publication");return true;
        });
    }
}
