#pragma once

#include "xar_bridge/ck3_12004_person_carrier_direct.hpp"

namespace xar::ck3_12004 {

inline constexpr char kPersonGovernmentGate12004Schema[] =
    "xar.ck3.person-government-gate-12004-v1";

struct PersonGovernmentGate12004Step {
  std::uint32_t native_index = 0;
  std::uintptr_t character_identity = 0;
  std::optional<std::uint32_t> magic_u32;
  std::optional<std::uint32_t> full_id_u32;
  std::optional<std::uintptr_t> death_context_identity;
  std::optional<std::uintptr_t> living_context_identity;
  std::optional<std::uintptr_t> related_context_identity;
  std::optional<std::uint32_t> related_full_id_u32;
  std::optional<std::uint32_t> registry_count_u32;
  std::optional<std::uintptr_t> registry_slots_identity;
  std::optional<std::uintptr_t> candidate_identity;
  std::optional<std::uint32_t> candidate_full_id_u32;
  std::optional<std::uintptr_t> selected_character_identity;
  std::string resolution_selection = "unavailable";
  friend bool operator==(const PersonGovernmentGate12004Step &,
                         const PersonGovernmentGate12004Step &) = default;
};

struct PersonGovernmentGate12004DTO {
  std::string build_version;
  std::string executable_sha256;
  bool ready = false;
  std::string reason;
  std::optional<std::uint32_t> character_id;
  std::uintptr_t character_identity = 0;
  // Ancillary current model attribution, not a reset/stage baseline.
  std::optional<std::uintptr_t> selected_model_identity;
  std::optional<bool> model_owner_matches;
  std::optional<std::uintptr_t> registry_identity;
  std::optional<std::uintptr_t> character_fallback_identity;
  std::optional<std::uintptr_t> government_identity;
  std::string selection = "unavailable";
  std::optional<std::uint32_t> flags_40_u32;
  std::optional<bool> bit19_set;
  std::optional<bool> branch_admitted;
  std::optional<bool> known_no_contribution;
  std::vector<PersonGovernmentGate12004Step> steps;
  friend bool operator==(const PersonGovernmentGate12004DTO &,
                         const PersonGovernmentGate12004DTO &) = default;
};

// Actual291CE04 CALL28C2DF0 followed by returned DWORD40 bit19. Only guarded
// copies; no native getter/logger, initializer, contribution or model write.
PersonGovernmentGate12004DTO ReadPersonGovernmentGateForCharacter12004(
    const PersonCarrierDirect12004Bindings &, std::uintptr_t actual_character);
std::string SerializePersonGovernmentGate12004(
    const PersonGovernmentGate12004DTO &);

} // namespace xar::ck3_12004
