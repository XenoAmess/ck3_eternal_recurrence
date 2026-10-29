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

/** Software formatter DATA only. These fixtures grant no current Native, Root or Game qualification. */
final class ArmyGuiPublicFormatterTest {
    private static final Instant NOW = Instant.parse("2026-10-24T19:00:00Z");
    private static final Set<Method> OWNED = Set.of(Method.OPEN_CHARACTER, Method.SELECT_ARMY, Method.HOVER_ARMY,
            Method.LEAVE_ARMY, Method.QUERY_ARMY, Method.OPEN_COMBAT, Method.FIT_COMBAT,
            Method.OPEN_KNIGHTS, Method.QUERY_WINDOW, Method.HOVER_KNIGHTS);
    private static RawJson raw(ObjectNode n) { return PublicDataJson.encode(n); }
    private static String sha(byte[] bytes) {
        try { return HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (java.security.NoSuchAlgorithmException impossible) { throw new AssertionError(impossible); }
    }
    private static ExactRef ref(String name, byte[] bytes) { return new ExactRef("software-data:" + name, bytes.length, sha(bytes)); }
    private static ExactRef ref(String name) { return ref(name, name.getBytes(StandardCharsets.UTF_8)); }
    private static OpportunityJson.Obj args(ObjectNode value) {
        return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(value)), "software GUI arguments");
    }
    private static ObjectNode before() {
        ObjectNode value = StrictJson.object().put("revision", 4).put("native_revision", 3).put("snapshot_id", "software-before-3")
                .put("episode_run_id", "software-army-episode").put("paused", true).put("map_ready", true).put("date_raw", 53146848);
        value.putObject("played_character").put("character_id", 29829).put("alive", true);
        value.putObject("diagnostics").put("connection_generation", 2); return value;
    }
    private static GuiModels.Context context(ObjectNode before, GuiModels.Build build) {
        var identity = new JointBudgetSelector.Frame(before.get("played_character").get("character_id").bigIntegerValue(),
                before.get("native_revision").bigIntegerValue(), before.get("date_raw").bigIntegerValue());
        var frame = new JointBudgetSelector.ProposalFrame(identity, before.get("snapshot_id").textValue(),
                before.get("revision").bigIntegerValue(), before.get("episode_run_id").textValue());
        var source = new G2Source("xenoamess-full-tower-eb9d2c1186", NOW.toString(), build.version(), ref("source"));
        var observed = new ObservationIdentity(source.machineId(), new GameGeneration(12700,
                new PythonOnlyUInt64(new BigInteger("133700000000000001"))), frame, 1);
        return new GuiModels.Context(observed, source, "software-army-session", BigInteger.TWO, build, NOW.plusSeconds(60));
    }
    private static RawJson bundle(ObjectNode before) {
        return GuiPublicMetadata.beforeSource(raw(before), raw((ObjectNode) before.get("diagnostics")));
    }
    private static Request request(Method method, GuiModels.Context c) {
        Arguments a = switch (method) {
            case OPEN_CHARACTER -> new Subject(new GuiModels.Subject(33437));
            case SELECT_ARMY -> new Subject(new GuiModels.Subject(0));
            case OPEN_COMBAT, FIT_COMBAT -> new Subject(new GuiModels.Subject(16777218));
            case OPEN_KNIGHTS -> new Empty();
            case HOVER_KNIGHTS -> new KnightHover(new GuiModels.Subject(16777218), GuiModels.Side.LEFT);
            case HOVER_ARMY, LEAVE_ARMY, QUERY_ARMY -> new ArmyTooltip(new GuiModels.Subject(0), GuiModels.TooltipKind.SUPPLY_STATE,
                    method == Method.HOVER_ARMY ? new Absent<>() : new Present<>(new GuiModels.ReceiptId("a".repeat(32))));
            case QUERY_WINDOW -> new WindowQuery("combat");
            default -> throw new AssertionError(method);
        };
        return new Request(method, a, new PublicUnsigned64.Value(c.before().frame().revision()));
    }
    private static ObjectNode nativeArguments(Request r, GuiModels.Context c) {
        ObjectNode n = StrictJson.object().put("_gui_build", c.build().name()).put("_gui_generation", c.connectionGeneration());
        String kind, operation; BigInteger subject;
        switch (r.method()) {
            case OPEN_CHARACTER -> { kind = "character"; operation = "open_character"; subject = ((Subject) r.arguments()).value().value(); }
            case SELECT_ARMY -> { kind = "army"; operation = "select_army"; subject = ((Subject) r.arguments()).value().value(); }
            case OPEN_COMBAT, FIT_COMBAT -> { kind = "combat"; operation = r.method() == Method.OPEN_COMBAT ? "open_combat" : "fit_combat_window"; subject = ((Subject) r.arguments()).value().value(); }
            case OPEN_KNIGHTS -> { kind = "knights"; operation = "open_knights"; subject = BigInteger.ZERO; }
            case HOVER_KNIGHTS -> { var v = (KnightHover) r.arguments(); kind = "combat"; operation = "hover_" + v.side().wire() + "_knights"; subject = v.combat().value(); }
            case HOVER_ARMY, LEAVE_ARMY, QUERY_ARMY -> {
                var v = (ArmyTooltip) r.arguments(); kind = "army"; subject = v.army().value();
                operation = r.method() == Method.HOVER_ARMY ? "hover_army_tooltip" : r.method() == Method.LEAVE_ARMY ? "leave_army_tooltip" : "query";
                n.put("army_tooltip_kind", v.kind().wire()); optional(v.receipt()).ifPresent(x -> n.put("army_tooltip_receipt", x.value()));
            }
            case QUERY_WINDOW -> { kind = ((WindowQuery) r.arguments()).kind(); operation = "query"; subject = BigInteger.ZERO; }
            default -> throw new AssertionError(r.method());
        }
        n.put("window_kind", kind).put("subject_id", subject); if (r.method().mutation()) n.put("operation", operation); return n;
    }
    private static RawJson token(Request r, GuiModels.Context c) {
        ObjectNode n = nativeArguments(r, c);
        return raw(StrictJson.object().put("schema", "ck3-ingame-ui-window-v1").put("window_kind", n.get("window_kind").textValue())
                .put("requested_subject_id", n.get("subject_id").bigIntegerValue()).put("native_revision", c.before().frame().identity().nativeRevision())
                .put("date_raw", c.before().frame().identity().dateRaw()).put("played_character_id", c.before().frame().identity().player())
                .put("status", r.method().mutation() ? "acknowledged_verification_pending" : "observed")
                .put("verification_pending", r.method().mutation()).put("dispatch_invoked", r.method().mutation()));
    }
    private static GuardEvidence guard(GuiModels.Context c, String op) {
        return new GuardEvidence(c.before(), c.source(), c.sessionId(), c.connectionGeneration(), new OperationKey(op), ref("native"), ref("capability"),
                "software-only", NOW, c.deadline());
    }
    private static NativeActionPort.AckReceived ack(RawJson token, boolean nativeOk) {
        return new NativeActionPort.AckReceived("software-request", nativeOk, Optional.of(token), raw(StrictJson.object().put("software_data", true)),
                StrictJson.canonical(StrictJson.object().put("request_id", "software-request").put("ok", nativeOk)));
    }
    private static PlanningReadReceipt receipt(Request r, GuiModels.Context c, RawJson token) {
        String op = "query-ingame-ui-window-v1";
        var request = new PlanningReadRequest(c.before(), c.source(), c.sessionId(), new OperationKey(op), args(nativeArguments(r, c)), c.deadline());
        var guard = new PlanningReadGuard(guard(c, op), true, true, true, "a".repeat(64));
        return new PlanningReadReceipt(request, "software-data:" + op, "software-request", guard, guard, ack(token, true));
    }
    private static Optional<RawJson> parsed(RawJson token) {
        JsonNode n = PublicDataJson.object(token).get("native_ui_raw_return_receipt");
        return n == null ? Optional.empty() : Optional.of(raw((ObjectNode) n));
    }
    private static ReadReply readReply(Request r, GuiModels.Context c, ObjectNode before, RawJson token) {
        return new ReadReply(receipt(r, c, token), ref("read"), Optional.of(bundle(before)), parsed(token));
    }
    private static ActionReply actionReply(Request r, GuiModels.Context c, ObjectNode before, RawJson token, boolean acknowledged, boolean settled) {
        String op = "navigate-ingame-ui-v1";
        var expected = new ExpectedPostcondition(1, c.before(), c.source(), "software.gui-observer/v1", List.of(new ExpectedBoolean(new FieldKey("gui.actual"), true)));
        var command = new ActionCommand("software-army-action", c.before(), c.source(), c.sessionId(), new OperationKey(op), args(nativeArguments(r, c)), expected,
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), c.deadline());
        var attempt = new ActionState.Attempt("software-request", NOW, guard(c, op), new NativeRequest(op, "game.command." + op, raw(StrictJson.object())));
        ActionState state = settled ? new ActionState.Settled(attempt, ack(token, true), new ActionState.ControlApplied(
                receipt(request(Method.QUERY_WINDOW, c), c, token), "software.gui-observer/v1", expected.values()))
                : new ActionState.Unknown(Optional.of(attempt), acknowledged ? Optional.of(ack(token, true)) : Optional.empty(), "software result unknown; no replay", List.of(ref("unknown")));
        var receipt = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), state);
        byte[] data = ActionCodec.encodeCommand(command);
        return new ActionReply(receipt, data, ref("canonical-data", data), Optional.of(bundle(before)), parsed(token));
    }

    @Test void tenMethodPartitionAndOriginalRequestSerdeAreExact() {
        for (Method m : Method.values()) assertEquals(OWNED.contains(m), ArmyGuiPublicFormatter.supports(m));
        assertFalse(ArmyGuiPublicFormatter.supports(null)); assertEquals(10, OWNED.size());
        var c = context(before(), GuiModels.Build.CROZIER3);
        for (Method m : OWNED) { Request r = request(m, c); assertEquals(r, GuiCodec.decode(m.originalName(), GuiCodec.encodeRequest(r))); }
        ObjectNode bool = GuiCodec.encodeRequest(request(Method.SELECT_ARMY, c)); bool.put("subject_army_id", true);
        assertThrows(IllegalArgumentException.class, () -> GuiCodec.decode(Method.SELECT_ARMY.originalName(), bool));
        ObjectNode missing = GuiCodec.encodeRequest(request(Method.QUERY_ARMY, c)); missing.remove("action_receipt");
        assertThrows(IllegalArgumentException.class, () -> GuiCodec.decode(Method.QUERY_ARMY.originalName(), missing));
    }

    @Test void realBeforeAndDriverGenerationAreRequiredWithoutHelloSubstitution() {
        var b = before(); var c = context(b, GuiModels.Build.CROZIER3); Request r = request(Method.QUERY_WINDOW, c);
        RawJson token = token(r, c); ReadReply reply = readReply(r, c, b, token);
        ObjectNode diagnostics = StrictJson.object().put("connection_generation", "18446744073709551615");
        ReadReply separate = new ReadReply(reply.receipt(), reply.originalReference(), Optional.of(GuiPublicMetadata.beforeSource(raw(b), raw(diagnostics))), Optional.empty());
        ObjectNode output = PublicDataJson.object(ArmyGuiPublicFormatter.read(r, separate, Optional.of(c)));
        assertEquals("18446744073709551615", output.get("queried_connection_generation").textValue());
        assertEquals("4", output.get("queried_revision").textValue()); assertEquals("3", output.get("queried_native_revision").textValue());
        assertThrows(IllegalArgumentException.class, () -> ArmyGuiPublicFormatter.read(r, reply, Optional.empty()));
        ReadReply absent = new ReadReply(reply.receipt(), reply.originalReference(), Optional.empty(), Optional.empty());
        assertThrows(IllegalArgumentException.class, () -> ArmyGuiPublicFormatter.read(r, absent, Optional.of(c)));
        ObjectNode stale = b.deepCopy(); stale.put("revision", 5);
        ReadReply changed = new ReadReply(reply.receipt(), reply.originalReference(), Optional.of(bundle(stale)), Optional.empty());
        assertThrows(IllegalArgumentException.class, () -> ArmyGuiPublicFormatter.read(r, changed, Optional.of(c)));
    }

    @Test void sameCallAckFlagsSurviveCanonicalConfirmationAndUnknownHasNoMadeUpRead() {
        var b = before(); var c = context(b, GuiModels.Build.CROZIER3); Request r = request(Method.SELECT_ARMY, c); RawJson token = token(r, c);
        for (boolean settled : List.of(false, true)) {
            ActionReply reply = actionReply(r, c, b, token, true, settled);
            ObjectNode out = PublicDataJson.object(ArmyGuiPublicFormatter.action(r, reply, c, Optional.empty(), Optional.empty()));
            assertTrue(out.get("verification_pending").booleanValue()); assertFalse(out.has("postcondition_verified"));
            assertEquals("acknowledged_verification_pending", out.get("status").textValue());
            assertEquals(settled ? "applied_confirmed" : "unresolved", out.get("canonical_gui_action").get("outcome").textValue());
            assertThrows(IllegalArgumentException.class, () -> ArmyGuiPublicFormatter.action(r, reply, c, Optional.of(token), Optional.empty()));
        }
        ObjectNode unknown = PublicDataJson.object(ArmyGuiPublicFormatter.action(r, actionReply(r, c, b, token, false, false), c, Optional.empty(), Optional.empty()));
        assertFalse(unknown.has("queried_snapshot_id")); assertFalse(unknown.has("verification_pending")); assertFalse(unknown.has("backend_id"));
        assertFalse(unknown.get("canonical_gui_action").get("ack_received").booleanValue());
    }

    @Test void crossRoleSourceMissingWrongTypeAndCanonicalDigestAreRejected() {
        var b = before(); var c = context(b, GuiModels.Build.CROZIER3); Request q = request(Method.QUERY_WINDOW, c); RawJson t = token(q, c);
        var foreign = new GuiModels.Context(c.before(), c.source(), "foreign-session", c.connectionGeneration(), c.build(), c.deadline());
        assertThrows(IllegalArgumentException.class, () -> ArmyGuiPublicFormatter.read(q, readReply(q, c, b, t), Optional.of(foreign)));
        ObjectNode wrong = PublicDataJson.object(t); wrong.put("native_revision", true); RawJson boolRevision = raw(wrong);
        assertThrows(IllegalArgumentException.class, () -> ArmyGuiPublicFormatter.read(q, readReply(q, c, b, boolRevision), Optional.of(c)));
        ObjectNode absentSubject = PublicDataJson.object(t); absentSubject.remove("requested_subject_id"); RawJson missing = raw(absentSubject);
        assertThrows(IllegalArgumentException.class, () -> ArmyGuiPublicFormatter.read(q, readReply(q, c, b, missing), Optional.of(c)));
        Request inventory = new Request(Method.QUERY_WINDOW, new WindowQuery("inventory"), q.expectedRevision());
        assertThrows(IllegalArgumentException.class, () -> ArmyGuiPublicFormatter.read(inventory, readReply(q, c, b, t), Optional.of(c)));
        Request a = request(Method.OPEN_COMBAT, c); ActionReply reply = actionReply(a, c, b, token(a, c), true, false);
        ActionReply corrupt = new ActionReply(reply.receipt(), new byte[] {1}, reply.originalReference(), reply.beforeSnapshot(), reply.parsedReturnReference());
        assertThrows(IllegalArgumentException.class, () -> ArmyGuiPublicFormatter.action(a, corrupt, c, Optional.empty(), Optional.empty()));
    }

    @Test void parsedReturnKeepsActualUnvalidatedRoleAndAbsentNullRemainDistinct() {
        var b = before(); var c = context(b, GuiModels.Build.CROZIER3); Request r = request(Method.QUERY_WINDOW, c);
        ObjectNode original = PublicDataJson.object(token(r, c)); original.putNull("actual_nullable"); original.putArray("actual_empty");
        ObjectNode reference = ref("parsed-return").toJson(); reference.put("validation_state", "unvalidated");
        ReadReply base = readReply(r, c, b, raw(original));
        ReadReply actual = new ReadReply(base.receipt(), base.originalReference(), base.beforeSnapshot(), Optional.of(raw(reference)));
        ObjectNode out = PublicDataJson.object(ArmyGuiPublicFormatter.read(r, actual, Optional.of(c)));
        assertEquals(reference, out.get("native_ui_raw_return_receipt"));
        assertTrue(out.get("actual_nullable").isNull()); assertTrue(out.get("actual_empty").isArray()); assertFalse(out.has("actual_absent"));
        ObjectNode wrong = reference.deepCopy(); wrong.put("validation_state", "validated");
        assertThrows(IllegalArgumentException.class, () -> new ReadReply(base.receipt(), base.originalReference(), base.beforeSnapshot(), Optional.of(raw(wrong))));
        ObjectNode boolBytes = reference.deepCopy(); boolBytes.put("bytes", true);
        assertThrows(IllegalArgumentException.class, () -> new ReadReply(base.receipt(), base.originalReference(), base.beforeSnapshot(), Optional.of(raw(boolBytes))));
    }

    @Test void actualNativeFalseAckKeepsOriginalFaultInsteadOfReturningCanonicalSuccess() {
        var b = before(); var c = context(b, GuiModels.Build.CROZIER3); Request r = request(Method.OPEN_COMBAT, c);
        ActionReply base = actionReply(r, c, b, token(r, c), true, false);
        RawJson top = raw(StrictJson.object().put("type", "command_result").put("protocol_version", 1)
                .put("request_id", "software-request").put("ok", false).put("error", "original GUI owner refused"));
        byte[] body = top.bytes(); byte[] packet = java.nio.ByteBuffer.allocate(body.length + Integer.BYTES)
                .order(java.nio.ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
        var rejected = new NativeActionPort.AckReceived("software-request", false, Optional.empty(), top, packet);
        var prior = (ActionState.Unknown) base.receipt().state();
        var state = new ActionState.Unknown(prior.attempt(), Optional.of(rejected), "original negative native result", List.of(ref("negative-original")));
        var receipt = new ActionReceipt(1, 1, base.receipt().command(), ActionCodec.bodySha256(base.receipt().command()), state);
        var reply = new ActionReply(receipt, base.archivedReceipt(), base.originalReference(), base.beforeSnapshot(), Optional.empty());
        GuiActionFailure failure = assertThrows(GuiActionFailure.class,
                () -> ArmyGuiPublicFormatter.action(r, reply, c, Optional.empty(), Optional.empty()));
        assertSame(receipt, failure.receipt()); assertSame(rejected, failure.original());
        assertEquals(GuiReadFailure.Kind.NATIVE_REFUSAL, failure.kind());
        assertEquals("native gameplay step failed: original GUI owner refused", failure.getMessage());
    }

    @Test void actualOriginalTenPythonWrappersReachFormatterAndPublicJsonRoundtrip() throws Exception {
        JsonNode rows = originalOracle(); Set<Method> observed = EnumSet.noneOf(Method.class);
        for (JsonNode row : rows) {
            Method m = Method.valueOf(row.get("method").textValue()); observed.add(m);
            ObjectNode b = (ObjectNode) row.get("before"); var c = context(b, GuiModels.Build.valueOf(row.get("build").textValue()));
            Request r = request(m, c); RawJson original = raw((ObjectNode) row.get("original"));
            RawJson result = m.mutation() ? ArmyGuiPublicFormatter.action(r, actionReply(r, c, b, original, true, false), c, Optional.empty(), Optional.empty())
                    : ArmyGuiPublicFormatter.read(r, readReply(r, c, b, original), Optional.of(c));
            ObjectNode actual = PublicDataJson.object(result); actual.remove(m.mutation() ? "canonical_gui_action" : "canonical_gui_read");
            ObjectNode expected = (ObjectNode) row.get("expected");
            assertEquals(PublicDataJson.object(GuiCodec.encodePublicOriginal(raw(expected))), actual, m.toString());
            assertEquals(actual, PublicDataJson.object(GuiCodec.encodePublicOriginal(raw(actual))));
        }
        assertEquals(OWNED, observed);
    }

    private static JsonNode originalOracle() throws Exception {
        Path root = requiredPath("xar.source.repository", true), python = requiredPath("xar.python", false);
        requireSource(root, "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py", 1658471,
                "eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603");
        requireSource(root, "ck3_autonomous_player/src/xar_autoplayer/bridge/ingame_ui_contract.py", 44182,
                "74608d05074a48e1139a17fea360e34cf65cb01144d0a9a0e1dcf4ca49065ed4");
        requireSource(root, "ck3_autonomous_player/tests/unit/test_ingame_ui_navigation_v1.py", 63891,
                "878f239b24591b30e4830403c6bc912688ebea8edfa55d20c970402bdc1ea847");
        String program = """
            import copy,json,sys
            from pathlib import Path
            root=Path(sys.argv[1]);sys.path[:0]=[str(root/'ck3_autonomous_player/src'),str(root/'ck3_autonomous_player/tests/unit')]
            import test_ingame_ui_navigation_v1 as U
            rows=[]
            cases=[('OPEN_CHARACTER','character','open_character',33437),('SELECT_ARMY','army','select_army',0),
              ('OPEN_COMBAT','combat','open_combat',16777218),('FIT_COMBAT','combat','fit_combat_window',16777218),
              ('OPEN_KNIGHTS','knights','open_knights',0),('QUERY_WINDOW','combat','query',0),
              ('HOVER_KNIGHTS','combat','hover_left_knights',16777218)]
            for method,kind,operation,subject in cases:
                original=U.result(kind,operation,subject);original['backend_id']='native-headless'
                d=U.DriverFixture(original);b=copy.deepcopy(U.snapshot())
                if method=='OPEN_CHARACTER':expected=d.open_character_window_v1(subject,expected_revision=4)
                elif method=='SELECT_ARMY':expected=d.select_army_ui_v1(subject,expected_revision=4)
                elif method=='OPEN_COMBAT':expected=d.open_combat_window_v1(subject,expected_revision=4)
                elif method=='FIT_COMBAT':expected=d.fit_combat_window_v1(subject,expected_revision=4)
                elif method=='OPEN_KNIGHTS':expected=d.open_knights_window_v1(expected_revision=4)
                elif method=='QUERY_WINDOW':expected=d.query_ingame_ui_window_v1(kind,expected_revision=4)
                else:expected=d.hover_combat_knights_v1(subject,'left',expected_revision=4)
                rows.append(dict(method=method,build='LEGACY',before=b,original=original,expected=expected))
            for method,operation in [('HOVER_ARMY','hover_army_tooltip'),('LEAVE_ARMY','leave_army_tooltip'),('QUERY_ARMY','query')]:
                original=U.army_tooltip_result(operation,phase='cache' if operation=='query' else 'ack',
                    receipt=U.LEAVE_RECEIPT if operation=='leave_army_tooltip' else U.HOVER_RECEIPT)
                original['backend_id']='native-headless';d=U.CurrentUiDriverFixture(original);b=copy.deepcopy(U.current_snapshot())
                if method=='HOVER_ARMY':expected=d.hover_army_tooltip_v1(0,'supply_state',expected_revision=4)
                elif method=='LEAVE_ARMY':expected=d.leave_army_tooltip_v1(0,'supply_state',U.HOVER_RECEIPT,expected_revision=4)
                else:expected=d.query_army_tooltip_v1(0,'supply_state',U.HOVER_RECEIPT,expected_revision=4)
                rows.append(dict(method=method,build='CROZIER3',before=b,original=original,expected=expected))
            print(json.dumps(rows,separators=(',',':')))
            """;
        Path output = Files.createTempFile("army-gui-original-", ".json");
        try {
            var builder = new ProcessBuilder(python.toString(), "-B", "-X", "utf8", "-c", program, root.toString());
            builder.directory(root.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.environment().put("PYTHONUTF8", "1");
            builder.environment().put("PYTHONPATH", root.resolve("ck3_autonomous_player/src").toString());
            Process child = builder.redirectErrorStream(true).redirectOutput(output.toFile()).start();
            boolean ended = child.waitFor(45, TimeUnit.SECONDS); if (!ended) { child.destroyForcibly(); child.waitFor(5, TimeUnit.SECONDS); }
            assertTrue(ended, "original Army/window producer oracle timed out"); byte[] bytes = Files.readAllBytes(output);
            assertEquals(0, child.exitValue(), new String(bytes, StandardCharsets.UTF_8)); JsonNode result = StrictJson.parse(bytes, StrictJson.EXPLICIT_MAX_BYTES);
            assertTrue(result.isArray()); assertEquals(10, result.size()); return result;
        } finally { Files.deleteIfExists(output); }
    }
    private static Path requiredPath(String property, boolean directory) throws java.io.IOException {
        String configured = System.getProperty(property); assertNotNull(configured, property + " mandatory; original oracle never skipped");
        assertFalse(configured.isBlank()); Path path = Path.of(configured); assertTrue(path.isAbsolute()); Path actual = path.toRealPath();
        assertTrue(directory ? Files.isDirectory(actual) : Files.isRegularFile(actual)); return actual;
    }
    private static void requireSource(Path root, String relative, long bytes, String expectedSha) throws java.io.IOException {
        Path path = root.resolve(relative).toRealPath(); assertTrue(path.startsWith(root));
        byte[] body = Files.readAllBytes(path); assertEquals(bytes, body.length, relative + " source length changed");
        assertEquals(expectedSha, sha(body), relative + " source digest changed");
    }
}
