package org.xar.ck3.control.wave2.governance.succession;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;

/** Test-only mechanical export from the unique actual original producer artifact. No process or domain policy. */
public final class ExportM3HttpFixtures {
    private static final ObjectMapper JSON = JsonMapper.builder(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS,
                    DeserializationFeature.USE_BIG_INTEGER_FOR_INTS,
                    DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .disable(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES).build();
    private ExportM3HttpFixtures() { }

    public static void main(String[] args) throws Exception {
        if (args.length != 3) { throw new IllegalArgumentException("actual-golden existing-output-directory expected-golden-sha256 required"); }
        Path original = Path.of(args[0]).toRealPath();
        Path output = Path.of(args[1]).toRealPath();
        if (!Files.isRegularFile(original) || !Files.isDirectory(output)
                || !args[2].matches("[0-9a-f]{64}") || Files.size(original) > 2_097_152) {
            throw new IllegalArgumentException("bounded actual golden and existing owned output required");
        }
        byte[] raw = Files.readAllBytes(original);
        String digest = sha256(raw);
        if (!digest.equals(args[2])) { throw new IllegalArgumentException("actual original golden source changed"); }
        JsonNode golden = JSON.readTree(raw);
        if (!golden.path("schema").asText().equals("xar.g2.m3.original-producer-golden/v1")
                || !golden.path("synthetic_fixture").asBoolean()
                || !golden.path("source_refs_unchanged").asBoolean()
                || !golden.path("producer_cases").isArray() || golden.path("producer_cases").isEmpty()
                || !golden.path("producer_rejected").isArray() || golden.path("producer_rejected").isEmpty()) {
            throw new IllegalArgumentException("actual synthetic original producer cases with complete source checks required");
        }
        ExactRef originalRef = new ExactRef(original.toString(), raw.length, digest);
        G2Source source = new G2Source(golden.path("machine_id").textValue(),
                golden.path("observed_at_utc").textValue(), "offline-original-producer-fixture", originalRef);
        JsonNode positive = golden.path("producer_cases").get(0);
        JsonNode negative = golden.path("producer_rejected").get(0);
        byte[] request = envelope(source, "m3-host-positive", positive.get("request"));
        byte[] expected = JSON.writeValueAsBytes(positive.get("expected"));
        byte[] rejected = envelope(source, "m3-host-negative", negative.get("request"));
        ObjectNode pins = JSON.createObjectNode();
        pins.put("schema", "xar.g2.m3.http-fixture-pins/v1");
        pins.put("machine_id", source.machineId());
        pins.put("observed_at_utc", source.observedAtUtc());
        pins.put("synthetic_fixture", true);
        pins.set("original_golden", originalRef.toJson());
        pins.put("actual_source_ref_count", golden.path("source_refs").size());
        pins.put("positive_case", positive.path("name").textValue());
        pins.put("rejected_case", negative.path("name").textValue());
        pins.put("original_error_type", negative.path("error_type").textValue());
        pins.put("original_error_message", negative.path("error_message").textValue());
        pins.put("scope", "Actual original Python producer output only; synthetic offline inputs; no Game/build qualification or business credit");
        ObjectNode outputs = pins.putObject("outputs");
        outputs.set("M3.request.json", new ExactRef("M3.request.json", request.length, sha256(request)).toJson());
        outputs.set("M3.expected-result.json", new ExactRef("M3.expected-result.json", expected.length, sha256(expected)).toJson());
        outputs.set("M3.rejected-request.json", new ExactRef("M3.rejected-request.json", rejected.length, sha256(rejected)).toJson());
        byte[] pinBytes = JSON.writeValueAsBytes(pins);
        List<String> names = List.of("M3.request.json", "M3.expected-result.json", "M3.rejected-request.json", "M3.source-pins.json");
        List<byte[]> bodies = List.of(request, expected, rejected, pinBytes);
        int total = 0;
        for (int i = 0; i < names.size(); i++) {
            if (Files.exists(output.resolve(names.get(i)))) { throw new IllegalArgumentException("fixture output already exists"); }
            total = Math.addExact(total, bodies.get(i).length);
        }
        if (total > 49_152) { throw new IllegalArgumentException("host fixture export exceeds admitted48KiB output"); }
        for (int i = 0; i < names.size(); i++) {
            Files.write(output.resolve(names.get(i)), bodies.get(i), StandardOpenOption.CREATE_NEW);
        }
        System.out.println("M3 actual original HTTP fixtures exported bytes=" + total + " golden_sha256=" + digest);
    }

    private static byte[] envelope(G2Source source, String requestId, JsonNode payload) throws Exception {
        if (payload == null || !payload.isObject()) { throw new IllegalArgumentException("actual original request must be an object"); }
        return G2Wire.encodeRequest(new G2Request(requestId, Milestone.M3, source,
                ProjectionJson.object(JSON.writeValueAsBytes(payload), ProjectionJson.MAX_BYTES)));
    }
    private static String sha256(byte[] value) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value));
    }
}
