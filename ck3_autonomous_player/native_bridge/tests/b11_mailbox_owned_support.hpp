#pragma once
#ifdef NDEBUG
#error B11 mailbox assertions must remain enabled
#endif
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <deque>

// Synthetic image/page/TLS metadata, over memory owned by this process only.
// These helpers neither map nor inspect CK3, and never invoke the hooked IAT.
// Shape follows the existing production mailbox's explicit offline-fixture seam.
namespace b11_owned {
namespace mt=xar::ck3_11906;
// Production intentionally pins its singleton mailbox identity until exit.
inline mt::MainThreadQueryMailboxV1 retained_mailbox{};
inline void* tls_context=nullptr;
inline void* __fastcall TlsContext() noexcept {return tls_context;}
inline BOOL WINAPI OriginalPeek(LPMSG,HWND,UINT,UINT,UINT){return FALSE;}
inline bool RejectAnchor(std::uintptr_t) noexcept {return false;}
inline constexpr std::uintptr_t kOwnedPumpReturn=0x1234;
inline const mt::MainThreadQueryBuildProfileV1 profile{
  kOwnedPumpReturn,0,0,0,0,0,0,&RejectAnchor};
struct Protection {
  void** slot=nullptr;
  DWORD current=PAGE_READONLY;
  unsigned queries=0,changes=0;
};
inline bool QueryPage(void* opaque,const void* address,MEMORY_BASIC_INFORMATION& out) noexcept {
  auto& p=*static_cast<Protection*>(opaque);++p.queries;
  if(address!=p.slot)return false;
  const auto page=reinterpret_cast<std::uintptr_t>(address)&~std::uintptr_t(4095);
  out={};out.BaseAddress=reinterpret_cast<void*>(page);out.AllocationBase=out.BaseAddress;
  out.AllocationProtect=PAGE_READONLY;out.RegionSize=4096;
  out.State=MEM_COMMIT;out.Protect=p.current;out.Type=MEM_IMAGE;return true;
}
inline bool ProtectPage(void* opaque,void* page,std::size_t size,DWORD desired,DWORD& old) noexcept {
  auto& p=*static_cast<Protection*>(opaque);++p.changes;
  const auto expected=reinterpret_cast<std::uintptr_t>(p.slot)&~std::uintptr_t(4095);
  if(size!=4096||reinterpret_cast<std::uintptr_t>(page)!=expected)return false;
  old=p.current;p.current=desired;return true;
}
struct Runtime {
  std::array<std::byte,0x18> rng_state{};
  std::uintptr_t rng_wrapper=0,rng_wrapper_slot=0;
  std::array<std::byte,0x28> jomini{};
  std::uintptr_t jomini_slot=0;
  std::array<std::byte,0x18> game{};
  std::uintptr_t game_slot=0;
  std::uint8_t initialized=1;
  std::array<std::byte,0x28> tls{};
  alignas(void*) void* iat=reinterpret_cast<void*>(&OriginalPeek);
  Protection protection{};
  std::uint32_t thread=GetCurrentThreadId();
  std::int32_t date=123456;
  Runtime() {
    std::memcpy(rng_state.data()+0x10,&thread,sizeof(thread));
    rng_wrapper=reinterpret_cast<std::uintptr_t>(rng_state.data());
    rng_wrapper_slot=reinterpret_cast<std::uintptr_t>(&rng_wrapper);
    jomini[0x20]=std::byte{1};jomini_slot=reinterpret_cast<std::uintptr_t>(jomini.data());
    std::memcpy(game.data()+8,&date,sizeof(date));game_slot=reinterpret_cast<std::uintptr_t>(game.data());
    tls[0x20]=std::byte{1};tls_context=tls.data();protection.slot=&iat;
  }
  Runtime(const Runtime&)=delete;
  Runtime& operator=(const Runtime&)=delete;
  mt::MainThreadQueryInstallEnvironmentV1 Environment() {
    mt::MainThreadQueryInstallEnvironmentV1 e{};
    e.module_base=1;e.exact_build_admitted=true;e.offline_fixture=true;
    e.peek_message_iat_slot_override=&iat;e.resolved_peek_message_override=&OriginalPeek;
    e.global_rng_wrapper_slot_override=reinterpret_cast<std::uintptr_t>(&rng_wrapper_slot);
    e.jomini_state_slot_override=reinterpret_cast<std::uintptr_t>(&jomini_slot);
    e.game_state_slot_override=reinterpret_cast<std::uintptr_t>(&game_slot);
    e.tls_initialized_flag_override=reinterpret_cast<std::uintptr_t>(&initialized);
    e.tls_context_getter_override=&TlsContext;e.memory_protection_context=&protection;
    e.memory_query_override=&QueryPage;e.memory_protect_override=&ProtectPage;
    e.system_page_size_override=4096;e.executor_submission_enabled=true;e.build_profile=&profile;
    return e;
  }
  void Warm(mt::MainThreadQueryMailboxV1& m) const {
    assert(!mt::ObserveMainThreadPumpAndDrainV1(m,kOwnedPumpReturn,thread));
    assert(!mt::ObserveMainThreadPumpAndDrainV1(m,kOwnedPumpReturn,thread));
    const auto d=mt::ReadMainThreadQueryMailboxDiagnosticsV1(m);
    assert(d.ready&&d.owner_thread_id==thread&&d.paused_main_thread_observed);
  }
  void Finish(mt::MainThreadQueryMailboxV1& m) const {
    const auto frontend_before=m.permitted_frontend_executor;
    assert(mt::UninstallMainThreadQueryMailboxV1(m,50)==mt::MainThreadQueryUninstallResultV1::uninstalled);
    assert(iat==reinterpret_cast<void*>(&OriginalPeek));
    assert(m.state.load()==mt::MainThreadQueryMailboxStateV1::detached);
    assert(protection.current==PAGE_READONLY&&protection.queries>=2&&protection.changes>=4);
    assert(!m.permitted_executor_character_skill_effect12004);
    assert(!m.permitted_executor_player_inventory_window_read12004);
    assert(!m.permitted_executor_player_inventory_window_open12004);
    assert(!m.permitted_executor_artifact_personal_read12004);
    assert(!m.permitted_executor_artifact_personal_action12004);
    assert(!m.permitted_executor_ghw_permissions_read12004);
    assert(!m.permitted_executor_player_pilgrimage_identities12004);
    assert(!m.permitted_executor_player_pilgrimage_execution12004);
    // Legacy frontend identity is intentionally retained by production. New
    // gameplay slots clear, while stop/detached must reject retained frontend.
    assert(m.permitted_frontend_executor==frontend_before);
    if(frontend_before) {
      unsigned context=0;mt::MainThreadQueryTicketV1 ticket{};
      assert(mt::TrySubmitMainThreadQueryV1(m,frontend_before,&context,ticket)==mt::MainThreadQuerySubmitResultV1::mailbox_not_installed);
      assert(ticket.sequence==0);
    }
  }
};
inline std::deque<Runtime> retained_runtimes{};
inline Runtime& NewRuntime(){return retained_runtimes.emplace_back();}
struct Seen {unsigned calls=0,tag=0;mt::MainThreadExecutionStampV1 stamp{};};
template<unsigned Tag> bool Marker(void* p,const mt::MainThreadExecutionStampV1& stamp) noexcept {
  if(!p)return false;auto& s=*static_cast<Seen*>(p);++s.calls;s.tag=Tag;s.stamp=stamp;return true;
}
using Executor=mt::MainThreadQueryExecutorV1;
struct Slot {
  const char* name;
  Executor mt::MainThreadQueryInstallEnvironmentV1::*environment;
  Executor mt::MainThreadQueryMailboxV1::*mailbox;
  Executor callback;
};
inline const std::array<Slot,9> slots{{
  {"actor",&mt::MainThreadQueryInstallEnvironmentV1::permitted_executor_character_skill_effect12004,&mt::MainThreadQueryMailboxV1::permitted_executor_character_skill_effect12004,&Marker<1>},
  {"inventory_read",&mt::MainThreadQueryInstallEnvironmentV1::permitted_executor_player_inventory_window_read12004,&mt::MainThreadQueryMailboxV1::permitted_executor_player_inventory_window_read12004,&Marker<2>},
  {"inventory_open",&mt::MainThreadQueryInstallEnvironmentV1::permitted_executor_player_inventory_window_open12004,&mt::MainThreadQueryMailboxV1::permitted_executor_player_inventory_window_open12004,&Marker<3>},
  {"artifact_read",&mt::MainThreadQueryInstallEnvironmentV1::permitted_executor_artifact_personal_read12004,&mt::MainThreadQueryMailboxV1::permitted_executor_artifact_personal_read12004,&Marker<4>},
  {"artifact_action",&mt::MainThreadQueryInstallEnvironmentV1::permitted_executor_artifact_personal_action12004,&mt::MainThreadQueryMailboxV1::permitted_executor_artifact_personal_action12004,&Marker<5>},
  {"ghw_read",&mt::MainThreadQueryInstallEnvironmentV1::permitted_executor_ghw_permissions_read12004,&mt::MainThreadQueryMailboxV1::permitted_executor_ghw_permissions_read12004,&Marker<6>},
  {"legacy_pilgrimage_read",&mt::MainThreadQueryInstallEnvironmentV1::permitted_executor_player_pilgrimage_identities12004,&mt::MainThreadQueryMailboxV1::permitted_executor_player_pilgrimage_identities12004,&Marker<7>},
  {"legacy_pilgrimage_execute",&mt::MainThreadQueryInstallEnvironmentV1::permitted_executor_player_pilgrimage_execution12004,&mt::MainThreadQueryMailboxV1::permitted_executor_player_pilgrimage_execution12004,&Marker<8>},
  {"legacy_normal_exit_frontend",&mt::MainThreadQueryInstallEnvironmentV1::permitted_frontend_executor,&mt::MainThreadQueryMailboxV1::permitted_frontend_executor,&Marker<9>}
}};
inline void RunMarker(Runtime& r,mt::MainThreadQueryMailboxV1& m,const Slot& slot,unsigned tag) {
  Seen seen{};mt::MainThreadQueryTicketV1 ticket{};
  assert(mt::TrySubmitMainThreadQueryV1(m,slot.callback,&seen,ticket)==mt::MainThreadQuerySubmitResultV1::submitted);
  assert(mt::ObserveMainThreadPumpAndDrainV1(m,kOwnedPumpReturn,r.thread));
  assert(mt::WaitForMainThreadQueryV1(m,ticket,20)==mt::MainThreadQueryWaitResultV1::completed);
  assert(seen.calls==1&&seen.tag==tag&&seen.stamp.thread_id==r.thread&&seen.stamp.date_raw==r.date);
  assert(mt::ReclaimMainThreadQueryV1(m,ticket)==mt::MainThreadQueryReclaimResultV1::reclaimed);
}
}
