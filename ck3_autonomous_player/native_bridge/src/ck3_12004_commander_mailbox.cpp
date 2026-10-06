#include "xar_bridge/ck3_12004_commander_mailbox.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_army_support.hpp"

#include <utility>

namespace xar::ck3_12004 {
namespace {
void ReplaceGetter(std::string &serialized, std::string_view old_rva,
                   std::string_view actual_rva) {
  const std::string old_field =
      std::string("\"native_getter_rva\":\"") + std::string(old_rva) + '"';
  const std::string actual_field =
      std::string("\"native_getter_rva\":\"") + std::string(actual_rva) + '"';
  std::size_t at = 0;
  while ((at = serialized.find(old_field, at)) != std::string::npos) {
    serialized.replace(at, old_field.size(), actual_field);
    at += actual_field.size();
  }
}
} // namespace

std::string SerializeArmyCommanderCandidates12004(
    const ck3_12003::ArmyCommanderCandidatesSnapshot &observation,
    ck3_12003::CommanderCandidatesReadResult read_result,
    std::uint64_t query_sequence, std::uint64_t snapshot_revision,
    std::int32_t date_raw, std::string_view step) {
  auto serialized = ck3_12003::SerializeArmyCommanderCandidates(
      observation, read_result, query_sequence, snapshot_revision, date_raw, step);
  // The complete local getter maps preserve the software DTO and native
  // receiver contracts. Change only the three actual getter metadata fields.
  ReplaceGetter(serialized, "0x24AA940", kCommanderLandMovementRateRvaText12004);
  ReplaceGetter(serialized, "0x24AAC00", kCommanderNavalMovementRateRvaText12004);
  ReplaceGetter(serialized, "0x24AB5C0", kCommanderCurrentEdgeMovementRateRvaText12004);
  return game::Render12004BuildIdentity(
      std::move(serialized), game::Ck3_12004AdapterDescriptor());
}

} // namespace xar::ck3_12004
