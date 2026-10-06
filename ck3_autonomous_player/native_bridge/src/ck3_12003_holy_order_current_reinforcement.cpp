#include "xar_bridge/ck3_12003_holy_order_current_reinforcement.hpp"
#include "xar_bridge/ck3_12003_player_holy_order_context.hpp"

#include <cstddef>
#include <cstring>
#include <ostream>
#include <utility>

#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12003::religion::holy_order {
namespace {
constexpr std::string_view kExactSha =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
template <class T> bool Read(const void *p, std::size_t offset, T &value) noexcept {
  if (p == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&value, static_cast<const std::byte *>(p) + offset, sizeof(T));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
template <class Fn, class T, class... Args>
bool Call(Fn fn, T &value, Args... args) noexcept {
  if (fn == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    value = fn(args...);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
bool Resolve(void **slot, std::uint32_t id, std::uint32_t expected_tag, void *&object) noexcept {
  object = nullptr;
  if (id == UINT32_MAX) return true;
  void *registry = nullptr;
  if (!Read(slot, 0, registry)) return false;
  if (registry == nullptr) return true;
  std::int32_t bound = -1;
  if (!Read(registry, 0x2C, bound) || bound < 0) return false;
  const auto index = id & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(bound)) return true;
  const void *entries = nullptr;
  if (!Read(registry, 0x20, entries) || entries == nullptr) return false;
  void *candidate = nullptr;
  if (!Read(entries, static_cast<std::size_t>(index) * 0x10 + 8, candidate)) return false;
  if (candidate == nullptr) return true;
  std::uint32_t actual = UINT32_MAX, tag = 0;
  if (!Read(candidate, 0x10, actual) || !Read(candidate, 0x14, tag)) return false;
  if (actual == id && tag == expected_tag) object = candidate;
  // Canonical-invalid result: do not expose default-object fields as actual Regi.
  return true;
}
CurrentReinforcementChunk12003 ReadChunk(
    const CurrentReinforcementBindings12003 &b, void *regiment,
    std::uint32_t full_id, std::int32_t index) {
  CurrentReinforcementChunk12003 row;
  row.chunk_index = index;
  row.unavailable_reason = "native_holy_order_reinforcement_chunk_unavailable";
  auto *chunk = static_cast<std::byte *>(regiment) + 0x18 +
      static_cast<std::size_t>(index) * 0x24;
  std::int32_t maximum = 0, current = 0, ordinal = -1, state = 0;
  std::uint32_t persistent = UINT32_MAX, army_regiment = UINT32_MAX;
  std::uint8_t pending = 0;
  if (!Read(chunk, 0, maximum) || !Read(chunk, 4, current) ||
      !Read(chunk, 8, persistent) || !Read(chunk, 0x0C, ordinal) ||
      !Read(chunk, 0x10, army_regiment) || !Read(chunk, 0x14, pending) ||
      !Read(chunk, 0x18, state)) return row;
  row.maximum_soldiers = maximum; row.current_soldiers = current;
  row.persistent_regiment_id = persistent; row.native_chunk_index = ordinal;
  row.army_regiment_id = army_regiment; row.pending_raw = pending; row.state_raw = state;
  if (persistent != full_id || ordinal != index) {
    row.unavailable_reason = "native_holy_order_reinforcement_chunk_backlink_mismatch";
    return row;
  }
  bool permitted = false, chunk_permitted = false;
  if (Call(b.can_replenish, permitted, regiment, static_cast<void *>(chunk)))
    row.native_can_replenish = permitted;
  if (Call(b.chunk_can_replenish, chunk_permitted, static_cast<void *>(chunk)))
    row.native_chunk_can_replenish = chunk_permitted;
  row.available = row.native_can_replenish.has_value() && row.native_chunk_can_replenish.has_value();
  if (row.available) row.unavailable_reason.clear();
  return row;
}
CurrentReinforcementRegiment12003 ReadRegiment(
    const CurrentReinforcementBindings12003 &b, std::uint32_t id, std::int32_t index) {
  CurrentReinforcementRegiment12003 row;
  row.persistent_regiment_id = id; row.source_index = index;
  row.unavailable_reason = "native_holy_order_persistent_regiment_unavailable";
  void *regiment = nullptr;
  if (!Resolve(b.persistent_registry_slot, id, 0x52656769U, regiment)) return row;
  row.resolved = regiment != nullptr;
  if (!row.resolved) {
    row.available = true; row.unavailable_reason.clear(); return row;
  }
  std::uint32_t owner = UINT32_MAX;
  if (Read(regiment, 0x12C, owner)) row.owner_character_id = owner;
  std::int64_t fraction = 0;
  std::int64_t *returned = nullptr;
  if (Call(b.monthly_fraction, returned, regiment, &fraction) && returned == &fraction)
    row.monthly_replenishment_fraction_raw = fraction;
  std::int32_t months = 0;
  if (Call(b.months_to_full, months, regiment)) row.native_months_to_full = months;
  bool complete = row.owner_character_id.has_value() &&
      row.monthly_replenishment_fraction_raw.has_value() && row.native_months_to_full.has_value();
  row.chunks.reserve(7);
  for (std::int32_t i = 0; i < 7; ++i) {
    auto chunk = ReadChunk(b, regiment, id, i);
    complete = complete && chunk.available;
    row.chunks.push_back(std::move(chunk));
  }
  row.available = complete;
  if (complete) row.unavailable_reason.clear();
  return row;
}
void Quote(std::ostream &out, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  out << '"';
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') out << '\\' << static_cast<char>(c);
    else if (c < 0x20) out << "\\u00" << hex[c >> 4] << hex[c & 15];
    else out << static_cast<char>(c);
  }
  out << '"';
}
void Reason(std::ostream &out, bool available, const std::string &reason) {
  if (available) out << "null"; else Quote(out, reason);
}
template <class T> void Optional(std::ostream &out, const std::optional<T> &v) {
  if (v) out << *v; else out << "null";
}
void Optional(std::ostream &out, const std::optional<std::uint8_t> &v) {
  if (v) out << static_cast<unsigned>(*v); else out << "null";
}
} // namespace

CurrentReinforcementBindings12003 BindHolyOrderCurrentReinforcementImage12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  CurrentReinforcementBindings12003 b;
  if (base == 0 || sha != kExactSha) return b;
  b.enabled = true;
  b.persistent_registry_slot = reinterpret_cast<void **>(base + 0x5D1EB68);
  b.monthly_fraction = reinterpret_cast<decltype(b.monthly_fraction)>(base + 0x262CAD0);
  b.months_to_full = reinterpret_cast<decltype(b.months_to_full)>(base + 0x262BC90);
  b.can_replenish = reinterpret_cast<decltype(b.can_replenish)>(base + 0x262C700);
  b.chunk_can_replenish = reinterpret_cast<decltype(b.chunk_can_replenish)>(base + 0x2657F10);
  b.army_registry_slot = reinterpret_cast<void **>(base + 0x5D1DE48);
  b.unit_registry_slot = reinterpret_cast<void **>(base + 0x5D1E380);
  return b;
}
CurrentReinforcement12003 ReadHolyOrderCurrentReinforcement12003(
    const CurrentReinforcementBindings12003 &b, const void *order,
    std::uint32_t full_id) noexcept {
  CurrentReinforcement12003 out;
  if (!b.enabled || b.persistent_registry_slot == nullptr || b.monthly_fraction == nullptr ||
      b.months_to_full == nullptr || b.can_replenish == nullptr || b.chunk_can_replenish == nullptr)
    return out;
  out.unavailable_reason = "native_holy_order_reinforcement_order_unavailable";
  std::uint32_t actual = UINT32_MAX, tag = 0;
  if (!Read(order, 0x10, actual) || actual != full_id ||
      !Read(order, 0x14, tag) || tag != 0x486F4F72U) return out;
  const void *ids = nullptr;
  std::int32_t count = -1;
  out.unavailable_reason = "native_holy_order_reinforcement_roster_unavailable";
  if (!Read(order, 0x68, ids) || !Read(order, 0x74, count)) return out;
  out.source_count = count;
  if (count < 0 || (count > 0 && ids == nullptr)) return out;
  try {
    out.rows.reserve(static_cast<std::size_t>(count));
    bool complete = true;
    for (std::int32_t index = 0; index < count; ++index) {
      std::uint32_t id = UINT32_MAX;
      if (!Read(ids, static_cast<std::size_t>(index) * 4, id)) return out;
      auto row = ReadRegiment(b, id, index);
      complete = complete && row.available;
      out.rows.push_back(std::move(row));
    }
    out.available = complete;
    out.unavailable_reason = complete ? "" : "native_holy_order_reinforcement_partial";
  } catch (...) { out.unavailable_reason = "native_holy_order_reinforcement_copy_exception"; }
  return out;
}
CurrentArmyRoles12003 ReadHolyOrderCurrentArmyRoles12003(
    const CurrentReinforcementBindings12003 &b, const TroopAssociation &association) noexcept {
  CurrentArmyRoles12003 out;
  out.applies_to_player = association.applies_to_player;
  if (!out.applies_to_player) {
    out.available = true; out.unavailable_reason.clear(); return out;
  }
  if (!b.enabled || b.army_registry_slot == nullptr || b.unit_registry_slot == nullptr) return out;
  out.unavailable_reason = "native_holy_order_army_association_unavailable";
  if (!association.available) return out;
  try {
    bool complete = true;
    out.rows.reserve(association.rows.size());
    for (std::size_t index = 0; index < association.rows.size(); ++index) {
      const auto &source = association.rows[index];
      CurrentArmyRole12003 row;
      row.association_index = static_cast<std::int32_t>(index);
      row.army_regiment_id = source.regiment_id;
      row.native_carmy_id = source.native_carmy_id;
      row.unavailable_reason = "native_holy_order_army_role_unavailable";
      if (!source.native_carmy_resolved || !source.native_carmy_id) row.available = true;
      else {
        void *army = nullptr;
        if (Resolve(b.army_registry_slot, *source.native_carmy_id, 0x41726D79U, army)) {
          row.army_resolved = army != nullptr;
          if (army == nullptr) row.available = true;
          else {
            std::uint32_t commander = UINT32_MAX, public_id = UINT32_MAX;
            const bool commander_copied = Read(army, 0x120, commander);
            if (commander_copied) row.commander_character_id = commander;
            if (Read(army, 0x124, public_id)) {
              row.public_army_id = public_id;
              void *unit = nullptr;
              if (Resolve(b.unit_registry_slot, public_id, 0x556E6974U, unit)) {
                if (unit == nullptr) row.available = commander_copied;
                else {
                  std::uint32_t backlink = UINT32_MAX, owner = UINT32_MAX;
                  const bool backlink_copied = Read(unit, 0x178, backlink);
                  const bool owner_copied = Read(unit, 0x174, owner);
                  if (backlink_copied) row.unit_carmy_backlink = backlink;
                  if (owner_copied) row.owner_character_id = owner;
                  if (backlink_copied && owner_copied) {
                    if (backlink == *source.native_carmy_id) {
                      row.unit_resolved = true;
                      row.available = commander_copied;
                    } else row.unavailable_reason = "native_holy_order_army_unit_backlink_mismatch";
                  }
                }
              }
            }
          }
        }
      }
      if (row.available) row.unavailable_reason.clear();
      complete = complete && row.available;
      out.rows.push_back(std::move(row));
    }
    out.available = complete;
    out.unavailable_reason = complete ? "" : "native_holy_order_army_roles_partial";
  } catch (...) { out.unavailable_reason = "native_holy_order_army_roles_copy_exception"; }
  return out;
}
void SerializeHolyOrderCurrentReinforcement12003(
    std::ostream &out, const CurrentReinforcement12003 &value) {
  out << std::boolalpha << "{\"available\":" << value.available << ",\"unavailable_reason\":";
  Reason(out, value.available, value.unavailable_reason);
  out << ",\"fraction_scale\":100000,\"source_count\":"; Optional(out, value.source_count);
  out << ",\"rows\":[";
  for (std::size_t i = 0; i < value.rows.size(); ++i) {
    if (i != 0) out << ',';
    const auto &row = value.rows[i];
    out << "{\"source_index\":" << row.source_index << ",\"persistent_regiment_id\":"
        << row.persistent_regiment_id << ",\"available\":" << row.available << ",\"unavailable_reason\":";
    Reason(out, row.available, row.unavailable_reason);
    out << ",\"resolved\":" << row.resolved << ",\"owner_character_id\":"; Optional(out, row.owner_character_id);
    out << ",\"monthly_replenishment_fraction_raw\":"; Optional(out, row.monthly_replenishment_fraction_raw);
    out << ",\"native_months_to_full\":"; Optional(out, row.native_months_to_full);
    out << ",\"chunks\":[";
    for (std::size_t j = 0; j < row.chunks.size(); ++j) {
      if (j != 0) out << ',';
      const auto &c = row.chunks[j];
      out << "{\"chunk_index\":" << c.chunk_index << ",\"available\":" << c.available << ",\"unavailable_reason\":";
      Reason(out, c.available, c.unavailable_reason);
      out << ",\"maximum_soldiers\":"; Optional(out, c.maximum_soldiers);
      out << ",\"current_soldiers\":"; Optional(out, c.current_soldiers);
      out << ",\"persistent_regiment_id\":"; Optional(out, c.persistent_regiment_id);
      out << ",\"native_chunk_index\":"; Optional(out, c.native_chunk_index);
      out << ",\"army_regiment_id\":"; Optional(out, c.army_regiment_id);
      out << ",\"pending_raw\":"; Optional(out, c.pending_raw);
      out << ",\"state_raw\":"; Optional(out, c.state_raw);
      out << ",\"native_can_replenish\":"; Optional(out, c.native_can_replenish);
      out << ",\"native_chunk_can_replenish\":"; Optional(out, c.native_chunk_can_replenish);
      out << '}';
    }
    out << "]}";
  }
  const auto &roles = value.army_roles;
  out << "],\"army_roles\":{\"available\":" << roles.available << ",\"unavailable_reason\":";
  Reason(out, roles.available, roles.unavailable_reason);
  out << ",\"applies_to_player\":" << roles.applies_to_player << ",\"rows\":[";
  for (std::size_t i = 0; i < roles.rows.size(); ++i) {
    if (i != 0) out << ',';
    const auto &role = roles.rows[i];
    out << "{\"association_index\":" << role.association_index << ",\"army_regiment_id\":"
        << role.army_regiment_id << ",\"available\":" << role.available << ",\"unavailable_reason\":";
    Reason(out, role.available, role.unavailable_reason);
    out << ",\"native_carmy_id\":"; Optional(out, role.native_carmy_id);
    out << ",\"army_resolved\":" << role.army_resolved << ",\"commander_character_id\":";
    Optional(out, role.commander_character_id);
    out << ",\"public_army_id\":"; Optional(out, role.public_army_id);
    out << ",\"unit_resolved\":" << role.unit_resolved << ",\"unit_carmy_backlink\":";
    Optional(out, role.unit_carmy_backlink);
    out << ",\"owner_character_id\":";
    Optional(out, role.owner_character_id);
    out << '}';
  }
  out << "]}}";
}
} // namespace xar::ck3_12003::religion::holy_order
