#include "xar_bridge/marriage_proposal_resolution_journal_v1.hpp"

#include <intrin.h>

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>
#include <thread>

namespace xar::bridge {
namespace {

constexpr std::array<std::uintptr_t, kMarriageResolutionHookCountV1>
    kHookRvas{kMarriageResolutionDispatchRvaV1,
              kMarriageResolutionImmediateRvaV1,
              kMarriageResolutionResponseRvaV1,
              kMarriageResolutionConstructRvaV1,
              kMarriageResolutionDeleteRvaV1};
constexpr std::size_t kContextDefinitionOffset = 0x00;
constexpr std::size_t kContextActorOffset = 0x2D8;
constexpr std::size_t kContextRecipientOffset = 0x2DC;
constexpr std::size_t kContextSubjectOffset = 0x2E0;
constexpr std::size_t kContextCandidateOffset = 0x2E4;
constexpr std::size_t kContextIntermediaryOffset = 0x2E8;
constexpr std::size_t kPendingIdOffset = 0x10;
constexpr std::size_t kPendingContextOffset = 0x18;
constexpr std::size_t kPendingSpecialPointerOffset = 0x348;
constexpr std::size_t kPendingRouteOffset = 0x5C0;
constexpr std::size_t kComponentSlotsOffset = 0x20;
constexpr std::size_t kComponentCapacityOffset = 0x2C;
constexpr std::size_t kComponentSlotStride = 0x10;
constexpr std::size_t kComponentSlotObjectOffset = 0x08;
constexpr std::int32_t kMaximumPendingCapacity = 1'000'000;
constexpr std::uint32_t kMaximumActiveCallWaits = 1'000'000;

std::atomic<MarriageProposalResolutionJournalDetourStateV1 *> g_active_state{
    nullptr};
std::atomic<MarriageResolutionDispatchOriginalV1> g_dispatch_original{nullptr};
std::atomic<MarriageResolutionImmediateOriginalV1> g_immediate_original{
    nullptr};
std::atomic<MarriageResolutionResponseOriginalV1> g_response_original{nullptr};
std::atomic<MarriageResolutionConstructOriginalV1> g_construct_original{
    nullptr};
std::atomic<MarriageResolutionDeleteOriginalV1> g_delete_original{nullptr};

struct DispatchFrameV1 {
  MarriageProposalResolutionJournalDetourStateV1 *state = nullptr;
  MarriageProposalResolutionIdentityV1 identity{};
  bool nested_terminal_or_pending_observed = false;
};

thread_local std::array<DispatchFrameV1, 8> g_dispatch_frames{};
thread_local std::size_t g_dispatch_depth = 0;

template <typename Callback>
bool FaultBoundary(Callback callback) noexcept {
#if defined(_MSC_VER)
  __try {
    return callback();
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  return callback();
#endif
}

template <typename Value>
Value LoadAt(const void *base, std::size_t offset) noexcept {
  Value value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset,
              sizeof(value));
  return value;
}

std::int32_t NativeId(std::uint32_t value) noexcept {
  std::int32_t output = -1;
  static_assert(sizeof(output) == sizeof(value));
  std::memcpy(&output, &value, sizeof(output));
  return output;
}

class JournalGuardV1 {
public:
  explicit JournalGuardV1(
      MarriageProposalResolutionJournalDetourStateV1 &state) noexcept
      : state_(state) {
    while (state_.journal_lock.test_and_set(std::memory_order_acquire)) {
      _mm_pause();
    }
  }
  ~JournalGuardV1() { state_.journal_lock.clear(std::memory_order_release); }
  JournalGuardV1(const JournalGuardV1 &) = delete;
  JournalGuardV1 &operator=(const JournalGuardV1 &) = delete;

private:
  MarriageProposalResolutionJournalDetourStateV1 &state_;
};

class ActiveCallGuardV1 {
public:
  ActiveCallGuardV1() noexcept
      : state_(g_active_state.load(std::memory_order_acquire)) {
    if (state_ != nullptr) {
      state_->active_calls.fetch_add(1, std::memory_order_acq_rel);
      if (g_active_state.load(std::memory_order_acquire) != state_) {
        state_->active_calls.fetch_sub(1, std::memory_order_acq_rel);
        state_ = nullptr;
      }
    }
  }
  ~ActiveCallGuardV1() {
    if (state_ != nullptr) {
      state_->active_calls.fetch_sub(1, std::memory_order_acq_rel);
    }
  }
  MarriageProposalResolutionJournalDetourStateV1 *get() const noexcept {
    return state_;
  }

private:
  MarriageProposalResolutionJournalDetourStateV1 *state_ = nullptr;
};

bool ValidIdentity(const MarriageProposalResolutionIdentityV1 &identity)
    noexcept {
  const auto valid_native_id = [](std::int32_t value) {
    return value != -1 && value != 0;
  };
  return identity.interaction_definition != 0 &&
      valid_native_id(identity.actor_character_id) &&
      valid_native_id(identity.recipient_character_id) &&
      valid_native_id(identity.subject_character_id) &&
      valid_native_id(identity.candidate_character_id) &&
      identity.subject_character_id != identity.candidate_character_id &&
      (identity.intermediary_character_id == -1 ||
       valid_native_id(identity.intermediary_character_id));
}

bool ReadContextIdentityUnsafe(
    const void *context,
    MarriageProposalResolutionIdentityV1 &output) noexcept {
  if (context == nullptr) {
    return false;
  }
  output.interaction_definition =
      LoadAt<std::uintptr_t>(context, kContextDefinitionOffset);
  output.actor_character_id =
      LoadAt<std::int32_t>(context, kContextActorOffset);
  output.recipient_character_id =
      LoadAt<std::int32_t>(context, kContextRecipientOffset);
  output.subject_character_id =
      LoadAt<std::int32_t>(context, kContextSubjectOffset);
  output.candidate_character_id =
      LoadAt<std::int32_t>(context, kContextCandidateOffset);
  output.intermediary_character_id =
      LoadAt<std::int32_t>(context, kContextIntermediaryOffset);
  return ValidIdentity(output);
}

bool ReadContextIdentity(
    const void *context,
    MarriageProposalResolutionIdentityV1 &output) noexcept {
  output = {};
  return FaultBoundary(
      [&]() noexcept { return ReadContextIdentityUnsafe(context, output); });
}

bool MatchesArmed(
    MarriageProposalResolutionJournalDetourStateV1 &state,
    const MarriageProposalResolutionIdentityV1 &identity) noexcept {
  JournalGuardV1 guard(state);
  return state.identity_armed && state.armed_identity == identity;
}

bool PublishResolution(
    MarriageProposalResolutionJournalDetourStateV1 &state,
    const MarriageProposalResolutionIdentityV1 &identity,
    MarriageProposalNativeResolutionV1 resolution,
    std::int32_t pending_id = -1) noexcept {
  JournalGuardV1 guard(state);
  if (!state.identity_armed || state.armed_identity != identity) {
    return false;
  }
  if (pending_id != -1) {
    if (pending_id == 0 ||
        (state.pending_id != -1 && state.pending_id != pending_id)) {
      state.failure_flags.fetch_or(
          marriage_resolution_install_failure_identity,
          std::memory_order_acq_rel);
      return false;
    }
    state.pending_id = pending_id;
  }
  if (!state.resolution_ready ||
      state.resolution == MarriageProposalNativeResolutionV1::pending ||
      state.resolution == resolution) {
    state.resolution = resolution;
    state.resolution_ready = true;
    return true;
  }
  state.failure_flags.fetch_or(marriage_resolution_install_failure_identity,
                               std::memory_order_acq_rel);
  state.resolution = MarriageProposalNativeResolutionV1::invalidated;
  state.resolution_ready = false;
  return false;
}

void MarkNestedObservation(
    MarriageProposalResolutionJournalDetourStateV1 &state,
    const MarriageProposalResolutionIdentityV1 &identity) noexcept {
  if (g_dispatch_depth == 0) {
    return;
  }
  auto &frame = g_dispatch_frames[g_dispatch_depth - 1];
  if (frame.state == &state && frame.identity == identity) {
    frame.nested_terminal_or_pending_observed = true;
  }
}

bool ReadPendingIdentityUnsafe(
    const MarriageProposalResolutionJournalDetourStateV1 &state,
    const void *pending, MarriageProposalResolutionIdentityV1 &identity,
    std::int32_t &pending_id, std::uint8_t &route) noexcept {
  if (pending == nullptr) {
    return false;
  }
  pending_id = LoadAt<std::int32_t>(pending, kPendingIdOffset);
  route = LoadAt<std::uint8_t>(pending, kPendingRouteOffset);
  if (!ReadContextIdentityUnsafe(
          static_cast<const std::byte *>(pending) + kPendingContextOffset,
      identity) ||
      pending_id == -1 || pending_id == 0) {
    return false;
  }
  void *const special =
      LoadAt<void *>(pending, kPendingSpecialPointerOffset);
  if (special == nullptr ||
      LoadAt<std::uintptr_t>(special, 0) !=
          state.module_base + kMarriagePendingSpecialVtableRvaV1) {
    return false;
  }
  return true;
}

bool ReadPendingIdentity(
    const MarriageProposalResolutionJournalDetourStateV1 &state,
    const void *pending, MarriageProposalResolutionIdentityV1 &identity,
    std::int32_t &pending_id, std::uint8_t &route) noexcept {
  identity = {};
  pending_id = -1;
  route = 0xFF;
  return FaultBoundary([&]() noexcept {
    return ReadPendingIdentityUnsafe(state, pending, identity, pending_id,
                                     route);
  });
}

void *ResolvePendingUnsafe(
    const MarriageProposalResolutionJournalDetourStateV1 &state,
    std::int32_t pending_id) noexcept {
  if (state.module_base == 0 || pending_id == -1 || pending_id == 0) {
    return nullptr;
  }
  void *const storage = *reinterpret_cast<void *const *>(
      state.module_base + kMarriagePendingStorageSlotRvaV1);
  if (storage == nullptr) {
    return nullptr;
  }
  void *const slots = LoadAt<void *>(storage, kComponentSlotsOffset);
  const auto capacity =
      LoadAt<std::int32_t>(storage, kComponentCapacityOffset);
  const auto index = static_cast<std::uint32_t>(pending_id) & 0x00FFFFFFU;
  if (slots == nullptr || capacity <= 0 ||
      capacity > kMaximumPendingCapacity ||
      index >= static_cast<std::uint32_t>(capacity)) {
    return nullptr;
  }
  void *const pending = LoadAt<void *>(
      slots, static_cast<std::size_t>(index) * kComponentSlotStride +
                 kComponentSlotObjectOffset);
  return pending != nullptr &&
                 LoadAt<std::int32_t>(pending, kPendingIdOffset) == pending_id
             ? pending
             : nullptr;
}

void WriteAbsoluteJump(std::uint8_t *destination,
                       std::uintptr_t target) noexcept {
  constexpr std::array<std::uint8_t, 6> prefix{
      0xFF, 0x25, 0x00, 0x00, 0x00, 0x00};
  std::memcpy(destination, prefix.data(), prefix.size());
  std::memcpy(destination + prefix.size(), &target, sizeof(target));
}

void *DefaultVirtualAlloc(void *, std::size_t size, DWORD allocation_type,
                          DWORD protection) noexcept {
  return VirtualAlloc(nullptr, size, allocation_type, protection);
}

bool DefaultVirtualFree(void *, void *address, std::size_t size,
                        DWORD free_type) noexcept {
  return VirtualFree(address, size, free_type) != FALSE;
}

bool DefaultVirtualProtect(void *, void *address, std::size_t size,
                           DWORD protection, DWORD &old) noexcept {
  return VirtualProtect(address, size, protection, &old) != FALSE;
}

bool DefaultFlush(void *, const void *address, std::size_t size) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}

void AddFailure(MarriageProposalResolutionJournalDetourStateV1 &state,
                MarriageProposalResolutionJournalInstallFailureV1 failure)
    noexcept {
  state.failure_flags.fetch_or(static_cast<std::uint32_t>(failure),
                               std::memory_order_acq_rel);
}

bool Flush(MarriageProposalResolutionJournalDetourStateV1 &state,
           const void *address, std::size_t size) noexcept {
  if (state.flush_instruction_cache == nullptr ||
      !state.flush_instruction_cache(state.memory_context, address, size)) {
    AddFailure(state, marriage_resolution_install_failure_flush);
    return false;
  }
  return true;
}

bool WritePatch(MarriageProposalResolutionJournalDetourStateV1 &state,
                std::size_t index, const std::uint8_t *expected,
                const std::uint8_t *desired) noexcept {
  const auto target = state.targets[index];
  const auto size = kMarriageResolutionPatchSizesV1[index];
  if (target == 0 ||
      std::memcmp(reinterpret_cast<const void *>(target), expected, size) !=
          0) {
    AddFailure(state, marriage_resolution_install_failure_anchor);
    return false;
  }
  DWORD old = 0;
  if (state.virtual_protect == nullptr ||
      !state.virtual_protect(state.memory_context,
                             reinterpret_cast<void *>(target), size,
                             PAGE_EXECUTE_READWRITE, old)) {
    AddFailure(state, marriage_resolution_install_failure_protection);
    return false;
  }
  std::memcpy(reinterpret_cast<void *>(target), desired, size);
  const bool identity =
      std::memcmp(reinterpret_cast<const void *>(target), desired, size) == 0;
  const bool flushed = Flush(state, reinterpret_cast<void *>(target), size);
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(target), size, old,
      ignored);
  if (identity && flushed && restored) {
    return true;
  }
  AddFailure(state, marriage_resolution_install_failure_protection);
  return false;
}

