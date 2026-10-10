#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004 {

using ConceptionPairListBonus12004ReadMemory =
    bool (*)(void *, const void *, void *, std::size_t) noexcept;

struct ConceptionPairListBonus12004Bindings {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  ConceptionPairListBonus12004ReadMemory read_memory = nullptr;
  void *read_context = nullptr;
};

struct ConceptionPairListBonus12004Read {
  std::string_view status = "unavailable";
  std::string_view unavailable_reason = "conception_pair_list_binding_unavailable";
  std::optional<bool> primary_relation_match;
  // Absent when the native caller did not evaluate this input.
  std::optional<std::int32_t> first_child_count_raw;
  std::optional<std::int32_t> second_child_count_raw;
  std::optional<bool> first_list_has_second_parent_witness;
  std::optional<bool> second_list_has_first_parent_witness;
  std::optional<bool> either_land_state_present;
  std::optional<bool> apply_relation_bonus;
  std::optional<bool> apply_land_state_bonus;
};

ConceptionPairListBonus12004Bindings BindConceptionPairListBonus12004(
    std::uintptr_t image_base, std::string_view build,
    std::string_view executable_sha256,
    ConceptionPairListBonus12004ReadMemory read_memory,
    void *read_context = nullptr) noexcept;

// Pure conditional model of 2B9606E..2B960F4. Unknown required inputs stay
// unknown. A native short-circuit does not require unconsumed inputs.
std::optional<bool> ConceptionPairRelationBonusCondition12004(
    bool primary_relation_match,
    std::optional<std::int32_t> first_count,
    std::optional<std::int32_t> second_count,
    std::optional<bool> first_witness,
    std::optional<bool> second_witness) noexcept;

// Root supplies two independently resolved household Character receivers and
// full IDs in its existing application-thread frame. No game calls or writes.
// The child-list helper retains full-generation resolution and native default
// Character fallback. This reports bonus conditions, not loaded scalar values.
ConceptionPairListBonus12004Read ReadConceptionPairListBonusForCharacters12004(
    const ConceptionPairListBonus12004Bindings &bindings,
    std::uintptr_t first, std::uint32_t first_full_id,
    std::uintptr_t second, std::uint32_t second_full_id) noexcept;

} // namespace xar::ck3_12004
