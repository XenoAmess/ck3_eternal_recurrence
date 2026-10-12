#pragma once

#include "xar_bridge/prewar_force_allies12004.hpp"

#include <cstddef>
#include <cstdint>
#include <string_view>
#include <vector>

namespace xar::ck3_12004 {

inline constexpr std::int32_t kPrewarPotentialMaximumCharacterSlots12004 =
    1'000'000;

enum class PrewarPotentialSupporterSource12004 : std::uint32_t {
  current_bilateral_alliance = 1U << 0,
  subject_contract_endpoint = 1U << 1,
  suzerain_contract_endpoint = 1U << 2,
  confederation_member = 1U << 3,
  same_house_living_character = 1U << 4,
};

struct PrewarPotentialSupporter12004 {
  std::int32_t character_id = -1;
  std::uint32_t source_mask = 0;
  bool operator==(const PrewarPotentialSupporter12004 &) const = default;
};

struct PrewarPotentialContract12004 {
  std::int32_t contract_id = -1;
  std::uint32_t source_native_order = 0;
  bool is_owner_contract = false;
  bool identity_verified = false;
  std::int32_t subject_character_id = -1;
  std::int32_t suzerain_character_id = -1;
  bool subject_verified = false;
  bool suzerain_verified = false;
  bool operator==(const PrewarPotentialContract12004 &) const = default;
};

struct PrewarPotentialSupportersBindings12004 {
  bool enabled = false;
  ck3_12002::family_obligations_alliance::Bindings alliance;
  void **subject_contract_storage_slot = nullptr;
  void **subject_contract_fallback_slot = nullptr;
  void **confederation_storage_slot = nullptr;
  void **confederation_fallback_slot = nullptr;
};

struct PrewarPotentialSupporters12004 {
  std::int32_t owner_character_id = -1;
  bool owner_verified = false;
  bool owner_alive = false;
  bool current_allies_available = false;
  PrewarOwnerAllies12004 current_allies;

  bool land_component_present = false;
  bool contract_source_complete = false;
  std::int32_t contract_source_count = -1;
  std::int32_t contract_source_visited_count = 0;
  std::vector<std::int32_t> source_contract_ids;
  bool owner_contract_source_complete = false;
  bool owner_contract_present = false;
  std::vector<PrewarPotentialContract12004> contracts;
  std::vector<std::int32_t> unresolved_contract_ids;
  std::uint32_t unresolved_contract_endpoint_count = 0;

  std::int32_t confederation_id = -1;
  bool confederation_source_complete = false;
  std::int32_t confederation_source_count = -1;
  std::int32_t confederation_source_visited_count = 0;
  std::vector<std::int32_t> source_confederation_character_ids;

  bool owner_house_observed = false;
  std::int32_t owner_house_id = -1;
  bool same_house_source_complete = false;
  bool whole_character_scan_required = false;
  bool whole_character_scan_complete = false;
  bool character_storage_owner_seen = false;
  std::int32_t character_storage_capacity = -1;
  std::int32_t character_storage_visited_count = 0;
  std::int32_t character_storage_non_null_count = 0;
  std::int32_t character_storage_dead_count = 0;
  std::vector<std::uint32_t> unresolved_character_slot_indices;
  // Internal census summary only: slot order, raw object address, full ID,
  // liveness and House ID are mixed into both words. Do not export a census.
  // Equality of these fingerprints is a consistency check, not byte equality
  // of a retained whole-character inventory or cryptographic identity proof.
  std::uint64_t character_census_fingerprint_a = 0;
  std::uint64_t character_census_fingerprint_b = 0;

  std::vector<std::int32_t> unresolved_character_ids;
  std::vector<std::int32_t> dead_source_character_ids;
  std::vector<PrewarPotentialSupporter12004> candidates;
  bool covered_source_subset_complete = false;
  // Liege, diarch, religious followers and selected-CB initial participants
  // belong to separate, explicitly merged source domains. This leaf never
  // sets this full-domain claim true, even when its covered subset is complete.
  bool complete_all_potential_supporters = false;
  std::string_view declared_overapproximation_scope =
      "current_alliances_contract_endpoints_confederation_same_house";
  std::string_view reason;

  bool operator==(const PrewarPotentialSupporters12004 &) const = default;
};

PrewarPotentialSupportersBindings12004 BindPrewarPotentialSupportersImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// One passive owning-application-thread sample. Keep the genuine player frame
// separate from owner. The aggregate supplies exact4 admission, its main-thread
// ticket, two whole DTO samples and post-capture frame validation.
// True includes a partial sample; completeness is explicit. False denotes an
// unavailable binding/frame/owner/capture. Actual source rows are retained on
// partial results, and unobserved counts remain -1 rather than invented zero.
// Candidates are a conservative superset for the declared source subset. No
// faith/playability/House-head/DLC/cost/answer filter or CanSend prediction is
// applied. A cap above 1,000,000 refuses the whole-character scan without
// truncating it into a complete result. Native House=-1 is observed empty.
bool ReadPrewarPotentialSupporters12004(
    const PrewarPotentialSupportersBindings12004 &bindings,
    const ck3_12002::CoreSnapshotPrefix &frame,
    std::int32_t owner_character_id, PrewarPotentialSupporters12004 &output,
    std::string_view *reason = nullptr) noexcept;

} // namespace xar::ck3_12004
