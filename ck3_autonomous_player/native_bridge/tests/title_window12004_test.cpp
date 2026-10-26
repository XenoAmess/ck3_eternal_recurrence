#include "xar_bridge/title_window12004.hpp"
#include "xar_bridge/title_window12004_source_pins.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <map>
#include <stdexcept>

namespace ui=xar::ck3_12004::title_ui;
namespace {
constexpr std::uintptr_t image=0x140000000ULL,handler=0x300000000ULL;
constexpr std::uintptr_t window=handler+0x10000,root=handler+0x20000;
constexpr std::uintptr_t storage=handler+0x30000,rows=handler+0x40000,title=handler+0x50000;
constexpr std::uint32_t full_id=0x81000001U;
struct Memory {
  std::map<std::uintptr_t,unsigned char> bytes;
  std::uintptr_t mutate_address=0;unsigned matching_reads=0;
  template<class T>void put(std::uintptr_t address,const T &value) {
    const auto *data=reinterpret_cast<const unsigned char *>(&value);
    for(std::size_t i=0;i<sizeof(value);++i)bytes[address+i]=data[i];
  }
  void raw(std::uintptr_t address,const unsigned char *data,std::size_t size) {
    for(std::size_t i=0;i<size;++i)bytes[address+i]=data[i];
  }
  static bool read(void *context,const void *address,void *output,std::size_t size) noexcept {
    auto &m=*static_cast<Memory *>(context);
    const auto at=reinterpret_cast<std::uintptr_t>(address);auto *out=static_cast<unsigned char *>(output);
    for(std::size_t i=0;i<size;++i) {
      const auto found=m.bytes.find(at+i);if(found==m.bytes.end())return false;out[i]=found->second;
    }
    if(at==m.mutate_address&&++m.matching_reads==2&&size==4)out[3]^=1;
    return true;
  }
};
void require(bool value,const char *name) {
  if(!value)throw std::runtime_error(name);
}
Memory fixture() {
  Memory m;
  for(const auto &pin:ui::source::pins)m.raw(image+pin.rva,pin.bytes.data(),pin.size);
  m.put(handler+0x1C0,window);m.put(window,image+0x45206B0);m.put(window+0x10,image+0x4520780);
  m.put(image+0x45206B0-8,image+0x4AF5190);m.put(image+0x4520780-8,image+0x4AF5168);
  m.put(image+0x4AF5190,std::array<std::uint32_t,6>{1,0,0,0x5729118,0x4AF4CA0,0x4AF5190});
  m.put(image+0x4AF5168,std::array<std::uint32_t,6>{1,0x10,0,0x5729118,0x4AF4CA0,0x4AF5168});
  constexpr char type_name[]=".?AVCTitleViewWindow@@";
  m.raw(image+0x5729118+0x10,reinterpret_cast<const unsigned char *>(type_name),sizeof(type_name));
  m.put(window+0xA0,handler);m.put(window+0x60,root);
  m.put(window+0xC8,std::uint32_t{0xFFFFFFFFU});m.put(window+0xCC,full_id);
  m.put(image+0x5D1DAF8,storage);m.put(image+0x5D1DAE0,std::uintptr_t{0});
  m.put(storage+0x20,rows);m.put(storage+0x2C,std::int32_t{2});
  m.put(rows+16+8,title);m.put(title+0x10,full_id);
  return m;
}
}
int main() {
  try {
    unsigned cases=0;auto m=fixture();
    auto b=ui::BindImage12004(image,xar::ck3_12004::kExecutableSha256,Memory::read,&m);
    ui::Selection selected{};std::string reason;
    const auto read=[&]{return ui::ReadSelection12004(b,reinterpret_cast<const void *>(handler),selected,reason);};
    require(!ui::BindImage12004(image,"wrong",Memory::read,&m).enabled,"wrong exact build");++cases;
    require(read()&&selected.subject_available&&selected.raw_title_id==full_id&&
        selected.root==reinterpret_cast<const void *>(root),"complete high-bit TitleID from CC, not C8");++cases;
    m.put(window+0xCC,std::uint32_t{0});m.put(rows+8,title);m.put(title+0x10,std::uint32_t{0});
    require(read()&&selected.subject_available&&selected.raw_title_id==0,"TitleID zero");++cases;m=fixture();
    m.put(window+0xCC,std::uint32_t{0xFF000001U});m.put(title+0x10,std::uint32_t{0xFF000001U});
    require(read()&&selected.subject_available&&selected.raw_title_id==0xFF000001U,"all generation bits retained");++cases;m=fixture();
    m.put(title+0x10,full_id^0x01000000U);
    require(read()&&!selected.subject_available&&!selected.title,"stale generation not a selected Title");++cases;m=fixture();
    m.put(window+0xCC,std::uint32_t{0xFFFFFFFFU});
    require(read()&&!selected.subject_available&&!selected.title,"invalid sentinel");++cases;m=fixture();
    m.put(image+0x5D1DAE0,title);
    require(read()&&!selected.subject_available&&!selected.title,"fallback cannot become a selected Title");++cases;m=fixture();
    m.put(window+0x10,std::uintptr_t{0});require(!read(),"secondary vtable");++cases;m=fixture();
    m.put(image+0x4AF5168+4,std::uint32_t{0});require(!read(),"secondary COL complete-object offset");++cases;m=fixture();
    m.put(image+0x5729118+0x10,std::uint8_t{0});require(!read(),"RTTI name");++cases;m=fixture();
    m.put(window+0xA0,handler+8);require(!read(),"handler backlink");++cases;m=fixture();
    m.put(image+ui::source::pins.front().rva,std::uint8_t{0});require(!read(),"loaded source pin drift");++cases;m=fixture();
    m.mutate_address=window+0xCC;require(!read(),"selection changed between reads");++cases;m=fixture();
    m.put(storage+0x2C,std::int32_t{-1});require(read()&&!selected.subject_available,"invalid capacity");++cases;m=fixture();
    m.put(handler+0x1C0,std::uintptr_t{0});require(!read(),"absent candidate");++cases;
    std::printf("{\"status\":\"PASS\",\"fixture_cases\":%u,\"game_contacted\":false,\"live_qualification\":false}\n",cases);
    return 0;
  } catch(const std::exception &error) {
    std::fprintf(stderr,"%s\n",error.what());return 1;
  }
}
