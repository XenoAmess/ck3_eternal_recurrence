#pragma once
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>

namespace xar::ck3_12004 {
using ArmyRegularCoreReadonlyRead12004 = bool (*)(void *, std::uintptr_t, void *, std::size_t) noexcept;
struct ArmyRegularCoreReadonlyAccess12004 {
  std::uintptr_t image_base = 0;
  void *read_context = nullptr;
  ArmyRegularCoreReadonlyRead12004 read = nullptr;
  std::size_t maximum_occurrences = 65536;
};
struct ArmyRegularCoreReadonlyPredicate12004 {
  std::optional<bool> value;
  std::string unavailable_reason;
};
// This access is a bounded guarded read callback only, never a native getter.
// The owning regular-core collector supplies one shared per-frame read budget.
} // namespace xar::ck3_12004
