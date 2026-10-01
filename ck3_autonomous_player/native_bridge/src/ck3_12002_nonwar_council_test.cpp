#include "xar_bridge/ck3_12002_nonwar_council.hpp"

#include <array>
#include <cassert>
#include <cstring>
#include <iostream>
#include <vector>

namespace {
using namespace xar::ck3_12002;

template <typename T, typename Blob>
void Put(Blob &blob, std::size_t offset, T value) {
  assert(offset + sizeof(value) <= blob.size());
  std::memcpy(blob.data() + offset, &value, sizeof(value));
}

void *expected_scopes = nullptr;
bool current_scopes_seen = false;
bool maximum_scopes_seen = false;
std::int64_t *Current(void *, std::int64_t *output, void *scopes) {
  current_scopes_seen = scopes == expected_scopes;
  *output = 175'000;
  return output;
}
std::int64_t *Maximum(void *, std::int64_t *output, void *scopes) {
  maximum_scopes_seen = scopes == expected_scopes;
  *output = 500'000;
  return output;
}

struct Fixture {
  static constexpr std::int32_t owner_id = 0x01000001;
  static constexpr std::int32_t incumbent_id = 0x02000003;
  static constexpr std::int32_t task_id = 0x03000002;
  std::array<std::byte, 0x200> owner{}, incumbent{};
  std::array<std::byte, 0x300> extension{};
  std::array<std::byte, 0x100> task{}, type{};
  std::array<std::byte, 0x60> position_type{}, character_storage{}, task_storage{};
  std::array<std::byte, 0x80> character_slots{}, task_slots{};
  std::array<std::byte, 0xB0> game_state{};
  std::array<std::byte, 0x160> game_data{};
  std::array<std::byte, 0x900> province{};
  std::array<void *, 3> provinces{};
  std::array<std::int32_t, 2> ids{task_id, task_id};
  void *character_storage_pointer = character_storage.data();
  void *task_storage_pointer = task_storage.data();
  void *fallback = nullptr;
  void *game_state_pointer = game_state.data();
  std::string position_key = "councillor_steward";
  std::string task_key = "task_develop_county";
  CampaignRootNativeEnvironmentV1 environment{};
  CampaignRootAccessV1 access{};

  Fixture() {
    Put(owner, 0x18, owner_id);
    Put(incumbent, 0x18, incumbent_id);
    // Poison the old extension location: choosing +1B8 would observe no council.
    Put(owner, 0x1B8, static_cast<void *>(nullptr));
    Put(owner, 0x1C0, static_cast<void *>(extension.data()));
    Put(extension, 0x230, static_cast<void *>(ids.data()));
    Put(extension, 0x23C, std::int32_t{0});
    Put(character_storage, 0x20, static_cast<void *>(character_slots.data()));
    Put(character_storage, 0x2C, std::int32_t{8});
    Put(character_slots, 1 * 0x10 + 8, static_cast<void *>(owner.data()));
    Put(character_slots, 3 * 0x10 + 8, static_cast<void *>(incumbent.data()));
    Put(task_storage, 0x20, static_cast<void *>(task_slots.data()));
    Put(task_storage, 0x2C, std::int32_t{8});
    Put(task_slots, 2 * 0x10 + 8, static_cast<void *>(task.data()));
    Put(task, 0x10, task_id);
    Put(task, 0x18, static_cast<void *>(type.data()));
    Put(task, 0x40, incumbent_id);
    Put(task, 0x44, owner_id);
    Put(type, 0x40, static_cast<void *>(position_type.data()));
    Put(game_state, 0xA0, static_cast<void *>(game_data.data()));
    provinces[2] = province.data();
    Put(game_data, 0x140, static_cast<void *>(provinces.data()));
    Put(game_data, 0x14C, std::int32_t{3});
    Put(province, 0x10, std::int32_t{2});
    Put(province, 0x85C, std::uint32_t{0x50726F76U});
    environment.exact_build_admitted = true;
    environment.offline_fixture_function_overrides = true;
    environment.character_storage_slot = &character_storage_pointer;
    environment.character_fallback_slot = &fallback;
    environment.active_council_task_storage_slot = &task_storage_pointer;
    environment.active_council_task_fallback_slot = &fallback;
    environment.council_value_progress_current = Current;
    environment.council_value_progress_maximum = Maximum;
    environment.game_state_slot = &game_state_pointer;
    access.context = this;
    access.read_string = [](void *opaque, const void *address,
                            std::string &output) noexcept {
      auto &fixture = *static_cast<Fixture *>(opaque);
      if (address == fixture.type.data() + 0x18) output = fixture.task_key;
      else if (address == fixture.position_type.data() + 0x18) output = fixture.position_key;
      else return false;
      return true;
    };
  }

