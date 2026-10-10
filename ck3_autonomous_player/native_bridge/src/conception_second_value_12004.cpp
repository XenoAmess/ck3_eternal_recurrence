#include "xar_bridge/conception_second_value_12004.hpp"
#include <bit>
#include <limits>

namespace xar::ck3_12004 {
namespace {
constexpr std::string_view kExactSha =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
bool Fail(std::string &reason, const char *text) {
  reason = text;
  return false;
}
template<class T> bool Read(const ConceptionSecondValueBindings12004 &b,
                           std::uintptr_t base, std::size_t offset, T &out) {
  if (base == 0 || offset > std::numeric_limits<std::uintptr_t>::max() - base)
    return false;
  return b.read_memory(b.read_context, base + offset, &out, sizeof(out));
}
bool ReadModifierBF(const ConceptionSecondValueBindings12004 &b,
                    std::uintptr_t character, std::uintptr_t extension,
                    std::int64_t &value, std::string &reason) {
  std::uintptr_t model = 0, owner = 0;
  if (!Read(b, extension, 0x258, model) || model == 0 ||
      !Read(b, model, 8, owner) || owner != character)
    return Fail(reason, "modifier_context_owned_model_unavailable");
  if (model > std::numeric_limits<std::uintptr_t>::max() - 0x10)
    return Fail(reason, "modifier_context_address_unavailable");
  const auto context = model + 0x10;
  std::int32_t count = 0;
  std::uintptr_t keys = 0;
  if (!Read(b, context, 0x74, count) || count < 0)
    return Fail(reason, "modifier_key_count_unavailable");
  if (count == 0) { value = 0; return true; }
  if (!Read(b, context, 0x68, keys) || keys == 0)
    return Fail(reason, "modifier_key_array_unavailable");
  // The actual lower-bound loop; no full PC scan or numerical-name mapping.
  std::uint32_t first = 0, n = static_cast<std::uint32_t>(count);
  while (n != 0) {
    const auto half = n >> 1;
    std::uint16_t key = 0;
    if (!Read(b, keys, static_cast<std::size_t>(first + half) * 2, key))
      return Fail(reason, "modifier_key_copy_unavailable");
    if (key < 0xBF) first += n - half;
    n = half;
  }
  if (first == static_cast<std::uint32_t>(count)) {
    value = 0;
    return true;
  }
  std::uint16_t selected_key = 0;
  if (!Read(b, keys, static_cast<std::size_t>(first) * 2, selected_key))
    return Fail(reason, "modifier_selected_key_unavailable");
  if (0xBF < selected_key) { value = 0; return true; }
  std::uintptr_t values = 0;
  if (!Read(b, context, 0xD0, values) || values == 0 ||
      !Read(b, values, static_cast<std::size_t>(first) * 8, value))
    return Fail(reason, "modifier_selected_value_unavailable");
  return true;
}
} // namespace

ConceptionSecondValueBindings12004 BindConceptionSecondValue12004(
    std::uintptr_t base, std::string_view version, std::string_view sha,
    ConceptionSecondValueRead12004 read, void *context) noexcept {
  ConceptionSecondValueBindings12004 result;
  if (base == 0 || version != "1.20.0.4" || sha != kExactSha || read == nullptr)
    return result;
  result.enabled = true;
  result.module_base = base;
  result.read_memory = read;
  result.read_context = context;
  return result;
}

ConceptionSecondValue12004 ComputeConceptionSecondValue12004(
    const ConceptionSecondValueInputs12004 &input) {
  ConceptionSecondValue12004 result;
  const auto age = ConceptionAdjustedAgeRaw12004(input.selected_age_raw,
                                               input.modifier_bf_raw);
  std::int32_t band = 0;
  bool matched = input.threshold_count_raw <= 0;
  if (input.threshold_count_raw > 0) {
    for (const auto threshold : input.thresholds_prefix) {
      if (band >= input.threshold_count_raw) break;
      if (age >= threshold) { matched = true; break; }
      ++band;
    }
    if (band == input.threshold_count_raw) matched = true;
  }
  if (!matched || band != input.selected_band_index) {
    result.reason = "age_threshold_prefix_or_band_unavailable";
    return result;
  }
  const auto prefinal = MultiplyConceptionRaw12004(input.fertility_seed_raw,
                                                 input.selected_multiplier_raw);
  const bool conditional = input.extension_1b0_present &&
      !input.pointer_1b8_present && !input.pointer_1c0_present &&
      !input.pointer_1c8_present;
  if (conditional && !input.conditional_final_factor_raw) {
    result.reason = "conditional_final_factor_unavailable";
    return result;
  }
  result.ready = true;
  result.adjusted_age_raw = age;
  result.selected_band_index = band;
  result.prefinal_raw = prefinal;
  result.value_raw = conditional
      ? MultiplyConceptionRaw12004(prefinal, *input.conditional_final_factor_raw)
      : prefinal;
  return result;
}

bool ReadConceptionSecondValueInputs12004(
    const ConceptionSecondValueBindings12004 &b, std::uintptr_t character,
    std::int32_t expected_id,
    const ck3_12002::family_value::FertilityRead &seed,
    ConceptionSecondValueInputs12004 &output, std::string &reason) {
  output = {};
  reason.clear();
  if (!b.enabled || b.read_memory == nullptr || character == 0 || expected_id == -1)
    return Fail(reason, "second_value_binding_or_character_unavailable");
  std::int32_t actual_id = -1;
  if (!Read(b, character, 0x18, actual_id) || actual_id != expected_id)
    return Fail(reason, "second_character_full_id_mismatch");
  if (!seed.available)
    return Fail(reason, "existing_family_fertility_seed_unavailable");
  ConceptionSecondValueInputs12004 input;
  std::uintptr_t extension = 0, p1b8 = 0, p1c0 = 0, p1c8 = 0;
  if (!Read(b, character, 0x1B0, extension) ||
      !Read(b, character, 0x1B8, p1b8) ||
      !Read(b, character, 0x1C0, p1c0) ||
      !Read(b, character, 0x1C8, p1c8))
    return Fail(reason, "character_final_condition_inputs_unavailable");
  if (seed.extension_present != (extension != 0) ||
      (extension != 0 && !seed.native_gate_evaluated) ||
      (!seed.native_gate_allows && seed.effective_raw != 0))
    return Fail(reason, "existing_family_fertility_seed_binding_mismatch");
  input.fertility_seed_raw = seed.effective_raw;
  input.extension_1b0_present = extension != 0;
  input.pointer_1b8_present = p1b8 != 0;
  input.pointer_1c0_present = p1c0 != 0;
  input.pointer_1c8_present = p1c8 != 0;
  std::int16_t override_age = 0;
  if (!Read(b, character, 0x6C, override_age))
    return Fail(reason, "selected_age_override_unavailable");
  input.selected_age_raw = override_age;
  if (override_age < 0 && !Read(b, character, 0x68, input.selected_age_raw))
    return Fail(reason, "selected_age_fallback_unavailable");
  if (!ReadModifierBF(b, character, extension, input.modifier_bf_raw, reason))
    return false;
  std::uint64_t count_qword = 0;
  if (!Read(b, b.module_base, kConceptionSecondThresholdCount12004, count_qword))
    return Fail(reason, "age_threshold_count_unavailable");
  input.threshold_count_raw = std::bit_cast<std::int32_t>(
      static_cast<std::uint32_t>(count_qword));
  const auto age = ConceptionAdjustedAgeRaw12004(input.selected_age_raw,
                                               input.modifier_bf_raw);
  std::int32_t band = 0;
  if (input.threshold_count_raw > 0) {
    if (static_cast<std::uint32_t>(input.threshold_count_raw) >
        b.age_threshold_read_budget)
      return Fail(reason, "age_threshold_count_exceeds_observer_read_budget");
    std::uintptr_t thresholds = 0;
    if (!Read(b, b.module_base, kConceptionSecondThresholdPointer12004, thresholds) || thresholds == 0)
      return Fail(reason, "age_threshold_pointer_unavailable");
    for (; band < input.threshold_count_raw; ++band) {
      std::int32_t threshold = 0;
      if (!Read(b, thresholds, static_cast<std::size_t>(band) * 4, threshold))
        return Fail(reason, "age_threshold_entry_unavailable");
      input.thresholds_prefix.push_back(threshold);
      if (age >= threshold) break;
    }
  }
  input.selected_band_index = band;
  std::uintptr_t multipliers = 0;
  if (!Read(b, b.module_base, kConceptionSecondMultiplierPointer12004, multipliers) || multipliers == 0 ||
      !Read(b, multipliers, static_cast<std::size_t>(band) * 8, input.selected_multiplier_raw))
    return Fail(reason, "selected_age_multiplier_unavailable");
  if (input.extension_1b0_present && !input.pointer_1b8_present &&
      !input.pointer_1c0_present && !input.pointer_1c8_present) {
    std::int64_t factor = 0;
    if (!Read(b, b.module_base, kConceptionFinalConditionalFactor12004, factor))
      return Fail(reason, "conditional_final_factor_unavailable");
    input.conditional_final_factor_raw = factor;
  }
  output = std::move(input);
  return true;
}
} // namespace xar::ck3_12004
