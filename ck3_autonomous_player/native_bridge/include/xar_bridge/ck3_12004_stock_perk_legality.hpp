#pragma once

#include "xar_bridge/ck3_12004_lifestyle.hpp"

#include <optional>
#include <string>

namespace xar::ck3_12004::lifestyle {

// Private sibling source facts from the existing current stock-perk query.
// An absent observation serializes to JSON null. This never changes can_select.
std::string SerializeStockPerkLegalitySourcePacket12004V1(
    const std::optional<StockPerkLegalitySourcePacketV1> &);


std::string SerializeStockPerkRawTargetsSource12004V1(
    const StockPerkLegalityResultV1 &);
void FinishStockPerkRawTargetsSourceMailbox12004V1(
    StockPerkLegalityResultV1 &, bool actual_finish_accepted) noexcept;
} // namespace xar::ck3_12004::lifestyle
