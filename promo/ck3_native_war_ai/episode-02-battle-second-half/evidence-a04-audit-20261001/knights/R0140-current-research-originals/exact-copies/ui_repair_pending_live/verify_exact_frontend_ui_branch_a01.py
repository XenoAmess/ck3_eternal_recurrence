from pathlib import Path
import hashlib,json,os,shutil,subprocess
HERE=Path(__file__).parent
RUN=HERE/'offline-exact-frontend-branch-attempt-01';RUN.mkdir(exist_ok=False)
SRC=Path('C:/w/e2research1001/ck3_autonomous_player/native_bridge')
source=(SRC/'src/frontend_gui_route_v1.cpp').read_text(encoding='utf-8')
slot=source[source.index('bool IsExecutingFrontendSlot('):source.index('\nstd::string FormatPointer(')]
branch=source[source.index('bool ExecuteFrontendGuiRouteMailboxV1('):source.index('  if (query->operation == FrontendGuiRouteOperationV1::inspect_tree)')]
branch+='  return false;\n}\n'
header='''#if defined(NDEBUG)
#undef NDEBUG
#endif
#include "xar_bridge/frontend_gui_route_v1.hpp"
#include <windows.h>
#include <cassert>
#include <iostream>
namespace xar::ck3_11906 {
static game::Snapshot fixture_before{},fixture_after{};
static bool snapshot_ok=true,gui_before_ok=true,gui_after_ok=true;
static unsigned snapshot_reads=0,gui_reads=0,invokes=0;
static IngameUiGuiOwnerBindingV1 fixture_gui_before{},fixture_gui_after{};
bool ReadSnapshot(const Bindings &,game::Snapshot &out) noexcept {
  out=snapshot_reads++==0?fixture_before:fixture_after;return snapshot_ok;
}
bool ReadIngameUiGuiOwnerBindingV1(const ZhongguoScoreboardNativeEnvironmentV1 &,IngameUiGuiOwnerBindingV1 &out) noexcept {
  const bool first=gui_reads++==0;out=first?fixture_gui_before:fixture_gui_after;
  return first?gui_before_ok:gui_after_ok;
}
bool ExecuteIngameUiNavigationV1(const ZhongguoScoreboardNativeEnvironmentV1 &,const IngameUiRequestV1 &,
 const game::Snapshot &snap,const MainThreadExecutionStampV1 &stamp,const IngameUiGuiOwnerBindingV1 &,IngameUiResultV1 &out) noexcept {
  ++invokes;out={};out.available=true;out.dispatch_invoked=true;out.verification_pending=true;
  out.status="acknowledged_verification_pending";out.date_raw=snap.date_raw;out.paused=snap.paused;
  out.played_character_id=snap.played_character_id;out.thread_id=stamp.thread_id;out.pump_epoch=stamp.pump_epoch;return true;
}
namespace {
'''
footer='''
} // namespace
} // namespace xar
int main() {
 using namespace xar::ck3_11906;
 MainThreadQueryMailboxV1 mb{};FrontendGuiRouteMailboxContextV1 q{};MainThreadExecutionStampV1 st{};
 const auto reset=[&] {
  q={};q.mailbox=&mb;q.ticket.sequence=2;q.operation=FrontendGuiRouteOperationV1::ingame_ui;
  mb.state.store(MainThreadQueryMailboxStateV1::executing);mb.stop_requested.store(false);mb.failure_flags.store(0);
  mb.published_sequence.store(2);mb.owner_thread_id.store(GetCurrentThreadId());
  mb.owner_verified_pump_epochs.store(7396);mb.paused_owner_verified_pump_epochs.store(7396);
  mb.executor=&ExecuteFrontendGuiRouteMailboxV1;mb.executor_context=&q;
  st={};st.pump_epoch=23345;st.thread_id=GetCurrentThreadId();st.tls_initialized_flag_address=1;
  st.tls_initialized=1;st.tls_context=2;st.tls_main_thread_marker=1;st.jomini_state=3;st.game_state=4;
  st.date_raw=53146848;st.paused=true;st.rng_owner_thread_id=0;
  fixture_before={};fixture_before.paused=true;fixture_before.map_ready=true;fixture_before.has_played_character=true;
  fixture_before.date_raw=53146848;fixture_before.played_character_id=29829;fixture_after=fixture_before;
  q.ingame_expected_snapshot=fixture_before;snapshot_ok=gui_before_ok=gui_after_ok=true;
  fixture_gui_before={reinterpret_cast<void *>(101),reinterpret_cast<void *>(201)};fixture_gui_after=fixture_gui_before;
  snapshot_reads=gui_reads=invokes=0;
 };
 unsigned cases=0;
 reset();assert(ExecuteFrontendGuiRouteMailboxV1(&q,st) && invokes==1 && q.ingame_result.available);
 assert(q.ingame_result.application_owner_thread_verified && q.ingame_result.gui_owner_binding_verified && q.ingame_result.rng_owner_thread_id==0);++cases;
 reset();st.rng_owner_thread_id=GetCurrentThreadId()+1;assert(ExecuteFrontendGuiRouteMailboxV1(&q,st) && invokes==1);++cases;
 for(unsigned i=0;i<15;++i) {
  reset();switch(i) {
  case 0:q.ticket.sequence=0;break;case 1:mb.published_sequence.store(3);break;
  case 2:mb.executor=nullptr;break;case 3:mb.executor_context=nullptr;break;
  case 4:mb.state.store(MainThreadQueryMailboxStateV1::queued);break;case 5:mb.stop_requested.store(true);break;
  case 6:mb.failure_flags.store(1);break;case 7:st.thread_id=GetCurrentThreadId()+1;break;
  case 8:mb.owner_thread_id.store(GetCurrentThreadId()+1);break;case 9:st.tls_initialized=0;break;
  case 10:st.tls_main_thread_marker=0;break;case 11:st.tls_context=0;break;
  case 12:st.tls_initialized_flag_address=0;break;case 13:st.pump_epoch=0;break;
  case 14:mb.owner_verified_pump_epochs.store(1);break;
  }
  assert(!ExecuteFrontendGuiRouteMailboxV1(&q,st) && invokes==0);++cases;
 }
 for(unsigned i=0;i<4;++i) {
  reset();switch(i) {case 0:st.paused=false;break;case 1:st.jomini_state=0;break;
  case 2:st.game_state=0;break;case 3:mb.paused_owner_verified_pump_epochs.store(1);break;}
  assert(ExecuteFrontendGuiRouteMailboxV1(&q,st) && invokes==0 && !q.ingame_result.available);
  assert(q.ingame_result.unavailable_reason=="application_paused_owner_stamp_unverified");++cases;
 }
 reset();q.ingame_expected_snapshot.date_raw=53146872;
 assert(ExecuteFrontendGuiRouteMailboxV1(&q,st) && invokes==0 && q.ingame_result.date_raw==53146848);
 assert(q.ingame_result.unavailable_reason=="owner_fresh_snapshot_admission_failed");++cases;
 reset();fixture_before.date_raw=53146872;q.ingame_expected_snapshot=fixture_before;
 assert(ExecuteFrontendGuiRouteMailboxV1(&q,st) && invokes==0 && q.ingame_result.date_raw==53146848);++cases;
 reset();snapshot_ok=false;assert(ExecuteFrontendGuiRouteMailboxV1(&q,st) && invokes==0);
 assert(q.ingame_result.played_character_id==-1 && q.ingame_result.unavailable_reason=="owner_fresh_snapshot_read_failed");++cases;
 reset();gui_before_ok=false;assert(ExecuteFrontendGuiRouteMailboxV1(&q,st) && invokes==0);
 assert(q.ingame_result.unavailable_reason=="current_gui_owner_binding_unverified");++cases;
 for(unsigned i=0;i<3;++i) {
  reset();switch(i) {case 0:fixture_gui_after.context=reinterpret_cast<void *>(102);break;
  case 1:fixture_gui_after.owner=reinterpret_cast<void *>(202);break;case 2:gui_after_ok=false;break;}
  assert(ExecuteFrontendGuiRouteMailboxV1(&q,st) && invokes==1 && !q.ingame_result.available && !q.ingame_result.gui_owner_binding_verified);
  assert(q.ingame_result.unavailable_reason=="current_gui_owner_binding_changed_after_navigation");++cases;
 }
 reset();fixture_after.date_raw=53146872;assert(ExecuteFrontendGuiRouteMailboxV1(&q,st) && invokes==1 && !q.ingame_result.available);
 assert(q.ingame_result.unavailable_reason=="owner_post_navigation_snapshot_changed");++cases;
 reset();fixture_after.played_character_id=33437;assert(ExecuteFrontendGuiRouteMailboxV1(&q,st) && invokes==1 && !q.ingame_result.available);++cases;
 std::cout<<cases<<" cases PASS: verbatim production ticket/UI branch with offline snapshot/GUI/navigation stubs, no game calls\\n";
}
'''
cpp=RUN/'exact_frontend_ui_branch_fixture.cpp'
cpp.write_text(header+slot+'\n} // anonymous\n'+branch+footer.replace('} // namespace\n} // namespace xar','} // namespace xar'),encoding='utf-8')
def ident(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest().upper()}
def write(name,v):
 with (RUN/name).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2);f.write('\n')
