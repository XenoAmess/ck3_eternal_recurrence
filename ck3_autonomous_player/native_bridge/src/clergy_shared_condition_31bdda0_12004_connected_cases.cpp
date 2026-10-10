#include "xar_bridge/clergy_shared_condition_31bdda0_12004.hpp"

#include <array>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <utility>
#include <vector>

namespace xar::ck3_12004::religion::clergy {
namespace {
void Require(bool condition, const char *reason) {
  if (!condition) throw std::runtime_error(reason);
}

struct OwnedMemory {
  static constexpr std::uintptr_t base = 0x10000;
  std::array<std::uint8_t, 0x400> bytes{};
  std::vector<std::pair<std::uintptr_t, std::size_t>> reads;
  std::optional<std::uintptr_t> unread;

  template <typename T> void Put(std::uintptr_t offset, T value) {
    std::memcpy(bytes.data() + offset, &value, sizeof(value));
  }
  static bool Copy(void *context, const void *address, void *out, std::size_t size) noexcept {
    auto &self = *static_cast<OwnedMemory *>(context);
    auto raw = reinterpret_cast<std::uintptr_t>(address);
    self.reads.emplace_back(raw, size);
    if (self.unread && *self.unread == raw) return false;
    if (raw < base || raw - base > self.bytes.size() ||
        size > self.bytes.size() - (raw - base)) return false;
    std::memcpy(out, self.bytes.data() + (raw - base), size);
    return true;
  }
};
constexpr auto byte_ptr = OwnedMemory::base + 0x100;
constexpr auto support_ptr = OwnedMemory::base + 0x200;
} // namespace

// New guard/width/rawbyte cases for26/10's unique fresh connected compound.
// No main and no native execution. Nine distinct cases; old20 QA is absent.
void VerifyClergyShared31BDDA0ConnectedCases12004() {
  {
    OwnedMemory memory;
    memory.Put<std::uint8_t>(0x100, 255);
    auto result = ReadClergyShared31BDDA0RawAL12004(&memory, OwnedMemory::Copy,
        0xFFFFFFFFU, byte_ptr, std::numeric_limits<std::uintptr_t>::max());
    Require(result.source_ready && result.raw_al == 255, "20f case1 preserves raw255");
    Require(result.rcx_raw_u32 == 0xFFFFFFFFU && result.rdx_identity == byte_ptr,
        "20f case1 preserves literal identity and raw32");
    Require(!result.r8_4c_raw_u32 && !result.condition_child_required,
        "20f case1 skips support and condition child");
    Require(memory.reads.size() == 1 && memory.reads[0].second == 1,
        "20f case1 reads one byte only");
  }
  {
    OwnedMemory memory;
    memory.Put<std::uint8_t>(0x100, 2);
    auto result = ReadClergyShared31BDDA0RawAL12004(&memory, OwnedMemory::Copy,
        0, byte_ptr, 0);
    Require(result.source_ready && result.raw_al == 2, "20f case2 preserves raw2");
    Require(memory.reads.size() == 1, "20f case2 does not demand null support");
  }
  {
    OwnedMemory memory;
    memory.Put<std::uint32_t>(0x24C, 0);
    memory.Put<std::uint32_t>(0x250, 0xFFFFFFFFU);
    auto result = ReadClergyShared31BDDA0RawAL12004(&memory, OwnedMemory::Copy,
        42, byte_ptr, support_ptr);
    Require(result.source_ready && result.raw_al == 0, "20f case3 known zero remains available");
    Require(result.r8_4c_raw_u32 == std::uint32_t{0} && !result.condition_child_required,
        "20f case3 zero DWORD skips child");
    Require(memory.reads.size() == 2 && memory.reads[1].first == support_ptr + 0x4C,
        "20f case3 demands exact support operand");
    Require(memory.reads[1].second == 4, "20f case3 reads exactly four bytes");
  }
  {
    OwnedMemory memory;
    memory.Put<std::uint32_t>(0x24C, 0x01000000U);
    auto result = ReadClergyShared31BDDA0RawAL12004(&memory, OwnedMemory::Copy,
        42, byte_ptr, support_ptr);
    Require(!result.source_ready && !result.raw_al && result.condition_child_required,
        "20f case4 preserves required missing condition");
    Require(result.r8_4c_raw_u32 == 0x01000000U, "20f case4 reads high DWORD byte");
    Require(result.unavailable_reason == "condition_372df10_source_pending",
        "20f case4 reports dynamic source frontier");
  }
  {
    OwnedMemory memory;
    memory.unread = byte_ptr;
    auto result = ReadClergyShared31BDDA0RawAL12004(&memory, OwnedMemory::Copy,
        42, byte_ptr, support_ptr);
    Require(!result.source_ready && !result.raw_al && !result.rdx_raw_u8,
        "20f case5 unread byte is unavailable");
    Require(!result.r8_4c_raw_u32 && memory.reads.size() == 1,
        "20f case5 unread byte does not demand support");
    Require(result.unavailable_reason == "literal_rdx_byte_unread",
        "20f case5 preserves unread reason");
  }
  {
    OwnedMemory memory;
    memory.unread = support_ptr + 0x4C;
    auto result = ReadClergyShared31BDDA0RawAL12004(&memory, OwnedMemory::Copy,
        42, byte_ptr, support_ptr);
    Require(!result.source_ready && !result.raw_al && result.rdx_raw_u8 == 0,
        "20f case6 unread DWORD is not false");
    Require(!result.r8_4c_raw_u32 && memory.reads.size() == 2,
        "20f case6 records mandatory DWORD read");
  }
  {
    OwnedMemory memory;
    auto result = ReadClergyShared31BDDA0RawAL12004(&memory, OwnedMemory::Copy,
        42, byte_ptr, std::numeric_limits<std::uintptr_t>::max() - 0x4B);
    Require(!result.source_ready && !result.raw_al && memory.reads.size() == 1,
        "20f case7 rejects offset addition overflow before copy");
  }
  {
    OwnedMemory memory;
    auto result = ReadClergyShared31BDDA0RawAL12004(&memory, OwnedMemory::Copy,
        42, byte_ptr, std::numeric_limits<std::uintptr_t>::max() - 0x4D);
    Require(!result.source_ready && !result.raw_al && memory.reads.size() == 1,
        "20f case8 rejects read width overflow before copy");
  }
  {
    auto result = ReadClergyShared31BDDA0RawAL12004(nullptr, nullptr,
        42, byte_ptr, support_ptr);
    Require(!result.source_ready && !result.raw_al && !result.rdx_raw_u8,
        "20f case9 absent callback has no fallback");
  }
}
} // namespace xar::ck3_12004::religion::clergy
