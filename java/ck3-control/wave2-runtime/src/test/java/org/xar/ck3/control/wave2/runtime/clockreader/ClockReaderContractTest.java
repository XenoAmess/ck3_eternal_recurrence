package org.xar.ck3.control.wave2.runtime.clockreader;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.AssessmentCodec;
import org.xar.ck3.control.reconciliation.AttemptFingerprint;
import org.xar.ck3.control.reconciliation.LateOutcome.Outcome;
import org.xar.ck3.control.reconciliation.LateOutcome.Read;
import org.xar.ck3.control.reconciliation.LateOutcome.ReadKind;
import org.xar.ck3.control.reconciliation.LateOutcome.SemanticRead;
import org.xar.ck3.control.reconciliation.LateOutcome.StatusRead;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockQueueProtocol.Channel;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockQueueProtocol.Collected;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderPorts.ReadCommand;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderPorts.ReadLedger;
import static org.junit.jupiter.api.Assertions.*;

/** Actual file consumers with synthetic Queue/native facts; no child process, SDK or Game is started. */
class ClockReaderContractTest {
    @TempDir Path temporary;
    private ClockReaderTest.Fixture fixture(String name) throws IOException {
        ClockReaderTest support = new ClockReaderTest();
        support.temporary = Files.createDirectory(temporary.resolve(name));
        return support.new Fixture();
    }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static String text(byte[] value) { return new String(value, StandardCharsets.UTF_8); }
    private static ObjectNode object(byte[] raw) { return (ObjectNode) StrictJson.parse(raw); }
    private static ReadCommand command(ClockReaderTest.Fixture fixture, ReadKind kind, char ticket) {
        return new ReadCommand(fixture.attempt, kind, String.valueOf(ticket).repeat(32), 8192, 1000,
                fixture.time.base.plusSeconds(1));
    }

    @Test void actualFileConsumersRehydrateTypedReceiptsAndBothNativeBodiesBeforePlannerProposal() throws Exception {
        var fixture = fixture("roundtrip");
        Channel channel = ClockQueueProtocol.channel(Files.readAllBytes(fixture.manifest.path()), fixture.attempt);
        assertEquals(channel, ClockQueueProtocol.channel(ClockQueueProtocol.channel(channel, fixture.attempt), fixture.attempt));
        assertEquals(fixture.attempt.scope().game(), channel.game());
        try (var reader = fixture.open()) {
            var application = new ClockReaderApplication(reader, fixture.time);
            var result = application.run(fixture.attempt, fixture.budget(), new ReadLedger(List.of()));
            assertEquals(Outcome.PROPOSED, result.assessment().outcome());
            var retainedCallback = application.originalWriterRecheck(result);
            assertEquals(List.of(ReadKind.CURRENT_SENTINEL_STATUS, ReadKind.CURRENT_SEMANTIC_FRAME,
                    ReadKind.CURRENT_SENTINEL_STATUS), result.ledger().reads().stream().map(Read::kind).toList());
            assertInstanceOf(StatusRead.class, result.ledger().reads().get(0));
            assertInstanceOf(SemanticRead.class, result.ledger().reads().get(1));
            for (Read read : result.ledger().reads()) {
                int matchingReceipts = 0;
                try (var files = Files.newDirectoryStream(fixture.root.resolve("receipts"), "COMPLETED-*.json")) {
                    for (Path path : files) {
                        Collected receipt = ClockQueueProtocol.collected(Files.readAllBytes(path), fixture.attempt);
                        if (receipt.sequence() != read.evidence().sequence()) { continue; }
                        matchingReceipts++;
                        byte[] intent = Files.readAllBytes(fixture.root.resolve("receipts/INTENT-" + receipt.ticket() + ".json"));
                        ReadCommand request = ClockQueueProtocol.preservedRequest(intent, fixture.attempt);
                        assertEquals(request, ClockQueueProtocol.preservedRequest(ClockQueueProtocol.request(request), fixture.attempt));
                        byte[] rawReply = Files.readAllBytes(fixture.root.resolve("replies/" + receipt.ticket() + ".json"));
                        var reply = ClockQueueProtocol.reply(rawReply, request);
                        assertEquals(reply, ClockQueueProtocol.reply(ClockQueueProtocol.reply(reply, request), request));
                        assertEquals(read.evidence(), receipt.evidence(fixture.attempt, reply.originalRow()));
                        byte[] encoded = ClockQueueProtocol.collected(receipt, fixture.attempt);
                        assertEquals(receipt, ClockQueueProtocol.collected(encoded, fixture.attempt));
                        Files.write(path, encoded); // Restart/history consumer reads the actual encoded receipt bytes.
                    }
                }
                assertEquals(1, matchingReceipts, "each actual read must rebind to exactly one preserved completion");
            }
            reader.verifyCompleteLedger(fixture.attempt, result.ledger());
            assertEquals(result, retainedCallback.recheck());
            assertEquals(3, fixture.served.size(), "retained callback consumes the same typed receipts without a new read");
            assertEquals(result.assessment(), AssessmentCodec.decode(AssessmentCodec.encode(fixture.attempt, result.assessment()), fixture.attempt));
            assertEquals(0, result.originalCredit()); assertTrue(result.neverReplay());
        }
    }

