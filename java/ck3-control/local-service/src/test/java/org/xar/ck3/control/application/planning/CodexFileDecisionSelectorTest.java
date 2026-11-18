package org.xar.ck3.control.application.planning;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.RootOnlineDecisionSelector;
import org.xar.ck3.control.service.root.CodexSessionDecisionFiles;
import org.xar.ck3.control.service.root.CodexSessionDecisionMain;
import org.xar.ck3.control.service.root.RootOrdinaryRuntimeConfiguration;

/** Real local file exchange and existing selector, without any HTTP, Native or action submission. */
final class CodexFileDecisionSelectorTest {
    @TempDir Path directory;
    private record Input(PlanningRequest request, PlanningResult.ActionSelected proposal) { }

    @Test @Timeout(20)
    void exactCodexReplyUsesFullArchivedPayloadAndOriginalParserWithoutAnHttpClient() throws Exception {
        String complete = "complete-context-" + "x".repeat(24000);
        Input input = input(complete); Path queue = directory.resolve("queue");
        var selector = selector(queue, Duration.ofSeconds(8));
        var http = RootOnlineDecisionSelector.class.getDeclaredField("http"); http.setAccessible(true);
        assertNull(http.get(selector), "explicit file transport must not instantiate an HTTP client");
        byte[] command = ActionCodec.encodeCommand(input.proposal().command());
        CompletableFuture<Path> responder = respondPublic(queue);
        var selection = selector.select(input.request(), input.proposal());
        Path requestPath = responder.get(5, TimeUnit.SECONDS);
        assertEquals(OrdinaryDecisionSelector.Choice.ACCEPT, selection.choice(), selection.reason());
        assertArrayEquals(command, ActionCodec.encodeCommand(input.proposal().command()));
        JsonNode request = tree(requestPath);
        assertTrue(Files.size(requestPath) <= 16384, "queue envelope has a bound independent of complete context size");
        Path payload = Path.of(request.path("payload").path("path").textValue());
        byte[] payloadBytes = Files.readAllBytes(payload);
        assertTrue(payloadBytes.length > 16384);
        assertEquals(request.path("payload").path("sha256").textValue(), ActionCodec.sha256(payloadBytes));
        assertTrue(new String(payloadBytes, StandardCharsets.UTF_8).contains(complete), "context must not be truncated to queue-envelope size");
        assertFalse(Files.exists(requestPath.getParent().resolve("payload.json")), "the queue references original archive material");
        assertTrue(Files.isRegularFile(requestPath.getParent().resolve("archived.json")));
        JsonNode receipt = tree(Path.of(selection.evidence().orElseThrow().path()));
        assertEquals("xar.ordinary-codex-decision/v1", receipt.path("schema").textValue());
        assertEquals("codex-file", receipt.path("transport").textValue());
        JsonNode attempt = tree(Path.of(receipt.path("attempts").get(0).path("path").textValue()));
        assertEquals("xar.ordinary-codex-file-attempt/v1", attempt.path("schema").textValue());
        assertFalse(attempt.has("status"), "file completion is never reported as an HTTP status");
        assertEquals(CodexSessionDecisionFiles.REQUEST_SCHEMA, request.path("schema").textValue());
        assertArrayEquals(command, read(Path.of(request.path("original_command").path("path").textValue())));
        assertArrayEquals(read(requestPath), java.util.Base64.getDecoder().decode(attempt.path("request_wire_base64").textValue()),
                "durable attempt must retain the exact queue request even after queue reclamation");
    }

    @Test @Timeout(20)
    void crossedRequestEnvelopeIsRejectedOnceAndTheOriginalSelectionIdentityStillApplies() throws Exception {
        for (String fault : List.of("request", "proposal")) {
            Input input = input("context"); Path queue = directory.resolve(fault);
            var selector = selector(queue, Duration.ofSeconds(5));
            CompletableFuture<Path> responder = respond(queue, Set.of(), response -> {
                if (fault.equals("request")) response.put("request_sha256", "0".repeat(64));
                else ((ObjectNode) response.get("selection")).put("body_sha256", "0".repeat(64));
            }, "SELECT_PROPOSAL");
            var selection = selector.select(input.request(), input.proposal()); responder.get(5, TimeUnit.SECONDS);
            assertEquals(OrdinaryDecisionSelector.Choice.WAIT, selection.choice());
            try (var paths = Files.list(queue)) { assertEquals(1, paths.filter(Files::isDirectory).count(), "invalid file reply must not create a retry request"); }
            assertTrue(selection.evidence().isPresent());
        }
    }

