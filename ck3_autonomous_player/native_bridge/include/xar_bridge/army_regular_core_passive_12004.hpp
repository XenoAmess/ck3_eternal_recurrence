#pragma once

#include "xar_bridge/army_natural_phase_scope_12004.hpp"
#include "xar_bridge/army_scoped_ordered_refill_inputs_v1.hpp"
#include "xar_bridge/army_regular_core_readonly_access_12004.hpp"
#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>
#include <windows.h>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kArmyRegularCoreRva12004 = 0x2A98AC0;
inline constexpr std::uintptr_t kArmyRegularCoreCallerReturnRva12004 = 0x2A9A8E2;
inline constexpr std::size_t kArmyRegularCorePatchBytes12004 = 15;
inline constexpr std::size_t kArmyRegularCoreJournalCapacity12004 = 4;
inline constexpr std::string_view kArmyRegularCoreEntryKind12004 =
    "explicit_postdate_regular_core_observed_prepared148";

struct ArmyRegularCoreOccurrence12004 {
  std::int32_t stored_index = -1;
  std::optional<std::int32_t> raw_full_id;
  std::optional<std::int32_t> resolved_full_id;
  std::optional<bool> used_fallback;
  // Process-local before-frame physical address identity, never an execution ID.
  std::uintptr_t physical_token = 0;
  std::string unavailable_reason;
};
struct ArmyRegularCorePersistent12004 {
  std::uintptr_t physical_token = 0;
  std::optional<std::int32_t> resolved_full_id;
  std::optional<std::int64_t> prepared_fraction_raw;
  std::vector<game::ArmyOrderedRefillChunkV1> chunks;
  std::string unavailable_reason;
};
struct ArmyRegularCoreDataRecord12004 {
  std::int32_t record_index = -1;
  std::optional<std::int32_t> persistent_regiment_id;
  std::optional<std::int32_t> chunk_index;
  std::uintptr_t persistent_physical_token = 0;
  std::optional<std::int32_t> state_raw;
  bool native_record_admitted = false;
  std::string unavailable_reason;
};
struct ArmyRegularCoreArRg12004 {
  ArmyRegularCoreOccurrence12004 occurrence;
  std::optional<std::uint32_t> resolved_magic_14_raw;
  std::optional<bool> native_refresh_admitted;
  std::optional<bool> native_loss_writer_skipped;
  std::optional<std::int32_t> native_record_count;
  bool records_complete = false;
  std::vector<ArmyRegularCoreDataRecord12004> records;
  std::string unavailable_reason;
};
struct ArmyRegularCoreArmy12004 {
  std::uintptr_t physical_token = 0;
  std::optional<std::int32_t> resolved_full_id;
  std::optional<std::int32_t> native_arrg_occurrence_count;
  std::vector<ArmyRegularCoreArRg12004> arrg_occurrences;
  std::string unavailable_reason;
};
inline constexpr std::size_t kMaximumArmyRegularCoreSubjects12004 = 64;
// Explicit research scope is pinned before enable. It never changes the default
// full-manager collector and is never inferred from a later query.
struct ArmyRegularCoreSubjectScope12004 {
  std::uint64_t scope_epoch = 0;
  std::uintptr_t game_state_identity = 0;
  std::int32_t owner_character_id = -1;
  std::vector<std::int32_t> full_carmy_ids;
  std::vector<std::int32_t> allowed_public_unit_ids;
};
struct ArmyRegularCoreSubjectIdentity12004 {
  std::int32_t full_carmy_id = -1;
  std::optional<std::int32_t> resolved_full_carmy_id;
  std::optional<std::uint32_t> carmy_magic_14_raw;
  std::optional<std::int32_t> public_unit_id;
  std::optional<std::int32_t> unit_resolved_full_id;
  std::optional<std::uint32_t> unit_magic_14_raw;
  std::optional<std::int32_t> unit_owner_character_id;
  std::optional<std::int32_t> unit_full_carmy_id;
};
struct ArmyRegularCoreSubjectCoverage12004 {
  std::uint64_t scope_epoch = 0;
  std::uintptr_t bound_game_state_identity = 0;
  std::int32_t bound_owner_character_id = -1;
  std::vector<std::int32_t> requested_full_carmy_ids;
  bool manager_occurrences_complete = false;
  // Raw seven-slot/DATA closure only. Never full-manager cause completeness.
  bool physical_closure_complete = false;
  std::vector<ArmyRegularCoreSubjectIdentity12004> subject_identity_witnesses;
  std::vector<std::string> missing_inputs;
};
struct ArmyRegularCoreFrame12004 {
  // Complete ordered materialization. Optional branch context can remain unknown
  // and the existing conditional projector must check whichever branch it uses.
  bool capture_complete = false;
  std::optional<std::int32_t> native_persistent_occurrence_count;
  std::optional<std::int32_t> native_army_refresh_occurrence_count;
  std::vector<ArmyRegularCoreOccurrence12004> persistent_occurrences;
  std::vector<ArmyRegularCorePersistent12004> persistent_objects;
  std::vector<ArmyRegularCoreOccurrence12004> army_refresh_occurrences;
  std::vector<ArmyRegularCoreArmy12004> army_objects;
  std::vector<std::string> missing_inputs;
  std::optional<ArmyRegularCoreSubjectCoverage12004> subject_coverage_v1;
};
struct ArmyRegularCoreObservation12004 {
  // journal_sequence is retention order only; never a natural clock timestamp.
  std::uint64_t journal_sequence = 0;
  bool observed = false;
  bool original_called = false;
  bool original_returned = false;
  bool entry_provenance_complete = false;
  bool return_provenance_complete = false;
  std::uintptr_t manager_identity = 0;
  std::uintptr_t caller_return_rva = 0;
  std::uintptr_t raw_return_bits = 0;
  // Actual common TLS invocation identity. It is not the natural event clock.
  std::uint64_t native_core_invocation_token = 0;
  std::optional<std::uint64_t> parent_invocation_token;
  std::uint32_t core_invocation_nesting_depth = 0;
  bool core_carrier_published = false;
  std::uint64_t core_carrier_source_epoch = 0;
  std::optional<std::uint64_t> entry_date_raw;
  std::optional<std::uint64_t> returned_date_raw;
  ArmyNaturalPhaseScope12004 parent_scope;
  ArmyNaturalPhaseEvent12004 entry_event;
  ArmyNaturalPhaseEvent12004 returned_event;
  ArmyRegularCoreFrame12004 entry;
  // Independent return-frame capture; it never fills an absent entry value.
  ArmyRegularCoreFrame12004 returned;
  std::vector<std::string> provenance_failures;
};
struct ArmyRegularCoreJournal12004 {
  bool observer_initialized = false;
  bool observer_installed = false;
  std::uint64_t latest_journal_sequence = 0;
  std::uint64_t overwritten_events = 0;
  std::uint64_t publication_failures = 0;
  std::vector<ArmyRegularCoreObservation12004> events;
};

