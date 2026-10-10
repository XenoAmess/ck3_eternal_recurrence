// Fresh actual2C42820 cases exported to03's single new compound. No main.
#include "xar_bridge/title_selected_full_id_12004.hpp"

#include <initializer_list>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace {
using namespace xar::ck3_12004;
constexpr std::uintptr_t kBase = 0x140000000ULL;
constexpr std::uintptr_t kTitle = 0x500000;
constexpr std::uintptr_t kStore = 0x600000;
constexpr std::uintptr_t kTable = 0x610000;
constexpr std::uintptr_t kObject = 0x620000;
constexpr std::uintptr_t kFallback = 0x630000;
constexpr std::uintptr_t kLink = 0x640000;
constexpr std::uintptr_t kFallbackLink = 0x650000;

struct Fixture {
  std::unordered_map<std::uintptr_t, std::uint8_t> memory;
  std::vector<std::pair<std::uintptr_t, std::size_t>> reads;
  TitleSelectedFullIdAccess12004 access{this, &ReadMemory, kBase, true};

  template<class T> void Put(std::uintptr_t address, T value) {
    const auto *bytes = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t i = 0; i < sizeof(value); ++i) memory[address + i] = bytes[i];
  }

  static bool ReadMemory(void *context, std::uintptr_t address,
                         void *out, std::size_t count) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    self.reads.emplace_back(address, count);
    for (std::size_t i = 0; i < count; ++i)
      if (self.memory.find(address + i) == self.memory.end()) return false;
    auto *bytes = static_cast<std::uint8_t *>(out);
    for (std::size_t i = 0; i < count; ++i) bytes[i] = self.memory[address + i];
    return true;
  }

  bool ReadAt(std::uintptr_t address) const {
    for (const auto &row : reads) if (row.first == address) return true;
    return false;
  }

  void Direct(bool nonzero, std::uint32_t requested) {
    Put<std::uint8_t>(kTitle + 0x130, nonzero ? 7 : 0);
    Put<std::uint32_t>(kTitle + (nonzero ? 0x128 : 0x12C), requested);
    Put<std::uintptr_t>(kBase + (nonzero ? 0x5C67568 : 0x5D1DAF8), kStore);
    Put<std::uintptr_t>(kBase + (nonzero ? 0x5C67570 : 0x5D1DAE0), kFallback);
    Put<std::uint32_t>(kStore + 0x2C, (requested & 0xFFFFFFU) + 1);
    Put<std::uintptr_t>(kStore + 0x20, kTable);
    Put<std::uintptr_t>(kTable + std::uintptr_t(requested & 0xFFFFFFU) * 16 + 8, kObject);
    Put<std::uint32_t>(kObject + (nonzero ? 0x18 : 0x10), requested);
  }
};

bool Need(bool condition, std::string &failure, const char *label) {
  if (!condition) failure = label;
  return condition;
}
} // namespace

