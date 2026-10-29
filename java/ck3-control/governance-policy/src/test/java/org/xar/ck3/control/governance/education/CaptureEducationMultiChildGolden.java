package org.xar.ck3.control.governance.education;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

/** Capture a genuine multiple-child amplification case without retaining duplicated large expected bodies in Git. */
public final class CaptureEducationMultiChildGolden {
    private static final ObjectMapper JSON = new ObjectMapper();
    private CaptureEducationMultiChildGolden() { }
    public static void main(String[] args) throws IOException, InterruptedException, NoSuchAlgorithmException {
        if (args.length != 6 || args[5].isBlank()) { throw new IllegalArgumentException("root python scratch baseline output verified-machine-id required"); }
        Path root = Path.of(args[0]), scratch = Path.of(args[2]); Files.createDirectories(scratch);
        Path input = scratch.resolve("multi-child-input.json"), output = scratch.resolve("multi-child-actual-output.json"), summary = scratch.resolve("multi-child-summary.json");
        for (Path target : List.of(input, output, summary, scratch.resolve("multi-child.stdout.log"), scratch.resolve("multi-child.stderr.log"), Path.of(args[4]))) {
            if (Files.exists(target)) { throw new IOException("fresh capture path required: " + target); }
        }
        List<String> paths = List.of("family_generation_education_decision_v1.py", "family_generation_education_inputs_v1.py", "education_child_court_owner_readonly_12004.py", "bridge/education_point_source_modifiers_12004.py");
        Map<String, String> before = pins(root, paths);
        byte[] baselineBytes = Files.readAllBytes(Path.of(args[3]));
        ObjectNode data = (ObjectNode) JSON.readTree(baselineBytes).get("cases").get(2).get("input").deepCopy();
        ArrayNode occurrences = (ArrayNode) data.get("rows"); ObjectNode occurrence = (ObjectNode) occurrences.get(0).deepCopy();
        occurrence.put("occurrence_index", 2).put("raw_character_id", 501); occurrences.add(occurrence); data.put("native_child_count_raw", 3);
        ArrayNode children = (ArrayNode) data.get("child_inputs").get("rows"); ObjectNode child = (ObjectNode) children.get(0).deepCopy();
        child.put("character_id", 501).putArray("occurrence_indices").add(2); ((ObjectNode) child.get("court_owner_source")).put("child_character_id", 501); children.add(child);
        JSON.writeValue(input.toFile(), data);
        String script = "import hashlib,json,sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); from xar_autoplayer.family_generation_education_decision_v1 import derive_family_generation_education_decision_inputs_v1 as derive; d=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8')); b=json.dumps(derive(d),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'); Path(sys.argv[3]).write_bytes(b); Path(sys.argv[4]).write_text(json.dumps({'expected_sha256':hashlib.sha256(b).hexdigest(),'expected_bytes':len(b)},sort_keys=True),encoding='utf-8')";
        Process process = new ProcessBuilder(args[1], "-c", script, root.resolve("ck3_autonomous_player/src").toString(), input.toString(), output.toString(), summary.toString())
                .redirectOutput(scratch.resolve("multi-child.stdout.log").toFile()).redirectError(scratch.resolve("multi-child.stderr.log").toFile()).start();
        if (!process.waitFor(30, TimeUnit.SECONDS)) { process.destroyForcibly(); process.waitFor(); throw new IOException("multi-child producer timed out"); }
        if (process.exitValue() != 0) { throw new IOException("multi-child producer exit " + process.exitValue()); }
        Map<String, String> after = pins(root, paths); if (!before.equals(after)) { throw new IOException("producer changed during capture"); }
        ObjectNode result = (ObjectNode) JSON.readTree(summary.toFile()); result.set("input", data);
        result.put("schema", "xar.education.multiple-child-producer-golden/v1"); result.put("machine_id", args[5]); result.put("machine_id_source", "caller_verified_tools/ck3_live_run_id.py_machine"); result.put("captured_at_utc", Instant.now().toString());
        result.put("baseline_sha256", digest(baselineBytes)); result.put("producer_exit_code", process.exitValue()); result.put("source_before_after_unchanged", true); result.put("scope", "actual_old_pure_producer_hash_over_complete_canonical_json_no_game");
        ObjectNode sources = result.putObject("source_sha256"); after.forEach(sources::put);
        JsonNode expected = JSON.readTree(output.toFile());
        if (expected.get("education_rows").size() != 2 || Files.size(output) <= 65_536 || Files.size(output) != result.get("expected_bytes").longValue() || !digest(Files.readAllBytes(output)).equals(result.get("expected_sha256").textValue())) { throw new IOException("capture did not exercise the multiple-child output boundary"); }
        byte[] bytes = JSON.writeValueAsBytes(result); if (bytes.length > 12_000) { throw new IOException("multiple-child fixture budget exceeded"); }
        Files.createDirectories(Path.of(args[4]).toAbsolutePath().getParent()); Files.write(Path.of(args[4]), bytes);
        System.out.println("EDUCATION_MULTI_CAPTURED output_bytes=" + Files.size(output) + " fixture_bytes=" + bytes.length + " fixture_sha256=" + digest(bytes));
    }
    private static Map<String, String> pins(Path root, List<String> paths) throws IOException, NoSuchAlgorithmException {
        Map<String, String> result = new LinkedHashMap<>(); for (String path : paths) { result.put(path, digest(Files.readAllBytes(root.resolve("ck3_autonomous_player/src/xar_autoplayer").resolve(path)))); } return Map.copyOf(result);
    }
    private static String digest(byte[] bytes) throws NoSuchAlgorithmException { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
}
