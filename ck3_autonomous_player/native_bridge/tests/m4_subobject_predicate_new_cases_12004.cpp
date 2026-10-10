// Fresh actual2C39EE0 cases for13->03d->10's sole mode3 compound. No main.
#include "xar_bridge/m4_subobject_predicate_12004.hpp"

#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace {
using namespace xar::ck3_12004;
constexpr std::uintptr_t kBase = 0x140000000ULL;
constexpr std::uintptr_t kSubobject = 0x500620;
constexpr std::uintptr_t kData = 0x600000;
constexpr std::uintptr_t kObject = 0x610000;
constexpr std::uintptr_t kDefault = 0x620000;
constexpr std::uintptr_t kParentRdi = 0x630000;
constexpr std::uint64_t kRevision = 0xFE010203F4050607ULL;

struct Fixture {
  std::unordered_map<std::uintptr_t, std::uint8_t> memory;
  std::vector<std::pair<std::uintptr_t, std::size_t>> reads;
  construction_owner_mode3::RawReceiverAccessV1 access{this, &ReadMemory, kBase, true};

  template<class T> void Put(std::uintptr_t address, T value) {
    const auto *bytes = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t i = 0; i < sizeof(value); ++i) memory[address + i] = bytes[i];
  }

  static bool ReadMemory(void *context, const void *address,
                         void *out, std::size_t count) {
    auto &self = *static_cast<Fixture *>(context);
    const auto raw = reinterpret_cast<std::uintptr_t>(address);
    self.reads.emplace_back(raw, count);
    for (std::size_t i = 0; i < count; ++i)
      if (self.memory.find(raw + i) == self.memory.end()) return false;
    auto *bytes = static_cast<std::uint8_t *>(out);
    for (std::size_t i = 0; i < count; ++i) bytes[i] = self.memory[raw + i];
    return true;
  }

  std::size_t ReadCount(std::uintptr_t address) const {
    std::size_t count = 0;
    for (const auto &row : reads) count += row.first == address;
    return count;
  }

  void Direct(std::uint32_t count, std::uint8_t flag) {
    Put<std::uintptr_t>(kSubobject, kParentRdi);
    Put<std::uint32_t>(kSubobject + 0x1C, count);
    Put<std::uintptr_t>(kSubobject + 0x10, kData);
    Put<std::uintptr_t>(kData, kObject);
    Put<std::uint32_t>(kObject + 0x38, 0x4744624F);
    Put<std::uint8_t>(kData + 8, flag);
  }
};

bool Need(bool condition, std::string &failure, const char *label) {
  if (!condition) failure = label;
  return condition;
}
} // namespace

bool RunNewM4SubobjectPredicateCases12004(std::string &failure) {
  using namespace xar::ck3_12004;
  failure.clear();
  {
    Fixture f;
    f.Direct(UINT32_MAX, 6);
    bool out = false;
    M4SubobjectPredicateSource12004 source;
    if (!Need(ReadM4SubobjectPredicate12004(f.access, kSubobject, kRevision, out, &source)
              && out && source.output_al == 1 && source.source_complete
              && source.count_1c_raw_u32 == UINT32_MAX
              && source.original_subobject_identity == kSubobject
              && source.unchanged_snapshot_revision == kRevision
              && source.selected_object_identity == kObject
              && f.ReadCount(kSubobject) == 0
              && f.ReadCount(kSubobject + 0x10) == 2
              && f.ReadCount(kBase + 0x5D1E320) == 0,
              failure, "nonzero raw count and flag use original RCX subobject and preserve full64 frame"))
      return false;
  }
  {
    Fixture f;
    f.Direct(0, 0);
    f.Put<std::uintptr_t>(kBase + 0x5D1E320, kDefault);
    f.Put<std::uint32_t>(kDefault + 0x38, 0x4744624F);
    bool out = true;
    M4SubobjectPredicateSource12004 source;
    if (!Need(ReadM4SubobjectPredicate12004(f.access, kSubobject, kRevision, out, &source)
              && !out && source.output_al == 0 && source.source_complete
              && source.selected_object_identity == kDefault
              && !source.first_data_identity && source.flag_data_identity == kData
              && f.ReadCount(kData) == 0 && f.ReadCount(kSubobject + 0x10) == 1,
              failure, "zero count selects exact global but still reads actual flag data on matching magic"))
      return false;
  }
  {
    Fixture f;
    f.Put<std::uint32_t>(kSubobject + 0x1C, 0);
    f.Put<std::uintptr_t>(kBase + 0x5D1E320, kDefault);
    f.Put<std::uint32_t>(kDefault + 0x38, 0x4744624E);
    bool out = true;
    if (!Need(ReadM4SubobjectPredicateAdapter12004(nullptr, f.access, kSubobject, kRevision, out)
              && !out && f.ReadCount(kSubobject + 0x10) == 0,
              failure, "wrong magic is observed AL0 without backfilling absent flag data")) return false;
  }
  {
    Fixture f;
    f.Direct(1, 7);
    f.Put<std::uint32_t>(kObject + 0x38, 0x4744624E);
    bool out = true;
    M4SubobjectPredicateSource12004 source;
    if (!Need(ReadM4SubobjectPredicate12004(f.access, kSubobject, 0, out, &source)
              && !out && source.source_complete && source.unchanged_snapshot_revision == 0
              && !source.flag_data_identity && !source.flag_08_raw_u8
              && f.ReadCount(kSubobject + 0x10) == 1 && f.ReadCount(kData + 8) == 0,
              failure, "magic branch preserves missing unvisited fields and adds no caller revision gate"))
      return false;
  }
  {
    Fixture f;
    f.Direct(1, 1);
    for (std::size_t i = 0; i < 4; ++i) f.memory.erase(kObject + 0x38 + i);
    bool out = true;
    M4SubobjectPredicateSource12004 source;
    if (!Need(!ReadM4SubobjectPredicate12004(f.access, kSubobject, kRevision, out, &source)
              && out && !source.source_complete && !source.output_al
              && f.ReadCount(kData + 8) == 0,
              failure, "uncaptured magic remains unavailable rather than observed AL0")) return false;
  }
  {
    Fixture f;
    f.Direct(1, 1);
    f.memory.erase(kData + 8);
    bool out = true;
    M4SubobjectPredicateSource12004 source;
    if (!Need(!ReadM4SubobjectPredicate12004(f.access, kSubobject, kRevision, out, &source)
              && out && !source.source_complete && !source.output_al
              && source.selected_magic_38_raw_u32 == 0x4744624FU,
              failure, "matching magic without captured flag cannot manufacture a boolean result")) return false;
  }
  return true;
}
