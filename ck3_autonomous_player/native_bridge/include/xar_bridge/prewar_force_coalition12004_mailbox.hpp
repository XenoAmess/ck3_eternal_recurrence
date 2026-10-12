#pragma once

#include "xar_bridge/ck3_12002_commands.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12004_province.hpp"
#include "xar_bridge/prewar_force_coalition12004.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12004 {

inline constexpr std::string_view kPrewarForceCoalitionPrivateStep12004 =
    kPrewarForceCoalitionStep12004;
inline constexpr std::string_view kPrewarForceCoalitionDomainKey12004 =
    kPrewarForceCoalitionDomain12004;
inline constexpr bool kPrewarForceCoalitionCapabilityAdvertised12004 = false;

// A fresh query owns every bundle until its exact mailbox ticket is terminal
// and reclaimed. MilitaryBindings retains a pointer to commands: moving even a
// not-yet-submitted query would invalidate that dependency.
struct PrewarForceCoalitionMailbox12004 {
  ck3_12002::QueryMailboxEnvelope envelope{};
  PrewarForceCoalitionRequest12004 request{};
  ck3_12002::CommandBindings commands{};
  ck3_12002::ProvinceBindings provinces{};
  PrewarForceCoalitionBindings12004 bindings{};
  ck3_12002::MilitaryWorldAccess world{};
  PrewarForceCoalitionSample12004 observation{};
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

  PrewarForceCoalitionMailbox12004() = default;
  PrewarForceCoalitionMailbox12004(const PrewarForceCoalitionMailbox12004 &) = delete;
  PrewarForceCoalitionMailbox12004 &operator=(
      const PrewarForceCoalitionMailbox12004 &) = delete;
  PrewarForceCoalitionMailbox12004(PrewarForceCoalitionMailbox12004 &&) = delete;
  PrewarForceCoalitionMailbox12004 &operator=(
      PrewarForceCoalitionMailbox12004 &&) = delete;
};

bool IsPrewarForceCoalitionPrivateStep12004(std::string_view step) noexcept;

bool ExecutePrewarForceCoalitionMailbox12004(
    void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

// Returns a bare domain DTO only after two complete equal samples, Finish,
// completed wait and exact-ticket reclaim. The caller supplies a fresh query
// with caller-owned, admitted .4 bundles; no capability is registered here.
bool RunPrewarForceCoalitionMailbox12004(
    PrewarForceCoalitionMailbox12004 &query,
    std::string &serialized, std::string &failure) noexcept;

// Builds the actual .4 bundles in their final query addresses. A typed request
// is intentional: the central protocol parser remains the single JSON parser.
// Successful command_result includes a separate execution_receipt constructed
// from this query's actual envelope ticket and execution stamp, not domain JSON.
bool HandlePrewarForceCoalitionPrivate12004(
    const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t native_revision,
    const PrewarForceCoalitionRequest12004 &request,
    std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept;

} // namespace xar::ck3_12004
