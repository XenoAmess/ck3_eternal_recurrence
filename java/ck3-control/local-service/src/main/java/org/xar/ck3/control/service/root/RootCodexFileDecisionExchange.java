package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.TimeUnit;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * One local Codex decision for an already archived, exact planner input. This is transport only:
 * the ordinary selector still parses the chosen original proposal and the controller still owns
 * every command, guard, once-dispatch and postcondition. No HTTP or game operation exists here.
 */
final class RootCodexFileDecisionExchange {
    static final String REQUEST_SCHEMA = CodexSessionDecisionFiles.REQUEST_SCHEMA;
    static final String RESPONSE_SCHEMA = "xar.ordinary-codex-file-response/v1";
    static final String ARCHIVED_SCHEMA = "xar.ordinary-codex-file-archived/v2";
    static final int MAX_ENTRIES = 32;
    static final int MAX_REQUEST_BYTES = 16 * 1024;
    static final int MAX_RESPONSE_BYTES = 256 * 1024;
    static final int MAX_ACK_BYTES = 4 * 1024;
    private final Path root;
    private final Clock clock;

    static final class Reply implements AutoCloseable {
        private final RootCodexFileDecisionExchange owner;
        private final Path directory;
        private final String requestId;
        private final String requestSha256;
        private final CodexDecisionFilePins.Held requestHeld, responseHeld;
        private boolean closed;
        private final byte[] requestRaw;
        private final byte[] raw;
        private final String content;
        private final String failure;
        private final long totalMs;
        private Reply(RootCodexFileDecisionExchange owner, Path directory, String requestId, String requestSha256,
                byte[] requestRaw, CodexDecisionFilePins.Held requestHeld, CodexDecisionFilePins.Held responseHeld,
                byte[] raw, String content, String failure, long totalMs) {
            this.owner = owner; this.directory = directory; this.requestId = requestId;
            this.requestSha256 = requestSha256; this.requestRaw = requestRaw.clone();
            this.requestHeld = requestHeld; this.responseHeld = responseHeld;
            this.raw = raw.clone(); this.content = content;
            this.failure = failure; this.totalMs = totalMs;
        }
        JsonNode requestPin() { return requestHeld == null ? com.fasterxml.jackson.databind.node.NullNode.getInstance() : requestHeld.original().pin().toJson(); }
        JsonNode responsePin() { return responseHeld == null ? com.fasterxml.jackson.databind.node.NullNode.getInstance() : responseHeld.original().pin().toJson(); }
        void verifyHeld() throws IOException {
            if (closed) throw new IOException("Codex reply custody already closed");
            if (requestHeld != null) requestHeld.verify();
            if (responseHeld != null) responseHeld.verify();
        }
        @Override public void close() throws IOException {
            if (closed) return;
            closed = true; IOException failure = null;
            if (responseHeld != null) try { responseHeld.close(); } catch (IOException problem) { failure = problem; }
            if (requestHeld != null) try { requestHeld.close(); } catch (IOException problem) {
                if (failure == null) failure = problem; else failure.addSuppressed(problem);
            }
            if (failure != null) throw failure;
        }
        byte[] requestRaw() { return requestRaw.clone(); }
        byte[] raw() { return raw.clone(); }
        String content() { return content; }
        String failure() { return failure; }
        long totalMs() { return totalMs; }
        boolean complete() { return failure.isEmpty() && !content.isEmpty(); }
    }

    RootCodexFileDecisionExchange(Path directory, Clock clock) {
        root = Objects.requireNonNull(directory).toAbsolutePath().normalize();
        this.clock = Objects.requireNonNull(clock);
    }

