package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

final class PublicSnapshotCodecCorePowerPublicBoundaryTest {
    private static final String MINIMUM = "-9223372036854775808";
    private static final String MAXIMUM = "9223372036854775807";
    private static final String AVAILABLE_ROW = """
            {"status":"available","army_id":0,"native_carmy_id":10,"scope_role":"player",
             "war_ids":[],"regiment_count":0,"current_soldiers":0,"maximum_soldiers":0,
             "ai_base_power_raw":POWER,"ai_base_power_scale":100000,"unavailable_reason":null}
            """;
    private static final String UNAVAILABLE_ROW = """
            {"status":"unavailable","army_id":3,"native_carmy_id":null,"scope_role":"player",
             "war_ids":[],"regiment_count":null,"current_soldiers":null,"maximum_soldiers":null,
             "ai_base_power_raw":null,"ai_base_power_scale":100000,"unavailable_reason":"not_retained"}
            """;

    @Test
    void signed64PowerRoundtripsPreserveTypesAndRawByteOwnership() {
        String rows = "[" + AVAILABLE_ROW.replace("POWER", MINIMUM) + ","
                + AVAILABLE_ROW.replace("POWER", MAXIMUM).replace("\"army_id\":0", "\"army_id\":1") + ","
                + AVAILABLE_ROW.replace("POWER", "0").replace("\"army_id\":0", "\"army_id\":2") + ","
                + UNAVAILABLE_ROW + "]";
        byte[] expectedInput = snapshot(rows, "partial", 1).bytes();
        for (Function<RawJson, RawJson> encode : List.<Function<RawJson, RawJson>>of(
                PublicSnapshotCodec::encodeSemanticData, PublicSnapshotCodec::encodePlanningSnapshotData)) {
            byte[] supplied = expectedInput.clone();
            RawJson original = new RawJson(supplied);
            supplied[0] = (byte) '!';
            byte[] exposed = original.bytes();
            exposed[0] = (byte) '!';
            assertArrayEquals(expectedInput, original.bytes());

            RawJson encoded = encode.apply(original);
            var projected = DriverJson.object(encoded.bytes(), RawJson.MAXIMUM_BYTES);
            var publicRows = OpportunityJson.array(projected.get("army_strengths"), "public rows");
            assertEquals(4, publicRows.size());
            assertEquals(new OpportunityJson.Text(MINIMUM),
                    OpportunityJson.object(publicRows.get(0), "minimum row").get("ai_base_power_raw"));
            assertEquals(new OpportunityJson.Text(MAXIMUM),
                    OpportunityJson.object(publicRows.get(1), "maximum row").get("ai_base_power_raw"));
            assertEquals(new OpportunityJson.Text("0"),
                    OpportunityJson.object(publicRows.get(2), "zero row").get("ai_base_power_raw"));
            assertEquals(OpportunityJson.Nil.INSTANCE,
                    OpportunityJson.object(publicRows.get(3), "unavailable row").get("ai_base_power_raw"));
            assertEquals(new OpportunityJson.IntegerValue(BigInteger.valueOf(100000)),
                    OpportunityJson.object(publicRows.get(0), "minimum row").get("ai_base_power_scale"));
            var opaque = OpportunityJson.object(projected.get("opaque"), "opaque");
            assertEquals(new OpportunityJson.IntegerValue(BigInteger.valueOf(7)), opaque.get("n"));
            assertEquals(new OpportunityJson.Text("9223372036854775808"), opaque.get("note"));

            byte[] expectedEncoded = encoded.bytes();
            byte[] exposedEncoded = encoded.bytes();
            exposedEncoded[0] = (byte) '!';
            assertArrayEquals(expectedEncoded, encoded.bytes());
            RawJson decoded = PublicSnapshotCodec.decodeSemanticData(encoded);
            var restored = DriverJson.object(decoded.bytes(), RawJson.MAXIMUM_BYTES);
            var restoredRows = OpportunityJson.array(restored.get("army_strengths"), "restored rows");
            assertEquals(new OpportunityJson.IntegerValue(new BigInteger(MINIMUM)),
                    OpportunityJson.object(restoredRows.get(0), "minimum row").get("ai_base_power_raw"));
            assertEquals(new OpportunityJson.IntegerValue(new BigInteger(MAXIMUM)),
                    OpportunityJson.object(restoredRows.get(1), "maximum row").get("ai_base_power_raw"));
            assertEquals(new OpportunityJson.IntegerValue(BigInteger.ZERO),
                    OpportunityJson.object(restoredRows.get(2), "zero row").get("ai_base_power_raw"));
            assertEquals(OpportunityJson.Nil.INSTANCE,
                    OpportunityJson.object(restoredRows.get(3), "unavailable row").get("ai_base_power_raw"));
            assertEquals(opaque, restored.get("opaque"));
            assertArrayEquals(expectedInput, original.bytes());
            assertArrayEquals(expectedEncoded, encoded.bytes());
        }
    }

