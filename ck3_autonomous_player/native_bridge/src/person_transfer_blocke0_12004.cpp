#include "xar_bridge/person_transfer_blocke0_12004.hpp"

#include <utility>

namespace xar::ck3_12004 {
namespace {
constexpr std::string_view kVersion = "1.20.0.4";
constexpr std::string_view kExecutableSha256 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";

template <typename T>
std::optional<T> Copy(const PersonTransferBlockE0Bindings12004 &bindings,
                      std::uintptr_t address) {
  T value{};
  if (!bindings.read_memory(bindings.read_context,
                            reinterpret_cast<const void *>(address), &value,
                            sizeof(value)))
    return std::nullopt;
  return value;
}

bool HeaderCopied(const PersonTransferBlockE0Copy12004 &copy) {
  return copy.data_identity.has_value() && copy.capacity_i32.has_value() &&
         copy.count_i32.has_value();
}

bool CrossHeader(const PersonTransferBlockE0Copy12004 &before,
                 const PersonTransferBlockE0Copy12004 &after) {
  return before.data_identity == after.data_identity &&
         before.capacity_i32 == after.capacity_i32 &&
         before.count_i32 == after.count_i32;
}
} // namespace

PersonTransferBlockE0Bindings12004 BindPersonTransferBlockE0Memory12004(
    std::string_view version, std::string_view executable_sha256,
    PersonTransferBlockE0ReadMemory12004 read_memory,
    void *read_context) noexcept {
  if (version != kVersion || executable_sha256 != kExecutableSha256 ||
      read_memory == nullptr)
    return {};
  return {true, read_memory, read_context};
}

PersonTransferBlockE0Copy12004 CopyPersonTransferBlockE0Storage12004(
    const PersonTransferBlockE0Bindings12004 &bindings,
    std::uintptr_t actual_model) {
  PersonTransferBlockE0Copy12004 result;
  result.model_identity = actual_model;
  if (!bindings.enabled || bindings.read_memory == nullptr) {
    result.values_reason = "exact_build_binding_unavailable";
    return result;
  }
  if (actual_model == 0) {
    result.values_reason = "actual_model_unavailable";
    return result;
  }
  const auto block = actual_model + kPersonTransferBlockE0Offset12004;
  result.block_identity = block;
  result.allocator_receiver_identity = block + 0x18;
  result.data_identity = Copy<std::uintptr_t>(bindings, block);
  result.capacity_i32 = Copy<std::int32_t>(bindings, block + 8);
  result.count_i32 = Copy<std::int32_t>(bindings, block + 0xC);
  if (!result.count_i32) {
    result.values_reason = "value_count_unread";
    return result;
  }
  if (*result.count_i32 < 0) {
    result.values_reason = "value_count_negative";
    return result;
  }
  if (*result.count_i32 == 0) {
    result.values_q64.emplace();
    return result;
  }
  if (!result.data_identity || *result.data_identity == 0) {
    result.values_reason = "value_data_unread_or_null";
    return result;
  }
  std::vector<std::int64_t> values(
      static_cast<std::size_t>(*result.count_i32));
  if (!bindings.read_memory(
          bindings.read_context,
          reinterpret_cast<const void *>(*result.data_identity), values.data(),
          values.size() * sizeof(std::int64_t))) {
    result.values_reason = "value_array_unread";
    return result;
  }
  result.values_q64 = std::move(values);
  return result;
}

PersonTransferBlockE0Comparison12004 ComparePersonTransferBlockE0Copies12004(
    const PersonTransferBlockE0Copy12004 &pre_a,
    const PersonTransferBlockE0Copy12004 &pre_b,
    const PersonTransferBlockE0Copy12004 &post_a,
    const PersonTransferBlockE0Copy12004 &post_b) {
  PersonTransferBlockE0Comparison12004 result;
  result.model_pair_matches =
      pre_a.model_identity != 0 && pre_b.model_identity != 0 &&
      pre_a.model_identity == post_a.model_identity &&
      pre_b.model_identity == post_b.model_identity;
  if (!result.model_pair_matches) {
    result.reason = "copied_model_pair_mismatch";
    return result;
  }
  if (pre_b.values_q64 && post_a.values_q64)
    result.a_values_equal_pre_b = *post_a.values_q64 == *pre_b.values_q64;
  if (pre_a.values_q64 && post_b.values_q64)
    result.b_values_equal_pre_a = *post_b.values_q64 == *pre_a.values_q64;
  if (result.a_values_equal_pre_b && result.b_values_equal_pre_a)
    result.copied_values_cross_equal =
        *result.a_values_equal_pre_b && *result.b_values_equal_pre_a;
  else
    result.reason = "copied_value_sequences_partial";
  if (HeaderCopied(pre_a) && HeaderCopied(pre_b) && HeaderCopied(post_a) &&
      HeaderCopied(post_b))
    result.entry_headers_cross_equal =
        CrossHeader(pre_b, post_a) && CrossHeader(pre_a, post_b);
  return result;
}

PersonTransferBlockE0DirectHeaderPostimage12004
ProjectPersonTransferBlockE0DirectHeaderStores12004(
    const PersonTransferBlockE0Header12004 &a,
    const PersonTransferBlockE0Header12004 &b) noexcept {
  return {{a.block_identity, b.data_identity, b.capacity_i32, b.count_i32,
           a.allocator_receiver_identity},
          {b.block_identity, a.data_identity, a.capacity_i32, a.count_i32,
           b.allocator_receiver_identity}};
}
} // namespace xar::ck3_12004
