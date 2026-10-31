package org.xar.ck3.control.application.planning;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.xar.ck3.control.application.planning.PlanningFixtures.SOURCE;

import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
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
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmUnavailable;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.RootOnlineDecisionSelector;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.service.root.RootOrdinaryRuntimeConfiguration;

/** Real HTTP provider/planner/M7 consumers with explicit software proposals; no Native or canonical submit. */
class OnlineOrdinaryDecisionSelectorTest {
    private record Fixture(OrdinaryPlanner planner, RealmLifecycle realm, PlanningRequest request,
            ActionCommand command, OrdinaryPolicy.Draft draft) { }
    private record Reply(String inner, long contentDelayMillis, String finishReason) {
        private Reply(String inner, long contentDelayMillis) { this(inner, contentDelayMillis, "stop"); }
    }

    @Test void streamedSelectionRetainsTheOriginalCommandAndRealmDraft(@TempDir Path root) throws Exception {
        Fixture fixture = fixture(false);
        try (LocalModel model = new LocalModel()) {
            model.reply.set(new Reply(inner(fixture.command(), "SELECT_PROPOSAL").toString(), 0));
            var selector = provider(model, root, Duration.ofSeconds(2));
            AtomicReference<PlanningResult.ActionSelected> original = new AtomicReference<>();
            fixture.planner().bindSelector((request, proposal) -> {
                original.set(proposal);
                return selector.select(request, proposal);
            });
            String before = ActionCodec.bodySha256(fixture.command());
            PlanningResult evaluated = fixture.planner().plan(fixture.request());
            var selected = assertInstanceOf(PlanningResult.ActionSelected.class, evaluated,
                    evaluated instanceof PlanningResult.ReadOnlyWait waiting ? waiting.reason() : evaluated.toString());
            assertSame(fixture.command(), original.get().command());
            assertSame(fixture.draft(), original.get().trace().finalPlan().orElseThrow());
            assertSame(fixture.command(), selected.command());
            assertSame(fixture.draft(), selected.trace().finalPlan().orElseThrow());
            assertEquals(before, ActionCodec.bodySha256(selected.command()));
            assertEquals(1, model.calls.get());
            assertTrue(model.request.get().path("stream").isBoolean());
            assertTrue(model.request.get().path("stream").booleanValue());
            assertTrue(model.request.get().path("stream_options").path("include_usage").booleanValue());
            assertEquals("qwen38-coder", model.request.get().path("model").textValue());
            assertTrue(selected.trace().visits().stream().anyMatch(visit -> visit.evidence()
                    .map(value -> value.get("model_decision_receipt") != null).orElse(false)),
                    "actual model decision receipt is attached to the existing stage evidence");
            try (var material = Files.list(root)) {
                assertTrue(material.findAny().isPresent(), "the real material sink preserved HTTP decision data");
            }
            assertEquals("original_query_not_confirmed", completion(fixture));
            assertEquals("original_query_plan_slot_unavailable", completion(fixture));
        }
    }

    @Test void waitAndInvalidModelRepliesLeaveNoRealmPublication(@TempDir Path root) throws Exception {
        try (LocalModel model = new LocalModel()) {
            List<String> faults = List.of("wait", "wrong-id", "wrong-sha", "extra-native-args", "bool-decision",
                    "malformed", "invalid-accept-enum");
            for (String fault : faults) {
                Fixture fixture = fixture(false);
                ObjectNode json = inner(fixture.command(), "SELECT_PROPOSAL");
                String raw;
                switch (fault) {
                    case "wait" -> json.put("decision", "WAIT");
                    case "wrong-id" -> json.put("proposal_id", "a-different-proposal");
                    case "wrong-sha" -> json.put("body_sha256", "0".repeat(64));
                    case "extra-native-args" -> json.putObject("native_args").put("target", 777);
                    case "bool-decision" -> json.put("decision", true);
                    case "invalid-accept-enum" -> json.put("decision", "ACCEPT");
                    case "malformed" -> { }
                    default -> throw new AssertionError(fault);
                }
                raw = fault.equals("malformed") ? "{unfinished-model-json" : json.toString();
                model.reply.set(new Reply(raw, 0));
                fixture.planner().bindSelector(provider(model, root.resolve(fault), Duration.ofSeconds(2)));
                assertWait(fixture, fixture.planner().plan(fixture.request()));
            }
            assertEquals(faults.size(), model.calls.get(), "every case reached the actual HTTP provider");
        }
    }

    @Test @Timeout(6)
    void delayedStreamContentAndIoFailureWaitWithoutStagingTheOriginalQuery(@TempDir Path root) throws Exception {
        Fixture delayed = fixture(false);
        try (LocalModel model = new LocalModel()) {
            model.reply.set(new Reply(inner(delayed.command(), "SELECT_PROPOSAL").toString(), 1_500));
            delayed.planner().bindSelector(provider(model, root.resolve("timeout"), Duration.ofMillis(500)));
            long started = System.nanoTime();
            assertWait(delayed, delayed.planner().plan(delayed.request()));
            assertTrue(Duration.ofNanos(System.nanoTime() - started).compareTo(Duration.ofSeconds(3)) < 0,
                    "stream content must respect the finite operation budget after headers arrive");
            assertEquals(1, model.headersSent.get(), "the timeout case actually received headers and an empty delta");
        }
        Fixture unavailable = fixture(false);
        LocalModel closed = new LocalModel();
        RootOnlineDecisionSelector selector;
        try { selector = provider(closed, root.resolve("io"), Duration.ofMillis(500)); }
        finally { closed.close(); }
        unavailable.planner().bindSelector(selector);
        assertWait(unavailable, unavailable.planner().plan(unavailable.request()));
    }

    @Test void aNonActionPlanningResultDoesNotAskTheModel(@TempDir Path root) throws Exception {
        Fixture fixture = fixture(true);
        try (LocalModel model = new LocalModel()) {
            AtomicInteger selected = new AtomicInteger();
            var actual = provider(model, root, Duration.ofSeconds(2));
            fixture.planner().bindSelector((request, proposal) -> {
                selected.incrementAndGet();
                return actual.select(request, proposal);
            });
            var waiting = assertInstanceOf(PlanningResult.ReadOnlyWait.class, fixture.planner().plan(fixture.request()));
            assertEquals("existing software read-only wait", waiting.reason());
            assertEquals(0, selected.get());
            assertEquals(0, model.calls.get());
            assertEquals("original_query_plan_slot_unavailable", completion(fixture));
        }
    }

