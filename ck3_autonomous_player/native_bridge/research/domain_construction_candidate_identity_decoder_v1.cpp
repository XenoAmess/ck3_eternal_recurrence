#include "domain_construction_candidate_identity_decoder_v1.hpp"

#include <cstring>
#include <limits>
#include <string>

namespace xar::ck3::research {
namespace {

template <typename T>
T LoadRowValue(const std::uint8_t* row, const std::size_t offset) {
  T value{};
  std::memcpy(&value, row + offset, sizeof(value));
  return value;
}

bool LoadObjectIdentity(const std::uintptr_t object,
                        DomainConstructionReadMemoryV1 read_memory,
                        void* read_context, std::int32_t& identity,
                        DomainConstructionCandidateDecodeFailureV1& failure) {
  if (object == 0U) {
    failure = DomainConstructionCandidateDecodeFailureV1::null_pointer;
    return false;
  }
  if (object > std::numeric_limits<std::uintptr_t>::max() -
                   kDomainConstructionObjectIdentityOffsetV1) {
    failure = DomainConstructionCandidateDecodeFailureV1::address_overflow;
    return false;
  }
  if (!read_memory(read_context,
                   object + kDomainConstructionObjectIdentityOffsetV1,
                   &identity, sizeof(identity))) {
    failure = DomainConstructionCandidateDecodeFailureV1::memory_read;
    return false;
  }
  return true;
}

std::string BuildingCandidateId(const std::int32_t holding_province_id,
                                const std::int32_t candidate_selector,
                                const std::int32_t building_type_id) {
  return "building:" + std::to_string(holding_province_id) + ":" +
         std::to_string(candidate_selector) + ":" +
         std::to_string(building_type_id);
}

std::string HoldingCandidateId(const std::int32_t candidate_province_id,
                               const std::int32_t candidate_selector) {
  return "holding:" + std::to_string(candidate_province_id) + ":" +
         std::to_string(candidate_selector);
}

}  // namespace

DomainConstructionCandidateIdentityV1 DecodeDomainConstructionCandidateIdentityV1(
    const std::uint8_t* row, const std::size_t row_bytes,
    const DomainConstructionReadMemoryV1 read_memory, void* read_context) {
  DomainConstructionCandidateIdentityV1 result{};
  if (row == nullptr || row_bytes != kDomainConstructionCandidateRowBytesV1) {
    result.failure = DomainConstructionCandidateDecodeFailureV1::row_size;
    return result;
  }
  if (row[0x24] != 1U) {
    result.failure = DomainConstructionCandidateDecodeFailureV1::row_marker;
    return result;
  }
  if (read_memory == nullptr) {
    result.failure = DomainConstructionCandidateDecodeFailureV1::memory_read;
    return result;
  }

  result.native_ai_value = LoadRowValue<std::int32_t>(row, 0x00);
  result.candidate_selector = LoadRowValue<std::int32_t>(row, 0x20);
  if (result.candidate_selector < 0) {
    result.failure = DomainConstructionCandidateDecodeFailureV1::selector;
    return result;
  }

  const auto holding_pointer = LoadRowValue<std::uintptr_t>(row, 0x08);
  const auto building_pointer = LoadRowValue<std::uintptr_t>(row, 0x10);
  const auto candidate_pointer = LoadRowValue<std::uintptr_t>(row, 0x18);
  if (!LoadObjectIdentity(holding_pointer, read_memory, read_context,
                          result.holding_province_id, result.failure) ||
      !LoadObjectIdentity(building_pointer, read_memory, read_context,
                          result.building_type_id, result.failure) ||
      !LoadObjectIdentity(candidate_pointer, read_memory, read_context,
                          result.candidate_province_id, result.failure)) {
    return result;
  }

  const bool building_shape = result.holding_province_id >= 0 &&
                              result.building_type_id >= 0 &&
                              result.candidate_province_id < 0;
  const bool holding_shape = result.holding_province_id < 0 &&
                             result.building_type_id < 0 &&
                             result.candidate_province_id >= 0;
  if (building_shape == holding_shape) {
    result.failure = DomainConstructionCandidateDecodeFailureV1::identity_shape;
    return result;
  }

  if (building_shape) {
    result.kind = DomainConstructionCandidateKindV1::building_in_holding;
    result.candidate_id = BuildingCandidateId(
        result.holding_province_id, result.candidate_selector,
        result.building_type_id);
  } else {
    result.kind = DomainConstructionCandidateKindV1::new_holding;
    result.candidate_id = HoldingCandidateId(result.candidate_province_id,
                                             result.candidate_selector);
  }
  result.ready = true;
  result.failure = DomainConstructionCandidateDecodeFailureV1::none;
  return result;
}

}  // namespace xar::ck3::research
