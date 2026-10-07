#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {

// Standalone DTO with the existing resolution wire shape. This avoids a
// game_contract include cycle when the additive leaf is attached there.
struct ArmyCharacterDetachmentResolutionV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::string> unavailable_reason;
  std::optional<std::uint32_t> requested_full_id_u32;
  std::optional<bool> registry_loaded;
  std::optional<std::uint32_t> registry_capacity_u32, registry_index_u32;
  std::optional<std::string> indexed_identity;
  std::optional<std::uint32_t> indexed_full_id_u32;
  std::optional<std::string> selection;
  std::optional<bool> used_fallback;
  std::optional<std::string> object_identity;
  std::optional<std::uint32_t> selected_full_id_u32;
  friend bool operator==(const ArmyCharacterDetachmentResolutionV1 &,
                         const ArmyCharacterDetachmentResolutionV1 &) = default;
};

struct ArmyCurrentCharacterDetachmentRequestV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::string> unavailable_reason;
  std::int32_t seed_incoming_native_index = 0;
  std::optional<std::string> arrg_identity;
  std::optional<std::uint32_t> character_full_id_148_u32;
  ArmyCharacterDetachmentResolutionV1 character_resolution{};
  std::optional<std::string> passed_province_identity;
  std::optional<bool> current_extension_1b8_present;
  std::optional<std::string> current_extension_1b8_identity;
  std::optional<std::uint32_t> extension_f8_raw_u32;
  std::optional<std::int64_t> extension_100_raw64;
  bool extension_reset_inputs_ready = false;
  bool source_chain_ready = false;
  ArmyCharacterDetachmentResolutionV1 arrg_resolution{};
  std::optional<std::uint32_t> army_full_id_140_u32;
  ArmyCharacterDetachmentResolutionV1 army_resolution{};
  std::optional<std::uint32_t> unit_full_id_124_u32;
  ArmyCharacterDetachmentResolutionV1 unit_resolution{};
  friend bool operator==(const ArmyCurrentCharacterDetachmentRequestV1 &,
                         const ArmyCurrentCharacterDetachmentRequestV1 &) = default;
};

struct ArmyCurrentCharacterDetachmentInputsV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::string> unavailable_reason;
  bool seed_selection_ready = false, seed_roster_ready = false;
  std::optional<std::int64_t> current_date_storage_raw64;
  std::optional<std::string> source_parent_identity;
  std::vector<ArmyCurrentCharacterDetachmentRequestV1> requests;
  friend bool operator==(const ArmyCurrentCharacterDetachmentInputsV1 &,
                         const ArmyCurrentCharacterDetachmentInputsV1 &) = default;
};

} // namespace xar::game

namespace xar::ck3_12004 {
struct CurrentCharacterDetachmentBindings12004 {
  bool enabled = false;
  const void *source_parent = nullptr;
};
} // namespace xar::ck3_12004