    @Test void modelSnapshotDropsOnlyTheExactDuplicateAndRetainsAllOriginalHistory(@TempDir Path root) throws Exception {
        try (LocalModel model = new LocalModel()) {
            for (boolean equal : List.of(true, false)) {
                Fixture fixture = fixture(false);
                var row = new OpportunityJson.Obj(Map.of("read_id", new OpportunityJson.Text("controlled-complete-read"),
                        "original_response", new OpportunityJson.Obj(Map.of("raw_value", new OpportunityJson.Text("complete-original-response"))),
                        "wide_integer", new OpportunityJson.IntegerValue(new java.math.BigInteger("18446744073709551615"))));
                List<OpportunityJson.Obj> history = List.of(row);
                var complete = new OpportunityJson.Arr(List.of(row));
                var different = new OpportunityJson.Arr(List.of(row.with("read_id", new OpportunityJson.Text("another-original-read"))));
                var snapshot = fixture.request().observations().snapshot().with("native_command_history", equal ? complete : different);
                byte[] originalSnapshot = OpportunityJson.encode(snapshot), originalHistory = OpportunityJson.encode(complete);
                var old = fixture.request().observations();
                var observations = new PlanningObservation(snapshot, history, old.actionSteps(), old.bridgeCapabilities(),
                        old.battleSpeedReadiness(), old.actionFacts(), old.campaignGoal(), old.crossRunPlan(), old.initialLifestyleFocusRequired());
                var request = new PlanningRequest(fixture.request().before(), fixture.request().source(), fixture.request().sessionId(),
                        fixture.request().deadline(), observations);
                model.reply.set(new Reply(inner(fixture.command(), "SELECT_PROPOSAL").toString(), 0));
                fixture.planner().bindSelector(provider(model, root.resolve(equal ? "equal" : "unequal"), Duration.ofSeconds(2)));
                var selected = assertInstanceOf(PlanningResult.ActionSelected.class, fixture.planner().plan(request));
                assertSame(fixture.command(), selected.command());
                assertSame(fixture.draft(), selected.trace().finalPlan().orElseThrow());
                var sent = org.xar.ck3.control.contracts.FullJsonTree.parse(model.request.get().get("messages").get(1)
                        .get("content").textValue().getBytes(StandardCharsets.UTF_8), StrictJson.EXPLICIT_MAX_BYTES);
                assertEquals(org.xar.ck3.control.contracts.FullJsonTree.parse(originalHistory, StrictJson.EXPLICIT_MAX_BYTES), sent.get("history"));
                if (equal) assertTrue(!sent.get("snapshot").has("native_command_history"));
                else assertEquals(org.xar.ck3.control.contracts.FullJsonTree.parse(OpportunityJson.encode(different), StrictJson.EXPLICIT_MAX_BYTES),
                        sent.get("snapshot").get("native_command_history"));
                org.junit.jupiter.api.Assertions.assertArrayEquals(originalSnapshot, OpportunityJson.encode(request.observations().snapshot()));
                org.junit.jupiter.api.Assertions.assertArrayEquals(originalHistory, OpportunityJson.encode(
                        new OpportunityJson.Arr(new ArrayList<OpportunityJson.Value>(request.observations().history()))));
                assertEquals(ActionCodec.bodySha256(fixture.command()), sent.get("body_sha256").textValue());
            }
            assertEquals(2, model.calls.get());
        }
    }

    @Test void modelRootDictionaryIsLosslessAndLeavesUnknownRowsComplete(@TempDir Path root) throws Exception {
        Fixture fixture = fixture(false);
        ObjectNode first = StrictJson.object();
        first.put("command", "query-campaign-root-context-v1"); first.put("index", 1); first.put("ok", true);
        ObjectNode source = first.putObject("read_history_source");
        source.put("schema", "xar.driver-read-history-source/v1"); source.put("kind", "CAMPAIGN_ROOT_CONTEXT");
        source.put("payload_field", "campaign_root_context"); source.put("query_sequence", 19);
        ObjectNode frame = source.putObject("source_frame"); frame.put("machine_id", "explicit-software-frame");
        frame.putObject("game").put("pid", 17); frame.putObject("frame").put("native_revision", "18446744073709551615");
        source.putObject("decoder_source").put("path", "software-code-reference");
        source.putObject("definition_source").put("path", "software-native-code-reference");
        source.putObject("source").put("path", "software-implementation-source-reference");
        source.putObject("original_receipt").put("path", "software-original-metadata-retained");
        source.putArray("supporting_evidence").add("complete-software-evidence");
        ObjectNode result = first.putObject("result"); result.put("status", "available"); result.put("accepted", true);
        ObjectNode facts = result.putObject("campaign_root_context"); facts.put("status", "available");
        facts.put("snapshot_revision", new java.math.BigInteger("18446744073709551615"));
        facts.put("player_character_id", 1234); facts.put("treasury", 47);
        facts.putObject("provenance").put("source", "unknown-full-ROOT-field-retained");
        facts.putArray("future_fact").addNull().add(true).add(new java.math.BigInteger("18446744073709551614"));
        facts.putObject("player_heir_candidate_v1").put("snapshot_revision", new java.math.BigInteger("18446744073709551615"))
                .put("getter_rva", "complete-technical-root-data-retained");
        ObjectNode second = first.deepCopy(); second.put("index", 2);
        ((ObjectNode) second.get("result").get("campaign_root_context")).put("snapshot_revision", 98);
        ((ObjectNode) second.get("result").get("campaign_root_context").get("player_heir_candidate_v1")).put("snapshot_revision", 99);
        ((ObjectNode) second.get("read_history_source").get("source_frame").get("frame")).put("native_revision", "98");
        ObjectNode changed = first.deepCopy(); changed.put("index", 3);
        ((ObjectNode) changed.get("result").get("campaign_root_context")).put("treasury", 48);
        ObjectNode unknown = first.deepCopy(); unknown.put("index", 4); unknown.put("ok", false);
        ((ObjectNode) unknown.get("result")).put("status", "UNKNOWN");
        ObjectNode nonRead = first.deepCopy(); nonRead.put("index", 5); nonRead.put("command", "actual-non-read-operation");
        ObjectNode missingStamp = first.deepCopy(); missingStamp.put("index", 6);
        ((ObjectNode) missingStamp.get("result").get("campaign_root_context")).remove("snapshot_revision");
        ObjectNode boolStamp = first.deepCopy(); boolStamp.put("index", 7);
        ((ObjectNode) boolStamp.get("result").get("campaign_root_context").get("player_heir_candidate_v1")).put("snapshot_revision", true);
        ObjectNode missingOk = first.deepCopy(); missingOk.put("index", 8); missingOk.remove("ok");
        ObjectNode badFrame = first.deepCopy(); badFrame.put("index", 9);
        ((ObjectNode) badFrame.get("read_history_source")).putArray("source_frame").add("unfamiliar-shape");
        ObjectNode unfamiliar = first.deepCopy(); unfamiliar.put("index", 10); unfamiliar.put("unknown", true);
        List<ObjectNode> originals = List.of(first, second, changed, unknown, nonRead, missingStamp, boolStamp, missingOk, badFrame, unfamiliar);
        var history = new ArrayList<OpportunityJson.Obj>();
        for (var row : originals) history.add(OpportunityJson.object(OpportunityJson.parse(
                org.xar.ck3.control.contracts.FullJsonTree.encode(row, StrictJson.EXPLICIT_MAX_BYTES)), "software dictionary row DATA"));
        var complete = new OpportunityJson.Arr(new ArrayList<OpportunityJson.Value>(history));
        var snapshot = fixture.request().observations().snapshot().with("native_command_history", complete);
        byte[] beforeSnapshot = OpportunityJson.encode(snapshot), beforeHistory = OpportunityJson.encode(complete);
        var old = fixture.request().observations();
        var observations = new PlanningObservation(snapshot, history, old.actionSteps(), old.bridgeCapabilities(), old.battleSpeedReadiness(),
                old.actionFacts(), old.campaignGoal(), old.crossRunPlan(), old.initialLifestyleFocusRequired());
        var request = new PlanningRequest(fixture.request().before(), fixture.request().source(), fixture.request().sessionId(), fixture.request().deadline(), observations);
        try (LocalModel model = new LocalModel()) {
            model.reply.set(new Reply(inner(fixture.command(), "SELECT_PROPOSAL").toString(), 0));
            fixture.planner().bindSelector(provider(model, root, Duration.ofSeconds(2)));
            var selected = assertInstanceOf(PlanningResult.ActionSelected.class, fixture.planner().plan(request));
            assertSame(fixture.command(), selected.command()); assertSame(fixture.draft(), selected.trace().finalPlan().orElseThrow());
            var sent = org.xar.ck3.control.contracts.FullJsonTree.parse(model.request.get().get("messages").get(1).get("content")
                    .textValue().getBytes(StandardCharsets.UTF_8), StrictJson.EXPLICIT_MAX_BYTES);
            assertEquals("xar.model-root-history-dictionary/v1", sent.get("history_projection_schema").textValue());
            assertEquals(2, sent.get("root_facts").size()); assertEquals(10, sent.get("history").size());
            assertTrue(!sent.get("snapshot").has("native_command_history"), "exact duplicate is compared before dictionary projection");
            assertTrue(model.request.get().get("messages").get(0).get("content").textValue().contains("root_facts[root_ref]"));
            for (int index = 0; index < originals.size(); index++) {
                ObjectNode expanded = sent.get("history").get(index).deepCopy();
                if (index < 3) {
                    ObjectNode reference = (ObjectNode) expanded.get("result").get("campaign_root_context");
                    assertEquals(index == 2 ? 1 : 0, reference.get("root_ref").intValue());
                    ObjectNode restored = sent.get("root_facts").get(reference.get("root_ref").intValue()).deepCopy();
                    restored.set("snapshot_revision", reference.get("snapshot_revision"));
                    ((ObjectNode) restored.get("player_heir_candidate_v1")).set("snapshot_revision", reference.get("player_heir_candidate_v1_snapshot_revision"));
                    ((ObjectNode) expanded.get("result")).set("campaign_root_context", restored);
                }
                var expected = org.xar.ck3.control.contracts.FullJsonTree.parse(org.xar.ck3.control.contracts.FullJsonTree.encode(
                        originals.get(index), StrictJson.EXPLICIT_MAX_BYTES), StrictJson.EXPLICIT_MAX_BYTES);
                if (index < 3) ((ObjectNode) expected.get("read_history_source")).remove(List.of(
                        "decoder_source", "definition_source", "original_receipt", "supporting_evidence", "source"));
                assertEquals(expected, expanded, "all game facts/frame/unknown fields equal; only qualifying READ five technical refs omitted: " + index);
            }
            assertEquals(ActionCodec.bodySha256(fixture.command()), sent.get("body_sha256").textValue());
            assertEquals(org.xar.ck3.control.contracts.FullJsonTree.parse(ActionCodec.encodeCommand(fixture.command()), ActionCodec.MAX_COMMAND_BYTES), sent.get("proposal"));
            org.junit.jupiter.api.Assertions.assertArrayEquals(beforeSnapshot, OpportunityJson.encode(request.observations().snapshot()));
            org.junit.jupiter.api.Assertions.assertArrayEquals(beforeHistory, OpportunityJson.encode(new OpportunityJson.Arr(new ArrayList<OpportunityJson.Value>(request.observations().history()))));
        }
    }

