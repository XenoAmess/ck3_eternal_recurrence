#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <string_view>

namespace xar::ck3_12004 {

enum class ConceptionChildLimitRole12004 { first, second };

// Actual provider 2B95AB4..2B95ADA. Highest tiers are supplied from the already
// qualified 28AC690 callback; no native routine is called by this leaf.
constexpr ConceptionChildLimitRole12004 SelectConceptionChildLimitRole12004(
    bool first_1c0_nonzero, std::int32_t first_highest_tier_raw,
    std::int32_t second_highest_tier_raw) noexcept {
  return first_1c0_nonzero && first_highest_tier_raw > second_highest_tier_raw
             ? ConceptionChildLimitRole12004::first
             : ConceptionChildLimitRole12004::second;
}

struct ConceptionChildLimitInputs12004 {
  std::uint32_t selected_full_id = 0;
  std::optional<std::int32_t> table_base_raw;
  bool either_1c0_nonzero = false;
  std::optional<std::int32_t> either_1c0_bonus_raw;
  bool either_current_id_list_match = false;
  std::optional<std::int32_t> id_list_bonus_raw;
  std::optional<std::int32_t> selected_relation20_living_count_raw;
  std::optional<std::int32_t> extra_relation20_coefficient_raw;
  std::optional<std::int32_t> selected_relation50_count_raw;
  std::optional<std::int32_t> extra_relation50_coefficient_raw;
  bool selected_special_four_slot_predicate = false;
  std::optional<std::int32_t> special_four_slot_bonus_raw;
  std::optional<std::int64_t> decrement_threshold_raw;
};

struct ConceptionChildLimitValue12004 {
  bool complete = false;
  std::string_view unavailable_reason = "child_limit_current_input_unavailable";
  std::optional<std::int32_t> accumulated_before_decrement_raw;
  std::optional<std::uint32_t> deterministic_remainder_raw;
  std::optional<bool> decremented;
  std::optional<std::int32_t> child_limit_raw;
};

constexpr std::int32_t ConceptionChildLimitSigned32FromBits12004(
    std::uint32_t bits) noexcept {
  return bits <= 0x7FFFFFFFU
             ? static_cast<std::int32_t>(bits)
             : static_cast<std::int32_t>(static_cast<std::int64_t>(bits) -
                                         0x100000000LL);
}

// Direct unsigned32 translation of 2B9501B..2B950B3, including the native
// multiplication-high reduction. These literals are instruction operands.
constexpr std::uint32_t ConceptionChildLimitRemainder12004(
    std::uint32_t selected_full_id) noexcept {
  std::uint32_t c = 0x5EA6BA9FU - selected_full_id * 0x4AD685B3U;
  std::uint32_t d = (c ^ (c >> 8)) + 0x68E31DA4U;
  c = ((d << 8) ^ d) * 0x1B56C4E9U;
  c = (c ^ (c >> 8)) * 0x92D68CA2U;
  c = (c ^ (c >> 8)) * 0xB5297A4DU;
  d = (c ^ (c >> 8)) + 0x68E31DA4U;
  c = ((d << 8) ^ d) * 0x1B56C4E9U;
  c = (c ^ (c >> 8)) * 0x92D68CA2U;
  const std::uint32_t value = (c ^ (c >> 8)) & 0x7FFFFFFFU;
  const std::uint32_t high = static_cast<std::uint32_t>(
      (static_cast<std::uint64_t>(0x4F8B588FU) * value) >> 32);
  const std::uint32_t quotient = (((value - high) >> 1) + high) >> 16;
  return value - quotient * 100000U;
}

constexpr ConceptionChildLimitValue12004 EvaluateConceptionChildLimit12004(
    const ConceptionChildLimitInputs12004 &input) noexcept {
  ConceptionChildLimitValue12004 result{};
  if (!input.table_base_raw || !input.selected_relation20_living_count_raw ||
      !input.selected_relation50_count_raw || !input.decrement_threshold_raw ||
      (input.either_1c0_nonzero && !input.either_1c0_bonus_raw) ||
      (input.either_current_id_list_match && !input.id_list_bonus_raw) ||
      (*input.selected_relation20_living_count_raw > 1 &&
       !input.extra_relation20_coefficient_raw) ||
      (*input.selected_relation50_count_raw > 1 &&
       !input.extra_relation50_coefficient_raw) ||
      (input.selected_special_four_slot_predicate &&
       !input.special_four_slot_bonus_raw))
    return result;
  std::uint32_t sum = static_cast<std::uint32_t>(*input.table_base_raw);
  if (input.either_1c0_nonzero)
    sum += static_cast<std::uint32_t>(*input.either_1c0_bonus_raw);
  if (input.either_current_id_list_match)
    sum += static_cast<std::uint32_t>(*input.id_list_bonus_raw);
  if (*input.selected_relation20_living_count_raw > 1)
    sum += (static_cast<std::uint32_t>(
                *input.selected_relation20_living_count_raw) - 1U) *
           static_cast<std::uint32_t>(*input.extra_relation20_coefficient_raw);
  if (*input.selected_relation50_count_raw > 1)
    sum += (static_cast<std::uint32_t>(*input.selected_relation50_count_raw) -
            1U) * static_cast<std::uint32_t>(
                      *input.extra_relation50_coefficient_raw);
  if (input.selected_special_four_slot_predicate)
    sum += static_cast<std::uint32_t>(*input.special_four_slot_bonus_raw);
  const auto remainder = ConceptionChildLimitRemainder12004(input.selected_full_id);
  const bool decrement = static_cast<std::int64_t>(remainder) <
                         *input.decrement_threshold_raw;
  result.complete = true;
  result.unavailable_reason = {};
  result.accumulated_before_decrement_raw =
      ConceptionChildLimitSigned32FromBits12004(sum);
  result.deterministic_remainder_raw = remainder;
  result.decremented = decrement;
  result.child_limit_raw =
      ConceptionChildLimitSigned32FromBits12004(sum - (decrement ? 1U : 0U));
  return result;
}

using ConceptionChildLimit12004ReadMemory =
    bool (*)(void *context, const void *address, void *output,
             std::size_t size) noexcept;

struct ConceptionChildLimit12004Bindings {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  ConceptionChildLimit12004ReadMemory read_memory = nullptr;
  void *read_context = nullptr;
  std::size_t maximum_collection_rows = 4096;
};

inline ConceptionChildLimit12004Bindings BindConceptionChildLimit12004(
    std::string_view build_version, std::string_view executable_sha256,
    std::uintptr_t module_base,
    ConceptionChildLimit12004ReadMemory read_memory,
    void *read_context = nullptr) noexcept {
  ConceptionChildLimit12004Bindings result{};
  result.enabled = build_version == "1.20.0.4" &&
      executable_sha256 ==
          "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518" &&
      module_base != 0 && read_memory != nullptr;
  result.module_base = module_base;
  result.read_memory = read_memory;
  result.read_context = read_context;
  return result;
}

struct ConceptionChildLimit12004Read {
  std::string_view source = "native_conception_child_limit";
  std::string_view status = "unavailable";
  std::string_view unavailable_reason = "child_limit_binding_unavailable";
  std::uintptr_t selected_character = 0;
  std::uint32_t selected_full_id = 0;
  std::int32_t pair_lineage_tier_max_raw = 0;
  bool used_extended_fallback = false;
  std::size_t relation20_fallback_rows = 0;
  ConceptionChildLimitInputs12004 inputs{};
  ConceptionChildLimitValue12004 value{};
};

namespace conception_child_limit_12004_detail {

inline bool Add(std::uintptr_t address, std::uintptr_t offset,
                std::uintptr_t &output) noexcept {
  if (address > std::numeric_limits<std::uintptr_t>::max() - offset)
    return false;
  output = address + offset;
  return output != 0;
}

template <typename T>
inline bool Read(const ConceptionChildLimit12004Bindings &b,
                 std::uintptr_t address, T &output) noexcept {
  return address != 0 && b.read_memory != nullptr &&
         address <= std::numeric_limits<std::uintptr_t>::max() - sizeof(T) &&
         b.read_memory(b.read_context, reinterpret_cast<const void *>(address),
                       &output, sizeof(T));
}

template <typename T>
inline bool Field(const ConceptionChildLimit12004Bindings &b,
                  std::uintptr_t base, std::uintptr_t offset,
                  T &output) noexcept {
  std::uintptr_t address = 0;
  return Add(base, offset, address) && Read(b, address, output);
}

inline bool Identity(const ConceptionChildLimit12004Bindings &b,
                     std::uintptr_t character,
                     std::uint32_t expected_full_id) noexcept {
  std::uint32_t actual = 0;
  return Field(b, character, 0x18, actual) && actual == expected_full_id;
}

inline bool List(const ConceptionChildLimit12004Bindings &b,
                 std::uintptr_t descriptor, std::uintptr_t &data,
                 std::int32_t &count) noexcept {
  return Read(b, descriptor, data) && Field(b, descriptor, 0xC, count) &&
         count >= 0 &&
         static_cast<std::size_t>(count) <= b.maximum_collection_rows &&
         (count == 0 || data != 0);
}

inline bool ResolveRelation20(const ConceptionChildLimit12004Bindings &b,
                              std::uint32_t full_id,
                              std::uintptr_t store,
                              std::uintptr_t fallback,
                              std::uintptr_t &character,
                              bool &used_fallback) noexcept {
  character = fallback;
  used_fallback = true;
  if (store == 0) return fallback != 0;
  std::uint32_t capacity = 0;
  if (!Field(b, store, 0x2C, capacity)) return false;
  const auto index = full_id & 0xFFFFFFU;
  if (index >= capacity) return fallback != 0;
  std::uintptr_t slots = 0, slot = 0, candidate = 0;
  if (!Field(b, store, 0x20, slots) || slots == 0 ||
      !Add(slots, static_cast<std::uintptr_t>(index) * 16U + 8U, slot) ||
      !Read(b, slot, candidate))
    return false;
  if (candidate == 0) return fallback != 0;
  std::uint32_t candidate_id = 0;
  if (!Field(b, candidate, 0x18, candidate_id)) return false;
  if (candidate_id != full_id) return fallback != 0;
  character = candidate;
  used_fallback = false;
  return true;
}

} // namespace conception_child_limit_12004_detail

// Root supplies first/second and the already-qualified selected role from the
// same application-thread frame, plus continuation-48's actual signed index.
// This function only copies current inputs. It never calls the pair provider,
// child-limit helper, native predicate, compiler dispatch or any mutation API.
inline ConceptionChildLimit12004Read ReadConceptionChildLimitForPair12004(
    const ConceptionChildLimit12004Bindings &b,
    std::uintptr_t first_character, std::uint32_t first_full_id,
    std::uintptr_t second_character, std::uint32_t second_full_id,
    std::uintptr_t selected_character, std::uint32_t selected_full_id,
    std::int32_t pair_lineage_tier_max_raw) noexcept {
  using namespace conception_child_limit_12004_detail;
  ConceptionChildLimit12004Read out{};
  out.selected_character = selected_character;
  out.selected_full_id = selected_full_id;
  out.pair_lineage_tier_max_raw = pair_lineage_tier_max_raw;
  out.inputs.selected_full_id = selected_full_id;
  if (!b.enabled || b.module_base == 0 || b.read_memory == nullptr) return out;
  out.unavailable_reason = "child_limit_current_memory_unavailable";
  if (!((selected_character == first_character &&
         selected_full_id == first_full_id) ||
        (selected_character == second_character &&
         selected_full_id == second_full_id))) {
    out.unavailable_reason = "child_limit_selected_role_identity_mismatch";
    return out;
  }
  if (!Identity(b, first_character, first_full_id) ||
      !Identity(b, second_character, second_full_id)) {
    out.unavailable_reason = "child_limit_character_identity_unavailable";
    return out;
  }
  constexpr std::array<std::uint8_t, 16> signature{
      0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x6C,
      0x24, 0x10, 0x48, 0x89, 0x74, 0x24, 0x18, 0x48};
  std::array<std::uint8_t, 16> actual{};
  if (!Field(b, b.module_base, 0x2B94ED0, actual) || actual != signature) {
    out.unavailable_reason = "child_limit_source_signature_mismatch";
    return out;
  }
  std::uintptr_t table = 0;
  if (!Field(b, b.module_base, 0x545CE80, table) || table == 0) return out;
  const std::int64_t displacement =
      static_cast<std::int64_t>(pair_lineage_tier_max_raw) * 4;
  std::uintptr_t table_entry = 0;
  if (displacement < 0) {
    const auto subtract = static_cast<std::uint64_t>(-displacement);
    if (table < subtract) return out;
    table_entry = table - static_cast<std::uintptr_t>(subtract);
  } else if (!Add(table, static_cast<std::uintptr_t>(displacement), table_entry))
    return out;
  std::int32_t table_value = 0;
  if (!Read(b, table_entry, table_value)) return out;
  out.inputs.table_base_raw = table_value;
  std::uint64_t first_1c0 = 0, second_1c0 = 0;
  if (!Field(b, first_character, 0x1C0, first_1c0)) return out;
  if (first_1c0 == 0 &&
      !Field(b, second_character, 0x1C0, second_1c0)) return out;
  out.inputs.either_1c0_nonzero = first_1c0 != 0 || second_1c0 != 0;
  std::int32_t scalar = 0;
  if (out.inputs.either_1c0_nonzero) {
    if (!Field(b, b.module_base, 0x5C69E80, scalar)) return out;
    out.inputs.either_1c0_bonus_raw = scalar;
  }
  std::uintptr_t manager = 0, collection_owner = 0, id_data = 0;
  std::int32_t id_count = 0;
  if (!Field(b, b.module_base, 0x5C68C50, manager) || manager == 0 ||
      !Field(b, manager, 0xA0, collection_owner) || collection_owner == 0 ||
      !Field(b, collection_owner, 0x22358, id_data) ||
      !Field(b, collection_owner, 0x22364, id_count) || id_count < 0 ||
      static_cast<std::size_t>(id_count) > b.maximum_collection_rows ||
      (id_count != 0 && id_data == 0)) return out;
  for (std::int32_t i = 0; i < id_count; ++i) {
    std::uint32_t id = 0;
    if (!Field(b, id_data, static_cast<std::uintptr_t>(i) * 4, id)) return out;
    if (id == first_full_id || id == second_full_id) {
      out.inputs.either_current_id_list_match = true;
      break;
    }
  }
  if (out.inputs.either_current_id_list_match) {
    if (!Field(b, b.module_base, 0x5C69DB0, scalar)) return out;
    out.inputs.id_list_bonus_raw = scalar;
  }
  std::uintptr_t extended = 0, fallback_descriptor = 0;
  if (!Field(b, selected_character, 0x1A8, extended) ||
      !Add(b.module_base, 0x5459588, fallback_descriptor)) return out;
  out.used_extended_fallback = extended == 0;
  std::uintptr_t descriptor20 = fallback_descriptor;
  if (extended != 0 && !Add(extended, 0x20, descriptor20)) return out;
  std::uintptr_t relation_data = 0;
  std::int32_t relation_count = 0;
  if (!List(b, descriptor20, relation_data, relation_count)) return out;
  std::uintptr_t store = 0, character_fallback = 0;
  if (relation_count != 0 &&
      (!Field(b, b.module_base, 0x5C67568, store) ||
       !Field(b, b.module_base, 0x5C67570, character_fallback))) return out;
  std::int32_t living = 0;
  for (std::int32_t i = 0; i < relation_count; ++i) {
    std::uint32_t id = 0;
    std::uintptr_t character = 0;
    bool fallback_used = false;
    std::uint64_t death = 0;
    if (!Field(b, relation_data, static_cast<std::uintptr_t>(i) * 4, id) ||
        !ResolveRelation20(b, id, store, character_fallback, character,
                           fallback_used) ||
        !Field(b, character, 0x1D0, death)) return out;
    if (fallback_used) ++out.relation20_fallback_rows;
    if (death == 0) ++living;
  }
  out.inputs.selected_relation20_living_count_raw = living;
  if (living > 1) {
    if (!Field(b, b.module_base, 0x5C69D9C, scalar)) return out;
    out.inputs.extra_relation20_coefficient_raw = scalar;
  }
  std::uintptr_t descriptor50 = fallback_descriptor;
  if (extended != 0 && !Add(extended, 0x50, descriptor50)) return out;
  std::int32_t count50 = 0;
  if (!Field(b, descriptor50, 0xC, count50)) return out;
  out.inputs.selected_relation50_count_raw = count50;
  if (count50 > 1) {
    if (!Field(b, b.module_base, 0x5C69DB4, scalar)) return out;
    out.inputs.extra_relation50_coefficient_raw = scalar;
  }
  std::uint64_t slot1c8 = 0, slot1c0 = 0, slot1b8 = 0, slot1b0 = 0;
  if (!Field(b, selected_character, 0x1C8, slot1c8)) return out;
  if (slot1c8 == 0) {
    if (!Field(b, selected_character, 0x1C0, slot1c0)) return out;
    if (slot1c0 == 0) {
      if (!Field(b, selected_character, 0x1B8, slot1b8)) return out;
      if (slot1b8 == 0 &&
          !Field(b, selected_character, 0x1B0, slot1b0)) return out;
    }
  }
  out.inputs.selected_special_four_slot_predicate =
      slot1c8 == 0 && slot1c0 == 0 && slot1b8 == 0 && slot1b0 != 0;
  if (out.inputs.selected_special_four_slot_predicate) {
    if (!Field(b, b.module_base, 0x5C69E88, scalar)) return out;
    out.inputs.special_four_slot_bonus_raw = scalar;
  }
  std::int64_t threshold = 0;
  if (!Field(b, b.module_base, 0x5C69E78, threshold)) return out;
  out.inputs.decrement_threshold_raw = threshold;
  if (!Identity(b, first_character, first_full_id) ||
      !Identity(b, second_character, second_full_id)) {
    out.unavailable_reason = "child_limit_character_identity_changed";
    return out;
  }
  out.value = EvaluateConceptionChildLimit12004(out.inputs);
  if (out.value.complete) {
    out.status = "complete";
    out.unavailable_reason = {};
  } else out.unavailable_reason = out.value.unavailable_reason;
  return out;
}

} // namespace xar::ck3_12004
