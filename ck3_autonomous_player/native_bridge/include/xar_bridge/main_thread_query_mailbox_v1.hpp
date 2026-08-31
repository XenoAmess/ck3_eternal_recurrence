#pragma once

#include <windows.h>

#include <atomic>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_11906 {

// This is infrastructure, not a gameplay capability.  It remains completely
// absent from the advertised command set until an exact-build paused live
// fixture has observed the pump and a concrete query has its own full reader
// contract.
inline constexpr bool kMainThreadQueryMailboxV1CapabilityAdvertised = false;
inline constexpr std::string_view kMainThreadQueryMailboxV1CandidateId =
    "application_main_thread_war_entry_v1";
inline constexpr std::string_view kMainThreadQueryMailboxV1AdapterId =
    "ck3-1.19.0.6-msvc-x64";
inline constexpr std::string_view kMainThreadQueryMailboxV1ExecutableSha256 =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";

// CK3 1.19.0.6 embeds SDL.  The Windows video-device constructor stores the
// exact pump at +0x238; SDL_PumpEvents reaches that slot before event dequeue.
inline constexpr std::uintptr_t kSdlWindowsVideoDevicePumpInstallRva =
    0x3CFE7AB;
inline constexpr std::uintptr_t kSdlPumpEventsRva = 0x3CD3600;
inline constexpr std::uintptr_t kSdlWindowsPumpFunctionRva = 0x3CE41E0;
inline constexpr std::uintptr_t kSdlWindowsPumpFirstPeekCallRva = 0x3CE421C;
inline constexpr std::uintptr_t kSdlWindowsPumpFirstPeekReturnRva = 0x3CE4222;
inline constexpr std::uintptr_t kPeekMessageWIatSlotRva = 0x3FD2EE8;

// The native global RNG wrapper is a generic scoped-owner diagnostic.  It is
// not an admission gate for this application-main-thread boundary: the live
// SDL observation proved the HandlePdxEvents TLS marker while a different
// subsystem owned this wrapper.  The mailbox mirrors the value and never
// draws RNG.
inline constexpr std::uintptr_t kGlobalRngWrapperSlotRva = 0x4FEB1C8;
inline constexpr std::size_t kGlobalRngWrapperStateOffset = 0x00;
inline constexpr std::size_t kGlobalRngOwnerThreadIdOffset = 0x10;
inline constexpr std::uintptr_t kNativeRngOwnerThreadCheckRva = 0x356A0A0;
inline constexpr std::uintptr_t kGetCurrentThreadIdThunkRva = 0x3D00000;
inline constexpr std::uintptr_t kGetCurrentThreadIdIatSlotRva = 0x3FD2570;

// RNG ownership alone is not a main-thread proof: 0x356B600 is a generic
// owner-acquire path.  HandlePdxEvents independently requires this initialized
// global and the current thread's native TLS marker at +0x20.
inline constexpr std::uintptr_t kMainThreadTlsInitializedFlagRva = 0x57727ED;
inline constexpr std::uintptr_t kMainThreadTlsContextGetterRva = 0x3B86430;
inline constexpr std::size_t kMainThreadTlsMarkerOffset = 0x20;
inline constexpr std::uintptr_t kMainThreadTlsStartupStoreRva = 0x7E7CDE;
inline constexpr std::uintptr_t kHandlePdxEventsRva = 0x3A2EC30;
inline constexpr std::uintptr_t kHandlePdxEventsTlsGateRva = 0x3A2EC4D;

inline constexpr std::uintptr_t kJominiStateSlotRva = 0x570F7B8;
inline constexpr std::size_t kJominiPausedOffset = 0x20;
inline constexpr std::uintptr_t kGameStateSlotRva = 0x570E068;
inline constexpr std::size_t kGameStateDateRawOffset = 0x08;

inline constexpr std::uint32_t kMainThreadQueryMaximumDrainPerPump = 1;
inline constexpr std::uint64_t
    kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs = 2;

using PeekMessageWFunctionV1 =
    BOOL(WINAPI *)(LPMSG, HWND, UINT, UINT, UINT);

struct MainThreadExecutionStampV1 {
  std::uint64_t pump_epoch = 0;
  std::uint32_t thread_id = 0;
  std::uintptr_t rng_wrapper = 0;
  std::uintptr_t rng_state = 0;
  std::uint32_t rng_owner_thread_id = 0;
  std::uintptr_t tls_initialized_flag_address = 0;
  std::uint8_t tls_initialized = 0;
  std::uintptr_t tls_context = 0;
  std::uint8_t tls_main_thread_marker = 0;
  std::uintptr_t jomini_state = 0;
  std::uintptr_t game_state = 0;
  std::int32_t date_raw = 0;
  bool paused = false;

