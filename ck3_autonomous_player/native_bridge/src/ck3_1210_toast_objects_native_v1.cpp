#include "xar_bridge/ck3_1210_toast_objects_v1.hpp"
#include <limits>
#if defined(_WIN32)
#include <windows.h>
#endif
namespace xar::ck3_1210 {
namespace {
#include "ck3_1210_gui_pins_v1.inc"
bool Copy(void *, std::uintptr_t address, void *out, std::size_t count) noexcept {
#if defined(_WIN32)
  SIZE_T actual=0;
  return address && out && count && count-1<=(std::numeric_limits<std::uintptr_t>::max)()-address &&
      ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void *>(address),out,count,&actual) && actual==count;
#else
  (void)address;(void)out;(void)count;return false;
#endif
}
template<std::size_t N> bool Pin(std::uintptr_t base,std::uintptr_t rva,
    const std::array<std::uint8_t,N> &expected) noexcept {
  std::array<std::uint8_t,N> actual{};
  return Copy(nullptr,base+rva,actual.data(),N) && actual==expected;
}
}
ToastObjectMemoryReaderV1 NativeToastObjectMemoryReaderV1() noexcept {return {nullptr,&Copy};}
ToastObjectBindingsV1 BindToastObjectImageV1(std::uintptr_t base,std::string_view sha) noexcept {
  if(!base || sha!=kExecutableSha256 || base>(std::numeric_limits<std::uintptr_t>::max)()-0x6FE4C00)return {};
  // Complete instructions sourced from exact disk PE. No function is invoked.
  constexpr std::array<std::uint8_t,11> has{0x83,0xB9,0xD4,0,0,0,0,0x0F,0x95,0xC0,0xC3};
  constexpr std::array<std::uint8_t,7> current{0x48,0x8B,0x81,0xC8,0,0,0};
  constexpr std::array<std::uint8_t,15> title{0x48,0x8D,0x93,0xC8,0x11,0,0,0x48,0x8B,0xCF,0xE8,0x24,0x1D,0x83,0xFF};
  constexpr std::array<std::uint8_t,15> description{0x48,0x8D,0x93,0xE8,0x11,0,0,0x48,0x8B,0xCF,0xE8,0xD4,0x1C,0x83,0xFF};
  constexpr std::array<std::uint8_t,7> publish{0x48,0x89,0xBE,0x80,0x04,0,0};
  constexpr std::array<std::uint8_t,9> reverse{0x81,0xE2,0xFF,0xFF,0xFF,0,0x8B,0x41,0x3C};
  if(!BindIngameReadyImageV1(base,sha).exact_build_admitted || !Pin(base,0xDD6F50,has) ||
      !Pin(base,0xDD6FA1,current) ||
      !Pin(base,0x1082BBD,title) || !Pin(base,0x1082C0D,description) ||
      !Pin(base,0xB01788,publish) || !Pin(base,0x45112C7,reverse) ||
      !Pin(base,kGuiFindTopRvaV1,kGuiFindTopPinV1) ||
      !Pin(base,kGuiShortcutRvaV1,kGuiShortcutPinV1) ||
      !Pin(base,kGuiContextChainRvaV1,kGuiContextChainPinV1) ||
      !Pin(base,kGuiHostBackrefRvaV1,kGuiHostBackrefPinV1) ||
      !Pin(base,kGuiHostStoreRvaV1,kGuiHostStorePinV1))return {};
  const auto identities=BindToastScopeIdentityImageV1(base,sha);
  if(!identities.exact_build_admitted)return {};
  return {base,true,identities};
}
} // namespace xar::ck3_1210
