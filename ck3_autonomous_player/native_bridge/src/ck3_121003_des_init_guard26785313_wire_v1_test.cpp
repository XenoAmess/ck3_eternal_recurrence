// Self-owned NoGame parser/serializer tests only. No runtime or ABI qualification.
// Link the actual candidate wire TU; do not include or duplicate its implementation.
#ifndef XAR_DES_INIT_GUARD_TEST_HEADER
#define XAR_DES_INIT_GUARD_TEST_HEADER "xar_bridge/ck3_121003_des_init_guard26785313_v1.hpp"
#endif
#include XAR_DES_INIT_GUARD_TEST_HEADER
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <Windows.h>
#include <algorithm>
#include <array>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <limits>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace g = xar::ck3_121003::build26785313;
namespace {
using Request = g::DesInitGuardRequest267V1;
using Result = g::DesInitGuardResult267V1;
using Source = g::DesInitGuardSource267V1;
using Status = g::DesInitGuardStatus267V1;
std::size_t checks = 0;

void Check(bool value, const char* label) {
  ++checks;
  if (!value) throw std::runtime_error(label);
}
bool Has(std::string_view wire, std::string_view text) {
  return wire.find(text) != std::string_view::npos;
}
std::string Replace(std::string value, std::string_view from, std::string_view to) {
  const auto offset = value.find(from);
  Check(offset != std::string::npos, "test mutation must change an actual input");
  value.replace(offset, from.size(), to);
  return value;
}

xar::ck3_1210::CoreSnapshotPrefix Core(std::int32_t actor = 36423) {
  xar::ck3_1210::CoreSnapshotPrefix core{};
  core.clock.date_raw = 53144328;
  core.clock.speed = 2;
  core.clock.paused = true;
  core.local_player_id = 0;
  core.map_ready = true;
  core.has_played_character = true;
  core.played_character_id = actor;
  core.played_character_alive = true;
  return core;
}

std::string CoreJson(std::int32_t actor = 36423) {
  return "{\"date_raw\":53144328,\"speed\":2,\"paused\":true,"
    "\"local_player_id\":0,\"map_ready\":true,\"has_played_character\":true,"
    "\"played_character_id\":" + std::to_string(actor) + ",\"played_character_alive\":true}";
}

std::string Query(std::string_view id = "des-guard-query-original-01", std::int32_t actor = 36423) {
  return std::string("{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"") +
    std::string(id) + "\",\"step\":\"" + g::kDesInitGuardStep267V1 +
    "\",\"expected_revision\":0,\"arguments\":{},\"des_init_guard\":{\"schema\":\"" +
    g::kDesInitGuardRequestSchema267V1 + "\",\"game_version\":\"" + g::kGameVersion +
    "\",\"executable_sha256\":\"" + g::kExecutableSha256 + "\",\"adapter_id\":\"" +
    g::kAdapterId + "\",\"backend\":\"" + g::kDesInitGuardBackend267V1 +
    "\",\"action\":\"query_guard\",\"expected_core\":" + CoreJson(actor) +
    "},\"core_control_deadline_unix_ms\":18446744073709551615}";
}

Result Available(std::int32_t actor = 36423, bool shown = false) {
  Result result{};
  result.status = Status::available;
  result.source_available = true;
  result.cleanup_known = true;
  result.facts_available = true;
  result.provider_generation = (std::numeric_limits<std::uint64_t>::max)();
  result.query_sequence = (std::numeric_limits<std::uint64_t>::max)();
  result.connection_generation = (std::numeric_limits<std::uint64_t>::max)();
  result.ticket_sequence = (std::numeric_limits<std::uint64_t>::max)();
  result.pump_epoch = (std::numeric_limits<std::uint64_t>::max)();
  result.thread_id = (std::numeric_limits<std::uint32_t>::max)();
  result.facts = Core(actor);
  result.source = Source{actor, true, true, true, shown, true, true};
  return result;
}

void NoEffect(const std::string& wire) {
  for (const auto text : {"\"action\":\"query_guard\"", "\"claim_sequence\":\"0\"",
    "\"effect_attempted\":false", "\"native_returned\":false", "\"native_handled\":false",
    "\"initialization_executed\":false", "\"migration_executed\":false",
    "\"new_date_observed\":false", "\"physical_save_confirmed\":false", "\"addresses_redacted\":true"})
    Check(Has(wire, text), "readonly family must preserve all zero-effect fields");
}
void Refused(const std::string& wire, std::string_view status) {
  NoEffect(wire);
  Check(Has(wire, "\"ok\":false"), "rejection must not be outer successful");
  Check(Has(wire, std::string("\"status\":\"") + std::string(status) + "\""), "exact typed rejection status");
  Check(Has(wire, "\"source_available\":false"), "no usable Source");
  Check(Has(wire, "\"source\":null"), "rejection must not leak a partial Source");
  Check(!Has(wire, "\"unavailable_reason\":null"), "refusal has an actual reason");
}

void ValidRequestAndSignedPackedIds() {
  for (const auto actor : {std::int32_t{36423}, std::int32_t{0}, std::int32_t{-2},
       (std::numeric_limits<std::int32_t>::min)(), (std::numeric_limits<std::int32_t>::max)()}) {
    Request q{};
    Check(g::ParseDesInitGuardRequest267V1(Query("des-guard-signed-id", actor), q), "all packed IDs except -1 are allowed");
    Check(q.id() == "des-guard-signed-id", "request ID retained");
    Check(q.expected.played_character_id == actor, "full signed actor retained");
    Check(q.deadline_unix_ms == (std::numeric_limits<std::uint64_t>::max)(), "deadline is full unsigned64");
    Check(g::DesInitGuardRequestShape267V1(q), "accepted parser result meets shape");
  }
  auto lower = Query();
  std::string digest = g::kExecutableSha256;
  std::transform(digest.begin(), digest.end(), digest.begin(), [](char c) { return c >= 'A' && c <= 'F' ? static_cast<char>(c - 'A' + 'a') : c; });
  lower = Replace(lower, g::kExecutableSha256, digest);
  Request q{};
  Check(g::ParseDesInitGuardRequest267V1(lower, q), "only exact digest case normalization is allowed");
}

void DuplicateAndUnknownFieldsAreRejected() {
  const auto query = Query();
  std::vector<std::string> invalid{
    Replace(query, "\"protocol_version\":1", "\"protocol_version\":1,\"protocol_version\":1"),
    Replace(query, "\"action\":\"query_guard\"", "\"action\":\"query_guard\",\"action\":\"query_guard\""),
    Replace(query, "\"paused\":true", "\"paused\":true,\"paused\":true"),
    Replace(query, "\"type\":", "\"caller_permission\":true,\"type\":"),
    Replace(query, "\"action\":", "\"guard_key\":\"des_saved_game_initialize_gui\",\"action\":"),
    Replace(query, "\"expected_core\":", "\"actor\":36423,\"expected_core\":"),
    Replace(query, "\"paused\":true", "\"unknown_core_field\":false,\"paused\":true"),
    Replace(query, "\"arguments\":{}", "\"arguments\":{\"key\":\"arbitrary\"}"),
    Replace(query, "\"query_guard\"", "\"execute\""),
    Replace(query, "\"expected_revision\":0", "\"expected_revision\":1"),
    Replace(query, "\"protocol_version\":1", "\"protocol_version\":2"),
    Replace(query, ",\"played_character_alive\":true", "")
  };
  for (const auto& wire : invalid) {
    Request out{};
    out.request_id_size = 1;
    out.request_id[0] = 'x';
    Check(!g::ParseDesInitGuardRequest267V1(wire, out), "duplicates/unknown/caller selectors must fail");
    Check(out.id().empty() && out.deadline_unix_ms == 0 && out.expected.played_character_id == -1,
      "failed parse leaves no stale accepted request authority");
  }
}

void MalformedNumbersTypesAndIdentityFail() {
  const auto query = Query();
  std::vector<std::string> invalid{
    Query("bad/id"), Query(""), Query(std::string(97, 'a')), Query("nonascii-\xc3\xa9"),
    Replace(query, "53144328", "053144328"),
    Replace(query, "\"speed\":2", "\"speed\":2.0"),
    Replace(query, "\"paused\":true", "\"paused\":1"),
    Replace(query, "\"local_player_id\":0", "\"local_player_id\":-0"),
    Replace(query, "\"played_character_id\":36423", "\"played_character_id\":2147483648"),
    Replace(query, "\"played_character_id\":36423", "\"played_character_id\":-2147483649"),
    Replace(query, "18446744073709551615", "18446744073709551616"),
    Replace(query, "18446744073709551615", "\"18446744073709551615\""),
    Replace(query, "18446744073709551615", "-1"),
    Replace(query, "18446744073709551615", "0"),
    Replace(query, g::kGameVersion, "1.20.0.4"),
    Replace(query, g::kDesInitGuardBackend267V1, "arbitrary-backend"),
    query + "{}", query.substr(0, query.size() - 1), std::string(16385, ' ')
  };
  for (const auto& wire : invalid) {
    Request out{};
    Check(!g::ParseDesInitGuardRequest267V1(wire, out), "malformed or misbound request must fail");
  }
  Request valid{};
  Check(g::ParseDesInitGuardRequest267V1(" \n\t" + Query(std::string(96, 'a')) + "\r\n", valid), "ASCII96 and surrounding JSON whitespace are valid");
}

void ExpectedCoreAndDirectShapeBoundaries() {
  Request accepted{};
  Check(g::ParseDesInitGuardRequest267V1(Query(), accepted), "test baseline request is real parser output");
  for (int field = 0; field < 9; ++field) {
    auto q = accepted;
    switch (field) {
      case 0: q.expected.played_character_id = -1; break;
      case 1: q.expected.local_player_id = -1; break;
      case 2: q.expected.clock.paused = false; break;
      case 3: q.expected.clock.speed = 0; break;
      case 4: q.expected.clock.speed = 6; break;
      case 5: q.expected.map_ready = false; break;
      case 6: q.expected.has_played_character = false; break;
      case 7: q.expected.played_character_alive = false; break;
      default: q.deadline_unix_ms = 0; break;
    }
    Check(!g::DesInitGuardRequestShape267V1(q), "direct request shape rejects invalid expected Core/deadline");
  }
  Request rejected{};
  Check(!g::ParseDesInitGuardRequest267V1(Query("invalid-id", -1), rejected), "parser rejects only reserved packed -1 actor");
  auto size = accepted;
  size.request_id_size = 97;
  Check(!g::DesInitGuardRequestShape267V1(size), "fixed ID buffer length beyond96 rejected before traversal");
  size = accepted;
  size.request_id_size = 0;
  Check(!g::DesInitGuardRequestShape267V1(size), "empty ID is invalid");
}

void FalseShownIsAvailableDataWithoutAnExecute() {
  for (const bool shown : {false, true}) {
    const auto wire = g::SerializeDesInitGuardResult267V1("des-guard-shown", Available(36423, shown));
    NoEffect(wire);
    Check(Has(wire, "\"ok\":true"), "shown false or true is a known available observation");
    Check(Has(wire, "\"status\":\"available\""), "actual data remains AVAILABLE");
    Check(Has(wire, shown ? "\"native_shown\":true" : "\"native_shown\":false"), "actual IsShown bool retained");
    Check(Has(wire, "\"guard_key\":\"des_saved_game_initialize_gui\""), "only fixed product guard is observed");
    Check(Has(wire, "\"unavailable_reason\":null"), "available result has no refusal reason");
  }
}

void SerializedSignedActorAndUnsignedWitnessesRetainTypes() {
  for (const auto actor : {std::int32_t{0}, std::int32_t{-2}, (std::numeric_limits<std::int32_t>::min)()}) {
    const auto wire = g::SerializeDesInitGuardResult267V1("des-guard-packed", Available(actor));
    NoEffect(wire);
    Check(Has(wire, "\"ok\":true"), "full packed actor can be nonpositive");
    Check(Has(wire, "\"character_id\":" + std::to_string(actor)), "actor remains signed JSON integer");
    Check(Has(wire, "\"provider_generation\":\"18446744073709551615\""), "provider retains canonical uint64 string");
    Check(Has(wire, "\"query_sequence\":\"18446744073709551615\""), "query retains canonical uint64 string");
    Check(Has(wire, "\"connection_generation\":\"18446744073709551615\""), "connection retains unsigned owner scalar");
    Check(Has(wire, "\"thread_id\":4294967295"), "thread retains unsigned32 integer");
  }
}

void IncompleteOrWrongSourceNeverBecomesFalseClosure() {
  for (int field = 0; field < 6; ++field) {
    auto r = Available();
    switch (field) {
      case 0: r.source->native_definition_found = false; break;
      case 1: r.source->native_is_player = false; break;
      case 2: r.source->scope_bound = false; break;
      case 3: r.source->sampled_twice = false; break;
      case 4: r.source->character_alive = false; break;
      default: r.source->character_id = -1; break;
    }
    Refused(g::SerializeDesInitGuardResult267V1("des-guard-partial", r), "indeterminate");
  }
  auto missing = Available();
  missing.status = Status::unavailable;
  missing.source->native_definition_found = false;
  missing.reason = "des_saved_game_init_guard_definition_unavailable";
  Refused(g::SerializeDesInitGuardResult267V1("des-guard-missing", missing), "unavailable");
}

void ChangedActorCoreCannotReuseOldSource() {
  auto changed = Available(36423);
  changed.status = Status::stale_source;
  changed.facts.played_character_id = 40180;
  changed.reason = "des_saved_game_init_guard_core_changed";
  const auto wire = g::SerializeDesInitGuardResult267V1("des-guard-changed-core", changed);
  Refused(wire, "stale_source");
  Check(Has(wire, "\"played_character_id\":40180"), "actual changed facts are preserved");
  Check(!Has(wire, "\"character_id\":36423"), "old actor Source is never emitted under new actor facts");
}

void CleanupUnknownOrIncompleteFactsCannotMintAvailableSource() {
  auto unknown = Available();
  unknown.cleanup_known = false;
  const auto wire = g::SerializeDesInitGuardResult267V1("des-guard-cleanup-unknown", unknown);
  Refused(wire, "indeterminate");
  Check(Has(wire, "\"cleanup_known\":false"), "raw cleanup unknown is not rewritten");
  for (int field = 0; field < 6; ++field) {
    auto r = Available();
    switch (field) {
      case 0: r.facts_available = false; break;
      case 1: r.connection_generation = 0; break;
      case 2: r.ticket_sequence = 0; break;
      case 3: r.pump_epoch = 0; break;
      case 4: r.thread_id = 0; break;
      default: r.facts.clock.speed = 0; break;
    }
    const auto partial = g::SerializeDesInitGuardResult267V1("des-guard-no-facts", r);
    Refused(partial, "indeterminate");
    Check(Has(partial, "\"facts_before\":null") && Has(partial, "\"owner\":null"), "facts/owner absence remains paired");
  }
}

void CleanTypedRefusalsAndEscapedReasonsStayReadonly() {
  const std::array<std::pair<Status, const char*>, 4> statuses{{
    {Status::unavailable, "unavailable"}, {Status::expired, "expired"},
    {Status::stale_source, "stale_source"}, {Status::indeterminate, "indeterminate"}
  }};
  for (const auto& [status, name] : statuses) {
    Result r{};
    r.status = status;
    r.reason = "self-owned \"refusal\"\\path\nline";
    const auto wire = g::SerializeDesInitGuardResult267V1("des-guard-refusal", r);
    Refused(wire, name);
    Check(Has(wire, "\"facts_before\":null") && Has(wire, "\"owner\":null"), "absent owner is never invented");
    Check(Has(wire, "\\\"refusal\\\"\\\\path\\u000aline"), "serializer escapes raw reason data");
  }
}

struct Frame { const char* file; const char* id; Result result; };

void WriteNew(const std::filesystem::path& file, const std::string& data) {
  const auto h = CreateFileW(file.c_str(), GENERIC_WRITE, 0, nullptr, CREATE_NEW, FILE_ATTRIBUTE_NORMAL, nullptr);
  if (h == INVALID_HANDLE_VALUE) throw std::runtime_error("CREATE_NEW output refused");
  DWORD written = 0;
  const bool ok = data.size() <= (std::numeric_limits<DWORD>::max)() &&
    WriteFile(h, data.data(), static_cast<DWORD>(data.size()), &written, nullptr) && written == data.size() && FlushFileBuffers(h);
  const bool closed = CloseHandle(h) != 0;
  Check(ok && closed, "complete immutable producer output write");
}

void Emit(const std::filesystem::path& output) {
  if (!std::filesystem::create_directory(output)) throw std::runtime_error("new emission directory must not exist");
  std::vector<Frame> frames;
  frames.push_back({"available-shown-false.json", "des-guard-query-original-01", Available()});
  frames.push_back({"available-shown-true.json", "des-guard-shown-true-02", Available(36423, true)});
  frames.push_back({"available-actor-zero.json", "des-guard-actor-zero-03", Available(0)});
  frames.push_back({"available-actor-negative.json", "des-guard-actor-negative-04", Available(-2)});
  auto missing = Available(); missing.status = Status::unavailable; missing.source->native_definition_found = false;
  missing.reason = "des_saved_game_init_guard_definition_unavailable";
  frames.push_back({"unavailable-missing-definition.json", "des-guard-missing-definition-05", missing});
  auto changed = Available(); changed.status = Status::stale_source; changed.facts.played_character_id = 40180;
  changed.reason = "des_saved_game_init_guard_core_changed";
  frames.push_back({"stale-source-actor-changed.json", "des-guard-core-changed-06", changed});
  auto unknown = Available(); unknown.cleanup_known = false;
  unknown.reason = "des_saved_game_init_guard_cleanup_unknown";
  frames.push_back({"indeterminate-cleanup-unknown.json", "des-guard-cleanup-unknown-07", unknown});
  Result expired{}; expired.status = Status::expired; expired.reason = "des_saved_game_init_guard_expired";
  frames.push_back({"expired-before-source.json", "des-guard-expired-08", expired});
  Result absent{}; absent.reason = "des_saved_game_init_guard_source_unavailable";
  frames.push_back({"unavailable-no-facts.json", "des-guard-no-facts-09", absent});
  auto partial = Available(); partial.source->sampled_twice = false;
  partial.reason = "des_saved_game_init_guard_incomplete_samples";
  frames.push_back({"indeterminate-incomplete-samples.json", "des-guard-incomplete-samples-10", partial});
  WriteNew(output / "request-query-guard.json", Query());
  std::vector<std::string> ids;
  for (const auto& frame : frames) {
    Check(std::find(ids.begin(), ids.end(), frame.id) == ids.end(), "emitted result IDs must be distinct");
    ids.push_back(frame.id);
    const auto wire = g::SerializeDesInitGuardResult267V1(frame.id, frame.result);
    NoEffect(wire);
    WriteNew(output / frame.file, wire);
  }
  Check(frames.size() == 10, "ten actual C++ serializer outputs");
}
} // namespace

int main(int argc, char** argv) {
  try {
    if(argc==3&&std::string_view(argv[1])=="--validate-request"){
      std::ifstream in(argv[2],std::ios::binary);if(!in)return 3;
      const std::string body{std::istreambuf_iterator<char>(in),std::istreambuf_iterator<char>()};Request request{};
      if(!g::ParseDesInitGuardRequest267V1(body,request)){std::fprintf(stderr,"actual retained request parser rejected\n");return 2;}
      std::printf("Actual DES fixed readonly request parser accepted %zu original bytes; no runtime permission.\n",body.size());return 0;
    }
    ValidRequestAndSignedPackedIds();
    DuplicateAndUnknownFieldsAreRejected();
    MalformedNumbersTypesAndIdentityFail();
    ExpectedCoreAndDirectShapeBoundaries();
    FalseShownIsAvailableDataWithoutAnExecute();
    SerializedSignedActorAndUnsignedWitnessesRetainTypes();
    IncompleteOrWrongSourceNeverBecomesFalseClosure();
    ChangedActorCoreCannotReuseOldSource();
    CleanupUnknownOrIncompleteFactsCannotMintAvailableSource();
    CleanTypedRefusalsAndEscapedReasonsStayReadonly();
    if (argc == 3 && std::string_view(argv[1]) == "--emit-json") Emit(std::filesystem::path(argv[2]));
    else if (argc != 1) throw std::runtime_error("usage: test [--emit-json NEW_DIRECTORY]");
    std::printf("DES guard: 10 self-owned NoGame wire scenarios, %zu checks; no runtime permission.\n", checks);
    return 0;
  } catch (const std::exception& error) {
    std::fprintf(stderr, "DES guard test failure after %zu checks: %s\n", checks, error.what());
    return 1;
  }
}
