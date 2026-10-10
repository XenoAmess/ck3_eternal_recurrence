#pragma once

#include <cstdint>
#include <cstddef>
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_12004 {

// Exact2305F30 exchanges the U16 key storage beginning at Model+78.
// Its allocator subobject at +18 is never exchanged by its direct stores.
struct PersonTransferKeyStorage12004 {
  std::uintptr_t storage_identity = 0;
  std::uintptr_t data_identity = 0;
  std::int32_t capacity_i32 = 0;
  std::int32_t count_i32 = 0;
  std::optional<std::vector<std::uint16_t>> keys_u16;
  friend bool operator==(const PersonTransferKeyStorage12004 &,
                         const PersonTransferKeyStorage12004 &) = default;
};
struct PersonTransferKeyRange12004 {
  std::uintptr_t base_identity = 0;
  std::int32_t element_count_i32 = 0;
};
struct PersonTransferBlock78Input12004 {
  PersonTransferKeyStorage12004 a;
  PersonTransferKeyStorage12004 b;
  // Actual slot28 responses, in native order. Initial B is not demanded when
  // initial A is inline. The two later responses belong to separate calls.
  std::optional<PersonTransferKeyRange12004> initial_a_range;
  std::optional<PersonTransferKeyRange12004> initial_b_range;
  std::optional<std::uintptr_t> b_allocator_identity;
  std::optional<std::uintptr_t> a_allocator_identity;
  std::optional<std::uintptr_t> repeated_a_allocator_identity;
  std::optional<PersonTransferKeyRange12004> later_b_range;
  std::optional<PersonTransferKeyRange12004> later_a_range;
  // The fallback compares these actual storage+10 QWORD fields, independently
  // of the earlier virtual slot30 responses.
  std::optional<std::uintptr_t> a_allocator_field10;
  std::optional<std::uintptr_t> b_allocator_field10;
  // Actual completed storage copies following demanded11E10D0 calls; these
  // are concrete inputs, never a call ACK or an invented allocator return.
  std::optional<PersonTransferKeyStorage12004> b_conversion_postimage;
  std::optional<PersonTransferKeyStorage12004> a_conversion_postimage;
};
enum class PersonTransferBlock78Path12004 {
  unknown,
  element_swap,
  compatible_allocator_header_swap,
  allocator_fallback
};
struct PersonTransferBlock78Postimage12004 {
  bool ready = false;
  bool key_elements_ready = false;
  PersonTransferBlock78Path12004 path = PersonTransferBlock78Path12004::unknown;
  std::string reason;
  std::optional<PersonTransferKeyStorage12004> after_a;
  std::optional<PersonTransferKeyStorage12004> after_b;
  std::optional<std::int32_t> after_a_count_i32;
  std::optional<std::int32_t> after_b_count_i32;
  std::optional<std::vector<std::uint16_t>> after_a_keys_u16;
  std::optional<std::vector<std::uint16_t>> after_b_keys_u16;
  std::vector<std::uintptr_t> demanded_callees;
  // These receivers are physical subobjects, not allocator slot30 return IDs.
  std::uintptr_t a_allocator_receiver_identity = 0;
  std::uintptr_t b_allocator_receiver_identity = 0;
  bool actual_native_write_performed = false;
  bool full_person_transfer_ready = false;
};

// Pure conditional reconstruction from supplied, per-call native inputs.
// No native callback, allocator, memory access, or historical join is invoked.
PersonTransferBlock78Postimage12004
EvaluatePersonTransferBlock78Postimage12004(
    const PersonTransferBlock78Input12004 &input);

using PersonTransferKeyRead12004 =
    bool (*)(void *, const void *, void *, std::size_t) noexcept;
struct PersonTransferKeyCopy12004 {
  std::uintptr_t storage_identity = 0;
  std::optional<std::uintptr_t> data_identity;
  std::optional<std::int32_t> capacity_i32;
  std::optional<std::int32_t> count_i32;
  std::optional<std::vector<std::uint16_t>> keys_u16;
  bool header_ready = false;
  bool key_elements_ready = false;
  std::string reason;
};
struct PersonTransferKeyCopyComparison12004 {
  std::optional<bool> header_cross_equal;
  std::optional<bool> key_payload_cross_equal;
  // A relation in supplied before/after copies; actual original invocation and
  // its owner/temporal lineage remain the separate continuation-13 boundary.
  bool key_exchange_relation_observed = false;
  bool all_native_delegate_postimages_ready = false;
  bool full_person_transfer_ready = false;
};
PersonTransferKeyCopy12004 CopyPersonTransferBlock78Keys12004(
    std::uintptr_t actual_storage, void *read_context,
    PersonTransferKeyRead12004 read_memory);
PersonTransferKeyCopyComparison12004 ComparePersonTransferBlock78Copies12004(
    const PersonTransferKeyCopy12004 &before_a,
    const PersonTransferKeyCopy12004 &before_b,
    const PersonTransferKeyCopy12004 &after_a,
    const PersonTransferKeyCopy12004 &after_b);

} // namespace xar::ck3_12004
