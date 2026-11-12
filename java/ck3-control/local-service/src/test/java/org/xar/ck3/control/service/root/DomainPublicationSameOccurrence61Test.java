package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.InterruptedIOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector;
import org.xar.ck3.control.application.planning.governance.*;
import org.xar.ck3.control.governance.activity.ActivityPlannerDiagnostic;
import org.xar.ck3.control.planning.optionalcadence.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;
import org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier;
import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.application.planning.OrdinaryPolicy.*;
import static org.xar.ck3.control.application.session.SessionPorts.*;

/** Real software Native READ/ACK -> publisher/CAS -> actual collector -> planner/Controller -> one Native ACK.
 * Controlled selection is not a live LLM/Game gameplay or day-advance qualification. */
final class DomainPublicationSameOccurrence61Test {
    @TempDir Path directory;
    private static final byte[] SEED=StrictJson.canonical(StrictJson.object().put("schema","controlled-same-occurrence-cadence-seed-v1"));
    private static final String PROFILE="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";

    @Test void readThenDomainPublicationRejoinBeforeOnlyCurrentProposalCanBeSelected() throws Exception {
        var definitions=new AtomicReference<FinanceReadContracts>(); var source=new AtomicReference<ExactRef>();
        var cadencePublisher=new AtomicReference<GovernanceCadencePublication>();
        var baseline=new AtomicReference<CadenceModels.State>();
        RawJson packet;
        try(var input=getClass().getResourceAsStream("/org/xar/ck3/control/application/driver/campaign-root-native-v1-fixture.json")) {
            if(input==null)throw new IOException("existing complete ROOT software packet resource missing");packet=new RawJson(input.readAllBytes());
        }
        var nativeReads=new ActionWriterIntegrationFixture.SoftwareReadScenario(PROFILE,"read-planning-handoff",ref->{
            source.set(ref);var actual=new FinanceReadContracts(query->{String permission="game.command."+query.operation().value();
                return new FinanceReadContracts.Registration(ref,new FinanceReadContracts.Permission(Optional.of(permission),permission,
                        ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP));});
            definitions.set(actual);return List.of(actual.contract(FinanceReadContracts.Query.ROOT));
        },request->packet,Optional.of("1.20.0.4"),Set.of());
        var operation=new OperationKey("pause-map");
        var action=new ActionWriterIntegrationFixture.SoftwareActionScenario(operation,"game.command.pause-map",
                (command,attempt,dispatch)->new ActionPorts.Pending("controlled actual ACK retained, semantic outcome remains UNKNOWN",List.of(attempt.guard().nativeEvidence())),
                ()->{},Optional.empty(),Optional.empty(),true);
        var installedActions=withFeastActions(action);
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("actual-writer"),false,nativeReads,installedActions,List.of(),ref->List.of(
                new DomainBodies.Registration(DomainBodies.Slot.OPTIONAL_CADENCE,CadenceModels.SCHEMA,1_048_576,List.of(ref),seedVerifier(cadencePublisher,baseline))))) {
            var publisher=new DriverReadHistoryPublisher(fixture.driverAuthority(),fixture.archive,fixture.reads.catalog(),List.of(source.get()));
            fixture.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_READ_HISTORY_KIND,publisher);
            fixture.bindKnownReadObserver(publisher::enqueue);
            var verifier=new NativeSemanticEvidenceVerifier((same,ref,max)->fixture.archive.readArtifact(same,ref,max));
            var cycles=new OrdinaryCycleTransitions(fixture.archive,verifier,(same,owner,pair,proof)->{throw new AssertionError("no SAVE");},
                    new OriginalWindowReducer.Policy(10958),fixture.writer::requireSession);
            cycles.bindTerminalFrameLoader(fixture.frameLoader());
            for(String kind:cycles.kinds())fixture.bindAdditionalTransitionAuthority(kind,cycles);
            var batches=new ContinuityBatchJournal(fixture.writer,cycles);
            var initial=fixture.ready();
            var replay=new GovernanceCadenceReplay(()->active(fixture),fixture.writer::requireSession,
                    (same,ref)->fixture.archive.readArtifact(same,ref,1_048_576));
            var cadence=new GovernanceCadencePublication(fixture.root.resolve("ROOT-CONTINUITY-WINDOW.lock").toAbsolutePath(),
                    fixture.writer::requireSession,List.of(source.get()),replay,
                    (id,bytes)->fixture.archive.withSession(active(fixture)).preserveMaterial(new RawJson(bytes)));
            cadencePublisher.set(cadence);baseline.set(CadenceModels.State.empty(initial.request().before().frame().episodeRunId()));
            seed(fixture,baseline.get(),source.get());
            var feast=replay.record(new OrdinaryFeastPolicy(source.get(),replay.observe(new ActualFeastInputs(fixture,source.get())),
                    (ignoredOperation,request,args)->Optional.empty()));
            fixture.writer.locked(same->fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(60),lease->{
                var config=new DynamicCapabilities.Configuration(Optional.empty(),Optional.empty(),3,3,false,false);
                var presentation=new CapabilitySessionPresentation(false,Optional.empty(),Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
                        CapabilitySessionPresentation.BindingState.ACTIVE_NEW,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
                var policy=fixture.archive.preserveMaterial(new RawJson(DriverJson.encode(new OpportunityJson.Obj(Map.of("software_start",new OpportunityJson.Bool(true))))));
                var produced=DriverCapabilityStateProducer.initializeNewEpisode(lease.frame(),lease.driver(),config,presentation,policy,fixture.archive.withSession(same));
                fixture.driverAuthority().publishCapabilityInputs(same,lease.driver().stamp(),produced.expectedAuxiliarySha256(),produced);return null;
            }));
            var held=new AtomicReference<ContinuityStorePort.Session>();
            var prepared=new AtomicReference<OrdinaryPlanCompletion.SelectionDisposition>();
            var domainPublications=new AtomicInteger();var originalExpiry=new AtomicReference<Instant>();
            var governance=new GovernancePlanCompletion(held::get,fixture.writer::requireSession,cadence,replay);
            var changed=new AtomicReference<Optional<OrdinaryPlanCompletion.Published>>(Optional.empty());
            var originalRead=new AtomicReference<PlanningReadResult.Known<FinanceReadContracts.Packet>>();
            var firstTemporary=new AtomicReference<ActionCommand>();var selected=new AtomicReference<ActionCommand>();
            var actualRootReads=new ArrayList<PlanningReadResult.Known<FinanceReadContracts.Packet>>();
            var rootReadDomainPhases=new ArrayList<Integer>();var proposedCommands=new ArrayList<ActionCommand>();
            var initialHistory=initial.request().observations().history();
            var proposals=new AtomicInteger();var selections=new AtomicInteger();var publications=new AtomicInteger();
            OrdinaryPlanCompletion.PlanningScope completion=new OrdinaryPlanCompletion.PlanningScope(){
                private Optional<Published> flush()throws IOException {
                    var actual=publisher.flushActualReads(held.get()).map(value->new Published(value.predecessor(),value.actual()));
                    if(actual.isPresent()){changed.set(actual);publications.incrementAndGet();
                        fixture.driverAuthority().withFrozenFacts(held.get(),frozen->{assertTrue(((DriverSnapshotFacts.Known)frozen.state()).observation().isEmpty());return null;});}
                    return actual;
                }
                public <T>ScopeResult<T> inPlanningScope(ScopeWork<T> work)throws IOException,InterruptedException {
                    try{return fixture.writer.locked(same->{held.set(same);try {
                        return fixture.collector.withPlanningRound(same,()->RootReadPublicationCompletion.finishPlanningReads(()->{
                            changed.set(Optional.empty());prepared.set(null);return RootReadPublicationCompletion.finishOriginalWork(work,this::flush,()->false);
                        },()->changed.get().isPresent(),()->{
                            assertTrue(changed.get().isEmpty(),"real READ publication must short-circuit prepared-selection supplier");return prepared.get();
                        },()->fixture.collector.prepareReadPublicationReplan(same)));
                    }catch(InterruptedException interrupted){var failure=new InterruptedIOException("actual planning interrupted");failure.initCause(interrupted);throw failure;}
                    finally{held.set(null);}});}catch(InterruptedIOException failure){throw (InterruptedException)failure.getCause();}
                }
                public Optional<Published> beforeSelection(PlanningRequest request,PlanningResult.ActionSelected proposed){
                    try{return flush();}catch(IOException failure){throw new UncheckedIOException(failure);}
                }
                public SelectionDisposition beforeModel(PlanningRequest request,PlanningResult.ActionSelected proposed){
                    var actual=governance.beforeModel(request,proposed);
                    if(actual instanceof Published||actual instanceof Blocked)prepared.set(actual);
                    if(actual instanceof Published)domainPublications.incrementAndGet();return actual;
                }
                public PlanningDisposition afterPlanning(PlanningRequest request,PlanningResult planned){
                    if(prepared.get() instanceof Published actual)return actual;
                    if(prepared.get() instanceof Blocked actual)return actual;
                    if(changed.get().isPresent())return changed.get().orElseThrow();
                    return governance.afterPlanning(request,planned);
                }
                public ExecutionDisposition afterExecution(ActionReceipt actual){return new Unchanged("original ACK/UNKNOWN consumed once");}
            };
            var realm=new RealmLifecycle(source.get());
            var policies=Arrays.stream(PlanningStage.values()).<OrdinaryPolicy>map(stage->{
                if(stage==PlanningStage.REALM_MEMBERSHIP_PUBLICATION)return realm;
                return new OrdinaryPolicy(){public PlanningStage stage(){return stage;}public ExactRef implementationSource(){return source.get();}
                    public Decision evaluate(PlanningRequest input,Draft previous){
                        if(stage!=PlanningStage.ORDINARY_CORE)return new Keep("other software stages retain the actual proposal");
                        try{fixture.collector.current(held.get(),input.before(),input.deadline(),lease->{
                            var contract=definitions.get().contract(FinanceReadContracts.Query.ROOT);
                            var query=new PlanningReadRequest(input.before(),input.source(),input.sessionId(),contract.operation(),FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.PUBLIC_QUERY),input.deadline());
                            var canonical=publisher.canonicalReadWitness(held.get(),contract,query);
                            if(canonical.isPresent())assertEquals(originalRead.get().originalReceipt(),canonical.orElseThrow().requireCurrent(held.get(),contract,query).originalReceipt());
                            else {var actual=definitions.get().read(held.get(),FinanceReadContracts.Query.ROOT,fixture.reads,input);
                                if(!(actual instanceof PlanningReadResult.Known<FinanceReadContracts.Packet> known))throw new AssertionError(actual);
                                originalRead.set(known);actualRootReads.add(known);rootReadDomainPhases.add(domainPublications.get());}
                            return null;
                        });}catch(IOException failure){throw new UncheckedIOException(failure);}
                        originalExpiry.compareAndSet(null,input.deadline());assertEquals(originalExpiry.get(),input.deadline());
                        var noAction=assertInstanceOf(OrdinaryPolicy.Annotate.class,feast.evaluate(input,advanceDraft(input)));
                        int number=proposals.incrementAndGet();
                        var expected=new ProposalLifecycle.ExpectedPostcondition(1,input.before(),input.source(),"paused/v1",List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"),true)));
                        var command=new ActionCommand("actual-root-read-handoff-"+number,input.before(),input.source(),input.sessionId(),operation,new OpportunityJson.Obj(Map.of()),expected,
                                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),input.deadline());
                        firstTemporary.compareAndSet(null,command);proposedCommands.add(command);
                        return new Replace(new Draft("actual-read-handoff","ordinary","native software action after canonical READ",Kind.ORDINARY,Optional.of(command),Purpose.WORLD_ACTION,Optional.empty(),noAction.retained().detail()),"actual current proposal carrying the original producer transcript");
                    }};
            }).toList();
            var planner=new OrdinaryPlanner(policies,Clock.systemUTC(),realm);
            planner.bindSelector((request,proposal)->{
                assertFalse(publisher.hasPending(held.get()));
                var history=request.observations().history();
                assertEquals(initialHistory,history.subList(0,initialHistory.size()),"the complete original history prefix is retained");
                var appended=history.subList(initialHistory.size(),history.size());
                assertEquals(actualRootReads.size(),appended.size());
                // The first ROOT is before the domain import; its old READ-only lineage cannot be
                // reused across that real import. The second ROOT is a new original, not a replay.
                assertEquals(List.of(0,1),rootReadDomainPhases);
                var receiptRefs=new HashSet<ExactRef>();
                for(int i=0;i<appended.size();i++) {
                    var row=org.xar.ck3.control.application.history.DriverReadHistoryRowProducer.decode(DriverJson.encode(appended.get(i)));
                    var actual=actualRootReads.get(i);var sourceRow=row.provenance();
                    assertEquals(FinanceReadContracts.Query.ROOT.operation().value(),row.command());assertTrue(row.ok());
                    assertEquals(org.xar.ck3.control.application.history.DriverReadHistoryRowProducer.Kind.CAMPAIGN_ROOT_CONTEXT,sourceRow.kind());
                    assertEquals(actual.originalReceipt(),sourceRow.originalReceipt());assertTrue(receiptRefs.add(sourceRow.originalReceipt()));
                    assertEquals(actual.receipt(),fixture.archive.loadRead(sourceRow.originalReceipt()));
                    assertEquals(actual.originalReceipt(),fixture.archive.readReferenceOf(actual.receipt()));
                    assertEquals(definitions.get().contract(FinanceReadContracts.Query.ROOT).contractId(),sourceRow.contractId());
                    assertEquals(actual.receipt().requestId(),sourceRow.requestId());
                    assertEquals(actual.receipt().request().before(),sourceRow.sourceFrame());
                }
                assertEquals(publications.get()+domainPublications.get()+1,proposals.get());
                assertEquals(proposals.get(),proposedCommands.size());assertSame(proposedCommands.getLast(),proposal.command());
                for(int i=0;i<proposedCommands.size()-1;i++)assertNotSame(proposedCommands.get(i),proposal.command());
                assertNotSame(firstTemporary.get(),proposal.command());
                selections.incrementAndGet();selected.set(proposal.command());return new OrdinaryDecisionSelector.Selection(OrdinaryDecisionSelector.Choice.ACCEPT,"controlled exact proposal",Optional.empty());
            });
            CheckpointFiles files=new CheckpointFiles(){
                public Optional<CheckpointPair.FileWitness> observe(Path path){throw new AssertionError("no SAVE");}
                public byte[] read(CheckpointPair.FileWitness value,int max){throw new AssertionError("no SAVE");}
                public CheckpointPair.FileWitness replace(Path path,byte[] bytes){throw new AssertionError("no SAVE");}
                public CheckpointPair.FileWitness createNew(Path path,byte[] bytes){throw new AssertionError("no SAVE");}
                public CheckpointPair.FileWitness copyNew(CheckpointPair.FileWitness value,Path path){throw new AssertionError("no SAVE");}
            };
            var snapshots=new DriverCheckpointStore.SnapshotSupplier(){public <T>T withFrozen(DriverCheckpointStore.SnapshotWork<T> work){throw new AssertionError("no SAVE");}};
            var drivers=new DriverCheckpointStore(files,directory.resolve("unused-driver.json"),"unused-pipe",snapshots);
            CheckpointRequest.ObservationPort save=until->{throw new AssertionError("no SAVE");};
            var checkpoint=new CheckpointService(files,drivers,save,directory.resolve("unused-evidence"),Clock.systemUTC(),(pair,receipt)->{throw new AssertionError("no SAVE");});
            var owner=fixture.observationIdentity();
            var coordinator=new ActionCoordinatorPort(){
                public ActionReceipt execute(ActionCommand command){assertSame(selected.get(),command);return fixture.coordinator.execute(command);}
                public ActionReceipt reconcile(String id){throw new AssertionError("UNKNOWN must not replay/reconcile automatically");}
            };
            var controller=new SessionController(owner,(actual,until)->new GameLifecycle.Running(owner.game(),source.get()),
                    new ObservationPort() {
                        public Observation observe(SessionIdentity actual,Instant until)throws IOException,InterruptedException {
                            return fixture.collector.observe(held.get(),actual,until);
                        }
                        public Observation observe(SessionIdentity actual,Instant readinessUntil,Instant planningUntil)throws IOException,InterruptedException {
                            assertTrue(readinessUntil.isBefore(planningUntil),"readiness acquisition and full planning budgets differ");
                            Observation result=fixture.collector.observe(held.get(),actual,readinessUntil,planningUntil);
                            if(result instanceof Ready ready)assertEquals(planningUntil,ready.request().deadline(),"publish the actual full planning deadline through the same Native producer");
                            return result;
                        }
                    },planner,coordinator,checkpoint,
                    new CheckpointRequestFactory(directory.resolve("unused.ck3"),save),batches,work->{throw new AssertionError("no incident");},
                    new SessionClock.SystemClock(),Optional.empty(),0,completion,(actual,receipt,until)->{throw new AssertionError("no episode");});
            controller.bindRetainedIncidents(List::of);controller.bindRestartDriver(fixture.driverAuthority());
            var report=controller.autoTurn(Instant.now().plusSeconds(120)).execution();
            assertEquals(actualRootReads.size(),fixture.scenarioReadWrites());assertEquals(actualRootReads.size(),publications.get());
            assertEquals(publications.get()+domainPublications.get()+1,proposals.get());assertEquals(1,selections.get());
            assertEquals(1,fixture.nativeActionWrites(),()->report.terminal()+":"+report.detail());assertEquals(1,report.turns().size());
            assertEquals(1,domainPublications.get());
            fixture.writer.locked(same->{var state=CadenceJson.readState(available(same).canonicalBody(),baseline.get().episodeRunId());
                assertEquals(1,state.row(CadenceModels.Domain.FEAST).consecutiveNoAction());
                assertTrue(state.row(CadenceModels.Domain.FEAST).nextDueDateRaw().isEmpty());return null;});
            var receipt=report.turns().getFirst().receipt();
            assertTrue(assertInstanceOf(NativeActionPort.AckReceived.class,ActionTransitions.dispatch(receipt.state()).orElseThrow()).nativeOk());
            assertEquals(ActionCodec.bodySha256(selected.get()),receipt.bodySha256());
            assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,report.terminal());assertTrue(controller.isQuarantined());
            var refused=controller.autoTurn(Instant.now().plusSeconds(1)).execution();
            assertEquals(BatchReport.Terminal.INTERNAL_FAILURE,refused.terminal());
            assertTrue(refused.turns().isEmpty());assertEquals(1,fixture.nativeActionWrites());
        }
    }


    @Test void actualSameOccurrenceDeduplicatesAndOnlyNewNativeMarkersReachOriginalThirdMissCooldown() throws Exception {
        try(var env=new CadenceEnvironment(directory.resolve("actual-cadence-markers"))) {
            env.fixture.writer.locked(same->{
                try{return env.fixture.collector.withPlanningRound(same,()->{
                    Instant until=Instant.now().plusSeconds(60);
                    var packet=env.fixture.physicalInputs().transport().currentSnapshot(until);
                    var passes=new AtomicInteger();
                    var prepared=new AtomicReference<OrdinaryPlanCompletion.SelectionDisposition>();
                    var requests=new ArrayList<PlanningRequest>();
                    var completed=RootReadPublicationCompletion.finishPlanningReads(()->{
                        prepared.set(null);passes.incrementAndGet();
                        var request=env.observe(same,until);requests.add(request);
                        var plan=env.produce(same,request);
                        prepared.set(env.publish(same,plan));
                        return new OrdinaryPlanCompletion.ScopeResult<>(plan,Optional.empty());
                    },()->false,prepared::get,()->env.fixture.collector.prepareReadPublicationReplan(same));
                    assertEquals(2,passes.get());assertInstanceOf(OrdinaryPlanCompletion.Unchanged.class,prepared.get());
                    assertSame(packet,env.fixture.physicalInputs().transport().currentSnapshot(until));
                    assertEquals(requests.getFirst().before().frame().identity().nativeRevision(),requests.getLast().before().frame().identity().nativeRevision());
                    assertEquals(until,requests.getFirst().deadline());assertEquals(until,requests.getLast().deadline());
                    assertEquals(1,env.state(same).row(CadenceModels.Domain.FEAST).consecutiveNoAction());
                    assertTrue(env.state(same).row(CadenceModels.Domain.FEAST).nextDueDateRaw().isEmpty());
                    assertEquals(env.state(same),GovernanceCadencePublication.reduce(completed.value()));
                    var previousRequest=requests.getLast();
                    for(int expectedCount:List.of(2,0)) {
                        assertTrue(env.fixture.collector.prepareReadPublicationReplan(same));
                        ObservedFrame next=env.newNativeMarker(packet,until);assertNotSame(packet,next);
                        var request=env.observe(same,until);assertEquals(until,request.deadline());
                        assertNotEquals(previousRequest.before().frame().identity().nativeRevision(),request.before().frame().identity().nativeRevision());
                        var staleConsumer=new AtomicInteger();var staleRequest=previousRequest;
                        assertThrows(IllegalArgumentException.class,()->env.fixture.collector.current(same,staleRequest.before(),until,lease->{staleConsumer.incrementAndGet();return null;}));
                        assertEquals(0,staleConsumer.get());
                        var plan=env.produce(same,request);assertInstanceOf(OrdinaryPlanCompletion.Published.class,env.publish(same,plan));
                        var row=env.state(same).row(CadenceModels.Domain.FEAST);assertEquals(expectedCount,row.consecutiveNoAction());
                        if(expectedCount==2)assertTrue(row.nextDueDateRaw().isEmpty());
                        else assertEquals(Optional.of(request.before().frame().identity().dateRaw().add(java.math.BigInteger.valueOf(720))),row.nextDueDateRaw());
                        packet=next;previousRequest=request;
                    }
                    assertEquals(0,env.fixture.nativeActionWrites());return null;
                });}catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException(interrupted);}
            });
        }
    }

    @Test void expiredActualCallerDeadlineNeverEntersProducerOrReselectsAndRoundCannotEscape() throws Exception {
        try(var env=new CadenceEnvironment(directory.resolve("actual-expired-caller"))) {
            var escaped=new AtomicReference<PlanningRequest>();
            env.fixture.writer.locked(same->{
                try{return env.fixture.collector.withPlanningRound(same,()->{
                    var request=env.observe(same,Instant.now().plusSeconds(60));escaped.set(request);
                    int packets=env.fixture.nativePacketReads();String head=same.head().digest();var entered=new AtomicInteger();
                    var failure=assertThrows(ContractViolationException.class,()->env.fixture.collector.current(same,request.before(),Instant.now().minusSeconds(1),lease->{entered.incrementAndGet();env.produce(same,request);return null;}));
                    assertEquals("caller readiness deadline expired before any native query",failure.getMessage());
                    assertEquals(0,entered.get());assertEquals(packets,env.fixture.nativePacketReads());assertEquals(head,same.head().digest());
                    assertEquals(0,env.inputs.plannerReads);assertEquals(0,env.fixture.nativeActionWrites());return null;
                });}catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException(interrupted);}
            });
            env.fixture.writer.locked(same->{assertFalse(env.fixture.collector.prepareReadPublicationReplan(same),"the previous writer round cannot be revived");return null;});
            assertNotNull(escaped.get());
        }
    }

    @Test void actualProducerFailureUnwindsThenFlushesAndBlockedDoesNotInvokeRejoin() throws Exception {
        try(var env=new CadenceEnvironment(directory.resolve("actual-producer-failure"))) {
            env.inputs.failPlanner=true;
            env.fixture.writer.locked(same->{
                try{return env.fixture.collector.withPlanningRound(same,()->{
                    String head=same.head().digest();var order=new ArrayList<String>();
                    var original=assertThrows(IllegalStateException.class,()->RootReadPublicationCompletion.finishPlanningReads(()->
                        RootReadPublicationCompletion.finishOriginalWork(()->{
                            order.add("work");var request=env.observe(same,Instant.now().plusSeconds(60));return env.produce(same,request);
                        },()->{
                            order.add("flush");assertEquals(1,env.inputs.plannerReads);
                            env.fixture.driverAuthority().withFrozenFacts(same,frozen->{assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state());return null;});
                            assertEquals(head,same.head().digest());return Optional.empty();
                        },()->false),()->{throw new AssertionError("failed work cannot inspect READ state");},
                        ()->{throw new AssertionError("failed work cannot inspect prepared selection");},
                        ()->{throw new AssertionError("failed producer cannot rejoin");}));
                    assertSame(env.inputs.plannerFailure,original);assertEquals(List.of("work","flush"),order);
                    assertEquals(head,same.head().digest());assertEquals(0,env.state(same).row(CadenceModels.Domain.FEAST).consecutiveNoAction());
                    return null;
                });}catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException(interrupted);}
            });
            assertEquals(0,env.fixture.nativeActionWrites());
        }
        // Real policy transcript, deliberately rebound only in this negative DATA input. No positive
        // issuer or acceptance is fabricated: the actual completion must reject the changed session.
        try(var env=new CadenceEnvironment(directory.resolve("actual-blocked-session"))) {
            env.fixture.writer.locked(same->{
                try{return env.fixture.collector.withPlanningRound(same,()->{
                    var request=env.observe(same,Instant.now().plusSeconds(60));
                    var retained=env.fixture.collector.current(same,request.before(),request.deadline(),lease->
                            assertInstanceOf(OrdinaryPolicy.Annotate.class,env.feast.evaluate(request,advanceDraft(request))).retained());
                    assertTrue(GovernanceCadencePublication.fromDetail(retained.detail()).isPresent());
                    var proposed=new PlanningResult.ActionSelected(retained.command().orElseThrow(),new PlanTrace(request.before(),List.of(),Optional.of(retained)));
                    var rebound=new PlanningRequest(request.before(),request.source(),request.sessionId()+"-rebound",request.deadline(),request.observations());
                    var completion=new GovernancePlanCompletion(()->same,env.fixture.writer::requireSession,env.publication,env.replay);
                    String head=same.head().digest();var blocked=assertInstanceOf(OrdinaryPlanCompletion.Blocked.class,completion.beforeModel(rebound,proposed));
                    assertTrue(blocked.reason().contains("actual cadence plan source/session differs"));
                    var result=RootReadPublicationCompletion.finishPlanningReads(()->new OrdinaryPlanCompletion.ScopeResult<>(blocked,Optional.empty()),
                            ()->false,()->blocked,()->{throw new AssertionError("actual Blocked must never rejoin");});
                    assertSame(blocked,result.value());assertEquals(head,same.head().digest());
                    assertEquals(0,env.state(same).row(CadenceModels.Domain.FEAST).consecutiveNoAction());
                    assertEquals(0,env.fixture.nativeActionWrites());return null;
                });}catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException(interrupted);}
            });
        }
        try(var env=new CadenceEnvironment(directory.resolve("actual-replan-io"))) {
            env.fixture.writer.locked(same->{
                try{return env.fixture.collector.withPlanningRound(same,()->{
                    var prepared=new AtomicReference<OrdinaryPlanCompletion.SelectionDisposition>();var calls=new AtomicInteger();
                    var order=new ArrayList<String>();var original=new IOException("actual original rejoin IO failure");
                    var actual=assertThrows(IOException.class,()->RootReadPublicationCompletion.finishPlanningReads(()->{
                        order.add("work");calls.incrementAndGet();prepared.set(null);
                        var request=env.observe(same,Instant.now().plusSeconds(60));var plan=env.produce(same,request);
                        prepared.set(env.publish(same,plan));return new OrdinaryPlanCompletion.ScopeResult<>(plan,Optional.empty());
                    },()->false,prepared::get,()->{
                        order.add("replan");assertTrue(env.fixture.collector.prepareReadPublicationReplan(same));throw original;
                    }));
                    assertSame(original,actual);assertEquals(1,calls.get());assertEquals(List.of("work","replan"),order);
                    assertInstanceOf(OrdinaryPlanCompletion.Published.class,prepared.get());
                    assertEquals(1,env.state(same).row(CadenceModels.Domain.FEAST).consecutiveNoAction());
                    assertEquals(0,env.fixture.nativeActionWrites());return null;
                });}catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException(interrupted);}
            });
        }
        var order=new ArrayList<String>();var original=new IOException("original work failed");var flush=new IOException("original flush failed");
        assertSame(original,assertThrows(IOException.class,()->RootReadPublicationCompletion.finishPlanningReads(()->
            RootReadPublicationCompletion.finishOriginalWork(()->{order.add("work");throw original;},()->{order.add("flush");throw flush;},()->false),
            ()->{throw new AssertionError("failed flush cannot inspect READ state");},()->{throw new AssertionError("failed flush cannot inspect prepared selection");},
            ()->{throw new AssertionError("failed flush cannot invoke replan");})));
        assertEquals(List.of("work","flush"),order);assertArrayEquals(new Throwable[]{flush},original.getSuppressed());
    }

    /** Real same-writer domain verifier and original policy transcript; no positive Plan is constructed here. */
    private static final class CadenceEnvironment implements AutoCloseable {
        final ActionWriterIntegrationFixture fixture;
        final ExactRef source;
        final GovernanceCadenceReplay replay;
        final GovernanceCadencePublication publication;
        final ActualFeastInputs inputs;
        final OrdinaryPolicy feast;
        final CadenceModels.State baseline;
        CadenceEnvironment(Path root)throws Exception {
            var sourceRef=new AtomicReference<ExactRef>();var publisherRef=new AtomicReference<GovernanceCadencePublication>();
            var initialState=new AtomicReference<CadenceModels.State>();
            var reads=new ActionWriterIntegrationFixture.SoftwareReadScenario(PROFILE,"actual-cadence-rejoin",ref->{sourceRef.set(ref);return List.of();},
                    ignored->new RawJson(new byte[]{'{','}'}),Optional.of("1.20.0.4"),Set.of());
            var never=new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("pause-map"),"game.command.pause-map",
                    (command,attempt,dispatch)->{throw new AssertionError("cadence DATA must not submit");},()->{throw new AssertionError("no business action");});
            fixture=new ActionWriterIntegrationFixture(root,false,reads,withFeastActions(never),List.of(),ref->List.of(
                    new DomainBodies.Registration(DomainBodies.Slot.OPTIONAL_CADENCE,CadenceModels.SCHEMA,1_048_576,List.of(ref),seedVerifier(publisherRef,initialState))));
            source=Objects.requireNonNull(sourceRef.get());
            var ready=fixture.ready();baseline=CadenceModels.State.empty(ready.request().before().frame().episodeRunId());initialState.set(baseline);
            replay=new GovernanceCadenceReplay(()->active(fixture),fixture.writer::requireSession,(same,ref)->fixture.archive.readArtifact(same,ref,1_048_576));
            publication=new GovernanceCadencePublication(fixture.root.resolve("ROOT-CONTINUITY-WINDOW.lock").toAbsolutePath(),fixture.writer::requireSession,
                    List.of(source),replay,(id,bytes)->fixture.archive.withSession(active(fixture)).preserveMaterial(new RawJson(bytes)));
            publisherRef.set(publication);seed(fixture,baseline,source);
            inputs=new ActualFeastInputs(fixture,source);
            feast=replay.record(new OrdinaryFeastPolicy(source,replay.observe(inputs),(ignoredOperation,request,args)->Optional.empty()));
        }
        PlanningRequest observe(ContinuityStorePort.Session same,Instant until)throws IOException,InterruptedException {
            return assertInstanceOf(Ready.class,fixture.collector.observe(same,fixture.observationIdentity(),until)).request();
        }
        GovernanceCadencePublication.Plan produce(ContinuityStorePort.Session same,PlanningRequest request)throws IOException {
            return fixture.collector.current(same,request.before(),request.deadline(),lease->{
                var decision=assertInstanceOf(OrdinaryPolicy.Annotate.class,feast.evaluate(request,advanceDraft(request)));
                return GovernanceCadencePublication.fromDetail(decision.retained().detail()).orElseThrow();
            });
        }
        OrdinaryPlanCompletion.SelectionDisposition publish(ContinuityStorePort.Session same,GovernanceCadencePublication.Plan plan)throws IOException {
            var previous=same.head();var actual=publication.publish(same,plan,List.of(source));
            if(actual instanceof GovernanceCadencePublication.Changed changed)return new OrdinaryPlanCompletion.Published(previous,changed.committed());
            assertInstanceOf(GovernanceCadencePublication.AlreadyCurrent.class,actual);
            return new OrdinaryPlanCompletion.Unchanged("actual same-marker reducer already current");
        }
        CadenceModels.State state(ContinuityStorePort.Session same)throws IOException {
            return CadenceJson.readState(available(same).canonicalBody(),baseline.episodeRunId());
        }
        ObservedFrame newNativeMarker(ObservedFrame previous,Instant until)throws IOException,InterruptedException {
            byte[] raw=previous.originalPacket();
            var packet=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(Arrays.copyOfRange(raw,4,raw.length));
            packet.put("snapshot_id",previous.snapshotId()+"-next-native-marker");
            packet.put("revision",previous.nativeRevision().add(java.math.BigInteger.ONE));
            fixture.enqueueSoftwareNativePacket(NativeWire.packet(StrictJson.canonical(packet)));
            var actual=fixture.physicalInputs().transport().observe(until);
            assertEquals(previous.nativeRevision().add(java.math.BigInteger.ONE),actual.nativeRevision());
            return actual;
        }
        @Override public void close()throws IOException {fixture.close();}
    }

    private static List<ActionWriterIntegrationFixture.SoftwareActionScenario> withFeastActions(ActionWriterIntegrationFixture.SoftwareActionScenario first) {
        var result=new ArrayList<ActionWriterIntegrationFixture.SoftwareActionScenario>();result.add(first);
        for(var operation:OrdinaryFeastPolicy.OWNED)if(!operation.equals(first.operation()))
            result.add(new ActionWriterIntegrationFixture.SoftwareActionScenario(operation,"game.command."+operation.value(),
                    (command,attempt,dispatch)->{throw new AssertionError("software Feast action must never execute");},()->{throw new AssertionError("no Feast action");}));
        return List.copyOf(result);
    }
    private static ContinuityStorePort.Session active(ActionWriterIntegrationFixture fixture) {
        try{return fixture.writer.activeSession().orElseThrow(()->new IllegalStateException("original held writer is required"));}
        catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    private static DomainBodies.Available available(ContinuityStorePort.Session same)throws IOException {
        if(same.readDomain(DomainBodies.Slot.OPTIONAL_CADENCE) instanceof DomainBodies.Available body)return body;
        throw new IOException("original cadence body unavailable");
    }
    private static DomainBodies.Verifier seedVerifier(AtomicReference<GovernanceCadencePublication> publication,
            AtomicReference<CadenceModels.State> baseline) {
        return new DomainBodies.Verifier(){
            @Override public String verify(org.xar.ck3.control.continuity.ContinuityState head,Optional<DomainBodies.BodyRef> previous,
                    DomainBodies.ImportRequest request,byte[] body)throws IOException {throw new IOException("actual locked Head required");}
            @Override public String verify(WriterContracts.Head head,Optional<DomainBodies.BodyRef> previous,
                    DomainBodies.ImportRequest request,byte[] body)throws IOException {
                if(Arrays.equals(SEED,request.producerInput())) {
                    assertTrue(previous.isEmpty());assertEquals(0,head.state().sequence());
                    var expected=Objects.requireNonNull(baseline.get());
                    assertEquals(expected,CadenceJson.readState(body,expected.episodeRunId()));return ActionCodec.sha256(body);
                }
                return Objects.requireNonNull(publication.get()).verify(head,previous,request,body);
            }
        };
    }
    private static void seed(ActionWriterIntegrationFixture fixture,CadenceModels.State before,ExactRef source)throws IOException {
        fixture.writer.locked(same->{
            var body=fixture.archive.withSession(same).preserveMaterial(new RawJson(CadenceJson.writeState(before)));
            var input=new DomainBodies.ImportRequest(DomainBodies.Slot.OPTIONAL_CADENCE,CadenceModels.SCHEMA,body,SEED,List.of(source),"controlled-same-occurrence-cadence-seed");
            same.commitImport(same.previewImport(input));
            assertEquals(before,CadenceJson.readState(available(same).canonicalBody(),before.episodeRunId()));return null;
        });
    }
    private static OrdinaryPolicy.Draft advanceDraft(PlanningRequest request) {
        var expected=new ProposalLifecycle.ExpectedPostcondition(1,request.before(),request.source(),"paused/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"),true)));
        var command=new ActionCommand("unsubmitted-feast-cadence-basis",request.before(),request.source(),request.sessionId(),
                new OperationKey("life-advance"),new OpportunityJson.Obj(Map.of()),expected,
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),request.deadline());
        return new OrdinaryPolicy.Draft("controlled-unsubmitted-advance","ordinary","actual current typed no-action input",
                OrdinaryPolicy.Kind.ORDINARY,Optional.of(command),OrdinaryPolicy.Purpose.DATE_ADVANCE,Optional.empty(),new OpportunityJson.Obj(Map.of()));
    }
    /** Typed software input edge; the production Feast policy issues the only private replay transcript. */
    private static final class ActualFeastInputs implements FeastObservationSupplier {
        final ActionWriterIntegrationFixture fixture;final ExactRef source;boolean failPlanner;int plannerReads;
        final IllegalStateException plannerFailure=new IllegalStateException("actual controlled typed planner failure");
        ActualFeastInputs(ActionWriterIntegrationFixture fixture,ExactRef source){this.fixture=fixture;this.source=source;}
        public Read<FeastObservationSupplier.State> state(PlanningRequest request){
            try {
                var same=active(fixture);fixture.writer.requireSession(same);
                var cadence=CadenceJson.readState(available(same).canonicalBody(),request.before().frame().episodeRunId());
                return new Known<>(new FeastObservationSupplier.State(request.before(),request.sessionId(),cadence,
                        Optional.empty(),Optional.empty(),List.of(),new OpportunityJson.Obj(Map.of())),List.of(source));
            }catch(IOException failure){throw new UncheckedIOException(failure);}
        }
        public Read<FeastObservationSupplier.Planner> planner(PlanningRequest request){
            plannerReads++;if(failPlanner)throw plannerFailure;
            return new Known<>(new FeastObservationSupplier.Planner(ActivityPlannerDiagnostic.Kind.OTHER,new OpportunityJson.Obj(Map.of())),List.of(source));
        }
        public Read<FeastObservationSupplier.Hosted> hosted(PlanningRequest request){throw new AssertionError("OTHER no-action never reads hosted state");}
        public Read<OpportunityJson.Obj> root(PlanningRequest request){throw new AssertionError("OTHER no-action never reads ROOT");}
        public Read<OrdinaryFinanceCollector.Spending> spending(PlanningRequest request){throw new AssertionError("OTHER no-action never reads spending");}
        public Read<OrdinaryFinanceCollector.Feast> feast(PlanningRequest request,OrdinaryFinanceCollector.Spending spending){throw new AssertionError("OTHER no-action never requests Start");}
    }
}
