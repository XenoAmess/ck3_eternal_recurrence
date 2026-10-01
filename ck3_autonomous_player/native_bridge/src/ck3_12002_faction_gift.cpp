#include "xar_bridge/ck3_12002_faction_gift.hpp"

#include <algorithm>
#include <array>
#include <cstring>

namespace xar::ck3_12002 {
namespace {

template <typename T> T Load(const void *base, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(T));
  return value;
}

struct alignas(8) GiftContext {
  std::array<std::byte, kFactionGiftContextSizeV1> bytes{};
};
struct alignas(8) GiftCommand {
  std::array<std::byte, kFactionGiftCommandSizeV1> bytes{};
};

bool ReadOpinion(void *, std::uintptr_t module, const CoreBindings &core,
    std::uint32_t recipient, std::uint32_t actor, GiftOpinionResult &output) noexcept {
  return ReadGiftOpinionExact12002(module, core, recipient, actor, output);
}
bool ReadDelta(void *, std::uintptr_t module, const void *scope,
    std::uint32_t recipient, std::uint32_t actor, std::int32_t &output) noexcept {
  return ReadGiftOpinionDeltaExact12002(module, scope, recipient, actor, output);
}
bool ReadGiftValue(void *, std::uintptr_t module, const void *scope,
    std::uint32_t recipient, std::uint32_t actor, std::int64_t &output) noexcept {
  return ReadGiftValueExact12002(module, scope, recipient, actor, output);
}

bool HasContextBindings(const FactionGiftBindingsV1 &b) noexcept {
  const auto &c = b.interaction;
  return b.enabled && c.enabled && c.core.enabled && b.get_database != nullptr &&
      b.stable_hash != nullptr && b.lookup_definition != nullptr &&
      b.construct_two_role != nullptr && c.refresh != nullptr &&
      c.finalize != nullptr && c.validate != nullptr && c.destroy != nullptr;
}

bool ReadKey(const void *definition, std::string &key) {
  const auto *text = static_cast<const std::byte *>(definition) +
      kFactionGiftDefinitionKeyOffsetV1;
  const auto size = Load<std::uint64_t>(text, 0x10);
  const auto capacity = Load<std::uint64_t>(text, 0x18);
  if (size > capacity || size > 256) return false;
  const char *data = capacity < 16 ? reinterpret_cast<const char *>(text) :
      Load<const char *>(text, 0);
  if (size != 0 && data == nullptr) return false;
  key.assign(data == nullptr ? "" : data, static_cast<std::size_t>(size));
  return true;
}

bool ResolveDefinition(const FactionGiftBindingsV1 &b, void *&definition,
    std::uint64_t &hash) {
  definition = nullptr; hash = 0;
  void *database = b.get_database();
  if (database == nullptr) return false;
  constexpr auto key = ck3_11906::kFactionGiftMitigationActionV1DefinitionKey;
  const auto native_hash = b.stable_hash(database, key.data(),
      static_cast<std::uint32_t>(key.size()));
  void *candidate = b.lookup_definition(database, native_hash);
  std::string native_key;
  if (candidate == nullptr || Load<std::int32_t>(candidate,
          kFactionGiftDefinitionHashOffsetV1) != native_hash ||
      !ReadKey(candidate, native_key) || native_key != key) return false;
  definition = candidate;
  hash = static_cast<std::uint32_t>(native_hash);
  return true;
}

bool BindPlayedPair(const FactionGiftBindingsV1 &b, std::uint32_t actor,
    std::uint32_t recipient) noexcept {
  CoreSnapshotPrefix frame{};
  if (!ReadCoreSnapshot(b.interaction.core, frame) || !frame.clock.paused ||
      !frame.map_ready || !frame.has_played_character ||
      !frame.played_character_alive ||
      static_cast<std::uint32_t>(frame.played_character_id) != actor ||
      actor == recipient) return false;
  void *target = ResolveCoreCharacter(b.interaction.core,
      static_cast<std::int32_t>(recipient));
  return target != nullptr && Load<void *>(target, kCharacterDeathDataOffset) == nullptr;
}

bool Prepare(const FactionGiftBindingsV1 &b, std::uint32_t actor,
    std::uint32_t recipient, GiftContext &context, void *&definition,
    std::uint64_t &hash) {
  if (!HasContextBindings(b) || !BindPlayedPair(b, actor, recipient) ||
      !ResolveDefinition(b, definition, hash)) return false;
  void *storage = context.bytes.data();
  if (b.construct_two_role(storage, definition, static_cast<std::int32_t>(actor),
          static_cast<std::int32_t>(recipient), nullptr, true) != storage)
    return false;
  b.interaction.refresh(storage, true);
  b.interaction.finalize(storage);
  if (Load<void *>(storage, 0) != definition ||
      Load<std::uint32_t>(storage, kFactionGiftContextActorOffsetV1) != actor ||
      Load<std::uint32_t>(storage, kFactionGiftContextRecipientOffsetV1) != recipient ||
      Load<std::uint32_t>(storage, kFactionGiftContextPayerOffsetV1) != actor) {
    b.interaction.destroy(storage);
    return false;
  }
  return true;
}

bool NoSendCost(const std::array<std::int64_t, 10> &cost) noexcept {
  return std::all_of(cost.begin(), cost.end(),
      [](std::int64_t value) { return value == 0; });
}

void Replace(std::string &text, std::string_view before, std::string_view after) {
  const auto found = text.find(before);
  if (found != std::string::npos) text.replace(found, before.size(), after);
}

} // namespace

