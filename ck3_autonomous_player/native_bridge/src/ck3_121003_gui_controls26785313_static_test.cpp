#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
// Finite whole-unit fixture follows the existing BB3 body-inclusion pattern.
// Compile the actual unchanged Core and actual new implementation once.
#include "ck3_1210_core.cpp"
#include "ck3_121003_readonly26785313_v1.cpp"
#include "ck3_121003_core_route26785313_v1.cpp"
#include "ck3_121003_doctrine_key26785313_v1.cpp"
#include "xar_bridge/ck3_1210_adapter.hpp"
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
  void GuiImageWindows() {
#if defined(XAR_CK3_ENABLE_121003_26785313_GUI_WINDOW_V1)
    for(const auto&pin:f::GuiWindowImagePinsV1()) {
      if(input.is_open()) {
        bool copied=false;
        for(const auto&section:sections)if(pin.rva>=section.rva&&pin.rva-section.rva+pin.bytes.size()<=section.size) {
          input.seekg(static_cast<std::streamoff>(section.offset+pin.rva-section.rva));
          input.read(static_cast<char*>(image)+pin.rva,static_cast<std::streamsize>(pin.bytes.size()));
          Require(bool(input),"actual named-window file window");copied=true;break;
        }Require(copied,"current named-window windows file-backed");
      }else std::memcpy(static_cast<char*>(image)+pin.rva,pin.bytes.data(),pin.bytes.size());
    }
    const auto widget_col=reinterpret_cast<std::uintptr_t>(image)+0x58E23D8;
    std::memcpy(static_cast<char*>(image)+0x50BE758,&widget_col,sizeof(widget_col));
#endif

#if defined(XAR_CK3_ENABLE_121003_26785313_GUI_ROOT_INDEX_V1)
    for(const auto&pin:f::GuiRootIndexImagePinsV1()) {
      if(input.is_open()) {
        bool copied=false;
        for(const auto&section:sections)if(pin.rva>=section.rva&&pin.rva-section.rva+pin.bytes.size()<=section.size) {
          input.seekg(static_cast<std::streamoff>(section.offset+pin.rva-section.rva));
          input.read(static_cast<char*>(image)+pin.rva,static_cast<std::streamsize>(pin.bytes.size()));
          Require(bool(input),"actual GUI/RTTI file window");copied=true;break;
        }
        Require(copied,"all current GUI pins are file-backed");
      } else std::memcpy(static_cast<char*>(image)+pin.rva,pin.bytes.data(),pin.bytes.size());
    }
    // RAM-only explicit PE relocation of three COL pointer slots. Original
    // disk windows stay untouched; this creates no Game or live witness.
    for(const auto&type:f::gui_root_pins::kTypes) {
      const auto col=reinterpret_cast<std::uintptr_t>(image)+type.col_rva;
      std::memcpy(static_cast<char*>(image)+type.vtable_rva-sizeof(col),&col,sizeof(col));
    }
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_APPLICATION_EXIT_V1)
    for(const auto&pin:f::ApplicationExitImagePins267V1()) {
      if(input.is_open()) {
        bool copied=false;
        for(const auto&section:sections)if(pin.rva>=section.rva&&pin.rva-section.rva+pin.bytes.size()<=section.size) {
          input.seekg(static_cast<std::streamoff>(section.offset+pin.rva-section.rva));
          input.read(static_cast<char*>(image)+pin.rva,static_cast<std::streamsize>(pin.bytes.size()));
          Require(bool(input),"actual current quit body/RTTI file windows");copied=true;break;
        }
        Require(copied,"current exit pin file-backed");
      } else std::memcpy(static_cast<char*>(image)+pin.rva,pin.bytes.data(),pin.bytes.size());
    }
    const auto col=reinterpret_cast<std::uintptr_t>(image)+0x5162E58;
    std::memcpy(static_cast<char*>(image)+f::kGuiRootApplicationVtableRvaV1-sizeof(col),&col,sizeof(col));
#endif
  }
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
    put(pe+24,std::uint16_t{0x20B});put(pe+24+24,reinterpret_cast<std::uintptr_t>(image));
    put(pe+24+56,static_cast<std::uint32_t>(f::kImageSize));
    for(const auto&pin:f::ReadonlyImagePins())
      std::memcpy(static_cast<unsigned char*>(image)+pin.rva,pin.bytes.data(),pin.bytes.size());    GuiImageWindows();
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
    const auto loader_image_base=reinterpret_cast<std::uintptr_t>(image);std::memcpy(static_cast<char*>(image)+pe+24+24,&loader_image_base,8);
    for(const auto&pin:f::ReadonlyImagePins()){
      bool copied=false;
      for(const auto&section:sections)if(pin.rva>=section.rva&&pin.rva-section.rva+pin.bytes.size()<=section.size){
        input.seekg(static_cast<std::streamoff>(section.offset+pin.rva-section.rva));
        input.read(static_cast<char*>(image)+pin.rva,static_cast<std::streamsize>(pin.bytes.size()));Require(bool(input),"actual immutable code window");copied=true;break;}
      Require(copied,"all pins are actual file-backed windows");
    }
    GuiImageWindows();
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
  std::int32_t id=-16777215;std::uint32_t calls=0;bool drift=false,actor_drift=false;
  void (*second_read)(void*)=nullptr;void *second_read_context=nullptr;
  static Fixture *active;
  static void*Local(void*){auto&v=*active;++v.calls;if(v.calls==2&&v.second_read)v.second_read(v.second_read_context);if(v.drift&&v.calls==2)Put(v.living,0x100,std::int64_t{-12344});if(v.actor_drift&&v.calls==2)Put(v.actor,0x18,std::int32_t{-16777214});return v.player.data();}
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
bool Run(Fixture&fixture,std::uintptr_t image,f::ReadonlyObservation&out,bool offline=true,f::ReadonlyModeV1 mode=f::ReadonlyModeV1::core_and_raw_resources){
  m::MainThreadQueryMailboxV1 mailbox;mailbox.offline_fixture=offline;
  f::ReadonlyContext query;query.bindings=f::NoGameBindings(image,fixture.Core());query.mailbox=&mailbox;query.ticket.sequence=1;query.mode=mode;
  const bool ack=f::ExecuteReadonlyOnOwner(&query,{});out=query.observation;return ack;
}

