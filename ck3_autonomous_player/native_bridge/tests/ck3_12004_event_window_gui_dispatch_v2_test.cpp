#include "xar_bridge/ck3_12002_event_window_context_v2_query.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "support/event_window_owned_fixture_v2.hpp"
#include <atomic>
#include <cstdlib>
#include <exception>
#include <filesystem>
#include <fstream>
#include <thread>

namespace game = xar::game;
namespace build = xar::ck3_12002;
namespace mailbox = xar::ck3_11906;
namespace current = xar::ck3_12004;
namespace {
unsigned checks = 0;
void Check(bool value, const char *why) { ++checks; if (!value) throw std::runtime_error(why); }
unsigned gate_calls = 0, bad_gate_arguments = 0, dummy_executor_calls = 0;
const void *expected_owner = nullptr;
bool GuiGate(const void *owner, const void *reason) {
  ++gate_calls;
  if (owner != expected_owner || reason != nullptr) ++bad_gate_arguments;
  return owner == expected_owner && reason == nullptr;
}
bool ReadOwnedPrefix(const build::EventWindowBindings &, game::Snapshot &out) noexcept {
  out = {}; out.date_raw = 741221; out.paused = true; out.map_ready = true;
  out.player_id = 0; out.has_played_character = true;
  out.played_character_id = kCharacterId; out.played_character_alive = true;
  out.has_active_event = true; out.active_event_instance_id = kEventId;
  return true;
}
class OwnedAdapter final : public game::GameAdapter {
public:
  mutable unsigned snapshot_calls = 0;
  const game::AdapterDescriptor &descriptor() const noexcept override {
    static constexpr std::array<std::string_view, 1> capabilities{"game.state.snapshot"};
    static const game::AdapterDescriptor descriptor{
        "ck3-1.20.0.4-msvc-x64", "1.20.0.4", current::kExecutableSha256,
        "owned-event-gui-request-dispatch-fixture", capabilities};
    return descriptor;
  }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    ++snapshot_calls; build::EventWindowBindings unused{}; return ReadOwnedPrefix(unused, out);
  }
#define OFF(Type, Name, Args) game::Type Name Args const noexcept override { std::abort(); }
  OFF(PauseSubmitResult, submit_pause_map, (game::Snapshot *))
  OFF(ResumeSubmitResult, submit_resume_map, (game::Snapshot *))
  bool submit_set_speed(std::int32_t) const noexcept override { std::abort(); }
  OFF(SelectEventOptionResult, submit_select_event_option, (std::int32_t))
  OFF(SaveCheckpointResult, submit_save_checkpoint, ())
  OFF(ReplyPendingInteractionResult, submit_reply_to_pending_interaction, (game::PendingInteractionReply))
  OFF(RaiseTroopsResult, submit_raise_troops_default, ())
  OFF(MoveArmyResult, submit_move_army, (std::int32_t, std::int32_t))
  OFF(PreviewMoveArmyResult, preview_move_army, (std::int32_t, std::int32_t))
  OFF(DisbandArmyResult, submit_disband_army, (std::int32_t))
  OFF(SplitArmyHalfResult, submit_split_army_half, (std::int32_t))
  OFF(MergeArmiesResult, submit_merge_armies, (std::int32_t, std::int32_t))
  OFF(StartAssaultResult, submit_start_assault, (std::int32_t))
  OFF(StopAssaultResult, submit_stop_assault, (std::int32_t))
  bool read_declarable_wars(std::vector<game::DeclarableWarSnapshot> &) const noexcept override { std::abort(); }
  OFF(ReadDeclarableWarsResult, read_declarable_wars_for_target, (std::int32_t, std::vector<game::DeclarableWarSnapshot> &))
  OFF(DeclareWarResult, submit_declare_war, (const game::DeclarableWarSnapshot &))
  OFF(ReadArrangeMarriageChoicesResult, read_arrange_marriage_choices, (std::vector<game::ArrangeMarriageChoice> &, game::ArrangeMarriageQueryDiagnostics &))
  OFF(ArrangeMarriageResult, submit_arrange_marriage, (const game::ArrangeMarriageChoice &))
  OFF(EnforceDemandsResult, submit_enforce_demands, (std::int32_t))
  OFF(ReadArmyStrengthsResult, read_army_strengths, (std::vector<game::ArmyStrengthSnapshot> &))
  OFF(ReadCombatSimulationInputsResult, read_combat_simulation_inputs, (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &))
  OFF(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3, (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &))
  OFF(ReadWarTerminationOptionsResult, read_war_termination_options, (std::int32_t, game::WarTerminationOptionsSnapshot &))
  OFF(ReadWarTerminationTermsResult, read_war_termination_terms, (std::int32_t, game::WarTerminationTermsSnapshot &))
  OFF(ReadWarTerminationExitTermsResult, read_war_termination_exit_terms, (std::int32_t, game::WarTerminationExitTermsSnapshot &))
  OFF(SurrenderWarResult, submit_surrender_war, (std::int32_t))
  OFF(OfferWhitePeaceResult, submit_offer_white_peace, (std::int32_t))
#undef OFF
};
bool DummyExecutor(void *, const mailbox::MainThreadExecutionStampV1 &) noexcept { ++dummy_executor_calls; return false; }
struct OwnedEnvelope {
  OwnedAdapter game;
  mailbox::MainThreadQueryMailboxV1 slot;
  build::QueryMailboxEnvelope envelope;
  OwnedEnvelope() {
    const auto thread = GetCurrentThreadId();
    envelope.game = &game; envelope.mailbox = &slot;
    envelope.ticket.sequence = 1; envelope.expected_snapshot_revision = kRevision;
    build::EventWindowBindings unused{}; ReadOwnedPrefix(unused, envelope.expected_snapshot);
    slot.state.store(mailbox::MainThreadQueryMailboxStateV1::executing);
    slot.published_sequence.store(1); slot.owner_thread_id.store(thread);
    slot.executor.store(&DummyExecutor); slot.executor_context = &envelope;
    mailbox::MainThreadExecutionStampV1 stamp{};
    stamp.pump_epoch = 1; stamp.thread_id = thread; stamp.paused = true;
    stamp.date_raw = envelope.expected_snapshot.date_raw;
    stamp.tls_initialized = 1; stamp.tls_main_thread_marker = 1;
    stamp.tls_context = 1; stamp.jomini_state = 1; stamp.game_state = 1;
    Check(build::EnterQueryMailbox(envelope, stamp, &DummyExecutor), "actual EnterQueryMailbox rejected owned context");
    Check(build::IsQueryOwningThread(&envelope), "actual owning-thread predicate rejected current owner");
  }
};
struct ParseCase { const char *name; const char *suffix; bool accepted; bool version2; };
std::string Request(std::string_view suffix) {
  return "{\"type\":\"execute_step\",\"request_id\":\"owned-gui-v2\",\"step\":\"query-current-event-window-context-v1\",\"expected_revision\":17,\"event_instance_id\":" +
      std::to_string(kEventId) + std::string(suffix) + "}";
}
void ParserCases(const std::filesystem::path &out) {
  const std::array<ParseCase, 21> cases{{
      {"absent", "", true, false}, {"integer2", ",\"gui_observation_version\":2", true, true},
      {"whitespace2", ",\"gui_observation_version\" : \t2 \r\n", true, true},
      {"bool_true", ",\"gui_observation_version\":true", false, false},
      {"bool_false", ",\"gui_observation_version\":false", false, false},
      {"float", ",\"gui_observation_version\":2.0", false, false},
      {"exponent", ",\"gui_observation_version\":2e0", false, false},
      {"string", ",\"gui_observation_version\":\"2\"", false, false},
      {"null", ",\"gui_observation_version\":null", false, false},
      {"zero", ",\"gui_observation_version\":0", false, false},
      {"one", ",\"gui_observation_version\":1", false, false},
      {"three", ",\"gui_observation_version\":3", false, false},
      {"negative", ",\"gui_observation_version\":-2", false, false},
      {"array", ",\"gui_observation_version\":[]", false, false},
      {"object", ",\"gui_observation_version\":{}", false, false},
      {"leading_zero_token", ",\"gui_observation_version\":02", false, false},
      {"plus_token", ",\"gui_observation_version\":+2", false, false},
      {"duplicate", ",\"gui_observation_version\":2,\"gui_observation_version\":2", false, false},
      {"quoted_mention", ",\"note\":\"gui_observation_version\"", true, false},
      {"nested_mention", ",\"nested\":{\"gui_observation_version\":null}", true, false},
      {"nested_before_root", ",\"nested\":{\"gui_observation_version\":true},\"gui_observation_version\":2", true, true},
  }};
  std::ofstream requests(out / "request-cases.ndjson", std::ios::binary);
  for (const auto &test : cases) {
    const auto raw = Request(test.suffix);
    auto version = build::EventWindowGuiRequestVersionV2::gui_v2;
    const bool result = build::ParseEventWindowGuiRequestVersionV2(raw, version);
    Check(result == test.accepted, test.name);
    Check((version == build::EventWindowGuiRequestVersionV2::gui_v2) == test.version2, "parser did not reset/select exact version");
    Check(gate_calls == 0, "request parsing invoked GUI gate");
    requests << raw << '\n';
    std::cout << "{\"case\":\"" << test.name << "\",\"parser_accepted\":" << (result ? "true" : "false")
        << ",\"version2\":" << (test.version2 ? "true" : "false") << ",\"gate_calls\":0}\n";
  }
  Check(requests.good(), "raw request artifacts unavailable");
}
void DispatchCase(const std::filesystem::path &out, const char *name, bool version2, bool nonowner) {
  Fixture fixture; fixture.InitializeOption(0, 0, true, false);
  fixture.bindings.read_observation_prefix = &ReadOwnedPrefix;
  Store<void *>(fixture.option_items.data(), 0x88, nullptr);
  Store<std::int32_t>(fixture.option_items.data(), 0x90, 0);
  Store<std::int32_t>(fixture.option_items.data(), 0x94, 0);
  expected_owner = fixture.window.data() + 0xB8;
  gate_calls = 0; bad_gate_arguments = 0;
  build::EventWindowGuiBindingsV2 bindings{fixture.bindings, &GuiGate};
  OwnedEnvelope owned;
  build::EventWindowGuiRequestVersionV2 version{};
  const auto raw = Request(version2 ? ",\"gui_observation_version\":2" : "");
  Check(build::ParseEventWindowGuiRequestVersionV2(raw, version), "actual request helper rejected dispatch case");
  std::uint64_t revision = 0; std::int32_t event = -1;
  Check(build::ParseEventWindowContextRequestV1(raw, revision, event) && revision == kRevision && event == kEventId,
      "actual original event request fields rejected");
  game::EventWindowContextV1 presentation;
  game::EventWindowContextV2 gui;
  auto result = game::ReadEventWindowContextResultV1::unavailable;
  bool child_owns = true; std::exception_ptr failure;
  const auto dispatch = [&] {
    result = build::ReadVersionedEventWindowInQueryV2(version, bindings, owned.envelope, event, presentation, gui);
  };
  if (nonowner) {
    std::thread worker([&] { try { child_owns = build::IsQueryOwningThread(&owned.envelope); dispatch(); } catch (...) { failure = std::current_exception(); } });
    worker.join(); if (failure != nullptr) std::rethrow_exception(failure);
    Check(!child_owns, "real mailbox predicate accepted nonowner thread");
  } else dispatch();
  Check(result == game::ReadEventWindowContextResultV1::available, "actual versioned collector unavailable");
  Check(build::FinishQueryMailbox(owned.envelope) && owned.game.snapshot_calls == 2, "actual finish did not preserve owned frame");
  Check(bad_gate_arguments == 0 && dummy_executor_calls == 0, "unexpected native argument or executor invocation");
  std::string body;
  if (!version2) {
    Check(gate_calls == 0 && gui.gui_observations.empty(), "v1 dispatch read new GUI gate");
    body = build::SerializeEventWindowContextV1(presentation);
    Check(body.find("\"schema_version\":1") != std::string::npos && body.find("gui_availability") == std::string::npos,
        "default request did not retain v1 wire");
  } else {
    Check(gui.presentation == presentation && gui.gui_observations.size() == 1, "dispatch did not copy v2 presentation");
    const auto &observation = gui.gui_observations.front().gui_availability;
    if (nonowner) {
      const auto *value = std::get_if<game::EventGuiAvailabilityUnobservedV2>(&observation);
      Check(gate_calls == 0 && value != nullptr && value->reason == game::EventGuiAvailabilityFailureV2::native_read_unavailable,
          "nonowner dispatch invoked gate or changed typed failure");
    } else {
      const auto *value = std::get_if<game::EventGuiAvailabilityObservedV2>(&observation);
      Check(gate_calls == 1 && value != nullptr && value->is_valid, "v2 dispatch did not observe actual owned gate once");
    }
    body = build::SerializeEventWindowContextV2(gui);
    Check(body.find("current-event-window-context-v2") != std::string::npos && body.find("\"schema_version\":2") != std::string::npos,
        "integer2 dispatch did not render v2 wire");
  }
  Check(!body.empty(), "versioned serializer returned empty");
  std::ofstream file(out / (std::string(name) + ".inner-result.json"), std::ios::binary); file << body;
  Check(file.good(), "actual serializer artifact write failed");
  std::cout << "{\"dispatch_case\":\"" << name << "\",\"version2\":" << (version2 ? "true" : "false")
      << ",\"nonowner_thread\":" << (nonowner ? "true" : "false") << ",\"gate_calls\":" << gate_calls
      << ",\"actual_Enter_and_Finish\":true,\"snapshot_calls\":" << owned.game.snapshot_calls << "}\n";
}
}
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "fresh output root required");
    const auto out = std::filesystem::path(argv[1]) / ("run-" + std::to_string(GetCurrentProcessId()) + "-" + std::to_string(GetTickCount64()));
    Check(!std::filesystem::exists(out) && std::filesystem::create_directories(out), "fresh output required");
    ParserCases(out);
    DispatchCase(out, "default-v1-no-gui", false, false);
    DispatchCase(out, "integer2-v2-owning", true, false);
    DispatchCase(out, "integer2-v2-nonowner", true, true);
    std::cout << "{\"complete\":true,\"parser_cases\":21,\"dispatch_cases\":3,\"checks\":" << checks
        << ",\"physical_submit_pump_executed\":false,\"complete_Bridge_dispatch_executed\":false,\"game_calls\":0,\"model_calls\":0}\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