void FreeTrampolines(
    MarriageProposalResolutionJournalDetourStateV1 &state) noexcept {
  if (state.virtual_free != nullptr) {
    for (auto &trampoline : state.trampolines) {
      if (trampoline != nullptr) {
        (void)state.virtual_free(state.memory_context, trampoline, 0,
                                 MEM_RELEASE);
      }
      trampoline = nullptr;
    }
  }
}

void ClearOriginals() noexcept {
  g_dispatch_original.store(nullptr, std::memory_order_release);
  g_immediate_original.store(nullptr, std::memory_order_release);
  g_response_original.store(nullptr, std::memory_order_release);
  g_construct_original.store(nullptr, std::memory_order_release);
  g_delete_original.store(nullptr, std::memory_order_release);
}

bool InstallTrampoline(
    MarriageProposalResolutionJournalDetourStateV1 &state,
    MarriageResolutionVirtualAllocV1 allocate, std::size_t index) noexcept {
  const auto patch_size = kMarriageResolutionPatchSizesV1[index];
  const auto allocation_size =
      patch_size + kMarriageResolutionAbsoluteJumpBytesV1;
  void *const trampoline = allocate(state.memory_context, allocation_size,
                                    MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (trampoline == nullptr) {
    return false;
  }
  state.trampolines[index] = trampoline;
  auto *const bytes = static_cast<std::uint8_t *>(trampoline);
  std::memcpy(bytes, kMarriageResolutionExpectedPrefixesV1[index].data(),
              patch_size);
  WriteAbsoluteJump(bytes + patch_size, state.targets[index] + patch_size);
  DWORD old = 0;
  return state.virtual_protect != nullptr &&
      state.virtual_protect(state.memory_context, trampoline, allocation_size,
                            PAGE_EXECUTE_READ, old) &&
      old == PAGE_READWRITE && Flush(state, trampoline, allocation_size);
}

std::array<std::uintptr_t, kMarriageResolutionHookCountV1>
HookAddresses() noexcept {
  return {reinterpret_cast<std::uintptr_t>(
              &XarMarriageResolutionDispatchHookV1),
          reinterpret_cast<std::uintptr_t>(
              &XarMarriageResolutionImmediateHookV1),
          reinterpret_cast<std::uintptr_t>(
              &XarMarriageResolutionResponseHookV1),
          reinterpret_cast<std::uintptr_t>(
              &XarMarriageResolutionConstructHookV1),
          reinterpret_cast<std::uintptr_t>(
              &XarMarriageResolutionDeleteHookV1)};
}

void PublishOriginals(
    const MarriageProposalResolutionJournalDetourStateV1 &state) noexcept {
  g_dispatch_original.store(
      reinterpret_cast<MarriageResolutionDispatchOriginalV1>(
          state.trampolines[0]),
      std::memory_order_release);
  g_immediate_original.store(
      reinterpret_cast<MarriageResolutionImmediateOriginalV1>(
          state.trampolines[1]),
      std::memory_order_release);
  g_response_original.store(
      reinterpret_cast<MarriageResolutionResponseOriginalV1>(
          state.trampolines[2]),
      std::memory_order_release);
  g_construct_original.store(
      reinterpret_cast<MarriageResolutionConstructOriginalV1>(
          state.trampolines[3]),
      std::memory_order_release);
  g_delete_original.store(
      reinterpret_cast<MarriageResolutionDeleteOriginalV1>(
          state.trampolines[4]),
      std::memory_order_release);
}

} // namespace