#if defined(XAR_CK3_ENABLE_121003_26785313_GUI_ROOT_INDEX_V1)
struct GuiFixture {
  Fixture core;
  std::uintptr_t image;
  std::vector<unsigned char> first=std::vector<unsigned char>(0x60),context=std::vector<unsigned char>(1),
    entry=std::vector<unsigned char>(0x70),entry2=std::vector<unsigned char>(0x70);
  std::array<std::uintptr_t,2> entries{};
  explicit GuiFixture(std::uintptr_t base):image(base) {
    Put(core.players,0,base+f::kGuiRootApplicationVtableRvaV1);
    Put(core.players,0x1B8,first.data());Put(first,0x58,context.data());
    Set(base+f::kGuiRootManagerRvaV1,base+f::kGuiRootManagerVtableRvaV1);
    Set(base+f::kGuiRootManagerRvaV1+0x30,reinterpret_cast<std::uintptr_t>(entries.data()));
    Set(base+f::kGuiRootManagerRvaV1+0x38,std::int32_t{2});Set(base+f::kGuiRootManagerRvaV1+0x3C,std::int32_t{1});
    Put(entry,0,base+f::kGuiRootEntryVtableRvaV1);Put(entry,0x60,std::uintptr_t{1});Put(entry,0x68,context.data());
    Put(entry2,0,base+f::kGuiRootEntryVtableRvaV1);Put(entry2,0x60,std::uintptr_t{2});Put(entry2,0x68,context.data());
    entries={reinterpret_cast<std::uintptr_t>(entry.data()),reinterpret_cast<std::uintptr_t>(entry2.data())};
  }
  template<class T>void Set(std::uintptr_t a,T v){std::memcpy(reinterpret_cast<void*>(a),&v,sizeof(v));}
  f::GuiRootIndexRequestV1 Request(){
    f::GuiRootIndexRequestV1 r;r.connection_generation=7;r.deadline_unix_ms=static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count())+60000;r.expected_core.clock={53176992,3,true};
    r.expected_core.local_player_id=1;r.expected_core.map_ready=true;r.expected_core.has_played_character=true;
    r.expected_core.played_character_id=core.id;r.expected_core.played_character_alive=true;return r;
  }
  f::ReadonlyObservation Run(std::optional<f::GuiRootIndexRequestV1> request,bool offline=true) {
    m::MainThreadQueryMailboxV1 mailbox;mailbox.offline_fixture=offline;
    f::ReadonlyContext q;q.bindings=f::NoGameBindings(image,core.Core());q.mailbox=&mailbox;q.ticket.sequence=1;
    q.mode=f::ReadonlyModeV1::core_and_gui_root_index;q.gui_root_request=std::move(request);
    Require(f::ExecuteReadonlyOnOwner(&q,{}),"typed root executor ACK");return q.observation;
  }
};
void GuiCases(std::uintptr_t base) {
  Require(f::VerifyGuiRootIndexImageV1(base),"current GUI code+RTTI+COL slot guards");
  {GuiFixture g(base);const auto out=g.Run(g.Request());
   Require(out.available&&out.offline_fixture&&!out.main_owner_observed&&!out.raw_resources&&out.gui_root_index,"root mode is explicit partial NoGame data");
   const auto &v=*out.gui_root_index;
   Require(v.context==reinterpret_cast<std::uintptr_t>(g.context.data())&&v.entries.size()==1&&v.entries[0].widget==1&&
       v.connection_generation==7&&v.ticket_sequence==1,"bounded index preserves opaque root identity without dereferencing widget1");
   Require(!f::CoreRouteObservationV1(out).core_available,"offline root witness is not live Core");
   auto data=out;data.offline_fixture=false;data.main_owner_observed=true;
   Require(!f::CoreRouteObservationV1(data).core_available,"root-bearing data cannot masquerade as Core-only mode1");}
  {GuiFixture g(base);Require(!g.Run(std::nullopt).available,"missing trusted Core occurrence denied");}
  {GuiFixture g(base);auto r=g.Request();r.deadline_unix_ms=1;Require(!g.Run(r).available,"expired root query denied");}
  {GuiFixture g(base);auto r=g.Request();r.connection_generation=0;Require(!g.Run(r).available,"missing connection identity denied");}
  {GuiFixture g(base);auto r=g.Request();++r.expected_core.clock.date_raw;Require(!g.Run(r).available,"stale expected Core date denied");}
  {GuiFixture g(base);auto r=g.Request();++r.expected_core.played_character_id;Require(!g.Run(r).available,"changed full actor generation denied");}
  {GuiFixture g(base);Put(g.core.jomini,0x20,std::uint8_t{0});Require(!g.Run(g.Request()).available,"unpaused root read denied");}
  {GuiFixture g(base);const auto out=g.Run(g.Request(),false);Require(!out.available&&!out.main_owner_observed&&g.core.calls==0,"fixture cannot forge live owner/executor admission");}
  {GuiFixture g(base);Put(g.core.players,0,base+0x4AFA620);Require(!g.Run(g.Request()).available,"old application vtable denied");}
  {GuiFixture g(base);g.Set(base+f::kGuiRootManagerRvaV1,base+0x507D570);Require(!g.Run(g.Request()).available,"old manager vtable denied");}
  {GuiFixture g(base);Put(g.entry,0,base+0x507D550);Require(!g.Run(g.Request()).available,"old entry vtable denied");}
  {GuiFixture g(base);Put(g.entry,0x68,std::uintptr_t{1});Require(!g.Run(g.Request()).available,"foreign context denied");}
  {GuiFixture g(base);g.Set(base+f::kGuiRootManagerRvaV1+0x3C,std::int32_t{4097});g.Set(base+f::kGuiRootManagerRvaV1+0x38,std::int32_t{4097});Require(!g.Run(g.Request()).available,"count bound before allocation/dereference");}
  {GuiFixture g(base);g.Set(base+f::kGuiRootManagerRvaV1+0x3C,std::int32_t{-1});Require(!g.Run(g.Request()).available,"negative count denied");}
  {GuiFixture g(base);g.Set(base+f::kGuiRootManagerRvaV1+0x38,std::int32_t{0});Require(!g.Run(g.Request()).available,"capacity below count denied");}
  {GuiFixture g(base);g.Set(base+f::kGuiRootManagerRvaV1+0x30,std::uintptr_t{0});Require(!g.Run(g.Request()).available,"missing nonempty vector denied");}
  {GuiFixture g(base);g.entries[0]=1;Require(!g.Run(g.Request()).available,"invalid entry memory is typed unavailable");}
  {GuiFixture g(base);g.entries[1]=g.entries[0];g.Set(base+f::kGuiRootManagerRvaV1+0x3C,std::int32_t{2});Require(!g.Run(g.Request()).available,"duplicate entry denied");}
  {GuiFixture g(base);Put(g.entry2,0x60,std::uintptr_t{1});g.Set(base+f::kGuiRootManagerRvaV1+0x3C,std::int32_t{2});Require(!g.Run(g.Request()).available,"duplicate materialized root denied");}
  {GuiFixture g(base);Put(g.entry,0x60,std::uintptr_t{0});const auto out=g.Run(g.Request());Require(out.available&&out.gui_root_index->entries[0].widget==0,"unmaterialized entry is explicitly retained");}
  {GuiFixture g(base);g.Set(base+f::kGuiRootManagerRvaV1+0x3C,std::int32_t{0});g.Set(base+f::kGuiRootManagerRvaV1+0x30,std::uintptr_t{0});const auto out=g.Run(g.Request());Require(out.available&&out.gui_root_index->entries.empty(),"empty root index is not GUI complete");}
  {GuiFixture g(base);g.core.second_read_context=&g;g.core.second_read=[](void*ctx){auto&v=*static_cast<GuiFixture*>(ctx);Put(v.entry,0x60,std::uintptr_t{3});};const auto out=g.Run(g.Request());Require(!out.available&&!out.gui_root_index,"second Core sample root drift denied with no partial payload");}
  {GuiFixture g(base);g.core.actor_drift=true;Require(!g.Run(g.Request()).available,"same-frame actor drift rejects root witness");}
  {GuiFixture g(base);Put(g.core.actor,0x1B0,std::uintptr_t{1});Require(g.Run(g.Request()).available,"root mode never dereferences financial living storage");}
  {auto *pin=reinterpret_cast<unsigned char*>(base+f::GuiRootIndexImagePinsV1()[0].rva);*pin^=1;
   {GuiFixture g(base);Require(!g.Run(g.Request()).available,"tampered current GUI code denied");}
   {Fixture fixture;f::ReadonlyObservation out;Require(Run(fixture,base,out,true,f::ReadonlyModeV1::core_only)&&out.available&&!out.gui_root_index,"mode1 independent from root code and never reads roots");}
   *pin^=1;Require(f::VerifyGuiRootIndexImageV1(base),"RAM-only current code restored");}
  {const auto&type=f::gui_root_pins::kTypes[0];auto *slot=reinterpret_cast<std::uintptr_t*>(base+type.vtable_rva-sizeof(std::uintptr_t));const auto original=*slot;*slot=original+1;Require(!f::VerifyGuiRootIndexImageV1(base),"wrong RTTI COL binding denied");*slot=original;}
}
#endif


