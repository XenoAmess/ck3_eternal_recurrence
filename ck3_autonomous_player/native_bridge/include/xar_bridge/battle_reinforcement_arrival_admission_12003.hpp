#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::game {

inline constexpr std::string_view kBattleReinforcementArrivalAdmissionSchema12003 =
    "ck3.battle_reinforcement_arrival_admission.v1";

enum class ArrivalAdmission12003Status {
  available,
  not_applicable,
  requires_paused,
  subject_cunit_not_found,
  target_province_not_found,
  state_changed,
  unavailable,
};

struct BattleReinforcementArrivalAdmissionSubject12003 {
  std::int32_t public_cunit_id = -1;
  std::optional<std::int32_t> native_carmy_id;
  std::optional<std::int32_t> owner_character_id;
  std::optional<std::int32_t> current_province_id;
  std::optional<std::int32_t> active_combat_id;

  friend bool operator==(const BattleReinforcementArrivalAdmissionSubject12003 &,
                         const BattleReinforcementArrivalAdmissionSubject12003 &) = default;
};

struct BattleReinforcementArrivalAdmissionTarget12003 {
  std::optional<std::int32_t> province_id;
  std::string provenance = "none";

  friend bool operator==(const BattleReinforcementArrivalAdmissionTarget12003 &,
                         const BattleReinforcementArrivalAdmissionTarget12003 &) = default;
};

struct BattleReinforcementArrivalAdmissionRawGates12003 {
  bool province_contact_gate_enabled = false;
  bool contact_game_mode_allows_contact = false;
  std::int32_t unit_contact_state_raw = 0;
  std::int32_t unit_retreat_state_raw = 0;
  bool army_empty_for_contact = false;

  friend bool operator==(const BattleReinforcementArrivalAdmissionRawGates12003 &,
                         const BattleReinforcementArrivalAdmissionRawGates12003 &) = default;
};

struct BattleReinforcementArrivalAdmission12003Snapshot {
  std::string schema = std::string(kBattleReinforcementArrivalAdmissionSchema12003);
  std::int32_t schema_version = 1;
  ArrivalAdmission12003Status status = ArrivalAdmission12003Status::unavailable;
  std::string unavailable_reason;
  // The owning query fills its existing revision after the native read.
  std::uint64_t snapshot_revision = 0;
  std::int64_t observed_date_raw = 0;
  BattleReinforcementArrivalAdmissionSubject12003 subject;
  BattleReinforcementArrivalAdmissionTarget12003 target;
  std::string eligibility_now = "unavailable";
  std::optional<BattleReinforcementArrivalAdmissionRawGates12003> raw_gates;
  std::vector<std::int32_t> current_target_combat_ids_in_stored_order;
  std::vector<std::int32_t> current_target_compatible_combat_ids_in_stored_order;
  std::optional<std::int32_t> contact_if_now_selected_combat_id;
  std::optional<std::int32_t> selected_combat_stored_index;
  // In the already_in_active_combat branch this is the observed actual side.
  std::string join_side = "none";
  // These are actual current rosters. An absent incoming subject is never added.
  std::vector<std::int32_t> current_attacker_public_cunit_ids_in_stored_order;
  std::vector<std::int32_t> current_defender_public_cunit_ids_in_stored_order;
  bool subject_current_participation_verified = false;
  std::string temporal_semantics = "present_time_only_not_future_binding";
  bool future_binding = false;

  friend bool operator==(const BattleReinforcementArrivalAdmission12003Snapshot &,
                         const BattleReinforcementArrivalAdmission12003Snapshot &) = default;
};

} // namespace xar::game
