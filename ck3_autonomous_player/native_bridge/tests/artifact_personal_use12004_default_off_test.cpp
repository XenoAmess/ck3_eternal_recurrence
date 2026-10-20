#ifdef NDEBUG
#error "Finite assertion fixture must be compiled with NDEBUG undefined"
#endif
#ifdef XAR_CK3_ENABLE_ARTIFACT_PERSONAL_USE_PRIVATE_V1
#error "This target qualifies the absent default-OFF macro; it must not inherit ON"
#endif
#include "../src/artifact_personal_use12004.cpp"
#include <cassert>
namespace item=xar::ck3_12004::artifact_personal_use;
namespace {
unsigned frames=0,reads=0,claims=0,dispatches=0;
item::Frame expected{1,1,1,53144328,123,77,0x1000,true,true,true,true,true};
bool Frame(void*,item::Frame& out) noexcept {++frames;out=expected;return true;}
bool Read(void*,const void*,void*,std::size_t) noexcept {++reads;return false;}
bool Claim(void*,const item::Frame&,const item::Request&,
           const item::Observation&,const item::Witness&) noexcept {++claims;return true;}
bool Dispatch(const item::Env&,const void*,const void*,bool) noexcept {++dispatches;return true;}
}
int main(){
  item::Env env{};env.enabled=true;env.actions_enabled=true;
  env.existing.model.enabled=true;env.existing.model.image_base=0x10000000;
  env.existing.model.read_memory=&Read;env.existing.source_bound=true;
  env.admitted_executable_sha256=xar::ck3_12004::kExecutableSha256;
  env.frame=&Frame;env.claim_once=&Claim;env.dispatch=&Dispatch;
  const auto result=item::SubmitArtifactPersonalUse12004(env,expected,{1,900,0,item::absent,true});
  assert(result.status=="private_action_disabled");
  assert(!result.invoked&&!result.once_intent_consumed&&!result.dispatch_call_returned&&!result.needs_recovery);
  assert(frames==0&&reads==0&&claims==0&&dispatches==0);
}
