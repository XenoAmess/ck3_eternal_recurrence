// Thin offline regression: production profile parser and Army serializers,
// with typed owned journal readers. No CK3, hooks, memory readers, or pipe.
#include "xar_bridge/army_strengths_manager_shared_wire_v1.hpp"

#include <array>
#include <cstdlib>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>

#if defined(XAR_ENABLE_ARMY_OBSERVED_PHASE_QUERY_12004)
// Keep the production non-inline journal serializer in this single test TU.
#include "../src/army_natural_phase_json_12004.cpp"
#endif

namespace army_profile_fixture {
constexpr std::uint32_t kArmyFullId = 0x81000021U;
constexpr std::uintptr_t kPrimary = 0x123400U;
std::array<unsigned, 9> phase_reads{};
std::array<unsigned, 5> other_reads{};
unsigned assertions = 0;

constexpr std::array<std::string_view, 9> kPhaseKeys = {
    "actual_army_daily_assault_preparation_observations_v1",
    "actual_army_assault_placement_observations_v1",
    "army_natural_phase_observations_v1",
    "actual_army_regular_core_observations_v1",
    "army_actual_assault_consumer_observations_v1",
    "actual_army_assault_group_release_observations_v1",
    "native_gathering_due_natural_stage_12004",
    "actual_army_cleanup_observations_v1",
    "actual_army_pre_date_prefix_observations_v1",
};

void Require(bool condition, std::string_view message) {
  ++assertions;
  if (!condition) throw std::runtime_error(std::string(message));
}

void JsonString(std::string &out, std::string_view text) {
  constexpr char hex[] = "0123456789abcdef";
  out += '"';
  for (const auto raw : text) {
    const auto c = static_cast<unsigned char>(raw);
    if (c == '"' || c == '\\') { out += '\\'; out += raw; }
    else if (c < 0x20U) {
      out += "\\u00"; out += hex[c >> 4U]; out += hex[c & 15U];
    } else out += raw;
  }
  out += '"';
}

const auto Number = [](auto value) { return std::to_string(value); };
const auto Int32Array = [](std::string &out, const auto &values) {
  out += '[';
  bool first = true;
  for (const auto value : values) {
    if (!first) out += ',';
    first = false;
    out += std::to_string(value);
  }
  out += ']';
};

// Locate raw values in the generated top-level object. This test reader never
// constructs or modifies wire data, and distinguishes an absent key from null.
std::optional<std::string_view> Member(std::string_view object,
                                     std::string_view wanted) {
  Require(!object.empty() && object.front() == '{' && object.back() == '}',
          "serializer must return an object");
  std::size_t i = 1;
  while (i < object.size() - 1) {
    Require(object[i] == '"', "generated object key must be quoted");
    const auto key_start = ++i;
    while (i < object.size() && object[i] != '"') ++i;
    Require(i + 1 < object.size() && object[i + 1] == ':',
            "generated object key needs a colon");
    const auto key = object.substr(key_start, i - key_start);
    i += 2;
    const auto value_start = i;
    unsigned nesting = 0;
    bool quoted = false, escaped = false;
    while (i < object.size()) {
      const char c = object[i];
      if (quoted) {
        if (escaped) escaped = false;
        else if (c == '\\') escaped = true;
        else if (c == '"') quoted = false;
      } else if (c == '"') quoted = true;
      else if (c == '[' || c == '{') ++nesting;
      else if (c == ']' || c == '}') {
        if (nesting == 0) break;
        --nesting;
      } else if (c == ',' && nesting == 0) break;
      ++i;
    }
    Require(!quoted && nesting == 0, "generated value must be complete");
    if (key == wanted) return object.substr(value_start, i - value_start);
    if (i < object.size() && object[i] == ',') ++i;
  }
  return std::nullopt;
}

xar::game::ArmyStrengthSnapshot Strength() {
  xar::game::ArmyStrengthSnapshot value{};
  value.available = true;
  value.army_id = 18;
  value.native_carmy_id_observable = true;
  value.native_carmy_id = static_cast<std::int32_t>(kArmyFullId);
  value.scope_role = xar::game::ArmyStrengthScopeRole::player;
  value.war_ids = {71, 71, 73};
  value.regiment_count = 1;
  value.current_soldiers = 160;
  value.maximum_soldiers = 200;
  value.ai_base_power_raw = 18000000;
  value.current_supply_raw = 0;
  value.regiment_strengths = std::vector<xar::game::ArmyRegimentStrengthSnapshot>{
      {.army_regiment_id = 41, .current_soldiers = 160, .maximum_soldiers = 200}};
  value.regiment_replenishment_records_v1.emplace();
  value.scoped_ordered_refill_inputs_v1.emplace();
  value.next_route_replenishment_position_inputs_v1.emplace();
  value.gathering_days_status = xar::game::ArmyGatheringDaysStatus::not_gathering;
  return value;
}

std::string Row(const xar::game::ArmyStrengthSnapshot &strength, bool history) {
  std::string out;
  xar::game::AppendArmyStrengthV1WithManagerInputsMode(
      out, strength, Number, Int32Array, JsonString,
      xar::game::ArmyStrengthManagerInputsModeV1::inline_values, history);
  return out;
}

std::string LegacyRow(const xar::game::ArmyStrengthSnapshot &strength) {
  std::string out;
  xar::game::AppendArmyStrengthV1(out, strength, Number, Int32Array, JsonString);
  return out;
}

#if defined(XAR_ENABLE_ARMY_OBSERVED_PHASE_QUERY_12004)
// A controlled wire input, not a sampling controller. Queries never populate it.
std::optional<std::vector<xar::ck3_12004::ArmyGatheringDueNaturalStage12004>>
    gathering_wire_fixture;

std::vector<xar::ck3_12004::ArmyNaturalPhaseRecord12004> NaturalRecords() {
  std::vector<xar::ck3_12004::ArmyNaturalPhaseRecord12004> records(2);
  for (std::size_t i = 0; i < records.size(); ++i) {
    auto &record = records[i];
    record.scope.observed = true;
    record.scope.primary_manager_identity = kPrimary;
    record.scope.original_army_roster.ordered_full_ids = {kArmyFullId, kArmyFullId};
    record.scope.original_army_roster.complete = true;
    record.original_called = record.original_returned = true;
    record.raw_return_bits = 1234501 + i;
  }
  return records;
}

std::vector<xar::ck3_12004::ArmyGatheringDueNaturalStage12004> GatheringRecords() {
  std::vector<xar::ck3_12004::ArmyGatheringDueNaturalStage12004> records(3);
  for (std::size_t i = 0; i < records.size(); ++i) {
    auto &record = records[i];
    record.observed = record.original_called = record.original_returned = true;
    record.raw_return_bits = 2345601 + i;
    record.entry.queue158.ordered_full_ids = {kArmyFullId, kArmyFullId};
    record.entry.missing_fields = {"first_retained_marker", "last_retained_marker"};
    record.returned.entry_queue_extent_backing_full_ids = {99, 99, 101};
  }
  return records;
}
#endif

void ParserCases() {
  using namespace xar::game;
  using P = ArmyStrengthQueryProfileV1;
  const std::array<std::pair<std::string_view, P>, 23> cases = {{
      {R"({})", P::legacy_full},
      {R"({"step":"query-army-strengths-v1"})", P::legacy_full},
      {R"({"army_strengths_profile":"ordinary_core_v1"})", P::ordinary_core},
      {R"({ "army_strengths_profile" : "observed_history_full_v1" })", P::observed_history_full},
      {R"({"army_strengths_profile":null})", P::invalid},
      {R"({"army_strengths_profile":false})", P::invalid},
      {R"({"army_strengths_profile":1})", P::invalid},
      {R"({"army_strengths_profile":[]})", P::invalid},
      {R"({"army_strengths_profile":{}})", P::invalid},
      {R"({"army_strengths_profile":""})", P::invalid},
      {R"({"army_strengths_profile":"ordinary_core_v2"})", P::invalid},
      {R"({"army_strengths_profile":" ordinary_core_v1"})", P::invalid},
      {R"({"army_strengths_profile":"ordinary_core_v1","army_strengths_profile":"ordinary_core_v1"})", P::invalid},
      {R"({"army_strengths_profile":null,"army_strengths_profile":"observed_history_full_v1"})", P::invalid},
      {R"({"nested":{"army_strengths_profile":"ordinary_core_v1"}})", P::legacy_full},
      {R"({"note":"\"army_strengths_profile\":\"ordinary_core_v1\""})", P::legacy_full},
      {R"({"other":[true,false,null,-1.2e+3,{"key":"value"}],"army_strengths_profile":"ordinary_core_v1"})", P::ordinary_core},
      {R"({"army_strengths_\u0070rofile":"ordinary_core_v1"})", P::ordinary_core},
      {R"({"army_strengths_profile":"ordinary_\u0063ore_v1"})", P::ordinary_core},
      {R"({"army_strengths_profile":"ordinary_core_v1","army_strengths_\u0070rofile":"ordinary_core_v1"})", P::invalid},
      {R"({"army_strengths_profile":"ordinary_core_v1",})", P::invalid},
      {R"({"army_strengths_profile":"ordinary_core_v1"} {})", P::invalid},
      {R"(["ordinary_core_v1"])", P::invalid},
  }};
  for (const auto &[wire, expected] : cases)
    Require(ParseArmyStrengthQueryProfileV1(wire) == expected,
            std::string("profile parser mismatch: ") + std::string(wire));
  Require(ArmyStrengthQueryProfileAvailableV1(P::legacy_full), "legacy must remain available");
  Require(ArmyStrengthQueryProfileAvailableV1(P::ordinary_core), "core must be available");
  Require(!ArmyStrengthQueryProfileAvailableV1(P::invalid), "invalid must fail closed");
  Require(!ArmyStrengthQueryProfileIncludesObservedHistoryV1(P::ordinary_core), "core must skip phase history");
  Require(ArmyStrengthQueryProfileIncludesObservedHistoryV1(P::legacy_full), "legacy must retain phase history request");
  Require(ArmyStrengthQueryProfileIncludesObservedHistoryV1(P::observed_history_full), "full must retain phase history request");
  Require(ArmyStrengthQueryProfileNameV1(P::ordinary_core) == "ordinary_core_v1", "core echo must be exact");
  Require(ArmyStrengthQueryProfileNameV1(P::observed_history_full) == "observed_history_full_v1", "full echo must be exact");
#if defined(XAR_ENABLE_ARMY_OBSERVED_PHASE_QUERY_12004)
  Require(ArmyStrengthQueryProfileAvailableV1(P::observed_history_full), "macro-on full must be available");
#else
  Require(!ArmyStrengthQueryProfileAvailableV1(P::observed_history_full), "macro-off explicit full must fail closed");
#endif
}

