package org.xar.ck3.control.wave2.governance.succession;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
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

/** Mechanical test export from actual unchanged registered-App output, never a synthetic replacement oracle. */
public final class ExportM3ResidentFixtures {
    private static final ObjectMapper JSON = JsonMapper.builder(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS, DeserializationFeature.USE_BIG_INTEGER_FOR_INTS,
                    DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS).build();
    private ExportM3ResidentFixtures() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("actual-golden existing-owned-output expected-sha256 required");
        Path original = Path.of(args[0]).toRealPath(); Path output = Path.of(args[1]).toRealPath();
        if (!Files.isDirectory(output) || !Files.isRegularFile(original) || Files.size(original) > 2_097_152
                || !args[2].matches("[0-9a-f]{64}")) throw new IllegalArgumentException("bounded actual capture and existing output required");
        byte[] raw = Files.readAllBytes(original); if (!sha(raw).equals(args[2])) throw new IllegalArgumentException("original registered-App capture changed");
        JsonNode golden = JSON.readTree(raw);
        if (!"xar.g2.m3.original-resident-ui-golden/v1".equals(golden.path("schema").textValue())
                || !golden.path("source_refs_unchanged").booleanValue() || !golden.path("synthetic_fixture").booleanValue()
                || golden.path("cases").size() < 3 || golden.path("rejected").size() != 6
                || golden.path("original_suite").path("tests").intValue() != 12) throw new IllegalArgumentException("complete actual registered-App suite required");
        for (String key : List.of("failures", "errors", "skipped")) if (golden.path("original_suite").path(key).intValue() != 0) throw new IllegalArgumentException("original suite did not pass completely");
        ExactRef originalRef = new ExactRef(original.toString(), raw.length, sha(raw));
        G2Source source = new G2Source(golden.path("machine_id").textValue(), golden.path("observed_at_utc").textValue(), "offline-registered-app-fixture", originalRef);
        ObjectNode all = JSON.createObjectNode(); all.put("schema", "xar.g2.m3.resident-http-fixtures/v1");
        ArrayNode positives = all.putArray("cases"), negatives = all.putArray("rejected");
        for (JsonNode row : golden.path("cases")) {
            ObjectNode entry = positives.addObject(); entry.put("name", row.path("name").textValue());
            entry.set("request", JSON.readTree(envelope(source, "m3-resident-" + row.path("name").textValue(), row.get("request")))); entry.set("expected", row.get("expected"));
        }
        for (JsonNode row : golden.path("rejected")) {
            ObjectNode entry = negatives.addObject(); entry.put("name", row.path("name").textValue());
            entry.set("request", JSON.readTree(envelope(source, "m3-resident-reject-" + row.path("name").textValue(), row.get("request")))); entry.put("original_error_type", row.path("error_type").textValue());
        }
        byte[] request = JSON.writeValueAsBytes(positives.get(0).get("request"));
        byte[] expected = JSON.writeValueAsBytes(positives.get(0).get("expected"));
        byte[] negative = JSON.writeValueAsBytes(negatives.get(0).get("request"));
        byte[] complete = JSON.writeValueAsBytes(all);
        ObjectNode pins = JSON.createObjectNode(); pins.put("schema", "xar.g2.m3.resident-http-pins/v1");
        pins.put("machine_id", source.machineId()).put("observed_at_utc", source.observedAtUtc()).put("synthetic_fixture", true);
        pins.set("original_golden", originalRef.toJson()); pins.put("actual_source_ref_count", golden.path("source_refs").size());
        pins.put("scope", "Original registered-App/Queue software output export; no HTTP or native/gameplay completion inferred");
        List<String> names = List.of("M3.resident.request.json", "M3.resident.expected-result.json", "M3.resident.rejected-request.json", "M3.resident.requests.json");
        List<byte[]> bodies = List.of(request, expected, negative, complete);
        ObjectNode refs = pins.putObject("outputs"); int total = 0;
        for (int i=0;i<names.size();i++) { total = Math.addExact(total, bodies.get(i).length); refs.set(names.get(i), new ExactRef(names.get(i), bodies.get(i).length, sha(bodies.get(i))).toJson()); }
        byte[] pinBytes = JSON.writeValueAsBytes(pins); total = Math.addExact(total, pinBytes.length);
        if (total > 524_288) throw new IllegalArgumentException("resident fixture export exceeds512KiB output estimate");
        for (String name : names) if (Files.exists(output.resolve(name))) throw new IllegalArgumentException("create-new export already exists");
        if (Files.exists(output.resolve("M3.resident.source-pins.json"))) throw new IllegalArgumentException("create-new pins already exist");
        for (int i=0;i<names.size();i++) Files.write(output.resolve(names.get(i)), bodies.get(i), StandardOpenOption.CREATE_NEW);
        Files.write(output.resolve("M3.resident.source-pins.json"), pinBytes, StandardOpenOption.CREATE_NEW);
        System.out.println("M3 original registered-App fixtures exported bytes=" + total);
    }
    private static byte[] envelope(G2Source source, String id, JsonNode payload) throws Exception {
        return G2Wire.encodeRequest(new G2Request(id, Milestone.M3, source, ProjectionJson.object(JSON.writeValueAsBytes(payload), ProjectionJson.MAX_BYTES)));
    }
    private static String sha(byte[] raw) throws Exception { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
}