bool InstallMarriageProposalResolutionJournalV1(
    MarriageProposalResolutionJournalDetourStateV1 &state,
    const MarriageProposalResolutionJournalInstallEnvironmentV1 &environment)
    noexcept {
  state.failure_flags.store(marriage_resolution_install_failure_none,
                            std::memory_order_release);
  if (!environment.exact_build_admitted || environment.module_base == 0 ||
      environment.admitted_executable_sha256 !=
          kMarriageProposalResolutionJournalExecutableSha256V1) {
    AddFailure(state, marriage_resolution_install_failure_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    AddFailure(state, marriage_resolution_install_failure_quiescence);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0) {
    return true;
  }
  MarriageProposalResolutionJournalDetourStateV1 *expected = nullptr;
  if (!g_active_state.compare_exchange_strong(
          expected, &state, std::memory_order_acq_rel,
          std::memory_order_acquire)) {
    AddFailure(state, marriage_resolution_install_failure_already_installed);
    return false;
  }
  state.module_base = environment.module_base;
  state.offline_fixture = environment.offline_fixture;
  state.memory_context = environment.memory_context;
  state.virtual_free = environment.virtual_free_override != nullptr
                           ? environment.virtual_free_override
                           : &DefaultVirtualFree;
  state.virtual_protect = environment.virtual_protect_override != nullptr
                              ? environment.virtual_protect_override
                              : &DefaultVirtualProtect;
  state.flush_instruction_cache =
      environment.flush_instruction_cache_override != nullptr
          ? environment.flush_instruction_cache_override
          : &DefaultFlush;
  const auto allocate = environment.virtual_alloc_override != nullptr
                            ? environment.virtual_alloc_override
                            : &DefaultVirtualAlloc;
  for (std::size_t index = 0; index < state.targets.size(); ++index) {
    state.targets[index] = environment.target_overrides[index] != 0
                               ? environment.target_overrides[index]
                               : environment.module_base + kHookRvas[index];
    const auto size = kMarriageResolutionPatchSizesV1[index];
    if (std::memcmp(reinterpret_cast<const void *>(state.targets[index]),
                    kMarriageResolutionExpectedPrefixesV1[index].data(),
                    size) != 0) {
      AddFailure(state, marriage_resolution_install_failure_anchor);
      g_active_state.store(nullptr, std::memory_order_release);
      return false;
    }
    std::memcpy(state.originals[index].data(),
                kMarriageResolutionExpectedPrefixesV1[index].data(), size);
  }
  for (std::size_t index = 0; index < state.trampolines.size(); ++index) {
    if (!InstallTrampoline(state, allocate, index)) {
      AddFailure(state, marriage_resolution_install_failure_allocation);
      FreeTrampolines(state);
      g_active_state.store(nullptr, std::memory_order_release);
      return false;
    }
  }
  PublishOriginals(state);
  const auto hook_addresses = HookAddresses();
  std::array<std::array<std::uint8_t, 15>, kMarriageResolutionHookCountV1>
      patches{};
  std::size_t installed_count = 0;
  for (; installed_count < patches.size(); ++installed_count) {
    auto &patch = patches[installed_count];
    patch.fill(0x90);
    WriteAbsoluteJump(patch.data(), hook_addresses[installed_count]);
    if (!WritePatch(state, installed_count,
                    kMarriageResolutionExpectedPrefixesV1[installed_count]
                        .data(),
                    patch.data())) {
      const auto patch_size =
          kMarriageResolutionPatchSizesV1[installed_count];
      if (std::memcmp(
              reinterpret_cast<const void *>(
                  state.targets[installed_count]),
              patch.data(), patch_size) == 0 &&
          !WritePatch(
              state, installed_count, patch.data(),
              kMarriageResolutionExpectedPrefixesV1[installed_count]
                  .data())) {
        AddFailure(state, marriage_resolution_install_failure_rollback);
      }
      break;
    }
  }
  if (installed_count != patches.size()) {
    while (installed_count != 0) {
      --installed_count;
      if (!WritePatch(state, installed_count,
                      patches[installed_count].data(),
                      kMarriageResolutionExpectedPrefixesV1[installed_count]
                          .data())) {
        AddFailure(state, marriage_resolution_install_failure_rollback);
      }
    }
    ClearOriginals();
    FreeTrampolines(state);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  state.active_calls.store(0, std::memory_order_release);
  state.installed.store(1, std::memory_order_release);
  return true;
}

bool RemoveMarriageProposalResolutionJournalV1(
    MarriageProposalResolutionJournalDetourStateV1 &state,
    bool primary_thread_suspended_proven) noexcept {
  if (!primary_thread_suspended_proven) {
    AddFailure(state, marriage_resolution_install_failure_quiescence);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) == 0) {
    return true;
  }
  if (g_active_state.load(std::memory_order_acquire) != &state) {
    AddFailure(state, marriage_resolution_install_failure_already_installed);
    return false;
  }
  const auto hooks = HookAddresses();
  std::array<std::array<std::uint8_t, 15>, kMarriageResolutionHookCountV1>
      patches{};
  for (std::size_t index = 0; index < patches.size(); ++index) {
    patches[index].fill(0x90);
    WriteAbsoluteJump(patches[index].data(), hooks[index]);
  }
  for (std::size_t remaining = patches.size(); remaining != 0; --remaining) {
    const auto index = remaining - 1;
    if (!WritePatch(state, index, patches[index].data(),
                    state.originals[index].data())) {
      AddFailure(state, marriage_resolution_install_failure_rollback);
      return false;
    }
  }
  MarriageProposalResolutionJournalDetourStateV1 *expected = &state;
  if (!g_active_state.compare_exchange_strong(
          expected, nullptr, std::memory_order_acq_rel,
          std::memory_order_acquire)) {
    AddFailure(state, marriage_resolution_install_failure_already_installed);
    return false;
  }
  for (std::uint32_t wait = 0;
       wait < kMaximumActiveCallWaits &&
       state.active_calls.load(std::memory_order_acquire) != 0;
       ++wait) {
    if ((wait & 0x3FFU) == 0) {
      std::this_thread::yield();
    } else {
      _mm_pause();
    }
  }
  if (state.active_calls.load(std::memory_order_acquire) != 0) {
    AddFailure(state, marriage_resolution_install_failure_active_calls);
    return false;
  }
  ClearOriginals();
  FreeTrampolines(state);
  state.installed.store(0, std::memory_order_release);
  return true;
}

bool ArmMarriageProposalResolutionJournalV1(
    MarriageProposalResolutionJournalDetourStateV1 &state,
    const MarriageProposalSubmissionV1 &submission,
    std::uintptr_t interaction_definition) noexcept {
  MarriageProposalResolutionIdentityV1 identity{
      interaction_definition,
      NativeId(submission.roles.actor_character_id),
      NativeId(submission.roles.recipient_character_id),
      NativeId(submission.roles.secondary_actor_character_id),
      NativeId(submission.roles.secondary_recipient_character_id),
      submission.roles.intermediary_character_id == 0
          ? -1
          : NativeId(submission.roles.intermediary_character_id)};
  if (state.installed.load(std::memory_order_acquire) == 0 ||
      g_active_state.load(std::memory_order_acquire) != &state ||
      !ValidIdentity(identity) ||
      identity.subject_character_id !=
          NativeId(submission.subject_character_id) ||
      identity.candidate_character_id !=
          NativeId(submission.candidate_character_id)) {
    AddFailure(state, marriage_resolution_install_failure_identity);
    return false;
  }
  JournalGuardV1 guard(state);
  state.failure_flags.fetch_and(
      ~static_cast<std::uint32_t>(
          marriage_resolution_install_failure_identity),
      std::memory_order_acq_rel);
  state.armed_identity = identity;
  state.pending_id = -1;
  state.resolution = MarriageProposalNativeResolutionV1::pending;
  state.identity_armed = true;
  state.resolution_ready = false;
  return true;
}

bool ConfigureMarriageProposalResolutionJournalV1(
    MarriageProposalResolutionJournalDetourStateV1 &state,
    MarriageProposalNativeBinderStateV1 &binder) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0 ||
      g_active_state.load(std::memory_order_acquire) != &state) {
    binder.environment.proposal_resolution_certified = false;
    binder.environment.proposal_resolution_context = nullptr;
    binder.environment.read_proposal_resolution = nullptr;
    return false;
  }
  binder.environment.proposal_resolution_context = &state;
  binder.environment.read_proposal_resolution =
      &ReadMarriageProposalResolutionJournalV1;
  binder.environment.proposal_resolution_certified = true;
  return true;
}

