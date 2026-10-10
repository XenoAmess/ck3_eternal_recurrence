// Reuse qualified stores, adapter and transport helpers, without running the
// old matrix or its producer. Only the new continuation worlds run below.
#define main QualifiedFactionAdoptedMainNotCalled
#include "ck3_12004_faction_adopted_whole_test.cpp"
#undef main
#include <utility>

namespace {
constexpr std::uint32_t later_recipient_id = 0x07000004;
enum class ContinuationScene { native_denied, already_gifted, human, all_denied };
ContinuationScene continuation_scene = ContinuationScene::native_denied;
std::vector<std::uint32_t> preview_order;

bool ContinueValidate(void *context, void *error) {
  assert(error == nullptr);
  const auto recipient = Get<std::uint32_t>(context, 0x2DC);
  preview_order.push_back(recipient);
  return continuation_scene != ContinuationScene::all_denied &&
      !(continuation_scene == ContinuationScene::native_denied && recipient == recipient_id);
}
bool ContinueHuman(std::uint32_t recipient) {
  return continuation_scene == ContinuationScene::human && recipient == recipient_id;
}
bool ContinueDelta(void *, std::uintptr_t, const void *scope, std::uint32_t recipient,
    std::uint32_t actor, std::int32_t &output) noexcept {
  assert((recipient == recipient_id || recipient == later_recipient_id) && actor == actor_id);
  assert(Get<void *>(static_cast<const std::byte *>(scope) - 8, 0) == definition);
  output = delta; return true;
}
bool ContinueValue(void *, std::uintptr_t, const void *scope, std::uint32_t recipient,
    std::uint32_t actor, std::int64_t &output) noexcept {
  assert((recipient == recipient_id || recipient == later_recipient_id) && actor == actor_id);
  assert(Get<void *>(static_cast<const std::byte *>(scope) - 8, 0) == definition);
  output = gift_value; return true;
}
bool ContinueOpinion(void *opaque, std::uintptr_t module, const CoreBindings &core,
    std::uint32_t recipient, std::uint32_t actor, GiftOpinionResult &output) noexcept {
  // Authored per-recipient stores still flow through ReadGiftOpinion12004.
  gift_applied = continuation_scene == ContinuationScene::already_gifted && recipient == recipient_id;
  Put(opinion_group.data(), 0x14, std::int32_t{gift_applied ? 1 : 0});
  return OpinionSource(opaque, module, core, recipient, actor, output);
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const std::filesystem::path out = argv[1];
  std::filesystem::create_directories(out);
  Fixture fixture;
  RouterAdapter adapter;
  std::array<std::byte, 0x1D8> later_character{};
  std::array<std::byte, 0x40> members{};
  Put(later_character.data(), 0x18, later_recipient_id);
  Put(later_character.data(), 0x1B0, opinion_extension.data());
  Put(fixture.slots.data(), 4 * 0x10 + 8, later_character.data());
  Put(members.data(), 8, recipient_id);
  Put(members.data(), 0x0C, source_id);
  Put(members.data(), 0x20 + 8, later_recipient_id);
  Put(members.data(), 0x20 + 0x0C, source_id);
  Put(fixture.faction.data(), 0x48, members.data());
  Put(fixture.faction.data(), 0x54, std::int32_t{2});
  fixture.campaign.direct_landed_vassal_character_ids.push_back(
      static_cast<std::int32_t>(later_recipient_id));
  fixture.b.interaction.validate = &ContinueValidate;
  fixture.b.read_opinion_delta = &ContinueDelta;
  fixture.b.read_gift_value = &ContinueValue;
  fixture.b.read_opinion = &ContinueOpinion;
  fixture.factions.character_is_human = &ContinueHuman;
  ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  mailbox.offline_fixture = true;
  mailbox.permitted_executor_quattuortrigintary = &ExecuteFactionGiftPrivateMailbox12004;
  FactionGiftPrivateFixtureBindings12004 bindings{};
  bindings.factions = fixture.factions; bindings.gift = fixture.b;
  bindings.context = &fixture; bindings.read_campaign = &RootSource; bindings.read_alerts = &AlertSource;
  const std::array scenes{
      std::pair{ContinuationScene::native_denied, "first-native-denied"},
      std::pair{ContinuationScene::already_gifted, "first-already-gifted"},
      std::pair{ContinuationScene::human, "first-human"},
      std::pair{ContinuationScene::all_denied, "all-native-denied"}};
  const auto queues_before = queues;
  for (const auto &[scene, name] : scenes) {
    continuation_scene = scene; preview_order.clear();
    FactionGiftPrivateState12004 state;
    std::string wire, failure;
    CheckRouter(HandleFactionGiftPrivate12004(adapter, mailbox, adapter.snapshot, 1,
        ck3_11906::kFactionGiftPrivateQueryStepV1, FramePayload(1) + "}",
        "faction-candidate-continuation-first", state, wire, failure, &bindings));
    CheckRouter(preview_order == std::vector<std::uint32_t>{recipient_id, later_recipient_id});
    CheckRouter(state.last_query && state.last_query->recipient_character_id == later_recipient_id);
    CheckRouter(state.last_query->snapshot_revision == 1 &&
        state.last_query->native_snapshot_revision == 1 &&
        state.last_query->observed_date_raw == 53175816);
    CheckRouter(wire.find(scene == ContinuationScene::all_denied
        ? "\"status\":\"no_legal_candidate\"" : "\"status\":\"preview_ready\"") != std::string::npos);
    CheckRouter(!state.pending_ack && !state.action_may_have_submitted && queues == queues_before);
    WriteWire(out, std::string(name) + ".command-result.json", wire);
  }
  CheckRouter(constructs == destroys);
  std::ofstream(out / "NATIVE-CONTINUATION-RECEIPT.json")
      << "{\"status\":\"GREEN_FIXTURE_ONLY\",\"live\":false,\"new_worlds\":4,"
         "\"previewed_recipients_per_world\":2,\"original_matrix_runs\":0,"
         "\"command_queue_calls\":0,\"game_sdk_operations\":0,\"checks\":"
      << router_checks << "}\n";
  return 0;
}
