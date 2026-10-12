#pragma once

#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12002_military.hpp"
#include "xar_bridge/ck3_12003_army_reserve.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12004 {

enum class PrewarOwnerInventoryStatus12004 { available, partial, unavailable };

struct PrewarOwnerInventoryRequest12004 {
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t actor_character_id = -1; // Current public player root: positive.
  std::int32_t owner_character_id = -1; // Native signed32 FullID; only -1 absent.
};

struct PrewarOwnerInventoryBindings12004 {
  bool enabled = false;
  ck3_12003::PlayerArmyReserveBindingsV1 composition;
  void **persistent_regiment_storage_slot = nullptr;
  void **army_regiment_storage_slot = nullptr;
  void **domicile_storage_slot = nullptr;
  std::int64_t *(*domicile_current)(void *, std::int64_t *) = nullptr;
  bool (*domicile_owner_type_predicate)(void *) = nullptr;
};

struct PrewarOwnerIdCollection12004 {
  // A copied native composition member, not an inferred category census.
  std::string source_member;
  std::optional<bool> data_present;
  std::optional<std::int32_t> capacity;
  std::optional<std::int32_t> count;
  bool header_read_complete = false;
  bool entries_copied_complete = false;
  std::vector<std::int32_t> full_ids; // Original order and repeated occurrences.
  std::vector<std::int32_t> unique_full_ids; // First occurrence order; no sums.
  std::int32_t duplicate_full_id_occurrences = 0;
  std::string failure;
  bool operator==(const PrewarOwnerIdCollection12004 &) const = default;
};

struct PrewarOwnerPersistentChunk12004 {
  std::int32_t chunk_index = -1;
  std::optional<std::int32_t> maximum_soldiers_raw;
  std::optional<std::int32_t> current_soldiers_raw;
  std::optional<std::int32_t> persistent_regiment_id_raw;
  std::optional<std::int32_t> native_ordinal_raw;
  std::optional<std::int32_t> army_regiment_id_raw;
  std::optional<std::uint8_t> pending_raw;
  std::optional<std::int32_t> state_raw;
  bool atoms_read_complete = false;
  std::string failure;
  bool operator==(const PrewarOwnerPersistentChunk12004 &) const = default;
};

struct PrewarOwnerPersistentRegiment12004 {
  std::int32_t occurrence_index = -1;
  std::int32_t persistent_regiment_id = -1;
  std::optional<std::int32_t> observed_full_id;
  std::optional<std::uint32_t> observed_magic;
  // Native source owner can differ from the requested employer/controller.
  std::optional<std::int32_t> native_owner_character_id;
  std::optional<std::int32_t> native_capacity_raw;
  bool full_generation_ready = false;
  bool atoms_read_complete = false;
  std::vector<PrewarOwnerPersistentChunk12004> chunks;
  std::string failure;
  bool operator==(const PrewarOwnerPersistentRegiment12004 &) const = default;
};

struct PrewarOwnerKnight12004 {
  std::int32_t occurrence_index = -1;
  std::int32_t character_id = -1;
  std::optional<std::int32_t> observed_full_id;
  std::optional<std::uint32_t> observed_magic;
  // Exact count getter reads Character+1B8, then component+F8. A missing
  // component is distinct from an unread component or a stored -1 backlink.
  std::optional<bool> assignment_component_present;
  std::optional<std::int32_t> army_regiment_id_raw;
  bool full_generation_ready = false;
  bool atoms_read_complete = false;
  std::string failure;
  bool operator==(const PrewarOwnerKnight12004 &) const = default;
};

struct PrewarOwnerArmyRegiment12004 {
  std::int32_t occurrence_index = -1;
  std::int32_t army_regiment_id = -1;
  std::optional<std::int32_t> observed_full_id;
  std::optional<std::uint32_t> observed_magic;
  std::optional<std::int32_t> current_soldiers_raw;
  std::optional<std::int32_t> maximum_soldiers_raw;
  std::optional<std::int32_t> native_carmy_id_raw;
  bool full_generation_ready = false;
  bool atoms_read_complete = false;
  std::string failure;
  bool operator==(const PrewarOwnerArmyRegiment12004 &) const = default;
};

