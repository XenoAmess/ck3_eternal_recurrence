"""One O2 actual all-slot Doctrine source reader/serializer fixture; no CK3."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess
BODY=r'''
#include "xar_bridge/religion_reform12002_fullchoices.hpp"
std::array<const void *,10> definitions{};
bool SourceTrigger(const void *trigger,const void *scope) {
  ++f->trigger_calls;f->arguments_correct&=scope==f->window.data()+0xD0;
  for(const auto *definition:definitions) {
    const auto *base=static_cast<const std::byte *>(definition);
    if(trigger==base+0x1B8||trigger==base+0xE8) {
      bool result{};std::memcpy(&result,trigger,sizeof(result));return result;
    }
  }f->arguments_correct=false;return false;
}
bool SourceKnowledge(void *actor,const void *definition) {
  ++f->knows_calls;f->arguments_correct&=actor==f->character.data();
  for(const auto *candidate:definitions)if(candidate==definition) {
    bool result{};std::memcpy(&result,static_cast<const std::byte *>(definition)+0xB10,sizeof(result));return result;
  }f->arguments_correct=false;return false;
}
void FullWire(const std::filesystem::path &p,const char *name,const r::DraftFullDoctrineChoices &v) {
  std::ofstream(p/name)<<r::SerializeCurrentDraftFullDoctrineChoices12002(v)<<'\n';
}
int main(int argc,char **argv) {
  const auto p=argc>1?std::filesystem::path(argv[1]):std::filesystem::current_path();
  Fixture q;auto b=Bind(q);b.evaluate_trigger=&SourceTrigger;b.knows_doctrine=&SourceKnowledge;
  std::array<Bytes<0xB20>,10> defs{};std::array<Bytes<0x160>,3> groups{};Bytes<0x48*4> selected{};
  const std::array<const char *,10> keys{"doctrine_a","doctrine_b","doctrine_c","doctrine_d","doctrine_e","doctrine_f","doctrine_g","doctrine_h","doctrine_i","doctrine_j"};
  Key(groups[0],"group_a");Key(groups[1],"group_g");Key(groups[2],"group_zero");
  for(std::size_t i=0;i<defs.size();++i) {
    auto &def=defs[i];Key(def,keys[i]);definitions[i]=def.data();
    Put(def,0xB08,groups[i<6?0:(i<9?1:2)].data());
    Put(def,0x1B8,i!=2);Put(def,0xE8,i!=3);Put(def,0xB10,i!=4&&i!=7&&i!=8);
  }
  std::array<void *,6> source_a{};for(std::size_t i=0;i<source_a.size();++i)source_a[i]=defs[i].data();
  std::array<void *,3> source_g{defs[6].data(),defs[7].data(),defs[8].data()};
  Array(groups[0],0x140,source_a.data(),6);Array(groups[1],0x140,source_g.data(),3);
  Array(groups[2],0x140,static_cast<void *>(nullptr),0);
  Put(selected,0x28,defs[0].data());Put(selected,0x48+0x28,defs[1].data());
  Put(selected,0x48*2+0x28,defs[6].data());Put(selected,0x48*3+0x28,defs[9].data());
  Array(q.window,0x790,selected.data(),4);
  Put(q.window,0x8D8,std::int32_t{-1});Array(q.window,0x8A8,static_cast<void *>(nullptr),0);
  Array(q.window,0x7A8,static_cast<void *>(nullptr),0);
  r::DraftFullDoctrineChoices v{};
  if(!Check(r::ReadCurrentDraftFullDoctrineChoices12002(b,90,v)&&v.draft_observed&&v.doctrine_gates_complete&&
      v.slots.size()==4&&v.slots[0].sources.size()==6&&v.slots[1].sources.size()==6&&v.slots[2].sources.size()==3&&
      v.slots[3].sources.empty()&&v.slots[3].group_key=="group_zero"&&
      v.slots[0].sources[0].currently_selected&&v.slots[0].sources[0].final_selectable&&
      v.slots[0].sources[1].duplicate_excluded&&!v.slots[0].sources[1].passed_shown&&!v.slots[0].sources[1].final_selectable&&
      v.slots[1].sources[0].duplicate_excluded&&v.slots[1].sources[1].currently_selected&&v.slots[1].sources[1].final_selectable&&
      v.slots[0].sources[2].passed_shown==false&&v.slots[0].sources[2].native_can_pick==false&&
      v.slots[0].sources[3].passed_shown==true&&v.slots[0].sources[3].native_can_pick==false&&
      v.slots[0].sources[4].native_knows_doctrine==false&&v.slots[0].sources[4].native_has_prophet==false&&
      !v.slots[0].sources[4].final_selectable&&v.slots[0].sources[5].final_selectable&&
      v.slots[2].sources[0].final_selectable&&!v.slots[2].sources[1].final_selectable&&
      q.trigger_calls==24&&q.knows_calls==9&&q.perk_calls==4&&q.tenet_calls==0&&q.arguments_correct,
      "four actual slots / fifteen sources before popup materialization; duplicate shown raw and knowledge gates"))return 1;
  FullWire(p,"actual-four-slots.json",v);
  q.prophet=true;
  if(!Check(r::ReadCurrentDraftFullDoctrineChoices12002(b,91,v)&&v.slots[0].sources[4].final_selectable&&
      v.slots[2].sources[1].native_has_prophet==true&&v.slots[2].sources[1].final_selectable&&
      v.slots[0].sources[1].duplicate_excluded&&!v.slots[0].sources[1].final_selectable&&
      v.slots[0].sources[2].native_can_pick==false&&!v.slots[0].sources[2].final_selectable&&q.arguments_correct,
      "prophet changes only knowledge branch; native exclusions remain"))return 2;
  FullWire(p,"prophet-alternative.json",v);
  Array(q.window,0x790,selected.data()+0x48*3,1);
  if(!Check(r::ReadCurrentDraftFullDoctrineChoices12002(b,92,v)&&v.draft_observed&&v.doctrine_gates_complete&&
      v.slots.size()==1&&v.slots[0].selected_doctrine_key=="doctrine_j"&&v.slots[0].sources.empty(),
      "actual selected slot with zero native sources"))return 3;
  FullWire(p,"zero-source-slot.json",v);
  Array(q.window,0x790,static_cast<void *>(nullptr),0);
  if(!Check(r::ReadCurrentDraftFullDoctrineChoices12002(b,93,v)&&v.draft_observed&&v.doctrine_gates_complete&&v.slots.empty(),
      "observed current draft zero slots"))return 4;
  FullWire(p,"zero-slots.json",v);
  q.visible=false;const auto calls=q.trigger_calls;
  if(!Check(r::ReadCurrentDraftFullDoctrineChoices12002(b,94,v)&&v.available&&!v.draft_observed&&
      !v.doctrine_gates_complete&&v.slots.empty()&&q.trigger_calls==calls,
      "hidden draft absence is distinct from observed empty"))return 5;
  FullWire(p,"hidden-draft.json",v);
  std::cout<<"GREEN checks="<<cases<<" actual four-slot fifteen-source Doctrine gates / five actual JSON; no CK3\n";return 0;
}
'''
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
 N=Path(__file__).resolve().parent.parent;out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
 template=N/'src/religion_reform12002_choices_test.cpp'
 prefix=template.read_text(encoding='utf-8-sig').split('int main(int argc, char **argv)')[0]
 prefix=prefix.replace('Bytes<0x40> doctrine_group{}','Bytes<0x160> doctrine_group{}')
 prefix=prefix.replace('void Wire(const std::filesystem::path &p, const char *name, const r::DraftChoices &v) {\n  std::ofstream(p / name) << r::SerializeCurrentDraftChoices12002(v) << \'\\n\';\n}\n','')
 fixture=out/'actual_full_doctrine_choices.cpp';fixture.write_text(prefix+BODY,encoding='utf-8')
 sources=[N/'src'/name for name in ('ck3_12002.cpp','religion_reform12002_window.cpp','religion_doctrine12002_intrinsic.cpp','religion_reform12002_fullchoices.cpp')]+[fixture]
 vswhere=Path(os.environ.get('ProgramFiles(x86)',r'C:\Program Files (x86)'))/'Microsoft Visual Studio/Installer/vswhere.exe'
 installed=subprocess.run([str(vswhere),'-latest','-products','*','-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64','-property','installationPath'],capture_output=True,text=True,check=True).stdout.strip()
 vcvars=Path(installed)/'VC/Auxiliary/Build/vcvars64.bat';temp=out/'tmp';temp.mkdir(exist_ok=True);exe=out/'actual-full-doctrine-choices.exe'
 command=subprocess.list2cmdline(['cl.exe','/nologo','/std:c++20','/EHsc','/O2','/W4','/WX','/utf-8','/I'+str(N/'include'),*map(str,sources),'/Fe:'+str(exe)])
 batch=out/'build.cmd';batch.write_text('@echo off\ncall "'+str(vcvars)+'" >nul\nif errorlevel 1 exit /b %errorlevel%\n'+command+'\nexit /b %errorlevel%\n',encoding='utf-8')
 build=subprocess.run(['cmd.exe','/d','/c',str(batch)],cwd=out,env=dict(os.environ,TEMP=str(temp),TMP=str(temp)),capture_output=True,text=True,encoding='utf-8',errors='replace')
 (out/'build.log').write_text(build.stdout+build.stderr,encoding='utf-8')
 if build.returncode:raise RuntimeError('Compile failed '+str(out/'build.log'))
 run=subprocess.run([str(exe),str(out)],cwd=out,capture_output=True,text=True,encoding='utf-8',errors='replace')
 (out/'test.log').write_text(run.stdout+run.stderr,encoding='utf-8')
 if run.returncode:raise RuntimeError('Fixture failed '+str(out/'test.log'))
 wires={f.name:json.loads(f.read_text()) for f in out.glob('*.json')}
 observed=wires['actual-four-slots.json'];assert observed['doctrine_gates_complete'] and len(observed['slots'])==4
 assert sum(len(slot['sources']) for slot in observed['slots'])==15
 assert sum(row['final_selectable'] for slot in observed['slots'] for row in slot['sources'])==5
 assert sum(row['final_selectable'] for slot in wires['prophet-alternative.json']['slots'] for row in slot['sources'])==9
 assert wires['zero-source-slot.json']['draft_observed'] and len(wires['zero-source-slot.json']['slots'])==1
 assert wires['zero-slots.json']['draft_observed'] and not wires['zero-slots.json']['slots']
 assert not wires['hidden-draft.json']['draft_observed'] and not wires['hidden-draft.json']['doctrine_gates_complete']
 result={'status':'GREEN','readiness':'static-ready','local_ck3_touched':False,'live_verified':False,'compiler':'MSVC /W4 /WX /O2','checks':5,'actual_json_count':len(wires),'stdout':run.stdout.strip(),'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'source_pins':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources},'fixture_template':str(template),'template_sha256':hashlib.sha256(template.read_bytes()).hexdigest(),'wire_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.glob('*.json')}}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(run.stdout.strip())
if __name__=='__main__':main()
