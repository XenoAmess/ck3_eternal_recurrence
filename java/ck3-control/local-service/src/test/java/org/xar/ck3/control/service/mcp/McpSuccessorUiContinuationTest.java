package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.OrdinarySessionResource;

/** Real coordinator child -> explicitly DATA-only terminal parent/report -> shared UI JSON,
 * MCP response/real SDK and REST consumers. No Controller, Root PendingToken, finalized proof,
 * actual succession, physical UI clearance, SAVE or gameplay qualification is constructed here. */
final class McpSuccessorUiContinuationTest {
    @TempDir Path directory;
    private static final OperationKey CHILD = new OperationKey("fixture-successor-ui-report-child");

    @Test void actualUnknownChildRemainsPendingThroughMcpSdkAndRestWithoutAnotherAttempt() throws Exception {
        try (var fixture=fixture(true,"unknown")) {
            var child=fixture.coordinator.execute(fixture.command("actual-ui-unknown-child"));
            assertEquals(ActionReceipt.Outcome.UNRESOLVED,child.outcome());
            assertInstanceOf(CommandOrigin.Gameplay.class,child.command().origin());
            fixture.writer.locked(same->{
                var report=reportData(fixture,same,child,true,CompositeContinuationToken.Kind.SUCCESSOR_UI_CLOSE);
                var ui=assertConsumers(fixture,same,report,List.of(child));
                assertEquals("UNRESOLVED",ui.path("new_child_attempts").get(0).path("outcome").textValue());
                assertFalse(child.settled());assertFalse(child.visibleGameplay());assertFalse(child.eligibleAdvance());
                return null;
            });
        }
    }

    @Test void actualRejectedChildDoesNotTurnTheOriginalUnresolvedParentIntoAppliedOrReadonly() throws Exception {
        try (var fixture=fixture(false,"rejected")) {
            var child=fixture.coordinator.execute(fixture.command("actual-ui-rejected-child"));
            assertEquals(ActionReceipt.Outcome.REJECTED_CONFIRMED,child.outcome());
            assertTrue(child.ack().orElseThrow().nativeOk(),"transport ACK is separate from the rejected business result");
            fixture.writer.locked(same->{
                var report=reportData(fixture,same,child,true,CompositeContinuationToken.Kind.SUCCESSOR_UI_EVENT);
                var ui=assertConsumers(fixture,same,report,List.of(child));
                assertEquals("REJECTED_CONFIRMED",ui.path("new_child_attempts").get(0).path("outcome").textValue());
                assertFalse(report.execution().lifecycleTurns().getFirst().receipt().settled());
                return null;
            });
        }
    }

    @Test void noNewAttemptHasAnEmptyChildListAndStillUsesTheOriginalParent() throws Exception {
        try (var fixture=fixture(true,"no-child")) {
            var actualEarlierChild=fixture.coordinator.execute(fixture.command("actual-earlier-ui-child"));
            fixture.writer.locked(same->{
                var report=reportData(fixture,same,actualEarlierChild,false,CompositeContinuationToken.Kind.SUCCESSOR_UI_CLOSE);
                var ui=assertConsumers(fixture,same,report,List.of());
                assertEquals("NO_NEW_CHILD_ATTEMPT",ui.path("disposition").textValue());
                assertTrue(ui.path("new_child_attempts").isEmpty());
                var turn=report.execution().lifecycleTurns().getFirst();
                assertThrows(IllegalArgumentException.class,()->new BatchReport.LifecycleTurn(1,turn.current(),turn.receipt(),true,turn.successorUiContinuation()));
                return null;
            });
        }
    }

