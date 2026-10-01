#include "xar_bridge/religion_doctrine12002_query.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace d = xar::ck3_12002::religion::doctrine12002;
namespace r = xar::ck3_12002::religion;
namespace c = xar::ck3_12002;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename B, typename T> void Put(B &b, std::size_t at, T value) {
  std::memcpy(b.data() + at, &value, sizeof(value));
}
template <typename T> T Get(const void *p, std::size_t at) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(p) + at, sizeof(value)); return value;
}
template <typename B> void Text(B &b, std::size_t at, std::string_view value) {
  if (value.size() < 16) std::memcpy(b.data() + at, value.data(), value.size());
  else Put(b, at, value.data());
  Put(b, at + 0x10, static_cast<std::uint64_t>(value.size()));
  Put(b, at + 0x18, value.size() < 16 ? std::uint64_t{15} : static_cast<std::uint64_t>(value.size()));
}
struct Fixture {
  Bytes<0xA8> state{};
  Bytes<0x28> jomini{};
  Bytes<0x1F8> players{};
  Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> storage{};
  Bytes<0x80> slots{};
  Bytes<0x1D8> character{};
  Bytes<0x900> actor_rite{}, main_rite{};
  Bytes<0x320> faith{};
  Bytes<0x40> religion{};
  Bytes<0x50> religion_definition{}, group{};
  Bytes<0xB20> actor_doctrine{}, faith_doctrine{};
  std::array<void *, 1> actor_rows{actor_doctrine.data()}, faith_rows{faith_doctrine.data()};
  std::array<std::int32_t, 1> actor_tokens{11}, main_tokens{22};
  Bytes<0x20> actor_parameter_key{}, main_parameter_key{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::uint32_t actor_rite_id = 0x81000006, main_rite_id = 0x82000007;
  static constexpr std::uint32_t faith_id = 0x83000003, religion_id = 0x84000005;
  bool missing_parameter_key = false;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, actor_id);
    Put(character, r::kCharacterRiteIdOffset, actor_rite_id);
    Put(actor_rite, 8, actor_rite_id); Put(main_rite, 8, main_rite_id);
    Put(actor_rite, r::kRiteFaithIdOffset, faith_id); Put(main_rite, r::kRiteFaithIdOffset, faith_id);
    Put(faith, 8, faith_id); Put(faith, r::kFaithReligionIdOffset, religion_id);
    Put(faith, r::kFaithMainRiteIdOffset, main_rite_id);
    Put(religion, 8, religion_id); Put(religion, 0x20, religion_definition.data());
    Text(faith, 0xE0, "faith_current"); Text(religion_definition, 0x28, "religion_current");
    Text(group, 0x18, "head_group");
    Text(actor_doctrine, 0x18, "doctrine_actor\"礼"); Text(faith_doctrine, 0x18, "doctrine_faith_main");
    Put(actor_doctrine, 0xB08, group.data()); Put(faith_doctrine, 0xB08, group.data());
    Put(actor_rite, 0x7A0, actor_rows.data()); Put(actor_rite, 0x7A8, std::int32_t{1}); Put(actor_rite, 0x7AC, std::int32_t{1});
    Put(main_rite, 0x7A0, faith_rows.data()); Put(main_rite, 0x7A8, std::int32_t{1}); Put(main_rite, 0x7AC, std::int32_t{1});
    Put(actor_rite, 0x7B8, actor_tokens.data()); Put(actor_rite, 0x7C4, std::int32_t{1});
    Put(main_rite, 0x7B8, main_tokens.data()); Put(main_rite, 0x7C4, std::int32_t{1});
    Text(actor_parameter_key, 0, "actor_rule"); Text(main_parameter_key, 0, "main_rule");
  }
};
Fixture *active = nullptr;
void *Player(void *) { return active->player.data(); }
void *ActorRite(void *) { return active->actor_rite.data(); }
void *Faith(void *) { return active->faith.data(); }
void *Religion(void *) { return active->religion.data(); }
void *MainRite(void *) { return active->main_rite.data(); }
std::int64_t *Fixed(void *, std::int64_t *out) { *out = 0; return out; }
const void *FaithTag(void *faith) { return static_cast<const std::byte *>(faith) + 0xE0; }
const void *ReligionTag(void *religion) {
  return static_cast<const std::byte *>(Get<const void *>(religion, 0x20)) + 0x28;
}
bool Membership(const void *array, const std::int32_t *token) {
  const auto *rows = Get<const std::int32_t *>(array, 0);
  const auto count = Get<std::int32_t>(array, 0xC);
  for (std::int32_t i = 0; i < count; ++i) if (rows[i] == *token) return true;
  return false;
}
const void *ParameterKey(std::int32_t token) {
  if (active->missing_parameter_key) return nullptr;
  return token == 11 ? active->actor_parameter_key.data() : active->main_parameter_key.data();
}
d::CurrentDoctrineBindings Bind(Fixture &fixture) {
  active = &fixture;
  d::CurrentDoctrineBindings b{};
  b.context.enabled = true;
  b.context.core = {true, &active->state_ptr, &active->jomini_ptr, &active->storage_ptr, &Player};
  b.context.character_rite = &ActorRite; b.context.character_faith = &Faith;
  b.context.rite_faith = &Faith; b.context.faith_religion = &Religion; b.context.faith_main_rite = &MainRite;
  b.context.faith_fervor = &Fixed; b.context.character_spiritual_fulfillment = &Fixed;
  b.context.faith_tag = &FaithTag; b.context.religion_tag = &ReligionTag;
  b.parameters = {true, &Membership, &ParameterKey};
  return b;
}
[[maybe_unused]] void Wire(const std::filesystem::path &directory, const char *name, const d::CurrentDoctrineContext &value) {
  std::ofstream(directory / name) << d::SerializePlayedCurrentDoctrines12002(value) << '\n';
}
} // namespace

