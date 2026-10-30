package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.time.Duration;
import java.time.Clock;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Base64;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.NativeStepDiscriminator;
import org.xar.ck3.control.application.action.NativeStepDiscriminator.RiteCreation;
import org.xar.ck3.control.application.action.ExecutableStepBindings.Kind;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadGuard;
import org.xar.ck3.control.application.action.NativeSelectorReadFixture;
import org.xar.ck3.control.application.ritecreation.RiteCreationContract;
import org.xar.ck3.control.application.ritecreation.RiteCreationCodec;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.application.action.NativeRequestChronologyCodec;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.NativeTransportSubmissionFixture;
import org.xar.ck3.control.application.action.council.NativeTransportCouncilFixture;
import org.xar.ck3.control.application.action.council.CouncilContinuationModel.Stage;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Uses the original pinned NativeNamedPipeServer.send encoder, never a hand-written expected packet. */
final class NativeOriginalProducerTest {
    @TempDir Path temporary;
    private int sequence;
    private static final String ORIGINAL_SEND_FIXTURE = """
            import ast,base64,hashlib,json,struct,sys,threading,types
            from pathlib import Path
            source=Path(sys.argv[1]).read_bytes()
            if hashlib.sha256(source).hexdigest()!=sys.argv[2]: raise RuntimeError('original Native producer source drift')
            tree=ast.parse(source.decode('utf-8-sig'))
            cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='NativeNamedPipeServer')
            send=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='send')
            captured=[]
            def capture(handle,packet):
                captured.append(packet)
                return True
            scope={'json':json,'struct':struct,'MAXIMUM_FRAME_BYTES':64*1024*1024,'_write_all':capture,'BridgeUnavailableError':RuntimeError}
            future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
            module=ast.fix_missing_locations(ast.Module(body=[future,send],type_ignores=[]))
            exec(compile(module,str(Path(sys.argv[1])),'exec'),scope)
            frame=json.loads(base64.b64decode(sys.argv[3]))
            if sys.argv[4]=='large': frame['state']['large_native_field']='x'*(1048576+17)
            owner=types.SimpleNamespace(_write_lock=threading.Lock(),_current_handle=lambda:1)
            scope['send'](owner,frame)
            if len(captured)!=1: raise RuntimeError('original producer did not make exactly one packet attempt')
            sys.stdout.buffer.write(base64.b64encode(captured[0]))
            """;

    @Test void originalRequestProducerMatchesJavaPacketAndPreservesUint64() throws Exception {
        String request = "{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"step-original-fixture\",\"step\":\"pause-map\",\"expected_revision\":18446744073709551615}";
        byte[] actualPython = producer(request, false);
        byte[] actualJava = NativeWire.execute("step-original-fixture", "pause-map", NativeWire.UINT64_MAX, "{}".getBytes(StandardCharsets.UTF_8));
        assertArrayEquals(actualPython, actualJava);
        assertThrows(IOException.class, () -> NativeWire.execute("fixture", "pause-map", NativeWire.UINT64_MAX.add(BigInteger.ONE), "{}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IOException.class, () -> NativeWire.execute("fixture", "pause-map", BigInteger.ONE, "{\"expected_revision\":2}".getBytes(StandardCharsets.UTF_8)));
    }

    @Test void councilStatusMatchesOriginalFourFieldProducerAndRejectsEnvelopeAdditions() throws Exception {
        String step = "private-council-application-main-status-v1";
        String request = "{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"council-status-fixture\",\"step\":\"" + step + "\"}";
        assertArrayEquals(producer(request, false), NativeWire.executeCouncilMailboxStatus("council-status-fixture", step,
                "{}".getBytes(StandardCharsets.UTF_8)));
        var status = NativeWire.decodeExecuteRequest(producer(request, false));
        assertTrue(status.expectedRevision().isEmpty()); assertTrue(status.expectedSnapshotRevision().isEmpty());
        for (String forbidden : List.of("{\"expected_revision\":7}", "{\"expected_snapshot_revision\":7}",
                "{\"ticket\":1}", "{\"unused\":null}", "[]", "null"))
            assertThrows(IOException.class, () -> NativeWire.executeCouncilMailboxStatus("fixture", step,
                    forbidden.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IOException.class, () -> NativeWire.executeCouncilMailboxStatus("fixture", "pause-map",
                "{}".getBytes(StandardCharsets.UTF_8)));
    }

    @Test void outgoingDecoderRetainsOriginalBytesAndRejectsWrongRevisionProfiles() throws Exception {
        byte[] actual = producer("{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"actual-outbound\",\"step\":\"read-fixture\",\"expected_revision\":18446744073709551615,\"flag\":true}", false);
        var decoded = NativeWire.decodeExecuteRequest(actual);
        assertArrayEquals(actual, decoded.originalPacket().value());
        assertEquals(NativeWire.UINT64_MAX, decoded.expectedRevision().orElseThrow());
        assertTrue(decoded.expectedSnapshotRevision().isEmpty());
        assertTrue(NativeWire.parse(decoded.normalizedAdditionalFields().value()).get("flag").booleanValue());
        for (String revision : List.of("true", "1.0", "\"1\"", "null", "-1"))
            assertThrows(IOException.class, () -> NativeWire.decodeExecuteRequest(producer("{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"fixture\",\"step\":\"read-fixture\",\"expected_revision\":" + revision + "}", false)));
        assertThrows(IOException.class, () -> NativeWire.decodeExecuteRequest(producer("{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"fixture\",\"step\":\"read-fixture\",\"expected_revision\":1,\"expected_snapshot_revision\":2}", false)));
    }

    @Test void immutablePipeNameAndLatestSnapshotDoNotCreateAQueryOrConsumeDelivery() throws Exception {
        Replay port = new Replay(producer(hello(), false), producer(snapshot("7"), false));
        NativeGameTransport transport = new NativeGameTransport(port, config(), 16, 16);
        try (transport) {
            assertEquals(config().pipeName(), transport.pipeName());
            assertTrue(transport.latestObservedSnapshot().isEmpty());
            assertThrows(IOException.class, () -> transport.verifyHeld(Instant.now().plusSeconds(5)));
            var received = transport.observe(Instant.now().plusSeconds(5));
            int priorVerifications = port.verifications;
            var retained = transport.latestObservedSnapshot().orElseThrow();
            assertEquals(priorVerifications, port.verifications);
            assertEquals(received.observedAt(), retained.observedAt());
            assertEquals(received.session(), retained.session());
            assertArrayEquals(received.originalPacket(), retained.originalPacket());
            transport.verifyHeld(Instant.now().plusSeconds(5));
            assertEquals(priorVerifications + 1, port.verifications);
            assertEquals(0, port.writes);
        }
        assertThrows(IOException.class, transport::latestObservedSnapshot);
        transport.close();
    }

    @Test void incompleteMailboxRetainsUnknownCustodyAndBlocksEveryNewProducer() throws Exception {
        Replay port = new Replay(producer(frontendHello(true), false));
        port.onWrite = packet -> {
            var request = NativeWire.parse(Arrays.copyOfRange(packet, 4, packet.length));
            port.packets.addLast(producer("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""
                    + NativeWire.text(request.get("request_id")) + "\",\"ok\":true,\"result\":{\"private_council_transport\":true,\"advertised\":false,\"status\":\"pending\"}}", false));
        };
        try (NativeGameTransport transport = new NativeGameTransport(port, frontendConfig(), 16, 16)) {
            assertThrows(IOException.class, () -> transport.withMailbox(Instant.now().plusSeconds(5), scope -> {
                var pending = transport.readFrontendRoute(Instant.now().plusSeconds(5));
                scope.complete(pending); return pending;
            }));
            assertTrue(transport.mailboxDiagnostics().poison().isPresent());
            assertEquals(1, transport.mailboxDiagnostics().unresolvedRequestIds().size());
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,
                    transport.readFrontendRoute(Instant.now().plusSeconds(5)));
            assertEquals(1, port.writes);
            assertThrows(IOException.class, () -> transport.withMailbox(Instant.now().plusSeconds(5), scope -> "no replay"));
        }
    }

    @Test void mailboxCompletionRequiresTheSameActualAckAndClosesItsDispatchWindow() throws Exception {
        Replay port = new Replay(producer(frontendHello(true), false));
        port.onWrite = packet -> {
            var request = NativeWire.parse(Arrays.copyOfRange(packet, 4, packet.length));
            port.packets.addLast(producer("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""
                    + NativeWire.text(request.get("request_id")) + "\",\"ok\":true,\"result\":{\"step\":\"query-frontend-gui-route-v1\",\"accepted\":true,\"status\":\"main_menu\"}}", false));
        };
        try (NativeGameTransport transport = new NativeGameTransport(port, frontendConfig(), 16, 16)) {
            transport.withMailbox(Instant.now().plusSeconds(5), scope -> {
                var actual = assertInstanceOf(NativeActionPort.AckReceived.class,
                        transport.readFrontendRoute(Instant.now().plusSeconds(5)));
                var reconstructed = new NativeActionPort.AckReceived(actual.requestId(), actual.nativeOk(),
                        actual.originalResultToken(), actual.originalFrame(), actual.originalPacket());
                assertThrows(IOException.class, () -> scope.complete(reconstructed));
                assertThrows(IOException.class, () -> transport.withMailbox(Instant.now().plusSeconds(5), nested -> "nested"));
                scope.complete(actual);
                assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,
                        transport.readFrontendRoute(Instant.now().plusSeconds(5)));
                return actual;
            });
            assertTrue(transport.mailboxDiagnostics().poison().isEmpty());
            assertEquals(1, port.writes);
            assertInstanceOf(NativeActionPort.AckReceived.class, transport.readFrontendRoute(Instant.now().plusSeconds(5)));
            assertEquals(2, port.writes);
        }
    }

    @Test void originalProducerFlowsThroughWireSharedRawAndObservationConsumerAboveOneMiB() throws Exception {
        byte[] hello = producer(hello(), false);
        BigInteger opaque = new BigInteger("184467440737095516160000001");
        byte[] state = producer(snapshot(opaque.toString()), true);
        NativeWire.Snapshot decoded = assertInstanceOf(NativeWire.Snapshot.class, NativeWire.decode(state));
        assertEquals(opaque, decoded.revision());
        assertTrue(state.length > 1_048_576);
        RawJson raw = new RawJson(decoded.state().value());
        assertTrue(raw.objectFieldNames().containsAll(List.of("date_raw", "played_character", "large_native_field", "nullable")));
        byte[] saved = raw.bytes(); saved[0] = 0; assertEquals((byte) '{', raw.bytes()[0]);
        Replay port = new Replay(hello, state);
        try (NativeGameTransport transport = new NativeGameTransport(port, config(), 16, 16)) {
            var observation = transport.observe(Instant.now().plusSeconds(5));
            assertEquals(opaque, observation.nativeRevision());
            assertEquals(new BigInteger("18446744073709551615"), observation.session().connectionGeneration());
            assertArrayEquals(state, observation.originalPacket());
            assertArrayEquals(decoded.state().value(), observation.state().bytes());
            assertEquals(0, port.writes);
        }
    }

    @Test void rejectedNativeAckKeepsAbsentAndExplicitNullDistinct() throws Exception {
        byte[] absent = producer("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"fixture\",\"ok\":false,\"error\":\"revision mismatch\"}", false);
        byte[] explicitNull = producer("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"fixture\",\"ok\":false,\"error\":\"revision mismatch\",\"result\":null}", false);
        var missing = assertInstanceOf(NativeWire.CommandResult.class, NativeWire.decode(absent));
        var nullable = assertInstanceOf(NativeWire.CommandResult.class, NativeWire.decode(explicitNull));
        assertFalse(missing.nativeOk()); assertEquals(NativeWire.Presence.ABSENT, missing.result().presence());
        assertEquals(NativeWire.Presence.NULL, nullable.result().presence());
        assertTrue(missing.result().token().isEmpty());
        assertArrayEquals("null".getBytes(StandardCharsets.UTF_8), nullable.result().token().orElseThrow().value());
    }

