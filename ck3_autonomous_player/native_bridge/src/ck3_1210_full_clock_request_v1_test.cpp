#include "xar_bridge/ck3_1210_full_clock_request_v1.hpp"

#include <algorithm>
#include <array>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <string>
#include <utility>
#include <vector>

namespace {
using namespace xar::ck3_1210;
using Field = std::pair<std::string, std::string>;
using Fields = std::vector<Field>;
void Require(bool value, const char *message) {
  if (!value) { std::cerr << "FAIL " << message << '\n'; std::exit(1); }
}
std::string Q(std::string_view value) { return "\"" + std::string(value) + "\""; }
std::string Object(const Fields &fields) {
  std::string result = "{";
  for (const auto &[key, value] : fields) {
    if (result.size() != 1) result += ',';
    result += Q(key) + ':' + value;
  }
  result += '}';
  return result;
}
void Set(Fields &fields, std::string_view key, std::string value) {
  const auto found = std::find_if(fields.begin(), fields.end(),
      [key](const Field &field) { return field.first == key; });
  Require(found != fields.end(), "fixture member exists");
  found->second = std::move(value);
}
Fields Claim(std::string_view revision = "7", std::string_view snapshot = "7",
    std::string_view deadline = "123456789") {
  return {{"schema", Q(kFullClockRequestClaimSchemaV1)}, {"game_version", Q(kGameVersion)},
      {"executable_sha256", Q(kExecutableSha256)}, {"adapter_id", Q(kAdapterId)},
      {"backend", Q(kCoreBackendV1)}, {"snapshot_id", Q("native:" + std::string(snapshot))},
      {"native_revision", std::string(revision)}, {"deadline_unix_ms", std::string(deadline)}};
}
Fields Root(std::string claim = Object(Claim()), std::string_view step = "pause-map",
    std::string_view revision = "7", bool arguments = true) {
  Fields fields{{"type", Q("execute_step")}, {"protocol_version", "1"},
      {"request_id", Q("R-01_a.Z")}, {"step", Q(step)},
      {"expected_revision", std::string(revision)},
      {"full_snapshot_clock_control", std::move(claim)}};
  if (arguments) fields.emplace_back("arguments", "{}");
  return fields;
}
void Rejected(std::string_view text) {
  FullClockRequestV1 out{CoreControlOperationV1::application_exit, "stale", 99,
      (std::numeric_limits<std::uint64_t>::max)(), 999};
  Require(!ParseFullClockRequestV1(text, out), "invalid request rejected");
  Require(out.operation == CoreControlOperationV1::unavailable && out.step.empty() &&
      out.public_speed == 0 && out.native_revision == 0 && out.deadline_unix_ms == 0,
      "all failure paths clear stale DTO");
}
struct StepCase {
  std::string_view step;
  CoreControlOperationV1 operation;
  std::int32_t speed;
};
constexpr std::array steps{
    StepCase{"pause-map", CoreControlOperationV1::pause, 0},
    StepCase{"resume-map", CoreControlOperationV1::resume, 0},
    StepCase{"save-checkpoint", CoreControlOperationV1::save, 0},
    StepCase{"set-speed-1", CoreControlOperationV1::speed, 1},
    StepCase{"set-speed-2", CoreControlOperationV1::speed, 2},
    StepCase{"set-speed-3", CoreControlOperationV1::speed, 3},
    StepCase{"set-speed-4", CoreControlOperationV1::speed, 4},
    StepCase{"set-speed-5", CoreControlOperationV1::speed, 5}};

FullClockRequestV1 Accepted(std::string_view text, const StepCase &step,
    std::uint64_t revision = 7, std::uint64_t deadline = 123456789) {
  FullClockRequestV1 out{};
  Require(ParseFullClockRequestV1(text, out) && out.operation == step.operation &&
      out.step == step.step && out.public_speed == step.speed &&
      out.native_revision == revision && out.deadline_unix_ms == deadline,
      "exact normalized request DTO");
  return out;
}
void StaticStepLifetime(const StepCase &step) {
  std::string payload = Object(Root(Object(Claim()), step.step));
  const auto begin = reinterpret_cast<std::uintptr_t>(payload.data());
  const auto end = begin + payload.size();
  const auto out = Accepted(payload, step);
  const auto pointer = reinterpret_cast<std::uintptr_t>(out.step.data());
  Require(pointer < begin || pointer >= end, "success step does not borrow payload storage");
  std::fill(payload.begin(), payload.end(), '#');
  Require(out.step == step.step, "step survives original request overwrite");
  std::string{}.swap(payload);
  Require(out.step == step.step && out.operation == step.operation,
      "step survives release of original request bytes");
}
} // namespace

