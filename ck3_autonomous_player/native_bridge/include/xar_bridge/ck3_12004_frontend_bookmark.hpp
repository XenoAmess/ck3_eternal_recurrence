#pragma once

#include "xar_bridge/frontend_bookmark_model_abi_v1.hpp"

#include <string_view>

namespace xar::ck3_12004 {

// The finite owner packet proves this profile independently of the older GUI
// revision. Build admission uses the executable identity selected by the adapter.
const ck3_11906::FrontendModelAbiV1 *BindFrontendBookmarkModel12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004
