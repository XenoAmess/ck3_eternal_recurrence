#include "xar_bridge/ck3_12004_county_relation_inputs_reader.hpp"
#include "xar_bridge/army_position_relation_28bc250_12004.hpp"
#include "xar_bridge/army_position_2c09280_12004.hpp"
#include <limits>

namespace xar::ck3_12004 {
std::optional<std::uint32_t> ReadCountyRelationFullId12004(
    const ArmyRegularCoreReadonlyAccess12004 &access,
    std::uintptr_t identity) noexcept {
  std::uint32_t value = 0;
  if (!access.read || !identity ||
      identity > std::numeric_limits<std::uintptr_t>::max() - 0x18 ||
      !access.read(access.read_context, identity + 0x18, &value, sizeof(value)))
    return std::nullopt;
  return value;
}

game::ArmyCountyRelationInputsV1 ReadCountyRelationInputs12004(
    const ArmyRegularCoreReadonlyAccess12004 &access, std::uintptr_t receiver,
    std::uintptr_t actor, std::uintptr_t auxiliary) noexcept {
  game::ArmyCountyRelationInputsV1 out{};
  out.auxiliary_identity = auxiliary;
  out.receiver_full_id = ReadCountyRelationFullId12004(access, receiver);
  out.actor_full_id = ReadCountyRelationFullId12004(access, actor);
  if (!out.receiver_full_id || !out.actor_full_id) {
    out.sampled_relation_unavailable_reason = "county_relation_full_ids_unreadable";
    return out;
  }
  if (out.receiver_full_id == out.actor_full_id) {
    // Held 2C0963B..63E returns false before its first pair lookup.
    out.sampled_relation_unavailable_reason = "same_full_id_precedes_relation_lookup";
    return out;
  }
  const auto relation = ReadArmyPositionRelation28BC25012004(access, receiver, actor);
  out.sampled_relation_identity = relation.relation_identity;
  out.sampled_relation_full_war_id = relation.war_id;
  if (!relation.war_id) {
    out.sampled_relation_unavailable_reason = relation.unavailable_reason;
    return out;
  }
  if (*relation.war_id == -1) {
    out.sampled_relation_available = true;
    out.sampled_direct_war_gate = false;
    out.sampled_relation_unavailable_reason.clear();
    return out;
  }
  // Existing pure reader performs the full ID/generation check and fallback
  // selected by the held body. +358 is retained as a raw byte here.
  const auto war = ReadArmyPositionWarOperands12004(access, *relation.war_id, auxiliary);
  out.sampled_selected_war_identity = war.resolved_war_identity;
  out.sampled_selected_war_used_fallback = war.fallback_used;
  out.sampled_selected_war_byte_358_u8 = war.ended_byte;
  if (!war.resolved_war_identity || *war.resolved_war_identity == 0 || !war.ended_byte) {
    out.sampled_relation_unavailable_reason = war.failures.empty()
        ? "county_relation_selected_war_or_byte358_unavailable"
        : war.failures.front().field + ":" + war.failures.front().reason;
    return out;
  }
  out.sampled_direct_war_matches_aux = auxiliary == 0 ||
      auxiliary == *war.resolved_war_identity;
  out.sampled_direct_war_gate = *war.ended_byte == 0 &&
      *out.sampled_direct_war_matches_aux;
  out.sampled_relation_available = true;
  out.sampled_relation_unavailable_reason.clear();
  return out;
}
}
