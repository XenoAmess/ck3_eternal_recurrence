#include <chrono>
#include "xar_bridge/ck3_121003_decisions_close26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_rmtm_decision26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_aub_decision_abi26785313_v1.hpp"
#include "xar_bridge/ck3_121003_aub_decision26785313_pins_v1.hpp"
#include "xar_bridge/ck3_121003_gui_controls26785313_pins_v2.hpp"
#include <algorithm>
#include <chrono>
#include <cstring>
#include <limits>
#include <unordered_set>
#include <windows.h>
#include "xar_bridge/ck3_121003_ccc_tooltip26785313_pins_v1.hpp"
#include "xar_bridge/ck3_121003_rmtm_owner26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
namespace {
namespace abi=aub_decision_abi;
[[maybe_unused]]bool Alive(std::uint64_t mono);
#ifndef XAR_RMTM_TOOLTIP_CALL_ADDRESS
#define XAR_RMTM_TOOLTIP_CALL_ADDRESS(image,rva) ((image)+(rva))
#endif
[[maybe_unused]]bool RmtmTooltipBytes267V1(std::uintptr_t p,void*out,std::size_t n)noexcept{if(!p||!out||!n)return false;__try{std::memcpy(out,reinterpret_cast<const void*>(p),n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool RmtmDecisionDeadline267V1(std::uint64_t wall,std::uint64_t mono)noexcept{const auto now=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return wall&&mono&&now>0&&static_cast<std::uint64_t>(now)<wall&&GetTickCount64()<mono;}
[[maybe_unused]]bool RmtmTooltipUtf8267V1(std::string_view text)noexcept{
 if(text.size()>16384)return false;
 for(std::size_t i=0;i<text.size();){const auto c=static_cast<unsigned char>(text[i++]);std::uint32_t value=0;unsigned count=0;if(c<0x80)value=c;else if(c>=0xC2&&c<=0xDF){value=c&31;count=1;}else if(c>=0xE0&&c<=0xEF){value=c&15;count=2;}else if(c>=0xF0&&c<=0xF4){value=c&7;count=3;}else return false;if(i+count>text.size())return false;for(unsigned n=0;n<count;++n){const auto v=static_cast<unsigned char>(text[i++]);if((v&0xC0)!=0x80)return false;value=(value<<6)|(v&63);}if((count==1&&value<0x80)||(count==2&&value<0x800)||(count==3&&value<0x10000)||value>0x10FFFF||(value>=0xD800&&value<=0xDFFF))return false;}return true;
}
[[maybe_unused]]bool RmtmTooltipPins267V1(std::uintptr_t image)noexcept{
 std::array<std::byte,4096>sample{};for(const auto&p:ccc_tooltip_pins::kPins){if(p.bytes.empty()||p.bytes.size()>sample.size()||p.rva>kImageSize-p.bytes.size()||!RmtmTooltipBytes267V1(image+p.rva,sample.data(),p.bytes.size())||std::memcmp(sample.data(),p.bytes.data(),p.bytes.size()))return false;}return true;
}
[[maybe_unused]]bool ReadRmtmConfirmTooltip267V1(std::uintptr_t image,std::uintptr_t detail,std::uint64_t wall,std::uint64_t mono,std::string&text,bool&clean,bool&entered)noexcept{
 text.clear();clean=true;entered=false;if(!image||!detail||!RmtmDecisionDeadline267V1(wall,mono)||!RmtmTooltipPins267V1(image))return false;
 alignas(std::uintptr_t)std::array<std::byte,32>value{};const std::uint64_t initialcap=15;std::memcpy(value.data()+24,&initialcap,8);
 bool returned=false,valid=false,destroyed=false;entered=true;clean=false;
 __try{
  using Getter=void*(__fastcall*)(const void*,void*);
  returned=reinterpret_cast<Getter>(XAR_RMTM_TOOLTIP_CALL_ADDRESS(image,0x1603C90))(reinterpret_cast<const void*>(detail),value.data())==value.data();
  if(returned&&RmtmDecisionDeadline267V1(wall,mono)){
   std::uint64_t length=0,capacity=0;std::uintptr_t data=reinterpret_cast<std::uintptr_t>(value.data());std::memcpy(&length,value.data()+16,8);std::memcpy(&capacity,value.data()+24,8);
   if(length<=16384&&capacity>=length&&(capacity==15||capacity>=16)&&capacity<=0x10000000){if(capacity>=16)std::memcpy(&data,value.data(),8);std::array<char,16385>bytes{};if(RmtmTooltipBytes267V1(data,bytes.data(),static_cast<std::size_t>(length)+1)&&!bytes[static_cast<std::size_t>(length)]){text.assign(bytes.data(),static_cast<std::size_t>(length));valid=RmtmTooltipUtf8267V1(text);}}
  }
 }__except(EXCEPTION_EXECUTE_HANDLER){returned=false;}
 // Even expired/partial owned output gets the official destructor; no borrowed text survives.
 __try{using Dtor=void(__fastcall*)(void*);reinterpret_cast<Dtor>(XAR_RMTM_TOOLTIP_CALL_ADDRESS(image,0x897460))(value.data());destroyed=true;}__except(EXCEPTION_EXECUTE_HANDLER){destroyed=false;}
 clean=returned&&destroyed;if(!clean||!valid||!RmtmDecisionDeadline267V1(wall,mono)){text.clear();return false;}return true;
}


using ck3_1210::GuiControlCallbackV1;
[[maybe_unused]]bool Bytes(std::uintptr_t p,void*out,std::size_t n)noexcept{if(!p||!out||!n||n-1>(std::numeric_limits<std::uintptr_t>::max)()-p)return false;__try{std::memcpy(out,reinterpret_cast<const void*>(p),n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
template<class T>bool At(std::uintptr_t p,std::size_t off,T&v)noexcept{return p&&off<=(std::numeric_limits<std::uintptr_t>::max)()-p&&Bytes(p+off,&v,sizeof(v));}
[[maybe_unused]]bool Typed(std::uintptr_t p,std::uintptr_t image,std::uintptr_t vt){std::uintptr_t actual=0;return At(p,0,actual)&&actual==image+vt;}
[[maybe_unused]]bool Alive(std::uint64_t mono){return mono&&GetTickCount64()<mono;}
[[maybe_unused]]bool Add(std::vector<std::byte>&out,std::uintptr_t p,std::size_t n){if(n>256*1024||out.size()>256*1024-n)return false;const auto i=out.size();out.resize(i+n);return !n||Bytes(p,out.data()+i,n);}
[[maybe_unused]]bool CStringKey(std::uintptr_t p,std::string&out,std::vector<std::byte>&proof){std::array<std::byte,32>a{},z{};if(!Bytes(p,a.data(),32))return false;std::uint64_t n=0,cap=0;std::uintptr_t data=p;std::memcpy(&n,a.data()+16,8);std::memcpy(&cap,a.data()+24,8);if(n>192||n>cap||(cap<16&&cap!=15)||cap>0x1000000)return false;if(cap>=16)std::memcpy(&data,a.data(),8);std::array<char,193>text{};if(!Bytes(data,text.data(),static_cast<std::size_t>(n)+1)||text[n]||!Bytes(p,z.data(),32)||a!=z)return false;for(std::size_t i=0;i<n;++i)if(!((text[i]>='a'&&text[i]<='z')||(text[i]>='A'&&text[i]<='Z')||(text[i]>='0'&&text[i]<='9')||text[i]=='_'))return false;out.assign(text.data(),static_cast<std::size_t>(n));return Add(proof,p,32)&&Add(proof,data,static_cast<std::size_t>(n)+1);}
template<class T>bool AppendCuratedModelValue267V1(std::vector<std::byte>&out,const T&v){if(out.size()>256*1024-sizeof(v))return false;const auto p=out.size();out.resize(p+sizeof(v));std::memcpy(out.data()+p,&v,sizeof(v));return true;}
[[maybe_unused]]bool AppendCuratedModelRow267V1(std::vector<std::byte>&out,std::uintptr_t definition,std::uint32_t actor,std::uintptr_t owner,std::uint8_t state){return AppendCuratedModelValue267V1(out,definition)&&AppendCuratedModelValue267V1(out,actor)&&AppendCuratedModelValue267V1(out,owner)&&AppendCuratedModelValue267V1(out,state);}
[[maybe_unused]]bool Header(std::uintptr_t p,std::uintptr_t&data,std::int32_t&count,std::size_t max,std::vector<std::byte>&proof,bool semantic=false){std::int32_t cap=0;return At(p,0,data)&&At(p,8,cap)&&At(p,12,count)&&count>=0&&static_cast<std::size_t>(count)<=max&&cap>=count&&cap<=0x1000000&&(!count||data)&&(semantic?AppendCuratedModelValue267V1(proof,count):Add(proof,p,16));}
[[maybe_unused]]bool Window(const RmtmDecisionScene267V1&e,std::uintptr_t image,std::uintptr_t p,std::uintptr_t vt,std::uintptr_t secondary,std::uintptr_t root){std::uintptr_t v=0;return Typed(p,image,vt)&&At(p,0x10,v)&&v==image+secondary&&At(p,abi::kWindowJomini,v)&&v==e.jomini&&At(p,abi::kWindowHandler,v)&&v==e.handler&&At(p,abi::kWindowGuiContext,v)&&v==e.context&&At(p,abi::kWindowRoot,v)&&v==root;}
[[maybe_unused]]bool Modal(std::uintptr_t ctx,RmtmDecisionRaw267V1&out){std::uintptr_t data=0;std::int32_t count=0;if(!Header(ctx+0x298,data,count,64,out.modal_source))return false;for(std::int32_t i=0;i<count;++i){std::uintptr_t modal=0;std::uint8_t flags=0;if(!At(data,static_cast<std::size_t>(i)*8,modal)||!At(modal,0xD0,flags)||!Add(out.modal_source,data+static_cast<std::size_t>(i)*8,8)||!Add(out.modal_source,modal+0xD0,1))return false;if((flags&8)==0)out.source.blocked_by_visible_modal=true;}return true;}
[[maybe_unused]]bool NativeCan(std::uintptr_t image,std::uintptr_t detail,bool&out)noexcept{using Fn=bool(__fastcall*)(const void*);__try{out=reinterpret_cast<Fn>(image+abi::kCanConfirm)(reinterpret_cast<const void*>(detail));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]RmtmDecisionRawCall267V1 Native(std::uintptr_t image,std::uintptr_t receiver,RmtmDecisionAction267V1 action,std::uintptr_t manager)noexcept{
 RmtmDecisionRawCall267V1 out;alignas(void*)std::array<std::byte,32>text{};alignas(void*)std::array<std::byte,0x50>pimpl{};const std::uint64_t cap=15;std::memcpy(text.data()+24,&cap,8);std::memcpy(pimpl.data()+0x48,&receiver,8);out.effect_entered=true;out.status=RmtmDecisionRawCallStatus267V1::indeterminate;out.cleanup_known=false;
 __try{if(action==RmtmDecisionAction267V1::open_list){using Fn=bool(__fastcall*)(void*,std::int32_t,void*,void*);out.native_handled=reinterpret_cast<Fn>(image+0x4089380)(reinterpret_cast<void*>(manager),0,text.data(),pimpl.data());}
 else{using Fn=void(__fastcall*)(void*);reinterpret_cast<Fn>(image+(action==RmtmDecisionAction267V1::open_detail?abi::kRowSelect:abi::kConfirm))(reinterpret_cast<void*>(receiver));}out.status=RmtmDecisionRawCallStatus267V1::returned;out.cleanup_known=true;return out;}__except(EXCEPTION_EXECUTE_HANDLER){return out;}
}
[[maybe_unused]]bool InImage(std::uintptr_t image,std::uintptr_t p,std::size_t n){return p>=image&&n<=kImageSize&&p-image<=kImageSize-n;}
[[maybe_unused]]bool SourceVector(std::uintptr_t object,std::size_t offset,std::size_t stride,
    std::vector<std::byte> &out,bool nested_chain=false) {
  std::uintptr_t data=0;std::int32_t capacity=0,count=0;
  if(!At(object,offset,data) || !At(object,offset+8,capacity) || !At(object,offset+12,count) ||
      count<0 || count>64 || capacity<count || (count && !data))return false;
  const auto start=out.size(),size=static_cast<std::size_t>(count)*stride;
  if(start>65536||size>65536-start)return false;
  out.resize(start+size);if(size && !Bytes(data,out.data()+start,size))return false;
  if(nested_chain)for(std::int32_t i=0;i<count;++i)
    if(!SourceVector(data,static_cast<std::size_t>(i)*stride,0x18,out))return false;
  return true;
}
[[maybe_unused]]bool CallbackGroup(std::uintptr_t image,std::uintptr_t widget,std::size_t group,
    std::vector<GuiControlCallbackV1> &out,bool &proven) {
  std::int32_t count=0,capacity=0;std::uintptr_t data=0;
  if(!At(widget,group,data) || !At(widget,group+8,capacity) || !At(widget,group+12,count) ||
      count<0 || count>64 || capacity<count || (count && !data))return false;
  for(std::int32_t i=0;i<count;++i) {
    GuiControlCallbackV1 cb{};
    if(!Bytes(data+static_cast<std::size_t>(i)*0x48,cb.binding.data(),cb.binding.size()))return false;
    std::memcpy(&cb.object,cb.binding.data()+0x40,sizeof(cb.object));
    if(!cb.object || !Bytes(cb.object,cb.object_header.data(),cb.object_header.size()))return false;
    std::memcpy(&cb.vtable,cb.object_header.data(),sizeof(cb.vtable));
    if(!InImage(image,cb.vtable,24) || !At(cb.vtable,16,cb.invoke) || !InImage(image,cb.invoke,1))return false;
    // The independently reviewed current constructor406FA30 and leaf406FFF0
    // bind an F8-byte expression source with receiver+F0 and expression+10.
    // Snapshot the whole source and
    // all bounded operand vectors, including each parameter's scope chain.
    // Other callback classes remain observable but cannot grant activation.
    if(cb.vtable==image+0x50BFE48 && cb.invoke==image+0x406FFF0) {
      cb.native_source.resize(0xF8);
      if(!Bytes(cb.object,cb.native_source.data(),0xF8) ||
          !SourceVector(cb.object,0x10,0x40,cb.native_source,true) ||
          !SourceVector(cb.object,0x28,0x18,cb.native_source) ||
          !SourceVector(cb.object,0x90,0x30,cb.native_source) ||
          !SourceVector(cb.object,0xA8,8,cb.native_source) ||
          !SourceVector(cb.object,0xC0,4,cb.native_source))return false;
    } else proven=false;
    out.push_back(cb);
  }return true;
}


[[maybe_unused]]bool Navigation(const RmtmDecisionScene267V1&e,std::uintptr_t image,RmtmDecisionRaw267V1&out){
 std::uintptr_t host=0,back=0;if(!At(e.context,0x3D8,host)||!At(host,8,back)||back!=e.context||!At(e.context,0x3E8,out.shortcut_manager)||!At(out.shortcut_manager,0,back)||back!=e.context)return false;
 std::size_t tab=e.hud.size(),tabs=0;for(std::size_t i=0;i<e.hud.size();++i)if(e.hud[i].name=="tab_decisions"){tab=i;++tabs;}if(tabs>1)return false;if(!tabs)return true;
 std::size_t choices=0;for(std::size_t i=tab+1;i<e.hud.size();++i){const auto&node=e.hud[i];std::uintptr_t p=node.parent;bool child=false;for(std::size_t depth=0;depth<32&&p;++depth){if(p==e.hud[tab].widget){child=true;break;}auto found=std::find_if(e.hud.begin(),e.hud.begin()+static_cast<std::ptrdiff_t>(i),[&](const auto&n){return n.widget==p;});if(found==e.hud.begin()+static_cast<std::ptrdiff_t>(i))break;p=found->parent;}if(!child||!node.visible||!node.enabled)continue;
  std::uintptr_t slot=0;if(!At(node.vtable,13*8,slot))return false;if(slot!=image+0x406DB30)continue;std::vector<ck3_1210::GuiControlCallbackV1>cbs;bool proven=true;if(!CallbackGroup(image,node.widget,0x4B8,cbs,proven)||!CallbackGroup(image,node.widget,0x3F8,cbs,proven))return false;if(!proven||cbs.empty())continue;if(++choices>1)return false;out.nav_widget=node.widget;out.nav_callbacks=std::move(cbs);
 }out.source.open_list_admissible=choices==1&&!out.source.list_visible&&!out.source.blocked_by_visible_modal;return true;
}
[[maybe_unused]]bool FactoryUnselected267V1(std::uintptr_t selected,std::uintptr_t factory_default,std::uintptr_t actual_vptr,std::uintptr_t image,std::uint32_t actor,std::uintptr_t controller,bool visible,const std::array<std::byte,32>&key)noexcept{
 std::uint64_t n=0,cap=0;std::memcpy(&n,key.data()+16,8);std::memcpy(&cap,key.data()+24,8);
 return selected&&selected==factory_default&&actual_vptr==image+0x4FD0500&&actor==0xFFFFFFFFU&&!controller&&!visible&&!n&&cap==15&&key.front()==std::byte{};
}
[[maybe_unused]]bool Sample(const ReadonlyBindings&b,const ck3_1210::CoreSnapshotPrefix&core,const RmtmDecisionScene267V1&e,std::uint64_t mono,RmtmDecisionRaw267V1&out,std::string&reason){
 const auto fail=[&](const char*why){reason=why;return false;};const auto image=b.module_base;if(!RmtmDecisionDeadline267V1(e.wall_deadline,mono))return fail("rmtm_actual_decision_deadline_expired");
#if defined(XAR_CK3_26785313_OFFLINE_FIXTURE)
 if(b.offline_fixture)return fail("rmtm_decision_offline_fixture_has_no_live_authority");
#endif

 if(!Alive(mono)||!b.exact_image_admitted||!b.core.enabled||!VerifyRmtmDecisionImage267V1(image)||!e.jomini||!e.gfx||!e.handler||!e.context||!e.global||!core.clock.paused||!core.played_character_alive||!core.map_ready||!core.has_played_character||core.played_character_id==-1)return fail("rmtm_decision_actual_paused_living_source_unavailable");
 std::uintptr_t v=0;if(!At(image,kJominiStateSlotRva,v)||v!=e.jomini||!Typed(e.jomini,image,0x4B45FE0)||!At(e.jomini,0x10,v)||v!=e.gfx||!Typed(e.gfx,image,0x4B24748)||!At(e.gfx,0x20,v)||v!=e.jomini||!At(e.gfx,0x88,v)||v!=e.handler||!Typed(e.handler,image,0x4B22578)||!At(e.handler,0x40,v)||v!=e.jomini||!At(e.handler,abi::kHandlerList,out.list)||!At(e.handler,abi::kHandlerDetail,out.detail))return fail("rmtm_decision_actual_handler_source_unavailable");
 if(!Modal(e.context,out))return fail("rmtm_decision_actual_modal_census_unavailable");
 if(e.list_root){if(!Window(e,image,out.list,abi::kDecisionsViewVtable,abi::kDecisionsViewSecondary10,e.list_root))return fail("rmtm_decision_actual_list_type_root_or_context_mismatch");out.source.list_found=true;out.source.list_visible=e.list_visible;out.source.list_enabled=e.list_enabled;
  std::uintptr_t groups=0;std::int32_t count=0;if(!Header(out.list+abi::kListGroups,groups,count,64,out.exact_model,true))return fail("rmtm_decision_complete_group_header_unavailable");out.source.groups_count=count;std::size_t total=0;std::unordered_set<std::uintptr_t>seen;
  for(std::int32_t i=0;i<count;++i){const auto group=groups+static_cast<std::size_t>(i)*abi::kDecisionGroupStride;std::uintptr_t rows=0;std::int32_t n=0;if(!Add(out.exact_model,group,8)||!Header(group+abi::kGroupDecisions,rows,n,1024,out.exact_model,true)||total+static_cast<std::size_t>(n)>1024)return fail("rmtm_decision_complete_decision_row_header_unavailable");total+=n;
   for(std::int32_t j=0;j<n;++j){const auto row=rows+static_cast<std::size_t>(j)*abi::kDecisionRowStride;std::uintptr_t def=0,owner=0;std::uint32_t actor=0;std::string key;if(!seen.insert(row).second||!At(row,0,def)||!Typed(def,image,abi::kDecisionTypeVtable)||!At(row,abi::kRowOwner,owner)||owner!=out.list||!At(row,abi::kRowCharacterReference,actor)||!CStringKey(def+abi::kDecisionKey,key,out.exact_model))return fail("rmtm_decision_actual_decision_row_identity_unavailable");std::uint8_t actual_state=0;if(!At(row,0x14,actual_state)||!AppendCuratedModelRow267V1(out.exact_model,def,actor,owner,actual_state))return fail("rmtm_decision_actual_complete_row_semantics_unavailable");if(const auto chosen=ParseRmtmDecisionKey267V1(key)){const auto index=static_cast<std::size_t>(*chosen);if(actor!=static_cast<std::uint32_t>(core.played_character_id)||out.rows[index])return fail("rmtm_decision_fixed_decision_player_or_unique_key_mismatch");out.rows[index]=row;out.source.rows.push_back({*chosen,false,false});}
   }
  }out.source.total_model_rows=static_cast<std::int32_t>(total);out.source.complete_model_census=true;
 }
 if(e.detail_root){if(!Window(e,image,out.detail,abi::kDecisionDetailVtable,abi::kDecisionDetailSecondary10,e.detail_root))return fail("rmtm_decision_actual_detail_type_root_or_context_mismatch");out.source.detail_found=true;out.source.detail_visible=e.detail_visible;out.source.detail_enabled=e.detail_enabled;std::uint32_t actor=0;std::uint8_t state=0;
  if(!At(out.detail,abi::kDetailDecision,out.definition)||!At(out.detail,abi::kDetailActor,actor)||!At(out.detail,abi::kDetailController,out.controller)||!At(out.detail,abi::kDetailWidgetState,state)||state>1||!Add(out.exact_model,out.detail+abi::kDetailDecision,12)||!Add(out.exact_model,out.detail+abi::kDetailController,8)||!Add(out.exact_model,out.detail+abi::kDetailWidgetState,1))return fail("rmtm_decision_actual_detail_fields_unavailable");out.source.widget_state=state;
  std::uintptr_t factory_default=0;if(!At(image,0x6A689A0,factory_default)||!Add(out.exact_model,image+0x6A689A0,8))return fail("rmtm_decision_actual_factory_default_source_unavailable");
  if(out.definition&&out.definition==factory_default){std::uintptr_t default_vptr=0;std::array<std::byte,32>key{};if(!At(out.definition,0,default_vptr)||!Bytes(out.definition+abi::kDecisionKey,key.data(),key.size())||!Add(out.exact_model,out.definition,0x38)||!FactoryUnselected267V1(out.definition,factory_default,default_vptr,image,actor,out.controller,e.detail_visible,key))return fail("rmtm_decision_factory_default_not_hidden_unselected_source");}
  else if(out.definition){std::string key;if(!Typed(out.definition,image,abi::kDecisionTypeVtable)||!CStringKey(out.definition+abi::kDecisionKey,key,out.exact_model))return fail("rmtm_decision_actual_selected_definition_unavailable");out.source.selected_decision=ParseRmtmDecisionKey267V1(key);out.source.other_decision_selected=!out.source.selected_decision;
   if(out.source.selected_decision&&e.detail_visible){if(actor!=static_cast<std::uint32_t>(core.played_character_id)||!out.rows[static_cast<std::size_t>(*out.source.selected_decision)]||!out.source.complete_model_census)return fail("rmtm_decision_selected_player_or_model_membership_mismatch");if(out.controller){if(!Typed(out.controller,image,abi::kDefaultControllerVtable)||!Add(out.exact_model,out.controller,0x20))return fail("rmtm_decision_unreviewed_custom_decision_widget_refused");}
    bool can=false;out.native_read_entered=true;if(!NativeCan(image,out.detail,can)){out.cleanup_known=false;return fail("rmtm_decision_native_can_completion_unknown");}out.source.native_can_confirm=can;out.source.confirm_admissible=can&&e.detail_enabled&&!out.source.blocked_by_visible_modal;
   }
  }
 }
 for(auto&row:out.source.rows){row.is_selected=e.detail_visible&&out.source.selected_decision==row.decision;row.can_open_detail=e.list_visible&&e.list_enabled&&!row.is_selected&&!out.source.blocked_by_visible_modal;}
 if(!Navigation(e,image,out)){out.nav_widget=0;out.nav_callbacks.clear();out.source.open_list_admissible=false;}
 out.source.case_bound=RmtmCaseAdmitted267V1(core,e.connection_generation,reinterpret_cast<std::uintptr_t>(*b.core.game_state_slot),reinterpret_cast<std::uintptr_t>(*b.core.jomini_state_slot));
 if(!out.source.case_bound){out.source.open_list_admissible=false;out.source.confirm_admissible=false;for(auto&row:out.source.rows)row.can_open_detail=false;}

 if(out.source.selected_decision&&e.detail_visible){std::string why;bool clean=true,entered=false;if(!ReadRmtmConfirmTooltip267V1(image,out.detail,e.wall_deadline,mono,why,clean,entered)){out.native_read_entered=out.native_read_entered||entered;out.cleanup_known=clean;return fail("rmtm_actual_confirm_tooltip_source_unavailable");}out.native_read_entered=out.native_read_entered||entered;out.source.confirm_tooltip=std::move(why);out.source.confirm_tooltip_observed=true;}
 return Alive(mono);
}
}
bool VerifyRmtmDecisionImage267V1([[maybe_unused]]std::uintptr_t image)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_DECISION_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_DECISION_V1
 if(!VerifyGuiWindowImageV1(image)||!RmtmTooltipPins267V1(image))return false;std::array<unsigned char,4096>bytes{};const std::array<unsigned char,25>factory_pin{0x48,0x8B,0x05,0x54,0x49,0xF6,0x05,0x48,0x89,0x86,0xD0,0x00,0x00,0x00,0x48,0xC7,0x86,0xD8,0x00,0x00,0x00,0xFF,0xFF,0xFF,0xFF};if(!Bytes(image+0xB04045,bytes.data(),factory_pin.size())||std::memcmp(bytes.data(),factory_pin.data(),factory_pin.size()))return false;std::uintptr_t default_col=0;if(!At(image,0x4FD0500-8,default_col)||default_col!=image+0x5774560)return false;for(const auto&pin:aub_decision_source_pins::kPins)if(pin.bytes.empty()||pin.bytes.size()>bytes.size()||pin.rva>kImageSize-pin.bytes.size()||!Bytes(image+pin.rva,bytes.data(),pin.bytes.size())||std::memcmp(bytes.data(),pin.bytes.data(),pin.bytes.size()))return false;
 for(const auto&pin:gui_control_pins_v2::kPins)if(pin.bytes.empty()||pin.bytes.size()>bytes.size()||pin.rva>kImageSize-pin.bytes.size()||!Bytes(image+pin.rva,bytes.data(),pin.bytes.size())||std::memcmp(bytes.data(),pin.bytes.data(),pin.bytes.size()))return false;for(const auto&pin:aub_decision_source_pins::kPointers){std::uintptr_t v=0;if(!At(image,pin.slot,v)||v!=image+pin.target)return false;}std::uintptr_t v=0;return At(image,0x50BFE48-8,v)&&v==image+0x58E4738&&At(image,0x50BFE48+16,v)&&v==image+0x406FFF0;
#else
 return false;
#endif
}
bool ReadRmtmDecisionRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&core,[[maybe_unused]]const RmtmDecisionScene267V1&e,[[maybe_unused]]std::uint64_t mono,RmtmDecisionRaw267V1&out,std::string&reason)noexcept{out={};reason="current_rmtm_decision_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_DECISION_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_DECISION_V1
 RmtmDecisionRaw267V1 a,z;try{if(!Sample(b,core,e,mono,a,reason)){out=std::move(a);return false;}if(!Sample(b,core,e,mono,z,reason)){z.native_read_entered=z.native_read_entered||a.native_read_entered;out=std::move(z);return false;}if(a!=z){out=std::move(z);reason="rmtm_decision_complete_model_or_native_can_changed_between_samples";return false;}out=std::move(z);reason.clear();return true;}catch(...){out.native_read_entered=a.native_read_entered||z.native_read_entered;out.cleanup_known=!out.native_read_entered;reason="rmtm_decision_source_capture_exception";return false;}
#else
 return false;
#endif
}
RmtmDecisionRawCall267V1 CallRmtmDecisionRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&core,[[maybe_unused]]const RmtmDecisionScene267V1&e,[[maybe_unused]]std::uint64_t mono,[[maybe_unused]]const RmtmDecisionRaw267V1&expected,[[maybe_unused]]RmtmDecisionAction267V1 action,[[maybe_unused]]std::optional<RmtmDecision267V1>key)noexcept{
 RmtmDecisionRawCall267V1 call;
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_DECISION_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_DECISION_V1
 RmtmDecisionRaw267V1 actual;std::string reason;if(!ReadRmtmDecisionRaw267V1(b,core,e,mono,actual,reason)){call.cleanup_known=actual.cleanup_known;if(!call.cleanup_known)call.status=RmtmDecisionRawCallStatus267V1::indeterminate;return call;}if(actual!=expected||!Alive(mono))return call;std::uintptr_t receiver=0;
 if(action==RmtmDecisionAction267V1::open_list){if(key||!actual.source.open_list_admissible)return call;receiver=actual.nav_widget;}
 else if(action==RmtmDecisionAction267V1::open_detail&&key){for(const auto&row:actual.source.rows)if(row.decision==key&&row.can_open_detail)receiver=actual.rows[static_cast<std::size_t>(*key)];}
 else if(action==RmtmDecisionAction267V1::confirm&&key&&actual.source.selected_decision==key&&actual.source.confirm_admissible&&actual.source.native_can_confirm==true)receiver=actual.detail;
 if(!receiver||!RmtmDecisionDeadline267V1(e.wall_deadline,mono))return call;call=Native(b.module_base,receiver,action,actual.shortcut_manager);if(call.effect_entered&&call.status==RmtmDecisionRawCallStatus267V1::returned&&(!VerifyRmtmDecisionImage267V1(b.module_base)||!RmtmDecisionDeadline267V1(e.wall_deadline,mono))){call.status=RmtmDecisionRawCallStatus267V1::indeterminate;call.cleanup_known=false;}
#endif
 return call;
}
}
