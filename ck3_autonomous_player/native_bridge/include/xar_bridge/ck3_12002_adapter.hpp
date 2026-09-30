#pragma once

#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12002_claim_terms.hpp"
#include "xar_bridge/ck3_12002_combat.hpp"
#include "xar_bridge/ck3_12002_context.hpp"
#include "xar_bridge/ck3_12002_declarations.hpp"
#include "xar_bridge/ck3_12002_diplomacy.hpp"
#include "xar_bridge/ck3_12002_events.hpp"
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

const AdapterDescriptor &Ck3_12002AdapterDescriptor() noexcept;
std::unique_ptr<GameAdapter>
CreateCk3_12002Adapter(std::string_view executable_sha256) noexcept;

} // namespace xar::game
