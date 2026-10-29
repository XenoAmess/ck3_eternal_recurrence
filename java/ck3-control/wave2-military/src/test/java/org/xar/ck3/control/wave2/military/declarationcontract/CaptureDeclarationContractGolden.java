package org.xar.ck3.control.wave2.military.declarationcontract;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Original pure-producer capture; only the shared storage owner launches the admitted bounded process tree. */
public final class CaptureDeclarationContractGolden {
    private CaptureDeclarationContractGolden() { }
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 3) throw new IllegalArgumentException("repo python new-D-output required");
        Path output = Path.of(args[2]).toAbsolutePath().normalize();
        if (!output.startsWith(Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1").toRealPath()) || Files.exists(output)) {
            throw new IllegalArgumentException("new admitted D output required");
        }
        ProcessBuilder builder = new ProcessBuilder(List.of(args[1], "-B", "-c", SCRIPT, args[0], output.toString()));
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.environment().put("OPENBLAS_NUM_THREADS", "1"); builder.environment().put("OMP_NUM_THREADS", "1");
        Process child = builder.directory(Path.of(args[0]).toFile()).inheritIO().start();
        if (!child.waitFor(100, TimeUnit.SECONDS)) { child.destroyForcibly(); throw new IOException("capture timeout; shared Job owns descendants"); }
        if (child.exitValue() != 0) throw new IOException("original declaration producer exit " + child.exitValue());
        if (!Files.isRegularFile(output) || Files.size(output) == 0 || Files.size(output) > 51_200) throw new IOException("golden exceeded 50KiB");
    }
    private static final String SCRIPT = """
import copy,datetime,hashlib,json,pathlib,sys
repo=pathlib.Path(sys.argv[1]);output=pathlib.Path(sys.argv[2])
sys.path[:0]=[str(repo/'tools'),str(repo/'ck3_autonomous_player/src'),str(repo/'ck3_autonomous_player/tests/unit')]
from ck3_live_run_id import current_machine_id
from xar_autoplayer.bridge.declaration_contract import normalize_declarable_wars,declare_war_step,parse_declare_war_step,is_native_declaration_step
from test_declaration_contract import _declaration
paths=['ck3_autonomous_player/src/xar_autoplayer/bridge/declaration_contract.py','ck3_autonomous_player/tests/unit/test_declaration_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py','ck3_autonomous_player/src/xar_autoplayer/strategy.py','ck3_autonomous_player/src/xar_autoplayer/joint_candidate_ledger.py','ck3_autonomous_player/src/xar_autoplayer/m5_joint_intake.py','ck3_autonomous_player/src/xar_autoplayer/ordinary_holy_war_defender_observation_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/player_ordinary_holy_war_declaration_context_private_observation.py','ck3_autonomous_player/src/xar_autoplayer/bridge/war_declaration_continuity_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py','ck3_autonomous_player/src/xar_autoplayer/construction_formal_consumer.py','ck3_autonomous_player/src/xar_autoplayer/current_first_heir_betrothal_formal_consumer.py','ck3_autonomous_player/src/xar_autoplayer/family_marriage_formal_consumer.py','tools/ck3_live_run_id.py']
before={p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in paths}
rows=[]; literals=[]
def add(name,value):
    raw=json.dumps(value,ensure_ascii=False,separators=(',',':'));value=json.loads(raw);untouched=copy.deepcopy(value)
    try:expected=dict(accepted=True,rows=normalize_declarable_wars(value))
    except ValueError:expected=dict(accepted=False)
    if value!=untouched:raise RuntimeError('original catalogue normalizer mutated input')
    rows.append(dict(id=name,raw_input_json=raw,expected=expected))
base=_declaration()
add('original_factory',[base]);add('known_empty',[]);add('root_null',None);add('root_object',base);add('row_null',[None])
for field,values in [('target_character_id',[0,True,808.0,-1,'808',None]),('casus_belli_index',[0,True,17.0,-1,None]),('configuration_index',[-1,True,0.0,-2,None]),('claimant_character_id',[0,True,-1.0,-2,None]),('casus_belli_key',['',' ',' native ',None,1]),('target_title_ids',[[],[0,91,91],[True],[91.0],[-1],None])]:
    for index,value in enumerate(values):
        row=copy.deepcopy(base);row[field]=value
        if type(row['target_character_id']) is int and type(row['casus_belli_index']) is int and type(row['configuration_index']) is int:row['declaration_id']=str(row['target_character_id'])+'-'+str(row['casus_belli_index'])+'-'+str(row['configuration_index'])
        add(field+'_'+str(index),[row])
for field in list(base):
    row=copy.deepcopy(base);row.pop(field);add('missing_'+field,[row])
extra=dict(base,source='synthetic_source',extra_native_metadata={'extension':[1,2]});add('native_extension_projection',[extra])
add('duplicate_choice',[base,base])
second=dict(base,target_character_id=809,declaration_id='809-17-0',target_title_ids=[9,2,9]);add('stored_order',[second,base])
big=10**80+7;row=dict(base,target_character_id=big,casus_belli_index=big+1,configuration_index=big+2,claimant_character_id=big+3,target_title_ids=[big+4,0,big+4]);row['declaration_id']=str(big)+'-'+str(big+1)+'-'+str(big+2);add('unbounded_python_integer_domain',[row])
for value in ['0808-17-0','808-017-0','808-17-00','808-17--01','808-17-0\\n','٨٠٨-١٧-٠']:
    add('noncanonical_catalogue_id_'+str(len(rows)),[dict(base,declaration_id=value)])
values=['808-17-0','808-17--1','0808-017-00','0-0-0','0-0--1','٨٠٨-١٧-٠','𝟠𝟘𝟠-𝟙𝟟-𝟘','808-17--١','808-17--2','808-17-0\\n','','808-17','808_17_0','²-17-0',None,True,123,[],{}]
for index,value in enumerate(values):
    try:built=dict(accepted=True,step=declare_war_step(value))
    except ValueError:built=dict(accepted=False)
    step='declare-war-'+value if isinstance(value,str) else value
    literals.append(dict(id='literal_'+str(index),raw_id_json=json.dumps(value,ensure_ascii=False),raw_step_json=json.dumps(step,ensure_ascii=False),expected_build=built,expected_parse=parse_declare_war_step(step),expected_native=is_native_declaration_step(step)))
for step in ['query-declarable-wars','declare-war-808-17-0','query-declarable-wars-extra',None,False]:
    literals.append(dict(id='native_'+str(len(literals)),raw_step_json=json.dumps(step),expected_parse=parse_declare_war_step(step),expected_native=is_native_declaration_step(step)))
refs=[]
for p in paths:
    raw=(repo/p).read_bytes();digest=hashlib.sha256(raw).hexdigest()
    if digest!=before[p]:raise RuntimeError('source changed during capture: '+p)
    refs.append(dict(path=p,bytes=len(raw),sha256=digest))
data=dict(schema='xar.declarationcontract.original-producer-golden/v1',machine_id=current_machine_id(),observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_refs=refs,input_refs=[],scope='projection_not_original; unchanged real catalogue normalizer, literal step builder/parser and native-step classifier; synthetic variations of existing fixture; no live discovery/action/continuity qualification',catalogues=rows,literals=literals)
raw=(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode()
if len(raw)>51200:raise RuntimeError('declaration golden exceeds 50KiB')
with output.open('xb') as handle:handle.write(raw)
print(json.dumps(dict(machine_id=data['machine_id'],observed_at_utc=data['observed_at_utc'],catalogues=len(rows),literals=len(literals),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())))
""";
}
