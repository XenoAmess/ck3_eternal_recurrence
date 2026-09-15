#include "xar_bridge/council_production_final_gates_v1.hpp"

#include "xar_bridge/council_replacement_fireability_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>

#include <windows.h>

namespace xar::bridge {
namespace {

constexpr std::uintptr_t kPlayedCharacterIdRva = 0x4FE7EE0;
constexpr std::uintptr_t kIsCouncillorRva = 0x2667300;
constexpr std::uintptr_t kIsGuestRva = 0x18E2A10;
constexpr std::uintptr_t kPendingManagerSetupRva = 0x1058C00;
constexpr std::uintptr_t kHasPendingInteractionRva = 0x2752220;
constexpr std::size_t kCharacterIdOffset = 0x18;
constexpr std::size_t kPendingSetupStorageSize = 0x598;
constexpr std::size_t kPendingManagerOffset = 0x588;

using NativeCharacterPredicate = bool (*)(void *);
using NativePendingManagerSetup = void (*)(void *);
using NativePendingPredicate = bool (*)(void *, std::int32_t);

bool Address(std::uintptr_t base, std::uintptr_t rva,
             std::uintptr_t &value) noexcept {
  if (base == 0 || rva > (std::numeric_limits<std::uintptr_t>::max)() - base) {
    value = 0;
    return false;
  }
  value = base + rva;
  return true;
}

bool NativePredicates(std::uintptr_t councillor_address,
                      std::uintptr_t guest_address,
                      std::uintptr_t pending_setup_address,
                      std::uintptr_t pending_address, void *candidate,
                      std::int32_t candidate_character_id,
                      void *pending_setup_storage, bool &already_councillor,
                      bool &guest, bool &pending) noexcept {
  already_councillor = false;
  guest = false;
  pending = false;
  void *manager = nullptr;
#if defined(_MSC_VER)
  __try {
#endif
    already_councillor =
        reinterpret_cast<NativeCharacterPredicate>(councillor_address)(candidate);
    guest = reinterpret_cast<NativeCharacterPredicate>(guest_address)(candidate);
    reinterpret_cast<NativePendingManagerSetup>(pending_setup_address)(
        pending_setup_storage);
    std::memcpy(&manager,
                static_cast<const std::byte *>(pending_setup_storage) +
                    kPendingManagerOffset,
                sizeof(manager));
    if (manager == nullptr) return false;
    pending = reinterpret_cast<NativePendingPredicate>(pending_address)(
        manager, candidate_character_id);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
  return true;
}

bool ReadBoundValue(
    const ck3_11906::CouncilCompositionStewardCandidatesBindingStateV1 &binding,
    std::uintptr_t address, void *destination, std::size_t size) noexcept {
  return address != 0 && destination != nullptr && size != 0 &&
         binding.operations.read_memory != nullptr &&
         binding.operations.read_memory(binding.operation_context,
                                        reinterpret_cast<const void *>(address),
                                        destination, size);
}

} // namespace

bool EvaluateCouncilAssignCouncillorProductionGatesV1(
    void *opaque, const game::CouncilAssignCouncillorFrameV1 &frame,
    std::int32_t candidate_character_id,
    game::CouncilAssignCouncillorFinalLegalityV1 &output) noexcept {
  output = {};
  auto *context = static_cast<CouncilApplicationMainContextV1 *>(opaque);
  if (context == nullptr || context->shared_state == nullptr ||
      context->active_stamp == nullptr ||
      !context->configuration.exact_build_admitted ||
      !context->configuration.private_candidate_admitted ||
      !context->configuration.native_command_abi_certified ||
      context->configuration.offline_fixture ||
      context->configuration.admitted_executable_sha256 !=
          ck3_11906::kCouncilAssignCouncillorExecutableSha256V1 ||
      context->configuration.module_base == 0 ||
      !context->active_stamp->paused ||
      context->active_stamp->thread_id == 0 ||
      GetCurrentThreadId() != context->active_stamp->thread_id ||
      !frame.available || !frame.paused || !frame.map_ready ||
      !frame.owner_identity_round_trip ||
      !frame.active_task_identity_round_trip ||
      frame.position_key != ck3_11906::kCouncilAssignCouncillorPositionKeyV1 ||
      frame.owner_character_id <= 0 || frame.active_task_id <= 0 ||
      candidate_character_id <= 0 ||
      (frame.has_incumbent &&
       (!frame.incumbent_identity_round_trip ||
        frame.incumbent_character_id <= 0))) {
    return false;
  }

  const auto &binding = context->shared_state->binding;
  if (!binding.attached || !binding.frame_bound || binding.transaction_active ||
      binding.module_base != context->configuration.module_base ||
      binding.operations.resolve_character == nullptr ||
      binding.operations.read_memory == nullptr ||
      binding.bound_frame.played_character_id != frame.owner_character_id ||
      binding.bound_frame.active_task_id != frame.active_task_id) {
    return false;
  }

  std::uintptr_t played_id_address = 0;
  if (!Address(binding.module_base, kPlayedCharacterIdRva,
               played_id_address)) {
    return false;
  }
  std::int32_t current_player_id = -1;
  if (!ReadBoundValue(binding, played_id_address, &current_player_id,
                      sizeof(current_player_id)) ||
      current_player_id != frame.owner_character_id) {
    return false;
  }

  std::uintptr_t candidate = 0;
  if (!binding.operations.resolve_character(
          binding.operation_context, binding.module_base,
          candidate_character_id, candidate) ||
      candidate == 0 ||
      candidate > (std::numeric_limits<std::uintptr_t>::max)() -
                      kCharacterIdOffset) {
    return false;
  }
  std::int32_t observed_candidate_id = -1;
  if (!ReadBoundValue(binding, candidate + kCharacterIdOffset,
                      &observed_candidate_id,
                      sizeof(observed_candidate_id)) ||
      observed_candidate_id != candidate_character_id) {
    return false;
  }

  std::uintptr_t councillor_address = 0;
  std::uintptr_t guest_address = 0;
  std::uintptr_t pending_setup_address = 0;
  std::uintptr_t pending_address = 0;
  if (!Address(binding.module_base, kIsCouncillorRva, councillor_address) ||
      !Address(binding.module_base, kIsGuestRva, guest_address) ||
      !Address(binding.module_base, kPendingManagerSetupRva,
               pending_setup_address) ||
      !Address(binding.module_base, kHasPendingInteractionRva,
               pending_address)) {
    return false;
  }
  alignas(16) std::array<std::byte, kPendingSetupStorageSize>
      pending_setup_storage{};
  bool already_councillor = false;
  bool guest = false;
  bool pending = false;
  if (!NativePredicates(councillor_address, guest_address,
                        pending_setup_address, pending_address,
                        reinterpret_cast<void *>(candidate),
                        candidate_character_id, pending_setup_storage.data(),
                        already_councillor, guest, pending)) {
    return false;
  }

  output.candidate_already_councillor = already_councillor;
  output.candidate_is_guest = guest;
  output.pending_character_interaction = pending;
  if (frame.has_incumbent) {
    ck3_11906::CouncilAssignCouncillorNativeEnvironmentV1 fire_environment{};
    fire_environment.exact_build_admitted = true;
    fire_environment.admitted_executable_sha256 =
        ck3_11906::kCouncilAssignCouncillorExecutableSha256V1;
    fire_environment.module_base = binding.module_base;
    fire_environment.native_command_abi_certified = true;
    fire_environment.private_candidate_admitted = true;
    fire_environment.current_thread_id = GetCurrentThreadId();
    fire_environment.application_main_thread_id =
        context->active_stamp->thread_id;
    bool can_fire = false;
    if (!ck3_11906::EvaluateCouncilReplacementFireabilityV1(
            fire_environment, frame.incumbent_character_id,
            frame.active_task_id, can_fire)) {
      return false;
    }
    output.incumbent_fireability_evaluated = true;
    output.incumbent_can_be_fired = can_fire;
  }
  output.available = true;
  return true;
}

} // namespace xar::bridge
