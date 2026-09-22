#include "xar_bridge/minor_religious_war_defenders_private_wire_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <atomic>
#include <charconv>
#include <limits>
#include <type_traits>

namespace xar::ck3_11906 {
namespace {

struct FrameAccess {
  MinorReligiousWarDefendersPrivateQueryV1 *query = nullptr;
  const MainThreadExecutionStampV1 *stamp = nullptr;
};

bool OwnsPausedSlot(const FrameAccess &access) noexcept {
  if (access.query == nullptr || access.stamp == nullptr ||
      access.query->mailbox == nullptr || access.query->ticket.sequence == 0 ||
      access.stamp->pump_epoch == 0 || access.stamp->thread_id == 0 ||
      !access.stamp->paused || access.stamp->game_state == 0 ||
      access.stamp->jomini_state == 0 ||
      access.stamp->tls_initialized_flag_address == 0 ||
      access.stamp->tls_initialized != 1 || access.stamp->tls_context == 0 ||
      access.stamp->tls_main_thread_marker != 1 ||
      GetCurrentThreadId() != access.stamp->thread_id) {
    return false;
  }
  const auto &mailbox = *access.query->mailbox;
  return mailbox.state.load(std::memory_order_acquire) ==
             MainThreadQueryMailboxStateV1::executing &&
         !mailbox.stop_requested.load(std::memory_order_acquire) &&
         mailbox.failure_flags.load(std::memory_order_acquire) == 0 &&
         mailbox.published_sequence.load(std::memory_order_acquire) ==
             access.query->ticket.sequence &&
         mailbox.owner_thread_id.load(std::memory_order_acquire) ==
             access.stamp->thread_id &&
         mailbox.paused_owner_verified_pump_epochs.load(
             std::memory_order_acquire) >=
             kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs &&
         mailbox.executor ==
             &ExecuteMinorReligiousWarDefendersPrivateQueryV1 &&
         mailbox.executor_context == access.query;
}

bool SameFrame(const FrameAccess &access) {
  const auto &query = *access.query;
  game::Snapshot snapshot{};
  std::vector<game::DeclarableWarSnapshot> wars;
  return OwnsPausedSlot(access) && query.game != nullptr &&
         game::ReadSnapshot(*query.game, snapshot) &&
         snapshot == query.expected_snapshot && snapshot.paused &&
         snapshot.date_raw == access.stamp->date_raw &&
         game::ReadDeclarableWarsForTarget(*query.game,
                                           query.target_character_id, wars) ==
             game::ReadDeclarableWarsResult::available &&
         wars == query.expected_declarations &&
         std::count(wars.begin(), wars.end(), query.chosen_declaration) == 1;
}

bool CaptureWarFrame(void *opaque,
                     game::WarEntryAssessmentFrameV1 &output) noexcept {
  const auto *const access = static_cast<const FrameAccess *>(opaque);
  try {
    if (access == nullptr || !SameFrame(*access)) return false;
    const auto &query = *access->query;
    const auto &snapshot = query.expected_snapshot;
    output = {};
    output.snapshot_revision = query.expected_revision;
    output.date_raw = snapshot.date_raw;
    output.paused = snapshot.paused;
    output.map_ready = snapshot.map_ready;
    output.actor_alive = snapshot.has_played_character &&
                         snapshot.played_character_alive;
    output.actor_character_id = snapshot.played_character_id;
    output.declarable_target_character_ids = {query.target_character_id};
    for (const auto &war : snapshot.active_wars) {
      const auto target = war.primary_opponent_character_id;
      if (target > 0 &&
          std::find(output.active_war_primary_opponent_character_ids.begin(),
                    output.active_war_primary_opponent_character_ids.end(),
                    target) ==
              output.active_war_primary_opponent_character_ids.end()) {
        output.active_war_primary_opponent_character_ids.push_back(target);
      }
    }
    return true;
  } catch (...) {
    output = {};
    return false;
  }
}

bool IsApplicationMain(void *opaque) noexcept {
  const auto *const access = static_cast<const FrameAccess *>(opaque);
  return access != nullptr && OwnsPausedSlot(*access);
}

void AppendJsonString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output.push_back('"');
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') {
      output.push_back('\\');
      output.push_back(static_cast<char>(c));
    } else if (c < 0x20) {
      output += "\\u00";
      output.push_back(hex[(c >> 4U) & 0x0FU]);
      output.push_back(hex[c & 0x0FU]);
    } else {
      output.push_back(static_cast<char>(c));
    }
  }
  output.push_back('"');
}

} // namespace