    @Test void compactCompleteSelectionAcceptsButLengthTruncationNeverDispatches(@TempDir Path root) throws Exception {
        try (LocalModel model = new LocalModel()) {
            for (String transport : List.of("partial-length", "complete-length", "compact-stop")) {
                Fixture fixture = fixture(false);
                ObjectNode response = inner(fixture.command(), "SELECT_PROPOSAL");
                response.put("reason", "Legal focus ready.");
                String raw = response.toString();
                if (transport.equals("partial-length")) raw = raw.substring(0, raw.length() - 2);
                model.reply.set(new Reply(raw, 0, transport.equals("compact-stop") ? "stop" : "length"));
                fixture.planner().bindSelector(provider(model, root.resolve(transport), Duration.ofSeconds(2)));
                PlanningResult planned = fixture.planner().plan(fixture.request());
                if (transport.equals("compact-stop")) {
                    var selected = assertInstanceOf(PlanningResult.ActionSelected.class, planned);
                    assertSame(fixture.command(), selected.command());
                    assertSame(fixture.draft(), selected.trace().finalPlan().orElseThrow());
                    assertEquals("original_query_not_confirmed", completion(fixture));
                    assertEquals("original_query_plan_slot_unavailable", completion(fixture));
                } else assertWait(fixture, planned);
                var data = org.xar.ck3.control.contracts.FullJsonTree.parse(model.request.get().get("messages").get(1).get("content")
                        .textValue().getBytes(StandardCharsets.UTF_8), StrictJson.EXPLICIT_MAX_BYTES);
                var keys = new ArrayList<String>(); data.fieldNames().forEachRemaining(keys::add);
                assertEquals(List.of("history", "root_facts", "history_projection_schema", "capabilities", "routable_operations",
                        "action_facts", "snapshot", "proposal", "proposal_id", "body_sha256", "planning_deadline"), keys,
                        "complete stable data precedes all varying proposal fields with the exact original field set");
                assertEquals(org.xar.ck3.control.contracts.FullJsonTree.parse(OpportunityJson.encode(fixture.request().observations().snapshot()),
                        StrictJson.EXPLICIT_MAX_BYTES), data.get("snapshot"));
                assertTrue(fixture.request().observations().history().isEmpty() && data.get("history").isEmpty());
                assertTrue(data.get("root_facts").isEmpty());
                assertEquals("xar.model-root-history-dictionary/v1", data.get("history_projection_schema").textValue());
                var expected = StrictJson.object();
                var caps = expected.putArray("capabilities"); fixture.request().observations().bridgeCapabilities().stream().sorted().forEach(caps::add);
                var routes = expected.putArray("routable_operations"); fixture.request().observations().actionSteps().stream().map(step -> step.value()).sorted().forEach(routes::add);
                assertEquals(expected.get("capabilities"), data.get("capabilities")); assertEquals(expected.get("routable_operations"), data.get("routable_operations"));
                assertEquals(1, data.get("routable_operations").size());
                assertEquals(M7CampaignPolicies.FACTION_QUERY, data.get("routable_operations").get(0).textValue(),
                        "the model receives the exact native operation name instead of the record wrapper");
                assertEquals(data.get("proposal").get("operation"), data.get("routable_operations").get(0),
                        "the selected legal operation appears under the same exact wire name");
                assertTrue(fixture.request().observations().actionFacts().isEmpty() && data.get("action_facts").isEmpty());
                assertEquals(org.xar.ck3.control.contracts.FullJsonTree.parse(ActionCodec.encodeCommand(fixture.command()), ActionCodec.MAX_COMMAND_BYTES), data.get("proposal"));
                assertEquals(fixture.command().actionId(), data.get("proposal_id").textValue());
                assertEquals(ActionCodec.bodySha256(fixture.command()), data.get("body_sha256").textValue());
                assertEquals(fixture.request().deadline().toString(), data.get("planning_deadline").textValue());
                assertEquals(256, model.request.get().get("max_tokens").intValue(), "original finite token cap is unchanged");
                String policy = model.request.get().get("messages").get(0).get("content").textValue();
                assertTrue(policy.contains("compact") && policy.contains("reason"), "fixed prompt requests compact output");
                assertTrue(policy.contains("root_facts[root_ref]"), "existing complete dictionary interpretation remains");
            }
            assertEquals(3, model.calls.get(), "real Java HttpClient and SSE transport exercised all three terminal branches");
        }
    }

    private static RootOnlineDecisionSelector provider(LocalModel model, Path directory, Duration timeout)
            throws IOException {
        Files.createDirectories(directory);
        AtomicInteger materials = new AtomicInteger();
        return new RootOnlineDecisionSelector(new RootOrdinaryRuntimeConfiguration.DecisionProvider(
                model.endpoint(), "qwen38-coder", timeout, 1, Duration.ofMillis(1)), Clock.systemUTC(), raw -> {
                    Path path = directory.resolve("actual-http-material-" + materials.incrementAndGet() + ".json");
                    byte[] bytes = raw.bytes();
                    Files.write(path, bytes, StandardOpenOption.CREATE_NEW);
                    return new ExactRef(path.toAbsolutePath().toString(), bytes.length, ActionCodec.sha256(bytes));
                });
    }

