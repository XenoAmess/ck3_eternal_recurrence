#pragma once

#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"

#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_11906 {

inline constexpr std::string_view kFrontendGameRulesV1Capability =
    "game.command.query-frontend-game-rule-selections-v1";
inline constexpr std::string_view kFrontendGameRulesV1Step =
    "query-frontend-game-rule-selections-v1";
inline constexpr std::string_view kFrontendOpenGameRulesV1Capability =
    "game.command.activate-frontend-game-rules-v1";
inline constexpr std::string_view kFrontendOpenGameRulesV1Step =
    "activate-frontend-game-rules-v1";

struct FrontendGameRuleSelectionV1 {
  std::string rule_key;
  std::string selected_setting_key;
  bool operator==(const FrontendGameRuleSelectionV1 &) const = default;
};

struct FrontendGameRulesObservationV1 {
  bool ready = false;
  std::string unavailable_reason;
  std::vector<FrontendGameRuleSelectionV1> selections;
};

// Application-main mailbox only. game_rules_root is resolved by the native
// named-widget reader; the public request accepts no pointer, key or limit.
// Reads CJominiGameRulesGui's current selection model, never a preset or OCR.
bool ProbeFrontendGameRulesV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access, const void *game_rules_root,
    FrontendGameRulesObservationV1 &output) noexcept;

std::string SerializeFrontendGameRulesV1(
    const FrontendGameRulesObservationV1 &observation);

} // namespace xar::ck3_11906
