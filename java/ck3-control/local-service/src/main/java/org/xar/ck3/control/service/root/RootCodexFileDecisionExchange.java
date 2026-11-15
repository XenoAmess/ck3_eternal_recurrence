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
    static final String REQUEST_SCHEMA = "xar.ordinary-codex-file-request/v1";
    static final String RESPONSE_SCHEMA = "xar.ordinary-codex-file-response/v1";
    static final String ARCHIVED_SCHEMA = "xar.ordinary-codex-file-archived/v1";
    static final int MAX_ENTRIES = 32;
    static final int MAX_REQUEST_BYTES = 16 * 1024;
    static final int MAX_RESPONSE_BYTES = 256 * 1024;
    static final int MAX_ACK_BYTES = 4 * 1024;
    private final Path root;
    private final Clock clock;

    static final class Reply {
        private final RootCodexFileDecisionExchange owner;
        private final Path directory;
        private final String requestId;
        private final String requestSha256;
        private final byte[] raw;
        private final String content;
        private final String failure;
        private final long totalMs;
        private Reply(RootCodexFileDecisionExchange owner, Path directory, String requestId, String requestSha256,
                byte[] raw, String content, String failure, long totalMs) {
            this.owner = owner; this.directory = directory; this.requestId = requestId;
            this.requestSha256 = requestSha256; this.raw = raw.clone(); this.content = content;
            this.failure = failure; this.totalMs = totalMs;
        }
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
    synchronized Reply exchange(ExactRef payload, String machineId, String proposalId, String bodySha256,
            JsonNode before, Instant deadline, long nanoEnd) {
        Objects.requireNonNull(payload); StrictJson.text(machineId); StrictJson.text(proposalId);
        StrictJson.require(bodySha256.matches("[0-9a-f]{64}"), "exact original proposal body required");
        Objects.requireNonNull(before); Objects.requireNonNull(deadline);
        long started = System.nanoTime();
        Path directory = null;
        String id = "codex-" + UUID.randomUUID(), requestSha256 = "";
        byte[] response = new byte[0];
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
            request.put("response_file", directory.resolve("response.json").toString());
            request.put("response_schema", RESPONSE_SCHEMA);
            request.put("selection_contract", "Exactly decision,proposal_id,body_sha256,reason; SELECT_PROPOSAL or WAIT; original IDs only");
            byte[] bytes = FullJsonTree.encode(request, MAX_REQUEST_BYTES);
            requestSha256 = ActionCodec.sha256(bytes);
            publish(directory.resolve("request.json"), bytes);
            emitReady(directory, id, requestSha256, proposalId, deadline);
            Path responseFile = directory.resolve("response.json");
            while (true) {
                requireRemaining(deadline, nanoEnd);
                if (Files.isRegularFile(responseFile)) {
                    response = readBounded(responseFile, MAX_RESPONSE_BYTES);
                    JsonNode envelope = FullJsonTree.parse(response, MAX_RESPONSE_BYTES);
                    StrictJson.object(envelope, Set.of("schema", "request_id", "request_sha256", "selection"));
                    StrictJson.require(RESPONSE_SCHEMA.equals(StrictJson.text(envelope.get("schema")))
                            && id.equals(StrictJson.text(envelope.get("request_id")))
                            && requestSha256.equals(StrictJson.text(envelope.get("request_sha256"))),
                            "Codex response belongs to another original request");
                    JsonNode selection = StrictJson.object(envelope.get("selection"),
                            Set.of("decision", "proposal_id", "body_sha256", "reason"));
                    requireRemaining(deadline, nanoEnd);
                    return new Reply(this, directory, id, requestSha256, response,
                            new String(FullJsonTree.encode(selection, MAX_RESPONSE_BYTES), java.nio.charset.StandardCharsets.UTF_8),
                            "", elapsed(started));
                }
                long remaining = remaining(deadline, nanoEnd);
                TimeUnit.NANOSECONDS.sleep(Math.min(100_000_000L, remaining));
            }
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            return new Reply(this, directory, id, requestSha256, response, "", "interrupted", elapsed(started));
        } catch (IOException | RuntimeException failure) {
            return new Reply(this, directory, id, requestSha256, response, "",
                    failure.getClass().getSimpleName() + ":" + String.valueOf(failure.getMessage()), elapsed(started));
        }
    }

    /** Called only after the ordinary material sink preserved the complete original response attempt. */
    void acknowledge(Reply reply, ExactRef actualAttempt) throws IOException {
        Objects.requireNonNull(reply); Objects.requireNonNull(actualAttempt);
        StrictJson.require(reply.owner == this, "Codex response belongs to another transport instance");
        if (reply.directory == null || !Files.isRegularFile(reply.directory.resolve("request.json"))) return;
        ObjectNode ack = StrictJson.object();
        ack.put("schema", ARCHIVED_SCHEMA); ack.put("request_id", reply.requestId);
        ack.put("request_sha256", reply.requestSha256); ack.put("observed_at_utc", clock.instant().toString());
        ack.set("attempt", actualAttempt.toJson());
        publish(reply.directory.resolve("archived.json"), FullJsonTree.encode(ack, MAX_ACK_BYTES));
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
            Path ackFile = entry.resolve("archived.json");
            if (!Files.isRegularFile(ackFile)) continue;
            JsonNode ack = FullJsonTree.parse(readBounded(ackFile, MAX_ACK_BYTES), MAX_ACK_BYTES);
            byte[] request = readBounded(entry.resolve("request.json"), MAX_REQUEST_BYTES);
            if (!ARCHIVED_SCHEMA.equals(StrictJson.text(ack.get("schema")))
                    || !entry.getFileName().toString().equals(StrictJson.text(ack.get("request_id")))
                    || !ActionCodec.sha256(request).equals(StrictJson.text(ack.get("request_sha256")))) continue;
            StrictJson.require(entry.toAbsolutePath().normalize().getParent().equals(root), "owned Codex queue entry required");
            // Only these transport-owned files are reclaimed; an unknown file prevents deleting its directory.
            Files.deleteIfExists(entry.resolve("response.json")); Files.deleteIfExists(ackFile);
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

    private void emitReady(Path directory, String id, String sha, String proposal, Instant deadline) throws IOException {
        ObjectNode event = StrictJson.object(); event.put("schema", "xar.ordinary-codex-file-progress/v1");
        event.put("status", "ORDINARY_CODEX_REQUEST_READY"); event.put("request_id", id);
        event.put("request_sha256", sha); event.put("proposal_id", proposal);
        event.put("request_file", directory.resolve("request.json").toString());
        event.put("deadline_utc", deadline.toString());
        byte[] bytes = FullJsonTree.encode(event, MAX_REQUEST_BYTES);
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
