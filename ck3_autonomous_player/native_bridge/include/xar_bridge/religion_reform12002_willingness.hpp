#pragma once

#include "xar_bridge/ck3_12002.hpp"

#include <cstddef>
#include <cstdint>

namespace xar::ck3_12002::religion_reform {

inline constexpr std::uintptr_t kFaithMainRiteGetterRva = 0x2444360;
inline constexpr std::uintptr_t kFaithIsUnreformedGetterRva = 0x2BD8960;
inline constexpr std::size_t kFaithMainRiteIdOffset = 0x98;
inline constexpr std::size_t kObjectFullReferenceOffset = 0x08;
inline constexpr std::size_t kRiteUnreformedOffset = 0x8B0;
inline constexpr std::uint32_t kAbsentFullReference = 0xFFFFFFFFU;

using MainRiteGetter = void *(*)(void *faith);
using IsUnreformedGetter = bool (*)(void *faith);

struct MainRiteBindings {
  bool enabled = false;
  MainRiteGetter main_rite = nullptr;
  IsUnreformedGetter is_unreformed = nullptr;
};

enum class MainRiteStatus {
  observed,
  bindings_unavailable,
  faith_unavailable,
  main_rite_unavailable,
  state_changed,
};

struct MainRiteUnreformed {
  MainRiteStatus status = MainRiteStatus::bindings_unavailable;
  std::uint32_t faith_id = kAbsentFullReference;
  std::uint32_t main_rite_id = kAbsentFullReference;
  bool is_unreformed = false;
};

MainRiteBindings BindFaithMainRiteUnreformedImage12002(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// A paused application-main owner supplies the resolved Faith and full identity.
// This is the existing Faith.IsUnreformed value consumed by the vanilla AI
// reform handler. It is neither a final CanReform gate nor a willingness score.
MainRiteUnreformed ReadFaithMainRiteUnreformed12002(
    const MainRiteBindings &bindings, void *faith,
    std::uint32_t expected_faith_id) noexcept;

} // namespace xar::ck3_12002::religion_reform
