#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/ck3_1210_read_wire_registry_v1.hpp"

namespace xar::game {

bool GameAdapter::supports(std::string_view capability) const noexcept {
  if (!enabled()) {
    return false;
  }
  // These versioned read protocols have producers only in the exact Florin
  // adapter. A copied capability string cannot qualify another descriptor.
  const auto &identity=descriptor();
  const ck3_1210::ReadWireBuildIdentityV1 build{identity.adapter_id,identity.game_version,identity.executable_sha256};
  for(const auto &read:ck3_1210::kReadWireContractsV1)
    if(read.capability==capability && !ck3_1210::FindReadWireContractV1(build,read.step))return false;
  for(const auto &read:ck3_1210::kOpeningReadWireContracts56)
    if(read.capability==capability && !ck3_1210::FindReadWireContractV1(
        {identity.adapter_id,identity.game_version,identity.executable_sha256},read.step))return false;
  if((capability==ck3_1210::kActiveWarsHotfixCapability58 || capability==ck3_1210::kArmyBaseHotfixFullCapability58) &&
     (identity.adapter_id!=ck3_1210::hotfix26757580::kAdapterId || identity.game_version!=ck3_1210::kGameVersion ||
      identity.executable_sha256!=ck3_1210::hotfix26757580::kExecutableSha256))return false;
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
