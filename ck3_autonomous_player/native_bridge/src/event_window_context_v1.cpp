#include "xar_bridge/event_window_context_v1.hpp"

#include "xar_bridge/ck3_11906.hpp"

#include <algorithm>
#include <charconv>
#include <cstddef>
#include <cstring>
#include <limits>
#include <string_view>
#include <utility>

namespace xar::ck3_11906 {
namespace {

constexpr std::size_t kIdlerFromOwnerOffset = 0x10;
constexpr std::size_t kGameStateGameDataOffset = 0xA0;
constexpr std::size_t kActiveEventDataOffset = 0x1B0;
constexpr std::size_t kActiveEventInstanceIdOffset = 0x1BC;
constexpr std::size_t kEventDataCalculatedIdOffset = 0x08;
constexpr std::size_t kEventDataRuntimeStatsOrdinalOffset = 0x0C;
constexpr std::size_t kEventDataDefinitionKeyOffset = 0x10;
constexpr std::size_t kEventDataAuthoredOptionDataOffset = 0x1B0;
constexpr std::size_t kEventDataAuthoredOptionCapacityOffset = 0x1B8;
constexpr std::size_t kEventDataAuthoredOptionCountOffset = 0x1BC;
constexpr std::size_t kEventScopeRootOffset = 0x00;
constexpr std::size_t kEventScopeNamedDataOffset = 0x18;
constexpr std::size_t kEventScopeNamedCapacityOffset = 0x20;
constexpr std::size_t kEventScopeNamedCountOffset = 0x24;
constexpr std::size_t kEventScopeTokenTypeIndexOffset = 0x00;
constexpr std::size_t kEventScopeTokenSubtypeOffset = 0x02;
constexpr std::size_t kEventScopeTokenPayloadOffset = 0x08;
constexpr std::size_t kEventScopeNamedRowStride = 0x18;
constexpr std::size_t kEventScopeNamedRowIdentifierOffset = 0x00;
constexpr std::size_t kEventScopeNamedRowTokenOffset = 0x08;
constexpr std::size_t kGenericValueTypeRegistryDataOffset = 0x00;
constexpr std::size_t kGenericValueTypeRegistryCountOffset = 0x0C;
constexpr std::size_t kGenericValueTypeRegistryEntryStride = 0x50;
constexpr std::size_t kGenericValueTypeRegistryEntryIdentifierOffset = 0x00;
constexpr std::size_t kComponentStorageSlotsOffset = 0x20;
constexpr std::size_t kComponentStorageCapacityOffset = 0x2C;
constexpr std::size_t kComponentStorageSlotStride = 0x10;
constexpr std::size_t kComponentStorageSlotObjectOffset = 0x08;
constexpr std::size_t kCharacterIdOffset = 0x18;
constexpr std::size_t kEventOptionDefinitionIsCancelOffset = 0x47A;
constexpr std::size_t kManagerFromIdlerOffset = 0x28;
constexpr std::size_t kManagerWindowDataOffset = 0x10;
constexpr std::size_t kManagerWindowCountOffset = 0x1C;
constexpr std::size_t kWindowDataOffset = 0xE8;
constexpr std::size_t kDataInstanceIdOffset = 0x00;
constexpr std::size_t kDataOptionDataOffset = 0x10;
constexpr std::size_t kDataOptionCapacityOffset = 0x18;
constexpr std::size_t kDataOptionCountOffset = 0x1C;
constexpr std::size_t kOptionStride = 0x1B8;
constexpr std::size_t kOptionEffectDataOffset = 0x88;
constexpr std::size_t kOptionEffectCapacityOffset = 0x90;
constexpr std::size_t kOptionEffectCountOffset = 0x94;
constexpr std::size_t kOptionOwnerOffset = 0x160;
constexpr std::size_t kOptionNameOffset = 0x170;
constexpr std::size_t kOptionReasonOffset = 0x190;
constexpr std::size_t kOptionNativeIndexOffset = 0x1B0;
constexpr std::size_t kOptionEnabledOffset = 0x1B4;
constexpr std::size_t kOptionFallbackOffset = 0x1B5;
constexpr std::size_t kEffectIndicatorStride = 0x18;
constexpr std::size_t kEffectIndicatorPayload0Offset = 0x00;
constexpr std::size_t kEffectIndicatorPayload1Offset = 0x08;
constexpr std::size_t kEffectIndicatorKindOffset = 0x10;
constexpr std::size_t kEffectIndicatorGainOffset = 0x14;
constexpr std::size_t kEffectIndicatorAffectedByTraitOffset = 0x15;
constexpr std::size_t kEffectIndicatorCriticalOffset = 0x16;
constexpr std::size_t kTraitDatabaseDataOffset = 0x68;
constexpr std::size_t kTraitDatabaseCountOffset = 0x74;
constexpr std::size_t kTraitNativeIdOffset = 0x10;
constexpr std::size_t kTraitStableKeyOffset = 0x18;
constexpr std::size_t kSchemeTypeStableKeyOffset = 0x18;
constexpr std::size_t kMaximumWindows = 32;
constexpr std::size_t kMaximumOptions = 64;
constexpr std::size_t kMaximumEffectIndicators = 128;
constexpr std::size_t kMaximumTraitDefinitions = 4'096;
constexpr std::size_t kMaximumSavedScopes = 1'024;
constexpr std::int32_t kMaximumGenericValueTypes = 65'536;
constexpr std::int32_t kMaximumComponentSlots = 4'194'304;
constexpr std::size_t kMaximumStringBytes = 16'384;
constexpr std::uint16_t kCharacterScopeTypeIndex = 4;
constexpr std::string_view kCharacterScopeTypeKey = "character";
constexpr std::string_view kGenericScopeIdentityUnavailableReason =
    "generic_scope_payload_identity_not_closed";
constexpr std::string_view kCharacterScopeIdentityUnavailableReason =
    "character_scope_identity_unavailable";

template <typename T>
T LoadAt(const void *base, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset,
              sizeof(value));
  return value;
}

void SetUnavailable(game::EventWindowContextV1 &output,
                    std::string_view reason) {
  const auto revision = output.snapshot_revision;
  const auto date_raw = output.date_raw;
  const auto event_id = output.current_event_instance_id;
  const auto matches = output.window_match_count;
  output = {};
  output.snapshot_revision = revision;
  output.date_raw = date_raw;
  output.current_event_instance_id = event_id;
  output.window_match_count = matches;
  output.unavailable_reason.assign(reason);
}

bool ReadNativeString(const void *object, std::string &output,
                      bool require_nonempty = false,
                      bool require_bounded_capacity = false) {
  output.clear();
  if (object == nullptr) {
    return false;
  }
  const auto size = LoadAt<std::uint64_t>(object, 0x10);
  const auto capacity = LoadAt<std::uint64_t>(object, 0x18);
  if (size > kMaximumStringBytes || capacity < size ||
      (require_bounded_capacity && capacity > kMaximumStringBytes) ||
      (require_nonempty && size == 0)) {
    return false;
  }
  const void *data = object;
  if (capacity >= 16) {
    data = LoadAt<const void *>(object, 0x00);
  }
  if (size != 0 && data == nullptr) {
    return false;
  }
  try {
    output.assign(static_cast<const char *>(data),
                  static_cast<std::size_t>(size));
  } catch (...) {
    output.clear();
    return false;
  }
  return true;
}

struct EventDefinitionIdentityObservationV1 {
  void *active_event = nullptr;
  void *event_data = nullptr;
  std::int32_t event_instance_id = -1;
  std::int32_t calculated_event_id = 0;
  std::int32_t runtime_stats_ordinal = 0;
  std::string event_definition_key;