using ArmyRegularCoreScopeReader12004 = ArmyNaturalPhaseScope12004 (*)(void *) noexcept;
using ArmyRegularCorePairPredicate12004 = ArmyRegularCoreReadonlyPredicate12004 (*)(
    const ArmyRegularCoreReadonlyAccess12004 &, std::uintptr_t, std::uintptr_t, std::uintptr_t) noexcept;
using ArmyRegularCoreMembershipPredicate12004 = ArmyRegularCoreReadonlyPredicate12004 (*)(
    const ArmyRegularCoreReadonlyAccess12004 &, std::uintptr_t, std::int32_t) noexcept;
using ArmyRegularCoreFinalPairPredicate12004 = ArmyRegularCoreReadonlyPredicate12004 (*)(
    const ArmyRegularCoreReadonlyAccess12004 &, std::uintptr_t, std::uintptr_t) noexcept;
struct ArmyRegularCorePositionPredicates12004 {
  ArmyRegularCorePairPredicate12004 common_war_side_2C090D0 = nullptr;
  ArmyRegularCorePairPredicate12004 relation_2C09280 = nullptr;
  ArmyRegularCorePairPredicate12004 relation_2C09410 = nullptr;
  ArmyRegularCoreMembershipPredicate12004 membership_2494B40 = nullptr;
  ArmyRegularCoreMembershipPredicate12004 holder_relation_28B2800 = nullptr;
  ArmyRegularCoreFinalPairPredicate12004 final_relation_2C3A0E0 = nullptr;
};
#if defined(_MSC_VER)
using ArmyRegularCoreOriginal12004 = std::uintptr_t(__fastcall *)(void *);
#else
using ArmyRegularCoreOriginal12004 = std::uintptr_t (*)(void *);
#endif
struct ArmyRegularCoreBindings12004 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  void *read_context = nullptr;
  ArmyNaturalPhaseRead12004 read = nullptr;
  void *event_context = nullptr;
  ArmyNaturalPhaseEventReader12004 next_event = nullptr;
  void *scope_context = nullptr;
  ArmyRegularCoreScopeReader12004 read_scope = nullptr;
  ArmyRegularCorePositionPredicates12004 position_predicates;
  // A bound failure leaves a separate partial record; no truncated list is ready.
  std::size_t maximum_occurrences = 65536;
  std::size_t maximum_physical_objects = 4096;
  std::size_t maximum_total_data_records = 65536;
  std::size_t maximum_read_bytes = 4 * 1024 * 1024;
  std::optional<ArmyRegularCoreSubjectScope12004> subject_scope;
};

