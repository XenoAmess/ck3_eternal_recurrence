#include "xar_bridge/ck3_121003_ccc_actor_transition26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_ccc_event26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_ccc_decision26785313_owner_v1.hpp"
#include <windows.h>
#include <iostream>
#include <stdexcept>
namespace {void*expected=nullptr;unsigned called=0;bool throw_call=false;void Check(bool value,const char*why){if(!value)throw std::runtime_error(why);}bool Call(void*p){Check(p==expected,"typed context identity");++called;if(throw_call)RaiseException(0xE0CCC032,0,0,nullptr);return true;}}
namespace xar::ck3_121003::build26785313 {
bool ExecuteCccTransitionOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&)noexcept{return Call(p);}
bool ExecuteCccEventOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&)noexcept{return Call(p);}
bool ExecuteCccDecisionOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&)noexcept{return Call(p);}
}
int main(){try{using namespace xar::ck3_121003::build26785313;xar::ck3_11906::MainThreadExecutionStampV1 stamp;CccTransitionContext267V1 transition;CccEventContext267V1 event;CccDecisionContext267V1 decision;
for(auto*entry:{&transition.invocation,&event.invocation,&decision.invocation}){expected=entry->context;called=0;
#if defined(XAR_CCC_SHARED_TEST_ON) && XAR_CCC_SHARED_TEST_ON
Check(ExecuteCccOnOwner267V1(entry,stamp)&&called==1,"closed typed invocation delivers exactly once");
#else
Check(!ExecuteCccOnOwner267V1(entry,stamp)&&called==0,"defaultOFF no child dispatch");
#endif
const auto clean=*entry;auto copied=*entry;called=0;Check(!ExecuteCccOnOwner267V1(&copied,stamp)&&called==0,"copied entry cannot borrow another owned context");entry->magic=0;Check(!ExecuteCccOnOwner267V1(entry,stamp)&&called==0,"bad magic");*entry=clean;entry->context=nullptr;Check(!ExecuteCccOnOwner267V1(entry,stamp)&&called==0,"null context");*entry=clean;entry->kind=static_cast<CccInvocationKind267V1>(4);Check(!ExecuteCccOnOwner267V1(entry,stamp)&&called==0,"fourth kind not authorized");*entry=clean;}
Check(!ExecuteCccOnOwner267V1(nullptr,stamp),"null invocation");
#if defined(XAR_CCC_SHARED_TEST_ON) && XAR_CCC_SHARED_TEST_ON
expected=&event;throw_call=true;called=0;Check(!ExecuteCccOnOwner267V1(&event.invocation,stamp)&&called==1,"typed callback SEH never successful dispatch");
#endif
std::cout<<"PASS closed owner32 actual shared callback and exact owned invocation; child handlers explicit NoGame DATA\n";return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
