#include "xar_bridge/faction_gift_mitigation_async_glue_v1.hpp"
#include "xar_bridge/faction_gift_receivers_v1.hpp"

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

bool SelectDirectTargetingMemberV1(
    const bridge::FactionTargetingRowProbeResultV1 &rows,
    const std::vector<std::int32_t> &direct_landed_vassals,
    std::uint32_t player_character_id, std::uint32_t &faction_id,
    std::uint32_t &recipient_id) noexcept {
  faction_id = 0;
  recipient_id = 0;
  if (rows.terminal != bridge::FactionTargetingRowProbeTerminalV1::ready)
    return false;
  const auto eligible = [&](std::uint32_t id) {
    return id != 0 && id != player_character_id &&
           std::binary_search(direct_landed_vassals.begin(),
                              direct_landed_vassals.end(),
                              static_cast<std::int32_t>(id));
  };
  for (std::size_t index = 0; index < rows.faction_count; ++index) {
    const auto &row = rows.factions[index];
    if (row.target_character_id != player_character_id) continue;
    if (row.leader_present && eligible(row.leader_character_id)) {
      faction_id = row.faction_id;
      recipient_id = row.leader_character_id;
      return true;
    }
    for (std::size_t member = 0;
         member < row.character_member_count; ++member) {
      const auto id = row.character_member_ids[member];
      if (!eligible(id)) continue;
      faction_id = row.faction_id;
      recipient_id = id;
      return true;
    }
  }
  return false;
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
  output.queried_source_faction_id = faction_id;
  output.source_faction_present = true;
  const bool war_read = query.offline_receivers_fixture
                            ? ReadFactionAtWarFromExactStoresV1(
                                  query.faction_at_war_exact_stores,
                                  faction_id, output.source_faction_at_war)
                            : ReadFactionAtWarExact11906V1(
                                  query.module_base, faction_id,
                                  output.source_faction_at_war);
  const bool metric_read = query.offline_receivers_fixture
                               ? ReadFactionMetricsFromExactFixtureV1(
                                     query.faction_metrics_exact_fixture,
                                     faction_id, output.power_raw,
                                     output.discontent_raw)
                               : ReadFactionMetricsExact11906V1(
                                     query.module_base, faction_id,
                                     output.power_raw,
                                     output.discontent_raw);
  output.metrics_available = metric_read;
  output.metric_scale = metric_read ? kFactionGiftMetricScaleV1 : 0;
  // Keep the source/details envelope readable so the async owner can publish
  // the dedicated receiver RED.  query_complete remains the only authority
  // for this field; the default false value is never accepted as an observed
  // no-war result when the exact receiver fails.
  output.query_complete = war_read;
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
  GiftOpinionReceiverResultV1 opinion{};
  const bool opinion_read =
      query.offline_receivers_fixture
          ? ReadGiftOpinionFromExactFixtureV1(
                query.gift_opinion_exact_fixture, recipient_id,
                required.player_character_id, opinion)
          : ReadGiftOpinionExact11906V1(
                query.module_base, query.bindings, recipient_id,
                required.player_character_id, opinion);
  if (opinion_read) {
    output.opinion_query_complete = opinion.query_complete;
    output.opinion_of_player = opinion.recipient_opinion_of_player;
    output.gift_opinion_present = opinion.gift_opinion_present;
    output.gift_opinion_modifier_value =
        opinion.gift_opinion_modifier_value;
  }
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
          query.bindings, query.module_base,
          query.offline_receivers_fixture
              ? &query.gift_opinion_exact_fixture
              : nullptr,
          player_id, recipient_id, output.preview)) {
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

bool CaptureIndependentReceiptPostV1(
    FactionGiftMitigationAsyncContextV1 &query,
    const game::Snapshot &current,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  const auto &ack = query.pending_ack;
  if (ack.status != game::FactionGiftMitigationAckStatusV1::
                        submitted_verification_pending ||
      !ack.verification_pending ||
      query.expected_public_revision <= ack.pre_snapshot_revision ||
      stamp.pump_epoch <= ack.pre_native_snapshot_revision ||
      current.date_raw != ack.pre_observed_date_raw ||
      current.played_character_id <= 0 ||
      static_cast<std::uint32_t>(current.played_character_id) !=
          ack.player_character_id ||
      query.source_faction_id != ack.source_faction_id ||
      query.recipient_character_id != ack.recipient_character_id ||
      current.played_character_gold.scale < 0 ||
      current.played_character_gold.scale >
          (std::numeric_limits<std::uint32_t>::max)()) {
    query.failure_flags |= faction_gift_async_failure_frame;
    return false;
  }

  FactionGiftIndependentEntityV1 entity{};
  if (!ReadFactionGiftIndependentEntityExact11906V1(
          query.module_base, query.bindings, query.source_faction_id,
          entity)) {
    query.failure_flags |=
        faction_gift_async_failure_independent_entity_receiver;
    return false;
  }
  const bridge::FactionTargetingRowProbeFactionV1 *source_row = nullptr;
  const bool in_targeting_view = FindFactionRow(
      query.targeting_rows, query.source_faction_id, source_row);
  if (!entity.present && in_targeting_view) {
    query.failure_flags |=
        faction_gift_async_failure_independent_entity_receiver;
    return false;
  }
  void *const recipient =
      ResolveCharacter(query.bindings, query.recipient_character_id);
  GiftOpinionReceiverResultV1 opinion{};
  if (recipient == nullptr ||
      !ReadGiftOpinionExact11906V1(
          query.module_base, query.bindings,
          query.recipient_character_id, ack.player_character_id,
          opinion) || !opinion.query_complete) {
    query.failure_flags |= faction_gift_async_failure_opinion_receiver;
    return false;
  }
  bool at_war = false;
  if (entity.present &&
      !ReadFactionAtWarExact11906V1(
          query.module_base, query.source_faction_id, at_war)) {
    query.failure_flags |= faction_gift_async_failure_faction_war_receiver;
    return false;
  }

  auto &post = query.observation;
  post = {};
  post.available = true;
  post.paused = true;
  post.snapshot_revision = query.expected_public_revision;
  post.native_snapshot_revision = stamp.pump_epoch;
  post.observed_date_raw = current.date_raw;
  post.player_resources_query_complete = true;
  post.player_character_id = ack.player_character_id;
  post.player_gold_raw = current.played_character_gold.raw;
  post.player_gold_scale =
      static_cast<std::uint32_t>(current.played_character_gold.scale);
  post.source_faction_requery_complete = true;
  post.queried_source_faction_id = query.source_faction_id;
  post.source_faction_present = entity.present;
  if (entity.present) {
    post.source_faction_target_character_id = entity.target_character_id;
    post.source_faction_targeting_player =
        entity.target_character_id == ack.player_character_id;
    post.source_faction_at_war = at_war;
    post.source_faction_leader_character_id =
        entity.leader_character_id;
    post.source_faction_member_character_ids =
        entity.member_character_ids;
    post.source_faction_metrics_available = entity.metrics_available;
    post.source_faction_power_raw = entity.power_raw;
    post.source_faction_discontent_raw = entity.discontent_raw;
    post.source_faction_metric_scale = entity.metric_scale;
  }
  post.recipient_identity_resolved = true;
  post.recipient_character_id = query.recipient_character_id;
  post.recipient_alive =
      LoadAt<void *>(recipient, kCharacterDeathDataOffset) == nullptr;
  post.recipient_opinion_query_complete = true;
  post.recipient_opinion_of_player =
      opinion.recipient_opinion_of_player;
  post.gift_opinion_present = opinion.gift_opinion_present;
  post.gift_opinion_modifier_value =
      opinion.gift_opinion_modifier_value;
  return true;
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
    const Bindings &bindings, std::uintptr_t module_base,
    const GiftOpinionReceiverFixtureV1 *offline_fixture,
    std::uint32_t player_character_id,
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
  std::int32_t opinion_delta = 0;
  const bool opinion_delta_read =
      offline_fixture != nullptr
          ? ReadGiftOpinionDeltaFromExactFixtureV1(
                *offline_fixture, recipient_character_id,
                player_character_id, opinion_delta)
          : ReadGiftOpinionDeltaExact11906V1(
                module_base, storage.data() + kContextScopeOffset,
                recipient_character_id, player_character_id,
                opinion_delta);
  bindings.destroy_character_interaction_context(storage.data());
  if (!opinion_delta_read) return false;
  output.available = true;
  output.definition_key.assign(
      kFactionGiftMitigationActionV1DefinitionKey);
  output.definition_stable_hash = stable_hash;
  output.interaction_legal = legal;
  output.auto_accept = auto_accept;
  output.gold_cost_raw = costs[0];
  output.gold_scale = kFactionGiftMitigationActionV1GoldScale;
  output.opinion_delta = opinion_delta;
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

bool CaptureFactionGiftColdRecoveryObservationV1(
    const Bindings &bindings, std::uintptr_t module_base,
    const game::Snapshot &current, std::uint64_t public_revision,
    std::uint64_t native_revision, std::uint32_t source_faction_id,
    std::uint32_t recipient_character_id,
    game::FactionGiftMitigationObservationV1 &output) noexcept {
  output = {};
  if (!current.paused || !current.map_ready || !current.has_played_character ||
      current.played_character_id <= 0 || public_revision == 0 ||
      native_revision == 0 || source_faction_id == 0 ||
      recipient_character_id == 0 ||
      current.played_character_gold.scale < 0 ||
      current.played_character_gold.scale >
          (std::numeric_limits<std::uint32_t>::max)()) {
    return false;
  }
  FactionGiftIndependentEntityV1 entity{};
  if (!ReadFactionGiftIndependentEntityExact11906V1(
          module_base, bindings, source_faction_id, entity)) {
    return false;
  }
  void *const recipient = ResolveCharacter(bindings, recipient_character_id);
  GiftOpinionReceiverResultV1 opinion{};
  if (recipient == nullptr ||
      !ReadGiftOpinionExact11906V1(
          module_base, bindings, recipient_character_id,
          static_cast<std::uint32_t>(current.played_character_id), opinion) ||
      !opinion.query_complete) {
    return false;
  }
  bool at_war = false;
  if (entity.present &&
      !ReadFactionAtWarExact11906V1(module_base, source_faction_id, at_war)) {
    return false;
  }
  output.available = true;
  output.paused = true;
  output.snapshot_revision = public_revision;
  output.native_snapshot_revision = native_revision;
  output.observed_date_raw = current.date_raw;
  output.player_resources_query_complete = true;
  output.player_character_id =
      static_cast<std::uint32_t>(current.played_character_id);
  output.player_gold_raw = current.played_character_gold.raw;
  output.player_gold_scale =
      static_cast<std::uint32_t>(current.played_character_gold.scale);
  output.source_faction_requery_complete = true;
  output.queried_source_faction_id = source_faction_id;
  output.source_faction_present = entity.present;
  if (entity.present) {
    output.source_faction_target_character_id = entity.target_character_id;
    output.source_faction_targeting_player =
        entity.target_character_id == output.player_character_id;
    output.source_faction_at_war = at_war;
    output.source_faction_leader_character_id = entity.leader_character_id;
    output.source_faction_member_character_ids = entity.member_character_ids;
    output.source_faction_metrics_available = entity.metrics_available;
    output.source_faction_power_raw = entity.power_raw;
    output.source_faction_discontent_raw = entity.discontent_raw;
    output.source_faction_metric_scale = entity.metric_scale;
  }
  output.recipient_identity_resolved = true;
  output.recipient_character_id = recipient_character_id;
  output.recipient_alive =
      LoadAt<void *>(recipient, kCharacterDeathDataOffset) == nullptr;
  output.recipient_opinion_query_complete = true;
  output.recipient_opinion_of_player = opinion.recipient_opinion_of_player;
  output.gift_opinion_present = opinion.gift_opinion_present;
  output.gift_opinion_modifier_value = opinion.gift_opinion_modifier_value;
  return true;
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
  query.preflight = {};
  query.preflight_attempted = false;
  query.receipt_pending = false;
  query.direct_source_known_empty = false;
  query.execution_stamp = stamp;
  if (!stamp.paused || stamp.pump_epoch == 0 ||
      stamp.date_raw != query.expected_snapshot.date_raw) {
    query.failure_flags |= faction_gift_async_failure_frame;
    return true;
  }
  if (query.use_direct_source_rows) {
    game::Snapshot current{};
    if (query.expected_public_revision == 0 ||
        !ReadSnapshot(query.bindings, current) ||
        current != query.expected_snapshot ||
        !current.has_played_character ||
        current.played_character_id <= 0 ||
        !ReadFactionGiftDirectTargetingRowsExact11906V1(
            query.module_base, query.bindings,
            {true, stamp.pump_epoch, query.expected_public_revision,
             current.date_raw,
             static_cast<std::uint32_t>(current.played_character_id)},
            query.targeting_rows)) {
      query.failure_flags |= faction_gift_async_failure_frame;
      return true;
    }
    query.direct_source_known_empty =
        query.targeting_rows.terminal ==
        bridge::FactionTargetingRowProbeTerminalV1::known_empty;
    if (query.verify_receipt) {
      CaptureIndependentReceiptPostV1(query, current, stamp);
      return true;
    }
    if (query.direct_source_known_empty) return true;
    if (query.source_faction_id == 0 || query.recipient_character_id == 0) {
      if (!SelectDirectTargetingMemberV1(
              query.targeting_rows,
              query.direct_landed_vassal_character_ids,
              static_cast<std::uint32_t>(current.played_character_id),
              query.source_faction_id,
              query.recipient_character_id)) {
        query.failure_flags |= faction_gift_async_failure_recipient;
        return true;
      }
    }
    if (query.execute_request) {
      if (query.prior_query_native_revision == 0 ||
          query.request.expected_native_revision !=
              query.prior_query_native_revision ||
          query.request.expected_revision !=
              query.expected_public_revision ||
          query.request.expected_date_raw != current.date_raw ||
          query.request.player_character_id !=
              static_cast<std::uint32_t>(current.played_character_id) ||
          query.request.source_faction_id != query.source_faction_id ||
          query.request.recipient_character_id !=
              query.recipient_character_id) {
        query.failure_flags |= faction_gift_async_failure_frame;
        return true;
      }
      // A subsequent paused application-main pulse can have a newer native
      // epoch while the public gameplay frame and selected source remain the
      // same. The certified action recaptures every field in this new epoch.
      query.request.expected_native_revision = stamp.pump_epoch;
    }
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
  if (!query.observation.source_faction_requery_complete) {
    query.failure_flags |= faction_gift_async_failure_faction_war_receiver;
  }
  if (!query.observation.source_faction_metrics_available) {
    query.failure_flags |= faction_gift_async_failure_faction_metric_receiver;
  }
  if (!query.observation.recipient_opinion_query_complete ||
      !query.observation.gift_preview.available) {
    query.failure_flags |= faction_gift_async_failure_opinion_receiver;
  }
  query.completion =
      query.observation.gift_preview.available
          ? FactionGiftMitigationAsyncCompletionV1::preview_ready
          : FactionGiftMitigationAsyncCompletionV1::unavailable;
  if (query.execute_request) {
    query.preflight_attempted = true;
    if (EvaluateFactionGiftMitigationIntegrationGateV1(
            binder, query.request, query.preflight) !=
        FactionGiftMitigationIntegrationGateTerminalV1::ready) {
      query.failure_flags |= faction_gift_async_failure_read_only_preflight;
      query.ack.request_id = query.request.request_id;
      query.ack.rejection_reason = query.preflight.first_red_reason;
      query.ack.failure_class =
          game::FactionGiftMitigationFailureClassV1::faction_binding;
      return true;
    }
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
  std::string typed_reds{"["};
  bool first_red = true;
  const auto append_red = [&](std::string_view red) {
    if (!first_red) typed_reds += ',';
    typed_reds += Quote(red);
    first_red = false;
  };
  if ((context.failure_flags &
       faction_gift_async_failure_faction_war_receiver) != 0) {
    append_red("faction_at_war_receiver_unavailable");
  }
  if ((context.failure_flags &
       faction_gift_async_failure_opinion_receiver) != 0) {
    append_red("gift_opinion_receiver_unavailable");
  }
  if ((context.failure_flags &
       faction_gift_async_failure_faction_metric_receiver) != 0) {
    append_red("faction_metric_receiver_unavailable");
  }
  if ((context.failure_flags &
       faction_gift_async_failure_read_only_preflight) != 0) {
    append_red("faction_gift_read_only_preflight_red");
  }
  if ((context.failure_flags &
       faction_gift_async_failure_independent_entity_receiver) != 0) {
    append_red("independent_faction_entity_requery_unavailable");
  }
  typed_reds += ']';
  std::string output =
      "{\"schema_version\":1,\"private\":true,\"completion\":" +
      Quote(completion) + ",\"failure_flags\":" +
      std::to_string(context.failure_flags) +
      ",\"typed_reds\":" + typed_reds +
      ",\"source_faction_id\":" +
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
      ",\"observed_date_raw\":" +
      std::to_string(observation.observed_date_raw) +
      ",\"player_resources_query_complete\":" +
      (observation.player_resources_query_complete ? "true" : "false") +
      ",\"player_character_id\":" +
      std::to_string(observation.player_character_id) +
      ",\"player_gold_raw\":" +
      std::to_string(observation.player_gold_raw) +
      ",\"player_gold_scale\":" +
      std::to_string(observation.player_gold_scale) +
      ",\"source_faction_requery_complete\":" +
      (observation.source_faction_requery_complete ? "true" : "false") +
      ",\"queried_source_faction_id\":" +
      std::to_string(observation.queried_source_faction_id) +
      ",\"source_faction_present\":" +
      (observation.source_faction_present ? "true" : "false") +
      ",\"source_faction_target_character_id\":" +
      std::to_string(observation.source_faction_target_character_id) +
      ",\"source_faction_targeting_player\":" +
      (observation.source_faction_targeting_player ? "true" : "false") +
      ",\"source_faction_at_war\":" +
      (observation.source_faction_at_war ? "true" : "false") +
      ",\"source_faction_metrics_available\":" +
      (observation.source_faction_metrics_available ? "true" : "false") +
      ",\"source_faction_power_raw\":" +
      std::to_string(observation.source_faction_power_raw) +
      ",\"source_faction_discontent_raw\":" +
      std::to_string(observation.source_faction_discontent_raw) +
      ",\"source_faction_metric_scale\":" +
      std::to_string(observation.source_faction_metric_scale) +
      ",\"recipient_identity_resolved\":" +
      (observation.recipient_identity_resolved ? "true" : "false") +
      ",\"recipient_character_id\":" +
      std::to_string(observation.recipient_character_id) +
      ",\"recipient_alive\":" +
      (observation.recipient_alive ? "true" : "false") +
      ",\"recipient_is_ai\":" +
      (observation.recipient_is_ai ? "true" : "false") +
      ",\"recipient_is_direct_landed_vassal\":" +
      (observation.recipient_is_direct_landed_vassal ? "true" : "false") +
      ",\"recipient_opinion_query_complete\":" +
      (observation.recipient_opinion_query_complete ? "true" : "false") +
      ",\"recipient_opinion_of_player\":" +
      std::to_string(observation.recipient_opinion_of_player) +
      ",\"gift_opinion_present\":" +
      (observation.gift_opinion_present ? "true" : "false") +
      ",\"gift_opinion_modifier_value\":" +
      (observation.gift_opinion_modifier_value.has_value()
           ? std::to_string(*observation.gift_opinion_modifier_value)
           : "null") +
      ",\"gift_preview\":{\"available\":" +
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
      ",\"opinion_delta\":" + std::to_string(preview.opinion_delta) +
      "}";
  output += ",\"source_faction_leader_character_id\":";
  output += observation.source_faction_leader_character_id.has_value()
                ? std::to_string(*observation.source_faction_leader_character_id)
                : "null";
  output += ",\"source_faction_member_character_ids\":[";
  for (std::size_t index = 0;
       index < observation.source_faction_member_character_ids.size();
       ++index) {
    if (index != 0) output += ',';
    output += std::to_string(
        observation.source_faction_member_character_ids[index]);
  }
  output += "]},\"receipt_pending\":";
  output += context.receipt_pending ? "true" : "false";
  if (context.execute_request) {
    output += ",\"ack\":" + SerializeFactionGiftMitigationAckV1(context.ack);
    output += ",\"preflight\":" +
              SerializeFactionGiftMitigationIntegrationGateResultV1(
                  context.preflight);
  } else {
    output += ",\"ack\":null";
    output += ",\"preflight\":null";
  }
  output += ",\"executor_invocations\":" +
            std::to_string(context.executor_invocations) + "}";
  return output;
}

} // namespace xar::ck3_11906
