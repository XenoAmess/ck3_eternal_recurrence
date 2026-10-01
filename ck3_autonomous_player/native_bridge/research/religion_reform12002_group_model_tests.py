"""One necessary O2 fixture for actual selected-group sources/cache reader."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
 N=Path(__file__).resolve().parent.parent;S=N.parent.parent;out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
 template=N/'src/religion_reform12002_choices_test.cpp'
 prefix=template.read_text(encoding='utf-8-sig').split('int main(int argc, char **argv)')[0]
 prefix=prefix.replace('Bytes<0x40> doctrine_group{}','Bytes<0x160> doctrine_group{}')
 prefix=prefix.replace('void Wire(const std::filesystem::path &p, const char *name, const r::DraftChoices &v) {\n  std::ofstream(p / name) << r::SerializeCurrentDraftChoices12002(v) << \'\\n\';\n}\n','')
 fixture=out/'group_model_actual_test.cpp'
 fixture.write_text(prefix+'''
#include "xar_bridge/religion_reform12002_group_model.hpp"
void ModelWire(const std::filesystem::path &p,const char *name,const r::DraftGroupModel &v) {
  std::ofstream(p/name)<<r::SerializeCurrentDraftGroupModel12002(v)<<'\\n';
}
int main(int argc,char **argv) {
  const auto p=argc>1?std::filesystem::path(argv[1]):std::filesystem::current_path();
  Fixture q;auto b=Bind(q);
  Bytes<0xB20> def_b{},def_c{},def_d{};Bytes<0x160> group_c{};Bytes<0x48*2> slots{};
  Key(def_b,"doctrine_b");Key(def_c,"doctrine_c");Key(def_d,"doctrine_d");Key(group_c,"group_c");
  Put(def_b,0xB08,q.doctrine_group.data());Put(def_c,0xB08,group_c.data());Put(def_d,0xB08,group_c.data());
  std::array<void *,2> a_source{q.doctrine.data(),def_b.data()},c_source{def_c.data(),def_d.data()};
  Array(q.doctrine_group,0x140,a_source.data(),2);Array(group_c,0x140,c_source.data(),2);
  Put(slots,0x28,q.doctrine.data());Put(slots,0x48+0x28,def_c.data());Array(q.window,0x790,slots.data(),2);
  Put(q.window,0x888,q.window.data());Put(q.window,0x890,q.doctrine_group.data());Put(q.window,0x898,q.doctrine.data());
  Put(q.window,0x8D8,std::int32_t{0});Array(q.window,0x8C0,q.tenet_item.data(),1);
  r::DraftGroupModel v{};
  if(!Check(r::ReadCurrentDraftGroupModel12002(b,80,v)&&v.draft_observed&&v.category_materialized&&
       v.selected_slots.size()==2&&v.selected_slots[1].selected_definition_key=="doctrine_c"&&
       v.selected_slots[0].group_source_definition_keys==std::vector<std::string>{"doctrine_a","doctrine_b"}&&
       v.selected_slots[1].group_source_definition_keys==std::vector<std::string>{"doctrine_c","doctrine_d"}&&
       v.current_group_key=="group_a"&&v.current_category_slot==0&&v.current_doctrine_cache_count==1&&
       v.current_tenet_source_count==1&&v.current_tenet_group_count==1&&v.current_tenet_choices.size()==1&&
       v.current_tenet_choices[0].final_can_pick&&v.current_tenet_gate_complete&&q.arguments_correct&&
       v.founder_character_id==static_cast<std::uint32_t>(Fixture::actor),"actual two-group source caches and Founder Tenet gate"))return 1;
  ModelWire(p,"selected-groups-current-cache.json",v);
  q.native_tenet=false;
  if(!Check(r::ReadCurrentDraftGroupModel12002(b,81,v)&&!v.current_tenet_choices[0].final_can_pick,
       "actual final Tenet false stays false"))return 2;
  ModelWire(p,"blocked-tenet.json",v);
  Put(q.window,0x8D8,std::int32_t{-1});Array(q.window,0x8A8,q.doctrine_item.data(),0);
  Array(q.window,0x8C0,q.tenet_item.data(),0);Array(q.window,0x7A8,q.tenet_group.data(),0);
  if(!Check(r::ReadCurrentDraftGroupModel12002(b,82,v)&&v.selected_slots.size()==2&&!v.category_materialized&&
       !v.current_tenet_gate_complete&&!v.current_group_key&&v.current_tenet_choices.empty(),
       "actual source caches exist before any current group is materialized"))return 3;
  ModelWire(p,"unmaterialized-category.json",v);
  q.visible=false;
  if(!Check(r::ReadCurrentDraftGroupModel12002(b,83,v)&&v.available&&!v.draft_observed&&v.selected_slots.empty(),
       "hidden window is observed no current model"))return 4;
  ModelWire(p,"hidden-window.json",v);
  q.visible=true;Put(q.window,0x8D8,std::int32_t{0});Array(q.window,0x7A8,q.tenet_group.data(),1);q.drift=true;
  if(!Check(!r::ReadCurrentDraftGroupModel12002(b,84,v)&&v.failure=="state_changed"&&v.selected_slots.empty(),
       "actual frame drift publishes no partial group source"))return 5;
  ModelWire(p,"state-changed.json",v);
  q.drift=false;Put(q.state,8,std::int32_t{53175816});Put(q.window,0x888,static_cast<void *>(nullptr));
  if(!Check(!r::ReadCurrentDraftGroupModel12002(b,85,v)&&v.failure=="category_owner_unavailable",
       "inline category belongs to current window"))return 6;
  std::cout<<"GREEN checks="<<cases<<" actual group-source/cache/Tenet gate reader; no CK3\\n";return 0;
}
''',encoding='utf-8')
 sources=[N/'src'/n for n in ('ck3_12002.cpp','ck3_12002_religion_context.cpp','religion_reform12002_window.cpp',
  'religion_doctrine12002_intrinsic.cpp','religion_doctrine12002_choices.cpp','religion_doctrine12002_tenet_rows.cpp',
  'religion_reform12002_choices.cpp','religion_reform12002_group_model.cpp')]+[fixture]
 vswhere=Path(os.environ.get('ProgramFiles(x86)',r'C:\Program Files (x86)'))/'Microsoft Visual Studio/Installer/vswhere.exe'
 installed=subprocess.run([str(vswhere),'-latest','-products','*','-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64','-property','installationPath'],capture_output=True,text=True,check=True).stdout.strip()
 vcvars=Path(installed)/'VC/Auxiliary/Build/vcvars64.bat';temp=out/'tmp';temp.mkdir(exist_ok=True);exe=out/'actual-group-model.exe'
 command=subprocess.list2cmdline(['cl.exe','/nologo','/std:c++20','/EHsc','/O2','/W4','/WX','/utf-8','/I'+str(N/'include'),*map(str,sources),'/Fe:'+str(exe)])
 batch=out/'build.cmd';batch.write_text('@echo off\ncall "'+str(vcvars)+'" >nul\nif errorlevel 1 exit /b %errorlevel%\n'+command+'\nexit /b %errorlevel%\n',encoding='utf-8')
 build=subprocess.run(['cmd.exe','/d','/c',str(batch)],cwd=out,env=dict(os.environ,TEMP=str(temp),TMP=str(temp)),capture_output=True,text=True,encoding='utf-8',errors='replace')
 (out/'build.log').write_text(build.stdout+build.stderr,encoding='utf-8')
 if build.returncode:raise RuntimeError('Compile failed '+str(out/'build.log'))
 run=subprocess.run([str(exe),str(out)],cwd=out,capture_output=True,text=True,encoding='utf-8',errors='replace');(out/'test.log').write_text(run.stdout+run.stderr,encoding='utf-8')
 if run.returncode:raise RuntimeError('Fixture failed '+str(out/'test.log'))
 wires={f.name:json.loads(f.read_text()) for f in out.glob('*.json')}
 observed=wires['selected-groups-current-cache.json'];assert observed['founder_character_id']==observed['played_character_id']
 assert [x['group_key'] for x in observed['selected_slots']]==['group_a','group_c']
 assert not observed['all_group_materialized_choices_complete'] and observed['current_tenet_gate_complete']
 assert not wires['blocked-tenet.json']['current_tenet_choices'][0]['final_can_pick']
 assert not wires['unmaterialized-category.json']['category_materialized'] and len(wires['unmaterialized-category.json']['selected_slots'])==2
 assert not wires['hidden-window.json']['draft_observed'] and not wires['state-changed.json']['available']
 result={'status':'GREEN','readiness':'static-ready','local_ck3_touched':False,'live_verified':False,'compiler':'MSVC /W4 /WX /O2',
  'checks':6,'actual_json_count':len(wires),'stdout':run.stdout.strip(),'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),
  'source_pins':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources},'fixture_template':str(template),
  'template_sha256':hashlib.sha256(template.read_bytes()).hexdigest(),'wire_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.glob('*.json')}}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(run.stdout.strip())
if __name__=='__main__':main()
