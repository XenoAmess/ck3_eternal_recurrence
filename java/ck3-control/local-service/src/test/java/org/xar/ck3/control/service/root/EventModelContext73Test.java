package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.lang.reflect.Field;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.http.HttpClient;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryDecisionSelector;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanTrace;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalFact;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalState;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.UnknownScope;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** Real public selector and loopback SSE. No provider, Native, game, issuer or action submission. */
final class EventModelContext73Test {
    private static final int MATERIAL = 16 * 1024 * 1024;
    private static final int WIRE_BOUND = 262144;
    private static final String FIXTURE_SHA = "43910f65b1db692796bb9e06296defbf193aec74e83d1d494bdb6974ce5dd88c";
    private static final Path FIXTURE = Path.of(System.getProperty("event73.fixture",
            "src/test/resources/event-model-context73.json"));

    @Test @Timeout(30)
    void actualPreparedEventBoundsTheWholeWireAndRetainsFullOriginals(@TempDir Path root) throws Exception {
        Fixture f = fixture(true);
        byte[] beforeCommand = ActionCodec.encodeCommand(f.command());
        byte[] beforeSnapshot = OpportunityJson.encode(f.request().observations().snapshot());
        byte[] beforeHistory = historyBytes(f.request());
        assertTrue(beforeHistory.length > 1048576, "the ignored history really exceeds the provider input cap");
        try (Stub model = new Stub(); Client client = client(model, root, f)) {
            model.reply.set(reply(f.command()));
            var result = client.selector.select(f.request(), f.selected());
            assertEquals(OrdinaryDecisionSelector.Choice.ACCEPT, result.choice(), result.reason());
            model.assertHealthy();
            assertEquals(1, model.calls.get());
            byte[] wire = model.requests.getFirst();
            assertTrue(wire.length <= WIRE_BOUND, "bound the complete HTTP body, including system policy and escaping");
            JsonNode payload = tree(wire);
            JsonNode data = userData(payload);
            assertEquals("xar.model-event-admission/v1", data.path("decision_context_schema").textValue());
            assertEquals("event_admission/v1", data.path("decision_scope").textValue());
            assertTrue(data.path("projection_scope").textValue().contains("not lossless"));
            assertEquals(tree(beforeCommand), data.get("proposal"));
            assertEquals(f.command().actionId(), data.path("proposal_id").textValue());
            assertEquals(ActionCodec.bodySha256(f.command()), data.path("body_sha256").textValue());
            assertEquals(f.request().deadline().toString(), data.path("planning_deadline").textValue());
            assertEquals(tree(beforeSnapshot), data.get("snapshot"), "all current unknown, option and capability fields stay intact");
            assertFalse(data.has("history"), "this task projection must not send unrelated full history");
            assertFalse(data.has("root_facts"));
            assertFalse(new String(wire, StandardCharsets.UTF_8).contains("irrelevant-history-marker-"));
            assertEquals(expectedFacts(f.request()), data.get("action_facts"));
            assertEquals(strings(f.request().observations().bridgeCapabilities().stream().sorted().toList()), data.get("capabilities"));
            assertEquals(strings(f.request().observations().actionSteps().stream().map(Object::toString).sorted().toList()), data.get("routable_operations"));
            JsonNode original = null;
            ExactRef originalRef = null;
            for (var entry : client.materials.entrySet()) {
                JsonNode retained = tree(entry.getValue());
                // Source73 preserves the complete legacy HTTP wire, whose user content contains the context.
                JsonNode retainedContext = retained.has("messages") ? userData(retained) : retained;
                JsonNode fullContext = findOriginalContext(retainedContext, tree(beforeHistory), tree(beforeSnapshot), tree(beforeCommand));
                if (fullContext != null) { original = fullContext; originalRef = entry.getKey(); }
                assertArrayEquals(entry.getValue(), Files.readAllBytes(Path.of(entry.getKey().path())));
                assertEquals(entry.getValue().length, entry.getKey().bytes());
                assertEquals(ActionCodec.sha256(entry.getValue()), entry.getKey().sha256());
            }
            assertNotNull(original, "one archived full original context must preserve unprojected history, snapshot and command together");
            assertNotNull(originalRef);
            assertEquals(originalRef, ExactRef.fromJson(data.get("original_model_input")));
            assertTrue(contains(data, tree(FullJsonTree.encode(originalRef.toJson(), MATERIAL))), "bounded request is tied to the exact full original material");
            assertEquals(expectedFacts(f.request()), original.get("action_facts"));
            assertTrue(result.evidence().isPresent());
            assertTrue(client.materials.containsKey(result.evidence().orElseThrow()));
            String policy = payload.path("messages").get(0).path("content").textValue();
            assertTrue(policy.toLowerCase(java.util.Locale.ROOT).contains("not lossless"));
            assertTrue(policy.contains("WAIT"));
            assertArrayEquals(beforeCommand, ActionCodec.encodeCommand(f.command()));
            assertArrayEquals(beforeSnapshot, OpportunityJson.encode(f.request().observations().snapshot()));
            assertArrayEquals(beforeHistory, historyBytes(f.request()));
        }
        assertFixtureUnchanged();
    }

