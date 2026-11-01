package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.application.readiness.*;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.application.planning.OrdinaryPolicy.*;

/** Owner regression with mechanical fixture support and independently frozen semantic expectations.
 * Selector callbacks are software HTTP-boundary observations, never real HTTP.
 * Marker transitions prove generic typed control flow, not Governance private replay or live authority. */
final class RootCadenceBeforeSelection268Test {
    @TempDir Path directory;

    private static final class MutableClock268 extends Clock {
        private Instant now;
        MutableClock268(Instant now) { this.now=Objects.requireNonNull(now); }
        void set(Instant actual) { now=Objects.requireNonNull(actual); }
        @Override public ZoneId getZone() { return ZoneOffset.UTC; }
        @Override public Clock withZone(ZoneId zone) { return Clock.fixed(now,zone); }
        @Override public Instant instant() { return now; }
    }

    /** Real collector request, policies and canonical writer; no controller/native action is run. */
    private static final class PlannerHarness268 implements AutoCloseable {
        private static final String MARKER="software_test_cadence268_marker";
        final ActionWriterIntegrationFixture fixture;
        final PlanningRequest request;
        final MutableClock268 clock;
        final OrdinaryPlanner planner;
        final AtomicInteger selectorCalls=new AtomicInteger();
        private int markerSequence;
        PlannerHarness268(Path root) throws Exception {
            fixture=new ActionWriterIntegrationFixture(root,false);
            fixture.bindAdditionalTransitionAuthority(MARKER,new WriterContracts.TransitionAuthority() {
                public String revalidate(ContinuityState previous,WriterContracts.Request actual) {
                    StrictJson.require(MARKER.equals(actual.kind()),"controlled marker kind");
                    return ContinuityJson.digest(actual.detailsObject());
                }
                public ContinuityState reduce(ContinuityState previous,WriterContracts.Request actual) {
                    var next=previous.toJson();next.set(MARKER,actual.detailsObject());
                    return ContinuityState.fromJson(next,previous.machineId());
                }
            });
            request=fixture.ready().request();
            clock=new MutableClock268(Instant.now());
            var realm=new RealmLifecycle(request.source().sourceRef());
            var policies=Arrays.stream(PlanningStage.values()).<OrdinaryPolicy>map(stage->{
                if(stage==PlanningStage.REALM_MEMBERSHIP_PUBLICATION)return realm;
                return new OrdinaryPolicy() {
                    public PlanningStage stage(){return stage;}
                    public ExactRef implementationSource(){return request.source().sourceRef();}
                    public Decision evaluate(PlanningRequest input,Draft previous) {
                        if(stage!=PlanningStage.ORDINARY_CORE)return new Keep("mechanical stage retains proposal");
                        return new Replace(draft268(input),"controlled ordinary proposal");
                    }
                };
            }).toList();
            planner=new OrdinaryPlanner(policies,clock,realm);
            planner.bindSelector((original,proposed)->{
                selectorCalls.incrementAndGet();
                return new OrdinaryDecisionSelector.Selection(OrdinaryDecisionSelector.Choice.ACCEPT,"controlled selector",Optional.empty());
            });
        }
        OrdinaryPlanCompletion.Published publishMarker() throws IOException {
            int number=++markerSequence;
            return fixture.writer.locked(same->{
                var details=StrictJson.object().put("evidence_id","marker268-"+number);
                details.set("source",request.source().sourceRef().toJson());
                var actual=new WriterContracts.Request(MARKER,StrictJson.canonical(details),List.of(request.source().sourceRef()));
                var predecessor=same.head();
                var committed=same.commit(same.preview(actual));
                return new OrdinaryPlanCompletion.Published(predecessor,committed);
            });
        }
        @Override public void close() throws IOException { fixture.close(); }
    }