env=dict(os.environ);env.update(json.loads((HERE/'build-attempt-03-paused-original-ui-owner/vs-environment-selected.json').read_text(encoding='utf-8')))
env['VSLANG']='1033';compiler=shutil.which('cl',path=env['PATH'])
write('exact-source-extraction.json',{'source':ident(SRC/'src/frontend_gui_route_v1.cpp'),'fixture':ident(cpp),
 'IsExecutingFrontendSlot_verbatim':slot,'ExecuteFrontendGuiRouteMailboxV1_exact_UI_prefix':branch,
 'remainder_non_UI_dispatch_omitted':True,'ReadSnapshot_ReadGuiBinding_ExecuteUI_explicit_offline_stubs':True})
for name,argv in [('compile',[compiler,'/nologo','/std:c++20','/EHsc','/MD','/DNOMINMAX','/DWIN32_LEAN_AND_MEAN',
 '/I'+str(SRC/'include'),'/Fe'+str(RUN/'fixture.exe'),'/Fo'+str(RUN/'fixture.obj'),str(cpp),'/link','kernel32.lib']),
 ('execute',[str(RUN/'fixture.exe')])]:
 write(name+'-argv.json',{'argv':argv,'cwd':str(RUN)})
 with (RUN/(name+'-stdout.bin')).open('xb') as out,(RUN/(name+'-stderr.bin')).open('xb') as err:
  p=subprocess.run(argv,cwd=RUN,env=env,stdout=out,stderr=err)
 write(name+'-result.json',{'exit_code':p.returncode,'stdout':ident(RUN/(name+'-stdout.bin')),'stderr':ident(RUN/(name+'-stderr.bin'))})
 print(name,p.returncode,flush=True)
 if p.returncode:raise RuntimeError(name+' failed; originals retained')
print((RUN/'execute-stdout.bin').read_text(encoding='utf-8'))
