#pragma once
#include "xar_bridge/ck3_121003_ccc_actor_transition26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_ccc_event26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_ccc_decision26785313_owner_v1.hpp"
namespace xar::ck3_121003::build26785313 {
inline bool VerifyCccImage267V1(std::uintptr_t image)noexcept{return VerifyCccRoleImage267V1(image)&&VerifyCccEventImage267V1(image)&&VerifyCccDecisionImage267V1(image);}
}
