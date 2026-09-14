#pragma once

#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/military_preparation_summary_v1.hpp"

#include <cstdint>
#include <string>

namespace xar::bridge {

inline constexpr std::string_view
    kMilitaryPreparationSummaryPrivateProbeKeyV1 =
        "g2_military_preparation_summary_v1_private_probe";

struct MilitaryPreparationSummaryPrivateProbeV1 {
  MilitaryPreparationSummaryEnvironmentV1 environment{};
  MilitaryPreparationFrameIdentityV1 requested_frame{};
  MilitaryPreparationSummaryResultV1 execution_result{};
  MilitaryPreparationSummaryResultV1 published_result{};
  std::uint64_t expected_revision = 0;
  std::uint64_t published_execution_count = 0;
  bool installed = false;
  bool request_prepared = false;
  bool execution_result_ready = false;
  bool result_published = false;
};

// Attaches an already configured MIL3 environment. The caller may first pass
// it through the MIL4 binding; this layer owns no native pointer and installs
// no hook of its own.
bool InstallMilitaryPreparationSummaryPrivateProbeV1(
    MilitaryPreparationSummaryPrivateProbeV1 &probe,
    const MilitaryPreparationSummaryEnvironmentV1 &environment) noexcept;

bool PrepareMilitaryPreparationSummaryPrivateProbeV1(
    MilitaryPreparationSummaryPrivateProbeV1 &probe,
    const MilitaryPreparationFrameIdentityV1 &frame,
    std::uint64_t expected_revision) noexcept;

bool ReadMilitaryPreparationSummaryPrivateProbeFrameV1(
    void *context, MilitaryPreparationFrameIdentityV1 &output) noexcept;

// Fixed application-main executor admitted only by a private candidate build.
// Query-specific unavailable results still return true to the mailbox.
bool ExecuteMilitaryPreparationSummaryPrivateProbeV1(
    void *context,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

// Called by the bridge worker only after the mailbox reports completion.
bool PublishMilitaryPreparationSummaryPrivateProbeV1(
    MilitaryPreparationSummaryPrivateProbeV1 &probe) noexcept;

bool PublishMilitaryPreparationSummaryPrivateProbeFailureV1(
    MilitaryPreparationSummaryPrivateProbeV1 &probe,
    std::uint32_t failure_flags) noexcept;

std::string SerializeMilitaryPreparationSummaryPrivateProbeV1(
    const MilitaryPreparationSummaryPrivateProbeV1 &probe);

} // namespace xar::bridge
