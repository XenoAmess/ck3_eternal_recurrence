#pragma once

#include "xar_bridge/ck3_12003_holy_order_hire_action.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"

namespace xar::ck3_12004::religion::holy_order {

// Caller-owned software DTOs; these aliases do not accept an old native image.
using Bindings = ck3_12003::religion::holy_order::Bindings;
using HireActionBindings = ck3_12003::religion::holy_order::HireActionBindings;
using HireActionResult = ck3_12003::religion::holy_order::HireActionResult;

Bindings BindPlayerHolyOrderImage12004(std::uintptr_t module_base,
    std::string_view executable_sha256) noexcept;
HireActionBindings BindHolyOrderHireActionImage12004(std::uintptr_t module_base,
    std::string_view executable_sha256) noexcept;

// Fresh native .4 results retain the existing structure and action semantics.
std::string SerializeHolyOrderHireResult12004(const HireActionResult &,
    std::string_view request_id, std::uint64_t command_sequence,
    std::uint64_t snapshot_revision, std::int32_t date_raw,
    const game::AdapterDescriptor &);

} // namespace xar::ck3_12004::religion::holy_order
