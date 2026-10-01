#pragma once

#include "xar_bridge/ck3_12002_council_runtime.hpp"
#include "xar_bridge/game_adapter.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12002 {

// Worker-owned storage remains alive until the application-main ticket is
// terminal and reclaimed. The pending helper ACK survives later requests.
struct CouncilTransportState12002 {
  ck3_11906::MainThreadQueryMailboxV1* mailbox = nullptr;
  CoreBindings core{};
  CouncilMailboxState12002 shared{};
  CouncilMailboxContext12002 context{};
  CouncilMailboxContext12002 completed{};
  game::Snapshot expected_snapshot{};
  std::string expected_snapshot_id;
  std::uint64_t expected_revision = 0;
  bool configured = false;
  bool action_enabled = false;
  bool gate_query_enabled = false;
  bool in_flight = false;
  bool has_completed = false;
};

bool IsCouncilPrivate12002(std::string_view step) noexcept;

// Binds only the frozen image; this call performs no native reads or calls.
// Submission and the read-only final-gate query retain separate opt-in flags.
bool ConfigureCouncilTransport12002(
    CouncilTransportState12002& state,
    ck3_11906::MainThreadQueryMailboxV1& mailbox,
    std::uintptr_t module_base, std::string_view executable_sha256,
    bool action_enabled = false, bool gate_query_enabled = false) noexcept;

void PollCouncilTransport12002(CouncilTransportState12002& state) noexcept;

// A queued operation returns the existing pending command_result immediately.
// Status consumes a later completed v1 envelope. No wait or cancellation is
// performed here, and the public full Snapshot is never read on this worker.
// Returns false with a failure reason when the step cannot be accepted.
bool HandleCouncilPrivate12002(
    const game::GameAdapter& adapter,
    ck3_11906::MainThreadQueryMailboxV1& mailbox,
    const game::Snapshot& published, std::uint64_t revision,
    std::string_view step, std::string_view payload,
    std::string_view request_id, CouncilTransportState12002& state,
    std::string& serialized, std::string& failure) noexcept;

} // namespace xar::ck3_12002
