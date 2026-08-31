#pragma once

#include "xar_bridge/zhongguo_case_snapshot_v1.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class ZhongguoIncidentSnapshotStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

enum class ZhongguoIncidentProfileV1 : std::uint32_t {
  x = 1,
  y = 2,
  z = 3,
};

enum class ZhongguoIncidentTerminalKindV1 : std::uint32_t {
  unavailable = 0,
  na = 1,
  incident = 2,
};

enum class ZhongguoIncidentKpiDispositionV1 : std::uint32_t {
  unavailable = 0,
  not_staged = 1,
  pending = 2,
  consumed = 3,
};

struct ZhongguoIncidentProbeV1 {
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 probe_serial;
  ZhongguoTypedIntegerV1 result;
  ZhongguoTypedIntegerV1 source_kind;
  ZhongguoTypedIntegerV1 consequence_kind;

  friend bool operator==(const ZhongguoIncidentProbeV1 &,
                         const ZhongguoIncidentProbeV1 &) = default;
};

struct ZhongguoIncidentResourceSnapshotV1 {
  // Exact Jomini fixed-point payloads.  Consumers retain the Q100000 scale.
  ZhongguoTypedIntegerV1 subject_personal_gold_q100000;
  ZhongguoTypedIntegerV1 manager_treasury_q100000;
  ZhongguoTypedIntegerV1 capital_control_q100000;

  friend bool operator==(const ZhongguoIncidentResourceSnapshotV1 &,
                         const ZhongguoIncidentResourceSnapshotV1 &) =
      default;
};

struct ZhongguoIncidentNaTerminalV1 {
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 reason;
  ZhongguoTypedIntegerV1 probe_serial;
  ZhongguoTypedIntegerV1 receipt_serial;
  ZhongguoTypedIntegerV1 applicable;
  ZhongguoTypedIntegerV1 kpi_staged;

  friend bool operator==(const ZhongguoIncidentNaTerminalV1 &,
                         const ZhongguoIncidentNaTerminalV1 &) = default;
};

struct ZhongguoIncidentPositiveTerminalV1 {
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedIntegerV1 revision;
  ZhongguoTypedIntegerV1 incident_serial;
  ZhongguoTypedIntegerV1 source_kind;
  ZhongguoTypedIntegerV1 consequence_kind;
  ZhongguoTypedIntegerV1 final_score;
  ZhongguoTypedIntegerV1 applicable;
  ZhongguoTypedIntegerV1 kpi_staged;

  friend bool operator==(const ZhongguoIncidentPositiveTerminalV1 &,
                         const ZhongguoIncidentPositiveTerminalV1 &) =
      default;
};

struct ZhongguoIncidentKpiStateV1 {
  ZhongguoIncidentKpiDispositionV1 disposition =
      ZhongguoIncidentKpiDispositionV1::unavailable;
  ZhongguoTypedIntegerV1 pending;
  ZhongguoTypedIntegerV1 consumed;
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 origin_cycle;
  ZhongguoTypedIntegerV1 due_cycle;
  ZhongguoTypedIntegerV1 due_offset;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedIntegerV1 score;
  ZhongguoTypedIntegerV1 incident_serial;
  ZhongguoTypedIntegerV1 source_kind;
  ZhongguoTypedIntegerV1 consequence_kind;
  ZhongguoTypedIntegerV1 receipt_serial;
  ZhongguoTypedIntegerV1 consumed_owner_character_id;
  ZhongguoTypedIntegerV1 consumed_subject_character_id;
  ZhongguoTypedIntegerV1 consumed_origin_cycle;
  ZhongguoTypedIntegerV1 consumed_due_cycle;
  ZhongguoTypedIntegerV1 consumed_cycle;
  ZhongguoTypedIntegerV1 consumed_case_serial;
  ZhongguoTypedIntegerV1 consumed_score;
  ZhongguoTypedIntegerV1 consumed_incident_serial;

