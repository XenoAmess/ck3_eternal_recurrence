package org.xar.ck3.control.wave2.governance.educationneeds;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
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

/** One-time real Python producer/consumer capture; default tests use only the committed results. */
public final class CaptureEducationNeedsGolden {
    private static final ObjectMapper JSON = new ObjectMapper();
    private CaptureEducationNeedsGolden() { }
    public static void main(String[] args) throws IOException, InterruptedException, NoSuchAlgorithmException {
        if (args.length != 5 || args[4].isBlank()) { throw new IllegalArgumentException("root python scratch output verified-machine-id required"); }
        Path root = Path.of(args[0]), scratch = Path.of(args[2]), output = Path.of(args[3]); Files.createDirectories(scratch);
        Path raw = scratch.resolve("needs-oracle.json"), stdout = scratch.resolve("needs-oracle.stdout.log"), stderr = scratch.resolve("needs-oracle.stderr.log");
        for (Path file : List.of(output, raw, stdout, stderr)) { if (Files.exists(file)) { throw new IOException("fresh capture path required: " + file); } }
        List<String> paths = List.of("ck3_autonomous_player/src/xar_autoplayer/family_education_needs_12004.py",
                "ck3_autonomous_player/src/xar_autoplayer/family_generation_education_decision_v1.py", "ck3_autonomous_player/src/xar_autoplayer/family_generation_education_inputs_v1.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/education_point_source_modifiers_12004.py", "ck3_autonomous_player/src/xar_autoplayer/education_child_court_owner_readonly_12004.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/family_guardian_negative_cadence_v1.py",
                "ck3_autonomous_player/tests/fixtures/family_guardian_p43_completed_projection_v1.json",
                "java/ck3-control/governance-policy/src/test/resources/education/producer-golden.json");
        Map<String, String> before = pins(root, paths);
        String script = """
                import copy,hashlib,json,sys
                from pathlib import Path
                root=Path(sys.argv[1]); sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
                from xar_autoplayer.family_generation_education_decision_v1 import derive_family_generation_education_decision_inputs_v1 as educate
                from xar_autoplayer.family_education_needs_12004 import derive_family_education_needs_12004 as needs, project_family_education_request_candidate_12004 as candidate
                from xar_autoplayer.bridge.family_guardian_negative_cadence_v1 import source_scope
                actual=json.loads((root/'ck3_autonomous_player/tests/fixtures/family_guardian_p43_completed_projection_v1.json').read_text(encoding='utf-8'))['rows'][0]
                family=actual['family_marriage_current_relationship']
                request={'schema':'xar.education-needs.request/v1','decision_inputs':family['family_generation_education_decision_inputs_v1'], 'child_relation_materials':family.get('current_child_relation_materials_v1'),'child_education_provider_inputs':family.get('current_child_education_provider_inputs_v1'),'child_education_provider_source':family.get('current_child_education_provider_inputs_source_v1')}
                def invoke(r):
                    return needs(r['decision_inputs'],child_relation_materials=r['child_relation_materials'],child_education_provider_inputs=r['child_education_provider_inputs'],child_education_provider_source=r['child_education_provider_source'])
                def digest(v):
                    b=json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
                    return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
                def variant(name):
                    r=copy.deepcopy(request)
                    if name=='no_attachments':
                        for key in ('child_relation_materials','child_education_provider_inputs','child_education_provider_source'): r[key]=None
                    elif name=='no_decision': r['decision_inputs']=None
                    elif name=='unavailable_provider':
                        p=r['child_education_provider_inputs']; p.update(status='unavailable',unavailable_reason='fixture_provider_unavailable',roster_complete=False,collection_available=False,child_observation_complete=False,rows=[])
                    return r
                cases=[]
                for name in ('actual_p43','no_attachments','no_decision','unavailable_provider'):
                    cases.append({'name':name,'expected':digest(invoke(variant(name)))})
                current=invoke(request)
                scope=source_scope(actual['planning_source_frame'],current['rows'][0],family['heir_character_id'])
                if scope is None: raise RuntimeError('actual downstream guardian scope consumer did not accept captured needs')
                native=actual['family_education_observations'][0]['default_query']['character_interaction_ordinary_context']
                keys=('status','interaction_key','unavailable_reason','effective_roles','snapshot_revision','date_raw','player_character_id','game_pid','connection_generation','can_send','ready_to_initiate')
                context={key:copy.deepcopy(native[key]) for key in keys}
                candidates=[]
                for name in ('actual_native_pair','other_child','known_null_guardian','other_interaction','unavailable_context'):
                    c=copy.deepcopy(context)
                    if name=='other_child': c['effective_roles']['secondary_recipient_id']=501
                    elif name=='known_null_guardian': c['effective_roles']['secondary_actor_id']=None
                    elif name=='other_interaction': c['interaction_key']='offer_vassalization_interaction'
                    elif name=='unavailable_context': c.update(status='unavailable',unavailable_reason='fixture_context_unavailable')
                    candidates.append({'name':name,'expected':candidate(current['rows'][0],c)})
                baseline=json.loads((root/'java/ck3-control/governance-policy/src/test/resources/education/producer-golden.json').read_text(encoding='utf-8'))
                upstream=[{'index':i,'name':c['name'],'expected':digest(needs(educate(c['input'])))} for i,c in enumerate(baseline['cases'])]
                result={'schema':'xar.education-needs.producer-consumer-golden/v1','request':request,'cases':cases,'ordinary_context_projection':context,'candidate_cases':candidates,'upstream_cases':upstream,'actual_guardian_scope_consumer':scope,'planning_frame':actual['planning_source_frame'],'heir_character_id':family['heir_character_id']}
                Path(sys.argv[2]).write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\\n',encoding='utf-8')
                """;
        ProcessBuilder builder = new ProcessBuilder(args[1], "-c", script, root.toString(), raw.toString());
        builder.environment().put("PYTHONUTF8", "1"); builder.environment().put("PYTHONIOENCODING", "utf-8");
        Process process = builder.redirectOutput(stdout.toFile()).redirectError(stderr.toFile()).start();
        if (!process.waitFor(30, TimeUnit.SECONDS)) { process.destroyForcibly(); process.waitFor(); throw new IOException("education needs capture timed out"); }
        if (process.exitValue() != 0) { throw new IOException("education needs actual producer/consumer exit " + process.exitValue()); }
        Map<String, String> after = pins(root, paths); if (!before.equals(after)) { throw new IOException("producer/consumer inputs changed during capture"); }
        ObjectNode data = (ObjectNode) JSON.readTree(raw.toFile()); ObjectNode provenance = data.putObject("provenance");
        provenance.put("machine_id", args[4]); provenance.put("machine_id_source", "caller_verified_tools/ck3_live_run_id.py_machine"); provenance.put("captured_at_utc", Instant.now().toString()); provenance.put("source_before_after_unchanged", true); provenance.put("producer_exit_code", process.exitValue());
        provenance.put("scope", "actual_retained_P43_projection_and_original_pure_producer_to_needs_candidate_and_guardian_scope_consumers_no_game"); ObjectNode refs = provenance.putObject("source_sha256"); after.forEach(refs::put);
        provenance.put("retained_observation_machine_id", "unknown"); provenance.put("retained_observation_observed_at_utc", "unknown");
        provenance.put("retained_observation_source", "ck3_autonomous_player/tests/fixtures/family_guardian_p43_completed_projection_v1.json#rows[0]");
        byte[] bytes = JSON.writeValueAsBytes(data); if (bytes.length > 90_000) { throw new IOException("education needs golden exceeds bounded lane allocation"); }
        Files.createDirectories(output.toAbsolutePath().getParent()); Files.write(output, bytes);
        System.out.println("EDUCATION_NEEDS_CAPTURED bytes=" + bytes.length + " sha256=" + digest(bytes) + " upstream=" + data.get("upstream_cases").size() + " candidates=" + data.get("candidate_cases").size());
    }
    private static Map<String, String> pins(Path root, List<String> paths) throws IOException, NoSuchAlgorithmException { Map<String, String> pins = new LinkedHashMap<>(); for (String path : paths) { pins.put(path, digest(Files.readAllBytes(root.resolve(path)))); } return Map.copyOf(pins); }
    private static String digest(byte[] bytes) throws NoSuchAlgorithmException { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
}
