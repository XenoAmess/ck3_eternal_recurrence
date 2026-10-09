#include "xar_bridge/ck3_12004_person_local_titles.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <sstream>
#include <utility>

namespace xar::ck3_12004 {
namespace {
// Source first: external after-government53/native-tree/ACTUAL-HELPER-SOURCE-TREE.
// Actual291E3A0 2310B,291ECB0 966B and held230F8E0 118B. No native calls,
// initialization, physical temporary allocation, Model writes or stage copies.
constexpr std::uintptr_t kTitleRegistry = 0x5D1DAF8;
constexpr std::uintptr_t kTitleFallback = 0x5D1DAE0;
constexpr std::uintptr_t kDefaultHeader = 0x5459C88;
constexpr std::uintptr_t kCountyDataFallback = 0x5D21900;

template <class T>
std::optional<T> Copy(const PersonCarrierDirect12004Bindings &b, std::uintptr_t p) {
  T value{};
  if (!b.read_memory || !b.read_memory(b.read_context,
      reinterpret_cast<const void *>(p), &value, sizeof(value))) return std::nullopt;
  return value;
}

PersonFollowing2922680Resolution ResolveTitle(
    const PersonCarrierDirect12004Bindings &b, std::uint32_t full,
    std::optional<std::uintptr_t> held_registry = std::nullopt,
    std::optional<std::uintptr_t> held_fallback = std::nullopt) {
  PersonFollowing2922680Resolution r;
  r.requested_full_id_u32 = full;
  r.registry_identity = held_registry ? held_registry
      : Copy<std::uintptr_t>(b, b.module_base + kTitleRegistry);
  if (!r.registry_identity) { r.reason = "registry_slot_unread"; return r; }
  bool fallback = *r.registry_identity == 0;
  if (!fallback) {
    r.registry_count_u32 = Copy<std::uint32_t>(b, *r.registry_identity + 0x2C);
    if (!r.registry_count_u32) { r.reason = "registry_count_unread"; return r; }
    const auto index = full & 0xFFFFFFU;
    fallback = index >= *r.registry_count_u32;
    if (!fallback) {
      r.registry_slots_identity = Copy<std::uintptr_t>(b, *r.registry_identity + 0x20);
      if (!r.registry_slots_identity || !*r.registry_slots_identity) {
        r.reason = "registry_slots_unread"; return r;
      }
      r.candidate_identity = Copy<std::uintptr_t>(b,
          *r.registry_slots_identity + static_cast<std::uintptr_t>(index) * 16 + 8);
      if (!r.candidate_identity) { r.reason = "registry_candidate_unread"; return r; }
      fallback = *r.candidate_identity == 0;
      if (!fallback) {
        r.candidate_full_id_u32 = Copy<std::uint32_t>(b, *r.candidate_identity + 0x10);
        if (!r.candidate_full_id_u32) { r.reason = "candidate_full_id_unread"; return r; }
        fallback = *r.candidate_full_id_u32 != full;
      }
    }
  }
  r.selection = fallback ? "fallback" : "mapped";
  r.selected_identity = fallback ? (held_fallback ? held_fallback
      : Copy<std::uintptr_t>(b, b.module_base + kTitleFallback)) : r.candidate_identity;
  if (!r.selected_identity || !*r.selected_identity) {
    r.reason = "selected_title_unread"; return r;
  }
  r.ready = true;
  return r;
}

template <class T>
std::optional<std::vector<T>> Array(const PersonCarrierDirect12004Bindings &b,
    const std::optional<std::uintptr_t> &p, std::int32_t n) {
  if (!p || !*p) return std::nullopt;
  std::vector<T> a(static_cast<std::size_t>(n));
  if (!b.read_memory(b.read_context, reinterpret_cast<const void *>(*p),
                     a.data(), a.size() * sizeof(T))) return std::nullopt;
  return a;
}

void ReadPc(const PersonCarrierDirect12004Bindings &b, std::uintptr_t p,
            PersonFollowing2922680Pc &r) {
  r.admitted = true;
  r.identity = p;
  r.count_i32 = Copy<std::int32_t>(b, p + 0xC);
  if (!r.count_i32) { r.reason = "pc_count_unread"; return; }
  if (*r.count_i32 < 0) { r.reason = "pc_count_negative"; return; }
  r.properties.emplace();
  if (*r.count_i32 == 0) {
    r.properties->keys_u16.emplace(); r.properties->values_q64.emplace();
    r.ready = true; return;
  }
  r.properties->keys_u16 = Array<std::uint16_t>(b, Copy<std::uintptr_t>(b, p), *r.count_i32);
  r.properties->values_q64 = Array<std::int64_t>(b, Copy<std::uintptr_t>(b, p + 0x68), *r.count_i32);
  if (!r.properties->keys_u16 && !r.properties->values_q64) r.reason = "pc_keys_and_values_unread";
  else if (!r.properties->keys_u16) r.reason = "pc_keys_unread";
  else if (!r.properties->values_q64) r.reason = "pc_values_unread";
  else r.ready = true;
}

void Empty(PersonLocalTitlesPcFamily12004 &f) {
  f.ready = true; f.count_i32 = 0; f.known_empty = true;
}

void ReadPcList(const PersonCarrierDirect12004Bindings &b, std::uintptr_t owner,
                std::uintptr_t data_offset, std::uintptr_t count_offset,
                std::uintptr_t pc_offset, PersonLocalTitlesPcFamily12004 &f) {
  f.array_identity = Copy<std::uintptr_t>(b, owner + data_offset);
  f.count_i32 = Copy<std::int32_t>(b, owner + count_offset);
  if (!f.array_identity) { f.reason = "source_array_unread"; return; }
  if (!f.count_i32) { f.reason = "source_count_unread"; return; }
  if (*f.count_i32 < 0) { f.reason = "source_count_negative"; return; }
  if (*f.count_i32 == 0) { Empty(f); return; }
  if (!*f.array_identity) { f.reason = "source_array_unread"; return; }
  bool complete = true, empty = true;
  for (std::uint32_t i = 0; i < static_cast<std::uint32_t>(*f.count_i32); ++i) {
    PersonFollowing2922680Pc pc;
    pc.admitted = true;
    const auto source = Copy<std::uintptr_t>(b, *f.array_identity + static_cast<std::uintptr_t>(i) * 8);
    if (!source) pc.reason = "source_pointer_unread";
    else if (!*source) pc.reason = "source_pointer_null";
    else ReadPc(b, *source + pc_offset, pc);
    complete = complete && pc.ready;
    if (pc.count_i32 && *pc.count_i32 > 0) empty = false;
    f.source_pcs.push_back(std::move(pc));
  }
  f.ready = complete;
  if (!empty) f.known_empty = false;
  else if (complete) f.known_empty = true;
  if (!complete) f.reason = "source_pcs_partial";
}

std::optional<std::uintptr_t> ProvinceForTitle(
    const PersonCarrierDirect12004Bindings &b, std::uintptr_t title,
    std::string &reason) {
  // Held actual230F8E0: county follows first child repeatedly, otherwise338.
  // Registry/fallback are loaded once when the initial title is a county.
  std::optional<std::uintptr_t> registry, fallback;
  bool loaded = false;
  while (title) {

    const auto definition = Copy<std::uintptr_t>(b, title + 0x48);
    if (!definition || !*definition) { reason = "province_template_unread"; return std::nullopt; }
    const auto tier = Copy<std::int32_t>(b, *definition + 0x64);
    if (!tier) { reason = "province_tier_unread"; return std::nullopt; }
    if (*tier != 2) {
      const auto p = Copy<std::uintptr_t>(b, title + 0x338);
      if (!p || !*p) reason = "province_pointer_unread";
      return p && *p ? p : std::nullopt;
    }
    if (!loaded) {
      registry = Copy<std::uintptr_t>(b, b.module_base + kTitleRegistry);
      fallback = Copy<std::uintptr_t>(b, b.module_base + kTitleFallback);
      if (!registry || !fallback) { reason = "province_title_slots_unread"; return std::nullopt; }
      loaded = true;
    }
    const auto count = Copy<std::int32_t>(b, title + 0x11C);
    if (!count) { reason = "province_child_count_unread"; return std::nullopt; }
    std::optional<std::uint32_t> full{0xFFFFFFFFU};
    if (*count != 0) {
      const auto data = Copy<std::uintptr_t>(b, title + 0x110);
      if (!data || !*data) { reason = "province_child_array_unread"; return std::nullopt; }
      full = Copy<std::uint32_t>(b, *data);
    }
    if (!full) { reason = "province_child_id_unread"; return std::nullopt; }
    const auto selected = ResolveTitle(b, *full, registry, fallback);
    if (!selected.ready) { reason = "province_" + selected.reason; return std::nullopt; }
    title = *selected.selected_identity;
  }
  reason = "province_title_missing";
  return std::nullopt;
}

void ReadPrimary(const PersonCarrierDirect12004Bindings &b, std::uintptr_t title,
                 std::int32_t tier, PersonLocalTitlesPcFamily12004 &f) {
  if (tier != 1 && tier != 2) { Empty(f); return; }
  const auto province = ProvinceForTitle(b, title, f.reason);
  if (!province) return;
  if (tier == 1) {
    f.count_i32 = 1;
    f.source_pcs.emplace_back();
    ReadPc(b, *province + 0x278, f.source_pcs.back());
    f.ready = f.source_pcs.back().ready;
    if (f.ready) f.known_empty = *f.source_pcs.back().count_i32 == 0;
    else f.reason = "source_pcs_partial";
    return;
  }
  const auto magic = Copy<std::uint32_t>(b, *province + 0x85C);
  if (!magic) { f.reason = "province_magic_unread"; return; }
  const auto owner = *magic == 0x50726F76U
      ? Copy<std::uintptr_t>(b, *province + 0x848)
      : Copy<std::uintptr_t>(b, b.module_base + kCountyDataFallback);
  if (!owner || !*owner) { f.reason = "county_data_unread"; return; }
  ReadPcList(b, *owner, 0x28, 0x34, 0x438, f);
}

void ReadRow(const PersonCarrierDirect12004Bindings &b, std::uintptr_t address,
             PersonLocalTitlesRow12004 &r) {
  r.requested_title_full_id_u32 = Copy<std::uint32_t>(b, address);
  if (!r.requested_title_full_id_u32) { r.reason = "requested_title_full_id_unread"; return; }
  r.resolution = ResolveTitle(b, *r.requested_title_full_id_u32);
  if (!r.resolution.ready) { r.reason = r.resolution.reason; return; }
  const auto title = *r.resolution.selected_identity;
  r.selected_title_full_id_u32 = Copy<std::uint32_t>(b, title + 0x10);
  r.exclusion_byte_130_u8 = Copy<std::uint8_t>(b, title + 0x130);
  if (!r.exclusion_byte_130_u8) { r.reason = "exclusion_byte_130_unread"; return; }
  if (*r.exclusion_byte_130_u8 != 0) {
    r.native_contribution_eligible = false; r.exclusion = "byte_130_nonzero";
  } else {
    r.exclusion_dword_12c_i32 = Copy<std::int32_t>(b, title + 0x12C);
    if (!r.exclusion_dword_12c_i32) { r.reason = "exclusion_dword_12c_unread"; return; }
    r.native_contribution_eligible = *r.exclusion_dword_12c_i32 == -1;
    r.exclusion = *r.native_contribution_eligible ? "eligible" : "dword_12c_not_minus_one";
  }
  if (!*r.native_contribution_eligible) {
    r.input_ready = r.ready = r.supplemental_ready = true;
    Empty(r.composer); Empty(r.primary); return;
  }
  // These source families remain independently copied across missing siblings.
  r.template_identity = Copy<std::uintptr_t>(b, title + 0x48);
  if (r.template_identity && *r.template_identity)
    r.template_tier_i32 = Copy<std::int32_t>(b, *r.template_identity + 0x64);
  r.input_ready = r.template_tier_i32.has_value();
  ReadPcList(b, title, 0x228, 0x234, 0xD8, r.composer);
  if (!r.template_tier_i32) {
    r.reason = "template_tier_unread";
    r.primary.reason = "template_tier_unread";
    r.supplemental_reason = "template_tier_unread";
    return;
  }
  const auto tier = *r.template_tier_i32;
  ReadPrimary(b, title, tier, r.primary);
  if (tier != 2) r.supplemental_ready = true;
  else {
    r.supplemental_array_identity = Copy<std::uintptr_t>(b, title + 0x1E0);
    r.supplemental_count_i32 = Copy<std::int32_t>(b, title + 0x1EC);
    if (!r.supplemental_array_identity) r.supplemental_reason = "tier2_supplemental_array_unread";
    else if (!r.supplemental_count_i32) r.supplemental_reason = "tier2_supplemental_count_unread";
    else if (*r.supplemental_count_i32 == 0) r.supplemental_ready = true;
    else r.supplemental_reason = *r.supplemental_count_i32 < 0
        ? "tier2_supplemental_count_negative" : "tier2_supplemental_inputs_unobserved";
  }
  r.ready = r.input_ready && r.composer.ready && r.primary.ready && r.supplemental_ready;
  if (!r.ready) r.reason = !r.composer.ready ? "composer_inputs_partial"
      : !r.primary.ready ? "primary_inputs_partial" : r.supplemental_reason;
}

std::string Quote(const std::string &s) {
  std::ostringstream o; o << '"';
  for (const auto c : s) {
    if (c == '"' || c == '\\') o << '\\' << c;
    else if (c == '\n') o << "\\n";
    else if (c == '\r') o << "\\r";
    else if (c == '\t') o << "\\t";
    else o << c;
  }
  o << '"'; return o.str();
}
template <class T> std::string Number(const std::optional<T> &v) {
  return v ? std::to_string(+*v) : "null";
}
std::string Pointer(const std::optional<std::uintptr_t> &v) {
  if (!v) return "null";
  std::ostringstream o; o << "0x" << std::hex << *v;
  return Quote(o.str());
}
std::string Reason(const std::string &v) { return v.empty() ? "null" : Quote(v); }
std::string Boolean(bool v) { return v ? "true" : "false"; }
std::string Boolean(const std::optional<bool> &v) { return v ? Boolean(*v) : "null"; }
struct Json {
  std::ostringstream o; bool first = true;
  void Add(const char *key, const std::string &v) {
    if (!first) o << ','; first = false; o << Quote(key) << ':' << v;
  }
  std::string Finish() { return "{" + o.str() + "}"; }
};
std::string ResolutionJson(const PersonFollowing2922680Resolution &r) {
  Json j; j.Add("ready", Boolean(r.ready)); j.Add("reason", Reason(r.reason));
  j.Add("selection", Quote(r.selection));
  j.Add("requested_full_id_u32", Number(r.requested_full_id_u32));
  j.Add("registry_identity", Pointer(r.registry_identity));
  j.Add("registry_count_u32", Number(r.registry_count_u32));
  j.Add("registry_slots_identity", Pointer(r.registry_slots_identity));
  j.Add("candidate_identity", Pointer(r.candidate_identity));
  j.Add("candidate_full_id_u32", Number(r.candidate_full_id_u32));
  j.Add("selected_identity", Pointer(r.selected_identity)); return j.Finish();
}
std::string PcJson(const PersonFollowing2922680Pc &p) {
  Json j; j.Add("ready", Boolean(p.ready)); j.Add("reason", Reason(p.reason));
  j.Add("admitted", Boolean(p.admitted)); j.Add("identity", Pointer(p.identity));
  j.Add("count_i32", Number(p.count_i32)); j.Add("weight_q100000", std::to_string(p.weight_q100000));
  std::string properties = "null";
  if (p.properties) {
    Json fields;
    std::string keys = "null", values = "null";
    if (p.properties->keys_u16) {
      keys = "["; bool first = true;
      for (auto k : *p.properties->keys_u16) { if (!first) keys += ','; first = false; keys += std::to_string(k); }
      keys += ']';
    }
    if (p.properties->values_q64) {
      values = "["; bool first = true;
      for (auto v : *p.properties->values_q64) { if (!first) values += ','; first = false; values += Quote(std::to_string(v)); }
      values += ']';
    }
    fields.Add("keys_u16", keys); fields.Add("values_q64", values); properties = fields.Finish();
  }
  j.Add("properties", properties); return j.Finish();
}
std::string FamilyJson(const PersonLocalTitlesPcFamily12004 &f) {
  Json j; j.Add("ready", Boolean(f.ready)); j.Add("reason", Reason(f.reason));
  j.Add("array_identity", Pointer(f.array_identity)); j.Add("count_i32", Number(f.count_i32));
  j.Add("known_empty", Boolean(f.known_empty));
  std::string rows = "["; bool first = true;
  for (const auto &pc : f.source_pcs) { if (!first) rows += ','; first = false; rows += PcJson(pc); }
  rows += ']'; j.Add("source_pcs", rows); return j.Finish();
}
std::string RowJson(const PersonLocalTitlesRow12004 &r) {
  Json j; j.Add("native_index", std::to_string(r.native_index));
  j.Add("input_ready", Boolean(r.input_ready)); j.Add("ready", Boolean(r.ready)); j.Add("reason", Reason(r.reason));
  j.Add("requested_title_full_id_u32", Number(r.requested_title_full_id_u32));
  j.Add("resolution", ResolutionJson(r.resolution));
  j.Add("selected_title_full_id_u32", Number(r.selected_title_full_id_u32));
  j.Add("exclusion_byte_130_u8", Number(r.exclusion_byte_130_u8));
  j.Add("exclusion_dword_12c_i32", Number(r.exclusion_dword_12c_i32));
  j.Add("native_contribution_eligible", Boolean(r.native_contribution_eligible)); j.Add("exclusion", Quote(r.exclusion));
  j.Add("template_identity", Pointer(r.template_identity)); j.Add("template_tier_i32", Number(r.template_tier_i32));
  j.Add("composer", FamilyJson(r.composer)); j.Add("primary", FamilyJson(r.primary));
  j.Add("supplemental_array_identity", Pointer(r.supplemental_array_identity));
  j.Add("supplemental_count_i32", Number(r.supplemental_count_i32));
  j.Add("supplemental_ready", Boolean(r.supplemental_ready)); j.Add("supplemental_reason", Reason(r.supplemental_reason));
  return j.Finish();
}
} // namespace

PersonLocalTitles12004DTO ReadPersonLocalTitlesForCharacter12004(
    const PersonCarrierDirect12004Bindings &b, std::uintptr_t character) {
  PersonLocalTitles12004DTO d; d.build_version = kGameVersion; d.executable_sha256 = kExecutableSha256;
  d.character_identity = character;
  if (!b.enabled || !b.read_memory || !b.module_base || !character ||
      b.current_context_getter_identity != b.module_base + kPersonCarrierContextGetterRva12004) {
    d.reason = "binding_or_character_unavailable"; return d;
  }
  d.character_id = Copy<std::uint32_t>(b, character + 0x18);
  const auto carrier = Copy<std::uintptr_t>(b, character + 0x1B0);
  if (!carrier || !*carrier) { d.reason = "character_carrier_unavailable"; return d; }
  const auto model = Copy<std::uintptr_t>(b, *carrier + 0x258);
  if (!model || !*model) { d.reason = "character_model_unavailable"; return d; }
  const auto owner = Copy<std::uintptr_t>(b, *model + 8);
  if (!owner || *owner != character) { d.reason = "model_character_mismatch"; return d; }
  d.selected_model_identity = *model;
  d.destination_pc_identity = Copy<std::uintptr_t>(b, *model + 0x10);
  d.character_context_1c0_identity = Copy<std::uintptr_t>(b, character + 0x1C0);
  if (!d.character_context_1c0_identity) { d.reason = "character_context_1c0_unread"; return d; }
  d.header_selection = *d.character_context_1c0_identity ? "context_1c0_1e0" : "existing_default_5459c88";
  d.header_identity = *d.character_context_1c0_identity ? *d.character_context_1c0_identity + 0x1E0
      : b.module_base + kDefaultHeader;
  d.array_identity = Copy<std::uintptr_t>(b, *d.header_identity);
  d.count_i32 = Copy<std::int32_t>(b, *d.header_identity + 0xC);
  if (!d.array_identity) { d.reason = "local_title_array_unread"; return d; }
  if (!d.count_i32) { d.reason = "local_title_count_unread"; return d; }
  if (*d.count_i32 < 0) { d.reason = "local_title_count_negative"; return d; }
  if (*d.count_i32 == 0) {
    d.ready = d.family_input_ready = d.composer_ready = d.primary_ready = d.supplemental_ready = true;
    d.family_known_zero = true; return d;
  }
  if (!*d.array_identity) { d.reason = "local_title_array_unread"; return d; }
  d.family_input_ready = d.composer_ready = d.primary_ready = d.supplemental_ready = true;
  bool all_known_zero = true, known_nonzero = false;
  for (std::uint32_t i = 0; i < static_cast<std::uint32_t>(*d.count_i32); ++i) {
    PersonLocalTitlesRow12004 row; row.native_index = i;
    ReadRow(b, *d.array_identity + static_cast<std::uintptr_t>(i) * 4, row);
    d.family_input_ready = d.family_input_ready && row.input_ready;
    d.composer_ready = d.composer_ready && row.native_contribution_eligible.has_value() && row.composer.ready;
    d.primary_ready = d.primary_ready && row.primary.ready;
    d.supplemental_ready = d.supplemental_ready && row.supplemental_ready;
    const bool row_zero = row.native_contribution_eligible == false ||
        (row.composer.known_empty == true && row.primary.known_empty == true && row.supplemental_ready);
    all_known_zero = all_known_zero && row_zero;
    known_nonzero = known_nonzero || row.composer.known_empty == false || row.primary.known_empty == false;
    d.rows.push_back(std::move(row));
  }
  if (all_known_zero) d.family_known_zero = true;
  else if (known_nonzero) d.family_known_zero = false;
  d.ready = d.family_input_ready && d.composer_ready && d.primary_ready && d.supplemental_ready;
  if (!d.ready) d.reason = !d.family_input_ready ? "local_title_inputs_partial"
      : !d.composer_ready ? "composer_inputs_partial"
      : !d.primary_ready ? "primary_inputs_partial" : "supplemental_inputs_partial";
  return d;
}

std::string SerializePersonLocalTitles12004(const PersonLocalTitles12004DTO &d) {
  Json j; j.Add("schema", Quote(kPersonLocalTitles12004Schema));
  j.Add("build_version", Quote(d.build_version)); j.Add("executable_sha256", Quote(d.executable_sha256));
  j.Add("ready", Boolean(d.ready)); j.Add("reason", Reason(d.reason));
  j.Add("family_input_ready", Boolean(d.family_input_ready)); j.Add("composer_ready", Boolean(d.composer_ready));
  j.Add("primary_ready", Boolean(d.primary_ready)); j.Add("supplemental_ready", Boolean(d.supplemental_ready));
  j.Add("family_known_zero", Boolean(d.family_known_zero)); j.Add("character_id", Number(d.character_id));
  j.Add("character_identity", Pointer(d.character_identity)); j.Add("selected_model_identity", Pointer(d.selected_model_identity));
  j.Add("destination_pc_identity", Pointer(d.destination_pc_identity));
  j.Add("character_context_1c0_identity", Pointer(d.character_context_1c0_identity));
  j.Add("header_selection", Quote(d.header_selection)); j.Add("header_identity", Pointer(d.header_identity));
  j.Add("array_identity", Pointer(d.array_identity)); j.Add("count_i32", Number(d.count_i32));
  std::string rows = "["; bool first = true;
  for (const auto &row : d.rows) { if (!first) rows += ','; first = false; rows += RowJson(row); }
  rows += ']'; j.Add("rows", rows);
  j.Add("full_helper_ready", Boolean(d.full_helper_ready)); j.Add("full_helper_reason", Quote(d.full_helper_reason));
  return j.Finish();
}
} // namespace xar::ck3_12004
