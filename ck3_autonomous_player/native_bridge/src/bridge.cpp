#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/battle_control_snapshot_v1_mailbox.hpp"
#include "xar_bridge/battle_reinforcement_assignment_v1_mailbox.hpp"
#include "xar_bridge/battle_terminal_journal_v1.hpp"
#include "xar_bridge/battle_terminal_transition_v1_mailbox.hpp"
#include "xar_bridge/battle_transition_v1_mailbox.hpp"
#include "xar_bridge/campaign_root_context_v1_mailbox.hpp"
#include "xar_bridge/combat_simulation_inputs_v3_mailbox.hpp"
#include "xar_bridge/event_window_context_v1_mailbox.hpp"
#include "xar_bridge/loaded_feature_manifest_v1_mailbox.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/pending_character_interaction_context_v1_mailbox.hpp"
#include "xar_bridge/route_contact_horizon_v1_mailbox.hpp"
#include "xar_bridge/actual_contact_scope_v1_mailbox.hpp"
#include "xar_bridge/protocol.hpp"
#include "xar_bridge/startup_dx11_render_context_draw_guard_v1.hpp"
#include "xar_bridge/startup_localize_current_root_guard_v1.hpp"
#include "xar_bridge/startup_particle2_consumer_null_guard_v1.hpp"
#include "xar_bridge/startup_particle2_null_guard_v1.hpp"
#include "xar_bridge/startup_particle2_stage_recorder_v1.hpp"
#include "xar_bridge/tactical_daily_sentinel_v1.hpp"
#include "xar_bridge/title_map_navigation_v1_mailbox.hpp"
#include "xar_bridge/title_map_navigation_v1_serializer.hpp"
#include "xar_bridge/war_entry_assessments_v1_mailbox.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <charconv>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <utility>

namespace {

static_assert(sizeof(void *) == 8, "the CK3 bridge is x64-only");

constexpr wchar_t kPipeEnvironment[] = L"XAR_CK3_BRIDGE_PIPE";
constexpr std::size_t kPipeNameCapacity = 256;
constexpr DWORD kHeartbeatIntervalMs = 250;
// The four startup guards remain exact-build diagnostic fixtures, while the
// production default leaves the original executable bytes untouched.  The
// separate build-time stage recorder is opt-in and only counts the three
// particle2 factory null exits without suppressing or redirecting native flow.
constexpr bool kStartupFailureContainmentEnabledV1 = false;
#if defined(XAR_CK3_ENABLE_STARTUP_PARTICLE2_STAGE_RECORDER_V1)
constexpr bool kStartupParticle2StageRecorderEnabledV1 = true;
#else
constexpr bool kStartupParticle2StageRecorderEnabledV1 = false;
#endif
static_assert(!(kStartupFailureContainmentEnabledV1 &&
                kStartupParticle2StageRecorderEnabledV1));

wchar_t g_pipe_name[kPipeNameCapacity]{};
HANDLE g_stop_event = nullptr;
HANDLE g_worker_thread = nullptr;
std::atomic<long> g_lifecycle{0}; // 0 stopped, 1 starting/running, 2 stopping
// Process-lifetime storage is mandatory for the IAT hook.  Stop restores the
// original IAT entry but never permits unloading this DLL before process exit.
static xar::ck3_11906::MainThreadQueryMailboxV1
    g_main_thread_query_mailbox_v1{};
static xar::ck3_11906::BattleTerminalJournalDetourStateV1
    g_battle_terminal_journal_v1{};
static xar::ck3_11906::TacticalDailySentinelDetourStateV1
    g_tactical_daily_sentinel_v1{};
static xar::bridge::StartupParticle2NullGuardV1State
    g_startup_particle2_null_guard_v1{};
static xar::bridge::StartupParticle2ConsumerGuardV1State
    g_startup_particle2_consumer_null_guard_v1{};
static xar::bridge::StartupParticle2StageRecorderV1State
    g_startup_particle2_stage_recorder_v1{};
static xar::bridge::StartupDx11RenderContextDrawGuardV1State
    g_startup_dx11_render_context_draw_guard_v1{};
static xar::bridge::StartupLocalizeCurrentRootGuardV1State
    g_startup_localize_current_root_guard_v1{};

bool IsPipeName(const wchar_t *value, DWORD length) noexcept {
  constexpr wchar_t prefix[] = L"\\\\.\\pipe\\";
  constexpr DWORD prefix_length =
      static_cast<DWORD>((sizeof(prefix) / sizeof(prefix[0])) - 1U);
  if (length <= prefix_length || length >= kPipeNameCapacity) {
    return false;
  }
  for (DWORD index = 0; index < prefix_length; ++index) {
    if (value[index] != prefix[index]) {
      return false;
    }
  }
  return true;
}

std::string Number(std::uint64_t value) {
  std::array<char, 32> buffer{};
  const auto result =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (result.ec != std::errc{}) {
    return "0";
  }
  return std::string(buffer.data(), result.ptr);
}

std::string SignedNumber(std::int64_t value) {
  std::array<char, 32> buffer{};
  const auto result =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (result.ec != std::errc{}) {
    return "0";
  }
  return std::string(buffer.data(), result.ptr);
}

void AppendJsonString(std::string &result, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  result += '"';
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      result += '\\';
      result += static_cast<char>(character);
    } else if (character < 0x20U) {
      result += "\\u00";
      result += hex[(character >> 4U) & 0x0FU];
      result += hex[character & 0x0FU];
    } else {
      result += static_cast<char>(character);
    }
  }
  result += '"';
}

std::string IdentityFrame() {
  const auto &descriptor = xar::game::PreferredAdapterDescriptor();
  std::string result =
      "{\"bridge\":\"xar_ck3_bridge\",\"bridge_version\":\"";
  result += XAR_BRIDGE_VERSION;
  result += "\",\"protocol_version\":1,\"architecture\":"
            "\"x86_64-windows-msvc\",\"expected_ck3_version\":";
  AppendJsonString(result, descriptor.game_version);
  result += ",\"expected_ck3_sha256\":";
  AppendJsonString(result, descriptor.executable_sha256);
  result += ",\"game_adapter_id\":";
  AppendJsonString(result, descriptor.adapter_id);
  result += '}';
  return result;
}

struct CheckpointSubmission {
  std::uint64_t sequence = 0;
  std::int32_t date_raw = 0;
  std::string_view save_name;
};

struct SnapshotPublishDiagnostics {
  std::string_view status = "not_attempted";
  std::uint64_t revision = 0;
  std::size_t payload_bytes = 0;
};

std::string HelloFrame(const xar::game::GameAdapter &game) {
  const auto &descriptor = game.descriptor();
  std::string result =
      "{\"type\":\"hello\",\"protocol_version\":1,\"bridge_version\":\"";
  result += XAR_BRIDGE_VERSION;
  result += "\",\"pid\":";
  result += Number(GetCurrentProcessId());
  result +=
      ",\"session_generation\":0,\"architecture\":\"x86_64-windows-msvc\","
      "\"expected_ck3_version\":";
  AppendJsonString(result, descriptor.game_version);
  result += ",\"expected_ck3_sha256\":";
  AppendJsonString(result, descriptor.executable_sha256);
  result += ",\"game_adapter_id\":";
  AppendJsonString(result, descriptor.adapter_id);
  result += ",\"game_adapter_status\":";
  AppendJsonString(result, game.enabled() ? "ready" : "unsupported_build");
  result += ",\"ck3_build_match\":";
  result += game.enabled() ? "true" : "false";
  result += ",\"capabilities\":[\"bridge.identity\",\"bridge.heartbeat\","
            "\"bridge.ping\"";
  if (game.enabled()) {
    for (const auto capability : descriptor.capabilities) {
      result += ',';
      AppendJsonString(result, capability);
    }
  }
  result += "]}";
  return result;
}

std::string HeartbeatFrame(std::uint64_t sequence) {
  const auto mailbox =
      xar::ck3_11906::ReadMainThreadQueryMailboxDiagnosticsV1(
          g_main_thread_query_mailbox_v1);
  const auto startup_guard =
      xar::bridge::ReadStartupParticle2NullGuardV1Diagnostics(
          g_startup_particle2_null_guard_v1);
  const auto startup_consumer_guard =
      xar::bridge::ReadStartupParticle2ConsumerGuardV1Diagnostics(
          g_startup_particle2_consumer_null_guard_v1);
  const auto startup_stage_recorder =
      xar::bridge::ReadStartupParticle2StageRecorderV1Diagnostics(
          g_startup_particle2_stage_recorder_v1);
  const auto startup_dx11_draw_guard =
      xar::bridge::ReadStartupDx11RenderContextDrawGuardV1Diagnostics(
          g_startup_dx11_render_context_draw_guard_v1);
  const auto startup_localize_guard =
      xar::bridge::ReadStartupLocalizeCurrentRootGuardV1Diagnostics(
          g_startup_localize_current_root_guard_v1);
  std::string result =
      "{\"type\":\"heartbeat\",\"protocol_version\":1,\"sequence\":";
  result += Number(sequence);
  result += ",\"pid\":";
  result += Number(GetCurrentProcessId());
  result += ",\"monotonic_ms\":";
  result += Number(GetTickCount64());
  result += ",\"startup_failure_containment_enabled\":";
  result += kStartupFailureContainmentEnabledV1 ? "true" : "false";
  result += ",\"startup_particle2_stage_recorder_enabled\":";
  result += kStartupParticle2StageRecorderEnabledV1 ? "true" : "false";
  result += ",\"main_thread_query_mailbox_v1\":{";
  result += "\"candidate_id\":";
  AppendJsonString(result,
                   xar::ck3_11906::kMainThreadQueryMailboxV1CandidateId);
  result +=
      ",\"query_scope\":\"typed_war_entry_route_actual_contact_combat_v3_battle_control_battle_transition_reinforcement_assignment_campaign_root_context_loaded_feature_manifest_pending_character_interaction_context_current_event_window_title_map_navigation\"";
  result += ",\"installed\":";
  result += mailbox.iat_installed ? "true" : "false";
  result += ",\"stop\":";
  result += mailbox.stop_requested ? "true" : "false";
  result += ",\"failure\":";
  result += Number(mailbox.failure_flags);
  result += ",\"pump_epochs\":";
  result += Number(mailbox.pump_epochs);
  result += ",\"consecutive_verified\":";
  result += Number(mailbox.paused_owner_verified_pump_epochs);
  result += ",\"owner_tid\":";
  result += Number(mailbox.owner_thread_id);
  result += ",\"current_tid\":";
  result += Number(mailbox.observed_current_thread_id);
  result += ",\"rng_owner_tid\":";
  result += Number(mailbox.observed_rng_owner_thread_id);
  result += ",\"tls_global\":";
  result += Number(mailbox.observed_tls_initialized);
  result += ",\"tls_context\":";
  result += Number(mailbox.observed_tls_context);
  result += ",\"tls_marker\":";
  result += Number(mailbox.observed_tls_main_thread_marker);
  result += ",\"jomini_state\":";
  result += Number(mailbox.observed_jomini_state);
  result += ",\"game_state\":";
  result += Number(mailbox.observed_game_state);
  result += ",\"date_raw\":";
  result += SignedNumber(mailbox.observed_date_raw);
  result += ",\"paused\":";
  result += mailbox.observed_paused ? "true" : "false";
  result += ",\"stamp_read_success\":";
  result += mailbox.observed_stamp_read_success ? "true" : "false";
  result += ",\"executed_requests\":";
  result += Number(mailbox.executed_requests);
  result += ",\"executor_submission_enabled\":";
  result += mailbox.executor_submission_enabled ? "true" : "false";
  result += ",\"ready\":";
  result += mailbox.ready ? "true" : "false";
  result += "},\"startup_particle2_null_guard_v1\":{";
  result += "\"installed\":";
  result += startup_guard.installed ? "true" : "false";
  result += ",\"failure\":";
  result += Number(startup_guard.failure_flags);
  result += ",\"suppressed_count\":";
  result += Number(startup_guard.suppressed_count);
  result += ",\"suppressed_index_mask\":";
  result += Number(startup_guard.suppressed_index_mask);
  result += ",\"last_suppressed_index\":";
  result += Number(startup_guard.last_suppressed_index);
  result += "},\"startup_particle2_consumer_null_guard_v1\":{";
  result += "\"installed\":";
  result += startup_consumer_guard.installed ? "true" : "false";
  result += ",\"failure\":";
  result += Number(startup_consumer_guard.failure_flags);
  result += ",\"suppressed_count\":";
  result += Number(startup_consumer_guard.suppressed_count);
  result += ",\"missing_slot_mask\":";
  result += Number(startup_consumer_guard.missing_slot_mask);
  result += "},\"startup_particle2_stage_recorder_v1\":{";
  result += "\"installed\":";
  result += startup_stage_recorder.installed ? "true" : "false";
  result += ",\"patch_mask\":";
  result += Number(startup_stage_recorder.patch_mask);
  result += ",\"failure\":";
  result += Number(startup_stage_recorder.failure_flags);
  result += ",\"source_lookup_null_count\":";
  result += Number(startup_stage_recorder.source_lookup_null_count);
  result += ",\"variant_lookup_null_count\":";
  result += Number(startup_stage_recorder.variant_lookup_null_count);
  result += ",\"backend_creation_null_count\":";
  result += Number(startup_stage_recorder.backend_creation_null_count);
  result += "},\"startup_dx11_render_context_draw_guard_v1\":{";
  result += "\"installed\":";
  result += startup_dx11_draw_guard.installed ? "true" : "false";
  result += ",\"failure\":";
  result += Number(startup_dx11_draw_guard.failure_flags);
  result += ",\"suppressed_count\":";
  result += Number(startup_dx11_draw_guard.suppressed_count);
  result += "},\"startup_localize_current_root_guard_v1\":{";
  result += "\"installed\":";
  result += startup_localize_guard.installed ? "true" : "false";
  result += ",\"failure\":";
  result += Number(startup_localize_guard.failure_flags);
  result += ",\"native_miss_count\":";
  result += Number(startup_localize_guard.native_miss_count);
  result += "}}";
  return result;
}

void AppendInt32Array(std::string &result,
                      const std::vector<std::int32_t> &values) {
  result += '[';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      result += ',';
    }
    result += SignedNumber(values[index]);
  }
  result += ']';
}

void AppendArmySnapshot(std::string &result,
                        const xar::game::ArmySnapshot &army) {
  result += "{\"army_id\":";
  result += SignedNumber(army.army_id);
  result += ",\"owner_character_id\":";
  result += SignedNumber(army.owner_character_id);
  result += ",\"current_province_id\":";
  if (army.has_current_province) {
    result += SignedNumber(army.current_province_id);
  } else {
    result += "null";
  }
  result += ",\"route_province_ids\":";
  AppendInt32Array(result, army.route_province_ids);
  result += ",\"move_target_province_id\":";
  if (army.move_target_observable) {
    result += SignedNumber(army.move_target_province_id);
  } else {
    result += "null";
  }
  result += ",\"move_target_observable\":";
  result += army.move_target_observable ? "true" : "false";
  result += ",\"army_state_code\":";
  result += SignedNumber(army.army_state_code);
  result += ",\"army_state\":";
  AppendJsonString(result, army.army_state);
  result += ",\"in_combat\":";
  result += army.in_combat ? "true" : "false";
  result += ",\"retreating\":";
  result += army.retreating ? "true" : "false";
  result += ",\"controllable\":";
  result += army.controllable ? "true" : "false";
  result += '}';
}

void AppendArmyArray(
    std::string &result,
    const std::vector<xar::game::ArmySnapshot> &armies) {
  result += '[';
  for (std::size_t index = 0; index < armies.size(); ++index) {
    if (index != 0) {
      result += ',';
    }
    AppendArmySnapshot(result, armies[index]);
  }
  result += ']';
}

void AppendArmyStrength(
    std::string &result,
    const xar::game::ArmyStrengthSnapshot &strength) {
  result += "{\"status\":\"";
  result += strength.available ? "available" : "unavailable";
  result += "\",\"army_id\":";
  result += SignedNumber(strength.army_id);
  result += ",\"native_carmy_id\":";
  if (strength.native_carmy_id_observable) {
    result += SignedNumber(strength.native_carmy_id);
  } else {
    result += "null";
  }
  result += ",\"scope_role\":\"";
  switch (strength.scope_role) {
  case xar::game::ArmyStrengthScopeRole::player:
    result += "player";
    break;
  case xar::game::ArmyStrengthScopeRole::active_war_ally:
    result += "active_war_ally";
    break;
  case xar::game::ArmyStrengthScopeRole::active_war_enemy:
    result += "active_war_enemy";
    break;
  }
  result += "\",\"war_ids\":";
  AppendInt32Array(result, strength.war_ids);
  result += ",\"regiment_count\":";
  if (strength.available) {
    result += SignedNumber(strength.regiment_count);
  } else {
    result += "null";
  }
  result += ",\"current_soldiers\":";
  if (strength.available) {
    result += SignedNumber(strength.current_soldiers);
  } else {
    result += "null";
  }
  result += ",\"maximum_soldiers\":";
  if (strength.available) {
    result += SignedNumber(strength.maximum_soldiers);
  } else {
    result += "null";
  }
  result += ",\"ai_base_power_raw\":";
  if (strength.available) {
    result += SignedNumber(strength.ai_base_power_raw);
  } else {
    result += "null";
  }
  result += ",\"ai_base_power_scale\":";
  result += SignedNumber(strength.ai_base_power_scale);
  result += ",\"unavailable_reason\":";
  if (strength.available) {
    result += "null";
  } else {
    AppendJsonString(result, strength.unavailable_reason);
  }
  result += '}';
}

std::string_view CombatStatusName(
    xar::game::CombatObservationStatus status) noexcept {
  switch (status) {
  case xar::game::CombatObservationStatus::available:
    return "available";
  case xar::game::CombatObservationStatus::absent:
    return "absent";
  case xar::game::CombatObservationStatus::unavailable:
    return "unavailable";
  }
  return "unavailable";
}

void AppendUnavailableReason(std::string &result, bool unavailable,
                             std::string_view reason) {
  if (!unavailable) {
    result += "null";
  } else {
    AppendJsonString(result, reason);
  }
}

void AppendCombatMaaType(std::string &result,
                         const xar::game::CombatMaaTypeSnapshot &maa_type) {
  result += "{\"status\":";
  AppendJsonString(result, CombatStatusName(maa_type.status));
  result += ",\"key\":";
  if (maa_type.status == xar::game::CombatObservationStatus::available) {
    AppendJsonString(result, maa_type.key);
  } else {
    result += "null";
  }
  result += ",\"unavailable_reason\":";
  AppendUnavailableReason(
      result,
      maa_type.status == xar::game::CombatObservationStatus::unavailable,
      maa_type.unavailable_reason);
  result += '}';
}

void AppendCombatEffectiveStats(
    std::string &result,
    const xar::game::CombatEffectiveStatsSnapshot &stats) {
  result += "{\"status\":\"";
  result += stats.available ? "available" : "unavailable";
  result += "\",\"source_target_province_id\":";
  if (stats.available) {
    result += SignedNumber(stats.source_target_province_id);
  } else {
    result += "null";
  }
  result += ",\"max_size\":";
  result += stats.available ? SignedNumber(stats.max_size) : "null";
  result += ",\"siege_value_raw\":";
  result += stats.available ? SignedNumber(stats.siege_value_raw) : "null";
  result += ",\"damage_raw\":";
  result += stats.available ? SignedNumber(stats.damage_raw) : "null";
  result += ",\"toughness_raw\":";
  result += stats.available ? SignedNumber(stats.toughness_raw) : "null";
  result += ",\"pursuit_raw\":";
  result += stats.available ? SignedNumber(stats.pursuit_raw) : "null";
  result += ",\"screen_raw\":";
  result += stats.available ? SignedNumber(stats.screen_raw) : "null";
  result += ",\"scale\":";
  result += SignedNumber(stats.scale);
  result += ",\"unavailable_reason\":";
  AppendUnavailableReason(result, !stats.available, stats.unavailable_reason);
  result += '}';
}

void AppendCombatCounter(std::string &result,
                         const xar::game::CombatCounterSnapshot &counter) {
  const bool available =
      counter.status == xar::game::CombatObservationStatus::available;
  const bool unavailable =
      counter.status == xar::game::CombatObservationStatus::unavailable;
  result += "{\"status\":";
  AppendJsonString(result, CombatStatusName(counter.status));
  result += ",\"class_index\":";
  result += available ? SignedNumber(counter.class_index) : "null";
  result += ",\"current_chunk_raw\":";
  result += available ? SignedNumber(counter.current_chunk_raw) : "null";
  result += ",\"targets\":";
  if (unavailable) {
    result += "null";
  } else {
    result += '[';
    for (std::size_t index = 0; index < counter.targets.size(); ++index) {
      if (index != 0) {
        result += ',';
      }
      const auto &target = counter.targets[index];
      result += "{\"class_index\":";
      result += SignedNumber(target.class_index);
      result += ",\"effectiveness_raw\":";
      result += SignedNumber(target.effectiveness_raw);
      result += ",\"scale\":";
      result += SignedNumber(target.scale);
      result += '}';
    }
    result += ']';
  }
  result += ",\"scale\":";
  result += SignedNumber(counter.scale);
  result += ",\"unavailable_reason\":";
  AppendUnavailableReason(result, unavailable, counter.unavailable_reason);
  result += '}';
}

void AppendCombatRegiment(
    std::string &result,
    const xar::game::CombatRegimentSnapshot &regiment) {
  result += "{\"status\":\"";
  result += regiment.available ? "available" : "unavailable";
  result += "\",\"regiment_id\":";
  result += SignedNumber(regiment.regiment_id);
  result += ",\"identity_valid\":";
  result += regiment.identity_valid ? "true" : "false";
  result += ",\"current_soldiers\":";
  result += SignedNumber(regiment.current_soldiers);
  result += ",\"maximum_soldiers\":";
  result += SignedNumber(regiment.maximum_soldiers);
  result += ",\"maa_type\":";
  AppendCombatMaaType(result, regiment.maa_type);
  result += ",\"kind\":{\"status\":";
  AppendJsonString(result, CombatStatusName(regiment.kind.status));
  result += ",\"value\":";
  if (regiment.kind.status ==
      xar::game::CombatObservationStatus::available) {
    AppendJsonString(result, regiment.kind.value);
  } else {
    result += "null";
  }
  result += ",\"unavailable_reason\":";
  AppendUnavailableReason(
      result,
      regiment.kind.status ==
          xar::game::CombatObservationStatus::unavailable,
      regiment.kind.unavailable_reason);
  result += "},\"fights_in_main_phase\":";
  if (regiment.kind.status ==
      xar::game::CombatObservationStatus::available) {
    result += regiment.kind.fights_in_main_phase ? "true" : "false";
  } else {
    result += "null";
  }
  result += ",\"effective_stats\":";
  AppendCombatEffectiveStats(result, regiment.effective_stats);
  result += ",\"counter\":";
  AppendCombatCounter(result, regiment.counter);
  result += ",\"unavailable_reason\":";
  AppendUnavailableReason(result, !regiment.available,
                          regiment.unavailable_reason);
  result += '}';
}

void AppendCombatOwner(std::string &result,
                       const xar::game::CombatOwnerSnapshot &owner) {
  const bool available =
      owner.status == xar::game::CombatObservationStatus::available;
  result += "{\"status\":";
  AppendJsonString(result, CombatStatusName(owner.status));
  result += ",\"character_id\":";
  result += available ? SignedNumber(owner.character_id) : "null";
  result += ",\"counter_efficiency_raw\":";
  result += available ? SignedNumber(owner.counter_efficiency_raw) : "null";
  result += ",\"counter_resistance_raw\":";
  result += available ? SignedNumber(owner.counter_resistance_raw) : "null";
  result += ",\"scale\":";
  result += SignedNumber(owner.scale);
  result += ",\"unavailable_reason\":";
  AppendUnavailableReason(
      result,
      owner.status == xar::game::CombatObservationStatus::unavailable,
      owner.unavailable_reason);
  result += '}';
}

void AppendCombatCommander(
    std::string &result,
    const xar::game::CombatCommanderSnapshot &commander) {
  const bool available =
      commander.status == xar::game::CombatObservationStatus::available;
  result += "{\"status\":";
  AppendJsonString(result, CombatStatusName(commander.status));
  result += ",\"character_id\":";
  result += available ? SignedNumber(commander.character_id) : "null";
  result += ",\"generic_advantage_points\":";
  result += commander.generic_advantage_observable
                ? SignedNumber(commander.generic_advantage_points)
                : "null";
  const auto &context = commander.battle_context;
  result += ",\"battle_context\":{\"status\":\"";
  result += context.available ? "available" : "unavailable";
  result += "\",\"source_target_province_id\":";
  result += context.available ? SignedNumber(context.province_id) : "null";
  result += ",\"effective_min_roll\":";
  result += context.available ? SignedNumber(context.effective_min_roll)
                              : "null";
  result += ",\"effective_max_roll\":";
  result += context.available ? SignedNumber(context.effective_max_roll)
                              : "null";
  result += ",\"unavailable_reason\":";
  AppendUnavailableReason(result, !context.available,
                          context.unavailable_reason);
  result += "},\"unavailable_reason\":";
  AppendUnavailableReason(
      result,
      commander.status == xar::game::CombatObservationStatus::unavailable,
      commander.unavailable_reason);
  result += '}';
}

void AppendCombatKnights(std::string &result,
                         const xar::game::CombatKnightsSnapshot &knights) {
  result += "{\"status\":\"";
  result += knights.available ? "available" : "unavailable";
  result += "\",\"members\":";
  if (!knights.available) {
    result += "null";
  } else {
    result += '[';
    for (std::size_t index = 0; index < knights.members.size(); ++index) {
      if (index != 0) {
        result += ',';
      }
      const auto &knight = knights.members[index];
      result += "{\"eligible\":";
      result += knight.eligible ? "true" : "false";
      result += ",\"character_id\":";
      result += SignedNumber(knight.character_id);
      result += ",\"source_regiment_id\":";
      result += SignedNumber(knight.source_regiment_id);
      result += ",\"army_id\":";
      result += SignedNumber(knight.army_id);
      result += ",\"participant_army_membership_verified\":";
      result += knight.participant_army_membership_verified ? "true" : "false";
      result += ",\"prowess\":";
      result += SignedNumber(knight.prowess);
      result += ",\"knight_effectiveness_raw\":";
      result += SignedNumber(knight.knight_effectiveness_raw);
      result += ",\"effective_damage_raw\":";
      result += SignedNumber(knight.effective_damage_raw);
      result += ",\"effective_toughness_raw\":";
      result += SignedNumber(knight.effective_toughness_raw);
      result += ",\"scale\":";
      result += SignedNumber(knight.scale);
      result += '}';
    }
    result += ']';
  }
  result += ",\"unavailable_reason\":";
  AppendUnavailableReason(result, !knights.available,
                          knights.unavailable_reason);
  result += '}';
}

void AppendCombatArmy(std::string &result,
                      const xar::game::CombatArmyInputsSnapshot &army) {
  result += "{\"status\":\"";
  result += army.available ? "available" : "unavailable";
  result += "\",\"army_id\":";
  result += SignedNumber(army.army_id);
  result += ",\"native_carmy_id\":";
  result += army.native_carmy_id_observable ? SignedNumber(army.native_carmy_id)
                                           : "null";
  result += ",\"encounter_role\":";
  AppendJsonString(result, army.encounter_role);
  result += ",\"scope_role\":\"";
  switch (army.scope_role) {
  case xar::game::ArmyStrengthScopeRole::player:
    result += "player";
    break;
  case xar::game::ArmyStrengthScopeRole::active_war_ally:
    result += "active_war_ally";
    break;
  case xar::game::ArmyStrengthScopeRole::active_war_enemy:
    result += "active_war_enemy";
    break;
  }
  result += "\",\"war_ids\":";
  AppendInt32Array(result, army.war_ids);
  result += ",\"current_province_id\":";
  result += army.current_province_observable
                ? SignedNumber(army.current_province_id)
                : "null";
  result += ",\"owner\":";
  AppendCombatOwner(result, army.owner);
  result += ",\"commander\":";
  AppendCombatCommander(result, army.commander);
  result += ",\"regiments\":";
  if (!army.regiments_observable) {
    result += "null";
  } else {
    result += '[';
    for (std::size_t index = 0; index < army.regiments.size(); ++index) {
      if (index != 0) {
        result += ',';
      }
      AppendCombatRegiment(result, army.regiments[index]);
    }
    result += ']';
  }
  result += ",\"knights\":";
  AppendCombatKnights(result, army.knights);
  result += ",\"unavailable_reason\":";
  AppendUnavailableReason(result, !army.available, army.unavailable_reason);
  result += '}';
}

