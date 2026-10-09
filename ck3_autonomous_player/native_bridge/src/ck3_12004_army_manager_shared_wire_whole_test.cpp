#include "xar_bridge/army_strengths_manager_shared_wire_v1.hpp"
#include "xar_bridge/ck3_12002_army.hpp"

#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <initializer_list>
#include <iostream>
#include <memory>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {
using namespace xar;

void Check(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}

struct Memory {
  struct Region { std::unique_ptr<std::byte[]> bytes; std::size_t size; };
  struct Denied { std::uintptr_t begin; std::size_t size; };
  std::vector<Region> regions;
  std::vector<Denied> denied;
  std::size_t denied_attempts = 0;

  void *Allocate(std::size_t size) {
    auto bytes = std::make_unique<std::byte[]>(size);
    void *object = bytes.get();
    regions.push_back({std::move(bytes), size});
    return object;
  }
  template <class T> void Put(void *object, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
  }
  void Deny(const void *object, std::size_t offset, std::size_t size) {
    denied.push_back({reinterpret_cast<std::uintptr_t>(object) + offset, size});
  }
  std::vector<std::vector<std::byte>> Snapshot() const {
    std::vector<std::vector<std::byte>> result;
    for (const auto &region : regions)
      result.emplace_back(region.bytes.get(), region.bytes.get() + region.size);
    return result;
  }
  static bool Read(void *context, const void *address, void *output,
                   std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
    for (const auto &range : memory.denied) {
      if (begin < range.begin + range.size && range.begin < begin + size) {
        ++memory.denied_attempts;
        return false;
      }
    }
    for (const auto &region : memory.regions) {
      const auto base = reinterpret_cast<std::uintptr_t>(region.bytes.get());
      if (begin >= base && begin - base <= region.size &&
          size <= region.size - (begin - base)) {
        std::memcpy(output, address, size);
        return true;
      }
    }
    return false;
  }
};

struct Registry {
  Memory &memory;
  void *slot, *fallback_slot, *store, *table;
  explicit Registry(Memory &value)
      : memory(value), slot(value.Allocate(8)), fallback_slot(value.Allocate(8)),
        store(value.Allocate(0x30)), table(value.Allocate(16 * 16)) {
    memory.Put(slot, 0, store);
    memory.Put(store, 0x20, table);
    memory.Put(store, 0x2C, std::uint32_t{16});
  }
  void Add(std::uint32_t full_id, void *object,
           std::size_t full_id_offset = 0x10) {
    memory.Put(table, static_cast<std::size_t>(full_id & 0xFFFFFFU) * 16 + 8, object);
    memory.Put(object, full_id_offset, full_id);
  }
};

// Typed strength IDs are non-negative int32 handles. Keep their generation
// bits and independent public CUnit identities without setting the sign bit.
constexpr std::uint32_t kArmyA = 0x2B000001U, kArmyB = 0x67000002U;
constexpr std::uint32_t kCharacterA = 0xFE000003U, kCharacterB = 0x88000004U;
constexpr std::uint32_t kCombat = 0xD1000005U;
constexpr std::uint32_t kArRgA = 0x39000006U, kArRgB = 0x40000007U;
constexpr std::int32_t kUnitA = 0x6B00000B, kUnitB = 0x7700000C;
constexpr std::array<std::uint32_t, 5> kOriginalRoster{
    kArmyA, kArmyB, kArmyA, kArmyB, kArmyA};

struct Fixture;
Fixture *active = nullptr;
std::int32_t Current(void *, std::uint8_t);
std::int32_t Maximum(void *);

struct Capture {
  game::ReadArmyStrengthsResult status = game::ReadArmyStrengthsResult::unavailable;
  std::vector<game::ArmyStrengthSnapshot> rows;
};

struct Fixture {
  Memory memory;
  Registry armies{memory}, units{memory}, characters{memory}, combats{memory}, arrgs{memory};
  void *army_a = memory.Allocate(0x210), *army_b = memory.Allocate(0x210);
  void *unit_a = memory.Allocate(0x180), *unit_b = memory.Allocate(0x180);
  void *character_a = memory.Allocate(0x200), *character_b = memory.Allocate(0x200);
  void *arrg_a = memory.Allocate(0x150), *arrg_b = memory.Allocate(0x150);
  void *combat = memory.Allocate(0x720), *province = memory.Allocate(0x880);
  void *province_fallback_slot = memory.Allocate(8);
  void *state_slot = memory.Allocate(8), *state = memory.Allocate(0xA8);
  void *domain = memory.Allocate(0x2E9D0 + 0x190);
  void *army_manager = static_cast<std::byte *>(domain) + 0x2A540;
  void *combat_manager = static_cast<std::byte *>(domain) + 0x2E9D0;
  void *pending_entries = memory.Allocate(5 * 0x28);
  void *pending_allocator = memory.Allocate(8), *empty_pending_buffer = memory.Allocate(0x28);
  void *threshold_slot = memory.Allocate(4);
  ck3_12002::ArmyBindings query{};