    private static Draft draft268(PlanningRequest request) {
        var expected=new ProposalLifecycle.ExpectedPostcondition(1,request.before(),request.source(),"paused/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"),true)));
        var command=new ActionCommand("controlled-cadence268",request.before(),request.source(),request.sessionId(),new OperationKey("pause-map"),
                new OpportunityJson.Obj(Map.of()),expected,new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),request.deadline());
        return new Draft("controlled-cadence268","ordinary","controlled proposal",Kind.ORDINARY,Optional.of(command),Purpose.WORLD_ACTION,
                Optional.empty(),new OpportunityJson.Obj(Map.of()));
    }
    private static PlanningResult.ActionSelected selected268(PlanningRequest request) {
        var draft=draft268(request);
        return new PlanningResult.ActionSelected(draft.command().orElseThrow(),new PlanTrace(request.before(),List.of(),Optional.of(draft)));
    }

    /** Explicit archive DATA request for same-Core round control flow, never a Ready/current lease. */
    private static PlanningRequest dataRequest268(String machine,ExactRef sourceRef) {
        var game=new GameGeneration(121,new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var before=new ProposalLifecycle.ObservationIdentity(machine,game,new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(73),BigInteger.ONE,BigInteger.valueOf(1000)),"data268",BigInteger.ONE,"data-episode268"),1);
        var source=new G2Source(machine,Instant.now().toString(),"controlled-archive-data",sourceRef);
        var snapshot=new OpportunityJson.Obj(Map.of()).with("snapshot_id",new OpportunityJson.Text("data268"))
                .with("episode_run_id",new OpportunityJson.Text("data-episode268"))
                .with("revision",new OpportunityJson.IntegerValue(BigInteger.ONE)).with("native_revision",new OpportunityJson.IntegerValue(BigInteger.ONE))
                .with("date_raw",new OpportunityJson.IntegerValue(BigInteger.valueOf(1000))).with("paused",new OpportunityJson.Bool(true))
                .with("map_ready",new OpportunityJson.Bool(true)).with("played_character",new OpportunityJson.Obj(Map.of("character_id",new OpportunityJson.IntegerValue(BigInteger.valueOf(73)))))
                .with("active_wars",new OpportunityJson.Arr(List.of())).with("player_armies",new OpportunityJson.Arr(List.of()));
        var observations=new PlanningObservation(snapshot,List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
        return new PlanningRequest(before,source,"data-session268",Instant.now().plusSeconds(30),observations);
    }

    @FunctionalInterface private interface RoundWork268<T> { T run(RootReadPublicationCompletion completion) throws Exception; }

    /** Real Core/actual writer scope. All current observation and transport edges reject use. */
    private static final class RootRoundHarness268 implements AutoCloseable {
        private static final String SCHEMA="controlled-round-marker268/v1";
        final RootApplicationAssembly.Core core;
        final PlanningRequest request;
        final AtomicInteger observationEdges=new AtomicInteger();
        private final ActionWriterIntegrationFixture transportFactory;
        private final DriverReadHistoryPublisher publisher;
        private final DriverStateAssembler driver;
        private final ExactRef source;
        private int markers;
        RootRoundHarness268(Path root) throws Exception {
            var opened=RootManagedSessionScopeTest.dataCore(root.resolve("core"));
            source=opened.source();var configuration=opened.configuration();opened.core().close();
            DomainBodies.Verifier marker=(head,previous,actual,body)->{
                StrictJson.require(actual.slot()==DomainBodies.Slot.OPTIONAL_CADENCE&&actual.contractSchema().equals(SCHEMA),"controlled marker contract");
                StrictJson.require(Arrays.equals(actual.producerInput(),body),"controlled marker material exactness");
                return ActionCodec.sha256(body);
            };
            var registration=new DomainBodies.Registration(DomainBodies.Slot.OPTIONAL_CADENCE,SCHEMA,4096,List.of(source),marker);
            core=RootApplicationAssembly.open(configuration,Clock.systemUTC(),List.of(registration),Optional.empty(),StorageWriteGuardTestSupport.create(configuration.ledger()));
            request=dataRequest268(configuration.machineId(),source);
            driver=new DriverStateAssembler(new ActionSnapshotReader(core.journal()),new DriverFactsRepository(new DriverSnapshotFacts.Unavailable(List.of("archive round only"))),
                    actual->{observationEdges.incrementAndGet();throw new AssertionError("no observation facts");});
            driver.bindHistoryArchive(core.archive(),()->{
                try{return core.writer().borrowedSession();}catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
            });
            publisher=new DriverReadHistoryPublisher(driver,core.archive(),RootReadContractCatalog.staticOnly(List.of()),List.of(source));
            transportFactory=new ActionWriterIntegrationFixture(root.resolve("transport-factory"),false);
        }
        OrdinaryPlanCompletion.Published publishMarker() throws IOException {
            var same=core.writer().borrowedSession();core.writer().requireSession(same);
            byte[] body=StrictJson.canonical(StrictJson.object().put("marker",++markers));
            var ref=core.archive().withSession(same).preserveMaterial(new RawJson(body));
            var input=new DomainBodies.ImportRequest(DomainBodies.Slot.OPTIONAL_CADENCE,SCHEMA,ref,body,List.of(source),"round268-"+markers);
            var prepared=same.previewImport(input);var actual=same.commitImport(prepared);
            return new OrdinaryPlanCompletion.Published(prepared.predecessor(),actual);
        }
        <T>T with(OrdinaryPlanCompletion downstream,RoundWork268<T> work) throws Exception {
            NativePacketPort packets=new NativePacketPort() {
                private AssertionError rejected(){observationEdges.incrementAndGet();return new AssertionError("no packet edge");}
                public void verify(){throw rejected();}
                public void awaitConnection(Instant deadline){throw rejected();}
                public byte[] readPacket(Instant deadline){throw rejected();}
                public void writePacket(byte[] packet,Instant deadline){throw rejected();}
                public void close(){ }
            };
            var config=new NativePipeEndpoint.Config("\\\\.\\pipe\\offline-round268",request.source().machineId(),request.before().game(),request.sessionId(),"software","0".repeat(64),"software-round268");
            return transportFactory.withSoftwareProtocol(packets,config,transport->{
                var collector=new NativeReadinessCollector(new SessionPorts.SessionIdentity(request.source().machineId(),request.before().game(),request.sessionId()),
                        core.writer(),transport,driver,new DriverObservationAssembler(),
                        (game,deadline)->{observationEdges.incrementAndGet();throw new AssertionError("no lifecycle edge");},
                        (same,role,original)->{observationEdges.incrementAndGet();throw new AssertionError("no observation archive edge");},
                        new NativeSemanticEvidenceVerifier((same,ref,max)->{observationEdges.incrementAndGet();throw new AssertionError("no semantic observation edge");}),
                        (same,identity,frame,known,received,process,deadline)->{observationEdges.incrementAndGet();throw new AssertionError("no source observation edge");},
                        (same,frame,known,received,deadline)->{observationEdges.incrementAndGet();throw new AssertionError("no capability edge");},
                        (same,frame,known,received,deadline)->{observationEdges.incrementAndGet();throw new AssertionError("no planning observation edge");},
                        new NativeReadiness.Policy(false,false,Optional.empty(),Duration.ZERO,false),Duration.ofSeconds(1),Clock.systemUTC());
                collector.bindObservationSession(core.writer()::requireSession);
                return work.run(new RootReadPublicationCompletion(core,publisher,downstream,collector));
            });
        }
        @Override public void close() throws IOException { try{transportFactory.close();}finally{core.close();} }
    }
    private static OrdinaryPlanCompletion unchanged268(AtomicInteger normal) {
        return new OrdinaryPlanCompletion() {
            public PlanningDisposition afterPlanning(PlanningRequest request,PlanningResult planned) {
                normal.incrementAndGet();return new Unchanged("normal post-planning completion");
            }
            public ExecutionDisposition afterExecution(ActionReceipt receipt) { return new Unchanged("unused execution edge"); }
        };
    }

    @Test void legacyReadPublicationPrecedesAndSkipsEarlyHookAndSelector() throws Exception {
        try(var h=new PlannerHarness268(directory.resolve("read-first"))) {
            var actual=h.publishMarker();var reads=new AtomicInteger();var early=new AtomicInteger();
            OrdinaryPlanCompletion completion=new OrdinaryPlanCompletion() {
                public Optional<Published> beforeSelection(PlanningRequest original,PlanningResult.ActionSelected proposed) {
                    assertSame(h.request,original);reads.incrementAndGet();return Optional.of(actual);
                }
                public SelectionDisposition beforeModel(PlanningRequest original,PlanningResult.ActionSelected proposed) {
                    early.incrementAndGet();throw new AssertionError("READ publication must skip early domain work");
                }
                public PlanningDisposition afterPlanning(PlanningRequest original,PlanningResult planned) { throw new AssertionError("planner does not own completion"); }
                public ExecutionDisposition afterExecution(ActionReceipt receipt) { throw new AssertionError("no execution"); }
            };
            var result=assertInstanceOf(PlanningResult.RefreshRequired.class,h.planner.plan(h.request,completion));
            assertEquals("actual_read_publication_requires_current_proposal",result.reason());
            assertEquals(1,reads.get());assertEquals(0,early.get());assertEquals(0,h.selectorCalls.get());
            assertTrue(result.trace().finalPlan().orElseThrow().command().isEmpty());
            assertEquals(Purpose.READ_ONLY,result.trace().finalPlan().orElseThrow().purpose());
            assertEquals(0,h.fixture.nativeActionWrites());
        }
    }

    @Test void changedPreparationReturnsRefreshWithoutSelectingAnAction() throws Exception {
        try(var h=new PlannerHarness268(directory.resolve("changed"))) {
            var order=new ArrayList<String>();var published=new AtomicReference<OrdinaryPlanCompletion.Published>();
            OrdinaryPlanCompletion completion=new OrdinaryPlanCompletion() {
                public Optional<Published> beforeSelection(PlanningRequest original,PlanningResult.ActionSelected proposed) { order.add("READ");return Optional.empty(); }
                public SelectionDisposition beforeModel(PlanningRequest original,PlanningResult.ActionSelected proposed) {
                    order.add("DOMAIN");try{var actual=h.publishMarker();published.set(actual);return actual;}
                    catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
                }
                public PlanningDisposition afterPlanning(PlanningRequest original,PlanningResult planned) { throw new AssertionError("planner does not retry domain completion"); }
                public ExecutionDisposition afterExecution(ActionReceipt receipt) { throw new AssertionError("no execution"); }
            };
            var result=assertInstanceOf(PlanningResult.RefreshRequired.class,h.planner.plan(h.request,completion));
            assertEquals(List.of("READ","DOMAIN"),order);assertNotNull(published.get());
            assertEquals("actual_domain_publication_requires_current_proposal",result.reason());
            assertEquals(0,h.selectorCalls.get());assertTrue(result.trace().finalPlan().orElseThrow().command().isEmpty());
            assertEquals(Purpose.READ_ONLY,result.trace().finalPlan().orElseThrow().purpose());
            assertEquals(0,h.fixture.nativeActionWrites());
        }
    }

    @Test void blockedCompositionStopsLaterHooksAndOnlineSelection() throws Exception {
        try(var h=new PlannerHarness268(directory.resolve("blocked"))) {
            var first=new AtomicInteger();var second=new AtomicInteger();var later=new AtomicInteger();
            var blocked=new OrdinaryPlanCompletion.Blocked("controlled missing original",List.of(h.request.source().sourceRef()));
            OrdinaryPlanCompletion a=new OrdinaryPlanCompletion() {
                public SelectionDisposition beforeModel(PlanningRequest request,PlanningResult.ActionSelected proposed){first.incrementAndGet();return new Unchanged("first unchanged");}
                public PlanningDisposition afterPlanning(PlanningRequest request,PlanningResult planned){throw new AssertionError("no normal completion in planner");}
                public ExecutionDisposition afterExecution(ActionReceipt receipt){throw new AssertionError("no execution");}
            };
            OrdinaryPlanCompletion b=new OrdinaryPlanCompletion() {
                public SelectionDisposition beforeModel(PlanningRequest request,PlanningResult.ActionSelected proposed){second.incrementAndGet();return blocked;}
                public PlanningDisposition afterPlanning(PlanningRequest request,PlanningResult planned){throw new AssertionError("no normal completion in planner");}
                public ExecutionDisposition afterExecution(ActionReceipt receipt){throw new AssertionError("no execution");}
            };
            OrdinaryPlanCompletion c=new OrdinaryPlanCompletion() {
                public SelectionDisposition beforeModel(PlanningRequest request,PlanningResult.ActionSelected proposed){later.incrementAndGet();throw new AssertionError("blocked composition must stop");}
                public PlanningDisposition afterPlanning(PlanningRequest request,PlanningResult planned){throw new AssertionError("no normal completion in planner");}
                public ExecutionDisposition afterExecution(ActionReceipt receipt){throw new AssertionError("no execution");}
            };
            var completion=new RootRuntimePipeline.Completion(List.of(a,b,c));
            var result=assertInstanceOf(PlanningResult.ReadOnlyWait.class,h.planner.plan(h.request,completion));
            assertEquals("actual_pre_model_completion_blocked:"+blocked.reason(),result.reason());
            assertEquals(1,first.get());assertEquals(1,second.get());assertEquals(0,later.get());assertEquals(0,h.selectorCalls.get());
            assertTrue(result.trace().finalPlan().orElseThrow().command().isEmpty());assertEquals(0,h.fixture.nativeActionWrites());
        }
    }

    @Test void defaultUnchangedAllowsSelectionAndKeepsNormalCompletionLater() throws Exception {
        try(var h=new PlannerHarness268(directory.resolve("default"))) {
            var normal=new AtomicInteger();var completion=unchanged268(normal);
            var result=assertInstanceOf(PlanningResult.ActionSelected.class,h.planner.plan(h.request,completion));
            assertEquals(1,h.selectorCalls.get());assertEquals(0,normal.get());
            assertInstanceOf(OrdinaryPlanCompletion.Unchanged.class,completion.afterPlanning(h.request,result));
            assertEquals(1,normal.get());assertEquals(0,h.fixture.nativeActionWrites());
        }
    }

    @Test void expiryAcrossReadBarrierPreventsEarlyHookAndSelector() throws Exception {
        try(var h=new PlannerHarness268(directory.resolve("deadline"))) {
            var reads=new AtomicInteger();var early=new AtomicInteger();
            OrdinaryPlanCompletion completion=new OrdinaryPlanCompletion() {
                public Optional<Published> beforeSelection(PlanningRequest original,PlanningResult.ActionSelected proposed) {
                    reads.incrementAndGet();h.clock.set(original.deadline());return Optional.empty();
                }
                public SelectionDisposition beforeModel(PlanningRequest original,PlanningResult.ActionSelected proposed) {early.incrementAndGet();throw new AssertionError("expired original cannot publish");}
                public PlanningDisposition afterPlanning(PlanningRequest original,PlanningResult planned){throw new AssertionError("no post-planning call here");}
                public ExecutionDisposition afterExecution(ActionReceipt receipt){throw new AssertionError("no execution");}
            };
            var result=assertInstanceOf(PlanningResult.Stopped.class,h.planner.plan(h.request,completion));
            assertEquals(PlanningResult.StopReason.DEADLINE,result.reason());
            assertEquals(1,reads.get());assertEquals(0,early.get());assertEquals(0,h.selectorCalls.get());assertEquals(0,h.fixture.nativeActionWrites());
        }
    }

    @Test void actualRootRetainsSameTypedChangedAndDoesNotGrantReadRejoin() throws Exception {
        try(var h=new RootRoundHarness268(directory.resolve("root-changed"))) {
            var early=new AtomicInteger();var normal=new AtomicInteger();var change=new AtomicReference<OrdinaryPlanCompletion.Published>();
            var first=new java.util.concurrent.atomic.AtomicBoolean(true);
            OrdinaryPlanCompletion downstream=new OrdinaryPlanCompletion() {
                public SelectionDisposition beforeModel(PlanningRequest request,PlanningResult.ActionSelected proposed) {
                    early.incrementAndGet();
                    if(first.getAndSet(false))try{var actual=h.publishMarker();change.set(actual);return actual;}catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
                    return new Unchanged("next round has no work");
                }
                public PlanningDisposition afterPlanning(PlanningRequest request,PlanningResult planned){normal.incrementAndGet();return new Unchanged("original normal completion");}
                public ExecutionDisposition afterExecution(ActionReceipt receipt){throw new AssertionError("no execution");}
            };
            h.with(downstream,completion->{
                var proposed=selected268(h.request);
                var firstScope=completion.inPlanningScope(()->{
                    assertTrue(completion.beforeSelection(h.request,proposed).isEmpty());
                    var prepared=completion.beforeModel(h.request,proposed);assertSame(change.get(),prepared);
                    assertSame(prepared,completion.afterPlanning(h.request,proposed));
                    var equalButDifferent=h.request.withHistory(h.request.observations().history());
                    assertNotSame(h.request,equalButDifferent);
                    assertThrows(IllegalArgumentException.class,()->completion.afterPlanning(equalButDifferent,proposed));
                    return prepared;
                });
                assertTrue(firstScope.readPublication().isEmpty(),"domain commit must not become READ rejoin authority");
                assertEquals(1,early.get());assertEquals(0,normal.get());
                var nextScope=completion.inPlanningScope(()->{
                    assertTrue(completion.beforeSelection(h.request,proposed).isEmpty());
                    assertInstanceOf(OrdinaryPlanCompletion.Unchanged.class,completion.beforeModel(h.request,proposed));
                    return completion.afterPlanning(h.request,proposed);
                });
                assertInstanceOf(OrdinaryPlanCompletion.Unchanged.class,nextScope.value());assertTrue(nextScope.readPublication().isEmpty());
                assertEquals(2,early.get());assertEquals(1,normal.get());
                assertThrows(java.io.UncheckedIOException.class,()->completion.beforeModel(h.request,proposed));
                return null;
            });
            assertEquals(0,h.observationEdges.get());
        }
    }

    @Test void actualRootRetainsBlockedAndCleansItsRoundAfterException() throws Exception {
        try(var h=new RootRoundHarness268(directory.resolve("root-blocked"))) {
            var blocked=new OrdinaryPlanCompletion.Blocked("controlled blocked proof",List.of(h.request.source().sourceRef()));
            var shouldBlock=new java.util.concurrent.atomic.AtomicBoolean(true);var normal=new AtomicInteger();var early=new AtomicInteger();
            OrdinaryPlanCompletion downstream=new OrdinaryPlanCompletion() {
                public SelectionDisposition beforeModel(PlanningRequest request,PlanningResult.ActionSelected proposed){early.incrementAndGet();return shouldBlock.get()?blocked:new Unchanged("following scope");}
                public PlanningDisposition afterPlanning(PlanningRequest request,PlanningResult planned){normal.incrementAndGet();return new Unchanged("normal after exception");}
                public ExecutionDisposition afterExecution(ActionReceipt receipt){throw new AssertionError("no execution");}
            };
            h.with(downstream,completion->{
                var proposed=selected268(h.request);var originalFailure=new IOException("controlled post-preparation work failure");
                var received=assertThrows(IOException.class,()->completion.inPlanningScope(()->{
                    assertTrue(completion.beforeSelection(h.request,proposed).isEmpty());
                    assertSame(blocked,completion.beforeModel(h.request,proposed));
                    assertSame(blocked,completion.afterPlanning(h.request,proposed));
                    assertEquals(0,normal.get());throw originalFailure;
                }));
                assertSame(originalFailure,received);shouldBlock.set(false);
                var next=completion.inPlanningScope(()->{
                    assertTrue(completion.beforeSelection(h.request,proposed).isEmpty());
                    assertInstanceOf(OrdinaryPlanCompletion.Unchanged.class,completion.beforeModel(h.request,proposed));
                    return completion.afterPlanning(h.request,proposed);
                });
                assertInstanceOf(OrdinaryPlanCompletion.Unchanged.class,next.value());assertTrue(next.readPublication().isEmpty());
                assertEquals(2,early.get());assertEquals(1,normal.get());
                return null;
            });
            assertEquals(0,h.observationEdges.get());
        }
    }

    @Test void governanceProbeBlocksChangedWithoutSessionAndLeavesUnchangedProofInItsOriginalPhase() throws Exception {
        try(var h=new PlannerHarness268(directory.resolve("governance-probe"))) {
            var sessions=new AtomicInteger();var evidence=new AtomicInteger();
            var publisher=new org.xar.ck3.control.application.planning.governance.GovernanceCadencePublication(
                    directory.resolve("never-used-cadence.lock").toAbsolutePath(),same->{throw new AssertionError("no borrowed session was issued");},
                    List.of(h.request.source().sourceRef()),(head,previous,plan,originals)->{throw new AssertionError("no private transcript was issued");},
                    (id,body)->{throw new AssertionError("no publication without a real Session");});
            var actual=new org.xar.ck3.control.application.planning.governance.GovernancePlanCompletion(()->{sessions.incrementAndGet();return null;},
                    same->{throw new AssertionError("no borrowed session was issued");},publisher,
                    (request,planned,plan)->{evidence.incrementAndGet();throw new AssertionError("no original replay without a Session");});
            var before=org.xar.ck3.control.planning.optionalcadence.CadenceModels.State.empty(h.request.before().frame().episodeRunId());
            var selected=selectedWithCadence268(h.request,before,h.request.sessionId());
            assertInstanceOf(OrdinaryPlanCompletion.Blocked.class,actual.beforeModel(h.request,selected));
            assertEquals(1,sessions.get());assertEquals(0,evidence.get());
            var plan=org.xar.ck3.control.application.planning.governance.GovernanceCadencePublication.fromDetail(selected.trace().finalPlan().orElseThrow().detail()).orElseThrow();
            var unchangedState=org.xar.ck3.control.application.planning.governance.GovernanceCadencePublication.reduce(plan);
            var unchanged=selectedWithCadence268(h.request,unchangedState,h.request.sessionId());
            assertInstanceOf(OrdinaryPlanCompletion.Unchanged.class,actual.beforeModel(h.request,unchanged));assertEquals(1,sessions.get());
            assertInstanceOf(OrdinaryPlanCompletion.Blocked.class,actual.afterPlanning(h.request,unchanged));assertEquals(2,sessions.get());assertEquals(0,evidence.get());
            var wrongSession=selectedWithCadence268(h.request,unchangedState,"different-planning-session");
            assertInstanceOf(OrdinaryPlanCompletion.Blocked.class,actual.beforeModel(h.request,wrongSession));assertEquals(2,sessions.get());
        }
    }

    private static PlanningResult.ActionSelected selectedWithCadence268(PlanningRequest request,
            org.xar.ck3.control.planning.optionalcadence.CadenceModels.State before,String session) {
        var plan=new org.xar.ck3.control.application.planning.governance.GovernanceCadencePublication.Plan(request.before(),request.source(),session,before,
                List.of(org.xar.ck3.control.planning.optionalcadence.CadenceModels.Domain.FEAST));
        var original=draft268(request);var detail=original.detail().with(org.xar.ck3.control.application.planning.governance.GovernanceCadencePublication.FIELD,
                OpportunityJson.parse(org.xar.ck3.control.application.planning.governance.GovernanceCadencePublication.encode(plan)));
        var annotated=new Draft(original.policy(),original.phase(),original.reason(),original.kind(),original.command(),original.purpose(),original.domain(),detail);
        return new PlanningResult.ActionSelected(annotated.command().orElseThrow(),new PlanTrace(request.before(),List.of(),Optional.of(annotated)));
    }

}
