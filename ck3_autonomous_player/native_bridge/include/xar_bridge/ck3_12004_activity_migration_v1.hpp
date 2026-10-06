#pragma once

#include "xar_bridge/ck3_12004.hpp"

#include <cstdint>
#include <string_view>

namespace xar::bridge {

// Explicit current executable admission. Old software DTOs do not admit old RVAs.
inline bool IsActivity12004BuildV1(std::string_view sha) noexcept {
  return sha == ck3_12004::kExecutableSha256;
}

// Finite paired source operands: activity/common-native/SHARED-PROFILE-LEDGER.json.
// Historical callers retain their exact existing address selection.
inline std::uintptr_t Activity12004RvaV1(
    std::string_view sha, std::uintptr_t old12002_rva) noexcept {
  if (!IsActivity12004BuildV1(sha)) return old12002_rva;
  switch (old12002_rva) {
  case 0x878290: return 0x878290;
  case 0x8FC200: return 0x8FC200;
  case 0x9DEA70: return 0x9DEA70;
  case 0x9DEB70: return 0x9DEB70;
  case 0x9DFF87: return 0x9DFF87;
  case 0x9E002A: return 0x9E002A;
  case 0xA90050: return 0xA90050;
  case 0xAF3950: return 0xAF3950;
  case 0xAF39E0: return 0xAF39E0;
  case 0xAF39FD: return 0xAF39FD;
  case 0xB1F0A0: return 0xB1F0A0;
  case 0xC86146: return 0xC86146;
  case 0xD51E50: return 0xD51E50;
  case 0x11B2885: return 0x11B2865;
  case 0x11B2E30: return 0x11B2E10;
  case 0x11B5950: return 0x11B5930;
  case 0x11B5B30: return 0x11B5B10;
  case 0x11B5B5F: return 0x11B5B3F;
  case 0x11B5BE0: return 0x11B5BC0;
  case 0x11B5C46: return 0x11B5C26;
  case 0x11B5C58: return 0x11B5C38;
  case 0x11B64C0: return 0x11B64A0;
  case 0x11B6550: return 0x11B6530;
  case 0x11B6C80: return 0x11B6C60;
  case 0x11B6CB7: return 0x11B6C97;
  case 0x11B6CD3: return 0x11B6CB3;
  case 0x11B6CE0: return 0x11B6CC0;
  case 0x11B6D51: return 0x11B6D31;
  case 0x11B6F50: return 0x11B6F30;
  case 0x11B8066: return 0x11B8046;
  case 0x11B8073: return 0x11B8053;
  case 0x11B8331: return 0x11B8311;
  case 0x11B8350: return 0x11B8330;
  case 0x11B8670: return 0x11B8650;
  case 0x11B8693: return 0x11B8673;
  case 0x11B86DF: return 0x11B86BF;
  case 0x11B88E8: return 0x11B88C8;
  case 0x11B8CD0: return 0x11B8CB0;
  case 0x11B8D53: return 0x11B8D33;
  case 0x11B8D90: return 0x11B8D70;
  case 0x11B95D0: return 0x11B95B0;
  case 0x11BA6D0: return 0x11BA6B0;
  case 0x11D3404: return 0x11D33E4;
  case 0x11D8EC0: return 0x11D8EA0;
  case 0x1642F05: return 0x1642EE5;
  case 0x1643A17: return 0x16439F7;
  case 0x165A9D0: return 0x165A9B0;
  case 0x165AB90: return 0x165AB70;
  case 0x165B655: return 0x165B635;
  case 0x21603A0: return 0x2160380;
  case 0x21603AA: return 0x216038A;
  case 0x23F0195: return 0x23F0175;
  case 0x23FC85A: return 0x23FC83A;
  case 0x29C2E97: return 0x29C2E77;
  case 0x2ADD8EE: return 0x2ADD8CE;
  case 0x2BBADE0: return 0x2BBADC0;
  case 0x2BBD1B0: return 0x2BBD190;
  case 0x2BBD32A: return 0x2BBD30A;
  case 0x2BBE691: return 0x2BBE671;
  case 0x3057BC0: return 0x3057BA0;
  case 0x305A280: return 0x305A260;
  case 0x310AE10: return 0x310ADF0;
  case 0x310AEE5: return 0x310AEC5;
  case 0x3118700: return 0x31186E0;
  case 0x3765880: return 0x3765860;
  case 0x3F7E240: return 0x3F7E220;
  case 0x3F8A6F0: return 0x3F8A6D0;
  case 0x3F8A800: return 0x3F8A7E0;
  case 0x4260E94: return 0x4260E74;
  case 0x44BA890: return 0x44BA8A0;
  case 0x44BC408: return 0x44BC418;
  case 0x44E6F38: return 0x44E6F48;
  case 0x45325C8: return 0x45325D8;
  case 0x45326A0: return 0x45326B0;
  case 0x457A110: return 0x457A120;
  case 0x457A138: return 0x457A148;
  case 0x472E130: return 0x472E140;
  case 0x48B2EC0: return 0x48B2ED0;
  case 0x48B2F20: return 0x48B2F30;
  case 0x48BFD18: return 0x48BFD28;
  case 0x48BFE50: return 0x48BFE60;
  case 0x54D76F0: return 0x54D76F0;
  case 0x5514438: return 0x5514438;
  case 0x5514460: return 0x5514460;
  case 0x5C67208: return 0x5C67208;
  case 0x5C67568: return 0x5C67568;
  case 0x5C67570: return 0x5C67570;
  case 0x5C68C50: return 0x5C68C50;
  case 0x5C6A520: return 0x5C6A520;
  case 0x5D1FB40: return 0x5D1FB40;
  case 0x5D33EE8: return 0x5D33EE8;
  case 0x5D33F48: return 0x5D34048;
  default: return 0;
  }
}

} // namespace xar::bridge