#if defined(XAR_CK3_ENABLE_121003_26785313_GUI_WINDOW_V1)
struct WindowFixture {
 Fixture core;std::uintptr_t image;
 std::vector<unsigned char> first=std::vector<unsigned char>(0x60),context=std::vector<unsigned char>(0xE0),
  root=std::vector<unsigned char>(0x1D8),window=std::vector<unsigned char>(0x1D8),button=std::vector<unsigned char>(0x1D8),other=std::vector<unsigned char>(0x1D8);
 std::array<std::uintptr_t,2> roots{},children{};std::string long_name="rite_creation_window";
 explicit WindowFixture(std::uintptr_t base):image(base) {
  Put(core.players,0,base+f::kGuiRootApplicationVtableRvaV1);Put(core.players,0x1B8,first.data());Put(first,0x58,context.data());Put(context,0xD0,root.data());
  Init(root,0,"");Init(window,reinterpret_cast<std::uintptr_t>(root.data()),long_name);Init(button,reinterpret_cast<std::uintptr_t>(window.data()),"confirm");Init(other,reinterpret_cast<std::uintptr_t>(window.data()),"cancel");
  roots[0]=reinterpret_cast<std::uintptr_t>(window.data());children={reinterpret_cast<std::uintptr_t>(button.data()),reinterpret_cast<std::uintptr_t>(other.data())};
  Put(root,0xF0,roots.data());Put(root,0xF8,std::int32_t{2});Put(root,0xFC,std::int32_t{1});Put(window,0xF0,children.data());Put(window,0xF8,std::int32_t{2});Put(window,0xFC,std::int32_t{2});
 }
 void Init(std::vector<unsigned char>&n,std::uintptr_t parent,const std::string&name) {
  Put(n,0,image+0x50BE760);Put(n,0xD8,context.data());Put(n,0xE8,parent);Put(n,0x1C8,static_cast<std::uint64_t>(name.size()));
  if(name.size()>15){Put(n,0x1B8,name.data());Put(n,0x1D0,std::uint64_t{31});}
  else{std::memcpy(n.data()+0x1B8,name.c_str(),name.size()+1);Put(n,0x1D0,std::uint64_t{15});}
 }
 f::GuiWindowRequestV1 Request(){f::GuiWindowRequestV1 r;r.window_name=long_name;r.connection_generation=7;r.deadline_unix_ms=4102444800000;
  r.expected_core.clock={53176992,3,true};r.expected_core.local_player_id=1;r.expected_core.map_ready=true;r.expected_core.has_played_character=true;r.expected_core.played_character_id=core.id;r.expected_core.played_character_alive=true;return r;}
 f::ReadonlyObservation Run(std::optional<f::GuiWindowRequestV1> r,bool offline=true) {
  m::MainThreadQueryMailboxV1 mailbox;mailbox.offline_fixture=offline;f::ReadonlyContext q;q.bindings=f::NoGameBindings(image,core.Core());q.mailbox=&mailbox;q.ticket.sequence=1;
  q.mode=f::ReadonlyModeV1::core_and_gui_window;q.gui_window_request=std::move(r);Require(f::ExecuteReadonlyOnOwner(&q,{}),"tree typed executor ACK");return q.observation;
 }
};
void WindowCases(std::uintptr_t base) {
 Require(f::VerifyGuiWindowImageV1(base),"current constructor/flag propagation/root traversal/RTTI pins");
 {WindowFixture g(base);const auto o=g.Run(g.Request());Require(o.available&&o.offline_fixture&&!o.main_owner_observed&&!o.raw_resources&&!o.gui_root_index&&o.gui_window&&o.gui_window->window_found,"named global-root tree is synthetic readonly only");
  const auto&w=*o.gui_window;Require(w.top_level.size()==1&&w.tree.size()==3&&w.tree[1].name=="confirm"&&w.tree[1].parent_index==0&&w.tree[1].visible&&w.tree[1].enabled,"current SSO/heap names and parent/child layout");
  auto forged=o;forged.offline_fixture=false;forged.main_owner_observed=true;Require(!f::CoreRouteObservationV1(forged).core_available,"tree-bearing observation cannot masquerade as mode1 Core");}
 {WindowFixture g(base);Put(g.root,0xD0,std::uint8_t{20});const auto o=g.Run(g.Request());Require(o.available&&!o.gui_window->top_level[0].visible&&!o.gui_window->top_level[0].enabled&&!o.gui_window->tree[1].visible&&!o.gui_window->tree[1].enabled,"global-root forced hidden/disabled propagates conservatively");}
 for(const std::uint8_t flags:{std::uint8_t{2},std::uint8_t{4},std::uint8_t{6}}){WindowFixture g(base);Put(g.button,0xD0,flags);const auto o=g.Run(g.Request());Require(o.available&&!o.gui_window->tree[1].enabled&&o.gui_window->tree[1].visible,"local/effective disabled bits independent");}
 for(const std::uint8_t flags:{std::uint8_t{8},std::uint8_t{16},std::uint8_t{24}}){WindowFixture g(base);Put(g.window,0xD0,flags);const auto o=g.Run(g.Request());Require(o.available&&!o.gui_window->tree[0].visible&&!o.gui_window->tree[1].visible,"local/effective hidden plus inherited false");}
 {WindowFixture g(base);auto r=g.Request();r.window_name="absent_window";const auto o=g.Run(r);Require(o.available&&!o.gui_window->window_found&&o.gui_window->tree.empty()&&o.gui_window->top_level.size()==1,"missing exact named window explicit, not root-count GuiReady");}
 {WindowFixture g(base);Require(!g.Run(std::nullopt).available,"missing Core occurrence refused");}
 {WindowFixture g(base);auto r=g.Request();r.deadline_unix_ms=1;Require(!g.Run(r).available,"expired read refused");}
 {WindowFixture g(base);auto r=g.Request();r.connection_generation=0;Require(!g.Run(r).available,"generation absent refused");}
 {WindowFixture g(base);auto r=g.Request();++r.expected_core.clock.date_raw;Require(!g.Run(r).available,"stale Core refused");}
 {WindowFixture g(base);Put(g.core.jomini,0x20,std::uint8_t{0});Require(!g.Run(g.Request()).available,"unpaused refused");}
 {WindowFixture g(base);Require(!g.Run(g.Request(),false).available&&g.core.calls==0,"synthetic pointer cannot forge owner");}
 {WindowFixture g(base);Put(g.button,0xD8,std::uintptr_t{1});Require(!g.Run(g.Request()).available,"foreign context refused");}
 {WindowFixture g(base);Put(g.button,0xE8,std::uintptr_t{0});Require(!g.Run(g.Request()).available,"parent linkage refused");}
 {WindowFixture g(base);g.children[0]=reinterpret_cast<std::uintptr_t>(g.window.data());Require(!g.Run(g.Request()).available,"cycle refused");}
 {WindowFixture g(base);g.children[1]=g.children[0];Require(!g.Run(g.Request()).available,"duplicate child refused");}
 {WindowFixture g(base);g.roots[1]=g.roots[0];Put(g.root,0xFC,std::int32_t{2});Require(!g.Run(g.Request()).available,"ambiguous/duplicate root refused");}
 {WindowFixture g(base);Put(g.button,0,std::uintptr_t{1});Require(!g.Run(g.Request()).available,"non-image vtable refused");}
 {WindowFixture g(base);Put(g.window,0xFC,std::int32_t{4097});Put(g.window,0xF8,std::int32_t{4097});Require(!g.Run(g.Request()).available,"child count bounded");}
 {WindowFixture g(base);Put(g.window,0xF8,std::int32_t{1});Require(!g.Run(g.Request()).available,"invalid capacity refused");}
 {WindowFixture g(base);Put(g.button,0x1C8,std::uint64_t{193});Require(!g.Run(g.Request()).available,"name allocation bounded");}
 {WindowFixture g(base);Put(g.button,0x1B8,std::uint8_t{0xFF});Require(!g.Run(g.Request()).available,"invalid UTF8 refused");}
 {WindowFixture g(base);Put(g.button,0xD0,std::uint8_t{1});Require(!g.Run(g.Request()).available,"released widget refused");}
 {WindowFixture g(base);g.core.second_read_context=&g;g.core.second_read=[](void*p){Put(static_cast<WindowFixture*>(p)->button,0xD0,std::uint8_t{4});};Require(!g.Run(g.Request()).available,"second sample name/flags/tree drift refused");}
 {WindowFixture g(base);g.core.actor_drift=true;Require(!g.Run(g.Request()).available,"same-frame actor drift refused");}
 {WindowFixture g(base);Put(g.core.actor,0x1B0,std::uintptr_t{1});Require(g.Run(g.Request()).available,"window mode never reads raw living storage");}
 {auto*p=reinterpret_cast<unsigned char*>(base+f::GuiWindowImagePinsV1()[0].rva);*p^=1;{WindowFixture g(base);Require(!g.Run(g.Request()).available,"pin mutation refused");}*p^=1;}
}
#endif

}