void TransportLimitCases() {
  using namespace xar::game;
  constexpr std::array<char, 8> tiny_payload{};
  constexpr std::size_t tiny_limit = 7;
  Require(!ArmyStrengthQueryReplyExceedsTransportLimitV1(0, tiny_limit),
          "empty payload must not exceed the limit");
  Require(!ArmyStrengthQueryReplyExceedsTransportLimitV1(tiny_limit - 1, tiny_limit),
          "below-limit payload must be admitted");
  Require(!ArmyStrengthQueryReplyExceedsTransportLimitV1(tiny_limit, tiny_limit),
          "exact-limit payload must be admitted");
  Require(ArmyStrengthQueryReplyExceedsTransportLimitV1(tiny_payload.size(), tiny_limit),
          "limit plus one must be rejected before the transport write");
  Require(ArmyStrengthQueryReplySizeLimitErrorV1(
              ArmyStrengthQueryProfileV1::ordinary_core, tiny_payload.size(), tiny_limit) ==
              "payload_exceeds_transport_limit requested_profile=ordinary_core_v1 actual_bytes=8 limit_bytes=7",
          "size rejection must bind the actual bytes and requested core profile");
  Require(ArmyStrengthQueryReplySizeLimitErrorV1(
              ArmyStrengthQueryProfileV1::observed_history_full, 9, tiny_limit) ==
              "payload_exceeds_transport_limit requested_profile=observed_history_full_v1 actual_bytes=9 limit_bytes=7",
          "full-profile size rejection must stay an explicit rejection");
}

