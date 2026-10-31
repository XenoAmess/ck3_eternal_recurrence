package org.xar.ck3.control.application.session;

import java.io.IOException;
import org.xar.ck3.control.application.checkpoint.PublicCheckpointMaterialCapture.Captured;
import java.util.Objects;
import java.util.Optional;
import java.time.Instant;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.driver.DriverCapabilityStateProducer;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
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
        private Optional<org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known> retainedFacts;
        private Optional<ExactRef> retainedFullDriver;
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
            this.retainedFacts=capturedFacts;this.retainedFullDriver=capturedManifest.map(CleanBatchRestart::fullDriver);
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
        /** Actual retained READ DATA; the capture originals remain unchanged. */
        public Optional<org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known> retainedFacts(){return retainedFacts;}
        public Optional<ExactRef> retainedFullDriver(){return retainedFullDriver;}
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
                WriterContracts.ACTION_LIFECYCLE_FIELD,
                WriterContracts.DRIVER_HISTORY_BASELINE_FIELD,WriterContracts.GAMEPLAY_ENTRY_FIELD));
        for(String field:fields)StrictJson.require(before.has(field)==after.has(field)
                &&(!before.has(field)||ContinuityJson.same(before.get(field),after.get(field))),
                "zero-dispatch suffix changed captured business state: "+field);
    }
    private record RetainedReadDriver(org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known facts,ExactRef fullDriver) { }
    /** Replays committed typed READ DATA only; no query, live decoder or Native action is invoked. */
    private RetainedReadDriver retainCapturedRead(ContinuityStorePort.Session same,SessionIdentity owner,
            WriterContracts.HistoricalTransition edge,RetainedReadDriver previous,
            org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive originals,
            java.util.List<WriterContracts.Pin> originalsPins,boolean retainPins)throws IOException {
        var details=StrictJson.object(ContinuityJson.parseObject(edge.details(),ContinuityJson.LEDGER_MAX_BYTES),java.util.Set.of(
                "schema","evidence_id","token","source","predecessor_head_sha256","read_head_sha256","read_head_sequence",
                "before_version","after_version","episode_epoch","before_driver","after_driver","read_rows"));
        StrictJson.require("xar.driver-read-publication/v1".equals(StrictJson.text(details.get("schema"))),
                "captured READ recovery requires actual ordinary typed READ publication");
        StrictJson.text(details.get("evidence_id"));StrictJson.text(details.get("token"));
        var before=edge.before().toJson();var after=edge.after().toJson();
        var fields=new java.util.HashSet<String>();before.fieldNames().forEachRemaining(fields::add);after.fieldNames().forEachRemaining(fields::add);
        fields.removeAll(java.util.Set.of("sequence","last_event_identity",WriterContracts.DRIVER_READ_HISTORY_FIELD));
        for(String field:fields)StrictJson.require(before.has(field)==after.has(field)
                &&(!before.has(field)||ContinuityJson.same(before.get(field),after.get(field))),"captured READ changed business field: "+field);
        StrictJson.require(after.has(WriterContracts.DRIVER_READ_HISTORY_FIELD)
                &&ContinuityJson.same(after.get(WriterContracts.DRIVER_READ_HISTORY_FIELD),details),"captured READ lost its exact publication registry");
        var known=previous.facts();String predecessor=ContinuityJson.digest(before);
        long version=StrictJson.integer(details.get("before_version"),0,StrictJson.MAX_SAFE_INTEGER);
        long nextVersion=StrictJson.integer(details.get("after_version"),1,StrictJson.MAX_SAFE_INTEGER);
        StrictJson.require(version==known.stamp().driverVersion()&&nextVersion==Math.addExact(version,1)
                &&StrictJson.integer(details.get("episode_epoch"),0,StrictJson.MAX_SAFE_INTEGER)==known.stamp().episodeEpoch()
                &&StrictJson.text(details.get("predecessor_head_sha256")).equals(predecessor)
                &&StrictJson.integer(details.get("read_head_sequence"),0,StrictJson.MAX_SAFE_INTEGER)==edge.before().sequence()
                &&StrictJson.text(details.get("read_head_sha256")).equals(predecessor),"captured READ crossed its actual Driver version/epoch/head");
        ExactRef beforeRef=ExactRef.fromJson(details.get("before_driver")),afterRef=ExactRef.fromJson(details.get("after_driver"));
        StrictJson.require(beforeRef.equals(previous.fullDriver())
                &&java.util.Arrays.equals(originals.loadFullMaterial(beforeRef).bytes(),known.driver().encode()),"captured READ changed the complete Driver prefix");
        var appended=new java.util.ArrayList<>(known.driver().commandHistory());var rows=details.get("read_rows");
        StrictJson.require(rows!=null&&rows.isArray()&&!rows.isEmpty()&&rows.size()<=128,"finite actual captured READ rows required");
        for(var value:rows) {
            var row=StrictJson.object(value,java.util.Set.of("index","contract_id","row","read","definition_source","decoder_source"));
            ExactRef rowRef=ExactRef.fromJson(row.get("row")),readRef=ExactRef.fromJson(row.get("read"));
            var decoded=org.xar.ck3.control.application.history.DriverReadHistoryRowProducer.decode(originals.loadFullMaterial(rowRef).bytes());
            var source=decoded.provenance();var read=originals.loadRead(readRef);
            StrictJson.require(!source.kind().isRich()
                    &&source.kind()!=org.xar.ck3.control.application.history.DriverReadHistoryRowProducer.Kind.GIFT_COLD_RECOVERY,
                    "captured READ recovery requires the ordinary single original READ row contract");
            org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.requireRead(read,originals);
            StrictJson.require(decoded.index()==appended.size()+1L&&decoded.index()==StrictJson.integer(row.get("index"),1,StrictJson.MAX_SAFE_INTEGER)
                    &&source.originalReceipt().equals(readRef)&&source.contractId().equals(StrictJson.text(row.get("contract_id")))
                    &&source.definitionSource().equals(ExactRef.fromJson(row.get("definition_source")))
                    &&source.decoderSource().equals(ExactRef.fromJson(row.get("decoder_source")))
                    &&source.contractId().equals(read.contractId())&&source.requestId().equals(read.requestId())
                    &&decoded.command().equals(read.request().operation().value())&&source.sourceFrame().equals(read.request().before())
                    &&source.source().equals(read.request().source())&&source.sessionId().equals(read.request().sessionId())
                    &&source.connectionGeneration().equals(read.before().binding().connectionGeneration())
                    &&ContinuityJson.same(details.get("source"),org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.source(source.source()))
                    &&source.sourceFrame().game().equals(owner.game())&&source.sourceFrame().machineId().equals(owner.machineId())
                    &&source.sourceFrame().frame().identity().player().equals(known.driver().session().actorId())
                    &&source.sourceFrame().frame().episodeRunId().equals(known.stamp().episodeRunId())
                    &&source.sessionId().equals(owner.sessionId())&&read.request().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay,
                    "captured READ row changed its actual typed original/source/owner/ordinal");
            for(var guard:java.util.List.of(read.before(),read.after()))StrictJson.require(guard.paused()&&guard.mapReady()&&guard.playerAlive()
                    &&guard.guardMode()==org.xar.ck3.control.application.action.ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                    "captured READ crossed its original paused gameplay guards");
            StrictJson.require(read.before().originalBindingSha256().equals(read.after().originalBindingSha256()),
                    "captured READ changed its original complete semantic binding");
            // Definition/decoder references remain metadata; only original DATA is pinned.
            if(retainPins){originalsPins.add(same.capturePin(rowRef,WriterContracts.MAX_PIN_BYTES));originalsPins.add(same.capturePin(readRef,WriterContracts.MAX_PIN_BYTES));}
            if(retainPins)for(var ref:source.supportingEvidence())if(!ref.equals(source.definitionSource())&&!ref.equals(source.decoderSource()))
                originalsPins.add(same.capturePin(ref,WriterContracts.MAX_PIN_BYTES));
            appended.add(decoded.historyEntry());
        }
        var old=known.driver();
        var driver=new org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Complete(old.session(),appended,
                old.lastCheckpoint(),old.rollbackWarFailure(),old.managedRestoreTransaction(),old.successionExpectation(),
                old.successionLifecycle(),old.campaignGoal(),old.rollbackWarFailures());
        StrictJson.require(java.util.Arrays.equals(driver.encode(),originals.loadFullMaterial(afterRef).bytes()),
                "captured READ changed a non-history Driver slot or original row");
        if(retainPins){originalsPins.add(same.capturePin(beforeRef,WriterContracts.MAX_PIN_BYTES));originalsPins.add(same.capturePin(afterRef,WriterContracts.MAX_PIN_BYTES));}
        var stamp=new org.xar.ck3.control.application.driver.DriverSnapshotFacts.Stamp(nextVersion,known.stamp().episodeEpoch(),
                known.stamp().game(),known.stamp().episodeRunId(),org.xar.ck3.control.application.driver.DriverJson.sha256(driver.encode()));
        var auxiliary=new java.util.LinkedHashMap<>(known.auxiliary().members());
        auxiliary.put("driver_read_publication",new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of(
                "event_identity",new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text(edge.eventIdentity()),
                "request_sha256",new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text(
                        org.xar.ck3.control.application.driver.DriverJson.sha256(edge.details())))));
        var facts=new org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known(driver,stamp,known.originalHistoryBasis(),
                known.actionRows(),new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(auxiliary),known.loop(),Optional.empty());
        return new RetainedReadDriver(facts,afterRef);
    }
    /** Recover committed single-row ACTION history DATA after effect settlement, without issuing another action. */
    private RetainedReadDriver retainCapturedAction(WriterContracts.HistoricalTransition edge,RetainedReadDriver previous,
            java.util.List<ActionReceipt> receipts,org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive originals) {
        var details=ContinuityJson.parseObject(edge.details(),ContinuityJson.LEDGER_MAX_BYTES);
        String actionId=StrictJson.text(details.get("action_id"));
        var matches=receipts.stream().filter(r->r.command().actionId().equals(actionId)).toList();
        StrictJson.require(matches.size()==1&&matches.getFirst().outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED,
                "captured ACTION history requires its one settled original applied receipt");
        var action=matches.getFirst();
        var publication=org.xar.ck3.control.application.driver.DriverActionHistoryState.decode(details,action);
        var known=previous.facts();
        StrictJson.require(publication.predecessor().equals(ContinuityJson.digest(edge.before().toJson()))
                        &&publication.actionSequence()==edge.before().sequence()
                        &&publication.beforeVersion()==known.stamp().driverVersion()
                        &&publication.episodeEpoch()==known.stamp().episodeEpoch()
                        &&publication.beforeDriver().equals(previous.fullDriver())
                        &&java.util.Arrays.equals(originals.loadFullMaterial(publication.beforeDriver()).bytes(),known.driver().encode()),
                "captured ACTION changed its canonical predecessor or complete Driver");
        org.xar.ck3.control.application.driver.DriverActionHistoryState.requireReduction(edge.before(),edge.after(),
                publication.request(java.util.List.of(publication.beforeDriver(),publication.afterDriver(),publication.originalSource())),true);
        var driver=org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.decodeComplete(
                originals.loadFullMaterial(publication.afterDriver()).bytes());
        var oldHistory=known.driver().commandHistory();var newHistory=driver.commandHistory();
        StrictJson.require(newHistory.size()==oldHistory.size()+1&&newHistory.subList(0,oldHistory.size()).equals(oldHistory)
                        &&driver.session().equals(known.driver().session()),
                "captured ACTION history changed another Driver row or session");
        var rowRef=publication.legacyRow().orElseThrow(()->new IllegalArgumentException("captured ACTION requires its actual legacy history row"));
        var rowBytes=originals.loadMaterial(rowRef).bytes();
        StrictJson.require(java.util.Arrays.equals(newHistory.getLast().originalRow().json(),rowBytes),
                "captured ACTION history row differs from its named original");
        var coverage=new org.xar.ck3.control.application.driver.DriverSnapshotFacts.ActionRow(actionId,action.bodySha256(),
                action.sequence(),newHistory.size(),rowRef);
        var rows=new java.util.ArrayList<>(known.actionRows());rows.add(coverage);
        var stamp=new org.xar.ck3.control.application.driver.DriverSnapshotFacts.Stamp(publication.afterVersion(),
                known.stamp().episodeEpoch(),known.stamp().game(),known.stamp().episodeRunId(),
                org.xar.ck3.control.application.driver.DriverJson.sha256(driver.encode()));
        var facts=new org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known(driver,stamp,known.originalHistoryBasis(),
                rows,known.auxiliary(),known.loop(),Optional.empty());
        return new RetainedReadDriver(facts,publication.afterDriver());
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
        var readPins=new java.util.ArrayList<WriterContracts.Pin>();var readDriver=new RetainedReadDriver(facts,manifest.fullDriver());
        same.requireHistoricalHead(capture.sequence(),previous);
        for(var edge:suffix) {
            StrictJson.require(ContinuityJson.digest(edge.before().toJson()).equals(previous),"captured suffix ancestry changed");
            var details=ContinuityJson.parseObject(edge.details(),ContinuityJson.LEDGER_MAX_BYTES);
            if(!edge.kind().equals(WriterContracts.DRIVER_READ_HISTORY_KIND)) {
                var beforeRead=edge.before().toJson();var afterRead=edge.after().toJson();
                StrictJson.require(beforeRead.has(WriterContracts.DRIVER_READ_HISTORY_FIELD)==afterRead.has(WriterContracts.DRIVER_READ_HISTORY_FIELD)
                        &&(!beforeRead.has(WriterContracts.DRIVER_READ_HISTORY_FIELD)||ContinuityJson.same(beforeRead.get(WriterContracts.DRIVER_READ_HISTORY_FIELD),
                        afterRead.get(WriterContracts.DRIVER_READ_HISTORY_FIELD))),"non-READ suffix changed the retained READ registry");
            }
            if(phase==3&&edge.kind().equals(OrdinaryCycleTransitions.CYCLE_KIND)) {
                transitions.requireInitialNoDispatchHistoryEdge(edge,owner,batch,controller.nextBatchSequence()+used.size()-capturedCount);retained=edge;deferredClosed=false;phase=1;
            }else if(phase==2&&edge.kind().equals(WriterContracts.DRIVER_READ_HISTORY_KIND)) {
                readDriver=retainCapturedRead(same,owner,edge,readDriver,originals,readPins,true);
            }else if(phase==1&&edge.kind().equals(org.xar.ck3.control.continuity.writer.DomainBodies.IMPORT_KIND)) {
                // Real historical import is retained; no replayed publication is produced.
            }else if(phase==2&&edge.kind().equals(org.xar.ck3.control.continuity.writer.DomainBodies.IMPORT_KIND)) {
                // Real historical domain import is retained; no replayed publication is produced.
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
        originalPins.addAll(readPins);for(var pin:readPins)same.verifyPin(pin);
        var result=new InitialNoDispatchRecovery(this,same,owner,state.sequence(),head.digest(),used,history,
                Optional.of(manifest),Optional.of(controller),Optional.of(facts),originalPins,Optional.of(capture.after()),open);
        result.retainedRecovery=retained;result.retainedFacts=Optional.of(readDriver.facts());result.retainedFullDriver=Optional.of(readDriver.fullDriver());
        return Optional.of(result);
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

    /** Eligibility to install read-only reconciliation of the exact original Life parent; grants no terminal or submit authority. */
    public static boolean isReadOnlyLifeRecovery(ActionReceipt receipt) {
        if (!(receipt.state() instanceof org.xar.ck3.control.application.action.ActionState.CompositeUnknown unknown)
                || !org.xar.ck3.control.application.advance.LifeAdvanceComposite.accepts(receipt.command().operation().value())
                || !unknown.execution().handlerId().equals(org.xar.ck3.control.application.advance.LifeAdvanceComposite.HANDLER)
                || unknown.execution().children().size() > 4) return false;
        var command = receipt.command();
        var guard = unknown.execution().guard();
        return command.origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay
                && command.origin().acceptsGuard(guard.origin())
                && guard.source().equals(command.source()) && guard.sessionId().equals(command.sessionId())
                && guard.operation().equals(command.operation()) && guard.observed().equals(command.before());
    }

    /** Canonical DATA admission only: retains the one Life parent and its finite control prefix for observation. */
    public static Optional<ActionReceipt> readOnlyLifeRecoveryRoot(java.util.List<ActionReceipt> canonicalActions) {
        canonicalActions = java.util.List.copyOf(canonicalActions);
        var roots = canonicalActions.stream().filter(action -> !action.settled() && isReadOnlyLifeRecovery(action)).toList();
        if (roots.size() != 1) return Optional.empty();
        var parent = roots.getFirst();
        var execution = ((org.xar.ck3.control.application.action.ActionState.CompositeUnknown) parent.state()).execution();
        try {
            var plan = org.xar.ck3.control.application.advance.AdvancePlan.decode(parent.command());
            StrictJson.require(parent.command().expected().observerSchema().equals(org.xar.ck3.control.application.advance.AdvancePlan.OBSERVER)
                    && parent.command().expected().values().equals(plan.expected())
                    && plan.startingDateRaw().equals(parent.command().before().frame().identity().dateRaw()),
                    "read-only Life recovery retains its original requested plan");
            var children = new java.util.ArrayList<ActionReceipt>();
            var admitted = new java.util.HashSet<String>();
            admitted.add(parent.command().actionId());
            boolean pause = false, speed = false, arm = false, cancel = false;
            for (var binding : execution.children()) {
                StrictJson.require(admitted.add(binding.actionId()), "duplicate or recursive Life child");
                var matches = canonicalActions.stream().filter(action -> action.command().actionId().equals(binding.actionId())).toList();
                StrictJson.require(matches.size() == 1, "original Life child is not uniquely canonical");
                var child = matches.getFirst();
                StrictJson.require(child.bodySha256().equals(binding.bodySha256()) && child.command().arguments().members().isEmpty()
                        && org.xar.ck3.control.application.action.ActionTransitions.composite(child.state()).isEmpty()
                        && (child.settled() || child.state() instanceof org.xar.ck3.control.application.action.ActionState.Unknown)
                        && org.xar.ck3.control.application.advance.AdvancePrimitives.expected(child.command().before(), child.command().source(),
                                child.command().operation(), child.command().arguments()).equals(child.command().expected()),
                        "read-only Life prefix retains its actual primitive child");
                String operation = child.command().operation().value();
                if (operation.equals("pause-map")) {
                    StrictJson.require(!pause && !speed && !arm && !cancel, "Life initialization pause order differs");
                    pause = true;
                } else if (operation.startsWith("set-speed-")) {
                    StrictJson.require(!speed && !arm && !cancel && operation.equals("set-speed-" + plan.speed()), "only the original finite Life control prefix can reconcile");
                    speed = true;
                } else if (operation.equals(plan.armStep())) {
                    StrictJson.require(!arm && !cancel && plan.clockMode() != org.xar.ck3.control.application.advance.AdvancePlan.ClockMode.POLLED, "only the original finite Life control prefix can reconcile");
                    arm = true;
                } else if (operation.startsWith(org.xar.ck3.control.application.advance.ClockStatusRead.CANCEL_PREFIX)) {
                    StrictJson.require(arm && !cancel, "Life cancellation requires its prior ARM");
                    // Validate the prefix (pause/speed/arm) is fully settled and canonical before accepting CANCEL
                    var prefixExecution = new org.xar.ck3.control.application.action.CompositeExecution(
                            execution.handlerId(), execution.startedAt(), execution.guard(),
                            execution.children().subList(0, children.size()));
                    org.xar.ck3.control.application.advance.LifeAdvanceComposite.requireArmedInitializationPrefix(
                            parent.command(), prefixExecution, children);
                    // Derive expected generation from the confirmed ARM
                    var armReceipt = children.getLast();
                    var armAck = org.xar.ck3.control.application.advance.AdvancePrimitives.acknowledgedSentinel(
                            armReceipt.ack().orElseThrow(), plan.armStep());
                    var expectedCancelOp = org.xar.ck3.control.application.advance.ClockStatusRead.CANCEL_PREFIX + armAck.generation().decimal();
                    StrictJson.require(operation.equals(expectedCancelOp), "Life cancellation targets another native generation");
                    cancel = true;
                } else {
                    StrictJson.require(false, "only the original finite Life control prefix can reconcile");
                }
                children.add(child);
            }
            long previousSequence = 0;
            var original = parent.command();
            for (var child : children) {
                var command = child.command();
                StrictJson.require(child.sequence() > previousSequence
                        && child.bodySha256().equals(org.xar.ck3.control.application.action.ActionCodec.bodySha256(command))
                        && command.origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay
                        && command.source().equals(original.source()) && command.sessionId().equals(original.sessionId())
                        && command.claims().equals(original.claims()) && (!command.deadline().isAfter(original.deadline())
                            || cancel && child == children.getLast()
                                && command.operation().value().startsWith(org.xar.ck3.control.application.advance.ClockStatusRead.CANCEL_PREFIX))
                        && command.before().game().equals(original.before().game())
                        && command.before().machineId().equals(original.before().machineId())
                        && command.before().frame().episodeRunId().equals(original.before().frame().episodeRunId())
                        && command.before().frame().identity().player().equals(original.before().frame().identity().player())
                        && command.before().frame().identity().dateRaw().compareTo(original.before().frame().identity().dateRaw()) >= 0
                        && command.before().frame().identity().nativeRevision().compareTo(original.before().frame().identity().nativeRevision()) >= 0,
                        "Life read-only child changed its original binding");
                previousSequence = child.sequence();
            }
            StrictJson.require(canonicalActions.stream().filter(action -> !action.settled())
                    .allMatch(action -> admitted.contains(action.command().actionId())), "another unresolved original remains outside the Life prefix");
            return Optional.of(parent);
        } catch (IllegalArgumentException rejected) {
            return Optional.empty();
        }
    }

    /** Ordinary immutable DATA for a living same Game after first primitive FOCUS became UNKNOWN. */
    public record UnresolvedSameGameData(CleanBatchRestart capturedManifest, ControllerRestartState capturedController,
            org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known retainedFacts, ExactRef retainedFullDriver,
            long canonicalSequence, String canonicalHeadDigest, java.util.List<String> usedBatches, long nextBatchSequence,
            java.util.List<org.xar.ck3.control.application.action.ActionReceipt> unresolvedActions, Optional<SettledSameGameData> retainedHistory) {
        public UnresolvedSameGameData {
            Objects.requireNonNull(capturedManifest); Objects.requireNonNull(capturedController);
            Objects.requireNonNull(retainedFacts); Objects.requireNonNull(retainedFullDriver);
            StrictJson.safe(canonicalSequence, 1); WriterContracts.requireDigest(canonicalHeadDigest);
            usedBatches = java.util.List.copyOf(usedBatches);
            StrictJson.safe(nextBatchSequence, 0);
            unresolvedActions = java.util.List.copyOf(unresolvedActions);
            retainedHistory = Objects.requireNonNull(retainedHistory);
        }
        public UnresolvedSameGameData(CleanBatchRestart capturedManifest, ControllerRestartState capturedController,
                org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known retainedFacts, ExactRef retainedFullDriver,
                long canonicalSequence, String canonicalHeadDigest, java.util.List<String> usedBatches, long nextBatchSequence,
                java.util.List<org.xar.ck3.control.application.action.ActionReceipt> unresolvedActions) {
            this(capturedManifest, capturedController, retainedFacts, retainedFullDriver, canonicalSequence, canonicalHeadDigest, usedBatches, nextBatchSequence, unresolvedActions, Optional.empty());
        }
    }

    /** Read original authenticated historical transitions; grants no readiness/submit/epoch token. */
    public UnresolvedSameGameData readUnresolvedSameGame(ContinuityStorePort.Session same, SessionIdentity owner) throws IOException {
        store.requireSession(same);
        Objects.requireNonNull(owner);
        var pendingControl = transitions.withLocked(same, () -> {
            var originals = transitions.restartArchive(same);
            var state = same.head().state();
            var pending = state.toJson().path(WriterContracts.ORDINARY_CYCLE_FIELD).get("pending_receipt");
            if (pending == null || pending.isNull()) return Optional.<ActionReceipt>empty();
            var actions = org.xar.ck3.control.application.action.ContinuityActionJournal.receipts(state, originals);
            return pendingCancelledLifeCycle(actions, ExactRef.fromJson(pending), originals);
        });
        if (pendingControl.isPresent()) {
            var captured = new java.util.concurrent.atomic.AtomicReference<CleanBatchRestart>();
            var retained = readSameGameHistory(same, owner, false, captured::set, pendingControl);
            StrictJson.require(captured.get() != null, "pending Life control cycle retains its actual restart capture");
            return new UnresolvedSameGameData(captured.get(), retained.controller(), retained.retainedFacts(),
                    retained.retainedFullDriver(), retained.canonicalSequence(), retained.canonicalHeadDigest(),
                    new java.util.ArrayList<>(retained.controller().usedBatches()), retained.controller().nextBatchSequence(),
                    java.util.List.of(pendingControl.orElseThrow()), Optional.of(retained));
        }
        var isolated = transitions.withLocked(same, () -> {
            var originals = transitions.restartArchive(same);
            var actions = org.xar.ck3.control.application.action.ContinuityActionJournal.receipts(same.head().state(), originals);
            return readOnlyLifeRecoveryRoot(actions).map(java.util.List::of).orElseGet(java.util.List::of);
        });
        if (!isolated.isEmpty()) {
            var captured = new java.util.concurrent.atomic.AtomicReference<CleanBatchRestart>();
            var retained = readSameGameHistory(same, owner, true, captured::set);
            StrictJson.require(captured.get() != null, "isolated Life recovery retains its actual restart capture");
            return new UnresolvedSameGameData(captured.get(), retained.controller(), retained.retainedFacts(),
                    retained.retainedFullDriver(), retained.canonicalSequence(), retained.canonicalHeadDigest(),
                    new java.util.ArrayList<>(retained.controller().usedBatches()), retained.controller().nextBatchSequence(),
                    isolated, Optional.of(retained));
        }
        return transitions.withLocked(same, () -> {
            var head = same.head();
            var state = head.state();
            var whole = state.toJson();

            // 1. Locate latest genuine WORKER_RESTART_CAPTURE canonical batch event
            var pins = new java.util.TreeMap<Long, WriterContracts.Pin>();
            var directory = java.nio.file.Path.of(same.persistedHead().path()).toAbsolutePath().normalize().resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS");
            for (var pin : head.documents()) {
                var p = java.nio.file.Path.of(pin.reference().path()).toAbsolutePath().normalize();
                if (p.getParent().equals(directory) && p.getFileName().toString().matches("[0-9]{8}\\.json")) {
                    StrictJson.require(pins.putIfAbsent(Long.parseLong(p.getFileName().toString().substring(0, 8)), pin) == null, "duplicate actual recovery event");
                }
            }
            java.util.List<WriterContracts.Pin> requestedPins = new java.util.ArrayList<>();
            for (long sequence = state.sequence(); sequence >= 1; sequence--) {
                var pin = pins.get(sequence);
                if (pin == null) break;
                requestedPins.add(pin);
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
                    capture = edge;
                    history.add(pin.reference());
                    break;
                }
                suffix.add(edge);
                history.add(pin.reference());
            }
            StrictJson.require(capture != null, "no genuine WORKER_RESTART_CAPTURE canonical batch event found");
            StrictJson.require(!suffix.isEmpty(), "captured recovery requires an actual unfinished original-action suffix");

            // 2. Decode real captured manifest/controller/Known/full Driver
            var originals = transitions.restartArchive(same);
            var captureDetails = ContinuityJson.parseObject(capture.details(), ContinuityJson.LEDGER_MAX_BYTES);
            StrictJson.require(OrdinaryCycleTransitions.sessionFromJson(captureDetails.get("session")).equals(owner), "captured recovery crossed owner");
            ExactRef manifestRef = ExactRef.fromJson(captureDetails.get("restart_manifest"));
            byte[] manifestBytes = originals.loadMaterial(manifestRef).bytes();
            var manifest = CleanBatchRestart.decode(manifestBytes);
            byte[] controllerBytes = originals.loadMaterial(manifest.controller()).bytes();
            var controller = ControllerRestartState.decode(controllerBytes);
            var knownOriginal = originals.loadFullMaterial(manifest.driverFacts());
            var facts = org.xar.ck3.control.application.driver.DriverSnapshotFacts.decodeKnownOriginal(knownOriginal, Optional.empty());
            byte[] full = originals.loadFullMaterial(manifest.fullDriver()).bytes();
            StrictJson.require(java.util.Arrays.equals(manifestBytes, manifest.encode()) && java.util.Arrays.equals(controllerBytes, controller.encode())
                    && sameKnownRestartOriginal(knownOriginal.bytes(), facts) && java.util.Arrays.equals(full, facts.driver().encode()), "actual captured originals differ");
            StrictJson.require(controller.owner().equals(owner) && manifest.previousTransport().game().equals(owner.game())
                    && manifest.previousTransport().machineId().equals(owner.machineId()) && manifest.previousTransport().sessionId().equals(owner.sessionId())
                    && facts.stamp().game().equals(owner.game()), "captured restart owner changed");
            StrictJson.require(!controller.quarantined() && !controller.localUnresolved() && !controller.stopRequested(),
                    "captured recovery cannot clear unresolved or stopped Controller state");
            transitions.requireCapturedRestartFrame(same, capture.after(), controller, manifest);
            StrictJson.require(facts.originalHistoryBasis().equals(ExactRef.fromJson(whole.get(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD))), "captured original history basis is no longer the actual baseline");

            // 3. Process suffix: allow only BATCH_STARTED/BATCH_INTERRUPTED, DOMAIN_IMPORT, ACTION_LIFECYCLE_KIND, DRIVER_READ_HISTORY_KIND
            var readDriver = new RetainedReadDriver(facts, manifest.fullDriver());
            String previous = ContinuityJson.digest(capture.after().toJson());
            String batch = null;
            int phase = 1;
            boolean deferredClosed = false;
            ExactRef retainedCycleReceipt = null;
            java.util.Collections.reverse(suffix);
            same.requireHistoricalHead(capture.sequence(), previous);

            var usedBatches = new java.util.ArrayList<String>(controller.usedBatches().stream().sorted().toList());
            var capturedCount = usedBatches.size();
            var currentReceipts = org.xar.ck3.control.application.action.ContinuityActionJournal.receipts(state, originals);

            for (var edge : suffix) {
                StrictJson.require(ContinuityJson.digest(edge.before().toJson()).equals(previous), "captured suffix ancestry changed");
                var details = ContinuityJson.parseObject(edge.details(), ContinuityJson.LEDGER_MAX_BYTES);

                if (edge.kind().equals(WriterContracts.DRIVER_READ_HISTORY_KIND)) {
                    readDriver = retainCapturedRead(same, owner, edge, readDriver, originals, java.util.List.of(), false);
                } else if (edge.kind().equals(WriterContracts.DRIVER_ACTION_HISTORY_KIND)) {
                    readDriver = retainCapturedAction(edge, readDriver, currentReceipts, originals);
                } else if (edge.kind().equals(org.xar.ck3.control.continuity.writer.DomainBodies.IMPORT_KIND)) {
                    // Real historical domain import is retained; no replayed publication is produced.
                } else if (edge.kind().equals(OrdinaryCycleTransitions.BATCH_KIND)) {
                    var boundary = StrictJson.text(details.get("boundary"));
                    StrictJson.require((phase == 1 ? JournalKind.BATCH_STARTED.name().equals(boundary)
                            : java.util.Set.of(JournalKind.BATCH_INTERRUPTED.name(), JournalKind.BATCH_DEFERRED.name()).contains(boundary))
                            && details.get("checkpoint_pair").isNull()
                            && details.get("completed_cycle_proof").isNull()
                            && OrdinaryCycleTransitions.sessionFromJson(details.get("session")).equals(owner), "captured suffix has another batch owner or credit");
                    String actual = StrictJson.text(details.get("batch_id"));
                    if (phase == 1) {
                        StrictJson.require(actual.equals(controller.batchPrefix() + "-" + (controller.nextBatchSequence() + usedBatches.size() - capturedCount)) && !usedBatches.contains(actual), "captured suffix skips or reuses a batch");
                        batch = actual;
                        usedBatches.add(actual);
                        phase = 2;
                    } else {
                        StrictJson.require(actual.equals(batch), "captured terminal batch differs");
                        deferredClosed = JournalKind.BATCH_DEFERRED.name().equals(boundary);
                        phase = deferredClosed ? 1 : 3;
                    }
                } else if (edge.kind().equals(OrdinaryCycleTransitions.CYCLE_KIND)) {
                    StrictJson.require(phase == 3 && batch != null,
                            "historical cycle requires the actual interrupted batch");
                    if ("RETAIN".equals(StrictJson.text(details.get("operation")))) {
                        StrictJson.require(retainedCycleReceipt == null
                                        && OrdinaryCycleTransitions.sessionFromJson(details.get("session")).equals(owner)
                                        && details.get("semantic").isNull()
                                        && details.get("cycle_record_ref").isNull()
                                        && details.get("cycle_record").isNull(),
                                "captured recovery accepts only one original unfinished cycle RETAIN");
                        var receiptRef = ExactRef.fromJson(details.get("receipt_ref"));
                        StrictJson.require(ExactRef.fromJson(edge.after().toJson().path(WriterContracts.ORDINARY_CYCLE_FIELD)
                                        .path("pending_receipt")).equals(receiptRef),
                                "historical RETAIN did not preserve its exact pending receipt");
                        retainedCycleReceipt = receiptRef;
                    } else {
                        long next = Math.addExact(controller.nextBatchSequence(), usedBatches.size() - capturedCount);
                        transitions.requireInitialNoDispatchHistoryEdge(edge, owner, batch, next);
                        batch = null;
                        phase = 1;
                    }
                } else if (edge.kind().equals(WriterContracts.ACTION_LIFECYCLE_KIND)) {
                    // Action edges do not replace Driver or original history basis
                } else {
                    StrictJson.require(false, "captured recovery refuses action/read/SAVE or unrelated suffix");
                }
                previous = ContinuityJson.digest(edge.after().toJson());
            }
            StrictJson.require(head.digest().equals(previous) && phase == 3 && state.status() == ContinuityState.Status.REPAIR_REQUIRED, "actual captured interrupted suffix required");

            // 4. Retain the original FOCUS even when its effect settled before an interrupted cycle could close.
            var unresolved = currentReceipts.stream().filter(r -> !r.settled()).toList();
            long captureSequence = capture.sequence();
            var focusAction = unresolved.size() == 1 ? unresolved.getFirst() : currentReceipts.stream()
                    .filter(r -> r.command().operation().value().equals("private-select-player-lifestyle-stock-focus-v1")
                            && r.outcome() == org.xar.ck3.control.application.action.ActionReceipt.Outcome.APPLIED_CONFIRMED
                            && r.sequence() > captureSequence)
                    .max(java.util.Comparator.comparingLong(org.xar.ck3.control.application.action.ActionReceipt::sequence)).orElse(null);
            StrictJson.require(focusAction != null
                    && focusAction.command().operation().value().equals("private-select-player-lifestyle-stock-focus-v1")
                    && (focusAction.settled() ? unresolved.isEmpty()
                            : unresolved.size() == 1 && focusAction.state() instanceof org.xar.ck3.control.application.action.ActionState.Unknown),
                    "same-game recovery requires the one original FOCUS, unresolved or already applied before cycle closure");
            if (retainedCycleReceipt != null) StrictJson.require(focusAction.settled()
                            && retainedCycleReceipt.equals(originals.receiptReferenceOf(focusAction)),
                    "historical unfinished cycle RETAIN differs from the original settled FOCUS receipt");
            StrictJson.require(focusAction.command().origin().machineId().equals(owner.machineId())
                    && focusAction.command().origin().game().equals(owner.game())
                    && focusAction.command().sessionId().equals(owner.sessionId()), "FOCUS action crossed owner");
            StrictJson.require(focusAction.command().source().equals(manifest.source()), "FOCUS action source crossed manifest");
            StrictJson.require(focusAction.command().before().frame().identity().player().equals(facts.driver().session().actorId())
                    && focusAction.command().before().frame().episodeRunId().equals(facts.stamp().episodeRunId()), "FOCUS action crossed retained Known");
            StrictJson.require(org.xar.ck3.control.application.action.ActionTransitions.attempt(focusAction.state()).isPresent(), "FOCUS action lacks actual Attempt");
            StrictJson.require(org.xar.ck3.control.application.action.ActionTransitions.composite(focusAction.state()).isEmpty(), "FOCUS action has unexpected composite");
            var dispatch = org.xar.ck3.control.application.action.ActionTransitions.dispatch(focusAction.state()).orElse(null);
            StrictJson.require(dispatch instanceof org.xar.ck3.control.application.action.NativeActionPort.AckReceived ack && ack.nativeOk(), "FOCUS action lacks original positive ACK");

            // 5. Compute usedBatches and nextBatchSequence
            var nextSeq = controller.nextBatchSequence() + (usedBatches.size() - capturedCount);

            // Original bytes above were decoded through the exact archive under this writer lock.
            StrictJson.require(same.head().digest().equals(head.digest()) && same.head().state().sequence() == state.sequence(), "canonical recovery head changed during read");
            return new UnresolvedSameGameData(manifest, controller, readDriver.facts(), readDriver.fullDriver(),
                    state.sequence(), head.digest(), usedBatches, nextSeq, java.util.List.of(focusAction));
        });
    }
    /** Read-only reconstruction; this DATA is neither a clean ticket nor a replay permission. */
    public record SettledSameGameData(
            org.xar.ck3.control.continuity.ObservedGameplayEntry.Details entry,
            ControllerRestartState controller,
            org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known retainedFacts,
            ExactRef retainedFullDriver,
            org.xar.ck3.control.application.action.NativeObservationPort.TransportSession previousTransport,
            org.xar.ck3.control.g2.common.G2Source source,
            SemanticEvidence latestCycleSemantic,
            ObservationIdentity latestObservedFrame,
            java.util.List<ActionReceipt> settledActions,
            long canonicalSequence, String canonicalHeadDigest, java.util.List<ExactRef> history) {
        public SettledSameGameData {
            Objects.requireNonNull(entry);Objects.requireNonNull(controller);Objects.requireNonNull(retainedFacts);
            Objects.requireNonNull(retainedFullDriver);Objects.requireNonNull(previousTransport);
            Objects.requireNonNull(source);Objects.requireNonNull(latestCycleSemantic);Objects.requireNonNull(latestObservedFrame);
            settledActions=java.util.List.copyOf(settledActions);history=java.util.List.copyOf(history);
            StrictJson.safe(canonicalSequence,1);WriterContracts.requireDigest(canonicalHeadDigest);
        }
    }

    private SettledSameGameData committedSettledSameGameData;
    private WriterContracts.Receipt committedSettledSameGameReceipt;
    private SettledSameGameData issuedSettledSameGameData;
    private WriterContracts.HistoricalTransition issuedSettledSameGameRecovery;
    private boolean issuedSettledSameGameOpenBatch;
    private long acceptedSettledSameGameSequence;
    private String acceptedSettledSameGameDigest;

    public Optional<WriterContracts.Receipt> recoverSettledSameGame(ContinuityStorePort.Session same,
            SettledSameGameData data, SemanticEvidence fresh) throws IOException {
        store.requireSession(same);Objects.requireNonNull(data);Objects.requireNonNull(fresh);
        return transitions.withLocked(same,()->{
            StrictJson.require(committedSettledSameGameData==null&&data==issuedSettledSameGameData,
                    "settled recovery binds this journal's actual read DATA once");
            requireSettledObservedContinuation(data.latestObservedFrame(),fresh.frame());
            if(same.head().state().status()==ContinuityState.Status.RUNNING&&!issuedSettledSameGameOpenBatch) {
                StrictJson.require(issuedSettledSameGameRecovery!=null,"READY recovery requires its actual committed history");
                transitions.requireSettledSameGameReady(same,data,fresh,issuedSettledSameGameRecovery);
                committedSettledSameGameData=data;
                acceptedSettledSameGameSequence=data.canonicalSequence();
                acceptedSettledSameGameDigest=data.canonicalHeadDigest();
                return Optional.empty();
            }
            var receipt=issuedSettledSameGameOpenBatch
                    ?transitions.commitSettledSameGameRecovery(same,data,fresh,issuedSettledSameGameRecovery)
                    :transitions.commitSettledSameGameRecovery(same,data,fresh);
            committedSettledSameGameData=data;committedSettledSameGameReceipt=receipt;
            acceptedSettledSameGameSequence=receipt.head().sequence();
            acceptedSettledSameGameDigest=ContinuityJson.digest(receipt.head().toJson());
            return Optional.of(receipt);
        });
    }

    void requireSettledSameGameRecovery(ContinuityStorePort.Session same,SettledSameGameData data,
            SessionIdentity owner) throws IOException {
        store.requireSession(same);
        StrictJson.require(data==committedSettledSameGameData&&acceptedSettledSameGameDigest!=null
                &&data.controller().owner().equals(owner),"Controller must restore this journal's actual settled recovery");
        same.requireDomainImportContinuation(acceptedSettledSameGameSequence,acceptedSettledSameGameDigest);
    }

    /** Historical observation DATA stays separate from the immutable completed-cycle SEM. */
    private static void requireSettledObservedContinuation(ObservationIdentity retained,ObservationIdentity next) {
        var before=retained.frame();var after=next.frame();
        StrictJson.require(retained.machineId().equals(next.machineId())&&retained.game().equals(next.game())
                &&retained.observationVersion()==next.observationVersion()
                &&before.identity().player().equals(after.identity().player())
                &&before.episodeRunId().equals(after.episodeRunId())
                &&after.identity().dateRaw().compareTo(before.identity().dateRaw())>=0
                &&after.identity().nativeRevision().compareTo(before.identity().nativeRevision())>=0
                &&after.revision().compareTo(before.revision())>=0,
                "settled recovery observation regressed its actual Game, subject, version, date or revision");
    }

    private static org.xar.ck3.control.application.action.NativeObservationPort.TransportSession settledSemanticTransport(
            SemanticEvidence semantic,SessionIdentity owner,
            org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive originals) {
        var body=DriverJson.object(originals.loadFullMaterial(semantic.semantic()).bytes(),DriverJson.MAX_NATIVE_BYTES);
        var manifestRef=DriverObservationEvidenceReader.reference(body.get("java_driver_facts_evidence"));
        var manifest=originals.loadFullMaterial(manifestRef);
        var transport=org.xar.ck3.control.application.driver.DriverObservationEvidenceReader.nativeFrame(
                manifestRef,manifest,originals.loadNativeFrame(semantic.originalNativePacket())).session();
        StrictJson.require(transport.machineId().equals(owner.machineId())&&transport.game().equals(owner.game())
                &&transport.sessionId().equals(owner.sessionId()),"settled semantic packet crossed the actual Game");
        return transport;
    }

    /** Replays the actual capability/persistent owner captured by a completed cycle, without reinitializing the episode. */
    private static RetainedReadDriver retainSettledCapabilities(SemanticEvidence semantic,RetainedReadDriver previous,
            org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive originals) {
        var body=DriverJson.object(originals.loadFullMaterial(semantic.semantic()).bytes(),DriverJson.MAX_NATIVE_BYTES);
        var manifestRef=DriverObservationEvidenceReader.reference(body.get("java_driver_facts_evidence"));
        var manifest=originals.loadFullMaterial(manifestRef);
        var actual=DriverObservationEvidenceReader.nativeFrame(manifestRef,manifest,originals.loadNativeFrame(semantic.originalNativePacket()));
        var observed=DriverObservationEvidenceReader.decode(manifestRef,manifest,originals.loadFullMaterial(semantic.originalDriver()),actual);
        var sourceValue=observed.originalSemanticFields().get(DriverCapabilityStateProducer.STATE_SOURCE);
        if(sourceValue==null)return previous;
        var known=previous.facts();
        StrictJson.require(observed.driverVersion()==known.stamp().driverVersion()
                &&observed.episodeEpoch()==known.stamp().episodeEpoch()
                &&java.util.Arrays.equals(observed.driver().encode(),known.driver().encode()),
                "settled capability source crossed the retained complete Driver");
        var source=DriverObservationEvidenceReader.reference(sourceValue);
        var state=DriverJson.object(originals.loadFullMaterial(source).bytes(),DriverJson.MAX_NATIVE_BYTES);
        var originalManifestRef=DriverObservationEvidenceReader.reference(state.get("semantic_source"));
        var originalManifest=originals.loadFullMaterial(originalManifestRef);
        var originalNative=DriverObservationEvidenceReader.nativeFrame(originalManifestRef,originalManifest,
                originals.loadNativeFrame(semantic.originalNativePacket()));
        var originalFacts=DriverObservationEvidenceReader.decode(originalManifestRef,originalManifest,
                originals.loadFullMaterial(previous.fullDriver()),originalNative);
        var originalKnown=new DriverSnapshotFacts.Known(known.driver(),known.stamp(),known.originalHistoryBasis(),
                known.actionRows(),known.auxiliary(),known.loop(),Optional.of(originalFacts));
        var projected=new DriverObservationAssembler().assemble(originalNative,originalFacts,semantic.originalNativePacket());
        StrictJson.require(projected instanceof DriverObservationAssembler.Complete,
                "settled capability source lost its original complete physical frame");
        var restored=DriverCapabilityStateProducer.replay((DriverObservationAssembler.Complete)projected,originalKnown,source,originals);
        for(var field:restored.members().entrySet())StrictJson.require(
                Objects.equals(observed.originalSemanticFields().get(field.getKey()),field.getValue()),
                "settled capability replay differs from the actual cycle observation: "+field.getKey());
        return new RetainedReadDriver(new DriverSnapshotFacts.Known(known.driver(),known.stamp(),known.originalHistoryBasis(),
                known.actionRows(),restored,known.loop(),Optional.empty()),previous.fullDriver());
    }

    public SettledSameGameData readSettledSameGame(ContinuityStorePort.Session same,
            SessionIdentity owner) throws IOException {
        return readSameGameHistory(same, owner, false, ignored -> { });
    }

    /** Canonical timeline children remain facts, but their ordinary parent owns cycle credit. */
    static java.util.List<ActionReceipt> ordinaryCycleRoots(java.util.List<ActionReceipt> actions) {
        return ordinaryCycleRoots(actions, false);
    }
    /** The isolated Life path observes its exact canonical control children without inventing their own ordinary cycle. */
    static java.util.List<ActionReceipt> ordinaryCycleRoots(java.util.List<ActionReceipt> actions, boolean isolatedLife) {
        var children=new java.util.HashSet<org.xar.ck3.control.application.action.CompositeExecution.Child>();
        if (isolatedLife) {
            var root = readOnlyLifeRecoveryRoot(actions).orElseThrow();
            var execution = ((org.xar.ck3.control.application.action.ActionState.CompositeUnknown) root.state()).execution();
            for (var binding : execution.children()) {
                var actual = actions.stream().filter(action -> action.command().actionId().equals(binding.actionId())
                        && action.bodySha256().equals(binding.bodySha256())).findFirst().orElseThrow();
                if (actual.state() instanceof org.xar.ck3.control.application.action.ActionState.Settled settled
                        && (settled.settlement() instanceof org.xar.ck3.control.application.action.ActionState.Applied
                        || settled.settlement() instanceof org.xar.ck3.control.application.action.ActionState.PauseConfirmed)) children.add(binding);
            }
        }
        for(var action:actions) {
            if(action.state() instanceof org.xar.ck3.control.application.action.ActionState.CompositeSettled settled)
                children.addAll(settled.execution().children());
        }
        return actions.stream().filter(action->{
            var command=action.command();
            if(!children.contains(new org.xar.ck3.control.application.action.CompositeExecution.Child(
                    command.actionId(),action.bodySha256())))return true;
            if(!org.xar.ck3.control.application.advance.AdvancePrimitives.supports(command.operation())
                    ||!command.arguments().members().isEmpty())return true;
            return !org.xar.ck3.control.application.advance.AdvancePrimitives.expected(command.before(),command.source(),
                    command.operation(),command.arguments()).equals(command.expected());
        }).toList();
    }

    /** A completed source-owned cancellation may still have its original RETAIN awaiting ordinary semantic settlement. */
    static Optional<ActionReceipt> pendingCancelledLifeCycle(java.util.List<ActionReceipt> actions, ExactRef pending,
            org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive originals) {
        if (actions.isEmpty() || actions.stream().anyMatch(action -> !action.settled())) return Optional.empty();
        var actual = originals.loadReceipt(pending);
        if (!actions.contains(actual) || actual.outcome() != ActionReceipt.Outcome.APPLIED_CONFIRMED
                || actual.visibleGameplay() || actual.eligibleAdvance()
                || !(actual.state() instanceof org.xar.ck3.control.application.action.ActionState.CompositeSettled settled)
                || !(settled.settlement() instanceof org.xar.ck3.control.application.action.ActionState.CompositeControlApplied control)
                || !org.xar.ck3.control.application.advance.LifeAdvanceComposite.accepts(actual.command().operation().value())
                || !settled.execution().handlerId().equals(org.xar.ck3.control.application.advance.LifeAdvanceComposite.HANDLER)
                || !control.observation().semantic().actual().contains(new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedText(
                        new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("progress_status"), "initialization_cancelled")))
            return Optional.empty();
        var children = settled.execution().children().stream().map(bound -> actions.stream()
                .filter(child -> child.command().actionId().equals(bound.actionId()) && child.bodySha256().equals(bound.bodySha256()))
                .findFirst().orElseThrow()).toList();
        org.xar.ck3.control.application.advance.LifeAdvanceComposite.requireCancelledInitialization(
                actual.command(), settled.execution(), control.observation(), children);
        return Optional.of(actual);
    }

    private SettledSameGameData readSameGameHistory(ContinuityStorePort.Session same,
            SessionIdentity owner, boolean isolatedLife, java.util.function.Consumer<CleanBatchRestart> captures) throws IOException {
        return readSameGameHistory(same, owner, isolatedLife, captures, Optional.empty());
    }
    private SettledSameGameData readSameGameHistory(ContinuityStorePort.Session same,
            SessionIdentity owner, boolean isolatedLife, java.util.function.Consumer<CleanBatchRestart> captures,
            Optional<ActionReceipt> pendingControl) throws IOException {
        store.requireSession(same);Objects.requireNonNull(owner);Objects.requireNonNull(pendingControl);
        return transitions.withLocked(same,()->{
            var head=same.head();var state=head.state();var whole=state.toJson();
            StrictJson.require((state.status()==ContinuityState.Status.REPAIR_REQUIRED||state.status()==ContinuityState.Status.RUNNING)
                    &&state.settledCycles()==0,"settled initial recovery retains the unsaved interrupted frontier");
            var entry=org.xar.ck3.control.continuity.ObservedGameplayEntry.decode(
                    whole.get(WriterContracts.GAMEPLAY_ENTRY_FIELD));
            StrictJson.require(entry.machineId().equals(owner.machineId())&&entry.game().equals(owner.game())
                    &&entry.sessionId().equals(owner.sessionId()),"settled recovery crossed the actual Game owner");
            var originals=transitions.restartArchive(same);
            var actions=org.xar.ck3.control.application.action.ContinuityActionJournal.receipts(state,originals);
            if (isolatedLife) {
                StrictJson.require(readOnlyLifeRecoveryRoot(actions).isPresent(),
                        "isolated recovery retains one exact Life original and its canonical control prefix");
            } else {
                StrictJson.require(!actions.isEmpty()&&actions.stream().allMatch(ActionReceipt::settled),
                        "settled recovery cannot discard an unresolved action");
            }
            if (pendingControl.isPresent()) {
                var ref = ExactRef.fromJson(whole.path(WriterContracts.ORDINARY_CYCLE_FIELD).get("pending_receipt"));
                StrictJson.require(!isolatedLife && pendingCancelledLifeCycle(actions, ref, originals).equals(pendingControl),
                        "pending Life control cycle changed its exact canonical receipt or complete source proof");
            }
            for(var action:actions)StrictJson.require(action.command().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay
                    &&action.command().origin().machineId().equals(owner.machineId())
                    &&action.command().origin().game().equals(owner.game())
                    &&action.command().sessionId().equals(owner.sessionId()),
                    "settled recovery action crossed the current gameplay owner");
            var source=actions.getFirst().command().source();
            StrictJson.require(actions.stream().allMatch(action->action.command().source().equals(source)),
                    "settled recovery cannot merge different original sources");
            var openingRef=ExactRef.fromJson(whole.path(org.xar.ck3.control.continuity.writer.DomainBodies.FIELD)
                    .path("entries").path("OPENING_GATE").get("payload"));
            var opening=org.xar.ck3.control.application.planning.governance.GovernanceOpeningDocument.decode(
                    originals.loadMaterial(openingRef).bytes());
            StrictJson.require(opening.stage()==org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.OpeningStage.COMPLETE
                    &&opening.sessionId().equals(owner.sessionId())&&opening.source().equals(source)
                    &&opening.checkpoint().isEmpty()&&opening.actionReceipt().isPresent()
                    &&actions.contains(originals.loadReceipt(opening.actionReceipt().orElseThrow())),
                    "settled recovery must retain the actually consumed opening action without a SAVE");

            // Start from the actual first-map Known, then apply already committed Driver DATA.
            var knownOriginal=originals.loadFullMaterial(entry.driverFacts());
            var observationRef=org.xar.ck3.control.application.driver.DriverSnapshotFacts
                    .observationOriginalReference(knownOriginal).orElseThrow(
                            ()->new IOException("initial settled recovery observation DATA unavailable"));
            var observationOriginal=originals.loadFullMaterial(observationRef);
            var initialFull=originals.loadFullMaterial(entry.fullDriver());
            var nativeFrame=org.xar.ck3.control.application.driver.DriverObservationEvidenceReader.nativeFrame(
                    observationRef,observationOriginal,originals.loadNativeFrame(entry.nativeFrame()));
            var observation=org.xar.ck3.control.application.driver.DriverObservationEvidenceReader.decode(
                    observationRef,observationOriginal,initialFull,nativeFrame);
            var known=org.xar.ck3.control.application.driver.DriverSnapshotFacts.decodeKnownOriginal(
                    knownOriginal,Optional.of(observation));
            StrictJson.require(known.originalHistoryBasis().equals(entry.fullDriver())
                    &&java.util.Arrays.equals(known.driver().encode(),initialFull.bytes())
                    &&known.stamp().game().equals(owner.game()),
                    "initial settled recovery full Driver differs from its original entry");

            var directory=java.nio.file.Path.of(same.persistedHead().path()).toAbsolutePath().normalize()
                    .resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS");
            var pins=new java.util.TreeMap<Long,WriterContracts.Pin>();
            for(var pin:head.documents()) {
                var path=java.nio.file.Path.of(pin.reference().path()).toAbsolutePath().normalize();
                if(directory.equals(path.getParent())&&path.getFileName().toString().matches("[0-9]{8}\\.json"))
                    pins.put(Long.parseLong(path.getFileName().toString().substring(0,8)),pin);
            }
            var requested=new java.util.ArrayList<WriterContracts.Pin>();
            for(long sequence=1;sequence<=state.sequence();sequence++) {
                var pin=pins.get(sequence);
                StrictJson.require(pin!=null,"settled initial recovery requires its actual canonical event history");
                requested.add(pin);
            }
            var edges=same.readHistoricalTransitions(requested);
            var retained=new RetainedReadDriver(known,entry.fullDriver());
            var latestObserved=new ObservationIdentity(owner.machineId(),owner.game(),
                    new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame(
                            new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(
                                    java.math.BigInteger.valueOf(entry.actorId()),entry.nativeRevision(),java.math.BigInteger.valueOf(entry.dateRaw())),
                            entry.snapshotId(),java.math.BigInteger.valueOf(entry.revision()),entry.episodeId()),observation.observationVersion());
            var previousTransport=nativeFrame.session();
            WriterContracts.HistoricalTransition retainedRecovery=null;
            var used=new java.util.LinkedHashSet<String>();
            String batchPrefix=null,openBatch=null;
            var history=new java.util.ArrayList<ExactRef>();
            var cycleReceipts=new java.util.HashSet<ExactRef>();
            ExactRef pending=null,lastCycleRef=null;
            SemanticEvidence latest=null;
            long completedCycles=0;
            for(int i=0;i<edges.size();i++) {
                var edge=edges.get(i);history.add(requested.get(i).reference());
                var details=ContinuityJson.parseObject(edge.details(),ContinuityJson.LEDGER_MAX_BYTES);
                if(edge.kind().equals(org.xar.ck3.control.continuity.ObservedGameplayEntry.KIND)) {
                    StrictJson.require(edge.sequence()==1,"settled initial recovery has another gameplay entry");
                } else if(edge.kind().equals(WriterContracts.DRIVER_READ_HISTORY_KIND)) {
                    retained=retainCapturedRead(same,owner,edge,retained,originals,java.util.List.of(),false);
                    for(var row:details.get("read_rows")) {
                        var read=originals.loadRead(ExactRef.fromJson(row.get("read")));
                        for(var guard:java.util.List.of(read.before().binding(),read.after().binding())) {
                            requireSettledObservedContinuation(latestObserved,guard.observed());
                            latestObserved=guard.observed();
                            previousTransport=new org.xar.ck3.control.application.action.NativeObservationPort.TransportSession(
                                    owner.machineId(),owner.game(),guard.connectionGeneration(),owner.sessionId());
                        }
                    }
                } else if(edge.kind().equals(WriterContracts.DRIVER_ACTION_HISTORY_KIND)) {
                    retained=retainCapturedAction(edge,retained,actions,originals);
                } else if(edge.kind().equals(org.xar.ck3.control.continuity.writer.DomainBodies.IMPORT_KIND)) {
                    // Domain DATA does not submit another gameplay action.
                } else if(edge.kind().equals(WriterContracts.ACTION_LIFECYCLE_KIND)) {
                    // The canonical action journal owns these transitions. Current receipts above
                    // must all be settled; the original cycle edges below retain their own credit.
                } else if(edge.kind().equals(OrdinaryCycleTransitions.BATCH_KIND)) {
                    StrictJson.require(OrdinaryCycleTransitions.sessionFromJson(details.get("session")).equals(owner)
                            &&details.get("checkpoint_pair").isNull()&&details.get("completed_cycle_proof").isNull(),
                            "settled initial recovery cannot replace a saved or foreign batch");
                    String boundary=StrictJson.text(details.get("boundary")),batch=StrictJson.text(details.get("batch_id"));
                    if(JournalKind.BATCH_STARTED.name().equals(boundary)) {
                        if(batchPrefix==null) {
                            StrictJson.require(batch.endsWith("-0"),"initial recovery batch sequence must start at zero");
                            batchPrefix=batch.substring(0,batch.length()-2);
                        }
                        StrictJson.require(openBatch==null&&batch.equals(batchPrefix+"-"+used.size())&&used.add(batch),
                                "settled recovery cannot reuse or skip an actual batch");
                        openBatch=batch;
                    } else if(JournalKind.WORKER_RESTART_CAPTURE.name().equals(boundary)) {
                        StrictJson.require(openBatch==null&&pending==null&&batchPrefix!=null,
                                "settled restart capture requires its actual idle batch frontier");
                        var manifest=CleanBatchRestart.decode(originals.loadMaterial(ExactRef.fromJson(details.get("restart_manifest"))).bytes());
                        var captured=ControllerRestartState.decode(originals.loadMaterial(manifest.controller()).bytes());
                        StrictJson.require(captured.owner().equals(owner)&&captured.batchPrefix().equals(batchPrefix)
                                &&captured.nextBatchSequence()==used.size()&&captured.usedBatches().equals(used)
                                &&batch.equals(batchPrefix+":restart:"+captured.nextBatchSequence())
                                &&captured.savedPair().isEmpty()&&!captured.quarantined()&&!captured.localUnresolved()
                                &&!captured.stopRequested(),"settled restart capture differs from its actual retained Controller");
                        transitions.requireCapturedRestartFrame(same,edge.after(),captured,manifest);
                        var capturedOriginal=originals.loadFullMaterial(manifest.driverFacts());
                        var capturedKnown=DriverSnapshotFacts.decodeKnownOriginal(capturedOriginal,Optional.empty());
                        byte[] capturedFull=originals.loadFullMaterial(manifest.fullDriver()).bytes();
                        StrictJson.require(sameKnownRestartOriginal(capturedOriginal.bytes(),capturedKnown)
                                &&java.util.Arrays.equals(capturedFull,capturedKnown.driver().encode())
                                &&java.util.Arrays.equals(capturedFull,retained.facts().driver().encode())
                                &&capturedKnown.stamp().equals(retained.facts().stamp())
                                &&capturedKnown.originalHistoryBasis().equals(retained.facts().originalHistoryBasis())
                                &&capturedKnown.actionRows().equals(retained.facts().actionRows())
                                &&manifest.source().equals(source)&&manifest.previousTransport().machineId().equals(owner.machineId())
                                &&manifest.previousTransport().game().equals(owner.game())
                                &&manifest.previousTransport().sessionId().equals(owner.sessionId()),
                                "settled restart capture changed its original Driver/action/source owner");
                        retained=new RetainedReadDriver(capturedKnown,manifest.fullDriver());
                        previousTransport=manifest.previousTransport();
                        captures.accept(manifest);
                    } else {
                        boolean closed=JournalKind.BATCH_INTERRUPTED.name().equals(boundary)
                                ||retainedRecovery!=null&&java.util.Set.of(JournalKind.BATCH_FINISHED.name(),
                                        JournalKind.BATCH_DEFERRED.name()).contains(boundary);
                        StrictJson.require(closed&&batch.equals(openBatch),
                                "settled recovery requires its actual closed batch terminal boundary");
                        openBatch=null;
                    }
                } else if(edge.kind().equals(OrdinaryCycleTransitions.CYCLE_KIND)) {
                    String operation=StrictJson.text(details.get("operation"));
                    if("SETTLED_SAME_GAME_RECOVERY".equals(operation)) {
                        StrictJson.require((openBatch==null||retainedRecovery!=null&&openBatch.equals(used.getLast()))
                                &&pending==null&&latest!=null&&!used.isEmpty()
                                &&StrictJson.text(details.get("batch_id")).equals(used.getLast())
                                &&StrictJson.integer(details.get("next_sequence"),1,StrictJson.MAX_SAFE_INTEGER)==used.size()
                                &&ExactRef.fromJson(details.get("cycle_record_ref")).equals(lastCycleRef),
                                "settled recovery history changed its completed cycle or consumed batches");
                        transitions.requireSettledSameGameHistoryEdge(edge,owner);
                        var recovered=OrdinaryCycleTransitions.semanticFromJson(details.get("semantic"));
                        requireSettledObservedContinuation(latestObserved,recovered.frame());
                        latestObserved=recovered.frame();
                        previousTransport=settledSemanticTransport(recovered,owner,originals);
                        // This real canonical recovery row closes an unfinished read-only batch.
                        openBatch=null;
                        retainedRecovery=edge;
                        continue;
                    }
                    var receiptRef=ExactRef.fromJson(details.get("receipt_ref"));
                    boolean retainedControl = pendingControl.isPresent() && "RETAIN".equals(operation)
                            && receiptRef.equals(originals.receiptReferenceOf(pendingControl.orElseThrow()))
                            && edge.after().status() == ContinuityState.Status.REPAIR_REQUIRED;
                    StrictJson.require((openBatch!=null || retainedControl)
                            && OrdinaryCycleTransitions.sessionFromJson(details.get("session")).equals(owner),
                            "settled cycle crossed its real active batch or original retained control");
                    if("RETAIN".equals(operation)) {
                        StrictJson.require(pending==null,"settled recovery cannot overwrite a pending cycle");
                        pending=receiptRef;
                    } else {
                        StrictJson.require("SETTLE".equals(operation)&&receiptRef.equals(pending)&&cycleReceipts.add(receiptRef),
                                "settled recovery cannot repeat or skip the original cycle");
                        var receipt=originals.loadReceipt(receiptRef);
                        StrictJson.require(actions.contains(receipt)&&receipt.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED,
                                "settled cycle must retain its original applied action");
                        var record=details.get("cycle_record");
                        String classification=receipt.eligibleAdvance()?"ELIGIBLE_ADVANCE":receipt.visibleGameplay()?"VISIBLE_GAMEPLAY":"CONTROL_ONLY";
                        completedCycles=Math.addExact(completedCycles,"CONTROL_ONLY".equals(classification)?0:1);
                        StrictJson.require(StrictJson.text(record.get("classification")).equals(classification)
                                &&StrictJson.integer(record.get("completed_cycles"),0,StrictJson.MAX_SAFE_INTEGER)==completedCycles
                                &&ExactRef.fromJson(record.get("receipt_ref")).equals(receiptRef),
                                "settled recovery cannot grant new cycle credit");
                        latest=OrdinaryCycleTransitions.semanticFromJson(details.get("semantic"));
                        retained=retainSettledCapabilities(latest,retained,originals);
                        requireSettledObservedContinuation(latestObserved,latest.frame());
                        latestObserved=latest.frame();
                        previousTransport=settledSemanticTransport(latest,owner,originals);
                        lastCycleRef=ExactRef.fromJson(details.get("cycle_record_ref"));
                        pending=null;
                    }
                } else {
                    throw new IOException("settled initial recovery cannot reinterpret canonical transition "+edge.kind());
                }
            }
            var cycle=whole.get(WriterContracts.ORDINARY_CYCLE_FIELD);
            StrictJson.require(state.status()!=ContinuityState.Status.RUNNING||retainedRecovery!=null,
                    "READY settled recovery requires its actual prior recovery transition");
            boolean unfinishedReadOnlyBatch=openBatch!=null;
            boolean retainedControl = pendingControl.isPresent() && pending != null
                    && pending.equals(originals.receiptReferenceOf(pendingControl.orElseThrow()))
                    && pending.equals(ExactRef.fromJson(cycle.get("pending_receipt")));
            StrictJson.require((!unfinishedReadOnlyBatch||retainedRecovery!=null&&state.status()==ContinuityState.Status.RUNNING)
                    &&!used.isEmpty()&&(pending==null || retainedControl)&&latest!=null
                    &&(cycle.get("pending_receipt").isNull() || retainedControl)
                    &&StrictJson.integer(cycle.get("completed_cycles"),0,StrictJson.MAX_SAFE_INTEGER)==completedCycles
                    &&ExactRef.fromJson(cycle.get("head")).equals(lastCycleRef),
                    "settled recovery requires the actual closed cycle frontier");
            var unsaved=new java.util.LinkedHashSet<String>();boolean dirty=false;int eligible=0;
            for(var action:ordinaryCycleRoots(actions, isolatedLife)) {
                if(!action.visibleGameplay()&&!action.eligibleAdvance())continue;
                StrictJson.require(cycleReceipts.contains(originals.receiptReferenceOf(action)),
                        "settled gameplay action lacks its already completed ordinary cycle");
                if(unsaved.add(action.command().actionId())) {
                    dirty|=action.visibleGameplay();
                    if(action.eligibleAdvance())eligible=Math.addExact(eligible,1);
                }
            }
            var controller=new ControllerRestartState(owner,batchPrefix,used.size(),used,unsaved,
                    Optional.empty(),Optional.of(same.persistedHead()),eligible,dirty,false,false,0,
                    java.util.Set.of(),false);
            StrictJson.require(same.head().state().sequence()==state.sequence()&&same.head().digest().equals(head.digest()),
                    "settled canonical recovery head changed during read");
            var data=new SettledSameGameData(entry,controller,retained.facts(),retained.fullDriver(),previousTransport,
                    source,latest,latestObserved,actions,state.sequence(),head.digest(),history);
            if (isolatedLife || pendingControl.isPresent()) return data; // Pending cycle DATA is not a settled recovery or ordinary Ready grant.
            issuedSettledSameGameData=data;issuedSettledSameGameRecovery=retainedRecovery;
            issuedSettledSameGameOpenBatch=unfinishedReadOnlyBatch;
            return data;
        });
    }

    /** Closes only a verified canonical no-write original through the existing all-settled recovery transition. */
    public JournalCommit recoverNoGameplaySameGame(SessionIdentity owner, ActionReceipt actual, SemanticEvidence fresh) throws IOException {
        return recoverLifeTerminalSameGame(owner, actual, fresh, false);
    }

    /** Resumes ordinary planning only after the actual control prefix has settled without calendar credit. */
    public JournalCommit recoverLifeControlPrefixSameGame(SessionIdentity owner, ActionReceipt actual, SemanticEvidence fresh) throws IOException {
        return recoverLifeTerminalSameGame(owner, actual, fresh, true);
    }

    private JournalCommit recoverLifeTerminalSameGame(SessionIdentity owner, ActionReceipt actual, SemanticEvidence fresh,
            boolean controlPrefix) throws IOException {
        Objects.requireNonNull(owner);Objects.requireNonNull(actual);Objects.requireNonNull(fresh);
        return store.locked(same -> {
            transitions.withLocked(same, () -> {
                StrictJson.require(actual.state() instanceof org.xar.ck3.control.application.action.ActionState.CompositeSettled,
                        "read-only recovery needs its actual composite terminal");
                var settled = (org.xar.ck3.control.application.action.ActionState.CompositeSettled) actual.state();
                StrictJson.require(actual.outcome() == ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT,
                        "read-only recovery cannot reinterpret another action outcome");
                var originals = transitions.restartArchive(same);
                var actions = org.xar.ck3.control.application.action.ContinuityActionJournal.receipts(same.head().state(), originals);
                if (controlPrefix) {
                    StrictJson.require(settled.settlement() instanceof org.xar.ck3.control.application.action.ActionState.LifeControlPrefixInterrupted,
                            "actual source-owned Life prefix terminal required");
                    var prefix = (org.xar.ck3.control.application.action.ActionState.LifeControlPrefixInterrupted) settled.settlement();
                    prefix.observation().validateParent(actual.command(), settled.execution());
                    var children = new java.util.ArrayList<ActionReceipt>();
                    for (var binding : settled.execution().children()) {
                        var child = actions.stream().filter(receipt -> receipt.command().actionId().equals(binding.actionId())).findFirst().orElseThrow();
                        StrictJson.require(child.bodySha256().equals(binding.bodySha256()), "canonical Life child body changed");
                        children.add(child);
                    }
                    prefix.observation().validateChildren(actual.command(), children);
                } else {
                    StrictJson.require(settled.settlement() instanceof org.xar.ck3.control.application.action.ActionState.CompositeNoGameplayWrite,
                            "actual canonical no-write terminal required");
                    var noGameplay = (org.xar.ck3.control.application.action.ActionState.CompositeNoGameplayWrite) settled.settlement();
                    noGameplay.observation().validate(actual.command(), settled.execution());
                }
                var canonical = actions.stream().filter(receipt -> receipt.command().actionId().equals(actual.command().actionId())).findFirst().orElseThrow();
                StrictJson.require(canonical.equals(actual), "read-only recovery retains the complete actual canonical terminal");
                return true;
            });
            var data = readSettledSameGame(same, owner);
            recoverSettledSameGame(same, data, fresh);
            long delta = same.head().state().settledDateRaw() - same.head().state().origin().startDateRaw();
            StrictJson.require(delta >= 0 && delta % 24 == 0, "actual committed saved-day accounting differs");
            return new JournalCommit(same.persistedHead(), delta / 24);
        });
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
