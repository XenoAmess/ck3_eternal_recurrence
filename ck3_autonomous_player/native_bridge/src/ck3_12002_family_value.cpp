#include "xar_bridge/ck3_12002_family_value.hpp"

#include <cstring>

namespace xar::ck3_12002::family_value {
namespace {

template <typename T>
T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

void *ResolveComponent(void **slot, void **fallback, std::int32_t id) noexcept {
  if (slot == nullptr || *slot == nullptr || fallback == nullptr || id == -1)
    return nullptr;
  const auto storage = *slot;
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  const auto capacity = Load<std::int32_t>(storage, 0x2C);
  const auto slots = Load<void *>(storage, 0x20);
  if (slots == nullptr || capacity <= 0 || capacity > 4'194'304 ||
      index >= static_cast<std::uint32_t>(capacity))
    return nullptr;
  const auto component = Load<void *>(slots, index * 0x10ULL + 8);
  return component != nullptr && component != *fallback &&
                 Load<std::int32_t>(component, 0x10) == id
             ? component : nullptr;
}

bool Fail(std::string_view *reason, std::string_view value) noexcept {
  if (reason != nullptr) *reason = value;
  return false;
}

} // namespace

Bindings BindImage(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings bindings{};
  bindings.core = BindCoreImage(base, sha);
  if (!bindings.core.enabled) return bindings;
  bindings.enabled = true;
  bindings.house_store = reinterpret_cast<void **>(base + kHouseStoreSlotRva);
  bindings.house_fallback = reinterpret_cast<void **>(base + kHouseFallbackSlotRva);
  bindings.dynasty_store = reinterpret_cast<void **>(base + kDynastyStoreSlotRva);
  bindings.dynasty_fallback = reinterpret_cast<void **>(base + kDynastyFallbackSlotRva);
  bindings.fertility_gate = reinterpret_cast<FertilityGate>(base + kFertilityGateRva);
  return bindings;
}

bool ReadCharacterLineage(const Bindings &bindings, const void *character,
                          Lineage &output, std::string_view *reason) noexcept {
  output = {};
  if (reason != nullptr) *reason = {};
  if (!bindings.enabled || character == nullptr)
    return Fail(reason, "lineage_binding_or_character_unavailable");
  const auto house_id = Load<std::int32_t>(character, kCharacterHouseOffset);
  if (house_id == -1) return true;
  const auto house = ResolveComponent(bindings.house_store,
                                     bindings.house_fallback, house_id);
  if (house == nullptr) return Fail(reason, "house_full_id_unavailable");
  Lineage result{};
  result.house_id = house_id;
  const auto dynasty_id = Load<std::int32_t>(house, kHouseDynastyOffset);
  if (dynasty_id != -1 &&
      ResolveComponent(bindings.dynasty_store, bindings.dynasty_fallback,
                       dynasty_id) == nullptr)
    return Fail(reason, "dynasty_full_id_unavailable");
  result.dynasty_id = dynasty_id;
  output = result;
  return true;
}

bool ReadCharacterValue(const Bindings &bindings, std::int32_t id,
                        CharacterValue &output, bool read_fertility,
                        std::string_view *reason,
                        OptionalMemoryRead optional_memory_read,
                        void *optional_memory_context) noexcept {
  output = {};
  if (reason != nullptr) *reason = {};
  if (!bindings.enabled || !bindings.core.enabled)
    return Fail(reason, "family_value_binding_unavailable");
  const auto character = ResolveCoreCharacter(bindings.core, id);
  if (character == nullptr ||
      Load<void *>(character, kCharacterDeathDataOffset) != nullptr)
    return Fail(reason, "character_full_id_or_liveness_unavailable");
  CharacterValue result{};
  result.character_id = id;
  result.age_raw = Load<std::int16_t>(character, kCharacterAgeOffset);
  if (optional_memory_read != nullptr) {
    std::int16_t raw = 0;
    if (optional_memory_read(optional_memory_context,
                            reinterpret_cast<std::uintptr_t>(character) +
                                kCharacterScorerAgeOverrideOffset,
                            &raw, sizeof(raw)))
      result.scorer_age_override_raw = raw;
  }
  result.sex_selector_raw = Load<std::uint8_t>(character,
                                              kCharacterSexSelectorOffset);
  if (result.sex_selector_raw > 1)
    return Fail(reason, "character_sex_selector_unavailable");
  if (!ReadCharacterLineage(bindings, character, result.lineage, reason))
    return false;
  const auto court = Load<void *>(character, kCharacterCourtRelationOffset);
  if (court != nullptr) {
    result.employer_character_id = Load<std::int32_t>(
        court, kCourtRelationEmployerOffset);
    if (result.employer_character_id != -1 &&
        ResolveCoreCharacter(bindings.core, result.employer_character_id) == nullptr)
      return Fail(reason, "employer_full_id_unavailable");
  }
  if (read_fertility) {
    if (bindings.fertility_gate == nullptr)
      return Fail(reason, "native_fertility_gate_unavailable");
    auto &fertility = result.fertility;
    fertility.available = true;
    const auto extension = Load<void *>(character, kFertilityExtensionOffset);
    if (extension != nullptr) {
      fertility.extension_present = true;
      fertility.native_gate_evaluated = true;
      fertility.native_gate_allows = bindings.fertility_gate(character);
      if (fertility.native_gate_allows)
        fertility.effective_raw = Load<std::int64_t>(extension, kFertilityRawOffset);
    }
  }
  output = result;
  return true;
}

} // namespace xar::ck3_12002::family_value
