package org.xar.ck3.control.application.driver;

import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Arrays;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

final class DriverCanonicalNativeStatePublicOracle113Test {
    @Test
    void canonicalProjectionPreservesCompleteMilitaryDataAndInputCustody() {
        Input input = input("""
                {
                  "active_wars":[{
                    "war_id":18446744073709551616,"player_side":"attacker",
                    "targeted_title_ids":[9,9,8],"war_objective_province_ids":[11,11],
                    "objective_province_states":[{
                      "province_id":11,"occupation_observable":false,"siege_observable":true,
                      "active_siege":{
                        "siege_id":0,"besieging_army_id":7,"player_army_besieging":true,
                        "progress_fraction":{"raw":25000,"scale":100000},
                        "current_work":{"raw":25,"scale":100000},
                        "total_work":{"raw":100,"scale":100000},"assault_observable":false
                      }
                    }],
                    "player_relative_war_score":-2,
                    "allied_armies":[
                      {"army_id":7,"owner_character_id":9,"soldier_count":99,"controllable":true},
                      {"army_id":8,"owner_character_id":9,"controllable":true},
                      {"army_id":9,"owner_character_id":9,"controllable":false}
                    ],"enemy_armies":[]
                  }],
                  "player_armies":[{"army_id":7,"owner_character_id":9,"soldier_count":3,"controllable":true}],
                  "opaque":{"numbers":{"z":1e2,"a":-0.0,"large":9223372036854775808},"text":"???"},
                  "history":[{"n":-0.00e+3}],
                  "top_exclusive_modal_choice_hint":{"keep":1e+2,"pump_epoch":99,"thread_id":88}
                }
                """, BigInteger.ONE);
        byte[] expectedState = input.callerState().clone();
        byte[] expectedPacket = input.callerPacket().clone();
        Arrays.fill(input.callerState(), (byte) '!');
        Arrays.fill(input.callerPacket(), (byte) '!');
        Arrays.fill(input.original().state().bytes(), (byte) '?');
        Arrays.fill(input.original().originalPacket(), (byte) '?');

        OpportunityJson.Obj actual = DriverObservationAssembler.canonicalNativeState(input.original()).semantic();
        OpportunityJson.Obj expected = DriverJson.object("""
                {
                  "active_wars":[{
                    "war_id":18446744073709551616,"player_side":"attacker",
                    "primary_opponent_character_id":null,"player_is_primary_war_leader":null,
                    "enemy_primary_default_raise_province_id":null,
                    "targeted_title_ids":[9,8],"war_objective_province_ids":[11],
                    "objective_province_states":[{
                      "province_id":11,"occupation_observable":false,"is_occupied":null,
                      "occupying_character_id":null,"fort_level":null,"garrison_size":null,
                      "besieging_strength":null,"siege_observable":true,
                      "active_siege":{
                        "siege_id":0,"besieging_army_id":7,"player_army_besieging":true,
                        "progress_fraction":{"raw":25000,"scale":100000},
                        "current_work":{"raw":25,"scale":100000},
                        "total_work":{"raw":100,"scale":100000},
                        "remaining_work":{"raw":75,"scale":100000},
                        "days_left":null,"ordinary_daily_progress":null,"current_phase_length":null,
                        "prepared_phase_length":null,"phase_counter":null,"can_advance":null,
                        "phase_event_state":null,"prepared_selected_phase_event_enum":null,
                        "assault_observable":false,"breach_level":null,"assault_in_progress":null,
                        "can_start_assault":null,"can_stop_assault":null,"assault_daily_progress":null,
                        "assault_daily_casualties":null,"walls_breached":null
                      }
                    }],
                    "player_relative_war_score":-2,
                    "allied_armies":[
                      {"army_id":7,"owner_character_id":9,"soldiers":99,"current_province_id":null,
                       "move_target_province_id":null,"move_target_observable":false,"controllable":true,"source":"native"},
                      {"army_id":8,"owner_character_id":9,"soldiers":null,"current_province_id":null,
                       "move_target_province_id":null,"move_target_observable":false,"controllable":true,"source":"native"},
                      {"army_id":9,"owner_character_id":9,"soldiers":null,"current_province_id":null,
                       "move_target_province_id":null,"move_target_observable":false,"controllable":false,"source":"native"}
                    ],"enemy_armies":[],"source":"native"
                  }],
                  "player_armies":[
                    {"army_id":7,"owner_character_id":9,"soldiers":3,"current_province_id":null,
                     "move_target_province_id":null,"move_target_observable":false,"controllable":true,"source":"native"},
                    {"army_id":8,"owner_character_id":9,"soldiers":null,"current_province_id":null,
                     "move_target_province_id":null,"move_target_observable":false,"controllable":true,"source":"native"}
                  ],
                  "opaque":{"numbers":{"z":1e2,"a":-0.0,"large":9223372036854775808},"text":"???"},
                  "history":[{"n":-0.00e+3}],"top_exclusive_modal_choice_hint":{"keep":1e+2},
                  "format_version":1,"snapshot_id":"unit-snapshot","revision":1,
                  "active_event":null,"one_life_settlement":null,"played_character":null,
                  "played_character_gold":null,"played_character_prestige":null,"played_character_piety":null,
                  "pending_character_interaction":null
                }
                """.getBytes(StandardCharsets.UTF_8), DriverJson.MAX_NATIVE_BYTES);
        assertEquals(expected, actual);
        OpportunityJson.Obj opaque = OpportunityJson.object(actual.get("opaque"), "opaque");
        assertEquals("{\"z\":1e2,\"a\":-0.0,\"large\":9223372036854775808}", wire(opaque.get("numbers")));
        assertEquals("[{\"n\":-0.00e+3}]", wire(actual.get("history")));
        assertEquals("{\"keep\":1e+2}", wire(actual.get("top_exclusive_modal_choice_hint")));
        assertArrayEquals(expectedState, input.original().state().bytes());
        assertArrayEquals(expectedPacket, input.original().originalPacket());
    }

