package org.xar.ck3.control.wave2.runtime.closedadoption;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.Instant;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.admission.closedpartial.ClosedPartialAdmissionVerifier;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/** Actual original writer/consumer subprocesses; the inherited SDK fixture authority stays explicitly synthetic. */
class RootConsumerOperationsIntegrationTest {
    private record Context(ClosedAdoptionTransactionTest.Fixture fixture,
            OriginalWriterTransaction.Committed committed, RecoveryEvidence basis, RecoveryEvidence qualification) { }
    private static Context context() throws Exception {
        var fixture = ClosedAdoptionTransactionTest.fixture();
        var settings = ClosedAdoptionTransactionTest.settings(fixture);
        var committed = OriginalWriterTransaction.execute(fixture.target(),fixture::material,
                ignored -> WindowsFileWriterSession.start(settings,WindowsFileWriterSession.Mode.WRITER));
        var prepared = ClosedColdInputsConsumer.prepare(fixture::material,committed,fixture::canonical);
        var basis = ClosedAdoptionTransactionTest.publish(fixture.root().resolve("retained-basis.json"),prepared.basisBytes());
        var qualification = ClosedAdoptionTransactionTest.publish(fixture.root().resolve("retained-qualification.json"),prepared.qualificationBytes(basis.reference()));
        return new Context(fixture,committed,basis,qualification);
    }

    @Test void realOriginalColdAndSdkConsumersUseTheSameAuthorityWithRepeatedCallbacks() throws Exception {
        var context = context(); var fixture = context.fixture();
        var settings = ClosedAdoptionTransactionTest.settings(fixture);
        byte[] pending = fixture.material().input().rawState().bytes();
        try (var authority = ClosedInputsSessionAuthority.open(fixture::material,context.committed(),fixture::canonical,
                context.basis(),context.qualification(),settings.leaseDeadline())) {
            var wire = StrictJson.parse(authority.qualify(context.basis().reference(),context.qualification().reference()).wireBytes());
            assertEquals(fixture.material().sources().sdkClosed().reference(),ExactRef.fromJson(wire.get("closed").get("sdk_closed_ref")));
            AtomicReference<WindowsFileWriterSession> child = new AtomicReference<>();
            var cold = OriginalColdConsumerSession.runOperation(authority,new OriginalColdConsumerSession.ColdInputs(),() -> {
                var process = WindowsFileWriterSession.start(settings,WindowsFileWriterSession.Mode.ROOT_OPERATION); child.set(process); return process;
            });
            assertEquals("COLD_INPUTS",StrictJson.parse(cold.originalConsumerReceipt()).get("operation").textValue());
            assertNotNull(child.get()); assertTrue(child.get().actualCommandResult().orElseThrow().passed());
            long beforeSdk = authority.callbackCount();
            var sdk = OriginalColdConsumerSession.runOperation(authority,new OriginalColdConsumerSession.SdkClosure(),() -> {
                var process = WindowsFileWriterSession.start(settings,WindowsFileWriterSession.Mode.ROOT_OPERATION); child.set(process); return process;
            });
            var result = StrictJson.parse(sdk.originalConsumerReceipt());
            assertEquals("SDK_CLOSURE",result.get("operation").textValue());
            assertEquals("xar.current-saved-qualified-sdk-closure/v1",result.get("operation_result").get("schema").textValue());
            assertEquals(fixture.material().sources().sdkClosed().reference(),ExactRef.fromJson(result.get("operation_result").get("source_ref")));
            assertTrue(authority.callbackCount()-beforeSdk >= 4,"baseline, resolver and formal SDK validator must call the same live authority");
            assertTrue(child.get().actualCommandResult().orElseThrow().passed());
            assertEquals(0,result.get("new_game_day_credit").longValue()); assertFalse(result.get("grants_new_warm_attachment").booleanValue());
            assertArrayEquals(pending,fixture.material().input().rawState().bytes());
            assertEquals(5190,StrictJson.parse(pending).get("pending_cycle").get("global_turn").longValue());
        }
    }

