#include "xar_bridge/religion_doctrine12002_choices.hpp"

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
template <typename Buffer, typename T> void Put(Buffer &b, std::size_t offset, T value) {
  std::memcpy(b.data() + offset, &value, sizeof(value));
}
template <typename T> T Load(const void *object, std::size_t offset) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value)); return value;
}
template <typename Buffer> void Key(Buffer &b, std::size_t offset, std::string_view text) {
  std::memcpy(b.data() + offset, text.data(), text.size());
  Put(b, offset + 0x10, static_cast<std::uint64_t>(text.size()));
  Put(b, offset + 0x18, std::uint64_t{15});
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
  Bytes<0x100> extension{};
  Bytes<0x8D0> rite{}, main_rite{};
  Bytes<0xB20> doctrine_a{}, doctrine_b{}, doctrine_c{};
  Bytes<0x40> group_a{}, group_b{};
  Bytes<0x70> database{};
  std::array<const void *, 2> learned{doctrine_a.data(), doctrine_b.data()};
  std::array<const void *, 1> rite_doctrines{doctrine_c.data()};
  std::array<const void *, 3> registry{doctrine_a.data(), doctrine_b.data(), doctrine_c.data()};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  void *database_ptr = database.data();
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::uint32_t rite_id = 0x82000002;
  int knows_calls = 0;
  bool wrong_subject = false, drift = false;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, actor_id);
    Put(character, r::kCharacterRiteIdOffset, rite_id);
    Put(character, d::kCharacterKnowledgeExtensionOffset, extension.data());
    Put(rite, 8, rite_id); Put(main_rite, 8, std::uint32_t{0x83000002});
    Put(extension, d::kLearnedDoctrineArrayOffset, learned.data());
    Put(extension, d::kLearnedDoctrineCountOffset, std::int32_t{2});
    Put(rite, d::kMainRiteDoctrineArrayOffset, rite_doctrines.data());
    Put(rite, d::kMainRiteDoctrineCountOffset, std::int32_t{1});
    Put(database, d::kDefinitionRegistryArrayOffset, registry.data());
    Put(database, d::kDefinitionRegistryCountOffset, std::int32_t{3});
    Key(group_a, d::kDoctrineGroupStableKeyOffset, "group_a");
    Key(group_b, d::kDoctrineGroupStableKeyOffset, "group_b");
    Key(doctrine_a, d::kDoctrineStableKeyOffset, "doctrine_a");
    Key(doctrine_b, d::kDoctrineStableKeyOffset, "doc\"\xe4\xbf\xa1");
    Key(doctrine_c, d::kDoctrineStableKeyOffset, "doctrine_c");
    Put(doctrine_a, d::kDoctrineGroupPointerOffset, group_a.data());
    Put(doctrine_b, d::kDoctrineGroupPointerOffset, group_a.data());
    Put(doctrine_c, d::kDoctrineGroupPointerOffset, group_b.data());
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *CharacterRite(void *character) {
  if (character != f->character.data()) f->wrong_subject = true;
  return f->rite.data();
}
bool NativeKnown(void *character, const void *definition) {
  if (character != f->character.data()) f->wrong_subject = true;
  ++f->knows_calls;
  if (f->drift) return f->knows_calls % 2 != 0;
  const auto *extension = Load<const void *>(character, d::kCharacterKnowledgeExtensionOffset);
  const auto *owner = extension ? extension : f->rite.data();
  const auto array_at = extension ? d::kLearnedDoctrineArrayOffset : d::kMainRiteDoctrineArrayOffset;
  const auto count_at = extension ? d::kLearnedDoctrineCountOffset : d::kMainRiteDoctrineCountOffset;
  const auto *rows = Load<const void *const *>(owner, array_at);
  const auto count = Load<std::int32_t>(owner, count_at);
  for (std::int32_t i = 0; i < count; ++i) if (rows[i] == definition) return true;
  return false;
}
d::KnowledgeBindings Bind(Fixture &value) {
  f = &value;
  d::KnowledgeBindings b{};
  b.context.enabled = true;
  b.context.core = {true, &f->state_ptr, &f->jomini_ptr, &f->storage_ptr, &Player};
  b.context.character_rite = &CharacterRite;
  b.knows_doctrine = &NativeKnown;
  b.definition_database_global = &f->database_ptr;
  return b;
}
int checks = 0;
bool Check(bool value, const char *message) {
  ++checks; if (!value) std::cerr << "FAIL " << message << '\n'; return value;
}
template <typename Value> void Wire(const std::filesystem::path &directory, const char *name,
                                 const Value &value, std::string (*serialize)(const Value &)) {
  if (!directory.empty()) std::ofstream(directory / name) << serialize(value) << '\n';
}
} // namespace

