#include "xar_bridge/ck3_12002_nonwar_council.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"

#include <windows.h>

#include <array>
#include <cassert>
#include <cstring>
#include <iostream>
#include <fstream>
#include <string_view>
#include <utility>
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

// One focused synthetic engine case. IDs reuse the observed Robert task binding;
// the signed modifier amount is deliberately synthetic, not an actual sample.
constexpr std::int32_t kReligiousOwner = 29829;
constexpr std::int32_t kReligiousIncumbent = 56513;
constexpr std::int32_t kReligiousTask = 7162;
constexpr std::int64_t kSyntheticOwnerPiety = -225'000;
void *expected_type = nullptr;
const void *religious_scopes = nullptr;
std::array<std::byte, 32> expected_scope_bytes{};
void *evaluated_storage = nullptr;
std::vector<int> engine_calls;

void *__fastcall OwnerModifierBuilder(const void *type, void *output,
                                     const void *scopes) {
  assert(type == expected_type && scopes == religious_scopes);
  assert(std::memcmp(scopes, expected_scope_bytes.data(), 32) == 0);
  assert(reinterpret_cast<std::uintptr_t>(output) % 8 == 0);
  evaluated_storage = output;
  static_cast<std::byte *>(output)[0x1B8] = std::byte{0x5A};
  engine_calls.push_back(1);
  return output;
}

std::int64_t *__fastcall ModifierValue(const void *modifier, std::int64_t *output,
                                     std::uint16_t id) {
  assert(modifier == evaluated_storage && id == 0x61);
  assert(static_cast<const std::byte *>(modifier)[0x1B8] == std::byte{0x5A});
  engine_calls.push_back(2);
  *output = kSyntheticOwnerPiety;
  return output;
}

void __fastcall DestroyModifier(void *modifier) {
  assert(modifier == evaluated_storage);
  assert(static_cast<std::byte *>(modifier)[0x1B8] == std::byte{0x5A});
  static_cast<std::byte *>(modifier)[0x1B8] = std::byte{0};
  engine_calls.push_back(3);
}

struct EngineStubModule {
  std::byte *base = static_cast<std::byte *>(VirtualAlloc(
      nullptr, 0x31AC000, MEM_RESERVE, PAGE_NOACCESS));
  ~EngineStubModule() { if (base != nullptr) VirtualFree(base, 0, MEM_RELEASE); }
  bool Install(std::uintptr_t rva, std::uintptr_t target) {
    if (base == nullptr || VirtualAlloc(base + (rva & ~std::uintptr_t{0xFFF}),
        0x1000, MEM_COMMIT, PAGE_EXECUTE_READWRITE) == nullptr) return false;
    // Three exact RVA entries jump to synthetic ABI stubs, preserving all args.
    const std::array<std::byte, 12> jump{
        std::byte{0x48}, std::byte{0xB8}, {}, {}, {}, {}, {}, {}, {}, {},
        std::byte{0xFF}, std::byte{0xE0}};
    std::memcpy(base + rva, jump.data(), jump.size());
    std::memcpy(base + rva + 2, &target, sizeof(target));
    return FlushInstructionCache(GetCurrentProcess(), base + rva, jump.size()) != 0;
  }
};

