#include "xar_bridge/route_contact_horizon_v1_dispatch.hpp"

#include <windows.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>

namespace {
using namespace xar::ck3_11906;

// Uninstall deliberately pins g_active_mailbox until process exit. Reinstall
// the same process-lifetime mailbox across cases, as the production contract
// requires; a second stack mailbox would fail the singleton install gate.
MainThreadQueryMailboxV1 g_process_fixture_mailbox{};

void *g_tls_context = nullptr;
void *__fastcall FixtureTlsContext() noexcept { return g_tls_context; }
BOOL WINAPI FixturePeekMessage(LPMSG, HWND, UINT, UINT, UINT) { return FALSE; }
int __cdecl FixtureSdlPollEvent(void *) { return 0; }

struct Protection {
  void *slot = nullptr;
  DWORD current = PAGE_READONLY;
};
bool QueryProtection(void *opaque, const void *address,
                     MEMORY_BASIC_INFORMATION &information) noexcept {
  auto &value = *static_cast<Protection *>(opaque);
  if (address != value.slot) {
    return false;
  }
  const auto page = reinterpret_cast<std::uintptr_t>(address) & ~std::uintptr_t{4095};
  information = {};
  information.BaseAddress = reinterpret_cast<void *>(page);
  information.AllocationBase = information.BaseAddress;
  information.AllocationProtect = PAGE_READONLY;
  information.RegionSize = 4096;
  information.State = MEM_COMMIT;
  information.Protect = value.current;
  information.Type = MEM_IMAGE;
  return true;
}
bool ChangeProtection(void *opaque, void *, std::size_t size,
                      DWORD requested, DWORD &previous) noexcept {
  auto &value = *static_cast<Protection *>(opaque);
  previous = value.current;
  value.current = requested;
  return size == 4096;
}

struct Runtime {
  MainThreadQueryMailboxV1 &mailbox = g_process_fixture_mailbox;
  std::array<std::byte, 0x18> rng{};
  std::uintptr_t rng_object = reinterpret_cast<std::uintptr_t>(rng.data());
  std::uintptr_t rng_wrapper = reinterpret_cast<std::uintptr_t>(&rng_object);
  std::array<std::byte, 0x28> jomini{};
  std::uintptr_t jomini_object = reinterpret_cast<std::uintptr_t>(jomini.data());
  std::array<std::byte, 0x18> game{};
  std::uintptr_t game_object = reinterpret_cast<std::uintptr_t>(game.data());
  std::array<std::byte, 0x28> tls{};
  std::uint8_t tls_initialized = 1;
  void *peek_slot = reinterpret_cast<void *>(&FixturePeekMessage);
  void *sdl_slot = reinterpret_cast<void *>(&FixtureSdlPollEvent);
  Protection protection{&peek_slot};
  void *reservation = nullptr;
  void *thunk = nullptr;
  using Pump = int(__cdecl *)(void *);
  Pump pump = nullptr;

