#include "xar_bridge/ck3_12004_council_gates.hpp"
#include "xar_bridge/ck3_12004_council_candidates.hpp"

#include <array>
#include <cstring>
#include <limits>

#if defined(_WIN32)
#include <windows.h>
#endif

namespace xar::ck3_12004 {
namespace {

bool ReadBytes(const CouncilGatesEnvironment12004 &environment,
               const void *address, void *destination,
               std::size_t size) noexcept {
  if (address == nullptr || destination == nullptr || size == 0) return false;
  if (environment.read_memory != nullptr)
    return environment.read_memory(environment.read_context, address,
                                   destination, size);
#if defined(_MSC_VER)
  __try {
    std::memcpy(destination, address, size);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  std::memcpy(destination, address, size);
#endif
  return true;
}

bool ReadId(const CouncilGatesEnvironment12004 &environment, const void *object,
            std::size_t offset, std::int32_t &output) noexcept {
  const auto address = reinterpret_cast<std::uintptr_t>(object);
  return address != 0 &&
      offset <= (std::numeric_limits<std::uintptr_t>::max)() - address &&
      ReadBytes(environment, reinterpret_cast<const void *>(address + offset),
                &output, sizeof(output));
}

bool ExactEnvironment(const CouncilGatesEnvironment12004 &e) noexcept {
  if (!e.exact_build_admitted ||
      e.admitted_executable_sha256 != kCouncilGatesExecutableSha25612004 ||
      e.current_thread_id == 0 ||
      e.current_thread_id != e.application_main_thread_id ||
      e.played_character_id_slot == nullptr || e.is_councillor == nullptr ||
      e.is_guest == nullptr || e.pending_setup == nullptr ||
      e.has_pending == nullptr || e.can_confirm == nullptr) return false;
  if (e.offline_fixture) return e.module_base == 0;
  if (e.module_base == 0 ||
      e.module_base > (std::numeric_limits<std::uintptr_t>::max)() -
                          kCouncilGatesPlayedCharacterIdRva12004) return false;
#if defined(_WIN32)
  if (GetCurrentThreadId() != e.current_thread_id) return false;
#else
  return false;
#endif
  const auto base = e.module_base;
  return reinterpret_cast<std::uintptr_t>(e.played_character_id_slot) ==
             base + kCouncilGatesPlayedCharacterIdRva12004 &&
         reinterpret_cast<std::uintptr_t>(e.is_councillor) ==
             base + kCouncilGatesIsCouncillorRva12004 &&
         reinterpret_cast<std::uintptr_t>(e.is_guest) ==
             base + kCouncilGatesIsGuestRva12004 &&
         reinterpret_cast<std::uintptr_t>(e.pending_setup) ==
             base + kCouncilGatesPendingSetupRva12004 &&
         reinterpret_cast<std::uintptr_t>(e.has_pending) ==
             base + kCouncilGatesHasPendingRva12004 &&
         reinterpret_cast<std::uintptr_t>(e.can_confirm) ==
             base + kCouncilGatesCanConfirmRva12004;
}

bool EvaluateNative(const CouncilGatesEnvironment12004 &e, void *candidate,
                    std::int32_t candidate_id, void *pending_window,
                    void *confirmation, bool has_incumbent,
                    std::int32_t owner_id, bool &councillor, bool &guest,
                    bool &pending, bool &can_confirm) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    councillor = e.is_councillor(candidate);
    guest = e.is_guest(candidate);
    e.pending_setup(pending_window);
    void *manager = nullptr;
    std::memcpy(&manager, static_cast<std::byte *>(pending_window) +
                              kCouncilGatesPendingManagerOffset12004,
                sizeof(manager));
    std::int32_t manager_owner = -1;
    if (manager == nullptr || !ReadId(e, manager, 0x8, manager_owner) ||
        manager_owner != owner_id) return false;
    pending = e.has_pending(manager, candidate_id);
    if (has_incumbent) can_confirm = e.can_confirm(confirmation);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
  return true;
}

} // namespace

CouncilGatesEnvironment12004 BindCouncilGates12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept {
  CouncilGatesEnvironment12004 e{};
  if (executable_sha256 != kCouncilGatesExecutableSha25612004 ||
      module_base == 0 ||
      module_base > (std::numeric_limits<std::uintptr_t>::max)() -
                        kCouncilGatesPlayedCharacterIdRva12004) return e;
  e.exact_build_admitted = true;
  e.admitted_executable_sha256 = kCouncilGatesExecutableSha25612004;
  e.module_base = module_base;
  e.played_character_id_slot = reinterpret_cast<const std::int32_t *>(
      module_base + kCouncilGatesPlayedCharacterIdRva12004);
  e.is_councillor = reinterpret_cast<NativeCouncilCharacterPredicate12004>(
      module_base + kCouncilGatesIsCouncillorRva12004);
  e.is_guest = reinterpret_cast<NativeCouncilCharacterPredicate12004>(
      module_base + kCouncilGatesIsGuestRva12004);
  e.pending_setup = reinterpret_cast<NativeCouncilPendingSetup12004>(
      module_base + kCouncilGatesPendingSetupRva12004);
  e.has_pending = reinterpret_cast<NativeCouncilPendingPredicate12004>(
      module_base + kCouncilGatesHasPendingRva12004);
  e.can_confirm = reinterpret_cast<NativeCouncilCanConfirm12004>(
      module_base + kCouncilGatesCanConfirmRva12004);
  return e;
}

static bool EvaluateCouncilGatesWithProfile12004(
    const CouncilGatesEnvironment12004 &e,
    const game::CouncilAssignCouncillorFrameV1 &frame,
    std::int32_t candidate_character_id, void *resolved_candidate,
    game::CouncilAssignCouncillorFinalLegalityV1 &output,
    bool observation_only) noexcept {
  output.available = false;
  output.candidate_already_councillor = false;
  output.candidate_is_guest = false;
  output.pending_character_interaction = false;
  output.incumbent_fireability_evaluated = false;
  output.incumbent_can_be_fired = false;
  if (!ExactEnvironment(e) || !frame.available || !frame.paused ||
      !frame.map_ready || !frame.owner_identity_round_trip ||
      !frame.active_task_identity_round_trip || frame.owner_character_id <= 0 ||
      frame.active_task_id <= 0 ||
      (observation_only
          ? CouncilCandidatesCompositionProfile12004(frame.position_key).position_key.empty()
          : (CouncilCandidatesProfile12004(frame.position_key).position_key.empty() &&
             frame.position_key != kCouncilCandidatesChaplainPosition12004)) ||
      candidate_character_id <= 0 || resolved_candidate == nullptr ||
      (frame.has_incumbent && (!frame.incumbent_identity_round_trip ||
                              frame.incumbent_character_id <= 0)) ||
      output.owner_character_id != frame.owner_character_id ||
      output.active_task_id != frame.active_task_id ||
      output.position_key != frame.position_key ||
      output.candidate_character_id != candidate_character_id ||
      output.candidate_match_count != 1 ||
      !output.candidate_identity_round_trip) return false;
  std::int32_t player = -1, observed_candidate = -1;
  if (!ReadBytes(e, e.played_character_id_slot, &player, sizeof(player)) ||
      player != frame.owner_character_id ||
      !ReadId(e, resolved_candidate, 0x18, observed_candidate) ||
      observed_candidate != candidate_character_id) return false;

  alignas(16) std::array<std::byte, kCouncilGatesPendingWindowSize12004>
      pending_window{};
  alignas(16) std::array<std::byte, kCouncilGatesConfirmationSize12004>
      confirmation{};
  if (frame.has_incumbent) {
    std::memcpy(confirmation.data() + kCouncilGatesConfirmationIncumbentOffset12004,
                &frame.incumbent_character_id, sizeof(frame.incumbent_character_id));
    std::memcpy(confirmation.data() + kCouncilGatesConfirmationCandidateOffset12004,
                &candidate_character_id, sizeof(candidate_character_id));
  }
  bool councillor = false, guest = false, pending = false, can_confirm = false;
  if (!EvaluateNative(e, resolved_candidate, candidate_character_id,
                      pending_window.data(), confirmation.data(), frame.has_incumbent,
                      frame.owner_character_id, councillor, guest, pending,
                      can_confirm)) return false;
  // Setup/CanConfirm use the played global; bind both ends of that observation.
  if (!ReadBytes(e, e.played_character_id_slot, &player, sizeof(player)) ||
      player != frame.owner_character_id) return false;
  output.candidate_already_councillor = councillor;
  output.candidate_is_guest = guest;
  output.pending_character_interaction = pending;
  output.incumbent_fireability_evaluated = frame.has_incumbent;
  output.incumbent_can_be_fired = can_confirm;
  output.available = true;
  return true;
}

bool EvaluateCouncilGates12004(
    const CouncilGatesEnvironment12004 &e,
    const game::CouncilAssignCouncillorFrameV1 &frame,
    std::int32_t candidate_character_id, void *resolved_candidate,
    game::CouncilAssignCouncillorFinalLegalityV1 &output) noexcept {
  return EvaluateCouncilGatesWithProfile12004(e, frame, candidate_character_id,
      resolved_candidate, output, false);
}

bool EvaluateCouncilCandidateObservationGates12004(
    const CouncilGatesEnvironment12004 &e,
    const game::CouncilAssignCouncillorFrameV1 &frame,
    std::int32_t candidate_character_id, void *resolved_candidate,
    game::CouncilAssignCouncillorFinalLegalityV1 &output) noexcept {
  return EvaluateCouncilGatesWithProfile12004(e, frame, candidate_character_id,
      resolved_candidate, output, true);
}

} // namespace xar::ck3_12004
