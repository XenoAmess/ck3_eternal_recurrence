#include "xar_bridge/zhongguo_scoreboard_production_v1.hpp"

#include <array>
#include <cstddef>
#include <limits>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

constexpr std::size_t kWindowIndex = 1;
constexpr std::size_t kModalIndex = 2;
constexpr std::array<std::size_t, 3> kPageIndices{10, 11, 12};
constexpr std::array<std::string_view, 3> kTabs{"managed", "received",
                                                "system"};

ZhongguoScoreboardPostconditionProofV1 Reject(
    ZhongguoScoreboardPostconditionResultV1 result,
    std::string_view reason) noexcept {
  return {result, reason, false};
}

bool AvailableBoolean(const game::ZhongguoTypedBooleanV1 &value,
                      bool &output) noexcept {
  if (!value.available || !value.value.has_value() ||
      !value.unavailable_reason.empty()) {
    return false;
  }
  output = value.value.value();
  return true;
}

bool AvailableString(const game::ZhongguoTypedStringV1 &value,
                     std::string_view &output) noexcept {
  if (!value.available || !value.value.has_value() ||
      !value.unavailable_reason.empty() || value.value->empty()) {
    return false;
  }
  output = value.value.value();
  return true;
}

bool FixedProjection(const game::ZhongguoScoreboardStateV1 &state) noexcept {
  for (std::size_t index = 0; index < state.widgets.size(); ++index) {
    if (state.widgets[index].stable_identity !=
            kZhongguoScoreboardStateV1WidgetIdentities[index] ||
        state.widgets[index].runtime_name !=
            kZhongguoScoreboardStateV1WidgetNames[index]) {
      return false;
    }
  }
  return true;
}

bool UpperHex(std::string_view value, std::size_t length) noexcept {
  if (value.size() != length) return false;
  for (const char character : value) {
    if (!((character >= '0' && character <= '9') ||
          (character >= 'A' && character <= 'F'))) {
      return false;
    }
  }
  return true;
}

bool AckPostconditionIsCoherent(
    const game::ZhongguoScoreboardActionAckV1 &ack) noexcept {
  if (ack.source.revision == 0 || ack.source.native_revision == 0 ||
      ack.source.connection_generation == 0 ||
      ack.source.player_character_id <= 0 ||
      ack.source.observation_sequence == 0 ||
      ack.source.observation_sequence ==
          std::numeric_limits<std::uint64_t>::max() ||
      ack.source.observed_state_revision == 0 ||
      ack.source.observed_state_revision ==
          std::numeric_limits<std::uint64_t>::max() ||
      !UpperHex(ack.source.provider_session_id, 32) ||
      !UpperHex(ack.source.tree_fingerprint_v1, 64) ||
      !UpperHex(ack.source.semantic_fingerprint_v1, 64) ||
      ack.window_instance_pointer.empty() ||
      ack.expected_postcondition.minimum_observation_sequence !=
          ack.source.observation_sequence + 1 ||
      ack.expected_postcondition.minimum_observed_state_revision !=
          ack.source.observed_state_revision + 1 ||
      ack.expected_postcondition.expected_provider_session_id !=
          ack.source.provider_session_id ||
      ack.expected_postcondition.expected_tree_fingerprint_v1 !=
          ack.source.tree_fingerprint_v1 ||
      ack.expected_postcondition.expected_window_instance_pointer !=
          ack.window_instance_pointer) {
    return false;
  }
  switch (ack.action) {
  case game::ZhongguoScoreboardActionV1::open:
    return ack.expected_postcondition.active_tab_available &&
           ack.expected_postcondition.list_view_required &&
           ack.expected_postcondition.modal_effective_visible;
  case game::ZhongguoScoreboardActionV1::switch_managed:
    return ack.expected_postcondition.active_tab_available &&
           ack.expected_postcondition.list_view_required &&
           ack.expected_postcondition.modal_effective_visible &&
           ack.expected_postcondition.active_tab == "managed";
  case game::ZhongguoScoreboardActionV1::switch_received:
    return ack.expected_postcondition.active_tab_available &&
           ack.expected_postcondition.list_view_required &&
           ack.expected_postcondition.modal_effective_visible &&
           ack.expected_postcondition.active_tab == "received";
  case game::ZhongguoScoreboardActionV1::switch_system:
    return ack.expected_postcondition.active_tab_available &&
           ack.expected_postcondition.list_view_required &&
           ack.expected_postcondition.modal_effective_visible &&
           ack.expected_postcondition.active_tab == "system";
  case game::ZhongguoScoreboardActionV1::close:
    return !ack.expected_postcondition.active_tab_available &&
           !ack.expected_postcondition.list_view_required &&
           !ack.expected_postcondition.modal_effective_visible &&
           ack.expected_postcondition.active_tab.empty();
  case game::ZhongguoScoreboardActionV1::reopen:
    return false;
  }
  return false;
}

} // namespace

