#include "xar_bridge/construction_scaled_key_2c4d530_12004.hpp"

namespace xar::ck3_12004::construction_owner_mode3 {

ScaledCollectionKey12004 ReadScaledCollectionKey12004(
    const LoadedInputAccessV1 &access, std::uintptr_t collection,
    std::uint32_t raw_key, std::int64_t factor_raw,
    std::uintptr_t detail, std::int32_t selector) {
  ScaledCollectionKey12004 out;
  out.collection_identity = collection;
  out.incoming_key_raw_u32 = raw_key;
  out.property_key_u16 = static_cast<std::uint16_t>(raw_key);
  out.factor_raw_q64 = factor_raw;
  out.detail_identity = detail;
  out.selector_raw_i32 = selector;
  const auto fail = [&](ScaledCollectionKeyFailure12004 failure) {
    out.failure = failure;
    out.ready = false;
    return out;
  };
  const auto finish = [&](ScaledCollectionKeySelection12004 selection,
                          std::int64_t value) {
    out.selection = selection;
    out.selected_value_raw_q64 = value;
    out.scaled_value_raw_q64 = SignedScaleProduct100000V1(value, factor_raw);
    out.ready = true;
    return out;
  };
  if (!access.exact_12004_bound) return fail(ScaledCollectionKeyFailure12004::exact_build);
  if (factor_raw == 0) {
    // There is no selected-value observation on this original early return.
    out.selection = ScaledCollectionKeySelection12004::factor_zero;
    out.scaled_value_raw_q64 = 0;
    out.ready = true;
    return out;
  }
  if (detail != 0) return fail(ScaledCollectionKeyFailure12004::detail_branch_not_supplied);
  if (selector != 0) return fail(ScaledCollectionKeyFailure12004::selector_branch_not_supplied);
  if (out.property_key_u16 == 0xFFFF)
    return finish(ScaledCollectionKeySelection12004::key_sentinel, 0);
  if (access.read_memory == nullptr) return fail(ScaledCollectionKeyFailure12004::read_callback);
  if (!AddOffsetV1(collection, 0x68, out.pc_identity))
    return fail(ScaledCollectionKeyFailure12004::collection);
  std::int32_t count = 0;
  if (!ReadOffsetV1(access, out.pc_identity, 0xC, count))
    return fail(ScaledCollectionKeyFailure12004::count_read);
  out.pc_count_i32 = count;
  if (count < 0) return fail(ScaledCollectionKeyFailure12004::negative_count);
  // A zero count's unused pointer load cannot influence the selected value.
  if (count == 0) return finish(ScaledCollectionKeySelection12004::count_zero, 0);
  std::uintptr_t keys = 0;
  if (!ReadOffsetV1(access, out.pc_identity, 0, keys) || keys == 0)
    return fail(ScaledCollectionKeyFailure12004::keys_read);
  std::uint32_t first = 0;
  std::uint32_t remaining = static_cast<std::uint32_t>(count);
  while (remaining != 0) {
    const auto half = remaining >> 1;
    std::uint16_t key = 0;
    if (!ReadOffsetV1(access, keys, static_cast<std::size_t>(first + half) * 2, key))
      return fail(ScaledCollectionKeyFailure12004::probe_read);
    ++out.binary_probe_count;
    // Actual2303727/3736 advances by remaining-half, then always keeps half.
    if (key < out.property_key_u16) first += remaining - half;
    remaining = half;
  }
  std::uintptr_t values = 0;
  bool mapped = false;
  std::int64_t value = 0;
  if (first != static_cast<std::uint32_t>(count)) {
    std::uint16_t candidate = 0;
    if (!ReadOffsetV1(access, keys, static_cast<std::size_t>(first) * 2, candidate))
      return fail(ScaledCollectionKeyFailure12004::probe_read);
    // Preserve the native unsigned less-than test rather than replacing it
    // with equality, sorting, scanning or a duplicate-key normalization.
    if (!(out.property_key_u16 < candidate)) {
      mapped = true;
      out.selected_index_u32 = first;
      if (!ReadOffsetV1(access, out.pc_identity, 0x68, values) || values == 0)
        return fail(ScaledCollectionKeyFailure12004::values_read);
      if (!ReadOffsetV1(access, values, static_cast<std::size_t>(first) * 8, value))
        return fail(ScaledCollectionKeyFailure12004::selected_value_read);
    }
  }
  std::int32_t after_count = 0;
  std::uintptr_t after_keys = 0, after_values = 0;
  if (!ReadOffsetV1(access, out.pc_identity, 0xC, after_count) || after_count != count ||
      !ReadOffsetV1(access, out.pc_identity, 0, after_keys) || after_keys != keys ||
      (mapped && (!ReadOffsetV1(access, out.pc_identity, 0x68, after_values) || after_values != values)))
    return fail(ScaledCollectionKeyFailure12004::source_changed);
  return finish(mapped ? ScaledCollectionKeySelection12004::mapped
                       : ScaledCollectionKeySelection12004::key_absent, value);
}

} // namespace xar::ck3_12004::construction_owner_mode3
