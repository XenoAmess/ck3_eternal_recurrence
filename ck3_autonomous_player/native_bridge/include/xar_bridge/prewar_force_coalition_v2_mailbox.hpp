#pragma once

#include "xar_bridge/ck3_12002_commands.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12004_province.hpp"
#include "xar_bridge/prewar_force_coalition_v2.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12004 {

inline constexpr std::string_view kPrewarForceCoalitionV2PrivateStep12004 =
    kPrewarForceCoalitionV2Step12004;
inline constexpr std::string_view kPrewarForceCoalitionV2DomainKey12004 =
    kPrewarForceCoalitionV2Domain12004;
// Central capability publication still requires the feature and exact4 gate.
inline constexpr bool kPrewarForceCoalitionV2CapabilityAdvertised12004 = true;

// A fresh query owns every bundle until its exact mailbox ticket is terminal
// and reclaimed. MilitaryBindings retains a pointer to commands: moving even a
// not-yet-submitted query would invalidate that dependency.
struct PrewarForceCoalitionV2Mailbox12004 {
  ck3_12002::QueryMailboxEnvelope envelope{};
  PrewarForceCoalitionRequest12004 request{};
  ck3_12002::CommandBindings commands{};
  ck3_12002::ProvinceBindings provinces{};
  PrewarForceCoalitionV2Bindings12004 bindings{};
  ck3_12002::MilitaryWorldAccess world{};
  PrewarForceCoalitionV2Sample12004 observation{};
  std::uint64_t capture_epoch = 0;
  // The query sequence deliberately uses the same fresh namespace as ticket.
  std::uint64_t query_sequence = 0;
  std::uint32_t executor_invocations = 0;
  bool completed = false;
  ck3_11906::MainThreadQueryWaitResultV1 wait_result =
      ck3_11906::MainThreadQueryWaitResultV1::ticket_mismatch;
  ck3_11906::MainThreadQueryReclaimResultV1 reclaim_result =
      ck3_11906::MainThreadQueryReclaimResultV1::not_terminal;
  std::string failure;

  PrewarForceCoalitionV2Mailbox12004() = default;
  PrewarForceCoalitionV2Mailbox12004(const PrewarForceCoalitionV2Mailbox12004 &) = delete;
  PrewarForceCoalitionV2Mailbox12004 &operator=(
      const PrewarForceCoalitionV2Mailbox12004 &) = delete;
  PrewarForceCoalitionV2Mailbox12004(PrewarForceCoalitionV2Mailbox12004 &&) = delete;
  PrewarForceCoalitionV2Mailbox12004 &operator=(
      PrewarForceCoalitionV2Mailbox12004 &&) = delete;
};

bool IsPrewarForceCoalitionV2Step12004(std::string_view step) noexcept;

bool ExecutePrewarForceCoalitionV2Mailbox12004(
    void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

// Returns a bare domain DTO only after two complete equal samples, Finish,
// completed wait and exact-ticket reclaim. The caller supplies a fresh query
// with caller-owned, admitted .4 bundles; no capability is registered here.
bool RunPrewarForceCoalitionV2Mailbox12004(
    PrewarForceCoalitionV2Mailbox12004 &query,
    std::string &serialized, std::string &failure) noexcept;

// Builds the actual .4 bundles in their final query addresses. A typed request
// is intentional: the central protocol parser remains the single JSON parser.
// Successful command_result includes a separate execution_receipt constructed
// from this query's actual envelope ticket and execution stamp, not domain JSON.
bool HandlePrewarForceCoalitionV2_12004(
    const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t native_revision,
    const PrewarForceCoalitionRequest12004 &request,
    std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept;

} // namespace xar::ck3_12004
