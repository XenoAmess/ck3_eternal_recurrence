#include "xar_bridge/conception_pair_shortcircuit_observer_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <algorithm>
#include <cstring>
#include <iostream>
#include <map>
#include <stdexcept>
#include <vector>

namespace {
using namespace xar::ck3_12004;
constexpr std::uintptr_t image = 0x10000000;
constexpr std::uintptr_t first = 0x20000000;
constexpr std::uintptr_t second = 0x20001000;
constexpr std::uintptr_t scratch = 0x21000000;
constexpr std::uintptr_t model = 0x22000000;
constexpr std::uintptr_t keys = 0x23000000;
constexpr std::uintptr_t values = 0x24000000;
constexpr std::uintptr_t ids = 0x25000000;
constexpr std::uintptr_t database = 0x26000000;
constexpr std::uintptr_t entries = 0x27000000;
constexpr std::uintptr_t definition = 0x28000000;
constexpr std::uintptr_t invalid_definition = 0x29000000;

void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

struct Memory {
  std::map<std::uintptr_t, std::vector<std::byte>> regions;
  std::vector<std::uintptr_t> reads;
  void Map(std::uintptr_t address, std::size_t bytes) {
    regions.emplace(address, std::vector<std::byte>(bytes));
  }
  template <typename T> void Put(std::uintptr_t address, T value) {
    auto found = regions.upper_bound(address);
    if (found == regions.begin()) { Map(address, sizeof(T)); found = regions.upper_bound(address); }
    --found;
    const auto offset = address - found->first;
    if (offset > found->second.size() || sizeof(T) > found->second.size() - offset) {
      Map(address, sizeof(T)); found = regions.find(address);
    }
    std::memcpy(found->second.data() + (address - found->first), &value, sizeof(T));
  }
  static bool Read(void *context, const void *source, void *output,
                   std::size_t count) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    const auto address = reinterpret_cast<std::uintptr_t>(source);
    memory.reads.push_back(address);
    auto found = memory.regions.upper_bound(address);
    if (found == memory.regions.begin()) return false;
    --found;
    const auto offset = address - found->first;
    if (offset > found->second.size() || count > found->second.size() - offset) return false;
    std::memcpy(output, found->second.data() + offset, count);
    return true;
  }
  bool ReadAt(std::uintptr_t address) const {
    return std::find(reads.begin(), reads.end(), address) != reads.end();
  }
  ConceptionPairShortCircuit12004Bindings Bind() {
    return BindConceptionPairShortCircuit12004(image, kGameVersion,
        kExecutableSha256, Read, this);
  }
  void Character(std::uintptr_t address, std::uint32_t id,
                 std::uint8_t selector, std::int16_t measure) {
    Map(address, 0x200);
    Put(address + 0x18, id);
    Put(address + 0x1C, std::uint32_t{0x43686172U});
    Put(address + 0x1A1, selector);
    Put(address + 0x6C, measure);
    Put(image + 0x5C69EA0, std::int32_t{16});
    Put(image + 0x5C69EA4, std::int32_t{16});
    Put(image + 0x5C6A1A8, std::int32_t{40});
  }
  void OwnedContext(std::int32_t count) {
    Map(scratch, 0x270);
    Map(model, 0x110);
    Put(first + 0x1B0, scratch);
    Put(scratch + 0x258, model);
    Put(model + 8, first);
    Put(model + 0x10 + 0x74, count);
  }
  void TraitDatabase(std::uint32_t count) {
    Put(first + 0x104, count);
    Put(first + 0xF8, ids);
    Put(image + 0x5C67528, database);
    Map(database, 0x70);
    Put(database + 0x5C, std::int32_t{1});
    Put(database + 0x50, entries);
    Put(entries, definition);
    Put(image + 0x5D1E318, invalid_definition);
  }
};
} // namespace

