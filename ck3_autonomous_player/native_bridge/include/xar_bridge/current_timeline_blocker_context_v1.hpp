#pragma once

#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class CurrentTimelineBlockerStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

enum class CurrentTimelineBlockerIdentityV1 : std::uint32_t {
  none = 0,
  death_succession_modal = 1,
  game_over_modal = 2,
  succession_select_destiny_modal = 3,
};

struct TimelineBlockerTypedBooleanV1 {
  bool available = false;
  bool value = false;
  std::string unavailable_reason;

  friend bool operator==(const TimelineBlockerTypedBooleanV1 &,
                         const TimelineBlockerTypedBooleanV1 &) = default;
};

struct CurrentTimelineBlockerEvidenceV1 {
  std::string source_kind;
  std::string source_path;
  std::string root_name;
  std::string decisive_widget_name;

  friend bool operator==(const CurrentTimelineBlockerEvidenceV1 &,
                         const CurrentTimelineBlockerEvidenceV1 &) = default;
};

struct CurrentTimelineBlockerContextV1 {
  CurrentTimelineBlockerStatusV1 status =
      CurrentTimelineBlockerStatusV1::unavailable;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  CurrentTimelineBlockerIdentityV1 identity =
      CurrentTimelineBlockerIdentityV1::none;
  TimelineBlockerTypedBooleanV1 blocks_simulation;
  TimelineBlockerTypedBooleanV1 can_continue;
  CurrentTimelineBlockerEvidenceV1 evidence;
  std::string unavailable_reason;

  friend bool operator==(const CurrentTimelineBlockerContextV1 &,
                         const CurrentTimelineBlockerContextV1 &) = default;
};

enum class ReadCurrentTimelineBlockerContextResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr bool kCurrentTimelineBlockerContextV1CapabilityAdvertised =
    false;
inline constexpr std::string_view kCurrentTimelineBlockerContextV1Capability =
    "game.command.query-current-timeline-blocker-context-v1";
inline constexpr std::string_view kCurrentTimelineBlockerContextV1Step =
    "query-current-timeline-blocker-context-v1";
inline constexpr std::string_view kCurrentTimelineBlockerContextV1GameVersion =
    "1.19.0.6";
inline constexpr std::string_view
    kCurrentTimelineBlockerContextV1ExecutableSha256 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view kCurrentTimelineBlockerStockGuiPath =
    "game/gui/window_succession_event.gui";

enum class CurrentTimelineFixedWidgetV1 : std::uint32_t {
  succession_root = 0,
  succession_bottom = 1,
  succession_close = 2,
  succession_menu = 3,
  destiny_root = 4,
  destiny_continue = 5,
  destiny_continue_random = 6,
  destiny_cancel = 7,
};

inline constexpr std::size_t kCurrentTimelineFixedWidgetCountV1 = 8;

struct CurrentTimelineWidgetObservationV1 {
  bool exists = false;
  bool effective_visible = false;
  bool enabled = false;

  friend bool operator==(const CurrentTimelineWidgetObservationV1 &,
                         const CurrentTimelineWidgetObservationV1 &) = default;
};

using ObserveCurrentTimelineFixedWidgetV1 =
    bool (*)(void *, CurrentTimelineFixedWidgetV1,
             CurrentTimelineWidgetObservationV1 &) noexcept;

struct CurrentTimelineBlockerReadRequestV1 {
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
};

struct CurrentTimelineBlockerSourceV1 {
  void *context = nullptr;
  ObserveCurrentTimelineFixedWidgetV1 observe_fixed_widget = nullptr;
};

game::ReadCurrentTimelineBlockerContextResultV1
ReadCurrentTimelineBlockerContextV1(
    const CurrentTimelineBlockerReadRequestV1 &request,
    const CurrentTimelineBlockerSourceV1 &source,
    game::CurrentTimelineBlockerContextV1 &output) noexcept;

// Production adapter. It reuses the frozen exact-build GUI owner, fixed-name
// lookup, child traversal, and effective visibility primitives. It accepts no
// caller-provided widget name or pointer.
game::ReadCurrentTimelineBlockerContextResultV1
ReadCurrentTimelineBlockerContextNativeV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access,
    const CurrentTimelineBlockerReadRequestV1 &request,
    game::CurrentTimelineBlockerContextV1 &output) noexcept;

std::string SerializeCurrentTimelineBlockerContextV1(
    const game::CurrentTimelineBlockerContextV1 &context);

bool ParseCurrentTimelineBlockerContextV1Step(std::string_view step) noexcept;
bool ParseCurrentTimelineBlockerContextRequestV1(
    std::string_view json, std::uint64_t &expected_revision) noexcept;

} // namespace xar::ck3_11906