#include "ck3_121003_gui_controls26785313_v2.cpp"
#include "ck3_1210_gui_control_v1.cpp"
namespace {
void ControlsPins(PeWindows &pe){
 std::vector<f::ImagePin> pins;for(const auto&pin:f::GuiControlImagePins267V2())pins.push_back(pin);
 for(const auto&pin:f::RiteDraftImagePinsV2())pins.push_back(pin);
 for(const auto &pin:pins){
  if(pe.input.is_open()){bool found=false;
   for(const auto&sec:pe.sections)if(pin.rva>=sec.rva&&pin.rva-sec.rva+pin.bytes.size()<=sec.size){
    pe.input.seekg(static_cast<std::streamoff>(sec.offset+pin.rva-sec.rva));pe.input.read(static_cast<char*>(pe.image)+pin.rva,static_cast<std::streamsize>(pin.bytes.size()));Require(bool(pe.input),"actual controls immutable file window");found=true;break;
   }Require(found,"controls source window is file backed");
  }else std::memcpy(static_cast<char*>(pe.image)+pin.rva,pin.bytes.data(),pin.bytes.size());
 }
 const auto base=reinterpret_cast<std::uintptr_t>(pe.image);
 for(const auto&type:f::rite_draft_pins::kTypes){const auto col=base+type.col;std::memcpy(static_cast<char*>(pe.image)+type.vtable-8,&col,8);}
 for(const auto [slot,rva]:std::array<std::pair<std::uintptr_t,std::uintptr_t>,2>{{{0x50BFE48-8,0x58E4738},{0x50BFE48+16,0x406FFF0}}}){
  if(pe.input.is_open()){bool found=false;for(const auto&sec:pe.sections)if(slot>=sec.rva&&slot-sec.rva+8<=sec.size){
   const auto actual=pe.At<std::uint64_t>(sec.offset+slot-sec.rva);Require(actual==0x140000000ULL+rva,"actual callback COL/invoke raw preferred-base pointer");found=true;break;
  }Require(found,"current callback pointer file-backed");}
  const auto value=base+rva;std::memcpy(static_cast<char*>(pe.image)+slot,&value,8);
 }
}
struct ControlsFixture {
 WindowFixture window;
 std::vector<unsigned char> host=std::vector<unsigned char>(16),manager=std::vector<unsigned char>(16),
  callback=std::vector<unsigned char>(0xF8),binding=std::vector<unsigned char>(0x48);
 std::vector<unsigned char> gfx=std::vector<unsigned char>(0x90),handler=std::vector<unsigned char>(0x280),controller=std::vector<unsigned char>(0x8C0);
 explicit ControlsFixture(std::uintptr_t base):window(base){auto&g=window;
  Put(g.core.jomini,0,base+0x4B45FE0);Put(g.core.jomini,0x10,gfx.data());
  Put(gfx,0,base+0x4B24748);Put(gfx,0x20,g.core.jomini.data());Put(gfx,0x88,handler.data());
  Put(handler,0,base+0x4B22578);Put(handler,0x58,base+0x4B22558);Put(handler,0x278,controller.data());
  Put(controller,0,base+0x4C09438);Put(controller,0x10,base+0x4C09410);Put(controller,0x60,g.window.data());
  Put(controller,0x98,g.core.jomini.data());Put(controller,0xA0,handler.data());Put(controller,0xC8,std::uint32_t{152});Put(controller,0xCC,g.core.id);
  g.context.resize(0x400);g.button.resize(0x500);
  Put(g.first,0x58,g.context.data());Put(g.context,0xD0,g.root.data());
  for(auto*p:{&g.root,&g.window,&g.button,&g.other})Put(*p,0xD8,g.context.data());
  g.children[0]=reinterpret_cast<std::uintptr_t>(g.button.data());
  Put(g.context,0x3D8,host.data());Put(host,8,g.context.data());Put(g.context,0x3E8,manager.data());Put(manager,0,g.context.data());
  Put(g.button,0x4B8,binding.data());Put(g.button,0x4C0,std::int32_t{1});Put(g.button,0x4C4,std::int32_t{1});
  Put(binding,0x40,callback.data());Put(callback,0,base+0x50BFE48);Put(callback,8,base+0x406E560);Put(callback,0xF0,g.button.data());
  // Explicit SYNTHETIC DATA: only this fake button receives an isolated
  // primary Widget-COL vtable with the current input slot. Never mutate the
  // shared base Widget table and accidentally turn every fixture node into a button.
  constexpr std::uintptr_t shadow=0x50BE900;const auto col=base+0x58E23D8,input=base+0x406DB30;
  std::memcpy(reinterpret_cast<void*>(base+shadow-8),&col,8);
  std::memcpy(reinterpret_cast<void*>(base+shadow+13*8),&input,8);Put(g.button,0,base+shadow);
 }
 f::GuiWindowV1 Frame(){auto o=window.Run(window.Request());Require(o.available&&o.offline_fixture&&o.gui_window,"current real window reader only against explicit NoGame memory");auto frame=*o.gui_window;
  // Nonzero witness shape is synthetic DATA, never a real owner assertion.
  frame.pump_epoch=23;frame.owner_thread_id=42;return frame;}
 bool Capture(c::GuiControlCaptureV1 &capture,std::string &reason){return f::CaptureGuiControlWindow267V2(f::BindGuiControlImage267V2(window.image,f::kExecutableSha256),Frame(),capture,reason);}
};
void ControlsCases(std::uintptr_t base){
 {ControlsFixture g(base);f::GuiControlsRiteSource267V2 source;auto frame=g.Frame();const auto b=f::BindGuiControlImage267V2(base,f::kExecutableSha256);
  Require(f::ReadControlsRiteSource267V2(b,frame,152,g.window.core.id,source)&&source.source_rite_id==152,"current exact controller/handler/gfx/root/actor/source Rite provenance");
  Put(g.controller,0xC8,std::uint32_t{153});Require(!f::ReadControlsRiteSource267V2(b,frame,152,g.window.core.id,source),"Core and button unchanged but source Rite153 must be denied");
  Put(g.controller,0xC8,std::uint32_t{152});Put(g.controller,0xCC,std::int32_t{-16777214});Require(!f::ReadControlsRiteSource267V2(b,frame,152,g.window.core.id,source),"controller actor generation drift denied");
 }
 Require(f::VerifyGuiControlImage267V2(base),"current code/host/shortcut/typed callback pins verified");
 {ControlsFixture g(base);c::GuiControlCaptureV1 capture;std::string reason;Require(g.Capture(capture,reason)&&capture.widgets.size()==3&&capture.widgets[1].row.clickable&&!capture.complete,"current capture actual source complete rows but no owner token/cap/action inferred");
  Require(capture.widgets[1].callbacks.size()==1&&capture.widgets[1].callbacks[0].native_source.size()==0xF8,"exact typed expression object source retained privately");}
 {ControlsFixture g(base);Put(g.host,8,std::uintptr_t{1});c::GuiControlCaptureV1 capture;std::string reason;Require(!g.Capture(capture,reason),"host backref denied");}
 {ControlsFixture g(base);Put(g.manager,0,std::uintptr_t{1});c::GuiControlCaptureV1 capture;std::string reason;Require(!g.Capture(capture,reason),"shortcut manager backref denied");}
 {ControlsFixture g(base);Put(g.window.button,0xD0,std::uint8_t{4});c::GuiControlCaptureV1 capture;std::string reason;Require(g.Capture(capture,reason)&&!capture.widgets[1].row.clickable,"disabled native button cannot be issued as clickable");}
 {ControlsFixture g(base);Put(g.callback,0,base+0x50D44A0);const auto invoke=base+0x406FFF0;std::memcpy(reinterpret_cast<void*>(base+0x50D44A0+16),&invoke,8);c::GuiControlCaptureV1 capture;std::string reason;Require(g.Capture(capture,reason)&&!capture.widgets[1].row.clickable,"second Widget binder with same leaf is not ButtonBase capability");}
 {ControlsFixture g(base);Put(g.callback,0x1C,std::int32_t{65});c::GuiControlCaptureV1 capture;std::string reason;Require(!g.Capture(capture,reason),"native expression vectors bounded before allocation");}
 {ControlsFixture g(base);Put(g.binding,0x40,std::uintptr_t{1});c::GuiControlCaptureV1 capture;std::string reason;Require(!g.Capture(capture,reason),"unreadable callback object denied without any invocation");}
 {auto*p=reinterpret_cast<unsigned char*>(base+f::GuiControlImagePins267V2()[0].rva);*p^=1;Require(!f::VerifyGuiControlImage267V2(base),"tampered code pin rejected");*p^=1;}
 {ControlsFixture g(base);const auto env=f::BindCoreRouteMailboxEnvironmentV1(base,f::kExecutableSha256);Require(env.permitted_executor==&f::ExecuteReadonlyOnOwner&&env.permitted_executor_tertiary==&f::ExecuteGuiControlsOnOwner267V2,"fixed tertiary current executor; readonly still primary");
  f::GuiControlsSession267V2 session;session.provider.valid=true;m::MainThreadQueryMailboxV1 mailbox;mailbox.offline_fixture=true;
  f::GuiControlsContext267V2 q;q.session=&session;q.mailbox=&mailbox;q.control.activate=true;q.request=g.window.Request();f::ArmGuiControlsDeadline267V2(q);
  Require(f::ExecuteGuiControlsOnOwner267V2(&q,{})&&!q.result.effect_attempted&&!session.provider.valid&&!q.core_before_verified,"NoGame mailbox cannot claim actual owner or dispatch any function");}
}
}

