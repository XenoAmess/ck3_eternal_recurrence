#include "xar_bridge/prewar_force_coalition12004.hpp"

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_war.hpp"

#include <algorithm>
#include <limits>
#include <optional>
#include <set>
#include <sstream>
#include <string_view>
#include <utility>

namespace xar::ck3_12004 {
namespace {

bool Fail(std::string &failure, std::string_view reason) {
  failure.assign(reason);
  return false;
}

std::string CanonicalDeclarationId(const game::DeclarableWarSnapshot &row) {
  return std::to_string(row.target_character_id) + '-' +
      std::to_string(row.casus_belli_index) + '-' +
      std::to_string(row.configuration_index);
}

struct WarEntryCapture {
  ck3_12002::QueryMailboxEnvelope *envelope = nullptr;
  const PrewarForceCoalitionRequest12004 *request = nullptr;
};

bool ReadSelectedCatalogue(ck3_12002::QueryMailboxEnvelope &envelope,
    const PrewarForceCoalitionRequest12004 &request) noexcept {
  try {
    if (!ck3_12002::IsQueryOwningThread(&envelope) || !envelope.game)
      return false;
    std::vector<game::DeclarableWarSnapshot> rows;
    if (game::ReadDeclarableWarsForTarget(*envelope.game,
            request.selected.target_character_id, rows) !=
        game::ReadDeclarableWarsResult::available)
      return false;
    // Compare the entire choice, including key, claimant and ordered titles.
    return std::count_if(rows.begin(), rows.end(), [&](const auto &row) {
             return CanonicalDeclarationId(row) == request.declaration_id;
           }) == 1 &&
        std::count(rows.begin(), rows.end(), request.selected) == 1;
  } catch (...) { return false; }
}

bool CaptureWarEntry(void *opaque,
    game::WarEntryAssessmentFrameV1 &output) noexcept {
  output = {};
  try {
    auto *capture = static_cast<WarEntryCapture *>(opaque);
    if (!capture || !capture->envelope || !capture->request) return false;
    auto &envelope = *capture->envelope;
    game::Snapshot frame;
    if (!ck3_12002::CaptureQuerySnapshot(&envelope, frame) ||
        !ReadSelectedCatalogue(envelope, *capture->request)) return false;
    output.snapshot_revision = envelope.expected_snapshot_revision;
    output.date_raw = static_cast<std::int32_t>(frame.date_raw);
    output.paused = frame.paused;
    output.map_ready = frame.map_ready;
    output.actor_alive = frame.has_played_character && frame.played_character_alive;
    output.actor_character_id = static_cast<std::int32_t>(frame.played_character_id);
    output.declarable_target_character_ids = {
        capture->request->selected.target_character_id};
    return true;
  } catch (...) { output = {}; return false; }
}

bool OwnsWarEntry(void *opaque) noexcept {
  auto *capture = static_cast<WarEntryCapture *>(opaque);
  return capture && capture->envelope &&
      ck3_12002::IsQueryOwningThread(capture->envelope);
}

std::string Quote(std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  std::string result = "\"";
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') {
      result += '\\'; result += static_cast<char>(c);
    } else if (c < 0x20) {
      result += "\\u00";
      result += hex[c >> 4]; result += hex[c & 0xF];
    } else result += static_cast<char>(c);
  }
  result += '"';
  return result;
}

template <class T> void Nullable(std::ostream &out,
    const std::optional<T> &value) {
  if (value) out << *value;
  else out << "null";
}

void Bool(std::ostream &out, bool value) { out << (value ? "true" : "false"); }

void Ids(std::ostream &out, const std::vector<std::int32_t> &ids) {
  out << '[';
  for (std::size_t i = 0; i < ids.size(); ++i) {
    if (i) out << ',';
    out << ids[i];
  }
  out << ']';
}

void Selected(std::ostream &out, const game::DeclarableWarSnapshot &row) {
  out << "{\"target_character_id\":" << row.target_character_id
      << ",\"casus_belli_index\":" << row.casus_belli_index
      << ",\"casus_belli_key\":" << Quote(row.casus_belli_key)
      << ",\"configuration_index\":" << row.configuration_index
      << ",\"claimant_character_id\":" << row.claimant_character_id
      << ",\"target_title_ids\":";
  Ids(out, row.target_title_ids);
  out << '}';
}

