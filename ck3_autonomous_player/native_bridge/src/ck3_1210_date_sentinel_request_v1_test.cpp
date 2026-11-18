#include "xar_bridge/ck3_1210_date_sentinel_request_v1.hpp"

#include <algorithm>
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
constexpr std::string_view hash =
    "2F2B236A16223891C2DA8B167F5F3738D2AE3E6D69DE1B4FBE190A5402998ACC";
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
  return result + '}';
}
void Set(Fields &fields, std::string_view key, std::string value) {
  const auto found = std::find_if(fields.begin(), fields.end(),
      [key](const Field &field) { return field.first == key; });
  Require(found != fields.end(), "fixture field exists");
  found->second = std::move(value);
}
std::string Step(std::string_view start = "1", std::string_view target = "25",
    std::string_view speed = "3", std::string_view tail = "-mode-terminal-a-0") {
  return "research-arm-tactical-daily-sentinel-v1-" + std::string(start) +
      "-to-" + std::string(target) + "-speed-" + std::string(speed) + std::string(tail);
}
Fields Claim(std::string_view revision = "7", std::string_view snapshot = "7",
    std::string_view deadline = "123456789") {
  return {{"schema", Q(kDateSentinelArmRequestClaimSchemaV1)},
      {"game_version", Q("1.21.0")}, {"executable_sha256", Q(hash)},
      {"adapter_id", Q("ck3-1.21.0-msvc-x64")},
      {"backend", Q("ck3-1.21.0-native-headless-main-thread")},
      {"snapshot_id", Q("native:" + std::string(snapshot))},
      {"native_revision", std::string(revision)}, {"deadline_unix_ms", std::string(deadline)}};
}
Fields Root(std::string step = Step(), std::string claim = Object(Claim()),
    std::string_view revision = "7", bool arguments = true) {
  Fields result{{"type", Q("execute_step")}, {"protocol_version", "1"},
      {"request_id", Q("Sentinel-01_a.Z")}, {"step", Q(step)},
      {"expected_revision", std::string(revision)}, {"date_sentinel_arm", std::move(claim)}};
  if (arguments) result.emplace_back("arguments", "{}");
  return result;
}
void Rejected(std::string_view text) {
  DateSentinelArmRequestV1 out{};
  out.step_bytes.fill('s'); out.step_size = out.step_bytes.size();
  out.starting_date_raw = 1; out.target_date_raw = 25; out.speed = 5;
  out.native_revision = (std::numeric_limits<std::uint64_t>::max)();
  out.deadline_unix_ms = 999;
  Require(!ParseDateSentinelArmRequestV1(text, out) && out.step_size == 0 &&
      out.Step().empty() && out.starting_date_raw == 0 && out.target_date_raw == 0 &&
      out.speed == 0 && out.native_revision == 0 && out.deadline_unix_ms == 0 &&
      std::all_of(out.step_bytes.begin(), out.step_bytes.end(), [](char ch) { return ch == 0; }),
      "failure clears all owned step bytes and scalar DATA");
}
DateSentinelArmRequestV1 Accepted(std::string_view payload, std::string_view step,
    std::int32_t start = 1, std::int32_t target = 25, std::int32_t speed = 3,
    std::uint64_t revision = 7, std::uint64_t deadline = 123456789) {
  DateSentinelArmRequestV1 out{};
  Require(ParseDateSentinelArmRequestV1(payload, out) && out.Step() == step &&
      out.step_size == step.size() && out.Step().data() == out.step_bytes.data() &&
      out.starting_date_raw == start && out.target_date_raw == target && out.speed == speed &&
      out.native_revision == revision && out.deadline_unix_ms == deadline,
      "exact owned date-sentinel DATA");
  return out;
}
void Ownership(std::int32_t speed) {
  const auto step = Step("1", "25", std::to_string(speed));
  std::string payload = Object(Root(step));
  auto original = Accepted(payload, step, 1, 25, speed);
  std::fill(payload.begin(), payload.end(), '#');
  Require(original.Step() == step, "own step survives request overwrite");
  std::string{}.swap(payload);
  Require(original.Step() == step, "own step survives request storage release");
  auto copy = original;
  Require(copy.Step().data() == copy.step_bytes.data() &&
      copy.Step().data() != original.Step().data(), "copied DTO view points to itself");
  original.step_bytes.fill('x'); original.step_size = 0;
  Require(copy.Step() == step, "copy does not depend on original DTO");
  DateSentinelArmRequestV1 assigned{}; assigned = copy;
  auto moved = std::move(copy); copy.step_bytes.fill('y'); copy.step_size = 0;
  Require(assigned.Step() == step && assigned.Step().data() == assigned.step_bytes.data() &&
      moved.Step() == step && moved.Step().data() == moved.step_bytes.data(),
      "assignment and move also retain self-owned views");
  std::vector<DateSentinelArmRequestV1> relocated;
  relocated.reserve(1); relocated.push_back(moved); relocated.emplace_back();
  moved.step_bytes.fill('z'); moved.step_size = 0;
  Require(relocated[0].Step() == step &&
      relocated[0].Step().data() == relocated[0].step_bytes.data(), "container relocation is owned");
}
} // namespace

