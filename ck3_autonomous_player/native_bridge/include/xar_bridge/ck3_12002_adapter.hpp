#pragma once

#include "xar_bridge/ck3_12003_maa_recruitment.hpp"
#include "xar_bridge/ck3_12003_maa_create.hpp"

#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12002_battle.hpp"
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
#include "xar_bridge/ck3_12002_prewar_muster.hpp"
#include "xar_bridge/ck3_12003_war_cash_current_reader.hpp"
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
  ck3_12002::BattleBindings native_owner_recall;
  ck3_12003::NativeMaaRecruitmentBindings native_maa_recruitment;
  ck3_12003::OwnedRegimentsBindingsV1 owned_regiments;
  ck3_12003::NativeMaaCreateBindings native_maa_create;
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
  ck3_12003::war_cash_current::Bindings war_cash_current;
};

// Same row publisher called by the current Army query and focused fixtures.
void AttachNativeMaaRecruitmentInputsToArmyRowsV1(
    const ck3_12003::NativeMaaRecruitmentBindings &,
    std::vector<ArmyStrengthSnapshot> &) noexcept;

void AttachPlayerOwnedRegimentsToArmyRowsV1(
    const ck3_12002::CoreBindings &,
    const ck3_12003::OwnedRegimentsBindingsV1 &,
    const Snapshot &, std::vector<ArmyStrengthSnapshot> &) noexcept;

// Used by the existing paused owning-thread private action provider.
NativeMaaRegularPersonalCreateSubmissionV1 SubmitNativeMaaRegularPersonalCreate(
    const GameAdapter &, const NativeMaaRegularPersonalCreateRequestV1 &) noexcept;

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

ck3_12002::PrewarDefaultMusterStatusV1 ReadCk3_12003PlayerDefaultRaiseV1(
    const GameAdapter &adapter,
    ck3_12002::PlayerDefaultRaiseObservationV1 &output) noexcept;

bool ReadCk3_12003WarCashCurrentResourcesV1(
    const GameAdapter &adapter, const Snapshot &snapshot,
    ck3_12003::war_cash_current::ActorResources &output) noexcept;

const AdapterDescriptor &Ck3_12002AdapterDescriptor() noexcept;
std::unique_ptr<GameAdapter>
CreateCk3_12002Adapter(std::string_view executable_sha256) noexcept;

} // namespace xar::game
