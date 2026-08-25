#include "xar_bridge/network_session_boundary_counter_v1.hpp"

#include <intrin.h>

#include <array>
#include <cstring>

namespace xar::ck3_11906 {
namespace {

std::atomic<NetworkSessionBoundaryCounterV1 *> g_active_counter{nullptr};
std::atomic<ReleaseSrwLockExclusiveFunctionV1> g_original_release_srw{
    nullptr};

constexpr std::array<std::uint8_t, 23> kThreadNameStoreAnchor{
    0x44, 0x8D, 0x46, 0x16, 0x48, 0x8D, 0x15, 0x36,
    0x39, 0x0C, 0x01, 0x48, 0x8D, 0x0D, 0xA7, 0x55,
    0x34, 0x02, 0xE8, 0x0A, 0xC8, 0x3C, 0xFD};
constexpr std::array<std::uint8_t, 25> kCallbackInstallAnchor{
    0x48, 0x8D, 0x9E, 0xB8, 0x00, 0x00, 0x00, 0x48,
    0x8D, 0x05, 0xAF, 0x5B, 0x00, 0x00, 0x48, 0x89,
    0x03, 0x48, 0x89, 0x73, 0x08, 0xC6, 0x43, 0x10,
    0x00};
constexpr std::array<std::uint8_t, 15> kThreadRegisterAnchor{
    0x48, 0x8B, 0xD3, 0x48, 0x8D, 0x0D, 0xDC, 0xBD,
    0x79, 0x00, 0xE8, 0x37, 0xC4, 0x7A, 0x00};
constexpr std::array<std::uint8_t, 30> kThreadNameTrampolineAnchor{
    0x48, 0x89, 0x5C, 0x24, 0x08, 0x57, 0x48, 0x83,
    0xEC, 0x20, 0x48, 0x8B, 0xDA, 0x48, 0x8B, 0xF9,
    0x4D, 0x85, 0xC0, 0x74, 0x08, 0x49, 0x8B, 0xC8,
    0xE8, 0xC3, 0xC8, 0xFB, 0xFF, 0x48};
constexpr std::array<std::uint8_t, 53> kThreadLoopAnchor{
    0x40, 0x53, 0x48, 0x83, 0xEC, 0x20, 0x48, 0x8B,
    0xD9, 0x8B, 0x49, 0x40, 0xE8, 0xEF, 0x05, 0x01,
    0x00, 0xB1, 0x01, 0x0F, 0xB6, 0x43, 0x10, 0x84,
    0xC0, 0x75, 0x12, 0x84, 0xC9, 0x74, 0x0E, 0x48,
    0x8B, 0x03, 0x48, 0x8B, 0x4B, 0x08, 0xFF, 0xD0,
    0x0F, 0xB6, 0xC8, 0xEB, 0xE6, 0x33, 0xC0, 0x48,
    0x83, 0xC4, 0x20, 0x5B, 0xC3};
constexpr std::array<std::uint8_t, 24> kIterationPrologueAnchor{
    0x48, 0x89, 0x5C, 0x24, 0x18, 0x55, 0x56, 0x57,
    0x41, 0x54, 0x41, 0x55, 0x41, 0x56, 0x41, 0x57,
    0x48, 0x8B, 0xEC, 0x48, 0x83, 0xEC, 0x60, 0x48};
constexpr std::array<std::uint8_t, 20> kMainLockAcquireAnchor{
    0x48, 0x8B, 0x8F, 0xD0, 0x03, 0x00, 0x00, 0x48,
    0x81, 0xC1, 0x98, 0x00, 0x00, 0x00, 0xFF, 0x15,
    0xE6, 0xF1, 0xBA, 0x00};
constexpr std::array<std::uint8_t, 8> kStateMachineCallAnchor{
    0x48, 0x8B, 0xCF, 0xE8, 0xC2, 0xA5, 0xFF, 0xFF};
constexpr std::array<std::uint8_t, 21> kMainLockReleaseAnchor{
    0x48, 0x8B, 0x8F, 0xD0, 0x03, 0x00, 0x00, 0x48,
    0x81, 0xC1, 0x98, 0x00, 0x00, 0x00, 0xFF, 0x15,
    0xE2, 0xEE, 0xBA, 0x00, 0x90};
constexpr std::array<std::uint8_t, 26> kIterationTrueAnchor{
    0xB0, 0x01, 0x48, 0x8B, 0x9C, 0x24, 0xB0, 0x00,
    0x00, 0x00, 0x48, 0x83, 0xC4, 0x60, 0x41, 0x5F,
    0x41, 0x5E, 0x41, 0x5D, 0x41, 0x5C, 0x5F, 0x5E,
    0x5D, 0xC3};
constexpr std::array<char, 23> kThreadNameAnchor{
    'N', 'e', 't', 'w', 'o', 'r', 'k', '/', 'S', 'e', 's', 's',
    'i', 'o', 'n', ' ', 't', 'h', 'r', 'e', 'a', 'd', '\0'};

enum class IatSwapResult {
  swapped,
  identity_mismatch,
  page_identity_mismatch,
  protection_failed,
};

struct RawBoundaryStamp {
  std::uint32_t current_thread_id = 0;
  std::uint32_t rng_owner_thread_id = 0;
  std::uint8_t tls_global = 0;
  std::uint8_t tls_marker = 0;
  std::uintptr_t tls_context = 0;
  std::uintptr_t jomini_state = 0;
  std::uintptr_t game_state = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
};

template <typename T>
T LoadAt(std::uintptr_t address, std::size_t offset = 0) noexcept {
  T value{};
  std::memcpy(&value, reinterpret_cast<const void *>(address + offset),
              sizeof(value));
  return value;
}

template <std::size_t Size>
bool BytesMatchUnsafe(std::uintptr_t address,
                      const std::array<std::uint8_t, Size> &expected) noexcept {
  return std::memcmp(reinterpret_cast<const void *>(address), expected.data(),
                     Size) == 0;
}

bool DefaultMemoryQuery(void *, const void *address,
                        MEMORY_BASIC_INFORMATION &information) noexcept {
  information = {};
  return VirtualQuery(address, &information, sizeof(information)) ==
         sizeof(information);
}

bool DefaultMemoryProtect(void *, void *page_address, std::size_t page_size,
                          DWORD new_protect, DWORD &old_protect) noexcept {
  old_protect = 0;
  return VirtualProtect(page_address, page_size, new_protect,
                        &old_protect) != FALSE;
}

void AddFailure(NetworkSessionBoundaryCounterV1 &counter,
                NetworkSessionBoundaryCounterFailureV1 failure) noexcept {
  counter.failure_flags.fetch_or(static_cast<std::uint32_t>(failure),
                                 std::memory_order_acq_rel);
}

IatSwapResult AtomicSwapReadOnlyIat(NetworkSessionBoundaryCounterV1 &counter,
                                    void *expected, void *desired) noexcept {
  if (counter.release_srw_iat_slot == nullptr ||
      counter.memory_query == nullptr || counter.memory_protect == nullptr ||
      counter.system_page_size == 0) {
    return IatSwapResult::page_identity_mismatch;
  }
  const auto slot =
      reinterpret_cast<std::uintptr_t>(counter.release_srw_iat_slot);
  const auto page_size = counter.system_page_size;
  const auto page = (slot / page_size) * page_size;
  if (slot < page || slot - page > page_size - sizeof(void *)) {
    return IatSwapResult::page_identity_mismatch;
  }
  MEMORY_BASIC_INFORMATION information{};
  if (!counter.memory_query(counter.memory_protection_context,
                            counter.release_srw_iat_slot, information)) {
    return IatSwapResult::page_identity_mismatch;
  }
  const auto region_base =
      reinterpret_cast<std::uintptr_t>(information.BaseAddress);
  if (information.State != MEM_COMMIT || information.Type != MEM_IMAGE ||
      information.Protect != PAGE_READONLY || region_base > page ||
      information.RegionSize < page_size ||
      page - region_base > information.RegionSize - page_size) {
    return IatSwapResult::page_identity_mismatch;
  }

  DWORD old_protect = 0;
  void *const page_address = reinterpret_cast<void *>(page);
  if (!counter.memory_protect(counter.memory_protection_context, page_address,
                              page_size, PAGE_READWRITE, old_protect) ||
      old_protect != PAGE_READONLY) {
    return IatSwapResult::protection_failed;
  }
  void *const observed = InterlockedCompareExchangePointer(
      reinterpret_cast<void *volatile *>(counter.release_srw_iat_slot),
      desired, expected);
  DWORD ignored = 0;
  const bool restored = counter.memory_protect(
      counter.memory_protection_context, page_address, page_size, old_protect,
      ignored);
  if (!restored) {
    if (observed == expected) {
      InterlockedCompareExchangePointer(
          reinterpret_cast<void *volatile *>(counter.release_srw_iat_slot),
          expected, desired);
    }
    DWORD retry_ignored = 0;
    (void)counter.memory_protect(counter.memory_protection_context,
                                 page_address, page_size, old_protect,
                                 retry_ignored);
    return IatSwapResult::protection_failed;
  }
  return observed == expected ? IatSwapResult::swapped
                              : IatSwapResult::identity_mismatch;
}

bool ExactAnchorsMatch(std::uintptr_t module_base) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    return BytesMatchUnsafe(module_base + 0x341CD0F,
                            kThreadNameStoreAnchor) &&
           std::memcmp(reinterpret_cast<const void *>(
                           module_base + kNetworkSessionThreadNameRva),
                       kThreadNameAnchor.data(), kThreadNameAnchor.size()) ==
               0 &&
           BytesMatchUnsafe(module_base + 0x341D853,
                            kCallbackInstallAnchor) &&
           BytesMatchUnsafe(module_base + 0x341D87A,
                            kThreadRegisterAnchor) &&
           BytesMatchUnsafe(module_base + kNetworkSessionThreadProcedureRva,
                            kThreadLoopAnchor) &&
           BytesMatchUnsafe(module_base + kNativeThreadNameTrampolineRva,
                            kThreadNameTrampolineAnchor) &&
           BytesMatchUnsafe(module_base + kNetworkSessionIterationRva,
                            kIterationPrologueAnchor) &&
           BytesMatchUnsafe(module_base + 0x342346E,
                            kMainLockAcquireAnchor) &&
           BytesMatchUnsafe(module_base + 0x34234C6,
                            kStateMachineCallAnchor) &&
           BytesMatchUnsafe(module_base + 0x3423762,
                            kMainLockReleaseAnchor) &&
           BytesMatchUnsafe(module_base + kNetworkSessionIterationTrueRva,
                            kIterationTrueAnchor);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool ReadRawStamp(NetworkSessionBoundaryCounterV1 &counter,
                  std::uint32_t current_thread_id,
                  RawBoundaryStamp &output) noexcept {
  output = {};
  output.current_thread_id = current_thread_id;
  if (current_thread_id == 0 || counter.global_rng_wrapper_slot == 0 ||
      counter.jomini_state_slot == 0 || counter.game_state_slot == 0 ||
      counter.tls_initialized_flag == 0 ||
      counter.tls_context_getter == nullptr) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
#endif
    const auto rng_wrapper =
        LoadAt<std::uintptr_t>(counter.global_rng_wrapper_slot);
    const auto jomini_state =
        LoadAt<std::uintptr_t>(counter.jomini_state_slot);
    const auto game_state = LoadAt<std::uintptr_t>(counter.game_state_slot);
    if (rng_wrapper == 0 || jomini_state == 0 || game_state == 0) {
      return false;
    }
    const auto rng_state =
        LoadAt<std::uintptr_t>(rng_wrapper, kGlobalRngWrapperStateOffset);
    if (rng_state == 0) {
      return false;
    }
    const auto owner = LoadAt<std::uint32_t>(
        rng_state, kGlobalRngOwnerThreadIdOffset);
    const auto tls_global =
        LoadAt<std::uint8_t>(counter.tls_initialized_flag);
    const auto tls_context = reinterpret_cast<std::uintptr_t>(
        counter.tls_context_getter());
    if (tls_context == 0) {
      return false;
    }
    const auto tls_marker =
        LoadAt<std::uint8_t>(tls_context, kMainThreadTlsMarkerOffset);
    const auto paused =
        LoadAt<std::uint8_t>(jomini_state, kJominiPausedOffset) != 0;
    const auto date_raw =
        LoadAt<std::int32_t>(game_state, kGameStateDateRawOffset);

    if (LoadAt<std::uintptr_t>(counter.global_rng_wrapper_slot) !=
            rng_wrapper ||
        LoadAt<std::uintptr_t>(rng_wrapper,
                               kGlobalRngWrapperStateOffset) != rng_state ||
        LoadAt<std::uint32_t>(rng_state,
                              kGlobalRngOwnerThreadIdOffset) != owner ||
        LoadAt<std::uint8_t>(counter.tls_initialized_flag) != tls_global ||
        reinterpret_cast<std::uintptr_t>(counter.tls_context_getter()) !=
            tls_context ||
        LoadAt<std::uint8_t>(tls_context, kMainThreadTlsMarkerOffset) !=
            tls_marker ||
        LoadAt<std::uintptr_t>(counter.jomini_state_slot) != jomini_state ||
        (LoadAt<std::uint8_t>(jomini_state, kJominiPausedOffset) != 0) !=
            paused ||
        LoadAt<std::uintptr_t>(counter.game_state_slot) != game_state ||
        LoadAt<std::int32_t>(game_state, kGameStateDateRawOffset) != date_raw) {
      return false;
    }

    output.rng_owner_thread_id = owner;
    output.tls_global = tls_global;
    output.tls_marker = tls_marker;
    output.tls_context = tls_context;
    output.jomini_state = jomini_state;
    output.game_state = game_state;
    output.date_raw = date_raw;
    output.paused = paused;
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = {};
    output.current_thread_id = current_thread_id;
    return false;
  }
#endif
}

void PublishRaw(NetworkSessionBoundaryCounterV1 &counter,
                const RawBoundaryStamp &stamp, bool success) noexcept {
  counter.current_thread_id.store(stamp.current_thread_id,
                                  std::memory_order_relaxed);
  counter.rng_owner_thread_id.store(stamp.rng_owner_thread_id,
                                    std::memory_order_relaxed);
  counter.tls_global.store(stamp.tls_global, std::memory_order_relaxed);
  counter.tls_marker.store(stamp.tls_marker, std::memory_order_relaxed);
  counter.tls_context.store(stamp.tls_context, std::memory_order_relaxed);
  counter.jomini_state_observed.store(stamp.jomini_state,
                                      std::memory_order_relaxed);
  counter.game_state_observed.store(stamp.game_state,
                                    std::memory_order_relaxed);
  counter.date_raw.store(stamp.date_raw, std::memory_order_relaxed);
  counter.paused.store(stamp.paused, std::memory_order_relaxed);
  counter.read_success.store(success, std::memory_order_release);
}

bool AllAdmissionGates(const RawBoundaryStamp &stamp) noexcept {
  return stamp.current_thread_id != 0 &&
         stamp.rng_owner_thread_id == stamp.current_thread_id &&
         stamp.tls_global == 1 && stamp.tls_context != 0 &&
         stamp.tls_marker == 1 && stamp.jomini_state != 0 &&
         stamp.game_state != 0 && stamp.paused;
}

bool SameVerifiedIdentity(const NetworkSessionBoundaryCounterV1 &counter,
                          const RawBoundaryStamp &stamp) noexcept {
  return counter.last_verified_valid &&
         counter.last_thread_id == stamp.current_thread_id &&
         counter.last_rng_owner_thread_id == stamp.rng_owner_thread_id &&
         counter.last_tls_context == stamp.tls_context &&
         counter.last_jomini_state == stamp.jomini_state &&
         counter.last_game_state == stamp.game_state &&
         counter.last_date_raw == stamp.date_raw;
}

void ResetVerified(NetworkSessionBoundaryCounterV1 &counter) noexcept {
  counter.last_verified_valid = false;
  counter.consecutive_verified.store(0, std::memory_order_release);
}

} // namespace