    private record NativeField(ReadKind kind, String key, String validToken) { }
    @Test void malformedOriginalNativeTokensReachActualFileDecoderWithMatchingArtifactDigests() throws Exception {
        int index = 0;
        for (NativeField field : List.of(new NativeField(ReadKind.CURRENT_SENTINEL_STATUS, "generation", "1"),
                new NativeField(ReadKind.CURRENT_SEMANTIC_FRAME, "native_revision", "3"))) {
            for (String token : List.of("true", "1.0", "1e0", "\"1\"", "null", "MISSING")) {
                var fixture = fixture("native-" + index++);
                fixture.time.onWait = () -> {
                    fixture.serve();
                    mutateOriginals(fixture, raw -> {
                        String present = "\"" + field.key() + "\":" + field.validToken() + ",";
                        String replacement = token.equals("MISSING") ? "" : "\"" + field.key() + "\":" + token + ",";
                        assertTrue(raw.contains(present), "test must reach the actual raw native token");
                        return raw.replace(present, replacement);
                    });
                };
                try (var reader = fixture.open()) {
                    IOException error = assertThrows(IOException.class, () -> reader.read(command(fixture, field.kind(), 'a')));
                    assertInstanceOf(ContractViolationException.class, error.getCause());
                    assertTrue(error.getMessage().contains("fixed read contract rejected"));
                    assertTrue(Files.exists(fixture.root.resolve("ACTIVE-READ.json")));
                    assertEquals(0, reader.completedReadCount(fixture.attempt));
                    assertThrows(IOException.class, () -> reader.read(command(fixture, field.kind(), 'b')));
                    assertEquals(1, fixture.served.size());
                }
            }
        }
    }

    @FunctionalInterface private interface RawMutation { String apply(String raw); }
    private static void mutateOriginals(ClockReaderTest.Fixture fixture, RawMutation mutation) throws IOException {
        try (var files = Files.newDirectoryStream(fixture.root.resolve("replies"), "*.json")) {
            for (Path replyPath : files) {
                ObjectNode reply = object(Files.readAllBytes(replyPath));
                ObjectNode artifact = (ObjectNode) reply.get("original_row");
                Path rowPath = fixture.root.resolve(artifact.get("path").textValue());
                byte[] changed = bytes(mutation.apply(text(Files.readAllBytes(rowPath))));
                Files.write(rowPath, changed); artifact.put("bytes", changed.length); artifact.put("sha256", ClockPinnedFiles.hash(changed));
                Files.write(replyPath, bytes(reply.toString()));
            }
        }
    }

    @Test void mismatchedTextBodyReachesActualFileDecoderInsteadOfBecomingNativeEvidence() throws Exception {
        var fixture = fixture("two-bodies");
        fixture.time.onWait = () -> {
            fixture.serve();
            mutateOriginals(fixture, raw -> {
                ObjectNode row = object(bytes(raw));
                ObjectNode content = (ObjectNode) row.at("/result/content/0");
                String original = content.get("text").textValue();
                String changed = original.replace("\"generation\":1,", "\"generation\":2,");
                assertNotEquals(original, changed); content.put("text", changed); return row.toString();
            });
        };
        try (var reader = fixture.open()) {
            IOException error = assertThrows(IOException.class, () -> reader.read(command(fixture, ReadKind.CURRENT_SENTINEL_STATUS, 'c')));
            assertInstanceOf(ContractViolationException.class, error.getCause());
            assertTrue(error.getCause().getMessage().contains("MCP text and structured sentinel facts disagree"));
            assertTrue(Files.exists(fixture.root.resolve("ACTIVE-READ.json"))); assertEquals(0, reader.completedReadCount(fixture.attempt));
        }
    }

