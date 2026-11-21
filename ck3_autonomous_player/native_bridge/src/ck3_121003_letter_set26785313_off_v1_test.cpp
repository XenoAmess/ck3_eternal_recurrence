#if defined(NDEBUG)
#undef NDEBUG
#endif
#include "xar_bridge/ck3_121003_letter_set26785313_raw_v1.hpp"
#include <cassert>
#include <iostream>
using namespace xar::ck3_121003::build26785313;
int main(){ReadonlyBindings bindings;LetterBindings267V1 image;xar::ck3_1210::CoreSnapshotPrefix core;LetterSetScene267V1 scene;LetterSetRaw267V1 raw;std::string reason;assert(!ReadLetterSetRaw267V1(bindings,image,core,scene,1,raw,reason));assert(reason=="current_letter_set_default_off"&&!raw.native_read_entered&&raw.cleanup_known);const auto call=ReplyKnownLetterSetRaw267V1(bindings,image,core,scene,1,raw,3);assert(call.status==LetterRawCallStatus267V1::unavailable&&!call.effect_entered&&call.cleanup_known);std::cout<<"LetterSet defaultOFF true native refusal PASS\n";}
