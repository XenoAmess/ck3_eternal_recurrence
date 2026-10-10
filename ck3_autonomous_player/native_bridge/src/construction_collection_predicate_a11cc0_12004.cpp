#include "xar_bridge/construction_collection_predicate_a11cc0_12004.hpp"

#include <limits>
#include <utility>

namespace xar::ck3_12004::construction_owner_mode3 {
namespace {
static_assert(sizeof(std::uintptr_t) == 8, "Actual12004 qword model requires x64");

template <typename T>
bool ReadField(const RawReceiverAccessV1 &access, std::uintptr_t base,
               std::size_t offset, T &value) noexcept {
  std::uintptr_t address = 0;
  if (access.read_memory == nullptr ||
      !RawReceiverAddV1(base, offset, address)) return false;
  try {
    return access.read_memory(access.context,
        reinterpret_cast<const void *>(address), &value, sizeof(value));
  } catch (...) {
    return false;
  }
}

std::uintptr_t NativeEndBits(std::uintptr_t buffer,
                            std::int32_t count) noexcept {
  // Native LEA wraps the address width. Signed count is sign extended before
  // multiplication; this final arithmetic does not dereference the endpoint.
  return buffer + static_cast<std::uintptr_t>(static_cast<std::int64_t>(count)) *
      std::uintptr_t{8};
}
} // namespace

ConstructionCollectionPredicateA11CC0V1
ReadConstructionCollectionPredicateA11CC0V1(
    const RawReceiverAccessV1 &access, const ContextPredicateInputsV1 &inputs,
    std::uintptr_t collection_pointer, std::uintptr_t key_qword,
    std::size_t maximum_entries) noexcept {
  ConstructionCollectionPredicateA11CC0V1 result{};
  result.inputs = inputs;
  result.collection_pointer = collection_pointer;
  result.key_qword = key_qword;
  const auto fail = [&](CollectionPredicateA11CC0FailureV1 failure) {
    result.failure = failure;
  };
  if (!access.exact_12004_bound) {
    fail(CollectionPredicateA11CC0FailureV1::exact_build);
    return result;
  }
  if (access.read_memory == nullptr) {
    fail(CollectionPredicateA11CC0FailureV1::read_callback);
    return result;
  }
  if (key_qword != inputs.first_pointer) {
    fail(CollectionPredicateA11CC0FailureV1::copied_key_binding);
    return result;
  }
  try {
    std::int32_t count = 0;
    std::uintptr_t buffer = 0;
    // Match the actual load order: signed count first, then pointer.
    if (!ReadField(access, collection_pointer, 12, count)) {
      fail(CollectionPredicateA11CC0FailureV1::header_count);
      return result;
    }
    result.initial_count_raw = count;
    if (!ReadField(access, collection_pointer, 0, buffer)) {
      fail(CollectionPredicateA11CC0FailureV1::header_buffer);
      return result;
    }
    result.initial_buffer_pointer = buffer;
    result.initial_end_pointer = NativeEndBits(buffer, count);
    if (count < 0) {
      fail(CollectionPredicateA11CC0FailureV1::negative_initial_count);
      return result;
    }
    const auto entries = static_cast<std::size_t>(count);
    if (entries > maximum_entries) {
      fail(CollectionPredicateA11CC0FailureV1::copy_bound);
      return result;
    }
    const auto extent_bytes = static_cast<std::uintptr_t>(entries) * 8;
    if (extent_bytes > std::numeric_limits<std::uintptr_t>::max() - buffer) {
      fail(CollectionPredicateA11CC0FailureV1::initial_extent_overflow);
      return result;
    }
    if (entries != 0 && buffer == 0) {
      fail(CollectionPredicateA11CC0FailureV1::array_pointer);
      return result;
    }
    result.ordered_qwords.reserve(entries);
    for (std::size_t index = 0; index < entries; ++index) {
      std::uintptr_t raw = 0;
      if (!ReadField(access, buffer, index * 8, raw)) {
        fail(CollectionPredicateA11CC0FailureV1::array_read);
        return result;
      }
      result.ordered_qwords.push_back(raw);
      if (!result.first_match_index && raw == key_qword)
        result.first_match_index = static_cast<std::uint32_t>(index);
    }
    result.ordered_qwords_complete = true;
    result.found_pointer = result.first_match_index
        ? buffer + static_cast<std::uintptr_t>(*result.first_match_index) * 8
        : *result.initial_end_pointer;

    std::int32_t reloaded_count = 0;
    std::uintptr_t reloaded_buffer = 0;
    if (!ReadField(access, collection_pointer, 12, reloaded_count)) {
      fail(CollectionPredicateA11CC0FailureV1::reloaded_count);
      return result;
    }
    result.reloaded_count_raw = reloaded_count;
    if (!ReadField(access, collection_pointer, 0, reloaded_buffer)) {
      fail(CollectionPredicateA11CC0FailureV1::reloaded_buffer);
      return result;
    }
    result.reloaded_buffer_pointer = reloaded_buffer;
    result.reloaded_end_pointer = NativeEndBits(reloaded_buffer, reloaded_count);
    result.header_unchanged = reloaded_count == count && reloaded_buffer == buffer;
    // Literal A11DB2/DB5/DB9/DC1: endpoint equality converts the found pointer
    // to null, then setne tests that pointer. Do not replace this with contains.
    result.value = *result.found_pointer != *result.reloaded_end_pointer &&
        *result.found_pointer != 0;
    return result;
  } catch (...) {
    fail(CollectionPredicateA11CC0FailureV1::copy_exception);
    return result;
  }
}

bool ReadConstructionCollectionPredicateA11CC0ChildV1(
    void *opaque, const RawReceiverAccessV1 &access,
    const ContextPredicateInputsV1 &inputs, std::uintptr_t collection_pointer,
    std::uintptr_t key_qword, bool &value) noexcept {
  auto *context = static_cast<CollectionPredicateA11CC0ReadContextV1 *>(opaque);
  auto result = ReadConstructionCollectionPredicateA11CC0V1(
      access, inputs, collection_pointer, key_qword,
      context ? context->maximum_entries : kConstructionCollectionCopyBoundV1);
  const auto captured_value = result.value;
  if (context != nullptr && context->last_result != nullptr)
    *context->last_result = std::move(result);
  if (!captured_value) return false;
  value = *captured_value;
  return true;
}

} // namespace xar::ck3_12004::construction_owner_mode3
