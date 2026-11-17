#pragma once

#include "xar_bridge/ck3_1210.hpp"

#include <cstdint>
#include <optional>
#include <string_view>
#include <vector>

namespace xar::ck3_1210 {

inline constexpr char kActorFoundationSchemaV1[] = "ck3_1210_actor_foundation_v1";
inline constexpr std::int64_t kActorFoundationResourceScaleV1 = 100'000;
// Conservative observation scope, not an asserted engine spouse limit.
inline constexpr std::size_t kActorFoundationSpouseObservationLimitV1 = 64;

struct ActorFoundationBindingsV1 {
  bool exact_build_admitted = false;
  CoreBindings core{};
};

struct ActorFoundationRelationshipsV1 {
  // -1 means a successfully observed absent scalar relation. Every other
  // signed full32 value, including zero, must resolve with exact generation.
  std::int32_t betrothed_character_id = -1;
  std::int32_t primary_spouse_character_id = -1;
  // Native order and full signed IDs retained. No alive/dead script filter.
  std::vector<std::int32_t> spouse_character_ids;
};

// Internal observation only. No serializer, capability, complete Snapshot or
// action qualification. Application-main custody belongs to the outer owner.
struct ActorFoundationObservationV1 {
  std::string_view schema = kActorFoundationSchemaV1;
  std::string_view game_version = kGameVersion;
  std::string_view steam_build_id = kSteamBuildId;
  std::string_view executable_sha256 = kExecutableSha256;
  std::size_t executable_file_size = kExecutableFileSize;
  bool available = false;
  // Two complete Core prefixes and actor headers agreed; not a thread stamp.
  bool same_frame_ready = false;
  bool resources_ready = false;
  bool relationships_ready = false;
  bool partial = true;
  bool full_snapshot_available = false;
  bool treasury_observed = false;
  bool monthly_flow_observed = false;
  CoreSnapshotPrefix frame{};
  // Resource group is atomic. Stress retains the signed native DWORD; no
  // promise that negative stress satisfies a downstream gameplay contract.
  // Include the independently proven personal wallet in this same sample;
  // the narrow personal-gold query remains a separate, unchanged interface.
  std::optional<std::int64_t> gold_raw;
  std::optional<std::int64_t> prestige_raw;
  std::optional<std::int64_t> piety_raw;
  std::optional<std::int32_t> stress_points;
  std::int64_t resource_scale = kActorFoundationResourceScaleV1;
  // Present empty relations means a real empty family, not a failed read.
  std::optional<ActorFoundationRelationshipsV1> relationships;
  std::string_view resources_unavailable_reason = "resources_not_read";
  std::string_view relationships_unavailable_reason = "relationships_not_read";
  std::string_view unavailable_reason = "actor_foundation_not_read";
};

ActorFoundationBindingsV1 BindActorFoundationImageV1(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;

// False if neither group was observed or the expected frame/identity failed.
// A stable frame may expose one group with the other explicitly unavailable.
// Bad pointers, stale peer IDs and inconsistent vectors never become empty.
bool ReadActorFoundationV1(const ActorFoundationBindingsV1 &bindings,
    const CoreSnapshotPrefix &expected,
    ActorFoundationObservationV1 &output) noexcept;

} // namespace xar::ck3_1210
