#pragma once

#include <cstddef>
#include <cstdint>
#include <limits>

namespace xar::ck3_12004::piety_price_raw_inputs {

// Source-owned readonly math projections share one memory access ABI.
// Unchanged snapshot revision is a full64 reader argument, not an access gate.
struct PietyPriceNumericAccess12004 {
  std::uintptr_t module_base = 0;
  void *context = nullptr;
  bool (*guarded_read)(void *, const void *, void *, std::size_t) noexcept = nullptr;
  bool exact_12004_bound = false;
};

template<class T>
inline bool ReadPietyPriceNumericField12004(
    const PietyPriceNumericAccess12004 &access, std::uintptr_t object,
    std::size_t offset, T &out) noexcept {
  if (!access.exact_12004_bound || !access.guarded_read || !object ||
      offset > (std::numeric_limits<std::uintptr_t>::max)() - object) return false;
  const auto address = object + offset;
  if (sizeof(T) - 1 >
      (std::numeric_limits<std::uintptr_t>::max)() - address) return false;
  return access.guarded_read(access.context,
      reinterpret_cast<const void *>(address), &out, sizeof(out));
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
