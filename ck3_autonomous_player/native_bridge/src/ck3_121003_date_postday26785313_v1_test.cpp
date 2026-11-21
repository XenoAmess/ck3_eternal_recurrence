#include "xar_bridge/ck3_121003_date_postday26785313_v1.hpp"
#include <cassert>
#include <cstring>
#include <map>
#include <limits>

namespace current=xar::ck3_121003::build26785313;
namespace {
// Sparse NoGame mapped-image DATA, not an actual owner, thread or callback.
struct Image {std::map<std::uintptr_t,unsigned char> bytes;};
void Put(Image &image,std::uintptr_t at,const void *raw,std::size_t n) {
  const auto *bytes=static_cast<const unsigned char *>(raw);
  for(std::size_t i=0;i<n;++i) {
    auto [where,added]=image.bytes.emplace(at+i,bytes[i]);
    assert(added||where->second==bytes[i]);
  }
}
bool Read(void *opaque,std::uintptr_t at,void *raw,std::size_t n) noexcept {
  if(!opaque||!raw)return false;
  const auto &image=*static_cast<const Image *>(opaque);
  auto *bytes=static_cast<unsigned char *>(raw);
  for(std::size_t i=0;i<n;++i) {
    const auto found=image.bytes.find(at+i);if(found==image.bytes.end())return false;
    bytes[i]=found->second;
  }
  return true;
}
Image Fixture(std::uintptr_t base) {
  Image image;
  const std::uint16_t mz=0x5A4D,machine=0x8664,magic=0x20B;
  const std::uint32_t pe=0x100,signature=0x4550,timestamp=current::kPeTimestamp;
  const std::uint32_t image_size=static_cast<std::uint32_t>(current::kImageSize);
  const std::uint64_t preferred=base;
  Put(image,base,&mz,sizeof(mz));Put(image,base+0x3C,&pe,sizeof(pe));
  Put(image,base+pe,&signature,sizeof(signature));Put(image,base+pe+4,&machine,sizeof(machine));
  Put(image,base+pe+8,&timestamp,sizeof(timestamp));Put(image,base+pe+24,&magic,sizeof(magic));
  Put(image,base+pe+48,&preferred,sizeof(preferred));Put(image,base+pe+80,&image_size,sizeof(image_size));
  for(const auto set:{current::CommandCodePinsV1(),current::CommandMetadataPinsV1(),
      current::CurrentDatePostdayCodePins267V1(),current::CurrentDatePostdayMetadataPins267V1()})
    for(const auto &pin:set)Put(image,base+pin.rva,pin.bytes.data(),pin.bytes.size());
  for(const auto &pin:current::CommandPointerPinsV1()) {
    const auto va=base+pin.target_rva;Put(image,base+pin.rva,&va,sizeof(va));
  }
  for(const auto &pin:current::CurrentDatePostdayPointerPins267V1()) {
    const auto va=base+pin.target_rva;Put(image,base+pin.rva,&va,sizeof(va));
  }
  return image;
}
}
int main() {
  const current::CommandIdentityV1 identity{current::kGameVersion,current::kSteamBuildId,current::kExecutableSha256};
  for(const std::uintptr_t base:{0x140000000ULL,0x7ff600000000ULL}) {
    auto image=Fixture(base);
    const current::CommandImageReadV1 read{&image,&Read};
    assert(current::VerifyCurrentDatePostdayImage267V1(base,identity,read));
    auto wrong=identity;wrong.game_version="1.21.0";
    assert(!current::VerifyCurrentDatePostdayImage267V1(base,wrong,read));
    wrong=identity;wrong.steam_build_id="26757580";
    assert(!current::VerifyCurrentDatePostdayImage267V1(base,wrong,read));
    image.bytes.at(base+current::kDateDailyFinalFunction267V1)^=1;
    assert(!current::VerifyCurrentDatePostdayImage267V1(base,identity,read));
    image=Fixture(base);
    image.bytes.at(base+0x60B12D8)^=1;
    assert(!current::VerifyCurrentDatePostdayImage267V1(base,identity,read));
    image=Fixture(base);
    image.bytes.at(base+current::kDateDailyFinalSlot267V1)^=1;
    assert(!current::VerifyCurrentDatePostdayImage267V1(base,identity,read));
    image=Fixture(base);
    image.bytes.erase(base+current::kDateWorkerConsumer267V1+40);
    assert(!current::VerifyCurrentDatePostdayImage267V1(base,identity,read));
    image=Fixture(base);
    const auto preferred_only=0x140000000ULL+current::kDateDailyFinalFunction267V1;
    for(std::size_t i=0;i<sizeof(preferred_only);++i)
      image.bytes[base+current::kDateDailyFinalSlot267V1+i]=reinterpret_cast<const unsigned char *>(&preferred_only)[i];
    assert(current::VerifyCurrentDatePostdayImage267V1(base,identity,read)==(base==0x140000000ULL));
  }
  auto image=Fixture(0x140000000ULL);
  assert(!current::VerifyCurrentDatePostdayImage267V1(0,identity,{&image,&Read}));
  assert(!current::VerifyCurrentDatePostdayImage267V1((std::numeric_limits<std::uintptr_t>::max)()-1,identity,{&image,&Read}));
  assert(!current::CurrentDatePostdayTargetsMatch267V1({}));
  assert(!current::BindCurrentDatePostdayImage267V1(0,identity).current_image_verified);
  static_assert(current::kDateCommandScopeOffset267V1==0x140);
  static_assert(current::kDateNativeAccessOffset267V1==0x6E8);
  static_assert(current::kDateMainWarmOffset267V1==0x3620);
  static_assert(current::kDateMainContextOffset267V1==0x3628);
}
