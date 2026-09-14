#pragma once

#include <cstddef>
#include <cstdint>
#include <string>

namespace xar::ck3::research {

inline constexpr std::size_t kDomainConstructionCandidateRowBytesV1 = 0x28;
inline constexpr std::size_t kDomainConstructionObjectIdentityOffsetV1 = 0x10;

enum class DomainConstructionCandidateKindV1 : std::uint8_t {
  building_in_holding = 1,
  new_holding = 2,
};

enum class DomainConstructionCandidateDecodeFailureV1 : std::uint8_t {
  none = 0,
  row_size,
  row_marker,
  selector,
  null_pointer,
  address_overflow,
  memory_read,
  identity_shape,
};

using DomainConstructionReadMemoryV1 = bool (*)(
    void* context, std::uintptr_t address, void* destination,
    std::size_t bytes);

struct DomainConstructionCandidateIdentityV1 final {
  bool ready = false;
  DomainConstructionCandidateKindV1 kind =
      DomainConstructionCandidateKindV1::building_in_holding;
  DomainConstructionCandidateDecodeFailureV1 failure =
      DomainConstructionCandidateDecodeFailureV1::none;
  std::int32_t native_ai_value = 0;
  std::int32_t holding_province_id = -1;
  std::int32_t building_type_id = -1;
  std::int32_t candidate_province_id = -1;
  std::int32_t candidate_selector = -1;
  std::string candidate_id;
};

[[nodiscard]] DomainConstructionCandidateIdentityV1
DecodeDomainConstructionCandidateIdentityV1(
    const std::uint8_t* row, std::size_t row_bytes,
    DomainConstructionReadMemoryV1 read_memory, void* read_context);

}  // namespace xar::ck3::research