    @Test @Timeout(30)
    void preparedEventStillRejectsChangedIdentityAndAdditionalInstructions(@TempDir Path root) throws Exception {
        Fixture f = fixture(false);
        try (Stub model = new Stub(); Client client = client(model, root, f)) {
            for (String fault : List.of("id", "sha", "extra", "alternative")) {
                ObjectNode bad = reply(f.command());
                switch (fault) {
                    case "id" -> bad.put("proposal_id", "other-proposal");
                    case "sha" -> bad.put("body_sha256", "0".repeat(64));
                    case "extra" -> bad.putObject("arguments").put("native_option_index", 2);
                    case "alternative" -> bad.put("decision", "SELECT_ALTERNATIVE");
                    default -> throw new AssertionError(fault);
                }
                model.reply.set(bad);
                var result = client.selector.select(f.request(), f.selected());
                assertEquals(OrdinaryDecisionSelector.Choice.WAIT, result.choice(), fault + ": " + result.reason());
                assertTrue(result.reason().startsWith("model_invalid_selection:"), result.reason());
            }
            model.assertHealthy();
            assertEquals(4, model.calls.get(), "each malformed response actually traversed the unchanged SSE validator");
            for (byte[] wire : model.requests) assertTrue(wire.length <= WIRE_BOUND);
        }
    }

