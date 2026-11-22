// SOURCE_ONLY NoGame native-call simulation; no CK3/ABI/live qualification.
// The included actual candidate is not copied or modified. Its existing
// CALL_ADDRESS seam maps only fixed reviewed addresses to explicit fake thunks.
#include <array>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string_view>
#include <windows.h>
#include "xar_bridge/ck3_121003_des_init_guard26785313_v1.hpp"
using xar::ck3_121003::build26785313::kDesInitGuardKey267V1;
namespace {
ULONGLONG mock_tick=10;
ULONGLONG DesGuardMockTick()noexcept{return mock_tick;}
std::uintptr_t DesGuardMockAddress(std::uintptr_t)noexcept;
}
#define GetTickCount64 DesGuardMockTick
#define XAR_DES_INIT_GUARD_CALL_ADDRESS(image,rva) DesGuardMockAddress(rva)
#ifndef XAR_DES_INIT_GUARD_NATIVE_TEST_INC
#define XAR_DES_INIT_GUARD_NATIVE_TEST_INC "ck3_121003_des_init_guard26785313_native_v1.inc"
#endif
#include XAR_DES_INIT_GUARD_NATIVE_TEST_INC
#undef XAR_DES_INIT_GUARD_CALL_ADDRESS
#undef GetTickCount64

