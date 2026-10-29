package org.xar.ck3.control.wave2.prisoners.negotiatedpreview;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedQuoteResult12004.Available;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedQuoteResult12004.Match;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedSourceCopy12004.QuoteBinding;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.FrameBinding;

class NegotiatedQuoteResultTest {
    private static final FrameBinding FRAME = new FrameBinding(BigInteger.valueOf(1014), 53286360, 29829, 61540);
    private static final QuoteBinding BINDING = new QuoteBinding(FRAME, BigInteger.valueOf(23), BigInteger.valueOf(721), 2, 8);

    @Test void actualOriginalSourceNormalizerToResultConsumerGolden() throws IOException {
        JsonNode golden = golden();
        int accepted = 0;
        int rejected = 0;
        for (JsonNode item : golden.path("quote_result_cases")) {
            String id = item.path("id").textValue();
            if (item.path("rejected").asBoolean()) {
                assertThrows(IllegalArgumentException.class, () -> consume(golden, item), id);
                rejected++;
            } else {
                var result = consume(golden, item);
                assertEquals(item.get("expected"), StrictJson.parse(NegotiatedQuoteResult12004.encode(result)), id);
                assertFalse(NegotiatedQuoteResult12004.toJson(result).path("material_result").booleanValue(), id);
                assertFalse(NegotiatedQuoteResult12004.toJson(result).path("action_selected").booleanValue(), id);
                accepted++;
            }
        }
        assertEquals(12, accepted);
        assertEquals(18, rejected);
    }

    @Test void nullComparisonsAreUnknownAndDisagreementNeverOverwritesNativeOperands() throws IOException {
        JsonNode golden = golden();
        Available mismatch = assertInstanceOf(Available.class, consume(golden, golden.path("quote_result_cases").get(2)));
        assertEquals(Match.DIFFERENT, mismatch.comparisons().getFirst().nativeScoreMatchesQuote());
        assertEquals(5000001L, assertInstanceOf(NegotiatedPreview12003.NativeAnswer.class,
                mismatch.nativeResult().acceptance()).recipientAcceptanceScoreRaw());
        Available partial = assertInstanceOf(Available.class, consume(golden, golden.path("quote_result_cases").get(4)));
        assertEquals(Match.UNKNOWN, partial.comparisons().getFirst().scoreProjectionMatchesNativeCopy());
        assertEquals(Match.MATCH, partial.comparisons().getFirst().nativeScoreMatchesQuote());
        Available absent = assertInstanceOf(Available.class, consume(golden, golden.path("quote_result_cases").get(1)));
        assertTrue(absent.source().isEmpty());
        assertTrue(absent.comparisons().isEmpty());
    }

    @Test void originalSignedWrapAndNativeRoundingIsExactAtBothInt64Ends() throws IOException {
        for (JsonNode item : golden().path("native_round_cases")) {
            assertEquals(item.get("expected").longValue(), NegotiatedSourceCodec12004.roundNative(item.get("raw").longValue()));
        }
    }

    @Test void copiedSourceCannotBeJoinedToAnotherQueryAndIntegerTokensRemainStrict() throws IOException {
        JsonNode golden = golden();
        byte[] rawSource = golden.path("source_base_json").textValue().getBytes(StandardCharsets.UTF_8);
        var source = NegotiatedSourceCodec12004.decode(rawSource, BINDING);
        var preview = NegotiatedPreviewCodec.decode(golden.path("base_preview_json").textValue().getBytes(StandardCharsets.UTF_8), FRAME, 8);
        QuoteBinding other = new QuoteBinding(FRAME, BigInteger.valueOf(24), BigInteger.valueOf(721), 2, 8);
        assertThrows(IllegalArgumentException.class,
                () -> NegotiatedQuoteResult12004.consume(preview, Optional.of(source), other));
        String text = golden.path("source_base_json").textValue();
        String floatIndex = text.replace("\"lane_index\":0", "\"lane_index\":0.0");
        assertThrows(IllegalArgumentException.class,
                () -> NegotiatedSourceCodec12004.decode(floatIndex.getBytes(StandardCharsets.UTF_8), BINDING));
        String boolVersion = text.replace("\"schema_version\":1", "\"schema_version\":true");
        assertThrows(IllegalArgumentException.class,
                () -> NegotiatedSourceCodec12004.decode(boolVersion.getBytes(StandardCharsets.UTF_8), BINDING));
    }

    private static NegotiatedQuoteResult12004 consume(JsonNode golden, JsonNode item) {
        String previewText = item.has("preview_json") ? item.get("preview_json").textValue() : golden.path("base_preview_json").textValue();
        var preview = NegotiatedPreviewCodec.decode(previewText.getBytes(StandardCharsets.UTF_8), FRAME, 8);
        Optional<NegotiatedSourceCopy12004> source = Optional.empty();
        if (item.path("source_present").booleanValue()) {
            String base = golden.path("source_base_json").textValue();
            JsonNode patch = item.path("source_patch");
            int prefix = patch.path("prefix_chars").intValue();
            int remove = patch.path("replace_chars").intValue();
            String text = base.substring(0, prefix) + patch.path("replacement").textValue() + base.substring(prefix + remove);
            source = Optional.of(NegotiatedSourceCodec12004.decode(text.getBytes(StandardCharsets.UTF_8), BINDING));
        }
        return NegotiatedQuoteResult12004.consume(preview, source, BINDING);
    }

    private static JsonNode golden() throws IOException {
        try (var stream = NegotiatedQuoteResultTest.class.getResourceAsStream("/negotiatedpreview/original-producer-golden.json")) {
            assertNotNull(stream, "original source/result producer capture is required");
            return StrictJson.parse(stream.readAllBytes(), 98_304);
        }
    }
}
