#include "xar_bridge/holy_site_creation12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/holy_site_creation12004_source_pins.hpp"
#include <windows.h>
#include <algorithm>
#include <cstring>
#include <limits>

namespace xar::ck3_12004::religion::holy_site_creation {
namespace {
constexpr std::uint32_t absent=0xFFFFFFFFU;
constexpr std::size_t max_rows=16384;
const void*At(const void*p,std::size_t n) noexcept {
 auto a=reinterpret_cast<std::uintptr_t>(p);
 return a&&n<=std::numeric_limits<std::uintptr_t>::max()-a?reinterpret_cast<const void*>(a+n):nullptr;
}
template<class T>bool Read(const Bindings&b,const void*p,std::size_t n,T&v) noexcept {
 auto*q=At(p,n);return q&&b.read_memory&&b.read_memory(b.read_context,q,&v,sizeof(v));
}
bool ProcessRead(void*,const void*p,void*out,std::size_t n) noexcept {
 SIZE_T got=0;return p&&out&&n&&ReadProcessMemory(GetCurrentProcess(),p,out,n,&got)&&got==n;
}
bool Pins(const Bindings&b) noexcept {
 if(!b.enabled||!b.image_base||!b.read_memory)return false;
 for(const auto&p:source::pins){
  std::array<unsigned char,32>raw{};
  if(!b.read_memory(b.read_context,reinterpret_cast<const void*>(b.image_base+p.rva),raw.data(),p.size)||raw!=p.bytes)return false;
 }
 return true;
}
bool TypedWindow(const Bindings&b,const void*w) noexcept {
 std::uintptr_t vt=0,second=0,col=0;std::uint32_t sig=0,offset=1,td=0,self=0;
 return Read(b,w,0,vt)&&vt==b.image_base+0x4593690&&
  Read(b,w,0x10,second)&&second==b.image_base+0x4593760&&
  Read(b,reinterpret_cast<const void*>(vt-8),0,col)&&col>=b.image_base&&
  Read(b,reinterpret_cast<const void*>(col),0,sig)&&sig==1&&
  Read(b,reinterpret_cast<const void*>(col),4,offset)&&offset==0&&
  Read(b,reinterpret_cast<const void*>(col),12,td)&&td==0x57EC440&&
  Read(b,reinterpret_cast<const void*>(col),20,self)&&col==b.image_base+self;
}
const void*Resolve(const Bindings&b,std::uintptr_t global,std::uint32_t id,std::size_t id_offset) noexcept {
 const void*storage=nullptr,*rows=nullptr,*object=nullptr;std::uint32_t count=0,actual=absent;
 if(id==absent||!Read(b,reinterpret_cast<const void*>(b.image_base+global),0,storage)||!storage||
  !Read(b,storage,0x20,rows)||!rows||!Read(b,storage,0x2C,count)||(id&0xFFFFFFU)>=count||
  !Read(b,rows,static_cast<std::size_t>(id&0xFFFFFFU)*16+8,object)||!object||
  !Read(b,object,id_offset,actual)||actual!=id)return nullptr;
 return object;
}
bool CString(const Bindings&b,const void*value,std::string&out,std::size_t bound) {
 std::uint64_t size=0,capacity=0;const void*text=value;
 if(!Read(b,value,0x10,size)||!Read(b,value,0x18,capacity)||size>bound||size>capacity)return false;
 if(capacity>=16&&(!Read(b,value,0,text)||!text))return false;
 out.resize(static_cast<std::size_t>(size));
 return size==0||b.read_memory(b.read_context,text,out.data(),out.size());
}
bool TypeKey(const Bindings&b,const void*object,std::string&key) {
 std::uint32_t magic=0;
 return object&&Read(b,object,0x38,magic)&&magic==0x4744624FU&&CString(b,At(object,0x18),key,160);
}
template<class T>bool Vector(const Bindings&b,const void*window,std::size_t offset,std::vector<T>&out) {
 const void*rows=nullptr;std::int32_t capacity=0,count=0;
 if(!Read(b,window,offset,rows)||!Read(b,window,offset+8,capacity)||!Read(b,window,offset+12,count)||
  capacity<0||count<0||count>capacity||static_cast<std::size_t>(count)>max_rows||(!rows&&count))return false;
 out.resize(static_cast<std::size_t>(count));
 return out.empty()||b.read_memory(b.read_context,rows,out.data(),out.size()*sizeof(T));
}
struct Window {
 const void*window=nullptr,*root=nullptr,*gfx=nullptr;
 bool operator==(const Window&)const=default;
};
bool GetWindow(const Bindings&b,const void*handler,Window&v) noexcept {
 const void*owner=nullptr;
 return Read(b,handler,0x5E8,v.window)&&v.window&&TypedWindow(b,v.window)&&
  Read(b,v.window,0xA0,owner)&&owner==handler&&Read(b,v.window,0x98,v.gfx)&&v.gfx&&
  Read(b,v.window,0x60,v.root);
}
struct Raw {
 Window w{};
 std::uint32_t actor=absent,faith=absent,barony=absent;
 const void*type=nullptr;
 std::vector<const void*>types;
 std::vector<std::uint32_t>baronies,artifacts,selected;
 std::array<std::int64_t,10>quote{};
 bool operator==(const Raw&)const=default;
};
bool ReadRaw(const Bindings&b,const void*handler,const ck3_12002::religion::Context&ctx,Raw&v) {
 if(!ctx.available||ctx.played_character_id==-1||!ctx.faith_id||*ctx.faith_id==absent||
  !GetWindow(b,handler,v.w)||!Read(b,reinterpret_cast<const void*>(b.image_base+0x54DBC00),0,v.actor)||
  v.actor!=static_cast<std::uint32_t>(ctx.played_character_id)||
  !Read(b,v.w.window,0xC8,v.faith)||v.faith!=*ctx.faith_id||
  !Read(b,v.w.window,0xD0,v.type)||!Read(b,v.w.window,0xD8,v.barony)||
  !Vector(b,v.w.window,0x130,v.types)||!Vector(b,v.w.window,0x100,v.baronies)||
  !Vector(b,v.w.window,0x118,v.artifacts)||!Vector(b,v.w.window,0xE0,v.selected)||
  !Read(b,v.w.window,0x178,v.quote))return false;
 const auto*faith=Resolve(b,0x5D1E300,v.faith,8);std::uint32_t magic=0;
 if(!faith||!Read(b,faith,0xC,magic)||magic!=0x46616974U)return false;
 for(const auto*ids:{&v.baronies,&v.artifacts,&v.selected})
  if(std::find(ids->begin(),ids->end(),absent)!=ids->end())return false;
 return true;
}
bool Destroy(const Bindings&b,void*str) noexcept {
 if(!b.destroy_string)return false;
#if defined(_MSC_VER)
 __try {b.destroy_string(str);return true;} __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 b.destroy_string(str);return true;
#endif
}
bool Enabled(const Bindings&b,void*w,bool&value) noexcept {
 if(!b.native_enabled)return false;
#if defined(_MSC_VER)
 __try {value=b.native_enabled(w);return true;} __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 value=b.native_enabled(w);return true;
#endif
}
bool Settings(const Bindings&b,std::uint8_t&value) noexcept {
 if(!b.requirements_settings)return false;void*settings=nullptr;
#if defined(_MSC_VER)
 __try {settings=b.requirements_settings();} __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 settings=b.requirements_settings();
#endif
 return settings&&Read(b,settings,0x10,value);
}
bool Rarity(const Bindings&b,void*w,std::int64_t&value) noexcept {
 if(!b.rarity_sum)return false;std::int64_t*result=nullptr;
#if defined(_MSC_VER)
 __try {result=b.rarity_sum(w,&value);} __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 result=b.rarity_sum(w,&value);
#endif
 return result==&value;
}
bool TooltipCall(const Bindings&b,void*w,void*out) noexcept {
 if(!b.create_tooltip)return false;
#if defined(_MSC_VER)
 __try {return b.create_tooltip(w,out)==out;} __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 return b.create_tooltip(w,out)==out;
#endif
}
bool CanPickCall(const Bindings&b,void*w,const void*type,void*reason,bool&value) noexcept {
 if(!b.can_pick_type)return false;
#if defined(_MSC_VER)
 __try {value=b.can_pick_type(w,type,reason);return true;} __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 value=b.can_pick_type(w,type,reason);return true;
#endif
}
bool SelectCall(NativeSelect call,void*w,const void*subject,bool&attempted) noexcept {
 if(!call)return false;
#if defined(_MSC_VER)
 __try {attempted=true;call(w,subject);return true;} __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 attempted=true;call(w,subject);return true;
#endif
}
struct Any {void*type=nullptr;std::array<unsigned char,32>data{};};
static_assert(sizeof(Any)==40);
bool OpenCall(const Bindings&b,void*handler,std::uint32_t faith,bool&attempted) noexcept {
 if(!b.faith_any_type||!b.open_view)return false;Any value{};
#if defined(_MSC_VER)
 __try {
#endif
  value.type=b.faith_any_type();std::uintptr_t vt=0;
  if(reinterpret_cast<std::uintptr_t>(value.type)!=b.image_base+0x54D70F8||
   !Read(b,value.type,0,vt)||vt!=b.image_base+0x44B92F0)return false;
  for(const auto&edge:std::array<std::pair<std::size_t,std::uintptr_t>,6>{{
    {0x18,0x8522C0},{0x28,0x876E00},{0x38,0x877200},
    {0x50,0xB1AA90},{0x58,0x8771F0},{0x60,0x8771F0}}}){
    std::uintptr_t target=0;
    if(!Read(b,reinterpret_cast<const void*>(vt),edge.first,target)||target!=b.image_base+edge.second)return false;
   }
   std::memcpy(value.data.data(),&faith,4);attempted=true;b.open_view(handler,0xAA,&value);return true;
#if defined(_MSC_VER)
 } __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
}
Bindings BindImage12004(std::uintptr_t base,std::string_view sha) noexcept {
 Bindings b{};if(!base||sha!=ck3_12004::kExecutableSha256)return b;
 b.enabled=true;b.image_base=base;b.read_memory=&ProcessRead;
 b.native_enabled=reinterpret_cast<NativeEnabled>(base+0x17E9A70);
 b.create_tooltip=reinterpret_cast<NativeTooltip>(base+0x17E9050);
 b.destroy_string=reinterpret_cast<NativeDestroyString>(base+0x856050);
 b.can_pick_type=reinterpret_cast<NativeCanPick>(base+0x17EAE10);
 b.rarity_sum=reinterpret_cast<NativeRarity>(base+0x17EA9D0);
 b.requirements_settings=reinterpret_cast<NativeSettings>(base+0xA75D00);
 b.select_type=reinterpret_cast<NativeSelect>(base+0x17E97D0);
 b.select_barony=reinterpret_cast<NativeSelect>(base+0x17E9890);
 b.select_artifact=reinterpret_cast<NativeSelect>(base+0x17E9940);
 b.faith_any_type=reinterpret_cast<NativeAnyType>(base+0xB19AD0);
 b.open_view=reinterpret_cast<NativeOpenView>(base+0xAF39E0);return b;
}
bool ReadContext12004(const Bindings&b,const void*handler,const ck3_12002::religion::Context&ctx,Snapshot&out) noexcept {
 out={};out.capture_epoch=ctx.capture_epoch;out.date_raw=ctx.date_raw;out.played_character_id=ctx.played_character_id;
 if(ctx.faith_id)out.player_faith_id=*ctx.faith_id;
 auto fail=[&](const char*why){out.available=false;out.unavailable_reason=why;return false;};
 try {
  if(!Pins(b))return fail("holy_site_creation_loaded_source_pins_changed");
  Raw first{},second{};
  if(!ReadRaw(b,handler,ctx,first))return fail("holy_site_creation_window_or_models_unavailable");
  out.handler=handler;out.window=first.w.window;out.root=first.w.root;out.gfx=first.w.gfx;
  out.window_present=true;out.root_present=first.w.root!=nullptr;out.window_faith_id=first.faith;out.player_faith_matches=true;
  for(const auto*type:first.types){
   TypeCandidate row{};row.native_type=type;
   std::uint8_t dynamic=0;
   if(!TypeKey(b,type,row.type_key)||row.type_key.empty()||!Read(b,type,0x418,dynamic)||dynamic==0)
    return fail("holy_site_creation_native_type_row_unavailable");
   row.is_selected=type==first.type;
   alignas(8)std::array<unsigned char,32>reason{};reason[24]=15;
   row.native_can_pick_observed=CanPickCall(b,const_cast<void*>(first.w.window),type,reason.data(),row.native_can_pick);
   if(row.native_can_pick_observed){
    row.tooltip_available=CString(b,reason.data(),row.tooltip,16384);
    if(!Destroy(b,reason.data()))return fail("holy_site_creation_type_reason_cleanup_failed");
   }
   out.available_holy_site_types.push_back(std::move(row));
  }
  std::string selected_key;
  if(first.type){
    if(!TypeKey(b,first.type,selected_key)||selected_key.empty())return fail("holy_site_creation_selected_type_unavailable");
    out.selected_type_key=std::move(selected_key);
   }
  if(first.barony!=absent)out.selected_barony_title_id=first.barony;
  out.potential_barony_title_ids=first.baronies;out.enshrinable_artifact_ids=first.artifacts;
  out.selected_artifact_ids=first.selected;
  out.native_rarity_sum_observed=Rarity(b,const_cast<void*>(first.w.window),out.native_rarity_sum_raw);
  out.bypass_requirements_observed=Settings(b,out.bypass_requirements_raw);
  out.native_enabled_observed=Enabled(b,const_cast<void*>(first.w.window),out.native_create_button_enabled);
  alignas(8)std::array<unsigned char,32>text{};
  if(TooltipCall(b,const_cast<void*>(first.w.window),text.data())){
   out.create_tooltip_available=CString(b,text.data(),out.create_tooltip,32768);
   if(!Destroy(b,text.data()))return fail("holy_site_creation_create_reason_cleanup_failed");
  }
  if(!ReadRaw(b,handler,ctx,second)||first!=second)return fail("holy_site_creation_context_changed_during_read");
  std::uint8_t after_bypass=0;
  if(out.bypass_requirements_observed&&(!Settings(b,after_bypass)||after_bypass!=out.bypass_requirements_raw))
   return fail("holy_site_creation_requirements_setting_changed");
  out.cached_resource_vector_raw=first.quote;out.cached_resource_quote_available=true;
  out.models_available=true;out.models_complete=true;out.selection_available=true;out.available=true;return true;
 }catch(...){return fail("holy_site_creation_host_read_exception");}
}
bool InvokeUi12004(const Bindings&b,void*handler,const ck3_12002::religion::Context&ctx,const UiRequest&request,
 bool&attempted,bool&already,std::string&failure) noexcept {
 attempted=false;already=false;failure.clear();
 try {
  if(!Pins(b)||!ctx.available||ctx.played_character_id==-1||!ctx.faith_id||*ctx.faith_id==absent){
   failure="holy_site_creation_ui_context_unavailable";return false;
  }
  if(request.action==UiAction::open){
   Window first{},second{};
   if(!GetWindow(b,handler,first)||!GetWindow(b,handler,second)||first!=second){
    failure="holy_site_creation_registered_window_unverified";return false;
   }
   const auto*faith=Resolve(b,0x5D1E300,*ctx.faith_id,8);std::uint32_t magic=0,current=absent;
   if(!faith||!Read(b,faith,0xC,magic)||magic!=0x46616974U||
    !Read(b,reinterpret_cast<const void*>(b.image_base+0x54DBC00),0,current)||current!=static_cast<std::uint32_t>(ctx.played_character_id)){
    failure="holy_site_creation_current_player_or_faith_changed";return false;
   }
   const bool ok=OpenCall(b,handler,*ctx.faith_id,attempted);
    if(!ok)failure=attempted?"holy_site_creation_open_dispatch_result_unknown":"holy_site_creation_open_typed_arguments_unverified";
    return ok;
  }
  Snapshot current{};
  if(!ReadContext12004(b,handler,ctx,current)){failure=current.unavailable_reason;return false;}
  auto*w=const_cast<void*>(current.window);
  if(request.action==UiAction::select_type){
   const TypeCandidate*match=nullptr;
   for(const auto&row:current.available_holy_site_types)if(row.type_key==request.type_key){
    if(match){failure="holy_site_creation_type_key_ambiguous";return false;}match=&row;
   }
   if(!match){failure="holy_site_creation_type_not_native_candidate";return false;}
   if(match->is_selected){already=true;return true;}
   if(!match->native_can_pick_observed||!match->native_can_pick){failure="holy_site_creation_type_not_pickable";return false;}
   return SelectCall(b.select_type,w,match->native_type,attempted);
  }
  if(request.action==UiAction::select_barony){
    if(request.object_id==absent){failure="holy_site_creation_barony_reference_absent";return false;}
   if(current.selected_barony_title_id==request.object_id){already=true;return true;}
   if(std::find(current.potential_barony_title_ids.begin(),current.potential_barony_title_ids.end(),request.object_id)==current.potential_barony_title_ids.end()){
    failure="holy_site_creation_barony_not_native_candidate";return false;
   }
   const auto*object=Resolve(b,0x5D1DAF8,request.object_id,0x10);std::uint32_t magic=0,rank=0;const void*definition=nullptr;
   if(!object||!Read(b,object,0x14,magic)||magic!=0x4C616E64U||!Read(b,object,0x48,definition)||
    !Read(b,definition,0x64,rank)||rank!=1){failure="holy_site_creation_barony_reference_changed";return false;}
   return SelectCall(b.select_barony,w,object,attempted);
  }
  if(request.action==UiAction::set_artifact){
    if(request.object_id==absent){failure="holy_site_creation_artifact_reference_absent";return false;}
   const bool selected=std::find(current.selected_artifact_ids.begin(),current.selected_artifact_ids.end(),request.object_id)!=current.selected_artifact_ids.end();
   if(selected==request.selected){already=true;return true;}
   if(request.selected&&std::find(current.enshrinable_artifact_ids.begin(),current.enshrinable_artifact_ids.end(),request.object_id)==current.enshrinable_artifact_ids.end()){
    failure="holy_site_creation_artifact_not_native_candidate";return false;
   }
   const auto*object=Resolve(b,0x5D1DE68,request.object_id,0x10);std::uint32_t magic=0;
   if(!object||!Read(b,object,0x14,magic)||magic!=0x41727469U){failure="holy_site_creation_artifact_reference_changed";return false;}
   return SelectCall(b.select_artifact,w,object,attempted);
  }
  failure="holy_site_creation_ui_action_unknown";return false;
 }catch(...){failure="holy_site_creation_ui_host_exception";return false;}
}
}
