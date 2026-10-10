#pragma once

#include "xar_bridge/religion_rite_governance12002_clergy_mailbox.hpp"
#include <string>
#include <string_view>

namespace xar::ck3_12002 {
std::string SerializeActualClergyMode0QueryForNewCase12004(
    const PlayerClergyAppointmentMailboxContext12002 &completed_current_query,
    std::string_view request_id);
std::string SerializeActualClergyQueryFrameReceiptForNewCase12004(
    const PlayerClergyAppointmentMailboxContext12002 &completed_current_query);
} // namespace xar::ck3_12002