bool ParseMinorReligiousWarDefendersPrivateStepV1(
    std::string_view step, std::int32_t &target_character_id) noexcept {
  target_character_id = -1;
  if (!step.starts_with(kMinorReligiousWarDefendersPrivateStepPrefixV1))
    return false;
  const auto suffix =
      step.substr(kMinorReligiousWarDefendersPrivateStepPrefixV1.size());
  if (suffix.empty() || suffix.front() == '0' || suffix.size() > 10)
    return false;
  std::int32_t parsed = -1;
  const auto [end, error] =
      std::from_chars(suffix.data(), suffix.data() + suffix.size(), parsed);
  if (error != std::errc{} || end != suffix.data() + suffix.size() ||
      parsed <= 0)
    return false;
  target_character_id = parsed;
  return true;
}

bool ExecuteMinorReligiousWarDefendersPrivateQueryV1(
    void *opaque_context, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *const query =
      static_cast<MinorReligiousWarDefendersPrivateQueryV1 *>(opaque_context);
  if (query == nullptr) return false;
  const FrameAccess access{query, &stamp};
  if (!OwnsPausedSlot(access) || query->executor_invocations != 0 ||
      query->available || query->expected_revision == 0 ||
      query->target_character_id <= 0 || query->module_base == 0 ||
      query->chosen_declaration.casus_belli_key != "minor_religious_war" ||
      query->war_environment.module_base != query->module_base ||
      query->defender_environment.module_base != query->module_base ||
      query->war_environment.game_state_slot == nullptr ||
      *query->war_environment.game_state_slot !=
          reinterpret_cast<void *>(stamp.game_state)) {
    query->failure_stage = "application_main_admission";
    return false;
  }
  try {
    ++query->executor_invocations;
    query->execution_stamp = stamp;
    if (!SameFrame(access)) {
      query->failure_stage = "public_or_legal_frame_drift";
      return true;
    }
    WarEntryAssessmentAccessV1 war_access{};
    war_access.context = const_cast<FrameAccess *>(&access);
    war_access.capture_frame = &CaptureWarFrame;
    war_access.is_main_thread = &IsApplicationMain;
    WarEntryAssessmentsV1Request request{};
    request.expected_snapshot_revision = query->expected_revision;
    request.target_character_ids = {query->target_character_id};
    game::WarEntryAssessmentsV1 entry{};
    if (ReadWarEntryAssessmentsV1(query->war_environment, war_access, request,
                                  entry) !=
            game::ReadWarEntryAssessmentsV1Result::available ||
        !entry.available || !entry.readiness.ready ||
        entry.assessments.size() != 1 ||
        entry.assessments[0].effective_target_character_id <= 0) {
      query->failure_stage = entry.unavailable_stage.empty()
                                 ? "war_entry_unavailable"
                                 : entry.unavailable_stage;
      return true;
    }
    MinorReligiousDefenderAccessV1 defender_access{};
    defender_access.application_main_paused = true;
    const auto defenders = ReadMinorReligiousDefendersV1(
        query->defender_environment, defender_access,
        query->expected_snapshot.played_character_id,
        entry.assessments[0].effective_target_character_id);
    if (defenders.failure != MinorReligiousDefenderFailureV1::none) {
      query->failure_stage = "faith_defender_observer_unavailable:" +
                             std::to_string(
                                 static_cast<int>(defenders.failure));
      return true;
    }
    const auto &assessment = entry.assessments[0];
    if (defenders.actor_base_power_raw != assessment.actor_power_base_raw ||
        defenders.primary_defender_base_power_raw !=
            assessment.target_power_base_raw) {
      query->failure_stage = "same_frame_power_leaf_mismatch";
      return true;
    }
    if (!SameFrame(access)) {
      query->failure_stage = "postread_public_or_legal_frame_drift";
      return true;
    }
    query->result.native_revision = query->expected_revision;
    query->result.date_raw = query->expected_snapshot.date_raw;
    query->result.declaration = query->chosen_declaration;
    query->result.assessment = assessment;
    query->result.defenders = defenders;
    query->available = true;
    return true;
  } catch (...) {
    query->result = {};
    query->failure_stage = "private_query_exception";
    return true;
  }
}

