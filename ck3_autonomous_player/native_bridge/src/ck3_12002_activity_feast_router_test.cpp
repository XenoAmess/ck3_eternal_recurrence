#include "ck3_12002_activity_feast_router.hpp"
#include "ck3_12002_activity_feast_private_transport_v1.hpp"
#include "ck3_12002_activity_stage5_canstart_private_transport_v1.hpp"
#include "xar_bridge/ck3_12002_thread_runtime.hpp"

#include <array>
#include <atomic>
#include <cstdio>
#include <cstring>
#include <thread>

// Dispatch fixture only: the router and mailbox are production code; native
// gameplay executors and their inner DTO serializers below are fixture data.
// No native activity, actual Start, or live qualification is asserted here.
namespace {
namespace api = xar::ck3_11906;
namespace build = xar::ck3_12002;
namespace game = xar::game;
#define CHECK(condition) do { if (!(condition)) { \
  std::fprintf(stderr, "feast router fixture line %d: %s\n", __LINE__, #condition); \
  return false; } } while (false)

class FixtureAdapter final : public game::GameAdapter {
public:
  game::Snapshot frame{};
  mutable std::atomic<std::uint32_t> reads{0};
  bool available = true;
  FixtureAdapter() {
    frame.date_raw = 53220000;
    frame.paused = true;
    frame.map_ready = true;
    frame.has_played_character = true;
    frame.played_character_id = 29829;
    frame.played_character_alive = true;
  }
  const game::AdapterDescriptor &descriptor() const noexcept override {
    static const game::AdapterDescriptor result{
        "ck3-1.20.0.2-msvc-x64", "1.20.0.2", build::kExecutableSha256,
        "fixture-only", {}};
    return result;
  }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &output) const noexcept override {
    ++reads;
    output = available ? frame : game::Snapshot{};
    return available;
  }
  game::PauseSubmitResult submit_pause_map(game::Snapshot *) const noexcept override {
    return game::PauseSubmitResult::unavailable;
  }
  game::ResumeSubmitResult submit_resume_map(game::Snapshot *) const noexcept override {
    return game::ResumeSubmitResult::unavailable;
  }
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  game::SaveCheckpointResult submit_save_checkpoint() const noexcept override { return {}; }
  game::PreviewMoveArmyResult preview_move_army(std::int32_t, std::int32_t) const noexcept override { return {}; }
  bool read_declarable_wars(std::vector<game::DeclarableWarSnapshot> &) const noexcept override { return false; }
#define UNAVAILABLE(Result, Method, Parameters) \
  game::Result Method Parameters const noexcept override { return game::Result::unavailable; }
  UNAVAILABLE(SelectEventOptionResult, submit_select_event_option, (std::int32_t))
  UNAVAILABLE(ReplyPendingInteractionResult, submit_reply_to_pending_interaction, (game::PendingInteractionReply))
  UNAVAILABLE(RaiseTroopsResult, submit_raise_troops_default, ())
  UNAVAILABLE(MoveArmyResult, submit_move_army, (std::int32_t, std::int32_t))
  UNAVAILABLE(DisbandArmyResult, submit_disband_army, (std::int32_t))
  UNAVAILABLE(SplitArmyHalfResult, submit_split_army_half, (std::int32_t))
  UNAVAILABLE(MergeArmiesResult, submit_merge_armies, (std::int32_t, std::int32_t))
  UNAVAILABLE(StartAssaultResult, submit_start_assault, (std::int32_t))
  UNAVAILABLE(StopAssaultResult, submit_stop_assault, (std::int32_t))
  UNAVAILABLE(ReadDeclarableWarsResult, read_declarable_wars_for_target,
              (std::int32_t, std::vector<game::DeclarableWarSnapshot> &))
  UNAVAILABLE(DeclareWarResult, submit_declare_war, (const game::DeclarableWarSnapshot &))
  UNAVAILABLE(ReadArrangeMarriageChoicesResult, read_arrange_marriage_choices,
              (std::vector<game::ArrangeMarriageChoice> &, game::ArrangeMarriageQueryDiagnostics &))
  UNAVAILABLE(ArrangeMarriageResult, submit_arrange_marriage, (const game::ArrangeMarriageChoice &))
  UNAVAILABLE(EnforceDemandsResult, submit_enforce_demands, (std::int32_t))
  UNAVAILABLE(ReadArmyStrengthsResult, read_army_strengths, (std::vector<game::ArmyStrengthSnapshot> &))
  UNAVAILABLE(ReadCombatSimulationInputsResult, read_combat_simulation_inputs,
              (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsSnapshot &))
  UNAVAILABLE(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3,
              (const game::CombatSimulationInputsRequest &, game::CombatSimulationInputsV3Snapshot &))
  UNAVAILABLE(ReadWarTerminationOptionsResult, read_war_termination_options,
              (std::int32_t, game::WarTerminationOptionsSnapshot &))
  UNAVAILABLE(ReadWarTerminationTermsResult, read_war_termination_terms,
              (std::int32_t, game::WarTerminationTermsSnapshot &))
  UNAVAILABLE(ReadWarTerminationExitTermsResult, read_war_termination_exit_terms,
              (std::int32_t, game::WarTerminationExitTermsSnapshot &))
  UNAVAILABLE(SurrenderWarResult, submit_surrender_war, (std::int32_t))
  UNAVAILABLE(OfferWhitePeaceResult, submit_offer_white_peace, (std::int32_t))
