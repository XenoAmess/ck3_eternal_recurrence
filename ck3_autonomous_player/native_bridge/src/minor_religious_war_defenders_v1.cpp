#include "xar_bridge/minor_religious_war_defenders_v1.hpp"

#include "xar_bridge/war_entry_assessments_v1.hpp"

#include <array>
#include <cstring>
#include <limits>

#if defined(_WIN32)
#include <windows.h>
#endif

namespace xar::ck3_11906 {
namespace {

constexpr std::size_t kIdentityOffset = 0x18;
constexpr std::size_t kPowerContainerOffset = 0x1B8;
constexpr std::size_t kPowerRawOffset = 0x308;
constexpr std::size_t kStoreSlotsOffset = 0x20;
constexpr std::size_t kStoreCapacityOffset = 0x2C;
constexpr std::size_t kSlotStride = 0x10;
constexpr std::size_t kSlotObjectOffset = 0x08;
constexpr std::int32_t kMaximumStoreCapacity = 4'194'304;
constexpr std::int32_t kMaximumProspectiveJoiners = 64;

bool DirectRead(const void *address, void *out, std::size_t size) noexcept {
  if (address == nullptr || out == nullptr || size == 0) return false;
#if defined(_MSC_VER)
  __try {
    std::memcpy(out, address, size);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  std::memcpy(out, address, size);
  return true;
#endif
}

bool Read(const MinorReligiousDefenderAccessV1 &access, const void *address,
          void *out, std::size_t size) noexcept {
  return access.read_memory == nullptr
             ? DirectRead(address, out, size)
             : access.read_memory(access.context, address, out, size);
}

template <typename T>
bool At(const MinorReligiousDefenderAccessV1 &access, const void *base,
        std::size_t offset, T &out) noexcept {
  if (base == nullptr ||
      reinterpret_cast<std::uintptr_t>(base) >
          std::numeric_limits<std::uintptr_t>::max() - offset) {
    return false;
  }
  return Read(access, reinterpret_cast<const void *>(
                          reinterpret_cast<std::uintptr_t>(base) + offset),
              &out, sizeof(out));
}

bool IsBound(const MinorReligiousDefenderEnvironmentV1 &env) noexcept {
  if (env.collector == nullptr || env.allocator == nullptr ||
      env.character_storage_slot == nullptr ||
      env.character_fallback_slot == nullptr) {
    return false;
  }
  return env.offline_fixture_overrides
             ? env.fixture_free != nullptr
             : env.module_base != 0 &&
                   reinterpret_cast<std::uintptr_t>(env.collector) ==
                       env.module_base + kMinorReligiousDefenderCollectorRvaV1 &&
                   reinterpret_cast<std::uintptr_t>(env.allocator) ==
                       env.module_base + kMinorReligiousDefenderAllocatorRvaV1 &&
                   reinterpret_cast<std::uintptr_t>(env.character_storage_slot) ==
                       env.module_base + kWarEntryCharacterStorageSlotRva &&
                   reinterpret_cast<std::uintptr_t>(env.character_fallback_slot) ==
                       env.module_base + kWarEntryCharacterFallbackSlotRva;
}

void *ResolveCharacter(const MinorReligiousDefenderEnvironmentV1 &env,
                       const MinorReligiousDefenderAccessV1 &access,
                       std::int32_t full_id) noexcept {
  if (full_id <= 0) return nullptr;
  void *store = nullptr;
  void *fallback = nullptr;
  if (!Read(access, env.character_storage_slot, &store, sizeof(store)) ||
      !Read(access, env.character_fallback_slot, &fallback, sizeof(fallback)) ||
      store == nullptr) {
    return nullptr;
  }
  void *slots = nullptr;
  std::int32_t capacity = 0;
  if (!At(access, store, kStoreSlotsOffset, slots) ||
      !At(access, store, kStoreCapacityOffset, capacity) || slots == nullptr ||
      capacity <= 0 || capacity > kMaximumStoreCapacity) {
    return nullptr;
  }
  const auto index = static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  void *character = nullptr;
  std::int32_t identity = -1;
  if (!At(access, slots, static_cast<std::size_t>(index) * kSlotStride +
                              kSlotObjectOffset, character) ||
      character == nullptr || character == fallback ||
      !At(access, character, kIdentityOffset, identity) ||
      identity != full_id) {
    return nullptr;
  }
  return character;
}

bool Invoke(MinorReligiousDefenderCollectorV1 collector, void *actor,
            void *defender, NativeCharacterPointerVectorV1 &out) noexcept {
#if defined(_MSC_VER)
  __try {
    collector(actor, defender, &out);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  collector(actor, defender, &out);
  return true;
#endif
}

bool NativeFree(MinorReligiousDefenderFreeV1 free_function,
                void *allocator, void *data) noexcept {
#if defined(_MSC_VER)
  __try {
    free_function(allocator, data, 8);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  free_function(allocator, data, 8);
  return true;
#endif
}

bool Release(const MinorReligiousDefenderEnvironmentV1 &env,
             const MinorReligiousDefenderAccessV1 &access,
             NativeCharacterPointerVectorV1 &value) noexcept {
  if (value.data == nullptr) return true;
  if (value.allocator != env.allocator) return false;
  auto free_function = env.fixture_free;
  if (!env.offline_fixture_overrides) {
    void **vtable = nullptr;
    if (!At(access, env.allocator, 0, vtable) || vtable == nullptr ||
        !At(access, vtable, 2 * sizeof(void *), free_function)) {
      return false;
    }
  }
  if (free_function == nullptr ||
      !NativeFree(free_function, value.allocator, value.data)) {
    return false;
  }
  value.data = nullptr;
  value.count = 0;
  value.capacity = 0;
  return true;
}

}  // namespace

MinorReligiousDefenderEnvironmentV1 BindMinorReligiousDefenderEnvironmentV1(
    std::uintptr_t module_base) noexcept {
  MinorReligiousDefenderEnvironmentV1 out{};
  if (module_base == 0) return out;
  out.module_base = module_base;
  out.character_storage_slot = reinterpret_cast<void **>(
      module_base + kWarEntryCharacterStorageSlotRva);
  out.character_fallback_slot = reinterpret_cast<void **>(
      module_base + kWarEntryCharacterFallbackSlotRva);
  out.allocator = reinterpret_cast<void *>(
      module_base + kMinorReligiousDefenderAllocatorRvaV1);
  out.collector = reinterpret_cast<MinorReligiousDefenderCollectorV1>(
      module_base + kMinorReligiousDefenderCollectorRvaV1);
  return out;
}

MinorReligiousDefenderReadbackV1 ReadMinorReligiousDefendersV1(
    const MinorReligiousDefenderEnvironmentV1 &env,
    const MinorReligiousDefenderAccessV1 &access, std::int32_t actor_id,
    std::int32_t primary_defender_id) noexcept {
  MinorReligiousDefenderReadbackV1 result{};
  if (!access.application_main_paused) {
    result.failure = MinorReligiousDefenderFailureV1::boundary;
    return result;
  }
  if (!IsBound(env)) return result;
  void *actor = ResolveCharacter(env, access, actor_id);
  void *defender = ResolveCharacter(env, access, primary_defender_id);
  if (actor == nullptr || defender == nullptr || actor == defender) {
    result.failure = MinorReligiousDefenderFailureV1::character;
    return result;
  }
  void *actor_power_container = nullptr;
  void *defender_power_container = nullptr;
  std::int64_t actor_power = -1;
  std::int64_t defender_power = -1;
  if (!At(access, actor, kPowerContainerOffset, actor_power_container) ||
      !At(access, defender, kPowerContainerOffset,
          defender_power_container) ||
      actor_power_container == nullptr || defender_power_container == nullptr ||
      !At(access, actor_power_container, kPowerRawOffset, actor_power) ||
      !At(access, defender_power_container, kPowerRawOffset, defender_power) ||
      actor_power < 0 || defender_power < 0) {
    result.failure = MinorReligiousDefenderFailureV1::power;
    return result;
  }
  NativeCharacterPointerVectorV1 native{};
  native.allocator = env.allocator;
  const bool invoked = Invoke(env.collector, actor, defender, native);
  auto fail = [&](MinorReligiousDefenderFailureV1 failure) {
    result.failure = Release(env, access, native)
                         ? failure : MinorReligiousDefenderFailureV1::cleanup;
    return result;
  };
  if (!invoked) return fail(MinorReligiousDefenderFailureV1::collector);
  if (native.allocator != env.allocator || native.count < 0 ||
      native.count > native.capacity ||
      native.count > kMaximumProspectiveJoiners ||
      (native.count > 0 && native.data == nullptr)) {
    return fail(MinorReligiousDefenderFailureV1::vector);
  }
  std::array<MinorReligiousDefenderRowV1, kMaximumProspectiveJoiners> rows{};
  std::int64_t total = 0;
  for (std::int32_t i = 0; i < native.count; ++i) {
    void *candidate = nullptr;
    std::int32_t id = -1;
    void *power_container = nullptr;
    std::int64_t power = -1;
    if (!At(access, native.data, static_cast<std::size_t>(i) * sizeof(void *),
            candidate) || candidate == nullptr ||
        !At(access, candidate, kIdentityOffset, id) || id <= 0 ||
        id == actor_id || id == primary_defender_id ||
        ResolveCharacter(env, access, id) != candidate) {
      return fail(MinorReligiousDefenderFailureV1::identity);
    }
    for (std::int32_t prior = 0; prior < i; ++prior) {
      if (rows[prior].character_id == id)
        return fail(MinorReligiousDefenderFailureV1::identity);
    }
    if (!At(access, candidate, kPowerContainerOffset, power_container) ||
        power_container == nullptr ||
        !At(access, power_container, kPowerRawOffset, power) || power < 0 ||
        total > std::numeric_limits<std::int64_t>::max() - power) {
      return fail(MinorReligiousDefenderFailureV1::power);
    }
    total += power;
    rows[static_cast<std::size_t>(i)] = {id, power};
  }
  const auto row_count = native.count;
  if (!Release(env, access, native)) {
    result.failure = MinorReligiousDefenderFailureV1::cleanup;
    return result;
  }
  try {
    result.prospective_joiners.assign(rows.begin(), rows.begin() + row_count);
  } catch (...) {
    result.failure = MinorReligiousDefenderFailureV1::vector;
    return result;
  }
  if (total > std::numeric_limits<std::int64_t>::max() - defender_power) {
    result.failure = MinorReligiousDefenderFailureV1::power;
    result.prospective_joiners.clear();
    return result;
  }
  result.actor_character_id = actor_id;
  result.primary_defender_character_id = primary_defender_id;
  result.actor_base_power_raw = actor_power;
  result.primary_defender_base_power_raw = defender_power;
  result.prospective_joiner_base_power_raw = total;
  result.primary_plus_joiner_base_power_raw = defender_power + total;
  result.failure = MinorReligiousDefenderFailureV1::none;
  return result;
}

}  // namespace xar::ck3_11906