    @Test void closedExpiredWrongRefsAndOtherThreadsCannotUseTheRetainedContext() throws Exception {
        var context = context(); var fixture = context.fixture();
        var authority = ClosedInputsSessionAuthority.open(fixture::material,context.committed(),fixture::canonical,
                context.basis(),context.qualification(),Instant.now().plusSeconds(30));
        AtomicReference<Throwable> rejected = new AtomicReference<>();
        Thread other = new Thread(() -> {
            try { authority.qualify(context.basis().reference(),context.qualification().reference()); }
            catch (RuntimeException error) { rejected.set(error); }
        });
        other.start(); other.join(5_000); assertFalse(other.isAlive()); assertTrue(rejected.get() instanceof ContractViolationException);
        var wrong = new ExactRef(context.basis().reference().path(),context.basis().reference().bytes(),"0".repeat(64));
        assertThrows(ContractViolationException.class,() -> authority.qualify(wrong,context.qualification().reference()));
        authority.close(); assertTrue(authority.isClosed());
        assertThrows(ContractViolationException.class,() -> authority.qualify(context.basis().reference(),context.qualification().reference()));
        assertThrows(ContractViolationException.class,() -> ClosedInputsSessionAuthority.open(fixture::material,context.committed(),fixture::canonical,
                context.basis(),context.qualification(),Instant.now().minusSeconds(1)));
    }

    @Test void lostSdkAuthorityPreventsAnyFollowupChildLaunch() throws Exception {
        var context = context(); var fixture = context.fixture(); AtomicBoolean unavailable = new AtomicBoolean();
        var original = fixture.material();
        var missing = new ClosedAdoptionMaterial(original.input(),original.sources(),original.publishedEpoch(),original.publishedPrefix(),
                original.business(),original.sourceVerifier(),ClosedPartialAdmissionVerifier.unavailableOriginalSdk());
        ClosedAdoptionMaterial.CurrentSource current = () -> unavailable.get() ? missing : original;
        try (var authority = ClosedInputsSessionAuthority.open(current,context.committed(),fixture::canonical,
                context.basis(),context.qualification(),Instant.now().plusSeconds(30))) {
            unavailable.set(true); AtomicInteger launches = new AtomicInteger();
            assertThrows(ContractViolationException.class,() -> OriginalColdConsumerSession.runOperation(authority,
                    new OriginalColdConsumerSession.SdkClosure(),() -> { launches.incrementAndGet(); throw new java.io.IOException("must not launch"); }));
            assertEquals(0,launches.get());
        }
    }

    @Test void thirtyThirdCallbackIsRejectedAndTheOriginalTransportIsClosed() throws Exception {
        var context = context(); var fixture = context.fixture();
        var callback = StrictJson.object(); callback.put("schema","xar.java-closed-partial-cold-inputs-callback/v1");
        callback.put("machine_id",ClosedAdoptionTransactionTest.MACHINE);
        callback.set("basis_ref",context.basis().reference().toJson()); callback.set("validation_ref",context.qualification().reference().toJson());
        var incoming = new java.io.ByteArrayOutputStream();
        for (int index = 0; index <= OriginalColdConsumerSession.MAX_CALLBACKS_PER_OPERATION; index++) {
            OriginalWriterTransaction.send(incoming,callback);
        }
        var replies = new java.io.ByteArrayOutputStream(); AtomicInteger closes = new AtomicInteger(), exits = new AtomicInteger();
        var simulatedTransport = new OriginalWriterTransaction.ManagedProcess() {
            private final java.io.InputStream source = new java.io.ByteArrayInputStream(incoming.toByteArray());
            @Override public java.io.InputStream stdout() { return source; }
            @Override public java.io.OutputStream stdin() { return replies; }
            @Override public void closeOwnedInput() { closes.incrementAndGet(); }
            @Override public OriginalWriterTransaction.ActualExit awaitActualExit() {
                exits.incrementAndGet(); return new OriginalWriterTransaction.ActualExit(1,"1",0,true);
            }
        };
        try (var authority = ClosedInputsSessionAuthority.open(fixture::material,context.committed(),fixture::canonical,
                context.basis(),context.qualification(),Instant.now().plusSeconds(30))) {
            assertThrows(ContractViolationException.class,() -> OriginalColdConsumerSession.runOperation(authority,
                    new OriginalColdConsumerSession.SdkClosure(),() -> simulatedTransport));
            assertEquals(1,closes.get()); assertEquals(1,exits.get());
            long lines = new String(replies.toByteArray(),java.nio.charset.StandardCharsets.UTF_8).chars().filter(value -> value == '\n').count();
            assertEquals(1L+OriginalColdConsumerSession.MAX_CALLBACKS_PER_OPERATION,lines,"request plus exactly 32 qualified replies");
        }
    }

