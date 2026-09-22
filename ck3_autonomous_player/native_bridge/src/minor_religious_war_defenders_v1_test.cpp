#include "xar_bridge/minor_religious_war_defenders_v1.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace {

constexpr std::int32_t kActorId = 0x01000001;
constexpr std::int32_t kDefenderId = 0x02000002;
constexpr std::int32_t kJoinerAId = 0x03000003;
constexpr std::int32_t kJoinerBId = 0x04000004;

struct Fixture {
  alignas(void *) std::array<std::byte, 0x40> store{};
  alignas(void *) std::array<std::byte, 0x80> slots{};
  alignas(void *) std::array<std::byte, 0x400> actor{};
  alignas(void *) std::array<std::byte, 0x400> defender{};
  alignas(void *) std::array<std::byte, 0x400> joiner_a{};
  alignas(void *) std::array<std::byte, 0x400> joiner_b{};
  alignas(void *) std::array<std::byte, 0x320> power_actor{};
  alignas(void *) std::array<std::byte, 0x320> power_defender{};
  alignas(void *) std::array<std::byte, 0x320> power_a{};
  alignas(void *) std::array<std::byte, 0x320> power_b{};
  void *store_slot = store.data();
  void *fallback_slot = nullptr;
  std::array<void *, 2> returned{};
  std::int32_t returned_count = 0;
  std::int32_t frees = 0;
};

Fixture *g_fixture = nullptr;

template <typename Value>
void Put(void *base, std::size_t offset, Value value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}

void SetCharacter(Fixture &fixture, void *character, std::int32_t id,
                  void *power, std::int64_t power_raw) {
  Put(character, 0x18, id);
  Put(character, 0x1B8, power);
  if (power != nullptr) Put(power, 0x308, power_raw);
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  Put(fixture.slots.data(), static_cast<std::size_t>(index) * 0x10 + 0x08,
      character);
}

void Collect(void *, void *,
             xar::ck3_11906::NativeCharacterPointerVectorV1 *out) {
  assert(g_fixture != nullptr);
  if (g_fixture->returned_count == 0) return;
  auto *copy = new void *[static_cast<std::size_t>(g_fixture->returned_count)];
  for (std::int32_t i = 0; i < g_fixture->returned_count; ++i)
    copy[i] = g_fixture->returned[static_cast<std::size_t>(i)];
  out->data = copy;
  out->capacity = g_fixture->returned_count;
  out->count = g_fixture->returned_count;
}

void Free(void *, void *data, std::uint64_t element_size) {
  assert(element_size == 8);
  delete[] static_cast<void **>(data);
  ++g_fixture->frees;
}

xar::ck3_11906::MinorReligiousDefenderEnvironmentV1 Environment(
    Fixture &fixture) {
  xar::ck3_11906::MinorReligiousDefenderEnvironmentV1 result{};
  result.character_storage_slot = &fixture.store_slot;
  result.character_fallback_slot = &fixture.fallback_slot;
  result.allocator = &fixture;
  result.collector = &Collect;
  result.fixture_free = &Free;
  result.offline_fixture_overrides = true;
  return result;
}

void Initialize(Fixture &fixture) {
  Put(fixture.store.data(), 0x20, fixture.slots.data());
  Put(fixture.store.data(), 0x2C, std::int32_t{8});
  SetCharacter(fixture, fixture.actor.data(), kActorId,
               fixture.power_actor.data(),
               5'000'000);
  SetCharacter(fixture, fixture.defender.data(), kDefenderId,
               fixture.power_defender.data(), 900'000);
  SetCharacter(fixture, fixture.joiner_a.data(), kJoinerAId,
               fixture.power_a.data(),
               1'250'000);
  SetCharacter(fixture, fixture.joiner_b.data(), kJoinerBId,
               fixture.power_b.data(),
               2'500'000);
}

void TestReadsCharacterPointersAndPowers() {
  Fixture fixture{};
  Initialize(fixture);
  g_fixture = &fixture;
  fixture.returned = {fixture.joiner_a.data(), fixture.joiner_b.data()};
  fixture.returned_count = 2;
  const auto result = xar::ck3_11906::ReadMinorReligiousDefendersV1(
      Environment(fixture), {.application_main_paused = true}, kActorId,
      kDefenderId);
  assert(result.failure ==
         xar::ck3_11906::MinorReligiousDefenderFailureV1::none);
  assert(result.prospective_joiners.size() == 2);
  assert(result.prospective_joiners[0].character_id == kJoinerAId);
  assert(result.prospective_joiners[1].character_id == kJoinerBId);
  assert(result.actor_character_id == kActorId);
  assert(result.primary_defender_character_id == kDefenderId);
  assert(result.actor_base_power_raw == 5'000'000);
  assert(result.primary_defender_base_power_raw == 900'000);
  assert(result.prospective_joiner_base_power_raw == 3'750'000);
  assert(result.primary_plus_joiner_base_power_raw == 4'650'000);
  assert(fixture.frees == 1);
}

void TestRequiresPausedApplicationMain() {
  Fixture fixture{};
  Initialize(fixture);
  g_fixture = &fixture;
  const auto result = xar::ck3_11906::ReadMinorReligiousDefendersV1(
      Environment(fixture), {}, kActorId, kDefenderId);
  assert(result.failure ==
         xar::ck3_11906::MinorReligiousDefenderFailureV1::boundary);
}

void TestRejectsDuplicateIdentityAndStillFrees() {
  Fixture fixture{};
  Initialize(fixture);
  g_fixture = &fixture;
  fixture.returned = {fixture.joiner_a.data(), fixture.joiner_a.data()};
  fixture.returned_count = 2;
  const auto result = xar::ck3_11906::ReadMinorReligiousDefendersV1(
      Environment(fixture), {.application_main_paused = true}, kActorId,
      kDefenderId);
  assert(result.failure ==
         xar::ck3_11906::MinorReligiousDefenderFailureV1::identity);
  assert(result.prospective_joiners.empty());
  assert(fixture.frees == 1);
}

}  // namespace

int main() {
  TestReadsCharacterPointersAndPowers();
  TestRequiresPausedApplicationMain();
  TestRejectsDuplicateIdentityAndStillFrees();
  return 0;
}
