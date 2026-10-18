#include "xar_bridge/rite_creation_actions12004_wire.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <algorithm>
#include <array>
#include <charconv>
#include <limits>
#include <utility>
#include <vector>

namespace xar::ck3_12004::religion::rite_creation_actions {
namespace {
constexpr std::array<std::string_view, 8> operations{
    "open_create_draft", "open_edit_current_rite_draft", "select_core_tenet",
    "select_doctrine", "set_name_field", "preview", "prepare_confirmation",
    "confirm_once"};
constexpr std::array<std::string_view, 5> name_fields{
    "name", "adjective", "adherent", "adherent_plural", "description"};
constexpr std::array<std::string_view, 3> outcomes{
    "create_faith", "create_rite", "edit_rite"};
constexpr std::array<std::string_view, 19> all_keys{
    "type", "protocol_version", "request_id", "step", "expected_revision",
    "expected_connection_generation", "expected_date_raw",
    "expected_player_character_id", "operation", "expected_source_rite_id",
    "core_slot_index", "tenet_key", "group_key", "doctrine_key", "name_field",
    "text", "expected_preview_identity", "expected_outcome_kind", "action_id"};

bool Fail(std::string& reason, const char* value) {
  reason = value;
  return false;
}
bool White(char c) noexcept {
  return c == ' ' || c == '\t' || c == '\r' || c == '\n';
}
bool Scalar(std::string_view value, std::size_t& at, std::uint32_t& cp) noexcept {
  if (at == value.size()) return false;
  const auto first = static_cast<unsigned char>(value[at++]);
  unsigned more = 0;
  cp = first;
  if (first < 0x80) return true;
  if (first >= 0xC2 && first <= 0xDF) { more = 1; cp = first & 31U; }
  else if (first >= 0xE0 && first <= 0xEF) { more = 2; cp = first & 15U; }
  else if (first >= 0xF0 && first <= 0xF4) { more = 3; cp = first & 7U; }
  else return false;
  const auto count = more;
  if (more > value.size() - at) return false;
  while (more-- != 0) {
    const auto next = static_cast<unsigned char>(value[at++]);
    if ((next & 0xC0U) != 0x80U) return false;
    cp = (cp << 6U) | (next & 63U);
  }
  return !((count == 1 && cp < 0x80) || (count == 2 && cp < 0x800) ||
      (count == 3 && cp < 0x10000) || cp > 0x10FFFF ||
      (cp >= 0xD800 && cp <= 0xDFFF));
}
void AppendScalar(std::string& value, std::uint32_t cp) {
  if (cp < 0x80) value += static_cast<char>(cp);
  else if (cp < 0x800) {
    value += static_cast<char>(0xC0U | (cp >> 6U));
    value += static_cast<char>(0x80U | (cp & 63U));
  } else if (cp < 0x10000) {
    value += static_cast<char>(0xE0U | (cp >> 12U));
    value += static_cast<char>(0x80U | ((cp >> 6U) & 63U));
    value += static_cast<char>(0x80U | (cp & 63U));
  } else {
    value += static_cast<char>(0xF0U | (cp >> 18U));
    value += static_cast<char>(0x80U | ((cp >> 12U) & 63U));
    value += static_cast<char>(0x80U | ((cp >> 6U) & 63U));
    value += static_cast<char>(0x80U | (cp & 63U));
  }
}
struct Value {
  std::string key, text;
  bool is_string = false;
};
class Parser {
 public:
  explicit Parser(std::string_view input) : input_(input) {}
  bool Object(std::vector<Value>& values, std::string& reason) {
    if (!Take('{')) return Fail(reason, "rite_creation_request_object_required");
    Skip();
    if (Take('}')) return End(reason);
    for (;;) {
      if (values.size() >= all_keys.size())
        return Fail(reason, "rite_creation_request_too_many_fields");
      Value field{};
      if (!String(field.key, 128))
        return Fail(reason, "rite_creation_request_invalid_key");
      if (std::any_of(values.begin(), values.end(), [&](const Value& other) {
            return field.key == other.key;
          })) return Fail(reason, "rite_creation_request_duplicate_key");
      if (std::find(all_keys.begin(), all_keys.end(), field.key) == all_keys.end())
        return Fail(reason, "rite_creation_request_unknown_field");
      if (!Take(':')) return Fail(reason, "rite_creation_request_missing_colon");
      Skip();
      field.is_string = at_ < input_.size() && input_[at_] == '"';
      if (field.is_string ? !String(field.text, 4096) : !Integer(field.text))
        return Fail(reason, "rite_creation_request_invalid_flat_value");
      values.push_back(std::move(field));
      if (Take('}')) return End(reason);
      if (!Take(',')) return Fail(reason, "rite_creation_request_missing_comma");
    }
  }
 private:
  std::string_view input_;
  std::size_t at_ = 0;
  void Skip() noexcept {
    while (at_ < input_.size() && White(input_[at_])) ++at_;
  }
  bool Take(char c) noexcept {
    Skip();
    if (at_ == input_.size() || input_[at_] != c) return false;
    ++at_;
    return true;
  }
  bool End(std::string& reason) {
    Skip();
    return at_ == input_.size() || Fail(reason, "rite_creation_request_trailing_input");
  }
  bool Hex4(std::uint32_t& value) noexcept {
    if (input_.size() - at_ < 4) return false;
    value = 0;
    for (unsigned n = 0; n != 4; ++n) {
      const char c = input_[at_++];
      const unsigned digit = c >= '0' && c <= '9' ? static_cast<unsigned>(c - '0') :
          c >= 'a' && c <= 'f' ? static_cast<unsigned>(c - 'a') + 10U :
          c >= 'A' && c <= 'F' ? static_cast<unsigned>(c - 'A') + 10U : 16U;
      if (digit == 16) return false;
      value = (value << 4U) | digit;
    }
    return true;
  }
  bool String(std::string& output, std::size_t maximum) {
    if (!Take('"')) return false;
    output.clear();
    while (at_ < input_.size()) {
      const char c = input_[at_++];
      if (c == '"') return true;
      if (c == '\\') {
        if (at_ == input_.size()) return false;
        const char escaped = input_[at_++];
        switch (escaped) {
          case '"': output += '"'; break;
          case '\\': output += '\\'; break;
          case '/': output += '/'; break;
          case 'b': output += '\b'; break;
          case 'f': output += '\f'; break;
          case 'n': output += '\n'; break;
          case 'r': output += '\r'; break;
          case 't': output += '\t'; break;
          case 'u': {
            std::uint32_t cp = 0;
            if (!Hex4(cp)) return false;
            if (cp >= 0xD800 && cp <= 0xDBFF) {
              if (input_.size() - at_ < 2 || input_[at_] != '\\' ||
                  input_[at_ + 1] != 'u') return false;
              at_ += 2;
              std::uint32_t low = 0;
              if (!Hex4(low) || low < 0xDC00 || low > 0xDFFF) return false;
              cp = 0x10000U + ((cp - 0xD800U) << 10U) + low - 0xDC00U;
            } else if (cp >= 0xDC00 && cp <= 0xDFFF) return false;
            AppendScalar(output, cp);
            break;
          }
          default: return false;
        }
      } else {
        const auto byte = static_cast<unsigned char>(c);
        if (byte < 0x20) return false;
        if (byte < 0x80) output += c;
        else {
          const auto begin = at_ - 1;
          auto finish = begin;
          std::uint32_t cp = 0;
          if (!Scalar(input_, finish, cp)) return false;
          output.append(input_.substr(begin, finish - begin));
          at_ = finish;
        }
      }
      if (output.size() > maximum) return false;
    }
    return false;
  }
  bool Integer(std::string& output) {
    Skip();
    const auto begin = at_;
    if (at_ < input_.size() && input_[at_] == '-') ++at_;
    const auto digits = at_;
    while (at_ < input_.size() && input_[at_] >= '0' && input_[at_] <= '9') ++at_;
    if (at_ == digits || at_ - begin > 21 ||
        (at_ - digits > 1 && input_[digits] == '0') ||
        (at_ < input_.size() && input_[at_] != ',' && input_[at_] != '}' && !White(input_[at_])))
      return false;
    output.assign(input_.substr(begin, at_ - begin));
    return true;
  }
};
const Value* Get(const std::vector<Value>& values, std::string_view key) noexcept {
  const auto found = std::find_if(values.begin(), values.end(), [&](const Value& value) {
    return value.key == key;
  });
  return found == values.end() ? nullptr : &*found;
}
bool Text(const std::vector<Value>& values, std::string_view key, std::string& value) {
  const auto* found = Get(values, key);
  if (!found || !found->is_string) return false;
  value = found->text;
  return true;
}
template <typename T> bool Number(const std::vector<Value>& values,
    std::string_view key, T& value) noexcept {
  const auto* found = Get(values, key);
  if (!found || found->is_string) return false;
  const auto text = std::string_view(found->text);
  const auto parsed = std::from_chars(text.data(), text.data() + text.size(), value);
  return parsed.ec == std::errc{} && parsed.ptr == text.data() + text.size();
}
template <typename Enum, std::size_t N> bool Named(std::string_view text,
    const std::array<std::string_view, N>& names, Enum& value) noexcept {
  const auto found = std::find(names.begin(), names.end(), text);
  if (found == names.end()) return false;
  value = static_cast<Enum>(found - names.begin());
  return true;
}
template <typename Enum, std::size_t N> std::string_view Name(Enum value,
    const std::array<std::string_view, N>& names) noexcept {
  const auto index = static_cast<std::size_t>(value);
  return index < names.size() ? names[index] : std::string_view{};
}
bool ControlId(std::string_view value) noexcept {
  return !value.empty() && value.size() <= 128 &&
      std::all_of(value.begin(), value.end(), [](char c) {
        return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
            (c >= '0' && c <= '9') || c == '-' || c == '_' || c == '.' || c == ':';
      });
}
bool Hash(std::string_view value) noexcept {
  return value.size() == 64 && std::all_of(value.begin(), value.end(), [](char c) {
    return (c >= 'a' && c <= 'f') || (c >= '0' && c <= '9');
  });
}

class Json {
 public:
  std::string text;
  bool valid = true;
  void String(std::string_view value) {
    text += '"';
    constexpr char hex[] = "0123456789abcdef";
    for (std::size_t at = 0; at < value.size();) {
      const auto begin = at;
      std::uint32_t cp = 0;
      if (!Scalar(value, at, cp)) { valid = false; return; }
      switch (cp) {
        case '"': text += "\\\""; break;
        case '\\': text += "\\\\"; break;
        case '\b': text += "\\b"; break;
        case '\f': text += "\\f"; break;
        case '\n': text += "\\n"; break;
        case '\r': text += "\\r"; break;
        case '\t': text += "\\t"; break;
        default:
          if (cp < 0x20) {
            text += "\\u00";
            text += hex[(cp >> 4U) & 15U];
            text += hex[cp & 15U];
          } else text.append(value.substr(begin, at - begin));
      }
    }
    text += '"';
  }
  void Key(std::string_view key) { String(key); text += ':'; }
  void Boolean(bool value) { text += value ? "true" : "false"; }
  template <typename T> void Integer(T value) { text += std::to_string(value); }
  void Optional(const std::optional<std::string>& value) {
    if (value) String(*value); else text += "null";
  }
  void Optional(const std::optional<bool>& value) {
    if (value) Boolean(*value); else text += "null";
  }
  template <typename T> void Optional(const std::optional<T>& value) {
    if (value) Integer(*value); else text += "null";
  }
  template <typename Enum, std::size_t N> void OptionalName(
      const std::optional<Enum>& value, const std::array<std::string_view, N>& names) {
    if (!value) { text += "null"; return; }
    const auto name = Name(*value, names);
    if (name.empty()) { valid = false; return; }
    String(name);
  }
};
bool ResultContract(const Result& result, std::string& reason) {
  if (!result.frame.connection_generation || !result.frame.native_revision ||
      !result.frame.capture_epoch || result.frame.played_character_id <= 0)
    return Fail(reason, "rite_creation_result_actual_frame_unavailable");
  if (Name(result.operation, operations).empty() || result.status.empty() ||
      (!result.available && result.unavailable_reason.empty()) ||
      (result.available && !result.unavailable_reason.empty()) ||
      result.business_outcome_observed ||
      (result.dispatch_invoked && !result.native_dispatch_attempted) ||
      (result.original_writer_may_have_been_queued && result.operation != Operation::confirm_once))
    return Fail(reason, "rite_creation_result_flags_invalid");
  if (result.operation == Operation::confirm_once &&
      (!result.action_id || !ControlId(*result.action_id)))
    return Fail(reason, "rite_creation_confirmation_result_action_id_required");
  if (!result.full_can.observed && (result.full_can.can_create || result.full_can.can_edit ||
      result.full_can.create_reason || result.full_can.edit_reason))
    return Fail(reason, "rite_creation_unobserved_can_has_values");
  if (!result.quote.observed && (result.quote.piety_cost_raw ||
      result.quote.piety_missing_signed_raw || result.quote.has_enough_piety))
    return Fail(reason, "rite_creation_unobserved_quote_has_values");
  if (!result.draft.selected_core_tenets_observed && !result.draft.selected_core_tenets.empty())
    return Fail(reason, "rite_creation_unobserved_tenets_have_values");
  if (!result.draft.selected_doctrines_observed && !result.draft.selected_doctrines.empty())
    return Fail(reason, "rite_creation_unobserved_doctrines_have_values");
  if (result.preview_identity_available) {
    const auto& draft = result.draft;
    if (!result.preview_identity || !Hash(*result.preview_identity) ||
        !result.complete_command_payload_observed || !result.original_writer_inputs_observed ||
        !result.native_command_text_bytes || *result.native_command_text_bytes == 0 ||
        !result.native_command_text_sha256 || !Hash(*result.native_command_text_sha256) ||
        !draft.observed || !draft.names_observed || !draft.selected_core_tenets_observed ||
        !draft.selected_doctrines_observed || !draft.source_rite_id || *draft.source_rite_id == absent ||
        !draft.source_faith_id || *draft.source_faith_id == absent ||
        !draft.actor_faith_id || *draft.actor_faith_id == absent || !draft.actual_outcome_kind ||
        !std::all_of(draft.names.begin(), draft.names.end(), [](const auto& value) { return value.has_value(); }) ||
        !result.modal.observed || result.modal.stage == ModalStage::unknown ||
        !result.full_can.observed || !result.full_can.can_create || !result.full_can.can_edit ||
        !result.quote.observed || !result.quote.piety_cost_raw ||
        !result.quote.piety_missing_signed_raw || !result.quote.has_enough_piety)
      return Fail(reason, "rite_creation_preview_identity_incomplete");
  } else if (result.preview_identity) {
    return Fail(reason, "rite_creation_unavailable_preview_identity_has_value");
  }
  return true;
}
void FrameJson(Json& json, const Frame& value) {
  json.text += '{'; json.Key("connection_generation"); json.Integer(value.connection_generation);
  json.text += ','; json.Key("native_revision"); json.Integer(value.native_revision);
  json.text += ','; json.Key("capture_epoch"); json.Integer(value.capture_epoch);
  json.text += ','; json.Key("date_raw"); json.Integer(value.date_raw);
  json.text += ','; json.Key("played_character_id"); json.Integer(value.played_character_id);
  json.text += '}';
}
void DraftJson(Json& json, const Draft& value) {
  json.text += '{'; json.Key("observed"); json.Boolean(value.observed);
  json.text += ','; json.Key("names_observed"); json.Boolean(value.names_observed);
  json.text += ','; json.Key("selected_core_tenets_observed"); json.Boolean(value.selected_core_tenets_observed);
  json.text += ','; json.Key("selected_doctrines_observed"); json.Boolean(value.selected_doctrines_observed);
  json.text += ','; json.Key("source_rite_id"); json.Optional(value.source_rite_id);
  json.text += ','; json.Key("source_faith_id"); json.Optional(value.source_faith_id);
  json.text += ','; json.Key("actor_faith_id"); json.Optional(value.actor_faith_id);
  json.text += ','; json.Key("actual_outcome_kind"); json.OptionalName(value.actual_outcome_kind, outcomes);
  json.text += ','; json.Key("editing_owned_current_rite"); json.Optional(value.editing_owned_current_rite);
  json.text += ','; json.Key("native_create_faith_or_reform"); json.Optional(value.native_create_faith_or_reform);
  json.text += ','; json.Key("names"); json.text += '{';
  for (std::size_t n = 0; n != name_fields.size(); ++n) {
    if (n) json.text += ',';
    json.Key(name_fields[n]); json.Optional(value.names[n]);
  }
  json.text += '}';
  json.text += ','; json.Key("selected_core_tenets");
  if (!value.selected_core_tenets_observed) json.text += "null";
  else {
    json.text += '[';
    for (std::size_t n = 0; n != value.selected_core_tenets.size(); ++n) {
      if (n) json.text += ',';
      const auto& row = value.selected_core_tenets[n];
      json.text += '{'; json.Key("slot_index"); json.Integer(row.slot_index);
      json.text += ','; json.Key("tenet_key"); json.String(row.tenet_key); json.text += '}';
    }
    json.text += ']';
  }
  json.text += ','; json.Key("selected_doctrines");
  if (!value.selected_doctrines_observed) json.text += "null";
  else {
    json.text += '[';
    for (std::size_t n = 0; n != value.selected_doctrines.size(); ++n) {
      if (n) json.text += ',';
      const auto& row = value.selected_doctrines[n];
      json.text += '{'; json.Key("group_key"); json.String(row.group_key);
      json.text += ','; json.Key("doctrine_key"); json.String(row.doctrine_key); json.text += '}';
    }
    json.text += ']';
  }
  json.text += '}';
}
void ModalJson(Json& json, const Modal& value) {
  constexpr std::array<std::string_view, 3> stages{"unknown", "none", "confirmation"};
  constexpr std::array<std::string_view, 2> kinds{"create", "edit"};
  json.text += '{'; json.Key("observed"); json.Boolean(value.observed);
  json.text += ','; json.Key("stage");
  const auto stage_name = Name(value.stage, stages);
  if (stage_name.empty()) json.valid = false; else json.String(stage_name);
  json.text += ','; json.Key("kind"); json.OptionalName(value.kind, kinds);
  json.text += ','; json.Key("active"); json.Optional(value.active);
  json.text += ','; json.Key("same_draft_window_bound"); json.Optional(value.same_draft_window_bound);
  json.text += ','; json.Key("native_can_accept"); json.Optional(value.native_can_accept);
  json.text += '}';
}
void FullCanJson(Json& json, const FullCan& value) {
  json.text += '{'; json.Key("observed"); json.Boolean(value.observed);
  json.text += ','; json.Key("can_create"); json.Optional(value.can_create);
  json.text += ','; json.Key("can_edit"); json.Optional(value.can_edit);
  json.text += ','; json.Key("create_reason"); json.Optional(value.create_reason);
  json.text += ','; json.Key("edit_reason"); json.Optional(value.edit_reason);
  json.text += '}';
}
void QuoteJson(Json& json, const Quote& value) {
  json.text += '{'; json.Key("observed"); json.Boolean(value.observed);
  json.text += ','; json.Key("piety_cost_raw"); json.Optional(value.piety_cost_raw);
  json.text += ','; json.Key("piety_missing_signed_raw"); json.Optional(value.piety_missing_signed_raw);
  json.text += ','; json.Key("has_enough_piety"); json.Optional(value.has_enough_piety);
  json.text += ','; json.Key("raw_scale"); json.Integer(Quote::raw_scale);
  json.text += '}';
}
void LeafJson(Json& json, const Result& value) {
  json.text += '{'; json.Key("schema"); json.String(schema);
  json.text += ','; json.Key("operation"); json.String(Name(value.operation, operations));
  json.text += ','; json.Key("available"); json.Boolean(value.available);
  json.text += ','; json.Key("status"); json.String(value.status);
  json.text += ','; json.Key("unavailable_reason");
  if (value.available) json.text += "null"; else json.String(value.unavailable_reason);
  json.text += ','; json.Key("frame"); FrameJson(json, value.frame);
  json.text += ','; json.Key("draft"); DraftJson(json, value.draft);
  json.text += ','; json.Key("modal"); ModalJson(json, value.modal);
  json.text += ','; json.Key("full_can"); FullCanJson(json, value.full_can);
  json.text += ','; json.Key("quote"); QuoteJson(json, value.quote);
  json.text += ','; json.Key("preview_identity_available"); json.Boolean(value.preview_identity_available);
  json.text += ','; json.Key("preview_identity"); json.Optional(value.preview_identity);
  json.text += ','; json.Key("complete_command_payload_observed"); json.Boolean(value.complete_command_payload_observed);
  json.text += ','; json.Key("original_writer_inputs_observed"); json.Boolean(value.original_writer_inputs_observed);
  json.text += ','; json.Key("native_command_text_bytes"); json.Optional(value.native_command_text_bytes);
  json.text += ','; json.Key("native_command_text_sha256"); json.Optional(value.native_command_text_sha256);
  json.text += ','; json.Key("native_dispatch_attempted"); json.Boolean(value.native_dispatch_attempted);
  json.text += ','; json.Key("dispatch_invoked"); json.Boolean(value.dispatch_invoked);
  json.text += ','; json.Key("verification_pending"); json.Boolean(value.verification_pending);
  json.text += ','; json.Key("original_writer_may_have_been_queued"); json.Boolean(value.original_writer_may_have_been_queued);
  json.text += ','; json.Key("business_outcome_observed"); json.Boolean(value.business_outcome_observed);
  json.text += ','; json.Key("already_in_requested_state"); json.Boolean(value.already_in_requested_state);
  json.text += ','; json.Key("selection_or_name_postcondition_observed"); json.Boolean(value.selection_or_name_postcondition_observed);
  json.text += ','; json.Key("draft_open_postcondition_observed"); json.Boolean(value.draft_open_postcondition_observed);
  json.text += ','; json.Key("native_once_claimed"); json.Boolean(value.native_once_claimed);
  json.text += ','; json.Key("action_id"); json.Optional(value.action_id);
  json.text += '}';
}
}  // namespace

bool ParseRequest12004(std::string_view input, WireRequest& output,
                                    std::string& reason) noexcept {
  output = {};
  try {
    reason.clear();
    if (input.empty() || input.size() > maximum_wire_request_bytes)
      return Fail(reason, "rite_creation_request_size_invalid");
    std::vector<Value> values;
    if (!Parser(input).Object(values, reason)) return false;
    WireRequest candidate{};
    std::string type, requested_step, operation;
    std::uint64_t protocol_version = 0, source = 0;
    if (!Text(values, "type", type) || type != "execute_step" ||
        !Number(values, "protocol_version", protocol_version) || protocol_version != 1 ||
        !Text(values, "request_id", candidate.request_id) || !ControlId(candidate.request_id) ||
        !Text(values, "step", requested_step) || requested_step != step ||
        !Number(values, "expected_revision", candidate.expected_revision) || !candidate.expected_revision ||
        !Number(values, "expected_connection_generation", candidate.expected_connection_generation) ||
        !candidate.expected_connection_generation ||
        !Number(values, "expected_date_raw", candidate.expected_date_raw) ||
        !Number(values, "expected_player_character_id", candidate.expected_player_character_id) ||
        candidate.expected_player_character_id <= 0 ||
        !Text(values, "operation", operation) || !Named(operation, operations, candidate.request.operation) ||
        !Number(values, "expected_source_rite_id", source) || source >= absent)
      return Fail(reason, "rite_creation_request_envelope_or_assertion_invalid");
    candidate.request.expected_source_rite_id = static_cast<std::uint32_t>(source);
    std::vector<std::string_view> admitted(all_keys.begin(), all_keys.begin() + 10);
    const auto require_text = [&](std::string_view key, std::string& target) {
      admitted.push_back(key);
      return Text(values, key, target);
    };
    switch (candidate.request.operation) {
      case Operation::select_core_tenet: {
        std::uint32_t index = 0;
        admitted.push_back("core_slot_index");
        if (!Number(values, "core_slot_index", index) ||
            !require_text("tenet_key", candidate.request.tenet_key))
          return Fail(reason, "rite_creation_tenet_selectors_invalid");
        candidate.request.core_slot_index = index;
        break;
      }
      case Operation::select_doctrine:
        if (!require_text("group_key", candidate.request.group_key) ||
            !require_text("doctrine_key", candidate.request.doctrine_key))
          return Fail(reason, "rite_creation_doctrine_selectors_invalid");
        break;
      case Operation::set_name_field: {
        std::string field;
        NameField parsed{};
        if (!require_text("name_field", field) || !Named(field, name_fields, parsed) ||
            !require_text("text", candidate.request.text))
          return Fail(reason, "rite_creation_name_selectors_invalid");
        candidate.request.name_field = parsed;
        break;
      }
      case Operation::prepare_confirmation:
      case Operation::confirm_once: {
        std::string kind;
        Outcome parsed{};
        if (!require_text("expected_preview_identity", candidate.request.expected_preview_identity) ||
            !require_text("expected_outcome_kind", kind) || !Named(kind, outcomes, parsed))
          return Fail(reason, "rite_creation_confirmation_assertions_invalid");
        candidate.request.expected_outcome_kind = parsed;
        if (candidate.request.operation == Operation::confirm_once &&
            (!require_text("action_id", candidate.request.action_id) ||
             candidate.request.action_id != candidate.request_id))
          return Fail(reason, "rite_creation_confirmation_action_id_differs");
        break;
      }
      case Operation::open_create_draft:
      case Operation::open_edit_current_rite_draft:
      case Operation::preview: break;
    }
    if (values.size() != admitted.size() || std::any_of(values.begin(), values.end(), [&](const Value& value) {
          return std::find(admitted.begin(), admitted.end(), value.key) == admitted.end();
        })) return Fail(reason, "rite_creation_request_selector_fields_differ");
    if (!ValidateRequest(candidate.request)) return Fail(reason, "rite_creation_native_request_invalid");
    output = std::move(candidate);
    return true;
  } catch (...) {
    output = {};
    return Fail(reason, "rite_creation_request_parse_exception");
  }
}

bool MatchRequestFrame(const WireRequest& request,
    const Frame& actual, std::string& reason) noexcept {
  try {
    reason.clear();
    if (!actual.connection_generation || !actual.native_revision ||
        actual.played_character_id <= 0)
      return Fail(reason, "rite_creation_actual_owner_frame_unavailable");
    if (!request.expected_revision || request.expected_revision != actual.native_revision)
      return Fail(reason, "rite_creation_expected_revision_differs");
    if (!request.expected_connection_generation ||
        request.expected_connection_generation != actual.connection_generation)
      return Fail(reason, "rite_creation_connection_generation_differs");
    if (request.expected_date_raw != actual.date_raw)
      return Fail(reason, "rite_creation_date_raw_differs");
    if (request.expected_player_character_id != actual.played_character_id)
      return Fail(reason, "rite_creation_player_character_id_differs");
    return true;
  } catch (...) { return false; }
}
bool MatchRequestFrame(const WireRequest& request, const Frame& actual) noexcept {
  std::string ignored;
  return MatchRequestFrame(request, actual, ignored);
}

bool FormatRiteCreationActionLeaf12004(const Result& result, std::string& output,
                                     std::string& reason) noexcept {
  output.clear();
  try {
    reason.clear();
    if (!ResultContract(result, reason)) return false;
    Json json;
    LeafJson(json, result);
    if (!json.valid) return Fail(reason, "rite_creation_result_utf8_or_enum_invalid");
    output = std::move(json.text);
    return true;
  } catch (...) { return Fail(reason, "rite_creation_result_format_exception"); }
}

bool FormatResult12004(const Result& result, std::string& output,
                      std::string& reason) noexcept {
  output.clear();
  try {
    reason.clear();
    if (!ResultContract(result, reason)) return false;
    Json json;
    json.text += '{'; json.Key("step"); json.String(step);
    json.text += ','; json.Key("accepted"); json.Boolean(true);
    json.text += ','; json.Key("private_build"); json.Boolean(true);
    json.text += ','; json.Key("advertised"); json.Boolean(false);
    json.text += ','; json.Key("status"); json.String(result.status);
    json.text += ','; json.Key("snapshot_revision"); json.Integer(result.frame.native_revision);
    json.text += ','; json.Key("date_raw"); json.Integer(result.frame.date_raw);
    json.text += ','; json.Key("read_only"); json.Boolean(result.operation == Operation::preview);
    json.text += ','; json.Key("domain_key"); json.String(domain_key);
    json.text += ','; json.Key("backend_id"); json.String(native_backend_id);
    json.text += ','; json.Key("game_version"); json.String(ck3_12004::kGameVersion);
    json.text += ','; json.Key("executable_sha256"); json.String(ck3_12004::kExecutableSha256);
    json.text += ','; json.Key(result_key); LeafJson(json, result); json.text += '}';
    if (!json.valid) return Fail(reason, "rite_creation_result_utf8_or_enum_invalid");
    output = std::move(json.text);
    return true;
  } catch (...) { return Fail(reason, "rite_creation_result_format_exception"); }
}
std::string SerializeCommandResult12004(const Result& result,
                                      std::string_view request_id) noexcept {
  try {
    if (!ControlId(request_id)) return {};
    if (result.operation == Operation::confirm_once &&
        (!result.action_id || *result.action_id != request_id)) return {};
    std::string body, reason;
    if (!FormatResult12004(result, body, reason)) return {};
    Json json;
    json.text += '{'; json.Key("type"); json.String("command_result");
    json.text += ','; json.Key("protocol_version"); json.Integer(1);
    json.text += ','; json.Key("request_id"); json.String(request_id);
    json.text += ','; json.Key("ok"); json.Boolean(true);
    json.text += ','; json.Key("result"); json.text += body; json.text += '}';
    return json.valid ? std::move(json.text) : std::string{};
  } catch (...) { return {}; }
}
}  // namespace xar::ck3_12004::religion::rite_creation_actions
