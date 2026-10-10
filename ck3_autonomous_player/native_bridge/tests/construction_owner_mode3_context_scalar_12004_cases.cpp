#include "xar_bridge/construction_owner_mode3_context_scalar_12004.hpp"

#include <cassert>
#include <cstdint>
#include <cstring>
#include <limits>
#include <map>
#include <utility>
#include <vector>

namespace {
using namespace xar::ck3_12004::construction_owner_mode3;

struct Memory {
  std::map<std::uintptr_t, std::uint8_t> bytes;
  std::vector<std::pair<std::uintptr_t, std::size_t>> reads;
  std::vector<std::uintptr_t> scripted_character_stores;
  std::size_t character_store_index = 0;
  static constexpr std::uintptr_t module = 0x10000000;
  static constexpr std::uintptr_t context = 0x20000000;
  static constexpr std::uintptr_t data = 0x20001000;
  static constexpr std::uintptr_t title_store = 0x30000000;
  static constexpr std::uintptr_t title_slots = 0x30001000;
  static constexpr std::uintptr_t title_fallback = 0x40000000;
  static constexpr std::uintptr_t character_fallback = 0x50000000;

  template <typename T> void Put(std::uintptr_t address, T value) {
    const auto *raw = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t i = 0; i < sizeof(T); ++i) bytes[address + i] = raw[i];
  }
  static bool Read(void *opaque, const void *pointer, void *out,
                   std::size_t width) {
    auto &memory = *static_cast<Memory *>(opaque);
    const auto address = reinterpret_cast<std::uintptr_t>(pointer);
    memory.reads.emplace_back(address, width);
    if (address == module + 0x5C67568 && width == sizeof(std::uintptr_t) &&
        memory.character_store_index < memory.scripted_character_stores.size()) {
      const auto value = memory.scripted_character_stores[memory.character_store_index++];
      std::memcpy(out, &value, width);
      return true;
    }
    auto *raw = static_cast<std::uint8_t *>(out);
    for (std::size_t i = 0; i < width; ++i) {
      const auto found = memory.bytes.find(address + i);
      if (found == memory.bytes.end()) return false;
      raw[i] = found->second;
    }
    return true;
  }
  RawReceiverAccessV1 Access() {
    return {this, Read, module, true};
  }
  std::size_t CountReads(std::uintptr_t address) const {
    std::size_t count = 0;
    for (const auto &read : reads) if (read.first == address) ++count;
    return count;
  }
  void Collection(std::int32_t count) {
    Put(context + 0x28, count == 0 ? std::uintptr_t{0} : data);
    Put(context + 0x34, count);
  }
  void Globals() {
    Put(module + 0x5D1DAF8, title_store);
    Put(module + 0x5D1DAE0, title_fallback);
    Put(title_store + 0x2C, std::uint32_t{4});
    Put(title_store + 0x20, title_slots);
    Put(module + 0x5C67568, std::uintptr_t{0});
    Put(module + 0x5C67570, character_fallback);
    Put(character_fallback + 0x1C0, std::uintptr_t{0});
  }
  void Title(std::size_t occurrence, std::uint32_t title_id,
              std::uint32_t candidate, bool branch = false) {
    const auto reference = std::uintptr_t{0x60000000} + occurrence * 0x1000;
    const auto title = std::uintptr_t{0x70000000} + occurrence * 0x1000;
    Put(data + occurrence * 8, reference);
    Put(reference + 0x738, title_id);
    Put(title_slots + (title_id & 0xFFFFFFu) * 16 + 8, title);
    Put(title + 0x10, title_id);
    Put(title + 0x130, std::uint8_t{static_cast<std::uint8_t>(branch)});
    Put(title + 0x12C, title_id);
    Put(title + 0x128, candidate);
  }
};

