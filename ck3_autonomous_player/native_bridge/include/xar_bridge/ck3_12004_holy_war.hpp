#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/ordinary_holy_war_cb_cost_v1.hpp"

namespace xar::ck3_12004 {

// These return existing software DTOs with actual .4 native bindings. The
// declaration factory supplies only the selected-context readonly fields;
// the overall WAR factory owns command and send fields and merges them once.
ck3_12002::DeclarationsBindings BindOrdinaryHolyWarDeclarationsImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
ck3_12002::OrdinaryHolyWarCbCostBindingsV1 BindOrdinaryHolyWarCbCostImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004

namespace xar::game {
// Implemented by the shared adapter owner; borrow its already composed .4
// declaration bindings rather than configuring the same callback slots again.
const ck3_12002::DeclarationsBindings *BorrowOrdinaryHolyWarDeclarations12004(
    const GameAdapter &adapter) noexcept;
} // namespace xar::game