  bool Install() {
    const std::uint8_t one = 1;
    const std::int32_t date = 53'219'928;
    std::memcpy(jomini.data() + 0x20, &one, sizeof(one));
    std::memcpy(game.data() + 0x08, &date, sizeof(date));
    std::memcpy(tls.data() + 0x20, &one, sizeof(one));
    g_tls_context = tls.data();
    // Reuse the frozen ROLE fixture's reserved exact-RVA call/return pattern
    // (owner-wake-production-fixture-a03). Read the actual installed SDL slot
    // instead of a hard-coded hook address. No direct Pump/Drain call is used.
    std::array<std::uint8_t, 24> code{
        0x48,0x83,0xEC,0x28,             // sub rsp, 28h
        0x48,0xB8,0,0,0,0,0,0,0,0,     // mov rax, &sdl_slot
        0x48,0x8B,0x00,                  // mov rax, [rax]
        0xFF,0xD0,                       // call rax; return offset 19
        0x48,0x83,0xC4,0x28,0xC3};      // add rsp, 28h; ret
    const auto slot = reinterpret_cast<std::uintptr_t>(&sdl_slot);
    std::memcpy(code.data() + 6, &slot, sizeof(slot));
    reservation = VirtualAlloc(nullptr, 0x6000000, MEM_RESERVE, PAGE_NOACCESS);
    if (reservation == nullptr) {
      return false;
    }
    auto *const base = static_cast<std::byte *>(reservation);
    void *const page = VirtualAlloc(
        base + (kHandlePdxEventsSdlPollEventReturnRva & ~std::uintptr_t{4095}),
        4096, MEM_COMMIT, PAGE_READWRITE);
    if (page == nullptr) { return false; }
    thunk = base + kHandlePdxEventsSdlPollEventReturnRva - 19;
    std::memcpy(thunk, code.data(), code.size());
    DWORD old = 0;
    if (!VirtualProtect(page, 4096, PAGE_EXECUTE_READ, &old) ||
        !FlushInstructionCache(GetCurrentProcess(), thunk, code.size())) {
      return false;
    }
    pump = reinterpret_cast<Pump>(thunk);
    MainThreadQueryInstallEnvironmentV1 environment{};
    environment.module_base = reinterpret_cast<std::uintptr_t>(reservation);
    environment.exact_build_admitted = true;
    environment.offline_fixture = true;
    environment.peek_message_iat_slot_override = &peek_slot;
    environment.resolved_peek_message_override = &FixturePeekMessage;
    environment.global_rng_wrapper_slot_override = reinterpret_cast<std::uintptr_t>(&rng_wrapper);
    environment.jomini_state_slot_override = reinterpret_cast<std::uintptr_t>(&jomini_object);
    environment.game_state_slot_override = reinterpret_cast<std::uintptr_t>(&game_object);
    environment.tls_initialized_flag_override = reinterpret_cast<std::uintptr_t>(&tls_initialized);
    environment.tls_context_getter_override = &FixtureTlsContext;
    environment.memory_protection_context = &protection;
    environment.memory_query_override = &QueryProtection;
    environment.memory_protect_override = &ChangeProtection;
    environment.system_page_size_override = 4096;
    environment.executor_submission_enabled = true;
    environment.permitted_executor = &ExecuteRouteContactHorizonMailboxQueryV1;
    environment.sdl_poll_event_slot_override = &sdl_slot;
    environment.resolved_sdl_poll_event_override = &FixtureSdlPollEvent;
    const bool installed = InstallMainThreadQueryMailboxV1(mailbox, environment);
    if (!installed) {
      const auto diagnostics = ReadMainThreadQueryMailboxDiagnosticsV1(mailbox);
      std::fprintf(stderr, "fixture install failed: state=%u failure_flags=%u\n",
                   static_cast<unsigned>(diagnostics.state), diagnostics.failure_flags);
    }
    return installed;
  }

