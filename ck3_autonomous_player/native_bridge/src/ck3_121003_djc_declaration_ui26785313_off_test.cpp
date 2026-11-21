#include "ck3_121003_djc_declaration_ui26785313_wire_v1.cpp"
#include "ck3_121003_djc_declaration_ui26785313_owner_v1.cpp"
#include <iostream>
#include <stdexcept>
using namespace xar::ck3_121003::build26785313;
void Check(bool v){if(!v)throw std::runtime_error("fixed DJC UI defaultOFF authority invariant");}
int main(){try{auto b=BindDjcUiImage267V1(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);Check(!b.verified&&!b.image);ReadonlyBindings core;core.exact_image_admitted=true;core.core.enabled=true;DjcUiExpectedScene267V1 e;DjcUiRawObservation267V1 sample;std::string reason;b.verified=true;
 Check(!ReadDjcUiRaw267V1(core,b,{},888,0,e,UINT64_MAX,sample,reason));Check(!ReadDjcUiRawForClaim267V1(core,b,{},888,0,e,UINT64_MAX,sample,reason));
 for(const auto a:{DjcUiAction267V1::open_ui,DjcUiAction267V1::select_choice,DjcUiAction267V1::send_ui,DjcUiAction267V1::accept_warning})Check(!CallDjcUiRaw267V1(a,core,b,{},888,0,e,UINT64_MAX,sample,1).effect_entered);
 DjcUiSession267V1 session;DjcUiContext267V1 q;q.session=&session;q.bindings=core;xar::ck3_11906::MainThreadExecutionStampV1 stamp{};stamp.thread_id=GetCurrentThreadId();stamp.pump_epoch=1;stamp.paused=true;Check(!ExecuteDjcUiOnOwner267V1(nullptr,stamp));Check(ExecuteDjcUiOnOwner267V1(&q,stamp));Check(!q.result.source_available&&!q.result.effect_attempted&&!q.result.facts_available);BlockDjcUiUnknown267V1(session);Check(ExecuteDjcUiOnOwner267V1(&q,stamp));Check(!q.result.effect_attempted&&!q.result.native_returned);
 std::cout<<"PASS defaultOFF current fixed Open/Select/Send/warning and owner refusal despite caller DATA; no Native calls\n";return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
