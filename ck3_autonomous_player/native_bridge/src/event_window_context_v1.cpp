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
constexpr std::size_t kMaximumStringBytes = 16'384;

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
        bindings.lookup_scheme_type == nullptr) {
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
    candidate.event_definition_identity_ready = true;
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
