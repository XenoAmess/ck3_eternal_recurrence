#include "xar_bridge/religion_rite_governance12002_context.hpp"

namespace xar::ck3_12002::religion::governance {
namespace {
bool SamePlayerFrame(const CoreSnapshotPrefix &a,
                     const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.paused == b.clock.paused &&
      a.clock.speed == b.clock.speed && a.local_player_id == b.local_player_id &&
      a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id &&
      a.played_character_alive == b.played_character_alive;
}
template <typename Component>
bool ComponentHasPlayerFrame(const Component &part,
                            const CoreSnapshotPrefix &frame) noexcept {
  return !part.available ||
      (static_cast<std::uint32_t>(part.played_character_id) ==
          static_cast<std::uint32_t>(frame.played_character_id) &&
       part.date_raw == frame.clock.date_raw);
}
const char *Bool(bool value) noexcept { return value ? "true" : "false"; }
} // namespace

Bindings BindRiteGovernanceImage12002(std::uintptr_t module_base,
                                     std::string_view executable_sha256) noexcept {
  Bindings result{};
  result.core = BindCoreImage(module_base, executable_sha256);
  result.state_rite = state_rite::BindStateRiteImage12002(module_base, executable_sha256);
  result.heads = head::BindRiteHeadsImage12002(module_base, executable_sha256);
  result.organization = organization::BindOrganizationImage12002(module_base, executable_sha256);
  result.enabled = result.core.enabled;
  return result;
}

bool ReadPlayedRiteGovernance12002(const Bindings &bindings,
    std::uint64_t capture_epoch, Context &output) noexcept {
  output = {};
  output.capture_epoch = capture_epoch;
  if (!bindings.enabled || !bindings.core.enabled) return false;
  CoreSnapshotPrefix before{};
  if (!ReadCoreSnapshot(bindings.core, before) || !before.map_ready ||
      !before.has_played_character || !before.played_character_alive) {
    output.failure = Failure::played_character_unavailable; return false;
  }
  output.date_raw = before.clock.date_raw;
  output.played_character_id = before.played_character_id;
  if (!before.clock.paused) {
    output.failure = Failure::frame_not_paused; return false;
  }
  (void)state_rite::ReadPlayedStateRite12002(bindings.state_rite, capture_epoch, output.state_rite);
  (void)head::ReadPlayedRiteHeads12002(bindings.heads, capture_epoch, output.heads);
  (void)organization::ReadPlayedOrganizationCounts12002(
      bindings.organization, capture_epoch, output.organization);
  CoreSnapshotPrefix after{};
  if (!ReadCoreSnapshot(bindings.core, after) || !SamePlayerFrame(before, after) ||
      !ComponentHasPlayerFrame(output.state_rite, before) ||
      !ComponentHasPlayerFrame(output.heads, before) ||
      !ComponentHasPlayerFrame(output.organization, before)) {
    output = {};
    output.capture_epoch = capture_epoch;
    output.failure = Failure::state_changed;
    return false;
  }
  output.frame_available = true;
  output.available = output.state_rite.available || output.heads.available ||
      output.organization.available;
  output.failure = output.available ? Failure::none : Failure::components_unavailable;
  return output.available;
}

const char *RiteGovernanceFailureKey(Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::bindings_unavailable: return "bindings_unavailable";
  case Failure::played_character_unavailable: return "played_character_unavailable";
  case Failure::frame_not_paused: return "frame_not_paused";
  case Failure::state_changed: return "state_changed";
  case Failure::components_unavailable: return "components_unavailable";
  }
  return "unavailable";
}

std::string SerializePlayedRiteGovernance12002(const Context &value) {
  const unsigned observed = static_cast<unsigned>(value.state_rite.available) +
      static_cast<unsigned>(value.heads.available) +
      static_cast<unsigned>(value.organization.available);
  return "{\"schema\":\"ck3_12002_player_rite_governance_v1\",\"available\":" +
      std::string(Bool(value.available)) + ",\"frame_available\":" + Bool(value.frame_available) +
      ",\"unavailable_reason\":\"" + RiteGovernanceFailureKey(value.failure) +
      "\",\"capture_epoch\":" + std::to_string(value.capture_epoch) +
      ",\"date_raw\":" + std::to_string(value.date_raw) +
      ",\"played_character_id\":" + std::to_string(value.played_character_id) +
      ",\"observed_components\":" + std::to_string(observed) +
      ",\"all_components_available\":" + Bool(observed == 3) +
      ",\"state_rite\":" + state_rite::SerializePlayedStateRite12002(value.state_rite) +
      ",\"heads\":" + head::SerializePlayedRiteHeads12002(value.heads) +
      ",\"organization\":" + organization::SerializePlayedOrganizationCounts12002(value.organization) + "}";
}
} // namespace xar::ck3_12002::religion::governance
