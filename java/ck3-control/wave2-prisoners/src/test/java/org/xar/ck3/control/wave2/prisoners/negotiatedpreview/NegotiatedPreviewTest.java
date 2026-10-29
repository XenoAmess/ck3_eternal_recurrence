package org.xar.ck3.control.wave2.prisoners.negotiatedpreview;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedPreview12003.Available;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedPreview12003.NotEvaluatedUnsendable;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.FrameBinding;

class NegotiatedPreviewTest {
    @Test void unchangedOriginalNormalizerGoldenAndRoundTrips() throws IOException, NoSuchAlgorithmException {
        JsonNode golden = golden();
        assertEquals("xar.java.negotiated-preview-original-producer-golden.v1", golden.path("schema").textValue());
        assertNotNull(golden.get("machine_id"));
        assertNotNull(golden.get("observed_at_utc"));
        int accepted = 0;
        int rejected = 0;
        for (JsonNode item : golden.path("cases")) {
            String id = item.path("id").textValue();
            byte[] raw = input(golden, item).getBytes(StandardCharsets.UTF_8);
            if (item.path("rejected").asBoolean()) {
                assertThrows(IllegalArgumentException.class, () -> decode(raw, item.path("frame")), id);
                rejected++;
            } else {
                NegotiatedPreview12003 actual = decode(raw, item.path("frame"));
                byte[] encoded = NegotiatedPreviewCodec.encode(actual);
                assertEquals(item.get("expected_canonical_sha256").textValue(),
                        HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(encoded)), id);
                assertEquals(StrictJson.parse(raw), StrictJson.parse(encoded), id);
                assertEquals(actual, decode(encoded, item.path("frame")), id);
                accepted++;
            }
        }
        assertEquals(9, accepted);
        assertEquals(34, rejected);
    }

    @Test void originalAuthoredOptionsMapToExactNativeBits() throws IOException {
        for (JsonNode item : golden().path("option_mask_cases")) {
            byte[] keys = StrictJson.canonical(item.get("keys"));
            if (item.path("rejected").asBoolean()) {
                assertThrows(IllegalArgumentException.class, () -> NegotiatedPreviewCodec.decodeRequestedOptions(keys));
            } else {
                assertEquals(item.get("expected_mask").intValue(), NegotiatedPreview12003.releaseOptionMask(
                        NegotiatedPreviewCodec.decodeRequestedOptions(keys)));
            }
        }
    }

    @Test void unknownAnswerRemainsUnevaluatedAndRawFloatTokensRemainFloats() throws IOException {
        JsonNode golden = golden();
        JsonNode item = golden.path("cases").get(2);
        byte[] raw = input(golden, item).getBytes(StandardCharsets.UTF_8);
        Available available = assertInstanceOf(Available.class, decode(raw, item.path("frame")));
        assertInstanceOf(NotEvaluatedUnsendable.class, available.acceptance());
        String input = input(golden, golden.path("cases").get(0));
        String floatMask = input.replace("\"requested_option_mask_bits\":8", "\"requested_option_mask_bits\":8.0");
        assertThrows(IllegalArgumentException.class,
                () -> decode(floatMask.getBytes(StandardCharsets.UTF_8), item.path("frame")));
        String duplicate = input.replace("\"can_send\":true", "\"can_send\":true,\"can_send\":false");
        assertThrows(IllegalArgumentException.class,
                () -> decode(duplicate.getBytes(StandardCharsets.UTF_8), item.path("frame")));
        assertThrows(IllegalArgumentException.class,
                () -> decode((input + "{}").getBytes(StandardCharsets.UTF_8), item.path("frame")));
    }

    private static NegotiatedPreview12003 decode(byte[] raw, JsonNode frame) {
        FrameBinding binding = new FrameBinding(StrictJson.integer(frame.get("native_revision"),
                java.math.BigInteger.ONE, StrictJson.UINT64_MAX),
                (int) StrictJson.integer(frame.get("date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE),
                StrictJson.integer(frame.get("player_character_id"), 1, 0xffff_ffffL),
                StrictJson.integer(frame.get("prisoner_character_id"), 1, 0xffff_ffffL));
        return NegotiatedPreviewCodec.decode(raw, binding,
                (int) StrictJson.integer(frame.get("requested_option_mask_bits"), 1, NegotiatedPreview12003.MAXIMUM_MASK));
    }

    private static String input(JsonNode golden, JsonNode item) {
        String base = golden.path("base_preview_json").textValue();
        JsonNode patch = item.path("input_patch");
        int prefix = patch.path("prefix_chars").intValue();
        int remove = patch.path("replace_chars").intValue();
        return base.substring(0, prefix) + patch.path("replacement").textValue() + base.substring(prefix + remove);
    }

    private static JsonNode golden() throws IOException {
        try (var stream = NegotiatedPreviewTest.class.getResourceAsStream("/negotiatedpreview/original-producer-golden.json")) {
            assertNotNull(stream, "original producer capture must be committed; missing capture is a failure");
            return StrictJson.parse(stream.readAllBytes(), 98_304);
        }
    }
}
