package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original Driver number domain -> all three actual command schemas -> sole body hash/decoder.
 * These contract-only identities confer no Native or writer authority. Archive consumer regression has its own owner. */
final class ActionCodecNumericTokenTest {
    private static final Instant NOW = Instant.parse("2026-10-24T03:00:00Z");
    private static final String MACHINE = "numeric-command-contract";
    private static final GameGeneration GAME = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001")));
    private static final JointBudgetSelector.Claims NONE = new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of());
    private static ExactRef ref(String role, char hash) { return new ExactRef("contract-data/" + role, 1, String.valueOf(hash).repeat(64)); }
    private static final G2Source SOURCE = new G2Source(MACHINE, NOW.toString(), "1.20.0.4", ref("source.java", 'a'));
    private static final List<ExpectedValue> VALUES = List.of(new ExpectedBoolean(new FieldKey("ready"), true));
    private static OpportunityJson.Obj args(String json) { return DriverJson.object(json.getBytes(StandardCharsets.UTF_8), ActionCommand.MAX_ARGUMENT_BYTES); }
    private static List<ActionCommand> commands(OpportunityJson.Obj arguments) {
        var before = new ObservationIdentity(MACHINE, GAME, new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.ONE, BigInteger.TWO, BigInteger.valueOf(100)), "native:2", BigInteger.TWO, "episode-decimal"), 1);
        var expected = new ExpectedPostcondition(1, before, SOURCE, "numeric-contract/v1", VALUES);
        ActionCommand ordinary = new ActionCommand("numeric-ordinary", before, SOURCE, "ordinary-session", new OperationKey("select-event-option-1"), arguments, expected, NONE, NOW.plusSeconds(30));
        var frontend = new FrontendIdentity(MACHINE, GAME, "frontend-session", new BigInteger("9007199254740993"), GAME.pid(),
                new FrontendFrame.Menu(BigInteger.ONE), ref("native", 'b'), ref("hello", 'c'));
        ActionCommand menu = new ActionCommand("numeric-frontend", new CommandOrigin.Frontend(frontend), SOURCE, frontend.frontendSessionId(),
                new OperationKey("frontend-contract-operation"), arguments,
                new CommandExpectation.Frontend(new FrontendExpectedPostcondition(frontend, SOURCE, "frontend-numeric/v1", VALUES)), NONE, NOW.plusSeconds(30));
        var terminal = new LifecycleIdentity(MACHINE, GAME, "terminal-session", BigInteger.ONE,
                new LifecycleIdentity.Subject(BigInteger.ONE, "old-episode", 1, 1),
                new LifecycleIdentity.Frame("native:5", BigInteger.valueOf(5), BigInteger.valueOf(5), BigInteger.valueOf(100), true, false),
                new LifecycleIdentity.Null(), LifecycleIdentity.TerminalReason.MISSING,
                new LifecycleIdentity.Evidence(ref("native", 'b'), ref("hello", 'c'), ref("manifest", 'd'), ref("driver", 'e'), ref("qualification", 'f')), NOW);
        var operation = LifecycleExpectedPostcondition.Operation.DEATH_TERMINAL;
        var noCredit = List.<ExpectedValue>of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), false),
                new ExpectedBoolean(new FieldKey("timeline.advance_verified"), false), new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"), false));
        ActionCommand lifecycle = new ActionCommand("numeric-lifecycle", new CommandOrigin.LifecycleTerminal(terminal), SOURCE, terminal.sessionId(), operation.key(), arguments,
                new CommandExpectation.LifecycleTerminal(new LifecycleExpectedPostcondition(terminal, SOURCE, "terminal-numeric/v1", operation, noCredit)), NONE, NOW.plusSeconds(30));
        return List.of(ordinary, menu, lifecycle);
    }

    @Test void driverOriginalDecimalTokensAndLargeIntegersSurviveAllCommandSchemasAndHashes() {
        OpportunityJson.Obj original = args("{\"event_resolution\":{\"strategy_score\":-0.0,\"positive_zero\":0.0,\"decimal_integer\":1.0,\"trailing\":1.2300,\"exponent\":1E+3,\"wide_exponent\":1e10000,\"huge\":"
                + "9".repeat(120) + ",\"nested\":[-0.0,1,1.0,null,true,\"😀\"]}}");
        for (ActionCommand command : commands(original)) {
            byte[] wire = ActionCodec.encodeCommand(command); ActionCommand decoded = ActionCodec.decodeCommand(wire);
            assertEquals(command, decoded); assertEquals(original, decoded.arguments());
            assertEquals(original, DriverJson.object(wire, ActionCodec.MAX_COMMAND_BYTES).get("arguments"));
            assertArrayEquals(wire, ActionCodec.encodeCommand(decoded));
            assertEquals(ActionCodec.sha256(wire), ActionCodec.bodySha256(command));
            assertEquals(ActionCodec.bodySha256(command), ActionCodec.bodySha256(decoded));
            assertTrue(new String(wire, StandardCharsets.UTF_8).contains("\"strategy_score\":-0.0"));
            assertTrue(new String(wire, StandardCharsets.UTF_8).contains("1e10000"));
        }
    }

    @Test void legacyCharacterCanonicalBodiesRetainTheirActualStoredTokensAndBodySha() {
        for (String token : List.of("1", "1.0", "1.00", "1e3", "-0.0")) {
            for (ActionCommand command : commands(args("{\"emoji\":\"😀\",\"score\":" + token + ",\"nested\":{\"\uE000\":1,\"😀\":2}}"))) {
                byte[] legacy = legacyWire(command);
                ActionCommand loaded = ActionCodec.decodeCommand(legacy);
                assertEquals(DriverJson.object(legacy, ActionCodec.MAX_COMMAND_BYTES).get("arguments"), loaded.arguments());
                assertArrayEquals(legacy, ActionCodec.encodeCommand(loaded), "old canonical bytes must retain supplementary Unicode and original key order");
                assertEquals(ActionCodec.sha256(legacy), ActionCodec.bodySha256(loaded));
            }
        }
        ActionCommand legacyZero = ActionCodec.decodeCommand(legacyWire(commands(args("{\"score\":-0.0}")).getFirst()));
        assertEquals(new OpportunityJson.DecimalValue("0.0"), legacyZero.arguments().get("score"), "old lost signed zero cannot be re-created as historical evidence");
    }

    @Test void fieldOrderCanonicalizesButNumberCategoryAndSignedZeroRemainDifferentBodies() {
        var first = commands(args("{\"z\":1,\"a\":{\"b\":-0.0,\"a\":1.0}}")).getFirst();
        var reordered = commands(args("{\"a\":{\"a\":1.0,\"b\":-0.0},\"z\":1}")).getFirst();
        assertArrayEquals(ActionCodec.encodeCommand(first), ActionCodec.encodeCommand(reordered));
        assertNotEquals(ActionCodec.bodySha256(commands(args("{\"score\":-0.0}")).getFirst()), ActionCodec.bodySha256(commands(args("{\"score\":0.0}")).getFirst()));
        assertNotEquals(ActionCodec.bodySha256(commands(args("{\"score\":1}")).getFirst()), ActionCodec.bodySha256(commands(args("{\"score\":1.0}")).getFirst()));
    }

    @Test void existingSchemaOriginAndRoleBudgetGuardsRemainStrict() {
        for (ActionCommand command : commands(args("{}"))) {
            ObjectNode original = (ObjectNode) StrictJson.parse(ActionCodec.encodeCommand(command), ActionCodec.MAX_COMMAND_BYTES);
            for (String json : List.of("null", "[]", "false")) {
                ObjectNode changed = original.deepCopy(); changed.set("arguments", StrictJson.parse(json.getBytes(StandardCharsets.UTF_8)));
                assertThrows(IllegalArgumentException.class, () -> ActionCodec.decodeCommand(ProposalLifecycleCodec.encodePayload(changed, ActionCodec.MAX_COMMAND_BYTES)));
            }
            ObjectNode unknown = original.deepCopy(); unknown.put("schema", "xar.java-action-command/v4");
            assertThrows(IllegalArgumentException.class, () -> ActionCodec.decodeCommand(ProposalLifecycleCodec.encodePayload(unknown, ActionCodec.MAX_COMMAND_BYTES)));
            ObjectNode missing = original.deepCopy(); missing.remove("arguments");
            assertThrows(IllegalArgumentException.class, () -> ActionCodec.decodeCommand(ProposalLifecycleCodec.encodePayload(missing, ActionCodec.MAX_COMMAND_BYTES)));
            ObjectNode extra = original.deepCopy(); extra.put("alias", "not permitted");
            assertThrows(IllegalArgumentException.class, () -> ActionCodec.decodeCommand(ProposalLifecycleCodec.encodePayload(extra, ActionCodec.MAX_COMMAND_BYTES)));
        }
        assertThrows(IllegalArgumentException.class, () -> commands(new OpportunityJson.Obj(Map.of("large", new OpportunityJson.Text("x".repeat(ActionCommand.MAX_ARGUMENT_BYTES))))));
        assertThrows(IllegalArgumentException.class, () -> ActionCodec.decodeCommand(new byte[ActionCodec.MAX_COMMAND_BYTES + 1]));
        String valid = new String(ActionCodec.encodeCommand(commands(args("{}")).getFirst()), StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> ActionCodec.decodeCommand(valid.replace("\"arguments\":{}", "\"arguments\":{},\"arguments\":{}").getBytes(StandardCharsets.UTF_8)));
    }

    /** Frozen predecessor contract reuses its original field producers and character canonicalizer, including its old numeric loss. */
    private static byte[] legacyWire(ActionCommand command) {
        ObjectNode row = StrictJson.object(); row.put("action_id", command.actionId());
        if (command.origin() instanceof CommandOrigin.Gameplay) {
            row.put("schema", ActionCodec.COMMAND_SCHEMA); row.set("before", ProposalLifecycleCodec.observation(command.before()));
            row.set("expected", ProposalLifecycleCodec.expected(command.expected()));
        } else {
            row.put("schema", command.origin() instanceof CommandOrigin.Frontend ? ActionCodec.FRONTEND_COMMAND_SCHEMA : ActionCodec.LIFECYCLE_COMMAND_SCHEMA);
            row.set("origin", CommandOriginCodec.origin(command.origin())); row.set("expectation", CommandOriginCodec.expectation(command.expectation()));
        }
        row.set("source", ProposalLifecycleCodec.source(command.source())); row.put("session_id", command.sessionId()); row.put("operation", command.operation().value());
        row.set("arguments", OpportunityJson.toNode(command.arguments())); row.set("claims", ActionCodec.claims(command.claims())); row.put("deadline", command.deadline().toString());
        return ProposalLifecycleCodec.encodePayload(row, ActionCodec.MAX_COMMAND_BYTES);
    }
}
