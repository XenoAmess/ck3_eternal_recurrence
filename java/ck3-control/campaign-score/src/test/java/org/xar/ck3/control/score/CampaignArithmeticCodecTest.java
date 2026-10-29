package org.xar.ck3.control.score;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual frozen original function calls through the new typed consumer/serialization boundary. */
final class CampaignArithmeticCodecTest {
    private static final String RESOURCE = "/org/xar/ck3/control/score/campaign_score_python_golden_v1.jsonl";

    @Test void allOriginalArithmeticCallsUseTypedProfileAndRoundtrip() throws Exception {
        try (var stream = getClass().getResourceAsStream(RESOURCE)) {
            assertNotNull(stream, "actual original producer corpus required; missing is failure");
            byte[] raw = stream.readNBytes(512 * 1024 + 1);
            assertTrue(raw.length > 0 && raw.length <= 512 * 1024);
            String[] lines = new String(raw, StandardCharsets.UTF_8).split("\n");
            JsonNode header = StrictJson.parse(bytes(lines[0]));
            assertEquals(28, header.path("decimal_default_precision").intValue());
            assertEquals("ba4421fdc66048852e3c7a158a461e8fa2dad5d96c75904e4077e8797652dd4d",
                    header.path("source_sha256").path("ck3_autonomous_player/src/xar_autoplayer/campaign_development_score_v1.py").textValue());
            int count = 0;
            for (int index = 1; index < lines.length; index++) {
                JsonNode vector = StrictJson.parse(bytes(lines[index]));
                ObjectNode request = request(vector.path("operation").textValue(), vector.get("input"));
                byte[] wire = StrictJson.canonical(request);
                if ("invalid_contract".equals(vector.path("expected_kind").textValue())) {
                    assertThrows(ContractViolationException.class, () -> CampaignArithmeticCodec.evaluate(wire));
                } else {
                    var typed = CampaignArithmeticCodec.decode(wire);
                    byte[] actual = CampaignArithmeticCodec.evaluate(wire);
                    assertArrayEquals(StrictJson.canonical(vector.get("expected")), actual);
                    byte[] roundtrip = CampaignArithmeticCodec.encodeRequest(typed);
                    assertEquals(typed, CampaignArithmeticCodec.decode(roundtrip));
                    assertArrayEquals(actual, CampaignArithmeticCodec.evaluate(roundtrip));
                }
                count++;
            }
            assertEquals(header.path("vector_count").intValue(), count); assertTrue(count >= 30);
        }
    }

    @Test void strictProfileOperationFieldAndNumericTokensCannotCoerce() {
        ObjectNode valid = request("roundtrip", CampaignScoreCodec.json(ScoreInterval.UNKNOWN));
        for (String field : List.of("schema", "profile", "operation", "input")) {
            ObjectNode changed = valid.deepCopy(); changed.remove(field); refused(changed);
            changed = valid.deepCopy(); changed.putNull(field); refused(changed);
        }
        ObjectNode changed = valid.deepCopy(); changed.put("profile", "ROUND_UP"); refused(changed);
        changed = valid.deepCopy(); changed.put("decimal_context", "default"); refused(changed);
        changed = valid.deepCopy(); changed.put("operation", "aggregate_state"); refused(changed);
        for (String token : List.of("true", "2.0", "null", "\"2\"")) {
            String display = "{\"schema\":\"" + CampaignArithmeticCodec.SCHEMA + "\",\"profile\":\""
                    + CampaignArithmeticCodec.ArithmeticProfile.PYTHON_DECIMAL_DEFAULT_28_HALF_EVEN.wire()
                    + "\",\"operation\":\"display\",\"input\":{\"lower\":\"1.005\",\"upper\":\"1.005\",\"places\":" + token + "}}";
            assertThrows(ContractViolationException.class, () -> CampaignArithmeticCodec.decode(bytes(display)));
        }
        assertThrows(ContractViolationException.class, () -> new CampaignArithmeticCodec.Request(
                CampaignArithmeticCodec.ArithmeticProfile.PYTHON_DECIMAL_DEFAULT_28_HALF_EVEN,
                CampaignArithmeticCodec.Operation.AGGREGATE, new CampaignArithmeticCodec.IntervalInput(ScoreInterval.UNKNOWN)));
    }

    private static ObjectNode request(String operation, JsonNode input) {
        ObjectNode request = StrictJson.object().put("schema", CampaignArithmeticCodec.SCHEMA)
                .put("profile", CampaignArithmeticCodec.ArithmeticProfile.PYTHON_DECIMAL_DEFAULT_28_HALF_EVEN.wire())
                .put("operation", operation);
        request.set("input", input); return request;
    }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static void refused(ObjectNode row) {
        assertThrows(ContractViolationException.class, () -> CampaignArithmeticCodec.decode(StrictJson.canonical(row)));
    }
}
