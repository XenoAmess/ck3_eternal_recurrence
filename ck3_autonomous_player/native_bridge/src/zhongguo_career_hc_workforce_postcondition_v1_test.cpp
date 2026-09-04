#include "xar_bridge/zhongguo_career_hc_workforce_postcondition_v1.hpp"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace {

using xar::ck3_11906::ZhongguoCareerHcWorkforceRawVariableV1;

struct Fixture {
  xar::game::ZhongguoCaseFrameV1 frame{88, 123'456, true, true,
                                       true, true, 202};
  bool main_thread = true;
  bool drift = false;
  std::uint32_t reads = 0;
  std::unordered_set<std::int32_t> characters{101, 202};
  std::unordered_map<std::string, ZhongguoCareerHcWorkforceRawVariableV1>
      variables;
  std::vector<std::string> requested_keys;
};

ZhongguoCareerHcWorkforceRawVariableV1 Number(std::int64_t value) {
  return {true, 1, value * 100'000};
}

ZhongguoCareerHcWorkforceRawVariableV1 Character(std::int32_t value) {
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
                  ZhongguoCareerHcWorkforceRawVariableV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  const auto &allowlist = xar::ck3_11906::
      kZhongguoCareerHcWorkforcePostconditionV1VariableAllowlist;
  if (character_id != fixture.frame.played_character_id ||
      std::find(allowlist.begin(), allowlist.end(), key) == allowlist.end()) {
    return false;
  }
  fixture.requested_keys.emplace_back(key);
  ++fixture.reads;
  const auto found = fixture.variables.find(std::string(key));
  output = found == fixture.variables.end()
               ? ZhongguoCareerHcWorkforceRawVariableV1{}
               : found->second;
  if (fixture.drift && fixture.reads > allowlist.size() &&
      key == "zg361_ch_hc_available") {
    output = Number(3);
  }
  return true;
}

xar::ck3_11906::ZhongguoCareerHcWorkforceNativeEnvironmentV1 Environment() {
  xar::ck3_11906::ZhongguoCareerHcWorkforceNativeEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.offline_fixture_function_overrides = true;
  return environment;
}

xar::ck3_11906::ZhongguoCareerHcWorkforceAccessV1 Access(Fixture &fixture) {
  xar::ck3_11906::ZhongguoCareerHcWorkforceAccessV1 access{};
  access.context = &fixture;
  access.capture_frame = &Capture;
  access.is_main_thread = &IsMain;
  access.validate_character = &ValidateCharacter;
  access.read_allowlisted_variable = &ReadVariable;
  return access;
}

xar::ck3_11906::ZhongguoCareerHcWorkforcePostconditionRequestV1 Request(
    std::int32_t owner = 101) {
  return {88, owner, "b6.route-b.post"};
}

void Populate(Fixture &fixture) {
  fixture.variables["zg361_we_m360_receipt_owner"] = Character(101);
  fixture.variables["zg361_we_m360_receipt_subject"] = Character(202);
  fixture.variables["zg361_we_m360_receipt_cycle"] = Number(7);
  fixture.variables["zg361_we_m360_receipt_case"] = Number(7'009);
  fixture.variables["zg361_we_m360_receipt_state"] = Number(4);
  fixture.variables["zg361_we_m360_receipt_choice"] = Number(2);
  fixture.variables["zg361_ch_hc_authorized"] = Number(8);
  fixture.variables["zg361_ch_hc_available"] = Number(2);
  fixture.variables["zg361_ch_hc_reserved"] = Number(1);
  fixture.variables["zg361_ch_hc_occupied"] = Number(3);
  fixture.variables["zg361_ch_hc_frozen"] = Number(1);
  fixture.variables["zg361_ch_hc_reclaimed"] = Number(1);
  fixture.variables["zg361_ch_hc_conserved"] = Number(1);
  fixture.variables["zg361_we_al_external_collective_manager_cost_total"] =
      Number(0);
}

xar::game::ReadZhongguoCareerHcWorkforcePostconditionResultV1 Read(
    Fixture &fixture,
    xar::game::ZhongguoCareerHcWorkforcePostconditionV1 &output,
    xar::ck3_11906::ZhongguoCareerHcWorkforcePostconditionRequestV1 request =
        Request()) {
  return xar::ck3_11906::ReadZhongguoCareerHcWorkforcePostconditionV1(
      Environment(), Access(fixture), request, output);
}

bool TestGreenAndFixedAllowlist() {
  Fixture fixture;
  Populate(fixture);
  xar::game::ZhongguoCareerHcWorkforcePostconditionV1 output{};
  if (Read(fixture, output) !=
          xar::game::ReadZhongguoCareerHcWorkforcePostconditionResultV1::available ||
      !output.readiness.ready ||
      *output.m360_receipt.state.value != 4 ||
      *output.m360_receipt.choice.value != 2 ||
      *output.career_hc_partition.authorized.value != 8 ||
      *output.route_b_cost.manager_cost_total.value != 0 ||
      fixture.reads !=
          2 * xar::ck3_11906::
                  kZhongguoCareerHcWorkforcePostconditionV1VariableAllowlist
                      .size()) {
    return false;
  }
  const auto serialized = xar::ck3_11906::
      SerializeZhongguoCareerHcWorkforcePostconditionV1(output);
  return serialized.find(
             "\"capability\":\"game.command.query-zhongguo-career-hc-workforce-postcondition-v1\"") !=
             std::string::npos &&
         serialized.find("\"choice\":{\"status\":\"available\",\"value\":2") !=
             std::string::npos &&
         serialized.find("\"provenance\":{") != std::string::npos &&
         std::all_of(fixture.requested_keys.begin(),
                     fixture.requested_keys.end(), [](const std::string &key) {
                       return key.starts_with("zg361_we_m360_receipt_") ||
                              key.starts_with("zg361_ch_hc_") ||
                              key == "zg361_we_al_external_collective_manager_cost_total";
                     });
}

bool TestAckAbsenceAndIdentityAreUnavailable() {
  xar::game::ZhongguoCareerHcWorkforcePostconditionV1 output{};
  Fixture no_receipt;
  Populate(no_receipt);
  for (const auto key : {
           "zg361_we_m360_receipt_owner", "zg361_we_m360_receipt_subject",
           "zg361_we_m360_receipt_cycle", "zg361_we_m360_receipt_case",
           "zg361_we_m360_receipt_state", "zg361_we_m360_receipt_choice"}) {
    no_receipt.variables.erase(key);
  }
  if (Read(no_receipt, output) !=
          xar::game::ReadZhongguoCareerHcWorkforcePostconditionResultV1::unavailable ||
      output.status !=
          xar::game::ZhongguoCareerHcWorkforcePostconditionStatusV1::unavailable ||
      output.unavailable_reason != "receipt_not_recorded" ||
      output.readiness.ready) {
    return false;
  }

  Fixture wrong_identity;
  Populate(wrong_identity);
  wrong_identity.variables["zg361_we_m360_receipt_owner"] = Character(202);
  return Read(wrong_identity, output) ==
             xar::game::ReadZhongguoCareerHcWorkforcePostconditionResultV1::unavailable &&
         output.unavailable_reason == "postcondition_incomplete" &&
         !output.readiness.owner_binding_ready && !output.readiness.ready;
}

bool TestBusinessNegativesAreUnavailable() {
  xar::game::ZhongguoCareerHcWorkforcePostconditionV1 output{};
  Fixture route_a;
  Populate(route_a);
  route_a.variables["zg361_we_m360_receipt_choice"] = Number(1);
  if (Read(route_a, output) !=
          xar::game::ReadZhongguoCareerHcWorkforcePostconditionResultV1::unavailable ||
      output.readiness.m360_route_b_receipt_ready || output.readiness.ready) {
    return false;
  }

  Fixture nonconserved;
  Populate(nonconserved);
  nonconserved.variables["zg361_ch_hc_available"] = Number(1);
  if (Read(nonconserved, output) !=
          xar::game::ReadZhongguoCareerHcWorkforcePostconditionResultV1::unavailable ||
      output.readiness.career_hc_conservation_ready || output.readiness.ready) {
    return false;
  }

  Fixture nonzero_cost;
  Populate(nonzero_cost);
  nonzero_cost.variables[
      "zg361_we_al_external_collective_manager_cost_total"] = Number(1);
  return Read(nonzero_cost, output) ==
             xar::game::ReadZhongguoCareerHcWorkforcePostconditionResultV1::unavailable &&
         !output.readiness.route_b_manager_cost_zero_ready &&
         !output.readiness.ready;
}

bool TestFrameAndReadStability() {
  xar::game::ZhongguoCareerHcWorkforcePostconditionV1 output{};
  Fixture drift;
  Populate(drift);
  drift.drift = true;
  if (Read(drift, output) !=
          xar::game::ReadZhongguoCareerHcWorkforcePostconditionResultV1::unavailable ||
      output.unavailable_reason != "state_changed") {
    return false;
  }
  Fixture not_main;
  Populate(not_main);
  not_main.main_thread = false;
  return Read(not_main, output) ==
             xar::game::ReadZhongguoCareerHcWorkforcePostconditionResultV1::unavailable &&
         output.unavailable_reason == "requires_application_main";
}

} // namespace

int main() {
  const bool ok = TestGreenAndFixedAllowlist() &&
                  TestAckAbsenceAndIdentityAreUnavailable() &&
                  TestBusinessNegativesAreUnavailable() &&
                  TestFrameAndReadStability();
  if (!ok) {
    std::cerr << "zhongguo career-HC/workforce postcondition fixture failed\n";
    return 1;
  }
  return 0;
}
