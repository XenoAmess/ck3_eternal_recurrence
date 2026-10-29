package org.xar.ck3.control.contracts;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;

class GameGenerationDecimalTest {
    private static GameGeneration game(String birth) { return new GameGeneration(42, new PythonOnlyUInt64(new BigInteger(birth))); }
    private static ObjectNode input(String token) {
        return (ObjectNode) StrictJson.parse(("{\"pid\":42,\"creation_filetime\":" + token + "}").getBytes(StandardCharsets.UTF_8));
    }
    @Test void exact100nsTicksAndUint64MaximumRoundtripWithoutNumberCoercion() {
        for (String decimal : new String[] {"1", "9007199254740993", "134372284757522641", "18446744073709551615"}) {
            GameGeneration original = game(decimal);
            assertEquals(decimal, original.toJson().get("creation_filetime").textValue());
            assertEquals(original, GameGeneration.fromJson(StrictJson.parse(StrictJson.canonical(original.toJson()))));
        }
        assertNotEquals(game("134372284757522640"), game("134372284757522641"));
    }
    @Test void numericLegacyAndMalformedDecimalInputsCannotCreateCurrentIdentity() {
        for (String token : new String[] {"true", "null", "1", "9007199254740993", "134372284757522641.0", "1e2",
                "\"\"", "\"0\"", "\"01\"", "\"+1\"", "\"-1\"", "\" 1\"", "\"1 \"",
                "\"18446744073709551616\"", "\"2026-10-23T16:00:00.123456Z\""})
            assertThrows(ContractViolationException.class, () -> GameGeneration.fromJson(input(token)), token);
    }
    @Test void missingNullUnknownFieldsAndWrongPidTokensRemainRejected() {
        ObjectNode valid = game("134372284757522641").toJson();
        ObjectNode missing = valid.deepCopy(); missing.remove("creation_filetime");
        ObjectNode unknown = valid.deepCopy(); unknown.put("creationDate", "2026-10-23T16:00:00Z");
        assertThrows(ContractViolationException.class, () -> GameGeneration.fromJson(missing));
        assertThrows(ContractViolationException.class, () -> GameGeneration.fromJson(unknown));
        for (String token : new String[] {"true", "1.0", "\"42\"", "0", "4294967296"}) {
            var wrong = StrictJson.parse(("{\"pid\":" + token + ",\"creation_filetime\":\"1\"}").getBytes(StandardCharsets.UTF_8));
            assertThrows(ContractViolationException.class, () -> GameGeneration.fromJson(wrong));
        }
    }
    @Test void opaquePythonMapV1AndCurrentCrossLanguageLanesNeverAcceptEachOthersTokens() {
        GameGeneration actual = game("18446744073709551615");
        ObjectNode opaque = PythonOpaqueGameGenerationV1.toJson(actual);
        ObjectNode current = actual.toJson();
        assertTrue(opaque.get("creation_filetime").isIntegralNumber());
        assertTrue(current.get("creation_filetime").isTextual());
        assertEquals(actual, PythonOpaqueGameGenerationV1.fromJson(opaque));
        assertEquals(actual, GameGeneration.fromJson(current));
        assertThrows(ContractViolationException.class, () -> GameGeneration.fromJson(opaque));
        assertThrows(ContractViolationException.class, () -> PythonOpaqueGameGenerationV1.fromJson(current));
    }
}
