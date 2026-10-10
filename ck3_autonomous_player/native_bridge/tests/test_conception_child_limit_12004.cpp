#include "conception_child_limit_12004.hpp"

#include <cstring>
#include <map>

using namespace xar::ck3_12004;

constexpr auto PureBase() {
  ConceptionChildLimitInputs12004 in{};
  in.selected_full_id = 0x02000022U;
  in.table_base_raw = 7;
  in.selected_relation20_living_count_raw = 0;
  in.selected_relation50_count_raw = 0;
  in.decrement_threshold_raw = 0;
  return in;
}

static_assert(SelectConceptionChildLimitRole12004(false, 9, 0) ==
              ConceptionChildLimitRole12004::second);
static_assert(SelectConceptionChildLimitRole12004(true, 4, 4) ==
              ConceptionChildLimitRole12004::second);
static_assert(SelectConceptionChildLimitRole12004(true, 5, 4) ==
              ConceptionChildLimitRole12004::first);
static_assert(EvaluateConceptionChildLimit12004(PureBase()).child_limit_raw == 7);

namespace {

struct Memory {
  std::map<std::uintptr_t, std::uint8_t> bytes;
  template <typename T> void put(std::uintptr_t address, const T &value) {
    const auto *source = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t i = 0; i < sizeof(value); ++i) bytes[address + i] = source[i];
  }
  void erase(std::uintptr_t address, std::size_t size) {
    for (std::size_t i = 0; i < size; ++i) bytes.erase(address + i);
  }
  static bool read(void *context, const void *pointer, void *output,
                   std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    auto *destination = static_cast<std::uint8_t *>(output);
    const auto address = reinterpret_cast<std::uintptr_t>(pointer);
    for (std::size_t i = 0; i < size; ++i) {
      auto found = memory.bytes.find(address + i);
      if (found == memory.bytes.end()) return false;
      destination[i] = found->second;
    }
    return true;
  }
};

constexpr std::uintptr_t base = 0x10000000;
constexpr std::uintptr_t first = 0x200000;
constexpr std::uintptr_t second = 0x300000;
constexpr std::uintptr_t family = 0x400000;
constexpr std::uintptr_t relation_data = 0x410000;
constexpr std::uintptr_t store = 0x500000;
constexpr std::uintptr_t slots = 0x510000;
constexpr std::uintptr_t alive = 0x600000;
constexpr std::uintptr_t dead = 0x700000;
constexpr std::uintptr_t fallback = 0x800000;
constexpr std::uintptr_t stale = 0x900000;
constexpr std::uintptr_t table = 0xA00000;
constexpr std::uintptr_t manager = 0xB00000;
constexpr std::uintptr_t collection_owner = 0xC00000;
constexpr std::uintptr_t ids = 0xD00000;
constexpr std::uint32_t first_id = 0x01000011;
constexpr std::uint32_t second_id = 0x02000022;

Memory FullMemory() {
  Memory m{};
  const std::array<std::uint8_t, 16> signature{
      0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x6C,
      0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x48};
  m.put(base + 0x2B94ED0, signature);
  m.put(first + 0x18, first_id);
  m.put(second + 0x18, second_id);
  m.put(first + 0x1C0, std::uint64_t{0x111});
  m.put(second + 0x1C0, std::uint64_t{0});
  m.put(second + 0x1A8, family);
  m.put(second + 0x1C8, std::uint64_t{0});
  m.put(second + 0x1B8, std::uint64_t{0});
  m.put(second + 0x1B0, std::uint64_t{0x777});
  m.put(base + 0x545CE80, table);
  m.put(table + 2*4, std::int32_t{7});
  m.put(table - 4, std::int32_t{-8});
  m.put(base + 0x5C69E80, std::int32_t{10});
  m.put(base + 0x5C69DB0, std::int32_t{20});
  m.put(base + 0x5C69D9C, std::int32_t{30});
  m.put(base + 0x5C69DB4, std::int32_t{50});
  m.put(base + 0x5C69E88, std::int32_t{40});
  m.put(base + 0x5C69E78, std::int64_t{100000});
  m.put(base + 0x5C68C50, manager);
  m.put(manager + 0xA0, collection_owner);
  m.put(collection_owner + 0x22358, ids);
  m.put(collection_owner + 0x22364, std::int32_t{2});
  m.put(ids, std::uint32_t{0x99000011}); // same low24, different generation
  m.put(ids + 4, second_id);
  m.put(family + 0x20, relation_data);
  m.put(family + 0x2C, std::int32_t{4});
  m.put(family + 0x5C, std::int32_t{3});
  m.put(relation_data, std::uint32_t{0x03000003});
  m.put(relation_data + 4, std::uint32_t{0x03000003}); // native duplicate
  m.put(relation_data + 8, std::uint32_t{0x04000004});
  m.put(relation_data + 12, std::uint32_t{0x0A000005});
  m.put(base + 0x5C67568, store);
  m.put(base + 0x5C67570, fallback);
  m.put(store + 0x2C, std::uint32_t{16});
  m.put(store + 0x20, slots);
  m.put(slots + 3*16 + 8, alive);
  m.put(slots + 4*16 + 8, dead);
  m.put(slots + 5*16 + 8, stale);
  m.put(alive + 0x18, std::uint32_t{0x03000003});
  m.put(dead + 0x18, std::uint32_t{0x04000004});
  m.put(stale + 0x18, std::uint32_t{0x0B000005});
  m.put(alive + 0x1D0, std::uint64_t{0});
  m.put(dead + 0x1D0, std::uint64_t{123});
  m.put(fallback + 0x1D0, std::uint64_t{0});
  return m;
}

