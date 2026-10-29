package org.xar.ck3.control.governance.council;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.governance.council.CouncilModels.*;

/** Actual retained native .2 packets, then the same shared codec consumed by public and ordinary planners. */
final class CouncilPrivateCodecProducerTest {
    private static final String SHA = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
    private static final Frame NATIVE = new Frame("native:13", BigInteger.valueOf(13), BigInteger.valueOf(13), 53175816, 16777217);
    private static final Frame PUBLIC = new Frame("public:900", BigInteger.valueOf(900), BigInteger.valueOf(13), 53175816, 16777217);
    private static ObjectNode result(String fixture) throws Exception {
        String root = System.getProperty("xar.repository.root");
        assertNotNull(root, "required retained native producer originals missing; this is not a skipped test");
        return CouncilCodec.object(StrictJson.parse(Files.readAllBytes(Path.of(root,
                "ck3_autonomous_player/tests/fixtures/native_12002/governance/" + fixture + ".json"))).get("result"));
    }
    private static CouncilPrivateCodec.Terminal terminal(ObjectNode value) {
        return assertInstanceOf(CouncilPrivateCodec.Terminal.class, CouncilPrivateCodec.decodeReply(StrictJson.canonical(value), CouncilPrivateCodec.STATUS));
    }
    @Test void actualPendingStatusAndTerminalRemainIndependentAndRoundTrip() throws Exception {
        assertInstanceOf(CouncilPrivateCodec.Pending.class, CouncilPrivateCodec.decodeReply(StrictJson.canonical(result("council-private-query-pending")), CouncilPrivateCodec.QUERY));
        assertInstanceOf(CouncilPrivateCodec.Pending.class, CouncilPrivateCodec.decodeReply(StrictJson.canonical(result("council-private-status-pending")), CouncilPrivateCodec.STATUS));
        ObjectNode original = result("council-private-query-available");
        var terminal = terminal(original);
        ObjectNode projected = CouncilCodec.object(StrictJson.parse(CouncilPrivateCodec.normalize(terminal, CouncilPrivateCodec.QUERY,
                NATIVE, PUBLIC, Position.STEWARD, "1.20.0.2", SHA).bytes()));
        assertEquals(900, projected.get("queried_revision").intValue()); assertEquals(13, projected.get("queried_native_revision").intValue());
        assertEquals("public:900", projected.get("source_frame").get("snapshot_id").textValue());
        Candidates typed = CouncilCodec.decode(StrictJson.canonical(projected.get("council_composition_candidates")), NATIVE, Position.STEWARD);
        assertEquals(2, typed.candidates().size()); assertEquals(22, typed.candidates().get(0).mainSkill());
        assertEquals(typed, CouncilCodec.decode(CouncilCodec.encode(typed), NATIVE, Position.STEWARD));
        assertEquals(original, StrictJson.parse(terminal.original().bytes()), "normalization cannot rewrite retained original native metadata");
    }
    @Test void idleWrongStepMissingFieldsAndNonintegerBindingsAreRejected() throws Exception {
        assertThrows(IllegalArgumentException.class, () -> CouncilPrivateCodec.decodeReply(StrictJson.canonical(result("council-private-status-idle")), CouncilPrivateCodec.STATUS));
        assertThrows(IllegalArgumentException.class, () -> CouncilPrivateCodec.decodeReply(StrictJson.canonical(result("council-private-query-pending")), CouncilPrivateCodec.STATUS));
        ObjectNode bad = result("council-private-query-available"); bad.put("query_sequence", true);
        assertThrows(IllegalArgumentException.class, () -> terminal(bad));
        ObjectNode missing = result("council-private-query-available"); missing.remove("snapshot_revision");
        assertThrows(IllegalArgumentException.class, () -> terminal(missing));
        ObjectNode fractional = result("council-private-query-available"); fractional.put("snapshot_revision", 13.0);
        assertThrows(IllegalArgumentException.class, () -> terminal(fractional));
        var valid = terminal(result("council-private-query-available"));
        assertThrows(IllegalArgumentException.class, () -> CouncilPrivateCodec.requireTerminalBinding(valid, CouncilPrivateCodec.GATES, NATIVE));
    }
    @Test void missingPayloadIsUnavailableButActionMaterialNeverBecomesARead() throws Exception {
        ObjectNode missing = result("council-private-query-available"); missing.remove("council_composition_candidates");
        var value = CouncilCodec.object(StrictJson.parse(CouncilPrivateCodec.normalize(terminal(missing), CouncilPrivateCodec.QUERY,
                NATIVE, PUBLIC, Position.STEWARD, "1.20.0.2", SHA).bytes()));
        assertEquals("unavailable", value.get("status").textValue()); assertTrue(value.get("council_missing_payload_readonly").booleanValue());
        assertFalse(value.has("council_composition_candidates"));
        missing.put("business_action_submitted", true);
        assertThrows(IllegalArgumentException.class, () -> CouncilPrivateCodec.requireTerminalBinding(terminal(missing), CouncilPrivateCodec.QUERY, NATIVE));
        ObjectNode action = result("council-private-query-available"); action.putNull("council_assign_councillor_ack");
        assertThrows(IllegalArgumentException.class, () -> CouncilPrivateCodec.requireTerminalBinding(terminal(action), CouncilPrivateCodec.QUERY, NATIVE));
    }
    @Test void malformedBusinessPayloadIsRetainedAndRejectedAfterTerminalArchivalBoundary() throws Exception {
        ObjectNode wrong = result("council-private-query-available");
        CouncilCodec.object(wrong.get("council_composition_candidates")).put("owner_character_id", true);
        var originalTerminal = terminal(wrong);
        CouncilPrivateCodec.requireTerminalBinding(originalTerminal, CouncilPrivateCodec.QUERY, NATIVE);
        assertEquals(wrong, StrictJson.parse(originalTerminal.original().bytes()));
        assertThrows(IllegalArgumentException.class, () -> CouncilPrivateCodec.normalize(originalTerminal, CouncilPrivateCodec.QUERY,
                NATIVE, PUBLIC, Position.STEWARD, "1.20.0.2", SHA));
        ObjectNode unknown = result("council-private-query-available"); unknown.put("unmigrated_field", 1);
        assertThrows(IllegalArgumentException.class, () -> CouncilPrivateCodec.normalize(terminal(unknown), CouncilPrivateCodec.QUERY,
                NATIVE, PUBLIC, Position.STEWARD, "1.20.0.2", SHA));
    }
    @Test void historicalGatesFixtureCannotBeRestampedAsAPrivateNativeFrame() throws Exception {
        var legacy = terminal(result("council-gates"));
        assertThrows(IllegalArgumentException.class, () -> CouncilPrivateCodec.normalize(legacy, CouncilPrivateCodec.GATES,
                NATIVE, PUBLIC, Position.STEWARD, "1.20.0.2", SHA));
    }
    @Test void syntheticGateBindingTestsCollectionOrderAndExactBooleanKinds() throws Exception {
        // This deliberately changed frame is a synthetic parser vector, never another native observation.
        ObjectNode gatesResult = result("council-gates"); gatesResult.put("snapshot_revision", 13);
        ObjectNode gates = CouncilCodec.object(gatesResult.get("council_final_gates"));
        ObjectNode frame = CouncilCodec.object(gates.get("council_composition_candidates").get("snapshot"));
        frame.put("snapshot_id", "native:13").put("public_revision", 13).put("native_revision", 13).put("date_raw", 53175816);
        ObjectNode normalized = CouncilCodec.object(StrictJson.parse(CouncilPrivateCodec.normalize(terminal(gatesResult), CouncilPrivateCodec.GATES,
                NATIVE, PUBLIC, Position.STEWARD, "1.20.0.2", SHA).bytes()));
        assertEquals(normalized.get("council_composition_candidates"), normalized.get("council_final_gates").get("council_composition_candidates"));
        CouncilCodec.object(gates.get("rows").get(0)).put("final_gate_available", 1);
        assertThrows(IllegalArgumentException.class, () -> CouncilPrivateCodec.normalize(terminal(gatesResult), CouncilPrivateCodec.GATES,
                NATIVE, PUBLIC, Position.STEWARD, "1.20.0.2", SHA));
        CouncilCodec.object(gates.get("rows").get(0)).put("final_gate_available", true).put("native_collection_ordinal", 0);
        assertThrows(IllegalArgumentException.class, () -> CouncilPrivateCodec.normalize(terminal(gatesResult), CouncilPrivateCodec.GATES,
                NATIVE, PUBLIC, Position.STEWARD, "1.20.0.2", SHA));
    }
}
