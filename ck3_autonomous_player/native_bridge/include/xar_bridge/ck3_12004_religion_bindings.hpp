#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12003_player_tenet_knowledge_catalogue.hpp"
#include "xar_bridge/ck3_12003_target_rite_tenet_comparison.hpp"
#include "xar_bridge/religion_doctrine12002_choices.hpp"
#include "xar_bridge/religion_doctrine12002_query.hpp"
#include "xar_bridge/religion_doctrine12002_tenet_rows.hpp"
#include "xar_bridge/religion_reform12002_query_runtime.hpp"

namespace xar::ck3_12004::religion {

// The software DTOs/readers are shared; every image pointer is supplied by
// the independently mapped .4 profile and exact .4 executable identity.
using ContextBindings = ck3_12002::religion::Bindings;
using RiteModelBindings = ck3_12002::religion_reform::rite::Bindings;
using MainRiteBindings = ck3_12002::religion_reform::MainRiteBindings;
using DraftWindowBindings = ck3_12002::religion_reform::DraftWindowBindings;
using ReformQueryBindings = ck3_12002::religion_reform::query::Bindings;
using CurrentDoctrineBindings =
    ck3_12002::religion::doctrine12002::CurrentDoctrineBindings;
using DoctrineKnowledgeBindings =
    ck3_12002::religion::doctrine12002::KnowledgeBindings;

struct PlayerTenetBindings {
  ContextBindings context{};
  ck3_12002::religion::doctrine12002::TenetRowsBindings rows{};
  ck3_12003::religion::target_tenet::Bindings comparison{};
  ck3_12003::religion::tenet_knowledge::Bindings knowledge{};
};

ContextBindings BindReligionContextImage12004(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
RiteModelBindings BindRiteModelImage12004(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
MainRiteBindings BindFaithMainRiteUnreformedImage12004(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
DraftWindowBindings BindCurrentRiteCreationWindow12004(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;

// Current context/model/main-Rite/window and the existing adopted cost,
// eligibility, popup choices and creation-terms providers use independently
// mapped .4 bindings. Draft absence retains its ordinary typed observations.
ReformQueryBindings BindReformQueryImage12004(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
CurrentDoctrineBindings BindCurrentDoctrineImage12004(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
DoctrineKnowledgeBindings BindDoctrineKnowledgeImage12004(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
PlayerTenetBindings BindPlayerTenetImage12004(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;

// The actual .4 core selector precedes the shared software reader. The latter
// retains its existing two-sample and owning-frame checks; no new game input
// or complete gameplay Snapshot is constructed here.
bool ReadPlayedReligionContext12004(const ContextBindings &,
    std::uint64_t capture_epoch, ck3_12002::religion::Context &) noexcept;
bool ReadPlayedReformQuery12004(const ReformQueryBindings &,
    std::uint64_t capture_epoch,
    ck3_12002::religion_reform::query::Observation &) noexcept;
bool ReadPlayedCurrentDoctrines12004(const CurrentDoctrineBindings &,
    std::uint64_t capture_epoch,
    ck3_12002::religion::doctrine12002::CurrentDoctrineContext &) noexcept;
bool ReadPlayedDoctrineKnowledge12004(const DoctrineKnowledgeBindings &,
    std::uint64_t capture_epoch,
    ck3_12002::religion::doctrine12002::PlayedDoctrineKnowledge &) noexcept;
bool ReadPlayedDoctrineKnowledgeByKey12004(const DoctrineKnowledgeBindings &,
    std::string_view doctrine_key, std::uint64_t capture_epoch,
    ck3_12002::religion::doctrine12002::PlayedDoctrineKnowledgeLookup &) noexcept;
bool ReadPlayedTenetRows12004(const ContextBindings &,
    const ck3_12002::religion::doctrine12002::TenetRowsBindings &,
    std::uint64_t capture_epoch,
    ck3_12002::religion::doctrine12002::TenetRowsContext &) noexcept;
bool ReadPlayedTargetRiteTenetComparison12004(
    const ck3_12003::religion::target_tenet::Bindings &,
    std::uint32_t target_rite_id, std::string_view tenet_key,
    std::uint64_t capture_epoch,
    ck3_12003::religion::target_tenet::Comparison &) noexcept;
bool ReadPlayedTenetKnowledgeCatalogue12004(
    const ck3_12003::religion::tenet_knowledge::Bindings &,
    std::uint64_t capture_epoch,
    ck3_12003::religion::tenet_knowledge::Catalogue &) noexcept;

} // namespace xar::ck3_12004::religion
