#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_TEXT_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_TEXT_V1
#error Independent default-OFF test must not enable the feature.
#endif
#include "rite_text_owner_nogame_fixture.hpp"
int main(){using namespace text_owner_fixture;try{state.Reset();Session s;auto m=Mail();for(auto a:{A::query,A::set_name,A::set_description}){auto q=Request(s,m.get(),a);Run(q);Require(q.result.status==S::unavailable&&q.result.reason=="rite_text_default_off"&&!q.result.claim_sequence&&!q.result.effect_attempted&&!q.result.native_returned&&q.result.cleanup_known&&!state.bindings&&!state.frames&&!state.observations&&!state.calls,"defaultOFF actual owner performed work");NoSource(q);Wire(q);}std::cout<<"PASS default_OFF_three_actions_no_work; NoGame\n";return 0;}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}}
