#include "xar_bridge/ck3_12003_family_terminal_events.hpp"

#include <algorithm>
#include <cstddef>
#include <cstring>
#include <limits>
#include <utility>

#if defined(_MSC_VER)
#include <windows.h>
#endif

namespace xar::ck3_12003 {
namespace {

constexpr std::size_t kGameDataOffset = 0xA0;
constexpr std::size_t kQueueDataOffset = 0x1F18;
constexpr std::size_t kQueueCapacityOffset = 0x1F20;
constexpr std::size_t kQueueCountOffset = 0x1F24;
constexpr std::size_t kQueueStride = 8;
constexpr std::size_t kEventDefinitionOffset = 0x1B0;
constexpr std::size_t kEventReceiverOffset = 0x1B8;
constexpr std::size_t kEventInstanceOffset = 0x1BC;
constexpr std::size_t kEventPrimaryOffset = 0x1C0;
constexpr std::size_t kScopeDataOffset = 0x18;
constexpr std::size_t kScopeCapacityOffset = 0x20;
constexpr std::size_t kScopeCountOffset = 0x24;
constexpr std::size_t kScopeRowStride = 0x18;
constexpr std::int32_t kMaximumQueueEntries = 1'000'000;
constexpr std::int32_t kMaximumSavedScopes = 1'024;
constexpr std::uint64_t kMaximumStringBytes = 16'384;
constexpr std::uint16_t kCharacterScopeTypeIndex = 4;

template <typename T>
T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

template <typename Callback>
bool ReadBoundary(Callback callback) noexcept {
#if defined(_MSC_VER)
  __try { return callback(); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  return callback();
#endif
}

bool Fail(FamilyTerminalEventsSnapshotV1 &output,
          FamilyTerminalEventFailureV1 failure) noexcept {
  output.available = false;
  output.failure = failure;
  return false;
}

bool ValidCharacterId(std::int32_t id) noexcept {
  return id != -1 && id != 0;
}

bool ReadNativeString(const void *object, std::string &output) {
  output.clear();
  if (object == nullptr) return false;
  const auto size = Load<std::uint64_t>(object, 0x10);
  const auto capacity = Load<std::uint64_t>(object, 0x18);
  if (size == 0 || size > kMaximumStringBytes || capacity < size ||
      capacity > kMaximumStringBytes) return false;
  const void *data = capacity >= 16 ? Load<const void *>(object, 0) : object;
  if (data == nullptr) return false;
  output.assign(static_cast<const char *>(data), static_cast<std::size_t>(size));
  return true;
}

struct NativeStringView32 {
  const char *data = nullptr;
  std::int32_t size = 0;
  std::int32_t padding = 0;
};

bool ReadScopeName(const ck3_12002::EventWindowBindings &bindings,
                   void *table, std::int32_t identifier, std::string &output) {
  const std::string *name =
      bindings.resolve_script_identifier_name(table, identifier);
  if (name == nullptr || name == bindings.script_identifier_name_fallback ||
      !ReadNativeString(name, output)) return false;
  const NativeStringView32 view{
      output.data(), static_cast<std::int32_t>(output.size()), 0};
  std::int32_t roundtrip = -1;
  return bindings.lookup_script_identifier_id(table, &roundtrip, &view) != nullptr &&
      roundtrip == identifier;
}

bool ReadScope(const ck3_12002::EventWindowBindings &bindings,
               const void *token, bool named_scope,
               FamilyTerminalEventScopeV1 &output) noexcept {
  output.raw_type_index = Load<std::uint16_t>(token, 0);
  output.subtype = Load<std::uint16_t>(token, 2);
  output.raw_payload = Load<std::uint64_t>(token, 8);
  if (output.raw_type_index != kCharacterScopeTypeIndex) return true;
  if (named_scope && bindings.allow_null_saved_character_scope &&
      output.raw_payload == std::numeric_limits<std::uint32_t>::max()) {
    output.character_scope_is_null = true;
    return true;
  }
  const auto raw_id = static_cast<std::uint32_t>(output.raw_payload);
  std::int32_t id = -1;
  std::memcpy(&id, &raw_id, sizeof(id));
  if (output.raw_payload != static_cast<std::uint64_t>(raw_id) ||
      !ValidCharacterId(id)) return false;
  const void *character = ck3_12002::ResolveCoreCharacter(bindings.events.core, id);
  if (character == nullptr || Load<std::int32_t>(character, 0x18) != id) return false;
  output.character_id = id;
  output.character_identity_verified = true;
  return true;
}

bool ScopeIs(const FamilyTerminalEventScopeV1 &scope, std::int32_t id) noexcept {
  return scope.character_identity_verified && scope.character_id == id;
}

bool NamedScopeIs(const FamilyTerminalEventRecordV1 &record,
                  std::string_view name, std::int32_t id) noexcept {
  const auto found = std::find_if(record.saved_scopes.begin(), record.saved_scopes.end(),
      [name](const FamilyTerminalEventSavedScopeV1 &row) { return row.name == name; });
  return found != record.saved_scopes.end() && ScopeIs(found->scope, id);
}

bool ReadLetterScopes(const ck3_12002::EventWindowBindings &bindings,
                      void *table, const void *event,
                      const FamilyTerminalEventsRequestV1 &request,
                      FamilyTerminalEventRecordV1 &record,
                      FamilyTerminalEventsSnapshotV1 &output) {
  if (!ReadScope(bindings, event, false, record.root_scope))
    return Fail(output, FamilyTerminalEventFailureV1::character_scope_identity_invalid);
  const void *rows = Load<const void *>(event, kScopeDataOffset);
  const auto capacity = Load<std::int32_t>(event, kScopeCapacityOffset);
  const auto count = Load<std::int32_t>(event, kScopeCountOffset);
  if (count < 0 || capacity < count || capacity > kMaximumSavedScopes ||
      (count != 0 && rows == nullptr))
    return Fail(output, FamilyTerminalEventFailureV1::saved_scope_vector_invalid);
  record.saved_scopes.reserve(static_cast<std::size_t>(count));
  for (std::int32_t index = 0; index < count; ++index) {
    const auto *row = static_cast<const std::byte *>(rows) +
        static_cast<std::size_t>(index) * kScopeRowStride;
    FamilyTerminalEventSavedScopeV1 saved{};
    saved.name_identifier = Load<std::int32_t>(row, 0);
    if (!ReadScopeName(bindings, table, saved.name_identifier, saved.name))
      return Fail(output, FamilyTerminalEventFailureV1::saved_scope_name_invalid);
    if (std::any_of(record.saved_scopes.begin(), record.saved_scopes.end(),
        [&saved](const FamilyTerminalEventSavedScopeV1 &prior) {
          return prior.name == saved.name;
        })) return Fail(output, FamilyTerminalEventFailureV1::duplicate_saved_scope_name);
    if (!ReadScope(bindings, row + 8, true, saved.scope))
      return Fail(output, FamilyTerminalEventFailureV1::character_scope_identity_invalid);
    record.saved_scopes.push_back(std::move(saved));
  }
  record.scopes_sampled = true;
  record.original_roles_match = ScopeIs(record.root_scope, request.played_character_id) &&
      NamedScopeIs(record, "actor", request.actor_character_id) &&
      NamedScopeIs(record, "recipient", request.recipient_character_id) &&
      NamedScopeIs(record, "secondary_actor", request.subject_character_id) &&
      NamedScopeIs(record, "secondary_recipient", request.candidate_character_id);
  // puppet_or_actor, when present, is retained above as a typed observation.
  // It is not a fifth required name or an invented value when absent.
  return true;
}

struct QueueObservation {
  const void *game_state = nullptr;
  const void *game_data = nullptr;
  const void *manager = nullptr;
  const void *data = nullptr;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
  std::vector<FamilyTerminalEventRecordV1> records;

  friend bool operator==(const QueueObservation &, const QueueObservation &) = default;
};

bool ReadQueue(const ck3_12002::EventWindowBindings &bindings,
               void *identifier_table, const FamilyTerminalEventsRequestV1 &request,
               QueueObservation &queue, FamilyTerminalEventsSnapshotV1 &output) {
  queue.game_state = *bindings.events.core.game_state_slot;
  if (queue.game_state == nullptr)
    return Fail(output, FamilyTerminalEventFailureV1::event_manager_unavailable);
  queue.game_data = Load<const void *>(queue.game_state, kGameDataOffset);
  if (queue.game_data == nullptr)
    return Fail(output, FamilyTerminalEventFailureV1::event_manager_unavailable);
  queue.manager = static_cast<const std::byte *>(queue.game_data) +
      ck3_12002::kEventManagerOffset;
  queue.data = Load<const void *>(queue.manager, kQueueDataOffset);
  queue.capacity = Load<std::int32_t>(queue.manager, kQueueCapacityOffset);
  queue.count = Load<std::int32_t>(queue.manager, kQueueCountOffset);
  if (queue.count < 0 || queue.capacity < queue.count ||
      queue.capacity > kMaximumQueueEntries || (queue.count != 0 && queue.data == nullptr))
    return Fail(output, FamilyTerminalEventFailureV1::queue_invalid);
  queue.records.reserve(static_cast<std::size_t>(queue.count));
  for (std::int32_t index = 0; index < queue.count; ++index) {
    const void *event = Load<const void *>(queue.data,
        static_cast<std::size_t>(index) * kQueueStride);
    if (event == nullptr)
      return Fail(output, FamilyTerminalEventFailureV1::event_record_invalid);
    const void *definition = Load<const void *>(event, kEventDefinitionOffset);
    if (definition == nullptr)
      return Fail(output, FamilyTerminalEventFailureV1::event_record_invalid);
    FamilyTerminalEventRecordV1 record{};
    record.queue_ordinal = static_cast<std::uint32_t>(index);
    record.event_address = reinterpret_cast<std::uintptr_t>(event);
    record.definition_address = reinterpret_cast<std::uintptr_t>(definition);
    record.event_instance_id = Load<std::int32_t>(event, kEventInstanceOffset);
    record.receiver_character_id = Load<std::int32_t>(event, kEventReceiverOffset);
    record.primary_raw = Load<std::uint8_t>(event, kEventPrimaryOffset);
    record.calculated_event_id = Load<std::int32_t>(definition, 8);
    record.runtime_stats_ordinal = Load<std::int32_t>(definition, 0xC);
    if (record.event_instance_id == -1)
      return Fail(output, FamilyTerminalEventFailureV1::event_record_invalid);
    if (!ReadNativeString(static_cast<const std::byte *>(definition) + 0x10,
                          record.event_definition_key))
      return Fail(output, FamilyTerminalEventFailureV1::event_key_invalid);
    if (record.event_definition_key == "marriage_interaction.0010")
      record.letter_kind = FamilyTerminalEventKindV1::acceptance;
    else if (record.event_definition_key == "marriage_interaction.0011")
      record.letter_kind = FamilyTerminalEventKindV1::refusal;
    if (record.letter_kind != FamilyTerminalEventKindV1::no_match &&
        record.receiver_character_id == request.played_character_id &&
        !ReadLetterScopes(bindings, identifier_table, event, request, record, output))
      return false;
    queue.records.push_back(std::move(record));
  }
  return true;
}

bool SameCore(const ck3_12002::CoreSnapshotPrefix &first,
              const ck3_12002::CoreSnapshotPrefix &last) noexcept {
  return first.clock.date_raw == last.clock.date_raw &&
      first.clock.speed == last.clock.speed && first.clock.paused == last.clock.paused &&
      first.local_player_id == last.local_player_id && first.map_ready == last.map_ready &&
      first.has_played_character == last.has_played_character &&
      first.played_character_id == last.played_character_id &&
      first.played_character_alive == last.played_character_alive;
}

bool ReadComplete(const ck3_12002::EventWindowBindings &bindings,
                  const FamilyTerminalEventsRequestV1 &request,
                  FamilyTerminalEventsSnapshotV1 &output) {
  ck3_12002::CoreSnapshotPrefix before{};
  if (!ck3_12002::ReadCoreSnapshot(bindings.events.core, before))
    return Fail(output, FamilyTerminalEventFailureV1::core_snapshot_unavailable);
  output.date_raw = before.clock.date_raw;
  output.played_character_id = before.played_character_id;
  output.paused = before.clock.paused;
  output.map_ready = before.map_ready;
  if (!before.has_played_character || !before.played_character_alive ||
      before.played_character_id != request.played_character_id ||
      before.clock.date_raw != request.expected_date_raw)
    return Fail(output, FamilyTerminalEventFailureV1::player_or_date_mismatch);
  if (!before.clock.paused || !before.map_ready)
    return Fail(output, FamilyTerminalEventFailureV1::paused_map_required);
  void *identifier_table = bindings.get_script_identifier_table();
  if (identifier_table == nullptr)
    return Fail(output, FamilyTerminalEventFailureV1::saved_scope_name_invalid);
  QueueObservation first{};
  QueueObservation last{};
  if (!ReadQueue(bindings, identifier_table, request, first, output) ||
      !ReadQueue(bindings, identifier_table, request, last, output)) return false;
  output.queue_read_complete = true;
  output.queue_count = last.count;
  output.queue_capacity = last.capacity;
  if (!(first == last))
    return Fail(output, FamilyTerminalEventFailureV1::queue_changed);
  output.queue_stable = true;
  ck3_12002::CoreSnapshotPrefix after{};
  if (!ck3_12002::ReadCoreSnapshot(bindings.events.core, after))
    return Fail(output, FamilyTerminalEventFailureV1::core_snapshot_unavailable);
  if (!SameCore(before, after))
    return Fail(output, FamilyTerminalEventFailureV1::core_snapshot_changed);
  for (const auto &record : last.records) {
    if (!record.original_roles_match) continue;
    ++output.matched_count;
    output.kind = output.matched_count == 1 ? record.letter_kind :
        FamilyTerminalEventKindV1::ambiguous;
  }
  output.records = std::move(last.records);
  output.available = true;
  return true;
}

} // namespace

std::string_view FamilyTerminalEventKindNameV1(FamilyTerminalEventKindV1 kind) noexcept {
  switch (kind) {
  case FamilyTerminalEventKindV1::no_match: return "no_match";
  case FamilyTerminalEventKindV1::refusal: return "refusal";
  case FamilyTerminalEventKindV1::acceptance: return "acceptance";
  case FamilyTerminalEventKindV1::ambiguous: return "ambiguous";
  }
  return "ambiguous";
}

std::string_view FamilyTerminalEventFailureNameV1(FamilyTerminalEventFailureV1 failure) noexcept {
  switch (failure) {
  case FamilyTerminalEventFailureV1::none: return "none";
  case FamilyTerminalEventFailureV1::invalid_request: return "invalid_request";
  case FamilyTerminalEventFailureV1::bindings_unavailable: return "bindings_unavailable";
  case FamilyTerminalEventFailureV1::core_snapshot_unavailable: return "core_snapshot_unavailable";
  case FamilyTerminalEventFailureV1::player_or_date_mismatch: return "player_or_date_mismatch";
  case FamilyTerminalEventFailureV1::paused_map_required: return "paused_map_required";
  case FamilyTerminalEventFailureV1::event_manager_unavailable: return "event_manager_unavailable";
  case FamilyTerminalEventFailureV1::queue_invalid: return "retained_player_event_queue_invalid";
  case FamilyTerminalEventFailureV1::event_record_invalid: return "retained_player_event_record_invalid";
  case FamilyTerminalEventFailureV1::event_key_invalid: return "retained_player_event_key_invalid";
  case FamilyTerminalEventFailureV1::saved_scope_vector_invalid: return "saved_scope_vector_invalid";
  case FamilyTerminalEventFailureV1::saved_scope_name_invalid: return "saved_scope_name_invalid";
  case FamilyTerminalEventFailureV1::duplicate_saved_scope_name: return "duplicate_saved_scope_name";
  case FamilyTerminalEventFailureV1::character_scope_identity_invalid: return "character_scope_identity_invalid";
  case FamilyTerminalEventFailureV1::queue_changed: return "retained_player_event_queue_changed";
  case FamilyTerminalEventFailureV1::core_snapshot_changed: return "core_snapshot_changed";
  case FamilyTerminalEventFailureV1::memory_read_failed: return "retained_player_event_memory_read_failed";
  case FamilyTerminalEventFailureV1::allocation_failed: return "allocation_failed";
  }
  return "retained_player_event_memory_read_failed";
}

bool ReadFamilyTerminalEventsV1(const ck3_12002::EventWindowBindings &bindings,
    const FamilyTerminalEventsRequestV1 &request,
    FamilyTerminalEventsSnapshotV1 &output) noexcept {
  output = {};
  if (request.expected_date_raw <= 0 || !ValidCharacterId(request.played_character_id) ||
      request.actor_character_id != request.played_character_id ||
      !ValidCharacterId(request.recipient_character_id) ||
      !ValidCharacterId(request.subject_character_id) ||
      !ValidCharacterId(request.candidate_character_id) ||
      request.subject_character_id == request.candidate_character_id)
    return Fail(output, FamilyTerminalEventFailureV1::invalid_request);
  if (!bindings.events.core.enabled || bindings.events.core.game_state_slot == nullptr ||
      bindings.events.core.character_storage_slot == nullptr ||
      bindings.get_script_identifier_table == nullptr ||
      bindings.resolve_script_identifier_name == nullptr ||
      bindings.lookup_script_identifier_id == nullptr ||
      bindings.script_identifier_name_fallback == nullptr)
    return Fail(output, FamilyTerminalEventFailureV1::bindings_unavailable);
  const bool read = ReadBoundary([&]() {
    try { return ReadComplete(bindings, request, output); }
    catch (...) { return Fail(output, FamilyTerminalEventFailureV1::allocation_failed); }
  });
  if (!read && output.failure == FamilyTerminalEventFailureV1::none)
    return Fail(output, FamilyTerminalEventFailureV1::memory_read_failed);
  return read;
}

} // namespace xar::ck3_12003
