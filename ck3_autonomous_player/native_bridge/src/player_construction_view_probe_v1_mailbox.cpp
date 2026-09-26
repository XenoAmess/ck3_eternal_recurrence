#include "player_construction_view_probe_v1_mailbox.hpp"

#include "player_construction_view_probe_v1_process.hpp"
#include "player_world_building_definition_source_v1_process.hpp"

#include <windows.h>

#include <atomic>
#include <cstring>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

using ProbeFailure =
    xar::ck3::shared::PlayerConstructionViewProbeFailureV1;
using ProbeResult = xar::ck3::shared::PlayerConstructionViewProbeResultV1;
using ProbeStatus = xar::ck3::shared::PlayerConstructionViewProbeStatusV1;
using ModelFailure = PlayerHeldConstructionModelFailureV1;
using ModelStatus = PlayerHeldConstructionModelStatusV1;
using WorldFailure = PlayerWorldBuildingFailureV1;

struct ModelAccessProxyV1 final {
  const PlayerConstructionViewProbeMailboxContextV1* query = nullptr;
  const MainThreadExecutionStampV1* stamp = nullptr;
};

bool IsExecutingExactSlot(
    const PlayerConstructionViewProbeMailboxContextV1& query,
    const MainThreadExecutionStampV1& stamp) noexcept {
  if (query.mailbox == nullptr || query.ticket.sequence == 0U ||
      query.module_base == 0U || stamp.pump_epoch == 0U ||
      stamp.thread_id == 0U || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0U ||
      stamp.tls_initialized != 1 || stamp.tls_context == 0U ||
      stamp.tls_main_thread_marker != 1 || stamp.jomini_state == 0U ||
      stamp.game_state == 0U || GetCurrentThreadId() != stamp.thread_id) {
    return false;
  }
  const auto& mailbox = *query.mailbox;
  return mailbox.state.load(std::memory_order_acquire) ==
             MainThreadQueryMailboxStateV1::executing &&
         !mailbox.stop_requested.load(std::memory_order_acquire) &&
         mailbox.failure_flags.load(std::memory_order_acquire) == 0U &&
         mailbox.published_sequence.load(std::memory_order_acquire) ==
             query.ticket.sequence &&
         mailbox.owner_thread_id.load(std::memory_order_acquire) ==
             stamp.thread_id &&
         mailbox.paused_owner_verified_pump_epochs.load(
             std::memory_order_acquire) >=
             kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs &&
         mailbox.executor == &ExecutePlayerConstructionViewProbeMailboxV1 &&
         mailbox.executor_context == &query;
}

bool CaptureSameSnapshot(
    const PlayerConstructionViewProbeMailboxContextV1& query,
    const MainThreadExecutionStampV1& stamp) noexcept {
  game::Snapshot current{};
  return ReadSnapshot(query.bindings, current) &&
         current == query.expected_snapshot && current.map_ready &&
         current.paused && current.has_played_character &&
         current.played_character_alive &&
         current.date_raw == stamp.date_raw;
}

bool ModelIsMainThread(void* opaque) noexcept {
  const auto* proxy = static_cast<const ModelAccessProxyV1*>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         IsExecutingExactSlot(*proxy->query, *proxy->stamp);
}

bool ModelCaptureFrame(void* opaque,
                       game::CampaignRootFrameV1& output) noexcept {
  const auto* proxy = static_cast<const ModelAccessProxyV1*>(opaque);
  if (proxy == nullptr || proxy->query == nullptr ||
      proxy->stamp == nullptr ||
      !IsExecutingExactSlot(*proxy->query, *proxy->stamp) ||
      !CaptureSameSnapshot(*proxy->query, *proxy->stamp)) {
    return false;
  }
  const auto& snapshot = proxy->query->expected_snapshot;
  output.snapshot_revision = proxy->query->expected_revision;
  output.date_raw = snapshot.date_raw;
  output.paused = snapshot.paused;
  output.map_ready = snapshot.map_ready;
  output.has_played_character = snapshot.has_played_character;
  output.played_character_alive = snapshot.played_character_alive;
  output.played_character_id = snapshot.played_character_id;
  return true;
}

