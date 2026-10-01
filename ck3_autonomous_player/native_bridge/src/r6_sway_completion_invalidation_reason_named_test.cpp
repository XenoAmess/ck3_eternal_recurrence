// Reuse the readonly typed-slot fixture constructor; its old matrix is not run.
#define main ExecutionInstallerPreviousFixtureMainNotExecuted
#include "ck3_12002_sway_completion_execution_install_test.cpp"
#undef main

#include "xar_bridge/ck3_12002_sway_completion_invalidation_reason_mailbox.hpp"

namespace {
namespace api = xar::ck3_11906;
namespace game = xar::game;

template <typename T> T ReasonNamedGet(const void *pointer, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(pointer) + offset, sizeof(value));
  return value;
}
std::int32_t reason_named_owner_identifier = 201;
std::int32_t reason_named_target_identifier = 202;
std::int32_t reason_named_scheme_identifier = 203;
SwayInvalidationToken12002 *ReasonNamedLookup(
    const void *environment, SwayInvalidationToken12002 *out, std::int32_t identifier) {
  const auto *data = ReasonNamedGet<const std::byte *>(environment, 0);
  const auto count = ReasonNamedGet<std::int32_t>(environment, 0x0C);
  for (std::int32_t index = 0; index < count; ++index) {
    const auto *row = data + static_cast<std::size_t>(index) * 0x20;
    if (ReasonNamedGet<std::int32_t>(row, 0) == identifier) {
      *out = ReasonNamedGet<SwayInvalidationToken12002>(row, 8);
      return out;
    }
  }
  const auto *script = ReasonNamedGet<const std::byte *>(environment, 0x3D0);
  const auto *script_data = ReasonNamedGet<const std::byte *>(script, 0x18);
  const auto script_count = ReasonNamedGet<std::int32_t>(script, 0x24);
  for (std::int32_t index = 0; index < script_count; ++index) {
    const auto *row = script_data + static_cast<std::size_t>(index) * 0x18;
    if (ReasonNamedGet<std::int32_t>(row, 0) == identifier) {
      *out = ReasonNamedGet<SwayInvalidationToken12002>(row, 8);
      return out;
    }
  }
  *out = {};
  return out;
}

struct ReasonNamedInput {
  alignas(8) std::array<std::byte, 0xC0> effect{};
  alignas(8) std::array<std::byte, 0x80> child{};
  alignas(8) std::array<std::byte, 0x50> scalar{};
  std::array<void *, 1> children{child.data()};
  std::array<std::byte, 0x400> environment{};
  std::array<std::byte, 0x28> script{};
  std::array<std::byte, 2 * 0x20> env_rows{};
  std::array<std::byte, 0x18> script_rows{};
  std::array<std::byte, 0x30> context{};
  SwayInvalidationToken12002 root{4, 0, 0, actor};
  std::string *title = nullptr;
  std::string *reason = nullptr;
  ReasonNamedInput() {
    names[701] = "send_interface_toast";
    names[702] = "custom_tooltip";
    Put(effect.data(), 0, base + kSwayExecutionToastVtableRva12002);
    Put(effect.data(), 8, std::int32_t{701});
    Put(effect.data(), 0x0C, std::uint8_t{0});
    Put(effect.data(), 0x30, children.data());
    Put(effect.data(), 0x38, std::int32_t{1});
    Put(effect.data(), 0x3C, std::int32_t{1});
    Put(effect.data(), 0x60, base + kSwayExecutionTitleWrapperVtableRva12002);
    Put(effect.data(), 0x68, std::uint16_t{4});
    Put(effect.data(), 0x70, scalar.data());
    Put(scalar.data(), 0, base + kSwayExecutionScalarLocalizationVtableRva12002);
    title = ::new (scalar.data() + 0x30) std::string("sway_invalidated_title");
    Put(child.data(), 0, base + 0x4931918);
    Put(child.data(), 8, std::int32_t{702});
    Put(child.data(), 0x0C, std::uint8_t{0});
    Put(child.data(), 0x3C, std::int32_t{0});
    reason = ::new (child.data() + 0x50) std::string("sway_invalidated_dead");
    Put(environment.data(), 0, env_rows.data());
    Put(environment.data(), 8, std::int32_t{2});
    Put(environment.data(), 0x0C, std::int32_t{2});
    Put(environment.data(), 0x3D0, script.data());
    Put(script.data(), 0x18, script_rows.data());
    Put(script.data(), 0x20, std::int32_t{1});
    Put(script.data(), 0x24, std::int32_t{1});
    Put(env_rows.data(), 0, reason_named_owner_identifier);
    Put(env_rows.data(), 8, SwayInvalidationToken12002{4, 0, 0, actor});
    Put(env_rows.data(), 0x20, reason_named_target_identifier);
    Put(env_rows.data(), 0x28, SwayInvalidationToken12002{4, 0, 0, target});
    Put(script_rows.data(), 0, reason_named_scheme_identifier);
    Put(script_rows.data(), 8, SwayInvalidationToken12002{9, 0, 0, scheme});
    Put(context.data(), 0, &root);
    Put(context.data(), 0x10, script.data());
    Put(context.data(), 0x18, environment.data());
  }
  ~ReasonNamedInput() {
    std::destroy_at(title);
    std::destroy_at(reason);
  }
};