    @Test void malformedOrUnretainedContinuationDataCannotEnterEitherPublicProjection() throws Exception {
        try (var fixture=fixture(true,"invalid")) {
            var child=fixture.coordinator.execute(fixture.command("actual-ui-invalid-cases-child"));
            fixture.writer.locked(same->{
                var report=reportData(fixture,same,child,true,CompositeContinuationToken.Kind.SUCCESSOR_UI_CLOSE);
                var known=known(fixture,same);
                var original=McpAutoTurnEncoder.encode(report,known,fixture.archive.withSession(same),List.of());
                var row=McpJson.object(McpJson.parse(original.original().bytes()));
                var ui=(ObjectNode)row.get("successor_ui_continuation");
                for(String field:List.of("kind","disposition","canonical_domain","actual_published_driver","canonical_publication_proof")) {
                    var missing=ui.deepCopy();missing.remove(field);
                    assertThrows(RuntimeException.class,()->SuccessorUiContinuationJson.validate(missing));
                }
                var claimedParent=ui.deepCopy();claimedParent.put("new_parent_submitted",true);
                assertThrows(IllegalArgumentException.class,()->SuccessorUiContinuationJson.validate(claimedParent));
                var lossySequence=ui.deepCopy();((ObjectNode)lossySequence.path("new_child_attempts").get(0)).put("writer_sequence",child.sequence());
                assertThrows(IllegalArgumentException.class,()->SuccessorUiContinuationJson.validate(lossySequence));
                var leadingZero=ui.deepCopy();((ObjectNode)leadingZero.path("new_child_attempts").get(0)).put("writer_sequence","01");
                assertThrows(IllegalArgumentException.class,()->SuccessorUiContinuationJson.validate(leadingZero));
                var duplicate=ui.deepCopy();((ArrayNode)duplicate.get("new_child_attempts")).add(duplicate.path("new_child_attempts").get(0).deepCopy());
                assertThrows(IllegalArgumentException.class,()->SuccessorUiContinuationJson.validate(duplicate));
                var readonly=row.deepCopy();readonly.putObject("original_action_reconciliation").put("action_id",ui.path("original_parent_action_id").textValue()).put("new_action_submitted",false);
                assertThrows(IllegalArgumentException.class,()->McpAutoTurnEncoder.parse(new RawJson(McpJson.encode(readonly))));
                var differentParent=row.deepCopy();((ObjectNode)differentParent.path("successor_ui_continuation")).put("original_parent_action_id","other-parent");
                assertThrows(IllegalArgumentException.class,()->McpAutoTurnEncoder.parse(new RawJson(McpJson.encode(differentParent))));
                var unretained=new ActionReceipt(child.version(),child.sequence()+1,child.command(),child.bodySha256(),child.state());
                var altered=withChildren(report,List.of(unretained));
                assertThrows(RuntimeException.class,()->McpAutoTurnEncoder.encode(altered,known,fixture.archive.withSession(same),List.of()));
                return null;
            });
        }
    }

    private static ObjectNode assertConsumers(ActionWriterIntegrationFixture fixture,Session same,
            SessionController.TurnReport report,List<ActionReceipt> expectedChildren) throws IOException {
        String head=same.head().digest();int writes=fixture.nativeActionWrites(),reads=fixture.nativeReadWrites();
        var payload=McpAutoTurnEncoder.encode(report,known(fixture,same),fixture.archive.withSession(same),List.of());
        assertEquals(McpAutoTurnEncoder.Status.PENDING,payload.status(),"the original DATA-only parent is still unresolved");
        assertArrayEquals(payload.original().bytes(),McpAutoTurnEncoder.parse(payload.original()).original().bytes());
        var row=McpJson.object(McpJson.parse(payload.original().bytes()));
        assertTrue(row.path("plan").isNull());assertTrue(row.path("planning_source_frame").isNull());
        assertTrue(row.has("lifecycle_source_frame"));assertFalse(row.has("original_action_reconciliation"));
        assertFalse(row.path("public_result_available").booleanValue());
        assertTrue(row.path("result").path("never_replay").booleanValue());assertFalse(row.path("result").has("accepted"));
        var pass=report.execution().lifecycleTurns().getFirst().successorUiContinuation().orElseThrow();
        var shared=SuccessorUiContinuationJson.encode(pass);
        assertEquals(shared,row.get("successor_ui_continuation"));SuccessorUiContinuationJson.validate(shared);
        assertFalse(shared.path("new_parent_submitted").booleanValue());
        assertEquals(expectedChildren.size(),shared.path("new_child_attempts").size());
        for(int index=0;index<expectedChildren.size();index++) {
            var child=expectedChildren.get(index);var encoded=shared.path("new_child_attempts").get(index);
            assertEquals(child,fixture.archive.loadReceipt(fixture.archive.receiptReferenceOf(child)));
            assertEquals(child.command().actionId(),encoded.path("action_id").textValue());
            assertEquals(child.bodySha256(),encoded.path("body_sha256").textValue());
            assertEquals(child.command().operation().value(),encoded.path("operation").textValue());
            assertEquals(Long.toString(child.sequence()),encoded.path("writer_sequence").textValue());
        }
        var rest=OrdinarySessionResource.report(report.execution());
        assertEquals(shared,rest.path("last_lifecycle_turns").get(0).path("successor_ui_continuation"));
        assertEquals(0,rest.path("applied_turns").intValue());assertEquals(0,rest.path("committed_saved_days").longValue());
        assertFalse(rest.path("last_lifecycle_turns").get(0).path("visible_gameplay").booleanValue());
        assertFalse(rest.path("last_lifecycle_turns").get(0).path("eligible_advance").booleanValue());
        assertEquals(rest,StrictJson.parse(StrictJson.canonical(rest,262_144)));
        var envelope=PublicMcpDirectory.CallResult.fromBusinessJson(payload.original());
        assertArrayEquals(envelope.bytes(),new PublicMcpDirectory.CallResult(envelope.bytes()).bytes());
        var publicResult=McpJson.object(McpJson.parse(envelope.bytes()));
        assertFalse(publicResult.path("isError").booleanValue());
        assertEquals(row,publicResult.path("structuredContent"));
        assertEquals(row,McpJson.parse(publicResult.path("content").get(0).path("text").textValue().getBytes(StandardCharsets.UTF_8)));
        sdk(envelope);
        assertEquals(head,same.head().digest());assertEquals(writes,fixture.nativeActionWrites());assertEquals(reads,fixture.nativeReadWrites());
        assertEquals(0,report.execution().committedSavedDays());assertFalse(report.execution().dirtySinceSave());
        return shared;
    }

