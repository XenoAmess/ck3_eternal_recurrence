#include "xar_bridge/ck3_121003_date_postday26785313_v1.hpp"
#include "xar_bridge/ck3_121003_date_postday_pins26785313_v1.hpp"
#include <array>
#include <cstring>
#include <limits>
#include <windows.h>

namespace xar::ck3_121003::build26785313 {
namespace {
namespace pins = date_postday_pins267_v1;
constexpr std::array<DatePostdayPointerPin267V1,pins::kPointerPins.size()> Pointers() noexcept {
  std::array<DatePostdayPointerPin267V1,pins::kPointerPins.size()> out{};
  for(std::size_t i=0;i<out.size();++i)out[i]={pins::kPointerPins[i].rva,pins::kPointerPins[i].target_rva};
  return out;
}
constexpr auto kPointers = Pointers();
bool Copy(CommandImageReadV1 reader,std::uintptr_t at,void *out,std::size_t n) noexcept {
  if(!at||!out||!n)return false;
  if(reader.copy)return reader.copy(reader.context,at,out,n);
  if(reader.context)return false;
#if defined(_MSC_VER)
  __try {std::memcpy(out,reinterpret_cast<const void *>(at),n);return true;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
  std::memcpy(out,reinterpret_cast<const void *>(at),n);return true;
#endif
}
bool PinSet(std::uintptr_t base,CommandImageReadV1 reader,std::span<const ImagePin> values) noexcept {
  std::array<unsigned char,4096> actual{};
  for(const auto &pin:values) {
    if(pin.bytes.empty()||pin.bytes.size()>actual.size()||pin.rva>=kImageSize||pin.bytes.size()>kImageSize-pin.rva||
        !Copy(reader,base+pin.rva,actual.data(),pin.bytes.size())||
        std::memcmp(actual.data(),pin.bytes.data(),pin.bytes.size())!=0)return false;
  }
  return true;
}
} // namespace

std::span<const ImagePin> CurrentDatePostdayCodePins267V1() noexcept {return pins::kCodePins;}
std::span<const ImagePin> CurrentDatePostdayMetadataPins267V1() noexcept {return pins::kMetadataPins;}
std::span<const DatePostdayPointerPin267V1> CurrentDatePostdayPointerPins267V1() noexcept {return kPointers;}

bool VerifyCurrentDatePostdayImage267V1(std::uintptr_t base,
    const CommandIdentityV1 &identity,CommandImageReadV1 reader) noexcept {
  if(!base||base>(std::numeric_limits<std::uintptr_t>::max)()-kImageSize||
      !VerifyCurrentCommandImageV1(base,identity,reader)||
      !PinSet(base,reader,pins::kCodePins)||!PinSet(base,reader,pins::kMetadataPins))return false;
  for(const auto &pin:kPointers) {
    std::uintptr_t actual=0;
    if(pin.rva>kImageSize-sizeof(actual)||pin.target_rva>=kImageSize||
        !Copy(reader,base+pin.rva,&actual,sizeof(actual))||actual!=base+pin.target_rva)return false;
  }
  return true;
}

bool CurrentDatePostdayTargetsMatch267V1(const DatePostdayImageBindings267V1 &b) noexcept {
  const auto base=b.module_base;
  return b.current_image_verified&&base&&base<=(std::numeric_limits<std::uintptr_t>::max)()-kImageSize&&
      b.commands.current_image_verified&&!b.commands.offline_fixture&&b.commands.module_base==base&&
      CurrentCommandTargetsMatchV1(b.commands)&&
      reinterpret_cast<std::uintptr_t>(b.daily_final_slot)==base+kDateDailyFinalSlot267V1&&
      reinterpret_cast<std::uintptr_t>(b.daily_final_original)==base+kDateDailyFinalFunction267V1&&
      reinterpret_cast<std::uintptr_t>(b.set_paused)==base+kDatePauseFunction267V1&&
      reinterpret_cast<std::uintptr_t>(b.acquire_worker_access)==base+kDateWorkerAcquire267V1&&
      reinterpret_cast<std::uintptr_t>(b.destroy_worker_access)==base+kDateWorkerDestroy267V1&&
      b.command_manager==base+kCommandManagerRvaV1&&b.worker_consumer==base+kDateWorkerConsumer267V1&&
      b.worker_runner==base+kDateWorkerRunner267V1&&b.worker_start==base+kDateWorkerStart267V1&&
      b.application_slot==base+kDateApplicationSlot267V1&&b.tls_initialized_flag==base+kTlsFlagRva;
}

DatePostdayImageBindings267V1 BindCurrentDatePostdayImage267V1(
    std::uintptr_t base,const CommandIdentityV1 &identity) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1) && XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1 == 1
  if(base!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))||
      !VerifyCurrentDatePostdayImage267V1(base,identity))return {};
  auto commands=BindCurrentCommandImageV1(base,identity);
  if(!commands.current_image_verified||commands.offline_fixture||!CurrentCommandTargetsMatchV1(commands))return {};
  DatePostdayImageBindings267V1 b{};
  b.module_base=base;b.commands=commands;
  b.daily_final_slot=reinterpret_cast<DateDailyFinalOriginal267V1 *>(base+kDateDailyFinalSlot267V1);
  b.daily_final_original=reinterpret_cast<DateDailyFinalOriginal267V1>(base+kDateDailyFinalFunction267V1);
  b.set_paused=reinterpret_cast<ck3_11906::TacticalSetPausedV1>(base+kDatePauseFunction267V1);
  b.acquire_worker_access=reinterpret_cast<DateWorkerAcquire267V1>(base+kDateWorkerAcquire267V1);
  b.destroy_worker_access=reinterpret_cast<DateWorkerDestroy267V1>(base+kDateWorkerDestroy267V1);
  b.command_manager=base+kCommandManagerRvaV1;b.worker_consumer=base+kDateWorkerConsumer267V1;
  b.worker_runner=base+kDateWorkerRunner267V1;b.worker_start=base+kDateWorkerStart267V1;
  b.application_slot=base+kDateApplicationSlot267V1;b.tls_initialized_flag=base+kTlsFlagRva;
  b.current_image_verified=true;
  return CurrentDatePostdayTargetsMatch267V1(b)?b:DatePostdayImageBindings267V1{};