  friend bool operator==(const EventDefinitionIdentityObservationV1 &,
                         const EventDefinitionIdentityObservationV1 &) =
      default;
};

bool ReadEventDefinitionIdentity(
    const Bindings &bindings, std::int32_t expected_event_instance_id,
    EventDefinitionIdentityObservationV1 &output) {
  output = {};
  if (bindings.game_state_slot == nullptr ||
      bindings.get_current_event == nullptr ||
      bindings.event_manager_offset == 0) {
    return false;
  }
  void *const game_state = *bindings.game_state_slot;
  void *const game_data =
      game_state != nullptr
          ? LoadAt<void *>(game_state, kGameStateGameDataOffset)
          : nullptr;
  if (game_data == nullptr) {
    return false;
  }
  void *const event_manager = static_cast<std::byte *>(game_data) +
                              bindings.event_manager_offset;
  output.active_event = bindings.get_current_event(event_manager);
  if (output.active_event == nullptr) {
    return false;
  }
  output.event_data =
      LoadAt<void *>(output.active_event, kActiveEventDataOffset);
  output.event_instance_id = LoadAt<std::int32_t>(
      output.active_event, kActiveEventInstanceIdOffset);
  if (output.event_data == nullptr ||
      output.event_instance_id != expected_event_instance_id) {
    return false;
  }
  output.calculated_event_id = LoadAt<std::int32_t>(
      output.event_data, kEventDataCalculatedIdOffset);
  output.runtime_stats_ordinal = LoadAt<std::int32_t>(
      output.event_data, kEventDataRuntimeStatsOrdinalOffset);
  return ReadNativeString(
      static_cast<std::byte *>(output.event_data) +
          kEventDataDefinitionKeyOffset,
      output.event_definition_key, true, true);
}

bool ValidVector(std::int32_t count, std::int32_t capacity,
                 std::size_t maximum, const void *data) noexcept {
  return count >= 0 && capacity >= count &&
         capacity <= static_cast<std::int32_t>(maximum) &&
         (count == 0 || data != nullptr);
}

struct NativeStringView32 {
  const char *data = nullptr;
  std::int32_t size = 0;
  std::int32_t padding = 0;
};

struct EventScopeInventoryV1 {
  game::EventScopeV1 root_scope;
  std::vector<game::EventSavedScopeV1> saved_scopes;

