#include "xar_bridge/activity_feast_guest_opinion_v1.hpp"

namespace xar::bridge {

ActivityFeastGuestOpinionResultV1 ReadActivityFeastGuestOpinionV1(
    const ActivityFeastGuestOpinionEnvironmentV1 &environment,
    const ActivityFeastGuestOpinionFrameV1 &expected,
    std::int32_t guest_character_id,
    std::uint32_t activity_id) noexcept {
  ActivityFeastGuestOpinionResultV1 result{};
  result.frame = expected;
  result.guest_character_id = guest_character_id;
  result.activity_target_requested = activity_id != 0;
  if (result.activity_target_requested) {
    result.activity_target.activity_id = activity_id;
    result.activity_target.guest_character_id = guest_character_id;
    result.activity_target.status = ActivityHostedTargetStatusV1::frame_rejected;
  }
  if (expected.revision == 0 || expected.actor_character_id <= 0 ||
      guest_character_id <= 0 ||
      guest_character_id == expected.actor_character_id || !expected.paused ||
      !expected.map_ready || !expected.actor_alive ||
      environment.read_frame == nullptr ||
      environment.read_opinion == nullptr || activity_id == UINT32_MAX) {
    return result;
  }
  ActivityFeastGuestOpinionFrameV1 before{};
  ActivityFeastGuestOpinionFrameV1 after{};
  if (!environment.read_frame(environment.context, before) ||
      before != expected) {
    result.status = ActivityFeastGuestOpinionStatusV1::frame_changed;
    return result;
  }
  result.reward_modifiers_requested = environment.read_reward_modifiers != nullptr;
  if (result.activity_target_requested && environment.read_activity_target != nullptr) {
    environment.read_activity_target(environment.context, activity_id,
                                     guest_character_id, result.activity_target);
  }
  std::int32_t opinion = 0;
  if (!environment.read_opinion(environment.context,
                                static_cast<std::uint32_t>(guest_character_id),
                                static_cast<std::uint32_t>(
                                    expected.actor_character_id),
                                opinion)) {
    result.status = ActivityFeastGuestOpinionStatusV1::opinion_unavailable;
    return result;
  }
  if (result.reward_modifiers_requested) {
    ActivityFeastRewardOpinionModifiersV1 first{};
    ActivityFeastRewardOpinionModifiersV1 second{};
    environment.read_reward_modifiers(environment.context,
        static_cast<std::uint32_t>(guest_character_id),
        static_cast<std::uint32_t>(expected.actor_character_id), first);
    environment.read_reward_modifiers(environment.context,
        static_cast<std::uint32_t>(guest_character_id),
        static_cast<std::uint32_t>(expected.actor_character_id), second);
    for (std::size_t index = 0; index < first.size(); ++index) {
      // A failed or changing modifier does not erase independently read total
      // opinion. It is published as read_failed rather than legal absence.
      if (first[index].observed && first[index] == second[index] &&
          first[index].present == first[index].value.has_value())
        result.reward_modifiers[index] = first[index];
    }
  }
  if (!environment.read_frame(environment.context, after) ||
      after != expected) {
    result.reward_modifiers = {};
    if (result.activity_target_requested) {
      result.activity_target = {};
      result.activity_target.activity_id = activity_id;
      result.activity_target.guest_character_id = guest_character_id;
      result.activity_target.status = ActivityHostedTargetStatusV1::snapshot_changed;
    }
    result.status = ActivityFeastGuestOpinionStatusV1::frame_changed;
    return result;
  }
  result.status = ActivityFeastGuestOpinionStatusV1::observed;
  result.guest_opinion_of_actor = opinion;
  return result;
}

std::string_view ActivityFeastGuestOpinionStatusKeyV1(
    ActivityFeastGuestOpinionStatusV1 status) noexcept {
  switch (status) {
  case ActivityFeastGuestOpinionStatusV1::observed: return "observed";
  case ActivityFeastGuestOpinionStatusV1::invalid_request:
    return "invalid_request";
  case ActivityFeastGuestOpinionStatusV1::frame_changed:
    return "frame_changed";
  case ActivityFeastGuestOpinionStatusV1::opinion_unavailable:
    return "opinion_unavailable";
  }
  return "invalid_request";
}

} // namespace xar::bridge