    @Test @Timeout(20)
    void deadlineRemainsFiniteAndLateReplyCannotTransferToANewOriginalRequest() throws Exception {
        Input input = input("deadline-context"); Path queue = directory.resolve("late");
        var first = selector(queue, Duration.ofMillis(180)).select(input.request(), input.proposal());
        assertEquals(OrdinaryDecisionSelector.Choice.WAIT, first.choice());
        Path original = onlyRequest(queue); JsonNode old = tree(original);
        writeResponse(original, response(old, Files.readAllBytes(original), "SELECT_PROPOSAL"));
        var responder = respond(queue, Set.of(original.getParent().getFileName().toString()), response -> {
            response.put("request_id", old.path("request_id").textValue());
            response.put("request_sha256", ActionCodec.sha256(read(original)));
        }, "SELECT_PROPOSAL");
        var second = selector(queue, Duration.ofSeconds(5)).select(input.request(), input.proposal());
        responder.get(5, TimeUnit.SECONDS);
        assertEquals(OrdinaryDecisionSelector.Choice.WAIT, second.choice());
        assertTrue(Files.isRegularFile(original.getParent().resolve("archived.json")));
    }

    @Test @Timeout(20)
    void pendingQueueBoundDoesNotDeleteUnansweredRequestsAndArchivedEntryCanReleaseOneSlot() throws Exception {
        Path full = directory.resolve("pending"); Files.createDirectories(full);
        for (int n = 0; n < 32; n++) Files.createDirectory(full.resolve("codex-" + UUID.randomUUID()));
        Input input = input("bounded-context");
        var denied = selector(full, Duration.ofSeconds(2)).select(input.request(), input.proposal());
        assertEquals(OrdinaryDecisionSelector.Choice.WAIT, denied.choice());
        try (var paths = Files.list(full)) { assertEquals(32, paths.filter(Files::isDirectory).count()); }

        Path queue = directory.resolve("archived");
        var firstResponder = respond(queue, Set.of(), response -> { }, "WAIT");
        var first = selector(queue, Duration.ofSeconds(5)).select(input.request(), input.proposal());
        Path firstRequest = firstResponder.get(5, TimeUnit.SECONDS);
        assertEquals(OrdinaryDecisionSelector.Choice.WAIT, first.choice());
        for (int n = 0; n < 31; n++) Files.createDirectory(queue.resolve("codex-" + UUID.randomUUID()));
        var nextResponder = respond(queue, Set.of(firstRequest.getParent().getFileName().toString()), response -> { }, "SELECT_PROPOSAL");
        var next = selector(queue, Duration.ofSeconds(5)).select(input.request(), input.proposal()); nextResponder.get(5, TimeUnit.SECONDS);
        assertEquals(OrdinaryDecisionSelector.Choice.ACCEPT, next.choice(), next.reason());
        assertFalse(Files.exists(firstRequest), "only the response already committed to the material archive releases a slot");
        try (var paths = Files.list(queue)) { assertEquals(32, paths.filter(Files::isDirectory).count()); }
    }

