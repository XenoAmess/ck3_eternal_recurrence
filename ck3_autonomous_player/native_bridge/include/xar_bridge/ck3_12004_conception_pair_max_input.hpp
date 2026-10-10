#pragma once

#include "xar_bridge/ck3_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kConceptionLineageTierMaxRva = 0x2B94DC0;
using ConceptionPairMaxReadMemory = bool (*)(
    void *context, const void *address, void *output, std::size_t bytes) noexcept;
using NativeConceptionLineageTierMax = std::int32_t (*)(void *character);

struct ConceptionPairMaxInputBindings {
  bool enabled = false;
  std::string_view unavailable_reason = "binding_unavailable";
  NativeConceptionLineageTierMax read_lineage_tier_max = nullptr;
  ConceptionPairMaxReadMemory read_memory = nullptr;
  void *memory_context = nullptr;
};

enum class ConceptionPairMaxReturnRole : std::uint8_t { first, second };

struct ConceptionPairMaxInput {
  std::string_view status = "unavailable";
  std::string_view unavailable_reason = "binding_unavailable";
  std::uint32_t first_full_id = 0xFFFFFFFFU;
  std::uint32_t second_full_id = 0xFFFFFFFFU;
  std::optional<std::int32_t> first_lineage_tier_max_raw;
  std::optional<std::int32_t> second_lineage_tier_max_raw;
  std::optional<std::int32_t> pair_lineage_tier_max_raw;
  // Source of B98/B9A maximum only. The downstream RCX role at BA5 is
  // selected earlier by its independently owned provider branch.
  std::optional<ConceptionPairMaxReturnRole> maximum_return_role;
};

ConceptionPairMaxInputBindings BindConceptionPairMaxInputImage(
    std::string_view build_version, std::string_view executable_sha256,
    std::uintptr_t module_base, ConceptionPairMaxReadMemory read_memory,
    void *memory_context) noexcept;

// Caller supplies the existing current household's resolved role pointers and
// full-ID/frame guard. This API selects no pair and changes no native state.
ConceptionPairMaxInput ReadConceptionPairMaxInput(
    const ConceptionPairMaxInputBindings &bindings,
    std::uintptr_t first, std::uint32_t first_full_id,
    std::uintptr_t second, std::uint32_t second_full_id) noexcept;

} // namespace xar::ck3_12004