void DoctrineKeyPins(PeWindows&pe) {
 for(const auto&pin:f::DoctrineKeyImagePins267V1()) {
  if(pe.input.is_open()) {
   bool found=false;for(const auto&sec:pe.sections)if(pin.rva>=sec.rva&&pin.rva-sec.rva+pin.bytes.size()<=sec.size) {
    pe.input.seekg(static_cast<std::streamoff>(sec.offset+pin.rva-sec.rva));
    pe.input.read(static_cast<char*>(pe.image)+pin.rva,static_cast<std::streamsize>(pin.bytes.size()));
    Require(bool(pe.input),"actual doctrine key code/metadata file window");found=true;break;
   }Require(found,"doctrine key pins actual file-backed");
  }else std::memcpy(static_cast<char*>(pe.image)+pin.rva,pin.bytes.data(),pin.bytes.size());
 }
 for(const auto&pin:f::doctrine_key_pins267_v1::kPointers) {
  if(pe.input.is_open()) {
   bool found=false;for(const auto&sec:pe.sections)if(pin.slot>=sec.rva&&pin.slot-sec.rva+8<=sec.size) {
    Require(pe.At<std::uint64_t>(sec.offset+pin.slot-sec.rva)==0x140000000ULL+pin.target,"actual doctrine pointer raw preferred VA");found=true;break;
   }Require(found,"doctrine pointer actual file-backed");
  }
  const auto value=reinterpret_cast<std::uintptr_t>(pe.image)+pin.target;
  std::memcpy(static_cast<char*>(pe.image)+pin.slot,&value,8);
 }
}
void DoctrineKeyCases(std::uintptr_t image) {
 Require(f::VerifyDoctrineKeyImage267V1(image),"independent current doctrine ABI/code/RTTI/relocation pins");
 const auto binding=f::BindReadonlyImage(image,f::kExecutableSha256);
 const auto check=[&](std::string key,bool heap) {
  std::vector<unsigned char> object(0x3C),data(key.begin(),key.end());data.push_back(0);
  Put(object,0,image+0x5012530);Put(object,8,image+0x4FC61A0);Put(object,0x10,std::uint32_t{42});
  Put(object,0x14,std::uint32_t{0x13579BDF});Put(object,0x38,std::uint32_t{0x4744624F});
  Put(object,0x28,static_cast<std::uint64_t>(key.size()));Put(object,0x30,std::uint64_t{heap?31U:15U});
  if(heap)Put(object,0x18,data.data());else std::memcpy(object.data()+0x18,data.data(),data.size());
  f::DoctrineInternalKey267V1 got;std::string reason;
  const auto read=[&](){return f::ReadSDoctrineInternalKey267V1(binding,reinterpret_cast<std::uintptr_t>(object.data()),got,reason);};
  Require(read()&&got.exact_bytes==key&&got.database_index==42&&got.stored_identifier_hash==0x13579BDF,"exact raw internal key from native CString layout; not a runtime row identity");
  auto original=object;
  Put(object,0x38,std::uint32_t{0x4E756C6C});Require(!read()&&got.exact_bytes.empty(),"null object marker denied");object=original;
  Put(object,0,image+0x4FC6D70);Require(!read(),"null doctrine primary vptr denied");object=original;
  Put(object,8,image+0x4FC61A8);Require(!read(),"wrong vbptr denied");object=original;
  Put(object,0x10,std::uint32_t{0xFFFFFFFF});Require(!read(),"null index denied");object=original;
  Put(object,0x28,std::uint64_t{257});Require(!read(),"explicit observation ceiling denied");object=original;
  Put(object,0x30,std::uint64_t{14});Require(!read(),"unqualified CString capacity denied");object=original;
  Put(object,0x30,std::uint64_t{0});Require(!read(),"length exceeds capacity denied");object=original;
  if(heap) {Put(object,0x18,std::uintptr_t{1});Require(!read(),"unreadable heap pointer denied");object=original;
   data.back()='x';Require(!read(),"missing trailing NUL denied");data.back()=0;
   data[1]=0;Require(!read(),"embedded NUL denied");data[1]=key[1];}
  auto bad=binding;bad.exact_image_admitted=false;
  Require(!f::ReadSDoctrineInternalKey267V1(bad,reinterpret_cast<std::uintptr_t>(object.data()),got,reason),"missing current binding denied");
 };
 check("des_doctrine_dynastic",true);check("inline_key",false);
 const auto &pin=f::DoctrineKeyImagePins267V1().front();auto*byte=reinterpret_cast<unsigned char*>(image+pin.rva);
 *byte^=1;Require(!f::VerifyDoctrineKeyImage267V1(image),"tampered current code denied");*byte^=1;
}


