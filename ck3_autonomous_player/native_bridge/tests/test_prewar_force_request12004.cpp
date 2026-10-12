// Pure control-schema fixture: no mailbox execution, bindings, Game or SDK.
#include "xar_bridge/prewar_force_coalition_request12004.hpp"

#include <algorithm>
#include <iostream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {
using Request = xar::ck3_12004::PrewarForceCoalitionRequest12004;
using Fields = std::vector<std::pair<std::string, std::string>>;
constexpr std::string_view kStep = "query-prewar-force-coalition-coverage-v1";
constexpr std::string_view kRequestId = "fixture-current-request";
unsigned cases = 0;
unsigned assertions = 0;

void Require(bool condition, const std::string &message) {
  ++assertions;
  if (!condition) throw std::runtime_error(message);
}

std::string Object(const Fields &fields) {
  std::string text = "{";
  for (const auto &[key, value] : fields) {
    if (text.size() != 1) text += ',';
    text += '"' + key + "\":" + value;
  }
  return text + '}';
}

Fields Selected() {
  return {{"target_character_id", "536936448"}, {"casus_belli_index", "3"},
          {"casus_belli_key", "\"claim_cb_4\""}, {"configuration_index", "-1"},
          {"claimant_character_id", "-1"}, {"target_title_ids", "[0,65536,0,65536]"}};
}

Fields Top(const Fields &selected = Selected()) {
  auto fields = Fields{{"type", "\"execute_step\""}, {"protocol_version", "1"},
      {"request_id", "\"fixture-current-request\""},
      {"step", "\"query-prewar-force-coalition-coverage-v1\""},
      {"expected_revision", "17"}, {"expected_public_revision", "29"},
      {"declaration_id", "\"536936448-3--1\""},
      {"selected_declaration", Object(selected)}};
  return fields;
}

Request Parse(const std::string &payload, std::string_view step = kStep,
              std::string_view request_id = kRequestId) {
  ++cases;
  Request out;
  Require(xar::ck3_12004::ParsePrewarForceCoalitionRequest12004(
      payload, step, request_id, out), "valid request rejected");
  return out;
}

void Reject(const std::string &name, const std::string &payload,
            std::string_view step = kStep, std::string_view request_id = kRequestId) {
  ++cases;
  Request out;
  out.expected_native_revision = 991;
  out.expected_public_revision = 992;
  out.declaration_id = "unchanged";
  out.selected.target_character_id = 993;
  out.selected.casus_belli_index = 995;
  out.selected.casus_belli_key = "unchanged_cb";
  out.selected.configuration_index = 996;
  out.selected.claimant_character_id = 997;
  out.selected.target_title_ids = {994, 0, 994};
  Require(!xar::ck3_12004::ParsePrewarForceCoalitionRequest12004(
      payload, step, request_id, out), name + " accepted");
  Require(out.expected_native_revision == 991 && out.expected_public_revision == 992 &&
      out.declaration_id == "unchanged" && out.selected.target_character_id == 993 &&
      out.selected.casus_belli_index == 995 && out.selected.casus_belli_key == "unchanged_cb" &&
      out.selected.configuration_index == 996 && out.selected.claimant_character_id == 997 &&
      out.selected.target_title_ids == std::vector<std::int32_t>{994, 0, 994},
      name + " modified output on refusal");
}

void TopValue(std::size_t index, const std::string &value, const std::string &name) {
  auto top = Top(); top[index].second = value; Reject(name, Object(top));
}

void SelectedValue(std::size_t index, const std::string &value, const std::string &name) {
  auto selected = Selected(); selected[index].second = value;
  const auto selected_payload = Object(selected);
  xar::ck3_12004::prewar_request12004::Cursor cursor(selected_payload);
  Request selected_output;
  ++cases;
  Require(!xar::ck3_12004::prewar_request12004::Selected(cursor, selected_output.selected) ||
      !cursor.End(), name + " accepted by selected parser independently of canonical ID");
  Reject(name, Object(Top(selected)));
}

void ValidCases() {
  const auto out = Parse(Object(Top()));
  Require(out.expected_native_revision == 17 && out.expected_public_revision == 29,
      "native/public revision association changed");
  Require(out.declaration_id == "536936448-3--1" &&
      out.selected.target_character_id == 536936448 && out.selected.casus_belli_index == 3 &&
      out.selected.casus_belli_key == "claim_cb_4" &&
      out.selected.configuration_index == -1 && out.selected.claimant_character_id == -1,
      "selected full-ID tuple changed");
  Require(out.selected.target_title_ids == std::vector<std::int32_t>{0, 65536, 0, 65536},
      "TitleID zero, duplicates or ordering lost");
  auto selected = Selected(); std::reverse(selected.begin(), selected.end());
  auto top = Top(selected); std::reverse(top.begin(), top.end());
  Require(Parse(" \r\n\t" + Object(top) + " \n").selected.target_title_ids ==
      out.selected.target_title_ids, "field reordering or JSON whitespace changed values");
  selected = Selected(); selected[5].second = "[]";
  Require(Parse(Object(Top(selected))).selected.target_title_ids.empty(), "empty titles rejected");
  top = Top(); top[4].second = "18446744073709551615";
  top[5].second = "18446744073709551615";
  const auto maximum = Parse(Object(top));
  Require(maximum.expected_native_revision == UINT64_MAX &&
      maximum.expected_public_revision == UINT64_MAX, "uint64 revision truncated");
  selected = Selected();
  for (const auto i : {0U, 1U, 3U, 4U}) selected[i].second = "2147483647";
  selected[5].second = "[2147483647,0,2147483647]";
  top = Top(selected); top[6].second = "\"2147483647-2147483647-2147483647\"";
  const auto ids = Parse(Object(top));
  Require(ids.selected.target_character_id == INT32_MAX &&
      ids.selected.claimant_character_id == INT32_MAX &&
      ids.selected.target_title_ids.back() == INT32_MAX, "int32 IDs truncated");
  selected = Selected(); selected[5].second = "[0";
  for (unsigned i = 1; i < 4096; ++i) selected[5].second += ",0";
  selected[5].second += ']';
  Require(Parse(Object(Top(selected))).selected.target_title_ids.size() == 4096,
      "4096-title boundary rejected");
  selected[5].second.insert(selected[5].second.size() - 1, ",0");
  Reject("4097 titles", Object(Top(selected)));
}

