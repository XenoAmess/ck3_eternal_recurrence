#include "xar_bridge/army_position_2c3a0e0_readonly_12004.hpp"

#include <limits>

namespace xar::ck3_12004 {
namespace {
constexpr std::uint32_t kCharacterTag = 0x43686172U;
constexpr std::uint32_t kInvalidId = 0xFFFFFFFFU;
constexpr std::uintptr_t kFallbackSlot = 0x5C67570U;

template <typename T>
bool ReadField(const ArmyRegularCoreReadonlyAccess12004 &access,
               std::uintptr_t object, std::uintptr_t offset, T &value) noexcept {
  return access.read != nullptr && object != 0 &&
         offset <= std::numeric_limits<std::uintptr_t>::max() - object &&
         access.read(access.read_context, object + offset, &value, sizeof(value));
}

struct Step {
  std::optional<std::uintptr_t> value;
  const char *reason;
};

// Literal reads of the actual 28BFCD0 leaf. A read failure stays unknown;
// only the native null state branch selects the actual loaded fallback slot.
Step ReadStep(const ArmyRegularCoreReadonlyAccess12004 &access,
              std::uintptr_t object) noexcept {
  std::uintptr_t state = 0;
  if (!ReadField(access, object, 0x1C0U, state))
    return {{}, "hierarchy_state_unreadable"};
  if (state == 0) {
    std::uintptr_t fallback = 0;
    if (!ReadField(access, access.image_base, kFallbackSlot, fallback))
      return {{}, "loaded_hierarchy_fallback_unreadable"};
    return {fallback, ""};
  }

  std::uintptr_t intermediate = 0;
  std::uintptr_t candidate = 0;
  std::uint32_t kind = 0;
  std::uint32_t id = 0;
  if (!ReadField(access, state, 0x1C8U, intermediate) ||
      !ReadField(access, intermediate, 0x28U, candidate) ||
      !ReadField(access, candidate, 0x1CU, kind))
    return {{}, "hierarchy_candidate_unreadable"};
  if (kind != kCharacterTag)
    return {object, ""};
  if (!ReadField(access, candidate, 0x18U, id))
    return {{}, "hierarchy_candidate_id_unreadable"};
  if (id == kInvalidId)
    return {object, ""};

  std::uintptr_t alternate_state = 0;
  if (!ReadField(access, candidate, 0x1D0U, alternate_state))
    return {{}, "hierarchy_candidate_alternate_state_unreadable"};
  if (alternate_state != 0)
    return {object, ""};
  std::uintptr_t candidate_state = 0;
  if (!ReadField(access, candidate, 0x1C0U, candidate_state))
    return {{}, "hierarchy_candidate_state_unreadable"};
  if (candidate_state == 0)
    return {object, ""};
  std::uintptr_t secondary_state = 0;
  std::uintptr_t secondary = 0;
  if (!ReadField(access, candidate_state, 0x1C0U, secondary_state) ||
      !ReadField(access, secondary_state, 0x28U, secondary) ||
      !ReadField(access, secondary, 0x1CU, kind))
    return {{}, "hierarchy_secondary_unreadable"};
  if (kind != kCharacterTag)
    return {candidate, ""};
  if (!ReadField(access, secondary, 0x18U, id))
    return {{}, "hierarchy_secondary_id_unreadable"};
  return {id == kInvalidId ? candidate : object, ""};
}

ArmyRegularCoreReadonlyPredicate12004 Unknown(const char *reason) {
  return {{}, reason};
}
} // namespace

ArmyRegularCoreReadonlyPredicate12004 ReadArmyPosition2C3A0E012004(
    const ArmyRegularCoreReadonlyAccess12004 &access,
    std::uintptr_t holder, std::uintptr_t actor) noexcept {
  if (access.read == nullptr)
    return Unknown("readonly_reader_unavailable");
  std::uintptr_t current = holder;
  for (std::size_t occurrence = 0; occurrence < access.maximum_occurrences;
       ++occurrence) {
    const Step first = ReadStep(access, current);
    if (!first.value)
      return Unknown(first.reason);
    std::uint32_t kind = 0;
    std::uint32_t first_id = 0;
    if (!ReadField(access, *first.value, 0x1CU, kind))
      return Unknown("returned_character_kind_unreadable");
    if (kind != kCharacterTag)
      return {false, ""};
    if (!ReadField(access, *first.value, 0x18U, first_id))
      return Unknown("returned_character_id_unreadable");
    if (first_id == kInvalidId || current == *first.value)
      return {false, ""};

    if (current != actor) {
      // The source calls 28BFCD0 a second time, independently. Do not reuse
      // first.value: real guarded reads may return a different current value.
      const Step second = ReadStep(access, current);
      if (!second.value)
        return Unknown(second.reason);
      if (!ReadField(access, *second.value, 0x1CU, kind))
        return Unknown("second_character_kind_unreadable");
      if (kind == kCharacterTag) {
        std::uint32_t second_id = 0;
        if (!ReadField(access, *second.value, 0x18U, second_id))
          return Unknown("second_character_id_unreadable");
        if (second_id != kInvalidId) {
          std::uint32_t actor_id = 0;
          if (!ReadField(access, actor, 0x18U, actor_id))
            return Unknown("actor_full_id_unreadable");
          if (second_id == actor_id) {
            std::uintptr_t state = 0;
            if (!ReadField(access, current, 0x1C0U, state))
              return Unknown("activity_state_unreadable");
            std::uint32_t count = 0;
            if (state != 0) {
              if (!ReadField(access, state, 0x1ECU, count))
                return Unknown("activity_state_count_unreadable");
              if (count != 0)
                return {true, ""};
            } else {
              if (!ReadField(access, current, 0x1D0U, state))
                return Unknown("alternate_activity_state_unreadable");
              if (state != 0) {
                if (!ReadField(access, state, 0x74U, count))
                  return Unknown("alternate_activity_count_unreadable");
                if (count != 0)
                  return {true, ""};
              }
            }
          }
        }
      }
    }
    current = *first.value;
  }
  return Unknown("hierarchy_occurrence_limit_reached");
}
} // namespace xar::ck3_12004