namespace {
struct MockType {std::uintptr_t vtable=0;};
std::array<MockType,4>types{};
std::array<std::array<std::uintptr_t,8>,4>vtables{};
alignas(16)std::array<std::byte,0x170>builder_storage{},top_scope{};
alignas(16)std::array<std::byte,64>character{};
std::uintptr_t image=0;
DesInitGuardAny267V1*last_reference=nullptr;
std::uint64_t returned_id=0;
std::string_view last_key{};
bool player_value=true,shown_value=true,missing_definition=false;
bool wrong_player_type=false,noncanonical_player=false,player_callback_failed=false;
bool wrong_reference_type=false,wrong_reference_tag=false,wrong_reference_high=false;
bool wrong_builder_root=false,wrong_top_high=false,partial_end=false;
bool wrong_bool_type=false,noncanonical_bool=false,shown_callback_failed=false;
bool mutate_reference_in_shown=false,mutate_top_in_shown=false;
bool expire_in_player=false,expire_in_end=false,expire_in_shown=false;
bool destroy_top_throws=false,assign_throws=false;
unsigned players=0,made=0,builders=0,set_roots=0,ends=0,lookups=0,shown_calls=0;
unsigned top_destroys=0,reference_destroys=0,bool_destroys=0,text_destroys=0;
unsigned invalid_calls=0,execute_calls=0,unknown_rvas=0,layout_errors=0;
std::array<std::byte,8>definition{};
void Require(bool value,const char*why){if(!value)throw std::runtime_error(why);}
void Contract(bool value){if(!value)++layout_errors;}
std::uintptr_t Type(unsigned i){return reinterpret_cast<std::uintptr_t>(&types[i]);}
std::uintptr_t Empty(){return Type(0);}
std::uintptr_t Reference(){return Type(1);}
std::uintptr_t Top(){return Type(2);}
std::uintptr_t Boolean(){return Type(3);}
void Destroy(void*type,void*storage){
 const auto v=reinterpret_cast<std::uintptr_t>(type);
 if(v==Top()){
  ++top_destroys;std::uintptr_t p=0;std::memcpy(&p,storage,8);
  Contract(p==reinterpret_cast<std::uintptr_t>(top_scope.data()));
  if(destroy_top_throws)RaiseException(0xE0DE5891,0,0,nullptr);
 }else if(v==Reference())++reference_destroys;
 else if(v==Boolean())++bool_destroys;
 else Contract(v==Empty());
}
bool IsPlayer(void*actual,DesInitGuardAny267V1*out){
 ++players;Contract(actual==character.data());
 out->type=wrong_player_type?Empty():Boolean();
 out->storage[0]=static_cast<std::byte>(noncanonical_player?2:(player_value?1:0));
 if(expire_in_player)mock_tick=100;
 return !player_callback_failed;
}
bool MakeScope(void*actual,DesInitGuardAny267V1*out){
 ++made;Contract(actual==character.data());
 out->type=wrong_reference_type?Empty():Reference();
 const std::uint32_t tag=wrong_reference_tag?5u:4u;
 const auto id=returned_id|(wrong_reference_high?(std::uint64_t{1}<<32):0);
 std::memcpy(out->storage.data(),&tag,4);std::memcpy(out->storage.data()+8,&id,8);return true;
}
std::uintptr_t Builder(){++builders;builder_storage.fill(std::byte{});return image+0x6B03530;}
void CursorContract(const DesInitGuardArgCursor267V1*args,const DesInitGuardAny267V1*value){
 Contract(args&&args->table&&args->table->data==value&&args->index==0&&args->reserved==0);
 if(args&&args->table)Contract(args->table->capacity==1&&args->table->count==1&&args->table->allocator==0);
}
void*SetRoot(void*builder,const DesInitGuardArgCursor267V1*args){
 ++set_roots;Contract(builder==builder_storage.data());
 if(!args||!args->table||!args->table->data){++layout_errors;return nullptr;}
 CursorContract(args,args->table->data);Contract(args->table->data->type==Reference());
 last_reference=args->table->data;std::memcpy(builder,last_reference->storage.data(),16);
 if(wrong_builder_root){std::uint64_t id=returned_id+1;std::memcpy(static_cast<std::byte*>(builder)+8,&id,8);}
 return builder;
}
bool End(void*builder,DesInitGuardAny267V1*out){
 ++ends;Contract(builder==builder_storage.data());std::memcpy(top_scope.data(),builder,16);
 if(wrong_top_high){std::uint64_t id=0;std::memcpy(&id,top_scope.data()+8,8);id|=std::uint64_t{1}<<32;std::memcpy(top_scope.data()+8,&id,8);}
 out->type=Top();const auto p=reinterpret_cast<std::uintptr_t>(top_scope.data());std::memcpy(out->storage.data(),&p,8);
 if(expire_in_end)mock_tick=100;
 return !partial_end;
}
void*Assign(void*storage,const char*key,std::size_t n){
 last_key=std::string_view(key,n);Contract(last_key==std::string_view(kDesInitGuardKey267V1));
 Contract(last_key=="des_saved_game_initialize_gui"); // Exact header literal, never caller input.
 if(assign_throws)RaiseException(0xE0DE5892,0,0,nullptr);
 const auto p=reinterpret_cast<std::uintptr_t>(key);const auto len=static_cast<std::uint64_t>(n);
 std::memcpy(storage,&p,8);std::memcpy(static_cast<std::byte*>(storage)+16,&len,8);std::memcpy(static_cast<std::byte*>(storage)+24,&len,8);return storage;
}
void TextDestroy(void*){++text_destroys;}
void*Lookup(const void*storage){
 ++lookups;std::uintptr_t p=0;std::uint64_t n=0;std::memcpy(&p,storage,8);std::memcpy(&n,static_cast<const std::byte*>(storage)+16,8);
 Contract(std::string_view(reinterpret_cast<const char*>(p),static_cast<std::size_t>(n))==std::string_view(kDesInitGuardKey267V1));
 return missing_definition?nullptr:definition.data();
}
bool IsShown(void*actual,DesInitGuardAny267V1*out,const DesInitGuardArgCursor267V1*args){
 ++shown_calls;Contract(actual==definition.data());
 if(!args||!args->table||!args->table->data){++layout_errors;return false;}
 CursorContract(args,args->table->data);Contract(args->table->data->type==Top());
 std::uintptr_t p=0;std::memcpy(&p,args->table->data->storage.data(),8);Contract(p==reinterpret_cast<std::uintptr_t>(top_scope.data()));
 out->type=wrong_bool_type?Empty():Boolean();out->storage[0]=static_cast<std::byte>(noncanonical_bool?2:(shown_value?1:0));
 if(mutate_reference_in_shown&&last_reference){std::uint64_t id=returned_id+1;std::memcpy(last_reference->storage.data()+8,&id,8);}
 if(mutate_top_in_shown){std::uint64_t id=returned_id+1;std::memcpy(top_scope.data()+8,&id,8);}
 if(expire_in_shown)mock_tick=100;
 return !shown_callback_failed;
}
bool IsValidTrap(void*,DesInitGuardAny267V1*,const DesInitGuardArgCursor267V1*){++invalid_calls;return false;}
bool ExecuteTrap(void*,DesInitGuardAny267V1*,const DesInitGuardArgCursor267V1*){++execute_calls;return false;}
std::uintptr_t DesGuardMockAddress(std::uintptr_t rva)noexcept{
 switch(rva){
 case 0x8B2EF0:return reinterpret_cast<std::uintptr_t>(&Empty);
 case 0x8B5030:return reinterpret_cast<std::uintptr_t>(&Reference);
 case 0x16AFB60:return reinterpret_cast<std::uintptr_t>(&Top);
 case 0x8C2930:return reinterpret_cast<std::uintptr_t>(&Boolean);
 case 0x2B584E0:return reinterpret_cast<std::uintptr_t>(&IsPlayer);
 case 0x2BA7A20:return reinterpret_cast<std::uintptr_t>(&MakeScope);
 case 0x3D42F70:return reinterpret_cast<std::uintptr_t>(&Builder);
 case 0x3D5D7F0:return reinterpret_cast<std::uintptr_t>(&SetRoot);
 case 0x3D5D8C0:return reinterpret_cast<std::uintptr_t>(&End);
 case 0x896BB0:return reinterpret_cast<std::uintptr_t>(&Assign);
 case 0x897460:return reinterpret_cast<std::uintptr_t>(&TextDestroy);
 case 0x3D42F00:return reinterpret_cast<std::uintptr_t>(&Lookup);
 case 0x3DD1970:return reinterpret_cast<std::uintptr_t>(&IsShown);
 case 0x3DD19D0:return reinterpret_cast<std::uintptr_t>(&IsValidTrap);
 case 0x3DD18A0:return reinterpret_cast<std::uintptr_t>(&ExecuteTrap);
 default:++unknown_rvas;return 0;
 }
}
void Reset(std::uint32_t actor){
 returned_id=actor;player_value=shown_value=true;
 missing_definition=wrong_player_type=noncanonical_player=player_callback_failed=false;
 wrong_reference_type=wrong_reference_tag=wrong_reference_high=wrong_builder_root=false;
 wrong_top_high=partial_end=wrong_bool_type=noncanonical_bool=shown_callback_failed=false;
 mutate_reference_in_shown=mutate_top_in_shown=expire_in_player=expire_in_end=expire_in_shown=false;
 destroy_top_throws=assign_throws=false;
 players=made=builders=set_roots=ends=lookups=shown_calls=0;
 top_destroys=reference_destroys=bool_destroys=text_destroys=0;
 invalid_calls=execute_calls=unknown_rvas=layout_errors=0;
 mock_tick=10;last_key={};last_reference=nullptr;
 character.fill(std::byte{});std::memcpy(character.data()+0x18,&actor,4);
}
std::uint64_t WallFuture(){const auto n=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return static_cast<std::uint64_t>(n)+60000;}
bool Invoke(std::uint32_t actor,DesInitGuardNative267V1&out){return NativeDesInitGuard267V1(image,character.data(),actor,WallFuture(),100,out);}
void NoEffects(){Require(invalid_calls==0&&execute_calls==0&&unknown_rvas==0&&layout_errors==0,"unexpected call, effect, key or Any40/table24/cursor16 contract");}
}
int main(){
 try{
  static_assert(sizeof(DesInitGuardAny267V1)==40&&sizeof(DesInitGuardArgTable267V1)==24&&sizeof(DesInitGuardArgCursor267V1)==16);
  // This is own writable DATA, no executable fake image/process injection. The
  // arithmetic builder equality is retained; only callable addresses use seam.
  image=reinterpret_cast<std::uintptr_t>(builder_storage.data())-0x6B03530;
  Require(image!=0,"own synthetic nonzero base");
  for(unsigned i=0;i<types.size();++i){vtables[i].fill(0);vtables[i][3]=reinterpret_cast<std::uintptr_t>(&Destroy);types[i].vtable=reinterpret_cast<std::uintptr_t>(vtables[i].data());}
  DesInitGuardNative267V1 out;
  Reset(0);Require(Invoke(0,out)&&out.entered&&out.native_is_player&&out.shown&&out.cleanup_known&&out.definition==reinterpret_cast<std::uintptr_t>(definition.data()),"packedID0 clean true fixed query");
  Require(players==1&&made==1&&set_roots==1&&ends==1&&lookups==1&&shown_calls==1&&top_destroys==1&&reference_destroys==1&&bool_destroys==2&&text_destroys==1,"all owned objects and exact argument layout");NoEffects();
  Reset(0xFFFFFFFEu);Require(Invoke(0xFFFFFFFEu,out)&&out.native_is_player&&out.shown&&out.cleanup_known,"packedFFFFFFFE zero-extension is legal");NoEffects();
  Reset(7);shown_value=false;Require(Invoke(7,out)&&out.native_is_player&&!out.shown&&out.definition!=0&&out.cleanup_known,"real fixed definition IsShownfalse is clean DATA");NoEffects();
  Reset(7);missing_definition=true;Require(!Invoke(7,out)&&out.native_is_player&&out.definition==0&&!out.shown&&out.cleanup_known&&shown_calls==0&&top_destroys==1,"missing definition unavailable cannot masquerade as false closure");NoEffects();
  Reset(7);player_value=false;Require(!Invoke(7,out)&&!out.native_is_player&&out.definition==0&&made==0&&lookups==0&&shown_calls==0&&out.cleanup_known,"actualIsPlayerfalse cannot authorize closed guard evidence");NoEffects();
  Reset(7);wrong_player_type=true;Require(!Invoke(7,out)&&made==0&&out.cleanup_known,"wrong IsPlayer Any type must reject");NoEffects();
  Reset(7);noncanonical_player=true;Require(!Invoke(7,out)&&made==0&&out.cleanup_known,"IsPlayer bool2 must reject");NoEffects();
  Reset(7);player_callback_failed=true;Require(!Invoke(7,out)&&made==0&&out.cleanup_known,"typed IsPlayer callback failure must reject");NoEffects();
  Reset(7);wrong_reference_type=true;Require(!Invoke(7,out)&&set_roots==0&&out.cleanup_known,"wrong MakeScope Any type");NoEffects();
  Reset(7);wrong_reference_tag=true;Require(!Invoke(7,out)&&set_roots==0&&out.cleanup_known,"wrong Character reference tag");NoEffects();
  Reset(7);returned_id=8;Require(!Invoke(7,out)&&set_roots==0&&out.cleanup_known,"wrong actual reference ID");NoEffects();
  Reset(7);wrong_reference_high=true;Require(!Invoke(7,out)&&set_roots==0&&out.cleanup_known,"high32 reference pollution cannot truncate");NoEffects();
  Reset(0xFFFFFFFEu);returned_id=0xFFFFFFFFFFFFFFFEull;Require(!Invoke(0xFFFFFFFEu,out)&&set_roots==0&&out.cleanup_known,"sign extension is not packed32 zero extension");NoEffects();
  Reset(7);wrong_builder_root=true;Require(!Invoke(7,out)&&ends==0&&out.cleanup_known,"SetRoot full reference must match");NoEffects();
  Reset(7);wrong_top_high=true;Require(!Invoke(7,out)&&shown_calls==0&&top_destroys==1&&out.cleanup_known,"completed Top full reference mismatch still cleans");NoEffects();
  Reset(7);partial_end=true;Require(!Invoke(7,out)&&!out.cleanup_known&&shown_calls==0&&top_destroys==0,"partial nonempty Top cannot become completed/clean");NoEffects();
  Reset(7);wrong_bool_type=true;Require(!Invoke(7,out)&&top_destroys==1&&out.cleanup_known,"wrong IsShown Any type");NoEffects();
  Reset(7);noncanonical_bool=true;Require(!Invoke(7,out)&&out.cleanup_known,"IsShown bool2 cannot normalize false");NoEffects();
  Reset(7);shown_callback_failed=true;Require(!Invoke(7,out)&&out.cleanup_known,"IsShown typed callback false is not predicatefalse DATA");NoEffects();
  Reset(7);mutate_reference_in_shown=true;Require(!Invoke(7,out)&&out.cleanup_known,"postquery Character reference identity must remain full");NoEffects();
  Reset(7);mutate_top_in_shown=true;Require(!Invoke(7,out)&&out.cleanup_known,"postquery Top reference identity must remain full");NoEffects();
  Reset(7);mock_tick=100;Require(!Invoke(7,out)&&!out.entered&&players==0,"expired mono entry cannot invoke typed producers");NoEffects();
  Reset(7);Require(!NativeDesInitGuard267V1(image,character.data(),7,1,100,out)&&!out.entered&&players==0,"expired wall entry cannot invoke typed producers");NoEffects();
  Reset(7);expire_in_player=true;Require(!Invoke(7,out)&&made==0&&out.cleanup_known,"IsPlayer return expiry blocks later scope calls");NoEffects();
  Reset(7);expire_in_end=true;Require(!Invoke(7,out)&&top_destroys==1&&shown_calls==0&&out.cleanup_known,"completed Top is destroyed after return deadline expiry");NoEffects();
  Reset(7);expire_in_shown=true;Require(!Invoke(7,out)&&top_destroys==1&&text_destroys==1&&out.cleanup_known,"IsShown return expiry refuses result but cleans owned objects");NoEffects();
  Reset(7);destroy_top_throws=true;Require(!Invoke(7,out)&&!out.cleanup_known&&top_destroys==1,"SEH cleanup failure must remain unknown");NoEffects();
  Reset(7);assign_throws=true;Require(!Invoke(7,out)&&!out.cleanup_known&&lookups==0&&text_destroys==0,"partial string construction cleanup unknown cannot become false closure");NoEffects();
  std::cout<<"NoGame DES fixed readonly guard:28 explicit native-call/layout/identity/deadline/cleanup cases; zero IsValid/Execute; no ABI/live qualification\n";
  return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
 catch(...){return 1;}
}
