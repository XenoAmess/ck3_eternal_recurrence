package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.planning.PlanTrace;
import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.application.session.SessionPorts.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual coordinator/publication -> typed report DATA -> full encoder -> public MCP result consumers.
 * This does not mint Controller, private Root, native Game or SDK qualification. The real Controller
 * UNKNOWN producer remains covered by the original McpAutoTurnEncoderTest. */
final class McpAutoCanonicalCoverageFlowTest {
    @TempDir Path directory;
    private static final OperationKey OP=new OperationKey("fixture-full-auto-canonical-flow");
    @Test void actualCanonicalOnlyNoEffectRemainsBlockedThroughTheWholePublicEnvelope()throws Exception {
        try(var fixture=fixture(false)) {
            var source=new Materials(fixture);var publisher=new DriverActionHistoryPublisher(fixture.driverAuthority(),fixture.journal,fixture.archive,
                    source,List.of(fixture.observationSource().sourceRef()));
            fixture.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_ACTION_HISTORY_KIND,publisher);
            fixture.bindAdditionalArchivedVerifier(new NativeRecordedEvidenceVerifier.Binding(OP,fixture.observationSource().sourceRef(),
                    (head,receipt,archive)->source.requireRejected(receipt,archive)));
            var actual=fixture.coordinator.execute(fixture.command("full-auto-canonical-rejection"));
            assertEquals(ActionReceipt.Outcome.REJECTED_CONFIRMED,actual.outcome());
            fixture.writer.locked(same->{
                var published=assertInstanceOf(DriverActionHistoryPublisher.Published.class,publisher.completed(same,actual));
                assertTrue(published.legacyRow().isEmpty());var known=known(fixture,same);
                assertInstanceOf(DriverSnapshotFacts.CanonicalOnly.class,known.actionRows().getLast().coverageSource());
                String head=same.head().digest();int writes=fixture.nativeActionWrites(),reads=fixture.nativeReadWrites();
                assertTrue(actual.ack().orElseThrow().nativeOk(),"successful transport ACK is not an applied gameplay result");
                var payload=McpAutoTurnEncoder.encode(report(actual),known,fixture.archive.withSession(same),List.of());
                assertEquals(McpAutoTurnEncoder.Status.BLOCKED,payload.status());
                var envelope=PublicMcpDirectory.CallResult.fromBusinessJson(payload.original());
                var json=McpJson.object(McpJson.parse(envelope.bytes()));assertFalse(json.path("isError").booleanValue());
                assertEquals("blocked",json.path("structuredContent").path("status").textValue());
                assertFalse(json.path("structuredContent").path("public_result_available").booleanValue());
                assertArrayEquals(envelope.bytes(),new PublicMcpDirectory.CallResult(envelope.bytes()).bytes());
                assertEquals(head,same.head().digest());assertEquals(writes,fixture.nativeActionWrites());assertEquals(reads,fixture.nativeReadWrites());
                sdk(envelope);
                return null;
            });
        }
    }
    @Test void actualUnknownReportPreservesPendingUnavailableResultAndTextStructuredSerdeWithoutAnotherCall()throws Exception {
        try(var fixture=fixture(true)) {
            var actual=fixture.coordinator.execute(fixture.command("full-auto-unknown"));assertFalse(actual.settled());
            fixture.writer.locked(same->{
                String head=same.head().digest();int writes=fixture.nativeActionWrites(),reads=fixture.nativeReadWrites();
                var known=known(fixture,same);var payload=McpAutoTurnEncoder.encode(report(actual),known,fixture.archive.withSession(same),List.of());
                assertEquals(McpAutoTurnEncoder.Status.PENDING,payload.status());
                assertArrayEquals(payload.original().bytes(),McpAutoTurnEncoder.parse(payload.original()).original().bytes());
                var result=PublicMcpDirectory.CallResult.fromBusinessJson(payload.original());
                var envelope=McpJson.object(McpJson.parse(result.bytes()));assertFalse(envelope.path("isError").booleanValue());
                byte[] structured=McpJson.token(result.bytes(),"structuredContent");
                var business=DriverJson.object(structured,RawJson.MAXIMUM_BYTES);
                assertEquals(new OpportunityJson.Text("pending"),business.get("status"));
                assertEquals(new OpportunityJson.Bool(false),business.get("public_result_available"));
                var unavailable=OpportunityJson.object(business.get("result"),"actual unavailable result");
                assertEquals(new OpportunityJson.Bool(true),unavailable.get("never_replay"));
                assertFalse(unavailable.members().containsKey("accepted"));
                String text=envelope.get("content").get(0).get("text").textValue();
                assertEquals(business,DriverJson.object(text.getBytes(StandardCharsets.UTF_8),RawJson.MAXIMUM_BYTES));
                assertArrayEquals(result.bytes(),new PublicMcpDirectory.CallResult(result.bytes()).bytes());
                assertTrue(known.actionRows().isEmpty(),"UNKNOWN cannot obtain fabricated canonical or legacy coverage");
                assertEquals(0,report(actual).execution().committedSavedDays());
                assertEquals(head,same.head().digest());assertEquals(writes,fixture.nativeActionWrites());assertEquals(reads,fixture.nativeReadWrites());
                sdk(result);
                return null;
            });
        }
    }
    /** Executes the real pinned SDK model in the independently selected canonical Python, never a replacement parser. */
    private static void sdk(PublicMcpDirectory.CallResult result)throws IOException {
        String python=System.getProperty("xar.python");assertNotNull(python,"canonical Python is mandatory");assertFalse(python.isBlank());
        String repository=System.getProperty("xar.repository.root");assertNotNull(repository,"canonical repository is mandatory");assertFalse(repository.isBlank());
        String code="import sys,json,importlib.metadata as m\nassert m.version('mcp')=='2.0.0'\nfrom mcp.types import CallToolResult\n"
                +"raw=sys.stdin.buffer.read(); original=json.loads(raw); actual=CallToolResult.model_validate_json(raw)\n"
                +"encoded=actual.model_dump(mode='json',by_alias=True,exclude_none=True)\n"
                +"assert encoded['structuredContent']==original['structuredContent']\n"
                +"assert encoded['isError']==original['isError']\n"
                +"assert json.loads(actual.content[0].text)==actual.structuredContent\n"
                +"assert actual.structuredContent['status'] in ('blocked','pending')\n"
                +"assert actual.structuredContent['public_result_available'] is False\n"
                +"assert actual.structuredContent['result']['never_replay'] is True\n"
                +"sys.stdout.write('actual-mcp-2.0.0-consumer-ok')\n";
        try {
            var process=new ProcessBuilder(python,"-B","-c",code).directory(Path.of(repository).toFile()).redirectErrorStream(true).start();
            try(var input=process.getOutputStream()){input.write(result.bytes());}
            if(!process.waitFor(30,java.util.concurrent.TimeUnit.SECONDS)){process.destroyForcibly();throw new AssertionError("actual SDK consumer timed out");}
            String output=new String(process.getInputStream().readAllBytes(),StandardCharsets.UTF_8);
            assertEquals(0,process.exitValue(),output);assertEquals("actual-mcp-2.0.0-consumer-ok",output);
        }catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("actual SDK consumer interrupted",interrupted);}
    }
    private static SessionController.TurnReport report(ActionReceipt actual) {
        var before=actual.command().before();var plan=new PlanTrace(before,List.of(),Optional.empty());
        Instant now=Instant.now();var tick=new SessionClock.Tick(1,now);
        var turn=new BatchReport.Turn(1,before,plan,actual,new TurnFacts(false,false,List.of()));
        var identity=new SessionIdentity(before.machineId(),before.game(),actual.command().sessionId());
        return new SessionController.TurnReport(new BatchReport(identity,"auto-flow-data",actual.settled()?BatchReport.Terminal.ACTION_REJECTED:BatchReport.Terminal.ACTION_UNKNOWN,
                "actual coordinator outcome, typed report DATA only",tick,tick,List.of(),List.of(turn),List.of(),List.of(),List.of(),List.of(),Optional.of(plan),Optional.empty(),
                Optional.empty(),Optional.empty(),Optional.empty(),0,0,false,List.of(),List.of(),List.of()));
    }
    private ActionWriterIntegrationFixture fixture(boolean loseAck)throws Exception {
        var held=new AtomicReference<ActionWriterIntegrationFixture>();
        var scenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(OP,"game.command."+OP.value(),(command,attempt,dispatch)->{
            var actual=held.get();var ack=assertInstanceOf(NativeActionPort.AckReceived.class,dispatch);
            return new ActionPorts.RejectionObserved(new ActionState.Rejected(attempt.requestId(),"actual whole AUTO controlled rejection",actual.archive.referenceOf(ack)));
        },()->{},()->new RawJson(DriverJson.encode(new OpportunityJson.Obj(Map.of("accepted",new OpportunityJson.Bool(false))))));
        var fixture=new ActionWriterIntegrationFixture(directory.resolve(loseAck?"unknown":"canonical"),loseAck,scenario);held.set(fixture);return fixture;
    }
    private static DriverSnapshotFacts.Known known(ActionWriterIntegrationFixture actual,Session same)throws IOException {
        return actual.driverAuthority().withFrozenFacts(same,frozen->assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state()));
    }
    private static final class Materials implements DriverActionHistoryPublisher.MaterialSource {
        private final ActionWriterIntegrationFixture actual;Materials(ActionWriterIntegrationFixture actual){this.actual=actual;}
        public List<ExactRef> sources(){return List.of(actual.observationSource().sourceRef());}
        public void requireOwner(DriverStateAssembler authority,ActionJournal journal,ActionPorts.OutcomeArchive archive){
            assertSame(actual.driverAuthority(),authority);assertSame(actual.journal,journal);assertSame(actual.archive,archive);
        }
        public DriverActionHistoryCodec.OriginalMaterial capture(Session same,ActionReceipt receipt,ActionPorts.OutcomeArchive archive)throws IOException {
            var attempt=ActionTransitions.attempt(receipt.state()).orElseThrow();var dispatch=ActionTransitions.dispatch(receipt.state()).orElseThrow();
            var material=new DriverActionHistoryCodec.CanonicalOnly(DriverActionHistoryCodec.CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER,
                    List.of(new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.NATIVE_FRAME,attempt.guard().nativeEvidence()),
                            new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.MATERIAL,actual.archive.referenceOf(dispatch))),sources());
            requireOriginal(same,receipt,material,archive);return material;
        }
        public void requireOriginal(Session same,ActionReceipt receipt,DriverActionHistoryCodec.OriginalMaterial material,ActionPorts.OutcomeArchive archive)throws IOException {
            actual.writer.requireSession(same);requireRejected(receipt,archive);
            assertEquals(sources(),material.producers());
            var canonical=assertInstanceOf(DriverActionHistoryCodec.CanonicalOnly.class,material);
            assertEquals(DriverActionHistoryCodec.CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER,canonical.reason());
        }
        private void requireRejected(ActionReceipt receipt,ActionPorts.OutcomeArchive archive) {
            assertEquals(OP,receipt.command().operation());
            var settled=assertInstanceOf(ActionState.Settled.class,receipt.state());var rejected=assertInstanceOf(ActionState.Rejected.class,settled.settlement());
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,settled.dispatch());assertEquals(ack,archive.load(rejected.originalEvidence()));
            assertEquals(ack.requestId(),rejected.requestId());
        }
    }
}
