#include "xar_bridge/faction_gift_mitigation_async_glue_v1.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstring>
#include <limits>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

constexpr std::size_t kContextSize = 0x338;
constexpr std::size_t kCommandSize = 0x368;
constexpr std::size_t kCommandContextOffset = 0x20;
constexpr std::size_t kDefinitionHashOffset = 0x14;
constexpr std::size_t kDefinitionKeyOffset = 0x18;
constexpr std::size_t kDefinitionCostOffset = 0x38;
constexpr std::size_t kDefinitionAutoAcceptTriggerOffset = 0x2580;
constexpr std::size_t kDefinitionAutoAcceptScalarOffset = 0x2A48;
constexpr std::size_t kContextScopeOffset = 0x08;
constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotSize = 0x10;
constexpr std::size_t kStorageSlotObjectOffset = 0x08;
constexpr std::size_t kCharacterIdOffset = 0x18;
constexpr std::size_t kCharacterDeathDataOffset = 0x1C8;
constexpr std::size_t kGameStateGameDataOffset = 0xA0;
constexpr std::size_t kPlayerEntriesOffset = 0x58;
constexpr std::size_t kPlayerEntryCountOffset = 0x64;
constexpr std::size_t kPlayerCharacterIdOffset = 0xB0;
constexpr std::size_t kMaximumCharacters = 1 << 24;
constexpr std::int32_t kMaximumPlayerEntries = 1024;
constexpr std::size_t kCostResourceCount = 10;

template <typename T>
T LoadAt(const void *base, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset,
              sizeof(value));
  return value;
}

bool ReadMsvcString(const void *storage, std::string &output) noexcept {
  output.clear();
  if (storage == nullptr) return false;
  const auto size = LoadAt<std::uint64_t>(storage, 0x10);
  const auto capacity = LoadAt<std::uint64_t>(storage, 0x18);
  if (size > capacity || size > 256) return false;
  const char *data = capacity < 16
                         ? static_cast<const char *>(storage)
                         : LoadAt<const char *>(storage, 0x00);
  if (size != 0 && data == nullptr) return false;
  output.assign(data == nullptr ? "" : data, static_cast<std::size_t>(size));
  return true;
}

void *ResolveCharacter(const Bindings &bindings,
                       std::uint32_t character_id) noexcept {
  if (bindings.character_storage_slot == nullptr) return nullptr;
  void *const storage = *bindings.character_storage_slot;
  if (storage == nullptr) return nullptr;
  void *const slots = LoadAt<void *>(storage, kStorageSlotsOffset);
  const auto capacity = LoadAt<std::int32_t>(storage, kStorageCapacityOffset);
  const auto index = character_id & 0x00FFFFFFU;
  if (slots == nullptr || capacity <= 0 ||
      static_cast<std::size_t>(capacity) > kMaximumCharacters ||
      index >= static_cast<std::uint32_t>(capacity)) {
    return nullptr;
  }
  void *const object = LoadAt<void *>(
      slots, static_cast<std::size_t>(index) * kStorageSlotSize +
                 kStorageSlotObjectOffset);
  return object != nullptr &&
                 LoadAt<std::uint32_t>(object, kCharacterIdOffset) ==
                     character_id
             ? object
             : nullptr;
}

bool ReadCharacterIsAi(const Bindings &bindings,
                       std::uint32_t character_id, bool &is_ai) noexcept {
  is_ai = false;
  if (bindings.game_state_slot == nullptr ||
      bindings.player_character_manager_offset == 0) {
    return false;
  }
  void *const game_state = *bindings.game_state_slot;
  void *const game_data =
      game_state == nullptr
          ? nullptr
          : LoadAt<void *>(game_state, kGameStateGameDataOffset);
  if (game_data == nullptr) return false;
  const auto *const manager = static_cast<const std::byte *>(game_data) +
                              bindings.player_character_manager_offset;
  void *const entries = LoadAt<void *>(manager, kPlayerEntriesOffset);
  const auto count = LoadAt<std::int32_t>(manager, kPlayerEntryCountOffset);
  if (entries == nullptr || count <= 0 || count > kMaximumPlayerEntries) {
    return false;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    void *const entry =
        LoadAt<void *>(entries, static_cast<std::size_t>(index) *
                                    sizeof(void *));
    if (entry != nullptr &&
        LoadAt<std::uint32_t>(entry, kPlayerCharacterIdOffset) ==
            character_id) {
      is_ai = false;
      return true;
    }
  }
  is_ai = true;
  return true;
}