    @Test @Timeout(20)
    void heldQueueEnvelopeDeniesRewriteAndPinsTheActualResponseBeforeArchival() throws Exception {
        Input input = input("original request custody"); Path queue = directory.resolve("mutated-envelope");
        var selector = selector(queue, Duration.ofSeconds(5));
        var running = CompletableFuture.supplyAsync(() -> selector.select(input.request(), input.proposal()));
        Path file = awaitRequest(queue); byte[] original = read(file);
        assertThrows(java.io.IOException.class, () -> Files.write(file, (new String(original, StandardCharsets.UTF_8) + " ").getBytes(StandardCharsets.UTF_8)));
        writeResponse(file, response(FullJsonTree.parse(original, 16384), original, "SELECT_PROPOSAL"));
        var selection = running.get(5, TimeUnit.SECONDS);
        assertEquals(OrdinaryDecisionSelector.Choice.ACCEPT, selection.choice(), selection.reason());
        JsonNode receipt = tree(Path.of(selection.evidence().orElseThrow().path()));
        JsonNode attempt = tree(Path.of(receipt.path("attempts").get(0).path("path").textValue()));
        assertArrayEquals(original, java.util.Base64.getDecoder().decode(attempt.path("request_wire_base64").textValue()));
        assertEquals("", attempt.path("failure").textValue());
        var requestPin = org.xar.ck3.control.continuity.writer.WriterContracts.Pin.fromJson(attempt.get("request_pin"));
        var responsePin = org.xar.ck3.control.continuity.writer.WriterContracts.Pin.fromJson(attempt.get("response_pin"));
        assertEquals(ActionCodec.sha256(original), requestPin.reference().sha256());
        assertEquals(ActionCodec.sha256(java.util.Base64.getDecoder().decode(attempt.path("wire_base64").textValue())), responsePin.reference().sha256());
        assertFalse(requestPin.identity().fileIdDecimal().isEmpty());
        assertFalse(responsePin.identity().fileIdDecimal().isEmpty());
        // Archive completion releases the actual request/response handles, allowing ordinary cleanup.
        Files.move(file, file.resolveSibling("closed-request.json"));
    }

    @Test @Timeout(20)
    void publicConsumerRevalidatesCustodyAndNeverOverwritesAnOriginalResponse() throws Exception {
        Input input = input("exact custody context"); Path queue = directory.resolve("public-custody");
        var selector = selector(queue, Duration.ofSeconds(5));
        var running = CompletableFuture.supplyAsync(() -> selector.select(input.request(), input.proposal()));
        Path file = awaitRequest(queue); byte[] originalRequest = read(file);
        String sha = ActionCodec.sha256(originalRequest); Path materials = directory.resolve("materials");
        var pending = CodexSessionDecisionFiles.read(file, sha, materials, Clock.systemUTC());
        assertArrayEquals(ActionCodec.encodeCommand(input.proposal().command()), pending.originalCommandBytes());
        assertThrows(RuntimeException.class, () -> CodexSessionDecisionFiles.read(file, "0".repeat(64), materials, Clock.systemUTC()));
        Path wrongRoot = Files.createDirectory(directory.resolve("different-custody"));
        assertThrows(RuntimeException.class, () -> CodexSessionDecisionFiles.read(file, sha, wrongRoot, Clock.systemUTC()));
        JsonNode envelope = tree(file);
        assertThrows(java.io.IOException.class, () -> Files.write(file, new byte[] {1}));
        for (Path changed : List.of(Path.of(envelope.path("payload").path("path").textValue()),
                Path.of(envelope.path("original_command").path("path").textValue()))) {
            byte[] original = read(changed);
            var modified = Files.getLastModifiedTime(changed);
            Files.write(changed, java.util.Arrays.copyOf(original, original.length + 1));
            assertThrows(RuntimeException.class, () -> CodexSessionDecisionFiles.respond(pending,
                    pending.selection(CodexSessionDecisionFiles.Decision.SELECT_PROPOSAL, "reviewed original")));
            assertFalse(Files.exists(file.getParent().resolve("response.json")));
            Files.write(changed, original); Files.setLastModifiedTime(changed, modified);
        }
        assertThrows(RuntimeException.class, () -> CodexSessionDecisionFiles.respond(pending,
                new CodexSessionDecisionFiles.Selection(CodexSessionDecisionFiles.Decision.SELECT_PROPOSAL,
                        "another-action", ActionCodec.bodySha256(input.proposal().command()), "wrong original")));
        var response = CodexSessionDecisionFiles.respond(pending,
                pending.selection(CodexSessionDecisionFiles.Decision.WAIT, "reviewed and wait"));
        byte[] originalResponse = read(Path.of(response.path()));
        assertThrows(RuntimeException.class, () -> CodexSessionDecisionFiles.respond(pending,
                pending.selection(CodexSessionDecisionFiles.Decision.SELECT_PROPOSAL, "must not replace")));
        assertArrayEquals(originalResponse, read(Path.of(response.path())));
        assertEquals(OrdinaryDecisionSelector.Choice.WAIT, running.get(5, TimeUnit.SECONDS).choice());
        assertArrayEquals(originalRequest, read(file));
    }

