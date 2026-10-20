#pragma once
#ifdef NDEBUG
#error B11 qualification consumers require active assertions
#endif
#ifndef XAR_B11_PROFILE_MASK
#error Explicit finite profile is required
#endif
#if XAR_B11_PROFILE_MASK != 0 && XAR_B11_PROFILE_MASK != 1 && XAR_B11_PROFILE_MASK != 3 && XAR_B11_PROFILE_MASK != 4 && XAR_B11_PROFILE_MASK != 8 && XAR_B11_PROFILE_MASK != 16 && XAR_B11_PROFILE_MASK != 31
#error Unsupported finite B11 profile
#endif
// Applied before including the unchanged production .cpp, not only to main().
// OFF means absent. In particular, defining an OFF feature as =0 is forbidden.
#undef XAR_CK3_ENABLE_G2_PLAYER_ARTIFACT_PERSONAL_USE_READONLY_V1
#undef XAR_CK3_ENABLE_ARTIFACT_PERSONAL_USE_PRIVATE_V1
#undef XAR_CK3_ENABLE_G2_PLAYER_GHW_PERMISSIONS_READONLY_V1
#undef XAR_CK3_ENABLE_CHARACTER_SKILL_EFFECTS12004_PRIVATE_QUERY_V1
#undef XAR_CK3_ENABLE_PLAYER_INVENTORY_WINDOW_OPEN_PRIVATE_V1
#if XAR_B11_PROFILE_MASK & 1
#define XAR_CK3_ENABLE_G2_PLAYER_ARTIFACT_PERSONAL_USE_READONLY_V1 1
#endif
#if XAR_B11_PROFILE_MASK & 2
#define XAR_CK3_ENABLE_ARTIFACT_PERSONAL_USE_PRIVATE_V1 1
#endif
#if XAR_B11_PROFILE_MASK & 4
#define XAR_CK3_ENABLE_G2_PLAYER_GHW_PERMISSIONS_READONLY_V1 1
#endif
#if XAR_B11_PROFILE_MASK & 8
#define XAR_CK3_ENABLE_CHARACTER_SKILL_EFFECTS12004_PRIVATE_QUERY_V1 1
#endif
#if XAR_B11_PROFILE_MASK & 16
#define XAR_CK3_ENABLE_PLAYER_INVENTORY_WINDOW_OPEN_PRIVATE_V1 1
#endif
namespace b11_qualification {
inline constexpr unsigned CompiledMask() noexcept {
  unsigned result=0;
#if defined(XAR_CK3_ENABLE_G2_PLAYER_ARTIFACT_PERSONAL_USE_READONLY_V1)
  result|=1;
#endif
#if defined(XAR_CK3_ENABLE_ARTIFACT_PERSONAL_USE_PRIVATE_V1)
  result|=2;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_GHW_PERMISSIONS_READONLY_V1)
  result|=4;
#endif
#if defined(XAR_CK3_ENABLE_CHARACTER_SKILL_EFFECTS12004_PRIVATE_QUERY_V1)
  result|=8;
#endif
#if defined(XAR_CK3_ENABLE_PLAYER_INVENTORY_WINDOW_OPEN_PRIVATE_V1)
  result|=16;
#endif
  return result;
}
static_assert(CompiledMask()==XAR_B11_PROFILE_MASK);
}
