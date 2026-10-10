#include "xar_bridge/construction_numeric_child_24cef10_12004.hpp"

#include <cstring>
#include <map>
#include <set>
#include <stdexcept>
#include <utility>
#include <vector>

namespace xar::ck3_12004::construction_owner_mode3 {
namespace {

constexpr std::uintptr_t kImage = 0x10000000;
constexpr std::uintptr_t kReceiver = 0x210000;
constexpr std::uintptr_t kRegistry1 = 0x220000;
constexpr std::uintptr_t kSlots1 = 0x230000;
constexpr std::uintptr_t kObject1 = 0x240000;
constexpr std::uintptr_t kRegistry2 = 0x250000;
constexpr std::uintptr_t kSlots2 = 0x260000;
constexpr std::uintptr_t kObject2 = 0x270000;
constexpr std::uintptr_t kContext = 0x280000;
constexpr std::uintptr_t kReturned = 0x290000;
constexpr std::uintptr_t kFallback1 = 0x2A0000;
constexpr std::uintptr_t kFallback2 = 0x2B0000;
constexpr std::uintptr_t kFallbackContext = 0x2C0000;
constexpr std::uintptr_t kFallbackReturned = 0x2D0000;
constexpr std::uint64_t kFrame = 91;

void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

struct Memory {
  std::map<std::uintptr_t, std::uint8_t> bytes;
  std::set<std::uintptr_t> blocked;
  std::vector<std::pair<std::uintptr_t, std::size_t>> reads;
  bool change_flags_on_second_read = false;
  unsigned flags_reads = 0;

  template <typename T> void Set(std::uintptr_t address, T value) {
    const auto *raw = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t i = 0; i < sizeof(T); ++i) bytes[address + i] = raw[i];
  }
  void Block(std::uintptr_t address, std::size_t size) {
    for (std::size_t i = 0; i < size; ++i) blocked.insert(address + i);
  }
  bool Read(std::uintptr_t address, void *out, std::size_t size) {
    reads.emplace_back(address, size);
    if (address == kReturned + 0x40 && ++flags_reads == 2 &&
        change_flags_on_second_read)
      Set<std::uint64_t>(kReturned + 0x40, 0);
    for (std::size_t i = 0; i < size; ++i)
      if (blocked.count(address + i) || !bytes.count(address + i)) return false;
    auto *raw = static_cast<std::uint8_t *>(out);
    for (std::size_t i = 0; i < size; ++i) raw[i] = bytes.at(address + i);
    return true;
  }
  bool WasRead(std::uintptr_t address) const {
    for (const auto &read : reads) if (read.first == address) return true;
    return false;
  }
};

bool ReadMemory(void *context, const void *address, void *out, std::size_t bytes) {
  return static_cast<Memory *>(context)->Read(
      reinterpret_cast<std::uintptr_t>(address), out, bytes);
}

Memory DirectSource() {
  Memory m;
  m.Set<std::uintptr_t>(kImage + 0x5D1DAF8, kRegistry1);
  m.Set<std::uintptr_t>(kImage + 0x5D1DAE0, kFallback1);
  m.Set<std::uintptr_t>(kImage + 0x5C67568, kRegistry2);
  m.Set<std::uintptr_t>(kImage + 0x5C67570, kFallback2);
  m.Set<std::uintptr_t>(kImage + 0x5D1E2A8, kFallbackReturned);
  m.Set<std::uint32_t>(kReceiver + 0x18, 0xCD000001U);
  m.Set<std::uint32_t>(kRegistry1 + 0x2C, 2);
  m.Set<std::uintptr_t>(kRegistry1 + 0x20, kSlots1);
  m.Set<std::uintptr_t>(kSlots1 + 16 + 8, kObject1);
  m.Set<std::uint32_t>(kObject1 + 0x10, 0xCD000001U);
  m.Set<std::uint32_t>(kObject1 + 0x128, 0xAB000002U);
  m.Set<std::uint32_t>(kRegistry2 + 0x2C, 3);
  m.Set<std::uintptr_t>(kRegistry2 + 0x20, kSlots2);
  m.Set<std::uintptr_t>(kSlots2 + 32 + 8, kObject2);
  m.Set<std::uint32_t>(kObject2 + 0x18, 0xAB000002U);
  m.Set<std::uint32_t>(kObject2 + 0x1C, 0x43686172U);
  m.Set<std::uintptr_t>(kObject2 + 0x1D0, kContext);
  m.Set<std::uintptr_t>(kContext + 0x88, kReturned);
  m.Set<std::uint64_t>(kReturned + 0x40, 1ULL << 35);
  m.Set<std::uint32_t>(kReceiver + 0x38C, 0x80000001U);
  m.Set<std::uint32_t>(kFallback1 + 0x128, 0xEF000004U);
  m.Set<std::uint32_t>(kFallback2 + 0x18, 0xEF000004U);
  m.Set<std::uint32_t>(kFallback2 + 0x1C, 0x43686172U);
  m.Set<std::uintptr_t>(kFallback2 + 0x1D0, kFallbackContext);
  m.Set<std::uintptr_t>(kFallbackContext + 0x88, kFallbackReturned);
  m.Set<std::uint64_t>(kFallbackReturned + 0x40, 0);
  // No4D6 bytes exist. Successful24 source must not depend on that selector.
  return m;
}

ConstructionNumericChild24CEF10ObservationV1 Read(
    Memory &m, std::uintptr_t receiver = kReceiver) {
  const LoadedInputAccessV1 access{&m, &ReadMemory, true};
  return ReadConstructionNumericChild24CEF10V1(access, kImage, receiver, kFrame);
}

} // namespace

