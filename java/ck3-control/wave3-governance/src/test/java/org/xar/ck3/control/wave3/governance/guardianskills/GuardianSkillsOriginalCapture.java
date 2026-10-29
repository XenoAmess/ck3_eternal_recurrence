package org.xar.ck3.control.wave3.governance.guardianskills;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.capture.PythonStdinCapture;

/** Offline unchanged original reference capture; qualification belongs to the outer owner. */
public final class GuardianSkillsOriginalCapture {
    private GuardianSkillsOriginalCapture() { }

    public static void main(String[] arguments) throws IOException, InterruptedException {
        if (arguments.length != 5) {
            throw new IllegalArgumentException("repository python scratch output machine required");
        }
        Path repository = Path.of(arguments[0]).toRealPath();
        Path python = Path.of(arguments[1]).toRealPath();
        Path scratch = Path.of(arguments[2]).toRealPath();
        Path output = Path.of(arguments[3]).toAbsolutePath().normalize();
        String machine = StrictJson.text(arguments[4]);
        if (!Files.isDirectory(repository) || !Files.isDirectory(scratch)
                || !python.equals(repository.resolve("tools/.venv/Scripts/python.exe").toRealPath())
                || output.startsWith(repository) || scratch.startsWith(repository)
                || !Files.isDirectory(output.getParent()) || Files.exists(output)) {
            throw new IllegalArgumentException("actual repository interpreter and fresh external output required");
        }
        PythonStdinCapture.requireCompiledLauncher(GuardianSkillsOriginalCapture.class,
                requiredOrigin("xar.capture.classRoot"), requiredOrigin("xar.capture.helperRoot"));
        byte[] raw = PythonStdinCapture.run(new PythonStdinCapture.Invocation(python, repository,
                SCRIPT, List.of(repository.toString(), scratch.toString(), machine),
                Duration.ofSeconds(60), 98_304)).stdout();
        var golden = StrictJson.parse(raw, 98_304);
        StrictJson.require(StrictJson.text(golden.get("schema")).equals(
                "xar.java.guardian-focus-skills-legacy-golden.v1"), "original guardian schema required");
        StrictJson.require(StrictJson.text(golden.get("machine_id")).equals(machine), "observing machine required");
        StrictJson.require(golden.path("cases").isArray() && golden.path("cases").size() == 13
                && golden.path("validation_cases").isArray()
                && golden.path("validation_cases").size() == 8, "complete original guardian cases required");
        Files.write(output, raw, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
    }

    private static Path requiredOrigin(String property) {
        String value = System.getProperty(property);
        if (value == null || value.isBlank()) { throw new IllegalArgumentException("explicit " + property + " required"); }
        return Path.of(value);
    }

    private static final String SCRIPT = """
import sys,json,pathlib,hashlib,copy,datetime
root=pathlib.Path(sys.argv[1]).resolve();scratch=pathlib.Path(sys.argv[2]).resolve();machine=sys.argv[3]
sys.path.insert(0,str(root/'tools'));sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
from ck3_live_run_id import current_machine_id
if current_machine_id()!=machine:raise RuntimeError('actual machine mismatch')
sources=[root/'ck3_autonomous_player/src/xar_autoplayer/bridge/request_guardian_skill_inputs_private_v1.py',root/'ck3_autonomous_player/src/xar_autoplayer/family_education_needs_12004.py',root/'ck3_autonomous_player/tests/fixtures/family_guardian_p43_completed_projection_v1.json',root/'tools/ck3_live_run_id.py']
original={p:p.read_bytes() for p in sources}
from xar_autoplayer.bridge.request_guardian_skill_inputs_private_v1 import validate_request_guardian_skill_inputs_v1 as validate,project_request_guardian_focus_skills_v1 as project
from xar_autoplayer.family_education_needs_12004 import derive_family_education_needs_12004
fixture=root/'ck3_autonomous_player/tests/fixtures/family_guardian_p43_completed_projection_v1.json'
def context_projection(context):
 out={key:copy.deepcopy(context[key]) for key in ['exact_build','interaction_key','status','snapshot_revision','date_raw','player_character_id']};out['effective_roles']={key:context['effective_roles'][key] for key in ['secondary_actor_id','secondary_recipient_id']}
 if 'request_guardian_skill_inputs_v1' in context:out['request_guardian_skill_inputs_v1']=copy.deepcopy(context['request_guardian_skill_inputs_v1'])
 return out
cases=[]
def add(name,needs,context):
 needs=copy.deepcopy(needs);context=copy.deepcopy(context);profile=context.get('request_guardian_skill_inputs_v1')
 if profile is not None:validate(profile,context)
 cases.append({'name':name,'input':{'schema':'xar.java.request-guardian-focus-skill-input.v1','needs':needs,'context':context},'expected':project(needs,context)})
for row in json.loads(fixture.read_bytes())['rows']:
 relation=row['family_marriage_current_relationship'];derived=derive_family_education_needs_12004(relation['family_generation_education_decision_inputs_v1'],child_relation_materials=relation.get('current_child_relation_materials_v1'),child_education_provider_inputs=relation.get('current_child_education_provider_inputs_v1'),child_education_provider_source=relation.get('current_child_education_provider_inputs_source_v1'))['rows']
 observation=row['family_education_observations'][0];context=observation['default_query']['character_interaction_ordinary_context'];need=next(need for need in derived if need['raw_character_id']==context['recipient_id']);needs={key:copy.deepcopy(need[key]) for key in ['raw_character_id','focus_management','frame']};validate(context['request_guardian_skill_inputs_v1'],context);add('retained-'+row['source_ref'].replace('/','-'),needs,context_projection(context))
base_needs=copy.deepcopy(cases[0]['input']['needs']);base_context=copy.deepcopy(cases[0]['input']['context'])
def focused(needs,key):
 out=copy.deepcopy(needs);out['focus_management']={'available':True,'state':'education_focus_present','current_key':key,'focus_absent':False,'education_focus_present':True,'unavailable_reason':None};return out
martial=copy.deepcopy(base_context);martial['request_guardian_skill_inputs_v1']['total_martial_callback_v1']['value']=12345
add('martial-raw-distinct-from-total',focused(base_needs,'education_martial'),martial)
add('learning-focus-reuses-observed-operand',focused(base_needs,'education_learning'),base_context)
child=copy.deepcopy(base_needs);child['raw_character_id']+=1;add('focus-child-mismatch-learning-retained',child,base_context)
missing=copy.deepcopy(base_needs);missing['frame']=None;add('focus-frame-missing-learning-retained',missing,base_context)
changed=copy.deepcopy(base_needs);changed['frame']['native_revision']+=1;add('focus-frame-mismatch-learning-retained',changed,base_context)
unknown=copy.deepcopy(base_needs);unknown['focus_management']={'available':False,'state':'unknown','current_key':None,'focus_absent':None,'education_focus_present':None,'unavailable_reason':'focus_not_observed'};add('focus-unknown-learning-retained',unknown,base_context)
other=copy.deepcopy(base_needs);other['focus_management']={'available':True,'state':'other_focus_present','current_key':'stewardship_wealth_focus','focus_absent':False,'education_focus_present':False,'unavailable_reason':None};add('noneducation-focus-learning-retained',other,base_context)
no_profile=copy.deepcopy(base_context);no_profile.pop('request_guardian_skill_inputs_v1');add('profile-not-observed',base_needs,no_profile)
learning=copy.deepcopy(base_context);learning['request_guardian_skill_inputs_v1']['skills']['learning']={'available':False,'value':None,'unavailable_reason':'learning_read_unavailable'};add('learning-unavailable-independent-focus',focused(base_needs,'education_diplomacy'),learning)
null_guardian=copy.deepcopy(base_context);profile=null_guardian['request_guardian_skill_inputs_v1'];profile['character_id']=None;profile['binding_status']='known_null';profile['unavailable_reason']='request_guardian_role_known_null';null_guardian['effective_roles']['secondary_actor_id']=None
for value in profile['skills'].values():value.update(available=False,value=None,unavailable_reason='guardian_role_known_null')
if 'total_martial_callback_v1' in profile:profile['total_martial_callback_v1'].update(target_character_id=None,available=False,value=None,unavailable_reason='guardian_role_known_null')
if 'education_traits' in profile:
 for value in profile['education_traits'].values():value.update(available=False,value=None,unavailable_reason='guardian_role_known_null')
if 'education_culture_parameters' in profile:profile['education_culture_parameters'].update(available=False,better_ward_education=None,unavailable_reason='guardian_role_known_null')
add('known-null-guardian-preserved',base_needs,null_guardian)
validation=[]
def check(name,profile,context):
 try:validate(profile,context);valid=True
 except ValueError:valid=False
 validation.append({'name':name,'profile':copy.deepcopy(profile),'context':copy.deepcopy(context),'accepted':valid})
profile=base_context['request_guardian_skill_inputs_v1'];check('actual-valid',profile,base_context)
for name,key,value in [('wrong-build','exact_build','1.20.0.3'),('wrong-interaction','interaction_key','sway_interaction'),('unavailable-context','status','unavailable'),('wrong-revision','snapshot_revision',base_context['snapshot_revision']+1)]:
 context=copy.deepcopy(base_context);context[key]=value;check(name,profile,context)
for name,key in [('wrong-child-role','secondary_recipient_id'),('wrong-guardian-role','secondary_actor_id')]:
 context=copy.deepcopy(base_context);context['effective_roles'][key]+=1;check(name,profile,context)
bad=copy.deepcopy(profile);bad['character_id']=True;check('boolean-profile-id',bad,base_context)
for p,raw_source in original.items():
 if p.read_bytes()!=raw_source:raise RuntimeError('source changed during original capture: '+str(p))
golden={'schema':'xar.java.guardian-focus-skills-legacy-golden.v1','machine_id':machine,'retained_runtime_machine_id':'unknown','captured_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'projection_not_original':True,'method':'unchanged original validator and focus projection; retained P43 inputs plus named synthetic contract changes, no new native run','source_refs':[{'path':str(p.relative_to(root)).replace(chr(92),'/'),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources],'cases':cases,'validation_cases':validation}
raw=(json.dumps(golden,ensure_ascii=False,separators=(',',':'))+chr(10)).encode();assert len(raw)<=98304,('golden finite budget',len(raw))
sys.stdout.buffer.write(raw)

""";
}