    @Test void independentPythonReaderCallsTheLiveJavaFileEndpointTwice() throws Exception {
        var context = context(); var fixture = context.fixture(); var settings = ClosedAdoptionTransactionTest.settings(fixture);
        String script = """
                import sys,json
                from tools.g2_saved_campaign.current_saved_basis_v1 import ExactRefV1,parse_ref
                from tools.g2_saved_campaign.current_saved_continuity_v1 import open_java_closed_partial_file_reader_v1
                reference=ExactRefV1(sys.argv[1],int(sys.argv[2]),sys.argv[3])
                reader=open_java_closed_partial_file_reader_v1(reference,expected_machine_id=sys.argv[4])
                with open(reference.path,'rb') as stream: endpoint=json.load(stream)
                basis=parse_ref(endpoint['basis_ref']);qualification=parse_ref(endpoint['validation_ref'])
                first=reader.java_closed_partial_cold_inputs(basis,qualification)
                second=reader.java_closed_partial_cold_inputs(basis,qualification)
                assert first==second
                assert first['grants_new_warm_attachment'] is False
                print(json.dumps({'calls':2,'scope':first['qualification_scope'],'sdk_closed_ref':first['closed']['sdk_closed_ref']}))
                """;
        try (var authority = ClosedInputsSessionAuthority.open(fixture::material,context.committed(),fixture::canonical,
                context.basis(),context.qualification(),settings.leaseDeadline())) {
            var endpoint = ClosedInputsFileEndpoint.create(authority,settings,"a".repeat(32),fixture.root(),settings.leaseDeadline());
            var reference = endpoint.descriptorRef();
            var stdout = fixture.root().resolve("file-reader.stdout.json"); var stderr = fixture.root().resolve("file-reader.stderr.log");
            var command = new WindowsJobProcess.CommandSpec(settings.python(),java.util.List.of("-B","-u","-X","utf8","-c",script,
                    reference.path(),Long.toString(reference.bytes()),reference.sha256(),ClosedAdoptionTransactionTest.MACHINE),
                    settings.repo(),settings.environment(),stdout,stderr,settings.memoryLimitBytes());
            try (var job = WindowsJobProcess.start(command)) {
                long deadline = System.nanoTime()+java.time.Duration.ofSeconds(30).toNanos();
                while (job.isRunning()) {
                    endpoint.poll();
                    if (System.nanoTime() >= deadline) { job.terminate(31); break; }
                    Thread.sleep(10);
                }
                var actual = job.await(java.time.Duration.ofSeconds(5),Instant.now().plusSeconds(5),settings.capacityGuard());
                assertTrue(actual.passed(),"independent original callback reader must exit zero with Job active zero; stderr="+stderr);
            }
            assertEquals(2,endpoint.processedCount());
            byte[] raw;
            try (var input = java.nio.file.Files.newInputStream(stdout)) { raw = input.readNBytes(RecoveryEvidence.MAX_BYTES+1); }
            assertTrue(raw.length <= RecoveryEvidence.MAX_BYTES);
            var result = StrictJson.parse(raw);
            assertEquals(2,result.get("calls").longValue());
            assertEquals(ClosedColdInputsConsumer.SCOPE,result.get("scope").textValue());
            assertEquals(fixture.material().sources().sdkClosed().reference(),ExactRef.fromJson(result.get("sdk_closed_ref")));
            assertFalse(authority.grantsWarmAttachment());
        }
    }

