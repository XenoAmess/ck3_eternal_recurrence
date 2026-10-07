#pragma once

#include "xar_bridge/ck3_12004_gift_opinion.hpp"
#include "xar_bridge/player_prisoner_collection_query_v1_private.hpp"

#include <optional>
#include <string>

namespace xar::ck3_12004 {

struct KeeperOpinionBindings12004 {
  GiftOpinionBindings12004 opinion{};
};

// Independent current actor-to-target opinion. The full target ID may be
// retained after release; this value does not assert current custody.
struct KeeperOpinion12004 {
  bool available = false;
  std::string unavailable_reason;
  bridge::PlayerPrisonerFrameV1 frame{};
  std::uint32_t target_character_id = 0;
  std::optional<std::int32_t> actor_opinion_of_target;
};

KeeperOpinionBindings12004 BindKeeperOpinionImage12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

bool ReadKeeperOpinion12004(
    const KeeperOpinionBindings12004 &bindings,
    const bridge::PlayerPrisonerCollectionAccessV1 &access,
    const bridge::PlayerPrisonerFrameV1 &expected_frame,
    std::uint32_t target_character_id, KeeperOpinion12004 &output) noexcept;

std::string SerializeKeeperOpinion12004(const KeeperOpinion12004 &row);

} // namespace xar::ck3_12004
