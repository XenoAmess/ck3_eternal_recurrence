#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12003_title_holder.hpp"

namespace xar::ck3_12004 {

// Reuse the software DTO and ck3_12003::ReadTitleHolderV1. This factory binds
// native addresses only for the actual .4 executable.
ck3_12003::TitleHolderBindingsV1 BindTitleHolderImageV1(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004