std::string SerializeMinorReligiousWarDefendersPrivateResultV1(
    const MinorReligiousWarDefendersPrivateResultV1 &result) {
  const auto &declaration = result.declaration;
  const auto &assessment = result.assessment;
  const auto &defenders = result.defenders;
  if (result.native_revision == 0 ||
      declaration.casus_belli_key != "minor_religious_war" ||
      declaration.target_character_id <= 0 ||
      assessment.target_character_id != declaration.target_character_id ||
      assessment.effective_target_character_id <= 0 ||
      defenders.failure != MinorReligiousDefenderFailureV1::none ||
      defenders.actor_character_id <= 0 ||
      defenders.primary_defender_character_id !=
          assessment.effective_target_character_id) {
    return {};
  }
  std::string output =
      "{\"status\":\"available\",\"native_revision\":" +
      std::to_string(result.native_revision) +
      ",\"date_raw\":" + std::to_string(result.date_raw) +
      ",\"declaration\":{\"target_character_id\":" +
      std::to_string(declaration.target_character_id) +
      ",\"casus_belli_index\":" +
      std::to_string(declaration.casus_belli_index) +
      ",\"casus_belli_key\":";
  AppendJsonString(output, declaration.casus_belli_key);
  output += ",\"configuration_index\":" +
            std::to_string(declaration.configuration_index) +
            ",\"claimant_character_id\":" +
            std::to_string(declaration.claimant_character_id) +
            ",\"target_title_ids\":[";
  for (std::size_t index = 0; index < declaration.target_title_ids.size();
       ++index) {
    if (index != 0) output.push_back(',');
    output += std::to_string(declaration.target_title_ids[index]);
  }
  output += "],\"defender_faith_can_join_source\":true}";
  output += ",\"actor_character_id\":" +
            std::to_string(defenders.actor_character_id) +
            ",\"primary_defender_character_id\":" +
            std::to_string(defenders.primary_defender_character_id) +
            ",\"actor_power_base_raw\":" +
            std::to_string(assessment.actor_power_base_raw) +
            ",\"actor_power_total_raw\":" +
            std::to_string(assessment.actor_power_total_raw) +
            ",\"primary_defender_power_base_raw\":" +
            std::to_string(assessment.target_power_base_raw) +
            ",\"primary_defender_power_total_raw\":" +
            std::to_string(assessment.target_power_total_raw) +
            ",\"prospective_joiner_base_power_raw\":" +
            std::to_string(defenders.prospective_joiner_base_power_raw) +
            ",\"primary_plus_joiner_base_power_raw\":" +
            std::to_string(defenders.primary_plus_joiner_base_power_raw) +
            ",\"primary_total_plus_joiner_base_power_raw\":";
  if (assessment.target_power_total_raw >
      std::numeric_limits<std::int64_t>::max() -
          defenders.prospective_joiner_base_power_raw) {
    return {};
  }
  output += std::to_string(assessment.target_power_total_raw +
                           defenders.prospective_joiner_base_power_raw);
  output += ",\"power_scale\":100000,\"prospective_joiners\":[";
  for (std::size_t index = 0; index < defenders.prospective_joiners.size();
       ++index) {
    if (index != 0) output.push_back(',');
    const auto &row = defenders.prospective_joiners[index];
    output += "{\"character_id\":" + std::to_string(row.character_id) +
              ",\"base_power_raw\":" +
              std::to_string(row.base_power_raw) + "}";
  }
  output += "]}";
  return output;
}

static_assert(
    std::is_same_v<decltype(&ExecuteMinorReligiousWarDefendersPrivateQueryV1),
                   MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
