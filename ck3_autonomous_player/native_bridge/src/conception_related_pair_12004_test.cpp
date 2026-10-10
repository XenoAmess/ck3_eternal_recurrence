#include "xar_bridge/conception_related_pair_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <array>
#include <cstddef>
#include <cstring>
#include <iostream>
#include <map>
#include <stdexcept>
#include <utility>
#include <vector>

namespace {
using namespace xar::ck3_12004;
constexpr std::uintptr_t kBase = 0x100000000ULL;
constexpr std::uintptr_t kStore = 0x200000000ULL;
constexpr std::uintptr_t kSlots = 0x210000000ULL;
constexpr std::uintptr_t kFallback = 0x220000000ULL;
constexpr std::uint32_t kInvalid = 0xFFFFFFFFU;
constexpr std::uint32_t kMagic = 0x43686172U;

struct Person {
  std::uintptr_t pointer;
  std::uintptr_t relation;
  std::uint32_t id;
};
constexpr Person kFirst{0x300000000ULL, 0x310000000ULL, 0x01000001U};
constexpr Person kSecond{0x300001000ULL, 0x310001000ULL, 0x02000002U};
constexpr Person kFirstParent{0x300002000ULL, 0x310002000ULL, 0x03000003U};
constexpr Person kSecondParent{0x300003000ULL, 0x310003000ULL, 0x04000004U};
constexpr Person kSharedAncestor{0x300004000ULL, 0x310004000ULL, 0x05000005U};

struct OwnedMemory {
  std::map<std::uintptr_t, std::byte> bytes;
  std::uintptr_t denied = 0;
  std::vector<std::pair<std::uintptr_t, std::size_t>> copies;

  template <typename T> void Put(std::uintptr_t address, T value) {
    std::array<std::byte, sizeof(T)> raw{};
    std::memcpy(raw.data(), &value, sizeof(value));
    for (std::size_t i = 0; i < raw.size(); ++i) bytes[address + i] = raw[i];
  }

  void Parents(const Person &person, std::uint32_t slot0,
               std::uint32_t slot1 = kInvalid) {
    Put(person.pointer + 0x1A8, person.relation);
    Put(person.relation, slot0);
    Put(person.relation + 4, slot1);
  }

  void Add(const Person &person) {
    Put(person.pointer + 0x18, person.id);
    Put(person.pointer + 0x1C, kMagic);
    Put(kSlots + static_cast<std::uintptr_t>(person.id & 0x00FFFFFFU) * 0x10 + 8,
        person.pointer);
    Parents(person, kInvalid);
  }

