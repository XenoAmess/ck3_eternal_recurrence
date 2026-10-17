#define XAR_RELIC_ACTION_CONTEXT_FIXTURE_TYPES_ONLY 1
#include "ck3_12004_holy_site_relic_action_context_test.cpp"

namespace {
struct BindingFixture:ActionFixture {
 bool drift_on_candidate=false,drift_on_text=false;
 void*foreign_owner=nullptr;
 BindingFixture(){foreign_owner=memory.Make(0x20);}
 static BindingFixture&SelfBinding(const r::Bindings&b){return *static_cast<BindingFixture*>(b.model.read_context);}
 static bool CandidateWithDrift(const r::Bindings&b,const void*artifact,const void*site,bool&v)noexcept {
  auto&f=SelfBinding(b);const bool ok=Fixture::Candidate(b,artifact,site,v);
  if(f.drift_on_candidate)f.memory.Put(f.window,0x98,f.foreign_owner);return ok;
 }
 static bool TextWithDrift(const a::Bindings&b,const void*w,std::uintptr_t rva,std::string&v)noexcept {
  auto&f=*static_cast<BindingFixture*>(b.permissions.model.read_context);
  const bool ok=ActionFixture::Text(b,w,rva,v);
  if(f.drift_on_text)f.memory.Put(f.window,0x98,f.foreign_owner);return ok;
 }
 r::Bindings BindPermissions(){auto b=Bind();b.candidate_predicate=&CandidateWithDrift;return b;}
 a::Bindings BindContext(){auto b=BindAction();b.permissions=BindPermissions();b.text=&TextWithDrift;return b;}
 bool Permissions(r::Snapshot&s){return r::ReadHolySiteRelicPermissions12004(BindPermissions(),owner,Context(),site_id,first,s);}
 bool Action(a::Snapshot&s){return a::ReadHolySiteRelicActionContext12004(BindContext(),owner,Context(),site_id,first,s);}
};
}
int main(int argc,char**argv){try {
 checks=0;Check(argc==2,"one fresh focused packet directory required");
 const std::filesystem::path dir(argv[1]);Check(std::filesystem::create_directories(dir),"existing packet directory refused");
 {BindingFixture f;r::Snapshot s;Check(f.owner!=f.gfx,"actual distinct native owner and Gfx roles");
  Check(f.Permissions(s)&&s.window_context.available&&s.artifact_permissions.available&&s.current_buttons.available,"correct outer owner accepts original permission dependencies");
  Check(f.artifact_permission_calls==2&&f.button_calls==2,"four actual injected original permission routes executed");Save(dir,"binding-distinct-permissions.json",s);}
 {BindingFixture f;f.memory.Put(f.window,0x110,static_cast<void*>(nullptr));a::Snapshot s;
  Check(f.Action(s)&&s.preview_identity_available&&s.permissions.window_context.available,"correct outer owner accepts composed action context");
  SaveAction(dir,"binding-distinct-action-context.json",s);}
 {BindingFixture f;f.memory.Put(f.window,0x98,f.foreign_owner);r::Snapshot s;
  Check(f.Permissions(s)&&!s.window_context.available&&!s.artifact_permissions.can_enshrine.available&&s.current_candidates.available,"foreign nonnull window owner preserves candidates but no permission");
  Check(f.artifact_permission_calls==0&&f.button_calls==0,"foreign owner stops original permission dependencies");Save(dir,"binding-foreign-owner-permissions.json",s);}
 {BindingFixture f;f.memory.Put(f.window,0x98,static_cast<void*>(nullptr));a::Snapshot s;
  Check(f.Action(s)&&s.artifact_ownership.available&&!s.preview_identity_available&&!s.destination.available&&f.text_calls==0,"null window owner preserves independent object ownership only");
  SaveAction(dir,"binding-null-owner-action-context.json",s);}
 {BindingFixture f;f.drift_on_candidate=true;r::Snapshot s;
  Check(!f.Permissions(s)&&!s.available&&s.unavailable_reason=="relic_permissions_inputs_changed_during_read","outer owner drift rejects permission snapshot on independent reread");
  Save(dir,"binding-owner-drift-permissions.json",s);}
 {BindingFixture f;f.drift_on_text=true;a::Snapshot s;
  Check(!f.Action(s)&&!s.available&&!s.preview_identity_available&&s.unavailable_reason=="relic_action_context_inputs_changed_during_read","outer owner drift after original text rejects frozen action preview");
  SaveAction(dir,"binding-owner-drift-action-context.json",s);}
 {BindingFixture f;f.memory.Put(f.window,0xA0,f.foreign_owner);r::Snapshot s;
  Check(f.Permissions(s)&&!s.window_context.available&&f.artifact_permission_calls==0&&f.button_calls==0,"registered handler back-pointer remains mandatory");}
 std::cout<<"PASS focused_checks="<<checks<<" packets=6 corrected_owner_roles=true production_readers_and_serializers=true engine_getters_executed=false live=false old_matrix_executed=false\n";
 return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}}
