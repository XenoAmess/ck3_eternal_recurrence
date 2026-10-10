#pragma once

#include "xar_bridge/person_installed_transfer_stage_12004.hpp"

namespace xar::ck3_12004 {

// One process-lifetime domain for actual transfer and consumed-getter events.
// It never resets while this DLL owns historical records. Capture/journal
// ordinal counters remain separate and must not be used as event timestamps.
PersonInstalledTransferEvent12004 NextPersonNaturalLineageEvent12004() noexcept;

} // namespace xar::ck3_12004