void AppendCombatTargetProvince(
    std::string &result,
    const xar::game::CombatCandidateProvinceSnapshot &province) {
  result += "{\"status\":\"";
  result += province.available ? "available" : "unavailable";
  result += "\",\"province_id\":";
  result += SignedNumber(province.province_id);
  result += ",\"terrain\":{\"status\":\"";
  result += province.terrain.available ? "available" : "unavailable";
  result += "\",\"key\":";
  if (province.terrain.available) {
    AppendJsonString(result, province.terrain.key);
  } else {
    result += "null";
  }
  result += ",\"combat_width_multiplier_raw\":";
  result += province.terrain.available
                ? SignedNumber(province.terrain.combat_width_multiplier_raw)
                : "null";
  result += ",\"scale\":";
  result += SignedNumber(province.terrain.scale);
  result += ",\"unavailable_reason\":";
  AppendUnavailableReason(result, !province.terrain.available,
                          province.terrain.unavailable_reason);
  result += "},\"crossing\":{\"status\":\"";
  result += province.crossing.available ? "available" : "unavailable";
  result += "\",\"kind\":";
  if (province.crossing.available) {
    AppendJsonString(result, province.crossing.kind);
  } else {
    result += "null";
  }
  result += ",\"unavailable_reason\":";
  AppendUnavailableReason(result, !province.crossing.available,
                          province.crossing.unavailable_reason);
  result += "},\"defender_context\":{\"status\":\"";
  result += province.defender_context.available ? "available" : "unavailable";
  result += "\",\"defender_side\":";
  if (province.defender_context.available) {
    AppendJsonString(result, province.defender_context.defender_side);
  } else {
    result += "null";
  }
  result += ",\"holding_defender_status\":";
  AppendJsonString(
      result,
      CombatStatusName(province.defender_context.holding_defender_status));
  result += ",\"holding_defender\":";
  result += province.defender_context.holding_defender_status ==
                    xar::game::CombatObservationStatus::available
                ? (province.defender_context.holding_defender ? "true"
                                                              : "false")
                : "null";
  result += ",\"holding_unavailable_reason\":";
  AppendUnavailableReason(
      result,
      province.defender_context.holding_defender_status ==
          xar::game::CombatObservationStatus::unavailable,
      province.defender_context.holding_unavailable_reason);
  result += ",\"unavailable_reason\":";
  AppendUnavailableReason(result, !province.defender_context.available,
                          province.defender_context.unavailable_reason);
  result += "},\"precontact_width\":{\"status\":\"";
  result += province.precontact_width.available ? "available" : "unavailable";
  result += "\",\"base\":";
  result += province.precontact_width.available
                ? SignedNumber(province.precontact_width.base)
                : "null";
  result += ",\"final\":";
  result += province.precontact_width.available
                ? SignedNumber(province.precontact_width.final)
                : "null";
  result += ",\"unavailable_reason\":";
  AppendUnavailableReason(result, !province.precontact_width.available,
                          province.precontact_width.unavailable_reason);
  result += "},\"unavailable_reason\":";
  AppendUnavailableReason(result, !province.available,
                          province.unavailable_reason);
  result += '}';
}

void AppendOngoingCombat(
    std::string &result,
    const xar::game::OngoingCombatInputsSnapshot &combat) {
  result += "{\"status\":\"";
  result += combat.available ? "available" : "unavailable";
  result += "\",\"combat_id\":";
  result += combat.combat_id_observable ? SignedNumber(combat.combat_id)
                                       : "null";
  result += ",\"province_id\":";
  result += combat.available ? SignedNumber(combat.province_id) : "null";
  result += ",\"phase\":";
  result += combat.available ? SignedNumber(combat.phase) : "null";
  result += ",\"phase_day\":";
  result += combat.available ? SignedNumber(combat.phase_day) : "null";
  result += ",\"base_combat_width\":";
  result += combat.available ? SignedNumber(combat.base_combat_width) : "null";
  result += ",\"final_combat_width\":";
  result += combat.available ? SignedNumber(combat.final_combat_width) : "null";
  result += ",\"side_0_roll\":";
  result += combat.available ? SignedNumber(combat.side_0_roll) : "null";
  result += ",\"side_1_roll\":";
  result += combat.available ? SignedNumber(combat.side_1_roll) : "null";
  result += ",\"base_advantage\":";
  result += combat.available ? SignedNumber(combat.base_advantage) : "null";
  result += ",\"resolved_advantage\":";
  result += combat.available ? SignedNumber(combat.resolved_advantage) : "null";
  result += ",\"orientation\":";
  if (combat.available) {
    AppendJsonString(result, combat.orientation);
  } else {
    result += "null";
  }
  result += ",\"unavailable_reason\":";
  AppendUnavailableReason(result, !combat.available, combat.unavailable_reason);
  result += '}';
}

void AppendCounterResolution(
    std::string &result,
    const xar::game::CombatCounterResolutionSnapshot &resolution) {
  result += "{\"status\":\"";
  result += resolution.available ? "available" : "unavailable";
  result += "\",\"countered_side\":";
  AppendJsonString(result, resolution.countered_side);
  result += ",\"countering_side\":";
  AppendJsonString(result, resolution.countering_side);
  result += ",\"countered_modifier_owner_character_id\":";
  result += resolution.available
                ? SignedNumber(resolution.countered_modifier_owner_character_id)
                : "null";
  result += ",\"countering_modifier_owner_character_id\":";
  result += resolution.available
                ? SignedNumber(resolution.countering_modifier_owner_character_id)
                : "null";
  result += ",\"context_scale_raw\":";
  result += resolution.available ? SignedNumber(resolution.context_scale_raw)
                                 : "null";
  result += ",\"class_count\":";
  result += SignedNumber(resolution.class_count);
  result += ",\"damage_retention_by_class_raw\":";
  if (!resolution.available) {
    result += "null";
  } else {
    result += '[';
    for (std::size_t index = 0;
         index < resolution.damage_retention_by_class_raw.size(); ++index) {
      if (index != 0) {
        result += ',';
      }
      result += SignedNumber(
          resolution.damage_retention_by_class_raw[index]);
    }
    result += ']';
  }
  result += ",\"scale\":";
  result += SignedNumber(resolution.scale);
  result += ",\"unavailable_reason\":";
  AppendUnavailableReason(result, !resolution.available,
                          resolution.unavailable_reason);
  result += '}';
}

void AppendCombatSimulationInputs(
    std::string &result,
    const xar::game::CombatSimulationInputsSnapshot &snapshot) {
  result += "{\"target_province_id\":";
  result += SignedNumber(snapshot.target_province_id);
  result += ",\"participant_policy\":"
            "\"explicit_hypothetical_fixed_at_contact_no_reinforcements\",";
  result += "\"scenario\":{\"kind\":"
            "\"explicit_hypothetical_contact\",\"attacker_entry_province_id\":";
  result += SignedNumber(snapshot.scenario.attacker_entry_province_id);
  result += ",\"attacker_army_ids\":";
  AppendInt32Array(result, snapshot.scenario.attacker_army_ids);
  result += ",\"defender_army_ids\":";
  AppendInt32Array(result, snapshot.scenario.defender_army_ids);
  result += ",\"attacker_side\":";
  AppendJsonString(result, snapshot.scenario.attacker_side);
  result += ",\"defender_side\":";
  AppendJsonString(result, snapshot.scenario.defender_side);
  result += ",\"attacker_position_policy\":"
            "\"fixed_at_entry_hypothetical\","
            "\"defender_position_policy\":"
            "\"fixed_at_target_hypothetical\","
            "\"defender_insertion_order_policy\":"
            "\"explicit_request_order_hypothetical\","
            "\"actual_route_dependency\":false},\"armies\":[";
  for (std::size_t index = 0; index < snapshot.armies.size(); ++index) {
    if (index != 0) {
      result += ',';
    }
    AppendCombatArmy(result, snapshot.armies[index]);
  }
  result += "],\"target_province\":";
  AppendCombatTargetProvince(result, snapshot.target_province);
  result += ",\"ongoing_combats\":[";
  for (std::size_t index = 0; index < snapshot.ongoing_combats.size(); ++index) {
    if (index != 0) {
      result += ',';
    }
    AppendOngoingCombat(result, snapshot.ongoing_combats[index]);
  }
  result += "],\"counter_resolutions\":[";
  for (std::size_t index = 0; index < snapshot.counter_resolutions.size();
       ++index) {
    if (index != 0) {
      result += ',';
    }
    AppendCounterResolution(result, snapshot.counter_resolutions[index]);
  }
  result += "],\"completeness\":{\"observation_slice\":"
            "\"precontact-composition-context-v2\",";
  result += "\"input_observation_ready\":";
  result += snapshot.input_observation_ready ? "true" : "false";
  result += ",\"monte_carlo_ready\":";
  result += snapshot.monte_carlo_ready ? "true" : "false";
  result += ",\"missing_required_domains\":[";
  for (std::size_t index = 0;
       index < snapshot.missing_required_domains.size(); ++index) {
    if (index != 0) {
      result += ',';
    }
    AppendJsonString(result, snapshot.missing_required_domains[index]);
  }
  result += "]}}";
}

void AppendCombatSimulationInputsV3(
    std::string &result,
    const xar::game::CombatSimulationInputsV3Snapshot &snapshot) {
  result += "{\"schema_version\":3,\"contract_stage\":"
            "\"production_exact_132_refs\",\"rules_manifest_sha256\":";
  AppendJsonString(result, xar::game::kCombatPhaseManifestSha256);
  result += ",\"base_inputs\":";
  AppendCombatSimulationInputs(result, snapshot.base_inputs);
  result += ",\"phase_event_inputs\":";
  result += xar::ck3_11906::SerializeCombatPhaseInputsV3(
      snapshot.phase_event_inputs);
  result += '}';
}

void AppendFixedPoint(std::string &result,
                      const xar::game::FixedPointValue &value) {
  result += "{\"raw\":";
  result += SignedNumber(value.raw);
  result += ",\"scale\":";
  result += SignedNumber(value.scale);
  result += '}';
}

void AppendWarObjectiveProvinceState(
    std::string &result,
    const xar::game::WarObjectiveProvinceState &state) {
  result += "{\"province_id\":";
  result += SignedNumber(state.province_id);
  result += ",\"occupation_observable\":";
  result += state.occupation_observable ? "true" : "false";
  result += ",\"is_occupied\":";
  if (!state.occupation_observable) {
    result += "null";
  } else {
    result += state.is_occupied ? "true" : "false";
  }
  result += ",\"occupying_character_id\":";
  if (!state.occupation_observable || !state.is_occupied ||
      state.occupying_character_id == -1) {
    result += "null";
  } else {
    result += SignedNumber(state.occupying_character_id);
  }
  result += ",\"fort_level\":";
  if (!state.fort_level_observable) {
    result += "null";
  } else {
    result += SignedNumber(state.fort_level);
  }
  result += ",\"garrison_size\":";
  if (!state.garrison_size_observable) {
    result += "null";
  } else {
    result += SignedNumber(state.garrison_size);
  }
  result += ",\"besieging_strength\":";
  if (!state.besieging_strength_observable) {
    result += "null";
  } else {
    result += SignedNumber(state.besieging_strength);
  }
  result += ",\"siege_observable\":";
  result += state.siege_observable ? "true" : "false";
  result += ",\"active_siege\":";
  if (!state.siege_observable || !state.has_active_siege) {
    result += "null";
  } else {
    result += "{\"siege_id\":";
    result += SignedNumber(state.siege_id);
    result += ",\"besieging_army_id\":";
    if (state.besieging_army_id == -1) {
      result += "null";
    } else {
      result += SignedNumber(state.besieging_army_id);
    }
    result += ",\"player_army_besieging\":";
    result += state.player_army_besieging ? "true" : "false";
    result += ",\"progress_fraction\":";
    AppendFixedPoint(result, state.siege_progress_fraction);
    result += ",\"current_work\":";
    AppendFixedPoint(result, state.siege_current_work);
    result += ",\"total_work\":";
    AppendFixedPoint(result, state.siege_total_work);
    result += ",\"days_left\":";
    if (!state.siege_days_left_observable) {
      result += "null";
    } else {
      result += SignedNumber(state.siege_days_left);
    }
    result += ",\"assault_observable\":";
    result += state.assault_observable ? "true" : "false";
    result += ",\"breach_level\":";
    if (!state.assault_observable) {
      result += "null";
    } else {
      result += SignedNumber(state.breach_level);
    }
    result += ",\"assault_in_progress\":";
    if (!state.assault_observable) {
      result += "null";
    } else {
      result += state.assault_in_progress ? "true" : "false";
    }
    result += ",\"can_start_assault\":";
    if (!state.assault_observable) {
      result += "null";
    } else {
      result += state.can_start_assault ? "true" : "false";
    }
    result += ",\"can_stop_assault\":";
    if (!state.assault_observable) {
      result += "null";
    } else {
      result += state.can_stop_assault ? "true" : "false";
    }
    result += ",\"assault_daily_progress\":";
    if (!state.assault_observable) {
      result += "null";
    } else {
      AppendFixedPoint(result, state.assault_daily_progress);
    }
    result += ",\"assault_daily_casualties\":";
    if (!state.assault_observable) {
      result += "null";
    } else {
      result += SignedNumber(state.assault_daily_casualties);
    }
    result += '}';
  }
  result += '}';
}

void AppendWarObjectiveProvinceStates(
    std::string &result,
    const std::vector<xar::game::WarObjectiveProvinceState> &states) {
  result += '[';
  for (std::size_t index = 0; index < states.size(); ++index) {
    if (index != 0) {
      result += ',';
    }
    AppendWarObjectiveProvinceState(result, states[index]);
  }
  result += ']';
}

void AppendOneLifeSettlement(
    std::string &result,
    const xar::game::OneLifeSettlementSnapshot &settlement) {
  result += "{\"ready\":";
  result += settlement.ready ? "true" : "false";
  result += ",\"commit_serial\":";
  result += SignedNumber(settlement.commit_serial);
  result += ",\"source_character_id\":";
  result += SignedNumber(settlement.source_character_id);
  result += ",\"final_score\":";
  AppendFixedPoint(result, settlement.final_score);
  result += ",\"score_before_reject\":";
  AppendFixedPoint(result, settlement.score_before_reject);
  result += ",\"record_candidate\":";
  result += SignedNumber(settlement.record_candidate);
  result += ",\"old_record\":";
  result += SignedNumber(settlement.old_record);
  result += ",\"record_delta\":";
  result += SignedNumber(settlement.record_delta);
  result += ",\"blessing_count\":";
  result += SignedNumber(settlement.blessing_count);
  result += ",\"refusal_count\":";
  result += SignedNumber(settlement.refusal_count);
  result += ",\"contract_progress\":";
  result += SignedNumber(settlement.contract_progress);
  result += ",\"record_written\":";
  result += settlement.record_written ? "true" : "false";
  result += '}';
}

std::string DeclarationId(
    const xar::game::DeclarableWarSnapshot &declaration) {
  std::string result = SignedNumber(declaration.target_character_id);
  result += '-';
  result += SignedNumber(declaration.casus_belli_index);
  result += '-';
  result += SignedNumber(declaration.configuration_index);
  return result;
}

std::string DeclarationStep(
    const xar::game::DeclarableWarSnapshot &declaration) {
  return "declare-war-" + DeclarationId(declaration);
}

void AppendDeclaration(
    std::string &result,
    const xar::game::DeclarableWarSnapshot &declaration) {
  result += "{\"declaration_id\":\"";
  result += DeclarationId(declaration);
  result += "\",\"target_character_id\":";
  result += SignedNumber(declaration.target_character_id);
  result += ",\"casus_belli_index\":";
  result += SignedNumber(declaration.casus_belli_index);
  result += ",\"casus_belli_key\":";
  AppendJsonString(result, declaration.casus_belli_key);
  result += ",\"configuration_index\":";
  result += SignedNumber(declaration.configuration_index);
  result += ",\"claimant_character_id\":";
  result += SignedNumber(declaration.claimant_character_id);
  result += ",\"target_title_ids\":[";
  for (std::size_t index = 0; index < declaration.target_title_ids.size();
       ++index) {
    if (index != 0) {
      result += ',';
    }
    result += SignedNumber(declaration.target_title_ids[index]);
  }
  result += "]}";
}

void AppendWarTerminationOption(
    std::string &result,
    const xar::game::WarTerminationOptionSnapshot &option) {
  result += "{\"outcome\":";
  AppendJsonString(result, option.outcome);
  result += ",\"hostage_variant\":\"none\",";
  result += "\"context_constructed\":";
  result += option.context_constructed ? "true" : "false";
  result += ",\"native_validator_passed\":";
  if (option.native_validator_observable) {
    result += option.native_validator_passed ? "true" : "false";
  } else {
    result += "null";
  }
  result += ",\"available\":";
  result += option.context_constructed &&
                    option.native_validator_observable &&
                    option.native_validator_passed
                ? "true"
                : "false";
  result +=
      ",\"terms_observable\":false,\"terms\":{"
      "\"status\":\"unavailable\","
      "\"reason\":\"cb_specific_terms_not_observable\"},";
  result += "\"ai_acceptance_observable\":";
  result += option.ai_acceptance_observable ? "true" : "false";
  result += ",\"ai_acceptance\":";
  if (option.ai_acceptance_observable) {
    AppendFixedPoint(result, option.ai_acceptance);
  } else {
    result += "null";
  }
  result += ",\"auto_accept_observable\":";
  result += option.auto_accept_observable ? "true" : "false";
  result += ",\"auto_accept\":";
  if (option.auto_accept_observable) {
    result += option.auto_accept ? "true" : "false";
  } else {
    result += "null";
  }
  result += ",\"recipient_response\":{\"status\":\"";
  result += option.recipient_response.observable ? "available" : "unavailable";
  result += "\",\"decision_status_raw\":";
  if (option.recipient_response.observable) {
    result += SignedNumber(option.recipient_response.decision_status_raw);
  } else {
    result += "null";
  }
  result += ",\"would_accept_now\":";
  if (option.recipient_response.observable) {
    result += option.recipient_response.would_accept_now ? "true" : "false";
  } else {
    result += "null";
  }
  result += '}';
  result += '}';
}

void AppendWarTerminationOptions(
    std::string &result,
    const xar::game::WarTerminationOptionsSnapshot &options) {
  result += "{\"war_id\":";
  result += SignedNumber(options.war_id);
  result += ",\"player_side\":\"";
  result += options.player_side == xar::game::PlayerWarSide::attacker
                ? "attacker"
                : "defender";
  result += "\",\"player_is_primary_war_leader\":";
  result += options.player_is_primary_war_leader ? "true" : "false";
  result += ",\"player_relative_war_score\":";
  result += SignedNumber(options.player_relative_war_score);
  result += ",\"war_duration_days\":";
  if (options.war_duration_days_observable) {
    result += SignedNumber(options.war_duration_days);
  } else {
    result += "null";
  }
  result += ",\"absolute_war_scores_observable\":";
  result += options.absolute_war_scores_observable ? "true" : "false";
  result += ",\"attacker_war_score\":";
  if (options.absolute_war_scores_observable) {
    result += SignedNumber(options.attacker_war_score);
  } else {
    result += "null";
  }
  result += ",\"defender_war_score\":";
  if (options.absolute_war_scores_observable) {
    result += SignedNumber(options.defender_war_score);
  } else {
    result += "null";
  }
  result += ",\"war_score_breakdown\":";
  if (!options.war_score_breakdown.observable) {
    result += "null";
  } else {
    result += "{\"imprisonment\":";
    result += SignedNumber(options.war_score_breakdown.imprisonment);
    result += ",\"battles\":";
    result += SignedNumber(options.war_score_breakdown.battles);
    result += ",\"occupation\":";
    result += SignedNumber(options.war_score_breakdown.occupation);
    result += ",\"ticking\":";
    result += SignedNumber(options.war_score_breakdown.ticking);
    result += '}';
  }
  result += ",\"active_casus_belli_present\":";
  if (options.active_casus_belli_observable) {
    result += options.active_casus_belli_present ? "true" : "false";
  } else {
    result += "null";
  }
  result += ",\"active_casus_belli_identity\":";
  if (!options.active_casus_belli_identity_observable) {
    result += "null";
  } else {
    result += "{\"database_index\":";
    result += SignedNumber(options.active_casus_belli_database_index);
    result += ",\"canonical_key\":";
    AppendJsonString(result, options.active_casus_belli_key);
    result += '}';
  }
  result += ",\"cb_allows_white_peace\":";
  if (options.white_peace_permission_observable) {
    result += options.cb_allows_white_peace ? "true" : "false";
  } else {
    result += "null";
  }
  result += ",\"options\":{";
  result += "\"surrender\":";
  AppendWarTerminationOption(result, options.surrender);
  result += ",\"white_peace\":";
  AppendWarTerminationOption(result, options.white_peace);
  result += ",\"victory\":";
  AppendWarTerminationOption(result, options.victory);
  result += "}}";
}

std::string MarriageChoiceId(
    const xar::game::ArrangeMarriageChoice &choice) {
  std::string result = SignedNumber(choice.played_character_id);
  result += '-';
  result += SignedNumber(choice.candidate_character_id);
  return result;
}

std::string MarriageStep(
    const xar::game::ArrangeMarriageChoice &choice) {
  return "arrange-marriage-" + MarriageChoiceId(choice);
}

void AppendMarriageChoice(
    std::string &result,
    const xar::game::ArrangeMarriageChoice &choice) {
  result += "{\"choice_id\":\"";
  result += MarriageChoiceId(choice);
  result += "\",\"played_character_id\":";
  result += SignedNumber(choice.played_character_id);
  result += ",\"candidate_character_id\":";
  result += SignedNumber(choice.candidate_character_id);
  result += '}';
}

void AppendWarClaimDisposition(
    std::string &result,
    const xar::game::WarClaimDispositionSnapshot &disposition) {
  result += "{\"declared_title_disposition\":";
  AppendJsonString(result, disposition.declared_title_disposition);
  result += ",\"claim_disposition\":";
  AppendJsonString(result, disposition.claim_disposition);
  result += '}';
}

void AppendWarTerminationTermsProvenance(std::string &result) {
  result +=
      "{\"game_version\":\"1.19.0.6\","
      "\"executable_sha256\":"
      "\"2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86\","
      "\"native_reader\":\"CWar+0x270/+0x290;0x28B1AA0\","
      "\"present_claim_lifecycle\":"
      "\"present_only_vtable_slot_0_delete_flags_0\","
      "\"claim_script_sha256\":"
      "\"D9AA37BDC45F81B4F6185B2697A3EBD09404084EA0D3CF77BBE3C1D2C962E8B1\"}";
}

void AppendWarTerminationTerms(
    std::string &result,
    const xar::game::WarTerminationTermsSnapshot &terms,
    bool supported) {
  result += "{\"schema_version\":1,\"status\":\"";
  result += supported ? "available" : "unsupported";
  result += "\",\"war_id\":";
  result += SignedNumber(terms.war_id);
  result += ",\"casus_belli\":{\"database_index\":";
  result += SignedNumber(terms.active_casus_belli_database_index);
  result += ",\"canonical_key\":";
  AppendJsonString(result, terms.active_casus_belli_key);
  result +=
      "},\"supported_slice\":\"claim_cb_claim_disposition\",";
  if (!supported) {
    result +=
        "\"reason\":\"casus_belli_not_claim_cb\","
        "\"readiness\":{\"ready\":false},\"provenance\":";
    AppendWarTerminationTermsProvenance(result);
    result += '}';
    return;
  }

  result += "\"claimant_character_id\":";
  result += SignedNumber(terms.claimant_character_id);
  result += ",\"target_title_ids\":[";
  for (std::size_t index = 0; index < terms.target_title_ids.size(); ++index) {
    if (index != 0) {
      result += ',';
    }
    result += SignedNumber(terms.target_title_ids[index]);
  }
  result += "],\"claims\":[";
  for (std::size_t index = 0; index < terms.claims.size(); ++index) {
    if (index != 0) {
      result += ',';
    }
    const auto &claim = terms.claims[index];
    result += "{\"title_id\":";
    result += SignedNumber(claim.title_id);
    result += ",\"present\":";
    result += claim.present ? "true" : "false";
    if (claim.present) {
      result += ",\"strong\":";
      result += claim.strong ? "true" : "false";
      result += ",\"implicit\":";
      result += claim.implicit ? "true" : "false";
    }
    result += ",\"state\":";
    AppendJsonString(result, claim.state);
    result += '}';
  }
  result += "],\"outcomes\":{\"attacker_victory\":";
  AppendWarClaimDisposition(result, terms.attacker_victory);
  result += ",\"white_peace\":";
  AppendWarClaimDisposition(result, terms.white_peace);
  result += ",\"attacker_defeat\":";
  AppendWarClaimDisposition(result, terms.attacker_defeat);
  result +=
      "},\"readiness\":{\"identity_ready\":true,"
      "\"targets_ready\":true,\"claim_rows_ready\":true,"
      "\"claim_disposition_ready\":true,\"ready\":true},"
      "\"provenance\":";
  AppendWarTerminationTermsProvenance(result);
  result += '}';
}

void AppendMarriageQueryDiagnostics(
    std::string &result,
    const xar::game::ArrangeMarriageQueryDiagnostics &diagnostics) {
  result += "{\"storage_capacity\":";
  result += SignedNumber(diagnostics.storage_capacity);
  result += ",\"slots_scanned\":";
  result += SignedNumber(diagnostics.slots_scanned);
  result += ",\"empty_slots\":";
  result += SignedNumber(diagnostics.empty_slots);
  result += ",\"live_candidates\":";
  result += SignedNumber(diagnostics.live_candidates);
  result += ",\"dead_candidates\":";
  result += SignedNumber(diagnostics.dead_candidates);
  result += ",\"self_candidates\":";
  result += SignedNumber(diagnostics.self_candidates);
  result += ",\"generation_mismatch_candidates\":";
  result += SignedNumber(diagnostics.generation_mismatch_candidates);
  result += ",\"contexts_constructed\":";
  result += SignedNumber(diagnostics.contexts_constructed);
  result += ",\"context_construct_failures\":";
  result += SignedNumber(diagnostics.context_construct_failures);
  result += ",\"native_validate_true\":";
  result += SignedNumber(diagnostics.native_validate_true);
  result += ",\"native_validate_false\":";
  result += SignedNumber(diagnostics.native_validate_false);
  result += ",\"validation_false_samples\":[";
  for (std::size_t index = 0;
       index < diagnostics.validation_false_samples.size(); ++index) {
    if (index != 0) {
      result += ',';
    }
    const auto &sample = diagnostics.validation_false_samples[index];
    result += "{\"slot_index\":";
    result += SignedNumber(sample.slot_index);
    result += ",\"candidate_character_id\":";
    result += SignedNumber(sample.candidate_character_id);
    result += ",\"actor_character_id\":";
    result += SignedNumber(sample.actor_character_id);
    result += ",\"recipient_character_id\":";
    result += SignedNumber(sample.recipient_character_id);
    result += ",\"secondary_actor_character_id\":";
    result += SignedNumber(sample.secondary_actor_character_id);
    result += ",\"secondary_recipient_character_id\":";
    result += SignedNumber(sample.secondary_recipient_character_id);
    result += ",\"intermediary_character_id\":";
    result += SignedNumber(sample.intermediary_character_id);
    result += '}';
  }
  result += "]}";
}

