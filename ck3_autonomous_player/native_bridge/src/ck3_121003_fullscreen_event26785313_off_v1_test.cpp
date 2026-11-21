#if defined(NDEBUG)
#undef NDEBUG
#endif
#include "xar_bridge/ck3_121003_fullscreen_event26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_date_time_gate26785313_v1.hpp"
#include <cassert>
#include <iostream>
using namespace xar::ck3_121003::build26785313;
int main(){ReadonlyBindings b;FullscreenEventBindings267V1 image;xar::ck3_1210::CoreSnapshotPrefix core;FullscreenEventScene267V1 scene;FullscreenEventRaw267V1 raw;std::string reason;assert(!ReadFullscreenEventRaw267V1(b,image,core,scene,1,raw,reason));assert(reason=="current_fullscreen_event_default_off"&&!raw.native_read_entered&&raw.cleanup_known);const auto call=AcknowledgeKnownFullscreenEventRaw267V1(b,image,core,scene,1,raw);assert(call.status==FullscreenEventRawCallStatus267V1::unavailable&&!call.effect_entered&&call.cleanup_known);assert(ReadRuntimeEventTimeGate267V1(b,core)==RuntimeEventTimeGate267V1::unavailable);
 for(const auto gate:{RuntimeEventTimeGate267V1::blocked,RuntimeEventTimeGate267V1::unavailable,RuntimeEventTimeGate267V1::indeterminate}){DateAdvanceResult267V1 result;assert(!DateTimeGateAllowsArm267V1(gate,result));assert(!result.arm_attempted&&!result.resume_attempted&&!result.resume_submitted&&!result.claim_found&&result.claim_sequence==0);assert(result.access_cleanup_unknown==(gate==RuntimeEventTimeGate267V1::indeterminate));}
 DateAdvanceResult267V1 clear;assert(DateTimeGateAllowsArm267V1(RuntimeEventTimeGate267V1::clear,clear));assert(!clear.arm_attempted&&!clear.access_cleanup_unknown);std::cout<<"Fullscreen defaultOFF and actual preARM gate projection PASS\n";}
