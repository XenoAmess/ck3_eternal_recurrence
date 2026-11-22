// Self-owned NoGame DATA tests. Link the actual Native wire translation unit.
// No owner, raw reader, native callback, Game process, or runtime qualification.
#ifndef XAR_RITE_CREATE_TEST_HEADER
#define XAR_RITE_CREATE_TEST_HEADER "xar_bridge/ck3_121003_rite_create26785313_v1.hpp"
#endif
#include XAR_RITE_CREATE_TEST_HEADER
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <Windows.h>
#include <algorithm>
#include <array>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace g = xar::ck3_121003::build26785313;
namespace {
using Action = g::RiteCreateAction267V1;
using Phase = g::RiteCreatePhase267V1;
using Status = g::RiteCreateStatus267V1;
using Request = g::RiteCreateRequest267V1;
using Result = g::RiteCreateResult267V1;
using Source = g::RiteCreateSource267V1;
constexpr auto U64MAX = (std::numeric_limits<std::uint64_t>::max)();
std::size_t checks = 0;

void Check(bool condition, const char* message) {
  ++checks;
  if (!condition) throw std::runtime_error(message);
}
bool Has(std::string_view wire, std::string_view part) {
  return wire.find(part) != std::string_view::npos;
}
std::string Replace(std::string wire, std::string_view from, std::string_view to) {
  const auto at = wire.find(from);
  Check(at != std::string::npos, "test mutation must change an existing field");
  wire.replace(at, from.size(), to);
  return wire;
}
const char* ActionText(Action action) {
  switch (action) {
    case Action::query: return "query";
    case Action::create: return "create";
    case Action::query_confirmation: return "query_confirmation";
    case Action::accept_confirmation: return "accept_confirmation";
  }
  throw std::runtime_error("test builder received unknown action");
}
xar::ck3_1210::CoreSnapshotPrefix Core(std::int32_t actor = 36423) {
  xar::ck3_1210::CoreSnapshotPrefix core{};
  core.clock.date_raw = 53144328;
  core.clock.speed = 2;
  core.clock.paused = true;
  core.local_player_id = 0;
  core.map_ready = core.has_played_character = core.played_character_alive = true;
  core.played_character_id = actor;
  return core;
}
std::string CoreJson(std::int32_t actor) {
  return "{\"date_raw\":53144328,\"speed\":2,\"paused\":true,\"local_player_id\":0,"
    "\"map_ready\":true,\"has_played_character\":true,\"played_character_id\":" +
    std::to_string(actor) + ",\"played_character_alive\":true}";
}
std::string RequestJson(Action action, std::string_view id = "rite-create-request-01",
                        std::int32_t actor = 36423, std::uint32_t rite = 47) {
  const std::string lease = action == Action::query ? "0" : "18446744073709551615";
  return std::string("{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"") +
    std::string(id) + "\",\"step\":\"" + g::kRiteCreateStep267V1 +
    "\",\"expected_revision\":0,\"arguments\":{},\"rite_create\":{\"schema\":\"" +
    g::kRiteCreateRequestSchema267V1 + "\",\"game_version\":\"" + g::kGameVersion +
    "\",\"executable_sha256\":\"" + g::kExecutableSha256 + "\",\"adapter_id\":\"" +
    g::kAdapterId + "\",\"backend\":\"" + g::kRiteCreateBackend267V1 +
    "\",\"action\":\"" + ActionText(action) + "\",\"expected_core\":" + CoreJson(actor) +
    ",\"expected_source_rite_id\":" + std::to_string(rite) +
    ",\"provider_generation\":\"" + lease + "\",\"query_sequence\":\"" + lease +
    "\"},\"core_control_deadline_unix_ms\":18446744073709551615}";
}

Source Draft(std::int32_t actor = 36423, std::uint32_t rite = 47) {
  Source source{};
  source.phase = Phase::draft; source.actor_id = actor; source.source_rite_id = rite;
  source.draft.emplace();
  auto& draft = *source.draft;
  draft.is_creating = draft.native_can_create = true;
  draft.piety_cost_raw = 123456;
  draft.piety_missing_raw = -7;
  draft.known_dynastic = draft.selected_dynastic = true;
  draft.create_button_found = draft.create_button_visible = draft.create_button_enabled = true;
  draft.blocked_by_unrelated_modal = false;
  draft.create_admissible = true;
  return source;
}
Source Confirmation(std::int32_t actor = 36423, std::uint32_t rite = 47) {
  Source source{};
  source.phase = Phase::confirmation; source.actor_id = actor; source.source_rite_id = rite;
  source.confirmation.emplace();
  auto& modal = *source.confirmation;
  modal.modal_found = modal.native_can_accept = true;
  modal.accept_button_visible = modal.accept_button_enabled = true;
  modal.original_create_bound = modal.accept_admissible = true;
  return source;
}
Result Available(Action action = Action::query, std::int32_t actor = 36423,
                 std::uint32_t rite = 47) {
  Result result{};
  result.action = action; result.status = Status::available;
  result.source_available = result.cleanup_known = result.facts_available = true;
  result.provider_generation = result.query_sequence = U64MAX;
  result.connection_generation = result.ticket_sequence = result.pump_epoch = U64MAX;
  result.thread_id = (std::numeric_limits<std::uint32_t>::max)();
  result.facts = Core(actor);
  result.source = action == Action::query_confirmation ? Confirmation(actor, rite) : Draft(actor, rite);
  return result;
}
Result Dispatched(Action action) {
  auto result = Available(action == Action::create ? Action::query : Action::query_confirmation);
  result.action = action;
  result.status = action == Action::create ? Status::create_dispatched : Status::confirmation_dispatched;
  result.claim_sequence = U64MAX;
  result.effect_attempted = result.native_returned = true;
  result.native_handled = false; // Actual native methods return void.
  return result;
}
Result Refusal(Action action, Status status) {
  Result result{};
  result.action = action; result.status = status;
  result.reason = "nogame_typed_refusal";
  result.cleanup_known = status != Status::indeterminate;
  // A parsed rejection/pending may echo the original Create query lease. It does
  // not grant a new Source, claim, or permission by doing so.
  if (action != Action::query) result.provider_generation = result.query_sequence = U64MAX;
  return result;
}
std::string Wire(const Result& result, std::string_view id = "rite-create-result-01") {
  return g::SerializeRiteCreateResult267V1(id, result);
}
void NoBusinessCredit(const std::string& wire) {
  for (const auto part : {"\"addresses_redacted\":true", "\"rite_created\":false",
      "\"initial_binding_confirmed\":false", "\"new_date_observed\":false",
      "\"physical_save_confirmed\":false"})
    Check(Has(wire, part), "wire invented business/date/Save credit");
}
void QueryOnly(const std::string& wire) {
  NoBusinessCredit(wire);
  for (const auto part : {"\"claim_sequence\":\"0\"", "\"effect_attempted\":false",
                         "\"native_returned\":false", "\"native_handled\":false"})
    Check(Has(wire, part), "query acquired effect/claim credit");
}
void AvailableWire(const std::string& wire) {
  Check(Has(wire, "\"ok\":true") && Has(wire, "\"source_available\":true") &&
      !Has(wire, "\"source\":null") && Has(wire, "\"unavailable_reason\":null"),
      "complete actual DATA source was rejected");
  NoBusinessCredit(wire);
}
void NoSourceWire(const std::string& wire) {
  Check(Has(wire, "\"ok\":false") && Has(wire, "\"source_available\":false") &&
      Has(wire, "\"source\":null") && !Has(wire, "\"unavailable_reason\":null"),
      "invalid/partial/refused source remained usable");
  NoBusinessCredit(wire);
}

void FourActionsAndLeaseShape() {
  for (const auto action : {Action::query, Action::create, Action::query_confirmation,
                            Action::accept_confirmation}) {
    Request parsed{};
    const auto request = RequestJson(action);
    Check(g::ParseRiteCreateRequest267V1(request, parsed), "canonical fixed action rejected");
    Check(parsed.action == action && parsed.expected_source_rite_id == 47 &&
      parsed.id() == "rite-create-request-01" && parsed.deadline_unix_ms == U64MAX &&
      parsed.expected.played_character_id == 36423 && g::RiteCreateRequestShape267V1(parsed),
      "parser changed actual request DATA");
    Check(parsed.provider_generation == (action == Action::query ? 0 : U64MAX) &&
      parsed.query_sequence == (action == Action::query ? 0 : U64MAX), "request lease changed");
    const auto invalid = action == Action::query ?
      Replace(request, "\"provider_generation\":\"0\"", "\"provider_generation\":\"1\"") :
      Replace(request, "\"query_sequence\":\"18446744073709551615\"", "\"query_sequence\":\"0\"");
    Check(!g::ParseRiteCreateRequest267V1(invalid, parsed), "query/action lease distinction lost");
  }
  auto request = RequestJson(Action::query);
  Request parsed{};
  Check(!g::ParseRiteCreateRequest267V1(Replace(request, "\"query_sequence\":\"0\"",
    "\"query_sequence\":\"1\""), parsed), "query accepted positive sequence");
}

void PackedActorsAndUnsignedRiteIds() {
  for (const std::int32_t actor : {0, -2, (std::numeric_limits<std::int32_t>::min)(),
                                   (std::numeric_limits<std::int32_t>::max)()}) {
    for (const std::uint32_t rite : {0U, 47U, 4294967294U}) {
      Request parsed{};
      Check(g::ParseRiteCreateRequest267V1(RequestJson(Action::query, "packed", actor, rite), parsed),
          "valid packed actor/sourceRite boundary rejected");
      Check(parsed.expected.played_character_id == actor && parsed.expected_source_rite_id == rite,
          "packed actor or unsigned source Rite changed");
    }
  }
  Request parsed{};
  Check(!g::ParseRiteCreateRequest267V1(RequestJson(Action::query, "invalid", -1), parsed),
      "invalid packed actor -1 accepted");
  Check(!g::ParseRiteCreateRequest267V1(RequestJson(Action::query, "invalid", 0, 0xFFFFFFFFU), parsed),
      "invalid Rite FFFFFFFF accepted");
  for (const auto value : {"-1", "4294967296", "47.0", "true", "\"47\""})
    Check(!g::ParseRiteCreateRequest267V1(Replace(RequestJson(Action::query),
      "\"expected_source_rite_id\":47", "\"expected_source_rite_id\":" + std::string(value)), parsed),
      "source Rite is not an exact uint32 JSON integer");
}

void DuplicateUnknownAndCallerSelectorsFail() {
  const auto request = RequestJson(Action::create);
  std::vector<std::string> invalid{
    Replace(request, "\"protocol_version\":1", "\"protocol_version\":1,\"protocol_version\":1"),
    Replace(request, "\"action\":\"create\"", "\"action\":\"create\",\"action\":\"create\""),
    Replace(request, "\"paused\":true", "\"paused\":true,\"paused\":true"),
    Replace(request, "\"type\":", "\"caller_permission\":true,\"type\":"),
    Replace(request, "\"action\":", "\"native_can_create\":true,\"action\":"),
    Replace(request, "\"expected_core\":", "\"actor\":36423,\"expected_core\":"),
    Replace(request, "\"expected_core\":", "\"key\":\"create_faith\",\"expected_core\":"),
    Replace(request, "\"arguments\":{}", "\"arguments\":{\"ordinal\":0}"),
    Replace(request, "\"create\"", "\"confirm_edit\""),
    Replace(request, "\"expected_revision\":0", "\"expected_revision\":1"),
    Replace(request, "\"protocol_version\":1", "\"protocol_version\":2"),
    Replace(request, ",\"played_character_alive\":true", ""),
    Replace(request, ",\"expected_source_rite_id\":47", ""),
  };
  for (const auto& wire : invalid) {
    Request out{}; out.request_id_size = 1; out.request_id[0] = 'x';
    Check(!g::ParseRiteCreateRequest267V1(wire, out), "unknown/duplicate/caller field accepted");
    Check(out.id().empty() && out.deadline_unix_ms == 0 &&
      out.expected.played_character_id == -1 && out.expected_source_rite_id == 0xFFFFFFFFU,
      "failed parser preserved old request authority");
  }
}

void CanonicalIntegersIdentityAndCoreShape() {
  const auto request = RequestJson(Action::create);
  std::vector<std::string> invalid{
    RequestJson(Action::query, ""), RequestJson(Action::query, "bad/id"),
    RequestJson(Action::query, std::string(97, 'a')),
    Replace(request, "\"provider_generation\":\"18446744073709551615\"", "\"provider_generation\":18446744073709551615"),
    Replace(request, "\"provider_generation\":\"18446744073709551615\"", "\"provider_generation\":\"01\""),
    Replace(request, "\"query_sequence\":\"18446744073709551615\"", "\"query_sequence\":\"+1\""),
    Replace(request, "\"query_sequence\":\"18446744073709551615\"", "\"query_sequence\":\"18446744073709551616\""),
    Replace(request, "\"core_control_deadline_unix_ms\":18446744073709551615", "\"core_control_deadline_unix_ms\":\"18446744073709551615\""),
    Replace(request, "\"core_control_deadline_unix_ms\":18446744073709551615", "\"core_control_deadline_unix_ms\":0"),
    Replace(request, "\"core_control_deadline_unix_ms\":18446744073709551615", "\"core_control_deadline_unix_ms\":18446744073709551616"),
    Replace(request, "\"speed\":2", "\"speed\":0"),
    Replace(request, "\"speed\":2", "\"speed\":6"),
    Replace(request, "\"paused\":true", "\"paused\":false"),
    Replace(request, "\"local_player_id\":0", "\"local_player_id\":-1"),
    Replace(request, "\"map_ready\":true", "\"map_ready\":false"),
    Replace(request, "\"has_played_character\":true", "\"has_played_character\":false"),
    Replace(request, "\"played_character_alive\":true", "\"played_character_alive\":false"),
    Replace(request, "53144328", "053144328"),
    Replace(request, g::kGameVersion, "1.20.0.4"),
    Replace(request, g::kRiteCreateBackend267V1, "wrong-backend"),
    Replace(request, g::kRiteCreateStep267V1, "current-rite-edit-v1"),
    request + " trailing",
    std::string(16385, ' '),
  };
  Request parsed{};
  for (const auto& wire : invalid)
    Check(!g::ParseRiteCreateRequest267V1(wire, parsed), "noncanonical/old identity/Core accepted");
}

void DraftFalseDataAndSignedRawAreRetained() {
  auto result = Available();
  auto& draft = *result.source->draft;
  draft.native_can_create = draft.create_admissible = false;
  draft.piety_cost_raw = (std::numeric_limits<std::int64_t>::max)();
  draft.piety_missing_raw = (std::numeric_limits<std::int64_t>::min)();
  const auto wire = Wire(result);
  AvailableWire(wire); QueryOnly(wire);
  Check(Has(wire, "\"phase\":\"draft\"") && Has(wire, "\"confirmation\":null") &&
    Has(wire, "\"native_can_create\":false") &&
    Has(wire, "\"piety_cost_raw\":\"9223372036854775807\"") &&
    Has(wire, "\"piety_missing_raw\":\"-9223372036854775808\""),
    "false nativeCan or signed raw values changed");
  auto not_creating = Available();
  not_creating.source->draft->is_creating = false;
  not_creating.source->draft->create_admissible = false;
  AvailableWire(Wire(not_creating));
  Check(Has(Wire(not_creating), "\"is_creating\":false"), "creating=false was fabricated as missing");
  auto one_way = Available(); one_way.source->draft->create_admissible = false;
  AvailableWire(Wire(one_way));
  Check(Has(Wire(one_way), "\"create_admissible\":false"), "admissibility implication was reversed");
}

void ResultPackedIdsAndSourceUnion() {
  for (const std::int32_t actor : {0, -2}) {
    const auto result = Available(Action::query, actor, 0);
    const auto wire = Wire(result);
    AvailableWire(wire); QueryOnly(wire);
    Check(Has(wire, "\"actor_id\":" + std::to_string(actor)) &&
      Has(wire, "\"source_rite_id\":0"), "result packed actor or source Rite0 changed");
  }
  std::vector<Result> invalid;
  auto both = Available(); both.source->confirmation = Confirmation().confirmation; invalid.push_back(both);
  auto absent = Available(); absent.source->draft.reset(); invalid.push_back(absent);
  auto wrong_actor = Available(); wrong_actor.source->actor_id = 37846; invalid.push_back(wrong_actor);
  auto bad_actor = Available(); bad_actor.source->actor_id = -1; invalid.push_back(bad_actor);
  auto bad_rite = Available(); bad_rite.source->source_rite_id = 0xFFFFFFFFU; invalid.push_back(bad_rite);
  auto wrong_phase = Available(); wrong_phase.source->phase = Phase::confirmation; invalid.push_back(wrong_phase);
  auto false_permission = Available(); false_permission.source->draft->native_can_create = false; invalid.push_back(false_permission);
  auto missing_positive = Available(); missing_positive.query_sequence = 0; invalid.push_back(missing_positive);
  for (const auto& result : invalid) NoSourceWire(Wire(result));
}

void CreateVoidDispatchRetainsImmutableDraftAndSpentClaim() {
  const auto result = Dispatched(Action::create);
  const auto wire = Wire(result);
  AvailableWire(wire);
  Check(Has(wire, "\"status\":\"create_dispatched\"") &&
    Has(wire, "\"action\":\"create\"") && Has(wire, "\"phase\":\"draft\"") &&
    Has(wire, "\"claim_sequence\":\"18446744073709551615\"") &&
    Has(wire, "\"provider_generation\":\"18446744073709551615\"") &&
    Has(wire, "\"query_sequence\":\"18446744073709551615\"") &&
    Has(wire, "\"effect_attempted\":true") && Has(wire, "\"native_returned\":true") &&
    Has(wire, "\"native_handled\":false"), "void Create ACK lost beforeSource/lease/claim");
  auto zero_claim = result; zero_claim.claim_sequence = 0; NoSourceWire(Wire(zero_claim));
  auto no_entry = result; no_entry.effect_attempted = false; NoSourceWire(Wire(no_entry));
  auto no_return = result; no_return.native_returned = false; NoSourceWire(Wire(no_return));
  auto wrong_source = result; wrong_source.source = Confirmation(); NoSourceWire(Wire(wrong_source));
}

void ConfirmationFalseCanAndOriginalAssociation() {
  auto result = Available(Action::query_confirmation);
  result.source->confirmation->native_can_accept = false;
  result.source->confirmation->accept_admissible = false;
  const auto wire = Wire(result);
  AvailableWire(wire); QueryOnly(wire);
  Check(Has(wire, "\"phase\":\"confirmation\"") && Has(wire, "\"draft\":null") &&
    Has(wire, "\"original_create_bound\":true") && Has(wire, "\"native_can_accept\":false"),
    "actual bound confirmation with nativeCan=false was fabricated unavailable");
  auto one_way = Available(Action::query_confirmation);
  one_way.source->confirmation->accept_admissible = false; AvailableWire(Wire(one_way));
  auto no_bound = result; no_bound.source->confirmation->original_create_bound = false;
  NoSourceWire(Wire(no_bound));
  auto no_modal = result; no_modal.source->confirmation->modal_found = false;
  NoSourceWire(Wire(no_modal));
  auto bad_gate = Available(Action::query_confirmation);
  bad_gate.source->confirmation->accept_button_enabled = false; NoSourceWire(Wire(bad_gate));
}

void AcceptVoidDispatchRetainsConfirmationAndNoCreationCredit() {
  const auto result = Dispatched(Action::accept_confirmation);
  const auto wire = Wire(result);
  AvailableWire(wire);
  Check(Has(wire, "\"status\":\"confirmation_dispatched\"") &&
    Has(wire, "\"action\":\"accept_confirmation\"") &&
    Has(wire, "\"phase\":\"confirmation\"") &&
    Has(wire, "\"original_create_bound\":true") &&
    Has(wire, "\"native_handled\":false") && Has(wire, "\"native_returned\":true") &&
    Has(wire, "\"effect_attempted\":true") && Has(wire, "\"claim_sequence\":\"18446744073709551615\""),
    "void final acceptance lost actual confirmation beforeSource/spent claim");
  auto draft = result; draft.source = Draft(); NoSourceWire(Wire(draft));
  auto wrong_status = result; wrong_status.status = Status::create_dispatched;
  NoSourceWire(Wire(wrong_status));
}

void PendingAndTypedRefusalsDoNotMintSource() {
  const auto pending = Wire(Refusal(Action::query_confirmation, Status::confirmation_pending));
  NoSourceWire(pending); QueryOnly(pending);
  Check(Has(pending, "\"status\":\"confirmation_pending\""), "clean finite pending changed status");
  for (const auto status : {Status::unavailable, Status::expired, Status::stale_source,
                           Status::claim_consumed, Status::prerequisite_rejected}) {
    auto refusal = Refusal(Action::create, status);
    if (status == Status::claim_consumed) refusal.claim_sequence = 17;
    const auto wire = Wire(refusal);
    NoSourceWire(wire); NoBusinessCredit(wire);
    Check(Has(wire, "\"effect_attempted\":false") && Has(wire, "\"native_returned\":false"),
      "typed early refusal acquired a new callback entry/return");
  }
}

void CleanupUnknownAndPartialCustodyFailClosed() {
  auto unknown = Dispatched(Action::create);
  unknown.cleanup_known = false;
  const auto wire = Wire(unknown);
  NoSourceWire(wire);
  Check(Has(wire, "\"status\":\"indeterminate\"") && Has(wire, "\"cleanup_known\":false"),
      "cleanup unknown was rewritten known or retained usable Source");
  std::vector<Result> partial;
  auto absent = Available(); absent.source.reset(); partial.push_back(absent);
  auto no_flag = Available(); no_flag.source_available = false; partial.push_back(no_flag);
  auto no_facts = Available(); no_facts.facts_available = false; partial.push_back(no_facts);
  auto no_connection = Available(); no_connection.connection_generation = 0; partial.push_back(no_connection);
  auto no_ticket = Available(); no_ticket.ticket_sequence = 0; partial.push_back(no_ticket);
  auto no_pump = Available(); no_pump.pump_epoch = 0; partial.push_back(no_pump);
  auto no_thread = Available(); no_thread.thread_id = 0; partial.push_back(no_thread);
  for (const auto& result : partial) NoSourceWire(Wire(result));
}

void QueryCannotBorrowEffectStateAndActionsCannotBorrowSource() {
  auto query_effect = Available(); query_effect.effect_attempted = true;
  NoSourceWire(Wire(query_effect));
  auto query_claim = Available(); query_claim.claim_sequence = 1;
  NoSourceWire(Wire(query_claim));
  auto wrong_action = Available(); wrong_action.action = Action::accept_confirmation;
  NoSourceWire(Wire(wrong_action));
  auto confirmation_with_draft = Available(Action::query_confirmation);
  confirmation_with_draft.source = Draft(); NoSourceWire(Wire(confirmation_with_draft));
}

void WriteNew(const std::filesystem::path& path, const std::string& bytes) {
  HANDLE file = CreateFileW(path.c_str(), GENERIC_WRITE, 0, nullptr,
                            CREATE_NEW, FILE_ATTRIBUTE_NORMAL, nullptr);
  if (file == INVALID_HANDLE_VALUE) throw std::runtime_error("CREATE_NEW output refused");
  DWORD written = 0;
  const bool valid = bytes.size() <= (std::numeric_limits<DWORD>::max)() &&
    WriteFile(file, bytes.data(), static_cast<DWORD>(bytes.size()), &written, nullptr) &&
    written == bytes.size() && FlushFileBuffers(file);
  CloseHandle(file);
  if (!valid) throw std::runtime_error("full original output write failed");
}
void Emit(const std::filesystem::path& root) {
  if (!CreateDirectoryW(root.c_str(), nullptr))
    throw std::runtime_error("emit root must be a NEW directory");
  std::vector<std::pair<std::string, Result>> samples;
  auto can_false = Available(); can_false.source->draft->native_can_create = false;
  can_false.source->draft->create_admissible = false;
  samples.emplace_back("draft-native-can-false", can_false);
  auto creating_false = Available(); creating_false.source->draft->is_creating = false;
  creating_false.source->draft->create_admissible = false;
  samples.emplace_back("draft-is-creating-false", creating_false);
  samples.emplace_back("draft-actor-zero", Available(Action::query, 0, 0));
  samples.emplace_back("draft-actor-minus-two", Available(Action::query, -2));
  samples.emplace_back("draft-ready", Available());
  samples.emplace_back("create-dispatched", Dispatched(Action::create));
  auto accept_false = Available(Action::query_confirmation);
  accept_false.source->confirmation->native_can_accept = false;
  accept_false.source->confirmation->accept_admissible = false;
  samples.emplace_back("confirmation-native-can-false", accept_false);
  samples.emplace_back("confirmation-ready", Available(Action::query_confirmation));
  samples.emplace_back("accept-dispatched", Dispatched(Action::accept_confirmation));
  samples.emplace_back("confirmation-pending", Refusal(Action::query_confirmation, Status::confirmation_pending));
  samples.emplace_back("expired", Refusal(Action::create, Status::expired));
  samples.emplace_back("stale-source", Refusal(Action::create, Status::stale_source));
  auto cleanup_unknown = Dispatched(Action::create); cleanup_unknown.cleanup_known = false;
  samples.emplace_back("cleanup-unknown", cleanup_unknown);
  samples.emplace_back("unavailable", Refusal(Action::query, Status::unavailable));
  for (const auto& [name, result] : samples)
    WriteNew(root / (name + ".json"), Wire(result, "rite-create-original-result-" + name) + "\n");
  for (const auto action : {Action::query, Action::create, Action::query_confirmation,
                            Action::accept_confirmation}) {
    const auto name = std::string(ActionText(action));
    WriteNew(root / ("request-" + name + ".json"),
      RequestJson(action, "rite-create-original-request-" + name) + "\n");
  }
}
int ValidateOriginal(const std::filesystem::path& path) {
  std::ifstream file(path, std::ios::binary);
  if (!file) throw std::runtime_error("cannot open original request");
  std::string body;
  body.reserve(16385);
  char byte = 0;
  while (body.size() <= 16384 && file.get(byte)) body += byte;
  Request parsed{};
  const bool valid = body.size() <= 16384 && g::ParseRiteCreateRequest267V1(body, parsed);
  std::cout << (valid ? "VALID\n" : "INVALID\n");
  return valid ? 0 : 2;
}
}

int main(int argc, char** argv) {
  try {
    if (argc == 3 && std::string_view(argv[1]) == "--validate-request")
      return ValidateOriginal(std::filesystem::path(argv[2]));
    if (argc != 1 && !(argc == 3 && std::string_view(argv[1]) == "--emit-json"))
      throw std::runtime_error("usage: test [--emit-json NEWDIR | --validate-request ORIGINAL_BODY]");
    unsigned groups = 0;
    const auto test = [&](const char* name, auto body) {
      body(); ++groups; std::cout << "PASS " << name << '\n';
    };
    test("four_actions_and_private_lease_shape", FourActionsAndLeaseShape);
    test("packed_actor_and_unsigned_rite", PackedActorsAndUnsignedRiteIds);
    test("strict_keys_and_no_caller_authority", DuplicateUnknownAndCallerSelectorsFail);
    test("canonical_numbers_identity_core", CanonicalIntegersIdentityAndCoreShape);
    test("draft_false_data_and_signed_raw", DraftFalseDataAndSignedRawAreRetained);
    test("result_identity_and_strict_source_union", ResultPackedIdsAndSourceUnion);
    test("create_void_ack_before_source", CreateVoidDispatchRetainsImmutableDraftAndSpentClaim);
    test("bound_confirmation_false_data", ConfirmationFalseCanAndOriginalAssociation);
    test("accept_void_ack_not_business", AcceptVoidDispatchRetainsConfirmationAndNoCreationCredit);
    test("finite_pending_and_refusals", PendingAndTypedRefusalsDoNotMintSource);
    test("unknown_and_partial_custody", CleanupUnknownAndPartialCustodyFailClosed);
    test("no_cross_phase_effect_authority", QueryCannotBorrowEffectStateAndActionsCannotBorrowSource);
    if (argc == 3) Emit(std::filesystem::path(argv[2]));
    std::cout << "NoGame groups=" << groups << " checks=" << checks
              << "; live ABI/runtime qualification=false\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
