#include "xar_bridge/pointer_key_predicate_31c1d10_12004.hpp"

#include <limits>

namespace xar::ck3_12004::construction_owner_mode3 {
namespace {

std::int32_t Signed32(std::uint32_t bits) noexcept {
  return bits < 0x80000000u ? static_cast<std::int32_t>(bits)
      : static_cast<std::int32_t>(static_cast<std::int64_t>(bits) - 0x100000000LL);
}

std::uint32_t PointerHash(std::uintptr_t key) noexcept {
  std::uint32_t hash = 0x811C9DC5u;
  const auto bits = static_cast<std::uint64_t>(key);
  for (unsigned index = 0; index != 8; ++index) {
    hash ^= static_cast<std::uint32_t>((bits >> (index * 8)) & 0xFFu);
    hash *= 0x01000193u;
  }
  return hash;
}

// Native arithmetic is signed-index addressing with 64-bit wrap. A wrapped or
// unrepresentable observer address stays unknown; negative in-range indices
// remain supported. This is not an extra AL branch or a table-layout rule.
bool SlotAddress(std::uintptr_t entries, std::int64_t index,
                 std::uintptr_t &address) noexcept {
  if (entries == 0) return false;
  constexpr auto maximum = std::numeric_limits<std::uintptr_t>::max();
  const auto magnitude = index < 0 ? 0ULL - static_cast<std::uint64_t>(index)
                                   : static_cast<std::uint64_t>(index);
  if (magnitude > maximum / 16) return false;
  const auto offset = static_cast<std::uintptr_t>(magnitude * 16);
  if (index < 0) {
    if (offset >= entries) return false;
    address = entries - offset;
  } else {
    if (offset > maximum - entries) return false;
    address = entries + offset;
  }
  return true;
}

template<class T>
bool Copy(const RawReceiverAccessV1 &access, std::uintptr_t base,
          std::size_t offset, T &value) noexcept {
  std::uintptr_t address = 0;
  return RawReceiverAddV1(base, offset, address) &&
      sizeof(T) - 1 <= std::numeric_limits<std::uintptr_t>::max() - address &&
      RawReceiverReadV1(access, base, offset, value);
}

} // namespace

PointerKeyPredicate31C1D10V1 ReadPointerKeyPredicate31C1D10V1(
    const RawReceiverAccessV1 &access, std::uintptr_t singleton,
    std::uintptr_t first_pointer, std::size_t maximum_probe_records) noexcept {
  static_assert(sizeof(std::uintptr_t) == 8, "actual31C1D10 consumes all8 pointer bytes");
  PointerKeyPredicate31C1D10V1 result;
  result.singleton_pointer = singleton;
  result.copied_first_pointer = first_pointer;
  result.maximum_probe_records = maximum_probe_records;
  const auto fail = [&](PointerKeyPredicateFailureV1 failure) {
    result.failure = failure;
    return result;
  };
  if (!access.exact_12004_bound) return fail(PointerKeyPredicateFailureV1::exact_build);
  if (access.read_memory == nullptr) return fail(PointerKeyPredicateFailureV1::read_callback);
  const auto hash = PointerHash(first_pointer);
  result.pointer_hash_raw_u32 = hash;
  std::uintptr_t entries = 0;
  if (!Copy(access, singleton, 0xF08, entries)) return fail(PointerKeyPredicateFailureV1::entries_pointer);
  result.entries_pointer = entries;
  std::int32_t mask = 0;
  if (!Copy(access, singleton, 0xF14, mask)) return fail(PointerKeyPredicateFailureV1::mask);
  result.mask_raw_i32 = mask;
  const std::int64_t initial = static_cast<std::int64_t>(Signed32(hash)) &
                              static_cast<std::int64_t>(mask);
  result.initial_slot_index_i64 = initial;
  std::uintptr_t record = 0;
  if (!SlotAddress(entries, initial, record)) return fail(PointerKeyPredicateFailureV1::address_unrepresentable);
  std::uint8_t control = 0;
  if (!Copy(access, record, 4, control)) return fail(PointerKeyPredicateFailureV1::probe_control);
  std::uint8_t distance = 1;
  result.probe_distance_raw_u8 = distance;
  bool matched = false;
  if (control >= distance) {
    for (;;) {
      if (result.copied_probe_key_count >= maximum_probe_records)
        return fail(PointerKeyPredicateFailureV1::probe_budget);
      std::uintptr_t stored_key = 0;
      if (!Copy(access, record, 8, stored_key)) return fail(PointerKeyPredicateFailureV1::probe_key);
      ++result.copied_probe_key_count;
      if (stored_key == first_pointer) {
        matched = true;
        break;
      }
      std::uintptr_t next_record = 0;
      if (!RawReceiverAddV1(record, 16, next_record))
        return fail(PointerKeyPredicateFailureV1::address_unrepresentable);
      record = next_record;
      distance = static_cast<std::uint8_t>(static_cast<unsigned>(distance) + 1u);
      result.probe_distance_raw_u8 = distance;
      if (!Copy(access, record, 4, control)) return fail(PointerKeyPredicateFailureV1::probe_control);
      if (distance > control) break;
    }
  }
  if (matched) {
    result.path = PointerKeyPredicatePathV1::copied_key_match;
  } else {
    std::uint8_t tail = 0;
    if (!Copy(access, singleton, 0xF18, tail)) return fail(PointerKeyPredicateFailureV1::end_tail);
    result.end_tail_raw_u8 = tail;
    const auto end = Signed32(static_cast<std::uint32_t>(mask) + static_cast<std::uint32_t>(tail) + 1u);
    result.end_slot_index_i32 = end;
    if (!SlotAddress(entries, end, record)) return fail(PointerKeyPredicateFailureV1::address_unrepresentable);
    result.path = PointerKeyPredicatePathV1::copied_end_record;
  }
  result.selected_record_pointer = record;
  // DF6 rereads this byte after selecting either a matched or an end record.
  if (!Copy(access, record, 4, control)) return fail(PointerKeyPredicateFailureV1::selected_control);
  result.selected_control_raw_u8 = control;
  result.value = control != 0xFFu;
  return result;
}

} // namespace xar::ck3_12004::construction_owner_mode3
