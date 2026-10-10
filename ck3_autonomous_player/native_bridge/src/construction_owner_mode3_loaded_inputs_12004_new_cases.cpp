#include "xar_bridge/construction_owner_mode3_loaded_inputs_12004.hpp"

#include <array>
#include <cstring>
#include <stdexcept>

namespace {
using namespace xar::ck3_12004::construction_owner_mode3;

struct MemoryFixture {
  std::array<unsigned char, 0x800> province{};
  std::array<unsigned char, 0x200> context{};
  std::array<std::uint16_t, 3> keys{0x20, 0x3F, 0x70};
  std::array<std::int64_t, 3> values{111, -123456, 333};
  bool deny_value = false;
  template <typename T>
  void store(unsigned char *p, std::size_t off, T value) {
    std::memcpy(p + off, &value, sizeof(value));
  }
  MemoryFixture() {
    store(province.data(), 0x10, std::int32_t{2635});
    store(province.data(), 0x710,
          reinterpret_cast<std::uintptr_t>(context.data()));
    store(context.data(), 0x98,
          reinterpret_cast<std::uintptr_t>(keys.data()));
    store(context.data(), 0xA4, std::int32_t{3});
    store(context.data(), 0x100,
          reinterpret_cast<std::uintptr_t>(values.data()));
  }
  static bool contains(std::uintptr_t start, std::size_t capacity,
                        std::uintptr_t address, std::size_t size) {
    return address >= start && size <= capacity &&
        address - start <= capacity - size;
  }
  static bool read(void *opaque, const void *source, void *target,
                    std::size_t size) {
    auto &self = *static_cast<MemoryFixture *>(opaque);
    const auto address = reinterpret_cast<std::uintptr_t>(source);
    const auto value_base = reinterpret_cast<std::uintptr_t>(self.values.data());
    if (self.deny_value && contains(value_base, sizeof(self.values), address, size))
      return false;
    const bool allowed =
        contains(reinterpret_cast<std::uintptr_t>(self.province.data()),
                 self.province.size(), address, size) ||
        contains(reinterpret_cast<std::uintptr_t>(self.context.data()),
                 self.context.size(), address, size) ||
        contains(reinterpret_cast<std::uintptr_t>(self.keys.data()),
                 sizeof(self.keys), address, size) ||
        contains(value_base, sizeof(self.values), address, size);
    if (!allowed) return false;
    std::memcpy(target, source, size);
    return true;
  }
  LoadedInputAccessV1 access() { return {this, read, true}; }
  std::uintptr_t owner() {
    return reinterpret_cast<std::uintptr_t>(province.data());
  }
};

void require(bool value) {
  if (!value) throw std::runtime_error("actual mode3 loaded-input connected case failed");
}
}

// No standalone main and no native calls. Central10 executes this fragment
// once with the other newly composed actual-source leaves.
int RunConstructionOwnerMode3LoadedInputs12004NewCases() {
  int executed = 0;
  {
    MemoryFixture memory;
    const auto raw = ReadLoadedKey3FInputV1(memory.access(), memory.owner(), 2635);
    require(raw.observed && raw.key_present && raw.key_index == 1 &&
            raw.signed_qword_raw == -123456 &&
            raw.context_pointer == reinterpret_cast<std::uintptr_t>(memory.context.data()));
    ++executed;
  }
  {
    MemoryFixture memory;
    memory.keys[1] = 0x40;
    const auto raw = ReadLoadedKey3FInputV1(memory.access(), memory.owner(), 2635);
    require(raw.observed && !raw.key_present && raw.signed_qword_raw == 0);
    ++executed;
  }
  {
    MemoryFixture memory;
    memory.deny_value = true;
    const auto raw = ReadLoadedKey3FInputV1(memory.access(), memory.owner(), 2635);
    require(!raw.observed && raw.failure == LoadedInputFailureV1::value_read);
    ++executed;
  }
  {
    MemoryFixture memory;
    const auto raw = ReadLoadedKey3FInputV1(memory.access(), memory.owner(), 604);
    require(!raw.observed && raw.failure == LoadedInputFailureV1::province_identity);
    ++executed;
  }
  {
    require(SignedScaleProduct100000V1(-123456, 150000) == -185184);
    ++executed;
  }
  {
    // This uses the native slow branch, preserving its operation order.
    require(SignedScaleProduct100000V1(5000000000LL, 100000) == 5000000000LL &&
            SignedScaleProduct100000V1(-5000000000LL, 100000) == -5000000000LL);
    ++executed;
  }
  return executed;
}
