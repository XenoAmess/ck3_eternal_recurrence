#pragma once

#include "xar_bridge/ck3_12002_family.hpp"
#include "xar_bridge/family_heir_betrothal_materializer_12004.hpp"

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
namespace xar::bridge {

// The actual private Prepared value has the same five roles, complete authored
// option bank and non-null effective lineality. This alias does not assert
// natural child identity; its caller must supply the real child observation.
using FamilyChildMatrilinealPreparedCopy12004 = FamilyHeirBetrothalPreparedCopy12004;

FamilyRulerMaterializeStatus12004 MaterializeFamilyChildMatrilinealContext12004(
    const ck3_12002::FamilyBindings &,
    const FamilyRulerContextAccess12004 &,
    const FamilyMarriageOutgoingRequestV2 &,
    FamilyChildMatrilinealPreparedCopy12004 &) noexcept;

} // namespace xar::bridge
#endif
