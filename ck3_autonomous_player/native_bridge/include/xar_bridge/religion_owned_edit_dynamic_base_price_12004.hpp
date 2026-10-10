#pragma once

#include "xar_bridge/religion_owned_edit_base_price_2c64710_12004.hpp"
#include "xar_bridge/piety_price_numeric_31d9930_dynamic_12004.hpp"
#include "xar_bridge/piety_price_numeric_31df3b0_dynamic_12004.hpp"

namespace xar::ck3_12004::piety_price_raw_inputs {

// These are typed source-model input providers. Callers cannot substitute an
// EAX function or overall quotation for either source-owned scalar adapter.
struct OwnedEditDynamicBasePriceBindings12004 {
  OwnedEditReadAccess12004 access;
  Numeric31D9930DynamicBindings12004 first;
  Numeric31DF3B0DynamicBindings12004 second;
  std::size_t maximum_entries =
      construction_owner_mode3::kConstructionCollectionCopyBoundV1;
};

// Bind22f/23f's real dynamic software adapters into the frozen14e parent.
// Owned typed contexts remain alive for the entire synchronous invocation.
// Read access comes from this actual input; child resolver/nullable operands
// come from the corresponding binding. Missing reached values stay unknown.
// The caller guards actual draft/Rite/frame identity; revision is a carrier.
// No native function/getter/provider method is executed.
OwnedEditBasePrice12004 ReadOwnedEditDynamicBasePrice2C6471012004(
    const OwnedEditDynamicBasePriceBindings12004 &, std::uintptr_t draft,
    std::uintptr_t current_rite,
    std::uint64_t unchanged_snapshot_revision) noexcept;

} // namespace xar::ck3_12004::piety_price_raw_inputs
