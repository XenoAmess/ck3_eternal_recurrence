package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Original Commander rejection report serialization only; failure DATA can never authorize a retry. */
final class ArmyCommanderRejectedPublicWireTest {
    private static final BigInteger MAX = new BigInteger("18446744073709551615");
    private static ArmyTypes.Context context() {
        var source = new G2Source("software-commander-report", "2026-10-24T00:00:00Z", "1.20.0.4", new ExactRef("software-commander-source", 1, "a".repeat(64)));
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(73), MAX, BigInteger.valueOf(77)), "native:" + MAX, BigInteger.ONE, "commander-report-data");
        return new ArmyTypes.Context(new ObservationIdentity(source.machineId(), new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1), source, "commander-report-data", Instant.parse("2026-10-25T00:00:00Z"));
    }
    @Test void fullOriginalCommanderFailureReportRetainsWideRequestAndNeverReplayShape() {
        ObjectNode original = ArmyJson.empty().put("schema", "army-commander-native-rejection-v1").put("native_request_id", "original-commander-report")
                .put("dispatch_status", "unknown-unless-native-diagnostic-proves-predispatch").put("never_replay", true);
        original.putObject("native_request_frame").put("type", "execute_step").put("protocol_version", 1).put("request_id", "original-commander-report")
                .put("step", "assign-army-commander-v1-army-73-character-74").put("expected_revision", MAX);
        original.putObject("native_command_result_frame").put("type", "command_result").put("protocol_version", 1).put("request_id", "original-commander-report").put("ok", false).put("error", "native Commander request rejected");
        byte[] unchanged = ArmyJson.bytes(original); var data = DriverJson.object(unchanged, DriverJson.MAX_NATIVE_BYTES);
        var encoded = ArmyPublicWire.encodeExactSourceBound(data, context()); var wire = ArmyJson.parse(encoded.bytes());
        assertEquals(MAX.toString(), wire.path("native_request_frame").path("expected_revision").textValue());
        assertEquals(data, ArmyPublicWire.decodeExactSourceBound(encoded, context())); assertArrayEquals(unchanged, ArmyJson.bytes(original));
        assertTrue(wire.path("never_replay").booleanValue()); assertFalse(wire.path("native_command_result_frame").has("result")); assertFalse(wire.has("queried_revision"));
        for (var invalid : List.of(ArmyJson.empty().booleanNode(true), ArmyJson.empty().numberNode(1.0), ArmyJson.empty().textNode(MAX.toString()), ArmyJson.empty().numberNode(MAX.add(BigInteger.ONE)))) {
            ObjectNode bad = original.deepCopy(); ((ObjectNode) bad.path("native_request_frame")).set("expected_revision", invalid);
            assertThrows(IllegalArgumentException.class, () -> ArmyPublicWire.encodeExactSourceBound(DriverJson.object(ArmyJson.bytes(bad), DriverJson.MAX_NATIVE_BYTES), context()));
        }
        ObjectNode foreign = ArmyJson.empty(); foreign.putObject("unrelated_frame").put("expected_revision", MAX);
        assertThrows(IllegalArgumentException.class, () -> ArmyPublicWire.encodeExactSourceBound(DriverJson.object(ArmyJson.bytes(foreign), DriverJson.MAX_NATIVE_BYTES), context()));
    }
}