    @Test @Timeout(30)
    void oversizedPreparedEventWaitsBeforeHttpAndNonEventKeepsItsOriginalRoute(@TempDir Path root) throws Exception {
        Fixture f = fixture(false);
        Obj huge = f.request().observations().snapshot().with("unrelated_large_current_fact",
                new OpportunityJson.Text("retained-current-fact:" + "x".repeat(WIRE_BOUND)));
        PlanningRequest oversized = withSnapshot(f, huge);
        try (Stub model = new Stub(); Client client = client(model, root, f)) {
            model.reply.set(reply(f.command()));
            var waiting = client.selector.select(oversized, f.selected());
            assertEquals(OrdinaryDecisionSelector.Choice.WAIT, waiting.choice(), waiting.reason());
            assertEquals(0, model.calls.get(), "never fall back to an unbounded event HTTP request");
            // A derived public DATA negative case, never a replacement for the frozen real command.
            ActionCommand unsupportedCommand = new ActionCommand(f.command().actionId(), f.command().origin(), f.command().source(),
                    f.command().sessionId(), f.command().operation(), f.command().arguments().with("phase",
                            new OpportunityJson.Text("unsupported_future_event_phase")), f.command().expectation(),
                    f.command().claims(), f.command().deadline());
            var unsupported = selected(f.request(), unsupportedCommand, "unsupported_future_event_phase", OrdinaryPolicy.Kind.FOREGROUND);
            model.reply.set(reply(unsupportedCommand));
            var unsupportedResult = client.selector.select(f.request(), unsupported);
            assertEquals(OrdinaryDecisionSelector.Choice.WAIT, unsupportedResult.choice(), unsupportedResult.reason());
            assertEquals(0, model.calls.get(), "unsupported event task must not silently fall back to the full-history route");
            // The same public DTO route for a non-event operation must retain the complete generic history.
            ActionCommand original = f.command();
            ActionCommand ordinary = new ActionCommand(original.actionId(), original.origin(), original.source(),
                    original.sessionId(), new OperationKey("query-campaign-root-context-v1"), original.arguments(),
                    original.expectation(), original.claims(), original.deadline());
            Fixture other = new Fixture(f.request(), ordinary, selected(f.request(), ordinary, "ordinary-public-query", OrdinaryPolicy.Kind.ORDINARY));
            model.reply.set(reply(ordinary));
            var accepted = client.selector.select(other.request(), other.selected());
            assertEquals(OrdinaryDecisionSelector.Choice.ACCEPT, accepted.choice(), accepted.reason());
            model.assertHealthy();
            assertEquals(1, model.calls.get());
            JsonNode data = userData(tree(model.requests.getFirst()));
            assertEquals(tree(historyBytes(other.request())), data.get("history"));
            assertEquals(tree(ActionCodec.encodeCommand(ordinary)), data.get("proposal"));
            assertEquals("xar.model-root-history-dictionary/v1", data.path("history_projection_schema").textValue());
        }
    }

    private record Fixture(PlanningRequest request, ActionCommand command, PlanningResult.ActionSelected selected) { }

    private static Fixture fixture(boolean largeHistory) throws IOException {
        byte[] input = Files.readAllBytes(FIXTURE);
        assertEquals(101045, input.length); assertEquals(FIXTURE_SHA, ActionCodec.sha256(input));
        JsonNode document = tree(input);
        JsonNode original = document.get("decision_originals");
        ActionCommand command = ActionCodec.decodeCommand(FullJsonTree.encode(original.get("proposal"), ActionCodec.MAX_COMMAND_BYTES));
        assertEquals(original.path("proposal_id").textValue(), command.actionId());
        assertEquals(original.path("body_sha256").textValue(), ActionCodec.bodySha256(command));
        Obj snapshot = object(document.get("current_snapshot_without_history"));
        List<Obj> history = new ArrayList<>();
        for (JsonNode row : document.get("relevant_event_rows")) history.add(object(row.get("row")));
        if (largeHistory) {
            for (int i = 0; i < 40; i++) {
                var row = StrictJson.object(); row.put("index", 1000 + i); row.put("command", "unrelated-software-read");
                row.put("ok", false); row.putObject("result").put("unknown_detail", "irrelevant-history-marker-" + i + ":" + "q".repeat(32768));
                history.add(object(row));
            }
        }
        Set<String> capabilities = new LinkedHashSet<>();
        for (JsonNode value : document.path("current_snapshot_without_history").path("diagnostics").path("hello").path("capabilities")) capabilities.add(value.textValue());
        Set<OperationKey> steps = Set.of(command.operation(), new OperationKey("pause-map"), new OperationKey("query-campaign-root-context-v1"));
        ExternalFact settled = new ExternalFact("software-original-rejected-fact", "e".repeat(64), command.before(),
                ExternalState.REJECTED_CONFIRMED, UnknownScope.GLOBAL, Domain.lifestyle, command.claims(), command.source().sourceRef());
        PlanningObservation observations = new PlanningObservation(snapshot, history, steps, capabilities, Optional.empty(),
                List.of(settled), Optional.empty(), Optional.empty(), false);
        PlanningRequest request = new PlanningRequest(command.before(), command.source(), command.sessionId(),
                Instant.parse(original.path("planning_deadline").textValue()), observations);
        return new Fixture(request, command, selected(request, command, OpportunityJson.text(command.arguments().get("phase"), "phase"), OrdinaryPolicy.Kind.FOREGROUND));
    }

