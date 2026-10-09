#include "../src/ck3_12004_construction_submit_binding.hpp"
#include "../src/player_world_building_private_action_latch_v1.hpp"

#include <windows.h>

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>

namespace {
using namespace xar::ck3_11906;
using namespace xar::ck3_12004;
constexpr std::uintptr_t kOfflineModule = 0x140000000ULL;

struct Calls {
  PlayerWorldBuildingActionCandidateV1 candidate{};
  std::uint32_t validators = 0;
  std::uint32_t materializers = 0;
  std::uint32_t receivers = 0;
};

template <typename T> T Field(const void *command, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(command) + offset, sizeof(value));
  return value;
}

bool Validate(void *context, const void *command, bool &allowed) noexcept {
  auto &calls = *static_cast<Calls *>(context);
  ++calls.validators;
  const auto &candidate = calls.candidate;
  allowed = Field<std::int32_t>(command, 0x20) == candidate.actor_character_id &&
      Field<std::int32_t>(command, 0x24) == candidate.province_id &&
      Field<std::int32_t>(command, 0x28) == candidate.slot_index &&
      Field<std::int32_t>(command, 0x2C) == candidate.building_type_id;
  return true;
}

bool Materialize(void *context, void *, std::uintptr_t &owned) noexcept {
  ++static_cast<Calls *>(context)->materializers;
  owned = 0xBEEF;
  return true;
}

bool Receive(void *context, std::uintptr_t &owned, std::uint32_t flags,
             bool &accepted, std::uint64_t &sequence) noexcept {
  auto &calls = *static_cast<Calls *>(context);
  ++calls.receivers;
  accepted = owned == 0xBEEF && flags == kConstructionReceiverFlags;
  sequence = accepted ? calls.receivers : 0;
  owned = 0;
  return true;
}

bool Release(void *, std::uintptr_t &owned) noexcept {
  owned = 0;
  return true;
}

PlayerWorldBuildingLegalSampleV1 Sample(std::int32_t barony, std::int32_t province,
                                      std::int32_t slot) {
  PlayerWorldBuildingLegalSampleV1 row{};
  row.barony_title_id = barony;
  row.province_id = province;
  row.building_type_id = 604;
  row.slot_index = slot;
  row.building_key = "cereal_fields_01";
  row.native_cost_observed = true;
  row.cost_raw_native[0] = 14250000;
  return row;
}

// The source-shaped IDs/amounts are explicit offline DTO inputs. This fixture
// does not map a game definition registry or execute a stock game command.
PlayerWorldBuildingSourceResultV1 FirstSource() {
  PlayerWorldBuildingSourceResultV1 source{};
  source.source_available = true;
  source.native_final_legality_evaluated = true;
  source.native_cost_evaluated = true;
  source.player_gold_observed = true;
  source.completed_buildings_observed = true;
  source.player_gold_raw = 83667022;
  source.snapshot_revision = 2;
  source.date_raw = 53288568;
  source.player_character_id = 29829;
  source.active_constructions.push_back({2103, 2635, false});
  source.active_constructions.push_back({2106, 2644, false});
  source.legal_samples.push_back(Sample(2103, 2635, 3));
  return source;
}

bool Submit(Calls &calls, PlayerWorldBuildingPrivateActionLatchV1 &latch,
            const PlayerWorldBuildingSourceResultV1 &source, std::uint64_t proof) {
  if (latch.may_have_submitted) return false;
  calls.candidate = SelectPlayerWorldBuildingActionCandidateV1(source, proof, 20000000);
  if (!calls.candidate.ready) return false;
  ConstructionActionRequestV1 request{};
  request.exact_build_admitted = true;
  request.session_live = true;
  request.offline_fixture = true;
  request.module_base = kOfflineModule;
  request.source = &source;
  request.candidate = &calls.candidate;
  request.native_calls = {&calls, false, Validate, nullptr, Materialize, Receive, Release};
  MainThreadExecutionStampV1 stamp{};
  stamp.thread_id = GetCurrentThreadId();
  stamp.tls_context = 0xABCD;
  stamp.tls_main_thread_marker = 1;
  stamp.paused = true;
  stamp.pump_epoch = proof;
  stamp.date_raw = source.date_raw;
  ConstructionActionStateV1 state{};
  BeginPlayerWorldBuildingPrivateActionV1(latch);
  const bool accepted = xar::ck3_12004::SubmitPlayerWorldBuildingDirectActionV1(
      state, request, stamp);
  RememberPlayerWorldBuildingPrivateActionV1(latch, calls.candidate,
                                            state.materialize_calls, state.receiver_calls);
  return accepted;
}

bool Check(bool value, const char *message) {
  if (!value) std::cerr << "RED " << message << '\n';
  return value;
}
} // namespace

int main() {
  {
    Calls calls{};
    PlayerWorldBuildingPrivateActionLatchV1 latch{};
    const auto first = FirstSource();
    if (!Check(Submit(calls, latch, first, 100), "first real actual4 submit")) return 1;
    auto material = first;
    material.snapshot_revision = 3;
    material.player_gold_raw = 69417022;
    material.active_constructions[0] = {2103, 2635, true, 604, 3, 29829};
    if (!Check(ObservePlayerWorldBuildingPrivateActionMaterialV1(latch, material, 101)
               && !latch.may_have_submitted, "fresh first active material releases old latch")) return 1;
    auto second = material;
    second.snapshot_revision = 4;
    second.date_raw += 24;
    second.legal_samples = {Sample(2106, 2644, 2)};
    if (!Check(Submit(calls, latch, second, 102) && calls.receivers == 2 &&
               latch.submitted.barony_title_id == 2106 && latch.submitted.slot_index == 2,
               "different legal second submit passes after first receipt")) return 1;
  }
  {
    Calls calls{};
    PlayerWorldBuildingPrivateActionLatchV1 latch{};
    const auto first = FirstSource();
    if (!Check(Submit(calls, latch, first, 200), "unknown case first submit")) return 1;
    auto no_material = first;
    no_material.snapshot_revision = 3;
    if (!Check(!ObservePlayerWorldBuildingPrivateActionMaterialV1(latch, no_material, 201)
               && latch.may_have_submitted && !Submit(calls, latch, no_material, 202)
               && calls.receivers == 1, "unknown material keeps existing unresolved behavior")) return 1;
  }
  {
    Calls calls{};
    PlayerWorldBuildingPrivateActionLatchV1 latch{};
    const auto first = FirstSource();
    if (!Check(Submit(calls, latch, first, 300), "completed case first submit")) return 1;
    auto completed = first;
    completed.snapshot_revision = 3;
    completed.completed_buildings.push_back({2103, 2635, 604, 3, "cereal_fields_01"});
    if (!Check(ObservePlayerWorldBuildingPrivateActionMaterialV1(latch, completed, 301)
               && !latch.may_have_submitted, "observed first completed inventory releases latch")) return 1;
  }
  std::cout << "{\"status\":\"GREEN\",\"fixture\":\"construction_latch_lifecycle12004\","
               "\"scenes\":3,\"actual4_submit_calls\":4,\"live\":false,\"game_calls\":0}\n";
  return 0;
}
