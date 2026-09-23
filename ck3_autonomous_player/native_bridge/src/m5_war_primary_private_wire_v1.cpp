#include "xar_bridge/m5_war_primary_private_wire_v1.hpp"

#include "xar_bridge/prewar_scope_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <atomic>
#include <charconv>
#include <cstddef>
#include <cstring>
#include <type_traits>
#include <utility>

namespace xar::ck3_11906 {
namespace {

struct FrameAccess {
  M5WarPrimaryPrivateQueryV1 *query = nullptr;
  const MainThreadExecutionStampV1 *stamp = nullptr;
};

bool OwnsPausedSlot(const FrameAccess &access) noexcept {
  if (access.query == nullptr || access.stamp == nullptr ||
      access.query->mailbox == nullptr || access.query->ticket.sequence == 0 ||
      access.stamp->pump_epoch == 0 || access.stamp->thread_id == 0 ||
      !access.stamp->paused || access.stamp->game_state == 0 ||
      access.stamp->jomini_state == 0 ||
      access.stamp->tls_initialized_flag_address == 0 ||
      access.stamp->tls_initialized != 1 ||
      access.stamp->tls_context == 0 ||
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
         mailbox.executor == &ExecuteM5WarPrimaryPrivateQueryV1 &&
         mailbox.executor_context == access.query;
}

bool SameFrame(const FrameAccess &access, game::Snapshot *snapshot_out = nullptr,
               std::vector<game::DeclarableWarSnapshot> *wars_out = nullptr) {
  const auto &query = *access.query;
  game::Snapshot snapshot{};
  std::vector<game::DeclarableWarSnapshot> wars;
  if (!OwnsPausedSlot(access) || query.game == nullptr ||
      !game::ReadSnapshot(*query.game, snapshot) ||
      snapshot != query.expected_snapshot || !snapshot.paused ||
      snapshot.date_raw != access.stamp->date_raw ||
      game::ReadDeclarableWarsForTarget(*query.game,
                                       query.target_character_id, wars) !=
          game::ReadDeclarableWarsResult::available ||
      wars != query.expected_declarations ||
      std::count(wars.begin(), wars.end(), query.chosen_declaration) != 1) {
    return false;
  }
  if (query.require_unique_player_claim) {
    const auto player = snapshot.played_character_id;
    const auto is_player_claim = [&](const game::DeclarableWarSnapshot &row) {
      return row.target_character_id == query.target_character_id &&
             row.casus_belli_key == "claim_cb" &&
             row.claimant_character_id == player &&
             row.target_title_ids.size() == 1;
    };
    if (!is_player_claim(query.chosen_declaration) ||
        std::count_if(wars.begin(), wars.end(), is_player_claim) != 1) {
      return false;
    }
  }
  if (snapshot_out != nullptr) {
    *snapshot_out = std::move(snapshot);
  }
  if (wars_out != nullptr) {
    *wars_out = std::move(wars);
  }
  return true;
}

bool CaptureWarFrame(void *opaque,
                     game::WarEntryAssessmentFrameV1 &output) noexcept {
  const auto *const access = static_cast<const FrameAccess *>(opaque);
  try {
    if (access == nullptr || !SameFrame(*access)) {
      return false;
    }
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

template <typename T>
T LoadAt(const void *base, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset,
              sizeof(value));
  return value;
}

// Mirrors the already-shipped exact-build read-only ResolveProvince in
// ck3_11906.cpp:2582; no native function is called and no new offset is used.
void *ResolvePrewarProvince(void *game_state,
                            std::int32_t province_id) noexcept {
  if (game_state == nullptr || province_id < 1) {
    return nullptr;
  }
  void *const game_data = LoadAt<void *>(game_state, 0xA0);
  if (game_data == nullptr) {
    return nullptr;
  }
  void *const provinces = LoadAt<void *>(game_data, 0x140);
  const auto count = LoadAt<std::int32_t>(game_data, 0x14C);
  if (provinces == nullptr || count <= 1 || province_id >= count) {
    return nullptr;
  }
  void *const province = LoadAt<void *>(
      provinces, static_cast<std::size_t>(province_id) * sizeof(void *));
  return province != nullptr &&
                 LoadAt<std::int32_t>(province, 0x10) == province_id
             ? province
             : nullptr;
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

bool ParseM5WarPrimaryPrivateStepV1(std::string_view step,
                                   std::int32_t &target_character_id) noexcept {
  target_character_id = -1;
  if (!step.starts_with(kM5WarPrimaryPrivateStepPrefixV1)) {
    return false;
  }
  const auto suffix = step.substr(kM5WarPrimaryPrivateStepPrefixV1.size());
  if (suffix.empty() || suffix.front() == '0' || suffix.size() > 10) {
    return false;
  }
  std::int32_t parsed = -1;
  const auto [end, error] = std::from_chars(
      suffix.data(), suffix.data() + suffix.size(), parsed);
  if (error != std::errc{} || end != suffix.data() + suffix.size() ||
      parsed <= 0) {
    return false;
  }
  target_character_id = parsed;
  return true;
}

bool ParsePrewarPlayerClaimPrivateStepV1(
    std::string_view step, std::int32_t &target_character_id) noexcept {
  target_character_id = -1;
  if (!step.starts_with(kPrewarPlayerClaimPrivateStepPrefixV1)) {
    return false;
  }
  const auto suffix =
      step.substr(kPrewarPlayerClaimPrivateStepPrefixV1.size());
  if (suffix.empty() || suffix.front() == '0' || suffix.size() > 10) {
    return false;
  }
  std::int32_t parsed = -1;
  const auto [end, error] = std::from_chars(
      suffix.data(), suffix.data() + suffix.size(), parsed);
  if (error != std::errc{} || end != suffix.data() + suffix.size() ||
      parsed <= 0) {
    return false;
  }
  target_character_id = parsed;
  return true;
}

bool ExecuteM5WarPrimaryPrivateQueryV1(
    void *opaque_context, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *const query = static_cast<M5WarPrimaryPrivateQueryV1 *>(opaque_context);
  if (query == nullptr) {
    return false;
  }
  const FrameAccess access{query, &stamp};
  if (!OwnsPausedSlot(access) || query->executor_invocations != 0 ||
      query->available || query->expected_revision == 0 ||
      query->target_character_id <= 0 || query->module_base == 0 ||
      query->war_environment.module_base != query->module_base ||
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

    const PrewarScopeBindingsV1 bindings{
        reinterpret_cast<void **>(query->module_base +
                                  kPrewarScopeV1UnitStorageSlotRva),
        reinterpret_cast<void **>(query->module_base +
                                  kPrewarScopeV1ArmyStorageSlotRva),
        &ResolvePrewarProvince};
    const PrewarScopeRequestV1 scope_request{
        query->expected_revision, query->expected_snapshot.date_raw,
        query->expected_snapshot.played_character_id,
        entry.assessments[0].effective_target_character_id};
    PrewarScopeObservationV1 scope{};
    if (ReadDeclarationBoundPrewarScopeV1(
            bindings, reinterpret_cast<void *>(stamp.game_state), true, true,
            scope_request, scope) !=
        ReadPrewarScopeStatusV1::available_primary_scope) {
      query->failure_stage = scope.failure_stage.empty()
                                 ? "prewar_primary_scope_unavailable"
                                 : scope.failure_stage;
      return true;
    }
    M5PrimaryArmySupplyObservationV1 supply{};
    if (ReadM5PrimaryArmySupplyV1(bindings.carmy_storage_slot, true, true,
                                  scope, supply) !=
        M5PrimaryArmySupplyStatusV1::available) {
      query->failure_stage = supply.failure_stage.empty()
                                 ? "current_supply_unavailable"
                                 : supply.failure_stage;
      return true;
    }
    const M5WarPrimaryReadbackInputsV1 inputs{
        query->expected_revision, &query->expected_snapshot,
        query->expected_revision, &query->expected_declarations,
        query->expected_revision, &query->chosen_declaration, &entry, &scope,
        &supply};
    if (ReadM5WarPrimaryReadbackV1(inputs, query->result) !=
        M5WarPrimaryReadbackStatusV1::available_current_primary_slice) {
      query->failure_stage = query->result.unavailable_stage.empty()
                                 ? "primary_join_unavailable"
                                 : query->result.unavailable_stage;
      return true;
    }
    if (query->require_unique_player_claim) {
      if (!game::ReadClaimCountyObjectiveProvince(
              *query->game,
              query->chosen_declaration.target_title_ids.front(),
              query->claim_county_objective_province_id)) {
        query->result = {};
        query->failure_stage = "claim_county_objective_unavailable";
        return true;
      }
      query->claim_primary_current_raised_armies =
          scope.primary_raised_armies;
    }
    if (!SameFrame(access)) {
      query->result = {};
      query->failure_stage = "postread_public_or_legal_frame_drift";
      return true;
    }
    query->available = true;
    return true;
  } catch (...) {
    query->result = {};
    query->failure_stage = "private_query_exception";
    return true;
  }
}

std::string SerializeM5WarPrimaryPrivateResultV1(
    const M5WarPrimaryReadbackV1 &result) {
  if (result.status !=
          M5WarPrimaryReadbackStatusV1::available_current_primary_slice ||
      result.native_revision == 0 || result.actor_character_id <= 0 ||
      result.effective_target_character_id <= 0 ||
      result.current_treasury.scale <= 0) {
    return {};
  }
  std::string output = "{\"status\":\"available_current_primary_slice\",\"native_revision\":";
  output += std::to_string(result.native_revision);
  output += ",\"date_raw\":" + std::to_string(result.date_raw);
  output += ",\"actor_character_id\":" +
            std::to_string(result.actor_character_id);
  output += ",\"declaration\":{\"target_character_id\":" +
            std::to_string(result.declaration.target_character_id);
  output += ",\"casus_belli_index\":" +
            std::to_string(result.declaration.casus_belli_index);
  output += ",\"casus_belli_key\":";
  AppendJsonString(output, result.declaration.casus_belli_key);
  output += ",\"configuration_index\":" +
            std::to_string(result.declaration.configuration_index);
  output += ",\"claimant_character_id\":" +
            std::to_string(result.declaration.claimant_character_id);
  output += ",\"target_title_ids\":[";
  for (std::size_t i = 0; i < result.declaration.target_title_ids.size(); ++i) {
    if (i != 0) output.push_back(',');
    output += std::to_string(result.declaration.target_title_ids[i]);
  }
  output += "]},\"effective_target_character_id\":" +
            std::to_string(result.effective_target_character_id);
  output += ",\"native_power_ratio_raw\":" +
            std::to_string(result.native_power_ratio_raw);
  output += ",\"native_power_ratio_scale\":100000";
  output += ",\"current_treasury\":{\"raw\":" +
            std::to_string(result.current_treasury.raw) +
            ",\"scale\":" +
            std::to_string(result.current_treasury.scale) + "}";
  output += ",\"active_war_ids\":[";
  for (std::size_t i = 0; i < result.active_war_ids.size(); ++i) {
    if (i != 0) output.push_back(',');
    output += std::to_string(result.active_war_ids[i]);
  }
  output += "],\"actor_current_raised_armies\":[";
  for (std::size_t i = 0; i < result.actor_current_raised_armies.size(); ++i) {
    const auto &army = result.actor_current_raised_armies[i];
    if (i != 0) output.push_back(',');
    output += "{\"army_id\":" + std::to_string(army.army_id);
    output += ",\"owner_character_id\":" +
              std::to_string(army.owner_character_id);
    output += ",\"has_current_province\":";
    output += army.has_current_province ? "true" : "false";
    output += ",\"current_province_id\":" +
              std::to_string(army.current_province_id);
    output += ",\"move_target_observable\":";
    output += army.move_target_observable ? "true" : "false";
    output += ",\"move_target_province_id\":" +
              std::to_string(army.move_target_province_id);
    output += ",\"route_province_ids\":[";
    for (std::size_t j = 0; j < army.route_province_ids.size(); ++j) {
      if (j != 0) output.push_back(',');
      output += std::to_string(army.route_province_ids[j]);
    }
    output += "]}";
  }
  output += "],\"actor_current_raised_supply\":[";
  for (std::size_t i = 0; i < result.actor_current_raised_supply.size(); ++i) {
    const auto &row = result.actor_current_raised_supply[i];
    if (i != 0) output.push_back(',');
    output += "{\"army_id\":" + std::to_string(row.army_id);
    output += ",\"native_carmy_id\":" +
              std::to_string(row.native_carmy_id);
    output += ",\"owner_character_id\":" +
              std::to_string(row.owner_character_id);
    output += ",\"current_supply_raw\":" +
              std::to_string(row.current_supply_raw);
    output += ",\"current_supply_scale\":" +
              std::to_string(row.current_supply_scale) + "}";
  }
  output += "]}";
  return output;
}

std::string SerializePrewarPlayerClaimPrivateResultV1(
    const M5WarPrimaryPrivateQueryV1 &query) {
  if (!query.require_unique_player_claim || !query.available ||
      query.claim_county_objective_province_id <= 0) {
    return {};
  }
  std::string output = SerializeM5WarPrimaryPrivateResultV1(query.result);
  if (output.empty() || output.back() != '}') {
    return {};
  }
  output.pop_back();
  output += ",\"prewar_player_claim\":{\"county_objective_province_id\":";
  output += std::to_string(query.claim_county_objective_province_id);
  output += ",\"primary_current_raised_armies\":[";
  for (std::size_t i = 0;
       i < query.claim_primary_current_raised_armies.size(); ++i) {
    const auto &army = query.claim_primary_current_raised_armies[i];
    if (i != 0) output.push_back(',');
    output += "{\"army_id\":" + std::to_string(army.army_id);
    output += ",\"native_carmy_id\":" +
              std::to_string(army.native_carmy_id);
    output += ",\"owner_character_id\":" +
              std::to_string(army.owner_character_id);
    output += ",\"side\":\"";
    output += army.side == PrewarSideV1::attacker ? "attacker" : "defender";
    output += "\",\"current_province_id\":";
    output += army.has_current_province
                  ? std::to_string(army.current_province_id)
                  : "null";
    output += ",\"move_target_province_id\":";
    output += army.has_move_target_province
                  ? std::to_string(army.move_target_province_id)
                  : "null";
    output += ",\"route_province_ids\":[";
    for (std::size_t j = 0; j < army.route_province_ids.size(); ++j) {
      if (j != 0) output.push_back(',');
      output += std::to_string(army.route_province_ids[j]);
    }
    output += "]}";
  }
  output += "],\"complete_initial_participants_ready\":false,";
  output += "\"combat_forecast_ready\":false}}";
  return output;
}

static_assert(std::is_same_v<decltype(&ExecuteM5WarPrimaryPrivateQueryV1),
                             MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
