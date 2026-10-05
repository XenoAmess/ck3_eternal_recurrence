#include "knight_effectiveness_context_memory.hpp"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <stdexcept>

namespace initialization_context_wire {
std::string SerializeRegiment(const xar::game::CombatRegimentSnapshot &);
}

namespace {
using namespace combat_fixture;
Memory<0x140> source_regiment{}, source_selector{};
Memory<0x220> selected_character{};
Memory<0xE0> selected_context{};
Memory<0x800> extra{};
Memory<0x700> culture{};
Memory<0x500> government{};
Memory<0x870> target_province{};
Memory<0xC0> target_map{};
Memory<0x40> province_definition{};
Memory<0xA00> inner_type{};
Memory<0x18> government_row{};
Memory<0x1000> culture_definition{};
std::array<Memory<0x48>, 3> culture_rows{};
std::array<void *, 1> culture_definitions{};
std::array<Memory<0x58>, 2> class_rows{};
Memory<0x20> first_row{};
std::array<Memory<0x30>, 4> new_stores{};
std::array<std::array<Memory<0x10>, 16>, 4> new_slots{};
std::array<void *, 4> new_store_ptrs{};
void *regiment_fallback = nullptr, *selector_fallback = nullptr;
void *character_fallback = nullptr, *culture_fallback = nullptr;
void *accolade_fallback = nullptr, *army_regiment_fallback = nullptr;
Memory<0x160> linked_regiment{};
Memory<0x100> linked_army{};
std::array<std::int32_t, 2> linked_ids{};
Memory<0x580> carrier{};
Memory<0x80> accolade{}, fallback_accolade{};
Memory<0x18> accolade_row{};
Memory<0x400> accolade_definition{};
Memory<0x600> tier{};
std::array<std::uint16_t, 1> selected_keys{0x1B8}, extra_keys{0x1CB}, tier_keys{0x1B7};
std::array<std::int64_t, 1> selected_values{50000}, extra_values{10000}, tier_values{15000};
std::array<std::int64_t, 5> ordinary_bases{0, -1, 0, -1, 0};
std::array<Memory<0x38>, 3> type_vectors{}, linked_vectors{};
int case_index = 0;
constexpr std::int32_t source_id = 0x01000001, selector_id = 0x01000002;
constexpr std::int32_t selected_id = 0x0100000D, linked_regiment_id = 0x0100000E;
constexpr std::int32_t culture_id = 0x01000003, accolade_id = 0x01000004;

void Require(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
void *SelectedContext(void *character) {
  if (character == selected_character.data()) return case_index == 3 ? nullptr : selected_context.data();
  return character;
}
void *Government(void *) { return government.data(); }
void *ActualArmy(void *) { return linked_army.data(); }
void *Holder(void *) { return selected_character.data(); }
std::int32_t Piety(void *) { return 2; }
void *Tier(std::int32_t level, void *definition) {
  return level == 1 && definition == accolade_definition.data() + 0x3C0 ? tier.data() : nullptr;
}
std::int64_t *SelectorFactor(std::int64_t *out, void *, void *debug) {
  if (debug) return nullptr;
  *out = 50000; return out;
}
const void *TypeTerrain(void *, void *environment) {
  return environment == terrain.data() ? type_vectors[0].data() : nullptr;
}
const void *TypeDefinition(void *, void *environment) {
  return environment == province_definition.data() ? type_vectors[1].data() : nullptr;
}
const void *TypeProvince(void *, void *environment) {
  return environment == target_province.data() ? type_vectors[2].data() : nullptr;
}
void *LinkedVector(void *out, const void *ids, std::size_t index) {
  if (Get<std::int32_t>(ids, 0xC) != 2 || Get<const std::int32_t *>(ids, 0)[0] != selected_id ||
      Get<const std::int32_t *>(ids, 0)[1] != selected_id) return nullptr;
  std::memcpy(out, linked_vectors[index].data(), 0x38); return out;
}
void *LinkedTerrain(void *out, void *, void *environment, const void *ids) {
  return environment == terrain.data() ? LinkedVector(out, ids, 0) : nullptr;
}
void *LinkedDefinition(void *out, void *, void *environment, const void *ids) {
  return environment == province_definition.data() ? LinkedVector(out, ids, 1) : nullptr;
}
void *LinkedProvince(void *out, void *, void *environment, const void *ids) {
  return environment == target_province.data() ? LinkedVector(out, ids, 2) : nullptr;
}
void *MaaStats(void *regiment, void *out, void *province) {
  return Stats(regiment, out, province == target_province.data() ? provinces[0].data() : province);
}
bool MaaHolding(void *owner, void *province) {
  return Holding(owner, province == target_province.data() ? provinces[0].data() : province);
}
xar::game::Snapshot Scope() {
  xar::game::Snapshot scope{};
  scope.paused = true; scope.has_played_character = true; scope.played_character_alive = true;
  xar::game::ArmySnapshot own{}; own.army_id = player;
  xar::game::ArmySnapshot enemy_row{}; enemy_row.army_id = enemy;
  scope.player_armies.push_back(own);
  xar::game::ActiveWarSnapshot war{}; war.war_id = 0x01000020;
  war.allied_armies.push_back(own); war.enemy_armies.push_back(enemy_row);
  scope.active_wars.push_back(war); return scope;
}

void RunCase(const std::filesystem::path &directory, int index, const char *name) {
  case_index = index;
  auto b = Setup();
  source_regiment = {}; source_selector = {}; selected_character = {}; selected_context = {};
  extra = {}; culture = {}; government = {}; inner_type = {}; first_row = {};
  target_province = {}; target_map = {}; province_definition = {};
  new_stores = {}; new_slots = {}; culture_definition = {}; culture_rows = {};
  linked_regiment = {}; linked_army = {}; carrier = {}; accolade = {}; fallback_accolade = {};
  accolade_row = {}; accolade_definition = {}; tier = {}; type_vectors = {}; linked_vectors = {};
  for (std::size_t i = 0; i != 4; ++i) {
    new_store_ptrs[i] = new_stores[i].data();
    Put(new_stores[i].data(), 0x20, new_slots[i].data());
    Put(new_stores[i].data(), 0x2C, std::int32_t{16});
  }
  Put(source_regiment.data(), 0x10, source_id);
  Put(source_regiment.data(), 0x118, inner_type.data());
  Put(source_regiment.data(), 0x120, extra.data());
  Put(source_regiment.data(), 0x12C, index == 1 ? selected_id : std::int32_t{-1});
  Put(source_regiment.data(), 0x130, index == 1 ? std::int32_t{-1} : selector_id);
  Put(new_slots[0][1].data(), 8, source_regiment.data());
  Put(source_selector.data(), 0x10, selector_id);
  Put(source_selector.data(), 0x128, selected_id);
  Put(new_slots[1][2].data(), 8, source_selector.data());
  Put(selected_character.data(), 0x18, selected_id);
  Put(selected_character.data(), 0x1C, std::uint32_t{0x43686172});
  Put(selected_character.data(), 0xB0, culture_id);
  Put(selected_character.data(), 0x1B0, carrier.data());
  Put(slots[3][13].data(), 8, selected_character.data());
  Put(selected_context.data(), 0x68, selected_keys.data());
  Put(selected_context.data(), 0x74, std::int32_t{1});
  Put(selected_context.data(), 0xD0, selected_values.data());
  Put(first_row.data(), 8, source_id);
  Put(regiments[0].data(), 0x20, first_row.data());
  Put(regiments[0].data(), 0x2C, std::int32_t{1});
  Put(inner_type.data(), 0x38, std::uint32_t{index == 2 ? 0U : 0x4744624FU});
  Put(inner_type.data(), 0x260, index == 1 ? std::int32_t{-1} : std::int32_t{1});
  Put(inner_type.data(), 0x270, std::int32_t{100});
  for (std::size_t i = 0; i != 5; ++i)
    Put(inner_type.data(), 0x278 + i * 8, static_cast<std::int64_t>((i + 1) * 100000));
  Put(rules.data(), 0xEF0, class_rows.data());
  class_rows[1].fill(std::byte{0xFF});
  Put(extra.data(), 0x30 + 0x68, extra_keys.data());
  Put(extra.data(), 0x30 + 0x74, std::int32_t{1});
  Put(extra.data(), 0x30 + 0xD0, extra_values.data());
  Put(extra.data(), 0x738, selector_id);
  Put(culture.data(), 0x10, culture_id);
  Put(new_slots[2][3].data(), 8, culture.data());
  Put(government.data(), 0x10, index == 4 ? std::int32_t{-1} : std::int32_t{0});
  Put(government.data(), 0x4D6, std::uint8_t{5});
  Put(culture.data(), 0x688, government_row.data());
  Put(culture.data(), 0x694, std::int32_t{1});
  culture_definitions[0] = culture_definition.data();
  Put(government_row.data(), 0, culture_definitions.data());
  Put(government_row.data(), 0xC, std::int32_t{1});
  Put(culture.data(), 0x6A0, culture_definitions.data());
  Put(culture.data(), 0x6AC, std::int32_t{1});
  Put(culture_definition.data(), 0x7C8, culture_rows.data());
  Put(culture_definition.data(), 0x7D4, std::int32_t{2});
  Put(culture_definition.data(), 0xFE0, culture_rows[2].data());
  Put(culture_definition.data(), 0xFEC, std::int32_t{1});
  for (std::size_t i = 0; i != 3; ++i) {
    Put(culture_rows[i].data(), 0x38, std::int32_t{-1});
    Put(culture_rows[i].data(), 0x40, i == 1 ? types[1].data() : inner_type.data());
    Put(culture_rows[i].data(), 8, std::int32_t{2});
    Put(culture_rows[i].data(), 0x18, std::int64_t{10000});
  }
  Put(target_province.data(), 0x10, std::int32_t{1});
  Put(target_province.data(), 0x20, target_map.data());
  Put(target_map.data(), 0xB8, terrain.data());
  Put(target_province.data(), 0x620, province_definition.data());
  Put(province_definition.data(), 0x38, std::uint32_t{index == 4 ? 0U : 0x4744624FU});
  province_index[1] = target_province.data();
  Put(units[1].data(), 0x20, target_province.data());
  Put(linked_regiment.data(), 0x10, linked_regiment_id);
  Put(linked_regiment.data(), 0x148, selected_id);
  Put(slots[2][14].data(), 8, linked_regiment.data());
  linked_ids = {linked_regiment_id, linked_regiment_id};
  Put(linked_army.data(), 0x38, linked_ids.data());
  Put(linked_army.data(), 0x44, std::int32_t{2});
  Put(carrier.data(), 0x570, accolade_id);
  Put(accolade.data(), 8, accolade_id);
  Put(accolade.data(), 0xC, std::uint32_t{0x4163636F});
  Put(accolade.data(), 0x58, accolade_row.data());
  Put(accolade.data(), 0x64, std::int32_t{1});
  Put(new_slots[3][4].data(), 8, accolade.data());
  Put(fallback_accolade.data(), 8, std::int32_t{-1});
  Put(accolade_row.data(), 8, std::int32_t{1});
  Put(accolade_row.data(), 0x10, accolade_definition.data());
  Put(accolade_definition.data(), 0x38, std::uint32_t{0x4744624F});
  Put(tier.data(), 0x390, tier_keys.data());
  Put(tier.data(), 0x39C, std::int32_t{1});
  Put(tier.data(), 0x3F8, tier_values.data());
  Put(type_vectors[0].data(), 0x18, std::int64_t{-50001});
  Put(linked_vectors[0].data(), 0x18, std::int64_t{20});
  b.maa_stat_inputs_enabled = true;
  regiment_fallback = source_regiment.data(); selector_fallback = source_selector.data();
  character_fallback = selected_character.data(); culture_fallback = culture.data();
  accolade_fallback = fallback_accolade.data(); army_regiment_fallback = linked_regiment.data();
  b.ordinary_regiment_storage_slot = &new_store_ptrs[0]; b.ordinary_regiment_fallback_slot = &regiment_fallback;
  b.ordinary_selector_storage_slot = &new_store_ptrs[1]; b.ordinary_selector_fallback_slot = &selector_fallback;
  b.ordinary_character_fallback_slot = &character_fallback;
  b.maa_culture_storage_slot = &new_store_ptrs[2]; b.maa_culture_fallback_slot = &culture_fallback;
  b.maa_accolade_storage_slot = &new_store_ptrs[3]; b.maa_accolade_fallback_slot = &accolade_fallback;
  b.maa_army_regiment_fallback_slot = &army_regiment_fallback;
  b.get_character_modifier_aggregator = SelectedContext;
  b.maa_get_government = Government; b.maa_get_actual_army = ActualArmy;
  b.maa_get_title_holder = Holder; b.maa_get_piety_rank = Piety;
  b.maa_get_tier = Tier; b.maa_get_selector_factor = SelectorFactor;
  b.maa_get_type_environment = {TypeTerrain, TypeDefinition, TypeProvince};
  b.maa_get_linked_environment = {LinkedTerrain, LinkedDefinition, LinkedProvince};
  b.evaluate_regiment_stats_at_province = MaaStats; b.is_holding_defender = MaaHolding;
  for (std::size_t i = 0; i != 5; ++i) b.ordinary_stat_loaded_bases[i] = &ordinary_bases[i];
  const auto regiment_before = source_regiment;
  const auto context_before = selected_context;
  const auto extra_before = extra;
  const auto culture_before = culture;
  const auto tier_before = tier;
  xar::game::CombatSimulationInputsSnapshot output{};
  const xar::game::CombatSimulationInputsRequest request{1, 2, {enemy}, {player}};
  Require(xar::ck3_12002::ReadCombatSimulationInputs(b, Scope(), request, output) ==
      xar::game::ReadCombatSimulationInputsResult::available, "optional MAA sources changed query readiness");
  Require(source_regiment == regiment_before && selected_context == context_before && extra == extra_before &&
      culture == culture_before && tier == tier_before, "MAA observer mutated source memory");
  const auto army = std::find_if(output.armies.begin(), output.armies.end(),
      [](const auto &r) { return r.army_id == enemy; });
  Require(army != output.armies.end() && army->regiments.size() == 1, "Army occurrence lost");
  const auto &r = army->regiments.front();
  Require(r.maa_stat_inputs_v1.has_value() && r.effective_stats.available, "MAA source leaf omitted");
  const auto &s = *r.maa_stat_inputs_v1;
  Require(s.available == (index != 3), "MAA independent readiness differs");
  Require(s.source_regiment_full_id == source_id && s.selected_character_full_id == selected_id,
      "actual source identity differs");
  if (index == 0 || index == 1 || index == 4) {
    Require(s.linked_character_full_ids == std::vector<std::int32_t>{selected_id, selected_id} &&
        s.accolade_blocks->size() == 2, "ordered linked duplicates lost");
    Require(s.class_row_present == (index != 1), "class presence source differs");
  }
  if (index == 1) Require(!s.extra_properties, "absent class read extra source");
  if (index == 2) Require(s.inner_type_is_gdbo == false && !s.type_bases, "inner fallback branch lost");
  if (index == 4) Require(s.government_rows->empty() && s.global_rows->empty() &&
      s.definition620_present == false && !s.environment_components[1] && !s.environment_components[4],
      "native government/definition skips became missing");
  for (const auto &a : output.armies)
    for (const auto &other : a.regiments)
      if (other.regiment_id == knight_reg) Require(!other.maa_stat_inputs_v1, "special row acquired MAA inputs");
  const auto wire = initialization_context_wire::SerializeRegiment(r);
  Require(wire.find("\"maa_stat_inputs_v1\":") != std::string::npos, "literal serializer omitted new leaf");
  std::ofstream file(directory / (std::string(name) + ".json"), std::ios::binary);
  file << wire << '\n'; Require(file.good(), "new wire write failed");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "one output directory required");
    const std::filesystem::path directory(argv[1]); std::filesystem::create_directories(directory);
    constexpr std::uintptr_t base = 0x100000000ULL;
    auto b = xar::ck3_12002::BindCombatImage(base, xar::ck3_12002::kExecutableSha256);
    Require(!b.maa_stat_inputs_enabled, "unchanged .2 binder enabled .3 MAA source");
    xar::ck3_12002::EnableMaaRegimentStatInputs12003(b, base,
        "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6");
    Require(b.maa_stat_inputs_enabled &&
        reinterpret_cast<std::uintptr_t>(b.maa_get_tier) == base + 0x2B8FCF0 &&
        reinterpret_cast<std::uintptr_t>(b.maa_culture_storage_slot) == base + 0x5D1E2F0 &&
        reinterpret_cast<std::uintptr_t>(b.maa_get_linked_environment[2]) == base + 0x2B924C0,
        "exact .3 MAA bindings differ");
    const std::array<const char *, 5> names{"full_sources", "class_absent", "inner_ordinary_fallback",
        "unavailable_selected_context", "native_government_definition_skips"};
    for (std::size_t i = 0; i != names.size(); ++i) RunCase(directory, static_cast<int>(i), names[i]);
    std::cout << "5 new MAA source/wire cases; synthetic memory only\n"; return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n'; return 1;
  }
}
