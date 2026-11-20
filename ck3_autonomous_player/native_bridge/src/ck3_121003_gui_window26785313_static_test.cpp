#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
// Finite whole-unit fixture follows the existing BB3 body-inclusion pattern.
// Compile the actual unchanged Core and actual new implementation once.
#include "ck3_1210_core.cpp"
#include "ck3_121003_readonly26785313_v1.cpp"
#include "ck3_121003_core_route26785313_v1.cpp"
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
    put(pe+24,std::uint16_t{0x20B});put(pe+24+24,std::uint64_t{0x140000000ULL});
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
   {Fixture fixture;fixture.drift=true;
    Require(Run(fixture,base,out,true,f::ReadonlyModeV1::core_only)&&out.available&&!out.raw_resources&&out.core_read_attempts==2,"Core-only ignores unrelated raw amount drift");
    Require(!f::CoreRouteObservationV1(out).core_available,"NoGame observation cannot become a live Core");}
   {Fixture fixture;Put(fixture.actor,0x1B0,std::uintptr_t{1});
    Require(Run(fixture,base,out,true,f::ReadonlyModeV1::core_only)&&out.available&&!out.raw_resources,"Core-only never dereferences living/resource storage");}
   {Fixture fixture;fixture.actor_drift=true;
    Require(Run(fixture,base,out,true,f::ReadonlyModeV1::core_only)&&!out.available&&!out.raw_resources,"Core-only full-generation drift denied");}
   {Fixture fixture;Require(Run(fixture,base,out,true,static_cast<f::ReadonlyModeV1>(99))&&!out.available,"unknown mode denied");}
#if defined(XAR_CK3_ENABLE_121003_26785313_GUI_ROOT_INDEX_V1)
   GuiCases(base);
#else
   Require(!f::VerifyGuiRootIndexImageV1(base),"default-OFF root image gate closed");
   {Fixture fixture;Require(Run(fixture,base,out,true,f::ReadonlyModeV1::core_and_gui_root_index)&&!out.available&&!out.gui_root_index&&!out.raw_resources,"default-OFF root mode refused");}
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_GUI_WINDOW_V1)
   WindowCases(base);
#else
   Require(!f::VerifyGuiWindowImageV1(base),"defaultOFF window gate closed");
   {Fixture fixture;Require(Run(fixture,base,out,true,f::ReadonlyModeV1::core_and_gui_window)&&!out.available&&!out.gui_window,"mode3 defaultOFF refused");}
#endif
   const auto environment=f::BindCoreRouteMailboxEnvironmentV1(base,f::kExecutableSha256);
   Require(environment.exact_build_admitted&&environment.build_profile==&f::ReadonlyThreadProfile()&&
       environment.permitted_executor==&f::ExecuteReadonlyOnOwner&&
#if defined(XAR_CK3_ENABLE_121003_26785313_APPLICATION_EXIT_V1)
       environment.permitted_executor_secondary==&f::ExecuteApplicationExitOnOwner267V1&&
#else
       environment.permitted_executor_secondary==nullptr&&
#endif
       environment.snapshot_observer_callback==nullptr&&environment.permitted_frontend_executor==nullptr,"only one exact owner executor");
   Require(!f::BindCoreRouteMailboxEnvironmentV1(base,"wrong").exact_build_admitted&&
       !f::BindCoreRouteMailboxEnvironmentV1(0,f::kExecutableSha256).exact_build_admitted,"mixed mailbox source denied");
   f::ReadonlyObservation data{};data.available=true;data.main_owner_observed=true;
   data.core.clock={123456,5,true};data.core.local_player_id=7;data.core.map_ready=true;
   data.core.has_played_character=true;data.core.played_character_id=16777217;data.core.played_character_alive=true;
   Require(f::CoreRouteObservationV1(data).core_available,"hand-authored mapper DATA only");
   data.raw_resources=f::RawResources{};Require(!f::CoreRouteObservationV1(data).core_available,"raw resource observation cannot masquerade as Core-only");
   data.raw_resources.reset();data.main_owner_observed=false;
   Require(!f::CoreRouteObservationV1(data).core_available,"missing owner denied");
   constexpr std::array<std::string_view,1> caps{c::kCoreFrameCapabilityV1};
   const xar::game::AdapterDescriptor descriptor{f::kAdapterId,f::kGameVersion,f::kExecutableSha256,"xar_checkpoint",caps};
   Require(xar::game::IsCk3_121003Core26785313Descriptor(descriptor)&&!xar::game::IsCk3_1210BasicDescriptor(descriptor),"Core identity is outside old Full/clock union");
#if defined(XAR_CK3_ENABLE_121003_26785313_GUI_ROOT_INDEX_V1)
    std::cout<<"PASS bounded current scripted-root index production reader; opaque identities/owner/Core/date/actor/drift/limits/oldtuple guards; NO TREE/GUI/ACTION/LIVE qualification\n";
#else
    std::cout<<"PASS root profile default-OFF; prior Core/Gold behavior retained\n";
#endif
    if(synthetic)std::cout<<"PASS SOURCE_ONLY synthetic PE/Core/actor/resources/drift; EXE NOT_CHECKED; LIVE NOT_RUN\n";
   else std::cout<<"PASS exact26785313 disk SHA/PE windows; real Core reader synthetic signed-ID/resources/drift; legacy routing closed; no Game code executed; LIVE NOT_RUN\n";
  return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}
}
