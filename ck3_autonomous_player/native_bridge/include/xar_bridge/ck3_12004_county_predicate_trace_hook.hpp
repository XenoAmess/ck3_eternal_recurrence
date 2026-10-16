#pragma once
#include "xar_bridge/ck3_12004_county_predicate_trace_context.hpp"
#include <cstdint>
#include <string_view>
namespace xar::ck3_12004 {
bool CountyPredicateTraceHookInstalled12004() noexcept;
bool InstallCountyPredicateTraceHook12004(std::uintptr_t image_base,
    std::string_view executable_sha256, bool primary_thread_suspended) noexcept;
}
