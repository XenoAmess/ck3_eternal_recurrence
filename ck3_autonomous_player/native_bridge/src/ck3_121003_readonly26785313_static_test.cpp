#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
// Finite whole-unit fixture follows the existing BB3 body-inclusion pattern.
// Compile the actual unchanged Core and actual new implementation once.
#include "ck3_1210_core.cpp"
#include "ck3_121003_readonly26785313_v1.cpp"
#include <windows.h>
#include <bcrypt.h>
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
namespace f=xar::ck3_121003::build26785313;
namespace c=xar::ck3_1210;
namespace m=xar::ck3_11906;
namespace {
void Require(bool value,const char *message){if(!value)throw std::runtime_error(message);}
template<class T>void Put(std::vector<unsigned char>&v,std::size_t off,T value){
  Require(off+sizeof(value)<=v.size(),"fixture bounds");std::memcpy(v.data()+off,&value,sizeof(value));
}
std::string Sha(const std::filesystem::path&path) {
  BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
  Require(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)>=0,"SHA provider");
  ULONG object_bytes=0,actual=0;
  Require(BCryptGetProperty(algorithm,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&object_bytes),sizeof(object_bytes),&actual,0)>=0,"SHA object size");
  std::vector<unsigned char> object(object_bytes);
  Require(BCryptCreateHash(algorithm,&hash,object.data(),object_bytes,nullptr,0,0)>=0,"SHA init");
  std::ifstream input(path,std::ios::binary);Require(bool(input),"actual EXE open");
  std::array<char,65536> chunk{};
  while(input){input.read(chunk.data(),static_cast<std::streamsize>(chunk.size()));const auto count=input.gcount();
    if(count)Require(BCryptHashData(hash,reinterpret_cast<PUCHAR>(chunk.data()),static_cast<ULONG>(count),0)>=0,"SHA chunk");}
  Require(input.eof(),"actual EXE stream");
  std::array<unsigned char,32> digest{};Require(BCryptFinishHash(hash,digest.data(),static_cast<ULONG>(digest.size()),0)>=0,"SHA finish");
  BCryptDestroyHash(hash);BCryptCloseAlgorithmProvider(algorithm,0);
  const char hex[]="0123456789ABCDEF";std::string result;
  for(const auto b:digest){result.push_back(hex[b>>4]);result.push_back(hex[b&15]);}return result;
}
struct PeWindows {
  struct Section{std::uint32_t rva,size,offset;};
  std::ifstream input;std::vector<Section> sections;void*image=nullptr;
  // CI has no game files. This explicit mode exercises source-only guards and
  // the same production reader; it never claims an actual EXE observation.
  PeWindows(){
    image=VirtualAlloc(nullptr,f::kImageSize,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
    Require(image!=nullptr,"synthetic source-only image");
    const auto put=[this]<class T>(std::size_t offset,T value){
      std::memcpy(static_cast<unsigned char*>(image)+offset,&value,sizeof(value));
    };
    constexpr std::uint32_t pe=0x100;
    put(0,std::uint16_t{0x5A4D});put(0x3C,pe);put(pe,std::uint32_t{0x4550});
    put(pe+4,std::uint16_t{0x8664});put(pe+8,f::kPeTimestamp);
    put(pe+24,std::uint16_t{0x20B});put(pe+24+24,std::uint64_t{0x140000000ULL});
    put(pe+24+56,static_cast<std::uint32_t>(f::kImageSize));
    for(const auto&pin:f::ReadonlyImagePins())
      std::memcpy(static_cast<unsigned char*>(image)+pin.rva,pin.bytes.data(),pin.bytes.size());
  }
  template<class T>T At(std::uint64_t position) {T v{};input.seekg(static_cast<std::streamoff>(position));input.read(reinterpret_cast<char*>(&v),sizeof(v));Require(bool(input),"bounded PE read");return v;}
  explicit PeWindows(const std::filesystem::path&path):input(path,std::ios::binary){
    Require(std::filesystem::file_size(path)==f::kExecutableFileBytes&&Sha(path)==f::kExecutableSha256,"exact actual EXE SHA and size");
    const auto pe=At<std::uint32_t>(0x3C);const auto n=At<std::uint16_t>(pe+6),opt=At<std::uint16_t>(pe+20);
    Require(At<std::uint32_t>(pe+8)==f::kPeTimestamp,"timestamp");
    Require(At<std::uint32_t>(pe+24+56)==f::kImageSize,"image bounds");
    for(std::uint16_t i=0;i<n;++i){const auto s=pe+24+opt+std::uint32_t{i}*40;
      sections.push_back({At<std::uint32_t>(s+12),At<std::uint32_t>(s+16),At<std::uint32_t>(s+20)});}
    image=VirtualAlloc(nullptr,f::kImageSize,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);Require(image!=nullptr,"RAM-only bounded mapped windows");
    input.seekg(0);input.read(static_cast<char*>(image),0x400);Require(bool(input),"PE headers");
    for(const auto&pin:f::ReadonlyImagePins()){
      bool copied=false;
      for(const auto&section:sections)if(pin.rva>=section.rva&&pin.rva-section.rva+pin.bytes.size()<=section.size){
        input.seekg(static_cast<std::streamoff>(section.offset+pin.rva-section.rva));
        input.read(static_cast<char*>(image)+pin.rva,static_cast<std::streamsize>(pin.bytes.size()));Require(bool(input),"actual immutable code window");copied=true;break;}
      Require(copied,"all pins are actual file-backed windows");
    }
  }
  ~PeWindows(){if(image)VirtualFree(image,0,MEM_RELEASE);}
};
struct Fixture {
  std::vector<unsigned char> state=std::vector<unsigned char>(0x100),jomini=std::vector<unsigned char>(0x40),
    players=std::vector<unsigned char>(0x200),player=std::vector<unsigned char>(0x80),
    data=std::vector<unsigned char>(0x27000),entry=std::vector<unsigned char>(0xE0),
    storage=std::vector<unsigned char>(0x30),slots=std::vector<unsigned char>(0x20),
    actor=std::vector<unsigned char>(0x1D8),living=std::vector<unsigned char>(0x300);
  void *state_slot=state.data(),*jomini_slot=jomini.data(),*storage_slot=storage.data(),*entry_slot=entry.data();
  std::int32_t id=-16777215;std::uint32_t calls=0;bool drift=false;
  static Fixture *active;
  static void*Local(void*){auto&v=*active;++v.calls;if(v.drift&&v.calls==2)Put(v.living,0x100,std::int64_t{-12344});return v.player.data();}
  Fixture(){active=this;Put(state,8,std::int32_t{53176992});Put(state,0x70,std::int32_t{2});Put(state,0xA0,data.data());
    Put(jomini,0x18,players.data());Put(jomini,0x20,std::uint8_t{1});Put(players,0x1F0,std::int32_t{1});Put(player,0x70,std::int32_t{1});
    Put(data,0x26FB0,&entry_slot);Put(data,0x26FBC,std::int32_t{1});Put(entry,0xD8,std::int32_t{1});Put(entry,0xB0,id);
    Put(storage,0x20,slots.data());Put(storage,0x2C,std::int32_t{2});Put(slots,0x18,actor.data());
    Put(actor,0x18,id);Put(actor,0x1C,std::uint32_t{0x43686172});Put(actor,0x1B0,living.data());
    Put(living,0x100,std::int64_t{-12345});Put(living,0x130,std::int64_t{222222});Put(living,0x110,std::int64_t{333333});Put(living,0x2F8,std::int32_t{42});
  }
  c::CoreBindings Core(){return {true,&state_slot,&jomini_slot,&storage_slot,&Local,c::ImageBuildV1::unknown};}
};
Fixture*Fixture::active=nullptr;
bool Run(Fixture&fixture,std::uintptr_t image,f::ReadonlyObservation&out,bool offline=true){
  m::MainThreadQueryMailboxV1 mailbox;mailbox.offline_fixture=offline;
  f::ReadonlyContext query;query.bindings=f::NoGameBindings(image,fixture.Core());query.mailbox=&mailbox;query.ticket.sequence=1;
  const bool ack=f::ExecuteReadonlyOnOwner(&query,{});out=query.observation;return ack;
}
}
int main(int argc,char**argv){
 try {
   Require(argc==2,"actual EXE path or explicit --synthetic-image required; no Game process accepted");
   const bool synthetic=std::string_view(argv[1])=="--synthetic-image";
   const auto pe=synthetic?std::make_unique<PeWindows>():std::make_unique<PeWindows>(argv[1]);
   const auto base=reinterpret_cast<std::uintptr_t>(pe->image);
   Require(f::VerifyReadonlyImage(base),"exact image pin guards");
  Require(f::BindReadonlyImage(base,f::kExecutableSha256).exact_image_admitted,"new isolated binder");
  Require(!f::BindReadonlyImage(base,"BB3FEF106240E95ECDB6F1532982E89E9432C92A99D33DB623521572F06E6F79").exact_image_admitted,"BB3 denied");
  Require(!c::BindCoreImage(base,f::kExecutableSha256).enabled,"legacy hash router remains closed");
   auto*first=static_cast<unsigned char*>(pe->image)+f::ReadonlyImagePins()[0].rva;*first^=1;
  Require(!f::VerifyReadonlyImage(base),"tampered actual pin denied");*first^=1;Require(f::VerifyReadonlyImage(base),"restored RAM-only pin");
  const auto&owner=f::ReadonlyThreadProfile();
  Require(owner.jomini_state_slot_rva==f::kJominiStateSlotRva&&owner.game_state_slot_rva==f::kGameStateSlotRva,"separate exact owner roots");
  f::ReadonlyObservation out{};
  {Fixture fixture;Require(Run(fixture,base,out)&&out.available&&out.offline_fixture&&!out.main_owner_observed,"actual production reader against explicit synthetic memory");
    Require(out.core.played_character_id==fixture.id&&out.core.clock.date_raw==53176992&&out.core.clock.speed==3,"signed full ID/date/speed");
    Require(out.raw_resources&&out.raw_resources->personal_gold_raw==-12345&&out.raw_resources->prestige_raw==222222&&out.raw_resources->piety_raw==333333&&out.raw_resources->stress_points==42,"atomic raw resources");}
  {Fixture fixture;fixture.drift=true;Require(Run(fixture,base,out)&&!out.available&&!out.raw_resources,"same-frame amount drift rejected");}
  {Fixture fixture;Put(fixture.actor,0x18,std::int32_t{-16777214});Require(Run(fixture,base,out)&&!out.available&&!out.raw_resources,"full generation mismatch denied");}
  {Fixture fixture;Put(fixture.jomini,0x20,std::uint8_t{0});Require(Run(fixture,base,out)&&!out.available&&!out.raw_resources,"running gameplay denied");}
  {Fixture fixture;Require(Run(fixture,base,out,false)&&!out.available&&!out.main_owner_observed&&fixture.calls==0,"offline seam cannot claim a real main owner");}
   if(synthetic)std::cout<<"PASS SOURCE_ONLY synthetic PE/Core/actor/resources/drift; EXE NOT_CHECKED; LIVE NOT_RUN\n";
   else std::cout<<"PASS exact26785313 disk SHA/PE windows; real Core reader synthetic signed-ID/resources/drift; legacy routing closed; no Game code executed; LIVE NOT_RUN\n";
  return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}
}
