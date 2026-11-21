#pragma once
#include "xar_bridge/ck3_121003_fullscreen_event26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_date_advance26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
inline bool DateTimeGateAllowsArm267V1(RuntimeEventTimeGate267V1 gate,DateAdvanceResult267V1& result)noexcept{
 if(gate==RuntimeEventTimeGate267V1::clear)return true;
 result.status=gate==RuntimeEventTimeGate267V1::indeterminate?DateAdvanceStatus267V1::indeterminate:gate==RuntimeEventTimeGate267V1::blocked?DateAdvanceStatus267V1::rejected:DateAdvanceStatus267V1::unavailable;
 result.access_cleanup_unknown=gate==RuntimeEventTimeGate267V1::indeterminate;return false;
}
}
