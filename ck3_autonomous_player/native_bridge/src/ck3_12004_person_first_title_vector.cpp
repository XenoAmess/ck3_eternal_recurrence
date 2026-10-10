#include "xar_bridge/ck3_12004_person_first_title_vector.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <sstream>
#include <utility>

namespace xar::ck3_12004 {
namespace {
// Source tree: external person-merged-helper-first-vector/native-tree.
// Actual2B986B0, held28BFC50 and880340 held62B+actual165B append closure.
// No native call, allocation or Model write.
constexpr std::uintptr_t kTitleRegistry = 0x5D1DAF8;
constexpr std::uintptr_t kTitleFallback = 0x5D1DAE0;
constexpr std::uintptr_t kSecondRegistry = 0x5D1DF10;
constexpr std::uintptr_t kSecondFallback = 0x5D1DF00;
constexpr std::uintptr_t kCharacterRegistry = 0x5C67568;
constexpr std::uintptr_t kCharacterFallback = 0x5C67570;
constexpr std::uintptr_t kDefaultHeader = 0x5459C88;

template <class T>
std::optional<T> Copy(const PersonCarrierDirect12004Bindings &b, std::uintptr_t p) {
  T value{};
  if (!b.read_memory || !b.read_memory(b.read_context,
      reinterpret_cast<const void *>(p), &value, sizeof(value))) return std::nullopt;
  return value;
}

PersonFollowing2922680Resolution Resolve(
    const PersonCarrierDirect12004Bindings &b,
    std::optional<std::uintptr_t> registry, std::uintptr_t fallback_rva,
    std::optional<std::uint32_t> full, std::uintptr_t id_offset,
    std::optional<std::uintptr_t> held_fallback = std::nullopt) {
  PersonFollowing2922680Resolution r;
  r.registry_identity = registry;
  r.requested_full_id_u32 = full;
  if (!registry) { r.reason = "registry_slot_unread"; return r; }
  bool fallback = *registry == 0;
  if (!fallback) {
    if (!full) { r.reason = "requested_full_id_unread"; return r; }
    r.registry_count_u32 = Copy<std::uint32_t>(b, *registry + 0x2C);
    if (!r.registry_count_u32) { r.reason = "registry_count_unread"; return r; }
    const auto index = *full & 0xFFFFFFU;
    fallback = index >= *r.registry_count_u32;
    if (!fallback) {
      r.registry_slots_identity = Copy<std::uintptr_t>(b, *registry + 0x20);
      if (!r.registry_slots_identity || !*r.registry_slots_identity) {
        r.reason = "registry_slots_unread"; return r;
      }
      r.candidate_identity = Copy<std::uintptr_t>(b,
          *r.registry_slots_identity + static_cast<std::uintptr_t>(index) * 16 + 8);
      if (!r.candidate_identity) { r.reason = "registry_candidate_unread"; return r; }
      fallback = *r.candidate_identity == 0;
      if (!fallback) {
        r.candidate_full_id_u32 = Copy<std::uint32_t>(b, *r.candidate_identity + id_offset);
        if (!r.candidate_full_id_u32) { r.reason = "candidate_full_id_unread"; return r; }
        fallback = *r.candidate_full_id_u32 != *full;
      }
    }
  }
  r.selection = fallback ? "fallback" : "mapped";
  r.selected_identity = fallback ? (held_fallback ? held_fallback
      : Copy<std::uintptr_t>(b, b.module_base + fallback_rva)) : r.candidate_identity;
  if (!r.selected_identity) { r.reason = "fallback_slot_unread"; return r; }
  // A copied null is retained. A later demanded dereference determines its use.
  r.ready = true;
  return r;
}

void ReadReceiver(const PersonCarrierDirect12004Bindings &b, std::uintptr_t subject,
                  PersonFirstTitleVectorReceiver12004 &r) {
  // Held actual28BFC50 loads BOTH fields before its context branch.
  r.input_context_1c0_identity = Copy<std::uintptr_t>(b, subject + 0x1C0);
  r.input_link_1b8_identity = Copy<std::uintptr_t>(b, subject + 0x1B8);
  if (!r.input_context_1c0_identity) { r.reason = "receiver_input_context_unread"; return; }
  if (!r.input_link_1b8_identity) { r.reason = "receiver_input_link_unread"; return; }
  if (*r.input_context_1c0_identity) {
    r.context_link_1c0_identity = Copy<std::uintptr_t>(b, *r.input_context_1c0_identity + 0x1C0);
    if (!r.context_link_1c0_identity || !*r.context_link_1c0_identity) {
      r.reason = "receiver_context_link_unread"; return;
    }
    r.context_candidate_28_identity = Copy<std::uintptr_t>(b, *r.context_link_1c0_identity + 0x28);
    if (!r.context_candidate_28_identity || !*r.context_candidate_28_identity) {
      r.reason = "receiver_context_candidate_unread"; return;
    }
    r.candidate_magic_1c_u32 = Copy<std::uint32_t>(b, *r.context_candidate_28_identity + 0x1C);
    if (!r.candidate_magic_1c_u32) { r.reason = "receiver_candidate_magic_unread"; return; }
    bool use_candidate = *r.candidate_magic_1c_u32 == 0x43686172U;
    if (use_candidate) {
      r.candidate_full_id_18_u32 = Copy<std::uint32_t>(b, *r.context_candidate_28_identity + 0x18);
      if (!r.candidate_full_id_18_u32) { r.reason = "receiver_candidate_id_unread"; return; }
      use_candidate = *r.candidate_full_id_18_u32 != 0xFFFFFFFFU;
    }
    r.selection = use_candidate ? "context_candidate" : "original_character";
    r.selected_identity = use_candidate ? r.context_candidate_28_identity : subject;
    r.ready = true;
    return;
  }
  if (!*r.input_link_1b8_identity) {
    // Actual28BFC84 skips the database load, not merely the requested ID.
    r.selected_identity = Copy<std::uintptr_t>(b, b.module_base + kCharacterFallback);
    if (!r.selected_identity) { r.reason = "receiver_fallback_unread"; return; }
    r.selection = "database_fallback"; r.ready = true;
    return;
  }
  const auto registry = Copy<std::uintptr_t>(b, b.module_base + kCharacterRegistry);
  r.resolution.registry_identity = registry;
  if (!registry) { r.reason = "receiver_registry_unread"; return; }
  if (*registry) {
    r.requested_full_id_u32 = Copy<std::uint32_t>(b, *r.input_link_1b8_identity + 0xC8);
    if (!r.requested_full_id_u32) { r.reason = "receiver_requested_id_unread"; return; }
  }
  r.resolution = Resolve(b, registry, kCharacterFallback, r.requested_full_id_u32, 0x18);
  if (!r.resolution.ready) { r.reason = r.resolution.reason; return; }
  r.selected_identity = r.resolution.selected_identity;
  r.selection = r.resolution.selection == "mapped" ? "database_mapped" : "database_fallback";
  r.ready = true;
}

void ReadElement(const PersonCarrierDirect12004Bindings &b, std::uintptr_t subject,
                 std::uintptr_t title, PersonFirstTitleVectorElement12004 &e) {
  e.identity = title;
  if (!title) { e.reason = "element_pointer_null"; return; }
  // Direct consumer has NO local-Title ID lookup or130/12C gate.
  e.template_identity = Copy<std::uintptr_t>(b, title + 0x48);
  if (e.template_identity && *e.template_identity)
    e.template_tier_i32 = Copy<std::int32_t>(b, *e.template_identity + 0x64);
  e.input_ready = e.template_tier_i32.has_value();
  ReadPersonTitleComposerInputs12004(b, title, e.composer);
  if (!e.input_ready) {
    e.reason = "element_template_tier_unread";
    e.primary.reason = e.supplemental.reason = e.reason;
    return;
  }
  const auto tier = *e.template_tier_i32;
  ReadPersonTitlePrimaryInputs12004(b, title, tier, e.primary);
  if (tier == 2) ReadPersonTitleSupplementalInputs12004(b, subject, title, e.supplemental);
  else { e.supplemental.ready = true; e.supplemental.known_empty = true; }
  e.ready = e.primary.ready && e.composer.ready && e.supplemental.ready;
  if (!e.ready) e.reason = !e.primary.ready ? "primary_inputs_partial"
      : !e.composer.ready ? "composer_inputs_partial" : "supplemental_inputs_partial";
}

bool ReadTitleRoots(const PersonCarrierDirect12004Bindings &b,
                    PersonFirstTitleVectorPhase12004 &p) {
  // Actual producer loads registry AND fallback before its row resolution.
  p.title_registry_identity = Copy<std::uintptr_t>(b, b.module_base + kTitleRegistry);
  p.title_fallback_identity = Copy<std::uintptr_t>(b, b.module_base + kTitleFallback);
  if (!p.title_registry_identity) { p.reason = "title_registry_slot_unread"; return false; }
  if (!p.title_fallback_identity) { p.reason = "title_fallback_slot_unread"; return false; }
  return true;
}

void ReadCandidates(const PersonCarrierDirect12004Bindings &b, std::uintptr_t subject,
                    bool filter, PersonFirstTitleVectorPhase12004 &p) {
  if (!p.array_identity) { p.reason = "phase_array_unread"; return; }
  if (!p.count_i32) { p.reason = "phase_count_unread"; return; }
  if (*p.count_i32 < 0) { p.reason = "phase_count_negative"; return; }
  if (*p.count_i32 == 0) { p.ready = true; return; }
  if (!p.title_registry_identity && !ReadTitleRoots(b, p)) return;
  bool complete = true;
  for (std::uint32_t i = 0; i < static_cast<std::uint32_t>(*p.count_i32); ++i) {
    PersonFirstTitleVectorCandidate12004 row; row.native_index = i;
    row.id_demanded = *p.title_registry_identity != 0;
    if (*row.id_demanded) {
      row.requested_full_id_u32 = Copy<std::uint32_t>(b,
          *p.array_identity + static_cast<std::uintptr_t>(i) * 4);
      if (!row.requested_full_id_u32) row.reason = "candidate_id_unread";
    }
    if (row.reason.empty()) {
      row.resolution = Resolve(b, p.title_registry_identity, kTitleFallback,
          row.requested_full_id_u32, 0x10, p.title_fallback_identity);
      if (!row.resolution.ready) row.reason = row.resolution.reason;
      else {
        bool emit = true;
        if (filter) {
          row.filter_byte_130_u8 = Copy<std::uint8_t>(b, *row.resolution.selected_identity + 0x130);
          if (!row.filter_byte_130_u8) row.reason = "filter_byte_130_unread";
          else emit = *row.filter_byte_130_u8 != 0;
        }
        if (row.reason.empty()) {
          row.emitted = emit; row.ready = true;
          if (emit) {
            row.element.emplace();
            ReadElement(b, subject, *row.resolution.selected_identity, *row.element);
          }
        }
      }
    }
    complete = complete && row.ready;
    p.rows.push_back(std::move(row));
  }
  p.ready = complete;
  if (!complete) p.reason = "phase_candidates_partial";
}

void ReadPhaseA(const PersonCarrierDirect12004Bindings &b,
                 PersonFirstTitleVector12004DTO &d) {
  auto &p = d.phase_a;
  if (!d.receiver.ready) { p.reason = "receiver_unavailable"; return; }
  d.receiver_context_1c0_identity = Copy<std::uintptr_t>(b, *d.receiver.selected_identity + 0x1C0);
  if (!d.receiver_context_1c0_identity) { p.reason = "receiver_context_1c0_unread"; return; }
  d.receiver_context_1b8_full_id_u32 = *d.receiver_context_1c0_identity
      ? Copy<std::uint32_t>(b, *d.receiver_context_1c0_identity + 0x1B8)
      : std::optional<std::uint32_t>{0xFFFFFFFFU};
  if (!d.receiver_context_1b8_full_id_u32) { p.reason = "receiver_context_owner_unread"; return; }
  if (!d.character_id) { p.reason = "subject_full_id_unread"; return; }
  p.admitted = *d.receiver_context_1b8_full_id_u32 == *d.character_id;
  if (!*p.admitted) { p.ready = true; return; }
  p.header_identity = *d.receiver_context_1c0_identity
      ? *d.receiver_context_1c0_identity + 0x1E0 : b.module_base + kDefaultHeader;
  p.array_identity = Copy<std::uintptr_t>(b, *p.header_identity);
  p.count_i32 = Copy<std::int32_t>(b, *p.header_identity + 0xC);
  ReadCandidates(b, *d.character_identity, true, p);
}

void ReadPhaseB(const PersonCarrierDirect12004Bindings &b,
                 PersonFirstTitleVector12004DTO &d) {
  auto &p = d.phase_b;
  auto &s = d.phase_b_inputs;
  const auto subject = *d.character_identity;
  if (!ReadTitleRoots(b, p)) { s.reason = p.reason; return; }
  s.subject_context_1c0_identity = Copy<std::uintptr_t>(b, subject + 0x1C0);
  if (!s.subject_context_1c0_identity) { s.reason = p.reason = "subject_context_1c0_unread"; return; }
  s.initial_title_full_id_u32 = 0xFFFFFFFFU;
  std::optional<std::uintptr_t> first_array;
  if (*s.subject_context_1c0_identity) {
    s.context_count_1ec_i32 = Copy<std::int32_t>(b, *s.subject_context_1c0_identity + 0x1EC);
    if (!s.context_count_1ec_i32) { s.reason = p.reason = "context_first_count_unread"; return; }
    s.selection = *s.context_count_1ec_i32 != 0 ? "context_first" : "context_empty";
    if (*s.context_count_1ec_i32 != 0) {
      s.context_array_1e0_identity = Copy<std::uintptr_t>(b, *s.subject_context_1c0_identity + 0x1E0);
      first_array = s.context_array_1e0_identity;
    }
  } else {
    s.alternate_root_1d0_identity = Copy<std::uintptr_t>(b, subject + 0x1D0);
    if (!s.alternate_root_1d0_identity) { s.reason = p.reason = "alternate_root_unread"; return; }
    s.selection = "alternate_absent";
    if (*s.alternate_root_1d0_identity) {
      s.alternate_count_74_i32 = Copy<std::int32_t>(b, *s.alternate_root_1d0_identity + 0x74);
      if (!s.alternate_count_74_i32) { s.reason = p.reason = "alternate_first_count_unread"; return; }
      s.selection = *s.alternate_count_74_i32 != 0 ? "alternate_first" : "alternate_empty";
      if (*s.alternate_count_74_i32 != 0) {
        s.alternate_array_68_identity = Copy<std::uintptr_t>(b, *s.alternate_root_1d0_identity + 0x68);
        first_array = s.alternate_array_68_identity;
      }
    }
  }
  if (s.selection == "context_first" || s.selection == "alternate_first") {
    if (!first_array || !*first_array) { s.reason = p.reason = "initial_title_array_unread"; return; }
    s.initial_title_full_id_u32 = Copy<std::uint32_t>(b, *first_array);
    if (!s.initial_title_full_id_u32) { s.reason = p.reason = "initial_title_id_unread"; return; }
  }
  s.initial_title_resolution = Resolve(b, p.title_registry_identity, kTitleFallback,
      s.initial_title_full_id_u32, 0x10, p.title_fallback_identity);
  if (!s.initial_title_resolution.ready) { s.reason = p.reason = s.initial_title_resolution.reason; return; }
  const auto second_registry = Copy<std::uintptr_t>(b, b.module_base + kSecondRegistry);
  s.second_resolution.registry_identity = second_registry;
  if (!second_registry) { s.reason = p.reason = "second_registry_slot_unread"; return; }
  if (*second_registry) {
    s.second_requested_full_id_330_u32 = Copy<std::uint32_t>(b,
        *s.initial_title_resolution.selected_identity + 0x330);
    if (!s.second_requested_full_id_330_u32) { s.reason = p.reason = "second_requested_id_unread"; return; }
  }
  s.second_resolution = Resolve(b, second_registry, kSecondFallback,
      s.second_requested_full_id_330_u32, 0x10);
  if (!s.second_resolution.ready) { s.reason = p.reason = s.second_resolution.reason; return; }
  p.admitted = true;
  p.header_identity = *s.second_resolution.selected_identity + 0x50;
  p.array_identity = Copy<std::uintptr_t>(b, *p.header_identity);
  p.count_i32 = Copy<std::int32_t>(b, *p.header_identity + 0xC);
  s.ready = true;
  ReadCandidates(b, subject, false, p);
}

// Wire formatting is intentionally shared with the already qualified PC family.
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
  std::ostringstream o; o << "0x" << std::hex << *v; return Quote(o.str());
}
std::string Reason(const std::string &v) { return v.empty() ? "null" : Quote(v); }
std::string Boolean(bool v) { return v ? "true" : "false"; }
std::string Boolean(const std::optional<bool> &v) { return v ? Boolean(*v) : "null"; }
struct Json {
  std::ostringstream o; bool first = true;
  void Add(const char *k, const std::string &v) {
    if (!first) o << ','; first = false; o << Quote(k) << ':' << v;
  }
  std::string Finish() { return "{" + o.str() + "}"; }
};

std::string ReceiverJson(const PersonFirstTitleVectorReceiver12004 &r) {
  Json j; j.Add("ready", Boolean(r.ready)); j.Add("reason", Reason(r.reason));
  j.Add("selection", Quote(r.selection));
  j.Add("input_context_1c0_identity", Pointer(r.input_context_1c0_identity));
  j.Add("input_link_1b8_identity", Pointer(r.input_link_1b8_identity));
  j.Add("context_link_1c0_identity", Pointer(r.context_link_1c0_identity));
  j.Add("context_candidate_28_identity", Pointer(r.context_candidate_28_identity));
  j.Add("candidate_magic_1c_u32", Number(r.candidate_magic_1c_u32));
  j.Add("candidate_full_id_18_u32", Number(r.candidate_full_id_18_u32));
  j.Add("requested_full_id_u32", Number(r.requested_full_id_u32));
  j.Add("resolution", SerializePersonTitleResolution12004(r.resolution));
  j.Add("selected_identity", Pointer(r.selected_identity)); return j.Finish();
}
std::string ElementJson(const PersonFirstTitleVectorElement12004 &e) {
  Json j; j.Add("input_ready", Boolean(e.input_ready)); j.Add("ready", Boolean(e.ready));
  j.Add("reason", Reason(e.reason)); j.Add("identity", Pointer(e.identity));
  j.Add("template_identity", Pointer(e.template_identity)); j.Add("template_tier_i32", Number(e.template_tier_i32));
  j.Add("primary", SerializePersonTitlePcFamily12004(e.primary));
  j.Add("composer", SerializePersonTitlePcFamily12004(e.composer));
  j.Add("supplemental", SerializePersonTitleSupplementalFamily12004(e.supplemental));
  return j.Finish();
}
std::string PhaseJson(const PersonFirstTitleVectorPhase12004 &p) {
  Json j; j.Add("ready", Boolean(p.ready)); j.Add("reason", Reason(p.reason));
  j.Add("admitted", Boolean(p.admitted)); j.Add("header_identity", Pointer(p.header_identity));
  j.Add("array_identity", Pointer(p.array_identity)); j.Add("count_i32", Number(p.count_i32));
  j.Add("title_registry_identity", Pointer(p.title_registry_identity));
  j.Add("title_fallback_identity", Pointer(p.title_fallback_identity));
  std::string rows = "["; bool first = true;
  for (const auto &r : p.rows) {
    if (!first) rows += ','; first = false;
    Json row; row.Add("native_index", std::to_string(r.native_index));
    row.Add("ready", Boolean(r.ready)); row.Add("reason", Reason(r.reason));
    row.Add("id_demanded", Boolean(r.id_demanded));
    row.Add("requested_full_id_u32", Number(r.requested_full_id_u32));
    row.Add("resolution", SerializePersonTitleResolution12004(r.resolution));
    row.Add("filter_byte_130_u8", Number(r.filter_byte_130_u8));
    row.Add("emitted", Boolean(r.emitted)); row.Add("element", r.element ? ElementJson(*r.element) : "null");
    rows += row.Finish();
  }
  rows += ']'; j.Add("rows", rows); return j.Finish();
}
std::string PhaseBInputsJson(const PersonFirstTitleVectorPhaseBInputs12004 &s) {
  Json j; j.Add("ready", Boolean(s.ready)); j.Add("reason", Reason(s.reason));
  j.Add("selection", Quote(s.selection));
  j.Add("subject_context_1c0_identity", Pointer(s.subject_context_1c0_identity));
  j.Add("context_count_1ec_i32", Number(s.context_count_1ec_i32));
  j.Add("context_array_1e0_identity", Pointer(s.context_array_1e0_identity));
  j.Add("alternate_root_1d0_identity", Pointer(s.alternate_root_1d0_identity));
  j.Add("alternate_count_74_i32", Number(s.alternate_count_74_i32));
  j.Add("alternate_array_68_identity", Pointer(s.alternate_array_68_identity));
  j.Add("initial_title_full_id_u32", Number(s.initial_title_full_id_u32));
  j.Add("initial_title_resolution", SerializePersonTitleResolution12004(s.initial_title_resolution));
  j.Add("second_requested_full_id_330_u32", Number(s.second_requested_full_id_330_u32));
  j.Add("second_resolution", SerializePersonTitleResolution12004(s.second_resolution));
  return j.Finish();
}
} // namespace

