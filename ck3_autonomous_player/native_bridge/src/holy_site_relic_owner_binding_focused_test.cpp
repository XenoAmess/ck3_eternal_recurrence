// Reuse the frozen owned-memory fixture definitions, never its old matrix
// entrypoint. Production helper and complete production formatters are linked.
#define main FrozenRelicPolicyMatrixNotExecuted
#include "ck3_12004_holy_site_relic_actions_test.cpp"
#undef main

namespace {
struct OwnerFixture:Fixture {
 bool drift_owner=false;int owner_reads=0;
 OwnerFixture(){Put(window.data(),0x98,owner.data());bindings.read_memory=&ReadOwner;}
 static bool ReadOwner(void*opaque,const void*address,void*out,std::size_t bytes) noexcept {
  auto&f=*static_cast<OwnerFixture*>(static_cast<Fixture*>(opaque));
  if(address==f.window.data()+0x98&&bytes==sizeof(void*)){
   ++f.owner_reads;
   if(f.drift_owner&&f.owner_reads>1){const void*foreign=f.gfx.data();std::memcpy(out,&foreign,bytes);return true;}
  }
  return Fixture::Read(opaque,address,out,bytes);
 }
 static bool SelectThenOwnerChanges(const relic::Bindings&b,const void*w,const void*a,bool&attempted) noexcept {
  const bool result=Fixture::Select(b,w,a,attempted);
  auto&f=*static_cast<OwnerFixture*>(static_cast<Fixture*>(b.read_context));Put(f.window.data(),0x98,f.gfx.data());return result;
 }
};
}
int main(int argc,char**argv){try{
 const std::filesystem::path dir=argc>1?argv[1]:"";
 if(dir.empty()||std::filesystem::exists(dir))throw std::runtime_error("fresh focused output directory required");
 std::filesystem::create_directories(dir);
 {OwnerFixture f;relic::Result result;
  Check(static_cast<const void*>(f.owner.data())!=f.gfx.data(),"actual R6 owner and gfx roles are modeled as distinct objects");
  Put(f.window.data(),0x110,static_cast<const void*>(&f.slots[1]));const auto request=f.SelectRequest();
  Check(f.Run(request,result)&&result.dispatch_invoked&&result.selection_postcondition_observed,"distinct real owner+98 and gfx+88 handler admitted");
  Check(f.select_calls==1&&result.after.slot_index==1U,"single select preserves source slot");
  Packet(dir,"select-preserves-slot",result,request);
 }
 {OwnerFixture f;relic::Result result;Put(f.window.data(),0x98,f.gfx.data());
  Check(!f.Run(f.SelectRequest(),result)&&!result.native_dispatch_attempted&&f.select_calls==0,"foreign owner even equal to gfx rejected");
  Packet(dir,"foreign-window-owner",result,f.SelectRequest());
 }
 {OwnerFixture f;relic::Result result;Put(f.window.data(),0x98,static_cast<const void*>(nullptr));
  Check(!f.Run(f.SelectRequest(),result)&&!result.native_dispatch_attempted,"null window owner rejected");
  Packet(dir,"null-window-owner",result,f.SelectRequest());
 }
 {OwnerFixture f;relic::Result result;f.drift_owner=true;
  Check(!f.Run(f.SelectRequest(),result)&&f.owner_reads>=2&&!result.native_dispatch_attempted&&f.select_calls==0,"window owner drift refused before callback");
  Packet(dir,"window-owner-drift-before-dispatch",result,f.SelectRequest());
 }
 {OwnerFixture f;relic::Result result;Put(f.window.data(),0xA0,f.gfx.data());
  Check(!f.Run(f.SelectRequest(),result)&&!result.native_dispatch_attempted&&f.select_calls==0,"wrong handler backpointer rejected");
  Packet(dir,"bad-window-back-handler",result,f.SelectRequest());
 }
 {OwnerFixture f;relic::Result result;f.bindings.select_artifact=&OwnerFixture::SelectThenOwnerChanges;
  Check(f.Run(f.SelectRequest(),result)&&result.native_dispatch_attempted&&result.verification_pending,"owner drift after callback keeps actual ACK pending");
  Check(!result.selection_postcondition_observed&&!result.after.available&&f.select_calls==1,"owner drift after callback is unknown without retry");
  Packet(dir,"window-owner-drift-after-dispatch",result,f.SelectRequest());
 }
 {OwnerFixture f;relic::Result result;const auto request=f.ActionRequest(relic::Operation::enshrine);
  Check(f.Run(request,result)&&f.click_calls==1&&result.verification_pending&&!result.business_outcome_observed,"original click injected ACK remains no business proof with corrected owner role");
  Packet(dir,"enshrine-ack-only",result,request);
 }
 std::cout<<"{\"status\":\"PASS\",\"focused_owner_binding_checks\":"<<checks
  <<",\"old_30_check_matrix_executed\":false,\"source_role_shaped_synthetic_memory\":true,\"original_engine_code_executed\":false,\"action_ready\":false}\n";
 return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
