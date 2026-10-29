package org.xar.ck3.control.wave2.finance.holyloan;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanModel.ExpectedFrame;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;

/** Offline shared replay boundary for the original function-capture corpus and consumer substitution pipe. */
final class HolyLoanHarness {
    private HolyLoanHarness() { }
    static byte[] evaluate(byte[] bytes) {
        JsonNode node = StrictJson.object(StrictJson.parse(bytes), Set.of("operation", "arguments"));
        JsonNode a = node.get("arguments");
        return switch (StrictJson.text(node.get("operation"))) {
            case "project" -> {
                StrictJson.object(a, Set.of("value", "expected_played_character_id", "expected_date_raw", "expected_capture_epoch"));
                ExpectedFrame frame = new ExpectedFrame((int) StrictJson.integer(a.get("expected_played_character_id"), 1, Integer.MAX_VALUE),
                        (int) StrictJson.integer(a.get("expected_date_raw"), 0, Integer.MAX_VALUE),
                        StrictJson.integer(a.get("expected_capture_epoch"), java.math.BigInteger.ONE, HolyLoanModel.UINT64_MAX));
                yield HolyLoanCodec.encode(HolyLoanCodec.project(wire(a.get("value")), frame));
            }
            case "normalize" -> {
                StrictJson.object(a, Set.of("value", "snapshot"));
                yield RawCashCodec.normalize(wire(a.get("value")), wire(a.get("snapshot"))).toJson();
            }
            case "monthly" -> {
                StrictJson.object(a, Set.of("current")); RawCashCodec.validateMonthlyFlow(wire(a.get("current"))); yield new byte[] {'n', 'u', 'l', 'l'};
            }
            case "financing" -> {
                StrictJson.object(a, Set.of("snapshot", "cash_resources", "cash_source_frame"));
                yield LoanFinancingCodec.encode(LoanFinancingCodec.decodeAndProject(wire(a)));
            }
            default -> throw new IllegalArgumentException("unknown captured operation");
        };
    }
    static byte[] wire(JsonNode node) {
        return SdkProjectionJson.encode(node);
    }
}
