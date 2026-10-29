package org.xar.ck3.control.wave2.prisoners.ransomquote;

import org.xar.ck3.control.contracts.StrictJson;

/** Diagnostic-only ordinary ransom mask. Does not expose the ninth option as an action. */
public record RansomOptionMask12004(int requestedOptionIndex, int observedOptionMaskBits) {
    public static final int AUTHORED_OPTION_COUNT = 9;
    public static final int MAXIMUM_MASK = (1 << AUTHORED_OPTION_COUNT) - 1;
    public static final String EXACT_BUILD = "1.20.0.4";
    public static final String STOCK_SHA256 = "1bb43b3c2061212af8d41b11314ff4e569af2a3506319f820d05877a7762abc5";
    public static final String NATIVE_PRODUCER_SHA256 = "5d166454db5104e9e6a94db704a4adab9279e1320b7bb8d9c1a5071f83c64764";

    public RansomOptionMask12004 {
        StrictJson.require(requestedOptionIndex >= 0 && requestedOptionIndex <= 3
                && observedOptionMaskBits >= 1 && observedOptionMaskBits <= MAXIMUM_MASK
                && observedOptionMaskBits != (1 << requestedOptionIndex),
                "different current nine-option native diagnostic mask required");
    }

    /** Bind parsed stock send_option count to the exact .4 native kOptionCount source contract. */
    public static void requireAuthoredOptionCount(int observedCount) {
        StrictJson.require(observedCount == AUTHORED_OPTION_COUNT, "ordinary ransom authored option count drift");
    }
}
