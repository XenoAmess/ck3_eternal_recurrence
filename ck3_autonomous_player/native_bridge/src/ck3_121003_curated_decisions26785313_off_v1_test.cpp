#include "xar_bridge/ck3_121003_curated_decisions26785313_raw_v1.hpp"
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <iostream>
using namespace xar::ck3_121003::build26785313;
int main(){ReadonlyBindings b;CuratedDecisionRaw267V1 out;std::string reason;xar::ck3_1210::CoreSnapshotPrefix core;CuratedDecisionScene267V1 scene;assert(!VerifyCuratedDecisionImage267V1(0));assert(!ReadCuratedDecisionRaw267V1(b,core,scene,1,out,reason));assert(reason=="current_curated_decisions_default_off");for(std::size_t i=0;i<4;++i){const auto call=CallCuratedDecisionRaw267V1(b,core,scene,1,out,static_cast<CuratedDecisionAction267V1>(i),{});assert(!call.effect_entered&&call.cleanup_known&&call.status==CuratedDecisionRawCallStatus267V1::refused);}std::cout<<"default OFF no native read/effect\n";}
