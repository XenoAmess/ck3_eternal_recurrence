// Included only by the new finite LYD Raw TU. No arbitrary key/Any/receiver input comes from wire.
namespace lyd_personal_native {
struct Any{std::uintptr_t type=0;std::array<std::byte,32>storage{};};
static_assert(sizeof(Any)==40);
struct ArgTable{Any*data=nullptr;};
struct ArgCursor{ArgTable*table=nullptr;std::uint32_t index=0,reserved=0;};
using Factory=std::uintptr_t(__fastcall*)();
[[maybe_unused]]bool Destroy(Any&value,std::uintptr_t empty,std::uintptr_t character,std::uintptr_t text)noexcept{
 __try{
  if(value.type!=empty&&value.type!=character&&value.type!=text)return false;
  const auto vt=*reinterpret_cast<const std::uintptr_t*>(value.type);const auto fn=*reinterpret_cast<const std::uintptr_t*>(vt+0x18);
  reinterpret_cast<void(__fastcall*)(void*,void*)>(fn)(reinterpret_cast<void*>(value.type),value.storage.data());
  value={};value.type=empty;return true;
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool CharacterMatches(void*actual,std::int32_t id)noexcept{
 if(!actual||id==-1)return false;
 __try{const auto p=static_cast<const std::byte*>(actual);std::int32_t found=-1;std::uint32_t magic=0;std::memcpy(&found,p+0x18,4);std::memcpy(&magic,p+0x1C,4);return found==id&&magic==0x43686172;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]LydRawCall267V1 Open(const ReadonlyBindings&bindings,const ck3_1210::CoreSnapshotPrefix&core,const LydScene267V1&scene,std::uint64_t mono,void*actual)noexcept{
 const auto image=bindings.module_base;const auto actor=core.played_character_id;
 LydRawCall267V1 out;if(!CharacterMatches(actual,actor)||!lyd_common::Fresh(bindings,core,scene,mono))return out;
 std::array<Any,2>args{};alignas(void*)std::array<std::byte,32>key{};
 const std::uint64_t cap=15;std::memcpy(key.data()+24,&cap,8);
 std::uintptr_t empty=0,character=0,text=0;bool initialized=false,key_entered=false,key_complete=false,any_copy_entered=false,any_copy_complete=false,player_entered=false,player_complete=false;
 __try{
  empty=reinterpret_cast<Factory>(image+0x8B2EF0)();character=reinterpret_cast<Factory>(image+0xA3F530)();text=reinterpret_cast<Factory>(image+0x8C21D0)();
  if(!empty||character!=image+lyd_personal_pins::kCharacterAnyInstanceRva||text!=image+lyd_personal_pins::kStringAnyInstanceRva)return out;
  args[0].type=args[1].type=empty;initialized=true;
  using AssignText=void*(__fastcall*)(void*,const char*,std::size_t);
  constexpr char view[]="personal_beliefs_window";key_entered=true;
  reinterpret_cast<AssignText>(image+0x896BB0)(key.data(),view,sizeof(view)-1);key_complete=true;
  // Exact8B4960 ABI: destination Any RCX, source STORAGE RDX, actual type R8.
  using CopyAny=void(__fastcall*)(Any*,const void*,void*);any_copy_entered=true;
  reinterpret_cast<CopyAny>(image+0x8B4960)(&args[0],key.data(),reinterpret_cast<void*>(text));any_copy_complete=true;
  if(args[0].type==text){
  // Actual GetPlayer callback produces the complete current Character Any. Its bool also covers fallback; pointer/full-ID/magic checks are independent.
  using GetPlayer=bool(__fastcall*)(void*,Any*);player_entered=true;
  const auto handled=reinterpret_cast<GetPlayer>(image+0x2B48940)(nullptr,&args[1]);player_complete=true;
  std::uintptr_t payload=0;std::memcpy(&payload,args[1].storage.data(),8);
  if(handled&&args[1].type==character&&payload==reinterpret_cast<std::uintptr_t>(actual)&&CharacterMatches(actual,actor)&&lyd_common::Fresh(bindings,core,scene,mono)){
   ArgTable table{args.data()};ArgCursor cursor{&table,0,0};
   using ToggleData=bool(__fastcall*)(void*,void*,const ArgCursor*);
   out.effect_entered=true;out.status=LydRawCallStatus267V1::indeterminate;out.cleanup_known=false;
   out.native_handled=reinterpret_cast<ToggleData>(image+0xBC1460)(nullptr,nullptr,&cursor);
   out.status=LydRawCallStatus267V1::returned;out.cleanup_known=true;
  }
  }else out.cleanup_known=false;
 }__except(EXCEPTION_EXECUTE_HANDLER){out.cleanup_known=false;if(out.effect_entered)out.status=LydRawCallStatus267V1::indeterminate;}
 if(key_complete){__try{reinterpret_cast<void(__fastcall*)(void*)>(image+0x897460)(key.data());}__except(EXCEPTION_EXECUTE_HANDLER){out.cleanup_known=false;}}
 else if(key_entered)out.cleanup_known=false;
 if(initialized){
  if(!any_copy_entered||any_copy_complete){if(!Destroy(args[0],empty,character,text))out.cleanup_known=false;}else out.cleanup_known=false;
  if(!player_entered||player_complete){if(!Destroy(args[1],empty,character,text))out.cleanup_known=false;}else out.cleanup_known=false;
 }
 if(!out.cleanup_known)out.status=LydRawCallStatus267V1::indeterminate;
 return out;
}
[[maybe_unused]]bool CanPick(std::uintptr_t image,std::int32_t actor,std::uintptr_t tenet,bool&value)noexcept{
 __try{using Fn=bool(__fastcall*)(std::int32_t,const void*,void*);value=reinterpret_cast<Fn>(image+0x317FA90)(actor,reinterpret_cast<const void*>(tenet),nullptr);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool CanAccept(std::uintptr_t image,std::uintptr_t modal,bool&value)noexcept{
 __try{using Fn=bool(__fastcall*)(const void*);value=reinterpret_cast<Fn>(image+0x1A4AC10)(reinterpret_cast<const void*>(modal));return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]LydRawCall267V1 Call(std::uintptr_t image,std::uintptr_t resident,std::uintptr_t definition,std::uintptr_t modal,LydAction267V1 action)noexcept{
 LydRawCall267V1 out;
 if(action!=LydAction267V1::start_add_personal&&action!=LydAction267V1::select_personal_candidate&&action!=LydAction267V1::confirm_personal_add)return out;
 if((action!=LydAction267V1::confirm_personal_add&&!resident)||(action==LydAction267V1::select_personal_candidate&&!definition)||(action==LydAction267V1::confirm_personal_add&&!modal))return out;
 out.effect_entered=true;out.cleanup_known=false;out.status=LydRawCallStatus267V1::indeterminate;
 __try{
  if(action==LydAction267V1::start_add_personal){using Fn=void(__fastcall*)(void*);reinterpret_cast<Fn>(image+0x1A4CDF0)(reinterpret_cast<void*>(resident));}
  else if(action==LydAction267V1::select_personal_candidate){using Fn=void(__fastcall*)(void*,const void*);reinterpret_cast<Fn>(image+0x1A4CFD0)(reinterpret_cast<void*>(resident),reinterpret_cast<const void*>(definition));}
  else{using Fn=void(__fastcall*)(void*);reinterpret_cast<Fn>(image+0xCF3200)(reinterpret_cast<void*>(modal));}
  out.status=LydRawCallStatus267V1::returned;out.cleanup_known=true;
 }__except(EXCEPTION_EXECUTE_HANDLER){}
 return out;
}
} // namespace lyd_personal_native
