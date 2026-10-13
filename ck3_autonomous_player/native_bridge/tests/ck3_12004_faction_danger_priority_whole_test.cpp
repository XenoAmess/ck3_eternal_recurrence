// New danger-order worlds only; reuse qualified fixture stores and transport.
#define main QualifiedFactionAdoptedMainNotCalled
#include "ck3_12004_faction_adopted_whole_test.cpp"
#undef main
#include <utility>

namespace {
constexpr std::uint32_t danger_source_id = 0x06000004;
constexpr std::uint32_t danger_recipient_id = 0x07000004;
constexpr std::uint32_t danger_war_id = 0x08000005;
enum class PriorityScene { both_usable, dangerous_denied, dangerous_at_war };
PriorityScene priority_scene = PriorityScene::both_usable;
void *danger_faction = nullptr;
std::vector<std::uint32_t> priority_preview_order;

std::int64_t *PriorityGrowth(void *faction, std::int64_t *out) {
  *out = faction == danger_faction ? 100'000 : -100'000;
  return out;
}
std::int32_t PriorityMonths(void *faction) { return faction == danger_faction ? 20 : 0; }
bool PriorityDanger(void *faction, void *) { return faction == danger_faction; }
bool PriorityAtWar(void *faction) {
  return faction == danger_faction && priority_scene == PriorityScene::dangerous_at_war;
}
bool PriorityValidate(void *context, void *error) {
  assert(error == nullptr);
  const auto recipient = Get<std::uint32_t>(context, 0x2DC);
  priority_preview_order.push_back(recipient);
  return !(priority_scene == PriorityScene::dangerous_denied && recipient == danger_recipient_id);
}
bool PriorityDelta(void *, std::uintptr_t, const void *scope, std::uint32_t recipient,
    std::uint32_t actor, std::int32_t &output) noexcept {
  assert((recipient == recipient_id || recipient == danger_recipient_id) && actor == actor_id);
  assert(Get<void *>(static_cast<const std::byte *>(scope) - 8, 0) == definition);
  output = delta; return true;
}
bool PriorityValue(void *, std::uintptr_t, const void *scope, std::uint32_t recipient,
    std::uint32_t actor, std::int64_t &output) noexcept {
  assert((recipient == recipient_id || recipient == danger_recipient_id) && actor == actor_id);
  assert(Get<void *>(static_cast<const std::byte *>(scope) - 8, 0) == definition);
  output = gift_value; return true;
}
bool PriorityAlerts(void *opaque, const game::PlayerFactionAlertsFrameV1 &frame,
    game::PlayerFactionAlertsV1 &out) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  out = {};
  out.status = game::PlayerFactionAlertsStatusV1::available;
  out.snapshot_revision = frame.snapshot_revision;
  out.date_raw = frame.date_raw; out.player_character_id = frame.played_character_id;
  out.readiness.targeting_rows_ready = out.readiness.same_frame_ready = true;
  out.readiness.stock_dangerous_predicate_ready = true;
  for (const auto id : {source_id, danger_source_id}) {
    game::PlayerTargetingFactionV1 row{};
    if (ReadFactionEntity12004(fixture.factions, fixture.faction_access, id, row) !=
        ReadFactionEntityResult12004::available) return false;
    out.targeting_factions.push_back(std::move(row));
  }
  out.targeting_faction_count = 2;
  return true;
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const std::filesystem::path out = argv[1];
  std::filesystem::create_directories(out);
  Fixture fixture;
  RouterAdapter adapter;
  std::array<std::byte, 0x1D8> second_character{};
  std::array<std::byte, 0x90> second_faction = fixture.faction;
  std::array<std::byte, 0x20> second_member{};
  std::array<std::byte, 0x30> war_store{};
  std::array<std::byte, 8 * 0x10> war_slots{};
  std::array<std::byte, 0x10> faction_war{};
  void *war_store_pointer = war_store.data();
  danger_faction = second_faction.data();
  Put(second_character.data(), 0x18, danger_recipient_id);
  Put(second_character.data(), 0x1B0, opinion_extension.data());
  Put(fixture.slots.data(), 4 * 0x10 + 8, second_character.data());
  Put(fixture.faction_slots.data(), 4 * 0x10 + 8, second_faction.data());
  Put(second_faction.data(), 0x10, danger_source_id);
  Put(second_faction.data(), 0x44, danger_recipient_id);
  Put(second_faction.data(), 0x48, second_member.data());
  Put(second_faction.data(), 0x8C, danger_war_id);
  Put(war_store.data(), 0x20, war_slots.data());
  Put(war_store.data(), 0x2C, std::int32_t{8});
  Put(war_slots.data(), 5 * 0x10 + 8, faction_war.data());
  Put(faction_war.data(), 8, danger_war_id);
  fixture.factions.war_storage_slot = &war_store_pointer;
  Put(second_member.data(), 8, danger_recipient_id);
  Put(second_member.data(), 0x0C, danger_source_id);
  fixture.campaign.direct_landed_vassal_character_ids.push_back(
      static_cast<std::int32_t>(danger_recipient_id));
  fixture.b.interaction.validate = &PriorityValidate;
  fixture.b.read_opinion_delta = &PriorityDelta;
  fixture.b.read_gift_value = &PriorityValue;
  fixture.factions.discontent_per_month = &PriorityGrowth;
  fixture.factions.months_until_max_discontent = &PriorityMonths;
  fixture.factions.dangerous = &PriorityDanger;
  fixture.factions.at_war = &PriorityAtWar;
  ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  mailbox.offline_fixture = true;
  mailbox.permitted_executor_quattuortrigintary = &ExecuteFactionGiftPrivateMailbox12004;
  FactionGiftPrivateFixtureBindings12004 bindings{};
  bindings.factions = fixture.factions; bindings.gift = fixture.b;
  bindings.context = &fixture; bindings.read_campaign = &RootSource; bindings.read_alerts = &PriorityAlerts;
  const std::array scenes{
      std::pair{PriorityScene::both_usable, "watch-before-dangerous-both-usable"},
      std::pair{PriorityScene::dangerous_denied, "dangerous-denied-watch-usable"},
      std::pair{PriorityScene::dangerous_at_war, "dangerous-at-war-watch-usable"}};
  const auto queues_before = queues;
  for (const auto &[scene, name] : scenes) {
    priority_scene = scene; priority_preview_order.clear();
    game::PlayerFactionAlertsV1 alerts;
    game::PlayerFactionAlertsFrameV1 frame{};
    frame.snapshot_revision = 1; frame.date_raw = adapter.snapshot.date_raw;
    frame.played_character_id = actor_id;
    CheckRouter(PriorityAlerts(&fixture, frame, alerts));
    CheckRouter(!alerts.targeting_factions[0].dangerous_by_stock_rule &&
        alerts.targeting_factions[1].dangerous_by_stock_rule);
    std::uint32_t raw_source = 0, raw_recipient = 0;
    CheckRouter(SelectFactionGiftPrivateCandidate12004(fixture.campaign, alerts,
        raw_source, raw_recipient) && raw_source == source_id && raw_recipient == recipient_id);
    FactionGiftPrivateState12004 state;
    std::string wire, failure;
    CheckRouter(HandleFactionGiftPrivate12004(adapter, mailbox, adapter.snapshot, 1,
        ck3_11906::kFactionGiftPrivateQueryStepV1, FramePayload(1) + "}",
        name, state, wire, failure, &bindings));
    const auto expected = scene == PriorityScene::both_usable ? danger_recipient_id : recipient_id;
    const auto expected_source = scene == PriorityScene::both_usable ? danger_source_id : source_id;
    CheckRouter(state.last_query && state.last_query->recipient_character_id == expected &&
        state.last_query->queried_source_faction_id == expected_source);
    const auto expected_order = scene == PriorityScene::both_usable
        ? std::vector<std::uint32_t>{danger_recipient_id}
        : scene == PriorityScene::dangerous_denied
            ? std::vector<std::uint32_t>{danger_recipient_id, recipient_id}
            : std::vector<std::uint32_t>{recipient_id};
    CheckRouter(priority_preview_order == expected_order);
    CheckRouter(wire.find("\"status\":\"preview_ready\"") != std::string::npos);
    CheckRouter(!state.pending_ack && !state.action_may_have_submitted && queues == queues_before);
    WriteWire(out, std::string(name) + ".command-result.json", wire);
  }
  CheckRouter(constructs == destroys);
  std::ofstream(out / "NATIVE-DANGER-PRIORITY-RECEIPT.json")
      << "{\"status\":\"GREEN_FIXTURE_ONLY\",\"live\":false,\"new_worlds\":3,"
         "\"original_matrix_runs\":0,\"command_queue_calls\":0,\"checks\":"
      << router_checks << "}\n";
  return 0;
}
