#pragma once

#include "xar_bridge/construction_scaled_key_2c4d530_12004.hpp"
#include <array>
#include <cstdint>
#include <optional>
#include <string>

namespace xar::ck3_12004::construction_owner_mode3 {

struct ContextNumericKey2C23340V1 {
  bool observed = false;
  std::string unavailable_input;
  std::uint32_t source_pc = 0;
  std::uintptr_t raw_context = 0;
  std::uint32_t incoming_key_raw_u32 = 0;
  std::uint16_t property_key_u16 = 0;
  std::uintptr_t raw_store = 0;
  std::uintptr_t raw_default_object = 0;
  std::optional<std::uint32_t> context_738_full_id;
  std::uintptr_t selected_raw_object = 0;
  std::uintptr_t candidate_character = 0;
  bool candidate_character_accepted = false;
  std::uintptr_t selected_character = 0;
  std::optional<std::uint32_t> selected_character_physical_full_id;
  bool used_final_character_default = false;
  std::uintptr_t context_848_payload = 0;
  std::optional<std::uint32_t> context_848_magic;
  std::array<std::uintptr_t, 3> collection_pointers{};
  std::array<std::optional<ScaledCollectionKey12004>, 3> collection_values;
  std::optional<std::int64_t> signed_qword_raw;
};

// Exact reached flag0/NULL-detail branch only. Context identity, Province/slot
// association and current paused frame remain03's outer before/after guard.
// The function never assumes context==Province, reads context+10 or calls CK3.
// Source-selected raw objects and Character defaults retain full-generation
// checks; missing source inputs never become a zero contribution.
ContextNumericKey2C23340V1 ReadContextNumericKey2C23340V1(
    const LoadedInputAccessV1 &access, std::uintptr_t module_base,
    std::uintptr_t raw_context, std::uint32_t raw_key);

std::int64_t SumContextNumericKey2C23340V1(
    std::int64_t first, std::int64_t second, std::int64_t third) noexcept;

} // namespace xar::ck3_12004::construction_owner_mode3
