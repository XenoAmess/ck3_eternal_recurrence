#pragma once
#include "xar_bridge/war_payment_passive_12004.hpp"
#include <array>
#include <atomic>
#include <string>
#include <string_view>
#include <windows.h>

namespace xar::ck3_12004 {
#if defined(XAR_ENABLE_WAR_PAYMENT_RAW4_GETTER_12004)
inline constexpr std::size_t kWarPaymentHookCount12004 = 6;
#else
inline constexpr std::size_t kWarPaymentHookCount12004 = 5;
#endif
enum class WarPaymentHook12004 : std::size_t { transition, gateway, personal_add, personal_sub, land_sub
#if defined(XAR_ENABLE_WAR_PAYMENT_RAW4_GETTER_12004)
  , raw4_getter
#endif
};
struct WarPaymentHookDescription12004 {
  std::uintptr_t rva = 0;
  std::size_t prefix_bytes = 0;
  std::array<std::uint8_t,16> prefix{};
};
const std::array<WarPaymentHookDescription12004,kWarPaymentHookCount12004> &WarPaymentHookDescriptions12004() noexcept;
using WarPaymentWrite12004 = bool (*)(void *,std::uintptr_t,const void *,std::size_t) noexcept;
using WarPaymentAllocate12004 = void *(*)(void *,std::size_t) noexcept;
using WarPaymentFree12004 = bool (*)(void *,void *) noexcept;
using WarPaymentProtect12004 = bool (*)(void *,void *,std::size_t,DWORD,DWORD &) noexcept;
using WarPaymentFlush12004 = bool (*)(void *,const void *,std::size_t) noexcept;
using WarPaymentPin12004 = bool (*)(void *) noexcept;
struct WarPaymentInstallEnvironment12004 {
  bool primary_thread_suspended_proven = false;
  std::uintptr_t module_base = 0;
  std::string_view executable_sha256;
  WarPaymentBindings12004 bindings;
  // Only an explicitly labelled no-game fixture may replace native targets.
  bool fixture_targets = false;
  std::array<std::uintptr_t,kWarPaymentHookCount12004> target_overrides{};
  void *memory_context = nullptr;
  WarPaymentWrite12004 write = nullptr;
  WarPaymentAllocate12004 allocate = nullptr;
  WarPaymentFree12004 free = nullptr;
  WarPaymentProtect12004 protect = nullptr;
  WarPaymentFlush12004 flush = nullptr;
  WarPaymentPin12004 pin_module = nullptr;
};
struct WarPaymentHookSlot12004 {
  std::uintptr_t target = 0;
  void *trampoline = nullptr;
  std::array<std::uint8_t,16> original{};
  std::size_t size = 0;
  DWORD original_protection = 0;
  bool patch_may_be_present = false;
};
struct WarPaymentDetourState12004 {
  std::atomic<bool> installed{false};
  std::atomic<std::uint32_t> failure_flags{0};
  std::atomic<std::uint64_t> active_calls{0};
  std::array<WarPaymentHookSlot12004,kWarPaymentHookCount12004> hooks{};
  WarPaymentInstallEnvironment12004 environment;
  bool module_pinned = false;
};
bool InstallWarPaymentPassive12004(WarPaymentDetourState12004 &,
    const WarPaymentInstallEnvironment12004 &) noexcept;
// Requires a fresh quiescent/suspended-primary proof. Never called from DllMain.
// Failed restoration retains every reachable original/trampoline and ownership.
bool UninstallWarPaymentPassive12004(WarPaymentDetourState12004 &,
    bool primary_thread_suspended_proven) noexcept;
std::uintptr_t WarPaymentEntryThunkAddress12004(WarPaymentHook12004) noexcept;

struct WarPaymentEnvelope12004 {
  std::string machine_id;
  std::string_view executable_sha256;
  WarPaymentSession12004 current_session;
  bool installed = false;
  std::uint32_t install_failure_flags = 0;
  // True only for the operator's explicit same-owned-process/no-load window.
  // It is not a source-proved loaded-game epoch.
  bool controlled_window_admitted = false;
};
struct WarPaymentQualifiedDebit12004 {
  std::uint64_t writer_sequence = 0, transition_sequence = 0, gateway_sequence = 0;
  std::int32_t account_kind = -1;
  std::uint32_t payer_character_id = 0;
  std::optional<std::uint32_t> land_id;
  std::int64_t requested_amount_raw = 0;
  std::uint64_t entry_balance_bits = 0, returned_balance_bits = 0;
  bool returned_balance_matches_requested_sub = false;
};
std::vector<WarPaymentQualifiedDebit12004> QualifyWarPaymentDebits12004(
    const WarPaymentJournalSnapshot12004 &,const WarPaymentEnvelope12004 &,
    const std::vector<ArmyNaturalPhaseRecord12004> &,
    const ArmyNaturalPhaseJournalStatus12004 &);
std::string SerializeWarPaymentJournal12004(const WarPaymentJournalSnapshot12004 &,
    const WarPaymentEnvelope12004 &,const std::vector<ArmyNaturalPhaseRecord12004> &,
    const ArmyNaturalPhaseJournalStatus12004 &);
std::string AppendWarPaymentJournal12004(std::string current_resources_json,
    const WarPaymentJournalSnapshot12004 &,const WarPaymentEnvelope12004 &,
    const std::vector<ArmyNaturalPhaseRecord12004> &,
    const ArmyNaturalPhaseJournalStatus12004 &);
} // namespace xar::ck3_12004
