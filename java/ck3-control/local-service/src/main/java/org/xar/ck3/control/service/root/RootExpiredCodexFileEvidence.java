package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.WriterContracts.Pin;

/** Historical queue evidence only. Caller retains its original writer Session; no process/death/action fact is inferred. */
final class RootExpiredCodexFileEvidence {
    static final String RECEIPT_SCHEMA = "xar.ordinary-codex-file-expired-evidence/v1";
    static final int MAX_EVIDENCE_BYTES = 512 * 1024;
    private static final int SMALL = RootCodexFileDecisionExchange.MAX_REQUEST_BYTES;
    private RootExpiredCodexFileEvidence() { }

    static void archive(Path root, String machine, Clock clock, RootOnlineDecisionSelector.MaterialSink sink,
            Instant currentDeadline, long currentNanoEnd) throws IOException {
        if (!Files.isDirectory(root, LinkOption.NOFOLLOW_LINKS)) return;
        List<Path> entries;
        try (var paths = Files.list(root)) {
            entries = paths.filter(path -> Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS))
                    .filter(path -> path.getFileName().toString().matches("codex-[0-9a-f-]{36}"))
                    .limit(RootCodexFileDecisionExchange.MAX_ENTRIES + 1L).toList();
        }
        if (entries.size() > RootCodexFileDecisionExchange.MAX_ENTRIES) throw new IOException("bounded owned Codex queue required");
        for (Path entry : entries) {
            if (!clock.instant().isBefore(currentDeadline) || currentNanoEnd - System.nanoTime() <= 0) return;
            if (Files.exists(entry.resolve("expired-late.json"), LinkOption.NOFOLLOW_LINKS)) continue;
            archiveOne(entry, machine, clock, sink);
        }
    }

    private static void archiveOne(Path entry, String machine, Clock clock, RootOnlineDecisionSelector.MaterialSink sink) throws IOException {
        HeldFiles files = new HeldFiles(); boolean archiveStarted = false; ObjectNode marker = null; boolean hadPrevious = false;
        try (files) {
            // A requester can stop after creating its directory and before publishing request.json.
            var request = files.optional(entry.resolve("request.json"), SMALL);
            if (request == null) return;
            ObjectNode row = CodexSessionDecisionFiles.parseEnvelope(request.original().bytes());
            String id = StrictJson.text(row.get("request_id"));
            if (!id.equals(entry.getFileName().toString()) || !machine.equals(StrictJson.text(row.get("machine_id")))) return;
            String until = StrictJson.text(row.get("deadline_utc"));
            StrictJson.require(until.endsWith("Z"), "original UTC expiry required");
            Instant deadline = Instant.parse(until);
            if (clock.instant().isBefore(deadline)) return;
            var response = files.optional(entry.resolve("response.json"), RootCodexFileDecisionExchange.MAX_RESPONSE_BYTES);
            var ready = files.optional(entry.resolve("ready.json"), SMALL);
            var ack = files.optional(entry.resolve("archived.json"), RootCodexFileDecisionExchange.MAX_ACK_BYTES);
            var previous = files.optional(entry.resolve("expired.json"), RootCodexFileDecisionExchange.MAX_ACK_BYTES);
            hadPrevious = previous != null;
            if (coveredByOriginalArchive(request, response, ack) || coveredByExpired(request, response, previous)) return;
            ObjectNode evidence = StrictJson.object().put("schema", "xar.ordinary-codex-expired-file-material/v1")
                    .put("request_id", id).put("machine_id", machine).put("deadline_utc", until)
                    .put("observed_at_utc", clock.instant().toString()).put("requester_state", "UNKNOWN")
                    .put("effective_decision", "WAIT").put("qualification", "HISTORICAL_FILE_DATA_ONLY");
            evidence.set("referenced_payload", row.get("payload"));
            if (row.has("original_command")) evidence.set("referenced_original_command", row.get("original_command"));
            evidence.put("referenced_dependencies", "NOT_QUALIFIED_OR_REOPENED");
            add(evidence, "request", request); add(evidence, "response", response);
            add(evidence, "ready", ready); add(evidence, "original_ack", ack); add(evidence, "previous_expired", previous);
            byte[] bytes = FullJsonTree.encode(evidence, MAX_EVIDENCE_BYTES);
            files.verify(); archiveStarted = true;
            ExactRef archived = sink.preserve(RawJson.fullMaterial(bytes));
            StrictJson.require(archived.bytes() == bytes.length && archived.sha256().equals(ActionCodec.sha256(bytes)),
                    "actual complete expired evidence archive required");
            var archiveFile = files.hold(Path.of(archived.path()), MAX_EVIDENCE_BYTES);
            StrictJson.require(archiveFile.original().pin().reference().bytes() == bytes.length
                    && archiveFile.original().pin().reference().sha256().equals(archived.sha256()), "actual pinned archive blob required");
            files.verify();
            marker = StrictJson.object().put("schema", RECEIPT_SCHEMA).put("request_id", id)
                    .put("request_sha256", request.original().pin().reference().sha256()).put("deadline_utc", until)
                    .put("requester_state", "UNKNOWN").put("effective_decision", "WAIT");
            marker.set("evidence", archived.toJson()); marker.set("evidence_pin", archiveFile.original().pin().toJson()); marker.set("request_pin", request.original().pin().toJson());
            marker.set("response_pin", pin(response)); marker.set("ready_pin", pin(ready)); marker.set("original_ack_pin", pin(ack));
            marker.set("previous_expired_pin", pin(previous));
        } catch (IOException | RuntimeException failure) {
            if (archiveStarted || files.closeFailed) throw failure;
            // An unreadable, malformed, oversized or partially published entry remains untouched; no receipt is minted.
            retained(entry, failure); return;
        }
        if (marker != null) publish(entry.resolve(hadPrevious ? "expired-late.json" : "expired.json"), FullJsonTree.encode(marker, RootCodexFileDecisionExchange.MAX_ACK_BYTES));
    }

    static boolean matches(Path file, JsonNode expected, int maximum) throws IOException {
        try { Files.readAttributes(file, java.nio.file.attribute.BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS); }
        catch (java.nio.file.NoSuchFileException absent) { return expected == null || expected.isNull(); }
        return expected != null && !expected.isNull() && CodexDecisionFilePins.read(file, maximum).pin().equals(Pin.fromJson(expected));
    }
    static void requireReceipt(JsonNode value) {
        var row = StrictJson.object(value, Set.of("schema", "request_id", "request_sha256", "deadline_utc", "requester_state",
                "effective_decision", "evidence", "evidence_pin", "request_pin", "response_pin", "ready_pin", "original_ack_pin", "previous_expired_pin"));
        var ref = ExactRef.fromJson(row.get("evidence")); var pin = Pin.fromJson(row.get("evidence_pin"));
        StrictJson.require(Path.of(ref.path()).isAbsolute() && Path.of(ref.path()).normalize().equals(Path.of(pin.reference().path()).normalize())
                && ref.bytes() == pin.reference().bytes() && ref.sha256().equals(pin.reference().sha256()), "exact archive blob pin binding required");
        StrictJson.require(RECEIPT_SCHEMA.equals(StrictJson.text(row.get("schema")))
                && "UNKNOWN".equals(StrictJson.text(row.get("requester_state")))
                && "WAIT".equals(StrictJson.text(row.get("effective_decision"))), "historical expired evidence cannot adopt a decision or assert requester exit");
    }

    private static boolean coveredByExpired(CodexDecisionFilePins.Held request, CodexDecisionFilePins.Held response,
            CodexDecisionFilePins.Held previous) {
        if (previous == null) return false;
        try {
            JsonNode row = FullJsonTree.parse(previous.original().bytes(), RootCodexFileDecisionExchange.MAX_ACK_BYTES);
            requireReceipt(row);
            return request.original().pin().equals(Pin.fromJson(row.get("request_pin")))
                    && (response == null ? !row.hasNonNull("response_pin") : response.original().pin().equals(Pin.fromJson(row.get("response_pin"))));
        } catch (RuntimeException malformedOldReceipt) { return false; }
    }

    private static boolean coveredByOriginalArchive(CodexDecisionFilePins.Held request,
            CodexDecisionFilePins.Held response, CodexDecisionFilePins.Held ack) {
        if (ack == null) return false;
        try {
            JsonNode row = FullJsonTree.parse(ack.original().bytes(), RootCodexFileDecisionExchange.MAX_ACK_BYTES);
            return RootCodexFileDecisionExchange.ARCHIVED_SCHEMA.equals(StrictJson.text(row.get("schema")))
                    && request.original().pin().equals(Pin.fromJson(row.get("request_pin")))
                    && (response == null ? !row.hasNonNull("response_pin")
                    : response.original().pin().equals(Pin.fromJson(row.get("response_pin"))));
        } catch (RuntimeException malformedOldReceipt) { return false; }
    }
    private static JsonNode pin(CodexDecisionFilePins.Held held) {
        return held == null ? com.fasterxml.jackson.databind.node.NullNode.getInstance() : held.original().pin().toJson();
    }
    private static void add(ObjectNode record, String name, CodexDecisionFilePins.Held held) {
        record.set(name + "_pin", pin(held));
        if (held == null) record.putNull(name + "_wire_base64");
        else record.put(name + "_wire_base64", Base64.getEncoder().encodeToString(held.original().bytes()));
    }
    private static final class HeldFiles implements AutoCloseable {
        private final List<CodexDecisionFilePins.Held> files = new ArrayList<>();
        private boolean closeFailed;
        CodexDecisionFilePins.Held hold(Path path, int maximum) throws IOException {
            var held = CodexDecisionFilePins.hold(path, maximum); files.add(held); return held;
        }
        CodexDecisionFilePins.Held optional(Path path, int maximum) throws IOException {
            try { Files.readAttributes(path, java.nio.file.attribute.BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS); }
            catch (java.nio.file.NoSuchFileException absent) { return null; }
            return hold(path, maximum);
        }
        void verify() throws IOException { for (var held : files) held.verify(); }
        @Override public void close() throws IOException {
            IOException problem = null;
            for (int i = files.size() - 1; i >= 0; i--) try { files.get(i).close(); }
            catch (IOException failure) {
                closeFailed = true;
                if (problem == null) problem = failure; else problem.addSuppressed(failure);
            }
            if (problem != null) throw problem;
        }
    }
    private static void publish(Path target, byte[] bytes) throws IOException {
        Path staged = target.resolveSibling("expired." + UUID.randomUUID() + ".tmp");
        try {
            Files.write(staged, bytes, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
            Files.createLink(target, staged);
        } finally { Files.deleteIfExists(staged); }
    }
    private static void retained(Path entry, Exception failure) throws IOException {
        String reason = failure.getClass().getSimpleName() + ":" + String.valueOf(failure.getMessage());
        if (reason.length() > 256) reason = reason.substring(0, 256);
        String path = entry.toString(); if (path.length() > 512) path = path.substring(0, 512);
        var event = StrictJson.object().put("schema", "xar.ordinary-codex-file-progress/v1")
                .put("status", "EXPIRED_CODEX_EVIDENCE_RETAINED_UNARCHIVED").put("entry", path).put("reason", reason)
                .put("requester_state", "UNKNOWN");
        byte[] bytes = FullJsonTree.encode(event, 4096);
        synchronized (System.out) { System.out.write(bytes); System.out.write(10); System.out.flush(); }
    }
}
