#ifdef NDEBUG
#error "Finite assertion fixture must be compiled with NDEBUG undefined"
#endif
// Owned-memory consumer fixture. Source candidate only: NOT built or executed.
// Future isolated target: C++20, native_bridge/include + candidate/include.
// The action guard is enabled solely in this standalone fixture translation unit.
#define XAR_CK3_ENABLE_ARTIFACT_PERSONAL_USE_PRIVATE_V1 1
#include "../src/artifact_personal_use12004.cpp"
#include <cassert>
#include <cstring>
#include <unordered_map>

namespace ap=xar::ck3_12004::artifact_personal_use;
struct Fixture {
  static constexpr std::uintptr_t image=0x100000000, actor=0x200000,
    artifact=0x220000, replacement=0x230000, component=0x240000,
    inventory=component+0x458, slots=0x250000, owned=0x260000,
    type=0x270000, slot_type=0x280000, owner=0x300000, gfx=0x310000,
    handler=0x320000, view=0x330000, widget=0x340000,
    character_slot=0x400000, character_store=0x410000, character_rows=0x420000,
    artifact_slot=0x430000, artifact_store=0x440000, artifact_rows=0x450000,
    player_reference=0x460000;
  static constexpr std::uint32_t actor_id=0x01000001, artifact_id=0x02000002,
      replacement_id=0x03000003;
  std::unordered_map<std::uintptr_t,unsigned char>memory;
  ap::Frame current{41,3,8,100,123,actor_id,owner,true,true,true,true,true};
  ap::Env env{};
  bool allowed=true, claimed=false, dispatched_ok=true, drift=false,
       report_native_member=false, visible=true;
  unsigned dispatches=0,claims=0;const void*picked=reinterpret_cast<const void*>(slots);
  template<class T> void put(std::uintptr_t at,const T&value){
    const auto*raw=reinterpret_cast<const unsigned char*>(&value);
    for(std::size_t n=0;n<sizeof(T);++n)memory[at+n]=raw[n];
  }
  void bytes(std::uintptr_t at,std::string_view value){
    for(std::size_t n=0;n<value.size();++n)memory[at+n]=static_cast<unsigned char>(value[n]);
  }
  template<class T> T get(std::uintptr_t at){T out{};assert(read(this,reinterpret_cast<const void*>(at),&out,sizeof(out)));return out;}
  static bool read(void*context,const void*address,void*out,std::size_t size)noexcept{
    auto&self=*static_cast<Fixture*>(context);const auto at=reinterpret_cast<std::uintptr_t>(address);
    for(std::size_t n=0;n<size;++n){auto it=self.memory.find(at+n);if(it==self.memory.end())return false;
      static_cast<unsigned char*>(out)[n]=it->second;}return true;
  }
  static bool frame(void*context,ap::Frame&out)noexcept{out=static_cast<Fixture*>(context)->current;return true;}
  static Fixture& f(const ap::Env&e){return *static_cast<Fixture*>(e.context);}
  static bool is_visible(const ap::Env&e,const void*,bool&out)noexcept{out=f(e).visible;return true;}
  static bool pick(const ap::Env&e,const void*,const void*,const void*&out)noexcept{out=f(e).picked;return true;}
  static bool can(const ap::Env&e,const void*,const void*,const void*,bool&out)noexcept{
    auto&self=f(e);out=self.allowed;if(self.drift)++self.current.capture_epoch;return true;}
  static bool equipped(const ap::Env&e,const void*,const void*,bool&out)noexcept{out=f(e).report_native_member;return true;}
  static bool text(const ap::Env&,const void*,std::string&out)noexcept{
    out="synthetic item-local modifier description";return true;}
  static bool claim(void*context,const ap::Frame&frame,const ap::Request&request,
                    const ap::Observation&before,const ap::Witness&witness)noexcept{
    auto&self=*static_cast<Fixture*>(context);
    assert(frame==self.current&&before.available&&before.frame==frame&&before.artifact_id==request.artifact_id);
    assert(request.artifact_id==artifact_id&&witness.actor==actor&&witness.artifact==artifact);
    assert(witness.inventory==inventory&&witness.view==view&&witness.character_owner==actor_id&&witness.site_owner==ap::absent);
    ++self.claims;if(self.claimed)return false;self.claimed=true;return true;}
  static bool dispatch(const ap::Env&e,const void*,const void*,bool)noexcept{
    ++f(e).dispatches;return f(e).dispatched_ok;}
  void header(std::uintptr_t at,std::uintptr_t data,std::int32_t count){
    put(at,data);put(at+8,count);put(at+12,count);put(at+16,std::uint64_t{0});}
  void object(std::uintptr_t at,std::uint32_t id){
    put(at+0x10,id);put(at+0x14,std::uint32_t{0x41727469});
    put(at+0x78,actor_id);put(at+0x7C,ap::absent);put(at+0xB8,type);
  }
  void row(std::uint32_t index,std::uint32_t id){
    const auto at=slots+index*24;put(at,image+0x4593568);put(at+8,slot_type);
    put(at+16,id);put(at+20,std::uint32_t{0x496E7653});}
  void held(bool requested){row(0,requested?artifact_id:replacement_id);report_native_member=requested;}
  Fixture(){
    struct Pin{std::uintptr_t rva;const char*hex;};
#include "../src/artifact_personal_use12004_pins.inc"
    for(const auto&p:pins){const std::string_view hex=p.hex;
      const auto digit=[](char c){return c<='9'?c-'0':c-'a'+10;};
      for(std::size_t n=0;n<hex.size()/2;++n)put(image+p.rva+n,
          static_cast<unsigned char>(digit(hex[n*2])*16+digit(hex[n*2+1])));}
    put(character_slot,character_store);put(character_store+0x20,character_rows);
    put(character_store+0x2C,std::uint32_t{2});put(character_rows+16+8,actor);
    put(actor+0x18,actor_id);put(actor+0x1C,std::uint32_t{0x43686172});put(actor+0x1B0,component);
    put(artifact_slot,artifact_store);put(artifact_store+0x20,artifact_rows);
    put(artifact_store+0x2C,std::uint32_t{4});put(artifact_rows+2*16+8,artifact);
    put(artifact_rows+3*16+8,replacement);object(artifact,artifact_id);object(replacement,replacement_id);
    put(player_reference,actor_id);put(inventory+0x38,actor_id);put(inventory+0x3C,ap::absent);
    header(inventory+0x40,slots,2);header(inventory+0x58,owned,2);
    put(owned,artifact_id);put(owned+4,replacement_id);row(0,replacement_id);row(1,ap::absent);
    put(type+0x44,std::uint32_t{0});put(slot_type+0x38,std::uint32_t{0x4744624F});
    bytes(slot_type+0x18,"weapon");put(slot_type+0x28,std::uint64_t{6});put(slot_type+0x30,std::uint64_t{15});
    put(artifact+0xD8,std::uintptr_t{0});put(artifact+0xD8+0xC,std::int32_t{0});
    put(artifact+0xD8+0x68,std::uintptr_t{0});
    put(owner+0x10,gfx);put(gfx+0x88,handler);put(handler+0x378,view);
    put(view,image+0x4577608);put(view+0x10,image+0x45776D8);
    put(view+0x98,owner);put(view+0xA0,handler);put(view+0x60,widget);
    put(view+0xC8,actor_id);put(view+0x2D0,std::uintptr_t{0});
    env.existing.model.enabled=true;env.existing.model.image_base=image;
    env.existing.model.read_memory=&read;env.existing.model.read_context=this;
    env.existing.model.character_storage=reinterpret_cast<void**>(character_slot);
    env.existing.model.artifact_storage=reinterpret_cast<void**>(artifact_slot);
    env.existing.current_actor_reference=reinterpret_cast<const std::uint32_t*>(player_reference);
    env.existing.source_bound=true;env.admitted_executable_sha256=xar::ck3_12004::kExecutableSha256;
    env.enabled=true;env.actions_enabled=true;env.context=this;env.frame=&frame;
    env.visible=&is_visible;env.pick=&pick;env.can_equip_in_slot=&can;env.equipped=&equipped;
    env.modifier_text=&text;env.claim_once=&claim;env.dispatch=&dispatch;
  }
  ap::Request equip()const{return {1,artifact_id,0,replacement_id,true};}
  ap::Observation observation(){ap::Observation out;assert(ap::ReadArtifactPersonalUse12004(env,current,artifact_id,out));return out;}
};
int main(){
  {Fixture f;auto o=f.observation();assert(o.available&&o.personally_owned&&!o.equipped&&o.effective_slot_index==0);
    assert(o.can_equip_in_effective_slot==true&&o.replacing_artifact_id==Fixture::replacement_id);
    assert(o.item_modifier_definition_available&&o.modifier_description_available&&!o.personal_net_effect_attributed);}
  {Fixture f;f.put(Fixture::artifact+0x10,std::uint32_t{0x04000002});ap::Observation o;
    assert(!ap::ReadArtifactPersonalUse12004(f.env,f.current,Fixture::artifact_id,o));}
  {Fixture f;f.put(Fixture::replacement+0x78,std::uint32_t{0x01000009});ap::Observation o;
    assert(!ap::ReadArtifactPersonalUse12004(f.env,f.current,Fixture::artifact_id,o));}
  {Fixture f;f.put(Fixture::inventory+0x64,std::int32_t{65});ap::Observation o;
    assert(!ap::ReadArtifactPersonalUse12004(f.env,f.current,Fixture::artifact_id,o));}
  {Fixture f;f.held(true);f.row(1,Fixture::artifact_id);ap::Observation o;
    assert(!ap::ReadArtifactPersonalUse12004(f.env,f.current,Fixture::artifact_id,o));}
  {Fixture f;f.picked=reinterpret_cast<const void*>(Fixture::slots+1);ap::Observation o;
    assert(!ap::ReadArtifactPersonalUse12004(f.env,f.current,Fixture::artifact_id,o));}
  {Fixture f;f.report_native_member=true;ap::Observation o;
    assert(!ap::ReadArtifactPersonalUse12004(f.env,f.current,Fixture::artifact_id,o));}
  {Fixture f;f.drift=true;ap::Observation o;
    assert(!ap::ReadArtifactPersonalUse12004(f.env,f.current,Fixture::artifact_id,o));}
  {Fixture f;f.env.actions_enabled=false;auto r=ap::SubmitArtifactPersonalUse12004(f.env,f.current,f.equip());assert(!r.invoked&&!f.dispatches&&!f.claims);}
  {Fixture f;f.held(true);auto r=ap::SubmitArtifactPersonalUse12004(f.env,f.current,f.equip());
    assert(r.status=="desired_state_already_observed_no_dispatch"&&!f.dispatches&&!f.claims);}
  {Fixture f;f.allowed=false;auto r=ap::SubmitArtifactPersonalUse12004(f.env,f.current,f.equip());assert(!r.invoked&&!f.dispatches&&!f.claims);}
  {Fixture f;auto request=f.equip();auto r=ap::SubmitArtifactPersonalUse12004(f.env,f.current,request);
    assert(r.invoked&&r.once_intent_consumed&&r.dispatch_call_returned&&r.needs_recovery&&f.dispatches==1);
    auto unchanged=f.observation();assert(!ap::DesiredStateObserved12004(r.before,request,unchanged));
    f.held(true);++f.current.capture_epoch;++f.current.revision;auto after=f.observation();
    assert(ap::DesiredStateObserved12004(r.before,request,after));}
  {Fixture f;f.dispatched_ok=false;auto request=f.equip();auto r=ap::SubmitArtifactPersonalUse12004(f.env,f.current,request);
    assert(r.status=="dispatch_result_unknown_no_replay"&&r.needs_recovery);++request.request_sequence;
    auto again=ap::SubmitArtifactPersonalUse12004(f.env,f.current,request);assert(!again.invoked&&f.dispatches==1);}
  {Fixture f;f.held(true);ap::Request request{2,Fixture::artifact_id,0,ap::absent,false};
    auto r=ap::SubmitArtifactPersonalUse12004(f.env,f.current,request);assert(r.invoked&&r.before.can_unequip==true);
    f.row(0,ap::absent);f.report_native_member=false;++f.current.capture_epoch;++f.current.revision;
    auto after=f.observation();assert(ap::DesiredStateObserved12004(r.before,request,after));}
  {Fixture f;auto before=f.observation();auto request=f.equip();auto after=before;
    ++after.frame.capture_epoch;after.equipped=true;after.equipped_slot_index=0;
    assert(!ap::DesiredStateObserved12004(before,request,after));}
  {Fixture f;f.visible=false;auto r=ap::SubmitArtifactPersonalUse12004(f.env,f.current,f.equip());assert(!r.invoked&&!f.dispatches);}
}
