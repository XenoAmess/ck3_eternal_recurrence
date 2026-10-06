// FIRST_NOTRUN: seven complete actual mailbox/serializer/renderer packets.
// Reuse the already-frozen memory helpers, without invoking its older tests.
#define main TargetTenetLibraryFixtureMain
#include "religion_doctrine12002_tenet_rows_test.cpp"
#undef main
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/religion_doctrine12002_tenet_rows_mailbox.hpp"
#include <windows.h>

#include <atomic>
#include <chrono>
#include <cstdlib>
#include <stdexcept>
#include <thread>

namespace xar::ck3_12002 {
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept { return adapter; }
}
// Same standalone-renderer linkage as the existing .3 confession fixture;
// these image factories are unreachable in a fixture-owned-memory query.
namespace xar::game {
Ck3_12002AdapterBindings BindCk3_12002AdapterImage(std::uintptr_t, std::string_view) noexcept { std::abort(); }
const AdapterDescriptor &Ck3_12002AdapterDescriptor() noexcept { std::abort(); }
std::unique_ptr<GameAdapter> CreateCk3_12003AdapterFromBindings(Ck3_12003AdapterBindings) noexcept { std::abort(); }
}
namespace {
namespace game = xar::game;
namespace api = xar::ck3_11906;
namespace target = xar::ck3_12003::religion::target_tenet;
int mailbox_checks = 0;
void Assert(bool condition, const char *message) {
  ++mailbox_checks;
  if (!condition) throw std::runtime_error(message);
}
class FrameAdapter final : public game::GameAdapter {
public:
  game::Snapshot frame{};
  const DWORD owner = GetCurrentThreadId();
  mutable unsigned reads = 0;
  game::AdapterDescriptor identity{xar::ck3_12003::kAdapterId, xar::ck3_12003::kGameVersion,
      xar::ck3_12003::kExecutableSha256, "target-rite-tenet-fixture", {}};
  const game::AdapterDescriptor &descriptor() const noexcept override { return identity; }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    if (GetCurrentThreadId() != owner) return false;
    out = frame; ++reads; return true;
  }
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override { return {}; }
  game::PreviewMoveArmyResult preview_move_army(std::int32_t, std::int32_t) const noexcept override { return {}; }
  bool read_declarable_wars(std::vector<game::DeclarableWarSnapshot> &) const noexcept override { return false; }
#define ABSENT(Result, Name, Params) game::Result Name Params const noexcept override { return game::Result::unavailable; }
  ABSENT(PauseSubmitResult, submit_pause_map, (game::Snapshot *))
  ABSENT(ResumeSubmitResult, submit_resume_map, (game::Snapshot *))
  ABSENT(SelectEventOptionResult, submit_select_event_option, (std::int32_t))
  ABSENT(ReplyPendingInteractionResult, submit_reply_to_pending_interaction, (game::PendingInteractionReply))
  ABSENT(RaiseTroopsResult, submit_raise_troops_default, ())
  ABSENT(MoveArmyResult, submit_move_army, (std::int32_t, std::int32_t))
  ABSENT(DisbandArmyResult, submit_disband_army, (std::int32_t))
  ABSENT(SplitArmyHalfResult, submit_split_army_half, (std::int32_t))
  ABSENT(MergeArmiesResult, submit_merge_armies, (std::int32_t, std::int32_t))
  ABSENT(StartAssaultResult, submit_start_assault, (std::int32_t))
  ABSENT(StopAssaultResult, submit_stop_assault, (std::int32_t))
  ABSENT(ReadDeclarableWarsResult, read_declarable_wars_for_target, (std::int32_t, std::vector<game::DeclarableWarSnapshot> &))
  ABSENT(DeclareWarResult, submit_declare_war, (const game::DeclarableWarSnapshot &))
  ABSENT(ReadArrangeMarriageChoicesResult, read_arrange_marriage_choices, (std::vector<game::ArrangeMarriageChoice> &, game::ArrangeMarriageQueryDiagnostics &))
  ABSENT(ArrangeMarriageResult, submit_arrange_marriage, (const game::ArrangeMarriageChoice &))
  ABSENT(EnforceDemandsResult, submit_enforce_demands, (std::int32_t))
  ABSENT(SurrenderWarResult, submit_surrender_war, (std::int32_t))
  ABSENT(OfferWhitePeaceResult, submit_offer_white_peace, (std::int32_t))
  ABSENT(ReadArmyStrengthsResult, read_army_strengths, (std::vector<game::ArmyStrengthSnapshot> &))
  ABSENT(ReadCombatSimulationInputsResult, read_combat_simulation_inputs, (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &))
  ABSENT(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3, (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &))
  ABSENT(ReadWarTerminationOptionsResult, read_war_termination_options, (std::int32_t, game::WarTerminationOptionsSnapshot &))
  ABSENT(ReadWarTerminationTermsResult, read_war_termination_terms, (std::int32_t, game::WarTerminationTermsSnapshot &))
  ABSENT(ReadWarTerminationExitTermsResult, read_war_termination_exit_terms, (std::int32_t, game::WarTerminationExitTermsSnapshot &))
#undef ABSENT
};