void SerializerCases() {
  const auto strength = Strength();
#if defined(XAR_ENABLE_ARMY_OBSERVED_PHASE_QUERY_12004)
  // Explicit input for the original row comparison; do not enable a sampler.
  gathering_wire_fixture = GatheringRecords();
#endif
  phase_reads.fill(0);
  const auto core = Row(strength,
      xar::game::ArmyStrengthQueryProfileIncludesObservedHistoryV1(
          xar::game::ArmyStrengthQueryProfileV1::ordinary_core));
  for (auto count : phase_reads) Require(count == 0, "core invoked a phase-history reader");
  for (const auto key : kPhaseKeys)
    Require(!Member(core, key), "core must omit phase key, not synthesize null");
  Require(Member(core, "current_supply_raw") == "0", "observed zero must remain zero");
  Require(Member(core, "unavailable_reason") == "null", "available core reason must remain null");
  Require(Member(core, "war_ids") == "[71,71,73]", "war occurrence order must survive");

  phase_reads.fill(0);
  const auto full = Row(strength,
      xar::game::ArmyStrengthQueryProfileIncludesObservedHistoryV1(
          xar::game::ArmyStrengthQueryProfileV1::observed_history_full));
  Require(LegacyRow(strength) == full, "legacy wrapper must retain full inline bytes");
  constexpr std::array<std::string_view, 16> retained = {
      "status", "army_id", "native_carmy_id", "scope_role", "war_ids",
      "regiment_count", "current_soldiers", "maximum_soldiers",
      "ai_base_power_raw", "ai_base_power_scale", "unavailable_reason",
      "regiment_strengths", "regiment_replenishment_records_v1",
      "scoped_ordered_refill_inputs_v1", "next_route_replenishment_position_inputs_v1",
      "current_supply_raw"};
  for (const auto key : retained)
    Require(Member(core, key) && Member(core, key) == Member(full, key),
            "ordinary business member changed across profiles");
  constexpr std::array<std::string_view, 3> unaffected = {
      "actual_loss_writer_observations_v1", "battle_casualty_observations_v1",
      "actual_supply_callback_observations_v1"};
  for (const auto key : unaffected)
    Require(Member(core, key) && Member(core, key) == Member(full, key),
            "non-phase journal changed across profiles");
  Require(Member(core, "actual_compiled_effect_observations_v1") ==
              Member(full, "actual_compiled_effect_observations_v1"),
          "compiled-effect journal changed across profiles");
#if defined(XAR_CK3_ENABLE_G2_ARMY_LATE_EVENT_OBSERVER_V1)
  Require(Member(core, "actual_army_late_event_observations_v1") &&
              Member(core, "actual_army_late_event_observations_v1") ==
              Member(full, "actual_army_late_event_observations_v1"),
          "late-event journal changed across profiles");
#endif

#if defined(XAR_ENABLE_ARMY_OBSERVED_PHASE_QUERY_12004)
  for (const auto key : kPhaseKeys) Require(Member(full, key).has_value(), "full lost a retained phase key");
  for (auto count : phase_reads) Require(count == 2, "full/legacy must read each phase fixture once");
  Require(Member(full, "actual_army_assault_placement_observations_v1") == "null", "unavailable placement must remain null");
  const auto gathering = Member(full, "native_gathering_due_natural_stage_12004");
  Require(gathering && *gathering == xar::ck3_12004::SerializeArmyGatheringDueNaturalStage12004(GatheringRecords()),
          "full gathering value must retain the complete owned fixture");
  Require(gathering->find("2345601") != std::string_view::npos &&
              gathering->find("2345602") != std::string_view::npos &&
              gathering->find("2345603") != std::string_view::npos &&
              gathering->find("[99,99,101]") != std::string_view::npos,
          "full fixture records and duplicate occurrences must not be capped");
  Require(full.size() > core.size(), "full fixture must exercise a nonempty omitted value");
#else
  for (const auto key : kPhaseKeys) Require(!Member(full, key), "macro-off legacy shape must not invent phase keys");
  Require(full == core, "macro-off core and legacy row bytes must agree");
  Require(Member(full, "actual_compiled_effect_observations_v1") == "null", "compiled macro-off must remain null");
#endif

  auto unresolved = strength;
  unresolved.native_carmy_id_observable = false;
  phase_reads.fill(0);
  const auto unknown_core = Row(unresolved, false);
  Require(Member(unknown_core, "native_carmy_id") == "null", "unread Army ID must remain null");
  for (const auto key : kPhaseKeys) Require(!Member(unknown_core, key), "unread core still omits phase key");
#if defined(XAR_ENABLE_ARMY_OBSERVED_PHASE_QUERY_12004)
  const auto unknown_full = Row(unresolved, true);
  for (const auto key : kPhaseKeys) Require(Member(unknown_full, key) == "null", "unread full phase value must remain null");
#endif
  for (auto count : phase_reads) Require(count == 0, "unresolved identity must not read phase journals");
}