  Fixture() {
    armies.Add(kArmyA, army_a); armies.Add(kArmyB, army_b);
    units.Add(static_cast<std::uint32_t>(kUnitA), unit_a);
    units.Add(static_cast<std::uint32_t>(kUnitB), unit_b);
    characters.Add(kCharacterA, character_a, 0x18);
    characters.Add(kCharacterB, character_b, 0x18);
    combats.Add(kCombat, combat, 8);
    arrgs.Add(kArRgA, arrg_a); arrgs.Add(kArRgB, arrg_b);
    memory.Put(armies.fallback_slot, 0, army_a);
    memory.Put(units.fallback_slot, 0, unit_a);
    memory.Put(characters.fallback_slot, 0, character_a);
    memory.Put(combats.fallback_slot, 0, combat);
    memory.Put(arrgs.fallback_slot, 0, arrg_a);
    memory.Put(province_fallback_slot, 0, province);
    ConfigureArmy(army_a, unit_a, kArmyA, kUnitA, kCharacterA, kArRgA);
    ConfigureArmy(army_b, unit_b, kArmyB, kUnitB, kCharacterB, kArRgB);
    ConfigureRegiment(arrg_a, 20, 40, 4000000);
    ConfigureRegiment(arrg_b, 30, 60, 6000000);
    memory.Put(state_slot, 0, state); memory.Put(state, 0xA0, domain);
    Ids(static_cast<std::byte *>(army_manager) + 0x50,
        {kArmyA, kArmyB, kArmyA, kArmyB, kArmyA});
    Ids(static_cast<std::byte *>(army_manager) + 0x68, {kArmyB, kArmyB});
    // Complete physical pending image, including an unrelated full ID and
    // repeated full ArRg references; no filtering by the requested Army.
    memory.Put(army_manager, 0x138, pending_entries);
    memory.Put(army_manager, 0x140, std::int32_t{2});
    memory.Put(army_manager, 0x144, std::int32_t{3});
    memory.Put(army_manager, 0x148, std::uint8_t{0});
    memory.Put(army_manager, 0x14C, std::uint32_t{0x3F400000U});
    PendingRecord(0, kArmyA, {kArRgB, kArRgA, kArRgB});
    PendingRecord(2, 0xF1000008U, {kArRgA, kArRgA});
    memory.Put(pending_entries, 4 * 0x28 + 4, std::uint8_t{0xFF});
    memory.Put(combat, 0xC, std::uint32_t{0x436F6D62U});
    memory.Put(combat, 0x6B0, std::int32_t{1});
    memory.Put(combat, 0x6B4, std::int32_t{4});
    memory.Put(combat, 0x700, std::int32_t{-1});
    memory.Put(combat_manager, 8, reinterpret_cast<const void *>(std::uintptr_t{0x14477F178ULL}));
    CombatIds(combat_manager, 0x28, 0x30, 0x34, {kCombat, kCombat}, 4);
    Side(0x20, {kArmyA, kArmyA}, kCharacterA);
    Side(0x368, {kArmyB}, kCharacterB);
    memory.Put(threshold_slot, 0, std::int32_t{3});

    query.enabled = true;
    query.game_state_slot = static_cast<void **>(state_slot);
    query.unit_storage_slot = static_cast<void **>(units.slot);
    query.internal_army_storage_slot = static_cast<void **>(armies.slot);
    query.regiment_storage_slot = static_cast<void **>(arrgs.slot);
    query.get_army_current_soldiers = Current;
    query.get_army_maximum_soldiers = Maximum;
    auto &common = query.current_daily_assault_roster_admission_bindings;
    common.enabled = true; common.game_state_slot = state_slot;
    common.army_registry_slot = armies.slot; common.army_fallback_slot = armies.fallback_slot;
    common.unit_registry_slot = units.slot; common.unit_fallback_slot = units.fallback_slot;
    common.character_registry_slot = characters.slot; common.character_fallback_slot = characters.fallback_slot;
    common.province_fallback_slot = province_fallback_slot;
    common.read_memory = Memory::Read; common.read_context = &memory;
    auto &pending = query.current_pre_date_pending_update_bindings;
    pending.common = common;
    pending.combat_registry_slot = combats.slot; pending.combat_fallback_slot = combats.fallback_slot;
    pending.arrg_registry_slot = arrgs.slot; pending.arrg_fallback_slot = arrgs.fallback_slot;
    pending.native_empty_pending_buffer = empty_pending_buffer;
    pending.expected_pending_vector_allocator = pending_allocator;
    auto &refresh = query.current_post_admission_refresh_bindings;
    refresh.common = common;
    refresh.arrg_registry_slot = arrgs.slot; refresh.arrg_fallback_slot = arrgs.fallback_slot;
    query.current_selected_title_holder_owner_relation_bindings.common = common;
    auto &flag31 = query.current_army_flag31_bindings;
    flag31.common = common;
    flag31.combat_registry_slot = combats.slot; flag31.combat_fallback_slot = combats.fallback_slot;
    auto &roles = query.current_army_combat_roles_phase_bindings;
    roles.common = common;
    roles.combat_registry_slot = combats.slot; roles.combat_fallback_slot = combats.fallback_slot;
    roles.expected_secondary_vtable = reinterpret_cast<const void *>(std::uintptr_t{0x14477F178ULL});
    roles.maneuver_threshold_slot = threshold_slot;
  }