SwayInvalidationReasonQuery12002 ReasonNamedRequest() { return {actor, target, scheme, 0}; }
struct ReasonNamedSinkContext {
  SwayInvalidationReasonBindings12002 bindings;
  SwayInvalidationReasonRecorder12002 recorder;
  std::size_t calls = 0;
  bool same_native_arguments = true;
  bool source_capture_precedes_original = false;
  SwayInvalidationReasonCapture12002 last_capture = SwayInvalidationReasonCapture12002::ignored;
};
ReasonNamedSinkContext *reason_named_original_sink = nullptr;
void ReasonNamedSecondarySink(void *owner, const void *effect, const void *context) noexcept {
  auto &sink = *static_cast<ReasonNamedSinkContext *>(owner);
  ++sink.calls;
  sink.same_native_arguments = sink.same_native_arguments &&
      effect == expected_effect && context == expected_context;
  // The only capture invocation is reached through the actually installed slot.
  sink.last_capture = CaptureAndRecordSwayInvalidationReason12002(
      sink.bindings, effect, context, sink.recorder);
}
void ReasonNamedOriginal(std::size_t index, const void *effect, const void *context) {
  ++original_calls[index];
  original_arguments_match = original_arguments_match &&
      effect == expected_effect && context == expected_context;
  SwayInvalidationReasonQueryResult12002 copied;
  reason_named_original_sink->source_capture_precedes_original =
      reason_named_original_sink->calls == 1 &&
      reason_named_original_sink->recorder.Query(ReasonNamedRequest(), copied) &&
      copied.records.size() == 1;
}
void ReasonNamedOriginal0(const void *effect, const void *context) {
  ReasonNamedOriginal(0, effect, context);
}
void ReasonNamedOriginal1(const void *effect, const void *context) {
  ReasonNamedOriginal(1, effect, context);
}
void ReasonNamedOriginal2(const void *effect, const void *context) {
  ReasonNamedOriginal(2, effect, context);
}
const std::array<SwayCompletionNativeExecute12002, 3> reason_named_originals{
    &ReasonNamedOriginal0, &ReasonNamedOriginal1, &ReasonNamedOriginal2};