struct ComparisonFixture : Fixture {
  Bytes<0x800> target_rite{};
  Bytes<0x30> rite_storage{};
  Bytes<0x40> rite_slots{};
  Bytes<0xF00> database{};
  std::array<const void *, 5> loaded{};
  std::array<const void *, 2> actor_core{definitions[4].data(), definitions[4].data()};
  std::array<const void *, 2> target_core{definitions[2].data(), definitions[2].data()};
  void *rite_storage_ptr = rite_storage.data(), *database_ptr = database.data();
  std::uint32_t target_id = 0x85000003U;
  ComparisonFixture() {
    Put(rite, 0x0C, std::uint32_t{0x52697465});
    Put(main_rite, 0x0C, std::uint32_t{0x52697465});
    Put(target_rite, 0x0C, std::uint32_t{0x52697465});
    Put(target_rite, 8, target_id);
    Put(target_rite, r::kRiteFaithIdOffset, faith_id);
    Set(rite, d::kRiteCoreTenetsOffset, actor_core.data(), 2);
    Set(target_rite, d::kRiteCoreTenetsOffset, target_core.data(), 2);
    Put(rite_storage, 0x20, rite_slots.data());
    Put(rite_storage, 0x2C, std::uint32_t{4});
    Put(rite_slots, 8, rite.data());
    Put(rite_slots, 2 * 0x10 + 8, main_rite.data());
    Put(rite_slots, 3 * 0x10 + 8, target_rite.data());
    for (std::size_t i = 0; i < loaded.size(); ++i) loaded[i] = definitions[i].data();
    Put(database, 0xEF0, loaded.data());
    Put(database, 0xEF8, std::int32_t{5}); Put(database, 0xEFC, std::int32_t{5});
  }
};
ComparisonFixture *comparison_fixture = nullptr;
std::uint8_t ComparisonState(void *rite, const void *definition) {
  if (rite == comparison_fixture->target_rite.data()) {
    if (definition == comparison_fixture->definitions[0].data()) return 2;
    if (definition == comparison_fixture->definitions[1].data()) return 3;
  }
  return State(rite, definition);
}
void *tls_context = nullptr;
void *__fastcall FixtureTls() noexcept { return tls_context; }
struct Pump {
  Bytes<0x28> tls{};
  std::uint8_t initialized = 1;
  std::uintptr_t unused_rng = 0;
  Pump(Fixture &fixture, api::MainThreadQueryMailboxV1 &mailbox) {
    tls[0x20] = std::byte{1}; tls_context = tls.data();
    mailbox.global_rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&unused_rng);
    mailbox.jomini_state_slot = reinterpret_cast<std::uintptr_t>(&fixture.jomini_ptr);
    mailbox.game_state_slot = reinterpret_cast<std::uintptr_t>(&fixture.state_ptr);
    mailbox.tls_initialized_flag = reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter = &FixtureTls;
    mailbox.executor_submission_enabled = true;
    mailbox.permitted_executor = &c::ExecutePlayerReligionTenetsMailbox12002;
    mailbox.iat_hook_installed = true;
    mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (unsigned i = 0; i < 2; ++i)
      api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};

