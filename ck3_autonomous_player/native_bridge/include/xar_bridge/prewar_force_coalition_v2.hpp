#pragma once

#include "xar_bridge/prewar_force_coalition12004.hpp"
#include "xar_bridge/prewar_selected_declaration12004.hpp"
#include "xar_bridge/prewar_owner_inventory12004.hpp"
#include "xar_bridge/prewar_levy_inventory12004.hpp"
#include "xar_bridge/prewar_hired_inventory12004.hpp"
#include "xar_bridge/prewar_potential_supporters12004.hpp"
#include "xar_bridge/prewar_additional_supporters12004.hpp"
#include "xar_bridge/prewar_force_bounds12004.hpp"
#include "xar_bridge/prewar_commandable_raised12004.hpp"
#include "xar_bridge/ck3_12004_holy_war_defender_join_inputs.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_12004 {

inline constexpr char kPrewarForceCoalitionV2Step12004[] =
    "query-prewar-force-coalition-coverage-v2";
inline constexpr char kPrewarForceCoalitionV2Domain12004[] =
    "prewar_force_coalition_coverage_v2";

// All bundles are constructed for the admitted actual4 image in their final
// owning mailbox addresses. No legacy central adapter DTO layout is extended.
struct PrewarForceCoalitionV2Bindings12004 {
  CoreBindings core;
  ck3_12002::ArmyBindings armies;
  ck3_12002::MilitaryBindings military;
  ck3_12003::PlayerArmyReserveBindingsV1 reserve;
  ck3_12002::family_obligations_alliance::Bindings alliance;
  ck3_12002::WarEntryNativeEnvironmentV1 war_entry;
  ck3_12002::DeclarationsBindings declarations;
  religion::ContextBindings faith;
  religion::holy_war_defender_join::Bindings holy_join;
  ck3_12003::mercenary::CandidateBindings mercenary;
  ck3_12003::religion::holy_order::Bindings holy_order;
  PrewarOwnerInventoryBindings12004 owner_inventory;
  PrewarLevyInventoryBindings12004 levy_inventory;
  PrewarPotentialSupportersBindings12004 potential;
  PrewarAdditionalSupportersBindings12004 additional;
};

struct PrewarForceCoalitionV2Participant12004 {
  std::int32_t character_id = -1;
  std::vector<std::string> sources;
  bool operator==(const PrewarForceCoalitionV2Participant12004 &) const = default;
};

struct PrewarForceCoalitionV2Owner12004 {
  PrewarOwnerInventory12004 inventory;
  PrewarLevyInventorySnapshot12004 levy;
  PrewarForceOwnerBounds12004 bounds;
  bool operator==(const PrewarForceCoalitionV2Owner12004 &) const = default;
};

struct PrewarForceMobilization12004 {
  bool available = false;
  std::string unavailable_reason = "native_mobilization_qualification_unavailable";
  std::optional<bool> native_raise_legal;
  std::optional<std::int32_t> default_raise_province_id;
  std::optional<std::int64_t> physical_inventory_lower_soldiers;
  std::optional<std::int32_t> native_unraised_stock_soldiers;
  bool native_unraised_stock_ready = false;
  std::optional<std::int64_t> unraised_lower_soldiers;
  bool unraised_lower_ready = false;
  // Already-raised armies are not credited without their independent current
  // control/physical identity proof. An unobserved source stays nullable.
  std::optional<std::int64_t> raised_commandable_lower_soldiers;
  bool raised_lower_ready = false;
  std::optional<std::int64_t> executable_lower_soldiers;
  bool executable_lower_ready = false;
  bool operator==(const PrewarForceMobilization12004 &) const = default;
};

struct PrewarForceCoalitionV2Sample12004 {
  game::DeclarableWarSnapshot selected;
  std::uint64_t native_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t actor_character_id = -1;
  // Generic war-entry identity is an optional diagnostic. It does not define
  // selected CB roles and is not a prerequisite or a second query here.
  std::optional<std::int32_t> generic_effective_target_character_id;
  PrewarSelectedDeclarationObservation12004 final_cb_roles;
  PrewarPotentialSupporters12004 potential;
  PrewarAdditionalSupportersSnapshot12004 additional;
  // The existing child lacks equality; its full deterministic serialization
  // retains every ordered row, raw flag, role, identity and diagnostic failure.
  std::string holy_join_complete_observation;
  bool holy_joiners_complete = false;
  bool current_allies_complete = false;
  bool additional_supporters_complete = false;
  bool selected_cb_initial_complete = false;
  bool potential_enemy_collection_complete = false;
  std::vector<PrewarForceCoalitionV2Participant12004> enemy_participants;
  PrewarHiredInventory12004 hired;
  std::vector<PrewarForceCoalitionV2Owner12004> owners;
  PrewarForceMobilization12004 native_mobilization_qualification;
  PrewarCommandableRaisedObservation12004 commandable_raised;
  std::optional<std::int64_t> actor_lower_soldiers;
  std::optional<std::int64_t> enemy_upper_soldiers;
  bool enemy_force_coverage_complete = false;
  bool enemy_upper_aggregate_overflow = false;
  bool complete_initial_participants_ready = false;
  bool coverage_available = false;
  std::vector<std::string> missing_required_domains;
  bool sampled = false;
  bool operator==(const PrewarForceCoalitionV2Sample12004 &) const = default;
};

// Each complete sample creates a fresh selected declaration context. All
// dependent providers run synchronously inside its consumer callback and copy
// their pointer-free DTOs before native temporary buffers are destroyed. Caller
// compares two whole samples and seals the same actual main-thread ticket.
bool ReadPrewarForceCoalitionV2Sample12004(
    const PrewarForceCoalitionV2Bindings12004 &bindings,
    const PrewarForceCoalitionRequest12004 &request,
    ck3_12002::QueryMailboxEnvelope &envelope,
    const ck3_12002::MilitaryWorldAccess &world,
    PrewarForceCoalitionV2Sample12004 &output, std::string &failure) noexcept;

// Bare schema2 evidence, never a native automatic-declaration authorization.
// Margin and ordinary action readiness belong to the explicit policy consumer.
std::string SerializePrewarForceCoalitionV2_12004(
    const PrewarForceCoalitionV2Sample12004 &sample,
    const PrewarForceCoalitionRequest12004 &request,
    std::uint64_t capture_epoch, std::uint64_t ticket_sequence,
    std::uint64_t query_sequence, std::int32_t date_raw,
    std::int32_t actor_character_id);

} // namespace xar::ck3_12004