class ReasonNamedFrameAdapter final : public game::GameAdapter {
public:
  game::Snapshot frame{};
  DWORD owner = GetCurrentThreadId();
  const game::AdapterDescriptor &descriptor() const noexcept override {
    static const game::AdapterDescriptor value{"ck3-1.20.0.2-msvc-x64", "1.20.0.2",
        kExecutableSha256, "offline-sway-invalidation-reason-named", {}};
    return value;
  }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(game::Snapshot &out) const noexcept override {
    if (GetCurrentThreadId() != owner) return false;
    out = frame;
    return true;
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

void *reason_named_tls_context = nullptr;
void *__fastcall ReasonNamedQueueTls() noexcept { return reason_named_tls_context; }
BOOL WINAPI ReasonNamedQueuePeek(LPMSG, HWND, UINT, UINT, UINT) { return FALSE; }
struct ReasonNamedProtection {
  void **slot = nullptr;
  DWORD current = PAGE_READONLY;
};
bool ReasonNamedMemoryQuery(void *opaque, const void *address,
                            MEMORY_BASIC_INFORMATION &info) noexcept {
  auto &memory = *static_cast<ReasonNamedProtection *>(opaque);
  if (address != memory.slot) return false;
  const auto start = reinterpret_cast<std::uintptr_t>(address) & ~std::uintptr_t{4095};
  info = {};
  info.BaseAddress = reinterpret_cast<void *>(start);
  info.AllocationBase = info.BaseAddress;
  info.AllocationProtect = PAGE_READONLY;
  info.RegionSize = 4096;
  info.State = MEM_COMMIT;
  info.Protect = memory.current;
  info.Type = MEM_IMAGE;
  return true;
}
bool ReasonNamedMemoryProtect(void *opaque, void *, std::size_t size,
                              DWORD protection, DWORD &previous) noexcept {
  auto &memory = *static_cast<ReasonNamedProtection *>(opaque);
  if (size != 4096) return false;
  previous = memory.current;
  memory.current = protection;
  return true;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "reason named queue artifact directory");
    const std::filesystem::path output{argv[1]};
    Fixture fixture;
    ReasonNamedInput input;
    ReasonNamedSinkContext sink;
    sink.bindings = {true, base, fixture.bindings.core, &ReasonNamedLookup,
                    &GlobalCommandKey, &reason_named_scheme_identifier,
                    &reason_named_owner_identifier, &reason_named_target_identifier};
    reason_named_original_sink = &sink;
    expected_effect = input.effect.data();
    expected_context = input.context.data();
    DWORD previous{}, ignored{};
    Check(VirtualProtect(fixture.page, 4096, PAGE_READWRITE, &previous) != FALSE,
          "fixture initializes its owned typed originals");
    for (std::size_t index = 0; index < fixture.slots.size(); ++index)
      *fixture.slots[index] = reason_named_originals[index];
    Check(VirtualProtect(fixture.page, 4096, previous, &ignored) != FALSE,
          "fixture restores readonly source-slot page before actual installation");
    Check(InstallSwayCompletionExecutionFixtureWithSecondarySink12002(
              fixture.bindings, fixture.slots, reason_named_originals,
              fixture.recorder, fixture.installation, &ReasonNamedSecondarySink, &sink) &&
          fixture.recorder.ObserverAttached() && !sink.recorder.ObserverAttached(),
          "actual three-slot installation owns the secondary reason sink");
    // This mirrors the root lifecycle only after the actual fixture slot install.
    sink.recorder.SetObserverAttached(true);
    Check(sink.recorder.ObserverAttached(), "installed fixture sink now grants reason observation");
    (*fixture.slots[1])(input.effect.data(), input.context.data());
    Check(sink.calls == 1 &&
          sink.last_capture == SwayInvalidationReasonCapture12002::captured &&
          sink.same_native_arguments && sink.source_capture_precedes_original &&
          original_calls == std::array<std::size_t, 3>{0, 1, 0} &&
          original_arguments_match,
          "actual installed toast slot captures the selected reason before typed original once");

    Put(fixture.jomini.data(), 0x20, std::uint8_t{1});
    ReasonNamedFrameAdapter adapter;
    adapter.frame.date_raw = 53220000;
    adapter.frame.paused = true;
    adapter.frame.speed = 1;
    adapter.frame.player_id = 0;
    adapter.frame.map_ready = true;
    adapter.frame.has_played_character = true;
    adapter.frame.played_character_id = actor;
    adapter.frame.played_character_alive = true;
    std::array<std::byte, 0x28> tls{};
    tls[0x20] = std::byte{1};
    reason_named_tls_context = tls.data();
    std::uint8_t tls_initialized = 1;
    std::uintptr_t unused_rng = 0;
    void *peek_slot = reinterpret_cast<void *>(&ReasonNamedQueuePeek);
    ReasonNamedProtection protection{&peek_slot};
    api::MainThreadQueryBuildProfileV1 fixture_profile{};
    fixture_profile.pump_exact_return_rva = 0x12002;
    api::MainThreadQueryInstallEnvironmentV1 environment{};
    environment.module_base = base;
    environment.exact_build_admitted = true;
    environment.offline_fixture = true;
    environment.peek_message_iat_slot_override = &peek_slot;
    environment.resolved_peek_message_override = &ReasonNamedQueuePeek;
    environment.global_rng_wrapper_slot_override = reinterpret_cast<std::uintptr_t>(&unused_rng);
    environment.jomini_state_slot_override = reinterpret_cast<std::uintptr_t>(&fixture.jomini_pointer);
    environment.game_state_slot_override = reinterpret_cast<std::uintptr_t>(&fixture.core_pointer);
    environment.tls_initialized_flag_override = reinterpret_cast<std::uintptr_t>(&tls_initialized);
    environment.tls_context_getter_override = &ReasonNamedQueueTls;
    environment.memory_protection_context = &protection;
    environment.memory_query_override = &ReasonNamedMemoryQuery;
    environment.memory_protect_override = &ReasonNamedMemoryProtect;
    environment.system_page_size_override = 4096;
    environment.executor_submission_enabled = true;
    environment.build_profile = &fixture_profile;
    environment.permitted_executor_sway_completion_invalidation_reason12002 =
        &ExecuteSwayCompletionInvalidationReasonMailboxV1;
    api::MainThreadQueryMailboxV1 mailbox;
    Check(api::InstallMainThreadQueryMailboxV1(mailbox, environment),
          "production queue Install admits the new reason callback");
    Check(mailbox.permitted_executor_sway_completion_invalidation_reason12002 ==
              &ExecuteSwayCompletionInvalidationReasonMailboxV1 &&
          mailbox.permitted_executor_sway_completion12002 == nullptr &&
          mailbox.permitted_executor_sway_completion_execution12002 == nullptr &&
          mailbox.permitted_executor_sway_completion_termination12002 == nullptr &&
          mailbox.permitted_executor == nullptr,
          "Install copies the exact reason permit while old and generic permits remain null");
    for (int pump = 0; pump < 2; ++pump)
      (void)api::ObserveMainThreadPumpAndDrainV1(
          mailbox, fixture_profile.pump_exact_return_rva, GetCurrentThreadId());
    Check(api::ReadMainThreadQueryMailboxDiagnosticsV1(mailbox).ready,
          "two actual paused owner pumps qualify reason query admission");
    SwayCompletionInvalidationReasonMailboxContextV1 query{};
    query.envelope.game = &adapter;
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = adapter.frame;
    query.envelope.expected_snapshot_revision = 7;
    query.envelope.typed_context = &query;
    query.request = ReasonNamedRequest();
    query.recorder = &sink.recorder;
    Check(api::TrySubmitMainThreadQueryV1(
              mailbox, &ExecuteSwayCompletionInvalidationReasonMailboxV1,
              &query.envelope, query.envelope.ticket) ==
              api::MainThreadQuerySubmitResultV1::submitted,
          "production TrySubmit admits the exact named reason callback");
    Check(mailbox.state == api::MainThreadQueryMailboxStateV1::queued,
          "actual queued state precedes reason execution");
    Check(api::ObserveMainThreadPumpAndDrainV1(
              mailbox, fixture_profile.pump_exact_return_rva, GetCurrentThreadId()),
          "owner pump drains the exact reason query callback");
    Check(api::WaitForMainThreadQueryV1(mailbox, query.envelope.ticket, 100) ==
              api::MainThreadQueryWaitResultV1::completed,
          "actual Wait sees the completed reason query");
    Check(query.completed && query.envelope.frame_stable && query.failure.empty() &&
          query.result.available && query.result.observer_attached &&
          query.result.records.size() == 1 && query.result.records[0].sequence == 1 &&
          query.result.records[0].source.branch ==
              SwayInvalidationNotificationBranch12002::target_dead_notification_source &&
          query.result.records[0].source.actor_character_id == actor &&
          query.result.records[0].source.target_character_id == target &&
          query.result.records[0].source.scheme_id == scheme &&
          query.result.records[0].source.selected_notification_branch_observed,
          "actual named query publishes the installed sink's copied selected notification input");
    Check(api::ReclaimMainThreadQueryV1(mailbox, query.envelope.ticket) ==
              api::MainThreadQueryReclaimResultV1::reclaimed &&
          mailbox.state == api::MainThreadQueryMailboxStateV1::idle,
          "actual completed reason query ticket reclaimed to idle");
    const auto wire = SerializeSwayCompletionInvalidationReasonCommandResultV1(
        query.result, query.envelope.expected_snapshot_revision,
        query.envelope.execution_stamp.date_raw, "reason-named-queue");
    Check(!wire.empty(), "production full reason command_result emitted after named drain");
    std::ofstream file(output / "named-reason-command-result.json");
    file << wire << '\n';
    Check(file.good(), "actual full reason command_result saved for SDK");
    Check(api::UninstallMainThreadQueryMailboxV1(mailbox, 100) ==
              api::MainThreadQueryUninstallResultV1::uninstalled,
          "fixture named reason queue released through production Uninstall");
    sink.recorder.SetObserverAttached(false);
    Check(UninstallSwayCompletionExecution12002(fixture.installation) &&
          !fixture.recorder.ObserverAttached() && !sink.recorder.ObserverAttached() &&
          fixture.installation.secondary_sink == nullptr &&
          fixture.installation.secondary_sink_context == nullptr &&
          *fixture.slots[0] == reason_named_originals[0] &&
          *fixture.slots[1] == reason_named_originals[1] &&
          *fixture.slots[2] == reason_named_originals[2],
          "root-style detach and source Uninstall clear the sink and restore typed originals");
    reason_named_tls_context = nullptr;
    reason_named_original_sink = nullptr;
    std::cout << "PASS " << checks << " checks; actual installed toast slot secondary capture, "
                 "selected notification before typed original once, named reason env/runtime Install, "
                 "two paused owner pumps, TrySubmit/drain/Wait/Reclaim, full command_result, "
                 "root detach and source/queue Uninstall; no CK3/render/native endcause claim\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
