#include "xar_bridge/faction_gift_mitigation_async_glue_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>

namespace {

constexpr std::int32_t kGiftHash = 0x12345678;
constexpr std::uintptr_t kPrimaryVtable = 0x11111111;
constexpr std::uintptr_t kSecondaryVtable = 0x22222222;
alignas(16) std::array<std::byte, 0x2B00> g_definition{};
std::array<std::byte, 32> g_database{};
std::array<char, 17> g_key_storage{
    'g', 'i', 'f', 't', '_', 'i', 'n', 't', 'e',
    'r', 'a', 'c', 't', 'i', 'o', 'n', '\0'};
int g_destroy_count = 0;
int g_submit_count = 0;
int g_hash_count = 0;
int g_lookup_count = 0;
int g_construct_count = 0;
xar::game::Snapshot g_snapshot{};
alignas(16) std::array<std::byte, 0x200> g_character{};
std::array<std::byte, 0x40> g_character_storage{};
std::array<std::byte, 203 * 0x10> g_character_slots{};
void *g_character_storage_pointer = g_character_storage.data();
std::array<std::byte, 0xB0> g_game_state{};
std::array<std::byte, 0x300> g_game_data{};
std::array<std::byte, 0xE0> g_player_entry{};
std::array<void *, 1> g_player_entries{g_player_entry.data()};
void *g_game_state_pointer = g_game_state.data();
std::array<std::byte, 0x40> g_faction_storage{};
std::array<std::byte, 304 * 0x10> g_faction_slots{};
std::array<std::byte, 0xA0> g_faction{};
std::array<std::byte, 0x20> g_faction_fallback{};
std::array<std::byte, 0x40> g_war_storage{};
std::array<std::byte, 405 * 0x10> g_war_slots{};
std::array<std::byte, 0x20> g_war{};
std::array<std::byte, 0x20> g_war_fallback{};
std::array<std::uintptr_t, 2> g_faction_vtable{};
std::array<std::uintptr_t, 2> g_war_vtable{};
std::array<std::uintptr_t, 2> g_null_war_vtable{};
constexpr std::uintptr_t kAliveLeaf = 0x33333333;
constexpr std::uintptr_t kNullAliveLeaf = 0x77777777;
constexpr std::uintptr_t kModifierDefinition = 0x88888888;
constexpr std::uintptr_t kModifierVtable = 0x99999999;
constexpr std::uintptr_t kNamedDefinition = 0xAAAAAAAA;
constexpr std::uintptr_t kNamedVtable = 0xBBBBBBBB;
constexpr std::uintptr_t kNamedSecondaryVtable = 0xCCCCCCCC;

template <typename T>
void Store(void *base, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value,
              sizeof(value));
}

void *GetDatabase() { return g_database.data(); }

std::int32_t Hash(void *database, const char *data, std::uint32_t size) {
  ++g_hash_count;
  return database == g_database.data() &&
                 std::string_view(data, size) == "gift_interaction"
             ? kGiftHash
             : 0;
}

void *Lookup(void *database, std::int32_t hash) {
  ++g_lookup_count;
  return database == g_database.data() && hash == kGiftHash
             ? g_definition.data()
             : nullptr;
}

void *Construct(void *context, void *definition, std::int32_t actor,
                std::int32_t recipient, void *, bool) {
  ++g_construct_count;
  if (definition != g_definition.data() || actor != 101 || recipient != 202)
    return nullptr;
  return context;
}

void Refresh(void *, bool) {}
void Finalize(void *) {}
bool Validate(void *, void *) { return true; }
bool Trigger(void *, const void *) { return true; }
void Costs(const void *block, const void *, std::int64_t *output) {
  if (block == g_definition.data() + 0x38) output[0] = 2'500'000;
}
void Destroy(void *) { ++g_destroy_count; }

void *ConstructCommand(void *command, const void *) {
  Store(command, 0x00, kPrimaryVtable);
  Store(command, 0x18, kSecondaryVtable);
  return command;
}

