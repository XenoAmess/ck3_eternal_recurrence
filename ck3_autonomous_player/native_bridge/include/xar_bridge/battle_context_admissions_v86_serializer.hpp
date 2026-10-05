#pragma once

#include "xar_bridge/battle_context_source_inputs_v1.hpp"
#include "xar_bridge/battle_context_locale_inputs_v1.hpp"

#include <cstddef>
#include <optional>
#include <string>
#include <string_view>

namespace xar::bridge {
namespace battle_context_admissions_v86_detail {
inline void Text(std::string &out, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  out += '"';
  for (unsigned char c : value) {
    if (c == '"' || c == '\\') { out += '\\'; out += static_cast<char>(c); }
    else if (c < 0x20U) { out += "\\u00"; out += hex[c >> 4U]; out += hex[c & 15U]; }
    else out += static_cast<char>(c);
  }
  out += '"';
}
inline void Reason(std::string &out, std::string_view value) {
  if (value.empty()) out += "null";
  else Text(out, value);
}
template <typename T> inline void Number(std::string &out, const std::optional<T> &v) {
  out += v ? std::to_string(*v) : "null";
}
inline void Boolean(std::string &out, const std::optional<bool> &v) {
  out += v ? (*v ? "true" : "false") : "null";
}
inline void Resolution(std::string &out, const std::optional<game::ContextSourceResolutionV1> &v) {
  if (!v) { out += "null"; return; }
  out += "{\"status\":"; Text(out, v->status);
  out += ",\"requested_full_id\":"; Number(out, v->requested_full_id);
  out += ",\"selected_full_id\":"; Number(out, v->selected_full_id);
  out += ",\"reason\":"; Reason(out, v->reason); out += '}';
}
inline void SignedSet(std::string &out, const std::optional<game::ContextSourceSignedKeySetV1> &v) {
  if (!v) { out += "null"; return; }
  out += "{\"native_index\":" + std::to_string(v->native_index) + ",\"count\":";
  Number(out, v->count); out += ",\"keys_i32\":";
  if (!v->keys_i32) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < v->keys_i32->size(); ++i) {
      if (i) out += ',';
      out += std::to_string((*v->keys_i32)[i]);
    }
    out += ']';
  }
  out += ",\"reason\":"; Reason(out, v->reason); out += '}';
}
}  // namespace battle_context_admissions_v86_detail

inline std::string SerializeContextSourceSelectorFieldsV86(const game::ContextSource291d7e0V1 &v) {
  using namespace battle_context_admissions_v86_detail;
  std::string out = ",\"selector_a_stage1\":"; Resolution(out, v.selector_a_stage1);
  out += ",\"selector_a_stage2\":"; Resolution(out, v.selector_a_stage2);
  out += ",\"selector_a_stage3\":"; Resolution(out, v.selector_a_stage3);
  out += ",\"selector_a_selected_source\":"; Text(out, v.selector_a_selected_source);
  out += ",\"selector_a_key_count\":"; Number(out, v.selector_a_key_count);
  out += ",\"selector_a_key_identities\":";
  if (!v.selector_a_key_identities) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < v.selector_a_key_identities->size(); ++i) {
      if (i) out += ',';
      Text(out, (*v.selector_a_key_identities)[i]);
    }
    out += ']';
  }
  out += ",\"selector_b_resolution\":"; Resolution(out, v.selector_b_resolution);
  out += ",\"selector_b_primary_keys\":"; SignedSet(out, v.selector_b_primary_keys);
  out += ",\"selector_b_nested_count\":"; Number(out, v.selector_b_nested_count);
  out += ",\"selector_b_nested_keys\":";
  if (!v.selector_b_nested_keys) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < v.selector_b_nested_keys->size(); ++i) {
      if (i) out += ',';
      SignedSet(out, std::optional<game::ContextSourceSignedKeySetV1>((*v.selector_b_nested_keys)[i]));
    }
    out += ']';
  }
  return out;
}

inline std::string SerializeContextSourceLocaleClassificationV86(
    const std::optional<game::ContextSourceLocaleClassificationV1> &v) {
  using namespace battle_context_admissions_v86_detail;
  if (!v) return "null";
  std::string out = "{\"status\":"; Text(out, v->status);
  out += ",\"ready\":"; out += v->ready ? "true" : "false";
  out += ",\"first_signed_byte\":"; Number(out, v->first_signed_byte);
  out += ",\"crt_index\":"; Number(out, v->crt_index);
  out += ",\"cached_value_api_status\":"; Text(out, v->cached_value_api_status);
  out += ",\"thread_state_source\":"; Text(out, v->thread_state_source);
  out += ",\"locale_source\":"; Text(out, v->locale_source);
  out += ",\"thread_state_present\":"; Boolean(out, v->thread_state_present);
  out += ",\"current_locale_present\":"; Boolean(out, v->current_locale_present);
  out += ",\"global_locale_present\":"; Boolean(out, v->global_locale_present);
  out += ",\"selected_locale_present\":"; Boolean(out, v->selected_locale_present);
  out += ",\"thread_locale_flags\":"; Number(out, v->thread_locale_flags);
  out += ",\"flags_mask\":"; Number(out, v->flags_mask);
  out += ",\"locale_max_multibyte\":"; Number(out, v->locale_max_multibyte);
  out += ",\"table_element_u16\":"; Number(out, v->table_element_u16);
  out += ",\"result_i32\":"; Number(out, v->result_i32);
  out += ",\"reason\":"; Reason(out, v->reason); out += '}';
  return out;
}
}  // namespace xar::bridge
