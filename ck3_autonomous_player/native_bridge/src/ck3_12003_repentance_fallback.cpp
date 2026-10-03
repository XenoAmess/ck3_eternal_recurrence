#include "xar_bridge/ck3_12003_repentance_fallback.hpp"

#include <algorithm>
#include <bit>
#include <cstring>
#include <functional>
#include <sstream>
#include <unordered_set>

#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12003::religion::repentance_fallback {
namespace {
bool DirectRead(const void *address, void *out, std::size_t size) noexcept {
  if (!address) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(out, address, size); return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
template <typename T> bool Read(const Bindings &b, const void *object,
    std::size_t offset, T &out) noexcept {
  if (!object) return false;
  const auto *address = static_cast<const std::byte *>(object) + offset;
  return b.read_memory ? b.read_memory(b.read_context, address, &out, sizeof(T))
                       : DirectRead(address, &out, sizeof(T));
}
template <typename Fn, typename T, typename... Args>
bool Call(Fn fn, T &out, Args... args) noexcept {
  if (!fn) return false;
#if defined(_MSC_VER)
  __try {
#endif
    out = fn(args...); return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
bool Resolve(const Bindings &b, void **storage_slot, std::int32_t id,
    std::size_t identity_offset, void *&out) noexcept {
  out = nullptr;
  void *storage = nullptr, *rows = nullptr;
  std::int32_t count = 0, actual = -1;
  const auto index = static_cast<std::uint32_t>(id) & 0x00ffffffU;
  return id != -1 && Read(b, storage_slot, 0, storage) && storage &&
      Read(b, storage, 0x20, rows) && Read(b, storage, 0x2c, count) &&
      count > 0 && index < static_cast<std::uint32_t>(count) &&
      Read(b, rows, index * 16ULL + 8, out) && out &&
      Read(b, out, identity_offset, actual) && actual == id;
}
bool Span(const Bindings &b, const void *object, std::size_t offset,
    std::vector<std::int32_t> &ids) {
  void *data = nullptr;
  std::int32_t count = 0;
  if (!Read(b, object, offset, data) || !Read(b, object, offset + 12, count) ||
      count < 0 || (count && !data)) return false;
  ids.reserve(static_cast<std::size_t>(count));
  for (std::int32_t i = 0; i < count; ++i) {
    std::int32_t id = -1;
    if (!Read(b, data, static_cast<std::size_t>(i) * 4, id)) return false;
    ids.push_back(id);
  }
  return true;
}
void Begin(Collection &c, std::string_view source) {
  c.source = source; c.reason = "none";
  c.available = c.traversal_complete = true;
}
void Fail(Collection &c, const char *reason) {
  if (c.available) c.reason = reason;
  c.available = c.traversal_complete = false;
}
void Realm(const Bindings &b, void *player, std::int32_t actor, Collection &out) {
  Begin(out, kRealmSource);
  std::unordered_set<std::int32_t> seen{actor};
  std::vector<void *> pending{player};
  while (!pending.empty()) {
    void *owner = pending.back(); pending.pop_back(); ++out.visited_nodes;
    void *land = nullptr;
    if (!Read(b, owner, 0x1c0, land)) { Fail(out, "realm_land_unavailable"); continue; }
    if (!land) continue;
    std::vector<std::int32_t> contracts;
    if (!Span(b, land, 0x218, contracts)) { Fail(out, "realm_contract_span_unavailable"); continue; }
    for (const auto id : contracts) {
      void *contract = nullptr, *vassal = nullptr, *resolved = nullptr;
      std::int32_t character = -1;
      if (!Resolve(b, b.contract_storage_slot, id, 8, contract) ||
          !Read(b, contract, 0x20, vassal) || !vassal ||
          !Read(b, vassal, 0x18, character) || character == -1 ||
          !Resolve(b, b.character_storage_slot, character, 0x18, resolved) || resolved != vassal) {
        Fail(out, "realm_contract_owner_unavailable"); continue;
      }
      if (!seen.insert(character).second) continue;
      out.rows.push_back({character, std::nullopt});
      pending.push_back(vassal);
    }
  }
}
void Dejure(const Bindings &b, void *player, Context &context) {
  auto &out = context.dejure_clerical_holders;
  Begin(out, kDejureSource);
  void *primary = nullptr;
  std::int32_t primary_id = -1;
  if (!Call(b.primary_title, primary, player)) { Fail(out, "primary_title_unavailable"); return; }
  if (!primary) { context.primary_title_id = -1; return; }
  if (!Read(b, primary, 0x10, primary_id)) { Fail(out, "primary_title_unavailable"); return; }
  context.primary_title_id = primary_id;
  if (primary_id == -1) return;
  void *resolved = nullptr;
  if (!Resolve(b, b.title_storage_slot, primary_id, 0x10, resolved) || resolved != primary) {
    Fail(out, "primary_title_unavailable"); return;
  }
  std::vector<std::int32_t> pending{primary_id};
  std::unordered_set<std::int32_t> visited, clerical_titles;
  while (!pending.empty()) {
    const auto id = pending.back(); pending.pop_back();
    if (!visited.insert(id).second) continue;
    ++out.visited_nodes;
    void *title = nullptr, *definition = nullptr;
    std::int32_t tier = -1;
    if (!Resolve(b, b.title_storage_slot, id, 0x10, title) ||
        !Read(b, title, 0x48, definition) || !Read(b, definition, 0x64, tier)) {
      Fail(out, "dejure_title_unavailable"); continue;
    }
    if (tier < 2) continue;
    if (tier > 2) {
      std::vector<std::int32_t> children;
      if (!Span(b, title, 0x110, children)) { Fail(out, "dejure_child_span_unavailable"); continue; }
      // Reverse insertion preserves each native child vector's order in DFS.
      pending.insert(pending.end(), children.rbegin(), children.rend());
      continue;
    }
    Scope16 input{5, 0, static_cast<std::uint32_t>(id)}, region{};
    const Scope16 *input_pointer = &input;
    Scope16 *returned = nullptr;
    if (!Call(b.clerical_region, returned, static_cast<void *>(nullptr), &region, &input_pointer) ||
        returned != &region || region.kind != 5 || region.id > UINT32_MAX) {
      Fail(out, "dejure_clerical_region_unavailable"); continue;
    }
    const auto clerical_id = std::bit_cast<std::int32_t>(static_cast<std::uint32_t>(region.id));
    if (clerical_id == -1 || !clerical_titles.insert(clerical_id).second) continue;
    void *clerical_title = nullptr;
    std::int32_t holder = -1;
    if (!Resolve(b, b.title_storage_slot, clerical_id, 0x10, clerical_title) ||
        !Read(b, clerical_title, 0x128, holder)) {
      Fail(out, "dejure_clerical_holder_unavailable"); continue;
    }
    if (holder == -1) continue;
    void *character = nullptr;
    if (!Resolve(b, b.character_storage_slot, holder, 0x18, character)) {
      Fail(out, "dejure_clerical_holder_unavailable"); continue;
    }
    out.rows.push_back({holder, clerical_id});
  }
}
void Merge(const Collection &source, std::vector<Candidate> &out) {
  for (const auto &row : source.rows) {
    auto found = std::find_if(out.begin(), out.end(), [&](const Candidate &c) {
      return c.character_id == row.character_id;
    });
    if (found == out.end()) {
      out.push_back({row.character_id, {}, {}}); found = out.end() - 1;
    }
    if (std::find(found->sources.begin(), found->sources.end(), source.source) == found->sources.end())
      found->sources.push_back(source.source);
    if (row.origin_title_id &&
        std::find(found->origin_title_ids.begin(), found->origin_title_ids.end(), *row.origin_title_id) == found->origin_title_ids.end())
      found->origin_title_ids.push_back(*row.origin_title_id);
  }
}
void Quote(std::ostream &out, std::string_view value) {
  out << '"';
  for (const char c : value) { if (c == '"' || c == '\\') out << '\\'; out << c; }
  out << '"';
}
void SerializeCollection(std::ostream &out, const Collection &c) {
  out << "{\"source\":"; Quote(out, c.source);
  out << ",\"available\":" << (c.available ? "true" : "false")
      << ",\"traversal_complete\":" << (c.traversal_complete ? "true" : "false")
      << ",\"reason\":"; Quote(out, c.reason);
  out << ",\"visited_nodes\":" << c.visited_nodes << ",\"rows\":[";
  for (std::size_t i = 0; i < c.rows.size(); ++i) {
    if (i) out << ',';
    out << "{\"character_id\":" << c.rows[i].character_id << ",\"origin_title_id\":";
    if (c.rows[i].origin_title_id) out << *c.rows[i].origin_title_id; else out << "null";
    out << '}';
  }
  out << "]}";
}
} // namespace

Bindings BindRepentanceFallbackImage12003(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (!base || sha != ck3_12003::kExecutableSha256) return b;
  b.enabled = true;
  b.character_storage_slot = reinterpret_cast<void **>(base + 0x5c67568);
  b.contract_storage_slot = reinterpret_cast<void **>(base + 0x5d1eb88);
  b.title_storage_slot = reinterpret_cast<void **>(base + 0x5d1daf8);
  b.primary_title = reinterpret_cast<ObjectGetter>(base + 0x289da30);
  b.clerical_region = reinterpret_cast<ClericalRegion>(base + 0x1b9c9e0);
  return b;
}
bool ReadRepentanceFallback12003(const Bindings &b, void *player, std::int32_t actor,
    std::int32_t date, std::uint64_t epoch, Context &out) noexcept {
  out = {}; out.capture_epoch = epoch; out.date_raw = date; out.played_character_id = actor;
  out.realm_vassals.source = kRealmSource; out.dejure_clerical_holders.source = kDejureSource;
  if (!b.enabled) return false;
  std::int32_t actual = -1;
  if (actor == -1 || !Read(b, player, 0x18, actual) || actual != actor) {
    out.unavailable_reason = "played_character_unavailable"; return false;
  }
  Realm(b, player, actor, out.realm_vassals);
  Dejure(b, player, out);
  Merge(out.realm_vassals, out.candidates); Merge(out.dejure_clerical_holders, out.candidates);
  out.available = out.realm_vassals.available && out.dejure_clerical_holders.available;
  out.complete_source_traversal = out.realm_vassals.traversal_complete && out.dejure_clerical_holders.traversal_complete;
  out.unavailable_reason = out.available ? "none" : "one_or_more_fallback_sources_unavailable";
  return out.available;
}
std::string SerializeRepentanceFallback12003(const Context &c) {
  std::ostringstream out;
  out << "{\"schema\":"; Quote(out, kSchema);
  out << ",\"read_only\":true,\"available\":" << (c.available ? "true" : "false")
      << ",\"unavailable_reason\":"; Quote(out, c.unavailable_reason);
  out << ",\"capture_epoch\":" << c.capture_epoch << ",\"date_raw\":" << c.date_raw
      << ",\"played_character_id\":" << c.played_character_id
      << ",\"complete_source_traversal\":" << (c.complete_source_traversal ? "true" : "false")
      << ",\"complete_stock_preferred_selector\":false,\"stock_preferred_filters_applied\":false"
      << ",\"coverage\":\"recursive_realm_contract_owners_and_primary_title_dejure_clerical_holders\""
      << ",\"primary_title_id\":";
  if (c.primary_title_id) out << *c.primary_title_id; else out << "null";
  out << ",\"realm_vassals\":"; SerializeCollection(out, c.realm_vassals);
  out << ",\"dejure_clerical_holders\":"; SerializeCollection(out, c.dejure_clerical_holders);
  out << ",\"candidates\":[";
  for (std::size_t i = 0; i < c.candidates.size(); ++i) {
    if (i) out << ',';
    const auto &candidate = c.candidates[i];
    out << "{\"character_id\":" << candidate.character_id << ",\"sources\":[";
    for (std::size_t j = 0; j < candidate.sources.size(); ++j) {
      if (j) out << ','; Quote(out, candidate.sources[j]);
    }
    out << "],\"origin_title_ids\":[";
    for (std::size_t j = 0; j < candidate.origin_title_ids.size(); ++j) {
      if (j) out << ','; out << candidate.origin_title_ids[j];
    }
    out << "]}";
  }
  out << "]}"; return out.str();
}
} // namespace xar::ck3_12003::religion::repentance_fallback
