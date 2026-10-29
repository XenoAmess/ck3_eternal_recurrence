package org.xar.ck3.control.governance.education;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
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

/** Explicit one-time oracle capture; default JUnit never launches Python. No game or native calls. */
public final class CaptureEducationGolden {
    private static final ObjectMapper JSON = new ObjectMapper();
    private CaptureEducationGolden() { }
    public static void main(String[] args) throws IOException, InterruptedException, NoSuchAlgorithmException {
        if (args.length != 5 || args[4].isBlank()) { throw new IllegalArgumentException("repository python scratch output verified-machine-id required"); }
        Path root = Path.of(args[0]).toAbsolutePath(); Path scratch = Path.of(args[2]).toAbsolutePath();
        Files.createDirectories(scratch); Path input = scratch.resolve("education-oracle-input.json");
        Path output = scratch.resolve("education-oracle-output.json");
        for (Path target : List.of(input, output, scratch.resolve("education-oracle.stdout.log"), scratch.resolve("education-oracle.stderr.log"), Path.of(args[3]))) {
            if (Files.exists(target)) { throw new IOException("capture requires fresh evidence path: " + target); }
        }
        List<String> sourcePaths = List.of("family_generation_education_decision_v1.py", "family_generation_education_inputs_v1.py", "education_child_court_owner_readonly_12004.py", "bridge/education_point_source_modifiers_12004.py");
        Map<String, String> sourceBefore = sourcePins(root, sourcePaths);
        ObjectNode manifest = JSON.createObjectNode(); ArrayNode cases = manifest.putArray("cases");
        cases.addObject().put("name", "missing_descendants").putNull("input");
        cases.addObject().put("name", "complete_empty").set("input", base());
        ObjectNode child = base(); occurrence(child, 0x80000033L, true, true); occurrence(child, 0x80000033L, true, true);
        ObjectNode inputs = child.putObject("child_inputs"); inputs.put("source", "native_current_heir_child_inputs"); inputs.put("status", "available"); inputs.putNull("unavailable_reason"); copyFrame(child, inputs);
        ObjectNode read = inputs.putArray("rows").addObject(); read.put("character_id", -2147483597); read.putArray("occurrence_indices").add(0).add(1);
        read.putObject("values").put("source", "native_character_age_and_sex").put("status", "available").putNull("unavailable_reason").put("age_measure_raw", 10).put("sex_selector_raw", 0).put("legacy_extension", "保留");
        traits(read.putObject("childhood_traits"), List.of("curious", "rowdy", "bossy", "pensive", "charming"), List.of("curious", "pensive"));
        traits(read.putObject("education_point_traits"), List.of("intellect_good_1", "intellect_good_2", "intellect_good_3", "intellect_bad_1", "intellect_bad_2", "intellect_bad_3", "shrewd", "dull", "inbred"), List.of("intellect_bad_2", "shrewd"));
        read.putObject("native_focus").put("source", "native_character_current_focus").put("status", "available").putNull("unavailable_reason").put("presence", "absent").putNull("key");
        ObjectNode court = read.putObject("court_owner_source"); court.put("schema", "xar.ck3.current-child-court-owner-readonly/1.20.0.4/v1").put("status", "known_null").put("unavailable_reason", "");
        court.put("child_character_id", 0x80000033L).put("native_revision", 100).put("court_owner_present", false).putNull("court_owner_id").put("child_address", 9007199254740993L).putNull("court_owner_address");
        court.put("getter_return_address", 0).put("fallback_address", 0).putNull("fallback_full_id_raw").putNull("relation_owner_id_raw").put("source_path", "unlanded_relation_absent_fallback").put("fallback_reached", true);
        court.put("getter_projection_complete", true).put("identity_round_trip", true).put("sample_stable", true).put("source_qualified", true);
        cases.addObject().put("name", "full_id_duplicate_occurrences_known_null_focus_and_owner").set("input", child);
        ObjectNode unknown = base(); occurrence(unknown, 500, true, true); occurrence(unknown, 700, null, true);
        cases.addObject().put("name", "partial_classification_missing_optional_reads").set("input", unknown);
        ObjectNode unavailable = base(); unavailable.put("status", "unavailable").put("unavailable_reason", "native_family_unavailable").put("roster_complete", false);
        cases.addObject().put("name", "unavailable_roster").set("input", unavailable);
        JSON.writeValue(input.toFile(), manifest);
        String script = "import json,sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); from xar_autoplayer.family_generation_education_decision_v1 import derive_family_generation_education_decision_inputs_v1 as derive; d=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8')); [(c.update(expected=derive(c['input']))) for c in d['cases']]; Path(sys.argv[3]).write_text(json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n',encoding='utf-8')";
        Process process = new ProcessBuilder(args[1], "-c", script, root.resolve("ck3_autonomous_player/src").toString(), input.toString(), output.toString())
                .redirectOutput(scratch.resolve("education-oracle.stdout.log").toFile()).redirectError(scratch.resolve("education-oracle.stderr.log").toFile()).start();
        if (!process.waitFor(30, TimeUnit.SECONDS)) { process.destroyForcibly(); process.waitFor(); throw new IOException("old education oracle timeout"); }
        if (process.exitValue() != 0) { throw new IOException("old education oracle exit " + process.exitValue()); }
        ObjectNode result = (ObjectNode) JSON.readTree(output.toFile());
        ObjectNode provenance = result.putObject("provenance"); provenance.put("machine_id", args[4]); provenance.put("machine_id_source", "caller_verified_tools/ck3_live_run_id.py_machine"); provenance.put("captured_at_utc", Instant.now().toString());
        provenance.put("producer", "xar_autoplayer.family_generation_education_decision_v1.derive_family_generation_education_decision_inputs_v1");
        provenance.put("scope", "actual_old_pure_producer_outputs_synthetic_current_query_inputs_no_game"); provenance.put("old_producer_exit_code", process.exitValue());
        ObjectNode sources = provenance.putObject("source_sha256");
        Map<String, String> sourceAfter = sourcePins(root, sourcePaths);
        if (!sourceBefore.equals(sourceAfter)) { throw new IOException("old producer source changed during capture"); }
        sourceAfter.forEach(sources::put); provenance.put("source_before_after_unchanged", true);
        byte[] bytes = (JSON.writeValueAsString(result) + "\n").getBytes(StandardCharsets.UTF_8);
        if (bytes.length > 145_000) { throw new IOException("education golden exceeds lane budget"); }
        Files.createDirectories(Path.of(args[3]).toAbsolutePath().getParent()); Files.write(Path.of(args[3]), bytes);
        System.out.println("EDUCATION_GOLDEN_CAPTURED cases=" + cases.size() + " bytes=" + bytes.length + " sha256=" + HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
    }
    private static Map<String, String> sourcePins(Path root, List<String> paths) throws IOException, NoSuchAlgorithmException {
        Map<String, String> result = new LinkedHashMap<>();
        for (String relative : paths) { result.put(relative, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(root.resolve("ck3_autonomous_player/src/xar_autoplayer").resolve(relative))))); }
        return Map.copyOf(result);
    }
    private static ObjectNode base() {
        ObjectNode node = JSON.createObjectNode(); node.put("native_revision", 100).put("played_character_id", 29829).put("heir_character_id", 29830).put("date_raw", 53279400);
        node.put("status", "available").putNull("unavailable_reason").put("roster_complete", true).put("family_present", true).put("data_pointer_present", true).put("native_child_count_raw", 0);
        for (String field : List.of("played_lineage", "heir_lineage")) { node.putObject(field).put("status", "available").putNull("unavailable_reason").put("house_id_raw", 200).put("dynasty_id_raw", 100); }
        node.putArray("rows"); return node;
    }
    private static void occurrence(ObjectNode node, long id, Boolean alive, Boolean child) {
        ArrayNode rows = (ArrayNode) node.get("rows"); ObjectNode row = rows.addObject(); row.put("occurrence_index", rows.size() - 1).put("raw_character_id", id).put("generation_valid", true);
        if (alive == null) { row.putNull("alive"); } else { row.put("alive", alive); }
        if (child == null) { row.putNull("child_of_heir"); } else { row.put("child_of_heir", child); }
        row.put("parent_family_present", true).put("parent_0_character_id_raw", 29830).put("parent_4_character_id_raw", 400);
        row.putObject("lineage").put("status", "available").putNull("unavailable_reason").put("house_id_raw", 200).put("dynasty_id_raw", 100);
        node.put("native_child_count_raw", rows.size());
    }
    private static void copyFrame(ObjectNode from, ObjectNode to) { for (String key : List.of("native_revision", "played_character_id", "heir_character_id", "date_raw")) { to.set(key, from.get(key)); } }
    private static void traits(ObjectNode node, List<String> queried, List<String> present) {
        node.put("source", "native_character_has_trait").put("status", "available").putNull("unavailable_reason");
        ArrayNode keys = node.putArray("queried_trait_keys"); queried.forEach(keys::add); ArrayNode subset = node.putArray("present_trait_keys"); present.forEach(subset::add);
    }
}
