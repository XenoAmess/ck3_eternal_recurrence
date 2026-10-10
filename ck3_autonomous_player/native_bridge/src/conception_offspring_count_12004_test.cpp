#include "xar_bridge/conception_offspring_count_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <algorithm>
#include <cstddef>
#include <cstring>
#include <iostream>
#include <map>
#include <stdexcept>
#include <utility>
#include <vector>

namespace {
using namespace xar::ck3_12004;
constexpr std::uintptr_t image = 0x100000000ULL;
constexpr std::uintptr_t selected = 0x200000000ULL;
constexpr std::uintptr_t family = 0x200001000ULL;
constexpr std::uintptr_t ids = 0x200002000ULL;
constexpr std::uintptr_t store = 0x200003000ULL;
constexpr std::uintptr_t slots = 0x200004000ULL;
constexpr std::uintptr_t child_a = 0x200005000ULL;
constexpr std::uintptr_t child_b = 0x200006000ULL;
constexpr std::uintptr_t fallback = 0x200007000ULL;
constexpr std::uintptr_t trait_ids = 0x200008000ULL;
constexpr std::uintptr_t database = 0x200009000ULL;
constexpr std::uintptr_t entries = 0x20000A000ULL;
constexpr std::uintptr_t definition = 0x20000B000ULL;
constexpr std::uintptr_t invalid_definition = 0x20000C000ULL;
constexpr std::uintptr_t invalid_ids = 0x20000D000ULL;
constexpr std::uint32_t selected_id = 0x03000007;
constexpr std::uint32_t id_a = 0x01000001;
constexpr std::uint32_t id_b = 0x01000002;
constexpr std::uint32_t stale_id_a = 0x02000001;

struct Memory {
  std::map<std::uintptr_t, std::vector<std::byte>> blocks;
  std::vector<std::pair<std::uintptr_t, std::size_t>> copies;
  std::uintptr_t denied = 0;
  template <typename T> void Put(std::uintptr_t address, T value) {
    auto found = blocks.upper_bound(address);
    if (found == blocks.begin()) throw std::runtime_error("fixture block absent");
    --found;
    if (address - found->first + sizeof(T) > found->second.size())
      throw std::runtime_error("fixture store exceeds block");
    std::memcpy(found->second.data() + address - found->first, &value, sizeof(T));
  }
  bool Saw(std::uintptr_t address, std::size_t size) const {
    return std::find(copies.begin(), copies.end(), std::pair{address, size}) !=
        copies.end();
  }
};

bool Read(void *context, const void *address, void *output,
          std::size_t size) noexcept {
  auto &memory = *static_cast<Memory *>(context);
  const auto raw = reinterpret_cast<std::uintptr_t>(address);
  memory.copies.emplace_back(raw, size);
  if (raw == memory.denied) return false;
  auto found = memory.blocks.upper_bound(raw);
  if (found == memory.blocks.begin()) return false;
  --found;
  const auto offset = raw - found->first;
  if (offset > found->second.size() || size > found->second.size() - offset)
    return false;
  std::memcpy(output, found->second.data() + offset, size);
  return true;
}

void Require(bool value, const char *reason) {
  if (!value) throw std::runtime_error(reason);
}

Memory Fixture() {
  Memory memory;
  for (const auto address : {selected, child_a, child_b, fallback})
    memory.blocks[address].resize(0x1D8);
  for (const auto address : {family, store, database})
    memory.blocks[address].resize(0x60);
  memory.blocks[ids].resize(16);
  memory.blocks[slots].resize(128);
  memory.blocks[trait_ids].resize(4);
  memory.blocks[invalid_ids].resize(4);
  memory.blocks[entries].resize(8);
  memory.blocks[definition].resize(0x4AA);
  memory.blocks[invalid_definition].resize(0x4AA);
  for (const auto rva : {0x5C67568ULL, 0x5C67570ULL, 0x5C67528ULL,
                         0x5D1E318ULL, 0x5D59588ULL})
    memory.blocks[image + rva].resize(rva == 0x5D59588ULL ? 16 : 8);
  memory.Put(selected + 0x18, selected_id);
  memory.Put(selected + 0x1C, std::uint32_t{0x43686172});
  memory.Put(selected + 0x1A8, family);
  memory.Put(family + 0x38, ids);
  memory.Put(family + 0x44, std::int32_t{4});
  memory.Put(ids, id_a);
  memory.Put(ids + 4, id_b);
  memory.Put(ids + 8, id_a);
  memory.Put(ids + 12, stale_id_a);
  memory.Put(image + 0x5C67568, store);
  memory.Put(image + 0x5C67570, fallback);
  memory.Put(store + 0x20, slots);
  memory.Put(store + 0x2C, std::uint32_t{8});
  memory.Put(slots + 16 + 8, child_a);
  memory.Put(slots + 32 + 8, child_b);
  memory.Put(child_a + 0x18, id_a);
  memory.Put(child_b + 0x18, id_b);
  memory.Put(child_a + 0x104, std::int32_t{1});
  memory.Put(child_a + 0xF8, trait_ids);
  memory.Put(child_b + 0x1D0, std::uint64_t{1} << 40);
  // If read, this nonsensical trait count would make B unavailable. Native1D0
  // short circuit must skip it completely and preserve an available false row.
  memory.Put(child_b + 0x104, std::int32_t{-1});
  memory.Put(trait_ids, std::int32_t{0});
  memory.Put(image + 0x5C67528, database);
  memory.Put(image + 0x5D1E318, invalid_definition);
  memory.Put(database + 0x50, entries);
  memory.Put(database + 0x5C, std::int32_t{1});
  memory.Put(entries, definition);
  memory.Put(definition + 0x4A4, std::uint32_t{8});
  memory.Put(definition + 0x4A9, std::uint8_t{2});
  return memory;
}

ConceptionOffspringCount12004Read Run(Memory &memory) {
  const auto before = memory.blocks;
  memory.copies.clear();
  const auto binding = BindConceptionOffspringCount12004(
      image, kGameVersion, kExecutableSha256, Read, &memory);
  auto result = ReadConceptionOffspringCountForCharacter12004(
      binding, selected, selected_id);
  Require(before == memory.blocks, "leaf modified source memory");
  return result;
}

void FocusedCheck() {
  auto memory = Fixture();
  auto result = Run(memory);
  Require(result.status == "available" && result.native_count == 3 &&
      result.offspring_list_count_raw_i32 == 4 && result.rows.size() == 4,
      "ordered/fallback raw count incorrect");
  Require(result.rows[0].requested_full_id == id_a &&
      result.rows[1].requested_full_id == id_b &&
      result.rows[2].requested_full_id == id_a &&
      result.rows[3].requested_full_id == stale_id_a &&
      result.rows[3].used_character_fallback == true &&
      !result.rows[3].matched_full_id.has_value(),
      "full generation, order, duplicates or fallback lost");
  Require(result.rows[0].trait_4a9_equals_one == false &&
      result.rows[1].character_1d0_raw_u64 == (std::uint64_t{1} << 40) &&
      result.rows[1].counted == false &&
      !result.rows[1].trait_4a9_equals_one.has_value() &&
      !memory.Saw(child_b + 0x104, 4),
      "native short circuit or exact-byte comparison changed");
  Require(memory.Saw(child_b + 0x1D0, 8) &&
      memory.Saw(definition + 0x4A9, 1) &&
      !memory.Saw(definition + 0x4A4, 4), "native operand width changed");

  memory.Put(definition + 0x4A9, std::uint8_t{1});
  result = Run(memory);
  Require(result.status == "available" && result.native_count == 1 &&
      result.rows[0].first_matching_trait_id == 0 &&
      result.rows[2].trait_4a9_equals_one == true,
      "exact BYTE1 did not exclude both duplicate entries");

  memory.Put(fallback + 0x104, std::int32_t{1});
  memory.Put(fallback + 0xF8, invalid_ids);
  memory.Put(invalid_ids, std::int32_t{-1});
  memory.Put(invalid_definition + 0x4A9, std::uint8_t{1});
  result = Run(memory);
  Require(result.status == "available" && result.native_count == 0 &&
      result.rows[3].first_matching_trait_id == -1 &&
      result.rows[3].trait_4a9_equals_one == true &&
      memory.Saw(invalid_definition + 0x4A9, 1),
      "native invalid-trait fallback was skipped");

  memory.denied = definition + 0x4A9;
  result = Run(memory);
  Require(result.status == "unavailable" && !result.native_count.has_value() &&
      !result.rows[0].counted.has_value(), "unread trait byte became count zero");
  memory.denied = 0;
  memory.Put(child_a + 0x104, std::int32_t{-1});
  result = Run(memory);
  Require(result.status == "unavailable" && !result.native_count.has_value() &&
      result.rows[0].trait_count_raw_i32 == -1,
      "negative equality-loop trait count became known false");

  memory.Put(selected + 0x1A8, std::uintptr_t{0});
  result = Run(memory);
  Require(result.status == "available" && result.native_count == 0 &&
      result.family_component_present == false && result.rows.empty() &&
      memory.Saw(image + 0x5D59588, 8) &&
      !memory.Saw(image + 0x5C67568, 8),
      "null-family static default did not preserve zero-list short circuit");
  memory.Put(image + 0x5D59588 + 0xC, std::int32_t{-1});
  result = Run(memory);
  Require(result.status == "unavailable" && !result.native_count.has_value(),
      "negative offspring count became zero");
  memory.copies.clear();
  const auto wrong = BindConceptionOffspringCount12004(
      image, kGameVersion, "wrong", Read, &memory);
  result = ReadConceptionOffspringCountForCharacter12004(wrong, selected, selected_id);
  Require(!wrong.enabled && memory.copies.empty() &&
      !result.native_count.has_value(), "wrong exact build performed reads");
}
} // namespace

int main() {
  try {
    FocusedCheck();
    std::cout << "{\"check\":\"conception_offspring_count_12004_owned_memory\","
        "\"status\":\"GREEN\",\"ordered_duplicates\":true,"
        "\"full_generation_fallback\":true,\"trait_byte_exact_one\":true,"
        "\"qword_short_circuit\":true,\"read_failures_distinct\":true,"
        "\"source_memory_unchanged\":true,\"game_or_sdk\":false}\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
