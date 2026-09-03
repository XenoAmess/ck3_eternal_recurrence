#include "xar_bridge/zhongguo_projects_metrics_postcondition_v1.hpp"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace {

using xar::ck3_11906::ZhongguoProjectsMetricsRawVariableV1;

struct Fixture {
  xar::game::ZhongguoCaseFrameV1 frame{91, 730'109, true, true,
                                       true, true, 100};
  bool main_thread = true;
  bool drift = false;
  std::uint32_t reads = 0;
  std::unordered_set<std::int32_t> characters{100, 200};
  std::unordered_map<std::string, ZhongguoProjectsMetricsRawVariableV1>
      variables;
  std::vector<std::string> requested_keys;
};

ZhongguoProjectsMetricsRawVariableV1 Number(std::int64_t value) {
  return {true, 1, value * 100'000};
}

ZhongguoProjectsMetricsRawVariableV1 Character(std::int32_t value) {
  return {true, 4, value};
}

bool Capture(void *opaque, xar::game::ZhongguoCaseFrameV1 &output) noexcept {
  output = static_cast<Fixture *>(opaque)->frame;
  return true;
}

bool IsMain(void *opaque) noexcept {
  return static_cast<Fixture *>(opaque)->main_thread;
}

bool ValidateCharacter(void *opaque, std::int32_t character_id) noexcept {
  return static_cast<Fixture *>(opaque)->characters.contains(character_id);
}

bool ReadVariable(void *opaque, std::int32_t character_id,
                  std::string_view key,
                  ZhongguoProjectsMetricsRawVariableV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  const auto &allowlist = xar::ck3_11906::
      kZhongguoProjectsMetricsPostconditionV1VariableAllowlist;
  if (character_id != fixture.frame.played_character_id ||
      std::find(allowlist.begin(), allowlist.end(), key) == allowlist.end()) {
    return false;
  }
  fixture.requested_keys.emplace_back(key);
  ++fixture.reads;
  const auto found = fixture.variables.find(std::string(key));
  output = found == fixture.variables.end()
               ? ZhongguoProjectsMetricsRawVariableV1{}
               : found->second;
  if (fixture.drift && fixture.reads > allowlist.size() &&
      key == "zg361_p3_m229_metrics_revision") {
    output = Number(4);
  }
  return true;
}

xar::ck3_11906::ZhongguoProjectsMetricsNativeEnvironmentV1 Environment() {
  xar::ck3_11906::ZhongguoProjectsMetricsNativeEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.offline_fixture_function_overrides = true;
  return environment;
}

xar::ck3_11906::ZhongguoProjectsMetricsAccessV1 Access(Fixture &fixture) {
  xar::ck3_11906::ZhongguoProjectsMetricsAccessV1 access{};
  access.context = &fixture;
  access.capture_frame = &Capture;
  access.is_main_thread = &IsMain;
  access.validate_character = &ValidateCharacter;
  access.read_allowlisted_variable = &ReadVariable;
  return access;
}

xar::ck3_11906::ZhongguoProjectsMetricsPostconditionRequestV1 Request(
    std::int32_t owner = 200) {
  return {91, owner, "projects-metrics:91"};
}

void Populate(Fixture &fixture) {
  const auto set_identity = [&fixture](std::string_view prefix) {
    fixture.variables[std::string(prefix) + "owner"] = Character(200);
    fixture.variables[std::string(prefix) + "subject"] = Character(100);
    fixture.variables[std::string(prefix) + "cycle"] = Number(15);
    fixture.variables[std::string(prefix) + "case"] = Number(1'526);
  };
  fixture.variables["zg361_p3_project_source_ready"] = Number(1);
  set_identity("zg361_p3_project_source_");
  fixture.variables[
      "zg361_p3_project_source_contribution_receipt_id"] = Number(26'001);
  fixture.variables[
      "zg361_p3_project_source_contribution_receipt_revision"] = Number(9);
  fixture.variables["zg361_p3_project_source_contribution_value"] =
      Number(-3);
  set_identity("zg361_p3_m229_result_");
  fixture.variables["zg361_p3_m229_source_contribution_receipt_id"] =
      Number(26'001);
  fixture.variables["zg361_p3_m229_source_contribution_receipt_revision"] =
      Number(9);
  fixture.variables["zg361_p3_m229_metrics_revision"] = Number(3);
  fixture.variables["zg361_p3_m229_dictionary_key_code"] = Number(1);
  fixture.variables["zg361_p3_m229_consumed_owner"] = Character(200);
  fixture.variables["zg361_p3_m229_consumed_subject"] = Character(100);
  fixture.variables["zg361_p3_m229_consumed_cycle"] = Number(15);
  fixture.variables["zg361_p3_m229_consumed_case"] = Number(2'901);
  fixture.variables["zg361_p3_m229_consumed_state"] = Number(1);
  fixture.variables["zg361_p3_m229_receipt_choice"] = Number(1);
  fixture.variables["zg361_p3_m229_visible_value"] = Number(1);
  fixture.variables["zg361_p3_m229_visible_provenance_case"] = Number(2'901);
}

bool Read(Fixture &fixture,
          xar::game::ZhongguoProjectsMetricsPostconditionV1 &output,
          xar::ck3_11906::ZhongguoProjectsMetricsPostconditionRequestV1
              request = Request()) {
  return xar::ck3_11906::ReadZhongguoProjectsMetricsPostconditionV1(
             Environment(), Access(fixture), request, output) ==
         xar::game::ReadZhongguoProjectsMetricsPostconditionResultV1::
             available;
}

bool TestGreenAndAllowlist() {
  Fixture fixture;
  Populate(fixture);
  xar::game::ZhongguoProjectsMetricsPostconditionV1 output{};
  if (!Read(fixture, output) || !output.readiness.ready ||
      !output.readiness.same_project_case_identity ||
      !output.readiness.receipt_lineage_ready ||
      *output.contribution.receipt_id.value != 26'001 ||
      *output.contribution.receipt_revision.value != 9 ||
      *output.metrics_result.source_contribution_receipt_id.value != 26'001 ||
      *output.metrics_result.source_contribution_receipt_revision.value != 9 ||
      *output.metrics_result.metrics_revision.value != 3 ||
      *output.metrics_result.dictionary_key.value !=
          "metric_dictionary_subject_v1" ||
      fixture.reads !=
          2 * xar::ck3_11906::
                  kZhongguoProjectsMetricsPostconditionV1VariableAllowlist
                      .size()) {
    return false;
  }
  const auto serialized =
      xar::ck3_11906::SerializeZhongguoProjectsMetricsPostconditionV1(output);
  return serialized.find(
             "\"capability\":\"game.command.query-zhongguo-projects-metrics-postcondition-v1\"") !=
             std::string::npos &&
         serialized.find(
             "\"source_contribution_receipt_revision\":{\"status\":\"available\",\"value\":9") !=
             std::string::npos &&
         std::all_of(
      fixture.requested_keys.begin(), fixture.requested_keys.end(),
      [](const std::string &key) {
        return key.starts_with("zg361_p3_") &&
               key.find("zg361_cp_") == std::string::npos;
      });
}

bool TestLineageAndIdentityFailClosed() {
  xar::game::ZhongguoProjectsMetricsPostconditionV1 output{};
  Fixture receipt_drift;
  Populate(receipt_drift);
  receipt_drift.variables["zg361_p3_m229_source_contribution_receipt_id"] =
      Number(26'002);
  if (!Read(receipt_drift, output) || output.readiness.ready ||
      output.readiness.receipt_lineage_ready) {
    return false;
  }

  Fixture revision_drift;
  Populate(revision_drift);
  revision_drift.variables[
      "zg361_p3_m229_source_contribution_receipt_revision"] = Number(8);
  if (!Read(revision_drift, output) || output.readiness.ready ||
      output.readiness.receipt_lineage_ready) {
    return false;
  }

  Fixture identity_drift;
  Populate(identity_drift);
  identity_drift.variables["zg361_p3_m229_result_case"] = Number(1'527);
  return Read(identity_drift, output) && !output.readiness.ready &&
         !output.readiness.same_project_case_identity;
}

bool TestTypedUnavailableAndDrift() {
  xar::game::ZhongguoProjectsMetricsPostconditionV1 output{};
  Fixture no_source;
  Populate(no_source);
  no_source.variables.erase("zg361_p3_project_source_ready");
  if (Read(no_source, output) ||
      output.unavailable_reason != "project_source_not_found") {
    return false;
  }

  Fixture wrong_owner;
  Populate(wrong_owner);
  if (!Read(wrong_owner, output, Request(201)) || output.readiness.ready ||
      output.readiness.owner_binding_ready) {
    return false;
  }

  Fixture drift;
  Populate(drift);
  drift.drift = true;
  if (Read(drift, output) || output.unavailable_reason != "state_changed") {
    return false;
  }

  Fixture not_main;
  Populate(not_main);
  not_main.main_thread = false;
  return !Read(not_main, output) &&
         output.unavailable_reason == "requires_application_main";
}

} // namespace

int main() {
  const bool ok = TestGreenAndAllowlist() &&
                  TestLineageAndIdentityFailClosed() &&
                  TestTypedUnavailableAndDrift();
  if (!ok) {
    std::cerr << "zhongguo projects/metrics postcondition fixture failed\n";
    return 1;
  }
  return 0;
}