    private static ObjectNode inner(ActionCommand command, String decision) {
        ObjectNode json = StrictJson.object();
        json.put("decision", decision);
        json.put("proposal_id", command.actionId());
        json.put("body_sha256", ActionCodec.bodySha256(command));
        json.put("reason", "explicit local HTTP test decision");
        return json;
    }

    private static void assertWait(Fixture fixture, PlanningResult result) {
        var waiting = assertInstanceOf(PlanningResult.ReadOnlyWait.class, result);
        assertTrue(!waiting.reason().isBlank());
        var draft = waiting.trace().finalPlan().orElseThrow();
        assertTrue(draft.command().isEmpty(), "WAIT cannot retain a dispatchable proposal command");
        assertEquals(OrdinaryPolicy.Purpose.READ_ONLY, draft.purpose());
        assertEquals("original_query_plan_slot_unavailable", completion(fixture));
    }

    /** Existing M7 test technique observes the real private pending slot without a Native result. */
    private static String completion(Fixture fixture) {
        var unknown = new ActionReceipt(1, 1, fixture.command(), ActionCodec.bodySha256(fixture.command()),
                new ActionState.Unknown(Optional.empty(), Optional.empty(), "software-unknown", List.of()));
        return assertInstanceOf(RealmUnavailable.class, fixture.realm().afterExecution(unknown)).reason();
    }

    private static Fixture fixture(boolean waitBeforeSelection) {
        return fixture(waitBeforeSelection, new OpportunityJson.Obj(Map.of()));
    }

    private static Fixture fixture(boolean waitBeforeSelection, OpportunityJson.Obj arguments) {
        var operation = new OperationKey(M7CampaignPolicies.FACTION_QUERY);
        var base = PlanningFixtures.request(PlanningFixtures.snapshot(), List.of(), Set.of(operation));
        var request = new PlanningRequest(base.before(), base.source(), base.sessionId(),
                Instant.now().plusSeconds(20), base.observations());
        var command = PlanningFixtures.command(request, operation, arguments);
        var draft = new OrdinaryPolicy.Draft("software-existing-query", "selected-original-query", "legal software proposal",
                OrdinaryPolicy.Kind.ORDINARY, Optional.of(command), OrdinaryPolicy.Purpose.READ_ONLY,
                Optional.empty(), new OpportunityJson.Obj(Map.of()));
        var realm = new RealmLifecycle(SOURCE);
        var stages = new ArrayList<OrdinaryPolicy>();
        for (var stage : PlanningStage.values()) {
            if (stage == PlanningStage.REALM_MEMBERSHIP_PUBLICATION) { stages.add(realm); continue; }
            stages.add(new OrdinaryPolicy() {
                @Override public PlanningStage stage() { return stage; }
                @Override public ExactRef implementationSource() { return SOURCE; }
                @Override public Decision evaluate(PlanningRequest ignored, Draft previous) {
                    if (stage != PlanningStage.ORDINARY_CORE) return new Keep("explicit software stage");
                    return waitBeforeSelection ? new Wait("existing software read-only wait")
                            : new Replace(draft, "retain this existing legal proposal");
                }
            });
        }
        return new Fixture(new OrdinaryPlanner(stages, Clock.systemUTC(), realm), realm, request, command, draft);
    }

    private static final class LocalModel implements AutoCloseable {
        private final HttpServer server;
        private final ExecutorService workers = Executors.newVirtualThreadPerTaskExecutor();
        private final AtomicReference<Reply> reply = new AtomicReference<>(new Reply("{}", 0));
        private final AtomicInteger calls = new AtomicInteger();
        private final AtomicInteger headersSent = new AtomicInteger();
        private final AtomicReference<ObjectNode> request = new AtomicReference<>();
        private final AtomicReference<String> usageJson = new AtomicReference<>("");
        private boolean closed;
        volatile java.util.concurrent.CountDownLatch requestReached;
        volatile java.util.concurrent.CountDownLatch releaseResponse;
        volatile boolean firstUnavailable;
        LocalModel() throws IOException {
            server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
            server.setExecutor(workers);
            server.createContext("/v1/chat/completions", this::handle);
            server.start();
        }
        URI endpoint() { return URI.create("http://127.0.0.1:" + server.getAddress().getPort() + "/v1"); }
        private void handle(HttpExchange exchange) throws IOException {
            try {
                byte[] raw = exchange.getRequestBody().readNBytes(StrictJson.EXPLICIT_MAX_BYTES + 1);
                request.set((ObjectNode) StrictJson.parse(raw, StrictJson.EXPLICIT_MAX_BYTES));
                int actualCall = calls.incrementAndGet();
                if (requestReached != null) requestReached.countDown();
                if (releaseResponse != null) {
                    try {
                        if (!releaseResponse.await(5, java.util.concurrent.TimeUnit.SECONDS)) throw new java.io.IOException("release timeout");
                    } catch (InterruptedException interrupted) {
                        Thread.currentThread().interrupt();
                        throw new java.io.IOException("release interrupted", interrupted);
                    }
                }
                if (firstUnavailable && actualCall == 1) {
                    exchange.sendResponseHeaders(503, -1);
                    return;
                }
                Reply planned = reply.get();
                exchange.getResponseHeaders().set("Content-Type", "text/event-stream; charset=UTF-8");
                exchange.sendResponseHeaders(200, 0);
                writeDelta(exchange, ""); // headers/empty delta are not a first nonempty model content.
                headersSent.incrementAndGet();
                if (planned.contentDelayMillis() > 0) {
                    try { Thread.sleep(planned.contentDelayMillis()); }
                    catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); return; }
                }
                int split = planned.inner().length() / 2;
                writeDelta(exchange, planned.inner().substring(0, split));
                writeDelta(exchange, planned.inner().substring(split));
                ObjectNode finish = StrictJson.object();
                ObjectNode choice = finish.putArray("choices").addObject();
                choice.putObject("delta");
                choice.put("finish_reason", planned.finishReason());
                exchange.getResponseBody().write(("data: " + finish + "\n\n").getBytes(StandardCharsets.UTF_8));
                String injectedUsage = usageJson.get();
                if (!injectedUsage.isEmpty()) {
                    exchange.getResponseBody().write(("data: " + injectedUsage + "\n\n").getBytes(StandardCharsets.UTF_8));
                } else {
                    ObjectNode usage = StrictJson.object();
                    usage.putArray("choices");
                    ObjectNode counts = usage.putObject("usage");
                    counts.put("prompt_tokens", 10);
                    counts.put("completion_tokens", 2);
                    counts.putObject("prompt_tokens_details").put("cached_tokens", 0);
                    exchange.getResponseBody().write(("data: " + usage + "\n\n").getBytes(StandardCharsets.UTF_8));
                }
                exchange.getResponseBody().write("data: [DONE]\n\n".getBytes(StandardCharsets.UTF_8));
                exchange.getResponseBody().flush();
            } finally { exchange.close(); }
        }
        private static void writeDelta(HttpExchange exchange, String content) throws IOException {
            ObjectNode frame = StrictJson.object();
            frame.putArray("choices").addObject().putObject("delta").put("content", content);
            exchange.getResponseBody().write(("data: " + frame + "\n\n").getBytes(StandardCharsets.UTF_8));
            exchange.getResponseBody().flush();
        }
        @Override public void close() {
            if (!closed) { closed = true; server.stop(0); workers.shutdownNow(); }
        }
    }

