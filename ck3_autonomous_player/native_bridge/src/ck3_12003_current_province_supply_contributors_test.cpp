#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {
using namespace xar;
using namespace xar::ck3_12002;
template<class T, class Bytes> void Put(Bytes &bytes, std::size_t offset, T value) {
  std::memcpy(bytes.data() + offset, &value, sizeof value);
}
template<class T> T Get(const void *object, std::size_t offset) {
  T result{}; std::memcpy(&result, static_cast<const std::byte *>(object) + offset, sizeof result);
  return result;
}
void Check(bool value, const char *message) { if (!value) throw std::runtime_error(message); }
constexpr std::int32_t subject_unit_id = 0x01000001, same_unit_id = 0x01000002;
constexpr std::int32_t common_unit_id = 0x01000003, excluded_unit_id = 0x01000004;
constexpr std::int32_t subject_army_id = 0x02000001, same_army_id = 0x02000002;
constexpr std::int32_t common_army_id = 0x02000003, excluded_army_id = 0x02000004;
constexpr std::int32_t actor_id = 0x03000001, common_owner_id = 0x03000002, excluded_owner_id = 0x03000003;
constexpr std::int32_t same_regiment_id = 0x04000002, common_regiment_id = 0x04000003;
constexpr std::int32_t ineligible_regiment_id = 0x04000004;
constexpr std::int32_t same_persistent_id = 0x05000002, common_persistent_id = 0x05000003;
void *raised_storage = nullptr;
void *common_owner = nullptr;
std::int32_t current_usage = 338;
bool Eligible(void *regiment) { return Get<std::int32_t>(regiment, 0x10) != ineligible_regiment_id; }
bool CommonSide(void *, void *other, void *breakdown) {
  Check(breakdown == nullptr, "native common-side optional output is null"); return other == common_owner;
}
std::int32_t Count(void *descriptor, std::uint8_t flags) {
  const auto ids = Get<const std::int32_t *>(descriptor, 0);
  const auto count = Get<std::int32_t>(descriptor, 0x0C);
  const auto slots = Get<void *>(raised_storage, 0x20);
  std::uint32_t sum = 0;
  for (std::int32_t index = 0; index < count; ++index) {
    const auto slot = static_cast<std::uint32_t>(ids[index]) & 0xFFFFFFU;
    auto *regiment = Get<void *>(slots, static_cast<std::size_t>(slot) * 0x10 + 8);
    if (flags == 2 && !Eligible(regiment)) continue;
    sum += static_cast<std::uint32_t>(Get<std::int32_t>(regiment, 0x38));
  }
  std::int32_t result{}; std::memcpy(&result, &sum, sizeof result); return result;
}
std::int32_t Maximum(void *) { return 0; }
std::int32_t Limit(void *, void *, void *, void *breakdown) {
  Check(breakdown == nullptr, "native limit optional output is null"); return 500;
}
std::int32_t Usage(void *, void *, std::int32_t mode, std::int64_t *breakdown) {
  Check(mode == 0 && breakdown == nullptr, "query uses exact mode0 and null breakdown"); return current_usage;
}
bool CanReplenish(void *, void *) { return true; }
bool ChunkCanReplenish(void *) { return true; }
bool WriterSkipped(void *) { return false; }
std::int64_t *Fraction(void *persistent, std::int64_t *output) {
  *output = Get<std::int64_t>(persistent, 0x148); return output;
}
void Emit(const std::filesystem::path &directory, const char *label, const game::ArmyStrengthSnapshot &row) {
  std::string wire;
  game::AppendArmyStrengthV1(wire, row,
      [](auto value) { return std::to_string(value); },
      [](std::string &out, const std::vector<std::int32_t> &values) {
        out += '[';
        for (std::size_t index = 0; index < values.size(); ++index) {
          if (index != 0) out += ',';
          out += std::to_string(values[index]);
        }
        out += ']';
      },
      [](std::string &out, std::string_view value) { out += '"'; out += value; out += '"'; });
  std::filesystem::create_directories(directory);
  std::ofstream file(directory / (std::string(label) + ".json"), std::ios::binary);
  Check(static_cast<bool>(file), "new contributor production wire output"); file << wire << '\n';
}
void Cases(const std::filesystem::path &directory) {
  std::array<std::byte, 0x180> subject_unit{}, same_unit{}, common_unit{}, excluded_unit{};
  std::array<std::byte, 0x208> subject_army{}, same_army{}, common_army{}, excluded_army{};
  std::array<std::byte, 0x160> same_regiment{}, common_regiment{}, ineligible_regiment{};
  std::array<std::byte, 0x160> same_persistent{}, common_persistent{};
  std::array<std::byte, 0x30> actor{}, common_character{}, excluded_character{};
  std::array<std::byte, 0x860> province{};
  std::array<std::byte, 0x150> game_data{};
  std::array<std::byte, 0xA8> game_state{};
  std::array<void *, 2> province_slots{nullptr, province.data()};
  std::array<std::int32_t, 5> province_occurrences{subject_unit_id, same_unit_id, same_unit_id, common_unit_id, excluded_unit_id};
  std::array<std::int32_t, 2> same_ids{same_regiment_id, ineligible_regiment_id};
  std::array<std::int32_t, 1> common_ids{common_regiment_id};
  std::array<std::array<std::int32_t, 4>, 2> same_data{{{0, 0, same_persistent_id, 0}, {0, 0, same_persistent_id, 0}}};
  std::array<std::array<std::int32_t, 4>, 1> common_data{{{0, 0, common_persistent_id, 0}}};
  std::array<std::byte, 0x30> units{}, armies{}, raised{}, persistent{}, characters{};
  std::array<std::byte, 0x50> unit_slots{}, army_slots{}, raised_slots{}, persistent_slots{}, character_slots{};
  const auto setup_unit = [&](auto &unit, std::int32_t id, std::int32_t army_id, std::int32_t owner_id) {
    Put(unit, 0x10, id); Put(unit, 0x20, static_cast<void *>(province.data()));
    Put(unit, 0x174, owner_id); Put(unit, 0x178, army_id);
  };
  setup_unit(subject_unit, subject_unit_id, subject_army_id, actor_id);
  setup_unit(same_unit, same_unit_id, same_army_id, actor_id);
  setup_unit(common_unit, common_unit_id, common_army_id, common_owner_id);
  setup_unit(excluded_unit, excluded_unit_id, excluded_army_id, excluded_owner_id);
  const auto setup_army = [&](auto &army, std::int32_t id, std::int32_t unit_id) {
    Put(army, 0x10, id); Put(army, 0x14, std::uint32_t{0x41726D79});
    Put(army, 0x120, std::int32_t{-1}); Put(army, 0x124, unit_id);
  };
  setup_army(subject_army, subject_army_id, subject_unit_id);
  setup_army(same_army, same_army_id, same_unit_id);
  setup_army(common_army, common_army_id, common_unit_id);
  setup_army(excluded_army, excluded_army_id, excluded_unit_id);
  Put(same_army, 0x38, static_cast<void *>(same_ids.data())); Put(same_army, 0x40, std::int32_t{2}); Put(same_army, 0x44, std::int32_t{2});
  Put(common_army, 0x38, static_cast<void *>(common_ids.data())); Put(common_army, 0x40, std::int32_t{1}); Put(common_army, 0x44, std::int32_t{1});
  const auto setup_regiment = [&](auto &regiment, std::int32_t id, std::int32_t current, std::int32_t maximum) {
    Put(regiment, 0x10, id); Put(regiment, 0x14, std::uint32_t{0x41725267});
    Put(regiment, 0x38, current); Put(regiment, 0x3C, maximum);
  };
  setup_regiment(same_regiment, same_regiment_id, 160, 200);
  setup_regiment(common_regiment, common_regiment_id, 18, 30);
  setup_regiment(ineligible_regiment, ineligible_regiment_id, 7, 10);
  Put(same_regiment, 0x20, static_cast<void *>(same_data.data())); Put(same_regiment, 0x28, std::int32_t{2}); Put(same_regiment, 0x2C, std::int32_t{2});
  Put(common_regiment, 0x20, static_cast<void *>(common_data.data())); Put(common_regiment, 0x28, std::int32_t{1}); Put(common_regiment, 0x2C, std::int32_t{1});
  const auto setup_persistent = [&](auto &regiment, std::int32_t id, std::int32_t associated, std::int32_t current, std::int32_t maximum) {
    Put(regiment, 0x10, id); Put(regiment, 0x14, std::uint32_t{0x52656769});
    Put(regiment, 0x18, maximum); Put(regiment, 0x1C, current);
    Put(regiment, 0x20, id); Put(regiment, 0x24, std::int32_t{0}); Put(regiment, 0x28, associated);
    Put(regiment, 0x148, std::int64_t{10000});
  };
  setup_persistent(same_persistent, same_persistent_id, same_regiment_id, 80, 100);
  setup_persistent(common_persistent, common_persistent_id, common_regiment_id, 18, 30);
  Put(actor, 0x18, actor_id); Put(common_character, 0x18, common_owner_id); Put(excluded_character, 0x18, excluded_owner_id);
  Put(province, 0x10, std::int32_t{1}); Put(province, 0x740, static_cast<void *>(province_occurrences.data())); Put(province, 0x74C, std::int32_t{5});
  Put(game_data, 0x140, static_cast<void *>(province_slots.data())); Put(game_data, 0x14C, std::int32_t{2});
  Put(game_state, 0xA0, static_cast<void *>(game_data.data()));
  const auto set_slot = [&](auto &slots, std::size_t index, auto &object) { Put(slots, index * 0x10 + 8, static_cast<void *>(object.data())); };
  set_slot(unit_slots, 1, subject_unit); set_slot(unit_slots, 2, same_unit); set_slot(unit_slots, 3, common_unit); set_slot(unit_slots, 4, excluded_unit);
  set_slot(army_slots, 1, subject_army); set_slot(army_slots, 2, same_army); set_slot(army_slots, 3, common_army); set_slot(army_slots, 4, excluded_army);
  set_slot(raised_slots, 2, same_regiment); set_slot(raised_slots, 3, common_regiment); set_slot(raised_slots, 4, ineligible_regiment);
  set_slot(persistent_slots, 2, same_persistent); set_slot(persistent_slots, 3, common_persistent);
  set_slot(character_slots, 1, actor); set_slot(character_slots, 2, common_character); set_slot(character_slots, 3, excluded_character);
  const auto storage = [&](auto &header, auto &slots) { Put(header, 0x20, static_cast<void *>(slots.data())); Put(header, 0x2C, std::int32_t{5}); };
  storage(units, unit_slots); storage(armies, army_slots); storage(raised, raised_slots); storage(persistent, persistent_slots); storage(characters, character_slots);
  void *unit_pointer = units.data(), *army_pointer = armies.data(), *raised_pointer = raised.data();
  void *persistent_pointer = persistent.data(), *character_pointer = characters.data(), *state_pointer = game_state.data(), *fallback_pointer = actor.data();
  raised_storage = raised.data(); common_owner = common_character.data();
  ArmyBindings bindings{}; bindings.enabled = true; bindings.game_state_slot = &state_pointer;
  bindings.unit_storage_slot = &unit_pointer; bindings.internal_army_storage_slot = &army_pointer; bindings.regiment_storage_slot = &raised_pointer;
  bindings.persistent_regiment_storage_slot = &persistent_pointer;
  bindings.get_army_current_soldiers = Count; bindings.get_army_maximum_soldiers = Maximum;
  bindings.is_regiment_supply_loss_eligible = Eligible; bindings.get_province_supply_limit = Limit; bindings.get_province_supply_usage = Usage;
  bindings.province_supply_character_fallback_slot = &fallback_pointer;
  bindings.monthly_loss_budget_bindings.character_storage_slot = &character_pointer;
  bindings.can_regiment_replenish = CanReplenish; bindings.can_chunk_replenish = ChunkCanReplenish;
  bindings.get_regiment_monthly_replenishment_fraction = Fraction; bindings.is_army_regiment_loss_writer_skipped = WriterSkipped;
  bindings.current_province_supply_contributor_bindings.enabled = true;
  bindings.current_province_supply_contributor_bindings.shares_current_war_side = CommonSide;
  const std::array<ArmyStrengthScope, 1> scope{{{subject_unit_id, game::ArmyStrengthScopeRole::player, {}}}};
  std::vector<game::ArmyStrengthSnapshot> rows;
  const auto read = [&]() {
    Check(ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available, "parent strength available");
    Check(rows.size() == 1 && rows[0].current_province_supply_contributors_v1.has_value(), "new same-query field attached");
    return rows[0];
  };
  auto row = read();
  const auto &inputs = *row.current_province_supply_contributors_v1;
  Check(inputs.current_usage_ready && inputs.contributors_ready && inputs.status == "available" && inputs.native_supply_usage_soldiers == 338 &&
        inputs.occurrences.size() == 5 && inputs.occurrences[1].army_id == inputs.occurrences[2].army_id &&
        inputs.occurrences[1].regiments.size() == 2 && inputs.occurrences[1].regiments[0].replenishment_records_v1->records.size() == 2 &&
        inputs.occurrences[1].regiments[1].native_supply_loss_eligible == false &&
        !inputs.occurrences[1].regiments[1].replenishment_records_v1 &&
        inputs.occurrences[3].inclusion_basis == "native_common_war_side" && inputs.occurrences[4].included == false &&
        !inputs.occurrences[4].native_eligible_current_soldiers, "ordered duplicates, DATA aliases, eligible, common side and excluded observed");
  Check(read() == row, "stable two-capture DTO includes all new contributor inputs");
  Check(Get<std::int32_t>(same_persistent.data(), 0x1C) == 80 && Get<std::int32_t>(same_regiment.data(), 0x38) == 160,
        "readonly query does not perform the conditional refill");
  Emit(directory, "ordered-aliases", row);
  Put(same_regiment, 0x20, static_cast<void *>(nullptr)); row = read();
  Check(row.current_province_supply_contributors_v1->contributors_ready && row.current_province_supply_contributors_v1->current_usage_ready &&
        row.current_province_supply_contributors_v1->occurrences[1].regiments[0].replenishment_records_v1->status ==
            game::ArmyRegimentReplenishmentRecordsStatusV1::unavailable, "missing DATA affects conditional model independently of current scalar/current roster");
  Emit(directory, "missing-associated-data", row); Put(same_regiment, 0x20, static_cast<void *>(same_data.data()));
  province_occurrences[4] = static_cast<std::int32_t>(0x99000004U); row = read();
  Check(row.current_province_supply_contributors_v1->current_usage_ready && !row.current_province_supply_contributors_v1->contributors_ready &&
        row.current_province_supply_contributors_v1->occurrences[4].army_id == province_occurrences[4] &&
        !row.current_province_supply_contributors_v1->occurrences[4].included, "unresolved full generation remains raw and partial");
  Emit(directory, "unresolved-roster-occurrence", row);
  Put(province, 0x74C, std::int32_t{0}); current_usage = 0; row = read();
  Check(row.current_province_supply_contributors_v1->current_usage_ready && row.current_province_supply_contributors_v1->contributors_ready &&
        row.current_province_supply_contributors_v1->occurrences.empty() && row.current_province_supply_contributors_v1->native_supply_usage_soldiers == 0,
        "legal empty roster and scalar zero stay ready");
  Emit(directory, "empty-zero", row);
  bindings.current_province_supply_contributor_bindings.enabled = false;
  Check(ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available &&
        !rows[0].current_province_supply_contributors_v1, "older producer family stays absent");
}
} // namespace
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "wire directory required"); Cases(argv[1]);
    std::cout << "PASS: current Province supply contributors and four new production wires\n"; return 0;
  } catch (const std::exception &error) {
    std::cerr << "FIXTURE RED: " << error.what() << '\n'; return 1;
  }
}
