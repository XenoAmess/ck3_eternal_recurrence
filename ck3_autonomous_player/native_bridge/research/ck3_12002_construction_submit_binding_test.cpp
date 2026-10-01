#include "ck3_12002_construction_submit_binding.hpp"

#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>

#include <windows.h>

namespace {

using namespace xar::ck3_12002;
using Phase = xar::ck3::shared::PlayerWorldBuildingDirectActionPhaseV1;
using Failure = xar::ck3::shared::PlayerWorldBuildingDirectActionFailureV1;
constexpr std::uintptr_t kModuleBase = 0x140000000ULL;

struct Fixture final {
  xar::ck3_11906::PlayerWorldBuildingSourceResultV1 source;
  xar::ck3_11906::PlayerWorldBuildingActionCandidateV1 candidate;
  std::uint32_t validators = 0;
  std::uint32_t materializers = 0;
  std::uint32_t receivers = 0;
  std::uint32_t releases = 0;
  bool allowed = true;
  bool accepted = true;
  bool receiver_keeps_ownership = false;
};

template <typename T>
T Field(const void* command, const std::size_t offset) {
  T result{};
  std::memcpy(&result, static_cast<const std::byte*>(command) + offset,
              sizeof(result));
  return result;
}

bool Validate(void* context, const void* command, bool& allowed) noexcept {
  auto& fixture = *static_cast<Fixture*>(context);
  ++fixture.validators;
  assert(Field<std::uintptr_t>(command, 0) ==
         kModuleBase + kConstructionBuildingPrimaryVtableRva);
  assert(Field<std::uintptr_t>(command, 0x18) ==
         kModuleBase + kConstructionBuildingSecondaryVtableRva);
  assert(Field<std::int32_t>(command, 0x20) == 29829);
  assert(Field<std::int32_t>(command, 0x24) == 2635);
  assert(Field<std::int32_t>(command, 0x28) == 1);
  assert(Field<std::int32_t>(command, 0x2C) == 24);
  assert(Field<std::uint32_t>(command, 0x0C) == 0);
  allowed = fixture.allowed;
  return true;
}

bool Materialize(void* context, void*, std::uintptr_t& owned) noexcept {
  ++static_cast<Fixture*>(context)->materializers;
  owned = 0xBEEF;
  return true;
}

bool Receive(void* context, std::uintptr_t& owned, std::uint32_t flags,
             bool& accepted, std::uint64_t& sequence) noexcept {
  auto& fixture = *static_cast<Fixture*>(context);
  ++fixture.receivers;
  assert(owned == 0xBEEF && flags == 7);
  accepted = fixture.accepted;
  sequence = accepted ? 7001 : 0;
  if (!fixture.receiver_keeps_ownership) owned = 0;
  return true;
}

bool Release(void* context, std::uintptr_t& owned) noexcept {
  ++static_cast<Fixture*>(context)->releases;
  assert(owned == 0xBEEF);
  owned = 0;
  return true;
}

Fixture MakeFixture() {
  Fixture result{};
  auto& source = result.source;
  source.source_available = true;
  source.native_final_legality_evaluated = true;
  source.native_cost_evaluated = true;
  source.player_gold_observed = true;
  source.snapshot_revision = 3;
  source.date_raw = 53168784;
  source.player_character_id = 29829;
  source.player_gold_raw = 50035659;
  source.active_constructions.push_back({2103, 2635, false, -1, -1, -1});
  xar::ck3_11906::PlayerWorldBuildingLegalSampleV1 row{};
  row.barony_title_id = 2103;
  row.province_id = 2635;
  row.building_type_id = 24;
  row.slot_index = 1;
  row.native_cost_observed = true;
  row.cost_raw_native[0] = 15000000;
  source.legal_samples.push_back(row);
  auto& candidate = result.candidate;
  candidate.ready = true;
  candidate.snapshot_revision = 3;
  candidate.proof_epoch = 91;
  candidate.date_raw = source.date_raw;
  candidate.actor_character_id = 29829;
  candidate.barony_title_id = 2103;
  candidate.province_id = 2635;
  candidate.building_type_id = 24;
  candidate.slot_index = 1;
  candidate.player_gold_before_raw = source.player_gold_raw;
  candidate.stock_gold_cost_raw = 15000000;
  candidate.gold_reserve_after_raw = 35035659;
  candidate.stock_cost_raw_native = row.cost_raw_native;
  return result;
}

ConstructionActionRequestV1 Request(Fixture& fixture) {
  ConstructionActionRequestV1 request{};
  request.exact_build_admitted = true;
  request.session_live = true;
  request.offline_fixture = true;
  request.module_base = kModuleBase;
  request.source = &fixture.source;
  request.candidate = &fixture.candidate;
  request.native_calls = {&fixture, false, Validate, nullptr,
                          Materialize, Receive, Release};
  return request;
}

xar::ck3_11906::MainThreadExecutionStampV1 Stamp() {
  xar::ck3_11906::MainThreadExecutionStampV1 stamp{};
  stamp.thread_id = GetCurrentThreadId();
  stamp.tls_context = 0xABCD;
  stamp.tls_main_thread_marker = 1;
  stamp.paused = true;
  stamp.pump_epoch = 91;
  stamp.date_raw = 53168784;
  return stamp;
}

void TestPendingAckAndFreshMaterial() {
  auto fixture = MakeFixture();
  const auto request = Request(fixture);
  ConstructionActionStateV1 state{};
  assert(xar::ck3_12002::SubmitPlayerWorldBuildingDirectActionV1(
      state, request, Stamp()));
  assert(state.phase == Phase::pending_receipt && !state.production_native_path);
  assert(state.receiver_command_sequence == 7001);
  assert(fixture.validators == 1 && fixture.materializers == 1 &&
         fixture.receivers == 1 && fixture.releases == 0);
  auto fresh = fixture.source;
  assert(!xar::ck3_12002::ObservePlayerWorldBuildingDirectActionReceiptV1(
      state, fresh, 92));
  fresh.active_constructions[0] = {2103, 2635, true, 24, 1, 29829};
  assert(!xar::ck3_12002::ObservePlayerWorldBuildingDirectActionReceiptV1(
      state, fresh, 91));
  assert(!xar::ck3_12002::SubmitPlayerWorldBuildingDirectActionV1(
      state, request, Stamp()));
  assert(state.failure == Failure::already_submitted && fixture.receivers == 1);
  assert(xar::ck3_12002::ObservePlayerWorldBuildingDirectActionReceiptV1(
      state, fresh, 92));
  assert(state.phase == Phase::applied);
}

void TestValidatorRejectionDoesNotQueue() {
  auto fixture = MakeFixture();
  fixture.allowed = false;
  ConstructionActionStateV1 state{};
  assert(!xar::ck3_12002::SubmitPlayerWorldBuildingDirectActionV1(
      state, Request(fixture), Stamp()));
  assert(state.phase == Phase::rejected && state.failure == Failure::validator);
  assert(fixture.validators == 1 && fixture.materializers == 0 &&
         fixture.receivers == 0);
}

void TestRejectedReceiverClosesLeftover() {
  auto fixture = MakeFixture();
  fixture.accepted = false;
  fixture.receiver_keeps_ownership = true;
  ConstructionActionStateV1 state{};
  assert(!xar::ck3_12002::SubmitPlayerWorldBuildingDirectActionV1(
      state, Request(fixture), Stamp()));
  assert(state.phase == Phase::rejected && state.failure == Failure::receiver);
  assert(fixture.receivers == 1 && fixture.releases == 1);
}

void TestSourceAndFrameBinding() {
  auto fixture = MakeFixture();
  fixture.candidate.stock_cost_raw_native[7] = 1;
  ConstructionActionStateV1 state{};
  assert(!xar::ck3_12002::SubmitPlayerWorldBuildingDirectActionV1(
      state, Request(fixture), Stamp()));
  assert(state.failure == Failure::candidate_drift && fixture.validators == 0);
  state = {};
  fixture = MakeFixture();
  auto stamp = Stamp();
  stamp.paused = false;
  assert(!xar::ck3_12002::SubmitPlayerWorldBuildingDirectActionV1(
      state, Request(fixture), stamp));
  assert(state.failure == Failure::frame_binding && fixture.validators == 0);
}

void TestOnlyMappedBuildingBinder() {
  const auto calls =
      xar::ck3_12002::BindCurrentProcessDomainConstructionExactNativeCallsV1(
          kModuleBase);
  assert(calls.production_exact_addresses && calls.validate_building != nullptr);
  assert(calls.validate_holding == nullptr && calls.materialize != nullptr &&
         calls.receive != nullptr && calls.release != nullptr);
  const auto empty =
      xar::ck3_12002::BindCurrentProcessDomainConstructionExactNativeCallsV1(0);
  assert(!empty.production_exact_addresses && empty.materialize == nullptr);
}

}  // namespace

int main() {
  TestPendingAckAndFreshMaterial();
  TestValidatorRejectionDoesNotQueue();
  TestRejectedReceiverClosesLeftover();
  TestSourceAndFrameBinding();
  TestOnlyMappedBuildingBinder();
  std::cout << "ck3-12002-construction-submit: GREEN_OFFLINE\n";
}
