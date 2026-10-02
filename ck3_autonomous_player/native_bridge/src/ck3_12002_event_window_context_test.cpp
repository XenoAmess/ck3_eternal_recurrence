#include "xar_bridge/ck3_12002_event_window_context.hpp"




#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <map>
#include <string>

namespace {

constexpr std::int32_t kEventId = 0x01000029;
constexpr std::int32_t kCalculatedEventId = 812'449;
constexpr std::int32_t kRuntimeStatsOrdinal = 37;
constexpr std::int32_t kCharacterId = 42;
constexpr std::int32_t kCharacterTypeNameIdentifier = -2'130'706'328;
constexpr std::int32_t kSavedRootNameIdentifier = -2'130'706'232;
constexpr std::int32_t kStaleSavedRootNameIdentifier = -2'113'929'016;
constexpr std::uint64_t kRevision = 17;
void *g_local_player = nullptr;
void *g_active_event = nullptr;
void *g_secondary_active_event = nullptr;
void *g_secondary_event_definition = nullptr;
void *g_scheme_type_database = nullptr;
void *g_scheme_type = nullptr;
void *g_scheme_type_fallback = nullptr;
void *g_generic_value_type_registry = nullptr;
void *g_script_identifier_table = nullptr;
const std::string *g_generic_value_type_name_fallback = nullptr;
const std::string *g_script_identifier_fallback = nullptr;
std::map<std::int32_t, const std::string *> g_generic_value_type_names;
std::map<std::int32_t, const std::string *> g_script_identifier_names;
std::map<std::int32_t, std::string_view> g_script_identifier_text;

enum class EventIdentityDrift {
  none,
  active_event_pointer,
  event_data_pointer,
  calculated_id,
  runtime_stats_ordinal,
  definition_key,
  instance_id,
  scope_subtype,
  saved_scope_payload,
  splash_current_item,
  splash_transition_item,
};

EventIdentityDrift g_event_identity_drift = EventIdentityDrift::none;
std::uint32_t g_current_event_calls = 0;
void *g_splash_window = nullptr;

template <typename T> void Store(void *base, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}

template <typename T> T Load(const void *base, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset,
              sizeof(value));
  return value;
}

void StoreInlineString(void *object, const char *value) {
  const auto size = std::strlen(value);
  std::memcpy(object, value, size);
  Store<std::uint64_t>(object, 0x10, size);
  Store<std::uint64_t>(object, 0x18, 15);
}

template <std::size_t Size>
void StoreHeapString(void *object, std::array<char, Size> &backing,
                     const char *value) {
  const auto size = std::strlen(value);
  if (size >= backing.size()) {
    return;
  }
  std::memcpy(backing.data(), value, size);
  Store<const char *>(object, 0x00, backing.data());
  Store<std::uint64_t>(object, 0x10, size);
  Store<std::uint64_t>(object, 0x18, backing.size() - 1);
}