bool InstallNetworkSessionBoundaryCounterV1(
    NetworkSessionBoundaryCounterV1 &counter,
    const NetworkSessionBoundaryInstallEnvironmentV1 &environment) noexcept {
  if (!environment.exact_build_admitted || environment.module_base == 0) {
    AddFailure(counter, network_session_boundary_failure_exact_build);
    return false;
  }
  if (counter.installed.load(std::memory_order_acquire)) {
    return g_active_counter.load(std::memory_order_acquire) == &counter;
  }

  void **iat_slot = environment.release_srw_iat_slot_override;
  auto original = environment.resolved_release_srw_override;
  auto rng_slot = environment.global_rng_wrapper_slot_override;
  auto jomini_slot = environment.jomini_state_slot_override;
  auto game_slot = environment.game_state_slot_override;
  auto tls_flag = environment.tls_initialized_flag_override;
  auto tls_getter = environment.tls_context_getter_override;
  auto memory_query = environment.memory_query_override;
  auto memory_protect = environment.memory_protect_override;
  auto page_size = environment.system_page_size_override;
  if (!environment.offline_fixture) {
    if (!ExactAnchorsMatch(environment.module_base)) {
      AddFailure(counter, network_session_boundary_failure_anchor);
      return false;
    }
    iat_slot = reinterpret_cast<void **>(
        environment.module_base + kReleaseSrwLockExclusiveIatSlotRva);
    const auto kernel32 = GetModuleHandleW(L"kernel32.dll");
    original = kernel32 == nullptr
                   ? nullptr
                   : reinterpret_cast<ReleaseSrwLockExclusiveFunctionV1>(
                         GetProcAddress(kernel32,
                                        "ReleaseSRWLockExclusive"));
    rng_slot = environment.module_base + kGlobalRngWrapperSlotRva;
    jomini_slot = environment.module_base + kJominiStateSlotRva;
    game_slot = environment.module_base + kGameStateSlotRva;
    tls_flag = environment.module_base + kMainThreadTlsInitializedFlagRva;
    tls_getter = reinterpret_cast<NetworkSessionTlsContextGetterV1>(
        environment.module_base + kMainThreadTlsContextGetterRva);
    memory_query = &DefaultMemoryQuery;
    memory_protect = &DefaultMemoryProtect;
    SYSTEM_INFO system_information{};
    GetSystemInfo(&system_information);
    page_size = system_information.dwPageSize;
  }
  if (iat_slot == nullptr || original == nullptr || rng_slot == 0 ||
      jomini_slot == 0 || game_slot == 0 || tls_flag == 0 ||
      tls_getter == nullptr || memory_query == nullptr ||
      memory_protect == nullptr || page_size < sizeof(void *)) {
    AddFailure(counter, network_session_boundary_failure_iat_identity);
    return false;
  }

  void *observed = nullptr;
#if defined(_MSC_VER)
  __try {
#endif
    observed = *iat_slot;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    AddFailure(counter, network_session_boundary_failure_iat_identity);
    return false;
  }
#endif
  if (observed != reinterpret_cast<void *>(original)) {
    AddFailure(counter, network_session_boundary_failure_iat_identity);
    return false;
  }

  NetworkSessionBoundaryCounterV1 *expected = nullptr;
  if (!g_active_counter.compare_exchange_strong(
          expected, &counter, std::memory_order_acq_rel,
          std::memory_order_acquire) &&
      expected != &counter) {
    AddFailure(counter, network_session_boundary_failure_singleton);
    return false;
  }
  const auto pinned_original =
      g_original_release_srw.load(std::memory_order_acquire);
  if (pinned_original != nullptr && pinned_original != original) {
    AddFailure(counter, network_session_boundary_failure_iat_identity);
    return false;
  }

  counter.failure_flags.store(0, std::memory_order_release);
  counter.epochs.store(0, std::memory_order_release);
  counter.consecutive_verified.store(0, std::memory_order_release);
  counter.current_thread_id.store(0, std::memory_order_release);
  counter.rng_owner_thread_id.store(0, std::memory_order_release);
  counter.tls_global.store(0, std::memory_order_release);
  counter.tls_marker.store(0, std::memory_order_release);
  counter.tls_context.store(0, std::memory_order_release);
  counter.jomini_state_observed.store(0, std::memory_order_release);
  counter.game_state_observed.store(0, std::memory_order_release);
  counter.date_raw.store(0, std::memory_order_release);
  counter.paused.store(false, std::memory_order_release);
  counter.read_success.store(false, std::memory_order_release);
  counter.stop_requested.store(false, std::memory_order_release);
  counter.active_hook_calls.store(0, std::memory_order_release);
  counter.module_base = environment.module_base;
  counter.release_srw_iat_slot = iat_slot;
  counter.original_release_srw = original;
  counter.global_rng_wrapper_slot = rng_slot;
  counter.jomini_state_slot = jomini_slot;
  counter.game_state_slot = game_slot;
  counter.tls_initialized_flag = tls_flag;
  counter.tls_context_getter = tls_getter;
  counter.memory_protection_context = environment.memory_protection_context;
  counter.memory_query = memory_query;
  counter.memory_protect = memory_protect;
  counter.system_page_size = page_size;
  counter.last_verified_valid = false;
  g_original_release_srw.store(original, std::memory_order_release);

  const auto swapped = AtomicSwapReadOnlyIat(
      counter, reinterpret_cast<void *>(original),
      reinterpret_cast<void *>(
          &XarNetworkSessionReleaseSrwLockExclusiveHookV1));
  if (swapped != IatSwapResult::swapped) {
    counter.stop_requested.store(true, std::memory_order_release);
    AddFailure(counter,
               swapped == IatSwapResult::identity_mismatch
                   ? network_session_boundary_failure_iat_identity
                   : swapped == IatSwapResult::page_identity_mismatch
                         ? network_session_boundary_failure_page_identity
                         : network_session_boundary_failure_page_protect);
    return false;
  }
  counter.installed.store(true, std::memory_order_release);
  return true;
}