    @Test void actualProducerPacketsRejectWrongTypesDuplicateKeysUtf8AndReconnection() throws Exception {
        byte[] original = producer(snapshot("7"), false);
        String payload = new String(Arrays.copyOfRange(original, 4, original.length), StandardCharsets.UTF_8);
        for (String replacement : List.of("true", "7.0", "\"7\"", "null")) {
            byte[] mutated = NativeWire.packet(payload.replace("\"revision\":7", "\"revision\":" + replacement).getBytes(StandardCharsets.UTF_8));
            assertThrows(IOException.class, () -> NativeWire.decode(mutated));
        }
        byte[] duplicate = NativeWire.packet(payload.replace("\"revision\":7", "\"revision\":7,\"revision\":7").getBytes(StandardCharsets.UTF_8));
        assertThrows(IOException.class, () -> NativeWire.decode(duplicate));
        byte[] malformed = original.clone(); malformed[malformed.length - 2] = (byte) 0xff;
        assertThrows(IOException.class, () -> NativeWire.decode(malformed));
        byte[] wrongLength = original.clone(); ByteBuffer.wrap(wrongLength).order(ByteOrder.LITTLE_ENDIAN).putInt(original.length);
        assertThrows(IOException.class, () -> NativeWire.decode(wrongLength));
        byte[] originalHello = producer(hello(), false);
        try (NativeGameTransport transport = new NativeGameTransport(new Replay(originalHello, originalHello), config(), 16, 16)) {
            transport.awaitHello(Instant.now().plusSeconds(5));
            assertThrows(java.io.UncheckedIOException.class, () -> transport.observe(Instant.now().plusSeconds(5)));
            assertArrayEquals(originalHello, transport.lastOriginalPacket());
        }
    }