bool Submit(void *, void *, std::uint32_t flags) {
  if (flags != 0x0E) return false;
  ++g_submit_count;
  return true;
}

xar::ck3_11906::Bindings MakeBindings() {
  xar::ck3_11906::Bindings bindings{};
  bindings.enabled = true;
  bindings.command_manager = g_database.data();
  bindings.submit_command = &Submit;
  bindings.get_character_interaction_database = &GetDatabase;
  bindings.hash_stable_key = &Hash;
  bindings.lookup_character_interaction = &Lookup;
  bindings.evaluate_character_interaction_cost = &Costs;
  bindings.construct_character_interaction_context = &Construct;
  bindings.refresh_character_interaction_context = &Refresh;
  bindings.finalize_character_interaction_context = &Finalize;
  bindings.validate_character_interaction_context = &Validate;
  bindings.evaluate_character_interaction_trigger = &Trigger;
  bindings.construct_send_character_interaction_command = &ConstructCommand;
  bindings.destroy_character_interaction_context = &Destroy;
  bindings.send_character_interaction_primary_vtable = kPrimaryVtable;
  bindings.send_character_interaction_secondary_vtable = kSecondaryVtable;
  bindings.character_storage_slot = &g_character_storage_pointer;
  bindings.game_state_slot = &g_game_state_pointer;
  bindings.player_character_manager_offset = 0x100;
  return bindings;
}

bool Check(bool value, const char *message) {
  if (!value) std::cerr << message << '\n';
  return value;
}

} // namespace

namespace xar::ck3_11906 {
bool ReadSnapshot(const Bindings &, game::Snapshot &output) noexcept {
  output = g_snapshot;
  return true;
}
} // namespace xar::ck3_11906

