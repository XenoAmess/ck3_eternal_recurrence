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
        CompletableFuture<Path> responder = respond(queue, Set.of(), request -> { }, "SELECT_PROPOSAL");
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