bool ModelReadMemory(void* opaque, const void* address, void* output,
                     std::size_t size) noexcept {
  const auto* proxy = static_cast<const ModelAccessProxyV1*>(opaque);
  if (proxy == nullptr || proxy->query == nullptr ||
      proxy->stamp == nullptr || address == nullptr ||
      output == nullptr || size == 0 ||
      !IsExecutingExactSlot(*proxy->query, *proxy->stamp)) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
    std::memcpy(output, address, size);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  std::memcpy(output, address, size);
  return true;
#endif
}

bool ActiveViewUsesModelSource(
    const xar::ck3::shared::PlayerConstructionViewProbeSourceV1& source,
    std::uintptr_t module) noexcept {
  if (source.resolve_owner == nullptr || source.read_memory == nullptr) {
    return false;
  }
  xar::ck3::shared::PlayerConstructionViewResolvedOwnerV1 owner{};
  std::uintptr_t view = 0;
  std::uintptr_t view_model = 0;
  std::uintptr_t singleton = 0;
  return source.resolve_owner(source.owner_context, module, owner) &&
         owner.exact_idler_rtti_cast && owner.handler != 0 &&
         source.read_memory(source.read_context, owner.handler + 0xD0,
                            &view, sizeof(view)) && view != 0 &&
         source.read_memory(source.read_context, view + 0x108,
                            &view_model, sizeof(view_model)) &&
         source.read_memory(source.read_context, module + 0x57BFBA8,
                            &singleton, sizeof(singleton)) &&
         singleton != 0 && view_model == singleton;
}

std::string_view ModelStatusKey(ModelStatus status) noexcept {
  return status == ModelStatus::sources_available ? "sources_available"
                                                 : "unavailable";
}

std::string_view ModelFailureKey(ModelFailure failure) noexcept {
  switch (failure) {
    case ModelFailure::none: return "none";
    case ModelFailure::exact_build: return "exact_build";
    case ModelFailure::application_main: return "application_main";
    case ModelFailure::paused_frame: return "paused_frame";
    case ModelFailure::player_identity: return "player_identity";
    case ModelFailure::held_title_source: return "held_title_source";
    case ModelFailure::holding_province_identity:
      return "holding_province_identity";
    case ModelFailure::definition_source: return "definition_source";
    case ModelFailure::frame_changed: return "frame_changed";
  }
  return "definition_source";
}

std::string_view WorldFailureKey(WorldFailure failure) noexcept {
  switch (failure) {
    case WorldFailure::none: return "none";
    case WorldFailure::exact_build: return "exact_build";
    case WorldFailure::application_main: return "application_main";
    case WorldFailure::paused_frame: return "paused_frame";
    case WorldFailure::held_source: return "held_source";
    case WorldFailure::player_actor_binding: return "player_actor_binding";
    case WorldFailure::registry_source: return "registry_source";
    case WorldFailure::definition_identity: return "definition_identity";
    case WorldFailure::definition_key: return "definition_key";
    case WorldFailure::province_slot_source:
      return "province_slot_source";
    case WorldFailure::native_final_legality:
      return "native_final_legality";
    case WorldFailure::player_gold_source:
      return "player_gold_source";
    case WorldFailure::native_cost:
      return "native_cost";
    case WorldFailure::construction_state:
      return "construction_state";
    case WorldFailure::frame_changed: return "frame_changed";
  }
  return "registry_source";
}

std::string_view WorldActionCandidateFailureKey(
    PlayerWorldBuildingActionFailureV1 failure) noexcept {
  switch (failure) {
    case PlayerWorldBuildingActionFailureV1::none: return "none";
    case PlayerWorldBuildingActionFailureV1::source_unavailable:
      return "source_unavailable";
    case PlayerWorldBuildingActionFailureV1::frame_binding:
      return "frame_binding";
    case PlayerWorldBuildingActionFailureV1::resource_unknown:
      return "resource_unknown";
    case PlayerWorldBuildingActionFailureV1::economic_value_unknown:
      return "economic_value_unknown";
    case PlayerWorldBuildingActionFailureV1::active_construction:
      return "active_construction";
    case PlayerWorldBuildingActionFailureV1::no_budget_safe_candidate:
      return "no_budget_safe_candidate";
  }
  return "source_unavailable";
}

