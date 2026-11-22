#include "xar_bridge/ck3_121003_rite_text26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_rite_text26785313_pins_v1.hpp"
#include "xar_bridge/ck3_121003_doctrine_category26785313_v1.hpp"
#include "xar_bridge/ck3_121003_doctrine_select26785313_v1.hpp"
#include "xar_bridge/ck3_121003_doctrine_knowledge26785313_v1.hpp"
#include <chrono>
#include <cstring>
#include <limits>
#include <unordered_set>
#include <windows.h>
#ifndef XAR_RITE_TEXT_CALL_ADDRESS
#define XAR_RITE_TEXT_CALL_ADDRESS(image,rva) ((image)+(rva))
#endif
namespace xar::ck3_121003::build26785313 {namespace {
bool Copy(std::uintptr_t p,void*out,std::size_t n)noexcept{if(!p||!out||!n)return false;__try{std::memcpy(out,reinterpret_cast<void*>(p),n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
template<class T>bool At(std::uintptr_t p,std::size_t n,T&v)noexcept{constexpr auto max=(std::numeric_limits<std::uintptr_t>::max)();return p&&n<=max-p&&sizeof(T)-1<=max-p-n&&Copy(p+n,&v,sizeof(v));}
[[maybe_unused]]bool Time(std::uint64_t wall,std::uint64_t mono)noexcept{const auto n=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return n>0&&wall&&mono&&static_cast<std::uint64_t>(n)<wall&&GetTickCount64()<mono;}
[[maybe_unused]]bool SameCore(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool Fresh(const ReadonlyBindings&b,const RiteTextFrame267V1&f,std::uint64_t wall,std::uint64_t mono)noexcept{
 if(!b.exact_image_admitted||!f.facts_verified||!Time(wall,mono))return false;
 __try{ck3_1210::CoreSnapshotPrefix c;std::int32_t id=-1;std::uint32_t magic=0;std::uintptr_t death=1;return ck3_1210::ReadCoreSnapshot(b.core,c)&&SameCore(c,f.core)&&reinterpret_cast<std::uintptr_t>(*b.core.game_state_slot)==f.game&&reinterpret_cast<std::uintptr_t>(*b.core.jomini_state_slot)==f.jomini&&reinterpret_cast<std::uintptr_t>(*b.core.character_storage_slot)==f.storage&&reinterpret_cast<std::uintptr_t>(ck3_1210::ResolveCoreCharacter(b.core,c.played_character_id))==f.actor&&At(f.actor,0x18,id)&&id==c.played_character_id&&At(f.actor,0x1C,magic)&&magic==0x43686172&&At(f.actor,0x1D0,death)&&!death&&Time(wall,mono);}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool Bool(std::uintptr_t image,std::uintptr_t rva,std::uintptr_t self,bool second,bool&out)noexcept{__try{if(second){using Fn=bool(__fastcall*)(const void*,void*);out=reinterpret_cast<Fn>(XAR_RITE_TEXT_CALL_ADDRESS(image,rva))(reinterpret_cast<void*>(self),nullptr);}else{using Fn=bool(__fastcall*)(const void*);out=reinterpret_cast<Fn>(XAR_RITE_TEXT_CALL_ADDRESS(image,rva))(reinterpret_cast<void*>(self));}return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Controller(const ReadonlyBindings&b,const RiteTextFrame267V1&f,std::uintptr_t expected,std::uint32_t source,std::uintptr_t context,std::uintptr_t root)noexcept{
 const auto image=b.module_base;std::uintptr_t gfx=0,handler=0,controller=0,vt=0,back=0,app=0,first=0,cx=0;std::uint32_t rite=0xFFFFFFFFU;std::int32_t actor=-1;
 return expected&&context&&root&&At(f.jomini,0,vt)&&vt==image+0x4B45FE0&&At(f.jomini,0x10,gfx)&&At(gfx,0,vt)&&vt==image+0x4B24748&&At(gfx,0x20,back)&&back==f.jomini&&At(gfx,0x88,handler)&&At(handler,0,vt)&&vt==image+0x4B22578&&At(handler,0x58,vt)&&vt==image+0x4B22558&&At(handler,0x278,controller)&&controller==expected&&At(controller,0,vt)&&vt==image+0x4C09438&&At(controller,0x10,vt)&&vt==image+0x4C09410&&At(controller,0x98,back)&&back==f.jomini&&At(controller,0xA0,back)&&back==handler&&At(controller,0x60,back)&&back==root&&At(controller,0xC8,rite)&&rite==source&&At(controller,0xCC,actor)&&actor==f.core.played_character_id&&At(f.jomini,0x18,app)&&At(app,0x1B8,first)&&At(first,0x58,cx)&&cx==context;
}
[[maybe_unused]]bool UnrelatedModal(const ck3_1210::GuiControlCaptureV1&c,const GuiWindowV1&w)noexcept{if(c.modal_receivers.size()!=c.modal_flags.size())return true;bool visible=false;for(auto v:c.modal_flags)if((v&8)==0)visible=true;if(!visible)return false;if(c.modal_receivers.empty()||w.tree.empty())return true;const auto selected=c.modal_receivers.back();if(selected==w.tree.front().widget||selected==w.global_root)return false;for(const auto&a:w.ancestors)if(a.widget==selected)return false;return true;}
[[maybe_unused]]bool SelectedDraft(std::uintptr_t controller,std::array<std::byte,16>&header,std::vector<std::array<std::byte,0x48>>&rows){
 if(!At(controller,0x798,header))return false;std::uintptr_t data=0;std::int32_t cap=0,count=0;std::memcpy(&data,header.data(),8);std::memcpy(&cap,header.data()+8,4);std::memcpy(&count,header.data()+12,4);if(count<0||count>static_cast<std::int32_t>(kRiteDoctrineItemsObservationMax267V1)||cap<count||(count&&!data))return false;
 for(std::int32_t i=0;i<count;++i){std::array<std::byte,0x48>row{};if(!At(data,static_cast<std::size_t>(i)*row.size(),row))return false;rows.push_back(row);}return true;
}

[[maybe_unused]]bool NamePointer(std::uintptr_t image,std::uintptr_t controller,std::uintptr_t&out)noexcept{using Fn=const void*(__fastcall*)(const void*);__try{out=reinterpret_cast<std::uintptr_t>(reinterpret_cast<Fn>(XAR_RITE_TEXT_CALL_ADDRESS(image,0x16BB5A0))(reinterpret_cast<void*>(controller)));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Setter(std::uintptr_t image,std::uintptr_t rva,std::uintptr_t controller,const void*input)noexcept{using Fn=void(__fastcall*)(void*,const void*);__try{reinterpret_cast<Fn>(XAR_RITE_TEXT_CALL_ADDRESS(image,rva))(reinterpret_cast<void*>(controller),input);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool ReadableUtf8(std::string_view s)noexcept{for(std::size_t i=0;i<s.size();){const auto lead=static_cast<unsigned char>(s[i++]);unsigned n=0;std::uint32_t cp=0;if(lead<128)cp=lead;else if(lead>=0xC2&&lead<=0xDF){cp=lead&31;n=1;}else if(lead>=0xE0&&lead<=0xEF){cp=lead&15;n=2;}else if(lead>=0xF0&&lead<=0xF4){cp=lead&7;n=3;}else return false;if(i+n>s.size())return false;for(unsigned j=0;j<n;++j){const auto c=static_cast<unsigned char>(s[i++]);if((c&0xC0)!=0x80)return false;cp=(cp<<6)|(c&63);}if((n==1&&cp<128)||(n==2&&cp<0x800)||(n==3&&cp<0x10000)||cp>0x10FFFF||(cp>=0xD800&&cp<=0xDFFF))return false;}return true;}
[[maybe_unused]]bool Value(std::uintptr_t field,std::array<std::byte,32>&header,std::string&out){
 if(!Copy(field,header.data(),header.size()))return false;std::uint64_t length=0,capacity=0;std::uintptr_t data=field;std::memcpy(&length,header.data()+16,8);std::memcpy(&capacity,header.data()+24,8);if(length>4096||capacity<length||(capacity<=15&&length>15))return false;if(capacity>15)std::memcpy(&data,header.data(),8);if(!data)return false;std::array<char,4097>bytes{};if(!Copy(data,bytes.data(),static_cast<std::size_t>(length)+1)||bytes[static_cast<std::size_t>(length)]!=0)return false;out.assign(bytes.data(),static_cast<std::size_t>(length));return ReadableUtf8(out);
}
[[maybe_unused]]bool Sample(const ReadonlyBindings&b,const RiteTextFrame267V1&f,const RiteTextRequest267V1&q,std::uint64_t mono,RiteTextRaw267V1&out,std::string&why){
 if(!f.draft||f.draft->window.tree.empty()){why="rite_text_actual_draft_missing";return false;}out.draft=*f.draft;out.controller=out.draft.controller;out.context=out.draft.window.context;out.root=out.draft.window.tree.front().widget;
 if(out.draft.source_rite_id!=q.expected_source_rite_id||!Controller(b,f,out.controller,q.expected_source_rite_id,out.context,out.root)){why="rite_text_actual_controller_actor_source_unavailable";return false;}out.source.source_rite_id=q.expected_source_rite_id;out.source.actor_id=f.core.played_character_id;out.entered=true;
 if(!Time(q.deadline_unix_ms,mono)||!Bool(b.module_base,0x16B9260,out.controller,false,out.source.is_creating)||!Time(q.deadline_unix_ms,mono)){out.cleanup_known=false;why="rite_text_actual_creating_predicate_unavailable";return false;}
 if(!ReadRiteTextValues267V1(b,out.controller,q.deadline_unix_ms,mono,out.values,why))return false;
 if(!CaptureGuiControlWindow267V2(BindGuiControlImage267V2(b.module_base,kExecutableSha256),out.draft.window,out.controls,why)||!ReadRiteDoctrineItems267V1(b,out.controller,out.doctrine_items,why)||!SelectedDraft(out.controller,out.selected_header,out.selected_rows))return false;
 out.source.name=out.values.name;out.source.description=out.values.description;out.source.window_visible=out.draft.window.tree.front().visible;out.source.window_enabled=out.draft.window.tree.front().enabled;out.source.blocked_by_unrelated_modal=UnrelatedModal(out.controls,out.draft.window);out.source.write_admissible=out.source.is_creating&&out.source.window_visible&&out.source.window_enabled&&!out.source.blocked_by_unrelated_modal;
 out.draft.window.ticket_sequence=0;out.draft.window.pump_epoch=0;return Fresh(b,f,q.deadline_unix_ms,mono);
}
}
bool VerifyRiteTextImage267V1([[maybe_unused]]std::uintptr_t image)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_TEXT_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_TEXT_V1
 if(!image||image!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))||!VerifyReadonlyImage(image)||!VerifyRiteCreateImage267V1(image))return false;std::array<std::byte,4096>bytes{};
 for(const auto&p:rite_text_pins::kPins)if(p.bytes.empty()||p.bytes.size()>bytes.size()||p.rva>kImageSize-p.bytes.size()||!Copy(image+p.rva,bytes.data(),p.bytes.size())||std::memcmp(bytes.data(),p.bytes.data(),p.bytes.size()))return false;
 for(const auto&p:rite_text_pins::kPointers){std::uintptr_t value=0;if(!At(image,p.slot,value)||value!=image+p.target)return false;}return true;
#else
 return false;
#endif
}
bool ReadRiteTextValues267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]std::uintptr_t controller,[[maybe_unused]]std::uint64_t wall,[[maybe_unused]]std::uint64_t mono,RiteTextValues267V1&out,std::string&why)noexcept{
 out={};why="rite_text_values_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_TEXT_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_TEXT_V1
 try{std::uintptr_t vt=0,sec=0;if(!VerifyRiteTextImage267V1(b.module_base)||!Time(wall,mono)||!At(controller,0,vt)||vt!=b.module_base+0x4C09438||!At(controller,0x10,sec)||sec!=b.module_base+0x4C09410||controller>(std::numeric_limits<std::uintptr_t>::max)()-0xA00)return false;
  RiteTextValues267V1 samples[2];for(auto&s:samples){std::uintptr_t name=0;if(!Time(wall,mono)||!NamePointer(b.module_base,controller,name)||name!=controller+0x920||!Value(name,s.name_header,s.name)||!Value(controller+0x9E0,s.description_header,s.description)||!At(controller,0x940,s.name_dirty)||s.name_dirty>1||!At(controller,0xA00,s.description_dirty)||s.description_dirty>1||!Time(wall,mono))return false;}
  if(samples[0]!=samples[1]){why="rite_text_actual_header_or_value_changed_between_samples";return false;}out=std::move(samples[1]);why.clear();return true;
 }catch(...){why="rite_text_actual_value_copy_unavailable";return false;}
#else
 return false;
#endif
}
bool ReadRiteTextRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const RiteTextFrame267V1&f,[[maybe_unused]]const RiteTextRequest267V1&q,[[maybe_unused]]std::uint64_t mono,RiteTextRaw267V1&out,std::string&why)noexcept{
 out={};why="rite_text_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_TEXT_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_TEXT_V1
 if(!VerifyRiteTextImage267V1(b.module_base)||!Fresh(b,f,q.deadline_unix_ms,mono)){why="rite_text_actual_image_or_world_unavailable";return false;}
 try{RiteTextRaw267V1 samples[2];for(auto&s:samples){const bool good=Sample(b,f,q,mono,s,why);out=s;if(!good||!s.cleanup_known)return false;}if(samples[0]!=samples[1]){why="rite_text_actual_complete_draft_changed_between_samples";return false;}out=std::move(samples[1]);why.clear();return true;}catch(...){why="rite_text_actual_raw_exception";return false;}
#else
 return false;
#endif
}
RiteTextCall267V1 CallRiteTextRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const RiteTextFrame267V1&f,[[maybe_unused]]const RiteTextRequest267V1&q,[[maybe_unused]]std::uint64_t mono,[[maybe_unused]]const RiteTextRaw267V1&expected)noexcept{
 RiteTextCall267V1 out;
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_TEXT_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_TEXT_V1
 if(!RiteTextRequestShape267V1(q)||q.action==RiteTextAction267V1::query)return out;RiteTextRaw267V1 actual;std::string why;if(!ReadRiteTextRaw267V1(b,f,q,mono,actual,why)||actual!=expected||!actual.source.write_admissible||!Fresh(b,f,q.deadline_unix_ms,mono))return out;
 // The real raw ABI is const CUTF8String32*, not a CString Any. Both native
 // setters synchronously copy their input into an owned temporary then draft.
 alignas(8)std::array<std::byte,32>input{};const auto size=static_cast<std::uint64_t>(q.text.size());std::uint64_t capacity=15;if(size<=15)std::memcpy(input.data(),q.text.c_str(),q.text.size()+1);else{const auto data=reinterpret_cast<std::uintptr_t>(q.text.c_str());std::memcpy(input.data(),&data,8);capacity=size;}std::memcpy(input.data()+16,&size,8);std::memcpy(input.data()+24,&capacity,8);
 out.entered=true;out.status=RiteTextCallStatus267V1::indeterminate;if(Setter(b.module_base,q.action==RiteTextAction267V1::set_name?0x16B8720:0x16B8B90,actual.controller,input.data()))out.status=RiteTextCallStatus267V1::returned;else out.cleanup_known=false;
 if(!Time(q.deadline_unix_ms,mono)||!VerifyRiteTextImage267V1(b.module_base))out.status=RiteTextCallStatus267V1::indeterminate;
#endif
 return out;
}
}
