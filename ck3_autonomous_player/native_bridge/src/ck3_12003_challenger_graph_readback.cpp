#include "xar_bridge/ck3_12003_challenger_graph_readback.hpp"
#include "xar_bridge/ck3_12004_confucian_title_profile.hpp"
#include <algorithm>
#include <bit>
#include <cstring>
#include <utility>
#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12003::challenger_graph {
namespace {
template <class T> bool Load(const void *object, std::size_t offset, T &out) noexcept {
  if (!object) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&out, static_cast<const std::byte *>(object) + offset, sizeof(T));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
bool CopyRecords(const void *source, NativeRecord *target, std::size_t count) noexcept {
  if (count == 0) return true;
  if (!source || !target) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(target, source, count * sizeof(NativeRecord)); return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
bool Call(religious_title::ObjectGetter getter, void *object, void *&out) noexcept {
  if (!getter || !object) return false;
#if defined(_MSC_VER)
  __try {
#endif
    out = getter(object); return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
void *Resolve(void **slot, std::uint32_t id, std::size_t identity,
              void **fallback_slot) noexcept {
  if (id == UINT32_MAX || !slot || !fallback_slot) return nullptr;
  void *storage = nullptr, *rows = nullptr, *object = nullptr, *fallback = nullptr;
  std::int32_t count = 0; std::uint32_t actual = UINT32_MAX;
  const auto index = id & 0xFFFFFFU;
  if (!Load(slot, 0, storage) || !storage || !Load(storage, 0x20, rows) || !rows ||
      !Load(storage, 0x2C, count) || count <= 0 || count > 1'000'000 ||
      index >= static_cast<std::uint32_t>(count) ||
      !Load(rows, static_cast<std::size_t>(index) * 0x10 + 8, object) || !object ||
      !Load(fallback_slot, 0, fallback) || !fallback || object == fallback ||
      !Load(object, identity, actual) || actual != id) return nullptr;
  return object;
}
bool FaithType(const Bindings &b, void *faith, std::uint32_t id) noexcept {
  std::uintptr_t vptr = 0; std::uint32_t actual = UINT32_MAX, kind = 0;
  return faith && id != UINT32_MAX && Load(faith, 0, vptr) &&
      vptr == b.titles.properties.image_base + b.primary_faith_vtable_rva &&
      Load(faith, kFaithFullIdOffset, actual) && actual == id &&
      Load(faith, kFaithKindOffset, kind) && kind == kFaithKindMagic;
}
void *Faith(const Bindings &b, std::uint32_t id) noexcept {
  auto *faith = Resolve(b.faith_storage_slot, id, kFaithFullIdOffset,
                        b.titles.faith_fallback_slot);
  return FaithType(b, faith, id) ? faith : nullptr;
}
void *Character(const Bindings &b, std::uint32_t id) noexcept {
  const auto &h = b.titles.properties.title_holder;
  auto *c = Resolve(h.character_storage_slot, id, 0x18, h.character_fallback_slot);
  std::uint32_t kind = 0;
  return c && Load(c, 0x1C, kind) && kind == 0x43686172U ? c : nullptr;
}
void *Title(const Bindings &b, std::uint32_t id) noexcept {
  if (id == UINT32_MAX) return nullptr;
  void *title = nullptr;
#if defined(_MSC_VER)
  __try {
#endif
    title = ck3_12002::ResolveObjectiveTitle(
        b.titles.properties.title_holder.provinces, std::bit_cast<std::int32_t>(id));
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
#endif
  void *fallback = nullptr; std::uintptr_t vptr = 0;
  std::uint32_t actual = UINT32_MAX;
  return title && Load(b.titles.title_fallback_slot, 0, fallback) && title != fallback &&
      Load(title, 0, vptr) &&
      vptr == b.titles.properties.image_base + b.titles.properties.primary_title_vtable_rva &&
      Load(title, 0x10, actual) && actual == id ? title : nullptr;
}

struct FaithCapture {
  std::uint32_t id = UINT32_MAX;
  void *faith = nullptr, *data = nullptr, *storage = nullptr, *slots = nullptr;
  std::int32_t storage_count = 0, count = -1;
  std::vector<NativeRecord> records;
};
bool Same(const FaithCapture &a, const FaithCapture &b) noexcept {
  return a.id == b.id && a.faith == b.faith && a.data == b.data &&
      a.storage == b.storage && a.slots == b.slots &&
      a.storage_count == b.storage_count && a.count == b.count && a.records == b.records;
}
bool CaptureFaith(const Bindings &b, std::uint32_t id, FaithCapture &out,
                  std::string &reason) {
  reason = "faith_full_generation_or_type_unavailable";
  out.id = id; out.faith = Faith(b, id);
  if (!out.faith || !Load(b.faith_storage_slot, 0, out.storage) || !out.storage ||
      !Load(out.storage, 0x20, out.slots) || !out.slots ||
      !Load(out.storage, 0x2C, out.storage_count)) return false;
  reason = "faith_challenger_collection_unavailable";
  // +0xC8 capacity has not been qualified. No read or assumption uses it.
  if (!Load(out.faith, kFaithChallengersDataOffset, out.data) ||
      !Load(out.faith, kFaithChallengersCountOffset, out.count) ||
      out.count < 0 || out.count > kMaximumChallengersPerFaith ||
      (out.count > 0 && !out.data)) return false;
  out.records.resize(static_cast<std::size_t>(out.count));
  if (!CopyRecords(out.data, out.records.data(), out.records.size())) return false;
  std::vector<std::uint32_t> ids;
  ids.reserve(out.records.size());
  for (const auto &record : out.records) {
    if (record.challenger_title_full_id == UINT32_MAX) {
      reason = "absent_challenger_id_in_native_collection"; return false;
    }
    ids.push_back(record.challenger_title_full_id);
  }
  std::sort(ids.begin(), ids.end());
  if (std::adjacent_find(ids.begin(), ids.end()) != ids.end()) {
    reason = "duplicate_challenger_id_in_native_collection"; return false;
  }
  if (Faith(b, id) != out.faith) { reason = "faith_changed_during_collection_copy"; return false; }
  return true;
}

struct TitleGraph {
  void *title = nullptr, *holder = nullptr, *holder_faith = nullptr;
  std::uint32_t id = UINT32_MAX, holder_id = UINT32_MAX, faith_id = UINT32_MAX;
  bool operator==(const TitleGraph &) const = default;
};
bool CaptureTitle(const Bindings &b, std::uint32_t id, TitleGraph &g,
                  std::string &reason) {
  g.id = id;
  if (id == UINT32_MAX) return true;
  reason = "title_full_generation_or_type_unavailable";
  g.title = Title(b, id);
  if (!g.title || !Load(g.title, 0x128, g.holder_id)) return false;
  if (g.holder_id == UINT32_MAX) return true;
  reason = "title_holder_full_generation_unavailable";
  g.holder = Character(b, g.holder_id);
  if (!g.holder) return false;
  reason = "title_holder_current_faith_unavailable";
  if (!Call(b.titles.character_faith, g.holder, g.holder_faith) ||
      !g.holder_faith || !Load(g.holder_faith, kFaithFullIdOffset, g.faith_id) ||
      Faith(b, g.faith_id) != g.holder_faith) return false;
  return true;
}
bool ReadTitle(const Bindings &b, const game::Snapshot &frame, std::uint32_t id,
               TitleObservation &out, std::string &reason, TitleGraph &graph) {
  TitleGraph before, after;
  if (!CaptureTitle(b, id, before, reason)) return false;
  TitleObservation value;
  value.title_absent = id == UINT32_MAX;
  if (id == UINT32_MAX) {
    value.properties.unavailable_reason = "native_title_absent";
    value.laws.unavailable_reason = "native_title_absent";
  } else {
    value.title_full_id = id;
    value.native_title_class = "CLandedTitle";
    value.holder_absent = before.holder_id == UINT32_MAX;
    if (before.holder_id != UINT32_MAX) {
      value.holder_character_full_id = before.holder_id;
      value.holder_current_faith_full_id = before.faith_id;
    }
    if (!title_properties::Read(b.titles.properties, frame, id, value.properties)) {
      reason = value.properties.unavailable_reason; return false;
    }
    if (!title_laws::Read(b.titles.properties, frame, id, value.laws)) {
      reason = value.laws.unavailable_reason; return false;
    }
  }
  if (!CaptureTitle(b, id, after, reason) || before != after) {
    reason = "title_graph_changed_during_leaf_reads"; return false;
  }
  value.available = true; value.unavailable_reason.clear();
  graph = before; out = std::move(value); return true;
}

std::string Quote(std::string_view value) {
  std::string out = "\""; constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') { out += '\\'; out += static_cast<char>(c); }
    else if (c < 32) { out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15]; }
    else out += static_cast<char>(c);
  }
  return out + '"';
}
std::string Bool(bool value) { return value ? "true" : "false"; }
std::string Boolean(const std::optional<bool> &value) { return value ? Bool(*value) : "null"; }
template <class T> std::string Number(const std::optional<T> &value) {
  return value ? std::to_string(*value) : "null";
}
std::string Reason(bool available, std::string_view reason) {
  return available ? "null" : Quote(reason.empty() ? "observation_failed" : reason);
}
std::string Properties(const title_properties::Observation &p) {
  return "{\"available\":" + Bool(p.available) + ",\"unavailable_reason\":" + Reason(p.available, p.unavailable_reason) +
      ",\"destroy_if_invalid_heir\":" + (p.available ? Boolean(p.destroy_if_invalid_heir) : "null") +
      ",\"no_automatic_claims\":" + (p.available ? Boolean(p.no_automatic_claims) : "null") +
      ",\"definitive_form\":" + (p.available ? Boolean(p.definitive_form) : "null") +
      ",\"always_follows_primary_heir\":" + (p.available ? Boolean(p.always_follows_primary_heir) : "null") + "}";
}
std::string Laws(const title_laws::Observation &l) {
  std::string rows = "null";
  if (l.available && l.complete_laws) {
    rows = "["; bool first = true;
    for (const auto &law : *l.complete_laws) {
      if (!first) rows += ','; first = false;
      rows += "{\"native_definition_id\":" + std::to_string(law.native_definition_id) + ",\"key\":" + Quote(law.key) + "}";
    }
    rows += ']';
  }
  return "{\"available\":" + Bool(l.available) + ",\"unavailable_reason\":" + Reason(l.available, l.unavailable_reason) +
      ",\"native_count\":" + (l.available ? Number(l.native_count) : "null") + ",\"complete_laws\":" + rows +
      ",\"expected_law_key\":" + Quote(title_laws::kExpectedLawKey) + ",\"expected_law_member\":" +
      (l.available ? Boolean(l.temporal_head_of_faith_succession_law_member) : "null") + "}";
}
std::string TitleJson(const TitleObservation &t) {
  return "{\"available\":" + Bool(t.available) + ",\"unavailable_reason\":" + Reason(t.available, t.unavailable_reason) +
      ",\"title_absent\":" + Boolean(t.title_absent) + ",\"title_full_id\":" + Number(t.title_full_id) +
      ",\"native_title_class\":" + (t.native_title_class ? Quote(*t.native_title_class) : "null") +
      ",\"holder_absent\":" + Boolean(t.holder_absent) + ",\"holder_character_full_id\":" + Number(t.holder_character_full_id) +
      ",\"holder_current_faith_full_id\":" + Number(t.holder_current_faith_full_id) +
      ",\"title_properties\":" + Properties(t.properties) + ",\"title_laws\":" + Laws(t.laws) + "}";
}
std::string ChallengerJson(const ChallengerObservation &c) {
  return "{\"challenger_title_full_id\":" + std::to_string(c.challenger_title_full_id) +
      ",\"available\":" + Bool(c.available) + ",\"unavailable_reason\":" + Reason(c.available, c.unavailable_reason) +
      ",\"challenger_title\":" + TitleJson(c.challenger_title) + ",\"registered_sponsor_title\":" + TitleJson(c.registered_sponsor_title) +
      ",\"scope_sponsor_available\":" + Bool(c.scope_sponsor_available) +
      ",\"scope_lookup_complete\":" + Bool(c.scope_lookup_complete) +
      ",\"scope_sponsor_unavailable_reason\":" + Reason(c.scope_sponsor_available, c.scope_sponsor_unavailable_reason) +
      ",\"scope_lookup_faith_full_id\":" + Number(c.scope_lookup_faith_full_id) +
      ",\"scope_lookup_native_count\":" + Number(c.scope_lookup_native_count) +
      ",\"scope_lookup_faith_matches_collection\":" + Boolean(c.scope_lookup_faith_matches_collection) +
      ",\"scope_matches_registered_pair\":" + Boolean(c.scope_matches_registered_pair) +
      ",\"scope_sponsor_title\":" + TitleJson(c.scope_sponsor_title) + "}";
}
std::string FaithJson(const FaithObservation &f) {
  std::string ids = "null", rows = "null";
  if (f.complete_native_challenger_title_ids) {
    ids = "["; bool first = true;
    for (const auto id : *f.complete_native_challenger_title_ids) {
      if (!first) ids += ','; first = false; ids += std::to_string(id);
    }
    ids += ']';
  }
  if (f.challengers) {
    rows = "["; bool first = true;
    for (const auto &c : *f.challengers) { if (!first) rows += ','; first = false; rows += ChallengerJson(c); }
    rows += ']';
  }
  return "{\"requested_faith_full_id\":" + std::to_string(f.requested_faith_full_id) +
      ",\"available\":" + Bool(f.available) + ",\"collection_complete\":" + Bool(f.collection_complete) +
      ",\"unavailable_reason\":" + Reason(f.available, f.unavailable_reason) + ",\"native_count\":" + Number(f.native_count) +
      ",\"complete_native_challenger_title_ids\":" + ids + ",\"challengers\":" + rows + "}";
}

struct Pass {
  std::vector<FaithCapture> captures;
  std::vector<TitleGraph> title_graphs;
  std::vector<FaithObservation> faiths;
};
bool CacheFaith(const Bindings &b, std::uint32_t id, Pass &p, std::size_t &index,
                std::string &reason) {
  for (std::size_t i = 0; i < p.captures.size(); ++i) {
    if (p.captures[i].id == id) { index = i; return true; }
  }
  if (p.captures.size() >= kMaximumCapturedFaiths) {
    reason = "complete_scope_faith_collection_bound_exceeded"; return false;
  }
  FaithCapture capture;
  if (!CaptureFaith(b, id, capture, reason)) return false;
  std::size_t total = capture.records.size();
  for (const auto &row : p.captures) total += row.records.size();
  if (total > kMaximumTotalCapturedRecords) {
    reason = "complete_native_record_bound_exceeded"; return false;
  }
  index = p.captures.size(); p.captures.push_back(std::move(capture)); return true;
}
bool CapturePass(const Bindings &b, const game::Snapshot &frame,
                 std::span<const std::uint32_t> ids, Pass &pass, std::string &reason) {
  for (const auto id : ids) {
    std::size_t collection_index = 0;
    if (!CacheFaith(b, id, pass, collection_index, reason)) return false;
    // Copy before inserting other Faith captures; vector reallocation must not
    // invalidate a reference to the registered complete record array.
    const auto records = pass.captures[collection_index].records;
    FaithObservation f; f.requested_faith_full_id = id;
    f.native_count = static_cast<std::int32_t>(records.size());
    f.complete_native_challenger_title_ids.emplace(); f.challengers.emplace();
    for (const auto &record : records) {
      ChallengerObservation c; c.challenger_title_full_id = record.challenger_title_full_id;
      TitleGraph challenger_graph, registered_graph, scope_graph;
      if (!ReadTitle(b, frame, record.challenger_title_full_id, c.challenger_title, reason, challenger_graph) ||
          !ReadTitle(b, frame, record.sponsor_title_full_id, c.registered_sponsor_title, reason, registered_graph)) return false;
      pass.title_graphs.push_back(challenger_graph);
      pass.title_graphs.push_back(registered_graph);
      if (!c.challenger_title.holder_current_faith_full_id) {
        // Registered membership remains factual, but an absent holder does not
        // supply an independently qualified active challenger_sponsor scope.
        reason = "challenger_holder_current_faith_unavailable"; return false;
      }
      const auto scope_faith = *c.challenger_title.holder_current_faith_full_id;
      std::size_t scope_index = 0;
      if (!CacheFaith(b, scope_faith, pass, scope_index, reason)) return false;
      const auto &scope_records = pass.captures[scope_index].records;
      auto scope_sponsor = UINT32_MAX;
      for (const auto &candidate : scope_records) {
        if (candidate.challenger_title_full_id == record.challenger_title_full_id) {
          scope_sponsor = candidate.sponsor_title_full_id; break;
        }
      }
      if (!ReadTitle(b, frame, scope_sponsor, c.scope_sponsor_title, reason, scope_graph)) return false;
      pass.title_graphs.push_back(scope_graph);
      c.scope_lookup_faith_full_id = scope_faith;
      c.scope_lookup_native_count = static_cast<std::int32_t>(scope_records.size());
      c.scope_lookup_faith_matches_collection = scope_faith == id;
      c.scope_matches_registered_pair = scope_sponsor == record.sponsor_title_full_id;
      c.scope_sponsor_available = true; c.scope_lookup_complete = true;
      c.scope_sponsor_unavailable_reason.clear();
      c.available = true; c.unavailable_reason.clear();
      f.complete_native_challenger_title_ids->push_back(record.challenger_title_full_id);
      f.challengers->push_back(std::move(c));
    }
    f.available = true; f.collection_complete = true; f.unavailable_reason.clear();
    pass.faiths.push_back(std::move(f));
  }
  // Complete source snapshots include lookup Faiths outside the requested list.
  // None are selected through untrusted caller Title IDs.
  for (const auto &before : pass.captures) {
    FaithCapture after;
    if (!CaptureFaith(b, before.id, after, reason) || !Same(before, after)) {
      reason = "native_challenger_collection_changed"; return false;
    }
  }
  return true;
}
bool Same(const Pass &a, const Pass &b) {
  if (a.captures.size() != b.captures.size() || a.faiths.size() != b.faiths.size() ||
      a.title_graphs != b.title_graphs) return false;
  for (std::size_t i = 0; i < a.captures.size(); ++i) if (!Same(a.captures[i], b.captures[i])) return false;
  for (std::size_t i = 0; i < a.faiths.size(); ++i) if (FaithJson(a.faiths[i]) != FaithJson(b.faiths[i])) return false;
  return true;
}
} // namespace

Bindings BindImage(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b;
  if (base == 0 || (sha != kExecutableSha256 && sha != ck3_12004::kExecutableSha256))
    return b;
  b.titles = religious_title::BindImage(base, sha);
  if (!b.titles.enabled) return b;
  if (b.titles.properties.actual4) {
    b.faith_storage_slot = reinterpret_cast<void **>(
        base + ck3_12004::confucian_titles::kFaithStorageSlotRva);
    b.primary_faith_vtable_rva = ck3_12004::confucian_titles::kCFaithPrimaryVtableRva;
  } else {
    b.faith_storage_slot = reinterpret_cast<void **>(base + kFaithStorageSlotRva);
  }
  b.enabled = true; return b;
}
bool Read(const Bindings &b, const game::Snapshot &frame, std::uint64_t epoch,
          std::span<const std::uint32_t> ids, Observation &out) noexcept {
  try {
    out = {}; out.actual4 = b.titles.properties.actual4;
    out.capture_epoch = epoch; out.date_raw = frame.date_raw;
    out.played_character_id = frame.played_character_id;
    out.requested_faith_full_ids.assign(ids.begin(), ids.end());
    const auto fail = [&out](std::string_view reason) {
      out.available = false; out.graph_complete = false;
      out.faiths.reset(); out.unavailable_reason = reason; return false;
    };
    if (!b.enabled || !b.titles.enabled || !b.titles.properties.enabled ||
        !b.titles.properties.title_holder.enabled || !b.titles.properties.title_holder.provinces.enabled ||
        !b.faith_storage_slot || !b.titles.faith_fallback_slot || !b.titles.title_fallback_slot ||
        !b.titles.character_faith) return fail("challenger_graph_bindings_unavailable");
    if (!frame.paused || !frame.map_ready || !frame.has_played_character ||
        !frame.played_character_alive || frame.played_character_id == -1 || epoch == 0)
      return fail("paused_player_frame_unavailable");
    if (ids.empty() || ids.size() > kMaximumRequestedFaiths) return fail("faith_selector_invalid");
    for (std::size_t i = 0; i < ids.size(); ++i) {
      if (ids[i] == UINT32_MAX) return fail("faith_selector_invalid");
      for (std::size_t j = 0; j < i; ++j) if (ids[i] == ids[j]) return fail("faith_selector_invalid");
    }
    const auto actor_id = std::bit_cast<std::uint32_t>(frame.played_character_id);
    auto *actor = Character(b, actor_id);
    if (!actor) return fail("played_character_generation_unavailable");
    Pass first, second; std::string reason;
    if (!CapturePass(b, frame, ids, first, reason) ||
        !CapturePass(b, frame, ids, second, reason)) return fail(reason);
    if (Character(b, actor_id) != actor || !Same(first, second))
      return fail("native_challenger_graph_changed");
    out.faiths = std::move(first.faiths);
    out.available = true; out.graph_complete = true; out.unavailable_reason.clear(); return true;
  } catch (...) {
    out.available = false; out.graph_complete = false; out.faiths.reset();
    out.capture_epoch = epoch; out.date_raw = frame.date_raw;
    out.played_character_id = frame.played_character_id; out.unavailable_reason.clear(); return false;
  }
}
std::string Serialize(const Observation &o) {
  const auto version = o.actual4 ? ck3_12004::kGameVersion : kGameVersion;
  const auto sha = o.actual4 ? ck3_12004::kExecutableSha256 : kExecutableSha256;
  const auto faith_index = o.actual4 ? ck3_12004::confucian_titles::kFiniteMapSha256 :
      "712298a183573a588c24fd0a357e0d83d4e6886a9e5ddd45db7ddf8e5a3aba2d";
  const auto challenger_index = o.actual4 ? ck3_12004::confucian_titles::kFiniteMapSha256 :
      "3dffb1d4ee1fa0e100ea26b12f577841317ebdcae4d6e702282bad768ceadfb1";
  const auto record_index = o.actual4 ? ck3_12004::confucian_titles::kFiniteMapSha256 :
      "3e24fe49a46749ce353274c2a22659f229802a972b720b6153349effe01af35f";
  const auto properties_index = o.actual4 ? ck3_12004::confucian_titles::kFiniteMapSha256 :
      "14bf997b58a8ff33d7407ece6be2675917a2b7ed7e6ffdba70ca8ea938347a0a";
  const auto laws_index = o.actual4 ? ck3_12004::confucian_titles::kFiniteMapSha256 :
      "9d371bf97f50281c621d777890915d6767c354275222fa38d7e1127076afeb60";
  std::string ids = "["; bool first = true;
  for (const auto id : o.requested_faith_full_ids) { if (!first) ids += ','; first = false; ids += std::to_string(id); }
  ids += ']'; std::string rows = "null";
  if (o.available && o.graph_complete && o.faiths) {
    rows = "["; first = true;
    for (const auto &f : *o.faiths) { if (!first) rows += ','; first = false; rows += FaithJson(f); }
    rows += ']';
  }
  return "{\"schema\":\"ck3_12003_confucian_challenger_graph_v1\",\"game_version\":" + Quote(version) + ',' +
      "\"executable_sha256\":" + Quote(sha) + ",\"read_only\":true,\"available\":" + Bool(o.available) +
      ",\"graph_complete\":" + Bool(o.graph_complete) + ",\"unavailable_reason\":" + Reason(o.available, o.unavailable_reason) +
      ",\"capture_epoch\":" + std::to_string(o.capture_epoch) + ",\"date_raw\":" + std::to_string(o.date_raw) +
      ",\"played_character_id\":" + std::to_string(o.played_character_id) + ",\"played_character_full_id\":" +
      (o.played_character_id != -1 ? std::to_string(std::bit_cast<std::uint32_t>(o.played_character_id)) : "null") +
      ",\"requested_faith_full_ids\":" + ids + ",\"faiths\":" + rows +
      ",\"mod_owned_markers\":null,\"saved_owner_faith_variables\":null,\"qualification\":{"
      "\"kind\":\"exact_current_static_abi\",\"faith_rtti_index_sha256\":" + Quote(faith_index) + ',' +
      "\"faith_challenger_abi_index_sha256\":" + Quote(challenger_index) + ',' +
      "\"record_layout_index_sha256\":" + Quote(record_index) + ',' +
      "\"title_properties_index_sha256\":" + Quote(properties_index) + ',' +
      "\"title_laws_index_sha256\":" + Quote(laws_index) + ',' +
      "\"runtime_acceptance\":null}}";
}
} // namespace xar::ck3_12003::challenger_graph