bool ReadMarriageProposalResolutionJournalV1(
    void *context, std::uint32_t subject_character_id,
    std::uint32_t candidate_character_id,
    MarriageProposalNativeResolutionV1 &output) noexcept {
  output = MarriageProposalNativeResolutionV1::pending;
  if (context == nullptr) {
    return false;
  }
  auto &state = *static_cast<
      MarriageProposalResolutionJournalDetourStateV1 *>(context);
  if (state.installed.load(std::memory_order_acquire) == 0 ||
      g_active_state.load(std::memory_order_acquire) != &state) {
    return false;
  }
  JournalGuardV1 guard(state);
  if (!state.identity_armed || !state.resolution_ready ||
      (state.failure_flags.load(std::memory_order_acquire) &
       marriage_resolution_install_failure_identity) != 0 ||
      state.armed_identity.subject_character_id !=
          NativeId(subject_character_id) ||
      state.armed_identity.candidate_character_id !=
          NativeId(candidate_character_id)) {
    return false;
  }
  output = state.resolution;
  return true;
}

bool CaptureMarriageResolutionDispatchReturnFixtureV1(
    const MarriageProposalResolutionIdentityV1 &identity,
    bool nested_terminal_or_pending_observed) noexcept {
  auto *const state = g_active_state.load(std::memory_order_acquire);
  return state != nullptr && MatchesArmed(*state, identity) &&
      (nested_terminal_or_pending_observed ||
       PublishResolution(*state, identity,
                         MarriageProposalNativeResolutionV1::invalidated));
}

