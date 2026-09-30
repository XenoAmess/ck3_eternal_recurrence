#include "xar_bridge/h2743_stock_private_query_v1.hpp"

#include <array>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <string_view>
#include <vector>

namespace {
using namespace xar::ck3_11906;
using namespace xar::game;
int g_checks = 0;
int g_failures = 0;
int g_cases = 0;
const char *g_case = "initial";
void Check(bool condition, const char *expression, int line) {
  ++g_checks;
  if (!condition) {
    ++g_failures;
    std::fprintf(stderr, "FAIL %s line %d: %s\n", g_case, line, expression);
  }
}
#define CHECK(expression) Check(static_cast<bool>(expression), #expression, __LINE__)
void Case(const char *name) { g_case = name; ++g_cases; }

// The actual mailbox remains alive for the fixture process lifetime.
MainThreadQueryMailboxV1 g_mailbox{};
void *g_tls_context = nullptr;
void *__fastcall FakeTls() noexcept { return g_tls_context; }
BOOL WINAPI FakePeek(LPMSG, HWND, UINT, UINT, UINT) { return FALSE; }
int __cdecl FakePoll(void *) { return 0; }
bool ForeignExecutor(void *, const MainThreadExecutionStampV1 &) noexcept {
  return true;
}

struct Protection {
  void *slot = nullptr;
  DWORD protect = PAGE_READONLY;
};
bool MemoryQuery(void *opaque, const void *address,
                 MEMORY_BASIC_INFORMATION &out) noexcept {
  auto &p = *static_cast<Protection *>(opaque);
  if (address != p.slot) return false;
  const auto value = reinterpret_cast<std::uintptr_t>(address);
  out = {};
  out.BaseAddress = reinterpret_cast<void *>((value / 4096) * 4096);
  out.AllocationBase = out.BaseAddress;
  out.AllocationProtect = PAGE_READONLY;
  out.RegionSize = 4096;
  out.State = MEM_COMMIT;
  out.Protect = p.protect;
  out.Type = MEM_IMAGE;
  return true;
}
bool MemoryProtect(void *opaque, void *, std::size_t size, DWORD next,
                   DWORD &previous) noexcept {
  auto &p = *static_cast<Protection *>(opaque);
  previous = p.protect;
  if (size != 4096) return false;
  p.protect = next;
  return true;
}

struct FakeRuntime {
  std::array<std::byte, 0x18> rng{}, game{};
  std::array<std::byte, 0x28> jomini{}, tls{};
  std::uintptr_t rng_pointer = 0, rng_slot = 0;
  std::uintptr_t game_slot = 0, jomini_slot = 0;
  std::uint8_t tls_initialized = 1;
  Protection protection{};
  void *iat = reinterpret_cast<void *>(&FakePeek);
  void *poll = reinterpret_cast<void *>(&FakePoll);
  static constexpr std::int32_t date = 53'219'928;
  static constexpr std::uintptr_t module = 0x140000000ULL;
  FakeRuntime() {
    const auto owner = GetCurrentThreadId();
    std::memcpy(rng.data() + 0x10, &owner, sizeof(owner));
    rng_pointer = reinterpret_cast<std::uintptr_t>(rng.data());
    rng_slot = reinterpret_cast<std::uintptr_t>(&rng_pointer);
    game_slot = reinterpret_cast<std::uintptr_t>(game.data());
    jomini_slot = reinterpret_cast<std::uintptr_t>(jomini.data());
    SetDate(date);
    jomini[0x20] = std::byte{1};
    tls[0x20] = std::byte{1};
    g_tls_context = tls.data();
  }
  void SetDate(std::int32_t value) {
    std::memcpy(game.data() + kGameStateDateRawOffset, &value, sizeof(value));
  }
  std::int32_t Date() const {
    std::int32_t value = 0;
    std::memcpy(&value, game.data() + kGameStateDateRawOffset, sizeof(value));
    return value;
  }
  MainThreadQueryInstallEnvironmentV1 Environment() {
    protection.slot = &iat;
    MainThreadQueryInstallEnvironmentV1 e{};
    e.module_base = module;
    e.exact_build_admitted = true;
    e.offline_fixture = true;
    e.peek_message_iat_slot_override = &iat;
    e.resolved_peek_message_override = &FakePeek;
    e.global_rng_wrapper_slot_override = reinterpret_cast<std::uintptr_t>(&rng_slot);
    e.jomini_state_slot_override = reinterpret_cast<std::uintptr_t>(&jomini_slot);
    e.game_state_slot_override = reinterpret_cast<std::uintptr_t>(&game_slot);
    e.tls_initialized_flag_override = reinterpret_cast<std::uintptr_t>(&tls_initialized);
    e.tls_context_getter_override = &FakeTls;
    e.memory_protection_context = &protection;
    e.memory_query_override = &MemoryQuery;
    e.memory_protect_override = &MemoryProtect;
    e.system_page_size_override = 4096;
    e.executor_submission_enabled = true;
    e.permitted_h2743_stock_predicate_executor = &ExecuteH2743StockPrivateQueryV1;
    e.sdl_poll_event_slot_override = &poll;
    e.resolved_sdl_poll_event_override = &FakePoll;
    return e;
  }
};

// Snapshot and original baseline virtual calls are the only simulated game
// observations. Every gameplay virtual increments a counter if ever reached.
class FakeGame final : public GameAdapter {
public:
  static constexpr std::int32_t actor = 29829, opponent = 18090, war = 16777231;
  Snapshot snapshot{};
  DefenderDeJureExitTermsV1 baseline{};
  mutable unsigned snapshot_calls = 0, baseline_calls = 0, actions = 0;
  unsigned drift_snapshot_call = 0;
  ReadDefenderDeJureExitTermsV1Result baseline_result =
      ReadDefenderDeJureExitTermsV1Result::available_baseline;
  FakeGame() {
    snapshot.date_raw = FakeRuntime::date;
    snapshot.paused = true;
    snapshot.map_ready = true;
    snapshot.has_played_character = true;
    snapshot.played_character_id = actor;
    snapshot.played_character_alive = true;
    ActiveWarSnapshot w{};
    w.war_id = war;
    w.player_side = PlayerWarSide::defender;
    w.primary_opponent_character_id = opponent;
    w.player_is_primary_war_leader = true;
    snapshot.active_wars.push_back(w);
    baseline.war_id = war;
    baseline.date_raw = FakeRuntime::date;
    baseline.primary_attacker_character_id = opponent;
    baseline.primary_defender_character_id = actor;
    baseline.same_frame_stable = true;
  }
  const AdapterDescriptor &descriptor() const noexcept override {
    static const AdapterDescriptor d{"offline-h2743-query-fixture", "fixture",
      "fixture-not-a-CK3-hash", "fixture", {}};
    return d;
  }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(Snapshot &out) const noexcept override {
    ++snapshot_calls;
    out = snapshot;
    if (snapshot_calls == drift_snapshot_call) ++out.date_raw;
    return true;
  }
  ReadDefenderDeJureExitTermsV1Result read_defender_de_jure_exit_terms_v1(
      std::int32_t id, DefenderDeJureExitTermsV1 &out) const noexcept override {
    ++baseline_calls;
    out = baseline;
    return id == war ? baseline_result : ReadDefenderDeJureExitTermsV1Result::unavailable;
  }
  PauseSubmitResult submit_pause_map(Snapshot *) const noexcept override { ++actions; return PauseSubmitResult::unavailable; }
  ResumeSubmitResult submit_resume_map(Snapshot *) const noexcept override { ++actions; return ResumeSubmitResult::unavailable; }
  bool submit_set_speed(std::int32_t) const noexcept override { ++actions; return false; }
  SelectEventOptionResult submit_select_event_option(std::int32_t) const noexcept override { ++actions; return SelectEventOptionResult::unavailable; }
  SaveCheckpointResult submit_save_checkpoint() const noexcept override { ++actions; return {}; }
  ReplyPendingInteractionResult submit_reply_to_pending_interaction(PendingInteractionReply) const noexcept override { ++actions; return ReplyPendingInteractionResult::unavailable; }
  RaiseTroopsResult submit_raise_troops_default() const noexcept override { ++actions; return RaiseTroopsResult::unavailable; }
  MoveArmyResult submit_move_army(std::int32_t, std::int32_t) const noexcept override { ++actions; return MoveArmyResult::unavailable; }
  PreviewMoveArmyResult preview_move_army(std::int32_t, std::int32_t) const noexcept override { return {}; }
  DisbandArmyResult submit_disband_army(std::int32_t) const noexcept override { ++actions; return DisbandArmyResult::unavailable; }
  SplitArmyHalfResult submit_split_army_half(std::int32_t) const noexcept override { ++actions; return SplitArmyHalfResult::unavailable; }
  MergeArmiesResult submit_merge_armies(std::int32_t, std::int32_t) const noexcept override { ++actions; return MergeArmiesResult::unavailable; }
  StartAssaultResult submit_start_assault(std::int32_t) const noexcept override { ++actions; return StartAssaultResult::unavailable; }
  StopAssaultResult submit_stop_assault(std::int32_t) const noexcept override { ++actions; return StopAssaultResult::unavailable; }
  bool read_declarable_wars(std::vector<DeclarableWarSnapshot> &) const noexcept override { return false; }
  ReadDeclarableWarsResult read_declarable_wars_for_target(std::int32_t, std::vector<DeclarableWarSnapshot> &) const noexcept override { return ReadDeclarableWarsResult::unavailable; }
  DeclareWarResult submit_declare_war(const DeclarableWarSnapshot &) const noexcept override { ++actions; return DeclareWarResult::unavailable; }
  ReadArrangeMarriageChoicesResult read_arrange_marriage_choices(std::vector<ArrangeMarriageChoice> &, ArrangeMarriageQueryDiagnostics &) const noexcept override { return ReadArrangeMarriageChoicesResult::unavailable; }
  ArrangeMarriageResult submit_arrange_marriage(const ArrangeMarriageChoice &) const noexcept override { ++actions; return ArrangeMarriageResult::unavailable; }
  EnforceDemandsResult submit_enforce_demands(std::int32_t) const noexcept override { ++actions; return EnforceDemandsResult::unavailable; }
  ReadArmyStrengthsResult read_army_strengths(std::vector<ArmyStrengthSnapshot> &) const noexcept override { return ReadArmyStrengthsResult::unavailable; }
  ReadCombatSimulationInputsResult read_combat_simulation_inputs(const CombatSimulationInputsRequest &, CombatSimulationInputsSnapshot &) const noexcept override { return ReadCombatSimulationInputsResult::unavailable; }
  ReadCombatSimulationInputsV3Result read_combat_simulation_inputs_v3(const CombatSimulationInputsRequest &, CombatSimulationInputsV3Snapshot &) const noexcept override { return ReadCombatSimulationInputsV3Result::unavailable; }
  ReadWarTerminationOptionsResult read_war_termination_options(std::int32_t, WarTerminationOptionsSnapshot &) const noexcept override { return ReadWarTerminationOptionsResult::unavailable; }
  ReadWarTerminationTermsResult read_war_termination_terms(std::int32_t, WarTerminationTermsSnapshot &) const noexcept override { return ReadWarTerminationTermsResult::unavailable; }
  ReadWarTerminationExitTermsResult read_war_termination_exit_terms(std::int32_t, WarTerminationExitTermsSnapshot &) const noexcept override { return ReadWarTerminationExitTermsResult::unavailable; }
  SurrenderWarResult submit_surrender_war(std::int32_t) const noexcept override { ++actions; return SurrenderWarResult::unavailable; }
  OfferWhitePeaceResult submit_offer_white_peace(std::int32_t) const noexcept override { ++actions; return OfferWhitePeaceResult::unavailable; }
};

struct Session {
  FakeRuntime runtime{};
  FakeGame game{};
  H2743StockPrivateQueryV1 query{};
  bool installed = false;
  Session() {
    installed = InstallMainThreadQueryMailboxV1(g_mailbox, runtime.Environment());
    CHECK(installed);
    if (!installed) std::abort();
    CHECK(g_mailbox.offline_fixture);
    CHECK(g_mailbox.permitted_h2743_stock_predicate_executor == &ExecuteH2743StockPrivateQueryV1);
    query.mailbox = &g_mailbox;
    query.game = &game;
    query.module_base = FakeRuntime::module;
    query.expected_revision = 17;
    query.expected_snapshot = game.snapshot;
    query.war_id = FakeGame::war;
    CHECK(!ObserveMainThreadPumpAndDrainV1(g_mailbox, kHandlePdxEventsSdlPollEventReturnRva, GetCurrentThreadId()));
    CHECK(!ObserveMainThreadPumpAndDrainV1(g_mailbox, kHandlePdxEventsSdlPollEventReturnRva, GetCurrentThreadId()));
    CHECK(ReadMainThreadQueryMailboxDiagnosticsV1(g_mailbox).ready);
  }
  ~Session() {
    CHECK(game.actions == 0);
    CHECK(UninstallMainThreadQueryMailboxV1(g_mailbox, 100) == MainThreadQueryUninstallResultV1::uninstalled);
    CHECK(runtime.iat == reinterpret_cast<void *>(&FakePeek));
    CHECK(runtime.poll == reinterpret_cast<void *>(&FakePoll));
  }
  void Submit() {
    CHECK(TrySubmitMainThreadQueryV1(g_mailbox, &ExecuteH2743StockPrivateQueryV1, &query, query.ticket) == MainThreadQuerySubmitResultV1::submitted);
    CHECK(query.ticket.sequence != 0);
  }
  MainThreadQueryWaitResultV1 DrainWaitReclaim() {
    const auto original_ticket = query.ticket;
    const auto before_date = runtime.Date();
    (void)ObserveMainThreadPumpAndDrainV1(g_mailbox, kHandlePdxEventsSdlPollEventReturnRva, GetCurrentThreadId());
    const auto wait = WaitForMainThreadQueryV1(g_mailbox, original_ticket, 0);
    CHECK(ReclaimMainThreadQueryV1(g_mailbox, original_ticket) == MainThreadQueryReclaimResultV1::reclaimed);
    CHECK(runtime.Date() == before_date);
    return wait;
  }
};

void TestGrammar() {
  Case("canonical_parser");
  for (const std::string_view token : {"1", "16777231", "2147483647"}) {
    std::int32_t id = -1;
    CHECK(ParseH2743StockPrivateStepV1(std::string(kH2743StockPrivateStepPrefixV1) + std::string(token), id));
    CHECK(id > 0);
  }
  for (const std::string_view token : {"", "0", "01", "-1", "+1", "1x", "1 ", " 1", "1-2", "2147483648", "99999999999"}) {
    std::int32_t id = 123;
    CHECK(!ParseH2743StockPrivateStepV1(std::string(kH2743StockPrivateStepPrefixV1) + std::string(token), id));
    CHECK(id == -1);
  }
  std::int32_t id = 123;
  CHECK(!ParseH2743StockPrivateStepV1("query-defender-de-jure-exit-terms-v2-1", id));
  CHECK(id == -1);
}

void TestTypedInput() {
  Case("typed_input_conversion");
  using S = H2743StockPredicateStateV1;
  using F = H2743StockPredicateFailureV1;
  const auto yes = H2743StockTypedInputV1({S::observed_native_true, F::none});
  const auto no = H2743StockTypedInputV1({S::observed_native_false, F::none});
  CHECK(yes.value.has_value() && *yes.value && yes.unavailable_reason.empty());
  CHECK(no.value.has_value() && !*no.value && no.unavailable_reason.empty());
  for (const auto failure : {F::disabled, F::stale_identity, F::unstable_sample}) {
    const auto unavailable = H2743StockTypedInputV1({S::unavailable, failure});
    CHECK(!unavailable.value.has_value() && !unavailable.unavailable_reason.empty());
  }
  const auto contradictory = H2743StockTypedInputV1({S::observed_native_true, F::stale_identity});
  CHECK(!contradictory.value.has_value());
}

#if XAR_CK3_ENABLE_H2743_STOCK_PREDICATE_READER_V1
void TestMailboxRoute() {
  {
    Case("actual_named_mailbox_complete_unavailable");
    Session s;
    s.Submit();
    CHECK(s.DrainWaitReclaim() == MainThreadQueryWaitResultV1::completed);
    CHECK(s.query.completed && s.query.failure_stage.empty());
    CHECK(s.query.executor_invocations == 1 && s.game.baseline_calls == 1);
    CHECK(s.game.snapshot_calls == 2);
    CHECK(!s.query.stock.double_sample_stable && !s.query.stock.material_complete);
    for (const auto value : {s.query.stock.short_truce, s.query.stock.long_truce, s.query.stock.border_raid_pair}) {
      CHECK(value.state == H2743StockPredicateStateV1::unavailable);
      CHECK(value.failure == H2743StockPredicateFailureV1::disabled);
      const auto typed = H2743StockTypedInputV1(value);
      CHECK(!typed.value.has_value() && typed.unavailable_reason == "stock_condition_reader_disabled");
    }
    H2743StockNativeContextV1 context{};
    context.module_base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    context.application_main_thread_id = GetCurrentThreadId();
    context.exact_build_verified = false; // actual offline owner gate
    const auto native = BindH2743StockNativeSourcesV1(context);
    CHECK(!native.enabled && native.read_bytes == nullptr && native.lookup_identifier == nullptr && native.hash_name == nullptr && native.read_stamp == nullptr);
    CHECK(ReadMainThreadQueryMailboxDiagnosticsV1(g_mailbox).executed_requests == 1);
    const auto bytes = SerializeH2743StockPrivateEvidenceV1(s.query);
    const auto expected = std::string("{\"schema\":\"xar.ck3.h2743-stock-predicate-evidence.v1\",\"native_revision\":17,\"date_raw\":53219928,\"actor_character_id\":29829,\"war_id\":16777231,\"attacker_character_id\":18090,\"defender_character_id\":29829,\"paused\":true,\"map_ready\":true,\"application_main_thread_id\":") + std::to_string(GetCurrentThreadId()) + ",\"pump_epoch\":3,\"mailbox_sequence\":1,\"executor_invocations\":1,\"same_frame_stable\":true,\"stock_double_sample_stable\":false,\"stock_parties_bound\":false,\"material_complete\":false}";
    CHECK(bytes == expected);
    std::printf("EVIDENCE_JSON=%s\n", bytes.c_str());
    std::printf("QUERY_DATE_ADVANCE=0 QUERY_GAMEPLAY_ACTIONS=%u NATIVE_BINDING_ENABLED=0\n", s.game.actions);
  }
  {
    Case("foreign_executor_rejected");
    Session s;
    MainThreadQueryTicketV1 ticket{};
    CHECK(TrySubmitMainThreadQueryV1(g_mailbox, &ForeignExecutor, &s.query, ticket) == MainThreadQuerySubmitResultV1::invalid_request);
    CHECK(ticket.sequence == 0 && s.query.executor_invocations == 0 && s.game.baseline_calls == 0);
  }
  {
    Case("stale_query_ticket_rejected");
    Session s;
    s.Submit();
    const auto ticket = s.query.ticket;
    ++s.query.ticket.sequence;
    CHECK(ObserveMainThreadPumpAndDrainV1(g_mailbox, kHandlePdxEventsSdlPollEventReturnRva, GetCurrentThreadId()));
    CHECK(WaitForMainThreadQueryV1(g_mailbox, ticket, 0) == MainThreadQueryWaitResultV1::executor_failed);
    CHECK(ReclaimMainThreadQueryV1(g_mailbox, ticket) == MainThreadQueryReclaimResultV1::reclaimed);
    CHECK(!s.query.completed && s.game.baseline_calls == 0 && s.query.failure_stage == "application_main_ownership");
  }
  {
    Case("native_tls_marker_drift_rejected");
    Session s;
    s.Submit();
    s.runtime.tls[0x20] = std::byte{0};
    CHECK(s.DrainWaitReclaim() == MainThreadQueryWaitResultV1::infrastructure_failed);
    CHECK(!s.query.completed && s.query.executor_invocations == 0 && s.game.baseline_calls == 0);
  }
  {
    Case("native_date_admission_mismatch_rejected");
    Session s;
    s.Submit();
    s.runtime.SetDate(FakeRuntime::date + 1); // fixture injection, never game command
    const auto wait = s.DrainWaitReclaim();
    std::printf("NATIVE_DATE_DRIFT_WAIT=%u INVOCATIONS=%u PHASE=%.*s\n", static_cast<unsigned>(wait), s.query.executor_invocations, static_cast<int>(s.query.failure_stage.size()), s.query.failure_stage.data());
    CHECK(wait == MainThreadQueryWaitResultV1::executor_failed);
    CHECK(!s.query.completed && s.query.failure_stage == "application_main_ownership" && s.game.baseline_calls == 0);
  }
  {
    Case("published_date_native_stamp_mismatch_rejected");
    Session s;
    ++s.game.snapshot.date_raw;
    s.query.expected_snapshot = s.game.snapshot;
    s.Submit();
    CHECK(s.DrainWaitReclaim() == MainThreadQueryWaitResultV1::completed);
    CHECK(!s.query.completed && s.query.failure_stage == "admission_frame" && s.game.baseline_calls == 0);
  }
  {
    Case("published_actor_frame_drift_rejected");
    Session s;
    s.Submit();
    ++s.game.snapshot.played_character_id;
    CHECK(s.DrainWaitReclaim() == MainThreadQueryWaitResultV1::completed);
    CHECK(!s.query.completed && s.query.failure_stage == "admission_frame" && s.game.baseline_calls == 0);
  }
  {
    Case("duplicate_war_frame_rejected");
    Session s;
    s.game.snapshot.active_wars.push_back(s.game.snapshot.active_wars.front());
    s.query.expected_snapshot = s.game.snapshot;
    s.Submit();
    CHECK(s.DrainWaitReclaim() == MainThreadQueryWaitResultV1::completed);
    CHECK(!s.query.completed && s.query.failure_stage == "admission_frame" && s.game.baseline_calls == 0);
  }
  {
    Case("baseline_attacker_party_mismatch_rejected");
    Session s;
    ++s.game.baseline.primary_attacker_character_id;
    s.Submit();
    CHECK(s.DrainWaitReclaim() == MainThreadQueryWaitResultV1::completed);
    CHECK(!s.query.completed && s.query.failure_stage == "baseline_unavailable" && s.game.baseline_calls == 1);
  }
  {
    Case("baseline_defender_party_mismatch_rejected");
    Session s;
    ++s.game.baseline.primary_defender_character_id;
    s.Submit();
    CHECK(s.DrainWaitReclaim() == MainThreadQueryWaitResultV1::completed);
    CHECK(!s.query.completed && s.query.failure_stage == "baseline_unavailable" && s.game.baseline_calls == 1);
  }
  {
    Case("baseline_target_titles_mismatch_rejected");
    Session s;
    s.game.baseline.target_title_ids.push_back(2111);
    s.Submit();
    CHECK(s.DrainWaitReclaim() == MainThreadQueryWaitResultV1::completed);
    CHECK(!s.query.completed && s.query.failure_stage == "baseline_unavailable");
  }
  {
    Case("baseline_date_mismatch_rejected");
    Session s;
    ++s.game.baseline.date_raw;
    s.Submit();
    CHECK(s.DrainWaitReclaim() == MainThreadQueryWaitResultV1::completed);
    CHECK(!s.query.completed && s.query.failure_stage == "baseline_unavailable");
  }
  {
    Case("completion_frame_drift_rejected");
    Session s;
    s.game.drift_snapshot_call = 2;
    s.Submit();
    CHECK(s.DrainWaitReclaim() == MainThreadQueryWaitResultV1::completed);
    CHECK(!s.query.completed && s.query.failure_stage == "completion_frame");
  }
  {
    Case("material_complete_baseline_rejected");
    Session s;
    s.game.baseline.material_complete = true;
    s.Submit();
    CHECK(s.DrainWaitReclaim() == MainThreadQueryWaitResultV1::completed);
    CHECK(!s.query.completed && s.query.failure_stage == "baseline_unavailable");
  }
}
#endif
} // namespace

int main() {
#if XAR_CK3_ENABLE_H2743_STOCK_PREDICATE_READER_V1
  TestGrammar();
  TestTypedInput();
  TestMailboxRoute();
#else
  Case("default_OFF_executor_rejected");
  H2743StockPrivateQueryV1 query{};
  MainThreadExecutionStampV1 stamp{};
  CHECK(!ExecuteH2743StockPrivateQueryV1(&query, stamp));
  CHECK(!query.completed && query.executor_invocations == 0);
  H2743StockNativeContextV1 context{};
  const auto bindings = BindH2743StockNativeSourcesV1(context);
  CHECK(!bindings.enabled && bindings.read_bytes == nullptr && bindings.lookup_identifier == nullptr && bindings.hash_name == nullptr && bindings.read_stamp == nullptr);
#endif
  std::printf("h2743 private query route fixture: %d cases, %d checks, %d failures; macro=%d\n", g_cases, g_checks, g_failures, XAR_CK3_ENABLE_H2743_STOCK_PREDICATE_READER_V1);
  return g_failures == 0 ? 0 : 1;
}
