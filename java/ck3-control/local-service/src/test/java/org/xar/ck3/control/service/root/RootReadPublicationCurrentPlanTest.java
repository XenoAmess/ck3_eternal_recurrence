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
import org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier;
import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.application.planning.OrdinaryPolicy.*;
import static org.xar.ck3.control.application.session.SessionPorts.*;

/** Real software Native READ/ACK -> publisher/CAS -> actual collector -> planner/Controller -> one Native ACK.
 * Controlled selection is not a live LLM/Game gameplay or day-advance qualification. */
final class RootReadPublicationCurrentPlanTest {
    @TempDir Path directory;
    private static final String PROFILE="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";

    @Test void publishedRootIsRejoinedBeforeSelectionAndTheControllerSubmitsOnlyTheCurrentCommand() throws Exception {
        var definitions=new AtomicReference<FinanceReadContracts>(); var source=new AtomicReference<ExactRef>();
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
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("actual-writer"),false,nativeReads,List.of(action))) {
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
            fixture.writer.locked(same->fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(60),lease->{
                var config=new DynamicCapabilities.Configuration(Optional.empty(),Optional.empty(),3,3,false,false);
                var presentation=new CapabilitySessionPresentation(false,Optional.empty(),Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
                        CapabilitySessionPresentation.BindingState.ACTIVE_NEW,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
                var policy=fixture.archive.preserveMaterial(new RawJson(DriverJson.encode(new OpportunityJson.Obj(Map.of("software_start",new OpportunityJson.Bool(true))))));
                var produced=DriverCapabilityStateProducer.initializeNewEpisode(lease.frame(),lease.driver(),config,presentation,policy,fixture.archive.withSession(same));
                fixture.driverAuthority().publishCapabilityInputs(same,lease.driver().stamp(),produced.expectedAuxiliarySha256(),produced);return null;
            }));
            var held=new AtomicReference<ContinuityStorePort.Session>();
            var changed=new AtomicReference<Optional<OrdinaryPlanCompletion.Published>>(Optional.empty());
            var originalRead=new AtomicReference<PlanningReadResult.Known<FinanceReadContracts.Packet>>();
            var firstTemporary=new AtomicReference<ActionCommand>();var selected=new AtomicReference<ActionCommand>();
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
                            changed.set(Optional.empty());return RootReadPublicationCompletion.finishOriginalWork(work,this::flush,()->false);
                        },()->changed.get().isPresent(),()->fixture.collector.prepareReadPublicationReplan(same)));
                    }catch(InterruptedException interrupted){var failure=new InterruptedIOException("actual planning interrupted");failure.initCause(interrupted);throw failure;}
                    finally{held.set(null);}});}catch(InterruptedIOException failure){throw (InterruptedException)failure.getCause();}
                }
                public Optional<Published> beforeSelection(PlanningRequest request,PlanningResult.ActionSelected proposed){
                    try{return flush();}catch(IOException failure){throw new UncheckedIOException(failure);}
                }
                public PlanningDisposition afterPlanning(PlanningRequest request,PlanningResult planned){return changed.get().<PlanningDisposition>map(value->value).orElseGet(()->new Unchanged("actual read fixed point"));}
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
                                originalRead.set(known);}
                            return null;
                        });}catch(IOException failure){throw new UncheckedIOException(failure);}
                        int number=proposals.incrementAndGet();
                        var expected=new ProposalLifecycle.ExpectedPostcondition(1,input.before(),input.source(),"paused/v1",List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"),true)));
                        var command=new ActionCommand("actual-root-read-handoff-"+number,input.before(),input.source(),input.sessionId(),operation,new OpportunityJson.Obj(Map.of()),expected,
                                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),input.deadline());
                        firstTemporary.compareAndSet(null,command);
                        return new Replace(new Draft("actual-read-handoff","ordinary","native software action after canonical READ",Kind.ORDINARY,Optional.of(command),Purpose.WORLD_ACTION,Optional.empty(),new OpportunityJson.Obj(Map.of())),"actual current proposal");
                    }};
            }).toList();
            var planner=new OrdinaryPlanner(policies,Clock.systemUTC(),realm);
            planner.bindSelector((request,proposal)->{
                assertFalse(publisher.hasPending(held.get()));assertEquals(1,request.observations().history().size());
                assertEquals(2,proposals.get());assertNotSame(firstTemporary.get(),proposal.command());
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
                    (actual,until)->fixture.collector.observe(held.get(),actual,until),planner,coordinator,checkpoint,
                    new CheckpointRequestFactory(directory.resolve("unused.ck3"),save),batches,work->{throw new AssertionError("no incident");},
                    new SessionClock.SystemClock(),Optional.empty(),0,completion,(actual,receipt,until)->{throw new AssertionError("no episode");});
            controller.bindRetainedIncidents(List::of);controller.bindRestartDriver(fixture.driverAuthority());
            var report=controller.autoTurn(Instant.now().plusSeconds(120)).execution();
            assertEquals(1,fixture.scenarioReadWrites());assertEquals(1,publications.get());assertEquals(2,proposals.get());assertEquals(1,selections.get());
            assertEquals(1,fixture.nativeActionWrites(),()->report.terminal()+":"+report.detail());assertEquals(1,report.turns().size());
            var receipt=report.turns().getFirst().receipt();
            assertTrue(assertInstanceOf(NativeActionPort.AckReceived.class,ActionTransitions.dispatch(receipt.state()).orElseThrow()).nativeOk());
            assertEquals(ActionCodec.bodySha256(selected.get()),receipt.bodySha256());
            assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,report.terminal());assertTrue(controller.isQuarantined());
            var refused=controller.autoTurn(Instant.now().plusSeconds(1)).execution();
            assertEquals(BatchReport.Terminal.INTERNAL_FAILURE,refused.terminal());
            assertTrue(refused.turns().isEmpty());assertEquals(1,fixture.nativeActionWrites());
        }
    }
}