bool CaptureMarriageResolutionImmediateFixtureV1(
    const MarriageProposalResolutionIdentityV1 &identity,
    std::uint8_t recipient_reply) noexcept {
  auto *const state = g_active_state.load(std::memory_order_acquire);
  return state != nullptr &&
      PublishResolution(
          *state, identity,
          recipient_reply == 1
              ? MarriageProposalNativeResolutionV1::accepted
              : MarriageProposalNativeResolutionV1::refused);
}

bool CaptureMarriageResolutionConstructFixtureV1(
    const MarriageProposalResolutionIdentityV1 &identity,
    std::int32_t pending_id) noexcept {
  auto *const state = g_active_state.load(std::memory_order_acquire);
  return state != nullptr &&
      PublishResolution(*state, identity,
                        MarriageProposalNativeResolutionV1::pending,
                        pending_id);
}

bool CaptureMarriageResolutionResponseFixtureV1(
    const MarriageProposalResolutionIdentityV1 &identity,
    std::int32_t pending_id, std::uint8_t route,
    std::int32_t recipient_reply) noexcept {
  auto *const state = g_active_state.load(std::memory_order_acquire);
  if (state == nullptr || route != 0 || !MatchesArmed(*state, identity)) {
    return false;
  }
  if (recipient_reply == 4) {
    return true;
  }
  if (recipient_reply != 0 && recipient_reply != 1) {
    AddFailure(*state, marriage_resolution_install_failure_identity);
    return false;
  }
  const auto resolution = recipient_reply == 0
      ? MarriageProposalNativeResolutionV1::accepted
      : MarriageProposalNativeResolutionV1::refused;
  return PublishResolution(*state, identity, resolution, pending_id);
}