#if !defined(XAR_CURRENT_DOCTRINE_FIXTURE_MEMORY_ONLY)
int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const std::filesystem::path output(argv[1]);
  Fixture fixture; const auto bindings = Bind(fixture);
  d::CurrentDoctrineContext observation{};
  if (!d::ReadPlayedCurrentDoctrines12002(bindings, 77, observation) ||
      observation.current_rite.rows.size() != 1 || observation.faith_main_rite.rows.size() != 1 ||
      observation.current_rite.rows[0].doctrine_key == observation.faith_main_rite.rows[0].doctrine_key ||
      observation.current_rite.rows[0].source != "rite_effective" ||
      observation.faith_main_rite.rows[0].source != "faith_main_rite" ||
      !observation.boolean_parameters.current_rite || !observation.boolean_parameters.faith_main_rite ||
      observation.boolean_parameters.current_rite->parameters[0].key != "actor_rule" ||
      observation.boolean_parameters.faith_main_rite->parameters[0].key != "main_rule") return 3;
  Wire(output, "current-scopes.json", observation);
  Put(fixture.actor_rite, 0x7AC, std::int32_t{0}); Put(fixture.main_rite, 0x7AC, std::int32_t{0});
  Put(fixture.actor_rite, 0x7C4, std::int32_t{0}); Put(fixture.main_rite, 0x7C4, std::int32_t{0});
  if (!d::ReadPlayedCurrentDoctrines12002(bindings, 78, observation) || !observation.available ||
      !observation.current_rite.rows.empty() || !observation.faith_main_rite.rows.empty() ||
      !observation.boolean_parameters.current_rite->parameters.empty() ||
      !observation.boolean_parameters.faith_main_rite->parameters.empty()) return 4;
  Wire(output, "known-empty.json", observation);
  Put(fixture.actor_rite, 0x7C4, std::int32_t{1}); fixture.missing_parameter_key = true;
  if (d::ReadPlayedCurrentDoctrines12002(bindings, 79, observation) || observation.available ||
      !observation.unavailable_reason.starts_with("boolean_parameters:")) return 5;
  Wire(output, "parameter-unavailable.json", observation);
  std::cout << "PASS actual_cross_provider_cases=3 actual_serializer=true live=false\n";
  return 0;
}
#endif
