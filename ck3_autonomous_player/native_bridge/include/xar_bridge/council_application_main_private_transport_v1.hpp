#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/council_application_main_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kCouncilPrivateQueryStepV1 =
    "private-query-council-composition-candidates-v1";
inline constexpr std::string_view kCouncilPrivateAssignStepV1 =
    "private-assign-councillor-v1";
inline constexpr std::string_view kCouncilPrivateReceiptStepV1 =
    "private-query-assign-councillor-receipt-v1";
inline constexpr std::string_view kCouncilPrivateStatusStepV1 =
    "private-council-application-main-status-v1";

// This is an opt-in candidate transport. It does not add a GameAdapter
// capability or a public command. The caller must compile and route it
// explicitly for controlled acceptance.
struct CouncilApplicationMainPrivateTransportV1 {
  ck3_11906::MainThreadQueryMailboxV1 *mailbox = nullptr;
  ck3_11906::Bindings bindings{};
  CouncilApplicationMainStateV1 shared{};
  CouncilApplicationMainContextV1 context{};
  CouncilApplicationMainContextV1 completed{};
  ck3_11906::CouncilAssignCouncillorNativeSubmitAdapterV1 submit_adapter{};
  game::Snapshot expected_snapshot{};
  std::string expected_snapshot_id;
  bool configured = false;
  bool in_flight = false;
  bool has_completed = false;
};

bool IsCouncilApplicationMainPrivateStepV1(std::string_view step) noexcept;

// The action callback is deliberately absent until the four native final
// gates are bound. `action_admitted` is a separate controlled-candidate switch;
// a linked callback alone never opens submission.
bool ConfigureCouncilApplicationMainPrivateTransportV1(
    CouncilApplicationMainPrivateTransportV1 &transport,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const ck3_11906::Bindings &bindings, std::uintptr_t module_base,
    bool action_admitted = false,
    EvaluateCouncilAssignCouncillorNativeGatesV1 evaluate_action_gates =
        nullptr,
    void *action_gate_context = nullptr) noexcept;

void PollCouncilApplicationMainPrivateTransportV1(
    CouncilApplicationMainPrivateTransportV1 &transport) noexcept;

// Returns one protocol command_result JSON frame. A queued request returns a
// typed pending response; its status is retrieved on a later worker turn.
// Polling never waits on or cancels the application-main executor.
std::string ExecuteCouncilApplicationMainPrivateStepV1(
    CouncilApplicationMainPrivateTransportV1 &transport,
    std::string_view step, std::string_view payload,
    std::string_view protocol_request_id,
    const game::Snapshot &published_snapshot,
    std::uint64_t published_revision);

} // namespace xar::bridge
