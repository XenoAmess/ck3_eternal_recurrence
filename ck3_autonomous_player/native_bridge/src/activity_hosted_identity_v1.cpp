#include "xar_bridge/activity_hosted_identity_v1.hpp"

#include <array>
#include <limits>

namespace xar::bridge {
namespace {

constexpr std::uintptr_t kManagerRootRva = 0x570E068;
constexpr std::uintptr_t kPlayedCharacterIdRva = 0x4FE7EE0;
constexpr std::uintptr_t kCharacterStorageRva = 0x570C130;
constexpr std::uintptr_t kCharacterFallbackRva = 0x570C138;
constexpr std::uintptr_t kActivityVtableRva = 0x42F2F28;
constexpr std::uintptr_t kActivityTypeVtableRva = 0x440E308;
constexpr std::uint32_t kMaximumSlotIndex = 0x00FFFFFE;
constexpr std::size_t kActivityStride = 0x5F0;
constexpr std::size_t kSlotsPerChunk = 1024;

bool Is12002(const ActivityHostedIdentityEnvironmentV1 &environment) noexcept {
  return environment.admitted_executable_sha256 ==
         kActivityHostedIdentity12002ExeSha256V1;
}

struct ManagerSample {
  std::uintptr_t chunks = 0;
  std::uint32_t chunk_count = 0;
  std::uintptr_t index_table = 0;
  std::uint32_t capacity = 0;
  std::int32_t highest_live = -1;
  std::uint32_t active_count = 0;