struct Child {
  std::vector<std::int64_t> values;
  std::vector<std::uintptr_t> characters;
  std::vector<std::uint16_t> keys;
  bool available = true;
  static bool Read(void *opaque, const RawReceiverAccessV1 &,
                   std::uintptr_t character, std::uint16_t key,
                   std::uintptr_t detail, std::int64_t scale,
                   std::int64_t &value) noexcept {
    auto &child = *static_cast<Child *>(opaque);
    assert(detail == 0 && scale == 100000);
    const auto index = child.characters.size();
    child.characters.push_back(character);
    child.keys.push_back(key);
    if (!child.available || index >= child.values.size()) return false;
    value = child.values[index];
    return true;
  }
  ReadContextScalarChild2C4D1D0V1 Adapter() { return {this, Read, true}; }
};

ContextScalarResultV1 Read(Memory &memory, const ReadContextScalarChild2C4D1D0V1 &child,
                           std::uint16_t key = 0xA5, std::uintptr_t detail = 0,
                           std::size_t limit = 4096) {
  return ReadContextScalar2C82340V1(memory.Access(), Memory::context, key,
                                   detail, child, limit);
}
} // namespace

// Root03/10 imports this new fragment into the sole fresh mode3 compound.
// No main and no execution are provided by this packet.
void RunConstructionOwnerMode3ContextScalar12004Cases() {
  {
    Memory memory;
    memory.Collection(0);
    const auto result = Read(memory, {});
    assert(result.observed && result.raw_qword == 0);
    assert(result.ordered_unique_full_ids.empty());
    assert(memory.reads.size() == 2); // no globals/child for native empty.
  }
  {
    Memory memory;
    memory.Collection(3);
    memory.Globals();
    memory.Title(0, 0x01000001, 0x01000005);
    memory.Title(1, 0x01000002, 0x02000005);
    memory.Title(2, 0x01000003, 0x01000005);
    Child child{{std::numeric_limits<std::int64_t>::max(), 1}, {}, {}};
    const auto result = Read(memory, child.Adapter(), 0xA7);
    assert(result.observed && result.raw_qword == std::numeric_limits<std::int64_t>::min());
    assert((result.ordered_unique_full_ids == std::vector<std::uint32_t>{0x01000005, 0x02000005}));
    assert(result.occurrences[0].unique_index == 0);
    assert(result.occurrences[1].unique_index == 1);
    assert(result.occurrences[2].unique_index == 0);
    assert(child.characters.size() == 2 && child.keys[0] == 0xA7 && child.keys[1] == 0xA7);
    assert(result.child_operands[0].requested_character_full_id == 0x01000005);
    assert(result.child_operands[1].requested_character_full_id == 0x02000005);
    assert(memory.CountReads(Memory::module + 0x5D1DAF8) == 4);
    assert(memory.CountReads(Memory::module + 0x5D1DAE0) == 4);
  }
  {
    Memory memory;
    memory.Collection(1);
    memory.Globals();
    memory.Title(0, 0x01000001, 0xFFFFFFFFu);
    const auto result = Read(memory, {});
    assert(result.observed && result.raw_qword == 0);
    assert(result.occurrences[0].skipped_sentinel);
    assert(result.occurrences[0].used_first_title_candidate);
    assert(memory.CountReads(Memory::module + 0x5D1DAF8) == 1);
    assert(memory.CountReads(Memory::module + 0x5C67568) == 0);
  }
  {
    Memory memory;
    memory.Collection(1);
    memory.Globals();
    memory.Title(0, 0x01000001, 0, true);
    Child child{{-7}, {}, {}};
    const auto result = Read(memory, child.Adapter(), 0xFFFF);
    assert(result.observed && result.raw_qword == -7);
    assert(result.ordered_unique_full_ids[0] == 0);
    assert(result.occurrences[0].domain_pointer == 0);
    assert(result.occurrences[0].used_first_title_candidate);
    assert(child.keys[0] == 0xFFFF);
  }
  {
    Memory memory;
    memory.Collection(1);
    memory.Globals();
    memory.Title(0, 0x01000001, 0x81000001, true);
    const auto domain = std::uintptr_t{0x80000000};
    memory.Put(Memory::character_fallback + 0x1C0, domain);
    memory.Put(domain + 0x1B8, std::uint32_t{0xFFFFFFFFu});
    Child child{{11}, {}, {}};
    const auto result = Read(memory, child.Adapter());
    assert(result.observed && result.raw_qword == 11);
    assert(result.ordered_unique_full_ids[0] == 0x81000001);
    assert(result.occurrences[0].used_first_title_candidate);
  }
  {
    Memory memory;
    memory.Collection(1);
    memory.Globals();
    memory.Title(0, 0x01000001, 0x81000001, true);
    const auto domain = std::uintptr_t{0x80000000};
    memory.Put(Memory::character_fallback + 0x1C0, domain);
    memory.Put(domain + 0x1B8, std::uint32_t{0x82000002});
    Child child{{13}, {}, {}};
    const auto result = Read(memory, child.Adapter());
    assert(result.observed && result.raw_qword == 13);
    assert(result.ordered_unique_full_ids[0] == 0x82000002);
    assert(!result.occurrences[0].used_first_title_candidate);
  }
  {
    Memory memory;
    memory.Collection(1);
    memory.Globals();
    memory.Title(0, 0x01000001, 9);
    memory.Put(std::uintptr_t{0x70000000} + 0x10, std::uint32_t{0x02000001});
    memory.Put(Memory::title_fallback + 0x130, std::uint8_t{0});
    memory.Put(Memory::title_fallback + 0x12C, std::uint32_t{0xFFFFFFFFu});
    memory.Put(Memory::title_fallback + 0x128, std::uint32_t{0x83000003});
    Child child{{17}, {}, {}};
    const auto result = Read(memory, child.Adapter());
    assert(result.observed && result.raw_qword == 17);
    assert(result.occurrences[0].title_pointer == Memory::title_fallback);
    assert(result.ordered_unique_full_ids[0] == 0x83000003);
  }
  {
    Memory memory;
    memory.Collection(1);
    memory.Globals();
    memory.Title(0, 0x01000001, 0x01000005);
    const auto result = Read(memory, {});
    assert(!result.observed && !result.raw_qword);
    assert(result.failure == ContextScalarFailureV1::child_unavailable);
    assert(result.ordered_unique_full_ids[0] == 0x01000005);
  }
  {
    Memory memory;
    memory.Collection(1);
    memory.Globals();
    memory.Title(0, 0x01000001, 0x01000005);
    Child child{{23}, {}, {}, false};
    const auto result = Read(memory, child.Adapter());
    assert(!result.observed && !result.raw_qword);
    assert(result.failure == ContextScalarFailureV1::child_unavailable);
  }
  {
    Memory memory;
    memory.Collection(1);
    memory.Globals();
    memory.Title(0, 0x01000001, 0x01000005, true);
    memory.bytes.erase(Memory::character_fallback + 0x1C0);
    const auto result = Read(memory, {});
    assert(!result.observed && !result.raw_qword);
    assert(result.failure == ContextScalarFailureV1::character_fields);
  }
  {
    Memory memory;
    memory.Collection(1);
    memory.Globals();
    memory.Title(0, 0x01000001, 0x01000005, true);
    memory.scripted_character_stores = {0x90000000, 0};
    const auto result = Read(memory, {});
    assert(!result.observed && !result.raw_qword);
    assert(result.failure == ContextScalarFailureV1::character_registry);
    assert(memory.CountReads(Memory::module + 0x5C67570) == 0);
  }
  {
    Memory memory;
    memory.Collection(-1);
    const auto result = Read(memory, {});
    assert(!result.observed && result.failure == ContextScalarFailureV1::occurrence_limit);
    assert(memory.reads.size() == 2);
  }
  {
    Memory memory;
    memory.Collection(2);
    const auto result = Read(memory, {}, 0xA5, 0, 1);
    assert(!result.observed && result.failure == ContextScalarFailureV1::occurrence_limit);
  }
  {
    Memory memory;
    memory.Collection(0);
    const auto result = Read(memory, {}, 0xA5, 1);
    assert(!result.observed && result.failure == ContextScalarFailureV1::detail_route);
    assert(memory.reads.empty());
  }
}