    private static PlanningResult.ActionSelected selected(PlanningRequest request, ActionCommand command, String phase, OrdinaryPolicy.Kind kind) {
        OrdinaryPolicy.Draft draft = new OrdinaryPolicy.Draft("one-life-turn-v1", phase, "original prepared event proposal", kind,
                Optional.of(command), OrdinaryPolicy.Purpose.WORLD_ACTION, Optional.empty(), command.arguments());
        var visit = new PlanTrace.StageVisit(PlanningStage.TERMINAL_AND_FOREGROUND_WINDOWS, PlanTrace.Outcome.REPLACED,
                "original prepared event proposal", Optional.of(command.source().sourceRef()), Optional.of(command.arguments()));
        return new PlanningResult.ActionSelected(command, new PlanTrace(request.before(), List.of(visit), Optional.of(draft)));
    }

    private static PlanningRequest withSnapshot(Fixture f, Obj snapshot) {
        PlanningObservation old = f.request().observations();
        return new PlanningRequest(f.request().before(), f.request().source(), f.request().sessionId(), f.request().deadline(),
                new PlanningObservation(snapshot, old.history(), old.actionSteps(), old.bridgeCapabilities(), old.battleSpeedReadiness(),
                        old.actionFacts(), old.campaignGoal(), old.crossRunPlan(), old.initialLifestyleFocusRequired()));
    }
    private static byte[] historyBytes(PlanningRequest request) {
        return OpportunityJson.encode(new OpportunityJson.Arr(new ArrayList<OpportunityJson.Value>(request.observations().history())));
    }
    private static Obj object(JsonNode node) {
        return OpportunityJson.object(OpportunityJson.parse(FullJsonTree.encode(node, MATERIAL)), "software original object");
    }
    private static JsonNode tree(byte[] raw) { return FullJsonTree.parse(raw, MATERIAL); }
    private static JsonNode userData(JsonNode wire) {
        return tree(wire.path("messages").get(1).path("content").textValue().getBytes(StandardCharsets.UTF_8));
    }
    private static ArrayNode strings(List<String> values) {
        ArrayNode result = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.arrayNode(); values.forEach(result::add); return result;
    }
    private static ArrayNode expectedFacts(PlanningRequest request) {
        ArrayNode result = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.arrayNode();
        for (ExternalFact fact : request.observations().actionFacts()) {
            ObjectNode item = result.addObject(); item.put("action_id", fact.actionId()); item.put("body_sha256", fact.bodySha256());
            item.put("state", fact.state().name()); item.put("unresolved", fact.unresolved()); item.put("scope", fact.scope().name());
            item.put("domain", String.valueOf(fact.domain())); item.set("affected_claims", ActionCodec.claims(fact.affectedClaims()));
        }
        return result;
    }
    private static JsonNode findOriginalContext(JsonNode node, JsonNode history, JsonNode snapshot, JsonNode command) {
        if (node != null && node.isObject() && history.equals(node.get("history"))
                && snapshot.equals(node.get("snapshot")) && command.equals(node.get("proposal"))) return node;
        if (node != null && node.isContainerNode()) {
            for (JsonNode child : node) {
                JsonNode found = findOriginalContext(child, history, snapshot, command);
                if (found != null) return found;
            }
        }
        return null;
    }
    private static boolean contains(JsonNode container, JsonNode expected) {
        if (expected.equals(container)) return true;
        if (container != null && container.isContainerNode()) for (JsonNode child : container) if (contains(child, expected)) return true;
        return false;
    }
    private static ObjectNode reply(ActionCommand command) {
        ObjectNode result = StrictJson.object(); result.put("decision", "SELECT_PROPOSAL"); result.put("proposal_id", command.actionId());
        result.put("body_sha256", ActionCodec.bodySha256(command)); result.put("reason", "select original prepared option"); return result;
    }
    private static void assertFixtureUnchanged() throws IOException {
        byte[] input = Files.readAllBytes(FIXTURE); assertEquals(101045, input.length); assertEquals(FIXTURE_SHA, ActionCodec.sha256(input));
    }

