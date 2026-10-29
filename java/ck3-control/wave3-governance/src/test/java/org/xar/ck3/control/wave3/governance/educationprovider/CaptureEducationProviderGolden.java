package org.xar.ck3.control.wave3.governance.educationprovider;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.ByteArrayOutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.zip.GZIPOutputStream;

/** Explicit offline original pure validator/needs capture. It does not mint an actual native export qualification. */
public final class CaptureEducationProviderGolden {
    private static final ObjectMapper JSON = new ObjectMapper();
    private CaptureEducationProviderGolden() { }
    public static void main(String[] args) throws IOException, InterruptedException, NoSuchAlgorithmException {
        if (args.length != 7 || args[4].isBlank()) { throw new IllegalArgumentException("root python scratch output verified-machine-id frozen-provider frozen-needs required"); }
        Path root = Path.of(args[0]).toRealPath(), scratch = Path.of(args[2]).toAbsolutePath().normalize(), output = Path.of(args[3]).toAbsolutePath().normalize();
        if (scratch.startsWith(root) || output.startsWith(root) || !Files.isRegularFile(Path.of(args[1]))) {
            throw new IllegalArgumentException("offline oracle executable and explicit non-source evidence roots required");
        }
        Files.createDirectory(scratch);
        Path input = scratch.resolve("provider-input.json"), raw = scratch.resolve("provider-oracle.json"), stdout = scratch.resolve("provider.stdout.log"), stderr = scratch.resolve("provider.stderr.log");
        for (Path path : List.of(input, raw, stdout, stderr, output)) { if (Files.exists(path)) { throw new IOException("fresh evidence path required: " + path); } }
        List<String> sources = List.of("ck3_autonomous_player/src/xar_autoplayer/bridge/current_first_heir_descendants_v1.py",
                "ck3_autonomous_player/src/xar_autoplayer/family_generation_education_decision_v1.py", "ck3_autonomous_player/src/xar_autoplayer/family_generation_education_inputs_v1.py",
                "ck3_autonomous_player/src/xar_autoplayer/education_child_court_owner_readonly_12004.py", "ck3_autonomous_player/src/xar_autoplayer/bridge/education_point_source_modifiers_12004.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/guardian_factory_create_inputs_contract_v1.py", "ck3_autonomous_player/src/xar_autoplayer/bridge/current_first_heir_relationship_private_transport.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/__init__.py", "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py");
        Map<String, String> before = pins(root, sources);
        Path frozenProvider = Path.of(args[5]).toRealPath(), frozenNeeds = Path.of(args[6]).toRealPath();
        if (!hash(Files.readAllBytes(frozenProvider)).equals("7e0a3097918ccfdcf4ca661e1eba1839d96a0eda7cb68ca3e4ac4659df910c71")
                || !hash(Files.readAllBytes(frozenNeeds)).equals("6e64515f2c47dc19119cd5de099613f6679e6af902cf9454f6a1423eb443259b")) {
            throw new IOException("frozen original provider/needs source pins changed");
        }
        ObjectNode manifest = JSON.createObjectNode(); ArrayNode cases = manifest.putArray("cases");
        for (String name : List.of("available_duplicates_high_id", "missing_optional", "unavailable_no_roster", "partial_traits", "partial_culture",
                "known_empty", "dead_unread_child_extension", "uint64_max_revision", "no_heir_empty", "qualified_false", "roster_conflict",
                "selected_order", "provider_order", "trait_order", "trait_duplicate", "authoritative_guardian", "provider_status", "count_incomplete",
                "native_revision_float", "raw_id_bool", "missing_mandatory", "unknown_provider_field")) {
            ObjectNode request = fixture(); mutate(name, request); ObjectNode item = cases.addObject().put("name", name); item.set("request", request);
        }
        JSON.writeValue(input.toFile(), manifest);
        if (Files.size(input) > 196_608) { throw new IOException("provider capture input manifest exceeds finite bound"); }
        String script = """
                import copy,hashlib,json,sys,importlib.util
                from pathlib import Path
                root=Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
                def frozen(name,path):
                    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
                provider_oracle=frozen('xar_autoplayer.bridge._education_provider_original_oracle',sys.argv[4])
                needs_oracle=frozen('xar_autoplayer._education_needs_original_oracle',sys.argv[5])
                validate=provider_oracle.validate_current_child_education_provider_inputs_v1
                from xar_autoplayer.family_generation_education_decision_v1 import derive_family_generation_education_decision_inputs_v1 as educate
                needs=needs_oracle.derive_family_education_needs_12004
                def wire(v): return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
                data=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
                for c in data['cases']:
                    r=c['request']; before=copy.deepcopy(r)
                    # This exact UTF8 text is the only persisted input. Tree parsing in the Java
                    # envelope must never normalize a negative integer-token test such as 100.0.
                    c['input_json']=wire(r).decode('utf-8')
                    try:
                        result=validate(r['value'],family_result=r['family_result'],qualified=r['qualified'],request_id=r['request_id'],revision=r['revision'],actor=r['actor'],heir=r['heir'],date=r['date'])
                    except ValueError as exc:
                        c['accepted']=False;c['error_type']=type(exc).__name__;c['error_message']=str(exc)
                    else:
                        c['accepted']=True;c['expected']=result
                        if result is not None and r['family_result'].get('current_first_heir_descendants_v1') is not None and c['name'] != 'dead_unread_child_extension':
                            decision=educate(r['family_result']['current_first_heir_descendants_v1'])
                            proof={'request_id':r['request_id'],'binding_scope':'query_before_after','bridge_pid':7001,'connection_generation':1,'native_revision':r['revision'],'date_raw':r['date'],'played_character_id':r['actor'],'heir_character_id':None if r['heir']==-1 else r['heir'],'sidecar_bytes':len(wire(result)),'sidecar_sha256':hashlib.sha256(wire(result)).hexdigest(),'same_request_export_completed':True}
                            final=needs(decision,child_relation_materials=None,child_education_provider_inputs=result,child_education_provider_source=proof)
                            c['needs_inputs']={'decision':decision,'source':proof};c['needs_expected']={'sha256':hashlib.sha256(wire(final)).hexdigest(),'bytes':len(wire(final))}
                    if r!=before: raise RuntimeError('original validator mutated caller input')
                    del c['request']
                raw=wire(data)+b'\\n'
                if len(raw)>768000: raise ValueError('provider raw oracle exceeds finite bound')
                with Path(sys.argv[3]).open('xb') as stream: stream.write(raw)
                """;
        ProcessBuilder builder = new ProcessBuilder(args[1], "-B", "-", root.toString(), input.toString(), raw.toString(), frozenProvider.toString(), frozenNeeds.toString());
        builder.environment().put("PYTHONUTF8", "1"); builder.environment().put("PYTHONIOENCODING", "utf-8");
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        Process process = builder.redirectOutput(stdout.toFile()).redirectError(stderr.toFile()).start();
        try (var stdin = process.getOutputStream()) { stdin.write(script.getBytes(StandardCharsets.UTF_8)); }
        if (!process.waitFor(30, TimeUnit.SECONDS)) { process.destroyForcibly(); process.waitFor(); throw new IOException("provider original capture timeout"); }
        if (process.exitValue() != 0) { throw new IOException("provider original producer/consumer exit " + process.exitValue()); }
        if (Files.size(stdout) > 65_536 || Files.size(stderr) > 65_536) { throw new IOException("provider original capture log exceeds finite bound"); }
        Map<String, String> after = pins(root, sources); if (!before.equals(after)) { throw new IOException("original sources changed during capture"); }
        if (!hash(Files.readAllBytes(frozenProvider)).equals("7e0a3097918ccfdcf4ca661e1eba1839d96a0eda7cb68ca3e4ac4659df910c71")
                || !hash(Files.readAllBytes(frozenNeeds)).equals("6e64515f2c47dc19119cd5de099613f6679e6af902cf9454f6a1423eb443259b")) {
            throw new IOException("frozen original provider/needs changed during capture");
        }
        if (Files.size(raw) > 768_000) { throw new IOException("provider raw oracle exceeds finite bound"); }
        ObjectNode result = (ObjectNode) JSON.readTree(raw.toFile()); ObjectNode provenance = result.putObject("provenance");
        provenance.put("machine_id", args[4]).put("machine_id_source", "caller_verified_tools/ck3_live_run_id.py_machine").put("captured_at_utc", Instant.now().toString());
        provenance.put("scope", "actual_original_pure_validator_to_needs_synthetic_typed_fixture_no_native_source_qualification_no_game");
        provenance.put("input_representation", "canonical_utf8_input_json_preserves_integer_and_float_tokens");
        provenance.put("native_observation_machine_id", "unknown").put("source_before_after_unchanged", true).put("producer_exit_code", process.exitValue());
        provenance.put("outer_guardian_factory_qualification_migrated", false).put("live_native_source_admitted", false);
        ObjectNode sourcePins = provenance.putObject("source_sha256"); after.forEach(sourcePins::put);
        ObjectNode frozenPins = provenance.putObject("frozen_original_source_sha256");
        frozenPins.put(frozenProvider.toString(), hash(Files.readAllBytes(frozenProvider))).put(frozenNeeds.toString(), hash(Files.readAllBytes(frozenNeeds)));
        byte[] bytes = JSON.writeValueAsBytes(result); if (bytes.length > 768_000) { throw new IOException("provider golden uncompressed bound exceeded"); }
        ByteArrayOutputStream packed = new ByteArrayOutputStream();
        try (GZIPOutputStream gzip = new GZIPOutputStream(packed)) { gzip.write(bytes); }
        byte[] compressed = packed.toByteArray(); if (compressed.length > 50_000) { throw new IOException("provider golden exceeds finite lane allocation"); }
        Files.createDirectories(output.toAbsolutePath().getParent()); Files.write(output, compressed, StandardOpenOption.CREATE_NEW);
        System.out.println("EDUCATION_PROVIDER_CAPTURED cases=" + cases.size() + " bytes=" + compressed.length + " uncompressed=" + bytes.length + " sha256=" + hash(compressed));
    }
    private static ObjectNode fixture() {
        ObjectNode root = JSON.createObjectNode(); root.put("schema", "xar.education-provider.validation-request/v1").put("qualified", true)
                .put("request_id", "education-provider-合同").put("revision", 100).put("actor", 29829).put("heir", 29830).put("date", 53279400);
        ObjectNode family = root.putObject("family_result"); family.put("heir_character_id", 29830);
        ObjectNode descendants = family.putObject("current_first_heir_descendants_v1"); frame(descendants); descendants.put("status", "available").putNull("unavailable_reason")
                .put("roster_complete", true).put("family_present", true).put("data_pointer_present", true).put("native_child_count_raw", 3);
        for (String key : List.of("played_lineage", "heir_lineage")) { descendants.putObject(key).put("status", "available").putNull("unavailable_reason").put("house_id_raw", 200).put("dynasty_id_raw", 100); }
        ArrayNode raw = descendants.putArray("rows");
        for (int index = 0; index < 3; index++) { raw.addObject().put("occurrence_index", index).put("raw_character_id", index == 1 ? 600 : 0x8000_0033L)
                .put("generation_valid", true).put("alive", true).put("child_of_heir", true); }
        ObjectNode selected = descendants.putObject("child_inputs"); frame(selected); selected.put("source", "native_current_heir_child_inputs").put("status", "available").putNull("unavailable_reason");
        ArrayNode children = selected.putArray("rows");
        for (int index = 0; index < 2; index++) {
            ObjectNode child = children.addObject().put("character_id", index == 0 ? -2147483597 : 600); ArrayNode indices = child.putArray("occurrence_indices"); if (index == 0) { indices.add(0).add(2); } else { indices.add(1); }
            child.putObject("values").put("source", "native_character_age_and_sex").put("status", "available").putNull("unavailable_reason").put("age_measure_raw", 10).put("sex_selector_raw", 0);
            ObjectNode traits = child.putObject("childhood_traits"); traits.put("source", "native_character_has_trait").put("status", "available").putNull("unavailable_reason");
            ArrayNode queried = traits.putArray("queried_trait_keys"); List.of("curious", "rowdy", "bossy", "pensive", "charming").forEach(queried::add); traits.putArray("present_trait_keys").add("curious");
        }
        ObjectNode provider = root.putObject("value"); provider.put("schema_version", 1).put("read_only", true).put("source", "same_query_actual4_child_education_inputs").put("request_id", root.get("request_id").textValue())
                .put("native_revision", 100).put("date_raw", 53279400).put("played_character_full_id", 29829).put("heir_character_full_id", 29830)
                .put("status", "available").putNull("unavailable_reason").put("roster_complete", true).put("collection_available", true).put("child_observation_complete", true)
                .put("m6_inputs_complete", false).put("guardian_role_equivalence_qualified", false);
        ArrayNode catalog = provider.putArray("queried_education_trait_keys");
        for (String skill : List.of("diplomacy", "martial", "stewardship", "intrigue", "learning")) { for (int rank = 1; rank <= 5; rank++) { catalog.add("education_" + skill + "_" + rank); } }
        ArrayNode rows = provider.putArray("rows");
        for (int index = 0; index < 2; index++) {
            ObjectNode row = rows.addObject().put("child_full_id", index == 0 ? 0x8000_0033L : 600).put("role_source", "current_living_actual_child_of_first_heir");
            ArrayNode indices = row.putArray("occurrence_indices"); if (index == 0) { indices.add(0).add(2); } else { indices.add(1); }
            ObjectNode traits = row.putObject("education_traits"); traits.put("available", true).putNull("unavailable_reason"); traits.putArray("present_trait_keys").add("education_martial_2");
            row.putObject("culture_parameter").put("key", "better_ward_education").put("available", true).put("culture_full_id", 0xffff_ffffL).put("value", false).putNull("unavailable_reason");
            for (String field : List.of("guardian_full_id", "guardian_culture_parameter", "rite_parameters", "education_type", "education_progress")) { row.putNull(field); }
            row.put("guardian_unavailable_reason", "authoritative_educator_identity_not_observed").put("rite_unavailable_reason", "target_rite_education_parameters_not_observed")
                    .put("education_variables_unavailable_reason", "typed_target_variable_value_access_not_wired");
        }
        return root;
    }
    private static void frame(ObjectNode value) { value.put("native_revision", 100).put("played_character_id", 29829).put("heir_character_id", 29830).put("date_raw", 53279400); }
    private static void mutate(String name, ObjectNode root) {
        ObjectNode provider = (ObjectNode) root.get("value"), family = (ObjectNode) root.get("family_result");
        ObjectNode descendants = (ObjectNode) family.get("current_first_heir_descendants_v1"); ObjectNode selected = (ObjectNode) descendants.get("child_inputs");
        ObjectNode first = (ObjectNode) provider.get("rows").get(0);
        switch (name) {
            case "available_duplicates_high_id" -> { }
            case "missing_optional" -> root.putNull("value");
            case "unavailable_no_roster" -> { provider.put("status", "unavailable").put("unavailable_reason", "fixture-unavailable").put("roster_complete", false).put("collection_available", false).put("child_observation_complete", false).putArray("rows"); family.remove("current_first_heir_descendants_v1"); }
            case "partial_traits", "partial_culture" -> { provider.put("status", "partial").put("unavailable_reason", "education_child_inputs_partially_observed").put("child_observation_complete", false); ObjectNode leaf = (ObjectNode) first.get(name.equals("partial_traits") ? "education_traits" : "culture_parameter"); leaf.put("available", false).put("unavailable_reason", "fixture-read-unavailable"); leaf.putNull(name.equals("partial_traits") ? "present_trait_keys" : "value"); }
            case "known_empty", "no_heir_empty" -> { descendants.put("native_child_count_raw", 0).put("data_pointer_present", false).putArray("rows"); selected.putArray("rows"); provider.putArray("rows"); if (name.equals("no_heir_empty")) { root.put("heir", -1); family.putNull("heir_character_id"); descendants.putNull("heir_character_id"); selected.putNull("heir_character_id"); provider.put("heir_character_full_id", 0xffff_ffffL); } }
            case "dead_unread_child_extension" -> { ((ObjectNode) descendants.get("rows").get(1)).put("alive", false).putObject("child_of_heir").put("ignored_unread", 1.0); ((ArrayNode) selected.get("rows")).remove(1); ((ArrayNode) provider.get("rows")).remove(1); }
            case "uint64_max_revision" -> { java.math.BigInteger revision = new java.math.BigInteger("18446744073709551615"); root.put("revision", revision); provider.put("native_revision", revision); descendants.put("native_revision", revision); selected.put("native_revision", revision); }
            case "qualified_false" -> root.put("qualified", false);
            case "roster_conflict" -> ((ObjectNode) descendants.get("rows").get(2)).put("alive", false);
            case "selected_order" -> { ArrayNode rows = (ArrayNode) selected.get("rows"); JsonNode row = rows.remove(0); rows.add(row); }
            case "provider_order" -> { ArrayNode rows = (ArrayNode) provider.get("rows"); JsonNode row = rows.remove(0); rows.add(row); }
            case "trait_order" -> ((ObjectNode) first.get("education_traits")).putArray("present_trait_keys").add("education_learning_1").add("education_martial_2");
            case "trait_duplicate" -> ((ArrayNode) first.get("education_traits").get("present_trait_keys")).add("education_martial_2");
            case "authoritative_guardian" -> first.put("guardian_full_id", 900);
            case "provider_status" -> provider.put("status", "partial").put("unavailable_reason", "education_child_inputs_partially_observed").put("child_observation_complete", false);
            case "count_incomplete" -> descendants.put("native_child_count_raw", 2);
            case "native_revision_float" -> provider.put("native_revision", 100.0);
            case "raw_id_bool" -> ((ObjectNode) descendants.get("rows").get(0)).put("raw_character_id", true);
            case "missing_mandatory" -> provider.remove("m6_inputs_complete");
            case "unknown_provider_field" -> provider.put("new_field", false);
            default -> throw new IllegalArgumentException("unknown capture fixture " + name);
        }
    }
    private static Map<String, String> pins(Path root, List<String> paths) throws IOException, NoSuchAlgorithmException { Map<String, String> result = new LinkedHashMap<>(); for (String path : paths) { result.put(path, hash(Files.readAllBytes(root.resolve(path)))); } return Map.copyOf(result); }
    private static String hash(byte[] bytes) throws NoSuchAlgorithmException { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
}