  friend bool operator==(const EventScopeInventoryV1 &,
                         const EventScopeInventoryV1 &) = default;
};

bool ReadGenericValueTypeKey(const Bindings &bindings,
                             void *registry,
                             std::uint16_t type_index,
                             std::string &type_key) {
  type_key.clear();
  if (registry == nullptr ||
      registry != bindings.expected_generic_value_type_registry ||
      bindings.resolve_generic_value_type_name == nullptr ||
      type_index == 0) {
    return false;
  }
  void *const entries =
      LoadAt<void *>(registry, kGenericValueTypeRegistryDataOffset);
  const auto count = LoadAt<std::int32_t>(
      registry, kGenericValueTypeRegistryCountOffset);
  if (entries == nullptr || count <= 0 || count > kMaximumGenericValueTypes ||
      type_index >= static_cast<std::uint32_t>(count)) {
    return false;
  }
  const auto entry_offset =
      static_cast<std::size_t>(type_index) *
      kGenericValueTypeRegistryEntryStride;
  const auto identifier = LoadAt<std::int32_t>(
      entries, entry_offset + kGenericValueTypeRegistryEntryIdentifierOffset);
  const std::string *const native_name =
      bindings.resolve_generic_value_type_name(identifier);
  return native_name != nullptr &&
         native_name != bindings.generic_value_type_name_fallback &&
         ReadNativeString(native_name, type_key, true, true);
}

bool ResolveCharacterScopeIdentity(const Bindings &bindings,
                                   const void *token,
                                   std::int32_t &character_id) noexcept {
  character_id = -1;
  if (bindings.character_storage_slot == nullptr || token == nullptr) {
    return false;
  }
  const auto raw_payload = LoadAt<std::uint64_t>(
      token, kEventScopeTokenPayloadOffset);
  const auto raw_character_id = static_cast<std::uint32_t>(raw_payload);
  character_id = static_cast<std::int32_t>(raw_character_id);
  if (raw_payload != static_cast<std::uint64_t>(raw_character_id) ||
      character_id <= 0) {
    return false;
  }
  void *const storage = *bindings.character_storage_slot;
  if (storage == nullptr) {
    return false;
  }
  void *const slots =
      LoadAt<void *>(storage, kComponentStorageSlotsOffset);
  const auto capacity = LoadAt<std::int32_t>(
      storage, kComponentStorageCapacityOffset);
  const auto index = raw_character_id & 0x00FFFFFFU;
  if (slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentSlots ||
      index >= static_cast<std::uint32_t>(capacity)) {
    return false;
  }
  const auto slot_offset =
      static_cast<std::size_t>(index) * kComponentStorageSlotStride +
      kComponentStorageSlotObjectOffset;
  void *const character = LoadAt<void *>(slots, slot_offset);
  return character != nullptr &&
         LoadAt<std::int32_t>(character, kCharacterIdOffset) == character_id;
}

bool ReadEventScopeToken(const Bindings &bindings, void *registry,
                         const void *token, game::EventScopeV1 &output,
                         bool allow_unresolved_character_identity = false) {
  output = {};
  if (token == nullptr) {
    return false;
  }
  output.raw_type_index = LoadAt<std::uint16_t>(
      token, kEventScopeTokenTypeIndexOffset);
  output.subtype =
      LoadAt<std::uint16_t>(token, kEventScopeTokenSubtypeOffset);
  if (!ReadGenericValueTypeKey(bindings, registry, output.raw_type_index,
                               output.type_key)) {
    return false;
  }
  if (output.raw_type_index == kCharacterScopeTypeIndex) {
    if (output.type_key != kCharacterScopeTypeKey) {
      return false;
    }
    std::int32_t character_id = -1;
    if (!ResolveCharacterScopeIdentity(bindings, token, character_id)) {
      if (!allow_unresolved_character_identity) {
        return false;
      }
      output.typed_identity.available = false;
      output.typed_identity.character_id.reset();
      output.typed_identity.unavailable_reason.assign(
          kCharacterScopeIdentityUnavailableReason);
      return true;
    }
    output.typed_identity.available = true;
    output.typed_identity.character_id = character_id;
    output.typed_identity.unavailable_reason.clear();
    return true;
  }
  if (output.type_key == kCharacterScopeTypeKey) {
    return false;
  }
  output.typed_identity.available = false;
  output.typed_identity.character_id.reset();
  output.typed_identity.unavailable_reason.assign(
      kGenericScopeIdentityUnavailableReason);
  return true;
}

bool ReadSavedScopeName(const Bindings &bindings, void *table,
                        std::int32_t identifier, std::string &output) {
  output.clear();
  if (table == nullptr ||
      bindings.resolve_script_identifier_name == nullptr ||
      bindings.lookup_script_identifier_id == nullptr) {
    return false;
  }
  const std::string *const native_name =
      bindings.resolve_script_identifier_name(table, identifier);
  if (native_name == nullptr ||
      native_name == bindings.script_identifier_name_fallback ||
      !ReadNativeString(native_name, output, true, true) ||
      output.size() >
          static_cast<std::size_t>(std::numeric_limits<std::int32_t>::max())) {
    output.clear();
    return false;
  }
  const NativeStringView32 view{
      output.data(), static_cast<std::int32_t>(output.size()), 0};
  std::int32_t roundtrip_identifier = -1;
  if (bindings.lookup_script_identifier_id(
          table, &roundtrip_identifier, &view) == nullptr ||
      roundtrip_identifier != identifier) {
    output.clear();
    return false;
  }
  return true;
}

bool ReadEventScopeInventory(const Bindings &bindings,
                             const void *active_event,
                             EventScopeInventoryV1 &output,
                             std::string_view &failure_reason) {
  output = {};
  failure_reason = "event_scope_layout_invalid";
  if (active_event == nullptr ||
      bindings.get_generic_value_type_registry == nullptr ||
      bindings.expected_generic_value_type_registry == nullptr ||
      bindings.generic_value_type_name_fallback == nullptr ||
      bindings.resolve_generic_value_type_name == nullptr ||
      bindings.get_script_identifier_table == nullptr ||
      bindings.lookup_script_identifier_id == nullptr ||
      bindings.resolve_script_identifier_name == nullptr ||
      bindings.script_identifier_name_fallback == nullptr ||
      bindings.character_storage_slot == nullptr) {
    failure_reason = "unsupported_build";
    return false;
  }
  void *const registry = bindings.get_generic_value_type_registry();
  if (registry == nullptr ||
      registry != bindings.expected_generic_value_type_registry) {
    failure_reason = "event_scope_type_registry_invalid";
    return false;
  }
  if (!ReadEventScopeToken(
          bindings, registry,
          static_cast<const std::byte *>(active_event) +
              kEventScopeRootOffset,
          output.root_scope)) {
    failure_reason = "event_root_scope_invalid";
    return false;
  }
  void *const rows =
      LoadAt<void *>(active_event, kEventScopeNamedDataOffset);
  const auto capacity = LoadAt<std::int32_t>(
      active_event, kEventScopeNamedCapacityOffset);
  const auto count =
      LoadAt<std::int32_t>(active_event, kEventScopeNamedCountOffset);
  if (!ValidVector(count, capacity, kMaximumSavedScopes, rows)) {
    failure_reason = "event_saved_scope_vector_invalid";
    return false;
  }
  void *const identifier_table = bindings.get_script_identifier_table();
  if (identifier_table == nullptr) {
    failure_reason = "event_saved_scope_name_invalid";
    return false;
  }
  try {
    output.saved_scopes.reserve(static_cast<std::size_t>(count));
  } catch (...) {
    failure_reason = "event_saved_scope_vector_invalid";
    return false;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    const auto *const row =
        static_cast<const std::byte *>(rows) +
        static_cast<std::size_t>(index) * kEventScopeNamedRowStride;
    game::EventSavedScopeV1 saved{};
    saved.name_identifier = LoadAt<std::int32_t>(
        row, kEventScopeNamedRowIdentifierOffset);
    if (!ReadSavedScopeName(bindings, identifier_table,
                            saved.name_identifier, saved.name)) {
      failure_reason = "event_saved_scope_name_invalid";
      return false;
    }
    const bool duplicate_name = std::any_of(
        output.saved_scopes.begin(), output.saved_scopes.end(),
        [&saved](const game::EventSavedScopeV1 &existing) {
          return existing.name_identifier == saved.name_identifier ||
                 existing.name == saved.name;
        });
    if (duplicate_name) {
      failure_reason = "event_saved_scope_name_invalid";
      return false;
    }
    if (!ReadEventScopeToken(
            bindings, registry,
            row + kEventScopeNamedRowTokenOffset, saved.scope, true)) {
      failure_reason = "event_saved_scope_invalid";
      return false;
    }
    try {
      output.saved_scopes.push_back(std::move(saved));
    } catch (...) {
      failure_reason = "event_saved_scope_vector_invalid";
      return false;
    }
  }
  failure_reason = {};
  return true;
}

void ReadTraitIndicatorIdentity(const Bindings &bindings, const void *payload,
                                game::EventEffectIndicatorRowV1 &row) {
  row.identity_available = false;
  row.native_id.reset();
  row.stable_key.clear();
  if (payload == nullptr || bindings.trait_database_slot == nullptr) {
    return;
  }
  void *const database = *bindings.trait_database_slot;
  if (database == nullptr) {
    return;
  }
  void *const definitions = LoadAt<void *>(database, kTraitDatabaseDataOffset);
  const auto count = LoadAt<std::int32_t>(database, kTraitDatabaseCountOffset);
  if (count <= 0 ||
      count > static_cast<std::int32_t>(kMaximumTraitDefinitions) ||
      definitions == nullptr) {
    return;
  }
  std::int32_t pointer_matches = 0;
  for (std::int32_t index = 0; index < count; ++index) {
    void *const definition = LoadAt<void *>(
        definitions, static_cast<std::size_t>(index) * sizeof(void *));
    if (definition == payload) {
      ++pointer_matches;
    }
  }
  if (pointer_matches != 1) {
    return;
  }
  const auto native_id = LoadAt<std::int32_t>(payload, kTraitNativeIdOffset);
  std::string stable_key;
  if (native_id < 0 ||
      !ReadNativeString(static_cast<const std::byte *>(payload) +
                            kTraitStableKeyOffset,
                        stable_key, true, true)) {
    return;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    void *const definition = LoadAt<void *>(
        definitions, static_cast<std::size_t>(index) * sizeof(void *));
    if (definition == nullptr) {
      return;
    }
    if (definition == payload) {
      continue;
    }
    if (LoadAt<std::int32_t>(definition, kTraitNativeIdOffset) == native_id) {
      return;
    }
    std::string other_key;
    if (!ReadNativeString(static_cast<std::byte *>(definition) +
                              kTraitStableKeyOffset,
                          other_key, true, true) ||
        other_key == stable_key) {
      return;
    }
  }
  row.identity_available = true;
  row.native_id = native_id;
  row.stable_key = std::move(stable_key);
}

void ReadSchemeIndicatorIdentity(const Bindings &bindings, const void *payload,
                                 game::EventEffectIndicatorRowV1 &row) {
  row.identity_available = false;
  row.native_id.reset();
  row.stable_key.clear();
  if (payload == nullptr || bindings.scheme_type_database_slot == nullptr ||
      bindings.scheme_type_fallback_slot == nullptr ||
      bindings.scheme_type_primary_vtable == 0 ||
      bindings.hash_stable_key == nullptr ||
      bindings.lookup_scheme_type == nullptr) {
    return;
  }
  void *const database = *bindings.scheme_type_database_slot;
  void *const fallback = *bindings.scheme_type_fallback_slot;
  if (database == nullptr || fallback == nullptr || payload == fallback ||
      LoadAt<std::uintptr_t>(payload, 0) !=
          bindings.scheme_type_primary_vtable) {
    return;
  }
  std::string stable_key;
  if (!ReadNativeString(static_cast<const std::byte *>(payload) +
                            kSchemeTypeStableKeyOffset,
                        stable_key, true, true) ||
      stable_key.size() >
          static_cast<std::size_t>(std::numeric_limits<std::uint32_t>::max())) {
    return;
  }
  // Mirror the engine caller's ABI even though 1.19.0.6's hash body does not
  // currently consume its first argument.
  const auto hash = bindings.hash_stable_key(
      database, stable_key.data(),
      static_cast<std::uint32_t>(stable_key.size()));
  if (bindings.lookup_scheme_type(database, hash) != payload) {
    return;
  }
  row.identity_available = true;
  row.stable_key = std::move(stable_key);
}

bool ReadEffectIndicators(
    const Bindings &bindings, const void *item,
    std::vector<game::EventEffectIndicatorRowV1> &output) {
  output.clear();
  void *const rows = LoadAt<void *>(item, kOptionEffectDataOffset);
  const auto count = LoadAt<std::int32_t>(item, kOptionEffectCountOffset);
  const auto capacity = LoadAt<std::int32_t>(item, kOptionEffectCapacityOffset);
  if (!ValidVector(count, capacity, kMaximumEffectIndicators, rows)) {
    return false;
  }
  try {
    output.reserve(static_cast<std::size_t>(count));
  } catch (...) {
    return false;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    const auto *const source =
        static_cast<const std::byte *>(rows) +
        static_cast<std::size_t>(index) * kEffectIndicatorStride;
    game::EventEffectIndicatorRowV1 row{};
    row.raw_kind = LoadAt<std::int32_t>(source, kEffectIndicatorKindOffset);
    switch (row.raw_kind) {
    case 0:
      row.kind = game::EventEffectIndicatorKindV1::trait;
      row.gain = LoadAt<std::uint8_t>(source, kEffectIndicatorGainOffset) != 0;
      ReadTraitIndicatorIdentity(
          bindings, LoadAt<void *>(source, kEffectIndicatorPayload0Offset),
          row);
      break;
    case 1:
      row.kind = game::EventEffectIndicatorKindV1::stress;
      row.gain = LoadAt<std::uint8_t>(source, kEffectIndicatorGainOffset) != 0;
      row.affected_by_trait =
          LoadAt<std::uint8_t>(source, kEffectIndicatorAffectedByTraitOffset) !=
          0;
      row.critical =
          LoadAt<std::uint8_t>(source, kEffectIndicatorCriticalOffset) != 0;
      break;
    case 2:
      row.kind = game::EventEffectIndicatorKindV1::death;
      break;
    case 3:
      row.kind = game::EventEffectIndicatorKindV1::scheme;
      ReadSchemeIndicatorIdentity(
          bindings, LoadAt<void *>(source, kEffectIndicatorPayload1Offset),
          row);
      break;
    default:
      row.kind = game::EventEffectIndicatorKindV1::unknown;
      break;
    }
    try {
      output.push_back(std::move(row));
    } catch (...) {
      output.clear();
      return false;
    }
  }
  return true;
}

bool ReadMatchingWindow(const Bindings &bindings, const void *event_data,
                        void *window,
                        std::int32_t expected_event_id,
                        game::EventWindowContextV1 &candidate) {
  if (event_data == nullptr || window == nullptr ||
      LoadAt<std::uintptr_t>(window, 0) !=
          bindings.event_window_primary_vtable) {
    return false;
  }
  auto *const data = static_cast<std::byte *>(window) + kWindowDataOffset;
  if (LoadAt<std::int32_t>(data, kDataInstanceIdOffset) !=
      expected_event_id) {
    return true;
  }
  ++candidate.window_match_count;
  if (candidate.window_match_count != 1) {
    return true;
  }
  void *const items = LoadAt<void *>(data, kDataOptionDataOffset);
  const auto count = LoadAt<std::int32_t>(data, kDataOptionCountOffset);
  const auto capacity = LoadAt<std::int32_t>(
      data, kDataOptionCapacityOffset);
  if (!ValidVector(count, capacity, kMaximumOptions, items)) {
    return false;
  }
  void *const authored_options =
      LoadAt<void *>(event_data, kEventDataAuthoredOptionDataOffset);
  const auto authored_count =
      LoadAt<std::int32_t>(event_data, kEventDataAuthoredOptionCountOffset);
  const auto authored_capacity = LoadAt<std::int32_t>(
      event_data, kEventDataAuthoredOptionCapacityOffset);
  if (!ValidVector(authored_count, authored_capacity, kMaximumOptions,
                   authored_options)) {
    return false;
  }
  try {
    candidate.options.clear();
    candidate.options.reserve(static_cast<std::size_t>(count));
  } catch (...) {
    return false;
  }
  for (std::int32_t rendered = 0; rendered < count; ++rendered) {
    const auto offset = static_cast<std::size_t>(rendered) * kOptionStride;
    auto *const item = static_cast<std::byte *>(items) + offset;
    if (LoadAt<void *>(item, kOptionOwnerOffset) != data) {
      return false;
    }
    const auto enabled = LoadAt<std::uint8_t>(item, kOptionEnabledOffset);
    const auto fallback = LoadAt<std::uint8_t>(item, kOptionFallbackOffset);
    if (enabled > 1 || fallback > 1) {
      return false;
    }
    game::EventWindowOptionV1 option{};
    option.rendered_index = rendered;
    option.native_option_index =
        LoadAt<std::int32_t>(item, kOptionNativeIndexOffset);
    if (option.native_option_index < 0 ||
        option.native_option_index >= authored_count) {
      return false;
    }
    void *const authored_option = LoadAt<void *>(
        authored_options,
        static_cast<std::size_t>(option.native_option_index) * sizeof(void *));
    if (authored_option == nullptr) {
      return false;
    }
    const auto is_cancel = LoadAt<std::uint8_t>(
        authored_option, kEventOptionDefinitionIsCancelOffset);
    if (is_cancel > 1) {
      return false;
    }
    option.shown = true;
    option.enabled = enabled != 0;
    option.fallback = fallback != 0;
    option.cancel = is_cancel != 0;
    const bool duplicate_native_index = std::any_of(
        candidate.options.begin(), candidate.options.end(),
        [&option](const game::EventWindowOptionV1 &existing) {
          return existing.native_option_index == option.native_option_index;
        });
    if (duplicate_native_index ||
        !ReadNativeString(item + kOptionNameOffset,
                          option.resolved_name) ||
        !ReadNativeString(item + kOptionReasonOffset,
                          option.unavailable_reason) ||
        !ReadEffectIndicators(bindings, item, option.effect_indicators)) {
      return false;
    }
    try {
      candidate.options.push_back(std::move(option));
    } catch (...) {
      return false;
    }
  }
  return true;
}

template <typename T>
bool ParsePositiveField(std::string_view json, std::string_view key,
                        T &output) noexcept {
  const auto first = json.find(key);
  if (first == std::string_view::npos ||
      json.find(key, first + key.size()) != std::string_view::npos) {
    return false;
  }
  auto begin = first + key.size();
  while (begin < json.size() && (json[begin] == ' ' || json[begin] == '\t')) {
    ++begin;
  }
  if (begin >= json.size() || json[begin] < '1' || json[begin] > '9') {
    return false;
  }
  auto end = begin;
  while (end < json.size() && json[end] >= '0' && json[end] <= '9') {
    ++end;
  }
  T value{};
  const auto parsed = std::from_chars(json.data() + begin,
                                      json.data() + end, value);
  if (parsed.ec != std::errc{} || parsed.ptr != json.data() + end ||
      value <= 0) {
    return false;
  }
  output = value;
  return true;
}

} // namespace