    /** The payload is already in the ordinary archive; the queue never duplicates its 64 MiB body. */
    synchronized Reply exchange(ExactRef payload, ExactRef originalCommand, String machineId, String proposalId, String bodySha256,
            JsonNode before, Instant deadline, long nanoEnd) {
        Objects.requireNonNull(payload); Objects.requireNonNull(originalCommand);
        StrictJson.require(originalCommand.sha256().equals(bodySha256), "exact archived original command required");
        StrictJson.text(machineId); StrictJson.text(proposalId);
        StrictJson.require(bodySha256.matches("[0-9a-f]{64}"), "exact original proposal body required");
        Objects.requireNonNull(before); Objects.requireNonNull(deadline);
        long started = System.nanoTime();
        Path directory = null;
        String id = "codex-" + UUID.randomUUID(), requestSha256 = "";
        byte[] response = new byte[0], requestBytes = new byte[0];
        CodexDecisionFilePins.Held requestHeld = null, responseHeld = null;
        try {
            requireRemaining(deadline, nanoEnd);
            Files.createDirectories(root);
            makeRoom();
            directory = root.resolve(id);
            Files.createDirectory(directory);
            ObjectNode request = StrictJson.object();
            request.put("schema", REQUEST_SCHEMA); request.put("request_id", id);
            request.put("provider", "codex-session"); request.put("machine_id", machineId);
            request.put("proposal_id", proposalId); request.put("body_sha256", bodySha256);
            request.put("created_at_utc", clock.instant().toString()); request.put("deadline_utc", deadline.toString());
            request.set("before", before); request.set("payload", payload.toJson());
            request.set("original_command", originalCommand.toJson());
            request.put("response_file", directory.resolve("response.json").toString());
            request.put("response_schema", RESPONSE_SCHEMA);
            request.put("selection_contract", CodexSessionDecisionFiles.SELECTION_CONTRACT);
            byte[] bytes = FullJsonTree.encode(request, MAX_REQUEST_BYTES);
            requestBytes = bytes; requestSha256 = ActionCodec.sha256(bytes);
            publish(directory.resolve("request.json"), bytes);
            requestHeld = CodexDecisionFilePins.hold(directory.resolve("request.json"), MAX_REQUEST_BYTES);
            StrictJson.require(requestHeld.original().pin().reference().sha256().equals(requestSha256), "published original request differs");
            emitReady(directory, id, requestSha256, proposalId, deadline, requestHeld.original().pin());
            Path responseFile = directory.resolve("response.json");
            while (true) {
                requireRemaining(deadline, nanoEnd);
                if (Files.isRegularFile(responseFile)) {
                    responseHeld = CodexDecisionFilePins.hold(responseFile, MAX_RESPONSE_BYTES);
                    response = responseHeld.original().bytes();
                    requestHeld.verify();
                    StrictJson.require(requestSha256.equals(ActionCodec.sha256(readBounded(directory.resolve("request.json"), MAX_REQUEST_BYTES))),
                            "original Codex request changed before consumption");
                    JsonNode envelope = FullJsonTree.parse(response, MAX_RESPONSE_BYTES);
                    StrictJson.object(envelope, Set.of("schema", "request_id", "request_sha256", "selection"));
                    StrictJson.require(RESPONSE_SCHEMA.equals(StrictJson.text(envelope.get("schema")))
                            && id.equals(StrictJson.text(envelope.get("request_id")))
                            && requestSha256.equals(StrictJson.text(envelope.get("request_sha256"))),
                            "Codex response belongs to another original request");
                    JsonNode selection = StrictJson.object(envelope.get("selection"),
                            Set.of("decision", "proposal_id", "body_sha256", "reason"));
                    requireRemaining(deadline, nanoEnd);
                    return new Reply(this, directory, id, requestSha256, requestBytes, requestHeld, responseHeld, response,
                            new String(FullJsonTree.encode(selection, MAX_RESPONSE_BYTES), java.nio.charset.StandardCharsets.UTF_8),
                            "", elapsed(started));
                }
                long remaining = remaining(deadline, nanoEnd);
                TimeUnit.NANOSECONDS.sleep(Math.min(100_000_000L, remaining));
            }
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            return new Reply(this, directory, id, requestSha256, requestBytes, requestHeld, responseHeld, response, "", "interrupted", elapsed(started));
        } catch (IOException | RuntimeException failure) {
            return new Reply(this, directory, id, requestSha256, requestBytes, requestHeld, responseHeld, response, "",
                    failure.getClass().getSimpleName() + ":" + String.valueOf(failure.getMessage()), elapsed(started));
        } catch (Error failure) {
            if (responseHeld != null) try { responseHeld.close(); } catch (IOException closing) { failure.addSuppressed(closing); }
            if (requestHeld != null) try { requestHeld.close(); } catch (IOException closing) { failure.addSuppressed(closing); }
            throw failure;
        }
    }

