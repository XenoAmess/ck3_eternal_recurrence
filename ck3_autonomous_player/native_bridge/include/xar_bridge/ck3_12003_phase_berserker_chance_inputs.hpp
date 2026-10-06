#pragma once

#include "xar_bridge/ck3_12003_phase_berserker_validity_inputs.hpp"
#include "xar_bridge/phase_berserker_chance_inputs_v1.hpp"

namespace xar::ck3_12003::phase_berserker_chance {
using phase_berserker::Load;
using phase_berserker::Matches;
struct Bindings {
  bool enabled = false;
  ck3_12002::phase_character::Bindings character;
  void *const *trait_database = nullptr;
  void *const *character_perk_database = nullptr;
  void *const *dynasty_perk_database = nullptr;
  void *const *house_store = nullptr;
  void *const *house_fallback = nullptr;
  void *const *dynasty_store = nullptr;
  void *const *dynasty_fallback = nullptr;
  void *const *accolade_store = nullptr;
  void *const *accolade_fallback = nullptr;
  void *(*character_perks)(void *) = nullptr;
};
inline Bindings BindImage(std::uintptr_t base, std::string_view sha) noexcept {
  if (!base || sha != ck3_12003::kExecutableSha256) return {};
  Bindings b{};
  b.enabled = true;
  b.character = ck3_12002::phase_character::BindImage(base, ck3_12002::kExecutableSha256);
  b.trait_database = reinterpret_cast<void *const *>(base + 0x5C67528);
  b.character_perk_database = reinterpret_cast<void *const *>(base + 0x5C67128);
  b.dynasty_perk_database = reinterpret_cast<void *const *>(base + 0x5D1FC00);
  b.house_store = reinterpret_cast<void *const *>(base + 0x5D1DAF0);
  b.house_fallback = reinterpret_cast<void *const *>(base + 0x5D1DAE8);
  b.dynasty_store = reinterpret_cast<void *const *>(base + 0x5D1DE78);
  b.dynasty_fallback = reinterpret_cast<void *const *>(base + 0x5D1DE28);
  b.accolade_store = reinterpret_cast<void *const *>(base + 0x5D1ECA0);
  b.accolade_fallback = reinterpret_cast<void *const *>(base + 0x5D1EC40);
  b.character_perks = reinterpret_cast<decltype(b.character_perks)>(base + 0x2919360);
  return b;
}
inline void Known(game::PhaseBerserkerChanceBoolV1 &out, bool value) {
  out.value = value; out.unavailable_reason.clear();
}
inline bool ValidSpan(const void *data, std::int32_t count) {
  return count >= 0 && count <= 65536 && (!count || data);
}
inline void *Resolve(void *const *storage_slot, std::uint32_t id, std::size_t identity_offset) {
  if (!storage_slot || !*storage_slot || id == 0xFFFFFFFFU) return nullptr;
  const auto *storage = *storage_slot;
  const auto index = id & 0xFFFFFFU;
  const auto *slots = Load<const std::byte *>(storage, 0x20);
  if (!slots || index >= Load<std::uint32_t>(storage, 0x2C)) return nullptr;
  auto *object = Load<void *>(slots, static_cast<std::size_t>(index) * 0x10 + 8);
  return Matches(object, id, identity_offset) ? object : nullptr;
}
inline bool Membership(const void *data, std::int32_t count, const void *definition) {
  for (std::int32_t index = 0; index < count; ++index)
    if (Load<const void *>(data, static_cast<std::size_t>(index) * 8) == definition) return true;
  return false;
}
inline void *Definition(void *const *slot, std::string_view key) {
  return slot && *slot ? ck3_12002::phase_character::FindUniqueTraitDefinition(*slot, key) : nullptr;
}
inline void ReadTraits(const Bindings &b, void *character,
                       std::array<game::PhaseBerserkerChanceBoolV1, 18> &out) {
  for (std::size_t index = 0; index < out.size(); ++index) {
    void *definition = Definition(b.trait_database, game::kPhaseBerserkerChanceTraitKeysV1[index]);
    bool value = false;
    if (!definition || !ck3_12002::phase_character::ReadTraitPresence(
        b.character, character, std::span<void *const>(&definition, 1), value)) {
      out[index].unavailable_reason = "trait_definition_or_presence_unavailable"; continue;
    }
    Known(out[index], value);
  }
}
inline void ReadStalwart(const Bindings &b, void *character, game::PhaseBerserkerChancePerkV1 &out) {
  void *definition = Definition(b.character_perk_database, "stalwart_leader_perk");
  if (!definition) { out.presence.unavailable_reason = "stalwart_definition_unresolved"; return; }
  out.definition_key = "stalwart_leader_perk";
  const auto *span = b.character_perks ? b.character_perks(character) : nullptr;
  if (!span) { out.presence.unavailable_reason = "stalwart_owned_span_unavailable"; return; }
  const auto *data = Load<const void *>(span, 0);
  const auto count = Load<std::int32_t>(span, 0xC);
  if (!ValidSpan(data, count)) { out.presence.unavailable_reason = "stalwart_owned_span_unavailable"; return; }
  Known(out.presence, Membership(data, count, definition));
}
inline void ReadDynasty(const Bindings &b, void *character, game::PhaseBerserkerChanceDynastyV1 &out) {
  out.raw_house_id = Load<std::uint32_t>(character, 0x158);
  auto &perk = out.warfare_legacy_3;
  void *definition = Definition(b.dynasty_perk_database, "warfare_legacy_3");
  if (definition) perk.definition_key = "warfare_legacy_3";
  if (out.raw_house_id == 0xFFFFFFFFU) {
    out.house_resolution = "absent"; out.dynasty_resolution = "absent";
    if (definition) Known(perk.presence, false);
    else perk.presence.unavailable_reason = "warfare_definition_unresolved";
    return;
  }
  auto *house = Resolve(b.house_store, out.raw_house_id, 0x10);
  if (!house || !b.house_fallback || house == *b.house_fallback) {
    if (house && b.house_fallback && house == *b.house_fallback) out.house_resolution = "native_fallback";
    perk.presence.unavailable_reason = "house_reference_unavailable"; return;
  }
  out.house_id = out.raw_house_id; out.house_resolution = "resolved";
  out.raw_dynasty_id = Load<std::uint32_t>(house, 0x2C);
  if (*out.raw_dynasty_id == 0xFFFFFFFFU) {
    out.dynasty_resolution = "absent";
    if (definition) Known(perk.presence, false);
    else perk.presence.unavailable_reason = "warfare_definition_unresolved";
    return;
  }
  auto *dynasty = Resolve(b.dynasty_store, *out.raw_dynasty_id, 0x10);
  if (!dynasty || !b.dynasty_fallback || dynasty == *b.dynasty_fallback) {
    if (dynasty && b.dynasty_fallback && dynasty == *b.dynasty_fallback) out.dynasty_resolution = "native_fallback";
    perk.presence.unavailable_reason = "dynasty_reference_unavailable"; return;
  }
  out.dynasty_id = out.raw_dynasty_id; out.dynasty_resolution = "resolved";
  if (!definition) { perk.presence.unavailable_reason = "warfare_definition_unresolved"; return; }
  const auto *data = Load<const void *>(dynasty, 0x178);
  const auto count = Load<std::int32_t>(dynasty, 0x184);
  if (!ValidSpan(data, count)) { perk.presence.unavailable_reason = "warfare_owned_span_unavailable"; return; }
  Known(perk.presence, Membership(data, count, definition));
}
inline void ReadAccolade(const Bindings &b, void *character, game::PhaseBerserkerChanceAccoladeV1 &out) {
  const auto *extension = Load<const void *>(character, 0x1B0);
  if (!extension) { out.resolution = "absent"; Known(out.is_acclaimed, false); return; }
  out.raw_accolade_id = Load<std::uint32_t>(extension, 0x570);
  if (*out.raw_accolade_id == 0xFFFFFFFFU) { out.resolution = "absent"; Known(out.is_acclaimed, false); return; }
  auto *accolade = Resolve(b.accolade_store, *out.raw_accolade_id, 8);
  if (!accolade || !b.accolade_fallback || accolade == *b.accolade_fallback) {
    if (accolade && b.accolade_fallback && accolade == *b.accolade_fallback) out.resolution = "native_fallback";
    out.is_acclaimed.unavailable_reason = "accolade_reference_unavailable"; return;
  }
  if (Load<std::uint32_t>(accolade, 0xC) != 0x4163636FU) {
    out.is_acclaimed.unavailable_reason = "accolade_kind_unavailable"; return;
  }
  out.accolade_id = out.raw_accolade_id; out.resolution = "resolved";
  Known(out.is_acclaimed, true);
}
inline std::optional<game::PhaseBerserkerChanceInputsV1> Read(
    const Bindings &b, void *character, std::uint32_t character_id) {
  if (!b.enabled || !character) return std::nullopt;
  game::PhaseBerserkerChanceInputsV1 out{};
  out.source_character_id = character_id;
  const auto invalidate = [&] {
    out = {}; out.source_character_id = character_id;
    out.is_ai.unavailable_reason = "source_character_changed";
    out.stalwart.presence.unavailable_reason = "source_character_changed";
    out.dynasty.warfare_legacy_3.presence.unavailable_reason = "source_character_changed";
    out.acclaimed.is_acclaimed.unavailable_reason = "source_character_changed";
    for (auto &trait : out.traits) trait.unavailable_reason = "source_character_changed";
  };
  if (Load<std::uint32_t>(character, 0x18) != character_id) { invalidate(); return out; }
  ck3_12002::phase_character::Identity identity{};
  if (ck3_12002::phase_character::ReadIdentity(b.character, character,
      static_cast<std::int32_t>(character_id), identity)) Known(out.is_ai, identity.is_ai);
  else out.is_ai.unavailable_reason = "character_identity_unavailable";
  ReadTraits(b, character, out.traits);
  ReadStalwart(b, character, out.stalwart);
  ReadDynasty(b, character, out.dynasty);
  ReadAccolade(b, character, out.acclaimed);
  if (Load<std::uint32_t>(character, 0x18) != character_id ||
      Load<std::uint32_t>(character, 0x158) != out.dynasty.raw_house_id) invalidate();
  return out;
}
} // namespace xar::ck3_12003::phase_berserker_chance