bool RunNewTitleSelectedFullIdCases12004(std::string &failure) {
  using namespace xar::ck3_12004;
  failure.clear();
  {
    Fixture f;
    f.Direct(true, 0x81000003);
    f.Put<std::uintptr_t>(kObject + 0x1C0, kLink);
    f.Put<std::uint32_t>(kLink + 0x1B8, 0xFE00000A);
    std::uint32_t out = 0;
    TitleSelectedFullIdSource12004 source;
    if (!Need(ReadTitleSelectedFullId12004(f.access, kTitle, out, &source)
              && out == 0xFE00000A && source.output_full_id == out
              && source.source_complete && source.requested_full_id == 0x81000003
              && source.used_fallback == false
              && source.branch == TitleSelectedFullIdBranch12004::flag_nonzero_character_link,
              failure, "nonzero flag exact Character -> linked raw output generation")) return false;
  }
  {
    Fixture f;
    f.Direct(false, 0xC2000003);
    f.Put<std::uint32_t>(kTitle + 0x128, 0x11000001);
    f.Put<std::uint32_t>(kObject + 0x128, 0xA4000004);
    std::uint32_t out = 0;
    if (!Need(ReadTitleSelectedFullIdAdapter12004(&f.access, kTitle, out)
              && out == 0xA4000004 && !f.ReadAt(kTitle + 0x128)
              && !f.ReadAt(kObject + 0x1C0), failure,
              "zero flag exact Title callback preserves selected output and parent boundary")) return false;
  }
  for (bool nonzero : {true, false}) {
    Fixture f;
    const std::uint32_t requested = 0x82000003;
    f.Direct(nonzero, requested);
    f.Put<std::uint32_t>(kObject + (nonzero ? 0x18 : 0x10), requested ^ 0x01000000U);
    if (nonzero) {
      f.Put<std::uintptr_t>(kFallback + 0x1C0, kFallbackLink);
      f.Put<std::uint32_t>(kFallbackLink + 0x1B8, 0xB2000005);
    } else f.Put<std::uint32_t>(kFallback + 0x128, 0xB2000005);
    std::uint32_t out = 0;
    TitleSelectedFullIdSource12004 source;
    if (!Need(ReadTitleSelectedFullId12004(f.access, kTitle, out, &source)
              && out == 0xB2000005 && source.used_fallback == true
              && source.selected_object_identity == kFallback,
              failure, "same low24 index with different generation uses exact branch fallback")) return false;
  }
  for (bool nonzero : {true, false}) {
    Fixture f;
    f.Put<std::uint8_t>(kTitle + 0x130, nonzero ? 1 : 0);
    f.Put<std::uintptr_t>(kBase + (nonzero ? 0x5C67568 : 0x5D1DAF8), 0);
    f.Put<std::uintptr_t>(kBase + (nonzero ? 0x5C67570 : 0x5D1DAE0), kFallback);
    if (nonzero) {
      f.Put<std::uintptr_t>(kFallback + 0x1C0, kFallbackLink);
      f.Put<std::uint32_t>(kFallbackLink + 0x1B8, 0xCE000005);
    } else f.Put<std::uint32_t>(kFallback + 0x128, 0xCE000005);
    std::uint32_t out = 0;
    TitleSelectedFullIdSource12004 source;
    if (!Need(ReadTitleSelectedFullId12004(f.access, kTitle, out, &source)
              && out == 0xCE000005 && source.used_fallback == true
              && !source.requested_full_id && !f.ReadAt(kTitle + (nonzero ? 0x128 : 0x12C)),
              failure, "registry-null native path does not query unused originalTitle FullID")) return false;
  }
  {
    Fixture f;
    f.Direct(true, 0x93000003);
    f.Put<std::uintptr_t>(kObject + 0x1C0, 0);
    std::uint32_t out = 0;
    TitleSelectedFullIdSource12004 source;
    if (!Need(ReadTitleSelectedFullId12004(f.access, kTitle, out, &source)
              && out == UINT32_MAX && source.source_complete
              && source.selected_link_identity == 0,
              failure, "null linked object yields complete native sentinel without parent substitution")) return false;
  }
  for (bool nonzero : {true, false}) {
    Fixture f;
    f.Direct(nonzero, 0x93000003);
    if (nonzero) {
      f.Put<std::uintptr_t>(kObject + 0x1C0, kLink);
      f.Put<std::uint32_t>(kLink + 0x1B8, UINT32_MAX);
    } else f.Put<std::uint32_t>(kObject + 0x128, UINT32_MAX);
    std::uint32_t out = 0;
    if (!Need(ReadTitleSelectedFullId12004(f.access, kTitle, out) && out == UINT32_MAX,
              failure, "raw source field sentinel remains a successful full32 result")) return false;
  }
  {
    Fixture f;
    f.Direct(true, 0xA3000003);
    for (std::size_t i = 0; i < 4; ++i) f.memory.erase(kObject + 0x18 + i);
    f.Put<std::uintptr_t>(kFallback + 0x1C0, kFallbackLink);
    f.Put<std::uint32_t>(kFallbackLink + 0x1B8, 0xB4000004);
    std::uint32_t out = 0x12345678;
    TitleSelectedFullIdSource12004 source;
    if (!Need(!ReadTitleSelectedFullId12004(f.access, kTitle, out, &source)
              && out == 0x12345678 && !source.source_complete
              && !f.ReadAt(kBase + 0x5C67570), failure,
              "uncaptured selected generation cannot manufacture fallback or sentinel")) return false;
  }
  return true;
}
