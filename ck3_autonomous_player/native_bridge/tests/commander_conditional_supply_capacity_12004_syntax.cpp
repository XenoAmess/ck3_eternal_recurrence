#include "xar_bridge/ck3_12004_commander_conditional_supply_capacity.hpp"
#include <limits>
#include <type_traits>
using namespace xar::ck3_12004;
static_assert(CommanderCapacityFixedMul12004(30000000, 100000) == 30000000);
static_assert(CommanderCapacityFixedMul12004(100001, -1) == -1);
static_assert(CommanderCapacityFixedMul12004(-30000000, 50000) == -15000000);
static_assert(CommanderCapacityFixedMul12004(0, std::numeric_limits<std::int64_t>::min()) == 0);
static_assert(CommanderCapacityFixedMul12004(std::numeric_limits<std::int64_t>::min(), 100000) == std::numeric_limits<std::int64_t>::min());
static_assert(CommanderCapacityFixedMul12004(std::numeric_limits<std::int64_t>::max(), std::numeric_limits<std::int64_t>::max()) == std::numeric_limits<std::int64_t>::min());
static_assert(CapacityWrapAdd12004(std::numeric_limits<std::int64_t>::max(), 1) == std::numeric_limits<std::int64_t>::min());
static_assert(CapacityWrapSub12004(std::numeric_limits<std::int64_t>::min(), 1) == std::numeric_limits<std::int64_t>::max());
static_assert(std::is_same_v<CommanderCapacityModifierReader12004,
    std::int64_t *(*)(void *, std::int64_t *, std::int32_t)>);
