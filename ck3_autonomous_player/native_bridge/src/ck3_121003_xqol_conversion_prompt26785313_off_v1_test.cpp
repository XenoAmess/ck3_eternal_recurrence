#ifdef NDEBUG
#undef NDEBUG
#endif
#include "xar_bridge/ck3_121003_xqol_conversion_prompt26785313_raw_v1.hpp"
#include <cassert>
#include <iostream>
using namespace xar::ck3_121003::build26785313;
int main(){ReadonlyBindings b;LetterBindings267V1 image;xar::ck3_1210::CoreSnapshotPrefix core;XqolConversionScene267V1 scene;XqolConversionPromptRaw267V1 raw;std::string reason;assert(!ReadXqolConversionPromptRaw267V1(b,image,core,scene,1,raw,reason));assert(reason=="current_xqol_prompt_default_off");for(const auto choice:{XqolConversionChoice267V1::confirm,XqolConversionChoice267V1::cancel}){const auto call=SelectXqolConversionPromptRaw267V1(b,image,core,scene,1,raw,choice);assert(!call.effect_entered&&call.cleanup_known&&call.status==LetterRawCallStatus267V1::unavailable);}std::cout<<"XQOL prompt defaultOFF no native read/select\n";}
