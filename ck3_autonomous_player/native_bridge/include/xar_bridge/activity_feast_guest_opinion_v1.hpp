#pragma once

#include "xar_bridge/activity_hosted_identity_v1.hpp"

#include <array>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::bridge {

// A generic host/guest opinion read for a paused planner frame. The caller
// supplies full generation-bearing CharacterIDs; this does not infer an
// invite rule, an accepted invitation, or an activity reward.
struct ActivityFeastGuestOpinionFrameV1 {
  std::uint64_t revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t actor_character_id = -1;
  bool paused = false;
  bool map_ready = false;
  bool actor_alive = false;

  friend bool operator==(const ActivityFeastGuestOpinionFrameV1 &,
                         const ActivityFeastGuestOpinionFrameV1 &) = default;
};

enum class ActivityFeastGuestOpinionStatusV1 {
  observed,
  invalid_request,
  frame_changed,
  opinion_unavailable,
};

// Fixed stock on-complete keys. Presence alone does not prove attendance or
// causation; these are independent recipient-toward-host observations.
inline constexpr std::array<std::string_view, 3> kActivityFeastRewardOpinionKeysV1{
    "hosted_feast_opinion", "hosted_mediocre_feast_opinion", "impressed_opinion"};

struct ActivityFeastRewardOpinionModifierV1 {
  bool observed = false;
  bool present = false;
  std::optional<std::int32_t> value;
  friend bool operator==(const ActivityFeastRewardOpinionModifierV1 &,
                         const ActivityFeastRewardOpinionModifierV1 &) = default;
};
using ActivityFeastRewardOpinionModifiersV1 =
    std::array<ActivityFeastRewardOpinionModifierV1, 3>;

struct ActivityFeastGuestOpinionEnvironmentV1 {
  void *context = nullptr;
  bool (*read_frame)(void *, ActivityFeastGuestOpinionFrameV1 &) noexcept =
      nullptr;
  bool (*read_opinion)(void *, std::uint32_t recipient_character_id,
                       std::uint32_t actor_character_id,
                       std::int32_t &opinion) noexcept = nullptr;
  void (*read_reward_modifiers)(void *, std::uint32_t recipient_character_id,
                               std::uint32_t actor_character_id,
                               ActivityFeastRewardOpinionModifiersV1 &) noexcept = nullptr;
  void (*read_activity_target)(void *, std::uint32_t activity_id,
                               std::int32_t guest_character_id,
                               ActivityHostedTargetResultV1 &) noexcept = nullptr;
};

struct ActivityFeastGuestOpinionResultV1 {
  ActivityFeastGuestOpinionStatusV1 status =
      ActivityFeastGuestOpinionStatusV1::invalid_request;
  ActivityFeastGuestOpinionFrameV1 frame{};
  std::int32_t guest_character_id = -1;
  std::int32_t guest_opinion_of_actor = 0;
  bool reward_modifiers_requested = false;
  ActivityFeastRewardOpinionModifiersV1 reward_modifiers{};
  bool activity_target_requested = false;
  ActivityHostedTargetResultV1 activity_target{};
};

ActivityFeastGuestOpinionResultV1 ReadActivityFeastGuestOpinionV1(
    const ActivityFeastGuestOpinionEnvironmentV1 &environment,
    const ActivityFeastGuestOpinionFrameV1 &expected,
    std::int32_t guest_character_id,
    std::uint32_t activity_id = 0) noexcept;

std::string_view ActivityFeastGuestOpinionStatusKeyV1(
    ActivityFeastGuestOpinionStatusV1 status) noexcept;

} // namespace xar::bridge
