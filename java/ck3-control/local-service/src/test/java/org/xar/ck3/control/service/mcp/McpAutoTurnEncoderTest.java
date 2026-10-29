package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Arrays;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.nativebridge.McpAutoSavedBaselineFixture;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.application.session.SessionPorts.*;

/** Calls the actual shared Controller producer; tests never call Game or a private HTTP presenter. */
final class McpAutoTurnEncoderTest {
    @TempDir Path temporary;
    private static final Instant NOW=Instant.parse("2026-10-23T18:00:00Z");
    private static final BigInteger MAX64=new BigInteger("18446744073709551615");
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(MAX64));
    private static final SessionIdentity SESSION=new SessionIdentity("source-fixture-machine",GAME,"same-held-session");
    private static final String DRIVER="""
        {"format_version":2,"pipe_name":"source-fixture","bridge_pid":42,"episode_character_id":73,"episode_run_id":"source-episode",
         "last_checkpoint":null,"command_history":[],"rollback_war_failure":null,"managed_restore_transaction":null,
         "succession_expectation":null,"succession_lifecycle":null,"campaign_goal":null,"rollback_war_failures":[]}
        """;
    private static byte[] bytes(String value){return value.getBytes(StandardCharsets.UTF_8);}
    private static ExactRef ref(byte[] value){return new ExactRef("memory/"+DriverJson.sha256(value),value.length,DriverJson.sha256(value));}
    private static final ExactRef SOURCE=ref(bytes("actual software fixture source"));
    private static DriverSnapshotFacts.Known known(){return DriverFactsRepository.imported(ref(bytes(DRIVER)),bytes(DRIVER),1,1,GAME,new OpportunityJson.Obj(Map.of()));}
    private static PlanningRequest request(Instant deadline) {
        var before=new ObservationIdentity(SESSION.machineId(),GAME,new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(73),MAX64,BigInteger.valueOf(53144328)),"original-frame",MAX64,"source-episode"),1);
        var snapshot=DriverJson.object(bytes("{\"paused\":true,\"map_ready\":true,\"revision\":"+MAX64+",\"native_revision\":"+MAX64+",\"date_raw\":53144328,\"snapshot_id\":\"original-frame\",\"episode_run_id\":\"source-episode\",\"played_character\":{\"character_id\":73},\"active_wars\":[],\"player_armies\":[]}"),65536);
        var observation=new PlanningObservation(snapshot,List.of(),Set.of(new OperationKey("fixture-world-action")),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
        return new PlanningRequest(before,new G2Source(SESSION.machineId(),NOW.toString(),"source-bound-fixture",SOURCE),SESSION.sessionId(),deadline,observation);
    }
    private static ActionCommand command(PlanningRequest request) {return command(request,"actual-action");}
    private static ActionCommand command(PlanningRequest request,String actionId) {
        return new ActionCommand(actionId,request.before(),request.source(),request.sessionId(),new OperationKey("fixture-world-action"),new OpportunityJson.Obj(Map.of()),
                new ExpectedPostcondition(1,request.before(),request.source(),"fixture/v1",List.of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"),true))),
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),request.deadline());
    }
    private static final class TestClock implements SessionClock {
        long nanos;@Override public Tick now(){nanos+=1_000_000;return new Tick(nanos,NOW.plusNanos(nanos));}
        @Override public void waitFor(Duration duration){nanos+=duration.toNanos();}
    }
    private static SessionController controller(boolean complete,AtomicInteger submissions,Archive archive) {
        return controller(complete,submissions,archive,(expected,deadline)->componentReady(archive,deadline));
    }
    private static SessionController controller(boolean complete,AtomicInteger submissions,Archive archive,ObservationPort observed) {
        return controller(complete,submissions,archive,observed,Optional.empty());
    }
    private static SessionController controller(boolean complete,AtomicInteger submissions,Archive archive,ObservationPort observed,Optional<OrdinaryPlanCompletion.Published> refresh) {
        var component=archive.componentInputs();
        CheckpointFiles files=new CheckpointFiles(){
            @Override public Optional<CheckpointPair.FileWitness> observe(Path path){throw new AssertionError("AUTO cannot read SAVE files");}
            @Override public byte[] read(CheckpointPair.FileWitness value,int maximum){throw new AssertionError("AUTO cannot read SAVE files");}
            @Override public CheckpointPair.FileWitness replace(Path path,byte[] value){throw new AssertionError("AUTO cannot write SAVE files");}
            @Override public CheckpointPair.FileWitness createNew(Path path,byte[] value){throw new AssertionError("AUTO cannot create SAVE files");}
            @Override public CheckpointPair.FileWitness copyNew(CheckpointPair.FileWitness source,Path target){throw new AssertionError("AUTO cannot copy SAVE files");}};
        DriverCheckpointStore.SnapshotSupplier supplier=new DriverCheckpointStore.SnapshotSupplier(){@Override public <T>T withFrozen(DriverCheckpointStore.SnapshotWork<T> work){throw new AssertionError("AUTO cannot SAVE");}};
        var drivers=new DriverCheckpointStore(files,Path.of("D:/fixture/Driver.json"),"source-fixture",supplier);
        CheckpointRequest.ObservationPort readiness=deadline->{throw new AssertionError("AUTO cannot begin SAVE readiness");};
        var saves=new CheckpointService(files,drivers,readiness,Path.of("D:/fixture/evidence"),Clock.fixed(NOW,ZoneOffset.UTC),(pair,receipt)->{throw new AssertionError("AUTO cannot seed SAVE");});
        var realm=new RealmLifecycle(SOURCE);
        List<OrdinaryPolicy> policies=complete?Arrays.stream(PlanningStage.values()).<OrdinaryPolicy>map(stage->{
            if(stage==PlanningStage.REALM_MEMBERSHIP_PUBLICATION)return realm;
            return new OrdinaryPolicy(){public PlanningStage stage(){return stage;}public ExactRef implementationSource(){return SOURCE;}
                public Decision evaluate(PlanningRequest input,Draft previous){return stage==PlanningStage.ORDINARY_CORE?
                    new Replace(new Draft("actual-policy","actual-phase","actual-reason",Kind.ORDINARY,Optional.of(command(input,refresh.isPresent()?"original-parent":"actual-action")),Purpose.WORLD_ACTION,Optional.empty(),new OpportunityJson.Obj(Map.of())),"actual selection"):new Keep("preserve preceding plan");}};
        }).toList():List.of();
        ActionCoordinatorPort actions=new ActionCoordinatorPort(){public ActionReceipt execute(ActionCommand actual){submissions.incrementAndGet();
                if(refresh.isPresent())throw new ReadPublicationRefreshException(actual,Optional.empty(),refresh.orElseThrow(),Optional.of("original-parent"));
                var receipt=new ActionReceipt(1,1,actual,ActionCodec.bodySha256(actual),new ActionState.Unknown(Optional.empty(),Optional.empty(),"actual completion unobserved",List.of(SOURCE)));archive.preserveReceipt(receipt);return receipt;}
            public ActionReceipt reconcile(String id){return archive.receipts.values().stream().filter(row->row.command().actionId().equals(id)).findFirst().orElseThrow(()->new AssertionError("reconciliation may only read its archived original UNKNOWN"));}};
        var depth=new AtomicInteger();
        OrdinaryPlanCompletion completion=new OrdinaryPlanCompletion.PlanningScope(){
            public PlanningDisposition afterPlanning(PlanningRequest input,PlanningResult plan){assertEquals(1,depth.get());return new Unchanged("no domain publication");}
            public ExecutionDisposition afterExecution(ActionReceipt actual){assertEquals(0,depth.get());return new Unchanged("original component receipt consumed");}
            public <T> ScopeResult<T> inPlanningScope(ScopeWork<T> work) throws IOException,InterruptedException {
                assertEquals(0,depth.getAndIncrement());
                try{return new ScopeResult<>(work.run(),Optional.empty());}finally{assertEquals(1,depth.getAndDecrement());}
            }};
        BatchJournal journal=new BatchJournal(){
            @Override public JournalCommit commit(JournalInput input){
                assertEquals(SESSION,input.session());assertTrue(input.pair().isEmpty(),"component AUTO never confirms SAVE");
                archive.journalKinds.add(input.kind());
                var row=StrictJson.object().put("scope","controller-codec-component-only").put("batch_id",input.batchId()).put("kind",input.kind().name());
                return new JournalCommit(archive.preserveMaterial(new RawJson(StrictJson.canonical(row))),0);
            }
            @Override public Optional<CompletedCycleProof> cycleProof(SessionIdentity owner,SemanticEvidence semantic){
                assertEquals(SESSION,owner);
                if(!semantic.equals(component.semantic()))return Optional.empty();
                semantic.references().forEach(archive::loadFullMaterial);
                return Optional.of(new CompletedCycleProof(0,semantic,component.cycleDigest()));
            }};
        var controller=new SessionController(SESSION,(expected,deadline)->new GameLifecycle.Running(GAME,SOURCE),observed,
                new OrdinaryPlanner(policies,Clock.fixed(NOW,ZoneOffset.UTC),realm),actions,saves,new CheckpointRequestFactory(Path.of("D:/fixture/save.ck3"),readiness),
                journal,work->{throw new AssertionError("no incident captured");},new TestClock(),Optional.of(component.pair()),0,completion,
                (owner,actual,fresh)->{throw new AssertionError("ordinary software fixture cannot publish an episode handoff");});
        controller.bindRetainedIncidents(List::of);return controller;
    }
    @Test void actualControllerUnknownToOriginalPublicWireAndParserDoesNotRetryOrGrantCredit() throws IOException {
        var archive=new Archive();var submissions=new AtomicInteger();var controller=controller(true,submissions,archive);
        var actual=controller.autoTurn(NOW.plusSeconds(5));assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,actual.execution().terminal());
        var probes=new AtomicInteger();AutoFailureDiagnostic.Port absent=(receipt,held)->{assertSame(archive,held);probes.incrementAndGet();return Optional.empty();};
        var encoded=McpAutoTurnEncoder.encode(actual,known(),archive,List.of(absent));
        assertEquals(1,submissions.get());assertEquals(1,probes.get());assertTrue(controller.isQuarantined());assertEquals(0,actual.execution().committedSavedDays());
        var wire=McpJson.object(McpJson.parse(encoded.original().bytes()));assertEquals("pending",wire.path("status").textValue());
        assertEquals(MAX64.toString(),wire.path("revision").textValue());assertEquals(MAX64.toString(),wire.path("planning_source_frame").path("native_revision").textValue());
        assertTrue(wire.path("planning_source_frame").path("connection_generation").isNull());assertEquals("partial",wire.path("planning_source_frame").path("status").textValue());
        assertEquals("fixture-world-action",wire.path("selected_step").textValue());assertTrue(wire.path("result").path("never_replay").booleanValue());
        assertFalse(wire.path("public_result_available").booleanValue());assertFalse(wire.path("result").has("accepted"));
        assertArrayEquals(encoded.original().bytes(),McpAutoTurnEncoder.parse(encoded.original()).original().bytes());
        try(var input=getClass().getResourceAsStream("/mcp/original-auto-source-frame-oracle.json")) {
            assertNotNull(input);var oracle=McpJson.object(McpJson.parse(input.readAllBytes()));
            assertEquals(oracle.get("cases").get(1).get("expected_public"),wire.get("planning_source_frame"));
        }
    }
    @Test void actualIncompletePlannerProducerReportsBlockedWithoutFabricatingAnAction() {
        var archive=new Archive();var submissions=new AtomicInteger();var actual=controller(false,submissions,archive).autoTurn(NOW.plusSeconds(5));
        assertEquals(BatchReport.Terminal.INCOMPLETE_MIGRATION,actual.execution().terminal());
        var encoded=McpAutoTurnEncoder.encode(actual,known(),archive,List.of());assertEquals(McpAutoTurnEncoder.Status.BLOCKED,encoded.status());
        var row=McpJson.object(McpJson.parse(encoded.original().bytes()));assertFalse(row.has("selected_step"));assertFalse(row.has("result"));assertEquals(0,submissions.get());
    }
    @Test void actualTerminalControllerRetainsMissingPlayerWithoutAnOrdinaryPlanningIdentity() {
        var source=request(NOW.plusSeconds(5)).source();
        var identity=new LifecycleIdentity(SESSION.machineId(),GAME,SESSION.sessionId(),MAX64,
                new LifecycleIdentity.Subject(BigInteger.valueOf(73),"source-episode",1,1),
                new LifecycleIdentity.Frame("terminal-source",MAX64,MAX64,BigInteger.valueOf(53144328),true,true),new LifecycleIdentity.Missing(),LifecycleIdentity.TerminalReason.MISSING,
                new LifecycleIdentity.Evidence(ref(bytes("native")),ref(bytes("hello")),ref(bytes("manifest")),ref(bytes(DRIVER)),ref(bytes("qualification"))),NOW);
        var archive=new Archive();var submissions=new AtomicInteger();
        ObservationPort observed=(expected,deadline)->{
            var operation=LifecycleExpectedPostcondition.Operation.DEATH_TERMINAL;
            var expectation=new LifecycleExpectedPostcondition(identity,source,"fixture-terminal/v1",operation,List.of(
                    new ExpectedBoolean(new FieldKey("native.gameplay_verified"),false),new ExpectedBoolean(new FieldKey("timeline.advance_verified"),false),new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"),false)));
            var command=new ActionCommand("terminal-original",new CommandOrigin.LifecycleTerminal(identity),source,SESSION.sessionId(),operation.key(),
                    new OpportunityJson.Obj(Map.of("expected_revision",new OpportunityJson.IntegerValue(MAX64))),new CommandExpectation.LifecycleTerminal(expectation),
                    new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),deadline);
            assertThrows(IllegalStateException.class,command::before);return new TerminalReady(identity,new TerminalAction(command));};
        var actual=controller(false,submissions,archive,observed).autoTurn(NOW.plusSeconds(5));
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,actual.execution().terminal());assertEquals(1,actual.execution().lifecycleTurns().size());assertTrue(actual.execution().turns().isEmpty());
        var encoded=McpAutoTurnEncoder.encode(actual,known(),archive,List.of());var row=McpJson.object(McpJson.parse(encoded.original().bytes()));
        assertEquals("pending",row.path("status").textValue());assertTrue(row.path("planning_source_frame").isNull());assertTrue(row.path("plan").isNull());
        assertEquals("MISSING",row.path("lifecycle_source_frame").path("current_player").path("kind").textValue());assertEquals(identity,LifecycleIdentityCodec.decode(row.get("lifecycle_source_frame")));
        assertEquals(MAX64.toString(),row.path("revision").textValue());assertEquals(1,submissions.get());assertEquals(0,actual.execution().committedSavedDays());
        assertArrayEquals(encoded.original().bytes(),McpAutoTurnEncoder.parse(encoded.original()).original().bytes());
        var blockedSubmissions=new AtomicInteger();var blocked=controller(false,blockedSubmissions,archive,
                (owner,deadline)->new TerminalReady(identity,new TerminalBlocked("actual private custody unavailable",List.of(identity.nativeEvidence())))).autoTurn(NOW.plusSeconds(5));
        assertEquals(BatchReport.Terminal.INCOMPLETE_MIGRATION,blocked.execution().terminal());
        var blockedWire=McpJson.object(McpJson.parse(McpAutoTurnEncoder.encode(blocked,known(),archive,List.of()).original().bytes()));
        assertEquals("blocked",blockedWire.path("status").textValue());assertTrue(blockedWire.path("planning_source_frame").isNull());
        assertEquals(identity,LifecycleIdentityCodec.decode(blockedWire.get("lifecycle_source_frame")));assertFalse(blockedWire.has("selected_step"));assertEquals(0,blockedSubmissions.get());
        var ordinary=controller(true,new AtomicInteger(),archive).autoTurn(NOW.plusSeconds(5));
        assertEquals(1,ordinary.execution().turns().size());
        var reconcileSubmissions=new AtomicInteger();var reconciled=controller(false,reconcileSubmissions,archive,
                (owner,deadline)->new TerminalReady(identity,new TerminalReconciliation("actual-action"))).autoTurn(NOW.plusSeconds(5));
        assertEquals(1,reconciled.execution().lifecycleTurns().size());assertInstanceOf(CommandOrigin.Gameplay.class,reconciled.execution().lifecycleTurns().getFirst().receipt().command().origin());
        var reconcileWire=McpJson.object(McpJson.parse(McpAutoTurnEncoder.encode(reconciled,known(),archive,List.of()).original().bytes()));
        assertTrue(reconcileWire.path("plan").isNull());assertEquals("original-frame",reconcileWire.path("planning_source_frame").path("snapshot_id").textValue());
        assertEquals(identity,LifecycleIdentityCodec.decode(reconcileWire.get("terminal_reconciliation_frame")));assertFalse(reconcileWire.has("lifecycle_source_frame"));assertEquals(0,reconcileSubmissions.get());
    }
    @Test void parserRejectsMissingWrongTypedAndInconsistentActualFrameOrResult() {
        var archive=new Archive();var actual=controller(true,new AtomicInteger(),archive).autoTurn(NOW.plusSeconds(5));
        var original=McpJson.object(McpJson.parse(McpAutoTurnEncoder.encode(actual,known(),archive,List.of()).original().bytes()));
        for(int variant=0;variant<6;variant++) {var wrong=original.deepCopy();var frame=(com.fasterxml.jackson.databind.node.ObjectNode)wrong.get("planning_source_frame");
            switch(variant){case 0->wrong.remove("plan");case 1->frame.put("revision",true);case 2->frame.put("revision",MAX64);case 3->frame.put("native_revision","01");case 4->((com.fasterxml.jackson.databind.node.ObjectNode)wrong.get("result")).put("step",true);case 5->frame.put("status","complete");default->throw new AssertionError();}
            assertThrows(IllegalArgumentException.class,()->McpAutoTurnEncoder.parse(new RawJson(McpJson.encode(wrong))));}
    }
    @Test void typedFailureConsumerPreservesExactDiagnosticAndRejectsAnotherOriginalAction() {
        var archive=new Archive();var actual=controller(true,new AtomicInteger(),archive).autoTurn(NOW.plusSeconds(5));var receipt=actual.execution().turns().getFirst().receipt();
        var original=new RawJson(bytes("{\"schema\":\"xar.tactical-clock-failure.v1\",\"is_error\":true,\"never_replay\":true,\"credit\":0,\"step_result\":{\"revision\":\""+MAX64+"\"},\"wait_progress\":null}"));
        var diagnostic=new AutoFailureDiagnostic(AutoFailureDiagnostic.Kind.TACTICAL_CLOCK,receipt.command().actionId(),receipt.bodySha256(),"actual typed failure",original,archive.preserveMaterial(original));
        var failure=McpAutoFailure.fromDiagnostic(diagnostic,receipt);var envelope=McpJson.object(McpJson.parse(failure.result().bytes()));
        assertTrue(envelope.path("isError").booleanValue());assertEquals("StepPostconditionError",envelope.path("structuredContent").path("error_type").textValue());
        assertEquals(McpJson.parse(original.bytes()),envelope.path("structuredContent").path("diagnostics").get("tactical_clock_failure_v1"));
        var wrong=new AutoFailureDiagnostic(diagnostic.kind(),"another-action",diagnostic.actionBodySha256(),diagnostic.message(),original,diagnostic.originalEvidence());
        assertThrows(IllegalArgumentException.class,()->McpAutoFailure.fromDiagnostic(wrong,receipt));
        assertThrows(IllegalArgumentException.class,()->new AutoFailureDiagnostic(diagnostic.kind(),diagnostic.actionId(),diagnostic.actionBodySha256(),diagnostic.message(),new RawJson(bytes(new String(original.bytes(),StandardCharsets.UTF_8).replace("\"credit\":0","\"credit\":false"))),diagnostic.originalEvidence()));
    }
    @Test void actualReadPublicationRefreshReconcilesOriginalParentBeforeAnotherObservationAndPublicParserRetainsItsSource() {
        var archive=new Archive();var input=request(NOW.plusSeconds(5));var selected=command(input);
        var original=new ActionCommand("original-parent",selected.before(),selected.source(),selected.sessionId(),selected.operation(),selected.arguments(),selected.expected(),selected.claims(),selected.deadline());
        var receipt=new ActionReceipt(1,1,original,ActionCodec.bodySha256(original),new ActionState.Unknown(Optional.empty(),Optional.empty(),"actual original parent remains unknown",List.of(SOURCE)));archive.preserveReceipt(receipt);
        String state="{\"schema\":\"root.ck3.continuity-window/v1\",\"machine_id\":\"source-fixture-machine\",\"sequence\":0,\"window_id\":1,\"status\":\"running\",\"target_days\":10,\"start_date_raw\":53144328,\"target_date_raw\":53144568,\"last_settled_date_raw\":53144328,\"last_settled_cycles\":0,\"UNKNOWN\":{}}";
        var before=org.xar.ck3.control.continuity.ContinuityState.fromJson(McpJson.object(McpJson.parse(bytes(state))),SESSION.machineId());
        var after=org.xar.ck3.control.continuity.ContinuityState.fromJson(McpJson.object(McpJson.parse(bytes(state.replace("\"sequence\":0","\"sequence\":1")))),SESSION.machineId());
        var head=new org.xar.ck3.control.continuity.writer.WriterContracts.Head(before,List.of(),List.of(),List.of(),false);
        var publication=new OrdinaryPlanCompletion.Published(head,new org.xar.ck3.control.continuity.writer.WriterContracts.Receipt(org.xar.ck3.control.continuity.writer.WriterContracts.Disposition.COMMITTED,after,"b".repeat(64),1,false));
        var observations=new AtomicInteger();var attempts=new AtomicInteger();
        var actual=controller(true,attempts,archive,(owner,deadline)->{observations.incrementAndGet();return componentReady(archive,deadline);},Optional.of(publication)).autoTurn(NOW.plusSeconds(5));
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,actual.execution().terminal());assertEquals(1,observations.get());assertEquals(1,attempts.get());
        assertTrue(actual.execution().turns().isEmpty());assertEquals(1,actual.execution().readPublicationReconciliations().size());
        var payload=McpAutoTurnEncoder.encode(actual,known(),archive,List.of());var row=McpJson.object(McpJson.parse(payload.original().bytes()));
        assertEquals("pending",row.path("status").textValue());assertTrue(row.path("plan").isNull());assertEquals("original-frame",row.path("planning_source_frame").path("snapshot_id").textValue());
        assertEquals("original-parent",row.path("read_publication_reconciliation").path("original_action_id").textValue());
        assertEquals("b".repeat(64),row.path("read_publication_reconciliation").path("event_identity").textValue());assertFalse(row.path("original_action_reconciliation").path("new_action_submitted").booleanValue());
        assertArrayEquals(payload.original().bytes(),McpAutoTurnEncoder.parse(payload.original()).original().bytes());assertEquals(0,actual.execution().committedSavedDays());
        for(int variant=0;variant<3;variant++){var wrong=row.deepCopy();var source=(com.fasterxml.jackson.databind.node.ObjectNode)wrong.get("read_publication_reconciliation");
            switch(variant){case 0->source.put("event_identity",true);case 1->source.put("new_action_submitted",true);case 2->source.set("resulting_head_sha256",source.get("predecessor_sha256"));default->throw new AssertionError();}
            assertThrows(IllegalArgumentException.class,()->McpAutoTurnEncoder.parse(new RawJson(McpJson.encode(wrong))));}
    }
    @Test void missingCurrentSemanticRefusesBeforeOrdinarySubmission() {
        var archive=new Archive();var submissions=new AtomicInteger();
        var actual=controller(true,submissions,archive,(owner,deadline)->
                new Ready(request(deadline),CheckpointEligibility.SAFE,Optional.empty(),Optional.empty())).autoTurn(NOW.plusSeconds(5));
        assertEquals(BatchReport.Terminal.INCOMPLETE_MIGRATION,actual.execution().terminal());
        assertEquals(0,submissions.get());assertTrue(actual.execution().turns().isEmpty());
    }
    @Test void actualSoftwareSavedBaselineAndCanonicalUnknownFeedControllerAndPublicMcpWithoutAnotherSave()throws Exception {
        try(var fixture=McpAutoSavedBaselineFixture.open(temporary.resolve("actual-software-paired-auto"))) {
            var realm=new RealmLifecycle(fixture.source().sourceRef());
            var policies=Arrays.stream(PlanningStage.values()).<OrdinaryPolicy>map(stage->{
                if(stage==PlanningStage.REALM_MEMBERSHIP_PUBLICATION)return realm;
                return new OrdinaryPolicy(){
                    @Override public PlanningStage stage(){return stage;}
                    @Override public ExactRef implementationSource(){return fixture.source().sourceRef();}
                    @Override public Decision evaluate(PlanningRequest input,Draft previous){
                        if(stage!=PlanningStage.ORDINARY_CORE)return new Keep("preserve actual software plan");
                        var command=new ActionCommand("mcp-software-pause-original",input.before(),input.source(),input.sessionId(),
                                new OperationKey("pause-map"),new OpportunityJson.Obj(Map.of()),
                                new ExpectedPostcondition(1,input.before(),input.source(),"paused/v1",
                                        List.of(new ExpectedBoolean(new FieldKey("paused"),true))),
                                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),input.deadline());
                        return new Replace(new Draft("software-physical-auto","ordinary","consume actual saved baseline",Kind.ORDINARY,
                                Optional.of(command),Purpose.WORLD_ACTION,Optional.empty(),new OpportunityJson.Obj(Map.of())),"actual canonical pause attempt");
                    }
                };
            }).toList();
            var scopeDepth=new AtomicInteger();var consumed=new AtomicInteger();
            OrdinaryPlanCompletion completion=new OrdinaryPlanCompletion.PlanningScope(){
                @Override public PlanningDisposition afterPlanning(PlanningRequest input,PlanningResult planned){
                    assertEquals(1,scopeDepth.get());return new Unchanged("no software domain publication");
                }
                @Override public ExecutionDisposition afterExecution(ActionReceipt receipt){
                    assertEquals(0,scopeDepth.get());consumed.incrementAndGet();return new Unchanged("actual original receipt consumed");
                }
                @Override public <T> ScopeResult<T> inPlanningScope(ScopeWork<T> work)throws IOException,InterruptedException {
                    assertEquals(0,scopeDepth.getAndIncrement());
                    try{return new ScopeResult<>(work.run(),Optional.empty());}finally{assertEquals(1,scopeDepth.getAndDecrement());}
                }
            };
            var controller=new SessionController(fixture.owner(),(owner,deadline)->{
                    assertEquals(fixture.owner(),owner);return new GameLifecycle.Running(owner.game(),fixture.source().sourceRef());
                },fixture::observe,new OrdinaryPlanner(policies,Clock.systemUTC(),realm),fixture.actions(),fixture.checkpoints(),
                fixture.checkpointRequests(),fixture.batchJournal(),work->{throw new AssertionError("no offline incident");},
                new SessionClock.SystemClock(),Optional.of(fixture.pair()),0,completion,
                (owner,receipt,fresh)->{throw new AssertionError("no software episode handoff");});
            controller.bindRetainedIncidents(List::of);
            // Functional software wall budget; this does not change native frame freshness.
            var actual=controller.autoTurn(Instant.now().plusSeconds(120));
            assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,actual.execution().terminal(),actual.execution()::detail);
            assertEquals(1,actual.execution().turns().size());assertTrue(fixture.proofCalls()>0);
            var receipt=actual.execution().turns().getFirst().receipt();fixture.requireOriginalReceipt(receipt);
            assertFalse(receipt.settled());assertEquals(1,consumed.get());assertEquals(0,scopeDepth.get());
            assertEquals(2,fixture.nativeActionWrites(),"one baseline SAVE and one canonical pause, never a second SAVE");
            assertEquals(fixture.pair(),actual.execution().lastSavedPair().orElseThrow());
            assertEquals(0,actual.execution().committedSavedDays());assertTrue(controller.isQuarantined());
            var payload=McpAutoTurnEncoder.encode(actual,fixture.heldDriver(),fixture.archive(),List.of());
            var row=McpJson.object(McpJson.parse(payload.original().bytes()));
            assertEquals("pending",row.path("status").textValue());assertEquals("pause-map",row.path("selected_step").textValue());
            assertEquals(receipt.command().before().frame().revision().toString(),row.path("revision").textValue());
            assertEquals(receipt.command().before().frame().identity().nativeRevision().toString(),
                    row.path("planning_source_frame").path("native_revision").textValue());
            assertEquals("complete",row.path("planning_source_frame").path("status").textValue());
            assertTrue(row.path("result").path("never_replay").booleanValue());
            assertArrayEquals(payload.original().bytes(),McpAutoTurnEncoder.parse(payload.original()).original().bytes());
            controller.autoTurn(Instant.now().plusSeconds(5));
            assertEquals(2,fixture.nativeActionWrites(),"quarantine cannot repeat the original pause or create another SAVE");
        }
    }
    /** Controller DATA inputs only: these memory witnesses do not prove a physical SAVE, Native readiness or Root admission. */
    private record ComponentInputs(CheckpointPair pair,SemanticEvidence semantic,String cycleDigest) { }
    private static Ready componentReady(Archive archive,Instant deadline) {
        return new Ready(request(deadline),CheckpointEligibility.SAFE,Optional.empty(),Optional.of(archive.componentInputs().semantic()));
    }
    private static final class Archive implements ActionPorts.OutcomeArchive {
        final Map<ExactRef,RawJson> materials=new HashMap<>();final Map<ExactRef,ActionReceipt> receipts=new HashMap<>();
        final List<JournalKind> journalKinds=new ArrayList<>();private ComponentInputs components;
        private ExactRef componentMaterial(String role,RawJson value) {
            var reference=new ExactRef("D:/fixture/mcp-controller-component/"+role+"-"+DriverJson.sha256(value.bytes())+".json",
                    value.bytes().length,DriverJson.sha256(value.bytes()));
            materials.putIfAbsent(reference,value);return reference;
        }
        ComponentInputs componentInputs() {
            if(components!=null)return components;
            var input=request(NOW.plusSeconds(5));var snapshot=new RawJson(DriverJson.encode(input.observations().snapshot()));
            // Separate role references retain the same original component input; neither is a qualified Native capture.
            var semantic=componentMaterial("semantic-input",snapshot);
            var rawInput=componentMaterial("original-input",snapshot);
            var driver=componentMaterial("driver-input",new RawJson(bytes(DRIVER)));
            var stamp=componentMaterial("known-input",DriverSnapshotFacts.encodeKnownOriginal(known()));
            var evidence=new SemanticEvidence(input.before(),semantic,rawInput,stamp,driver,NOW);
            var save=componentMaterial("paired-data",new RawJson(bytes("{\"scope\":\"component-paired-input-not-physical-SAVE\"}")));
            var ack=componentMaterial("pair-source",new RawJson(bytes("{\"scope\":\"component-source-not-native-ACK\"}")));
            var pair=new CheckpointPair(new CheckpointPair.FileWitness(save,new FileStatIdentity(BigInteger.valueOf(save.bytes()),"9007199254740993","134000000000000001")),
                    new CheckpointPair.FileWitness(driver,new FileStatIdentity(BigInteger.valueOf(driver.bytes()),"9007199254740995","134000000000000003")),
                    input.before(),"controller-codec-component",1,"component-paired-input",ack,NOW);
            components=new ComponentInputs(pair,evidence,DriverJson.sha256(CheckpointPairCodec.encode(pair)));return components;
        }
        private UnsupportedOperationException unused(){return new UnsupportedOperationException("unrelated mutation outside actual AUTO software fixture");}
        public ExactRef preserveMaterial(RawJson value){var ref=ref(value.bytes());materials.putIfAbsent(ref,value);return ref;}
        public RawJson loadMaterial(ExactRef ref){var value=materials.get(ref);if(value==null || value.bytes().length!=ref.bytes() || !DriverJson.sha256(value.bytes()).equals(ref.sha256()))throw new IllegalArgumentException("actual immutable material absent/drift");return value;}
        @Override public RawJson loadFullMaterial(ExactRef ref){return RawJson.fullMaterial(loadMaterial(ref).bytes());}
        public ExactRef materialReferenceOf(RawJson value){var ref=ref(value.bytes());if(!materials.containsKey(ref))throw new IllegalArgumentException("actual material not archived");return ref;}
        public ExactRef preserveReceipt(ActionReceipt value){byte[] original=ActionReceiptCodec.encodeReceipt(value,this);var ref=ref(original);receipts.putIfAbsent(ref,ActionReceiptCodec.decodeReceipt(original,this));return ref;}
        public ActionReceipt loadReceipt(ExactRef ref){var value=receipts.get(ref);if(value==null)throw new IllegalArgumentException("actual receipt absent");return value;}
        public ExactRef receiptReferenceOf(ActionReceipt value){var ref=ref(ActionReceiptCodec.encodeReceipt(value,this));if(!value.equals(receipts.get(ref)))throw new IllegalArgumentException("actual original receipt not archived");return ref;}
        public ExactRef preserve(NativeActionPort.DispatchOutcome value){throw unused();}public NativeActionPort.DispatchOutcome load(ExactRef ref){throw unused();}
        public ExactRef preserveRequest(NativeRequest value){throw unused();}public NativeRequest loadRequest(ExactRef ref){throw unused();}
        public ExactRef referenceOf(NativeActionPort.DispatchOutcome value){throw unused();}public ExactRef requestReferenceOf(NativeRequest value){throw unused();}
        public ExactRef preserveRead(PlanningReadReceipt value){throw unused();}public PlanningReadReceipt loadRead(ExactRef ref){throw unused();}public ExactRef readReferenceOf(PlanningReadReceipt value){throw unused();}
        public ExactRef preserveRecord(ActionRecord value){throw unused();}public ActionRecord loadRecord(ExactRef ref){throw unused();}public ExactRef recordReferenceOf(ActionRecord value){throw unused();}
        public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value){throw unused();}public byte[] loadNativeFrame(ExactRef ref){throw unused();}
    }
}
