package org.xar.ck3.control.g2.m6.prisonerransom;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.prisoners.ransomquote.RansomOptionMask12004;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.FrameBinding;

final class RansomOptionMask12004Test {
    private static final FrameBinding FRAME = new FrameBinding(BigInteger.ONE, 1, 1, 2);
    private static final String PREFIX = "{\"private_build\":true,\"read_only\":true,\"advertised\":false,\"action_surface_present\":false,\"status\":\"unavailable\",\"unavailable_reason\":\"option_mask_unexpected\"";

    @Test
    void soleNineBitSourceContractAndWholeQuoteCodecRejectMalformedDiagnostics() {
        assertEquals(9, RansomOptionMask12004.AUTHORED_OPTION_COUNT);
        assertEquals(511, RansomOptionMask12004.MAXIMUM_MASK);
        assertEquals(PrisonerVanillaResearch.STOCK_SHA256, RansomOptionMask12004.STOCK_SHA256);
        assertEquals(PrisonerVanillaResearch.EXACT_BUILD, RansomOptionMask12004.EXACT_BUILD);
        RansomOptionMask12004.requireAuthoredOptionCount(9);
        for (int count : List.of(0, 8, 10)) assertThrows(IllegalArgumentException.class, () -> RansomOptionMask12004.requireAuthoredOptionCount(count));
        for (int mask : List.of(256, 511)) {
            assertEquals(mask, new RansomOptionMask12004(2, mask).observedOptionMaskBits());
            var quote = decode(PREFIX + ",\"requested_option_index\":2,\"observed_option_mask_bits\":" + mask + "}");
            assertEquals(new PrisonerVanillaResearch.OptionMask(2, mask), assertInstanceOf(PrisonerVanillaResearch.UnavailableQuote.class, quote).diagnostic());
            assertEquals(quote, PrisonerVanillaResearch.decodeQuote(StrictJson.canonical(PrisonerVanillaResearch.quoteJson(quote)), FRAME, BigInteger.ONE));
        }
        for (String bad : List.of("0", "512", "-1", "true", "256.0", "null", "\"256\"", "4")) {
            assertThrows(IllegalArgumentException.class, () -> decode(PREFIX + ",\"requested_option_index\":2,\"observed_option_mask_bits\":" + bad + "}"));
        }
        assertThrows(IllegalArgumentException.class, () -> decode(PREFIX + ",\"requested_option_index\":2}"));
        assertThrows(IllegalArgumentException.class, () -> decode(PREFIX + ",\"observed_option_mask_bits\":256}"));
        assertThrows(IllegalArgumentException.class, () -> new RansomOptionMask12004(4, 256));
        assertInstanceOf(PrisonerVanillaResearch.NoQuoteDiagnostic.class,
                assertInstanceOf(PrisonerVanillaResearch.UnavailableQuote.class, decode(PREFIX + "}")).diagnostic());
        assertEquals("future_reason", assertInstanceOf(PrisonerVanillaResearch.UnavailableQuote.class,
                decode(PREFIX.replace("option_mask_unexpected", "future_reason") + "}")).reason());
    }

    private static PrisonerVanillaResearch.RansomQuote decode(String raw) {
        return PrisonerVanillaResearch.decodeQuote(raw.getBytes(StandardCharsets.UTF_8), FRAME, BigInteger.ONE);
    }
}