  friend bool operator==(const ZhongguoIncidentKpiStateV1 &,
                         const ZhongguoIncidentKpiStateV1 &) = default;
};

struct ZhongguoIncidentReadinessV1 {
  bool player_subject_binding_ready = false;
  bool owner_binding_ready = false;
  bool profile_binding_ready = false;
  bool probe_ready = false;
  bool terminal_ready = false;
  bool resource_snapshot_ready = false;
  bool kpi_state_ready = false;
  bool same_frame_ready = false;
  bool ready = false;

  friend bool operator==(const ZhongguoIncidentReadinessV1 &,
                         const ZhongguoIncidentReadinessV1 &) = default;
};

struct ZhongguoIncidentSnapshotV1 {
  ZhongguoIncidentSnapshotStatusV1 status =
      ZhongguoIncidentSnapshotStatusV1::unavailable;
  std::string case_kind;
  std::string profile;
  std::string request_nonce;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t player_character_id = -1;
  std::int32_t subject_character_id = -1;
  std::int32_t requested_owner_character_id = -1;
  ZhongguoIncidentTerminalKindV1 terminal_kind =
      ZhongguoIncidentTerminalKindV1::unavailable;
  ZhongguoIncidentProbeV1 probe;
  ZhongguoIncidentResourceSnapshotV1 resources;
  ZhongguoIncidentNaTerminalV1 na_terminal;
  ZhongguoIncidentPositiveTerminalV1 incident_terminal;
  ZhongguoIncidentKpiStateV1 kpi;
  ZhongguoIncidentReadinessV1 readiness;
  std::string unavailable_reason;

  friend bool operator==(const ZhongguoIncidentSnapshotV1 &,
                         const ZhongguoIncidentSnapshotV1 &) = default;
};

enum class ReadZhongguoIncidentSnapshotResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kZhongguoIncidentSnapshotV1Capability =
    "game.command.query-zhongguo-incident-snapshot-v1";
inline constexpr std::string_view kZhongguoIncidentSnapshotV1Step =
    "query-zhongguo-incident-snapshot-v1";
inline constexpr std::string_view kZhongguoIncidentSnapshotV1CaseKind =
    "zhongguo.incident.subject-self";
inline constexpr std::string_view kZhongguoIncidentSnapshotV1BackendId =
    "ck3-1.19.0.6-native-zhongguo-incident-snapshot-v1";
inline constexpr std::string_view kZhongguoIncidentSnapshotV1ConsumerId =
    "xar-autoplayer-zhongguo-incident-snapshot-v1";
inline constexpr std::string_view kZhongguoIncidentSnapshotV1AllowlistId =
    "zg361-incident-terminal-x-y-z-v1";

