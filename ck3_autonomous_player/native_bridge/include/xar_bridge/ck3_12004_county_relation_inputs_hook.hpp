#pragma once
#include <cstdint>
#include <string_view>
namespace xar::ck3_12004 {
bool CountyRelationInputsHookInstalled12004() noexcept;
bool InstallCountyRelationInputsHook12004(std::uintptr_t image_base,
    std::string_view executable_sha256, bool primary_thread_suspended) noexcept;
}
