#pragma once
#include <atomic>

namespace xar::ck3_12003 {
struct NormalExitAutosaveV1 {
  bool state_available = false, control_visible = false, control_enabled = false;
  bool should_save = false, disable_claimed = false;
  bool dispatch_invoked = false, postcondition_observed = false;
  friend bool operator==(const NormalExitAutosaveV1 &, const NormalExitAutosaveV1 &) = default;
};

// The owner/source/frame/signature gates precede this fixed semantic policy.
// A false state never invokes ToggleShouldSave. An unknown callback remains
// consumed, even after a later query/reconnect. No caller supplies a setting.
template<class Read, class Toggle>
bool DisableNormalExitAutosaveV1(std::atomic<bool> &claim,
    const NormalExitAutosaveV1 &expected, Read read, Toggle toggle,
    NormalExitAutosaveV1 &out) {
  out = {};
  if (!read(out) || out != expected || !out.state_available ||
      !out.control_visible || !out.control_enabled) return false;
  if (!out.should_save) {
    out.disable_claimed = claim.load();
    out.postcondition_observed = true;
    return true;
  }
  bool unclaimed = false;
  if (!claim.compare_exchange_strong(unclaimed, true)) {
    out.disable_claimed = true;
    return false;
  }
  out.disable_claimed = true;
  out.dispatch_invoked = true;
  if (!toggle()) return false;
  NormalExitAutosaveV1 after{};
  if (!read(after)) return false;
  out.state_available = after.state_available;
  out.control_visible = after.control_visible;
  out.control_enabled = after.control_enabled;
  out.should_save = after.should_save;
  out.postcondition_observed = after.state_available && after.control_visible &&
      after.control_enabled && !after.should_save;
  return out.postcondition_observed;
}
} // namespace xar::ck3_12003