std::string StateSnapshotFrame(const xar::game::Snapshot &snapshot,
                               std::uint64_t revision,
                               const CheckpointSubmission &checkpoint) {
  std::string result = "{\"type\":\"state_snapshot\",\"protocol_version\":1,"
                       "\"snapshot_id\":\"native:";
  result += Number(revision);
  result += "\",\"revision\":";
  result += Number(revision);
  result += ",\"state\":{\"date_raw\":";
  result += SignedNumber(snapshot.date_raw);
  result += ",\"speed\":";
  result += SignedNumber(snapshot.speed);
  result += ",\"paused\":";
  result += snapshot.paused ? "true" : "false";
  // This is Jomini's 32-bit local/network player id used by
  // CPauseGameCommand, not CK3's played-character CharacterID.
  result += ",\"local_player_id\":";
  result += SignedNumber(snapshot.player_id);
  result += ",\"map_ready\":";
  result += snapshot.map_ready ? "true" : "false";
  result += ",\"played_character\":";
  if (!snapshot.has_played_character) {
    result += "null";
  } else {
    result += "{\"character_id\":";
    result += SignedNumber(snapshot.played_character_id);
    result += ",\"alive\":";
    result += snapshot.played_character_alive ? "true" : "false";
    result += ",\"betrothed_id\":";
    if (snapshot.played_character_betrothed_id == -1) {
      result += "null";
    } else {
      result += SignedNumber(snapshot.played_character_betrothed_id);
    }
    result += ",\"primary_spouse_id\":";
    if (snapshot.played_character_primary_spouse_id == -1) {
      result += "null";
    } else {
      result += SignedNumber(snapshot.played_character_primary_spouse_id);
    }
    result += ",\"spouse_ids\":[";
    for (std::size_t index = 0;
         index < snapshot.played_character_spouse_ids.size(); ++index) {
      if (index != 0) {
        result += ',';
      }
      result += SignedNumber(snapshot.played_character_spouse_ids[index]);
    }
    result += ']';
    result += '}';
  }
  result += ",\"one_life_settlement\":";
  if (!snapshot.has_one_life_settlement) {
    result += "null";
  } else {
    AppendOneLifeSettlement(result, snapshot.one_life_settlement);
  }
  result += ",\"active_event\":";
  if (!snapshot.has_active_event) {
    result += "null";
  } else {
    result += "{\"instance_id\":";
    result += SignedNumber(snapshot.active_event_instance_id);
    result += ",\"option_count\":";
    result += SignedNumber(snapshot.active_event_option_count);
    result += ",\"option_indexes\":[";
    for (std::int32_t public_index = 1;
         public_index <= snapshot.active_event_option_count; ++public_index) {
      if (public_index != 1) {
        result += ',';
      }
      result += SignedNumber(public_index);
    }
    result += "]}";
  }
  result += ",\"pending_character_interaction\":";
  if (!snapshot.has_pending_character_interaction) {
    result += "null";
  } else {
    result += "{\"instance_id\":";
    result += SignedNumber(snapshot.pending_character_interaction_id);
    result += ",\"sender_character_id\":";
    result += SignedNumber(snapshot.pending_sender_character_id);
    result += ",\"auto_accept_notification\":";
    result += snapshot.pending_auto_accept_notification ? "true" : "false";
    result += '}';
  }
  result += ",\"active_wars\":[";
  for (std::size_t index = 0; index < snapshot.active_wars.size(); ++index) {
    if (index != 0) {
      result += ',';
    }
    const auto &war = snapshot.active_wars[index];
    result += "{\"war_id\":";
    result += SignedNumber(war.war_id);
    result += ",\"player_side\":\"";
    result += war.player_side == xar::game::PlayerWarSide::attacker
                  ? "attacker"
                  : "defender";
    result += "\",\"primary_opponent_character_id\":";
    if (war.primary_opponent_character_id == -1) {
      result += "null";
    } else {
      result += SignedNumber(war.primary_opponent_character_id);
    }
    result += ",\"player_is_primary_war_leader\":";
    result += war.player_is_primary_war_leader ? "true" : "false";
    result += ",\"targeted_title_ids\":";
    AppendInt32Array(result, war.targeted_title_ids);
    result += ",\"war_objective_province_ids\":";
    AppendInt32Array(result, war.war_objective_province_ids);
    result += ",\"objective_province_states\":";
    AppendWarObjectiveProvinceStates(result,
                                     war.objective_province_states);
    result += ",\"enemy_primary_default_raise_province_id\":";
    if (war.enemy_primary_default_raise_province_id < 1) {
      result += "null";
    } else {
      result +=
          SignedNumber(war.enemy_primary_default_raise_province_id);
    }
    result += ",\"player_relative_war_score\":";
    result += SignedNumber(war.player_relative_war_score);
    result += ",\"allied_armies\":";
    AppendArmyArray(result, war.allied_armies);
    result += ",\"enemy_armies\":";
    AppendArmyArray(result, war.enemy_armies);
    result += '}';
  }
  result += "],\"player_armies\":";
  AppendArmyArray(result, snapshot.player_armies);
  result += ",\"last_checkpoint_submission\":";
  if (checkpoint.sequence == 0) {
    result += "null";
  } else {
    result += "{\"sequence\":";
    result += Number(checkpoint.sequence);
    result += ",\"requested_save_name\":\"";
    result += checkpoint.save_name;
    result += "\",\"date_raw\":";
    result += SignedNumber(checkpoint.date_raw);
    result += ",\"status\":\"submitted\"}";
  }
  result += ",\"history\":[]}}";
  return result;
}

std::string SnapshotPublishDiagnosticFrame(
    std::string_view request_id, std::string_view phase,
    const SnapshotPublishDiagnostics &diagnostics) {
  std::string result =
      "{\"type\":\"snapshot_publish_diagnostic\","
      "\"protocol_version\":1,\"request_id\":";
  AppendJsonString(result, request_id);
  result += ",\"phase\":";
  AppendJsonString(result, phase);
  result += ",\"status\":";
  AppendJsonString(result, diagnostics.status);
  result += ",\"revision\":";
  result += Number(diagnostics.revision);
  result += ",\"payload_bytes\":";
  result += Number(diagnostics.payload_bytes);
  result += '}';
  return result;
}

std::string CommandResultFrame(std::string_view request_id,
                               std::string_view step, bool ok,
                               std::string_view status) {
  std::string result = "{\"type\":\"command_result\",\"protocol_version\":1,"
                       "\"request_id\":\"";
  result += request_id;
  result += "\",\"ok\":";
  result += ok ? "true" : "false";
  if (ok) {
    result += ",\"result\":{\"step\":\"";
    result += step;
    result += "\",\"accepted\":true,\"status\":\"";
    result += status;
    result += "\"}}";
  } else {
    result += ",\"error\":\"";
    result += status;
    result += "\"}";
  }
  return result;
}

std::string_view TacticalDailySentinelStateName(
    xar::ck3_11906::TacticalDailySentinelStateV1 state) noexcept {
  using State = xar::ck3_11906::TacticalDailySentinelStateV1;
  switch (state) {
  case State::idle:
    return "idle";
  case State::armed:
    return "armed";
  case State::triggered:
    return "triggered";
  case State::failed:
    return "failed";
  case State::unavailable:
  default:
    return "unavailable";
  }
}

std::string_view TacticalDailySentinelModeName(
    xar::ck3_11906::TacticalDailySentinelModeV1 mode) noexcept {
  using Mode = xar::ck3_11906::TacticalDailySentinelModeV1;
  return mode == Mode::terminal_or_sentinel ? "terminal_or_sentinel"
                                             : "decision_epoch";
}

void AppendTacticalDailySentinelTriggerReasons(
    std::string &result, std::uint32_t flags) {
  using namespace xar::ck3_11906;
  struct Entry {
    std::uint32_t flag;
    std::string_view name;
  };
  constexpr std::array<Entry, 16> entries{{
      {tactical_daily_trigger_date_deadline, "date_deadline"},
      {tactical_daily_trigger_army_unavailable, "army_unavailable"},
      {tactical_daily_trigger_route_target_changed,
       "route_target_changed"},
      {tactical_daily_trigger_combat_transition, "combat_transition"},
      {tactical_daily_trigger_retreat_transition, "retreat_transition"},
      {tactical_daily_trigger_combat_unavailable, "combat_unavailable"},
      {tactical_daily_trigger_combat_phase_changed,
       "combat_phase_changed"},
      {tactical_daily_trigger_combat_roster_changed,
       "combat_roster_changed"},
      {tactical_daily_trigger_combat_terminal, "combat_terminal"},
      {tactical_daily_trigger_date_sequence_failure,
       "date_sequence_failure"},
      {tactical_daily_trigger_world_identity_changed,
       "world_identity_changed"},
      {tactical_daily_trigger_pause_not_observed, "pause_not_observed"},
      {tactical_daily_trigger_original_unavailable,
       "original_unavailable"},
      {tactical_daily_trigger_native_pause, "native_pause"},
      {tactical_daily_trigger_combat_winner_changed,
       "combat_winner_changed"},
      {tactical_daily_trigger_evaluation_failure, "evaluation_failure"},
  }};
  result += '[';
  bool first = true;
  for (const auto &entry : entries) {
    if ((flags & entry.flag) == 0) {
      continue;
    }
    if (!first) {
      result += ',';
    }
    AppendJsonString(result, entry.name);
    first = false;
  }
  result += ']';
}

std::string TacticalDailySentinelResultFrame(
    std::string_view request_id, std::string_view step,
    const xar::ck3_11906::TacticalDailySentinelStatusV1 &status) {
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":";
  AppendJsonString(result, request_id);
  result += ",\"ok\":true,\"result\":{\"step\":";
  AppendJsonString(result, step);
  result += ",\"accepted\":true,\"status\":\"available\","
            "\"tactical_daily_sentinel\":{\"state\":";
  AppendJsonString(result, TacticalDailySentinelStateName(status.state));
  result += ",\"generation\":";
  result += Number(status.generation);
  result += ",\"starting_date_raw\":";
  result += SignedNumber(status.starting_date_raw);
  result += ",\"target_date_raw\":";
  result += SignedNumber(status.target_date_raw);
  result += ",\"last_observed_date_raw\":";
  result += SignedNumber(status.last_observed_date_raw);
  result += ",\"trigger_date_raw\":";
  result += SignedNumber(status.trigger_date_raw);
  result += ",\"speed\":";
  result += SignedNumber(status.speed);
  result += ",\"mode\":";
  AppendJsonString(result, TacticalDailySentinelModeName(status.mode));
  result += ",\"army_count\":";
  result += Number(status.army_count);
  result += ",\"combat_count\":";
  result += Number(status.combat_count);
  result += ",\"completed_daily_ticks\":";
  result += Number(status.completed_daily_ticks);
  result += ",\"intermediate_pause_count\":";
  result += Number(status.intermediate_pause_count);
  result += ",\"trigger_flags\":";
  result += Number(status.trigger_flags);
  result += ",\"trigger_reasons\":";
  AppendTacticalDailySentinelTriggerReasons(result, status.trigger_flags);
  result += ",\"signed_date_delta_from_target_raw\":";
  result += SignedNumber(status.signed_date_delta_from_target_raw);
  result += ",\"overshoot_days\":";
  result += SignedNumber(status.overshoot_days);
  result += ",\"pause_wrapper_called\":";
  result += status.pause_wrapper_called ? "true" : "false";
  result += ",\"pause_observed\":";
  result += status.pause_observed ? "true" : "false";
  result += ",\"terminal_observed\":";
  result += status.terminal_observed ? "true" : "false";
  result += ",\"abnormal\":";
  result += status.abnormal ? "true" : "false";
  result += "}}}";
  return result;
}

std::string TitleMapNavigationResultFrame(
    std::string_view request_id, std::string_view payload) {
  if (payload.empty()) {
    return {};
  }
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":\"";
  result += request_id;
  result += "\",\"ok\":true,\"result\":";
  result += payload;
  result += '}';
  return result;
}

std::string RoutePreviewResultFrame(
    std::string_view request_id, std::string_view step,
    const xar::game::PreviewMoveArmyResult &preview) {
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":\"";
  result += request_id;
  result += "\",\"ok\":true,\"result\":{\"step\":\"";
  result += step;
  result += "\",\"accepted\":true,\"status\":\"available\","
            "\"route_preview\":{\"status\":\"available\",\"army_id\":";
  result += SignedNumber(preview.army_id);
  result += ",\"origin_province_id\":";
  result += SignedNumber(preview.origin_province_id);
  result += ",\"target_province_id\":";
  result += SignedNumber(preview.target_province_id);
  result += ",\"route_province_ids\":";
  AppendInt32Array(result, preview.route_province_ids);
  result += "}}}";
  return result;
}

void AppendRouteTimeline(
    std::string &result,
    const xar::game::RouteTimelineSnapshot &timeline) {
  result += "{\"timeline_observable\":";
  result += timeline.timeline_observable ? "true" : "false";
  result += ",\"army_id\":";
  result += SignedNumber(timeline.army_id);
  result += ",\"current_province_id\":";
  result += SignedNumber(timeline.current_province_id);
  result += ",\"effective_origin_province_id\":";
  result += SignedNumber(timeline.effective_origin_province_id);
  result += ",\"route_province_ids\":";
  AppendInt32Array(result, timeline.route_province_ids);
  result += ",\"arrival_date_raws\":";
  AppendInt32Array(result, timeline.arrival_date_raws);
  result += '}';
}

void AppendRouteContactConflict(
    std::string &result,
    const xar::game::RouteContactConflictSnapshot &conflict) {
  result += "{\"kind\":";
  AppendJsonString(result, conflict.kind);
  result += ",\"hostile_army_id\":";
  result += SignedNumber(conflict.hostile_army_id);
  if (conflict.kind == "same_province") {
    result += ",\"province_id\":";
    result += SignedNumber(conflict.province_id);
  } else if (conflict.kind == "opposing_edge") {
    result += ",\"subject_from_province_id\":";
    result += SignedNumber(conflict.subject_from_province_id);
    result += ",\"subject_to_province_id\":";
    result += SignedNumber(conflict.subject_to_province_id);
    result += ",\"hostile_from_province_id\":";
    result += SignedNumber(conflict.hostile_from_province_id);
    result += ",\"hostile_to_province_id\":";
    result += SignedNumber(conflict.hostile_to_province_id);
  }
  result += ",\"overlap_start_date_raw\":";
  result += SignedNumber(conflict.overlap_start_date_raw);
  result += ",\"overlap_end_date_raw\":";
  result += SignedNumber(conflict.overlap_end_date_raw);
  result += '}';
}

std::string RouteContactHorizonResultFrame(
    std::string_view request_id, std::string_view step,
    std::uint64_t query_sequence,
    const xar::game::RouteContactHorizonSnapshot &horizon) {
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":";
  AppendJsonString(result, request_id);
  result += ",\"ok\":true,\"result\":{\"step\":";
  AppendJsonString(result, step);
  result +=
      ",\"accepted\":true,\"status\":\"available\",\"query_sequence\":";
  result += Number(query_sequence);
  result += ",\"snapshot_revision\":";
  result += Number(horizon.snapshot_revision);
  result += ",\"route_contact_horizon\":{\"status\":\"available\",";
  result += "\"snapshot_revision\":";
  result += Number(horizon.snapshot_revision);
  result += ",\"date_raw\":";
  result += SignedNumber(horizon.date_raw);
  result += ",\"subject_army_id\":";
  result += SignedNumber(horizon.subject_army_id);
  result += ",\"target_province_id\":";
  result += SignedNumber(horizon.target_province_id);
  result += ",\"hostile_army_ids\":";
  AppendInt32Array(result, horizon.hostile_army_ids);
  result += ",\"subject_route\":";
  AppendRouteTimeline(result, horizon.subject_route);
  result += ",\"hostile_routes\":[";
  for (std::size_t index = 0; index < horizon.hostile_routes.size(); ++index) {
    if (index != 0) {
      result += ',';
    }
    AppendRouteTimeline(result, horizon.hostile_routes[index]);
  }
  result += "],\"horizon_start_date_raw\":";
  result += SignedNumber(horizon.horizon_start_date_raw);
  result += ",\"horizon_end_date_raw\":";
  result += SignedNumber(horizon.horizon_end_date_raw);
  result += ",\"one_day_contact_free\":";
  result += horizon.one_day_contact_free ? "true" : "false";
  result += ",\"conflicts\":[";
  for (std::size_t index = 0; index < horizon.conflicts.size(); ++index) {
    if (index != 0) {
      result += ',';
    }
    AppendRouteContactConflict(result, horizon.conflicts[index]);
  }
  result += "]}}}";
  return result;
}

std::string ActualContactScopeResultFrame(
    std::string_view request_id, std::string_view step,
    std::uint64_t query_sequence,
    const xar::game::ActualContactScopeSnapshot &scope) {
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":";
  AppendJsonString(result, request_id);
  result += ",\"ok\":true,\"result\":{\"step\":";
  AppendJsonString(result, step);
  result +=
      ",\"accepted\":true,\"status\":\"available\",\"query_sequence\":";
  result += Number(query_sequence);
  result += ",\"snapshot_revision\":";
  result += Number(scope.snapshot_revision);
  result += ",\"actual_contact_scope\":{\"schema_version\":1,";
  result += "\"contract_stage\":\"production_exact_current_province\",";
  result += "\"status\":\"available\",\"scope_kind\":";
  AppendJsonString(result, scope.scope_kind);
  result += ",\"snapshot_revision\":";
  result += Number(scope.snapshot_revision);
  result += ",\"date_raw\":";
  result += SignedNumber(scope.date_raw);
  result += ",\"subject_army_id\":";
  result += SignedNumber(scope.subject_army_id);
  result += ",\"subject_native_carmy_id\":";
  result += SignedNumber(scope.subject_native_carmy_id);
  result += ",\"subject_owner_character_id\":";
  result += SignedNumber(scope.subject_owner_character_id);
  result += ",\"target_province_id\":";
  result += SignedNumber(scope.target_province_id);
  result += ",\"province_unit_army_ids\":";
  AppendInt32Array(result, scope.province_unit_army_ids);
  result += ",\"province_combat_ids\":";
  AppendInt32Array(result, scope.province_combat_ids);
  result += ",\"stored_order_policy\":\"numeric_full_id\",";
  result += "\"transition_kind\":";
  AppendJsonString(result, scope.transition_kind);
  result += ",\"selected_combat_id\":";
  if (scope.selected_combat_id > 0) {
    result += SignedNumber(scope.selected_combat_id);
  } else {
    result += "null";
  }
  result += ",\"selected_combat_array_index\":";
  if (scope.selected_combat_array_index >= 0) {
    result += SignedNumber(scope.selected_combat_array_index);
  } else {
    result += "null";
  }
  result += ",\"join_side\":";
  if (scope.join_side == "none") {
    result += "null";
  } else {
    AppendJsonString(result, scope.join_side);
  }
  result += ",\"defender_seed_character_id\":";
  if (scope.defender_seed_character_id > 0) {
    result += SignedNumber(scope.defender_seed_character_id);
  } else {
    result += "null";
  }
  result += ",\"initiator_is_defender\":";
  result += scope.initiator_is_defender ? "true" : "false";
  result += ",\"adjacency_kind_raw\":";
  result += SignedNumber(scope.adjacency_kind_raw);
  result += ",\"loser_excluded_native_carmy_ids\":";
  AppendInt32Array(result, scope.loser_excluded_native_carmy_ids);
  result += ",\"opponent_army_ids\":";
  AppendInt32Array(result, scope.opponent_army_ids);
  result += ",\"attacker_army_ids\":";
  AppendInt32Array(result, scope.attacker_army_ids);
  result += ",\"defender_army_ids\":";
  AppendInt32Array(result, scope.defender_army_ids);
  result += ",\"actual_contact_scope_ready\":";
  result += scope.actual_contact_scope_ready ? "true" : "false";
  result += ",\"combat_v3_participant_scope_ready\":";
  result += scope.combat_v3_participant_scope_ready ? "true" : "false";
  result += "}}}";
  return result;
}

std::string BattleControlSnapshotResultFrame(
    std::string_view request_id, std::string_view step,
    std::uint64_t query_sequence,
    const xar::game::BattleControlSnapshot &snapshot) {
  const auto payload =
      xar::ck3_11906::SerializeBattleControlSnapshotV1(snapshot);
  if (payload.empty()) {
    return {};
  }
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":";
  AppendJsonString(result, request_id);
  result += ",\"ok\":true,\"result\":{\"step\":";
  AppendJsonString(result, step);
  result +=
      ",\"accepted\":true,\"status\":\"available\",\"query_sequence\":";
  result += Number(query_sequence);
  result += ",\"snapshot_revision\":";
  result += Number(snapshot.snapshot_revision);
  result += ",\"battle_control_snapshot\":";
  result += payload;
  result += "}}";
  return result;
}

std::string BattleTransitionResultFrame(
    std::string_view request_id, std::string_view step,
    std::uint64_t query_sequence,
    const xar::game::BattleTransitionSnapshot &snapshot) {
  const auto payload =
      xar::ck3_11906::SerializeBattleTransitionV1(snapshot);
  const auto status =
      xar::ck3_11906::BattleTransitionStatusNameV1(snapshot.status);
  if (payload.empty() || status.empty()) {
    return {};
  }
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":";
  AppendJsonString(result, request_id);
  result += ",\"ok\":true,\"result\":{\"step\":";
  AppendJsonString(result, step);
  result += ",\"accepted\":true,\"status\":";
  AppendJsonString(result, status);
  result += ",\"query_sequence\":";
  result += Number(query_sequence);
  result += ",\"snapshot_revision\":";
  result += Number(snapshot.snapshot_revision);
  result += ",\"battle_transition_snapshot\":";
  result += payload;
  result += "}}";
  return result;
}

std::string BattleTerminalTransitionResultFrame(
    std::string_view request_id, std::string_view step,
    std::uint64_t query_sequence,
    const xar::game::BattleTerminalTransitionSnapshotV1 &snapshot) {
  const auto payload =
      xar::ck3_11906::SerializeBattleTerminalTransitionV1(snapshot);
  if (payload.empty()) {
    return {};
  }
  const std::string_view status =
      snapshot.status ==
              xar::game::BattleTerminalTransitionStatusV1::available
          ? "available"
          : "unavailable";
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":";
  AppendJsonString(result, request_id);
  result += ",\"ok\":true,\"result\":{\"step\":";
  AppendJsonString(result, step);
  result += ",\"accepted\":true,\"status\":";
  AppendJsonString(result, status);
  result += ",\"query_sequence\":";
  result += Number(query_sequence);
  result += ",\"snapshot_revision\":";
  result += Number(snapshot.snapshot_revision);
  result += ",\"battle_terminal_transition\":";
  result += payload;
  result += "}}";
  return result;
}

std::string BattleReinforcementAssignmentResultFrame(
    std::string_view request_id, std::string_view step,
    std::uint64_t query_sequence,
    const xar::game::BattleReinforcementAssignmentSnapshot &snapshot) {
  const auto payload =
      xar::ck3_11906::SerializeBattleReinforcementAssignmentV1(snapshot);
  if (payload.empty()) {
    return {};
  }
  const std::string_view status =
      snapshot.status ==
              xar::game::BattleReinforcementAssignmentStatus::available
          ? "available"
          : "unavailable";
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":";
  AppendJsonString(result, request_id);
  result += ",\"ok\":true,\"result\":{\"step\":";
  AppendJsonString(result, step);
  result += ",\"accepted\":true,\"status\":";
  AppendJsonString(result, status);
  result += ",\"query_sequence\":";
  result += Number(query_sequence);
  result += ",\"snapshot_revision\":";
  result += Number(snapshot.snapshot_revision);
  result += ",\"battle_reinforcement_assignment\":";
  result += payload;
  result += "}}";
  return result;
}

std::string CampaignRootContextResultFrame(
    std::string_view request_id, std::uint64_t query_sequence,
    const xar::game::CampaignRootContextV1 &context) {
  const auto payload =
      xar::ck3_11906::SerializeCampaignRootContextV1(context);
  if (payload.empty()) {
    return {};
  }
  const std::string_view status =
      context.status == xar::game::CampaignRootContextStatusV1::available
          ? "available"
          : "unavailable";
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":";
  AppendJsonString(result, request_id);
  result +=
      ",\"ok\":true,\"result\":{\"step\":\"query-campaign-root-context-v1\",";
  result += "\"accepted\":true,\"status\":";
  AppendJsonString(result, status);
  result += ",\"query_sequence\":";
  result += Number(query_sequence);
  result += ",\"snapshot_revision\":";
  result += Number(context.snapshot_revision);
  result += ",\"campaign_root_context\":";
  result += payload;
  result += ",\"backend_id\":\"native-headless\"}}";
  return result;
}

std::string LoadedFeatureManifestResultFrame(
    std::string_view request_id, std::uint64_t query_sequence,
    const xar::game::LoadedFeatureManifestV1 &manifest) {
  const auto payload =
      xar::ck3_11906::SerializeLoadedFeatureManifestV1(manifest);
  if (payload.empty()) {
    return {};
  }
  const std::string_view status =
      manifest.status == xar::game::LoadedFeatureManifestStatusV1::available
          ? "available"
          : "unavailable";
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":";
  AppendJsonString(result, request_id);
  result +=
      ",\"ok\":true,\"result\":{\"step\":\"query-loaded-feature-manifest-v1\",";
  result += "\"accepted\":true,\"status\":";
  AppendJsonString(result, status);
  result += ",\"query_sequence\":";
  result += Number(query_sequence);
  result += ",\"snapshot_revision\":";
  result += Number(manifest.snapshot_revision);
  result += ",\"loaded_feature_manifest\":";
  result += payload;
  result += ",\"backend_id\":\"native-headless\"}}";
  return result;
}

std::string PendingCharacterInteractionContextResultFrame(
    std::string_view request_id, std::uint64_t query_sequence,
    const xar::game::PendingCharacterInteractionContextV1 &context) {
  const auto payload =
      xar::ck3_11906::SerializePendingCharacterInteractionContextV1(context);
  if (payload.empty()) {
    return {};
  }
  std::string_view status = "unavailable";
  if (context.status ==
      xar::game::PendingCharacterInteractionContextStatusV1::available) {
    status = "available";
  } else if (
      context.status ==
      xar::game::PendingCharacterInteractionContextStatusV1::invalid) {
    status = "invalid";
  }
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":";
  AppendJsonString(result, request_id);
  result +=
      ",\"ok\":true,\"result\":{\"step\":\"query-pending-character-"
      "interaction-context-v1\",";
  result += "\"accepted\":true,\"status\":";
  AppendJsonString(result, status);
  result += ",\"query_sequence\":";
  result += Number(query_sequence);
  result += ",\"snapshot_revision\":";
  result += Number(context.snapshot_revision);
  result += ",\"pending_character_interaction_context\":";
  result += payload;
  result += ",\"backend_id\":\"native-headless\"}}";
  return result;
}

std::string EventWindowContextResultFrame(
    std::string_view request_id, std::uint64_t query_sequence,
    const xar::game::EventWindowContextV1 &context) {
  const auto payload =
      xar::ck3_11906::SerializeEventWindowContextV1(context);
  if (payload.empty()) {
    return {};
  }
  const std::string_view status =
      context.status == xar::game::EventWindowContextStatusV1::available
          ? "available"
          : "unavailable";
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":";
  AppendJsonString(result, request_id);
  result +=
      ",\"ok\":true,\"result\":{\"step\":"
      "\"query-current-event-window-context-v1\",";
  result += "\"accepted\":true,\"status\":";
  AppendJsonString(result, status);
  result += ",\"query_sequence\":";
  result += Number(query_sequence);
  result += ",\"snapshot_revision\":";
  result += Number(context.snapshot_revision);
  result += ",\"current_event_window_context\":";
  result += payload;
  result += ",\"backend_id\":\"native-headless\"}}";
  return result;
}

