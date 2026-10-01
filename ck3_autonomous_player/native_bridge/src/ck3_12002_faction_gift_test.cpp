#ifdef NDEBUG
#undef NDEBUG
#endif
#include "xar_bridge/ck3_12002_faction_gift.hpp"

#include <array>
#include <cassert>
#include <cstring>
#include <fstream>
#include <iostream>
#include <vector>

namespace {
using namespace xar::ck3_12002;
constexpr std::uint32_t actor_id = 0x03000001;
constexpr std::uint32_t recipient_id = 0x04000002;
constexpr std::int32_t definition_hash = kFactionGiftDefinitionStableHashV1;
template <typename T> void Put(void *base, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(T));
}
template <typename T> T Get(const void *base, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(T));
  return value;
}

void *local_player = nullptr;
void *database = nullptr;
void *definition = nullptr;
std::array<std::byte, 0x98> opinion_definition{};
std::array<std::byte, 0x40> opinion_extension{}, opinion_group{};
std::array<std::byte, 0x30> opinion_active{};
std::array<void *, 1> opinion_rows{opinion_active.data()};
void *opinion_database = opinion_definition.data();
bool gift_applied = false;
std::array<std::uintptr_t, 9> command_vtable{};
const std::uintptr_t secondary_vtable = 0x12002034;
bool legal = true, queue_accepts = true, other_payer = false;
bool other_cost = false, value_available = true, delta_available = true;
int constructs = 0, destroys = 0, clones = 0, queues = 0;
std::int32_t delta = 35;
std::int64_t gift_value = 7'500'000;
void *LocalPlayer(void *) { return local_player; }
void *Database() { return database; }
std::int32_t Hash(void *db, const char *key, std::uint32_t size) {
  assert(db == database && std::string_view(key, size) == "gift_interaction");
  return definition_hash;
}
void *Lookup(void *db, std::int32_t hash) {
  assert(db == database && hash == definition_hash); return definition;
}
void *Construct(void *storage, void *def, std::int32_t actor,
    std::int32_t recipient, void *extra, bool redirect_roles) {
  assert(def == definition && extra == nullptr && redirect_roles);
  ++constructs;
  Put(storage, 0, def); Put(storage, 0x2D8, actor);
  Put(storage, 0x2DC, recipient); Put(storage, 0x2E0, std::int32_t{-1});
  Put(storage, 0x2E4, std::int32_t{-1}); Put(storage, 0x2E8, std::int32_t{-1});
  Put(storage, 0x2EC, other_payer ? recipient : actor);
  return storage;
}
void Refresh(void *, bool value) { assert(value); }
void Finalize(void *) {}
bool Validate(void *, void *error) { assert(error == nullptr); return legal; }
void Destroy(void *storage) { ++destroys; Put(storage, 0, static_cast<void *>(nullptr)); }
void Cost(const void *block, const void *scope, std::int64_t *output) {
  assert(block == static_cast<std::byte *>(definition) + 0x40);
  assert(Get<void *>(static_cast<const std::byte *>(scope) - 8, 0) == definition);
  for (int index = 0; index < 10; ++index) output[index] = 0;
  if (other_cost) output[6] = 500'000;
}
bool Trigger(void *, const void *) { return true; }
bool Delta(void *, std::uintptr_t, const void *scope, std::uint32_t recipient,
    std::uint32_t actor, std::int32_t &output) noexcept {
  assert(recipient == recipient_id && actor == actor_id);
  assert(Get<void *>(static_cast<const std::byte *>(scope) - 8, 0) == definition);
  output = delta; return delta_available;
}
bool Value(void *, std::uintptr_t, const void *scope, std::uint32_t recipient,
    std::uint32_t actor, std::int64_t &output) noexcept {
  assert(recipient == recipient_id && actor == actor_id);
  assert(Get<void *>(static_cast<const std::byte *>(scope) - 8, 0) == definition);
  output = gift_value; return value_available;
}
void **Clone(const void *source, void **output) {
  ++clones;
  auto *copy = new std::array<std::byte, 0x368>;
  std::memcpy(copy->data(), source, copy->size()); *output = copy;
  return output;
}
bool Queue(void *manager, void **owned, std::uint32_t flags) {
  assert(manager == &queues && flags == 0x0E);
  assert(Get<std::uint32_t>(*owned, 0x20 + 0x2D8) == actor_id);
  assert(Get<std::uint32_t>(*owned, 0x20 + 0x2DC) == recipient_id);
  assert(Get<std::uint32_t>(*owned, 0x20 + 0x2EC) == actor_id);
  ++queues; delete static_cast<std::array<std::byte, 0x368> *>(*owned);
  *owned = nullptr; return queue_accepts;
}
void *Send(void *storage, const void *context) {
  Put(storage, 0, reinterpret_cast<std::uintptr_t>(command_vtable.data()));
  Put(storage, 0x18, secondary_vtable);
  std::memcpy(static_cast<std::byte *>(storage) + 0x20, context, 0x338);
  return storage;
}
std::int32_t NativeOpinion(void *, void *) { return gift_applied ? delta : 0; }
void *LookupModifier(void *db, std::uint32_t hash) {
  assert(db == opinion_database && hash == 0xCA82155BU);
  return opinion_definition.data();
}
void *FindOpinionGroup(void *extension, std::uint32_t toward) {
  assert(extension == opinion_extension.data() && toward == actor_id);
  return opinion_group.data();
}
std::int32_t SumOpinion(void *group, void *modifier) {
  assert(group == opinion_group.data() && modifier == opinion_definition.data());
  return delta;
}
bool OpinionSource(void *, std::uintptr_t, const CoreBindings &core,
    std::uint32_t recipient, std::uint32_t actor, GiftOpinionResult &output) noexcept {
  GiftOpinionBindings12002 b{};
  b.enabled = true; b.core = core; b.modifier_database_slot = &opinion_database;
  b.read_opinion = &NativeOpinion; b.lookup_modifier = &LookupModifier;
  b.find_group = &FindOpinionGroup; b.sum_modifier = &SumOpinion;
  b.modifier_primary_vtable = 0x1000; b.modifier_secondary_vtable = 0x1010;
  b.active_opinion_vtable = 0x2000; b.temporary_opinion_vtable = 0x2010;
  return ReadGiftOpinion12002(b, recipient, actor, output);
}
bool MainThread(void *) noexcept { return true; }
bool Human(std::uint32_t) { return false; }
std::int64_t *FactionPower(void *, std::int64_t *out) { *out = 11'000'000; return out; }
std::int64_t *FactionThreshold(void *, std::int64_t *out) { *out = 8'000'000; return out; }
std::int64_t *FactionGrowth(void *, std::int64_t *out) { *out = 100'000; return out; }
std::int32_t FactionMonths(void *) { return 20; }
bool AtWar(void *) { return false; }
bool Danger(void *, void *) { return true; }

struct Fixture {
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> local{};
  std::vector<std::byte> game_data = std::vector<std::byte>(0x36780);
  std::array<std::byte, 0xE0> player_entry{};
  std::array<void *, 1> entries{player_entry.data()};
  std::array<std::byte, 0x30> store{};
  std::array<std::byte, 8 * 0x10> slots{};
  std::array<std::array<std::byte, 0x1D8>, 2> characters{};
  std::array<std::byte, 0x2720> gift_definition{};
  std::array<std::byte, 0x108> player_extension{};
  std::array<std::byte, 0x30> faction_store{};
  std::array<std::byte, 8 * 0x10> faction_slots{};
  std::array<std::byte, 0x90> faction{};
  std::array<std::byte, 0x40> faction_type{};
  std::array<std::byte, 0x20> faction_member{};
  void *state_pointer = state.data(), *jomini_pointer = jomini.data();
  void *store_pointer = store.data();
  void *faction_store_pointer = faction_store.data();
  void *faction_fallback = nullptr;
  PlayerFactionAlertsNativeEnvironmentV1 factions{};
  PlayerFactionAlertsAccessV1 faction_access{};
  xar::game::CampaignRootContextV1 campaign{};
  FactionGiftBindingsV1 b{};
  Fixture() {
    Put(state.data(), 8, std::int32_t{53175816});
    Put(state.data(), 0x70, std::int32_t{2}); Put(state.data(), 0xA0, game_data.data());
    Put(jomini.data(), 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players.data(), 0x1F0, std::int32_t{7}); Put(local.data(), 0x70, std::int32_t{7});
    Put(game_data.data(), 0x222E8 + 0x58, entries.data());
    Put(game_data.data(), 0x222E8 + 0x64, std::int32_t{1});
    Put(player_entry.data(), 0xD8, std::int32_t{7}); Put(player_entry.data(), 0xB0, actor_id);
    Put(store.data(), 0x20, slots.data()); Put(store.data(), 0x2C, std::int32_t{8});
    Put(characters[0].data(), 0x18, actor_id); Put(characters[1].data(), 0x18, recipient_id);
    Put(slots.data(), 1 * 0x10 + 8, characters[0].data());
    Put(slots.data(), 2 * 0x10 + 8, characters[1].data());
    Put(gift_definition.data(), 0x14, definition_hash);
    const std::string_view key = "gift_interaction";
    Put(gift_definition.data() + 0x18, 0, key.data());
    Put(gift_definition.data() + 0x18, 0x10, std::uint64_t{key.size()});
    Put(gift_definition.data() + 0x18, 0x18, std::uint64_t{key.size()});
    Put(gift_definition.data(), 0x2718, std::uint8_t{1});
    definition = gift_definition.data(); database = &b; local_player = local.data();
    command_vtable[8] = reinterpret_cast<std::uintptr_t>(&Clone);
    b.enabled = true;
    b.interaction.enabled = true;
    b.interaction.core = {true, &state_pointer, &jomini_pointer, &store_pointer, &LocalPlayer};
    b.interaction.refresh = &Refresh; b.interaction.finalize = &Finalize;
    b.interaction.validate = &Validate; b.interaction.destroy = &Destroy;
    b.interaction.evaluate_cost = &Cost; b.interaction.evaluate_trigger = &Trigger;
    b.interaction.construct_send_command = &Send;
    b.interaction.send_primary_vtable = reinterpret_cast<std::uintptr_t>(command_vtable.data());
    b.interaction.send_secondary_vtable = secondary_vtable;
    b.interaction.commands.enabled = true;
    b.interaction.commands.command_manager = &queues;
    b.interaction.commands.queue_owned_command = &Queue;
    b.get_database = &Database; b.stable_hash = &Hash;
    b.lookup_definition = &Lookup; b.construct_two_role = &Construct;
    b.read_opinion_delta = &Delta; b.read_gift_value = &Value;
    b.read_opinion = &OpinionSource;
    Put(characters[0].data(), 0x1B0, player_extension.data());
    Put(player_extension.data(), 0x100, std::int64_t{20'000'000});
    Put(characters[1].data(), 0x1B0, opinion_extension.data());
    Put(opinion_definition.data(), 0, std::uintptr_t{0x1000});
    Put(opinion_definition.data(), 0x88, std::uintptr_t{0x1010});
    Put(opinion_definition.data(), 0x14, std::uint32_t{0xCA82155B});
    Put(opinion_definition.data(), 0x38, std::uint32_t{0x4744624F});
    std::memcpy(opinion_definition.data() + 0x18, "gift_opinion", 12);
    Put(opinion_definition.data(), 0x28, std::uint64_t{12});
    Put(opinion_definition.data(), 0x30, std::uint64_t{15});
    Put(opinion_active.data(), 0, std::uintptr_t{0x2000});
    Put(opinion_active.data(), 8, opinion_definition.data());
    Put(opinion_group.data(), 8, opinion_rows.data());
    Put(opinion_group.data(), 0x14, std::int32_t{0});
    Put(faction_store.data(), 0x20, faction_slots.data());
    Put(faction_store.data(), 0x2C, std::int32_t{8});
    Put(faction_slots.data(), 3 * 0x10 + 8, faction.data());
    Put(faction.data(), 0, std::uintptr_t{0x3000});
    Put(faction.data(), 0x10, std::int32_t{0x05000003});
    Put(faction.data(), 0x20, faction_type.data());
    Put(faction.data(), 0x28, std::int64_t{7'000'000});
    Put(faction.data(), 0x40, actor_id); Put(faction.data(), 0x44, recipient_id);
    Put(faction.data(), 0x48, faction_member.data());
    Put(faction.data(), 0x54, std::int32_t{1});
    Put(faction_member.data(), 8, recipient_id);
    Put(faction_member.data(), 0x0C, std::uint32_t{0x05000003});
    std::memcpy(faction_type.data() + 0x18, "liberty_faction", 15);
    Put(faction_type.data(), 0x28, std::uint64_t{15});
    Put(faction_type.data(), 0x30, std::uint64_t{15});
    factions.exact_build_admitted = true;
    factions.offline_fixture_function_overrides = true;
    factions.character_storage_slot = &store_pointer;
    factions.faction_storage_slot = &faction_store_pointer;
    factions.faction_fallback_slot = &faction_fallback;
    factions.expected_faction_vtable = 0x3000;
    factions.character_is_human = &Human; factions.power = &FactionPower;
    factions.power_threshold = &FactionThreshold;
    factions.discontent_per_month = &FactionGrowth;
    factions.months_until_max_discontent = &FactionMonths;
    factions.at_war = &AtWar; factions.dangerous = &Danger;
    faction_access.is_main_thread = &MainThread;
    campaign.status = xar::game::CampaignRootContextStatusV1::available;
    campaign.snapshot_revision = 1; campaign.date_raw = 53175816;
    campaign.player_character_id = static_cast<std::int32_t>(actor_id);
    campaign.player_character_alive = true;
    campaign.readiness.direct_landed_vassals_ready = true;
    campaign.direct_landed_vassal_character_ids = {static_cast<std::int32_t>(recipient_id)};
  }
};

struct ActionFixture {
  Fixture *fixture = nullptr;
  std::uint64_t native_revision = 1;
  bool claimed = false;
};
bool Capture(void *context, xar::game::FactionGiftMitigationObservationV1 &output) noexcept {
  auto &state = *static_cast<ActionFixture *>(context);
  auto &f = *state.fixture;
  return CaptureFactionGiftObservationV1(f.b, f.factions, f.faction_access,
      f.campaign, state.native_revision, 0x05000003, recipient_id, true, output);
}
bool ValidateAction(void *context, std::uint32_t actor, std::uint32_t recipient,
    std::string_view key, bool &valid, std::string &reason) noexcept {
  auto &f = *static_cast<ActionFixture *>(context)->fixture;
  return ValidateFactionGiftV1(f.b, actor, recipient, key, definition_hash, valid, reason);
}
bool Claim(void *context, std::string_view key) noexcept {
  auto &state = *static_cast<ActionFixture *>(context);
  assert(key == "offline-gift-once");
  if (state.claimed) return false;
  state.claimed = true; return true;
}
bool SubmitAction(void *context, std::uint32_t actor, std::uint32_t recipient,
    std::uint64_t hash) noexcept {
  auto &f = *static_cast<ActionFixture *>(context)->fixture;
  return SubmitFactionGiftV1(f.b, actor, recipient, "gift_interaction", hash);
}
} // namespace

