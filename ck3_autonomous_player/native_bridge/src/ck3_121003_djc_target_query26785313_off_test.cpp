#include "ck3_121003_djc_target_query26785313_wire_v1.cpp"
#include "ck3_121003_djc_target_query26785313_owner_v1.cpp"
#include <iostream>
#include <stdexcept>
using namespace xar::ck3_121003::build26785313;
void Check(bool v){if(!v)throw std::runtime_error("DJC default-OFF authority invariant");}
int main(){try{
 auto b=BindCurrentDjcDeclarations267V1(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);Check(!b.verified&&!b.image);
 ReadonlyBindings core;core.exact_image_admitted=true;core.core.enabled=true;DjcRawTarget267V1 raw;xar::ck3_1210::CoreSnapshotPrefix expected{};
 b.verified=true;Check(!ReadCurrentDjcTargetRaw267V1(core,b,expected,42,UINT64_MAX,raw)&&!raw.available);
 DjcTargetQuerySession267V1 session;DjcTargetQueryContext267V1 q;q.session=&session;q.bindings=core;q.request.target_character_id=42;
 xar::ck3_11906::MainThreadExecutionStampV1 s{};s.thread_id=GetCurrentThreadId();s.pump_epoch=1;s.paused=true;
 Check(!ExecuteDjcTargetQueryOnOwner267V1(nullptr,s));Check(ExecuteDjcTargetQueryOnOwner267V1(&q,s));Check(!q.result.raw.available&&!q.result.core_available&&!q.result.provider_generation&&!q.native_query_entered);
 BlockDjcTargetQueryUnknown267V1(session);Check(ExecuteDjcTargetQueryOnOwner267V1(&q,s));Check(!q.native_query_entered&&!q.result.raw.available);
 std::cout<<"PASS default-OFF raw and owner refusal despite caller data; no game/native calls\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
