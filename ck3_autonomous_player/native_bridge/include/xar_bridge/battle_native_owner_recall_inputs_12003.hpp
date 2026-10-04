#pragma once

#include "xar_bridge/battle_native_activity_context_12003.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12002 { struct BattleBindings; }

namespace xar::game {
struct Snapshot;
struct BattleTransitionSnapshot;

struct BattleNativeOwnerRecallUnitInputsV1 {
  std::int32_t public_cunit_id = -1;
  std::string status = "unit_unresolved";
  std::optional<std::int32_t> receiver_owner_character_id;
  std::optional<std::int32_t> native_carmy_id;
  std::optional<std::int32_t> attached_combat_id;
  std::optional<std::int32_t> current_province_id;
  std::optional<std::uint8_t> army_1d4_raw;
  std::optional<std::uint8_t> army_1ec_raw;
  std::optional<bool> first_fallback_raw_condition;
  std::optional<bool> second_fallback_raw_condition;

  friend bool operator==(const BattleNativeOwnerRecallUnitInputsV1 &,
                         const BattleNativeOwnerRecallUnitInputsV1 &) = default;
};

struct BattleNativeOwnerRecallOwnerInputsV1 {
  std::int32_t owner_character_id = -1;
  std::optional<BattleNativeActivityContextV1> native_activity_context_v1;
  std::optional<std::int32_t> land_318_count_raw;
  std::optional<std::int32_t> owner_target_source_title_id;
  std::optional<std::int32_t> owner_native_recall_target_province_id;
  std::string target_status = "owner_land_unavailable";
  std::string owned_cunit_roster_status = "owner_land_unavailable";
  bool raw_inputs_ready = false;
  std::vector<BattleNativeOwnerRecallUnitInputsV1> owned_cunits_in_stored_order;

  friend bool operator==(const BattleNativeOwnerRecallOwnerInputsV1 &,
                         const BattleNativeOwnerRecallOwnerInputsV1 &) = default;
};

// Current owner/army inputs. This leaf does not observe scheduler membership,
// enqueue an action, or record a naturally submitted native AI command.
struct BattleNativeOwnerRecallInputsV1 {
  bool available = false;
  std::string unavailable_reason;
  bool raw_inputs_ready = false;
  std::string native_context_prefix_status = "unobserved_scheduler_context";
  std::optional<bool> native_context_prefix_admitted;
  bool native_selection_ready = false;
  std::vector<BattleNativeOwnerRecallOwnerInputsV1> owners_in_stored_order;

  friend bool operator==(const BattleNativeOwnerRecallInputsV1 &,
                         const BattleNativeOwnerRecallInputsV1 &) = default;
};
} // namespace xar::game

namespace xar::ck3_12003 {
// Native inner-plan early rejection and outer army-byte selection only.
// A true result still requires the actual outer context prefix, target,
// native permission and path before any command can be selected/submitted.
inline std::optional<bool> OwnerRecallFallbackRawConditionV1(
    std::optional<std::int32_t> land_318_count_raw,
    std::optional<std::uint8_t> army_flag_raw) noexcept {
  if ((land_318_count_raw && *land_318_count_raw == 0) ||
      (army_flag_raw && *army_flag_raw == 0)) return false;
  if (!land_318_count_raw || !army_flag_raw) return std::nullopt;
  return true;
}

void EnableBattleNativeOwnerRecallInputs12003(
    ck3_12002::BattleBindings &, std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;

void AttachBattleNativeOwnerRecallInputsV1(
    const ck3_12002::BattleBindings &, const game::Snapshot &paused_scope,
    game::BattleTransitionSnapshot &) noexcept;

// Same current raw reader addressed by already scoped full public CUnit IDs.
// This entry also works for raised units outside an active Combat.
void AttachBattleNativeOwnerRecallInputsForUnitsV1(
    const ck3_12002::BattleBindings &, const game::Snapshot &paused_scope,
    const std::vector<std::int32_t> &public_cunit_ids,
    game::BattleNativeOwnerRecallInputsV1 &) noexcept;
} // namespace xar::ck3_12003

namespace xar::ck3_11906 {
// Shared leaf serializer for existing transition and army-strength publishers.
std::string SerializeBattleNativeOwnerRecallInputsV1(
    const std::optional<game::BattleNativeOwnerRecallInputsV1> &);
} // namespace xar::ck3_11906