void RiteDoctrineItemsPins(PeWindows&pe) {
 for(const auto&pin:f::RiteDoctrineItemsImagePins267V1()) {
  if(pe.input.is_open()) {
   bool found=false;for(const auto&sec:pe.sections)if(pin.rva>=sec.rva&&pin.rva-sec.rva+pin.bytes.size()<=sec.size) {
    pe.input.seekg(static_cast<std::streamoff>(sec.offset+pin.rva-sec.rva));pe.input.read(static_cast<char*>(pe.image)+pin.rva,static_cast<std::streamsize>(pin.bytes.size()));
    Require(bool(pe.input),"actual Rite typed value-array code window");found=true;break;
   }Require(found,"typed list code window file-backed");
  }else std::memcpy(static_cast<char*>(pe.image)+pin.rva,pin.bytes.data(),pin.bytes.size());
 }
 for(const auto&pin:f::rite_doctrine_items_pins267_v1::kPointers) {
  if(pe.input.is_open()) {
   bool found=false;for(const auto&sec:pe.sections)if(pin.slot>=sec.rva&&pin.slot-sec.rva+8<=sec.size) {
    Require(pe.At<std::uint64_t>(sec.offset+pin.slot-sec.rva)==0x140000000ULL+pin.target,"actual typed list pointer preferredVA");found=true;break;
   }Require(found,"typed list pointer file-backed");
  }
  const auto value=reinterpret_cast<std::uintptr_t>(pe.image)+pin.target;std::memcpy(static_cast<char*>(pe.image)+pin.slot,&value,8);
 }
}
void RiteDoctrineItemsCases(std::uintptr_t image) {
 Require(f::VerifyRiteDoctrineItemsImage267V1(image),"exact typed array code/model class/ASLR pins");
 ControlsFixture g(image);const auto binding=f::BindReadonlyImage(image,f::kExecutableSha256);
 f::RiteDoctrineItems267V1 observed;std::string reason;
 const auto read=[&](){return f::ReadRiteDoctrineItems267V1(binding,reinterpret_cast<std::uintptr_t>(g.controller.data()),observed,reason);};
 Require(read()&&observed.values.empty(),"unopened category is an actual empty list, no target presence inferred");
 std::vector<unsigned char> items(0x90),one(0x3C),two(0x3C);std::string key1="des_doctrine_none",key2="des_doctrine_dynastic";
 const auto setup=[&](std::vector<unsigned char>&d,const std::string&key,std::uint32_t index){
  Put(d,0,image+0x5012530);Put(d,8,image+0x4FC61A0);Put(d,0x10,index);Put(d,0x14,index+17);Put(d,0x18,key.c_str());Put(d,0x28,static_cast<std::uint64_t>(key.size()));Put(d,0x30,std::uint64_t{31});Put(d,0x38,std::uint32_t{0x4744624F});};
 setup(one,key1,42);setup(two,key2,43);Put(items,0x28,one.data());Put(items,0x48+0x28,two.data());
 Put(g.controller,0x8B0,items.data());Put(g.controller,0x8B8,std::int32_t{2});Put(g.controller,0x8BC,std::int32_t{2});
 Require(read()&&observed.values.size()==2&&observed.values[0].key.exact_bytes==key1&&observed.values[1].key.exact_bytes==key2,"actual typed value-array stride48h, item+28, complete native key");
 const auto *selected=f::FindUniqueRiteDoctrineKey267V1(observed,key2);Require(selected&&selected->item==reinterpret_cast<std::uintptr_t>(items.data()+0x48),"unique semantic key is independent from ordinal convention");
 Require(!f::FindUniqueRiteDoctrineKey267V1(observed,"absent"),"missing key unavailable");
 f::GuiControlsRiteSource267V2 snapshot;
 Require(f::ReadControlsRiteSource267V2(f::BindGuiControlImage267V2(image,f::kExecutableSha256),g.Frame(),152,g.window.core.id,snapshot)&&snapshot.doctrine_items==observed,"actual existing Rite source reader consumes typed array, not unused helper");
 const auto earlier=snapshot;
 Put(items,0x28,two.data());Require(read()&&!f::FindUniqueRiteDoctrineKey267V1(observed,key2),"duplicate exact key unavailable, never choose ordinal fallback");
 Require(f::ReadControlsRiteSource267V2(f::BindGuiControlImage267V2(image,f::kExecutableSha256),g.Frame(),152,g.window.core.id,snapshot)&&snapshot!=earlier,"private query source identity includes typed list drift");Put(items,0x28,one.data());
 Put(g.controller,0x8BC,std::int32_t{-1});Require(!read()&&observed.values.empty(),"negative native model count denied");
 Put(g.controller,0x8BC,std::int32_t{257});Require(!read(),"bounded observer list ceiling denied");Put(g.controller,0x8BC,std::int32_t{2});
 Put(g.controller,0x8B0,std::uintptr_t{1});Require(!read(),"unreadable native array denied");Put(g.controller,0x8B0,items.data());
 Put(g.controller,0,image+0x4C09440);Require(!read(),"wrong actual controller class denied");Put(g.controller,0,image+0x4C09438);
 Put(items,0x48+0x28,std::uintptr_t{1});Require(!read(),"unreadable per-item doctrine denied, no partial/truncated list offered");Put(items,0x48+0x28,two.data());
 Require(read()&&observed.values.size()==2,"correct typed list restored");
 const auto&pin=f::RiteDoctrineItemsImagePins267V1().front();auto*byte=reinterpret_cast<unsigned char*>(image+pin.rva);*byte^=1;
 Require(!f::VerifyRiteDoctrineItemsImage267V1(image),"tampered typed array code denied");*byte^=1;
}