bool ResolveGiftDefinition(const Bindings &bindings, void *&definition,
                           std::uint64_t &stable_hash) noexcept {
  definition = nullptr;
  stable_hash = 0;
  if (!bindings.enabled ||
      bindings.get_character_interaction_database == nullptr ||
      bindings.hash_stable_key == nullptr ||
      bindings.lookup_character_interaction == nullptr) {
    return false;
  }
  void *const database = bindings.get_character_interaction_database();
  if (database == nullptr) return false;
  constexpr auto key = kFactionGiftMitigationActionV1DefinitionKey;
  const auto hash = bindings.hash_stable_key(
      database, key.data(), static_cast<std::uint32_t>(key.size()));
  void *const candidate =
      bindings.lookup_character_interaction(database, hash);
  if (candidate == nullptr ||
      LoadAt<std::int32_t>(candidate, kDefinitionHashOffset) != hash) {
    return false;
  }
  std::string round_trip;
  if (!ReadMsvcString(static_cast<std::byte *>(candidate) +
                          kDefinitionKeyOffset,
                      round_trip) ||
      round_trip != key) {
    return false;
  }
  definition = candidate;
  stable_hash = static_cast<std::uint32_t>(hash);
  return true;
}

bool PrepareGiftContext(const Bindings &bindings, std::uint32_t actor,
                        std::uint32_t recipient, void *context,
                        void *&definition,
                        std::uint64_t &stable_hash) noexcept {
  if (context == nullptr ||
      bindings.construct_character_interaction_context == nullptr ||
      bindings.refresh_character_interaction_context == nullptr ||
      bindings.finalize_character_interaction_context == nullptr ||
      bindings.destroy_character_interaction_context == nullptr ||
      !ResolveGiftDefinition(bindings, definition, stable_hash)) {
    return false;
  }
  if (bindings.construct_character_interaction_context(
          context, definition, static_cast<std::int32_t>(actor),
          static_cast<std::int32_t>(recipient), nullptr, true) != context) {
    return false;
  }
  bindings.refresh_character_interaction_context(context, true);
  bindings.finalize_character_interaction_context(context);
  return true;
}

using ContextStorage = std::array<std::byte, kContextSize>;
using CommandStorage = std::array<std::byte, kCommandSize>;

bool FindFactionRow(const bridge::FactionTargetingRowProbeResultV1 &rows,
                    std::uint32_t faction_id,
                    const bridge::FactionTargetingRowProbeFactionV1 *&row)
    noexcept {
  row = nullptr;
  for (std::size_t index = 0; index < rows.faction_count; ++index) {
    if (rows.factions[index].faction_id != faction_id) continue;
    if (row != nullptr) return false;
    row = &rows.factions[index];
  }
  return row != nullptr;
}

bool ReadRows(void *context,
              bridge::FactionTargetingRowProbeResultV1 &output) noexcept {
  output = static_cast<FactionGiftMitigationAsyncContextV1 *>(context)
               ->targeting_rows;
  return true;
}

bool ReadFrame(void *context,
               const FactionGiftMitigationSourceFrameV1 &required,
               FactionGiftMitigationNativeFrameObservationV1 &output)
    noexcept {
  auto &query = *static_cast<FactionGiftMitigationAsyncContextV1 *>(context);
  output = {};
  game::Snapshot current{};
  if (query.mailbox == nullptr ||
      !ReadSnapshot(query.bindings, current) ||
      current != query.expected_snapshot || !current.paused ||
      !current.has_played_character || current.played_character_id <= 0 ||
      required.snapshot_revision == 0 ||
      required.snapshot_revision != query.targeting_rows.observed_binding.snapshot_revision ||
      required.date_raw != current.date_raw ||
      required.player_character_id !=
          static_cast<std::uint32_t>(current.played_character_id)) {
    return false;
  }
  output.available = true;
  output.frame = required;
  output.frame.native_snapshot_revision = query.execution_stamp.pump_epoch;
  if (output.frame.native_snapshot_revision == 0) return false;
  output.player_resources_query_complete = true;
  output.player_gold_raw = current.played_character_gold.raw;
  if (current.played_character_gold.scale < 0 ||
      current.played_character_gold.scale >
          (std::numeric_limits<std::uint32_t>::max)()) {
    return false;
  }
  output.player_gold_scale =
      static_cast<std::uint32_t>(current.played_character_gold.scale);
  return true;
}