int main() {
  try {
    {
      Memory m;
      const auto wrong = BindConceptionPairShortCircuit12004(image, "1.20.0.3",
          kExecutableSha256, Memory::Read, &m);
      const auto result = ReadConceptionPairShortCircuit12004(wrong, first, 1, second, 2);
      Check(!result.short_circuits_to_zero && m.reads.empty(), "exact-build guard must precede copies");
    }
    {
      Memory m; m.Character(first, 1, 1, 15);
      const auto result = ReadConceptionPairShortCircuit12004(m.Bind(), first, 1, second, 2);
      Check(result.first_output_raw == 0 && !result.second_evaluated,
            "first lower rejection must skip the second receiver");
      Check(!m.ReadAt(first + 0x1B0) && !m.ReadAt(first + 0x104) &&
            !m.ReadAt(second + 0x1C), "lower rejection must not gather later inputs");
    }
    {
      Memory m; m.Character(first, 0, 0, 20); m.Character(second, 2, 0, 20);
      const auto result = ReadConceptionPairShortCircuit12004(m.Bind(), first, 0, second, 2);
      Check(result.short_circuits_to_zero == false && !result.first_output_raw,
            "both empty zero-selector rows continue provider with no final output value");
      Check(!m.ReadAt(first + 0x1B0) && !m.ReadAt(image + 0x5C67528),
            "zero selector and observed count0 must skip context and trait database");
    }
    {
      Memory m; m.Character(first, 1, 1, 20); m.OwnedContext(3);
      m.Put(model + 0x10 + 0x68, keys); m.Put(model + 0x10 + 0xD0, values);
      m.Map(keys, 6); m.Put(keys, std::uint16_t{0x10});
      m.Put(keys + 2, std::uint16_t{0xBF}); m.Put(keys + 4, std::uint16_t{0xC0});
      m.Map(values, 24); m.Put(values + 8, std::int64_t{-50000});
      m.Put(image + 0x5C6A1A8, std::int32_t{20});
      const auto result = ReadConceptionCharacterPredicate12004(m.Bind(), first, 1);
      Check(result.predicate_true == true && result.rounded_modifier == -1 &&
            result.adjusted_maximum == 19, "owned context must select current BF value");
      std::vector<std::uintptr_t> observed_keys;
      for (const auto address : m.reads)
        if (address >= keys && address < keys + 6) observed_keys.push_back(address);
      Check(observed_keys == std::vector<std::uintptr_t>{keys + 2, keys, keys + 2},
            "modifier lookup must preserve actual partition and final key-copy order");
      Check(!m.ReadAt(first + 0x104), "upper rejection must skip traits");
    }
    {
      Memory m; m.Character(first, 1, 1, 20); m.OwnedContext(2);
      m.Put(model + 0x10 + 0x68, keys);
      m.Map(keys, 4); m.Put(keys, std::uint16_t{0x10}); m.Put(keys + 2, std::uint16_t{0x20});
      const auto result = ReadConceptionCharacterPredicate12004(m.Bind(), first, 1);
      Check(result.predicate_true == false && result.rounded_modifier == 0,
            "completed no-match yields observed raw0");
      Check(!m.ReadAt(model + 0x10 + 0xD0), "end equality must skip values pointer");
    }
    {
      for (const std::int32_t guard : {std::int32_t{-2147483647}, std::int32_t{0}, std::int32_t{-1}}) {
        Memory m; m.Character(first, 1, 1, 20);
        m.Put(image + 0x5D67B80, guard);
        m.Put(image + 0x5D67B90 + 0x74, std::int32_t{0});
        const auto result = ReadConceptionCharacterPredicate12004(m.Bind(), first, 1);
        if (guard != 0 && guard != -1) {
          Check(result.predicate_true == false, "initialized negative epoch must admit default context");
          Check(!m.ReadAt(image + 0x5D67B90 + 0x68), "context count0 skips key pointer");
        } else {
          Check(!result.predicate_true && result.reason == "current_modifier_bf_unread",
                "uninitialized/initializing default cannot manufacture no-match");
          Check(!m.ReadAt(image + 0x5D67B90 + 0x74), "pending default skips arrays");
        }
      }
    }
    {
      Memory m; m.Character(first, 1, 0, 20); m.TraitDatabase(3);
      m.Map(ids, 12); m.Put(ids, std::int32_t{0}); m.Put(ids + 4, std::int32_t{-1});
      m.Put(ids + 8, std::int32_t{7});
      m.Put(definition + 0x4A4, std::uint32_t{0x20});
      m.Put(invalid_definition + 0x4A4, std::uint32_t{0x8});
      const auto result = ReadConceptionCharacterPredicate12004(m.Bind(), first, 1);
      Check(result.predicate_true == true && result.first_blocking_trait_occurrence == 1U,
            "invalid trait ID uses native definition fallback and independent bit5 test");
      Check(!m.ReadAt(ids + 8), "blocking trait must skip remaining occurrences");
    }
    {
      Memory m; m.Character(first, 1, 0, 20); m.TraitDatabase(2);
      m.Map(ids, 8); m.Put(ids, std::int32_t{0}); m.Put(ids + 4, std::int32_t{-1});
      m.Put(invalid_definition + 0x4A4, std::uint32_t{0});
      const auto result = ReadConceptionPairShortCircuit12004(m.Bind(), first, 1, second, 2);
      Check(!result.short_circuits_to_zero && !result.second_evaluated,
            "unread earlier definition must preserve unknown first predicate");
      Check(!m.ReadAt(ids + 4) && !m.ReadAt(second + 0x1C), "unknown first stops later reads");
    }
    {
      Memory m; m.Character(first, 1, 1, 20); m.OwnedContext(-1);
      m.Put(model + 0x10 + 0x68, keys); m.Put(model + 0x10 + 0xD0, values);
      m.Put(keys, std::uint16_t{0xBF}); m.Put(values, std::int64_t{0});
      m.TraitDatabase(0xFFFFFFFFU); m.Put(ids, std::int32_t{0});
      m.Put(definition + 0x4A4, std::uint32_t{0});
      const auto result = ReadConceptionCharacterPredicate12004(m.Bind(), first, 1);
      Check(result.predicate_true == true && result.first_blocking_trait_occurrence == 0U,
            "raw DWORD countFFFFFFFF must evaluate first blocking occurrence");
      Check(m.ReadAt(keys) && m.ReadAt(values), "negative modifier count is not synthetic empty");
    }
    {
      Memory m; m.Character(first, 1, 0, 20);
      const auto result = ReadConceptionCharacterPredicate12004(m.Bind(), first, 2);
      Check(!result.predicate_true && result.reason == "current_character_identity_unavailable" &&
            !m.ReadAt(first + 0x1A1), "full ID must match before predicate inputs");
    }
    std::cout << "GREEN: actual4 guarded pair predicate observer; 10 input scenarios\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED: " << error.what() << '\n';
    return 1;
  }
}