PersonFirstTitleVectorReceiver12004
ReadPersonFirstTitleVectorReceiverForCharacter12004(
    const PersonCarrierDirect12004Bindings &b, std::uintptr_t character) {
  PersonFirstTitleVectorReceiver12004 receiver;
  if (!b.enabled || !b.module_base || !b.read_memory || !character) {
    receiver.reason = "binding_or_character_unavailable";
    return receiver;
  }
  ReadReceiver(b, character, receiver);
  return receiver;
}

PersonFirstTitleVector12004DTO ReadPersonFirstTitleVectorForCharacter12004(
    const PersonCarrierDirect12004Bindings &b, std::uintptr_t character) {
  PersonFirstTitleVector12004DTO d;
  d.build_version = kGameVersion; d.executable_sha256 = kExecutableSha256;
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
  ReadReceiver(b, character, d.receiver);
  ReadPhaseA(b, d);
  ReadPhaseB(b, d);
  d.source_inputs_ready = d.phase_a.ready && d.phase_b_inputs.ready && d.phase_b.ready;
  // Both actual880340 paths append one QWORD at oldcount; no dedup/filter.
  d.producer_ready = d.source_inputs_ready;
  d.family_input_ready = d.primary_ready = d.composer_ready = d.supplemental_ready = d.producer_ready;
  bool all_zero = d.producer_ready, known_nonzero = false;
  const auto positive_source = [](const PersonLocalTitlesPcFamily12004 &f) {
    for (const auto &pc : f.source_pcs)
      if (pc.admitted && pc.count_i32 && *pc.count_i32 > 0) return true;
    return false;
  };
  std::vector<std::uintptr_t> emitted;
  for (const auto *phase : {&d.phase_a, &d.phase_b}) {
    for (const auto &r : phase->rows) {
      if (r.emitted != true || !r.element) continue;
      const auto &e = *r.element;
      emitted.push_back(*e.identity);
      d.family_input_ready = d.family_input_ready && e.input_ready;
      d.primary_ready = d.primary_ready && e.primary.ready;
      d.composer_ready = d.composer_ready && e.composer.ready;
      d.supplemental_ready = d.supplemental_ready && e.supplemental.ready;
      all_zero = all_zero && e.primary.known_empty == true &&
          e.composer.known_empty == true && e.supplemental.known_empty == true;
      known_nonzero = known_nonzero || e.primary.known_empty == false ||
          e.composer.known_empty == false || e.supplemental.known_empty == false ||
          positive_source(e.primary) || positive_source(e.composer);
    }
  }
  if (d.producer_ready) d.emitted_element_identities = std::move(emitted);
  if (known_nonzero) d.family_known_zero = false;
  else if (all_zero) d.family_known_zero = true;
  d.ready = d.producer_ready && d.family_input_ready && d.primary_ready &&
      d.composer_ready && d.supplemental_ready;
  if (!d.ready) d.reason = !d.source_inputs_ready ? "first_vector_source_inputs_partial"
      : !d.family_input_ready ? "first_vector_element_inputs_partial"
      : !d.primary_ready ? "primary_inputs_partial"
      : !d.composer_ready ? "composer_inputs_partial" : "supplemental_inputs_partial";
  return d;
}

