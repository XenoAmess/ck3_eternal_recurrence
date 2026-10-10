#pragma once

#include "xar_bridge/person_transfer_postimage_capture_12004.hpp"

#include <string>

namespace xar::ck3_12004 {

// Serializes the already owned same-occurrence copies only. Raw64 payloads
// use exact hexadecimal strings; opaque rows retain their ordered 16 bytes.
std::string SerializePersonTransferPhysicalPostimage12004(
    const PersonTransferPhysicalPostimage12004 &);

} // namespace xar::ck3_12004
