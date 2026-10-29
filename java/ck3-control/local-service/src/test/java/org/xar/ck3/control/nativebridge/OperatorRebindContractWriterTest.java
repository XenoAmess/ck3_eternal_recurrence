package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigDecimal;
import java.nio.file.Path;
import java.util.Set;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;

/** Uses the actual software writer's before producer. Codec DATA is never a private operator issuer. */
public final class OperatorRebindContractWriterTest {
    @TempDir Path directory;
    private static ActionCommand operator(ActionWriterIntegrationFixture fixture, ActionCommand original) throws Exception {
        return fixture.writer.locked(same -> fixture.driverAuthority().withFrozenFacts(same, frozen -> {
            var known = (DriverSnapshotFacts.Known) frozen.state();
            var before = fixture.archive.withSession(same).preserveMaterial(new RawJson(known.driver().encode()));
            var request = new OperatorPlayerSwitch.Request(123, original.before().frame().revision());
            var expected = new OperatorRebindExpectation(original.origin(), original.source(), request,
                    original.before().frame().episodeRunId(), known.stamp().episodeEpoch(), before);
            return new ActionCommand("operator-contract", original.origin(), original.source(), original.sessionId(),
                    new OperationKey(request.step()), original.arguments(), new CommandExpectation.OperatorRebind(expected),
                    new Claims(Set.of(), Set.of(), Set.of(), Set.of()), original.deadline());
        }));
    }
    @Test public void actualBeforeProducerUsesNewCommandAndReceiptDataVersionsWithoutGrantingOperatorAuthority() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(directory, false)) {
            var original = fixture.command("original-command");
            var command = operator(fixture, original);
            byte[] legacy = ActionCodec.encodeCommand(original);
            assertArrayEquals(legacy, ActionCodec.encodeCommand(ActionCodec.decodeCommand(legacy)));
            byte[] encoded = ActionCodec.encodeCommand(command);
            assertEquals(ActionCodec.OPERATOR_COMMAND_SCHEMA, StrictJson.text(StrictJson.parse(encoded).get("schema")));
            assertEquals(command, ActionCodec.decodeCommand(encoded));
            // An uncommitted Intent is deliberately codec DATA, not an actual canonical receipt or submit permission.
            var data = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.IntentDurable());
            byte[] metadata = ActionReceiptCodec.encodeReceipt(data, fixture.archive);
            assertEquals(ActionReceiptCodec.OPERATOR_SCHEMA, StrictJson.text(StrictJson.parse(metadata).get("schema")));
            var decoded = ActionReceiptCodec.decodeReceipt(metadata, fixture.archive);
            assertEquals(data, decoded); assertFalse(decoded.settled()); assertFalse(decoded.visibleGameplay());
            assertFalse(decoded.eligibleAdvance());
            assertThrows(RuntimeException.class, () -> fixture.coordinator.execute(command));
            assertEquals(0, fixture.nativeActionWrites());
        }
    }
    /** Requires the actual terminal source command from the genuine operator issuer; no terminal proof is constructed here. */
    public static void assertActualTerminalCommandVersions(ActionCommand actual) {
        assertInstanceOf(CommandOrigin.LifecycleTerminal.class, actual.origin());
        assertInstanceOf(CommandExpectation.OperatorRebind.class, actual.expectation());
        byte[] encoded = ActionCodec.encodeCommand(actual);
        assertEquals(actual, ActionCodec.decodeCommand(encoded));
        var downgraded = (ObjectNode) StrictJson.parse(encoded);
        downgraded.put("schema", ActionCodec.LIFECYCLE_COMMAND_SCHEMA);
        assertThrows(IllegalArgumentException.class, () -> ActionCodec.decodeCommand(StrictJson.canonical(downgraded)));
    }
    @Test public void actualExpectationCodecRejectsWrongTypesMissingRolesAndHistoricalCommandSchema() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(directory, false)) {
            var command = operator(fixture, fixture.command("before-types"));
            var correct = CommandOriginCodec.expectation(command.expectation());
            assertEquals(command.expectation(), CommandOriginCodec.expectation(correct));
            for (JsonNode wrong : new JsonNode[]{BooleanNode.TRUE, DecimalNode.valueOf(new BigDecimal("123.0")),
                    TextNode.valueOf("123"), NullNode.instance, IntNode.valueOf(-1)}) {
                var copy = correct.deepCopy(); copy.set("target_character_id", wrong);
                assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.expectation(copy));
            }
            for (String key : new String[]{"before_driver", "episode_epoch", "expected_revision", "origin", "source"}) {
                var copy = correct.deepCopy(); copy.remove(key);
                assertThrows(RuntimeException.class, () -> CommandOriginCodec.expectation(copy));
            }
            for (String wrong : new String[]{"+1", "01", "-0", "18446744073709551616"}) {
                var copy = correct.deepCopy(); copy.put("expected_revision", wrong);
                assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.expectation(copy));
            }
            var wrongSchema = (ObjectNode) StrictJson.parse(ActionCodec.encodeCommand(command));
            wrongSchema.put("schema", ActionCodec.LIFECYCLE_COMMAND_SCHEMA);
            assertThrows(RuntimeException.class, () -> ActionCodec.decodeCommand(StrictJson.canonical(wrongSchema)));
        }
    }
}
