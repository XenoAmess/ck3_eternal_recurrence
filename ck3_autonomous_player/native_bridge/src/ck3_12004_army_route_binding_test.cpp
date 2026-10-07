#include "xar_bridge/ck3_12004_army.hpp"
#include "xar_bridge/ck3_12004_army_support.hpp"
#include "xar_bridge/ck3_12004_routes.hpp"

#include <iostream>
#include <stdexcept>

namespace {
void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
} // namespace

int main() {
  try {
    namespace current = xar::ck3_12004;
    constexpr std::uintptr_t base = 0x140000000ULL;
    // Both complete production constructors must return. No mapped pointer is
    // dereferenced and no callback into CK3 is executed by this fixture.
    const auto army = current::BindArmyImage12004(base, current::kExecutableSha256);
    const auto route = current::BindRouteImage12004(base, current::kExecutableSha256);
    Check(army.enabled && route.enabled, "actual4 army and route construction must finish enabled");
    Check(route.army_storage_slot == army.unit_storage_slot,
          "route must retain the same army storage binding");
    const auto speed = base + current::kCommanderCurrentEdgeMovementRateRva12004;
    Check(reinterpret_cast<std::uintptr_t>(army.get_unit_current_edge_movement_rate) == speed &&
          reinterpret_cast<std::uintptr_t>(route.read_unit_current_edge_speed) == speed,
          "army and route must bind the same current edge speed leaf");
    Check(!current::BindArmyImage12004(0, current::kExecutableSha256).enabled &&
          !current::BindRouteImage12004(0, current::kExecutableSha256).enabled,
          "zero base must remain unavailable");
    Check(!current::BindArmyImage12004(base, "wrong executable").enabled &&
          !current::BindRouteImage12004(base, "wrong executable").enabled,
          "wrong executable identity must remain unavailable");
    std::cout << "actual4 army and route constructors completed; current edge speed preserved\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
