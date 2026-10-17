// Owned synthetic typed storage and callbacks, production reader+full serializer.
// No CK3 process, original game function or desktop operation executes.
#include "xar_bridge/ck3_12004_holy_site_adoption_detail.hpp"
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
namespace h=xar::ck3_12004::religion::holy_site;
namespace{
unsigned checks=0;
void Check(bool v,const char*why){++checks;if(!v)throw std::runtime_error(why);}
template<std::size_t N>using Bytes=std::array<std::byte,N>;
template<class B,class T>void Put(B&b,std::size_t o,T v){std::memcpy(b.data()+o,&v,sizeof(v));}
struct Fixture{
 static constexpr std::uintptr_t base=0x140000000;
 static constexpr std::uint32_t actor=0x03000004,site_id=0x81000002,token=44;
 Bytes<0x28>owner{};Bytes<0x90>gfx{};Bytes<0x1C0>handler{};Bytes<0x250>detail{};
 Bytes<0x40>controller{},context{},definition{};Bytes<128>entries{};Bytes<48>dict{};
 Bytes<0x30>store{};Bytes<0x50>slots{};Bytes<0x18>site{};Bytes<0x20>settings{};
 Bytes<48>detail_dict{};Bytes<0x30>character_store{};Bytes<0x50>character_slots{};
 Bytes<0x1C8>character{};Bytes<0x450>character_state{};Bytes<0x10>clock{};Bytes<0x60>cooldown_rows{};
 std::array<Bytes<24>,3>cols{};
 void*storeptr=store.data();std::uint32_t actual_actor=actor,selected_token=token;
 void*character_storeptr=character_store.data(),*clockptr=clock.data();
 std::string key="adopt_holy_site_decision",reason="native fixture reason";
 std::string requirements="Full native requirements\nCompatibility: false\nIndependent: true",cost_description="Native piety cost: 1000";
 std::array<std::int64_t,10>costs{0,0,100000000,0,0,0,0,0,0,0};
 bool fail_requirements=false,mutate_detail_context=false,affordable=true,bad_lookup=false,change_clock=false,wrong_context_getter=false;unsigned lookups=0;
 bool legal=false;unsigned confirms=0,reasons=0,destroys=0;
 Fixture(){
  Put(owner,0x10,gfx.data());Put(gfx,0x88,handler.data());Put(handler,0x1B8,detail.data());
  Put(detail,0,base+0x455D4F8);Put(detail,0xA0,handler.data());Put(detail,0x60,site.data());
  Put(detail,0xD0,definition.data());Put(detail,0xD8,actor);Put(detail,0xDC,std::int32_t{-1});Put(detail,0x248,controller.data());
  Put(definition,0,base+0x48BD150);Put(definition,0x18,key.c_str());
  Put(definition,0x28,static_cast<std::uint64_t>(key.size()));Put(definition,0x30,std::uint64_t{31});Put(definition,0x38,std::uint32_t{0x4744624F});
  Put(controller,0,base+0x45A08F0);Put(controller,8,detail.data());Put(controller,0x10,handler.data());Put(controller,0x18,context.data());
  Put(controller,0x20,entries.data());Put(controller,0x28,std::int32_t{2});Put(controller,0x2C,std::int32_t{2});Put(controller,0x38,std::int32_t{1});
  Put(context,0x28,dict.data());Put(context,0x30,std::int32_t{2});Put(context,0x34,std::int32_t{2});
  Put(dict,0,std::uint32_t{99});Scope(dict,8,0x82000003);Put(dict,24,token);Scope(dict,32,site_id);
  detail_dict=dict;Put(detail,0xE0,std::uint16_t{4});Put(detail,0xE2,std::uint16_t{0});Put(detail,0xE8,static_cast<std::uint64_t>(actor));
  Put(detail,0xF8,detail_dict.data());Put(detail,0x100,std::int32_t{2});Put(detail,0x104,std::int32_t{2});
  Put(character_store,xar::ck3_12004::kCharacterStorageSlotsOffset,character_slots.data());
  Put(character_store,xar::ck3_12004::kCharacterStorageCapacityOffset,std::int32_t{5});
  Put(character_slots,4*xar::ck3_12004::kCharacterStorageSlotStride+xar::ck3_12004::kCharacterStorageObjectOffset,character.data());
  Put(character,xar::ck3_12004::kCharacterFullIdOffset,actor);Put(character,0x1C0,character_state.data());
  Put(character_state,0x444,std::int32_t{-1});Put(clock,8,std::int32_t{100});
  Scope(entries,0,0x82000003);Scope(entries,64,site_id);entries[64+0x38]=std::byte{1};
  // Different padding must not make native semantic equality fail.
  Put(entries,64+4,std::uint32_t{0xA5A5A5A5});Put(dict,32+4,std::uint32_t{0x5A5A5A5A});
  Put(store,0x20,slots.data());Put(store,0x2C,std::uint32_t{5});Put(slots,2*16+8,site.data());
  Put(site,0x10,site_id);Put(site,0x14,std::uint32_t{0x486F5374});
  const std::array<std::uint32_t,3>td{0x5795050,0x5586B90,0x5802AC0};
  for(std::size_t i=0;i<3;++i){Put(cols[i],0,std::uint32_t{1});Put(cols[i],12,td[i]);Put(cols[i],20,static_cast<std::uint32_t>(0x1000+i*0x100));}
 }
 template<class B>static void Scope(B&b,std::size_t o,std::uint32_t id){Put(b,o,std::uint16_t{23});Put(b,o+2,std::uint16_t{0});Put(b,o+8,static_cast<std::uint64_t>(id));}
};
Fixture*f=nullptr;
struct Code{std::uintptr_t rva;std::string_view hex;};
constexpr Code code[]{
 {0x1471140,"33d2e9c90a0000"},{0x1471C10,"48895c240848896c24104889742418574883ec60488bea488bf140b701488b89"},
 {0x1471190,"40534883ec60488bd933d2e8700a000084c0745a488d542420488bcbe80f0b00"},
 {0x1471CC0,"48895c2410555657415641574883ec30488bfa488be94533ff44897c2420448b"},
 {0x18D1890,"48895c2408574883ec304c8b4a28488bf9486352348b0541aa47044c8d04524b"},
 {0x26C3F10,"40534883ec20488bda4885c90f84c70000006683391775058b5108eb05baffff"},
 {0xA75D00,"48895c2408564883ec20be1000000065488b042558000000488b188b041e3905"},
 {0x1471150,"4889542410534883ec30488bda33c0894424204889024889421048c742180f00"},
 {0x856050,"40534883ec20488b5118488bd94883fa10722c488b0948ffc24881fa00100000"},
 {0x1470BF0,"48895c24084889542410574883ec30488bda488bf933c0894424204889024889"},
 {0x3103A10,"48895c241048896c2418488974242057415641574883ec504d8bf94d8bf0488b"},
 {0xB1DFF0,"488b4118c3"},{0x1470DF0,"48895c2420488954241055565741564157488dac24a0fcffff4881ec60040000"},
 {0x14706B0,"488d81881400004c8bc1488d91e81d0000483bc2741483b8c000000000752048"},
 {0x310CE50,"40534883ec70498bd80f57c00f114424200f114424300f114424400f11442450"},
 {0x310CEC0,"48895c2410488974241848897c2420554154415541564157488dac24c0fcffff"},
 {0x310B390,"488bc448895808574881ecc0000000498bd9498bf80f57c00f1140a80f1140b8"},
 {0x310E6F0,"48895c24085556574154415541564157488dac2490fdffff4881ec700300004d"},
 {0x1A74790,"4c8bd90fb6c235c59d1c814c8bd24469c893010001488bc248c1e808440fb6c0"},
 {0x2957F10,"48895c241048897424185557415441564157488dac24b0fdffff4881ec50030000"}};
bool Copy(void*,const void*p,void*out,std::size_t n)noexcept{
 const auto address=reinterpret_cast<std::uintptr_t>(p);
 for(const auto&c:code)if(address==Fixture::base+c.rva){
  if(n>c.hex.size()/2)return false;
  const auto digit=[](char v){return v>='0'&&v<='9'?v-'0':v-'a'+10;};
  for(std::size_t i=0;i<n;++i)static_cast<unsigned char*>(out)[i]=static_cast<unsigned char>((digit(c.hex[2*i])<<4)|digit(c.hex[2*i+1]));return true;
 }
 const std::array<std::uintptr_t,3>vt{0x455D4F8,0x48BD150,0x45A08F0};
 for(std::size_t i=0;i<3;++i){
  if(i==2&&address==Fixture::base+vt[i]+0x10&&n==8){const auto getter=Fixture::base+0xB1DFF0+(f->wrong_context_getter?1U:0U);std::memcpy(out,&getter,8);return true;}
  if(address==Fixture::base+vt[i]-8&&n==8){const auto col=Fixture::base+0x1000+i*0x100;std::memcpy(out,&col,8);return true;}
  const auto start=Fixture::base+0x1000+i*0x100;
  if(address>=start&&address+n<=start+24){std::memcpy(out,f->cols[i].data()+(address-start),n);return true;}
 }
 if(!p)return false;std::memcpy(out,p,n);return true;
}
bool __fastcall Can(void*p){Check(p==f->detail.data(),"CanConfirm receives actual fixture-owned detail");return f->legal;}
void __fastcall Confirm(void*p){Check(p==f->detail.data(),"Confirm receives actual fixture-owned detail");++f->confirms;}
void*__fastcall Settings(){return f->settings.data();}
void*String(void*p,void*out,const std::string&value){Check(p==f->detail.data(),"text receives actual detail");++f->reasons;
 std::memset(out,0,32);const auto text=value.c_str();const auto size=static_cast<std::uint64_t>(value.size());
 std::memcpy(out,&text,8);std::memcpy(static_cast<std::byte*>(out)+16,&size,8);const std::uint64_t cap=size>31?size:31;std::memcpy(static_cast<std::byte*>(out)+24,&cap,8);return out;}
void*__fastcall Reason(void*p,void*out){return String(p,out,f->reason);}
void*__fastcall Requirements(void*p,void*out){return f->fail_requirements?nullptr:String(p,out,f->requirements);}
void*__fastcall CostDescription(void*p,void*out){return String(p,out,f->cost_description);}
const void*__fastcall Cost(const void*definition){Check(definition==f->definition.data(),"actual definition used for costs");return f->costs.data();}
void __fastcall Evaluate(const void*cost,const void*context,std::int64_t*out){
 Check(cost==f->costs.data()&&context==f->detail.data()+0xE0,"cost evaluation borrows actual detail context");
 std::memcpy(out,f->costs.data(),80);if(f->mutate_detail_context)Fixture::Scope(f->detail_dict,32,Fixture::site_id+1);
}
bool __fastcall Affordable(const void*cost,const void*context,const void*actor,void*reason){
 Check(cost==f->costs.data()&&context==f->detail.data()+0xE0&&actor==f->character.data()&&!reason,"affordability binds actual actor/context");return f->affordable;
}
const std::int32_t*__fastcall CooldownLookup(const void*map,const void*definition){
 Check(map==f->character_state.data()+0x430&&definition==f->definition.data(),"cooldown key is definition pointer value");++f->lookups;
 if(f->change_clock){std::int32_t current=0;std::memcpy(&current,f->clock.data()+8,4);Put(f->clock,8,current+1);}
 if(f->bad_lookup)return reinterpret_cast<const std::int32_t*>(f->clock.data());
 return reinterpret_cast<const std::int32_t*>(f->cooldown_rows.data()+0x10);
}
void __fastcall Destroy(void*){++f->destroys;}
h::AdoptionDetailBindings Bind(Fixture&v){f=&v;h::AdoptionDetailBindings b{};b.enabled=true;b.image_base=Fixture::base;
 b.holy_site_storage=&v.storeptr;b.selected_item_token=&v.selected_token;b.current_actor_reference=&v.actual_actor;b.read_memory=&Copy;
 b.can_confirm=&Can;b.confirm=&Confirm;b.requirements_settings=&Settings;b.confirm_tooltip=&Reason;b.destroy_string=&Destroy;
 b.character_storage=&v.character_storeptr;b.decision_clock=&v.clockptr;b.requirements_description=&Requirements;b.cost_description=&CostDescription;
 b.decision_cost=&Cost;b.evaluate_cost=&Evaluate;b.affordable_cost=&Affordable;b.cooldown_lookup=&CooldownLookup;return b;}
xar::ck3_12002::religion::Context Frame(){xar::ck3_12002::religion::Context c{};c.available=true;c.capture_epoch=17;c.date_raw=53175816;c.played_character_id=Fixture::actor;return c;}
void Save(const std::filesystem::path&d,const char*name,const h::AdoptionDetailSnapshot&s){std::ofstream out(d/name);out<<h::SerializeHolySiteAdoptionDetailCommand12004(s,"g2-read-adoption-fixture",701,s.date_raw)<<'\n';Check(bool(out),"whole native command_result written");}
}
int main(int argc,char**argv){try{
 Check(argc==2,"output directory required");const std::filesystem::path d(argv[1]);std::filesystem::create_directories(d);
 Fixture v;auto b=Bind(v);const auto c=Frame();h::AdoptionDetailSnapshot s{};
 Check(h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s)&&s.available&&!s.native_can_confirm&&
  s.parameter_and_selection_match&&s.selected_index==1&&s.parameter_holy_site_id==Fixture::site_id,"native observed false, second actual entry and padding-independent parameter identity");
 Check(s.confirm_tooltip_available&&s.confirm_tooltip==v.reason&&v.reasons==v.destroys,"actual callback reason copied and original destroy paired");Save(d,"native-false.json",s);
 Check(s.native_detail_context_verified&&s.native_requirements_description_available&&s.native_requirements_description==v.requirements&&
  s.native_cost_description_available&&s.native_cost_description==v.cost_description,"full native requirements and cost text read independently");
 Check(s.native_resource_quote_available&&s.native_resource_vector_raw==v.costs&&s.native_affordable,"actual context cost vector and affordability observed");
 Check(s.native_decision_cooldown_observed&&!s.native_decision_cooldown_present&&!s.native_decision_cooldown_active&&v.lookups==0,"stable zero-count cooldown observed absent without unsafe lookup");
 bool attempted=true;Check(!h::ConfirmHolySiteAdoptionDetail12004(b,s,attempted)&&!attempted&&v.confirms==0,"observed false cannot invoke original Confirm");
 v.legal=true;Check(h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s)&&s.native_can_confirm,"native true stays distinct from unavailable");Save(d,"native-true.json",s);
 attempted=false;Check(h::ConfirmHolySiteAdoptionDetail12004(b,s,attempted)&&attempted&&v.confirms==1,"one authorized original Confirm callback after fresh full binding");
 v.settings[0x10]=std::byte{1};Check(h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s)&&s.native_can_confirm&&s.bypass_requirements_raw==1,"engine true with requirements bypass remains observed separately");Save(d,"bypass-enabled.json",s);
 attempted=true;Check(!h::ConfirmHolySiteAdoptionDetail12004(b,s,attempted)&&!attempted&&v.confirms==1,"bypass never qualifies ordinary original Confirm");v.settings[0x10]=std::byte{0};
 b.requirements_settings=nullptr;Check(h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s)&&s.native_can_confirm&&!s.bypass_requirements_observed,"unavailable bypass setting does not invent regular native legality");Save(d,"bypass-unavailable.json",s);
 attempted=true;Check(!h::ConfirmHolySiteAdoptionDetail12004(b,s,attempted)&&!attempted&&v.confirms==1,"unknown bypass setting blocks original Confirm");b.requirements_settings=&Settings;
 Put(v.dict,32+8,static_cast<std::uint64_t>(Fixture::site_id)+(1ULL<<32));
 Check(!h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s)&&!s.available,"upper payload bits cannot alias a valid HolySite full ID");Save(d,"parameter-mismatch.json",s);
 Fixture::Scope(v.dict,32,Fixture::site_id);Put(v.controller,0x38,std::int32_t{0});v.entries[0x38]=std::byte{1};
 Check(!h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s),"fallback first entry does not prove requested target");Save(d,"fallback-first-rejected.json",s);
 Put(v.controller,0x38,std::int32_t{1});v.actual_actor=Fixture::actor+1;
 Check(!h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s),"current-global actor mismatch blocks binding");
 Check(!h::BindHolySiteAdoptionDetailImage12004(Fixture::base,"wrong-exe").enabled,"foreign source image rejected");
 v.actual_actor=Fixture::actor;v.legal=false;
 Fixture::Scope(v.detail_dict,32,Fixture::site_id+1);
 Check(h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s)&&s.available&&!s.native_detail_context_verified&&
  !s.native_requirements_description_available&&!s.native_resource_quote_available,"detail E0 mismatch preserves base observation but never fabricates quote");Save(d,"detail-context-mismatch.json",s);
 attempted=true;Check(!h::ConfirmHolySiteAdoptionDetail12004(b,s,attempted)&&!attempted,"unverified actual detail context cannot Confirm");
 Fixture::Scope(v.detail_dict,32,Fixture::site_id);v.fail_requirements=true;
 Check(h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s)&&s.native_detail_context_verified&&!s.native_requirements_description_available&&
  s.native_cost_description_available&&s.native_resource_quote_available,"missing requirements text remains unknown independently");Save(d,"requirements-unavailable.json",s);v.fail_requirements=false;
 b.evaluate_cost=nullptr;
 Check(h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s)&&s.native_requirements_description_available&&!s.native_resource_quote_available,"unavailable quote does not erase actual requirements text");Save(d,"quote-unavailable.json",s);b.evaluate_cost=&Evaluate;
 v.wrong_context_getter=true;
 Check(h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s)&&!s.native_requirements_description_available&&!s.native_cost_description_available&&s.native_resource_quote_available,
  "changed original virtual context getter blocks only native text calls");Save(d,"text-context-getter-changed.json",s);v.wrong_context_getter=false;
 v.mutate_detail_context=true;
 Check(h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s)&&!s.native_detail_context_verified&&!s.native_resource_quote_available&&!s.native_requirements_description_available,
  "detail context mutation invalidates all planning observations");Save(d,"detail-context-changed.json",s);v.mutate_detail_context=false;Fixture::Scope(v.detail_dict,32,Fixture::site_id);
 Put(v.character_state,0x438,v.cooldown_rows.data());Put(v.character_state,0x440,std::int32_t{1});Put(v.character_state,0x444,std::int32_t{0});Put(v.character_state,0x448,std::uint8_t{2});
 v.cooldown_rows[4]=std::byte{1};Put(v.cooldown_rows,8,v.definition.data());Put(v.cooldown_rows,0x10,std::int32_t{172});v.cooldown_rows[3*0x18+4]=std::byte{0xFF};
 Check(h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s)&&s.native_decision_cooldown_observed&&s.native_decision_cooldown_present&&
  s.native_decision_expiry_raw==172&&s.native_decision_clock_raw==100&&s.native_decision_cooldown_active,"actual decision-specific deadline and raw clock observed");Save(d,"cooldown-active.json",s);
 Put(v.clock,8,std::int32_t{172});
 Check(h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s)&&s.native_decision_cooldown_observed&&!s.native_decision_cooldown_active,"expiry equality is not active");Save(d,"cooldown-expired.json",s);
 const auto prior_lookups=v.lookups;v.cooldown_rows[3*0x18+4]=std::byte{0};
 Check(h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s)&&!s.native_decision_cooldown_observed&&v.lookups==prior_lookups,"damaged sentinel refuses original lookup before invocation");Save(d,"cooldown-malformed-map.json",s);v.cooldown_rows[3*0x18+4]=std::byte{0xFF};
 v.bad_lookup=true;
 Check(h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s)&&!s.native_decision_cooldown_observed,"foreign expiry pointer stays unknown");Save(d,"cooldown-foreign-result.json",s);v.bad_lookup=false;
 v.change_clock=true;
 Check(h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s)&&!s.native_decision_cooldown_observed,"changing original counter cannot publish a stable cooldown");Save(d,"cooldown-clock-changed.json",s);v.change_clock=false;
 b.decision_clock=nullptr;
 Check(h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s)&&s.native_resource_quote_available&&!s.native_decision_cooldown_observed,"unreadable clock stays unknown independently");Save(d,"cooldown-unavailable.json",s);
 std::cout<<"PASS checks="<<checks<<" actual_reader=true actual_serializer=true synthetic_storage=true synthetic_callbacks=true live=false\n";return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}}
