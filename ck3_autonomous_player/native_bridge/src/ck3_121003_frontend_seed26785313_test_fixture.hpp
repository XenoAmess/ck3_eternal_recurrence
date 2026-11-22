#pragma once
// Self-owned NoGame memory only. Never include in the production bridge.
#ifndef XAR_FRONTEND_SEED_SELF_OWNED_TEST
#error Define XAR_FRONTEND_SEED_SELF_OWNED_TEST only in the independent NoGame test TU
#endif
#include "xar_bridge/ck3_121003_frontend_menu26785313_v1.hpp"
#include "xar_bridge/ck3_121003_frontend_seed26785313_pins_v1.hpp"
#include <algorithm>
#include <array>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <string>
#include <string_view>
#include <windows.h>

namespace xar::ck3_121003::build26785313::frontend_seed_test {
static_assert(sizeof(std::uintptr_t)==8,"Exact self-owned x64 fixture");
inline void Require(bool yes,const char*why){if(!yes)throw std::runtime_error(why);}
struct FakeImage;
inline thread_local FakeImage* active=nullptr;
inline ULONGLONG mock_tick=10;
inline ULONGLONG MockTick()noexcept{return mock_tick;}
inline std::uint64_t WallFuture(){return static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count())+60000;}
struct Calls {unsigned can=0,open=0,group=0,bookmark=0,character=0,start_game=0,on_start=0,layout_errors=0;};
struct FakeImage {
 static constexpr std::size_t image_bytes=0x6B00000;
 static constexpr std::uintptr_t own=0x6900000;
 std::uintptr_t image=0,application=0,owner=0,wrapper=0,handler=0,main=0,setup=0,context=0,main_root=0,book_root=0,
  database=0,group=0,other_group=0,group_rows=0,bookmark=0,other_bookmark=0,bookmark_rows=0,characters=0,strings=0;
 void* world=nullptr;
 Calls calls{};
 bool can_start=true,ignore_group=false,ignore_bookmark=false,ignore_character=false,ignore_start_game=false;
 std::uintptr_t throw_rva=0;
 void(*after_open)(FakeImage*)=nullptr;void(*after_group)(FakeImage*)=nullptr;void(*after_bookmark)(FakeImage*)=nullptr;
 void(*after_character)(FakeImage*)=nullptr;void(*after_start_game)(FakeImage*)=nullptr;void(*after_on_start)(FakeImage*)=nullptr;
 FakeImage(){
  image=reinterpret_cast<std::uintptr_t>(VirtualAlloc(nullptr,image_bytes,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
  Require(image!=0,"own RW fake-image allocation");
  application=image+own;owner=application+0x1000;wrapper=application+0x2000;handler=application+0x3000;
  main=application+0x4000;setup=application+0x5000;context=application+0x6000;main_root=application+0x7000;book_root=application+0x8000;
  database=application+0x9000;group=application+0xA000;other_group=group+0x200;group_rows=application+0xB000;
  bookmark=application+0xC000;other_bookmark=bookmark+0x300;bookmark_rows=application+0xD000;characters=application+0xE000;strings=application+0x10000;
  active=this;Reset();
 }
 FakeImage(const FakeImage&)=delete;FakeImage&operator=(const FakeImage&)=delete;
 ~FakeImage(){if(active==this)active=nullptr;if(image)VirtualFree(reinterpret_cast<void*>(image),0,MEM_RELEASE);}
 template<class T>void Put(std::uintptr_t object,std::size_t offset,T value){
  const auto at=object+offset;Require(at>=image&&at+sizeof(T)>=at&&at+sizeof(T)<=image+image_bytes,"own fixture write range");
  std::memcpy(reinterpret_cast<void*>(at),&value,sizeof(value));
 }
 template<class T>T Get(std::uintptr_t object,std::size_t offset)const {T value{};std::memcpy(&value,reinterpret_cast<const void*>(object+offset),sizeof(value));return value;}
 void Contract(bool yes){if(!yes)++calls.layout_errors;}
 void Type(std::uintptr_t object,std::uintptr_t vt,std::uintptr_t col,std::uint32_t offset,std::uint32_t descriptor){
  Put(object,0,image+vt);Put(image+vt-8,0,image+col);Put(image+col,0,std::uint32_t{1});Put(image+col,4,offset);
  Put(image+col,12,descriptor);Put(image+col,20,static_cast<std::uint32_t>(col));
 }
 void Key(std::uintptr_t object,std::size_t offset,std::string_view key,unsigned slot){
  Require(!key.empty()&&key.size()<=128&&slot<32,"own bounded key input");
  std::memset(reinterpret_cast<void*>(object+offset),0,32);
  if(key.size()<=15)std::memcpy(reinterpret_cast<void*>(object+offset),key.data(),key.size());
  else {const auto text=strings+slot*256;std::memset(reinterpret_cast<void*>(text),0,256);std::memcpy(reinterpret_cast<void*>(text),key.data(),key.size());Put(object,offset,text);}
  Put(object,offset+16,static_cast<std::uint64_t>(key.size()));Put(object,offset+24,static_cast<std::uint64_t>(key.size()<=15?15:key.size()));
 }
 void Group(std::uintptr_t object,std::string_view key,unsigned slot){
  Type(object,0x4FEE390,0x57C34E0,0,0x5F8A678);Key(object,0x18,key,slot);Put(object,0x38,std::uint32_t{0x4744624F});
 }
 void Bookmark(std::uintptr_t object,std::string_view key,unsigned slot,std::uintptr_t actual_group){
  Type(object,0x4FEDA28,0x57C3530,0,0x5F8A6C8);Key(object,0x18,key,slot);Put(object,0x38,std::uint32_t{0x4744624F});
  Put(object,0x40,std::int32_t{53144328});Put(object,0x100,std::uint8_t{1});Put(object,0xF8,actual_group);
  Put(object,0x108,characters);Put(object,0x110,std::int32_t{1});Put(object,0x114,std::int32_t{1});
 }
 void Character(std::uintptr_t object,std::string_view key,unsigned slot,std::uintptr_t parent){
  Type(object,0x5017120,0x57FA1C8,0,0x6731B20);Key(object,8,key,slot);Put(object,0x130,parent);
 }
 void Reset(){
  active=this;
  std::memset(reinterpret_cast<void*>(application),0,0x20000);
  for(const auto&p:frontend_seed_pins::kPins){Require(p.rva+p.bytes.size()<image_bytes,"actual code pin inside own fake image");std::memcpy(reinterpret_cast<void*>(image+p.rva),p.bytes.data(),p.bytes.size());}
  world=nullptr;calls={};can_start=true;ignore_group=ignore_bookmark=ignore_character=ignore_start_game=false;throw_rva=0;mock_tick=10;
  after_open=after_group=after_bookmark=after_character=after_start_game=after_on_start=nullptr;
  Put(application,0x28,owner); // current; pending+78 remains zero after update
  Type(owner,0x4B45978,0x51C8AF8,0,0x60B8E00);Put(owner,0x18,application);Put(owner,0x10,wrapper);
  Type(wrapper,0x4B7B2C0,0x5220950,0,0x5DB9748);Put(wrapper,8,handler);
  Type(handler,0x4B7B758,0x5221268,0,0x6120958);Put(handler,8,std::int32_t{0});Put(handler,12,std::int32_t{0});Put(handler,0x10,main);Put(handler,0x30,setup);
  Type(main,0x4C620D8,0x539FDB8,0,0x62F7E98);Type(main+0x10,0x4C62118,0x539FD90,0x10,0x62F7E98);
  Type(setup,0x4B9FB58,0x524F740,0,0x6155B88);Type(setup+0x10,0x4B9FB30,0x524F718,0x10,0x6155B88);
  Put(main,0x98,owner);Put(main,0xA0,handler);Put(main,0x68,context);Put(main,0x60,main_root);
  Put(setup,0x98,owner);Put(setup,0xA0,handler);Put(setup,0x68,context);Put(setup,0x60,book_root);
  Group(group,"bm_group_1066",0);Group(other_group,"bm_group_other",1);
  Put(group_rows,0,group);Put(setup,0xC0,group_rows);Put(setup,0xC8,std::int32_t{1});Put(setup,0xCC,std::int32_t{1});
  Type(database,0x5017038,0x57FA1A0,0,0x6731AF8);Put(image,0x68AFC40,database);
  Put(database,0x50,bookmark_rows);Put(database,0x58,std::int32_t{1});Put(database,0x5C,std::int32_t{1});Put(bookmark_rows,0,bookmark);
  Bookmark(bookmark,kFrontendRobertBookmark267V1,2,group);Character(characters,kFrontendRobertCharacter267V1,3,bookmark);
  Put(setup,0xD8,group);Put(setup,0x120,bookmark);Put(setup,0x128,std::int32_t{0});Put(setup,0x130,std::uint8_t{0});
 }
 void Main(){Put(handler,8,std::int32_t{0});Put(handler,12,std::int32_t{0});}
 void Book(){Put(handler,8,std::int32_t{4});Put(handler,12,std::int32_t{4});}
 unsigned Effects()const{return calls.open+calls.group+calls.bookmark+calls.character+calls.start_game+calls.on_start;}
 void MaybeThrow(std::uintptr_t rva){if(throw_rva==rva)RaiseException(0xE0F26739,0,0,nullptr);}
};
inline bool __fastcall CanStart(void*view){auto&f=*active;++f.calls.can;f.Contract(view==reinterpret_cast<void*>(f.setup));f.MaybeThrow(0x11320B0);return f.can_start;}
inline void __fastcall OnNewGame(void*view){auto&f=*active;++f.calls.open;f.Contract(view==reinterpret_cast<void*>(f.main));f.MaybeThrow(0x1BB01C0);f.Book();if(f.after_open)f.after_open(&f);}
inline void __fastcall SetGroup(void*view,const void*group){auto&f=*active;++f.calls.group;f.Contract(view==reinterpret_cast<void*>(f.setup)&&group==reinterpret_cast<void*>(f.group));f.MaybeThrow(0x11314D0);if(!f.ignore_group)f.Put(f.setup,0xD8,reinterpret_cast<std::uintptr_t>(group));if(f.after_group)f.after_group(&f);}
inline void __fastcall SetBookmark(void*view,const void*bookmark){auto&f=*active;++f.calls.bookmark;f.Contract(view==reinterpret_cast<void*>(f.setup)&&bookmark==reinterpret_cast<void*>(f.bookmark));f.MaybeThrow(0x1131EC0);if(!f.ignore_bookmark)f.Put(f.setup,0x120,reinterpret_cast<std::uintptr_t>(bookmark));if(f.after_bookmark)f.after_bookmark(&f);}
inline void __fastcall SetCharacter(void*view,const void*character){auto&f=*active;++f.calls.character;f.Contract(view==reinterpret_cast<void*>(f.setup)&&character==reinterpret_cast<void*>(f.characters));f.MaybeThrow(0x1131FF0);if(!f.ignore_character)f.Put(f.setup,0x128,std::int32_t{0});if(f.after_character)f.after_character(&f);}
inline void __fastcall StartGame(void*view){auto&f=*active;++f.calls.start_game;f.Contract(view==reinterpret_cast<void*>(f.setup));f.MaybeThrow(0x1130E90);if(!f.ignore_start_game)f.Put(f.setup,0x130,std::uint8_t{1});if(f.after_start_game)f.after_start_game(&f);}
inline void __fastcall OnStart(void*view){auto&f=*active;++f.calls.on_start;f.Contract(view==reinterpret_cast<void*>(f.setup));f.MaybeThrow(0x11315F0);if(f.after_on_start)f.after_on_start(&f);}
inline std::uintptr_t CallAddress(std::uintptr_t image,std::uintptr_t rva){
 if(!active||active->image!=image){if(active)++active->calls.layout_errors;return 0;}
 switch(rva){case 0x11320B0:return reinterpret_cast<std::uintptr_t>(&CanStart);case 0x1BB01C0:return reinterpret_cast<std::uintptr_t>(&OnNewGame);
  case 0x11314D0:return reinterpret_cast<std::uintptr_t>(&SetGroup);case 0x1131EC0:return reinterpret_cast<std::uintptr_t>(&SetBookmark);case 0x1131FF0:return reinterpret_cast<std::uintptr_t>(&SetCharacter);
  case 0x1130E90:return reinterpret_cast<std::uintptr_t>(&StartGame);case 0x11315F0:return reinterpret_cast<std::uintptr_t>(&OnStart);default:++active->calls.layout_errors;return 0;}
}
} // namespace xar::ck3_121003::build26785313::frontend_seed_test
