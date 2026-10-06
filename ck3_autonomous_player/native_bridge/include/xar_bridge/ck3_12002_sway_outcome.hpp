#pragma once

#include "xar_bridge/ck3_12002_event_window_context.hpp"
#include "xar_bridge/ck3_12002_gift_opinion.hpp"

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kSwayOutcomeSchemeStorageSlotRva = 0x5D1FC58;
inline constexpr std::uintptr_t kSwayOutcomeTargetOpinionRva = 0x28BC490;
inline constexpr std::uint16_t kSwayOutcomeSchemeScopeType = 9;
inline constexpr std::string_view kSwayOutcomeOpinionStepV1 =
    "query-sway-outcome-opinion-v1-private";

using SwayOutcomeTargetOpinion = std::int32_t (*)(void *recipient, void *actor);

struct SwayOutcomeBindings {
  EventWindowBindings event_window;
  void **scheme_storage_slot = nullptr;
  SwayOutcomeTargetOpinion target_opinion = nullptr;
  GiftOpinionBindings12002 opinion_modifiers;
  std::string_view build_version = "1.20.0.2";
};

SwayOutcomeBindings BindSwayOutcomeImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

struct SwayOutcomeRequestV1 {
  std::uint64_t expected_revision = 0;
  std::int32_t event_instance_id = -1;
  std::int32_t actor_character_id = -1;
  std::int32_t target_character_id = -1;
  std::uint32_t scheme_id = 0xFFFFFFFFu;
};

enum class SwayPhaseResultV1 { unknown, success, failure };

struct SwayOpinionModifierV1 {
  bool observed = false;
  bool present = false;
  std::optional<std::int32_t> value;
  friend bool operator==(const SwayOpinionModifierV1 &, const SwayOpinionModifierV1 &) = default;
};

struct SwayOutcomeOpinionV1 {
  bool available = false;
  std::string unavailable_reason;
  std::int32_t actor_character_id = -1;
  std::int32_t target_character_id = -1;
  std::int32_t target_opinion_of_actor = 0;
  SwayOpinionModifierV1 scheme_sway_opinion;
  SwayOpinionModifierV1 sway_blocker_opinion;
  std::string_view build_version = "1.20.0.2";
};

// Independent material readback, also usable after the outcome event has been
// consumed. Association to a prior exact event source belongs to its consumer.
bool ReadSwayOutcomeOpinionV1(const SwayOutcomeBindings &bindings,
                             std::int32_t actor_character_id,
                             std::int32_t target_character_id,
                             SwayOutcomeOpinionV1 &output) noexcept;
std::string SerializeSwayOutcomeOpinionV1(const SwayOutcomeOpinionV1 &output,
                                        std::uint64_t snapshot_revision,
                                        std::int32_t date_raw);
// Same full command-result wire used by the application-main mailbox handler.
// This readback is independent of the presence of a current outcome event.
std::string SerializeSwayOutcomeOpinionResponseV1(
    const SwayOutcomeOpinionV1 &output, std::uint64_t snapshot_revision,
    std::int32_t date_raw, std::string_view request_id);

// These are exact authored effects for the native option index. They are
// projections, never measurements of an executed option or total opinion delta.
struct SwayOutcomeOptionV1 {
  std::int32_t rendered_index = -1;
  std::int32_t native_option_index = -1;
  bool shown = false;
  bool enabled = false;
  bool deterministic = false;
  bool end_scheme_effect = false;
  bool sway_end_effect = false;
  std::int32_t authored_sway_points_on_success = 0;
  std::int32_t authored_sway_points_on_failure = 0;
  std::string authored_sway_modifier_selection = "none";
  std::int32_t authored_blocker_points = 0;
  std::string resolved_name;
};

struct SwayOutcomeEventV1 {
  bool available = false;
  std::string unavailable_reason;
  SwayOutcomeRequestV1 request;
  std::int32_t date_raw = 0;
  std::string event_definition_key;
  bool exact_scope_join_ready = false;
  bool phase_result_observed = false;
  SwayPhaseResultV1 phase_result = SwayPhaseResultV1::unknown;
  bool target_opinion_observed = false;
  std::int32_t target_opinion_of_actor = 0;
  SwayOpinionModifierV1 scheme_sway_opinion;
  SwayOpinionModifierV1 sway_blocker_opinion;
  std::int32_t authored_immediate_sway_points = 0;
  std::string authored_immediate_modifier_selection = "none";
  std::vector<SwayOutcomeOptionV1> options;
  // A current event precedes option execution. All available observations keep
  // this false; completion requires a separate material post-action source.
  bool instance_terminal_outcome_observed = false;
  bool cancel_outcome_observed = false;
};

// Application owner-thread read. Joins the existing current-event context's
// root/owner/target and its native typed SchemeID to an already tracked intent.
// The regular hidden .0001/.0002 messages are outside this producer's coverage.
bool ReadSwayOutcomeEventV1(const SwayOutcomeBindings &bindings,
                           const SwayOutcomeRequestV1 &request,
                           SwayOutcomeEventV1 &output) noexcept;

std::string SerializeSwayOutcomeEventV1(const SwayOutcomeEventV1 &output);

} // namespace xar::ck3_12002
