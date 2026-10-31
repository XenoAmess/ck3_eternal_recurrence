#pragma once

#include "xar_bridge/family_heir_betrothal_materializer_12004.hpp"

namespace xar::bridge {

using FamilyChildDefaultPreparedCopy12004 = FamilyHeirBetrothalPreparedCopy12004;

// Copies the actual DEFAULT private context. This API has no setter port.
// Native raw options/lineality and CanSend remain data; actual sender policy
// separately enforces require-off after observing that data.
FamilyRulerMaterializeStatus12004 MaterializeFamilyChildDefaultContext12004(
    const ck3_12002::ContextBindings &,
    const FamilyRulerContextAccess12004 &,
    const FamilyMarriageOutgoingRequestV2 &,
    FamilyChildDefaultPreparedCopy12004 &) noexcept;

} // namespace xar::bridge
