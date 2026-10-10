#include "xar_bridge/army_position_2c09410_12004.hpp"

#include "xar_bridge/army_position_2c09280_12004.hpp"
#include "xar_bridge/army_position_war_membership_12004.hpp"
#include <limits>

namespace xar::ck3_12004 {
namespace {

constexpr std::uintptr_t kDefaultListDescriptor = 0x5459D38;
constexpr std::uintptr_t kRecordStorageSlot = 0x5D1DE58;
constexpr std::uintptr_t kRecordFallbackSlot = 0x5D1DE40;
constexpr std::uintptr_t kCharacterStorageSlot = 0x5C67568;
constexpr std::uintptr_t kCharacterFallbackSlot = 0x5C67570;

template <class T>
bool Read(const ArmyRegularCoreReadonlyAccess12004 &access,
          std::uintptr_t address, T &output) noexcept {
  return address != 0 && access.read != nullptr &&
         access.read(access.read_context, address, &output, sizeof(output));
}

bool Add(std::uintptr_t address, std::uintptr_t offset,
         std::uintptr_t &result) noexcept {
  if (address > std::numeric_limits<std::uintptr_t>::max() - offset) return false;
  result = address + offset;
  return true;
}

struct Resolved {
  bool available = false;
  std::uintptr_t object = 0;
};

Resolved Candidate(const ArmyRegularCoreReadonlyAccess12004 &access,
                   std::uint32_t requested_id, std::uintptr_t storage,
                   std::uintptr_t id_offset) noexcept {
  if (storage != 0) {
    std::uint32_t capacity = 0;
    if (!Read(access, storage + 0x2C, capacity)) return {};
    const std::uint32_t index = requested_id & 0x00FFFFFF;
    if (index < capacity) {
      std::uintptr_t slots = 0, candidate = 0, slot = 0;
      if (!Read(access, storage + 0x20, slots) || slots == 0 ||
          !Add(slots, static_cast<std::uintptr_t>(index) * 0x10 + 8, slot) ||
          !Read(access, slot, candidate)) return {};
      if (candidate != 0) {
        std::uint32_t candidate_id = 0;
        if (!Read(access, candidate + id_offset, candidate_id)) return {};
        if (candidate_id == requested_id) return {true, candidate};
      }
    }
  }
  return {true, 0};
}

struct RecordRegistry {
  std::uintptr_t storage = 0;
  std::uintptr_t fallback = 0;
};

bool ReadRecordRegistry(const ArmyRegularCoreReadonlyAccess12004 &access,
                        RecordRegistry &registry) noexcept {
  std::uintptr_t storage_slot = 0, fallback_slot = 0;
  return Add(access.image_base, kRecordStorageSlot, storage_slot) &&
         Add(access.image_base, kRecordFallbackSlot, fallback_slot) &&
         Read(access, storage_slot, registry.storage) &&
         Read(access, fallback_slot, registry.fallback);
}

Resolved ResolveRecord(const ArmyRegularCoreReadonlyAccess12004 &access,
                       std::uint32_t requested_id,
                       const RecordRegistry &registry) noexcept {
  auto result = Candidate(access, requested_id, registry.storage, 8);
  if (!result.available) return {};
  if (result.object == 0) result.object = registry.fallback;
  result.available = result.object != 0;
  return result;
}

// Character fallback is read only after native candidate rejection.
Resolved ResolveCharacter(const ArmyRegularCoreReadonlyAccess12004 &access,
                          std::uint32_t requested_id) noexcept {
  std::uintptr_t storage_slot = 0, fallback_slot = 0, storage = 0;
  if (!Add(access.image_base, kCharacterStorageSlot, storage_slot) ||
      !Add(access.image_base, kCharacterFallbackSlot, fallback_slot) ||
      !Read(access, storage_slot, storage)) return {};
  auto result = Candidate(access, requested_id, storage, 0x18);
  if (!result.available || result.object != 0) return result;
  if (!Read(access, fallback_slot, result.object)) return {};
  result.available = result.object != 0;
  return result;
}

ArmyRegularCoreReadonlyPredicate12004 Unavailable(const char *reason) {
  return {std::nullopt, reason};
}

ArmyRegularCoreReadonlyPredicate12004 ReadImpl(
    const ArmyRegularCoreReadonlyAccess12004 &access,
    std::uintptr_t actor, std::uintptr_t holder,
    std::uintptr_t record_filter) {
  if (access.image_base == 0 || access.read == nullptr || actor == 0)
    return Unavailable("army_position_2c09410_unbound_context");
  std::uintptr_t actor_data = 0, descriptor = 0, data = 0;
  std::int32_t count = 0;
  if (!Read(access, actor + 0x1C0, actor_data))
    return Unavailable("army_position_2c09410_actor_list_pointer_unavailable");
  if (!Add(actor_data != 0 ? actor_data : access.image_base,
           actor_data != 0 ? 0x318 : kDefaultListDescriptor, descriptor) ||
      !Read(access, descriptor, data) || !Read(access, descriptor + 0xC, count))
    return Unavailable("army_position_2c09410_list_descriptor_unavailable");
  if (count == 0) return {false, {}};
  if (count < 0 || static_cast<std::size_t>(count) > access.maximum_occurrences || data == 0)
    return Unavailable("army_position_2c09410_list_not_bounded_complete");
  RecordRegistry record_registry;
  if (!ReadRecordRegistry(access, record_registry))
    return Unavailable("army_position_2c09410_record_registry_unavailable");
  for (std::int32_t i = 0; i < count; ++i) {
    std::uintptr_t occurrence = 0;
    std::uint32_t record_id = 0;
    if (!Add(data, static_cast<std::uintptr_t>(i) * 4, occurrence) ||
        !Read(access, occurrence, record_id))
      return Unavailable("army_position_2c09410_record_id_unavailable");
    const auto record = ResolveRecord(access, record_id, record_registry);
    if (!record.available)
      return Unavailable("army_position_2c09410_record_resolution_unavailable");
    if (record_filter != 0) {
      std::uint32_t filter_id = 0, resolved_id = 0;
      if (!Read(access, record_filter + 8, filter_id) ||
          !Read(access, record.object + 8, resolved_id))
        return Unavailable("army_position_2c09410_record_filter_unavailable");
      if (filter_id != resolved_id) continue;
    }
    std::int32_t actor_id = 0;
    if (!Read(access, actor + 0x18, actor_id))
      return Unavailable("army_position_2c09410_actor_full_id_unavailable");
    auto member = ReadArmyPosition2494B4012004(access, record.object + 0x20, actor_id);
    if (!member.value.has_value()) return member;
    std::uint32_t opposite_id = 0xFFFFFFFF;
    if (*member.value) {
      if (!Read(access, record.object + 0x28C, opposite_id))
        return Unavailable("army_position_2c09410_side20_opposite_id_unavailable");
    } else {
      member = ReadArmyPosition2494B4012004(access, record.object + 0x80, actor_id);
      if (!member.value.has_value()) return member;
      if (*member.value && !Read(access, record.object + 0x288, opposite_id))
        return Unavailable("army_position_2c09410_side80_opposite_id_unavailable");
    }
    const auto opposing = ResolveCharacter(access, opposite_id);
    if (!opposing.available)
      return Unavailable("army_position_2c09410_opposing_character_resolution_unavailable");
    const auto relation = ReadArmyPosition2C0928012004(access, opposing.object, holder, 0);
    if (!relation.value.has_value()) return relation;
    if (*relation.value) return {true, {}};
    // Native2C09538/3F reload both slots after false, including the last call.
    // Filter-only skips retain the previous slots exactly as native2C09546.
    if (!ReadRecordRegistry(access, record_registry))
      return Unavailable("army_position_2c09410_record_registry_refresh_unavailable");
  }
  return {false, {}};
}
} // namespace

ArmyRegularCoreReadonlyPredicate12004 ReadArmyPosition2C0941012004(
    const ArmyRegularCoreReadonlyAccess12004 &access,
    std::uintptr_t actor, std::uintptr_t holder,
    std::uintptr_t record_filter) noexcept {
  try {
    return ReadImpl(access, actor, holder, record_filter);
  } catch (...) {
    return {std::nullopt, "army_position_2c09410_collection_failed"};
  }
}
} // namespace xar::ck3_12004
