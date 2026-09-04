#pragma once

#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class ZhongguoPromotionSourceProgressStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

struct ZhongguoPromotionSourceProgressReadinessV1 {
  bool player_binding_ready = false;
  bool gui_root_ready = false;
  bool exact_widget_set_ready = false;
  bool same_frame_ready = false;
  bool query_ready = false;
  bool production_live_ready = false;
};

struct ZhongguoPromotionSourceProgressV1 {
  ZhongguoPromotionSourceProgressStatusV1 status =
      ZhongguoPromotionSourceProgressStatusV1::unavailable;
  std::string request_nonce;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t player_character_id = -1;
  std::array<ZhongguoScoreboardWidgetStateV1, 5> widgets;
  ZhongguoPromotionSourceProgressReadinessV1 readiness;
  std::string unavailable_reason;
};

enum class ReadZhongguoPromotionSourceProgressResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

struct ZhongguoReviewNowActionRequestV1 {
  std::string request_nonce;
  std::uint64_t expected_revision = 0;
  std::uint64_t expected_native_revision = 0;
  std::uint64_t expected_connection_generation = 0;
  std::int32_t expected_player_character_id = -1;
};

struct ZhongguoReviewNowActionAckV1 {
  bool accepted = false;
  std::string request_nonce;
  std::uint64_t source_revision = 0;
  std::uint64_t source_native_revision = 0;
  std::uint64_t source_connection_generation = 0;
  std::int32_t date_raw = 0;
  std::int32_t player_character_id = -1;
  ZhongguoScoreboardActionTargetV1 target;
  bool requires_independent_progress_query = true;
  std::string expected_postcondition;
  bool native_handled = false;
  bool postcondition_verified = false;
  std::string rejection_reason;
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kZhongguoPromotionSourceProgressV1Capability =
    "game.command.query-zhongguo-promotion-source-progress-v1";
inline constexpr std::string_view
    kZhongguoPromotionSourceProgressV1TransportCapability =
        "game.contract.zhongguo-promotion-source-progress-v1-fail-closed";
inline constexpr std::string_view kZhongguoPromotionSourceProgressV1Step =
    "query-zhongguo-promotion-source-progress-v1";
inline constexpr std::string_view kZhongguoPromotionSourceProgressV1BackendId =
    "ck3-1.19.0.6-native-zhongguo-promotion-source-progress-v1";
inline constexpr std::string_view kZhongguoReviewNowActionV1Capability =
    "game.command.activate-zhongguo-review-now-v1";
inline constexpr std::string_view kZhongguoReviewNowActionV1Step =
    "activate-zhongguo-review-now-v1";
inline constexpr std::string_view kZhongguoReviewNowActionV1TransportCapability =
    "game.contract.zhongguo-review-now-action-v1-fail-closed";
inline constexpr std::string_view kZhongguoReviewNowActionV1BackendId =
    "ck3-1.19.0.6-native-zhongguo-review-now-action-v1";
inline constexpr std::string_view kZhongguoPromotionSourceProgressV1AllowlistId =
    "zg361-promotion-source-fixed-widget-progress-v1";
inline constexpr bool
    kZhongguoPromotionSourceProgressV1ProductionCapabilityAdvertised = false;
inline constexpr bool kZhongguoReviewNowActionV1ProductionCapabilityAdvertised =
    false;

inline constexpr std::array<std::string_view, 5>
    kZhongguoPromotionSourceProgressV1WidgetNames{
        "zg361_promotion_source_bridge_window",
        "zg361_promotion_source_review_now_action",
        "zg361_promotion_source_b1_active",
        "zg361_promotion_source_central_active",
        "zg361_promotion_source_pp_active",
    };
inline constexpr auto kZhongguoPromotionSourceProgressV1WidgetIdentities =
    kZhongguoPromotionSourceProgressV1WidgetNames;

using ZhongguoPromotionSourceProgressNativeEnvironmentV1 =
    ZhongguoScoreboardNativeEnvironmentV1;
using ZhongguoPromotionSourceProgressAccessV1 = ZhongguoScoreboardAccessV1;

struct ZhongguoPromotionSourceProgressRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
  std::string request_nonce;
};

using DispatchZhongguoReviewNowActionV1 = bool (*)(
    void *, std::string_view, std::string_view, std::string_view,
    std::string_view, bool &) noexcept;

struct ZhongguoReviewNowActionAccessV1 {
  void *context = nullptr;
  DispatchZhongguoReviewNowActionV1 dispatch = nullptr;
};

game::ReadZhongguoPromotionSourceProgressResultV1
ReadZhongguoPromotionSourceProgressV1(
    const ZhongguoPromotionSourceProgressNativeEnvironmentV1 &environment,
    const ZhongguoPromotionSourceProgressAccessV1 &access,
    const ZhongguoPromotionSourceProgressRequestV1 &request,
    game::ZhongguoPromotionSourceProgressV1 &output) noexcept;

std::string SerializeZhongguoPromotionSourceProgressV1(
    const game::ZhongguoPromotionSourceProgressV1 &progress);

bool DispatchZhongguoReviewNowActionNativeV1(
    void *opaque_environment, std::string_view stable_identity,
    std::string_view runtime_name, std::string_view instance_pointer,
    std::string_view vtable_pointer, bool &native_handled) noexcept;

bool ExecuteZhongguoReviewNowActionV1(
    const game::ZhongguoReviewNowActionRequestV1 &request,
    const game::ZhongguoPromotionSourceProgressV1 &source,
    const ZhongguoReviewNowActionAccessV1 &access,
    game::ZhongguoReviewNowActionAckV1 &ack) noexcept;

std::string SerializeZhongguoReviewNowActionAckV1(
    const game::ZhongguoReviewNowActionAckV1 &ack);

} // namespace xar::ck3_11906