@Test @org.junit.jupiter.api.parallel.ResourceLock(org.junit.jupiter.api.parallel.Resources.SYSTEM_OUT)
void httpProgressBeginsBeforeResponseAndEndsBeforeArchive(@TempDir Path root) throws Exception {
    Fixture fixture = fixture(false);
    java.io.PrintStream originalOut = System.out;
    java.io.ByteArrayOutputStream capture = new java.io.ByteArrayOutputStream();
    java.util.concurrent.CountDownLatch requestReached = new java.util.concurrent.CountDownLatch(1);
    java.util.concurrent.CountDownLatch releaseResponse = new java.util.concurrent.CountDownLatch(1);
    java.util.concurrent.ExecutorService executor = java.util.concurrent.Executors.newVirtualThreadPerTaskExecutor();
    java.util.concurrent.Future<PlanningResult> future = null;
    LocalModel model = null;
    try {
        System.setOut(new java.io.PrintStream(capture, true, StandardCharsets.UTF_8));
        model = new LocalModel();
        model.requestReached = requestReached;
        model.releaseResponse = releaseResponse;
        ObjectNode reply = inner(fixture.command(), "SELECT_PROPOSAL");
        reply.put("reason", "sensitive-marker-no-stdout");
        model.reply.set(new Reply(reply.toString(), 0));
        var selector = new RootOnlineDecisionSelector(new RootOrdinaryRuntimeConfiguration.DecisionProvider(
                model.endpoint(), "qwen38-coder", Duration.ofSeconds(5), 1, Duration.ZERO), Clock.systemUTC(), raw -> {
            var material = FullJsonTree.parse(raw.bytes(), org.xar.ck3.control.application.action.RawJson.MAXIMUM_BYTES);
            if ("xar.ordinary-model-http-attempt/v1".equals(material.path("schema").asText())) {
                var progress = capture.toString(StandardCharsets.UTF_8).lines().filter(line -> !line.isBlank())
                        .map(line -> StrictJson.parse(line.getBytes(StandardCharsets.UTF_8), StrictJson.EXPLICIT_MAX_BYTES)).toList();
                assertEquals(2, progress.size(), "actual END precedes attempt material I/O");
                assertEquals("ORDINARY_MODEL_HTTP_END", progress.get(1).get("status").textValue());
            }
            byte[] bytes = raw.bytes();
            Path path = root.resolve("http-progress-material-" + java.util.UUID.randomUUID() + ".json");
            Files.write(path, bytes, java.nio.file.StandardOpenOption.CREATE_NEW);
            return new ExactRef(path.toAbsolutePath().toString(), bytes.length, ActionCodec.sha256(bytes));
        });
        fixture.planner().bindSelector((request, proposal) -> selector.select(request, proposal));
        future = executor.submit(() -> fixture.planner().plan(fixture.request()));
        assertTrue(requestReached.await(5, java.util.concurrent.TimeUnit.SECONDS), "HTTP handler reached before response");
        var lines = capture.toString(java.nio.charset.StandardCharsets.UTF_8).lines().filter(l -> !l.isBlank())
                .map(l -> (ObjectNode) org.xar.ck3.control.contracts.StrictJson.parse(l.getBytes(java.nio.charset.StandardCharsets.UTF_8), org.xar.ck3.control.contracts.StrictJson.EXPLICIT_MAX_BYTES)).toList();
        assertEquals(1, lines.size(), "exactly one BEGIN event before response");
        var begin = lines.get(0);
        assertEquals("xar.ordinary-model-http-progress/v1", begin.get("schema").textValue());
        assertEquals("ORDINARY_MODEL_HTTP_BEGIN", begin.get("status").textValue());
        assertEquals(fixture.command().origin().machineId(), begin.get("machine_id").textValue());
        assertEquals(fixture.command().actionId(), begin.get("proposal_id").textValue());
        assertEquals(1, begin.get("attempt").intValue());
        assertEquals(model.endpoint().toString() + "/chat/completions", begin.get("endpoint").textValue());
        assertEquals("qwen38-coder", begin.get("model").textValue());
        java.time.Instant.parse(begin.get("started_at_utc").textValue());
        java.time.Instant.parse(begin.get("deadline_utc").textValue());
        assertTrue(begin.get("payload_bytes").intValue() > 0);
        assertTrue(!begin.has("proposal") && !begin.has("messages") && !begin.has("history") && !begin.has("snapshot") && !begin.has("wire_base64") && !begin.has("content") && !begin.has("reason"));
        assertTrue(!future.isDone(), "planner blocked waiting for response");
        releaseResponse.countDown();
        var planned = future.get(5, java.util.concurrent.TimeUnit.SECONDS);
        var selected = assertInstanceOf(PlanningResult.ActionSelected.class, planned);
        assertSame(fixture.command(), selected.command());
        assertSame(fixture.draft(), selected.trace().finalPlan().orElseThrow());
        var finalLines = capture.toString(java.nio.charset.StandardCharsets.UTF_8).lines().filter(l -> !l.isBlank())
                .map(l -> (ObjectNode) org.xar.ck3.control.contracts.StrictJson.parse(l.getBytes(java.nio.charset.StandardCharsets.UTF_8), org.xar.ck3.control.contracts.StrictJson.EXPLICIT_MAX_BYTES)).toList();
        assertEquals(2, finalLines.size(), "one BEGIN and one END event");
        var end = finalLines.get(1);
        assertEquals("ORDINARY_MODEL_HTTP_END", end.get("status").textValue());
        assertEquals(begin.get("machine_id"), end.get("machine_id"));
        assertEquals(begin.get("proposal_id"), end.get("proposal_id"));
        assertEquals(begin.get("attempt"), end.get("attempt"));
        assertEquals(begin.get("endpoint"), end.get("endpoint"));
        assertEquals(begin.get("model"), end.get("model"));
        assertEquals(begin.get("started_at_utc"), end.get("started_at_utc"));
        assertEquals(begin.get("deadline_utc"), end.get("deadline_utc"));
        assertEquals(begin.get("payload_bytes"), end.get("payload_bytes"));
        assertEquals(200, end.get("http_status").intValue());
        assertTrue(end.get("complete").booleanValue());
        assertTrue(!end.get("transient_failure").booleanValue());
        assertTrue(end.get("total_ms").longValue() >= 0);
        if (!end.get("headers_ms").isNull()) assertTrue(end.get("headers_ms").longValue() >= 0);
        if (!end.get("ttft_ms").isNull()) assertTrue(end.get("ttft_ms").longValue() >= 0);
        assertTrue(!end.has("proposal") && !end.has("messages") && !end.has("history") && !end.has("snapshot") && !end.has("wire_base64") && !end.has("content") && !end.has("reason"));
        assertTrue(!capture.toString(StandardCharsets.UTF_8).contains("sensitive-marker-no-stdout"), "payload stays out of progress");
        boolean markerPreserved = false;
        try (var files = Files.list(root)) {
            for (Path file : files.toList()) {
                if (Files.readString(file, StandardCharsets.UTF_8).contains("sensitive-marker-no-stdout")) markerPreserved = true;
            }
        }
        assertTrue(markerPreserved, "normal response materials retain original evidence");
    } finally {
        System.setOut(originalOut);
        if (releaseResponse != null) releaseResponse.countDown();
        if (model != null) model.close();
        if (executor != null) executor.shutdownNow();
    }
}