void LiteralNavigationCases() {
 const auto row=[](std::uintptr_t ptr,std::uintptr_t parent,const char*name,bool clickable) {
  c::GuiControlIdentityV1 r;r.widget=ptr;r.parent=parent;r.row.runtime_name=name;
  r.row.clickable=clickable;r.row.enabled=true;r.row.effective_visible=true;return r;
 };
 c::GuiControlCaptureV1 hud;hud.root_name="bottom";
 hud.widgets={row(1,0,"bottom",false),row(2,1,"bottom_bar",false),row(3,2,"side_bottom_left_tabs",false),
  row(4,3,"left_edge_buttons",false),row(5,4,"faith_button_container",false),row(6,5,"faith_button",true),row(7,1,"other",true)};
 f::RestrictNavigationRows267V2(hud);Require(hud.widgets[5].row.clickable&&!hud.widgets[6].row.clickable,"only actual bottom ancestry faith callback is admissible");
 auto wrong=hud;wrong.widgets[4].row.runtime_name="other_container";
 f::RestrictNavigationRows267V2(wrong);Require(!wrong.widgets[5].row.clickable,"same button name under wrong ancestor refused");
 auto wrong_outer=hud;wrong_outer.widgets[1].row.runtime_name="other_bar";
 f::RestrictNavigationRows267V2(wrong_outer);Require(!wrong_outer.widgets[5].row.clickable,"actual bottom_bar ancestor required");
 auto duplicate=hud;duplicate.widgets.push_back(row(8,5,"faith_button",true));
 f::RestrictNavigationRows267V2(duplicate);Require(!duplicate.widgets[5].row.clickable&&!duplicate.widgets[7].row.clickable,"duplicate literal targets refuse all, no ordinal selection");
 auto obsolete=hud;obsolete.root_name="hud_layer";obsolete.widgets[0].row.runtime_name="hud_layer";
 f::RestrictNavigationRows267V2(obsolete);Require(!obsolete.widgets[5].row.clickable,"historical HUD query never grants OPEN_FAITH");
 c::GuiControlCaptureV1 faith;faith.root_name="faith_window";
 faith.widgets={row(1,0,"faith_window",false),row(2,1,"",false),row(3,2,"tab_beliefs",false),row(4,3,"",false),row(5,4,"actions",false),row(6,5,"edit_rite",true),row(7,5,"edit_faith",true)};
 f::RestrictNavigationRows267V2(faith);Require(faith.widgets[5].row.clickable&&!faith.widgets[6].row.clickable,"only exact Faith actions/tab_beliefs edit_rite is admissible");
 auto broken=faith;broken.widgets[5].parent=99;f::RestrictNavigationRows267V2(broken);Require(!broken.widgets[5].row.clickable,"unresolved parent cannot qualify navigation");
 auto wrong_tab=faith;wrong_tab.widgets[2].row.runtime_name="other_tab";f::RestrictNavigationRows267V2(wrong_tab);Require(!wrong_tab.widgets[5].row.clickable,"literal edit_rite under wrong tab refused");
 auto wrong_actions=faith;wrong_actions.widgets[4].row.runtime_name="other_actions";f::RestrictNavigationRows267V2(wrong_actions);Require(!wrong_actions.widgets[5].row.clickable,"literal edit_rite under wrong actions refused");
 auto duplicate_edit=faith;duplicate_edit.widgets.push_back(row(8,5,"edit_rite",false));f::RestrictNavigationRows267V2(duplicate_edit);Require(!duplicate_edit.widgets[5].row.clickable,"duplicate literal even disabled refuses ordinal selection");
 auto obsolete_windows=faith;obsolete_windows.root_name="windows_layer";obsolete_windows.widgets[0].row.runtime_name="windows_layer";f::RestrictNavigationRows267V2(obsolete_windows);Require(!obsolete_windows.widgets[5].row.clickable,"historical windows layer is readonly and never aliases middle/Faith");
 auto rite=faith;rite.root_name="rite_creation_window";rite.widgets[0].row.runtime_name="rite_creation_window";rite.widgets[6].row.clickable=true;
 f::RestrictNavigationRows267V2(rite);Require(rite.widgets[6].row.clickable,"existing source-bound Rite scope semantics unchanged");
}

