package org.xar.ck3.control.contracts;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;

class CampaignMapAdmissionComposerTest {
    private static ObjectNode request() {
        ObjectNode row = StrictJson.object();
        row.put("schema", CampaignMapAdmissionComposer.REQUEST_SCHEMA);
        row.put("machine_id", "xenoamess-full-tower-eb9d2c1186");
        row.put("observed_at_utc", "2026-10-22T12:00:00.123456+00:00");
        row.set("native_launch", new GameGeneration(200332,
                new PythonOnlyUInt64(new BigInteger("134371375868945259"))).toJson());
        row.put("recording_session_id", "recording-actual-session");
        row.set("actual_initial_frame", new SavedFrame("native:1", 2, 1,
                53279400, 40526, "native-40526-1bec95182886").toJson());
        row.put("game_map_visible", true); row.put("decision_text_visible", true);
        return row;
    }

    private static byte[] input(ObjectNode row) {
        // Malformed-number tests need actual float tokens that production canonical output forbids.
        return row.toString().getBytes(StandardCharsets.UTF_8);
    }

    @Test
    void producerWritesExactNumericUint64AndCurrentPythonFields() {
        byte[] output = CampaignMapAdmissionComposer.compose(input(request()));
        CampaignMapAdmission receipt = CampaignMapAdmission.fromJson(StrictJson.parse(output));
        assertEquals(new BigInteger("134371375868945259"), receipt.game().creationFiletime().value());
        String actual = new String(output, StandardCharsets.UTF_8);
        assertTrue(actual.contains("\"game_creation_filetime\":134371375868945259"));
        assertFalse(actual.contains("\"game_creation_filetime\":\""));
        assertTrue(actual.startsWith("{\"Game_map_visible\":true,\"actual_initial_frame\":"));
        assertArrayEquals(output, receipt.toCanonicalBytes());
    }

    @Test
    void exactUint64MaximumSurvivesProducerAndParseRoundtrip() {
        ObjectNode request = request();
        ((ObjectNode) request.get("native_launch")).put("creation_filetime", StrictJson.UINT64_MAX);
        byte[] output = CampaignMapAdmissionComposer.compose(input(request));
        assertEquals(StrictJson.UINT64_MAX,
                CampaignMapAdmission.fromJson(StrictJson.parse(output)).game().creationFiletime().value());
        assertArrayEquals(output, StrictJson.canonical(StrictJson.parse(output), StrictJson.OUTPUT_MAX_BYTES));
    }

    @Test
    void boolFloatStringNullAndOutOfRangeBirthAreRejected() {
        String[] invalid = {"true", "134371375868945259.0", "1e2", "\"134371375868945259\"", "null",
                "0", "-1", "18446744073709551616"};
        for (String value : invalid) {
            String body = request().toString().replace("134371375868945259", value);
            assertThrows(ContractViolationException.class,
                    () -> CampaignMapAdmissionComposer.compose(body.getBytes(StandardCharsets.UTF_8)), value);
        }
    }

    @Test
    void missingNullArrayAndUnknownFieldsRemainDistinctAndRejected() {
        ObjectNode base = request();
        for (String key : new String[] {"machine_id", "observed_at_utc", "native_launch", "recording_session_id",
                "actual_initial_frame", "schema", "game_map_visible", "decision_text_visible"}) {
            ObjectNode missing = base.deepCopy(); missing.remove(key);
            assertThrows(ContractViolationException.class, () -> CampaignMapAdmissionComposer.compose(input(missing)), key);
            ObjectNode nullValue = base.deepCopy(); nullValue.putNull(key);
            assertThrows(ContractViolationException.class, () -> CampaignMapAdmissionComposer.compose(input(nullValue)), key);
            ObjectNode emptyArray = base.deepCopy(); emptyArray.putArray(key);
            assertThrows(ContractViolationException.class, () -> CampaignMapAdmissionComposer.compose(input(emptyArray)), key);
        }
        ObjectNode unknown = base.deepCopy(); unknown.put("game_birth", 1);
        assertThrows(ContractViolationException.class, () -> CampaignMapAdmissionComposer.compose(input(unknown)));
    }

    @Test
    void nestedAliasesAndWrongFrameNumbersAreRejected() {
        ObjectNode unknownLaunch = request();
        ((ObjectNode) unknownLaunch.get("native_launch")).put("creationFiletime", 123);
        assertThrows(ContractViolationException.class, () -> CampaignMapAdmissionComposer.compose(input(unknownLaunch)));
        for (String key : new String[] {"revision", "native_revision", "date_raw", "actor_character_id"}) {
            ObjectNode wrong = request();
            ((ObjectNode) wrong.get("actual_initial_frame")).put(key, true);
            assertThrows(ContractViolationException.class, () -> CampaignMapAdmissionComposer.compose(input(wrong)), key);
            ObjectNode unsafe = request();
            ((ObjectNode) unsafe.get("actual_initial_frame")).put(key, StrictJson.MAX_SAFE_INTEGER + 1);
            assertThrows(ContractViolationException.class, () -> CampaignMapAdmissionComposer.compose(input(unsafe)), key);
        }
        ObjectNode mismatch = request();
        ((ObjectNode) mismatch.get("actual_initial_frame")).put("snapshot_id", "native:2");
        assertThrows(ContractViolationException.class, () -> CampaignMapAdmissionComposer.compose(input(mismatch)));
    }