struct PrewarOwnerDomicile12004 {
  bool association_read_complete = false;
  bool association_empty = false;
  std::optional<bool> realm_present;
  std::optional<std::int32_t> domicile_id;
  std::optional<std::int32_t> observed_full_id;
  std::optional<std::uint32_t> observed_magic;
  std::optional<std::int32_t> native_owner_character_id;
  std::optional<std::int32_t> observed_native_owner_full_id;
  std::optional<std::uint32_t> observed_native_owner_magic;
  bool native_owner_identity_ready = false;
  std::optional<bool> domicile_type_present;
  std::optional<std::uint8_t> type_flag_17e;
  // Predicate takes the Domi's resolved source Character, whose own associated
  // Domi need not be the input Domi. Input type_flag_17e cannot replace it.
  std::optional<bool> native_owner_type_predicate;
  std::optional<bool> assigned_branch;
  std::optional<bool> assigned_owner_military_present;
  PrewarOwnerIdCollection12004 assigned_regiment_ids;
  std::vector<PrewarOwnerPersistentRegiment12004> assigned_regiments;
  std::optional<std::int64_t> assigned_current_accumulator;
  bool assigned_atoms_read_complete = false;
  bool assigned_accumulator_int32_ready = false;
  bool full_generation_ready = false;
  bool native_current_call_succeeded = false;
  bool native_out_echo_ready = false;
  std::optional<std::int64_t> native_current_raw_q100000;
  // Ceil of the nonnegative current getter, not future regeneration/capacity.
  std::optional<std::int64_t> current_upper_soldiers;
  bool current_ready = false;
  std::string failure;
  bool operator==(const PrewarOwnerDomicile12004 &) const = default;
};

struct PrewarOwnerInventory12004 {
  PrewarOwnerInventoryStatus12004 status = PrewarOwnerInventoryStatus12004::unavailable;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t actor_character_id = -1;
  std::int32_t owner_character_id = -1;
  std::optional<std::int32_t> observed_owner_full_id;
  std::optional<std::uint32_t> observed_owner_magic;
  std::optional<std::int32_t> composition_owner_echo_90;
  std::optional<std::int32_t> opaque_scalar_80;
  bool exact_build_ready = false;
  bool owner_identity_ready = false;
  bool constructor_succeeded = false;
  bool initializer_succeeded = false;
  bool owner_echo_ready = false;
  bool cleanup_attempted = false;
  bool cleanup_succeeded = false;
  bool native_lifetime_ready = false;
  // Current-player scope never changes to the requested foreign owner.
  // The outer aggregate still owns the main-thread ticket and whole two-pass
  // epoch comparison; this flag only qualifies this sample's before/after scope.
  bool source_frame_ready = false;
  PrewarOwnerIdCollection12004 persistent_regiment_ids;
  PrewarOwnerIdCollection12004 knight_character_ids;
  PrewarOwnerIdCollection12004 raised_army_regiment_ids;
  std::vector<PrewarOwnerPersistentRegiment12004> persistent_regiments;
  std::vector<PrewarOwnerKnight12004> knights;
  std::vector<PrewarOwnerArmyRegiment12004> raised_army_regiments;
  PrewarOwnerDomicile12004 domicile;
  bool persistent_atoms_read_complete = false;
  bool knight_atoms_read_complete = false;
  bool raised_atoms_read_complete = false;
  // EAX of the exact whole native owner-composition getter, integer scale 1.
  // Its inclusion rules differ from raw seven-chunk sums. This is observed
  // stock, not foreign command permission, delivered strength or an upper bound.
  std::optional<std::int32_t> native_all_unraised_stock;
  bool native_all_unraised_stock_call_succeeded = false;
  bool native_all_unraised_stock_ready = false;
  bool raw_capture_complete = false;
  bool current_count_atoms_valid = false;
  // All atoms of this reader's native persistent/knight/ArRg/DOMI stock scope.
  // Full levy contribution descriptors belong to the separate mask-F reader.
  bool owner_stock_inventory_complete = false;
  // The initializer replaces full levy+50 with unraised+68. This reader does
  // not capture the separately required full mask-F shares or physical owner
  // permission projection. The pure aggregate joins those with the dynamic
  // owner_stock_inventory_complete flag. No force floor/upper/completeness may
  // be inferred from raw_capture_complete alone.
  bool overall_current_inventory_complete = false;
  std::optional<std::int64_t> current_inventory_lower_bound;
  std::optional<std::int64_t> current_inventory_upper_bound;
  std::string completeness_failure = "full_levy_and_physical_permission_projection_external";
  std::string failure;
  bool operator==(const PrewarOwnerInventory12004 &) const = default;
};

PrewarOwnerInventoryBindings12004 BindPrewarOwnerInventoryImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const ck3_12002::ArmyBindings &actual4_armies) noexcept;

// One synchronous owning-thread sample. Copies native-owned arrays before a
// non-deleting cleanup; no native pointer enters the DTO. The caller supplies
// actual4 world callbacks, owns the paused main-thread ticket and compares two
// complete aggregate samples. The player-only reserve wrapper is never used.
PrewarOwnerInventoryStatus12004 ReadPrewarOwnerInventory12004(
    const PrewarOwnerInventoryBindings12004 &bindings,
    const ck3_12002::MilitaryWorldAccess &world,
    const PrewarOwnerInventoryRequest12004 &request,
    PrewarOwnerInventory12004 &output) noexcept;

} // namespace xar::ck3_12004