int main(int argc,char**argv){try{
 LiteralNavigationCases();
 Require(argc==2,"--synthetic-image or explicit exact actual EXE required");const bool synthetic=std::string_view(argv[1])=="--synthetic-image";
 auto pe=synthetic?std::make_unique<PeWindows>():std::make_unique<PeWindows>(argv[1]);ControlsPins(*pe);DoctrineKeyPins(*pe);RiteDoctrineItemsPins(*pe);const auto base=reinterpret_cast<std::uintptr_t>(pe->image);
 GuiCases(base);WindowCases(base);ControlsCases(base);DoctrineKeyCases(base);RiteDoctrineItemsCases(base);
 {Fixture fixture;f::ReadonlyObservation o;Put(fixture.actor,0x1B0,std::uintptr_t{1});Require(Run(fixture,base,o,true,f::ReadonlyModeV1::core_only)&&o.available&&!o.raw_resources&&!o.gui_window&&!o.rite_draft,"new shared owner reader mode1 still never reads raw/GUI/Rite data");}
 {Fixture fixture;f::ReadonlyObservation o;fixture.actor_drift=true;Require(Run(fixture,base,o,true,f::ReadonlyModeV1::core_only)&&!o.available,"new shared owner reader mode1 still rejects full actor generation drift");}
 Require(!c::BindCoreImage(base,f::kExecutableSha256).enabled,"legacy old image mapper still denies current EXE");
 std::cout<<"PASS current control source capture/code+typed callback/host+manager/limits/default authority; SOURCE_ONLY NoGame, Native dispatch/MainOwner/GUI/Dynastic/Save NOT_RUN; actual_EXE="<<(!synthetic)<<'\n';return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
