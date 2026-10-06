#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12003_commander.hpp"
#include "xar_bridge/public_unit_id.hpp"

#include <string>
#include <string_view>

namespace xar::ck3_12003 {

inline constexpr std::string_view kArmyCommanderCandidatesCapability =
    "game.command.query-army-commander-candidates-v1-for-army-N";
inline constexpr std::string_view kArmyCommanderCandidatesForTargetCapability =
    "game.command.query-army-commander-candidates-v1-for-army-N-at-province-P";
inline constexpr std::string_view kArmyCommanderCandidatesStepPrefix =
    "query-army-commander-candidates-v1-for-army-";

inline bool ParseArmyCommanderCandidatesStep(std::string_view step,
                                            std::int32_t &army_id) noexcept {
  army_id = -1;
  return step.starts_with(kArmyCommanderCandidatesStepPrefix) &&
      game::ParsePublicCUnitIdV1(
          step.substr(kArmyCommanderCandidatesStepPrefix.size()), army_id);
}

// Optional target route is independent of the legacy no-target parser.
inline bool ParseArmyCommanderCandidatesRequest(
    std::string_view step, std::int32_t &army_id,
    std::optional<std::int32_t> &target_province_id) noexcept {
  army_id = -1;
  target_province_id.reset();
  if (!step.starts_with(kArmyCommanderCandidatesStepPrefix)) return false;
  const auto tail = step.substr(kArmyCommanderCandidatesStepPrefix.size());
  constexpr std::string_view marker = "-at-province-";
  const auto separator = tail.find(marker);
  if (separator == std::string_view::npos)
    return ParseArmyCommanderCandidatesStep(step, army_id);
  std::int32_t subject = -1, province = -1;
  // The shared parser supplies only canonical signed32 decimal-token syntax;
  // Province namespace semantics remain positive ID and native resolution.
  if (!game::ParsePublicCUnitIdV1(tail.substr(0, separator), subject) ||
      !game::ParsePublicCUnitIdV1(tail.substr(separator + marker.size()), province) ||
      province <= 0) return false;
  army_id = subject;
  target_province_id = province;
  return true;
}

struct ArmyCommanderMailboxContext {
  ck3_12002::QueryMailboxEnvelope envelope{};
  std::uintptr_t image_base = 0;
  std::int32_t army_id = -1;
  ArmyCommanderCandidatesSnapshot observation{};
  CommanderCandidatesReadResult read_result =
      CommanderCandidatesReadResult::unavailable;
  bool completed = false;
  std::optional<std::int32_t> target_province_id;
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
