#pragma once
#include "xar_bridge/ck3_12004_lifestyle.hpp"
#include "xar_bridge/current_first_heir_child_inputs_v1.hpp"
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12004::education {
inline constexpr std::string_view kChildEducationFocusQueryStep12004 =
    "private-query-child-education-focus-v1";
inline constexpr std::string_view kChildEducationFocusSubmitStep12004 =
    "private-select-child-education-focus-v1";
inline constexpr std::string_view kChildEducationFocusReceiptStep12004 =
    "private-query-child-education-focus-receipt-v1";
inline constexpr std::string_view kChildEducationFocusSchema12004 =
    "child-education-focus-private-12004-v1";

// The shared owning mailbox supplies this frame. native_revision is its
// existing published revision; no leaf creates an epoch or sequence.
struct ChildEducationFocusSourceFrame12004 {
  std::string snapshot_id{};
  std::string episode_run_id{};
  std::uint64_t native_revision = 0;
  std::int32_t date_raw = 0;
  std::uint32_t controller_full_id = 0;
  bool paused = false;
};

struct ChildEducationFocusQuery12004 {
  bool available = false;
  std::string unavailable_reason{};
  ChildEducationFocusSourceFrame12004 source_frame{};
  std::uint32_t child_full_id = 0;
  std::string target_key{};
  std::optional<bool> native_legal{};
  ck3_11906::CurrentFirstHeirChildFocusV1 current_focus{};
};

struct ChildEducationFocusSubmission12004 {
  std::string action_id{};
  std::string status = "rejected_before_submit";
  std::string unavailable_reason{};
  bool accepted = false;
  std::uint32_t child_full_id = 0;
  std::string requested_focus_key{};
  ChildEducationFocusSourceFrame12004 pre_frame{};
};

struct ChildEducationFocusPostObservation12004 {
  std::string action_id{};
  bool independently_published_after_submission = false;
  ChildEducationFocusSourceFrame12004 source_frame{};
  std::uint32_t child_full_id = 0;
  ck3_11906::CurrentFirstHeirChildFocusV1 current_focus{};
};

struct ChildEducationFocusReceipt12004 {
  std::string status = "verification_pending";
  std::string unavailable_reason{};
  bool observed_applied = false;
  ChildEducationFocusSubmission12004 submission{};
  std::optional<ChildEducationFocusPostObservation12004> post{};
};

struct ChildEducationFocusTransport12004 {
  std::optional<ChildEducationFocusSubmission12004> pending{};
  bool action_may_have_submitted = false;
  bool needs_post_submit_snapshot = false;
  std::string last_submit_request_id{};
};

bool AcceptsChildEducationFocusStep12004(std::string_view) noexcept;
bool ChildEducationFocusExpectedRevision12004(
    std::string_view payload, std::uint64_t &revision) noexcept;
bool ChildEducationFocusNeedsPostSubmitSnapshot12004(
    const ChildEducationFocusTransport12004 &, std::string_view request_id) noexcept;
bool ExecuteChildEducationFocusMailbox12004(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string HandleChildEducationFocus12004(
    ChildEducationFocusTransport12004 &, std::string_view request_id,
    std::string_view step, std::string_view payload,
    const game::GameAdapter &, const lifestyle::PlayerLifestyleBindings12004 &,
    const game::Snapshot &published, std::uint64_t published_revision,
    ck3_11906::MainThreadQueryMailboxV1 &);
} // namespace xar::ck3_12004::education