bool ReadFaction(void *context,
                 const FactionGiftMitigationSourceFrameV1 &required,
                 std::uint32_t faction_id,
                 FactionGiftMitigationNativeFactionObservationV1 &output)
    noexcept {
  auto &query = *static_cast<FactionGiftMitigationAsyncContextV1 *>(context);
  output = {};
  const bridge::FactionTargetingRowProbeFactionV1 *row = nullptr;
  if (!FindFactionRow(query.targeting_rows, faction_id, row)) return false;
  output.available = true;
  output.frame = required;
  output.query_complete = false;
  output.queried_source_faction_id = faction_id;
  output.source_faction_present = true;
  // No exact CFaction-at-war receiver is certified. Leaving query_complete
  // false prevents this placeholder value from passing the action gate.
  output.source_faction_at_war = false;
  return true;
}

bool ReadRecipient(void *context,
                   const FactionGiftMitigationSourceFrameV1 &required,
                   std::uint32_t recipient_id,
                   FactionGiftMitigationNativeRecipientObservationV1 &output)
    noexcept {
  auto &query = *static_cast<FactionGiftMitigationAsyncContextV1 *>(context);
  output = {};
  void *const character = ResolveCharacter(query.bindings, recipient_id);
  if (character == nullptr) return false;
  output.available = true;
  output.frame = required;
  output.identity_resolved = true;
  output.recipient_character_id = recipient_id;
  output.alive =
      LoadAt<void *>(character, kCharacterDeathDataOffset) == nullptr;
  if (!ReadCharacterIsAi(query.bindings, recipient_id, output.is_ai)) {
    output = {};
    return false;
  }
  output.is_direct_landed_vassal = std::binary_search(
      query.direct_landed_vassal_character_ids.begin(),
      query.direct_landed_vassal_character_ids.end(),
      static_cast<std::int32_t>(recipient_id));
  output.opinion_query_complete = false;
  return true;
}

bool ReadPreview(void *context,
                 const FactionGiftMitigationSourceFrameV1 &required,
                 std::uint32_t player_id, std::uint32_t recipient_id,
                 FactionGiftMitigationNativePreviewObservationV1 &output)
    noexcept {
  auto &query = *static_cast<FactionGiftMitigationAsyncContextV1 *>(context);
  output = {};
  if (!ReadFactionGiftPreviewThroughGenericInteractionV1(
          query.bindings, player_id, recipient_id, output.preview)) {
    return false;
  }
  output.available = true;
  output.frame = required;
  output.player_character_id = player_id;
  output.recipient_character_id = recipient_id;
  return true;
}

bool ValidateGift(void *context, std::uint32_t player_id,
                  std::uint32_t recipient_id, std::string_view key,
                  std::uint64_t stable_hash, bool &valid,
                  std::string &reason) noexcept {
  return ValidateFactionGiftThroughGenericInteractionDirectV1(
      static_cast<FactionGiftMitigationAsyncContextV1 *>(context)->bindings,
      player_id, recipient_id, key, stable_hash, valid, reason);
}

bool Claim(void *context, std::string_view) noexcept {
  auto &query = *static_cast<FactionGiftMitigationAsyncContextV1 *>(context);
  if (query.idempotency_claimed) return false;
  query.idempotency_claimed = true;
  return true;
}

bool SubmitGift(void *context, std::uint32_t player_id,
                std::uint32_t recipient_id, std::string_view key,
                std::uint64_t stable_hash) noexcept {
  return SubmitFactionGiftThroughGenericInteractionDirectV1(
      static_cast<FactionGiftMitigationAsyncContextV1 *>(context)->bindings,
      player_id, recipient_id, key, stable_hash);
}