ArmyRegularCoreBindings12004 BindArmyRegularCoreImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
// Pure guarded reads of the exact native entry receiver. No native getter is called.
ArmyRegularCoreFrame12004 CaptureArmyRegularCoreFrame12004(
    const ArmyRegularCoreBindings12004 &, const void *primary_manager) noexcept;
// Connected fixture and natural hook share exactly this original-once seam.
ArmyRegularCoreObservation12004 InvokeArmyRegularCorePassive12004(
    const ArmyRegularCoreBindings12004 &, ArmyRegularCoreOriginal12004,
    void *primary_manager, std::uintptr_t actual_caller_return_rva) noexcept;
// Owned records only: does not resolve/read live native objects or invoke the core.
ArmyRegularCoreJournal12004 ReadArmyRegularCoreJournal12004() noexcept;
std::optional<ArmyRegularCoreJournal12004> ReadSampledArmyRegularCoreJournal12004() noexcept;
ArmyObserverResearchSamplingState12004 ReadArmyRegularCoreResearchSampling12004() noexcept;
ArmyObserverResearchSamplingState12004 SetArmyRegularCoreResearchSampling12004(bool enabled) noexcept;
// Explicit opt-in is allowed only while disabled and quiescent. IDs and public
// player membership are verified with the same guarded reader before enable.
bool SetArmyRegularCoreScopedResearchSampling12004(
    const std::vector<std::int32_t> &requested_full_carmy_ids,
    std::int32_t expected_owner_character_id,
    const std::vector<std::int32_t> &fresh_controllable_public_unit_ids) noexcept;
void ClearArmyRegularCoreJournal12004() noexcept;
bool InitializeArmyRegularCoreFixture12004(const ArmyRegularCoreBindings12004 &,
    ArmyRegularCoreOriginal12004) noexcept;

using ArmyRegularCoreAlloc12004 = void *(*)(void *, std::size_t, DWORD, DWORD) noexcept;
using ArmyRegularCoreFree12004 = bool (*)(void *, void *, std::size_t, DWORD) noexcept;
using ArmyRegularCoreProtect12004 = bool (*)(void *, void *, std::size_t, DWORD, DWORD &) noexcept;
using ArmyRegularCoreFlush12004 = bool (*)(void *, const void *, std::size_t) noexcept;
struct ArmyRegularCoreInstallEnvironment12004 {
  bool primary_thread_suspended_proven = false;
  ArmyRegularCoreBindings12004 bindings;
  std::uintptr_t target_override = 0;
  void *memory_context = nullptr;
  ArmyRegularCoreAlloc12004 allocate = nullptr;
  ArmyRegularCoreFree12004 free = nullptr;
  ArmyRegularCoreProtect12004 protect = nullptr;
  ArmyRegularCoreFlush12004 flush = nullptr;
};
struct ArmyRegularCoreDetourState12004 {
  std::atomic<bool> installed{false};
  std::atomic<std::uint32_t> failure_flags{0};
  std::uintptr_t target = 0;
  void *trampoline = nullptr;
  std::array<std::uint8_t, kArmyRegularCorePatchBytes12004> original_bytes{};
  void *memory_context = nullptr;
  ArmyRegularCoreFree12004 free = nullptr;
  ArmyRegularCoreProtect12004 protect = nullptr;
  ArmyRegularCoreFlush12004 flush = nullptr;
};
bool InstallArmyRegularCorePassive12004(ArmyRegularCoreDetourState12004 &,
    const ArmyRegularCoreInstallEnvironment12004 &, std::string_view executable_sha256) noexcept;
bool UninstallArmyRegularCorePassive12004(ArmyRegularCoreDetourState12004 &,
    bool primary_thread_suspended_proven) noexcept;
extern "C" std::uintptr_t __fastcall XarArmyRegularCoreHook12004(void *primary_manager) noexcept;

} // namespace xar::ck3_12004
