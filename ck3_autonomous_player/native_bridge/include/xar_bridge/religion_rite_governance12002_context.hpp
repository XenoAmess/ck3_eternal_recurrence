#pragma once

#include "xar_bridge/religion_rite_governance12002_state_rite.hpp"
#include "xar_bridge/religion_rite_governance12002_head.hpp"
#include "xar_bridge/religion_rite_governance12002_organization.hpp"

namespace xar::ck3_12002::religion::governance {

struct Bindings {
  bool enabled = false;
  CoreBindings core{};
  state_rite::Bindings state_rite{};
  head::Bindings heads{};
  organization::Bindings organization{};
};

enum class Failure {
  none, bindings_unavailable, played_character_unavailable, frame_not_paused,
  state_changed, components_unavailable,
};

struct Context {
  // Availability means at least one actual component was observed. Components
  // keep their own status, so a failed head lookup cannot hide observed state Rite.
  bool available = false;
  bool frame_available = false;
  Failure failure = Failure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  state_rite::Context state_rite{};
  head::Context heads{};
  organization::Counts organization{};
};

Bindings BindRiteGovernanceImage12002(std::uintptr_t module_base,
                                     std::string_view executable_sha256) noexcept;
bool ReadPlayedRiteGovernance12002(const Bindings &, std::uint64_t capture_epoch,
                                  Context &) noexcept;
const char *RiteGovernanceFailureKey(Failure) noexcept;
std::string SerializePlayedRiteGovernance12002(const Context &);

} // namespace xar::ck3_12002::religion::governance