std::string Quote(std::string_view value) {
  std::string output{"\""};
  for (const char character : value) {
    if (character == '\\' || character == '"') output.push_back('\\');
    output.push_back(character);
  }
  output.push_back('"');
  return output;
}

} // namespace

bool ReadFactionGiftPreviewThroughGenericInteractionV1(
    const Bindings &bindings, std::uint32_t player_character_id,
    std::uint32_t recipient_character_id,
    game::FactionGiftPreviewV1 &output) noexcept {
  output = {};
  alignas(16) ContextStorage storage{};
  void *definition = nullptr;
  std::uint64_t stable_hash = 0;
  if (bindings.validate_character_interaction_context == nullptr ||
      bindings.evaluate_character_interaction_trigger == nullptr ||
      bindings.evaluate_character_interaction_cost == nullptr ||
      !PrepareGiftContext(bindings, player_character_id,
                          recipient_character_id, storage.data(),
                          definition, stable_hash)) {
    return false;
  }
  const bool legal = bindings.validate_character_interaction_context(
      storage.data(), nullptr);
  void *const trigger = LoadAt<void *>(
      definition, kDefinitionAutoAcceptTriggerOffset);
  const bool auto_accept =
      trigger != nullptr
          ? bindings.evaluate_character_interaction_trigger(
                trigger, storage.data() + kContextScopeOffset)
          : LoadAt<std::uint8_t>(definition,
                                 kDefinitionAutoAcceptScalarOffset) != 0;
  std::array<std::int64_t, kCostResourceCount> costs{};
  bindings.evaluate_character_interaction_cost(
      static_cast<const std::byte *>(definition) + kDefinitionCostOffset,
      storage.data() + kContextScopeOffset, costs.data());
  bindings.destroy_character_interaction_context(storage.data());
  output.available = true;
  output.definition_key.assign(
      kFactionGiftMitigationActionV1DefinitionKey);
  output.definition_stable_hash = stable_hash;
  output.interaction_legal = legal;
  output.auto_accept = auto_accept;
  output.gold_cost_raw = costs[0];
  output.gold_scale = kFactionGiftMitigationActionV1GoldScale;
  // This field is deliberately a typed gap until send_gift_opinion's exact
  // receiver and the existing modifier collector are closed.
  output.opinion_delta = 0;
  return true;
}

bool ValidateFactionGiftThroughGenericInteractionDirectV1(
    const Bindings &bindings, std::uint32_t player_character_id,
    std::uint32_t recipient_character_id, std::string_view definition_key,
    std::uint64_t expected_definition_stable_hash, bool &valid,
    std::string &native_reason_key) noexcept {
  valid = false;
  native_reason_key.clear();
  if (definition_key != kFactionGiftMitigationActionV1DefinitionKey ||
      bindings.validate_character_interaction_context == nullptr) {
    native_reason_key = "gift_definition_mismatch";
    return true;
  }
  alignas(16) ContextStorage storage{};
  void *definition = nullptr;
  std::uint64_t stable_hash = 0;
  if (!PrepareGiftContext(bindings, player_character_id,
                          recipient_character_id, storage.data(),
                          definition, stable_hash)) {
    native_reason_key = "gift_context_unavailable";
    return false;
  }
  if (stable_hash != expected_definition_stable_hash) {
    bindings.destroy_character_interaction_context(storage.data());
    native_reason_key = "gift_definition_hash_changed";
    return true;
  }
  valid = bindings.validate_character_interaction_context(
      storage.data(), nullptr);
  bindings.destroy_character_interaction_context(storage.data());
  if (!valid) native_reason_key = "native_gift_validator_rejected";
  return true;
}