void *GetLocalPlayer(void *) { return g_local_player; }
std::int32_t HashStableKey(void *context, const char *data,
                           std::uint32_t size) {
  if (context != g_scheme_type_database) {
    return 0;
  }
  std::uint32_t hash = 2'166'136'261U;
  for (std::uint32_t index = 0; index < size; ++index) {
    hash ^= static_cast<unsigned char>(data[index]);
    hash *= 16'777'619U;
  }
  return static_cast<std::int32_t>(hash);
}
void *LookupSchemeType(void *database, std::int32_t hash) {
  constexpr char key[] = "murder";
  return database == g_scheme_type_database &&
                 hash == HashStableKey(g_scheme_type_database, key,
                                       sizeof(key) - 1)
             ? g_scheme_type
             : g_scheme_type_fallback;
}
void *GetGenericValueTypeRegistry() {
  return g_generic_value_type_registry;
}
const std::string *ResolveGenericValueTypeName(std::int32_t identifier) {
  const auto found = g_generic_value_type_names.find(identifier);
  return found == g_generic_value_type_names.end()
             ? g_generic_value_type_name_fallback
             : found->second;
}
void *GetScriptIdentifierTable() { return g_script_identifier_table; }
const std::string *ResolveScriptIdentifierName(void *table,
                                               std::int32_t identifier) {
  if (table != g_script_identifier_table) {
    return g_script_identifier_fallback;
  }
  const auto index = static_cast<std::uint32_t>(identifier) & 0x00FFFFFFU;
  for (const auto &[candidate_identifier, candidate_name] :
       g_script_identifier_names) {
    if ((static_cast<std::uint32_t>(candidate_identifier) & 0x00FFFFFFU) ==
        index) {
      return candidate_name;
    }
  }
  return g_script_identifier_fallback;
}
struct NativeStringView32 {
  const char *data = nullptr;
  std::int32_t size = 0;
  std::int32_t padding = 0;
};
std::int32_t *LookupScriptIdentifierId(void *table, std::int32_t *output,
                                      const void *raw_view) {
  if (table != g_script_identifier_table || output == nullptr ||
      raw_view == nullptr) {
    return nullptr;
  }
  const auto &view = *static_cast<const NativeStringView32 *>(raw_view);
  if (view.data == nullptr || view.size <= 0 || view.padding != 0) {
    return nullptr;
  }
  const std::string_view name(view.data, static_cast<std::size_t>(view.size));
  for (const auto &[identifier, candidate] : g_script_identifier_text) {
    if (candidate == name) {
      *output = identifier;
      return output;
    }
  }
  return nullptr;
}
void *GetCurrentEvent(void *) {
  ++g_current_event_calls;
  if (g_current_event_calls >= 3) {
    switch (g_event_identity_drift) {
    case EventIdentityDrift::active_event_pointer:
      return g_secondary_active_event;
    case EventIdentityDrift::event_data_pointer:
      Store<void *>(g_active_event, 0x1B0, g_secondary_event_definition);
      break;
    case EventIdentityDrift::calculated_id: {
      void *const definition = Load<void *>(g_active_event, 0x1B0);
      Store<std::int32_t>(definition, 0x08, kCalculatedEventId + 1);
      break;
    }
    case EventIdentityDrift::runtime_stats_ordinal: {
      void *const definition = Load<void *>(g_active_event, 0x1B0);
      Store<std::int32_t>(definition, 0x0C, kRuntimeStatsOrdinal + 1);
      break;
    }
    case EventIdentityDrift::definition_key: {
      void *const definition = Load<void *>(g_active_event, 0x1B0);
      StoreInlineString(static_cast<std::byte *>(definition) + 0x10,
                        "xar_test.0002");
      break;
    }
    case EventIdentityDrift::instance_id:
      Store<std::int32_t>(g_active_event, 0x1BC, kEventId + 1);
      break;
    case EventIdentityDrift::scope_subtype:
      Store<std::uint16_t>(g_active_event, 0x02, 1);
      break;
    case EventIdentityDrift::saved_scope_payload: {
      void *const rows = Load<void *>(g_active_event, 0x18);
      Store<std::uint64_t>(rows, 0x10, kCharacterId);
      break;
    }
    case EventIdentityDrift::splash_current_item:
      Store<void *>(g_splash_window, 0xD0, nullptr);
      break;
    case EventIdentityDrift::splash_transition_item:
      Store<void *>(g_splash_window, 0xD8, g_active_event);
      break;
    case EventIdentityDrift::none:
      break;
    }
  }
  return g_active_event;
}

struct Fixture {
  std::array<std::byte, 0xB0> game_state{};
  std::array<std::byte, 0x30> jomini{};
  std::array<std::byte, 0x200> players{};
  std::array<std::byte, 0x80> local_player{};
  std::array<std::byte, 0x34500> game_data{};
  std::array<std::byte, 0x1C0> active_event{};
  std::array<std::byte, 0x1C0> secondary_active_event{};
  std::array<std::byte, 0x1C0> event_definition{};
  std::array<std::byte, 0x1C0> secondary_event_definition{};
  std::array<std::array<std::byte, 0x480>, 4> authored_options{};
  std::array<void *, 4> authored_option_pointers{};
  std::array<std::byte, 0x98> idler{};
  std::array<std::byte, 0x30> manager{};
  std::array<void *, 2> windows{};
  std::array<std::byte, 0x8F0> window{};
  std::array<std::byte, 0x8F0> secondary_window{};
  std::array<std::byte, 0xE0> splash_window{};
  std::array<std::byte, 0x20> splash_item{};
  std::array<void *, 2> splash_items{};
  std::array<std::byte, 0x370> option_items{};
  std::array<std::byte, 0xC0> effect_rows{};
  std::array<std::byte, 0x80> trait_database{};
  std::array<void *, 2> trait_definitions{};
  std::array<std::byte, 0x60> brave_trait{};
  std::array<std::byte, 0x60> calm_trait{};
  std::array<std::byte, 0x20> scheme_type_database{};
  std::array<std::byte, 0x60> murder_scheme_type{};
  std::array<std::byte, 0x60> scheme_type_fallback{};
  std::array<std::byte, 0x20> generic_value_type_registry{};
  std::array<std::byte, 5 * 0x50> generic_value_type_entries{};
  std::array<std::byte, 0x10> script_identifier_table{};
  std::array<std::byte, 0x20> generic_province_name{};
  std::array<std::byte, 0x20> generic_character_name{};
  std::array<std::byte, 0x20> generic_value_type_name_fallback{};
  std::array<std::byte, 0x20> saved_root_name{};
  std::array<char, 64> saved_root_name_backing{};
  std::array<std::byte, 0x20> saved_province_name{};
  std::array<char, 32> saved_province_name_backing{};
  std::array<std::byte, 0x20> script_identifier_fallback{};
  std::array<std::byte, 0x40> character_storage{};
  std::array<std::byte, 64 * 0x10> character_slots{};
  std::array<std::byte, 0x40> character{};
  std::array<std::byte, 2 * 0x18> saved_scope_rows{};
  void *game_state_pointer = game_state.data();
  void *jomini_pointer = jomini.data();
  void *trait_database_pointer = trait_database.data();
  void *scheme_type_database_pointer = scheme_type_database.data();
  void *scheme_type_fallback_pointer = scheme_type_fallback.data();
  void *character_storage_pointer = character_storage.data();
  xar::ck3_12002::EventWindowBindings bindings{};

