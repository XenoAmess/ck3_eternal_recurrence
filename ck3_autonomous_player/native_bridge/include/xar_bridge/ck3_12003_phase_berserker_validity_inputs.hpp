#pragma once

#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12002_phase_character.hpp"
#include "xar_bridge/ck3_12002_religion_context.hpp"
#include "xar_bridge/phase_berserker_validity_inputs_v1.hpp"
#include <algorithm>
#include <cstring>
#include <utility>

namespace xar::ck3_12003::phase_berserker {
inline constexpr std::array<std::string_view, 3> kTraitKeys{"craven", "berserker", "calm"};
struct Bindings {
  bool enabled = false;
  void *const *culture_store = nullptr;
  void *const *culture_fallback = nullptr;
  void *const *trait_database = nullptr;
  void *const *rite_fallback = nullptr;
  ck3_12002::phase_character::Bindings traits;
  ck3_12002::religion::ObjectGetter character_rite = nullptr;
  ck3_12002::religion::ObjectGetter character_faith = nullptr;
  ck3_12002::religion::ObjectGetter rite_faith = nullptr;
  ck3_12002::religion::ObjectGetter faith_religion = nullptr;
};
inline Bindings BindImage(std::uintptr_t base, std::string_view sha) noexcept {
  if (!base || sha != ck3_12003::kExecutableSha256) return {};
  Bindings b{};
  b.enabled = true;
  b.culture_store = reinterpret_cast<void *const *>(base + 0x5D1E2F0);
  b.culture_fallback = reinterpret_cast<void *const *>(base + 0x5D1E2E8);
  b.trait_database = reinterpret_cast<void *const *>(base + 0x5C67528);
  b.rite_fallback = reinterpret_cast<void *const *>(base + 0x5C67670);
  b.traits = ck3_12002::phase_character::BindImage(base, ck3_12002::kExecutableSha256);
  b.character_rite = reinterpret_cast<ck3_12002::religion::ObjectGetter>(base + 0x28D2F90);
  b.character_faith = reinterpret_cast<ck3_12002::religion::ObjectGetter>(base + 0x289E750);
  b.rite_faith = reinterpret_cast<ck3_12002::religion::ObjectGetter>(base + 0x24FC560);
  b.faith_religion = reinterpret_cast<ck3_12002::religion::ObjectGetter>(base + 0x2443D40);
  return b;
}
template <typename T> inline T Load(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
inline bool Matches(const void *object, std::uint32_t id, std::size_t offset = 8) {
  return object && id != 0xFFFFFFFFU && Load<std::uint32_t>(object, offset) == id;
}
// Same native CString layout/copy semantics as the closed Religion key reader.
inline bool CopyKey(const void *definition, std::string &out) {
  if (!definition) return false;
  const auto *text = static_cast<const std::byte *>(definition) + 0x18;
  const auto size = Load<std::uint64_t>(text, 0x10);
  const auto capacity = Load<std::uint64_t>(text, 0x18);
  if (size > capacity || size > 4096) return false;
  const auto *data = capacity < 16 ? reinterpret_cast<const char *>(text) : Load<const char *>(text, 0);
  if (!data && size) return false;
  out = size ? std::string(data, static_cast<std::size_t>(size)) : std::string{};
  return true;
}
inline void ReadCulture(const Bindings &b, void *character, game::PhaseBerserkerCultureV1 &out) {
  out.raw_culture_id = Load<std::uint32_t>(character, 0xB0);
  if (!b.culture_store || !b.culture_fallback) {
    out.unavailable_reason = "culture_bindings_unavailable"; return;
  }
  void *culture = nullptr;
  if (out.raw_culture_id != 0xFFFFFFFFU && *b.culture_store) {
    const auto *storage = *b.culture_store;
    const auto index = out.raw_culture_id & 0xFFFFFFU;
    const auto *slots = Load<const std::byte *>(storage, 0x20);
    if (slots && index < Load<std::uint32_t>(storage, 0x2C)) {
      auto *candidate = Load<void *>(slots, static_cast<std::size_t>(index) * 0x10 + 8);
      if (Matches(candidate, out.raw_culture_id, 0x10)) culture = candidate;
    }
  }
  if (!culture || culture == *b.culture_fallback) {
    if (*b.culture_fallback) {
      out.resolution = "native_fallback";
      out.unavailable_reason = "native_fallback_heritage_unobserved";
    } else out.unavailable_reason = "culture_reference_unavailable";
    return;
  }
  out.culture_id = out.raw_culture_id;
  out.resolution = "resolved";
  const auto *culture_template = Load<const void *>(culture, 0x20);
  const auto *resolved = culture_template ? Load<const void *>(culture_template, 0x128) : nullptr;
  const auto *pillars = resolved ? Load<const std::byte *>(resolved, 0x70) : nullptr;
  if (!pillars) { out.unavailable_reason = "culture_selected_pillars_unavailable"; return; }
  std::vector<std::string> keys;
  for (std::size_t index = 0; index < 5; ++index) {
    const auto *pillar = Load<const void *>(pillars, index * 8);
    std::string key;
    if (!CopyKey(pillar, key)) { out.unavailable_reason = "culture_selected_pillar_key_unavailable"; return; }
    keys.push_back(std::move(key));
  }
  out.heritage_north_germanic = std::find(keys.begin(), keys.end(), "heritage_north_germanic") != keys.end();
  out.selected_pillar_keys = std::move(keys);
  out.available = true;
  out.unavailable_reason.clear();
}
inline void ReadReligion(const Bindings &b, void *character, game::PhaseBerserkerReligionV1 &out) {
  out.raw_adopted_rite_id = Load<std::uint32_t>(character, 0xB4);
  if (!b.character_rite || !b.character_faith || !b.rite_faith || !b.faith_religion || !b.rite_fallback) {
    out.unavailable_reason = "religion_bindings_unavailable"; return;
  }
  void *const rite = b.character_rite(character);
  if (rite && rite == *b.rite_fallback) {
    out.resolution = "native_fallback";
    out.unavailable_reason = "native_fallback_religion_unobserved"; return;
  }
  if (!Matches(rite, out.raw_adopted_rite_id)) { out.unavailable_reason = "adopted_rite_reference_unavailable"; return; }
  out.rite_id = out.raw_adopted_rite_id;
  out.raw_faith_id = Load<std::uint32_t>(rite, 0x4B8);
  void *const faith = b.rite_faith(rite);
  if (!Matches(faith, *out.raw_faith_id) || b.character_faith(character) != faith) {
    out.unavailable_reason = "source_faith_reference_unavailable"; return;
  }
  out.faith_id = out.raw_faith_id;
  out.raw_religion_id = Load<std::uint32_t>(faith, 0x8C);
  void *const religion = b.faith_religion(faith);
  if (!Matches(religion, *out.raw_religion_id)) { out.unavailable_reason = "source_religion_reference_unavailable"; return; }
  out.religion_id = out.raw_religion_id;
  out.resolution = "resolved";
  std::string key;
  if (!CopyKey(Load<const void *>(religion, 0x20), key)) { out.unavailable_reason = "religion_definition_key_unavailable"; return; }
  out.germanic = key == "germanic_religion";
  out.religion_key = std::move(key);
  out.available = true;
  out.unavailable_reason.clear();
}
inline void ReadTraits(const Bindings &b, void *character, std::array<game::PhaseBerserkerTraitV1, 3> &out) {
  const auto fail_all = [&](const char *reason) { for (auto &trait : out) trait.unavailable_reason = reason; };
  if (!b.traits.enabled || !b.traits.character_has_trait) { fail_all("trait_bindings_unavailable"); return; }
  if (!b.trait_database || !*b.trait_database) { fail_all("trait_database_unavailable"); return; }
  for (std::size_t index = 0; index < kTraitKeys.size(); ++index) {
    void *definition = ck3_12002::phase_character::FindUniqueTraitDefinition(*b.trait_database, kTraitKeys[index]);
    bool present = false;
    if (!definition || !ck3_12002::phase_character::ReadTraitPresence(b.traits, character,
        std::span<void *const>(&definition, 1), present)) {
      out[index].unavailable_reason = "trait_definition_unresolved"; continue;
    }
    out[index].value = present;
    out[index].unavailable_reason.clear();
  }
}
inline std::optional<game::PhaseBerserkerValidityInputsV1> Read(
    const Bindings &b, void *character, std::uint32_t character_id) {
  if (!b.enabled || !character) return std::nullopt;
  game::PhaseBerserkerValidityInputsV1 out{};
  out.source_character_id = character_id;
  const auto invalidate = [&] {
    out.culture = {}; out.religion = {}; out.traits = {};
    out.culture.unavailable_reason = "source_character_changed";
    out.religion.unavailable_reason = "source_character_changed";
    for (auto &trait : out.traits) trait.unavailable_reason = "source_character_changed";
  };
  if (Load<std::uint32_t>(character, 0x18) != character_id) { invalidate(); return out; }
  ReadCulture(b, character, out.culture);
  ReadReligion(b, character, out.religion);
  ReadTraits(b, character, out.traits);
  if (Load<std::uint32_t>(character, 0x18) != character_id ||
      Load<std::uint32_t>(character, 0xB0) != out.culture.raw_culture_id ||
      Load<std::uint32_t>(character, 0xB4) != out.religion.raw_adopted_rite_id) invalidate();
  return out;
}
} // namespace xar::ck3_12003::phase_berserker
