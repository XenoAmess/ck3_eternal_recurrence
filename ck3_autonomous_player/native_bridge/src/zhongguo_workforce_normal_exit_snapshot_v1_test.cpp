#include "xar_bridge/zhongguo_workforce_normal_exit_snapshot_v1.hpp"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace {

using Raw = xar::ck3_11906::ZhongguoWorkforceNormalExitRawVariableV1;

struct Fixture {
  xar::game::ZhongguoCaseFrameV1 frame{81, 730'101, true, true,
                                       true, true, 100};
  bool main_thread = true;
  bool drift_rows = false;
  std::uint32_t captures = 0;
  std::uint32_t variable_reads = 0;
  std::unordered_set<std::int32_t> characters{100, 200};
  std::unordered_map<std::string, Raw> variables;
  std::vector<std::string> requested_keys;
};

Raw Number(std::int64_t value) { return {true, 1, value * 100'000}; }
Raw Character(std::int32_t value) { return {true, 4, value}; }

bool Capture(void *opaque, xar::game::ZhongguoCaseFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  output = fixture.frame;
  ++fixture.captures;
  return true;
}

bool IsMain(void *opaque) noexcept {
  return static_cast<Fixture *>(opaque)->main_thread;
}

bool ValidateCharacter(void *opaque, std::int32_t character_id) noexcept {
  return static_cast<Fixture *>(opaque)->characters.contains(character_id);
}

bool ReadVariable(void *opaque, std::int32_t character_id,
                  std::string_view key, Raw &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  const auto &allowlist =
      xar::ck3_11906::kZhongguoWorkforceNormalExitVariableAllowlist;
  if (character_id != fixture.frame.played_character_id ||
      std::find(allowlist.begin(), allowlist.end(), key) == allowlist.end()) {
    return false;
  }
  try {
    fixture.requested_keys.emplace_back(key);
  } catch (...) {
    return false;
  }
  ++fixture.variable_reads;
  const auto found = fixture.variables.find(std::string(key));
  output = found == fixture.variables.end() ? Raw{} : found->second;
  if (fixture.drift_rows && fixture.variable_reads > allowlist.size() &&
      key == "zg361_b2_m075_state") {
    output = Number(4);
  }
  return true;
}

xar::ck3_11906::ZhongguoWorkforceNormalExitNativeEnvironmentV1
Environment() {
  xar::ck3_11906::ZhongguoWorkforceNormalExitNativeEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.offline_fixture_function_overrides = true;
  return environment;
}

xar::ck3_11906::ZhongguoWorkforceNormalExitAccessV1 Access(Fixture &fixture) {
  xar::ck3_11906::ZhongguoWorkforceNormalExitAccessV1 access{};
  access.context = &fixture;
  access.capture_frame = &Capture;
  access.is_main_thread = &IsMain;
  access.validate_character = &ValidateCharacter;
  access.read_allowlisted_variable = &ReadVariable;
  return access;
}

xar::ck3_11906::ZhongguoWorkforceNormalExitSnapshotRequestV1 Request(
    std::int32_t owner = 200) {
  return {81, owner, "normal-exit:81"};
}

void PutPartition(Fixture &fixture, std::string_view prefix,
                  std::int64_t available, std::int64_t reserved,
                  std::int64_t occupied, std::int64_t frozen,
                  std::int64_t reclaimed) {
  fixture.variables[std::string(prefix) + "authorized"] =
      Number(available + reserved + occupied + frozen + reclaimed);
  fixture.variables[std::string(prefix) + "available"] = Number(available);
  fixture.variables[std::string(prefix) + "reserved"] = Number(reserved);
  fixture.variables[std::string(prefix) + "occupied"] = Number(occupied);
  fixture.variables[std::string(prefix) + "frozen"] = Number(frozen);
  fixture.variables[std::string(prefix) + "reclaimed"] = Number(reclaimed);
}

void PopulateSource(Fixture &fixture) {
  fixture.variables["zg361_b2_m075_owner"] = Character(200);
  fixture.variables["zg361_b2_m075_subject"] = Character(100);
  fixture.variables["zg361_b2_m075_cycle"] = Number(7);
  fixture.variables["zg361_b2_m075_case"] = Number(903);
  fixture.variables["zg361_b2_m075_state"] = Number(1);
  fixture.variables["zg361_b2_m075_route"] = Number(1);
  fixture.variables["zg361_b2_m075_offer_gold"] = Number(50);
  fixture.variables["zg361_b2_m075_receipt_serial"] = Number(903);
  fixture.variables["zg361_b2_m075_object_owner"] = Character(200);
  fixture.variables["zg361_b2_m075_object_subject"] = Character(100);
  fixture.variables["zg361_b2_m075_object_cycle"] = Number(7);
  fixture.variables["zg361_b2_m075_object_receipt_case"] = Number(903);
  fixture.variables["zg361_b2_m075_object_route"] = Number(1);
  fixture.variables["zg361_b2_m075_object_active"] = Number(1);
  fixture.variables["zg361_b2_m075_object_consumed"] = Number(0);
  PutPartition(fixture, "zg361_ch_hc_", 4, 1, 3, 1, 1);
  fixture.variables["zg361_we_formal_hc_active"] = Number(1);
  fixture.variables["zg361_we_formal_hc_active_case"] = Number(777);
}

void PopulatePending(Fixture &fixture) {
  fixture.variables["zg361_workforce_normal_exit_fact_pending"] = Number(1);
  fixture.variables["zg361_workforce_normal_exit_fact_pending_owner"] =
      Character(200);
  fixture.variables["zg361_workforce_normal_exit_fact_pending_subject"] =
      Character(100);
  fixture.variables["zg361_workforce_normal_exit_fact_pending_cycle"] = Number(7);
  fixture.variables["zg361_workforce_normal_exit_fact_pending_case"] = Number(903);
  PutPartition(fixture,
               "zg361_workforce_normal_exit_fact_pending_hc_", 4, 1, 3, 1, 1);
  for (const auto part : {"authorized", "available", "reserved", "occupied",
                          "frozen", "reclaimed"}) {
    const std::string base =
        "zg361_workforce_normal_exit_fact_pending_hc_" + std::string(part);
    fixture.variables[base + "_before"] = fixture.variables[base];
    fixture.variables.erase(base);
  }
  fixture.variables["zg361_workforce_normal_exit_fact_pending_slot_case"] =
      Number(777);
}

void MakeSourceConsumed(Fixture &fixture) {
  fixture.variables["zg361_b2_m075_state"] = Number(3);
  fixture.variables["zg361_b2_m075_object_active"] = Number(0);
  fixture.variables["zg361_b2_m075_object_consumed"] = Number(1);
  fixture.variables["zg361_b2_m075_consumer_receipt_case"] = Number(903);
}

void PopulateMigrating(Fixture &fixture) {
  PopulateSource(fixture);
  PopulatePending(fixture);
  MakeSourceConsumed(fixture);
  fixture.variables["zg361_workforce_normal_exit_fact_state"] = Number(3);
  fixture.variables
      ["zg361_workforce_normal_exit_fact_pending_hc_migration_authorized"] =
          Number(1);
  PutPartition(fixture, "zg361_ch_hc_", 4, 1, 2, 2, 1);
  fixture.variables["zg361_we_formal_hc_active"] = Number(0);
}

void ErasePending(Fixture &fixture) {
  constexpr std::array<std::string_view, 13> keys{
      "zg361_workforce_normal_exit_fact_pending",
      "zg361_workforce_normal_exit_fact_pending_owner",
      "zg361_workforce_normal_exit_fact_pending_subject",
      "zg361_workforce_normal_exit_fact_pending_cycle",
      "zg361_workforce_normal_exit_fact_pending_case",
      "zg361_workforce_normal_exit_fact_pending_hc_migration_authorized",
      "zg361_workforce_normal_exit_fact_pending_hc_authorized_before",
      "zg361_workforce_normal_exit_fact_pending_hc_available_before",
      "zg361_workforce_normal_exit_fact_pending_hc_reserved_before",
      "zg361_workforce_normal_exit_fact_pending_hc_occupied_before",
      "zg361_workforce_normal_exit_fact_pending_hc_frozen_before",
      "zg361_workforce_normal_exit_fact_pending_hc_reclaimed_before",
      "zg361_workforce_normal_exit_fact_pending_slot_case",
  };
  for (const auto key : keys) fixture.variables.erase(std::string(key));
}

void PopulateSealed(Fixture &fixture) {
  PopulateMigrating(fixture);
  ErasePending(fixture);
  fixture.variables["zg361_workforce_normal_exit_fact_state"] = Number(4);
  const auto boolean = [&](std::string_view suffix, bool value) {
    fixture.variables["zg361_workforce_normal_exit_fact_receipt_" +
                      std::string(suffix)] = Number(value ? 1 : 0);
  };
  boolean("active", true);
  boolean("sealed", true);
  boolean("published", true);
  boolean("consumed", true);
  fixture.variables
      ["zg361_workforce_normal_exit_fact_receipt_consumed_operation"] =
          Number(75);
  fixture.variables["zg361_workforce_normal_exit_fact_receipt_owner"] =
      Character(200);
  fixture.variables["zg361_workforce_normal_exit_fact_receipt_subject"] =
      Character(100);
  fixture.variables["zg361_workforce_normal_exit_fact_receipt_cycle"] = Number(7);
  fixture.variables["zg361_workforce_normal_exit_fact_receipt_case"] = Number(903);
  fixture.variables["zg361_workforce_normal_exit_fact_receipt_state"] = Number(6);
  fixture.variables["zg361_workforce_normal_exit_fact_receipt_id"] = Number(7701);
  fixture.variables["zg361_workforce_normal_exit_fact_receipt_hash"] =
      Number(9901);
  boolean("hc_ledger_settled", true);
  boolean("hc_destination_frozen", true);
  boolean("hc_conservation_verified", true);
  PutPartition(fixture,
               "zg361_workforce_normal_exit_fact_receipt_hc_", 4, 1, 3, 1, 1);
  // PutPartition wrote unsuffixed keys; move them to the before names.
  for (const auto part : {"authorized", "available", "reserved", "occupied",
                          "frozen", "reclaimed"}) {
    const std::string base =
        "zg361_workforce_normal_exit_fact_receipt_hc_" + std::string(part);
    fixture.variables[base + "_before"] = fixture.variables[base];
    fixture.variables.erase(base);
  }
  PutPartition(fixture, "zg361_workforce_normal_exit_fact_receipt_hc_", 4, 1,
               2, 2, 1);
  for (const auto part : {"authorized", "available", "reserved", "occupied",
                          "frozen", "reclaimed"}) {
    const std::string base =
        "zg361_workforce_normal_exit_fact_receipt_hc_" + std::string(part);
    fixture.variables[base + "_after"] = fixture.variables[base];
    fixture.variables.erase(base);
  }
  boolean("formal_hc_active_before", true);
  boolean("formal_hc_active_after", false);
  fixture.variables
      ["zg361_workforce_normal_exit_fact_receipt_formal_hc_case"] = Number(777);
}

void PopulateRehire(Fixture &fixture) {
  PopulateSealed(fixture);
  fixture.variables["zg361_workforce_rehire_fact_state"] = Number(1);
  fixture.variables["zg361_workforce_rehire_fact_subject"] = Character(100);
  fixture.variables["zg361_workforce_rehire_fact_exit_owner"] = Character(200);
  fixture.variables["zg361_workforce_rehire_fact_exit_cycle"] = Number(7);
  fixture.variables["zg361_workforce_rehire_fact_exit_case"] = Number(903);
  fixture.variables["zg361_workforce_rehire_fact_exit_state"] = Number(6);
  fixture.variables["zg361_workforce_rehire_fact_exit_receipt_id"] = Number(7701);
  fixture.variables["zg361_workforce_rehire_fact_exit_receipt_hash"] = Number(9901);
  fixture.variables["zg361_workforce_rehire_fact_normal_exit_verified"] = Number(1);
  const auto copy_partition = [&](std::string_view stage) {
    for (const auto part : {"authorized", "available", "reserved", "occupied",
                            "frozen", "reclaimed"}) {
      fixture.variables["zg361_workforce_rehire_fact_exit_hc_" +
                        std::string(part) + "_" + std::string(stage)] =
          fixture.variables["zg361_workforce_normal_exit_fact_receipt_hc_" +
                            std::string(part) + "_" + std::string(stage)];
    }
  };
  copy_partition("before");
  copy_partition("after");
  fixture.variables["zg361_workforce_rehire_fact_exit_hc_destination_frozen"] =
      Number(1);
  fixture.variables
      ["zg361_workforce_rehire_fact_exit_hc_conservation_verified"] = Number(1);
  fixture.variables
      ["zg361_workforce_rehire_fact_exit_formal_hc_active_before"] = Number(1);
  fixture.variables
      ["zg361_workforce_rehire_fact_exit_formal_hc_active_after"] = Number(0);
  fixture.variables["zg361_workforce_rehire_fact_exit_formal_hc_case"] =
      Number(777);
}

bool Read(Fixture &fixture,
          xar::game::ZhongguoWorkforceNormalExitSnapshotV1 &output,
          xar::ck3_11906::ZhongguoWorkforceNormalExitSnapshotRequestV1 request =
              Request()) {
  return xar::ck3_11906::ReadZhongguoWorkforceNormalExitSnapshotV1(
             Environment(), Access(fixture), request, output) ==
         xar::game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::available;
}

bool TestLifecycleAndAllowlist() {
  xar::game::ZhongguoWorkforceNormalExitSnapshotV1 output{};
  Fixture offered;
  PopulateSource(offered);
  if (!Read(offered, output) ||
      output.lifecycle !=
          xar::game::ZhongguoWorkforceNormalExitLifecycleV1::pre ||
      !output.readiness.ready || output.readiness.pending_snapshot_ready ||
      output.readiness.current_hc_matches_stage_ready ||
      offered.variable_reads !=
          2 * xar::ck3_11906::
                  kZhongguoWorkforceNormalExitVariableAllowlist.size()) {
    std::cerr << "offered stage failed reason=" << output.unavailable_reason
              << " reads=" << offered.variable_reads << '\n';
    return false;
  }
  if (offered.requested_keys.size() != offered.variable_reads) return false;

  Fixture pending;
  PopulateSource(pending);
  PopulatePending(pending);
  if (!Read(pending, output) || !output.readiness.pending_snapshot_ready ||
      !output.readiness.current_hc_matches_stage_ready) {
    std::cerr << "pending stage failed reason=" << output.unavailable_reason
              << '\n';
    return false;
  }

  Fixture accepted;
  PopulateSource(accepted);
  PopulatePending(accepted);
  MakeSourceConsumed(accepted);
  accepted.variables["zg361_workforce_normal_exit_fact_state"] = Number(2);
  if (!Read(accepted, output) ||
      output.lifecycle !=
          xar::game::ZhongguoWorkforceNormalExitLifecycleV1::pre) {
    std::cerr << "accepted stage failed reason=" << output.unavailable_reason
              << '\n';
    return false;
  }

  Fixture migrating;
  PopulateMigrating(migrating);
  if (!Read(migrating, output) ||
      output.lifecycle !=
          xar::game::ZhongguoWorkforceNormalExitLifecycleV1::migrating ||
      !output.readiness.migration_delta_ready) {
    std::cerr << "migrating stage failed reason=" << output.unavailable_reason
              << '\n';
    return false;
  }

  Fixture sealed;
  PopulateSealed(sealed);
  if (!Read(sealed, output) ||
      output.lifecycle !=
          xar::game::ZhongguoWorkforceNormalExitLifecycleV1::sealed ||
      !output.readiness.sealed_receipt_ready ||
      !output.readiness.current_hc_matches_stage_ready) {
    std::cerr << "sealed stage failed reason=" << output.unavailable_reason
              << '\n';
    return false;
  }

  Fixture rehire;
  PopulateRehire(rehire);
  if (!Read(rehire, output) ||
      output.lifecycle !=
          xar::game::ZhongguoWorkforceNormalExitLifecycleV1::rehire_captured ||
      !output.readiness.rehire_capture_ready) {
    std::cerr << "rehire stage failed reason=" << output.unavailable_reason
              << '\n';
    return false;
  }
  const auto json =
      xar::ck3_11906::SerializeZhongguoWorkforceNormalExitSnapshotV1(output);
  return json.find("\"lifecycle\":\"rehire_captured\"") !=
             std::string::npos &&
         json.find("\"subject_allowlist_count\":94") != std::string::npos &&
         json.find("\"owner_allowlist_count\":0") != std::string::npos;
}

bool TestImmutableReceiptSurvivesLiveDrift() {
  Fixture fixture;
  PopulateSealed(fixture);
  PutPartition(fixture, "zg361_ch_hc_", 3, 2, 2, 2, 1);
  fixture.variables["zg361_we_formal_hc_active"] = Number(1);
  fixture.variables["zg361_we_formal_hc_active_case"] = Number(888);
  xar::game::ZhongguoWorkforceNormalExitSnapshotV1 output{};
  return Read(fixture, output) && output.readiness.sealed_receipt_ready &&
         !output.readiness.current_hc_matches_stage_ready &&
         output.readiness.ready;
}

bool TestHigherStageAndIdentityNegatives() {
  xar::game::ZhongguoWorkforceNormalExitSnapshotV1 output{};
  Fixture partial;
  PopulateSealed(partial);
  partial.variables.erase("zg361_workforce_normal_exit_fact_receipt_hash");
  if (Read(partial, output) || output.unavailable_reason != "case_inconsistent") {
    return false;
  }
  Fixture wrong_owner;
  PopulateSource(wrong_owner);
  if (Read(wrong_owner, output, Request(201)) ||
      output.unavailable_reason != "owner_filter_mismatch") {
    return false;
  }
  Fixture self;
  PopulateSource(self);
  self.variables["zg361_b2_m075_owner"] = Character(100);
  self.variables["zg361_b2_m075_object_owner"] = Character(100);
  if (Read(self, output, Request(100)) ||
      output.unavailable_reason != "not_received_self") {
    return false;
  }
  Fixture partial_rehire;
  PopulateSealed(partial_rehire);
  partial_rehire.variables["zg361_workforce_rehire_fact_state"] = Number(1);
  return !Read(partial_rehire, output) &&
         output.unavailable_reason == "case_inconsistent";
}

bool TestConservationAndSameFrame() {
  xar::game::ZhongguoWorkforceNormalExitSnapshotV1 output{};
  Fixture bad_delta;
  PopulateMigrating(bad_delta);
  bad_delta.variables["zg361_ch_hc_occupied"] = Number(3);
  bad_delta.variables["zg361_ch_hc_frozen"] = Number(1);
  if (Read(bad_delta, output) ||
      output.unavailable_reason != "case_inconsistent") {
    return false;
  }
  Fixture drift;
  PopulateSource(drift);
  drift.drift_rows = true;
  if (Read(drift, output) || output.unavailable_reason != "state_changed") {
    return false;
  }
  Fixture absent;
  PutPartition(absent, "zg361_ch_hc_", 4, 1, 3, 1, 1);
  absent.variables["zg361_we_formal_hc_active"] = Number(1);
  absent.variables["zg361_we_formal_hc_active_case"] = Number(777);
  return !Read(absent, output) && output.unavailable_reason == "case_not_found";
}

} // namespace

int main() {
  const bool lifecycle = TestLifecycleAndAllowlist();
  const bool immutable = TestImmutableReceiptSurvivesLiveDrift();
  const bool negatives = TestHigherStageAndIdentityNegatives();
  const bool conservation = TestConservationAndSameFrame();
  const bool ok = lifecycle && immutable && negatives && conservation;
  if (!ok) {
    std::cerr << "Workforce normal-exit lifecycle provider fixture failed: "
              << "lifecycle=" << lifecycle << " immutable=" << immutable
              << " negatives=" << negatives
              << " conservation=" << conservation << '\n';
    return 1;
  }
  return 0;
}