std::string SaveCheckpointResultFrame(std::string_view request_id,
                                      const CheckpointSubmission &checkpoint) {
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":\"";
  result += request_id;
  result += "\",\"ok\":true,\"result\":{\"step\":\"save-checkpoint\","
            "\"accepted\":true,\"status\":\"submitted\","
            "\"submission\":{\"sequence\":";
  result += Number(checkpoint.sequence);
  result += ",\"requested_save_name\":\"";
  result += checkpoint.save_name;
  result += "\",\"date_raw\":";
  result += SignedNumber(checkpoint.date_raw);
  result += "}}}";
  return result;
}

std::string DeclarableWarsResultFrame(
    std::string_view request_id, std::uint64_t query_sequence,
    const std::vector<xar::game::DeclarableWarSnapshot> &declarations) {
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":\"";
  result += request_id;
  result +=
      "\",\"ok\":true,\"result\":{\"step\":\"query-declarable-wars\","
      "\"accepted\":true,\"status\":\"available\",\"query_sequence\":";
  result += Number(query_sequence);
  result += ",\"declarable_wars\":[";
  for (std::size_t index = 0; index < declarations.size(); ++index) {
    if (index != 0) {
      result += ',';
    }
    AppendDeclaration(result, declarations[index]);
  }
  result += "]}}";
  return result;
}

struct WarEntryBridgeFrameContext {
  const xar::game::GameAdapter *game = nullptr;
  std::uint64_t expected_snapshot_revision = 0;
  xar::game::Snapshot expected_snapshot;
  std::vector<std::int32_t> expected_declarable_target_character_ids;
};

bool CaptureWarEntryBridgeFrame(
    void *opaque, xar::game::WarEntryAssessmentFrameV1 &output) noexcept {
  const auto *const context =
      static_cast<const WarEntryBridgeFrameContext *>(opaque);
  if (context == nullptr) {
    return false;
  }
  try {
    if (context->game == nullptr ||
        context->expected_snapshot_revision == 0) {
      return false;
    }
    xar::game::Snapshot snapshot{};
    if (!xar::game::ReadSnapshot(*context->game, snapshot) ||
        snapshot != context->expected_snapshot) {
      return false;
    }

    output = {};
    output.snapshot_revision = context->expected_snapshot_revision;
    output.date_raw = snapshot.date_raw;
    output.paused = snapshot.paused;
    output.map_ready = snapshot.map_ready;
    output.actor_alive = snapshot.has_played_character &&
                         snapshot.played_character_alive;
    output.actor_character_id = snapshot.played_character_id;
    output.declarable_target_character_ids =
        context->expected_declarable_target_character_ids;
    return true;
  } catch (...) {
    output = {};
    return false;
  }
}

std::string WarEntryAssessmentsResultFrame(
    std::string_view request_id, std::string_view step,
    std::uint64_t query_sequence,
    const xar::game::WarEntryAssessmentsV1 &assessments) {
  const auto payload =
      xar::ck3_11906::SerializeWarEntryAssessmentsV1(assessments);
  if (payload.empty()) {
    return {};
  }
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":";
  AppendJsonString(result, request_id);
  result += ",\"ok\":true,\"result\":{\"step\":";
  AppendJsonString(result, step);
  result +=
      ",\"accepted\":true,\"status\":\"available\",\"query_sequence\":";
  result += Number(query_sequence);
  result += ",\"war_entry_assessments\":";
  result += payload;
  result += "}}";
  return result;
}

std::string WarTerminationOptionsResultFrame(
    std::string_view request_id, std::string_view step,
    std::uint64_t query_sequence,
    const xar::game::WarTerminationOptionsSnapshot &options) {
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":\"";
  result += request_id;
  result += "\",\"ok\":true,\"result\":{\"step\":";
  AppendJsonString(result, step);
  result +=
      ",\"accepted\":true,\"status\":\"available\",\"query_sequence\":";
  result += Number(query_sequence);
  result += ",\"war_termination_options\":";
  AppendWarTerminationOptions(result, options);
  result += "}}";
  return result;
}

std::string WarTerminationTermsResultFrame(
    std::string_view request_id, std::string_view step,
    std::uint64_t query_sequence,
    const xar::game::WarTerminationTermsSnapshot &terms,
    bool supported) {
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":\"";
  result += request_id;
  result += "\",\"ok\":true,\"result\":{\"step\":";
  AppendJsonString(result, step);
  result += ",\"accepted\":true,\"status\":\"";
  result += supported ? "available" : "unsupported";
  result += "\",\"query_sequence\":";
  result += Number(query_sequence);
  result += ",\"war_termination_terms\":";
  AppendWarTerminationTerms(result, terms, supported);
  result += "}}";
  return result;
}

std::string ArmyStrengthsResultFrame(
    std::string_view request_id, std::uint64_t query_sequence,
    xar::game::ReadArmyStrengthsResult query_result,
    const std::vector<xar::game::ArmyStrengthSnapshot> &strengths) {
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":\"";
  result += request_id;
  result +=
      "\",\"ok\":true,\"result\":{\"step\":"
      "\"query-army-strengths-v1\",\"accepted\":true,\"status\":\"";
  result += query_result == xar::game::ReadArmyStrengthsResult::available
                ? "available"
                : "partial";
  result += "\",\"query_sequence\":";
  result += Number(query_sequence);
  result += ",\"army_strengths\":[";
  for (std::size_t index = 0; index < strengths.size(); ++index) {
    if (index != 0) {
      result += ',';
    }
    AppendArmyStrength(result, strengths[index]);
  }
  result += "]}}";
  return result;
}

std::string CombatSimulationInputsResultFrame(
    std::string_view request_id, std::string_view step,
    std::uint64_t query_sequence,
    xar::game::ReadCombatSimulationInputsResult query_result,
    const xar::game::CombatSimulationInputsSnapshot &snapshot) {
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":";
  AppendJsonString(result, request_id);
  result += ",\"ok\":true,\"result\":{\"step\":";
  AppendJsonString(result, step);
  result += ",\"accepted\":true,\"status\":\"";
  result += query_result ==
                    xar::game::ReadCombatSimulationInputsResult::available
                ? "available"
                : "partial";
  result += "\",\"query_sequence\":";
  result += Number(query_sequence);
  result += ",\"combat_simulation_inputs\":";
  AppendCombatSimulationInputs(result, snapshot);
  result += "}}";
  return result;
}

std::string CombatSimulationInputsV3ResultFrame(
    std::string_view request_id, std::string_view step,
    std::uint64_t query_sequence,
    xar::game::ReadCombatSimulationInputsV3Result query_result,
    const xar::game::CombatSimulationInputsV3Snapshot &snapshot) {
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":";
  AppendJsonString(result, request_id);
  result += ",\"ok\":true,\"result\":{\"step\":";
  AppendJsonString(result, step);
  result += ",\"accepted\":true,\"status\":\"";
  result += query_result ==
                    xar::game::ReadCombatSimulationInputsV3Result::available
                ? "available"
                : "unavailable";
  result += "\",\"query_sequence\":";
  result += Number(query_sequence);
  result += ",\"combat_simulation_inputs\":";
  AppendCombatSimulationInputsV3(result, snapshot);
  result += "}}";
  return result;
}

std::string ArrangeMarriageChoicesResultFrame(
    std::string_view request_id, std::uint64_t query_sequence,
    const std::vector<xar::game::ArrangeMarriageChoice> &choices,
    const xar::game::ArrangeMarriageQueryDiagnostics &diagnostics) {
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":\"";
  result += request_id;
  result +=
      "\",\"ok\":true,\"result\":{\"step\":"
      "\"query-arrange-marriage-choices\",\"accepted\":true,"
      "\"status\":\"available\",\"query_sequence\":";
  result += Number(query_sequence);
  result += ",\"arrange_marriage_choices\":[";
  for (std::size_t index = 0; index < choices.size(); ++index) {
    if (index != 0) {
      result += ',';
    }
    AppendMarriageChoice(result, choices[index]);
  }
  result += "],\"arrange_marriage_diagnostics\":";
  AppendMarriageQueryDiagnostics(result, diagnostics);
  result += "}}";
  return result;
}

std::int32_t FixedSpeedStep(std::string_view step) noexcept {
  constexpr std::string_view prefix = "set-speed-";
  if (!step.starts_with(prefix) || step.size() != prefix.size() + 1U) {
    return -1;
  }
  const char digit = step.back();
  return digit >= '1' && digit <= '5' ? digit - '0' : -1;
}

std::optional<std::int32_t>
EventOptionStep(std::string_view step) noexcept {
  constexpr std::string_view prefix = "select-event-option-";
  if (!step.starts_with(prefix) || step.size() == prefix.size()) {
    return std::nullopt;
  }
  std::int32_t public_index = -1;
  const auto suffix = step.substr(prefix.size());
  const auto parsed = std::from_chars(suffix.data(),
                                      suffix.data() + suffix.size(),
                                      public_index);
  if (parsed.ec != std::errc{} || parsed.ptr != suffix.data() + suffix.size() ||
      public_index < 1) {
    return std::nullopt;
  }
  // MCP/agent-facing event choices are one based. CK3's native command
  // payload and executor are zero based.
  return public_index - 1;
}

std::optional<std::int32_t> PositiveNativeId(
    std::string_view value) noexcept {
  if (value.empty()) {
    return std::nullopt;
  }
  for (const char character : value) {
    if (character < '0' || character > '9') {
      return std::nullopt;
    }
  }
  std::int32_t parsed_value = -1;
  const auto parsed = std::from_chars(
      value.data(), value.data() + value.size(), parsed_value);
  if (parsed.ec != std::errc{} ||
      parsed.ptr != value.data() + value.size() || parsed_value < 1) {
    return std::nullopt;
  }
  return parsed_value;
}

struct MoveArmyStepIds {
  std::int32_t army_id = -1;
  std::int32_t province_id = -1;
};

std::optional<MoveArmyStepIds> ArmyToProvinceStep(
    std::string_view step, std::string_view prefix) noexcept {
  constexpr std::string_view separator = "-to-";
  if (!step.starts_with(prefix)) {
    return std::nullopt;
  }
  const auto payload = step.substr(prefix.size());
  const std::size_t separator_index = payload.find(separator);
  if (separator_index == std::string_view::npos ||
      payload.find(separator, separator_index + separator.size()) !=
          std::string_view::npos) {
    return std::nullopt;
  }
  const auto army_id = PositiveNativeId(payload.substr(0, separator_index));
  const auto province_id = PositiveNativeId(
      payload.substr(separator_index + separator.size()));
  if (!army_id.has_value() || !province_id.has_value()) {
    return std::nullopt;
  }
  return MoveArmyStepIds{army_id.value(), province_id.value()};
}

std::optional<MoveArmyStepIds> MoveArmyStep(
    std::string_view step) noexcept {
  return ArmyToProvinceStep(step, "move-army-");
}

std::optional<MoveArmyStepIds> PreviewMoveArmyStep(
    std::string_view step) noexcept {
  return ArmyToProvinceStep(step, "preview-move-army-");
}

std::optional<std::int32_t> DisbandArmyStep(
    std::string_view step) noexcept {
  constexpr std::string_view prefix = "disband-army-";
  if (!step.starts_with(prefix)) {
    return std::nullopt;
  }
  return PositiveNativeId(step.substr(prefix.size()));
}

std::optional<std::int32_t> SplitArmyHalfStep(
    std::string_view step) noexcept {
  constexpr std::string_view prefix = "split-army-half-";
  if (!step.starts_with(prefix)) {
    return std::nullopt;
  }
  return PositiveNativeId(step.substr(prefix.size()));
}

std::optional<std::int32_t> AssaultStep(
    std::string_view step, std::string_view prefix) noexcept {
  if (!step.starts_with(prefix)) {
    return std::nullopt;
  }
  return PositiveNativeId(step.substr(prefix.size()));
}

struct MergeArmiesStepIds {
  std::int32_t destination_army_id = -1;
  std::int32_t source_army_id = -1;
};

std::optional<MergeArmiesStepIds> MergeArmiesStep(
    std::string_view step) noexcept {
  constexpr std::string_view prefix = "merge-armies-";
  constexpr std::string_view separator = "-with-";
  if (!step.starts_with(prefix)) {
    return std::nullopt;
  }
  const auto payload = step.substr(prefix.size());
  const std::size_t separator_index = payload.find(separator);
  if (separator_index == std::string_view::npos ||
      payload.find(separator, separator_index + separator.size()) !=
          std::string_view::npos) {
    return std::nullopt;
  }
  const auto destination_army_id =
      PositiveNativeId(payload.substr(0, separator_index));
  const auto source_army_id = PositiveNativeId(
      payload.substr(separator_index + separator.size()));
  if (!destination_army_id.has_value() || !source_army_id.has_value() ||
      destination_army_id.value() == source_army_id.value()) {
    return std::nullopt;
  }
  return MergeArmiesStepIds{destination_army_id.value(),
                            source_army_id.value()};
}

std::optional<std::int32_t> EnforceDemandsStep(
    std::string_view step) noexcept {
  constexpr std::string_view prefix = "enforce-demands-";
  if (!step.starts_with(prefix)) {
    return std::nullopt;
  }
  return PositiveNativeId(step.substr(prefix.size()));
}

std::optional<std::int32_t> WarTerminationQueryStep(
    std::string_view step) noexcept {
  constexpr std::string_view prefix =
      "query-war-termination-options-";
  if (!step.starts_with(prefix)) {
    return std::nullopt;
  }
  return PositiveNativeId(step.substr(prefix.size()));
}

std::optional<std::int32_t> WarTerminationTermsQueryStep(
    std::string_view step) noexcept {
  constexpr std::string_view prefix =
      "query-war-termination-terms-v1-";
  if (!step.starts_with(prefix)) {
    return std::nullopt;
  }
  return PositiveNativeId(step.substr(prefix.size()));
}

std::optional<std::int32_t> SurrenderWarStep(
    std::string_view step) noexcept {
  constexpr std::string_view prefix = "surrender-war-";
  if (!step.starts_with(prefix)) {
    return std::nullopt;
  }
  return PositiveNativeId(step.substr(prefix.size()));
}

std::optional<std::int32_t> OfferWhitePeaceStep(
    std::string_view step) noexcept {
  constexpr std::string_view prefix = "offer-white-peace-";
  if (!step.starts_with(prefix)) {
    return std::nullopt;
  }
  return PositiveNativeId(step.substr(prefix.size()));
}

class WarEntryApplicationMainMailboxWorkerLifetime final {
public:
  explicit WarEntryApplicationMainMailboxWorkerLifetime(
      const xar::game::GameAdapter &game) noexcept
      : game_(&game) {}

  WarEntryApplicationMainMailboxWorkerLifetime(
      const WarEntryApplicationMainMailboxWorkerLifetime &) = delete;
  WarEntryApplicationMainMailboxWorkerLifetime &operator=(
      const WarEntryApplicationMainMailboxWorkerLifetime &) = delete;

  void MaybeInstall(const xar::game::Snapshot &snapshot) noexcept {
    if (installed_ || attempted_ || game_ == nullptr ||
        !snapshot.paused || !snapshot.map_ready ||
        !snapshot.has_played_character || !snapshot.played_character_alive) {
      return;
    }
    attempted_ = true;
    if (!game_->enabled() ||
        game_->descriptor().adapter_id !=
            xar::ck3_11906::kMainThreadQueryMailboxV1AdapterId) {
      return;
    }
    xar::ck3_11906::MainThreadQueryInstallEnvironmentV1 environment{};
    environment.module_base = reinterpret_cast<std::uintptr_t>(
        GetModuleHandleW(nullptr));
    environment.exact_build_admitted = true;
    environment.offline_fixture = false;
    environment.executor_submission_enabled = true;
    environment.permitted_executor =
        &xar::ck3_11906::ExecuteWarEntryAssessmentMailboxQueryV1;
    environment.permitted_executor_secondary =
        &xar::ck3_11906::ExecuteRouteContactHorizonMailboxQueryV1;
    environment.permitted_executor_tertiary =
        &xar::ck3_11906::ExecuteActualContactScopeMailboxQueryV1;
    environment.permitted_executor_quaternary =
        &xar::ck3_11906::ExecuteCombatSimulationInputsV3MailboxQuery;
    environment.permitted_executor_quinary =
        &xar::ck3_11906::ExecuteBattleControlSnapshotMailboxQueryV1;
    environment.permitted_executor_senary =
        &xar::ck3_11906::ExecuteBattleTransitionMailboxQueryV1;
    environment.permitted_executor_septenary =
        &xar::ck3_11906::
            ExecuteBattleReinforcementAssignmentMailboxQueryV1;
    environment.permitted_executor_octonary =
        &xar::ck3_11906::ExecuteBattleTerminalTransitionMailboxQueryV1;
    environment.permitted_executor_nonary =
        &xar::ck3_11906::ExecuteCampaignRootContextMailboxQueryV1;
    environment.permitted_executor_denary =
        &xar::ck3_11906::ExecuteLoadedFeatureManifestMailboxQueryV1;
    environment.permitted_executor_undenary =
        &xar::ck3_11906::
            ExecutePendingCharacterInteractionContextMailboxQueryV1;
    environment.permitted_executor_duodenary =
        &xar::ck3_11906::ExecuteEventWindowContextMailboxQueryV1;
    environment.permitted_executor_thirdenary =
        &xar::ck3_11906::ExecuteTitleMapNavigationMailboxV1;
    installed_ = xar::ck3_11906::InstallMainThreadQueryMailboxV1(
        g_main_thread_query_mailbox_v1, environment);
  }

  ~WarEntryApplicationMainMailboxWorkerLifetime() noexcept {
    if (!installed_) {
      return;
    }
    while (true) {
      const auto result = xar::ck3_11906::UninstallMainThreadQueryMailboxV1(
          g_main_thread_query_mailbox_v1, 250);
      if (result == xar::ck3_11906::MainThreadQueryUninstallResultV1::
                        uninstalled ||
          result == xar::ck3_11906::MainThreadQueryUninstallResultV1::
                        not_installed) {
        return;
      }
      // Fail closed. XarCk3BridgeStop observes the still-running worker and
      // retains lifecycle=stopping rather than discarding synchronization
      // objects underneath an incomplete IAT restore/drain.
      Sleep(1);
    }
  }

private:
  const xar::game::GameAdapter *game_ = nullptr;
  bool attempted_ = false;
  bool installed_ = false;
};

bool RouteHostileScopeMatchesSnapshot(
    const xar::game::Snapshot &snapshot,
    const xar::game::RouteContactHorizonRequest &request) {
  return xar::ck3_11906::RouteContactHostileScopeMatchesSnapshotV1(
      snapshot, request);
}

bool PublishSnapshot(HANDLE pipe, const xar::game::GameAdapter &bindings,
                     std::optional<xar::game::Snapshot> &previous,
                     std::uint64_t &revision,
                     const CheckpointSubmission &checkpoint,
                     std::uint64_t &published_checkpoint_sequence,
                     WarEntryApplicationMainMailboxWorkerLifetime
                         *mailbox_lifetime = nullptr,
                     SnapshotPublishDiagnostics *diagnostics = nullptr) {
  const auto record = [diagnostics](std::string_view status,
                                    std::uint64_t published_revision,
                                    std::size_t payload_bytes) {
    if (diagnostics != nullptr) {
      diagnostics->status = status;
      diagnostics->revision = published_revision;
      diagnostics->payload_bytes = payload_bytes;
    }
  };
  if (!bindings.supports_snapshot()) {
    record("unsupported", revision, 0);
    return true;
  }
  xar::game::Snapshot snapshot{};
  if (!xar::game::ReadSnapshot(bindings, snapshot)) {
    record("read_failed", revision, 0);
    return true;
  }
  if (mailbox_lifetime != nullptr) {
    mailbox_lifetime->MaybeInstall(snapshot);
  }
  if (previous.has_value() && previous.value() == snapshot &&
      published_checkpoint_sequence == checkpoint.sequence) {
    record("deduplicated", revision, 0);
    return true;
  }
  ++revision;
  const auto frame = StateSnapshotFrame(snapshot, revision, checkpoint);
  previous = snapshot;
  published_checkpoint_sequence = checkpoint.sequence;
  const bool written = xar::bridge::WriteFrame(pipe, frame);
  record(written ? "written" : "write_failed", revision, frame.size());
  return written;
}

bool PublishTimelineSnapshotWithDiagnostics(
    HANDLE pipe, std::string_view request_id,
    const xar::game::GameAdapter &bindings,
    std::optional<xar::game::Snapshot> &previous,
    std::uint64_t &revision, const CheckpointSubmission &checkpoint,
    std::uint64_t &published_checkpoint_sequence) {
  const SnapshotPublishDiagnostics begin{"begin", revision, 0};
  if (!xar::bridge::WriteFrame(
          pipe, SnapshotPublishDiagnosticFrame(request_id, "begin", begin))) {
    return false;
  }
  SnapshotPublishDiagnostics completed{};
  if (!PublishSnapshot(pipe, bindings, previous, revision, checkpoint,
                       published_checkpoint_sequence, nullptr, &completed)) {
    return false;
  }
  return xar::bridge::WriteFrame(
      pipe, SnapshotPublishDiagnosticFrame(request_id, "end", completed));
}

bool IsSimpleRequestId(std::string_view value) noexcept {
  if (value.empty() ||
      value.size() > xar::bridge::kMaximumControlStringBytes) {
    return false;
  }
  for (const char character : value) {
    const bool accepted = (character >= 'a' && character <= 'z') ||
                          (character >= 'A' && character <= 'Z') ||
                          (character >= '0' && character <= '9') ||
                          character == '-' || character == '_' ||
                          character == '.';
    if (!accepted) {
      return false;
    }
  }
  return true;
}

HANDLE ConnectToHost() noexcept {
  while (WaitForSingleObject(g_stop_event, 0) == WAIT_TIMEOUT) {
    HANDLE pipe = CreateFileW(g_pipe_name, GENERIC_READ | GENERIC_WRITE, 0,
                              nullptr, OPEN_EXISTING, 0, nullptr);
    if (pipe != INVALID_HANDLE_VALUE) {
      return pipe;
    }
    const DWORD error = GetLastError();
    if (error != ERROR_PIPE_BUSY && error != ERROR_FILE_NOT_FOUND) {
      return INVALID_HANDLE_VALUE;
    }
    WaitForSingleObject(g_stop_event, 50);
  }
  return INVALID_HANDLE_VALUE;
}

struct WorkerState {
  std::uint64_t sequence = 0;
  std::uint64_t state_revision = 0;
  CheckpointSubmission checkpoint_submission{};
  std::uint64_t published_checkpoint_sequence = 0;
  std::optional<xar::game::Snapshot> previous_snapshot;
  std::uint64_t declaration_query_sequence = 0;
  std::vector<xar::game::DeclarableWarSnapshot> declarable_wars;
  std::uint64_t war_entry_assessment_query_sequence = 0;
  std::uint64_t route_contact_horizon_query_sequence = 0;
  std::uint64_t actual_contact_scope_query_sequence = 0;
  std::uint64_t battle_control_snapshot_query_sequence = 0;
  std::uint64_t battle_transition_query_sequence = 0;
  std::uint64_t battle_reinforcement_assignment_query_sequence = 0;
  std::uint64_t battle_terminal_transition_query_sequence = 0;
  std::uint64_t campaign_root_context_query_sequence = 0;
  std::uint64_t loaded_feature_manifest_query_sequence = 0;
  std::uint64_t pending_character_interaction_context_query_sequence = 0;
  std::uint64_t event_window_context_query_sequence = 0;
  std::uint64_t army_strength_query_sequence = 0;
  std::uint64_t combat_inputs_query_sequence = 0;
  std::uint64_t war_termination_query_sequence = 0;
  std::uint64_t war_termination_terms_query_sequence = 0;
  std::uint64_t marriage_query_sequence = 0;
  std::vector<xar::game::ArrangeMarriageChoice> marriage_choices;
};

