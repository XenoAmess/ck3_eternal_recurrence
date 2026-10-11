#pragma once

#include "xar_bridge/ck3_12004_lifestyle.hpp"
#include "xar_bridge/current_first_heir_child_inputs_v1.hpp"

#include <bit>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <string>
#include <string_view>

namespace xar::ck3_12004 {

struct ChildCurrentFocusReadonlyAccess12004 {
  void *context = nullptr;
  bool (*read_memory)(void *, const void *, void *, std::size_t) noexcept = nullptr;
};

namespace child_current_focus_readonly_detail {
inline bool ReadBytes(const ChildCurrentFocusReadonlyAccess12004 &access,
                      std::uintptr_t address, void *output,
                      std::size_t bytes) noexcept {
  if (access.read_memory == nullptr || address == 0 || output == nullptr ||
      bytes == 0 ||
      bytes - 1 > (std::numeric_limits<std::uintptr_t>::max)() - address)
    return false;
  return access.read_memory(access.context,
                            reinterpret_cast<const void *>(address),
                            output, bytes);
}

template <typename Value>
inline bool ReadField(const ChildCurrentFocusReadonlyAccess12004 &access,
                      std::uintptr_t object, std::size_t offset,
                      Value &output) noexcept {
  if (object == 0 ||
      offset > (std::numeric_limits<std::uintptr_t>::max)() - object)
    return false;
  return ReadBytes(access, object + offset, &output, sizeof(output));
}

inline bool ReadKeyMemory(void *opaque, std::uintptr_t address,
                          void *output, std::size_t bytes) noexcept {
  const auto *access =
      static_cast<const ChildCurrentFocusReadonlyAccess12004 *>(opaque);
  return access != nullptr && ReadBytes(*access, address, output, bytes);
}

inline bool SameLivingChild(
    const ChildCurrentFocusReadonlyAccess12004 &access,
    std::uintptr_t child, std::int32_t child_full_id,
    std::string_view &reason) noexcept {
  if (child == 0 || child_full_id == -1) {
    reason = "child_full_id_or_liveness_unavailable";
    return false;
  }
  std::uint32_t actual_full_id = 0;
  if (!ReadField(access, child, kCharacterFullIdOffset, actual_full_id)) {
    reason = "child_current_focus_child_identity_read_failed";
    return false;
  }
  if (actual_full_id != std::bit_cast<std::uint32_t>(child_full_id)) {
    reason = "child_full_id_or_liveness_unavailable";
    return false;
  }
  std::uintptr_t death_data = 0;
  if (!ReadField(access, child, kCharacterDeathDataOffset, death_data)) {
    reason = "child_current_focus_child_liveness_read_failed";
    return false;
  }
  if (death_data != 0) {
    reason = "child_full_id_or_liveness_unavailable";
    return false;
  }
  return true;
}

inline ck3_11906::CurrentFirstHeirChildFocusV1 ReadSample(
    const ck3_11906::PlayerLifestyleSnapshotEnvironmentV1 &environment,
    const ChildCurrentFocusReadonlyAccess12004 &access,
    std::int32_t child_full_id, std::uintptr_t child) noexcept {
  ck3_11906::CurrentFirstHeirChildFocusV1 result{};
  if (!SameLivingChild(access, child, child_full_id, result.unavailable_reason))
    return result;

  // Complete readonly 29194B0 body: two nullable links, then verbatim QWORD.
  // This copies its reads; it never invokes the native getter.
  std::uintptr_t extension = 0, holder = 0, focus = 0;
  if (!ReadField(access, child, 0x1B0, extension)) {
    result.unavailable_reason = "child_current_focus_extension_read_failed";
    return result;
  }
  if (extension != 0 && !ReadField(access, extension, 0x280, holder)) {
    result.unavailable_reason = "child_current_focus_holder_read_failed";
    return result;
  }
  if (extension == 0 || holder == 0) {
    if (!ReadField(access, environment.module_base,
                   lifestyle::kPlayerLifestyleFocusFallbackSlotRvaV1, focus)) {
      result.unavailable_reason = "child_current_focus_fallback_read_failed";
      return result;
    }
  } else if (!ReadField(access, holder, 0x08, focus)) {
    result.unavailable_reason = "child_current_focus_getter_read_failed";
    return result;
  }
  if (focus == 0) {
    result.unavailable_reason = "child_current_focus_getter_failed";
    return result;
  }

  std::uintptr_t fallback = 0;
  if (!ReadField(access, environment.module_base,
                 lifestyle::kPlayerLifestyleFocusFallbackSlotRvaV1, fallback)) {
    result.unavailable_reason = "child_current_focus_fallback_read_failed";
    return result;
  }
  if (focus == fallback) {
    result.available = true;
    result.unavailable_reason = {};
    result.presence = "absent";
    return result;
  }

  if (0x18 > (std::numeric_limits<std::uintptr_t>::max)() - focus) {
    result.unavailable_reason = "child_current_focus_key_read_failed";
    return result;
  }
  game::PlayerLifestyleStableKeyV1 key{};
  auto key_access = access;
  if (!lifestyle::ReadPlayerLifestyleMsvcStableKey12004V1(
          &key_access, ReadKeyMemory, focus + 0x18, key)) {
    result.unavailable_reason = "child_current_focus_key_read_failed";
    return result;
  }
  result.available = true;
  result.unavailable_reason = {};
  result.presence = "present";
  result.key = std::string(lifestyle::PlayerLifestyleStableKeyView12004V1(key));
  return result;
}
} // namespace child_current_focus_readonly_detail

// Receiver comes only from the owning query's distinct actual child roster.
// The owning query supplies its coherent paused frame and guarded reader.
// This leaf requires no whole-player LIFE, age, education-key or edit gate.
inline ck3_11906::CurrentFirstHeirChildFocusV1
ReadChildCurrentFocusReadonly12004(
    const ck3_11906::PlayerLifestyleSnapshotEnvironmentV1 &environment,
    const ChildCurrentFocusReadonlyAccess12004 &access,
    std::int32_t child_full_id, std::uintptr_t resolved_child) noexcept {
  using namespace child_current_focus_readonly_detail;
  ck3_11906::CurrentFirstHeirChildFocusV1 unavailable{};
  if (!environment.exact_build_admitted || environment.module_base == 0 ||
      environment.admitted_executable_sha256 != kExecutableSha256)
    return unavailable;
  if (access.read_memory == nullptr) {
    unavailable.unavailable_reason = "child_current_focus_read_memory_unavailable";
    return unavailable;
  }
  const auto first = ReadSample(environment, access, child_full_id, resolved_child);
  if (!first.available) return first;
  auto second = ReadSample(environment, access, child_full_id, resolved_child);
  if (!second.available) return second;
  if (first.presence != second.presence || first.key != second.key) {
    unavailable.unavailable_reason = "child_current_focus_changed";
    return unavailable;
  }
  if (!SameLivingChild(access, resolved_child, child_full_id,
                       unavailable.unavailable_reason))
    return unavailable;
  return second;
}

} // namespace xar::ck3_12004
