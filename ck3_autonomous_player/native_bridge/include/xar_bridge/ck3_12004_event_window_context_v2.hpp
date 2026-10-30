#pragma once

#include "xar_bridge/ck3_12004_event_window_context.hpp"
#include "xar_bridge/ck3_12002_event_window_context_v2.hpp"

namespace xar::ck3_12004 {

ck3_12002::EventWindowGuiBindingsV2 BindEventWindowImage12004V2(
    std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004
