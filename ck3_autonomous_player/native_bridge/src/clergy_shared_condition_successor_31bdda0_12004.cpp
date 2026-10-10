#include "xar_bridge/clergy_shared_condition_successor_31bdda0_12004.hpp"

namespace xar::ck3_12004::religion::clergy {

ClergyShared31BDDA0RawAL12004 ReadClergyShared31BDDA0WithGenericChild12004(
    void *read_context, ReadMemory read, std::uint32_t owner_raw_u32,
    std::uintptr_t literal_rdx, std::uintptr_t literal_r8,
    xar::ck3_12004::GenericTriggerOwnerScopeChildContext12004 &child) {
  auto result = ReadClergyShared31BDDA0RawAL12004(read_context, read,
      owner_raw_u32, literal_rdx, literal_r8);
  if (!result.condition_child_required) return result;

  std::uint8_t child_raw{};
  const auto available = xar::ck3_12004::TryReadGenericTriggerOwnerScope372DF1012004(
      &child, read, read_context, result.r8_identity, std::uint16_t{4},
      std::uint64_t{result.rcx_raw_u32}, child_raw);
  if (!available) {
    result.raw_al.reset();
    result.source_ready = false;
    result.unavailable_reason = "condition_372df10_result_unavailable";
    return result;
  }
  result.raw_al = child_raw;
  result.source_ready = true;
  result.unavailable_reason = {};
  return result;
}

} // namespace xar::ck3_12004::religion::clergy
