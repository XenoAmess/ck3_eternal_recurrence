package org.xar.ck3.control.score.projection;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.ServiceLoader;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.*;
import org.xar.ck3.control.score.CampaignArithmeticCodec;
import org.xar.ck3.control.score.CampaignScoreCodec;
import org.xar.ck3.control.score.ScoreInterval;

/** Public projection wire: score decimal strings never become binary64 or native ScriptValue inputs. */
final class CampaignScorePrecisionProjectionTest {
    @Test void exportedStringsBeyondBinary64RoundtripWithoutMeasuringOrChangingTheirPrecision() {
        for (String text : List.of(
                "9007199254740993.0000000000000000000000000000000000000001",
                "1." + "0".repeat(78) + "05", "1." + "0".repeat(78) + "15",
                "123456789012345678901234567890123456789012345678901234567890123456789012345678901",
                "-0", "-0E+17", "0." + "0".repeat(99) + "1")) {
            ObjectNode expected = StrictJson.object().put("lower", text).put("upper", text)
                    .put("known", true).put("value", text);
            byte[] first = succeeded(request(expected));
            assertArrayEquals(StrictJson.canonical(expected), first, text);
            assertArrayEquals(first, succeeded(request(StrictJson.parse(first))), text);
            assertEquals(text, StrictJson.text(StrictJson.parse(first).get("value")));
        }
    }

    @Test void structuredNativeValuesAndNumericTokensCannotAcquireTheScoreProfileOrKnownStatus() {
        ObjectNode exact = CampaignScoreCodec.json(ScoreInterval.exact("9007199254740993"));
        for (String token : List.of("true", "false", "9007199254740993", "9007199254740993.0",
                "null", "[]", "{}")) {
            JsonNode otherDomain = StrictJson.parse(token.getBytes(StandardCharsets.UTF_8));
            for (String field : List.of("lower", "upper")) {
                ObjectNode changed = exact.deepCopy(); changed.set(field, otherDomain);
                rejected(request(changed));
            }
        }
        ObjectNode unknown = CampaignScoreCodec.json(ScoreInterval.UNKNOWN);
        JsonNode observed = StrictJson.parse(succeeded(request(unknown)));
        assertFalse(observed.get("known").booleanValue());
        assertTrue(observed.get("value").isNull());
        assertEquals("0", observed.get("lower").textValue());
        assertEquals("100", observed.get("upper").textValue());
        ObjectNode missing = unknown.deepCopy(); missing.remove("value"); rejected(request(missing));
        ObjectNode lied = unknown.deepCopy(); lied.put("known", true); rejected(request(lied));
        ObjectNode filled = unknown.deepCopy(); filled.put("value", "0"); rejected(request(filled));
        ObjectNode alienProfile = request(unknown); alienProfile.put("profile", "native-script-value");
        rejected(alienProfile);
        ObjectNode extra = request(unknown); extra.put("context", "unobserved"); rejected(extra);
    }

    private static ObjectNode request(JsonNode interval) {
        ObjectNode row = StrictJson.object().put("schema", CampaignArithmeticCodec.SCHEMA)
                .put("profile", CampaignArithmeticCodec.ArithmeticProfile.PYTHON_DECIMAL_DEFAULT_28_HALF_EVEN.wire())
                .put("operation", "roundtrip");
        row.set("input", interval); return row;
    }
    private static byte[] succeeded(ObjectNode request) {
        return assertInstanceOf(ProjectionResult.Succeeded.class, dispatch(request)).result().bytes();
    }
    private static void rejected(ObjectNode request) {
        ProjectionResult.Rejected result = assertInstanceOf(ProjectionResult.Rejected.class, dispatch(request));
        assertEquals(ProjectionError.Code.INVALID_PAYLOAD, result.error().code());
    }
    private static ProjectionResult dispatch(ObjectNode request) {
        ProjectionDispatcher dispatcher = ProjectionDispatcher.fromCatalogs(ServiceLoader.load(ProjectionPortCatalog.class));
        ProjectionCall call = new ProjectionCall(new ProjectionCall.Identity("score-decimal-domain-boundary",
                ProjectionOperation.CAMPAIGN_ARITHMETIC_EVALUATE), ProjectionJson.object(StrictJson.canonical(request), 65536));
        return dispatcher.dispatch(ProjectionWire.encodeCall(call));
    }
}
