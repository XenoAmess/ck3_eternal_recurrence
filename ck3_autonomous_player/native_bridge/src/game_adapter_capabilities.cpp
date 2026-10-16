#include "xar_bridge/game_adapter.hpp"

namespace xar::game {

bool GameAdapter::supports(std::string_view capability) const noexcept {
  if (!enabled()) {
    return false;
  }
  for (const auto candidate : descriptor().capabilities) {
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
