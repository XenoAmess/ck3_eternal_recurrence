// Isolated NoGame software fixture. No image/CK3 process/ABI/live qualification.
// Compile this TU with the owner's candidate mailbox cpp, existing canonical
// mailbox-test dependencies, and the current Core-route define enabled. Do not
// link the real ExecuteReadonlyOnOwner implementation: the one symbol below is
// an explicit fake-SDK callback which mutates only FakeRuntime memory.
#if !defined(XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1) || !XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1
#error This isolated test requires the candidate current267 Core loading boundary.
#endif
#define main OldMailboxMain
#include "D:/workspace/ck3_eternal_recurrence/ck3_autonomous_player/native_bridge/src/main_thread_query_mailbox_v1_test.cpp"
#undef main
#include "xar_bridge/ck3_121003_core_loading_read_boundary26785313_v1.hpp"

namespace {
namespace cur267 = xar::ck3_121003::build26785313;
struct CurrentCoreLoadingFixture {
  // The void* sent to the candidate is exactly &core: a real ReadonlyContext,
  // never a cast of FlorinReadDriftContext to a different production layout.
  cur267::ReadonlyContext core{};
  FlorinReadDriftContext drift{};
};
CurrentCoreLoadingFixture *g_current_loading_fixture = nullptr;
}

namespace xar::ck3_121003::build26785313 {
bool ExecuteReadonlyOnOwner(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  if (!g_current_loading_fixture ||
      opaque != static_cast<void *>(&g_current_loading_fixture->core)) return false;
  return ExecuteFlorinBootstrapRead(&g_current_loading_fixture->drift, stamp);
}
}

