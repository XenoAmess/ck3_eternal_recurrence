#pragma once

#include "xar_bridge/ck3_1210.hpp"
#include <cstddef>
#include <cstdint>
#include <string_view>
#include <vector>

namespace xar::ck3_1210 {
inline constexpr std::size_t kCharacterManagerOffsetV1 = 0x3F540;
inline constexpr std::uintptr_t kCharacterManagerVtableRvaV1 = 0x4E83550;
// Author observation bounds, never asserted engine maxima.
inline constexpr std::int32_t kCharacterManagerMemberLimitV1 = 131072;
inline constexpr std::int32_t kCharacterLookupCapacityLimitV1 = 4194304;
struct CharacterManagerBindingsV1 {
  bool exact_build_admitted = false;
  CoreBindings core{};
  std::uintptr_t manager_vtable = 0;
};
using CharacterManagerCopyV1 = bool (*)(void *context, const void *source,
    void *destination, std::size_t bytes) noexcept;
struct CharacterManagerReadAccessV1 {
  void *context = nullptr;
  CharacterManagerCopyV1 copy = nullptr;
};
struct CharacterManagerMemberV1 {
  // Preserve full signed32 bits; only -1 is absent. Zero is a real full ID.
  std::int32_t character_id = -1;
  bool alive = false;
  bool has_living_data = false;
  friend bool operator==(const CharacterManagerMemberV1 &,
      const CharacterManagerMemberV1 &) = default;
};
struct CharacterManagerObservationV1 {
  bool available = false;
  bool same_frame_ready = false;
  bool manager_members_complete = false;
  // The proven maintained vector is not a chooser, realm, or all-living proof.
  bool candidates_complete = false;
  bool full_snapshot_available = false;
  CoreSnapshotPrefix frame{};
  std::vector<CharacterManagerMemberV1> members;
  std::string_view unavailable_reason = "character_manager_not_read";
};
CharacterManagerBindingsV1 BindCharacterManagerImageV1(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
// Read-only internal observation. The caller owns the paused application-main
// execution and must not span pumps or use this result to admit a callback.
// Two exact transcripts include manager/root/storage identity, full generation,
// object equality and lifecycle headers. No native pointer or borrow escapes.
// Equality is a repeated observation, not a lock, pin or ABA/lifetime proof.
// Null/unread/stale/duplicate rows fail closed; dead rows are retained.
bool ReadCharacterManagerV1(const CharacterManagerBindingsV1 &bindings,
    const CoreSnapshotPrefix &expected, CharacterManagerObservationV1 &output,
    CharacterManagerReadAccessV1 access = {}) noexcept;
} // namespace xar::ck3_1210
