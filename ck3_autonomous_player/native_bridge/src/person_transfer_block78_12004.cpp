#include "xar_bridge/person_transfer_block78_12004.hpp"
#include <utility>

namespace xar::ck3_12004 {
namespace {
bool InRange(std::uintptr_t data, const PersonTransferKeyRange12004 &range) {
  // Literal MOVSXD + LEA*2 and unsigned JA/JB: modulo64 end arithmetic.
  const auto extent = static_cast<std::uintptr_t>(
      static_cast<std::int64_t>(range.element_count_i32)) * std::uintptr_t{2};
  const auto end = range.base_identity + extent;
  return range.base_identity <= data && data < end;
}
bool KeysMatchCount(const PersonTransferKeyStorage12004 &storage) {
  return storage.keys_u16 && storage.count_i32 >= 0 &&
         storage.keys_u16->size() ==
             static_cast<std::size_t>(storage.count_i32);
}
void LogicalCross(PersonTransferBlock78Postimage12004 &out,
                  const PersonTransferKeyStorage12004 &a,
                  const PersonTransferKeyStorage12004 &b) {
  out.after_a_count_i32 = b.count_i32;
  out.after_b_count_i32 = a.count_i32;
  out.after_a_keys_u16 = b.keys_u16;
  out.after_b_keys_u16 = a.keys_u16;
  out.key_elements_ready = KeysMatchCount(a) && KeysMatchCount(b);
}
} // namespace

PersonTransferBlock78Postimage12004
EvaluatePersonTransferBlock78Postimage12004(
    const PersonTransferBlock78Input12004 &input) {
  PersonTransferBlock78Postimage12004 out;
  out.a_allocator_receiver_identity = input.a.storage_identity + 0x18;
  out.b_allocator_receiver_identity = input.b.storage_identity + 0x18;
  if (!input.initial_a_range) {
    out.reason = "initial_a_slot28_response_unread";
    return out;
  }
  bool either_inline = InRange(input.a.data_identity, *input.initial_a_range);
  if (!either_inline) {
    if (!input.initial_b_range) {
      out.reason = "initial_b_slot28_response_unread";
      return out;
    }
    either_inline = InRange(input.b.data_identity, *input.initial_b_range);
  }
  if (input.a.capacity_i32 >= input.b.count_i32 &&
      input.b.capacity_i32 >= input.a.count_i32 && either_inline) {
    out.path = PersonTransferBlock78Path12004::element_swap;
    out.demanded_callees.push_back(0x17140D0);
    // Complete17140D0 plus actual byte-swap primitive and retained byte-copy:
    // common prefix exchange, longer tail copy, then count swap. Each side
    // keeps its physical data/capacity rather than exchanging those headers.
    out.after_a = input.a;
    out.after_b = input.b;
    out.after_a->count_i32 = input.b.count_i32;
    out.after_b->count_i32 = input.a.count_i32;
    out.after_a->keys_u16 = input.b.keys_u16;
    out.after_b->keys_u16 = input.a.keys_u16;
    LogicalCross(out,input.a,input.b);
    out.ready = true;
    if (!out.key_elements_ready) out.reason = "key_elements_not_observed";
    return out;
  }
  if (!input.b_allocator_identity || !input.a_allocator_identity) {
    out.reason = "compared_slot30_response_unread";
    return out;
  }
  bool fallback = *input.b_allocator_identity != *input.a_allocator_identity;
  if (!fallback) {
    if (!input.repeated_a_allocator_identity) {
      out.reason = "repeated_a_slot30_response_unread";
      return out;
    }
    fallback = *input.repeated_a_allocator_identity == 0;
  }
  if (fallback) {
    out.path = PersonTransferBlock78Path12004::allocator_fallback;
    out.demanded_callees.push_back(0x1714F50);
    if (!input.a_allocator_field10 || !input.b_allocator_field10) {
      out.reason = "fallback_allocator_field10_unread";
      return out;
    }
    if (*input.a_allocator_field10 != *input.b_allocator_field10) {
      out.demanded_callees.push_back(0x1713F40);
      // Source-closed three moves exchange the logical active U16 sequences.
      // Pointer/capacity postimages depend on the selected allocator backing.
      LogicalCross(out,input.a,input.b);
      out.reason = "allocator_selected_backing_not_supplied";
      return out;
    }
    // Actual1714F65..1714F90: equal +10 fields directly exchange headers.
    out.after_a = input.b;
    out.after_b = input.a;
    out.after_a->storage_identity = input.a.storage_identity;
    out.after_b->storage_identity = input.b.storage_identity;
    out.ready = true;
    LogicalCross(out,input.a,input.b);
    if (!out.key_elements_ready) out.reason = "key_elements_not_observed";
    return out;
  }
  out.path = PersonTransferBlock78Path12004::compatible_allocator_header_swap;
  auto current_a = input.a;
  auto current_b = input.b;
  if (!input.later_b_range) {
    out.reason = "later_b_slot28_response_unread";
    return out;
  }
  if (InRange(input.b.data_identity, *input.later_b_range)) {
    out.demanded_callees.push_back(0x11E10D0);
    if (!input.b_conversion_postimage) {
      out.reason = "actual_b_conversion_postimage_unread";
      return out;
    }
    current_b = *input.b_conversion_postimage;
  }
  if (!input.later_a_range) {
    out.reason = "later_a_slot28_response_unread";
    return out;
  }
  if (InRange(input.a.data_identity, *input.later_a_range)) {
    out.demanded_callees.push_back(0x11E10D0);
    if (!input.a_conversion_postimage) {
      out.reason = "actual_a_conversion_postimage_unread";
      return out;
    }
    current_a = *input.a_conversion_postimage;
  }
  // Exact2306098..23060B9: data, count and capacity move across owners.
  // The separately stored allocator receivers keep their original ownership.
  out.after_a = current_b;
  out.after_b = current_a;
  out.after_a->storage_identity = input.a.storage_identity;
  out.after_b->storage_identity = input.b.storage_identity;
  out.ready = true;
  LogicalCross(out,current_a,current_b);
  if (!out.key_elements_ready) out.reason = "key_elements_not_observed";
  return out;
}

PersonTransferKeyCopy12004 CopyPersonTransferBlock78Keys12004(
    std::uintptr_t actual_storage, void *read_context,
    PersonTransferKeyRead12004 read_memory) {
  PersonTransferKeyCopy12004 out;
  out.storage_identity = actual_storage;
  if (actual_storage == 0 || read_memory == nullptr) {
    out.reason = "key_storage_reader_unavailable";
    return out;
  }
  std::uintptr_t data = 0;
  std::int32_t capacity = 0, count = 0;
  if (read_memory(read_context, reinterpret_cast<const void *>(actual_storage),
                  &data, sizeof(data))) out.data_identity = data;
  if (read_memory(read_context, reinterpret_cast<const void *>(actual_storage + 8),
                  &capacity, sizeof(capacity))) out.capacity_i32 = capacity;
  if (read_memory(read_context, reinterpret_cast<const void *>(actual_storage + 12),
                  &count, sizeof(count))) out.count_i32 = count;
  out.header_ready = out.data_identity && out.capacity_i32 && out.count_i32;
  if (!out.count_i32) {
    out.reason = "key_count_unread";
    return out;
  }
  if (*out.count_i32 < 0) {
    out.reason = "key_count_negative";
    return out;
  }
  if (*out.count_i32 == 0) {
    out.keys_u16.emplace();
    out.key_elements_ready = true;
    if (!out.header_ready) out.reason = "key_header_unread";
    return out;
  }
  if (!out.data_identity || *out.data_identity == 0) {
    out.reason = "key_data_unread";
    return out;
  }
  try {
    std::vector<std::uint16_t> keys(static_cast<std::size_t>(*out.count_i32));
    if (!read_memory(read_context, reinterpret_cast<const void *>(*out.data_identity),
                     keys.data(), keys.size() * sizeof(std::uint16_t))) {
      out.reason = "key_elements_unread";
      return out;
    }
    out.keys_u16 = std::move(keys);
    out.key_elements_ready = true;
    if (!out.header_ready) out.reason = "key_header_unread";
  } catch (...) {
    out.reason = "key_copy_failed";
  }
  return out;
}

PersonTransferKeyCopyComparison12004 ComparePersonTransferBlock78Copies12004(
    const PersonTransferKeyCopy12004 &before_a,
    const PersonTransferKeyCopy12004 &before_b,
    const PersonTransferKeyCopy12004 &after_a,
    const PersonTransferKeyCopy12004 &after_b) {
  PersonTransferKeyCopyComparison12004 out;
  if (before_a.header_ready && before_b.header_ready &&
      after_a.header_ready && after_b.header_ready) {
    out.header_cross_equal =
        after_a.data_identity == before_b.data_identity &&
        after_a.capacity_i32 == before_b.capacity_i32 &&
        after_a.count_i32 == before_b.count_i32 &&
        after_b.data_identity == before_a.data_identity &&
        after_b.capacity_i32 == before_a.capacity_i32 &&
        after_b.count_i32 == before_a.count_i32;
  }
  if (before_a.key_elements_ready && before_b.key_elements_ready &&
      after_a.key_elements_ready && after_b.key_elements_ready) {
    out.key_payload_cross_equal =
        after_a.count_i32 == before_b.count_i32 &&
        after_b.count_i32 == before_a.count_i32 &&
        after_a.keys_u16 == before_b.keys_u16 &&
        after_b.keys_u16 == before_a.keys_u16;
    out.key_exchange_relation_observed = *out.key_payload_cross_equal;
  }
  return out;
}
} // namespace xar::ck3_12004
