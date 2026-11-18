#pragma once
#include "xar_bridge/ck3_1210_actor_foundation_v1.hpp"
#include "xar_bridge/ck3_1210_personal_gold_v1.hpp"
#include <string>

namespace xar::ck3_1210 {
inline constexpr char kActorResourceLeafSchemaV2[] = "ck3_1210_actor_resource_leaf_v2";
inline constexpr char kActorResourceLeafStepV2[] = "query-actor-resource-leaf-v2";
inline constexpr char kActorResourceLeafCapabilityV2[] = "game.query.actor-resource-leaf.v2";
inline constexpr char kActorResourceRenownUnknownV2[] = "dynasty_renown_main_owner_not_qualified";
inline constexpr char kActorResourceTreasuryUnknownV2[] = "government_treasury_main_owner_not_qualified";

// Constructed inside the existing verified Actor mailbox, from its real
// descriptor, GetModuleHandle image, bound Core, and current paused prefix.
// Caller-controlled actor addresses and raw callback values are not accepted.
struct ActorResourceLeafSourceInputV2 {
  std::uintptr_t image_base = 0;
  std::string_view game_version, executable_sha256, adapter_id;
  bool application_main_owner_admitted = false;
  PersonalGoldBindingsV1 gold_bindings{};
  CoreSnapshotPrefix expected{};
};
struct ActorResourceLeafObservationV2 {
  bool exact_image_verified = false;
  bool application_main_observed = false;
  bool core_interval_verified = false;
  bool gold_interval_verified = false;
  CoreSnapshotPrefix before{}, after{};
  std::optional<std::int32_t> actor_character_id;
  std::optional<std::int64_t> personal_gold_before_raw, actor_gold_raw,
      personal_gold_after_raw, prestige_raw, piety_raw;
  // Renown/true treasury have no observed-value member in this production
  // contract. Static decoder evidence does not grant their main-thread role.
  std::string_view unavailable_reason = "actor_resource_leaf_not_read";
};

// Real source path: Core-before -> ReadPersonalGoldV1 ->
// ReadActorFoundationV1 -> ReadPersonalGoldV1 -> Core-after. All complete
// prefixes, actor IDs, exact image metadata, source scales and wallet samples
// must agree. Failure clears every amount. No actor/header layout is guessed.
// Outer mailbox independently proves main/TLS custody; no Full/Root/action
// readiness, revision, world mutation, SAVE or capability is minted here.
bool ReadActorResourceLeafV2(const ActorResourceLeafSourceInputV2 &input,
    ActorResourceLeafObservationV2 &output) noexcept;

// Strict formatter rejects inconsistent DTOs and always keeps renown and
// true_treasury unavailable. Its gold interval is PERSONAL wallet coherence,
// not treasury, spending permission, monthly flow or complete finances.
std::string SerializeActorResourceLeafV2(const ActorResourceLeafObservationV2 &);
std::string SerializeActorResourceLeafCommandV2(std::string_view request_id,
    const ActorResourceLeafObservationV2 &);
} // namespace xar::ck3_1210
