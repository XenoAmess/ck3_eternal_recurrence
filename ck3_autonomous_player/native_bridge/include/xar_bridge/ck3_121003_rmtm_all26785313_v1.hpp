#pragma once
#include "xar_bridge/ck3_121003_rmtm_actor_transition26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_rmtm_event26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_rmtm_decision26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_rmtm_observation26785313_owner_v1.hpp"
namespace xar::ck3_121003::build26785313 {
inline bool VerifyRmtmImage267V1([[maybe_unused]]std::uintptr_t image)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_V1
 return VerifyRmtmRoleImage267V1(image)&&VerifyRmtmEventImage267V1(image)&&VerifyRmtmDecisionImage267V1(image)&&VerifyRmtmObservationImage267V1(image);
#else
 return false;
#endif
}
}