    @Test @Timeout(20)
    void publicConsumerCannotReplyAfterOriginalWallOrMonotonicDeadline() throws Exception {
        for (boolean rollback : List.of(false, true)) {
            Input input = input("expiry context"); Path queue = directory.resolve("public-expiry-" + rollback);
            var selector = selector(queue, Duration.ofMillis(1200));
            var running = CompletableFuture.supplyAsync(() -> selector.select(input.request(), input.proposal()));
            Path file = awaitRequest(queue); byte[] bytes = read(file);
            var clock = new java.util.concurrent.atomic.AtomicReference<>(Instant.now());
            Clock mutable = new Clock() {
                @Override public java.time.ZoneId getZone() { return java.time.ZoneOffset.UTC; }
                @Override public Clock withZone(java.time.ZoneId zone) { return this; }
                @Override public Instant instant() { return clock.get(); }
            };
            var pending = CodexSessionDecisionFiles.read(file, ActionCodec.sha256(bytes), directory.resolve("materials"), mutable);
            if (rollback) {
                clock.set(clock.get().minusSeconds(30));
                Thread.sleep(1300); // Original monotonic interval expires despite wall-clock rollback.
            } else clock.set(pending.deadline());
            assertThrows(RuntimeException.class, () -> CodexSessionDecisionFiles.respond(pending,
                    pending.selection(CodexSessionDecisionFiles.Decision.SELECT_PROPOSAL, "too late")));
            assertFalse(Files.exists(file.getParent().resolve("response.json")));
            assertEquals(OrdinaryDecisionSelector.Choice.WAIT, running.get(5, TimeUnit.SECONDS).choice());
        }
    }

    @Test @Timeout(20)
    void sameBytesWithANewNativeFileIdCannotReplacePreviouslyReviewedMaterial() throws Exception {
        Input input = input("same bytes physical custody"); Path queue = directory.resolve("physical-custody");
        var selector = selector(queue, Duration.ofSeconds(5));
        var running = CompletableFuture.supplyAsync(() -> selector.select(input.request(), input.proposal()));
        Path file = awaitRequest(queue); byte[] original = read(file); String sha = ActionCodec.sha256(original);
        Path materials = directory.resolve("materials");
        var pending = CodexSessionDecisionFiles.read(file, sha, materials, Clock.systemUTC());
        var envelope = tree(file); Path payload = Path.of(envelope.path("payload").path("path").textValue());
        Path retained = payload.resolveSibling("retained-review.json");
        Files.move(payload, retained); Files.copy(retained, payload, java.nio.file.StandardCopyOption.COPY_ATTRIBUTES);
        assertArrayEquals(read(retained), read(payload));
        var changed = CodexSessionDecisionFiles.read(file, sha, materials, Clock.systemUTC());
        assertThrows(RuntimeException.class, () -> changed.requireCustody(pending.custody()));
        assertThrows(RuntimeException.class, () -> CodexSessionDecisionFiles.respond(pending,
                pending.selection(CodexSessionDecisionFiles.Decision.SELECT_PROPOSAL, "same bytes cannot replace original")));
        assertFalse(Files.exists(file.getParent().resolve("response.json")));
        Files.delete(payload); Files.move(retained, payload);
        CodexSessionDecisionFiles.respond(pending, pending.selection(CodexSessionDecisionFiles.Decision.WAIT, "original restored, wait"));
        assertEquals(OrdinaryDecisionSelector.Choice.WAIT, running.get(5, TimeUnit.SECONDS).choice());
    }