bool SubmitFactionGiftThroughGenericInteractionDirectV1(
    const Bindings &bindings, std::uint32_t player_character_id,
    std::uint32_t recipient_character_id, std::string_view definition_key,
    std::uint64_t expected_definition_stable_hash) noexcept {
  if (definition_key != kFactionGiftMitigationActionV1DefinitionKey ||
      bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.validate_character_interaction_context == nullptr ||
      bindings.construct_send_character_interaction_command == nullptr ||
      bindings.send_character_interaction_primary_vtable == 0 ||
      bindings.send_character_interaction_secondary_vtable == 0) {
    return false;
  }
  alignas(16) ContextStorage context{};
  void *definition = nullptr;
  std::uint64_t stable_hash = 0;
  if (!PrepareGiftContext(bindings, player_character_id,
                          recipient_character_id, context.data(),
                          definition, stable_hash)) {
    return false;
  }
  if (stable_hash != expected_definition_stable_hash ||
      !bindings.validate_character_interaction_context(context.data(),
                                                       nullptr)) {
    bindings.destroy_character_interaction_context(context.data());
    return false;
  }
  alignas(16) CommandStorage command{};
  const bool constructed =
      bindings.construct_send_character_interaction_command(
          command.data(), context.data()) ==
          command.data() &&
      LoadAt<std::uintptr_t>(command.data(), 0) ==
          bindings.send_character_interaction_primary_vtable &&
      LoadAt<std::uintptr_t>(command.data(), 0x18) ==
          bindings.send_character_interaction_secondary_vtable;
  bool submitted = false;
  if (constructed) {
    submitted = bindings.submit_command(bindings.command_manager,
                                        command.data(), 0x0E);
    bindings.destroy_character_interaction_context(
        command.data() + kCommandContextOffset);
  } else if (LoadAt<void *>(command.data(), kCommandContextOffset) !=
             nullptr) {
    bindings.destroy_character_interaction_context(
        command.data() + kCommandContextOffset);
  }
  bindings.destroy_character_interaction_context(context.data());
  return constructed && submitted;
}

