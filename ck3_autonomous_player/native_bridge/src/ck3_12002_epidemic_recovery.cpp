#include "xar_bridge/ck3_12002_epidemic_recovery.hpp"

#include <windows.h>

#include <algorithm>
#include <cstring>
#include <limits>
#include <string>
#include <vector>

namespace xar::ck3_12002::epidemic_recovery {
namespace {
// Exact 1.20.0.2 source and PE proofs: event12002_recovery_county_modifier_abi,
// event12002_recovery_variable_list_abi and loaded-modifier definition ABI.
constexpr std::uintptr_t kTitleStoreRva = 0x5D1DAF8;
constexpr std::uintptr_t kModifierDatabaseRva = 0x8FD4E0;
constexpr std::uintptr_t kStableKeyHashRva = 0x3F7E240;
constexpr std::uintptr_t kModifierLookupRva = 0xAB8D20;
constexpr std::uintptr_t kModifierFallbackRva = 0x5D1E0B0;
constexpr std::uintptr_t kCountyModifierGetterRva = 0x1AF5D40;
constexpr std::size_t kTitleIdentityOffset = 0x10;
constexpr std::size_t kTitleDefinitionOffset = 0x48;
constexpr std::size_t kTitleDefinitionTierOffset = 0x64;
constexpr std::size_t kModifierNameOffset = 0x18;

bool Read(const void *object, std::size_t offset, void *out,
          std::size_t size) noexcept {
  SIZE_T actual = 0;
  return object && out && size &&
         ReadProcessMemory(GetCurrentProcess(),
                           static_cast<const std::byte *>(object) + offset,
                           out, size, &actual) && actual == size;
}
template <typename T>
bool Read(const void *object, std::size_t offset, T &out) noexcept {
  return Read(object, offset, &out, sizeof(out));
}

bool NameEquals(const void *definition, std::string_view expected) noexcept {
  if (!definition) return false;
  const auto *name = static_cast<const std::byte *>(definition) + kModifierNameOffset;
  std::size_t size = 0, capacity = 0;
  if (!Read(name, 0x10, size) || !Read(name, 0x18, capacity) ||
      size != expected.size() || capacity < size) return false;
  const void *data = name;
  if (capacity >= 16 && !Read(name, 0, data)) return false;
  std::string actual(size, '\0');
  return Read(data, 0, actual.data(), size) && actual == expected;
}

bool ResolveModifier(const Bindings &b, std::string_view key, void *&definition) {
  definition = nullptr;
  void *fallback = nullptr;
  if (!b.modifier_database || !b.stable_key_hash || !b.modifier_lookup ||
      !b.modifier_fallback_slot || !Read(b.modifier_fallback_slot, 0, fallback)) return false;
  void *database = b.modifier_database();
  if (!database || key.size() > std::numeric_limits<std::uint32_t>::max()) return false;
  const auto hash = b.stable_key_hash(database, key.data(), static_cast<std::uint32_t>(key.size()));
  definition = b.modifier_lookup(database, static_cast<std::int32_t>(hash));
  return definition && definition != fallback && NameEquals(definition, key);
}

bool ResolveCounty(const Bindings &b, std::int32_t id, void *&title) noexcept {
  title = nullptr;
  if (!b.landed_title_store_slot || id <= 0) return false;
  void *store = nullptr, *slots = nullptr, *definition = nullptr;
  std::int32_t count = 0, actual_id = -1, tier = -1;
  std::uint32_t tag = 0;
  if (!Read(b.landed_title_store_slot, 0, store) || !Read(store, 0x20, slots) ||
      !Read(store, 0x2C, count) || count <= 0 || !slots) return false;
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(count) ||
      !Read(slots, static_cast<std::size_t>(index) * 0x10 + 8, title) || !title ||
      !Read(title, kTitleIdentityOffset, actual_id) || actual_id != id ||
      !Read(title, 0x14, tag) || tag != 0x4C616E64 ||
      !Read(title, kTitleDefinitionOffset, definition) ||
      !Read(definition, kTitleDefinitionTierOffset, tier) || tier != 2) return false;
  return true;
}

bool Presence(const Bindings &b, void *title, void *definition, bool &present) {
  present = false;
  if (!b.county_modifier_getter) return false;
  CountyModifierResult value{};
  const auto *returned = b.county_modifier_getter(&value, title, definition);
  if (returned != &value || value.present > 1) return false;
  present = value.present != 0;
  return true;
}

bool Frame(const Bindings &b, std::int32_t date, std::int32_t actor) noexcept {
  CoreSnapshotPrefix frame{};
  return ReadCoreSnapshot(b.core, frame) && frame.clock.paused &&
         frame.clock.date_raw == date && frame.map_ready &&
         frame.has_played_character && frame.played_character_alive &&
         frame.played_character_id == actor;
}

ck3_11906::PlayerEpidemicRecoveryV1 Unavailable(
    std::uint64_t revision, std::int32_t date, std::int32_t actor,
    std::int32_t requested_title, const char *reason) {
  ck3_11906::PlayerEpidemicRecoveryV1 value{};
  value.snapshot_revision = revision;
  value.date_raw = date;
  value.played_character_id = actor;
  value.requested_title_id = requested_title;
  value.unavailable_reason = reason;
  return value;
}

// Reuse is permitted only after the new native list ABI is proved equal to
// the existing v1 row reader; the cooperating variable-list proof binds it.
bool ReadTargets(const Bindings &b, std::int32_t actor,
                 std::vector<std::int32_t> &titles) {
  std::int32_t identifier = -1;
  if (!ResolvePhaseVariableIdentifier(b.identifiers,
          ck3_11906::kPlayerEpidemicRecoveryListKeyV1, identifier) ||
      !b.identifiers.variable_context) return false;
  const PhaseVariableTarget target{4, {}, actor};
  const auto *context = b.identifiers.variable_context(&target);
  return ck3_11906::ReadEpidemicRecoveryListRowsV1(context, identifier, titles);
}
} // namespace

