#pragma once

#include "xar_bridge/ck3_12004_family.hpp"
#include "xar_bridge/ck3_12002_family_ranked.hpp"

namespace xar::ck3_12004 {
#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)

// Reuses the ranked software contract with independently proven actual4
// native callbacks and owner identities. No earlier image binder is invoked.
ck3_12002::FamilyRankedBindings BindFamilyRankedImage(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

#endif
} // namespace xar::ck3_12004
