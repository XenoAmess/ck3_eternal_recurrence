"""Compile one inert fixture using exact production GUI binder/callsite spans.

Only environment build admission is checked. No Win32 callback, GUI provider,
process, SDK, runtime DLL or game is invoked. Module base zero keeps callback
address construction outside this fixture's execution domain.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,subprocess,sys
from datetime import datetime,timezone
from run_confucian_semantic_identity_fixture import block

def ref(path):
    data=path.read_bytes();return {'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source-root','original-bridge','output','vcvars'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args();root=Path(args.source_root).resolve();out=Path(args.output).resolve();out.mkdir()
    native=root/'ck3_autonomous_player/native_bridge'
    refs=[]
    def read(relative):
        p=native/relative;refs.append(ref(p));return p.read_text('utf-8-sig')
    current=read('src/bridge.cpp');original_path=Path(args.original_bridge).resolve();original=original_path.read_text('utf-8-sig');refs.append(ref(original_path))
    old_pattern=r'BindZhongguoScoreboardNativeEnvironmentV1\(base,\s*true,\s*LydPrivateGuiRevision\(game\.descriptor\(\)\)\)'
    new_pattern=old_pattern[:-2]+r', game\.descriptor\(\)\.executable_sha256\)'
    old=list(re.finditer(old_pattern,original));new=list(re.finditer(new_pattern,current))
    assert len(old)==len(new)==5,(len(old),len(new))
    restored=re.sub(new_pattern,lambda m:m.group().replace(', game.descriptor().executable_sha256',''),current)
    assert restored==original,'bridge change extends beyond the five exact native binder arguments'
    binder=block(read('src/zhongguo_scoreboard_state_v1.cpp'),'ZhongguoScoreboardNativeEnvironmentV1 BindZhongguoScoreboardNativeEnvironmentV1(')
    descriptor=block(read('include/xar_bridge/game_adapter.hpp'),'struct AdapterDescriptor')
    exact3=block(read('src/ck3_12003_abi_profile.cpp'),'bool IsCk3_12003Descriptor(')
    exact4=block(read('src/ck3_12004_abi_profile.cpp'),'bool IsCk3_12004Descriptor(')
    select=block(current,'xar::ck3_11906::GuiAbiRevisionV1 LydPrivateGuiRevision(')
    guard=block(current,'bool IsLydPrivateBuild(')
    text='#include <cstdint>\n#include <cstdlib>\n#include <string_view>\n#include <span>\n#include <array>\n#include <iostream>\n'
    for version in ('12003','12004'):
        h=read('include/xar_bridge/ck3_'+version+'.hpp')
        constants=[re.search(r'inline constexpr char '+name+r'\[\]\s*=\s*"[^"]*";',h).group() for name in ('kGameVersion','kAdapterId','kExecutableSha256')]
        text+='namespace xar::ck3_'+version+'{'+''.join(constants)+'}\n'
    text+='namespace xar::game{'+descriptor+';\n'+exact3+'\n'+exact4+'}\n'
    text+='''namespace xar::ck3_11906 {
enum class GuiAbiRevisionV1 { legacy11906,crozier12003,crozier12004 };
struct Variables { std::uintptr_t module_base{}; bool exact_build_admitted{}; };
using NativeZhongguoFindTopLevelWidgetV1=void(*)();
struct ZhongguoScoreboardNativeEnvironmentV1 {
 Variables variables{};std::uintptr_t module_base{};GuiAbiRevisionV1 gui_abi_revision{};
 std::string_view executable_sha256{};bool exact_build_admitted{};
 void **gui_global_slot{};NativeZhongguoFindTopLevelWidgetV1 find_top_level_widget{};
};
Variables BindZhongguoCaseNativeEnvironmentV1(std::uintptr_t base,bool admitted){return {base,admitted};}
std::uintptr_t GuiGlobalSlotRvaV1(GuiAbiRevisionV1){std::abort();}
std::uintptr_t GuiFindTopLevelWidgetRvaV1(GuiAbiRevisionV1){std::abort();}
ZhongguoScoreboardNativeEnvironmentV1 BindZhongguoScoreboardNativeEnvironmentV1(std::uintptr_t,bool,GuiAbiRevisionV1,std::string_view={}) noexcept;
'''+binder+'\n}\n'+select+'\n'+guard+'''
struct Game { xar::game::AdapterDescriptor d; const xar::game::AdapterDescriptor &descriptor() const {return d;} };
'''
    for label,rows in [('original',old),('fixed',new)]:
        for i,row in enumerate(rows):
            text+='xar::ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 '+label+str(i)+'(Game game){std::uintptr_t base=0;if(!IsLydPrivateBuild(game.descriptor()))return {};return xar::ck3_11906::'+row.group()+';}\n'
    text+='''int main(){using namespace xar;using namespace xar::game;
constexpr std::array<std::string_view,0> caps{};
Game three{{ck3_12003::kAdapterId,ck3_12003::kGameVersion,ck3_12003::kExecutableSha256,"",caps}};
Game four{{ck3_12004::kAdapterId,ck3_12004::kGameVersion,ck3_12004::kExecutableSha256,"",caps}};
auto mixed=four;mixed.d.executable_sha256=ck3_12003::kExecutableSha256;
'''
    for i in range(5):
        text+=f'if(!original{i}(three).exact_build_admitted||!fixed{i}(three).exact_build_admitted||original{i}(four).exact_build_admitted||!fixed{i}(four).exact_build_admitted||fixed{i}(mixed).exact_build_admitted)return 2;\n'
    text+='''using namespace xar::ck3_11906;
if(BindZhongguoScoreboardNativeEnvironmentV1(0,true,GuiAbiRevisionV1::crozier12004).exact_build_admitted ||
 BindZhongguoScoreboardNativeEnvironmentV1(0,true,GuiAbiRevisionV1::crozier12004,ck3_12003::kExecutableSha256).exact_build_admitted ||
 BindZhongguoScoreboardNativeEnvironmentV1(0,false,GuiAbiRevisionV1::crozier12004,ck3_12004::kExecutableSha256).exact_build_admitted)return 3;
std::cout<<"{\\"exact_callsite_checks\\":25,\\"empty_wrong_hash_false_admission_checks\\":3,\\"GUI_callbacks_executed\\":false}\\n";return 0;}
'''
    cpp=out/'fixture.cpp';cpp.write_text(text,encoding='utf-8',newline='\n')
    command=out/'compiler_environment.cmd';command.write_text('@echo off\ncall "'+str(Path(args.vcvars).resolve())+'" >nul\nif errorlevel 1 exit /b 1\nset PATH\nset INCLUDE\nset LIB\n',encoding='utf-8')
    env_run=subprocess.run(['cmd.exe','/d','/c',str(command)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    assert env_run.returncode==0
    env=os.environ.copy()
    for line in env_run.stdout.decode('utf-8','replace').splitlines():
        if '=' in line:
            k,v=line.split('=',1)
            if k.upper() in ('PATH','INCLUDE','LIB','LIBPATH'):env[k.upper()]=v
    compiler=shutil.which('cl.exe',path=env['PATH']);assert compiler
    executable=out/'lyd_gui_environment_identity_fixture.exe';records=[]
    for label,argv in [('compile',[compiler,'/nologo','/std:c++20','/EHsc','/W4','/WX','/O2','/MD',str(cpp),'/Fe:'+str(executable),'/Fo:'+str(out/'fixture.obj'),'/link','/INCREMENTAL:NO']),('fixture',[str(executable)])]:
        start=datetime.now(timezone.utc).isoformat();run=subprocess.run(argv,cwd=out,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (out/(label+'.stdout.raw')).write_bytes(run.stdout);(out/(label+'.stderr.raw')).write_bytes(run.stderr)
        records.append({'argv':argv,'started_at_utc':start,'ended_at_utc':datetime.now(timezone.utc).isoformat(),'exit_code':run.returncode,'stdout':ref(out/(label+'.stdout.raw')),'stderr':ref(out/(label+'.stderr.raw'))})
        print(json.dumps({'phase':label,'exit_code':run.returncode}),flush=True)
        if run.returncode:raise SystemExit(run.returncode)
    result={'schema':'lyd.r22.isolated-production-gui-environment-callsite-fixture.v1','status':'OFFLINE_ADMISSION_FIXTURE_PASSED','source_refs':refs,'binder_span_sha256':hashlib.sha256(binder.encode()).hexdigest(),'callsites':{'original':[r.group() for r in old],'fixed':[r.group() for r in new]},'result':json.loads((out/'fixture.stdout.raw').read_bytes()),'records':records,'cpp':ref(cpp),'executable':ref(executable),'runtime_DLL_or_SDK_or_process_or_game_used':False,'GUI_provider_runtime_credit':None}
    (out/'RESULT.actual.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(ref(out/'RESULT.actual.json')))

if __name__=='__main__':main()
