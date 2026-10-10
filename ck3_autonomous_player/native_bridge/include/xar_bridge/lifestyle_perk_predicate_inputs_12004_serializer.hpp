#pragma once

#include "xar_bridge/ck3_12004_stock_perk_legality.hpp"

#include <string>

namespace xar::ck3_12004::lifestyle {

// The mailbox guard qualifies the copied child packet independently of native
// can_select. Keep each copied prefix, tail and trace plane for inspection.
inline void FinishLifestylePerkPredicateSourceMailbox12004(
    StockPerkLegalityResultV1 &result, bool accepted) noexcept {
  if (!result.source_packet) return;
  auto &packet = *result.source_packet;
  packet.read_frame.mailbox_after_accepted = accepted;
  if (accepted) return;
  packet.read_frame.caller_snapshot_confirmed = false;
  packet.value.reset();
  try {
    packet.unavailable_reason = "formal_mailbox_after_guard_rejected";
  } catch (...) {
    packet.unavailable_reason.clear();
  }
}

// Append inside the existing result object after its legacy members. The
// source packet serializer owns nulls, escaping and the source-only keyset.
inline void AppendLifestylePerkPredicateSourceSibling12004(
    std::string &output, const StockPerkLegalityResultV1 &result) {
  output += ",\"lifestyle_perk_predicate_source_12004\":";
  output += SerializeStockPerkLegalitySourcePacket12004V1(result.source_packet);
}

} // namespace xar::ck3_12004::lifestyle