    @Test void originalStandaloneCoreReadRequiresNoGameplaySnapshotAndRetainsHeartbeatBytes() throws Exception {
        String originalHello = hello().replace("\"fixture-adapter\"", "\"ck3-1.20.0.4-msvc-x64\"")
                .replace("\"expected_ck3_sha256\":\"" + "0".repeat(64) + "\"", "\"expected_ck3_sha256\":\"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518\",\"expected_ck3_version\":\"1.20.0.4\"")
                .replace("\"game.state.snapshot\"", "\"game.query.core-frame.v1\"");
        byte[] heartbeat = producer("{\"type\":\"heartbeat\",\"protocol_version\":1,\"sequence\":3,\"mailbox\":{\"pump_epochs\":7}}", false);
        Replay port = new Replay(producer(originalHello, false), heartbeat);
        port.onWrite = packet -> {
            var request = NativeWire.parse(Arrays.copyOfRange(packet, 4, packet.length));
            assertEquals("query-core-frame-v1", NativeWire.text(request.get("step")));
            assertEquals(BigInteger.ZERO, NativeWire.integer(request.get("expected_revision"), BigInteger.ZERO, BigInteger.ZERO));
            assertEquals(5, request.size());
            port.packets.addLast(producer("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""
                    + NativeWire.text(request.get("request_id")) + "\",\"ok\":true,\"result\":{}}", false));
        };
        NativePipeEndpoint.Config exact = new NativePipeEndpoint.Config(config().pipeName(), config().machineId(), config().game(), config().sessionId(),
                "fixture", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518", "ck3-1.20.0.4-msvc-x64");
        try (NativeGameTransport transport = new NativeGameTransport(port, exact, 16, 16)) {
            assertEquals(NativeGameTransport.ReceivedState.NO_HELLO, transport.diagnostics().receivedState());
            var outcome = transport.readCoreFrame(Instant.now().plusSeconds(5));
            assertInstanceOf(NativeActionPort.AckReceived.class, outcome); assertEquals(1, port.writes);
            var diagnostic = transport.diagnostics();
            assertEquals(NativeGameTransport.ReceivedState.HELLO_VERIFIED, diagnostic.receivedState());
            assertArrayEquals(heartbeat, diagnostic.latestHeartbeat().orElseThrow().original().packet().value());
            assertTrue(diagnostic.latestPong().isEmpty()); assertTrue(diagnostic.terminalFailure().isEmpty());
        }
    }

    @Test void originalFrontendBootstrapHasFixedReadStepRevisionZeroAndNoGameplaySnapshot() throws Exception {
        Replay port = new Replay(producer(frontendHello(true), false));
        port.onWrite = packet -> {
            var request = NativeWire.parse(Arrays.copyOfRange(packet, 4, packet.length));
            assertEquals("query-frontend-gui-route-v1", NativeWire.text(request.get("step")));
            assertEquals(BigInteger.ZERO, NativeWire.integer(request.get("expected_revision"), BigInteger.ZERO, BigInteger.ZERO));
            assertEquals(5, request.size());
            port.packets.addLast(producer("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""
                    + NativeWire.text(request.get("request_id")) + "\",\"ok\":true,\"result\":{\"step\":\"query-frontend-gui-route-v1\",\"accepted\":true,\"status\":\"main_menu\"}}", false));
        };
        try (NativeGameTransport transport = new NativeGameTransport(port, frontendConfig(), 16, 16)) {
            var ack = assertInstanceOf(NativeActionPort.AckReceived.class, transport.readFrontendRoute(Instant.now().plusSeconds(5)));
            assertTrue(ack.nativeOk()); assertEquals(1, port.writes);
            assertArrayEquals(port.lastWrite, ack.outbound().orElseThrow().originalPacket());
            assertEquals(ack.requestId(), ack.outbound().orElseThrow().requestId());
            var decoded = assertInstanceOf(NativeWire.CommandResult.class, NativeWire.decode(ack.originalPacket()));
            assertArrayEquals(decoded.result().token().orElseThrow().value(), ack.originalResultToken().orElseThrow().bytes());
            assertEquals("main_menu", NativeWire.text(NativeWire.parse(ack.originalResultToken().orElseThrow().bytes()).get("status")));
        }
    }
    @Test void frontendBootstrapMissingCapabilityCannotWrite() throws Exception {
        Replay port = new Replay(producer(frontendHello(false), false));
        try (NativeGameTransport transport = new NativeGameTransport(port, frontendConfig(), 16, 16)) {
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class, transport.readFrontendRoute(Instant.now().plusSeconds(5)));
            assertEquals(0, port.writes);
        }
    }
    @Test void frontendFalseAckRemainsOriginalRejectedAck() throws Exception {
        Replay port = new Replay(producer(frontendHello(true), false));
        port.onWrite = packet -> {
            var request = NativeWire.parse(Arrays.copyOfRange(packet, 4, packet.length));
            port.packets.addLast(producer("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""
                    + NativeWire.text(request.get("request_id")) + "\",\"ok\":false,\"error\":\"original frontend read rejected\"}", false));
        };
        try (NativeGameTransport transport = new NativeGameTransport(port, frontendConfig(), 16, 16)) {
            var ack = assertInstanceOf(NativeActionPort.AckReceived.class, transport.readFrontendRoute(Instant.now().plusSeconds(5)));
            assertFalse(ack.nativeOk()); assertTrue(ack.originalResultToken().isEmpty()); assertEquals(1, port.writes);
        }
    }
    @Test void frontendLostAckStaysUnknownAndLateReadResultReconcilesWithoutResending() throws Exception {
        Replay port = new Replay(producer(frontendHello(true), false));
        try (NativeGameTransport transport = new NativeGameTransport(port, frontendConfig(), 16, 16)) {
            var unknown = assertInstanceOf(NativeActionPort.Unknown.class, transport.readFrontendRoute(Instant.now().plusSeconds(5)));
            assertEquals(1, port.writes);
            var original = NativeWire.parse(Arrays.copyOfRange(unknown.originalRequestPacket(), 4, unknown.originalRequestPacket().length));
            assertEquals(unknown.requestId(), NativeWire.text(original.get("request_id")));
            port.packets.addLast(producer("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""
                    + unknown.requestId() + "\",\"ok\":true,\"result\":{\"step\":\"query-frontend-gui-route-v1\",\"accepted\":true,\"status\":\"main_menu\"}}", false));
            var retained = transport.originalOutboundPacket(unknown.requestId()).orElseThrow();
            assertArrayEquals(unknown.originalRequestPacket(), retained.originalPacket());
            byte[] detached = retained.originalPacket(); detached[0] = 0;
            assertArrayEquals(port.lastWrite, transport.originalOutboundPacket(unknown.requestId()).orElseThrow().originalPacket());
            var late = transport.collectOriginalOutcome(unknown.requestId(), Instant.now().plusSeconds(5)).orElseThrow();
            assertTrue(late.nativeOk()); assertEquals(1, port.writes);
            assertArrayEquals(port.lastWrite, late.outbound().orElseThrow().originalPacket());
            assertThrows(IOException.class, () -> transport.collectOriginalOutcome("never-sent", Instant.now().plusSeconds(5)));
            assertEquals(1, port.writes);
        }
    }
    @Test void unknownMailboxCannotIssueAnotherRequestOrBecomeUnlockedByAnUnrelatedTerminal() throws Exception {
        Replay port = new Replay(producer(frontendHello(true), false));
        try (NativeGameTransport transport = new NativeGameTransport(port, frontendConfig(), 16, 16)) {
            assertThrows(IOException.class, () -> transport.withMailbox(Instant.now().plusSeconds(5), scope -> {
                var unknown = assertInstanceOf(NativeActionPort.Unknown.class, transport.readFrontendRoute(Instant.now().plusSeconds(5)));
                assertThrows(IOException.class, () -> scope.complete(unknown));
                assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class, transport.readFrontendRoute(Instant.now().plusSeconds(5)));
                assertEquals(1, port.writes); return unknown;
            }));
            assertTrue(transport.mailboxDiagnostics().poison().isPresent());
        }
    }
    @Test void actualPrivatePendingAssignmentNeedsCanonicalStagesFreshFrameAndIndependentReceipt() throws Exception {
        Path producerSource = temporary.resolve("controlled-private-council-source.txt");
        Files.writeString(producerSource, "controlled reviewed source, no live exact-build qualification");
        ExactRef originalSource = ref(producerSource.toString(), Files.readAllBytes(producerSource));
        G2Source source = new G2Source(config().machineId(), Instant.now().toString(), "controlled-fixture", originalSource);
        String assign = "private-assign-councillor-v1", receipt = "private-query-assign-councillor-receipt-v1";
        String status = "private-council-application-main-status-v1";
        NativeRequest initial = new NativeRequest(assign, Optional.empty(), raw("{\"candidate_character_id\":73}"));
        NativePrivateActionPermission permission = new NativePrivateActionPermission(new OperationKey(assign), "controlled-private", originalSource,
                request -> { if (!request.additionalFields().objectFieldNames().equals(Set.of("candidate_character_id"))) throw new IOException("wrong controlled fields"); },
                (config, hello, actualGuard, request) -> originalSource);
        Replay port = new Replay(producer(hello(), false), producer(snapshot("7"), false));
        AtomicInteger statusCount = new AtomicInteger(), issuerChecks = new AtomicInteger();
        port.onWrite = packet -> {
            var decoded = NativeWire.decodeExecuteRequest(packet); String step = decoded.step();
            String result;
            if (step.equals(assign) || step.equals(receipt)) {
                assertEquals(step.equals(assign) ? BigInteger.valueOf(7) : BigInteger.valueOf(8), decoded.expectedRevision().orElseThrow());
                if (step.equals(receipt)) assertTrue(NativeWire.object(NativeWire.parse(decoded.normalizedAdditionalFields().value())).isEmpty());
                result = "{\"private_council_transport\":true,\"advertised\":false,\"status\":\"pending\"}";
            } else {
                assertEquals(status, step); assertTrue(decoded.expectedRevision().isEmpty());
                assertTrue(decoded.expectedSnapshotRevision().isEmpty()); assertTrue(NativeWire.object(NativeWire.parse(decoded.normalizedAdditionalFields().value())).isEmpty());
                boolean helper = statusCount.incrementAndGet() == 1;
                result = "{\"schema\":\"xar.ck3.council-application-main/v1\",\"accepted\":true,\"step\":\""
                        + (helper ? "assign-councillor-v1" : "query-assign-councillor-receipt-v1") + "\",\"query_sequence\":1,\"snapshot_revision\":8,\"backend_id\":\"native-headless\"}";
            }
            port.packets.addLast(producer("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + decoded.requestId()
                    + "\",\"ok\":true,\"result\":" + result + "}", false));
            if (step.equals(status) && statusCount.get() == 1) port.packets.addLast(producer(snapshot("8"), false));
        };
        try (NativeGameTransport transport = new NativeGameTransport(port, config(), 16, 32, List.of(permission))) {
            transport.observe(Instant.now().plusSeconds(5));
            transport.withMailbox(Instant.now().plusSeconds(10), scope -> {
                GuardEvidence before = councilGuard(transport, source, BigInteger.valueOf(7));
                var expected = new ProposalLifecycle.ExpectedPostcondition(1, before.observed(), source, "controlled-council/v1",
                        List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"), true)));
                ActionCommand command = new ActionCommand("controlled-council", before.observed(), source, config().sessionId(), before.operation(),
                        new OpportunityJson.Obj(Map.of()), expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), Instant.now().plusSeconds(10));
                NativeRequest statusRequest = new NativeRequest(status, Optional.empty(), raw("{}"));
                NativeRequest receiptRequest = new NativeRequest(receipt, Optional.empty(), raw("{}"));
                var noOriginal = NativeTransportCouncilFixture.issue(command.actionId(), "actual-assign", "missing-original", Stage.HELPER_STATUS, before, statusRequest, issuerChecks::incrementAndGet);
                assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class, transport.continueCouncil(noOriginal, statusRequest, Instant.now().plusSeconds(5)));
                assertFalse(noOriginal.consumed()); assertEquals(0, port.writes);
                var submission = NativeTransportSubmissionFixture.issue(command, before, initial, "actual-assign");
                var pending = assertInstanceOf(NativeActionPort.AckReceived.class, transport.submit(submission, initial, Instant.now().plusSeconds(5)));
                assertThrows(IOException.class, () -> scope.complete(pending));
                var early = NativeTransportCouncilFixture.issue(command.actionId(), "actual-assign", "early-receipt", Stage.RECEIPT_QUERY, before, receiptRequest, issuerChecks::incrementAndGet);
                assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class, transport.continueCouncil(early, receiptRequest, Instant.now().plusSeconds(5)));
                assertFalse(early.consumed()); assertEquals(1, port.writes);
                var staleWriter = NativeTransportCouncilFixture.issue(command.actionId(), "actual-assign", "stale-writer", Stage.HELPER_STATUS, before, statusRequest,
                        () -> { throw new IllegalStateException("controlled persisted ISSUED mismatch"); });
                assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class, transport.continueCouncil(staleWriter, statusRequest, Instant.now().plusSeconds(5)));
                assertFalse(staleWriter.consumed()); assertEquals(1, port.writes);
                var helperPermit = NativeTransportCouncilFixture.issue(command.actionId(), "actual-assign", "actual-helper-status", Stage.HELPER_STATUS, before, statusRequest, issuerChecks::incrementAndGet);
                var helper = assertInstanceOf(NativeActionPort.AckReceived.class, transport.continueCouncil(helperPermit, statusRequest, Instant.now().plusSeconds(5)));
                assertTrue(helperPermit.consumed()); assertThrows(IOException.class, () -> scope.complete(helper));
                transport.observe(Instant.now().plusSeconds(5)); GuardEvidence after = councilGuard(transport, source, BigInteger.valueOf(8));
                var receiptPermit = NativeTransportCouncilFixture.issue(command.actionId(), "actual-assign", "actual-receipt-query", Stage.RECEIPT_QUERY, after, receiptRequest, issuerChecks::incrementAndGet);
                assertInstanceOf(NativeActionPort.AckReceived.class, transport.continueCouncil(receiptPermit, receiptRequest, Instant.now().plusSeconds(5)));
                var finalPermit = NativeTransportCouncilFixture.issue(command.actionId(), "actual-assign", "actual-receipt-status", Stage.RECEIPT_STATUS, after, statusRequest, issuerChecks::incrementAndGet);
                var terminal = assertInstanceOf(NativeActionPort.AckReceived.class, transport.continueCouncil(finalPermit, statusRequest, Instant.now().plusSeconds(5)));
                assertArrayEquals(port.lastWrite, terminal.outbound().orElseThrow().originalPacket()); scope.complete(terminal);
                assertEquals(3, issuerChecks.get()); assertEquals(4, port.writes); return terminal;
            });
            assertTrue(transport.mailboxDiagnostics().poison().isEmpty());
        }
    }
    private enum CouncilRejectionVariant { CLEAN, EXECUTOR_EXCEPTION, PRIOR_ASSIGNMENT_UNRESOLVED, HELPER_INVOKED, NONZERO_PRE_FRAME,
        NONDEFAULT_OWNER, WRONG_CANDIDATE, FLOAT_OUTER_REVISION, WRONG_BOOLEAN_TOKEN }
    @Test void onlyActualNonInvokedCouncilRejectionClosesWithoutInventingAnUnavailableReceipt() throws Exception {
        for (CouncilRejectionVariant variant : CouncilRejectionVariant.values()) {
            Path producerSource = temporary.resolve("controlled-reject-" + variant + ".txt");
            Files.writeString(producerSource, "controlled original private source, no loaded-Game qualification");
            ExactRef sourceRef = ref(producerSource.toString(), Files.readAllBytes(producerSource));
            G2Source source = new G2Source(config().machineId(), Instant.now().toString(), "controlled-fixture", sourceRef);
            NativeRequest initial = new NativeRequest("private-assign-councillor-v1", Optional.empty(),
                    raw("{\"candidate_character_id\":73}"));
            NativePrivateActionPermission permission = new NativePrivateActionPermission(new OperationKey(initial.step()), "controlled-private", sourceRef,
                    request -> { if (!request.additionalFields().objectFieldNames().equals(Set.of("candidate_character_id"))) throw new IOException("wrong controlled fields"); },
                    (config, hello, guard, request) -> sourceRef);
            Replay port = new Replay(producer(hello(), false), producer(snapshot("7"), false));
            port.onWrite = packet -> {
                var request = NativeWire.decodeExecuteRequest(packet);
                String result;
                if (request.step().equals(initial.step())) {
                    result = "{\"private_council_transport\":true,\"advertised\":false,\"status\":\"pending\"}";
                } else {
                    assertEquals("private-council-application-main-status-v1", request.step());
                    assertTrue(request.expectedRevision().isEmpty()); assertTrue(request.expectedSnapshotRevision().isEmpty());
                    var outer = NativeWire.object(NativeWire.parse(councilRejectedResult().getBytes(StandardCharsets.UTF_8)));
                    var inner = NativeWire.object(outer.get("council_assign_councillor_ack"));
                    switch (variant) {
                        case CLEAN -> { }
                        case EXECUTOR_EXCEPTION -> inner.put("native_reason_key", "action_executor_exception");
                        case PRIOR_ASSIGNMENT_UNRESOLVED -> {
                            inner.put("failure", "callbacks_unavailable");
                            inner.put("native_reason_key", "pending_assignment_unresolved");
                        }
                        case HELPER_INVOKED -> inner.put("native_helper_invoked", true);
                        case NONZERO_PRE_FRAME -> inner.put("pre_date_raw", 1);
                        case NONDEFAULT_OWNER -> inner.put("owner_character_id", 73);
                        case WRONG_CANDIDATE -> inner.put("candidate_character_id", 74);
                        case FLOAT_OUTER_REVISION -> outer.put("snapshot_revision", 0.0);
                        case WRONG_BOOLEAN_TOKEN -> inner.put("had_incumbent", 0);
                    }
                    result = outer.toString();
                }
                port.packets.addLast(producer("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + request.requestId()
                        + "\",\"ok\":true,\"result\":" + result + "}", false));
            };
            try (NativeGameTransport transport = new NativeGameTransport(port, config(), 16, 32, List.of(permission))) {
                transport.observe(Instant.now().plusSeconds(5));
                NativeGameTransport.MailboxWork<NativeActionPort.AckReceived> work = scope -> {
                    GuardEvidence before = councilGuard(transport, source, BigInteger.valueOf(7));
                    var expected = new ProposalLifecycle.ExpectedPostcondition(1, before.observed(), source, "controlled-rejection/v1",
                            List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"), true)));
                    ActionCommand command = new ActionCommand("controlled-rejection", before.observed(), source, config().sessionId(), before.operation(),
                            new OpportunityJson.Obj(Map.of()), expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), Instant.now().plusSeconds(10));
                    var submitted = NativeTransportSubmissionFixture.issue(command, before, initial, "rejected-assign");
                    assertInstanceOf(NativeActionPort.AckReceived.class, transport.submit(submitted, initial, Instant.now().plusSeconds(5)));
                    NativeRequest status = new NativeRequest("private-council-application-main-status-v1", Optional.empty(), raw("{}"));
                    var continuation = NativeTransportCouncilFixture.issue(command.actionId(), "rejected-assign", "rejected-status", Stage.HELPER_STATUS, before, status, () -> { });
                    var actual = assertInstanceOf(NativeActionPort.AckReceived.class, transport.continueCouncil(continuation, status, Instant.now().plusSeconds(5)));
                    assertTrue(actual.custody().isPresent());
                    if (variant == CouncilRejectionVariant.CLEAN) {
                        NativeRequest receipt = new NativeRequest("private-query-assign-councillor-receipt-v1", Optional.empty(), raw("{}"));
                        var forbiddenReceipt = NativeTransportCouncilFixture.issue(command.actionId(), "rejected-assign", "never-send-receipt", Stage.RECEIPT_QUERY, before, receipt, () -> { });
                        assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class, transport.continueCouncil(forbiddenReceipt, receipt, Instant.now().plusSeconds(5)));
                        assertFalse(forbiddenReceipt.consumed()); assertEquals(2, port.writes);
                        var reconstructed = new NativeActionPort.AckReceived(actual.requestId(), actual.nativeOk(), actual.originalResultToken(), actual.originalFrame(), actual.originalPacket(), actual.outbound(), actual.custody());
                        assertThrows(IOException.class, () -> scope.complete(reconstructed));
                        scope.complete(actual);
                    } else {
                        if (variant == CouncilRejectionVariant.EXECUTOR_EXCEPTION
                                || variant == CouncilRejectionVariant.PRIOR_ASSIGNMENT_UNRESOLVED) {
                            NativeRequest receipt = new NativeRequest("private-query-assign-councillor-receipt-v1", Optional.empty(), raw("{}"));
                            var forbiddenReceipt = NativeTransportCouncilFixture.issue(command.actionId(), "rejected-assign", "ambiguous-receipt", Stage.RECEIPT_QUERY, before, receipt, () -> { });
                            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,
                                    transport.continueCouncil(forbiddenReceipt, receipt, Instant.now().plusSeconds(5)));
                            assertFalse(forbiddenReceipt.consumed());
                        }
                        assertThrows(IOException.class, () -> scope.complete(actual), variant.name());
                    }
                    return actual;
                };
                if (variant == CouncilRejectionVariant.CLEAN) transport.withMailbox(Instant.now().plusSeconds(15), work);
                else assertThrows(IOException.class, () -> transport.withMailbox(Instant.now().plusSeconds(15), work), variant.name());
                assertEquals(2, port.writes, variant.name());
                assertEquals(variant != CouncilRejectionVariant.CLEAN, transport.mailboxDiagnostics().poison().isPresent(), variant.name());
            }
        }
    }
    private static String councilRejectedResult() {
        return """
                {"schema":"xar.ck3.council-application-main/v1","accepted":true,"step":"assign-councillor-v1",
                 "status":"rejected_before_submit","query_sequence":1,"snapshot_revision":0,"backend_id":"native-headless",
                 "council_assign_councillor_ack":{"status":"rejected_before_submit","failure":"native_helper_not_invoked",
                 "action_request_id":"rejected-assign","pre_snapshot_id":"","pre_public_revision":0,"pre_native_revision":0,
                 "pre_date_raw":0,"owner_character_id":-1,"position_key":"councillor_marshal","active_task_id":-1,
                 "candidate_character_id":73,"had_incumbent":false,"previous_incumbent_character_id":-1,"route":"none",
                 "native_helper_invoked":false,"queue_acceptance_observed":false,"verification_pending":false,"native_reason_key":""}}
                """;
    }
    private GuardEvidence councilGuard(NativeGameTransport transport, G2Source source, BigInteger revision) throws IOException {
        var frame = transport.latestObservedSnapshot().orElseThrow();
        var identity = new ProposalLifecycle.ObservationIdentity(config().machineId(), config().game(),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829), revision, BigInteger.ONE),
                        frame.snapshotId(), revision, "controlled-episode"), 1);
        Instant now = Instant.now();
        return new GuardEvidence(identity, source, config().sessionId(), frame.session().connectionGeneration(), new OperationKey("private-assign-councillor-v1"),
                ref("controlled-snapshot", frame.originalPacket()), ref("controlled-hello", transport.originalHello().packet().value()),
                "controlled-root", now, now.plusSeconds(30));
    }
    @Test void additionalPrivateQualificationPreservesTheOriginalVerifierAndAllowsChangedMetadata() throws Exception {
        Path producerSource = temporary.resolve("composed-private-source.txt");
        Path originalEvidence = temporary.resolve("composed-original-evidence.txt");
        Path rootEvidence = temporary.resolve("composed-root-evidence.txt");
        Files.writeString(producerSource, "controlled original private source");
        Files.writeString(originalEvidence, "controlled original qualification");
        Files.writeString(rootEvidence, "controlled Root qualification");
        ExactRef sourceRef = ref(producerSource.toString(), Files.readAllBytes(producerSource));
        ExactRef firstRef = ref(originalEvidence.toString(), Files.readAllBytes(originalEvidence));
        ExactRef rootRef = ref(rootEvidence.toString(), Files.readAllBytes(rootEvidence));
        G2Source source = new G2Source(config().machineId(), Instant.now().toString(), "controlled-fixture", sourceRef);
        NativeRequest request = new NativeRequest("private-assign-councillor-v1", Optional.empty(), raw("{\"candidate_character_id\":73}"));
        List<String> calls = new ArrayList<>();
        Replay port = new Replay(producer(hello(), false), producer(snapshot("7"), false));
        try (NativeGameTransport transport = new NativeGameTransport(port, config(), 16, 16)) {
            transport.observe(Instant.now().plusSeconds(5));
            GuardEvidence guard = councilGuard(transport, source, BigInteger.valueOf(7));
            NativePrivateActionPermission original = new NativePrivateActionPermission(new OperationKey(request.step()), "controlled-private", sourceRef,
                    typed -> { assertEquals(request, typed); calls.add("request"); },
                    (actualConfig, actualHello, actualGuard, typed) -> {
                        assertEquals(config(), actualConfig); assertEquals(transport.originalHello(), actualHello);
                        assertEquals(guard, actualGuard); assertEquals(request, typed); calls.add("original"); return firstRef;
                    });
            NativePrivateActionPermission composed = original.withAdditionalQualification((actualConfig, actualHello, actualGuard, typed) -> {
                assertEquals(config(), actualConfig); assertEquals(transport.originalHello(), actualHello);
                assertEquals(guard, actualGuard); assertEquals(request, typed); calls.add("Root"); return rootRef;
            });
            assertEquals(original.operation(), composed.operation()); assertEquals(original.permissionKey(), composed.permissionKey());
            assertEquals(original.originalProducerSource(), composed.originalProducerSource());
            composed.verify(config(), transport.originalHello(), guard, request);
            assertEquals(List.of("request", "original", "Root"), calls);
            assertEquals(0, port.writes);
            // Mutate producerSource
            Files.writeString(producerSource, "changed producer source");
            calls.clear();
            composed.verify(config(), transport.originalHello(), guard, request);
            assertEquals(List.of("request", "original", "Root"), calls);
            assertEquals(0, port.writes);
            // Mutate originalEvidence
            Files.writeString(originalEvidence, "changed original evidence");
            calls.clear();
            composed.verify(config(), transport.originalHello(), guard, request);
            assertEquals(List.of("request", "original", "Root"), calls);
            assertEquals(0, port.writes);
            // Mutate rootEvidence
            Files.writeString(rootEvidence, "changed root evidence");
            calls.clear();
            composed.verify(config(), transport.originalHello(), guard, request);
            assertEquals(List.of("request", "original", "Root"), calls);
            assertEquals(0, port.writes);
            // Delete producerSource
            Files.delete(producerSource);
            calls.clear();
            composed.verify(config(), transport.originalHello(), guard, request);
            assertEquals(List.of("request", "original", "Root"), calls);
            assertEquals(0, port.writes);
            // Delete originalEvidence
            Files.delete(originalEvidence);
            calls.clear();
            composed.verify(config(), transport.originalHello(), guard, request);
            assertEquals(List.of("request", "original", "Root"), calls);
            assertEquals(0, port.writes);
            // Delete rootEvidence
            Files.delete(rootEvidence);
            calls.clear();
            composed.verify(config(), transport.originalHello(), guard, request);
            assertEquals(List.of("request", "original", "Root"), calls);
            assertEquals(0, port.writes);
            // Actual validator throwing stops additional
            calls.clear();
            var validatorThrows = new NativePrivateActionPermission(new OperationKey(request.step()), "controlled-private", sourceRef,
                    typed -> { throw new IOException("validator failure"); },
                    (actualConfig, actualHello, actualGuard, typed) -> { calls.add("original"); return firstRef; })
                    .withAdditionalQualification((actualConfig, actualHello, actualGuard, typed) -> { calls.add("Root"); return rootRef; });
            assertThrows(IOException.class, () -> validatorThrows.verify(config(), transport.originalHello(), guard, request));
            assertEquals(List.of(), calls);
            assertEquals(0, port.writes);
            // Actual business Qv throwing stops additional
            calls.clear();
            var businessThrows = new NativePrivateActionPermission(new OperationKey(request.step()), "controlled-private", sourceRef,
                    typed -> { calls.add("request"); },
                    (actualConfig, actualHello, actualGuard, typed) -> { calls.add("original"); throw new IOException("business Qv failure"); })
                    .withAdditionalQualification((actualConfig, actualHello, actualGuard, typed) -> { calls.add("Root"); return rootRef; });
            assertThrows(IOException.class, () -> businessThrows.verify(config(), transport.originalHello(), guard, request));
            assertEquals(List.of("request", "original"), calls);
            assertEquals(0, port.writes);
            // Wrong operation rejected
            var wrongOp = new NativePrivateActionPermission(new OperationKey("wrong-operation"), "controlled-private", sourceRef,
                    typed -> { }, (actualConfig, actualHello, actualGuard, typed) -> firstRef);
            assertThrows(IOException.class, () -> wrongOp.verify(config(), transport.originalHello(), guard, request));
            assertEquals(0, port.writes);
        }
    }
    @Test void absentOrEmptyOriginalPrivateQualificationCannotBeHiddenByAValidAdditionalVerifier() throws Exception {
        Path producerSource = temporary.resolve("composed-failure-source.txt");
        Path originalEvidence = temporary.resolve("composed-stale-evidence.txt");
        Path rootEvidence = temporary.resolve("composed-valid-root.txt");
        Path emptyEvidence = temporary.resolve("composed-empty.txt");
        Files.writeString(producerSource, "controlled source"); Files.writeString(originalEvidence, "old original evidence");
        Files.writeString(rootEvidence, "valid Root evidence"); Files.write(emptyEvidence, new byte[0]);
        ExactRef sourceRef = ref(producerSource.toString(), Files.readAllBytes(producerSource));
        ExactRef staleRef = ref(originalEvidence.toString(), Files.readAllBytes(originalEvidence));
        ExactRef rootRef = ref(rootEvidence.toString(), Files.readAllBytes(rootEvidence));
        ExactRef emptyRef = ref(emptyEvidence.toString(), new byte[0]);
        Files.writeString(originalEvidence, "changed original evidence");
        G2Source source = new G2Source(config().machineId(), Instant.now().toString(), "controlled-fixture", sourceRef);
        NativeRequest request = new NativeRequest("private-assign-councillor-v1", Optional.empty(), raw("{\"candidate_character_id\":73}"));
        Replay port = new Replay(producer(hello(), false), producer(snapshot("7"), false));
        try (NativeGameTransport transport = new NativeGameTransport(port, config(), 16, 16)) {
            transport.observe(Instant.now().plusSeconds(5));
            GuardEvidence guard = councilGuard(transport, source, BigInteger.valueOf(7));
            // Stale returned ref is now DATA allowed, only null/empty stay invalid
            for (Optional<ExactRef> invalid : List.of(Optional.<ExactRef>empty(), Optional.of(emptyRef))) {
                AtomicInteger additionalCalls = new AtomicInteger();
                NativePrivateActionPermission composed = new NativePrivateActionPermission(new OperationKey(request.step()), "controlled-private", sourceRef,
                        typed -> { }, (actualConfig, actualHello, actualGuard, typed) -> invalid.orElse(null))
                        .withAdditionalQualification((actualConfig, actualHello, actualGuard, typed) -> { additionalCalls.incrementAndGet(); return rootRef; });
                assertThrows(IOException.class, () -> composed.verify(config(), transport.originalHello(), guard, request));
                assertEquals(0, additionalCalls.get()); assertEquals(0, port.writes);
            }
            // Stale ref success
            AtomicInteger additionalCalls = new AtomicInteger();
            NativePrivateActionPermission composed = new NativePrivateActionPermission(new OperationKey(request.step()), "controlled-private", sourceRef,
                    typed -> { }, (actualConfig, actualHello, actualGuard, typed) -> staleRef)
                    .withAdditionalQualification((actualConfig, actualHello, actualGuard, typed) -> { additionalCalls.incrementAndGet(); return rootRef; });
            composed.verify(config(), transport.originalHello(), guard, request);
            assertEquals(1, additionalCalls.get()); assertEquals(0, port.writes);
        }
    }
    private static ExactRef ref(String path, byte[] original) {
        try { return new ExactRef(path, original.length, java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(original))); }
        catch (java.security.NoSuchAlgorithmException unavailable) { throw new IllegalStateException(unavailable); }
    }
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
    @Test void originalPrivateAndSnapshotOnlyRequestProfilesPreserveExactRevisionContract() throws Exception {
        String g2 = "{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"private-fixture\",\"step\":\"query-sway-completion-v1-private\",\"expected_revision\":7,\"expected_snapshot_revision\":7}";
        assertArrayEquals(producer(g2, false), NativeWire.executePrivateQuery("private-fixture",
                "query-sway-completion-v1-private", BigInteger.valueOf(7), "{}".getBytes(StandardCharsets.UTF_8)));
        String snapshotOnly = "{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"snapshot-fixture\",\"step\":\"query-actor-cached-succession-v1\",\"expected_snapshot_revision\":7}";
        assertArrayEquals(producer(snapshotOnly, false), NativeWire.executeSnapshotRevisionOnly("snapshot-fixture",
                "query-actor-cached-succession-v1", BigInteger.valueOf(7), "{}".getBytes(StandardCharsets.UTF_8)));
        for (String invalid : new String[] { "{\"expected_snapshot_revision\":true}",
                "{\"expected_snapshot_revision\":7.0}", "{\"expected_snapshot_revision\":8}" }) {
            assertThrows(IOException.class, () -> NativeWire.executePrivateQuery("private-fixture",
                    "query-sway-completion-v1-private", BigInteger.valueOf(7), invalid.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IOException.class, () -> NativeWire.executeSnapshotRevisionOnly("snapshot-fixture",
                    "query-actor-cached-succession-v1", BigInteger.valueOf(7), invalid.getBytes(StandardCharsets.UTF_8)));
        }
    }
    @Test void originalPacketsKeepActualEndpointChronologyAndColdCodecWithoutRefreshingTheHeldSnapshot() throws Exception {
        Replay port = new Replay(producer(chronologyHello(), false), producer(snapshot("7"), false));
        byte[][] response = new byte[1][];
        byte[] heartbeat = producer("{\"type\":\"heartbeat\",\"protocol_version\":1,\"sequence\":3}", false);
        port.onWrite = packet -> {
            String id = NativeWire.decodeExecuteRequest(packet).requestId();
            response[0] = producer("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + id
                    + "\",\"ok\":true,\"result\":{\"exact\":18446744073709551615}}", false);
            port.packets.addLast(heartbeat); port.packets.addLast(response[0]);
        };
        try (NativeGameTransport transport = new NativeGameTransport(port, frontendConfig(), 16, 16, List.of(), new ChronologyClock())) {
            var originalSnapshot = transport.observe(Instant.now().plusSeconds(30));
            var ack = assertInstanceOf(NativeActionPort.AckReceived.class, transport.readCoreFrame(Instant.now().plusSeconds(30)));
            var custody = ack.custody().orElseThrow();
            assertEquals(BigInteger.valueOf(3), custody.writeEntered().order());
            assertEquals(BigInteger.valueOf(4), custody.writeCompleted().order());
            assertEquals(BigInteger.valueOf(6), custody.responseReceived().order());
            assertEquals(NativeRequestChronology.PacketIdentity.of(port.lastWrite), custody.originalRequest());
            assertEquals(NativeRequestChronology.PacketIdentity.of(response[0]), custody.originalResponse());
            assertEquals(transport.awaitHello(Instant.now().plusSeconds(30)), custody.session());
            custody.verify(ack);
            var cold = NativeRequestChronologyCodec.decode(NativeRequestChronologyCodec.encode(custody));
            assertEquals(custody, cold); cold.verify(ack);
            assertArrayEquals(port.lastWrite, ack.outbound().orElseThrow().originalPacket());
            assertArrayEquals(response[0], ack.originalPacket());
            assertEquals(originalSnapshot.observedAt(), transport.latestObservedSnapshot().orElseThrow().observedAt());
            assertArrayEquals(originalSnapshot.originalPacket(), transport.latestObservedSnapshot().orElseThrow().originalPacket());
        }
    }
    @Test void lateDuplicateOriginalPacketRetainsItsFirstReceiveEventInsteadOfTheCollectionTime() throws Exception {
        Replay port = new Replay(producer(chronologyHello(), false));
        byte[][] response = new byte[1][];
        byte[] heartbeat = producer("{\"type\":\"heartbeat\",\"protocol_version\":1,\"sequence\":4}", false);
        port.onWrite = packet -> {
            String id = NativeWire.decodeExecuteRequest(packet).requestId();
            response[0] = producer("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + id + "\",\"ok\":true,\"result\":{}}", false);
            port.packets.addLast(heartbeat); port.packets.addLast(response[0]);
        };
        try (NativeGameTransport transport = new NativeGameTransport(port, frontendConfig(), 1, 16, List.of(), new ChronologyClock())) {
            var unknown = assertInstanceOf(NativeActionPort.Unknown.class, transport.readCoreFrame(Instant.now().plusSeconds(30)));
            assertTrue(transport.originalRequestChronology(unknown.requestId()).isEmpty());
            assertTrue(transport.collectOriginalResult(unknown.requestId(), Instant.now().plusSeconds(30)).isPresent());
            var first = transport.originalRequestChronology(unknown.requestId()).orElseThrow();
            assertEquals(BigInteger.valueOf(5), first.responseReceived().order());
            port.packets.addLast(response[0]);
            var late = transport.collectOriginalOutcome(unknown.requestId(), Instant.now().plusSeconds(30)).orElseThrow();
            assertEquals(first, late.custody().orElseThrow());
            assertEquals(first, transport.originalRequestChronology(unknown.requestId()).orElseThrow());
            assertEquals(1, port.writes); first.verify(late);
        }
    }
    @Test void partialAndProvenZeroWritesNeverMintCompletedChronologyFromALaterAck() throws Exception {
        Replay partial = new Replay(producer(chronologyHello(), false));
        partial.onWrite = packet -> {
            String id = NativeWire.decodeExecuteRequest(packet).requestId();
            partial.packets.addLast(producer("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + id + "\",\"ok\":true,\"result\":{}}", false));
            partial.writeFailure = new NativePipeEndpoint.TransferFailure("controlled partial write", packet, 5, true, new IOException("controlled"));
        };
        try (NativeGameTransport transport = new NativeGameTransport(partial, frontendConfig(), 16, 16, List.of(), new ChronologyClock())) {
            var unknown = assertInstanceOf(NativeActionPort.Unknown.class, transport.readCoreFrame(Instant.now().plusSeconds(30)));
            var late = transport.collectOriginalOutcome(unknown.requestId(), Instant.now().plusSeconds(30)).orElseThrow();
            assertTrue(late.outbound().isPresent()); assertTrue(late.custody().isEmpty());
            assertTrue(transport.originalRequestChronology(unknown.requestId()).isEmpty());
            assertEquals(1, partial.writes);
        }
        Replay zero = new Replay(producer(chronologyHello(), false));
        zero.onWrite = packet -> zero.writeFailure = new NativePipeEndpoint.TransferFailure("controlled pre-write rejection", packet, 0, false, new IOException("controlled"));
        try (NativeGameTransport transport = new NativeGameTransport(zero, frontendConfig(), 16, 16, List.of(), new ChronologyClock())) {
            var rejected = assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class, transport.readCoreFrame(Instant.now().plusSeconds(30)));
            assertTrue(transport.originalOutboundPacket(rejected.requestId()).isEmpty());
            assertTrue(transport.originalRequestChronology(rejected.requestId()).isEmpty());
            assertEquals(0, rejected.proof().requestBytesWritten());
        }
    }
    @Test void actualClockRollbackAfterWriteIsUnknownAndNeverRepairsTheTimestamp() throws Exception {
        Instant first = Instant.now();
        ChronologyClock clock = new ChronologyClock(first, first.plusSeconds(1), first.minusSeconds(1));
        Replay port = new Replay(producer(chronologyHello(), false));
        port.onWrite = packet -> {
            String id = NativeWire.decodeExecuteRequest(packet).requestId();
            port.packets.addLast(producer("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + id + "\",\"ok\":true,\"result\":{}}", false));
        };
        try (NativeGameTransport transport = new NativeGameTransport(port, frontendConfig(), 16, 16, List.of(), clock)) {
            var unknown = assertInstanceOf(NativeActionPort.Unknown.class, transport.readCoreFrame(Instant.now().plusSeconds(30)));
            assertEquals(1, port.writes); assertTrue(transport.originalOutboundPacket(unknown.requestId()).isPresent());
            assertTrue(transport.originalRequestChronology(unknown.requestId()).isEmpty());
            assertTrue(transport.diagnostics().terminalFailure().orElseThrow().contains("UTC regressed"));
            assertThrows(IOException.class, () -> transport.collectOriginalOutcome(unknown.requestId(), Instant.now().plusSeconds(30)));
        }
    }
    @Test void responseTransferFailureAfterACompletedWriteCannotBecomeZeroDispatchEvenWithIdenticalRetainedBytes() throws Exception {
        Replay port = new Replay(producer(chronologyHello(), false));
        port.onWrite = packet -> {
            String id = NativeWire.decodeExecuteRequest(packet).requestId();
            port.packets.addLast(producer("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + id
                    + "\",\"ok\":true,\"result\":{\"late\":true}}", false));
            // Actual NativePipeEndpoint.readPacket reports failed reads with false/0. Even exact
            // outgoing bytes in a read failure cannot erase the write that already returned.
            port.readFailure = new NativePipeEndpoint.TransferFailure("controlled response read failure", packet, 0, false, new IOException("controlled"));
        };
        try (NativeGameTransport transport = new NativeGameTransport(port, frontendConfig(), 16, 16, List.of(), new ChronologyClock())) {
            var unknown = assertInstanceOf(NativeActionPort.Unknown.class, transport.readCoreFrame(Instant.now().plusSeconds(30)));
            assertEquals(1, port.writes);
            assertArrayEquals(port.lastWrite, unknown.originalRequestPacket());
            assertArrayEquals(port.lastWrite, transport.originalOutboundPacket(unknown.requestId()).orElseThrow().originalPacket());
            assertTrue(transport.originalRequestChronology(unknown.requestId()).isEmpty());
            var actualLateAck = transport.collectOriginalOutcome(unknown.requestId(), Instant.now().plusSeconds(30)).orElseThrow();
            var chronology = actualLateAck.custody().orElseThrow();
            chronology.verify(actualLateAck);
            var cold = NativeRequestChronologyCodec.decode(NativeRequestChronologyCodec.encode(chronology));
            assertEquals(chronology, cold); cold.verify(actualLateAck);
            assertEquals(1, port.writes);
        }
    }
    @Test void equalLengthForeignFailureBytesCannotProveThatTheActualOutgoingPacketWasNeverWritten() throws Exception {
        Replay port = new Replay(producer(chronologyHello(), false));
        port.onWrite = packet -> {
            byte[] foreign = packet.clone(); foreign[foreign.length - 1] ^= 1;
            port.writeFailure = new NativePipeEndpoint.TransferFailure("foreign zero report", foreign, 0, false, new IOException("controlled"));
        };
        try (NativeGameTransport transport = new NativeGameTransport(port, frontendConfig(), 16, 16, List.of(), new ChronologyClock())) {
            var unknown = assertInstanceOf(NativeActionPort.Unknown.class, transport.readCoreFrame(Instant.now().plusSeconds(30)));
            assertEquals(1, port.writes);
            assertArrayEquals(port.lastWrite, unknown.originalRequestPacket());
            assertTrue(transport.originalOutboundPacket(unknown.requestId()).isPresent());
            assertTrue(transport.originalRequestChronology(unknown.requestId()).isEmpty());
        }
    }
    @Test void conflictingSecondResponseCannotReplaceTheFirstPacketCustodyAfterItWasConsumed() throws Exception {
        Replay port = new Replay(producer(chronologyHello(), false));
        port.onWrite = packet -> {
            String id = NativeWire.decodeExecuteRequest(packet).requestId();
            port.packets.addLast(producer("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + id + "\",\"ok\":true,\"result\":{}}", false));
        };
        try (NativeGameTransport transport = new NativeGameTransport(port, frontendConfig(), 16, 16, List.of(), new ChronologyClock())) {
            var first = assertInstanceOf(NativeActionPort.AckReceived.class, transport.readCoreFrame(Instant.now().plusSeconds(30)));
            byte[] conflicting = producer("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + first.requestId() + "\",\"ok\":true,\"result\":{\"changed\":true}}", false);
            port.packets.addLast(conflicting);
            assertThrows(IOException.class, () -> transport.collectOriginalOutcome(first.requestId(), Instant.now().plusSeconds(30)));
            assertArrayEquals(conflicting, transport.lastOriginalPacket());
            assertEquals(first.custody(), transport.originalRequestChronology(first.requestId()));
            assertThrows(IOException.class, () -> transport.verifyHeld(Instant.now().plusSeconds(30)));
        }
    }
    private static String chronologyHello() {
        return frontendHello(false).replace("\"game.state.snapshot\"", "\"game.state.snapshot\",\"game.query.core-frame.v1\"");
    }
    @Test void aNewJavaTransportCannotReuseThePreviousCounterEpochEvenWithTheSameNativeSession() throws Exception {
        NativeRequestChronology previous = null;
        for (int controller = 0; controller < 2; controller++) {
            Replay port = new Replay(producer(chronologyHello(), false));
            port.onWrite = packet -> {
                String id = NativeWire.decodeExecuteRequest(packet).requestId();
                port.packets.addLast(producer("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + id + "\",\"ok\":true,\"result\":{}}", false));
            };
            try (NativeGameTransport transport = new NativeGameTransport(port, frontendConfig(), 16, 16, List.of(), new ChronologyClock())) {
                var ack = assertInstanceOf(NativeActionPort.AckReceived.class, transport.readCoreFrame(Instant.now().plusSeconds(30)));
                var actual = ack.custody().orElseThrow(); actual.verify(ack);
                assertEquals(actual, NativeRequestChronologyCodec.decode(NativeRequestChronologyCodec.encode(actual)));
                if (previous != null) {
                    assertEquals(previous.session(), actual.session());
                    assertEquals(previous.writeEntered().order(), actual.writeEntered().order());
                    assertFalse(previous.custodyEpoch().equals(actual.custodyEpoch()));
                }
                previous = actual;
            }
        }
    }
    private static final class ChronologyClock extends Clock {
        private final ArrayDeque<Instant> scripted;
        private Instant next = Instant.now();
        ChronologyClock(Instant... events) { scripted = new ArrayDeque<>(List.of(events)); }
        @Override public ZoneId getZone() { return ZoneOffset.UTC; }
        @Override public Clock withZone(ZoneId zone) { if (!zone.equals(ZoneOffset.UTC)) throw new IllegalArgumentException("controlled UTC only"); return this; }
        @Override public Instant instant() {
            if (!scripted.isEmpty()) return scripted.removeFirst();
            Instant result = next; next = next.plusNanos(1); return result;
        }
    }

    private static String frontendHello(boolean capability) {
        String value = hello().replace("\"fixture-adapter\"", "\"ck3-1.20.0.4-msvc-x64\"")
                .replace("\"expected_ck3_sha256\":\"" + "0".repeat(64) + "\"", "\"expected_ck3_sha256\":\"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518\",\"expected_ck3_version\":\"1.20.0.4\"");
        return capability ? value.replace("\"game.state.snapshot\"", "\"game.command.query-frontend-gui-route-v1\"") : value;
    }
    private static NativePipeEndpoint.Config frontendConfig() {
        return new NativePipeEndpoint.Config(config().pipeName(), config().machineId(), config().game(), config().sessionId(),
                "fixture", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518", "ck3-1.20.0.4-msvc-x64");
    }
    private byte[] producer(String frame, boolean large) throws Exception {
        String python = required("xar.native.producer.python");
        String source = required("xar.native.producer.source");
        String sha256 = required("xar.native.producer.sha256");
        if (!sha256.matches("[a-f0-9]{64}") || !Path.of(source).isAbsolute() || !Path.of(python).isAbsolute())
            throw new IllegalStateException("original producer requires pinned absolute Python/source and SHA256");
        Path output = temporary.resolve("original-send-" + (++sequence) + ".base64");
        Path error = temporary.resolve("original-send-" + sequence + ".stderr");
        Process process = new ProcessBuilder(python, "-X", "utf8", "-c", ORIGINAL_SEND_FIXTURE, source, sha256,
                Base64.getEncoder().encodeToString(frame.getBytes(StandardCharsets.UTF_8)), large ? "large" : "small")
                .redirectOutput(output.toFile()).redirectError(error.toFile()).start();
        if (!process.waitFor(20, TimeUnit.SECONDS)) { process.destroyForcibly(); throw new IOException("original producer fixture timeout"); }
        if (process.exitValue() != 0) throw new IOException("original producer fixture failed: " + Files.readString(error, StandardCharsets.UTF_8));
        return Base64.getDecoder().decode(Files.readAllBytes(output));
    }
    @Test void actualRiteCodecProducerReachesAllEightWireSelectorsWithoutRenamingTheNativeStep() throws Exception {
        for (RiteCreation selected : RiteCreation.values()) {
            ExactRef original = riteSource();
            Replay port = new Replay(producer(riteHello(true), false), producer(snapshot("7"), false));
            port.onWrite = packet -> {
                var wire = NativeWire.decodeExecuteRequest(packet);
                assertEquals("player-rite-creation-action-v1", wire.step());
                assertEquals(BigInteger.valueOf(7), wire.expectedRevision().orElseThrow());
                NativeStepDiscriminator.requireWire(selected.operationKey(), selected.kind(), wire.step(), new RawJson(wire.normalizedAdditionalFields().value()));
                var fields = NativeWire.object(NativeWire.parse(wire.normalizedAdditionalFields().value()));
                assertEquals(selected.wire(), fields.get("operation").textValue());
                assertEquals(new BigInteger("18446744073709551615"), fields.get("expected_connection_generation").bigIntegerValue());
                port.packets.addLast(producer("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + wire.requestId() + "\",\"ok\":true,\"result\":{\"transport_only_fixture\":true}}", false));
            };
            try (var transport = new NativeGameTransport(port, config(), 16, 16)) {
                transport.observe(Instant.now().plusSeconds(5));
                GuardEvidence guard = riteGuard(transport, original, selected.operationKey());
                String id = "rite-wire-" + selected.wire();
                NativeRequest actual = riteRequest(selected, guard, id);
                NativeActionPort.AckReceived ack;
                if (selected == RiteCreation.PREVIEW) {
                    ReadContract<RawJson> contract = ritePreview(original, actual);
                    var read = new PlanningReadRequest(guard.observed(), guard.source(), guard.sessionId(), selected.operationKey(), new OpportunityJson.Obj(Map.of()), guard.validUntil());
                    NativeRequest prepared = contract.prepare(read, id);
                    var permit = NativeSelectorReadFixture.issue(contract, read, prepared, new PlanningReadGuard(guard, true, true, true, "b".repeat(64)), id);
                    ack = assertInstanceOf(NativeActionPort.AckReceived.class, transport.read(permit, prepared, guard.validUntil()));
                    assertTrue(permit.consumed());
                } else {
                    var permit = NativeTransportSubmissionFixture.issue(riteCommand(guard), guard, actual, id);
                    ack = assertInstanceOf(NativeActionPort.AckReceived.class, transport.submit(permit, actual, guard.validUntil()));
                    assertTrue(permit.consumed());
                }
                assertEquals(1, port.writes);
                assertArrayEquals(port.lastWrite, ack.outbound().orElseThrow().originalPacket());
                assertTrue(transport.originalRequestChronology(id).isPresent());
                assertEquals(selected.operationKey(), NativeStepDiscriminator.fromJson(NativeStepDiscriminator.toJson(NativeStepDiscriminator.identity(selected.operationKey()))).operation());
            }
        }
    }
    @Test void transportRejectsCrossKindSelectorAliasCapabilityAndForgedReadBeforeAnyOriginalWrite() throws Exception {
        ExactRef original = riteSource();
        Replay port = new Replay(producer(riteHello(true), false), producer(snapshot("7"), false));
        try (var transport = new NativeGameTransport(port, config(), 16, 32)) {
            transport.observe(Instant.now().plusSeconds(5));
            GuardEvidence actionGuard = riteGuard(transport, original, RiteCreation.OPEN_CREATE_DRAFT.operationKey());
            var preview = riteRequest(RiteCreation.PREVIEW, actionGuard, "unused-preview");
            var action = riteRequest(RiteCreation.OPEN_CREATE_DRAFT, actionGuard, "unused-action");
            List<NativeRequest> invalid = List.of(preview,
                    new NativeRequest(action.step(), Optional.empty(), action.additionalFields()),
                    new NativeRequest(action.step(), Optional.of("game.command.pause-map"), action.additionalFields()),
                    new NativeRequest(RiteCreation.OPEN_CREATE_DRAFT.operationKey().value(), action.requiredCapability(), action.additionalFields()),
                    new NativeRequest(action.step(), action.requiredCapability(), raw("{\"operation\":true}")),
                    new NativeRequest(action.step(), action.requiredCapability(), raw("{\"operation\":\"not_a_registered_selector\"}")));
            int counter = 0;
            for (var forged : invalid) {
                var permit = NativeTransportSubmissionFixture.issue(riteCommand(actionGuard), actionGuard, forged, "invalid-rite-" + counter++);
                assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class, transport.submit(permit, forged, actionGuard.validUntil()));
                assertFalse(permit.consumed()); assertEquals(0, port.writes);
            }
            GuardEvidence bare = riteGuard(transport, original, new OperationKey(action.step()));
            var barePermit = NativeTransportSubmissionFixture.issue(riteCommand(bare), bare, action, "ambiguous-bare-rite");
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class, transport.submit(barePermit, action, bare.validUntil()));
            GuardEvidence readGuard = riteGuard(transport, original, RiteCreation.PREVIEW.operationKey());
            var contract = ritePreview(original, preview);
            var read = new PlanningReadRequest(readGuard.observed(), readGuard.source(), readGuard.sessionId(), contract.operation(), new OpportunityJson.Obj(Map.of()), readGuard.validUntil());
            var forgedRead = NativeSelectorReadFixture.issue(contract, read, action, new PlanningReadGuard(readGuard, true, true, true, "b".repeat(64)), "forged-rite-read");
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class, transport.read(forgedRead, action, readGuard.validUntil()));
            assertFalse(forgedRead.consumed()); assertEquals(0, port.writes);
        }
        Replay missing = new Replay(producer(riteHello(false), false), producer(snapshot("7"), false));
        try (var transport = new NativeGameTransport(missing, config(), 16, 16)) {
            transport.observe(Instant.now().plusSeconds(5));
            var guard = riteGuard(transport, original, RiteCreation.OPEN_CREATE_DRAFT.operationKey());
            var request = riteRequest(RiteCreation.OPEN_CREATE_DRAFT, guard, "missing-rite-cap");
            var permit = NativeTransportSubmissionFixture.issue(riteCommand(guard), guard, request, "missing-rite-cap");
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class, transport.submit(permit, request, guard.validUntil()));
            assertFalse(permit.consumed()); assertEquals(0, missing.writes);
        }
    }
    @Test void unknownRiteOriginalCannotBeReplayedOrEscapedThroughAPrivatePermission() throws Exception {
        ExactRef original = riteSource();
        Replay port = new Replay(producer(riteHello(true), false), producer(snapshot("7"), false));
        port.onWrite = packet -> port.readFailure = new IOException("controlled actual post-write response loss");
        try (var transport = new NativeGameTransport(port, config(), 16, 16)) {
            transport.observe(Instant.now().plusSeconds(5));
            var guard = riteGuard(transport, original, RiteCreation.CONFIRM_ONCE.operationKey());
            var request = riteRequest(RiteCreation.CONFIRM_ONCE, guard, "rite-once-original");
            var permit = NativeTransportSubmissionFixture.issue(riteCommand(guard), guard, request, "rite-once-original");
            var outcome = assertInstanceOf(NativeActionPort.Unknown.class, transport.submit(permit, request, guard.validUntil()));
            assertTrue(permit.consumed()); assertEquals(1, port.writes);
            assertArrayEquals(port.lastWrite, outcome.originalRequestPacket());
            assertInstanceOf(NativeActionPort.Unknown.class, transport.submit(permit, request, guard.validUntil()));
            var duplicate = NativeTransportSubmissionFixture.issue(riteCommand(guard), guard, request, "rite-once-original");
            assertInstanceOf(NativeActionPort.Unknown.class, transport.submit(duplicate, request, guard.validUntil()));
            assertFalse(duplicate.consumed()); assertEquals(1, port.writes);
            AtomicInteger qualifiers = new AtomicInteger();
            var privatePermission = new NativePrivateActionPermission(guard.operation(), "fixture-cannot-grant-rite-private", original,
                    value -> { }, (config, hello, frame, typed) -> { qualifiers.incrementAndGet(); return original; });
            assertThrows(IOException.class, () -> privatePermission.verify(config(), transport.originalHello(), guard, request));
            var noCap = new NativeRequest(request.step(), Optional.empty(), request.additionalFields());
            assertThrows(IOException.class, () -> privatePermission.verify(config(), transport.originalHello(), guard, noCap));
            assertEquals(0, qualifiers.get()); assertEquals(1, port.writes);
        }
    }
    private ExactRef riteSource() throws IOException {
        Path path = temporary.resolve("rite-source-" + (++sequence) + ".txt");
        Files.writeString(path, "controlled software transport source; no Game/source qualification");
        return ref(path.toString(), Files.readAllBytes(path));
    }
    private GuardEvidence riteGuard(NativeGameTransport transport, ExactRef original, OperationKey operation) throws IOException {
        var source = new G2Source(config().machineId(), Instant.now().toString(), "controlled-rite-transport", original);
        var base = councilGuard(transport, source, BigInteger.valueOf(7));
        return new GuardEvidence(base.origin(), source, base.sessionId(), base.connectionGeneration(), operation,
                base.nativeEvidence(), base.capabilityEvidence(), base.authorityId(), base.observedAt(), base.validUntil(), base.supportingEvidence());
    }
    private static ActionCommand riteCommand(GuardEvidence guard) {
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, guard.observed(), guard.source(), "controlled-rite-transport/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"), true)));
        return new ActionCommand("controlled-rite-" + guard.operation().value(), guard.observed(), guard.source(), guard.sessionId(), guard.operation(),
                new OpportunityJson.Obj(Map.of()), expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), guard.validUntil());
    }
    private static NativeRequest riteRequest(RiteCreation operation, GuardEvidence guard, String requestId) {
        RiteCreationContract.Write write = switch (operation) {
            case PREVIEW -> null;
            case OPEN_CREATE_DRAFT -> new RiteCreationContract.OpenCreate();
            case OPEN_EDIT_CURRENT_RITE_DRAFT -> new RiteCreationContract.OpenEdit();
            case SELECT_CORE_TENET -> new RiteCreationContract.CoreTenet(0, new RiteCreationContract.Definition("tenet_fixture"));
            case SELECT_DOCTRINE -> new RiteCreationContract.Doctrine(new RiteCreationContract.Definition("group_fixture"), new RiteCreationContract.Definition("doctrine_fixture"));
            case SET_NAME_FIELD -> new RiteCreationContract.Name(RiteCreationContract.NameField.NAME, "Transport fixture");
            case PREPARE_CONFIRMATION -> new RiteCreationContract.Prepare(new RiteCreationContract.Identity("a".repeat(64)), RiteCreationContract.Outcome.CREATE_RITE);
            case CONFIRM_ONCE -> new RiteCreationContract.Confirm(new RiteCreationContract.Identity("a".repeat(64)), RiteCreationContract.Outcome.CREATE_RITE);
        };
        var fields = new RiteCreationContract.NativeFields(operation, new RiteCreationContract.SourceRite(7), Optional.ofNullable(write),
                operation == RiteCreation.CONFIRM_ONCE ? Optional.of(requestId) : Optional.empty());
        var frame = new RiteCreationContract.Frame(guard.observed().frame().snapshotId(), guard.observed().frame().revision(),
                guard.observed().frame().identity().nativeRevision(), guard.connectionGeneration(), guard.observed().game().pid(),
                guard.observed().frame().identity().player().intValueExact(), guard.observed().frame().identity().dateRaw().intValueExact(),
                new RiteCreationContract.EpisodeScope("controlled-episode"));
        return new NativeRequest(operation.nativeStep(), Optional.of(operation.capability()), RiteCreationCodec.raw(RiteCreationCodec.node(RiteCreationCodec.nativeFields(fields, frame))));
    }
    private static ReadContract<RawJson> ritePreview(ExactRef source, NativeRequest actual) {
        return new ReadContract<>("controlled-rite-preview-v1", RiteCreation.PREVIEW.operationKey(), Optional.of(RiteCreation.PREVIEW.capability()),
                "controlled-rite-preview", ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP, source,
                request -> actual, receipt -> raw("{}"));
    }
    private static String riteHello(boolean capability) {
        return capability ? hello().replace("\"game.command.pause-map\"", "\"game.command.pause-map\",\"player_rite_creation_action_v1\"") : hello();
    }
    private static String required(String name) {
        String value = System.getProperty(name);
        if (value == null || value.isBlank()) throw new IllegalStateException("NOT EXECUTED: required original-producer fixture property missing: " + name);
        return value;
    }
    private static String hello() {
        return "{\"type\":\"hello\",\"protocol_version\":1,\"pid\":42,\"connection_generation\":18446744073709551615,\"bridge_version\":\"fixture\",\"expected_ck3_sha256\":\"" + "0".repeat(64)
                + "\",\"game_adapter_id\":\"fixture-adapter\",\"game_adapter_status\":\"ready\",\"ck3_build_match\":true,\"capabilities\":[\"game.state.snapshot\",\"game.command.pause-map\"]}";
    }
    private static String snapshot(String revision) {
        return "{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"fixture-snapshot\",\"revision\":" + revision
                + ",\"state\":{\"date_raw\":1,\"paused\":true,\"map_ready\":true,\"played_character\":{\"character_id\":29829,\"alive\":true},\"nullable\":null}}";
    }
    private static NativePipeEndpoint.Config config() {
        return new NativePipeEndpoint.Config("\\\\.\\pipe\\original-producer-offline-fixture", "fixture-machine", new GameGeneration(42,
                new PythonOnlyUInt64(BigInteger.ONE)), "fixture-session", "fixture", "0".repeat(64), "fixture-adapter");
    }
    private static final class Replay implements NativePacketPort {
        private final ArrayDeque<byte[]> packets;
        private int writes;
        private int verifications;
        private byte[] lastWrite = new byte[0];
        private PacketReaction onWrite = packet -> { };
        private IOException writeFailure;
        private IOException readFailure;
        private final List<Instant> writeDeadlines = new ArrayList<>();
        private final List<Instant> readDeadlines = new ArrayList<>();
        private Runnable onRead = () -> { };
        private Clock typedExpiryClock;
        Replay(byte[]... packets) { this.packets = new ArrayDeque<>(Arrays.asList(packets)); }
        @Override public void verify() { verifications++; }
        @Override public void awaitConnection(Instant deadline) { }
        @Override public byte[] readPacket(Instant deadline) throws IOException {
            readDeadlines.add(java.util.Objects.requireNonNull(deadline));
            onRead.run();
            if (typedExpiryClock != null) {
                Instant observed = java.util.Objects.requireNonNull(typedExpiryClock.instant());
                if (!observed.isBefore(deadline))
                    throw new NativePacketPort.DeadlineExpired(new NativeActionPort.DeadlineObservation(deadline, observed, false));
            }
            if (readFailure != null) {
                IOException actual = readFailure; readFailure = null; throw actual;
            }
            if (packets.isEmpty()) throw new IOException("fixture packets exhausted"); return packets.removeFirst().clone();
        }
        @Override public void writePacket(byte[] packet, Instant deadline) throws IOException {
            writeDeadlines.add(java.util.Objects.requireNonNull(deadline));
            writes++;
            lastWrite = packet.clone();
            try { onWrite.accept(packet.clone()); }
            catch (Exception failure) { throw new IOException("original fixture reaction failed", failure); }
            if (writeFailure != null) throw writeFailure;
        }
        private void clearCaptured() { writeDeadlines.clear(); readDeadlines.clear(); }
        private List<Instant> capturedWriteDeadlines() { return List.copyOf(writeDeadlines); }
        private List<Instant> capturedReadDeadlines() { return List.copyOf(readDeadlines); }
        @Override public void close() { }
    }
    @FunctionalInterface private interface PacketReaction { void accept(byte[] packet) throws Exception; }

    /** Controlled operation clock; reading time never advances it or consumes a script. */
    private static final class MutableClock extends Clock {
        private Instant current;
        MutableClock(Instant initial) { current = java.util.Objects.requireNonNull(initial); }
        @Override public ZoneId getZone() { return ZoneOffset.UTC; }
        @Override public Clock withZone(ZoneId zone) {
            if (!ZoneOffset.UTC.equals(zone)) throw new IllegalArgumentException("controlled UTC only");
            return this;
        }
        @Override public Instant instant() { return current; }
        private void advance(Duration amount) {
            java.util.Objects.requireNonNull(amount);
            if (amount.isNegative()) throw new IllegalArgumentException("controlled clock cannot regress");
            current = current.plus(amount);
        }
    }
    /** New timeout cases use the real Java encoder without the old external producer fixture. */
    private static byte[] timeoutPacket(String json) throws IOException {
        return NativeWire.packet(json.getBytes(StandardCharsets.UTF_8));
    }
    private static Replay timeoutPort() throws IOException {
        return new Replay(timeoutPacket(riteHello(true)), timeoutPacket(snapshot("7")));
    }
    private static byte[] timeoutAck(byte[] actualRequest) throws IOException {
        var request = NativeWire.decodeExecuteRequest(actualRequest);
        var row = org.xar.ck3.control.contracts.StrictJson.object();
        row.put("type", "command_result").put("protocol_version", 1)
                .put("request_id", request.requestId()).put("ok", true);
        row.set("result", org.xar.ck3.control.contracts.StrictJson.object());
        return NativeWire.packet(org.xar.ck3.control.contracts.StrictJson.canonical(row));
    }
    private NativeActionPort.DispatchOutcome timeoutRead(NativeGameTransport transport, ExactRef source,
            String requestId, Instant callerDeadline) throws IOException, InterruptedException {
        GuardEvidence guard = riteGuard(transport, source, RiteCreation.PREVIEW.operationKey());
        NativeRequest actual = riteRequest(RiteCreation.PREVIEW, guard, requestId);
        var contract = ritePreview(source, actual);
        var read = new PlanningReadRequest(guard.observed(), guard.source(), guard.sessionId(), contract.operation(),
                new OpportunityJson.Obj(Map.of()), guard.validUntil());
        NativeRequest prepared = contract.prepare(read, requestId);
        var permit = NativeSelectorReadFixture.issue(contract, read, prepared,
                new PlanningReadGuard(guard, true, true, true, "b".repeat(64)), requestId);
        return transport.read(permit, prepared, callerDeadline);
    }

    @Test void ordinaryReadUsesOneBoundedDeadlineAndRenewsOnlyForNewRequest() throws Exception {
        Replay port = timeoutPort();
        MutableClock clock = new MutableClock(Instant.now());
        NativeGameTransport transport = new NativeGameTransport(port, config(), 16, 16, List.of(), clock, Duration.ofSeconds(60));
        try (transport) {
            transport.observe(Instant.now().plusSeconds(30));
            port.clearCaptured();
            Instant start = clock.instant();
            port.onWrite = packet -> {
                clock.advance(Duration.ofSeconds(10));
                port.packets.addLast(timeoutPacket("{\"type\":\"pong\",\"protocol_version\":1,\"request_id\":\"unrelated-pong\",\"pid\":42}"));
                port.packets.addLast(timeoutAck(packet));
            };
            port.onRead = () -> clock.advance(Duration.ofSeconds(5));
            var first = assertInstanceOf(NativeActionPort.AckReceived.class, timeoutRead(transport, riteSource(), "read-1", start.plusSeconds(600)));
            assertTrue(first.nativeOk());
            assertEquals(1, port.writes);
            var firstWrites = port.capturedWriteDeadlines();
            var firstReads = port.capturedReadDeadlines();
            assertEquals(1, firstWrites.size());
            assertEquals(2, firstReads.size());
            assertEquals(start.plusSeconds(60), firstWrites.get(0));
            assertEquals(start.plusSeconds(60), firstReads.get(0));
            assertEquals(start.plusSeconds(60), firstReads.get(1));
            clock.advance(Duration.ofSeconds(7));
            port.clearCaptured();
            Instant secondStart = clock.instant();
            var second = assertInstanceOf(NativeActionPort.AckReceived.class, timeoutRead(transport, riteSource(), "read-2", secondStart.plusSeconds(600)));
            assertTrue(second.nativeOk());
            assertEquals(2, port.writes);
            var secondWrites = port.capturedWriteDeadlines();
            var secondReads = port.capturedReadDeadlines();
            assertEquals(1, secondWrites.size());
            assertEquals(2, secondReads.size());
            assertEquals(secondStart.plusSeconds(60), secondWrites.get(0));
            assertEquals(secondStart.plusSeconds(60), secondReads.get(0));
            assertEquals(secondStart.plusSeconds(60), secondReads.get(1));
            org.junit.jupiter.api.Assertions.assertNotEquals(firstWrites.get(0), secondWrites.get(0));
        }
    }

    @Test void shortCallerAndCompatibilityMutationKeepTheirOwnDeadline() throws Exception {
        Replay port = timeoutPort();
        port.onWrite = packet -> port.packets.addLast(timeoutAck(packet));
        MutableClock clock = new MutableClock(Instant.now());
        NativeGameTransport transport = new NativeGameTransport(port, config(), 16, 16, List.of(), clock, Duration.ofSeconds(60));
        try (transport) {
            transport.observe(Instant.now().plusSeconds(30));
            port.clearCaptured();
            var source = riteSource();
            var shortCaller = clock.instant().plusSeconds(20);
            var readOutcome = timeoutRead(transport, source, "short-read", shortCaller);
            assertInstanceOf(NativeActionPort.AckReceived.class, readOutcome);
            assertEquals(List.of(shortCaller), port.capturedWriteDeadlines());
            assertEquals(List.of(shortCaller), port.capturedReadDeadlines());
            port.clearCaptured();
            var operation = RiteCreation.OPEN_CREATE_DRAFT;
            var guard = riteGuard(transport, source, operation.operationKey());
            var request = riteRequest(operation, guard, "long-mutation");
            var permit = NativeTransportSubmissionFixture.issue(riteCommand(guard), guard, request, "long-mutation");
            var longCaller = clock.instant().plusSeconds(600);
            var submitOutcome = assertInstanceOf(NativeActionPort.AckReceived.class, transport.submit(permit, request, longCaller));
            assertTrue(permit.consumed());
            assertEquals(List.of(longCaller), port.capturedWriteDeadlines());
            assertEquals(List.of(longCaller), port.capturedReadDeadlines());
        }
        Replay compatPort = timeoutPort();
        compatPort.onWrite = packet -> compatPort.packets.addLast(timeoutAck(packet));
        NativeGameTransport compatTransport = new NativeGameTransport(compatPort, config(), 16, 16, List.of(), new ChronologyClock());
        try (compatTransport) {
            compatTransport.observe(Instant.now().plusSeconds(30));
            compatPort.clearCaptured();
            var compatSource = riteSource();
            var compatCaller = Instant.now().plusSeconds(600);
            var compatOutcome = timeoutRead(compatTransport, compatSource, "compat-read", compatCaller);
            assertInstanceOf(NativeActionPort.AckReceived.class, compatOutcome);
            assertEquals(List.of(compatCaller), compatPort.capturedWriteDeadlines());
            assertEquals(List.of(compatCaller), compatPort.capturedReadDeadlines());
        }
    }

    @Test void expiredReadRetainsUnknownAndNeverWritesOriginalAgain() throws Exception {
        Replay port = timeoutPort();
        MutableClock clock = new MutableClock(Instant.now());
        try (NativeGameTransport transport = new NativeGameTransport(port, config(), 16, 16, List.of(), clock, Duration.ofSeconds(60))) {
            transport.observe(Instant.now().plusSeconds(30));
            port.clearCaptured();
            Instant start = clock.instant();
            ExactRef source = riteSource();
            GuardEvidence guard = riteGuard(transport, source, RiteCreation.PREVIEW.operationKey());
            String id = "expired-read-" + (++sequence);
            NativeRequest actual = riteRequest(RiteCreation.PREVIEW, guard, id);
            var contract = ritePreview(source, actual);
            var read = new PlanningReadRequest(guard.observed(), guard.source(), guard.sessionId(), contract.operation(), new OpportunityJson.Obj(Map.of()), guard.validUntil());
            NativeRequest prepared = contract.prepare(read, id);
            var permit = NativeSelectorReadFixture.issue(contract, read, prepared, new PlanningReadGuard(guard, true, true, true, "b".repeat(64)), id);
            port.typedExpiryClock = clock;
            port.onWrite = packet -> { clock.advance(Duration.ofSeconds(61)); };
            var outcome = assertInstanceOf(NativeActionPort.Unknown.class, transport.read(permit, prepared, start.plusSeconds(600)));
            assertEquals(1, port.writes);
            assertEquals(List.of(start.plusSeconds(60)), port.capturedWriteDeadlines());
            assertEquals(List.of(start.plusSeconds(60)), port.capturedReadDeadlines());
            assertArrayEquals(port.lastWrite, outcome.originalRequestPacket());
            assertTrue(permit.consumed());
            assertEquals(id, outcome.requestId());
            var cause = outcome.failureCause().orElseThrow();
            assertEquals(NativeActionPort.FailureKind.DEADLINE_EXPIRED, cause.kind());
            assertEquals(NativeActionPort.FailureStage.RESPONSE_WAIT, cause.stage());
            var observation = cause.deadline().orElseThrow();
            assertEquals(start.plusSeconds(60), observation.suppliedDeadline());
            assertEquals(clock.instant(), observation.observedAt());
            assertFalse(observation.monotonicExpired());
            var second = assertInstanceOf(NativeActionPort.Unknown.class, transport.read(permit, prepared, start.plusSeconds(600)));
            assertEquals(1, port.writes);
            assertEquals(List.of(start.plusSeconds(60)), port.capturedWriteDeadlines());
            assertEquals(List.of(start.plusSeconds(60)), port.capturedReadDeadlines());
            assertArrayEquals(port.lastWrite, second.originalRequestPacket());
            assertEquals(id, second.requestId());
        }
    }