  OwnedMemory() {
    Put(kBase + 0x5C67568, kStore);
    Put(kBase + 0x5C67570, kFallback);
    Put(kStore + 0x20, kSlots);
    Put(kStore + 0x2C, std::uint32_t{16});
    for (std::uint32_t i = 0; i < 16; ++i)
      Put(kSlots + static_cast<std::uintptr_t>(i) * 0x10 + 8,
          std::uintptr_t{0});
    Put(kFallback + 0x18, kInvalid);
    Put(kFallback + 0x1C, kMagic);
    Put(kFallback + 0x1A8, std::uintptr_t{0});
    for (const auto person : {kFirst, kSecond, kFirstParent,
                             kSecondParent, kSharedAncestor}) Add(person);
    Parents(kFirst, kFirstParent.id);
    Parents(kSecond, kSecondParent.id);
    Parents(kFirstParent, kSharedAncestor.id);
    Parents(kSecondParent, kSharedAncestor.id);
  }
};

bool CopyOwned(void *context, const void *address, void *output,
               std::size_t size) noexcept {
  auto &memory = *static_cast<OwnedMemory *>(context);
  const auto begin = reinterpret_cast<std::uintptr_t>(address);
  memory.copies.emplace_back(begin, size);
  if (begin == memory.denied) return false;
  auto *destination = static_cast<std::byte *>(output);
  for (std::size_t i = 0; i < size; ++i) {
    const auto found = memory.bytes.find(begin + i);
    if (found == memory.bytes.end()) return false;
    destination[i] = found->second;
  }
  return true;
}

void Require(bool condition, const char *reason) {
  if (!condition) throw std::runtime_error(reason);
}

const ConceptionRelatedCharacterRaw12004 &FindRaw(
    const ConceptionRelatedPair12004Read &read, std::uintptr_t pointer) {
  for (const auto &row : read.raw_characters)
    if (row.character == pointer) return row;
  throw std::runtime_error("expected actually traversed raw Character row absent");
}

ConceptionRelatedPair12004Read Observe(OwnedMemory &memory) {
  memory.copies.clear();
  const auto before = memory.bytes;
  const auto binding = BindConceptionRelatedPair12004(
      kGameVersion, kExecutableSha256, kBase, CopyOwned, &memory);
  auto result = ReadConceptionRelatedPairForHousehold12004(
      binding, kFirst.pointer, kFirst.id, kSecond.pointer, kSecond.id);
  Require(memory.bytes == before, "readonly observer changed fixture memory");
  for (const auto &[address, width] : memory.copies) {
    static_cast<void>(address);
    Require(width == 4 || width == 8, "unexpected field copy width");
  }
  return result;
}

void RunCurrentHouseholdRelationScene() {
  OwnedMemory scene;
  const auto cousin = Observe(scene);
  Require(cousin.status == "available" && cousin.related_pair_predicate == true &&
      cousin.second_to_first_28b3c10 == false &&
      cousin.first_to_second_28b3c10 == false &&
      cousin.first_second_28b3e50 == true,
      "two parent branches did not reach the actual third predicate true");
  Require(FindRaw(cousin, kFirst.pointer).parent_slot0_full_id ==
          kFirstParent.id &&
      FindRaw(cousin, kSecondParent.pointer).parent_slot0_full_id ==
          kSharedAncestor.id,
      "raw parent inputs lost full generation bits or concrete comparison row");

  // Identical low24 slot, different generation cannot borrow the old parent.
  scene.Put(kFirstParent.pointer + 0x18, std::uint32_t{0x08000003U});
  const auto stale_parent = Observe(scene);
  Require(stale_parent.status == "available" &&
      stale_parent.related_pair_predicate == false,
      "full-ID generation mismatch borrowed a stale parent");
  scene.Put(kFirstParent.pointer + 0x18, kFirstParent.id);

  // Matching IDs in opposite parent positions do not satisfy matching slots.
  scene.Parents(kSecondParent, kInvalid, kSharedAncestor.id);
  const auto crossed = Observe(scene);
  Require(crossed.status == "available" &&
      crossed.related_pair_predicate == false,
      "cross-position parent IDs were generalized to arbitrary relatedness");
  scene.Parents(kSecondParent, kSharedAncestor.id);

  // First native reverse helper true: later first-parent relation is irrelevant.
  scene.Parents(kSecondParent, kFirstParent.id);
  scene.denied = kFirstParent.pointer + 0x1A8;
  const auto reverse = Observe(scene);
  Require(reverse.status == "available" &&
      reverse.second_to_first_28b3c10 == true &&
      !reverse.first_to_second_28b3c10.has_value() &&
      !reverse.first_second_28b3e50.has_value() &&
      reverse.related_pair_predicate == true,
      "reverse helper true did not short circuit skipped unread branches");
  for (const auto &copy : scene.copies)
    Require(copy.first != scene.denied, "unreachable native branch was read");
  scene.denied = 0;

  // Reverse false followed by the second native helper true.
  scene.Parents(kSecondParent, kSharedAncestor.id);
  scene.Parents(kFirstParent, kSecondParent.id);
  const auto forward = Observe(scene);
  Require(forward.status == "available" &&
      forward.second_to_first_28b3c10 == false &&
      forward.first_to_second_28b3c10 == true &&
      !forward.first_second_28b3e50.has_value() &&
      forward.related_pair_predicate == true,
      "forward helper true did not preserve ordered component results");
  scene.Parents(kFirstParent, kSharedAncestor.id);

  // A real unread relation field is unknown, never a manufactured false.
  scene.denied = kSecondParent.relation;
  const auto unread = Observe(scene);
  Require(unread.status == "unavailable" &&
      unread.unavailable_reason == "native_conception_related_pair_parent_id_unread" &&
      !unread.related_pair_predicate.has_value(),
      "required field failure became a known false predicate");
  scene.denied = 0;

  // Two observed null relationship blocks use native sentinel/fallback inputs.
  scene.Put(kFirst.pointer + 0x1A8, std::uintptr_t{0});
  scene.Put(kSecond.pointer + 0x1A8, std::uintptr_t{0});
  const auto no_parents = Observe(scene);
  Require(no_parents.status == "available" &&
      no_parents.related_pair_predicate == false &&
      FindRaw(no_parents, kFirst.pointer).relationship_block_present == false &&
      FindRaw(no_parents, kFirst.pointer).parent_slot0_full_id == kInvalid &&
      FindRaw(no_parents, kFirst.pointer).parent_slot1_full_id == kInvalid,
      "native null relation was unavailable or synthesized ordinary parent0");
  scene.denied = kBase + 0x5C67570;
  const auto fallback_unread = Observe(scene);
  Require(fallback_unread.status == "unavailable" &&
      fallback_unread.unavailable_reason == "native_conception_related_pair_fallback_slot_unread" &&
      !fallback_unread.related_pair_predicate.has_value(),
      "unread actual fallback became a known absent parent");
  scene.denied = 0;

  scene.copies.clear();
  const auto wrong = BindConceptionRelatedPair12004(
      kGameVersion, "wrong-sha", kBase, CopyOwned, &scene);
  const auto rejected = ReadConceptionRelatedPairForHousehold12004(
      wrong, kFirst.pointer, kFirst.id, kSecond.pointer, kSecond.id);
  Require(!wrong.enabled && rejected.status == "unavailable" &&
      scene.copies.empty(), "wrong exact build performed memory reads");

  const auto admitted = BindConceptionRelatedPair12004(
      kGameVersion, kExecutableSha256, kBase, CopyOwned, &scene);
  const auto wrong_identity = ReadConceptionRelatedPairForHousehold12004(
      admitted, kFirst.pointer, kSecond.id, kSecond.pointer, kSecond.id);
  Require(wrong_identity.status == "unavailable" &&
      wrong_identity.unavailable_reason == "native_conception_related_pair_household_identity_mismatch" &&
      !wrong_identity.related_pair_predicate.has_value(),
      "stale caller household identity received relation output");
}

} // namespace

int main() {
  try {
    RunCurrentHouseholdRelationScene();
    std::cout << "{\"check\":\"conception_related_pair_12004_current_household_scene\","
        "\"status\":\"GREEN\",\"exact_predicate_rva\":\"2912210\","
        "\"parent_field_width\":4,\"full_generation_preserved\":true,"
        "\"short_circuit_and_unavailable_distinct\":true,"
        "\"source_memory_unchanged\":true,\"Game_or_SDK\":false}\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
