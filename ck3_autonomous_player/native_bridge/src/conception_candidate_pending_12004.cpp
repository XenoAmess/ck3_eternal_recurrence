#include "xar_bridge/conception_candidate_pending_12004.hpp"

#include <bit>

namespace xar::ck3_12004::conception_candidate_pending {
namespace {
template <typename T>
bool ReadAt(const Access &access, std::uintptr_t base, std::size_t offset,
            T &output) noexcept {
  return base != 0 && access.read_memory != nullptr &&
      access.read_memory(access.context, base + offset, &output, sizeof(T));
}
} // namespace

Observation Read(const Access &access, const void *character,
                 std::int32_t character_id) noexcept {
  Observation result{};
  if (!access.exact_build_admitted ||
      access.executable_sha256 != kExecutableSha256 ||
      access.read_memory == nullptr) return result;
  const auto owner = reinterpret_cast<std::uintptr_t>(character);
  std::uint32_t owner_id = 0;
  std::uint32_t owner_magic = 0;
  if (character_id == -1 ||
      !ReadAt(access, owner, kCharacterFullIdOffset, owner_id) ||
      !ReadAt(access, owner, kCharacterMagicOffset, owner_magic) ||
      owner_id != std::bit_cast<std::uint32_t>(character_id) ||
      owner_magic != kCharacterMagic) {
    result.candidate_state_unavailable_reason =
        "conception_candidate_owner_unavailable";
    return result;
  }
  std::uintptr_t extended = 0;
  if (!ReadAt(access, owner, kCharacterExtendedDataOffset, extended)) {
    result.candidate_state_unavailable_reason =
        "conception_candidate_extended_pointer_unavailable";
    return result;
  }
  result.extended_data_present = extended != 0;
  if (extended == 0) {
    result.candidate_state_unavailable_reason =
        "conception_candidate_extended_data_absent";
    return result;
  }
  std::uint8_t flag = 0;
  // Actual2929DA5 stores one byte; do not widen to a DWORD or a bool field.
  if (!ReadAt(access, extended, kCandidateFlagOffset, flag)) {
    result.candidate_state_unavailable_reason =
        "conception_candidate_flag_unavailable";
    return result;
  }
  result.candidate_state_available = true;
  result.candidate_state_unavailable_reason = {};
  result.candidate_flag_raw = flag;
  if (flag == 0) {
    result.target_status = "not_requested";
    result.target_unavailable_reason = {};
    return result;
  }

  result.target_status = "unavailable";
  result.target_unavailable_reason = "conception_candidate_target_pointer_unavailable";
  std::uintptr_t target = 0;
  static_assert(sizeof(target) == 8);
  // Actual2929DB3 stores the second Character pointer, not a pregnancy ID.
  if (!ReadAt(access, extended, kCandidateTargetOffset, target)) return result;
  result.target_pointer_raw = target;
  if (target == 0) {
    result.target_status = "null_pointer";
    result.target_unavailable_reason = {};
    return result;
  }
  std::uint32_t target_id = 0;
  std::uint32_t target_magic = 0;
  result.target_unavailable_reason = "conception_candidate_target_identity_unavailable";
  if (!ReadAt(access, target, kCharacterFullIdOffset, target_id)) return result;
  result.target_full_id_raw = target_id;
  if (!ReadAt(access, target, kCharacterMagicOffset, target_magic)) return result;
  if (target_id == 0xFFFFFFFFU || target_magic != kCharacterMagic) {
    result.target_status = "invalid_identity";
    result.target_unavailable_reason = "conception_candidate_target_identity_invalid";
    return result;
  }
  result.target_unavailable_reason = "conception_candidate_target_resolver_unavailable";
  if (access.resolve_character == nullptr) return result;
  const auto full_id = std::bit_cast<std::int32_t>(target_id);
  const auto *resolved = access.resolve_character(access.context, full_id);
  if (resolved != reinterpret_cast<const void *>(target)) {
    result.target_status = "generation_mismatch";
    result.target_unavailable_reason = "conception_candidate_target_generation_unavailable";
    return result;
  }
  result.target_status = "resolved";
  result.target_unavailable_reason = {};
  result.resolved_target_character_id = full_id;
  return result;
}

} // namespace xar::ck3_12004::conception_candidate_pending
