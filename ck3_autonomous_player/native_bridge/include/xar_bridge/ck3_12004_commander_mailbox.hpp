#pragma once

#include "xar_bridge/ck3_12003_commander_mailbox.hpp"

namespace xar::ck3_12004 {

// The caller supplies the observation obtained from the actual .4 binder.
// The existing six-argument .3 publisher remains unchanged.
std::string SerializeArmyCommanderCandidates12004(
    const ck3_12003::ArmyCommanderCandidatesSnapshot &observation,
    ck3_12003::CommanderCandidatesReadResult read_result,
    std::uint64_t query_sequence, std::uint64_t snapshot_revision,
    std::int32_t date_raw, std::string_view step);

} // namespace xar::ck3_12004