  Fixture() {
    g_local_player = local_player.data();
    g_active_event = active_event.data();
    g_secondary_active_event = secondary_active_event.data();
    g_secondary_event_definition = secondary_event_definition.data();
    g_scheme_type_database = scheme_type_database.data();
    g_scheme_type = murder_scheme_type.data();
    g_scheme_type_fallback = scheme_type_fallback.data();
    g_generic_value_type_registry = generic_value_type_registry.data();
    g_script_identifier_table = script_identifier_table.data();
    StoreInlineString(generic_province_name.data(), "province");
    StoreInlineString(generic_character_name.data(), "character");
    StoreInlineString(generic_value_type_name_fallback.data(), "fallback");
    StoreHeapString(saved_root_name.data(), saved_root_name_backing,
                    "xar_scope_root_control");
    StoreHeapString(saved_province_name.data(), saved_province_name_backing,
                    "province_control");
    StoreInlineString(script_identifier_fallback.data(), "fallback");
    g_script_identifier_fallback =
        reinterpret_cast<const std::string *>(
            script_identifier_fallback.data());
    g_generic_value_type_name_fallback =
        reinterpret_cast<const std::string *>(
            generic_value_type_name_fallback.data());
    g_generic_value_type_names.clear();
    g_generic_value_type_names.emplace(
        103, reinterpret_cast<const std::string *>(
                 generic_province_name.data()));
    g_generic_value_type_names.emplace(
        kCharacterTypeNameIdentifier,
        reinterpret_cast<const std::string *>(generic_character_name.data()));
    g_script_identifier_names.clear();
    g_script_identifier_names.emplace(
        kSavedRootNameIdentifier,
        reinterpret_cast<const std::string *>(saved_root_name.data()));
    g_script_identifier_names.emplace(
        201,
        reinterpret_cast<const std::string *>(saved_province_name.data()));
    g_script_identifier_text.clear();
    g_script_identifier_text.emplace(kSavedRootNameIdentifier,
                                     "xar_scope_root_control");
    g_script_identifier_text.emplace(201, "province_control");
    g_event_identity_drift = EventIdentityDrift::none;
    g_current_event_calls = 0;
    g_splash_window = splash_window.data();
    Store<std::int32_t>(game_state.data(), 0x08, 741221);
    Store<std::int32_t>(game_state.data(), 0x70, 0);
    Store<void *>(game_state.data(), 0xA0, game_data.data());
    Store<void *>(jomini.data(), 0x10, idler.data());
    Store<void *>(jomini.data(), 0x18, players.data());
    Store<std::uint8_t>(jomini.data(), 0x20, 1);
    Store<std::int32_t>(players.data(), 0x1F0, 0);
    Store<std::int32_t>(local_player.data(), 0x70, 0);
    Store<void *>(active_event.data(), 0x1B0, event_definition.data());
    Store<std::int32_t>(active_event.data(), 0x1BC, kEventId);
    Store<std::uint16_t>(active_event.data(), 0x00, 4);
    Store<std::uint16_t>(active_event.data(), 0x02, 0);
    Store<std::int64_t>(active_event.data(), 0x08, kCharacterId);
    Store<void *>(active_event.data(), 0x18, saved_scope_rows.data());
    Store<std::int32_t>(active_event.data(), 0x20, 2);
    Store<std::int32_t>(active_event.data(), 0x24, 2);
    Store<std::int32_t>(saved_scope_rows.data(), 0x00,
                        kSavedRootNameIdentifier);
    Store<std::uint16_t>(saved_scope_rows.data(), 0x08, 4);
    Store<std::uint16_t>(saved_scope_rows.data(), 0x0A, 2);
    Store<std::int64_t>(saved_scope_rows.data(), 0x10, kCharacterId);
    Store<std::int32_t>(saved_scope_rows.data() + 0x18, 0x00, 201);
    Store<std::uint16_t>(saved_scope_rows.data() + 0x18, 0x08, 3);
    Store<std::uint16_t>(saved_scope_rows.data() + 0x18, 0x0A, 1);
    Store<std::int64_t>(saved_scope_rows.data() + 0x18, 0x10,
                        0x123456789LL);
    Store<void *>(secondary_active_event.data(), 0x1B0,
                  event_definition.data());
    Store<std::int32_t>(secondary_active_event.data(), 0x1BC, kEventId);
    Store<std::int32_t>(event_definition.data(), 0x08, kCalculatedEventId);
    Store<std::int32_t>(event_definition.data(), 0x0C, kRuntimeStatsOrdinal);
    StoreInlineString(event_definition.data() + 0x10, "xar_test.0001");
    for (std::size_t index = 0; index < authored_options.size(); ++index) {
      authored_option_pointers[index] = authored_options[index].data();
    }
    Store<std::uint8_t>(authored_options[3].data(), 0x412, 1);
    Store<void *>(event_definition.data(), 0x1A0,
                  authored_option_pointers.data());
    Store<std::int32_t>(event_definition.data(), 0x1A8, 4);
    Store<std::int32_t>(event_definition.data(), 0x1AC, 4);
    Store<std::int32_t>(secondary_event_definition.data(), 0x08,
                        kCalculatedEventId);
    Store<std::int32_t>(secondary_event_definition.data(), 0x0C,
                        kRuntimeStatsOrdinal);
    StoreInlineString(secondary_event_definition.data() + 0x10,
                      "xar_test.0001");
    Store<std::int32_t>(secondary_event_definition.data(), 0x1AC, 4);

    Store<void *>(generic_value_type_registry.data(), 0x00,
                  generic_value_type_entries.data());
    Store<std::int32_t>(generic_value_type_registry.data(), 0x0C, 5);
    Store<std::int32_t>(generic_value_type_entries.data() + 3 * 0x50, 0x00,
                        103);
    Store<std::int32_t>(generic_value_type_entries.data() + 4 * 0x50, 0x00,
                        kCharacterTypeNameIdentifier);
    Store<void *>(character_storage.data(), 0x20, character_slots.data());
    Store<std::int32_t>(character_storage.data(), 0x2C, 64);
    Store<void *>(character_slots.data() + kCharacterId * 0x10, 0x08,
                  character.data());
    Store<std::int32_t>(character.data(), 0x18, kCharacterId);

    trait_definitions[0] = brave_trait.data();
    trait_definitions[1] = calm_trait.data();
    Store<void *>(trait_database.data(), 0x50, trait_definitions.data());
    Store<std::int32_t>(trait_database.data(), 0x5C, 2);
    Store<std::int32_t>(brave_trait.data(), 0x10, 123);
    StoreInlineString(brave_trait.data() + 0x18, "brave");
    Store<std::int32_t>(calm_trait.data(), 0x10, 124);
    StoreInlineString(calm_trait.data() + 0x18, "calm");

    bindings.events.core.enabled = true;
    bindings.events.core.game_state_slot = &game_state_pointer;
    bindings.events.core.jomini_state_slot = &jomini_pointer;
    bindings.events.core.get_local_player = &GetLocalPlayer;
    bindings.events.get_current_event = &GetCurrentEvent;
    bindings.ingame_interface_idler_vtable = 0x1844BC408;
    bindings.event_window_primary_vtable = 0x184597910;
    bindings.splash_window_primary_vtable = 0x184596D38;
    bindings.scheme_type_primary_vtable = 0x1848B9F20;
    bindings.trait_database_slot = &trait_database_pointer;
    bindings.scheme_type_database_slot = &scheme_type_database_pointer;
    bindings.scheme_type_fallback_slot = &scheme_type_fallback_pointer;
    bindings.events.core.character_storage_slot = &character_storage_pointer;
    bindings.expected_generic_value_type_registry =
        generic_value_type_registry.data();
    bindings.generic_value_type_name_fallback =
        reinterpret_cast<const std::string *>(
            generic_value_type_name_fallback.data());
    bindings.script_identifier_name_fallback =
        reinterpret_cast<const std::string *>(
            script_identifier_fallback.data());
    bindings.hash_stable_key = &HashStableKey;
    bindings.lookup_scheme_type = &LookupSchemeType;
    bindings.get_script_identifier_table = &GetScriptIdentifierTable;
    bindings.lookup_script_identifier_id = &LookupScriptIdentifierId;
    bindings.get_generic_value_type_registry =
        &GetGenericValueTypeRegistry;
    bindings.resolve_generic_value_type_name =
        &ResolveGenericValueTypeName;
    bindings.resolve_script_identifier_name =
        &ResolveScriptIdentifierName;
    Store<std::uintptr_t>(murder_scheme_type.data(), 0,
                          bindings.scheme_type_primary_vtable);
    StoreInlineString(murder_scheme_type.data() + 0x18, "murder");
    Store<std::uintptr_t>(idler.data(), 0,
                          bindings.ingame_interface_idler_vtable);
    Store<void *>(idler.data(), 0x28, manager.data());
    windows[0] = window.data();
    Store<void *>(manager.data(), 0x18, windows.data());
    Store<std::int32_t>(manager.data(), 0x24, 1);
    Store<std::uintptr_t>(window.data(), 0,
                          bindings.event_window_primary_vtable);
    auto *data = window.data() + 0xB8;
    Store<std::int32_t>(data, 0x00, kEventId);
    Store<void *>(data, 0x10, option_items.data());
    Store<std::int32_t>(data, 0x18, 2);
    Store<std::int32_t>(data, 0x1C, 1);
    Store<std::int32_t>(data, 0x2C, 0);
    InitializeOption(0, 3, false, true);
    InitializeEffectRows();
  }