game::ReadEventWindowContextResultV1 ReadEventWindowContextV1(
    const Bindings &bindings, std::uint64_t expected_snapshot_revision,
    std::int32_t expected_event_instance_id,
    game::EventWindowContextV1 &output) noexcept {
  output = {};
  output.snapshot_revision = expected_snapshot_revision;
  output.current_event_instance_id = expected_event_instance_id;
  try {
    if (!bindings.enabled || expected_snapshot_revision == 0 ||
        expected_event_instance_id <= 0 ||
        bindings.game_state_slot == nullptr ||
        bindings.jomini_state_slot == nullptr ||
        bindings.get_current_event == nullptr ||
        bindings.event_manager_offset == 0 ||
        bindings.ingame_interface_idler_vtable == 0 ||
        bindings.event_window_primary_vtable == 0 ||
        bindings.scheme_type_primary_vtable == 0 ||
        bindings.trait_database_slot == nullptr ||
        bindings.scheme_type_database_slot == nullptr ||
        bindings.scheme_type_fallback_slot == nullptr ||
        bindings.hash_stable_key == nullptr ||
        bindings.lookup_scheme_type == nullptr ||
        bindings.character_storage_slot == nullptr ||
        bindings.expected_generic_value_type_registry == nullptr ||
        bindings.generic_value_type_name_fallback == nullptr ||
        bindings.script_identifier_name_fallback == nullptr ||
        bindings.get_script_identifier_table == nullptr ||
        bindings.lookup_script_identifier_id == nullptr ||
        bindings.get_generic_value_type_registry == nullptr ||
        bindings.resolve_generic_value_type_name == nullptr ||
        bindings.resolve_script_identifier_name == nullptr) {
      SetUnavailable(output, "unsupported_build");
      return game::ReadEventWindowContextResultV1::unavailable;
    }
    game::Snapshot before{};
    if (!ReadSnapshot(bindings, before) || !before.paused ||
        !before.map_ready || !before.has_active_event ||
        before.active_event_instance_id != expected_event_instance_id) {
      SetUnavailable(output, "state_changed");
      return game::ReadEventWindowContextResultV1::unavailable;
    }
    output.date_raw = before.date_raw;
    EventDefinitionIdentityObservationV1 identity_before{};
    if (!ReadEventDefinitionIdentity(bindings, expected_event_instance_id,
                                     identity_before)) {
      SetUnavailable(output, "event_definition_identity_unavailable");
      return game::ReadEventWindowContextResultV1::unavailable;
    }
    EventScopeInventoryV1 scope_before{};
    std::string_view scope_failure_reason{};
    if (!ReadEventScopeInventory(bindings, identity_before.active_event,
                                 scope_before, scope_failure_reason)) {
      SetUnavailable(output, scope_failure_reason);
      return game::ReadEventWindowContextResultV1::unavailable;
    }
    void *const owner = *bindings.jomini_state_slot;
    void *const idler = owner != nullptr
                            ? LoadAt<void *>(owner, kIdlerFromOwnerOffset)
                            : nullptr;
    if (idler == nullptr ||
        LoadAt<std::uintptr_t>(idler, 0) !=
            bindings.ingame_interface_idler_vtable) {
      SetUnavailable(output, "ingame_idler_unavailable");
      return game::ReadEventWindowContextResultV1::unavailable;
    }
    void *const manager =
        LoadAt<void *>(idler, kManagerFromIdlerOffset);
    if (manager == nullptr) {
      SetUnavailable(output, "event_window_manager_unavailable");
      return game::ReadEventWindowContextResultV1::unavailable;
    }
    void *const windows =
        LoadAt<void *>(manager, kManagerWindowDataOffset);
    const auto count =
        LoadAt<std::int32_t>(manager, kManagerWindowCountOffset);
    if (count < 0 || count > static_cast<std::int32_t>(kMaximumWindows) ||
        (count != 0 && windows == nullptr)) {
      SetUnavailable(output, "event_window_vector_invalid");
      return game::ReadEventWindowContextResultV1::unavailable;
    }
    game::EventWindowContextV1 candidate = output;
    for (std::int32_t index = 0; index < count; ++index) {
      void *const window = LoadAt<void *>(
          windows, static_cast<std::size_t>(index) * sizeof(void *));
      if (!ReadMatchingWindow(bindings, identity_before.event_data, window,
                              expected_event_instance_id, candidate)) {
        SetUnavailable(output, "event_window_layout_invalid");
        return game::ReadEventWindowContextResultV1::unavailable;
      }
    }
    output.window_match_count = candidate.window_match_count;
    if (candidate.window_match_count != 1) {
      SetUnavailable(output, candidate.window_match_count == 0
                                 ? "event_window_not_materialized"
                                 : "event_window_ambiguous");
      return game::ReadEventWindowContextResultV1::unavailable;
    }
    EventDefinitionIdentityObservationV1 identity_after{};
    if (!ReadEventDefinitionIdentity(bindings, expected_event_instance_id,
                                     identity_after) ||
        identity_after != identity_before) {
      SetUnavailable(output, "event_definition_identity_changed");
      return game::ReadEventWindowContextResultV1::unavailable;
    }
    EventScopeInventoryV1 scope_after{};
    if (!ReadEventScopeInventory(bindings, identity_after.active_event,
                                 scope_after, scope_failure_reason)) {
      SetUnavailable(output, scope_failure_reason);
      return game::ReadEventWindowContextResultV1::unavailable;
    }
    if (scope_after != scope_before) {
      SetUnavailable(output, "event_scope_changed");
      return game::ReadEventWindowContextResultV1::unavailable;
    }
    game::Snapshot after{};
    if (!ReadSnapshot(bindings, after) || after != before) {
      SetUnavailable(output, "state_changed");
      return game::ReadEventWindowContextResultV1::unavailable;
    }
    candidate.status = game::EventWindowContextStatusV1::available;
    candidate.unavailable_reason.clear();
    candidate.event_definition_key =
        std::move(identity_before.event_definition_key);
    candidate.calculated_event_id = identity_before.calculated_event_id;
    candidate.runtime_stats_ordinal = identity_before.runtime_stats_ordinal;
    candidate.root_scope = std::move(scope_before.root_scope);
    candidate.saved_scopes = std::move(scope_before.saved_scopes);
    candidate.event_definition_identity_ready = true;
    candidate.root_scope_ready = true;
    candidate.saved_scopes_ready = true;
    candidate.option_presentation_ready = true;
    candidate.effect_indicators_ready = true;
    candidate.effect_preview_ready = false;
    candidate.semantic_decision_ready = false;
    output = std::move(candidate);
    return game::ReadEventWindowContextResultV1::available;
  } catch (...) {
    SetUnavailable(output, "internal_error");
    return game::ReadEventWindowContextResultV1::unavailable;
  }
}

bool ParseEventWindowContextRequestV1(
    std::string_view json, std::uint64_t &expected_revision,
    std::int32_t &event_instance_id) noexcept {
  expected_revision = 0;
  event_instance_id = -1;
  return ParsePositiveField(json, "\"expected_revision\":",
                            expected_revision) &&
         ParsePositiveField(json, "\"event_instance_id\":",
                            event_instance_id);
}

} // namespace xar::ck3_11906
