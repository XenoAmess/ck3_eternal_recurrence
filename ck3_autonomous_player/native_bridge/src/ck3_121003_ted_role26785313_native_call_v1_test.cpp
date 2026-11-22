// SOURCE_ONLY NoGame simulation. This file calls an OWN fake address image;
// passing it never qualifies CK3 ABI, installed definitions, permissions or live.
#include <array>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string_view>
#include <windows.h>

namespace {ULONGLONG mock_tick=10;ULONGLONG TedRoleMockTick()noexcept{return mock_tick;}}
// Deterministic deadline tests affect only this included Source candidate.
// Kernel32 declarations were included before the macro; there is no hooking.
#define GetTickCount64 TedRoleMockTick
#ifndef XAR_TED_ROLE_NATIVE_TEST_INC
#define XAR_TED_ROLE_NATIVE_TEST_INC "ck3_121003_ted_role26785313_native_v1.inc"
#endif
#include XAR_TED_ROLE_NATIVE_TEST_INC
#undef GetTickCount64

namespace {
constexpr std::size_t kFakeImageBytes=0x7000000;
constexpr std::uintptr_t kBuilder=0x6B03530,kEmpty=0x6C00000,kReference=0x6C00080,kTop=0x6C00100,kBoolean=0x6C00180,kDefinition=0x6C02000;
std::uintptr_t image=0;
std::array<std::byte,64>character{};
std::array<std::byte,0x170>top_scope{};
std::uint64_t returned_id=0;
bool expected_recipient=false,missing_definition=false,shown_value=true,wrong_reference_tag=false,wrong_reference_high=false,wrong_top_high=false;
bool partial_end=false,wrong_bool_type=false,noncanonical_bool=false,expire_in_shown=false,destroy_top_throws=false;
unsigned made=0,builders=0,set_roots=0,ends=0,lookups=0,shown_calls=0,top_destroys=0,reference_destroys=0,bool_destroys=0,text_destroys=0,invalid_calls=0,execute_calls=0,layout_errors=0;
std::string_view last_key;
void Require(bool condition,const char*why){if(!condition)throw std::runtime_error(why);}
void Contract(bool condition){if(!condition)++layout_errors;}
std::uintptr_t Empty(){return image+kEmpty;}
std::uintptr_t Reference(){return image+kReference;}
std::uintptr_t Top(){return image+kTop;}
std::uintptr_t Boolean(){return image+kBoolean;}
void Destroy(void*type,void*storage){
 const auto value=reinterpret_cast<std::uintptr_t>(type);
 if(value==image+kTop){
  ++top_destroys;std::uintptr_t ptr=0;std::memcpy(&ptr,storage,8);Contract(ptr==reinterpret_cast<std::uintptr_t>(top_scope.data()));
  if(destroy_top_throws)RaiseException(0xE07ED833,0,0,nullptr);
 }else if(value==image+kReference)++reference_destroys;
 else if(value==image+kBoolean)++bool_destroys;
 else Contract(value==image+kEmpty);
}
bool MakeScope(void*actual,TedRoleAny267V1*out){
 ++made;Contract(actual==character.data());out->type=Reference();
 const std::uint32_t tag=wrong_reference_tag?5u:4u;
 const std::uint64_t id=returned_id|(wrong_reference_high?(std::uint64_t{1}<<32):0);
 std::memcpy(out->storage.data(),&tag,4);std::memcpy(out->storage.data()+8,&id,8);return true;
}
std::uintptr_t Builder(){++builders;std::memset(reinterpret_cast<void*>(image+kBuilder),0,0x170);return image+kBuilder;}
void CursorContract(const TedRoleArgCursor267V1*args,const TedRoleAny267V1*value){
 Contract(args&&args->table&&args->table->data==value&&args->index==0&&args->reserved==0);
 if(args&&args->table)Contract(args->table->capacity==1&&args->table->count==1&&args->table->allocator==0);
}
void*SetRoot(void*builder,const TedRoleArgCursor267V1*args){
 ++set_roots;Contract(builder==reinterpret_cast<void*>(image+kBuilder));
 if(!args||!args->table||!args->table->data){++layout_errors;return nullptr;}
 CursorContract(args,args->table->data);Contract(args->table->data->type==Reference());
 std::memcpy(builder,args->table->data->storage.data(),16);return builder;
}
bool End(void*builder,TedRoleAny267V1*out){
 ++ends;Contract(builder==reinterpret_cast<void*>(image+kBuilder));std::memcpy(top_scope.data(),builder,16);
 if(wrong_top_high){std::uint64_t id=0;std::memcpy(&id,top_scope.data()+8,8);id|=std::uint64_t{1}<<32;std::memcpy(top_scope.data()+8,&id,8);}
 out->type=Top();const auto ptr=reinterpret_cast<std::uintptr_t>(top_scope.data());std::memcpy(out->storage.data(),&ptr,8);return !partial_end;
}
void*Assign(void*storage,const char*key,std::size_t n){
 last_key=std::string_view(key,n);const auto wanted=expected_recipient?std::string_view("tea120_current_recipient_actor_witness_gui"):std::string_view("tea120_current_song_actor_witness_gui");
 Contract(last_key==wanted);const auto ptr=reinterpret_cast<std::uintptr_t>(key);const auto length=static_cast<std::uint64_t>(n);
 std::memcpy(storage,&ptr,8);std::memcpy(static_cast<std::byte*>(storage)+16,&length,8);std::memcpy(static_cast<std::byte*>(storage)+24,&length,8);return storage;
}
void TextDestroy(void*){++text_destroys;}
void*Lookup(const void*storage){
 ++lookups;std::uintptr_t ptr=0;std::uint64_t length=0;std::memcpy(&ptr,storage,8);std::memcpy(&length,static_cast<const std::byte*>(storage)+16,8);
 Contract(std::string_view(reinterpret_cast<const char*>(ptr),static_cast<std::size_t>(length))==last_key);
 return missing_definition?nullptr:reinterpret_cast<void*>(image+kDefinition);
}
bool IsShown(void*definition,TedRoleAny267V1*out,const TedRoleArgCursor267V1*args){
 ++shown_calls;Contract(definition==reinterpret_cast<void*>(image+kDefinition));
 if(!args||!args->table||!args->table->data){++layout_errors;return false;}
 CursorContract(args,args->table->data);Contract(args->table->data->type==Top());std::uintptr_t root=0;std::memcpy(&root,args->table->data->storage.data(),8);
 Contract(root==reinterpret_cast<std::uintptr_t>(top_scope.data()));
 out->type=wrong_bool_type?Empty():Boolean();out->storage[0]=static_cast<std::byte>(noncanonical_bool?2:(shown_value?1:0));
 if(expire_in_shown)mock_tick=101;return true;
}
bool IsValidTrap(void*,TedRoleAny267V1*,const TedRoleArgCursor267V1*){++invalid_calls;return false;}
bool ExecuteTrap(void*,TedRoleAny267V1*,const TedRoleArgCursor267V1*){++execute_calls;return false;}
void Write(std::uintptr_t at,const void*data,std::size_t n){
 const auto page=at&~std::uintptr_t{4095};const auto length=((at-page+n+4095)/4096)*4096;
 Require(VirtualAlloc(reinterpret_cast<void*>(page),length,MEM_COMMIT,PAGE_READWRITE)!=nullptr,"own fake image commit");
 DWORD old=0;Require(VirtualProtect(reinterpret_cast<void*>(page),length,PAGE_READWRITE,&old)!=0,"own fake page writable");
 std::memcpy(reinterpret_cast<void*>(at),data,n);
}
template<class F>void Code(std::uintptr_t rva,F target){
 std::array<unsigned char,12>bytes{0x48,0xB8};const auto fn=reinterpret_cast<std::uintptr_t>(target);std::memcpy(bytes.data()+2,&fn,8);bytes[10]=0xFF;bytes[11]=0xE0;
 Write(image+rva,bytes.data(),bytes.size());DWORD old=0;Require(VirtualProtect(reinterpret_cast<void*>(image+rva),bytes.size(),PAGE_EXECUTE_READ,&old)!=0,"own fake thunk executable");
 Require(FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(image+rva),bytes.size())!=0,"own fake instruction flush");
}
void Type(std::uintptr_t singleton,std::uintptr_t vtable){
 const auto vt=image+vtable,fn=reinterpret_cast<std::uintptr_t>(&Destroy);Write(image+singleton,&vt,8);Write(vt+0x18,&fn,8);
}
void Reset(std::uint32_t actor,bool recipient=false){
 returned_id=actor;expected_recipient=recipient;missing_definition=wrong_reference_tag=wrong_reference_high=wrong_top_high=partial_end=wrong_bool_type=noncanonical_bool=expire_in_shown=destroy_top_throws=false;shown_value=true;
 made=builders=set_roots=ends=lookups=shown_calls=top_destroys=reference_destroys=bool_destroys=text_destroys=invalid_calls=execute_calls=layout_errors=0;mock_tick=10;last_key={};
}
std::uint64_t WallFuture(){const auto now=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return static_cast<std::uint64_t>(now)+60000;}
bool Invoke(std::uint32_t actor,TedRoleNative267V1&out){return NativeTedRole267V1(image,character.data(),actor,expected_recipient,WallFuture(),100,out);}
void NoEffects(){Require(invalid_calls==0&&execute_calls==0&&layout_errors==0,"forbidden call or exact argument/layout contract violated");}
}
int main(){
 try{
  static_assert(sizeof(TedRoleAny267V1)==40&&sizeof(TedRoleArgTable267V1)==24&&sizeof(TedRoleArgCursor267V1)==16);
  image=reinterpret_cast<std::uintptr_t>(VirtualAlloc(nullptr,kFakeImageBytes,MEM_RESERVE,PAGE_NOACCESS));Require(image!=0,"own fake image reserve");
  Type(kEmpty,0x6C10000);Type(kReference,0x6C10080);Type(kTop,0x6C10100);Type(kBoolean,0x6C10180);
  std::array<std::byte,0x170>zero{};Write(image+kBuilder,zero.data(),zero.size());
  Code(0x8B2EF0,&Empty);Code(0x8B5030,&Reference);Code(0x16AFB60,&Top);Code(0x8C2930,&Boolean);Code(0x2BA7A20,&MakeScope);
  Code(0x3D42F70,&Builder);Code(0x3D5D7F0,&SetRoot);Code(0x3D5D8C0,&End);Code(0x896BB0,&Assign);Code(0x897460,&TextDestroy);Code(0x3D42F00,&Lookup);
  Code(0x3DD1970,&IsShown);Code(0x3DD19D0,&IsValidTrap);Code(0x3DD18A0,&ExecuteTrap);
  TedRoleNative267V1 out;
  Reset(0);Require(Invoke(0,out)&&out.entered&&out.shown&&out.definition==image+kDefinition&&out.cleanup_known,"packedID0 must remain legal");
  Require(made==1&&set_roots==1&&ends==1&&shown_calls==1&&top_destroys==1&&reference_destroys==1&&bool_destroys==1&&text_destroys==1,"full exact argument/Top cleanup success");NoEffects();
  Reset(0xFFFFFFFEu,true);Require(Invoke(0xFFFFFFFEu,out)&&out.shown&&out.cleanup_known,"full signed32 bit pattern must be zero-extended packed ID");NoEffects();
  Reset(0xFFFFFFFEu);returned_id=0xFFFFFFFFFFFFFFFEull;Require(!Invoke(0xFFFFFFFEu,out)&&out.cleanup_known&&set_roots==0,"sign-extended high32 must not masquerade as the packed32 reference");NoEffects();
  Reset(7,true);shown_value=false;Require(Invoke(7,out)&&!out.shown&&out.definition==image+kDefinition&&out.cleanup_known,"IsShownfalse is clean DATA not failed permission");NoEffects();
  Reset(7);missing_definition=true;Require(Invoke(7,out)&&out.definition==0&&!out.shown&&out.cleanup_known&&shown_calls==0&&top_destroys==1&&text_destroys==1,"missing exact definition must be clean DATA0 without predicate");NoEffects();
  Reset(7);wrong_reference_high=true;Require(!Invoke(7,out)&&out.cleanup_known&&set_roots==0&&shown_calls==0,"high32 reference pollution must not truncate to actor");NoEffects();
  Reset(7);returned_id=8;Require(!Invoke(7,out)&&out.cleanup_known&&set_roots==0,"pointer reverse reference mismatch");NoEffects();
  Reset(7);wrong_reference_tag=true;Require(!Invoke(7,out)&&out.cleanup_known&&set_roots==0,"wrong reference tag");NoEffects();
  Reset(7);wrong_top_high=true;Require(!Invoke(7,out)&&out.cleanup_known&&shown_calls==0&&top_destroys==1,"Top reference mismatch must destroy only completedTop");NoEffects();
  Reset(7);partial_end=true;Require(!Invoke(7,out)&&!out.cleanup_known&&shown_calls==0&&top_destroys==0,"partial nonemptyTop must not be declared/destroyed as completed");NoEffects();
  Reset(7);wrong_bool_type=true;Require(!Invoke(7,out)&&out.cleanup_known&&top_destroys==1,"wrong boolean Any");NoEffects();
  Reset(7);noncanonical_bool=true;Require(!Invoke(7,out)&&out.cleanup_known,"noncanonical bool2 must be refused");NoEffects();
  Reset(7);mock_tick=100;Require(!Invoke(7,out)&&!out.entered&&made==0,"expired monotonic entry must not call typed producer");NoEffects();
  Reset(7);Require(!NativeTedRole267V1(image,character.data(),7,false,1,100,out)&&!out.entered&&made==0,"expired wall entry must not call typed producer");NoEffects();
  Reset(7);expire_in_shown=true;Require(!Invoke(7,out)&&out.cleanup_known&&shown_calls==1&&top_destroys==1&&text_destroys==1,"postcall expiry must refuse result but still clean completed objects");NoEffects();
  Reset(7);destroy_top_throws=true;Require(!Invoke(7,out)&&!out.cleanup_known&&top_destroys==1,"SEH cleanup failure must not normalize to clean success");NoEffects();
  Require(VirtualFree(reinterpret_cast<void*>(image),0,MEM_RELEASE)!=0,"own fake image release");image=0;
  std::cout<<"NoGame simulated fixed-role native calls/layout/deadline/cleanup cases completed; no ABI/live qualification\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';if(image)VirtualFree(reinterpret_cast<void*>(image),0,MEM_RELEASE);return 1;}
 catch(...){if(image)VirtualFree(reinterpret_cast<void*>(image),0,MEM_RELEASE);return 1;}
}
