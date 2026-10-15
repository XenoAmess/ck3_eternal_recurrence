#pragma once
#include "xar_bridge/army_natural_phase_scope_12004.hpp"
#include <array>
#include <mutex>
#include <optional>
#include <vector>

// Passive records for the opt-in exact-build payment detours and query window.
namespace xar::ck3_12004 {
enum class WarPaymentKind12004 { transition, gateway, personal_add, personal_sub, land_sub };
struct WarPaymentSession12004 {
  std::uint32_t pid = 0;
  std::uint64_t process_create_time_100ns = 0;
  std::uint64_t connection_generation = 0;
  std::optional<std::uintptr_t> loaded_game_epoch;
  std::uint64_t controlled_window_id = 0;
  bool same_owned_process_no_load_window = false;
  std::uintptr_t game_state_identity_witness = 0;
  std::optional<std::uint32_t> player_character_full_id;
  std::optional<std::uint64_t> snapshot_revision;
  std::optional<std::uint64_t> native_date_raw;
  std::optional<std::uint32_t> absolute_day_raw;
};
struct WarPaymentFrame12004 {
  std::uintptr_t character = 0, wrapper = 0;
  std::optional<std::uint32_t> character_id, character_magic;
  std::optional<std::uintptr_t> character_extension;
  std::optional<std::uint64_t> personal_gold_bits, wrapper_balance_bits;
  std::optional<std::uint32_t> land_id, land_magic;
  std::optional<std::uint32_t> army_id, army_magic, requested_unit_id, province_magic;
  std::optional<std::uint32_t> province_id;
  std::optional<std::uint8_t> army_1d4;
  bool capture_complete = false;
  std::uint32_t failed_reads = 0;
};
struct WarPaymentNaturalParent12004 {
  bool observed = false;
  ArmyNaturalPhaseKind12004 phase = ArmyNaturalPhaseKind12004::unknown;
  std::uintptr_t actual_entry_rva = 0, primary_manager = 0, game_state = 0;
  std::optional<std::uintptr_t> session_identity;
  ArmyNaturalPhaseEvent12004 entry_event;
  std::optional<std::uint64_t> date_raw;
  std::optional<std::uint32_t> absolute_day_raw;
};
struct WarPaymentRecord12004 {
  // Retention ordinal only. Every cross-family join uses the shared event clock.
  std::uint64_t journal_sequence = 0;
  WarPaymentKind12004 kind = WarPaymentKind12004::transition;
  std::uintptr_t receiver = 0, second_pointer = 0, caller_return_rva = 0;
  std::int64_t amount_raw = 0;
  std::int32_t resource_kind_raw = -1, component_raw = -1;
  ArmyNaturalPhaseEvent12004 entry_event, returned_event;
  ArmyNaturalPhaseEvent12004 parent_transition_entry, parent_gateway_entry;
  std::uintptr_t parent_transition_army = 0, parent_gateway_character = 0;
  std::uintptr_t parent_transition_caller = 0, parent_gateway_caller = 0;
  std::int32_t parent_gateway_resource = -1, parent_gateway_component = -1;
  std::int64_t parent_gateway_amount = 0;
  WarPaymentNaturalParent12004 natural_parent_metadata;
  WarPaymentNaturalParent12004 natural_return_metadata;
  WarPaymentSession12004 session_entry, session_return;
  WarPaymentFrame12004 before, after;
  bool original_called = false, original_returned = false;
  std::uintptr_t raw_return_bits = 0;
  bool clock_thread_order_matches = false, session_matches = false;
  bool natural_parent_matches = false;
  bool same_character_after = false, same_wrapper_after = false;
  bool personal_wrapper_matches_character = false;
  bool source_boarding_call_chain_matches = false;
  bool tls_depth_exceeded = false;
};
struct WarPaymentJournalSnapshot12004 {
  bool read_complete = false;
  std::uint64_t latest_sequence = 0, oldest_sequence = 0, overwritten = 0;
  std::uint64_t publication_failures = 0;
  ArmyObserverResearchSamplingState12004 sampling;
  std::vector<WarPaymentRecord12004> records;
};
struct WarPaymentJournal12004 {
  static constexpr std::size_t capacity = 512;
  std::mutex mutex;
  army_observer_research_detail_12004::Policy policy;
  std::array<WarPaymentRecord12004, capacity> records{};
  std::uint64_t latest = 0, publication_failures = 0;
  ArmyObserverResearchSamplingState12004 SetEnabled(bool) noexcept;
  WarPaymentJournalSnapshot12004 Copy() noexcept;
};
using WarPaymentSessionReader12004 = WarPaymentSession12004 (*)(void *) noexcept;
struct WarPaymentBindings12004 {
  bool exact_build_and_prefixes_verified = false;
  ArmyNaturalPhaseRead12004 read = nullptr;
  void *read_context = nullptr;
  ArmyNaturalPhaseEventReader12004 next_event = nullptr;
  void *event_context = nullptr;
  WarPaymentSessionReader12004 session = nullptr;
  void *session_context = nullptr;
  ArmyNaturalPhaseScope12004 (*natural_metadata)(void *) noexcept = nullptr;
  void *natural_context = nullptr;
  WarPaymentJournal12004 *journal = nullptr;
  // False only for a source-proven unrelated actor; unavailable identity retains
  // an explicitly incomplete record. This never skips or retries the original.
  bool (*retain_actor)(void *,WarPaymentKind12004,std::uintptr_t,std::uintptr_t) noexcept = nullptr;
  void *retain_actor_context = nullptr;
};
#if defined(_MSC_VER)
#define XAR_PAYMENT_ABI12004 __fastcall
#else
#define XAR_PAYMENT_ABI12004
#endif
using WarPaymentTransitionOriginal12004 = std::uintptr_t(XAR_PAYMENT_ABI12004 *)(void *, void *);
using WarPaymentGatewayOriginal12004 = std::uintptr_t(XAR_PAYMENT_ABI12004 *)(void *, std::int32_t, std::int64_t, std::int32_t);
using WarPaymentWriterOriginal12004 = std::uintptr_t(XAR_PAYMENT_ABI12004 *)(void *, std::int64_t, void *);
#undef XAR_PAYMENT_ABI12004
// actual_caller_return_rva is captured by Root's entry thunk, never inside these helpers.
std::uintptr_t InvokeWarPaymentTransition12004(const WarPaymentBindings12004 &,
  WarPaymentTransitionOriginal12004, void *army, void *province, std::uintptr_t actual_caller_return_rva) noexcept;
std::uintptr_t InvokeWarPaymentGateway12004(const WarPaymentBindings12004 &,
  WarPaymentGatewayOriginal12004, void *character, std::int32_t resource,
  std::int64_t amount, std::int32_t component, std::uintptr_t actual_caller_return_rva) noexcept;
std::uintptr_t InvokeWarPaymentWriter12004(const WarPaymentBindings12004 &,
  WarPaymentWriterOriginal12004, WarPaymentKind12004, void *wrapper,
  std::int64_t amount, void *character, std::uintptr_t actual_caller_return_rva) noexcept;
} // namespace xar::ck3_12004
