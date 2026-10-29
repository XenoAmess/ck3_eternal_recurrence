package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.Files;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.prisoners.PrisonerOrdinaryPolicy12004;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.service.mcp.PublicPlanningRpcAssertions;
import org.xar.ck3.control.service.mcp.PublicSourceFailureRpcAssertions;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** Actual transport/coordinator/archive failure, plus DATA-only original error projection cases. No CK3 authority. */
final class PrisonerPublicFailure12004Test {
    @TempDir Path temporary;
    private static final ExactRef SOURCE = new ExactRef("software-prisoner-original-error-source", 1, "1".repeat(64));
    private static final Instant READ_DEADLINE = Instant.parse("2026-10-25T01:00:00Z");
    private static final OperationKey READ = new OperationKey("query-player-prisoner-collection-private-v1");

    @Test void actualAfterWriteIoBecomesCanonicalUnknownAndPublicDiagnosticNeverSaysTimeoutOrResends() throws Exception {
        for (OperationKey operation : List.of(PrisonerOrdinaryPolicy12004.RANSOM, PrisonerOrdinaryPolicy12004.RELEASE)) {
            var nativeDispatches = new AtomicInteger();
            var producedPublic = new AtomicReference<PrisonerPublicFailure12004>();
            var scenario = new ActionWriterIntegrationFixture.SoftwareActionScenario(operation, "controlled-prisoner-public-failure",
                    (command, attempt, dispatch) -> new ActionPorts.Pending("actual missing ACK remains UNKNOWN; no material credit",
                            List.of(attempt.guard().nativeEvidence())),
                    () -> { nativeDispatches.incrementAndGet(); throw new IOException("actual controlled after-write IO; ACK unavailable"); });
            try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve(operation.value()), false, scenario)) {
                ActionCommand command = fixture.command("original-public-prisoner-io");
                ActionReceipt receipt = fixture.coordinator.execute(command);
                var unknown = assertInstanceOf(ActionState.Unknown.class, receipt.state());
                assertFalse(receipt.visibleGameplay()); assertFalse(receipt.eligibleAdvance());
                var original = assertInstanceOf(NativeActionPort.Unknown.class, unknown.dispatch().orElseThrow());
                assertEquals(NativeActionPort.FailureKind.IO_FAILURE, original.failureCause().orElseThrow().kind());
                assertEquals("IOException: actual controlled after-write IO; ACK unavailable", original.reason());
                assertTrue(original.originalRequestPacket().length > 4); assertEquals(1, nativeDispatches.get());
                fixture.writer.locked(same -> {
                    var archive = fixture.archive.withSession(same);
                    var failure = PrisonerPublicFailure12004.canonical(receipt, archive).orElseThrow();
                    producedPublic.set(failure);
                    assertEquals(PrisonerPublicFailure12004.Kind.UNKNOWN, failure.kind());
                    assertEquals(original.reason(), failure.getMessage()); assertFalse(failure.getMessage().contains("timeout"));
                    assertEquals(Optional.of(original), failure.originalOutcome()); assertEquals(Optional.of(receipt), failure.canonicalReceipt());
                    assertEquals(Optional.of(original.requestId()), failure.requestId()); assertEquals(2, failure.originalReferences().size());
                    assertEquals(receipt, archive.loadReceipt(failure.originalReferences().getFirst()));
                    assertEquals(original, archive.load(failure.originalReferences().getLast()));
                    assertFalse(failure.publishesNativeAttributes());
                    long before = same.head().state().sequence();
                    assertEquals(receipt, fixture.coordinator.execute(same, command));
                    assertEquals(before, same.head().state().sequence());
                    assertEquals(1, nativeDispatches.get()); assertEquals(1, fixture.nativeActionWrites());
                    return null;
                });
                assertEquals(receipt, fixture.reopenAndReturnExisting(command)); assertEquals(1, nativeDispatches.get());
                assertPublicConsumers(producedPublic.get());
                assertEquals(1, nativeDispatches.get()); assertEquals(1, fixture.nativeActionWrites());
            }
        }
    }

    @Test void readUnavailableAndUnclassifiedUnknownPreserveTheirActualReasonAndOriginalCause() {
        var unknown = new NativeActionPort.Unknown("original-read", "cancellation after entering write; original timeout word is diagnostic only", new byte[] {1}, Optional.empty());
        var unavailable = new PlanningReadResult.Unavailable<RawJson>("coordinator diagnostic wrapper", Optional.of(unknown));
        var failure = readFailure(unavailable);
        assertEquals(unknown.reason(), failure.getMessage()); assertEquals(PrisonerPublicFailure12004.Kind.UNKNOWN, failure.kind());
        assertEquals(Optional.of(unavailable), failure.originalRead()); assertEquals(Optional.of(unknown), failure.originalOutcome());
        var plain = new PlanningReadResult.Unavailable<RawJson>("actual option source unavailable", Optional.empty());
        assertEquals(plain.reason(), readFailure(plain).getMessage());
        var cause = new IOException("original local IO failure");
        var local = PrisonerPublicFailure12004.local(PrisonerPublicFailure12004.Operation.RELEASE, cause, List.of(SOURCE));
        assertSame(cause, local.getCause()); assertEquals(cause.getMessage(), local.getMessage());
        assertEquals(List.of(SOURCE), local.originalReferences()); assertFalse(local.publishesNativeAttributes());
    }

    @Test void operationSpecificNativeRedUsesOriginalErrorValueAndReleaseAlonePublishesItsAttributes() throws Exception {
        var ack = rejected("\"source rejected 'offer'\"");
        for (var operation : PrisonerPublicFailure12004.Operation.values()) {
            var failure = PrisonerPublicFailure12004.nativeRed(operation, ack, Optional.empty(), Optional.empty(), List.of(SOURCE));
            assertEquals(PrisonerPublicFailure12004.Kind.NATIVE_RED, failure.kind());
            String expected = switch (operation) {
                case COLLECTION -> "private prisoner collection native RED: source rejected 'offer'";
                case RANSOM -> "private ransom native RED: \"source rejected 'offer'\"";
                case RELEASE -> "private release native RED: \"source rejected 'offer'\"";
            };
            assertEquals(expected, failure.getMessage()); assertEquals(Optional.of(ack), failure.originalOutcome());
            assertEquals(operation == PrisonerPublicFailure12004.Operation.RELEASE, failure.publishesNativeAttributes());
            assertEquals(Optional.of("original-prisoner-error"), failure.requestId());
            assertEquals("source rejected 'offer'", error(failure).textValue());
            assertEquals("BridgeUnavailableError", failure.pythonClassName());
            assertPublicConsumers(failure);
        }
        var collection = readFailure(new PlanningReadResult.Unavailable<RawJson>("generic read RED", Optional.of(ack)));
        assertEquals("private prisoner collection native RED: source rejected 'offer'", collection.getMessage());
        assertTrue(collection.originalRead().isPresent());
    }

    @Test void nativeErrorMissingNullAndWrongPayloadStayDistinctAndDoNotInventRequestFields() throws Exception {
        for (String value : new String[] {null, "null", "false", "\"\"", "{\"reason\":[false,null,7]}"}) {
            var ack = rejected(value);
            var release = PrisonerPublicFailure12004.nativeRed(PrisonerPublicFailure12004.Operation.RELEASE, ack, Optional.empty(), Optional.empty(), List.of(SOURCE));
            assertTrue(release.publishesNativeAttributes());
            if (value == null) assertEquals(NativeWire.Presence.ABSENT, release.nativeError().presence());
            else if (value.equals("null")) assertEquals(NativeWire.Presence.NULL, release.nativeError().presence());
            else assertEquals(StrictJson.parse(value.getBytes(StandardCharsets.UTF_8)), error(release));
            var collection = readFailure(new PlanningReadResult.Unavailable<RawJson>("native RED", Optional.of(ack)));
            assertEquals("private prisoner collection native RED: unknown native error", collection.getMessage());
            if (value == null || value.equals("null")) assertEquals("private release native RED: None", release.getMessage());
            if ("false".equals(value)) assertEquals("private release native RED: False", release.getMessage());
            if (value != null && value.startsWith("{")) assertEquals("private release native RED: {'reason': [False, None, 7]}", release.getMessage());
            assertPublicConsumers(release);
        }
        var good = rejected("\"source RED\"");
        var changed = new NativeActionPort.AckReceived("wrong-request", false, good.originalResultToken(), good.originalFrame(), good.originalPacket());
        var malformed = PrisonerPublicFailure12004.nativeRed(PrisonerPublicFailure12004.Operation.RELEASE, changed, Optional.empty(), Optional.empty(), List.of(SOURCE));
        assertEquals(PrisonerPublicFailure12004.Kind.MALFORMED_ACK, malformed.kind());
        assertEquals("private release command result is malformed", malformed.getMessage());
        assertFalse(malformed.publishesNativeAttributes()); assertNotNull(malformed.getCause());
    }

    @Test void onlyTypedResponseDeadlineBoundToOriginalRequestAndDeadlineCanSelectTimeout() throws Exception {
        var exception = new NativeActionPort.OriginalException("java.io.IOException", "actual expiry diagnostic");
        var observed = new NativeActionPort.DeadlineObservation(READ_DEADLINE, READ_DEADLINE.plusNanos(1), false);
        var expired = new NativeActionPort.FailureCause(NativeActionPort.FailureKind.DEADLINE_EXPIRED,
                NativeActionPort.FailureStage.RESPONSE_WAIT, Optional.of(exception), Optional.empty(), Optional.of(observed));
        assertEquals(expired, NativeFailureCauseCodec.decodeValue(NativeFailureCauseCodec.encodeValue(expired)));
        byte[] request = NativeWire.packet(("{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"actual-expiry\",\"step\":\""
                + READ.value() + "\",\"expected_revision\":90}").getBytes(StandardCharsets.UTF_8));
        var original = new NativeActionPort.Unknown("actual-expiry", "actual original response deadline diagnostic", request, Optional.empty(), Optional.of(expired));
        var unavailable = new PlanningReadResult.Unavailable<RawJson>("read unavailable", Optional.of(original));
        var timeout = readFailure(unavailable);
        assertEquals(PrisonerPublicFailure12004.Kind.RESPONSE_TIMEOUT, timeout.kind());
        assertEquals("private prisoner collection command_result timed out", timeout.getMessage());
        assertEquals(Optional.of(original), timeout.originalOutcome()); assertFalse(timeout.publishesNativeAttributes());
        assertPublicConsumers(timeout);
        for (var cause : List.of(
                new NativeActionPort.FailureCause(NativeActionPort.FailureKind.DEADLINE_EXPIRED, NativeActionPort.FailureStage.WRITE,
                        Optional.of(exception), Optional.empty(), Optional.of(observed)),
                new NativeActionPort.FailureCause(NativeActionPort.FailureKind.IO_FAILURE, NativeActionPort.FailureStage.RESPONSE_WAIT,
                        Optional.of(exception), Optional.empty(), Optional.empty()),
                new NativeActionPort.FailureCause(NativeActionPort.FailureKind.INTERRUPTED, NativeActionPort.FailureStage.RESPONSE_WAIT,
                        Optional.of(exception), Optional.empty(), Optional.empty()),
                new NativeActionPort.FailureCause(NativeActionPort.FailureKind.FRAME_BUDGET_EXHAUSTED, NativeActionPort.FailureStage.RESPONSE_WAIT,
                        Optional.empty(), Optional.empty(), Optional.empty()))) {
            var unknown = new NativeActionPort.Unknown("actual-expiry", "original timeout word is not a timeout classification", request, Optional.empty(), Optional.of(cause));
            var result = readFailure(new PlanningReadResult.Unavailable<RawJson>("wrapped reason", Optional.of(unknown)));
            assertEquals(PrisonerPublicFailure12004.Kind.UNKNOWN, result.kind()); assertEquals(unknown.reason(), result.getMessage());
        }
        assertEquals(PrisonerPublicFailure12004.Kind.UNKNOWN, PrisonerPublicFailure12004.read(unavailable, SOURCE, READ,
                READ_DEADLINE.plusNanos(1)).kind());
        var wrongId = new NativeActionPort.Unknown("different-original-request", original.reason(), request, Optional.empty(), Optional.of(expired));
        assertEquals(PrisonerPublicFailure12004.Kind.UNKNOWN, readFailure(new PlanningReadResult.Unavailable<RawJson>("read unavailable", Optional.of(wrongId))).kind());
    }

    @Test void originalPythonNativeRedBranchesMatchMessagesAndOnlyAuthoredExceptionAttributes() throws Exception {
        Path repository = Path.of(required("xar.repository.root"));
        Path source = repository.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge");
        var originals = java.util.Map.of(
                "player_prisoner_collection_private_transport.py", "27d52c5e493ef6cfd14e1a915041bfd0bf978939408b6c8defa612174280ffe6",
                "player_prisoner_ransom_private_action.py", "952ddf07dfea470d7b4c1409d38919344e852b9e6168e4036e649b344c2bbe59",
                "prisoner_release_action_private_12004.py", "e2f478d39d5bdc1d008364b3612028e07b0b6489102ec4e494fa60b286f3f221");
        for (var original : originals.entrySet()) assertEquals(original.getValue(), DriverJson.sha256(Files.readAllBytes(source.resolve(original.getKey()))));
        // Execute the actual frozen source branch. This DATA oracle grants no driver/precondition/Game authority.
        String script = """
                import ast,json,pathlib,sys
                sys.dont_write_bytecode=True
                class BridgeUnavailableError(Exception): pass
                base=pathlib.Path(sys.argv[1]);rows=[]
                files={'COLLECTION':'player_prisoner_collection_private_transport.py','RANSOM':'player_prisoner_ransom_private_action.py','RELEASE':'prisoner_release_action_private_12004.py'}
                samples=[None,False,'',"source rejected 'offer'",'backslash\\\\and\\nline',{'reason':[False,None,7]},0.0001,1e20,['x',True]]
                for operation,name in files.items():
                    tree=ast.parse((base/name).read_text(encoding='utf-8'))
                    branches=[n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=="frame.get('ok') is not True"]
                    if len(branches)!=1: raise RuntimeError('nonunique original native-RED source branch')
                    code=compile(ast.fix_missing_locations(ast.Module(body=branches[0].body,type_ignores=[])),str(base/name),'exec')
                    for present,value in [(False,None)]+[(True,v) for v in samples]:
                        frame={'error':value} if present else {}
                        try: exec(code,{'frame':frame,'request_id':'original-prisoner-error','BridgeUnavailableError':BridgeUnavailableError})
                        except BridgeUnavailableError as error:
                            rows.append(dict(operation=operation,error_present=present,error_value=value,message=str(error),native_attributes=hasattr(error,'native_error'),native_error=getattr(error,'native_error',None),request_id=getattr(error,'request_id',None)))
                        else: raise RuntimeError('original source branch did not reject')
                print(json.dumps(rows,ensure_ascii=False,separators=(',',':')))
                """;
        var builder = new ProcessBuilder(required("xar.native.producer.python"), "-I", "-B", "-c", script, source.toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        var child = builder.start();
        try {
            assertTrue(child.waitFor(30, TimeUnit.SECONDS), "original Python native-error oracle timed out");
            byte[] output = child.getInputStream().readAllBytes(), errors = child.getErrorStream().readAllBytes();
            assertEquals(0, child.exitValue(), new String(errors, StandardCharsets.UTF_8));
            assertTrue(output.length <= 65_536, "bounded original Python error corpus required");
            for (JsonNode row : StrictJson.parse(output, 65_536)) {
                String value = row.get("error_present").booleanValue() ? row.get("error_value").toString() : null;
                var actual = PrisonerPublicFailure12004.nativeRed(PrisonerPublicFailure12004.Operation.valueOf(row.get("operation").textValue()),
                        rejected(value), Optional.empty(), Optional.empty(), List.of(SOURCE));
                assertEquals(row.get("message").textValue(), actual.getMessage(), row.toString());
                assertEquals(row.get("native_attributes").booleanValue(), actual.publishesNativeAttributes());
                if (actual.publishesNativeAttributes()) {
                    JsonNode nativeError = actual.nativeError().presence() == NativeWire.Presence.VALUE ? error(actual) : StrictJson.parse("null".getBytes(StandardCharsets.UTF_8));
                    assertEquals(row.get("native_error"), nativeError); assertEquals(row.get("request_id").textValue(), actual.requestId().orElseThrow());
                }
            }
        } finally { if (child.isAlive()) child.destroyForcibly(); }
    }
    private static String required(String name) {
        String value = System.getProperty(name);
        assertTrue(value != null && !value.isBlank(), "NOT_RUN: missing required original producer property " + name);
        return value;
    }
    private static PrisonerPublicFailure12004 readFailure(PlanningReadResult.Unavailable<RawJson> original) {
        return PrisonerPublicFailure12004.read(original, SOURCE, READ, READ_DEADLINE);
    }
    private static void assertPublicConsumers(PrisonerPublicFailure12004 original) throws Exception {
        String name = switch (original.operation()) {
            case COLLECTION -> RootPrisonerPublicProducts.QUERY;
            case RANSOM -> RootPrisonerPublicProducts.RANSOM;
            case RELEASE -> RootPrisonerPublicProducts.RELEASE;
        };
        String arguments = original.operation() == PrisonerPublicFailure12004.Operation.COLLECTION
                ? "{\"expected_revision\":56}" : "{\"collection\":{},\"prisoner_character_id\":303}";
        for (var consumer : PublicPlanningRpcAssertions.Consumer.values()) {
            var wrapper = PublicSourceFailureRpcAssertions.assertOriginal(consumer, name, arguments, original,
                    Optional.of(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE));
            if (wrapper.isPresent()) {
                var mapped = wrapper.orElseThrow();
                assertSame(original, mapped.getCause()); assertSame(original, mapped.originalFailure().orElseThrow());
                var retained = (PrisonerPublicFailure12004) mapped.originalFailure().orElseThrow();
                assertSame(original.originalOutcome(), retained.originalOutcome());
                assertSame(original.canonicalReceipt(), retained.canonicalReceipt());
                assertSame(original.originalReferences(), retained.originalReferences());
                assertEquals(original.publishesNativeAttributes(), mapped.nativeAttributes().isPresent());
                if (original.publishesNativeAttributes()) {
                    var attributes = mapped.nativeAttributes().orElseThrow();
                    JsonNode nativeError = original.nativeError().presence() == NativeWire.Presence.VALUE ? error(original)
                            : StrictJson.parse("null".getBytes(StandardCharsets.UTF_8));
                    assertEquals(nativeError, StrictJson.parse(attributes.nativeError().bytes(), RawJson.MAXIMUM_BYTES));
                    assertEquals(original.requestId().orElseThrow(), attributes.requestId());
                }
            }
        }
    }
    private static JsonNode error(PrisonerPublicFailure12004 failure) {
        return StrictJson.parse(failure.nativeError().token().orElseThrow().value(), RawJson.MAXIMUM_BYTES);
    }
    private static NativeActionPort.AckReceived rejected(String error) throws IOException {
        String body = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"original-prisoner-error\",\"ok\":false"
                + (error == null ? "" : ",\"error\":" + error) + "}";
        byte[] raw = body.getBytes(StandardCharsets.UTF_8);
        return new NativeActionPort.AckReceived("original-prisoner-error", false, Optional.empty(), new RawJson(raw), NativeWire.packet(raw));
    }
}