  void InitializeOption(std::size_t rendered, std::int32_t native_index,
                        bool enabled, bool fallback) {
    auto *const item = option_items.data() + rendered * 0x1B8;
    Store<void *>(item, 0x160, window.data() + 0xB8);
    StoreInlineString(item + 0x170, rendered == 0 ? "Wait" : "Leave");
    StoreInlineString(item + 0x190, enabled ? "" : "Not today");
    Store<std::int32_t>(item, 0x1B0, native_index);
    Store<std::uint8_t>(item, 0x1B4, enabled ? 1 : 0);
    Store<std::uint8_t>(item, 0x1B5, fallback ? 1 : 0);
  }

  void InitializeEffectRows() {
    auto *const item = option_items.data();
    Store<void *>(item, 0x88, effect_rows.data());
    Store<std::int32_t>(item, 0x90, 8);
    Store<std::int32_t>(item, 0x94, 5);

    auto *row = effect_rows.data();
    Store<void *>(row, 0x00, brave_trait.data());
    Store<std::int32_t>(row, 0x10, 0);
    Store<std::uint8_t>(row, 0x14, 1);

    row += 0x18;
    Store<std::int32_t>(row, 0x10, 1);
    Store<std::uint8_t>(row, 0x14, 0);
    Store<std::uint8_t>(row, 0x16, 1);
    Store<std::uint8_t>(row, 0x17, 1);

    row += 0x18;
    Store<std::uintptr_t>(row, 0x00, 0x11111111U);
    Store<std::uintptr_t>(row, 0x08, 0x22222222U);
    Store<std::int32_t>(row, 0x10, 4);
    Store<std::uint8_t>(row, 0x14, 1);

    row += 0x18;
    Store<std::uintptr_t>(row, 0x00, 0x33333333U);
    Store<void *>(row, 0x08, murder_scheme_type.data());
    Store<std::int32_t>(row, 0x10, 5);
    Store<std::uint8_t>(row, 0x14, 1);

    row += 0x18;
    Store<std::uintptr_t>(row, 0x00, 0x44444444U);
    Store<std::uintptr_t>(row, 0x08, 0x55555555U);
    Store<std::int32_t>(row, 0x10, 17);
    Store<std::uint8_t>(row, 0x14, 0xFF);
    Store<std::uint8_t>(row, 0x15, 0xFF);
    Store<std::uint8_t>(row, 0x16, 0xFF);
  }