FactionGiftBindingsV1 BindFactionGiftImageV1(std::uintptr_t base,
    std::string_view sha) noexcept {
  FactionGiftBindingsV1 b{};
  b.interaction = BindContextImage(base, sha);
  if (!b.interaction.enabled) return b;
  b.enabled = true;
  b.module_base = base;
  b.get_database = reinterpret_cast<FactionGiftGetDatabaseV1>(
      base + kFactionGiftDatabaseGetterRvaV1);
  b.stable_hash = reinterpret_cast<FactionGiftStableHashV1>(
      base + kFactionGiftStableHashRvaV1);
  b.lookup_definition = reinterpret_cast<FactionGiftLookupDefinitionV1>(
      base + kFactionGiftDefinitionLookupRvaV1);
  b.construct_two_role = reinterpret_cast<FactionGiftConstructTwoRoleContextV1>(
      base + kFactionGiftConstructTwoRoleContextRvaV1);
  b.read_opinion = &ReadOpinion;
  b.read_opinion_delta = &ReadDelta;
  b.read_gift_value = &ReadGiftValue;
  return b;
}

bool ReadFactionGiftPreviewV1(const FactionGiftBindingsV1 &b,
    std::uint32_t actor, std::uint32_t recipient,
    game::FactionGiftPreviewV1 &output) noexcept {
  output = {};
  try {
    if (b.interaction.evaluate_cost == nullptr ||
        b.interaction.evaluate_trigger == nullptr || b.read_opinion_delta == nullptr ||
        b.read_gift_value == nullptr)
      return false;
    GiftContext context{};
    void *definition = nullptr;
    std::uint64_t hash = 0;
    if (!Prepare(b, actor, recipient, context, definition, hash)) return false;
    void *storage = context.bytes.data();
    const bool legal = b.interaction.validate(storage, nullptr);
    void *trigger = Load<void *>(definition, kFactionGiftAutoAcceptTriggerOffsetV1);
    const bool automatic = trigger != nullptr ?
        b.interaction.evaluate_trigger(trigger, context.bytes.data() + 8) :
        Load<std::uint8_t>(definition, kFactionGiftAutoAcceptScalarOffsetV1) != 0;
    std::array<std::int64_t, 10> costs{};
    b.interaction.evaluate_cost(static_cast<const std::byte *>(definition) +
        kFactionGiftDefinitionCostOffsetV1, context.bytes.data() + 8, costs.data());
    std::int32_t delta = 0;
    const bool read = b.read_opinion_delta(b.opinion_delta_context, b.module_base,
        context.bytes.data() + 8, recipient, actor, delta);
    std::int64_t gift_gold = 0;
    const bool value_read = b.read_gift_value(b.gift_value_context, b.module_base,
        context.bytes.data() + 8, recipient, actor, gift_gold);
    b.interaction.destroy(storage);
    if (!read || !value_read || !NoSendCost(costs)) return false;
    output.available = true;
    output.definition_key.assign(ck3_11906::kFactionGiftMitigationActionV1DefinitionKey);
    output.definition_stable_hash = hash;
    output.interaction_legal = legal;
    output.auto_accept = automatic;
    output.gold_cost_raw = gift_gold;
    output.gold_scale = 100000;
    output.opinion_delta = delta;
    return true;
  } catch (...) { output = {}; return false; }
}

bool ValidateFactionGiftV1(const FactionGiftBindingsV1 &b,
    std::uint32_t actor, std::uint32_t recipient, std::string_view key,
    std::uint64_t expected_hash, bool &valid, std::string &reason) noexcept {
  valid = false; reason.clear();
  try {
    if (key != ck3_11906::kFactionGiftMitigationActionV1DefinitionKey) {
      reason = "gift_definition_mismatch"; return true;
    }
    GiftContext context{};
    void *definition = nullptr;
    std::uint64_t hash = 0;
    if (!Prepare(b, actor, recipient, context, definition, hash)) {
      reason = "gift_context_unavailable"; return false;
    }
    if (hash != expected_hash) {
      b.interaction.destroy(context.bytes.data());
      reason = "gift_definition_hash_changed"; return true;
    }
    valid = b.interaction.validate(context.bytes.data(), nullptr);
    b.interaction.destroy(context.bytes.data());
    if (!valid) reason = "native_gift_validator_rejected";
    return true;
  } catch (...) { reason = "gift_context_unavailable"; return false; }
}

