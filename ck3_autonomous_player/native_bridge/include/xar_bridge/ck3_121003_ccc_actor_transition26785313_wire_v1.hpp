#pragma once
#include "xar_bridge/ck3_121003_ccc_actor_transition26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
bool CccTransitionRequestShape267V1(const CccTransitionRequest267V1&)noexcept;
bool ParseCccTransitionRequest267V1(std::string_view,CccTransitionRequest267V1&)noexcept;
bool CccTransitionSourceShape267V1(const CccTransitionSource267V1&)noexcept;
bool CccTransitionProgressShape267V1(const CccTransitionProgress267V1&)noexcept;
std::string SerializeCccTransitionResult267V1(std::string_view,const CccTransitionResult267V1&);
}
