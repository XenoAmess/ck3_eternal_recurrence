#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12003_commander.hpp"
#include "xar_bridge/public_unit_id.hpp"

#include <string>
#include <string_view>

namespace xar::ck3_12003 {

inline constexpr std::string_view kArmyCommanderCandidatesCapability =
    "game.command.query-army-commander-candidates-v1-for-army-N";
inline constexpr std::string_view kArmyCommanderCandidatesStepPrefix =
    "query-army-commander-candidates-v1-for-army-";

inline bool ParseArmyCommanderCandidatesStep(std::string_view step,
                                            std::int32_t &army_id) noexcept {
  army_id = -1;
  return step.starts_with(kArmyCommanderCandidatesStepPrefix) &&
      game::ParsePublicCUnitIdV1(
          step.substr(kArmyCommanderCandidatesStepPrefix.size()), army_id);
}

struct ArmyCommanderMailboxContext {
  ck3_12002::QueryMailboxEnvelope envelope{};
  std::uintptr_t image_base = 0;
  std::int32_t army_id = -1;
  ArmyCommanderCandidatesSnapshot observation{};
  CommanderCandidatesReadResult read_result =
      CommanderCandidatesReadResult::unavailable;
  bool completed = false;
};

bool ExecuteArmyCommanderCandidatesMailbox(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

// Returns the standard command.result object, including its native payload.
std::string SerializeArmyCommanderCandidates(
    const ArmyCommanderCandidatesSnapshot &observation,
    CommanderCandidatesReadResult read_result, std::uint64_t query_sequence,
    std::uint64_t snapshot_revision, std::int32_t date_raw,
    std::string_view step);

} // namespace xar::ck3_12003
