#include "xar_bridge/clergy_position_raw_al_31bde90_12004.hpp"

#include <map>

namespace xar::ck3_12004::religion::clergy {
namespace {
constexpr std::uintptr_t position_byte = 0x1000;
constexpr std::uintptr_t predicate = 0x2000;
struct Fixture {
  std::map<std::uintptr_t, std::uint8_t> bytes;
  std::uint32_t owner = 0xFF000001u;
  std::uint8_t child_raw = 0;
  bool child_ready = false;
  int child_calls = 0, missing_reads = 0;
  template <typename T> void Put(std::uintptr_t address, const T &value) {
    const auto *source = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t i = 0; i < sizeof(value); ++i) bytes[address + i] = source[i];
  }
  static bool Read(void *opaque, const void *address, void *destination,
                   std::size_t size) noexcept {
    auto &f = *static_cast<Fixture *>(opaque);
    const auto base = reinterpret_cast<std::uintptr_t>(address);
    auto *out = static_cast<std::uint8_t *>(destination);
    for (std::size_t i = 0; i < size; ++i) {
      const auto found = f.bytes.find(base + i);
      if (found == f.bytes.end()) { ++f.missing_reads; return false; }
      out[i] = found->second;
    }
    return true;
  }
  static bool Child(void *opaque, ReadMemory read, void *read_context,
                    std::uintptr_t input, std::uint16_t word,
                    std::uint64_t payload, std::uint8_t &out) noexcept {
    auto &f = *static_cast<Fixture *>(opaque);
    ++f.child_calls;
    if (!f.child_ready || read != Read || read_context != &f || input != predicate ||
        word != 4 || payload != static_cast<std::uint64_t>(f.owner)) return false;
    out = f.child_raw;
    return true;
  }
  ClergyPositionRawAlResult12004 Run(bool supply_child = true,
                                    std::uintptr_t tooltip = 0) {
    const ClergyPositionRawAlOperands12004 operands{owner, position_byte, predicate, tooltip};
    return ReadClergyPositionRawAl12004(Read, this, operands,
        supply_child ? ClergyPositionRawAlChildReader12004{this, Child}
                     : ClergyPositionRawAlChildReader12004{});
  }
};
} // namespace

// New06e literal source cases. Synthetic child packets exercise availability
// and exact argument forwarding; they do not qualify372DF10 or889F60. The
// father26 sole current-base compound owns the only execution and main.
// Return failure count:0 means all cases passed.
int RunClergyPositionRawAl31BDE9012004NewCases() {
  int failures = 0;
  const auto require = [&](bool ok) { if (!ok) ++failures; };
  {
    Fixture f; f.Put(position_byte, std::uint8_t{0});
    const auto r = f.Run();
    require(r.raw_al == std::uint8_t{0} &&
            r.branch == ClergyPositionRawAlBranch12004::original_byte_not_one &&
            f.child_calls == 0 && f.missing_reads == 0);
  }
  {
    Fixture f; f.Put(position_byte, std::uint8_t{2});
    const auto r = f.Run();
    require(r.raw_al == std::uint8_t{2} && f.child_calls == 0 && f.missing_reads == 0);
  }
  {
    Fixture f; f.Put(position_byte, std::uint8_t{255});
    const auto r = f.Run();
    require(r.raw_al == std::uint8_t{255} && f.child_calls == 0 && f.missing_reads == 0);
  }
  {
    Fixture f; f.Put(position_byte, std::uint8_t{1}); f.Put(predicate + 0x4C, std::uint32_t{0});
    const auto r = f.Run();
    require(r.raw_al == std::uint8_t{1} &&
            r.branch == ClergyPositionRawAlBranch12004::original_one_zero_4c &&
            f.child_calls == 0);
  }
  {
    Fixture f; f.Put(position_byte, std::uint8_t{1}); f.Put(predicate + 0x4C, std::uint32_t{1});
    const auto r = f.Run(false);
    require(!r.raw_al && r.unavailable == ClergyPositionRawAlUnavailable12004::predicate_source);
  }
  {
    Fixture f; f.Put(position_byte, std::uint8_t{1}); f.Put(predicate + 0x4C, std::uint32_t{1});
    f.child_ready = true; f.child_raw = 0;
    const auto r = f.Run();
    require(r.raw_al == std::uint8_t{0} && f.child_calls == 1 &&
            !r.native_predicate_or_initializer_called);
  }
  {
    Fixture f; f.Put(position_byte, std::uint8_t{1}); f.Put(predicate + 0x4C, std::uint32_t{1});
    f.child_ready = true; f.child_raw = 231;
    const auto r = f.Run();
    require(r.raw_al == std::uint8_t{231} && f.child_calls == 1);
  }
  {
    Fixture f; f.Put(position_byte, std::uint8_t{1});
    const auto r = f.Run();
    require(!r.raw_al && r.unavailable == ClergyPositionRawAlUnavailable12004::predicate_4c &&
            f.child_calls == 0);
  }
  {
    Fixture f; f.Put(position_byte, std::uint8_t{1}); f.Put(predicate + 0x4C, std::uint32_t{0xFFFFFFFFu});
    f.owner = 0xFFFFFFFFu; f.child_ready = true; f.child_raw = 17;
    const auto r = f.Run();
    require(r.raw_al == std::uint8_t{17} && f.child_calls == 1);
  }
  {
    Fixture f; f.Put(position_byte, std::uint8_t{1}); f.Put(predicate + 0x4C, std::uint32_t{1});
    f.child_ready = true;
    const auto r = f.Run(true, 0x1234);
    require(!r.raw_al &&
            r.unavailable == ClergyPositionRawAlUnavailable12004::current_null_tooltip_path &&
            f.child_calls == 0);
  }
  {
    Fixture f;
    const auto r = f.Run();
    require(!r.raw_al && r.unavailable == ClergyPositionRawAlUnavailable12004::position_byte &&
            f.child_calls == 0);
  }
  return failures;
}

} // namespace xar::ck3_12004::religion::clergy