  void UseSplash() {
    Store<std::int32_t>(manager.data(), 0x24, 0);
    Store<void *>(manager.data(), 0x10, splash_window.data());
    Store<std::uintptr_t>(splash_window.data(), 0, bindings.splash_window_primary_vtable);
    splash_items[0] = splash_item.data();
    Store<void *>(splash_window.data(), 0xB8, splash_items.data());
    Store<std::int32_t>(splash_window.data(), 0xC0, 2);
    Store<std::int32_t>(splash_window.data(), 0xC4, 1);
    Store<void *>(splash_window.data(), 0xD0, splash_item.data());
    Store<void *>(splash_item.data(), 0, splash_window.data());
    Store<void *>(splash_item.data(), 8, active_event.data());
    Store<void *>(splash_item.data(), 0x10, window.data() + 0xB8);
  }
};

bool TestMigration() {
  using namespace xar;
  Fixture fixture;
  game::EventWindowContextV1 output{};
  auto read = [&]() { return ck3_12002::ReadEventWindowContextV1(
    fixture.bindings, kRevision, kEventId, output) ==
    game::ReadEventWindowContextResultV1::available; };
  if (!read() || output.event_definition_key != "xar_test.0001" ||
      output.root_scope->typed_identity.character_id != kCharacterId ||
      output.saved_scopes.size() != 2 || output.options.size() != 1 ||
      !output.options[0].cancel || !output.effect_indicators_ready ||
      output.effect_preview_ready || output.semantic_decision_ready) return false;
  const auto &rows = output.options[0].effect_indicators;
  if (rows.size() != 5 || rows[0].stable_key != "brave" ||
      !rows[0].identity_available || rows[0].native_id != 123 ||
      rows[1].kind != game::EventEffectIndicatorKindV1::stress ||
      !rows[1].affected_by_trait || !rows[1].critical ||
      rows[2].kind != game::EventEffectIndicatorKindV1::death ||
      rows[2].raw_kind != 4 || rows[3].stable_key != "murder" ||
      rows[3].raw_kind != 5 || rows[4].kind != game::EventEffectIndicatorKindV1::unknown)
    return false;
  // New fulfillment-only and combined rows; byte +0x15 now denotes the
  // secondary fulfillment direction, while stress flags moved to +0x16/+0x17.
  Store<std::int32_t>(fixture.effect_rows.data() + 2 * 0x18, 0x10, 2);
  Store<std::int32_t>(fixture.effect_rows.data() + 3 * 0x18, 0x10, 3);
  Store<std::uint8_t>(fixture.effect_rows.data() + 3 * 0x18, 0x15, 0);
  Store<std::uint8_t>(fixture.effect_rows.data() + 3 * 0x18, 0x16, 1);
  Store<std::uint8_t>(fixture.effect_rows.data() + 3 * 0x18, 0x17, 1);
  if (!read() || output.options[0].effect_indicators[2].kind !=
      game::EventEffectIndicatorKindV1::fulfillment ||
      output.options[0].effect_indicators[3].kind !=
      game::EventEffectIndicatorKindV1::stress_and_fulfillment ||
      output.options[0].effect_indicators[3].secondary_gain ||
      !output.options[0].effect_indicators[3].affected_by_trait ||
      !output.options[0].effect_indicators[3].critical) return false;
  auto wire = ck3_12002::SerializeEventWindowContextV1(output);
  if (wire.find("stress_and_fulfillment") == std::string::npos ||
      wire.find("\"secondary_direction\":\"decrease\"") == std::string::npos ||
      wire.find("module+0x5C6A520->+0x10") == std::string::npos ||
      wire.find("0x44BC408") == std::string::npos ||
      wire.find("1.19.0.6") != std::string::npos) return false;
  std::cout << wire << '\n';
  // A stale old-layout cancel byte must have no influence on the new reader.
  Store<std::uint8_t>(fixture.authored_options[3].data(), 0x47A, 1);
  Store<std::uint8_t>(fixture.authored_options[3].data(), 0x412, 0);
  if (!read() || output.options[0].cancel) return false;
  // The event belongs to the materialized Gfx idler, not the similarly named
  // non-Gfx engine idler whose table is a different dynamic type.
  Store<std::uintptr_t>(fixture.idler.data(), 0, 0x1844D6048);
  if (read() || output.unavailable_reason != "ingame_idler_unavailable") return false;
  Store<std::uintptr_t>(fixture.idler.data(), 0, fixture.bindings.ingame_interface_idler_vtable);
  fixture.windows[1] = fixture.window.data();
  Store<std::int32_t>(fixture.manager.data(), 0x24, 2);
  if (read() || output.unavailable_reason != "event_window_ambiguous") return false;
  Store<std::int32_t>(fixture.manager.data(), 0x24, 1);
  Store<std::int32_t>(fixture.character.data(), 0x18, kCharacterId | 0x01000000);
  if (read() || output.unavailable_reason != "event_root_scope_invalid") return false;
  Store<std::int32_t>(fixture.character.data(), 0x18, kCharacterId);
  fixture.bindings.events.core.enabled = false;
  if (read() || output.unavailable_reason != "unsupported_build") return false;
  const auto binding = ck3_12002::BindEventWindowImage(0x180000000,
    ck3_12002::kExecutableSha256);
  const auto mismatched = ck3_12002::BindEventWindowImage(0x180000000, "old");
  const auto patch3 = ck3_12002::BindEventWindowImage(0x180000000,
    ck3_12003::kExecutableSha256);
  if (!binding.events.core.enabled || mismatched.events.core.enabled ||
      binding.splash_window_primary_vtable != 0 ||
      binding.allow_null_saved_character_scope ||
      mismatched.splash_window_primary_vtable != 0 ||
      mismatched.allow_null_saved_character_scope ||
      !patch3.events.core.enabled || patch3.splash_window_primary_vtable != 0x184596D38 ||
      !patch3.allow_null_saved_character_scope ||
      binding.ingame_interface_idler_vtable != 0x1844BC408 ||
      reinterpret_cast<std::uintptr_t>(binding.trait_database_slot) != 0x185C67528)
    return false;
  std::uint64_t revision = 0; std::int32_t id = 0;
  return ck3_12002::ParseEventWindowContextRequestV1(
      "{\"expected_revision\":17,\"event_instance_id\":42}", revision, id) &&
      revision == 17 && id == 42;
}