  void Ids(void *header, std::initializer_list<std::uint32_t> ids) {
    memory.Put(header, 8, static_cast<std::int32_t>(ids.size()));
    memory.Put(header, 0xC, static_cast<std::int32_t>(ids.size()));
    void *data = ids.size() ? memory.Allocate(ids.size() * 4) : nullptr;
    std::size_t index = 0;
    for (auto id : ids) memory.Put(data, index++ * 4, id);
    memory.Put(header, 0, data);
  }
  void CombatIds(void *object, std::size_t data_offset, std::size_t capacity_offset,
                 std::size_t count_offset, std::initializer_list<std::uint32_t> ids,
                 std::uint32_t capacity) {
    void *data = ids.size() ? memory.Allocate(ids.size() * 4) : nullptr;
    std::size_t index = 0;
    for (auto id : ids) memory.Put(data, index++ * 4, id);
    memory.Put(object, data_offset, data);
    memory.Put(object, capacity_offset, capacity);
    memory.Put(object, count_offset, static_cast<std::int32_t>(ids.size()));
  }
  void ConfigureArmy(void *army, void *unit, std::uint32_t army_id,
                     std::int32_t unit_id, std::uint32_t character_id,
                     std::uint32_t arrg_id) {
    memory.Put(army, 0x10, army_id);
    memory.Put(army, 0x124, unit_id); memory.Put(army, 0x128, kCombat);
    memory.Put(army, 0x24, std::int32_t{-777});
    memory.Put(army, 0x28, std::int64_t{-888});
    memory.Put(army, 0x31, std::uint8_t{187});
    memory.Put(army, 0x180, std::int64_t{12345678});
    Ids(static_cast<std::byte *>(army) + 0x38, {arrg_id});
    memory.Put(unit, 0x18, std::uint32_t{1});
    memory.Put(unit, 0x20, province);
    memory.Put(unit, 0x174, character_id); memory.Put(unit, 0x178, army_id);
    // Wrong Province component magic selects a legal zero shared-tail result;
    // the admission gate independently exits on the actual Unit kind1.
    memory.Put(province, 0x85C, std::uint32_t{0});
  }
  void ConfigureRegiment(void *arrg, std::int32_t current, std::int32_t maximum,
                         std::int64_t power) {
    memory.Put(arrg, 0x14, std::uint32_t{0x41725267U});
    memory.Put(arrg, 0x38, current); memory.Put(arrg, 0x3C, maximum);
    memory.Put(arrg, 0x40, power);
  }
  void PendingRecord(std::size_t slot, std::uint32_t key,
                     std::initializer_list<std::uint32_t> refs) {
    auto *record = static_cast<std::byte *>(pending_entries) + slot * 0x28;
    memory.Put(record, 0, ck3_12003::daily_assault_roster_detail::Hash(key));
    memory.Put(record, 4, std::uint8_t{1}); memory.Put(record, 8, key);
    Ids(record + 0x10, refs); memory.Put(record, 0x20, pending_allocator);
  }
  void Side(std::size_t offset, std::initializer_list<std::uint32_t> armies_in_side,
            std::uint32_t owner) {
    auto *side = static_cast<std::byte *>(combat) + offset;
    CombatIds(side, 0x10, 0x18, 0x1C, armies_in_side,
              static_cast<std::uint32_t>(armies_in_side.size()));
    memory.Put(side, 0xB8, combat);
    memory.Put(side, 0x70, owner); memory.Put(side, 0x74, std::uint32_t{0});
  }
  Capture Observe(bool single = false) {
    active = this;
    const auto before = memory.Snapshot();
    const std::array<ck3_12002::ArmyStrengthScope, 2> scope{{
        {kUnitA, game::ArmyStrengthScopeRole::player, {}},
        {kUnitB, game::ArmyStrengthScopeRole::player, {}}}};
    Capture result;
    result.status = ck3_12002::ReadArmyStrengthsForScope(query,
        std::span<const ck3_12002::ArmyStrengthScope>(scope.data(), single ? 1 : 2),
        result.rows);
    Check(result.status == game::ReadArmyStrengthsResult::available &&
              result.rows.size() == (single ? 1U : 2U),
          "shared-wire fixture must use genuine available whole-query rows");
    for (std::size_t index = 0; index < result.rows.size(); ++index) {
      const auto &row = result.rows[index];
      Check(row.available && row.army_id == (index == 0 ? kUnitA : kUnitB) &&
                row.native_carmy_id_observable &&
                row.native_carmy_id == static_cast<std::int32_t>(index == 0 ? kArmyA : kArmyB) &&
                row.native_carmy_id != row.army_id &&
                row.current_soldiers == (index == 0 ? 20 : 30) &&
                row.maximum_soldiers == (index == 0 ? 40 : 60) &&
                row.regiment_count == 1 &&
                row.ai_base_power_raw == (index == 0 ? 4000000 : 6000000),
            "manager optional fields must not change independently read strength");
    }
    Check(before == memory.Snapshot(), "whole-query collector wrote fake world memory");
    active = nullptr;
    return result;
  }
  void DisableManagerFamilies() {
    query.current_daily_assault_roster_admission_bindings = {};
    query.current_pre_date_pending_update_bindings = {};
    query.current_post_admission_refresh_bindings = {};
    query.current_selected_title_holder_owner_relation_bindings = {};
    query.current_army_combat_roles_phase_bindings = {};
    query.current_army_flag31_bindings = {};
  }
};

