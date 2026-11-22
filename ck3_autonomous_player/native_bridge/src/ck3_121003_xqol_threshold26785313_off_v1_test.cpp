#ifdef NDEBUG
#undef NDEBUG
#endif
#include "xar_bridge/ck3_121003_xqol_threshold26785313_raw_v1.hpp"
#include <cassert>
#include <iostream>
using namespace xar::ck3_121003::build26785313;
int main(){ReadonlyBindings b;xar::ck3_1210::CoreSnapshotPrefix core;XqolThresholdScene267V1 scene;XqolThresholdRaw267V1 raw;std::string reason;assert(!ReadXqolThresholdRaw267V1(b,core,scene,1,20,raw,reason));assert(reason=="current_xqol_threshold_default_off");const auto call=SetXqolThresholdRaw267V1(b,core,scene,1,raw);assert(!call.effect_entered&&call.cleanup_known&&call.status==LetterRawCallStatus267V1::unavailable);std::cout<<"XQOL threshold defaultOFF no native read/scope/execute\n";}
