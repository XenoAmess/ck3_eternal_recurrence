#pragma once

#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/marriage_shared_glue_v1.hpp"

#include <atomic>
#include <cstdint>

namespace xar::bridge {

enum class MarriageApplicationMainReceiptFailureV1 : std::uint32_t {
  none = 0,
  invalid_environment,
  shared_glue_unavailable,
  mailbox_not_executing,
  application_main_identity_unproven,
  paused_frame_unproven,
  revision_unavailable,
  frame_publish_failed,
};

// Private bridge-side adapter for the fixed application-main mailbox. A
// future marriage query executor passes the execution stamp it received from
// that mailbox and the already-published native snapshot revision. The
// adapter constructs the canonical `native:<revision>` identity itself; an
// action ACK has no path to this surface.
struct MarriageApplicationMainReceiptStateV1 {
  MarriageSharedGlueStateV1 *shared_glue = nullptr;
  xar::ck3_11906::MainThreadQueryMailboxV1 *mailbox = nullptr;
  std::atomic<std::uint32_t> last_failure{static_cast<std::uint32_t>(
      MarriageApplicationMainReceiptFailureV1::none)};
};

bool ConfigureMarriageApplicationMainReceiptV1(
    MarriageApplicationMainReceiptStateV1 &state,
    MarriageSharedGlueStateV1 &shared_glue,
    xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox) noexcept;

bool PublishMarriageApplicationMainReceiptV1(
    MarriageApplicationMainReceiptStateV1 &state,
    const xar::ck3_11906::MainThreadExecutionStampV1 &execution_stamp,
    std::uint64_t snapshot_revision) noexcept;

MarriageApplicationMainReceiptFailureV1
ReadMarriageApplicationMainReceiptFailureV1(
    const MarriageApplicationMainReceiptStateV1 &state) noexcept;

} // namespace xar::bridge
