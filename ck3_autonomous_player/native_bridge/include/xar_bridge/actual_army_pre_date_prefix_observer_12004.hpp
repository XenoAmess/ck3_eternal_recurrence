#pragma once
#include "xar_bridge/army_natural_phase_scope_12004.hpp"
#include <array>
#include <atomic>
#include <optional>
#include <string_view>
#include <vector>
#include <windows.h>

#define XAR_HAS_ACTUAL_ARMY_PRE_DATE_PREFIX_12004 1
namespace xar::ck3_12004 {
inline constexpr std::string_view kActualArmyPreDatePrefixSha12004 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
inline constexpr std::uintptr_t kActualArmyPreDatePrefixRva12004=0x2A9A340;
inline constexpr std::uintptr_t kActualArmyPreDatePrefixReturnRva12004=0x2A99E76;
inline constexpr std::size_t kActualArmyPreDatePrefixPatchBytes12004=17;
inline constexpr std::size_t kActualArmyPreDatePrefixJournalCapacity12004=64;
// Production points to a tiny source-specific thunk: restore incoming RAX from
// R8, then JMP the relocated original. D4<=0 does not write RAX in the source.
using ActualArmyPreDatePrefixOriginal12004=std::uint64_t(__fastcall *)(const void *, const void *, std::uint64_t);
using ActualArmyPreDatePrefixRead12004=bool (*)(void *,const void *,void *,std::size_t) noexcept;
using ActualArmyPreDatePrefixAlloc12004=void *(*)(void *,std::size_t,DWORD,DWORD) noexcept;
using ActualArmyPreDatePrefixFree12004=bool (*)(void *,void *,std::size_t,DWORD) noexcept;
using ActualArmyPreDatePrefixProtect12004=bool (*)(void *,void *,std::size_t,DWORD,DWORD &) noexcept;
using ActualArmyPreDatePrefixFlush12004=bool (*)(void *,const void *,std::size_t) noexcept;
struct ActualArmyPreDatePrefixBindings12004 {
  bool enabled=false;
  std::uintptr_t image_base=0;
  void *read_context=nullptr;
  ActualArmyPreDatePrefixRead12004 read_memory=nullptr;
  std::size_t maximum_copied_occurrences=4096;
};
struct ActualArmyPreDatePrefixInstallEnvironment12004 {
  bool primary_thread_suspended_proven=false;
  ActualArmyPreDatePrefixBindings12004 bindings{};
  std::uintptr_t callback_target_override=0;
  void *memory_context=nullptr;
  ActualArmyPreDatePrefixAlloc12004 virtual_alloc_override=nullptr;
  ActualArmyPreDatePrefixFree12004 virtual_free_override=nullptr;
  ActualArmyPreDatePrefixProtect12004 virtual_protect_override=nullptr;
  ActualArmyPreDatePrefixFlush12004 flush_instruction_cache_override=nullptr;
};
struct ActualArmyPreDatePrefixDetourState12004 {
  std::atomic<std::uint32_t> installed{0},failure_flags{0};
  std::uintptr_t callback_target=0;
  void *trampoline=nullptr;
  std::array<std::uint8_t,kActualArmyPreDatePrefixPatchBytes12004> original{};
  void *memory_context=nullptr;
  ActualArmyPreDatePrefixFree12004 virtual_free=nullptr;
  ActualArmyPreDatePrefixProtect12004 virtual_protect=nullptr;
  ActualArmyPreDatePrefixFlush12004 flush_instruction_cache=nullptr;
};
enum ActualArmyPreDatePrefixInstallFailure12004 : std::uint32_t {
  actual_army_prefix_install_exact_build=1U<<0,actual_army_prefix_install_quiescence=1U<<1,
  actual_army_prefix_install_already_installed=1U<<2,actual_army_prefix_install_anchor=1U<<3,
  actual_army_prefix_install_allocation=1U<<4,actual_army_prefix_install_protection=1U<<5,
  actual_army_prefix_install_flush=1U<<6,actual_army_prefix_install_rollback=1U<<7
};
struct ActualArmyPreDatePrefixQueue12004 {
  std::optional<std::uintptr_t> data_identity,end_identity;
  std::optional<std::int32_t> capacity,count;
  std::optional<bool> bounds_valid,copy_bound_admitted;
  bool copied_complete=false;
  std::vector<std::uint32_t> ordered_full_ids;
};
struct ActualArmyPreDatePrefixSnapshot12004 {
  ActualArmyPreDatePrefixQueue12004 source_c8{},destination_158{};
  std::optional<std::uint64_t> supplied_date_raw_u64,game_date_raw_u64;
  std::optional<std::uint32_t> absolute_day_raw_u32;
  std::optional<std::uint8_t> calendar_c0_raw_u8;
  // Direct-source conditional no-work arm. This is separate from actual return.
  std::optional<bool> conditional_no_work_arm;
  bool positive_physical_transition_complete=false;
};
struct ActualArmyPreDatePrefixObservation12004 {
  std::uint64_t sequence=0;
  std::uintptr_t primary_manager_identity=0,date_argument_identity=0;
  std::uintptr_t caller_return_rva=0;
  ArmyNaturalPhaseScope12004 parent{};
  ArmyNaturalPhaseEvent12004 entry_event{},returned_event{};
  bool parent_bound=false,original_called=false,original_returned=false;
  std::uint64_t incoming_rax_raw_u64=0,original_rax_raw_u64=0;
  ActualArmyPreDatePrefixSnapshot12004 before{},after{};
  bool original_roster_capture_complete=false;
  ArmyNaturalPhaseRoster12004 captured_original_roster{};
  std::uint32_t capture_failure_flags=0;
};
struct ActualArmyPreDatePrefixObservations12004 {
  bool observer_installed=false,current_session_guard=false;
  std::uint64_t oldest_available_sequence=0,latest_sequence=0,overwritten_events=0,unattributed_capture_failures=0;
  std::vector<ActualArmyPreDatePrefixObservation12004> events;
};
ActualArmyPreDatePrefixBindings12004 BindActualArmyPreDatePrefixImage12004(std::uintptr_t,std::string_view) noexcept;
bool InstallActualArmyPreDatePrefixObserver12004(ActualArmyPreDatePrefixDetourState12004 &,
    const ActualArmyPreDatePrefixInstallEnvironment12004 &,std::string_view) noexcept;
std::optional<ActualArmyPreDatePrefixObservations12004> ReadActualArmyPreDatePrefixObservations12004(std::uintptr_t exact_primary_manager) noexcept;
extern "C" std::uint64_t __fastcall XarActualArmyPreDatePrefixHook12004(const void *,const void *,std::uint64_t incoming_rax) noexcept;
bool InitializeActualArmyPreDatePrefixFixture12004(const ActualArmyPreDatePrefixBindings12004 &,ActualArmyPreDatePrefixOriginal12004) noexcept;
std::uint64_t InvokeActualArmyPreDatePrefixFixture12004(std::uintptr_t caller_return_rva,const void *,const void *,std::uint64_t incoming_rax) noexcept;
} // namespace xar::ck3_12004