void RunConnectedSession(
    HANDLE pipe, const xar::game::GameAdapter &game, WorkerState &state,
    WarEntryApplicationMainMailboxWorkerLifetime &mailbox_lifetime) noexcept {
  state.checkpoint_submission.save_name =
      game.descriptor().checkpoint_save_name;
  if (!xar::bridge::WriteFrame(pipe, HelloFrame(game))) {
    return;
  }

  auto &sequence = state.sequence;
  auto &state_revision = state.state_revision;
  auto &checkpoint_submission = state.checkpoint_submission;
  auto &published_checkpoint_sequence = state.published_checkpoint_sequence;
  auto &previous_snapshot = state.previous_snapshot;
  auto &declaration_query_sequence = state.declaration_query_sequence;
  auto &declarable_wars = state.declarable_wars;
  auto &war_entry_assessment_query_sequence =
      state.war_entry_assessment_query_sequence;
  auto &route_contact_horizon_query_sequence =
      state.route_contact_horizon_query_sequence;
  auto &actual_contact_scope_query_sequence =
      state.actual_contact_scope_query_sequence;
  auto &battle_control_snapshot_query_sequence =
      state.battle_control_snapshot_query_sequence;
  auto &battle_transition_query_sequence =
      state.battle_transition_query_sequence;
  auto &battle_reinforcement_assignment_query_sequence =
      state.battle_reinforcement_assignment_query_sequence;
  auto &battle_terminal_transition_query_sequence =
      state.battle_terminal_transition_query_sequence;
  auto &campaign_root_context_query_sequence =
      state.campaign_root_context_query_sequence;
  auto &loaded_feature_manifest_query_sequence =
      state.loaded_feature_manifest_query_sequence;
  auto &pending_character_interaction_context_query_sequence =
      state.pending_character_interaction_context_query_sequence;
  auto &event_window_context_query_sequence =
      state.event_window_context_query_sequence;
  auto &army_strength_query_sequence =
      state.army_strength_query_sequence;
  auto &combat_inputs_query_sequence =
      state.combat_inputs_query_sequence;
  auto &war_termination_query_sequence =
      state.war_termination_query_sequence;
  auto &war_termination_terms_query_sequence =
      state.war_termination_terms_query_sequence;
  auto &marriage_query_sequence = state.marriage_query_sequence;
  auto &marriage_choices = state.marriage_choices;

  // A new MCP server has no copy of the previous semantic snapshot.  Force
  // the first heartbeat on every connection to republish current state and
  // the latest checkpoint submission, even if CK3 itself did not change.
  previous_snapshot.reset();
  published_checkpoint_sequence = 0;
  ULONGLONG next_heartbeat = GetTickCount64();
  bool connected = true;
  while (connected && WaitForSingleObject(g_stop_event, 0) == WAIT_TIMEOUT) {
    const ULONGLONG now = GetTickCount64();
    if (now >= next_heartbeat) {
      ++sequence;
      connected = xar::bridge::WriteFrame(pipe, HeartbeatFrame(sequence));
      if (connected && game.supports_snapshot()) {
        connected = PublishSnapshot(pipe, game, previous_snapshot,
                                    state_revision, checkpoint_submission,
                                    published_checkpoint_sequence,
                                    &mailbox_lifetime);
      }
      next_heartbeat = now + kHeartbeatIntervalMs;
      if (!connected) {
        break;
      }
    }

    const auto incoming = xar::bridge::TryReadFrame(pipe);
    if (incoming.status == xar::bridge::ReadStatus::closed ||
        incoming.status == xar::bridge::ReadStatus::invalid) {
      break;
    }
    if (incoming.status == xar::bridge::ReadStatus::frame) {
      std::string type;
      std::string request_id;
      if (xar::bridge::JsonStringField(
              incoming.payload, "type", type,
              xar::bridge::kMaximumControlStringBytes) &&
          type == "ping" &&
          xar::bridge::JsonStringField(
              incoming.payload, "request_id", request_id,
              xar::bridge::kMaximumControlStringBytes) &&
          IsSimpleRequestId(request_id)) {
        std::string pong =
            "{\"type\":\"pong\",\"protocol_version\":1,\"request_id\":\"";
        pong += request_id;
        pong += "\",\"pid\":";
        pong += Number(GetCurrentProcessId());
        pong += "}";
        connected = xar::bridge::WriteFrame(pipe, pong);
      } else if (type == "execute_step" &&
                 xar::bridge::JsonStringField(
                     incoming.payload, "request_id", request_id,
                     xar::bridge::kMaximumControlStringBytes) &&
                 IsSimpleRequestId(request_id)) {
        std::string step;
        if (!xar::bridge::JsonStringField(
                incoming.payload, "step", step,
                xar::ck3_11906::kTacticalDailySentinelMaximumArmStepBytesV1)) {
          connected = xar::bridge::WriteFrame(
              pipe, CommandResultFrame(request_id, "", false,
                                       "native gameplay step is missing"));
        } else if (!game.supports_step(step)) {
          connected = xar::bridge::WriteFrame(
              pipe, CommandResultFrame(request_id, step, false,
                                       "unsupported native gameplay step"));
        } else {
          xar::ck3_11906::TacticalDailySentinelArmRequestV1
              tactical_sentinel_request{};
          std::uint64_t tactical_sentinel_cancel_generation = 0;
          if (xar::ck3_11906::ParseTacticalDailySentinelArmStepV1(
                  step, tactical_sentinel_request)) {
            const auto result =
                xar::ck3_11906::ArmTacticalDailySentinelV1(
                    tactical_sentinel_request);
            if (result == xar::ck3_11906::
                              TacticalDailySentinelArmStatusV1::armed) {
              connected = xar::bridge::WriteFrame(
                  pipe, TacticalDailySentinelResultFrame(
                            request_id, step,
                            xar::ck3_11906::
                                ReadTacticalDailySentinelStatusV1()));
            } else {
              std::string_view error =
                  "tactical daily sentinel is unavailable";
              using ArmStatus = xar::ck3_11906::
                  TacticalDailySentinelArmStatusV1;
              if (result == ArmStatus::invalid_request) {
                error = "invalid tactical daily sentinel request";
              } else if (result == ArmStatus::requires_paused) {
                error = "tactical daily sentinel requires a paused map";
              } else if (result == ArmStatus::starting_date_mismatch) {
                error = "tactical daily sentinel starting date mismatch";
              } else if (result == ArmStatus::army_unavailable) {
                error = "tactical daily sentinel army is unavailable";
              } else if (result == ArmStatus::combat_unavailable) {
                error = "tactical daily sentinel combat is unavailable";
              } else if (result == ArmStatus::already_armed) {
                error = "tactical daily sentinel is already armed";
              }
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, false, error));
            }
          } else if (xar::ck3_11906::ParseTacticalDailySentinelCancelStepV1(
                         step, tactical_sentinel_cancel_generation)) {
            const auto result =
                xar::ck3_11906::CancelTacticalDailySentinelV1(
                    tactical_sentinel_cancel_generation);
            using CancelStatus = xar::ck3_11906::
                TacticalDailySentinelCancelStatusV1;
            if (result == CancelStatus::canceled) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, true,
                                           "canceled"));
            } else {
              std::string_view error =
                  "tactical daily sentinel cancel is unavailable";
              if (result == CancelStatus::invalid_request) {
                error = "invalid tactical daily sentinel cancel request";
              } else if (result == CancelStatus::requires_paused) {
                error = "tactical daily sentinel cancel requires a paused map";
              } else if (result == CancelStatus::generation_mismatch) {
                error = "tactical daily sentinel cancel generation mismatch";
              } else if (result == CancelStatus::not_armed) {
                error = "tactical daily sentinel cancel requires an armed generation";
              }
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, false, error));
            }
          } else if (step == xar::ck3_11906::
                                      kTacticalDailySentinelStatusStepV1) {
            connected = xar::bridge::WriteFrame(
                pipe, TacticalDailySentinelResultFrame(
                          request_id, step,
                          xar::ck3_11906::
                              ReadTacticalDailySentinelStatusV1()));
          } else if (step == xar::ck3_11906::kTitleMapNavigationV1Step) {
          xar::ck3_11906::TitleMapNavigationRequestV1 request{};
          if (!xar::ck3_11906::ParseTitleMapNavigationRequestV1(
                  incoming.payload, request)) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, false,
                                         "internal_error"));
          } else if (request.expected_snapshot_revision != state_revision) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, false,
                                         "state_changed"));
          } else {
            xar::game::Snapshot current_snapshot{};
            const bool snapshot_read =
                previous_snapshot.has_value() &&
                xar::game::ReadSnapshot(game, current_snapshot) &&
                current_snapshot == previous_snapshot.value();
            if (!snapshot_read) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, false,
                                           "state_changed"));
            } else if (!current_snapshot.paused) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, false,
                                           "requires_paused"));
            } else if (!current_snapshot.map_ready) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, false,
                                           "map_not_ready"));
            } else {
              xar::ck3_11906::TitleMapNavigationMailboxContextV1 query{};
              query.mailbox = &g_main_thread_query_mailbox_v1;
              query.bindings = xar::ck3_11906::BindCurrentProcess(true);
              const auto module_base = reinterpret_cast<std::uintptr_t>(
                  GetModuleHandleW(nullptr));
              query.title_environment =
                  xar::ck3_11906::BindTitleMapNavigationNativeEnvironmentV1(
                      module_base, true);
              query.camera_environment =
                  xar::ck3_11906::BindTitleMapNavigationCameraEnvironmentV1(
                      module_base, true);
              query.command.request = request;
              query.expected_snapshot = current_snapshot;

              const auto run =
                  xar::ck3_11906::RunTitleMapNavigationMailboxV1(query);
              xar::game::Snapshot completion_snapshot{};
              const bool completion_snapshot_stable =
                  xar::game::ReadSnapshot(game, completion_snapshot) &&
                  completion_snapshot == current_snapshot;
              std::string response;
              const bool success =
                  run == xar::ck3_11906::
                             TitleMapNavigationMailboxRunResultV1::terminal &&
                  completion_snapshot_stable &&
                  (query.command.status ==
                       xar::game::TitleMapNavigationCommandStatusV1::centered ||
                   query.command.status ==
                       xar::game::TitleMapNavigationCommandStatusV1::
                           already_centered);
              if (success) {
                const auto payload =
                    xar::ck3_11906::SerializeTitleMapNavigationResultV1(
                        query.command, query.dispatch_ticket_sequence);
                response =
                    TitleMapNavigationResultFrame(request_id, payload);
              }
              if (response.empty()) {
                if (!completion_snapshot_stable) {
                  query.command.status =
                      xar::game::TitleMapNavigationCommandStatusV1::
                          state_changed;
                }
                auto error =
                    xar::ck3_11906::
                        TitleMapNavigationCommandRejectionCodeV1(
                            query.command.status);
                if (error.empty()) {
                  error = "internal_error";
                }
                response =
                    CommandResultFrame(request_id, step, false, error);
              }
              connected = xar::bridge::WriteFrame(pipe, response);
            }
          }
          } else if (step == "pause-map") {
          const auto result = xar::game::SubmitPauseMap(game);
          if (result == xar::game::PauseSubmitResult::unavailable) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, false,
                                         "CK3 map state is unavailable"));
          } else {
            const std::string_view status =
                result == xar::game::PauseSubmitResult::submitted
                    ? "submitted"
                    : "already_paused";
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, true, status));
            if (connected) {
              // Timeline postconditions must be observable even when the
              // bridge already cached the same semantic state.  A consumer
              // can otherwise miss one state frame and wait forever after an
              // idempotent already_paused ACK while CK3 is truly paused.
              if (result == xar::game::PauseSubmitResult::already_paused) {
                previous_snapshot.reset();
              }
              connected = PublishTimelineSnapshotWithDiagnostics(
                  pipe, request_id, game, previous_snapshot, state_revision,
                  checkpoint_submission, published_checkpoint_sequence);
            }
          }
          } else if (step == "resume-map") {
          const auto result = xar::game::SubmitResumeMap(game);
          if (result == xar::game::ResumeSubmitResult::unavailable) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, false,
                                         "CK3 map state is unavailable"));
          } else {
            const std::string_view status =
                result == xar::game::ResumeSubmitResult::submitted
                    ? "submitted"
                    : "already_running";
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, true, status));
            if (connected) {
              // Symmetric with pause-map: already_running forces one fresh
              // state frame.  The ACK remains insufficient on its own;
              // Python still verifies paused=false.
              if (result == xar::game::ResumeSubmitResult::already_running) {
                previous_snapshot.reset();
              }
              connected = PublishTimelineSnapshotWithDiagnostics(
                  pipe, request_id, game, previous_snapshot, state_revision,
                  checkpoint_submission, published_checkpoint_sequence);
            }
          }
          } else if (step == "save-checkpoint") {
          const auto result = xar::game::SubmitSaveCheckpoint(game);
          if (result.status ==
              xar::game::SaveCheckpointStatus::submitted) {
            ++checkpoint_submission.sequence;
            checkpoint_submission.date_raw = result.date_raw;
            connected = xar::bridge::WriteFrame(
                pipe,
                SaveCheckpointResultFrame(request_id, checkpoint_submission));
            if (connected) {
              connected = PublishSnapshot(pipe, game, previous_snapshot,
                                          state_revision, checkpoint_submission,
                                          published_checkpoint_sequence);
            }
          } else {
            const std::string_view error =
                result.status ==
                        xar::game::SaveCheckpointStatus::map_not_ready
                    ? "CK3 map is not ready"
                    : "CK3 save state is unavailable";
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, false, error));
          }
        } else if (step == "accept-pending-character-interaction" ||
                   step == "reject-pending-character-interaction") {
          const auto reply =
              step == "accept-pending-character-interaction"
                  ? xar::game::PendingInteractionReply::accept
                  : xar::game::PendingInteractionReply::reject;
          const auto result =
              xar::game::SubmitReplyToPendingInteraction(game, reply);
          if (result ==
              xar::game::ReplyPendingInteractionResult::submitted) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, true, "submitted"));
          } else {
            std::string_view error =
                "CK3 pending character interaction state is unavailable";
            if (result == xar::game::ReplyPendingInteractionResult::
                              no_pending_interaction) {
              error = "no pending CK3 character interaction";
            } else if (result == xar::game::ReplyPendingInteractionResult::
                                     acknowledgement_required) {
              error = "pending CK3 interaction requires acknowledgement";
            }
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, false, error));
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision, checkpoint_submission,
                                        published_checkpoint_sequence);
          }
        } else if (step ==
                   "acknowledge-pending-character-interaction") {
          std::uint64_t expected_revision = 0;
          std::int32_t pending_interaction_id = -1;
          if (!xar::ck3_11906::
                  ParsePendingCharacterInteractionContextRequestV1(
                      incoming.payload, expected_revision,
                      pending_interaction_id)) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "ACK requires expected_revision and a valid signed "
                          "full pending_interaction_id"));
          } else if (expected_revision != state_revision) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "pending interaction ACK snapshot revision mismatch"));
          } else {
            const auto result =
                xar::game::SubmitAcknowledgePendingInteraction(
                    game, pending_interaction_id);
            if (result == xar::game::AcknowledgePendingInteractionResult::
                              submitted) {
              connected = xar::bridge::WriteFrame(
                  pipe,
                  CommandResultFrame(request_id, step, true, "submitted"));
            } else {
              std::string_view error =
                  "CK3 pending interaction ACK state is unavailable";
              if (result == xar::game::AcknowledgePendingInteractionResult::
                                no_pending_interaction) {
                error = "no pending CK3 character interaction";
              } else if (
                  result == xar::game::AcknowledgePendingInteractionResult::
                                pending_interaction_mismatch) {
                error = "pending CK3 interaction full ID mismatch";
              } else if (
                  result == xar::game::AcknowledgePendingInteractionResult::
                                acknowledgement_not_required) {
                error = "pending CK3 interaction is not an ACK notification";
              } else if (
                  result == xar::game::AcknowledgePendingInteractionResult::
                                requires_paused) {
                error = "pending CK3 interaction ACK requires a paused map";
              } else if (
                  result == xar::game::AcknowledgePendingInteractionResult::
                                not_for_played_character) {
                error = "pending CK3 interaction is not routed to the played "
                        "character";
              } else if (
                  result == xar::game::AcknowledgePendingInteractionResult::
                                state_changed) {
                error = "pending CK3 interaction changed before ACK submit";
              } else if (
                  result == xar::game::AcknowledgePendingInteractionResult::
                                queue_rejected) {
                error = "CK3 rejected the pending interaction ACK queue entry";
              }
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, false, error));
            }
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision, checkpoint_submission,
                                        published_checkpoint_sequence);
          }
        } else if (step == "query-arrange-marriage-choices") {
          marriage_choices.clear();
          xar::game::ArrangeMarriageQueryDiagnostics diagnostics{};
          const auto result = xar::game::ReadArrangeMarriageChoices(
              game, marriage_choices, diagnostics);
          if (result == xar::game::
                            ReadArrangeMarriageChoicesResult::available) {
            ++marriage_query_sequence;
            connected = xar::bridge::WriteFrame(
                pipe, ArrangeMarriageChoicesResultFrame(
                          request_id, marriage_query_sequence,
                          marriage_choices, diagnostics));
          } else {
            const std::string_view error =
                result == xar::game::
                              ReadArrangeMarriageChoicesResult::
                                  no_played_character
                    ? "no living played CK3 character"
                    : "CK3 arrange-marriage query is unavailable";
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, false, error));
          }
        } else if (step.starts_with("arrange-marriage-")) {
          const xar::game::ArrangeMarriageChoice *selected = nullptr;
          for (const auto &candidate : marriage_choices) {
            if (MarriageStep(candidate) == step) {
              selected = &candidate;
              break;
            }
          }
          if (selected == nullptr) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "arrange-marriage choice is missing or stale; "
                          "query first"));
          } else {
            const auto result =
                xar::game::SubmitArrangeMarriage(game, *selected);
            if (result ==
                xar::game::ArrangeMarriageResult::submitted) {
              connected = xar::bridge::WriteFrame(
                  pipe,
                  CommandResultFrame(request_id, step, true, "submitted"));
              marriage_choices.clear();
            } else {
              std::string_view error =
                  "CK3 arrange-marriage state is unavailable";
              if (result == xar::game::ArrangeMarriageResult::
                                no_played_character) {
                error = "no living played CK3 character";
              } else if (result ==
                         xar::game::ArrangeMarriageResult::
                             candidate_not_found) {
                error = "CK3 arrange-marriage candidate was not found";
                marriage_choices.clear();
              } else if (result ==
                         xar::game::ArrangeMarriageResult::
                             choice_unavailable) {
                error = "CK3 arrange-marriage choice changed; query again";
                marriage_choices.clear();
              }
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, false, error));
            }
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision, checkpoint_submission,
                                        published_checkpoint_sequence);
          }
        } else if (step == xar::ck3_11906::kCampaignRootContextV1Step) {
          std::uint64_t expected_revision = 0;
          if (!xar::ck3_11906::ParseCampaignRootContextExpectedRevisionV1(
                  incoming.payload, expected_revision)) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "campaign-root expected revision is malformed"));
          } else if (expected_revision != state_revision) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "campaign-root snapshot revision is stale"));
          } else {
            xar::game::Snapshot current_snapshot{};
            if (!previous_snapshot.has_value() || state_revision == 0 ||
                !xar::game::ReadSnapshot(game, current_snapshot) ||
                current_snapshot != previous_snapshot.value() ||
                !current_snapshot.paused || !current_snapshot.map_ready ||
                !current_snapshot.has_played_character) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(
                            request_id, step, false,
                            "campaign-root snapshot changed or is not ready"));
            } else {
              xar::ck3_11906::CampaignRootContextMailboxContextV1 query{};
              query.mailbox = &g_main_thread_query_mailbox_v1;
              query.bindings = xar::ck3_11906::BindCurrentProcess(true);
              query.environment =
                  xar::ck3_11906::BindCampaignRootNativeEnvironmentV1(
                      reinterpret_cast<std::uintptr_t>(
                          GetModuleHandleW(nullptr)),
                      true);
              query.request.expected_snapshot_revision = expected_revision;
              query.expected_snapshot = current_snapshot;

              const auto submit =
                  xar::ck3_11906::TrySubmitMainThreadQueryV1(
                      g_main_thread_query_mailbox_v1,
                      &xar::ck3_11906::
                          ExecuteCampaignRootContextMailboxQueryV1,
                      &query, query.ticket);
              if (submit != xar::ck3_11906::
                                MainThreadQuerySubmitResultV1::submitted) {
                std::string_view error =
                    "application-main campaign-root executor is unavailable";
                if (submit == xar::ck3_11906::
                                  MainThreadQuerySubmitResultV1::
                                      paused_main_thread_not_observed) {
                  error = "paused application-main boundary is not ready";
                } else if (submit == xar::ck3_11906::
                                         MainThreadQuerySubmitResultV1::
                                             mailbox_busy) {
                  error = "application-main campaign-root executor is busy";
                }
                connected = xar::bridge::WriteFrame(
                    pipe, CommandResultFrame(request_id, step, false, error));
              } else {
                auto wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                    g_main_thread_query_mailbox_v1, query.ticket,
                    xar::ck3_11906::
                        kCampaignRootContextV1QueuedWaitBudgetMilliseconds);
                while (wait == xar::ck3_11906::
                                   MainThreadQueryWaitResultV1::
                                       timeout_executor_already_running) {
                  wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                      g_main_thread_query_mailbox_v1, query.ticket,
                      xar::ck3_11906::
                          kCampaignRootContextV1ExecutingWaitSliceMilliseconds);
                }

                xar::game::Snapshot completion_snapshot{};
                const bool completion_snapshot_stable =
                    wait == xar::ck3_11906::
                                MainThreadQueryWaitResultV1::completed &&
                    xar::game::ReadSnapshot(game, completion_snapshot) &&
                    completion_snapshot == current_snapshot;
                std::string response;
                if (wait == xar::ck3_11906::
                                MainThreadQueryWaitResultV1::completed &&
                    query.completion == xar::ck3_11906::
                                            CampaignRootContextMailboxCompletionV1::
                                                completed &&
                    completion_snapshot_stable) {
                  response = CampaignRootContextResultFrame(
                      request_id,
                      campaign_root_context_query_sequence + 1,
                      query.result);
                  if (!response.empty()) {
                    ++campaign_root_context_query_sequence;
                  }
                }
                if (response.empty()) {
                  const auto error =
                      xar::ck3_11906::CampaignRootContextFailureMessageV1(
                          wait, query.completion,
                          completion_snapshot_stable);
                  response = CommandResultFrame(request_id, step, false,
                                                error);
                }
                const auto reclaimed =
                    xar::ck3_11906::ReclaimMainThreadQueryV1(
                        g_main_thread_query_mailbox_v1, query.ticket);
                if (reclaimed != xar::ck3_11906::
                                     MainThreadQueryReclaimResultV1::
                                         reclaimed) {
                  response = CommandResultFrame(
                      request_id, step, false,
                      "application-main campaign-root result was not "
                      "reclaimable");
                }
                connected = xar::bridge::WriteFrame(pipe, response);
              }
            }
          }
        } else if (step == xar::ck3_11906::kLoadedFeatureManifestV1Step) {
          std::uint64_t expected_revision = 0;
          if (!xar::ck3_11906::ParseLoadedFeatureManifestExpectedRevisionV1(
                  incoming.payload, expected_revision)) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "loaded-feature expected revision is malformed"));
          } else if (expected_revision != state_revision) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "loaded-feature snapshot revision is stale"));
          } else {
            xar::game::Snapshot current_snapshot{};
            if (!previous_snapshot.has_value() || state_revision == 0 ||
                !xar::game::ReadSnapshot(game, current_snapshot) ||
                current_snapshot != previous_snapshot.value() ||
                !current_snapshot.paused || !current_snapshot.map_ready ||
                !current_snapshot.has_played_character) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(
                            request_id, step, false,
                            "loaded-feature snapshot changed or is not ready"));
            } else {
              xar::ck3_11906::LoadedFeatureManifestMailboxContextV1 query{};
              query.mailbox = &g_main_thread_query_mailbox_v1;
              query.bindings = xar::ck3_11906::BindCurrentProcess(true);
              query.environment =
                  xar::ck3_11906::BindLoadedFeatureManifestNativeEnvironmentV1(
                      reinterpret_cast<std::uintptr_t>(
                          GetModuleHandleW(nullptr)),
                      true);
              query.request.expected_snapshot_revision = expected_revision;
              query.expected_snapshot = current_snapshot;

              const auto submit =
                  xar::ck3_11906::TrySubmitMainThreadQueryV1(
                      g_main_thread_query_mailbox_v1,
                      &xar::ck3_11906::
                          ExecuteLoadedFeatureManifestMailboxQueryV1,
                      &query, query.ticket);
              if (submit != xar::ck3_11906::
                                MainThreadQuerySubmitResultV1::submitted) {
                std::string_view error =
                    "application-main loaded-feature executor is unavailable";
                if (submit == xar::ck3_11906::
                                  MainThreadQuerySubmitResultV1::
                                      paused_main_thread_not_observed) {
                  error = "paused application-main boundary is not ready";
                } else if (submit == xar::ck3_11906::
                                         MainThreadQuerySubmitResultV1::
                                             mailbox_busy) {
                  error = "application-main loaded-feature executor is busy";
                }
                connected = xar::bridge::WriteFrame(
                    pipe, CommandResultFrame(request_id, step, false, error));
              } else {
                auto wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                    g_main_thread_query_mailbox_v1, query.ticket,
                    xar::ck3_11906::
                        kLoadedFeatureManifestV1QueuedWaitBudgetMilliseconds);
                while (wait == xar::ck3_11906::
                                   MainThreadQueryWaitResultV1::
                                       timeout_executor_already_running) {
                  wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                      g_main_thread_query_mailbox_v1, query.ticket,
                      xar::ck3_11906::
                          kLoadedFeatureManifestV1ExecutingWaitSliceMilliseconds);
                }

                xar::game::Snapshot completion_snapshot{};
                const bool completion_snapshot_stable =
                    wait == xar::ck3_11906::
                                MainThreadQueryWaitResultV1::completed &&
                    xar::game::ReadSnapshot(game, completion_snapshot) &&
                    completion_snapshot == current_snapshot;
                std::string response;
                if (wait == xar::ck3_11906::
                                MainThreadQueryWaitResultV1::completed &&
                    query.completion == xar::ck3_11906::
                                            LoadedFeatureManifestMailboxCompletionV1::
                                                completed &&
                    completion_snapshot_stable) {
                  response = LoadedFeatureManifestResultFrame(
                      request_id,
                      loaded_feature_manifest_query_sequence + 1,
                      query.result);
                  if (!response.empty()) {
                    ++loaded_feature_manifest_query_sequence;
                  }
                }
                if (response.empty()) {
                  const auto error =
                      xar::ck3_11906::LoadedFeatureManifestFailureMessageV1(
                          wait, query.completion,
                          completion_snapshot_stable);
                  response = CommandResultFrame(request_id, step, false,
                                                error);
                }
                const auto reclaimed =
                    xar::ck3_11906::ReclaimMainThreadQueryV1(
                        g_main_thread_query_mailbox_v1, query.ticket);
                if (reclaimed != xar::ck3_11906::
                                     MainThreadQueryReclaimResultV1::
                                         reclaimed) {
                  response = CommandResultFrame(
                      request_id, step, false,
                      "application-main loaded-feature result was not "
                      "reclaimable");
                }
                connected = xar::bridge::WriteFrame(pipe, response);
              }
            }
          }
        } else if (
            step == xar::ck3_11906::
                        kPendingCharacterInteractionContextV1Step) {
          std::uint64_t expected_revision = 0;
          std::int32_t pending_interaction_id = -1;
          if (!xar::ck3_11906::
                  ParsePendingCharacterInteractionContextRequestV1(
                      incoming.payload, expected_revision,
                      pending_interaction_id)) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "pending-interaction context request is malformed"));
          } else if (expected_revision != state_revision) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "pending-interaction context snapshot revision is "
                          "stale"));
          } else {
            xar::game::Snapshot current_snapshot{};
            if (!previous_snapshot.has_value() || state_revision == 0 ||
                !xar::game::ReadSnapshot(game, current_snapshot) ||
                current_snapshot != previous_snapshot.value() ||
                !current_snapshot.paused || !current_snapshot.map_ready ||
                !current_snapshot.has_played_character ||
                !current_snapshot.played_character_alive ||
                !current_snapshot.has_pending_character_interaction ||
                current_snapshot.pending_character_interaction_id !=
                    pending_interaction_id) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(
                            request_id, step, false,
                            "pending-interaction context snapshot changed or "
                            "is not ready"));
            } else {
              xar::ck3_11906::
                  PendingCharacterInteractionContextMailboxContextV1 query{};
              query.mailbox = &g_main_thread_query_mailbox_v1;
              query.bindings = xar::ck3_11906::BindCurrentProcess(true);
              query.environment = xar::ck3_11906::
                  BindPendingCharacterInteractionNativeEnvironmentV1(
                      reinterpret_cast<std::uintptr_t>(
                          GetModuleHandleW(nullptr)),
                      true);
              query.access.invoke_local_routing =
                  &xar::ck3_11906::
                      InvokePendingCharacterInteractionLocalRoutingDirectV1;
              query.access.invoke_reply_validator =
                  &xar::ck3_11906::
                      InvokePendingCharacterInteractionReplyValidatorDirectV1;
              query.access.invoke_trigger_evaluator =
                  &xar::ck3_11906::
                      InvokePendingCharacterInteractionTriggerEvaluatorDirectV1;
              query.access.invoke_cost_evaluator =
                  &xar::ck3_11906::
                      InvokePendingCharacterInteractionCostEvaluatorDirectV1;
              query.access.invoke_common_war_relation =
                  &xar::ck3_11906::
                      InvokePendingCharacterInteractionCommonWarRelationDirectV1;
              query.access.invoke_target_type_registry =
                  &xar::ck3_11906::
                      InvokePendingCharacterInteractionTargetTypeRegistryDirectV1;
              query.access.invoke_script_identifier_name =
                  &xar::ck3_11906::
                      InvokePendingCharacterInteractionScriptIdentifierNameDirectV1;
              query.request.expected_snapshot_revision = expected_revision;
              query.request.pending_interaction_id = pending_interaction_id;
              query.request.played_character_id =
                  current_snapshot.played_character_id;
              query.expected_snapshot = current_snapshot;

              const auto submit =
                  xar::ck3_11906::TrySubmitMainThreadQueryV1(
                      g_main_thread_query_mailbox_v1,
                      &xar::ck3_11906::
                          ExecutePendingCharacterInteractionContextMailboxQueryV1,
                      &query, query.ticket);
              if (submit != xar::ck3_11906::
                                MainThreadQuerySubmitResultV1::submitted) {
                std::string_view error =
                    "application-main pending-interaction context executor "
                    "is unavailable";
                if (submit == xar::ck3_11906::
                                  MainThreadQuerySubmitResultV1::
                                      paused_main_thread_not_observed) {
                  error = "paused application-main boundary is not ready";
                } else if (submit == xar::ck3_11906::
                                         MainThreadQuerySubmitResultV1::
                                             mailbox_busy) {
                  error =
                      "application-main pending-interaction context executor "
                      "is busy";
                }
                connected = xar::bridge::WriteFrame(
                    pipe, CommandResultFrame(request_id, step, false, error));
              } else {
                auto wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                    g_main_thread_query_mailbox_v1, query.ticket,
                    xar::ck3_11906::
                        kPendingCharacterInteractionContextV1QueuedWaitBudgetMilliseconds);
                while (wait == xar::ck3_11906::
                                   MainThreadQueryWaitResultV1::
                                       timeout_executor_already_running) {
                  wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                      g_main_thread_query_mailbox_v1, query.ticket,
                      xar::ck3_11906::
                          kPendingCharacterInteractionContextV1ExecutingWaitSliceMilliseconds);
                }

                xar::game::Snapshot completion_snapshot{};
                const bool completion_snapshot_stable =
                    wait == xar::ck3_11906::
                                MainThreadQueryWaitResultV1::completed &&
                    xar::game::ReadSnapshot(game, completion_snapshot) &&
                    completion_snapshot == current_snapshot;
                std::string response;
                if (wait == xar::ck3_11906::
                                MainThreadQueryWaitResultV1::completed &&
                    query.completion ==
                        xar::ck3_11906::
                            PendingCharacterInteractionContextMailboxCompletionV1::
                                completed &&
                    completion_snapshot_stable) {
                  response = PendingCharacterInteractionContextResultFrame(
                      request_id,
                      pending_character_interaction_context_query_sequence +
                          1,
                      query.result);
                  if (!response.empty()) {
                    ++pending_character_interaction_context_query_sequence;
                  }
                }
                if (response.empty()) {
                  const auto error = xar::ck3_11906::
                      PendingCharacterInteractionContextFailureMessageV1(
                          wait, query.completion,
                          completion_snapshot_stable);
                  response = CommandResultFrame(request_id, step, false,
                                                error);
                }
                const auto reclaimed =
                    xar::ck3_11906::ReclaimMainThreadQueryV1(
                        g_main_thread_query_mailbox_v1, query.ticket);
                if (reclaimed != xar::ck3_11906::
                                     MainThreadQueryReclaimResultV1::
                                         reclaimed) {
                  response = CommandResultFrame(
                      request_id, step, false,
                      "application-main pending-interaction context result "
                      "was not reclaimable");
                }
                connected = xar::bridge::WriteFrame(pipe, response);
              }
            }
          }
        } else if (step == xar::ck3_11906::kEventWindowContextV1Step) {
          std::uint64_t expected_revision = 0;
          std::int32_t event_instance_id = -1;
          if (!xar::ck3_11906::ParseEventWindowContextRequestV1(
                  incoming.payload, expected_revision,
                  event_instance_id)) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "event-window context request is malformed"));
          } else if (expected_revision != state_revision) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "event-window context snapshot revision is stale"));
          } else {
            xar::game::Snapshot current_snapshot{};
            if (!previous_snapshot.has_value() || state_revision == 0 ||
                !xar::game::ReadSnapshot(game, current_snapshot) ||
                current_snapshot != previous_snapshot.value() ||
                !current_snapshot.paused || !current_snapshot.map_ready ||
                !current_snapshot.has_played_character ||
                !current_snapshot.played_character_alive ||
                !current_snapshot.has_active_event ||
                current_snapshot.active_event_instance_id !=
                    event_instance_id) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(
                            request_id, step, false,
                            "event-window context snapshot changed or is not "
                            "ready"));
            } else {
              xar::ck3_11906::EventWindowContextMailboxContextV1 query{};
              query.mailbox = &g_main_thread_query_mailbox_v1;
              query.bindings = xar::ck3_11906::BindCurrentProcess(true);
              query.expected_snapshot = current_snapshot;
              query.expected_snapshot_revision = expected_revision;
              query.expected_event_instance_id = event_instance_id;

              const auto submit =
                  xar::ck3_11906::TrySubmitMainThreadQueryV1(
                      g_main_thread_query_mailbox_v1,
                      &xar::ck3_11906::
                          ExecuteEventWindowContextMailboxQueryV1,
                      &query, query.ticket);
              if (submit != xar::ck3_11906::
                                MainThreadQuerySubmitResultV1::submitted) {
                std::string_view error =
                    "application-main event-window executor is unavailable";
                if (submit == xar::ck3_11906::
                                  MainThreadQuerySubmitResultV1::
                                      paused_main_thread_not_observed) {
                  error = "paused application-main boundary is not ready";
                } else if (submit == xar::ck3_11906::
                                         MainThreadQuerySubmitResultV1::
                                             mailbox_busy) {
                  error = "application-main event-window executor is busy";
                }
                connected = xar::bridge::WriteFrame(
                    pipe, CommandResultFrame(request_id, step, false, error));
              } else {
                auto wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                    g_main_thread_query_mailbox_v1, query.ticket,
                    xar::ck3_11906::
                        kEventWindowContextV1QueuedWaitBudgetMilliseconds);
                while (wait == xar::ck3_11906::
                                   MainThreadQueryWaitResultV1::
                                       timeout_executor_already_running) {
                  wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                      g_main_thread_query_mailbox_v1, query.ticket,
                      xar::ck3_11906::
                          kEventWindowContextV1ExecutingWaitSliceMilliseconds);
                }

                xar::game::Snapshot completion_snapshot{};
                const bool completion_snapshot_stable =
                    wait == xar::ck3_11906::
                                MainThreadQueryWaitResultV1::completed &&
                    xar::game::ReadSnapshot(game, completion_snapshot) &&
                    completion_snapshot == current_snapshot;
                std::string response;
                if (wait == xar::ck3_11906::
                                MainThreadQueryWaitResultV1::completed &&
                    query.completion ==
                        xar::ck3_11906::
                            EventWindowContextMailboxCompletionV1::completed &&
                    completion_snapshot_stable) {
                  response = EventWindowContextResultFrame(
                      request_id, event_window_context_query_sequence + 1,
                      query.result);
                  if (!response.empty()) {
                    ++event_window_context_query_sequence;
                  }
                }
                if (response.empty()) {
                  const auto error =
                      xar::ck3_11906::EventWindowContextFailureMessageV1(
                          wait, query.completion,
                          completion_snapshot_stable);
                  response = CommandResultFrame(request_id, step, false,
                                                error);
                }
                const auto reclaimed =
                    xar::ck3_11906::ReclaimMainThreadQueryV1(
                        g_main_thread_query_mailbox_v1, query.ticket);
                if (reclaimed != xar::ck3_11906::
                                     MainThreadQueryReclaimResultV1::
                                         reclaimed) {
                  response = CommandResultFrame(
                      request_id, step, false,
                      "application-main event-window result was not "
                      "reclaimable");
                }
                connected = xar::bridge::WriteFrame(pipe, response);
              }
            }
          }
        } else if (step == "query-declarable-wars") {
          declarable_wars.clear();
          if (!xar::game::ReadDeclarableWars(game, declarable_wars)) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "CK3 declarable-war query is unavailable"));
          } else {
            ++declaration_query_sequence;
            connected = xar::bridge::WriteFrame(
                pipe, DeclarableWarsResultFrame(
                          request_id, declaration_query_sequence,
                          declarable_wars));
          }
        } else if (step.starts_with(
                       xar::ck3_11906::kWarEntryAssessmentsV1StepPrefix)) {
          std::vector<std::int32_t> target_character_ids;
          if (!xar::ck3_11906::ParseWarEntryAssessmentsV1Step(
                  step, target_character_ids)) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "war-entry assessment request is malformed"));
          } else if (target_character_ids.size() !=
                     static_cast<std::size_t>(xar::ck3_11906::
                         kWarEntryAssessmentsV1FirstLiveMaximumTargets)) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "first-live war-entry query requires one target"));
          } else {
            xar::game::Snapshot current_snapshot{};
            std::vector<xar::game::DeclarableWarSnapshot>
                current_declarations;
            if (!previous_snapshot.has_value() || state_revision == 0 ||
                !xar::game::ReadSnapshot(game, current_snapshot) ||
                current_snapshot != previous_snapshot.value()) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(
                            request_id, step, false,
                            "war-entry snapshot changed; retry after heartbeat"));
            } else if (xar::game::ReadDeclarableWarsForTarget(
                           game, target_character_ids.front(),
                           current_declarations) !=
                       xar::game::ReadDeclarableWarsResult::available) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(
                            request_id, step, false,
                            "war-entry declarations are unavailable"));
            } else {
              WarEntryBridgeFrameContext frame_context{};
              frame_context.game = &game;
              frame_context.expected_snapshot_revision = state_revision;
              frame_context.expected_snapshot = current_snapshot;
              for (const auto &declaration : current_declarations) {
                if (declaration.target_character_id > 0 &&
                    std::find(frame_context
                                  .expected_declarable_target_character_ids
                                  .begin(),
                              frame_context
                                  .expected_declarable_target_character_ids
                                  .end(),
                              declaration.target_character_id) ==
                        frame_context
                            .expected_declarable_target_character_ids.end()) {
                  frame_context.expected_declarable_target_character_ids
                      .push_back(declaration.target_character_id);
                }
              }

              xar::ck3_11906::WarEntryAssessmentMailboxContextV1 query{};
              query.mailbox = &g_main_thread_query_mailbox_v1;
              query.environment =
                  xar::ck3_11906::BindWarEntryNativeEnvironmentV1(
                      reinterpret_cast<std::uintptr_t>(
                          GetModuleHandleW(nullptr)));
              query.access.context = &frame_context;
              query.access.capture_frame = &CaptureWarEntryBridgeFrame;
              query.request.expected_snapshot_revision = state_revision;
              query.request.target_character_ids = target_character_ids;

              const auto submit =
                  xar::ck3_11906::TrySubmitMainThreadQueryV1(
                      g_main_thread_query_mailbox_v1,
                      &xar::ck3_11906::
                          ExecuteWarEntryAssessmentMailboxQueryV1,
                      &query, query.ticket);
              if (submit != xar::ck3_11906::
                                MainThreadQuerySubmitResultV1::submitted) {
                std::string_view error =
                    "application-main war-entry executor is unavailable";
                if (submit == xar::ck3_11906::
                                  MainThreadQuerySubmitResultV1::
                                      paused_main_thread_not_observed) {
                  error =
                      "paused application-main boundary is not ready";
                } else if (submit == xar::ck3_11906::
                                         MainThreadQuerySubmitResultV1::
                                             mailbox_busy) {
                  error = "application-main war-entry executor is busy";
                }
                connected = xar::bridge::WriteFrame(
                    pipe, CommandResultFrame(request_id, step, false, error));
              } else {
                auto wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                    g_main_thread_query_mailbox_v1, query.ticket, 2000);
                while (wait == xar::ck3_11906::
                                   MainThreadQueryWaitResultV1::
                                       timeout_executor_already_running) {
                  // The stack context is owned by the executing application
                  // thread. It must remain alive until the synchronous typed
                  // reader reaches a terminal state.
                  wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                      g_main_thread_query_mailbox_v1, query.ticket, 2000);
                }

                std::string response;
                if (wait == xar::ck3_11906::
                                MainThreadQueryWaitResultV1::completed &&
                    query.completion == xar::ck3_11906::
                                            WarEntryAssessmentMailboxCompletionV1::
                                                available) {
                  ++war_entry_assessment_query_sequence;
                  response = WarEntryAssessmentsResultFrame(
                      request_id, step,
                      war_entry_assessment_query_sequence, query.result);
                }
                if (response.empty()) {
                  std::string error =
                      "application-main war-entry query failed";
                  if (!query.result.unavailable_stage.empty()) {
                    error += ":";
                    error += query.result.unavailable_stage;
                  }
                  response = CommandResultFrame(request_id, step, false,
                                                error);
                }
                const auto reclaimed =
                    xar::ck3_11906::ReclaimMainThreadQueryV1(
                        g_main_thread_query_mailbox_v1, query.ticket);
                if (reclaimed != xar::ck3_11906::
                                     MainThreadQueryReclaimResultV1::
                                         reclaimed) {
                  response = CommandResultFrame(
                      request_id, step, false,
                      "application-main war-entry result was not reclaimable");
                }
                connected = xar::bridge::WriteFrame(pipe, response);
              }
            }
          }
        } else if (step == "query-army-strengths-v1") {
          std::vector<xar::game::ArmyStrengthSnapshot> strengths;
          const auto query_result =
              xar::game::ReadArmyStrengths(game, strengths);
          if (query_result ==
                  xar::game::ReadArmyStrengthsResult::available ||
              query_result ==
                  xar::game::ReadArmyStrengthsResult::partial) {
            ++army_strength_query_sequence;
            connected = xar::bridge::WriteFrame(
                pipe, ArmyStrengthsResultFrame(
                          request_id, army_strength_query_sequence,
                          query_result, strengths));
          } else {
            std::string_view error =
                "CK3 army-strength query is unavailable";
            if (query_result ==
                xar::game::ReadArmyStrengthsResult::requires_paused) {
              error = "CK3 army-strength query requires a paused map";
            } else if (query_result ==
                       xar::game::ReadArmyStrengthsResult::
                           no_played_character) {
              error = "no living played CK3 character";
            }
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, false, error));
          }
        } else if (step.starts_with(
                       "query-combat-simulation-inputs-v3-")) {
          xar::game::CombatSimulationInputsRequest combat_request{};
          std::uint64_t expected_revision = 0;
          if (!xar::game::ParseCombatSimulationInputsV3Step(
                  step, combat_request) ||
              !xar::ck3_11906::
                  ParseCombatSimulationInputsV3ExpectedRevision(
                      incoming.payload, expected_revision)) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "combat-input v3 query step is not canonical"));
          } else if (expected_revision != state_revision) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "combat-input v3 expected revision is stale"));
          } else {
            xar::game::Snapshot current_snapshot{};
            if (!previous_snapshot.has_value() || state_revision == 0 ||
                !xar::game::ReadSnapshot(game, current_snapshot) ||
                current_snapshot != previous_snapshot.value() ||
                !current_snapshot.paused) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(
                            request_id, step, false,
                            "combat-input v3 snapshot changed; retry after heartbeat"));
            } else {
              xar::ck3_11906::CombatSimulationInputsV3MailboxContext query{};
              query.mailbox = &g_main_thread_query_mailbox_v1;
              query.bindings = xar::ck3_11906::BindCurrentProcess(true);
              query.request = combat_request;
              query.expected_snapshot_revision = expected_revision;
              query.expected_snapshot = current_snapshot;
              query.module_base = reinterpret_cast<std::uintptr_t>(
                  GetModuleHandleW(nullptr));

              const auto submit =
                  xar::ck3_11906::TrySubmitMainThreadQueryV1(
                      g_main_thread_query_mailbox_v1,
                      &xar::ck3_11906::
                          ExecuteCombatSimulationInputsV3MailboxQuery,
                      &query, query.ticket);
              if (submit != xar::ck3_11906::
                                MainThreadQuerySubmitResultV1::submitted) {
                std::string_view error =
                    "application-main combat-input v3 executor is unavailable";
                if (submit == xar::ck3_11906::
                                  MainThreadQuerySubmitResultV1::
                                      paused_main_thread_not_observed) {
                  error = "paused application-main boundary is not ready";
                } else if (submit == xar::ck3_11906::
                                         MainThreadQuerySubmitResultV1::
                                             mailbox_busy) {
                  error = "application-main combat-input v3 executor is busy";
                }
                connected = xar::bridge::WriteFrame(
                    pipe, CommandResultFrame(request_id, step, false, error));
              } else {
                auto wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                    g_main_thread_query_mailbox_v1, query.ticket,
                    xar::ck3_11906::
                        kCombatSimulationInputsV3QueuedWaitBudgetMilliseconds);
                while (wait == xar::ck3_11906::
                                   MainThreadQueryWaitResultV1::
                                       timeout_executor_already_running) {
                  // The application-main reader owns the stack context after
                  // execution starts.  Retain it until terminal/reclaim even
                  // when the exact CK3 phase model is expensive.
                  wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                      g_main_thread_query_mailbox_v1, query.ticket,
                      xar::ck3_11906::
                          kCombatSimulationInputsV3ExecutingWaitSliceMilliseconds);
                }

                std::string response;
                bool completion_snapshot_stable = false;
                const bool typed_result =
                    query.completion == xar::ck3_11906::
                                            CombatSimulationInputsV3MailboxCompletion::
                                                available ||
                    query.completion == xar::ck3_11906::
                                            CombatSimulationInputsV3MailboxCompletion::
                                                phase_inputs_unavailable;
                if (wait == xar::ck3_11906::
                                MainThreadQueryWaitResultV1::completed &&
                    typed_result) {
                  xar::game::Snapshot completion_snapshot{};
                  if (state_revision == expected_revision &&
                      previous_snapshot.has_value() &&
                      xar::game::ReadSnapshot(game, completion_snapshot) &&
                      completion_snapshot == current_snapshot &&
                      completion_snapshot == previous_snapshot.value()) {
                    completion_snapshot_stable = true;
                    ++combat_inputs_query_sequence;
                    response = CombatSimulationInputsV3ResultFrame(
                        request_id, step, combat_inputs_query_sequence,
                        query.query_result, query.result);
                  }
                }
                if (response.empty()) {
                  const auto error = xar::ck3_11906::
                      CombatSimulationInputsV3FailureMessage(
                          wait, query.completion, query.query_result,
                          completion_snapshot_stable);
                  response =
                      CommandResultFrame(request_id, step, false, error);
                }
                const auto reclaimed =
                    xar::ck3_11906::ReclaimMainThreadQueryV1(
                        g_main_thread_query_mailbox_v1, query.ticket);
                if (reclaimed != xar::ck3_11906::
                                     MainThreadQueryReclaimResultV1::
                                         reclaimed) {
                  response = CommandResultFrame(
                      request_id, step, false,
                      "application-main combat-input v3 result was not reclaimable");
                }
                connected = xar::bridge::WriteFrame(pipe, response);
              }
            }
          }
        } else if (step.starts_with(
                       "query-combat-simulation-inputs-v2-")) {
          xar::game::CombatSimulationInputsRequest combat_request{};
          if (!xar::game::ParseCombatSimulationInputsStep(step,
                                                          combat_request)) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "combat-input query step is not canonical"));
          } else {
            xar::game::CombatSimulationInputsSnapshot snapshot{};
            const auto query_result =
                xar::game::ReadCombatSimulationInputs(game, combat_request,
                                                      snapshot);
            if (query_result ==
                    xar::game::ReadCombatSimulationInputsResult::available ||
                query_result ==
                    xar::game::ReadCombatSimulationInputsResult::partial) {
              ++combat_inputs_query_sequence;
              connected = xar::bridge::WriteFrame(
                  pipe, CombatSimulationInputsResultFrame(
                            request_id, step, combat_inputs_query_sequence,
                            query_result, snapshot));
            } else {
              std::string_view error =
                  "CK3 combat-input query is unavailable";
              switch (query_result) {
              case xar::game::ReadCombatSimulationInputsResult::
                  requires_paused:
                error = "CK3 combat-input query requires a paused map";
                break;
              case xar::game::ReadCombatSimulationInputsResult::
                  no_played_character:
                error = "no living played CK3 character";
                break;
              case xar::game::ReadCombatSimulationInputsResult::
                  invalid_arguments:
                error = "combat-input query arguments are invalid";
                break;
              case xar::game::ReadCombatSimulationInputsResult::
                  target_province_not_found:
                error = "combat-input target province was not found";
                break;
              case xar::game::ReadCombatSimulationInputsResult::
                  army_not_in_scope:
                error = "combat-input army is outside allowed scope";
                break;
              case xar::game::ReadCombatSimulationInputsResult::
                  invalid_encounter:
                error = "selected armies do not form a canonical encounter";
                break;
              case xar::game::ReadCombatSimulationInputsResult::available:
              case xar::game::ReadCombatSimulationInputsResult::partial:
              case xar::game::ReadCombatSimulationInputsResult::unavailable:
                break;
              }
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, false, error));
            }
          }
        } else if (step.starts_with("declare-war-")) {
          const xar::game::DeclarableWarSnapshot *selected = nullptr;
          for (const auto &candidate : declarable_wars) {
            if (DeclarationStep(candidate) == step) {
              selected = &candidate;
              break;
            }
          }
          if (selected == nullptr) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "declare-war choice is missing or stale; query first"));
          } else {
            const auto result =
                xar::game::SubmitDeclareWar(game, *selected);
            if (result == xar::game::DeclareWarResult::submitted) {
              connected = xar::bridge::WriteFrame(
                  pipe,
                  CommandResultFrame(request_id, step, true, "submitted"));
              declarable_wars.clear();
            } else {
              std::string_view error = "CK3 declare-war state is unavailable";
              if (result ==
                  xar::game::DeclareWarResult::no_played_character) {
                error = "no living played CK3 character";
              } else if (result ==
                         xar::game::DeclareWarResult::target_not_found) {
                error = "CK3 declare-war target was not found";
              } else if (
                  result == xar::game::DeclareWarResult::
                                declaration_unavailable) {
                error = "CK3 declare-war choice changed; query again";
              } else if (result ==
                         xar::game::DeclareWarResult::validation_failed) {
                error = "CK3 rejected declare-war validation";
              }
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, false, error));
            }
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision, checkpoint_submission,
                                        published_checkpoint_sequence);
          }
        } else if (step.starts_with(
                       "query-war-termination-options-")) {
          const auto war_id = WarTerminationQueryStep(step);
          if (!war_id.has_value()) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "invalid query-war-termination-options-<war_id> "
                          "step"));
          } else {
            std::uint64_t expected_revision = 0;
            if (!xar::ck3_11906::
                    ParseCampaignRootContextExpectedRevisionV1(
                        incoming.payload, expected_revision)) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(
                            request_id, step, false,
                            "war-termination expected revision is malformed"));
            } else if (expected_revision != state_revision) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(
                            request_id, step, false,
                            "war-termination snapshot revision is stale"));
            } else if (!previous_snapshot.has_value() ||
                       state_revision == 0) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(
                            request_id, step, false,
                            "war-termination admission snapshot is "
                            "unavailable"));
            } else {
              xar::game::Snapshot admission_snapshot{};
              if (!xar::game::ReadSnapshot(game, admission_snapshot)) {
                connected = xar::bridge::WriteFrame(
                    pipe, CommandResultFrame(
                              request_id, step, false,
                              "war-termination admission snapshot read "
                              "failed"));
              } else if (admission_snapshot != previous_snapshot.value()) {
                connected = PublishSnapshot(
                    pipe, game, previous_snapshot, state_revision,
                    checkpoint_submission, published_checkpoint_sequence);
                if (connected) {
                  connected = xar::bridge::WriteFrame(
                      pipe, CommandResultFrame(
                                request_id, step, false,
                                "war-termination admission snapshot changed; "
                                "retry after heartbeat"));
                }
              } else if (!admission_snapshot.paused ||
                         !admission_snapshot.map_ready ||
                         !admission_snapshot.has_played_character ||
                         !admission_snapshot.played_character_alive) {
                connected = xar::bridge::WriteFrame(
                    pipe, CommandResultFrame(
                              request_id, step, false,
                              "war-termination query requires a ready paused "
                              "living player snapshot"));
              } else {
                xar::game::WarTerminationOptionsSnapshot options{};
                const auto query_result =
                    xar::game::ReadWarTerminationOptions(
                        game, war_id.value(), options);
                xar::game::Snapshot completion_snapshot{};
                if (!xar::game::ReadSnapshot(game, completion_snapshot)) {
                  connected = xar::bridge::WriteFrame(
                      pipe, CommandResultFrame(
                                request_id, step, false,
                                "war-termination completion snapshot read "
                                "failed"));
                } else if (completion_snapshot != admission_snapshot) {
                  connected = PublishSnapshot(
                      pipe, game, previous_snapshot, state_revision,
                      checkpoint_submission, published_checkpoint_sequence);
                  if (connected) {
                    connected = xar::bridge::WriteFrame(
                        pipe, CommandResultFrame(
                                  request_id, step, false,
                                  "war-termination completion snapshot "
                                  "changed; retry after heartbeat"));
                  }
                } else if (
                    query_result ==
                    xar::game::ReadWarTerminationOptionsResult::available) {
                  const auto next_query_sequence =
                      war_termination_query_sequence + 1;
                  connected = xar::bridge::WriteFrame(
                      pipe, WarTerminationOptionsResultFrame(
                                request_id, step, next_query_sequence,
                                options));
                  if (connected) {
                    war_termination_query_sequence = next_query_sequence;
                  }
                } else {
                  std::string_view error =
                      "CK3 war-termination query is unavailable";
                  if (query_result ==
                      xar::game::ReadWarTerminationOptionsResult::
                          requires_paused) {
                    error =
                        "CK3 war-termination query requires a paused map";
                  } else if (query_result ==
                             xar::game::ReadWarTerminationOptionsResult::
                                 no_played_character) {
                    error = "no living played CK3 character";
                  } else if (query_result ==
                             xar::game::ReadWarTerminationOptionsResult::
                                 war_not_found) {
                    error = "CK3 war was not found";
                  } else if (query_result ==
                             xar::game::ReadWarTerminationOptionsResult::
                                 player_not_participant) {
                    error =
                        "played CK3 character is not a war participant";
                  }
                  connected = xar::bridge::WriteFrame(
                      pipe,
                      CommandResultFrame(request_id, step, false, error));
                }
              }
            }
          }
        } else if (step.starts_with(
                       "query-war-termination-terms-v1-")) {
          const auto war_id = WarTerminationTermsQueryStep(step);
          if (!war_id.has_value()) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "invalid query-war-termination-terms-v1-<war_id> "
                          "step"));
          } else {
            xar::game::WarTerminationTermsSnapshot terms{};
            const auto query_result = xar::game::ReadWarTerminationTerms(
                game, war_id.value(), terms);
            if (query_result ==
                    xar::game::ReadWarTerminationTermsResult::available ||
                query_result ==
                    xar::game::ReadWarTerminationTermsResult::
                        unsupported_casus_belli) {
              ++war_termination_terms_query_sequence;
              connected = xar::bridge::WriteFrame(
                  pipe, WarTerminationTermsResultFrame(
                            request_id, step,
                            war_termination_terms_query_sequence, terms,
                            query_result ==
                                xar::game::ReadWarTerminationTermsResult::
                                    available));
            } else {
              std::string_view error =
                  "CK3 war-termination terms query is unavailable";
              if (query_result ==
                  xar::game::ReadWarTerminationTermsResult::
                      requires_paused) {
                error =
                    "CK3 war-termination terms query requires a paused map";
              } else if (query_result ==
                         xar::game::ReadWarTerminationTermsResult::
                             no_played_character) {
                error = "no living played CK3 character";
              } else if (query_result ==
                         xar::game::ReadWarTerminationTermsResult::
                             war_not_found) {
                error = "CK3 war was not found";
              } else if (query_result ==
                         xar::game::ReadWarTerminationTermsResult::
                             player_not_participant) {
                error = "played CK3 character is not a war participant";
              }
              connected = xar::bridge::WriteFrame(
                  pipe,
                  CommandResultFrame(request_id, step, false, error));
            }
          }
        } else if (step.starts_with("offer-white-peace-")) {
          const auto war_id = OfferWhitePeaceStep(step);
          if (!war_id.has_value()) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "invalid offer-white-peace-<war_id> step"));
          } else {
            const auto white_peace_result =
                xar::game::SubmitOfferWhitePeace(game, war_id.value());
            if (white_peace_result ==
                xar::game::OfferWhitePeaceResult::submitted) {
              connected = xar::bridge::WriteFrame(
                  pipe,
                  CommandResultFrame(request_id, step, true, "submitted"));
            } else {
              std::string_view error =
                  "CK3 offer-white-peace state is unavailable";
              if (white_peace_result ==
                  xar::game::OfferWhitePeaceResult::submission_failed) {
                error = "CK3 rejected offer-white-peace queue submission";
              } else if (white_peace_result ==
                         xar::game::OfferWhitePeaceResult::requires_paused) {
                error = "CK3 offer-white-peace requires a paused map";
              } else if (white_peace_result ==
                         xar::game::OfferWhitePeaceResult::
                             no_played_character) {
                error = "no living played CK3 character";
              } else if (white_peace_result ==
                         xar::game::OfferWhitePeaceResult::war_not_found) {
                error = "CK3 war was not found";
              } else if (white_peace_result ==
                         xar::game::OfferWhitePeaceResult::
                             player_not_participant) {
                error = "played CK3 character is not a war participant";
              } else if (white_peace_result ==
                         xar::game::OfferWhitePeaceResult::
                             player_not_war_leader) {
                error = "played CK3 character is not the war leader";
              } else if (white_peace_result ==
                         xar::game::OfferWhitePeaceResult::
                             casus_belli_unavailable) {
                error = "CK3 war has no active casus belli";
              } else if (white_peace_result ==
                         xar::game::OfferWhitePeaceResult::
                             white_peace_not_allowed) {
                error = "active CK3 casus belli forbids white peace";
              } else if (white_peace_result ==
                         xar::game::OfferWhitePeaceResult::
                             context_unavailable) {
                error = "CK3 offer-white-peace context is unavailable";
              } else if (white_peace_result ==
                         xar::game::OfferWhitePeaceResult::
                             validation_failed) {
                error = "CK3 rejected offer-white-peace validation";
              }
              connected = xar::bridge::WriteFrame(
                  pipe,
                  CommandResultFrame(request_id, step, false, error));
            }
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision,
                                        checkpoint_submission,
                                        published_checkpoint_sequence);
          }
        } else if (step.starts_with("surrender-war-")) {
          const auto war_id = SurrenderWarStep(step);
          if (!war_id.has_value()) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "invalid surrender-war-<war_id> step"));
          } else {
            const auto surrender_result = xar::game::SubmitSurrenderWar(
                game, war_id.value());
            if (surrender_result ==
                xar::game::SurrenderWarResult::submitted) {
              connected = xar::bridge::WriteFrame(
                  pipe,
                  CommandResultFrame(request_id, step, true, "submitted"));
            } else {
              std::string_view error =
                  "CK3 surrender-war state is unavailable";
              if (surrender_result ==
                  xar::game::SurrenderWarResult::submission_failed) {
                error = "CK3 rejected surrender-war queue submission";
              } else if (surrender_result ==
                         xar::game::SurrenderWarResult::requires_paused) {
                error = "CK3 surrender-war requires a paused map";
              } else if (surrender_result ==
                         xar::game::SurrenderWarResult::
                             no_played_character) {
                error = "no living played CK3 character";
              } else if (surrender_result ==
                         xar::game::SurrenderWarResult::war_not_found) {
                error = "CK3 war was not found";
              } else if (surrender_result ==
                         xar::game::SurrenderWarResult::
                             player_not_participant) {
                error = "played CK3 character is not a war participant";
              } else if (surrender_result ==
                         xar::game::SurrenderWarResult::
                             player_not_war_leader) {
                error = "played CK3 character is not the war leader";
              } else if (surrender_result ==
                         xar::game::SurrenderWarResult::
                             context_unavailable) {
                error = "CK3 surrender-war context is unavailable";
              } else if (surrender_result ==
                         xar::game::SurrenderWarResult::validation_failed) {
                error = "CK3 rejected surrender-war validation";
              }
              connected = xar::bridge::WriteFrame(
                  pipe,
                  CommandResultFrame(request_id, step, false, error));
            }
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision,
                                        checkpoint_submission,
                                        published_checkpoint_sequence);
          }
        } else if (step.starts_with("enforce-demands-")) {
          const auto war_id = EnforceDemandsStep(step);
          if (!war_id.has_value()) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "invalid enforce-demands-<war_id> step"));
          } else {
            const auto result = xar::game::SubmitEnforceDemands(
                game, war_id.value());
            if (result == xar::game::EnforceDemandsResult::submitted) {
              connected = xar::bridge::WriteFrame(
                  pipe,
                  CommandResultFrame(request_id, step, true, "submitted"));
            } else {
              std::string_view error =
                  "CK3 enforce-demands state is unavailable";
              if (result ==
                  xar::game::EnforceDemandsResult::
                      no_played_character) {
                error = "no living played CK3 character";
              } else if (result ==
                         xar::game::EnforceDemandsResult::war_not_found) {
                error = "CK3 war was not found";
              } else if (
                  result == xar::game::EnforceDemandsResult::
                                player_not_participant) {
                error = "played CK3 character is not a war participant";
              } else if (
                  result == xar::game::EnforceDemandsResult::
                                player_not_war_leader) {
                error = "played CK3 character is not the war leader";
              } else if (result ==
                         xar::game::EnforceDemandsResult::
                             validation_failed) {
                error = "CK3 rejected enforce-demands validation";
              }
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, false, error));
            }
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision, checkpoint_submission,
                                        published_checkpoint_sequence);
          }
        } else if (step == "raise-troops-default") {
          const auto result = xar::game::SubmitRaiseTroopsDefault(game);
          if (result == xar::game::RaiseTroopsResult::submitted) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, true, "submitted"));
          } else {
            std::string_view error = "CK3 raise-troops state is unavailable";
            if (result ==
                xar::game::RaiseTroopsResult::no_played_character) {
              error = "no living played CK3 character";
            } else if (result ==
                       xar::game::RaiseTroopsResult::no_default_province) {
              error = "no default CK3 rally province";
            } else if (result ==
                       xar::game::RaiseTroopsResult::validation_failed) {
              error = "CK3 rejected raise-troops validation";
            }
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, false, error));
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision, checkpoint_submission,
                                        published_checkpoint_sequence);
          }
        } else if (step.starts_with(
                       xar::ck3_11906::
                           kBattleReinforcementAssignmentV1StepPrefix)) {
          xar::game::BattleReinforcementAssignmentRequest
              reinforcement_request{};
          std::uint64_t expected_revision = 0;
          if (!xar::ck3_11906::
                   ParseBattleReinforcementAssignmentV1Step(
                       step, reinforcement_request) ||
              !xar::ck3_11906::
                   ParseBattleReinforcementAssignmentExpectedRevisionV1(
                       incoming.payload, expected_revision)) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "battle-reinforcement request is malformed"));
          } else if (expected_revision != state_revision) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "battle-reinforcement expected revision is stale"));
          } else {
            xar::game::Snapshot current_snapshot{};
            if (!previous_snapshot.has_value() || state_revision == 0 ||
                !xar::game::ReadSnapshot(game, current_snapshot) ||
                current_snapshot != previous_snapshot.value() ||
                !current_snapshot.paused) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(
                            request_id, step, false,
                            "battle-reinforcement snapshot changed; retry after heartbeat"));
            } else {
              xar::ck3_11906::
                  BattleReinforcementAssignmentMailboxContextV1 query{};
              query.mailbox = &g_main_thread_query_mailbox_v1;
              query.bindings = xar::ck3_11906::BindCurrentProcess(true);
              query.request = reinforcement_request;
              query.expected_snapshot_revision = expected_revision;
              query.expected_snapshot = current_snapshot;
              const auto submit =
                  xar::ck3_11906::TrySubmitMainThreadQueryV1(
                      g_main_thread_query_mailbox_v1,
                      &xar::ck3_11906::
                          ExecuteBattleReinforcementAssignmentMailboxQueryV1,
                      &query, query.ticket);
              if (submit !=
                  xar::ck3_11906::MainThreadQuerySubmitResultV1::submitted) {
                std::string_view error =
                    "application-main battle-reinforcement executor is unavailable";
                if (submit ==
                    xar::ck3_11906::MainThreadQuerySubmitResultV1::
                        paused_main_thread_not_observed) {
                  error = "paused application-main boundary is not ready";
                } else if (
                    submit ==
                    xar::ck3_11906::MainThreadQuerySubmitResultV1::
                        mailbox_busy) {
                  error =
                      "application-main battle-reinforcement executor is busy";
                }
                connected = xar::bridge::WriteFrame(
                    pipe,
                    CommandResultFrame(request_id, step, false, error));
              } else {
                auto wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                    g_main_thread_query_mailbox_v1, query.ticket,
                    xar::ck3_11906::
                        kBattleReinforcementAssignmentV1QueuedWaitBudgetMilliseconds);
                while (wait ==
                       xar::ck3_11906::MainThreadQueryWaitResultV1::
                           timeout_executor_already_running) {
                  wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                      g_main_thread_query_mailbox_v1, query.ticket,
                      xar::ck3_11906::
                          kBattleReinforcementAssignmentV1ExecutingWaitSliceMilliseconds);
                }
                std::string response;
                bool completion_snapshot_stable = false;
                if (wait ==
                        xar::ck3_11906::MainThreadQueryWaitResultV1::
                            completed &&
                    query.completion ==
                        xar::ck3_11906::
                            BattleReinforcementAssignmentMailboxCompletionV1::
                                completed) {
                  xar::game::Snapshot completion_snapshot{};
                  if (state_revision == expected_revision &&
                      previous_snapshot.has_value() &&
                      xar::game::ReadSnapshot(game, completion_snapshot) &&
                      completion_snapshot == current_snapshot &&
                      completion_snapshot == previous_snapshot.value()) {
                    completion_snapshot_stable = true;
                    response = BattleReinforcementAssignmentResultFrame(
                        request_id, step,
                        battle_reinforcement_assignment_query_sequence + 1,
                        query.result);
                    if (!response.empty()) {
                      ++battle_reinforcement_assignment_query_sequence;
                    }
                  }
                }
                if (response.empty()) {
                  const auto error = xar::ck3_11906::
                      BattleReinforcementAssignmentFailureMessageV1(
                          wait, query.completion,
                          completion_snapshot_stable);
                  response =
                      CommandResultFrame(request_id, step, false, error);
                }
                const auto reclaimed =
                    xar::ck3_11906::ReclaimMainThreadQueryV1(
                        g_main_thread_query_mailbox_v1, query.ticket);
                if (reclaimed !=
                    xar::ck3_11906::MainThreadQueryReclaimResultV1::
                        reclaimed) {
                  response = CommandResultFrame(
                      request_id, step, false,
                      "application-main battle-reinforcement result was not reclaimable");
                }
                connected = xar::bridge::WriteFrame(pipe, response);
              }
            }
          }
        } else if (step.starts_with(
                       xar::ck3_11906::
                           kBattleTerminalTransitionV1StepPrefix)) {
          xar::game::BattleTerminalTransitionRequestV1 terminal_request{};
          std::uint64_t expected_revision = 0;
          if (!xar::ck3_11906::ParseBattleTerminalTransitionV1Step(
                  step, terminal_request) ||
              !xar::ck3_11906::
                   ParseBattleTerminalTransitionExpectedRevisionV1(
                       incoming.payload, expected_revision)) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "battle-terminal-transition request is malformed"));
          } else if (expected_revision != state_revision) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "battle-terminal-transition expected revision is stale"));
          } else {
            xar::game::Snapshot current_snapshot{};
            if (!previous_snapshot.has_value() || state_revision == 0 ||
                !xar::game::ReadSnapshot(game, current_snapshot) ||
                current_snapshot != previous_snapshot.value() ||
                !current_snapshot.paused) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(
                            request_id, step, false,
                            "battle-terminal-transition snapshot changed; retry after heartbeat"));
            } else {
              xar::ck3_11906::BattleTerminalTransitionMailboxContextV1
                  query{};
              query.mailbox = &g_main_thread_query_mailbox_v1;
              query.bindings = xar::ck3_11906::BindCurrentProcess(true);
              query.request = terminal_request;
              query.expected_snapshot_revision = expected_revision;
              query.expected_snapshot = current_snapshot;
              const auto submit =
                  xar::ck3_11906::TrySubmitMainThreadQueryV1(
                      g_main_thread_query_mailbox_v1,
                      &xar::ck3_11906::
                          ExecuteBattleTerminalTransitionMailboxQueryV1,
                      &query, query.ticket);
              if (submit !=
                  xar::ck3_11906::MainThreadQuerySubmitResultV1::submitted) {
                std::string_view error =
                    "application-main battle-terminal-transition executor is unavailable";
                if (submit ==
                    xar::ck3_11906::MainThreadQuerySubmitResultV1::
                        paused_main_thread_not_observed) {
                  error = "paused application-main boundary is not ready";
                } else if (
                    submit ==
                    xar::ck3_11906::MainThreadQuerySubmitResultV1::
                        mailbox_busy) {
                  error =
                      "application-main battle-terminal-transition executor is busy";
                }
                connected = xar::bridge::WriteFrame(
                    pipe,
                    CommandResultFrame(request_id, step, false, error));
              } else {
                auto wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                    g_main_thread_query_mailbox_v1, query.ticket,
                    xar::ck3_11906::
                        kBattleTerminalTransitionV1QueuedWaitBudgetMilliseconds);
                while (wait ==
                       xar::ck3_11906::MainThreadQueryWaitResultV1::
                           timeout_executor_already_running) {
                  wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                      g_main_thread_query_mailbox_v1, query.ticket,
                      xar::ck3_11906::
                          kBattleTerminalTransitionV1ExecutingWaitSliceMilliseconds);
                }
                std::string response;
                bool completion_snapshot_stable = false;
                if (wait ==
                        xar::ck3_11906::MainThreadQueryWaitResultV1::
                            completed &&
                    query.completion ==
                        xar::ck3_11906::
                            BattleTerminalTransitionMailboxCompletionV1::
                                completed) {
                  xar::game::Snapshot completion_snapshot{};
                  if (state_revision == expected_revision &&
                      previous_snapshot.has_value() &&
                      xar::game::ReadSnapshot(game, completion_snapshot) &&
                      completion_snapshot == current_snapshot &&
                      completion_snapshot == previous_snapshot.value()) {
                    completion_snapshot_stable = true;
                    response = BattleTerminalTransitionResultFrame(
                        request_id, step,
                        battle_terminal_transition_query_sequence + 1,
                        query.result);
                    if (!response.empty()) {
                      ++battle_terminal_transition_query_sequence;
                    }
                  }
                }
                if (response.empty()) {
                  const auto error = xar::ck3_11906::
                      BattleTerminalTransitionFailureMessageV1(
                          wait, query.completion,
                          completion_snapshot_stable);
                  response =
                      CommandResultFrame(request_id, step, false, error);
                }
                const auto reclaimed =
                    xar::ck3_11906::ReclaimMainThreadQueryV1(
                        g_main_thread_query_mailbox_v1, query.ticket);
                if (reclaimed !=
                    xar::ck3_11906::MainThreadQueryReclaimResultV1::
                        reclaimed) {
                  response = CommandResultFrame(
                      request_id, step, false,
                      "application-main battle-terminal-transition result was not reclaimable");
                }
                connected = xar::bridge::WriteFrame(pipe, response);
              }
            }
          }
        } else if (step.starts_with(
                       xar::ck3_11906::kBattleTransitionV1StepPrefix)) {
          xar::game::BattleTransitionRequest transition_request{};
          std::uint64_t expected_revision = 0;
          if (!xar::ck3_11906::ParseBattleTransitionV1Step(
                  step, transition_request) ||
              !xar::ck3_11906::ParseBattleTransitionExpectedRevisionV1(
                  incoming.payload, expected_revision)) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "battle-transition request is malformed"));
          } else if (expected_revision != state_revision) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "battle-transition expected revision is stale"));
          } else {
            xar::game::Snapshot current_snapshot{};
            if (!previous_snapshot.has_value() || state_revision == 0 ||
                !xar::game::ReadSnapshot(game, current_snapshot) ||
                current_snapshot != previous_snapshot.value() ||
                !current_snapshot.paused) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(
                            request_id, step, false,
                            "battle-transition snapshot changed; retry after heartbeat"));
            } else {
              xar::ck3_11906::BattleTransitionMailboxContextV1 query{};
              query.mailbox = &g_main_thread_query_mailbox_v1;
              query.bindings = xar::ck3_11906::BindCurrentProcess(true);
              query.request = transition_request;
              query.expected_snapshot_revision = expected_revision;
              query.expected_snapshot = current_snapshot;
              const auto submit =
                  xar::ck3_11906::TrySubmitMainThreadQueryV1(
                      g_main_thread_query_mailbox_v1,
                      &xar::ck3_11906::
                          ExecuteBattleTransitionMailboxQueryV1,
                      &query, query.ticket);
              if (submit !=
                  xar::ck3_11906::MainThreadQuerySubmitResultV1::submitted) {
                std::string_view error =
                    "application-main battle-transition executor is unavailable";
                if (submit ==
                    xar::ck3_11906::MainThreadQuerySubmitResultV1::
                        paused_main_thread_not_observed) {
                  error = "paused application-main boundary is not ready";
                } else if (
                    submit ==
                    xar::ck3_11906::MainThreadQuerySubmitResultV1::
                        mailbox_busy) {
                  error =
                      "application-main battle-transition executor is busy";
                }
                connected = xar::bridge::WriteFrame(
                    pipe,
                    CommandResultFrame(request_id, step, false, error));
              } else {
                auto wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                    g_main_thread_query_mailbox_v1, query.ticket,
                    xar::ck3_11906::
                        kBattleTransitionV1QueuedWaitBudgetMilliseconds);
                while (wait ==
                       xar::ck3_11906::MainThreadQueryWaitResultV1::
                           timeout_executor_already_running) {
                  wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                      g_main_thread_query_mailbox_v1, query.ticket,
                      xar::ck3_11906::
                          kBattleTransitionV1ExecutingWaitSliceMilliseconds);
                }
                std::string response;
                bool completion_snapshot_stable = false;
                if (wait ==
                        xar::ck3_11906::MainThreadQueryWaitResultV1::
                            completed &&
                    query.completion ==
                        xar::ck3_11906::
                            BattleTransitionMailboxCompletionV1::completed) {
                  xar::game::Snapshot completion_snapshot{};
                  if (state_revision == expected_revision &&
                      previous_snapshot.has_value() &&
                      xar::game::ReadSnapshot(game, completion_snapshot) &&
                      completion_snapshot == current_snapshot &&
                      completion_snapshot == previous_snapshot.value()) {
                    completion_snapshot_stable = true;
                    response = BattleTransitionResultFrame(
                        request_id, step,
                        battle_transition_query_sequence + 1,
                        query.result);
                    if (!response.empty()) {
                      ++battle_transition_query_sequence;
                    }
                  }
                }
                if (response.empty()) {
                  const auto error = xar::ck3_11906::
                      BattleTransitionFailureMessageV1(
                          wait, query.completion,
                          completion_snapshot_stable);
                  response =
                      CommandResultFrame(request_id, step, false, error);
                }
                const auto reclaimed =
                    xar::ck3_11906::ReclaimMainThreadQueryV1(
                        g_main_thread_query_mailbox_v1, query.ticket);
                if (reclaimed !=
                    xar::ck3_11906::MainThreadQueryReclaimResultV1::
                        reclaimed) {
                  response = CommandResultFrame(
                      request_id, step, false,
                      "application-main battle-transition result was not reclaimable");
                }
                connected = xar::bridge::WriteFrame(pipe, response);
              }
            }
          }
        } else if (step.starts_with(
                       xar::ck3_11906::
                           kBattleControlSnapshotV1StepPrefix)) {
          xar::game::BattleControlRequest battle_request{};
          std::uint64_t expected_revision = 0;
          if (!xar::ck3_11906::ParseBattleControlSnapshotV1Step(
                  step, battle_request) ||
              !xar::ck3_11906::ParseBattleControlExpectedRevisionV1(
                  incoming.payload, expected_revision)) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "battle-control-snapshot request is malformed"));
          } else if (expected_revision != state_revision) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "battle-control expected revision is stale"));
          } else {
            xar::game::Snapshot current_snapshot{};
            if (!previous_snapshot.has_value() || state_revision == 0 ||
                !xar::game::ReadSnapshot(game, current_snapshot) ||
                current_snapshot != previous_snapshot.value() ||
                !current_snapshot.paused) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(
                            request_id, step, false,
                            "battle-control snapshot changed; retry after heartbeat"));
            } else {
              const auto subject = std::find_if(
                  current_snapshot.player_armies.begin(),
                  current_snapshot.player_armies.end(),
                  [&battle_request](const xar::game::ArmySnapshot &army) {
                    return army.army_id ==
                           battle_request.subject_public_cunit_id;
                  });
              if (subject == current_snapshot.player_armies.end() ||
                  !subject->controllable || !subject->in_combat ||
                  subject->retreating) {
                connected = xar::bridge::WriteFrame(
                    pipe, CommandResultFrame(
                              request_id, step, false,
                              "battle-control subject is outside the active controllable battle scope"));
              } else {
                xar::ck3_11906::BattleControlSnapshotMailboxContextV1
                    query{};
                query.mailbox = &g_main_thread_query_mailbox_v1;
                query.bindings = xar::ck3_11906::BindCurrentProcess(true);
                query.request = battle_request;
                query.expected_snapshot_revision = expected_revision;
                query.expected_snapshot = current_snapshot;
                const auto submit =
                    xar::ck3_11906::TrySubmitMainThreadQueryV1(
                        g_main_thread_query_mailbox_v1,
                        &xar::ck3_11906::
                            ExecuteBattleControlSnapshotMailboxQueryV1,
                        &query, query.ticket);
                if (submit != xar::ck3_11906::
                                  MainThreadQuerySubmitResultV1::submitted) {
                  std::string_view error =
                      "application-main battle-control executor is unavailable";
                  if (submit == xar::ck3_11906::
                                    MainThreadQuerySubmitResultV1::
                                        paused_main_thread_not_observed) {
                    error = "paused application-main boundary is not ready";
                  } else if (submit == xar::ck3_11906::
                                           MainThreadQuerySubmitResultV1::
                                               mailbox_busy) {
                    error =
                        "application-main battle-control executor is busy";
                  }
                  connected = xar::bridge::WriteFrame(
                      pipe,
                      CommandResultFrame(request_id, step, false, error));
                } else {
                  auto wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                      g_main_thread_query_mailbox_v1, query.ticket,
                      xar::ck3_11906::
                          kBattleControlSnapshotV1QueuedWaitBudgetMilliseconds);
                  while (wait == xar::ck3_11906::
                                     MainThreadQueryWaitResultV1::
                                         timeout_executor_already_running) {
                    wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                        g_main_thread_query_mailbox_v1, query.ticket,
                        xar::ck3_11906::
                            kBattleControlSnapshotV1ExecutingWaitSliceMilliseconds);
                  }

                  std::string response;
                  bool completion_snapshot_stable = false;
                  if (wait == xar::ck3_11906::
                                  MainThreadQueryWaitResultV1::completed &&
                      query.completion == xar::ck3_11906::
                                              BattleControlSnapshotMailboxCompletionV1::
                                                  available) {
                    xar::game::Snapshot completion_snapshot{};
                    if (state_revision == expected_revision &&
                        previous_snapshot.has_value() &&
                        xar::game::ReadSnapshot(game,
                                                completion_snapshot) &&
                        completion_snapshot == current_snapshot &&
                        completion_snapshot == previous_snapshot.value()) {
                      completion_snapshot_stable = true;
                      response = BattleControlSnapshotResultFrame(
                          request_id, step,
                          battle_control_snapshot_query_sequence + 1,
                          query.result);
                      if (!response.empty()) {
                        ++battle_control_snapshot_query_sequence;
                      }
                    }
                  }
                  if (response.empty()) {
                    const auto failure = xar::ck3_11906::
                        BattleControlSnapshotFailureMessageV1(
                            wait, query.completion, query.result.status,
                            completion_snapshot_stable);
                    std::string error(failure);
                    if (query.result.status == xar::game::
                                                   BattleControlSnapshotStatus::
                                                       state_changed &&
                        !query.result.diagnostic_reason.empty()) {
                      error += " (";
                      error += query.result.diagnostic_reason;
                      error += ")";
                    }
                    response =
                        CommandResultFrame(request_id, step, false, error);
                  }
                  const auto reclaimed =
                      xar::ck3_11906::ReclaimMainThreadQueryV1(
                          g_main_thread_query_mailbox_v1, query.ticket);
                  if (reclaimed != xar::ck3_11906::
                                       MainThreadQueryReclaimResultV1::
                                           reclaimed) {
                    response = CommandResultFrame(
                        request_id, step, false,
                        "application-main battle-control result was not reclaimable");
                  }
                  connected = xar::bridge::WriteFrame(pipe, response);
                }
              }
            }
          }
        } else if (step.starts_with(
                       xar::ck3_11906::kActualContactScopeV1StepPrefix)) {
          xar::game::ActualContactScopeRequest contact_request{};
          std::uint64_t expected_revision = 0;
          if (!xar::ck3_11906::ParseActualContactScopeV1Step(
                  step, contact_request) ||
              !xar::ck3_11906::ParseActualContactExpectedRevisionV1(
                  incoming.payload, expected_revision)) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "actual-contact-scope request is malformed"));
          } else if (expected_revision != state_revision) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "actual-contact expected revision is stale"));
          } else {
            xar::game::Snapshot current_snapshot{};
            const auto subject = [&]()
                -> const xar::game::ArmySnapshot * {
              if (!previous_snapshot.has_value()) {
                return nullptr;
              }
              for (const auto &army : previous_snapshot->player_armies) {
                if (army.army_id == contact_request.subject_army_id) {
                  return &army;
                }
              }
              return nullptr;
            }();
            if (!previous_snapshot.has_value() || state_revision == 0 ||
                !xar::game::ReadSnapshot(game, current_snapshot) ||
                current_snapshot != previous_snapshot.value() ||
                subject == nullptr || !subject->controllable ||
                !subject->has_current_province ||
                subject->current_province_id !=
                    contact_request.target_province_id) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(
                            request_id, step, false,
                            "actual-contact snapshot or subject scope changed"));
            } else {
              xar::ck3_11906::ActualContactScopeMailboxContextV1 query{};
              query.mailbox = &g_main_thread_query_mailbox_v1;
              query.bindings = xar::ck3_11906::BindCurrentProcess(true);
              query.request = contact_request;
              const auto submit =
                  xar::ck3_11906::TrySubmitMainThreadQueryV1(
                      g_main_thread_query_mailbox_v1,
                      &xar::ck3_11906::
                          ExecuteActualContactScopeMailboxQueryV1,
                      &query, query.ticket);
              if (submit != xar::ck3_11906::
                                MainThreadQuerySubmitResultV1::submitted) {
                std::string_view error =
                    "application-main actual-contact executor is unavailable";
                if (submit == xar::ck3_11906::
                                  MainThreadQuerySubmitResultV1::
                                      paused_main_thread_not_observed) {
                  error = "paused application-main boundary is not ready";
                } else if (submit == xar::ck3_11906::
                                         MainThreadQuerySubmitResultV1::
                                             mailbox_busy) {
                  error = "application-main actual-contact executor is busy";
                }
                connected = xar::bridge::WriteFrame(
                    pipe, CommandResultFrame(request_id, step, false, error));
              } else {
                auto wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                    g_main_thread_query_mailbox_v1, query.ticket,
                    xar::ck3_11906::
                        kActualContactScopeV1QueuedWaitBudgetMilliseconds);
                while (wait == xar::ck3_11906::
                                   MainThreadQueryWaitResultV1::
                                       timeout_executor_already_running) {
                  wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                      g_main_thread_query_mailbox_v1, query.ticket,
                      xar::ck3_11906::
                          kActualContactScopeV1ExecutingWaitSliceMilliseconds);
                }
                std::string response;
                bool completion_snapshot_stable = false;
                if (wait == xar::ck3_11906::
                                MainThreadQueryWaitResultV1::completed &&
                    query.completion == xar::ck3_11906::
                                            ActualContactScopeMailboxCompletionV1::
                                                available) {
                  xar::game::Snapshot completion_snapshot{};
                  if (state_revision == expected_revision &&
                      previous_snapshot.has_value() &&
                      xar::game::ReadSnapshot(game, completion_snapshot) &&
                      completion_snapshot == current_snapshot &&
                      completion_snapshot == previous_snapshot.value()) {
                    completion_snapshot_stable = true;
                    query.result.snapshot_revision = state_revision;
                    ++actual_contact_scope_query_sequence;
                    response = ActualContactScopeResultFrame(
                        request_id, step,
                        actual_contact_scope_query_sequence, query.result);
                  }
                }
                if (response.empty()) {
                  const auto error = xar::ck3_11906::
                      ActualContactScopeFailureMessageV1(
                          wait, query.completion, query.result.status,
                          completion_snapshot_stable);
                  response =
                      CommandResultFrame(request_id, step, false, error);
                }
                const auto reclaimed =
                    xar::ck3_11906::ReclaimMainThreadQueryV1(
                        g_main_thread_query_mailbox_v1, query.ticket);
                if (reclaimed != xar::ck3_11906::
                                     MainThreadQueryReclaimResultV1::
                                         reclaimed) {
                  response = CommandResultFrame(
                      request_id, step, false,
                      "application-main actual-contact result was not reclaimable");
                }
                connected = xar::bridge::WriteFrame(pipe, response);
              }
            }
          }
        } else if (step.starts_with(
                       xar::ck3_11906::kRouteContactHorizonV1StepPrefix)) {
          xar::game::RouteContactHorizonRequest route_request{};
          std::uint64_t expected_revision = 0;
          if (!xar::ck3_11906::ParseRouteContactHorizonV1Step(
                  step, route_request) ||
              !xar::ck3_11906::ParseRouteContactExpectedRevisionV1(
                  incoming.payload, expected_revision)) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "route-contact-horizon request is malformed"));
          } else if (expected_revision != state_revision) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "route-contact expected revision is stale"));
          } else {
            xar::game::Snapshot current_snapshot{};
            if (!previous_snapshot.has_value() || state_revision == 0 ||
                !xar::game::ReadSnapshot(game, current_snapshot) ||
                current_snapshot != previous_snapshot.value()) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(
                            request_id, step, false,
                            "route-contact snapshot changed; retry after heartbeat"));
            } else if (!RouteHostileScopeMatchesSnapshot(
                           current_snapshot, route_request)) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(
                            request_id, step, false,
                            "route-contact hostile scope is incomplete or stale"));
            } else {
              xar::ck3_11906::RouteContactHorizonMailboxContextV1 query{};
              query.mailbox = &g_main_thread_query_mailbox_v1;
              query.bindings = xar::ck3_11906::BindCurrentProcess(true);
              query.request = route_request;
              const auto submit =
                  xar::ck3_11906::TrySubmitMainThreadQueryV1(
                      g_main_thread_query_mailbox_v1,
                      &xar::ck3_11906::
                          ExecuteRouteContactHorizonMailboxQueryV1,
                      &query, query.ticket);
              if (submit != xar::ck3_11906::
                                MainThreadQuerySubmitResultV1::submitted) {
                std::string_view error =
                    "application-main route-contact executor is unavailable";
                if (submit == xar::ck3_11906::
                                  MainThreadQuerySubmitResultV1::
                                      paused_main_thread_not_observed) {
                  error = "paused application-main boundary is not ready";
                } else if (submit == xar::ck3_11906::
                                         MainThreadQuerySubmitResultV1::
                                             mailbox_busy) {
                  error = "application-main route-contact executor is busy";
                }
                connected = xar::bridge::WriteFrame(
                    pipe, CommandResultFrame(request_id, step, false, error));
              } else {
                auto wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                    g_main_thread_query_mailbox_v1, query.ticket,
                    xar::ck3_11906::
                        kRouteContactHorizonV1QueuedWaitBudgetMilliseconds);
                while (wait == xar::ck3_11906::
                                   MainThreadQueryWaitResultV1::
                                       timeout_executor_already_running) {
                  // As in the war-entry worker, the application-main executor
                  // owns this stack context once it starts.  Keep it alive
                  // until terminal rather than returning a dangling request.
                  wait = xar::ck3_11906::WaitForMainThreadQueryV1(
                      g_main_thread_query_mailbox_v1, query.ticket,
                      xar::ck3_11906::
                          kRouteContactHorizonV1ExecutingWaitSliceMilliseconds);
                }

                std::string response;
                bool completion_snapshot_stable = false;
                if (wait == xar::ck3_11906::
                                MainThreadQueryWaitResultV1::completed &&
                    query.completion == xar::ck3_11906::
                                            RouteContactHorizonMailboxCompletionV1::
                                                available) {
                  xar::game::Snapshot completion_snapshot{};
                  if (state_revision == expected_revision &&
                      previous_snapshot.has_value() &&
                      xar::game::ReadSnapshot(game, completion_snapshot) &&
                      completion_snapshot == current_snapshot &&
                      completion_snapshot == previous_snapshot.value()) {
                    completion_snapshot_stable = true;
                    query.result.snapshot_revision = state_revision;
                    ++route_contact_horizon_query_sequence;
                    response = RouteContactHorizonResultFrame(
                        request_id, step,
                        route_contact_horizon_query_sequence, query.result);
                  }
                }
                if (response.empty()) {
                  const auto error = xar::ck3_11906::
                      RouteContactHorizonFailureMessageV1(
                          wait, query.completion, query.result.status,
                          completion_snapshot_stable);
                  response =
                      CommandResultFrame(request_id, step, false, error);
                }
                const auto reclaimed =
                    xar::ck3_11906::ReclaimMainThreadQueryV1(
                        g_main_thread_query_mailbox_v1, query.ticket);
                if (reclaimed != xar::ck3_11906::
                                     MainThreadQueryReclaimResultV1::
                                         reclaimed) {
                  response = CommandResultFrame(
                      request_id, step, false,
                      "application-main route-contact result was not reclaimable");
                }
                connected = xar::bridge::WriteFrame(pipe, response);
              }
            }
          }
        } else if (step.starts_with("preview-move-army-")) {
          const auto ids = PreviewMoveArmyStep(step);
          if (!ids.has_value()) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "invalid preview-move-army-<army_id>-to-<province_id> step"));
          } else {
            const auto preview = xar::game::PreviewMoveArmy(
                game, ids->army_id, ids->province_id);
            if (preview.status ==
                xar::game::PreviewMoveArmyStatus::available) {
              connected = xar::bridge::WriteFrame(
                  pipe, RoutePreviewResultFrame(request_id, step, preview));
            } else {
              std::string_view error =
                  "CK3 move-army route preview is unavailable";
              if (preview.status ==
                  xar::game::PreviewMoveArmyStatus::requires_paused) {
                error = "CK3 route preview requires a paused map";
              } else if (preview.status ==
                  xar::game::PreviewMoveArmyStatus::army_not_found) {
                error = "CK3 army was not found";
              } else if (preview.status ==
                         xar::game::PreviewMoveArmyStatus::
                             army_not_controllable) {
                error = "CK3 army is not player-controllable";
              } else if (preview.status ==
                         xar::game::PreviewMoveArmyStatus::
                             province_not_found) {
                error = "CK3 destination province was not found";
              } else if (preview.status ==
                         xar::game::PreviewMoveArmyStatus::
                             move_mode_unavailable) {
                error = "CK3 army has no move mode for the destination";
              } else if (preview.status ==
                         xar::game::PreviewMoveArmyStatus::
                             character_state_rejected) {
                error = "CK3 played character state rejects army movement";
              } else if (preview.status ==
                         xar::game::PreviewMoveArmyStatus::
                             army_state_rejected) {
                error = "CK3 army state rejects movement";
              } else if (preview.status ==
                         xar::game::PreviewMoveArmyStatus::
                             validation_failed) {
                error = "CK3 move-army validation failed";
              } else if (preview.status ==
                         xar::game::PreviewMoveArmyStatus::
                             origin_unavailable) {
                error = "CK3 move origin is unavailable";
              } else if (preview.status ==
                         xar::game::PreviewMoveArmyStatus::
                             route_unavailable) {
                error = "CK3 could not build a complete move route";
              }
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, false, error));
            }
          }
        } else if (step.starts_with("move-army-")) {
          const auto ids = MoveArmyStep(step);
          if (!ids.has_value()) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "invalid move-army-<army_id>-to-<province_id> step"));
          } else {
            const auto result = xar::game::SubmitMoveArmy(
                game, ids->army_id, ids->province_id);
            if (result == xar::game::MoveArmyResult::submitted) {
              connected = xar::bridge::WriteFrame(
                  pipe,
                  CommandResultFrame(request_id, step, true, "submitted"));
            } else {
              std::string_view error = "CK3 move-army state is unavailable";
              if (result == xar::game::MoveArmyResult::army_not_found) {
                error = "CK3 army was not found";
              } else if (result == xar::game::MoveArmyResult::
                                       army_not_controllable) {
                error = "CK3 army is not player-controllable";
              } else if (result ==
                         xar::game::MoveArmyResult::province_not_found) {
                error = "CK3 destination province was not found";
              } else if (result ==
                         xar::game::MoveArmyResult::move_mode_unavailable) {
                error = "CK3 army has no move mode for the destination";
              } else if (result == xar::game::MoveArmyResult::
                                       character_state_rejected) {
                error = "CK3 played character state rejects army movement";
              } else if (result ==
                         xar::game::MoveArmyResult::army_state_rejected) {
                error = "CK3 army state rejects movement";
              } else if (result ==
                         xar::game::MoveArmyResult::validation_failed) {
                error = "CK3 move-army command validation failed";
              }
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, false, error));
            }
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision, checkpoint_submission,
                                        published_checkpoint_sequence);
          }
        } else if (step.starts_with("disband-army-")) {
          const auto army_id = DisbandArmyStep(step);
          if (!army_id.has_value()) {
            connected = xar::bridge::WriteFrame(
                pipe,
                CommandResultFrame(request_id, step, false,
                                   "invalid disband-army-<army_id> step"));
          } else {
            const auto result =
                xar::game::SubmitDisbandArmy(game, army_id.value());
            if (result == xar::game::DisbandArmyResult::submitted) {
              connected = xar::bridge::WriteFrame(
                  pipe,
                  CommandResultFrame(request_id, step, true, "submitted"));
            } else {
              std::string_view error = "CK3 disband-army state is unavailable";
              if (result == xar::game::DisbandArmyResult::army_not_found) {
                error = "CK3 army was not found";
              } else if (result == xar::game::DisbandArmyResult::
                                       army_not_controllable) {
                error = "CK3 army is not player-controllable";
              }
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, false, error));
            }
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision, checkpoint_submission,
                                        published_checkpoint_sequence);
          }
        } else if (step.starts_with("split-army-half-")) {
          const auto army_id = SplitArmyHalfStep(step);
          if (!army_id.has_value()) {
            connected = xar::bridge::WriteFrame(
                pipe,
                CommandResultFrame(request_id, step, false,
                                   "invalid split-army-half-<army_id> step"));
          } else {
            const auto result =
                xar::game::SubmitSplitArmyHalf(game, army_id.value());
            if (result ==
                xar::game::SplitArmyHalfResult::split_submitted) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, true,
                                           "split_submitted"));
            } else {
              std::string_view error =
                  "CK3 split-army-half state is unavailable";
              if (result == xar::game::SplitArmyHalfResult::
                                no_played_character) {
                error = "no living played CK3 character";
              } else if (result ==
                         xar::game::SplitArmyHalfResult::army_not_found) {
                error = "CK3 army was not found";
              } else if (result ==
                         xar::game::SplitArmyHalfResult::
                             army_not_controllable) {
                error = "CK3 army is not player-controllable";
              } else if (result ==
                         xar::game::SplitArmyHalfResult::
                             validator_rejected) {
                error = "CK3 rejected split-army-half validation";
              } else if (result == xar::game::SplitArmyHalfResult::
                                       submission_failed) {
                error = "CK3 rejected split-army-half queue submission";
              }
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, false, error));
            }
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision, checkpoint_submission,
                                        published_checkpoint_sequence);
          }
        } else if (step.starts_with("merge-armies-")) {
          const auto army_ids = MergeArmiesStep(step);
          if (!army_ids.has_value()) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "invalid merge-armies-<destination_army_id>-with-"
                          "<source_army_id> step"));
          } else {
            const auto result = xar::game::SubmitMergeArmies(
                game, army_ids->destination_army_id,
                army_ids->source_army_id);
            if (result == xar::game::MergeArmiesResult::merge_submitted) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, true,
                                           "merge_submitted"));
            } else {
              std::string_view error =
                  "CK3 merge-armies state is unavailable";
              if (result ==
                  xar::game::MergeArmiesResult::no_played_character) {
                error = "no living played CK3 character";
              } else if (result == xar::game::MergeArmiesResult::
                                       destination_not_found) {
                error = "CK3 destination army was not found";
              } else if (result ==
                         xar::game::MergeArmiesResult::source_not_found) {
                error = "CK3 source army was not found";
              } else if (result == xar::game::MergeArmiesResult::
                                       destination_not_controllable) {
                error = "CK3 destination army is not player-controllable";
              } else if (result == xar::game::MergeArmiesResult::
                                       source_not_controllable) {
                error = "CK3 source army is not player-controllable";
              } else if (result ==
                         xar::game::MergeArmiesResult::same_army) {
                error = "CK3 merge-armies IDs must be distinct";
              } else if (result == xar::game::MergeArmiesResult::
                                       validator_rejected) {
                error = "CK3 rejected merge-armies validation";
              } else if (result == xar::game::MergeArmiesResult::
                                       submission_failed) {
                error = "CK3 rejected merge-armies queue submission";
              }
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, false, error));
            }
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision, checkpoint_submission,
                                        published_checkpoint_sequence);
          }
        } else if (step.starts_with("start-assault-")) {
          const auto siege_id = AssaultStep(step, "start-assault-");
          if (!siege_id.has_value()) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "invalid start-assault-<siege_id> step"));
          } else {
            const auto result =
                xar::game::SubmitStartAssault(game, siege_id.value());
            if (result == xar::game::StartAssaultResult::start_submitted) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, true,
                                           "start_submitted"));
            } else {
              std::string_view error =
                  "CK3 start-assault state is unavailable";
              if (result == xar::game::StartAssaultResult::
                                no_played_character) {
                error = "no living played CK3 character";
              } else if (result ==
                         xar::game::StartAssaultResult::siege_not_found) {
                error = "CK3 siege was not found";
              } else if (result == xar::game::StartAssaultResult::
                                       assault_already_active) {
                error = "CK3 assault is already active";
              } else if (result == xar::game::StartAssaultResult::
                                       validator_rejected) {
                error = "CK3 rejected start-assault validation";
              } else if (result == xar::game::StartAssaultResult::
                                       submission_failed) {
                error = "CK3 rejected start-assault queue submission";
              }
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, false, error));
            }
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision, checkpoint_submission,
                                        published_checkpoint_sequence);
          }
        } else if (step.starts_with("stop-assault-")) {
          const auto siege_id = AssaultStep(step, "stop-assault-");
          if (!siege_id.has_value()) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "invalid stop-assault-<siege_id> step"));
          } else {
            const auto result =
                xar::game::SubmitStopAssault(game, siege_id.value());
            if (result == xar::game::StopAssaultResult::stop_submitted) {
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, true,
                                           "stop_submitted"));
            } else {
              std::string_view error =
                  "CK3 stop-assault state is unavailable";
              if (result == xar::game::StopAssaultResult::
                                no_played_character) {
                error = "no living played CK3 character";
              } else if (result ==
                         xar::game::StopAssaultResult::siege_not_found) {
                error = "CK3 siege was not found";
              } else if (result == xar::game::StopAssaultResult::
                                       assault_not_active) {
                error = "CK3 assault is not active";
              } else if (result == xar::game::StopAssaultResult::
                                       validator_rejected) {
                error = "CK3 rejected stop-assault validation";
              } else if (result == xar::game::StopAssaultResult::
                                       submission_failed) {
                error = "CK3 rejected stop-assault queue submission";
              }
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, false, error));
            }
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision, checkpoint_submission,
                                        published_checkpoint_sequence);
          }
        } else if (const auto option_index = EventOptionStep(step);
                   option_index.has_value()) {
          const auto result = xar::game::SubmitSelectEventOption(
              game, option_index.value());
          if (result == xar::game::SelectEventOptionResult::submitted) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, true, "submitted"));
          } else {
            std::string_view error = "CK3 event state is unavailable";
            if (result ==
                xar::game::SelectEventOptionResult::no_active_event) {
              error = "no active CK3 event";
            } else if (result == xar::game::SelectEventOptionResult::
                                     option_out_of_range) {
              error = "event option index is out of range";
            }
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, false, error));
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision, checkpoint_submission,
                                        published_checkpoint_sequence);
          }
        } else {
          const std::int32_t requested_speed = FixedSpeedStep(step);
          if (requested_speed >= 1 &&
              xar::game::SubmitSetSpeed(game, requested_speed)) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, true, "submitted"));
            if (connected) {
              connected = PublishSnapshot(pipe, game, previous_snapshot,
                                          state_revision, checkpoint_submission,
                                          published_checkpoint_sequence);
            }
          } else {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, false,
                                         "unsupported native gameplay step"));
          }
        }
        }
      }
    }
    WaitForSingleObject(g_stop_event, 10);
  }
}

