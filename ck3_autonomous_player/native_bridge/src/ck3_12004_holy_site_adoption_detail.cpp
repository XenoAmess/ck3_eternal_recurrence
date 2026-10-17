#include "xar_bridge/ck3_12004_holy_site_adoption_detail.hpp"
#include <windows.h>
#include <array>
#include <limits>
#include <utility>

namespace xar::ck3_12004::religion::holy_site {
namespace {
constexpr std::uint32_t absent=0xFFFFFFFFU;
bool ProcessRead(void *,const void*p,void*out,std::size_t n)noexcept{
 SIZE_T got=0;return p&&out&&n&&ReadProcessMemory(GetCurrentProcess(),p,out,n,&got)&&got==n;
}
const void*At(const void*p,std::size_t o)noexcept{
 const auto v=reinterpret_cast<std::uintptr_t>(p);
 return v&&o<=std::numeric_limits<std::uintptr_t>::max()-v?reinterpret_cast<const void*>(v+o):nullptr;
}
template<class T>bool Read(const AdoptionDetailBindings&b,const void*p,std::size_t o,T&v)noexcept{
 const auto*q=At(p,o);return q&&b.read_memory&&b.read_memory(b.read_context,q,&v,sizeof(v));
}
bool Pin(const AdoptionDetailBindings&b,std::uintptr_t rva,std::string_view hex)noexcept{
 if(hex.empty()||hex.size()%2||hex.size()>64)return false;
 std::array<unsigned char,32>expected{},actual{};
 const auto digit=[](char c)->unsigned{return c>='0'&&c<='9'?static_cast<unsigned>(c-'0'):static_cast<unsigned>(c-'a'+10);};
 for(std::size_t i=0;i<hex.size()/2;++i)expected[i]=static_cast<unsigned char>((digit(hex[2*i])<<4)|digit(hex[2*i+1]));
 return b.read_memory&&b.read_memory(b.read_context,reinterpret_cast<const void*>(b.image_base+rva),actual.data(),hex.size()/2)&&actual==expected;
}
bool Pins(const AdoptionDetailBindings&b)noexcept{
 return Pin(b,0x1471140,"33d2e9c90a0000")&&
 Pin(b,0x1471C10,"48895c240848896c24104889742418574883ec60488bea488bf140b701488b89")&&
 Pin(b,0x1471190,"40534883ec60488bd933d2e8700a000084c0745a488d542420488bcbe80f0b00")&&
 Pin(b,0x1471CC0,"48895c2410555657415641574883ec30488bfa488be94533ff44897c2420448b")&&
 Pin(b,0x18D1890,"48895c2408574883ec304c8b4a28488bf9486352348b0541aa47044c8d04524b")&&
 Pin(b,0x26C3F10,"40534883ec20488bda4885c90f84c70000006683391775058b5108eb05baffff")&&
 Pin(b,0xA75D00,"48895c2408564883ec20be1000000065488b042558000000488b188b041e3905")&&
 Pin(b,0x1471150,"4889542410534883ec30488bda33c0894424204889024889421048c742180f00")&&
 Pin(b,0x856050,"40534883ec20488b5118488bd94883fa10722c488b0948ffc24881fa00100000");
}
bool TextPlanningPins(const AdoptionDetailBindings&b)noexcept{
 std::uintptr_t getter=0;
 return Read(b,reinterpret_cast<const void*>(b.image_base+0x45A08F0),0x10,getter)&&getter==b.image_base+0xB1DFF0&&
 Pin(b,0x1470BF0,"48895c24084889542410574883ec30488bda488bf933c0894424204889024889")&&
 Pin(b,0x3103A10,"48895c241048896c2418488974242057415641574883ec504d8bf94d8bf0488b")&&
 Pin(b,0xB1DFF0,"488b4118c3")&&
 Pin(b,0x1470DF0,"48895c2420488954241055565741564157488dac24a0fcffff4881ec60040000");
}
bool CostPlanningPins(const AdoptionDetailBindings&b)noexcept{
 return Pin(b,0x14706B0,"488d81881400004c8bc1488d91e81d0000483bc2741483b8c000000000752048")&&
 Pin(b,0x310CE50,"40534883ec70498bd80f57c00f114424200f114424300f114424400f11442450")&&
 Pin(b,0x310CEC0,"48895c2410488974241848897c2420554154415541564157488dac24c0fcffff")&&
 Pin(b,0x310B390,"488bc448895808574881ecc0000000498bd9498bf80f57c00f1140a80f1140b8")&&
 Pin(b,0x310E6F0,"48895c24085556574154415541564157488dac2490fdffff4881ec700300004d");
}
bool Typed(const AdoptionDetailBindings&b,const void*p,std::uintptr_t vt,std::uint32_t td)noexcept{
 std::uintptr_t actual=0,col=0;std::uint32_t signature=0,type=0,self=0;
 return Read(b,p,0,actual)&&actual==b.image_base+vt&&actual>=8&&
  Read(b,reinterpret_cast<const void*>(actual-8),0,col)&&col&&
  Read(b,reinterpret_cast<const void*>(col),0,signature)&&signature==1&&
  Read(b,reinterpret_cast<const void*>(col),12,type)&&type==td&&
  Read(b,reinterpret_cast<const void*>(col),20,self)&&col==b.image_base+self;
}
bool Key(const AdoptionDetailBindings&b,const void*definition,std::string&out){
 if(!Typed(b,definition,0x48BD150,0x5586B90))return false;
 std::uint32_t magic=0;std::uint64_t size=0,capacity=0;const void*text=At(definition,0x18);
 if(!Read(b,definition,0x38,magic)||magic!=0x4744624FU||!Read(b,text,16,size)||!Read(b,text,24,capacity)||
  !size||size>512||size>capacity||(capacity<16&&capacity!=15))return false;
 if(capacity>=16&&(!Read(b,text,0,text)||!text))return false;
 std::array<char,513>bytes{};
 if(!b.read_memory(b.read_context,text,bytes.data(),static_cast<std::size_t>(size)+1)||bytes[static_cast<std::size_t>(size)]!=0)return false;
 out.assign(bytes.data(),static_cast<std::size_t>(size));return true;
}
struct Header{const void*data=nullptr;std::int32_t capacity=0,count=0;const void*allocator=nullptr;bool operator==(const Header&)const=default;};
bool Array(const AdoptionDetailBindings&b,const void*p,std::size_t offset,Header&h)noexcept{
 const auto*base=At(p,offset);
 return Read(b,base,0,h.data)&&Read(b,base,8,h.capacity)&&Read(b,base,12,h.count)&&Read(b,base,16,h.allocator)&&
  h.count>=0&&h.capacity>=h.count&&h.count<=8192&&(h.count==0||h.data);
}
struct Scope{std::uint16_t kind=0,flags=0;std::uint64_t payload=0;bool operator==(const Scope&)const=default;};
bool ScopeAt(const AdoptionDetailBindings&b,const void*p,std::size_t o,Scope&s)noexcept{
 // The original Scope padding+4..7 is not initialized. Never compare it.
 const auto*q=At(p,o);return Read(b,q,0,s.kind)&&Read(b,q,2,s.flags)&&Read(b,q,8,s.payload);
}
bool HolyScope(const Scope&s,std::uint32_t expected)noexcept{return s.kind==23&&s.flags==0&&s.payload==expected&&expected!=absent;}
bool Site(const AdoptionDetailBindings&b,std::uint32_t id)noexcept{
 const void*storage=nullptr,*rows=nullptr,*object=nullptr;std::uint32_t count=0,actual=absent,magic=0;
 return id!=absent&&Read(b,b.holy_site_storage,0,storage)&&storage&&Read(b,storage,0x20,rows)&&rows&&
  Read(b,storage,0x2C,count)&&(id&0xFFFFFFU)<count&&Read(b,rows,static_cast<std::size_t>(id&0xFFFFFFU)*16+8,object)&&object&&
  Read(b,object,0x10,actual)&&actual==id&&Read(b,object,0x14,magic)&&magic==0x486F5374U;
}
struct NamedScope{std::uint32_t key=0;Scope value{};bool operator==(const NamedScope&)const=default;};
struct Pass{
 const void*gfx=nullptr,*handler=nullptr,*detail=nullptr,*root=nullptr,*definition=nullptr,*controller=nullptr,*context=nullptr;
 std::string key;std::uint32_t actor=absent,current_actor=absent,token=0;std::int32_t option=-1,index=-1;
 Header entries{},dictionary{};Scope selected{},parameter{};std::uint8_t selected_mark=0;
 std::vector<NamedScope>parameters;bool operator==(const Pass&)const=default;
};
bool ReadPass(const AdoptionDetailBindings&b,const void*owner,std::uint32_t requested,std::int32_t actor,Pass&p,std::string&why){
 const auto fail=[&](const char*r){why=r;return false;};const void*back=nullptr;
 if(!Read(b,owner,0x10,p.gfx)||!p.gfx||!Read(b,p.gfx,0x88,p.handler)||!p.handler||
  !Read(b,p.handler,0x1B8,p.detail)||!Typed(b,p.detail,0x455D4F8,0x5795050)||
  !Read(b,p.detail,0xA0,back)||back!=p.handler||!Read(b,p.detail,0x60,p.root))return fail("adoption_detail_window_or_owner_unavailable");
 if(!Read(b,p.detail,0xD0,p.definition)||!Key(b,p.definition,p.key)||p.key!="adopt_holy_site_decision")return fail("adoption_detail_definition_unavailable_or_different");
 if(!Read(b,p.detail,0xD8,p.actor)||!Read(b,b.current_actor_reference,0,p.current_actor)||
  !Read(b,p.detail,0xDC,p.option)||p.actor!=static_cast<std::uint32_t>(actor)||p.current_actor!=p.actor||p.option!=-1)
  return fail("adoption_detail_current_player_binding_differs");
 if(!Read(b,p.detail,0x248,p.controller)||!Typed(b,p.controller,0x45A08F0,0x5802AC0)||
  !Read(b,p.controller,8,back)||back!=p.detail||!Read(b,p.controller,0x10,back)||back!=p.handler||
  !Read(b,p.controller,0x18,p.context)||!p.context)return fail("adoption_select_scope_controller_unavailable");
 if(!Array(b,p.controller,0x20,p.entries)||!Read(b,p.controller,0x38,p.index)||p.index<0||p.index>=p.entries.count)
  return fail("adoption_selected_entry_unavailable");
 const auto*entry=At(p.entries.data,static_cast<std::size_t>(p.index)*0x40);
 if(!ScopeAt(b,entry,0,p.selected)||!Read(b,entry,0x38,p.selected_mark)||p.selected_mark!=1||!HolyScope(p.selected,requested))
  return fail("adoption_selected_entry_scope_differs");
 if(!Read(b,b.selected_item_token,0,p.token)||!Array(b,p.context,0x28,p.dictionary))return fail("adoption_parameter_dictionary_unavailable");
 unsigned matches=0;
 for(std::int32_t i=0;i<p.dictionary.count;++i){NamedScope value{};const auto*row=At(p.dictionary.data,static_cast<std::size_t>(i)*24);
  if(!Read(b,row,0,value.key)||!ScopeAt(b,row,8,value.value))return fail("adoption_parameter_dictionary_unreadable");
  if(value.key==p.token){++matches;p.parameter=value.value;}p.parameters.push_back(value);
 }
 if(matches!=1||!HolyScope(p.parameter,requested)||p.parameter!=p.selected||!Site(b,requested))
  return fail("adoption_selected_item_parameter_or_full_reference_differs");
 return true;
}
bool CanConfirm(const AdoptionDetailBindings&b,const void*detail,bool&value)noexcept{
 if(!b.can_confirm)return false;
#if defined(_MSC_VER)
 __try{
#endif
 value=b.can_confirm(const_cast<void*>(detail));return true;
#if defined(_MSC_VER)
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
bool Confirm(const AdoptionDetailBindings&b,const void*detail,bool&attempted)noexcept{
 if(!b.confirm)return false;
#if defined(_MSC_VER)
 __try{
#endif
 attempted=true;b.confirm(const_cast<void*>(detail));return true;
#if defined(_MSC_VER)
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
bool Requirements(const AdoptionDetailBindings&b,std::uint8_t&raw)noexcept{
 if(!b.requirements_settings)return false;void*settings=nullptr;
#if defined(_MSC_VER)
 __try{settings=b.requirements_settings();}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 settings=b.requirements_settings();
#endif
 return settings&&Read(b,settings,0x10,raw);
}
struct NativeString{std::array<std::byte,32>bytes{};};
bool CallTooltip(NativeConfirmTooltip reader,const void*detail,NativeString&out)noexcept{
 if(!reader)return false;
#if defined(_MSC_VER)
 __try{return reader(const_cast<void*>(detail),out.bytes.data())==out.bytes.data();}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 return reader(const_cast<void*>(detail),out.bytes.data())==out.bytes.data();
#endif
}
bool DestroyString(const AdoptionDetailBindings&b,NativeString&out)noexcept{
 if(!b.destroy_string)return false;
#if defined(_MSC_VER)
 __try{b.destroy_string(out.bytes.data());return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 b.destroy_string(out.bytes.data());return true;
#endif
}
bool Tooltip(const AdoptionDetailBindings&b,const void*detail,std::string&out,NativeConfirmTooltip reader=nullptr){
 NativeString value{};if(!CallTooltip(reader?reader:b.confirm_tooltip,detail,value))return false;
 bool copied=false;
 try{
  const void*text=value.bytes.data();std::uint64_t size=0,capacity=0;
  if(Read(b,text,16,size)&&Read(b,text,24,capacity)&&size<=65536&&size<=capacity&&
   (capacity>=16||capacity==15)&&(capacity<16||Read(b,text,0,text))&&text){
   std::vector<char>bytes(static_cast<std::size_t>(size)+1);
   if(b.read_memory(b.read_context,text,bytes.data(),bytes.size())&&bytes.back()==0){out.assign(bytes.data(),static_cast<std::size_t>(size));copied=true;}
  }
 }catch(...){copied=false;}
 const bool destroyed=DestroyString(b,value);if(!copied||!destroyed)out.clear();return copied&&destroyed;
}
struct PlanningIdentity{
 Scope actor{};Header dictionary{};std::vector<NamedScope>parameters;
 const void*actor_object=nullptr;bool operator==(const PlanningIdentity&)const=default;
};
bool PlanningContext(const AdoptionDetailBindings&b,const Pass&p,std::uint32_t requested,PlanningIdentity&out){
 const auto*scope=At(p.detail,0xE0);
 if(!ScopeAt(b,scope,0,out.actor)||out.actor.kind!=4||out.actor.flags!=0||out.actor.payload!=p.actor||
    !Array(b,p.detail,0xF8,out.dictionary))return false;
 unsigned matches=0;
 for(std::int32_t i=0;i<out.dictionary.count;++i){NamedScope value{};const auto*row=At(out.dictionary.data,static_cast<std::size_t>(i)*24);
  if(!Read(b,row,0,value.key)||!ScopeAt(b,row,8,value.value))return false;
  if(value.key==p.token){++matches;if(!HolyScope(value.value,requested)||value.value!=p.parameter||value.value!=p.selected)return false;}
  out.parameters.push_back(value);
 }
 if(matches!=1)return false;
 // The exact4 production core resolver's full-reference storage contract.
 const void*storage=nullptr,*slots=nullptr;std::int32_t count=0,actual=-1;
 if(!Read(b,b.character_storage,0,storage)||!storage||
    !Read(b,storage,ck3_12004::kCharacterStorageCapacityOffset,count)||count<=0||
    !Read(b,storage,ck3_12004::kCharacterStorageSlotsOffset,slots)||!slots||
    (p.actor&0xFFFFFFU)>=static_cast<std::uint32_t>(count)||
    !Read(b,slots,static_cast<std::size_t>(p.actor&0xFFFFFFU)*ck3_12004::kCharacterStorageSlotStride+ck3_12004::kCharacterStorageObjectOffset,out.actor_object)||
    !Read(b,out.actor_object,ck3_12004::kCharacterFullIdOffset,actual)||actual!=static_cast<std::int32_t>(p.actor))return false;
 return true;
}
bool CostQuote(const AdoptionDetailBindings&b,const Pass&p,const PlanningIdentity&identity,std::array<std::int64_t,10>&values,bool&affordable)noexcept{
 if(!b.decision_cost||!b.evaluate_cost||!b.affordable_cost||!CostPlanningPins(b))return false;
#if defined(_MSC_VER)
 __try{
#endif
  const auto*cost=b.decision_cost(p.definition);if(!cost)return false;
  b.evaluate_cost(cost,At(p.detail,0xE0),values.data());
  affordable=b.affordable_cost(cost,At(p.detail,0xE0),identity.actor_object,nullptr);return true;
#if defined(_MSC_VER)
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
struct CooldownPass{
 const void*state=nullptr,*rows=nullptr,*clock=nullptr;
 std::int32_t count=0,mask=-1,current=0,expiry=0;std::uint8_t overflow=0;
 bool present=false;std::vector<std::byte>bytes;bool operator==(const CooldownPass&)const=default;
};
bool CallCooldownLookup(const AdoptionDetailBindings&b,const void*map,const void*definition,const std::int32_t*&expiry)noexcept{
#if defined(_MSC_VER)
 __try{expiry=b.cooldown_lookup(map,definition);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 expiry=b.cooldown_lookup(map,definition);return true;
#endif
}
bool Cooldown(const AdoptionDetailBindings&b,const Pass&p,const PlanningIdentity&identity,CooldownPass&out){
 if(!b.cooldown_lookup||!Pin(b,0x1A74790,"4c8bd90fb6c235c59d1c814c8bd24469c893010001488bc248c1e808440fb6c0")||
    !Pin(b,0x2957F10,"48895c241048897424185557415441564157488dac24b0fdffff4881ec50030000"))return false;
 if(!Read(b,identity.actor_object,0x1C0,out.state)||!out.state||!Read(b,b.decision_clock,0,out.clock)||
    !out.clock||!Read(b,out.clock,8,out.current))return false;
 const auto*map=At(out.state,0x430);
 if(!Read(b,map,8,out.rows)||!Read(b,map,0x10,out.count)||!Read(b,map,0x14,out.mask)||!Read(b,map,0x18,out.overflow)||
    out.count<0||out.count>65536||out.mask< -1||out.mask>65535)return false;
 // The original writer's live count is zero: observed absence, not a native
 // lookup on a null table (the original lookup has no empty fast-return).
 if(out.count==0)return true;
 const auto buckets=static_cast<std::uint32_t>(out.mask)+1U;
 if(!out.rows||out.mask<0||!buckets||(buckets&(buckets-1U))!=0||
    static_cast<std::uint32_t>(out.count)>buckets+out.overflow)return false;
 const auto capacity=static_cast<std::size_t>(buckets)+out.overflow;
 out.bytes.resize((capacity+1U)*0x18U);
 if(!b.read_memory(b.read_context,out.rows,out.bytes.data(),out.bytes.size())||out.bytes[capacity*0x18U+4]!=std::byte{0xFF})return false;
 const std::int32_t*expiry=nullptr;
 if(!CallCooldownLookup(b,map,p.definition,expiry))return false;
 if(!expiry)return true;
 const auto start=reinterpret_cast<std::uintptr_t>(out.rows),address=reinterpret_cast<std::uintptr_t>(expiry);
 if(address<start||address-start>=capacity*0x18U||(address-start)%0x18U!=0x10U)return false;
 const auto*row=At(expiry,0);const void*key=nullptr;
 // The returned pointer is row+0x10; RDX was the definition pointer VALUE.
 if(!Read(b,reinterpret_cast<const void*>(address-8),0,key)||key!=p.definition||!Read(b,row,0,out.expiry))return false;
 out.present=true;return true;
}
void Planning(const AdoptionDetailBindings&b,const Pass&p,std::uint32_t requested,AdoptionDetailSnapshot&out){
 PlanningIdentity before{},after{};
 if(!PlanningContext(b,p,requested,before)){out.native_planning_unavailable_reason="native_detail_scope_context_unverified";return;}
 out.native_detail_context_verified=true;
 if(TextPlanningPins(b)){
  if(b.requirements_description)out.native_requirements_description_available=Tooltip(b,p.detail,out.native_requirements_description,b.requirements_description);
  if(b.cost_description)out.native_cost_description_available=Tooltip(b,p.detail,out.native_cost_description,b.cost_description);
 }
 std::array<std::int64_t,10>first{},second{};bool first_afford=false,second_afford=false;
 const bool quote_before=CostQuote(b,p,before,first,first_afford);
 const bool quote_after=CostQuote(b,p,before,second,second_afford);
 out.native_resource_quote_available=quote_before&&quote_after&&first==second&&first_afford==second_afford;
 if(out.native_resource_quote_available){out.native_resource_vector_raw=first;out.native_affordable=first_afford;}
 CooldownPass cooldown_before{},cooldown_after{};
 out.native_decision_cooldown_observed=Cooldown(b,p,before,cooldown_before)&&Cooldown(b,p,before,cooldown_after)&&cooldown_before==cooldown_after;
 if(out.native_decision_cooldown_observed){out.native_decision_cooldown_present=cooldown_before.present;
  out.native_decision_clock_raw=cooldown_before.current;out.native_decision_expiry_raw=cooldown_before.expiry;
  out.native_decision_cooldown_active=cooldown_before.present&&cooldown_before.current<cooldown_before.expiry;}
 if(!PlanningContext(b,p,requested,after)||before!=after){
  out.native_detail_context_verified=false;out.native_requirements_description_available=false;out.native_cost_description_available=false;
  out.native_resource_quote_available=false;out.native_requirements_description.clear();out.native_cost_description.clear();
  out.native_decision_cooldown_observed=false;
  out.native_planning_unavailable_reason="native_detail_scope_context_changed";return;
 }
 if(!out.native_requirements_description_available||!out.native_cost_description_available||!out.native_resource_quote_available||!out.native_decision_cooldown_observed)
  out.native_planning_unavailable_reason="native_detail_planning_component_unavailable";
}
}
AdoptionDetailBindings BindHolySiteAdoptionDetailImage12004(std::uintptr_t base,std::string_view sha)noexcept{
 AdoptionDetailBindings b{};if(!base||sha!=ck3_12004::kExecutableSha256)return b;
 b.enabled=true;b.image_base=base;b.holy_site_storage=reinterpret_cast<void**>(base+0x5D1DE80);
 b.selected_item_token=reinterpret_cast<const std::uint32_t*>(base+0x5D4C2EC);
 b.current_actor_reference=reinterpret_cast<const std::uint32_t*>(base+0x54DBC00);b.read_memory=&ProcessRead;
 b.can_confirm=reinterpret_cast<NativeCanConfirm>(base+0x1471140);b.confirm=reinterpret_cast<NativeConfirm>(base+0x1471190);
 b.requirements_settings=reinterpret_cast<NativeRequirementsSettings>(base+0xA75D00);
 b.confirm_tooltip=reinterpret_cast<NativeConfirmTooltip>(base+0x1471150);
 b.requirements_description=reinterpret_cast<NativeConfirmTooltip>(base+0x1470BF0);
 b.cost_description=reinterpret_cast<NativeConfirmTooltip>(base+0x1470DF0);
 b.decision_cost=reinterpret_cast<NativeDecisionCost>(base+0x14706B0);
 b.evaluate_cost=reinterpret_cast<NativeCostEvaluate>(base+0x310CE50);
 b.affordable_cost=reinterpret_cast<NativeCostAffordable>(base+0x310B390);
 b.character_storage=reinterpret_cast<void**>(base+ck3_12004::kCharacterStorageSlotRva);
 b.decision_clock=reinterpret_cast<void**>(base+0x5C68C50);
 b.cooldown_lookup=reinterpret_cast<NativeCooldownLookup>(base+0x1A74790);
 b.destroy_string=reinterpret_cast<NativeStringDestroy>(base+0x856050);return b;
}
bool ReadHolySiteAdoptionDetail12004(const AdoptionDetailBindings&b,const void*owner,
 const ck3_12002::religion::Context&context,std::uint32_t requested,AdoptionDetailSnapshot&out)noexcept{
 out={};out.owner=owner;out.capture_epoch=context.capture_epoch;out.date_raw=context.date_raw;
 out.played_character_id=context.played_character_id;out.requested_holy_site_id=requested;
 try{
  if(!b.enabled||!b.image_base||!b.read_memory||!context.available||!context.capture_epoch||context.played_character_id<=0||requested==absent){out.unavailable_reason="adoption_current_player_context_unavailable";return false;}
  if(!Pins(b)){out.unavailable_reason="adoption_loaded_native_source_pins_changed";return false;}
  Pass first{},second{};bool before=false,after=false;std::uint8_t bypass_before=0,bypass_after=0;
  if(!ReadPass(b,owner,requested,context.played_character_id,first,out.unavailable_reason))return false;
  if(!CanConfirm(b,first.detail,before)){out.unavailable_reason="adoption_native_can_confirm_unavailable";return false;}
  const bool bypass_observed=Requirements(b,bypass_before);
  out.confirm_tooltip_available=Tooltip(b,first.detail,out.confirm_tooltip);
  Planning(b,first,requested,out);
  if(!ReadPass(b,owner,requested,context.played_character_id,second,out.unavailable_reason))return false;
  if(first!=second||!CanConfirm(b,second.detail,after)||before!=after){out.unavailable_reason="adoption_detail_or_native_legality_changed";return false;}
  const bool bypass_after_observed=Requirements(b,bypass_after);
  if(bypass_observed!=bypass_after_observed||(bypass_observed&&bypass_before!=bypass_after)){
   out.unavailable_reason="adoption_requirements_bypass_changed";return false;
  }
  out.detail_present=true;out.root_present=first.root!=nullptr;out.detail_actor_id=first.actor;out.current_actor_id=first.current_actor;
  out.decision_option_id=first.option;out.decision_key=first.key;out.selected_index=first.index;
  out.candidate_count=static_cast<std::uint32_t>(first.entries.count);out.selected_item_token=first.token;
  out.parameter_holy_site_id=static_cast<std::uint32_t>(first.parameter.payload);out.selected_holy_site_id=static_cast<std::uint32_t>(first.selected.payload);
  out.native_can_confirm=before;out.bypass_requirements_observed=bypass_observed;out.bypass_requirements_raw=bypass_before;
  out.parameter_and_selection_match=true;out.detail=first.detail;out.root=first.root;
  out.controller=first.controller;out.context=first.context;out.available=true;return true;
 }catch(...){out.unavailable_reason="adoption_detail_capture_exception";return false;}
}
bool ConfirmHolySiteAdoptionDetail12004(const AdoptionDetailBindings&b,
 const AdoptionDetailSnapshot&prior,bool&attempted)noexcept{
 attempted=false;if(!prior.available||!prior.native_can_confirm||!prior.parameter_and_selection_match||!prior.native_detail_context_verified||
  !prior.bypass_requirements_observed||prior.bypass_requirements_raw!=0)return false;
 ck3_12002::religion::Context frame{};frame.available=true;frame.capture_epoch=prior.capture_epoch;
 frame.date_raw=prior.date_raw;frame.played_character_id=prior.played_character_id;AdoptionDetailSnapshot current{};
 if(!ReadHolySiteAdoptionDetail12004(b,prior.owner,frame,prior.requested_holy_site_id,current)||!current.native_can_confirm||!current.native_detail_context_verified||
  !current.bypass_requirements_observed||current.bypass_requirements_raw!=0||
  current.detail!=prior.detail||current.root!=prior.root||current.controller!=prior.controller||current.context!=prior.context)return false;
 return Confirm(b,current.detail,attempted);
}
}
