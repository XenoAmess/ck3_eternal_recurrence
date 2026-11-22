#pragma once
#include "xar_bridge/ck3_121003_ted_actor_transition26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
bool TedTransitionRequestShape267V1(const TedTransitionRequest267V1&)noexcept;
bool ParseTedTransitionRequest267V1(std::string_view,TedTransitionRequest267V1&)noexcept;
bool TedTransitionSourceShape267V1(const TedTransitionSource267V1&)noexcept;
bool TedTransitionProgressShape267V1(const TedTransitionProgress267V1&)noexcept;
std::string SerializeTedTransitionResult267V1(std::string_view,const TedTransitionResult267V1&);
}
