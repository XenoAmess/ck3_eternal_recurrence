#pragma once

#include "xar_bridge/ck3_12004_gift_opinion.hpp"
#include "xar_bridge/player_prisoner_collection_query_v1_private.hpp"

#include <optional>
#include <string>

namespace xar::ck3_12004 {

inline constexpr std::string_view kPrisonerReleaseMaterialOpinionKey12004 =
    "released_from_prison";
using PrisonerReleaseMaterialHash12004 = std::int32_t (*)(
    void *, const char *, std::uint32_t);

struct PrisonerReleaseMaterialOpinionBindings12004 {
  GiftOpinionBindings12004 opinion{};
  PrisonerReleaseMaterialHash12004 hash_key = nullptr;
};

PrisonerReleaseMaterialOpinionBindings12004
BindPrisonerReleaseMaterialOpinionImage12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

struct PrisonerReleaseMaterialOpinion12004 {
  bool available = false;
  std::string unavailable_reason;
  bridge::PlayerPrisonerFrameV1 frame{};
  std::uint32_t target_character_id = 0;
  std::optional<std::int32_t> target_opinion_of_actor;
  bool modifier_observed = false;
  bool modifier_present = false;
  std::optional<std::int32_t> modifier_value;
};

// Independent current pair measurement. The target need not remain in the
// prisoner collection. Presence or a positive delta does not prove release
// causation, custody change, duration or other on-accept consequences.
bool ReadPrisonerReleaseMaterialOpinion12004(
    const PrisonerReleaseMaterialOpinionBindings12004 &bindings,
    const bridge::PlayerPrisonerCollectionAccessV1 &access,
    const bridge::PlayerPrisonerFrameV1 &expected,
    std::uint32_t target_character_id,
    PrisonerReleaseMaterialOpinion12004 &output) noexcept;

std::string SerializePrisonerReleaseMaterialOpinion12004(
    const PrisonerReleaseMaterialOpinion12004 &output);

} // namespace xar::ck3_12004