int main() {
  using namespace xar::ck3_1210;
  for (const auto &step : steps) {
    StaticStepLifetime(step);
    // Rotate every claim field through every position; rotate the independent
    // outer object as well. arguments is intentionally absent in half cases.
    auto claim = Claim();
    for (std::size_t rotation = 0; rotation < claim.size(); ++rotation) {
      auto root = Root(Object(claim), step.step, "7", rotation % 2 == 0);
      const auto shift = rotation % root.size();
      std::rotate(root.begin(), root.begin() + static_cast<std::ptrdiff_t>(shift), root.end());
      Accepted(Object(root), step);
      std::rotate(claim.begin(), claim.begin() + 1, claim.end());
    }
    std::reverse(claim.begin(), claim.end());
    auto reversed = Root(Object(claim), step.step);
    std::reverse(reversed.begin(), reversed.end());
    Accepted(Object(reversed), step);
  }
  const auto base = Object(Root());
  Accepted(" \t\r\n" + base + "\n\r\t ", steps[0]);
  {
    auto fields = Root(); Set(fields, "arguments", "{ \t\r\n }");
    Accepted(Object(fields), steps[0]);
    std::string padded(16384 - base.size(), ' '); padded += base;
    Accepted(padded, steps[0]); padded += ' '; Rejected(padded);
  }
  {
    auto claim = Claim(); std::string hash(kExecutableSha256);
    for (char &ch : hash) if (ch >= 'A' && ch <= 'F') ch = static_cast<char>(ch - 'A' + 'a');
    Set(claim, "executable_sha256", Q(hash));
    Accepted(Object(Root(Object(claim))), steps[0]);
    for (std::size_t i = 0; i < hash.size(); i += 2)
      if (hash[i] >= 'a' && hash[i] <= 'f') hash[i] = static_cast<char>(hash[i] - 'a' + 'A');
    Set(claim, "executable_sha256", Q(hash));
    Accepted(Object(Root(Object(claim))), steps[0]);
  }
  constexpr std::string_view maximum = "18446744073709551615";
  Accepted(Object(Root(Object(Claim(maximum, maximum, maximum)), "set-speed-5", maximum)),
      steps[7], (std::numeric_limits<std::uint64_t>::max)(),
      (std::numeric_limits<std::uint64_t>::max)());
  Accepted(Object(Root(Object(Claim("1", "1", "1")), "pause-map", "1")), steps[0], 1, 1);

  // Every required field is required, and each recognized field is unique.
  for (std::size_t i = 0; i < 6; ++i) {
    auto fields = Root(); fields.erase(fields.begin() + static_cast<std::ptrdiff_t>(i));
    Rejected(Object(fields));
  }
  for (std::size_t i = 0; i < 7; ++i) {
    auto fields = Root(); const auto duplicate = fields[i]; fields.push_back(duplicate);
    Rejected(Object(fields));
  }
  for (std::size_t i = 0; i < 8; ++i) {
    auto claim = Claim(); claim.erase(claim.begin() + static_cast<std::ptrdiff_t>(i));
    Rejected(Object(Root(Object(claim))));
    claim = Claim(); const auto duplicate = claim[i]; claim.push_back(duplicate);
    Rejected(Object(Root(Object(claim))));
  }
  for (const auto key : {"core_clock_control", "core_application_exit", "full_clock_control",
           "core_control_deadline_unix_ms", "authority", "unknown"}) {
    auto fields = Root(); fields.emplace_back(key, "{}"); Rejected(Object(fields));
  }
  for (const auto key : {"date_raw", "paused", "speed", "observed_at_ms", "core_clock_control"}) {
    auto claim = Claim(); claim.emplace_back(key, "1"); Rejected(Object(Root(Object(claim))));
  }
  for (const auto alias : {"core_clock_control", "core_application_exit"}) {
    auto fields = Root(); fields[5].first = alias; Rejected(Object(fields));
  }
  for (const auto schema : {"ck3_1210_core_clock_control_v1", "ck3_1210_application_exit_v1", ""}) {
    auto claim = Claim(); Set(claim, "schema", Q(schema)); Rejected(Object(Root(Object(claim))));
  }
  for (const auto step : {"normal-exit-application-v1", "set-speed-0", "set-speed-6",
           "set-speed-01", "set-speed-+1", "set-speed--1", "set-speed-1 ",
           "pause", "pause-map ", "PAUSE-MAP", "", "save-checkpoint-v1"})
    Rejected(Object(Root(Object(Claim()), step)));
  for (const auto type : {"step", "command", "execute_step ", "EXECUTE_STEP", ""}) {
    auto fields = Root(); Set(fields, "type", Q(type)); Rejected(Object(fields));
  }
  for (const auto argument : {"null", "[]", "1", "true", "\"{}\"", "{\"speed\":1}", "{,}"}) {
    auto fields = Root(); Set(fields, "arguments", argument); Rejected(Object(fields));
  }
  for (const auto object : {"null", "[]", "true", "1", "{}", "\"claim\""}) {
    auto fields = Root(); Set(fields, "full_snapshot_clock_control", object);
    Rejected(Object(fields));
  }
  for (const auto token : {"0", "-1", "-0", "+1", "01", "1.0", "1e0", "1E+0",
           "18446744073709551616", "true", "null", "\"7\""}) {
    auto fields = Root(); Set(fields, "expected_revision", token); Rejected(Object(fields));
    auto claim = Claim(); Set(claim, "native_revision", token);
    Rejected(Object(Root(Object(claim))));
    claim = Claim(); Set(claim, "deadline_unix_ms", token);
    Rejected(Object(Root(Object(claim))));
  }
  for (const auto token : {"0", "2", "-1", "-0", "+1", "01", "1.0", "1e0",
           "18446744073709551616", "true", "null", "\"1\""}) {
    auto fields = Root(); Set(fields, "protocol_version", token); Rejected(Object(fields));
  }
  for (const auto suffix : {"", "0", "00", "01", "-1", "-0", "+1", "1.0", "1e0",
           "7 ", " 7", "18446744073709551616", "8"})
    Rejected(Object(Root(Object(Claim("7", suffix)))));
  for (const auto id : {"Native:7", "native7", "native::7", "native:7:7", "native:7x"}) {
    auto claim = Claim(); Set(claim, "snapshot_id", Q(id));
    Rejected(Object(Root(Object(claim))));
  }
  Rejected(Object(Root(Object(Claim("8", "8"))))); // Outer revision differs.
  Rejected(Object(Root(Object(Claim("7", "8"))))); // ID differs from claim revision.
  for (const auto field : {"game_version", "executable_sha256", "adapter_id", "backend"}) {
    auto claim = Claim(); Set(claim, field, Q("wrong")); Rejected(Object(Root(Object(claim))));
  }
  {
    auto claim = Claim(); Set(claim, "executable_sha256", Q(
        "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"));
    Rejected(Object(Root(Object(claim))));
  }
  for (const auto value : {"", "a b", "a/b", "a:b", "a\\b", "a\nb", "a\tb"}) {
    auto fields = Root(); Set(fields, "request_id", Q(value)); Rejected(Object(fields));
  }
  {
    auto fields = Root(); Set(fields, "request_id", Q(std::string(96, 'A')));
    Accepted(Object(fields), steps[0]); Set(fields, "request_id", Q(std::string(97, 'A')));
    Rejected(Object(fields));
  }
  for (const auto byte : {0, 1, 31, 127, 128, 255}) {
    auto fields = Root(); Set(fields, "request_id", Q("x" + std::string(1, static_cast<char>(byte))));
    Rejected(Object(fields));
    Rejected(base + std::string(1, static_cast<char>(byte)));
  }
  {
    auto fields = Root(); fields[3].first = "st\\u0065p"; Rejected(Object(fields));
    fields = Root(); fields[2].first = "request\\u005fid"; Rejected(Object(fields));
    auto claim = Claim(); claim[0].first = "sche\\u006da";
    Rejected(Object(Root(Object(claim))));
    fields = Root(); Set(fields, "type", Q("execute\\u005fstep")); Rejected(Object(fields));
  }
  Rejected(""); Rejected("{}"); Rejected("[]"); Rejected("null");
  Rejected(base + "{}"); Rejected(base + "junk"); Rejected(base.substr(0, base.size() - 1));
  Rejected(std::string("\xEF\xBB\xBF") + base);
  {
    auto comma = base; comma.insert(comma.size() - 1, ","); Rejected(comma);
    auto claim = Object(Claim()); claim.insert(claim.size() - 1, ",");
    Rejected(Object(Root(claim)));
    auto fields = Root(); fields.emplace_back(std::string(193, 'x'), "1");
    Rejected(Object(fields));
  }
  std::cout << "PASS synthetic Full-clock closed wire/eight steps/order/uint64/"
      "claim separation/static step lifetime; parser only, no native authority\n";
  return 0;
}