std::int32_t Current(void *receiver, std::uint8_t flags) {
  Check(active && flags == 0, "whole current getter called outside its synthetic world");
  if (receiver == static_cast<std::byte *>(active->army_a) + 0x38) return 20;
  Check(receiver == static_cast<std::byte *>(active->army_b) + 0x38,
        "whole current getter received a different Army");
  return 30;
}
std::int32_t Maximum(void *receiver) {
  Check(active != nullptr, "whole maximum getter called outside its synthetic world");
  if (receiver == active->army_a) return 40;
  Check(receiver == active->army_b, "whole maximum getter received a different Army");
  return 60;
}

void RequireSixFamilies(const game::ArmyStrengthSnapshot &row) {
  Check(row.current_daily_assault_roster_admission_v1.has_value() &&
            row.current_pre_date_pending_update_inputs_v1.has_value() &&
            row.current_post_admission_refresh_inputs_v1.has_value() &&
            row.current_selected_title_holder_owner_relation_v1.has_value() &&
            row.current_army_combat_roles_phase_inputs_v1.has_value() &&
            row.current_army_flag31_inputs_v1.has_value(),
        "all six manager families must be produced through real collector hooks");
}
void RequireComplete(const Capture &capture) {
  const auto &row = capture.rows.front();
  RequireSixFamilies(row);
  Check(row.current_daily_assault_roster_admission_v1->ready &&
            row.current_pre_date_pending_update_inputs_v1->ready &&
            row.current_post_admission_refresh_inputs_v1->ready &&
            row.current_selected_title_holder_owner_relation_v1->ready &&
            row.current_army_combat_roles_phase_inputs_v1->current_combat_roles_phase_inputs_ready &&
            row.current_army_flag31_inputs_v1->ready,
        "complete synthetic world must produce genuinely complete manager leaves");
  const auto &roster = row.current_daily_assault_roster_admission_v1->original_roster;
  Check(roster.occurrences.size() == kOriginalRoster.size(),
        "full ordered ArmyManager roster was cropped");
  for (std::size_t index = 0; index < kOriginalRoster.size(); ++index)
    Check(roster.occurrences[index].raw_full_id_u32 == kOriginalRoster[index],
          "full generation IDs, repeats or native order changed");
  const auto &pending = row.current_pre_date_pending_update_inputs_v1->pending_table_frame_v1;
  Check(pending && pending->ready && pending->records.size() == 5 &&
            pending->records[2].key_raw_full_id_u32 == std::uint32_t{0xF1000008U} &&
            pending->records[0].references.occurrences.size() == 3,
        "complete global pending image or unrelated/repeated references were lost");
}

