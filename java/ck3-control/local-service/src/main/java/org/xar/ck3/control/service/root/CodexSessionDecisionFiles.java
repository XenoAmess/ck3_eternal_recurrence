package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.Arrays;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.WriterContracts.Pin;

/** Public, offline Codex-session side of the ordinary selector's file transport. No action is submitted. */
public final class CodexSessionDecisionFiles {
    /** v2 adds an independently archived exact original command; response v1 remains unchanged. */
    public static final String REQUEST_SCHEMA = "xar.ordinary-codex-file-request/v2";
    public static final String LEGACY_REQUEST_SCHEMA = "xar.ordinary-codex-file-request/v1";
    public static final String RESPONSE_SCHEMA = "xar.ordinary-codex-file-response/v1";
    public static final int MAX_REQUEST_BYTES = 16 * 1024;
    public static final int MAX_RESPONSE_BYTES = 256 * 1024;
    public static final String SELECTION_CONTRACT = "Exactly decision,proposal_id,body_sha256,reason; SELECT_PROPOSAL or WAIT; original IDs only";
    private static final Set<String> REQUEST_FIELDS = Set.of("schema", "request_id", "provider", "machine_id",
            "proposal_id", "body_sha256", "created_at_utc", "deadline_utc", "before", "payload", "original_command",
            "response_file", "response_schema", "selection_contract");
    private static final Set<String> LEGACY_REQUEST_FIELDS = REQUEST_FIELDS.stream().filter(field -> !field.equals("original_command"))
            .collect(java.util.stream.Collectors.toUnmodifiableSet());
    public enum Decision { SELECT_PROPOSAL, WAIT }
    public record Selection(Decision decision, String proposalId, String bodySha256, String reason) {
        public Selection {
            Objects.requireNonNull(decision); StrictJson.text(proposalId); requireSha(bodySha256); StrictJson.text(reason);
        }
        public static Selection fromJson(JsonNode value) {
            var row = StrictJson.object(value, Set.of("decision", "proposal_id", "body_sha256", "reason"));
            return new Selection(Decision.valueOf(StrictJson.text(row.get("decision"))),
                    StrictJson.text(row.get("proposal_id")), StrictJson.text(row.get("body_sha256")), StrictJson.text(row.get("reason")));
        }
        public ObjectNode toJson() {
            return StrictJson.object().put("decision", decision.name()).put("proposal_id", proposalId)
                    .put("body_sha256", bodySha256).put("reason", reason);
        }
    }

    /** Constructible only by exact, bounded reads. Source metadata is original evidence, never live qualification. */
    public static final class PendingRequest {
        private final Path file, materialsRoot;
        private final String requestSha256;
        private final byte[] envelope, payload, originalCommand;
        private final Clock clock;
        private final Pin requestPin, payloadPin, commandPin;
        private final Instant deadline;
        private final long nanoEnd;
        private PendingRequest(Path file, Path materialsRoot, String sha, byte[] envelope, byte[] payload,
                byte[] command, Clock clock, Instant deadline, long nanoEnd, Pin requestPin, Pin payloadPin, Pin commandPin) {
            this.file = file; this.materialsRoot = materialsRoot; requestSha256 = sha;
            this.envelope = envelope.clone(); this.payload = payload.clone(); originalCommand = command.clone();
            this.clock = clock; this.deadline = deadline; this.nanoEnd = nanoEnd;
            this.requestPin = requestPin; this.payloadPin = payloadPin; this.commandPin = commandPin;
        }
        public ObjectNode custody() {
            ObjectNode result = StrictJson.object().put("schema", "xar.ordinary-codex-session-custody/v1");
            result.set("request", requestPin.toJson()); result.set("payload", payloadPin.toJson()); result.set("original_command", commandPin.toJson());
            return result;
        }
        public void requireCustody(JsonNode expected) {
            StrictJson.object(expected, Set.of("schema", "request", "payload", "original_command"));
            StrictJson.require("xar.ordinary-codex-session-custody/v1".equals(StrictJson.text(expected.get("schema")))
                    && requestPin.equals(Pin.fromJson(expected.get("request"))) && payloadPin.equals(Pin.fromJson(expected.get("payload")))
                    && commandPin.equals(Pin.fromJson(expected.get("original_command"))), "reviewed original FileID custody changed");
        }
        public Path requestFile() { return file; }
        public String requestSha256() { return requestSha256; }
        public byte[] envelopeBytes() { return envelope.clone(); }
        public byte[] payloadBytes() { return payload.clone(); }
        public byte[] originalCommandBytes() { return originalCommand.clone(); }
        public Instant deadline() { return deadline; }
        public Selection selection(Decision decision, String reason) {
            var row = FullJsonTree.parse(envelope, MAX_REQUEST_BYTES);
            return new Selection(decision, StrictJson.text(row.get("proposal_id")), StrictJson.text(row.get("body_sha256")), reason);
        }
    }

