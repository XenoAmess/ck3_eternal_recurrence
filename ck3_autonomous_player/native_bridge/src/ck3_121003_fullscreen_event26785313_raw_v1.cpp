#include "xar_bridge/ck3_121003_fullscreen_event26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_fullscreen_event26785313_pins_v1.hpp"
#include <algorithm>
#include <chrono>
#include <cstring>
#include <limits>
#include <unordered_set>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
[[maybe_unused]]bool Copy(std::uintptr_t p,void*out,std::size_t n)noexcept{if(!p||!out||!n||n-1>(std::numeric_limits<std::uintptr_t>::max)()-p)return false;__try{std::memcpy(out,reinterpret_cast<const void*>(p),n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
template<class T>bool At(std::uintptr_t p,std::size_t off,T&v)noexcept{return p&&off<=(std::numeric_limits<std::uintptr_t>::max)()-p&&Copy(p+off,&v,sizeof(v));}
[[maybe_unused]]bool Equal(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool Fresh(const ReadonlyBindings&b,const ck3_1210::CoreSnapshotPrefix&e,const FullscreenEventScene267V1&s,std::uint64_t mono)noexcept{
 const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();if(!mono||GetTickCount64()>=mono||!s.wall_deadline||t<=0||static_cast<std::uint64_t>(t)>=s.wall_deadline||!e.clock.paused||!e.map_ready||!e.has_played_character||!e.played_character_alive||e.played_character_id==-1)return false;
 __try{ck3_1210::CoreSnapshotPrefix p;return ck3_1210::ReadCoreSnapshot(b.core,p)&&Equal(p,e);}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool CoreEqualSafe(const ReadonlyBindings&b,const ck3_1210::CoreSnapshotPrefix&e)noexcept{__try{ck3_1210::CoreSnapshotPrefix p;return ck3_1210::ReadCoreSnapshot(b.core,p)&&Equal(p,e);}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Text(std::uintptr_t at,std::size_t limit,std::string&out){
 std::uint64_t n=0,cap=0;std::uintptr_t chars=at;if(!At(at,16,n)||!At(at,24,cap)||n>limit||n>cap||cap<15||cap>0x1000000)return false;if(cap==15){if(n>15)return false;}else if(!At(at,0,chars)||!chars)return false;
 std::vector<char>bytes(static_cast<std::size_t>(n)+1);if(!Copy(chars,bytes.data(),bytes.size())||bytes[static_cast<std::size_t>(n)]||std::memchr(bytes.data(),0,static_cast<std::size_t>(n))||(n&&MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,bytes.data(),static_cast<int>(n),nullptr,0)==0))return false;out.assign(bytes.data(),static_cast<std::size_t>(n));return true;
}
[[maybe_unused]]bool NativeLookup(std::uintptr_t image,std::uintptr_t manager,std::int32_t id,std::uintptr_t&out)noexcept{__try{out=reinterpret_cast<std::uintptr_t>(reinterpret_cast<void*(__fastcall*)(void*,std::int32_t)>(image+0x2EBEDB0)(reinterpret_cast<void*>(manager),id));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool NativeCan(std::uintptr_t image,std::uintptr_t option,bool&out)noexcept{__try{out=reinterpret_cast<bool(__fastcall*)(const void*)>(image+0x1B6CC30)(reinterpret_cast<const void*>(option));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool NativeSelect(std::uintptr_t image,std::uintptr_t option)noexcept{__try{reinterpret_cast<void(__fastcall*)(void*)>(image+0x1B6CA10)(reinterpret_cast<void*>(option));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool NativeTimeGate(std::uintptr_t image,std::uintptr_t manager,bool&out)noexcept{__try{out=reinterpret_cast<bool(__fastcall*)(void*,void*)>(image+0x2EBF540)(reinterpret_cast<void*>(manager),nullptr);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Sample(const ReadonlyBindings&b,const FullscreenEventBindings267V1&bindings,const ck3_1210::CoreSnapshotPrefix&e,const FullscreenEventScene267V1&s,std::uint64_t mono,FullscreenEventRaw267V1&out,std::string&reason){
 const auto fail=[&](const char*why){reason=why;return false;};if(!Fresh(b,e,s,mono))return fail("fullscreen_event_original_core_or_deadline_changed");const auto image=bindings.image;std::uintptr_t gfx=0,vt=0,owner=0;std::int32_t cap=0,count=0;
   if(!At(image,kGameStateSlotRva,out.game)||!out.game||!At(image,kJominiStateSlotRva,out.jomini)||out.jomini!=s.jomini||!At(out.jomini,0x10,gfx)||gfx!=s.gfx||!At(gfx,0,vt)||vt!=image+0x4B24748||!At(gfx,0x28,out.manager)||!out.manager||!At(out.manager,0,owner)||owner!=out.jomini)return fail("fullscreen_actual_typed_manager_source_unavailable");
  if(!At(out.manager,0x10,out.window)||!out.window)return fail("fullscreen_actual_splash_controller_missing");
  std::uintptr_t root=0,context=0,holder=0;
  if(!At(out.window,0,vt)||vt!=image+0x4C5C3B0||!At(out.window,0x10,vt)||vt!=image+0x4C5C390||!At(out.window,0x20,vt)||vt!=image+0x4C5C368||!At(out.window,0x70,root)||!At(out.window,0x78,context)||context!=s.context||!At(out.window,0xA8,holder)||holder!=out.jomini||!At(out.window,0xB0,holder)||holder!=out.manager)return fail("fullscreen_splash_type_owner_context_mismatch");
  if(!At(out.window,0xB8,out.items)||!At(out.window,0xC0,cap)||!At(out.window,0xC4,count)||count<0||count>32||cap<count||(count&&!out.items)||!Copy(out.window+0xB8,out.items_header.data(),16)||!At(out.window,0xD0,out.item))return fail("fullscreen_complete_item_vector_invalid");
  out.source.splash_item_count=count;std::unordered_set<std::uintptr_t>seen,seen_data;bool current=false;
  for(std::int32_t n=0;n<count;++n){std::uintptr_t item=0,back=0,data=0;if(!At(out.items,static_cast<std::size_t>(n)*8,item)||!item||!seen.insert(item).second||!At(item,0,back)||back!=out.window||!At(item,0x10,data)||!data||!seen_data.insert(data).second)return fail("fullscreen_item_lifetime_or_backref_invalid");out.item_pointers.push_back(item);out.item_data_pointers.push_back(data);if(item==out.item){out.data=data;current=true;}}
  if(!count){if(out.item||s.visible)return fail("fullscreen_empty_controller_still_materialized");return Fresh(b,e,s,mono);}
  if(!current||!s.fullscreen||root!=s.fullscreen||!s.visible)return fail("fullscreen_current_item_named_visible_root_unbound");
  if(!At(out.item,0x18,out.selected_index)||out.selected_index!=-1)return fail("fullscreen_item_selection_already_pending");
  auto&source=out.source;std::int32_t id=-1,recipient=-1,actual_id=-1;std::uint8_t selected=0;
  std::uintptr_t capture=0;
  if(!At(out.data,0,id)||id<=0||!At(out.data,0x30,selected)||selected||!At(out.data,0x7C0,out.custom)||out.custom!=out.data+0x788||!At(out.custom,0,vt)||vt!=image+0x4C5C2D0||!At(out.custom,8,capture)||capture!=out.item||!At(out.data,0x780,out.completion)||out.completion!=out.data+0x748||!At(out.completion,0,vt)||vt!=image+0x4C5C330||!At(out.completion,8,capture)||capture!=out.item)return fail("fullscreen_typed_item_custom_callbacks_unbound");
  std::uintptr_t game_data=0;if(!At(out.game,0xA0,game_data)||!game_data||game_data>(std::numeric_limits<std::uintptr_t>::max)()-0x44BC0)return fail("fullscreen_runtime_event_manager_unavailable");
  out.native_read_entered=true;if(!NativeLookup(image,game_data+0x44BC0,id,out.runtime_event)){out.cleanup_known=false;return fail("fullscreen_native_lookup_completion_unknown");}
  if(!out.runtime_event||!At(out.runtime_event,0x1C4,actual_id)||actual_id!=id||!At(out.runtime_event,0x1C0,recipient)||recipient==-1||!At(out.runtime_event,0x1B8,out.definition)||!out.definition)return fail("fullscreen_runtime_instance_definition_identity_mismatch");
  std::uintptr_t pool_data=0;std::int32_t pool_count=0;const auto pool=image+0x6B14820;
  if(!At(out.definition,0x20C,out.template_id)||out.template_id==0xFFFFFFFFU||!At(pool,0x30,pool_data)||!pool_data||!At(pool,0x3C,pool_count)||pool_count<0||(out.template_id&0xFFFFFFU)>=static_cast<std::uint32_t>(pool_count)||!Copy(pool+0x30,out.template_pool_header.data(),16))return fail("fullscreen_loaded_template_pool_unavailable");
  std::string actual_template;if(!Text(pool_data+static_cast<std::size_t>(out.template_id&0xFFFFFFU)*32,256,actual_template)||actual_template!="fullscreen_event")return fail("fullscreen_loaded_template_key_not_exact");
  std::string key,opening,description;if(!Text(out.definition+0x10,256,key)||key.empty()||!Text(out.data+0x208,16384,opening)||!Text(out.data+0x180,16384,description))return fail("fullscreen_actual_key_or_cached_text_unavailable");
std::uintptr_t authored=0;if(!At(out.definition,0x138,authored)||!At(out.definition,0x144,out.authored_option_count)||out.authored_option_count<0||out.authored_option_count>64||(out.authored_option_count&&!authored)||!Copy(out.definition+0x138,out.authored_header.data(),16))return fail("fullscreen_event_loaded_authored_options_invalid");
 for(std::int32_t i=0;i<out.authored_option_count;++i){std::uintptr_t item=0;if(!At(authored,static_cast<std::size_t>(i)*8,item)||!item)return fail("fullscreen_event_loaded_authored_option_identity_invalid");out.authored_option_pointers.push_back(item);}
 for(char c:key)if(!((c>='A'&&c<='Z')||(c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='_'||c=='.'))return fail("fullscreen_event_definition_key_invalid");
 if(!At(out.data,0x10,out.options)||!At(out.data,0x18,cap)||!At(out.data,0x1C,count)||count<0||count>64||cap<count||(count&&!out.options)||!Copy(out.data+0x10,out.options_header.data(),16))return fail("fullscreen_event_actual_options_vector_invalid");
 source.fullscreen_found=true;source.named_root_bound=true;source.window_visible=s.visible;source.window_enabled=s.enabled;source.instance_id=id;source.recipient_character_id=recipient;source.definition_key=std::move(key);source.opening=std::move(opening);source.description=std::move(description);
 std::unordered_set<std::int32_t>indices;for(std::int32_t i=0;i<count;++i){if(!Fresh(b,e,s,mono))return fail("fullscreen_event_deadline_expired_during_option_read");const auto at=out.options+static_cast<std::size_t>(i)*0x1B8;std::uintptr_t item_owner=0;std::uint8_t enabled=0,fallback=0;FullscreenEventOption267V1 row;
  if(!At(at,0x160,item_owner)||item_owner!=out.data||!At(at,0x1B0,row.authored_option_index)||row.authored_option_index<0||row.authored_option_index>=out.authored_option_count||!indices.insert(row.authored_option_index).second||!At(at,0x1B4,enabled)||enabled>1||!At(at,0x1B5,fallback)||fallback>1||!Text(at+0x170,16384,row.text)||!Text(at+0x190,16384,row.disabled_reason))return fail("fullscreen_event_actual_option_owner_key_or_text_invalid");
  if(!NativeCan(image,at,row.native_can_select)){out.cleanup_known=false;return fail("fullscreen_event_native_validity_completion_unknown");}out.option_pointers.push_back(at);source.options.push_back(std::move(row));
 }
 if(source.definition_key==kKnownFullscreenEventDefinition267V1&&out.authored_option_count==1&&source.options.size()==1&&source.options[0].authored_option_index==0){source.options[0].source_bound_option_key=kKnownFullscreenEventOption267V1;source.known_ack_admissible=source.splash_item_count==1&&recipient==e.played_character_id&&s.visible&&s.enabled&&source.options[0].native_can_select&&!source.options[0].text.empty();}
 return Fresh(b,e,s,mono);
}
}
bool VerifyFullscreenEventImage267V1([[maybe_unused]]std::uintptr_t image)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_FULLSCREEN_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_FULLSCREEN_EVENT_V1
 if(!image||image!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)))return false;const auto b=BindReadonlyImage(image,kExecutableSha256);if(!b.exact_image_admitted)return false;
#if defined(XAR_CK3_26785313_OFFLINE_FIXTURE)
 if(b.offline_fixture)return false;
#endif
   if(!VerifyLetterImage267V1(image))return false;
for(const auto&pin:fullscreen_event_pins_v1::spans){std::array<unsigned char,1024>bytes{};for(std::size_t off=0;off<pin.size;off+=bytes.size()){const auto count=(std::min)(bytes.size(),pin.size-off);if(!Copy(image+pin.rva+off,bytes.data(),count)||std::memcmp(bytes.data(),pin.data+off,count))return false;}}
 for(const auto&pin:fullscreen_event_pins_v1::pointers){std::uintptr_t value=0;if(!At(image,pin.slot,value)||value!=image+pin.target)return false;}return true;
#else
 return false;
#endif
}
FullscreenEventBindings267V1 BindFullscreenEventImage267V1([[maybe_unused]]std::uintptr_t image,[[maybe_unused]]std::string_view sha)noexcept{FullscreenEventBindings267V1 b;
#if defined(XAR_CK3_ENABLE_121003_26785313_FULLSCREEN_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_FULLSCREEN_EVENT_V1
 if(sha==kExecutableSha256&&VerifyFullscreenEventImage267V1(image))b={image,true};
#endif
 return b;
}
bool ReadFullscreenEventRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const FullscreenEventBindings267V1&bindings,[[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&e,[[maybe_unused]]const FullscreenEventScene267V1&s,[[maybe_unused]]std::uint64_t mono,FullscreenEventRaw267V1&out,std::string&reason)noexcept{
 out={};reason="current_fullscreen_event_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_FULLSCREEN_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_FULLSCREEN_EVENT_V1
 FullscreenEventRaw267V1 first,second;try{if(!bindings.verified||bindings.image!=b.module_base||!VerifyFullscreenEventImage267V1(bindings.image))return false;
  if(!Sample(b,bindings,e,s,mono,first,reason)){out=std::move(first);return false;}if(!Sample(b,bindings,e,s,mono,second,reason)){out=std::move(second);return false;}
  if(first!=second||!VerifyFullscreenEventImage267V1(bindings.image)){out=std::move(second);reason="fullscreen_event_actual_instance_or_material_changed_between_samples";return false;}out=std::move(second);reason.clear();return true;
 }catch(...){out.native_read_entered=first.native_read_entered||second.native_read_entered;out.cleanup_known=!out.native_read_entered;reason="fullscreen_event_raw_read_exception";return false;}
#else
 return false;
#endif
}
FullscreenEventRawCall267V1 AcknowledgeKnownFullscreenEventRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const FullscreenEventBindings267V1&bindings,[[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&e,[[maybe_unused]]const FullscreenEventScene267V1&s,[[maybe_unused]]std::uint64_t mono,[[maybe_unused]]const FullscreenEventRaw267V1&expected)noexcept{FullscreenEventRawCall267V1 call;
#if defined(XAR_CK3_ENABLE_121003_26785313_FULLSCREEN_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_FULLSCREEN_EVENT_V1
 FullscreenEventRaw267V1 now;std::string reason;if(!ReadFullscreenEventRaw267V1(b,bindings,e,s,mono,now,reason)){call.cleanup_known=now.cleanup_known;if(!call.cleanup_known)call.status=FullscreenEventRawCallStatus267V1::indeterminate;return call;}
 if(now!=expected||!now.source.known_ack_admissible||now.option_pointers.size()!=1||!Fresh(b,e,s,mono))return call;
 call.effect_entered=true;if(!NativeSelect(bindings.image,now.option_pointers[0])){call.status=FullscreenEventRawCallStatus267V1::indeterminate;call.cleanup_known=false;return call;}call.status=FullscreenEventRawCallStatus267V1::returned;
#endif
 return call;
}

RuntimeEventTimeGate267V1 ReadRuntimeEventTimeGate267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&e)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_FULLSCREEN_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_FULLSCREEN_EVENT_V1
 bool entered=false;try{if(!b.exact_image_admitted||!e.clock.paused||!VerifyFullscreenEventImage267V1(b.module_base))return RuntimeEventTimeGate267V1::unavailable;struct View{std::uintptr_t game=0,data=0,rows=0;std::int32_t count=0,capacity=0,actor=-1;std::vector<std::uintptr_t>pointers,definitions;std::vector<std::int32_t>ids,recipients,types;bool operator==(const View&)const=default;};
  const auto sample=[&](View&v){if(!At(b.module_base,kGameStateSlotRva,v.game)||!v.game||!At(v.game,0xA0,v.data)||!v.data||!At(b.module_base,0x5D50448,v.actor)||v.actor!=e.played_character_id||!At(v.data,0x44BC0+0x1F18,v.rows)||!At(v.data,0x44BC0+0x1F20,v.capacity)||!At(v.data,0x44BC0+0x1F24,v.count)||v.count<0||v.count>64||v.capacity<v.count||(v.count&&!v.rows))return false;std::unordered_set<std::uintptr_t>seen;
   for(std::int32_t i=0;i<v.count;++i){std::uintptr_t event=0,def=0;std::int32_t id=0,recipient=-1,type=-1;if(!At(v.rows,static_cast<std::size_t>(i)*8,event)||!event||!seen.insert(event).second||!At(event,0x1B8,def)||!def||!At(event,0x1C0,recipient)||!At(event,0x1C4,id)||id<=0||!At(def,0x208,type))return false;v.pointers.push_back(event);v.definitions.push_back(def);v.ids.push_back(id);v.recipients.push_back(recipient);v.types.push_back(type);}
   return CoreEqualSafe(b,e);};View a,z;if(!sample(a))return RuntimeEventTimeGate267V1::unavailable;bool before=false,after=false;entered=true;if(!NativeTimeGate(b.module_base,a.data+0x44BC0,before)||!NativeTimeGate(b.module_base,a.data+0x44BC0,after))return RuntimeEventTimeGate267V1::indeterminate;if(!sample(z)||a!=z||before!=after)return RuntimeEventTimeGate267V1::unavailable;return after?RuntimeEventTimeGate267V1::blocked:RuntimeEventTimeGate267V1::clear;
 }catch(...){return entered?RuntimeEventTimeGate267V1::indeterminate:RuntimeEventTimeGate267V1::unavailable;}
#else
 return RuntimeEventTimeGate267V1::unavailable;
#endif
}
} // namespace