bool CompleteRaisedObservation(const PrewarForceMilitarySnapshot12004 &whole,
    const PrewarForceOwnerMilitary12004 &owner) {
  // This is a native scalar observation, never a physical force lower bound.
  return whole.source_frame_ready && whole.unit_scan_complete &&
      owner.character_identity_ready && owner.raised_scan_complete &&
      std::all_of(owner.raised_armies.begin(), owner.raised_armies.end(),
          [](const auto &army) {
            return army.available && army.current_soldiers &&
                army.maximum_soldiers;
          });
}

} // namespace

bool ReadPrewarForceCoalitionSample12004(
    const PrewarForceCoalitionBindings12004 &bindings,
    const PrewarForceCoalitionRequest12004 &request,
    ck3_12002::QueryMailboxEnvelope &envelope,
    const ck3_12002::MilitaryWorldAccess &world,
    PrewarForceCoalitionSample12004 &output, std::string &failure) noexcept {
  output = {};
  failure.clear();
  try {
    if (!envelope.game || !ck3_12002::IsQueryOwningThread(&envelope) ||
        envelope.snapshot_comparison !=
            ck3_12002::QuerySnapshotComparison12002::full_snapshot ||
        !game::IsCk3_12004Descriptor(envelope.game->descriptor()) ||
        !request.expected_native_revision || !request.expected_public_revision ||
        request.expected_native_revision != envelope.expected_snapshot_revision ||
        request.selected.target_character_id <= 0 ||
        request.selected.casus_belli_index < 0 ||
        request.selected.configuration_index < -1 ||
        request.declaration_id != CanonicalDeclarationId(request.selected))
      return Fail(failure, "prewar_force_current_request_unavailable");
    game::Snapshot before;
    if (!ck3_12002::CaptureQuerySnapshot(&envelope, before) ||
        !before.map_ready || !before.has_played_character ||
        !before.played_character_alive || before.played_character_id <= 0 ||
        before.played_character_id > (std::numeric_limits<std::int32_t>::max)() ||
        before.date_raw < (std::numeric_limits<std::int32_t>::min)() ||
        before.date_raw > (std::numeric_limits<std::int32_t>::max)() ||
        !ReadSelectedCatalogue(envelope, request))
      return Fail(failure, "prewar_force_selected_catalogue_or_frame_unavailable");
    output.selected = request.selected;
    WarEntryCapture capture{&envelope, &request};
    ck3_12002::WarEntryAssessmentAccessV1 access{};
    access.context = &capture;
    access.capture_frame = &CaptureWarEntry;
    access.is_main_thread = &OwnsWarEntry;
    ck3_12002::WarEntryAssessmentsV1Request power_request{};
    power_request.expected_snapshot_revision = request.expected_native_revision;
    power_request.target_character_ids = {request.selected.target_character_id};
    if (ck3_12002::ReadWarEntryAssessmentsV1(bindings.war_entry, access,
            power_request, output.assessment) !=
            game::ReadWarEntryAssessmentsV1Result::available ||
        !output.assessment.available || !output.assessment.readiness.ready ||
        output.assessment.snapshot_revision != request.expected_native_revision ||
        output.assessment.date_raw != before.date_raw ||
        output.assessment.actor_character_id != before.played_character_id ||
        output.assessment.requested_target_character_ids !=
            power_request.target_character_ids ||
        output.assessment.assessments.size() != 1)
      return Fail(failure, "prewar_force_effective_target_unavailable");
    const auto &assessment = output.assessment.assessments.front();
    if (assessment.target_character_id != request.selected.target_character_id ||
        assessment.effective_target_character_id <= 0 ||
        assessment.effective_target_character_id == before.played_character_id)
      return Fail(failure, "prewar_force_effective_target_identity_unavailable");
    output.generic_effective_target_character_id =
        assessment.effective_target_character_id;
    CoreSnapshotPrefix core_frame;
    if (!ck3_12004::ReadCoreSnapshot(bindings.core, core_frame) ||
        !core_frame.clock.paused || !core_frame.map_ready ||
        !core_frame.has_played_character || !core_frame.played_character_alive ||
        core_frame.clock.date_raw != before.date_raw ||
        core_frame.played_character_id != before.played_character_id)
      return Fail(failure, "prewar_force_core_frame_changed");
    const auto actor = static_cast<std::int32_t>(before.played_character_id);
    const std::vector<std::int32_t> roots{
        actor, output.generic_effective_target_character_id};
    std::set<std::int32_t> owners(roots.begin(), roots.end());
    for (const auto owner : roots) {
      PrewarForceCoalitionOwnerAllies12004 row;
      std::string_view reason;
      row.available = ReadPrewarOwnerAllies12004(bindings.alliance, core_frame,
          owner, row.observed, &reason);
      if (!row.available)
        row.failure = reason.empty() ? "prewar_allies_owner_unavailable" : reason;
      if (row.available)
        for (const auto &ally : row.observed.allies) owners.insert(ally.character_id);
      output.current_allies.push_back(std::move(row));
    }
    output.owner_character_ids.assign(owners.begin(), owners.end());
    PrewarForceMilitaryRequest12004 military_request{};
    military_request.snapshot_revision = request.expected_native_revision;
    military_request.date_raw = static_cast<std::int32_t>(before.date_raw);
    military_request.actor_character_id = actor;
    military_request.owner_character_ids = output.owner_character_ids;
    const auto military_status = ReadPrewarForceMilitary12004(bindings.armies,
        bindings.military, bindings.reserve, world,
        envelope.game->descriptor().executable_sha256, military_request,
        output.military);
    if (military_status == PrewarForceMilitaryStatus12004::unavailable ||
        !output.military.exact_build_ready || !output.military.source_frame_ready)
      return Fail(failure, "prewar_force_military_source_frame_unavailable");
    game::Snapshot after;
    if (!ck3_12002::CaptureQuerySnapshot(&envelope, after) || after != before ||
        !ReadSelectedCatalogue(envelope, request))
      return Fail(failure, "prewar_force_sample_frame_changed");
    output.sampled = true;
    return true;
  } catch (...) {
    output.sampled = false;
    failure = "prewar_force_sample_exception";
    return false;
  }
}