    @Test
    void duplicateTrailingJsonAndInvalidUtf8AreRejected() {
        String duplicate = request().toString().replace("\"machine_id\":", "\"machine_id\":\"duplicate\",\"machine_id\":");
        assertThrows(ContractViolationException.class,
                () -> CampaignMapAdmissionComposer.compose(duplicate.getBytes(StandardCharsets.UTF_8)));
        String trailing = request() + " {}";
        assertThrows(ContractViolationException.class,
                () -> CampaignMapAdmissionComposer.compose(trailing.getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> StrictJson.parse(new byte[] {(byte) 0xc3, 0x28}));
    }

    @Test
    void pythonCanonicalEscapingRetainsUnicodeAndLowercaseControlHex() {
        ObjectNode request = request();
        request.put("machine_id", "中文😀\\\"\n\u000b\u001f");
        byte[] output = CampaignMapAdmissionComposer.compose(input(request));
        String actual = new String(output, StandardCharsets.UTF_8);
        assertTrue(actual.contains("中文😀\\\\\\\"\\n\\u000b\\u001f"), actual);
        assertEquals("中文😀\\\"\n\u000b\u001f", CampaignMapAdmission.fromJson(StrictJson.parse(output)).machineId());
    }

    @Test
    void requestBudgetAndMapOutputBudgetAreIndependentUtf8ByteLimits() {
        ObjectNode fittingInput = request();
        fittingInput.put("machine_id", "界".repeat(6000));
        byte[] raw = input(fittingInput);
        assertTrue(raw.length < StrictJson.INPUT_MAX_BYTES);
        assertThrows(ContractViolationException.class, () -> CampaignMapAdmissionComposer.compose(raw));
        assertThrows(ContractViolationException.class, () -> StrictJson.parse(new byte[StrictJson.INPUT_MAX_BYTES + 1]));
    }

    @Test
    void exactMapOutputByteBoundaryAcceptsUnicodeThenRejectsOneExtraByte() {
        ObjectNode base = request();
        base.put("machine_id", "x");
        int overhead = CampaignMapAdmissionComposer.compose(input(base)).length - 1;
        int available = StrictJson.OUTPUT_MAX_BYTES - overhead;
        for (String value : new String[] {"x".repeat(available),
                "界".repeat(available / 3) + "x".repeat(available % 3)}) {
            ObjectNode exact = request(); exact.put("machine_id", value);
            assertEquals(StrictJson.OUTPUT_MAX_BYTES, CampaignMapAdmissionComposer.compose(input(exact)).length);
            exact.put("machine_id", value + "x");
            assertThrows(ContractViolationException.class, () -> CampaignMapAdmissionComposer.compose(input(exact)));
        }
    }

    @Test
    void utcOffsetZeroIsRequiredAndOriginalSpellingPreserved() {
        for (String observed : new String[] {"2026-10-22T12:00:00Z", "2026-10-22 12:00:00+00:00",
                "2026-10-22T12:00:00.123456+00:00", "2026-10-22T12:00:00-00:00",
                "20261022T120000Z", "2026-W43-4T12:00:00+00:00", "2026-10-22T12:00:00.123456789+00:00"}) {
            ObjectNode request = request(); request.put("observed_at_utc", observed);
            CampaignMapAdmission result = CampaignMapAdmission.fromJson(
                    StrictJson.parse(CampaignMapAdmissionComposer.compose(input(request))));
            assertEquals(observed, result.observedAtUtc());
        }
        for (String bad : new String[] {"2026-10-22T12:00:00", "2026-10-22T12:00:00+01:00", "unknown"}) {
            ObjectNode request = request(); request.put("observed_at_utc", bad);
            assertThrows(ContractViolationException.class, () -> CampaignMapAdmissionComposer.compose(input(request)));
        }
    }

    @Test
    void refsAndOsStatDecimalIdentityHaveTheirOwnRoundtripContracts() {
        ExactRef reference = new ExactRef("Z:/证据\\map.json", 999, "ab".repeat(32));
        assertEquals(reference, ExactRef.fromJson(StrictJson.parse(StrictJson.canonical(reference.toJson()))));
        FileStatIdentity identity = new FileStatIdentity(new BigInteger("117661285"),
                "281474988852756", "1792638019516614900");
        assertEquals(identity, FileStatIdentity.fromJson(StrictJson.parse(StrictJson.canonical(identity.toJson())),
                FileStatIdentity.SCHEMA));
        assertThrows(ContractViolationException.class, () -> FileStatIdentity.fromJson(identity.toJson(), "FILETIME"));
        ObjectNode bad = identity.toJson(); bad.put("file_id", 281474988852756L);
        assertThrows(ContractViolationException.class, () -> FileStatIdentity.fromJson(bad, FileStatIdentity.SCHEMA));
        assertThrows(ContractViolationException.class, () -> new CrossJsDecimalUInt64("01"));
        assertEquals("18446744073709551615", new CrossJsDecimalUInt64("18446744073709551615").decimal());
        assertEquals(StrictJson.UINT64_MAX, new PythonOnlyUInt64(StrictJson.UINT64_MAX).value());
        JsonNode nullNode = StrictJson.parse("null".getBytes(StandardCharsets.UTF_8));
        assertTrue(nullNode.isNull());
        assertFalse(StrictJson.parse("[]".getBytes(StandardCharsets.UTF_8)).isNull());
    }
}
