#pragma once

#include "xar_bridge/ck3_12004_stock_perk_legality.hpp"

#include <string>

namespace xar::ck3_12004::lifestyle {

// The owning producer preserves copied raw planes when the real mailbox
// finish guard rejects their current-query admission.
inline void FinishLifestylePerkTriggerFrontierMailbox12004(
    StockPerkLegalityResultV1 &result, bool accepted) noexcept {
  FinishStockPerkRawTargetsSourceMailbox12004V1(result, accepted);
}

// The producer owns the independent frontier schema and nullable body.
inline void AppendLifestylePerkTriggerFrontierSibling12004(
    std::string &output, const StockPerkLegalityResultV1 &result) {
  output += ",\"lifestyle_perk_trigger_frontier_12004\":";
  output += SerializeStockPerkRawTargetsSource12004V1(result);
}

} // namespace xar::ck3_12004::lifestyle