    /** Called only after the ordinary material sink preserved the complete original response attempt. */
    void acknowledge(Reply reply, ExactRef actualAttempt) throws IOException {
        Objects.requireNonNull(reply); Objects.requireNonNull(actualAttempt);
        reply.verifyHeld();
        StrictJson.require(reply.owner == this, "Codex response belongs to another transport instance");
        if (reply.directory == null || !Files.isRegularFile(reply.directory.resolve("request.json"))) return;
        ObjectNode ack = StrictJson.object();
        ack.put("schema", ARCHIVED_SCHEMA); ack.put("request_id", reply.requestId);
        ack.put("request_sha256", reply.requestSha256); ack.put("observed_at_utc", clock.instant().toString());
        ack.set("attempt", actualAttempt.toJson());
        ack.set("request_pin", reply.requestPin()); ack.set("response_pin", reply.responsePin());
        // Attempt material has already been durably accepted by the existing sink. Release before queue reclamation.
        reply.close();
        publish(reply.directory.resolve("archived.json"), FullJsonTree.encode(ack, MAX_ACK_BYTES));
    }

    void archiveExpired(String machine, RootOnlineDecisionSelector.MaterialSink sink, Instant until, long nanoEnd) throws IOException {
        RootExpiredCodexFileEvidence.archive(root, machine, clock, sink, until, nanoEnd);
    }

    private void makeRoom() throws IOException {
        List<Path> entries = new ArrayList<>();
        try (var paths = Files.list(root)) {
            paths.filter(Files::isDirectory).filter(path -> path.getFileName().toString().startsWith("codex-"))
                    .forEach(entries::add);
        }
        entries.sort(Comparator.comparing(path -> path.getFileName().toString()));
        for (Path entry : entries) {
            if (entries.size() < MAX_ENTRIES) return;
            boolean late = Files.isRegularFile(entry.resolve("expired-late.json"));
            boolean expired = late || Files.isRegularFile(entry.resolve("expired.json"));
            Path ackFile = entry.resolve(late ? "expired-late.json" : expired ? "expired.json" : "archived.json");
            if (!Files.isRegularFile(ackFile)) continue;
            JsonNode ack = FullJsonTree.parse(readBounded(ackFile, MAX_ACK_BYTES), MAX_ACK_BYTES);
            byte[] request = readBounded(entry.resolve("request.json"), MAX_REQUEST_BYTES);
            if (!(ARCHIVED_SCHEMA.equals(StrictJson.text(ack.get("schema")))
                    || expired && RootExpiredCodexFileEvidence.RECEIPT_SCHEMA.equals(StrictJson.text(ack.get("schema"))))
                    || !entry.getFileName().toString().equals(StrictJson.text(ack.get("request_id")))
                    || !ActionCodec.sha256(request).equals(StrictJson.text(ack.get("request_sha256")))) continue;
            if (expired) {
                RootExpiredCodexFileEvidence.requireReceipt(ack);
                if (late && !RootExpiredCodexFileEvidence.matches(entry.resolve("expired.json"), ack.get("previous_expired_pin"), MAX_ACK_BYTES)) continue;
                if (clock.instant().isBefore(Instant.parse(StrictJson.text(ack.get("deadline_utc"))))) continue;
                var archived = org.xar.ck3.control.contracts.ExactRef.fromJson(ack.get("evidence"));
                if (!RootExpiredCodexFileEvidence.matches(Path.of(archived.path()), ack.get("evidence_pin"), RootExpiredCodexFileEvidence.MAX_EVIDENCE_BYTES)) continue;
                if (!RootExpiredCodexFileEvidence.matches(entry.resolve("ready.json"), ack.get("ready_pin"), MAX_REQUEST_BYTES)
                        || !RootExpiredCodexFileEvidence.matches(entry.resolve("archived.json"), ack.get("original_ack_pin"), MAX_ACK_BYTES)) continue;
            }
            // Reclaim only exact observed physical files, never a late, oversized or same-byte replacement response.
            if (!ack.hasNonNull("request_pin") || !CodexDecisionFilePins.read(entry.resolve("request.json"), MAX_REQUEST_BYTES).pin()
                    .equals(org.xar.ck3.control.continuity.writer.WriterContracts.Pin.fromJson(ack.get("request_pin")))) continue;
            if (Files.exists(entry.resolve("response.json"))) {
                if (!ack.hasNonNull("response_pin") || !CodexDecisionFilePins.read(entry.resolve("response.json"), MAX_RESPONSE_BYTES).pin()
                        .equals(org.xar.ck3.control.continuity.writer.WriterContracts.Pin.fromJson(ack.get("response_pin")))) continue;
            }
            StrictJson.require(entry.toAbsolutePath().normalize().getParent().equals(root), "owned Codex queue entry required");
            // Only these transport-owned files are reclaimed; an unknown file prevents deleting its directory.
            if (ack.hasNonNull("response_pin")) Files.deleteIfExists(entry.resolve("response.json"));
            Files.deleteIfExists(entry.resolve("ready.json")); Files.deleteIfExists(ackFile);
            if (expired) Files.deleteIfExists(entry.resolve("archived.json"));
            if (late) Files.deleteIfExists(entry.resolve("expired.json"));
            Files.delete(entry.resolve("request.json")); Files.delete(entry);
            entries = new ArrayList<>(entries); entries.remove(entry);
        }
        if (entries.size() >= MAX_ENTRIES) throw new IOException("Codex queue is full of unarchived original requests");
    }

