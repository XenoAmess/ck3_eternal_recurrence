#include "xar_bridge/ck3_121003_rite_create26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_rite_create26785313_pins_v1.hpp"
#include "xar_bridge/ck3_121003_doctrine_category26785313_v1.hpp"
#include "xar_bridge/ck3_121003_doctrine_select26785313_v1.hpp"
#include "xar_bridge/ck3_121003_doctrine_knowledge26785313_v1.hpp"
#include <chrono>
#include <cstring>
#include <limits>
#include <unordered_set>
#include <windows.h>
#ifndef XAR_RITE_CREATE_CALL_ADDRESS
#define XAR_RITE_CREATE_CALL_ADDRESS(image,rva) ((image)+(rva))
#endif
namespace xar::ck3_121003::build26785313 {namespace {
bool Copy(std::uintptr_t p,void*out,std::size_t n)noexcept{if(!p||!out||!n)return false;__try{std::memcpy(out,reinterpret_cast<void*>(p),n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
template<class T>bool At(std::uintptr_t p,std::size_t n,T&v)noexcept{constexpr auto max=(std::numeric_limits<std::uintptr_t>::max)();return p&&n<=max-p&&sizeof(T)-1<=max-p-n&&Copy(p+n,&v,sizeof(v));}
[[maybe_unused]]bool Time(std::uint64_t wall,std::uint64_t mono)noexcept{const auto n=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return n>0&&wall&&mono&&static_cast<std::uint64_t>(n)<wall&&GetTickCount64()<mono;}
[[maybe_unused]]bool SameCore(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool Fresh(const ReadonlyBindings&b,const RiteCreateFrame267V1&f,std::uint64_t wall,std::uint64_t mono)noexcept{
 if(!b.exact_image_admitted||!f.facts_verified||!Time(wall,mono))return false;
 __try{ck3_1210::CoreSnapshotPrefix c;std::int32_t id=-1;std::uint32_t magic=0;std::uintptr_t death=1;return ck3_1210::ReadCoreSnapshot(b.core,c)&&SameCore(c,f.core)&&reinterpret_cast<std::uintptr_t>(*b.core.game_state_slot)==f.game&&reinterpret_cast<std::uintptr_t>(*b.core.jomini_state_slot)==f.jomini&&reinterpret_cast<std::uintptr_t>(*b.core.character_storage_slot)==f.storage&&reinterpret_cast<std::uintptr_t>(ck3_1210::ResolveCoreCharacter(b.core,c.played_character_id))==f.actor&&At(f.actor,0x18,id)&&id==c.played_character_id&&At(f.actor,0x1C,magic)&&magic==0x43686172&&At(f.actor,0x1D0,death)&&!death&&Time(wall,mono);}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool Bool(std::uintptr_t image,std::uintptr_t rva,std::uintptr_t self,bool second,bool&out)noexcept{__try{if(second){using Fn=bool(__fastcall*)(const void*,void*);out=reinterpret_cast<Fn>(XAR_RITE_CREATE_CALL_ADDRESS(image,rva))(reinterpret_cast<void*>(self),nullptr);}else{using Fn=bool(__fastcall*)(const void*);out=reinterpret_cast<Fn>(XAR_RITE_CREATE_CALL_ADDRESS(image,rva))(reinterpret_cast<void*>(self));}return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool ManagerCall(std::uintptr_t image,std::uintptr_t&out)noexcept{using Fn=void*(__fastcall*)();__try{out=reinterpret_cast<std::uintptr_t>(reinterpret_cast<Fn>(XAR_RITE_CREATE_CALL_ADDRESS(image,0xCF2C50))());return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool VoidCall(std::uintptr_t image,std::uintptr_t rva,std::uintptr_t target)noexcept{using Fn=void(__fastcall*)(void*);__try{reinterpret_cast<Fn>(XAR_RITE_CREATE_CALL_ADDRESS(image,rva))(reinterpret_cast<void*>(target));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Controller(const ReadonlyBindings&b,const RiteCreateFrame267V1&f,std::uintptr_t expected,std::uint32_t source,std::uintptr_t context,std::uintptr_t root)noexcept{
 const auto image=b.module_base;std::uintptr_t gfx=0,handler=0,controller=0,vt=0,back=0,app=0,first=0,cx=0;std::uint32_t rite=0xFFFFFFFFU;std::int32_t actor=-1;
 return expected&&context&&root&&At(f.jomini,0,vt)&&vt==image+0x4B45FE0&&At(f.jomini,0x10,gfx)&&At(gfx,0,vt)&&vt==image+0x4B24748&&At(gfx,0x20,back)&&back==f.jomini&&At(gfx,0x88,handler)&&At(handler,0,vt)&&vt==image+0x4B22578&&At(handler,0x58,vt)&&vt==image+0x4B22558&&At(handler,0x278,controller)&&controller==expected&&At(controller,0,vt)&&vt==image+0x4C09438&&At(controller,0x10,vt)&&vt==image+0x4C09410&&At(controller,0x98,back)&&back==f.jomini&&At(controller,0xA0,back)&&back==handler&&At(controller,0x60,back)&&back==root&&At(controller,0xC8,rite)&&rite==source&&At(controller,0xCC,actor)&&actor==f.core.played_character_id&&At(f.jomini,0x18,app)&&At(app,0x1B8,first)&&At(first,0x58,cx)&&cx==context;
}
[[maybe_unused]]bool UnrelatedModal(const ck3_1210::GuiControlCaptureV1&c,const GuiWindowV1&w)noexcept{if(c.modal_receivers.size()!=c.modal_flags.size())return true;bool visible=false;for(auto v:c.modal_flags)if((v&8)==0)visible=true;if(!visible)return false;if(c.modal_receivers.empty()||w.tree.empty())return true;const auto selected=c.modal_receivers.back();if(selected==w.tree.front().widget||selected==w.global_root)return false;for(const auto&a:w.ancestors)if(a.widget==selected)return false;return true;}
[[maybe_unused]]bool SelectedDraft(std::uintptr_t controller,std::array<std::byte,16>&header,std::vector<std::array<std::byte,0x48>>&rows){
 if(!At(controller,0x798,header))return false;std::uintptr_t data=0;std::int32_t cap=0,count=0;std::memcpy(&data,header.data(),8);std::memcpy(&cap,header.data()+8,4);std::memcpy(&count,header.data()+12,4);if(count<0||count>static_cast<std::int32_t>(kRiteDoctrineItemsObservationMax267V1)||cap<count||(count&&!data))return false;
 for(std::int32_t i=0;i<count;++i){std::array<std::byte,0x48>row{};if(!At(data,static_cast<std::size_t>(i)*row.size(),row))return false;rows.push_back(row);}return true;
}
[[maybe_unused]]bool Draft(const ReadonlyBindings&b,const RiteCreateFrame267V1&f,const RiteCreateRequest267V1&q,std::uint64_t mono,RiteCreateRaw267V1&out,std::string&why){
 if(!f.draft||f.draft->window.tree.empty()){why="rite_create_actual_draft_missing";return false;}const auto&d=*f.draft;out.controller=d.controller;out.context=d.window.context;out.root=d.window.tree.front().widget;out.source.phase=RiteCreatePhase267V1::draft;out.source.source_rite_id=d.source_rite_id;out.source.actor_id=f.core.played_character_id;
 if(d.source_rite_id!=q.expected_source_rite_id||!Controller(b,f,out.controller,d.source_rite_id,out.context,out.root)){why="rite_create_actual_controller_actor_or_source_unavailable";return false;}RiteCreateDraft267V1 result;out.entered=true;
 if(!Time(q.deadline_unix_ms,mono)||!Bool(b.module_base,0x16B9260,out.controller,false,result.is_creating)||!Time(q.deadline_unix_ms,mono)||!Bool(b.module_base,0x16BA410,out.controller,true,result.native_can_create)||!Time(q.deadline_unix_ms,mono)){out.cleanup_known=false;why="rite_create_native_create_predicate_unavailable";return false;}
 result.piety_cost_raw=d.piety_cost_raw;result.piety_missing_raw=d.piety_missing_raw;
 ck3_1210::GuiControlCaptureV1 controls;if(!CaptureGuiControlWindow267V2(BindGuiControlImage267V2(b.module_base,kExecutableSha256),d.window,controls,why))return false;
 unsigned matches=0;for(const auto&row:controls.widgets)if(row.row.runtime_name=="create_faith"){++matches;out.create_button=row.widget;result.create_button_visible=row.row.effective_visible;result.create_button_enabled=row.row.enabled;}
 if(matches!=1){why="rite_create_actual_unique_create_button_unavailable";return false;}result.create_button_found=true;result.blocked_by_unrelated_modal=UnrelatedModal(controls,d.window);
 DynasticCategoryTarget267V1 category;RiteDoctrineItems267V1 items;if(!ReadRawDynasticDraftTarget267V1(b,out.controller,category,why)||!ReadRiteDoctrineItems267V1(b,out.controller,items,why))return false;
 const auto*target=FindUniqueRiteDoctrineKey267V1(items,"des_doctrine_dynastic");const auto doctrine=target?target->doctrine:category.doctrine_key.exact_bytes=="des_doctrine_dynastic"?category.doctrine:0;
 if(!doctrine){why="rite_create_actual_dynastic_typed_doctrine_unavailable";return false;}
 const auto selection=ReadRawHasDoctrineSelected267V1(b,BindDoctrineSelectImage267V1(b.module_base,kExecutableSha256),out.controller,doctrine);const auto known=ReadRawKnowsDoctrine267V1(b,f.actor,doctrine);
 if(selection.status!=RawDoctrineObservationStatus267V1::observed||known.status==RawDoctrineKnowledgeStatus267V1::unavailable){why="rite_create_actual_dynastic_selection_or_knowledge_unavailable";return false;}
 result.selected_dynastic=selection.has_selected;result.known_dynastic=known.status==RawDoctrineKnowledgeStatus267V1::native_true;
 // Retain the complete actual selected draft, not merely same-price predicates.
 // +798 header/72-byte rows are the existing current CaptureDraft source, not a new offset guess.
 if(!SelectedDraft(out.controller,out.selected_draft_header,out.selected_draft_rows))return false;
 out.draft_witness=d;
 // Fresh ticket/pump coordinates belong to this operation's checked Owner proof,
 // not to the semantic draft identity. The actual owner thread/connection stay bound.
 out.draft_witness->window.ticket_sequence=0;out.draft_witness->window.pump_epoch=0;
 out.controls_witness=std::move(controls);out.doctrine_items=std::move(items);

 result.create_admissible=result.is_creating&&result.native_can_create&&result.piety_missing_raw<=0&&result.known_dynastic&&result.selected_dynastic&&result.create_button_visible&&result.create_button_enabled&&!result.blocked_by_unrelated_modal&&d.window.tree.front().visible&&d.window.tree.front().enabled;
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_TEXT_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_TEXT_V1
 RiteTextValues267V1 text;if(!ReadRiteTextValues267V1(b,out.controller,q.deadline_unix_ms,mono,text,why))return false;out.text_values=std::move(text);
#endif
 out.source.draft=result;return Fresh(b,f,q.deadline_unix_ms,mono);
}
[[maybe_unused]]bool Confirmation(const ReadonlyBindings&b,const RiteCreateFrame267V1&f,const RiteCreateRequest267V1&q,const RiteCreateAssociation267V1&a,std::uint64_t mono,RiteCreateRaw267V1&out,std::string&why){
 const auto image=b.module_base;if(a.actor_id!=f.core.played_character_id||a.source_rite_id!=q.expected_source_rite_id||a.original_deadline!=q.deadline_unix_ms||!Controller(b,f,a.controller,a.source_rite_id,a.context,a.window_root)){why="rite_create_original_create_controller_or_actor_changed";return false;}
 if(!SelectedDraft(a.controller,out.selected_draft_header,out.selected_draft_rows)||out.selected_draft_header!=a.selected_draft_header||out.selected_draft_rows!=a.selected_draft_rows){why="rite_create_original_selected_draft_changed_before_confirmation";return false;}
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_TEXT_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_TEXT_V1
 RiteTextValues267V1 text;if(!a.text_values||!ReadRiteTextValues267V1(b,a.controller,q.deadline_unix_ms,mono,text,why)||text!=*a.text_values){why="rite_create_original_name_or_description_changed_before_confirmation";return false;}out.text_values=std::move(text);
#endif
 out.controller=a.controller;out.context=a.context;out.source.phase=RiteCreatePhase267V1::confirmation;out.source.source_rite_id=a.source_rite_id;out.source.actor_id=a.actor_id;out.entered=true;
 if(!ManagerCall(image,out.manager)){out.cleanup_known=false;return false;}
 if(!out.manager||!Copy(out.manager+0x18,out.dialog_header.data(),16))return false;std::uintptr_t data=0;std::int32_t cap=0,count=0;std::memcpy(&data,out.dialog_header.data(),8);std::memcpy(&cap,out.dialog_header.data()+8,4);std::memcpy(&count,out.dialog_header.data()+12,4);
 if(count<0||count>128||cap<count||(count&&!data))return false;unsigned active=0;std::unordered_set<std::uintptr_t>unique;
 for(std::int32_t i=0;i<count;++i){std::uintptr_t dialog=0,vt=0,root=0,cx=0,owner=0,sec=0;std::uint8_t closed=1;if(!At(data,static_cast<std::size_t>(i)*8,dialog))return false;out.dialog_pointers.push_back(dialog);if(!dialog)continue;if(!unique.insert(dialog).second||!At(dialog,0,vt)||!At(dialog,0x70,root)||!At(dialog,0x78,cx)||!At(dialog,0xA8,closed)||closed>1)return false;if(closed||!root)continue;
  if(++active!=1||vt!=image+0x4C09528||!At(dialog,0x10,sec)||sec!=image+0x4C09508||!At(dialog,0x20,sec)||sec!=image+0x4C095E8||!At(dialog,0x130,owner)||owner!=a.controller||cx!=a.context){why="rite_create_actual_modal_is_not_own_creation_confirmation";return false;}out.modal=dialog;out.root=root;
 }
 if(!active){out.pending=true;return Fresh(b,f,q.deadline_unix_ms,mono);}RiteCreateConfirmation267V1 source;source.modal_found=true;source.original_create_bound=true;
 if(!Time(q.deadline_unix_ms,mono)||!Bool(image,0x16B5F00,out.modal,false,source.native_can_accept)||!Time(q.deadline_unix_ms,mono)){out.cleanup_known=false;return false;}out.source.confirmation=source;return Fresh(b,f,q.deadline_unix_ms,mono);
}
}
bool VerifyRiteCreateImage267V1([[maybe_unused]]std::uintptr_t image)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_CREATE_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_CREATE_V1
 if(!image||image!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))||!VerifyReadonlyImage(image))return false;std::array<std::byte,4096>bytes{};
 for(const auto&p:rite_create_pins::kPins)if(p.bytes.empty()||p.bytes.size()>bytes.size()||p.rva>kImageSize-p.bytes.size()||!Copy(image+p.rva,bytes.data(),p.bytes.size())||std::memcmp(bytes.data(),p.bytes.data(),p.bytes.size()))return false;
 for(const auto&p:rite_create_pins::kPointers){std::uintptr_t value=0;if(!At(image,p.slot,value)||value!=image+p.target)return false;}return true;
#else
 return false;
#endif
}
bool ReadRiteCreateRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const RiteCreateFrame267V1&f,[[maybe_unused]]const RiteCreateRequest267V1&q,[[maybe_unused]]const std::optional<RiteCreateAssociation267V1>&a,[[maybe_unused]]std::uint64_t mono,RiteCreateRaw267V1&out,std::string&why)noexcept{
 out={};why="rite_create_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_CREATE_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_CREATE_V1
 if(!VerifyRiteCreateImage267V1(b.module_base)||!Fresh(b,f,q.deadline_unix_ms,mono)){why="rite_create_actual_image_or_world_unavailable";return false;}
 try{RiteCreateRaw267V1 samples[2];for(auto&sample:samples){if(!Fresh(b,f,q.deadline_unix_ms,mono))return false;bool good=false;if(q.action==RiteCreateAction267V1::query||q.action==RiteCreateAction267V1::create)good=Draft(b,f,q,mono,sample,why);else if(a)good=Confirmation(b,f,q,*a,mono,sample,why);out=sample;if(!good||!sample.cleanup_known)return false;}
  if(samples[0]!=samples[1]){why="rite_create_actual_source_changed_between_samples";return false;}out=samples[1];why.clear();return true;
 }catch(...){why="rite_create_actual_source_exception";return false;}
#else
 return false;
#endif
}
bool BindRiteCreateConfirmationWindow267V1([[maybe_unused]]const ReadonlyBindings&b,const GuiWindowV1&w,RiteCreateRaw267V1&r,std::string&why)noexcept{
 why="rite_create_named_confirmation_root_unavailable";if(!r.source.confirmation||r.pending||!w.window_found||w.requested_name!="confirmation"||w.context!=r.context||w.tree.empty())return false;
 std::int32_t modal=-1;unsigned roots=0,accepts=0;bool visible=false,enabled=false;
 for(std::size_t i=0;i<w.tree.size();++i){const auto&n=w.tree[i];if(n.name=="basic_confirmation_popup"&&n.widget==r.root&&n.context==r.context){++roots;modal=static_cast<std::int32_t>(i);}}
 if(roots!=1||modal<0)return false;
 for(std::size_t i=0;i<w.tree.size();++i){const auto&n=w.tree[i];if(n.name!="accept_button")continue;auto parent=n.parent_index;std::size_t bound=w.tree.size();bool belongs=false,ancestors=true;while(parent>=0&&bound--){if(static_cast<std::size_t>(parent)>=i)return false;const auto&p=w.tree[static_cast<std::size_t>(parent)];ancestors=ancestors&&p.visible&&p.enabled&&p.context==r.context;if(parent==modal){belongs=true;break;}parent=p.parent_index;}if(belongs){++accepts;visible=n.visible&&ancestors;enabled=n.enabled&&ancestors;}}
 if(accepts!=1)return false;auto&s=*r.source.confirmation;s.accept_button_visible=visible;s.accept_button_enabled=enabled;s.accept_admissible=s.modal_found&&s.original_create_bound&&s.native_can_accept&&visible&&enabled;why.clear();return true;
}
RiteCreateCall267V1 CallRiteCreateRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const RiteCreateFrame267V1&f,[[maybe_unused]]const RiteCreateRequest267V1&q,[[maybe_unused]]const std::optional<RiteCreateAssociation267V1>&a,[[maybe_unused]]std::uint64_t mono,[[maybe_unused]]const RiteCreateRaw267V1&expected)noexcept{
 RiteCreateCall267V1 out;
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_CREATE_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_CREATE_V1
 RiteCreateRaw267V1 actual;std::string why;if(!ReadRiteCreateRaw267V1(b,f,q,a,mono,actual,why)||actual.pending||!actual.cleanup_known)return out;
 // Final named-root fields were freshly read by the owner; structural modal identity is re-read here.
 if(q.action==RiteCreateAction267V1::accept_confirmation){if(!expected.source.confirmation||!expected.source.confirmation->accept_admissible)return out;actual.source.confirmation->accept_button_visible=expected.source.confirmation->accept_button_visible;actual.source.confirmation->accept_button_enabled=expected.source.confirmation->accept_button_enabled;actual.source.confirmation->accept_admissible=expected.source.confirmation->accept_admissible;}
 if(actual!=expected||!Fresh(b,f,q.deadline_unix_ms,mono))return out;
 const auto target=q.action==RiteCreateAction267V1::create?actual.controller:q.action==RiteCreateAction267V1::accept_confirmation?actual.modal:0;
 if(!target||(q.action==RiteCreateAction267V1::create&&(!actual.source.draft||!actual.source.draft->create_admissible)))return out;
 out.entered=true;out.status=RiteCreateCallStatus267V1::indeterminate;
 if(VoidCall(b.module_base,q.action==RiteCreateAction267V1::create?0x16B9F70:0xCF3200,target))out.status=RiteCreateCallStatus267V1::returned;else out.cleanup_known=false;
 if(!Time(q.deadline_unix_ms,mono)||!VerifyRiteCreateImage267V1(b.module_base))out.status=RiteCreateCallStatus267V1::indeterminate;
#endif
 return out;
}
}
