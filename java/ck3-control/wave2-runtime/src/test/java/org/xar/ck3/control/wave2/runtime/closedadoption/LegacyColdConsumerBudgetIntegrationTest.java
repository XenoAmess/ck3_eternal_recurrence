package org.xar.ck3.control.wave2.runtime.closedadoption;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/** Actual original writer/consumer Jobs; inherited original SDK prerequisite authority is explicitly synthetic. */
class LegacyColdConsumerBudgetIntegrationTest {
    /**
     * Preserve every original Java-produced field and byte; JSON permits trailing whitespace.
     * Only the qualified input frame is extended to its complete legal 64 KiB boundary.
     * The initial request stays original, and the historical cumulative profile stays unchanged.
     */
    private static final class CompleteQualifiedFrame implements OriginalWriterTransaction.ManagedProcess {
        private final WindowsFileWriterSession actual;
        private final ByteArrayOutputStream pending = new ByteArrayOutputStream();
        private int initialRequests;
        private int qualifiedReplies;
        private int producedReplyBytes;
        private final OutputStream requests = new OutputStream() {
            @Override public void write(int value) throws IOException {
                if (value != '\n') { pending.write(value); return; }
                byte[] original = pending.toByteArray(); pending.reset();
                var parsed = StrictJson.parse(original,OriginalWriterTransaction.MAX_PROTOCOL_BYTES);
                String schema = StrictJson.text(parsed.get("schema"));
                boolean qualified = ClosedColdInputsConsumer.INPUTS_SCHEMA.equals(schema);
                if (qualified) {
                    if (original.length > RecoveryEvidence.MAX_BYTES) { throw new IOException("original qualification exceeds its unchanged frame cap"); }
                    qualifiedReplies++;
                    producedReplyBytes = original.length;
                } else if ("xar.java-closed-partial-cold-consumer-request/v1".equals(schema)) {
                    initialRequests++;
                } else { throw new IOException("unexpected original frame in the fixed cold consumer test"); }
                actual.stdin().write(original);
                if (qualified) {
                    byte[] whitespace = new byte[RecoveryEvidence.MAX_BYTES-original.length];
                    Arrays.fill(whitespace,(byte)' '); actual.stdin().write(whitespace);
                }
                actual.stdin().write('\n'); actual.stdin().flush();
            }
            @Override public void flush() throws IOException { actual.stdin().flush(); }
        };
        private CompleteQualifiedFrame(WindowsFileWriterSession actual) { this.actual = actual; }
        @Override public InputStream stdout() { return actual.stdout(); }
        @Override public OutputStream stdin() { return requests; }
        @Override public void closeOwnedInput() throws IOException { actual.closeOwnedInput(); }
        @Override public OriginalWriterTransaction.ActualExit awaitActualExit() throws IOException, InterruptedException {
            return actual.awaitActualExit();
        }
    }

