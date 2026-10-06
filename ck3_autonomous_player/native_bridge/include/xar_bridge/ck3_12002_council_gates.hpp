#pragma once

#include "xar_bridge/council_assign_councillor_action_v1.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kCouncilGatesExecutableSha25612002 =
    "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
inline constexpr std::uintptr_t kCouncilGatesPlayedCharacterIdRva12002 = 0x54DBC00;
inline constexpr std::uintptr_t kCouncilGatesIsCouncillorRva12002 = 0x2917560;
inline constexpr std::uintptr_t kCouncilGatesIsGuestRva12002 = 0x1A8F780;
inline constexpr std::uintptr_t kCouncilGatesPendingSetupRva12002 = 0x115CA80;
inline constexpr std::uintptr_t kCouncilGatesHasPendingRva12002 = 0x2A307B0;
inline constexpr std::uintptr_t kCouncilGatesCanConfirmRva12002 = 0x11604A0;
inline constexpr std::size_t kCouncilGatesPendingWindowSize12002 = 0x5E8;
inline constexpr std::size_t kCouncilGatesPendingManagerOffset12002 = 0x5D8;
inline constexpr std::size_t kCouncilGatesPendingCleanupOffset12002 = 0x5E0;
inline constexpr std::size_t kCouncilGatesConfirmationSize12002 = 0x140;
inline constexpr std::size_t kCouncilGatesConfirmationIncumbentOffset12002 = 0x130;
inline constexpr std::size_t kCouncilGatesConfirmationCandidateOffset12002 = 0x134;

using NativeCouncilCharacterPredicate12002 = bool (*)(void *);
using NativeCouncilPendingSetup12002 = void (*)(void *);
using NativeCouncilPendingPredicate12002 = bool (*)(void *, std::int32_t);
using NativeCouncilCanConfirm12002 = bool (*)(void *);
using CouncilGatesReadMemory12002 = bool (*)(
    void *, const void *, void *, std::size_t) noexcept;

struct CouncilGatesEnvironment12002 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::uintptr_t module_base = 0;
  bool offline_fixture = false;
  std::uint32_t current_thread_id = 0;
  std::uint32_t application_main_thread_id = 0;
  void *read_context = nullptr;
  CouncilGatesReadMemory12002 read_memory = nullptr;
  const std::int32_t *played_character_id_slot = nullptr;
  NativeCouncilCharacterPredicate12002 is_councillor = nullptr;
  NativeCouncilCharacterPredicate12002 is_guest = nullptr;
  NativeCouncilPendingSetup12002 pending_setup = nullptr;
  NativeCouncilPendingPredicate12002 has_pending = nullptr;
  NativeCouncilCanConfirm12002 can_confirm = nullptr;
};

// Only exact-build pointers are installed. The application-main capture sets
// thread IDs and its existing memory-reader context immediately before use.
CouncilGatesEnvironment12002 BindCouncilGates12002(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// The candidate provider owns the five identity/match fields in output.
// This function preserves them, reads the native gates from the same resolved
// candidate, and marks available only when every required gate was obtained.
// Fixture function pointers are accepted only with offline_fixture/base==0.
bool EvaluateCouncilGates12002(
    const CouncilGatesEnvironment12002 &environment,
    const game::CouncilAssignCouncillorFrameV1 &frame,
    std::int32_t candidate_character_id, void *resolved_candidate,
    game::CouncilAssignCouncillorFinalLegalityV1 &output) noexcept;

// Read-only candidate observation profile. This includes chaplain composition
// without expanding the original three-seat assignment evaluator above.
bool EvaluateCouncilCandidateObservationGates12002(
    const CouncilGatesEnvironment12002 &environment,
    const game::CouncilAssignCouncillorFrameV1 &frame,
    std::int32_t candidate_character_id, void *resolved_candidate,
    game::CouncilAssignCouncillorFinalLegalityV1 &output) noexcept;

} // namespace xar::ck3_12002
