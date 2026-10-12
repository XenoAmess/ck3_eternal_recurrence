#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12003_mercenary_candidates.hpp"
#include "xar_bridge/ck3_12003_player_holy_order_context.hpp"

#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12004 {

enum class PrewarHiredKind12004 { mercenary, holy_order };

struct PrewarHiredChunk12004 {
  std::int32_t chunk_index = -1;
  std::optional<std::int32_t> maximum_soldiers_raw; // Diagnostic; not future strength.
  std::optional<std::int32_t> current_soldiers_raw;
  std::optional<std::int32_t> persistent_regiment_backlink;
  std::optional<std::int32_t> native_chunk_index;
  std::optional<std::int32_t> army_regiment_id;
  std::optional<std::uint8_t> pending_raw;
  std::optional<std::int32_t> state_raw;
  bool fields_copied = false;
  bool identity_ready = false;
  bool operator==(const PrewarHiredChunk12004 &) const = default;
};

struct PrewarHiredRegiment12004 {
  std::int32_t source_index = -1;
  std::int32_t persistent_regiment_id = -1;
  std::optional<std::int32_t> observed_full_id;
  std::optional<std::uint32_t> observed_magic;
  // This is the persistent object's owner, not its service employer.
  std::optional<std::int32_t> persistent_owner_character_id;
  std::optional<std::int32_t> native_capacity_raw;
  std::vector<PrewarHiredChunk12004> chunks;
  bool available = false;
  std::string failure;
  bool operator==(const PrewarHiredRegiment12004 &) const = default;
};

struct PrewarHiredOrganisation12004 {
  PrewarHiredKind12004 kind = PrewarHiredKind12004::mercenary;
  std::int32_t registry_slot_index = -1;
  std::int32_t full_id = -1;
  std::uint32_t magic = 0;
  std::optional<std::int32_t> employer_character_id;
  bool registry_identity_ready = false;
  bool selected_employer = false;
  bool employer_identity_ready = false;
  std::optional<bool> military_kind;
  // Authoritative stock current getter, whole soldiers. It includes the
  // organisation holder's knights and native state3/current0 semantics.
  // Keep it separate from physical raw chunks; it is not future maximum,
  // actual map arrival, an additive physical lower bound or new hire credit.
  std::optional<std::int32_t> native_current_soldiers;
  bool native_current_ready = false;
  std::optional<std::int32_t> source_regiment_capacity;
  std::optional<std::int32_t> source_regiment_count;
  bool persistent_roster_complete = false;
  std::int32_t duplicate_persistent_occurrences = 0;
  std::vector<PrewarHiredRegiment12004> regiments;
  std::string failure;
  bool operator==(const PrewarHiredOrganisation12004 &) const = default;
};

struct PrewarHiredEmployer12004 {
  std::int32_t character_id = -1;
  bool identity_ready = false;
  // These two flags qualify complete organisation stock-current enumeration,
  // independently of copied physical Regi/chunk coverage below.
  bool mercenary_inventory_complete = false;
  bool holy_order_inventory_complete = false;
  bool physical_hired_rosters_complete = false;
  // An upper bound for currently hired stock only. Repeated physical keys
  // and holder knights may overcount, which is allowed for an upper bound.
  // Callers must not add these values to a physical lower bound.
  std::optional<std::int64_t> hired_stock_current_upper_bound;
  std::string failure;
  bool operator==(const PrewarHiredEmployer12004 &) const = default;
};

struct PrewarHiredInventory12004 {
  bool exact_build_ready = false;
  bool mercenary_registry_complete = false;
  bool holy_order_registry_complete = false;
  std::optional<std::int32_t> mercenary_registry_capacity;
  std::optional<std::int32_t> holy_order_registry_capacity;
  std::int32_t mercenary_slots_scanned = 0;
  std::int32_t holy_order_slots_scanned = 0;
  bool selected_physical_rosters_complete = false;
  std::vector<PrewarHiredEmployer12004> employers;
  std::vector<PrewarHiredOrganisation12004> organisations;
  // No actual4 complete special/event troop group enumeration is admitted by
  // this hired-category reader. Missing categories never become known zero.
  bool special_inventory_complete = false;
  std::string special_inventory_failure = "special_event_troop_inventory_not_sampled_by_hired_reader";
  bool all_military_inventory_complete = false;
  std::string failure;
  bool operator==(const PrewarHiredInventory12004 &) const = default;
};

// Returns complete selected organisation STOCK-current observation only;
// physical roster completeness is independent and overall military is unclosed.
// One sample on the caller's paused application-main ticket. Bind all inputs
// using their actual4 binders; caller compares complete owning DTOs across the
// aggregate two rounds. Native pointers remain local and never enter output.
// Source owners: ck3_12004_mercenary_bindings.cpp and
// ck3_12004_holy_order_bindings.cpp, with their source-closed .4 field ledgers.
// Physical union key is (full persistent_regiment_id, chunk_index) across ALL
// personal/hired/allied sources; category/employer are attribution, not keys.
bool ReadPrewarHiredInventory12004(
    const ck3_12003::mercenary::CandidateBindings &mercenary,
    const ck3_12003::religion::holy_order::Bindings &holy_order,
    const ck3_12002::CoreBindings &core,
    const ck3_12002::ArmyBindings &armies,
    std::string_view executable_sha256,
    std::span<const std::int32_t> selected_employer_ids,
    PrewarHiredInventory12004 &output) noexcept;

} // namespace xar::ck3_12004
