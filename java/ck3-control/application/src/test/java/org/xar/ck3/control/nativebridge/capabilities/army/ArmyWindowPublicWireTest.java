package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
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

/** Actual strict fixed-window decoder to shared public wire. Software DATA grants no UI or dispatch authority. */
final class ArmyWindowPublicWireTest {
    private static final BigInteger MAX = new BigInteger("18446744073709551615");
    private static final String ID = "window-original-data";
    private static ArmyTypes.Context context() {
        var ref = new ExactRef("software-window-codec-data", 1, "a".repeat(64));
        var source = new G2Source("software-window-data", "2026-10-24T00:00:00Z", "1.20.0.4", ref);
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(73), BigInteger.ONE, BigInteger.valueOf(77)), "native:1", BigInteger.ONE, "window-data-episode");
        return new ArmyTypes.Context(new ObservationIdentity(source.machineId(), new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1), source, "window-data-session", Instant.parse("2026-10-25T00:00:00Z"));
    }
    private static ObjectNode original(ArmyWindowCodec.Kind kind) {
        ObjectNode top = ArmyJson.empty().put("type", "command_result").put("protocol_version", 1).put("request_id", ID).put("ok", true);
        ObjectNode owner = top.putObject(kind.ownerKey()).put("request_id", ID).put("date_raw", 77).put("thread_id", 17);
        for (String field : List.of("ticket_sequence", "executor_started_sequence", "completed_sequence", "pump_epoch", "connection_generation")) owner.put(field, MAX);
        ObjectNode row = top.putObject("result");
        for (String field : List.of("available", "accepted", "root_observed", "window_present", "effective_visible", "dispatch_attempted", "dispatch_invoked", "native_handled", "post_observed", "scope_unchanged", "closure_verified", "application_owner_thread_verified", "paused")) row.put(field, true);
        row.put("post_window_present", false).put("post_effective_visible", false);
        row.put("status", "closed_verified").put("unavailable_reason", "").put("request_id", ID).put("operation", "close")
                .put("root_observation_source", "guarded_registered_top_level").put("post_observation_source", "guarded_top_level_and_complete_owner_tree")
                .put("played_character_id", 73).put("date_raw", 77).put("native_revision", 1).put("thread_id", 17)
                .put("game_version", "1.20.0.4").put("executable_sha256", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");
        for (String field : List.of("connection_generation", "pump_epoch", "ticket_sequence")) row.put(field, MAX);
        if (kind == ArmyWindowCodec.Kind.OVERVIEW) row.put("schema", "ck3-war-declared-overview-v1").put("window_name", "war_declared_overview").put("button_name", "dismiss");
        else row.put("schema", "ck3-war-results-window-v1").put("window_name", "war_results").put("button_name", "close_button");
        return top;
    }
    private static ArmyWindowCodec.Observation decode(ArmyWindowCodec.Kind kind, ObjectNode original) {
        return decode(kind, original, BigInteger.valueOf(17));
    }
    private static ArmyWindowCodec.Observation decode(ArmyWindowCodec.Kind kind, ObjectNode original, BigInteger driverGeneration) {
        return ArmyWindowCodec.decode(kind, ArmyWindowCodec.Operation.CLOSE, ArmyJson.bytes(original), ID, context(), MAX, driverGeneration);
    }
    @Test void bothActualFixedWindowDecodersPreserveIndependentWideOwnerCounters() {
        for (BigInteger driverGeneration : List.of(BigInteger.ZERO, BigInteger.valueOf(17)))
        for (var kind : ArmyWindowCodec.Kind.values()) {
            ObjectNode original = original(kind); byte[] unchanged = ArmyJson.bytes(original);
            var observation = decode(kind, original, driverGeneration);
            var normalized = DriverJson.object(ArmyJson.bytes(observation.normalized()), DriverJson.MAX_NATIVE_BYTES);
            var wire = ArmyPublicWire.encodeExactSourceBound(normalized, context()); ObjectNode encoded = ArmyJson.parse(wire.bytes());
            JsonNode owner = encoded.path("native_command_result").path(kind.ownerKey());
            assertEquals(driverGeneration.toString(), encoded.path("queried_connection_generation").textValue());
            assertEquals(MAX.toString(), encoded.path("connection_generation").textValue());
            for (String field : List.of("ticket_sequence", "executor_started_sequence", "completed_sequence", "pump_epoch")) assertEquals(MAX.toString(), owner.path(field).textValue());
            assertEquals(normalized, ArmyPublicWire.decodeExactSourceBound(wire, context()));
            assertEquals(wire, ArmyPublicWire.encodeExactSourceBound(ArmyPublicWire.decodeExactSourceBound(wire, context()), context()));
            assertArrayEquals(unchanged, ArmyJson.bytes(original));
            assertFalse(encoded.path("native_command_result").has("result"));
        }
    }
    @Test void strictOwnerProofRejectsMissingForeignAndInvalidCounterDomains() {
        for (var kind : ArmyWindowCodec.Kind.values()) {
            ObjectNode missing = original(kind); ((ObjectNode) missing.path(kind.ownerKey())).remove("completed_sequence");
            assertThrows(IllegalArgumentException.class, () -> decode(kind, missing));
            ObjectNode changed = original(kind); ((ObjectNode) changed.path(kind.ownerKey())).put("completed_sequence", 1);
            assertThrows(IllegalArgumentException.class, () -> decode(kind, changed));
            for (JsonNode invalid : List.of(ArmyJson.empty().booleanNode(true), ArmyJson.empty().numberNode(1.0), ArmyJson.empty().textNode(MAX.toString()), ArmyJson.empty().numberNode(MAX.add(BigInteger.ONE)))) {
                ObjectNode bad = original(kind); ((ObjectNode) bad.path(kind.ownerKey())).set("executor_started_sequence", invalid);
                assertThrows(IllegalArgumentException.class, () -> decode(kind, bad));
            }
        }
        ObjectNode encoded = ArmyJson.empty().put("executor_started_sequence", "01");
        assertThrows(IllegalArgumentException.class, () -> ArmyPublicWire.decodeExactSourceBound(new RawJson(ArmyJson.bytes(encoded)), context()));
    }
}
