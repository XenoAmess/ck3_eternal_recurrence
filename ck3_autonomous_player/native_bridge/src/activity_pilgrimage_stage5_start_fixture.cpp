#include "xar_bridge/activity_pilgrimage_stage5_start_v1.hpp"
#include "xar_bridge/ck3_12002_activity_feast_start.hpp"

#include <cstdlib>
#include <iostream>

namespace {
using namespace xar::bridge;
#define REQUIRE(x) do { if (!(x)) { std::cerr << "failed " << __LINE__ << ": " #x "\n"; std::abort(); } } while (false)

struct Fixture {
  ActivityPilgrimageStage5SnapshotV1 value{};
  int captures = 0;
  int commits = 0;
  bool commit_return = true;
  bool change_second = false;
  bool bad_prefix = false;
};

template <std::size_t N>
bool CopyPrefix(std::uintptr_t rva, std::uintptr_t expected,
                void *out, std::size_t size,
                const std::array<std::uint8_t, N> &prefix) noexcept {
  if (rva != expected || size != N) return false;
  std::memcpy(out, prefix.data(), N);
  return true;
}

bool Read(void *opaque, std::uintptr_t address, void *out,
          std::size_t size) noexcept {
  auto &f = *static_cast<Fixture *>(opaque);
  if (f.bad_prefix || address < 0x10000000) return false;
  const auto rva = address - 0x10000000;
  const auto sha = xar::ck3_12004::kExecutableSha256;
  return CopyPrefix(rva, Activity12004RvaV1(sha, xar::ck3_12002::kFeastCommitRva),
                    out, size, xar::ck3_12002::kFeastCommitPrefix) ||
         CopyPrefix(rva, Activity12004RvaV1(sha, xar::ck3_12002::kFeastFinalCanStartRva),
                    out, size, xar::ck3_12002::kFeastFinalCanStartPrefix) ||
         CopyPrefix(rva, Activity12004RvaV1(sha, xar::ck3_12002::kFeastFinalStage5BranchRva),
                    out, size, xar::ck3_12002::kFeastFinalStage5Prefix);
}

bool Capture(void *opaque, const ActivityPlannerDiagFrameV1 &,
             ActivityPilgrimageStage5SnapshotV1 &out) noexcept {
  auto &f = *static_cast<Fixture *>(opaque);
  out = f.value;
  if (++f.captures == 2 && f.change_second)
    ++out.quote.configuration_fingerprint;
  return true;
}

bool Commit(void *opaque, std::uintptr_t module,
            std::uintptr_t planner) noexcept {
  auto &f = *static_cast<Fixture *>(opaque);
  REQUIRE(module == 0x10000000 && planner == f.value.quote.planner);
  ++f.commits;
  return f.commit_return;
}

Fixture Make(std::string_view option_key = "pilgrimage_type_pious") {
  Fixture f{};
  const ActivityPlannerDiagFrameV1 frame{5, 100, 77, true, true, true, true};
  auto &q = f.value.quote;
  q.observed = true;
  q.kind = ActivityTypedPlannerKindV1::pilgrimage;
  q.frame = frame;
  q.planner = 0x1000; q.owner = 0x2000; q.activity_type = 0x3000;
  q.planning_stage = 5; q.normal_refresh_sequence = 7;
  q.configuration_fingerprint = 33;
  q.final_can_start_observed = true; q.final_can_start = true;
  q.known_name_resource_indices = {3, 7, 2, 9}; // Gold deliberately is not zero.
  for (const auto i : q.known_name_resource_indices) q.named_cost_verified[i] = true;
  q.configured_cost_raw[3] = 10;
  auto &selected = q.selection;
  selected.observed = true; selected.kind = q.kind; selected.frame = frame;
  selected.planner = q.planner; selected.activity_type = q.activity_type;
  selected.planning_stage = 5; selected.native_selected_option = 0x4000;
  selected.native_option_id = 0;
  const auto key = option_key;
  std::memcpy(selected.option_key.data(), key.data(), key.size());
  selected.option_key_size = static_cast<std::uint16_t>(key.size());
  f.value.destination = {true, q.kind, frame, q.planner, q.activity_type, 5, 1, 10};
  f.value.balance_frame = frame;
  f.value.balance_available[3] = true; f.value.balance_raw[3] = 100;
  f.value.hosted.status = ActivityHostedIdentityStatusV1::observed;
  f.value.hosted.frame = {5, 100, 77, true, true, true, true};
  return f;
}

ActivityPilgrimageStage5StartEnvironmentV1 Environment(Fixture &f) {
  return {true, xar::ck3_12004::kExecutableSha256, 0x10000000,
          &f, &Read, &Capture, &Commit};
}

ActivityPilgrimageStage5StartRequestV1 Request(const Fixture &f) {
  ActivityPilgrimageStage5StartRequestV1 r{};
  r.expected = f.value.quote.frame; r.policy_approved = true;
  r.destination_province_id = 10; r.reserve_raw[3] = 5;
  return r;
}

void RejectCases() {
  for (int mutation = 0; mutation < 16; ++mutation) {
    auto f = Make(); auto r = Request(f); auto e = Environment(f);
    ActivityPilgrimageStartLedgerV1 ledger{};
    switch (mutation) {
    case 0: r.policy_approved = false; break;
    case 1: e.admitted_executable_sha256 = "old-executable"; break;
    case 2: f.bad_prefix = true; break;
    case 3: r.expected.paused = false; break;
    case 4: f.value.quote.selection.option_key[0] = 'x'; break;
    case 5: f.value.quote.configured_cost_raw[8] = 1; break;
    case 6: // A forged verification bit cannot admit an unknown positive index.
      f.value.quote.configured_cost_raw[8] = 1;
      f.value.quote.named_cost_verified[8] = true;
      f.value.balance_available[8] = true; f.value.balance_raw[8] = 100; break;
    case 7: f.value.balance_available[3] = false; break;
    case 8: f.value.balance_raw[3] = 14; break;
    case 9: r.reserve_raw[3] = (std::numeric_limits<std::int64_t>::max)(); break;
    case 10: f.change_second = true; break;
    case 11: f.value.destination.province_id = 11; break;
    case 12: f.value.quote.final_can_start = false; break;
    case 13: f.value.quote.known_name_resource_indices[1] = 3; break;
    case 14: f.value.quote.configured_cost_raw[8] = -1; break;
    case 15: f.value.quote.configured_cost_raw[7] = 1; break; // Treasury balance unavailable.
    }
    const auto out = StartActivityPilgrimageStage5V1(e, r, ledger);
    REQUIRE(!out.accepted && !out.invoked && f.commits == 0);
    REQUIRE(ledger.state == ActivityPilgrimageStartStateV1::idle);
  }
}

ActivityHostedIdentityV1 Identity(std::uint32_t id) {
  ActivityHostedIdentityV1 out{};
  out.activity_id = id; out.host_character_id = 77;
  const auto key = kOrdinaryPilgrimagePiousContractV1.activity_key;
  std::memcpy(out.type_key.data(), key.data(), key.size());
  out.type_key_size = static_cast<std::uint8_t>(key.size());
  out.terminal_flags_observed = true;
  return out;
}

void SubmissionAndReconciliation(bool returned, std::string_view option_key) {
  auto f = Make(option_key); f.commit_return = returned;
  // A prior terminal identity occupies the same low slot with old generation.
  f.value.hosted.hosted_count = 1;
  f.value.hosted.hosted[0] = Identity(0x02000005);
  f.value.hosted.hosted[0].native_completed = true;
  auto e = Environment(f); auto r = Request(f);
  ActivityPilgrimageStartLedgerV1 ledger{};
  const auto submitted = StartActivityPilgrimageStage5V1(e, r, ledger);
  REQUIRE(submitted.accepted && submitted.invoked && f.captures == 2 && f.commits == 1);
  REQUIRE(ledger.state == (returned ? ActivityPilgrimageStartStateV1::submitted_pending
                                   : ActivityPilgrimageStartStateV1::submission_outcome_unknown));
  REQUIRE(!StartActivityPilgrimageStage5V1(e, r, ledger).invoked && f.commits == 1);
  auto after = f.value.hosted; after.frame.revision = 6;
  REQUIRE(ReconcileActivityPilgrimageStartV1(ledger, after).status ==
          ActivityPilgrimageReconcileStatusV1::pending);
  after.hosted_count = 2; after.hosted[1] = Identity(0xFE000005);
  const auto read = ReconcileActivityPilgrimageStartV1(ledger, after);
  REQUIRE(read.status == ActivityPilgrimageReconcileStatusV1::identity_observed);
  REQUIRE(read.identity.activity_id == 0xFE000005);
  REQUIRE(!read.identity.native_completed && !read.identity.native_invalidated);
  REQUIRE(ledger.observed_activity_id == 0xFE000005);
  REQUIRE(!StartActivityPilgrimageStage5V1(e, r, ledger).invoked && f.commits == 1);
  after.hosted_count = 3; after.hosted[2] = Identity(0x03000009);
  REQUIRE(ReconcileActivityPilgrimageStartV1(ledger, after).status ==
          ActivityPilgrimageReconcileStatusV1::ambiguous_new_identities);
  after.hosted_count = 2; after.frame.revision = 5;
  REQUIRE(ReconcileActivityPilgrimageStartV1(ledger, after).status ==
          ActivityPilgrimageReconcileStatusV1::rejected_observation);
  REQUIRE(ledger.observed_activity_id == 0xFE000005 && f.commits == 1);
}
} // namespace

int main() {
  RejectCases();
  for (const auto key : {"pilgrimage_type_pious", "pilgrimage_type_worldly", "pilgrimage_type_hajj"}) {
    SubmissionAndReconciliation(true, key);
    SubmissionAndReconciliation(false, key);
  }
  std::cout << "owned typed Start safety fixture PASS (not native/live qualification)\n";
}
