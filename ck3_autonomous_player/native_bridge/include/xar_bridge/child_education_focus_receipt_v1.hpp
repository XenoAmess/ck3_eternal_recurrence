#pragma once

#include "xar_bridge/child_education_focus_private_12004.hpp"

namespace xar::ck3_12004::education {

// Inputs are copied accepted-submission facts and the host's independently
// published same-child observation. This function performs no native read,
// creates no frame identity and adds no admission to the original action.
inline ChildEducationFocusReceipt12004 EvaluateChildEducationFocusReceipt12004(
    const ChildEducationFocusSubmission12004 &submission,
    const std::optional<ChildEducationFocusPostObservation12004> &post) {
  ChildEducationFocusReceipt12004 receipt{};
  receipt.submission = submission;
  receipt.post = post;
  const auto unavailable = [&receipt](std::string_view reason) {
    receipt.status = "unavailable";
    receipt.unavailable_reason = reason;
  };

  if (!submission.accepted ||
      submission.status != "submitted_verification_pending") {
    unavailable("child_focus_submission_not_accepted");
    return receipt;
  }
  if (submission.action_id.empty() || submission.requested_focus_key.empty()) {
    unavailable("child_focus_submission_binding_unavailable");
    return receipt;
  }
  const auto &pre_frame = submission.pre_frame;
  if (pre_frame.snapshot_id.empty() || pre_frame.episode_run_id.empty() ||
      pre_frame.native_revision == 0) {
    unavailable("child_focus_submission_source_frame_unavailable");
    return receipt;
  }
  if (!post.has_value()) {
    receipt.unavailable_reason = "child_focus_acknowledged_verification_pending";
    return receipt;
  }

  const auto &observed = *post;
  const auto &post_frame = observed.source_frame;
  if (post_frame.snapshot_id.empty() || post_frame.episode_run_id.empty() ||
      post_frame.native_revision == 0) {
    unavailable("child_focus_post_submit_source_frame_unavailable");
    return receipt;
  }
  if (observed.action_id != submission.action_id) {
    unavailable("child_focus_receipt_action_id_mismatch");
    return receipt;
  }
  if (observed.child_full_id != submission.child_full_id) {
    unavailable("child_focus_receipt_child_full_id_mismatch");
    return receipt;
  }
  if (post_frame.episode_run_id != pre_frame.episode_run_id ||
      post_frame.controller_full_id != pre_frame.controller_full_id) {
    unavailable("child_focus_receipt_source_binding_mismatch");
    return receipt;
  }
  if (!observed.independently_published_after_submission) {
    receipt.unavailable_reason = "child_focus_independent_snapshot_pending";
    return receipt;
  }
  if (post_frame.native_revision <= pre_frame.native_revision ||
      post_frame.snapshot_id == pre_frame.snapshot_id) {
    receipt.unavailable_reason = "child_focus_new_source_snapshot_pending";
    return receipt;
  }

  // This is the existing owned readonly leaf, including its two agreeing
  // samples and full-ID/liveness bookends. Preserve its unknown/absent fields.
  const auto &focus = observed.current_focus;
  if (!focus.available) {
    unavailable(focus.unavailable_reason.empty()
                    ? std::string_view{"child_focus_current_focus_unavailable"}
                    : focus.unavailable_reason);
    return receipt;
  }
  if (focus.presence == "absent" && !focus.key.has_value()) {
    receipt.unavailable_reason = "child_focus_known_absent_after_submission";
    return receipt;
  }
  if (focus.presence != "present" || !focus.key.has_value()) {
    unavailable("child_focus_current_focus_shape_unavailable");
    return receipt;
  }
  if (*focus.key != submission.requested_focus_key) {
    receipt.unavailable_reason = "child_focus_requested_key_not_observed";
    return receipt;
  }

  // A new source frame observes this state. Queue acceptance alone and a
  // changed pointer inside the original published frame cannot establish it.
  receipt.status = "observed_applied";
  receipt.observed_applied = true;
  receipt.unavailable_reason.clear();
  return receipt;
}

} // namespace xar::ck3_12004::education