@Test void readBudgetClockFailureIsZeroAndOriginalPermitCanProceed() throws Exception {
    java.util.concurrent.atomic.AtomicBoolean failure = new java.util.concurrent.atomic.AtomicBoolean(false);
    java.time.Instant current = Instant.now();
    Clock clock = new Clock() {
        @Override public ZoneId getZone() { return ZoneOffset.UTC; }
        @Override public Clock withZone(ZoneId zone) { return this; }
        @Override public Instant instant() {
            if (failure.get()) throw new IllegalStateException("controlled budget clock failure");
            return current;
        }
    };
    Replay port = timeoutPort();
    port.onWrite = packet -> port.packets.addLast(timeoutAck(packet));
    try (NativeGameTransport transport = new NativeGameTransport(port, config(), 16, 16, List.of(), clock, Duration.ofSeconds(60))) {
        transport.observe(Instant.now().plusSeconds(30));
        port.clearCaptured();
        ExactRef source = riteSource();
        GuardEvidence guard = riteGuard(transport, source, RiteCreation.PREVIEW.operationKey());
        String id = "budget-clock-fixture";
        NativeRequest prepared = riteRequest(RiteCreation.PREVIEW, guard, id);
        var contract = ritePreview(source, prepared);
        var read = new PlanningReadRequest(guard.observed(), guard.source(), guard.sessionId(), contract.operation(), new OpportunityJson.Obj(Map.of()), guard.validUntil());
        var permit = NativeSelectorReadFixture.issue(contract, read, prepared, new PlanningReadGuard(guard, true, true, true, "b".repeat(64)), id);
        Instant caller = Instant.now().plusSeconds(600);
        failure.set(true);
        var rejected = assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class, transport.read(permit, prepared, caller));
        assertEquals(id, rejected.requestId());
        assertEquals(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE, rejected.proof().stage());
        assertEquals(0, rejected.proof().requestBytesWritten());
        assertFalse(permit.consumed());
        assertEquals(0, port.writes);
        assertTrue(port.capturedWriteDeadlines().isEmpty());
        assertTrue(port.capturedReadDeadlines().isEmpty());
        assertTrue(transport.originalOutboundPacket(id).isEmpty());
        assertTrue(transport.originalRequestChronology(id).isEmpty());
        failure.set(false);
        var ack = assertInstanceOf(NativeActionPort.AckReceived.class, transport.read(permit, prepared, caller));
        assertEquals(id, ack.requestId());
        assertTrue(ack.nativeOk());
        assertTrue(permit.consumed());
        assertEquals(1, port.writes);
        assertTrue(transport.originalOutboundPacket(id).isPresent());
    }
}

