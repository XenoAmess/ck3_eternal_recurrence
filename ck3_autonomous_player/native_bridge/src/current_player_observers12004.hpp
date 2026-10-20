#pragma once
#include "xar_bridge/artifact_personal_use12004.hpp"
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "ghw_permission_observer/ghw_variable_observer_12004.hpp"
#include "ghw_permission_observer/ghw_object_links_12004.hpp"
#include <optional>
#include <string>

namespace xar::ck3_12004::current_player_observers {
inline constexpr std::string_view artifact_step="query-player-artifact-personal-use-v1";
inline constexpr std::string_view artifact_submit_step="submit-player-artifact-personal-use-v1-private";
inline constexpr std::string_view artifact_post_step="query-player-artifact-personal-use-action-post-v1-private";
inline constexpr std::string_view ghw_step="query-player-ghw-permissions-v1-private";
struct GhwObservation {
  bool available=false,frame_verified=false,loaded_source_pins_verified=false;
  std::uint64_t capture_epoch=0;
  std::int32_t date_raw=0,played_character_id=-1;
  std::optional<std::uint32_t> faith_id,religion_id;
  religion::ghw_variables_candidate::Observation variables{};
  religion::ghw_links_candidate::Observation object_links{};
  std::string unavailable_reason="not_read";
};
struct ArtifactActionObservation {
  bool available=false,read_only=false,intent_found=false,desired_inventory_state_observed=false;
  bool after_attempted=false;
  std::uint32_t played_character_id=artifact_personal_use::absent;
  artifact_personal_use::Request request{};
  artifact_personal_use::Result result{};
  artifact_personal_use::Observation after{};
  std::string unavailable_reason="not_read",post_status="intent_unavailable";
};
// Internal source-only serializer seams are shared by the actual owner provider
// and finite reader->wire fixtures. No native pointer is serialized.
std::string SerializeArtifactPersonalUse12004(const artifact_personal_use::Observation&);
std::string SerializeGhwPermissions12004(const GhwObservation&);
std::string SerializeArtifactPersonalAction12004(const ArtifactActionObservation&);
bool IsCurrentPlayerObserverStep12004(std::string_view) noexcept;
bool ExecuteArtifactPersonalRead12004(void*,const ck3_11906::MainThreadExecutionStampV1&) noexcept;
bool ExecuteArtifactPersonalAction12004(void*,const ck3_11906::MainThreadExecutionStampV1&) noexcept;
bool ExecuteGhwPermissionsRead12004(void*,const ck3_11906::MainThreadExecutionStampV1&) noexcept;
// Called only by the existing global worker, using its actual retained current
// revision/connection. All caller expectations are matched against those values.
bool HandleCurrentPlayerObserver12004(const game::GameAdapter&,
    ck3_11906::MainThreadQueryMailboxV1&,const game::Snapshot* published,
    std::uint64_t actual_revision,std::uint64_t actual_connection_generation,
    std::string_view step,std::string_view payload,std::string_view request_id,
    std::string& serialized,std::string& failure) noexcept;
}
