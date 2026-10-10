#include "xar_bridge/person_transfer_values_snapshot_12004.hpp"

#include <bit>
#include <cstring>

namespace xar::ck3_12004 {
namespace {

struct LegacyReaderContext12004 {
  void *context = nullptr;
  PersonInstalledTransferRead12004 read = nullptr;
  std::uintptr_t count_address = 0;
  std::size_t maximum_payload_bytes = 0;
  std::optional<std::int32_t> actual_count;
  bool payload_budget_exceeded = false;
};

bool ReadLegacyValues12004(void *context, const void *source, void *destination,
                          std::size_t bytes) noexcept {
  auto &reader = *static_cast<LegacyReaderContext12004 *>(context);
  const auto address = reinterpret_cast<std::uintptr_t>(source);
  if (!reader.read(reader.context, address, destination, bytes))
    return false;
  if (address == reader.count_address && bytes == sizeof(std::int32_t)) {
    std::int32_t count = 0;
    std::memcpy(&count, destination, sizeof(count));
    reader.actual_count = count;
    if (count >= 0 && static_cast<std::uint64_t>(count) *
                          sizeof(std::int64_t) >
                          reader.maximum_payload_bytes) {
      reader.payload_budget_exceeded = true;
      return false;
    }
  }
  return true;
}

} // namespace

PersonTransferValuesSnapshot12004 CapturePersonTransferValuesSnapshot12004(
    const PersonTransferSnapshotScope12004 &scope, void *read_context,
    PersonInstalledTransferRead12004 read,
    std::size_t maximum_payload_bytes) {
  PersonTransferValuesSnapshot12004 result;
  result.scope = scope;
  result.maximum_payload_bytes = maximum_payload_bytes;
  LegacyReaderContext12004 reader{
      read_context, read,
      scope.model_identity + kPersonTransferBlockE0Offset12004 + 0xC,
      maximum_payload_bytes, std::nullopt, false};
  const auto bindings = BindPersonTransferBlockE0Memory12004(
      "1.20.0.4",
      "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
      read == nullptr ? nullptr : &ReadLegacyValues12004, &reader);
  result.raw = CopyPersonTransferBlockE0Storage12004(bindings,
                                                   scope.model_identity);
  if (reader.payload_budget_exceeded) {
    result.raw.count_i32 = reader.actual_count;
    result.raw.values_q64.reset();
    result.raw.values_reason = "values_payload_budget_exceeded";
  }
  result.descriptor_copy_complete =
      result.raw.data_identity.has_value() &&
      result.raw.capacity_i32.has_value() && result.raw.count_i32.has_value();
  result.payload_copy_complete =
      result.raw.count_i32.has_value() && *result.raw.count_i32 >= 0 &&
      result.raw.values_q64.has_value() &&
      result.raw.values_q64->size() ==
          static_cast<std::size_t>(*result.raw.count_i32);
  if (result.payload_copy_complete) {
    result.values_q64_raw_bits.emplace();
    result.values_q64_raw_bits->reserve(result.raw.values_q64->size());
    for (const auto value : *result.raw.values_q64)
      result.values_q64_raw_bits->push_back(std::bit_cast<std::uint64_t>(value));
  }
  result.declared_operand_copy_complete =
      result.descriptor_copy_complete && result.payload_copy_complete;
  if (!result.payload_copy_complete)
    result.reason = result.raw.values_reason.empty()
                        ? "values_payload_copy_incomplete"
                        : result.raw.values_reason;
  else if (!result.descriptor_copy_complete)
    result.reason = "values_descriptor_copy_partial";
  return result;
}

} // namespace xar::ck3_12004
