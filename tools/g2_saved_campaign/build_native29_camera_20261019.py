"""One separately admitted Native29 camera build; never contacts Game or desktop."""
from __future__ import annotations
import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
sys.dont_write_bytecode = True
import build_native26_performance_20261019 as b
from close_native26_performance_20261019 import exports

REPO = Path(__file__).resolve().parents[2]
PLAN = REPO/'docs/ck3-native-ai/evidence/native29-camera-build-plan-2026-10-19.json'
PLAN_SHA = '6bd541930f4247e847bd992ff104638bc1e6d88c1fa5e5456c35a462f1364d72'


def require(value, message):
    if not value:
        raise ValueError(message)


def fixture_source(cpp, statuses):
    begin = cpp.index('struct GameWindowSearch {')
    end = cpp.index('} // namespace', begin)
    body = cpp[begin:end]
    enum_asserts = '\n'.join('static_assert(static_cast<std::uint32_t>(Status::'+name+') == '+str(value)+');' for name, value in statuses.items())
    return r'''
#include "xar_bridge/camera_presentation_v1.hpp"
#include "xar_bridge/realm_camera_geometry_v1.hpp"
#include <array>
#include <climits>
#include <cwchar>
#include <string_view>
struct FakeWindow { HWND hwnd{}; DWORD pid=111; const wchar_t *title=L"Crusader Kings III"; bool valid=true; };
static std::array<FakeWindow, 3> fake{};
static std::size_t fake_count=0;
static bool enum_ok=true;
static FakeWindow *Find(HWND hwnd) { for (std::size_t i=0;i<fake_count;++i) if(fake[i].hwnd==hwnd) return &fake[i]; return nullptr; }
static BOOL WINAPI MockIsWindow(HWND hwnd) { const auto *p=Find(hwnd); return p && p->valid; }
static DWORD WINAPI MockGetWindowThreadProcessId(HWND hwnd, LPDWORD pid) { const auto *p=Find(hwnd); if(!p) return 0; *pid=p->pid; return 7; }
static int WINAPI MockGetWindowTextW(HWND hwnd, LPWSTR out, int count) { const auto *p=Find(hwnd); if(!p || count<=0) return 0; const auto n=std::wcslen(p->title); if(n>=static_cast<std::size_t>(count)) return 0; wcscpy_s(out,static_cast<std::size_t>(count),p->title); return static_cast<int>(n); }
static DWORD WINAPI MockGetCurrentProcessId() { return 111; }
static BOOL WINAPI MockEnumWindows(WNDENUMPROC callback, LPARAM context) { if(!enum_ok) return FALSE; for(std::size_t i=0;i<fake_count;++i) if(!callback(fake[i].hwnd,context)) return FALSE; return TRUE; }
#define IsWindow MockIsWindow
#define GetWindowThreadProcessId MockGetWindowThreadProcessId
#define GetWindowTextW MockGetWindowTextW
#define GetCurrentProcessId MockGetCurrentProcessId
#define EnumWindows MockEnumWindows
namespace xar::presentation {
''' + body + r'''
}
#undef IsWindow
#undef GetWindowThreadProcessId
#undef GetWindowTextW
#undef GetCurrentProcessId
#undef EnumWindows
using namespace xar::presentation;
static_assert(sizeof(Mode)==4 && sizeof(Status)==4);
static_assert(sizeof(Request)==168 && sizeof(Result)==65640 && sizeof(Shared)==65832);
static_assert(offsetof(Shared,request)==24 && offsetof(Shared,result)==192);
static_assert(offsetof(Result,county_ids)==104 && offsetof(Result,target)==48 && offsetof(Result,current)==72);
''' + enum_asserts + r'''
#define CHECK(condition) do { if(!(condition)) return -__LINE__; ++checks; } while(0)
extern "C" __declspec(dllexport) int RunNative29CameraFixture() {
  int checks=0;
  const auto h1=reinterpret_cast<HWND>(std::uintptr_t{1});
  const auto h2=reinterpret_cast<HWND>(std::uintptr_t{2});
  const auto h3=reinterpret_cast<HWND>(std::uintptr_t{3});
  fake={FakeWindow{h1},FakeWindow{h2},FakeWindow{h3}}; fake_count=1; enum_ok=true;
  CHECK(IsUniqueGameWindow(h1));
  CHECK(!IsUniqueGameWindow(h2));
  fake_count=2; CHECK(!IsUniqueGameWindow(h1));
  fake[1].pid=222; CHECK(IsUniqueGameWindow(h1));
  fake[1].pid=111; fake[1].title=L"Other"; CHECK(IsUniqueGameWindow(h1));
  fake[0].valid=false; CHECK(!IsUniqueGameWindow(h1)); fake[0].valid=true;
  fake[0].title=L"Other"; CHECK(!IsUniqueGameWindow(h1)); fake[0].title=L"Crusader Kings III";
  enum_ok=false; CHECK(!IsUniqueGameWindow(h1)); enum_ok=true;
  fake_count=0; CHECK(!IsUniqueGameWindow(h1));
  const std::array<std::int32_t,8> thresholds{1000,800,600,400,300,200,100,-1};
  const std::array<std::array<std::int32_t,2>,18> rows{{
    {0,7},{1,7},{50,7},{100,7},{101,6},{200,6},{201,5},{300,5},{301,4},
    {400,4},{401,3},{600,3},{601,2},{800,2},{801,1},{1000,1},{1001,0},{100000,0}}};
  std::size_t bucket=0;
  for(const auto &row:rows) CHECK(NativeBucket(row[0],thresholds,bucket) && bucket==static_cast<std::size_t>(row[1]));
  CHECK(!NativeBucket(-1,thresholds,bucket));
  CHECK(!NativeBucket(0,std::array<std::int32_t,3>{100,200,-1},bucket));
  CHECK(!NativeBucket(0,std::array<std::int32_t,2>{100,-2},bucket));
  CHECK(!NativeBucket(0,{},bucket));
  CHECK(NativeBucket(0,std::array<std::int32_t,1>{-1},bucket) && bucket==0);
  Bounds aggregate{}; bool initialized=false;
  CHECK(UnionBounds(aggregate,{10,20,100,200},initialized));
  CHECK(UnionBounds(aggregate,{10000,-200,11000,10},initialized));
  CHECK((aggregate==Bounds{10,-200,11000,200}));
  CHECK(!UnionBounds(aggregate,{3,4,2,5},initialized));
  std::int32_t extent=-1;
  CHECK(ViewportExtent({1898,2444,1898,2444},2560,1440,.15F,extent) && extent==0);
  CHECK(ViewportExtent({0,0,1000,500},1920,1080,0,extent) && extent==1000);
  CHECK(ViewportExtent({0,0,1000,500},600,1200,0,extent) && extent==2000);
  CHECK(ViewportExtent({0,0,1000,500},1920,1080,.15F,extent) && extent>1000);
  CHECK(!ViewportExtent({INT_MIN,0,INT_MAX,10},1920,1080,.15F,extent));
  CHECK(!ViewportExtent({0,0,1,1},10,10,.15F,extent));
  CHECK(!ViewportExtent({0,0,1,1},1920,1080,.45F,extent));
  return checks;
}
'''


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--admission', type=Path, required=True)
    args = parser.parse_args()
    require(b.sha(PLAN)==PLAN_SHA and PLAN.stat().st_size==14716, 'plan pin mismatch')
    plan, admission = b.read(PLAN), b.read(args.admission)
    machine = subprocess.check_output([sys.executable,'-B',str(REPO/'tools/ck3_live_run_id.py'),'machine'],text=True).strip()
    require(machine==plan['machine_id']==admission['machine_id'], 'machine mismatch')
    require(admission['status']=='ADMITTED', 'no child admission')
    root = Path(plan['proposed_root'])
    approved = admission.get('approved_root', admission.get('root', ''))
    require(b.norm(root)==b.norm(approved) and not root.exists(), 'fresh exact root required')
    hard = admission.get('hard_limit_bytes', admission.get('hard_total_child_peak_bytes'))
    require(hard==384*b.MIB, 'wrong hard ceiling')
    deadline = admission.get('review_at_utc', admission.get('expires_at_utc'))
    require(deadline and datetime.now(timezone.utc)<datetime.fromisoformat(deadline), 'expired admission')
    require(admission.get('source_plan',{}).get('sha256')==PLAN_SHA, 'admission source plan mismatch')
    require(admission.get('attempt_limit',1)==admission.get('workers',1)==1,'one worker/attempt only')
    root.mkdir(); (root/'build').mkdir(); (root/'source/include/xar_bridge').mkdir(parents=True); (root/'source/src').mkdir()
    (root/'producer-used.py').write_bytes(Path(__file__).read_bytes())
    (root/'INPUT-PLAN.json').write_bytes(PLAN.read_bytes()); (root/'ADMISSION.json').write_bytes(args.admission.read_bytes())
    phase, windows, refs, peaks = 'prepare', [], {}, {'logical_bytes':0,'allocated_bytes':0}
    class StandardInfo(ctypes.Structure):
        _fields_=[('AllocationSize',ctypes.c_longlong),('EndOfFile',ctypes.c_longlong),('NumberOfLinks',ctypes.c_ulong),('DeletePending',ctypes.c_ubyte),('Directory',ctypes.c_ubyte)]
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_void_p,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_void_p]; kernel.CreateFileW.restype=ctypes.c_void_p
    kernel.GetFileInformationByHandleEx.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p,ctypes.c_ulong]; kernel.GetFileInformationByHandleEx.restype=ctypes.c_int
    kernel.CloseHandle.argtypes=[ctypes.c_void_p]; kernel.CloseHandle.restype=ctypes.c_int

    def usage():
        logical=allocated=0
        for path in root.rglob('*'):
            if not path.is_file(): continue
            logical+=path.stat().st_size
            handle=kernel.CreateFileW(str(path),0,7,None,3,0,None)
            require(handle not in (None,ctypes.c_void_p(-1).value),'allocation stat open failed')
            info=StandardInfo()
            try: require(kernel.GetFileInformationByHandleEx(handle,1,ctypes.byref(info),ctypes.sizeof(info)),'allocation stat failed')
            finally: kernel.CloseHandle(handle)
            allocated+=info.AllocationSize
        peaks['logical_bytes']=max(peaks['logical_bytes'],logical); peaks['allocated_bytes']=max(peaks['allocated_bytes'],allocated)
        require(max(logical,allocated)<=hard,'child hard ceiling exceeded; retain failed attempt')
        require(not any(p.suffix.lower() in ('.pdb','.ilk','.exe') for p in root.rglob('*')),'unexpected debug/EXE output')
        return {'logical_bytes':logical,'allocated_bytes':allocated}

    def ref(pin):
        actual=b.pin(pin['path'])
        require(actual['sha256']==pin['sha256'] and ('bytes' not in pin or actual['bytes']==pin['bytes']),'retained pin changed: '+pin['path'])
        stat=Path(pin['path']).stat(); refs[b.norm(pin['path'])]=(stat.st_size,stat.st_mtime_ns)
        return actual

    def unchanged():
        for path,expected in refs.items():
            stat=Path(path).stat(); require((stat.st_size,stat.st_mtime_ns)==expected,'retained input changed: '+path)

    def run(argv,cwd,env,log,scratch=0,timeout=600):
        size=usage(); require(max(size.values())+scratch<=hard,'insufficient admitted next-phase scratch')
        unchanged(); started,tick=b.now(),time.perf_counter()
        with Path(log).open('xb') as stream:
            process=subprocess.Popen(list(map(str,argv)),cwd=cwd,env=env,stdout=stream,stderr=subprocess.STDOUT,creationflags=b.LOW_FLAGS)
            try:
                while process.poll() is None:
                    usage()
                    if time.perf_counter()-tick>timeout: raise TimeoutError('tool timeout; no automatic retry')
                    time.sleep(.1)
                code=process.returncode
            except BaseException:
                process.kill(); process.wait(timeout=30); raise
        result={'argv':list(map(str,argv)),'started_at_utc':started,'ended_at_utc':b.now(),'wall_seconds':time.perf_counter()-tick,'exit_code':code,'priority':'BELOW_NORMAL','log':b.pin(log),'child_usage':usage()}
        windows.append({'phase':phase,**{k:result[k] for k in ('started_at_utc','ended_at_utc','wall_seconds','exit_code')}})
        b.write(Path(log).with_suffix('.result.json'),result)
        require(code==0,'tool failed; single attempt retained: '+str(log))
        return result

    def env_at(env,path):
        path.mkdir(parents=True,exist_ok=True); child=env.copy(); child['TEMP']=child['TMP']=str(path); return child

    def argv_for(original,source,obj,deps,overlay):
        sources=[x for x in original if x.lower().endswith('.cpp')]; require(len(sources)==1,'source ambiguity')
        result=[original[0],'/I'+str(overlay)]
        for i,value in enumerate(original[1:],1):
            if value==sources[0]: result.append(str(source))
            elif value.lower().startswith('/fo'): result.append('/Fo'+str(obj))
            elif value.lower().startswith('/fd'): result.append('/Fd'+str(obj.with_suffix('.pdb')))
            elif original[i-1].lower()=='/sourcedependencies': result.append(str(deps))
            else: result.append(value)
        require(not any(x.lower() in ('/zi','/z7','/debug') for x in result),'debug prohibited')
        return result

    try:
        for pin in plan['source_pins'].values(): ref(pin)
        ref(plan['baseline_closed'])
        for pin in plan['baseline_pins'].values(): ref(pin)
        ref(plan['original_compile_recipe']); ref(plan['original_dependencies'])
        ref(plan['build_scope']['archive'])
        baseline=Path(plan['baseline_root'])
        prepared=b.read(baseline/'PREPARED.json')
        old_direct={b.norm(p['path']):p for p in prepared['direct_inputs']}
        for p in prepared['baseline_exact_pins'].values(): old_direct[b.norm(p['path'])]=p
        old_direct.update({b.norm(p['path']):p for p in plan['baseline_pins'].values()})
        original_rsp=baseline/'build/native27-link.rsp'
        direct=[v for v in b.tokens(original_rsp) if v.lower().endswith('.obj')]
        require(len(direct)==356,'direct count changed')
        directpins=[ref(old_direct[b.norm(value)]) for value in direct]
        recipe=b.read(plan['original_compile_recipe']['path']); original_deps=b.read(plan['original_dependencies']['path'])['Data']['Includes']
        headerpins=[ref(pin) for pin in recipe['actual_include_pins']]
        require(len(headerpins)==len(original_deps)==395,'camera include count changed')
        source=root/'source/src/camera_presentation_v1.cpp'; source.write_bytes(Path(plan['source_pins']['candidate_cpp']['path']).read_bytes())
        overlay=root/'source/include'; header=overlay/'xar_bridge/camera_presentation_v1.hpp'; header.write_bytes(Path(plan['source_pins']['candidate_header']['path']).read_bytes())
        geometry=overlay/'xar_bridge/realm_camera_geometry_v1.hpp'; geometry.write_bytes(Path(plan['source_pins']['candidate_geometry']['path']).read_bytes())
        env,tools=b.environment(root)
        ref(plan['build_scope']['compiler'])
        toolpins=prepared['tools']
        for key in ('compiler','linker_fresh','dumpbin_fresh'): ref(toolpins[key])
        require(b.sha(recipe['argv'][0])==plan['build_scope']['compiler']['sha256'],'short compiler path mismatch')
        linker=Path(toolpins['linker_fresh']['path']); dumpbin=Path(toolpins['dumpbin_fresh']['path'])
        b.write(root/'PREPARED.json',{'machine_id':machine,'at_utc':b.now(),'plan':b.pin(PLAN),'admission':b.pin(args.admission),'direct_inputs':directpins,'headers':headerpins,'tools':toolpins,'source':b.pin(source),'overlay':b.pin(header),'geometry_overlay':b.pin(geometry),'child_usage':usage(),'old_inputs_copied':0})
        print(json.dumps({'phase':'prepare_PASS','at_utc':b.now(),'usage':usage()}),flush=True)
        phase='compile_production'; attempt=root/'build/camera/attempt01'; attempt.mkdir(parents=True)
        obj,deps=attempt/'camera_presentation_v1.obj',attempt/'dependencies.json'
        compiled=run(argv_for(recipe['argv'],source,obj,deps,overlay),attempt,env_at(env,attempt/'temp'),attempt/'compile.log',64*b.MIB)
        actual_deps=b.read(deps)['Data']['Includes']
        oldheader=b.norm(plan['source_pins']['original_header']['path'])
        oldgeometry=b.norm(plan['source_pins']['original_geometry']['path'])
        expected=[b.norm(header) if b.norm(p)==oldheader else b.norm(geometry) if b.norm(p)==oldgeometry else b.norm(p) for p in original_deps]
        require([b.norm(p) for p in actual_deps]==expected,'actual Includes differ beyond unique overlay')
        require(sum(b.norm(p)==b.norm(header) for p in actual_deps)==sum(b.norm(p)==b.norm(geometry) for p in actual_deps)==1,'two overlay headers not unique')
        unchanged()
        b.write(root/'COMPILE-RESULT.json',{'machine_id':machine,'result':compiled,'source':b.pin(source),'header':b.pin(header),'object':b.pin(obj),'dependencies':b.pin(deps),'original395_order_preserved_except_two_explicit_headers':True,'geometry':b.pin(geometry),'M1_ABI_adopted':False})
        print(json.dumps({'phase':'compile_PASS','at_utc':b.now(),'usage':usage()}),flush=True)
        phase='link_production'
        lines=original_rsp.read_text(encoding='utf-8-sig').splitlines()
        oldobj=b.norm(plan['source_pins']['original_object']['path'])
        hits=[i for i,v in enumerate(lines) if b.norm(v.strip('"'))==oldobj]; require(len(hits)==1,'one camera replacement required'); lines[hits[0]]=str(obj)
        for prefix,suffix,count in (('/OUT:','dll',1),('/PDB:','pdb',1),('/IMPLIB:','lib',1),('/MAP:','map',2)):
            found=[i for i,v in enumerate(lines) if v.upper().startswith(prefix)]; require(len(found)==count,'output switch count')
            for i in found: lines[i]=prefix+str(root/('build/native29.'+suffix))
        rsp=root/'build/native29-link.rsp'; rsp.write_text('\n'.join(lines)+'\n',encoding='utf-8')
        linked=run([linker,'@'+str(rsp)],root/'build',env_at(env,root/'build/link-temp'),root/'build/link.log',256*b.MIB)
        dll,mapfile=root/'build/native29.dll',root/'build/native29.map'
        require(exports(dll)==exports(baseline/'build/native27.dll'),'five exports changed')
        maplines=[]
        with mapfile.open(encoding='utf-8-sig') as stream:
            for line in stream:
                if 'CameraPresentationRuntimeV1' in line or 'PopulateNonwarRouterExecutors12004' in line: maplines.append(line.strip())
        require(any('CameraPresentationRuntimeV1' in x and 'camera_presentation_v1.obj' in x for x in maplines),'new camera object absent from map')
        require(any('PopulateNonwarRouterExecutors12004' in x and 'nonwar12004.obj' in x for x in maplines),'Native27 router not retained')
        dump=run([dumpbin,'/EXPORTS',dll],root/'build',env,root/'build/exports.log')
        export_rows=[{'ordinal':int(o),'rva_hex':r,'name':n} for o,r,n in re.findall(r'^\s*(\d+)\s+[0-9A-F]+\s+([0-9A-F]+)\s+(Xar\w+)\s*$',(root/'build/exports.log').read_text(),re.M)]
        require([{k:r[k] for k in ('ordinal','name')} for r in export_rows]==exports(dll),'export RVA readback mismatch')
        b.write(root/'LINK-RESULT.json',{'machine_id':machine,'result':linked,'DLL':b.pin(dll),'map':b.pin(mapfile),'map_selected_lines':maplines,'exports':export_rows,'export_dump':dump,'direct_camera_replacements':1,'other355_direct_and612_archive_unchanged':True,'archive_rebuilds':0})
        print(json.dumps({'phase':'link_PASS','at_utc':b.now(),'usage':usage()}),flush=True)
        phase='offline_fixture'; offline=root/'offline01'; offline.mkdir()
        fixture=offline/'camera-fixture.cpp'; fixture.write_text(fixture_source(source.read_text(encoding='utf-8-sig'),plan['status_values']),encoding='utf-8',newline='\n')
        fixtureobj=offline/'camera-fixture.obj'; fixturedeps=offline/'dependencies.json'
        compile_fixture=run(argv_for(recipe['argv'],fixture,fixtureobj,fixturedeps,overlay),offline,env_at(env,offline/'temp'),offline/'compile.log',64*b.MIB)
        fixture_dll=offline/'camera-fixture.dll'
        fixture_link=run([linker,'/nologo','/DLL','/INCREMENTAL:NO','/OPT:REF','/OPT:ICF','/OUT:'+str(fixture_dll),fixtureobj],offline,env_at(env,offline/'link-temp'),offline/'link.log',128*b.MIB)
        loader=offline/'load-fixture.py'
        loader.write_text('import ctypes,json,sys\np=ctypes.WinDLL(sys.argv[1])\nf=p.RunNative29CameraFixture\nf.argtypes=[]\nf.restype=ctypes.c_int\nn=f()\nprint(json.dumps({"checks":n,"scope":"mock windows plus frozen geometry and additive enum/wire layout; no desktop or Game"}))\nraise SystemExit(0 if n==43 else 1)\n',encoding='utf-8')
        fixture_run=run([sys.executable,'-B',loader,fixture_dll],offline,env_at(env,offline/'load-temp'),offline/'run.log',timeout=120)
        b.write(offline/'RESULT.json',{'machine_id':machine,'status':'PASS','source':b.pin(fixture),'object':b.pin(fixtureobj),'fixture_DLL':b.pin(fixture_dll),'compile':compile_fixture,'link':fixture_link,'run':fixture_run,'checks_expected':43,'production_helper_body_extracted_verbatim':True,'production_DLL_loaded':False,'Game_RPC_desktop_actions':0})
        phase='close'; unchanged(); actual=usage()
        b.write(root/'QUALIFICATION.json',{'schema':'xar.ck3.native29-camera-qualification/v1','machine_id':machine,'observed_at_utc':b.now(),'status':'BUILD_AND_OFFLINE_PASS_NOT_DEPLOYED','label':'Native29 minimized camera and bounded native diagnostics','source':b.pin(source),'header':b.pin(header),'geometry':b.pin(geometry),'candidate_DLL':b.pin(dll),'baseline_DLL':plan['baseline_pins']['build/native27.dll'],'plan':b.pin(PLAN),'admission':b.pin(args.admission),'compile':b.pin(root/'COMPILE-RESULT.json'),'link':b.pin(root/'LINK-RESULT.json'),'offline':b.pin(offline/'RESULT.json'),'exports':export_rows,'status_values':plan['status_values'],'wire_layout_unchanged':True,'M1_ABI_adopted':False,'production_TUs_compiled':1,'fixture_TUs_compiled':1,'old_inputs_copied':0,'production_DLL_loaded':False,'Game_RPC_desktop_actions':0,'new_EXE_outputs':0,'tool_windows':windows,'measured_sampled_peak_bytes':peaks,'measured_peak_scope':'100ms samples and phase/exit checks; no claim to observe all transient peaks','child_usage_before_close':actual,'review_at_utc':deadline,'future_writes_bytes':0,'owned_subprocesses_remaining':0,'live_camera_qualified':False})
        status='PASS'
    except BaseException as error:
        b.write(root/'FAILED01.json',{'machine_id':machine,'observed_at_utc':b.now(),'phase':phase,'status':'RED_SINGLE_ATTEMPT_RETAINED','error':repr(error),'tool_windows':windows,'sampled_peak_bytes':peaks,'automatic_retry':False,'production_DLL_loaded':False,'Game_RPC_desktop_actions':0})
        status='RED'
    files=[b.pin(path)|{'relative_path':str(path.relative_to(root))} for path in sorted(root.rglob('*')) if path.is_file()]
    closed={'schema':'xar.storage.native29-files-closed/v1','machine_id':machine,'observed_at_utc':b.now(),'root':str(root),'status':status,'files_excluding_this_manifest':files,'logical_bytes_excluding_manifest':sum(p['bytes'] for p in files),'allocated_bytes_before_manifest':usage()['allocated_bytes'],'sampled_peak_bytes':peaks,'future_writes_bytes':0,'owned_build_or_fixture_subprocesses_remaining':0,'review_at_utc':deadline,'parent_or_child_credit_released':False}
    for _ in range(12):
        encoded=json.dumps(closed,ensure_ascii=True,indent=2).encode()+b'\n'
        total=closed['logical_bytes_excluding_manifest']+len(encoded)
        if closed.get('logical_bytes_including_manifest')==total: break
        closed['logical_bytes_including_manifest']=total
    else: raise ValueError('manifest fixed point failure')
    require(total<=hard,'closed total exceeds hard ceiling'); (root/'FILES-CLOSED.json').write_bytes(encoded)
    print(json.dumps({'status':status,'manifest':b.pin(root/'FILES-CLOSED.json'),'usage':usage(),'files':len(files)+1,'last_phase':phase}),flush=True)
    return 0 if status=='PASS' else 1


if __name__=='__main__':
    raise SystemExit(main())