std::string_view WorldActionNativeFailureKey(
    xar::ck3::shared::PlayerWorldBuildingDirectActionFailureV1 failure)
    noexcept {
  using Failure = xar::ck3::shared::PlayerWorldBuildingDirectActionFailureV1;
  switch (failure) {
    case Failure::none: return "none";
    case Failure::already_submitted: return "already_submitted";
    case Failure::frame_binding: return "frame_binding";
    case Failure::candidate_drift: return "candidate_drift";
    case Failure::backend: return "backend";
    case Failure::validator: return "validator";
    case Failure::materialize: return "materialize";
    case Failure::receiver: return "receiver";
    case Failure::ownership: return "ownership";
  }
  return "backend";
}

std::string_view WorldDefinitionIdentityStageKey(
    PlayerWorldDefinitionIdentityStageV1 stage) noexcept {
  switch (stage) {
    case PlayerWorldDefinitionIdentityStageV1::none: return "none";
    case PlayerWorldDefinitionIdentityStageV1::element_read:
      return "element_read";
    case PlayerWorldDefinitionIdentityStageV1::element_null:
      return "element_null";
    case PlayerWorldDefinitionIdentityStageV1::vtable_read:
      return "vtable_read";
    case PlayerWorldDefinitionIdentityStageV1::vtable_mismatch:
      return "vtable_mismatch";
    case PlayerWorldDefinitionIdentityStageV1::building_type_id_read:
      return "building_type_id_read";
    case PlayerWorldDefinitionIdentityStageV1::building_type_id_negative:
      return "building_type_id_negative";
    case PlayerWorldDefinitionIdentityStageV1::building_type_id_duplicate:
      return "building_type_id_duplicate";
  }
  return "none";
}

ProbeResult FrameChanged() noexcept {
  ProbeResult result{};
  result.failure = ProbeFailure::frame_changed;
  return result;
}

std::string_view StatusKey(ProbeStatus status) noexcept {
  switch (status) {
    case ProbeStatus::view_candidate_cache_empty:
      return "view_candidate_cache_empty";
    case ProbeStatus::view_candidate_cache_present:
      return "view_candidate_cache_present";
    case ProbeStatus::unavailable:
      return "unavailable";
  }
  return "unavailable";
}

std::string_view FailureKey(ProbeFailure failure) noexcept {
  switch (failure) {
    case ProbeFailure::none: return "none";
    case ProbeFailure::exact_build: return "exact_build";
    case ProbeFailure::application_main: return "application_main";
    case ProbeFailure::session: return "session";
    case ProbeFailure::owner_path: return "owner_path";
    case ProbeFailure::view_missing: return "view_missing";
    case ProbeFailure::view_identity: return "view_identity";
    case ProbeFailure::candidate_span: return "candidate_span";
    case ProbeFailure::source_read: return "source_read";
    case ProbeFailure::frame_changed: return "frame_changed";
  }
  return "source_read";
}

}  // namespace

