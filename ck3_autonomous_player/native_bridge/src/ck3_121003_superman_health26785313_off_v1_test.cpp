#include "xar_bridge/ck3_121003_superman_health26785313_owner_v1.hpp"
#include <stdexcept>
using namespace xar::ck3_121003::build26785313;
int main(){ReadonlyBindings b;xar::ck3_1210::CoreSnapshotPrefix core;SupermanHealthScene267V1 scene;SupermanHealthRaw267V1 raw;std::string reason;
 if(VerifySupermanHealthImage267V1(0)||ReadSupermanHealthRaw267V1(b,core,scene,1,SupermanHealthPhase267V1::baseline,raw,reason)||raw.native_read_entered)throw std::runtime_error("defaultOFF native observation entered");
 const auto call=ChooseKnownSupermanHealthRaw267V1(b,core,scene,1,raw);if(call.effect_entered||!call.cleanup_known||call.status!=LetterRawCallStatus267V1::unavailable)throw std::runtime_error("defaultOFF choice entered");
 SupermanHealthContext267V1 q;q.request.action=SupermanHealthAction267V1::choose_known;q.request.phase=SupermanHealthPhase267V1::completed;q.request.provider_generation=7;q.request.query_sequence=9;xar::ck3_11906::MainThreadExecutionStampV1 stamp;if(!ExecuteSupermanHealthOnOwner267V1(&q,stamp)||q.result.phase!=q.request.phase||q.result.provider_generation!=7||q.result.query_sequence!=9||q.result.effect_attempted||q.result.native_returned)throw std::runtime_error("defaultOFF parsed rejection lease echo lost");return 0;}