    @Test
    void militaryShapeErrorsPrecedeSemanticErrors() {
        firstFailure("{\"active_wars\":{},\"player_armies\":{},\"active_event\":17}",
                "native active_wars must be an array");
        firstFailure("{\"active_wars\":[],\"player_armies\":{},\"active_event\":17}",
                "native player_armies must be an array");
        firstFailure("{\"active_wars\":[],\"player_armies\":[],\"active_event\":17}",
                "active_event must be an object or null");
    }

    @Test
    void publicRevisionCallbackRemainsAfterMilitaryValidation() {
        IllegalStateException marker = new IllegalStateException("armed native revision");
        CallbackRevision earlyRevision = new CallbackRevision(marker);
        Input early = input("{\"active_wars\":{}}", earlyRevision);
        earlyRevision.arm();
        IllegalArgumentException earlier = assertThrows(IllegalArgumentException.class,
                () -> DriverObservationAssembler.canonicalNativeState(early.original()));
        plainFailure(earlier, "native active_wars must be an array");

        CallbackRevision lateRevision = new CallbackRevision(marker);
        Input late = input("{}", lateRevision);
        lateRevision.arm();
        IllegalStateException callback = assertThrows(IllegalStateException.class,
                () -> DriverObservationAssembler.canonicalNativeState(late.original()));
        assertTrue(callback == marker);
    }

    private static void firstFailure(String state, String expectedMessage) {
        Input input = input(state, BigInteger.ONE);
        IllegalArgumentException actual = assertThrows(IllegalArgumentException.class,
                () -> DriverObservationAssembler.canonicalNativeState(input.original()));
        plainFailure(actual, expectedMessage);
    }

    private static void plainFailure(IllegalArgumentException actual, String expectedMessage) {
        assertEquals(IllegalArgumentException.class, actual.getClass());
        assertEquals(expectedMessage, actual.getMessage());
        assertNull(actual.getCause());
    }

    private static String wire(OpportunityJson.Value value) {
        return new String(DriverJson.encode(value), StandardCharsets.UTF_8);
    }

    private static Input input(String state, BigInteger nativeRevision) {
        byte[] stateBytes = state.getBytes(StandardCharsets.UTF_8);
        RawJson raw = new RawJson(stateBytes);
        byte[] envelope = ("{\"type\":\"state_snapshot\",\"protocol_version\":1,"
                + "\"snapshot_id\":\"unit-snapshot\",\"revision\":1,\"state\":" + state + "}")
                .getBytes(StandardCharsets.UTF_8);
        byte[] packet = ByteBuffer.allocate(envelope.length + 4).order(ByteOrder.LITTLE_ENDIAN)
                .putInt(envelope.length).put(envelope).array();
        TransportSession session = new TransportSession("unit-machine",
                new GameGeneration(1, new PythonOnlyUInt64(BigInteger.ONE)), BigInteger.ONE, "unit-session");
        ObservedFrame original = new ObservedFrame(session, "unit-snapshot", nativeRevision, raw, packet, Instant.EPOCH);
        return new Input(original, stateBytes, packet);
    }

    private record Input(ObservedFrame original, byte[] callerState, byte[] callerPacket) { }

    private static final class CallbackRevision extends BigInteger {
        private static final long serialVersionUID = 1L;
        private transient IllegalStateException failure;
        private transient boolean armed;

        private CallbackRevision(IllegalStateException failure) {
            super("1");
            this.failure = failure;
        }

        private void arm() { armed = true; }

        @Override public int signum() {
            if (armed) throw failure;
            return super.signum();
        }
    }
}