bool ExecuteFactionGiftMitigationAsyncMailboxV1(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept {
  if (context == nullptr) return false;
  auto &query = *static_cast<FactionGiftMitigationAsyncContextV1 *>(context);
  ++query.executor_invocations;
  query.completion = FactionGiftMitigationAsyncCompletionV1::unavailable;
  query.failure_flags = faction_gift_async_failure_none;
  query.observation = {};
  query.ack = {};
  query.receipt_pending = false;
  query.execution_stamp = stamp;
  if (!stamp.paused || stamp.pump_epoch == 0 ||
      stamp.date_raw != query.expected_snapshot.date_raw) {
    query.failure_flags |= faction_gift_async_failure_frame;
    return true;
  }

  FactionGiftMitigationNativeBinderEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.executable_sha256 = kFactionGiftMitigationActionV1ExecutableSha256;
  environment.module_base = query.module_base;
  for (std::size_t index = 0;
       index < kFactionGiftMitigationNativeAnchorCountV1; ++index) {
    environment.anchors[index] = {
        kFactionGiftMitigationExpectedAnchorsV1[index].rva,
        query.module_base +
            kFactionGiftMitigationExpectedAnchorsV1[index].rva,
        std::string{kFactionGiftMitigationExpectedAnchorsV1[index]
                        .span_sha256}};
  }
  FactionGiftMitigationNativeUpstreamV1 upstream{};
  upstream.row_context = &query;
  upstream.read_targeting_rows = &ReadRows;
  upstream.native_context = &query;
  upstream.read_frame = &ReadFrame;
  upstream.read_faction = &ReadFaction;
  upstream.read_recipient = &ReadRecipient;
  upstream.read_preview = &ReadPreview;
  upstream.validate_gift = &ValidateGift;
  upstream.claim_idempotency_key = &Claim;
  upstream.submit_gift = &SubmitGift;
  FactionGiftMitigationNativeBinderStateV1 binder{};
  if (!BindFactionGiftMitigationNativeCallbacksV1(
          binder, environment, upstream)) {
    query.failure_flags |= faction_gift_async_failure_frame;
    return true;
  }
  auto access = MakeFactionGiftMitigationNativeSourceActionAccessV1(binder);
  if (!CaptureFactionGiftMitigationObservationFromSourcesV1(
          access, query.source_faction_id, query.recipient_character_id,
          query.observation)) {
    query.failure_flags |= faction_gift_async_failure_frame;
    return true;
  }
  if (!query.observation.recipient_identity_resolved) {
    query.failure_flags |= faction_gift_async_failure_recipient;
  }
  if (!query.observation.gift_preview.available) {
    query.failure_flags |= faction_gift_async_failure_preview;
  }
  query.failure_flags |= faction_gift_async_failure_faction_war_receiver |
                         faction_gift_async_failure_opinion_receiver;
  query.completion =
      query.observation.gift_preview.available
          ? FactionGiftMitigationAsyncCompletionV1::preview_ready
          : FactionGiftMitigationAsyncCompletionV1::unavailable;
  if (query.execute_request) {
    ExecuteFactionGiftMitigationSourceActionAdapterV1(
        MakeFactionGiftMitigationCertifiedActionEnvironmentV1(binder),
        access, query.request, query.ack);
    query.receipt_pending =
        query.ack.status == game::FactionGiftMitigationAckStatusV1::
                                submitted_verification_pending;
  }
  return true;
}

std::string SerializeFactionGiftMitigationAsyncContextV1(
    const FactionGiftMitigationAsyncContextV1 &context) {
  const auto completion =
      context.completion ==
              FactionGiftMitigationAsyncCompletionV1::preview_ready
          ? "preview_ready"
          : context.completion ==
                    FactionGiftMitigationAsyncCompletionV1::unavailable
                ? "unavailable"
                : "not_executed";
  const auto &observation = context.observation;
  const auto &preview = observation.gift_preview;
  std::string output =
      "{\"schema_version\":1,\"private\":true,\"completion\":" +
      Quote(completion) + ",\"failure_flags\":" +
      std::to_string(context.failure_flags) +
      ",\"typed_reds\":[\"faction_at_war_receiver_unclosed\","
      "\"gift_opinion_receiver_unclosed\"],\"source_faction_id\":" +
      std::to_string(context.source_faction_id) +
      ",\"recipient_character_id\":" +
      std::to_string(context.recipient_character_id) +
      ",\"observation\":{\"available\":" +
      (observation.available ? "true" : "false") +
      ",\"paused\":" + (observation.paused ? "true" : "false") +
      ",\"snapshot_revision\":" +
      std::to_string(observation.snapshot_revision) +
      ",\"native_snapshot_revision\":" +
      std::to_string(observation.native_snapshot_revision) +
      ",\"date_raw\":" + std::to_string(observation.observed_date_raw) +
      ",\"player_character_id\":" +
      std::to_string(observation.player_character_id) +
      ",\"player_gold_raw\":" +
      std::to_string(observation.player_gold_raw) +
      ",\"player_gold_scale\":" +
      std::to_string(observation.player_gold_scale) +
      ",\"recipient_alive\":" +
      (observation.recipient_alive ? "true" : "false") +
      ",\"recipient_is_ai\":" +
      (observation.recipient_is_ai ? "true" : "false") +
      ",\"recipient_is_direct_landed_vassal\":" +
      (observation.recipient_is_direct_landed_vassal ? "true" : "false") +
      ",\"preview\":{\"available\":" +
      (preview.available ? "true" : "false") +
      ",\"definition_key\":" + Quote(preview.definition_key) +
      ",\"definition_stable_hash\":" +
      std::to_string(preview.definition_stable_hash) +
      ",\"interaction_legal\":" +
      (preview.interaction_legal ? "true" : "false") +
      ",\"auto_accept\":" +
      (preview.auto_accept ? "true" : "false") +
      ",\"gold_cost_raw\":" + std::to_string(preview.gold_cost_raw) +
      ",\"gold_scale\":" + std::to_string(preview.gold_scale) +
      ",\"opinion_delta\":null}},\"receipt_pending\":" +
      (context.receipt_pending ? "true" : "false");
  if (context.execute_request) {
    output += ",\"ack\":" + SerializeFactionGiftMitigationAckV1(context.ack);
  } else {
    output += ",\"ack\":null";
  }
  output += ",\"executor_invocations\":" +
            std::to_string(context.executor_invocations) + "}";
  return output;
}

} // namespace xar::ck3_11906