namespace {
enum class CurrentCoreLoadingCase {
  date, pause, roots,
  control, unregistered, gui_mode, raw_mode, false_exact, wrong_mailbox,
  wrong_ticket, wrong_game_binding, wrong_jomini_binding, wrong_module,
  legacy_peek, tls_context, tls_marker, tls_global, tls_flag_address,
  after_unreadable, existing_failure, callback_failed, observation_fixture
};
const char *CaseName(CurrentCoreLoadingCase mode) noexcept {
  switch (mode) {
  case CurrentCoreLoadingCase::date: return "current_core_date_stale_no_poison";
  case CurrentCoreLoadingCase::pause: return "current_core_pause_stale_no_poison";
  case CurrentCoreLoadingCase::roots: return "current_core_roots_stale_no_poison";
  case CurrentCoreLoadingCase::control: return "current_control_drift_sticky";
  case CurrentCoreLoadingCase::unregistered: return "current_unregistered_drift_sticky";
  case CurrentCoreLoadingCase::gui_mode: return "current_gui_mode_drift_sticky";
  case CurrentCoreLoadingCase::raw_mode: return "current_raw_mode_drift_sticky";
  case CurrentCoreLoadingCase::false_exact: return "current_false_exact_drift_sticky";
  case CurrentCoreLoadingCase::wrong_mailbox: return "current_wrong_mailbox_drift_sticky";
  case CurrentCoreLoadingCase::wrong_ticket: return "current_wrong_ticket_drift_sticky";
  case CurrentCoreLoadingCase::wrong_game_binding: return "current_wrong_game_binding_drift_sticky";
  case CurrentCoreLoadingCase::wrong_jomini_binding: return "current_wrong_jomini_binding_drift_sticky";
  case CurrentCoreLoadingCase::wrong_module: return "current_wrong_module_drift_sticky";
  case CurrentCoreLoadingCase::legacy_peek: return "current_legacy_peek_drift_sticky";
  case CurrentCoreLoadingCase::tls_context: return "current_tls_context_drift_sticky";
  case CurrentCoreLoadingCase::tls_marker: return "current_tls_marker_drift_sticky";
  case CurrentCoreLoadingCase::tls_global: return "current_tls_global_drift_sticky";
  case CurrentCoreLoadingCase::tls_flag_address: return "current_tls_flag_address_drift_sticky";
  case CurrentCoreLoadingCase::after_unreadable: return "current_unreadable_after_sticky";
  case CurrentCoreLoadingCase::existing_failure: return "current_old_failure_never_cleared";
  case CurrentCoreLoadingCase::callback_failed: return "current_callback_failed_drift_sticky";
  case CurrentCoreLoadingCase::observation_fixture: return "current_fabricated_fixture_observation_sticky";
  }
  return "unknown_current_core_loading_case";
}
FlorinReadDriftCase DriftCase(CurrentCoreLoadingCase mode) noexcept {
  switch (mode) {
  case CurrentCoreLoadingCase::pause: return FlorinReadDriftCase::pause;
  case CurrentCoreLoadingCase::roots: return FlorinReadDriftCase::roots;
  case CurrentCoreLoadingCase::tls_context: return FlorinReadDriftCase::tls_context;
  case CurrentCoreLoadingCase::tls_marker: return FlorinReadDriftCase::tls_marker;
  case CurrentCoreLoadingCase::tls_global: return FlorinReadDriftCase::tls_global;
  case CurrentCoreLoadingCase::tls_flag_address: return FlorinReadDriftCase::tls_flag_address;
  case CurrentCoreLoadingCase::after_unreadable: return FlorinReadDriftCase::unreadable_after;
  case CurrentCoreLoadingCase::existing_failure: return FlorinReadDriftCase::existing_failure;
  case CurrentCoreLoadingCase::callback_failed: return FlorinReadDriftCase::callback_failed;
  default: return FlorinReadDriftCase::date;
  }
}
volatile unsigned g_control_loading_calls=0;
bool ExecuteCurrentLoadingControl(void *opaque,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  // Same fake mutation, different registered role/function address. It must not
  // borrow the exact current Core-read exception.
  g_control_loading_calls=g_control_loading_calls+1; // keep the distinct fake control address under /OPT:ICF
  return cur267::ExecuteReadonlyOnOwner(opaque, stamp);
}

bool TestCurrentCoreLoadingBoundary(CurrentCoreLoadingCase mode) {
  using namespace xar::ck3_11906;
  g_failure_stage = CaseName(mode);
  const bool recoverable = mode == CurrentCoreLoadingCase::date ||
      mode == CurrentCoreLoadingCase::pause || mode == CurrentCoreLoadingCase::roots;
  const auto owner = GetCurrentThreadId();
  FakeRuntime runtime(owner, 53'144'328);
  void *iat = reinterpret_cast<void *>(&FakePeekMessage);
  auto &mailbox = g_test_mailbox;
  MainThreadQueryMailboxV1 unrelated_mailbox{};
  static const MainThreadQueryBuildProfileV1 current_profile{
      cur267::kPeekReturnRva, cur267::kPeekMessageWIatRva,
      cur267::kRngWrapperSlotRva, cur267::kJominiStateSlotRva,
      cur267::kGameStateSlotRva, cur267::kTlsFlagRva,
      cur267::kTlsGetterRva, +[](std::uintptr_t) noexcept { return false; }};
  auto selected_profile = current_profile;
  if (mode == CurrentCoreLoadingCase::legacy_peek)
    selected_profile.pump_exact_return_rva = kSdlWindowsPumpFirstPeekReturnRva;
  auto env = runtime.Environment(0x140000000ULL, &iat, &FakePeekMessage);
  // Existing production offlineFixture install seam only. It bypasses physical
  // EXE/IAT address equality, not exact current Peek/no-Poll/context checks.
  env.build_profile = &selected_profile;
  env.permitted_executor = &cur267::ExecuteReadonlyOnOwner;
  env.permitted_executor_secondary = &ExecuteCurrentLoadingControl;
  FlorinReadObserverProbe observer{&mailbox};
  env.snapshot_observer_callback = &ObserveFlorinReadEligibility;
  env.snapshot_observer_context = &observer;
  if (!InstallMainThreadQueryMailboxV1(mailbox, env)) {std::fprintf(stderr,"installfailed flags=%u state=%u\n",mailbox.failure_flags.load(),static_cast<unsigned>(mailbox.state.load()));return false;}
  const auto cleanup = [&] {
    g_current_loading_fixture = nullptr;
    UnregisterMainThreadTimelineExecutorsV1(mailbox);
    return UninstallMainThreadQueryMailboxV1(mailbox, 10) ==
        MainThreadQueryUninstallResultV1::uninstalled;
  };
  if (!mailbox.offline_fixture || mailbox.sdl_poll_event_hook_installed.load() ||
      mailbox.sdl_poll_event_exact_return_rva != 0) {std::fprintf(stderr,"profilefailed offline=%u hook=%u poll=%llx pump=%llx\n",mailbox.offline_fixture?1u:0u,mailbox.sdl_poll_event_hook_installed.load()?1u:0u,static_cast<unsigned long long>(mailbox.sdl_poll_event_exact_return_rva),static_cast<unsigned long long>(mailbox.pump_exact_return_rva)); (void)cleanup(); return false; }
  if (mode != CurrentCoreLoadingCase::unregistered &&
      !RegisterMainThreadTimelineExecutorsV1(mailbox, &cur267::ExecuteReadonlyOnOwner,
          &ExecuteCurrentLoadingControl)) {std::fprintf(stderr,"registerfailed iat=%u\n",mailbox.iat_hook_installed.load()?1u:0u); (void)cleanup(); return false; }
  const auto pump = [&] {
    return ObserveMainThreadPumpAndDrainV1(mailbox,
        selected_profile.pump_exact_return_rva, owner);
  };
  (void)pump(); (void)pump();
  CurrentCoreLoadingFixture fixture{};
  fixture.drift.runtime = &runtime; fixture.drift.mailbox = &mailbox;
  fixture.drift.mode = DriftCase(mode); fixture.drift.apply_drift = true;
  fixture.core.mode = cur267::ReadonlyModeV1::core_only;
  fixture.core.mailbox = &mailbox;
  fixture.core.bindings.exact_image_admitted = true;
  fixture.core.bindings.module_base = mailbox.module_base;
  fixture.core.bindings.core.game_state_slot = reinterpret_cast<void **>(mailbox.game_state_slot);
  fixture.core.bindings.core.jomini_state_slot = reinterpret_cast<void **>(mailbox.jomini_state_slot);
  fixture.core.observation.offline_fixture = false;
  g_current_loading_fixture = &fixture;
  switch (mode) {
  case CurrentCoreLoadingCase::gui_mode:
    fixture.core.mode = cur267::ReadonlyModeV1::core_and_gui_window; break;
  case CurrentCoreLoadingCase::raw_mode:
    fixture.core.mode = cur267::ReadonlyModeV1::core_and_raw_resources; break;
  case CurrentCoreLoadingCase::false_exact:
    fixture.core.bindings.exact_image_admitted = false; break;
  case CurrentCoreLoadingCase::wrong_mailbox:
    fixture.core.mailbox = &unrelated_mailbox; break;
  case CurrentCoreLoadingCase::wrong_game_binding:
    fixture.core.bindings.core.game_state_slot = reinterpret_cast<void **>(&runtime.alternate_game_state); break;
  case CurrentCoreLoadingCase::wrong_jomini_binding:
    fixture.core.bindings.core.jomini_state_slot = reinterpret_cast<void **>(&runtime.alternate_jomini_state); break;
  case CurrentCoreLoadingCase::wrong_module:
    fixture.core.bindings.module_base = mailbox.module_base + 1; break;
  case CurrentCoreLoadingCase::observation_fixture:
    fixture.core.observation.offline_fixture = true; break;
  default: break;
  }
  const auto executor = mode == CurrentCoreLoadingCase::control
      ? &ExecuteCurrentLoadingControl : &cur267::ExecuteReadonlyOnOwner;
  MainThreadQueryTicketV1 original{};
  const auto started_before = mailbox.executor_started_requests.load();
  const auto executed_before = mailbox.executed_requests.load();
  bool ok = TrySubmitMainThreadQueryV1(mailbox, executor, &fixture.core, original) ==
      MainThreadQuerySubmitResultV1::submitted;
  // Only now can q.ticket refer to this real newly submitted synthetic ticket.
  fixture.core.ticket = original;
  if (mode == CurrentCoreLoadingCase::wrong_ticket) ++fixture.core.ticket.sequence;
  if (ok) ok = pump() && fixture.drift.calls == 1 && fixture.drift.observed.pump_epoch != 0 &&
      mailbox.executor_started_requests.load() == started_before + 1 &&
      mailbox.executed_requests.load() == executed_before + 1 &&
      WaitForMainThreadQueryV1(mailbox, original, 0) == MainThreadQueryWaitResultV1::infrastructure_failed &&
      mailbox.state.load() == MainThreadQueryMailboxStateV1::infrastructure_failed &&
      mailbox.completed_sequence.load() == original.sequence &&
      mailbox.owner_verified_pump_epochs.load() == 0 &&
      mailbox.paused_owner_verified_pump_epochs.load() == 0;
  const auto failure = mailbox.failure_flags.load();
  if(!ok || (recoverable && failure)) std::fprintf(stderr,"first: mode=%s ok=%u failure=%u state=%u calls=%u epochs=%llu/%llu verifier=%u\n",CaseName(mode),ok?1u:0u,failure,static_cast<unsigned>(mailbox.state.load()),fixture.drift.calls,static_cast<unsigned long long>(mailbox.owner_verified_pump_epochs.load()),static_cast<unsigned long long>(mailbox.paused_owner_verified_pump_epochs.load()),cur267::IsCurrentCoreLoadingRead267V1(mailbox,executor,&fixture.core)?1u:0u);
  ok = ok && (recoverable ? failure == 0 :
      (failure & main_thread_query_failure_post_execution_drift) != 0);
  if (mode == CurrentCoreLoadingCase::existing_failure)
    ok = ok && (failure & main_thread_query_failure_reentry) != 0;
  ok = ok && ReclaimMainThreadQueryV1(mailbox, original) ==
      MainThreadQueryReclaimResultV1::reclaimed;

  // Restore only this fixture's own synthetic memory. No production flag is
  // cleared; sticky failure_flags are asserted verbatim below.
  g_fake_tls_context = runtime.tls_context.data();
  runtime.SetTlsMarker(1); runtime.SetPaused(1); runtime.tls_initialized = 1;
  mailbox.tls_initialized_flag = reinterpret_cast<std::uintptr_t>(&runtime.tls_initialized);
  fixture.drift.apply_drift = false;
  const auto eligible_before = observer.eligible_calls;
  if (ok && recoverable) {
    MainThreadQueryTicketV1 next{};
    ok = TrySubmitMainThreadQueryV1(mailbox, executor, &fixture.core, next) ==
        MainThreadQuerySubmitResultV1::application_main_not_observed;
    (void)pump(); (void)pump();
    ok = ok && observer.eligible_calls == eligible_before &&
        TrySubmitMainThreadQueryV1(mailbox, executor, &fixture.core, next) ==
        MainThreadQuerySubmitResultV1::submitted;
    fixture.core.ticket = next;
    ok = ok && next.sequence == original.sequence + 1 && pump() && fixture.drift.calls == 2 &&
        observer.eligible_calls > eligible_before && mailbox.failure_flags.load() == 0 &&
        WaitForMainThreadQueryV1(mailbox, next, 0) == MainThreadQueryWaitResultV1::completed &&
        ReclaimMainThreadQueryV1(mailbox, next) == MainThreadQueryReclaimResultV1::reclaimed &&
        ReclaimMainThreadQueryV1(mailbox, original) == MainThreadQueryReclaimResultV1::ticket_mismatch;
  } else if (ok) {
    (void)pump(); (void)pump(); (void)pump();
    MainThreadQueryTicketV1 denied{};
    ok = mailbox.failure_flags.load() == failure && observer.eligible_calls == eligible_before &&
        fixture.drift.calls == 1 && TrySubmitMainThreadQueryV1(mailbox, executor,
        &fixture.core, denied) == MainThreadQuerySubmitResultV1::infrastructure_failed;
  }
  if(!ok) std::fprintf(stderr,"final: mode=%s failure=%u state=%u calls=%u eligible=%u/%u epochs=%llu/%llu\n",CaseName(mode),mailbox.failure_flags.load(),static_cast<unsigned>(mailbox.state.load()),fixture.drift.calls,observer.eligible_calls,eligible_before,static_cast<unsigned long long>(mailbox.owner_verified_pump_epochs.load()),static_cast<unsigned long long>(mailbox.paused_owner_verified_pump_epochs.load()));
  const bool uninstalled = cleanup();
  if (ok && uninstalled) std::printf("%s: stale-ticket rejected; recoverable=%u; no old replay\n",
      CaseName(mode), recoverable ? 1U : 0U);
  return ok && uninstalled;
}
}