std::string SerializePersonFirstTitleVector12004(const PersonFirstTitleVector12004DTO &d) {
  Json j; j.Add("schema", Quote(kPersonFirstTitleVector12004Schema));
  j.Add("build_version", Quote(d.build_version)); j.Add("executable_sha256", Quote(d.executable_sha256));
  j.Add("ready", Boolean(d.ready)); j.Add("reason", Reason(d.reason));
  j.Add("source_inputs_ready", Boolean(d.source_inputs_ready)); j.Add("producer_ready", Boolean(d.producer_ready));
  j.Add("family_input_ready", Boolean(d.family_input_ready)); j.Add("primary_ready", Boolean(d.primary_ready));
  j.Add("composer_ready", Boolean(d.composer_ready)); j.Add("supplemental_ready", Boolean(d.supplemental_ready));
  j.Add("family_known_zero", Boolean(d.family_known_zero)); j.Add("character_id", Number(d.character_id));
  j.Add("character_identity", Pointer(d.character_identity)); j.Add("selected_model_identity", Pointer(d.selected_model_identity));
  j.Add("destination_pc_identity", Pointer(d.destination_pc_identity));
  j.Add("receiver", ReceiverJson(d.receiver));
  j.Add("receiver_context_1c0_identity", Pointer(d.receiver_context_1c0_identity));
  j.Add("receiver_context_1b8_full_id_u32", Number(d.receiver_context_1b8_full_id_u32));
  j.Add("phase_a", PhaseJson(d.phase_a)); j.Add("phase_b_inputs", PhaseBInputsJson(d.phase_b_inputs));
  j.Add("phase_b", PhaseJson(d.phase_b));
  std::string emitted = "null";
  if (d.emitted_element_identities) {
    emitted = "["; bool first = true;
    for (auto p : *d.emitted_element_identities) { if (!first) emitted += ','; first = false; emitted += Pointer(p); }
    emitted += ']';
  }
  j.Add("emitted_element_identities", emitted); j.Add("full_helper_ready", Boolean(d.full_helper_ready));
  j.Add("full_helper_reason", Quote(d.full_helper_reason)); return j.Finish();
}
} // namespace xar::ck3_12004