    private static Client client(Stub model, Path root, Fixture f) {
        return new Client(model, root, Clock.fixed(f.request().deadline().minusSeconds(60), ZoneOffset.UTC));
    }
    private static final class Client implements AutoCloseable {
        private final Map<ExactRef, byte[]> materials = new LinkedHashMap<>();
        private final RootOnlineDecisionSelector selector;
        Client(Stub model, Path root, Clock clock) {
            selector = new RootOnlineDecisionSelector(new RootOrdinaryRuntimeConfiguration.DecisionProvider(model.endpoint(),
                    "local-stub-event-regression", Duration.ofSeconds(10), 1, Duration.ZERO), clock, raw -> {
                byte[] bytes = raw.bytes(); Path file = root.resolve("material-" + materials.size() + ".json");
                Files.write(file, bytes, StandardOpenOption.CREATE_NEW);
                ExactRef ref = new ExactRef(file.toAbsolutePath().toString(), bytes.length, ActionCodec.sha256(bytes));
                materials.put(ref, bytes); return ref;
            });
        }
        @Override public void close() throws ReflectiveOperationException {
            // Resource cleanup only. No private command, permit, token or projection method is invoked.
            Field field = RootOnlineDecisionSelector.class.getDeclaredField("http"); field.setAccessible(true);
            ((HttpClient) field.get(selector)).close();
        }
    }
    private static final class Stub implements AutoCloseable {
        private final HttpServer server;
        private final ExecutorService workers = Executors.newVirtualThreadPerTaskExecutor();
        private final AtomicReference<ObjectNode> reply = new AtomicReference<>();
        private final AtomicInteger calls = new AtomicInteger();
        private final AtomicReference<Throwable> failure = new AtomicReference<>();
        private final List<byte[]> requests = new ArrayList<>();
        Stub() throws IOException {
            server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0); server.setExecutor(workers);
            server.createContext("/v1/chat/completions", this::handle); server.start();
        }
        URI endpoint() { return URI.create("http://127.0.0.1:" + server.getAddress().getPort() + "/v1"); }
        private void handle(HttpExchange exchange) throws IOException {
            try {
                assertEquals("POST", exchange.getRequestMethod());
                byte[] raw = exchange.getRequestBody().readNBytes(MATERIAL + 1); requests.add(raw); calls.incrementAndGet();
                tree(raw);
                exchange.getResponseHeaders().set("Content-Type", "text/event-stream; charset=UTF-8");
                exchange.sendResponseHeaders(200, 0);
                ObjectNode frame = StrictJson.object(); frame.putArray("choices").addObject().putObject("delta").put("content", reply.get().toString());
                exchange.getResponseBody().write(("data: " + frame + "\n\n").getBytes(StandardCharsets.UTF_8));
                ObjectNode finish = StrictJson.object(); var choice = finish.putArray("choices").addObject();
                choice.putObject("delta"); choice.put("finish_reason", "stop");
                exchange.getResponseBody().write(("data: " + finish + "\n\ndata: [DONE]\n\n").getBytes(StandardCharsets.UTF_8));
                exchange.getResponseBody().flush();
            } catch (Throwable problem) {
                failure.compareAndSet(null, problem);
                if (problem instanceof IOException io) throw io;
            } finally { exchange.close(); }
        }
        void assertHealthy() { assertNull(failure.get(), () -> String.valueOf(failure.get())); }
        @Override public void close() { server.stop(0); workers.shutdownNow(); }
    }
}