bool SubmitFactionGiftV1(const FactionGiftBindingsV1 &b, std::uint32_t actor,
    std::uint32_t recipient, std::string_view key, std::uint64_t expected_hash) noexcept {
  try {
    const auto &c = b.interaction;
    if (key != ck3_11906::kFactionGiftMitigationActionV1DefinitionKey ||
        !c.commands.enabled || c.construct_send_command == nullptr ||
        c.send_primary_vtable == 0 || c.send_secondary_vtable == 0) return false;
    GiftContext context{};
    void *definition = nullptr;
    std::uint64_t hash = 0;
    if (!Prepare(b, actor, recipient, context, definition, hash)) return false;
    if (hash != expected_hash || !c.validate(context.bytes.data(), nullptr)) {
      c.destroy(context.bytes.data()); return false;
    }
    GiftCommand command{};
    void *native = command.bytes.data();
    const bool constructed = c.construct_send_command(native, context.bytes.data()) == native;
    const bool identity = constructed &&
        Load<std::uintptr_t>(native, 0) == c.send_primary_vtable &&
        Load<std::uintptr_t>(native, 0x18) == c.send_secondary_vtable &&
        Load<void *>(native, 0x20) == definition &&
        Load<std::uint32_t>(native, 0x20 + kFactionGiftContextActorOffsetV1) == actor &&
        Load<std::uint32_t>(native, 0x20 + kFactionGiftContextRecipientOffsetV1) == recipient &&
        Load<std::uint32_t>(native, 0x20 + kFactionGiftContextPayerOffsetV1) == actor;
    const auto result = identity ? SubmitCommandCopy(c.commands, native, 0x0E) :
        CommandSubmitResult::unavailable;
    if (constructed || Load<void *>(native, 0x20) != nullptr)
      c.destroy(static_cast<std::byte *>(native) + 0x20);
    c.destroy(context.bytes.data());
    return result == CommandSubmitResult::submitted;
  } catch (...) { return false; }
}

