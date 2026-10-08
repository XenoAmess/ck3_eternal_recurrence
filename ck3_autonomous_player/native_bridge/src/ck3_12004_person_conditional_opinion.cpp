#include "xar_bridge/ck3_12004_person_conditional_opinion.hpp"

#include <cstring>
#include <sstream>
#include <utility>

namespace xar::ck3_12004 {
namespace {
template <typename T> std::optional<T> Copy(
    const PersonCarrierDirect12004Bindings &b, std::uintptr_t address) {
  T value{};
  if (!b.read_memory || !b.read_memory(b.read_context,
      reinterpret_cast<const void *>(address), &value, sizeof(value)))
    return std::nullopt;
  return value;
}
float Float(std::uint32_t bits) {
  float value{};
  static_assert(sizeof(value) == sizeof(bits));
  std::memcpy(&value, &bits, sizeof(value));
  return value;
}
bool ValidId(std::optional<std::uint32_t> id) {
  return id && *id != 0 && *id != 0xFFFFFFFFU;
}
PersonConditionalOpinion12004Row Opinion(
    const PersonConditionalOpinion12004Bindings &b,
    const PersonCarrierDirect12004Bindings &memory,
    const PersonConditional2921a90DTO &source,
    const PersonConditional2921a90Vote &selected) {
  PersonConditionalOpinion12004Row r;
  r.source_index = selected.native_index;
  r.selected_character_identity = selected.selected_character_identity;
  r.toward_full_character_id = source.character_id;
  r.toward_character_identity = source.character_identity;
  if (!r.selected_character_identity || *r.selected_character_identity == 0 ||
      !r.toward_character_identity || *r.toward_character_identity == 0 ||
      !ValidId(r.toward_full_character_id)) {
    r.reason = selected.reason.empty() ? "pair_opinion_source_identity_unavailable" : selected.reason;
    return r;
  }
  if (r.selected_character_identity == r.toward_character_identity) {
    r.selected_full_character_id = source.character_id;
    r.source_selection = "self_source_inputs";
    r.base_value = selected.base_opinion_i32;
    r.additional_value = selected.additional_opinion_i32;
    r.total_opinion_i32 = selected.clamped_i32;
    r.high_threshold_bits_u32 = selected.high_threshold_bits_u32;
    r.low_threshold_bits_u32 = selected.low_threshold_bits_u32;
    r.vote = selected.vote;
    r.ready = selected.ready;
    if (!r.ready) r.reason = selected.reason.empty()
        ? "pair_opinion_self_source_unavailable" : selected.reason;
    return r;
  }
  r.selected_full_character_id = Copy<std::uint32_t>(
      memory, *r.selected_character_identity + kCharacterFullIdOffset);
  if (!r.selected_full_character_id) { r.reason = "pair_opinion_full_id_unread"; return r; }
  if (!ValidId(r.selected_full_character_id)) { r.reason = "pair_opinion_full_id_invalid"; return r; }
  if (!b.enabled || !b.opinion.enabled || !b.opinion.core.enabled || !b.opinion.read_opinion) {
    r.reason = "pair_opinion_provider_unavailable"; return r;
  }
  const auto owner = ck3_12004::ResolveCoreCharacter(b.opinion.core,
      static_cast<std::int32_t>(*r.selected_full_character_id));
  const auto toward = ck3_12004::ResolveCoreCharacter(b.opinion.core,
      static_cast<std::int32_t>(*r.toward_full_character_id));
  if (reinterpret_cast<std::uintptr_t>(owner) != *r.selected_character_identity ||
      reinterpret_cast<std::uintptr_t>(toward) != *r.toward_character_identity) {
    r.reason = "pair_opinion_selected_identity_mismatch"; return r;
  }
  std::int32_t total{};
  if (!ck3_12004::ReadCharacterOpinion(b.opinion, *r.selected_full_character_id,
                            *r.toward_full_character_id, total)) {
    r.reason = "pair_opinion_pair_unavailable"; return r;
  }
  r.total_opinion_i32 = total;
  r.source_selection = "native_pair_postclamp_28bc470";
  r.high_threshold_bits_u32 = Copy<std::uint32_t>(memory, memory.module_base + 0x5C68EE0);
  if (!r.high_threshold_bits_u32) { r.reason = "classifier_high_threshold_unread"; return r; }
  const float value = static_cast<float>(total);
  if (value >= Float(*r.high_threshold_bits_u32)) r.vote = "high";
  else {
    r.low_threshold_bits_u32 = Copy<std::uint32_t>(memory, memory.module_base + 0x5C68EF4);
    if (!r.low_threshold_bits_u32) { r.reason = "classifier_low_threshold_unread"; return r; }
    r.vote = Float(*r.low_threshold_bits_u32) >= value ? "low" : "middle";
  }
  r.ready = true;
  return r;
}

class Json {
public:
  std::ostringstream out;
  bool first = true;
  Json() { out << '{'; }
  void Text(std::string_view value) {
    constexpr char hex[] = "0123456789abcdef";
    out << '"';
    for (const unsigned char c : value) {
      if (c == '"' || c == '\\') out << '\\' << static_cast<char>(c);
      else if (c < 0x20) out << "\\u00" << hex[c >> 4] << hex[c & 0xF];
      else out << static_cast<char>(c);
    }
    out << '"';
  }
  void Key(std::string_view name) {
    if (!first) out << ',';
    first = false; Text(name); out << ':';
  }
  void String(std::string_view name, std::string_view value, bool nullable = false) {
    Key(name); if (nullable && value.empty()) out << "null"; else Text(value);
  }
  void Bool(std::string_view name, bool value) { Key(name); out << (value ? "true" : "false"); }
  template <typename T> void Number(std::string_view name, std::optional<T> value) {
    Key(name); if (value) out << +*value; else out << "null";
  }
  void Pointer(std::string_view name, std::optional<std::uintptr_t> value) {
    Key(name); if (value) out << "\"0x" << std::hex << *value << std::dec << '"'; else out << "null";
  }
  std::string End() { out << '}'; return out.str(); }
};
} // namespace

PersonConditionalOpinion12004Bindings BindPersonConditionalOpinionImage12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept {
  PersonConditionalOpinion12004Bindings b;
  b.opinion = ck3_12004::BindGiftOpinionImage(module_base, executable_sha256);
  b.enabled = b.opinion.enabled && b.opinion.core.enabled;
  if (b.enabled) b.module_base = module_base;
  return b;
}

PersonConditionalOpinion12004DTO ReadPersonConditionalOpinionInputs12004(
    const PersonConditionalOpinion12004Bindings &b,
    const PersonCarrierDirect12004Bindings &memory,
    const PersonFollowing2921a90DTO &direct,
    const PersonConditional2921a90DTO &source) {
  PersonConditionalOpinion12004DTO d;
  d.build_version = kGameVersion; d.executable_sha256 = kExecutableSha256;
  d.character_id = source.character_id;
  d.source_inputs = source;
  if (!memory.enabled || !memory.read_memory) {
    d.reason = "exact_build_binding_unavailable"; return d;
  }
  if (source.character_id != direct.character_id ||
      source.character_identity != direct.character_identity ||
      source.conditional_definition_identity != direct.conditional_definition_identity) {
    d.reason = "pair_opinion_source_receiver_mismatch"; return d;
  }
  if (source.selected_family == "not_demanded" && source.ready) {
    d.ready = true; d.selected_family = "not_demanded"; d.occurrence_count = 0U; return d;
  }
  if (source.admitted != true || !source.character_identity ||
      !source.conditional_definition_identity || *source.conditional_definition_identity == 0) {
    d.reason = source.reason.empty() ? "conditional_admission_unread" : source.reason; return d;
  }
  if (source.classifier_rows.empty()) {
    d.classifier_ready = source.classifier_ready;
    d.classifier_reason = source.classifier_reason;
    d.classifier_result_i32 = source.classifier_result_i32;
  } else {
    d.classifier_ready = true;
    std::uint32_t high = 0, low = 0, middle = 0;
    for (const auto &row : source.classifier_rows) {
      auto opinion = Opinion(b, memory, source, row);
      if (!opinion.ready) {
        d.classifier_ready = false;
        if (d.classifier_reason.empty()) d.classifier_reason = opinion.reason;
      } else if (opinion.vote == "high") ++high;
      else if (opinion.vote == "low") ++low;
      else ++middle;
      d.opinion_rows.push_back(std::move(opinion));
    }
    if (d.classifier_ready)
      d.classifier_result_i32 = high > low && high > middle ? 0
          : low > high && low > middle ? 2 : 1;
  }
  if (!d.classifier_ready || !d.classifier_result_i32) {
    d.reason = d.classifier_reason.empty() ? "classifier_source_unavailable" : d.classifier_reason;
    return d;
  }
  if (*d.classifier_result_i32 == 1) {
    d.selected_family = "classifier_other_empty";
    d.ready = true; d.occurrence_count = 0U; return d;
  }
  const bool high = *d.classifier_result_i32 == 0;
  d.selected_family = high ? "bb0_bbc" : "b80_b8c";
  if (source.classifier_ready && source.classifier_result_i32 == d.classifier_result_i32) {
    d.selected_array_identity = source.selected_array_identity;
    d.selected_count_i32 = source.selected_count_i32;
    d.rows = source.rows; d.ready = source.ready;
    d.reason = source.reason; d.occurrence_count = source.occurrence_count;
    return d;
  }
  const auto definition = *source.conditional_definition_identity;
  d.selected_array_identity = Copy<std::uintptr_t>(memory, definition + (high ? 0xBB0 : 0xB80));
  d.selected_count_i32 = Copy<std::int32_t>(memory, definition + (high ? 0xBBC : 0xB8C));
  if (!d.selected_array_identity || !d.selected_count_i32) {
    d.reason = "conditional_selected_header_unread"; return d;
  }
  const auto count = *d.selected_count_i32;
  if (count < 0) { d.reason = "conditional_selected_count_negative"; return d; }
  if (count > 0 && *d.selected_array_identity == 0) {
    d.reason = "conditional_selected_array_unread"; return d;
  }
  d.ready = true;
  std::uint32_t occurrences = 0;
  for (std::uint32_t index = 0; index < static_cast<std::uint32_t>(count); ++index) {
    auto row = ReadPersonConditional2921a90RowInputs12004(memory, *d.selected_array_identity, index);
    if (!row.ready) {
      d.ready = false;
      if (d.reason.empty()) d.reason = row.reason;
    } else if (row.weight_q64 && *row.weight_q64 != 0) ++occurrences;
    d.rows.push_back(std::move(row));
  }
  if (d.ready) d.occurrence_count = occurrences;
  return d;
}

std::string SerializePersonConditionalOpinion12004(const PersonConditionalOpinion12004DTO &d) {
  Json j;
  j.String("schema", kPersonConditionalOpinion12004Schema);
  j.String("build_version", d.build_version); j.String("executable_sha256", d.executable_sha256);
  j.Number("character_id", d.character_id); j.Bool("ready", d.ready); j.String("reason", d.reason, true);
  j.Key("source_inputs"); j.out << SerializePersonConditional2921a90(d.source_inputs);
  j.Key("opinion_rows"); j.out << '['; bool first = true;
  for (const auto &r : d.opinion_rows) {
    if (!first) j.out << ',';
    first = false;
    Json q;
    q.Number("source_index", std::optional<std::uint32_t>{r.source_index});
    q.Bool("ready", r.ready); q.String("reason", r.reason, true);
    q.Number("selected_full_character_id", r.selected_full_character_id);
    q.Pointer("selected_character_identity", r.selected_character_identity);
    q.Number("toward_full_character_id", r.toward_full_character_id);
    q.Pointer("toward_character_identity", r.toward_character_identity);
    q.String("source_selection", r.source_selection);
    q.Number("base_value", r.base_value); q.Number("additional_value", r.additional_value);
    q.Number("total_opinion_i32", r.total_opinion_i32);
    q.Number("high_threshold_bits_u32", r.high_threshold_bits_u32);
    q.Number("low_threshold_bits_u32", r.low_threshold_bits_u32);
    q.String("vote", r.vote);
    j.out << q.End();
  }
  j.out << ']'; j.Bool("classifier_ready", d.classifier_ready);
  j.String("classifier_reason", d.classifier_reason, true);
  j.Number("classifier_result_i32", d.classifier_result_i32);
  j.String("selected_family", d.selected_family);
  j.Pointer("selected_array_identity", d.selected_array_identity);
  j.Number("selected_count_i32", d.selected_count_i32);
  j.Number("occurrence_count", d.occurrence_count);
  j.Key("rows"); j.out << '['; first = true;
  for (const auto &r : d.rows) {
    if (!first) j.out << ',';
    first = false;
    j.out << SerializePersonConditional2921a90RowInputs12004(r);
  }
  j.out << ']';
  return j.End();
}
} // namespace xar::ck3_12004