// The three lists are deliberately explicit.  Profile is an enum selector;
// no caller supplied variable name ever reaches the engine reader.
inline constexpr std::array<std::string_view, 50>
    kZhongguoIncidentSnapshotV1XAllowlist{
        "zg361_ip_x_probe_owner", "zg361_ip_x_probe_subject",
        "zg361_ip_x_probe_cycle", "zg361_ip_x_probe_serial",
        "zg361_ip_x_probe_result", "zg361_ip_x_probe_source_kind",
        "zg361_ip_x_probe_consequence_kind", "zg361_ip_x_probe_subject_gold",
        "zg361_ip_x_probe_manager_treasury",
        "zg361_ip_x_probe_capital_control", "zg361_ip_x_final_applicable",
        "zg361_ip_x_final_kpi_staged", "zg361_ip_x_final_na_owner",
        "zg361_ip_x_final_na_subject", "zg361_ip_x_final_na_cycle",
        "zg361_ip_x_final_na_reason", "zg361_ip_x_final_na_probe_serial",
        "zg361_ip_x_final_na_receipt", "zg361_ip_x_final_owner",
        "zg361_ip_x_final_subject", "zg361_ip_x_final_cycle",
        "zg361_ip_x_final_case", "zg361_ip_x_final_state",
        "zg361_ip_x_final_revision", "zg361_ip_x_final_incident_serial",
        "zg361_ip_x_final_source_kind",
        "zg361_ip_x_final_consequence_kind", "zg361_ip_x_final_score",
        "zg361_ip_x_kpi_pending", "zg361_ip_x_kpi_consumed",
        "zg361_ip_x_kpi_owner", "zg361_ip_x_kpi_subject",
        "zg361_ip_x_kpi_origin_cycle", "zg361_ip_x_kpi_case",
        "zg361_ip_x_kpi_state", "zg361_ip_x_kpi_score",
        "zg361_ip_x_kpi_due_cycle", "zg361_ip_x_kpi_due_offset",
        "zg361_ip_x_kpi_incident_serial", "zg361_ip_x_kpi_source_kind",
        "zg361_ip_x_kpi_consequence_kind",
        "zg361_ip_x_kpi_receipt_serial",
        "zg361_ip_x_kpi_consumed_owner",
        "zg361_ip_x_kpi_consumed_subject",
        "zg361_ip_x_kpi_consumed_origin_cycle",
        "zg361_ip_x_kpi_consumed_due_cycle",
        "zg361_ip_x_kpi_consumed_cycle",
        "zg361_ip_x_kpi_consumed_case", "zg361_ip_x_kpi_consumed_score",
        "zg361_ip_x_kpi_consumed_incident_serial"};

inline constexpr std::array<std::string_view, 50>
    kZhongguoIncidentSnapshotV1YAllowlist{
        "zg361_ip_y_probe_owner", "zg361_ip_y_probe_subject",
        "zg361_ip_y_probe_cycle", "zg361_ip_y_probe_serial",
        "zg361_ip_y_probe_result", "zg361_ip_y_probe_source_kind",
        "zg361_ip_y_probe_consequence_kind", "zg361_ip_y_probe_subject_gold",
        "zg361_ip_y_probe_manager_treasury",
        "zg361_ip_y_probe_capital_control", "zg361_ip_y_final_applicable",
        "zg361_ip_y_final_kpi_staged", "zg361_ip_y_final_na_owner",
        "zg361_ip_y_final_na_subject", "zg361_ip_y_final_na_cycle",
        "zg361_ip_y_final_na_reason", "zg361_ip_y_final_na_probe_serial",
        "zg361_ip_y_final_na_receipt", "zg361_ip_y_final_owner",
        "zg361_ip_y_final_subject", "zg361_ip_y_final_cycle",
        "zg361_ip_y_final_case", "zg361_ip_y_final_state",
        "zg361_ip_y_final_revision", "zg361_ip_y_final_incident_serial",
        "zg361_ip_y_final_source_kind",
        "zg361_ip_y_final_consequence_kind", "zg361_ip_y_final_score",
        "zg361_ip_y_kpi_pending", "zg361_ip_y_kpi_consumed",
        "zg361_ip_y_kpi_owner", "zg361_ip_y_kpi_subject",
        "zg361_ip_y_kpi_origin_cycle", "zg361_ip_y_kpi_case",
        "zg361_ip_y_kpi_state", "zg361_ip_y_kpi_score",
        "zg361_ip_y_kpi_due_cycle", "zg361_ip_y_kpi_due_offset",
        "zg361_ip_y_kpi_incident_serial", "zg361_ip_y_kpi_source_kind",
        "zg361_ip_y_kpi_consequence_kind",
        "zg361_ip_y_kpi_receipt_serial",
        "zg361_ip_y_kpi_consumed_owner",
        "zg361_ip_y_kpi_consumed_subject",
        "zg361_ip_y_kpi_consumed_origin_cycle",
        "zg361_ip_y_kpi_consumed_due_cycle",
        "zg361_ip_y_kpi_consumed_cycle",
        "zg361_ip_y_kpi_consumed_case", "zg361_ip_y_kpi_consumed_score",
        "zg361_ip_y_kpi_consumed_incident_serial"};

