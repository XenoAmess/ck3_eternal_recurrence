#include "xar_bridge/ck3_121003_letter26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_letter26785313_pins_v1.hpp"
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
[[maybe_unused]]bool Fresh(const ReadonlyBindings&b,const ck3_1210::CoreSnapshotPrefix&e,const LetterScene267V1&s,std::uint64_t mono)noexcept{
 const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();if(!mono||GetTickCount64()>=mono||!s.wall_deadline||t<=0||static_cast<std::uint64_t>(t)>=s.wall_deadline||!e.clock.paused||!e.map_ready||!e.has_played_character||!e.played_character_alive||e.played_character_id==-1)return false;
 __try{ck3_1210::CoreSnapshotPrefix p;return ck3_1210::ReadCoreSnapshot(b.core,p)&&Equal(p,e);}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool Text(std::uintptr_t at,std::size_t limit,std::string&out){
 std::uint64_t n=0,cap=0;std::uintptr_t chars=at;if(!At(at,16,n)||!At(at,24,cap)||n>limit||n>cap||cap<15||cap>0x1000000)return false;if(cap==15){if(n>15)return false;}else if(!At(at,0,chars)||!chars)return false;
 std::vector<char>bytes(static_cast<std::size_t>(n)+1);if(!Copy(chars,bytes.data(),bytes.size())||bytes[static_cast<std::size_t>(n)]||std::memchr(bytes.data(),0,static_cast<std::size_t>(n))||(n&&MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,bytes.data(),static_cast<int>(n),nullptr,0)==0))return false;out.assign(bytes.data(),static_cast<std::size_t>(n));return true;
}
[[maybe_unused]]bool NativeLookup(std::uintptr_t image,std::uintptr_t manager,std::int32_t id,std::uintptr_t&out)noexcept{__try{out=reinterpret_cast<std::uintptr_t>(reinterpret_cast<void*(__fastcall*)(void*,std::int32_t)>(image+0x2EBEDB0)(reinterpret_cast<void*>(manager),id));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool NativeCan(std::uintptr_t image,std::uintptr_t option,bool&out)noexcept{__try{out=reinterpret_cast<bool(__fastcall*)(const void*)>(image+0x1B6CC30)(reinterpret_cast<const void*>(option));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool NativeSelect(std::uintptr_t image,std::uintptr_t option)noexcept{__try{reinterpret_cast<void(__fastcall*)(void*)>(image+0x1B6CA10)(reinterpret_cast<void*>(option));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Sample(const ReadonlyBindings&b,const LetterBindings267V1&bindings,const ck3_1210::CoreSnapshotPrefix&e,const LetterScene267V1&s,std::uint64_t mono,LetterRaw267V1&out,std::string&reason){
 const auto fail=[&](const char*why){reason=why;return false;};if(!Fresh(b,e,s,mono))return fail("letter_original_core_or_deadline_changed");const auto image=bindings.image;std::uintptr_t gfx=0,vt=0,owner=0;std::int32_t cap=0,count=0;
 if(!At(image,kGameStateSlotRva,out.game)||!out.game||!At(image,kJominiStateSlotRva,out.jomini)||out.jomini!=s.jomini||!At(out.jomini,0x10,gfx)||gfx!=s.gfx||!At(gfx,0,vt)||vt!=image+0x4B24748||!At(gfx,0x28,out.manager)||!out.manager||!At(out.manager,0,owner)||owner!=out.jomini)return fail("letter_actual_typed_manager_source_unavailable");
 if(!At(out.manager,0x18,out.windows)||!At(out.manager,0x20,cap)||!At(out.manager,0x24,count)||count<0||count>32||cap<count||(count&&!out.windows)||!Copy(out.manager+0x18,out.windows_header.data(),16))return fail("letter_resident_manager_vector_invalid");out.source.resident_count=count;
 std::unordered_set<std::uintptr_t>seen;std::size_t matches=0;
 for(std::int32_t i=0;i<count;++i){std::uintptr_t window=0,root=0,context=0;if(!At(out.windows,static_cast<std::size_t>(i)*8,window)||!window||!seen.insert(window).second||!At(window,0,vt))return fail("letter_resident_window_identity_invalid");out.window_pointers.push_back(window);
  if(vt!=image+0x4C5D448)continue;
  // These actual CEventWindow root/context offsets are independently pinned from
  // its current base constructor; they are not inherited from a Rite object.
  if(!At(window,0x70,root)||!At(window,0x78,context))return fail("letter_resident_widget_source_unreadable");
  if(s.letter&&root==s.letter){if(context!=s.context)return fail("letter_resident_widget_context_mismatch");out.window=window;++matches;}
 }
 if(matches>1)return fail("letter_materialized_window_ambiguous");
 if(!s.letter||!s.visible){if(matches&&s.visible)return fail("letter_named_root_mismatch");return Fresh(b,e,s,mono);}
 if(matches!=1)return fail("letter_named_visible_widget_not_bound_to_exact_controller");
 auto&source=out.source;out.data=out.window+0xB8;std::int32_t id=-1,recipient=-1,actual_id=-1;std::uint8_t selected=0;std::uintptr_t custom=0;
 if(!At(out.data,0,id)||id<=0||!At(out.data,0x30,selected)||selected||!At(out.data,0x7C0,custom)||custom)return fail("letter_instance_closed_or_custom_selection_unsupported");
 std::uintptr_t game_data=0;if(!At(out.game,0xA0,game_data)||!game_data||game_data>(std::numeric_limits<std::uintptr_t>::max)()-0x44BC0)return fail("letter_runtime_event_manager_unavailable");
 out.native_read_entered=true;if(!NativeLookup(image,game_data+0x44BC0,id,out.runtime_event)){out.cleanup_known=false;return fail("letter_native_lookup_completion_unknown");}
 if(!out.runtime_event||!At(out.runtime_event,0x1C4,actual_id)||actual_id!=id||!At(out.runtime_event,0x1C0,recipient)||recipient==-1||!At(out.runtime_event,0x1B8,out.definition)||!out.definition)return fail("letter_runtime_instance_definition_identity_mismatch");
 std::string key,opening,description;if(!Text(out.definition+0x10,256,key)||key.empty()||!Text(out.data+0x208,16384,opening)||!Text(out.data+0x180,16384,description))return fail("letter_actual_key_or_cached_text_unavailable");
 std::uintptr_t authored=0;if(!At(out.definition,0x138,authored)||!At(out.definition,0x144,out.authored_option_count)||out.authored_option_count<0||out.authored_option_count>64||(out.authored_option_count&&!authored)||!Copy(out.definition+0x138,out.authored_header.data(),16))return fail("letter_loaded_authored_options_invalid");
 for(std::int32_t i=0;i<out.authored_option_count;++i){std::uintptr_t item=0;if(!At(authored,static_cast<std::size_t>(i)*8,item)||!item)return fail("letter_loaded_authored_option_identity_invalid");out.authored_option_pointers.push_back(item);}
 for(char c:key)if(!((c>='A'&&c<='Z')||(c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='_'||c=='.'))return fail("letter_definition_key_invalid");
 if(!At(out.data,0x10,out.options)||!At(out.data,0x18,cap)||!At(out.data,0x1C,count)||count<0||count>64||cap<count||(count&&!out.options)||!Copy(out.data+0x10,out.options_header.data(),16))return fail("letter_actual_options_vector_invalid");
 source.letter_found=true;source.named_root_bound=true;source.window_visible=s.visible;source.window_enabled=s.enabled;source.instance_id=id;source.recipient_character_id=recipient;source.definition_key=std::move(key);source.opening=std::move(opening);source.description=std::move(description);
 std::unordered_set<std::int32_t>indices;for(std::int32_t i=0;i<count;++i){if(!Fresh(b,e,s,mono))return fail("letter_deadline_expired_during_option_read");const auto at=out.options+static_cast<std::size_t>(i)*0x1B8;std::uintptr_t item_owner=0;std::uint8_t enabled=0,fallback=0;LetterOption267V1 row;
  if(!At(at,0x160,item_owner)||item_owner!=out.data||!At(at,0x1B0,row.authored_option_index)||row.authored_option_index<0||row.authored_option_index>=out.authored_option_count||!indices.insert(row.authored_option_index).second||!At(at,0x1B4,enabled)||enabled>1||!At(at,0x1B5,fallback)||fallback>1||!Text(at+0x170,16384,row.text)||!Text(at+0x190,16384,row.disabled_reason))return fail("letter_actual_option_owner_key_or_text_invalid");
  if(!NativeCan(image,at,row.native_can_select)){out.cleanup_known=false;return fail("letter_native_validity_completion_unknown");}out.option_pointers.push_back(at);source.options.push_back(std::move(row));
 }
 if(source.definition_key==kKnownLetterDefinition267V1&&out.authored_option_count==1&&source.options.size()==1&&source.options[0].authored_option_index==0){source.options[0].source_bound_option_key=kKnownLetterOption267V1;source.known_reply_admissible=recipient==e.played_character_id&&s.visible&&s.enabled&&source.options[0].native_can_select&&!source.options[0].text.empty();}
 return Fresh(b,e,s,mono);
}
}
bool VerifyLetterImage267V1([[maybe_unused]]std::uintptr_t image)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_LETTER_V1) && XAR_CK3_ENABLE_121003_26785313_LETTER_V1
 if(!image||image!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)))return false;const auto b=BindReadonlyImage(image,kExecutableSha256);if(!b.exact_image_admitted)return false;
#if defined(XAR_CK3_26785313_OFFLINE_FIXTURE)
 if(b.offline_fixture)return false;
#endif
 for(const auto&pin:letter_pins_v1::spans){std::array<unsigned char,1024>bytes{};for(std::size_t off=0;off<pin.size;off+=bytes.size()){const auto count=(std::min)(bytes.size(),pin.size-off);if(!Copy(image+pin.rva+off,bytes.data(),count)||std::memcmp(bytes.data(),pin.data+off,count))return false;}}
 for(const auto&pin:letter_pins_v1::pointers){std::uintptr_t value=0;if(!At(image,pin.slot,value)||value!=image+pin.target)return false;}return true;
#else
 return false;
#endif
}
LetterBindings267V1 BindLetterImage267V1([[maybe_unused]]std::uintptr_t image,[[maybe_unused]]std::string_view sha)noexcept{LetterBindings267V1 b;
#if defined(XAR_CK3_ENABLE_121003_26785313_LETTER_V1) && XAR_CK3_ENABLE_121003_26785313_LETTER_V1
 if(sha==kExecutableSha256&&VerifyLetterImage267V1(image))b={image,true};
#endif
 return b;
}
bool ReadLetterRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const LetterBindings267V1&bindings,[[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&e,[[maybe_unused]]const LetterScene267V1&s,[[maybe_unused]]std::uint64_t mono,LetterRaw267V1&out,std::string&reason)noexcept{
 out={};reason="current_letter_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_LETTER_V1) && XAR_CK3_ENABLE_121003_26785313_LETTER_V1
 LetterRaw267V1 first,second;try{if(!bindings.verified||bindings.image!=b.module_base||!VerifyLetterImage267V1(bindings.image))return false;
  if(!Sample(b,bindings,e,s,mono,first,reason)){out=std::move(first);return false;}if(!Sample(b,bindings,e,s,mono,second,reason)){out=std::move(second);return false;}
  if(first!=second||!VerifyLetterImage267V1(bindings.image)){out=std::move(second);reason="letter_actual_instance_or_material_changed_between_samples";return false;}out=std::move(second);reason.clear();return true;
 }catch(...){out.native_read_entered=first.native_read_entered||second.native_read_entered;out.cleanup_known=!out.native_read_entered;reason="letter_raw_read_exception";return false;}
#else
 return false;
#endif
}
LetterRawCall267V1 ReplyKnownLetterRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const LetterBindings267V1&bindings,[[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&e,[[maybe_unused]]const LetterScene267V1&s,[[maybe_unused]]std::uint64_t mono,[[maybe_unused]]const LetterRaw267V1&expected)noexcept{LetterRawCall267V1 call;
#if defined(XAR_CK3_ENABLE_121003_26785313_LETTER_V1) && XAR_CK3_ENABLE_121003_26785313_LETTER_V1
 LetterRaw267V1 now;std::string reason;if(!ReadLetterRaw267V1(b,bindings,e,s,mono,now,reason)){call.cleanup_known=now.cleanup_known;if(!call.cleanup_known)call.status=LetterRawCallStatus267V1::indeterminate;return call;}
 if(now!=expected||!now.source.known_reply_admissible||now.option_pointers.size()!=1||!Fresh(b,e,s,mono))return call;
 call.effect_entered=true;if(!NativeSelect(bindings.image,now.option_pointers[0])){call.status=LetterRawCallStatus267V1::indeterminate;call.cleanup_known=false;return call;}call.status=LetterRawCallStatus267V1::returned;
#endif
 return call;
}
} // namespace