  bool Close() {
    const auto result = UninstallMainThreadQueryMailboxV1(mailbox, 2'000);
    if (reservation != nullptr) {
      (void)VirtualFree(reservation, 0, MEM_RELEASE);
      reservation = nullptr;
      thunk = nullptr;
    }
    return result == MainThreadQueryUninstallResultV1::uninstalled &&
        peek_slot == reinterpret_cast<void *>(&FixturePeekMessage) &&
        sdl_slot == reinterpret_cast<void *>(&FixtureSdlPollEvent);
  }
};

bool Check(bool condition, const char *name) {
  if (!condition) {
    std::fprintf(stderr, "FAIL %s\n", name);
  }
  return condition;
}

struct Owner {
  Runtime *runtime = nullptr;
  HANDLE ready = nullptr;
  UINT first_message = 0;
  UINT retry_message = 0;
  bool first_still_queued = false;
  std::uint64_t starts_before_retry = 99;
};

DWORD WINAPI OwnerAfterRetry(void *opaque) {
  auto &owner = *static_cast<Owner *>(opaque);
  MSG message{};
  (void)PeekMessageW(&message, nullptr, 0, 0, PM_NOREMOVE);
  owner.runtime->pump(nullptr);
  owner.runtime->pump(nullptr);
  SetEvent(owner.ready);
  if (GetMessageW(&message, nullptr, 0, 0) <= 0) {
    return 1;
  }
  owner.first_message = message.message;
  const auto first = ReadMainThreadQueryMailboxDiagnosticsV1(owner.runtime->mailbox);
  owner.first_still_queued = first.state == MainThreadQueryMailboxStateV1::queued;
  owner.starts_before_retry = first.executor_started_requests;
  // Intentionally consume the initial wake without entering the SDL hook.
  if (GetMessageW(&message, nullptr, 0, 0) <= 0) {
    return 2;
  }
  owner.retry_message = message.message;
  owner.runtime->pump(nullptr);
  return 0;
}

void PrepareQuery(Runtime &runtime, RouteContactHorizonMailboxContextV1 &query) {
  query.mailbox = &runtime.mailbox;
  query.request.subject_army_id = 83'886'367;
  query.request.target_province_id = 2610;
  query.request.hostile_army_ids = {16'777'218};
  query.physical_inventory_requested = true;
  query.physical_inventory_war_id = 3937;
  // bindings.enabled remains false: execute the real callback, but never
  // substitute a fake available route or physical inventory certificate.
}

bool RetryEntersActualCallback() {
  Runtime runtime;
  if (!Check(runtime.Install(), "retry_install")) {
    return false;
  }
  HANDLE ready = CreateEventW(nullptr, TRUE, FALSE, nullptr);
  Owner owner{&runtime, ready};
  DWORD thread_id = 0;
  HANDLE thread = ready == nullptr ? nullptr :
      CreateThread(nullptr, 0, &OwnerAfterRetry, &owner, 0, &thread_id);
  if (thread == nullptr || WaitForSingleObject(ready, 2'000) != WAIT_OBJECT_0) {
    if (thread != nullptr) {
      (void)PostThreadMessageW(thread_id, WM_QUIT, 0, 0);
      (void)WaitForSingleObject(thread, 2'000);
      CloseHandle(thread);
    }
    if (ready != nullptr) { CloseHandle(ready); }
    (void)runtime.Close();
    return Check(false, "retry_owner_ready");
  }
  RouteContactHorizonMailboxContextV1 query;
  PrepareQuery(runtime, query);
  MainThreadQueryQueuedWakeTraceV1 trace{};
  const auto before = ReadMainThreadQueryMailboxDiagnosticsV1(runtime.mailbox);
  const auto submitted = SubmitRouteContactHorizonQueryV1(query, trace);
  const auto initial_trace = trace;
  const auto wait = submitted == MainThreadQuerySubmitResultV1::submitted ?
      WaitForRouteContactHorizonQueryV1(query, trace) :
      MainThreadQueryWaitResultV1::ticket_mismatch;
  const auto after = ReadMainThreadQueryMailboxDiagnosticsV1(runtime.mailbox);
  auto joined = WaitForSingleObject(thread, 2'000);
  if (joined != WAIT_OBJECT_0) {
    (void)PostThreadMessageW(thread_id, WM_QUIT, 0, 0);
    joined = WaitForSingleObject(thread, 2'000);
  }
  DWORD exit_code = STILL_ACTIVE;
  (void)GetExitCodeThread(thread, &exit_code);
  CloseHandle(thread);
  CloseHandle(ready);
  const auto reclaimed = ReclaimMainThreadQueryV1(runtime.mailbox, query.ticket);
  const auto closed = runtime.Close();
  return Check(before.ready && before.sdl_poll_event_hook_installed,
               "retry_installed_hook_ready") &&
      Check(submitted == MainThreadQuerySubmitResultV1::submitted &&
            wait == MainThreadQueryWaitResultV1::completed, "retry_terminal") &&
      Check(joined == WAIT_OBJECT_0 && exit_code == 0 &&
            owner.first_message == WM_NULL && owner.retry_message == WM_NULL &&
            owner.first_still_queued && owner.starts_before_retry == 0,
            "initial_wake_did_not_execute") &&
      Check(initial_trace.wake_attempts == 1 && trace.owner_thread_id == before.owner_thread_id &&
            trace.wake_attempts >= 2 && trace.wake_failed == 0 &&
            trace.wake_succeeded == trace.wake_attempts &&
            trace.pump_epoch_at_end > trace.pump_epoch_at_start,
            "retry_wake_and_hook_pump") &&
      Check(query.executor_invocations == 1 &&
            query.completion == RouteContactHorizonMailboxCompletionV1::query_unavailable &&
            query.result.status == xar::game::RouteContactHorizonStatus::unavailable &&
            after.executor_started_requests == 1 && after.executed_requests == 1 &&
            after.executor_started_sequence == query.ticket.sequence &&
            after.completed_sequence == query.ticket.sequence,
            "actual_h3_callback_once_without_semantic_green") &&
      Check(query.physical_inventory_requested && !query.physical_inventory_same_source &&
            query.physical_inventory_before_read_status == PhysicalArmyInventoryStatusV1::unavailable &&
            query.physical_inventory_after_read_status == PhysicalArmyInventoryStatusV1::unavailable,
            "physical_inventory_remains_unavailable") &&
      Check(reclaimed == MainThreadQueryReclaimResultV1::reclaimed && closed,
            "retry_reclaim_cleanup");
}

bool QueuedBudgetCancelsWithBoundNegativeFrame() {
  Runtime runtime;
  if (!Check(runtime.Install(), "cancel_install")) { return false; }
  MSG ignored{};
  (void)PeekMessageW(&ignored, nullptr, 0, 0, PM_NOREMOVE);
  runtime.pump(nullptr);
  runtime.pump(nullptr);
  RouteContactHorizonMailboxContextV1 query;
  PrepareQuery(runtime, query);
  MainThreadQueryQueuedWakeTraceV1 trace{};
  const auto before = ReadMainThreadQueryMailboxDiagnosticsV1(runtime.mailbox);
  const auto submitted = SubmitRouteContactHorizonQueryV1(query, trace);
  const auto initial_trace = trace;
  const auto started = GetTickCount64();
  const auto wait = submitted == MainThreadQuerySubmitResultV1::submitted ?
      WaitForRouteContactHorizonQueryV1(query, trace) :
      MainThreadQueryWaitResultV1::ticket_mismatch;
  const auto elapsed = GetTickCount64() - started;
  const auto after = ReadMainThreadQueryMailboxDiagnosticsV1(runtime.mailbox);
  const auto error = RouteContactHorizonFailureDetailV1(
      wait, query.completion, query.result, false);
  const std::string bare = "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":\"h3937-fixture\",\"ok\":false,\"error\":\"" + error + "\"}";
  const auto frame = RouteContactHorizonNegativeFrameWithDispatchV1(
      bare, wait, query, trace, initial_trace, before, after);
  std::puts(frame.c_str());
  const auto reclaimed = ReclaimMainThreadQueryV1(runtime.mailbox, query.ticket);
  const auto closed = runtime.Close();
  return Check(before.ready && submitted == MainThreadQuerySubmitResultV1::submitted,
               "cancel_submitted_ready") &&
      Check(wait == MainThreadQueryWaitResultV1::timeout_cancelled_before_execution &&
            elapsed >= 8'000 && after.state == MainThreadQueryMailboxStateV1::cancelled,
            "actual_8000ms_queued_cancel") &&
      Check(after.published_sequence == query.ticket.sequence &&
            after.completed_sequence == query.ticket.sequence &&
            query.executor_invocations == 0 && after.executor_started_requests == 0 &&
            after.executed_requests == 0 &&
            trace.pump_epoch_at_start == trace.pump_epoch_at_end &&
            trace.wake_attempts >= 2 &&
            trace.wake_attempts == trace.wake_succeeded + trace.wake_failed,
            "cancel_no_callback_and_ticket_identity") &&
      Check(error == "application-main route-contact query timed out before execution" &&
            frame.find("\"ok\":false") != std::string::npos &&
            frame.find("\"route_contact_dispatch_v1\":{") != std::string::npos &&
            frame.find("\"ticket_sequence\":" + std::to_string(query.ticket.sequence)) != std::string::npos &&
            frame.find("\"wait\":" + std::to_string(static_cast<std::uint32_t>(wait))) != std::string::npos &&
            frame.find("\"wake_attempts\":" + std::to_string(trace.wake_attempts)) != std::string::npos &&
            frame.find("\"initial_wake_attempts\":1") != std::string::npos &&
            frame.find("\"queued_wake_attempts\":" + std::to_string(trace.wake_attempts-1)) != std::string::npos &&
            frame.find("\"total_wake_attempts\":" + std::to_string(trace.wake_attempts)) != std::string::npos &&
            frame.find("\"wake_owner_thread_id\":" + std::to_string(before.owner_thread_id)) != std::string::npos &&
            frame.find("\"queued_wait_budget_ms\":8000") != std::string::npos &&
            frame.find("\"executing_wait_slice_ms\":2000") != std::string::npos &&
            frame.find("\"queued_wake_interval_ms\":250") != std::string::npos &&
            frame.find("\"executor_invocations\":0") != std::string::npos &&
            frame.find("\"after_wait_before_reclaim\":{\"state\":" +
                       std::to_string(static_cast<std::uint32_t>(after.state))) != std::string::npos,
            "negative_sibling_binds_actual_cancel_fields") &&
      Check(RouteContactHorizonNegativeFrameWithDispatchV1(
            "{\"ok\":true,\"result\":{}}", wait, query, trace, initial_trace, before, after) ==
            "{\"ok\":true,\"result\":{}}", "success_frame_unchanged") &&
      Check(reclaimed == MainThreadQueryReclaimResultV1::reclaimed && closed,
            "cancel_reclaim_cleanup");
}
} // namespace

int main() {
  if (!RetryEntersActualCallback()) {
    return 1;
  }
  std::puts("PASS initial wake skipped hook then retry entered actual H3 callback; reclaimed/uninstalled");
  if (!QueuedBudgetCancelsWithBoundNegativeFrame()) {
    return 1;
  }
  std::puts("PASS h3937 actual SDL hook callback retry and 8000ms queued cancellation");
  return 0;
}