DWORD WINAPI WorkerMain(void *) noexcept {
  const auto game = xar::game::SelectCurrentProcessAdapter();
  if (game == nullptr) {
    return 1;
  }
  WarEntryApplicationMainMailboxWorkerLifetime mailbox_lifetime(*game);
  WorkerState state{};
  while (WaitForSingleObject(g_stop_event, 0) == WAIT_TIMEOUT) {
    HANDLE pipe = ConnectToHost();
    if (pipe == INVALID_HANDLE_VALUE) {
      return WaitForSingleObject(g_stop_event, 0) == WAIT_OBJECT_0 ? 0 : 1;
    }
    RunConnectedSession(pipe, *game, state, mailbox_lifetime);
    CloseHandle(pipe);
    if (WaitForSingleObject(g_stop_event, 0) == WAIT_TIMEOUT) {
      WaitForSingleObject(g_stop_event, 50);
    }
  }
  return 0;
}

BOOL StartWithPipeName(const wchar_t *pipe_name, DWORD length) noexcept {
  if (!IsPipeName(pipe_name, length)) {
    return FALSE;
  }
  long expected_lifecycle = 0;
  if (!g_lifecycle.compare_exchange_strong(expected_lifecycle, 1)) {
    return expected_lifecycle == 1 ? TRUE : FALSE;
  }
  for (DWORD index = 0; index <= length; ++index) {
    g_pipe_name[index] = pipe_name[index];
  }

  g_stop_event = CreateEventW(nullptr, TRUE, FALSE, nullptr);
  if (g_stop_event == nullptr) {
    g_lifecycle.store(0);
    return FALSE;
  }
  g_worker_thread = CreateThread(nullptr, 0, WorkerMain, nullptr, 0, nullptr);
  if (g_worker_thread == nullptr) {
    CloseHandle(g_stop_event);
    g_stop_event = nullptr;
    g_lifecycle.store(0);
    return FALSE;
  }
  return TRUE;
}