struct Number {
  template <class T> std::string operator()(T value) const { return std::to_string(value); }
};
struct Int32Array {
  void operator()(std::string &out, const std::vector<std::int32_t> &values) const {
    out += '[';
    for (std::size_t index = 0; index < values.size(); ++index) {
      if (index) out += ',';
      out += std::to_string(values[index]);
    }
    out += ']';
  }
};
struct JsonString {
  void operator()(std::string &out, std::string_view value) const {
    constexpr char hex[] = "0123456789abcdef";
    out += '"';
    for (const char raw : value) {
      const auto byte = static_cast<unsigned char>(raw);
      if (byte == '"' || byte == '\\') { out += '\\'; out += raw; }
      else if (byte < 0x20) {
        out += "\\u00"; out += hex[byte >> 4]; out += hex[byte & 15];
      } else out += raw;
    }
    out += '"';
  }
};

std::string Serialize(const Capture &capture, std::string_view name,
                      std::uint64_t sequence, bool shared) {
  std::string result = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  JsonString{}(result, std::string("fixture-") + std::string(name));
  result += ",\"ok\":true,\"result\":{\"step\":\"query-army-strengths-v1\","
            "\"accepted\":true,\"status\":\"";
  result += capture.status == game::ReadArmyStrengthsResult::available ? "available" : "partial";
  result += "\",\"query_sequence\":" + std::to_string(sequence);
  if (shared) {
    game::AppendArmyStrengthsQueryMembersV1(result,
        std::span<const game::ArmyStrengthSnapshot>(capture.rows), Number{}, Int32Array{}, JsonString{},
        [](std::string &out, const game::ArmyStrengthSnapshot &row,
           game::ArmyStrengthManagerInputsModeV1 mode) {
          game::AppendArmyStrengthV1WithManagerInputsMode(
              out, row, Number{}, Int32Array{}, JsonString{}, mode);
        });
  } else {
    result += ",\"army_strengths\":[";
    for (std::size_t index = 0; index < capture.rows.size(); ++index) {
      if (index) result += ',';
      game::AppendArmyStrengthV1(result, capture.rows[index], Number{}, Int32Array{}, JsonString{});
    }
    result += ']';
  }
  result += "}}";
  return result;
}

void Write(const std::filesystem::path &path, const std::string &wire) {
  std::ofstream output(path, std::ios::binary);
  output << wire << '\n';
  Check(static_cast<bool>(output), "shared-wire fixture packet write failed");
}

