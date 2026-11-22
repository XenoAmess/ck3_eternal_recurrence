#ifdef NDEBUG
#undef NDEBUG
#endif
#include "xar_bridge/ck3_121003_courtier_configuration26785313_raw_v1.hpp"
#include <cassert>
#include <iostream>
using namespace xar::ck3_121003::build26785313;
int main(){ReadonlyBindings b;xar::ck3_1210::CoreSnapshotPrefix core;CourtierConfigurationScene267V1 scene;CourtierConfigurationRaw267V1 raw;std::string reason;assert(!ReadCourtierConfigurationRaw267V1(b,core,scene,1,CourtierProduct267V1::main,CourtierSetting267V1::choose_female,raw,reason));assert(reason=="current_courtier_configuration_default_off");const auto call=ExecuteCourtierControlRaw267V1(b,core,scene,1,raw);assert(!call.effect_entered&&call.cleanup_known&&call.status==LetterRawCallStatus267V1::unavailable);std::cout<<"XQOL threshold defaultOFF no native read/scope/execute\n";}
