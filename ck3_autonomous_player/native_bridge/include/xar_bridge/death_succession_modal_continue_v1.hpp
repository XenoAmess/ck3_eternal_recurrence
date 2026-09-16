#pragma once

#include "xar_bridge/current_timeline_blocker_context_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class DeathSuccessionModalContinueStatusV1 : std::uint32_t {
  unavailable = 0,
  submitted = 1,
};

struct DeathSuccessionModalContinueReceiptV1 {
  DeathSuccessionModalContinueStatusV1 status =
      DeathSuccessionModalContinueStatusV1::unavailable;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  bool identity_verified = false;
  bool can_continue_verified = false;
  bool paused_by_succession_verified = false;
  bool has_open_succession_verified = false;
  bool controller_vtable_verified = false;
  bool controller_open_verified = false;
  std::uint32_t close_invocations = 0;
  std::string unavailable_reason;

  friend bool operator==(const DeathSuccessionModalContinueReceiptV1 &,
                         const DeathSuccessionModalContinueReceiptV1 &) =
      default;
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr bool kDeathSuccessionModalContinueV1CapabilityAdvertised =
    false;
inline constexpr std::string_view kDeathSuccessionModalContinueV1Step =
    "continue-death-succession-modal-v1";
inline constexpr std::string_view kDeathSuccessionModalContinueV1Capability =
    "game.command.continue-death-succession-modal-v1";

inline bool IsDeathSuccessionModalPrivateStepV1(
    std::string_view step) noexcept {
  return step == kCurrentTimelineBlockerContextV1Step ||
         step == kDeathSuccessionModalContinueV1Step;
}

struct DeathSuccessionModalContinueRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
  std::int32_t expected_date_raw = 0;
  std::int32_t expected_played_character_id = -1;
};

using ResolveDeathSuccessionControllerV1 = bool (*)(void *, void *&) noexcept;
using ReadDeathSuccessionControllerOpenV1 = bool (*)(void *, void *,
                                                      bool &) noexcept;
using CloseDeathSuccessionControllerV1 = bool (*)(void *, void *) noexcept;

struct DeathSuccessionModalContinueSourceV1 {
  void *context = nullptr;
  ResolveDeathSuccessionControllerV1 resolve_controller = nullptr;
  ReadDeathSuccessionControllerOpenV1 read_controller_open = nullptr;
  CloseDeathSuccessionControllerV1 close_controller = nullptr;
};

game::DeathSuccessionModalContinueStatusV1
ExecuteDeathSuccessionModalContinueV1(
    const DeathSuccessionModalContinueRequestV1 &request,
    const game::CurrentTimelineBlockerContextV1 &timeline,
    const DeathSuccessionModalContinueSourceV1 &source,
    game::DeathSuccessionModalContinueReceiptV1 &receipt) noexcept;

game::DeathSuccessionModalContinueStatusV1
ExecuteDeathSuccessionModalContinueNativeV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const DeathSuccessionModalContinueRequestV1 &request,
    const game::CurrentTimelineBlockerContextV1 &timeline,
    game::DeathSuccessionModalContinueReceiptV1 &receipt) noexcept;

bool ParseDeathSuccessionModalContinueV1Step(std::string_view step) noexcept;
bool ParseDeathSuccessionModalContinueRequestV1(
    std::string_view json,
    DeathSuccessionModalContinueRequestV1 &output) noexcept;

} // namespace xar::ck3_11906
