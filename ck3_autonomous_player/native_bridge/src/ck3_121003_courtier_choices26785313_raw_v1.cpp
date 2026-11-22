#include "xar_bridge/ck3_121003_courtier_choices26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_courtier_choices26785313_pins_v1.hpp"
#include <algorithm>
#include <chrono>
#include <cstring>
#include <cstdio>
#include <unordered_set>
#include <span>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {
#include "ck3_121003_courtier_configuration26785313_native_v1.inc"
#include "ck3_121003_courtier_choices26785313_native_v1.inc"
namespace {
[[maybe_unused]]bool Copy(std::uintptr_t p,void*out,std::size_t n)noexcept{if(!p||!n)return false;__try{std::memcpy(out,reinterpret_cast<const void*>(p),n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
template<class T>bool At(std::uintptr_t p,std::size_t off,T&v)noexcept{return p&&Copy(p+off,&v,sizeof(v));}
[[maybe_unused]]bool Fresh(const ReadonlyBindings&b,const ck3_1210::CoreSnapshotPrefix&expected,const CourtierChoicesScene267V1&scene,std::uint64_t mono)noexcept{
 const auto wall=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();if(!mono||GetTickCount64()>=mono||wall<=0||!scene.wall_deadline||static_cast<std::uint64_t>(wall)>=scene.wall_deadline)return false;
 __try{ck3_1210::CoreSnapshotPrefix actual;std::uintptr_t jomini=0,application=0,vt=0,first=0,context=0,global=0;
  return ck3_1210::ReadCoreSnapshot(b.core,actual)&&actual.clock.date_raw==expected.clock.date_raw&&actual.clock.speed==expected.clock.speed&&actual.clock.paused==expected.clock.paused&&actual.local_player_id==expected.local_player_id&&actual.map_ready==expected.map_ready&&actual.has_played_character==expected.has_played_character&&actual.played_character_id==expected.played_character_id&&actual.played_character_alive==expected.played_character_alive&&
   At(reinterpret_cast<std::uintptr_t>(b.core.jomini_state_slot),0,jomini)&&jomini==scene.jomini&&At(jomini,0x18,application)&&application==scene.application&&At(application,0,vt)&&vt==b.module_base+0x4AFA650&&At(application,0x1B8,first)&&At(first,0x58,context)&&context==scene.context&&At(context,0xD0,global)&&global==scene.global;
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool NodeStillCurrent(const GuiWindowNodeV1&n)noexcept{
 std::uint8_t flags=0;std::uintptr_t vt=0,context=0,parent=0,children=0,data=0;std::int32_t cap=0,count=0;std::uint64_t length=0,capacity=0;std::array<char,kGuiWindowMaxNameBytesV1+1>name{};
 if(!n.widget||n.name.size()>kGuiWindowMaxNameBytesV1||!At(n.widget,0,vt)||vt!=n.vtable||!At(n.widget,0xD0,flags)||flags!=n.flags||!At(n.widget,0xD8,context)||context!=n.context||!At(n.widget,0xE8,parent)||parent!=n.parent||!At(n.widget,0xF0,children)||children!=n.children||!At(n.widget,0xF8,cap)||cap!=n.child_capacity||!At(n.widget,0xFC,count)||count!=n.child_count||!At(n.widget,0x1C8,length)||length!=n.name_size||!At(n.widget,0x1D0,capacity)||capacity!=n.name_capacity)return false;
 if(capacity==15)data=n.widget+0x1B8;else if(capacity<=15||!At(n.widget,0x1B8,data))return false;
 return data==n.name_data&&length==n.name.size()&&Copy(data,name.data(),static_cast<std::size_t>(length)+1)&&name[length]==0&&std::string_view(name.data(),static_cast<std::size_t>(length))==n.name;
}
[[maybe_unused]]void* ResolveCourtierActor267V1(const ReadonlyBindings&b,std::int32_t id)noexcept{__try{return ck3_1210::ResolveCoreCharacter(b.core,id);}__except(EXCEPTION_EXECUTE_HANDLER){return nullptr;}}

struct ChoiceModel267V1{std::uintptr_t array=0,data=0;std::int32_t cap=0,count=0;};
bool ReadChoiceModel267V1(std::uintptr_t image,void*actor,std::int32_t actor_id,CourtierProduct267V1 product,CourtierCatalog267V1 catalog,ChoiceModel267V1&out,bool&cleanup)noexcept{
 cleanup=true;out={};if(static_cast<unsigned>(product)>1||static_cast<unsigned>(catalog)>6)return false;
 constexpr std::array<const char*,7>suffix{"education","commander","physical","personality","other","culture_heritages","faiths"};
 std::array<char,96>name{};const int n=std::snprintf(name.data(),name.size(),"%s_cc_catalog_%s",product==CourtierProduct267V1::main?"xar":"ervc",suffix[static_cast<unsigned>(catalog)]);if(n<=0||static_cast<std::size_t>(n)>=name.size())return false;
 ChoiceAny267V1 root{},key{};std::uintptr_t empty=0,reference=0,string=0;bool initialized=false,root_entered=false,root_complete=false,key_entered=false,key_complete=false,good=false;
 __try{using Factory=std::uintptr_t(__fastcall*)();empty=reinterpret_cast<Factory>(image+0x8B2EF0)();reference=reinterpret_cast<Factory>(image+0x8B5030)();string=reinterpret_cast<Factory>(image+0x8C21D0)();root.type=key.type=empty;initialized=true;
 do{root_entered=true;if(!reinterpret_cast<bool(__fastcall*)(void*,ChoiceAny267V1*)>(image+0x2BA7A20)(actor,&root)||root.type!=reference)break;root_complete=true;std::uint32_t actual_tag=0,actual_id=0;std::memcpy(&actual_tag,root.storage.data(),4);std::memcpy(&actual_id,root.storage.data()+8,4);if(actual_tag!=4||actual_id!=static_cast<std::uint32_t>(actor_id))break;
 key.type=string;std::uint64_t cap=15;std::memcpy(key.storage.data()+24,&cap,8);key_entered=true;reinterpret_cast<void*(__fastcall*)(void*,const char*,std::size_t)>(image+0x896BB0)(key.storage.data(),name.data(),static_cast<std::size_t>(n));key_complete=true;
 out.array=catalog==CourtierCatalog267V1::culture?reinterpret_cast<std::uintptr_t(__fastcall*)(const void*)>(image+0x3D59E90)(key.storage.data()):reinterpret_cast<std::uintptr_t(__fastcall*)(const void*,const void*)>(image+0x3D59E30)(root.storage.data(),key.storage.data());if(!out.array||out.array==image+0x5D6AB38||!At(out.array,0,out.data)||!At(out.array,8,out.cap)||!At(out.array,12,out.count)||out.count<0||out.count>2048||out.cap<out.count||out.cap>4096||(out.count&&!out.data))break;
 good=true;
 }while(false);
 }__except(EXCEPTION_EXECUTE_HANDLER){cleanup=false;}
 if(initialized){const std::array<std::uintptr_t,2>allowed{reference,string};if(!root_entered||root_complete||root.type==empty){if(!DestroyChoiceAny267V1(root,empty,allowed))cleanup=false;}else cleanup=false;if(!key_entered||key_complete||key.type==empty){if(!DestroyChoiceAny267V1(key,empty,allowed))cleanup=false;}else cleanup=false;}
 return good&&cleanup;
}
bool ModelStill(const ChoiceModel267V1&m)noexcept{std::uintptr_t data=0;std::int32_t cap=0,count=0;return At(m.array,0,data)&&At(m.array,8,cap)&&At(m.array,12,count)&&data==m.data&&cap==m.cap&&count==m.count;}

bool CultureReference267V1(std::uintptr_t image,std::uintptr_t culture,std::array<std::byte,16>&out,bool&cleanup)noexcept{
 cleanup=true;ChoiceAny267V1 result{};std::uintptr_t empty=0,type=0;bool initialized=false,entered=false,complete=false,good=false;__try{using Factory=std::uintptr_t(__fastcall*)();empty=reinterpret_cast<Factory>(image+0x8B2EF0)();type=reinterpret_cast<Factory>(image+0x8B5030)();result.type=empty;initialized=true;entered=true;if(culture&&reinterpret_cast<bool(__fastcall*)(void*,ChoiceAny267V1*)>(image+0x2BA5410)(reinterpret_cast<void*>(culture),&result)&&result.type==type){complete=true;std::memcpy(out.data(),result.storage.data(),16);good=true;}}__except(EXCEPTION_EXECUTE_HANDLER){cleanup=false;}if(initialized){if(!entered||complete||result.type==empty){if(!DestroyChoiceAny267V1(result,empty,std::span<const std::uintptr_t>(&type,1)))cleanup=false;}else cleanup=false;}return good&&cleanup;
}
bool PillarCultures267V1(std::uintptr_t image,const std::array<std::byte,16>&reference,std::array<std::uintptr_t,2048>&cultures,std::int32_t&count,CourtierChoiceIdentity267V1&identity,bool&cleanup)noexcept{
 count=0;cleanup=true;__try{std::uint16_t tag=0;std::int32_t id=-1;std::memcpy(&tag,reference.data(),2);std::memcpy(&id,reference.data()+8,4);std::uintptr_t db=0,data=0,wanted=0,fallback=0;std::int32_t size=0;if(tag!=0x32||id<0||!At(image,0x68AFBF0,db)||!At(image,0x6A66AB0,fallback)||!At(db,0x50,data)||!At(db,0x5C,size)||size<0||id>=size||!At(data,static_cast<std::size_t>(id)*8,wanted)||!wanted||wanted==fallback)return false;std::int32_t actual=-1;if(!At(wanted,0x10,actual)||actual!=id)return false;
 const auto pillar=reinterpret_cast<std::uintptr_t(__fastcall*)(const void*)>(image+0x2623020)(reference.data());if(pillar!=wanted)return false;
 const auto array=reinterpret_cast<std::uintptr_t(__fastcall*)(const void*)>(image+0xEEAAE0)(reinterpret_cast<void*>(pillar));std::uintptr_t pointers=0;std::int32_t capacity=0;if(array!=image+0x5D57850||!At(array,0,pointers)||!At(array,8,capacity)||!At(array,12,count)||count<0||count>2048||capacity<count||capacity>4096||(count&&!pointers)||(count&&!Copy(pointers,cultures.data(),static_cast<std::size_t>(count)*8)))return false;
 std::uintptr_t current=0;std::int32_t current_count=0;if(!At(array,0,current)||current!=pointers||!At(array,12,current_count)||current_count!=count)return false;identity.reference=reference;identity.definition=pillar;if(!Copy(pillar,identity.definition_header.data(),64))return false;return true;
 }__except(EXCEPTION_EXECUTE_HANDLER){cleanup=false;return false;}
}
bool Capture(const ReadonlyBindings&b,const ck3_1210::CoreSnapshotPrefix&core,const CourtierChoicesScene267V1&scene,std::uint64_t mono,CourtierProduct267V1 product,CourtierCatalog267V1 catalog,CourtierChoicesRaw267V1&out,std::string&reason){
 const auto fail=[&](const char*s){reason=s;return false;};
 if(!VerifyCourtierChoicesImage267V1(b.module_base)||!Fresh(b,core,scene,mono)||(scene.chain.size()!=2&&scene.chain.size()!=5)||static_cast<unsigned>(catalog)>6)return fail("courtier_choices_actual_image_owner_or_chain_unavailable");
 const auto prefix=product==CourtierProduct267V1::main?"xar":"ervc";
 for(std::size_t n=0;n<scene.chain.size();++n){const auto&node=scene.chain[n];if(!NodeStillCurrent(node)||node.context!=scene.context||(n==0?(node.widget!=scene.global||node.parent!=0):node.parent!=scene.chain[n-1].widget))return fail("courtier_choices_actual_fixed_chain_changed");if(n==1&&node.name!="confirmation")return fail("courtier_choices_actual_confirmation_missing");if(n>=2&&node.name!=std::string(prefix)+(n==2?"_courtier_creator_window":n==3?"_courtier_creator_modal":"_courtier_creator_panel"))return fail("courtier_choices_product_literal_mismatch");}
 auto&s=out.source;s.product=product;s.catalog=catalog;s.confirmation_layer_found=true;if(scene.chain.size()==2)return Fresh(b,core,scene,mono);
 
 s.creator_window_found=s.modal_found=s.panel_found=true;s.window_visible=s.window_enabled=true;for(const auto&node:scene.chain){s.window_visible=s.window_visible&&node.visible;s.window_enabled=s.window_enabled&&node.enabled;}
 auto*actor=ResolveCourtierActor267V1(b,core.played_character_id);if(!actor)return fail("courtier_choices_actual_player_unavailable");out.actor=reinterpret_cast<std::uintptr_t>(actor);
 CourtierNative267V1 values;out.native_read_entered=true;if(!NativeFixedCourtier267V1(b.module_base,actor,static_cast<std::uint32_t>(core.played_character_id),product,CourtierSetting267V1::choose_female,scene.wall_deadline,mono,0,CourtierNativePhase267V1::read_predicates,values)){out.cleanup_known=values.cleanup_known;return fail("courtier_choices_actual_configuration_unavailable");}out.cleanup_known=values.cleanup_known;s.configuration=values.configuration;out.cost_definition=values.cost_definition;const bool numeric=std::all_of(values.configuration.raw.begin(),values.configuration.raw.end(),[](const auto&v){return v.has_value();});
 ChoiceModel267V1 model;if(!ReadChoiceModel267V1(b.module_base,actor,core.played_character_id,product,catalog,model,out.cleanup_known))return fail("courtier_choices_actual_complete_catalog_model_unavailable");
 std::vector<std::array<std::byte,16>>references(static_cast<std::size_t>(model.count));if(model.count&&!Copy(model.data,references.data(),references.size()*16))return fail("courtier_choices_actual_catalog_rows_unreadable");if(!ModelStill(model))return fail("courtier_choices_actual_catalog_header_changed");std::unordered_set<std::string>keys;std::vector<std::array<std::byte,16>>leaf_references=references;
 if(catalog==CourtierCatalog267V1::culture){leaf_references.clear();std::unordered_set<std::uint32_t>handles;for(const auto&pillar_ref:references){std::array<std::uintptr_t,2048>cultures{};std::int32_t count=0;CourtierChoiceIdentity267V1 ancestor;if(!Fresh(b,core,scene,mono)||!ModelStill(model)||!PillarCultures267V1(b.module_base,pillar_ref,cultures,count,ancestor,out.cleanup_known))return fail("courtier_choices_actual_pillar_or_nested_culture_model_unavailable");out.ancestors.push_back(ancestor);for(std::int32_t n=0;n<count;++n){std::array<std::byte,16>reference{};if(!CultureReference267V1(b.module_base,cultures[n],reference,out.cleanup_known))return fail("courtier_choices_actual_culture_make_scope_unavailable");ChoiceIdentity267V1 identity;if(!ReadChoiceIdentity267V1(b.module_base,catalog,reference,identity,out.cleanup_known))return fail("courtier_choices_actual_culture_registry_identity_unavailable");std::uint32_t handle=0;std::memcpy(&handle,reference.data()+8,4);if(handles.insert(handle).second){if(leaf_references.size()>=2048)return fail("courtier_choices_actual_full_culture_census_bound_exceeded");leaf_references.push_back(reference);}}}}
 for(const auto&reference:leaf_references){if(!Fresh(b,core,scene,mono)||!ModelStill(model))return fail("courtier_choices_actual_model_or_deadline_changed");ChoiceIdentity267V1 identity;if(!ReadChoiceIdentity267V1(b.module_base,catalog,reference,identity,out.cleanup_known))return fail("courtier_choices_actual_row_type_or_canonical_identity_unavailable");const std::string key(identity.key.data(),identity.key_size);if(!keys.insert(key).second)return fail("courtier_choices_actual_catalog_duplicate_key");ChoiceScope267V1 predicates;if(!NativeChoiceScope267V1(b.module_base,actor,core.played_character_id,product,catalog,identity,scene.wall_deadline,mono,0,0,ChoiceScopePhase267V1::predicates,predicates)){out.cleanup_known=predicates.cleanup_known;return fail("courtier_choices_actual_row_native_predicates_unavailable");}
 s.rows.push_back({{},key,predicates.shown,predicates.valid,predicates.selected,s.window_visible&&s.window_enabled&&predicates.shown&&predicates.valid&&numeric});out.identities.push_back({identity.reference,identity.definition,identity.definition_header,predicates.action_definition,predicates.selected_definition,predicates.action_header,predicates.selected_header});
 }
 std::vector<std::array<std::byte,16>>after(references.size());if((model.count&&!Copy(model.data,after.data(),after.size()*16))||!ModelStill(model)||after!=references)return fail("courtier_choices_actual_catalog_rows_changed_within_sample");
 s.model_available=s.complete_model=true;s.catalog_count=static_cast<std::int32_t>(leaf_references.size());return Fresh(b,core,scene,mono);
}

}

bool SameCourtierChoicesRaw267V1(const CourtierChoicesRaw267V1&a,const CourtierChoicesRaw267V1&b)noexcept{
 if(a.identities.size()!=a.source.rows.size()||b.identities.size()!=b.source.rows.size()||a.ancestors.size()!=b.ancestors.size())return false;for(std::size_t i=0;i<a.ancestors.size();++i){const auto&x=a.ancestors[i];const auto&y=b.ancestors[i];if(!ChoiceReferenceSame267V1(x.reference.data(),y.reference.data())||x.definition!=y.definition||x.definition_header!=y.definition_header)return false;}
 if(a.actor!=b.actor||a.cost_definition!=b.cost_definition||!a.cleanup_known||!b.cleanup_known||a.identities.size()!=b.identities.size())return false;
 for(std::size_t i=0;i<a.identities.size();++i){const auto&x=a.identities[i];const auto&y=b.identities[i];if(!ChoiceReferenceSame267V1(x.reference.data(),y.reference.data())||x.definition!=y.definition||x.definition_header!=y.definition_header||x.action_definition!=y.action_definition||x.selected_definition!=y.selected_definition||x.action_header!=y.action_header||x.selected_header!=y.selected_header)return false;}
 try{auto x=a.source,y=b.source;for(auto&row:x.rows)row.choice_token.clear();for(auto&row:y.rows)row.choice_token.clear();return x==y;}catch(...){return false;}
}
bool VerifyCourtierChoicesImage267V1([[maybe_unused]]std::uintptr_t image)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_COURTIER_CHOICES_V1) && XAR_CK3_ENABLE_121003_26785313_COURTIER_CHOICES_V1
 if(!VerifyCourtierConfigurationImage267V1(image))return false;std::array<std::byte,256>buffer{};for(const auto&pin:courtier_choices_pins::kPins){if(pin.bytes.empty())return false;for(std::size_t offset=0;offset<pin.bytes.size();offset+=buffer.size()){const auto n=(std::min)(buffer.size(),pin.bytes.size()-offset);if(!Copy(image+pin.rva+offset,buffer.data(),n)||std::memcmp(buffer.data(),pin.bytes.data()+offset,n))return false;}}return true;
#else
 return false;
#endif
}
bool ReadCourtierChoicesRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&core,[[maybe_unused]]const CourtierChoicesScene267V1&scene,[[maybe_unused]]std::uint64_t mono,[[maybe_unused]]CourtierProduct267V1 product,[[maybe_unused]]CourtierCatalog267V1 catalog,CourtierChoicesRaw267V1&out,std::string&reason)noexcept{
 out={};reason="current_courtier_choices_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_COURTIER_CHOICES_V1) && XAR_CK3_ENABLE_121003_26785313_COURTIER_CHOICES_V1
 CourtierChoicesRaw267V1 a,z;try{if(!Capture(b,core,scene,mono,product,catalog,a,reason)){out=std::move(a);return false;}if(!Capture(b,core,scene,mono,product,catalog,z,reason)){z.native_read_entered=z.native_read_entered||a.native_read_entered;out=std::move(z);return false;}if(!SameCourtierChoicesRaw267V1(a,z)){out=std::move(z);reason="courtier_choices_actual_semantic_complete_model_changed_between_samples";return false;}out=std::move(z);reason.clear();return true;}catch(...){out.native_read_entered=a.native_read_entered||z.native_read_entered;out.cleanup_known=!out.native_read_entered;reason="courtier_choices_actual_capture_exception";return false;}
#else
 return false;
#endif
}
LetterRawCall267V1 ExecuteCourtierChoiceRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&core,[[maybe_unused]]const CourtierChoicesScene267V1&scene,[[maybe_unused]]std::uint64_t mono,[[maybe_unused]]const CourtierChoicesRaw267V1&issued,[[maybe_unused]]std::size_t index)noexcept{
 LetterRawCall267V1 result;
#if defined(XAR_CK3_ENABLE_121003_26785313_COURTIER_CHOICES_V1) && XAR_CK3_ENABLE_121003_26785313_COURTIER_CHOICES_V1
 CourtierChoicesRaw267V1 fresh;std::string reason;if(!ReadCourtierChoicesRaw267V1(b,core,scene,mono,issued.source.product,issued.source.catalog,fresh,reason)){result.cleanup_known=fresh.cleanup_known;if(!result.cleanup_known)result.status=LetterRawCallStatus267V1::indeterminate;return result;}
 if(!SameCourtierChoicesRaw267V1(issued,fresh)||index>=fresh.source.rows.size()||index>=fresh.identities.size()||!fresh.source.rows[index].execute_admissible||!Fresh(b,core,scene,mono))return result;
 const auto&row=fresh.identities[index];ChoiceIdentity267V1 identity;identity.reference=row.reference;identity.definition=row.definition;identity.definition_header=row.definition_header;identity.key_size=static_cast<std::uint16_t>(fresh.source.rows[index].key.size());std::copy(fresh.source.rows[index].key.begin(),fresh.source.rows[index].key.end(),identity.key.begin());ChoiceScope267V1 call;const bool good=NativeChoiceScope267V1(b.module_base,reinterpret_cast<void*>(fresh.actor),core.played_character_id,fresh.source.product,fresh.source.catalog,identity,scene.wall_deadline,mono,row.action_definition,row.selected_definition,ChoiceScopePhase267V1::execute,call);result.effect_entered=call.effect_entered;result.cleanup_known=call.cleanup_known;if(!call.cleanup_known||(call.effect_entered&&!call.native_returned))result.status=LetterRawCallStatus267V1::indeterminate;else if(good&&call.native_returned)result.status=LetterRawCallStatus267V1::returned;
#endif
 return result;
}
}
