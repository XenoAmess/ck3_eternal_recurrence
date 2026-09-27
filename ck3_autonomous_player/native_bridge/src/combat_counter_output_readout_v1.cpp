#include "xar_bridge/combat_counter_output_readout_v1.hpp"

#include <cstring>
#if defined(_MSC_VER)
#include <windows.h>
#endif

namespace xar::ck3_11906 {

namespace {
struct NativeHeader {
  const std::int64_t *data = nullptr;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
};
static_assert(sizeof(NativeHeader) == 16);
} // namespace

bool ReadCombatCounterOutputV1(
    const void *native_header, std::int32_t expected_class_count,
    CombatCounterOutputReadoutV1 &output) noexcept {
  output = {};
  if (native_header == nullptr || expected_class_count <= 0 ||
      expected_class_count >
          static_cast<std::int32_t>(kCombatCounterOutputMaximumClassesV1)) {
    return false;
  }
  NativeHeader before{};
  NativeHeader after{};
  bool copied = false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&before, native_header, sizeof(before));
    if (before.data != nullptr && before.count == expected_class_count &&
        before.capacity >= before.count &&
        before.capacity <=
            static_cast<std::int32_t>(kCombatCounterOutputMaximumClassesV1)) {
      std::memcpy(output.retention_raw.data(), before.data,
                  static_cast<std::size_t>(before.count) * sizeof(std::int64_t));
      std::memcpy(&after, native_header, sizeof(after));
      copied = before.data == after.data &&
               before.capacity == after.capacity &&
               before.count == after.count;
    }
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    copied = false;
  }
#endif
  if (!copied) {
    output = {};
    return false;
  }
  output.class_count = before.count;
  output.capacity = before.capacity;
  return true;
}

} // namespace xar::ck3_11906
