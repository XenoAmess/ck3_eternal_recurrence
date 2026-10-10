#include "xar_bridge/construction_scaled_key_2c4d530_12004.hpp"
#include "xar_bridge/construction_scaled_key_2c4d530_12004_focus.hpp"

#include <array>
#include <cstring>
#include <stdexcept>

namespace xar::ck3_12004::construction_owner_mode3 {
namespace {
void Check(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
struct Memory {
  std::array<std::byte, 0x100> collection{};
  std::array<std::uint16_t, 5> keys{0x46, 0xA2, 0xA2, 0xA4, 0x1EA};
  std::array<std::int64_t, 5> values{300001, -200003, 99000000, 400000, -700000};
  std::size_t reads = 0;
  std::uintptr_t denied = 0;
  template<class T> void Put(std::size_t offset, T value) {
    std::memcpy(collection.data() + offset, &value, sizeof value);
  }
  Memory() {
    Put(0x68, reinterpret_cast<std::uintptr_t>(keys.data()));
    Put(0x74, std::int32_t{5});
    Put(0xD0, reinterpret_cast<std::uintptr_t>(values.data()));
  }
  std::uintptr_t Address() const { return reinterpret_cast<std::uintptr_t>(collection.data()); }
  static bool Read(void *context, const void *address, void *out, std::size_t size) {
    auto &m = *static_cast<Memory *>(context);
    ++m.reads;
    const auto incoming = reinterpret_cast<std::uintptr_t>(address);
    if (incoming == m.denied) return false;
    const auto contains = [&](const auto &storage) {
      const auto begin = reinterpret_cast<std::uintptr_t>(storage.data());
      return incoming >= begin && size <= sizeof(storage) && incoming - begin <= sizeof(storage) - size;
    };
    if (!contains(m.collection) && !contains(m.keys) && !contains(m.values)) return false;
    std::memcpy(out, address, size);
    return true;
  }
  LoadedInputAccessV1 Access() { return {this, &Read, true}; }
};
} // namespace

void RunScaledCollectionKeyFocus12004() {
  Memory memory;
  const auto original_values = memory.values;
  auto result = ReadScaledCollectionKey12004(memory.Access(), memory.Address(), 0x100A2, 150000);
  Check(result.ready && result.property_key_u16 == 0xA2 && result.incoming_key_raw_u32 == std::uint32_t{0x100A2} &&
        result.selected_index_u32 == std::uint32_t{1} && result.selected_value_raw_q64 == -200003 &&
        result.scaled_value_raw_q64 == -300004,
        "actual low16 key / first duplicate / signed scale selected value");
  result = ReadScaledCollectionKey12004(memory.Access(), memory.Address(), 0x46, -200000);
  Check(result.ready && result.selected_value_raw_q64 == 300001 && result.scaled_value_raw_q64 == -600002,
        "actual caller source46 / negative signed fifth factor");
  result = ReadScaledCollectionKey12004(memory.Access(), memory.Address(), 0xA3, 100000);
  Check(result.ready && result.selection == ScaledCollectionKeySelection12004::key_absent &&
        result.scaled_value_raw_q64 == 0 && !result.selected_index_u32,
        "native interior absent key without a mapped value");
  memory.denied = reinterpret_cast<std::uintptr_t>(memory.values.data() + 1);
  result = ReadScaledCollectionKey12004(memory.Access(), memory.Address(), 0xA2, 100000);
  Check(!result.ready && !result.scaled_value_raw_q64 && result.selected_index_u32 == std::uint32_t{1} &&
        result.failure == ScaledCollectionKeyFailure12004::selected_value_read,
        "unread mapped value remains unavailable rather than zero");
  result = ReadScaledCollectionKey12004(memory.Access(), memory.Address(), 0x1EA, 100000);
  Check(result.ready && result.scaled_value_raw_q64 == -700000,
        "later independently readable actual1EA source retained");
  memory.denied = 0;
  const auto reads_before = memory.reads;
  result = ReadScaledCollectionKey12004(memory.Access(), 0, 0xA2, 0, 0x1234, 7);
  Check(result.ready && result.selection == ScaledCollectionKeySelection12004::factor_zero &&
        result.scaled_value_raw_q64 == 0 && !result.selected_value_raw_q64 && memory.reads == reads_before,
        "original fifth-factor zero bypasses PC and detail demands");
  result = ReadScaledCollectionKey12004(memory.Access(), 0, 0x1FFFF, 100000);
  Check(result.ready && result.selection == ScaledCollectionKeySelection12004::key_sentinel &&
        result.scaled_value_raw_q64 == 0 && !result.pc_count_i32 && memory.reads == reads_before,
        "original U16FFFF zero before PC demand");
  memory.Put(0x74, std::int32_t{0});
  memory.denied = memory.Address() + 0x68;
  result = ReadScaledCollectionKey12004(memory.Access(), memory.Address(), 0xA2, 100000);
  Check(result.ready && result.selection == ScaledCollectionKeySelection12004::count_zero &&
        result.scaled_value_raw_q64 == 0, "zero count has no numerical key-array demand");
  memory.Put(0x74, std::int32_t{5});
  memory.denied = 0;
  result = ReadScaledCollectionKey12004(memory.Access(), memory.Address(), 0xA2, 100000, 0x1234);
  Check(!result.ready && !result.scaled_value_raw_q64 &&
        result.failure == ScaledCollectionKeyFailure12004::detail_branch_not_supplied,
        "unclosed formatting branch retains independent unavailable result");
  Check(memory.values == original_values, "read-only source operands changed");
}
} // namespace xar::ck3_12004::construction_owner_mode3
