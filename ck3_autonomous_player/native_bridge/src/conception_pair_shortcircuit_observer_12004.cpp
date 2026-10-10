#include "xar_bridge/conception_pair_shortcircuit_observer_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <vector>

namespace xar::ck3_12004 {
namespace {

template <typename T>
std::optional<T> Copy(const ConceptionPairShortCircuit12004Bindings &b,
                      std::uintptr_t address) noexcept {
  T value{};
  if (!b.read_memory(b.read_context, reinterpret_cast<const void *>(address),
                     &value, sizeof(value))) return std::nullopt;
  return value;
}

std::optional<std::uintptr_t> CurrentContext(
    const ConceptionPairShortCircuit12004Bindings &b,
    std::uintptr_t character) noexcept {
  const auto scratch = Copy<std::uintptr_t>(b, character + 0x1B0);
  if (!scratch) return std::nullopt;
  if (*scratch != 0) {
    const auto model = Copy<std::uintptr_t>(b, *scratch + 0x258);
    if (!model) return std::nullopt;
    if (*model != 0) {
      const auto owner = Copy<std::uintptr_t>(b, *model + 8);
      if (!owner) return std::nullopt;
      if (*owner == character) return *model + 0x10;
    }
  }
  const auto guard = Copy<std::int32_t>(b, b.image_base + 0x5D67B80);
  // Held4223A84 header:0 uninitialized,-1 initializing; completed epoch
  // values may be negative. Never invoke its initializer or wait helper.
  if (!guard || *guard == 0 || *guard == -1) return std::nullopt;
  return b.image_base + 0x5D67B90;
}

std::optional<std::int64_t> ModifierBf(
    const ConceptionPairShortCircuit12004Bindings &b,
    std::uintptr_t character) noexcept {
  const auto context = CurrentContext(b, character);
  if (!context) return std::nullopt;
  const auto count = Copy<std::int32_t>(b, *context + 0x74);
  if (!count) return std::nullopt;
  if (*count == 0) return std::int64_t{0};
  const auto keys = Copy<std::uintptr_t>(b, *context + 0x68);
  if (!keys || *keys == 0) return std::nullopt;
  auto selected = *keys;
  auto remaining = static_cast<std::int64_t>(*count);
  while (remaining > 0) {
    const auto half = remaining / 2;
    const auto key = Copy<std::uint16_t>(b, selected +
        static_cast<std::uintptr_t>(half) * 2);
    if (!key) return std::nullopt;
    if (*key < 0xBFU)
      selected += static_cast<std::uintptr_t>(remaining - half) * 2;
    remaining = half;
  }
  // Match the actual end equality and lower-bound test, without sorting,
  // deduplicating or imposing a synthetic key-catalogue contract.
  const auto end = *keys + static_cast<std::uintptr_t>(
      static_cast<std::int64_t>(*count) * 2);
  if (selected == end) return std::int64_t{0};
  const auto key = Copy<std::uint16_t>(b, selected);
  if (!key) return std::nullopt;
  if (*key > 0xBFU) return std::int64_t{0};
  const auto index = (selected - *keys) / 2;
  if ((static_cast<std::uint32_t>(index) & 0x80000000U) != 0)
    return std::int64_t{0};
  const auto values = Copy<std::uintptr_t>(b, *context + 0xD0);
  if (!values || *values == 0) return std::nullopt;
  return Copy<std::int64_t>(b, *values + index * 8);
}

std::optional<std::uint32_t> TraitFlags(
    const ConceptionPairShortCircuit12004Bindings &b,
    std::uintptr_t database, std::int32_t id) noexcept {
  const auto count = Copy<std::int32_t>(b, database + 0x5C);
  if (!count) return std::nullopt;
  std::optional<std::uintptr_t> definition;
  if (id >= 0 && id < *count) {
    const auto entries = Copy<std::uintptr_t>(b, database + 0x50);
    if (!entries || *entries == 0) return std::nullopt;
    definition = Copy<std::uintptr_t>(b, *entries +
        static_cast<std::uintptr_t>(id) * 8);
  } else {
    definition = Copy<std::uintptr_t>(b, b.image_base + 0x5D1E318);
  }
  if (!definition || *definition == 0) return std::nullopt;
  return Copy<std::uint32_t>(b, *definition + 0x4A4);
}

} // namespace

ConceptionPairShortCircuit12004Bindings BindConceptionPairShortCircuit12004(
    std::uintptr_t image_base, std::string_view build_version,
    std::string_view executable_sha256,
    ConceptionPairShortCircuit12004ReadMemory read_memory,
    void *read_context) noexcept {
  if (image_base == 0 || build_version != kGameVersion ||
      executable_sha256 != kExecutableSha256 || read_memory == nullptr) return {};
  return {true, image_base, read_memory, read_context};
}

ConceptionCharacterPredicate12004Read ReadConceptionCharacterPredicate12004(
    const ConceptionPairShortCircuit12004Bindings &b,
    std::uintptr_t character, std::uint32_t expected_full_id) {
  ConceptionCharacterPredicate12004Read unavailable;
  unavailable.character_id = expected_full_id;
  if (!b.enabled || b.read_memory == nullptr) {
    unavailable.reason = "exact4_observer_binding_unavailable";
    return unavailable;
  }
  if (character == 0 || expected_full_id == 0xFFFFFFFFU) return unavailable;
  const auto magic = Copy<std::uint32_t>(b, character + 0x1C);
  const auto actual_id = Copy<std::uint32_t>(b, character + 0x18);
  if (!magic || !actual_id || *magic != 0x43686172U ||
      *actual_id != expected_full_id) {
    unavailable.reason = "current_character_identity_unavailable";
    return unavailable;
  }
  ConceptionCharacterPredicate12004Input input;
  input.character_id = expected_full_id;
  input.selector_1a1 = Copy<std::uint8_t>(b, character + 0x1A1);
  input.measure_6c = Copy<std::int16_t>(b, character + 0x6C);
  if (input.measure_6c && *input.measure_6c < 0)
    input.fallback_measure_68 = Copy<std::int16_t>(b, character + 0x68);
  if (!input.selector_1a1 || !input.measure_6c)
    return EvaluateConceptionCharacterPredicate12004(input);
  if (*input.selector_1a1 != 0)
    input.minimum_nonzero_selector = Copy<std::int32_t>(b, b.image_base + 0x5C69EA0);
  else
    input.minimum_zero_selector = Copy<std::int32_t>(b, b.image_base + 0x5C69EA4);
  auto result = EvaluateConceptionCharacterPredicate12004(input);
  if (result.predicate_true) return result;
  if (result.reason != "current_modifier_bf_unread" && result.reason != "trait_count_unread")
    return result;
  if (*input.selector_1a1 != 0) {
    input.current_modifier_bf_raw = ModifierBf(b, character);
    input.maximum_nonzero_selector = Copy<std::int32_t>(b, b.image_base + 0x5C6A1A8);
    result = EvaluateConceptionCharacterPredicate12004(input);
    if (result.predicate_true || result.reason != "trait_count_unread") return result;
  }
  input.trait_count_raw = Copy<std::uint32_t>(b, character + 0x104);
  if (!input.trait_count_raw || *input.trait_count_raw == 0)
    return EvaluateConceptionCharacterPredicate12004(input);
  const auto ids = Copy<std::uintptr_t>(b, character + 0xF8);
  const auto database = Copy<std::uintptr_t>(b, b.image_base + 0x5C67528);
  if (!ids || *ids == 0 || !database || *database == 0)
    return EvaluateConceptionCharacterPredicate12004(input);
  std::vector<std::optional<std::uint32_t>> flags;
  for (std::uint32_t occurrence = 0; occurrence < *input.trait_count_raw; ++occurrence) {
    const auto id = Copy<std::int32_t>(b, *ids +
        static_cast<std::uintptr_t>(occurrence) * 4);
    flags.push_back(id ? TraitFlags(b, *database, *id) : std::nullopt);
    if (!flags.back() || (*flags.back() & 0x20U) == 0) break;
  }
  input.trait_definition_flags = flags;
  return EvaluateConceptionCharacterPredicate12004(input);
}

ConceptionPairShortCircuit12004Read ReadConceptionPairShortCircuit12004(
    const ConceptionPairShortCircuit12004Bindings &b,
    std::uintptr_t first_character, std::uint32_t first_full_id,
    std::uintptr_t second_character, std::uint32_t second_full_id) {
  ConceptionPairShortCircuit12004Read result;
  result.source = "guarded_current_actual4_pair_provider_shortcircuit";
  result.first_character_id = first_full_id;
  result.second_character_id = second_full_id;
  result.first_evaluated = true;
  result.first = ReadConceptionCharacterPredicate12004(b, first_character, first_full_id);
  if (!result.first.predicate_true) { result.reason = "first_predicate_unavailable"; return result; }
  if (*result.first.predicate_true) {
    result.status = "available";
    result.reason = "first_predicate_true";
    result.short_circuits_to_zero = true;
    result.first_output_raw = 0;
    return result;
  }
  result.second_evaluated = true;
  result.second = ReadConceptionCharacterPredicate12004(b, second_character, second_full_id);
  if (!result.second.predicate_true) { result.reason = "second_predicate_unavailable"; return result; }
  result.status = "available";
  result.short_circuits_to_zero = *result.second.predicate_true;
  result.reason = *result.second.predicate_true ? "second_predicate_true" :
                                               "both_false_continue_provider";
  if (*result.second.predicate_true) result.first_output_raw = 0;
  return result;
}

} // namespace xar::ck3_12004