NetworkSessionBoundaryUninstallResultV1
UninstallNetworkSessionBoundaryCounterV1(
    NetworkSessionBoundaryCounterV1 &counter,
    std::uint32_t active_call_drain_timeout_milliseconds) noexcept {
  auto *const active = g_active_counter.load(std::memory_order_acquire);
  if (active == nullptr) {
    return NetworkSessionBoundaryUninstallResultV1::not_installed;
  }
  if (active != &counter) {
    return NetworkSessionBoundaryUninstallResultV1::wrong_counter;
  }
  counter.stop_requested.store(true, std::memory_order_release);
  if (counter.installed.load(std::memory_order_acquire)) {
    const auto swapped = AtomicSwapReadOnlyIat(
        counter,
        reinterpret_cast<void *>(
            &XarNetworkSessionReleaseSrwLockExclusiveHookV1),
        reinterpret_cast<void *>(counter.original_release_srw));
    if (swapped != IatSwapResult::swapped) {
      AddFailure(counter, network_session_boundary_failure_uninstall);
      return NetworkSessionBoundaryUninstallResultV1::iat_restore_failed;
    }
    counter.installed.store(false, std::memory_order_release);
  } else {
    return NetworkSessionBoundaryUninstallResultV1::not_installed;
  }

  const auto started = GetTickCount64();
  while (counter.active_hook_calls.load(std::memory_order_acquire) != 0) {
    if (GetTickCount64() - started >=
        active_call_drain_timeout_milliseconds) {
      return NetworkSessionBoundaryUninstallResultV1::
          active_hook_calls_pending;
    }
    Sleep(1);
  }
  return NetworkSessionBoundaryUninstallResultV1::uninstalled;
}

