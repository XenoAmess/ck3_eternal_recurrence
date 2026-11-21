#include "xar_bridge/ck3_121003_succession_continue26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_succession_continue26785313_abi_v1.hpp"
#include "xar_bridge/ck3_121003_succession_continue26785313_pins_v1.hpp"
#include <array>
#include <cstring>
#include <limits>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
namespace abi=xar::current267_succession_source_v1;
[[maybe_unused]]bool Copy(std::uintptr_t p,void*out,std::size_t n)noexcept{if(!p||!out||!n||n-1>(std::numeric_limits<std::uintptr_t>::max)()-p)return false;__try{std::memcpy(out,reinterpret_cast<const void*>(p),n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
template<class T>bool At(std::uintptr_t p,std::size_t off,T&v)noexcept{return off<=(std::numeric_limits<std::uintptr_t>::max)()-p&&Copy(p+off,&v,sizeof(v));}
[[maybe_unused]]bool Get(std::uintptr_t base,std::uintptr_t fn,std::uintptr_t controller,std::uintptr_t&out)noexcept{__try{out=reinterpret_cast<std::uintptr_t>(reinterpret_cast<abi::CharacterGetter>(base+fn)(reinterpret_cast<const void*>(controller)));return out!=0;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Open(std::uintptr_t base,std::uintptr_t controller,bool&out)noexcept{__try{out=reinterpret_cast<abi::ControllerPredicate>(base+abi::kIsOpen)(reinterpret_cast<void*>(controller));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Paused(std::uintptr_t base,bool&out)noexcept{__try{out=reinterpret_cast<abi::PausedPredicate>(base+abi::kIsPausedBySuccession)();return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Character(const ReadonlyBindings&b,std::uintptr_t p,bool dead,std::int32_t&id)noexcept{std::uint32_t type=0;std::uintptr_t death=0;if(!At(p,0x18,id)||id==-1||!At(p,0x1C,type)||type!=0x43686172U||!At(p,0x1D0,death)||(death!=0)!=dead)return false;__try{return ck3_1210::ResolveCoreCharacter(b.core,id)==reinterpret_cast<void*>(p);}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Capture(const ReadonlyBindings&core,const SuccessionRawBindings267V1&b,const SuccessionExpectedWindow267V1&e,SuccessionRawSample267V1&out){
 const auto base=b.image;SuccessionRawSample267V1 v;std::uintptr_t p=0,vt=0,heir=0,excluded=0;
 if(!At(e.jomini,0,vt)||vt!=base+0x4B45FE0||!At(e.jomini,0x10,p)||p!=e.gfx||!At(e.gfx,0,vt)||vt!=base+0x4B24748||!At(e.gfx,0x20,p)||p!=e.jomini||!At(e.gfx,0x88,p)||p!=e.handler||!At(e.handler,0,vt)||vt!=base+0x4B22578||!At(e.handler,0x58,vt)||vt!=base+0x4B22558)return false;
 if(!At(e.handler,abi::kHandlerController,v.controller)||!v.controller||!At(e.handler,abi::kExcludedLineageController,excluded)||excluded==v.controller||!At(v.controller,0,vt)||vt!=base+abi::kPrimaryVtable||!At(v.controller,0x10,vt)||vt!=base+abi::kSecondaryVtable)return false;
 if(!At(v.controller,abi::kRoot,v.root)||v.root!=e.root||!At(v.controller,abi::kGuiContext,v.context)||v.context!=e.gui_context||!At(v.controller,abi::kHandler,v.handler)||v.handler!=e.handler||!At(v.controller,abi::kJomini,v.jomini)||v.jomini!=e.jomini||!At(v.controller,abi::kSuccessionKind,v.kind)||v.kind!=0||!At(v.controller,abi::kAlternateMode,v.alternate_mode)||v.alternate_mode!=0||!At(v.controller,abi::kAlternateContinueId,v.alternate_id))return false;
 if(!Open(base,v.controller,v.native_open)||!v.native_open||!Paused(base,v.native_paused_by_succession)||!v.native_paused_by_succession||!Get(base,abi::kGetDeadCharacter,v.controller,v.dead_character)||!Get(base,abi::kGetPlayerHeir,v.controller,heir)||!Get(base,abi::kGetContinueAsCharacter,v.controller,v.continue_character)||heir!=v.continue_character||!Character(core,v.dead_character,true,v.dead_character_id)||!Character(core,v.continue_character,false,v.continue_character_id)||v.dead_character_id==v.continue_character_id)return false;
 std::int32_t id=-1;if(!At(v.controller,abi::kDeadCharacterId,id)||id!=v.dead_character_id||!At(v.controller,abi::kPlayerHeirId,id)||id!=v.continue_character_id)return false;
 if(!At(base,abi::kGameStateSlot,v.game_state)||!At(v.game_state,abi::kGameData,v.game_data)||!At(base,abi::kPlayerIdSlot,v.player_id)||!At(base,abi::kOpaqueCloseTokenSlot,v.opaque_token)||!At(v.game_data,abi::kPlayerRows,v.player_rows)||!At(v.game_data,abi::kPlayerRows+8,v.row_capacity)||!At(v.game_data,abi::kPlayerRowCount,v.row_count)||v.row_capacity<0||v.row_count<0||v.row_count>v.row_capacity||v.row_count>1024||(v.row_count&&!v.player_rows))return false;
 for(std::int32_t i=0;i<v.row_count;++i){std::uintptr_t row=0;std::int32_t key=-1,token=-1;std::uint8_t active=0;if(!At(v.player_rows,static_cast<std::size_t>(i)*8,row)||!row||!At(row,abi::kRowCharacterId,key)||!At(row,abi::kRowOpaqueToken,token)||!At(row,abi::kRowActive,active))return false;
  // Row key is compared with the same native global argument; no CharacterID domain is inferred here.
  if(key==v.player_id&&token==v.opaque_token&&active){if(v.active_player_row)return false;v.active_player_row=row;v.row_active=active;}}
 if(!v.active_player_row)return false;out=v;return true;
}
[[maybe_unused]]bool NativeClose(std::uintptr_t base,std::uintptr_t controller)noexcept{__try{reinterpret_cast<abi::ControllerClose>(base+abi::kClose)(reinterpret_cast<void*>(controller));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
}
bool VerifySuccessionContinueImage267V1([[maybe_unused]]std::uintptr_t base)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_SUCCESSION_CONTINUE_V1) && XAR_CK3_ENABLE_121003_26785313_SUCCESSION_CONTINUE_V1
 if(base!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))||!VerifyReadonlyImage(base)||!VerifyGuiWindowImageV1(base))return false;
 std::array<unsigned char,succession_source_pins::kMaxBytes>bytes{};for(const auto&p:succession_source_pins::kPins)if(p.bytes.empty()||p.rva>kImageSize-p.bytes.size()||!Copy(base+p.rva,bytes.data(),p.bytes.size())||std::memcmp(bytes.data(),p.bytes.data(),p.bytes.size()))return false;
 for(const auto&p:succession_source_pins::kPointers){std::uintptr_t value=0;if(!At(base,p.slot,value)||value!=base+p.target)return false;}return true;
#else
 return false;
#endif
}
SuccessionRawBindings267V1 BindSuccessionContinueImage267V1([[maybe_unused]]std::uintptr_t base,[[maybe_unused]]std::string_view sha)noexcept{SuccessionRawBindings267V1 b;
#if defined(XAR_CK3_ENABLE_121003_26785313_SUCCESSION_CONTINUE_V1) && XAR_CK3_ENABLE_121003_26785313_SUCCESSION_CONTINUE_V1
 if(BindReadonlyImage(base,sha).exact_image_admitted&&VerifySuccessionContinueImage267V1(base)){b.image=base;b.verified=true;}
#endif
 return b;}
bool ReadSuccessionContinueRaw267V1([[maybe_unused]]const ReadonlyBindings&core,[[maybe_unused]]const SuccessionRawBindings267V1&b,[[maybe_unused]]const SuccessionExpectedWindow267V1&e,SuccessionRawSample267V1&out,std::string&reason)noexcept{out={};reason="current_succession_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_SUCCESSION_CONTINUE_V1) && XAR_CK3_ENABLE_121003_26785313_SUCCESSION_CONTINUE_V1
 try{if(!b.verified||core.module_base!=b.image||!core.exact_image_admitted||!core.core.enabled||!e.root||!e.gui_context||!e.handler||!VerifySuccessionContinueImage267V1(b.image)){reason="current_succession_image_or_context_unavailable";return false;}SuccessionRawSample267V1 a,z;
  if(!Capture(core,b,e,a)||!Capture(core,b,e,z)||a!=z||!VerifySuccessionContinueImage267V1(b.image)){reason="current_succession_typed_default_or_material_source_unavailable";return false;}out=a;reason.clear();return true;
 }catch(...){reason="current_succession_source_exception";}
#endif
 return false;}
SuccessionRawCall267V1 CallSuccessionContinueRaw267V1([[maybe_unused]]const ReadonlyBindings&core,[[maybe_unused]]const SuccessionRawBindings267V1&b,[[maybe_unused]]const SuccessionExpectedWindow267V1&e,[[maybe_unused]]const SuccessionRawSample267V1&expected)noexcept{SuccessionRawCall267V1 r;
#if defined(XAR_CK3_ENABLE_121003_26785313_SUCCESSION_CONTINUE_V1) && XAR_CK3_ENABLE_121003_26785313_SUCCESSION_CONTINUE_V1
 try{SuccessionRawSample267V1 fresh;std::string reason;if(!ReadSuccessionContinueRaw267V1(core,b,e,fresh,reason)||fresh!=expected)return r;r.effect_entered=true;
  r.status=NativeClose(b.image,fresh.controller)&&VerifySuccessionContinueImage267V1(b.image)?SuccessionRawCallStatus267V1::returned:SuccessionRawCallStatus267V1::indeterminate;
 }catch(...){if(r.effect_entered)r.status=SuccessionRawCallStatus267V1::indeterminate;}
#endif
 return r;}
}