void ClosedSchemaCases() {
  for (std::size_t i = 0; i < 8; ++i) {
    auto fields = Top(); fields.erase(fields.begin() + static_cast<std::ptrdiff_t>(i));
    Reject("missing top " + std::to_string(i), Object(fields));
    fields = Top(); fields.push_back(fields[i]);
    Reject("duplicate top " + std::to_string(i), Object(fields));
  }
  for (std::size_t i = 0; i < 6; ++i) {
    auto fields = Selected(); fields.erase(fields.begin() + static_cast<std::ptrdiff_t>(i));
    Reject("missing selected " + std::to_string(i), Object(Top(fields)));
    fields = Selected(); fields.push_back(fields[i]);
    Reject("duplicate selected " + std::to_string(i), Object(Top(fields)));
  }
  auto top = Top(); top.push_back({"injected", Object(Top())});
  Reject("unknown nested top injection", Object(top));
  auto selected = Selected(); selected.push_back({"expected_revision", "17"});
  Reject("top key in selected injection", Object(Top(selected)));
  SelectedValue(0, "{\"target_character_id\":536936448}", "nested target injection");
  TopValue(0, "\"query\"", "wrong command type");
  TopValue(1, "2", "wrong protocol");
  Reject("request mismatch", Object(Top()), kStep, "another-request");
  Reject("empty expected request", Object(Top()), kStep, "");
  Reject("step mismatch", Object(Top()), "another-step");
  TopValue(6, "\"536936448-3-0\"", "configuration canonical mismatch");
  TopValue(6, "\"536936449-3--1\"", "target canonical mismatch");
  TopValue(6, "\"536936448-4--1\"", "CB canonical mismatch");
  TopValue(6, "\"0536936448-3--1\"", "noncanonical declaration identity");
  TopValue(2, "\"\"", "empty request");
  TopValue(3, "\"\"", "empty step");
  SelectedValue(2, "\"\"", "empty CB key");
  SelectedValue(2, "\"claim-cb\"", "CB key punctuation");
  TopValue(2, "\"fixture-current-\\u0072equest\"", "escaped identity");
  Reject("trailing data", Object(Top()) + " {}");
  Reject("trailing comma", Object(Top()).insert(Object(Top()).size() - 1, ","));
  Reject("unterminated object", Object(Top()).substr(0, Object(Top()).size() - 1));
  Reject("empty object", "{}"); Reject("array root", "[]");
  Reject("embedded NUL", Object(Top()) + std::string(1, '\0'));
  Reject("payload cap", Object(Top()) + std::string(1024 * 1024, ' '));
  auto long_id = std::string(129, 'a');
  top = Top(); top[2].second = '"' + long_id + '"';
  Reject("129-byte identity", Object(top), kStep, long_id);
}

void NumberCases() {
  for (const auto index : {1U, 4U, 5U}) {
    for (const auto *value : {"true", "false", "null", "1.0", "1e0", "\"1\"",
         "+1", "01", "-1", "18446744073709551616"})
      TopValue(index, value, "non-uint top " + std::to_string(index) + ':' + value);
    TopValue(index, "0", "zero required top " + std::to_string(index));
  }
  for (const auto index : {0U, 1U, 3U, 4U}) {
    for (const auto *value : {"true", "false", "null", "1.0", "1e0", "\"1\"",
         "+1", "01", "- 1", "-01", "2147483648", "-2147483648"})
      SelectedValue(index, value, "invalid ID " + std::to_string(index) + ':' + value);
  }
  SelectedValue(0, "0", "target zero"); SelectedValue(0, "-1", "target sentinel");
  SelectedValue(1, "-1", "negative CB index");
  SelectedValue(3, "-2", "configuration below sentinel");
  SelectedValue(4, "-2", "claimant below sentinel");
  for (const auto *value : {"[true]", "[1.0]", "[01]", "[- 1]", "[-1]",
       "[2147483648]", "[{}]", "[0,]", "null"})
    SelectedValue(5, value, "invalid title array " + std::string(value));
}
} // namespace

int main() {
  try {
    ValidCases(); ClosedSchemaCases(); NumberCases();
    std::cout << "prewar request pure fixture PASS cases=" << cases
              << " assertions=" << assertions << '\n';
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "prewar request pure fixture FAIL: " << error.what() << '\n';
    return 1;
  }
}