target::Comparison Query(ComparisonFixture &fixture, FrameAdapter &adapter,
    const std::filesystem::path &directory, const char *filename,
    std::optional<std::uint32_t> target_id, std::string_view key) {
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(fixture, mailbox);
  c::PlayerReligionTenetsMailboxContext12002 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = 701;
  query.bindings = Bind(fixture);
  query.tenet_bindings = {true, &State};
  comparison_fixture = &fixture;
  query.target_rite_id = target_id; query.tenet_key = key;
  query.comparison_bindings = {query.bindings, &fixture.rite_storage_ptr,
      &fixture.database_ptr, &ComparisonState};
  adapter.reads = 0;
  std::atomic<bool> done{false};
  bool result = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    result = c::RunPlayerReligionTenetsMailbox12002(query,
        "target-rite-tenet-fixture", serialized, failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Assert(result && drained && failure.empty() && query.completed && query.envelope.frame_stable,
      "actual queue executor and serializer close");
  Assert(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "actual mailbox reclaimed");
  Assert(query.observation.available && query.observation.current_rite->core_tenets.size() == 2,
      "current result independently preserved including duplicates");
  Assert(query.observation.capture_epoch == query.envelope.execution_stamp.pump_epoch &&
      query.observation.capture_epoch != 701, "actual owner epoch differs from published revision");
  if (target_id) {
    Assert(query.comparison.capture_epoch == query.observation.capture_epoch &&
        query.comparison.played_character_id == static_cast<std::uint32_t>(Fixture::character_id) &&
        query.comparison.date_raw == 53175816, "comparison actual owner metadata");
  } else {
    const auto old_dto = d::SerializeTenetRows12002(query.observation);
    Assert(serialized.find("\"player_religion_tenets\":" + old_dto + "}}") != std::string::npos &&
        serialized.find("target_rite_tenet_comparison") == std::string::npos,
        "old no-pair DTO bytes unchanged by composition");
  }
  const auto rendered = game::RenderCrozierBuildIdentity(std::move(serialized), adapter.descriptor());
  Assert(rendered.find("\"game_version\":\"1.20.0.3\"") != std::string::npos &&
      rendered.find(xar::ck3_12003::kExecutableSha256) != std::string::npos,
      "actual reviewed .3 renderer carries complete wire");
  std::ofstream(directory / filename, std::ios::binary) << rendered << '\n';
  return query.comparison;
}
void Available(const target::Comparison &out, std::uint32_t target_id,
    std::uint8_t actor_status, std::uint8_t target_status, bool same) {
  Assert(out.available && out.named_comparison_ready && out.failure == target::Failure::none,
      "fully observed named comparison");
  Assert(out.actor_rite && out.target_rite && out.same_rite == same && out.same_faith == true,
      "actual Rite/Faith equality");
  const auto &a = *out.actor_rite; const auto &t = *out.target_rite;
  Assert(a.rite_id == 0 && t.rite_id == target_id &&
      a.faith_id == Fixture::faith_id && t.faith_id == Fixture::faith_id &&
      a.faith_main_rite_id == Fixture::main_id && t.faith_main_rite_id == Fixture::main_id,
      "full-generation identity and actual Faith main");
  Assert(a.core_tenet_keys == std::vector<std::string>{"tenet_4", "tenet_4"} &&
      t.core_tenet_keys == (same ? a.core_tenet_keys : std::vector<std::string>{"tenet_2", "tenet_2"}) &&
      a.faith_main_core_tenet_keys == std::vector<std::string>{"tenet_3"} &&
      t.faith_main_core_tenet_keys == std::vector<std::string>{"tenet_3"},
      "four independently copied actual Core collections preserve occurrences");
  Assert(a.core_tenets_complete && a.faith_main_core_tenets_complete &&
      t.core_tenets_complete && t.faith_main_core_tenets_complete &&
      !a.current_is_main && !t.current_is_main, "each scope provenance complete");
  Assert(a.named_tenet_status == actor_status && t.named_tenet_status == target_status &&
      a.named_tenet_core_member == same && t.named_tenet_core_member == same &&
      !a.named_tenet_faith_main_core_member && !t.named_tenet_faith_main_core_member,
      "zero is valid and statuses independent of literal membership");
}
void Unavailable(const target::Comparison &out, target::Failure reason) {
  Assert(!out.available && !out.named_comparison_ready && out.failure == reason &&
      !out.actor_rite && !out.target_rite && !out.same_rite && !out.same_faith,
      "failure leaves all dependent scopes null");
}
void RequestCases() {
  std::optional<std::uint32_t> id; std::string key;
  Assert(c::ParsePlayerReligionTenetsComparisonRequest12003("{}", id, key) && !id && key.empty(), "old request");
  Assert(c::ParsePlayerReligionTenetsComparisonRequest12003(
      "{\"target_rite_id\":0,\"tenet_key\":\"tenet_4\"}", id, key) && id == 0 && key == "tenet_4", "paired zero ref");
  for (const auto payload : {
      "{\"target_rite_id\":0}", "{\"tenet_key\":\"tenet_4\"}",
      "{\"target_rite_id\":0,\"tenet_key\":\"\"}",
      "{\"target_rite_id\":4294967296,\"tenet_key\":\"tenet_4\"}"})
    Assert(!c::ParsePlayerReligionTenetsComparisonRequest12003(payload, id, key), "invalid new pair rejected");
  std::uint64_t revision = 0;
  Assert(c::ParsePlayerReligionTenetsRevision12002("{\"expected_revision\":701}", revision) && revision == 701, "revision alias retained");
  Assert(!c::ParsePlayerReligionTenetsRevision12002(
      "{\"expected_snapshot_revision\":701,\"expected_revision\":702}", revision), "revision conflict retained");
}
} // namespace
int main(int argc, char **argv) {
  try {
    Assert(argc == 2, "output directory argument");
    const std::filesystem::path output(argv[1]); std::filesystem::create_directories(output);
    ComparisonFixture fixture; FrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::character_id; adapter.frame.date_raw = 53175816;
    RequestCases();
    Available(Query(fixture, adapter, output, "distinct-same-faith.json", fixture.target_id, "tenet_1"), fixture.target_id, 1, 3, false);
    Available(Query(fixture, adapter, output, "valid-zero-prohibited.json", fixture.target_id, "tenet_0"), fixture.target_id, 0, 2, false);
    Available(Query(fixture, adapter, output, "same-rite-core.json", 0, "tenet_4"), 0, 4, 4, true);
    Unavailable(Query(fixture, adapter, output, "missing-definition.json", fixture.target_id, "tenet_absent"), target::Failure::tenet_definition_unavailable);
    fixture.target_id = 0xA5000003U; Put(fixture.target_rite, 8, fixture.target_id);
    Available(Query(fixture, adapter, output, "high-generation-target.json", fixture.target_id, "tenet_1"), fixture.target_id, 1, 3, false);
    Unavailable(Query(fixture, adapter, output, "wrong-generation-target.json", 0xA6000003U, "tenet_1"), target::Failure::target_rite_unavailable);
    (void)Query(fixture, adapter, output, "old-no-comparison.json", std::nullopt, "");
    std::cout << "PASS cases=7 checks=" << mailbox_checks
        << " actual_domain_mailbox=true actual_tenet_reader=true actual_full_wire=true actual_renderer=true live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
