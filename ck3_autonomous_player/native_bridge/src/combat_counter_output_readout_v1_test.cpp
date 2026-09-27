#include "xar_bridge/combat_counter_output_readout_v1.hpp"

#include <array>
#include <cstdint>
#include <iostream>

using xar::ck3_11906::CombatCounterOutputReadoutV1;
using xar::ck3_11906::ReadCombatCounterOutputV1;

namespace {
struct Header {
  const std::int64_t *data = nullptr;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
};
static_assert(sizeof(Header) == 16);

int Fail(const char *why) {
  std::cerr << why << '\n';
  return 1;
}
} // namespace

int main() {
  const std::array<std::int64_t, 3> values{100'000, 75'000, 0};
  Header header{values.data(), 3, 3};
  CombatCounterOutputReadoutV1 output{};
  if (!ReadCombatCounterOutputV1(&header, 3, output) ||
      output.class_count != 3 || output.capacity != 3 ||
      output.retention_raw[0] != 100'000 ||
      output.retention_raw[1] != 75'000 ||
      output.retention_raw[2] != 0) {
    return Fail("valid original output header was not copied");
  }
  if (ReadCombatCounterOutputV1(&header, 4, output) || output.class_count != 0) {
    return Fail("wrong expected class count was accepted");
  }
  header.capacity = 2;
  if (ReadCombatCounterOutputV1(&header, 3, output)) {
    return Fail("count larger than capacity was accepted");
  }
  header = {nullptr, 3, 3};
  if (ReadCombatCounterOutputV1(&header, 3, output)) {
    return Fail("null vector was accepted");
  }
  header = {values.data(), 4'097, 3};
  if (ReadCombatCounterOutputV1(&header, 3, output)) {
    return Fail("unbounded capacity was accepted");
  }
#if defined(_MSC_VER)
  header = {reinterpret_cast<const std::int64_t *>(1), 3, 3};
  if (ReadCombatCounterOutputV1(&header, 3, output) || output.class_count != 0) {
    return Fail("unreadable native pointer was accepted");
  }
#endif
  std::cout << "combat_counter_output_readout_v1_test: ok\n";
  return 0;
}
