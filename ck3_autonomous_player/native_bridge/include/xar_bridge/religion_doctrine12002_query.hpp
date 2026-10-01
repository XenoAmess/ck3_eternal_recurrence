#pragma once

#include "xar_bridge/religion_doctrine12002_intrinsic.hpp"
#include "xar_bridge/religion_doctrine12002_rite.hpp"
#include "xar_bridge/religion_doctrine12002_tenet.hpp"

namespace xar::ck3_12002::religion::doctrine12002 {

struct CurrentDoctrineBindings {
  religion::Bindings context{};
  TenetParameterBindings parameters{};
};

// Both native doctrine scopes and both native boolean-parameter scopes are
// preserved. No guessed intrinsic/effective merge or choices model is added.
struct CurrentDoctrineContext {
  bool available = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  RiteDoctrineSnapshot current_rite{};
  FaithMainRiteDoctrines faith_main_rite{};
  TenetParameterContext boolean_parameters{};
};

CurrentDoctrineBindings BindCurrentDoctrineImage12002(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;
bool ReadPlayedCurrentDoctrines12002(const CurrentDoctrineBindings &bindings,
    std::uint64_t capture_epoch, CurrentDoctrineContext &output) noexcept;
std::string SerializePlayedCurrentDoctrines12002(const CurrentDoctrineContext &value);

} // namespace xar::ck3_12002::religion::doctrine12002