bool CaptureMarriageResolutionDeleteFixtureV1(
    std::int32_t pending_id, std::uintptr_t caller_rva) noexcept {
  auto *const state = g_active_state.load(std::memory_order_acquire);
  if (state == nullptr ||
      (caller_rva != kMarriageDeleteInvalidatedCallerRvaV1 &&
       caller_rva != kMarriageDeleteExpiredCallerRvaV1)) {
    return false;
  }
  JournalGuardV1 guard(*state);
  if (!state->identity_armed || state->pending_id != pending_id) {
    return false;
  }
  state->resolution = MarriageProposalNativeResolutionV1::invalidated;
  state->resolution_ready = true;
  return true;
}

extern "C" void __fastcall XarMarriageResolutionDispatchHookV1(
    void *manager, void *context, std::uint8_t intermediary_reply,
    std::uint8_t recipient_reply) noexcept {
  ActiveCallGuardV1 call_guard;
  auto *const state = call_guard.get();
  MarriageProposalResolutionIdentityV1 identity{};
  const bool matching = state != nullptr &&
      ReadContextIdentity(context, identity) && MatchesArmed(*state, identity);
  bool frame_pushed = false;
  if (matching) {
    if (g_dispatch_depth < g_dispatch_frames.size()) {
      g_dispatch_frames[g_dispatch_depth++] = {state, identity, false};
      frame_pushed = true;
    } else {
      AddFailure(*state, marriage_resolution_install_failure_identity);
    }
  }
  const auto original = g_dispatch_original.load(std::memory_order_acquire);
  if (original != nullptr) {
    original(manager, context, intermediary_reply, recipient_reply);
  }
  if (frame_pushed) {
    const bool observed =
        g_dispatch_frames[g_dispatch_depth - 1]
            .nested_terminal_or_pending_observed;
    --g_dispatch_depth;
    if (!observed) {
      (void)PublishResolution(*state, identity,
                              MarriageProposalNativeResolutionV1::invalidated);
    }
  }
}