bool CaptureFactionGiftObservationV1(const FactionGiftBindingsV1 &b,
    const PlayerFactionAlertsNativeEnvironmentV1 &factions,
    const PlayerFactionAlertsAccessV1 &access,
    const game::CampaignRootContextV1 &campaign, std::uint64_t native_revision,
    std::uint32_t faction_id, std::uint32_t recipient,
    bool require_preview, game::FactionGiftMitigationObservationV1 &output) noexcept {
  output = {};
  try {
    if (!b.enabled || b.read_opinion == nullptr ||
        factions.character_is_human == nullptr || !factions.exact_build_admitted ||
        access.is_main_thread == nullptr || !access.is_main_thread(access.context) ||
        campaign.status != game::CampaignRootContextStatusV1::available ||
        !campaign.readiness.direct_landed_vassals_ready ||
        campaign.snapshot_revision == 0 || native_revision == 0 ||
        !campaign.player_character_id || !campaign.player_character_alive.value_or(false))
      return false;
    const auto actor = static_cast<std::uint32_t>(*campaign.player_character_id);
    CoreSnapshotPrefix before{};
    if (!ReadCoreSnapshot(b.interaction.core, before) || !before.clock.paused ||
        !before.map_ready || !before.has_played_character || !before.played_character_alive ||
        before.played_character_id != *campaign.player_character_id ||
        before.clock.date_raw != campaign.date_raw) return false;
    void *player = ResolveCoreCharacter(b.interaction.core, before.played_character_id);
    void *target = ResolveCoreCharacter(b.interaction.core, static_cast<std::int32_t>(recipient));
    if (player == nullptr || target == nullptr) return false;
    void *extension = Load<void *>(player, kFactionGiftCharacterExtensionOffsetV1);
    if (extension == nullptr) return false;
    const auto gold = Load<std::int64_t>(extension, kFactionGiftCharacterGoldOffsetV1);
    game::PlayerTargetingFactionV1 row{};
    const auto found = ReadFactionEntityV1(factions, access,
        static_cast<std::int32_t>(faction_id), row);
    if (found == ReadFactionEntityResult12002::unavailable) return false;
    GiftOpinionResult opinion{};
    if (!b.read_opinion(b.opinion_context, b.module_base, b.interaction.core,
            recipient, actor, opinion) || !opinion.query_complete) return false;
    game::FactionGiftMitigationObservationV1 observed{};
    observed.paused = true;
    observed.snapshot_revision = campaign.snapshot_revision;
    observed.native_snapshot_revision = native_revision;
    observed.observed_date_raw = campaign.date_raw;
    observed.player_resources_query_complete = true;
    observed.player_character_id = actor;
    observed.player_gold_raw = gold;
    observed.player_gold_scale = 100000;
    observed.source_faction_requery_complete = true;
    observed.queried_source_faction_id = faction_id;
    observed.source_faction_present = found == ReadFactionEntityResult12002::available;
    if (observed.source_faction_present) {
      observed.source_faction_target_character_id = static_cast<std::uint32_t>(row.target_character_id);
      observed.source_faction_targeting_player = row.target_character_id == before.played_character_id;
      observed.source_faction_at_war = row.faction_at_war;
      if (row.leader_character_id) observed.source_faction_leader_character_id =
          static_cast<std::uint32_t>(*row.leader_character_id);
      for (auto id : row.character_member_ids)
        observed.source_faction_member_character_ids.push_back(static_cast<std::uint32_t>(id));
      std::sort(observed.source_faction_member_character_ids.begin(),
          observed.source_faction_member_character_ids.end());
      observed.source_faction_metrics_available = true;
      observed.source_faction_power_raw = row.power.raw;
      observed.source_faction_discontent_raw = row.discontent.raw;
      observed.source_faction_metric_scale = static_cast<std::uint32_t>(row.power.scale);
    }
    observed.recipient_identity_resolved = true;
    observed.recipient_character_id = recipient;
    observed.recipient_alive = Load<void *>(target, kCharacterDeathDataOffset) == nullptr;
    observed.recipient_is_ai = !factions.character_is_human(recipient);
    observed.recipient_is_direct_landed_vassal = std::find(
        campaign.direct_landed_vassal_character_ids.begin(),
        campaign.direct_landed_vassal_character_ids.end(),
        static_cast<std::int32_t>(recipient)) != campaign.direct_landed_vassal_character_ids.end();
    observed.recipient_opinion_query_complete = true;
    observed.recipient_opinion_of_player = opinion.recipient_opinion_of_player;
    observed.gift_opinion_present = opinion.gift_opinion_present;
    observed.gift_opinion_modifier_value = opinion.gift_opinion_modifier_value;
    if (require_preview && !ReadFactionGiftPreviewV1(b, actor, recipient, observed.gift_preview))
      return false;
    CoreSnapshotPrefix after{};
    if (!ReadCoreSnapshot(b.interaction.core, after) || !after.clock.paused ||
        after.clock.date_raw != before.clock.date_raw ||
        after.played_character_id != before.played_character_id ||
        after.has_played_character != before.has_played_character ||
        after.played_character_alive != before.played_character_alive ||
        ResolveCoreCharacter(b.interaction.core, before.played_character_id) != player ||
        ResolveCoreCharacter(b.interaction.core, static_cast<std::int32_t>(recipient)) != target ||
        Load<void *>(player, kFactionGiftCharacterExtensionOffsetV1) != extension ||
        Load<std::int64_t>(extension, kFactionGiftCharacterGoldOffsetV1) != gold) return false;
    observed.available = true;
    output = std::move(observed);
    return true;
  } catch (...) { output = {}; return false; }
}

game::FactionGiftMitigationAckStatusV1 ExecuteFactionGiftActionV1(
    const ck3_11906::FactionGiftMitigationNativeEnvironmentV1 &environment,
    const ck3_11906::FactionGiftMitigationActionAccessV1 &access,
    const game::FactionGiftMitigationRequestV1 &request,
    game::FactionGiftMitigationAckV1 &ack) noexcept {
  return ck3_11906::ExecuteFactionGiftMitigationActionV1(environment, access, request, ack);
}

std::string SerializeFactionGiftAckV1(const game::FactionGiftMitigationAckV1 &ack) {
  auto json = ck3_11906::SerializeFactionGiftMitigationAckV1(ack);
  const auto change_field = [&json](std::string_view key,
      std::string_view before, std::string_view after) {
    Replace(json, "\"" + std::string(key) + "\":\"" + std::string(before) + "\"",
        "\"" + std::string(key) + "\":\"" + std::string(after) + "\"");
  };
  change_field("game_version", ck3_11906::kFactionGiftMitigationActionV1GameVersion, "1.20.0.2");
  change_field("executable_sha256", ck3_11906::kFactionGiftMitigationActionV1ExecutableSha256, kExecutableSha256);
  change_field("backend_id", ck3_11906::kFactionGiftMitigationActionV1BackendId, kFactionGiftBackendIdV1);
  change_field("contract_stage", ck3_11906::kFactionGiftMitigationActionV1ContractStage, kFactionGiftContractStageV1);
  return json;
}

} // namespace xar::ck3_12002
