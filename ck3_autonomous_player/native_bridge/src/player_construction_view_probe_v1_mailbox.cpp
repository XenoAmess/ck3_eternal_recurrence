#include "player_construction_view_probe_v1_mailbox.hpp"

#include "player_construction_view_probe_v1_process.hpp"

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
        }
      }
      if (!CaptureSameSnapshot(*query, stamp)) {
        query->result = FrameChanged();
        query->player_model_sources = {};
        query->player_model_sources.failure = ModelFailure::frame_changed;
        query->player_model_view_binding_verified.reset();
        query->player_model_definition_source_count = 0;
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
  json += ",\"executor_invocations\":";
  json += std::to_string(query.executor_invocations);
  json += '}';
  return json;
}

}  // namespace xar::ck3_11906
