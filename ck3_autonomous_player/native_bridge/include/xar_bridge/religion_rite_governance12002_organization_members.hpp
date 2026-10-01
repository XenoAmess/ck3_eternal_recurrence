#pragma once
#include "xar_bridge/ck3_12002_religion_context.hpp"
#include <vector>

namespace xar::ck3_12002::religion::organization::members {
inline constexpr std::uintptr_t kFaithCharacterCollectorRva = 0x1C610E0;
inline constexpr std::uintptr_t kRiteCountyCollectorRva = 0x1D2B6F0;
inline constexpr std::uintptr_t kTitleStorageSlotRva = 0x5D1DAF8;
inline constexpr std::size_t kAlivePoolOffset = 0x2EE60;
inline constexpr std::size_t kAlivePoolSizeOffset = 0x2EE6C;
inline constexpr std::size_t kReligionCountyPoolOffset = 0x200;
inline constexpr std::size_t kReligionCountyPoolSizeOffset = 0x20C;
inline constexpr std::size_t kTitleIdentityOffset = 0x10;
inline constexpr std::size_t kTitleTemplateOffset = 0x48;
inline constexpr std::size_t kTitleTemplateRankOffset = 0x64;
inline constexpr std::uint16_t kCharacterScope = 0x04;
inline constexpr std::uint16_t kTitleScope = 0x05;
inline constexpr std::uint16_t kFaithScope = 0x0D;
inline constexpr std::uint16_t kRiteScope = 0x2A;

struct ScopeValue {
  std::uint16_t kind = 0;
  std::uint16_t flags = 0;
  std::uint32_t reserved = 0;
  std::uint64_t identity = 0;
};
struct ScopeArray {
  ScopeValue *data = nullptr;
  std::int32_t capacity = 0;
  std::int32_t size = 0;
  void *allocator = nullptr;
};
struct ScopeRoot { const ScopeValue *root = nullptr; };
static_assert(sizeof(ScopeValue) == 16 && offsetof(ScopeValue, identity) == 8);
static_assert(sizeof(ScopeArray) == 24 && offsetof(ScopeArray, capacity) == 8 &&
              offsetof(ScopeArray, size) == 12 && offsetof(ScopeArray, allocator) == 16);
using Collector = void (*)(void *, ScopeArray *, const ScopeRoot *);
struct Bindings {
  bool enabled = false;
  CoreBindings core{};
  ObjectGetter character_rite = nullptr;
  ObjectGetter rite_faith = nullptr;
  ObjectGetter faith_religion = nullptr;
  void **title_storage_slot = nullptr;
  Collector faith_characters = nullptr;
  Collector rite_counties = nullptr;
};
enum class Failure {
  none,
  bindings_unavailable,
  frame_unavailable,
  frame_not_paused,
  religion_context_unavailable,
  source_pool_unavailable,
  native_output_unavailable,
  character_unavailable,
  county_title_unavailable,
  state_changed,
};
struct Snapshot {
  bool available = false;
  Failure failure = Failure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::optional<std::uint32_t> rite_id, faith_id, religion_id;
  std::vector<std::uint32_t> faith_character_ids;
  std::vector<std::uint32_t> rite_character_ids;
  std::vector<std::uint32_t> county_title_ids;
};
Bindings BindOrganizationMembersImage12002(std::uintptr_t module_base,
                                           std::string_view executable_sha256) noexcept;
bool ReadPlayedOrganizationMembers12002(const Bindings &bindings,
                                        std::uint64_t capture_epoch,
                                        Snapshot &output) noexcept;
const char *MembersFailureKey(Failure failure) noexcept;
std::string SerializePlayedOrganizationMembers12002(const Snapshot &snapshot);
} // namespace xar::ck3_12002::religion::organization::members
