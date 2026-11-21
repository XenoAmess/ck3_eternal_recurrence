#include "ck3_121003_succession_lifecycle26785313_wire_v1.cpp"
#include "ck3_121003_succession_lifecycle26785313_owner_v1.cpp"
#include <iostream>
#include <stdexcept>
using namespace xar::ck3_121003::build26785313;
void Check(bool v){if(!v)throw std::runtime_error("succession default-OFF authority invariant");}
int main(){try{
 auto b=BindSuccessionContinueImage267V1(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);Check(!b.verified&&!b.image);
 ReadonlyBindings core;core.exact_image_admitted=true;core.core.enabled=true;SuccessionExpectedWindow267V1 e;SuccessionRawSample267V1 sample;std::string reason;b.verified=true;
 Check(!ReadSuccessionContinueRaw267V1(core,b,e,sample,reason));Check(!CallSuccessionContinueRaw267V1(core,b,e,sample).effect_entered);
 SuccessionSession267V1 session;SuccessionContext267V1 q;q.session=&session;q.bindings=core;xar::ck3_11906::MainThreadExecutionStampV1 s{};s.thread_id=GetCurrentThreadId();s.pump_epoch=1;s.paused=true;
 Check(!ExecuteSuccessionLifecycleOnOwner267V1(nullptr,s));Check(ExecuteSuccessionLifecycleOnOwner267V1(&q,s));Check(!q.result.source_available&&!q.result.effect_attempted&&!q.result.world_available);
 BlockSuccessionUnknown267V1(session);Check(ExecuteSuccessionLifecycleOnOwner267V1(&q,s));Check(!q.result.effect_attempted&&!q.result.native_returned);
 std::cout<<"PASS default-OFF raw/Close/fixed lifecycle refusal despite caller DATA; no Native calls\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
