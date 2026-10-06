#pragma once

#include "xar_bridge/game_contract.hpp"
#include "xar_bridge/army_daily_assault_active_table_collector_v1.inc.hpp"

namespace xar::ck3_12003 {
struct CurrentAssaultRemovalReferenceBindings12003 {
  bool enabled = false;
  CurrentDailyAssaultTableBindings12003 lookup{};
};
inline CurrentAssaultRemovalReferenceBindings12003 BindCurrentAssaultRemovalReference12003(
    std::uintptr_t base, std::string_view executable_sha256) noexcept {
  CurrentAssaultRemovalReferenceBindings12003 out{};
  out.lookup = BindCurrentDailyAssaultTable12003(base, executable_sha256);
  out.enabled = out.lookup.enabled;
  return out;
}
game::ArmyCurrentAssaultRemovalReferenceInputsV1 ReadCurrentAssaultRemovalReferenceInputs12003(
    const CurrentAssaultRemovalReferenceBindings12003 &bindings,
    const game::ArmyDailyQueueInputsV1 *existing_queue,
    const game::ArmyFirstRemovalCleanupInputsV1 *existing_global_context,
    const game::ArmyCurrentDailyAssaultTableV1 *current_table) noexcept;
} // namespace xar::ck3_12003
