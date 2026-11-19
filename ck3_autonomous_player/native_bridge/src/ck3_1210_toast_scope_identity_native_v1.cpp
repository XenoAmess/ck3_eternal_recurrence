#include "xar_bridge/ck3_1210_toast_scope_identity_v1.hpp"
#include <windows.h>
#include <limits>
namespace xar::ck3_1210 {
namespace {
template<std::size_t N>bool Pin(std::uintptr_t base,std::uintptr_t rva,const std::array<std::uint8_t,N> &expected) noexcept {
  std::array<std::uint8_t,N> actual{};SIZE_T got=0;
  return ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void *>(base+rva),actual.data(),actual.size(),&got) &&
      got==actual.size() && actual==expected;
}
} // namespace
ToastScopeIdentityBindingsV1 BindToastScopeIdentityImageV1(std::uintptr_t base,std::string_view sha) noexcept {
  if(sha!=kExecutableSha256 || !base || base>(std::numeric_limits<std::uintptr_t>::max)()-0x6FE4C00)return {};
  constexpr std::array<std::uint8_t,4> story_tag{0x66,0x83,0x39,0x16};
  constexpr std::array<std::uint8_t,7> story_storage{0x48,0x8B,0x0D,0x07,0x21,0xEC,0x03};
  constexpr std::array<std::uint8_t,3> story_id{0x39,0x43,0x10};
  constexpr std::array<std::uint8_t,7> story_magic{0x81,0x79,0x14,0x74,0x53,0x63,0x41};
  constexpr std::array<std::uint8_t,4> character_tag{0x66,0x83,0x3A,0x04};
  constexpr std::array<std::uint8_t,7> character_storage{0x4C,0x8B,0x05,0x99,0x1E,0x67,0x03};
  constexpr std::array<std::uint8_t,3> character_id{0x39,0x50,0x18};
  constexpr std::array<std::uint8_t,7> character_magic{0x81,0x78,0x1C,0x72,0x61,0x68,0x43};
  if(!Pin(base,0x2BA45E2,story_tag) || !Pin(base,0x2BA45F2,story_storage) || !Pin(base,0x2BA4621,story_id) ||
      !Pin(base,0x2CD14D6,story_magic) || !Pin(base,0x3236778,character_tag) ||
      !Pin(base,0x3236788,character_storage) || !Pin(base,0x32367B4,character_id) || !Pin(base,0x32367D1,character_magic))return {};
  return {base,true};
}
} // namespace xar::ck3_1210
