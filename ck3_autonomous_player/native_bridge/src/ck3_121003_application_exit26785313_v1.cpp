#include "xar_bridge/ck3_121003_application_exit26785313_v1.hpp"
#include "xar_bridge/ck3_121003_application_exit26785313_pins_v1.hpp"
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#include <algorithm>
#include <array>
#include <chrono>
#include <cstring>
#include <limits>
#include <windows.h>

namespace xar::ck3_121003::build26785313 { namespace {
bool ExitCopy(const void *source,void *out,std::size_t count) noexcept {
  if(!source||!out)return false;
  __try {std::memcpy(out,source,count);return true;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
template<class T>bool ExitAt(std::uintptr_t object,std::size_t offset,T &out) noexcept {
  constexpr auto max=(std::numeric_limits<std::uintptr_t>::max)();
  return object&&offset<=max-object&&sizeof(T)-1<=max-object-offset&&
      ExitCopy(reinterpret_cast<const void*>(object+offset),&out,sizeof(out));
}
[[maybe_unused]] bool ExitCoreEqual(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b) noexcept {
  return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&
      a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&
      a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;
}
[[maybe_unused]] bool ExitUnexpired(const ApplicationExitContext267V1 &q) noexcept {
  const auto now=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
  return q.monotonic_deadline_ms&&now>=0&&static_cast<std::uint64_t>(now)<q.request.deadline_unix_ms&&
      GetTickCount64()<q.monotonic_deadline_ms;
}
struct ExitAdmission267V1 {
  ApplicationExitContext267V1 &query;
  const ck3_11906::MainThreadExecutionStampV1 &stamp;
  ck3_1210::ApplicationExitBindingsV1 bound;
};
[[maybe_unused]] bool BeforeCurrentApplicationExit267V1([[maybe_unused]]void *opaque) noexcept {
#if !defined(XAR_CK3_ENABLE_121003_26785313_APPLICATION_EXIT_V1)
  return false;
#else
  auto &a=*static_cast<ExitAdmission267V1*>(opaque);auto &q=a.query;ReadonlyObservation current;
  if(!ExitUnexpired(q)||!ReadApplicationExitCoreOnOwner267V1(q.bindings,q.mailbox,q.ticket,a.stamp,&q,current)||
      !current.available||current.offline_fixture||!current.main_owner_observed||
      !ExitCoreEqual(current.core,q.request.expected))return false;
  const auto bound=BindApplicationExitImage267V1(q.bindings.module_base,kExecutableSha256);
  return bound.enabled&&bound.application_slot==a.bound.application_slot&&bound.request_quit==a.bound.request_quit&&
      bound.expected_application_vtable==a.bound.expected_application_vtable;
#endif
}
} // namespace
std::span<const ImagePin> ApplicationExitImagePins267V1() noexcept {return application_exit_pins::kPins;}
void ArmApplicationExitDeadline267V1(ApplicationExitContext267V1 &q) noexcept {
  q.monotonic_deadline_ms=0;
  const auto now=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
  if(now<0||q.request.deadline_unix_ms<=static_cast<std::uint64_t>(now))return;
  const auto remaining=q.request.deadline_unix_ms-static_cast<std::uint64_t>(now);
  q.monotonic_deadline_ms=GetTickCount64()+(remaining<8000?remaining:8000);
}
bool VerifyApplicationExitImage267V1([[maybe_unused]]std::uintptr_t base) noexcept {
#if !defined(XAR_CK3_ENABLE_121003_26785313_APPLICATION_EXIT_V1)
  return false;
#else
  if(!VerifyReadonlyImage(base))return false;std::array<unsigned char,64> value{};
  for(const auto &pin:application_exit_pins::kPins) {
    if(pin.bytes.empty()||pin.bytes.size()>value.size()||pin.rva>kImageSize-pin.bytes.size()||
        !ExitCopy(reinterpret_cast<const void*>(base+pin.rva),value.data(),pin.bytes.size())||
        std::memcmp(value.data(),pin.bytes.data(),pin.bytes.size())!=0)return false;
  }
  std::uintptr_t col=0;
  return ExitAt(base,kGuiRootApplicationVtableRvaV1-sizeof(std::uintptr_t),col)&&col==base+0x5162E58;
#endif
}
ck3_1210::ApplicationExitBindingsV1 BindApplicationExitImage267V1(std::uintptr_t base,std::string_view sha) noexcept {
  const auto core=BindReadonlyImage(base,sha);
  if(!core.exact_image_admitted||!VerifyApplicationExitImage267V1(base))return {};
  std::uintptr_t jomini=0,app=0,vtable=0;
  if(!ExitAt(reinterpret_cast<std::uintptr_t>(core.core.jomini_state_slot),0,jomini)||
      !ExitAt(jomini,0x18,app)||!ExitAt(app,0,vtable)||vtable!=base+kGuiRootApplicationVtableRvaV1)return {};
  // This exact current application pointer slot is also used by GetLocalPlayer
  // and the reviewed root witness; no legacy global singleton is inferred.
  return {true,reinterpret_cast<void*const*>(jomini+0x18),
      reinterpret_cast<ck3_1210::ApplicationQuitRequestV1>(base+kApplicationQuitRequestRva267V1),
      base+kGuiRootApplicationVtableRvaV1,0};
}
bool ApplicationExitRouteEnabled267V1([[maybe_unused]]const game::AdapterDescriptor &d) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_APPLICATION_EXIT_V1)
  return game::IsCk3_121003Core26785313Descriptor(d)&&
      std::find(d.capabilities.begin(),d.capabilities.end(),ck3_1210::kApplicationExitCapabilityV1)!=d.capabilities.end()&&
      std::find(d.capabilities.begin(),d.capabilities.end(),ck3_1210::kCoreFrameCapabilityV1)!=d.capabilities.end();
#else
  return false;
#endif
}
bool ExecuteApplicationExitOnOwner267V1(void *opaque,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  if(!opaque)return false;auto &q=*static_cast<ApplicationExitContext267V1*>(opaque);q.result={};
#if defined(XAR_CK3_ENABLE_121003_26785313_APPLICATION_EXIT_V1)
  using Status=ck3_1210::CoreControlStatusV1;using Exit=ck3_1210::ApplicationExitStatusV1;
  if(!q.mailbox||q.mailbox->offline_fixture||!q.session||!q.connection_generation||
      q.request.operation!=ck3_1210::CoreControlOperationV1::application_exit||
      q.request.step!=ck3_1210::kApplicationExitStepV1)return true;
  if(!ExitUnexpired(q)){q.result.status=Status::expired;return true;}
  ReadonlyObservation current;
  if(!ReadApplicationExitCoreOnOwner267V1(q.bindings,q.mailbox,q.ticket,stamp,&q,current)||
      !current.available||current.offline_fixture||!current.main_owner_observed||
      !ExitCoreEqual(current.core,q.request.expected)){q.result.status=Status::stale;return true;}
  q.result.observed=current.core;
  const auto bound=BindApplicationExitImage267V1(q.bindings.module_base,kExecutableSha256);
  if(!bound.enabled)return true;ExitAdmission267V1 admitted{q,stamp,bound};
  const bool prior=q.session->claimed.load(std::memory_order_acquire);
  const auto result=ck3_1210::RequestApplicationExitV1(bound,*q.session,&BeforeCurrentApplicationExit267V1,&admitted);
  q.result.effect_attempted=!prior&&q.session->claimed.load(std::memory_order_acquire)&&
      (result==Exit::requested||result==Exit::indeterminate);
  q.result.status=result==Exit::requested?Status::exit_requested:
      result==Exit::already_requested?Status::exit_already_requested:
      result==Exit::claim_consumed?Status::exit_claim_consumed:
      result==Exit::indeterminate?Status::indeterminate:Status::unavailable;
#endif
  return true;
}
} // namespace xar::ck3_121003::build26785313