  bool Read(xar::game::CampaignRootCouncilV1 &output, bool scope = true) {
    std::string_view failure;
    const auto result = ReadNonwarCouncilProjection12002(
        environment, access, owner.data(), owner_id, scope, output, failure);
    if (!result) assert(failure == "council_unavailable");
    return result;
  }
};

const xar::game::CampaignRootCouncilPositionV1 &Steward(
    const xar::game::CampaignRootCouncilV1 &council) {
  for (const auto &row : council.positions)
    if (row.position_key == "councillor_steward") return row;
  std::abort();
}
} // namespace

int main() {
  Fixture fixture;
  xar::game::CampaignRootCouncilV1 output;
  assert(fixture.Read(output));
  assert(output.status == xar::game::CampaignRootCouncilStatusV1::available);
  assert(output.positions.size() == 5 && !output.auxiliary_vacancies_complete);
  assert(!Steward(output).incumbent_character_id);

  Put(fixture.extension, 0x23C, std::int32_t{1});
  Put(fixture.type, 0x48, std::int32_t{1});
  Put(fixture.type, 0x54, std::int32_t{1});
  Put(fixture.task, 0x39, std::uint8_t{1});
  Put(fixture.task, 0x48, std::uint16_t{8});
  Put(fixture.task, 0x50, std::int32_t{2});
  Put(fixture.task, 0x20, std::int64_t{1'234'567});
  assert(fixture.Read(output));
  assert(Steward(output).incumbent_character_id == Fixture::incumbent_id);
  assert(Steward(output).frozen == true);
  assert(Steward(output).target->province_id == 2);
  assert(Steward(output).progress->current->raw == 1'234'567);
  assert(Steward(output).progress->maximum->raw == 10'000'000);

  Put(fixture.type, 0x48, std::int32_t{2});
  Put(fixture.type, 0x54, std::int32_t{2});
  Put(fixture.task, 0x48, std::uint16_t{4});
  Put(fixture.task, 0x50, Fixture::owner_id);
  expected_scopes = fixture.task.data() + 0x40;
  assert(fixture.Read(output));
  assert(current_scopes_seen && maximum_scopes_seen);
  assert(Steward(output).target->character_id == Fixture::owner_id);
  assert(Steward(output).progress->current->raw == 175'000);
  assert(Steward(output).progress->maximum->raw == 500'000);

  Put(fixture.task, 0x10, std::int32_t{0x04000002});
  assert(!fixture.Read(output)); // Same slot index, wrong generation.
  Put(fixture.task, 0x10, Fixture::task_id);
  Put(fixture.extension, 0x23C, std::int32_t{2});
  assert(!fixture.Read(output)); // Same position cannot be published twice.
  Put(fixture.extension, 0x23C, std::int32_t{1});
  Put(fixture.task, 0x44, Fixture::incumbent_id);
  assert(!fixture.Read(output)); // Stored task belongs to another council.
  assert(fixture.Read(output, false));
  assert(output.status == xar::game::CampaignRootCouncilStatusV1::unavailable);
  assert(output.unavailable_reason == "outside_standard_landed_non_nomadic_core_scope");
  std::cout << "PASS council 12002: empty, county percentage, court value, shifted ABI, identity, scope\n";
}
