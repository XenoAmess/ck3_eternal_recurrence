#include "xar_bridge/ck3_12003_religious_title_readback.hpp"

#include <bit>
#include <cstring>
#include <utility>

#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12003::religious_title {
namespace {
template <class T>
bool Load(const void *base, std::size_t offset, T &value) noexcept {
  if (base == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(T));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool Call(ObjectGetter getter, void *object, void *&result) noexcept {
  if (getter == nullptr || object == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    result = getter(object);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

void *ResolveTitle(const Bindings &b, std::uint32_t id) noexcept {
  if (id == UINT32_MAX) return nullptr;
#if defined(_MSC_VER)
  __try {
#endif
    return ck3_12002::ResolveObjectiveTitle(
        b.properties.title_holder.provinces, std::bit_cast<std::int32_t>(id));
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
#endif
}

void *ResolveCharacter(const TitleHolderBindingsV1 &b, std::uint32_t id) noexcept {
  if (id == UINT32_MAX) return nullptr;
  void *storage = nullptr, *slots = nullptr, *character = nullptr, *fallback = nullptr;
  std::int32_t capacity = 0;
  std::uint32_t full_id = UINT32_MAX, magic = 0;
  const auto index = id & 0xFFFFFFU;
  if (!Load(b.character_storage_slot, 0, storage) || storage == nullptr ||
      !Load(storage, 0x20, slots) || slots == nullptr ||
      !Load(storage, 0x2C, capacity) || capacity <= 0 || capacity > 1'000'000 ||
      index >= static_cast<std::uint32_t>(capacity) ||
      !Load(slots, static_cast<std::size_t>(index) * 0x10 + 8, character) ||
      character == nullptr || !Load(b.character_fallback_slot, 0, fallback) ||
      character == fallback || !Load(character, 0x18, full_id) || full_id != id ||
      !Load(character, 0x1C, magic) || magic != 0x43686172U) return nullptr;
  return character;
}

bool ReadLegacyHolder(const Bindings &b, const game::Snapshot &frame,
                      std::uint32_t title_id, game::TitleHolderV1 &out) noexcept {
  if (std::bit_cast<std::int32_t>(title_id) < 0) {
    out = {};
    out.date_raw = frame.date_raw;
    out.actor_character_id = frame.played_character_id;
    out.title_id = std::bit_cast<std::int32_t>(title_id);
    out.unavailable_reason = "legacy_signed_title_id_boundary";
    return false;
  }
#if defined(_MSC_VER)
  __try {
#endif
    return ReadTitleHolderV1(b.properties.title_holder, frame,
        std::bit_cast<std::int32_t>(title_id), out) ==
        game::ReadTitleHolderV1Result::available;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    out = {};
    out.unavailable_reason = "legacy_holder_native_access_failed";
    return false;
  }
#endif
}

struct Graph {
  void *actor = nullptr, *faith = nullptr, *title = nullptr, *holder = nullptr;
  void *title_fallback = nullptr, *character_fallback = nullptr, *faith_fallback = nullptr;
  std::uintptr_t title_vptr = 0;
  std::uint32_t faith_id = UINT32_MAX, title_id = UINT32_MAX, holder_id = UINT32_MAX;
};

bool Same(const Graph &a, const Graph &b) noexcept {
  return a.actor == b.actor && a.faith == b.faith && a.title == b.title &&
      a.holder == b.holder && a.title_fallback == b.title_fallback &&
      a.character_fallback == b.character_fallback && a.faith_fallback == b.faith_fallback &&
      a.title_vptr == b.title_vptr &&
      a.faith_id == b.faith_id && a.title_id == b.title_id && a.holder_id == b.holder_id;
}

bool CaptureGraph(const Bindings &b, const game::Snapshot &frame, Graph &g,
                  std::string_view &reason) noexcept {
  reason = "native_actor_generation_unavailable";
  g.actor = ResolveCharacter(b.properties.title_holder,
                            std::bit_cast<std::uint32_t>(frame.played_character_id));
  if (g.actor == nullptr) return false;
  reason = "native_faith_unavailable";
  if (!Load(b.faith_fallback_slot, 0, g.faith_fallback) ||
      !Call(b.character_faith, g.actor, g.faith) || g.faith == nullptr ||
      g.faith == g.faith_fallback ||
      !Load(g.faith, kFaithReferenceIdentityOffset, g.faith_id) ||
      g.faith_id == UINT32_MAX) return false;
  reason = "native_faith_head_title_reference_unavailable";
  if (!Load(g.faith, kFaithHeadTitleIdOffset, g.title_id) ||
      !Load(b.title_fallback_slot, 0, g.title_fallback) ||
      !Load(b.properties.title_holder.character_fallback_slot, 0,
            g.character_fallback)) return false;
  void *getter_title = nullptr, *getter_holder = nullptr;
  if (!Call(b.faith_head_title, g.faith, getter_title) ||
      !Call(b.faith_head, g.faith, getter_holder)) return false;
  if (g.title_id == UINT32_MAX) {
    reason = "native_absent_head_getter_mismatch";
    // Native getters return their typed fallback, rather than an invented ID.
    return getter_title == g.title_fallback && getter_holder == g.character_fallback;
  }
  reason = "native_title_generation_or_type_unavailable";
  g.title = ResolveTitle(b, g.title_id);
  std::uint32_t actual_title_id = UINT32_MAX;
  if (g.title == nullptr || g.title == g.title_fallback || getter_title != g.title ||
      !Load(g.title, 0x10, actual_title_id) || actual_title_id != g.title_id ||
      !Load(g.title, 0, g.title_vptr) ||
      g.title_vptr != b.properties.image_base +
          title_properties::kCLandedTitlePrimaryVtableRva ||
      !Load(g.title, 0x128, g.holder_id)) return false;
  reason = "native_title_holder_generation_or_getter_unavailable";
  if (g.holder_id == UINT32_MAX) return getter_holder == g.character_fallback;
  g.holder = ResolveCharacter(b.properties.title_holder, g.holder_id);
  return g.holder != nullptr && getter_holder == g.holder;
}

bool Same(const title_properties::Observation &a,
          const title_properties::Observation &b) noexcept {
  return a.available == b.available && a.requested_title_full_id == b.requested_title_full_id &&
      a.date_raw == b.date_raw && a.actor_character_id == b.actor_character_id &&
      a.destroy_if_invalid_heir == b.destroy_if_invalid_heir &&
      a.no_automatic_claims == b.no_automatic_claims &&
      a.definitive_form == b.definitive_form &&
      a.always_follows_primary_heir == b.always_follows_primary_heir;
}

bool Same(const title_laws::Observation &a, const title_laws::Observation &b) noexcept {
  if (!a.available || !b.available || a.date_raw != b.date_raw ||
      a.actor_character_id != b.actor_character_id ||
      a.requested_title_full_id != b.requested_title_full_id ||
      a.native_count != b.native_count ||
      a.temporal_head_of_faith_succession_law_member !=
          b.temporal_head_of_faith_succession_law_member ||
      !a.complete_laws || !b.complete_laws ||
      a.complete_laws->size() != b.complete_laws->size()) return false;
  for (std::size_t i = 0; i < a.complete_laws->size(); ++i) {
    const auto &x = (*a.complete_laws)[i];
    const auto &y = (*b.complete_laws)[i];
    if (x.native_definition_id != y.native_definition_id || x.key != y.key) return false;
  }
  return true;
}

bool Same(const game::TitleHolderV1 &a, const game::TitleHolderV1 &b) noexcept {
  return a.available == b.available && a.unavailable_reason == b.unavailable_reason &&
      a.date_raw == b.date_raw && a.actor_character_id == b.actor_character_id &&
      a.title_id == b.title_id && a.title_tier_raw == b.title_tier_raw &&
      a.title_tier_key == b.title_tier_key && a.holder_character_id == b.holder_character_id &&
      a.holder_is_player == b.holder_is_player &&
      a.holder_in_player_realm == b.holder_in_player_realm &&
      a.holder_immediate_liege_character_id == b.holder_immediate_liege_character_id &&
      a.holder_top_liege_character_id == b.holder_top_liege_character_id;
}

std::string Quote(std::string_view text) {
  std::string out = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char c : text) {
    if (c == '"' || c == '\\') { out += '\\'; out += static_cast<char>(c); }
    else if (c < 32) {
      out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15];
    } else out += static_cast<char>(c);
  }
  return out + '"';
}
std::string Bool(bool value) { return value ? "true" : "false"; }
std::string Boolean(const std::optional<bool> &value) {
  return value ? Bool(*value) : "null";
}
template <class T> std::string Number(const std::optional<T> &value) {
  return value ? std::to_string(*value) : "null";
}
std::string FullId(const std::optional<std::int32_t> &id) {
  return id ? std::to_string(std::bit_cast<std::uint32_t>(*id)) : "null";
}
std::string Text(const std::optional<std::string> &value) {
  return value ? Quote(*value) : "null";
}
std::string Reason(bool available, std::string_view reason) {
  return available ? "null" : Quote(reason.empty() ? "observation_failed" : reason);
}
std::string Properties(const title_properties::Observation &p) {
  return "{\"available\":" + Bool(p.available) + ",\"unavailable_reason\":" +
      Reason(p.available, p.unavailable_reason) +
      ",\"destroy_if_invalid_heir\":" + (p.available ? Boolean(p.destroy_if_invalid_heir) : "null") +
      ",\"no_automatic_claims\":" + (p.available ? Boolean(p.no_automatic_claims) : "null") +
      ",\"definitive_form\":" + (p.available ? Boolean(p.definitive_form) : "null") +
      ",\"always_follows_primary_heir\":" + (p.available ? Boolean(p.always_follows_primary_heir) : "null") + "}";
}
std::string Laws(const title_laws::Observation &l) {
  std::string rows = "null";
  if (l.available && l.complete_laws) {
    rows = "[";
    bool first = true;
    for (const auto &law : *l.complete_laws) {
      if (!first) rows += ',';
      first = false;
      rows += "{\"native_definition_id\":" + std::to_string(law.native_definition_id) +
          ",\"key\":" + Quote(law.key) + "}";
    }
    rows += ']';
  }
  return "{\"available\":" + Bool(l.available) + ",\"unavailable_reason\":" +
      Reason(l.available, l.unavailable_reason) + ",\"native_count\":" +
      (l.available ? Number(l.native_count) : "null") +
      ",\"complete_laws\":" + rows + ",\"expected_law_key\":" +
      Quote(title_laws::kExpectedLawKey) +
      ",\"temporal_head_of_faith_succession_law_member\":" +
      (l.available ? Boolean(l.temporal_head_of_faith_succession_law_member) : "null") + "}";
}
std::string LegacyHolder(const game::TitleHolderV1 &h) {
  return "{\"available\":" + Bool(h.available) + ",\"unavailable_reason\":" +
      Reason(h.available, h.unavailable_reason) + ",\"title_tier_raw\":" +
      (h.available ? std::to_string(h.title_tier_raw) : "null") +
      ",\"title_tier_key\":" + (h.available ? Quote(h.title_tier_key) : "null") +
      ",\"holder_character_full_id\":" + (h.available ? FullId(h.holder_character_id) : "null") +
      ",\"holder_is_player\":" + (h.available ? Bool(h.holder_is_player) : "null") +
      ",\"holder_in_player_realm\":" + (h.available ? Bool(h.holder_in_player_realm) : "null") +
      ",\"holder_immediate_liege_character_full_id\":" +
      (h.available ? FullId(h.holder_immediate_liege_character_id) : "null") +
      ",\"holder_top_liege_character_full_id\":" +
      (h.available ? FullId(h.holder_top_liege_character_id) : "null") + "}";
}
} // namespace

Bindings BindImage(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (base == 0 || sha != kExecutableSha256) return b;
  b.properties = title_properties::BindImage(base, sha);
  if (!b.properties.enabled) return b;
  // Direct exact-current binding: no old executable hash is supplied here.
  b.character_faith = reinterpret_cast<ObjectGetter>(base + kCurrentCharacterFaithGetterRva);
  b.faith_head = reinterpret_cast<ObjectGetter>(base + kCurrentFaithHeadGetterRva);
  b.faith_head_title = reinterpret_cast<ObjectGetter>(base + kCurrentFaithHeadTitleGetterRva);
  b.title_fallback_slot = reinterpret_cast<void **>(base + kCurrentTitleFallbackSlotRva);
  b.faith_fallback_slot = reinterpret_cast<void **>(base + kCurrentFaithFallbackSlotRva);
  b.enabled = true;
  return b;
}

bool Read(const Bindings &b, const game::Snapshot &frame, std::uint64_t epoch,
          Observation &out) noexcept {
  try {
    out = {};
    out.capture_epoch = epoch;
    out.date_raw = frame.date_raw;
    out.played_character_id = frame.played_character_id;
    const auto fail = [&out](std::string_view reason) {
      out.available = false;
      out.unavailable_reason = reason;
      out.graph_unavailable_reason = reason;
      return false;
    };
    if (!b.enabled || !b.properties.enabled || b.properties.image_base == 0 ||
        !b.properties.title_holder.enabled || !b.properties.title_holder.provinces.enabled ||
        !b.title_fallback_slot || !b.faith_fallback_slot ||
        !b.character_faith || !b.faith_head || !b.faith_head_title)
      return fail("religious_title_bindings_unavailable");
    if (!frame.paused || !frame.map_ready || !frame.has_played_character ||
        !frame.played_character_alive)
      return fail("paused_player_frame_unavailable");
    Graph first, second, third;
    std::string_view graph_reason;
    if (!CaptureGraph(b, frame, first, graph_reason)) return fail(graph_reason);
    title_properties::Observation properties_first, properties_second;
    title_laws::Observation laws_first, laws_second;
    game::TitleHolderV1 holder_first, holder_second;
    if (first.title_id != UINT32_MAX) {
      if (!title_properties::Read(b.properties, frame, first.title_id, properties_first))
        return fail(properties_first.unavailable_reason);
      if (!title_laws::Read(b.properties, frame, first.title_id, laws_first))
        return fail(laws_first.unavailable_reason);
      ReadLegacyHolder(b, frame, first.title_id, holder_first);
    }
    if (!CaptureGraph(b, frame, second, graph_reason) || !Same(first, second))
      return fail("native_religious_title_graph_changed");
    if (first.title_id != UINT32_MAX) {
      if (!title_properties::Read(b.properties, frame, first.title_id, properties_second) ||
          !title_laws::Read(b.properties, frame, first.title_id, laws_second))
        return fail("native_religious_title_leaves_changed_or_unavailable");
      ReadLegacyHolder(b, frame, first.title_id, holder_second);
      if (!Same(properties_first, properties_second) || !Same(laws_first, laws_second) ||
          !Same(holder_first, holder_second))
        return fail("native_religious_title_leaves_changed");
      // Cross-check the legacy subrow only when it is qualified. Native graph
      // remains complete even when the historical signed TitleID gate rejects it.
      if (holder_first.available &&
          (holder_first.holder_character_id
              ? std::bit_cast<std::uint32_t>(*holder_first.holder_character_id) : UINT32_MAX)
              != first.holder_id)
        return fail("native_religious_title_holder_subrow_mismatch");
    }
    if (!CaptureGraph(b, frame, third, graph_reason) || !Same(first, third))
      return fail("native_religious_title_graph_changed");
    Observation value;
    value.capture_epoch = epoch;
    value.date_raw = frame.date_raw;
    value.played_character_id = frame.played_character_id;
    value.graph_available = true;
    value.graph_unavailable_reason.clear();
    value.faith_full_id = first.faith_id;
    value.legal_head_title_absent = first.title_id == UINT32_MAX;
    if (first.title_id == UINT32_MAX) {
      value.title_holder.unavailable_reason = "native_head_title_absent";
      value.title_properties.unavailable_reason = "native_head_title_absent";
      value.title_laws.unavailable_reason = "native_head_title_absent";
    } else {
      value.head_title_full_id = first.title_id;
      value.native_title_class = "CLandedTitle";
      value.native_title_holder_absent = first.holder_id == UINT32_MAX;
      if (first.holder_id != UINT32_MAX) value.native_title_holder_full_id = first.holder_id;
      value.title_holder = holder_first;
      value.title_properties = properties_first;
      value.title_laws = std::move(laws_first);
    }
    value.available = true;
    value.unavailable_reason.clear();
    out = std::move(value);
    return true;
  } catch (...) {
    // No partial graph, default false predicate or incomplete law list survives.
    out.available = false;
    out.graph_available = false;
    out.capture_epoch = epoch;
    out.date_raw = frame.date_raw;
    out.played_character_id = frame.played_character_id;
    out.faith_full_id.reset();
    out.head_title_full_id.reset();
    out.native_title_holder_full_id.reset();
    out.native_title_holder_absent.reset();
    out.legal_head_title_absent.reset();
    out.native_title_class.reset();
    out.title_holder = {};
    out.title_properties = {};
    out.title_laws = {};
    // Empty reasons are legal valid JSON if allocation itself failed.
    out.unavailable_reason.clear();
    out.graph_unavailable_reason.clear();
    return false;
  }
}

std::string Serialize(const Observation &o) {
  return "{\"schema\":\"ck3_12003_confucian_religious_title_v1\","
      "\"game_version\":\"1.20.0.3\",\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"available\":" + Bool(o.available) + ",\"unavailable_reason\":" +
      Reason(o.available, o.unavailable_reason) + ",\"capture_epoch\":" +
      std::to_string(o.capture_epoch) + ",\"date_raw\":" + std::to_string(o.date_raw) +
      ",\"played_character_id\":" + std::to_string(o.played_character_id) +
      ",\"played_character_full_id\":" +
      (o.played_character_id != -1
          ? std::to_string(std::bit_cast<std::uint32_t>(o.played_character_id)) : "null") +
      ",\"graph_available\":" + Bool(o.graph_available) + ",\"graph_unavailable_reason\":" +
      Reason(o.graph_available, o.graph_unavailable_reason) +
      ",\"legal_head_title_absent\":" + Boolean(o.legal_head_title_absent) +
      ",\"faith_full_id\":" + Number(o.faith_full_id) +
      ",\"head_title_full_id\":" + Number(o.head_title_full_id) +
      ",\"native_title_holder_full_id\":" + Number(o.native_title_holder_full_id) +
      ",\"native_title_holder_absent\":" + Boolean(o.native_title_holder_absent) +
      ",\"native_title_class\":" + Text(o.native_title_class) +
      ",\"title_holder\":" + LegacyHolder(o.title_holder) +
      ",\"title_properties\":" + Properties(o.title_properties) +
      ",\"title_laws\":" + Laws(o.title_laws) +
      ",\"mod_owned_marker\":null,\"mod_owner_faith_variable\":null,"
      "\"qualification\":{\"kind\":\"exact_current_static_abi\","
      "\"title_properties_index_sha256\":\"14bf997b58a8ff33d7407ece6be2675917a2b7ed7e6ffdba70ca8ea938347a0a\","
      "\"title_laws_index_sha256\":\"9d371bf97f50281c621d777890915d6767c354275222fa38d7e1127076afeb60\","
      "\"head_getters_index_sha256\":\"d93f24e7be97fc7a59c35b76313e9b7a10f8d97dcb7534015b504373aa2dd973\","
      "\"faith_reference_identity_offset\":8,\"title_full_id_offset\":16,"
      "\"faith_typed_fallback_slot_rva\":\"0x5D1E2E0\","
      "\"runtime_acceptance\":null}}";
}
} // namespace xar::ck3_12003::religious_title