@Test void readBudgetInstantOverflowIsZeroWithoutConsumingPermit() throws Exception {
    Replay port = timeoutPort();
    port.onWrite = packet -> port.packets.addLast(timeoutAck(packet));
    MutableClock clock = new MutableClock(Instant.now());
    try (NativeGameTransport transport = new NativeGameTransport(port, config(), 16, 16, List.of(), clock, Duration.ofSeconds(Long.MAX_VALUE))) {
        transport.observe(Instant.now().plusSeconds(30));
        port.clearCaptured();
        ExactRef source = riteSource();
        GuardEvidence guard = riteGuard(transport, source, RiteCreation.PREVIEW.operationKey());
        String id = "overflow-read-" + (++sequence);
        NativeRequest prepared = riteRequest(RiteCreation.PREVIEW, guard, id);
        var contract = ritePreview(source, prepared);
        var read = new PlanningReadRequest(guard.observed(), guard.source(), guard.sessionId(), contract.operation(), new OpportunityJson.Obj(Map.of()), guard.validUntil());
        var permit = NativeSelectorReadFixture.issue(contract, read, prepared, new PlanningReadGuard(guard, true, true, true, "b".repeat(64)), id);
        Instant caller = Instant.now().plusSeconds(600);
        var outcome = assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class, transport.read(permit, prepared, caller));
        assertEquals(id, outcome.requestId());
        assertEquals(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE, outcome.proof().stage());
        assertEquals(0, outcome.proof().requestBytesWritten());
        assertFalse(permit.consumed());
        assertEquals(0, port.writes);
        assertTrue(port.capturedWriteDeadlines().isEmpty());
        assertTrue(port.capturedReadDeadlines().isEmpty());
        assertTrue(transport.originalOutboundPacket(id).isEmpty());
        assertTrue(transport.originalRequestChronology(id).isEmpty());
    }
}
}