    private CodexSessionDecisionFiles() { }

    /** Shared envelope schema for current review and historical evidence capture; grants no freshness/authority. */
    static ObjectNode parseEnvelope(byte[] bytes) {
        var row = FullJsonTree.parse(bytes, MAX_REQUEST_BYTES);
        String schema = StrictJson.text(row.get("schema"));
        StrictJson.require(REQUEST_SCHEMA.equals(schema) || LEGACY_REQUEST_SCHEMA.equals(schema), "known original Codex file request schema required");
        var result = StrictJson.object(row, LEGACY_REQUEST_SCHEMA.equals(schema) ? LEGACY_REQUEST_FIELDS : REQUEST_FIELDS);
        StrictJson.require("codex-session".equals(StrictJson.text(result.get("provider")))
                && RESPONSE_SCHEMA.equals(StrictJson.text(result.get("response_schema")))
                && SELECTION_CONTRACT.equals(StrictJson.text(result.get("selection_contract"))), "original Codex response contract required");
        return result;
    }

    /** expectedRequestSha256 comes from the original READY event; materialRoot is explicit caller custody. */
    public static PendingRequest read(Path requestFile, String expectedRequestSha256, Path materialRoot, Clock clock) throws IOException {
        return readWithOriginalCommand(requestFile, expectedRequestSha256, materialRoot, null, clock);
    }

    /** Legacy v1 requires an explicit existing original command reference; no command is synthesized or deadline renewed. */
    public static PendingRequest readWithOriginalCommand(Path requestFile, String expectedRequestSha256, Path materialRoot,
            ExactRef suppliedOriginal, Clock clock) throws IOException {
        return checkedRead(requestFile, expectedRequestSha256, materialRoot, suppliedOriginal, clock, null);
    }

