#pragma once
#include "xar_bridge/ck3_121003_rmtm_actor_transition26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
bool RmtmTransitionRequestShape267V1(const RmtmTransitionRequest267V1&)noexcept;
bool ParseRmtmTransitionRequest267V1(std::string_view,RmtmTransitionRequest267V1&)noexcept;
bool RmtmTransitionSourceShape267V1(const RmtmTransitionSource267V1&)noexcept;
bool RmtmTransitionProgressShape267V1(const RmtmTransitionProgress267V1&)noexcept;
std::string SerializeRmtmTransitionResult267V1(std::string_view,const RmtmTransitionResult267V1&);
}
