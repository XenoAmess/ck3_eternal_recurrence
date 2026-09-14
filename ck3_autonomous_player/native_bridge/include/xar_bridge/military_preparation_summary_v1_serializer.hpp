#pragma once

#include "xar_bridge/military_preparation_summary_v1.hpp"

#include <string>

namespace xar::bridge {

std::string SerializeMilitaryPreparationSummaryV1(
    const MilitaryPreparationSummaryResultV1 &result);

} // namespace xar::bridge
