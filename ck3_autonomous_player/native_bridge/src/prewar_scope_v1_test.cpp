#include "xar_bridge/prewar_scope_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string_view>

namespace {

template <typename T, std::size_t N>
void Store(std::array<std::byte, N> &storage, std::size_t offset,
           const T &value) {
  std::memcpy(storage.data() + offset, &value, sizeof(value));
}

template <typename T>
void StoreRaw(void *storage, std::size_t offset, const T &value) {
  std::memcpy(static_cast<std::byte *>(storage) + offset, &value,
              sizeof(value));
}

constexpr std::int32_t kActor = 29'829;
constexpr std::int32_t kTarget = 29'097;
constexpr std::int32_t kOther = 31'111;
constexpr std::int32_t kActorUnitId = 0x01000001;
constexpr std::int32_t kTargetUnitId = 0x02000002;
constexpr std::int32_t kOtherUnitId = 0x03000003;
constexpr std::int32_t kActorCArmyId = 0x04000001;
constexpr std::int32_t kTargetCArmyId = 0x05000002;
constexpr std::int32_t kOtherCArmyId = 0x06000003;

std::array<std::byte, 0x30> g_storage{};
std::array<std::byte, 4 * 0x10> g_slots{};
std::array<std::byte, 0x30> g_carmy_storage{};
std::array<std::byte, 4 * 0x10> g_carmy_slots{};
std::array<std::byte, 0x180> g_actor_unit{};
std::array<std::byte, 0x180> g_target_unit{};
std::array<std::byte, 0x180> g_other_unit{};
std::array<std::byte, 0x130> g_actor_carmy{};
std::array<std::byte, 0x130> g_target_carmy{};
std::array<std::byte, 0x130> g_other_carmy{};
std::array<std::byte, 0x20> g_province_100{};
std::array<std::byte, 0x20> g_province_101{};
std::array<std::byte, 0x20> g_province_102{};
std::array<std::byte, 0x20> g_province_200{};
std::array<std::byte, 4> g_route_101{};
std::array<std::byte, 4> g_route_102{};
std::array<void *, 2> g_actor_route{};
void *g_storage_pointer = nullptr;
void *g_carmy_storage_pointer = nullptr;
int g_resolve_calls = 0;
int g_mutate_owner_after_resolve_call = -1;

void *ResolveProvince(void *, std::int32_t province_id) {
  ++g_resolve_calls;
  void *result = nullptr;
  switch (province_id) {
  case 100:
    result = g_province_100.data();
    break;
  case 101:
    result = g_province_101.data();
    break;
  case 102:
    result = g_province_102.data();
    break;
  case 200:
    result = g_province_200.data();
    break;
  default:
    break;
  }
  if (g_resolve_calls == g_mutate_owner_after_resolve_call) {
    StoreRaw(g_actor_unit.data(), 0x174, kOther);
  }
  return result;
}

void ResetFixture() {
  g_storage.fill(std::byte{});
  g_slots.fill(std::byte{});
  g_carmy_storage.fill(std::byte{});
  g_carmy_slots.fill(std::byte{});
  g_actor_unit.fill(std::byte{});
  g_target_unit.fill(std::byte{});
  g_other_unit.fill(std::byte{});
  g_actor_carmy.fill(std::byte{});
  g_target_carmy.fill(std::byte{});
  g_other_carmy.fill(std::byte{});
  g_province_100.fill(std::byte{});
  g_province_101.fill(std::byte{});
  g_province_102.fill(std::byte{});
  g_province_200.fill(std::byte{});
  g_route_101.fill(std::byte{});
  g_route_102.fill(std::byte{});
  g_actor_route = {g_route_101.data(), g_route_102.data()};
  g_resolve_calls = 0;
  g_mutate_owner_after_resolve_call = -1;

  Store(g_province_100, 0x10, std::int32_t{100});
  Store(g_province_101, 0x10, std::int32_t{101});
  Store(g_province_102, 0x10, std::int32_t{102});
  Store(g_province_200, 0x10, std::int32_t{200});
  Store(g_route_101, 0x00, std::int32_t{101});
  Store(g_route_102, 0x00, std::int32_t{102});

  Store(g_actor_unit, 0x10, kActorUnitId);
  Store(g_actor_unit, 0x178, kActorCArmyId);
  Store(g_actor_unit, 0x174, kActor);
  Store(g_actor_unit, 0x20, static_cast<void *>(g_province_100.data()));
  Store(g_actor_unit, 0x30, static_cast<void *>(g_province_101.data()));
  Store(g_actor_unit, 0x38, static_cast<void *>(g_actor_route.data()));
  Store(g_actor_unit, 0x40, std::int32_t{2});
  Store(g_actor_unit, 0x44, std::int32_t{2});

  Store(g_target_unit, 0x10, kTargetUnitId);
  Store(g_target_unit, 0x178, kTargetCArmyId);
  Store(g_target_unit, 0x174, kTarget);
  Store(g_target_unit, 0x20, static_cast<void *>(g_province_200.data()));

  Store(g_other_unit, 0x10, kOtherUnitId);
  Store(g_other_unit, 0x178, kOtherCArmyId);
  Store(g_other_unit, 0x174, kOther);

  Store(g_actor_carmy, 0x10, kActorCArmyId);
  Store(g_actor_carmy, 0x124, kActorUnitId);
  Store(g_target_carmy, 0x10, kTargetCArmyId);
  Store(g_target_carmy, 0x124, kTargetUnitId);
  Store(g_other_carmy, 0x10, kOtherCArmyId);
  Store(g_other_carmy, 0x124, kOtherUnitId);

  StoreRaw(g_slots.data(), 1 * 0x10 + 0x08,
           static_cast<void *>(g_actor_unit.data()));
  StoreRaw(g_slots.data(), 2 * 0x10 + 0x08,
           static_cast<void *>(g_target_unit.data()));
  StoreRaw(g_slots.data(), 3 * 0x10 + 0x08,
           static_cast<void *>(g_other_unit.data()));
  Store(g_storage, 0x20, static_cast<void *>(g_slots.data()));
  Store(g_storage, 0x2C, std::int32_t{4});
  g_storage_pointer = g_storage.data();

  StoreRaw(g_carmy_slots.data(), 1 * 0x10 + 0x08,
           static_cast<void *>(g_actor_carmy.data()));
  StoreRaw(g_carmy_slots.data(), 2 * 0x10 + 0x08,
           static_cast<void *>(g_target_carmy.data()));
  StoreRaw(g_carmy_slots.data(), 3 * 0x10 + 0x08,
           static_cast<void *>(g_other_carmy.data()));
  Store(g_carmy_storage, 0x20,
        static_cast<void *>(g_carmy_slots.data()));
  Store(g_carmy_storage, 0x2C, std::int32_t{4});
  g_carmy_storage_pointer = g_carmy_storage.data();
}

int Fail(std::string_view message) {
  std::cerr << message << '\n';
  return 1;
}

xar::ck3_11906::PrewarScopeRequestV1 Request() {
  return {74, 53'175'816, kActor, kTarget};
}

} // namespace

