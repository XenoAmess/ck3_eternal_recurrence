// Exact4 bounded ShowDetails loaded-code pins.
struct PresentationDetailPin12004{std::uintptr_t rva;const char*hex;};
static constexpr PresentationDetailPin12004 kPresentationDetailPins12004[]{
{0x1a2340U,"4c8bdc4881ec88000000498d43b84989430833c0498943c0498943b8498943c8"},
{0x12b3260U,"4883ec384885c97428488b4108448b41104c8bc8488b09c7442420010000008b"},
{0x12be718U,"8b041f39053f81a9040f8f040300008b1d3781a904899da8000000803d3c1aa8"},
{0x12b89d1U,"488bdaba1000000065488b042558000000488b088b040a390572dea9040f8f92"},
{0x12aafa4U,"488d05cd4e2903488945b0c745b813000000448865bc4c897da0c745a81a0000"},
{0x12b0423U,"488bd9488b81d800000081b85c080000766f72500f8530050000"},
{0x12b04cfU,"8b853001000083f8010f851c01000041817f384f624447753a488d8bc8010000"},
{0x12b0941U,"8b85300100008983f80e00008b85180100008983f40e00004489a3f00e000048"},
{0x12b3390U,"40534883ec30488bd94885c974384c8b41088b5110488b09e893d8ffff488b43"},
{0x12b0c40U,"4883ec58488b81d80000008b4810c64424280033c0488944242c89442434488d"},
{0x45402f8U,"53686f7744657461696c7300"},
{0x45402d8U,"475549506f74656e7469616c4275696c64696e674974656d"},
{0x453fe78U,"686f6c64696e675f747261636b735f7669657700"},
{0x4b348a8U,"01000000000000000000000098927605b831b304a848b304"},
{0x5769298U,"a01042440100000000000000000000002e3f4156434275696c64696e67547261"},
};
bool PresentationDetailSourcePins12004(const ZhongguoScoreboardNativeEnvironmentV1&env) {
std::array<unsigned char,32>raw{};
const auto digit=[](char c)->unsigned{return c<='9'?unsigned(c-'0'):unsigned(c-'a'+10);};
for(const auto&p:kPresentationDetailPins12004){const auto n=std::strlen(p.hex)/2;if(n>raw.size()||!Read(reinterpret_cast<const void*>(env.module_base+p.rva),raw.data(),n))return false;
std::size_t first=0;
if(p.rva==0x5769298U){
  // This TypeDescriptor's first qword is a loader-relocated type_info vftable
  // VA, not immutable file bytes. Keep exact vftable RVA and all suffix pins.
  std::uintptr_t actual=0;std::memcpy(&actual,raw.data(),sizeof(actual));
  if(env.module_base>(std::numeric_limits<std::uintptr_t>::max)()-0x44210A0U||actual!=env.module_base+0x44210A0U)return false;
  first=sizeof(actual);
}
for(std::size_t i=first;i<n;++i)if(raw[i]!=((digit(p.hex[2*i])<<4)|digit(p.hex[2*i+1])))return false;}
return true;
}
