#include "xar_bridge/army_position_relation_28b2800_12004.hpp"

namespace xar::ck3_12004 {
namespace {
constexpr std::uint32_t kChar = 0x43686172U;
constexpr std::uint32_t kSentinel = 0xFFFFFFFFU;

template <class T>
bool Copy(const ArmyRegularCoreReadonlyAccess12004 &access,
          std::uintptr_t address, T &value) noexcept {
  return access.read(access.read_context, address, &value, sizeof(value));
}

ArmyRegularCoreReadonlyPredicate12004 Unknown(const char *reason) {
  return {std::nullopt, reason};
}

// Complete cached118B28BFC50. Both receiver pointers are preloaded, even
// when1C0 selects the linked-carrier branch. Native miss usesactual fallback.
bool NextCharacter(const ArmyRegularCoreReadonlyAccess12004 &access,
                   std::uintptr_t character, std::uintptr_t &selected,
                   std::uintptr_t &carrier, std::size_t &selector_calls) noexcept {
  if (selector_calls >= access.maximum_occurrences) return false;
  ++selector_calls;
  std::uintptr_t link = 0;
  if (!Copy(access, character + 0x1C0, carrier) ||
      !Copy(access, character + 0x1B8, link)) return false;
  if (carrier != 0) {
    std::uintptr_t relation = 0, candidate = 0;
    std::uint32_t magic = 0, id = 0;
    if (!Copy(access, carrier + 0x1C0, relation) ||
        !Copy(access, relation + 0x28, candidate) ||
        !Copy(access, candidate + 0x1C, magic)) return false;
    selected = character;
    if (magic != kChar) return true;
    if (!Copy(access, candidate + 0x18, id)) return false;
    if (id != kSentinel) selected = candidate;
    return true;
  }
  if (link != 0) {
    std::uintptr_t store = 0;
    if (!Copy(access, access.image_base + 0x5C67568, store)) return false;
    if (store != 0) {
      std::uint32_t id = 0, count = 0;
      if (!Copy(access, link + 0xC8, id) ||
          !Copy(access, store + 0x2C, count)) return false;
      const auto index = id & 0x00FFFFFFU;
      if (index < count) {
        std::uintptr_t table = 0, candidate = 0;
        if (!Copy(access, store + 0x20, table) ||
            !Copy(access, table + std::uintptr_t{index} * 16 + 8, candidate))
          return false;
        if (candidate != 0) {
          std::uint32_t complete_id = 0;
          if (!Copy(access, candidate + 0x18, complete_id)) return false;
          if (complete_id == id) { selected = candidate; return true; }
        }
      }
    }
  }
  if (!Copy(access, access.image_base + 0x5C67570, selected)) return false;
  return selected != 0;
}

bool CandidateIdentity(const ArmyRegularCoreReadonlyAccess12004 &access,
                       std::uintptr_t candidate, std::uint32_t &id,
                       bool &valid) noexcept {
  std::uint32_t magic = 0;
  if (!Copy(access, candidate + 0x1C, magic)) return false;
  valid = false;
  if (magic != kChar) return true;
  if (!Copy(access, candidate + 0x18, id)) return false;
  valid = id != kSentinel;
  return true;
}

} // namespace

ArmyRegularCoreReadonlyPredicate12004 ReadArmyPosition28B280012004(
    const ArmyRegularCoreReadonlyAccess12004 &access,
    std::uintptr_t holder, std::int32_t target_full_id) noexcept {
  if (access.read == nullptr || access.image_base == 0 || holder == 0)
    return Unknown("position_relation_access_unavailable");
  const auto target = static_cast<std::uint32_t>(target_full_id);
  std::uint32_t receiver_id = 0;
  if (!Copy(access, holder + 0x18, receiver_id))
    return Unknown("position_relation_receiver_id_unread");
  // Strict predicate deliberately returnsfalse for receiver==soughtID.
  if (receiver_id == target) return {false, {}};
  std::uintptr_t current = holder;
  std::size_t selector_calls = 0;
  for (;;) {
    std::uintptr_t candidate = 0, carrier = 0;
    if (!NextCharacter(access, current, candidate, carrier, selector_calls))
      return Unknown("position_relation_selector_fields_or_budget_unavailable");
    // The outer predicate reads this field again after its selector call.
    if (!Copy(access, current + 0x1C0, carrier))
      return Unknown("position_relation_outer_carrier_unread");
    if (carrier == 0) {
      std::uint32_t id = 0, current_id = 0;
      bool valid = false;
      if (!CandidateIdentity(access, candidate, id, valid))
        return Unknown("position_relation_candidate_identity_unread");
      if (!valid) return {false, {}};
      if (!Copy(access, current + 0x18, current_id))
        return Unknown("position_relation_current_identity_unread");
      if (id == current_id) return {false, {}};
      if (id == target) return {true, {}};
      current = candidate;
      // Nativezero1C0 branch has no numericiteration limit. Guarded-read
      // budget exhaustion remainsunknown rather than inventing nativefalse.
      continue;
    }
    // Native nonzero1C0 branch tests at most seven candidate IDs. Each
    // unmatched comparison obtains the next candidate before the countertest.
    for (std::size_t compared = 0; compared < 7; ++compared) {
      std::uint32_t id = 0;
      bool valid = false;
      if (!CandidateIdentity(access, candidate, id, valid))
        return Unknown("position_relation_bounded_candidate_identity_unread");
      if (!valid) return {false, {}};
      if (id == target) return {true, {}};
      std::uintptr_t next = 0, ignored_carrier = 0;
      if (!NextCharacter(access, candidate, next, ignored_carrier, selector_calls))
        return Unknown("position_relation_bounded_selector_fields_or_budget_unavailable");
      std::uint32_t next_id = 0;
      if (!Copy(access, next + 0x18, next_id))
        return Unknown("position_relation_bounded_next_id_unread");
      if (next_id == id) return {false, {}};
      candidate = next;
    }
    return {false, {}};
  }
}

} // namespace xar::ck3_12004
