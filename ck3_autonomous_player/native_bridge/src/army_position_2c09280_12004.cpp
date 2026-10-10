#include "xar_bridge/army_position_2c09280_12004.hpp"
#include "xar_bridge/army_position_helper_2c09360_12004.hpp"
#include "xar_bridge/army_position_relation_28bc250_12004.hpp"
#include "xar_bridge/army_position_selected_actor_12004.hpp"
#include <limits>

namespace xar::ck3_12004 {
namespace {
constexpr std::uintptr_t kWarManagerRva = 0x5D1DE58;
constexpr std::uintptr_t kWarFallbackRva = 0x5D1DE40;
constexpr std::uint32_t kCharacterTag = 0x43686172;

template <class T>
bool ReadField(const ArmyRegularCoreReadonlyAccess12004 &access,
               std::uintptr_t identity, std::uintptr_t offset,
               std::optional<T> &value,
               std::vector<ArmyPositionOperandFailure12004> &failures,
               const char *field) noexcept {
  if (identity == 0 || offset > std::numeric_limits<std::uintptr_t>::max() - identity) {
    failures.push_back({field, "null_identity_or_address_overflow"});
    return false;
  }
  T raw{};
  if (access.read == nullptr || !access.read(access.read_context, identity + offset, &raw, sizeof raw)) {
    failures.push_back({field, "guarded_read_failed"});
    return false;
  }
  value = raw;
  return true;
}

ArmyRegularCoreReadonlyPredicate12004 Missing(
    const char *field, const std::vector<ArmyPositionOperandFailure12004> &failures) noexcept {
  for (const auto &failure : failures) {
    if (failure.field == field) return {std::nullopt, failure.field + ":" + failure.reason};
  }
  return {std::nullopt, std::string(field) + ":unavailable"};
}
} // namespace

ArmyPositionWarOperands12004 ReadArmyPositionWarOperands12004(
    const ArmyRegularCoreReadonlyAccess12004 &access, std::int32_t full_war_id,
    std::uintptr_t optional_war_identity) noexcept {
  ArmyPositionWarOperands12004 out;
  out.full_war_id = full_war_id;
  out.optional_war_identity = optional_war_identity;
  if (full_war_id == -1) return out;
  if (!ReadField(access, access.image_base, kWarManagerRva, out.manager_identity,
                 out.failures, "war_manager_identity")) return out;
  bool fallback = *out.manager_identity == 0;
  const auto index = static_cast<std::uint32_t>(full_war_id) & 0x00FFFFFFU;
  if (!fallback) {
    if (!ReadField(access, *out.manager_identity, 0x2C, out.capacity,
                   out.failures, "war_capacity")) return out;
    fallback = index >= *out.capacity;
    if (!fallback) {
      if (!ReadField(access, *out.manager_identity, 0x20, out.table_identity,
                     out.failures, "war_table_identity")) return out;
      const auto row_offset = static_cast<std::uintptr_t>(index) * 16U + 8U;
      if (!ReadField(access, *out.table_identity, row_offset, out.row_war_identity,
                     out.failures, "row_war_identity")) return out;
      fallback = *out.row_war_identity == 0;
      if (!fallback) {
        if (!ReadField(access, *out.row_war_identity, 8, out.row_full_war_id,
                       out.failures, "row_full_war_id")) return out;
        fallback = *out.row_full_war_id != static_cast<std::uint32_t>(full_war_id);
      }
    }
  }
  out.fallback_used = fallback;
  if (fallback) {
    if (!ReadField(access, access.image_base, kWarFallbackRva, out.fallback_war_identity,
                   out.failures, "fallback_war_identity")) return out;
    out.resolved_war_identity = out.fallback_war_identity;
  } else {
    out.resolved_war_identity = out.row_war_identity;
  }
  ReadField(access, *out.resolved_war_identity, 0x358, out.ended_byte,
            out.failures, "war_ended_byte");
  return out;
}

ArmyRegularCoreReadonlyPredicate12004 EvaluateArmyPositionWarGate12004(
    const ArmyPositionWarOperands12004 &in) noexcept {
  if (in.full_war_id == -1) return {false, {}};
  if (!in.resolved_war_identity || *in.resolved_war_identity == 0) {
    if (!in.failures.empty()) return {std::nullopt, in.failures.front().field + ":" + in.failures.front().reason};
    return Missing("resolved_war_identity", in.failures);
  }
  if (!in.ended_byte) return Missing("war_ended_byte", in.failures);
  if (*in.ended_byte != 0) return {false, {}};
  return {in.optional_war_identity == 0 || in.optional_war_identity == *in.resolved_war_identity, {}};
}

ArmyRegularCoreReadonlyPredicate12004 ReadArmyPositionWarGate12004(
    const ArmyRegularCoreReadonlyAccess12004 &access, std::int32_t full_war_id,
    std::uintptr_t optional_war_identity) noexcept {
  return EvaluateArmyPositionWarGate12004(
      ReadArmyPositionWarOperands12004(access, full_war_id, optional_war_identity));
}

ArmyPosition2C09280Operands12004 ReadArmyPosition2C09280Operands12004(
    const ArmyRegularCoreReadonlyAccess12004 &access, std::uintptr_t actor,
    std::uintptr_t holder, std::uintptr_t optional_war_identity) noexcept {
  ArmyPosition2C09280Operands12004 out;
  out.original_actor_identity = actor;
  out.holder_identity = holder;
  out.optional_war_identity = optional_war_identity;
  const auto criterion = ReadArmyPosition2C0936012004(access, holder, actor, optional_war_identity);
  out.criterion_result = criterion.value;
  if (!criterion.value) {
    out.failures.push_back({"criterion_result", criterion.unavailable_reason});
    return out;
  }
  out.selected_actor_identity = actor;
  if (!*criterion.value) {
    const auto selected = ReadArmyPositionSelectedActor2C0FEC012004(access, actor, holder, optional_war_identity);
    out.selected_actor_identity = selected.selected_actor_identity;
    if (!out.selected_actor_identity) {
      out.failures.push_back({"selected_actor_identity", selected.unavailable_reason});
      return out;
    }
  }
  if (!ReadField(access, *out.selected_actor_identity, 0x1C, out.selected_actor_tag,
                 out.failures, "selected_actor_tag") || *out.selected_actor_tag != kCharacterTag) return out;
  if (!ReadField(access, *out.selected_actor_identity, 0x18, out.selected_actor_full_id,
                 out.failures, "selected_actor_full_id") || *out.selected_actor_full_id == 0xFFFFFFFFU) return out;
  if (!ReadField(access, holder, 0x18, out.holder_full_id,
                 out.failures, "holder_full_id") || *out.holder_full_id == *out.selected_actor_full_id) return out;
  const auto relation = ReadArmyPositionRelation28BC25012004(access, holder, *out.selected_actor_identity);
  out.relation_identity = relation.relation_identity;
  out.relation_full_war_id = relation.war_id;
  if (!out.relation_full_war_id) {
    out.failures.push_back({"relation_full_war_id", relation.unavailable_reason});
    return out;
  }
  out.war = ReadArmyPositionWarOperands12004(access, *out.relation_full_war_id, optional_war_identity);
  return out;
}

ArmyRegularCoreReadonlyPredicate12004 EvaluateArmyPosition2C0928012004(
    const ArmyPosition2C09280Operands12004 &in) noexcept {
  if (!in.criterion_result) return Missing("criterion_result", in.failures);
  if (!in.selected_actor_identity) return Missing("selected_actor_identity", in.failures);
  if (!in.selected_actor_tag) return Missing("selected_actor_tag", in.failures);
  if (*in.selected_actor_tag != kCharacterTag) return {false, {}};
  if (!in.selected_actor_full_id) return Missing("selected_actor_full_id", in.failures);
  if (*in.selected_actor_full_id == 0xFFFFFFFFU) return {false, {}};
  if (!in.holder_full_id) return Missing("holder_full_id", in.failures);
  if (*in.holder_full_id == *in.selected_actor_full_id) return {false, {}};
  if (!in.relation_full_war_id) return Missing("relation_full_war_id", in.failures);
  if (*in.relation_full_war_id == -1) return {false, {}};
  if (!in.war || in.war->full_war_id != *in.relation_full_war_id ||
      in.war->optional_war_identity != in.optional_war_identity) return Missing("war_operands", in.failures);
  return EvaluateArmyPositionWarGate12004(*in.war);
}

ArmyRegularCoreReadonlyPredicate12004 ReadArmyPosition2C0928012004(
    const ArmyRegularCoreReadonlyAccess12004 &access, std::uintptr_t actor,
    std::uintptr_t holder, std::uintptr_t optional_war_identity) noexcept {
  return EvaluateArmyPosition2C0928012004(
      ReadArmyPosition2C09280Operands12004(access, actor, holder, optional_war_identity));
}
} // namespace xar::ck3_12004
