package org.xar.ck3.control.g2.m0;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.DecimalNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.math.BigDecimal;
import java.util.List;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.contracts.StrictJson;

/** Full actual-corpus differential; no fixture generation and no skipped missing resources. */
public final class M0ProducerDifferential {
    public record Counts(int originalTests, int rankingCases, int immediateReturned, int immediateRejected,
                         int terminalProducerCasesCaptured, int additionalNumericRefusals) { }
    private M0ProducerDifferential() { }

    public static void main(String[] args) throws IOException {
        if (args.length != 1) { throw new IllegalArgumentException("actual immutable producer gzip required"); }
        Counts counts;
        try (InputStream input = Files.newInputStream(Path.of(args[0]))) { counts = verify(input); }
        System.out.println("M0_PRODUCER_DIFFERENTIAL_PASS " + counts);
    }

    public static Counts verify(InputStream compressed) throws IOException {
        if (compressed == null) { throw new IOException("actual original M0 producer resource is mandatory"); }
        byte[] raw;
        try (GZIPInputStream gzip = new GZIPInputStream(compressed)) {
            raw = gzip.readNBytes(8 * 1024 * 1024 + 1);
            check(raw.length <= 8 * 1024 * 1024, "bounded original producer corpus required");
        }
        // The full corpus is a test artifact with an explicit8MiB budget; each service request retains65,536 bytes.
        JsonNode golden = new ObjectMapper().enable(com.fasterxml.jackson.databind.DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).readTree(raw);
        check(golden.path("schema").asText().equals("xar.g2.m0.original-producer-golden/v1"), "actual corpus schema drifted");
        check(golden.path("original_tests").isIntegralNumber() && golden.path("original_tests").intValue() == 90,
                "complete original90-test cohort required");
        check(golden.path("skipped").isIntegralNumber() && golden.path("skipped").intValue() == 0, "original skipped tests refused");
        check(golden.path("expected_failures").isIntegralNumber() && golden.path("expected_failures").intValue() == 0
                && golden.path("unexpected_successes").isIntegralNumber() && golden.path("unexpected_successes").intValue() == 0,
                "original expected failures and unexpected successes refused");
        check(golden.path("source_refs").isArray() && !golden.path("source_refs").isEmpty(), "actual producer source inventory required");
        int rankings = 0; ObjectNode baseline = null;
        for (JsonNode row : golden.path("cases")) {
            ObjectNode request = StrictJson.object(row.get("request"), Set.of("immediate_certificate", "normalized_power", "model", "terminal_control"));
            byte[] requestRaw = StrictJson.canonical(request);
            JsonNode actual = StrictJson.parse(RaiktorRecommendationInputCodec.execute(requestRaw));
            check(actual.equals(row.get("expected")), "ranking differs from actual original producer: " + row.path("id").asText());
            check(actual.equals(StrictJson.parse(StrictJson.canonical(actual))), "ranking serialization roundtrip changed content");
            if (baseline == null) { baseline = request.deepCopy(); }
            rankings++;
        }
        check(rankings > 0 && baseline != null, "actual original ranking cases required");
        int returned = 0; int rejected = 0; int opaqueMatched = 0;
        for (JsonNode row : golden.path("immediate_cases")) {
            JsonNode args = row.get("request"); check(args != null && args.isArray() && args.size() == 4, "original immediate four arguments required");
            ObjectNode request = StrictJson.object();
            String[] names = {"white_peace_projection", "surrender_session", "budget_provider", "model_provider"};
            for (int index = 0; index < names.length; index++) { request.set(names[index], args.get(index)); }
            boolean expectRejection = row.path("expected").path("status").asText().equals("rejected");
            try {
                JsonNode actual = RaiktorExitObservationCodec.parseWire(RaiktorImmediateInputCodec.execute(RaiktorExitObservationCodec.encodeWire(request)));
                check(!expectRejection, "Java accepted original rejected immediate case: " + row.path("id").asText());
                check(actual.equals(row.path("expected").get("value")), "immediate result differs from actual original: " + row.path("id").asText());
                JsonNode probe = args.get(0).get("retained_hash_probe");
                if (probe != null) {
                    JsonNode numeric = probe.get("numeric_forms");
                    check(numeric != null && numeric.isArray() && numeric.size() == 3
                            && numeric.get(0).isIntegralNumber() && numeric.get(0).bigIntegerValue().intValueExact() == 1
                            && numeric.get(1).isFloatingPointNumber() && numeric.get(1).doubleValue() == 1.0
                            && numeric.get(2).isFloatingPointNumber()
                            && Double.doubleToRawLongBits(numeric.get(2).doubleValue()) == Long.MIN_VALUE
                            && probe.has(new String(Character.toChars(0x10000))) && probe.has("\ue000"),
                            "actual opaque hash witness must retain numeric token types, negative zero and codepoint keys");
                    opaqueMatched++;
                }
                returned++;
            } catch (IllegalArgumentException expectedDomainRefusal) {
                check(expectRejection, "Java rejected original returned immediate case: " + row.path("id").asText()
                        + ": " + expectedDomainRefusal.getMessage());
                rejected++;
            }
        }
        check(returned > 0 && rejected > 0, "real immediate accepted and rejected producer paths required");
        check(opaqueMatched == 1, "the source-bound original opaque hash glue witness is mandatory");
        int terminalMatched = 0;
        for (JsonNode row : golden.path("terminal_cases")) {
            boolean refused = row.path("expected").path("status").asText().equals("rejected");
            try {
                JsonNode actual = RaiktorExitObservationCodec.parseWire(RaiktorTerminalInputProjection.execute(RaiktorExitObservationCodec.encodeWire(row.get("request"))));
                check(!refused && actual.equals(row.path("expected").get("value")),
                        "actual terminal-input producer differs: " + row.path("id").asText());
            } catch (IllegalArgumentException actualRefusal) {
                check(refused, "Java refused original returned terminal input: " + row.path("id").asText() + ": " + actualRefusal.getMessage());
            }
            terminalMatched++;
        }
        check(terminalMatched > 0, "actual formal terminal-input producer must be executed and compared");
        int extra = 0;
        for (List<String> path : List.of(List.of("terminal_control", "schema_version"),
                List.of("terminal_control", "player_relative_war_score"), List.of("immediate_certificate", "frame", "snapshot_revision"),
                List.of("normalized_power", "power", "actual_power_ratio_raw"),
                List.of("model", "tail_risk_policy", "parameters_raw", "long_war_scale_start_days"))) {
            JsonNode originalValue = baseline;
            for (String part : path) { originalValue = originalValue.get(part); }
            check(originalValue.isIntegralNumber(), "original actual wrong-token baseline must be an integer");
            JsonNode equalFloat = DecimalNode.valueOf(new BigDecimal(originalValue.bigIntegerValue()).setScale(1));
            for (JsonNode token : List.of(new ObjectMapper().getNodeFactory().booleanNode(true), equalFloat)) {
                ObjectNode wrong = baseline.deepCopy(); ObjectNode container = wrong;
                for (int i = 0; i < path.size() - 1; i++) { container = (ObjectNode) container.get(path.get(i)); }
                container.set(path.getLast(), token);
                if (path.equals(List.of("immediate_certificate", "frame", "snapshot_revision"))) {
                    // Keep all cross-frame comparisons equal so refusal must retain numeric-token distinctions.
                    ((ObjectNode) wrong.path("terminal_control").get("frame")).set("snapshot_revision", token);
                    ((ObjectNode) wrong.path("normalized_power").get("frame")).set("snapshot_revision", token);
                }
                try {
                    RaiktorRecommendationInputCodec.execute(new ObjectMapper().writeValueAsBytes(wrong));
                    throw new AssertionError("wrong integer token accepted: " + path);
                } catch (RaiktorRecommendationInputCodec.InputRejected expected) { extra++; }
            }
        }
        ObjectNode revisionOne = baseline.deepCopy();
        for (JsonNode frame : List.of(revisionOne.path("immediate_certificate").get("frame"),
                revisionOne.path("terminal_control").get("frame"), revisionOne.path("normalized_power").get("frame"))) {
            ((ObjectNode) frame).put("snapshot_revision", 1);
        }
        JsonNode revisionOneResult = StrictJson.parse(RaiktorRecommendationInputCodec.execute(StrictJson.canonical(revisionOne)));
        check(revisionOneResult.equals(StrictJson.parse(RaiktorRecommendationInputCodec.execute(StrictJson.canonical(baseline)))),
                "a valid different public revision must preserve this frame-independent decision");
        for (JsonNode frame : List.of(revisionOne.path("immediate_certificate").get("frame"),
                revisionOne.path("terminal_control").get("frame"), revisionOne.path("normalized_power").get("frame"))) {
            ((ObjectNode) frame).put("snapshot_revision", true);
        }
        try {
            RaiktorRecommendationInputCodec.execute(new ObjectMapper().writeValueAsBytes(revisionOne));
            throw new AssertionError("boolean true impersonated valid integer revision1");
        } catch (RaiktorRecommendationInputCodec.InputRejected expected) { extra++; }
        ObjectNode crossed = baseline.deepCopy();
        ObjectNode terminalFrame = (ObjectNode) crossed.path("terminal_control").get("frame");
        terminalFrame.put("date_raw", terminalFrame.path("date_raw").intValue() + 24);
        try {
            RaiktorRecommendationInputCodec.execute(StrictJson.canonical(crossed));
            throw new AssertionError("crossed paused frame accepted");
        } catch (RaiktorRecommendationInputCodec.InputRejected expected) { extra++; }
        // This corpus explicitly keeps public and native revision domains separate in real original fixtures.
        boolean unequal = false;
        for (JsonNode row : golden.path("cases")) {
            JsonNode f = row.path("request").path("immediate_certificate").path("frame");
            unequal |= !f.path("snapshot_revision").equals(f.path("native_revision"));
        }
        check(unequal, "at least one original public-revision!=native-revision frame required");
        return new Counts(90, rankings, returned, rejected, terminalMatched, extra);
    }
    private static void check(boolean condition, String message) { if (!condition) { throw new AssertionError(message); } }
}