  friend bool operator==(const ManagerSample &, const ManagerSample &) = default;
};

bool CheckedAdd(std::uintptr_t base, std::size_t offset,
                std::uintptr_t &address) noexcept {
  if (base == 0 || offset > (std::numeric_limits<std::uintptr_t>::max)() - base)
    return false;
  address = base + offset;
  return true;
}

bool Read(const ActivityHostedIdentityEnvironmentV1 &environment,
          std::uintptr_t address, void *output, std::size_t size) noexcept {
  return environment.read_memory != nullptr &&
         environment.read_memory(environment.context, address, output, size);
}

template <typename T>
bool ReadAt(const ActivityHostedIdentityEnvironmentV1 &environment,
            std::uintptr_t base, std::size_t offset, T &output) noexcept {
  std::uintptr_t address = 0;
  return CheckedAdd(base, offset, address) &&
         Read(environment, address, &output, sizeof(output));
}

template <std::size_t Size>
bool MatchCode(const ActivityHostedIdentityEnvironmentV1 &environment,
               std::uintptr_t rva,
               const std::array<std::uint8_t, Size> &expected) noexcept {
  std::array<std::uint8_t, Size> observed{};
  return ReadAt(environment, environment.module_base, rva, observed) &&
         observed == expected;
}

bool VerifyExactBuild(
    const ActivityHostedIdentityEnvironmentV1 &environment) noexcept {
  constexpr std::array<std::uint8_t, 7> kDispatch{
      0x48, 0x8B, 0x05, 0x11, 0x60, 0x04, 0x03};
  constexpr std::array<std::uint8_t, 7> kApply{
      0x48, 0x89, 0x54, 0x24, 0x10, 0x48, 0x89};
  constexpr std::array<std::uint8_t, 7> kEnumerate{
      0x48, 0x89, 0x5C, 0x24, 0x18, 0x55, 0x56};
  constexpr std::array<std::uint8_t, 7> kIdentityCopy{
      0x48, 0x8B, 0x07, 0x49, 0x89, 0x84, 0x24};
  return environment.enabled && environment.module_base != 0 &&
         (environment.admitted_executable_sha256 ==
              kActivityHostedIdentityExeSha256V1 || Is12002(environment)) &&
         environment.read_memory != nullptr &&
         environment.read_frame != nullptr &&
         (Is12002(environment)
              ? MatchCode(environment, 0x2ADD8EE,
                          std::array<std::uint8_t, 7>{0x49, 0x8D, 0xBF, 0xB8,
                                                       0x2C, 0x02, 0x00}) &&
                    MatchCode(environment, 0x29C2E97,
                              std::array<std::uint8_t, 7>{0x48, 0x81, 0xC3, 0x28,
                                                           0x06, 0x00, 0x00}) &&
                    MatchCode(environment, 0x23F0195,
                              std::array<std::uint8_t, 7>{0x41, 0x89, 0x87, 0xA8,
                                                           0x03, 0x00, 0x00})
              : MatchCode(environment, 0x26C8050, kDispatch) &&
         MatchCode(environment, 0x2700340, kApply) &&
         MatchCode(environment, 0x2703AF0, kEnumerate) &&
         MatchCode(environment, 0x218EE1F, kIdentityCopy));
}

bool ReadManager(const ActivityHostedIdentityEnvironmentV1 &environment,
                 std::uintptr_t manager, ManagerSample &sample) noexcept {
  std::uint8_t initialized = 0, changing = 0, clearing = 0;
  if (!ReadAt(environment, manager, 0x10, initialized) ||
      !ReadAt(environment, manager, 0x60, changing) ||
      !ReadAt(environment, manager, 0x61, clearing) || initialized == 0 ||
      changing != 0 || clearing != 0 ||
      !ReadAt(environment, manager, 0x20, sample.chunks) ||
      !ReadAt(environment, manager, 0x2C, sample.chunk_count) ||
      !ReadAt(environment, manager, 0x38, sample.index_table) ||
      !ReadAt(environment, manager, 0x44, sample.capacity) ||
      !ReadAt(environment, manager, 0x50, sample.highest_live) ||
      !ReadAt(environment, manager, 0x54, sample.active_count))
    return false;
  if (sample.active_count == 0)
    return sample.highest_live == -1;
  return sample.chunks != 0 && sample.index_table != 0 &&
         sample.chunk_count != 0 && sample.capacity != 0 &&
         sample.capacity <= kMaximumSlotIndex + 1 &&
         sample.highest_live >= 0 &&
         static_cast<std::uint32_t>(sample.highest_live) < sample.capacity &&
         sample.active_count <=
             static_cast<std::uint32_t>(sample.highest_live) + 1 &&
         sample.chunk_count >
             static_cast<std::uint32_t>(sample.highest_live) / kSlotsPerChunk;
}

bool ResolveActor(const ActivityHostedIdentityEnvironmentV1 &environment,
                  std::uint32_t full_id) noexcept {
  std::uint32_t played_id = 0;
  std::uintptr_t storage = 0, fallback = 0, slots = 0, character = 0;
  std::uint32_t capacity = 0, observed_id = 0;
  const bool current = Is12002(environment);
  // The admitted frame is captured by the existing native played-character
  // resolver. 1.20 does not read the old build's UI-selected CharacterID slot.
  if ((!current &&
       (!ReadAt(environment, environment.module_base, kPlayedCharacterIdRva,
                played_id) || played_id != full_id)) ||
      !ReadAt(environment, environment.module_base,
              current ? kActivityHosted12002CharacterStorageRva : kCharacterStorageRva,
              storage) ||
      !ReadAt(environment, environment.module_base,
              current ? kActivityHosted12002CharacterFallbackRva : kCharacterFallbackRva,
              fallback) ||
      storage == 0 || !ReadAt(environment, storage, 0x20, slots) ||
      !ReadAt(environment, storage, 0x2C, capacity) || slots == 0 ||
      (full_id & 0x00FFFFFFU) >= capacity ||
      !ReadAt(environment, slots,
              static_cast<std::size_t>(full_id & 0x00FFFFFFU) * 16 + 8,
              character) ||
      character == 0 || character == fallback ||
      !ReadAt(environment, character, 0x18, observed_id))
    return false;
  return observed_id == full_id;
}

bool ReadTypeKey(const ActivityHostedIdentityEnvironmentV1 &environment,
                 std::uintptr_t type, ActivityHostedIdentityV1 &identity) noexcept {
  std::uintptr_t vtable = 0, data = 0;
  std::uint64_t size = 0, capacity = 0;
  if (type == 0 || !ReadAt(environment, type, 0, vtable) ||
      vtable != environment.module_base +
          (Is12002(environment) ? kActivityHosted12002ActivityTypeVtableRva : kActivityTypeVtableRva) ||
      !ReadAt(environment, type, 0x28, size) ||
      !ReadAt(environment, type, 0x30, capacity) || size == 0 ||
      size > capacity || size >= identity.type_key.size() ||
      !CheckedAdd(type, 0x18, data))
    return false;
  if (capacity > 15 && !ReadAt(environment, type, 0x18, data)) return false;
  if (!Read(environment, data, identity.type_key.data(),
            static_cast<std::size_t>(size)))
    return false;
  for (std::size_t index = 0; index < size; ++index) {
    const char ch = identity.type_key[index];
    if (!((ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9') || ch == '_'))
      return false;
  }
  identity.type_key_size = static_cast<std::uint8_t>(size);
  return true;
}

bool ReadSlot(const ActivityHostedIdentityEnvironmentV1 &environment,
              const ManagerSample &manager, std::uint32_t index,
              std::uintptr_t &object) noexcept {
  object = 0;
  if (!ReadAt(environment, manager.index_table,
              static_cast<std::size_t>(index) * 16 + 8, object))
    return false;
  if (object == 0) return true;
  const auto chunk_index = index / kSlotsPerChunk;
  std::uintptr_t chunk = 0, expected = 0;
  return chunk_index < manager.chunk_count &&
         ReadAt(environment, manager.chunks,
                static_cast<std::size_t>(chunk_index) * 8, chunk) &&
         CheckedAdd(chunk,
                    static_cast<std::size_t>(index % kSlotsPerChunk) *
                        (Is12002(environment) ? kActivityHosted12002ObjectStride : kActivityStride),
                    expected) &&
         object == expected;
}

} // namespace

ActivityHostedIdentityResultV1 ReadActivityHostedIdentityV1(
    const ActivityHostedIdentityEnvironmentV1 &environment,
    const ActivityHostedIdentityFrameV1 &expected) noexcept {
  ActivityHostedIdentityResultV1 result{};
  result.frame = expected;
  if (!VerifyExactBuild(environment)) return result;
  ActivityHostedIdentityFrameV1 before{};
  if (expected.revision == 0 || expected.actor_character_id <= 0 ||
      !expected.paused || !expected.application_main_thread ||
      !expected.map_ready || !expected.actor_alive ||
      !environment.read_frame(environment.context, before) ||
      before != expected) {
    result.status = ActivityHostedIdentityStatusV1::frame_rejected;
    return result;
  }
  if (!ResolveActor(environment,
                    static_cast<std::uint32_t>(expected.actor_character_id))) {
    result.status = ActivityHostedIdentityStatusV1::actor_identity_unavailable;
    return result;
  }
  std::uintptr_t root = 0, world = 0, manager = 0;
  ManagerSample first{};
  if (!ReadAt(environment, environment.module_base, (Is12002(environment) ? kActivityHosted12002GameStateRva : kManagerRootRva), root) ||
      root == 0 || !ReadAt(environment, root, 0xA0, world) ||
      !CheckedAdd(world, Is12002(environment) ? kActivityHosted12002ManagerOffset : 0x1DEC0, manager) ||
      !ReadManager(environment, manager, first)) {
    result.status = ActivityHostedIdentityStatusV1::manager_unavailable;
    return result;
  }
  std::uint32_t seen = 0;
  if (first.active_count != 0) {
    for (std::uint32_t index = 0;
         index <= static_cast<std::uint32_t>(first.highest_live); ++index) {
      std::uintptr_t activity = 0;
      if (!ReadSlot(environment, first, index, activity)) {
        result.status = ActivityHostedIdentityStatusV1::activity_identity_unavailable;
        return result;
      }
      if (activity == 0) continue;
      ++seen;
      std::uint32_t id = 0;
      std::int32_t host_id = -1;
      if (!ReadAt(environment, activity, 0x08, id) ||
          id == 0xFFFFFFFFU || (id & 0x00FFFFFFU) != index ||
          !ReadAt(environment, activity, 0x3A8, host_id)) {
        result.status = ActivityHostedIdentityStatusV1::activity_identity_unavailable;
        return result;
      }
      if (host_id != expected.actor_character_id) continue;
      if (result.hosted_count == result.hosted.size()) {
        result.status = ActivityHostedIdentityStatusV1::output_capacity_exceeded;
        return result;
      }
      auto &identity = result.hosted[result.hosted_count];
      std::uintptr_t vtable = 0, type = 0, row_again = 0;
      if (!ReadAt(environment, activity, 0, vtable) ||
          vtable != environment.module_base +
              (Is12002(environment) ? kActivityHosted12002ActivityVtableRva : kActivityVtableRva) ||
          !ReadAt(environment, activity, 0x3A0, type) ||
          !ReadTypeKey(environment, type, identity) ||
          !ReadSlot(environment, first, index, row_again) ||
          row_again != activity) {
        result.status = ActivityHostedIdentityStatusV1::activity_identity_unavailable;
        return result;
      }
      identity.activity_id = id;
      identity.host_character_id = host_id;
      if (Is12002(environment)) {
        std::uint8_t complete = 0, invalidated = 0;
        if (!ReadAt(environment, activity, 0x421, complete) ||
            !ReadAt(environment, activity, 0x422, invalidated) ||
            complete > 1 || invalidated > 1) {
          result.status = ActivityHostedIdentityStatusV1::activity_identity_unavailable;
          return result;
        }
        identity.terminal_flags_observed = true;
        identity.native_completed = complete != 0;
        identity.native_invalidated = invalidated != 0;
      }
      ++result.hosted_count;
    }
  }
  ManagerSample last{};
  ActivityHostedIdentityFrameV1 after{};
  std::uintptr_t root_after = 0, world_after = 0;
  if (seen != first.active_count ||
      !ReadAt(environment, environment.module_base, (Is12002(environment) ? kActivityHosted12002GameStateRva : kManagerRootRva),
              root_after) ||
      root_after != root || !ReadAt(environment, root_after, 0xA0,
                                   world_after) ||
      world_after != world || !ReadManager(environment, manager, last) ||
      last != first || !environment.read_frame(environment.context, after) ||
      after != expected) {
    result.status = ActivityHostedIdentityStatusV1::snapshot_changed;
    return result;
  }
  result.manager_active_count = seen;
  result.status = ActivityHostedIdentityStatusV1::observed;
  return result;
}

} // namespace xar::bridge
