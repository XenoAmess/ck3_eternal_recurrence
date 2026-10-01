#pragma once

#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12002_claim_terms.hpp"
#include "xar_bridge/ck3_12002_combat.hpp"
#include "xar_bridge/ck3_12002_context.hpp"
#include "xar_bridge/ck3_12002_declarations.hpp"
#include "xar_bridge/ck3_12002_diplomacy.hpp"
#include "xar_bridge/ck3_12002_events.hpp"
#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_family.hpp"
#endif
#include "xar_bridge/ck3_12002_military.hpp"
#include "xar_bridge/ck3_12002_phase.hpp"
#include "xar_bridge/ck3_12002_settlement.hpp"

#include <memory>

namespace xar::game {

// Version-private dependency bundle. Production fills it with addresses from
// the exact image; offline integration fixtures replace them with owned data.
struct Ck3_12002AdapterBindings {
  ck3_12002::CoreBindings core;
  ck3_12002::CommandBindings commands;
  ck3_12002::EventsBindings events;
  ck3_12002::ArmyBindings armies;
  ck3_12002::WorldBindings world;
  ck3_12002::ProvinceBindings provinces;
  ck3_12002::MilitaryBindings military;
  ck3_12002::ContextBindings marriage;
#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
  ck3_12002::FamilyBindings family;
#endif
  ck3_12002::DiplomacyBindings diplomacy;
  ck3_12002::DeclarationsBindings declarations;
  ck3_12002::ClaimTermsBindings terms;
  ck3_12002::CombatBindings combat;
  ck3_12002::PhaseBindings phase;
  ck3_12002::SettlementBindings settlement;
};

Ck3_12002AdapterBindings BindCk3_12002AdapterImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
std::unique_ptr<GameAdapter> CreateCk3_12002AdapterFromBindings(
    Ck3_12002AdapterBindings bindings) noexcept;

// Worker timeline operations use its owner-published full snapshot. These
// private exact-build entry points validate one current core prefix before
// using that frame to decide idempotence or queue the existing time command.
// A stale prefix or a different adapter returns unavailable; no full native
// snapshot is read on the bridge worker thread.
PauseSubmitResult SubmitCk3_12002PauseMapObserved(
    const GameAdapter &adapter, const Snapshot &observed_snapshot) noexcept;
ResumeSubmitResult SubmitCk3_12002ResumeMapObserved(
    const GameAdapter &adapter, const Snapshot &observed_snapshot) noexcept;

const AdapterDescriptor &Ck3_12002AdapterDescriptor() noexcept;
std::unique_ptr<GameAdapter>
CreateCk3_12002Adapter(std::string_view executable_sha256) noexcept;

} // namespace xar::game
