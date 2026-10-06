#pragma once

#include "xar_bridge/council_assign_councillor_action_v1.hpp"
#include "xar_bridge/ck3_12004.hpp"

namespace xar::ck3_12004 {

// New-build body/layout proofs: Council gates/assign finite captures 01-04.
// PendingSetup is a no-pdata leaf proved in full after adjacent-gap candidate
// generation; assigning the unchanged numeric address alone was insufficient.
inline constexpr std::string_view kCouncilGatesExecutableSha25612004 =
    kExecutableSha256;
inline constexpr std::uintptr_t kCouncilGatesPlayedCharacterIdRva12004 = 0x54DBC00;
inline constexpr std::uintptr_t kCouncilGatesIsCouncillorRva12004 = 0x2917540;
inline constexpr std::uintptr_t kCouncilGatesIsGuestRva12004 = 0x1A8F760;
inline constexpr std::uintptr_t kCouncilGatesPendingSetupRva12004 = 0x115CA80;
inline constexpr std::uintptr_t kCouncilGatesHasPendingRva12004 = 0x2A30790;
inline constexpr std::uintptr_t kCouncilGatesCanConfirmRva12004 = 0x11604A0;
inline constexpr std::size_t kCouncilGatesPendingWindowSize12004 = 0x5E8;
inline constexpr std::size_t kCouncilGatesPendingManagerOffset12004 = 0x5D8;
inline constexpr std::size_t kCouncilGatesPendingCleanupOffset12004 = 0x5E0;
inline constexpr std::size_t kCouncilGatesConfirmationSize12004 = 0x140;
inline constexpr std::size_t kCouncilGatesConfirmationIncumbentOffset12004 = 0x130;
inline constexpr std::size_t kCouncilGatesConfirmationCandidateOffset12004 = 0x134;

using NativeCouncilCharacterPredicate12004 = bool (*)(void *);
using NativeCouncilPendingSetup12004 = void (*)(void *);
using NativeCouncilPendingPredicate12004 = bool (*)(void *, std::int32_t);
using NativeCouncilCanConfirm12004 = bool (*)(void *);
using CouncilGatesReadMemory12004 = bool (*)(
    void *, const void *, void *, std::size_t) noexcept;

struct CouncilGatesEnvironment12004 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::uintptr_t module_base = 0;
  bool offline_fixture = false;
  std::uint32_t current_thread_id = 0;
  std::uint32_t application_main_thread_id = 0;
  void *read_context = nullptr;
  CouncilGatesReadMemory12004 read_memory = nullptr;
  const std::int32_t *played_character_id_slot = nullptr;
  NativeCouncilCharacterPredicate12004 is_councillor = nullptr;
  NativeCouncilCharacterPredicate12004 is_guest = nullptr;
  NativeCouncilPendingSetup12004 pending_setup = nullptr;
  NativeCouncilPendingPredicate12004 has_pending = nullptr;
  NativeCouncilCanConfirm12004 can_confirm = nullptr;
};

// Only exact-build pointers are installed. The application-main capture sets
// thread IDs and its existing memory-reader context immediately before use.
CouncilGatesEnvironment12004 BindCouncilGates12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// The candidate provider owns the five identity/match fields in output.
// This function preserves them, reads the native gates from the same resolved
// candidate, and marks available only when every required gate was obtained.
// Fixture function pointers are accepted only with offline_fixture/base==0.
bool EvaluateCouncilGates12004(
    const CouncilGatesEnvironment12004 &environment,
    const game::CouncilAssignCouncillorFrameV1 &frame,
    std::int32_t candidate_character_id, void *resolved_candidate,
    game::CouncilAssignCouncillorFinalLegalityV1 &output) noexcept;

// Read-only candidate observation profile. This includes chaplain composition
// without expanding the original three-seat assignment evaluator above.
bool EvaluateCouncilCandidateObservationGates12004(
    const CouncilGatesEnvironment12004 &environment,
    const game::CouncilAssignCouncillorFrameV1 &frame,
    std::int32_t candidate_character_id, void *resolved_candidate,
    game::CouncilAssignCouncillorFinalLegalityV1 &output) noexcept;

} // namespace xar::ck3_12004