#else
  static_cast<void>(base);static_cast<void>(identity);return {};
#endif
}

ck3_1210::DailyFinalHookBindingsV1 CurrentDateDailyFinalHookSource267V1(
    const DatePostdayImageBindings267V1 &b) noexcept {
  const CommandIdentityV1 identity{kGameVersion,kSteamBuildId,kExecutableSha256};
  if(b.module_base!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))||
      !CurrentDatePostdayTargetsMatch267V1(b)||
      !VerifyCurrentDatePostdayImage267V1(b.module_base,identity))return {};
  return {ck3_1210::DailyFinalBindingKindV1::exact_image,b.module_base,
      b.daily_final_slot,b.daily_final_original};
}

bool VerifyCurrentDatePostdayHookImage267V1(const DatePostdayImageBindings267V1 &b,
    const ck3_1210::DailyFinalHookStateV1 &hook) noexcept {
  const CommandIdentityV1 identity{kGameVersion,kSteamBuildId,kExecutableSha256};
  if(b.module_base!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))||
      !CurrentDatePostdayTargetsMatch267V1(b))return false;
  const auto status=ck3_1210::ReadDailyFinalHookStatusV1(hook);
  if(status.phase!=ck3_1210::DailyFinalHookPhaseV1::installed||status.fixture_only||
      !status.image_guarded||!status.callback_enabled||
      hook.bindings.kind!=ck3_1210::DailyFinalBindingKindV1::exact_image||
      hook.bindings.module_base!=b.module_base||hook.bindings.slot!=b.daily_final_slot||
      hook.bindings.expected_original!=b.daily_final_original)return false;
  // a32's pointer inventory has no DailyFinal slot and stays unchanged.
  if(!VerifyCurrentCommandImageV1(b.module_base,identity)||
      !PinSet(b.module_base,{},pins::kCodePins)||!PinSet(b.module_base,{},pins::kMetadataPins))return false;
  for(const auto &pin:kPointers) {
    std::uintptr_t actual=0;
    const auto expected=pin.rva==kDateDailyFinalSlot267V1
        ?reinterpret_cast<std::uintptr_t>(&ck3_1210::XarDailyFinalHook1210V1)
        :b.module_base+pin.target_rva;
    if(!Copy({},b.module_base+pin.rva,&actual,sizeof(actual))||actual!=expected)return false;
  }
  return true;
}
} // namespace xar::ck3_121003::build26785313
