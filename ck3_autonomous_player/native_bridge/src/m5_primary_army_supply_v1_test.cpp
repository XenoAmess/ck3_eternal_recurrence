#include "xar_bridge/m5_primary_army_supply_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string_view>

namespace {

template <typename T, std::size_t N>
void Store(std::array<std::byte, N> &buffer, std::size_t offset,
           const T &value) {
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}

constexpr std::int32_t kActorUnitId = 0x01000001;
constexpr std::int32_t kActorCArmyId = 0x04000001;
constexpr std::int32_t kTargetUnitId = 0x02000002;
constexpr std::int32_t kTargetCArmyId = 0x05000002;

std::array<std::byte, 0x30> g_storage{};
std::array<std::byte, 3 * 0x10> g_slots{};
std::array<std::byte, 0x188> g_actor_carmy{};
std::array<std::byte, 0x188> g_target_carmy{};
void *g_storage_pointer = nullptr;

void ResetFixture() {
  g_storage.fill(std::byte{});
  g_slots.fill(std::byte{});
  g_actor_carmy.fill(std::byte{});
  g_target_carmy.fill(std::byte{});
  Store(g_actor_carmy, 0x10, kActorCArmyId);
  Store(g_actor_carmy, 0x124, kActorUnitId);
  Store(g_actor_carmy, 0x180, std::int64_t{7'500'000});
  Store(g_target_carmy, 0x10, kTargetCArmyId);
  Store(g_target_carmy, 0x124, kTargetUnitId);
  Store(g_target_carmy, 0x180, std::int64_t{0});
  Store(g_slots, 1 * 0x10 + 0x08,
        static_cast<void *>(g_actor_carmy.data()));
  Store(g_slots, 2 * 0x10 + 0x08,
        static_cast<void *>(g_target_carmy.data()));
  Store(g_storage, 0x20, static_cast<void *>(g_slots.data()));
  Store(g_storage, 0x2C, std::int32_t{3});
  g_storage_pointer = g_storage.data();
}

xar::ck3_11906::PrewarScopeObservationV1 Scope() {
  using namespace xar::ck3_11906;
  PrewarScopeObservationV1 scope{};
  scope.status = ReadPrewarScopeStatusV1::available_primary_scope;
  scope.snapshot_revision = 74;
  scope.date_raw = 53'175'816;
  scope.readiness.exact_build_ready = true;
  scope.readiness.primary_participants_ready = true;
  scope.readiness.primary_raised_armies_ready = true;
  scope.primary_raised_armies = {
      {.army_id = kActorUnitId,
       .native_carmy_id = kActorCArmyId,
       .owner_character_id = 29'829,
       .side = PrewarSideV1::attacker},
      {.army_id = kTargetUnitId,
       .native_carmy_id = kTargetCArmyId,
       .owner_character_id = 29'097,
       .side = PrewarSideV1::defender},
  };
  return scope;
}

int Fail(std::string_view message) {
  std::cerr << message << '\n';
  return 1;
}

} // namespace

int main() {
  using namespace xar::ck3_11906;
  ResetFixture();
  auto scope = Scope();
  M5PrimaryArmySupplyObservationV1 output{};
  if (ReadM5PrimaryArmySupplyV1(&g_storage_pointer, true, true, scope,
                                output) !=
          M5PrimaryArmySupplyStatusV1::available ||
      output.snapshot_revision != 74 || output.date_raw != 53'175'816 ||
      output.rows.size() != 2 ||
      output.rows[0].army_id != kActorUnitId ||
      output.rows[0].native_carmy_id != kActorCArmyId ||
      output.rows[0].current_supply_raw != 7'500'000 ||
      output.rows[0].current_supply_scale != 100'000 ||
      output.rows[1].army_id != kTargetUnitId ||
      output.rows[1].current_supply_raw != 0) {
    return Fail("current raw supply, zero and identities were not projected");
  }

  Store(g_actor_carmy, 0x10, std::int32_t{0x06000001});
  if (ReadM5PrimaryArmySupplyV1(&g_storage_pointer, true, true, scope,
                                output) !=
          M5PrimaryArmySupplyStatusV1::unavailable ||
      output.failure_stage != "carmy_identity" || !output.rows.empty()) {
    return Fail("stale full-generation CArmy identity was accepted");
  }
  ResetFixture();
  Store(g_actor_carmy, 0x124, kTargetUnitId);
  if (ReadM5PrimaryArmySupplyV1(&g_storage_pointer, true, true, scope,
                                output) !=
          M5PrimaryArmySupplyStatusV1::unavailable ||
      output.failure_stage != "carmy_identity") {
    return Fail("wrong CUnit backlink was accepted");
  }

  ResetFixture();
  if (ReadM5PrimaryArmySupplyV1(&g_storage_pointer, true, false, scope,
                                output) !=
          M5PrimaryArmySupplyStatusV1::requires_paused ||
      output.failure_stage != "paused_required") {
    return Fail("running frame was accepted");
  }
  scope.readiness.primary_raised_armies_ready = false;
  if (ReadM5PrimaryArmySupplyV1(&g_storage_pointer, true, true, scope,
                                output) !=
          M5PrimaryArmySupplyStatusV1::invalid_scope ||
      output.failure_stage != "primary_scope_not_authenticated") {
    return Fail("unauthenticated primary scope was accepted");
  }
  scope = Scope();
  scope.primary_raised_armies.clear();
  if (ReadM5PrimaryArmySupplyV1(&g_storage_pointer, true, true, scope,
                                output) !=
          M5PrimaryArmySupplyStatusV1::available ||
      !output.rows.empty()) {
    return Fail("no raised primary army was not available empty");
  }
  std::cout << "m5 primary current supply source GREEN\n";
  return 0;
}
