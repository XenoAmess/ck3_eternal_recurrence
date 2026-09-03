#include "xar_bridge/zhongguo_scoreboard_production_v1.hpp"

#include <iostream>
#include <string>

namespace {

template <typename Value>
xar::game::ZhongguoTypedValueV1<Value> Available(Value value) {
  xar::game::ZhongguoTypedValueV1<Value> result{};
  result.available = true;
  result.value = std::move(value);
  return result;
}

xar::game::ZhongguoScoreboardStateV1 State() {
  xar::game::ZhongguoScoreboardStateV1 state{};
  state.status = xar::game::ZhongguoScoreboardStateStatusV1::available;
  state.case_kind = "zhongguo.scoreboard.named-state-acl";
  state.request_nonce = "scoreboard.post.query";
  state.snapshot_revision = 9;
  state.date_raw = 4100;
  state.paused = true;
  state.player_character_id = 101;
  state.tree_fingerprint_v1 = std::string(64, 'A');
  state.semantic_fingerprint_v1 = std::string(64, 'C');
  state.provider_session_id = std::string(32, 'D');
  state.observation_sequence = 8;
  state.observed_state_revision = 4;
  state.readiness.state_acl_query_ready = true;
  for (std::size_t index = 0; index < state.widgets.size(); ++index) {
    auto &widget = state.widgets[index];
    widget.stable_identity.assign(
        xar::ck3_11906::kZhongguoScoreboardStateV1WidgetIdentities[index]);
    widget.runtime_name.assign(
        xar::ck3_11906::kZhongguoScoreboardStateV1WidgetNames[index]);
    widget.instance_pointer = Available(std::string("0x") +
                                        std::to_string(1000 + index));
    widget.vtable_pointer = Available(std::string("0x") +
                                      std::to_string(2000 + index));
    widget.exists = Available(true);
    widget.local_visible = Available(true);
    widget.effective_visible = Available(false);
    widget.enabled = Available(true);
  }
  state.widgets[2].effective_visible = Available(true);
  state.widgets[11].effective_visible = Available(true);
  return state;
}

xar::game::ZhongguoScoreboardActionAckV1 Ack(
    const xar::game::ZhongguoScoreboardStateV1 &post) {
  xar::game::ZhongguoScoreboardActionAckV1 ack{};
  ack.result = xar::game::ZhongguoScoreboardActionResultV1::
      acknowledged_verification_pending;
  ack.accepted = true;
  ack.request_nonce = "scoreboard.action";
  ack.action = xar::game::ZhongguoScoreboardActionV1::switch_received;
  ack.source.revision = 77;
  ack.source.native_revision = post.snapshot_revision;
  ack.source.connection_generation = 5;
  ack.source.date_raw = post.date_raw;
  ack.source.player_character_id = post.player_character_id;
  ack.source.provider_session_id = post.provider_session_id;
  ack.source.observation_sequence = post.observation_sequence - 1;
  ack.source.observed_state_revision = post.observed_state_revision - 1;
  ack.source.tree_fingerprint_v1 = post.tree_fingerprint_v1;
  ack.source.semantic_fingerprint_v1 = std::string(64, 'B');
  ack.window_instance_pointer = post.widgets[1].instance_pointer.value.value();
  ack.expected_postcondition.requires_independent_query = true;
  ack.expected_postcondition.minimum_observation_sequence =
      post.observation_sequence;
  ack.expected_postcondition.minimum_observed_state_revision =
      post.observed_state_revision;
  ack.expected_postcondition.expected_provider_session_id =
      post.provider_session_id;
  ack.expected_postcondition.expected_tree_fingerprint_v1 =
      post.tree_fingerprint_v1;
  ack.expected_postcondition.modal_effective_visible = true;
  ack.expected_postcondition.active_tab = "received";
  ack.expected_postcondition.active_tab_available = true;
  ack.expected_postcondition.list_view_required = true;
  ack.expected_postcondition.expected_window_instance_pointer =
      ack.window_instance_pointer;
  return ack;
}

bool Verified(const xar::game::ZhongguoScoreboardActionAckV1 &ack,
              const xar::game::ZhongguoScoreboardStateV1 &post) {
  return xar::ck3_11906::VerifyZhongguoScoreboardReadOnlyPostconditionV1(
             ack, post, 77, 5)
      .verified;
}

} // namespace

int main() {
#if defined(XAR_CK3_ENABLE_ZHONGGUO_SCOREBOARD_PRODUCTION_V1)
  if (!xar::ck3_11906::
          kZhongguoScoreboardProductionCandidateEnabledV1) {
    return 1;
  }
#else
  if (xar::ck3_11906::
          kZhongguoScoreboardProductionCandidateEnabledV1) {
    return 2;
  }
#endif
  if (xar::ck3_11906::
          kZhongguoScoreboardActionV1ProductionCapabilityAdvertised) {
    return 13;
  }

  const auto post = State();
  const auto ack = Ack(post);
  if (!Verified(ack, post)) return 3;

  auto unchanged = post;
  unchanged.semantic_fingerprint_v1 = ack.source.semantic_fingerprint_v1;
  if (Verified(ack, unchanged)) return 4;

  auto stale = post;
  stale.observed_state_revision = ack.source.observed_state_revision;
  if (Verified(ack, stale)) return 5;

  auto rebound = post;
  rebound.provider_session_id = std::string(32, 'E');
  if (Verified(ack, rebound)) return 6;

  auto wrong_page = post;
  wrong_page.widgets[11].effective_visible = Available(false);
  wrong_page.widgets[12].effective_visible = Available(true);
  if (Verified(ack, wrong_page)) return 7;

  auto same_nonce = post;
  same_nonce.request_nonce = ack.request_nonce;
  if (Verified(ack, same_nonce)) return 8;

  auto forged_ack = ack;
  forged_ack.postcondition_verified = true;
  if (Verified(forged_ack, post)) return 9;

  forged_ack = ack;
  forged_ack.expected_postcondition.minimum_observed_state_revision = 1;
  if (Verified(forged_ack, post)) return 10;

  forged_ack = ack;
  forged_ack.action = xar::game::ZhongguoScoreboardActionV1::switch_system;
  if (Verified(forged_ack, post)) return 11;

  forged_ack = ack;
  forged_ack.action = xar::game::ZhongguoScoreboardActionV1::reopen;
  if (Verified(forged_ack, post)) return 12;

  std::cout << "scoreboard production readiness fixture: GREEN\n";
  return 0;
}