extern "C" void __fastcall XarMarriageResolutionImmediateHookV1(
    void *manager, void *context, const std::uint8_t *intermediary_reply,
    const std::uint8_t *recipient_reply) noexcept {
  ActiveCallGuardV1 call_guard;
  auto *const state = call_guard.get();
  MarriageProposalResolutionIdentityV1 identity{};
  std::uint8_t reply = 0;
  const bool captured = state != nullptr && recipient_reply != nullptr &&
      ReadContextIdentity(context, identity) &&
      FaultBoundary([&]() noexcept {
        reply = *recipient_reply;
        return true;
      }) &&
      MatchesArmed(*state, identity);
  if (captured) {
    MarkNestedObservation(*state, identity);
  }
  const auto original = g_immediate_original.load(std::memory_order_acquire);
  if (original != nullptr) {
    original(manager, context, intermediary_reply, recipient_reply);
  }
  if (captured) {
    (void)PublishResolution(
        *state, identity,
        reply == 1 ? MarriageProposalNativeResolutionV1::accepted
                   : MarriageProposalNativeResolutionV1::refused);
  }
}

extern "C" void __fastcall XarMarriageResolutionResponseHookV1(
    void *manager, void *pending, std::int32_t intermediary_reply,
    std::int32_t recipient_reply) noexcept {
  ActiveCallGuardV1 call_guard;
  auto *const state = call_guard.get();
  MarriageProposalResolutionIdentityV1 identity{};
  std::int32_t pending_id = -1;
  std::uint8_t route = 0xFF;
  const bool captured = state != nullptr &&
      ReadPendingIdentity(*state, pending, identity, pending_id, route) &&
      MatchesArmed(*state, identity);
  const auto original = g_response_original.load(std::memory_order_acquire);
  if (original != nullptr) {
    original(manager, pending, intermediary_reply, recipient_reply);
  }
  if (captured && route == 0 && recipient_reply != 4) {
    if (recipient_reply == 0 || recipient_reply == 1) {
      const auto resolution = recipient_reply == 0
          ? MarriageProposalNativeResolutionV1::accepted
          : MarriageProposalNativeResolutionV1::refused;
      (void)PublishResolution(*state, identity, resolution, pending_id);
    } else {
      AddFailure(*state, marriage_resolution_install_failure_identity);
    }
  }
}

