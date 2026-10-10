#pragma once

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>

namespace xar::ck3_12004::construction_owner_mode3 {

// Concrete actual source: 2469146..246921B inside the already held 4118B
// 2468DA0 body. This is an unnamed aggregate input, not a building's yield.
struct LoadedInputAccessV1 {
  void *context = nullptr;
  bool (*read_memory)(void *, const void *, void *, std::size_t) = nullptr;
  bool exact_12004_bound = false;
};

enum class LoadedInputFailureV1 : std::uint8_t {
  none,
  exact_build,
  read_callback,
  province_identity,
  context,
  collection,
  key_read,
  value_read,
  source_changed,
};

struct LoadedKey3FInputV1 {
  bool observed = false;
  LoadedInputFailureV1 failure = LoadedInputFailureV1::none;
  std::int32_t province_id = -1;
  std::uintptr_t province_pointer = 0;
  std::uintptr_t slots_pointer = 0;
  std::uintptr_t context_pointer = 0;
  std::uintptr_t collection_pointer = 0;
  std::int32_t key_count = 0;
  bool key_present = false;
  std::int32_t key_index = -1;
  std::int64_t signed_qword_raw = 0;
};

inline bool AddOffsetV1(std::uintptr_t base, std::size_t offset,
                        std::uintptr_t &out) noexcept {
  if (base == 0 || offset >
      std::numeric_limits<std::uintptr_t>::max() - base) return false;
  out = base + offset;
  return true;
}

template <typename T>
inline bool ReadOffsetV1(const LoadedInputAccessV1 &access,
                         std::uintptr_t base, std::size_t offset,
                         T &out) noexcept {
  std::uintptr_t address = 0;
  return access.read_memory != nullptr && AddOffsetV1(base, offset, address) &&
      access.read_memory(access.context,
                         reinterpret_cast<const void *>(address), &out,
                         sizeof(T));
}

inline LoadedKey3FInputV1 ReadLoadedKey3FInputV1(
    const LoadedInputAccessV1 &access, std::uintptr_t province,
    std::int32_t expected_province_id) noexcept {
  LoadedKey3FInputV1 result{};
  result.province_pointer = province;
  result.province_id = expected_province_id;
  const auto fail = [&](LoadedInputFailureV1 failure) {
    result.failure = failure;
    result.observed = false;
    return result;
  };
  if (!access.exact_12004_bound) return fail(LoadedInputFailureV1::exact_build);
  if (access.read_memory == nullptr) return fail(LoadedInputFailureV1::read_callback);
  std::int32_t observed_id = -1;
  if (expected_province_id <= 0 ||
      !ReadOffsetV1(access, province, 0x10, observed_id) ||
      observed_id != expected_province_id)
    return fail(LoadedInputFailureV1::province_identity);
  if (!AddOffsetV1(province, 0x620, result.slots_pointer) ||
      !ReadOffsetV1(access, result.slots_pointer, 0xF0,
                    result.context_pointer) || result.context_pointer == 0)
    return fail(LoadedInputFailureV1::context);
  if (!AddOffsetV1(result.context_pointer, 0x30, result.collection_pointer))
    return fail(LoadedInputFailureV1::collection);
  std::uintptr_t keys = 0;
  if (!ReadOffsetV1(access, result.collection_pointer, 0x68, keys) ||
      !ReadOffsetV1(access, result.collection_pointer, 0x74,
                    result.key_count) || result.key_count < 0 ||
      (result.key_count > 0 && keys == 0))
    return fail(LoadedInputFailureV1::collection);

  // Literal2469160..246917F half/advance loop over uint16 keys. Native
  // advance is remaining-half and the retained count is always half.
  // No scan/export/allocation: signed32 count requires at most31 probes.
  std::int32_t first = 0;
  std::int32_t count = result.key_count;
  while (count > 0) {
    const std::int32_t half = count / 2;
    const std::int32_t middle = first + half;
    std::uint16_t key = 0;
    if (!ReadOffsetV1(access, keys,
                      static_cast<std::size_t>(middle) * sizeof(key), key))
      return fail(LoadedInputFailureV1::key_read);
    if (key < 0x3F) {
      first += count - half;
    }
    count = half;
  }
  std::uintptr_t values = 0;
  if (first < result.key_count) {
    std::uint16_t key = 0;
    if (!ReadOffsetV1(access, keys,
                      static_cast<std::size_t>(first) * sizeof(key), key))
      return fail(LoadedInputFailureV1::key_read);
    // Actual CMP BX,[RAX]/JB treats a selected key<=3F as mapped. Keep the
    // literal comparison; do not impose a sorting/equality admission gate.
    if (!(0x3F < key)) {
      result.key_present = true;
      result.key_index = first;
      if (!ReadOffsetV1(access, result.collection_pointer, 0xD0, values) ||
          values == 0 ||
          !ReadOffsetV1(access, values,
                        static_cast<std::size_t>(first) *
                            sizeof(result.signed_qword_raw),
                        result.signed_qword_raw))
        return fail(LoadedInputFailureV1::value_read);
    }
  }
  // The native absent-key branch contributes zero. Failure to read a
  // present value is a distinct unavailable source, not a zero value.
  std::uintptr_t after_context = 0;
  std::uintptr_t after_keys = 0;
  std::uintptr_t after_values = 0;
  std::int32_t after_count = -1;
  if (!ReadOffsetV1(access, province, 0x10, observed_id) ||
      observed_id != expected_province_id ||
      !ReadOffsetV1(access, result.slots_pointer, 0xF0, after_context) ||
      after_context != result.context_pointer ||
      !ReadOffsetV1(access, result.collection_pointer, 0x68, after_keys) ||
      after_keys != keys ||
      !ReadOffsetV1(access, result.collection_pointer, 0x74, after_count) ||
      after_count != result.key_count ||
      (result.key_present &&
       (!ReadOffsetV1(access, result.collection_pointer, 0xD0, after_values) ||
        after_values != values)))
    return fail(LoadedInputFailureV1::source_changed);
  result.observed = true;
  return result;
}

inline std::int64_t SignedBitsV1(std::uint64_t bits) noexcept {
  std::int64_t value = 0;
  std::memcpy(&value, &bits, sizeof(value));
  return value;
}

inline std::int64_t WrappedProductV1(std::int64_t a,
                                     std::int64_t b) noexcept {
  return SignedBitsV1(static_cast<std::uint64_t>(a) *
                      static_cast<std::uint64_t>(b));
}

// Exact actual fast/slow arithmetic shared by2468DA0, including native
// wrapped signed64 slow intermediates. Division truncates toward zero.
// Keep the caller's factor multiplication order; never algebraically fuse
// operations or reinterpret this as an independently attributed benefit.
inline std::int64_t SignedScaleProduct100000V1(std::int64_t a,
                                               std::int64_t b) noexcept {
  constexpr std::int64_t bound = 0xB504F333;
  constexpr std::int64_t scale = 100000;
  if (a >= -bound && a <= bound && b >= -bound && b <= bound)
    return (a * b) / scale;
  const std::int64_t high = std::max(a, b);
  const std::int64_t low = std::min(a, b);
  const std::int64_t whole = WrappedProductV1(high / scale, low);
  const std::int64_t fraction = WrappedProductV1(high % scale, low) / scale;
  return SignedBitsV1(static_cast<std::uint64_t>(whole) +
                      static_cast<std::uint64_t>(fraction));
}

} // namespace xar::ck3_12004::construction_owner_mode3
