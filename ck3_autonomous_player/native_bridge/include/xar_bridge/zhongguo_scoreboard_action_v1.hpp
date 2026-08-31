#pragma once

#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class ZhongguoScoreboardActionV1 : std::uint32_t {
  open = 0,
  switch_managed = 1,
  switch_received = 2,
  switch_system = 3,
  close = 4,
  reopen = 5,
};

enum class ZhongguoScoreboardActionResultV1 : std::uint32_t {
  rejected = 0,
  acknowledged_verification_pending = 1,
};

struct ZhongguoScoreboardActionBindingV1 {
  std::uint64_t revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t connection_generation = 0;
  std::int32_t date_raw = 0;
  std::int32_t player_character_id = -1;
};

struct ZhongguoScoreboardActionRequestV1 {
  std::string request_nonce;
  ZhongguoScoreboardActionV1 action = ZhongguoScoreboardActionV1::open;
  std::uint64_t expected_revision = 0;
  std::uint64_t expected_native_revision = 0;
  std::uint64_t expected_connection_generation = 0;
  std::int32_t expected_player_character_id = -1;
  std::string expected_window_instance_pointer;
  std::string expected_target_instance_pointer;
  std::string expected_target_vtable_pointer;
};

struct ZhongguoScoreboardActionTargetV1 {
  std::string stable_identity;
  std::string runtime_name;
  std::string instance_pointer;
  std::string vtable_pointer;
};

struct ZhongguoScoreboardActionPostconditionV1 {
  bool requires_independent_query = true;
  std::uint64_t minimum_revision = 0;
  std::uint64_t minimum_native_revision = 0;
  bool modal_effective_visible = false;
  std::string active_tab;
  bool active_tab_available = false;
  bool list_view_required = false;
  std::string expected_window_instance_pointer;
};

struct ZhongguoScoreboardActionAckV1 {
  ZhongguoScoreboardActionResultV1 result =
      ZhongguoScoreboardActionResultV1::rejected;
  bool accepted = false;
  std::string request_nonce;
  ZhongguoScoreboardActionV1 action = ZhongguoScoreboardActionV1::open;
  ZhongguoScoreboardActionBindingV1 source;
  std::string window_instance_pointer;
  ZhongguoScoreboardActionTargetV1 target;
  ZhongguoScoreboardActionPostconditionV1 expected_postcondition;
  bool postcondition_verified = false;
  std::string rejection_reason;
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kZhongguoScoreboardActionV1Capability =
    "game.command.activate-zhongguo-scoreboard-v1";
inline constexpr std::string_view kZhongguoScoreboardActionV1Step =
    "activate-zhongguo-scoreboard-v1";
inline constexpr std::string_view kZhongguoScoreboardActionV1BackendId =
    "ck3-1.19.0.6-native-zhongguo-scoreboard-action-v1";
inline constexpr std::string_view kZhongguoScoreboardActionV1ConsumerId =
    "xar-autoplayer-zhongguo-scoreboard-action-v1";
inline constexpr std::string_view kZhongguoScoreboardActionV1AllowlistId =
    "zg361-scoreboard-named-widget-action-v1";

using DispatchZhongguoScoreboardActionV1 = bool (*)(
    void *, game::ZhongguoScoreboardActionV1, std::string_view,
    std::string_view, std::string_view, std::string_view) noexcept;

struct ZhongguoScoreboardActionAccessV1 {
  void *context = nullptr;
  DispatchZhongguoScoreboardActionV1 dispatch = nullptr;
};

game::ZhongguoScoreboardActionResultV1 ExecuteZhongguoScoreboardActionV1(
    const game::ZhongguoScoreboardActionRequestV1 &request,
    const game::ZhongguoScoreboardActionBindingV1 &binding,
    const game::ZhongguoScoreboardStateV1 &source,
    const ZhongguoScoreboardActionAccessV1 &access,
    game::ZhongguoScoreboardActionAckV1 &ack) noexcept;

std::string SerializeZhongguoScoreboardActionAckV1(
    const game::ZhongguoScoreboardActionAckV1 &ack);

} // namespace xar::ck3_11906