    @Test void fileEndpointRejectsTheWrongActualInterpreterBeforeQualifyingAnything() throws Exception {
        var context = context(); var fixture = context.fixture(); var settings = ClosedAdoptionTransactionTest.settings(fixture);
        try (var authority = ClosedInputsSessionAuthority.open(fixture::material,context.committed(),fixture::canonical,
                context.basis(),context.qualification(),settings.leaseDeadline())) {
            String nonce = "b".repeat(32), requestNonce = "c".repeat(32);
            var endpoint = ClosedInputsFileEndpoint.create(authority,settings,nonce,fixture.root(),settings.leaseDeadline());
            var actualJava = WindowsJobProcess.observeLiveProcess(ProcessHandle.current().pid()).identity();
            var requester = StrictJson.object(); requester.put("pid",actualJava.pid()); requester.put("creation_filetime",actualJava.creationFiletimeDecimal());
            requester.put("executable",actualJava.executable());
            var callback = StrictJson.object(); callback.put("schema","xar.java-closed-partial-cold-inputs-callback/v1");
            callback.put("machine_id",ClosedAdoptionTransactionTest.MACHINE); callback.set("basis_ref",context.basis().reference().toJson());
            callback.set("validation_ref",context.qualification().reference().toJson());
            var request = StrictJson.object(); request.put("schema","xar.java-closed-partial-inputs-file-request/v1");
            request.put("machine_id",ClosedAdoptionTransactionTest.MACHINE); request.put("session_nonce",nonce); request.put("request_nonce",requestNonce);
            request.put("observed_at_utc",Instant.now().toString());
            request.set("endpoint_ref",endpoint.descriptorRef().toJson()); request.set("requester",requester);
            request.set("transport_source_ref",settings.mechanicalSource().toJson()); request.set("cold_owner_source_ref",settings.coldOwnerSource().toJson());
            request.set("request",callback);
            java.nio.file.Files.write(fixture.root().resolve("callbacks").resolve(requestNonce+".request.json"),StrictJson.canonical(request));
            long calls = authority.callbackCount();
            assertThrows(java.io.IOException.class,endpoint::poll);
            assertEquals(calls,authority.callbackCount(),"wrong interpreter must fail before the real Java qualification");
            byte[] raw;
            try (var input = java.nio.file.Files.newInputStream(fixture.root().resolve("callbacks").resolve(requestNonce+".response.json"))) {
                raw = input.readNBytes(RecoveryEvidence.MAX_BYTES+1);
            }
            var refusal = StrictJson.parse(raw); assertEquals("REJECTED_OR_UNAVAILABLE",refusal.get("status").textValue());
            assertTrue(refusal.get("wire").isNull()); assertTrue(refusal.get("error").isTextual());
        }
    }

