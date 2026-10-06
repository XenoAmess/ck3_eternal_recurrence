#pragma once

#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12002_religion_context.hpp"
#include "xar_bridge/phase_warmonger_core_v1.hpp"
#include "xar_bridge/tenet_definition_key_copy.hpp"
#include <cstring>
#include <utility>

namespace xar::ck3_12003::phase_warmonger {
struct Bindings {
  bool enabled = false;
  ck3_12002::religion::ObjectGetter character_rite = nullptr;
  void *const *tenet_database = nullptr;
  void *const *rite_fallback = nullptr;
  bool (*contains)(const void *, const void *) = nullptr;
};
inline Bindings BindImage(std::uintptr_t base, std::string_view sha) noexcept {
  if (!base || sha != ck3_12003::kExecutableSha256) return {};
  return {true,
      reinterpret_cast<ck3_12002::religion::ObjectGetter>(base + 0x28D2F90),
      reinterpret_cast<void *const *>(base + 0x5D1DEB8),
      reinterpret_cast<void *const *>(base + 0x5C67670),
      reinterpret_cast<bool (*)(const void *, const void *)>(base + 0xA11CC0)};
}
template <typename T> inline T Load(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
// The combat collector supplies the already resolved Character occurrence.
// Only its exact adopted Core membership is computed; fallback is explicit.
inline std::optional<game::PhaseWarmongerCoreV1> Read(
    const Bindings &b, void *character, std::uint32_t character_id) {
  if (!b.enabled || !character) return std::nullopt;
  game::PhaseWarmongerCoreV1 out{};
  out.source_character_id = character_id;
  out.raw_adopted_rite_id = Load<std::uint32_t>(character, 0xB4);
  const auto fail = [&](std::string reason) {
    out.available = false;
    out.warmonger_core_membership.reset();
    out.unavailable_reason = std::move(reason);
    return std::optional<game::PhaseWarmongerCoreV1>{out};
  };
  if (Load<std::uint32_t>(character, 0x18) != character_id)
    return fail("source_character_changed");
  if (!b.character_rite || !b.contains || !b.tenet_database || !b.rite_fallback)
    return fail("phase_warmonger_bindings_unavailable");
  void *const rite = b.character_rite(character);
  if (rite && rite == *b.rite_fallback) {
    out.rite_resolution = "native_fallback";
    return fail("native_fallback_core_membership_unobserved");
  }
  if (!rite || out.raw_adopted_rite_id == 0xFFFFFFFFU ||
      Load<std::uint32_t>(rite, 8) != out.raw_adopted_rite_id)
    return fail("adopted_rite_unavailable");
  out.rite_resolution = "adopted";
  out.rite_id = out.raw_adopted_rite_id;
  void *const database = *b.tenet_database;
  if (!database) return fail("tenet_database_unavailable");
  const auto *definitions = Load<const std::byte *>(database, 0xEF0);
  const auto count = Load<std::int32_t>(database, 0xEFC);
  if (count < 0 || count > 8192 || (count && !definitions))
    return fail("tenet_database_collection_unavailable");
  const void *target = nullptr;
  for (std::int32_t index = 0; index < count; ++index) {
    const auto *definition = Load<const void *>(definitions, static_cast<std::size_t>(index) * sizeof(void *));
    std::string key;
    if (!ck3_12002::religion::doctrine12002::detail::CopyTenetDefinitionKeySource(definition, key))
      return fail("tenet_definition_key_unavailable");
    if (key == "tenet_warmonger") {
      target = definition;
      out.target_tenet_key = std::move(key);
      break;
    }
  }
  if (!target) return fail("warmonger_definition_unresolved");
  const auto *core = static_cast<const std::byte *>(rite) + 0x758;
  const auto core_count = Load<std::int32_t>(core, 0xC);
  if (core_count < 0 || (core_count && !Load<const void *>(core, 0)))
    return fail("core_tenet_collection_unavailable");
  const bool membership = b.contains(core, &target);
  if (Load<std::uint32_t>(character, 0x18) != character_id ||
      Load<std::uint32_t>(character, 0xB4) != out.raw_adopted_rite_id ||
      Load<std::uint32_t>(rite, 8) != out.raw_adopted_rite_id)
    return fail("source_identity_changed");
  out.warmonger_core_membership = membership;
  out.available = true;
  out.unavailable_reason.clear();
  return out;
}
} // namespace xar::ck3_12003::phase_warmonger