bool TestSplash() {
  using namespace xar;
  Fixture fixture;
  fixture.UseSplash();
  game::EventWindowContextV1 output{};
  auto read = [&]() {
    g_current_event_calls = 0;
    return ck3_12002::ReadEventWindowContextV1(fixture.bindings, kRevision, kEventId, output) ==
           game::ReadEventWindowContextResultV1::available;
  };
  // A materialized SplashWindow uses the same genuine rendered option data.
  // Authored count is four; only native option index three is initially shown,
  // and its enabled byte is false. No synthetic active-event slot is used.
  if (!read() || output.window_match_count != 1 || output.options.size() != 1 ||
      !output.options[0].shown || output.options[0].enabled ||
      output.options[0].native_option_index != 3 ||
      output.event_definition_key != "xar_test.0001" || output.saved_scopes.size() != 2 ||
      output.root_scope->typed_identity.character_id != kCharacterId ||
      !output.option_presentation_ready || output.effect_preview_ready) return false;
  Store<std::int32_t>(fixture.window.data() + 0xB8, 0x1C, 2);
  fixture.InitializeOption(1, 1, true, false);
  if (!read() || output.options.size() != 2 || output.options[0].enabled ||
      !output.options[1].enabled || output.options[1].native_option_index != 1) return false;
  Store<std::int32_t>(fixture.window.data() + 0xB8, 0x1C, 1);
  Store<void *>(fixture.splash_window.data(), 0xD0, nullptr);
  if (read() || output.unavailable_reason != "event_window_not_materialized") return false;
  Store<void *>(fixture.splash_window.data(), 0xD0, fixture.splash_item.data());
  Store<void *>(fixture.splash_window.data(), 0xD8, fixture.splash_item.data());
  if (read() || output.unavailable_reason != "event_splash_transition_in_progress" ||
      !output.options.empty() || output.option_presentation_ready) return false;
  Store<void *>(fixture.splash_window.data(), 0xD8, nullptr);
  Store<std::uintptr_t>(fixture.splash_window.data(), 0, 0x184597910);
  if (read() || output.unavailable_reason != "event_splash_layout_invalid") return false;
  Store<std::uintptr_t>(fixture.splash_window.data(), 0, fixture.bindings.splash_window_primary_vtable);
  Store<std::int32_t>(fixture.splash_window.data(), 0xC4, 33);
  if (read() || output.unavailable_reason != "event_splash_layout_invalid") return false;
  Store<std::int32_t>(fixture.splash_window.data(), 0xC4, 1);
  Store<std::int32_t>(fixture.splash_window.data(), 0xC0, 0);
  if (read() || output.unavailable_reason != "event_splash_layout_invalid") return false;
  Store<std::int32_t>(fixture.splash_window.data(), 0xC0, 2);
  fixture.splash_items[0] = nullptr;
  if (read() || output.unavailable_reason != "event_splash_layout_invalid") return false;
  fixture.splash_items[0] = fixture.splash_item.data();
  fixture.splash_items[1] = fixture.splash_item.data();
  Store<std::int32_t>(fixture.splash_window.data(), 0xC4, 2);
  if (read() || output.unavailable_reason != "event_splash_layout_invalid") return false;
  Store<std::int32_t>(fixture.splash_window.data(), 0xC4, 1);
  Store<void *>(fixture.splash_item.data(), 0, fixture.manager.data());
  if (read() || output.unavailable_reason != "event_splash_layout_invalid") return false;
  Store<void *>(fixture.splash_item.data(), 0, fixture.splash_window.data());
  Store<void *>(fixture.splash_item.data(), 0x10, nullptr);
  if (read() || output.unavailable_reason != "event_splash_layout_invalid") return false;
  Store<void *>(fixture.splash_item.data(), 0x10, fixture.window.data() + 0xB8);
  Store<std::int32_t>(fixture.active_event.data(), 0x1BC, kEventId + 1);
  if (read() || output.unavailable_reason != "state_changed") return false;
  Store<std::int32_t>(fixture.active_event.data(), 0x1BC, kEventId);
  Store<std::int32_t>(fixture.window.data() + 0xB8, 0, kEventId + 1);
  if (read() || output.unavailable_reason != "event_splash_layout_invalid") return false;
  Store<std::int32_t>(fixture.window.data() + 0xB8, 0, kEventId);
  Store<std::int32_t>(fixture.window.data() + 0xB8, 0x1C, 65);
  if (read() || output.unavailable_reason != "event_splash_layout_invalid") return false;
  Store<std::int32_t>(fixture.window.data() + 0xB8, 0x1C, 1);
  Store<std::int32_t>(fixture.manager.data(), 0x24, 1);
  if (read() || output.unavailable_reason != "event_window_ambiguous") return false;
  Store<std::int32_t>(fixture.manager.data(), 0x24, 0);
  g_event_identity_drift = EventIdentityDrift::splash_current_item;
  if (read() || output.unavailable_reason != "event_splash_changed") return false;
  g_event_identity_drift = EventIdentityDrift::none;
  Store<void *>(fixture.splash_window.data(), 0xD0, fixture.splash_item.data());
  g_event_identity_drift = EventIdentityDrift::splash_transition_item;
  if (read() || output.unavailable_reason != "event_splash_changed") return false;
  g_event_identity_drift = EventIdentityDrift::none;
  Store<void *>(fixture.splash_window.data(), 0xD8, nullptr);
  Store<std::int32_t>(fixture.character.data(), 0x18, kCharacterId | 0x01000000);
  if (read() || output.unavailable_reason != "event_root_scope_invalid") return false;
  Store<std::int32_t>(fixture.character.data(), 0x18, kCharacterId);
  Store<std::int32_t>(fixture.game_state.data(), 0x70, 1);
  Store<std::uint8_t>(fixture.jomini.data(), 0x20, 0);
  if (read() || output.unavailable_reason != "state_changed") return false;
  return true;
}

