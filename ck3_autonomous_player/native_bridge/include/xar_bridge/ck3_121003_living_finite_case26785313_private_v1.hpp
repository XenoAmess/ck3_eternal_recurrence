#pragma once
#include "xar_bridge/ck3_121003_living_ui26785313_v1.hpp"
namespace xar::ck3_121003::build26785313::living_inventory_private {
enum class LivingFinitePhase267V1 {initial,tutorial_dispatched,management,first_review,cancel_dispatched,
 cancel_conserved,preview_dispatched,review,confirm_dispatched,settled,management_close_dispatched};
struct LivingFiniteCase267V1 {
 bool bound=false,unknown=false;
 LivingInventoryFrame267V1 initial;
 std::uint32_t target=0xFFFFFFFFU,review_material=0xFFFFFFFFU;
 std::int32_t review_instance=0,last_management_instance=0;
 LivingFinitePhase267V1 phase=LivingFinitePhase267V1::initial;
 LivingUiAction267V1 preview=LivingUiAction267V1::feed_common;
 std::optional<LivingInventorySource267V1>cancel_before;
 std::vector<std::pair<std::int32_t,LivingUiAction267V1>>spent;
 unsigned common_previews=0,confirmed_mask=0;
};

bool LivingFiniteSameOwner267V1(const LivingFiniteCase267V1&,const LivingInventoryFrame267V1&);
bool LivingFiniteBind267V1(LivingFiniteCase267V1&,const LivingInventoryFrame267V1&,const LivingInventorySource267V1&);
bool LivingFiniteObserve267V1(LivingFiniteCase267V1&,const LivingInventoryFrame267V1&,const LivingEventScopeData267V1&,const LivingInventorySource267V1&);
bool LivingFiniteMayConsume267V1(const LivingFiniteCase267V1&,LivingUiAction267V1,const LivingEventScopeData267V1&);
bool LivingFiniteClaim267V1(LivingFiniteCase267V1&,LivingUiAction267V1,const LivingEventScopeData267V1&);
void LivingFiniteUnknown267V1(LivingFiniteCase267V1&);
}
