#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>
#include <vector>

namespace xar::ck3_12004 {

using ConceptionOffspringCount12004ReadMemory =
    bool (*)(void *context, const void *address, void *output,
             std::size_t size) noexcept;

struct ConceptionOffspringCount12004Bindings {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  ConceptionOffspringCount12004ReadMemory read_memory = nullptr;
  void *read_context = nullptr;
  // A query work budget; exceeding it is unavailable, never a truncated count.
  std::size_t max_entries = 4096;
};

struct ConceptionOffspringCount12004Row {
  std::uint32_t requested_full_id = 0;
  std::optional<bool> used_character_fallback;
  std::optional<std::uint32_t> matched_full_id;
  std::optional<std::uint64_t> character_1d0_raw_u64;
  std::optional<std::int32_t> trait_count_raw_i32;
  std::optional<bool> trait_4a9_equals_one;
  std::optional<std::int32_t> first_matching_trait_id;
  std::optional<bool> counted;
};

struct ConceptionOffspringCount12004Read {
  std::string_view source = "native_conception_selected_role_offspring_count";
  std::string_view status = "unavailable";
  std::string_view unavailable_reason =
      "native_conception_offspring_binding_unavailable";
  std::optional<bool> family_component_present;
  std::optional<std::int32_t> offspring_list_count_raw_i32;
  // Actual RSI increments, consumed as signed ESI at2B95BAF. Not fertility,
  // living-child roster size, complete conception eligibility or a limit.
  std::optional<std::int32_t> native_count;
  std::vector<ConceptionOffspringCount12004Row> rows;
};

ConceptionOffspringCount12004Bindings BindConceptionOffspringCount12004(
    std::uintptr_t image_base, std::string_view build_version,
    std::string_view executable_sha256,
    ConceptionOffspringCount12004ReadMemory read_memory,
    void *read_context = nullptr, std::size_t max_entries = 4096) noexcept;

// Caller supplies the independently qualified selected first/second Character
// and complete ID in its Root-owned same-family before/after frame. This leaf
// preserves native offspring order/duplicates, generation equality, actual
// Character and trait fallbacks, and native1D0/predicate short circuits.
ConceptionOffspringCount12004Read ReadConceptionOffspringCountForCharacter12004(
    const ConceptionOffspringCount12004Bindings &bindings,
    std::uintptr_t selected_character, std::uint32_t expected_full_id) noexcept;

} // namespace xar::ck3_12004
