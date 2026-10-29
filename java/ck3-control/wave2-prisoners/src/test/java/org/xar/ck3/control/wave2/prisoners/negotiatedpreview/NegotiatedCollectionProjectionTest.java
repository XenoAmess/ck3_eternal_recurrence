package org.xar.ck3.control.wave2.prisoners.negotiatedpreview;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedCollectionProjection12004.QueryBinding;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleaseCollectionProjection12003.SupportedBuild;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.FrameBinding;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.ReleaseOption;

class NegotiatedCollectionProjectionTest {
    private static final QueryBinding QUERY = new QueryBinding(new FrameBinding(BigInteger.valueOf(1014), 53286360, 29829, 61540),
            "native:1014", BigInteger.valueOf(1014), List.of(ReleaseOption.GAIN_HOOK));

    @Test void actualOriginalTransportToCommonCollectionAndNegotiatedConsumer() throws IOException {
        JsonNode capture = capture();
        assertTrue(capture.path("original_transport_executed").booleanValue());
        assertEquals(0, capture.path("native_calls").intValue());
        String raw = capture.path("normalized_response_json").textValue();
        var actual = decode(raw);
        JsonNode original = StrictJson.parse(raw.getBytes(StandardCharsets.UTF_8), 131_072);
        assertEquals(1, actual.collection().rows().size());
        assertEquals(0, actual.collection().selectedOrdinal());
        assertEquals(61540, actual.collection().rows().getFirst().prisonerCharacterId());
        assertTrue(actual.source().isPresent());
        assertEquals(original.get("prisoner_negotiated_quote_result_12004"),
                StrictJson.parse(NegotiatedQuoteResult12004.encode(actual.quoteResult().orElseThrow())));
        assertTrue(actual.collection().originalSha256().matches("[0-9a-f]{64}"));
        // SDK root extensions are allowed; strictness belongs to the declared leaf.
        decode(raw.substring(0, raw.length() - 1) + ",\"future_sdk_extension\":{\"retained\":true}}");
    }

    @Test void requestProofOrdinalAndExistingResultCannotDrift() throws IOException {
        String raw = capture().path("normalized_response_json").textValue();
        assertThrows(IllegalArgumentException.class,
                () -> decode(raw.replace("\"queried_release_option_mask_bits\":8", "\"queried_release_option_mask_bits\":8.0")));
        assertThrows(IllegalArgumentException.class,
                () -> decode(raw.replace("\"queried_release_option_keys\":[\"gain_hook\"]", "\"queried_release_option_keys\":[\"banish\"]")));
        assertThrows(IllegalArgumentException.class,
                () -> decode(raw.replace("\"proof_epoch\":721", "\"proof_epoch\":722")));
        assertThrows(IllegalArgumentException.class,
                () -> decode(raw.replace("\"material_result\":false", "\"material_result\":true")));
        assertThrows(IllegalArgumentException.class,
                () -> decode(raw.replace("\"kind\":\"native_answer\"", "\"kind\":\"not_evaluated_unsendable\"")));
        assertThrows(IllegalArgumentException.class,
                () -> decode(raw.replace("\"queried_snapshot_id\":\"native:1014\"", "\"queried_snapshot_id\":\"native:1015\"")));
    }

    private static NegotiatedCollectionProjection12004.Observation decode(String raw) {
        return NegotiatedCollectionProjection12004.decodeNormalizedResponse(raw.getBytes(StandardCharsets.UTF_8), SupportedBuild.CK3_12004, QUERY);
    }
    private static JsonNode capture() throws IOException {
        try (var input = NegotiatedCollectionProjectionTest.class.getResourceAsStream("/negotiatedpreview/original-producer-golden.json")) {
            assertNotNull(input, "unchanged original collection transport capture required");
            return StrictJson.parse(input.readAllBytes(), 98_304).get("collection_capture");
        }
    }
}