auto Bind(Memory &m) {
  return BindConceptionChildLimit12004("1.20.0.4",
      "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
      base, Memory::read, &m);
}

auto Query(Memory &m, std::int32_t index = 2) {
  return ReadConceptionChildLimitForPair12004(
      Bind(m), first, first_id, second, second_id, second, second_id, index);
}

} // namespace

extern "C" __declspec(dllexport) int RunConceptionChildLimitFocus12004() {
  auto input = PureBase();
  const auto remainder = ConceptionChildLimitRemainder12004(input.selected_full_id);
  if (remainder >= 100000) return 1;
  input.decrement_threshold_raw = remainder;
  if (EvaluateConceptionChildLimit12004(input).child_limit_raw != 7) return 2;
  input.decrement_threshold_raw = static_cast<std::int64_t>(remainder) + 1;
  if (EvaluateConceptionChildLimit12004(input).child_limit_raw != 6) return 3;
  input.decrement_threshold_raw = -1;
  if (EvaluateConceptionChildLimit12004(input).child_limit_raw != 7) return 4;
  input.table_base_raw = std::numeric_limits<std::int32_t>::max();
  input.either_1c0_nonzero = true;
  input.either_1c0_bonus_raw = 1;
  input.decrement_threshold_raw = 100000;
  if (EvaluateConceptionChildLimit12004(input).child_limit_raw !=
      std::numeric_limits<std::int32_t>::max()) return 5;
  input.either_1c0_bonus_raw.reset();
  if (EvaluateConceptionChildLimit12004(input).complete) return 6;
  input = PureBase();
  input.table_base_raw.reset();
  if (EvaluateConceptionChildLimit12004(input).child_limit_raw) return 7;
  auto memory = FullMemory();
  auto read = Query(memory);
  if (read.status != "complete" || read.value.child_limit_raw != 236 ||
      read.inputs.selected_relation20_living_count_raw != 3 ||
      read.inputs.selected_relation50_count_raw != 3 ||
      read.relation20_fallback_rows != 1 ||
      !read.inputs.either_current_id_list_match) return 8;
  memory.put(base + 0x5C69E78, std::int64_t{0});
  if (Query(memory).value.child_limit_raw != 237) return 9;
  memory.erase(base + 0x5C69E88, 4);
  if (Query(memory).status != "unavailable" ||
      Query(memory).value.child_limit_raw) return 10;
  memory = FullMemory();
  auto wrong_role = ReadConceptionChildLimitForPair12004(
      Bind(memory), first, first_id, second, second_id, first, second_id, 2);
  if (wrong_role.unavailable_reason !=
      "child_limit_selected_role_identity_mismatch") return 11;
  memory.put(base + 0x2B94ED0, std::uint8_t{0});
  if (Query(memory).unavailable_reason != "child_limit_source_signature_mismatch")
    return 12;
  memory = FullMemory();
  memory.put(first + 0x1C0, std::uint64_t{0});
  memory.put(second + 0x1A8, std::uintptr_t{0});
  memory.put(second + 0x1B0, std::uint64_t{0});
  memory.put(collection_owner + 0x22364, std::int32_t{1});
  memory.put(base + 0x5459588, std::uintptr_t{0});
  memory.put(base + 0x5459588 + 0xC, std::int32_t{0});
  memory.put(base + 0x5C69E78, std::int64_t{0});
  for (const auto rva : {0x5C69E80U,0x5C69DB0U,0x5C69D9CU,0x5C69DB4U,0x5C69E88U})
    memory.erase(base + rva, 4);
  read = Query(memory);
  if (read.status != "complete" || read.value.child_limit_raw != 7 ||
      !read.used_extended_fallback || read.inputs.either_current_id_list_match)
    return 13;
  if (Query(memory, -1).value.child_limit_raw != -8) return 14;
  memory = FullMemory();
  memory.put(second + 0x1C8, std::uint64_t{1});
  memory.erase(second + 0x1C0, 8);
  memory.erase(second + 0x1B8, 8);
  memory.erase(second + 0x1B0, 8);
  read = Query(memory);
  if (read.status != "complete" || read.value.child_limit_raw != 196) return 15;
  return 0;
}