void SamplingCompatibilityCases() {
#if defined(XAR_ENABLE_ARMY_OBSERVED_PHASE_QUERY_12004)
  const auto strength = Strength();
  gathering_wire_fixture.reset();
  const auto unknown = Row(strength, true);
  Require(Member(unknown, "native_gathering_due_natural_stage_12004") == "null" &&
              !gathering_wire_fixture,
          "default unavailable fixture must remain null without query auto-enabling");

  // Exercise the serializer's typed empty-vector input only. The real producer
  // never calls this observed-empty subject history; its no-match result is null.
  gathering_wire_fixture.emplace();
  const auto empty_row = Row(strength, true);
  const auto empty_value = Member(empty_row, "native_gathering_due_natural_stage_12004");
  Require(empty_value && *empty_value != "null" &&
              empty_value->find("\"records\":[]") != std::string_view::npos,
          "explicit typed wire fixture must distinguish a value from null");

  gathering_wire_fixture = GatheringRecords();
  const auto full = Row(strength, true);
  Require(Member(full, "native_gathering_due_natural_stage_12004") ==
              xar::ck3_12004::SerializeArmyGatheringDueNaturalStage12004(*gathering_wire_fixture),
          "sampled-reader wire fixture must retain the complete explicit value");
  phase_reads.fill(0);
  const auto core = Row(strength, false);
  Require(!Member(core, "native_gathering_due_natural_stage_12004") && phase_reads[6] == 0,
          "ordinary profile must omit the sampled family without reading it");
  gathering_wire_fixture.reset();
#else
  Require(false, "sampling compatibility requires the observed-phase macro");
#endif
}
} // namespace army_profile_fixture

