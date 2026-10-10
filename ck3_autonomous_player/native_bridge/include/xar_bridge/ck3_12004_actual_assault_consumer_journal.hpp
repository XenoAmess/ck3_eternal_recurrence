#pragma once
#include "xar_bridge/army_actual_assault_consumer_observations_v1.hpp"
#include <array>
#include <atomic>
#include <string_view>
#include <windows.h>

namespace xar::ck3_12004 {
inline constexpr std::uintptr_t kActualAssaultConsumerRva12004 = 0x2A97EB0;
inline constexpr std::size_t kActualAssaultConsumerPatchBytes12004 = 19;
using ActualAssaultConsumerOriginal12004 = std::uintptr_t(__fastcall *)(void *);
using ActualAssaultConsumerRead12004 = bool (*)(void *, const void *, void *, std::size_t) noexcept;
using ActualAssaultConsumerScopeReader12004 = ArmyNaturalPhaseScope12004 (*)() noexcept;
using ActualAssaultConsumerEventReader12004 = ArmyNaturalPhaseEvent12004 (*)(void *) noexcept;
using ActualAssaultConsumerAlloc12004 = void *(*)(void *, std::size_t, DWORD, DWORD) noexcept;
using ActualAssaultConsumerFree12004 = bool (*)(void *, void *, std::size_t, DWORD) noexcept;
using ActualAssaultConsumerProtect12004 = bool (*)(void *, void *, std::size_t, DWORD, DWORD &) noexcept;
using ActualAssaultConsumerFlush12004 = bool (*)(void *, const void *, std::size_t) noexcept;
struct ActualAssaultConsumerBindings12004 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  void *read_context = nullptr;
  ActualAssaultConsumerRead12004 read_memory = nullptr;
  ActualAssaultConsumerScopeReader12004 read_parent_scope = nullptr;
  void *event_context = nullptr;
  ActualAssaultConsumerEventReader12004 next_event = nullptr;
};
struct ActualAssaultConsumerInstallEnvironment12004 {
  bool primary_thread_suspended_proven = false;
  ActualAssaultConsumerBindings12004 bindings;
  std::uintptr_t consumer_target_override = 0;
  void *memory_context = nullptr;
  ActualAssaultConsumerAlloc12004 virtual_alloc_override = nullptr;
  ActualAssaultConsumerFree12004 virtual_free_override = nullptr;
  ActualAssaultConsumerProtect12004 virtual_protect_override = nullptr;
  ActualAssaultConsumerFlush12004 flush_instruction_cache_override = nullptr;
};
struct ActualAssaultConsumerDetourState12004 {
  std::atomic<std::uint32_t> installed{0}, failure_flags{0};
  std::uintptr_t consumer_target = 0;
  void *trampoline = nullptr, *memory_context = nullptr;
  std::array<std::uint8_t, kActualAssaultConsumerPatchBytes12004> original{};
  ActualAssaultConsumerFree12004 virtual_free = nullptr;
  ActualAssaultConsumerProtect12004 virtual_protect = nullptr;
  ActualAssaultConsumerFlush12004 flush_instruction_cache = nullptr;
};
enum ActualAssaultConsumerInstallFailure12004 : std::uint32_t {
  assault_install_none = 0, assault_install_exact_build = 1U << 0,
  assault_install_quiescence = 1U << 1, assault_install_already_installed = 1U << 2,
  assault_install_anchor = 1U << 3, assault_install_allocation = 1U << 4,
  assault_install_protection = 1U << 5, assault_install_flush = 1U << 6,
  assault_install_rollback = 1U << 7,
};
// Called only by 38c's naturally executing 25205A0 observer at literal caller
// return PC 2A97F64. Attaches a captured scalar in original physical group order.
// No getter, registry read, clock increment, or allocation occurs here.
bool RecordActualAssaultConsumerBudget12004(std::uintptr_t selected_siege_identity,
    std::uintptr_t actual_caller_return_rva, const ArmyNaturalPhaseEvent12004 &entry,
    const ArmyNaturalPhaseEvent12004 &returned, std::int32_t native_scalar,
    std::optional<std::uint32_t> selected_siege_full_id,
    std::optional<std::uintptr_t> selected_province_identity,
    std::optional<std::uint32_t> selected_province_full_id) noexcept;
ActualAssaultConsumerBindings12004 BindActualAssaultConsumerJournalImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
bool InstallActualAssaultConsumerJournal12004(ActualAssaultConsumerDetourState12004 &,
    const ActualAssaultConsumerInstallEnvironment12004 &, std::string_view executable_sha256) noexcept;
bool UninstallActualAssaultConsumerJournal12004(ActualAssaultConsumerDetourState12004 &,
    bool primary_thread_suspended_proven) noexcept;
bool InitializeActualAssaultConsumerJournalFixture12004(
    const ActualAssaultConsumerBindings12004 &, ActualAssaultConsumerOriginal12004) noexcept;
// Fixture/typed dispatcher route supplies only the naturally reached caller PC.
// The installed hook reads its real return address itself.
std::uintptr_t InvokeActualAssaultConsumerObserver12004(void *manager,
    std::optional<std::uintptr_t> caller_return_rva) noexcept;
std::optional<ArmyActualAssaultConsumerObservationsV1>
ReadActualAssaultConsumerObservations12004(std::uint32_t owned_army_full_id) noexcept;
extern "C" std::uintptr_t __fastcall XarActualAssaultConsumerHook12004(void *) noexcept;
} // namespace xar::ck3_12004