Bindings BindImage(std::uintptr_t base, std::string_view hash) noexcept {
  Bindings b{};
  if (!base || hash != kExecutableSha256 || !kTitleStoreRva ||
      !kModifierDatabaseRva || !kCountyModifierGetterRva) return b;
  b.enabled = true;
  b.core = BindCoreImage(base, hash);
  b.identifiers = BindPhaseDefinitionsImage(base, hash);
  b.landed_title_store_slot = reinterpret_cast<void **>(base + kTitleStoreRva);
  b.modifier_fallback_slot = reinterpret_cast<void **>(base + kModifierFallbackRva);
  b.modifier_database = reinterpret_cast<ModifierDatabase>(base + kModifierDatabaseRva);
  b.stable_key_hash = reinterpret_cast<StableKeyHash>(base + kStableKeyHashRva);
  b.modifier_lookup = reinterpret_cast<ModifierLookup>(base + kModifierLookupRva);
  b.county_modifier_getter = reinterpret_cast<CountyModifierGetter>(base + kCountyModifierGetterRva);
  return b;
}

ck3_11906::PlayerEpidemicRecoveryV1 ReadEpidemicRecovery12002(
    const Bindings &b, std::uint64_t revision, std::int32_t date,
    std::int32_t actor, std::int32_t requested_title) noexcept {
  try {
    auto value = Unavailable(revision, date, actor, requested_title, "exact_build_or_frame_unavailable");
    if (!b.enabled || !b.core.enabled || !revision || actor <= 0 || requested_title < 0)
      return value;
    if (!Frame(b, date, actor)) {
      value.unavailable_reason = "played_character_or_paused_frame_unavailable";
      return value;
    }
    std::vector<std::int32_t> titles;
    if (requested_title) titles.push_back(requested_title);
    else if (!ReadTargets(b, actor, titles)) {
      value.unavailable_reason = "variable_list_unavailable";
      return value;
    }
    void *minor = nullptr, *tiny = nullptr;
    if (!titles.empty() && (!ResolveModifier(b, ck3_11906::kPlayerEpidemicRecoveryMinorKeyV1, minor) ||
                           !ResolveModifier(b, ck3_11906::kPlayerEpidemicRecoveryTinyKeyV1, tiny))) {
      value.unavailable_reason = "modifier_definition_unavailable";
      return value;
    }
    for (const auto id : titles) {
      void *title = nullptr;
      if (!ResolveCounty(b, id, title)) {
        value.counties.clear(); value.unavailable_reason = "landed_title_unavailable";
        return value;
      }
      ck3_11906::PlayerEpidemicRecoveryCountyV1 county{};
      county.landed_title_id = id;
      if (!Presence(b, title, minor, county.minor_present) ||
          !Presence(b, title, tiny, county.tiny_present)) {
        value.counties.clear(); value.unavailable_reason = "county_modifier_unavailable";
        return value;
      }
      value.counties.push_back(county);
    }
    if (!Frame(b, date, actor)) {
      value.counties.clear(); value.unavailable_reason = "state_changed";
      return value;
    }
    value.available = true;
    value.unavailable_reason.clear();
    return value;
  } catch (...) {
    return Unavailable(revision, date, actor, requested_title, "internal_error");
  }
}
} // namespace xar::ck3_12002::epidemic_recovery