bool TestNullSavedCharacterScope() {
  using namespace xar;
  // Exercise the same genuine option and scope reader in ordinary and splash
  // presentations. The null scope is a typed absence, never a live character.
  for (const bool splash : {false, true}) {
    Fixture fixture;
    fixture.bindings.allow_null_saved_character_scope = true;
    if (splash) fixture.UseSplash();
    constexpr std::uint64_t null_payload = 0xFFFFFFFFULL;
    Store<std::uint64_t>(fixture.saved_scope_rows.data(), 0x10, null_payload);
    game::EventWindowContextV1 output{};
    auto read = [&]() {
      g_current_event_calls = 0;
      return ck3_12002::ReadEventWindowContextV1(
          fixture.bindings, kRevision, kEventId, output) ==
          game::ReadEventWindowContextResultV1::available;
    };
    if (!read() || output.saved_scopes.size() != 2 ||
        output.saved_scopes[0].name != "xar_scope_root_control" ||
        output.saved_scopes[0].scope.raw_type_index != 4 ||
        output.saved_scopes[0].scope.type_key != "character" ||
        output.saved_scopes[0].scope.subtype != 2 ||
        output.saved_scopes[0].scope.typed_identity.available ||
        output.saved_scopes[0].scope.typed_identity.character_id.has_value() ||
        output.saved_scopes[0].scope.typed_identity.unavailable_reason != "character_scope_is_null" ||
        output.saved_scopes[1].scope.type_key != "province" ||
        output.root_scope->typed_identity.character_id != kCharacterId ||
        output.options.size() != 1 || !output.options[0].shown ||
        output.options[0].enabled || output.options[0].native_option_index != 3 ||
        output.effect_preview_ready || output.semantic_decision_ready) return false;
    if (!ck3_12002::SerializeEventWindowContextV1(output).empty()) return false;
    const auto wire = ck3_12002::SerializeEventWindowContextV1(output, true);
    if (wire.find("character_scope_is_null") == std::string::npos ||
        wire.find("\"typed_identity\":{\"status\":\"unavailable\",\"reason\":\"character_scope_is_null\"}") == std::string::npos) return false;
    std::cout << game::RenderCrozierBuildIdentity(
                     wire, game::Ck3_12003AdapterDescriptor()) << '\n';
    auto invalid_wire = output;
    invalid_wire.root_scope->typed_identity = output.saved_scopes[0].scope.typed_identity;
    if (!ck3_12002::SerializeEventWindowContextV1(invalid_wire, true).empty()) return false;
    invalid_wire = output;
    invalid_wire.saved_scopes[0].scope.typed_identity.character_id = kCharacterId;
    if (!ck3_12002::SerializeEventWindowContextV1(invalid_wire, true).empty()) return false;
    // Enabling a genuine option remains independent of null-scope admission.
    fixture.InitializeOption(0, 3, true, true);
    if (!read() || !output.options[0].enabled || !output.options[0].shown) return false;
    fixture.bindings.allow_null_saved_character_scope = false;
    if (read() || output.unavailable_reason != "event_saved_scope_invalid") return false;
    fixture.bindings.allow_null_saved_character_scope = true;
    Store<std::uint64_t>(fixture.active_event.data(), 0x08, null_payload);
    if (read() || output.unavailable_reason != "event_root_scope_invalid") return false;
    Store<std::uint64_t>(fixture.active_event.data(), 0x08, kCharacterId);
    for (const std::uint64_t invalid : {0ULL, 43ULL, 0x0100002AULL,
                                      0x1FFFFFFFFULL, 0xFFFFFFFFFFFFFFFFULL}) {
      Store<std::uint64_t>(fixture.saved_scope_rows.data(), 0x10, invalid);
      if (read() || output.unavailable_reason != "event_saved_scope_invalid" ||
          !output.options.empty()) return false;
    }
    Store<std::uint64_t>(fixture.saved_scope_rows.data(), 0x10, null_payload);
    for (const std::uint16_t invalid_type : {std::uint16_t{0}, std::uint16_t{5}}) {
      Store<std::uint16_t>(fixture.saved_scope_rows.data(), 0x08, invalid_type);
      if (read() || output.unavailable_reason != "event_saved_scope_invalid") return false;
    }
    Store<std::uint16_t>(fixture.saved_scope_rows.data(), 0x08, 3);
    g_generic_value_type_names[103] =
        reinterpret_cast<const std::string *>(fixture.generic_character_name.data());
    if (read() || output.unavailable_reason != "event_saved_scope_invalid") return false;
    g_generic_value_type_names[103] =
        reinterpret_cast<const std::string *>(fixture.generic_province_name.data());
    Store<std::uint16_t>(fixture.saved_scope_rows.data(), 0x08, 4);
    g_event_identity_drift = EventIdentityDrift::saved_scope_payload;
    if (read() || output.unavailable_reason != "event_scope_changed") return false;
    g_event_identity_drift = EventIdentityDrift::none;
  }
  return true;
}
} // namespace
int main() {
  if (!TestMigration() || !TestSplash() || !TestNullSavedCharacterScope()) { std::cerr << "CK3 1.20.0.2/.3 event-window fixture failed\n"; return 1; }
  std::cout << "CK3 1.20.0.2 event-window offline fixture passed\n";
  return 0;
}