int main() {
  constexpr std::string_view key = "gift_interaction";
  Store(g_definition.data(), 0x18, g_key_storage.data());
  Store(g_definition.data(), 0x14, kGiftHash);
  Store(g_definition.data(), 0x28,
        static_cast<std::uint64_t>(key.size()));
  Store(g_definition.data(), 0x30, std::uint64_t{31});
  Store(g_definition.data(), 0x2580, static_cast<void *>(nullptr));
  Store(g_definition.data(), 0x2A48, std::uint8_t{1});
  Store(g_character.data(), 0x18, std::uint32_t{202});
  Store(g_character.data(), 0x1C8, static_cast<void *>(nullptr));
  Store(g_character_slots.data(), 202 * 0x10 + 0x08,
        static_cast<void *>(g_character.data()));
  Store(g_character_storage.data(), 0x20,
        static_cast<void *>(g_character_slots.data()));
  Store(g_character_storage.data(), 0x2C, std::int32_t{203});
  Store(g_game_state.data(), 0xA0, static_cast<void *>(g_game_data.data()));
  Store(g_game_data.data() + 0x100, 0x58,
        static_cast<void *>(g_player_entries.data()));
  Store(g_game_data.data() + 0x100, 0x64, std::int32_t{1});
  Store(g_player_entry.data(), 0xB0, std::uint32_t{101});
  g_faction_vtable[0] = 0x44444444;
  g_war_vtable[0] = 0x55555555;
  g_war_vtable[1] = kAliveLeaf;
  g_null_war_vtable[0] = 0x66666666;
  g_null_war_vtable[1] = kNullAliveLeaf;
  Store(g_faction.data(), 0x00, g_faction_vtable.data());
  Store(g_faction.data(), 0x10, std::uint32_t{303});
  Store(g_faction.data(), 0x8C, std::uint32_t{404});
  Store(g_faction_slots.data(), 303 * 0x10 + 0x08,
        static_cast<void *>(g_faction.data()));
  Store(g_faction_storage.data(), 0x20,
        static_cast<void *>(g_faction_slots.data()));
  Store(g_faction_storage.data(), 0x2C, std::int32_t{304});
  Store(g_war.data(), 0x00, g_war_vtable.data());
  Store(g_war.data(), 0x08, std::uint32_t{404});
  Store(g_war_slots.data(), 404 * 0x10 + 0x08,
        static_cast<void *>(g_war.data()));
  Store(g_war_storage.data(), 0x20,
        static_cast<void *>(g_war_slots.data()));
  Store(g_war_storage.data(), 0x2C, std::int32_t{405});
  Store(g_war_fallback.data(), 0x00, g_null_war_vtable.data());
  Store(g_war_fallback.data(), 0x08, std::uint32_t{0xFFFFFFFFU});

  const auto bindings = MakeBindings();
  xar::ck3_11906::GiftOpinionReceiverFixtureV1 gift_fixture{};
  gift_fixture.available = true;
  gift_fixture.recipient_identity_before = 202;
  gift_fixture.recipient_identity_after = 202;
  gift_fixture.player_identity_before = 101;
  gift_fixture.player_identity_after = 101;
  gift_fixture.modifier_definition = kModifierDefinition;
  gift_fixture.modifier_definition_after = kModifierDefinition;
  gift_fixture.modifier_vtable = kModifierVtable;
  gift_fixture.expected_modifier_vtable = kModifierVtable;
  gift_fixture.modifier_hash =
      xar::ck3_11906::kFactionGiftOpinionModifierStableHashV1;
  gift_fixture.modifier_key =
      xar::ck3_11906::kFactionGiftOpinionModifierKeyV1;
  gift_fixture.opinion_first = 0;
  gift_fixture.opinion_second = 0;
  gift_fixture.modifier_present_first = false;
  gift_fixture.modifier_present_second = false;
  gift_fixture.named_definition = kNamedDefinition;
  gift_fixture.named_definition_after = kNamedDefinition;
  gift_fixture.named_vtable = kNamedVtable;
  gift_fixture.named_secondary_vtable = kNamedSecondaryVtable;
  gift_fixture.expected_named_vtable = kNamedVtable;
  gift_fixture.expected_named_secondary_vtable = kNamedSecondaryVtable;
  gift_fixture.named_hash =
      xar::ck3_11906::kFactionGiftSendOpinionStableHashV1;
  gift_fixture.named_key =
      xar::ck3_11906::kFactionGiftSendOpinionKeyV1;
  gift_fixture.opinion_delta_first = 40;
  gift_fixture.opinion_delta_second = 40;
  xar::ck3_11906::GiftOpinionReceiverResultV1 gift_result{};
  if (!Check(xar::ck3_11906::ReadGiftOpinionFromExactFixtureV1(
                 gift_fixture, 202, 101, gift_result) &&
                 gift_result.query_complete &&
                 gift_result.recipient_opinion_of_player == 0 &&
                 !gift_result.gift_opinion_present &&
                 !gift_result.gift_opinion_modifier_value.has_value(),
             "legal zero opinion/absent modifier fixture failed")) {
    return 1;
  }
  auto present_zero = gift_fixture;
  present_zero.modifier_present_first = true;
  present_zero.modifier_present_second = true;
  present_zero.modifier_value_first = 0;
  present_zero.modifier_value_second = 0;
  if (!Check(xar::ck3_11906::ReadGiftOpinionFromExactFixtureV1(
                 present_zero, 202, 101, gift_result) &&
                 gift_result.gift_opinion_present &&
                 gift_result.gift_opinion_modifier_value == 0,
             "present zero modifier must differ from unavailable")) {
    return 1;
  }
  auto generation_drift = gift_fixture;
  generation_drift.recipient_identity_after = 0x010000CA;
  if (!Check(!xar::ck3_11906::ReadGiftOpinionFromExactFixtureV1(
                 generation_drift, 202, 101, gift_result),
             "generation drift fixture was accepted")) {
    return 1;
  }
  const xar::ck3_11906::FactionAtWarExactStoresV1 faction_stores{
      g_faction_storage.data(), g_faction_fallback.data(),
      g_war_storage.data(), g_war_fallback.data(),
      reinterpret_cast<std::uintptr_t>(g_faction_vtable.data()),
      reinterpret_cast<std::uintptr_t>(g_war_vtable.data()),
      reinterpret_cast<std::uintptr_t>(g_null_war_vtable.data()), kAliveLeaf,
      kNullAliveLeaf};
  bool faction_at_war = false;
  if (!Check(xar::ck3_11906::ReadFactionAtWarFromExactStoresV1(
                 faction_stores, 303, faction_at_war) && faction_at_war,
             "at-war exact receiver failed")) {
    return 1;
  }
  Store(g_faction.data(), 0x8C, std::uint32_t{0xFFFFFFFFU});
  if (!Check(xar::ck3_11906::ReadFactionAtWarFromExactStoresV1(
                 faction_stores, 303, faction_at_war) && !faction_at_war,
             "legal no-war exact receiver failed")) {
    return 1;
  }
  Store(g_faction.data(), 0x8C, std::uint32_t{404});
  const auto saved_war_vtable = g_war_vtable[1];
  g_war_vtable[1] = 0;
  if (!Check(!xar::ck3_11906::ReadFactionAtWarFromExactStoresV1(
                 faction_stores, 303, faction_at_war),
             "war vtable gate accepted mismatch")) {
    return 1;
  }
  g_war_vtable[1] = saved_war_vtable;
  xar::game::FactionGiftPreviewV1 preview{};
  if (!Check(xar::ck3_11906::
                 ReadFactionGiftPreviewThroughGenericInteractionV1(
                     bindings, 0, &gift_fixture, 101, 202, preview),
             "preview failed")) {
    std::cerr << "hash=" << g_hash_count << " lookup=" << g_lookup_count
              << " construct=" << g_construct_count << '\n';
    return 1;
  }
  if (
      !Check(preview.available && preview.definition_key == key &&
                 preview.definition_stable_hash ==
                     static_cast<std::uint32_t>(kGiftHash) &&
                 preview.interaction_legal && preview.auto_accept &&
                 preview.gold_cost_raw == 2'500'000 &&
                 preview.gold_scale == 100000 &&
                 preview.opinion_delta == 40,
             "preview mismatch")) {
    return 1;
  }
  bool valid = false;
  std::string reason;
  if (!Check(xar::ck3_11906::
                 ValidateFactionGiftThroughGenericInteractionDirectV1(
                     bindings, 101, 202, key,
                     static_cast<std::uint32_t>(kGiftHash), valid, reason) &&
                 valid && reason.empty(),
             "validate failed") ||
      !Check(xar::ck3_11906::
                 SubmitFactionGiftThroughGenericInteractionDirectV1(
                     bindings, 101, 202, key,
                     static_cast<std::uint32_t>(kGiftHash)),
             "submit failed") ||
      !Check(g_submit_count == 1 && g_destroy_count == 4,
             "lifecycle mismatch")) {
    return 1;
  }

  g_snapshot.date_raw = 100;
  g_snapshot.speed = 1;
  g_snapshot.paused = true;
  g_snapshot.player_id = 1;
  g_snapshot.map_ready = true;
  g_snapshot.has_played_character = true;
  g_snapshot.played_character_id = 101;
  g_snapshot.played_character_alive = true;
  g_snapshot.played_character_gold = {5'000'000, 100'000};
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::FactionGiftMitigationAsyncContextV1 query{};
  query.mailbox = &mailbox;
  query.bindings = bindings;
  query.module_base = 0x10000000;
  query.offline_receivers_fixture = true;
  query.faction_at_war_exact_stores = {
      g_faction_storage.data(), g_faction_fallback.data(),
      g_war_storage.data(), g_war_fallback.data(),
      reinterpret_cast<std::uintptr_t>(g_faction_vtable.data()),
      reinterpret_cast<std::uintptr_t>(g_war_vtable.data()),
      reinterpret_cast<std::uintptr_t>(g_null_war_vtable.data()),
      kAliveLeaf, kNullAliveLeaf};
  query.gift_opinion_exact_fixture = gift_fixture;
  query.expected_snapshot = g_snapshot;
  query.targeting_rows.terminal =
      xar::bridge::FactionTargetingRowProbeTerminalV1::ready;
  query.targeting_rows.published_generation = 2;
  query.targeting_rows.required_binding = {true, 7, 11, 100, 101};
  query.targeting_rows.observed_binding =
      query.targeting_rows.required_binding;
  query.targeting_rows.faction_count = 1;
  query.targeting_rows.factions[0].faction_id = 303;
  query.targeting_rows.factions[0].target_character_id = 101;
  query.targeting_rows.factions[0].leader_present = true;
  query.targeting_rows.factions[0].leader_character_id = 202;
  query.targeting_rows.factions[0].leader_present_in_character_members = true;
  query.targeting_rows.factions[0].character_member_count = 1;
  query.targeting_rows.factions[0].character_member_ids[0] = 202;
  query.direct_landed_vassal_character_ids = {202};
  query.source_faction_id = 303;
  query.recipient_character_id = 202;
  xar::ck3_11906::MainThreadExecutionStampV1 stamp{};
  stamp.paused = true;
  stamp.pump_epoch = 12;
  stamp.date_raw = 100;
  if (!Check(xar::ck3_11906::ExecuteFactionGiftMitigationAsyncMailboxV1(
                 &query, stamp),
             "async executor failed") ||
      !Check(query.completion == xar::ck3_11906::
                                     FactionGiftMitigationAsyncCompletionV1::
                                         preview_ready &&
                 query.observation.available &&
                 query.observation.snapshot_revision == 11 &&
                 query.observation.native_snapshot_revision == 12 &&
                 query.observation.player_gold_raw == 5'000'000 &&
                 query.observation.recipient_alive &&
                 query.observation.recipient_is_ai &&
                 query.observation.recipient_is_direct_landed_vassal &&
                 query.observation.source_faction_requery_complete &&
                 query.observation.source_faction_at_war &&
                 query.observation.recipient_opinion_query_complete &&
                 query.observation.recipient_opinion_of_player == 0 &&
                 !query.observation.gift_opinion_present &&
                 query.observation.gift_preview.gold_cost_raw == 2'500'000 &&
                 query.observation.gift_preview.opinion_delta == 40 &&
                 query.failure_flags ==
                     xar::ck3_11906::faction_gift_async_failure_none &&
                 !query.receipt_pending,
             "async stack mismatch")) {
    return 1;
  }

  // Receiver failures remain typed REDs.  A war receiver identity drift must
  // not be hidden by the independently successful opinion and preview reads.
  auto war_receiver_red = query;
  war_receiver_red.faction_at_war_exact_stores.expected_war_alive_leaf =
      kAliveLeaf + 1;
  stamp.pump_epoch = 13;
  if (!Check(xar::ck3_11906::ExecuteFactionGiftMitigationAsyncMailboxV1(
                 &war_receiver_red, stamp),
             "war receiver RED executor failed") ||
      !Check(war_receiver_red.failure_flags ==
                 xar::ck3_11906::
                     faction_gift_async_failure_faction_war_receiver &&
                 !war_receiver_red.observation.
                     source_faction_requery_complete &&
                 war_receiver_red.observation.
                     recipient_opinion_query_complete &&
                 war_receiver_red.observation.gift_preview.available,
             "war receiver drift did not remain a local typed RED")) {
    return 1;
  }

  // Opinion observation is independently fail-closed.  The legal gift
  // preview may still be published for diagnosis, but the action gate keeps
  // the receiver RED and cannot treat the default zero as an observed value.
  auto opinion_receiver_red = query;
  opinion_receiver_red.gift_opinion_exact_fixture.
      modifier_definition_after = kModifierDefinition + 1;
  stamp.pump_epoch = 14;
  if (!Check(xar::ck3_11906::ExecuteFactionGiftMitigationAsyncMailboxV1(
                 &opinion_receiver_red, stamp),
             "opinion receiver RED executor failed") ||
      !Check(opinion_receiver_red.failure_flags ==
                 xar::ck3_11906::
                     faction_gift_async_failure_opinion_receiver &&
                 opinion_receiver_red.observation.
                     source_faction_requery_complete &&
                 !opinion_receiver_red.observation.
                     recipient_opinion_query_complete &&
                 opinion_receiver_red.observation.gift_preview.available,
             "opinion receiver drift did not remain a local typed RED")) {
    return 1;
  }

  // The closed receivers must unlock the real action preconditions rather
  // than merely replacing the old RED string. A legal no-war sample with no
  // existing modifier reaches the generic validate/send chain and publishes
  // a pending receipt.
  Store(g_faction.data(), 0x8C, std::uint32_t{0xFFFFFFFFU});
  auto action_query = query;
  action_query.execute_request = true;
  action_query.request.request_id = "faction16-gift";
  action_query.request.idempotency_key = "faction16-gift-once";
  action_query.request.expected_revision = 11;
  action_query.request.expected_native_revision = 15;
  action_query.request.expected_date_raw = 100;
  action_query.request.player_character_id = 101;
  action_query.request.source_faction_id = 303;
  action_query.request.recipient_character_id = 202;
  action_query.request.membership_role =
      xar::game::FactionGiftMembershipRoleV1::leader;
  action_query.request.expected_definition_key = "gift_interaction";
  action_query.request.expected_definition_stable_hash =
      static_cast<std::uint32_t>(kGiftHash);
  action_query.request.expected_gold_cost_raw = 2'500'000;
  action_query.request.expected_gold_scale = 100'000;
  action_query.request.expected_opinion_delta = 40;
  action_query.request.minimum_gold_reserve_raw = 1'000'000;
  action_query.request.minimum_gold_reserve_scale = 100'000;
  stamp.pump_epoch = 15;
  if (!Check(xar::ck3_11906::ExecuteFactionGiftMitigationAsyncMailboxV1(
                 &action_query, stamp),
             "action-ready async executor failed") ||
      !Check(action_query.failure_flags ==
                 xar::ck3_11906::faction_gift_async_failure_none &&
                 action_query.observation.source_faction_requery_complete &&
                 !action_query.observation.source_faction_at_war &&
                 action_query.observation.recipient_opinion_query_complete &&
                 action_query.observation.gift_preview.opinion_delta == 40 &&
                 action_query.ack.status == xar::game::
                     FactionGiftMitigationAckStatusV1::
                         submitted_verification_pending &&
                 action_query.ack.verification_pending &&
                 action_query.receipt_pending &&
                 action_query.idempotency_claimed && g_submit_count == 2,
             "closed receivers did not unlock action readiness")) {
    return 1;
  }

  xar::ck3_11906::FactionGiftMitigationAsyncContextV1 context{};
  context.completion = xar::ck3_11906::
      FactionGiftMitigationAsyncCompletionV1::preview_ready;
  context.failure_flags = xar::ck3_11906::
                              faction_gift_async_failure_faction_war_receiver |
                          xar::ck3_11906::
                              faction_gift_async_failure_opinion_receiver;
  context.source_faction_id = 303;
  context.recipient_character_id = 202;
  context.observation.available = true;
  context.observation.gift_preview = preview;
  const auto json = xar::ck3_11906::
      SerializeFactionGiftMitigationAsyncContextV1(context);
  if (!Check(json.find("\"completion\":\"preview_ready\"") !=
                 std::string::npos &&
                 json.find("\"gold_cost_raw\":2500000") !=
                     std::string::npos &&
                 json.find("\"opinion_delta\":40") !=
                     std::string::npos &&
                 json.find("gift_opinion_receiver_unavailable") !=
                     std::string::npos &&
                 json.find("\"receipt_pending\":false") !=
                     std::string::npos,
             "serializer mismatch")) {
    return 1;
  }
  return 0;
}
