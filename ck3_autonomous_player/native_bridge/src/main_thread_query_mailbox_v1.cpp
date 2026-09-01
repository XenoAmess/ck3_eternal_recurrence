#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <intrin.h>

#include <algorithm>
#include <array>
#include <cstring>

namespace xar::ck3_11906 {
namespace {

std::atomic<MainThreadQueryMailboxV1 *> g_active_mailbox{nullptr};
std::atomic<PeekMessageWFunctionV1> g_original_peek_message{nullptr};

static_assert(kMainThreadQueryMaximumDrainPerPump == 1);

constexpr std::array<std::uint8_t, 15> kWindowsPumpPrologue{
    0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74,
    0x24, 0x18, 0x57, 0x48, 0x83, 0xEC, 0x60};
constexpr std::array<std::uint8_t, 16> kFirstPeekCallAnchor{
    0x45, 0x33, 0xC0, 0x48, 0x8D, 0x4C, 0x24, 0x30,
    0x33, 0xD2, 0xFF, 0x15, 0xC6, 0xEC, 0x2E, 0x00};
constexpr std::array<std::uint8_t, 14> kVideoDevicePumpInstallAnchor{
    0x48, 0x8D, 0x05, 0x2E, 0x5A, 0xFE, 0xFF,
    0x48, 0x89, 0x85, 0x38, 0x02, 0x00, 0x00};
constexpr std::array<std::uint8_t, 15> kSdlPumpDispatchAnchor{
    0x48, 0x85, 0xF6, 0x74, 0x09, 0x48, 0x8B, 0xCE,
    0xFF, 0x96, 0x38, 0x02, 0x00, 0x00, 0x83};
constexpr std::array<std::uint8_t, 18> kNativeOwnerThreadAnchor{
    0xE8, 0x41, 0x5F, 0x79, 0x00, 0x48, 0x8B, 0x0B, 0x44,
    0x8B, 0x41, 0x10, 0x44, 0x3B, 0xC0, 0x74, 0x20, 0x33};
constexpr std::array<std::uint8_t, 6> kGetCurrentThreadIdThunkAnchor{
    0x48, 0xFF, 0x25, 0x69, 0x25, 0x2D};
constexpr std::array<std::uint8_t, 32> kTlsContextGetterAnchor{
    0x40, 0x53, 0x48, 0x83, 0xEC, 0x20, 0x65, 0x48,
    0x8B, 0x04, 0x25, 0x58, 0x00, 0x00, 0x00, 0x48,
    0x8B, 0x08, 0xBA, 0x98, 0x32, 0x00, 0x00, 0x8B,
    0x04, 0x0A, 0x41, 0xB8, 0xA0, 0x32, 0x00, 0x00};
constexpr std::array<std::uint8_t, 16> kTlsStartupStoreAnchor{
    0xC6, 0x05, 0x08, 0xAB, 0xF8, 0x04, 0x01, 0xE8,
    0x46, 0xE7, 0x39, 0x03, 0xC6, 0x40, 0x20, 0x01};
constexpr std::array<std::uint8_t, 22> kHandlePdxEventsTlsGateAnchor{
    0x0F, 0xB6, 0x05, 0x99, 0x3B, 0xD4, 0x01, 0x84,
    0xC0, 0x74, 0x28, 0xE8, 0xD3, 0x77, 0x15, 0x00,
    0x80, 0x78, 0x20, 0x00, 0x74, 0x1D};
constexpr std::array<std::uint8_t, 10> kRunnerAppVslotAnchor{
    0x48, 0x8B, 0x49, 0x08, 0x48, 0x8B, 0x01, 0xFF, 0x50, 0x18};
constexpr std::array<std::uint8_t, 19> kApplicationPumpGateAnchor{
    0x80, 0xB9, 0x60, 0x01, 0x00, 0x00, 0x00, 0x48,
    0x8B, 0xD9, 0x75, 0x5B, 0x80, 0xB9, 0x89, 0x00,
    0x00, 0x00, 0x00};
constexpr std::array<std::uint8_t, 8> kApplicationHandleEventsCallAnchor{
    0x48, 0x8B, 0xCB, 0xE8, 0x0D, 0xF9, 0xFF, 0xFF};
constexpr std::array<std::uint8_t, 7> kEventSingletonLoadAnchor{
    0x48, 0x8B, 0x35, 0x18, 0xA7, 0x1B, 0x02};
constexpr std::array<std::uint8_t, 35> kEventSingletonVslotCallAnchor{
    0x48, 0x8B, 0x06, 0x4C, 0x8B, 0x50, 0x08, 0x48,
    0x8B, 0x47, 0x28, 0x48, 0x89, 0x54, 0x24, 0x28,
    0x48, 0x89, 0x44, 0x24, 0x20, 0x4C, 0x8B, 0x4F,
    0x20, 0x4C, 0x8B, 0x47, 0x18, 0x48, 0x8B, 0xCE,
    0x41, 0xFF, 0xD2};
constexpr std::array<std::uint8_t, 11> kPdxEventsSdlSlotCallAnchor{
    0x48, 0x8D, 0x4C, 0x24, 0x48, 0xFF, 0x15, 0xBF,
    0x1B, 0x5B, 0x01};
constexpr std::array<std::uint8_t, 8> kSdlUpperPumpCallAnchor{
    0x8D, 0x48, 0x01, 0xE8, 0x98, 0xFE, 0xFF, 0xFF};

enum class IatSwapResult {
  swapped,
  identity_mismatch,
  page_identity_mismatch,
  protection_failed,
};

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

IatSwapResult AtomicSwapReadOnlyIat(
    MainThreadQueryMailboxV1 &mailbox, void *expected, void *desired) noexcept {
  if (mailbox.peek_message_iat_slot == nullptr ||
      mailbox.memory_query == nullptr || mailbox.memory_protect == nullptr ||
      mailbox.system_page_size == 0) {
    return IatSwapResult::page_identity_mismatch;
  }

  const auto slot_address = reinterpret_cast<std::uintptr_t>(
      mailbox.peek_message_iat_slot);
  const auto page_size = mailbox.system_page_size;
  const auto page_address_value = (slot_address / page_size) * page_size;
  if (slot_address < page_address_value ||
      slot_address - page_address_value > page_size - sizeof(void *)) {
    return IatSwapResult::page_identity_mismatch;
  }

  MEMORY_BASIC_INFORMATION information{};
  if (!mailbox.memory_query(mailbox.memory_protection_context,
                            mailbox.peek_message_iat_slot, information)) {
    return IatSwapResult::page_identity_mismatch;
  }
  const auto region_base =
      reinterpret_cast<std::uintptr_t>(information.BaseAddress);
  if (information.State != MEM_COMMIT || information.Type != MEM_IMAGE ||
      information.Protect != PAGE_READONLY || region_base > page_address_value ||
      information.RegionSize < page_size ||
      page_address_value - region_base > information.RegionSize - page_size) {
    return IatSwapResult::page_identity_mismatch;
  }

  void *const page_address = reinterpret_cast<void *>(page_address_value);
  DWORD original_protect = 0;
  if (!mailbox.memory_protect(mailbox.memory_protection_context, page_address,
                              page_size, PAGE_READWRITE,
                              original_protect) ||
      original_protect != PAGE_READONLY) {
    return IatSwapResult::protection_failed;
  }

  void *const observed = InterlockedCompareExchangePointer(
      reinterpret_cast<void *volatile *>(mailbox.peek_message_iat_slot),
      desired, expected);
  DWORD writable_protect = 0;
  const bool restored = mailbox.memory_protect(
      mailbox.memory_protection_context, page_address, page_size,
      original_protect, writable_protect);
  (void)writable_protect;
  if (!restored) {
    // VirtualProtect failure does not change the prior writable protection.
    // Roll the IAT value back before making one final best-effort protection
    // restore.  A failed install therefore never leaves the hook target
    // behind, and the exact read-only page is restored when the OS still
    // accepts protection changes.
    if (observed == expected) {
      InterlockedCompareExchangePointer(
          reinterpret_cast<void *volatile *>(mailbox.peek_message_iat_slot),
          expected, desired);
    }
    DWORD rollback_protect = 0;
    mailbox.memory_protect(mailbox.memory_protection_context, page_address,
                           page_size, original_protect, rollback_protect);
    return IatSwapResult::protection_failed;
  }
  return observed == expected ? IatSwapResult::swapped
                              : IatSwapResult::identity_mismatch;
}

template <typename Value>
Value LoadAt(std::uintptr_t address, std::size_t offset = 0) noexcept {
  Value value{};
  std::memcpy(&value, reinterpret_cast<const void *>(address + offset),
              sizeof(value));
  return value;
}

template <std::size_t Size>
bool BytesMatchUnsafe(std::uintptr_t address,
                      const std::array<std::uint8_t, Size> &expected) noexcept {
  return std::memcmp(reinterpret_cast<const void *>(address), expected.data(),
                     expected.size()) == 0;
}

bool ExactPumpAnchorsMatch(std::uintptr_t module_base) noexcept {
  if (module_base == 0) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
#endif
    return BytesMatchUnsafe(module_base + kSdlWindowsPumpFunctionRva,
                            kWindowsPumpPrologue) &&
           BytesMatchUnsafe(module_base + kSdlWindowsPumpFirstPeekCallRva - 10,
                            kFirstPeekCallAnchor) &&
           BytesMatchUnsafe(module_base + kSdlWindowsVideoDevicePumpInstallRva,
                            kVideoDevicePumpInstallAnchor) &&
           BytesMatchUnsafe(module_base + 0x3CD3664,
                            kSdlPumpDispatchAnchor) &&
           BytesMatchUnsafe(module_base + 0x356A0BA,
                            kNativeOwnerThreadAnchor) &&
           BytesMatchUnsafe(module_base + kGetCurrentThreadIdThunkRva,
                            kGetCurrentThreadIdThunkAnchor) &&
           BytesMatchUnsafe(module_base + kMainThreadTlsContextGetterRva,
                            kTlsContextGetterAnchor) &&
           BytesMatchUnsafe(module_base + kMainThreadTlsStartupStoreRva,
                            kTlsStartupStoreAnchor) &&
           BytesMatchUnsafe(module_base + kHandlePdxEventsTlsGateRva,
                            kHandlePdxEventsTlsGateAnchor) &&
           BytesMatchUnsafe(module_base + 0x351F0D9,
                            kRunnerAppVslotAnchor) &&
           BytesMatchUnsafe(module_base + 0x3555826,
                            kApplicationPumpGateAnchor) &&
           BytesMatchUnsafe(module_base + 0x355587B,
                            kApplicationHandleEventsCallAnchor) &&
           BytesMatchUnsafe(module_base + 0x35551F9,
                            kEventSingletonLoadAnchor) &&
           BytesMatchUnsafe(module_base + 0x355523B,
                            kEventSingletonVslotCallAnchor) &&
           BytesMatchUnsafe(module_base + 0x3A2EE9E,
                            kPdxEventsSdlSlotCallAnchor) &&
           BytesMatchUnsafe(module_base + 0x3CD3760,
                            kSdlUpperPumpCallAnchor);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

void AddFailure(MainThreadQueryMailboxV1 &mailbox,
                MainThreadQueryMailboxFailureV1 failure) noexcept {
  mailbox.failure_flags.fetch_or(static_cast<std::uint32_t>(failure),
                                 std::memory_order_acq_rel);
}

bool ReadExecutionStamp(MainThreadQueryMailboxV1 &mailbox,
                        std::uint64_t pump_epoch,
                        std::uint32_t current_thread_id,
                        MainThreadExecutionStampV1 &output) noexcept {
  output = {};
  if (mailbox.global_rng_wrapper_slot == 0 ||
      mailbox.jomini_state_slot == 0 || mailbox.game_state_slot == 0 ||
      mailbox.tls_initialized_flag == 0 ||
      mailbox.tls_context_getter == nullptr || current_thread_id == 0) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
#endif
    const auto jomini_state =
        LoadAt<std::uintptr_t>(mailbox.jomini_state_slot);
    const auto game_state = LoadAt<std::uintptr_t>(mailbox.game_state_slot);
    if (jomini_state == 0 || game_state == 0) {
      return false;
    }
    std::uintptr_t rng_wrapper = 0;
    std::uintptr_t rng_state = 0;
    std::uint32_t owner_thread_id = 0;
    // Diagnostic only. A different scoped subsystem may legitimately own the
    // global wrapper while HandlePdxEvents runs on its proven application
    // main thread. Failure or drift here must never reject a war-entry query.
    __try {
      rng_wrapper = LoadAt<std::uintptr_t>(mailbox.global_rng_wrapper_slot);
      if (rng_wrapper != 0) {
        rng_state = LoadAt<std::uintptr_t>(
            rng_wrapper, kGlobalRngWrapperStateOffset);
      }
      if (rng_state != 0) {
        owner_thread_id = LoadAt<std::uint32_t>(
            rng_state, kGlobalRngOwnerThreadIdOffset);
      }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
      rng_wrapper = 0;
      rng_state = 0;
      owner_thread_id = 0;
    }
    const auto tls_initialized =
        LoadAt<std::uint8_t>(mailbox.tls_initialized_flag);
    const auto tls_context = reinterpret_cast<std::uintptr_t>(
        mailbox.tls_context_getter());
    if (tls_context == 0) {
      return false;
    }
    const auto tls_main_thread_marker =
        LoadAt<std::uint8_t>(tls_context, kMainThreadTlsMarkerOffset);
    const auto paused =
        LoadAt<std::uint8_t>(jomini_state, kJominiPausedOffset) != 0;
    const auto date_raw =
        LoadAt<std::int32_t>(game_state, kGameStateDateRawOffset);

    // A second direct read is mandatory even before an executor is admitted.
    // It rejects an object replacement at the exact pump boundary without
    // caching any CK3 pointer across frames.
    if (LoadAt<std::uint8_t>(mailbox.tls_initialized_flag) !=
            tls_initialized ||
        reinterpret_cast<std::uintptr_t>(mailbox.tls_context_getter()) !=
            tls_context ||
        LoadAt<std::uint8_t>(tls_context, kMainThreadTlsMarkerOffset) !=
            tls_main_thread_marker ||
        LoadAt<std::uintptr_t>(mailbox.jomini_state_slot) != jomini_state ||
        (LoadAt<std::uint8_t>(jomini_state, kJominiPausedOffset) != 0) !=
            paused ||
        LoadAt<std::uintptr_t>(mailbox.game_state_slot) != game_state ||
        LoadAt<std::int32_t>(game_state, kGameStateDateRawOffset) != date_raw) {
      return false;
    }

    output.pump_epoch = pump_epoch;
    output.thread_id = current_thread_id;
    output.rng_wrapper = rng_wrapper;
    output.rng_state = rng_state;
    output.rng_owner_thread_id = owner_thread_id;
    output.tls_initialized_flag_address = mailbox.tls_initialized_flag;
    output.tls_initialized = tls_initialized;
    output.tls_context = tls_context;
    output.tls_main_thread_marker = tls_main_thread_marker;
    output.jomini_state = jomini_state;
    output.game_state = game_state;
    output.date_raw = date_raw;
    output.paused = paused;
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = {};
    return false;
  }
#endif
}

bool SameExecutionBoundary(const MainThreadExecutionStampV1 &left,
                           const MainThreadExecutionStampV1 &right) noexcept {
  return left.pump_epoch == right.pump_epoch &&
         left.thread_id == right.thread_id &&
         left.tls_initialized_flag_address ==
             right.tls_initialized_flag_address &&
         left.tls_initialized == right.tls_initialized &&
         left.tls_context == right.tls_context &&
         left.tls_main_thread_marker == right.tls_main_thread_marker &&
         left.jomini_state == right.jomini_state &&
         left.game_state == right.game_state &&
         left.date_raw == right.date_raw && left.paused == right.paused;
}

bool SameVerifiedPumpIdentity(const MainThreadExecutionStampV1 &left,
                              const MainThreadExecutionStampV1 &right) noexcept {
  return left.thread_id == right.thread_id &&
         left.tls_initialized_flag_address ==
             right.tls_initialized_flag_address &&
         left.tls_initialized == right.tls_initialized &&
         left.tls_context == right.tls_context &&
         left.tls_main_thread_marker == right.tls_main_thread_marker &&
         left.jomini_state == right.jomini_state &&
         left.game_state == right.game_state &&
         left.date_raw == right.date_raw && left.paused && right.paused;
}

void ResetConsecutivePausedPumpProof(
    MainThreadQueryMailboxV1 &mailbox) noexcept {
  mailbox.last_verified_stamp = {};
  mailbox.last_verified_stamp_valid = false;
  mailbox.owner_thread_id.store(0, std::memory_order_release);
  mailbox.paused_owner_verified_pump_epochs.store(0,
                                                   std::memory_order_release);
}

void RequestConsecutivePausedPumpProofReset(
    MainThreadQueryMailboxV1 &mailbox) noexcept {
  mailbox.proof_reset_requested.store(true, std::memory_order_release);
  mailbox.owner_thread_id.store(0, std::memory_order_release);
  mailbox.paused_owner_verified_pump_epochs.store(0,
                                                   std::memory_order_release);
}

void PublishObservedStamp(MainThreadQueryMailboxV1 &mailbox,
                          const MainThreadExecutionStampV1 &stamp,
                          bool read_success) noexcept {
  mailbox.observed_current_thread_id.store(stamp.thread_id,
                                            std::memory_order_release);
  mailbox.observed_rng_owner_thread_id.store(
      stamp.rng_owner_thread_id, std::memory_order_release);
  mailbox.observed_tls_context.store(stamp.tls_context,
                                     std::memory_order_release);
  mailbox.observed_jomini_state.store(stamp.jomini_state,
                                      std::memory_order_release);
  mailbox.observed_game_state.store(stamp.game_state,
                                    std::memory_order_release);
  mailbox.observed_date_raw.store(stamp.date_raw,
                                  std::memory_order_release);
  mailbox.observed_tls_initialized.store(stamp.tls_initialized,
                                         std::memory_order_release);
  mailbox.observed_tls_main_thread_marker.store(
      stamp.tls_main_thread_marker, std::memory_order_release);
  mailbox.observed_paused.store(stamp.paused, std::memory_order_release);
  mailbox.observed_stamp_read_success.store(read_success,
                                            std::memory_order_release);
}

void AdvanceConsecutivePausedPumpProof(
    MainThreadQueryMailboxV1 &mailbox,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  const bool consecutive =
      mailbox.last_verified_stamp_valid &&
      SameVerifiedPumpIdentity(mailbox.last_verified_stamp, stamp);
  const auto next =
      consecutive
          ? mailbox.paused_owner_verified_pump_epochs.load(
                std::memory_order_relaxed) +
                1
          : 1;
  mailbox.last_verified_stamp = stamp;
  mailbox.last_verified_stamp_valid = true;
  mailbox.owner_thread_id.store(stamp.thread_id, std::memory_order_release);
  mailbox.paused_owner_verified_pump_epochs.store(next,
                                                   std::memory_order_release);
}

bool IsTerminal(MainThreadQueryMailboxStateV1 state) noexcept {
  return state == MainThreadQueryMailboxStateV1::completed ||
         state == MainThreadQueryMailboxStateV1::executor_failed ||
         state == MainThreadQueryMailboxStateV1::cancelled ||
         state == MainThreadQueryMailboxStateV1::infrastructure_failed;
}

MainThreadQueryWaitResultV1
TerminalWaitResult(MainThreadQueryMailboxStateV1 state) noexcept {
  switch (state) {
  case MainThreadQueryMailboxStateV1::completed:
    return MainThreadQueryWaitResultV1::completed;
  case MainThreadQueryMailboxStateV1::executor_failed:
    return MainThreadQueryWaitResultV1::executor_failed;
  case MainThreadQueryMailboxStateV1::cancelled:
    return MainThreadQueryWaitResultV1::cancelled;
  default:
    return MainThreadQueryWaitResultV1::infrastructure_failed;
  }
}

} // namespace

bool InstallMainThreadQueryMailboxV1(
    MainThreadQueryMailboxV1 &mailbox,
    const MainThreadQueryInstallEnvironmentV1 &environment) noexcept {
  if (!environment.exact_build_admitted || environment.module_base == 0) {
    AddFailure(mailbox, main_thread_query_failure_exact_build);
    return false;
  }
  if (!environment.offline_fixture &&
      environment.executor_submission_enabled &&
      environment.permitted_executor == nullptr &&
      environment.permitted_executor_secondary == nullptr &&
      environment.permitted_executor_tertiary == nullptr &&
      environment.permitted_executor_quaternary == nullptr &&
      environment.permitted_executor_quinary == nullptr &&
      environment.permitted_executor_senary == nullptr &&
      environment.permitted_executor_septenary == nullptr &&
      environment.permitted_executor_octonary == nullptr &&
      environment.permitted_executor_nonary == nullptr &&
      environment.permitted_executor_denary == nullptr &&
      environment.permitted_executor_undenary == nullptr &&
      environment.permitted_executor_duodenary == nullptr &&
      environment.permitted_executor_thirdenary == nullptr &&
      environment.permitted_executor_quattuordenary == nullptr &&
      environment.permitted_executor_quindenary == nullptr &&
      environment.permitted_executor_sexdenary == nullptr &&
      environment.permitted_executor_septendenary == nullptr &&
      environment.permitted_executor_octodenary == nullptr &&
      environment.permitted_executor_novemdenary == nullptr &&
      environment.permitted_executor_vigintary == nullptr &&
      environment.permitted_executor_unvigintary == nullptr &&
      environment.permitted_executor_duovigintary == nullptr) {
    AddFailure(mailbox, main_thread_query_failure_request_identity);
    return false;
  }
  if (mailbox.state.load(std::memory_order_acquire) !=
      MainThreadQueryMailboxStateV1::detached) {
    return g_active_mailbox.load(std::memory_order_acquire) == &mailbox;
  }

  void **iat_slot = environment.peek_message_iat_slot_override;
  auto original = environment.resolved_peek_message_override;
  std::uintptr_t rng_slot = environment.global_rng_wrapper_slot_override;
  std::uintptr_t jomini_slot = environment.jomini_state_slot_override;
  std::uintptr_t game_slot = environment.game_state_slot_override;
  std::uintptr_t tls_initialized_flag =
      environment.tls_initialized_flag_override;
  auto tls_context_getter = environment.tls_context_getter_override;
  auto memory_query = environment.memory_query_override;
  auto memory_protect = environment.memory_protect_override;
  std::size_t system_page_size = environment.system_page_size_override;
  if (!environment.offline_fixture) {
    if (!ExactPumpAnchorsMatch(environment.module_base)) {
      AddFailure(mailbox, main_thread_query_failure_pump_anchor);
      return false;
    }
    iat_slot = reinterpret_cast<void **>(environment.module_base +
                                         kPeekMessageWIatSlotRva);
    const auto user32 = GetModuleHandleW(L"user32.dll");
    original = user32 == nullptr
                   ? nullptr
                   : reinterpret_cast<PeekMessageWFunctionV1>(
                         GetProcAddress(user32, "PeekMessageW"));
    rng_slot = environment.module_base + kGlobalRngWrapperSlotRva;
    jomini_slot = environment.module_base + kJominiStateSlotRva;
    game_slot = environment.module_base + kGameStateSlotRva;
    tls_initialized_flag =
        environment.module_base + kMainThreadTlsInitializedFlagRva;
    tls_context_getter = reinterpret_cast<MainThreadTlsContextGetterV1>(
        environment.module_base + kMainThreadTlsContextGetterRva);
    memory_query = &DefaultMemoryQuery;
    memory_protect = &DefaultMemoryProtect;
    SYSTEM_INFO system_information{};
    GetSystemInfo(&system_information);
    system_page_size = system_information.dwPageSize;
  }
  if (iat_slot == nullptr || original == nullptr || rng_slot == 0 ||
      jomini_slot == 0 || game_slot == 0 || memory_query == nullptr ||
      tls_initialized_flag == 0 || tls_context_getter == nullptr ||
      memory_protect == nullptr || system_page_size < sizeof(void *)) {
    AddFailure(mailbox, main_thread_query_failure_iat_identity);
    return false;
  }

  void *observed_iat = nullptr;
#if defined(_MSC_VER)
  __try {
#endif
    observed_iat = *iat_slot;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    AddFailure(mailbox, main_thread_query_failure_iat_identity);
    return false;
  }
#endif
  if (observed_iat != reinterpret_cast<void *>(original)) {
    AddFailure(mailbox, main_thread_query_failure_iat_identity);
    return false;
  }

  MainThreadQueryMailboxV1 *expected_mailbox = nullptr;
  if (!g_active_mailbox.compare_exchange_strong(
          expected_mailbox, &mailbox, std::memory_order_acq_rel,
          std::memory_order_acquire) && expected_mailbox != &mailbox) {
    AddFailure(mailbox, main_thread_query_failure_singleton);
    return false;
  }
  const auto pinned_original =
      g_original_peek_message.load(std::memory_order_acquire);
  if (pinned_original != nullptr && pinned_original != original) {
    AddFailure(mailbox, main_thread_query_failure_iat_identity);
    return false;
  }

  mailbox.failure_flags.store(0, std::memory_order_release);
  mailbox.published_sequence.store(0, std::memory_order_release);
  mailbox.completed_sequence.store(0, std::memory_order_release);
  mailbox.pump_epochs.store(0, std::memory_order_release);
  mailbox.paused_owner_verified_pump_epochs.store(
      0, std::memory_order_release);
  mailbox.executed_requests.store(0, std::memory_order_release);
  mailbox.owner_thread_id.store(0, std::memory_order_release);
  mailbox.observed_current_thread_id.store(0, std::memory_order_release);
  mailbox.observed_rng_owner_thread_id.store(0, std::memory_order_release);
  mailbox.observed_tls_context.store(0, std::memory_order_release);
  mailbox.observed_jomini_state.store(0, std::memory_order_release);
  mailbox.observed_game_state.store(0, std::memory_order_release);
  mailbox.observed_date_raw.store(0, std::memory_order_release);
  mailbox.observed_tls_initialized.store(0, std::memory_order_release);
  mailbox.observed_tls_main_thread_marker.store(0,
                                                std::memory_order_release);
  mailbox.observed_paused.store(false, std::memory_order_release);
  mailbox.observed_stamp_read_success.store(false,
                                             std::memory_order_release);
  mailbox.module_base = environment.module_base;
  mailbox.peek_message_iat_slot = iat_slot;
  mailbox.original_peek_message = original;
  mailbox.global_rng_wrapper_slot = rng_slot;
  mailbox.jomini_state_slot = jomini_slot;
  mailbox.game_state_slot = game_slot;
  mailbox.tls_initialized_flag = tls_initialized_flag;
  mailbox.tls_context_getter = tls_context_getter;
  mailbox.memory_protection_context = environment.memory_protection_context;
  mailbox.memory_query = memory_query;
  mailbox.memory_protect = memory_protect;
  mailbox.system_page_size = system_page_size;
  mailbox.offline_fixture = environment.offline_fixture;
  mailbox.executor_submission_enabled =
      environment.executor_submission_enabled;
  mailbox.permitted_executor = environment.permitted_executor;
  mailbox.permitted_executor_secondary =
      environment.permitted_executor_secondary;
  mailbox.permitted_executor_tertiary =
      environment.permitted_executor_tertiary;
  mailbox.permitted_executor_quaternary =
      environment.permitted_executor_quaternary;
  mailbox.permitted_executor_quinary =
      environment.permitted_executor_quinary;
  mailbox.permitted_executor_senary =
      environment.permitted_executor_senary;
  mailbox.permitted_executor_septenary =
      environment.permitted_executor_septenary;
  mailbox.permitted_executor_octonary =
      environment.permitted_executor_octonary;
  mailbox.permitted_executor_nonary =
      environment.permitted_executor_nonary;
  mailbox.permitted_executor_denary =
      environment.permitted_executor_denary;
  mailbox.permitted_executor_undenary =
      environment.permitted_executor_undenary;
  mailbox.permitted_executor_duodenary =
      environment.permitted_executor_duodenary;
  mailbox.permitted_executor_thirdenary =
      environment.permitted_executor_thirdenary;
  mailbox.permitted_executor_quattuordenary =
      environment.permitted_executor_quattuordenary;
  mailbox.permitted_executor_quindenary =
      environment.permitted_executor_quindenary;
  mailbox.permitted_executor_sexdenary =
      environment.permitted_executor_sexdenary;
  mailbox.permitted_executor_septendenary =
      environment.permitted_executor_septendenary;
  mailbox.permitted_executor_octodenary =
      environment.permitted_executor_octodenary;
  mailbox.permitted_executor_novemdenary =
      environment.permitted_executor_novemdenary;
  mailbox.permitted_executor_vigintary =
      environment.permitted_executor_vigintary;
  mailbox.permitted_executor_unvigintary =
      environment.permitted_executor_unvigintary;
  mailbox.permitted_executor_duovigintary =
      environment.permitted_executor_duovigintary;
  mailbox.executor = nullptr;
  mailbox.executor_context = nullptr;
  mailbox.executor_succeeded = false;
  mailbox.execution_stamp = {};
  mailbox.last_verified_stamp = {};
  mailbox.last_verified_stamp_valid = false;
  mailbox.stop_requested.store(false, std::memory_order_release);
  mailbox.iat_hook_installed.store(false, std::memory_order_release);
  mailbox.proof_reset_requested.store(false, std::memory_order_release);
  mailbox.state.store(MainThreadQueryMailboxStateV1::idle,
                      std::memory_order_release);
  g_original_peek_message.store(original, std::memory_order_release);

  const auto swap_result = AtomicSwapReadOnlyIat(
      mailbox, reinterpret_cast<void *>(original),
      reinterpret_cast<void *>(&XarMainThreadPeekMessageWHookV1));
  if (swap_result != IatSwapResult::swapped) {
    mailbox.state.store(MainThreadQueryMailboxStateV1::detached,
                        std::memory_order_release);
    mailbox.stop_requested.store(true, std::memory_order_release);
    AddFailure(mailbox,
               swap_result == IatSwapResult::identity_mismatch
                   ? main_thread_query_failure_iat_identity
                   : swap_result == IatSwapResult::page_identity_mismatch
                         ? main_thread_query_failure_iat_page_identity
                         : main_thread_query_failure_iat_page_protect);
    return false;
  }
  mailbox.iat_hook_installed.store(true, std::memory_order_release);
  return true;
}

void SignalMainThreadQueryMailboxProcessDetachV1(
    MainThreadQueryMailboxV1 &mailbox) noexcept {
  mailbox.stop_requested.store(true, std::memory_order_release);
}

MainThreadQueryUninstallResultV1 UninstallMainThreadQueryMailboxV1(
    MainThreadQueryMailboxV1 &mailbox,
    std::uint32_t active_call_drain_timeout_milliseconds) noexcept {
  auto *const active = g_active_mailbox.load(std::memory_order_acquire);
  if (active == nullptr) {
    return mailbox.state.load(std::memory_order_acquire) ==
                   MainThreadQueryMailboxStateV1::detached
               ? MainThreadQueryUninstallResultV1::not_installed
               : MainThreadQueryUninstallResultV1::wrong_mailbox;
  }
  if (active != &mailbox) {
    return MainThreadQueryUninstallResultV1::wrong_mailbox;
  }

  mailbox.stop_requested.store(true, std::memory_order_release);
  while (true) {
    auto state = mailbox.state.load(std::memory_order_acquire);
    if (state == MainThreadQueryMailboxStateV1::executing ||
        state == MainThreadQueryMailboxStateV1::publishing) {
      return MainThreadQueryUninstallResultV1::request_active;
    }
    if (state == MainThreadQueryMailboxStateV1::queued) {
      if (mailbox.state.compare_exchange_strong(
              state, MainThreadQueryMailboxStateV1::cancelled,
              std::memory_order_acq_rel, std::memory_order_acquire)) {
        mailbox.completed_sequence.store(
            mailbox.published_sequence.load(std::memory_order_acquire),
            std::memory_order_release);
      }
      continue;
    }
    if (state == MainThreadQueryMailboxStateV1::detached) {
      return MainThreadQueryUninstallResultV1::not_installed;
    }
    if (state == MainThreadQueryMailboxStateV1::detaching) {
      break;
    }
    if (mailbox.state.compare_exchange_strong(
            state, MainThreadQueryMailboxStateV1::detaching,
            std::memory_order_acq_rel, std::memory_order_acquire)) {
      break;
    }
  }

  if (mailbox.iat_hook_installed.load(std::memory_order_acquire)) {
    const auto restored = AtomicSwapReadOnlyIat(
        mailbox, reinterpret_cast<void *>(&XarMainThreadPeekMessageWHookV1),
        reinterpret_cast<void *>(mailbox.original_peek_message));
    if (restored != IatSwapResult::swapped) {
      AddFailure(mailbox,
                 restored == IatSwapResult::page_identity_mismatch
                     ? main_thread_query_failure_iat_page_identity
                     : restored == IatSwapResult::protection_failed
                           ? main_thread_query_failure_iat_page_protect
                           : main_thread_query_failure_uninstall);
      return MainThreadQueryUninstallResultV1::iat_restore_failed;
    }
    mailbox.iat_hook_installed.store(false, std::memory_order_release);
  }

  const auto started = GetTickCount64();
  while (mailbox.active_hook_calls.load(std::memory_order_acquire) != 0) {
    if (GetTickCount64() - started >=
        active_call_drain_timeout_milliseconds) {
      return MainThreadQueryUninstallResultV1::active_hook_calls_pending;
    }
    Sleep(1);
  }

  // The restored IAT prevents new normal entrants.  This bounded drain waits
  // for calls that have already incremented the counter so stop/reinstall does
  // not race their mailbox writes.  It is not an unload proof: a thread may
  // have fetched the old IAT target without entering the hook yet.
  MemoryBarrier();
  SwitchToThread();
  if (mailbox.active_hook_calls.load(std::memory_order_acquire) != 0) {
    return MainThreadQueryUninstallResultV1::active_hook_calls_pending;
  }

  // Process-lifetime pin: a thread may already have fetched the old IAT target
  // but not yet incremented active_hook_calls.  Keeping both globals and this
  // mailbox alive until process exit makes that delayed entry harmless.  The
  // bridge must never FreeLibrary this v1 hook module.
  mailbox.state.store(MainThreadQueryMailboxStateV1::detached,
                      std::memory_order_release);
  return MainThreadQueryUninstallResultV1::uninstalled;
}

MainThreadQuerySubmitResultV1 TrySubmitMainThreadQueryV1(
    MainThreadQueryMailboxV1 &mailbox, MainThreadQueryExecutorV1 executor,
    void *context, MainThreadQueryTicketV1 &ticket) noexcept {
  ticket = {};
  if (executor == nullptr || context == nullptr) {
    return MainThreadQuerySubmitResultV1::invalid_request;
  }
  if ((mailbox.permitted_executor != nullptr ||
       mailbox.permitted_executor_secondary != nullptr ||
       mailbox.permitted_executor_tertiary != nullptr ||
       mailbox.permitted_executor_quaternary != nullptr ||
       mailbox.permitted_executor_quinary != nullptr ||
       mailbox.permitted_executor_senary != nullptr ||
       mailbox.permitted_executor_septenary != nullptr ||
       mailbox.permitted_executor_octonary != nullptr ||
       mailbox.permitted_executor_nonary != nullptr ||
       mailbox.permitted_executor_denary != nullptr ||
       mailbox.permitted_executor_undenary != nullptr ||
       mailbox.permitted_executor_duodenary != nullptr ||
       mailbox.permitted_executor_thirdenary != nullptr ||
       mailbox.permitted_executor_quattuordenary != nullptr ||
       mailbox.permitted_executor_quindenary != nullptr ||
       mailbox.permitted_executor_sexdenary != nullptr ||
       mailbox.permitted_executor_septendenary != nullptr ||
       mailbox.permitted_executor_octodenary != nullptr ||
       mailbox.permitted_executor_novemdenary != nullptr ||
       mailbox.permitted_executor_vigintary != nullptr ||
       mailbox.permitted_executor_unvigintary != nullptr ||
       mailbox.permitted_executor_duovigintary != nullptr) &&
      executor != mailbox.permitted_executor &&
      executor != mailbox.permitted_executor_secondary &&
      executor != mailbox.permitted_executor_tertiary &&
      executor != mailbox.permitted_executor_quaternary &&
      executor != mailbox.permitted_executor_quinary &&
      executor != mailbox.permitted_executor_senary &&
      executor != mailbox.permitted_executor_septenary &&
      executor != mailbox.permitted_executor_octonary &&
      executor != mailbox.permitted_executor_nonary &&
      executor != mailbox.permitted_executor_denary &&
      executor != mailbox.permitted_executor_undenary &&
      executor != mailbox.permitted_executor_duodenary &&
      executor != mailbox.permitted_executor_thirdenary &&
      executor != mailbox.permitted_executor_quattuordenary &&
      executor != mailbox.permitted_executor_quindenary &&
      executor != mailbox.permitted_executor_sexdenary &&
      executor != mailbox.permitted_executor_septendenary &&
      executor != mailbox.permitted_executor_octodenary &&
      executor != mailbox.permitted_executor_novemdenary &&
      executor != mailbox.permitted_executor_vigintary &&
      executor != mailbox.permitted_executor_unvigintary &&
      executor != mailbox.permitted_executor_duovigintary) {
    return MainThreadQuerySubmitResultV1::invalid_request;
  }
  if (!mailbox.executor_submission_enabled) {
    return MainThreadQuerySubmitResultV1::executor_submission_disabled;
  }
  if (mailbox.stop_requested.load(std::memory_order_acquire)) {
    return MainThreadQuerySubmitResultV1::mailbox_not_installed;
  }
  const auto state = mailbox.state.load(std::memory_order_acquire);
  if (state == MainThreadQueryMailboxStateV1::detached) {
    return MainThreadQuerySubmitResultV1::mailbox_not_installed;
  }
  if (mailbox.failure_flags.load(std::memory_order_acquire) != 0) {
    return MainThreadQuerySubmitResultV1::infrastructure_failed;
  }
  if (mailbox.owner_thread_id.load(std::memory_order_acquire) == 0 ||
      mailbox.paused_owner_verified_pump_epochs.load(
          std::memory_order_acquire) <
          kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs) {
    return MainThreadQuerySubmitResultV1::paused_main_thread_not_observed;
  }

  auto expected = MainThreadQueryMailboxStateV1::idle;
  if (!mailbox.state.compare_exchange_strong(
          expected, MainThreadQueryMailboxStateV1::publishing,
          std::memory_order_acq_rel, std::memory_order_acquire)) {
    return MainThreadQuerySubmitResultV1::mailbox_busy;
  }
  if (mailbox.failure_flags.load(std::memory_order_acquire) != 0) {
    mailbox.state.store(MainThreadQueryMailboxStateV1::idle,
                        std::memory_order_release);
    return MainThreadQuerySubmitResultV1::infrastructure_failed;
  }

  const auto sequence =
      mailbox.next_sequence.fetch_add(1, std::memory_order_acq_rel) + 1;
  mailbox.executor = executor;
  mailbox.executor_context = context;
  mailbox.executor_succeeded = false;
  mailbox.execution_stamp = {};
  mailbox.published_sequence.store(sequence, std::memory_order_relaxed);
  ticket.sequence = sequence;
  mailbox.state.store(MainThreadQueryMailboxStateV1::queued,
                      std::memory_order_release);
  return MainThreadQuerySubmitResultV1::submitted;
}

MainThreadQueryCancelResultV1 CancelMainThreadQueryV1(
    MainThreadQueryMailboxV1 &mailbox,
    const MainThreadQueryTicketV1 &ticket) noexcept {
  if (ticket.sequence == 0 ||
      mailbox.published_sequence.load(std::memory_order_acquire) !=
          ticket.sequence) {
    return MainThreadQueryCancelResultV1::ticket_mismatch;
  }
  auto state = mailbox.state.load(std::memory_order_acquire);
  if (IsTerminal(state)) {
    return MainThreadQueryCancelResultV1::already_terminal;
  }
  if (state == MainThreadQueryMailboxStateV1::executing) {
    return MainThreadQueryCancelResultV1::executing;
  }
  if (state != MainThreadQueryMailboxStateV1::queued) {
    return MainThreadQueryCancelResultV1::ticket_mismatch;
  }
  if (!mailbox.state.compare_exchange_strong(
          state, MainThreadQueryMailboxStateV1::cancelled,
          std::memory_order_acq_rel, std::memory_order_acquire)) {
    return state == MainThreadQueryMailboxStateV1::executing
               ? MainThreadQueryCancelResultV1::executing
               : MainThreadQueryCancelResultV1::already_terminal;
  }
  mailbox.completed_sequence.store(ticket.sequence,
                                   std::memory_order_release);
  return MainThreadQueryCancelResultV1::cancelled;
}

MainThreadQueryWaitResultV1 WaitForMainThreadQueryV1(
    MainThreadQueryMailboxV1 &mailbox,
    const MainThreadQueryTicketV1 &ticket,
    std::uint32_t timeout_milliseconds) noexcept {
  if (ticket.sequence == 0 ||
      mailbox.published_sequence.load(std::memory_order_acquire) !=
          ticket.sequence) {
    return MainThreadQueryWaitResultV1::ticket_mismatch;
  }
  const auto started = GetTickCount64();
  while (true) {
    const auto state = mailbox.state.load(std::memory_order_acquire);
    if (IsTerminal(state)) {
      return TerminalWaitResult(state);
    }
    if (GetTickCount64() - started >= timeout_milliseconds) {
      const auto cancelled = CancelMainThreadQueryV1(mailbox, ticket);
      if (cancelled == MainThreadQueryCancelResultV1::cancelled) {
        return MainThreadQueryWaitResultV1::timeout_cancelled_before_execution;
      }
      if (cancelled == MainThreadQueryCancelResultV1::executing) {
        return MainThreadQueryWaitResultV1::timeout_executor_already_running;
      }
      const auto terminal = mailbox.state.load(std::memory_order_acquire);
      return IsTerminal(terminal)
                 ? TerminalWaitResult(terminal)
                 : MainThreadQueryWaitResultV1::ticket_mismatch;
    }
    Sleep(1);
  }
}

MainThreadQueryReclaimResultV1 ReclaimMainThreadQueryV1(
    MainThreadQueryMailboxV1 &mailbox,
    const MainThreadQueryTicketV1 &ticket) noexcept {
  if (ticket.sequence == 0 ||
      mailbox.published_sequence.load(std::memory_order_acquire) !=
          ticket.sequence) {
    return MainThreadQueryReclaimResultV1::ticket_mismatch;
  }
  const auto state = mailbox.state.load(std::memory_order_acquire);
  if (!IsTerminal(state)) {
    return MainThreadQueryReclaimResultV1::not_terminal;
  }
  if (mailbox.completed_sequence.load(std::memory_order_acquire) !=
      ticket.sequence) {
    return MainThreadQueryReclaimResultV1::ticket_mismatch;
  }
  mailbox.executor = nullptr;
  mailbox.executor_context = nullptr;
  mailbox.executor_succeeded = false;
  mailbox.execution_stamp = {};
  mailbox.state.store(MainThreadQueryMailboxStateV1::idle,
                      std::memory_order_release);
  return MainThreadQueryReclaimResultV1::reclaimed;
}

bool ObserveMainThreadPumpAndDrainV1(
    MainThreadQueryMailboxV1 &mailbox, std::uintptr_t return_rva,
    std::uint32_t current_thread_id) noexcept {
  if (return_rva != kSdlWindowsPumpFirstPeekReturnRva) {
    return false;
  }
  if (mailbox.stop_requested.load(std::memory_order_acquire)) {
    return false;
  }
  const auto pump_epoch =
      mailbox.pump_epochs.fetch_add(1, std::memory_order_acq_rel) + 1;
  if (mailbox.drain_guard.test_and_set(std::memory_order_acq_rel)) {
    RequestConsecutivePausedPumpProofReset(mailbox);
    AddFailure(mailbox, main_thread_query_failure_reentry);
    return false;
  }

  if (mailbox.proof_reset_requested.exchange(false,
                                              std::memory_order_acq_rel)) {
    ResetConsecutivePausedPumpProof(mailbox);
  }

  MainThreadExecutionStampV1 before{};
  if (!ReadExecutionStamp(mailbox, pump_epoch, current_thread_id, before)) {
    before.pump_epoch = pump_epoch;
    before.thread_id = current_thread_id;
    PublishObservedStamp(mailbox, before, false);
    ResetConsecutivePausedPumpProof(mailbox);
    mailbox.drain_guard.clear(std::memory_order_release);
    return false;
  }
  PublishObservedStamp(mailbox, before, true);
  if (before.tls_initialized != 1 ||
      before.tls_main_thread_marker != 1 || before.tls_context == 0) {
    ResetConsecutivePausedPumpProof(mailbox);
    AddFailure(mailbox, main_thread_query_failure_tls_identity);
    auto queued = MainThreadQueryMailboxStateV1::queued;
    if (mailbox.state.compare_exchange_strong(
            queued, MainThreadQueryMailboxStateV1::infrastructure_failed,
            std::memory_order_acq_rel, std::memory_order_acquire)) {
      mailbox.completed_sequence.store(
          mailbox.published_sequence.load(std::memory_order_acquire),
          std::memory_order_release);
    }
    mailbox.drain_guard.clear(std::memory_order_release);
    return false;
  }
  if (!before.paused) {
    ResetConsecutivePausedPumpProof(mailbox);
    mailbox.drain_guard.clear(std::memory_order_release);
    return false;
  }

  AdvanceConsecutivePausedPumpProof(mailbox, before);
  if (mailbox.proof_reset_requested.exchange(false,
                                              std::memory_order_acq_rel)) {
    ResetConsecutivePausedPumpProof(mailbox);
    mailbox.drain_guard.clear(std::memory_order_release);
    return false;
  }

  auto expected_state = MainThreadQueryMailboxStateV1::queued;
  if (!mailbox.state.compare_exchange_strong(
          expected_state, MainThreadQueryMailboxStateV1::executing,
          std::memory_order_acq_rel, std::memory_order_acquire)) {
    mailbox.drain_guard.clear(std::memory_order_release);
    return false;
  }

  const auto sequence =
      mailbox.published_sequence.load(std::memory_order_acquire);
  if (mailbox.stop_requested.load(std::memory_order_acquire) ||
      mailbox.proof_reset_requested.exchange(false,
                                              std::memory_order_acq_rel) ||
      mailbox.failure_flags.load(std::memory_order_acquire) != 0) {
    ResetConsecutivePausedPumpProof(mailbox);
    mailbox.completed_sequence.store(sequence, std::memory_order_release);
    mailbox.state.store(MainThreadQueryMailboxStateV1::infrastructure_failed,
                        std::memory_order_release);
    mailbox.drain_guard.clear(std::memory_order_release);
    return false;
  }
  const auto executor = mailbox.executor;
  void *const context = mailbox.executor_context;
  if (sequence == 0 || executor == nullptr || context == nullptr) {
    AddFailure(mailbox, main_thread_query_failure_request_identity);
    mailbox.completed_sequence.store(sequence, std::memory_order_release);
    mailbox.state.store(MainThreadQueryMailboxStateV1::infrastructure_failed,
                        std::memory_order_release);
    mailbox.drain_guard.clear(std::memory_order_release);
    return false;
  }

  bool succeeded = false;
#if defined(_MSC_VER)
  __try {
#endif
    succeeded = executor(context, before);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    AddFailure(mailbox, main_thread_query_failure_executor_exception);
    succeeded = false;
  }
#endif

  MainThreadExecutionStampV1 after{};
  const bool after_ready =
      ReadExecutionStamp(mailbox, pump_epoch, current_thread_id, after);
  mailbox.execution_stamp = before;
  mailbox.executor_succeeded = succeeded;
  mailbox.executed_requests.fetch_add(1, std::memory_order_acq_rel);
  mailbox.completed_sequence.store(sequence, std::memory_order_release);
  if (!after_ready || !SameExecutionBoundary(before, after)) {
    ResetConsecutivePausedPumpProof(mailbox);
    AddFailure(mailbox, main_thread_query_failure_post_execution_drift);
    mailbox.state.store(MainThreadQueryMailboxStateV1::infrastructure_failed,
                        std::memory_order_release);
  } else {
    mailbox.state.store(
        succeeded ? MainThreadQueryMailboxStateV1::completed
                  : MainThreadQueryMailboxStateV1::executor_failed,
        std::memory_order_release);
  }
  mailbox.drain_guard.clear(std::memory_order_release);
  return true;
}

MainThreadQueryMailboxDiagnosticsV1 ReadMainThreadQueryMailboxDiagnosticsV1(
    const MainThreadQueryMailboxV1 &mailbox) noexcept {
  MainThreadQueryMailboxDiagnosticsV1 output{};
  output.state = mailbox.state.load(std::memory_order_acquire);
  output.failure_flags =
      mailbox.failure_flags.load(std::memory_order_acquire);
  output.pump_epochs = mailbox.pump_epochs.load(std::memory_order_acquire);
  output.paused_owner_verified_pump_epochs =
      mailbox.paused_owner_verified_pump_epochs.load(
          std::memory_order_acquire);
  output.executed_requests =
      mailbox.executed_requests.load(std::memory_order_acquire);
  output.completed_sequence =
      mailbox.completed_sequence.load(std::memory_order_acquire);
  output.owner_thread_id =
      mailbox.owner_thread_id.load(std::memory_order_acquire);
  output.observed_current_thread_id =
      mailbox.observed_current_thread_id.load(std::memory_order_acquire);
  output.observed_rng_owner_thread_id =
      mailbox.observed_rng_owner_thread_id.load(std::memory_order_acquire);
  output.observed_tls_context =
      mailbox.observed_tls_context.load(std::memory_order_acquire);
  output.observed_jomini_state =
      mailbox.observed_jomini_state.load(std::memory_order_acquire);
  output.observed_game_state =
      mailbox.observed_game_state.load(std::memory_order_acquire);
  output.observed_date_raw =
      mailbox.observed_date_raw.load(std::memory_order_acquire);
  output.observed_tls_initialized =
      mailbox.observed_tls_initialized.load(std::memory_order_acquire);
  output.observed_tls_main_thread_marker =
      mailbox.observed_tls_main_thread_marker.load(
          std::memory_order_acquire);
  output.observed_paused =
      mailbox.observed_paused.load(std::memory_order_acquire);
  output.observed_stamp_read_success =
      mailbox.observed_stamp_read_success.load(std::memory_order_acquire);
  output.active_hook_calls =
      mailbox.active_hook_calls.load(std::memory_order_acquire);
  output.iat_installed =
      mailbox.iat_hook_installed.load(std::memory_order_acquire);
  output.stop_requested =
      mailbox.stop_requested.load(std::memory_order_acquire);
  output.executor_submission_enabled = mailbox.executor_submission_enabled;
  output.paused_main_thread_observed =
      output.owner_thread_id != 0 &&
      output.paused_owner_verified_pump_epochs >=
          kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs;
  output.ready = output.iat_installed && !output.stop_requested &&
                 output.failure_flags == 0 &&
                 output.paused_main_thread_observed;
  return output;
}

extern "C" BOOL WINAPI XarMainThreadPeekMessageWHookV1(
    LPMSG message, HWND window, UINT minimum_filter, UINT maximum_filter,
    UINT remove_message) noexcept {
  const auto return_address =
      reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  auto *const mailbox = g_active_mailbox.load(std::memory_order_acquire);
  const auto original =
      g_original_peek_message.load(std::memory_order_acquire);
  if (original == nullptr) {
    return FALSE;
  }
  if (mailbox != nullptr) {
    mailbox->active_hook_calls.fetch_add(1, std::memory_order_acq_rel);
  }

  const BOOL result = original(message, window, minimum_filter,
                               maximum_filter, remove_message);
  const DWORD original_last_error = GetLastError();
  if (mailbox != nullptr &&
      !mailbox->stop_requested.load(std::memory_order_acquire) &&
      return_address >= mailbox->module_base) {
    const auto return_rva = return_address - mailbox->module_base;
    ObserveMainThreadPumpAndDrainV1(*mailbox, return_rva,
                                   GetCurrentThreadId());
  }
  if (mailbox != nullptr) {
    mailbox->active_hook_calls.fetch_sub(1, std::memory_order_acq_rel);
  }
  SetLastError(original_last_error);
  return result;
}

} // namespace xar::ck3_11906
