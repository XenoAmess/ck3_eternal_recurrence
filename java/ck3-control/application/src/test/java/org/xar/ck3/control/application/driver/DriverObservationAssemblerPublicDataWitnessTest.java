package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * NONBLIND source witness: its author already read the actual and candidate bodies.
 * Manual public DATA witness; no main method, native operation or live authority.
 * Every frame below is synthetic public DATA, with no native custody/Game/source authority.
 * Assertions call only the real public canonicalNativeState entry. Expected output is
 * literal fixture material; this class implements no copy of the private normalizer.
 */
final class DriverObservationAssemblerPublicDataWitnessTest {
    @Test void lexicalTokensAndOriginalBytesSurviveTheRealPublicEntry() {
        String raw = """
                {"date_raw":53149608,"active_wars":null,"player_armies":null,
                 "history":[{"opaque":-0.00e+2,"id":184467440737095516170000}],
                 "opaque":{"decimal":1.2300E-7,"nullable":null},
                 "top_exclusive_modal_choice_hint":{"pump_epoch":9,"thread_id":8,"amount":-0.00e+2}}
                """;
        ObservedFrame frame = softwareData(raw);
        byte[] packetBefore = frame.originalPacket();
        byte[] stateBefore = frame.state().bytes();
        OpportunityJson.Obj actual = DriverObservationAssembler.canonicalNativeState(frame).semantic();
        assertLiteral("[{\"opaque\":-0.00e+2,\"id\":184467440737095516170000}]", actual.get("history"));
        assertLiteral("{\"decimal\":1.2300E-7,\"nullable\":null}", actual.get("opaque"));
        assertLiteral("{\"amount\":-0.00e+2}", actual.get("top_exclusive_modal_choice_hint"));
        assertEquals(List.of(), OpportunityJson.array(actual.get("active_wars"), "active_wars"));
        assertEquals(List.of(), OpportunityJson.array(actual.get("player_armies"), "player_armies"));
        for (String key : List.of("active_event", "one_life_settlement", "played_character",
                "played_character_gold", "played_character_prestige", "played_character_piety", "pending_character_interaction"))
            assertEquals(OpportunityJson.Nil.INSTANCE, actual.get(key), key);
        assertEquals(new OpportunityJson.Text("software-witness"), actual.get("snapshot_id"));
        assertEquals(BigInteger.ONE, OpportunityJson.integer(actual.get("revision"), "revision"));
        assertArrayEquals(packetBefore, frame.originalPacket());
        assertArrayEquals(stateBefore, frame.state().bytes());
    }

    @Test void completeLiteralMilitaryOutputRetainsStableFirstOccurrenceAndExactIdentity() {
        String raw = """
                {"date_raw":53149608,"active_wars":[{
                  "war_id":184467440737095516170000,"player_side":"attacker",
                  "targeted_title_ids":[12,12,13],"war_objective_province_ids":[],
                  "player_relative_war_score":-20,
                  "allied_armies":[{"army_id":7,"owner_character_id":22,"controllable":true},
                                   {"army_id":8,"owner_character_id":23,"controllable":true}],
                  "enemy_armies":[]}],
                 "player_armies":[{"army_id":7,"owner_character_id":21,"controllable":false}],"history":[]}
                """;
        OpportunityJson.Obj actual = DriverObservationAssembler.canonicalNativeState(softwareData(raw)).semantic();
        assertLiteral("""
                [{"war_id":184467440737095516170000,"player_side":"attacker",
                  "primary_opponent_character_id":null,"player_is_primary_war_leader":null,
                  "enemy_primary_default_raise_province_id":null,"targeted_title_ids":[12,13],
                  "war_objective_province_ids":[],"objective_province_states":[],"player_relative_war_score":-20,
                  "allied_armies":[
                    {"army_id":7,"owner_character_id":22,"soldiers":null,"current_province_id":null,
                     "move_target_province_id":null,"move_target_observable":false,"controllable":true,"source":"native"},
                    {"army_id":8,"owner_character_id":23,"soldiers":null,"current_province_id":null,
                     "move_target_province_id":null,"move_target_observable":false,"controllable":true,"source":"native"}],
                  "enemy_armies":[],"source":"native"}]
                """, actual.get("active_wars"));
        assertLiteral("""
                [{"army_id":7,"owner_character_id":21,"soldiers":null,"current_province_id":null,
                  "move_target_province_id":null,"move_target_observable":false,"controllable":false,"source":"native"},
                 {"army_id":8,"owner_character_id":23,"soldiers":null,"current_province_id":null,
                  "move_target_province_id":null,"move_target_observable":false,"controllable":true,"source":"native"}]
                """, actual.get("player_armies"));
    }

    @Test void activeWarsWrongKindPrecedesBadArmiesAndBadSemanticEvent() {
        assertFirstFailure("{\"active_wars\":{},\"player_armies\":{},\"active_event\":true}",
                "native active_wars must be an array");
    }

    @Test void badPlayerArmiesPrecedesBadSemanticEvent() {
        assertFirstFailure("{\"active_wars\":[],\"player_armies\":{},\"active_event\":true}",
                "native player_armies must be an array");
    }

    @Test void militarySuccessReachesActiveEventBeforeLaterBadSettlement() {
        assertFirstFailure("{\"active_wars\":[],\"player_armies\":[],\"active_event\":true,\"one_life_settlement\":true}",
                "active_event must be an object or null");
    }

    private static ObservedFrame softwareData(String rawState) {
        // These finite literal identities only satisfy public DATA contracts.
        // They do not identify or borrow an actual process, native issuer or Game owner.
        byte[] state = rawState.getBytes(StandardCharsets.UTF_8);
        byte[] packet = ("{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"software-witness\","
                + "\"revision\":1,\"state\":" + rawState + "}").getBytes(StandardCharsets.UTF_8);
        byte[] framed = ByteBuffer.allocate(packet.length + 4).order(ByteOrder.LITTLE_ENDIAN)
                .putInt(packet.length).put(packet).array();
        var session = new TransportSession("software-data-only",
                new GameGeneration(1, new PythonOnlyUInt64(BigInteger.ONE)), BigInteger.ONE, "software-data-only");
        return new ObservedFrame(session, "software-witness", BigInteger.ONE, new RawJson(state), framed, Instant.EPOCH);
    }

    private static void assertFirstFailure(String raw, String expected) {
        var failure = assertThrows(IllegalArgumentException.class,
                () -> DriverObservationAssembler.canonicalNativeState(softwareData(raw)));
        assertEquals(expected, failure.getMessage());
    }

    private static void assertLiteral(String expected, OpportunityJson.Value actual) {
        // No fixture string contains whitespace inside JSON string values.
        assertEquals(expected.replaceAll("\\s+", ""), new String(DriverJson.encode(actual), StandardCharsets.UTF_8));
    }
}
