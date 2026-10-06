#pragma once

#include "xar_bridge/ck3_12004_family.hpp"
#include "xar_bridge/ck3_12002_family_subject.hpp"

namespace xar::ck3_12004 {
#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)

// Existing software reader contract, independently bound to the actual .4
// family/value inputs and its source-proved inline child predicate mirror.
ck3_12002::FamilySubjectBindings BindFamilySubjectImage(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

#endif
} // namespace xar::ck3_12004
