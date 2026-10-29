package org.xar.ck3.control.nativebridge.capabilities.army;

import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import static org.junit.jupiter.api.Assertions.*;

/** The actual public decoder and persisted encoder for every one of the thirteen installed original services. */
final class ArmyPublic13ArgumentsTest {
    private record Case(PublicMethod method, String arguments, String boundedField) { }
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
    private static List<Case> cases() { return List.of(
            new Case(PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1, "{}", ""),
            new Case(PublicMethod.QUERY_PLAYER_TRUCE_EXPIRY_V1, "{\"toward_character_id\":1,\"expected_revision\":\"1\"}", "toward_character_id"),
            new Case(PublicMethod.QUERY_ARMY_GATHERING_RESEARCH_SAMPLING_V1, "{\"expected_revision\":\"1\"}", ""),
            new Case(PublicMethod.QUERY_BATTLE_CONTROL_SNAPSHOT_V1, "{\"subject_public_cunit_id\":0,\"expected_revision\":\"1\"}", "subject_public_cunit_id"),
            new Case(PublicMethod.QUERY_BATTLE_TRANSITION_V1, "{\"combat_id\":1,\"expected_revision\":\"1\"}", "combat_id"),
            new Case(PublicMethod.QUERY_BATTLE_TERMINAL_TRANSITION_V1, "{\"prior_combat_id\":1,\"subject_public_cunit_id\":0,\"expected_revision\":\"1\",\"after_terminal_sequence\":\"18446744073709551615\",\"character_ids\":[]}", "subject_public_cunit_id"),
            new Case(PublicMethod.PREVIEW_ACTIVE_COMBAT_RETREAT_V1, "{\"selected_public_cunit_id\":0,\"target_province_id\":1,\"expected_revision\":\"1\"}", "selected_public_cunit_id"),
            new Case(PublicMethod.ORDER_ACTIVE_COMBAT_RETREAT_V1, "{\"selected_public_cunit_id\":0,\"expected_revision\":\"1\",\"expected_combat_id\":1,\"expected_side_index\":0,\"expected_scope\":\"full_side\",\"target_province_id\":1,\"candidate_token\":\"original-candidate-token-0123456789\"}", "expected_side_index"),
            new Case(PublicMethod.QUERY_WAR_DECLARED_OVERVIEW_V1, "{\"expected_revision\":\"1\"}", ""),
            new Case(PublicMethod.QUERY_WAR_RESULTS_WINDOW_V1, "{\"expected_revision\":\"1\"}", ""),
            new Case(PublicMethod.QUERY_PLAYER_MERCENARY_CONTEXT_V1, "{\"expected_revision\":\"1\"}", ""),
            new Case(PublicMethod.QUERY_ARMY_COMMANDER_CANDIDATES_V1, "{\"army_id\":0,\"target_province_id\":1}", "army_id"),
            new Case(PublicMethod.QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1, "{\"selected_public_cunit_id\":0,\"expected_revision\":\"1\"}", "selected_public_cunit_id")); }
    @Test void allThirteenActualInputModelsRoundTripAndRejectWrongMissingOrExtraFields() {
        assertEquals(13, cases().stream().map(Case::method).distinct().count());
        for (Case c : cases()) {
            var actual = ArmyCallCodec.decode(c.method(), raw(c.arguments()));
            assertEquals(actual, ArmyCallCodec.decode(c.method(), ArmyCallCodec.encode(actual)), c.method().pythonName());
            var extra = ArmyJson.parse(raw(c.arguments()).bytes()).put("not_an_argument", 1);
            assertThrows(IllegalArgumentException.class, () -> ArmyCallCodec.decode(c.method(), new RawJson(ArmyJson.bytes(extra))));
            if (!c.boundedField().isEmpty()) {
                var value = ArmyJson.parse(raw(c.arguments()).bytes()); value.remove(c.boundedField());
                assertThrows(IllegalArgumentException.class, () -> ArmyCallCodec.decode(c.method(), new RawJson(ArmyJson.bytes(value))));
                var bool = ArmyJson.parse(raw(c.arguments()).bytes()).put(c.boundedField(), true);
                assertThrows(IllegalArgumentException.class, () -> ArmyCallCodec.decode(c.method(), new RawJson(ArmyJson.bytes(bool))));
                var decimal = ArmyJson.parse(raw(c.arguments()).bytes()).put(c.boundedField(), 1.0);
                assertThrows(IllegalArgumentException.class, () -> ArmyCallCodec.decode(c.method(), new RawJson(ArmyJson.bytes(decimal))));
                var text = ArmyJson.parse(raw(c.arguments()).bytes()).put(c.boundedField(), "1");
                assertThrows(IllegalArgumentException.class, () -> ArmyCallCodec.decode(c.method(), new RawJson(ArmyJson.bytes(text))));
            }
        }
    }
    @Test void revisionsRetainFullUnsigned64WhileNumericInputsRequireTheSafeRange() {
        var method = PublicMethod.QUERY_WAR_RESULTS_WINDOW_V1;
        var maximum = ArmyCallCodec.decode(method, raw("{\"expected_revision\":\"18446744073709551615\"}"));
        assertEquals(maximum, ArmyCallCodec.decode(method, ArmyCallCodec.encode(maximum)));
        for (String invalid : List.of("true", "1.0", "9007199254740992", "\"01\"", "\"-1\"", "null", "\"18446744073709551616\""))
            assertThrows(IllegalArgumentException.class, () -> ArmyCallCodec.decode(method, raw("{\"expected_revision\":" + invalid + "}")));
    }
}
