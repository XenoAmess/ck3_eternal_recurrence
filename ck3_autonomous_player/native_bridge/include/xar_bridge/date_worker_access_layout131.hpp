#pragma once
#include "xar_bridge/ck3_1210.hpp"
#include <cstdint>
#include <cstring>
namespace xar::ck3_1210 {
inline std::uint8_t ReadDateWorkerAccessByte131(const void *block,ImageBuildV1 build) noexcept {
 std::uint8_t out=0;
 std::memcpy(&out,static_cast<const std::byte*>(block)+(build==ImageBuildV1::full11126785313?0x6E8:0x6E0),1);
 return out;
}
}