    @Test @Timeout(20)
    void legacyV1RequiresTheActualArchivedOriginalAndKeepsItsExistingDeadline() throws Exception {
        Input input = input("legacy source-bound review"); Path queue = directory.resolve("legacy-producer");
        var selector = selector(queue, Duration.ofSeconds(5));
        var running = CompletableFuture.supplyAsync(() -> selector.select(input.request(), input.proposal()));
        Path original = awaitRequest(queue); ObjectNode envelope = (ObjectNode) tree(original);
        var originalRef = ExactRef.fromJson(envelope.get("original_command"));
        Path legacy = directory.resolve("legacy-fixture").resolve(original.getParent().getFileName()); Files.createDirectories(legacy);
        Path legacyRequest = legacy.resolve("request.json");
        envelope.put("schema", CodexSessionDecisionFiles.LEGACY_REQUEST_SCHEMA); envelope.remove("original_command");
        envelope.put("response_file", legacy.resolve("response.json").toString());
        byte[] bytes = FullJsonTree.encode(envelope, 16384); Files.write(legacyRequest, bytes);
        String sha = ActionCodec.sha256(bytes); Path materials = directory.resolve("materials");
        assertThrows(RuntimeException.class, () -> CodexSessionDecisionFiles.read(legacyRequest, sha, materials, Clock.systemUTC()));
        var legacyRead = CodexSessionDecisionFiles.readWithOriginalCommand(legacyRequest, sha, materials, originalRef, Clock.systemUTC());
        assertEquals(Instant.parse(envelope.path("deadline_utc").textValue()), legacyRead.deadline());
        assertArrayEquals(ActionCodec.encodeCommand(input.proposal().command()), legacyRead.originalCommandBytes());
        CodexSessionDecisionFiles.respond(legacyRead, legacyRead.selection(CodexSessionDecisionFiles.Decision.WAIT, "legacy reviewed, wait"));
        // Only the real original selector is settled; the detached legacy fixture grants no action authority.
        var actual = CodexSessionDecisionFiles.read(original, ActionCodec.sha256(read(original)), materials, Clock.systemUTC());
        CodexSessionDecisionFiles.respond(actual, actual.selection(CodexSessionDecisionFiles.Decision.WAIT, "original reviewed, wait"));
        assertEquals(OrdinaryDecisionSelector.Choice.WAIT, running.get(5, TimeUnit.SECONDS).choice());
    }

    @Test @Timeout(20)
    void lateOrOversizedResponsesWithoutAnArchivedPhysicalPinAreNeverReclaimed() throws Exception {
        for (boolean oversized : List.of(false, true)) {
            Input input = input("unarchived response custody"); Path queue = directory.resolve("unarchived-response-" + oversized);
            var firstSelector = selector(queue, Duration.ofMillis(500));
            var first = CompletableFuture.supplyAsync(() -> firstSelector.select(input.request(), input.proposal()));
            Path request = awaitRequest(queue); Path responseFile = request.getParent().resolve("response.json");
            if (oversized) Files.write(responseFile, new byte[262145]);
            assertEquals(OrdinaryDecisionSelector.Choice.WAIT, first.get(5, TimeUnit.SECONDS).choice());
            if (!oversized) writeResponse(request, response(tree(request), read(request), "SELECT_PROPOSAL"));
            String original = ActionCodec.sha256(read(responseFile));
            for (int n = 0; n < 31; n++) Files.createDirectory(queue.resolve("codex-" + UUID.randomUUID()));
            var next = selector(queue, Duration.ofSeconds(2)).select(input.request(), input.proposal());
            assertEquals(OrdinaryDecisionSelector.Choice.WAIT, next.choice());
            if (oversized) {
                assertTrue(Files.isRegularFile(request));
                assertEquals(original, ActionCodec.sha256(read(responseFile)), "unarchivable oversized response remains untouched");
            } else {
                assertFalse(Files.exists(request), "complete expired response evidence releases a slot after archival");
                try (var materials = Files.list(directory.resolve("materials"))) {
                    var evidence = materials.map(CodexFileDecisionSelectorTest::read)
                            .map(bytes -> FullJsonTree.parse(bytes, FullJsonTree.MAXIMUM_BYTES))
                            .filter(row -> "xar.ordinary-codex-expired-file-material/v1".equals(row.path("schema").asText()))
                            .filter(row -> request.getParent().getFileName().toString().equals(row.path("request_id").asText())).findFirst().orElseThrow();
                    assertEquals("WAIT", evidence.path("effective_decision").textValue());
                    assertEquals(original, ActionCodec.sha256(java.util.Base64.getDecoder().decode(evidence.path("response_wire_base64").textValue())));
                }
            }
        }
    }

