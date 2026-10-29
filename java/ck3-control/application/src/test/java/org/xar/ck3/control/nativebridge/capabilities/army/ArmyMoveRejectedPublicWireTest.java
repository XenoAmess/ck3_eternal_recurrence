package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Original move rejection request remains complete DATA; it never grants a retry or an action effect. */
final class ArmyMoveRejectedPublicWireTest {
    private static final BigInteger MAX = new BigInteger("18446744073709551615");
    private static ArmyTypes.Context context() {
        var source = new G2Source("software-move-rejection", "2026-10-24T00:00:00Z", "1.20.0.4", new ExactRef("software-move-source", 1, "a".repeat(64)));
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(73), MAX, BigInteger.valueOf(77)), "native:" + MAX, BigInteger.ONE, "move-rejection-data");
        return new ArmyTypes.Context(new ObservationIdentity(source.machineId(), new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1), source, "move-rejection-data", Instant.parse("2026-10-25T00:00:00Z"));
    }
    @Test void originalNegativeMoveRequestRevisionPreservesWideIdentityAndCompleteErrorFrame() {
        ObjectNode original = ArmyJson.empty().put("revision", 1).put("native_revision", MAX).put("snapshot_id", "native:" + MAX);
        ObjectNode evidence = original.putObject("native_error_evidence");
        evidence.putObject("native_request").put("type", "execute_step").put("protocol_version", 1).put("step", "move-army-73-to-77").put("request_id", "original-negative-move").put("expected_revision", MAX);
        evidence.putObject("native_command_result").put("type", "command_result").put("protocol_version", 1).put("request_id", "original-negative-move").put("ok", false).put("error", "native validation rejected move");
        byte[] unchanged = ArmyJson.bytes(original); var data = DriverJson.object(unchanged, DriverJson.MAX_NATIVE_BYTES);
        var encoded = ArmyPublicWire.encodeExactSourceBound(data, context()); var wire = ArmyJson.parse(encoded.bytes());
        assertEquals(MAX.toString(), wire.path("native_error_evidence").path("native_request").path("expected_revision").textValue());
        assertEquals(data, ArmyPublicWire.decodeExactSourceBound(encoded, context()));
        assertFalse(wire.path("native_error_evidence").path("native_command_result").has("result"));
        assertFalse(wire.has("queried_revision")); assertArrayEquals(unchanged, ArmyJson.bytes(original));
        for (var invalid : List.of(ArmyJson.empty().booleanNode(true), ArmyJson.empty().numberNode(1.0), ArmyJson.empty().textNode(MAX.toString()), ArmyJson.empty().numberNode(MAX.add(BigInteger.ONE)))) {
            ObjectNode changed = original.deepCopy(); ((ObjectNode) changed.path("native_error_evidence").path("native_request")).set("expected_revision", invalid);
            assertThrows(IllegalArgumentException.class, () -> ArmyPublicWire.encodeExactSourceBound(DriverJson.object(ArmyJson.bytes(changed), DriverJson.MAX_NATIVE_BYTES), context()));
        }
        ObjectNode foreign = ArmyJson.empty(); foreign.putObject("unrelated_request").put("expected_revision", MAX);
        assertThrows(IllegalArgumentException.class, () -> ArmyPublicWire.encodeExactSourceBound(DriverJson.object(ArmyJson.bytes(foreign), DriverJson.MAX_NATIVE_BYTES), context()));
        ObjectNode malformed = ArmyJson.empty(); malformed.putObject("native_error_evidence").putObject("native_request").put("expected_revision", "01");
        assertThrows(IllegalArgumentException.class, () -> ArmyPublicWire.decodeExactSourceBound(new RawJson(ArmyJson.bytes(malformed)), context()));
    }
}
