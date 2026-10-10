#pragma once
#define XAR_ARMY_GATHERING_DUE_NATURAL_12004_READY 1
#include "xar_bridge/army_natural_phase_scope_12004.hpp"
#include <array>
#include <string>
#include <string_view>

namespace xar::ck3_12004 {
inline constexpr std::uintptr_t kArmyGatheringDueNaturalRva12004 = 0x2A9AF20;
inline constexpr std::uintptr_t kArmyGatheringDueNaturalReturnRva12004 = 0x2A9A67D;

struct ArmyGatheringDueNativeList12004 {
  std::optional<std::uintptr_t> buffer_identity;
  std::optional<std::int32_t> capacity, count;
  bool complete = false;
  std::vector<std::uint32_t> ordered_full_ids;
};
struct ArmyGatheringDuePhysical12004 {
  std::uint32_t requested_full_id = 0;
  std::uintptr_t physical_identity = 0;
  bool resolution_complete = false, used_native_fallback = false;
  std::optional<std::uint32_t> selected_full_id, magic;
};
struct ArmyGatheringDueChunk12004 {
  std::int32_t ordinal = 0;
  std::uintptr_t physical_identity = 0;
  std::optional<std::int32_t> maximum, current, stored_ordinal, state;
  std::optional<std::uint32_t> owner_full_id, association_full_id;
  std::optional<std::uint8_t> byte14;
  std::optional<std::uint64_t> date_raw64;
};
struct ArmyGatheringDuePersistent12004 {
  ArmyGatheringDuePhysical12004 receiver;
  std::optional<std::int64_t> prepared148;
  std::vector<ArmyGatheringDueChunk12004> chunks;
};
struct ArmyGatheringDueReference12004 {
  std::uintptr_t source_ref_identity = 0;
  std::optional<std::uint32_t> owner_full_id;
  std::optional<std::int32_t> ordinal;
  ArmyGatheringDuePhysical12004 receiver;
  std::optional<ArmyGatheringDueChunk12004> chunk;
};
struct ArmyGatheringDueRecord12004 {
  std::uintptr_t physical_identity = 0;
  std::optional<std::int32_t> date_low32, pending_count, character_count;
  bool pending_refs_complete = false, character_ids_complete = false;
  std::vector<ArmyGatheringDueReference12004> pending_refs;
  std::vector<std::uint32_t> character_full_ids;
};
struct ArmyGatheringDueArRg12004 {
  ArmyGatheringDuePhysical12004 receiver;
  std::optional<std::int32_t> current38, maximum3c, state14c;
  std::optional<std::uint32_t> army140, owner144, character148;
  std::optional<std::uintptr_t> source_refs_identity;
  std::optional<std::int32_t> source_ref_count;
  bool source_refs_complete = false;
  std::vector<ArmyGatheringDueReference12004> source_refs;
};
struct ArmyGatheringDueArmy12004 {
  ArmyGatheringDuePhysical12004 receiver;
  std::optional<std::uint32_t> unit124, combat128;
  ArmyGatheringDuePhysical12004 combat_receiver;
  std::optional<bool> source_combat_skip;
  std::optional<std::int32_t> gathering_count;
  std::optional<std::uintptr_t> gathering_buffer_identity;
  bool gathering_records_complete = false;
  std::vector<ArmyGatheringDueRecord12004> gathering_records;
  ArmyGatheringDueNativeList12004 arrg_roster;
  std::vector<ArmyGatheringDueArRg12004> arrg;
  std::optional<std::array<std::uint8_t, 80>> statistics130;
  std::optional<std::uint64_t> finished_date190;
};
struct ArmyGatheringDueSnapshot12004 {
  std::uintptr_t primary_identity = 0, date_pointer_identity = 0;
  ArmyNaturalPhaseEvent12004 event;
  std::optional<std::uint64_t> passed_date_raw64, game_state_date_raw64;
  std::optional<std::uint32_t> absolute_day_raw;
  std::optional<std::uint8_t> current_c0_raw;
  ArmyGatheringDueNativeList12004 queue158, persistent_roster30, army_roster50;
  std::vector<ArmyGatheringDueArmy12004> queued_armies, roster_armies;
  std::vector<ArmyGatheringDuePersistent12004> persistent;
  // Physical rereads selected by immutable entry refs; removed record memory is
  // never reread. These retain the entry source-ref token, not its freed bytes.
  std::vector<ArmyGatheringDueReference12004> entry_due_refs_at_return;
  std::vector<std::uint32_t> entry_queue_extent_backing_full_ids;
  bool entry_queue_extent_backing_complete = false;
  bool all_declared_reads_complete = false;
  std::vector<std::string> missing_fields;
};
struct ArmyGatheringDueNaturalBindings12004 {
  bool exact_build_enabled = false;
  std::uintptr_t image_base = 0;
  void *read_context = nullptr;
  ArmyNaturalPhaseRead12004 read = nullptr;
  std::size_t maximum_occurrences = 4096, maximum_records = 256, maximum_read_operations = 65536;
};
#if defined(_MSC_VER)
using ArmyGatheringDueNaturalOriginal12004 = std::uintptr_t(__fastcall *)(void *, const void *);
#else
using ArmyGatheringDueNaturalOriginal12004 = std::uintptr_t (*)(void *, const void *);
#endif
struct ArmyGatheringDueNaturalStage12004 {
  bool observed = false, original_called = false, original_returned = false;
  bool actual_boundary_admitted = false, actual_poststage_observed = false;
  std::uintptr_t actual_return_rva = 0, raw_return_bits = 0;
  std::optional<std::uint8_t> actual_saved_mask;
  std::optional<bool> saved_mask_parent_observation_admitted;
  ArmyNaturalPhaseScope12004 parent;
  ArmyGatheringDueSnapshot12004 entry, returned;
  std::optional<bool> same_clock_thread_order, active_parent_unchanged;
  std::string unavailable_reason;
};
ArmyGatheringDueNaturalBindings12004 BindArmyGatheringDueNaturalStage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    void *read_context = nullptr, ArmyNaturalPhaseRead12004 read = nullptr) noexcept;
struct ArmyGatheringDueNaturalHook12004 {
  ArmyGatheringDueNaturalBindings12004 bindings;
  bool complete_source_proof = false, primary_thread_suspended_proven = false, installed = false;
  std::uintptr_t entry_trampoline_identity = 0, entry_thunk_identity = 0;
  std::string unavailable_reason;
};
ArmyGatheringDueNaturalHook12004 BindArmyGatheringDueNaturalHook12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
bool InstallArmyGatheringDueNaturalHook12004(ArmyGatheringDueNaturalHook12004 &) noexcept;
// Root entry thunk supplies actual67D and, only if register-captured, R13b mask.
// The original receives its unmodified two arguments, is called once, and returns
// opaque native RAX bits unchanged. No lookup getter or native mutator is called.
ArmyGatheringDueNaturalStage12004 InvokeArmyGatheringDueNatural12004(
    const ArmyGatheringDueNaturalBindings12004 &, ArmyGatheringDueNaturalOriginal12004,
    void *primary, const void *date_pointer, std::uintptr_t actual_return_rva,
    std::optional<std::uint8_t> actual_saved_mask = std::nullopt) noexcept;
std::vector<ArmyGatheringDueNaturalStage12004> ReadArmyGatheringDueNaturalJournal12004();
std::vector<ArmyGatheringDueNaturalStage12004> ReadArmyGatheringDueNaturalForArmy12004(std::uint32_t owned_full_id);
void ClearArmyGatheringDueNaturalJournal12004() noexcept;
} // namespace xar::ck3_12004