    @Test void activeOriginalConsumerPumpsAnIndependentFileReaderOnTheSameOwnerThread() throws Exception {
        var context = context(); var fixture = context.fixture(); var settings = ClosedAdoptionTransactionTest.settings(fixture);
        var marker = fixture.root().resolve("operation-is-active");
        String script = """
                import sys,json,time
                from pathlib import Path
                from tools.g2_saved_campaign.current_saved_basis_v1 import ExactRefV1,parse_ref
                from tools.g2_saved_campaign.current_saved_continuity_v1 import open_java_closed_partial_file_reader_v1
                reference=ExactRefV1(sys.argv[1],int(sys.argv[2]),sys.argv[3])
                reader=open_java_closed_partial_file_reader_v1(reference,expected_machine_id=sys.argv[4])
                with open(reference.path,'rb') as stream: endpoint=json.load(stream)
                limit=time.monotonic()+30
                while not Path(sys.argv[5]).exists():
                    if time.monotonic()>=limit: raise TimeoutError('actual original operation did not start')
                    time.sleep(.01)
                wire=reader.java_closed_partial_cold_inputs(parse_ref(endpoint['basis_ref']),parse_ref(endpoint['validation_ref']))
                assert wire['grants_new_warm_attachment'] is False
                print(json.dumps({'calls':1,'scope':wire['qualification_scope']}))
                """;
        try (var authority = ClosedInputsSessionAuthority.open(fixture::material,context.committed(),fixture::canonical,
                context.basis(),context.qualification(),settings.leaseDeadline())) {
            var endpoint = ClosedInputsFileEndpoint.create(authority,settings,"d".repeat(32),fixture.root(),settings.leaseDeadline());
            var operationSettings = RootConsumerSession.operationSettings(settings,settings.leaseDeadline(),endpoint);
            var reference = endpoint.descriptorRef();
            var stdout = fixture.root().resolve("active-reader.stdout.json"); var stderr = fixture.root().resolve("active-reader.stderr.log");
            var command = new WindowsJobProcess.CommandSpec(settings.python(),java.util.List.of("-B","-u","-X","utf8","-c",script,
                    reference.path(),Long.toString(reference.bytes()),reference.sha256(),ClosedAdoptionTransactionTest.MACHINE,marker.toString()),
                    settings.repo(),settings.environment(),stdout,stderr,settings.memoryLimitBytes());
            AtomicReference<WindowsFileWriterSession> child = new AtomicReference<>();
            try (var peer = WindowsJobProcess.start(command)) {
                var consumed = OriginalColdConsumerSession.runOperation(authority,new OriginalColdConsumerSession.ColdInputs(),() -> {
                    var process = WindowsFileWriterSession.start(operationSettings,WindowsFileWriterSession.Mode.ROOT_OPERATION);
                    child.set(process);
                    try {
                        java.nio.file.Files.writeString(marker,"actual original child started",java.nio.file.StandardOpenOption.CREATE_NEW);
                        long limit = System.nanoTime()+java.time.Duration.ofSeconds(30).toNanos();
                        while (true) {
                            boolean pending;
                            try (var entries = java.nio.file.Files.list(fixture.root().resolve("callbacks"))) {
                                pending = entries.anyMatch(path -> path.getFileName().toString().endsWith(".request.json"));
                            }
                            if (pending) { break; }
                            if (!peer.isRunning() || System.nanoTime() >= limit) {
                                throw new java.io.IOException("independent live reader did not publish its bounded request; stderr="+stderr);
                            }
                            try { Thread.sleep(10); }
                            catch (InterruptedException error) { Thread.currentThread().interrupt(); throw new java.io.IOException(error); }
                        }
                        if (endpoint.processedCount() != 0 || java.nio.file.Files.size(process.stdoutPath()) != 0) {
                            throw new java.io.IOException("actual original child must still await its first request; callback must remain pending");
                        }
                        return process;
                    } catch (java.io.IOException | RuntimeException error) {
                        try { process.closeOwnedInput(); process.awaitActualExit(); }
                        catch (java.io.IOException cleanup) { error.addSuppressed(cleanup); }
                        catch (InterruptedException cleanup) { Thread.currentThread().interrupt(); error.addSuppressed(cleanup); }
                        throw error;
                    }
                });
                assertEquals(1,endpoint.processedCount(),"the actual Root operation stdout/exit guard must service the waiting independent reader");
                assertEquals("COLD_INPUTS",StrictJson.parse(consumed.originalConsumerReceipt()).get("operation").textValue());
                assertTrue(child.get().actualCommandResult().orElseThrow().passed());
                // The peer is awaited with the original guard: no callback pumping after runOperation can rescue this assertion.
                var actual = peer.await(java.time.Duration.ofSeconds(5),Instant.now().plusSeconds(5),settings.capacityGuard());
                assertTrue(actual.passed(),"same-owner callback must release the independent process while the original operation is active");
                assertEquals(1,endpoint.processedCount());
            }
        }
    }

    @Test void anExplicitRestoreCommandCannotCreateHistoricalCustodyFromClosedJson() throws Exception {
        var context = context(); var fixture = context.fixture();
        try (var authority = ClosedInputsSessionAuthority.open(fixture::material,context.committed(),fixture::canonical,
                context.basis(),context.qualification(),Instant.now().plusSeconds(30))) {
            assertThrows(ContractViolationException.class,() -> authority.beginRestoreReads(1));
            assertEquals(ClosedColdInputsConsumer.SCOPE,authority.qualificationScope());
            var wire = StrictJson.parse(authority.qualify(context.basis().reference(),context.qualification().reference()).wireBytes());
            assertEquals(ClosedColdInputsConsumer.SCOPE,wire.get("qualification_scope").textValue());
            assertFalse(authority.grantsWarmAttachment());
        }
    }
}
