#include "xar_bridge/ck3_121003_lyd26785313_raw_v1.hpp"
#include "ck3_121003_full111_event_read_v1.hpp"
#include "xar_bridge/ck3_121003_lyd_personal26785313_pins_v1.hpp"
#include "xar_bridge/ck3_121003_xqol_threshold26785313_pins_v1.hpp"
#include <algorithm>
#include <chrono>
#include <cstring>
#include <limits>
#include <unordered_set>
#include <windows.h>
#include "ck3_121003_lyd26785313_decisions_v1.inc"
namespace xar::ck3_121003::build26785313 {
#if defined(XAR_CK3_ENABLE_121003_26785313_LYD_V1) && XAR_CK3_ENABLE_121003_26785313_LYD_V1
#include "ck3_121003_lyd26785313_common_v1.inc"
#if defined(XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_READ_V1) && XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_READ_V1
#include "ck3_121003_lyd26785313_full111_queue_v1.inc"
#endif
#include "ck3_121003_lyd26785313_personal_native_v1.inc"
namespace lyd_raw {
using namespace lyd_common;
struct ArrayView{std::uintptr_t address=0,data=0;std::int32_t count=0;std::array<std::byte,16>header{};};
[[maybe_unused]]bool Capture(std::uintptr_t address,std::size_t limit,ArrayView&v,std::vector<std::byte>&proof,bool*header_read=nullptr){
 v.address=address;std::int32_t capacity=0;const bool copied=Bytes(address,v.header.data(),16);if(header_read)*header_read=copied;if(!copied)return false;std::memcpy(&v.data,v.header.data(),8);std::memcpy(&capacity,v.header.data()+8,4);std::memcpy(&v.count,v.header.data()+12,4);
 return v.count>=0&&static_cast<std::size_t>(v.count)<=limit&&capacity>=v.count&&capacity<=0x1000000&&(!v.count||v.data)&&Value(proof,v.count);
}
[[maybe_unused]]bool Recheck(const ArrayView&v){std::array<std::byte,16>now{};return Bytes(v.address,now.data(),16)&&now==v.header;}
[[maybe_unused]]bool NativeVisible(std::uintptr_t image,std::uintptr_t window,bool&v)noexcept{__try{v=reinterpret_cast<bool(__fastcall*)(const void*)>(image+0x2516E20)(reinterpret_cast<const void*>(window));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool NativeManager(std::uintptr_t image,std::uintptr_t&v)noexcept{__try{v=reinterpret_cast<std::uintptr_t>(reinterpret_cast<void*(__fastcall*)()>(image+0xCF2C50)());return v!=0;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool NativeSelect(std::uintptr_t image,std::uintptr_t option,bool&entered,bool&clean)noexcept{__try{if(!reinterpret_cast<bool(__fastcall*)(const void*)>(image+0x1B6CC30)(reinterpret_cast<const void*>(option)))return false;entered=true;reinterpret_cast<void(__fastcall*)(void*)>(image+0x1B6CA10)(reinterpret_cast<void*>(option));return true;}__except(EXCEPTION_EXECUTE_HANDLER){clean=false;return false;}}
[[maybe_unused]]LetterScene267V1 EventScene(const LydScene267V1&s){LetterScene267V1 v;v.wall_deadline=s.wall_deadline;v.jomini=s.jomini;v.gfx=s.gfx;v.context=s.context;v.global=s.global;v.events=s.events_layer;return v;}
[[maybe_unused]]std::optional<LydPersonal267V1>PersonalKey(std::string_view key){for(std::size_t n=0;n<kLydPersonalKeys267V1.size();++n)if(kLydPersonalKeys267V1[n]==key)return static_cast<LydPersonal267V1>(n);return{};}
struct RoleRule{std::string_view definition,key;std::int32_t count,index;LydEventRole267V1 role;};
constexpr std::array<RoleRule,7>rules{{{"lyd.1","lyd_welcome_continue",1,0,LydEventRole267V1::welcome_continue},{"lyd.1002","lyd_play_ritual_music_option_0",2,0,LydEventRole267V1::ritual_music_pay},{"lyd.1002","lyd_play_cancel",2,1,LydEventRole267V1::ritual_music_cancel},{"lyd.1000","lyd_play_reverent_heaven_option_0",2,0,LydEventRole267V1::reverent_heaven_pay},{"lyd.1000","lyd_play_cancel",2,1,LydEventRole267V1::reverent_heaven_cancel},{"lyd.1032","lyd_play_knowing_acting_support_option_0",3,0,LydEventRole267V1::knowing_acting_inquiry},{"lyd.1032","lyd_play_cancel",3,2,LydEventRole267V1::knowing_acting_cancel}}};
[[maybe_unused]]bool Events(const ReadonlyBindings&b,const ck3_1210::CoreSnapshotPrefix&core,const LydScene267V1&s,std::uint64_t mono,LydRaw267V1&out,std::string&reason){
 const auto fail=[&](const char*why){reason=why;return false;};if(s.event_roots.size()>32)return fail("lyd_complete_character_event_census_out_of_bounds");const auto bindings=BindLetterImage267V1(b.module_base,kExecutableSha256);const auto common=EventScene(s);
 if(!ReadLetterRaw267V1(b,bindings,core,common,mono,out.manager_census,reason)){out.cleanup_known=out.manager_census.cleanup_known;out.native_read_entered=out.manager_census.native_read_entered;return false;}
 std::unordered_set<std::uintptr_t>roots;std::vector<std::uintptr_t>joined(s.event_roots.size());for(const auto&r:s.event_roots)if(!r.widget||!roots.insert(r.widget).second)return fail("lyd_character_event_roots_not_unique");
 for(const auto window:out.manager_census.window_pointers){std::uintptr_t vt=0,root=0,context=0;if(!At(window,0,vt))return fail("lyd_event_manager_member_type_unreadable");if(vt!=b.module_base+0x4C5D448)continue;if(!At(window,0x70,root)||!At(window,0x78,context))return fail("lyd_event_resident_root_context_unreadable");if(!root)continue;bool matched=false;for(std::size_t n=0;n<s.event_roots.size();++n)if(s.event_roots[n].widget==root){if(joined[n]||context!=s.context)return fail("lyd_event_root_controller_not_unique");joined[n]=window;matched=true;}
  if(!matched){std::string name;if(!Text(root+0x1B8,256,name))return fail("lyd_unmatched_event_root_name_unreadable");if(name=="character_event")return fail("lyd_complete_character_event_census_missing_controller");}
 }
 LydEventSource267V1 source;source.named_root_count=static_cast<std::int32_t>(s.event_roots.size());std::unordered_set<std::int32_t>instances;
 for(std::size_t n=0;n<s.event_roots.size();++n){const auto&root=s.event_roots[n];if(!joined[n]||!root.visible)return fail("lyd_character_event_inactive_or_unbound_material_unsupported");auto single=common;single.letter=root.widget;single.visible=root.visible;single.enabled=root.enabled;LetterRaw267V1 row;
  if(!ReadLetterRaw267V1(b,bindings,core,single,mono,row,reason)){out.cleanup_known=row.cleanup_known;out.native_read_entered=out.native_read_entered||row.native_read_entered;return false;}out.native_read_entered=out.native_read_entered||row.native_read_entered;
  if(row.window!=joined[n]||row.manager!=out.manager_census.manager||row.windows_header!=out.manager_census.windows_header||row.window_pointers!=out.manager_census.window_pointers||!row.source.instance_id||!row.source.recipient_character_id||!row.source.definition_key||!row.source.opening||!row.source.description||!instances.insert(*row.source.instance_id).second)return fail("lyd_complete_event_manager_or_instance_changed");
  LydEventRow267V1 v;v.instance_id=*row.source.instance_id;v.recipient_character_id=*row.source.recipient_character_id;v.authored_option_count=row.authored_option_count;v.definition_key=*row.source.definition_key;v.opening=*row.source.opening;v.description=*row.source.description;v.named_root_bound=row.source.named_root_bound;v.window_visible=root.visible;v.window_enabled=root.enabled;
  for(const auto&option:row.source.options){LydEventOption267V1 o;o.authored_option_index=option.authored_option_index;o.native_can_select=option.native_can_select;o.text=option.text;o.disabled_reason=option.disabled_reason;for(const auto&rule:rules)if(v.definition_key==rule.definition&&v.authored_option_count==rule.count&&o.authored_option_index==rule.index){o.source_bound_option_key=rule.key;o.permitted_role=rule.role;}v.options.push_back(std::move(o));}
  LydEventRawRow267V1 raw;raw.instance_id=v.instance_id;raw.controller=row.window;raw.root=root.widget;raw.data=row.data;raw.runtime=row.runtime_event;raw.definition=row.definition;raw.option_data=row.options;raw.options=row.option_pointers;raw.material=std::move(row);out.event_rows.push_back(std::move(raw));source.events.push_back(std::move(v));
 }
 source.census_complete=true;out.source.events=std::move(source);return Fresh(b,core,s,mono);
}
[[maybe_unused]]bool ActualPersonal(const ReadonlyBindings&b,std::uintptr_t actor,LydRaw267V1&out,LydPersonalSource267V1&source){
 std::uintptr_t persistent=0;if(!At(actor,0x1C8,persistent)||!persistent)return false;ArrayView a;if(!Capture(persistent+0xD0,64,a,out.semantic_model)||!Value(out.semantic_model,persistent))return false;std::unordered_set<std::string>seen;
 for(std::int32_t n=0;n<a.count;++n){std::uintptr_t definition=0;std::string key;if(!At(a.data,static_cast<std::size_t>(n)*8,definition)||!Key(b.module_base,definition,key,out.semantic_model)||!seen.insert(key).second)return false;source.actual_personal_keys.push_back(std::move(key));}
 if(!Recheck(a))return false;source.actual_personal_complete=true;return true;
}
// Only values already read by Models are described on its failure path.
// No pointer/address, new target read, changed bound or caller selector.
struct PersonalModelDiagnostic {
 const char*stage="headers";
 std::int32_t slot=-1,group=-1,row=-1;
 ArrayView slots,groups,rows;
 bool slots_read=false,groups_read=false,rows_read=false;
 bool definition_read=false,definition_nonnull=false,definition_is_default=false;
 bool personal_read=false,magic_read=false,key_complete=false;
 std::uint8_t personal=0;std::uint32_t magic=0;
 void Item(){definition_read=definition_nonnull=definition_is_default=false;personal_read=magic_read=key_complete=false;personal=0;magic=0;}
 void Header(std::string&why,const char*name,const ArrayView&v,bool read)const{
  why+=';';why+=name;why+="_read=";why+=read?"1":"0";
  if(!read)return;std::int32_t cap=0;std::memcpy(&cap,v.header.data()+8,4);
  why+=';';why+=name;why+="_count=";why+=std::to_string(v.count);
  why+=';';why+=name;why+="_cap=";why+=std::to_string(cap);
  why+=';';why+=name;why+="_nonNull=";why+=v.data?"1":"0";
 }
 bool Fail(std::string&why)const{
  why="lyd_personal_model_unavailable;stage=";why+=stage;
  why+=";slot="+std::to_string(slot)+";group="+std::to_string(group)+";row="+std::to_string(row);
  Header(why,"slots",slots,slots_read);Header(why,"groups",groups,groups_read);Header(why,"rows",rows,rows_read);
  why+=";def_read=";why+=definition_read?"1":"0";
  if(definition_read){why+=";def_nonNull=";why+=definition_nonnull?"1":"0";why+=";def_is_default=";why+=definition_is_default?"1":"0";}
  why+=";personal_read=";why+=personal_read?"1":"0";
  if(personal_read)why+=";personal="+std::to_string(personal);
  why+=";magic_read=";why+=magic_read?"1":"0";
  if(magic_read){why+=";loaded_magic=";why+=magic==0x4744624F?"1":"0";}
  why+=";key_complete=";why+=key_complete?"1":"0";return false;
 }
};
[[maybe_unused]]bool Models(const ReadonlyBindings&b,const ck3_1210::CoreSnapshotPrefix&core,const LydScene267V1&scene,std::uint64_t mono,std::uintptr_t window,std::uintptr_t default_tenet,LydRaw267V1&out,LydPersonalSource267V1&source,std::string&reason){
 PersonalModelDiagnostic d;
 d.stage="slots_capture";if(!Capture(window+0x190,64,d.slots,out.semantic_model,&d.slots_read))return d.Fail(reason);
 d.stage="groups_capture";if(!Capture(window+0x1A8,7,d.groups,out.semantic_model,&d.groups_read))return d.Fail(reason);
 const auto&slots=d.slots;const auto&groups=d.groups;
 std::unordered_set<std::string>slotkeys,keys;std::unordered_set<unsigned>categories;
 for(std::int32_t n=0;n<slots.count;++n){
  d.slot=n;d.Item();const auto item=slots.data+static_cast<std::size_t>(n)*0x70;
  std::uintptr_t definition=0;std::uint8_t personal=0;std::uint32_t magic=0;
  d.stage="slot_definition";d.definition_read=At(item,0x28,definition);d.definition_nonnull=definition!=0;d.definition_is_default=definition==default_tenet;
  if(!d.definition_read||!definition)return d.Fail(reason);
  d.stage="slot_personal";d.personal_read=At(item,0x58,personal);d.personal=personal;
  if(!d.personal_read||personal>1)return d.Fail(reason);
  d.stage="slot_magic";d.magic_read=At(definition,0x38,magic);d.magic=magic;
  if(!d.magic_read)return d.Fail(reason);
  d.stage="slot_personal_proof";if(!Value(out.semantic_model,personal))return d.Fail(reason);
  LydPersonalSlot267V1 row;
  if(magic!=0x4744624F){
   d.stage="slot_empty_identity_or_personal";if(definition!=default_tenet||personal)return d.Fail(reason);
   // The fixed engine default has TPdxNullObject<STenetType> primary.
   d.stage="slot_empty_type";if(!Typed(definition,b.module_base,0x4FC7290))return d.Fail(reason);
   d.stage="slot_empty_proof";if(!Value(out.semantic_model,definition)||!Value(out.semantic_model,magic))return d.Fail(reason);
   row.is_empty=true;source.empty_slot_found=true;
  }else{
   std::string key;d.stage="slot_key";d.key_complete=Key(b.module_base,definition,key,out.semantic_model);
   if(!d.key_complete)return d.Fail(reason);
   d.stage="slot_duplicate_key";if(!slotkeys.insert(key).second)return d.Fail(reason);
   row.definition_key=key;row.is_personal=personal!=0;
  }source.slots.push_back(std::move(row));
 }
 d.slot=-1;d.Item();
 for(std::int32_t n=0;n<groups.count;++n){
  d.group=n;d.row=-1;const auto group=groups.data+static_cast<std::size_t>(n)*0x20;std::uint8_t category=0;
  d.stage="group_category";if(!At(group,0,category)||category>6||!categories.insert(category).second||!Value(out.semantic_model,category))return d.Fail(reason);
  ArrayView rows;d.rows_read=false;d.stage="group_rows_capture";
  const bool captured=Capture(group+8,2048,rows,out.semantic_model,&d.rows_read);d.rows=rows;
  if(!captured)return d.Fail(reason);
  d.stage="candidate_total_bound";if(source.rows.size()+static_cast<std::size_t>(rows.count)>2048)return d.Fail(reason);
  for(std::int32_t k=0;k<rows.count;++k){
   d.row=k;d.Item();const auto item=rows.data+static_cast<std::size_t>(k)*0x70;std::uintptr_t definition=0;std::uint8_t personal=0;std::string key;
   d.stage="candidate_definition";d.definition_read=At(item,0x28,definition);d.definition_nonnull=definition!=0;d.definition_is_default=definition==default_tenet;
   if(!d.definition_read)return d.Fail(reason);
   d.stage="candidate_personal";d.personal_read=At(item,0x58,personal);d.personal=personal;
   if(!d.personal_read||personal>1)return d.Fail(reason);
   d.stage="candidate_key";d.key_complete=Key(b.module_base,definition,key,out.semantic_model);
   if(!d.key_complete)return d.Fail(reason);
   d.stage="candidate_duplicate_key";if(!keys.insert(key).second)return d.Fail(reason);
   d.stage="candidate_personal_proof";if(!Value(out.semantic_model,personal))return d.Fail(reason);
   LydPersonalRow267V1 row;row.group_category=category;row.definition_key=key;row.group_can_pick=category!=0&&category!=6;row.is_personal=personal!=0;
   LydPersonalChoice267V1 choice;choice.key=key;choice.definition=definition;
   if(PersonalKey(key)){
    d.stage="candidate_current_source";if(!Fresh(b,core,scene,mono))return d.Fail(reason);
    bool can=false;out.native_read_entered=true;d.stage="candidate_native_Can_completion";
    if(!lyd_personal_native::CanPick(b.module_base,core.played_character_id,definition,can)){out.cleanup_known=false;return d.Fail(reason);}
    row.native_can_pick=can;
   }out.choices.push_back(std::move(choice));source.rows.push_back(std::move(row));
  }d.stage="group_rows_recheck";if(!Recheck(rows))return d.Fail(reason);
 }
 d.stage="slots_recheck";if(!Recheck(slots))return d.Fail(reason);
 d.stage="groups_recheck";if(!Recheck(groups))return d.Fail(reason);
 source.model_materialized=true;source.slots_complete=true;source.groups_complete=true;
 source.slot_count=slots.count;source.group_count=groups.count;return true;
}
[[maybe_unused]]bool Dialogs(const ReadonlyBindings&b,const ck3_1210::CoreSnapshotPrefix&core,const LydScene267V1&scene,std::uint64_t mono,const std::optional<LydSelectionAssociation267V1>&pending,LydRaw267V1&out,LydPersonalSource267V1&source,std::uintptr_t default_tenet){
 out.native_read_entered=true;if(!NativeManager(b.module_base,out.dialog_manager)){out.cleanup_known=false;return false;}ArrayView dialogs;if(!Capture(out.dialog_manager+0x18,128,dialogs,out.modal_source)||!Value(out.modal_source,out.dialog_manager))return false;std::unordered_set<std::uintptr_t>seen;unsigned active=0,matched=0;
 for(std::int32_t n=0;n<dialogs.count;++n){std::uintptr_t dialog=0,vt=0,root=0,context=0;std::uint8_t closed=1;if(!At(dialogs.data,static_cast<std::size_t>(n)*8,dialog)||!Value(out.modal_source,dialog))return false;if(!dialog)continue;if(!seen.insert(dialog).second||!At(dialog,0,vt)||!At(dialog,0x70,root)||!At(dialog,0x78,context)||!At(dialog,0xA8,closed)||closed>1||!Value(out.modal_source,vt)||!Value(out.modal_source,root)||!Value(out.modal_source,context)||!Value(out.modal_source,closed))return false;
  if(closed||!root)continue;++active;source.blocked_by_visible_modal=true;
  if(vt!=b.module_base+lyd_personal_pins::kAddModalPrimaryVtableRva)continue;
  std::uintptr_t secondary=0,tenet=0;std::int32_t actor=-1;if(!At(dialog,0x10,secondary)||secondary!=b.module_base+lyd_personal_pins::kAddModalSecondary10VtableRva||!At(dialog,0x20,secondary)||secondary!=b.module_base+lyd_personal_pins::kAddModalSecondary20VtableRva||context!=scene.context||!At(dialog,0x130,actor)||!At(dialog,0x138,tenet)||!Value(out.modal_source,actor)||!Value(out.modal_source,tenet))return false;
  std::string key;if(!Key(b.module_base,tenet,key,out.modal_source))return false;const auto personal=PersonalKey(key);if(!personal)continue;
  std::string name;if(!Text(root+0x1B8,256,name)||name!="basic_confirmation_popup")return false;const LydNamedRoot267V1*bound=nullptr;for(const auto&r:scene.confirmation_roots)if(r.widget==root){if(bound)return false;bound=&r;}if(!bound||!bound->visible||actor!=core.played_character_id||++matched>1)return false;
  auto&m=source.add_modal;m.found=true;m.named_root_bound=true;m.visible=bound->visible;m.closed=false;m.personal=personal;out.modal=dialog;
  const bool associated=pending&&pending->personal==personal&&pending->resident==out.resident&&pending->root==out.root&&pending->context==scene.context&&pending->definition==tenet&&pending->actor==out.actor&&pending->wall_deadline==scene.wall_deadline&&GetTickCount64()<pending->monotonic_deadline;
  if(associated){std::uintptr_t old=0;if(!At(out.resident,0x180,old)||old!=default_tenet||!Fresh(b,core,scene,mono))return false;bool can=false;out.native_read_entered=true;if(!lyd_personal_native::CanAccept(b.module_base,dialog,can)){out.cleanup_known=false;return false;}m.native_can_accept=can;}
 }
 if(!Recheck(dialogs))return false;auto&m=source.add_modal;
 if(m.found&&m.native_can_accept==true&&active==1&&source.actor_bound&&source.window_visible&&source.window_enabled&&!source.is_adding&&source.empty_slot_found&&source.actual_personal_complete&&pending){const auto key=kLydPersonalKeys267V1[static_cast<std::size_t>(pending->personal)];m.accept_admissible=std::find(source.actual_personal_keys.begin(),source.actual_personal_keys.end(),key)==source.actual_personal_keys.end();}
 return true;
}
[[maybe_unused]]bool Personal(const ReadonlyBindings&b,const ck3_1210::CoreSnapshotPrefix&core,const LydScene267V1&scene,std::uint64_t mono,const std::optional<LydSelectionAssociation267V1>&pending,LydRaw267V1&out,std::string&reason){
 const auto fail=[&](const char*why){reason=why;return false;};const auto image=b.module_base;out.actor=reinterpret_cast<std::uintptr_t>(ck3_1210::ResolveCoreCharacter(b.core,core.played_character_id));if(!lyd_personal_native::CharacterMatches(reinterpret_cast<void*>(out.actor),core.played_character_id))return fail("lyd_actual_current_character_identity_unavailable");
 std::uintptr_t handler_source=0,source=0,handler=0,context=0,default_tenet=0,secondary=0;std::int32_t actor=-1;std::uint8_t adding=0;
 if(!At(scene.handler,0x618,out.resident)||!out.resident)return fail("lyd_actual_personal_controller_missing");
 if(!Typed(out.resident,image,lyd_personal_pins::kPersonalPrimaryVtableRva)||!At(out.resident,0x10,secondary)||secondary!=image+lyd_personal_pins::kPersonalSecondary10VtableRva||!At(scene.handler,0x40,handler_source)||!At(out.resident,0x98,source)||source!=handler_source||!At(out.resident,0xA0,handler)||handler!=scene.handler||!At(out.resident,0x60,out.root)||!At(out.resident,0x68,context)||context!=scene.context||!At(out.resident,0xE8,actor)||!At(out.resident,0x178,adding)||adding>1||!At(image,0x6A685B0,default_tenet)||!default_tenet)return fail("lyd_actual_personal_type_owner_context_or_default_unavailable");
 LydPersonalSource267V1 v;v.resident_available=true;v.named_root_bound=out.root&&out.root==scene.personal_root;v.window_visible=scene.personal_visible;v.window_enabled=scene.personal_enabled;v.actor_bound=actor==core.played_character_id;v.is_adding=adding!=0;
 if((out.root&&out.root!=scene.personal_root)||(!out.root&&scene.personal_root)||v.window_visible&&(!v.named_root_bound||!v.actor_bound))return fail("lyd_actual_personal_named_root_or_actor_mismatch");
 out.native_read_entered=true;bool native_visible=false;if(!Fresh(b,core,scene,mono)||!NativeVisible(image,out.resident,native_visible)){out.cleanup_known=false;return fail("lyd_native_personal_visibility_completion_unknown");}v.native_window_visible=native_visible;if(native_visible!=v.window_visible)return fail("lyd_actual_native_and_widget_visibility_differ");
 if(!Value(out.semantic_model,out.resident)||!Value(out.semantic_model,handler_source)||!Value(out.semantic_model,out.root)||!Value(out.semantic_model,context)||!Value(out.semantic_model,actor)||!Value(out.semantic_model,adding)||!Value(out.semantic_model,default_tenet)||!ActualPersonal(b,out.actor,out,v))return fail("lyd_actual_personal_membership_unavailable");
 if(v.actor_bound&&v.named_root_bound){if(!Models(b,core,scene,mono,out.resident,default_tenet,out,v,reason))return false;}
 else{ArrayView slots,groups;if(actor!=-1||v.is_adding||native_visible||!Capture(out.resident+0x190,64,slots,out.semantic_model)||!Capture(out.resident+0x1A8,7,groups,out.semantic_model)||slots.count||groups.count||!Recheck(slots)||!Recheck(groups))return fail("lyd_hidden_default_personal_model_not_exact_unmaterialized");}
 if(!Dialogs(b,core,scene,mono,pending,out,v,default_tenet))return fail("lyd_actual_complete_dialog_or_selected_association_unavailable");
 // A free slot ADD starts from the actual default old tenet, never a swap/remove request.
 std::uintptr_t old=0;const bool add_branch=v.is_adding&&At(out.resident,0x180,old)&&old==default_tenet;
 v.open_admissible=!native_visible&&!v.window_visible&&!v.blocked_by_visible_modal;
 v.start_add_admissible=v.window_visible&&v.window_enabled&&v.actor_bound&&v.model_materialized&&v.empty_slot_found&&v.actual_personal_complete&&!v.is_adding&&!v.blocked_by_visible_modal;
 for(std::size_t n=0;n<v.rows.size();++n){auto&r=v.rows[n];const bool absent=std::find(v.actual_personal_keys.begin(),v.actual_personal_keys.end(),r.definition_key)==v.actual_personal_keys.end();out.choices[n].admissible=v.window_visible&&v.window_enabled&&v.actor_bound&&add_branch&&v.empty_slot_found&&v.actual_personal_complete&&!v.blocked_by_visible_modal&&r.group_can_pick&&!r.is_personal&&absent&&r.native_can_pick==true&&PersonalKey(r.definition_key).has_value();}
 out.source.personal=std::move(v);return Fresh(b,core,scene,mono);
}
[[maybe_unused]]bool Sample(const ReadonlyBindings&b,const ck3_1210::CoreSnapshotPrefix&core,const LydScene267V1&s,std::uint64_t mono,const LydRequest267V1&q,const std::optional<LydSelectionAssociation267V1>&pending,LydRaw267V1&out,std::string&reason){
 if(!VerifyLydImage267V1(b.module_base)||!Fresh(b,core,s,mono)||s.kind!=LydKindForAction267V1(q.action)){reason="lyd_exact_image_core_deadline_or_family_unavailable";return false;}out.source.kind=s.kind;
 if(s.kind==LydKind267V1::decisions){if(!ReadLydDecisionRaw267V1(b,core,s,mono,out.decision,reason)){out.cleanup_known=out.decision.cleanup_known;out.native_read_entered=out.decision.native_read_entered;return false;}out.native_read_entered=out.decision.native_read_entered;out.source.decisions=out.decision.source;return Fresh(b,core,s,mono);}
 if(s.kind==LydKind267V1::events)return Events(b,core,s,mono,out,reason);
 if(s.kind==LydKind267V1::personal)return Personal(b,core,s,mono,pending,out,reason);
 if(!s.resources){reason="lyd_existing_typed_resource_snapshot_unavailable";return false;}LydReadbackSource267V1 v;v.resources=s.resources;out.source.readback=v;return Fresh(b,core,s,mono);
}
} // namespace lyd_raw
#if defined(XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_OPTION_V2) && XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_OPTION_V2
#include "ck3_121003_full111_event_option_raw_v2.inc"
#endif
#endif
bool VerifyLydImage267V1([[maybe_unused]]std::uintptr_t image)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_LYD_V1) && XAR_CK3_ENABLE_121003_26785313_LYD_V1
 if(!VerifyLydDecisionImage267V1(image)||!VerifyLetterImage267V1(image))return false;std::array<unsigned char,4096>buffer{};
 const auto code=[&](const auto&pins){for(const auto&pin:pins){if(pin.bytes.empty()||pin.bytes.size()>kImageSize||pin.rva>kImageSize-pin.bytes.size())return false;for(std::size_t off=0;off<pin.bytes.size();off+=buffer.size()){const auto n=(std::min)(buffer.size(),pin.bytes.size()-off);if(!lyd_common::Bytes(image+pin.rva+off,buffer.data(),n)||std::memcmp(buffer.data(),pin.bytes.data()+off,n))return false;}}return true;};
 if(!code(lyd_personal_pins::kPins)||!code(lyd_personal_pins::kDataPins))return false;for(const auto&pin:lyd_personal_pins::kPointerPins){std::uintptr_t v=0;if(!lyd_common::At(image,pin.rva,v)||v!=image+pin.expected_target_rva)return false;}
 constexpr std::array<unsigned char,91>string_factory{0x48,0x83,0xEC,0x28,0x65,0x48,0x8B,0x04,0x25,0x58,0x00,0x00,0x00,0xB9,0x1C,0x00,0x00,0x00,0x48,0x8B,0x00,0x8B,0x04,0x01,0x39,0x05,0x8A,0x64,0xFE,0x05,0x7F,0x0C,0x48,0x8D,0x05,0xE1,0x2E,0x46,0x05,0x48,0x83,0xC4,0x28,0xC3,0x48,0x8D,0x0D,0x75,0x64,0xFE,0x05,0xE8,0x8C,0xE1,0xF4,0x03,0x83,0x3D,0x69,0x64,0xFE,0x05,0xFF,0x75,0xDF,0x48,0x8D,0x0D,0x78,0xB3,0x04,0x04,0xE8,0x6B,0xE5,0xF4,0x03,0x48,0x8D,0x0D,0x54,0x64,0xFE,0x05,0xE8,0xFF,0xE0,0xF4,0x03,0xEB,0xC5};
 const auto exact=[&](std::uintptr_t rva,const auto&bytes){return lyd_common::Bytes(image+rva,buffer.data(),bytes.size())&&!std::memcmp(buffer.data(),bytes.data(),bytes.size());};
 if(!exact(0x8C21D0,string_factory)||!exact(0x896BB0,xqol_threshold_pins::kCode_00896BB0)||!exact(0x897460,xqol_threshold_pins::kCode_00897460))return false;
 // Existing a789 sealed prefix establishes this actual virtual visibility receiver; this is a prefix pin, not a claimed complete function body.
 constexpr std::array<unsigned char,64>visible_prefix{0x48,0x89,0x5C,0x24,0x08,0x57,0x48,0x83,0xEC,0x20,0x48,0x8B,0x59,0x60,0x48,0x85,0xDB,0x74,0x70,0xBA,0x01,0x00,0x00,0x00,0x48,0x8B,0xCB,0xE8,0x20,0xC7,0xB7,0x01,0x48,0x63,0xF8,0x83,0xFF,0xFF,0x74,0x1A,0xE8,0xB3,0x12,0xCD,0x01,0x4C,0x69,0xC7,0x08,0x03,0x00,0x00,0x48,0x8B,0x00,0x41,0x80,0xBC,0x00,0x00,0x03,0x00,0x00,0x00};
 return lyd_common::Bytes(image+0x2516E20,buffer.data(),visible_prefix.size())&&!std::memcmp(buffer.data(),visible_prefix.data(),visible_prefix.size());
#else
 return false;
#endif
}
bool ReadLydRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&core,[[maybe_unused]]const LydScene267V1&s,[[maybe_unused]]std::uint64_t mono,[[maybe_unused]]const LydRequest267V1&q,[[maybe_unused]]const std::optional<LydSelectionAssociation267V1>&pending,LydRaw267V1&out,std::string&reason)noexcept{
 out={};reason="current_lyd_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_LYD_V1) && XAR_CK3_ENABLE_121003_26785313_LYD_V1
 LydRaw267V1 a,z;try{if(!lyd_raw::Sample(b,core,s,mono,q,pending,a,reason)){out=std::move(a);return false;}if(!lyd_raw::Sample(b,core,s,mono,q,pending,z,reason)){z.native_read_entered=z.native_read_entered||a.native_read_entered;out=std::move(z);return false;}if(a!=z){out=std::move(z);reason="lyd_complete_source_changed_between_samples";return false;}out=std::move(z);reason.clear();return true;}catch(...){out.native_read_entered=a.native_read_entered||z.native_read_entered;out.cleanup_known=!out.native_read_entered;reason="lyd_actual_read_completion_unknown";return false;}
#else
 return false;
#endif
}
bool ReadFull111LydEventsWithQueueV1([[maybe_unused]]const ReadonlyBindings&bindings,
 [[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&core,[[maybe_unused]]const LydScene267V1&scene,
 [[maybe_unused]]std::uint64_t mono,[[maybe_unused]]const LydRequest267V1&request,
 [[maybe_unused]]std::uintptr_t owner_game,LydRaw267V1&out,std::string&reason,
 [[maybe_unused]]full111_event_queue::Sample* witness)noexcept{
 out={};reason="current111_ordinary_event_read_default_off";
#if defined(XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_READ_V1) && XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_READ_V1
 full111_event_queue::Sample before{},after{};
 if(request.action!=LydAction267V1::query_events||!core.clock.paused||
     !full111_event_queue::Capture(bindings,owner_game,before)){
  reason="current111_ordinary_event_queue_unavailable";return false;
 }
 if(!ReadLydRaw267V1(bindings,core,scene,mono,request,{},out,reason))return false;
 if(!full111_event_queue::Capture(bindings,owner_game,after)||before!=after||
     !full111_event_queue::Matches(after,owner_game,core.played_character_id,out)){
  reason="current111_ordinary_events_do_not_cover_runtime_queue";return false;
 }
 if(witness)*witness=after;
 return true;
#else
 return false;
#endif
}
bool ReadFull111LydEventRaw267V1(const ReadonlyBindings& bindings,const ck3_1210::CoreSnapshotPrefix& core,
 const LydScene267V1& scene,std::uint64_t mono,const LydRequest267V1& request,
 std::uintptr_t owner_game,LydRaw267V1& out,std::string& reason)noexcept{
 return ReadFull111LydEventsWithQueueV1(bindings,core,scene,mono,request,owner_game,out,reason,nullptr);
}
void TokenizeLydRaw267V1(LydRaw267V1&raw,std::uint64_t generation,std::uint64_t query){
 raw.token_generation=generation;raw.token_query=query;if(!raw.source.personal)return;auto&s=*raw.source.personal;std::unordered_set<std::string>tokens;
 for(std::size_t n=0;n<raw.choices.size();++n){auto&v=raw.choices[n];std::uint64_t h=1469598103934665603ULL;const auto mix=[&](std::uint64_t x){for(unsigned k=0;k<8;++k){h^=static_cast<unsigned char>(x>>(k*8));h*=1099511628211ULL;}};mix(generation);mix(query);mix(v.definition);mix(raw.actor);for(const unsigned char c:v.key){h^=c;h*=1099511628211ULL;}
  v.token="lyd."+std::to_string(generation)+"."+std::to_string(query)+"."+std::to_string(h);if(!tokens.insert(v.token).second)v.admissible=false;if(n<s.rows.size()){s.rows[n].choice_token=v.token;s.rows[n].select_admissible=v.admissible;}
 }
}
bool SameLydRawForLease267V1(const LydRaw267V1&a,const LydRaw267V1&b)noexcept{try{auto left=a,right=b;left.decision.rows.fill(0);right.decision.rows.fill(0);return left==right;}catch(...){return false;}}
bool LydRawAdmissible267V1(const LydRaw267V1&raw,const LydRequest267V1&q)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_LYD_V1) && XAR_CK3_ENABLE_121003_26785313_LYD_V1
 return raw.cleanup_known&&LydPublicAdmissible267V1(raw.source,q);
#else
 (void)raw;(void)q;return false;
#endif
}
LydRawCall267V1 CallLydRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&core,[[maybe_unused]]const LydScene267V1&s,[[maybe_unused]]std::uint64_t mono,[[maybe_unused]]const LydRequest267V1&q,[[maybe_unused]]const std::optional<LydSelectionAssociation267V1>&pending,[[maybe_unused]]const LydRaw267V1&issued)noexcept{
 LydRawCall267V1 call;
#if defined(XAR_CK3_ENABLE_121003_26785313_LYD_V1) && XAR_CK3_ENABLE_121003_26785313_LYD_V1
 try{LydRaw267V1 actual;std::string reason;if(!ReadLydRaw267V1(b,core,s,mono,q,pending,actual,reason)){call.cleanup_known=actual.cleanup_known;if(!call.cleanup_known)call.status=LydRawCallStatus267V1::indeterminate;return call;}TokenizeLydRaw267V1(actual,issued.token_generation,issued.token_query);if(!SameLydRawForLease267V1(actual,issued)||!LydRawAdmissible267V1(actual,q)||!lyd_common::Fresh(b,core,s,mono))return call;
  if(s.kind==LydKind267V1::decisions){const auto n=static_cast<unsigned>(q.action);if(n>3||n==0)return call;const auto result=CallLydDecisionRaw267V1(b,core,s,mono,actual.decision,static_cast<LydDecisionAction267V1>(n),q.decision);call.effect_entered=result.effect_entered;call.cleanup_known=result.cleanup_known;call.native_handled=result.native_handled;call.status=result.status==LydDecisionRawCallStatus267V1::returned?LydRawCallStatus267V1::returned:result.status==LydDecisionRawCallStatus267V1::indeterminate?LydRawCallStatus267V1::indeterminate:LydRawCallStatus267V1::refused;return call;}
  if(q.action==LydAction267V1::choose_known_event_option){for(std::size_t n=0;n<actual.source.events->events.size();++n){const auto&row=actual.source.events->events[n];if(row.instance_id!=q.instance_id)continue;for(std::size_t k=0;k<row.options.size();++k)if(row.options[k].permitted_role==q.event_role){if(k>=actual.event_rows[n].options.size())return call;if(!lyd_raw::NativeSelect(b.module_base,actual.event_rows[n].options[k],call.effect_entered,call.cleanup_known)){if(call.effect_entered||!call.cleanup_known)call.status=LydRawCallStatus267V1::indeterminate;return call;}call.status=LydRawCallStatus267V1::returned;return call;}}return call;}
  if(q.action==LydAction267V1::open_personal)return lyd_personal_native::Open(b,core,s,mono,reinterpret_cast<void*>(actual.actor));
  std::uintptr_t definition=0;if(q.action==LydAction267V1::select_personal_candidate){for(const auto&choice:actual.choices)if(choice.token==q.choice_token&&choice.admissible){definition=choice.definition;break;}if(!definition)return call;bool can=false;if(!lyd_personal_native::CanPick(b.module_base,core.played_character_id,definition,can)){call.cleanup_known=false;call.status=LydRawCallStatus267V1::indeterminate;return call;}if(!can)return call;}
  if(q.action==LydAction267V1::confirm_personal_add){bool can=false;if(!lyd_personal_native::CanAccept(b.module_base,actual.modal,can)){call.cleanup_known=false;call.status=LydRawCallStatus267V1::indeterminate;return call;}if(!can)return call;}
  if(!lyd_common::Fresh(b,core,s,mono))return call;return lyd_personal_native::Call(b.module_base,actual.resident,definition,actual.modal,q.action);
 }catch(...){call.status=LydRawCallStatus267V1::indeterminate;call.cleanup_known=false;}
#endif
 return call;
}
} // namespace
