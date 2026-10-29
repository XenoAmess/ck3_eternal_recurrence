package org.xar.ck3.control.application.planning.family;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsComposer;
import org.xar.ck3.control.wave3.governance.guardianskills.GuardianSkillInputs;
import org.xar.ck3.control.wave3.governance.guardianskills.GuardianSkillsCodec;

/** Executes unchanged original producers and their actual retained inputs. Missing reference environment fails, never skips. */
final class FamilyEducationProducerParityTest {
    @Test void originalProducerFeedsCompleteReviewBothSkillsAndOriginalServiceCadence() throws Exception {
        Obj capture = original();
        assertEquals(t("xar.java.family-education-original-parity/v1"), capture.get("schema"));
        assertFalse(text(capture.get("machine_id")).isBlank());
        assertEquals(3, array(capture.get("cases")).size());
        FamilyGuardianCadence cadence = new FamilyGuardianCadence();
        for (Value raw : array(capture.get("cases"))) {
            Obj sample = object(raw), snapshot = object(sample.get("snapshot")), query = object(sample.get("query"));
            Obj needs = decode(EducationNeedsComposer.composeDecision(bytes(sample.get("decision")),
                    bytes(sample.get("relations")), bytes(sample.get("provider")), bytes(sample.get("provider_source"))));
            Obj row = object(array(needs.get("rows")).get(0));
            assertEquals(sample.get("needs"), row, text(sample.get("name")));
            Obj review = FamilyEducationReview.prepare(query, snapshot, object(sample.get("intent")));
            assertEquals(sample.get("review"), review, text(sample.get("name")) + " complete original payload review and token");
            assertEquals(review, decode(bytes(review)), "review serialization retains original JSON type domain");
            for (Value checkRaw : array(sample.get("validation"))) {
                Obj check = object(checkRaw), intent = object(check.get("intent"));
                if (yes(check.get("accepted"))) assertEquals(check.get("expected"), FamilyEducationReview.prepare(query, snapshot, intent), text(check.get("name")));
                else assertThrows(IllegalArgumentException.class, () -> FamilyEducationReview.prepare(query, snapshot, intent), text(check.get("name")));
            }
            assertFalse(yes(review.get("dispatch_ready"))); assertFalse(yes(review.get("material_result")));
            assertSkills(row, object(object(sample.get("default_query")).get("character_interaction_ordinary_context")), sample.get("default_skills"));
            assertSkills(row, object(query.get("character_interaction_ordinary_context")), sample.get("selected_skills"));
            var scope = cadence.scope(snapshot, row, sample.get("heir_id"));
            assertTrue(scope.isPresent());
            assertEquals(sample.get("deferred_before"), cadence.deferred(scope).<Value>map(value -> value).orElse(Nil.INSTANCE));
            Optional<Obj> observed = cadence.observe(positive(row.get("raw_character_id")), scope, sample.get("default_query"), rows(array(sample.get("attempts"))));
            assertEquals(sample.get("cadence"), observed.<Value>map(value -> value).orElse(Nil.INSTANCE));
            assertFalse(yes(observed.orElseThrow().get("business_action_credit")));
            assertTrue(cadence.deferred(scope).isPresent(), "only completed original negative may be reused in this frame");
            Obj changedCourt = object(row.get("current_court_owner")).with("owner_character_id_raw", n(999));
            assertTrue(cadence.deferred(cadence.scope(snapshot, row.with("current_court_owner", changedCourt), sample.get("heir_id"))).isEmpty());
        }
        cadence.selectableIntentObserved(); assertTrue(cadence.currentState().records().isEmpty());
        assertTrue(new FamilyGuardianCadence().currentState().records().isEmpty(), "cold host never restores an in-memory negative cache");
    }
    @Test void digestMatchesPythonAsciiIntegerAndFiniteNumberDomain() {
        Obj input = obj("\u4e2d\ud83d\ude00", t("\u00e9\u007f"), "u64", new IntegerValue(new java.math.BigInteger("18446744073709551615")), "float", new DecimalValue("1.5"));
        assertEquals("{\"float\":1.5,\"u64\":18446744073709551615,\"\\u4e2d\\ud83d\\ude00\":\"\\u00e9\\u007f\"}",
                new String(FamilyEducationReview.asciiCanonical(input), StandardCharsets.US_ASCII));
    }
    private static void assertSkills(Obj needs, Obj context, Value expected) {
        var input = GuardianSkillsCodec.decode(bytes(obj("schema", t(GuardianSkillsCodec.INPUT_SCHEMA), "needs", needs, "context", context)));
        assertEquals(expected, decode(GuardianSkillsCodec.encodeProjection(GuardianSkillInputs.project(input))));
    }
    private static Obj original() throws Exception {
        String configured = required("xar.repository.root"), interpreter = required("xar.python");
        if (!Path.of(configured).isAbsolute() || !Path.of(interpreter).isAbsolute()) throw new IllegalStateException("explicit absolute original repository and Python bindings required");
        Path repository = Path.of(configured).toRealPath(), python = Path.of(interpreter).toRealPath();
        if (!Files.isRegularFile(python)) throw new IllegalStateException("actual original repository interpreter missing: " + python);
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-B", "-I", "-u", "-", repository.toString());
        builder.directory(repository.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTHONUTF8", "1");
        Process process = builder.start();
        try (var workers = Executors.newVirtualThreadPerTaskExecutor()) {
            var stdout = workers.submit(() -> read(process.getInputStream(), 1_048_576));
            var stderr = workers.submit(() -> read(process.getErrorStream(), 16_384));
            try (var input = process.getOutputStream()) { input.write(SCRIPT.getBytes(StandardCharsets.UTF_8)); }
            if (!process.waitFor(Duration.ofSeconds(60).toMillis(), TimeUnit.MILLISECONDS)) {
                process.destroyForcibly(); process.waitFor(10, TimeUnit.SECONDS);
                throw new IllegalStateException("unchanged original family producer timed out; no parity credit");
            }
            byte[] raw = stdout.get(10, TimeUnit.SECONDS), errors = stderr.get(10, TimeUnit.SECONDS);
            assertEquals(0, process.exitValue(), new String(errors, StandardCharsets.UTF_8));
            assertEquals(0, errors.length, "reference producer stderr retained as failure");
            return decodeDomain(raw);
        } finally { if (process.isAlive()) { process.destroyForcibly(); process.waitFor(10, TimeUnit.SECONDS); } }
    }
    private static byte[] read(java.io.InputStream stream, int maximum) throws IOException {
        byte[] raw = stream.readNBytes(maximum + 1); if (raw.length > maximum) throw new IOException("bounded original producer output exceeded " + maximum); return raw;
    }
    private static String required(String property) {
        String value = System.getProperty(property);
        if (value == null || value.isBlank()) throw new IllegalStateException("original family producer parity requires " + property + "; not executed");
        return value;
    }
    private static final String SCRIPT = """
import sys,json,pathlib,hashlib,copy
root=pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0,str(root/'tools'));sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
names=['ck3_autonomous_player/src/xar_autoplayer/bridge/education_payload_materializer_private_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/family_guardian_negative_cadence_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/request_guardian_skill_inputs_private_v1.py','ck3_autonomous_player/src/xar_autoplayer/family_education_needs_12004.py','ck3_autonomous_player/tests/fixtures/family_guardian_p43_completed_projection_v1.json']
before={name:(root/name).read_bytes() for name in names}
expected=[(12006,'75afb2ca71bf156975e4bc19b08bb1c03f283b39b2547ee070664f2df22bf60e'),(11308,'2becd9557b26620b661b33276970c82633e6461492033a99b53579850bc1041c'),(11292,'dbc10951fbb92bdaa3355c33134edf2f402271eb7f7218374ab8a0a732979b6a'),(8640,'6e64515f2c47dc19119cd5de099613f6679e6af902cf9454f6a1423eb443259b'),(152325,'329d2d7ad78b9e0122ec5c55cf2fc9f63dff1da77891387a5133403140a569db')]
for name,(size,digest) in zip(names,expected):
 raw=before[name]
 if len(raw)!=size or hashlib.sha256(raw).hexdigest()!=digest:raise RuntimeError('fixed original input pin changed: '+name)
from ck3_live_run_id import current_machine_id
from xar_autoplayer.bridge.education_payload_materializer_private_v1 import prepare_education_payload_review_v1
from xar_autoplayer.bridge.request_guardian_skill_inputs_private_v1 import project_request_guardian_focus_skills_v1
from xar_autoplayer.bridge import family_guardian_negative_cadence_v1 as negative
from xar_autoplayer.family_education_needs_12004 import derive_family_education_needs_12004
records={};cases=[]
fixture=json.loads(before[names[-1]])
for sample in fixture['rows']:
 frame=sample['planning_source_frame'];relation=sample['family_marriage_current_relationship']
 decision=relation['family_generation_education_decision_inputs_v1'];relations=relation['current_child_relation_materials_v1'];provider=relation['current_child_education_provider_inputs_v1'];provider_source=relation['current_child_education_provider_inputs_source_v1']
 needs=derive_family_education_needs_12004(decision,child_relation_materials=relations,child_education_provider_inputs=provider,child_education_provider_source=provider_source)['rows'][0]
 observation=sample['family_education_observations'][0];default=observation['default_query'];attempts=observation['request_attempts'];query=attempts[0]['query'];native=query['character_interaction_ordinary_context'];roles=native['effective_roles']
 snapshot={**frame,'played_character':{'character_id':frame['actor_character_id'],'alive':True},'paused':True,'map_ready':True,'active_wars':[],'active_event':None,'pending_character_interaction':None,'one_life_terminal_reason':None,'diagnostics':{'connected':True,'bridge_pid':frame['bridge_pid'],'connection_generation':frame['connection_generation'],'hello':{'expected_ck3_version':'1.20.0.4','expected_ck3_sha256':native['executable_sha256'],'ck3_build_match':True,'game_adapter_id':'ck3-1.20.0.4-msvc-x64','pid':frame['bridge_pid']}}}
 keys=list(dict.fromkeys(row['canonical_flag_key'] for row in native['education_option_rows']['rows'] if row['ordinal_selected']))
 intent={'recipient_id':native['recipient_id'],'child_full_id':roles['secondary_recipient_id'],'guardian_full_id':roles['secondary_actor_id'],'requested_option_keys':keys}
 review=prepare_education_payload_review_v1(query,snapshot,expected_revision=frame['revision'],**intent)
 validation=[]
 for name,key,value in [('boolean-child','child_full_id',True),('float-guardian','guardian_full_id',float(intent['guardian_full_id'])),('null-recipient','recipient_id',None),('same-pair','guardian_full_id',intent['child_full_id']),('null-option-intent','requested_option_keys',None),('duplicate-option-intent','requested_option_keys',['convert_culture','convert_culture']),('unknown-option-intent','requested_option_keys',['not_observed']),('empty-option-intent','requested_option_keys',[])]:
  changed=copy.deepcopy(intent);changed[key]=value
  try:
   expected=prepare_education_payload_review_v1(query,snapshot,expected_revision=frame['revision'],**changed);accepted=True
  except ValueError:
   expected=None;accepted=False
  validation.append({'name':name,'intent':changed,'accepted':accepted,'expected':expected})
 scope=negative.source_scope(frame,needs,relation['heir_character_id'])
 deferred_before=negative.deferred(records,scope,frame)
 result=negative.observe(records,scope,frame,default,attempts,selected_step='life-advance')
 cases.append({'name':sample['source_ref'],'snapshot':snapshot,'decision':decision,'relations':relations,'provider':provider,'provider_source':provider_source,'needs':needs,'query':query,'default_query':default,'attempts':attempts,'intent':intent,'review':review,'validation':validation,'default_skills':project_request_guardian_focus_skills_v1(needs,default['character_interaction_ordinary_context']),'selected_skills':project_request_guardian_focus_skills_v1(needs,native),'heir_id':relation['heir_character_id'],'deferred_before':deferred_before,'cadence':result})
for name,raw in before.items():
 if (root/name).read_bytes()!=raw:raise RuntimeError('original source changed during capture: '+name)
out={'schema':'xar.java.family-education-original-parity/v1','machine_id':current_machine_id(),'retained_runtime_machine_id':'unknown','projection_not_original':True,'source_manifest':[{'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()} for name,raw in before.items()],'cases':cases}
sys.stdout.buffer.write((json.dumps(out,ensure_ascii=False,separators=(',',':'),allow_nan=False)+chr(10)).encode('utf-8'))
""";
}
