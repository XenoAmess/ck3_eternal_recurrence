#pragma once

#include "xar_bridge/ck3_12004_person_following_2922680.hpp"

namespace xar::ck3_12004 {

inline constexpr char kPersonLocalTitles12004Schema[] =
    "xar.ck3.person-local-titles-12004-v1";

// A family is an ordered list of raw PC constituents. Unit100000 folds form
// one local composite; these constituents are not separate outer requests.
struct PersonLocalTitlesPcFamily12004 {
  bool ready = false;
  std::string reason;
  std::optional<std::uintptr_t> array_identity;
  std::optional<std::int32_t> count_i32;
  std::vector<PersonFollowing2922680Pc> source_pcs;
  std::optional<bool> known_empty;
  friend bool operator==(const PersonLocalTitlesPcFamily12004 &,
                         const PersonLocalTitlesPcFamily12004 &) = default;
};

// Ordered supplemental ID occurrences; skipped fields remain null. The search
// prefix ends at the first full-DWORD match, unread element, or array end.
struct PersonLocalTitlesSupplementalRow12004 {
  std::uint32_t native_index = 0;
  bool ready = false;
  std::string reason;
  std::optional<std::uint32_t> requested_full_id_u32;
  PersonFollowing2922680Resolution resolution;
  std::optional<std::uintptr_t> definition_identity;
  std::optional<std::int32_t> definition_gate_224_i32;
  std::optional<std::uint8_t> object_gate_18_u8;
  std::optional<bool> rite_id_demanded;
  std::optional<std::uint32_t> character_rite_full_id_u32;
  PersonFollowing2922680Resolution rite_resolution;
  std::optional<std::uintptr_t> membership_array_identity;
  std::optional<std::int32_t> membership_count_i32;
  std::optional<std::uint32_t> rite_membership_key_u32;
  std::vector<std::optional<std::uint32_t>> membership_full_ids_u32;
  std::optional<std::uint32_t> first_match_index;
  std::optional<std::uintptr_t> match_identity;
  std::optional<bool> admitted;
  PersonFollowing2922680Pc source_pc;
  friend bool operator==(const PersonLocalTitlesSupplementalRow12004 &,
                         const PersonLocalTitlesSupplementalRow12004 &) = default;
};

struct PersonLocalTitlesSupplementalFamily12004 {
  bool ready = false;
  std::string reason;
  std::optional<std::uintptr_t> array_identity;
  std::optional<std::int32_t> count_i32;
  std::optional<bool> known_empty;
  std::vector<PersonLocalTitlesSupplementalRow12004> rows;
  friend bool operator==(const PersonLocalTitlesSupplementalFamily12004 &,
                         const PersonLocalTitlesSupplementalFamily12004 &) = default;
};

struct PersonLocalTitlesRow12004 {
  std::uint32_t native_index = 0;
  bool input_ready = false;
  bool ready = false;
  std::string reason;
  std::optional<std::uint32_t> requested_title_full_id_u32;
  PersonFollowing2922680Resolution resolution;
  std::optional<std::uint32_t> selected_title_full_id_u32;
  std::optional<std::uint8_t> exclusion_byte_130_u8;
  std::optional<std::int32_t> exclusion_dword_12c_i32;
  std::optional<bool> native_contribution_eligible;
  std::string exclusion = "unavailable";
  std::optional<std::uintptr_t> template_identity;
  std::optional<std::int32_t> template_tier_i32;
  // Composer291ECB0: Title228/count234, each pointer+D8, inner unit100000.
  PersonLocalTitlesPcFamily12004 composer;
  // Parent291E3A0's distinct tier1/tier2 constituents remain separate.
  PersonLocalTitlesPcFamily12004 primary;
  PersonLocalTitlesSupplementalFamily12004 supplemental;
  // Compatibility mirrors of the typed supplemental family.
  std::optional<std::uintptr_t> supplemental_array_identity;
  std::optional<std::int32_t> supplemental_count_i32;
  bool supplemental_ready = false;
  std::string supplemental_reason;
  friend bool operator==(const PersonLocalTitlesRow12004 &,
                         const PersonLocalTitlesRow12004 &) = default;
};

struct PersonLocalTitles12004DTO {
  std::string build_version;
  std::string executable_sha256;
  bool ready = false;
  std::string reason;
  // Input and composer readiness are independently useful across primary gaps.
  bool family_input_ready = false;
  bool composer_ready = false;
  bool primary_ready = false;
  bool supplemental_ready = false;
  std::optional<bool> family_known_zero;
  std::optional<std::uint32_t> character_id;
  std::optional<std::uintptr_t> character_identity;
  std::optional<std::uintptr_t> selected_model_identity;
  std::optional<std::uintptr_t> destination_pc_identity;
  std::optional<std::uintptr_t> character_context_1c0_identity;
  std::string header_selection = "unavailable";
  std::optional<std::uintptr_t> header_identity;
  std::optional<std::uintptr_t> array_identity;
  std::optional<std::int32_t> count_i32;
  std::vector<PersonLocalTitlesRow12004> rows;
  // This leaf is only local titles, never the first2B986B0 vector/full helper.
  bool full_helper_ready = false;
  std::string full_helper_reason = "actual2b986b0_vector_unobserved";
  friend bool operator==(const PersonLocalTitles12004DTO &,
                         const PersonLocalTitles12004DTO &) = default;
};

PersonLocalTitles12004DTO ReadPersonLocalTitlesForCharacter12004(
    const PersonCarrierDirect12004Bindings &bindings,
    std::uintptr_t actual_character);
std::string SerializePersonLocalTitles12004(const PersonLocalTitles12004DTO &dto);

} // namespace xar::ck3_12004