    private CompletableFuture<Path> respondPublic(Path queue) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                Path file = awaitRequest(queue); byte[] original = read(file); String sha = ActionCodec.sha256(original);
                Path materials = directory.resolve("materials");
                var inspected = CodexSessionDecisionMain.execute(Clock.systemUTC(), "inspect", file.toString(), sha, materials.toString());
                assertEquals("xar.ordinary-codex-session-inspection/v1", inspected.path("schema").textValue());
                assertEquals(sha, inspected.path("request").path("sha256").textValue());
                var pending = CodexSessionDecisionFiles.read(file, sha, materials, Clock.systemUTC());
                byte[] payload = pending.payloadBytes(); payload[0] = 0;
                assertNotEquals(0, pending.payloadBytes()[0], "review bytes must be immutable");
                Path selection = directory.resolve("session-selection.json");
                Files.write(selection, FullJsonTree.encode(pending.selection(CodexSessionDecisionFiles.Decision.SELECT_PROPOSAL,
                        "reviewed original proposal").toJson(), 262144));
                Path inspection = directory.resolve("session-inspection.json");
                Files.write(inspection, FullJsonTree.encode(inspected, 262144));
                var published = CodexSessionDecisionMain.execute(Clock.systemUTC(), "respond", file.toString(), sha,
                        materials.toString(), selection.toString(), inspection.toString());
                assertEquals("xar.ordinary-codex-session-response-published/v1", published.path("schema").textValue());
                return file;
            } catch (Exception failure) { throw new java.util.concurrent.CompletionException(failure); }
        });
    }

    private static Path awaitRequest(Path queue) throws Exception {
        long until = System.nanoTime() + TimeUnit.SECONDS.toNanos(5);
        while (System.nanoTime() < until) {
            if (Files.isDirectory(queue)) try (var paths = Files.list(queue)) {
                var found = paths.filter(Files::isDirectory).map(path -> path.resolve("request.json"))
                        .filter(Files::isRegularFile).findFirst();
                if (found.isPresent() && Files.isRegularFile(found.orElseThrow().getParent().resolve("ready.json"))) return found.orElseThrow();
            }
            Thread.sleep(5);
        }
        throw new IllegalStateException("original file request was not published");
    }

    private RootOnlineDecisionSelector selector(Path queue, Duration timeout) {
        return new RootOnlineDecisionSelector(new RootOrdinaryRuntimeConfiguration.DecisionProvider(
                queue.toUri(), "codex-session", timeout, 1, Duration.ZERO), Clock.systemUTC(), raw -> {
            byte[] bytes = raw.bytes(); String sha = ActionCodec.sha256(bytes);
            Path root = directory.resolve("materials"); Files.createDirectories(root); Path file = root.resolve(sha + ".json");
            if (!Files.exists(file)) Files.write(file, bytes);
            return new ExactRef(file.toAbsolutePath().toString(), bytes.length, sha);
        });
    }
    private static Input input(String context) {
        OperationKey operation = new OperationKey("fixture-source-selected-query");
        var snapshot = new OpportunityJson.Obj(Map.ofEntries(
                Map.entry("paused", new OpportunityJson.Bool(true)), Map.entry("map_ready", new OpportunityJson.Bool(true)),
                Map.entry("revision", integer(1)), Map.entry("native_revision", integer(1)),
                Map.entry("date_raw", integer(24000)), Map.entry("snapshot_id", new OpportunityJson.Text("snapshot-1")),
                Map.entry("episode_run_id", new OpportunityJson.Text("episode-1")),
                Map.entry("played_character", new OpportunityJson.Obj(Map.of("character_id", integer(29829), "alive", new OpportunityJson.Bool(true)))),
                Map.entry("active_wars", new OpportunityJson.Arr(List.of())), Map.entry("player_armies", new OpportunityJson.Arr(List.of())),
                Map.entry("complete_codex_context", new OpportunityJson.Text(context)),
                Map.entry("diagnostics", new OpportunityJson.Obj(Map.of("connection_generation", integer(1), "bridge_pid", integer(123))))));
        var generation = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var before = new ObservationIdentity("fixture-machine-1", generation,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.ONE,
                        BigInteger.valueOf(24000)), "snapshot-1", BigInteger.ONE, "episode-1"), 1);
        var source = new G2Source(before.machineId(), Instant.now().toString(), "fixture-build",
                new ExactRef("fixture-source", 1, "a".repeat(64)));
        var observations = new PlanningObservation(snapshot, List.of(), Set.of(operation), Set.of(), Optional.empty(),
                List.of(), Optional.empty(), Optional.empty(), false);
        var request = new PlanningRequest(before, source, "session-1", Instant.now().plusSeconds(30), observations);
        var command = new ActionCommand("fixture-action", before, source, request.sessionId(), operation,
                new OpportunityJson.Obj(Map.of()), new ExpectedPostcondition(1, before, source, "fixture-observer/v1",
                        List.of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), true))),
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), request.deadline());
        var draft = new OrdinaryPolicy.Draft("source-selected-query", "original-query", "software proposal only", OrdinaryPolicy.Kind.ORDINARY,
                Optional.of(command), OrdinaryPolicy.Purpose.READ_ONLY, Optional.empty(), new OpportunityJson.Obj(Map.of()));
        return new Input(request, new PlanningResult.ActionSelected(command, new PlanTrace(request.before(), List.of(), Optional.of(draft))));
    }
    private static OpportunityJson.IntegerValue integer(long value) { return new OpportunityJson.IntegerValue(BigInteger.valueOf(value)); }
    private static CompletableFuture<Path> respond(Path queue, Set<String> ignored, Consumer<ObjectNode> change, String decision) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                long until = System.nanoTime() + TimeUnit.SECONDS.toNanos(10);
                while (System.nanoTime() < until) {
                    if (Files.isDirectory(queue)) try (var entries = Files.list(queue)) {
                        var requests = entries.filter(Files::isDirectory).filter(path -> !ignored.contains(path.getFileName().toString()))
                                .map(path -> path.resolve("request.json")).filter(Files::isRegularFile)
                                .filter(path -> !Files.exists(path.getParent().resolve("archived.json"))).toList();
                        if (!requests.isEmpty()) {
                            Path file = requests.getFirst(); byte[] bytes = Files.readAllBytes(file);
                            ObjectNode response = response(FullJsonTree.parse(bytes, 16384), bytes, decision);
                            change.accept(response); writeResponse(file, response); return file;
                        }
                    }
                    Thread.sleep(10);
                }
                throw new IllegalStateException("fixture did not receive an original Codex file request");
            } catch (Exception failure) { throw new java.util.concurrent.CompletionException(failure); }
        });
    }
    private static ObjectNode response(JsonNode request, byte[] bytes, String decision) {
        ObjectNode response = StrictJson.object().put("schema", "xar.ordinary-codex-file-response/v1")
                .put("request_id", request.path("request_id").textValue()).put("request_sha256", ActionCodec.sha256(bytes));
        response.set("selection", StrictJson.object().put("decision", decision).put("proposal_id", request.path("proposal_id").textValue())
                .put("body_sha256", request.path("body_sha256").textValue()).put("reason", "reviewed original proposal"));
        return response;
    }
    private static void writeResponse(Path request, ObjectNode response) throws Exception {
        Path target = request.getParent().resolve("response.json"), temporary = target.resolveSibling("response.tmp");
        Files.write(temporary, FullJsonTree.encode(response, 262144));
        Files.move(temporary, target, StandardCopyOption.ATOMIC_MOVE);
    }
    private static JsonNode tree(Path path) throws Exception { return FullJsonTree.parse(Files.readAllBytes(path), 64 * 1024 * 1024); }
    private static byte[] read(Path path) {
        try { return Files.readAllBytes(path); } catch (Exception failure) { throw new IllegalStateException(failure); }
    }
    private static Path onlyRequest(Path root) throws Exception {
        try (var entries = Files.list(root)) {
            return entries.filter(Files::isDirectory).map(path -> path.resolve("request.json")).filter(Files::isRegularFile).findFirst().orElseThrow();
        }
    }
}
