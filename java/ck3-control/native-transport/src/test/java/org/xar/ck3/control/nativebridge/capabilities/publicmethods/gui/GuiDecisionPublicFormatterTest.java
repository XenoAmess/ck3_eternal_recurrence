package org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiContract.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiModels;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Pure DATA oracle/formatter boundary. Constructed receipt DATA is never a current Root qualification. */
final class GuiDecisionPublicFormatterTest {
    private static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    private static final String KEY = "ervc_courtier_creator_decision";
    private static RawJson raw(ObjectNode value) { return PublicDataJson.encode(value); }
    private static String sha(byte[] bytes) {
        try { return HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (java.security.NoSuchAlgorithmException impossible) { throw new AssertionError(impossible); }
    }
    private static ExactRef ref(String name, byte[] bytes) { return new ExactRef("software-data:" + name, bytes.length, sha(bytes)); }
    private static ExactRef ref(String name) { return ref(name, name.getBytes(StandardCharsets.UTF_8)); }
    private static OpportunityJson.Obj args(ObjectNode value) { return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(value)), "software arguments"); }
    private static GuiModels.Context context(ObjectNode before, GuiModels.Build build) {
        BigInteger actor = before.get("played_character").get("character_id").bigIntegerValue();
        JsonNode diagnostics = before.get("diagnostics");
        BigInteger generation = diagnostics.get("connection_generation").bigIntegerValue();
        int pid = diagnostics.path("hello").path("pid").isIntegralNumber() ? diagnostics.get("hello").get("pid").intValue() : 12700;
        var source = new G2Source("xenoamess-full-tower-eb9d2c1186", NOW.toString(), build.version(), ref("source"));
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(actor, before.get("native_revision").bigIntegerValue(),
                before.get("date_raw").bigIntegerValue()), before.get("snapshot_id").textValue(), before.get("revision").bigIntegerValue(), before.get("episode_run_id").textValue());
        var identity = new ObservationIdentity(source.machineId(), new GameGeneration(pid, new PythonOnlyUInt64(BigInteger.valueOf(133700000000000001L))), frame, 1);
        return new GuiModels.Context(identity, source, "software-data-session", generation, build, NOW.plusSeconds(60));
    }
    private static ObjectNode before() {
        ObjectNode value = StrictJson.object().put("revision", 1).put("native_revision", 7).put("snapshot_id", "synthetic-paused-7")
                .put("episode_run_id", "synthetic-decision-action-episode").put("paused", true).put("map_ready", true).put("date_raw", 1234);
        value.putObject("played_character").put("character_id", 7001).put("alive", true);
        value.putObject("diagnostics").put("connection_generation", 1).putObject("hello").put("pid", 12700);
        return value;
    }
    private static RawJson bundle(ObjectNode before) {
        ObjectNode out = StrictJson.object().put("schema", "xar.gui-before-public-source/v1");
        out.set("snapshot", before.deepCopy()); out.set("driver_diagnostics", before.get("diagnostics").deepCopy()); return raw(out);
    }
    private static Request request(Method method, String key, GuiModels.Context context, String outcome) {
        Arguments arguments = switch (method) {
            case OPEN_DECISIONS -> new Empty();
            case QUERY_DECISION, SELECT_DECISION -> new Decision(new GuiModels.DecisionKey(key));
            case CONFIRM_ITEM -> new ConfirmItem(new GuiModels.DecisionKey(key), GuiModels.TreeKind.WHITE);
            case CONFIRM_OUTCOME -> new ConfirmOutcome(new GuiModels.DecisionKey(key), GuiModels.Outcome.valueOf(outcome.toUpperCase(Locale.ROOT)),
                    outcome.equals("event_window") ? new Present<>("generic_events.100") : new Absent<>());
            case QUERY_WINDOW -> new WindowQuery("combat");
            default -> throw new AssertionError(method);
        };
        return new Request(method, arguments, new PublicUnsigned64.Value(context.before().frame().revision()));
    }
    private static String operation(Method method) {
        return switch (method) {
            case OPEN_DECISIONS -> "activate-ingame-decisions-v1";
            case QUERY_DECISION -> "query-ingame-decision-item-v1";
            case SELECT_DECISION -> "select-ingame-decision-item-v1";
            case CONFIRM_ITEM -> "confirm-ingame-decision-item-v1";
            case CONFIRM_OUTCOME -> "confirm-ingame-decision-outcome-v1";
            case QUERY_WINDOW -> "query-ingame-ui-window-v1";
            default -> throw new AssertionError(method);
        };
    }
    private static ObjectNode nativeArguments(Request request, GuiModels.Context c) {
        ObjectNode out = GuiCodec.encodeRequest(request); out.remove("expected_revision");
        if (request.arguments() instanceof ConfirmOutcome confirm && confirm.outcome() == GuiModels.Outcome.DECISION_CLOSED) out.put("expected_event_definition_key", "");
        out.put("_gui_build", c.build().name()).put("_gui_generation", c.connectionGeneration()); return out;
    }
    private static GuardEvidence guard(GuiModels.Context c, String operation) {
        return new GuardEvidence(c.before(), c.source(), c.sessionId(), c.connectionGeneration(), new OperationKey(operation), ref("native"), ref("capability"),
                "software-data-only", NOW, NOW.plusSeconds(60));
    }
    private static NativeActionPort.AckReceived ack(String id, RawJson token) {
        byte[] packet = StrictJson.canonical(StrictJson.object().put("request_id", id).put("ok", true));
        return new NativeActionPort.AckReceived(id, true, Optional.of(token), raw(StrictJson.object().put("software_data", true)), packet);
    }
    private static PlanningReadReceipt read(GuiModels.Context c, String op, ObjectNode arguments, RawJson original) {
        var request = new PlanningReadRequest(c.before(), c.source(), c.sessionId(), new OperationKey(op), args(arguments), c.deadline());
        var guard = new PlanningReadGuard(guard(c, op), true, true, true, "a".repeat(64));
        return new PlanningReadReceipt(request, "software-data:" + op, "original-read", guard, guard, ack("original-read", original));
    }
    private static ReadReply readReply(Request request, GuiModels.Context context, ObjectNode before, RawJson original) {
        return new ReadReply(read(context, operation(request.method()), nativeArguments(request, context), original), ref("read"), Optional.of(bundle(before)), Optional.empty());
    }
    private static ActionReply actionReply(Request request, GuiModels.Context c, ObjectNode before, RawJson original, RawJson later, String nativeId, boolean settled) {
        String operation = operation(request.method());
        var expected = new ExpectedPostcondition(1, c.before(), c.source(), "software.gui-observer/v1", List.of(new ExpectedBoolean(new FieldKey("gui.actual"), true)));
        var command = new ActionCommand("software-data-action", c.before(), c.source(), c.sessionId(), new OperationKey(operation), args(nativeArguments(request, c)), expected,
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), c.deadline());
        var attempt = new ActionState.Attempt(nativeId, NOW, guard(c, operation), new NativeRequest(operation, "game.command." + operation, raw(StrictJson.object())));
        var acknowledgement = ack(nativeId, original);
        ActionState state = settled ? new ActionState.Settled(attempt, acknowledgement,
                new ActionState.ControlApplied(read(c, "inspect-gui-window-tree-v1", StrictJson.object().put("window_kind", "decisions"), later), "software.gui-observer/v1", expected.values()))
                : new ActionState.Unknown(Optional.of(attempt), Optional.of(acknowledgement), "software original remains unknown", List.of(ref("unknown")));
        var receipt = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), state);
        // This is immutable formatter DATA, not an archive/writer or any permit.
        byte[] canonicalData = ActionCodec.encodeCommand(command);
        return new ActionReply(receipt, canonicalData, ref("canonical-data", canonicalData), Optional.of(bundle(before)), Optional.empty());
    }

    @Test void finiteFiveMethodOwnershipAndWrongBranchesFail() {
        Set<Method> owned = Set.of(Method.OPEN_DECISIONS, Method.QUERY_DECISION, Method.SELECT_DECISION, Method.CONFIRM_ITEM, Method.CONFIRM_OUTCOME);
        for (Method method : Method.values()) assertEquals(owned.contains(method), GuiDecisionPublicFormatter.supports(method));
        assertFalse(GuiDecisionPublicFormatter.supports(null));
        var c = context(before(), GuiModels.Build.CROZIER3); var q = request(Method.QUERY_DECISION, KEY, c, "");
        var reply = readReply(q, c, before(), raw(StrictJson.object().put("available", false).put("unavailable_reason", "actual hidden")));
        assertThrows(IllegalArgumentException.class, () -> GuiDecisionPublicFormatter.read(q, reply, Optional.empty()));
        var changed = new GuiModels.Context(c.before(), c.source(), "foreign-session", c.connectionGeneration(), c.build(), c.deadline());
        assertThrows(IllegalArgumentException.class, () -> GuiDecisionPublicFormatter.read(q, reply, Optional.of(changed)));
        assertThrows(IllegalArgumentException.class, () -> GuiDecisionPublicFormatter.read(request(Method.SELECT_DECISION, KEY, c, ""), reply, Optional.of(c)));
        assertThrows(IllegalArgumentException.class, () -> GuiDecisionPublicFormatter.read(request(Method.QUERY_WINDOW, KEY, c, ""), reply, Optional.of(c)));
        assertThrows(IllegalArgumentException.class, () -> GuiDecisionPublicFormatter.read(request(Method.QUERY_DECISION, "foreign_key", c, ""), reply, Optional.of(c)));
    }

    @Test void allDecisionsRequireTheRetainedBeforeSourceAndSharedParsedReferenceContract() {
        var c = context(before(), GuiModels.Build.CROZIER3);
        var request = request(Method.QUERY_DECISION, KEY, c, "");
        RawJson token = raw(StrictJson.object().put("schema", "ck3-ingame-decision-item-v1").put("decision_key", KEY));
        var reply = readReply(request, c, before(), token);
        var absent = new ReadReply(reply.receipt(), reply.originalReference(), Optional.empty(), Optional.empty());
        assertThrows(IllegalArgumentException.class, () -> GuiDecisionPublicFormatter.read(request, absent, Optional.of(c)));
        ObjectNode changed = before().deepCopy(); changed.put("snapshot_id", "foreign-before");
        var foreign = new ReadReply(reply.receipt(), reply.originalReference(), Optional.of(bundle(changed)), Optional.empty());
        assertThrows(IllegalArgumentException.class, () -> GuiDecisionPublicFormatter.read(request, foreign, Optional.of(c)));
        ObjectNode noDiagnostics = PublicDataJson.object(bundle(before())); noDiagnostics.remove("driver_diagnostics");
        var incomplete = new ReadReply(reply.receipt(), reply.originalReference(), Optional.of(raw(noDiagnostics)), Optional.empty());
        assertThrows(IllegalArgumentException.class, () -> GuiDecisionPublicFormatter.read(request, incomplete, Optional.of(c)));
        RawJson parsed = raw(StrictJson.object().put("path", "software-data:parsed").put("bytes", 1)
                .put("sha256", "a".repeat(64)).put("validation_state", "unvalidated"));
        var withParsed = new ReadReply(reply.receipt(), reply.originalReference(), reply.beforeSnapshot(), Optional.of(parsed));
        ObjectNode actual = PublicDataJson.object(GuiDecisionPublicFormatter.read(request, withParsed, Optional.of(c)));
        assertEquals(PublicDataJson.object(parsed), actual.get("native_ui_raw_return_receipt"));
        assertEquals(actual, PublicDataJson.object(GuiCodec.encodePublicOriginal(raw(actual))));
        var action = request(Method.OPEN_DECISIONS, KEY, c, "");
        var actionReply = actionReply(action, c, before(), raw(StrictJson.object().put("status", "actual_pending")), token, "native", false);
        var absentAction = new ActionReply(actionReply.receipt(), actionReply.archivedReceipt(), actionReply.originalReference(), Optional.empty(), Optional.empty());
        assertThrows(IllegalArgumentException.class, () -> GuiDecisionPublicFormatter.action(action, absentAction, c, Optional.empty(), Optional.empty()));
    }

    @Test void unknownKeepsOriginalFlagsAndNeverInventsSuccessfulPoststateOrFilesystemClaim() {
        var c = context(before(), GuiModels.Build.CROZIER3); var request = request(Method.OPEN_DECISIONS, KEY, c, "");
        RawJson original = raw(StrictJson.object().put("schema", "ck3-ingame-decisions-open-v1").put("postcondition_verified", false)
                .put("verification_pending", true).put("status", "actual_pending").put("custom_observation", "preserved"));
        var reply = actionReply(request, c, before(), original, raw(StrictJson.object()), "original-native-request", false);
        ObjectNode output = PublicDataJson.object(GuiDecisionPublicFormatter.action(request, reply, c, Optional.empty(), Optional.empty()));
        assertFalse(output.get("postcondition_verified").booleanValue()); assertTrue(output.get("verification_pending").booleanValue());
        assertEquals("actual_pending", output.get("status").textValue()); assertEquals("preserved", output.get("custom_observation").textValue());
        assertEquals("unresolved", output.get("canonical_gui_action").get("outcome").textValue());
        assertEquals("original-native-request", output.get("canonical_gui_action").get("native_request_id").textValue());
        assertFalse(output.has("action_claim_path")); assertFalse(output.has("later_decisions_tree")); assertFalse(output.has("action_request_id"));
        assertFalse(output.get("legacy_claim_path_available").booleanValue());
        assertThrows(IllegalArgumentException.class, () -> GuiDecisionPublicFormatter.action(request, reply, c, Optional.of(original), Optional.empty()));
    }

    @Test void successRequiresActualLaterAndOutcomeSnapshotAndRejectsForeignCanonicalBytes() {
        var c = context(before(), GuiModels.Build.CROZIER3); var request = request(Method.CONFIRM_OUTCOME, KEY, c, "decision_closed");
        RawJson token = raw(StrictJson.object().put("schema", "ck3-ingame-decision-outcome-confirm-v1").put("verification_pending", true));
        ObjectNode tree = StrictJson.object().put("schema", "ck3-native-gui-window-tree-inspection-v1").put("window_kind", "decision_detail")
                .put("root_available", false).put("truncated", false); tree.putArray("widgets");
        RawJson later = raw(tree);
        var reply = actionReply(request, c, before(), token, later, "actual-native-request", true);
        assertThrows(IllegalArgumentException.class, () -> GuiDecisionPublicFormatter.action(request, reply, c, Optional.empty(), Optional.empty()));
        assertThrows(IllegalArgumentException.class, () -> GuiDecisionPublicFormatter.action(request, reply, c, Optional.of(later), Optional.empty()));
        var changed = new ActionReply(reply.receipt(), new byte[]{1}, reply.originalReference(), reply.beforeSnapshot(), reply.parsedReturnReference());
        assertThrows(IllegalArgumentException.class, () -> GuiDecisionPublicFormatter.action(request, changed, c, Optional.of(later), Optional.of(raw(before()))));
        var empty = new ActionReply(reply.receipt(), new byte[0], ref("empty-canonical", new byte[0]), reply.beforeSnapshot(), reply.parsedReturnReference());
        assertThrows(IllegalArgumentException.class, () -> GuiDecisionPublicFormatter.action(request, empty, c, Optional.of(later), Optional.of(raw(before()))));
        var bad = raw(StrictJson.object().put("path", "foreign").put("bytes", 1).put("sha256", "a".repeat(64)).put("validation_state", "validated"));
        assertThrows(IllegalArgumentException.class, () -> new ActionReply(reply.receipt(), reply.archivedReceipt(), reply.originalReference(), reply.beforeSnapshot(), Optional.of(bad)));
    }

    @Test void ordinaryOutcomeRejectsProfileFourMarkerOrChangedAfterActor() {
        var c = context(before(), GuiModels.Build.CROZIER3);
        var request = request(Method.CONFIRM_OUTCOME, KEY, c, "decision_closed");
        RawJson token = raw(StrictJson.object().put("schema", "ck3-ingame-decision-outcome-confirm-v1"));
        ObjectNode tree = StrictJson.object().put("schema", "ck3-native-gui-window-tree-inspection-v1")
                .put("window_kind", "decision_detail").put("root_available", false).put("truncated", false);
        tree.putArray("widgets"); RawJson later = raw(tree);
        var reply = actionReply(request, c, before(), token, later, "actual-native-request", true);
        ObjectNode borrowed = before(); borrowed.putObject("xar_java_snapshot_projection").put("observation_version", 4);
        assertThrows(IllegalArgumentException.class, () -> GuiDecisionPublicFormatter.action(request, reply, c, Optional.of(later), Optional.of(raw(borrowed))));
        ObjectNode foreignActor = before(); ((ObjectNode) foreignActor.get("played_character")).put("character_id", 7002);
        assertThrows(IllegalArgumentException.class, () -> GuiDecisionPublicFormatter.action(request, reply, c, Optional.of(later), Optional.of(raw(foreignActor))));
    }

    @Test void mandatoryOriginalPythonFiveMethodsSixResponsesThroughFormatterAndPublicSerde() throws Exception {
        for (JsonNode item : originalOracle()) {
            ObjectNode row = (ObjectNode) item; Method method = Method.valueOf(row.get("method").textValue());
            ObjectNode originalBefore = (ObjectNode) row.get("before"); GuiModels.Build build = GuiModels.Build.valueOf(row.get("build").textValue());
            var c = context(originalBefore, build); String outcome = row.path("outcome").asText("");
            String key = row.path("key").asText(KEY); Request request = request(method, key, c, outcome);
            ObjectNode expected = ((ObjectNode) row.get("expected")).deepCopy(); RawJson formatted;
            if (!method.mutation()) {
                ReadReply reply = readReply(request, c, originalBefore, raw((ObjectNode) row.get("original")));
                formatted = GuiDecisionPublicFormatter.read(request, reply, Optional.of(c));
            } else {
                RawJson later = raw((ObjectNode) expected.get(method == Method.OPEN_DECISIONS ? "later_decisions_tree" : "later_actual_observation"));
                Optional<RawJson> snapshot = method == Method.CONFIRM_OUTCOME ? Optional.of(raw((ObjectNode) expected.get("snapshot_after"))) : Optional.empty();
                var reply = actionReply(request, c, originalBefore, raw((ObjectNode) row.get("original")), later, expected.get("action_request_id").textValue(), true);
                formatted = GuiDecisionPublicFormatter.action(request, reply, c, Optional.of(later), snapshot);
            }
            ObjectNode actual = PublicDataJson.object(formatted);
            if (method.mutation()) {
                assertFalse(actual.get("legacy_claim_path_available").booleanValue());
                assertEquals("xar.java.gui-canonical-action-reference/v1", actual.get("canonical_gui_action").get("schema").textValue());
                assertFalse(actual.has("action_claim_path")); expected.remove("action_claim_path");
                actual.remove(List.of("legacy_claim_path_available", "canonical_gui_action"));
            } else actual.remove("canonical_gui_read");
            equalPublic(expected, actual, "", method);
            assertEquals(actual, PublicDataJson.object(GuiCodec.encodePublicOriginal(raw(actual))));
        }
    }

    private static final Set<String> PUBLIC_INTEGER_ROLES = Set.of("connection_generation", "queried_connection_generation", "expected_connection_generation",
            "native_revision", "queried_native_revision", "revision", "queried_revision", "snapshot_revision", "query_sequence", "pump_epoch", "capture_epoch",
            "action_epoch", "later_epoch", "query_epoch", "observation_epoch", "game_creation_filetime", "process_creation_filetime", "observation_uptime_ms");
    private static void equalPublic(JsonNode original, JsonNode actual, String path, Method method) {
        assertNotNull(actual, method + " missing " + path);
        if (original.isObject()) {
            assertTrue(actual.isObject(), method + " object " + path); Set<String> oldNames = new HashSet<>(), newNames = new HashSet<>();
            original.fieldNames().forEachRemaining(oldNames::add); actual.fieldNames().forEachRemaining(newNames::add); assertEquals(oldNames, newNames, method + " fields " + path);
            original.fieldNames().forEachRemaining(key -> equalPublic(original.get(key), actual.get(key), path + "/" + key, method));
        } else if (original.isArray()) {
            assertTrue(actual.isArray()); assertEquals(original.size(), actual.size(), method + path);
            for (int i = 0; i < original.size(); i++) equalPublic(original.get(i), actual.get(i), path + "/" + i, method);
        } else if (original.isIntegralNumber() && actual.isTextual()) {
            assertTrue(PUBLIC_INTEGER_ROLES.contains(path.substring(path.lastIndexOf('/') + 1)), "undeclared integer conversion " + path);
            assertEquals(original.bigIntegerValue().toString(), actual.textValue(), method + path);
        } else if (original.isIntegralNumber() && actual.isIntegralNumber()) assertEquals(original.bigIntegerValue(), actual.bigIntegerValue(), method + path);
        else assertEquals(original, actual, method + path);
    }

    private static JsonNode originalOracle() throws Exception {
        Path root = requiredPath("xar.source.repository", true), python = requiredPath("xar.python", false);
        String program = """
            import copy,json,sys,tempfile
            from pathlib import Path
            root=Path(sys.argv[1]);sys.path[:0]=[str(root/'ck3_autonomous_player/src'),str(root/'ck3_autonomous_player/tests/unit')]
            import test_ingame_decisions_open_contract as O
            import test_ingame_decision_item_actions as I
            import test_ingame_decision_outcomes as E
            from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver as N
            from xar_autoplayer.bridge.ingame_decisions_open_contract import opening_binding
            rows=[]
            def save(method,before,original,expected,**extra):
                rows.append(dict(method=method,before=before,original=original,expected=expected,build='CROZIER3',**extra))
            with tempfile.TemporaryDirectory(prefix='gui-original-formatter-') as tmp:
                d=O.SyntheticDriver(Path(tmp)/'open');b=copy.deepcopy(d.frame)
                original_tree=d.inspect_gui_window_tree_v1
                def public_tree(kind):
                    value=original_tree(kind);value.update(schema='ck3-native-gui-window-tree-inspection-v1',window_kind=kind,read_only=True);return value
                d.inspect_gui_window_tree_v1=public_tree
                r=d.open_ingame_decisions_v1(expected_revision=1)
                save('OPEN_DECISIONS',b,copy.deepcopy(d.ack),r)
                for action,method in [('select','SELECT_DECISION'),('confirm','CONFIRM_ITEM')]:
                    d=I.SyntheticDriver(Path(tmp)/action,action=action);b=copy.deepcopy(d.frame)
                    r=d.select_ingame_decision_item_v1(I.KEY,expected_revision=1) if action=='select' else d.confirm_ingame_decision_item_v1(I.KEY,expected_window_kind='vivhite_courtier',expected_revision=1)
                    save(method,b,copy.deepcopy(d.native_ack),r,key=I.KEY)
                for outcome in ('event_window','decision_closed'):
                    d=E.OutcomeDriver(Path(tmp)/outcome,outcome);b=copy.deepcopy(d.frame)
                    r=d.confirm_ingame_decision_outcome_v1(E.KEY,expected_outcome=outcome,expected_event_definition_key=E.EVENT_KEY if outcome=='event_window' else None,expected_revision=1)
                    save('CONFIRM_OUTCOME',b,copy.deepcopy(d.native_ack),r,key=E.KEY,outcome=outcome)
                class Q:
                    query_ingame_decision_item_v1=N.query_ingame_decision_item_v1
                    def take_snapshot(self):return copy.deepcopy(I.frame())
                    def take_snapshot_without_native_command_history(self):return self.take_snapshot()
                    def capabilities(self):return {'bridge_capabilities':['game.command.query-ingame-decision-item-v1']}
                    def _execute_primitive_step(self,*a,**k):return copy.deepcopy(I.model(opening_binding(I.frame()),selected=True))
                q=Q();b=q.take_snapshot();original=q._execute_primitive_step();r=q.query_ingame_decision_item_v1(I.KEY,expected_revision=1)
                save('QUERY_DECISION',b,original,r,key=I.KEY)
            print(json.dumps(rows,separators=(',',':')))
            """;
        Path output = Files.createTempFile("gui-original-formatter-", ".json");
        try {
            var builder = new ProcessBuilder(python.toString(), "-B", "-X", "utf8", "-c", program, root.toString());
            builder.directory(root.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.environment().put("PYTHONUTF8", "1");
            builder.environment().put("PYTHONPATH", root.resolve("ck3_autonomous_player/src").toString());
            Process process = builder.redirectErrorStream(true).redirectOutput(output.toFile()).start();
            boolean ended = process.waitFor(45, TimeUnit.SECONDS); if (!ended) { process.destroyForcibly(); process.waitFor(5, TimeUnit.SECONDS); }
            assertTrue(ended, "original GUI producer oracle timed out"); byte[] bytes = Files.readAllBytes(output);
            assertEquals(0, process.exitValue(), new String(bytes, StandardCharsets.UTF_8)); JsonNode result = StrictJson.parse(bytes, StrictJson.EXPLICIT_MAX_BYTES);
            assertTrue(result.isArray()); assertEquals(6, result.size()); return result;
        } finally { Files.deleteIfExists(output); }
    }
    private static Path requiredPath(String property, boolean directory) throws java.io.IOException {
        String configured = System.getProperty(property); assertNotNull(configured, property + " mandatory; oracle never skipped");
        assertFalse(configured.isBlank()); Path value = Path.of(configured); assertTrue(value.isAbsolute()); Path actual = value.toRealPath();
        assertTrue(directory ? Files.isDirectory(actual) : Files.isRegularFile(actual), property + " actual input absent"); return actual;
    }
}