BOOL StartFromEnvironment() noexcept {
  wchar_t pipe_name[kPipeNameCapacity]{};
  const DWORD length = GetEnvironmentVariableW(
      kPipeEnvironment, pipe_name, static_cast<DWORD>(kPipeNameCapacity));
  return StartWithPipeName(pipe_name, length);
}

void SignalStop() noexcept {
  if (g_stop_event != nullptr) {
    SetEvent(g_stop_event);
  }
}

} // namespace

extern "C" __declspec(dllexport) const char *WINAPI
XarCk3BridgeIdentity() noexcept {
  static const std::string identity = IdentityFrame();
  return identity.c_str();
}

// The injector calls this only while a newly-created process's primary thread
// is still suspended. Unsupported executables remain a successful no-op so the
// offline bridge target and diagnostic attach surface keep working. Production
// returns before installing any containment guard; an explicitly instrumented
// build may install only the no-suppression particle2 stage recorder.
extern "C" __declspec(dllexport) DWORD WINAPI
XarCk3BridgePrepareStartup(LPVOID) noexcept {
  auto game = xar::game::SelectCurrentProcessAdapter();
  if (game == nullptr) {
    return FALSE;
  }
  if (!game->enabled()) {
    return TRUE;
  }
  const auto exact_bindings = xar::ck3_11906::BindCurrentProcess(true);
  xar::ck3_11906::TacticalDailySentinelInstallEnvironmentV1
      tactical_sentinel_environment{};
  tactical_sentinel_environment.exact_build_admitted = true;
  tactical_sentinel_environment.primary_thread_suspended_proven = true;
  tactical_sentinel_environment.module_base =
      reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  tactical_sentinel_environment.bindings = exact_bindings;
  if (!xar::ck3_11906::InstallTacticalDailySentinelV1(
          g_tactical_daily_sentinel_v1,
          tactical_sentinel_environment)) {
    return FALSE;
  }
  xar::ck3_11906::BattleTerminalJournalInstallEnvironmentV1
      battle_terminal_environment{};
  battle_terminal_environment.exact_build_admitted = true;
  battle_terminal_environment.primary_thread_suspended_proven = true;
  battle_terminal_environment.module_base =
      reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  battle_terminal_environment.bindings = exact_bindings;
  if (!xar::ck3_11906::InstallBattleTerminalJournalV1(
          g_battle_terminal_journal_v1,
          battle_terminal_environment)) {
    return FALSE;
  }
  if (kStartupParticle2StageRecorderEnabledV1) {
    xar::bridge::StartupParticle2StageRecorderV1Environment environment{};
    environment.exact_build_admitted = true;
    environment.primary_thread_suspended_proven = true;
    environment.module_base =
        reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    return xar::bridge::InstallStartupParticle2StageRecorderV1(
               g_startup_particle2_stage_recorder_v1, environment)
        ? TRUE
        : FALSE;
  }
  if (!kStartupFailureContainmentEnabledV1) {
    return TRUE;
  }
  xar::bridge::StartupParticle2NullGuardV1Environment environment{};
  environment.exact_build_admitted = true;
  environment.primary_thread_suspended_proven = true;
  environment.module_base =
      reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  if (!xar::bridge::InstallStartupParticle2NullGuardV1(
          g_startup_particle2_null_guard_v1, environment)) {
    return FALSE;
  }

  xar::bridge::StartupParticle2ConsumerGuardV1Environment
      consumer_environment{};
  consumer_environment.exact_build_admitted = true;
  consumer_environment.primary_thread_suspended_proven = true;
  consumer_environment.module_base = environment.module_base;
  if (!xar::bridge::InstallStartupParticle2ConsumerGuardV1(
          g_startup_particle2_consumer_null_guard_v1,
          consumer_environment)) {
    // PrepareStartup runs before the primary thread is resumed, so restoring
    // the first patch here is quiescent.  Any unproven rollback still returns
    // failure and the managed launcher terminates the suspended target.
    (void)xar::bridge::UninstallStartupParticle2NullGuardV1(
        g_startup_particle2_null_guard_v1);
    return FALSE;
  }

  xar::bridge::StartupDx11RenderContextDrawGuardV1Environment
      dx11_draw_environment{};
  dx11_draw_environment.exact_build_admitted = true;
  dx11_draw_environment.primary_thread_suspended_proven = true;
  dx11_draw_environment.module_base = environment.module_base;
  if (!xar::bridge::InstallStartupDx11RenderContextDrawGuardV1(
          g_startup_dx11_render_context_draw_guard_v1,
          dx11_draw_environment)) {
    // All three patches are installed before the primary thread is resumed.
    // Failure therefore unwinds the already-installed guards in reverse order;
    // the managed launcher terminates the suspended target if any rollback is
    // unproven.
    const bool consumer_restored =
        xar::bridge::UninstallStartupParticle2ConsumerGuardV1(
            g_startup_particle2_consumer_null_guard_v1);
    const bool producer_restored =
        xar::bridge::UninstallStartupParticle2NullGuardV1(
            g_startup_particle2_null_guard_v1);
    (void)consumer_restored;
    (void)producer_restored;
    return FALSE;
  }

  xar::bridge::StartupLocalizeCurrentRootGuardV1Environment
      localize_environment{};
  localize_environment.exact_build_admitted = true;
  localize_environment.primary_thread_suspended_proven = true;
  localize_environment.module_base = environment.module_base;
  if (!xar::bridge::InstallStartupLocalizeCurrentRootGuardV1(
          g_startup_localize_current_root_guard_v1,
          localize_environment)) {
    // The primary thread is still suspended, so the already-installed guards
    // can be unwound in strict reverse order. Returning FALSE makes the managed
    // launcher terminate the suspended target if any restore is unproven.
    const bool draw_restored =
        xar::bridge::UninstallStartupDx11RenderContextDrawGuardV1(
            g_startup_dx11_render_context_draw_guard_v1);
    const bool consumer_restored =
        xar::bridge::UninstallStartupParticle2ConsumerGuardV1(
            g_startup_particle2_consumer_null_guard_v1);
    const bool producer_restored =
        xar::bridge::UninstallStartupParticle2NullGuardV1(
            g_startup_particle2_null_guard_v1);
    (void)draw_restored;
    (void)consumer_restored;
    (void)producer_restored;
    return FALSE;
  }
  return TRUE;
}