int main(int argc, char **argv) {
  Fixture fixture;
  const auto bound = BindFactionGiftImageV1(0x140000000, kExecutableSha256);
  assert(bound.enabled);
  assert(reinterpret_cast<std::uintptr_t>(bound.construct_two_role) ==
      0x140000000 + kFactionGiftConstructTwoRoleContextRvaV1);
  assert(!BindFactionGiftImageV1(0x140000000, "1.19.0.6").enabled);
  xar::game::FactionGiftPreviewV1 preview{};
  assert(ReadFactionGiftPreviewV1(fixture.b, actor_id, recipient_id, preview));
  // Generic on-send gold is zero. Actual on-accept gift_value must survive.
  assert(preview.available && preview.interaction_legal && preview.auto_accept);
  assert(preview.gold_cost_raw == 7'500'000 && preview.opinion_delta == 35);
  bool valid = false;
  std::string reason;
  assert(ValidateFactionGiftV1(fixture.b, actor_id, recipient_id,
      "gift_interaction", definition_hash, valid, reason) && valid);
  legal = false;
  assert(ReadFactionGiftPreviewV1(fixture.b, actor_id, recipient_id, preview));
  assert(preview.available && !preview.interaction_legal);
  assert(!SubmitFactionGiftV1(fixture.b, actor_id, recipient_id,
      "gift_interaction", definition_hash) && queues == 0);
  legal = true; other_cost = true;
  assert(!ReadFactionGiftPreviewV1(fixture.b, actor_id, recipient_id, preview));
  other_cost = false; value_available = false;
  assert(!ReadFactionGiftPreviewV1(fixture.b, actor_id, recipient_id, preview));
  value_available = true; delta_available = false;
  assert(!ReadFactionGiftPreviewV1(fixture.b, actor_id, recipient_id, preview));
  delta_available = true; other_payer = true;
  assert(!ReadFactionGiftPreviewV1(fixture.b, actor_id, recipient_id, preview));
  other_payer = false;
  assert(SubmitFactionGiftV1(fixture.b, actor_id, recipient_id,
      "gift_interaction", definition_hash) && clones == 1 && queues == 1);
  queue_accepts = false;
  assert(!SubmitFactionGiftV1(fixture.b, actor_id, recipient_id,
      "gift_interaction", definition_hash) && clones == 2 && queues == 2);
  fixture.jomini[0x20] = std::byte{};
  const int before = constructs;
  assert(!ReadFactionGiftPreviewV1(fixture.b, actor_id, recipient_id, preview));
  assert(constructs == before && destroys == constructs + queues);
  fixture.jomini[0x20] = std::byte{1}; queue_accepts = true;
  ActionFixture action{&fixture};
  xar::game::FactionGiftMitigationObservationV1 observed{};
  assert(Capture(&action, observed));
  assert(observed.source_faction_present && observed.source_faction_targeting_player);
  assert(observed.source_faction_power_raw == 11'000'000 &&
      observed.source_faction_metric_scale == 100000);
  assert(observed.player_gold_raw == 20'000'000 && !observed.gift_opinion_present);
  assert(observed.recipient_is_direct_landed_vassal && observed.recipient_is_ai);
  xar::game::FactionGiftMitigationRequestV1 request{};
  request.request_id = "offline-gift-12002"; request.idempotency_key = "offline-gift-once";
  request.expected_revision = 1; request.expected_native_revision = 1;
  request.expected_date_raw = fixture.campaign.date_raw;
  request.player_character_id = actor_id; request.recipient_character_id = recipient_id;
  request.source_faction_id = 0x05000003;
  request.expected_definition_key = "gift_interaction";
  request.expected_definition_stable_hash = definition_hash;
  request.expected_gold_cost_raw = gift_value; request.expected_gold_scale = 100000;
  request.expected_opinion_delta = delta;
  request.minimum_gold_reserve_raw = 10'000'000; request.minimum_gold_reserve_scale = 100000;
  xar::ck3_11906::FactionGiftMitigationActionAccessV1 access{};
  access.context = &action; access.capture_observation = &Capture;
  access.validate_native = &ValidateAction; access.claim_idempotency_key = &Claim;
  access.submit_native = &SubmitAction;
  const xar::ck3_11906::FactionGiftMitigationNativeEnvironmentV1 environment{
      0, true, false, true};
  xar::game::FactionGiftMitigationAckV1 ack{};
  assert(ExecuteFactionGiftActionV1(environment, access, request, ack) ==
      xar::game::FactionGiftMitigationAckStatusV1::submitted_verification_pending);
  assert(ack.verification_pending && ack.pre_player_gold_raw == 20'000'000);
  xar::game::FactionGiftMitigationReceiptV1 receipt{};
  assert(xar::ck3_11906::VerifyFactionGiftMitigationReceiptV1(ack, observed, receipt) ==
      xar::game::FactionGiftMitigationReceiptStatusV1::failed);
  // Simulate the separate native command application tick, then read sources.
  gift_applied = true;
  Put(fixture.player_extension.data(), 0x100, std::int64_t{12'500'000});
  Put(opinion_group.data(), 0x14, std::int32_t{1});
  fixture.campaign.snapshot_revision = 2; action.native_revision = 2;
  assert(Capture(&action, observed) && observed.gift_opinion_present);
  assert(xar::ck3_11906::VerifyFactionGiftMitigationReceiptV1(ack, observed, receipt) ==
      xar::game::FactionGiftMitigationReceiptStatusV1::mitigated);
  assert(receipt.postcondition_verified && receipt.mitigation_applied && !receipt.threat_resolved);
  const auto json = SerializeFactionGiftAckV1(ack);
  assert(json.find("1.20.0.2") != std::string::npos);
  assert(json.find(kExecutableSha256) != std::string::npos);
  assert(json.find("1.19.0.6") == std::string::npos);
  if (argc > 1) std::ofstream(argv[1]) << json << '\n';
  if (argc > 2) std::ofstream(argv[2]) <<
      xar::ck3_11906::SerializeFactionGiftMitigationReceiptV1(receipt) << '\n';
  // Independent entity remains observable even without a targeting GUI vector.
  Put(fixture.faction_slots.data(), 3 * 0x10 + 8, static_cast<void *>(nullptr));
  assert(Capture(&action, observed) && !observed.source_faction_present);
  std::cout << "PASS 1.20 gift actual on-accept cost, final CanSend, payer, owning queue and wire; no game access\n";
}