#undef UNAVAILABLE
};

struct MemoryFixture {
  void *iat = nullptr;
  DWORD protection = PAGE_READONLY;
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x18> state{};
  std::array<std::byte, 0x28> tls{};
  std::uintptr_t jomini_slot = 0, state_slot = 0, null_rng_slot = 0;
  std::uint8_t tls_initialized = 1;
};
MemoryFixture *memory_fixture = nullptr;
FixtureAdapter *expected_adapter = nullptr;
std::uint32_t callback_reads = 0, canstart_calls = 0, feast_calls = 0;
bool domain_unavailable = false, start_policy = false, prior_pending = false;
std::array<std::int64_t, 4> last_reserve{};
api::ActivityFeastStage5PrivateModeV1 last_mode{};
DWORD executor_thread = 0;
BOOL WINAPI FakePeek(LPMSG, HWND, UINT, UINT, UINT) { return FALSE; }
void *__fastcall FakeTls() noexcept { return memory_fixture->tls.data(); }
bool FakeQuery(void *opaque, const void *address, MEMORY_BASIC_INFORMATION &output) noexcept {
  auto &memory = *static_cast<MemoryFixture *>(opaque);
  if (address != &memory.iat) return false;
  output = {};
  output.BaseAddress = reinterpret_cast<void *>(reinterpret_cast<std::uintptr_t>(address) & ~4095ULL);
  output.AllocationBase = output.BaseAddress;
  output.RegionSize = 4096;
  output.State = MEM_COMMIT;
  output.Type = MEM_IMAGE;
  output.Protect = memory.protection;
  return true;
}
bool FakeProtect(void *opaque, void *, std::size_t size, DWORD desired, DWORD &previous) noexcept {
  auto &memory = *static_cast<MemoryFixture *>(opaque);
  if (size != 4096) return false;
  previous = memory.protection;
  memory.protection = desired;
  return true;
}
template <typename Query>
bool CheckCallback(Query &query, const api::MainThreadExecutionStampV1 &stamp) noexcept {
  game::Snapshot observed{};
  const bool okay = query.enabled && query.module_base != 0 &&
      query.executable_sha256 == build::kExecutableSha256 &&
      query.native_context == expected_adapter && query.read_snapshot != nullptr &&
      query.expected_revision == 19 && query.expected_snapshot == expected_adapter->frame &&
      query.read_snapshot(query.native_context, observed) && observed == query.expected_snapshot &&
      stamp.date_raw == observed.date_raw && stamp.paused;
  ++callback_reads;
  executor_thread = GetCurrentThreadId();
  query.completed = true;
  return okay;
}
bool Contains(const std::string &text, std::string_view expected) {
  return text.find(expected) != std::string::npos;
}
void Pump(api::MainThreadQueryMailboxV1 &mailbox) {
  api::ObserveMainThreadPumpAndDrainV1(mailbox, build::kSdlWindowsPumpFirstPeekReturnRva,
                                    GetCurrentThreadId());
}
template <typename Operation>
bool WorkerQuery(api::MainThreadQueryMailboxV1 &mailbox, Operation operation) {
  bool result = false;
  std::atomic<bool> done{false};
  std::thread worker([&] { result = operation(); done = true; });
  const auto deadline = GetTickCount64() + 10'000;
  while (!done.load() && GetTickCount64() < deadline) {
    if (mailbox.state.load() == api::MainThreadQueryMailboxStateV1::queued) Pump(mailbox);
    Sleep(1);
  }
  worker.join();
  return result;
}
bool TestRouter() {
  FixtureAdapter adapter;
  expected_adapter = &adapter;
  MemoryFixture memory;
  memory_fixture = &memory;
  memory.iat = reinterpret_cast<void *>(&FakePeek);
  memory.jomini_slot = reinterpret_cast<std::uintptr_t>(memory.jomini.data());
  memory.state_slot = reinterpret_cast<std::uintptr_t>(memory.state.data());
  memory.jomini[0x20] = std::byte{1};
  memory.tls[0x20] = std::byte{1};
  std::memcpy(memory.state.data() + 0x08, &adapter.frame.date_raw, sizeof(adapter.frame.date_raw));
  const std::array<api::MainThreadQueryExecutorV1, 2> executors{
      &build::ExecuteActivityStage5CanStartPrivate12002V1,
      &build::ExecuteActivityFeastStage5Private12002V1};
  auto environment = build::BindThreadRuntimeImage(0x140000000ULL, build::kExecutableSha256, executors);
  environment.offline_fixture = true;
  environment.peek_message_iat_slot_override = &memory.iat;
  environment.resolved_peek_message_override = &FakePeek;
  environment.global_rng_wrapper_slot_override = reinterpret_cast<std::uintptr_t>(&memory.null_rng_slot);
  environment.jomini_state_slot_override = reinterpret_cast<std::uintptr_t>(&memory.jomini_slot);
  environment.game_state_slot_override = reinterpret_cast<std::uintptr_t>(&memory.state_slot);
  environment.tls_initialized_flag_override = reinterpret_cast<std::uintptr_t>(&memory.tls_initialized);
  environment.tls_context_getter_override = &FakeTls;
  environment.memory_protection_context = &memory;
  environment.memory_query_override = &FakeQuery;
  environment.memory_protect_override = &FakeProtect;
  environment.system_page_size_override = 4096;
  api::MainThreadQueryMailboxV1 mailbox;
  CHECK(api::InstallMainThreadQueryMailboxV1(mailbox, environment));
  Pump(mailbox); Pump(mailbox);
  CHECK(api::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready);
  constexpr std::string_view request =
      "{\"expected_revision\":19,\"expected_actor_character_id\":29829,"
      "\"expected_date_raw\":53220000,\"expected_planning_stage\":5,"
      "\"expected_activity_key\":\"activity_feast\",\"expected_option_key\":\"feast_type_generic\"}";
  std::string serialized, failure;
  auto run = [&](std::string_view step, std::string_view payload) {
    return build::HandleActivityFeastPrivate12002(adapter, mailbox, adapter.frame, 19,
        step, payload, "fixture-request", serialized, failure);
  };
  CHECK(build::IsActivityFeastPrivateStep12002(api::kActivityStage5CanStartPrivateStepV1));
  CHECK(!build::IsActivityFeastPrivateStep12002("query-activity-stage5-gold-cost-v1-private"));
  CHECK(WorkerQuery(mailbox, [&] { return run(api::kActivityStage5CanStartPrivateStepV1, request); }));
  CHECK(canstart_calls == 1 && callback_reads == 1 && executor_thread == GetCurrentThreadId());
  CHECK(Contains(serialized, "\"activity_stage5_canstart\":{") &&
        Contains(serialized, "\"read_only\":true") && Contains(serialized, "fixture-request"));
  CHECK(mailbox.state == api::MainThreadQueryMailboxStateV1::idle);

  domain_unavailable = true;
  CHECK(WorkerQuery(mailbox, [&] { return run(api::kActivityStage5CanStartPrivateStepV1, request); }));
  CHECK(Contains(serialized, "\"query_status\":\"unavailable\"") &&
        Contains(serialized, "fixture final CanStart unavailable"));
  CHECK(mailbox.failure_flags == 0 && canstart_calls == 2);
  domain_unavailable = false;

  CHECK(!run(api::kActivityStage5CanStartPrivateStepV1,
      "{\"expected_revision\":19,\"expected_actor_character_id\":29829,\"expected_date_raw\":53220000} "));
  CHECK(failure == "activity stage-5 CanStart request invalid" && canstart_calls == 2);
  CHECK(!run(api::kActivityStage5CanStartPrivateStepV1, "{\"expected_revision\":18}"));
  CHECK(failure == "activity feast exact-build frame or request invalid" && canstart_calls == 2);
  CHECK(!run(api::kActivityFeastStage5StartPrivateStepV1, request));
  CHECK(failure == "activity feast Start policy request invalid" && feast_calls == 0);

  std::string start_request(request.substr(0, request.size() - 1));
  start_request += ",\"policy_positive\":true,\"previous_submit_pending\":false,"
      "\"reserve_gold_raw\":100000,\"reserve_treasury_raw\":200000,"
      "\"reserve_piety_raw\":300000,\"reserve_barter_goods_raw\":400000}";
  CHECK(WorkerQuery(mailbox, [&] { return run(api::kActivityFeastStage5StartPrivateStepV1, start_request); }));
  CHECK(feast_calls == 1 && callback_reads == 3 && start_policy && !prior_pending);
  const std::array<std::int64_t, 4> expected_reserve{100000, 200000, 300000, 400000};
  CHECK(last_reserve == expected_reserve && last_mode == api::ActivityFeastStage5PrivateModeV1::start_attempt);
  CHECK(Contains(serialized, "\"native_status\":\"submitted_pending\"") &&
        Contains(serialized, "\"status\":\"pending\"") && Contains(serialized, "\"read_only\":false"));

  CHECK(WorkerQuery(mailbox, [&] { return run(api::kActivityFeastHostedPostPrivateStepV1,
      "{\"expected_revision\":19,\"expected_actor_character_id\":29829,\"expected_date_raw\":53220000}"); }));
  CHECK(last_mode == api::ActivityFeastStage5PrivateModeV1::hosted_post && feast_calls == 2);
  CHECK(Contains(serialized, "\"activity_feast_hosted_post\":{") && Contains(serialized, "\"read_only\":true"));
  CHECK(mailbox.executed_requests == 4 && mailbox.failure_flags == 0 && callback_reads == 4);
  CHECK(api::UninstallMainThreadQueryMailboxV1(mailbox, 0) == api::MainThreadQueryUninstallResultV1::uninstalled);
  CHECK(memory.iat == reinterpret_cast<void *>(&FakePeek));
  return true;
}
} // namespace

