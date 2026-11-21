#pragma once
#include "xar_bridge/ck3_121003_commands26785313_v1.hpp"
#include "xar_bridge/tactical_daily_sentinel_v1.hpp"
#include "xar_bridge/ck3_1210_daily_final_hook_v1.hpp"
#include "xar_bridge/ck3_1210_date_worker_game_access_v1.hpp"
#include <span>

namespace xar::ck3_121003::build26785313 {
inline constexpr std::uintptr_t kDateDailyFinalSlot267V1 = 0x4B3D9B8;
inline constexpr std::uintptr_t kDateDailyFinalFunction267V1 = 0x2E77090;
inline constexpr std::uintptr_t kDatePauseFunction267V1 = 0x3E658B0;
inline constexpr std::uintptr_t kDatePauseCommit267V1 = 0x3E657F0;
inline constexpr std::uintptr_t kDateWorkerConsumer267V1 = 0x3E1D140;
inline constexpr std::uintptr_t kDateWorkerRunner267V1 = 0x3E1D530;
inline constexpr std::uintptr_t kDateWorkerStart267V1 = 0x3E17920;
inline constexpr std::uintptr_t kDateWorkerAcquire267V1 = 0x3E64C40;
inline constexpr std::uintptr_t kDateWorkerDestroy267V1 = 0x3E64F50;
inline constexpr std::uintptr_t kDateApplicationSlot267V1 = 0x6A643B8;
inline constexpr std::size_t kDateCommandScopeOffset267V1 = 0x140;
inline constexpr std::size_t kDateNativeAccessOffset267V1 = 0x6E8;
inline constexpr std::size_t kDateMainWarmOffset267V1 = 0x3620;
inline constexpr std::size_t kDateMainContextOffset267V1 = 0x3628;
inline constexpr std::size_t kDateWorkerStartedOffset267V1 = 0x3F0;
inline constexpr std::size_t kDateWorkerFunctionOffset267V1 = 0xB8;
inline constexpr std::size_t kDateWorkerContextOffset267V1 = 0xC0;
inline constexpr std::size_t kDateWorkerStopOffset267V1 = 0xC8;
inline constexpr std::size_t kDateWorkerHolderOffset267V1 = 0xD0;
using DateDailyFinalOriginal267V1 = void(__fastcall *)(); // Preserve exceptions.
using DateWorkerAcquire267V1 = void (*)();
using DateWorkerDestroy267V1 = void (*)(void *descriptor);
struct DatePostdayPointerPin267V1 {std::uintptr_t rva,target_rva;};
std::span<const ImagePin> CurrentDatePostdayCodePins267V1() noexcept;
std::span<const ImagePin> CurrentDatePostdayMetadataPins267V1() noexcept;
std::span<const DatePostdayPointerPin267V1> CurrentDatePostdayPointerPins267V1() noexcept;
// Actual current image verification only. Reader seams can verify NoGame data;
// they never create a production binding, owner, hook or clock permission.
bool VerifyCurrentDatePostdayImage267V1(std::uintptr_t module_base,
    const CommandIdentityV1 &, CommandImageReadV1 = {}) noexcept;
struct DatePostdayImageBindings267V1 {
  bool current_image_verified = false;
  std::uintptr_t module_base = 0;
  CommandImageBindingsV1 commands{};
  DateDailyFinalOriginal267V1 *daily_final_slot = nullptr;
  DateDailyFinalOriginal267V1 daily_final_original = nullptr;
  ck3_11906::TacticalSetPausedV1 set_paused = nullptr;
  DateWorkerAcquire267V1 acquire_worker_access = nullptr;
  DateWorkerDestroy267V1 destroy_worker_access = nullptr;
  std::uintptr_t command_manager = 0,worker_consumer = 0,worker_runner = 0;
  std::uintptr_t worker_start = 0,application_slot = 0,tls_initialized_flag = 0;
};
// Default OFF; current primary process module only; no model memory reader or
// caller boolean can qualify it. It returns static source targets, not actions.
DatePostdayImageBindings267V1 BindCurrentDatePostdayImage267V1(
    std::uintptr_t module_base,const CommandIdentityV1 &) noexcept;
bool CurrentDatePostdayTargetsMatch267V1(const DatePostdayImageBindings267V1 &) noexcept;
// Cold binding to the existing generic slot/CAS/lifetime installer. This is
// neither installation nor a cold-quiescence claim; the real suspended owner
// must still supply those facts to the existing installer.
ck3_1210::DailyFinalHookBindingsV1 CurrentDateDailyFinalHookSource267V1(
    const DatePostdayImageBindings267V1 &) noexcept;
// Runtime image check explicitly expects the existing owned hook thunk in the
// final slot. It does not pretend the original EXE pointer is still present.
bool VerifyCurrentDatePostdayHookImage267V1(const DatePostdayImageBindings267V1 &,
    const ck3_1210::DailyFinalHookStateV1 &) noexcept;
struct DateWorkerAccessContext267V1 {
  const DatePostdayImageBindings267V1 *image = nullptr;
  const ck3_1210::DailyFinalHookStateV1 *hook = nullptr;
};
// Resource scope only. The date consumer MUST independently retain and verify
// the actual duplicated worker handle/birth/ID and executing epoch before this
// call. This wrapper proves actual source/TLS/resource cleanup, not that epoch,
// a date target, a command receipt, or a caller-supplied authorization boolean.
ck3_1210::DateWorkerGameAccessResultV2 WithCurrentDateWorkerGameAccess267V2(
    void *actual_context,ck3_1210::DateWorkerGameBodyV1,void *body_context) noexcept;
} // namespace xar::ck3_121003::build26785313
