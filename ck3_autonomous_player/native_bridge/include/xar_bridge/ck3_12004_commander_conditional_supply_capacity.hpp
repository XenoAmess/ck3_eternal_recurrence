#pragma once

#include <algorithm>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12004 {

// Actual2C53BF0..2C541F9, null-details path. This is a conditional read of
// the candidate's current aggregate, never an applied commander assignment.
inline constexpr std::uintptr_t kCommanderCapacityRva12004 = 0x2C53BF0;
inline constexpr std::uintptr_t kCommanderCapacityLoadedFullRva12004 = 0x5C68C70;
inline constexpr std::int32_t kCommanderCapacityAdditiveModifier12004 = 0x1D3;
inline constexpr std::int32_t kCommanderCapacityMultiplicativeModifier12004 = 0x1D4;

struct CommanderConditionalSupplyCapacity12004 {
  std::string_view status = "unavailable";
  std::optional<std::int32_t> source_character_id;
  std::optional<std::int64_t> loaded_full_raw;
  std::optional<std::int64_t> additive_modifier_raw;
  std::optional<std::int64_t> multiplicative_modifier_raw;
  std::optional<std::int64_t> conditional_capacity_raw;
  std::string_view unavailable_reason = "candidate_not_read";
};

constexpr std::int64_t CapacityWrapAdd12004(std::int64_t a,
                                          std::int64_t b) noexcept {
  return std::bit_cast<std::int64_t>(std::bit_cast<std::uint64_t>(a) +
                                   std::bit_cast<std::uint64_t>(b));
}
constexpr std::int64_t CapacityWrapMul12004(std::int64_t a,
                                          std::int64_t b) noexcept {
  return std::bit_cast<std::int64_t>(std::bit_cast<std::uint64_t>(a) *
                                   std::bit_cast<std::uint64_t>(b));
}
constexpr std::int64_t CapacityWrapSub12004(std::int64_t a,
                                          std::int64_t b) noexcept {
  return std::bit_cast<std::int64_t>(std::bit_cast<std::uint64_t>(a) -
                                   std::bit_cast<std::uint64_t>(b));
}

// Preserve both native Q100000 multiplication branches, including the low64
// IMULs in the large-operand decomposition. This is not bigint product/division.
constexpr std::int64_t CommanderCapacityFixedMul12004(
    std::int64_t a, std::int64_t b) noexcept {
  const auto bounded = [](std::int64_t value) constexpr {
    return std::bit_cast<std::uint64_t>(value) + std::uint64_t{0xB504F333} <=
           std::uint64_t{0x16A09E666};
  };
  if (bounded(a) && bounded(b)) return CapacityWrapMul12004(a, b) / 100000;
  const auto greater = std::max(a, b);
  const auto lesser = std::min(a, b);
  const auto quotient = greater / 100000;
  const auto remainder = CapacityWrapSub12004(
      greater, CapacityWrapMul12004(quotient, 100000));
  return CapacityWrapAdd12004(CapacityWrapMul12004(remainder, lesser) / 100000,
                             CapacityWrapMul12004(quotient, lesser));
}

using CommanderCapacityModifierReader12004 =
    std::int64_t *(*)(void *, std::int64_t *, std::int32_t);

inline void InvalidateCommanderConditionalCapacity12004(
    CommanderConditionalSupplyCapacity12004 &value,
    std::string_view reason) noexcept {
  value.status = "unavailable";
  value.conditional_capacity_raw.reset();
  value.unavailable_reason = reason;
}

inline CommanderConditionalSupplyCapacity12004
ReadCommanderConditionalSupplyCapacity12004(
    std::int32_t character_id, void *aggregate,
    std::optional<std::int64_t> loaded_full,
    CommanderCapacityModifierReader12004 read_modifier) noexcept {
  CommanderConditionalSupplyCapacity12004 value;
  if (character_id >= 0) value.source_character_id = character_id;
  value.loaded_full_raw = loaded_full;
  if (!loaded_full) {
    value.unavailable_reason = "loaded_full_unavailable";
    return value;
  }
  if (character_id < 0 || aggregate == nullptr || read_modifier == nullptr) {
    value.unavailable_reason = "candidate_modifier_reader_unavailable";
    return value;
  }
  auto *context = static_cast<std::byte *>(aggregate) + 0x68;
  std::int64_t additive = 0, multiplicative = 0;
  if (read_modifier(context, &additive,
                    kCommanderCapacityAdditiveModifier12004) == &additive)
    value.additive_modifier_raw = additive;
  if (read_modifier(context, &multiplicative,
                    kCommanderCapacityMultiplicativeModifier12004) ==
      &multiplicative)
    value.multiplicative_modifier_raw = multiplicative;
  if (!value.additive_modifier_raw || !value.multiplicative_modifier_raw) {
    value.unavailable_reason = "candidate_capacity_modifier_read_failed";
    return value;
  }
  value.conditional_capacity_raw = CommanderCapacityFixedMul12004(
      CapacityWrapAdd12004(*loaded_full, additive),
      CapacityWrapAdd12004(100000, multiplicative));
  value.status = "available";
  value.unavailable_reason = {};
  return value;
}

inline std::string SerializeCommanderConditionalSupplyCapacity12004(
    const CommanderConditionalSupplyCapacity12004 &value) {
  const auto raw = [](const std::optional<std::int64_t> &v) {
    return v ? '"' + std::to_string(*v) + '"' : std::string("null");
  };
  std::string out =
      "{\"schema\":\"xar.ck3.commander-conditional-supply-capacity.12004.v1\","
      "\"status\":\"" + std::string(value.status) +
      "\",\"source_character_id\":" +
      (value.source_character_id ? std::to_string(*value.source_character_id)
                                 : std::string("null")) +
      ",\"scale\":100000,\"loaded_full_raw\":" + raw(value.loaded_full_raw) +
      ",\"additive_modifier_raw\":" + raw(value.additive_modifier_raw) +
      ",\"multiplicative_modifier_raw\":" + raw(value.multiplicative_modifier_raw) +
      ",\"conditional_capacity_raw\":" + raw(value.conditional_capacity_raw) +
      ",\"assignment_applied\":false,"
      "\"assumption\":\"candidate_aggregate_unchanged_after_assignment\","
      "\"unavailable_reason\":" +
      (value.unavailable_reason.empty()
           ? std::string("null")
           : '"' + std::string(value.unavailable_reason) + '"') +
      ",\"provenance\":{\"game_version\":\"1.20.0.4\","
      "\"executable_sha256\":\"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518\","
      "\"capacity_rva\":" + std::to_string(kCommanderCapacityRva12004) +
      ",\"loaded_full_rva\":" +
      std::to_string(kCommanderCapacityLoadedFullRva12004) +
      ",\"additive_modifier_id\":467,\"multiplicative_modifier_id\":468}}";
  return out;
}

} // namespace xar::ck3_12004
