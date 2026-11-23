#include "xar_bridge/ck3_121003_rite_creation_blockers26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_rite_creation_blockers26785313_pins_v1.hpp"
#include <chrono>
#include <cstring>
#include <limits>
#include <windows.h>
#ifndef XAR_RITE_BLOCKERS_CALL_ADDRESS
#define XAR_RITE_BLOCKERS_CALL_ADDRESS(image,rva) ((image)+(rva))
#endif
namespace xar::ck3_121003::build26785313 {namespace {
bool Copy(std::uintptr_t p,void*out,std::size_t n)noexcept{if(!p||!out||!n)return false;__try{std::memcpy(out,reinterpret_cast<void*>(p),n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
template<class T>bool At(std::uintptr_t p,std::size_t n,T&v)noexcept{constexpr auto max=(std::numeric_limits<std::uintptr_t>::max)();return p&&n<=max-p&&sizeof(T)-1<=max-p-n&&Copy(p+n,&v,sizeof(v));}
[[maybe_unused]]bool Time(std::uint64_t wall,std::uint64_t mono)noexcept{const auto n=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return n>0&&wall&&mono&&static_cast<std::uint64_t>(n)<wall&&GetTickCount64()<mono;}
[[maybe_unused]]bool SameCore(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool Fresh(const ReadonlyBindings&b,const RiteBlockersFrame267V1&f,std::uint64_t wall,std::uint64_t mono)noexcept{
 if(!b.exact_image_admitted||!f.facts_verified||!Time(wall,mono))return false;
 __try{ck3_1210::CoreSnapshotPrefix c;std::int32_t id=-1;std::uint32_t magic=0;std::uintptr_t death=1;return ck3_1210::ReadCoreSnapshot(b.core,c)&&SameCore(c,f.core)&&reinterpret_cast<std::uintptr_t>(*b.core.game_state_slot)==f.game&&reinterpret_cast<std::uintptr_t>(*b.core.jomini_state_slot)==f.jomini&&reinterpret_cast<std::uintptr_t>(*b.core.character_storage_slot)==f.storage&&reinterpret_cast<std::uintptr_t>(ck3_1210::ResolveCoreCharacter(b.core,c.played_character_id))==f.actor&&At(f.actor,0x18,id)&&id==c.played_character_id&&At(f.actor,0x1C,magic)&&magic==0x43686172&&At(f.actor,0x1D0,death)&&!death&&Time(wall,mono);}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool Controller(const ReadonlyBindings&b,const RiteBlockersFrame267V1&f,const RiteBlockersRequest267V1&q,const RiteDraftV2&d)noexcept{
 const auto image=b.module_base;std::uintptr_t gfx=0,handler=0,controller=0,vt=0,back=0,root=0,app=0,first=0,cx=0;std::uint32_t rite=0xFFFFFFFFU;std::int32_t actor=-1;
 return !d.window.tree.empty()&&d.window.requested_name=="rite_creation_window"&&d.window.tree.front().name=="rite_creation_window"&&d.source_rite_id==q.expected_source_rite_id&&At(f.jomini,0,vt)&&vt==image+0x4B45FE0&&At(f.jomini,0x10,gfx)&&At(gfx,0,vt)&&vt==image+0x4B24748&&At(gfx,0x20,back)&&back==f.jomini&&At(gfx,0x88,handler)&&At(handler,0,vt)&&vt==image+0x4B22578&&At(handler,0x58,vt)&&vt==image+0x4B22558&&At(handler,0x278,controller)&&controller==d.controller&&At(controller,0,vt)&&vt==image+0x4C09438&&At(controller,0x10,vt)&&vt==image+0x4C09410&&At(controller,0x98,back)&&back==f.jomini&&At(controller,0xA0,back)&&back==handler&&At(controller,0x60,root)&&root==d.window.tree.front().widget&&root&&At(controller,0x68,cx)&&cx==d.window.context&&cx&&At(controller,0xC8,rite)&&rite==q.expected_source_rite_id&&At(controller,0xCC,actor)&&actor==f.core.played_character_id&&At(f.jomini,0x18,app)&&At(app,0x1B8,first)&&At(first,0x58,back)&&back==cx;
}
[[maybe_unused]]bool Bool(std::uintptr_t image,std::uintptr_t rva,std::uintptr_t self,bool second,bool&out)noexcept{__try{if(second){using Fn=bool(__fastcall*)(const void*,void*);out=reinterpret_cast<Fn>(XAR_RITE_BLOCKERS_CALL_ADDRESS(image,rva))(reinterpret_cast<void*>(self),nullptr);}else{using Fn=bool(__fastcall*)(const void*);out=reinterpret_cast<Fn>(XAR_RITE_BLOCKERS_CALL_ADDRESS(image,rva))(reinterpret_cast<void*>(self));}return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Getter(std::uintptr_t image,std::uintptr_t controller,void*out)noexcept{using Fn=void*(__fastcall*)(const void*,void*);__try{return reinterpret_cast<Fn>(XAR_RITE_BLOCKERS_CALL_ADDRESS(image,0x16BA4C0))(reinterpret_cast<void*>(controller),out)==out;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Cleanup(std::uintptr_t image,void*object)noexcept{using Fn=void(__fastcall*)(void*);__try{reinterpret_cast<Fn>(XAR_RITE_BLOCKERS_CALL_ADDRESS(image,0x897460))(object);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Utf8(std::string_view s)noexcept{for(std::size_t i=0;i<s.size();){const auto c=static_cast<unsigned char>(s[i++]);unsigned n=0;std::uint32_t cp=0;if(c<128)cp=c;else if(c>=0xC2&&c<=0xDF){cp=c&31;n=1;}else if(c>=0xE0&&c<=0xEF){cp=c&15;n=2;}else if(c>=0xF0&&c<=0xF4){cp=c&7;n=3;}else return false;if(i+n>s.size())return false;for(unsigned j=0;j<n;++j){const auto v=static_cast<unsigned char>(s[i++]);if((v&0xC0)!=0x80)return false;cp=(cp<<6)|(v&63);}if((n==1&&cp<128)||(n==2&&cp<0x800)||(n==3&&cp<0x10000)||cp>0x10FFFF||(cp>=0xD800&&cp<=0xDFFF))return false;}return true;}
[[maybe_unused]]bool Value(const std::array<std::byte,32>&header,std::string&out){std::uint64_t length=0,cap=0;std::uintptr_t data=reinterpret_cast<std::uintptr_t>(header.data());std::memcpy(&length,header.data()+16,8);std::memcpy(&cap,header.data()+24,8);if(length>16384||cap<length||(cap<=15&&length>15))return false;if(cap>15)std::memcpy(&data,header.data(),8);if(!data)return false;std::array<char,16385>bytes{};if(!Copy(data,bytes.data(),static_cast<std::size_t>(length)+1)||bytes[static_cast<std::size_t>(length)]!=0)return false;out.assign(bytes.data(),static_cast<std::size_t>(length));return Utf8(out);}
[[maybe_unused]]bool Sample(const ReadonlyBindings&b,const RiteBlockersFrame267V1&f,const RiteBlockersRequest267V1&q,std::uint64_t mono,RiteBlockersRaw267V1&out,std::string&why){
 if(!f.draft||!Controller(b,f,q,*f.draft)||!Fresh(b,f,q.deadline_unix_ms,mono)){why="rite_creation_blockers_actual_controller_actor_source_unavailable";return false;}out.draft=*f.draft;out.controller=out.draft.controller;out.context=out.draft.window.context;out.root=out.draft.window.tree.front().widget;out.source.source_rite_id=q.expected_source_rite_id;out.source.actor_id=f.core.played_character_id;out.source.window_visible=out.draft.window.tree.front().visible;out.source.window_enabled=out.draft.window.tree.front().enabled;out.entered=true;
 if(!Bool(b.module_base,0x16B9260,out.controller,false,out.source.is_creating)){out.cleanup_known=false;why="rite_creation_blockers_actual_native_predicate_unknown";return false;}if(!Time(q.deadline_unix_ms,mono)){why="rite_creation_blockers_original_deadline_expired_after_predicate";return false;}
 if(!Bool(b.module_base,0x16BA410,out.controller,true,out.source.native_can_create)){out.cleanup_known=false;why="rite_creation_blockers_actual_native_predicate_unknown";return false;}if(!Time(q.deadline_unix_ms,mono)){why="rite_creation_blockers_original_deadline_expired_after_predicate";return false;}
 // Official GetCreationBlockers initializes this owned CString32, then calls
 // the same CanCreateRite with it as the blocker accumulator. Never retain a
 // returned pointer or mistake a native read return for a mutation result.
 alignas(8)std::array<std::byte,32>owned{};const std::uint64_t cap=15;std::memcpy(owned.data()+24,&cap,8);
 const bool returned=Getter(b.module_base,out.controller,owned.data());bool copied=false;try{if(returned)copied=Value(owned,out.source.blockers_text);}catch(...){copied=false;}
 const bool cleaned=Cleanup(b.module_base,owned.data());out.cleanup_known=returned&&cleaned;
 if(!out.cleanup_known){why="rite_creation_blockers_actual_owned_string_cleanup_unknown";return false;}if(!copied){why="rite_creation_blockers_actual_string_length_utf8_or_storage_unavailable";return false;}
 out.draft.window.ticket_sequence=0;out.draft.window.pump_epoch=0;return Controller(b,f,q,*f.draft)&&Fresh(b,f,q.deadline_unix_ms,mono);
}
}
bool VerifyRiteBlockersImage267V1([[maybe_unused]]std::uintptr_t image)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_CREATION_BLOCKERS_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_CREATION_BLOCKERS_V1
 if(!image||image!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))||!VerifyReadonlyImage(image)||!VerifyRiteCreateImage267V1(image))return false;std::array<std::byte,4096>bytes{};for(const auto&p:rite_creation_blockers_pins::kPins)if(p.bytes.empty()||p.bytes.size()>bytes.size()||p.rva>kImageSize-p.bytes.size()||!Copy(image+p.rva,bytes.data(),p.bytes.size())||std::memcmp(bytes.data(),p.bytes.data(),p.bytes.size()))return false;return true;
#else
 return false;
#endif
}
bool ReadRiteBlockersRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const RiteBlockersFrame267V1&f,[[maybe_unused]]const RiteBlockersRequest267V1&q,[[maybe_unused]]std::uint64_t mono,RiteBlockersRaw267V1&out,std::string&why)noexcept{
 out={};why="rite_creation_blockers_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_CREATION_BLOCKERS_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_CREATION_BLOCKERS_V1
 if(!VerifyRiteBlockersImage267V1(b.module_base)||!Fresh(b,f,q.deadline_unix_ms,mono))return false;
 try{RiteBlockersRaw267V1 samples[2];for(auto&s:samples){const bool good=Sample(b,f,q,mono,s,why);out=s;if(!good||!s.cleanup_known)return false;}if(samples[0]!=samples[1]){why="rite_creation_blockers_actual_source_changed_between_samples";return false;}out=std::move(samples[1]);out.source.sampled_twice=true;why.clear();return true;}catch(...){why="rite_creation_blockers_actual_copy_exception";return false;}
#endif
 return false;
}
}
