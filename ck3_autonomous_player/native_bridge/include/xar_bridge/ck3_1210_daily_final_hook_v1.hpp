#pragma once
#include "xar_bridge/ck3_1210.hpp"
#include <atomic>
#include <cstddef>
#include <cstdint>

namespace xar::ck3_1210 {
inline constexpr std::uintptr_t kDailyFinalFunctionRvaV1=0x2E772A0;
inline constexpr std::uintptr_t kDailyFinalSlotRvaV1=0x4B3D9B0;
inline constexpr std::uintptr_t kDailyFinalPrimaryVtableRvaV1=0x4B3D9D0;
inline constexpr std::uintptr_t kDailyFinalSecondaryVtableRvaV1=0x4B3D998;
inline constexpr std::uintptr_t kDailyFinalPrimaryColRvaV1=0x51C0470;
inline constexpr std::uintptr_t kDailyFinalSecondaryColRvaV1=0x51C0498;
inline constexpr std::uintptr_t kDailyFinalTypeDescriptorRvaV1=0x60B11C8;
using DailyFinalOriginalV1=void(__fastcall *)(); // Deliberately NOT noexcept.
using DailyFinalPostCallbackV1=void (*)(void *context) noexcept;
enum class DailyFinalBindingKindV1 { unavailable, exact_image, offline_fixture };
struct DailyFinalHookBindingsV1 {
  DailyFinalBindingKindV1 kind=DailyFinalBindingKindV1::unavailable;
  std::uintptr_t module_base=0;
  DailyFinalOriginalV1 *slot=nullptr;
  DailyFinalOriginalV1 expected_original=nullptr;
};
using DailyFinalCopyV1=bool (*)(void *,const void *,void *,std::size_t) noexcept;
using DailyFinalProtectV1=bool (*)(void *,void *,std::size_t,std::uint32_t,std::uint32_t &) noexcept;
using DailyFinalExchangeV1=bool (*)(void *,DailyFinalOriginalV1 *,DailyFinalOriginalV1,
    DailyFinalOriginalV1,DailyFinalOriginalV1 &) noexcept;
// A false exchange result guarantees no exchange write; a false protect result
// guarantees unchanged protection. Override seams are trusted internal code.
struct DailyFinalHookMemoryV1 {
  void *context=nullptr;
  DailyFinalCopyV1 copy=nullptr;
  DailyFinalProtectV1 protect=nullptr;
  DailyFinalExchangeV1 exchange=nullptr;
};
struct DailyFinalHookEnvironmentV1 {
  bool cold_quiescence_proven=false; // Owner-provided fact, never inferred here.
  bool allow_offline_fixture=false;
  DailyFinalHookMemoryV1 memory{};
};
enum class DailyFinalHookPhaseV1 { idle, installing, installed, stopping, uninstalled };
enum class DailyFinalHookResultV1 {
  installed, uninstalled, draining, invalid_request, invalid_state,
  quiescence_required, guard_failed, already_installed, foreign_slot,
  protection_failed, exchange_failed, protection_restore_failed, rollback_failed
};
// Single owner, noncopyable. Keep state and callback context alive until a
// successful Uninstall (not merely draining/foreign_slot). Never edit internals.
struct DailyFinalHookStateV1 {
  std::atomic<DailyFinalHookPhaseV1> phase{DailyFinalHookPhaseV1::idle};
  std::atomic<std::uint32_t> inflight{0};
  std::atomic<DailyFinalPostCallbackV1> callback{nullptr};
  std::atomic<DailyFinalHookResultV1> last_result{DailyFinalHookResultV1::invalid_state};
  DailyFinalHookBindingsV1 bindings{};
  DailyFinalHookMemoryV1 memory{};
  void *callback_context=nullptr;
  std::uint32_t original_protection=0;
  bool slot_restored=false;
  bool slot_published=false;
  bool protection_restored=true;
  bool image_guarded=false;
  bool fixture_only=false;
};
struct DailyFinalHookStatusV1 {
  DailyFinalHookPhaseV1 phase=DailyFinalHookPhaseV1::idle;
  DailyFinalHookResultV1 last_result=DailyFinalHookResultV1::invalid_state;
  std::uint32_t inflight=0;
  bool callback_enabled=false;
  bool slot_restored=false;
  bool protection_restored=true;
  bool image_guarded=false;
  bool fixture_only=false;
  bool capability_granted=false; // This component NEVER grants a game capability.
};
// Address calculation only. Install separately validates actual mapped bytes,
// both COLs, the CDailyTickCommand type/name, vtable methods and original slot.
DailyFinalHookBindingsV1 BindDailyFinalHookImageV1(std::uintptr_t base,
    std::string_view executable_sha256) noexcept;
// Explicit internal NoGame binding. It skips image qualification, not slot
// ownership/cold/protection/CAS/lifetime rules. Status always fixture_only.
DailyFinalHookBindingsV1 DailyFinalHookFixtureBindingsV1(DailyFinalOriginalV1 *slot,
    DailyFinalOriginalV1 original) noexcept;
DailyFinalHookResultV1 InstallDailyFinalHookV1(DailyFinalHookStateV1 &,
    const DailyFinalHookBindingsV1 &,const DailyFinalHookEnvironmentV1 &,
    DailyFinalPostCallbackV1,void *callback_context=nullptr) noexcept;
// Nonblocking stop: disables callback first; restores only our thunk using CAS.
// Draining means retry after inflight calls return; it never authorizes freeing
// state/context. Foreign slots are preserved. No automatic install/uninstall,
// reinstall after successful removal, or DLL hot-unload qualification exists.
DailyFinalHookResultV1 UninstallDailyFinalHookV1(DailyFinalHookStateV1 &) noexcept;
DailyFinalHookStatusV1 ReadDailyFinalHookStatusV1(const DailyFinalHookStateV1 &) noexcept;
extern "C" void __fastcall XarDailyFinalHook1210V1();
} // namespace xar::ck3_1210
