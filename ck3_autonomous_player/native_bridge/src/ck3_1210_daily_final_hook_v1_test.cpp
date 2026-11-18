#include "xar_bridge/ck3_1210_daily_final_hook_v1.hpp"
#include <atomic>
#include <chrono>
#include <cstdlib>
#include <cstring>
#include <exception>
#include <iostream>
#include <thread>
#include <vector>
#include <windows.h>
namespace {
using namespace xar::ck3_1210;
using Fn=DailyFinalOriginalV1;
using Code=DailyFinalHookResultV1;
using Phase=DailyFinalHookPhaseV1;
void Check(bool ok,const char *message) {
  if(!ok){std::cerr<<"FAIL "<<message<<std::endl;std::exit(1);}
}
void __fastcall Original();
void __fastcall Foreign() {}
struct Fixture {
  Fn slot=&Original;
  DailyFinalHookStateV1 state{};
  DailyFinalHookEnvironmentV1 env{};
  std::atomic<int> originals{0},posts{0},mode{0};
  std::atomic<bool> entered{false},block{false};
  std::vector<int> order;
  unsigned protects=0,copies=0,exchanges=0,fail_protect=0;
  bool fail_exchange=false,race_foreign=false;
  std::uint32_t protection=PAGE_READONLY;
  Fixture() {
    order.reserve(32);env.cold_quiescence_proven=true;env.allow_offline_fixture=true;
    env.memory={this,&Copy,&Protect,&Exchange};
  }
  Fn Load() {return std::atomic_ref<Fn>(slot).load(std::memory_order_acquire);}
  void Store(Fn fn) {std::atomic_ref<Fn>(slot).store(fn,std::memory_order_release);}
  DailyFinalHookBindingsV1 Binding(){return DailyFinalHookFixtureBindingsV1(&slot,&Original);}
  static bool Copy(void *ctx,const void *from,void *to,std::size_t size) noexcept {
    auto &f=*static_cast<Fixture *>(ctx);++f.copies;
    // No synthetic EXE image or CodeRVA execution: unknown addresses deny.
    if(from!=&f.slot || size!=sizeof(Fn))return false;
    const auto fn=f.Load();std::memcpy(to,&fn,sizeof(fn));return true;
  }
  static bool Protect(void *ctx,void *at,std::size_t size,std::uint32_t next,std::uint32_t &old) noexcept {
    auto &f=*static_cast<Fixture *>(ctx);++f.protects;
    if(at!=&f.slot || size!=sizeof(Fn) || f.protects==f.fail_protect)return false;
    old=f.protection;f.protection=next;return true;
  }
  static bool Exchange(void *ctx,Fn *at,Fn desired,Fn expected,Fn &observed) noexcept {
    auto &f=*static_cast<Fixture *>(ctx);++f.exchanges;
    if(at!=&f.slot)return false;
    if(f.fail_exchange){f.fail_exchange=false;observed=f.Load();return false;}
    if(f.race_foreign){f.race_foreign=false;f.Store(&Foreign);}
    observed=expected;
    std::atomic_ref<Fn>(f.slot).compare_exchange_strong(observed,desired,std::memory_order_acq_rel);
    return true;
  }
};
Fixture *active=nullptr;
struct OriginalFailure {};
constexpr DWORD kOriginalSeh=0xE1210101;
void __fastcall Original() {
  auto &f=*active;++f.originals;f.order.push_back(1);
  if(f.mode.load()==1)throw OriginalFailure{};
  if(f.mode.load()==2)RaiseException(kOriginalSeh,0,0,nullptr);
  if(f.mode.load()==3) {
    f.entered.store(true,std::memory_order_release);
    while(f.block.load(std::memory_order_acquire))std::this_thread::yield();
  }
}
void Post(void *context) noexcept {
  auto &f=*static_cast<Fixture *>(context);++f.posts;f.order.push_back(2);
}
void OtherPost(void *) noexcept {std::terminate();}
#if defined(_MSC_VER)
bool CatchOriginalSeh(Fn fn) {
  __try {fn();}
  __except(GetExceptionCode()==kOriginalSeh?EXCEPTION_EXECUTE_HANDLER:EXCEPTION_CONTINUE_SEARCH){return true;}
  return false;
}
#endif
void EmptyStatus(Fixture &f) {
  const auto s=ReadDailyFinalHookStatusV1(f.state);
  Check(s.phase==Phase::idle && !s.callback_enabled && !s.image_guarded &&
      !s.capability_granted && s.inflight==0,"failed admission grants nothing");
}
} // namespace
int main() {
  using namespace xar::ck3_1210;
  Fixture f;active=&f;
  Check(UninstallDailyFinalHookV1(f.state)==Code::invalid_state,"idle uninstall refused");
  Check(BindDailyFinalHookImageV1(0,kExecutableSha256).kind==DailyFinalBindingKindV1::unavailable &&
      BindDailyFinalHookImageV1(0x140000000,"old-sha").kind==DailyFinalBindingKindV1::unavailable,
      "address binder exact identity gate");
  const auto image=BindDailyFinalHookImageV1(0x140000000,kExecutableSha256);
  Check(image.kind==DailyFinalBindingKindV1::exact_image && image.module_base==0x140000000 &&
      reinterpret_cast<std::uintptr_t>(image.slot)==0x144B3D9B0,"address-only real slot binding");
  Check(InstallDailyFinalHookV1(f.state,image,f.env,&Post,&f)==Code::guard_failed,
      "actual mapped class/entry guards cannot be supplied by fixture slot");
  EmptyStatus(f);
  auto env=f.env;env.cold_quiescence_proven=false;
  Check(InstallDailyFinalHookV1(f.state,f.Binding(),env,&Post,&f)==Code::quiescence_required,"cold proof mandatory");
  env=f.env;env.allow_offline_fixture=false;
  Check(InstallDailyFinalHookV1(f.state,f.Binding(),env,&Post,&f)==Code::guard_failed,"fixture requires explicit test scope");
  Check(InstallDailyFinalHookV1(f.state,f.Binding(),f.env,nullptr,&f)==Code::invalid_request,"fixed callback required");
  auto unaligned=DailyFinalHookFixtureBindingsV1(reinterpret_cast<Fn *>(reinterpret_cast<std::uintptr_t>(&f.slot)+1),&Original);
  Check(InstallDailyFinalHookV1(f.state,unaligned,f.env,&Post,&f)==Code::invalid_request,"unaligned slot rejected before access");
  f.Store(&Foreign);
  Check(InstallDailyFinalHookV1(f.state,f.Binding(),f.env,&Post,&f)==Code::foreign_slot && f.Load()==&Foreign,
      "foreign original refused without overwrite");
  f.Store(&Original);f.protects=0;f.fail_protect=1;
  Check(InstallDailyFinalHookV1(f.state,f.Binding(),f.env,&Post,&f)==Code::protection_failed && f.Load()==&Original,
      "failed writable transition leaves original untouched");
  f.fail_protect=0;f.protects=0;f.fail_exchange=true;
  Check(InstallDailyFinalHookV1(f.state,f.Binding(),f.env,&Post,&f)==Code::exchange_failed &&
      f.Load()==&Original && f.protection==PAGE_READONLY,"CAS fault preserves slot/protection");
  f.protects=0;f.race_foreign=true;
  Check(InstallDailyFinalHookV1(f.state,f.Binding(),f.env,&Post,&f)==Code::foreign_slot &&
      f.Load()==&Foreign && f.protection==PAGE_READONLY,"CAS race preserves foreign pointer");
  f.Store(&Original);f.protects=0;f.fail_protect=2;
  Check(InstallDailyFinalHookV1(f.state,f.Binding(),f.env,&Post,&f)==Code::protection_restore_failed &&
      f.Load()==&Original && f.protection==PAGE_READONLY &&
      ReadDailyFinalHookStatusV1(f.state).phase==Phase::idle,"failed post-CAS protection rolls original back");
  f.fail_protect=0;f.protects=0;
  Check(InstallDailyFinalHookV1(f.state,f.Binding(),f.env,&Post,&f)==Code::installed,"one explicit cold fixture install");
  const auto installed=ReadDailyFinalHookStatusV1(f.state);
  Check(installed.phase==Phase::installed && installed.fixture_only && !installed.image_guarded &&
      !installed.capability_granted && installed.callback_enabled && f.protection==PAGE_READONLY,
      "fixture installation never claims real image/runtime capability");
  const auto thunk=f.Load();
  Check(thunk==&XarDailyFinalHook1210V1,"only owned slot points to new thunk");
  thunk();
  Check(f.originals.load()==1 && f.posts.load()==1 && f.order==std::vector<int>{1,2},
      "synchronous original completes before fixed postday callback");
  Check(InstallDailyFinalHookV1(f.state,f.Binding(),f.env,&OtherPost,nullptr)==Code::already_installed &&
      f.Load()==thunk,"repeat install cannot replace callback or original");
  DailyFinalHookStateV1 unrelated;
  Check(UninstallDailyFinalHookV1(unrelated)==Code::invalid_state && f.Load()==thunk,"unrelated state cannot uninstall");
  f.order.clear();f.mode.store(1);bool threw=false;
  try{thunk();}catch(const OriginalFailure &){threw=true;}
  Check(threw && f.originals.load()==2 && f.posts.load()==1 && f.order==std::vector<int>{1} &&
      ReadDailyFinalHookStatusV1(f.state).inflight==0,"original C++ exception propagates; post skipped; rundown balanced");
#if defined(_MSC_VER)
  f.order.clear();f.mode.store(2);
  Check(CatchOriginalSeh(thunk) && f.originals.load()==3 && f.posts.load()==1 &&
      f.order==std::vector<int>{1} && ReadDailyFinalHookStatusV1(f.state).inflight==0,
      "native original SEH propagates through thunk finally; no substitute/post");
#endif
  f.mode.store(3);f.order.clear();f.block.store(true);f.entered.store(false);
  const auto posts_before=f.posts.load();
  std::thread worker([&]{thunk();});
  const auto until=std::chrono::steady_clock::now()+std::chrono::seconds(2);
  while(!f.entered.load(std::memory_order_acquire) && std::chrono::steady_clock::now()<until)
    std::this_thread::yield();
  Check(f.entered.load(std::memory_order_acquire),"real thunk entry is inflight");
  f.Store(&Foreign); // Explicit external mutation of fixture RAM only.
  Check(UninstallDailyFinalHookV1(f.state)==Code::foreign_slot && f.Load()==&Foreign,
      "uninstall never overwrites a foreign hook");
  auto stopping=ReadDailyFinalHookStatusV1(f.state);
  Check(stopping.phase==Phase::stopping && !stopping.callback_enabled && stopping.inflight==1,
      "stop disables callback but retains state/context for inflight original");
  f.Store(thunk); // Fixture removes its simulated foreign hook for valid retry.
  Check(UninstallDailyFinalHookV1(f.state)==Code::draining && f.Load()==&Original && f.protection==PAGE_READONLY,
      "owned CAS restores original/protection; nonblocking drain refuses early release");
  f.block.store(false,std::memory_order_release);worker.join();
  Check(f.posts.load()==posts_before && f.order==std::vector<int>{1},"stopped callback not run after blocked original returns");
  Check(UninstallDailyFinalHookV1(f.state)==Code::uninstalled,"safe retry detaches after inflight zero");
  const auto removed=ReadDailyFinalHookStatusV1(f.state);
  Check(removed.phase==Phase::uninstalled && removed.inflight==0 && !removed.callback_enabled &&
      removed.slot_restored && removed.protection_restored && !removed.capability_granted,"completed stop state");
  f.mode.store(0);f.order.clear();const auto originals_before=f.originals.load();
  thunk(); // A preloaded old thunk pointer is safe after state detach.
  Check(f.originals.load()==originals_before+1 && f.posts.load()==posts_before && f.order==std::vector<int>{1},
      "late cached thunk always invokes retained actual original and no dead context");
  Check(UninstallDailyFinalHookV1(f.state)==Code::invalid_state && f.Load()==&Original,
      "duplicate uninstall is refused");
  DailyFinalHookStateV1 repeated;
  Check(InstallDailyFinalHookV1(repeated,f.Binding(),f.env,&Post,&f)==Code::already_installed,
      "successful hook claim cannot be replayed after stop");
  std::cout<<"PASS ck3_1210_daily_final_hook_v1 NoGame; original preserved; capability=0"<<std::endl;
  return 0;
}