    @Test void malformedCollectedTokensAreRejectedByTheActualRestartHistoryConsumer() throws Exception {
        int index = 0;
        for (String token : List.of("true", "1.0", "1e0", "null", "MISSING", "RENAMED")) {
            var fixture = fixture("collected-" + index++); ReadLedger ledger;
            try (var reader = fixture.open()) {
                var application = new ClockReaderApplication(reader, fixture.time);
                var result = application.run(fixture.attempt, fixture.budget(), new ReadLedger(List.of()));
                assertEquals(Outcome.PROPOSED, result.assessment().outcome()); ledger = result.ledger();
                var retainedCallback = application.originalWriterRecheck(result);
                Read actual = ledger.reads().get(0); Path path = null;
                try (var files = Files.newDirectoryStream(fixture.root.resolve("receipts"), "COMPLETED-*.json")) {
                    for (Path candidate : files) {
                        if (ClockQueueProtocol.collected(Files.readAllBytes(candidate), fixture.attempt).sequence() == actual.evidence().sequence()) {
                            assertNull(path); path = candidate;
                        }
                    }
                }
                assertNotNull(path);
                String original = text(Files.readAllBytes(path));
                String present = "\"received_elapsed_millis\":" + actual.evidence().receivedElapsedMillis() + ",";
                String replacement = token.equals("MISSING") ? "" : token.equals("RENAMED") ? "\"elapsed_ms\":1,"
                        : "\"received_elapsed_millis\":" + token + ",";
                assertTrue(original.contains(present)); Files.write(path, bytes(original.replace(present, replacement)));
                IOException failure = assertThrows(IOException.class, retainedCallback::recheck);
                assertInstanceOf(ContractViolationException.class, failure.getCause());
                assertEquals(3, fixture.served.size(), "a failed retained callback cannot request replacement observations");
            }
            try (var restarted = fixture.open()) {
                IOException error = assertThrows(IOException.class, () -> restarted.verifyCompleteLedger(fixture.attempt, ledger));
                assertInstanceOf(ContractViolationException.class, error.getCause());
                assertEquals(3, fixture.served.size());
            }
        }
    }

    @Test void collectedDecimalUptimeRoundTripKeepsEveryUInt64DigitAndRejectsNumericAlias() throws Exception {
        var fixture = fixture("decimal");
        Collected value = new Collected(AttemptFingerprint.sha256(fixture.attempt), "e".repeat(32), 11559,
                "a".repeat(64), 1, Instant.parse("2026-10-22T14:00:00Z"), new CrossJsDecimalUInt64("18446744073709551615"));
        byte[] raw = ClockQueueProtocol.collected(value, fixture.attempt);
        assertEquals(value, ClockQueueProtocol.collected(raw, fixture.attempt));
        byte[] alias = bytes(text(raw).replace("\"18446744073709551615\"", "18446744073709551615"));
        assertThrows(ContractViolationException.class, () -> ClockQueueProtocol.collected(alias, fixture.attempt));
        ObjectNode missing = object(raw); missing.remove("observed_at_utc");
        assertThrows(ContractViolationException.class, () -> ClockQueueProtocol.collected(bytes(missing.toString()), fixture.attempt));
        ObjectNode unknown = object(raw); unknown.put("green", true);
        assertThrows(ContractViolationException.class, () -> ClockQueueProtocol.collected(bytes(unknown.toString()), fixture.attempt));
    }

    @Test void malformedChannelIdentityIsRejectedAtTheMeasuredFileConstructor() throws Exception {
        int index = 0;
        for (String token : List.of("true", "12345.0", "1e0", "null", "MISSING")) {
            var fixture = fixture("channel-" + index++);
            String original = text(Files.readAllBytes(fixture.manifest.path()));
            String present = "\"game_pid\":12345,";
            assertTrue(original.contains(present));
            byte[] changed = bytes(original.replace(present, token.equals("MISSING") ? "" : "\"game_pid\":" + token + ","));
            Files.write(fixture.manifest.path(), changed);
            var measured = ClockPinnedFiles.capture(fixture.manifest.path(), ClockPinnedFiles.hash(changed), ClockQueueProtocol.CONTROL_BYTES);
            assertThrows(ContractViolationException.class, () -> new OriginalQueueFileReader(fixture.root.toAbsolutePath(), measured,
                    fixture.attempt, fixture.guard, fixture.time));
            assertTrue(fixture.served.isEmpty()); assertFalse(Files.exists(fixture.root.resolve("ACTIVE-READ.json")));
        }
    }
}