bool ExecutePlayerConstructionViewProbeMailboxV1(
    void* context, const MainThreadExecutionStampV1& stamp) noexcept {
  auto* query =
      static_cast<PlayerConstructionViewProbeMailboxContextV1*>(context);
  if (query == nullptr || !IsExecutingExactSlot(*query, stamp) ||
      query->completion !=
          PlayerConstructionViewProbeMailboxCompletionV1::not_executed ||
      query->executor_invocations != 0U) {
    if (query != nullptr) {
      query->completion =
          PlayerConstructionViewProbeMailboxCompletionV1::
              infrastructure_rejected;
    }
    return false;
  }
  ++query->executor_invocations;
  query->execution_stamp = stamp;
  if (!CaptureSameSnapshot(*query, stamp)) {
    query->result = FrameChanged();
    query->completion =
        PlayerConstructionViewProbeMailboxCompletionV1::completed;
    return true;
  }

  xar::ck3::shared::PlayerConstructionViewProcessAccessV1 process{};
  process.module_base = query->module_base;
  const auto source = xar::ck3::shared::
      BindCurrentProcessPlayerConstructionViewProbeSourceV1(process);
  xar::ck3::shared::PlayerConstructionViewProbeAdmissionV1 admission{};
  admission.exact_build_admitted = true;
  admission.application_main_thread = true;
  admission.session_live = true;
  admission.module_base = query->module_base;
  const auto first = xar::ck3::shared::ProbePlayerConstructionViewCacheV1(
      admission, source);
  const auto second = xar::ck3::shared::ProbePlayerConstructionViewCacheV1(
      admission, source);
  if (!CaptureSameSnapshot(*query, stamp) || first.status != second.status ||
      first.failure != second.failure ||
      first.view_present != second.view_present ||
      first.candidate_capacity != second.candidate_capacity ||
      first.cached_candidate_count != second.cached_candidate_count ||
      first.holding_view_visibility != second.holding_view_visibility) {
    query->result = FrameChanged();
  } else {
    query->result = second;
    if (second.status != ProbeStatus::unavailable &&
        second.failure == ProbeFailure::none) {
      ModelAccessProxyV1 proxy{query, &stamp};
      CampaignRootAccessV1 model_access{};
      model_access.context = &proxy;
      model_access.capture_frame = &ModelCaptureFrame;
      model_access.is_main_thread = &ModelIsMainThread;
      model_access.read_memory = &ModelReadMemory;
      query->player_model_sources = ReadPlayerHeldConstructionModelSourcesV1(
          query->module_base, true, model_access,
          {query->expected_revision});
      if (query->player_model_sources.status ==
          ModelStatus::sources_available) {
        const bool bound = ActiveViewUsesModelSource(source,
                                                    query->module_base);
        query->player_model_view_binding_verified = bound;
        if (!bound) {
          query->player_model_sources = {};
          query->player_model_sources.failure =
              ModelFailure::definition_source;
        } else {
          query->player_model_definition_source_count =
              query->player_model_sources.borrowed_definition_addresses.size();
          // No native definition address may outlive this application-main
          // callback; the private pipe receipt carries only its source count.
          std::vector<std::uintptr_t>{}.swap(
              query->player_model_sources.borrowed_definition_addresses);
          PlayerWorldBuildingNativeCallAccessV1 native_call{};
          native_call.module_base = query->module_base;
          native_call.exact_build_admitted = true;
          PlayerWorldBuildingSourceAccessV1 world_access{};
          world_access.campaign = model_access;
          world_access.final_legality =
              BindCurrentProcessPlayerWorldBuildingFinalLegalityV1(
                  native_call);
          world_access.final_legality_context = &native_call;
          world_access.native_cost =
              BindCurrentProcessPlayerWorldBuildingCostV1(native_call);
          world_access.native_cost_context = &native_call;
          query->player_world_building_source_executed = true;
          query->player_world_building_sources =
              ReadPlayerWorldBuildingDefinitionSourcesV1(
                  query->module_base, true, world_access,
                  {query->expected_revision, -1, 512, 8});
        }
      }
      if (!CaptureSameSnapshot(*query, stamp)) {
        query->result = FrameChanged();
        query->player_model_sources = {};
        query->player_model_sources.failure = ModelFailure::frame_changed;
        query->player_model_view_binding_verified.reset();
        query->player_model_definition_source_count = 0;
        query->player_world_building_sources = {};
        query->player_world_building_sources.failure =
            WorldFailure::frame_changed;
        query->player_world_building_source_executed = true;
      }
      if (query->request_private_action &&
          query->result.status != ProbeStatus::unavailable &&
          query->player_world_building_source_executed &&
          query->player_world_building_sources.source_available &&
          query->player_world_building_sources.failure == WorldFailure::none &&
          CaptureSameSnapshot(*query, stamp)) {
        query->private_action_candidate =
            SelectPlayerWorldBuildingActionCandidateV1(
                query->player_world_building_sources, stamp.pump_epoch,
                query->minimum_gold_reserve_raw);
        if (query->private_action_candidate.ready) {
          xar::ck3::shared::PlayerWorldBuildingDirectActionRequestV1 action{};
          action.exact_build_admitted = true;
          action.session_live = true;
          action.module_base = query->module_base;
          action.source = &query->player_world_building_sources;
          action.candidate = &query->private_action_candidate;
          (void)xar::ck3::shared::SubmitPlayerWorldBuildingDirectActionV1(
              query->private_action_state, action, stamp);
        }
      }
    }
  }
  query->completion =
      PlayerConstructionViewProbeMailboxCompletionV1::completed;
  return true;
}

