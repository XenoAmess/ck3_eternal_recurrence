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

std::string ProfileKey(std::string_view profile, std::string_view suffix) {
  return "zg361_ip_" + std::string(profile) + "_" + std::string(suffix);
}

void AddProbe(Fixture &fixture, std::string_view profile, bool incident,
              std::int64_t cycle = 7, std::int64_t serial = 12) {
  fixture.rows[ProfileKey(profile, "probe_owner")] = Character(kOwner);
  fixture.rows[ProfileKey(profile, "probe_subject")] = Character(kSubject);
  fixture.rows[ProfileKey(profile, "probe_cycle")] = Integer(cycle);
  fixture.rows[ProfileKey(profile, "probe_serial")] = Integer(serial);
  fixture.rows[ProfileKey(profile, "probe_result")] =
      Integer(incident ? 1 : 0);
  fixture.rows[ProfileKey(profile, "probe_source_kind")] =
      Integer(incident ? 3 : 0);
  fixture.rows[ProfileKey(profile, "probe_consequence_kind")] =
      Integer(incident ? 2 : 0);
  fixture.rows[ProfileKey(profile, "probe_subject_gold")] =
      Q100000(-125'000 + cycle);
  fixture.rows[ProfileKey(profile, "probe_manager_treasury")] =
      Q100000(-900'000 + cycle);
  fixture.rows[ProfileKey(profile, "probe_capital_control")] =
      Q100000(4'500'000 + cycle);
}

void AddNaTerminal(Fixture &fixture, std::string_view profile,
                   std::int64_t cycle = 7, std::int64_t serial = 12) {
  fixture.rows[ProfileKey(profile, "final_applicable")] = Integer(0);
  fixture.rows[ProfileKey(profile, "final_kpi_staged")] = Integer(0);
  fixture.rows[ProfileKey(profile, "final_na_owner")] = Character(kOwner);
  fixture.rows[ProfileKey(profile, "final_na_subject")] = Character(kSubject);
  fixture.rows[ProfileKey(profile, "final_na_cycle")] = Integer(cycle);
  fixture.rows[ProfileKey(profile, "final_na_reason")] = Integer(1);
  fixture.rows[ProfileKey(profile, "final_na_probe_serial")] = Integer(serial);
  fixture.rows[ProfileKey(profile, "final_na_receipt")] = Integer(serial + 1);
}

void AddIncidentPending(Fixture &fixture, std::string_view profile,
                        std::int64_t state, std::int64_t cycle = 7,
                        std::int64_t case_serial = 91) {
  fixture.rows[ProfileKey(profile, "final_applicable")] = Integer(1);
  fixture.rows[ProfileKey(profile, "final_kpi_staged")] = Integer(1);
  fixture.rows[ProfileKey(profile, "final_owner")] = Character(kOwner);
  fixture.rows[ProfileKey(profile, "final_subject")] = Character(kSubject);
  fixture.rows[ProfileKey(profile, "final_cycle")] = Integer(cycle);
  fixture.rows[ProfileKey(profile, "final_case")] = Integer(case_serial);
  fixture.rows[ProfileKey(profile, "final_state")] = Integer(state);
  fixture.rows[ProfileKey(profile, "final_revision")] = Integer(15);
  fixture.rows[ProfileKey(profile, "final_incident_serial")] = Integer(4);
  fixture.rows[ProfileKey(profile, "final_source_kind")] = Integer(3);
  fixture.rows[ProfileKey(profile, "final_consequence_kind")] = Integer(2);
  fixture.rows[ProfileKey(profile, "final_score")] = Integer(2);
  fixture.rows[ProfileKey(profile, "kpi_pending")] = Integer(1);
  fixture.rows[ProfileKey(profile, "kpi_consumed")] = Integer(0);
  fixture.rows[ProfileKey(profile, "kpi_owner")] = Character(kOwner);
  fixture.rows[ProfileKey(profile, "kpi_subject")] = Character(kSubject);
  fixture.rows[ProfileKey(profile, "kpi_origin_cycle")] = Integer(cycle);
  fixture.rows[ProfileKey(profile, "kpi_case")] = Integer(case_serial);
  fixture.rows[ProfileKey(profile, "kpi_state")] = Integer(state);
  fixture.rows[ProfileKey(profile, "kpi_score")] = Integer(2);
  fixture.rows[ProfileKey(profile, "kpi_due_cycle")] = Integer(cycle + 1);
  fixture.rows[ProfileKey(profile, "kpi_due_offset")] = Integer(1);
  fixture.rows[ProfileKey(profile, "kpi_incident_serial")] = Integer(4);
  fixture.rows[ProfileKey(profile, "kpi_source_kind")] = Integer(3);
  fixture.rows[ProfileKey(profile, "kpi_consequence_kind")] = Integer(2);
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
  AddProbe(fixture, "x", false);
  AddNaTerminal(fixture, "x");
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
         output.resources.manager_treasury_q100000.value == -899'993 &&
         wire.find("\"kind\":\"na\"") != std::string::npos &&
         wire.find("\"manager_treasury_source\":\"zg361_ip_probe_manager_treasury\"") !=
             std::string::npos &&
         wire.find("\"value\":0") != std::string::npos;
}

bool CheckMissingTreasury() {
  Fixture fixture;
  AddProbe(fixture, "x", false);
  fixture.rows.erase("zg361_ip_x_probe_manager_treasury");
  AddNaTerminal(fixture, "x");
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
  AddProbe(fixture, "y", true);
  AddIncidentPending(fixture, "y", 6);
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

bool CheckMixedProfileReceiptsInOnePausedFrame() {
  Fixture fixture;
  AddProbe(fixture, "x", false, 6, 11);
  AddNaTerminal(fixture, "x", 6, 11);
  AddProbe(fixture, "y", true, 7, 12);
  AddIncidentPending(fixture, "y", 6, 7, 91);
  AddProbe(fixture, "z", true, 7, 12);
  AddIncidentPending(fixture, "z", 6, 7, 92);

  game::ZhongguoIncidentSnapshotV1 x;
  game::ZhongguoIncidentSnapshotV1 y;
  game::ZhongguoIncidentSnapshotV1 z;
  const auto environment = Environment();
  auto access = Access(fixture);
  const auto x_result = ck3_11906::ReadZhongguoIncidentSnapshotV1(
      environment, access, Request(game::ZhongguoIncidentProfileV1::x), x);
  const auto y_result = ck3_11906::ReadZhongguoIncidentSnapshotV1(
      environment, access, Request(game::ZhongguoIncidentProfileV1::y), y);
  const auto z_result = ck3_11906::ReadZhongguoIncidentSnapshotV1(
      environment, access, Request(game::ZhongguoIncidentProfileV1::z), z);
  return x_result == game::ReadZhongguoIncidentSnapshotResultV1::available &&
         y_result == game::ReadZhongguoIncidentSnapshotResultV1::available &&
         z_result == game::ReadZhongguoIncidentSnapshotResultV1::available &&
         x.readiness.ready && y.readiness.ready && z.readiness.ready &&
         x.terminal_kind == game::ZhongguoIncidentTerminalKindV1::na &&
         y.terminal_kind == game::ZhongguoIncidentTerminalKindV1::incident &&
         z.terminal_kind == game::ZhongguoIncidentTerminalKindV1::incident &&
         x.probe.cycle_serial.value == 6 && y.probe.cycle_serial.value == 7 &&
         z.probe.cycle_serial.value == 7;
}

} // namespace

int main() {
  if (!CheckNa() || !CheckMissingTreasury() || !CheckIncidentPending() ||
      !CheckMixedProfileReceiptsInOnePausedFrame()) {
    std::cerr << "ZhongGuo incident snapshot fixture failed\n";
    return 1;
  }
  return 0;
}