std::string SerializePrewarForceCoalition12004(
    const PrewarForceCoalitionSample12004 &sample,
    const PrewarForceCoalitionRequest12004 &request,
    std::uint64_t capture_epoch, std::uint64_t ticket_sequence,
    std::uint64_t query_sequence, std::int32_t date_raw,
    std::int32_t actor_character_id) {
  if (!sample.sampled || !capture_epoch || !ticket_sequence || !query_sequence ||
      sample.selected != request.selected ||
      sample.military.actor_character_id != actor_character_id ||
      sample.military.date_raw != date_raw ||
      sample.military.snapshot_revision != request.expected_native_revision ||
      !sample.military.source_frame_ready) return {};
  std::ostringstream out;
  out << "{\"schema_version\":1,\"status\":\"available_partial\",\"read_only\":true"
      << ",\"game_version\":" << Quote(kGameVersion)
      << ",\"executable_sha256\":" << Quote(kExecutableSha256)
      << ",\"capture_epoch\":" << capture_epoch
      << ",\"native_revision\":" << request.expected_native_revision
      << ",\"public_revision\":" << request.expected_public_revision
      << ",\"date_raw\":" << date_raw
      << ",\"actor_character_id\":" << actor_character_id
      << ",\"declaration_id\":" << Quote(request.declaration_id)
      << ",\"selected_declaration\":";
  Selected(out, request.selected);
  out << ",\"effective_target_character_id\":"
      << sample.generic_effective_target_character_id
      << ",\"ticket\":" << ticket_sequence
      << ",\"query_sequence\":" << query_sequence
      << ",\"current_allies\":[";
  for (std::size_t i = 0; i < sample.current_allies.size(); ++i) {
    if (i) out << ',';
    const auto &row = sample.current_allies[i];
    const bool available = row.available && row.observed.collection_complete;
    out << "{\"owner_character_id\":" << row.observed.owner_character_id
        << ",\"available\":";
    Bool(out, available);
    out << ",\"unavailable_reason\":"
        << (available ? "null" : Quote(row.available ?
            (row.observed.reason.empty() ? "current_allies_source_partial" :
                row.observed.reason) : std::string_view(row.failure)))
        << ",\"collection_complete\":";
    Bool(out, row.available && row.observed.collection_complete);
    out << ",\"ally_character_ids\":";
    if (!row.available) out << "null";
    else {
      std::vector<std::int32_t> ids;
      for (const auto &ally : row.observed.allies) ids.push_back(ally.character_id);
      Ids(out, ids);
    }
    out << ",\"unresolved_source_character_ids\":";
    if (row.available) Ids(out, row.observed.unresolved_source_character_ids);
    else out << "null";
    out << ",\"dead_source_character_ids\":";
    if (row.available) Ids(out, row.observed.dead_source_character_ids);
    else out << "null";
    out << '}';
  }
  out << "],\"owner_forces\":[";
  for (std::size_t i = 0; i < sample.military.owners.size(); ++i) {
    if (i) out << ',';
    const auto &owner = sample.military.owners[i];
    const bool available = CompleteRaisedObservation(sample.military, owner);
    const bool actor = owner.owner_character_id == actor_character_id;
    const bool unraised = actor && sample.military.actor_unraised_ready &&
        sample.military.actor_unraised_current.has_value();
    out << "{\"owner_character_id\":" << owner.owner_character_id
        << ",\"raised_available\":";
    Bool(out, available);
    out << ",\"raised_unavailable_reason\":"
        << (available ? "null" : Quote(owner.failure.empty() ?
            "selected_owner_raised_scalar_scope_partial" : owner.failure))
        << ",\"raised_armies\":[";
    for (std::size_t j = 0; j < owner.raised_armies.size(); ++j) {
      if (j) out << ',';
      const auto &army = owner.raised_armies[j];
      out << "{\"army_id\":" << army.public_unit_id << ",\"current_soldiers\":";
      Nullable(out, army.available ? army.current_soldiers : std::nullopt);
      out << ",\"maximum_soldiers\":";
      Nullable(out, army.available ? army.maximum_soldiers : std::nullopt);
      out << '}';
    }
    out << "],\"raised_current_soldiers\":";
    if (available) out << owner.observed_raised_current_sum;
    else out << "null";
    out << ",\"raised_maximum_soldiers\":";
    if (available) out << owner.observed_raised_maximum_sum;
    else out << "null";
    out << ",\"unraised_available\":";
    Bool(out, unraised);
    out << ",\"unraised_unavailable_reason\":"
        << (unraised ? "null" : Quote(actor ?
            (sample.military.actor_unraised_failure.empty() ?
                "actor_unraised_not_available" : sample.military.actor_unraised_failure)
            : "foreign_unraised_not_sampled"))
        << ",\"unraised_soldiers\":";
    Nullable(out, unraised ? sample.military.actor_unraised_current : std::nullopt);
    out << ",\"native_raise_legal\":";
    if (actor && sample.military.default_raise_legality_ready &&
        sample.military.native_default_raise_legal.has_value())
      Bool(out, *sample.military.native_default_raise_legal);
    else out << "null";
    out << '}';
  }
  out << "],\"actor_ready_unraised_lower_soldiers\":";
  if (sample.military.actor_unraised_ready &&
      sample.military.actor_unraised_current.has_value() &&
      sample.military.default_raise_legality_ready &&
      sample.military.native_default_raise_legal.value_or(false))
    out << *sample.military.actor_unraised_current;
  else out << "null";
  out << ",\"enemy_upper_soldiers\":null,\"enemy_force_coverage_complete\":false"
      << ",\"complete_initial_participants_ready\":false"
      << ",\"automatic_declaration_enabled\":false}";
  return out.str();
}

} // namespace xar::ck3_12004