int main() {
  using namespace xar::ck3_1210;
  for (std::int32_t speed = 1; speed <= 5; ++speed) {
    Ownership(speed);
    const auto step = Step("1", "25", std::to_string(speed));
    auto claim = Claim();
    for (std::size_t i = 0; i < claim.size(); ++i) {
      auto root = Root(step, Object(claim), "7", i % 2 == 0);
      std::rotate(root.begin(), root.begin() + static_cast<std::ptrdiff_t>(i % root.size()), root.end());
      Accepted(Object(root), step, 1, 25, speed);
      std::rotate(claim.begin(), claim.begin() + 1, claim.end());
    }
    std::reverse(claim.begin(), claim.end()); auto root = Root(step, Object(claim));
    std::reverse(root.begin(), root.end()); Accepted(Object(root), step, 1, 25, speed);
  }
  const auto valid_step = Step(), base = Object(Root());
  Accepted(" \t\r\n" + base + "\n\t ", valid_step);
  {
    auto root = Root(); Set(root, "arguments", "{ \r\n\t }"); Accepted(Object(root), valid_step);
    std::string padded(16384 - base.size(), ' '); padded += base;
    Accepted(padded, valid_step); padded += ' '; Rejected(padded);
  }
  Accepted(Object(Root(Step("1", "49"))), Step("1", "49"), 1, 49);
  Accepted(Object(Root(Step("2147483623", "2147483647"))),
      Step("2147483623", "2147483647"), 2147483623, 2147483647);
  Accepted(Object(Root(Step("1", "2147483641"))), Step("1", "2147483641"), 1, 2147483641);
  constexpr std::string_view maximum = "18446744073709551615";
  Accepted(Object(Root(valid_step, Object(Claim(maximum, maximum, maximum)), maximum)),
      valid_step, 1, 25, 3, (std::numeric_limits<std::uint64_t>::max)(),
      (std::numeric_limits<std::uint64_t>::max)());
  Accepted(Object(Root(valid_step, Object(Claim("1", "1", "1")), "1")), valid_step, 1, 25, 3, 1, 1);
  {
    auto claim = Claim(); std::string lower(hash);
    for (char &ch : lower) if (ch >= 'A' && ch <= 'F') ch = static_cast<char>(ch - 'A' + 'a');
    Set(claim, "executable_sha256", Q(lower)); Accepted(Object(Root(valid_step, Object(claim))), valid_step);
  }
  for (const auto token : {"", "0", "00", "01", "-1", "+1", "1.0", "1e0", "1E+0",
           "2147483648", "4294967295", "18446744073709551615", " 1", "1 "}) {
    Rejected(Object(Root(Step(token, "25"))));
    Rejected(Object(Root(Step("1", token))));
  }
  for (const auto target : {"1", "24", "26"}) Rejected(Object(Root(Step("1", target))));
  Rejected(Object(Root(Step("25", "1"))));
  Rejected(Object(Root(Step("2147483646", "2147483647"))));
  for (const auto speed : {"", "0", "6", "01", "10", "+1", "-1", "1.0", "1e0"})
    Rejected(Object(Root(Step("1", "25", speed))));
  for (const auto tail : {"", "-mode-decision-a-0", "-mode-terminal", "-a-0",
           "-mode-Terminal-a-0", "-mode-terminal-a-1", "-mode-terminal-a-2147483647",
           "-mode-terminal-a-00", "-mode-terminal-a--1", "-mode-terminal-a-+0",
           "-mode-terminal-a-0-extra", "-mode-terminal-a-0 "})
    Rejected(Object(Root(Step("1", "25", "3", tail))));
  Rejected(Object(Root("Research-arm-tactical-daily-sentinel-v1-1-to-25-speed-3-mode-terminal-a-0")));
  Rejected(Object(Root("pause-map"))); Rejected(Object(Root("normal-exit-application-v1")));
  for (std::size_t i = 0; i < 6; ++i) {
    auto root = Root(); root.erase(root.begin() + static_cast<std::ptrdiff_t>(i)); Rejected(Object(root));
  }
  for (std::size_t i = 0; i < 7; ++i) {
    auto root = Root(); const auto duplicate = root[i]; root.push_back(duplicate); Rejected(Object(root));
  }
  for (std::size_t i = 0; i < 8; ++i) {
    auto claim = Claim(); claim.erase(claim.begin() + static_cast<std::ptrdiff_t>(i));
    Rejected(Object(Root(valid_step, Object(claim))));
    claim = Claim(); const auto duplicate = claim[i]; claim.push_back(duplicate);
    Rejected(Object(Root(valid_step, Object(claim))));
  }
  for (const auto key : {"full_snapshot_clock_control", "core_clock_control", "core_application_exit",
           "core_control_deadline_unix_ms", "authority", "unknown"}) {
    auto root = Root(); root.emplace_back(key, "{}"); Rejected(Object(root));
    root = Root(); root[5].first = key; Rejected(Object(root));
  }
  for (const auto schema : {"ck3_1210_full_clock_control_v1", "ck3_1210_core_clock_control_v1",
           "ck3_1210_application_exit_v1", ""}) {
    auto claim = Claim(); Set(claim, "schema", Q(schema));
    Rejected(Object(Root(valid_step, Object(claim))));
  }
  for (const auto key : {"starting_date_raw", "target_date_raw", "speed", "observed_at_ms"}) {
    auto claim = Claim(); claim.emplace_back(key, "1"); Rejected(Object(Root(valid_step, Object(claim))));
  }
  for (const auto token : {"0", "-1", "-0", "+1", "01", "1.0", "1e0",
           "18446744073709551616", "true", "null", "\"7\""}) {
    auto root = Root(); Set(root, "expected_revision", token); Rejected(Object(root));
    auto claim = Claim(); Set(claim, "native_revision", token);
    Rejected(Object(Root(valid_step, Object(claim))));
    claim = Claim(); Set(claim, "deadline_unix_ms", token);
    Rejected(Object(Root(valid_step, Object(claim))));
  }
  for (const auto token : {"0", "2", "01", "-0", "1.0", "1e0", "true", "\"1\""}) {
    auto root = Root(); Set(root, "protocol_version", token); Rejected(Object(root));
  }
  for (const auto suffix : {"0", "01", "-1", "+1", "1e0", " 7", "7 ",
           "18446744073709551616", "8"})
    Rejected(Object(Root(valid_step, Object(Claim("7", suffix)))));
  Rejected(Object(Root(valid_step, Object(Claim("8", "8")))));
  {
    auto claim = Claim(); Set(claim, "snapshot_id", Q("Native:7"));
    Rejected(Object(Root(valid_step, Object(claim))));
  }
  for (const auto key : {"game_version", "executable_sha256", "adapter_id", "backend"}) {
    auto claim = Claim(); Set(claim, key, Q("wrong")); Rejected(Object(Root(valid_step, Object(claim))));
  }
  for (const auto value : {"null", "[]", "true", "\"{}\"", "{\"mode\":\"terminal\"}"}) {
    auto root = Root(); Set(root, "arguments", value); Rejected(Object(root));
    root = Root(); Set(root, "date_sentinel_arm", value); Rejected(Object(root));
  }
  {
    auto root = Root(); Set(root, "request_id", Q(std::string(96, 'A')));
    Accepted(Object(root), valid_step); Set(root, "request_id", Q(std::string(97, 'A')));
    Rejected(Object(root));
  }
  for (const auto value : {"", "a b", "a/b", "a:b", "a\\b", "a\nb"}) {
    auto root = Root(); Set(root, "request_id", Q(value)); Rejected(Object(root));
  }
  for (const auto byte : {0, 1, 31, 127, 128, 255}) {
    auto root = Root(); Set(root, "request_id", Q("x" + std::string(1, static_cast<char>(byte))));
    Rejected(Object(root)); Rejected(base + std::string(1, static_cast<char>(byte)));
  }
  {
    auto root = Root(); root[3].first = "st\\u0065p"; Rejected(Object(root));
    auto claim = Claim(); claim[0].first = "sche\\u006da";
    Rejected(Object(Root(valid_step, Object(claim))));
    root = Root(); Set(root, "step", Q("research\\u002darm-tactical-daily-sentinel-v1-1-to-25-speed-3-mode-terminal-a-0"));
    Rejected(Object(root));
  }
  Rejected(""); Rejected("{}"); Rejected("[]"); Rejected("null");
  Rejected(base + "junk"); Rejected(base + "{}"); Rejected(base.substr(0, base.size() - 1));
  Rejected(std::string("\xEF\xBB\xBF") + base);
  {
    auto trailing = base; trailing.insert(trailing.size() - 1, ","); Rejected(trailing);
    auto claim = Object(Claim()); claim.insert(claim.size() - 1, ",");
    Rejected(Object(Root(valid_step, claim)));
    auto root = Root(std::string(193, 'x')); Rejected(Object(root));
    root = Root(); Set(root, "type", Q("command")); Rejected(Object(root));
  }
  DateSentinelArmRequestV1 corrupted{}; corrupted.step_size = 193;
  Require(corrupted.Step().empty(), "owned view never exceeds192 byte storage");
  std::cout << "PASS synthetic date-sentinel closed wire/canonical terminal grammar/"
      "int32 dates/uint64 join/owned DATA copies; no legacy or Native call\n";
  return 0;
}
