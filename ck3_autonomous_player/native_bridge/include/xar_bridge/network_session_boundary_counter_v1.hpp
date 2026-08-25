#pragma once

#include <windows.h>

#include <atomic>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_11906 {

// Diagnostic-only exact-build probe.  It is deliberately not a gameplay
// capability and has no request/executor surface.
inline constexpr bool kNetworkSessionBoundaryCounterV1CapabilityAdvertised =
    false;
inline constexpr bool kNetworkSessionBoundaryCounterV1ExecutorSubmission =
    false;
inline constexpr std::string_view kNetworkSessionBoundaryCounterV1CandidateId =
    "network_session_post_lock_v1";
inline constexpr std::string_view kNetworkSessionBoundaryCounterV1AdapterId =
    "ck3-1.19.0.6-msvc-x64";
inline constexpr std::string_view
    kNetworkSessionBoundaryCounterV1ExecutableSha256 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";

inline constexpr std::uintptr_t kReleaseSrwLockExclusiveIatSlotRva =
    0x3FD2658;
inline constexpr std::uintptr_t kAcquireSrwLockExclusiveIatSlotRva =
    0x3FD2668;
inline constexpr std::uintptr_t kTryAcquireSrwLockExclusiveIatSlotRva =
    0x3FD2660;
inline constexpr std::uintptr_t kNetworkSessionManagerRva = 0x57621F0;
inline constexpr std::uintptr_t kNetworkSessionThreadNameRva = 0x44E0650;
inline constexpr std::uintptr_t kNetworkSessionManagerConstructorRva =
    0x341CC80;
inline constexpr std::uintptr_t kNetworkSessionLoopStartRva = 0x341D6A0;
inline constexpr std::uintptr_t kNetworkSessionCallbackInstallRva = 0x341D85A;
inline constexpr std::uintptr_t kNativeThreadCreateRva = 0x3BC9CC0;
inline constexpr std::uintptr_t kNativeThreadNameTrampolineRva = 0x3BC9C10;
inline constexpr std::uintptr_t kNetworkSessionThreadProcedureRva = 0x3BB9660;
inline constexpr std::uintptr_t kNetworkSessionIterationRva = 0x3423410;
inline constexpr std::uintptr_t kNetworkSessionStateMachineCallRva =
    0x34234C9;
inline constexpr std::uintptr_t kNetworkSessionMainLockAcquireRva =
    0x342347C;
inline constexpr std::uintptr_t kNetworkSessionMainLockReleaseRva =
    0x3423770;
inline constexpr std::uintptr_t kNetworkSessionPostLockReturnRva =
    0x3423776;
inline constexpr std::uintptr_t kNetworkSessionIterationTrueRva = 0x34237D7;

inline constexpr std::uintptr_t kGlobalRngWrapperSlotRva = 0x4FEB1C8;
inline constexpr std::size_t kGlobalRngWrapperStateOffset = 0x00;
inline constexpr std::size_t kGlobalRngOwnerThreadIdOffset = 0x10;
inline constexpr std::uintptr_t kMainThreadTlsInitializedFlagRva = 0x57727ED;
inline constexpr std::uintptr_t kMainThreadTlsContextGetterRva = 0x3B86430;
inline constexpr std::size_t kMainThreadTlsMarkerOffset = 0x20;
inline constexpr std::uintptr_t kJominiStateSlotRva = 0x570F7B8;
inline constexpr std::size_t kJominiPausedOffset = 0x20;
inline constexpr std::uintptr_t kGameStateSlotRva = 0x570E068;
inline constexpr std::size_t kGameStateDateRawOffset = 0x08;
inline constexpr std::uint64_t
    kNetworkSessionBoundaryMinimumConsecutiveVerifiedEpochs = 2;

using ReleaseSrwLockExclusiveFunctionV1 = VOID(WINAPI *)(PSRWLOCK);
using NetworkSessionTlsContextGetterV1 = void *(__fastcall *)() noexcept;
using NetworkSessionMemoryQueryV1 = bool (*)(
    void *context, const void *address,
    MEMORY_BASIC_INFORMATION &information) noexcept;
using NetworkSessionMemoryProtectV1 = bool (*)(
    void *context, void *page_address, std::size_t page_size,
    DWORD new_protect, DWORD &old_protect) noexcept;

enum NetworkSessionBoundaryCounterFailureV1 : std::uint32_t {
  network_session_boundary_failure_none = 0,
  network_session_boundary_failure_exact_build = 1U << 0,
  network_session_boundary_failure_anchor = 1U << 1,
  network_session_boundary_failure_iat_identity = 1U << 2,
  network_session_boundary_failure_singleton = 1U << 3,
  network_session_boundary_failure_page_identity = 1U << 4,
  network_session_boundary_failure_page_protect = 1U << 5,
  network_session_boundary_failure_runtime_read = 1U << 6,
  network_session_boundary_failure_reentry = 1U << 7,
  network_session_boundary_failure_uninstall = 1U << 8,
};

enum class NetworkSessionBoundaryUninstallResultV1 : std::uint32_t {
  uninstalled = 0,
  not_installed = 1,
  active_hook_calls_pending = 2,
  iat_restore_failed = 3,
  wrong_counter = 4,
};

