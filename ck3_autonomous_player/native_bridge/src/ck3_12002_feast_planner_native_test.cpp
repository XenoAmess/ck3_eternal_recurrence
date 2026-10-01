#include "xar_bridge/ck3_12002_feast_planner_native.hpp"
#include "xar_bridge/ck3_12002_province.hpp"

#include <windows.h>

#include <array>
#include <cstring>
#include <iostream>
#include <vector>

namespace {

struct Region { std::uintptr_t address; std::size_t size; };
struct Fixture {
  xar::game::Snapshot snapshot{};
  std::array<std::byte, 0xA8> game_state{};
  std::array<std::byte, 0x150> game_data{};
  std::array<std::byte, 0x864> province{};
  std::array<std::uintptr_t, 4> provinces{};
  std::vector<Region> regions{};
  std::uint32_t snapshot_reads = 0;
};

template <class T, std::size_t N>
void Put(std::array<std::byte, N> &object, std::size_t offset, T value) {
  std::memcpy(object.data() + offset, &value, sizeof(value));
}

bool ReadMemory(void *opaque, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  const auto &fixture = *static_cast<Fixture *>(opaque);
  for (const auto &region : fixture.regions) {
    if (address >= region.address && size <= region.size &&
        address - region.address <= region.size - size) {
      std::memcpy(output, reinterpret_cast<const void *>(address), size);
      return true;
    }
  }
  return false;
}

bool ReadSnapshot(void *opaque, xar::game::Snapshot &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.snapshot_reads;
  output = fixture.snapshot;
  return true;
}

bool ResolveKey(void *, std::int32_t id, std::string_view &output) noexcept {
  if (id != 77) return false;
  output = "feast_type_generic";
  return true;
}

bool Require(bool condition, const char *description) {
  if (!condition) std::cerr << description << '\n';
  return condition;
}

} // namespace

int main() {
  using namespace xar;
  Fixture fixture{};
  fixture.snapshot.date_raw = 53220000;
  fixture.snapshot.played_character_id = 38822;
  fixture.snapshot.has_played_character = true;
  fixture.snapshot.played_character_alive = true;
  fixture.snapshot.map_ready = true;
  fixture.snapshot.paused = true;
  fixture.snapshot.played_character_gold.raw = 71250000;
  Put(fixture.game_state, 0xA0, reinterpret_cast<std::uintptr_t>(fixture.game_data.data()));
  Put(fixture.game_data, ck3_12002::kObjectiveProvinceArrayOffset,
      reinterpret_cast<std::uintptr_t>(fixture.provinces.data()));
  Put(fixture.game_data, ck3_12002::kObjectiveProvinceCountOffset, std::int32_t{4});
  Put(fixture.province, 0x10, std::int32_t{3});
  Put(fixture.province, ck3_12002::kObjectiveProvinceMagicOffset, std::uint32_t{0x50726F76});
  fixture.provinces[3] = reinterpret_cast<std::uintptr_t>(fixture.province.data());
  fixture.regions = {
      {reinterpret_cast<std::uintptr_t>(fixture.game_state.data()), fixture.game_state.size()},
      {reinterpret_cast<std::uintptr_t>(fixture.game_data.data()), fixture.game_data.size()},
      {reinterpret_cast<std::uintptr_t>(fixture.province.data()), fixture.province.size()},
      {reinterpret_cast<std::uintptr_t>(fixture.provinces.data()), sizeof(fixture.provinces)}};
  ck3_12002::ActivityPlanner12002NativeV1 native{};
  if (!Require(ck3_12002::BindActivityPlanner12002V1(
          native, 0x10000000, bridge::kActivityPlanner12002ExeSha256V1, &fixture,
          &ReadSnapshot, &ReadMemory, &ResolveKey, 17, GetCurrentThreadId(),
          reinterpret_cast<std::uintptr_t>(fixture.game_state.data())), "exact new binder rejected"))
    return 1;
  const auto diagnostic = ck3_12002::BuildActivityPlanner12002DiagEnvironmentV1(native);
  bridge::ActivityPlannerDiagFrameV1 frame{};
  if (!Require(diagnostic.read_frame(diagnostic.context, frame) &&
          frame.revision == 17 && frame.date_raw == fixture.snapshot.date_raw &&
          frame.actor_character_id == 38822 && frame.application_main_thread &&
          frame.paused && frame.map_ready && frame.actor_alive && fixture.snapshot_reads == 1,
          "full exact adapter snapshot was not consumed"))
    return 1;
  const auto option = ck3_12002::BuildActivityPlanner12002OptionEnvironmentV1(native);
  std::array<char, 96> key{};
  std::uint16_t key_size = 0;
  if (!Require(option.resolve_key(option.diagnostic.context, 77, key, key_size) &&
          std::string_view(key.data(), key_size) == "feast_type_generic",
          "exact script identifier callback was not consumed"))
    return 1;
  const auto destination = ck3_12002::BuildActivityPlanner12002DestinationEnvironmentV1(native);
  std::uintptr_t province = 0;
  if (!Require(destination.resolve_province(destination.diagnostic.context, 3, province) &&
          province == fixture.provinces[3], "current ProvinceDB source did not resolve typed ID"))
    return 1;
  if (!Require(!destination.resolve_province(destination.diagnostic.context, 1, province) &&
          province == 0 &&
          !destination.resolve_province(destination.diagnostic.context, 4, province) && province == 0,
          "absent and out of range ProvinceIDs did not remain unavailable"))
    return 1;
  Put(fixture.province, 0x10, std::int32_t{2});
  if (!Require(!destination.resolve_province(destination.diagnostic.context, 3, province) &&
          province == 0, "different native ProvinceID was accepted"))
    return 1;
  std::cout << "PASS: exact 1.20 planner callback snapshot, script key and ProvinceDB source; no native RVA invoked\n";
  return 0;
}