inline constexpr std::array<std::string_view, 50>
    kZhongguoIncidentSnapshotV1ZAllowlist{
        "zg361_ip_z_probe_owner", "zg361_ip_z_probe_subject",
        "zg361_ip_z_probe_cycle", "zg361_ip_z_probe_serial",
        "zg361_ip_z_probe_result", "zg361_ip_z_probe_source_kind",
        "zg361_ip_z_probe_consequence_kind", "zg361_ip_z_probe_subject_gold",
        "zg361_ip_z_probe_manager_treasury",
        "zg361_ip_z_probe_capital_control", "zg361_ip_z_final_applicable",
        "zg361_ip_z_final_kpi_staged", "zg361_ip_z_final_na_owner",
        "zg361_ip_z_final_na_subject", "zg361_ip_z_final_na_cycle",
        "zg361_ip_z_final_na_reason", "zg361_ip_z_final_na_probe_serial",
        "zg361_ip_z_final_na_receipt", "zg361_ip_z_final_owner",
        "zg361_ip_z_final_subject", "zg361_ip_z_final_cycle",
        "zg361_ip_z_final_case", "zg361_ip_z_final_state",
        "zg361_ip_z_final_revision", "zg361_ip_z_final_incident_serial",
        "zg361_ip_z_final_source_kind",
        "zg361_ip_z_final_consequence_kind", "zg361_ip_z_final_score",
        "zg361_ip_z_kpi_pending", "zg361_ip_z_kpi_consumed",
        "zg361_ip_z_kpi_owner", "zg361_ip_z_kpi_subject",
        "zg361_ip_z_kpi_origin_cycle", "zg361_ip_z_kpi_case",
        "zg361_ip_z_kpi_state", "zg361_ip_z_kpi_score",
        "zg361_ip_z_kpi_due_cycle", "zg361_ip_z_kpi_due_offset",
        "zg361_ip_z_kpi_incident_serial", "zg361_ip_z_kpi_source_kind",
        "zg361_ip_z_kpi_consequence_kind",
        "zg361_ip_z_kpi_receipt_serial",
        "zg361_ip_z_kpi_consumed_owner",
        "zg361_ip_z_kpi_consumed_subject",
        "zg361_ip_z_kpi_consumed_origin_cycle",
        "zg361_ip_z_kpi_consumed_due_cycle",
        "zg361_ip_z_kpi_consumed_cycle",
        "zg361_ip_z_kpi_consumed_case", "zg361_ip_z_kpi_consumed_score",
        "zg361_ip_z_kpi_consumed_incident_serial"};

using ZhongguoIncidentNativeEnvironmentV1 = ZhongguoCaseNativeEnvironmentV1;
using ZhongguoIncidentAccessV1 = ZhongguoCaseAccessV1;
using ZhongguoIncidentRawVariableV1 = ZhongguoRawVariableV1;
using ZhongguoIncidentFrameV1 = game::ZhongguoCaseFrameV1;

struct ZhongguoIncidentSnapshotRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
  std::int32_t owner_character_id = -1;
  game::ZhongguoIncidentProfileV1 profile =
      game::ZhongguoIncidentProfileV1::x;
  std::string request_nonce;
};

ZhongguoIncidentNativeEnvironmentV1 BindZhongguoIncidentNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

game::ReadZhongguoIncidentSnapshotResultV1 ReadZhongguoIncidentSnapshotV1(
    const ZhongguoIncidentNativeEnvironmentV1 &environment,
    const ZhongguoIncidentAccessV1 &access,
    const ZhongguoIncidentSnapshotRequestV1 &request,
    game::ZhongguoIncidentSnapshotV1 &output) noexcept;

std::string SerializeZhongguoIncidentSnapshotV1(
    const game::ZhongguoIncidentSnapshotV1 &snapshot);

} // namespace xar::ck3_11906