struct Scene {
  std::string name;
  Capture capture;
  bool expect_shared = false;
};
void Emit(const std::filesystem::path &directory, const Scene &scene,
          std::uint64_t sequence, std::string &metadata, bool first) {
  const auto rows = std::span<const game::ArmyStrengthSnapshot>(scene.capture.rows);
  Check(game::HaveSharedArmyManagerInputsV1(rows) == scene.expect_shared,
        "lossless bundle selection disagrees with complete typed family equality");
  const auto legacy = Serialize(scene.capture, scene.name, sequence, false);
  const auto shared = Serialize(scene.capture, scene.name, sequence, true);
  Check((shared.find("\"army_manager_inputs_shared_v1\"") != std::string::npos) == scene.expect_shared,
        "query packet did not use the requested complete-bundle representation");
  if (scene.expect_shared)
    Check(shared.size() < legacy.size(), "complete shared bundle failed to remove duplicated bytes");
  else
    Check(shared == legacy, "inline fallback changed the exact original full packet");
  Write(directory / (scene.name + "-legacy.json"), legacy);
  Write(directory / (scene.name + "-shared.json"), shared);
  if (!first) metadata += ',';
  metadata += "{\"case\":"; JsonString{}(metadata, scene.name);
  metadata += ",\"query_sequence\":" + std::to_string(sequence);
  metadata += ",\"expected_shared\":";
  metadata += scene.expect_shared ? "true" : "false";
  metadata += ",\"army_ids\":[";
  for (std::size_t index = 0; index < scene.capture.rows.size(); ++index) {
    if (index) metadata += ',';
    metadata += std::to_string(scene.capture.rows[index].army_id);
  }
  metadata += "],\"scope_role\":\"player\",\"war_ids\":[],\"legacy_bytes\":" +
      std::to_string(legacy.size()) + ",\"shared_bytes\":" + std::to_string(shared.size()) + '}';
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "usage: shared-wire-whole-test FRESH_OUTPUT_DIRECTORY");
    const std::filesystem::path directory(argv[1]);
    Check(!std::filesystem::exists(directory), "fixture requires a fresh output directory");
    Check(std::filesystem::create_directories(directory), "fixture output directory creation failed");
    std::vector<Scene> scenes;
    {
      Fixture world;
      auto capture = world.Observe(); RequireComplete(capture);
      scenes.push_back({"available-equal", std::move(capture), true});
    }
    {
      Fixture world; world.memory.Deny(world.combat, 0x6B0, 4);
      auto capture = world.Observe();
      RequireSixFamilies(capture.rows.front());
      Check(!capture.rows.front().current_army_combat_roles_phase_inputs_v1->current_combat_roles_phase_inputs_ready &&
                world.memory.denied_attempts == kOriginalRoster.size(),
            "partial equal scene must preserve missing demanded phase as partial");
      scenes.push_back({"partial-equal", std::move(capture), true});
    }
    {
      Fixture world; world.memory.Put(world.state_slot, 0, static_cast<void *>(nullptr));
      auto capture = world.Observe(); RequireSixFamilies(capture.rows.front());
      Check(!capture.rows.front().current_daily_assault_roster_admission_v1->manager_loaded &&
                !capture.rows.front().current_daily_assault_roster_admission_v1->ready,
            "unavailable same-query family must remain present and unavailable");
      scenes.push_back({"unavailable-equal", std::move(capture), true});
    }
    {
      Fixture world;
      auto capture = world.Observe(true); RequireComplete(capture);
      scenes.push_back({"single-fallback", std::move(capture), false});
    }
    {
      Fixture world; world.DisableManagerFamilies();
      auto capture = world.Observe();
      Check(!capture.rows.front().current_daily_assault_roster_admission_v1 &&
                !capture.rows.front().current_army_combat_roles_phase_inputs_v1,
            "absent manager fixture must use actual disabled collector bindings");
      scenes.push_back({"absent-fallback", std::move(capture), false});
    }
    {
      // Both rows are genuine independently collected values. Combining two
      // captures deliberately exercises serializer fallback without editing or
      // fabricating any manager leaf from a real query.
      Fixture world;
      const auto first = world.Observe(); RequireComplete(first);
      world.memory.Put(world.army_a, 0x31, std::uint8_t{23});
      const auto second = world.Observe(); RequireComplete(second);
      Capture capture; capture.status = game::ReadArmyStrengthsResult::available;
      capture.rows = {first.rows[0], second.rows[1]};
      scenes.push_back({"unequal-fallback", std::move(capture), false});
    }
    {
      Fixture world;
      const auto first = world.Observe(); RequireComplete(first);
      world.DisableManagerFamilies();
      const auto second = world.Observe();
      Capture capture; capture.status = game::ReadArmyStrengthsResult::available;
      capture.rows = {first.rows[0], second.rows[1]};
      scenes.push_back({"presence-fallback", std::move(capture), false});
    }
    std::string metadata =
        "{\"schema_version\":1,\"producer\":\"ReadArmyStrengthsForScope\","
        "\"native_callback_world\":\"synthetic\",\"game_execution\":false,"
        "\"manual_field_or_leaf_construction\":false,"
        "\"fallback_mismatch_source\":\"two_independent_whole_collector_captures\","
        "\"original_roster_raw_full_ids_u32\":[";
    for (std::size_t index = 0; index < kOriginalRoster.size(); ++index) {
      if (index) metadata += ',';
      metadata += std::to_string(kOriginalRoster[index]);
    }
    metadata += "],\"cases\":[";
    for (std::size_t index = 0; index < scenes.size(); ++index)
      Emit(directory, scenes[index], 100 + index, metadata, index == 0);
    metadata += "]}";
    Write(directory / "fixture-metadata.json", metadata);
    std::cout << "SOURCE_FIXTURE_PASS: seven genuine whole collector scenes; "
                 "complete shared manager inputs, original order, partial/unavailable and exact inline fallback; "
                 "synthetic world/getter callbacks, no game execution\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
