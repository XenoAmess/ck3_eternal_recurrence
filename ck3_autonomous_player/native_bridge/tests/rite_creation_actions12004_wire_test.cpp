// Future C++ unit fixture source only. This file has not been built or run by
// the source lane. Synthetic DTOs below test JSON formatting; no JSON packet is
// emitted or saved, and none is evidence of an original CK3 call or live result.
#include "xar_bridge/rite_creation_actions12004_wire.hpp"

#include <array>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <string>
#include <string_view>
#include <utility>

namespace a = xar::ck3_12004::religion::rite_creation_actions;
namespace {
void Check(bool passed, const char* label) {
  if (!passed) { std::fputs(label, stderr); std::fputc('\n', stderr); std::abort(); }
}
std::string Make(std::string_view operation, std::string_view selectors = {}) {
  std::string json = R"({"type":"execute_step","protocol_version":1,"request_id":"rite-action-0123456789abcdef0123456789abcdef","step":"player-rite-creation-action-v1","expected_revision":9,"expected_connection_generation":7,"expected_date_raw":-100,"expected_player_character_id":42,"expected_source_rite_id":17,"operation":")";
  json += operation; json += '"'; json += selectors; json += '}';
  return json;
}
std::string Replace(std::string value, std::string_view first, std::string_view second) {
  const auto at = value.find(first);
  Check(at != std::string::npos, "fixture replacement absent");
  value.replace(at, first.size(), second);
  return value;
}
void Reject(const std::string& json, const char* label) {
  a::WireRequest request{}; std::string reason;
  Check(!a::ParseRequest12004(json, request, reason), label);
  Check(!reason.empty(), "parse rejection retains diagnostic");
  Check(request.expected_revision == 0 && request.request.expected_source_rite_id == a::absent,
        "rejected request cannot retain partially parsed assertions");
}
void Parsing() {
  const std::string token(64, 'a');
  const std::array<std::pair<std::string, std::string>, 8> cases{{
      {"open_create_draft", ""}, {"open_edit_current_rite_draft", ""},
      {"select_core_tenet", R"(,"core_slot_index":0,"tenet_key":"tenet_ritual_cannibalism")"},
      {"select_doctrine", R"(,"group_key":"doctrine_clerical_marriage","doctrine_key":"doctrine_clerical_marriage_allowed")"},
      {"set_name_field", R"(,"name_field":"name","text":"")"}, {"preview", ""},
      {"prepare_confirmation", ",\"expected_preview_identity\":\"" + token + "\",\"expected_outcome_kind\":\"create_faith\""},
      {"confirm_once", ",\"expected_preview_identity\":\"" + token + "\",\"expected_outcome_kind\":\"edit_rite\",\"action_id\":\"rite-action-0123456789abcdef0123456789abcdef\""}
  }};
  for (std::size_t n = 0; n != cases.size(); ++n) {
    a::WireRequest request{}; std::string reason;
    Check(a::ParseRequest12004(Make(cases[n].first, cases[n].second), request, reason), "all eight finite operations parse");
    Check(static_cast<std::size_t>(request.request.operation) == n && reason.empty(), "operation identity preserved");
    Check(request.expected_revision == 9 && request.expected_connection_generation == 7 &&
        request.expected_date_raw == -100 && request.expected_player_character_id == 42 &&
        request.request.expected_source_rite_id == 17, "assertions are separate from Request");
  }
  for (const auto field : {"name", "adjective", "adherent", "adherent_plural", "description"}) {
    a::WireRequest request{}; std::string reason;
    Check(a::ParseRequest12004(Make("set_name_field", ",\"name_field\":\"" + std::string(field) +
        "\",\"text\":\"\""), request, reason), "all five actual name fields allow empty text");
    Check(request.request.name_field.has_value() && request.request.text.empty(), "empty name is a value, not absence");
  }
  a::WireRequest request{}; std::string reason;
  Check(a::ParseRequest12004(Make("set_name_field", R"(,"name_field":"description","text":"\u4fe1\u4ef0\n\t\uD83D\uDE00")"), request, reason),
        "escaped Unicode BMP plus supplementary pair and description whitespace");
  Check(request.request.text == "\xE4\xBF\xA1\xE4\xBB\xB0\n\t\xF0\x9F\x98\x80", "Unicode escapes decode to complete UTF-8");
  Check(a::ParseRequest12004(Make("set_name_field", R"(,"name_field":"name","text":"a\"b\\c\/d")"), request, reason),
        "quote backslash slash escapes accepted");
  Check(request.request.text == "a\"b\\c/d", "JSON escaping is decoded exactly once");
  Check(a::ParseRequest12004(Make("set_name_field", R"(,"name_field":"description","text":"\"rva\":0,\"operation\":\"preview\"")"), request, reason),
        "field-like text is never searched as a control field");
  Check(a::ParseRequest12004(" \r\n" + Make("preview") + "\t ", request, reason), "ordinary JSON whitespace");
  Check(a::ParseRequest12004(Replace(Make("preview"), "\"expected_revision\":9", "\"expected_revision\":18446744073709551615"), request, reason),
        "full uint64 native revision retained");
  Check(request.expected_revision == std::numeric_limits<std::uint64_t>::max(), "uint64 not rounded through floating point");
  Check(a::ParseRequest12004(Replace(Make("preview"), "\"expected_source_rite_id\":17", "\"expected_source_rite_id\":0"), request, reason), "source full ID zero is not absent sentinel");

  Reject(Make("arbitrary_native_call"), "unknown operation rejected");
  Reject(Make("set_name_field", R"(,"name_field":"faith_icon","text":"x")"), "unknown name field rejected");
  Reject(Make("preview", R"(,"operation":"confirm_once")"), "duplicate operation rejected");
  Reject(Make("preview", R"(,"oper\u0061tion":"confirm_once")"), "duplicate decoded key rejected");
  Reject(Make("preview", R"(,"pointer":123)"), "pointer injection rejected");
  Reject(Make("preview", R"(,"rva":123)"), "RVA injection rejected");
  Reject(Make("preview", R"(,"decision_key":"adopt_holy_site_decision")"), "foreign decision selector rejected");
  Reject(Make("preview", R"(,"text":"x")"), "cross-operation selector rejected");
  Reject(Make("select_doctrine", R"(,"group_key":"g","doctrine_key":"d","core_slot_index":0)"), "cross-selector mixture rejected");
  Reject(Make("select_core_tenet", R"(,"core_slot_index":64,"tenet_key":"x")"), "native core slot bound retained");
  Reject(Make("select_core_tenet", R"(,"core_slot_index":0,"tenet_key":"Bad-Key")"), "definition selectors remain finite ASCII keys");
  Reject(Make("set_name_field", R"(,"name_field":"name","text":{"text":"x"})"), "nested object rejected");
  Reject(Make("set_name_field", R"(,"name_field":"name","text":["x"])"), "nested array rejected");
  Reject(Make("set_name_field", R"(,"name_field":"name","text":null)"), "null is not a name string");
  Reject(Make("set_name_field", R"(,"name_field":"name","text":"\uD800")"), "unpaired high surrogate rejected");
  Reject(Make("set_name_field", R"(,"name_field":"name","text":"\uDC00")"), "unpaired low surrogate rejected");
  Reject(Make("set_name_field", R"(,"name_field":"name","text":"\uD800\u0041")"), "invalid surrogate partner rejected");
  Reject(Make("set_name_field", R"(,"name_field":"name","text":"\u0000")"), "embedded NUL rejected by native request validator");
  Reject(Make("set_name_field", R"(,"name_field":"name","text":"\n")"), "name newline rejected");
  Reject(Make("set_name_field", R"(,"name_field":"description","text":"\r")"), "description permits only LF and tab controls");
  Reject(Make("set_name_field", R"(,"name_field":"name","text":"\x41")"), "non-JSON escape rejected");
  Reject(Make("set_name_field", ",\"name_field\":\"name\",\"text\":\"" + std::string("\xC0\xAF", 2) + "\""), "overlong raw UTF-8 rejected");
  Reject(Make("set_name_field", ",\"name_field\":\"name\",\"text\":\"" + std::string("\xED\xA0\x80", 3) + "\""), "raw UTF-8 surrogate rejected");
  Reject(Make("set_name_field", ",\"name_field\":\"name\",\"text\":\"" + std::string(31, 'x') + "\""), "native thirty-character bound retained");
  Reject(Make("set_name_field", ",\"name_field\":\"description\",\"text\":\"" + std::string(4097, 'x') + "\""), "bounded decoded text enforced");
  Reject(std::string(a::maximum_wire_request_bytes + 1, ' '), "whole request budget enforced");
  Reject(Replace(Make("preview"), "\"expected_revision\":9", "\"expected_revision\":0"), "zero native revision rejected");
  Reject(Replace(Make("preview"), "\"expected_revision\":9,", ""), "native revision mandatory");
  Reject(Replace(Make("preview"), "\"expected_revision\":9", "\"expected_revision\":true"), "boolean cannot masquerade as revision");
  Reject(Replace(Make("preview"), "\"expected_revision\":9", "\"expected_revision\":9.0"), "float revision rejected");
  Reject(Replace(Make("preview"), "\"expected_revision\":9", "\"expected_revision\":09"), "leading zero rejected");
  Reject(Replace(Make("preview"), "\"expected_revision\":9", "\"expected_revision\":-0"), "negative unsigned assertion rejected");
  Reject(Replace(Make("preview"), "\"expected_revision\":9", "\"expected_revision\":18446744073709551616"), "uint64 overflow rejected");
  Reject(Replace(Make("preview"), "\"expected_connection_generation\":7", "\"expected_connection_generation\":0"), "connection generation mandatory nonzero");
  Reject(Replace(Make("preview"), "\"expected_date_raw\":-100", "\"expected_date_raw\":2147483648"), "native date int32 bound retained");
  Reject(Replace(Make("preview"), "\"expected_player_character_id\":42", "\"expected_player_character_id\":0"), "actual player binding is positive");
  Reject(Replace(Make("preview"), "\"expected_source_rite_id\":17", "\"expected_source_rite_id\":4294967295"), "invalid full source ID sentinel rejected");
  Reject(Replace(Make("preview"), "\"protocol_version\":1", "\"protocol_version\":2"), "foreign protocol rejected");
  Reject(Make("preview") + "{}", "trailing object rejected");
  Reject(Make("preview") + "true", "trailing scalar rejected");
  Reject(Replace(Make("preview"), "\"operation\":\"preview\"", "\"operation\":\"preview\","), "trailing comma rejected");
  Reject(Make("confirm_once", ",\"expected_preview_identity\":\"" + token + "\",\"expected_outcome_kind\":\"create_rite\",\"action_id\":\"different\""), "final action ID tied to actual request ID");
  Reject(Make("prepare_confirmation", ",\"expected_preview_identity\":\"" + token + "\",\"expected_outcome_kind\":\"create_rite\",\"action_id\":\"x\""), "prepare cannot acquire a confirm identity");
}
void ActualFrame() {
  a::WireRequest request{}; std::string reason;
  Check(a::ParseRequest12004(Make("preview"), request, reason), "frame fixture request parses");
  const a::Frame actual{7, 9, 1, -100, 42};
  Check(a::MatchRequestFrame(request, actual) && a::MatchRequestFrame(request, actual, reason), "actual owner frame matches assertions");
  auto changed = actual; changed.native_revision = 10;
  Check(!a::MatchRequestFrame(request, changed), "actual native revision difference rejected");
  changed = actual; ++changed.connection_generation;
  Check(!a::MatchRequestFrame(request, changed), "actual connection difference rejected");
  changed = actual; ++changed.date_raw;
  Check(!a::MatchRequestFrame(request, changed), "actual date difference rejected");
  changed = actual; ++changed.played_character_id;
  Check(!a::MatchRequestFrame(request, changed), "actual player difference rejected");
  changed = actual; changed.capture_epoch = 0;
  Check(a::MatchRequestFrame(request, changed), "prepare frame matching checks four assertions before owner pump stamps capture");
  Check(!a::MatchRequestFrame(request, a::Frame{}), "zero/default actual frame is rejected");
}
void FormattingOnlySyntheticUnitValues() {
  a::Result result{};
  result.frame = {20, 55, 44, -10, 123};
  std::string json, reason;
  Check(a::FormatResult12004(result, json, reason), "unavailable actual result formats");
  Check(json.find("\"private_build\":true") != std::string::npos &&
      json.find("\"advertised\":false") != std::string::npos,
      "private G2 envelope retains fixed private_build true and advertised false");
  Check(json.find("\"snapshot_revision\":55") != std::string::npos &&
      json.find("\"connection_generation\":20") != std::string::npos, "formatter uses Result.frame, not request assertions");
  Check(json.find("\"can_create\":null") != std::string::npos &&
      json.find("\"piety_cost_raw\":null") != std::string::npos &&
      json.find("\"selected_core_tenets\":null") != std::string::npos, "unobserved optionals remain null");
  Check(json.find("\"read_only\":true") != std::string::npos &&
      json.find("ck3-1.20.0.4-native-rite-creation-action-v1") != std::string::npos &&
      json.find("native-native") == std::string::npos, "fixed single-native backend and preview read-only envelope");
  result.frame.capture_epoch = 0;
  Check(!a::FormatResult12004(result, json, reason) && json.empty(), "actual result must retain owner capture epoch");
  result.frame.capture_epoch = 44;
  result.full_can.observed = true; result.full_can.can_create = false;
  result.quote.observed = true;
  result.quote.piety_cost_raw = std::numeric_limits<std::int64_t>::min();
  result.quote.piety_missing_signed_raw = std::numeric_limits<std::int64_t>::max();
  result.quote.has_enough_piety = false;
  result.draft.names[0] = "a\"b\\c\n";
  Check(a::FormatResult12004(result, json, reason), "known false values and full signed raw integers format");
  Check(json.find("\"can_create\":false") != std::string::npos &&
      json.find("\"can_edit\":null") != std::string::npos &&
      json.find("-9223372036854775808") != std::string::npos &&
      json.find("9223372036854775807") != std::string::npos &&
      json.find("a\\\"b\\\\c\\n") != std::string::npos, "formatter preserves optional false, signed range, and escaping");
  const auto packet = a::SerializeCommandResult12004(result, "rite-action-unit-only");
  Check(packet.find("\"type\":\"command_result\"") != std::string::npos &&
      packet.find("\"request_id\":\"rite-action-unit-only\"") != std::string::npos, "normal command_result wrapper");
  Check(a::SerializeCommandResult12004(result, "bad\nrequest").empty(), "unsafe control request ID not serialized");
  result.preview_identity_available = true; result.preview_identity = std::string(64, 'a');
  Check(!a::FormatResult12004(result, json, reason) && json.empty(), "partial proof cannot format a preview identity");
  result.preview_identity_available = false; result.preview_identity.reset();
  result.draft.names[0] = std::string("\xFF", 1);
  Check(!a::FormatResult12004(result, json, reason) && json.empty(), "invalid native UTF-8 is rejected, not replaced");
  result.draft.names[0].reset(); result.business_outcome_observed = true;
  Check(!a::FormatResult12004(result, json, reason), "writer serializer cannot claim an independent business outcome");
  result.business_outcome_observed = false; result.dispatch_invoked = true;
  Check(!a::FormatResult12004(result, json, reason), "inconsistent dispatch flags rejected");

  // Deliberately synthetic complete DTO: this checks format admission only.
  // No game callback, writer or canonical payload is invoked or represented.
  result = {};
  result.frame = {20, 55, 44, -10, 123};
  result.available = true; result.status = "observed"; result.unavailable_reason.clear();
  result.draft.observed = result.draft.names_observed = true;
  result.draft.selected_core_tenets_observed = result.draft.selected_doctrines_observed = true;
  result.draft.source_rite_id = 1; result.draft.source_faith_id = 2; result.draft.actor_faith_id = 2;
  result.draft.actual_outcome_kind = a::Outcome::create_rite;
  for (auto& name : result.draft.names) name = std::string{};
  result.modal.observed = true; result.modal.stage = a::ModalStage::none;
  result.modal.active = false;
  result.full_can.observed = true; result.full_can.can_create = true; result.full_can.can_edit = false;
  result.quote.observed = true; result.quote.piety_cost_raw = 0;
  result.quote.piety_missing_signed_raw = 0; result.quote.has_enough_piety = true;
  result.preview_identity_available = true; result.preview_identity = std::string(64, 'a');
  result.complete_command_payload_observed = result.original_writer_inputs_observed = true;
  result.native_command_text_bytes = 3; result.native_command_text_sha256 = std::string(64, 'b');
  Check(a::FormatResult12004(result, json, reason), "complete synthetic proof DTO serializes without replacing false Can or zero raw values");
  Check(json.find("\"preview_identity_available\":true") != std::string::npos &&
      json.find("\"original_writer_inputs_observed\":true") != std::string::npos &&
      json.find("\"native_command_text_bytes\":3") != std::string::npos &&
      json.find("\"selected_core_tenets\":[]") != std::string::npos, "complete proof fields and observed empty collections retained");
  result.original_writer_inputs_observed = false;
  Check(!a::FormatResult12004(result, json, reason), "canonical draft bytes alone do not prove original writer inputs");
  result.original_writer_inputs_observed = true; result.native_command_text_bytes = 0;
  Check(!a::FormatResult12004(result, json, reason), "empty command text is not complete proof");
  result.native_command_text_bytes = 3; result.draft.names[4].reset();
  Check(!a::FormatResult12004(result, json, reason), "unknown draft field prevents a complete preview identity");

  result = {}; result.operation = a::Operation::confirm_once;
  result.frame = {20, 55, 44, -10, 123}; result.action_id = "rite-action-unit-only";
  Check(!a::SerializeCommandResult12004(result, "rite-action-unit-only").empty(), "known-no-dispatch confirmation retains action ID metadata");
  Check(a::SerializeCommandResult12004(result, "rite-action-other").empty(), "formatter refuses a foreign confirmation request identity");
}
}  // namespace
int main() {
  Parsing();
  ActualFrame();
  FormattingOnlySyntheticUnitValues();
  return 0;
}
