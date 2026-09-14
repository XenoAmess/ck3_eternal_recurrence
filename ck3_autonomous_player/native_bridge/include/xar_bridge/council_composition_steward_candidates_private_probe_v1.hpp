#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/council_composition_steward_candidates_binding_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view
    kCouncilCompositionStewardCandidatesPrivateProbeKeyV1 =
        "g2_council_composition_steward_candidates_private_probe_v1";

struct CouncilCompositionStewardCandidatesPrivateProbeV1 {
  xar::ck3_11906::MainThreadQueryMailboxV1 *mailbox = nullptr;
  xar::ck3_11906::Bindings bindings{};
  xar::ck3_11906::CouncilCompositionStewardCandidatesBindingStateV1
      *binding_state = nullptr;
  xar::ck3_11906::CouncilCompositionStewardCandidatesEnvironmentV1
      environment{};
  xar::ck3_11906::CouncilCompositionStewardCandidatesAccessV1 access{};
  xar::ck3_11906::CouncilCompositionStewardCandidatesRequestV1 request{};
  xar::game::Snapshot expected_snapshot{};
  std::array<char, xar::game::kCouncilCompositionStewardSnapshotIdCapacityV1>
      expected_snapshot_id{};
  xar::game::CouncilCompositionStewardCandidatesV1 execution_result{};
  xar::game::CouncilCompositionStewardCandidatesV1 published_result{};
  xar::ck3_11906::MainThreadQueryTicketV1 ticket{};
  const xar::ck3_11906::MainThreadExecutionStampV1 *active_stamp = nullptr;
  std::uint64_t published_execution_count = 0;
  bool transport_configured = false;
  bool installed = false;
  bool request_prepared = false;
  bool execution_result_ready = false;
  bool result_published = false;
};

// Prepares the private application-main transport before Council7 binds the
// two callbacks returned by CouncilCompositionStewardCandidatesProbeAccessV1.
// No native call occurs here.
bool ConfigureCouncilCompositionStewardCandidatesPrivateProbeTransportV1(
    CouncilCompositionStewardCandidatesPrivateProbeV1 &probe,
    xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const xar::ck3_11906::Bindings &bindings,
    xar::ck3_11906::CouncilCompositionStewardCandidatesBindingStateV1
        &binding_state) noexcept;

xar::ck3_11906::CouncilCompositionStewardCandidatesAccessV1
CouncilCompositionStewardCandidatesProbeAccessV1(
    CouncilCompositionStewardCandidatesPrivateProbeV1 &probe) noexcept;

// Installs only a fully bound Council6 access set. The bridge obtains it by
// applying Council7 to the probe access above. This remains private and does
// not register a command, schema, planner edge, or hello capability.
bool InstallCouncilCompositionStewardCandidatesPrivateProbeV1(
    CouncilCompositionStewardCandidatesPrivateProbeV1 &probe,
    const xar::ck3_11906::CouncilCompositionStewardCandidatesEnvironmentV1
        &environment,
    const xar::ck3_11906::CouncilCompositionStewardCandidatesAccessV1
        &access) noexcept;

bool PrepareCouncilCompositionStewardCandidatesPrivateProbeV1(
    CouncilCompositionStewardCandidatesPrivateProbeV1 &probe,
    const xar::game::Snapshot &snapshot, std::uint64_t public_revision,
    std::uint64_t native_revision) noexcept;

// Fixed application-main executor admitted only by the private candidate.
// Typed reader unavailability still returns true to the mailbox.
bool ExecuteCouncilCompositionStewardCandidatesPrivateProbeV1(
    void *context,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

bool PublishCouncilCompositionStewardCandidatesPrivateProbeV1(
    CouncilCompositionStewardCandidatesPrivateProbeV1 &probe) noexcept;

bool PublishCouncilCompositionStewardCandidatesPrivateProbeFailureV1(
    CouncilCompositionStewardCandidatesPrivateProbeV1 &probe,
    xar::game::CouncilCompositionStewardCandidatesFailureV1 reason) noexcept;

std::string SerializeCouncilCompositionStewardCandidatesPrivateProbeV1(
    const CouncilCompositionStewardCandidatesPrivateProbeV1 &probe);

} // namespace xar::bridge
