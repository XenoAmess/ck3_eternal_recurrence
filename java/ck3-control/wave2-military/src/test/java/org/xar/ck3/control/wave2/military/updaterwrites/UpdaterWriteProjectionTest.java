package org.xar.ck3.control.wave2.military.updaterwrites;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;

class UpdaterWriteProjectionTest {
    private static final ObjectMapper JSON = new ObjectMapper();

    @Test void originalCompleteProducerProjectionGolden() throws IOException {
        JsonNode golden = golden();
        assertTrue(golden.path("projections").size() >= 20);
        for (JsonNode vector : golden.path("projections")) {
            UpdaterInput input = UpdaterWriteCodec.decode(JSON.writeValueAsBytes(vector.get("input")));
            assertEquals(vector.get("expected"), UpdaterWriteCodec.encode(UpdaterWriteProjection.project(input)), vector.path("id").asText());
        }
    }

    @Test void nativeFamilyLegacyExtendedAndNullRoundTrip() throws IOException {
        int legacy = 0, extended = 0;
        for (JsonNode vector : golden().path("projections")) {
            JsonNode original = vector.path("input").get("source_derived_next_daily_supply_frame_inputs_v1");
            SourceNextFrame frame = SourceNextFrameCodec.decode(original, 11, 12);
            if (original != null) assertEquals(original, SourceNextFrameCodec.encode(frame));
            if (frame instanceof SourceNextFrame.Legacy19) {
                legacy++;
                assertFalse(SourceNextFrameCodec.encode(frame).has("source_derived_full_cdate64_ready"));
            } else if (frame instanceof SourceNextFrame.Extended23) extended++;
        }
        assertTrue(legacy > 0); assertTrue(extended > 0);
        assertNull(SourceNextFrameCodec.decode(com.fasterxml.jackson.databind.node.NullNode.getInstance(), 11, 12));
    }

    @Test void actualOriginalRuntimeRejectionVectors() throws IOException {
        JsonNode vectors = golden().path("rejections");
        assertTrue(vectors.size() >= 8);
        for (JsonNode vector : vectors) {
            byte[] raw = vector.path("raw_json").textValue().getBytes(StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> SourceNextFrameCodec.decode(raw, 11, 12), vector.path("id").asText());
        }
    }

    @Test void firstRejectionDoesNotRequireLaterOperandsOrNextDate() {
        UpdaterInput input = new UpdaterInput(true, 11, 12, new UpdaterInput.GateInputs(3, null, null, null),
                new UpdaterInput.ClockInputs(null, null, null, null, 99L, null), new UpdaterInput.CallerInputs(null, null), null);
        UpdaterProjection result = UpdaterWriteProjection.project(input);
        assertTrue(result.ready()); assertEquals(false, result.nextAdmission().admitted());
        assertEquals("unit_native_170_raw", result.nextAdmission().rejection());
        assertEquals(1, result.nextAdmission().witnesses().size()); assertEquals(List.of(), result.missingInputs());
        ConditionalWrite.Date188Write date = assertInstanceOf(ConditionalWrite.Date188Write.class, result.conditionalWrites().get(1));
        assertEquals(99L, date.conditionalValue()); assertEquals(false, date.wouldWrite());
    }

    @Test void signed32DifferenceUsesTruncationTowardZeroAndStrictGreater() throws IOException {
        ObjectNode row = golden().path("projections").get(0).get("input").deepCopy();
        ObjectNode clock = (ObjectNode) row.get("army_update_clock_v1");
        ObjectNode future = (ObjectNode) row.get("source_derived_next_daily_supply_frame_inputs_v1");
        future.put("source_derived_next_date_raw_i32", Integer.MIN_VALUE); clock.put("grace_anchor_date_raw", Integer.MAX_VALUE);
        clock.put("loaded_grace_days", 0);
        UpdaterProjection wrapped = UpdaterWriteProjection.project(UpdaterWriteCodec.decode(row));
        assertEquals(false, wrapped.nextAdmission().admitted());
        UpdaterAdmission.GraceWitness witness = assertInstanceOf(UpdaterAdmission.GraceWitness.class, wrapped.nextAdmission().witnesses().getLast());
        assertEquals(1, witness.elapsedDateRawI32()); assertEquals(0, witness.elapsedDays());
        future.put("source_derived_next_date_raw_i32", 100); clock.put("grace_anchor_date_raw", 123); clock.put("loaded_grace_days", -1);
        UpdaterProjection negative = UpdaterWriteProjection.project(UpdaterWriteCodec.decode(row));
        assertEquals(true, negative.nextAdmission().admitted());
        assertEquals(0, assertInstanceOf(UpdaterAdmission.GraceWitness.class, negative.nextAdmission().witnesses().getLast()).elapsedDays());
    }

