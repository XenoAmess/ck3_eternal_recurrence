#pragma once

#include "xar_bridge/ck3_12003_confucian_assembly_predicates.hpp"

namespace xar::ck3_12004::confucian_assembly {

// Existing caller-owned reader/DTO; independent exact .4 image selection.
using Bindings = ck3_12003::confucian_assembly::Bindings;
Bindings BindImage(std::uintptr_t image_base,
                   std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004::confucian_assembly