// Typed local owned values replace only journal storage access. All wire
// serializers above are the production implementations; no native body runs.
namespace xar::ck3_12004 {
std::optional<game::ArmyActualLossWriterObservationsV1>
ReadActualLossWriterObservations12004(std::span<const std::int32_t> ids) noexcept {
  ++army_profile_fixture::other_reads[0];
  if (ids.size() != 1 || ids.front() != 41) return std::nullopt;
  game::ArmyActualLossWriterObservationsV1 value;
  value.events.resize(2); value.events[0].sequence = 901; value.events[1].sequence = 902;
  return value;
}
std::optional<game::ArmyBattleCasualtyObservationsV1>
ReadBattleCasualtyObservations12004(std::span<const std::int32_t> ids) noexcept {
  ++army_profile_fixture::other_reads[1];
  if (ids.size() != 1 || ids.front() != 41) return std::nullopt;
  game::ArmyBattleCasualtyObservationsV1 value;
  value.events.resize(1); value.events.front().sequence = 903;
  return value;
}
std::optional<game::ArmyActualSupplyCallbackObservationsV1>
ReadActualSupplyCallbackObservations12004(std::int32_t army, std::int32_t full) noexcept {
  ++army_profile_fixture::other_reads[2];
  if (army != 18 || static_cast<std::uint32_t>(full) != army_profile_fixture::kArmyFullId) return std::nullopt;
  game::ArmyActualSupplyCallbackObservationsV1 value;
  value.events.resize(1); value.events.front().sequence = 904;
  return value;
}
#if defined(XAR_CK3_ENABLE_G2_ARMY_LATE_EVENT_OBSERVER_V1)
std::optional<game::ArmyActualLateEventObservationsV1>
ReadActualArmyLateEventObservations12004(std::int32_t) noexcept {
  ++army_profile_fixture::other_reads[3];
  game::ArmyActualLateEventObservationsV1 value;
  value.events.resize(1); value.events.front().sequence = 905;
  return value;
}
#endif
#if defined(XAR_CK3_ENABLE_G2_ARMY_COMPILED_EFFECT_OBSERVER_V1)
std::optional<game::ArmyActualCompiledEffectObservationsV1>
ReadActualArmyCompiledEffectObservationsForArmy12004(std::int32_t) noexcept {
  ++army_profile_fixture::other_reads[4];
  game::ArmyActualCompiledEffectObservationsV1 value;
  value.events.resize(1); value.events.front().sequence = 906;
  return value;
}
#endif
#if defined(XAR_ENABLE_ARMY_OBSERVED_PHASE_QUERY_12004)
std::optional<ActualArmyDailyAssaultPreparationObservations12004>
ReadActualArmyDailyAssaultPreparationObservations12004(std::uint32_t) noexcept {
  ++army_profile_fixture::phase_reads[0];
  return ActualArmyDailyAssaultPreparationObservations12004{};
}
std::optional<ActualArmyAssaultPlacementObservations12004>
ReadActualArmyAssaultPlacementObservations12004(std::uint32_t) noexcept {
  ++army_profile_fixture::phase_reads[1];
  return std::nullopt;
}
ActualArmyAssaultPlacementProjection12004 ProjectActualArmyAssaultPlacementObservation12004(
    const ActualArmyAssaultPlacementObservation12004 &,
    const ActualArmyDailyAssaultPreparationObservation12004 &) {
  // The fixture has no placement event; touching this native projection is a bug.
  std::abort();
}
std::vector<ArmyNaturalPhaseRecord12004> ReadArmyNaturalPhaseJournal12004() {
  ++army_profile_fixture::phase_reads[2];
  return army_profile_fixture::NaturalRecords();
}
ArmyRegularCoreJournal12004 ReadArmyRegularCoreJournal12004() noexcept {
  ++army_profile_fixture::phase_reads[3];
  return {};
}
std::optional<ArmyActualAssaultConsumerObservationsV1>
ReadActualAssaultConsumerObservations12004(std::uint32_t) noexcept {
  ++army_profile_fixture::phase_reads[4];
  return std::nullopt;
}
std::optional<game::ArmyAssaultGroupReleaseObservations12004>
ReadArmyAssaultGroupReleaseObservations12004(std::uint32_t) noexcept {
  ++army_profile_fixture::phase_reads[5];
  return std::nullopt;
}
std::vector<ArmyGatheringDueNaturalStage12004>
ReadArmyGatheringDueNaturalForArmy12004(std::uint32_t) {
  ++army_profile_fixture::phase_reads[6];
  return army_profile_fixture::GatheringRecords();
}
std::optional<std::vector<ArmyGatheringDueNaturalStage12004>>
ReadSampledArmyGatheringDueNaturalForArmy12004(std::uint32_t full_id) {
  ++army_profile_fixture::phase_reads[6];
  if (full_id != army_profile_fixture::kArmyFullId) return std::nullopt;
  return army_profile_fixture::gathering_wire_fixture;
}
ArmyActualMonthfirstCleanupJournal12004 ReadArmyActualMonthfirstCleanupJournal12004() noexcept {
  ++army_profile_fixture::phase_reads[7];
  return {};
}
std::optional<ActualArmyPreDatePrefixObservations12004>
ReadActualArmyPreDatePrefixObservations12004(std::uintptr_t primary) noexcept {
  ++army_profile_fixture::phase_reads[8];
  if (primary != army_profile_fixture::kPrimary) std::abort();
  return std::nullopt;
}
#endif
} // namespace xar::ck3_12004

int main(int argc, char **argv) {
  try {
    const bool compatibility = argc == 2 && std::string_view(argv[1]) == "--sampling-compatibility";
    army_profile_fixture::Require(argc == 1 || compatibility, "unknown focused fixture selection");
    if (compatibility) army_profile_fixture::SamplingCompatibilityCases();
    else {
      army_profile_fixture::ParserCases();
      army_profile_fixture::TransportLimitCases();
      army_profile_fixture::SerializerCases();
    }
    std::cout << "{\"status\":\"passed\",\"assertions\":" << army_profile_fixture::assertions
              << ",\"observed_phase_macro\":"
#if defined(XAR_ENABLE_ARMY_OBSERVED_PHASE_QUERY_12004)
              << "true"
#else
              << "false"
#endif
              << ",\"live_ck3\":false,\"production_serializer\":true}\n";
    return EXIT_SUCCESS;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return EXIT_FAILURE;
  }
}
