package org.xar.ck3.control.wave2.military.supplyschedule;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class FutureDailySupplyScheduleTest {
    private static JsonNode golden() throws IOException {
        try (var stream = FutureDailySupplyScheduleTest.class.getResourceAsStream("/supplyschedule/golden.json")) {
            assertNotNull(stream, "original producer golden missing; execute capture through storage/M7");
            return StrictJson.parse(stream.readAllBytes(), 131_072);
        }
    }
    @Test void actualOriginalNormalizerProjectionAndRoundTripAgree() throws IOException {
        JsonNode golden = golden(); assertEquals(7, golden.get("original_tests").intValue()); assertEquals(0, golden.get("original_skipped").intValue());
        assertFalse(golden.get("machine_id").textValue().isEmpty());
        assertEquals("NOTRUN", golden.get("native_collector_execution").textValue());
        for (JsonNode sample : golden.get("cases")) {
            String name = sample.get("name").textValue();
            var schedule = FutureDailySupplyScheduleCodec.decode(sample.get("input"));
            assertEquals(sample.get("normalized"), canonicalTree(FutureDailySupplyScheduleCodec.encode(schedule)), name);
            assertEquals(schedule, FutureDailySupplyScheduleCodec.decode(FutureDailySupplyScheduleCodec.encodeBytes(schedule)), name + " integer JSON roundtrip");
            var frames = FutureDailySupplyScheduleProjectionCodec.decodeFrames(sample.get("frames"));
            var projection = FutureDailySupplyScheduleProjection.project(schedule, frames);
            assertEquals(sample.get("projection"), canonicalTree(FutureDailySupplyScheduleProjectionCodec.encode(projection)), name);
            if (projection != null) {
                assertFalse(projection.actualFutureCallbackObserved()); assertFalse(projection.futureBucketMutationsReconstructed());
                assertFalse(projection.fullDailySupplyTransitionReady()); assertFalse(projection.fullMonthlyReady());
            }
        }
    }
    @Test void originalRawNegativeTokensAreRejectedWithoutFloatCoercion() throws IOException {
        JsonNode golden = golden(); String base = golden.get("negative_base_raw").textValue();
        for (JsonNode sample : golden.get("negatives")) {
            String field = sample.get("field").textValue();
            String needle = '"' + field + "\":" + sample.get("old_token").textValue();
            int index = base.indexOf(needle); assertTrue(index >= 0);
            String replacement = '"' + field + "\":" + sample.get("replacement_token").textValue();
            String raw = base.substring(0, index) + replacement + base.substring(index + needle.length());
            assertFalse(sample.get("accepted").booleanValue());
            assertThrows(IllegalArgumentException.class, () -> FutureDailySupplyScheduleCodec.decode(raw.getBytes(StandardCharsets.UTF_8)), field);
        }
        assertThrows(IllegalArgumentException.class, () -> FutureDailySupplyScheduleCodec.decode((base + " null").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> FutureDailySupplyScheduleCodec.decode(base.replaceFirst("\\{", "{\"schema_version\":1,").getBytes(StandardCharsets.UTF_8)));
    }
    @Test void actualNativeNextFrameConsumerJoinAgreesAndRejectsMismatchedClock() throws IOException {
        JsonNode joins = golden().get("joins");
        for (JsonNode sample : joins) {
            var joined = NativeNextDailySupplyScheduleCodec.fromSameQueryRow(sample.get("row"));
            assertEquals(sample.get("projection"), canonicalTree(NativeNextDailySupplyScheduleCodec.encode(joined)), sample.get("name").textValue());
        }
        ObjectNode row = joins.get(0).get("row").deepCopy();
        ((ObjectNode) row.get(FutureDailySupplyScheduleCodec.FAMILY_KEY)).put("current_date_storage_raw64", 43800001);
        assertThrows(IllegalArgumentException.class, () -> NativeNextDailySupplyScheduleCodec.fromSameQueryRow(row));
        ObjectNode day = joins.get(0).get("row").deepCopy();
        ((ObjectNode) day.get(FutureDailySupplyScheduleCodec.FAMILY_KEY)).put("native_day_index_raw_i32", 13).put("selected_phase_index_i32", 13);
        assertThrows(IllegalArgumentException.class, () -> NativeNextDailySupplyScheduleCodec.fromSameQueryRow(day));
    }
    @Test void sameQueryMaskingAndMissingNullExtensionsRemainDistinct() throws IOException {
        JsonNode cases = golden().get("cases"); JsonNode edge = cases.get(2).get("input");
        var value = FutureDailySupplyScheduleCodec.decode(edge, -1, Integer.MIN_VALUE);
        assertEquals(0xFFFF_FFFFL, value.subjectArmyIdU32()); assertEquals(Long.MIN_VALUE, value.currentDateStorageRaw64());
        assertThrows(IllegalArgumentException.class, () -> FutureDailySupplyScheduleCodec.decode(edge, 10, 20));
        ObjectNode row = StrictJson.object(); row.put("unrelated_sdk_extension", true);
        assertInstanceOf(FutureDailySupplyScheduleCodec.Missing.class, FutureDailySupplyScheduleCodec.fromSameQueryRow(row, 10, 20));
        row.putNull(FutureDailySupplyScheduleCodec.FAMILY_KEY);
        assertInstanceOf(FutureDailySupplyScheduleCodec.ExplicitNull.class, FutureDailySupplyScheduleCodec.fromSameQueryRow(row, 10, 20));
        row.set(FutureDailySupplyScheduleCodec.FAMILY_KEY, cases.get(0).get("input"));
        assertInstanceOf(FutureDailySupplyScheduleCodec.Present.class, FutureDailySupplyScheduleCodec.fromSameQueryRow(row, 10, 20));
        ObjectNode wrong = cases.get(0).get("input").deepCopy(); wrong.put("unrelated_sdk_extension", true);
        assertThrows(IllegalArgumentException.class, () -> FutureDailySupplyScheduleCodec.decode(wrong));
        ObjectNode missing = cases.get(0).get("input").deepCopy(); missing.remove("current_date_raw_i32");
        assertThrows(IllegalArgumentException.class, () -> FutureDailySupplyScheduleCodec.decode(missing));
        assertThrows(IllegalArgumentException.class, () -> FutureDailySupplyScheduleCodec.decode((JsonNode) null));
    }
    @Test void selectedPartialPhaseAndImmutableRepeatedOriginalSlots() throws IOException {
        var schedule = FutureDailySupplyScheduleCodec.decode(golden().get("cases").get(1).get("input"));
        var projection = FutureDailySupplyScheduleProjection.project(schedule, List.of(new FutureDailySupplyScheduleProjection.NativeFrame(43800024, 1)));
        assertFalse(projection.ready()); assertTrue(projection.prospectiveFrames().getFirst().conditionalBucketOccurrencesReady());
        assertEquals(List.of(0, 2), projection.prospectiveFrames().getFirst().matchingPositions());
        assertThrows(UnsupportedOperationException.class, () -> schedule.phases().clear());
        assertThrows(UnsupportedOperationException.class, () -> schedule.phases().get(1).matchingPositions().add(1));
        assertEquals(15, FutureDailySupplySchedule.phaseIndex(-1)); assertEquals(8, FutureDailySupplySchedule.phaseIndex(Integer.MIN_VALUE));
    }
    @Test void originalProducerAndAllConsumerSourcePinsAreBound() throws IOException, NoSuchAlgorithmException {
        String configured = System.getProperty("xar.repo");
        if (configured == null || configured.isBlank()) configured = System.getenv("XAR_REPO_ROOT");
        Path root;
        if (configured == null || configured.isBlank()) {
            root = Path.of("").toAbsolutePath();
            while (root != null && !Files.isDirectory(root.resolve("ck3_autonomous_player"))) root = root.getParent();
        } else {
            root = Path.of(configured).toAbsolutePath().normalize();
            assertTrue(Files.isDirectory(root.resolve("ck3_autonomous_player")), "configured repository source required");
        }
        assertNotNull(root, "repository source required to verify retained producer pins");
        for (JsonNode pin : golden().get("source_pins")) {
            String actual = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(root.resolve(pin.get("path").textValue()))));
            assertEquals(pin.get("sha256").textValue(), actual, pin.get("path").textValue());
        }
    }
    private static JsonNode canonicalTree(JsonNode value) { return StrictJson.parse(StrictJson.canonical(value, 131_072), 131_072); }
}