extern "C" __declspec(dllexport) BOOL WINAPI XarCk3BridgeStart() noexcept {
  return StartFromEnvironment();
}

// The signature intentionally matches LPTHREAD_START_ROUTINE on x64 Windows.
// This lets the injector start an already-running process that did not inherit
// XAR_CK3_BRIDGE_PIPE, without modifying that process's environment block.
extern "C" __declspec(dllexport) BOOL WINAPI
XarCk3BridgeStartWithPipe(const wchar_t *pipe_name) noexcept {
  if (pipe_name == nullptr) {
    return FALSE;
  }
  DWORD length = 0;
  while (length < kPipeNameCapacity && pipe_name[length] != L'\0') {
    ++length;
  }
  return StartWithPipeName(pipe_name, length);
}

extern "C" __declspec(dllexport) void WINAPI XarCk3BridgeStop() noexcept {
  SignalStop();
  if (g_lifecycle.load() == 0) {
    return;
  }
  g_lifecycle.store(2);
  if (g_worker_thread != nullptr) {
    const DWORD worker_wait = WaitForSingleObject(g_worker_thread, 5000);
    if (worker_wait != WAIT_OBJECT_0) {
      // WorkerMain owns mailbox uninstall.  Retain both handles and the
      // stopping lifecycle so a later Stop call can finish cleanup; never
      // reset synchronization state after an uninstall timeout.
      return;
    }
    CloseHandle(g_worker_thread);
    g_worker_thread = nullptr;
  }
  if (g_stop_event != nullptr) {
    CloseHandle(g_stop_event);
    g_stop_event = nullptr;
  }
  g_pipe_name[0] = L'\0';
  g_lifecycle.store(0);
}

BOOL WINAPI DllMain(HINSTANCE instance, DWORD reason, LPVOID) {
  if (reason == DLL_PROCESS_ATTACH) {
    DisableThreadLibraryCalls(instance);
    wchar_t pipe_name[kPipeNameCapacity]{};
    const DWORD length = GetEnvironmentVariableW(
        kPipeEnvironment, pipe_name, static_cast<DWORD>(kPipeNameCapacity));
    if (IsPipeName(pipe_name, length)) {
      StartFromEnvironment();
    }
  } else if (reason == DLL_PROCESS_DETACH) {
    // V1 is process-lifetime pinned and does not support remote FreeLibrary.
    // At actual process teardown the loader lock permits signal-only cleanup;
    // waiting or changing the IAT here would deadlock or race teardown.
    xar::ck3_11906::SignalMainThreadQueryMailboxProcessDetachV1(
        g_main_thread_query_mailbox_v1);
    SignalStop();
  }
  return TRUE;
}