int main(int argc, char **argv) {
  const auto output = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  Fixture q; auto b = Bind(q); d::PlayedDoctrineKnowledge knowledge{};
  if (!Check(d::ReadPlayedDoctrineKnowledge12002(b, 111, knowledge), "production learned list") ||
      !Check(knowledge.available && knowledge.capture_epoch == 111 && knowledge.played_character_id == Fixture::actor_id,
             "actual player and epoch") ||
      !Check(knowledge.rite_id == Fixture::rite_id && knowledge.knowledge_source == "character_extension",
             "full actor Rite and cached source") ||
      !Check(knowledge.learned_rows.size() == 2 && knowledge.learned_rows[0].definition.doctrine_key == "doctrine_a" &&
             knowledge.learned_rows[1].definition.doctrine_key == "doc\"\xe4\xbf\xa1", "native keys copied") ||
      !Check(knowledge.learned_rows[0].native_knows_doctrine && knowledge.learned_rows[1].native_knows_doctrine &&
             q.knows_calls == 4 && !q.wrong_subject, "actual getter called for both samples and actual player")) return 1;
  Wire(output, "learned-current.json", knowledge, &d::SerializePlayedDoctrineKnowledge12002);
  d::PlayedDoctrineKnowledgeLookup lookup{};
  if (!Check(d::ReadPlayedDoctrineKnowledgeByKey12002(b, "doctrine_a", 112, lookup) &&
             lookup.definition && lookup.native_knows_doctrine == true, "registry-resolved known definition")) return 2;
  Wire(output, "lookup-known.json", lookup, &d::SerializePlayedDoctrineKnowledgeLookup12002);
  if (!Check(d::ReadPlayedDoctrineKnowledgeByKey12002(b, "doctrine_c", 113, lookup) &&
             lookup.available && lookup.definition && lookup.native_knows_doctrine == false,
             "observed unknown doctrine is a valid false bool")) return 3;
  Wire(output, "lookup-not-known.json", lookup, &d::SerializePlayedDoctrineKnowledgeLookup12002);
  if (!Check(d::ReadPlayedDoctrineKnowledgeByKey12002(b, "does_not_exist", 114, lookup) &&
             lookup.available && !lookup.definition && !lookup.native_knows_doctrine,
             "absent definition distinct from known false")) return 4;
  Wire(output, "lookup-absent.json", lookup, &d::SerializePlayedDoctrineKnowledgeLookup12002);
  q.database_ptr = nullptr;
  if (!Check(!d::ReadPlayedDoctrineKnowledgeByKey12002(b, "doctrine_a", 115, lookup) &&
             lookup.unavailable_reason == "definition_registry_unavailable" && !lookup.native_knows_doctrine,
             "read-only database absence does not initialize")) return 5;
  Wire(output, "lookup-registry-unavailable.json", lookup, &d::SerializePlayedDoctrineKnowledgeLookup12002);
  q.database_ptr = q.database.data();
  Put(q.character, d::kCharacterKnowledgeExtensionOffset, static_cast<void *>(nullptr));
  if (!Check(d::ReadPlayedDoctrineKnowledge12002(b, 116, knowledge) && knowledge.learned_rows.size() == 1 &&
             knowledge.learned_rows[0].definition.doctrine_key == "doctrine_c" &&
             knowledge.knowledge_source == "rite_default", "extension absent uses actor Rite rather than main Rite")) return 6;
  Wire(output, "learned-rite-default.json", knowledge, &d::SerializePlayedDoctrineKnowledge12002);
  Put(q.rite, d::kMainRiteDoctrineCountOffset, std::int32_t{0});
  if (!Check(d::ReadPlayedDoctrineKnowledge12002(b, 117, knowledge) && knowledge.available &&
             knowledge.learned_rows.empty(), "valid known-empty list")) return 7;
  Wire(output, "learned-empty.json", knowledge, &d::SerializePlayedDoctrineKnowledge12002);
  Put(q.rite, 8, std::uint32_t{0x81000002});
  if (!Check(!d::ReadPlayedDoctrineKnowledge12002(b, 118, knowledge) &&
             knowledge.unavailable_reason == "rite_unavailable", "wrong full-generation native Rite")) return 8;
  Put(q.rite, 8, r::kAbsentReference); Put(q.character, r::kCharacterRiteIdOffset, r::kAbsentReference);
  if (!Check(d::ReadPlayedDoctrineKnowledge12002(b, 119, knowledge) && !knowledge.rite_id &&
             knowledge.learned_rows.empty(), "actual native absent-Rite object can supply an empty list")) return 9;
  Wire(output, "learned-native-absent-rite.json", knowledge, &d::SerializePlayedDoctrineKnowledge12002);
  Put(q.character, r::kCharacterRiteIdOffset, Fixture::rite_id); Put(q.rite, 8, Fixture::rite_id);
  Put(q.character, d::kCharacterKnowledgeExtensionOffset, q.extension.data());
  Put(q.extension, d::kLearnedDoctrineCountOffset, std::int32_t{-1});
  if (!Check(!d::ReadPlayedDoctrineKnowledge12002(b, 120, knowledge) &&
             knowledge.unavailable_reason == "knowledge_collection_unavailable", "native collection read failure")) return 10;
  Put(q.extension, d::kLearnedDoctrineCountOffset, std::int32_t{2});
  Put(q.doctrine_a, d::kDoctrineGroupPointerOffset, static_cast<void *>(nullptr));
  if (!Check(!d::ReadPlayedDoctrineKnowledge12002(b, 121, knowledge) &&
             knowledge.unavailable_reason == "doctrine_definition_unavailable", "definition copy failure")) return 11;
  Put(q.doctrine_a, d::kDoctrineGroupPointerOffset, q.group_a.data());
  q.jomini[0x20] = std::byte{0};
  if (!Check(!d::ReadPlayedDoctrineKnowledge12002(b, 122, knowledge) &&
             knowledge.unavailable_reason == "frame_not_paused", "paused actual owner context required")) return 12;
  q.jomini[0x20] = std::byte{1}; q.drift = true; q.knows_calls = 0;
  if (!Check(!d::ReadPlayedDoctrineKnowledgeByKey12002(b, "doctrine_a", 123, lookup) &&
             lookup.unavailable_reason == "state_changed", "independent actual native getter samples drift")) return 13;
  q.drift = false;
  const auto exact = d::BindDoctrineKnowledgeImage12002(0x140000000, c::kExecutableSha256);
  if (!Check(exact.context.enabled && reinterpret_cast<std::uintptr_t>(exact.knows_doctrine) == 0x1428B0C00 &&
             reinterpret_cast<std::uintptr_t>(exact.definition_database_global) == 0x145C67198,
             "exact image bindings and read-only registry global") ||
      !Check(!d::BindDoctrineKnowledgeImage12002(0x140000000, "old").context.enabled,
             "exact build required")) return 14;
  std::cout << "PASS checks=" << checks << " actual_provider=true actual_serializer=true live=false\n";
  return 0;
}
