#include "xar_bridge/army_position_relation_28b2800_12004.hpp"
#include "xar_bridge/army_position_relation_28b2800_12004_new_focus.hpp"
#include <array>
#include <cstring>
#include <stdexcept>

namespace {
using namespace xar::ck3_12004;
constexpr std::uintptr_t kBase = 0x10000000;
struct Owned {
  std::array<std::array<std::byte, 0x1C8>, 10> chars{};
  std::array<std::array<std::byte, 0x1C8>, 10> carriers{};
  std::array<std::array<std::byte, 0x30>, 10> relations{};
  std::array<std::array<std::byte, 0xCC>, 10> links{};
  std::array<std::byte, 0x30> store{};
  std::array<std::byte, 16 * 12> table{};
  std::uintptr_t denied = 0;
  std::size_t reads = 0;
};

template <std::size_t N, class T>
void Put(std::array<std::byte, N> &buffer, std::size_t offset, T value) {
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}
template <std::size_t N>
std::uintptr_t Address(const std::array<std::byte, N> &buffer) {
  return reinterpret_cast<std::uintptr_t>(buffer.data());
}
template <std::size_t N>
bool Contains(const std::array<std::byte, N> &buffer, std::uintptr_t address,
              std::size_t size) {
  const auto begin = Address(buffer);
  return address >= begin && address - begin <= N &&
      size <= N - static_cast<std::size_t>(address - begin);
}

bool CopyOwned(void *context, std::uintptr_t address, void *out,
               std::size_t size) noexcept {
  auto &memory = *static_cast<Owned *>(context);
  ++memory.reads;
  if (address == memory.denied) return false;
  if (address == kBase + 0x5C67568 || address == kBase + 0x5C67570) {
    if (size != sizeof(std::uintptr_t)) return false;
    const auto pointer = address == kBase + 0x5C67568 ?
        Address(memory.store) : Address(memory.chars[9]);
    std::memcpy(out, &pointer, size);
    return true;
  }
  bool owned = Contains(memory.store, address, size) ||
      Contains(memory.table, address, size);
  for (std::size_t i = 0; i < memory.chars.size(); ++i) {
    owned = owned || Contains(memory.chars[i], address, size) ||
        Contains(memory.carriers[i], address, size) ||
        Contains(memory.relations[i], address, size) ||
        Contains(memory.links[i], address, size);
  }
  if (!owned) return false;
  std::memcpy(out, reinterpret_cast<const void *>(address), size);
  return true;
}

std::uint32_t Id(std::size_t i) { return 0x01000001U + static_cast<std::uint32_t>(i); }
void Reset(Owned &memory) {
  memory = {};
  for (std::size_t i = 0; i < memory.chars.size(); ++i) {
    Put(memory.chars[i], 0x18, Id(i));
    Put(memory.chars[i], 0x1C, std::uint32_t{0x43686172U});
    Put(memory.table, (i + 1) * 16 + 8, Address(memory.chars[i]));
  }
  Put(memory.store, 0x20, Address(memory.table));
  Put(memory.store, 0x2C, std::uint32_t{11});
}
void Link(Owned &memory, std::size_t from, std::size_t to, bool carrier) {
  if (carrier) {
    Put(memory.chars[from], 0x1C0, Address(memory.carriers[from]));
    Put(memory.carriers[from], 0x1C0, Address(memory.relations[from]));
    Put(memory.relations[from], 0x28, Address(memory.chars[to]));
  } else {
    Put(memory.chars[from], 0x1B8, Address(memory.links[from]));
    Put(memory.links[from], 0xC8, Id(to));
  }
}
void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
void Expect(Owned &memory, std::uint32_t target, std::optional<bool> expected,
            std::size_t maximum = 65536) {
  const auto chars = memory.chars;
  const auto carriers = memory.carriers;
  const auto relations = memory.relations;
  const auto links = memory.links;
  const auto store = memory.store;
  const auto table = memory.table;
  const ArmyRegularCoreReadonlyAccess12004 access{kBase, &memory, CopyOwned, maximum};
  const auto result = ReadArmyPosition28B280012004(
      access, Address(memory.chars[0]), static_cast<std::int32_t>(target));
  Require(result.value == expected, "28B2800 raw source branch result differs");
  Require(expected.has_value() ? result.unavailable_reason.empty() :
      !result.unavailable_reason.empty(), "knownfalse and unread input were conflated");
  Require(chars == memory.chars && carriers == memory.carriers &&
      relations == memory.relations && links == memory.links &&
      store == memory.store && table == memory.table, "guarded observer changed input storage");
}
} // namespace

namespace xar::ck3_12004 {
// Root34/33 compound central10 calls this export once; no separate main/CTest.
std::size_t RunArmyPosition28B2800NewFocus12004() {
  Owned memory;
  std::size_t cases = 0;
  Reset(memory); memory.denied = Address(memory.chars[0]) + 0x1B8;
  Expect(memory, Id(0), false); ++cases;
  Require(memory.reads == 1, "strictself gate demanded selector fields");
  Reset(memory); Link(memory, 0, 1, true);
  Expect(memory, Id(1), true); ++cases;
  Reset(memory); Link(memory, 0, 1, true);
  Put(memory.chars[1], 0x1C, std::uint32_t{0});
  Expect(memory, Id(1), false); ++cases;
  Reset(memory); Link(memory, 0, 1, false);
  Expect(memory, Id(1), true); ++cases;
  Reset(memory); Link(memory, 0, 1, false);
  Put(memory.chars[1], 0x18, std::uint32_t{0x02000002U});
  Expect(memory, Id(9), true); ++cases;
  Reset(memory); Link(memory, 0, 1, false); Link(memory, 1, 2, false);
  Link(memory, 2, 3, false); Link(memory, 3, 4, true);
  Expect(memory, Id(4), true); ++cases;
  Reset(memory);
  for (std::size_t i = 0; i < 8; ++i) Link(memory, i, i + 1, true);
  Expect(memory, Id(7), true); ++cases;
  Expect(memory, Id(8), false); ++cases;
  Reset(memory); Link(memory, 0, 1, false); Link(memory, 1, 2, false);
  Link(memory, 2, 3, false);
  Expect(memory, Id(3), std::nullopt, 2); ++cases;
  Reset(memory); Link(memory, 0, 1, true);
  memory.denied = Address(memory.chars[0]) + 0x1B8;
  Expect(memory, Id(1), std::nullopt); ++cases;
  return cases;
}
} // namespace xar::ck3_12004
