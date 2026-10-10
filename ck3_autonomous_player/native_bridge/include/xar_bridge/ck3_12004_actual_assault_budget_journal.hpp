#pragma once
#include "xar_bridge/army_actual_assault_budget_observations_v1.hpp"
#include <array>
#include <atomic>
#include <string_view>
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>

namespace xar::ck3_12004 {
inline constexpr std::uintptr_t kActualAssaultBudgetRva12004 = 0x25205A0;
inline constexpr std::uintptr_t kActualAssaultBudgetCallerReturnRva12004 = 0x2A97F64;
inline constexpr std::size_t kActualAssaultBudgetPatchBytes12004 = 16;
// Preserve opaque full RAX; only low EAX is the source-proved caller operand.
using ActualAssaultBudgetOriginal12004 = std::uintptr_t(__fastcall *)(void *);
using ActualAssaultBudgetRead12004 = bool (*)(void *, const void *, void *, std::size_t) noexcept;
using ActualAssaultBudgetParentReader12004 = bool (*)(ArmyAssaultConsumerParent12004 &) noexcept;
using ActualAssaultBudgetEventReader12004 = ArmyNaturalPhaseEvent12004 (*)(void *) noexcept;
using ActualAssaultBudgetRecorder12004 = bool (*)(std::uintptr_t, std::uintptr_t,
    const ArmyNaturalPhaseEvent12004 &, const ArmyNaturalPhaseEvent12004 &, std::int32_t,
    std::optional<std::uint32_t>, std::optional<std::uintptr_t>, std::optional<std::uint32_t>) noexcept;
using ActualAssaultBudgetAlloc12004 = void *(*)(void *, std::size_t, DWORD, DWORD) noexcept;
using ActualAssaultBudgetFree12004 = bool (*)(void *, void *, std::size_t, DWORD) noexcept;
using ActualAssaultBudgetProtect12004 = bool (*)(void *, void *, std::size_t, DWORD, DWORD &) noexcept;
using ActualAssaultBudgetFlush12004 = bool (*)(void *, const void *, std::size_t) noexcept;
struct ActualAssaultBudgetBindings12004 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  void *read_context = nullptr;
  ActualAssaultBudgetRead12004 read_memory = nullptr;
  ActualAssaultBudgetParentReader12004 copy_parent = nullptr;
  void *event_context = nullptr;
  ActualAssaultBudgetEventReader12004 next_event = nullptr;
  ActualAssaultBudgetRecorder12004 record_parent_budget = nullptr;
};
struct ActualAssaultBudgetInstallEnvironment12004 {
  bool primary_thread_suspended_proven = false;
  ActualAssaultBudgetBindings12004 bindings;
  std::uintptr_t budget_target_override = 0;
  void *memory_context = nullptr;
  ActualAssaultBudgetAlloc12004 virtual_alloc_override = nullptr;
  ActualAssaultBudgetFree12004 virtual_free_override = nullptr;
  ActualAssaultBudgetProtect12004 virtual_protect_override = nullptr;
  ActualAssaultBudgetFlush12004 flush_instruction_cache_override = nullptr;
};
struct ActualAssaultBudgetDetourState12004 {
  std::atomic<std::uint32_t> installed{0}, failure_flags{0};
  std::uintptr_t budget_target = 0;
  void *trampoline = nullptr, *memory_context = nullptr;
  std::array<std::uint8_t, kActualAssaultBudgetPatchBytes12004> original{};
  ActualAssaultBudgetFree12004 virtual_free = nullptr;
  ActualAssaultBudgetProtect12004 virtual_protect = nullptr;
  ActualAssaultBudgetFlush12004 flush_instruction_cache = nullptr;
};
ActualAssaultBudgetBindings12004 BindActualAssaultBudgetJournalImage12004(
    std::uintptr_t, std::string_view executable_sha256) noexcept;
bool InstallActualAssaultBudgetJournal12004(ActualAssaultBudgetDetourState12004 &,
    const ActualAssaultBudgetInstallEnvironment12004 &, std::string_view executable_sha256) noexcept;
bool UninstallActualAssaultBudgetJournal12004(ActualAssaultBudgetDetourState12004 &,
    bool primary_thread_suspended_proven) noexcept;
bool InitializeActualAssaultBudgetJournalFixture12004(
    const ActualAssaultBudgetBindings12004 &, ActualAssaultBudgetOriginal12004) noexcept;
std::uintptr_t InvokeActualAssaultBudgetObserver12004(void *selected_siege,
    std::optional<std::uintptr_t> actual_caller_return_rva) noexcept;
// Query serialization is paired to a copied parent entry token; an arbitrary
// query scalar cannot create or update a historical child observation.
ArmyActualAssaultBudgetObservationsV1 ReadActualAssaultBudgetObservations12004(
    const ArmyNaturalPhaseEvent12004 &parent_entry_event) noexcept;
extern "C" std::uintptr_t __fastcall XarActualAssaultBudgetHook12004(void *) noexcept;
} // namespace xar::ck3_12004