ZhongguoScoreboardPostconditionProofV1
VerifyZhongguoScoreboardReadOnlyPostconditionV1(
    const game::ZhongguoScoreboardActionAckV1 &ack,
    const game::ZhongguoScoreboardStateV1 &post_state,
    std::uint64_t observed_public_revision,
    std::uint64_t observed_connection_generation) noexcept {
  if (ack.result != game::ZhongguoScoreboardActionResultV1::
                        acknowledged_verification_pending ||
      !ack.accepted || ack.postcondition_verified || ack.request_nonce.empty() ||
      !ack.expected_postcondition.requires_independent_query ||
      !AckPostconditionIsCoherent(ack)) {
    return Reject(ZhongguoScoreboardPostconditionResultV1::ack_unavailable,
                  "ack_unavailable");
  }
  if (post_state.status != game::ZhongguoScoreboardStateStatusV1::available ||
      post_state.case_kind != kZhongguoScoreboardStateV1CaseKind ||
      !post_state.readiness.state_acl_query_ready ||
      !FixedProjection(post_state)) {
    return Reject(
        ZhongguoScoreboardPostconditionResultV1::post_state_unavailable,
        "post_state_unavailable");
  }
  if (!post_state.paused ||
      observed_public_revision != ack.source.revision ||
      post_state.snapshot_revision != ack.source.native_revision ||
      observed_connection_generation != ack.source.connection_generation ||
      post_state.date_raw != ack.source.date_raw ||
      post_state.player_character_id != ack.source.player_character_id) {
    return Reject(
        ZhongguoScoreboardPostconditionResultV1::paused_binding_changed,
        "paused_binding_changed");
  }
  if (post_state.request_nonce.empty() ||
      post_state.request_nonce == ack.request_nonce ||
      post_state.provider_session_id != ack.source.provider_session_id ||
      post_state.provider_session_id !=
          ack.expected_postcondition.expected_provider_session_id ||
      post_state.tree_fingerprint_v1 != ack.source.tree_fingerprint_v1 ||
      post_state.tree_fingerprint_v1 !=
          ack.expected_postcondition.expected_tree_fingerprint_v1) {
    return Reject(
        ZhongguoScoreboardPostconditionResultV1::provider_binding_changed,
        "provider_binding_changed");
  }
  if (post_state.observation_sequence <
          ack.expected_postcondition.minimum_observation_sequence ||
      post_state.observed_state_revision <
          ack.expected_postcondition.minimum_observed_state_revision) {
    return Reject(
        ZhongguoScoreboardPostconditionResultV1::observation_not_advanced,
        "observation_not_advanced");
  }
  if (!UpperHex(post_state.semantic_fingerprint_v1, 64) ||
      post_state.semantic_fingerprint_v1 ==
          ack.source.semantic_fingerprint_v1) {
    return Reject(
        ZhongguoScoreboardPostconditionResultV1::semantic_state_unchanged,
        "semantic_state_unchanged");
  }

  std::string_view window_instance;
  if (!AvailableString(post_state.widgets[kWindowIndex].instance_pointer,
                       window_instance) ||
      window_instance != ack.window_instance_pointer ||
      window_instance !=
          ack.expected_postcondition.expected_window_instance_pointer) {
    return Reject(
        ZhongguoScoreboardPostconditionResultV1::window_instance_changed,
        "window_instance_changed");
  }

  bool modal_visible = false;
  if (!AvailableBoolean(post_state.widgets[kModalIndex].effective_visible,
                        modal_visible)) {
    return Reject(
        ZhongguoScoreboardPostconditionResultV1::widget_projection_invalid,
        "modal_visibility_unavailable");
  }
  std::array<bool, 3> page_visible{};
  for (std::size_t index = 0; index < page_visible.size(); ++index) {
    if (!AvailableBoolean(
            post_state.widgets[kPageIndices[index]].effective_visible,
            page_visible[index])) {
      return Reject(
          ZhongguoScoreboardPostconditionResultV1::widget_projection_invalid,
          "page_visibility_unavailable");
    }
  }
  if (modal_visible !=
      ack.expected_postcondition.modal_effective_visible) {
    return Reject(
        ZhongguoScoreboardPostconditionResultV1::explicit_postcondition_failed,
        "modal_visibility_mismatch");
  }

  std::size_t visible_pages = 0;
  std::size_t visible_page_index = page_visible.size();
  for (std::size_t index = 0; index < page_visible.size(); ++index) {
    if (page_visible[index]) {
      ++visible_pages;
      visible_page_index = index;
    }
  }
  if (ack.expected_postcondition.active_tab_available) {
    if (!ack.expected_postcondition.list_view_required || visible_pages != 1 ||
        visible_page_index == page_visible.size() ||
        ack.expected_postcondition.active_tab != kTabs[visible_page_index]) {
      return Reject(
          ZhongguoScoreboardPostconditionResultV1::
              explicit_postcondition_failed,
          "active_page_mismatch");
    }
  } else if (ack.expected_postcondition.list_view_required ||
             !ack.expected_postcondition.active_tab.empty() ||
             visible_pages != 0) {
    return Reject(
        ZhongguoScoreboardPostconditionResultV1::explicit_postcondition_failed,
        "closed_page_mismatch");
  }

  return {ZhongguoScoreboardPostconditionResultV1::verified, "verified", true};
}

} // namespace xar::ck3_11906