@Test @org.junit.jupiter.api.parallel.ResourceLock(org.junit.jupiter.api.parallel.Resources.SYSTEM_OUT)
void httpProgressPairsActualRetryAndSkipsExpiredRequest(@TempDir Path root) throws Exception {
    Fixture fixture = fixture(false);
    java.io.PrintStream originalOut = System.out;
    try (LocalModel model = new LocalModel()) {
        model.firstUnavailable = true;
        model.reply.set(new Reply(inner(fixture.command(), "SELECT_PROPOSAL").toString(), 0));
        java.io.ByteArrayOutputStream capture = new java.io.ByteArrayOutputStream();
        System.setOut(new java.io.PrintStream(capture, true, StandardCharsets.UTF_8));
        var selector = new RootOnlineDecisionSelector(new RootOrdinaryRuntimeConfiguration.DecisionProvider(
                model.endpoint(), "qwen38-coder", Duration.ofSeconds(5), 2, Duration.ofMillis(1)), Clock.systemUTC(),
                raw -> {
                    Path path = root.resolve("retry-material-" + java.util.UUID.randomUUID() + ".json");
                    byte[] bytes = raw.bytes();
                    Files.write(path, bytes, java.nio.file.StandardOpenOption.CREATE_NEW);
                    return new ExactRef(path.toAbsolutePath().toString(), bytes.length, ActionCodec.sha256(bytes));
                });
        fixture.planner().bindSelector(selector);
        var planned = fixture.planner().plan(fixture.request());
        var selected = assertInstanceOf(PlanningResult.ActionSelected.class, planned);
        assertSame(fixture.command(), selected.command());
        assertSame(fixture.draft(), selected.trace().finalPlan().orElseThrow());
        assertEquals(2, model.calls.get());
        String log = capture.toString(StandardCharsets.UTF_8);
        var lines = log.split("\n");
        assertEquals(4, lines.length);
        var e1 = FullJsonTree.parse(lines[0].getBytes(StandardCharsets.UTF_8), StrictJson.EXPLICIT_MAX_BYTES);
        var e2 = FullJsonTree.parse(lines[1].getBytes(StandardCharsets.UTF_8), StrictJson.EXPLICIT_MAX_BYTES);
        var e3 = FullJsonTree.parse(lines[2].getBytes(StandardCharsets.UTF_8), StrictJson.EXPLICIT_MAX_BYTES);
        var e4 = FullJsonTree.parse(lines[3].getBytes(StandardCharsets.UTF_8), StrictJson.EXPLICIT_MAX_BYTES);
        assertEquals("xar.ordinary-model-http-progress/v1", e1.get("schema").textValue());
        assertEquals("ORDINARY_MODEL_HTTP_BEGIN", e1.get("status").textValue());
        assertEquals("ORDINARY_MODEL_HTTP_END", e2.get("status").textValue());
        assertEquals("ORDINARY_MODEL_HTTP_BEGIN", e3.get("status").textValue());
        assertEquals("ORDINARY_MODEL_HTTP_END", e4.get("status").textValue());
        assertEquals(1, e1.get("attempt").intValue()); assertEquals(2, e3.get("attempt").intValue());
        assertEquals(e1.get("machine_id"), e2.get("machine_id")); assertEquals(e1.get("machine_id"), e3.get("machine_id"));
        assertEquals(e1.get("proposal_id"), e2.get("proposal_id")); assertEquals(e1.get("proposal_id"), e3.get("proposal_id"));
        assertEquals(e1.get("endpoint"), e2.get("endpoint")); assertEquals(e1.get("model"), e2.get("model"));
        assertEquals(e1.get("deadline_utc"), e2.get("deadline_utc")); assertEquals(e1.get("payload_bytes"), e2.get("payload_bytes"));
        assertEquals(e1.get("started_at_utc"), e2.get("started_at_utc"));
        assertEquals(e3.get("started_at_utc"), e4.get("started_at_utc"));
        for (String field : List.of("machine_id", "proposal_id", "endpoint", "model", "deadline_utc", "payload_bytes")) {
            assertEquals(e3.get(field), e4.get(field), "second attempt pair " + field);
        }
        assertEquals(503, e2.get("http_status").intValue()); assertTrue(e2.get("transient_failure").booleanValue());
        assertTrue(!e2.get("complete").booleanValue()); assertTrue(e2.get("headers_ms").isNumber()); assertTrue(e2.get("ttft_ms").isNull());
        assertEquals(200, e4.get("http_status").intValue()); assertTrue(e4.get("complete").booleanValue());
        assertTrue(!e4.get("transient_failure").booleanValue()); assertTrue(e4.get("headers_ms").isNumber());
        assertTrue(e4.get("ttft_ms").isNumber()); assertTrue(e4.get("total_ms").isNumber());
        for (var event : List.of(e1, e2, e3, e4)) {
            assertTrue(!event.has("proposal") && !event.has("content") && !event.has("reason") && !event.has("wire")
                    && !event.has("messages") && !event.has("prompt") && !event.has("history") && !event.has("snapshot"));
        }
        int logLength = capture.size();
        int callsBefore = model.calls.get();
        var expired = new PlanningRequest(fixture.request().before(), fixture.request().source(), fixture.request().sessionId(),
                Instant.now().minusSeconds(1), fixture.request().observations());
        var waitResult = selector.select(expired, selected);
        assertEquals(OrdinaryDecisionSelector.Choice.WAIT, waitResult.choice());
        assertEquals(logLength, capture.size());
        assertEquals(callsBefore, model.calls.get());
    } finally {
        System.setOut(originalOut);
    }
}

    @Test @org.junit.jupiter.api.parallel.ResourceLock(org.junit.jupiter.api.parallel.Resources.SYSTEM_OUT)
    void sseUsageMetricsCapturedInEndAndAttempt(@TempDir Path root) throws Exception {
        Fixture fixture = fixture(false);
        java.io.PrintStream originalOut = System.out;
        java.io.ByteArrayOutputStream capture = new java.io.ByteArrayOutputStream();
        java.util.concurrent.atomic.AtomicReference<ExactRef> archivedAttempt = new java.util.concurrent.atomic.AtomicReference<>();
        try {
            System.setOut(new java.io.PrintStream(capture, true, StandardCharsets.UTF_8));
            try (LocalModel model = new LocalModel()) {
                model.usageJson.set("{\"choices\":[],\"usage\":{\"prompt_tokens\":123456,\"completion_tokens\":789,\"total_tokens\":124245,\"prompt_tokens_details\":{\"cached_tokens\":0}}}");
                model.reply.set(new Reply(inner(fixture.command(), "SELECT_PROPOSAL").toString(), 0));
                var selector = new RootOnlineDecisionSelector(new RootOrdinaryRuntimeConfiguration.DecisionProvider(
                        model.endpoint(), "qwen38-coder", Duration.ofSeconds(5), 1, Duration.ZERO), Clock.systemUTC(), raw -> {
                    Path path = root.resolve("usage-material-" + java.util.UUID.randomUUID() + ".json");
                    Files.write(path, raw.bytes(), java.nio.file.StandardOpenOption.CREATE_NEW);
                    var ref = new ExactRef(path.toAbsolutePath().toString(), raw.bytes().length, ActionCodec.sha256(raw.bytes()));
                    var material = FullJsonTree.parse(raw.bytes(), org.xar.ck3.control.application.action.RawJson.MAXIMUM_BYTES);
                    if ("xar.ordinary-model-http-attempt/v1".equals(material.path("schema").asText())) {
                        archivedAttempt.set(ref);
                    }
                    return ref;
                });
                fixture.planner().bindSelector((request, proposal) -> selector.select(request, proposal));
                var planned = fixture.planner().plan(fixture.request());
                var selected = assertInstanceOf(PlanningResult.ActionSelected.class, planned);
                assertSame(fixture.command(), selected.command());
                assertSame(fixture.draft(), selected.trace().finalPlan().orElseThrow());
                assertEquals(1, model.calls.get(), "one real HTTP attempt");

                var lines = capture.toString(StandardCharsets.UTF_8).lines().filter(l -> !l.isBlank())
                        .map(l -> (ObjectNode) StrictJson.parse(l.getBytes(StandardCharsets.UTF_8), StrictJson.EXPLICIT_MAX_BYTES)).toList();
                assertEquals(2, lines.size(), "one BEGIN and one END event");
                var end = lines.get(1);
                assertEquals("ORDINARY_MODEL_HTTP_END", end.get("status").textValue());
                assertEquals(123456, end.get("prompt_tokens").intValue());
                assertEquals(789, end.get("completion_tokens").intValue());
                assertEquals(124245, end.get("total_tokens").intValue());
                assertEquals(0, end.get("cached_prompt_tokens_if_reported").intValue());
                assertTrue(!end.has("usage") && !end.has("content") && !end.has("wire_base64"));

                var attempt = archivedAttempt.get();
                assertTrue(attempt != null, "attempt archived");
                var attemptJson = FullJsonTree.parse(Files.readAllBytes(Path.of(attempt.path())), StrictJson.EXPLICIT_MAX_BYTES);
                assertEquals("xar.ordinary-model-http-attempt/v1", attemptJson.get("schema").textValue());
                assertEquals(123456, attemptJson.get("prompt_tokens").intValue());
                assertEquals(789, attemptJson.get("completion_tokens").intValue());
                assertEquals(124245, attemptJson.get("total_tokens").intValue());
                assertEquals(0, attemptJson.get("cached_prompt_tokens_if_reported").intValue());
            }
        } finally {
            System.setOut(originalOut);
        }
    }

    @Test @org.junit.jupiter.api.parallel.ResourceLock(org.junit.jupiter.api.parallel.Resources.SYSTEM_OUT)
    void malformedUsageDoesNotAlterSelectionOrMetrics(@TempDir Path root) throws Exception {
        java.io.PrintStream originalOut = System.out;
        try {
            java.io.ByteArrayOutputStream capture = new java.io.ByteArrayOutputStream();
            System.setOut(new java.io.PrintStream(capture, true, StandardCharsets.UTF_8));
            List<String> cases = List.of(
                "{\"choices\":[],\"usage\":{\"prompt_tokens\":\"string\",\"completion_tokens\":-1,\"total_tokens\":1.5,\"prompt_tokens_details\":\"bad\"}}",
                "{\"choices\":[]}",
                "{\"choices\":[],\"usage\":\"not-an-object\"}",
                "{\"choices\":[],\"usage\":{\"prompt_tokens\":9223372036854775808,\"completion_tokens\":true,\"total_tokens\":0,\"prompt_tokens_details\":{\"cached_tokens\":\"bad\"}}}",
                "{\"choices\":[],\"usage\":{\"prompt_tokens\":0,\"completion_tokens\":0,\"total_tokens\":0}}",
                "{\"choices\":[],\"usage\":{\"prompt_tokens\":5,\"completion_tokens\":6,\"total_tokens\":11,\"prompt_tokens_details\":{\"cached_tokens\":4}}}\n\ndata: {\"choices\":[],\"usage\":{\"prompt_tokens\":0}}"
            );
            List<List<Boolean>> expectedNulls = List.of(
                List.of(true, true, true, true),
                List.of(true, true, true, true),
                List.of(true, true, true, true),
                List.of(true, true, false, true),
                List.of(false, false, false, true),
                List.of(false, true, true, true)
            );
            for (int caseIndex = 0; caseIndex < cases.size(); caseIndex++) {
                Fixture fixture = fixture(false);
                try (LocalModel model = new LocalModel()) {
                    model.usageJson.set(cases.get(caseIndex));
                    model.reply.set(new Reply(inner(fixture.command(), "SELECT_PROPOSAL").toString(), 0));
                    var selector = new RootOnlineDecisionSelector(new RootOrdinaryRuntimeConfiguration.DecisionProvider(
                            model.endpoint(), "qwen38-coder", Duration.ofSeconds(5), 1, Duration.ZERO), Clock.systemUTC(), raw -> {
                        Path path = root.resolve("malformed-usage-material-" + java.util.UUID.randomUUID() + ".json");
                        Files.write(path, raw.bytes(), java.nio.file.StandardOpenOption.CREATE_NEW);
                        return new ExactRef(path.toAbsolutePath().toString(), raw.bytes().length, ActionCodec.sha256(raw.bytes()));
                    });
                    fixture.planner().bindSelector((request, proposal) -> selector.select(request, proposal));
                    var planned = fixture.planner().plan(fixture.request());
                    var selected = assertInstanceOf(PlanningResult.ActionSelected.class, planned);
                    assertSame(fixture.command(), selected.command());
                    assertSame(fixture.draft(), selected.trace().finalPlan().orElseThrow());
                    assertEquals(1, model.calls.get());

                    var lines = capture.toString(StandardCharsets.UTF_8).lines().filter(l -> !l.isBlank())
                            .map(l -> (ObjectNode) StrictJson.parse(l.getBytes(StandardCharsets.UTF_8), StrictJson.EXPLICIT_MAX_BYTES)).toList();
                    assertEquals(2 * (caseIndex + 1), lines.size(), "exactly one BEGIN and one END per actual call");
                    var end = lines.get(2 * caseIndex + 1);
                    assertEquals("ORDINARY_MODEL_HTTP_END", end.get("status").textValue());
                    assertEquals(expectedNulls.get(caseIndex).get(0), end.get("prompt_tokens").isNull(), "prompt_tokens null state case " + caseIndex);
                    assertEquals(expectedNulls.get(caseIndex).get(1), end.get("completion_tokens").isNull(), "completion_tokens null state case " + caseIndex);
                    assertEquals(expectedNulls.get(caseIndex).get(2), end.get("total_tokens").isNull(), "total_tokens null state case " + caseIndex);
                    assertEquals(expectedNulls.get(caseIndex).get(3), end.get("cached_prompt_tokens_if_reported").isNull(), "cached_prompt_tokens null state case " + caseIndex);
                    var metricFields = List.of("prompt_tokens", "completion_tokens", "total_tokens", "cached_prompt_tokens_if_reported");
                    for (int metric = 0; metric < metricFields.size(); metric++) {
                        if (!expectedNulls.get(caseIndex).get(metric))
                            assertEquals(0L, end.get(metricFields.get(metric)).longValue(), "reported zero must remain zero");
                    }
                }
            }
        } finally {
            System.setOut(originalOut);
        }
    }

    @Test void familyLegalityAliasProjectionPreservesCommandAndReconstructs(@TempDir Path root) throws Exception {
        var candidate1 = new OpportunityJson.Obj(Map.of("id", new OpportunityJson.IntegerValue(new java.math.BigInteger("18446744073709551615")), "name", new OpportunityJson.Text("UTF8-Test-Ünï")));
        var candidate2 = new OpportunityJson.Text("mixed-order");
        var candidate3 = new OpportunityJson.Bool(true);
        var candidates = new OpportunityJson.Arr(List.of(candidate1, candidate2, candidate3));
        var nativeLegalCandidates = new OpportunityJson.Arr(List.of(candidate1, candidate2, candidate3));
        var legality = new OpportunityJson.Obj(Map.of(
            "candidates", candidates,
            "native_legal_candidates", nativeLegalCandidates,
            "unknown_sibling", new OpportunityJson.Text("retain-me")
        ));
        var proof = new OpportunityJson.Obj(Map.of("family_marriage_legality", legality));
        var args = new OpportunityJson.Obj(Map.of("planning_proof", proof));
        Fixture fixture = fixture(false, args);
        byte[] originalCommandBytes = ActionCodec.encodeCommand(fixture.command());
        String originalBodySha = ActionCodec.bodySha256(fixture.command());
        try (LocalModel model = new LocalModel()) {
            model.reply.set(new Reply(inner(fixture.command(), "SELECT_PROPOSAL").toString(), 0));
            fixture.planner().bindSelector(provider(model, root, Duration.ofSeconds(2)));
            var selected = assertInstanceOf(PlanningResult.ActionSelected.class, fixture.planner().plan(fixture.request()));
            assertSame(fixture.command(), selected.command());
            assertSame(fixture.draft(), selected.trace().finalPlan().orElseThrow());
            assertEquals(1, model.calls.get());

            var sent = FullJsonTree.parse(model.request.get().get("messages").get(1).get("content").textValue().getBytes(StandardCharsets.UTF_8), StrictJson.EXPLICIT_MAX_BYTES);
            assertTrue(sent.has("proposal_projection_schema"), "equal complete arrays should be projected");
            assertEquals("xar.model-family-legality-alias/v1", sent.get("proposal_projection_schema").textValue());
            var proposal = sent.get("proposal");
            var projectedLegality = proposal.get("arguments").get("planning_proof").get("family_marriage_legality");
            assertTrue(projectedLegality.has("candidates"));
            assertTrue(!projectedLegality.has("native_legal_candidates"));

            org.junit.jupiter.api.Assertions.assertArrayEquals(originalCommandBytes, ActionCodec.encodeCommand(fixture.command()));
            assertEquals(originalBodySha, ActionCodec.bodySha256(fixture.command()));
            assertEquals(originalBodySha, sent.get("body_sha256").textValue());
            var originalCommand = FullJsonTree.parse(originalCommandBytes, ActionCodec.MAX_COMMAND_BYTES);
            var originalLegality = originalCommand.get("arguments").get("planning_proof").get("family_marriage_legality");
            assertEquals(originalLegality.get("candidates"), projectedLegality.get("candidates"));

            var reconstructed = proposal.deepCopy();
            ((ObjectNode) reconstructed.get("arguments").get("planning_proof").get("family_marriage_legality")).set("native_legal_candidates", projectedLegality.get("candidates").deepCopy());
            assertEquals(originalCommand, reconstructed);

            assertTrue(model.request.get().get("messages").get(0).get("content").textValue().contains("xar.model-family-legality-alias/v1"));
            assertTrue(model.request.get().get("messages").get(0).get("content").textValue().contains(
                    "proposal.arguments.planning_proof.family_marriage_legality.candidates"));
        }
    }

    @Test void familyLegalityAliasNegativeCasesLeaveProposalUnchanged(@TempDir Path root) throws Exception {
        List<OpportunityJson.Obj> negativeArgs = List.of(
            // Unequal items
            new OpportunityJson.Obj(Map.of("planning_proof", new OpportunityJson.Obj(Map.of("family_marriage_legality", new OpportunityJson.Obj(Map.of(
                "candidates", new OpportunityJson.Arr(List.of(new OpportunityJson.Text("a"))),
                "native_legal_candidates", new OpportunityJson.Arr(List.of(new OpportunityJson.Text("b")))
            )))))),
            // Unequal order
            new OpportunityJson.Obj(Map.of("planning_proof", new OpportunityJson.Obj(Map.of("family_marriage_legality", new OpportunityJson.Obj(Map.of(
                "candidates", new OpportunityJson.Arr(List.of(new OpportunityJson.Text("a"), new OpportunityJson.Text("b"))),
                "native_legal_candidates", new OpportunityJson.Arr(List.of(new OpportunityJson.Text("b"), new OpportunityJson.Text("a")))
            )))))),
            // Missing one array
            new OpportunityJson.Obj(Map.of("planning_proof", new OpportunityJson.Obj(Map.of("family_marriage_legality", new OpportunityJson.Obj(Map.of(
                "candidates", new OpportunityJson.Arr(List.of(new OpportunityJson.Text("a")))
            )))))),
            // Empty arrays
            new OpportunityJson.Obj(Map.of("planning_proof", new OpportunityJson.Obj(Map.of("family_marriage_legality", new OpportunityJson.Obj(Map.of(
                "candidates", new OpportunityJson.Arr(List.of()),
                "native_legal_candidates", new OpportunityJson.Arr(List.of())
            )))))),
            // Wrong type (object instead of array)
            new OpportunityJson.Obj(Map.of("planning_proof", new OpportunityJson.Obj(Map.of("family_marriage_legality", new OpportunityJson.Obj(Map.of(
                "candidates", new OpportunityJson.Obj(Map.of()),
                "native_legal_candidates", new OpportunityJson.Obj(Map.of())
            )))))),
            // Wrong target type (string instead of array) while candidates is valid nonempty array
            new OpportunityJson.Obj(Map.of("planning_proof", new OpportunityJson.Obj(Map.of("family_marriage_legality", new OpportunityJson.Obj(Map.of(
                "candidates", new OpportunityJson.Arr(List.of(new OpportunityJson.Text("a"))),
                "native_legal_candidates", new OpportunityJson.Text("not-an-array")
            ))))))
        );

        for (int caseIndex = 0; caseIndex < negativeArgs.size(); caseIndex++) {
            var args = negativeArgs.get(caseIndex);
            Fixture fixture = fixture(false, args);
            try (LocalModel model = new LocalModel()) {
                model.reply.set(new Reply(inner(fixture.command(), "SELECT_PROPOSAL").toString(), 0));
                fixture.planner().bindSelector(provider(model, root.resolve("family-negative-" + caseIndex), Duration.ofSeconds(2)));
                var planned = fixture.planner().plan(fixture.request());
                var selected = assertInstanceOf(PlanningResult.ActionSelected.class, planned,
                        planned instanceof PlanningResult.ReadOnlyWait waiting ? waiting.reason() : planned.toString());
                assertSame(fixture.command(), selected.command());
                assertSame(fixture.draft(), selected.trace().finalPlan().orElseThrow());
                assertEquals(1, model.calls.get());

                var sent = FullJsonTree.parse(model.request.get().get("messages").get(1).get("content").textValue().getBytes(StandardCharsets.UTF_8), StrictJson.EXPLICIT_MAX_BYTES);
                assertTrue(!sent.has("proposal_projection_schema"));
                assertEquals(args, fixture.command().arguments());
                assertEquals(ActionCodec.bodySha256(fixture.command()), sent.get("body_sha256").textValue());
                var proposal = sent.get("proposal");
                var original = FullJsonTree.parse(ActionCodec.encodeCommand(fixture.command()), ActionCodec.MAX_COMMAND_BYTES);
                assertEquals(original, proposal);
            }
        }
    }

    @Test @org.junit.jupiter.api.parallel.ResourceLock(org.junit.jupiter.api.parallel.Resources.SYSTEM_OUT)
    void httpProgressWriteFailureDoesNotChangeSelection(@TempDir Path root) throws Exception {
    var originalOut = System.out;
    try (LocalModel model = new LocalModel()) {
        Fixture fixture = fixture(false);
        model.reply.set(new Reply(inner(fixture.command(), "SELECT_PROPOSAL").toString(), 0));
        var selector = provider(model, root, Duration.ofSeconds(5));
        fixture.planner().bindSelector(selector);
        System.setOut(new java.io.PrintStream(new java.io.ByteArrayOutputStream(), true, StandardCharsets.UTF_8) {
            @Override public void write(byte[] bytes) throws java.io.IOException { throw new java.io.IOException("controlled log-only failure"); }
        });
        var result = fixture.planner().plan(fixture.request());
        var selected = assertInstanceOf(PlanningResult.ActionSelected.class, result);
        assertSame(fixture.command(), selected.command());
        assertSame(fixture.draft(), selected.trace().finalPlan().orElseThrow());
        assertEquals(1, model.calls.get());
        try (var files = Files.list(root)) { assertTrue(files.findAny().isPresent()); }
    } finally {
        System.setOut(originalOut);
    }
}
}
