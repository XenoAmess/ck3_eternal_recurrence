#include "xar_bridge/actual_army_daily_assault_preparation_observer_12004.hpp"
#include "xar_bridge/actual_army_pre_date_prefix_observer_12004.hpp"
#include <array>
#include <cstring>

// This TU is linked only into59d's new whole-query compound. There is no main,
// Run function, readiness setter or call of the old focus.
bool InitializeArmyPreparationNaturalSetup12004(std::uint32_t,bool) noexcept;
bool ConfigureArmyPreparationNaturalPositiveSetup12004(std::uint32_t,std::uint32_t) noexcept;
void SetArmyPreparationNaturalSetupImage12004(std::uintptr_t,std::uintptr_t) noexcept;
void SetArmyPreparationNaturalQueryPlacement12004(bool (*)(const void *,const void *) noexcept) noexcept;
xar::ck3_12004::ActualArmyDailyAssaultPreparationOriginal12004 ArmyPreparationNaturalSetupPreparationOriginal12004() noexcept;
bool ReadArmyPreparationNaturalFocus12004(void *,const void *,void *,std::size_t) noexcept;
bool InvokeArmyPlacementNaturalQueryFocus12004(const void *,const void *) noexcept;

namespace {
using namespace xar::ck3_12004;
std::uintptr_t g_image_base=0;
ActualArmyDailyAssaultPreparationDetourState12004 g_installed_state;
std::uint64_t __fastcall QueryPrefixOriginal(const void *,const void *,std::uint64_t incoming) { return incoming; }
}
std::uintptr_t ArmyPreparationNaturalQueryImageBase12004() noexcept { return g_image_base; }
bool ReadArmyPreparationNaturalQueryFocus12004(void *context,const void *address,void *out,std::size_t size) noexcept {
  return ReadArmyPreparationNaturalFocus12004(context,address,out,size);
}
bool InitializeArmyPreparationNaturalQuerySetup12004(std::uint32_t exact_army_full_id) noexcept {
  if(g_image_base || !InitializeArmyPreparationNaturalSetup12004(exact_army_full_id,true) ||
      !ConfigureArmyPreparationNaturalPositiveSetup12004(exact_army_full_id,0x72000003U))return false;
  // One owned fake image spansactual RVA2A90000..2AB0000. Its code forwards an
  // owned fake original, with the real CALL return address. It contains no CK3
  // callback body and cannot be used to attest a game transition.
  auto *region=static_cast<std::uint8_t *>(VirtualAlloc(nullptr,0x20000,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
  if(!region)return false;
  g_image_base=reinterpret_cast<std::uintptr_t>(region)-0x2A90000;
  auto *producer=reinterpret_cast<std::uint8_t *>(g_image_base+kActualArmyDailyAssaultPreparationRva12004);
  constexpr std::array<std::uint8_t,16> prefix{0x40,0x56,0x57,0x48,0x83,0xEC,0x48,0x48,0x8B,0xF9,0x48,0x8B,0xF2,0x48,0x8B,0xCA};
  std::memcpy(producer,prefix.data(),prefix.size());
  constexpr std::array<std::uint8_t,8> restore_arguments{0x48,0x8B,0xCF,0x48,0x8B,0xD6,0x48,0xB8};
  std::memcpy(producer+16,restore_arguments.data(),restore_arguments.size());
  const auto fake_original=reinterpret_cast<std::uintptr_t>(ArmyPreparationNaturalSetupPreparationOriginal12004());
  std::memcpy(producer+24,&fake_original,sizeof fake_original); producer[32]=0xFF; producer[33]=0xD0;
  constexpr std::array<std::uint8_t,7> epilogue{0x48,0x83,0xC4,0x48,0x5F,0x5E,0xC3}; std::memcpy(producer+34,epilogue.data(),epilogue.size());
  auto *caller=reinterpret_cast<std::uint8_t *>(g_image_base+0x2A9A073);
  constexpr std::array<std::uint8_t,14> caller_head{0x41,0x54,0x41,0x57,0x48,0x83,0xEC,0x28,0x4D,0x8B,0xF8,0x4D,0x8B,0xE1};
  std::memcpy(caller,caller_head.data(),caller_head.size()); caller[14]=0xE8;
  constexpr auto displacement=static_cast<std::int32_t>(
      static_cast<std::int64_t>(kActualArmyDailyAssaultPreparationRva12004)-
      static_cast<std::int64_t>(kActualArmyDailyAssaultPreparationReturnRva12004));
  std::memcpy(caller+15,&displacement,sizeof displacement);
  constexpr std::array<std::uint8_t,9> caller_tail{0x48,0x83,0xC4,0x28,0x41,0x5F,0x41,0x5C,0xC3}; std::memcpy(caller+19,caller_tail.data(),caller_tail.size());
  DWORD old=0;
  if(VirtualProtect(region,0x20000,PAGE_EXECUTE_READ,&old)==FALSE || FlushInstructionCache(GetCurrentProcess(),region,0x20000)==FALSE)return false;
  SetArmyPreparationNaturalSetupImage12004(g_image_base,reinterpret_cast<std::uintptr_t>(caller));
  SetArmyPreparationNaturalQueryPlacement12004(&InvokeArmyPlacementNaturalQueryFocus12004);
  auto prefix_bindings=BindActualArmyPreDatePrefixImage12004(g_image_base,kDailyAssaultPreparationExecutableSha256);
  prefix_bindings.read_memory=&ReadArmyPreparationNaturalQueryFocus12004;
  if(!InitializeActualArmyPreDatePrefixFixture12004(prefix_bindings,&QueryPrefixOriginal))return false;
  ActualArmyDailyAssaultPreparationInstallEnvironment12004 environment{};
  environment.primary_thread_suspended_proven=true;
  environment.bindings=BindActualArmyDailyAssaultPreparationImage12004(g_image_base,kDailyAssaultPreparationExecutableSha256);
  environment.bindings.read_memory=&ReadArmyPreparationNaturalQueryFocus12004;
  return InstallActualArmyDailyAssaultPreparationObserver12004(g_installed_state,environment,kDailyAssaultPreparationExecutableSha256);
}
