#pragma once

#include "xar_bridge/ck3_12004.hpp"

#include <cstdint>
#include <string_view>

namespace xar::ck3_12004::confucian_titles {

// Independent actual .4 finite disk operands. Each primary vtable is closed by
// its own exact class name, zero-offset COL and table reference, rather than an
// assumed image-wide relocation. The external packet also preserves the four
// property setters, law/key/capacity fragments, Faith constructor, complete
// challenger builders and actual current-holder sponsor lookup operands.
inline constexpr std::uintptr_t kCLandedTitlePrimaryVtableRva = 0x4712A28;
inline constexpr std::uintptr_t kCFaithPrimaryVtableRva = 0x472FA58;
inline constexpr std::uintptr_t kCLawPrimaryVtableRva = 0x48B88A8;
inline constexpr std::uintptr_t kFaithStorageSlotRva = 0x5D1E300;
inline constexpr std::uintptr_t kFaithFallbackSlotRva = 0x5D1E2E0;
inline constexpr std::uintptr_t kTitleFallbackSlotRva = 0x5D1DAE0;
inline constexpr std::string_view kFiniteMapSha256 =
    "5f5a1005711ef523bcd228c1b2ff2822a9767e13c1b9a934f9a3a87f37287e3d";

// SOURCEONLY evidence, never native/runtime or product acceptance credit.
// C:/workspace/ck3_lyd_runtime_20261004/
// r20-native-adapter-review-sourceonly-20261007-001/titles/a03/
// FINITE-ACTUAL4-MAP.json

} // namespace xar::ck3_12004::confucian_titles