// Export only.03/10 calls this in its single fresh owned source compound.
// No standalone main, native invocation, build driver or runtime credit.
void VerifyConstructionNumericChild24CEF10OwnedCases12004() {
  {
    auto m = DirectSource();
    const auto out = Read(m);
    Require(out.observed && out.receiver_pointer == kReceiver && out.frame_key == kFrame &&
                out.source_pin == kConstructionNumeric24CEF10SourcePin12004 &&
                out.eax_raw_u32 == 0x80000001U && out.eax_signed_i32 == -2147483647 &&
                out.gate_bit35 == true && !out.actual_original_consumed_values,
            "24 direct source lost signed EAX/receiver/frame/provenance");
    Require(out.first_resolution.requested_full_id_u32 == 0xCD000001U &&
                out.second_resolution.requested_full_id_u32 == 0xAB000002U &&
                out.returned_object_source.input_receiver == kObject2 &&
                !m.WasRead(kReturned + 0x4D6),
            "24 borrowed another receiver or unrelated selector gate");
  }
  {
    auto m = DirectSource();
    m.Set<std::uint64_t>(kReturned + 0x40, 0);
    m.Block(kReceiver + 0x38C, 4);
    const auto out = Read(m);
    Require(out.observed && out.gate_bit35 == false && out.eax_raw_u32 == std::uint32_t{0} &&
                out.eax_signed_i32 == 0 && !m.WasRead(kReceiver + 0x38C),
            "24 clear bit invented a38C read or lost observed zero");
  }
  {
    auto m = DirectSource();
    m.Set<std::uint32_t>(kObject1 + 0x10, 0xCE000001U);
    const auto out = Read(m);
    Require(out.observed && out.first_resolution.used_fallback &&
                out.first_resolution.candidate_full_id_u32 == 0xCE000001U &&
                out.second_resolution.used_fallback && out.eax_raw_u32 == std::uint32_t{0},
            "24 first full generation mismatch joined masked ID");
  }
  {
    auto m = DirectSource();
    m.Set<std::uint32_t>(kObject2 + 0x18, 0xAC000002U);
    const auto out = Read(m);
    Require(out.observed && !out.first_resolution.used_fallback &&
                out.second_resolution.used_fallback && out.eax_raw_u32 == std::uint32_t{0} &&
                out.returned_object_source.input_receiver == kFallback2,
            "24 second full generation mismatch bypassed actual fallback");
  }
  {
    auto m = DirectSource();
    m.Set<std::uint32_t>(kReceiver + 0x18, 0xFFFFFFFFU);
    m.Set<std::uint32_t>(kRegistry1 + 0x2C, 0xFFFFFFFFU);
    m.Set<std::uintptr_t>(kSlots1 + static_cast<std::uintptr_t>(0xFFFFFF) * 16 + 8, kObject1);
    m.Set<std::uint32_t>(kObject1 + 0x10, 0xFFFFFFFFU);
    const auto out = Read(m);
    Require(out.observed && !out.first_resolution.used_fallback &&
                out.first_resolution.registry_count_u32 == 0xFFFFFFFFU &&
                out.eax_raw_u32 == 0x80000001U,
            "24 invented signed count or sentinel branch absent from source");
  }
  {
    auto m = DirectSource();
    m.Set<std::uintptr_t>(kImage + 0x5D1DAF8, 0);
    m.Set<std::uintptr_t>(kImage + 0x5D1DAE0, 0);
    m.Set<std::uintptr_t>(kImage + 0x5C67568, 0);
    const auto out = Read(m, 0);
    Require(out.observed && out.receiver_pointer == 0 && out.eax_raw_u32 == std::uint32_t{0} &&
                !out.first_resolution.requested_full_id_u32 &&
                !out.second_resolution.requested_full_id_u32 &&
                out.returned_object_source.input_receiver == kFallback2 &&
                !m.WasRead(0x18) && !m.WasRead(0x128) && !m.WasRead(0x38C),
            "24 lazy null roots invented required receiver reads");
  }
  {
    auto m = DirectSource();
    m.Block(kReturned + 0x40, 8);
    const auto out = Read(m);
    Require(!out.observed && out.failure == Numeric24CEF10FailureV1::flags_read &&
                !out.eax_raw_u32 && !m.WasRead(kReceiver + 0x38C),
            "24 missing actual gate became zero/positive input");
  }
  {
    auto m = DirectSource();
    m.Block(kReceiver + 0x38C, 4);
    const auto out = Read(m);
    Require(!out.observed && out.failure == Numeric24CEF10FailureV1::value_read &&
                out.gate_bit35 == true && !out.eax_raw_u32,
            "24 unread selected operand became completed zero");
  }
  {
    auto m = DirectSource();
    m.change_flags_on_second_read = true;
    const auto out = Read(m);
    Require(!out.observed && out.failure == Numeric24CEF10FailureV1::source_changed &&
                !out.actual_original_consumed_values,
            "24 changed source bookend obtained original-consumed credit");
  }
}

} // namespace xar::ck3_12004::construction_owner_mode3