    /** This parent is retained report DATA, never entered in the action journal or a Controller/Root. */
    private static SessionController.TurnReport reportData(ActionWriterIntegrationFixture fixture,Session same,
            ActionReceipt child,boolean newAttempt,CompositeContinuationToken.Kind kind) throws IOException {
        fixture.writer.requireSession(same);var before=child.command().before();
        ExactRef nativeRole=data(fixture,"lifecycle-native-role-data"),hello=data(fixture,"lifecycle-hello-role-data"),
                manifest=data(fixture,"lifecycle-manifest-role-data"),driver=data(fixture,"lifecycle-driver-role-data"),source=data(fixture,"lifecycle-source-role-data");
        var current=new LifecycleIdentity(before.machineId(),before.game(),child.command().sessionId(),BigInteger.ONE,
                new LifecycleIdentity.Subject(BigInteger.valueOf(29829),"prior-episode-report-data",1,1),
                new LifecycleIdentity.Frame(before.frame().snapshotId(),before.frame().revision(),before.frame().identity().nativeRevision(),
                        before.frame().identity().dateRaw(),true,true),
                new LifecycleIdentity.Character(before.frame().identity().player(),true),LifecycleIdentity.TerminalReason.CHANGED,
                new LifecycleIdentity.Evidence(nativeRole,hello,manifest,driver,source),Instant.now());
        var operation=LifecycleExpectedPostcondition.Operation.CONTINUE_SUCCESSOR;
        var flags=List.<ExpectedValue>of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"),false),
                new ExpectedBoolean(new FieldKey("timeline.advance_verified"),false),new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"),false));
        var command=new ActionCommand("retained-ui-parent-report-data",new CommandOrigin.LifecycleTerminal(current),child.command().source(),
                child.command().sessionId(),operation.key(),new OpportunityJson.Obj(Map.of()),
                new CommandExpectation.LifecycleTerminal(new LifecycleExpectedPostcondition(current,child.command().source(),"fixture-ui-report-data/v1",operation,flags)),
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),Instant.now().plusSeconds(30));
        var parent=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),
                new ActionState.Unknown(Optional.empty(),Optional.empty(),"report DATA has no private finalized lifecycle producer",List.of(source)));
        fixture.archive.preserveReceipt(parent);
        var continuation=new CompositeContinuationReport(parent,newAttempt?List.of(child):List.of(),
                newAttempt?CompositeContinuationReport.Disposition.NEW_CHILD_ATTEMPT:CompositeContinuationReport.Disposition.NO_NEW_CHILD_ATTEMPT);
        var pass=new BatchReport.SuccessorUiContinuation(kind,continuation,data(fixture,"domain-role-data"),
                data(fixture,"published-driver-role-data"),data(fixture,"publication-proof-role-data"));
        var turn=new BatchReport.LifecycleTurn(1,current,parent,false,Optional.of(pass));
        var tick=new SessionClock.Tick(1,Instant.now());
        return new SessionController.TurnReport(new BatchReport(new SessionIdentity(before.machineId(),before.game(),command.sessionId()),
                "successor-ui-report-data",BatchReport.Terminal.ACTION_UNKNOWN,"typed report DATA only; actual Root private completion remains unavailable",
                tick,tick,List.of(),List.of(),List.of(),List.of(turn),List.of(),List.of(),Optional.empty(),Optional.empty(),Optional.empty(),
                Optional.empty(),Optional.empty(),0,0,false,List.of(),List.of(),List.of()));
    }
    private static ExactRef data(ActionWriterIntegrationFixture fixture,String role) {
        return fixture.archive.preserveMaterial(new RawJson(("{\"typed_report_data_only\":\""+role+"\"}").getBytes(StandardCharsets.UTF_8)));
    }

    private static SessionController.TurnReport withChildren(SessionController.TurnReport original,List<ActionReceipt> children) {
        var r=original.execution();var old=r.lifecycleTurns().getFirst();var p=old.successorUiContinuation().orElseThrow();
        var pass=new BatchReport.SuccessorUiContinuation(p.kind(),new CompositeContinuationReport(p.actual().parent(),children,
                CompositeContinuationReport.Disposition.NEW_CHILD_ATTEMPT),p.canonicalDomain(),p.actualPublishedDriver(),p.canonicalPublicationProof());
        var turn=new BatchReport.LifecycleTurn(old.index(),old.current(),old.receipt(),false,Optional.of(pass));
        return new SessionController.TurnReport(new BatchReport(r.session(),r.batchId(),r.terminal(),r.detail(),r.began(),r.ended(),r.phases(),
                r.turns(),r.reconciliations(),List.of(turn),r.readPublicationReconciliations(),r.revisionReplans(),r.lastPlan(),r.lastTerminalObservation(),
                r.lastLifecycle(),r.lastSavedPair(),r.committedLedgerHead(),r.committedSavedDays(),r.eligibleAdvancesSinceSave(),r.dirtySinceSave(),
                r.pendingAnalysisBatchIds(),r.completedAnalyses(),r.failedAnalysisBatchIds()));
    }
    private ActionWriterIntegrationFixture fixture(boolean loseAck,String name) throws Exception {
        var held=new AtomicReference<ActionWriterIntegrationFixture>();
        var scenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(CHILD,"game.command."+CHILD.value(),(command,attempt,dispatch)->{
            var actual=held.get();var ack=assertInstanceOf(NativeActionPort.AckReceived.class,dispatch);
            return new ActionPorts.RejectionObserved(new ActionState.Rejected(attempt.requestId(),"controlled original UI child rejected",
                    actual.archive.referenceOf(ack)));
        },()->{},()->new RawJson(DriverJson.encode(new OpportunityJson.Obj(Map.of("accepted",new OpportunityJson.Bool(false))))));
        var fixture=new ActionWriterIntegrationFixture(directory.resolve(name),loseAck,scenario);held.set(fixture);return fixture;
    }
    private static DriverSnapshotFacts.Known known(ActionWriterIntegrationFixture actual,Session same) throws IOException {
        return actual.driverAuthority().withFrozenFacts(same,frozen->assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state()));
    }
    /** Authored for the full CI step. This source-only task does not run Python/SDK processes. */
    private static void sdk(PublicMcpDirectory.CallResult result) throws IOException {
        String python=System.getProperty("xar.python"),repository=System.getProperty("xar.repository.root");
        assertNotNull(python,"canonical Python is mandatory");assertFalse(python.isBlank());
        assertNotNull(repository,"canonical repository is mandatory");assertFalse(repository.isBlank());
        String code="""
                import sys,json,importlib.metadata as m
                assert m.version('mcp')=='2.0.0'
                from mcp.types import CallToolResult
                raw=sys.stdin.buffer.read(); original=json.loads(raw)
                actual=CallToolResult.model_validate_json(raw)
                encoded=actual.model_dump(mode='json',by_alias=True,exclude_none=True)
                assert encoded['structuredContent']==original['structuredContent']
                assert encoded['isError'] is False
                assert json.loads(actual.content[0].text)==actual.structuredContent
                row=actual.structuredContent
                assert row['status']=='pending' and row['public_result_available'] is False
                assert row['result']['never_replay'] is True
                assert 'original_action_reconciliation' not in row
                ui=row['successor_ui_continuation']
                assert ui['new_parent_submitted'] is False
                assert ui['original_parent_action_id']==row['result']['action_id']
                for child in ui['new_child_attempts']:
                    assert type(child['writer_sequence']) is str
                    assert child['outcome'] in ('UNRESOLVED','REJECTED_CONFIRMED')
                sys.stdout.write('actual-mcp-ui-consumer-ok')
                """;
        try {
            var process=new ProcessBuilder(python,"-B","-c",code).directory(Path.of(repository).toFile()).redirectErrorStream(true).start();
            try(var input=process.getOutputStream()){input.write(result.bytes());}
            if(!process.waitFor(30,TimeUnit.SECONDS)){process.destroyForcibly();throw new AssertionError("actual MCP SDK consumer timed out");}
            byte[] output=process.getInputStream().readNBytes(65_537);assertTrue(output.length<=65_536,"bounded SDK diagnostics required");
            String text=new String(output,StandardCharsets.UTF_8);assertEquals(0,process.exitValue(),text);assertEquals("actual-mcp-ui-consumer-ok",text);
        }catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("actual SDK consumer interrupted",interrupted);}
    }
}
