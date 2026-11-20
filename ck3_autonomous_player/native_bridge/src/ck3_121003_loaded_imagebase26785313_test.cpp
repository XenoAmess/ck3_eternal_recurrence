#include "ck3_1210_core.cpp"
#include "ck3_121003_readonly26785313_v1.cpp"
#include <windows.h>
#include <array>
#include <cstring>
#include <iostream>
#include <stdexcept>
namespace f=xar::ck3_121003::build26785313;
namespace {
void Need(bool value,const char *why){if(!value)throw std::runtime_error(why);}
struct DataImage {
 void *bytes=nullptr;std::uintptr_t base=0;static constexpr std::uint32_t pe=0x100;
 template<class T>void Set(std::size_t offset,T value){std::memcpy(static_cast<unsigned char*>(bytes)+offset,&value,sizeof(value));}
 DataImage(){bytes=VirtualAlloc(nullptr,f::kImageSize,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);Need(bytes!=nullptr,"non-executable source image allocation");base=reinterpret_cast<std::uintptr_t>(bytes);Need(base!=0x140000000ULL,"explicit non-preferred ASLR-shaped image");
  Set(0,std::uint16_t{0x5A4D});Set(0x3C,pe);Set(pe,std::uint32_t{0x4550});Set(pe+4,std::uint16_t{0x8664});Set(pe+8,f::kPeTimestamp);
  Set(pe+24,std::uint16_t{0x20B});Set(pe+24+24,static_cast<std::uint64_t>(base));Set(pe+24+56,static_cast<std::uint32_t>(f::kImageSize));
  for(const auto&pin:f::ReadonlyImagePins())std::memcpy(static_cast<unsigned char*>(bytes)+pin.rva,pin.bytes.data(),pin.bytes.size());
 }
 ~DataImage(){if(bytes)VirtualFree(bytes,0,MEM_RELEASE);}
};
}
int main(){try{
 DataImage image;
 // Calls the real production function with NO offline-fixture definition.
 // These are data-only windows, never executable code or a Game/owner proof.
 Need(f::VerifyReadonlyImage(image.base),"production verifier rejects loader-updated ASLR ImageBase");
 Need(f::BindReadonlyImage(image.base,f::kExecutableSha256).exact_image_admitted,"real current binder accepts loaded-base shape");
 image.Set(DataImage::pe+24+24,std::uint64_t{0x140000000ULL});Need(!f::VerifyReadonlyImage(image.base),"unrelocated preferred-header image cannot claim a loaded module");
 image.Set(DataImage::pe+24+24,static_cast<std::uint64_t>(image.base+4096));Need(!f::VerifyReadonlyImage(image.base),"foreign loaded header base rejected");
 image.Set(DataImage::pe+24+24,std::uint64_t{0});Need(!f::VerifyReadonlyImage(image.base),"zero loaded header base rejected");
 image.Set(DataImage::pe+24+24,static_cast<std::uint64_t>(image.base));
 auto *pin=static_cast<unsigned char*>(image.bytes)+f::ReadonlyImagePins()[0].rva;*pin^=1;Need(!f::VerifyReadonlyImage(image.base),"code pin mutation remains rejected");*pin^=1;
 Need(!f::BindReadonlyImage(image.base,"BB3FEF106240E95ECDB6F1532982E89E9432C92A99D33DB623521572F06E6F79").exact_image_admitted,"old executable hash remains rejected");
 Need(!xar::ck3_1210::BindCoreImage(image.base,f::kExecutableSha256).enabled,"legacy mapper remains closed");
 Need(f::VerifyReadonlyImage(image.base),"restored current loaded shape accepted");
 std::cout<<"PASS actual production ASLR loaded-base verifier positive and old-preferred/foreign/zero/code/tuple negative cases; DATA_ONLY no fixture bypass, Game/owner/RVA execution NOT_RUN\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