  friend bool operator==(const MainThreadExecutionStampV1 &,
                         const MainThreadExecutionStampV1 &) = default;
};

// Query-specific storage belongs to the bridge worker and must outlive the
// ticket until a terminal state is reclaimed.  The executor runs synchronously
// on the proven CK3 application main thread.  Returning false means only an
// infrastructure/executor failure; a valid query-specific unavailable result
// must be stored in context and return true.
using MainThreadQueryExecutorV1 = bool (*)(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept;

enum class MainThreadQueryMailboxStateV1 : std::uint32_t {
  detached = 0,
  idle = 1,
  publishing = 2,
  queued = 3,
  executing = 4,
  completed = 5,
  executor_failed = 6,
  cancelled = 7,
  infrastructure_failed = 8,
  detaching = 9,
};

enum MainThreadQueryMailboxFailureV1 : std::uint32_t {
  main_thread_query_failure_none = 0,
  main_thread_query_failure_exact_build = 1U << 0,
  main_thread_query_failure_pump_anchor = 1U << 1,
  main_thread_query_failure_iat_identity = 1U << 2,
  main_thread_query_failure_singleton = 1U << 3,
  main_thread_query_failure_runtime_identity = 1U << 4,
  main_thread_query_failure_thread_identity = 1U << 5,
  main_thread_query_failure_not_paused = 1U << 6,
  main_thread_query_failure_reentry = 1U << 7,
  main_thread_query_failure_request_identity = 1U << 8,
  main_thread_query_failure_executor_exception = 1U << 9,
  main_thread_query_failure_post_execution_drift = 1U << 10,
  main_thread_query_failure_iat_page_identity = 1U << 11,
  main_thread_query_failure_iat_page_protect = 1U << 12,
  main_thread_query_failure_uninstall = 1U << 13,
  main_thread_query_failure_tls_identity = 1U << 14,
};

enum class MainThreadQueryUninstallResultV1 : std::uint32_t {
  uninstalled = 0,
  not_installed = 1,
  request_active = 2,
  iat_restore_failed = 3,
  active_hook_calls_pending = 4,
  wrong_mailbox = 5,
};

enum class MainThreadQuerySubmitResultV1 : std::uint32_t {
  submitted = 0,
  invalid_request = 1,
  mailbox_not_installed = 2,
  paused_main_thread_not_observed = 3,
  mailbox_busy = 4,
  infrastructure_failed = 5,
  executor_submission_disabled = 6,
};

enum class MainThreadQueryCancelResultV1 : std::uint32_t {
  cancelled = 0,
  already_terminal = 1,
  executing = 2,
  ticket_mismatch = 3,
};

enum class MainThreadQueryReclaimResultV1 : std::uint32_t {
  reclaimed = 0,
  not_terminal = 1,
  ticket_mismatch = 2,
};

enum class MainThreadQueryWaitResultV1 : std::uint32_t {
  completed = 0,
  executor_failed = 1,
  infrastructure_failed = 2,
  cancelled = 3,
  timeout_cancelled_before_execution = 4,
  timeout_executor_already_running = 5,
  ticket_mismatch = 6,
};

struct MainThreadQueryTicketV1 {
  std::uint64_t sequence = 0;
};

using MainThreadMemoryQueryV1 = bool (*)(
    void *context, const void *address,
    MEMORY_BASIC_INFORMATION &information) noexcept;
using MainThreadMemoryProtectV1 = bool (*)(
    void *context, void *page_address, std::size_t page_size,
    DWORD new_protect, DWORD &old_protect) noexcept;
using MainThreadTlsContextGetterV1 = void *(__fastcall *)() noexcept;

// The production binder uses module_base plus the frozen RVAs.  The explicit
// override surface exists only so the offline fixture can exercise atomic IAT
// installation and queue state transitions without mapping a 0x5C2D000-byte
// CK3 image.
struct MainThreadQueryInstallEnvironmentV1 {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  bool offline_fixture = false;
  void **peek_message_iat_slot_override = nullptr;
  PeekMessageWFunctionV1 resolved_peek_message_override = nullptr;
  std::uintptr_t global_rng_wrapper_slot_override = 0;
  std::uintptr_t jomini_state_slot_override = 0;
  std::uintptr_t game_state_slot_override = 0;
  std::uintptr_t tls_initialized_flag_override = 0;
  MainThreadTlsContextGetterV1 tls_context_getter_override = nullptr;
  void *memory_protection_context = nullptr;
  MainThreadMemoryQueryV1 memory_query_override = nullptr;
  MainThreadMemoryProtectV1 memory_protect_override = nullptr;
  std::size_t system_page_size_override = 0;
  bool executor_submission_enabled = false;
  // At least one slot is non-null in production.  These exact typed callback
  // identities prevent the infrastructure from becoming a generic native-call
  // trampoline. V1 has fourteen fixed slots for the bounded war-entry,
  // route-contact, actual-contact, combat-v3, ongoing-battle, full-CombatID
  // lifecycle, campaign-root, loaded-feature and pending-interaction read-only
  // current-event-window read-only and explicit title-map presentation
  // executors.
  MainThreadQueryExecutorV1 permitted_executor = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_secondary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_tertiary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_quaternary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_quinary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_senary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_septenary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_octonary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_nonary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_denary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_undenary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_duodenary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_thirdenary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_quattuordenary = nullptr;
};

struct MainThreadQueryMailboxDiagnosticsV1 {
  MainThreadQueryMailboxStateV1 state =
      MainThreadQueryMailboxStateV1::detached;
  std::uint32_t failure_flags = 0;
  std::uint64_t pump_epochs = 0;
  std::uint64_t paused_owner_verified_pump_epochs = 0;
  std::uint64_t executed_requests = 0;
  std::uint64_t completed_sequence = 0;
  std::uint32_t owner_thread_id = 0;
  std::uint32_t observed_current_thread_id = 0;
  std::uint32_t observed_rng_owner_thread_id = 0;
  std::uintptr_t observed_tls_context = 0;
  std::uintptr_t observed_jomini_state = 0;
  std::uintptr_t observed_game_state = 0;
  std::int32_t observed_date_raw = 0;
  std::uint8_t observed_tls_initialized = 0;
  std::uint8_t observed_tls_main_thread_marker = 0;
  bool observed_paused = false;
  bool observed_stamp_read_success = false;
  std::uint32_t active_hook_calls = 0;
  bool iat_installed = false;
  bool stop_requested = false;
  bool executor_submission_enabled = false;
  bool paused_main_thread_observed = false;
  bool ready = false;
};

struct MainThreadQueryMailboxV1 {
  std::atomic<MainThreadQueryMailboxStateV1> state{
      MainThreadQueryMailboxStateV1::detached};
  std::atomic<std::uint32_t> failure_flags{0};
  std::atomic<std::uint64_t> next_sequence{0};
  std::atomic<std::uint64_t> published_sequence{0};
  std::atomic<std::uint64_t> completed_sequence{0};
  std::atomic<std::uint64_t> pump_epochs{0};
  std::atomic<std::uint64_t> paused_owner_verified_pump_epochs{0};
  std::atomic<std::uint64_t> executed_requests{0};
  std::atomic<std::uint32_t> owner_thread_id{0};
  std::atomic<std::uint32_t> observed_current_thread_id{0};
  std::atomic<std::uint32_t> observed_rng_owner_thread_id{0};
  std::atomic<std::uintptr_t> observed_tls_context{0};
  std::atomic<std::uintptr_t> observed_jomini_state{0};
  std::atomic<std::uintptr_t> observed_game_state{0};
  std::atomic<std::int32_t> observed_date_raw{0};
  std::atomic<std::uint8_t> observed_tls_initialized{0};
  std::atomic<std::uint8_t> observed_tls_main_thread_marker{0};
  std::atomic<bool> observed_paused{false};
  std::atomic<bool> observed_stamp_read_success{false};
  std::atomic<std::uint32_t> active_hook_calls{0};
  std::atomic<bool> stop_requested{false};
  std::atomic<bool> iat_hook_installed{false};
  std::atomic<bool> proof_reset_requested{false};
  std::atomic_flag drain_guard = ATOMIC_FLAG_INIT;

  // Immutable after successful installation.
  std::uintptr_t module_base = 0;
  void **peek_message_iat_slot = nullptr;
  PeekMessageWFunctionV1 original_peek_message = nullptr;
  std::uintptr_t global_rng_wrapper_slot = 0;
  std::uintptr_t jomini_state_slot = 0;
  std::uintptr_t game_state_slot = 0;
  std::uintptr_t tls_initialized_flag = 0;
  MainThreadTlsContextGetterV1 tls_context_getter = nullptr;
  void *memory_protection_context = nullptr;
  MainThreadMemoryQueryV1 memory_query = nullptr;
  MainThreadMemoryProtectV1 memory_protect = nullptr;
  std::size_t system_page_size = 0;
  bool offline_fixture = false;
  bool executor_submission_enabled = false;
  MainThreadQueryExecutorV1 permitted_executor = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_secondary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_tertiary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_quaternary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_quinary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_senary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_septenary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_octonary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_nonary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_denary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_undenary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_duodenary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_thirdenary = nullptr;
  MainThreadQueryExecutorV1 permitted_executor_quattuordenary = nullptr;

  // Written only inside the exact-return drain guard.  The worker consumes
  // only the atomic consecutive count; this stamp never crosses threads.
  MainThreadExecutionStampV1 last_verified_stamp{};
  bool last_verified_stamp_valid = false;

  // Single-producer/single-consumer slot.  The publishing/queued release-store
  // is the ownership boundary for these plain fields.
  MainThreadQueryExecutorV1 executor = nullptr;
  void *executor_context = nullptr;
  bool executor_succeeded = false;
  MainThreadExecutionStampV1 execution_stamp{};
};

bool InstallMainThreadQueryMailboxV1(
    MainThreadQueryMailboxV1 &mailbox,
    const MainThreadQueryInstallEnvironmentV1 &environment) noexcept;

// WorkerMain owns installation and must call this on every return path before
// XarCk3BridgeStop resets its worker lifecycle.  Success means the IAT contains
// the original PeekMessageW and every hook invocation already counted has
// returned.  It does NOT make FreeLibrary safe: a thread can have fetched the
// old IAT target without entering the hook yet.  V1 therefore pins this module,
// the mailbox and the original function pointer until CK3 process exit.  A
// timeout keeps the bridge lifecycle in stopping and may be retried.
MainThreadQueryUninstallResultV1 UninstallMainThreadQueryMailboxV1(
    MainThreadQueryMailboxV1 &mailbox,
    std::uint32_t active_call_drain_timeout_milliseconds) noexcept;

// PROCESS_DETACH may only signal.  It must never wait under the loader lock.
// Normal bridge shutdown still requires UninstallMainThreadQueryMailboxV1.
void SignalMainThreadQueryMailboxProcessDetachV1(
    MainThreadQueryMailboxV1 &mailbox) noexcept;

MainThreadQuerySubmitResultV1 TrySubmitMainThreadQueryV1(
    MainThreadQueryMailboxV1 &mailbox, MainThreadQueryExecutorV1 executor,
    void *context, MainThreadQueryTicketV1 &ticket) noexcept;

MainThreadQueryCancelResultV1 CancelMainThreadQueryV1(
    MainThreadQueryMailboxV1 &mailbox,
    const MainThreadQueryTicketV1 &ticket) noexcept;

// The timeout can atomically cancel only a still-queued request.  Once the
// main thread owns the slot, the executor must finish synchronously and the
// caller must retain context until a later terminal observation/reclaim.
MainThreadQueryWaitResultV1 WaitForMainThreadQueryV1(
    MainThreadQueryMailboxV1 &mailbox,
    const MainThreadQueryTicketV1 &ticket,
    std::uint32_t timeout_milliseconds) noexcept;

MainThreadQueryReclaimResultV1 ReclaimMainThreadQueryV1(
    MainThreadQueryMailboxV1 &mailbox,
    const MainThreadQueryTicketV1 &ticket) noexcept;

// Exact boundary surface used by the IAT hook and deterministic fixtures.
// It drains at most one request and returns true only when an executor ran.
bool ObserveMainThreadPumpAndDrainV1(
    MainThreadQueryMailboxV1 &mailbox, std::uintptr_t return_rva,
    std::uint32_t current_thread_id) noexcept;

MainThreadQueryMailboxDiagnosticsV1 ReadMainThreadQueryMailboxDiagnosticsV1(
    const MainThreadQueryMailboxV1 &mailbox) noexcept;

extern "C" BOOL WINAPI XarMainThreadPeekMessageWHookV1(
    LPMSG message, HWND window, UINT minimum_filter, UINT maximum_filter,
    UINT remove_message) noexcept;

} // namespace xar::ck3_11906
