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

// Exact original GUI predicates and the current owner's actual root visibility.
// This observation remains distinct from current selections and applied rules.
struct FrontendGameRulesControlV1 {
  bool ready = false;
  bool window_visible = false;
  bool window_enabled = false;
  bool is_host = false;
  bool game_has_started = false;
  bool may_edit = false;
  std::string unavailable_reason;
};

struct FrontendGameRuleChoiceV1 {
  std::string rule_key;
  std::string current_setting_key;
  std::string desired_setting_key;
  std::uint32_t next_count = 0;
  std::vector<std::string> option_keys;
  bool ready = false;
  std::string unavailable_reason;
};

// Internal providers accept a root already resolved as the actual named window.
// Public commands never accept pointers, GUI paths, or caller-selected callbacks.
bool ProbeFrontendGameRulesControlV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access, const void *game_rules_root,
    FrontendGameRulesControlV1 &output) noexcept;
bool ProbeFrontendGameRuleChoiceV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access, const void *game_rules_root,
    std::string_view rule_key, std::string_view expected_current_setting_key,
    std::string_view desired_setting_key,
    FrontendGameRuleChoiceV1 &output) noexcept;

inline constexpr std::string_view kFrontendGameRulesControlV1Capability =
    "game.command.query-frontend-game-rules-window-v1";
inline constexpr std::string_view kFrontendGameRulesControlV1Step =
    "query-frontend-game-rules-window-v1";
inline constexpr std::string_view kFrontendSelectGameRuleV1Capability =
    "game.command.select-frontend-game-rule-v1";
inline constexpr std::string_view kFrontendSelectGameRuleV1Step =
    "select-frontend-game-rule-v1";
inline constexpr std::string_view kFrontendApplyGameRulesV1Capability =
    "game.command.apply-and-hide-frontend-game-rules-v1";
inline constexpr std::string_view kFrontendApplyGameRulesV1Step =
    "apply-and-hide-frontend-game-rules-v1";
inline constexpr std::string_view kFrontendHideGameRulesV1Capability =
    "game.command.hide-frontend-game-rules-v1";
inline constexpr std::string_view kFrontendHideGameRulesV1Step =
    "hide-frontend-game-rules-v1";

// Internal test substitutions are accepted only with both explicit offline
// fixture admission and a fixture memory reader. Live callers leave this empty.
using NativeFrontendGameRulesCallV1 = bool (*)(void *, void *) noexcept;
struct FrontendGameRulesCallsV1 {
  void *context = nullptr;
  NativeFrontendGameRulesCallV1 next = nullptr;
  NativeFrontendGameRulesCallV1 apply = nullptr;
  NativeFrontendGameRulesCallV1 hide = nullptr;
};

enum class FrontendGameRulesMutationKindV1 : std::uint32_t {
  select = 1, apply_and_hide = 2, hide = 3,
};
struct FrontendGameRulesMutationV1 {
  bool ready = false;
  bool native_invoked = false;
  bool selection_verified = false;
  bool apply_invoked = false;
  bool hide_invoked = false;
  std::uint32_t native_next_calls = 0;
  std::string unavailable_reason;
};

bool SelectFrontendGameRuleV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access, const void *game_rules_root,
    std::string_view rule_key, std::string_view expected_current_setting_key,
    std::string_view desired_setting_key, const FrontendGameRulesCallsV1 &calls,
    FrontendGameRulesMutationV1 &output) noexcept;
bool ApplyAndHideFrontendGameRulesV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access, const void *game_rules_root,
    bool apply, const FrontendGameRulesCallsV1 &calls,
    FrontendGameRulesMutationV1 &output) noexcept;
std::string SerializeFrontendGameRulesControlV1(
    const FrontendGameRulesControlV1 &observation);
std::string SerializeFrontendGameRulesMutationV1(
    FrontendGameRulesMutationKindV1 kind,
    const FrontendGameRulesMutationV1 &result);

inline constexpr std::string_view kFrontendAppliedGameRulesV1Capability =
    "game.command.query-frontend-applied-game-rules-v1";
inline constexpr std::string_view kFrontendAppliedGameRulesV1Step =
    "query-frontend-applied-game-rules-v1";
struct FrontendAppliedGameRulesV1 {
  bool ready = false;
  std::string unavailable_reason;
  std::vector<FrontendGameRuleSelectionV1> selections;
};
bool ProbeFrontendAppliedGameRulesV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access,
    FrontendAppliedGameRulesV1 &output) noexcept;
std::string SerializeFrontendAppliedGameRulesV1(
    const FrontendAppliedGameRulesV1 &observation);

} // namespace xar::ck3_11906
