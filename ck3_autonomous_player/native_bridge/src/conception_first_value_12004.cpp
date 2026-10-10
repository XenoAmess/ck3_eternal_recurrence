#include "xar_bridge/conception_first_value_12004.hpp"
#include "xar_bridge/conception_value_arithmetic_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <cstring>

namespace xar::ck3_12004 {
namespace {

template <typename Signed, typename Unsigned>
Signed SignedBits(Unsigned bits) noexcept {
  static_assert(sizeof(Signed) == sizeof(Unsigned));
  Signed value = 0;
  std::memcpy(&value, &bits, sizeof(value));
  return value;
}

std::int64_t SeedAfterChildren(const ConceptionFirstValue12004Inputs &input) noexcept {
  // Actual IMUL2B95238/SUB2B95240 preserve the low64 result.
  const auto decrement = static_cast<std::uint64_t>(input.per_child_decrement_raw) *
      static_cast<std::uint64_t>(static_cast<std::int64_t>(input.children_count_raw));
  return SignedBits<std::int64_t>(static_cast<std::uint64_t>(input.seed_raw) - decrement);
}

std::int32_t AdjustedAge(const ConceptionFirstValue12004Inputs &input) noexcept {
  // BF lookup misses are a source-proved raw zero; successful values are
  // shifted by +/-50000 before signed truncation at2B952B4..2B952E7.
  const auto selected_age = input.age_override_raw < 0 ?
      input.age_raw : input.age_override_raw;
  return ConceptionAdjustedAgeRaw12004(selected_age, input.modifier_bf_raw);
}

bool Copy(const ConceptionFirstValue12004Bindings &bindings,
          std::uintptr_t address, void *output, std::size_t size) noexcept {
  return bindings.read_memory(bindings.read_context,
      reinterpret_cast<const void *>(address), output, size);
}

template <typename T>
bool Copy(const ConceptionFirstValue12004Bindings &bindings,
          std::uintptr_t address, T &output) noexcept {
  return Copy(bindings, address, &output, sizeof(output));
}

} // namespace

ConceptionFirstValue12004Read EvaluateConceptionFirstValue12004(
    const std::optional<ConceptionFirstValue12004Inputs> &inputs) noexcept {
  ConceptionFirstValue12004Read result;
  if (!inputs) return result;
  const auto &input = *inputs;
  result.seed_after_children_raw = SeedAfterChildren(input);
  result.adjusted_age_raw = AdjustedAge(input);
  std::int32_t index = 0;
  while (index < input.age_threshold_count_low32) {
    if (static_cast<std::size_t>(index) >= input.age_threshold_prefix.size()) {
      result.unavailable_reason = "native_conception_first_age_threshold_unread";
      return result;
    }
    if (*result.adjusted_age_raw >= input.age_threshold_prefix[index]) break;
    ++index;
  }
  if (index != input.sampled_age_band_index) {
    result.unavailable_reason = "native_conception_first_age_band_input_mismatch";
    return result;
  }
  result.selected_age_band_index = index;
  result.age_product_raw = MultiplyConceptionRaw12004(
      *result.seed_after_children_raw, input.selected_age_multiplier_raw);
  if (input.final_multiplier_applies) {
    if (!input.final_multiplier_raw) {
      result.unavailable_reason = "native_conception_first_final_multiplier_unread";
      return result;
    }
    result.first_output_raw = MultiplyConceptionRaw12004(
        *result.age_product_raw, *input.final_multiplier_raw);
  } else {
    result.first_output_raw = result.age_product_raw;
  }
  result.status = "available";
  result.unavailable_reason = {};
  return result;
}

ConceptionFirstValue12004Bindings BindConceptionFirstValue12004(
    std::string_view build_version, std::string_view executable_sha256,
    std::uintptr_t module_base, ConceptionFirstValue12004ReadMemory read_memory,
    void *read_context) noexcept {
  if (build_version != kGameVersion || executable_sha256 != kExecutableSha256 ||
      module_base == 0 || read_memory == nullptr) return {};
  return {true, module_base, read_memory, read_context};
}

std::optional<ConceptionFirstValue12004Inputs>
ReadConceptionFirstValueInputsForCharacter12004(
    const ConceptionFirstValue12004Bindings &bindings,
    std::uintptr_t character, std::uint32_t expected_full_id,
    const ck3_12002::family_value::CharacterValue &current_value,
    std::string_view *reason) {
  const auto Fail = [reason](std::string_view value)
      -> std::optional<ConceptionFirstValue12004Inputs> {
    if (reason != nullptr) *reason = value;
    return std::nullopt;
  };
  if (!bindings.enabled || bindings.read_memory == nullptr)
    return Fail("native_conception_first_binding_unavailable");
  if (character == 0 || expected_full_id == 0xFFFFFFFFU ||
      static_cast<std::uint32_t>(current_value.character_id) != expected_full_id ||
      !current_value.fertility.available)
    return Fail("native_conception_first_current_value_unavailable");
  std::uint32_t magic = 0, actual_full_id = 0;
  if (!Copy(bindings, character + 0x1C, magic) ||
      !Copy(bindings, character + 0x18, actual_full_id))
    return Fail("native_conception_first_character_identity_unread");
  if (magic != 0x43686172U || actual_full_id != expected_full_id)
    return Fail("native_conception_first_character_identity_mismatch");

  ConceptionFirstValue12004Inputs input;
  input.seed_raw = current_value.fertility.effective_raw;
  input.age_raw = current_value.age_raw;
  if (current_value.scorer_age_override_raw) {
    input.age_override_raw = *current_value.scorer_age_override_raw;
  } else if (!Copy(bindings, character + 0x6C, input.age_override_raw)) {
    return Fail("native_conception_first_age_override_unread");
  }
  std::uintptr_t family = 0;
  if (!Copy(bindings, character + 0x1A8, family))
    return Fail("native_conception_first_children_owner_unread");
  const auto children = family == 0 ? bindings.module_base + 0x5459588 : family + 0x38;
  if (!Copy(bindings, children + 0xC, input.children_count_raw) ||
      !Copy(bindings, bindings.module_base + 0x5C69ED8, input.per_child_decrement_raw))
    return Fail("native_conception_first_children_decrement_unread");

  // Reuse the closed owned return of actual28C3AC0, never its lazy default path.
  std::uintptr_t extended = 0, model = 0, model_owner = 0;
  if (!Copy(bindings, character + 0x1B0, extended))
    return Fail("native_conception_first_extended_unread");
  if (extended == 0)
    return Fail("native_conception_first_owned_modifier_model_unavailable");
  if (!Copy(bindings, extended + 0x258, model))
    return Fail("native_conception_first_modifier_model_unread");
  if (model == 0)
    return Fail("native_conception_first_owned_modifier_model_unavailable");
  if (!Copy(bindings, model + 8, model_owner))
    return Fail("native_conception_first_modifier_owner_unread");
  if (model_owner != character)
    return Fail("native_conception_first_modifier_owner_mismatch");
  const auto modifier = model + 0x10;
  std::uintptr_t keys = 0;
  std::int32_t modifier_count = 0;
  if (!Copy(bindings, modifier + 0x68, keys) ||
      !Copy(bindings, modifier + 0x74, modifier_count))
    return Fail("native_conception_first_modifier_key_layout_unread");
  std::int64_t candidate_index = 0, remaining = modifier_count;
  while (remaining > 0) {
    const auto half = remaining / 2;
    std::uint16_t key = 0;
    if (!Copy(bindings, keys + static_cast<std::uintptr_t>(candidate_index + half) * 2, key))
      return Fail("native_conception_first_modifier_key_unread");
    if (key < 0xBF) candidate_index += remaining - half;
    remaining = half;
  }
  input.modifier_bf_raw = 0;
  if (candidate_index != modifier_count) {
    std::uint16_t key = 0;
    if (!Copy(bindings, keys + static_cast<std::uintptr_t>(candidate_index) * 2, key))
      return Fail("native_conception_first_modifier_key_unread");
    if (key <= 0xBF && candidate_index >= 0) {
      std::uintptr_t values = 0;
      if (!Copy(bindings, modifier + 0xD0, values) ||
          !Copy(bindings, values + static_cast<std::uintptr_t>(candidate_index) * 8,
                input.modifier_bf_raw))
        return Fail("native_conception_first_modifier_value_unread");
    }
  }
  std::uint64_t count_qword = 0;
  if (!Copy(bindings, bindings.module_base + 0x544FC04, count_qword))
    return Fail("native_conception_first_age_count_unread");
  input.age_threshold_count_low32 = SignedBits<std::int32_t>(
      static_cast<std::uint32_t>(count_qword));
  std::uintptr_t thresholds = 0;
  if (input.age_threshold_count_low32 > 0 &&
      !Copy(bindings, bindings.module_base + 0x544FBF8, thresholds))
    return Fail("native_conception_first_age_threshold_pointer_unread");
  const auto adjusted_age = AdjustedAge(input);
  while (input.sampled_age_band_index < input.age_threshold_count_low32) {
    std::int32_t threshold = 0;
    if (!Copy(bindings, thresholds +
          static_cast<std::uintptr_t>(input.sampled_age_band_index) * 4, threshold))
      return Fail("native_conception_first_age_threshold_unread");
    input.age_threshold_prefix.push_back(threshold);
    if (adjusted_age >= threshold) break;
    ++input.sampled_age_band_index;
  }
  std::uintptr_t multipliers = 0;
  if (!Copy(bindings, bindings.module_base + 0x544FCA8, multipliers) ||
      !Copy(bindings, multipliers +
            static_cast<std::uintptr_t>(input.sampled_age_band_index) * 8,
            input.selected_age_multiplier_raw))
    return Fail("native_conception_first_age_multiplier_unread");

  bool any_nonzero = false;
  for (const auto offset : {0x1C8U, 0x1C0U, 0x1B8U}) {
    std::uint64_t raw = 0;
    if (!Copy(bindings, character + offset, raw))
      return Fail("native_conception_first_final_branch_unread");
    if (raw != 0) {
      any_nonzero = true;
      break;
    }
  }
  input.final_multiplier_applies = !any_nonzero && extended != 0;
  if (input.final_multiplier_applies) {
    std::int64_t raw = 0;
    if (!Copy(bindings, bindings.module_base + 0x5C69E10, raw))
      return Fail("native_conception_first_final_multiplier_unread");
    input.final_multiplier_raw = raw;
  }
  if (reason != nullptr) *reason = {};
  return input;
}

} // namespace xar::ck3_12004