    @Test void noSyntheticFullDateAndNoActualWritesAreInvented() throws IOException {
        for (JsonNode vector : golden().path("projections")) {
            UpdaterProjection result = UpdaterWriteProjection.project(UpdaterWriteCodec.decode(vector.get("input")));
            if (Boolean.TRUE.equals(result.nextAdmission().admitted()) && result.sourceNextDate() instanceof SourceNextFrame.Legacy19) {
                assertFalse(result.ready()); assertTrue(result.missingInputs().contains(
                        "source_derived_next_daily_supply_frame_inputs_v1.source_derived_next_date_storage_raw64"));
            }
            JsonNode wire = UpdaterWriteCodec.encode(result);
            for (JsonNode write : wire.path("conditional_writes")) assertFalse(write.path("actual_write_observed").booleanValue());
            assertFalse(wire.path("actual_future_writes_observed").booleanValue());
        }
    }

    @Test void schemaRejectsRawFloatDuplicateUnknownAndPartialExtension() throws IOException {
        JsonNode row = golden().path("projections").get(0).get("input");
        JsonNode frame = row.get("source_derived_next_daily_supply_frame_inputs_v1");
        String raw = JSON.writeValueAsString(frame);
        String wrongFloat = raw.replace("\"schema_version\":1", "\"schema_version\":1.0");
        assertNotEquals(raw, wrongFloat);
        assertThrows(IllegalArgumentException.class, () -> SourceNextFrameCodec.decode(wrongFloat.getBytes(StandardCharsets.UTF_8), 11, 12));
        assertThrows(IllegalArgumentException.class, () -> SourceNextFrameCodec.decode((raw + "{}").getBytes(StandardCharsets.UTF_8), 11, 12));
        assertThrows(IllegalArgumentException.class, () -> SourceNextFrameCodec.decode("{\"schema_version\":1,\"schema_version\":1}".getBytes(StandardCharsets.UTF_8), 11, 12));
        ObjectNode extra = frame.deepCopy(); extra.put("extra", 0);
        assertThrows(IllegalArgumentException.class, () -> SourceNextFrameCodec.decode(extra, 11, 12));
        ObjectNode partial = frame.deepCopy(); partial.remove("source_derived_next_calendar_day_u8");
        assertThrows(IllegalArgumentException.class, () -> SourceNextFrameCodec.decode(partial, 11, 12));
    }

    @Test void fullNativeIdentityUsesUnsigned32AndStrictIntegerTokens() throws IOException {
        ObjectNode frame = golden().path("projections").get(0).path("input").get("source_derived_next_daily_supply_frame_inputs_v1").deepCopy();
        frame.put("subject_army_id_u32", 0xffff_ffffL);
        assertEquals(0xffff_ffffL, SourceNextFrameCodec.decode(frame, -1, 12).subjectArmyIdU32());
        assertThrows(IllegalArgumentException.class, () -> SourceNextFrameCodec.decode(frame, 11, 12));
        frame.put("current_date_storage_raw64", 1.0);
        assertThrows(IllegalArgumentException.class, () -> SourceNextFrameCodec.decode(frame, -1, 12));
    }

    @Test void losslessGzipKeepsEveryProducerByteAndBothFiniteBudgets() throws IOException, NoSuchAlgorithmException {
        byte[] raw = goldenRaw();
        assertEquals(124_091, raw.length);
        assertEquals("f631c96cdf6b1a4d218de88327ef6f6c931989aab2f0a2f996be077a92ef7c92",
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
        assertArrayEquals(raw, CaptureUpdaterGolden.decompressGolden(CaptureUpdaterGolden.compressGolden(raw)));
        assertThrows(IOException.class, () -> CaptureUpdaterGolden.compressGolden(new byte[131_073]));
        assertThrows(IOException.class, () -> CaptureUpdaterGolden.decompressGolden(new byte[16_385]));
        assertThrows(IOException.class, () -> CaptureUpdaterGolden.decompressGolden(new byte[]{0, 1, 2}));
        assertThrows(IOException.class, () -> CaptureUpdaterGolden.compressGolden(new byte[]{(byte) 0xc3, 0x28}));
    }

    private static byte[] goldenRaw() throws IOException {
        try (var input = UpdaterWriteProjectionTest.class.getResourceAsStream("/updaterwrites/source-next-updater-golden-v1.json.gz")) {
            if (input == null) throw new IOException("tracked original producer golden required; no skipped or Python fallback tests");
            return CaptureUpdaterGolden.decompressGolden(input.readNBytes(CaptureUpdaterGolden.MAX_GZIP_BYTES + 1));
        }
    }

    private static JsonNode golden() throws IOException { return JSON.readTree(goldenRaw()); }
}