    private static PendingRequest checkedRead(Path requestFile, String expectedRequestSha256, Path materialRoot,
            ExactRef suppliedOriginal, Clock clock, PendingRequest reviewed) throws IOException {
        Objects.requireNonNull(clock); requireSha(expectedRequestSha256);
        Path file = Objects.requireNonNull(requestFile).toAbsolutePath().normalize();
        StrictJson.require(file.getFileName().toString().equals("request.json") && file.getParent() != null,
                "explicit original request.json required");
        StrictJson.require(Files.isRegularFile(file, LinkOption.NOFOLLOW_LINKS)
                && file.toRealPath().equals(file), "original request must not be redirected");
        var requestDocument = CodexDecisionFilePins.read(file, MAX_REQUEST_BYTES);
        byte[] envelope = requestDocument.bytes();
        StrictJson.require(ActionCodec.sha256(envelope).equals(expectedRequestSha256), "original READY request hash differs");
        var parsed = parseEnvelope(envelope);
        boolean legacy = LEGACY_REQUEST_SCHEMA.equals(StrictJson.text(parsed.get("schema")));
        var row = StrictJson.object(parsed, legacy ? LEGACY_REQUEST_FIELDS : REQUEST_FIELDS);
        StrictJson.require((REQUEST_SCHEMA.equals(StrictJson.text(row.get("schema"))) || legacy && suppliedOriginal != null)
                && "codex-session".equals(StrictJson.text(row.get("provider"))), "v2 request or explicit exact original for legacy v1 required");
        String id = StrictJson.text(row.get("request_id"));
        StrictJson.require(id.matches("codex-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
                && id.equals(file.getParent().getFileName().toString()), "request directory crossed original identity");
        StrictJson.require(file.getParent().resolve("response.json").equals(Path.of(StrictJson.text(row.get("response_file"))))
                && RESPONSE_SCHEMA.equals(StrictJson.text(row.get("response_schema")))
                && SELECTION_CONTRACT.equals(StrictJson.text(row.get("selection_contract"))), "original response contract differs");
        requirePending(file);
        Path readyFile = file.getParent().resolve("ready.json");
        if (!legacy || Files.exists(readyFile)) {
            JsonNode ready = FullJsonTree.parse(CodexDecisionFilePins.read(readyFile, MAX_REQUEST_BYTES).bytes(), MAX_REQUEST_BYTES);
            StrictJson.object(ready, Set.of("schema", "status", "request_id", "request_sha256", "proposal_id", "request_file", "deadline_utc", "request_pin"));
            StrictJson.require("xar.ordinary-codex-file-progress/v1".equals(StrictJson.text(ready.get("schema")))
                    && "ORDINARY_CODEX_REQUEST_READY".equals(StrictJson.text(ready.get("status")))
                    && id.equals(StrictJson.text(ready.get("request_id")))
                    && expectedRequestSha256.equals(StrictJson.text(ready.get("request_sha256")))
                    && file.equals(Path.of(StrictJson.text(ready.get("request_file"))))
                    && row.get("proposal_id").equals(ready.get("proposal_id")) && row.get("deadline_utc").equals(ready.get("deadline_utc"))
                    && requestDocument.pin().equals(Pin.fromJson(ready.get("request_pin"))), "published READY crossed original request FileID");
        }
        Instant created = utc(row, "created_at_utc"), deadline = utc(row, "deadline_utc");
        StrictJson.require(deadline.isAfter(created) && !deadline.isAfter(created.plusSeconds(120)), "finite original request interval required");
        long remaining = Duration.between(clock.instant(), deadline).toNanos();
        StrictJson.require(remaining > 0 && remaining <= Duration.ofSeconds(120).toNanos(), "original request expired or clock predates its interval");
        long nanoEnd = System.nanoTime() + remaining;
        Path materials = Objects.requireNonNull(materialRoot).toRealPath();
        StrictJson.require(Files.isDirectory(materials), "explicit existing material custody root required");
        ExactRef originalRef = legacy ? suppliedOriginal : ExactRef.fromJson(row.get("original_command"));
        StrictJson.require(suppliedOriginal == null || suppliedOriginal.equals(originalRef), "supplied original differs from v2 command reference");
        var commandDocument = exact(originalRef, materials, ActionCodec.MAX_COMMAND_BYTES);
        byte[] commandBytes = commandDocument.bytes();
        if (reviewed != null) {
            var payloadDocument = exact(ExactRef.fromJson(row.get("payload")), materials, FullJsonTree.MAXIMUM_BYTES);
            // The first read validated the complete command and review task. Match the original
            // FileIDs and bytes before reusing that validation for this response.
            StrictJson.require(requestDocument.pin().equals(reviewed.requestPin)
                    && commandDocument.pin().equals(reviewed.commandPin) && payloadDocument.pin().equals(reviewed.payloadPin)
                    && Arrays.equals(envelope, reviewed.envelope) && Arrays.equals(commandBytes, reviewed.originalCommand)
                    && Arrays.equals(payloadDocument.bytes(), reviewed.payload), "reviewed material changed before response");
            requireRemaining(clock, deadline, nanoEnd);
            return reviewed;
        }
        ActionCommand command = ActionCodec.decodeCommand(commandBytes);
        StrictJson.require(command.actionId().equals(StrictJson.text(row.get("proposal_id")))
                && ActionCodec.sha256(commandBytes).equals(StrictJson.text(row.get("body_sha256")))
                && command.origin().machineId().equals(StrictJson.text(row.get("machine_id")))
                && !deadline.isAfter(command.deadline()), "request crossed original command, source machine or deadline");
        var original = FullJsonTree.parse(commandBytes, ActionCodec.MAX_COMMAND_BYTES);
        StrictJson.require(original.has("before") && Arrays.equals(FullJsonTree.encode(original.get("before"), MAX_REQUEST_BYTES),
                FullJsonTree.encode(row.get("before"), MAX_REQUEST_BYTES)), "request crossed original observation identity");
        var payloadDocument = exact(ExactRef.fromJson(row.get("payload")), materials, FullJsonTree.MAXIMUM_BYTES);
        byte[] payload = payloadDocument.bytes();
        var wire = FullJsonTree.parse(payload, FullJsonTree.MAXIMUM_BYTES);
        StrictJson.require("codex-session".equals(StrictJson.text(wire.get("model"))) && wire.path("messages").isArray(),
                "original Codex review payload required");
        JsonNode task = null;
        for (var message : wire.get("messages")) {
            if ("user".equals(StrictJson.text(message.get("role")))) {
                StrictJson.require(task == null, "one original review task required");
                task = reviewTask(message.get("content"));
            }
        }
        StrictJson.require(task != null && command.actionId().equals(StrictJson.text(task.get("proposal_id")))
                && ActionCodec.sha256(commandBytes).equals(StrictJson.text(task.get("body_sha256"))), "review payload crossed original proposal");
        requireRemaining(clock, deadline, nanoEnd);
        return new PendingRequest(file, materials, expectedRequestSha256, envelope, payload, commandBytes, clock, deadline, nanoEnd, requestDocument.pin(), payloadDocument.pin(), commandDocument.pin());
    }

    /** Full archived review document, distinct from receipt identifiers and their smaller text bound. */
    static JsonNode reviewTask(JsonNode content) {
        StrictJson.require(content!=null&&content.isTextual()&&!content.textValue().isEmpty()
                &&content.textValue().length()<=FullJsonTree.MAXIMUM_BYTES,"bounded complete review document required");
        try {
            var encoded=java.nio.charset.StandardCharsets.UTF_8.newEncoder()
                    .onMalformedInput(java.nio.charset.CodingErrorAction.REPORT)
                    .onUnmappableCharacter(java.nio.charset.CodingErrorAction.REPORT)
                    .encode(java.nio.CharBuffer.wrap(content.textValue()));
            StrictJson.require(encoded.remaining()<=FullJsonTree.MAXIMUM_BYTES,"complete review document exceeds its explicit byte bound");
            byte[] bytes=new byte[encoded.remaining()];encoded.get(bytes);
            return FullJsonTree.parse(bytes,FullJsonTree.MAXIMUM_BYTES);
        }catch(java.nio.charset.CharacterCodingException invalid) {
            throw new IllegalArgumentException("invalid Unicode in complete review document",invalid);
        }
    }

    /** Revalidates all read material and the original deadline; one complete response is published without overwrite. */
    public static ExactRef respond(PendingRequest request, Selection selection) throws IOException {
        Objects.requireNonNull(request); Objects.requireNonNull(selection);
        requireRemaining(request.clock, request.deadline, request.nanoEnd);
        checkedRead(request.file, request.requestSha256, request.materialsRoot, request.commandPin.reference(), request.clock, request);
        Selection identity = request.selection(selection.decision(), selection.reason());
        StrictJson.require(identity.equals(selection), "selection crossed original proposal identity");
        var row = FullJsonTree.parse(request.envelope, MAX_REQUEST_BYTES);
        ObjectNode response = StrictJson.object().put("schema", RESPONSE_SCHEMA)
                .put("request_id", StrictJson.text(row.get("request_id"))).put("request_sha256", request.requestSha256);
        response.set("selection", selection.toJson());
        byte[] bytes = FullJsonTree.encode(response, MAX_RESPONSE_BYTES);
        Path target = request.file.getParent().resolve("response.json");
        Path temporary = target.resolveSibling("response." + UUID.randomUUID() + ".tmp");
        try {
            Files.write(temporary, bytes, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
            requirePending(request.file);
            requireRemaining(request.clock, request.deadline, request.nanoEnd);
            // A hard link atomically exposes complete bytes and fails if target exists. No replace/fallback.
            Files.createLink(target, temporary);
        } finally { Files.deleteIfExists(temporary); }
        return new ExactRef(target.toString(), bytes.length, ActionCodec.sha256(bytes));
    }

    public static byte[] readSelectionFile(Path selectionFile) throws IOException { return readBounded(selectionFile, MAX_RESPONSE_BYTES); }
    private static CodexDecisionFilePins.Document exact(ExactRef ref, Path root, int maximum) throws IOException {
        Path path = Path.of(ref.path());
        StrictJson.require(path.isAbsolute() && path.toAbsolutePath().normalize().startsWith(root)
                && path.toRealPath().startsWith(root) && Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS)
                && ref.bytes() > 0 && ref.bytes() <= maximum, "bounded material inside explicit custody root required");
        var document = CodexDecisionFilePins.read(path, maximum);
        byte[] bytes = document.bytes();
        StrictJson.require(ref.bytes() == bytes.length && ref.sha256().equals(ActionCodec.sha256(bytes)), "exact archived material changed");
        return document;
    }
    private static byte[] readBounded(Path path, int maximum) throws IOException {
        try (var input = Files.newInputStream(path)) {
            byte[] bytes = input.readNBytes(maximum + 1);
            if (bytes.length == 0 || bytes.length > maximum) throw new IOException("bounded complete Codex material required");
            return bytes;
        }
    }
    private static void requirePending(Path file) {
        StrictJson.require(!Files.exists(file.getParent().resolve("archived.json"), LinkOption.NOFOLLOW_LINKS)
                && !Files.exists(file.getParent().resolve("response.json"), LinkOption.NOFOLLOW_LINKS)
                && !Files.exists(file.getParent().resolve("expired.json"), LinkOption.NOFOLLOW_LINKS)
                && !Files.exists(file.getParent().resolve("expired-late.json"), LinkOption.NOFOLLOW_LINKS), "original request is already answered or archived");
    }
    private static void requireRemaining(Clock clock, Instant deadline, long nanoEnd) {
        StrictJson.require(clock.instant().isBefore(deadline) && nanoEnd - System.nanoTime() > 0, "original Codex request deadline expired");
    }
    private static Instant utc(JsonNode row, String field) {
        String text = StrictJson.text(row.get(field)); StrictJson.require(text.endsWith("Z"), "original UTC instant required");
        return Instant.parse(text);
    }
    private static void requireSha(String value) { StrictJson.require(value != null && value.matches("[0-9a-f]{64}"), "lowercase exact SHA-256 required"); }
}