namespace xar::ck3_12002 {
bool ExecuteActivityStage5CanStartPrivate12002V1(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto &query = *static_cast<ActivityStage5CanStartPrivate12002QueryV1 *>(opaque);
  ++canstart_calls;
  if (!CheckCallback(query, stamp)) return false;
  if (domain_unavailable) query.failure = "fixture final CanStart unavailable";
  return true;
}
std::string SerializeActivityStage5CanStartPrivate12002V1(
    const ActivityStage5CanStartPrivate12002QueryV1 &query) {
  return query.failure.empty()
      ? "{\"query_status\":\"available\",\"fixture_dispatch\":true}"
      : "{\"query_status\":\"unavailable\",\"failure\":\"fixture final CanStart unavailable\",\"fixture_dispatch\":true}";
}
bool ExecuteActivityFeastStage5Private12002V1(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto &query = *static_cast<ActivityFeastStage5Private12002QueryV1 *>(opaque);
  ++feast_calls;
  if (!CheckCallback(query, stamp)) return false;
  last_mode = query.mode;
  start_policy = query.policy_positive;
  prior_pending = query.previous_submit_pending;
  last_reserve = query.reserve_raw;
  if (query.mode == ck3_11906::ActivityFeastStage5PrivateModeV1::start_attempt) {
    query.start.invoked = true;
    query.start.status = bridge::ActivityFeastStage5StartStatusV1::submitted_pending;
  }
  return true;
}
std::string SerializeActivityFeastStage5Private12002V1(
    const ActivityFeastStage5Private12002QueryV1 &) {
  return "{\"query_status\":\"available\",\"fixture_dispatch\":true}";
}
} // namespace xar::ck3_12002

int main() {
  if (!TestRouter()) return 1;
  std::puts("PASS: production feast router and mailbox dispatch; fixture adapter snapshot callbacks, CanStart unavailable diagnostics, request grammar, reserve order, pending Start and independent hosted-post routes; no CK3 contact or native/live qualification");
  return 0;
}