bool TaskOwnerMonthlyPietyOnly(const char *wire_path) {
  EngineStubModule module;
  if (!module.Install(0x31ABE10, reinterpret_cast<std::uintptr_t>(&OwnerModifierBuilder)) ||
      !module.Install(0x2303700, reinterpret_cast<std::uintptr_t>(&ModifierValue)) ||
      !module.Install(0x9F24F0, reinterpret_cast<std::uintptr_t>(&DestroyModifier))) return false;
  Fixture fixture;
  fixture.position_key = "councillor_court_chaplain";
  fixture.task_key = "task_religious_relations";
  std::vector<std::byte> characters((static_cast<std::size_t>(kReligiousIncumbent) + 1) * 0x10);
  std::vector<std::byte> tasks((static_cast<std::size_t>(kReligiousTask) + 1) * 0x10);
  Put(fixture.owner, 0x18, kReligiousOwner);
  Put(fixture.incumbent, 0x18, kReligiousIncumbent);
  Put(fixture.task, 0x10, kReligiousTask);
  Put(fixture.task, 0x40, kReligiousIncumbent);
  Put(fixture.task, 0x44, kReligiousOwner);
  Put(fixture.task, 0x50, std::uint64_t{0x1122334455667788});
  Put(fixture.task, 0x58, std::uint64_t{0x8877665544332211});
  Put(characters, static_cast<std::size_t>(kReligiousOwner) * 0x10 + 8,
      static_cast<void *>(fixture.owner.data()));
  Put(characters, static_cast<std::size_t>(kReligiousIncumbent) * 0x10 + 8,
      static_cast<void *>(fixture.incumbent.data()));
  Put(fixture.character_storage, 0x20, static_cast<void *>(characters.data()));
  Put(fixture.character_storage, 0x2C, kReligiousIncumbent + 1);
  Put(tasks, static_cast<std::size_t>(kReligiousTask) * 0x10 + 8,
      static_cast<void *>(fixture.task.data()));
  Put(fixture.task_storage, 0x20, static_cast<void *>(tasks.data()));
  Put(fixture.task_storage, 0x2C, kReligiousTask + 1);
  fixture.ids[0] = kReligiousTask;
  Put(fixture.extension, 0x23C, std::int32_t{1});
  expected_type = fixture.type.data();
  religious_scopes = fixture.task.data() + 0x40;
  std::memcpy(expected_scope_bytes.data(), religious_scopes, 32);
  const auto module_base = reinterpret_cast<std::uintptr_t>(module.base);
  auto bound = fixture.environment;
  BindNonwarCouncil12002(bound, module_base);
  fixture.environment.module_base = module_base;
  fixture.environment.task_owner_monthly_piety = bound.task_owner_monthly_piety;
  xar::game::CampaignRootCouncilV1 council;
  std::string_view failure;
  if (!ReadNonwarCouncilProjection12002(fixture.environment, fixture.access,
      fixture.owner.data(), kReligiousOwner, true, council, failure)) return false;
  const xar::game::CampaignRootCouncilPositionV1 *chaplain = nullptr;
  for (const auto &row : council.positions)
    if (row.position_key == "councillor_court_chaplain") chaplain = &row;
  if (chaplain == nullptr || chaplain->incumbent_character_id != kReligiousIncumbent ||
      chaplain->task_key != "task_religious_relations" || chaplain->target.has_value() ||
      chaplain->frozen != false || !chaplain->progress ||
      chaplain->progress->kind != xar::game::CampaignRootCouncilProgressKindV1::infinite ||
      chaplain->task_owner_monthly_piety_v1 !=
          xar::game::FixedPointValue{kSyntheticOwnerPiety, 100'000} ||
      engine_calls != std::vector<int>{1, 2, 3}) return false;
  // Root fields below are fixture DTO context; this case covers the real Position
  // producer and serializer, not a full-root producer or actual paused sample.
  xar::game::CampaignRootContextV1 root;
  root.status = xar::game::CampaignRootContextStatusV1::available;
  root.snapshot_revision = 41;
  root.date_raw = 12'345;
  root.local_player_id = 7;
  root.player_character_id = kReligiousOwner;
  root.player_character_alive = true;
  root.player_monthly_gold_income = xar::game::FixedPointValue{570'772, 100'000};
  root.player_monthly_piety_v1 = xar::game::FixedPointValue{88'888, 100'000};
  root.player_health = xar::game::FixedPointValue{500'000, 100'000};
  root.player_legitimacy_v1 = xar::game::CampaignRootLegitimacyV1{
      xar::game::FixedPointValue{10'000'000, 100'000}, {}};
  root.player_domain_size = 1;
  root.player_domain_limit = 5;
  root.player_targeting_faction_count = 0;
  // Match the available council's admitted landed, non-nomadic fixture scope.
  root.primary_title = xar::game::CampaignRootTitleV1{1001, 2, "county"};
  root.capital_province_id = 2;
  root.held_title_partition = {{*root.primary_title, std::nullopt, 2, true}};
  root.government = xar::game::CampaignRootGovernmentV1{"feudal_government", {}, 0};
  root.top_liege_character_id = kReligiousOwner;
  root.independent = true;
  root.council = std::move(council);
  root.readiness = {true, true, true, true, true, true, true, true, true,
                    true, true, true, true, true, true, true, true, true};
  const xar::game::AdapterDescriptor descriptor{
      "ck3-1.20.0.3-msvc-x64", "1.20.0.3",
      xar::ck3_12003::kExecutableSha256, "fixture-only", {}};
  const auto wire = xar::game::RenderCrozierBuildIdentity(
      SerializeCampaignRootContextV1(root), descriptor);
  if (wire.empty() || wire.find("\"raw\":-225000,\"scale\":100000") == std::string::npos ||
      wire.find("1.20.0.3") == std::string::npos) return false;
  std::ofstream destination(wire_path, std::ios::binary);
  destination << wire << '\n';
  std::cout << "task-owner-monthly-piety-only production Position/three ABI calls/wire passed\n";
  return destination.good();
}

} // namespace

int main(int argc, char **argv) {
  if (argc == 3 && std::string_view(argv[1]) == "--task-owner-monthly-piety-only")
    return TaskOwnerMonthlyPietyOnly(argv[2]) ? 0 : 1;
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
