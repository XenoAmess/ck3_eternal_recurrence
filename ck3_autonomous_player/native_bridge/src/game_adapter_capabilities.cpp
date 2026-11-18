#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/ck3_1210_read_wire_registry_v1.hpp"

namespace xar::game {

bool GameAdapter::supports(std::string_view capability) const noexcept {
  if (!enabled()) {
    return false;
  }
  // These versioned read protocols have producers only in the exact Florin
  // adapter. A copied capability string cannot qualify another descriptor.
  bool florin_read = false;
  for (const auto &read : ck3_1210::kReadWireContractsV1)
    if (read.capability == capability) { florin_read = true; break; }
  const auto &identity = descriptor();
  if (florin_read && (identity.adapter_id != ck3_1210::kAdapterId ||
      identity.game_version != ck3_1210::kGameVersion ||
      identity.executable_sha256 != ck3_1210::kExecutableSha256)) return false;
  for (const auto candidate : identity.capabilities) {
    if (candidate == capability) {
      return true;
    }
  }
  return false;
}

bool GameAdapter::supports_snapshot() const noexcept {
  return supports("game.state.snapshot");
}

} // namespace xar::game