struct NetworkSessionBoundaryInstallEnvironmentV1 {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  bool offline_fixture = false;
  void **release_srw_iat_slot_override = nullptr;
  ReleaseSrwLockExclusiveFunctionV1 resolved_release_srw_override = nullptr;
  std::uintptr_t global_rng_wrapper_slot_override = 0;
  std::uintptr_t jomini_state_slot_override = 0;
  std::uintptr_t game_state_slot_override = 0;
  std::uintptr_t tls_initialized_flag_override = 0;
  NetworkSessionTlsContextGetterV1 tls_context_getter_override = nullptr;
  void *memory_protection_context = nullptr;
  NetworkSessionMemoryQueryV1 memory_query_override = nullptr;
  NetworkSessionMemoryProtectV1 memory_protect_override = nullptr;
  std::size_t system_page_size_override = 0;
};

struct NetworkSessionBoundaryDiagnosticsV1 {
  std::uint32_t failure_flags = 0;
  std::uint64_t epochs = 0;
  std::uint64_t consecutive_verified = 0;
  std::uint32_t current_thread_id = 0;
  std::uint32_t rng_owner_thread_id = 0;
  std::uint8_t tls_global = 0;
  std::uint8_t tls_marker = 0;
  std::uintptr_t jomini_state = 0;
  std::uintptr_t game_state = 0;
  std::int32_t date_raw = 0;
  std::uint32_t active_hook_calls = 0;
  bool paused = false;
  bool read_success = false;
  bool installed = false;
  bool stop_requested = false;
  bool ready = false;
  static constexpr bool executor_submission_enabled = false;
  static constexpr std::uint64_t executed_requests = 0;
};

struct NetworkSessionBoundaryCounterV1 {
  std::atomic<std::uint32_t> failure_flags{0};
  std::atomic<std::uint64_t> epochs{0};
  std::atomic<std::uint64_t> consecutive_verified{0};
  std::atomic<std::uint32_t> current_thread_id{0};
  std::atomic<std::uint32_t> rng_owner_thread_id{0};
  std::atomic<std::uint8_t> tls_global{0};
  std::atomic<std::uint8_t> tls_marker{0};
  std::atomic<std::uintptr_t> tls_context{0};
  std::atomic<std::uintptr_t> jomini_state_observed{0};
  std::atomic<std::uintptr_t> game_state_observed{0};
  std::atomic<std::int32_t> date_raw{0};
  std::atomic<bool> paused{false};
  std::atomic<bool> read_success{false};
  std::atomic<bool> installed{false};
  std::atomic<bool> stop_requested{false};
  std::atomic<std::uint32_t> active_hook_calls{0};
  std::atomic_flag observation_guard = ATOMIC_FLAG_INIT;

  // Immutable between successful install and uninstall.  Process-lifetime
  // storage is required because an IAT caller can fetch the hook target before
  // uninstall restores the slot.
  std::uintptr_t module_base = 0;
  void **release_srw_iat_slot = nullptr;
  ReleaseSrwLockExclusiveFunctionV1 original_release_srw = nullptr;
  std::uintptr_t global_rng_wrapper_slot = 0;
  std::uintptr_t jomini_state_slot = 0;
  std::uintptr_t game_state_slot = 0;
  std::uintptr_t tls_initialized_flag = 0;
  NetworkSessionTlsContextGetterV1 tls_context_getter = nullptr;
  void *memory_protection_context = nullptr;
  NetworkSessionMemoryQueryV1 memory_query = nullptr;
  NetworkSessionMemoryProtectV1 memory_protect = nullptr;
  std::size_t system_page_size = 0;

  std::uint32_t last_thread_id = 0;
  std::uint32_t last_rng_owner_thread_id = 0;
  std::uintptr_t last_tls_context = 0;
  std::uintptr_t last_jomini_state = 0;
  std::uintptr_t last_game_state = 0;
  std::int32_t last_date_raw = 0;
  bool last_verified_valid = false;
};

bool InstallNetworkSessionBoundaryCounterV1(
    NetworkSessionBoundaryCounterV1 &counter,
    const NetworkSessionBoundaryInstallEnvironmentV1 &environment) noexcept;

NetworkSessionBoundaryUninstallResultV1
UninstallNetworkSessionBoundaryCounterV1(
    NetworkSessionBoundaryCounterV1 &counter,
    std::uint32_t active_call_drain_timeout_milliseconds) noexcept;

void SignalNetworkSessionBoundaryCounterProcessDetachV1(
    NetworkSessionBoundaryCounterV1 &counter) noexcept;

bool ObserveNetworkSessionBoundaryV1(
    NetworkSessionBoundaryCounterV1 &counter, std::uintptr_t return_rva,
    std::uint32_t current_thread_id) noexcept;

NetworkSessionBoundaryDiagnosticsV1 ReadNetworkSessionBoundaryDiagnosticsV1(
    const NetworkSessionBoundaryCounterV1 &counter) noexcept;

extern "C" VOID WINAPI XarNetworkSessionReleaseSrwLockExclusiveHookV1(
    PSRWLOCK lock) noexcept;

} // namespace xar::ck3_11906