    @Test void oneActualColdQualificationFitsTheOriginalProfileAtTheComplete64KiBFrameBoundary() throws Exception {
        var fixture = ClosedAdoptionTransactionTest.fixture();
        var settings = ClosedAdoptionTransactionTest.settings(fixture);
        var committed = OriginalWriterTransaction.execute(fixture.target(),fixture::material,
                ignored -> WindowsFileWriterSession.start(settings,WindowsFileWriterSession.Mode.WRITER));
        var prepared = ClosedColdInputsConsumer.prepare(fixture::material,committed,fixture::canonical);
        var basis = ClosedAdoptionTransactionTest.publish(fixture.root().resolve("legacy-cold-basis.json"),prepared.basisBytes());
        var qualification = ClosedAdoptionTransactionTest.publish(fixture.root().resolve("legacy-cold-qualification.json"),
                prepared.qualificationBytes(basis.reference()));
        AtomicReference<CompleteQualifiedFrame> transported = new AtomicReference<>();
        try (var authority = ClosedInputsSessionAuthority.open(fixture::material,committed,fixture::canonical,
                basis,qualification,settings.leaseDeadline())) {
            var consumed = OriginalColdConsumerSession.runOperation(authority,new OriginalColdConsumerSession.ColdInputs(),() -> {
                var process = WindowsFileWriterSession.start(settings,WindowsFileWriterSession.Mode.COLD_CONSUMER);
                var wrapped = new CompleteQualifiedFrame(process); transported.set(wrapped); return wrapped;
            });
            var wrapped = transported.get(); assertNotNull(wrapped);
            assertEquals(1,wrapped.initialRequests,"one original initial request");
            assertEquals(1,wrapped.qualifiedReplies,"formal COLD_INPUTS must not repeat the same legal Java qualification");
            assertTrue(wrapped.producedReplyBytes > 0 && wrapped.producedReplyBytes <= RecoveryEvidence.MAX_BYTES,
                    "actual Java producer bytes remain separately measured; only legal transport whitespace completes the frame");
            assertEquals(131_074L,WindowsFileWriterSession.MAX_COLD_CONSUMER_STREAM_BYTES);
            Path request = coldRequest(fixture.root());
            byte[] sent = bounded(request,WindowsFileWriterSession.MAX_COLD_CONSUMER_STREAM_BYTES);
            int first = newline(sent,0), second = newline(sent,first+1);
            assertTrue(first > 0);
            assertEquals(RecoveryEvidence.MAX_BYTES,second-first-1,"complete legal qualified response frame");
            assertEquals(sent.length-1,second,"no third outgoing frame or hidden retry");
            assertTrue(sent.length <= WindowsFileWriterSession.MAX_COLD_CONSUMER_STREAM_BYTES,
                    "initial request plus complete legal reply fit the unchanged cumulative profile");
            byte[] observed = bounded(wrapped.actual.stdoutPath(),WindowsFileWriterSession.MAX_COLD_CONSUMER_STREAM_BYTES);
            int callbackEnd = newline(observed,0), terminalEnd = newline(observed,callbackEnd+1);
            assertTrue(callbackEnd > 0);
            assertEquals(observed.length-1,terminalEnd,"one actual callback and one complete terminal, without unread output");
            assertArrayEquals(Arrays.copyOfRange(observed,callbackEnd+1,terminalEnd),consumed.originalConsumerReceipt(),
                    "the accepted terminal retains its complete original bytes");
            var terminal = StrictJson.parse(consumed.originalConsumerReceipt(),OriginalWriterTransaction.MAX_PROTOCOL_BYTES);
            assertEquals("COLD_INPUTS",terminal.get("operation").textValue());
            assertEquals(0,terminal.get("new_game_day_credit").longValue());
            assertFalse(terminal.get("grants_new_warm_attachment").booleanValue());
            assertTrue(consumed.processExit().kernelExitObserved()); assertEquals(0,consumed.processExit().exitCode());
            var actual = wrapped.actual.actualCommandResult().orElseThrow();
            assertTrue(actual.passed()); assertEquals(0,actual.accounting().activeProcesses());
            var nativeTerminal = StrictJson.parse(bounded(wrapped.actual.terminalPath(),RecoveryEvidence.MAX_BYTES));
            assertEquals("COLD_CONSUMER",nativeTerminal.get("protocol_profile").textValue());
            assertEquals(131_074L,nativeTerminal.get("protocol_stream_limit_bytes").longValue());
        }
    }

    private static int newline(byte[] bytes, int start) {
        for (int index = start; index < bytes.length; index++) { if (bytes[index] == '\n') { return index; } }
        throw new AssertionError("complete original transport newline required");
    }
    private static Path coldRequest(Path root) throws IOException {
        try (var entries = Files.list(root)) {
            var requests = entries.filter(path -> path.getFileName().toString().startsWith("closed-partial-cold_consumer-")
                    && path.getFileName().toString().endsWith(".request.jsonl")).limit(2).toList();
            assertEquals(1,requests.size()); return requests.get(0);
        }
    }
    private static byte[] bounded(Path path, long maximum) throws IOException {
        assertTrue(Files.size(path) <= maximum,"complete original file remains within its unchanged profile");
        try (var input = Files.newInputStream(path)) {
            byte[] raw = input.readNBytes(Math.toIntExact(maximum+1));
            assertTrue(raw.length <= maximum); return raw;
        }
    }
}
