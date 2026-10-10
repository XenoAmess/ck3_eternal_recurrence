#pragma once

#include "xar_bridge/ck3_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004::conception_candidate_pending {

inline constexpr std::size_t kCharacterMagicOffset = 0x1C;
inline constexpr std::uint32_t kCharacterMagic = 0x43686172;
inline constexpr std::size_t kCharacterExtendedDataOffset = 0x1B0;
inline constexpr std::size_t kCandidateFlagOffset = 0x3E8;
inline constexpr std::size_t kCandidateTargetOffset = 0x3F0;

using ReadMemory = bool (*)(void *, std::uintptr_t, void *, std::size_t) noexcept;
// The owning family callback supplies its existing actual4 full-ID resolver,
// not a second Character store or an arbitrary population selector.
using ResolveCharacter = void *(*)(void *, std::int32_t) noexcept;

struct Access {
  bool exact_build_admitted = false;
  std::string_view executable_sha256{};
  void *context = nullptr;
  ReadMemory read_memory = nullptr;
  ResolveCharacter resolve_character = nullptr;
};

struct Observation {
  bool candidate_state_available = false;
  std::string_view candidate_state_unavailable_reason =
      "conception_candidate_binding_unavailable";
  std::optional<bool> extended_data_present{};
  std::optional<std::uint8_t> candidate_flag_raw{};

  // Target failure never changes a byte already read successfully. A zero
  // byte does not demand the unused target slot. These labels describe this
  // observation only; clearing, active pregnancy and birth remain separate.
  std::string_view target_status = "not_sampled";
  std::string_view target_unavailable_reason = "candidate_state_unavailable";
  std::optional<std::uintptr_t> target_pointer_raw{};
  std::optional<std::uint32_t> target_full_id_raw{};
  std::optional<std::int32_t> resolved_target_character_id{};
};

// character belongs to an existing current-heir/spouse role and has already
// been resolved by the owning query. The owning callback supplies its usual
// paused before/after frame validation. No native initializer or action runs.
Observation Read(const Access &, const void *character,
                 std::int32_t character_id) noexcept;

} // namespace xar::ck3_12004::conception_candidate_pending
