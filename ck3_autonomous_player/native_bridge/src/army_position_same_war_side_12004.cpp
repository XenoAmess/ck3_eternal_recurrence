#include "xar_bridge/army_position_same_war_side_12004.hpp"
#include "xar_bridge/army_position_war_membership_12004.hpp"

#include <bit>
#include <limits>
#include <string>
#include <utility>

namespace xar::ck3_12004 {
namespace {
constexpr std::uintptr_t kEmptyWarDescriptorRva = 0x5459D38;
constexpr std::uintptr_t kWarManagerSlotRva = 0x5D1DE58;
constexpr std::uintptr_t kWarFallbackSlotRva = 0x5D1DE40;

bool Address(std::uintptr_t base, std::uintptr_t offset,
             std::uintptr_t &result) noexcept {
  if (base == 0 || offset > std::numeric_limits<std::uintptr_t>::max() - base)
    return false;
  result = base + offset;
  return true;
}

template <class T>
bool Read(const ArmyRegularCoreReadonlyAccess12004 &access,
          std::uintptr_t base, std::uintptr_t offset, T &value) noexcept {
  std::uintptr_t address = 0;
  return access.read && Address(base, offset, address) &&
         access.read(access.read_context, address, &value, sizeof(value));
}

ArmyRegularCoreReadonlyPredicate12004 Unknown(std::string reason) {
  return {std::nullopt, std::move(reason)};
}

ArmyRegularCoreReadonlyPredicate12004 MembershipUnknown(
    const char *stage, const ArmyRegularCoreReadonlyPredicate12004 &result) {
  return Unknown(std::string("2C090D0 ") + stage + ": " +
                 (result.unavailable_reason.empty()
                      ? "participant membership unavailable"
                      : result.unavailable_reason));
}
} // namespace

ArmyRegularCoreReadonlyPredicate12004 ReadArmyPosition2C090D012004(
    const ArmyRegularCoreReadonlyAccess12004 &access,
    std::uintptr_t actor, std::uintptr_t holder,
    std::uintptr_t optional_war_identity) noexcept {
  // Literal initial setup reads holder before actor. Do not turn nullable or
  // unreadable Character input into a native false result.
  std::uint32_t holder_id = 0;
  std::uint32_t actor_id = 0;
  if (!Read(access, holder, 0x18, holder_id) ||
      !Read(access, actor, 0x18, actor_id))
    return Unknown("2C090D0 initial Character full ID unavailable");
  if (actor_id == holder_id)
    return {false, {}};

  std::uintptr_t domain = 0;
  if (!Read(access, actor, 0x1C0, domain))
    return Unknown("2C090D0 actor Domain pointer unavailable");
  std::uintptr_t descriptor = 0;
  if (!Address(domain ? domain : access.image_base,
               domain ? 0x318 : kEmptyWarDescriptorRva, descriptor))
    return Unknown("2C090D0 War-ID descriptor unavailable");

  std::uintptr_t war_ids = 0;
  std::int32_t war_count = 0;
  if (!Read(access, descriptor, 0, war_ids) ||
      !Read(access, descriptor, 0xC, war_count))
    return Unknown("2C090D0 War-ID descriptor operands unavailable");
  if (war_count == 0)
    return {false, {}};
  if (war_count < 0 ||
      static_cast<std::size_t>(war_count) > access.maximum_occurrences)
    return Unknown("2C090D0 War occurrence count outside supplied read bound");

  std::uintptr_t manager = 0;
  std::uintptr_t fallback = 0;
  const auto reload = [&]() noexcept {
    return Read(access, access.image_base, kWarManagerSlotRva, manager) &&
           Read(access, access.image_base, kWarFallbackSlotRva, fallback);
  };
  if (!reload())
    return Unknown("2C090D0 initial War manager/fallback slots unavailable");

  for (std::int32_t index = 0; index < war_count; ++index) {
    std::uintptr_t war = fallback;
    if (manager != 0) {
      std::uint32_t requested_id = 0;
      if (!Read(access, war_ids, static_cast<std::uintptr_t>(index) * 4,
                requested_id))
        return Unknown("2C090D0 requested War full ID unavailable");
      const auto slot_index = requested_id & 0xFFFFFFu;
      std::uint32_t capacity = 0;
      if (!Read(access, manager, 0x2C, capacity))
        return Unknown("2C090D0 War manager capacity unavailable");
      if (slot_index < capacity) {
        std::uintptr_t slots = 0;
        std::uintptr_t row = 0;
        if (!Read(access, manager, 0x20, slots) ||
            !Read(access, slots, static_cast<std::uintptr_t>(slot_index) * 16 + 8,
                  row))
          return Unknown("2C090D0 War manager row pointer unavailable");
        if (row != 0) {
          std::uint32_t actual_id = 0;
          if (!Read(access, row, 8, actual_id))
            return Unknown("2C090D0 resolved War full ID unavailable");
          if (actual_id == requested_id)
            war = row;
        }
      }
    }

    // Native filter mismatch goes straight to +4, bypassing both membership
    // and the two global-slot reloads. A null manager does not read a War ID.
    if (optional_war_identity != 0 && war != optional_war_identity)
      continue;
    if (!Read(access, actor, 0x18, actor_id))
      return Unknown("2C090D0 actor membership full ID unavailable");
    std::uintptr_t selected_side = 0;
    if (!Address(war, 0x20, selected_side))
      return Unknown("2C090D0 selected War identity unavailable");
    auto actor_member = ReadArmyPosition2494B4012004(
        access, selected_side, std::bit_cast<std::int32_t>(actor_id));
    if (!actor_member.value)
      return MembershipUnknown("attacker membership", actor_member);
    if (!*actor_member.value) {
      if (!Address(war, 0x80, selected_side))
        return Unknown("2C090D0 defender Side identity unavailable");
      actor_member = ReadArmyPosition2494B4012004(
          access, selected_side, std::bit_cast<std::int32_t>(actor_id));
      if (!actor_member.value)
        return MembershipUnknown("defender membership", actor_member);
    }
    if (*actor_member.value) {
      if (!Read(access, holder, 0x18, holder_id))
        return Unknown("2C090D0 holder membership full ID unavailable");
      const auto holder_member = ReadArmyPosition2494B4012004(
          access, selected_side, std::bit_cast<std::int32_t>(holder_id));
      if (!holder_member.value)
        return MembershipUnknown("holder membership", holder_member);
      if (*holder_member.value)
        return {true, {}};
    }
    // This reload occurs after false membership even on the final occurrence.
    if (!reload())
      return Unknown("2C090D0 continuation War manager/fallback slots unavailable");
  }
  return {false, {}};
}

} // namespace xar::ck3_12004
