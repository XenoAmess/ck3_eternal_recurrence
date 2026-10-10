#pragma once

#include "xar_bridge/ck3_12004_person_local_titles.hpp"

namespace xar::ck3_12004 {

inline constexpr char kPersonFirstTitleVector12004Schema[] =
    "xar.ck3.person-first-title-vector-12004-v1";

struct PersonFirstTitleVectorReceiver12004 {
  bool ready = false;
  std::string reason;
  std::string selection = "unavailable";
  std::optional<std::uintptr_t> input_context_1c0_identity;
  std::optional<std::uintptr_t> input_link_1b8_identity;
  std::optional<std::uintptr_t> context_link_1c0_identity;
  std::optional<std::uintptr_t> context_candidate_28_identity;
  std::optional<std::uint32_t> candidate_magic_1c_u32;
  std::optional<std::uint32_t> candidate_full_id_18_u32;
  std::optional<std::uint32_t> requested_full_id_u32;
  PersonFollowing2922680Resolution resolution;
  std::optional<std::uintptr_t> selected_identity;
  friend bool operator==(const PersonFirstTitleVectorReceiver12004 &,
                         const PersonFirstTitleVectorReceiver12004 &) = default;
};

struct PersonFirstTitleVectorElement12004 {
  bool input_ready = false;
  bool ready = false;
  std::string reason;
  std::optional<std::uintptr_t> identity;
  std::optional<std::uintptr_t> template_identity;
  std::optional<std::int32_t> template_tier_i32;
  PersonLocalTitlesPcFamily12004 primary;
  PersonLocalTitlesPcFamily12004 composer;
  PersonLocalTitlesSupplementalFamily12004 supplemental;
  friend bool operator==(const PersonFirstTitleVectorElement12004 &,
                         const PersonFirstTitleVectorElement12004 &) = default;
};

struct PersonFirstTitleVectorCandidate12004 {
  std::uint32_t native_index = 0;
  bool ready = false;
  std::string reason;
  std::optional<bool> id_demanded;
  std::optional<std::uint32_t> requested_full_id_u32;
  PersonFollowing2922680Resolution resolution;
  std::optional<std::uint8_t> filter_byte_130_u8;
  std::optional<bool> emitted;
  std::optional<PersonFirstTitleVectorElement12004> element;
  friend bool operator==(const PersonFirstTitleVectorCandidate12004 &,
                         const PersonFirstTitleVectorCandidate12004 &) = default;
};

struct PersonFirstTitleVectorPhase12004 {
  bool ready = false;
  std::string reason;
  std::optional<bool> admitted;
  std::optional<std::uintptr_t> header_identity;
  std::optional<std::uintptr_t> array_identity;
  std::optional<std::int32_t> count_i32;
  std::optional<std::uintptr_t> title_registry_identity;
  std::optional<std::uintptr_t> title_fallback_identity;
  std::vector<PersonFirstTitleVectorCandidate12004> rows;
  friend bool operator==(const PersonFirstTitleVectorPhase12004 &,
                         const PersonFirstTitleVectorPhase12004 &) = default;
};

struct PersonFirstTitleVectorPhaseBInputs12004 {
  bool ready = false;
  std::string reason;
  std::string selection = "unavailable";
  std::optional<std::uintptr_t> subject_context_1c0_identity;
  std::optional<std::int32_t> context_count_1ec_i32;
  std::optional<std::uintptr_t> context_array_1e0_identity;
  std::optional<std::uintptr_t> alternate_root_1d0_identity;
  std::optional<std::int32_t> alternate_count_74_i32;
  std::optional<std::uintptr_t> alternate_array_68_identity;
  std::optional<std::uint32_t> initial_title_full_id_u32;
  PersonFollowing2922680Resolution initial_title_resolution;
  std::optional<std::uint32_t> second_requested_full_id_330_u32;
  PersonFollowing2922680Resolution second_resolution;
  friend bool operator==(const PersonFirstTitleVectorPhaseBInputs12004 &,
                         const PersonFirstTitleVectorPhaseBInputs12004 &) = default;
};

struct PersonFirstTitleVector12004DTO {
  std::string build_version;
  std::string executable_sha256;
  bool ready = false;
  std::string reason;
  bool source_inputs_ready = false;
  bool producer_ready = false;
  bool family_input_ready = false;
  bool primary_ready = false;
  bool composer_ready = false;
  bool supplemental_ready = false;
  std::optional<bool> family_known_zero;
  std::optional<std::uint32_t> character_id;
  std::optional<std::uintptr_t> character_identity;
  std::optional<std::uintptr_t> selected_model_identity;
  std::optional<std::uintptr_t> destination_pc_identity;
  PersonFirstTitleVectorReceiver12004 receiver;
  std::optional<std::uintptr_t> receiver_context_1c0_identity;
  std::optional<std::uint32_t> receiver_context_1b8_full_id_u32;
  PersonFirstTitleVectorPhase12004 phase_a;
  PersonFirstTitleVectorPhaseBInputs12004 phase_b_inputs;
  PersonFirstTitleVectorPhase12004 phase_b;
  // Available only when the complete producer order is known, including duplicates.
  std::optional<std::vector<std::uintptr_t>> emitted_element_identities;
  bool full_helper_ready = false;
  std::string full_helper_reason =
      "historical_post_callback_model_and_final_append_unobserved";
  friend bool operator==(const PersonFirstTitleVector12004DTO &,
                         const PersonFirstTitleVector12004DTO &) = default;
};

// Pure actual28BFC50 selection, independent of Model, Title and PC inputs.
// Caller supplies its already qualified Character. A copied null fallback is
// preserved as selected_identity{0}; no native function is invoked.
PersonFirstTitleVectorReceiver12004
ReadPersonFirstTitleVectorReceiverForCharacter12004(
    const PersonCarrierDirect12004Bindings &bindings,
    std::uintptr_t actual_character);

PersonFirstTitleVector12004DTO ReadPersonFirstTitleVectorForCharacter12004(
    const PersonCarrierDirect12004Bindings &bindings,
    std::uintptr_t actual_character);
std::string SerializePersonFirstTitleVector12004(
    const PersonFirstTitleVector12004DTO &dto);

} // namespace xar::ck3_12004