std::string SerializePlayerConstructionViewProbePrivateV1(
    const PlayerConstructionViewProbeMailboxContextV1& query) {
  const auto& result = query.result;
  std::string json =
      "{\"schema_version\":1,\"private_key\":\"g2_player_construction_view_probe_v1\",\"advertised\":false,\"status\":\"";
  json += StatusKey(result.status);
  json += "\",\"failure\":\"";
  json += FailureKey(result.failure);
  json += "\",\"view_present\":";
  json += result.view_present ? "true" : "false";
  json += ",\"candidate_capacity\":";
  json += std::to_string(result.candidate_capacity);
  json += ",\"cached_candidate_count\":";
  json += std::to_string(result.cached_candidate_count);
  json += ",\"snapshot_revision\":";
  json += std::to_string(query.expected_revision);
  json += ",\"date_raw\":";
  json += std::to_string(query.expected_snapshot.date_raw);
  json += ",\"proof_epoch\":";
  json += std::to_string(query.execution_stamp.pump_epoch);
  json += ",\"holding_view_visibility\":{";
  json += "\"widget_key\":\"holding_view\",\"status\":\"";
  const auto visibility = result.holding_view_visibility;
  json += visibility == xar::ck3::shared::
                           PlayerConstructionHoldingViewVisibilityV1::
                               unavailable
              ? "unavailable"
              : "available";
  json += "\",\"effective_visible\":";
  json += visibility == xar::ck3::shared::
                           PlayerConstructionHoldingViewVisibilityV1::
                               unavailable
              ? "null"
              : visibility == xar::ck3::shared::
                                  PlayerConstructionHoldingViewVisibilityV1::
                                      visible
                    ? "true"
                    : "false";
  json += '}';
  const auto& model = query.player_model_sources;
  const bool model_available =
      model.status == ModelStatus::sources_available &&
      model.failure == ModelFailure::none &&
      query.player_model_view_binding_verified == true;
  json += ",\"player_model_sources\":{\"schema_version\":1,\"advertised\":false,\"status\":\"";
  json += ModelStatusKey(model.status);
  json += "\",\"failure\":\"";
  json += ModelFailureKey(model.failure);
  json += "\",\"snapshot_revision\":";
  json += model_available ? std::to_string(model.snapshot_revision) : "null";
  json += ",\"date_raw\":";
  json += model_available ? std::to_string(model.date_raw) : "null";
  json += ",\"player_character_id\":";
  json += model_available ? std::to_string(model.player_character_id) : "null";
  json += ",\"view_model_binding_verified\":";
  json += !query.player_model_view_binding_verified.has_value()
              ? "null"
              : *query.player_model_view_binding_verified ? "true" : "false";
  json += ",\"directly_held_barony_provinces\":[";
  if (model_available) {
    for (std::size_t index = 0;
         index < model.directly_held_barony_provinces.size(); ++index) {
      if (index != 0) json += ',';
      const auto& holding = model.directly_held_barony_provinces[index];
      json += "{\"barony_title_id\":";
      json += std::to_string(holding.barony_title_id);
      json += ",\"province_id\":";
      json += std::to_string(holding.province_id);
      json += '}';
    }
  }
  json += "],\"definition_source_count\":";
  json += model_available
              ? std::to_string(query.player_model_definition_source_count)
              : "null";
  json += ",\"legal_construction_evaluated\":false}";
  const auto& world = query.player_world_building_sources;
  const bool world_available =
      query.player_world_building_source_executed &&
      world.source_available && world.failure == WorldFailure::none;
  json += ",\"player_world_building_sources\":{\"schema_version\":1,\"advertised\":false,\"read_only\":true,\"status\":\"";
  json += !query.player_world_building_source_executed
              ? "not_executed"
              : world_available ? "source_available" : "unavailable";
  json += "\",\"failure\":\"";
  json += query.player_world_building_source_executed
              ? WorldFailureKey(world.failure)
              : "not_executed";
  const auto& diagnostic = world.definition_identity_diagnostic;
  const bool identity_failure =
      query.player_world_building_source_executed &&
      world.failure == WorldFailure::definition_identity;
  json += "\",\"definition_identity_diagnostic\":{\"registry_count\":";
  json += identity_failure && diagnostic.registry_count >= 0
              ? std::to_string(diagnostic.registry_count) : "null";
  json += ",\"failed_index\":";
  json += identity_failure && diagnostic.failed_index >= 0
              ? std::to_string(diagnostic.failed_index) : "null";
  json += ",\"stage\":\"";
  json += identity_failure
              ? WorldDefinitionIdentityStageKey(diagnostic.stage) : "none";
  json += "\",\"observed_vtable_rva\":";
  json += identity_failure && diagnostic.has_observed_vtable_rva
              ? std::to_string(diagnostic.observed_vtable_rva) : "null";
  json += ",\"observed_building_type_id\":";
  json += identity_failure && diagnostic.has_observed_building_type_id
              ? std::to_string(diagnostic.observed_building_type_id) : "null";
  json += "}";
  json += ",\"snapshot_revision\":";
  json += world_available ? std::to_string(world.snapshot_revision) : "null";
  json += ",\"date_raw\":";
  json += world_available ? std::to_string(world.date_raw) : "null";
  json += ",\"player_character_id\":";
  json += world_available ? std::to_string(world.player_character_id) : "null";
  json += ",\"definition_source_count\":";
  json += world_available
              ? std::to_string(world.definition_source_count) : "null";
  json += ",\"final_legality_checks\":";
  json += world_available
              ? std::to_string(world.final_legality_checks) : "null";
  json += ",\"native_final_legality_evaluated\":";
  json += world_available && world.native_final_legality_evaluated
              ? "true" : "false";
  json += ",\"native_cost_evaluated\":";
  json += world_available && world.native_cost_evaluated
              ? "true" : "false";
  json += ",\"native_cost_checks\":";
  json += world_available ? std::to_string(world.native_cost_checks) : "null";
  json += ",\"player_gold_raw\":";
  json += world_available && world.player_gold_observed
              ? std::to_string(world.player_gold_raw) : "null";
  json += ",\"player_gold_scale\":";
  json += world_available && world.player_gold_observed
              ? "100000" : "null";
  json += ",\"checks_truncated\":";
  json += world_available && world.checks_truncated ? "true" : "false";
  json += ",\"cost_ready\":false,\"construction_action_ready\":false";
  json += ",\"directly_held_barony_provinces\":[";
  if (world_available) {
    for (std::size_t index = 0;
         index < world.directly_held_barony_provinces.size(); ++index) {
      if (index != 0) json += ',';
      const auto& holding = world.directly_held_barony_provinces[index];
      json += "{\"barony_title_id\":";
      json += std::to_string(holding.barony_title_id);
      json += ",\"province_id\":";
      json += std::to_string(holding.province_id);
      json += '}';
    }
  }
  json += "],\"active_constructions\":[";
  if (world_available) {
    for (std::size_t index = 0; index < world.active_constructions.size();
         ++index) {
      if (index != 0) json += ',';
      const auto& active = world.active_constructions[index];
      json += "{\"barony_title_id\":";
      json += std::to_string(active.barony_title_id);
      json += ",\"province_id\":";
      json += std::to_string(active.province_id);
      json += ",\"active\":";
      json += active.active ? "true" : "false";
      json += ",\"building_type_id\":";
      json += active.active ? std::to_string(active.building_type_id) : "null";
      json += ",\"slot_index\":";
      json += active.active ? std::to_string(active.slot_index) : "null";
      json += ",\"initiator_character_id\":";
      json += active.active ? std::to_string(active.initiator_character_id)
                            : "null";
      json += '}';
    }
  }
  json += "],\"completed_buildings_observed\":";
  json += world_available && world.completed_buildings_observed
              ? "true" : "false";
  json += ",\"completed_buildings\":";
  if (world_available && world.completed_buildings_observed) {
    json += '[';
    for (std::size_t index = 0; index < world.completed_buildings.size();
         ++index) {
      if (index != 0) json += ',';
      const auto& built = world.completed_buildings[index];
      json += "{\"barony_title_id\":";
      json += std::to_string(built.barony_title_id);
      json += ",\"province_id\":";
      json += std::to_string(built.province_id);
      json += ",\"building_type_id\":";
      json += std::to_string(built.building_type_id);
      json += ",\"slot_index\":";
      json += std::to_string(built.slot_index);
      json += '}';
    }
    json += ']';
  } else {
    json += "null";
  }
  json += ",\"legal_samples\":[";
  if (world_available) {
    for (std::size_t index = 0; index < world.legal_samples.size(); ++index) {
      if (index != 0) json += ',';
      const auto& sample = world.legal_samples[index];
      json += "{\"barony_title_id\":";
      json += std::to_string(sample.barony_title_id);
      json += ",\"province_id\":";
      json += std::to_string(sample.province_id);
      json += ",\"building_type_id\":";
      json += std::to_string(sample.building_type_id);
      // ReadBuildingKey admits only lowercase ASCII, digits and underscore.
      json += ",\"building_key\":\"";
      json += sample.building_key;
      json += '"';
      json += ",\"slot_index\":";
      json += std::to_string(sample.slot_index);
      json += ",\"native_cost_observed\":";
      json += sample.native_cost_observed ? "true" : "false";
      json += ",\"cost_raw_slots\":";
      if (sample.native_cost_observed) {
        json += '[';
        for (std::size_t cost_index = 0;
             cost_index < sample.cost_raw_slots.size(); ++cost_index) {
          if (cost_index != 0) json += ',';
          json += std::to_string(sample.cost_raw_slots[cost_index]);
        }
        json += ']';
      } else {
        json += "null";
      }
      json += ",\"cost_raw_native\":";
      if (sample.native_cost_observed) {
        json += '[';
        for (std::size_t cost_index = 0;
             cost_index < sample.cost_raw_native.size(); ++cost_index) {
          if (cost_index != 0) json += ',';
          json += std::to_string(sample.cost_raw_native[cost_index]);
        }
        json += ']';
      } else {
        json += "null";
      }
      json += '}';
    }
  }
  json += "]}";
  if (query.request_private_action) {
    using Phase =
        xar::ck3::shared::PlayerWorldBuildingDirectActionPhaseV1;
    const auto& choice = query.private_action_candidate;
    const auto& action = query.private_action_state;
    json += ",\"private_action\":{\"schema_version\":1,\"advertised\":false,\"status\":\"";
    json += !choice.ready
                ? "candidate_unready"
                : action.phase == Phase::pending_receipt
                      ? "pending_receipt"
                      : action.phase == Phase::rejected
                            ? "validator_or_receiver_rejected"
                            : action.phase == Phase::red ? "red"
                                                         : "not_executed";
    json += "\",\"candidate_failure\":\"";
    json += WorldActionCandidateFailureKey(choice.failure);
    json += "\",\"native_failure\":\"";
    json += WorldActionNativeFailureKey(action.failure);
    json += "\",\"stock_candidate_ready\":";
    json += choice.ready ? "true" : "false";
    json += ",\"production_native_path\":";
    json += action.production_native_path ? "true" : "false";
    json += ",\"applied\":false,\"proof_epoch\":";
    json += choice.ready ? std::to_string(choice.proof_epoch) : "null";
    json += ",\"actor_character_id\":";
    json += choice.ready ? std::to_string(choice.actor_character_id) : "null";
    json += ",\"barony_title_id\":";
    json += choice.ready ? std::to_string(choice.barony_title_id) : "null";
    json += ",\"province_id\":";
    json += choice.ready ? std::to_string(choice.province_id) : "null";
    json += ",\"building_type_id\":";
    json += choice.ready ? std::to_string(choice.building_type_id) : "null";
    json += ",\"slot_index\":";
    json += choice.ready ? std::to_string(choice.slot_index) : "null";
    json += ",\"gold_before_raw\":";
    json += choice.ready ? std::to_string(choice.player_gold_before_raw)
                         : "null";
    json += ",\"stock_gold_cost_raw\":";
    json += choice.ready ? std::to_string(choice.stock_gold_cost_raw)
                         : "null";
    json += ",\"gold_after_reserve_raw\":";
    json += choice.ready ? std::to_string(choice.gold_reserve_after_raw)
                         : "null";
    json += ",\"receiver_command_sequence\":";
    json += action.receiver_command_sequence != 0
                ? std::to_string(action.receiver_command_sequence) : "null";
    json += ",\"validator_calls\":";
    json += std::to_string(action.validator_calls);
    json += ",\"materialize_calls\":";
    json += std::to_string(action.materialize_calls);
    json += ",\"receiver_calls\":";
    json += std::to_string(action.receiver_calls);
    json += '}';
  }
  json += ",\"executor_invocations\":";
  json += std::to_string(query.executor_invocations);
  json += '}';
  return json;
}

}  // namespace xar::ck3_11906
