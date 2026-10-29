package org.xar.ck3.control.wave2.runtime.clockreader;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.time.Instant;
import java.time.format.DateTimeParseException;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.AttemptFingerprint;
import org.xar.ck3.control.reconciliation.LateOutcome.Attempt;
import org.xar.ck3.control.reconciliation.LateOutcome.ContentEvidenceRef;
import org.xar.ck3.control.reconciliation.LateOutcome.Evidence;
import org.xar.ck3.control.reconciliation.LateOutcome.ProcessIdentity;
import org.xar.ck3.control.reconciliation.LateOutcome.ReadKind;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderPorts.ReadCommand;

/** Versioned mechanical transport wrapper; no source-success or continuation-authority flag. */
public final class ClockQueueProtocol {
    public static final int CONTROL_BYTES = 16_384;
    public record Artifact(String relativePath, long bytes, String sha256) {
        public Artifact {
            StrictJson.require(relativePath != null && relativePath.matches("[A-Za-z0-9_./-]+")
                    && !Path.of(relativePath).isAbsolute() && !relativePath.startsWith("/")
                    && !relativePath.contains("//") && !java.util.List.of(relativePath.split("/")).contains(".."), "confined portable artifact path");
            StrictJson.safe(bytes, 1); StrictJson.require(bytes <= 32 * 1024 * 1024, "bounded original artifact");
            ClockPinnedFiles.digest(sha256);
        }
    }
    public record Reply(long sequence, Artifact originalRow, Artifact guardBefore, Artifact guardAfter) {
        public Reply {
            StrictJson.safe(sequence, 1); java.util.Objects.requireNonNull(originalRow);
            java.util.Objects.requireNonNull(guardBefore); java.util.Objects.requireNonNull(guardAfter);
        }
    }
    /** Exact existing CHANNEL.json fields. Parsing and construction confer no source qualification. */
    public record Channel(String machineId, String sessionId, String attemptSha256, String sourceClosureSha256,
                          ProcessIdentity game, ProcessIdentity queue, ProcessIdentity application, Instant leaseDeadline) {
        public Channel {
            StrictJson.text(machineId); StrictJson.text(sessionId);
            ClockPinnedFiles.digest(attemptSha256); ClockPinnedFiles.digest(sourceClosureSha256);
            Objects.requireNonNull(game); Objects.requireNonNull(queue); Objects.requireNonNull(application);
            Objects.requireNonNull(leaseDeadline);
        }
    }
    /** Exact existing COMPLETED receipt; observed times are distinct from claimed native times. */
    public record Collected(String attemptSha256, String ticket, long sequence, String replySha256,
                            long receivedElapsedMillis, Instant observedAt, CrossJsDecimalUInt64 readerWin32UptimeMillis) {
        public Collected {
            ClockPinnedFiles.digest(attemptSha256); ClockPinnedFiles.digest(replySha256);
            StrictJson.require(ticket != null && ticket.matches("[0-9a-f]{32}"), "canonical completion ticket");
            StrictJson.safe(sequence, 1); StrictJson.safe(receivedElapsedMillis, 0);
            Objects.requireNonNull(observedAt); Objects.requireNonNull(readerWin32UptimeMillis);
        }
        public Evidence evidence(Attempt attempt, Artifact originalRow) {
            requireAttempt(attemptSha256, attempt);
            StrictJson.require(sequence > attempt.original().autoSequence(), "collected read follows original failure");
            return new Evidence(attempt.scope(), attempt.scope(), sequence,
                    new ContentEvidenceRef(originalRow.sha256(), originalRow.bytes(), originalRow.relativePath()),
                    receivedElapsedMillis, observedAt, readerWin32UptimeMillis);
        }
    }
    private static final Set<String> REPLY = Set.of("schema", "ticket", "read_kind", "attempt_sha256", "session_id",
            "source_closure_sha256", "original_auto_sequence", "original_failure_sha256", "read_sequence",
            "original_row", "guard_before", "guard_after");
    private static final Set<String> ARTIFACT = Set.of("path", "bytes", "sha256");
    private static final Set<String> REQUEST = Set.of("schema", "ticket", "read_kind", "attempt_sha256", "session_id",
            "source_closure_sha256", "original_auto_sequence", "original_failure_sha256", "hard_deadline_utc",
            "remaining_millis", "maximum_native_payload_bytes", "maximum_original_row_bytes");
    private static final Set<String> CHANNEL = Set.of("schema", "machine_id", "session_id", "attempt_sha256",
            "source_closure_sha256", "game_pid", "game_creation_filetime", "queue_pid", "queue_creation_filetime",
            "application_pid", "application_creation_filetime", "lease_deadline_utc");
    private static final Set<String> COLLECTED = Set.of("schema", "attempt_sha256", "ticket", "sequence", "reply_sha256",
            "received_elapsed_millis", "observed_at_utc", "reader_win32_uptime_millis");
    private ClockQueueProtocol() { }
    public static byte[] request(ReadCommand command) {
        ObjectNode row = StrictJson.object(); row.put("schema", "xar.clock-fixed-read-request/v1");
        row.put("ticket", command.ticket()); row.put("read_kind", command.kind().name());
        row.put("attempt_sha256", AttemptFingerprint.sha256(command.attempt())); row.put("session_id", command.attempt().scope().sessionId());
        row.put("source_closure_sha256", command.attempt().scope().source().closureSha256());
        row.put("original_auto_sequence", command.attempt().original().autoSequence());
        row.put("original_failure_sha256", command.attempt().original().receipt().sha256());
        row.put("hard_deadline_utc", command.hardDeadline().toString()); row.put("remaining_millis", command.remainingMillis());
        row.put("maximum_native_payload_bytes", command.maximumRawReplyBytes()); row.put("maximum_original_row_bytes", 32 * 1024 * 1024);
        return StrictJson.canonical(row, CONTROL_BYTES);
    }
    public static Reply reply(byte[] raw, ReadCommand expected) {
        StrictJson.require(raw != null && raw.length <= CONTROL_BYTES, "bounded reply wrapper");
        ObjectNode row = StrictJson.object(StrictJson.parse(raw), REPLY);
        StrictJson.require("xar.clock-fixed-read-reply/v1".equals(StrictJson.text(row.get("schema"))), "fixed read reply schema");
        StrictJson.require(expected.ticket().equals(StrictJson.text(row.get("ticket")))
                && expected.kind().name().equals(StrictJson.text(row.get("read_kind")))
                && AttemptFingerprint.sha256(expected.attempt()).equals(StrictJson.text(row.get("attempt_sha256")))
                && expected.attempt().scope().sessionId().equals(StrictJson.text(row.get("session_id")))
                && expected.attempt().scope().source().closureSha256().equals(StrictJson.text(row.get("source_closure_sha256")))
                && expected.attempt().original().autoSequence() == StrictJson.integer(row.get("original_auto_sequence"), 1, StrictJson.MAX_SAFE_INTEGER)
                && expected.attempt().original().receipt().sha256().equals(StrictJson.text(row.get("original_failure_sha256"))), "reply changed original session/source/request binding");
        long sequence = StrictJson.integer(row.get("read_sequence"), 1, StrictJson.MAX_SAFE_INTEGER);
        StrictJson.require(sequence > expected.attempt().original().autoSequence(), "new read sequence follows original failure");
        return new Reply(sequence, artifact(row.get("original_row")), artifact(row.get("guard_before")), artifact(row.get("guard_after")));
    }
    /** Producer for the same reply contract consumed above; the original Queue still owns publication. */
    public static byte[] reply(Reply reply, ReadCommand command) {
        ObjectNode row = StrictJson.object(StrictJson.parse(request(command)), REQUEST);
        for (String key : Set.of("hard_deadline_utc", "remaining_millis", "maximum_native_payload_bytes", "maximum_original_row_bytes")) { row.remove(key); }
        row.put("schema", "xar.clock-fixed-read-reply/v1"); row.put("read_sequence", reply.sequence());
        row.set("original_row", artifact(reply.originalRow())); row.set("guard_before", artifact(reply.guardBefore()));
        row.set("guard_after", artifact(reply.guardAfter()));
        byte[] raw = StrictJson.canonical(row, CONTROL_BYTES);
        reply(raw, command); // Producer and every consumer enforce identical source/sequence constraints.
        return raw;
    }
    public static ReadCommand preservedRequest(byte[] raw, Attempt expected) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw, CONTROL_BYTES), REQUEST);
        StrictJson.require("xar.clock-fixed-read-request/v1".equals(StrictJson.text(row.get("schema")))
                && AttemptFingerprint.sha256(expected).equals(StrictJson.text(row.get("attempt_sha256")))
                && expected.scope().sessionId().equals(StrictJson.text(row.get("session_id")))
                && expected.scope().source().closureSha256().equals(StrictJson.text(row.get("source_closure_sha256")))
                && expected.original().autoSequence() == StrictJson.integer(row.get("original_auto_sequence"), 1, StrictJson.MAX_SAFE_INTEGER)
                && expected.original().receipt().sha256().equals(StrictJson.text(row.get("original_failure_sha256")))
                && StrictJson.integer(row.get("maximum_original_row_bytes"), 32 * 1024 * 1024, 32 * 1024 * 1024) == 32 * 1024 * 1024,
                "preserved request belongs to this exact admitted attempt");
        ReadKind kind;
        try { kind = ReadKind.valueOf(StrictJson.text(row.get("read_kind"))); }
        catch (IllegalArgumentException error) { throw new ContractViolationException("fixed read kind", error); }
        String utc = StrictJson.text(row.get("hard_deadline_utc")); StrictJson.utc(utc);
        return new ReadCommand(expected, kind, StrictJson.text(row.get("ticket")),
                (int) StrictJson.integer(row.get("maximum_native_payload_bytes"), 1, 8 * 1024 * 1024),
                StrictJson.integer(row.get("remaining_millis"), 1, 3_600_000), Instant.parse(utc));
    }
    public static Channel channel(byte[] raw, Attempt expected) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw, CONTROL_BYTES), CHANNEL); var scope = expected.scope();
        StrictJson.require("xar.clock-fixed-reader-channel/v1".equals(StrictJson.text(row.get("schema")))
                && scope.machineId().equals(StrictJson.text(row.get("machine_id")))
                && scope.sessionId().equals(StrictJson.text(row.get("session_id")))
                && AttemptFingerprint.sha256(expected).equals(StrictJson.text(row.get("attempt_sha256")))
                && scope.source().closureSha256().equals(StrictJson.text(row.get("source_closure_sha256"))), "channel source/session binding");
        ProcessIdentity game = identity(row, "game"), queue = identity(row, "queue"), application = identity(row, "application");
        StrictJson.require(game.equals(scope.game()) && queue.equals(scope.queue()) && application.equals(scope.application()),
                "channel process identity mismatch");
        return new Channel(StrictJson.text(row.get("machine_id")), StrictJson.text(row.get("session_id")),
                StrictJson.text(row.get("attempt_sha256")), StrictJson.text(row.get("source_closure_sha256")),
                game, queue, application, instant(row.get("lease_deadline_utc")));
    }
    public static byte[] channel(Channel channel, Attempt expected) {
        ObjectNode row = StrictJson.object(); row.put("schema", "xar.clock-fixed-reader-channel/v1");
        row.put("machine_id", channel.machineId()); row.put("session_id", channel.sessionId());
        row.put("attempt_sha256", channel.attemptSha256()); row.put("source_closure_sha256", channel.sourceClosureSha256());
        identity(row, "game", channel.game()); identity(row, "queue", channel.queue()); identity(row, "application", channel.application());
        row.put("lease_deadline_utc", channel.leaseDeadline().toString());
        byte[] raw = StrictJson.canonical(row, CONTROL_BYTES); channel(raw, expected); return raw;
    }
    public static Collected collected(byte[] raw, Attempt expected) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw, CONTROL_BYTES), COLLECTED);
        StrictJson.require("xar.clock-fixed-read-collected/v1".equals(StrictJson.text(row.get("schema"))), "collected receipt schema");
        String attemptSha256 = StrictJson.text(row.get("attempt_sha256")); requireAttempt(attemptSha256, expected);
        long sequence = StrictJson.integer(row.get("sequence"), 1, StrictJson.MAX_SAFE_INTEGER);
        StrictJson.require(sequence > expected.original().autoSequence(), "collected read follows original failure");
        return new Collected(attemptSha256, StrictJson.text(row.get("ticket")), sequence, StrictJson.text(row.get("reply_sha256")),
                StrictJson.integer(row.get("received_elapsed_millis"), 0, StrictJson.MAX_SAFE_INTEGER), instant(row.get("observed_at_utc")),
                new CrossJsDecimalUInt64(StrictJson.text(row.get("reader_win32_uptime_millis"))));
    }
    public static byte[] collected(Collected collected, Attempt expected) {
        ObjectNode row = StrictJson.object(); row.put("schema", "xar.clock-fixed-read-collected/v1");
        row.put("attempt_sha256", collected.attemptSha256()); row.put("ticket", collected.ticket()); row.put("sequence", collected.sequence());
        row.put("reply_sha256", collected.replySha256()); row.put("received_elapsed_millis", collected.receivedElapsedMillis());
        row.put("observed_at_utc", collected.observedAt().toString()); row.put("reader_win32_uptime_millis", collected.readerWin32UptimeMillis().decimal());
        byte[] raw = StrictJson.canonical(row, CONTROL_BYTES); collected(raw, expected); return raw;
    }
    private static void requireAttempt(String fingerprint, Attempt expected) {
        StrictJson.require(AttemptFingerprint.sha256(expected).equals(fingerprint), "collected receipt belongs to another attempt");
    }
    private static Instant instant(JsonNode value) {
        String text = StrictJson.text(value); StrictJson.utc(text);
        try { return Instant.parse(text); }
        catch (DateTimeParseException error) { throw new ContractViolationException("clock receipt UTC timestamp", error); }
    }
    private static ProcessIdentity identity(JsonNode row, String prefix) {
        return new ProcessIdentity(StrictJson.integer(row.get(prefix + "_pid"), 1, 0xffff_ffffL),
                new CrossJsDecimalUInt64(StrictJson.text(row.get(prefix + "_creation_filetime"))));
    }
    private static void identity(ObjectNode row, String prefix, ProcessIdentity identity) {
        row.put(prefix + "_pid", identity.pid()); row.put(prefix + "_creation_filetime", identity.creationFiletime().decimal());
    }
    private static Artifact artifact(JsonNode value) {
        JsonNode row = StrictJson.object(value, ARTIFACT);
        return new Artifact(StrictJson.text(row.get("path")), StrictJson.integer(row.get("bytes"), 1, 32 * 1024 * 1024), StrictJson.text(row.get("sha256")));
    }
    private static ObjectNode artifact(Artifact artifact) {
        ObjectNode row = StrictJson.object(); row.put("path", artifact.relativePath()); row.put("bytes", artifact.bytes()); row.put("sha256", artifact.sha256()); return row;
    }
}