void SignalNetworkSessionBoundaryCounterProcessDetachV1(
    NetworkSessionBoundaryCounterV1 &counter) noexcept {
  counter.stop_requested.store(true, std::memory_order_release);
}

bool ObserveNetworkSessionBoundaryV1(
    NetworkSessionBoundaryCounterV1 &counter, std::uintptr_t return_rva,
    std::uint32_t current_thread_id) noexcept {
  if (return_rva != kNetworkSessionPostLockReturnRva ||
      counter.stop_requested.load(std::memory_order_acquire)) {
    return false;
  }
  counter.epochs.fetch_add(1, std::memory_order_acq_rel);
  if (counter.observation_guard.test_and_set(std::memory_order_acq_rel)) {
    counter.consecutive_verified.store(0, std::memory_order_release);
    AddFailure(counter, network_session_boundary_failure_reentry);
    return false;
  }

  RawBoundaryStamp stamp{};
  const bool success = ReadRawStamp(counter, current_thread_id, stamp);
  PublishRaw(counter, stamp, success);
  if (!success) {
    ResetVerified(counter);
    AddFailure(counter, network_session_boundary_failure_runtime_read);
    counter.observation_guard.clear(std::memory_order_release);
    return false;
  }

  if (!AllAdmissionGates(stamp)) {
    ResetVerified(counter);
    counter.observation_guard.clear(std::memory_order_release);
    return false;
  }
  const bool consecutive = SameVerifiedIdentity(counter, stamp);
  counter.last_thread_id = stamp.current_thread_id;
  counter.last_rng_owner_thread_id = stamp.rng_owner_thread_id;
  counter.last_tls_context = stamp.tls_context;
  counter.last_jomini_state = stamp.jomini_state;
  counter.last_game_state = stamp.game_state;
  counter.last_date_raw = stamp.date_raw;
  counter.last_verified_valid = true;
  const auto next = consecutive
                        ? counter.consecutive_verified.load(
                              std::memory_order_relaxed) +
                              1
                        : 1;
  counter.consecutive_verified.store(next, std::memory_order_release);
  counter.observation_guard.clear(std::memory_order_release);
  return true;
}

