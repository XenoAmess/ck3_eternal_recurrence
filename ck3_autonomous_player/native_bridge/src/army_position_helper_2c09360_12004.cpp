#include "xar_bridge/army_position_helper_2c09360_12004.hpp"
#include "xar_bridge/army_position_2c09280_12004.hpp"
#include "xar_bridge/army_position_relation_28bc250_12004.hpp"
#include "xar_bridge/army_position_same_war_side_12004.hpp"
#include <limits>

namespace xar::ck3_12004 {
namespace {

bool ReadCharacterId(const ArmyRegularCoreReadonlyAccess12004 &access,
    std::uintptr_t object, std::int32_t &value) noexcept {
  constexpr std::uintptr_t offset = 0x18;
  if (access.read == nullptr || object == 0 ||
      object > std::numeric_limits<std::uintptr_t>::max() - offset) return false;
  return access.read(access.read_context, object + offset, &value, sizeof(value));
}

ArmyRegularCoreReadonlyPredicate12004 Missing(const char *reason) {
  return {std::nullopt, reason};
}

} // namespace

ArmyRegularCoreReadonlyPredicate12004 ReadArmyPosition2C0936012004(
    const ArmyRegularCoreReadonlyAccess12004 &access,
    std::uintptr_t holder, std::uintptr_t actor,
    std::uintptr_t optional_war_identity) noexcept {
  try {
    std::int32_t holder_id = 0;
    std::int32_t actor_id = 0;
    // 2C09370..379: this return precedes the first delegated predicate.
    if (!ReadCharacterId(access, holder, holder_id))
      return Missing("2C09360 initial holder full Character ID unavailable");
    if (!ReadCharacterId(access, actor, actor_id))
      return Missing("2C09360 initial actor full Character ID unavailable");
    if (holder_id == actor_id) return {true, {}};

    // 2C09383: literal direction is holder -> actor, R8 is the original filter.
    const auto prefix = ReadArmyPosition2C090D012004(
        access, holder, actor, optional_war_identity);
    if (!prefix.value.has_value()) return prefix;
    if (*prefix.value) return {true, {}};

    // Native code reloads both fields after the prefix. Keep the read order.
    if (!ReadCharacterId(access, actor, actor_id))
      return Missing("2C09360 reloaded actor full Character ID unavailable");
    if (!ReadCharacterId(access, holder, holder_id))
      return Missing("2C09360 reloaded holder full Character ID unavailable");
    if (holder_id == actor_id) return {false, {}};

    const auto relation = ReadArmyPositionRelation28BC25012004(access, holder, actor);
    if (!relation.war_id.has_value())
      return {std::nullopt, relation.unavailable_reason.empty()
          ? "2C09360 reached relation full War ID unavailable"
          : relation.unavailable_reason};
    // 2C093AF..401 exactly matches 16b's source-bound resolution/end/filter gate.
    // Null R8 skips only pointer equality after a readable, non-ended War.
    return ReadArmyPositionWarGate12004(access, *relation.war_id,
        optional_war_identity);
  } catch (...) {
    return Missing("2C09360 guarded conditional projection failed");
  }
}

} // namespace xar::ck3_12004
