#pragma once
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

// External source candidate. NOT compiled, installed, registered or live tested.
namespace xar::ck3_12004::religion::ghw_links_candidate {
inline constexpr std::string_view kExactSha =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
inline constexpr std::uint32_t kNullReference = 0xffffffffu;
inline constexpr std::uintptr_t kFaithGhwReferenceOffset = 0x828;
inline constexpr std::uintptr_t kGhwDatabaseSlotRva = 0x5d1de98;
inline constexpr std::uintptr_t kWarDatabaseSlotRva = 0x5d1de58;
inline constexpr std::uintptr_t kGhwIdentityOffset = 0x10;
inline constexpr std::uintptr_t kGhwMagicOffset = 0x14;
inline constexpr std::uint32_t kGhwMagic = 0x47487957u;
inline constexpr std::uintptr_t kGhwWarReferenceOffset = 0x28;
inline constexpr std::uintptr_t kWarIdentityOffset = 0x08;
inline constexpr std::uintptr_t kWarMagicOffset = 0x0c;
inline constexpr std::uint32_t kWarMagic = 0x5761725fu;

using ReadMemory = bool (*)(void *context, std::uintptr_t address,
                            void *destination, std::size_t bytes) noexcept;
struct Access {
  ReadMemory read_memory = nullptr;
  void *context = nullptr;
  std::uintptr_t image_base = 0;
  // Prerequisite: existing exact .4 religion context resolved this Faith from
  // the played character, on the owned paused main-thread query callback.
  // This candidate deliberately does not infer a Faith ID/tag offset.
  std::uintptr_t bound_faith = 0;
  std::string_view executable_sha256;
};
enum class State { unknown, absent, present };
enum class Failure {
  none, input_not_admitted, memory_unreadable, arithmetic_overflow,
  database_unavailable, database_count_invalid, reference_index_out_of_range,
  table_unavailable, object_unavailable, generation_mismatch, magic_mismatch,
  observations_changed
};
struct Observation {
  bool available = false;
  bool stable_two_pass = false;
  State ghw = State::unknown;
  State war = State::unknown;
  Failure failure = Failure::none;
  // Raw full references are identities, never pointers. A non-null reference
  // alone is not a resolved object or a business outcome.
  std::optional<std::uint32_t> ghw_reference_full_id;
  std::optional<std::uint32_t> war_reference_full_id;
  std::optional<bool> faith_has_offensive_ghw;
  std::optional<bool> has_war_started;
};
// Read-only: supplied hook is the only memory access. The caller owns frame
// admission, actor/faith binding, epoch/date and capture-before/after checks.
// Exactly two bounded passes; no retry, mutation, native command or RPM.
bool ReadGhwObjectLinks12004(const Access &, Observation &) noexcept;
const char *FailureKey(Failure) noexcept;
} // namespace xar::ck3_12004::religion::ghw_links_candidate
