#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>
#include <vector>

namespace xar::ck3_12004 {

using ConceptionRelatedPair12004ReadMemory =
    bool (*)(void *context, const void *address, void *output,
             std::size_t size) noexcept;

struct ConceptionRelatedPair12004Bindings {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  ConceptionRelatedPair12004ReadMemory read_memory = nullptr;
  void *read_context = nullptr;
};

// Raw inputs actually traversed by the closed predicate. A native null block
// has both observed parent IDs FFFFFFFF; unread fields and skipped branches
// stay absent. Full32 IDs retain generation bits. Pointers remain internal.
struct ConceptionRelatedCharacterRaw12004 {
  std::uintptr_t character = 0;
  std::optional<std::uint32_t> magic_raw_u32;
  std::optional<std::uint32_t> full_id_raw_u32;
  std::optional<bool> relationship_block_present;
  std::optional<std::uint32_t> parent_slot0_full_id;
  std::optional<std::uint32_t> parent_slot1_full_id;
};

struct ConceptionRelatedPair12004Read {
  std::string_view source = "native_conception_related_pair";
  std::string_view status = "unavailable";
  std::string_view unavailable_reason =
      "native_conception_related_pair_binding_unavailable";
  std::optional<bool> second_to_first_28b3c10;
  std::optional<bool> first_to_second_28b3c10;
  std::optional<bool> first_second_28b3e50;
  std::optional<bool> related_pair_predicate;
  std::vector<ConceptionRelatedCharacterRaw12004> raw_characters;
};

ConceptionRelatedPair12004Bindings BindConceptionRelatedPair12004(
    std::string_view build_version, std::string_view executable_sha256,
    std::uintptr_t module_base,
    ConceptionRelatedPair12004ReadMemory read_memory,
    void *read_context = nullptr) noexcept;

// Existing current-household application-thread owner supplies both resolved
// Characters and expected full IDs. This software observer calls no CK3 code.
// It reproduces only actual2912210; faith branch, existing CloseFamily and
// loaded numerical multiplier remain the parent provider's separate inputs.
ConceptionRelatedPair12004Read ReadConceptionRelatedPairForHousehold12004(
    const ConceptionRelatedPair12004Bindings &bindings,
    std::uintptr_t first_character, std::uint32_t expected_first_full_id,
    std::uintptr_t second_character,
    std::uint32_t expected_second_full_id) noexcept;

} // namespace xar::ck3_12004