NetworkSessionBoundaryDiagnosticsV1 ReadNetworkSessionBoundaryDiagnosticsV1(
    const NetworkSessionBoundaryCounterV1 &counter) noexcept {
  NetworkSessionBoundaryDiagnosticsV1 output{};
  output.failure_flags =
      counter.failure_flags.load(std::memory_order_acquire);
  output.epochs = counter.epochs.load(std::memory_order_acquire);
  output.consecutive_verified =
      counter.consecutive_verified.load(std::memory_order_acquire);
  output.current_thread_id =
      counter.current_thread_id.load(std::memory_order_acquire);
  output.rng_owner_thread_id =
      counter.rng_owner_thread_id.load(std::memory_order_acquire);
  output.tls_global = counter.tls_global.load(std::memory_order_acquire);
  output.tls_marker = counter.tls_marker.load(std::memory_order_acquire);
  output.jomini_state =
      counter.jomini_state_observed.load(std::memory_order_acquire);
  output.game_state =
      counter.game_state_observed.load(std::memory_order_acquire);
  output.date_raw = counter.date_raw.load(std::memory_order_acquire);
  output.paused = counter.paused.load(std::memory_order_acquire);
  output.read_success = counter.read_success.load(std::memory_order_acquire);
  output.installed = counter.installed.load(std::memory_order_acquire);
  output.stop_requested =
      counter.stop_requested.load(std::memory_order_acquire);
  output.active_hook_calls =
      counter.active_hook_calls.load(std::memory_order_acquire);
  output.ready =
      output.installed && !output.stop_requested && output.read_success &&
      output.failure_flags == 0 && output.current_thread_id != 0 &&
      output.current_thread_id == output.rng_owner_thread_id &&
      output.tls_global == 1 && output.tls_marker == 1 && output.paused &&
      output.jomini_state != 0 && output.game_state != 0 &&
      output.consecutive_verified >=
          kNetworkSessionBoundaryMinimumConsecutiveVerifiedEpochs;
  return output;
}

extern "C" VOID WINAPI XarNetworkSessionReleaseSrwLockExclusiveHookV1(
    PSRWLOCK lock) noexcept {
  const auto return_address =
      reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  auto *const counter = g_active_counter.load(std::memory_order_acquire);
  const auto original =
      g_original_release_srw.load(std::memory_order_acquire);
  if (original == nullptr) {
    return;
  }
  const bool exact_candidate =
      counter != nullptr && return_address >= counter->module_base &&
      return_address - counter->module_base ==
          kNetworkSessionPostLockReturnRva;
  if (exact_candidate) {
    counter->active_hook_calls.fetch_add(1, std::memory_order_acq_rel);
  }
  original(lock);
  const DWORD original_last_error = GetLastError();
  if (exact_candidate &&
      !counter->stop_requested.load(std::memory_order_acquire)) {
    ObserveNetworkSessionBoundaryV1(*counter,
                                    kNetworkSessionPostLockReturnRva,
                                    GetCurrentThreadId());
  }
  if (exact_candidate) {
    counter->active_hook_calls.fetch_sub(1, std::memory_order_acq_rel);
  }
  SetLastError(original_last_error);
}

} // namespace xar::ck3_11906