int main() {
  using namespace xar::ck3_11906;
  ResetFixture();
  const PrewarScopeBindingsV1 bindings{&g_storage_pointer,
                                       &g_carmy_storage_pointer,
                                       ResolveProvince};
  PrewarScopeObservationV1 output{};
  if (ReadDeclarationBoundPrewarScopeV1(bindings, reinterpret_cast<void *>(1),
                                        true, true, Request(), output) !=
      ReadPrewarScopeStatusV1::available_primary_scope) {
    return Fail("exact primary prewar scope was unavailable");
  }
  if (output.primary_participants.size() != 2 ||
      output.primary_participants[0].character_id != kActor ||
      output.primary_participants[1].character_id != kTarget ||
      output.primary_raised_armies.size() != 2 ||
      output.primary_raised_armies[0].army_id != kActorUnitId ||
      output.primary_raised_armies[0].native_carmy_id != kActorCArmyId ||
      !output.primary_raised_armies[0].has_move_target_province ||
      output.primary_raised_armies[0].move_target_province_id != 101 ||
      output.primary_raised_armies[0].route_province_ids !=
          std::vector<std::int32_t>({101, 102}) ||
      output.primary_raised_armies[1].army_id != kTargetUnitId ||
      output.primary_raised_armies[1].native_carmy_id != kTargetCArmyId ||
      output.primary_raised_armies[1].has_move_target_province ||
      !output.primary_raised_armies[1].route_province_ids.empty()) {
    return Fail("primary owner/current/route projection drifted");
  }
  if (!output.readiness.exact_build_ready ||
      !output.readiness.primary_participants_ready ||
      !output.readiness.primary_raised_armies_ready ||
      output.readiness.native_join_bounds_ready ||
      output.readiness.declaration_objective_provinces_ready ||
      output.readiness.contact_geometry_ready ||
      output.readiness.native_arrival_timeline_ready ||
      output.readiness.combat_v3_prewar_scope_ready ||
      output.readiness.war_entry_forecast_inputs_ready) {
    return Fail("partial prewar readiness claimed an unresolved domain");
  }

  output = {};
  if (ReadDeclarationBoundPrewarScopeV1(bindings, reinterpret_cast<void *>(1),
                                        true, false, Request(), output) !=
          ReadPrewarScopeStatusV1::requires_paused ||
      output.failure_stage != "paused_required") {
    return Fail("running frame did not fail closed");
  }

  ResetFixture();
  Store(g_other_unit, 0x10, std::int32_t{0x03000002});
  output = {};
  if (ReadDeclarationBoundPrewarScopeV1(bindings, reinterpret_cast<void *>(1),
                                        true, true, Request(), output) !=
          ReadPrewarScopeStatusV1::unavailable ||
      output.failure_stage != "unit_identity") {
    return Fail("global CUnit identity drift was not rejected");
  }

  ResetFixture();
  Store(g_route_102, 0x00, std::int32_t{999});
  output = {};
  if (ReadDeclarationBoundPrewarScopeV1(bindings, reinterpret_cast<void *>(1),
                                        true, true, Request(), output) !=
          ReadPrewarScopeStatusV1::unavailable ||
      output.failure_stage != "unit_route") {
    return Fail("unresolved route ProvinceID was not rejected");
  }

  ResetFixture();
  Store(g_actor_carmy, 0x124, kTargetUnitId);
  output = {};
  if (ReadDeclarationBoundPrewarScopeV1(bindings, reinterpret_cast<void *>(1),
                                        true, true, Request(), output) !=
          ReadPrewarScopeStatusV1::unavailable ||
      output.failure_stage != "native_carmy_identity") {
    return Fail("CArmy public CUnit backlink drift was not rejected");
  }

  ResetFixture();
  // First sample makes five resolver calls: actor current + move target + two
  // route rows + target current.  Mutating after the fifth retains sample one and makes
  // sample two differ, exercising the same-frame atomicity gate.
  g_mutate_owner_after_resolve_call = 5;
  output = {};
  if (ReadDeclarationBoundPrewarScopeV1(bindings, reinterpret_cast<void *>(1),
                                        true, true, Request(), output) !=
          ReadPrewarScopeStatusV1::unavailable ||
      output.failure_stage != "same_frame_primary_army_scope") {
    return Fail("same-frame primary owner drift was not rejected");
  }

  output = {};
  auto invalid = Request();
  invalid.effective_target_character_id = invalid.actor_character_id;
  if (ReadDeclarationBoundPrewarScopeV1(bindings, reinterpret_cast<void *>(1),
                                        true, true, invalid, output) !=
          ReadPrewarScopeStatusV1::invalid_request ||
      output.failure_stage != "primary_participant_identity") {
    return Fail("ambiguous primary participant request was accepted");
  }

  return 0;
}