    @Test
    void coreAdmissionRetainsItsPublicCategoryWidthAndFirstErrors() {
        String badShape = AVAILABLE_ROW.replace("POWER", "9223372036854775808")
                .replace("\"unavailable_reason\":null", "\"unavailable_reason\":null,\"extra\":true");
        String[][] cases = {
                {AVAILABLE_ROW.replace("POWER", "9223372036854775808"), "1", "Core power requires signed64"},
                {AVAILABLE_ROW.replace("POWER", "-9223372036854775809"), "1", "Core power requires signed64"},
                {AVAILABLE_ROW.replace("POWER", "1.0"), "1", "ai_base_power_raw must be an integer token"},
                {AVAILABLE_ROW.replace("POWER", "true"), "1", "ai_base_power_raw must be an integer token"},
                {AVAILABLE_ROW.replace("POWER", "null"), "1", "ai_base_power_raw must be an integer token"},
                {AVAILABLE_ROW.replace("POWER", "\"not-a-number\""), "1", "ai_base_power_raw must be an integer token"},
                {badShape, "1", "exact eleven Core fields required"},
                {badShape, "0", "positive Core query sequence required"}
        };
        for (String[] example : cases) {
            RawJson original = snapshot("[" + example[0] + "]", "available", Integer.parseInt(example[1]));
            byte[] expectedInput = original.bytes();
            for (Function<RawJson, RawJson> encode : List.<Function<RawJson, RawJson>>of(
                    PublicSnapshotCodec::encodeSemanticData, PublicSnapshotCodec::encodePlanningSnapshotData)) {
                IllegalArgumentException failure = assertThrows(
                        IllegalArgumentException.class, () -> encode.apply(original));
                assertEquals(IllegalArgumentException.class, failure.getClass());
                assertEquals(example[2], failure.getMessage());
                assertNull(failure.getCause());
                assertArrayEquals(expectedInput, original.bytes());
            }
        }
    }

    private static RawJson snapshot(String rows, String status, int sequence) {
        String json = """
                {"format_version":1,"snapshot_id":"fixture-snapshot","revision":0,"native_revision":1,
                 "date_raw":0,"paused":true,"map_ready":true,"speed":1,"episode_run_id":"fixture-episode",
                 "episode_character_id":1,"active_wars":[],"player_armies":[],"diagnostics":{},
                 "active_event":null,"pending_character_interaction":null,"one_life_terminal_reason":null,
                 "native_command_history":[],"army_strengths":
                """ + rows + ",\"army_strengths_status\":\"" + status + "\",\"army_strengths_query_sequence\":" + sequence + """
                ,"army_strengths_queried_snapshot_id":"fixture-source","army_strengths_queried_revision":0,
                 "army_strengths_profile":"ordinary_core_v1","army_observed_phase_coverage":"not_requested",
                 "opaque":{"n":7,"note":"9223372036854775808"}}
                """;
        return new RawJson(json.getBytes(StandardCharsets.UTF_8));
    }
}