    private static byte[] readBounded(Path file, int maximum) throws IOException {
        try (var input = Files.newInputStream(file)) {
            byte[] bytes = input.readNBytes(maximum + 1);
            if (bytes.length == 0 || bytes.length > maximum) throw new IOException("bounded complete Codex transport material required");
            return bytes;
        }
    }

    private static void publish(Path target, byte[] bytes) throws IOException {
        Path temporary = target.resolveSibling(target.getFileName() + "." + UUID.randomUUID() + ".tmp");
        try {
            Files.write(temporary, bytes, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
            Files.move(temporary, target, StandardCopyOption.ATOMIC_MOVE);
        } finally { Files.deleteIfExists(temporary); }
    }

    private void emitReady(Path directory, String id, String sha, String proposal, Instant deadline, org.xar.ck3.control.continuity.writer.WriterContracts.Pin requestPin) throws IOException {
        ObjectNode event = StrictJson.object(); event.put("schema", "xar.ordinary-codex-file-progress/v1");
        event.put("status", "ORDINARY_CODEX_REQUEST_READY"); event.put("request_id", id);
        event.put("request_sha256", sha); event.put("proposal_id", proposal);
        event.set("request_pin", requestPin.toJson());
        event.put("request_file", directory.resolve("request.json").toString());
        event.put("deadline_utc", deadline.toString());
        byte[] bytes = FullJsonTree.encode(event, MAX_REQUEST_BYTES);
        publish(directory.resolve("ready.json"), bytes);
        synchronized (System.out) { System.out.write(bytes); System.out.write(10); System.out.flush(); }
    }

    private long remaining(Instant deadline, long nanoEnd) {
        return Math.min(Duration.between(clock.instant(), deadline).toNanos(), nanoEnd - System.nanoTime());
    }
    private void requireRemaining(Instant deadline, long nanoEnd) throws IOException {
        if (remaining(deadline, nanoEnd) <= 0) throw new IOException("Codex decision original deadline expired");
    }
    private static long elapsed(long start) { return TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - start); }
}