extern "C" void *__fastcall XarMarriageResolutionConstructHookV1(
    void *storage, void *context, const std::int32_t *cutoff,
    const std::uint8_t *intermediary_reply,
    const std::uint8_t *recipient_reply,
    const std::int32_t *notification) noexcept {
  ActiveCallGuardV1 call_guard;
  auto *const state = call_guard.get();
  const auto original = g_construct_original.load(std::memory_order_acquire);
  void *const pending = original == nullptr
                            ? nullptr
                            : original(storage, context, cutoff,
                                       intermediary_reply, recipient_reply,
                                       notification);
  if (state != nullptr && pending != nullptr) {
    MarriageProposalResolutionIdentityV1 identity{};
    std::int32_t pending_id = -1;
    std::uint8_t route = 0xFF;
    if (ReadPendingIdentity(*state, pending, identity, pending_id, route) &&
        MatchesArmed(*state, identity)) {
      MarkNestedObservation(*state, identity);
      (void)PublishResolution(*state, identity,
                              MarriageProposalNativeResolutionV1::pending,
                              pending_id);
    }
  }
  return pending;
}

extern "C" void __fastcall XarMarriageResolutionDeleteHookV1(
    void *manager, std::int32_t pending_id) noexcept {
  ActiveCallGuardV1 call_guard;
  auto *const state = call_guard.get();
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  bool invalidating = false;
  MarriageProposalResolutionIdentityV1 identity{};
  if (state != nullptr && caller >= state->module_base) {
    const auto caller_rva = caller - state->module_base;
    invalidating = caller_rva == kMarriageDeleteInvalidatedCallerRvaV1 ||
        caller_rva == kMarriageDeleteExpiredCallerRvaV1;
    if (invalidating) {
      void *pending = nullptr;
      if (state->offline_fixture) {
        JournalGuardV1 guard(*state);
        invalidating = state->identity_armed &&
            state->pending_id == pending_id;
        identity = state->armed_identity;
      } else {
        (void)FaultBoundary([&]() noexcept {
          pending = ResolvePendingUnsafe(*state, pending_id);
          return pending != nullptr;
        });
        std::int32_t observed_id = -1;
        std::uint8_t route = 0xFF;
        invalidating = pending != nullptr &&
            ReadPendingIdentity(*state, pending, identity, observed_id,
                                route) &&
            observed_id == pending_id && MatchesArmed(*state, identity);
      }
    }
  }
  const auto original = g_delete_original.load(std::memory_order_acquire);
  if (original != nullptr) {
    original(manager, pending_id);
  }
  if (state != nullptr && invalidating) {
    (void)PublishResolution(*state, identity,
                            MarriageProposalNativeResolutionV1::invalidated,
                            pending_id);
  }
}

} // namespace xar::bridge
