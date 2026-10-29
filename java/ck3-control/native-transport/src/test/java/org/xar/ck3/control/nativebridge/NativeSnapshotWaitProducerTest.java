package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.NativeSnapshotWaitReceiverFixture.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Arrays;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeSnapshotWaitPort;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.NativeTransportSubmissionFixture;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual endpoint byte reader with a software Win32 API, then the same receiver and original Python orchestration. */
public final class NativeSnapshotWaitProducerTest {
    @TempDir Path temporary;
    @Test void actualZeroPrefixDeadlineIsTypedDoesNotPoisonAndCannotConsumeAnAlreadyQueuedPrefix() throws Exception {
        Pipe api = new Pipe();
        try (var endpoint = endpoint(api)) {
            Instant wait = Instant.now().minusMillis(1);
            var elapsed = assertInstanceOf(NativePacketPort.Elapsed.class, endpoint.readPacketUntil(wait, deadline()));
            assertEquals(wait, elapsed.waitUntil()); assertFalse(elapsed.observedAt().isBefore(wait));
            assertEquals(0, api.readCalls); assertEquals(0, api.writes); assertEquals(0, endpoint.retainedFailureBytes().length);
            endpoint.verify();
            byte[] original = packet(snapshot("next", 8, STATE)); api.add(original);
            assertInstanceOf(NativePacketPort.Elapsed.class, endpoint.readPacketUntil(Instant.now().minusMillis(1), deadline()));
            assertEquals(0, api.readCalls, "an elapsed zero-prefix wait does not start consuming a queued packet");
            var received = assertInstanceOf(NativePacketPort.Packet.class, endpoint.readPacketUntil(Instant.now().plusSeconds(1), deadline()));
            assertArrayEquals(original, received.originalPacket());
            byte[] mutated = received.originalPacket(); mutated[4] ^= 1; assertArrayEquals(original, received.originalPacket());
            assertEquals(0, api.writes);
        }
    }
    @Test void startedPrefixOrBodyCanCompleteAfterWaitDeadlineButPartialCaptureFailureNeverBecomesElapsed() throws Exception {
        byte[] original = packet(snapshot("delayed", 8, STATE));
        for (int prefix : new int[] { 2, 4 }) {
            Pipe api = new Pipe(); api.maximumChunk = 2;
            api.add(Arrays.copyOf(original, prefix));
            try (var endpoint = endpoint(api)) {
                Instant wait = Instant.now().plusMillis(250);
                api.releaseAt = wait.plusMillis(30); api.delayed = Arrays.copyOfRange(original, prefix, original.length);
                var received = assertInstanceOf(NativePacketPort.Packet.class, endpoint.readPacketUntil(wait, wait.plusSeconds(3)));
                assertFalse(Instant.now().isBefore(wait)); assertArrayEquals(original, received.originalPacket());
                assertEquals(0, api.writes); endpoint.verify();
            }
        }
        for (int prefix : new int[] { 2, 7 }) {
            Pipe api = new Pipe(); byte[] partial = Arrays.copyOf(original, prefix); api.add(partial);
            try (var endpoint = endpoint(api)) {
                Instant wait = Instant.now().plusMillis(250);
                var failure = assertThrows(NativePipeEndpoint.TransferFailure.class,
                        () -> endpoint.readPacketUntil(wait, wait.plusMillis(250)));
                assertArrayEquals(partial, failure.retainedBytes()); assertArrayEquals(partial, endpoint.retainedFailureBytes());
                assertFalse(failure.writeAttempted()); assertEquals(0, failure.writtenBytes());
                assertThrows(IOException.class, endpoint::verify); assertEquals(0, api.writes);
            }
        }
    }
    @Test void actualPipeErrorsIdentityFailuresAndPartialInterruptionRemainFailuresEvenWithTimeoutLikeMessages() throws Exception {
        Pipe broken = new Pipe(); broken.failPeek = true;
        try (var endpoint = endpoint(broken)) {
            var failure = assertThrows(NativePipeEndpoint.TransferFailure.class,
                    () -> endpoint.readPacketUntil(Instant.now().plusSeconds(1), deadline()));
            assertEquals(0, failure.retainedBytes().length); assertThrows(IOException.class, endpoint::verify);
        }
        Pipe source = new Pipe();
        try (var endpoint = endpoint(source)) {
            source.guardFailure = new IOException("Native transport deadline expired");
            assertThrows(IOException.class, () -> endpoint.readPacketUntil(Instant.now().minusMillis(1), deadline()));
            assertEquals(0, source.readCalls);
        }
        Pipe foreign = new Pipe();
        try (var endpoint = endpoint(foreign)) {
            foreign.pid = 43;
            assertThrows(IOException.class, () -> endpoint.readPacketUntil(Instant.now().minusMillis(1), deadline()));
            assertEquals(0, foreign.readCalls);
        }
        Pipe interrupted = new Pipe(); interrupted.maximumChunk = 2; interrupted.interruptAfter = 2;
        byte[] partial = Arrays.copyOf(packet(snapshot("interrupted", 8, STATE)), 2); interrupted.add(partial);
        try (var endpoint = endpoint(interrupted)) {
            try {
                var failure = assertThrows(NativePacketPort.ReadInterrupted.class,
                        () -> endpoint.readPacketUntil(Instant.now().plusSeconds(1), deadline()));
                assertArrayEquals(partial, failure.originalPartialPacket()); assertArrayEquals(partial, endpoint.retainedFailureBytes());
                assertThrows(IOException.class, endpoint::verify);
            } finally { Thread.interrupted(); }
        }
    }
    @Test void actualEndpointToTransportElapsedReturnsTheSameOriginalAndReceivedUsesSoleCanonicalAccounting() throws Exception {
        Pipe api = new Pipe(); byte[] first = packet(snapshot("first", 7, STATE)); api.add(packet(HELLO)); api.add(first);
        try (var transport = transport(api, 16)) {
            var original = transport.observe(deadline()); int reads = api.readCalls;
            var before = transport.diagnostics().production().orElseThrow();
            var current = transport.currentSnapshot(deadline());
            assertArrayEquals(first, current.originalPacket()); assertEquals(original.observedAt(), current.observedAt());
            assertEquals(reads, api.readCalls, "already-satisfied public conditions can inspect actual cache without waiting");
            assertEquals(before, transport.diagnostics().production().orElseThrow());
            var elapsed = assertInstanceOf(NativeSnapshotWaitPort.Elapsed.class,
                    transport.waitForSnapshot(Instant.now().minusMillis(1), deadline()));
            assertArrayEquals(first, elapsed.frame().originalPacket()); assertEquals(original.session(), elapsed.frame().session());
            assertEquals(original.snapshotId(), elapsed.frame().snapshotId()); assertEquals(original.nativeRevision(), elapsed.frame().nativeRevision());
            assertEquals(original.observedAt(), elapsed.frame().observedAt());
            assertEquals(reads, api.readCalls); assertEquals(before, transport.diagnostics().production().orElseThrow());
            byte[] next = packet(snapshot("next", 8, STATE)); api.add(next);
            var received = assertInstanceOf(NativeSnapshotWaitPort.Received.class,
                    transport.waitForSnapshot(Instant.now().plusSeconds(1), deadline()));
            assertArrayEquals(next, received.frame().originalPacket()); assertEquals(BigInteger.valueOf(8), received.frame().nativeRevision());
            var after = transport.diagnostics().production().orElseThrow();
            assertEquals(before.receivedSnapshotCount().add(BigInteger.ONE), after.receivedSnapshotCount());
            assertEquals(before.rejectedSnapshotCount(), after.rejectedSnapshotCount()); assertEquals(0, api.writes);
            api.guardFailure = new IOException("actual source guard changed after timeout");
            assertThrows(IOException.class, () -> transport.waitForSnapshot(Instant.now().minusMillis(1), deadline()));
            assertThrows(IOException.class, () -> transport.currentSnapshot(deadline()));
        }
    }
    @Test void rejectedSemanticPacketUsesTheSameParserAndElapsedKeepsAcceptedOriginalWithoutGrantingFreshness() throws Exception {
        Pipe api = new Pipe(); byte[] first = packet(snapshot("first", 7, STATE)); api.add(packet(HELLO)); api.add(first);
        try (var transport = transport(api, 16)) {
            transport.observe(deadline());
            byte[] rejected = packet(snapshot("bad-war", 8, STATE.replace("\"active_wars\":[]", "\"active_wars\":true"))); api.add(rejected);
            var elapsed = assertInstanceOf(NativeSnapshotWaitPort.Elapsed.class,
                    transport.waitForSnapshot(Instant.now().plusMillis(100), deadline()));
            assertArrayEquals(first, elapsed.frame().originalPacket());
            var actual = transport.diagnostics().production().orElseThrow();
            assertEquals(BigInteger.TWO, actual.receivedSnapshotCount()); assertEquals(BigInteger.ONE, actual.rejectedSnapshotCount());
            assertArrayEquals(rejected, actual.lastReceivedSnapshot().orElseThrow().originalPacket().value());
            assertArrayEquals(rejected, actual.lastRejectedSnapshot().orElseThrow().original().originalPacket().value());
            assertEquals(0, api.writes);
        }
        Pipe bounded = new Pipe(); bounded.add(packet(HELLO)); bounded.add(first);
        try (var transport = transport(bounded, 1)) {
            transport.observe(deadline()); bounded.add(packet(snapshot("bad-war", 8, STATE.replace("\"active_wars\":[]", "\"active_wars\":true"))));
            assertThrows(IOException.class, () -> transport.waitForSnapshot(Instant.now().plusSeconds(1), deadline()));
            assertEquals(BigInteger.ONE, transport.diagnostics().production().orElseThrow().rejectedSnapshotCount());
        }
    }
    @Test void transportPreservesActualPartialFailureBytesAndCannotReturnRetainedSuccessForIt() throws Exception {
        Pipe api = new Pipe(); api.add(packet(HELLO)); api.add(packet(snapshot("first", 7, STATE)));
        try (var transport = transport(api, 16)) {
            transport.observe(deadline()); byte[] partial = Arrays.copyOf(packet(snapshot("partial", 8, STATE)), 7); api.add(partial);
            Instant wait = Instant.now().plusMillis(250);
            var failure = assertThrows(NativePipeEndpoint.TransferFailure.class,
                    () -> transport.waitForSnapshot(wait, wait.plusMillis(250)));
            assertArrayEquals(partial, failure.retainedBytes()); assertArrayEquals(partial, transport.lastOriginalPacket());
            assertEquals(NativeGameTransport.ReceivedState.TERMINAL, transport.diagnostics().receivedState());
            assertThrows(IOException.class, transport::latestObservedSnapshot); assertEquals(0, api.writes);
        }
    }
    @Test void missingAcceptedOriginalOrTypedProviderNeverCreatesASyntheticElapsedSnapshot() throws Exception {
        Pipe api = new Pipe(); api.add(packet(HELLO));
        try (var transport = transport(api, 16)) {
            transport.awaitHello(deadline());
            assertThrows(IOException.class, () -> transport.currentSnapshot(deadline()));
            assertThrows(IOException.class, () -> transport.waitForSnapshot(Instant.now().minusMillis(1), deadline()));
            assertTrue(transport.latestObservedSnapshot().isEmpty()); assertEquals(0, api.writes);
        }
        NativePacketPort legacy = new NativePacketPort() {
            public void verify() { }
            public void awaitConnection(Instant deadline) { }
            public byte[] readPacket(Instant deadline) { fail("typed wait must not call the legacy reader"); return new byte[0]; }
            public void writePacket(byte[] original, Instant deadline) { fail("typed wait never writes"); }
            public void close() { }
        };
        assertThrows(IOException.class, () -> legacy.readPacketUntil(Instant.now().minusMillis(1), deadline()));
    }
    @Test void actualUnknownThenLateOriginalPollHasZeroIoAndPopsOnlyAfterRetainingActualAckBytes() throws Exception {
        Path definition = temporary.resolve("controlled-original-poll-source.txt"); Files.writeString(definition, "software-only controlled source");
        byte[] definitionBytes = Files.readAllBytes(definition);
        ExactRef producer = exact(definition.toString(), definitionBytes);
        for (boolean nativeOk : new boolean[] { true, false }) {
            Pipe api = new Pipe(); api.allowWrites = true;
            api.add(packet(HELLO.replace("\"game.state.snapshot\"", "\"game.state.snapshot\",\"game.command.pause-map\"")));
            api.add(packet(snapshot("first", 7, STATE)));
            try (var transport = transport(api, 16)) {
                var frame = transport.observe(deadline());
                G2Source source = new G2Source(config().machineId(), Instant.now().toString(), "controlled-original-poll", producer);
                var identity = new ProposalLifecycle.ObservationIdentity(config().machineId(), config().game(),
                        new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(73), BigInteger.valueOf(7), BigInteger.valueOf(1234)),
                                frame.snapshotId(), BigInteger.valueOf(7), "controlled-episode"), 1);
                var guard = new GuardEvidence(identity, source, config().sessionId(), frame.session().connectionGeneration(), new OperationKey("pause-map"),
                        exact("controlled-snapshot", frame.originalPacket()), exact("controlled-hello", transport.originalHello().packet().value()),
                        "controlled-original-poll-root", Instant.now(), deadline());
                var expected = new ProposalLifecycle.ExpectedPostcondition(1, identity, source, "controlled-original-poll/v1",
                        java.util.List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"), true)));
                var command = new ActionCommand("original-poll-fixture", identity, source, guard.sessionId(), guard.operation(),
                        new OpportunityJson.Obj(java.util.Map.of()), expected, new JointBudgetSelector.Claims(java.util.Set.of(), java.util.Set.of(), java.util.Set.of(), java.util.Set.of()), guard.validUntil());
                var request = new NativeRequest("pause-map", Optional.of("game.command.pause-map"), new RawJson(new byte[] { '{', '}' }));
                String id = "actual-original-poll-" + nativeOk;
                var permit = NativeTransportSubmissionFixture.issue(command, guard, request, id);
                var unknown = assertInstanceOf(NativeActionPort.Unknown.class, transport.submit(permit, request, Instant.now().plusMillis(100)));
                assertTrue(permit.consumed()); assertArrayEquals(api.written.toByteArray(), unknown.originalRequestPacket());
                int reads = api.readCalls, checks = api.guardChecks, writes = api.writes;
                assertTrue(transport.pollOriginalOutcome(id).isEmpty());
                assertThrows(IOException.class, () -> transport.pollOriginalOutcome("unattempted-id"));
                assertEquals(reads, api.readCalls); assertEquals(checks, api.guardChecks); assertEquals(writes, api.writes);
                byte[] originalAck = packet("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + id + "\",\"ok\":" + nativeOk + ",\"result\":{\"native_counter\":18446744073709551615}}");
                api.add(originalAck);
                assertInstanceOf(NativeSnapshotWaitPort.Elapsed.class, transport.waitForSnapshot(Instant.now().plusMillis(30), deadline()));
                reads = api.readCalls; checks = api.guardChecks; writes = api.writes;
                api.guardFailure = new IOException("actual later source became unavailable; cache custody must remain readable");
                NativeActionPort.AckReceived firstRetained = transport.pollOriginalOutcome(id).orElseThrow();
                assertArrayEquals(originalAck, firstRetained.originalPacket()); assertArrayEquals(unknown.originalRequestPacket(), firstRetained.outbound().orElseThrow().originalPacket());
                assertEquals(nativeOk, firstRetained.nativeOk()); assertTrue(firstRetained.custody().isPresent());
                assertEquals(new BigInteger("18446744073709551615"), NativeWire.object(NativeWire.parse(firstRetained.originalResultToken().orElseThrow().bytes())).get("native_counter").bigIntegerValue());
                assertThrows(IllegalArgumentException.class, () -> { throw new IllegalArgumentException("controlled later semantic validation failure"); });
                assertTrue(transport.pollOriginalOutcome(id).isEmpty()); assertArrayEquals(originalAck, firstRetained.originalPacket());
                assertEquals(reads, api.readCalls); assertEquals(checks, api.guardChecks); assertEquals(writes, api.writes);
            }
        }
        NativeActionPort legacy = (permit, request, deadline) -> { throw new AssertionError("poll cannot submit"); };
        assertThrows(IOException.class, () -> legacy.pollOriginalOutcome("legacy-unavailable"));
    }

    private static final String ORIGINAL = """
        import ast,copy,hashlib,json,math,sys,threading,types,uuid
        from pathlib import Path
        path=Path(sys.argv[1]);data=path.read_bytes()
        if hashlib.sha256(data).hexdigest()!=sys.argv[2]:raise RuntimeError('original Native Driver source drift')
        tree=ast.parse(data.decode('utf-8-sig'));scope={'copy':copy,'math':math,'threading':threading,'uuid':uuid,'PROTOCOL_VERSION':1}
        def install(node):
            future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
            exec(compile(ast.fix_missing_locations(ast.Module(body=[future,node],type_ignores=[])),str(path),'exec'),scope)
        def cls(name):return next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==name)
        def method(owner,name):return next(n for n in cls(owner).body if isinstance(n,ast.FunctionDef) and n.name==name)
        for name in ['_validate_revision','_positive_seconds']:
            install(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name))
        state=cls('NativeProtocolState');state.body=[method('NativeProtocolState',name) for name in ['__init__','wait_for_public_change']];install(state)
        install(method('NativeHeadlessGameplayDriver','wait_for_change'))
        actual=scope['NativeProtocolState']('fixture');snapshots=[];retained={'snapshot_id':'actual-retained','revision':7}
        def take():snapshots.append(retained);return retained
        driver=types.SimpleNamespace(state=actual,capabilities=lambda:{'snapshot':True},take_snapshot=take)
        timed=scope['wait_for_change'](driver,0,timeout_seconds=0.001)
        if timed is not retained or snapshots!=[retained]:raise RuntimeError('original timeout did not return actual latest snapshot')
        actual._public_revision=1
        changed=scope['wait_for_change'](driver,0,timeout_seconds=1.0)
        if changed is not retained or len(snapshots)!=2:raise RuntimeError('original public-change branch differs')
        for timeout in [True,0,-1,float('inf')]:
            try:scope['wait_for_change'](driver,0,timeout_seconds=timeout)
            except ValueError:pass
            else:raise RuntimeError('original public timeout validation was widened')
        class Broken:
            def wait_for_public_change(self,*args):raise OSError('Native transport deadline expired')
        driver.state=Broken()
        try:scope['wait_for_change'](driver,0,timeout_seconds=1)
        except OSError:pass
        else:raise RuntimeError('original actual failure was converted into a timeout')
        if len(snapshots)!=2:raise RuntimeError('original failure returned retained success')
        print(json.dumps({'timeout_returns_original':True,'changed_returns_original':True,'actual_failures_propagate':True,'snapshot_calls':len(snapshots)},separators=(',',':')))
        """;
    @Test void independentOriginalPythonConditionAndDriverActuallyReturnLatestSnapshotOnTimeoutAndPropagateErrors() throws Exception {
        Path source = Path.of(required("xar.native.producer.source")), python = Path.of(required("xar.native.producer.python"));
        if (!source.isAbsolute() || !python.isAbsolute()) throw new IllegalArgumentException("absolute mandatory original fixture paths required");
        Path output = temporary.resolve("original-wait.json"), error = temporary.resolve("original-wait.stderr");
        Process process = new ProcessBuilder(python.toString(), "-X", "utf8", "-c", ORIGINAL, source.toString(), "eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603")
                .redirectOutput(output.toFile()).redirectError(error.toFile()).start();
        if (!process.waitFor(20, TimeUnit.SECONDS)) { process.destroyForcibly(); throw new IOException("original WAIT fixture timed out"); }
        if (process.exitValue() != 0) throw new IOException("original WAIT fixture failed: " + Files.readString(error, StandardCharsets.UTF_8));
        var actual = NativeWire.object(NativeWire.parse(Files.readAllBytes(output)));
        assertTrue(actual.get("timeout_returns_original").booleanValue()); assertTrue(actual.get("changed_returns_original").booleanValue());
        assertTrue(actual.get("actual_failures_propagate").booleanValue()); assertEquals(2, actual.get("snapshot_calls").intValue());
    }
    private static String required(String key) { String v = System.getProperty(key); if (v == null || v.isBlank()) throw new IllegalStateException("NOT EXECUTED: mandatory original WAIT fixture " + key); return v; }
    private static ExactRef exact(String path, byte[] original) {
        try { return new ExactRef(path, original.length, java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(original))); }
        catch (java.security.NoSuchAlgorithmException unavailable) { throw new IllegalStateException(unavailable); }
    }
}
