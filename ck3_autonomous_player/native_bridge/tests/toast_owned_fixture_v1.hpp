#pragma once
// Shared owned-memory fixture used by the actual provider regression and the
// serializer producer. It is never included by a production Native source.
#include "xar_bridge/ck3_1210_toast_objects_v1.hpp"
#include <cassert>
#include <cstring>
#include <map>
#include <vector>
namespace xar::ck3_1210::toast_test {
struct Memory {
  std::map<std::uintptr_t,std::vector<std::byte>> regions;
  std::uintptr_t fail_address=0,change_address=0;
  std::size_t change_hits=0,change_on_hit=2,bytes_seen=0;
  void add(std::uintptr_t address,std::size_t count) {assert(regions.emplace(address,std::vector<std::byte>(count)).second);}
  std::byte *find(std::uintptr_t address,std::size_t count) {
    auto i=regions.upper_bound(address);if(i==regions.begin())return nullptr;--i;
    const auto offset=address-i->first;
    return offset<=i->second.size() && count<=i->second.size()-offset?i->second.data()+offset:nullptr;
  }
  template<class T>void put(std::uintptr_t address,const T &value) {
    auto *p=find(address,sizeof(value));assert(p);std::memcpy(p,&value,sizeof(value));
  }
  static bool copy(void *p,std::uintptr_t address,void *out,std::size_t count) noexcept {
    auto &m=*static_cast<Memory *>(p);m.bytes_seen+=count;
    if(address==m.fail_address)return false;
    if(address==m.change_address && ++m.change_hits==m.change_on_hit)m.put<std::int32_t>(address,2);
    const auto *found=m.find(address,count);if(!found)return false;std::memcpy(out,found,count);return true;
  }
};
struct Fixture {
  static constexpr std::uintptr_t base=0x10000000,root=0x20000000,app=0x21000000,gfx=0x22000000;
  static constexpr std::uintptr_t interface_handler=0x23000000,toast=0x24000000,item=0x25000000;
  static constexpr std::uintptr_t frontend=0x26000000,context=0x27000000,host=0x28000000;
  static constexpr std::uintptr_t gui_root=0x29000000,toast_widget=0x2A000000,content=0x2B000000;
  static constexpr std::uintptr_t root_children=0x2C000000,toast_children=0x2D000000;
  Memory memory;std::uintptr_t string_cursor=0x40000000;
  ToastObjectBindingsV1 bindings{base,true,{base,true}};ToastObjectProviderV1 provider{};
  IngameReadyGraphV1 graph{reinterpret_cast<void *>(root),reinterpret_cast<void *>(app),
      reinterpret_cast<void *>(gfx),reinterpret_cast<void *>(interface_handler),7};
  Fixture() {
    memory.add(base+kJominiStateSlotRva,8);memory.put(base+kJominiStateSlotRva,root);
    for(auto p:{root,app,gfx,interface_handler,toast,frontend,context,host,gui_root,toast_widget,content})memory.add(p,0x600);
    memory.add(item,0x1230);memory.add(root_children,8);memory.add(toast_children,8);memory.add(0x33000000,0x140);
    memory.put<std::uintptr_t>(item,0x33000000);memory.put<std::uint32_t>(0x33000000+0x38,0x4744624F);memory.put<std::uint8_t>(item+0x10,2);
    memory.put(root,base+kIngameRootVtableRvaV1);memory.put(root+0x18,app);memory.put(root+0x10,gfx);
    memory.put(app,base+kIngameApplicationVtableRvaV1);memory.put(app+0x28,root);memory.put(app+0x180,graph.completed_frame_epoch);
    memory.put(gfx,base+kIngameGfxVtableRvaV1);memory.put(gfx+0x20,root);memory.put(gfx+0x90,app);memory.put(gfx+0x88,interface_handler);
    memory.put(interface_handler,base+kIngameHandlerVtableRvaV1);memory.put(interface_handler+0x40,root);memory.put(interface_handler+0x480,toast);
    memory.put(toast,base+std::uintptr_t{0x4B609C0});memory.put(toast+0x98,root);memory.put(toast+0xA0,interface_handler);
    memory.put(toast+0xC8,item);memory.put<std::int32_t>(toast+0xD0,4);memory.put<std::int32_t>(toast+0xD4,1);
    memory.put(toast+0x60,toast_widget);memory.put(app+0x1B8,frontend);memory.put(frontend+0x58,context);
    memory.put(context+0x3D8,host);memory.put(host+8,context);memory.put(context+0xD0,gui_root);
    widget(gui_root,0,root_children,1,"gui_root");widget(toast_widget,gui_root,toast_children,1,"toast_container_widget");
    widget(content,toast_widget,0,0,"toast_content");memory.put(root_children,toast_widget);memory.put(toast_children,content);
    text(item+0x11C8,"Test title");text(item+0x11E8,"Test description");
  }
  void text(std::uintptr_t p,std::string_view value) {
    memory.put<std::uint64_t>(p+0x10,value.size());memory.put<std::uint64_t>(p+0x18,value.size()<16?15:value.size());
    std::uintptr_t data=p;
    if(value.size()>=16) {data=string_cursor;string_cursor+=0x1000;memory.add(data,value.size()+1);memory.put(p,data);}
    auto *bytes=memory.find(data,value.size()+1);assert(bytes);std::memcpy(bytes,value.data(),value.size());bytes[value.size()]=std::byte{};
  }
  void widget(std::uintptr_t p,std::uintptr_t parent,std::uintptr_t children,std::int32_t count,std::string_view name) {
    memory.put(p,base+std::uintptr_t{0x4B60000});memory.put(p+0xD8,context);memory.put(p+0xE8,parent);
    memory.put(p+0xF0,children);memory.put(p+0xFC,count);text(p+0x1B8,name);
  }
  void advance() {++graph.completed_frame_epoch;memory.put(app+0x180,graph.completed_frame_epoch);}
  bool read(ToastObjectObservationV1 &out) {return ObservePublishedToastObjectV1(bindings,graph,{&memory,&Memory::copy},provider,out);}
  void scopes(std::int32_t count=1) {
    const auto table=base+std::uintptr_t{0x6B14640},data=std::uintptr_t{0x31000000},names=std::uintptr_t{0x32000000};
    memory.add(table,0x50);memory.add(data,0x30);memory.add(names,0x80);
    memory.put<std::uint8_t>(table,3);memory.put(table+0x30,names);memory.put<std::int32_t>(table+0x3C,4);
    text(names+0x60,"xfm_news_display_entry");
    memory.put(item+0x38,data);memory.put(item+0x40,count);memory.put(item+0x44,count);
    memory.put<std::uint32_t>(data,0x03000003);memory.put<std::uint32_t>(data+8,0x1234); // Deliberately unsupported tag.
    if(count==2)memory.put<std::uint32_t>(data+0x18,0x03000003);
  }
  void script_scopes() {
    const auto data=std::uintptr_t{0x34000000};memory.add(data,0x30);
    memory.put(item+0xF78,data);memory.put<std::int32_t>(item+0xF80,1);memory.put<std::int32_t>(item+0xF84,1);
    text(data,"xfm_news_display_entry");memory.put<std::uint32_t>(data+0x20,0x1234);
  }
  static std::array<std::byte,16> token(std::uint16_t tag,std::uint32_t id) {
    std::array<std::byte,16> out{};const std::uint64_t payload=id;
    std::memcpy(out.data(),&tag,2);std::memcpy(out.data()+8,&payload,8);return out;
  }
  static constexpr std::uintptr_t story_storage=0x35000000,character_storage=0x35100000;
  static constexpr std::uintptr_t story_slots=0x36000000,character_slots=0x37000000;
  static constexpr std::uintptr_t story_object=0x38000000,character_object=0x38100000;
  void canonical(std::uint16_t tag,std::uint32_t id) {
    const bool story=tag==22;const auto storage=story?story_storage:character_storage;
    const auto slots=story?story_slots:character_slots,object=story?story_object:character_object;
    const auto slot=base+(story?std::uintptr_t{0x6A66700}:kCharacterStorageSlotRva);
    memory.add(slot,8);memory.put(slot,storage);memory.add(storage,0x30);
    memory.put(storage+0x20,slots);memory.put<std::uint32_t>(storage+0x2C,(id&0xFFFFFFU)+1);
    const auto entry=slots+static_cast<std::size_t>(id&0xFFFFFFU)*0x10+8;
    memory.add(entry,8);memory.put(entry,object);memory.add(object,0x20);
    memory.put<std::uint32_t>(object+(story?0x10:0x18),id);
    memory.put<std::uint32_t>(object+(story?0x14:0x1C),story?0x41635374U:0x43686172U);
  }
  void script_typed_pair() {
    canonical(22,0x03000002);canonical(4,0x80000002);
    const std::uintptr_t data=0x34000000;memory.add(data,0x60);memory.put(item+0xF78,data);
    memory.put<std::int32_t>(item+0xF80,2);memory.put<std::int32_t>(item+0xF84,2);
    text(data,"software_story");memory.put(data+0x20,token(22,0x03000002));
    text(data+0x30,"software_character");memory.put(data+0x50,token(4,0x80000002));
  }
  void script_many(std::int32_t count) {
    canonical(22,0x03000002);const std::uintptr_t data=0x34000000;memory.add(data,static_cast<std::size_t>(count)*0x30);
    memory.put(item+0xF78,data);memory.put(item+0xF80,count);memory.put(item+0xF84,count);
    for(std::int32_t i=0;i<count;++i) {const auto entry=data+static_cast<std::size_t>(i)*0x30;
      text(entry,"scope_"+std::to_string(i));memory.put(entry+0x20,token(22,0x03000002));}
  }
};
} // namespace xar::ck3_1210::toast_test