int main() {
  for (const auto mode : {CurrentCoreLoadingCase::date, CurrentCoreLoadingCase::pause,
      CurrentCoreLoadingCase::roots, CurrentCoreLoadingCase::control,
      CurrentCoreLoadingCase::unregistered, CurrentCoreLoadingCase::gui_mode,
      CurrentCoreLoadingCase::raw_mode, CurrentCoreLoadingCase::false_exact,
      CurrentCoreLoadingCase::wrong_mailbox, CurrentCoreLoadingCase::wrong_ticket,
      CurrentCoreLoadingCase::wrong_game_binding, CurrentCoreLoadingCase::wrong_jomini_binding,
      CurrentCoreLoadingCase::wrong_module, CurrentCoreLoadingCase::legacy_peek,
      CurrentCoreLoadingCase::tls_context, CurrentCoreLoadingCase::tls_marker,
      CurrentCoreLoadingCase::tls_global, CurrentCoreLoadingCase::tls_flag_address,
      CurrentCoreLoadingCase::after_unreadable, CurrentCoreLoadingCase::existing_failure,
      CurrentCoreLoadingCase::callback_failed, CurrentCoreLoadingCase::observation_fixture}) {
    if (!TestCurrentCoreLoadingBoundary(mode)) {
      std::fprintf(stderr, "current Core loading fixture failed at %s\n", g_failure_stage);
      return 1;
    }
  }
  std::puts("current Core loading-boundary NoGame fixture: 3 recoverable + 19 sticky cases");
  return 0;
}
