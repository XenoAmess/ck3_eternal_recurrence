#pragma once
#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>
namespace xar::ck3_12003 {
struct AubPolicyEntryV1 {
  std::string value_key;
  bool selected = false;
  bool operator==(const AubPolicyEntryV1 &) const = default;
};
struct AubPolicyOptionsObservationV1 {
  bool ready = false;
  std::string unavailable_reason;
  std::int32_t played_character_id = -1;
  std::string decision_key;
  std::string selected_key;
  std::int32_t selected_index = -1;
  std::vector<AubPolicyEntryV1> entries;
};
// Native-private admission, never deserialized from a public request. The owner
// mailbox caller must independently acquire the actual named visible complete
// decisiondetail_view tree and paused/alive/no-event snapshot, and implement the
// callback as a fresh snapshot + same PID/generation/revision/Jomini/GUI owner
// check. The callback MUST NOT be a cached bool. Its absence fails closed.
struct AubPolicyNativeAdmissionV1 {
  std::string_view executable_sha256;
  const void *jomini_state = nullptr;
  const void *decision_detail_root = nullptr;
  const void *gui_context = nullptr;
  bool native_root_effectively_visible = false;
  bool native_tree_complete = false;
  std::int32_t played_character_id = -1;
  void *frame_context = nullptr;
  bool (*revalidate_paused_episode_frame)(void *) noexcept = nullptr;
};
struct AubPolicySelectionResultV1 {
  AubPolicyOptionsObservationV1 before, after;
  bool already_selected = false;
  bool dispatch_invoked = false;
  bool native_call_completed = false;
  bool postcondition_verified = false;
  std::string unavailable_reason;
};
// Test-only override, accepted only with offline_fixture_function_overrides.
// Production always calls the pinned source OnSelect handler, never this hook.
struct AubPolicyOfflineActionV1 {
  void *context = nullptr;
  bool (*select)(void *, void *, const void *) noexcept = nullptr;
};
bool ProbeAubPolicyOptionsV1(
    const ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 &,
    const ck3_11906::ZhongguoScoreboardAccessV1 &,
    const AubPolicyNativeAdmissionV1 &, AubPolicyOptionsObservationV1 &) noexcept;
// One invocation at most. The caller must durably consume the request claim
// before entering this function; a fault or missing postcondition is unknown,
// never retryable. Selects the actual member Entry.Self; does not Confirm.
bool SelectAubPolicyOptionV1(
    const ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 &,
    const ck3_11906::ZhongguoScoreboardAccessV1 &,
    const AubPolicyNativeAdmissionV1 &, std::string_view expected_selected_key,
    std::string_view desired_key, AubPolicySelectionResultV1 &,
    const AubPolicyOfflineActionV1 *offline = nullptr) noexcept;
} // namespace xar::ck3_12003
