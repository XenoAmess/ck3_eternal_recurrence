#include "xar_bridge/ck3_12003_player_holy_order_context.hpp"

#include <cstddef>
#include <cstring>
#include <sstream>
#include <utility>

#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12003::religion::holy_order {
namespace {
template <typename T>
bool Read(const void *object, std::size_t offset, T &value) noexcept {
  if (object == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(T));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
template <typename Fn, typename Result, typename... Args>
bool Call(Fn fn, Result &result, Args... args) noexcept {
  if (fn == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    result = fn(args...);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
void DestroyReason(ReasonDestroy fn, void *sink) noexcept {
  if (fn == nullptr) return;
#if defined(_MSC_VER)
  __try {
#endif
    fn(sink);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {}
#endif
}
class NativeReason {
 public:
  explicit NativeReason(ReasonDestroy destroy) noexcept : destroy_(destroy) {
    // The existing .3 reason sink ABI is a 32-byte small UTF-8 string.
    // Empty state matches native capacity15; native appends own heap data.
    const std::size_t capacity = 15;
    std::memcpy(bytes_.data() + 0x18, &capacity, sizeof(capacity));
  }
  ~NativeReason() { DestroyReason(destroy_, bytes_.data()); }
  NativeReason(const NativeReason &) = delete;
  NativeReason &operator=(const NativeReason &) = delete;
  void *get() noexcept { return bytes_.data(); }
  bool copy(std::string &text) const {
    std::size_t size = 0, capacity = 0;
    if (!Read(bytes_.data(), 0x10, size) || !Read(bytes_.data(), 0x18, capacity) ||
        size > capacity) return false;
    const char *data = reinterpret_cast<const char *>(bytes_.data());
    if (capacity >= 16 && !Read(bytes_.data(), 0, data)) return false;
    if (size != 0 && data == nullptr) return false;
    text.clear();
    for (std::size_t i = 0; i < size; ++i) {
      char value = 0;
      if (!Read(data, i, value)) return false;
      text.push_back(value);
    }
    return true;
  }
 private:
  alignas(8) std::array<std::byte, 0x20> bytes_{};
  ReasonDestroy destroy_ = nullptr;
};
std::optional<std::uint32_t> Identity(std::uint32_t raw) noexcept {
  return raw == UINT32_MAX ? std::nullopt : std::optional{raw};
}
bool ReadIdentity(const Bindings &b, void *order, Row &row) {
  std::uint32_t type = 0, founder = UINT32_MAX, employer = UINT32_MAX;
  const void *leases = nullptr;
  std::int32_t count = -1;
  if (!Read(order, 0x10, row.holy_order_id) ||
      !Read(order, 0x14, type) || type != 0x486F4F72U ||
      !Read(order, 0x24, row.rite_id) ||
      !Read(order, 0x40, founder) || !Read(order, 0x80, employer) ||
      !Read(order, 0x50, leases) || !Read(order, 0x5C, count) ||
      count < 0 || (count != 0 && leases == nullptr) ||
      !Call(b.is_military, row.is_military, order)) return false;
  row.founder_id = Identity(founder);
  row.employer_id = Identity(employer);
  row.leased_title_ids.reserve(static_cast<std::size_t>(count));
  for (std::int32_t i = 0; i < count; ++i) {
    std::uint32_t id = UINT32_MAX;
    if (!Read(leases, static_cast<std::size_t>(i) * sizeof(id), id)) return false;
    row.leased_title_ids.push_back(id);
  }
  // Patron is derived from current leased-title holders by the engine.
  // It must not be replaced with the historical founder.
  void *patron = nullptr;
  if (!Call(b.patron, patron, order)) return false;
  if (patron != nullptr) {
    std::uint32_t id = UINT32_MAX;
    if (!Read(patron, 0x18, id)) return false;
    row.patron_id = Identity(id);
  }
  return true;
}
void ReadMilitaryTerms(const Bindings &b, void *order, void *player,
                       MilitaryTerms &terms) {
  if (b.current_war_eligibility != nullptr) {
    auto &war = terms.current_war_eligibility;
    war.unavailable_reason = "native_war_eligibility_evaluation_unavailable";
    NativeReason reason(b.reason_destroy);
    bool qualifies = false;
    if (Call(b.current_war_eligibility, qualifies, order, player, reason.get())) {
      war.qualifies = qualifies;
      std::string literal;
      war.reasons_available = reason.copy(literal);
      if (war.reasons_available) war.reason_literal = std::move(literal);
      war.available = war.reasons_available;
      if (war.available) war.unavailable_reason.clear();
    }
  }
  terms.unavailable_reason = "native_evaluation_unavailable";
  terms.troop_strength.unavailable_reason = "native_current_soldiers_unavailable";
  std::int32_t current_soldiers = 0;
  if (Call(b.current_soldiers, current_soldiers, order)) {
    terms.troop_strength.current_soldiers = current_soldiers;
    terms.troop_strength.available = true;
    terms.troop_strength.unavailable_reason.clear();
  }
  NativeReason hire_reason(b.reason_destroy), afford_reason(b.reason_destroy);
  bool can_hire = false;
  if (Call(b.can_hire, can_hire, order, player, hire_reason.get())) {
    terms.can_hire = can_hire;
    std::string literal;
    terms.can_hire_reasons_available = hire_reason.copy(literal);
    if (terms.can_hire_reasons_available)
      terms.can_hire_reason_literal = std::move(literal);
  }
  std::array<std::int64_t, 10> cost{};
  std::int64_t *returned = nullptr;
  if (Call(b.cost, returned, order, cost.data(), player) && returned == cost.data()) {
    terms.resource_costs_raw = cost;
    bool affordable = false;
    if (Call(b.can_afford, affordable, static_cast<const std::int64_t *>(cost.data()),
             player, afford_reason.get())) {
      terms.can_afford = affordable;
      std::string literal;
      terms.can_afford_reasons_available = afford_reason.copy(literal);
      if (terms.can_afford_reasons_available)
        terms.can_afford_reason_literal = std::move(literal);
    }
  }
  terms.available = terms.can_hire.has_value() && terms.can_afford.has_value() &&
      terms.resource_costs_raw.has_value() && terms.can_hire_reasons_available &&
      terms.can_afford_reasons_available;
  if (terms.available) terms.unavailable_reason.clear();
}
struct ReleaseQueue {
  bool available = false;
  std::vector<std::uint32_t> ids;
};
ReleaseQueue ReadReleaseQueue(const Bindings &b, void *registry) {
  ReleaseQueue queue;
  if (b.release_eligible == nullptr || b.associated_regiment_in_combat == nullptr)
    return queue;
  // Constructor2A86200 stores registry at manager+28 in global5D1DF10.
  const auto *manager = reinterpret_cast<const void *>(
      reinterpret_cast<std::uintptr_t>(registry) - 0x28);
  const void *ids = nullptr;
  std::int32_t count = -1;
  if (!Read(manager, 0x24A8, ids) || !Read(manager, 0x24B4, count) ||
      count < 0 || (count != 0 && ids == nullptr)) return queue;
  queue.ids.reserve(static_cast<std::size_t>(count));
  for (std::int32_t i = 0; i < count; ++i) {
    std::uint32_t id = UINT32_MAX;
    if (!Read(ids, static_cast<std::size_t>(i) * sizeof(id), id)) return queue;
    queue.ids.push_back(id);
  }
  queue.available = true;
  return queue;
}
void ReadServiceLifecycle(const Bindings &b, void *order, const Row &row,
    std::int32_t actor, const ReleaseQueue &queue, ServiceLifecycle &service) {
  service.applies_to_player = row.employer_id == static_cast<std::uint32_t>(actor);
  if (!service.applies_to_player) {
    service.available = true;
    service.unavailable_reason.clear();
    return;
  }
  if (b.release_eligible == nullptr || b.associated_regiment_in_combat == nullptr)
    return;
  service.unavailable_reason = "native_service_lifecycle_evaluation_unavailable";
  bool eligible = false, combat = false;
  if (Call(b.release_eligible, eligible, order)) service.release_eligible = eligible;
  //261D5F0 receives the vector at order+88, not the order object itself.
  if (Call(b.associated_regiment_in_combat, combat,
           static_cast<void *>(static_cast<std::byte *>(order) + 0x88)))
    service.associated_regiment_in_combat = combat;
  if (queue.available) {
    bool queued = false;
    for (const auto id : queue.ids) if (id == row.holy_order_id) { queued = true; break; }
    service.release_check_queued = queued;
  } else service.unavailable_reason = "native_release_check_queue_unavailable";
  service.available = service.release_eligible.has_value() &&
      service.associated_regiment_in_combat.has_value() && service.release_check_queued.has_value();
  if (service.available) service.unavailable_reason.clear();
}
bool ResolveAssociated(void **slot, std::uint32_t id, std::size_t id_offset,
    std::size_t tag_offset, std::uint32_t tag, void *&object) {
  object = nullptr;
  // This is the native empty reference, not a failed registry read.
  if (id == UINT32_MAX) return true;
  void *registry = nullptr;
  if (!Read(slot, 0, registry)) return false;
  if (registry == nullptr) return true; // Native canonical-invalid fallback.
  std::int32_t bound = -1;
  if (!Read(registry, 0x2C, bound) || bound < 0) return false;
  const auto index = id & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(bound)) return true;
  const void *entries = nullptr;
  if (!Read(registry, 0x20, entries) || entries == nullptr) return false;
  void *candidate = nullptr;
  if (!Read(entries, static_cast<std::size_t>(index) * 0x10 + 8, candidate)) return false;
  if (candidate == nullptr) return true;
  std::uint32_t actual_id = UINT32_MAX, actual_tag = 0;
  if (!Read(candidate, id_offset, actual_id) || !Read(candidate, tag_offset, actual_tag)) return false;
  // Generation mismatch, absent slots and wrong types all follow the native
  // invalid fallback path. No fields from an invalid candidate are consumed.
  if (actual_id == id && actual_tag == tag) object = candidate;
  return true;
}
void ReadTroopAssociation(const Bindings &b, void *order, const Row &row,
    std::int32_t actor, TroopAssociation &association) {
  association.applies_to_player = row.employer_id == static_cast<std::uint32_t>(actor);
  if (!association.applies_to_player) {
    association.available = true;
    association.unavailable_reason.clear();
    return;
  }
  if (b.regiment_registry_slot == nullptr || b.army_registry_slot == nullptr ||
      b.combat_registry_slot == nullptr) return;
  association.unavailable_reason = "native_troop_association_vector_unavailable";
  const void *ids = nullptr;
  std::int32_t count = -1;
  if (!Read(order, 0x88, ids) || !Read(order, 0x94, count) ||
      count < 0 || (count != 0 && ids == nullptr)) return;
  association.rows.reserve(static_cast<std::size_t>(count));
  bool complete = true;
  for (std::int32_t i = 0; i < count; ++i) {
    AssociatedRegiment member;
    if (!Read(ids, static_cast<std::size_t>(i) * sizeof(member.regiment_id), member.regiment_id)) return;
    member.unavailable_reason = "native_associated_regiment_unavailable";
    void *regiment = nullptr;
    if (ResolveAssociated(b.regiment_registry_slot, member.regiment_id,
                          0x10, 0x14, 0x41725267U, regiment)) {
      member.regiment_resolved = regiment != nullptr;
      if (regiment == nullptr) member.available = true;
      else {
        std::uint32_t army_id = UINT32_MAX;
        member.unavailable_reason = "native_associated_army_unavailable";
        if (Read(regiment, 0x140, army_id)) {
          member.native_carmy_id = Identity(army_id);
          void *army = nullptr;
          if (ResolveAssociated(b.army_registry_slot, army_id, 0x10, 0x14, 0x41726D79U, army)) {
            member.native_carmy_resolved = army != nullptr;
            if (army == nullptr) member.available = true;
            else {
              std::uint32_t combat_id = UINT32_MAX;
              member.unavailable_reason = "native_associated_combat_unavailable";
              if (Read(army, 0x128, combat_id)) {
                member.combat_id = Identity(combat_id);
                void *combat = nullptr;
                if (ResolveAssociated(b.combat_registry_slot, combat_id,
                                      0x08, 0x0C, 0x436F6D62U, combat)) {
                  member.combat_resolved = combat != nullptr;
                  member.available = true;
                }
              }
            }
          }
        }
      }
    }
    if (member.available) member.unavailable_reason.clear();
    else complete = false;
    association.rows.push_back(std::move(member));
  }
  association.available = complete;
  association.unavailable_reason = complete ? "" : "native_troop_association_partial";
}
void Quote(std::ostream &out, std::string_view text) {
  constexpr char hex[] = "0123456789abcdef";
  out << '"';
  for (const unsigned char value : text) {
    if (value == '"' || value == '\\') out << '\\' << static_cast<char>(value);
    else if (value < 0x20)
      out << "\\u00" << hex[value >> 4] << hex[value & 15];
    else out << static_cast<char>(value);
  }
  out << '"';
}
template <typename T> void Optional(std::ostream &out, const std::optional<T> &value) {
  if (value) out << *value;
  else out << "null";
}
void Optional(std::ostream &out, const std::optional<std::string> &value) {
  if (value) Quote(out, *value);
  else out << "null";
}
void TermsJson(std::ostream &out, const MilitaryTerms &terms) {
  out << "{\"available\":" << terms.available << ",\"unavailable_reason\":";
  if (terms.available) out << "null";
  else Quote(out, terms.unavailable_reason);
  out << ",\"can_hire\":"; Optional(out, terms.can_hire);
  out << ",\"can_afford\":"; Optional(out, terms.can_afford);
  out << ",\"resource_costs_raw\":";
  if (terms.resource_costs_raw) {
    out << '[';
    for (std::size_t i = 0; i < terms.resource_costs_raw->size(); ++i) {
      if (i != 0) out << ',';
      out << (*terms.resource_costs_raw)[i];
    }
    out << ']';
  } else out << "null";
  out << ",\"resource_scale\":" << kRawScale
      << ",\"can_hire_reasons_available\":" << terms.can_hire_reasons_available
      << ",\"can_hire_reason_literal\":"; Optional(out, terms.can_hire_reason_literal);
  out << ",\"can_afford_reasons_available\":" << terms.can_afford_reasons_available
      << ",\"can_afford_reason_literal\":"; Optional(out, terms.can_afford_reason_literal);
  out << ",\"troop_strength\":{\"available\":" << terms.troop_strength.available
      << ",\"unavailable_reason\":";
  if (terms.troop_strength.available) out << "null";
  else Quote(out, terms.troop_strength.unavailable_reason);
  out << ",\"current_soldiers\":"; Optional(out, terms.troop_strength.current_soldiers);
  out << "},\"current_war_eligibility\":{\"available\":"
      << terms.current_war_eligibility.available << ",\"unavailable_reason\":";
  if (terms.current_war_eligibility.available) out << "null";
  else Quote(out, terms.current_war_eligibility.unavailable_reason);
  out << ",\"qualifies\":"; Optional(out, terms.current_war_eligibility.qualifies);
  out << ",\"reasons_available\":" << terms.current_war_eligibility.reasons_available
      << ",\"reason_literal\":"; Optional(out, terms.current_war_eligibility.reason_literal);
  const auto &service = terms.service_lifecycle;
  out << "},\"service_lifecycle\":{\"available\":" << service.available
      << ",\"unavailable_reason\":";
  if (service.available) out << "null";
  else Quote(out, service.unavailable_reason);
  out << ",\"applies_to_player\":" << service.applies_to_player
      << ",\"release_eligible\":"; Optional(out, service.release_eligible);
  out << ",\"associated_regiment_in_combat\":";
  Optional(out, service.associated_regiment_in_combat);
  out << ",\"release_check_queued\":"; Optional(out, service.release_check_queued);
  const auto &association = terms.troop_association;
  out << "},\"troop_association\":{\"available\":" << association.available
      << ",\"unavailable_reason\":";
  if (association.available) out << "null";
  else Quote(out, association.unavailable_reason);
  out << ",\"applies_to_player\":" << association.applies_to_player << ",\"rows\":[";
  for (std::size_t i = 0; i < association.rows.size(); ++i) {
    if (i != 0) out << ',';
    const auto &member = association.rows[i];
    out << "{\"regiment_id\":" << member.regiment_id << ",\"available\":" << member.available
        << ",\"unavailable_reason\":";
    if (member.available) out << "null";
    else Quote(out, member.unavailable_reason);
    out << ",\"regiment_resolved\":" << member.regiment_resolved << ",\"native_carmy_id\":";
    Optional(out, member.native_carmy_id);
    out << ",\"native_carmy_resolved\":" << member.native_carmy_resolved << ",\"combat_id\":";
    Optional(out, member.combat_id);
    out << ",\"combat_resolved\":" << member.combat_resolved << '}';
  }
  const auto &cost_context = terms.hire_cost_context;
  out << "]},\"hire_cost_context\":{\"available\":" << cost_context.available
      << ",\"unavailable_reason\":";
  if (cost_context.available) out << "null";
  else Quote(out, cost_context.unavailable_reason);
  out << ",\"order_title_id\":"; Optional(out, cost_context.order_title_id);
  out << ",\"order_title_resolved\":" << cost_context.order_title_resolved
      << ",\"order_title_holder_id\":"; Optional(out, cost_context.order_title_holder_id);
  out << ",\"title_holder_is_player\":"; Optional(out, cost_context.title_holder_is_player);
  out << ",\"patron_is_player\":"; Optional(out, cost_context.patron_is_player);
  out << ",\"employed_by_other\":"; Optional(out, cost_context.employed_by_other);
  out << ",\"cost_branch\":"; Optional(out, cost_context.cost_branch);
  out << ",\"selected_patron_multiplier_raw\":";
  Optional(out, cost_context.selected_patron_multiplier_raw);
  out << ",\"resource_scale\":" << kRawScale << "},\"current_reinforcement_v1\":";
  SerializeHolyOrderCurrentReinforcement12003(out, terms.current_reinforcement_v1);
  out << '}';
}
} // namespace

Bindings BindPlayerHolyOrderImage12003(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (base == 0 || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.manager_slot = reinterpret_cast<void **>(base + 0x5D1DF10);
  b.fallback_slot = reinterpret_cast<void **>(base + 0x5D1DF00);
  b.patron = reinterpret_cast<Patron>(base + 0x2618D80);
  b.is_military = reinterpret_cast<IsMilitary>(base + 0x261C490);
  b.can_hire = reinterpret_cast<CanHire>(base + 0x2619C50);
  b.cost = reinterpret_cast<Cost>(base + 0x26198E0);
  b.can_afford = reinterpret_cast<CanAfford>(base + 0x310E710);
  b.reason_destroy = reinterpret_cast<ReasonDestroy>(base + 0x856050);
  b.current_soldiers = reinterpret_cast<CurrentSoldiers>(base + 0x261AD10);
  b.current_war_eligibility = reinterpret_cast<CanHire>(base + 0x261C120);
  b.release_eligible = reinterpret_cast<LifecyclePredicate>(base + 0x261A1D0);
  b.associated_regiment_in_combat = reinterpret_cast<LifecyclePredicate>(base + 0x261D5F0);
  b.regiment_registry_slot = reinterpret_cast<void **>(base + 0x5D1F340);
  b.army_registry_slot = reinterpret_cast<void **>(base + 0x5D1DE48);
  b.combat_registry_slot = reinterpret_cast<void **>(base + 0x5D1DE70);
  b.hire_cost_context.title_registry_slot = reinterpret_cast<void **>(base + 0x5D1DAF8);
  b.hire_cost_context.title_fallback_slot = reinterpret_cast<void **>(base + 0x5D1DAE0);
  b.hire_cost_context.patron_hire_multiplier_raw =
      reinterpret_cast<const std::int64_t *>(base + 0x5C69250);
  b.hire_cost_context.patron_recall_multiplier_raw =
      reinterpret_cast<const std::int64_t *>(base + 0x5C69248);
  b.current_reinforcement = BindHolyOrderCurrentReinforcementImage12003(base, sha);
  b.current_reinforcement.army_registry_slot = b.army_registry_slot;
  return b;
}

bool ReadPlayerHolyOrderContext12003(const Bindings &b, void *player,
    std::int32_t actor, std::int32_t date, std::uint64_t epoch,
    Context &out) noexcept {
  out = {};
  out.capture_epoch = epoch;
  out.date_raw = date;
  out.played_character_id = actor;
  if (!b.enabled || b.manager_slot == nullptr || b.fallback_slot == nullptr ||
      b.patron == nullptr || b.is_military == nullptr || b.can_hire == nullptr ||
      b.cost == nullptr || b.can_afford == nullptr || b.reason_destroy == nullptr)
    return false;
  std::int32_t actual_actor = -1;
  if (!Read(player, 0x18, actual_actor) || actual_actor != actor) {
    out.unavailable_reason = "played_character_unavailable";
    return false;
  }
  void *manager = nullptr, *fallback = nullptr;
  if (!Read(b.manager_slot, 0, manager) || manager == nullptr ||
      !Read(b.fallback_slot, 0, fallback)) {
    out.unavailable_reason = "holy_order_manager_unavailable";
    return false;
  }
  const void *entries = nullptr;
  std::int32_t range_bound = -1;
  if (!Read(manager, 0x20, entries) || !Read(manager, 0x2C, range_bound) ||
      range_bound < 0 || (range_bound != 0 && entries == nullptr)) {
    out.unavailable_reason = "holy_order_entries_unavailable";
    return false;
  }
  try {
    const auto release_queue = ReadReleaseQueue(b, manager);
    // +2C is a slot range bound, not an active-object count. Hole slots are
    // expected: inspect every entry and copy each real organisation once.
    for (std::int32_t i = 0; i < range_bound; ++i) {
      void *order = nullptr;
      if (!Read(entries, static_cast<std::size_t>(i) * 0x10 + 8, order)) {
        out.unavailable_reason = "holy_order_entry_unavailable";
        return false;
      }
      if (order == nullptr || (fallback != nullptr && order == fallback)) continue;
      Row row{};
      if (!ReadIdentity(b, order, row)) {
        out.unavailable_reason = "holy_order_identity_unavailable";
        return false;
      }
      if (row.is_military) {
        row.military_terms.emplace();
        ReadMilitaryTerms(b, order, player, *row.military_terms);
        ReadServiceLifecycle(b, order, row, actor, release_queue,
                             row.military_terms->service_lifecycle);
        ReadTroopAssociation(b, order, row, actor,
                             row.military_terms->troop_association);
        row.military_terms->hire_cost_context =
            ReadHireCostContext12003(b.hire_cost_context, order, player, b.patron);
        auto &refill = row.military_terms->current_reinforcement_v1;
        refill = ReadHolyOrderCurrentReinforcement12003(
            b.current_reinforcement, order, row.holy_order_id);
        refill.army_roles = ReadHolyOrderCurrentArmyRoles12003(
            b.current_reinforcement, row.military_terms->troop_association);
      }
      out.rows.push_back(std::move(row));
    }
    out.available = true;
    out.unavailable_reason.clear();
    return true;
  } catch (...) {
    out.unavailable_reason = "holy_order_native_copy_exception";
    return false;
  }
}

std::string SerializePlayerHolyOrderContext12003(const Context &c) {
  std::ostringstream out;
  out << std::boolalpha << "{\"schema\":"; Quote(out, kSchema);
  out << ",\"read_only\":true,\"game_version\":\"1.20.0.3\",\"executable_sha256\":";
  Quote(out, kExecutableSha256);
  out << ",\"available\":" << c.available << ",\"unavailable_reason\":";
  if (c.available) out << "null";
  else Quote(out, c.unavailable_reason);
  out << ",\"capture_epoch\":" << c.capture_epoch << ",\"date_raw\":" << c.date_raw
      << ",\"played_character_id\":" << c.played_character_id
      << ",\"raw_scale\":" << kRawScale << ",\"rows\":[";
  for (std::size_t i = 0; i < c.rows.size(); ++i) {
    if (i != 0) out << ',';
    const auto &row = c.rows[i];
    out << "{\"holy_order_id\":" << row.holy_order_id << ",\"rite_id\":" << row.rite_id
        << ",\"is_military\":" << row.is_military << ",\"founder_id\":";
    Optional(out, row.founder_id);
    out << ",\"patron_id\":"; Optional(out, row.patron_id);
    out << ",\"employer_id\":"; Optional(out, row.employer_id);
    out << ",\"leased_title_ids\":[";
    for (std::size_t j = 0; j < row.leased_title_ids.size(); ++j) {
      if (j != 0) out << ',';
      out << row.leased_title_ids[j];
    }
    out << "],\"military_terms\":";
    if (row.military_terms) TermsJson(out, *row.military_terms);
    else out << "null";
    out << '}';
  }
  out << "]}";
  return out.str();
}
} // namespace xar::ck3_12003::religion::holy_order
