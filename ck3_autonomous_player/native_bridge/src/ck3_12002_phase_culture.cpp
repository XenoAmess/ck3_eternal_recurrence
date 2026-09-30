#include "xar_bridge/ck3_12002_phase_culture.hpp"
#include "xar_bridge/ck3_12002.hpp"

#include <array>
#include <cstring>
#include <limits>
#include <vector>

namespace xar::ck3_12002::phase_culture {
namespace {
constexpr std::array<std::string_view, 12> kInnovationKeys{
    "innovation_quilted_armor", "innovation_sarawit", "innovation_legionnaires",
    "innovation_arched_saddle", "innovation_valets", "innovation_tiefutu",
    "innovation_advanced_bowmaking", "innovation_repeating_crossbow",
    "innovation_war_camels", "innovation_elephantry", "innovation_gunpowder",
    "innovation_fire_medicine"};
constexpr std::array<std::string_view, 14> kTraditionKeys{
    "tradition_fp1_coastal_warriors", "tradition_hird", "tradition_futuwaa",
    "tradition_druzhina", "tradition_khadga_puja", "tradition_garuda_warriors",
    "tradition_himalayan_settlers", "tradition_mubarizuns",
    "tradition_burman_royal_army", "tradition_mountaineer_ruralism",
    "tradition_caucasian_wolves", "tradition_roman_legacy",
    "tradition_ep3_audacious_cadets", "tradition_ep3_imperial_tagmata"};
constexpr std::array<std::string_view, 10> kParameterKeys{
    "knights_slightly_more_prone_to_injury", "blademaster_traits_more_common",
    "unlock_zhanmadao", "unlock_burenjia", "unlock_maa_cataphract_archers",
    "unlock_maa_black_armor_cavalry", "unlock_maa_horse_archers",
    "unlock_maa_mangudai", "unlock_emishi_horse_archers_units",
    "unlock_mounted_samurai_units"};
template<class T> T Load(const void *base, std::size_t offset) noexcept {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(base) + offset,
              sizeof(result));
  return result;
}
bool ValidSpan(const void *data, std::int32_t count) noexcept {
  return count >= 0 && count <= 65536 && (count == 0 || data != nullptr);
}
bool KeyEquals(const void *object, std::string_view key) noexcept {
  if (object == nullptr) return false;
  const auto *storage = static_cast<const std::byte *>(object) + 0x18;
  const auto size = Load<std::size_t>(storage, 0x10);
  const auto capacity = Load<std::size_t>(storage, 0x18);
  if (size > capacity || size > 512 || size != key.size()) return false;
  const char *data = capacity < 16 ? reinterpret_cast<const char *>(storage)
                                  : Load<const char *>(storage, 0);
  return data != nullptr && std::string_view(data, size) == key;
}
void *Definition(void **database_slot, std::string_view key,
                 std::string *failure = nullptr) noexcept {
  if (failure != nullptr) failure->clear();
  if (database_slot == nullptr || *database_slot == nullptr) {
    if (failure != nullptr) *failure = "database_unavailable";
    return nullptr;
  }
  void *const database = *database_slot;
  const auto data = Load<void *>(database, kDefinitionObjectsOffset);
  const auto count = Load<std::int32_t>(database, kDefinitionCountOffset);
  if (!ValidSpan(data, count)) {
    if (failure != nullptr) *failure = "malformed_definition_span";
    return nullptr;
  }
  void *match = nullptr;
  for (std::int32_t index = 0; index < count; ++index) {
    void *object = Load<void *>(data, static_cast<std::size_t>(index) * 8);
    if (KeyEquals(object, key)) {
      if (match != nullptr) {
        if (failure != nullptr) *failure = "duplicate_loaded_key";
        return nullptr;
      }
      match = object;
    }
  }
  if (match == nullptr && failure != nullptr) *failure = "loaded_key_not_found";
  return match;
}
void *Resolve(void **store_slot, std::int32_t id,
              std::size_t identity_offset) noexcept {
  if (store_slot == nullptr || *store_slot == nullptr || id == -1) return nullptr;
  void *const store = *store_slot;
  void *const slots = Load<void *>(store, 0x20);
  const auto capacity = Load<std::int32_t>(store, 0x2C);
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  if (slots == nullptr || capacity <= 0 || capacity > 4194304 ||
      index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  void *const object = Load<void *>(slots, static_cast<std::size_t>(index) * 0x10 + 8);
  return object != nullptr && Load<std::int32_t>(object, identity_offset) == id
             ? object : nullptr;
}
bool Optional(void **store, void **fallback, std::int32_t id,
              std::size_t identity_offset, game::OptionalFullIdV3 &out,
              void *&object) noexcept {
  out = {};
  object = nullptr;
  if (id == -1) return true;
  object = Resolve(store, id, identity_offset);
  if (object == nullptr || fallback == nullptr || object == *fallback) return false;
  out = {true, id};
  return true;
}
bool Contains(const void *data, std::int32_t count, const void *needle) noexcept {
  for (std::int32_t index = 0; index < count; ++index) {
    if (Load<void *>(data, static_cast<std::size_t>(index) * 8) == needle)
      return true;
  }
  return false;
}
bool ScriptIdentifier(const Bindings &bindings, std::string_view key,
                      std::int32_t &id) noexcept {
  if (bindings.lookup_script_identifier == nullptr ||
      bindings.script_identifier_name == nullptr) return false;
  const NativeStringView64 view{key.data(), static_cast<std::int64_t>(key.size())};
  id = bindings.lookup_script_identifier(&view);
  if (id < 0 || id == 12) return false;
  const auto *name = bindings.script_identifier_name(id);
  return name != nullptr && *name == key;
}
} // namespace

Bindings BindImage(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings result;
  if (base == 0 || sha != kExecutableSha256) return result;
  result.enabled = true;
  result.character_store = reinterpret_cast<void **>(base + kCharacterStorageSlotRva);
  result.character_fallback = reinterpret_cast<void **>(base + 0x5C67570);
  result.house_store = reinterpret_cast<void **>(base + kHouseStoreSlot);
  result.house_fallback = reinterpret_cast<void **>(base + kHouseFallbackSlot);
  result.dynasty_store = reinterpret_cast<void **>(base + kDynastyStoreSlot);
  result.dynasty_fallback = reinterpret_cast<void **>(base + kDynastyFallbackSlot);
  result.culture_store = reinterpret_cast<void **>(base + kCultureStoreSlot);
  result.culture_fallback = reinterpret_cast<void **>(base + kCultureFallbackSlot);
  result.innovation_database = reinterpret_cast<void **>(base + kInnovationDatabaseSlot);
  result.innovation_fallback = reinterpret_cast<void **>(base + kInnovationFallbackSlot);
  result.tradition_database = reinterpret_cast<void **>(base + kTraditionDatabaseSlot);
  result.tradition_fallback = reinterpret_cast<void **>(base + kTraditionFallbackSlot);
  result.dynasty_perk_database = reinterpret_cast<void **>(base + kDynastyPerkDatabaseSlot);
  result.character_perk_database = reinterpret_cast<void **>(base + kCharacterPerkDatabaseSlot);
  result.character_context = reinterpret_cast<CharacterContext>(base + kCharacterKnightContextRva);
  result.character_perks = reinterpret_cast<CharacterPerks>(base + kCharacterPerksRva);
  result.culture_has_parameter = reinterpret_cast<CultureHasParameter>(base + kCultureHasParameterRva);
  result.lookup_script_identifier = reinterpret_cast<ScriptIdentifierLookup>(base + kScriptIdentifierLookupRva);
  result.script_identifier_name = reinterpret_cast<ScriptIdentifierName>(base + kScriptIdentifierNameRva);
  return result;
}

bool ReadPhaseCharacterCultureRelations(const Bindings &bindings,
                                        void *character,
                                        game::CombatPhaseCharacterV3 &out,
                                        std::string *unavailable_reason) noexcept {
  if (unavailable_reason != nullptr) unavailable_reason->clear();
  const auto fail = [&](std::string_view leaf, std::string_view cause,
                        std::string_view key = {}) {
    if (unavailable_reason != nullptr) {
      *unavailable_reason = "leaf=";
      *unavailable_reason += leaf;
      if (!key.empty()) {
        *unavailable_reason += ":key=";
        *unavailable_reason += key;
      }
      *unavailable_reason += ":character=";
      *unavailable_reason += std::to_string(
          character == nullptr ? -1 : Load<std::int32_t>(character, 0x18));
      *unavailable_reason += ':';
      *unavailable_reason += cause;
    }
    return false;
  };
  if (!bindings.enabled || character == nullptr ||
      bindings.character_context == nullptr || bindings.character_perks == nullptr ||
      bindings.culture_has_parameter == nullptr)
    return fail("bindings", "binding_or_character_unavailable");
  void *house = nullptr;
  if (!Optional(bindings.house_store, bindings.house_fallback,
                Load<std::int32_t>(character, kCharacterHouseIdOffset), 0x10,
                out.house, house)) return fail("house", "full_id_resolution_failed");
  void *const raw_liege = bindings.character_context(character);
  void *liege = nullptr;
  out.liege = {};
  out.liege_house = {};
  if (raw_liege != nullptr && bindings.character_fallback != nullptr &&
      raw_liege != *bindings.character_fallback) {
    if (!Optional(bindings.character_store, bindings.character_fallback,
                  Load<std::int32_t>(raw_liege, 0x18), 0x18,
                  out.liege, liege) || liege != raw_liege)
      return fail("liege", "full_id_resolution_failed");
    void *liege_house = nullptr;
    if (!Optional(bindings.house_store, bindings.house_fallback,
                  Load<std::int32_t>(liege, kCharacterHouseIdOffset), 0x10,
                  out.liege_house, liege_house))
      return fail("liege_house", "full_id_resolution_failed");
  }
  void *dynasty = nullptr;
  if (!Optional(bindings.dynasty_store, bindings.dynasty_fallback,
                house == nullptr ? -1 : Load<std::int32_t>(house, kHouseDynastyIdOffset),
                0x10, out.dynasty, dynasty))
    return fail("dynasty", "full_id_resolution_failed");
  std::string definition_failure;
  void *const warfare = Definition(bindings.dynasty_perk_database,
                                   "warfare_legacy_3", &definition_failure);
  if (warfare == nullptr)
    return fail("dynasty_perk_definition", definition_failure, "warfare_legacy_3");
  void *const stalwart = Definition(bindings.character_perk_database,
                                    "stalwart_leader_perk", &definition_failure);
  if (stalwart == nullptr)
    return fail("character_perk_definition", definition_failure, "stalwart_leader_perk");
  out.warfare_legacy_3 = false;
  if (dynasty != nullptr) {
    const auto data = Load<void *>(dynasty, kDynastyPerksDataOffset);
    const auto count = Load<std::int32_t>(dynasty, kDynastyPerksCountOffset);
    if (!ValidSpan(data, count)) return fail("dynasty_perks", "malformed_owned_span");
    out.warfare_legacy_3 = Contains(data, count, warfare);
  }
  const auto perk_span = bindings.character_perks(character);
  if (perk_span == nullptr) return fail("character_perks", "native_span_unavailable");
  const auto perk_data = Load<void *>(perk_span, 0);
  const auto perk_count = Load<std::int32_t>(perk_span, 0x0C);
  if (!ValidSpan(perk_data, perk_count))
    return fail("character_perks", "malformed_owned_span");
  out.stalwart_leader = Contains(perk_data, perk_count, stalwart);
  const auto relation = Load<void *>(character, kCharacterRelationOffset);
  void *employer = nullptr;
  if (!Optional(bindings.character_store, bindings.character_fallback,
                relation == nullptr ? -1 : Load<std::int32_t>(relation, kRelationEmployerIdOffset),
                0x18, out.employer, employer))
    return fail("employer", "full_id_resolution_failed");

  void *culture = nullptr;
  if (!Optional(bindings.culture_store, bindings.culture_fallback,
                Load<std::int32_t>(character, kCharacterCultureIdOffset),
                0x10, out.culture, culture))
    return fail("culture", "full_id_resolution_failed");
  out.heritage_north_germanic = false;
  out.knights_slightly_more_prone_to_injury = false;
  out.blademaster_traits_more_common = false;
  out.innovations.clear();
  out.traditions.clear();
  out.culture_parameters.clear();
  void *innovation_data = nullptr;
  void *tradition_data = nullptr;
  std::int32_t innovation_count = 0;
  std::int32_t tradition_count = 0;
  if (culture != nullptr) {
    const auto culture_template = Load<void *>(culture, kCultureTemplateOffset);
    const auto resolved = culture_template == nullptr ? nullptr
        : Load<void *>(culture_template, kTemplateResolvedDataOffset);
    if (resolved == nullptr) return fail("culture_resolved_data", "pointer_chain_unavailable");
    const auto pillars = Load<void *>(resolved, kResolvedPillarsDataOffset);
    if (pillars == nullptr) return fail("culture_pillars", "pointer_data_unavailable");
    // The native pillar evaluator indexes categories 0..4; category 5 is
    // the missing-pillar case. These are pointers in a span, never inline.
    for (std::size_t category = 0; category < 5; ++category) {
      const auto pillar = Load<void *>(pillars, category * 8);
      if (pillar == nullptr) return fail("culture_pillars", "selected_pointer_unavailable");
      if (KeyEquals(pillar, "heritage_north_germanic"))
        out.heritage_north_germanic = true;
    }
    innovation_data = Load<void *>(culture, kCultureInnovationsDataOffset);
    innovation_count = Load<std::int32_t>(culture, kCultureInnovationsCountOffset);
    tradition_data = Load<void *>(resolved, kResolvedTraditionsDataOffset);
    tradition_count = Load<std::int32_t>(resolved, kResolvedTraditionsCountOffset);
    if (!ValidSpan(innovation_data, innovation_count))
      return fail("culture_innovations", "malformed_owned_span");
    if (!ValidSpan(tradition_data, tradition_count))
      return fail("culture_traditions", "malformed_owned_span");
  }
  if (bindings.innovation_fallback == nullptr || bindings.tradition_fallback == nullptr)
    return fail("culture_definition_fallbacks", "binding_unavailable");
  for (const auto key : kInnovationKeys) {
    const auto definition = Definition(bindings.innovation_database, key, &definition_failure);
    if (definition == nullptr) return fail("innovation_definition", definition_failure, key);
    if (definition == *bindings.innovation_fallback)
      return fail("innovation_definition", "fallback_object", key);
    out.innovations.push_back({std::string(key), Contains(innovation_data, innovation_count, definition)});
  }
  for (const auto key : kTraditionKeys) {
    const auto definition = Definition(bindings.tradition_database, key, &definition_failure);
    // The exact has-tradition consumer 0x2B12530 calls 0x2B156B0;
    // that resolver uses the Tradition DB at 0x5D1DEE0, not the similarly
    // shaped registry at 0x5D1EB18. Its 0x225D520 indexed lookup returns
    // 0x5D1FB50 on a miss. CCultureTradition's constructor 0x314CEB7
    // writes the same database-object kind checked by this evaluator.
    if (definition == nullptr) return fail("tradition_definition", definition_failure, key);
    if (definition == *bindings.tradition_fallback)
      return fail("tradition_definition", "fallback_object", key);
    if (Load<std::uint32_t>(definition, 0x38) != 0x4744624FU)
      return fail("tradition_definition", "native_object_kind_mismatch", key);
    out.traditions.push_back({std::string(key), Contains(tradition_data, tradition_count, definition)});
  }
  for (const auto key : kParameterKeys) {
    std::int32_t id = -1;
    if (!ScriptIdentifier(bindings, key, id))
      return fail("culture_parameter", "identifier_lookup_or_roundtrip_failed", key);
    const auto present = culture != nullptr && bindings.culture_has_parameter(culture, id);
    out.culture_parameters.push_back({std::string(key), present});
    if (key == "knights_slightly_more_prone_to_injury")
      out.knights_slightly_more_prone_to_injury = present;
    if (key == "blademaster_traits_more_common")
      out.blademaster_traits_more_common = present;
  }
  return true;
}
} // namespace xar::ck3_12002::phase_culture
