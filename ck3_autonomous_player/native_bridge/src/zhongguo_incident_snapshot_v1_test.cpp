#include "xar_bridge/zhongguo_incident_snapshot_v1.hpp"

#include <cstdint>
#include <iostream>
#include <string>
#include <string_view>
#include <unordered_map>

namespace {

using namespace xar;

constexpr std::int64_t kScale = 100'000;
constexpr std::int32_t kOwner = 200;
constexpr std::int32_t kSubject = 300;

struct Fixture {
  game::ZhongguoCaseFrameV1 frame{41, 53'223'936, true, true, true, true,
                                  kSubject};
  std::unordered_map<std::string, ck3_11906::ZhongguoRawVariableV1> rows;
};

ck3_11906::ZhongguoRawVariableV1 Integer(std::int64_t value) {
  return {true, 1, value * kScale};
}

ck3_11906::ZhongguoRawVariableV1 Q100000(std::int64_t value) {
  return {true, 1, value};
}

ck3_11906::ZhongguoRawVariableV1 Character(std::int32_t value) {
  return {true, 4, value};
}

bool Capture(void *opaque, game::ZhongguoCaseFrameV1 &output) noexcept {
  output = static_cast<Fixture *>(opaque)->frame;
  return true;
}

bool MainThread(void *) noexcept { return true; }

bool Validate(void *, std::int32_t character_id) noexcept {
  return character_id == kOwner || character_id == kSubject;
}

bool Read(void *opaque, std::int32_t character_id, std::string_view key,
          ck3_11906::ZhongguoRawVariableV1 &output) noexcept {
  if (character_id != kSubject) return false;
  const auto &rows = static_cast<Fixture *>(opaque)->rows;
  const auto found = rows.find(std::string(key));
  output = found == rows.end()
               ? ck3_11906::ZhongguoRawVariableV1{}
               : found->second;
  return true;
}

void AddProbe(Fixture &fixture, bool incident) {
  fixture.rows["zg361_ip_probe_owner"] = Character(kOwner);
  fixture.rows["zg361_ip_probe_subject"] = Character(kSubject);
  fixture.rows["zg361_ip_probe_cycle"] = Integer(7);
  fixture.rows["zg361_ip_probe_serial"] = Integer(12);
  fixture.rows["zg361_ip_probe_result"] = Integer(incident ? 1 : 0);
  fixture.rows["zg361_ip_probe_source_kind"] = Integer(incident ? 3 : 0);
  fixture.rows["zg361_ip_probe_consequence_kind"] = Integer(incident ? 2 : 0);
  fixture.rows["zg361_ip_probe_subject_gold"] = Q100000(-125'000);
  fixture.rows["zg361_ip_probe_manager_treasury"] = Q100000(-900'000);
  fixture.rows["zg361_ip_probe_capital_control"] = Q100000(4'500'000);
}

ck3_11906::ZhongguoIncidentAccessV1 Access(Fixture &fixture) {
  ck3_11906::ZhongguoIncidentAccessV1 access{};
  access.context = &fixture;
  access.capture_frame = &Capture;
  access.is_main_thread = &MainThread;
  access.validate_character = &Validate;
  access.read_allowlisted_variable = &Read;
  return access;
}

ck3_11906::ZhongguoIncidentNativeEnvironmentV1 Environment() {
  ck3_11906::ZhongguoIncidentNativeEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.offline_fixture_function_overrides = true;
  return environment;
}

ck3_11906::ZhongguoIncidentSnapshotRequestV1 Request(
    game::ZhongguoIncidentProfileV1 profile) {
  return {41, kOwner, profile, "incident.fixture-01"};
}

bool CheckNa() {
  Fixture fixture;
  AddProbe(fixture, false);
  fixture.rows["zg361_ip_x_final_applicable"] = Integer(0);
  fixture.rows["zg361_ip_x_final_kpi_staged"] = Integer(0);
  fixture.rows["zg361_ip_x_final_na_owner"] = Character(kOwner);
  fixture.rows["zg361_ip_x_final_na_subject"] = Character(kSubject);
  fixture.rows["zg361_ip_x_final_na_cycle"] = Integer(7);
  fixture.rows["zg361_ip_x_final_na_reason"] = Integer(1);
  fixture.rows["zg361_ip_x_final_na_probe_serial"] = Integer(12);
  fixture.rows["zg361_ip_x_final_na_receipt"] = Integer(3);
  game::ZhongguoIncidentSnapshotV1 output;
  const auto result = ck3_11906::ReadZhongguoIncidentSnapshotV1(
      Environment(), Access(fixture), Request(game::ZhongguoIncidentProfileV1::x),
      output);
  const auto wire = ck3_11906::SerializeZhongguoIncidentSnapshotV1(output);
  return result == game::ReadZhongguoIncidentSnapshotResultV1::available &&
         output.terminal_kind == game::ZhongguoIncidentTerminalKindV1::na &&
         output.readiness.terminal_ready && output.readiness.kpi_state_ready &&
         output.readiness.resource_snapshot_ready && output.readiness.ready &&
         output.resources.manager_treasury_q100000.available &&
         output.resources.manager_treasury_q100000.value == -900'000 &&
         wire.find("\"kind\":\"na\"") != std::string::npos &&
         wire.find("\"manager_treasury_source\":\"zg361_ip_probe_manager_treasury\"") !=
             std::string::npos &&
         wire.find("\"value\":0") != std::string::npos;
}

bool CheckMissingTreasury() {
  Fixture fixture;
  AddProbe(fixture, false);
  fixture.rows.erase("zg361_ip_probe_manager_treasury");
  fixture.rows["zg361_ip_x_final_applicable"] = Integer(0);
  fixture.rows["zg361_ip_x_final_kpi_staged"] = Integer(0);
  fixture.rows["zg361_ip_x_final_na_owner"] = Character(kOwner);
  fixture.rows["zg361_ip_x_final_na_subject"] = Character(kSubject);
  fixture.rows["zg361_ip_x_final_na_cycle"] = Integer(7);
  fixture.rows["zg361_ip_x_final_na_reason"] = Integer(1);
  fixture.rows["zg361_ip_x_final_na_probe_serial"] = Integer(12);
  fixture.rows["zg361_ip_x_final_na_receipt"] = Integer(3);
  game::ZhongguoIncidentSnapshotV1 output;
  const auto result = ck3_11906::ReadZhongguoIncidentSnapshotV1(
      Environment(), Access(fixture), Request(game::ZhongguoIncidentProfileV1::x),
      output);
  return result == game::ReadZhongguoIncidentSnapshotResultV1::available &&
         !output.resources.manager_treasury_q100000.available &&
         !output.resources.manager_treasury_q100000.value.has_value() &&
         output.resources.manager_treasury_q100000.unavailable_reason ==
             "variable_absent" &&
         !output.readiness.resource_snapshot_ready &&
         !output.readiness.ready;
}

bool CheckIncidentPending() {
  Fixture fixture;
  AddProbe(fixture, true);
  fixture.rows["zg361_ip_y_final_applicable"] = Integer(1);
  fixture.rows["zg361_ip_y_final_kpi_staged"] = Integer(1);
  fixture.rows["zg361_ip_y_final_owner"] = Character(kOwner);
  fixture.rows["zg361_ip_y_final_subject"] = Character(kSubject);
  fixture.rows["zg361_ip_y_final_cycle"] = Integer(7);
  fixture.rows["zg361_ip_y_final_case"] = Integer(91);
  fixture.rows["zg361_ip_y_final_state"] = Integer(6);
  fixture.rows["zg361_ip_y_final_revision"] = Integer(15);
  fixture.rows["zg361_ip_y_final_incident_serial"] = Integer(4);
  fixture.rows["zg361_ip_y_final_source_kind"] = Integer(3);
  fixture.rows["zg361_ip_y_final_consequence_kind"] = Integer(2);
  fixture.rows["zg361_ip_y_final_score"] = Integer(2);
  fixture.rows["zg361_ip_y_kpi_pending"] = Integer(1);
  fixture.rows["zg361_ip_y_kpi_consumed"] = Integer(0);
  fixture.rows["zg361_ip_y_kpi_owner"] = Character(kOwner);
  fixture.rows["zg361_ip_y_kpi_subject"] = Character(kSubject);
  fixture.rows["zg361_ip_y_kpi_origin_cycle"] = Integer(7);
  fixture.rows["zg361_ip_y_kpi_case"] = Integer(91);
  fixture.rows["zg361_ip_y_kpi_state"] = Integer(6);
  fixture.rows["zg361_ip_y_kpi_score"] = Integer(2);
  fixture.rows["zg361_ip_y_kpi_due_cycle"] = Integer(8);
  fixture.rows["zg361_ip_y_kpi_due_offset"] = Integer(1);
  fixture.rows["zg361_ip_y_kpi_incident_serial"] = Integer(4);
  fixture.rows["zg361_ip_y_kpi_source_kind"] = Integer(3);
  fixture.rows["zg361_ip_y_kpi_consequence_kind"] = Integer(2);
  game::ZhongguoIncidentSnapshotV1 output;
  const auto result = ck3_11906::ReadZhongguoIncidentSnapshotV1(
      Environment(), Access(fixture), Request(game::ZhongguoIncidentProfileV1::y),
      output);
  const auto wire = ck3_11906::SerializeZhongguoIncidentSnapshotV1(output);
  return result == game::ReadZhongguoIncidentSnapshotResultV1::available &&
         output.terminal_kind ==
             game::ZhongguoIncidentTerminalKindV1::incident &&
         output.kpi.disposition ==
             game::ZhongguoIncidentKpiDispositionV1::pending &&
         output.readiness.kpi_state_ready && output.readiness.ready &&
         wire.find("\"disposition\":\"pending\"") != std::string::npos;
}

} // namespace

int main() {
  if (!CheckNa() || !CheckMissingTreasury() || !CheckIncidentPending()) {
    std::cerr << "ZhongGuo incident snapshot fixture failed\n";
    return 1;
  }
  return 0;
}
