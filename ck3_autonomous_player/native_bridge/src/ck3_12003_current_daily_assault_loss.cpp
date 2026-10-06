#include "xar_bridge/ck3_12003_current_daily_assault_loss.hpp"
#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12003_army_replenishment_records.hpp"
#include <algorithm>
#include <bit>
#include <utility>

namespace xar::ck3_12003 {
namespace {
using namespace daily_assault_table_detail;
std::int32_t Signed(std::uint32_t id) { return std::bit_cast<std::int32_t>(id); }

game::ArmyDailyAssaultLossRegimentV1 ReadCountRegiment(
    const CurrentDailyAssaultTableBindings12003 &b, std::int32_t index,
    std::optional<std::uint32_t> raw) {
  game::ArmyDailyAssaultLossRegimentV1 out{};
  out.native_index = index; out.raw_full_id_u32 = raw;
  const auto resolved = Resolve(b, b.arrg_registry_slot, b.arrg_fallback_slot, raw, 0x10);
  out.resolution = resolved.observation;
  if (!out.resolution.ready) return out;
  const auto magic = Read<std::uint32_t>(b, resolved.object, 0x14);
  if (!magic) return out;
  out.identity_valid = *magic == 0x41725267U && *out.resolution.selected_full_id_u32 != 0xFFFFFFFFU;
  if (!*out.identity_valid) return out;
  out.current_soldiers = Read<std::int32_t>(b, resolved.object, 0x38);
  out.maximum_soldiers = Read<std::int32_t>(b, resolved.object, 0x3C);
  return out;
}

game::ArmyDailyAssaultLossTargetV1 ReadTarget(
    const ck3_12002::ArmyBindings &bindings, std::optional<std::uint32_t> raw) {
  const auto &b = bindings.current_daily_assault_table_bindings;
  game::ArmyDailyAssaultLossTargetV1 out{};
  auto resolved = Resolve(b, b.arrg_registry_slot, b.arrg_fallback_slot, raw, 0x10);
  out.resolution = resolved.observation;
  const auto fail = [&](const char *reason) { out.unavailable_reason = reason; Finish(out, false); return out; };
  if (!resolved.observation.ready) return fail("daily_assault_loss_target_unresolved");
  const auto magic = Read<std::uint32_t>(b, resolved.object, 0x14);
  if (!magic) return fail("daily_assault_loss_target_magic_unavailable");
  out.identity_valid = *magic == 0x41725267U && *out.resolution.selected_full_id_u32 != 0xFFFFFFFFU;
  if (!*out.identity_valid) { Finish(out, true); return out; }
  out.current_soldiers = Read<std::int32_t>(b, resolved.object, 0x38);
  out.maximum_soldiers = Read<std::int32_t>(b, resolved.object, 0x3C);
  if (!out.current_soldiers || !out.maximum_soldiers) return fail("daily_assault_loss_target_counts_unavailable");
  if (!bindings.is_army_regiment_loss_writer_skipped) return fail("daily_assault_loss_writer_admission_unavailable");
  out.native_loss_writer_skipped = bindings.is_army_regiment_loss_writer_skipped(const_cast<void *>(resolved.object));
  // 2634880 exits before DATA/current/refresh. Do not demand unused DATA.
  if (*out.native_loss_writer_skipped) { Finish(out, true); return out; }
  out.replenishment_records_v1 = ReadArmyRegimentReplenishmentRecordsV1(
      bindings, resolved.object, Signed(*out.resolution.selected_full_id_u32));
  const bool data_ready = out.replenishment_records_v1->status == game::ArmyRegimentReplenishmentRecordsStatusV1::available;
  if (!data_ready) return fail("daily_assault_loss_associated_DATA_partial");
  Finish(out, true); return out;
}

game::ArmyDailyAssaultLossArmyCountV1 ReadArmyCount(
    const ck3_12002::ArmyBindings &bindings, const game::ArmyDailyAssaultOccurrenceV1 &occurrence) {
  const auto &b = bindings.current_daily_assault_table_bindings;
  game::ArmyDailyAssaultLossArmyCountV1 out{};
  out.native_index = occurrence.native_index; out.raw_full_id_u32 = occurrence.raw_full_id_u32;
  const auto resolved = Resolve(b, b.army_registry_slot, b.army_fallback_slot, out.raw_full_id_u32, 0x10);
  out.resolution = resolved.observation;
  const auto fail = [&](const char *reason) { out.unavailable_reason = reason; Finish(out, false); return out; };
  if (!resolved.observation.ready) return fail("daily_assault_loss_group_army_unresolved");
  if (!bindings.get_army_current_soldiers) return fail("daily_assault_loss_group_army_count_unbound");
  out.native_whole_current_soldiers = bindings.get_army_current_soldiers(
      const_cast<void *>(At(resolved.object, 0x38)), 0);
  const auto count = Read<std::int32_t>(b, resolved.object, 0x44);
  if (!count) return fail("daily_assault_loss_group_army_roster_count_unavailable");
  if (*count <= 0) { Finish(out, true); return out; }
  const auto ids = Read<const void *>(b, resolved.object, 0x38);
  if (!ids || !*ids) return fail("daily_assault_loss_group_army_roster_unavailable");
  bool complete = true;
  for (std::int32_t i = 0; i < *count; ++i) {
    auto row = ReadCountRegiment(b, i, Read<std::uint32_t>(b, *ids, static_cast<std::size_t>(i) * 4));
    complete = complete && row.resolution.ready && row.identity_valid.has_value() &&
        (!*row.identity_valid || row.current_soldiers.has_value());
    out.regiments.push_back(std::move(row));
  }
  Finish(out, complete);
  if (!complete) out.unavailable_reason = "daily_assault_loss_group_army_roster_partial";
  return out;
}

game::ArmyDailyAssaultLossGroupV1 ReadGroup(
    const ck3_12002::ArmyBindings &bindings, const game::ArmyDailyAssaultGroupV1 &group) {
  const auto &b = bindings.current_daily_assault_table_bindings;
  const auto &native = bindings.current_province_besieging_bindings;
  game::ArmyDailyAssaultLossGroupV1 out{};
  out.native_index = group.native_index; out.physical_slot_i64 = group.physical_slot_i64;
  const auto resolved = Resolve(b, b.siege_registry_slot, b.siege_fallback_slot, group.siege_full_id_u32, 8);
  const auto fail = [&](const char *reason) { out.unavailable_reason = reason; Finish(out, false); return out; };
  if (!resolved.observation.ready) return fail("daily_assault_loss_group_siege_unresolved");
  if (native.assault_expected_loss)
    out.native_current_expected_loss = native.assault_expected_loss(const_cast<void *>(resolved.object));
  const auto province = Read<const void *>(b, resolved.object, 0x200);
  if (!province || !*province) return fail("daily_assault_loss_group_province_unavailable");
  out.province_magic_raw_u32 = Read<std::uint32_t>(b, *province, 0x85C);
  if (!out.province_magic_raw_u32) return fail("daily_assault_loss_group_province_magic_unavailable");
  bool complete = true;
  if (*out.province_magic_raw_u32 == 0x50726F76U) {
    out.besieging_inputs_v1 = ReadCurrentProvinceBesiegingContributors12003(bindings, const_cast<void *>(*province));
    auto &context = out.besieging_inputs_v1->assault_context;
    // Province+788 belongs to its current link. The daily table owns another
    // actual Siege receiver; 25205C0 reads that receiver's +3D8 breach.
    context = {};
    context.has_active_siege = true;
    context.siege_id = Signed(*resolved.observation.selected_full_id_u32);
    context.breach_level_raw = Read<std::int32_t>(b, resolved.object, 0x3D8);
    if (native.casualty_percentage_count)
      context.casualty_percentage_count = Read<std::int32_t>(b, native.casualty_percentage_count);
    const auto percentage_index = context.breach_level_raw
        ? static_cast<std::int64_t>(*context.breach_level_raw) - 1 : -1;
    if (context.casualty_percentage_count && percentage_index >= 0 && percentage_index < *context.casualty_percentage_count) {
      const auto table = Read<const void *>(b, native.casualty_percentage_table_slot);
      if (table && *table) context.casualty_percentage_raw = Read<std::int64_t>(b, *table, static_cast<std::size_t>(percentage_index) * 8);
    }
    const bool context_ready = context.breach_level_raw && context.casualty_percentage_count &&
        (percentage_index < 0 || percentage_index >= *context.casualty_percentage_count || context.casualty_percentage_raw.has_value());
    context.status = context_ready ? "available" : "partial";
    if (!context_ready) context.unavailable_reason = "daily_assault_loss_actual_siege_budget_context_partial";
    out.besieging_inputs_v1->native_assault_expected_loss = out.native_current_expected_loss;
    complete = context_ready && out.besieging_inputs_v1->contributors_ready;
  }
  for (const auto &occurrence : group.armies.occurrences) {
    out.army_counts.push_back(ReadArmyCount(bindings, occurrence));
    complete = complete && out.army_counts.back().ready;
  }
  complete = complete && group.armies.references_ready && out.native_current_expected_loss.has_value();
  Finish(out, complete);
  if (!complete) out.unavailable_reason = "daily_assault_loss_group_operands_partial";
  return out;
}
} // namespace

game::ArmyCurrentDailyAssaultLossInputsV1 ReadCurrentDailyAssaultLossInputs12003(
    const ck3_12002::ArmyBindings &bindings, const game::ArmyCurrentDailyAssaultTableV1 &table) {
  game::ArmyCurrentDailyAssaultLossInputsV1 out{};
  if (!bindings.enabled || !bindings.current_daily_assault_loss_inputs_enabled) {
    out.unavailable_reason = "daily_assault_loss_exact_build_binding_unavailable"; return out;
  }
  bool complete = table.physical_scan_ready && table.raw_groups_ready;
  for (const auto &group : table.groups) {
    out.groups.push_back(ReadGroup(bindings, group));
    complete = complete && out.groups.back().ready;
    for (const auto &occurrence : group.arrgs.occurrences) {
      // Capture every valid type, including positive types used in residual.
      // Repeated raw references remain in the table; numerical context is by
      // actual resolved physical receiver, never by raw requested generation.
      auto target = ReadTarget(bindings, occurrence.raw_full_id_u32);
      const auto identity = target.resolution.object_identity;
      const bool seen = identity && std::any_of(out.target_regiments.begin(), out.target_regiments.end(),
          [&](const auto &held) { return held.resolution.object_identity == identity; });
      if (!seen) { complete = complete && target.ready; out.target_regiments.push_back(std::move(target)); }
    }
  }
  Finish(out, complete);
  if (!complete) out.unavailable_reason = "daily_assault_loss_current_operands_partial";
  return out;
}
} // namespace xar::ck3_12003
