#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12002_war_entry.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/prewar_force_allies12004.hpp"
#include "xar_bridge/prewar_force_military12004.hpp"

#include <cstdint>
#include <string>
#include <vector>

namespace xar::ck3_12004 {

inline constexpr char kPrewarForceCoalitionStep12004[] =
    "query-prewar-force-coalition-coverage-v1";
inline constexpr char kPrewarForceCoalitionDomain12004[] =
    "prewar_force_coalition_coverage";

struct PrewarForceCoalitionRequest12004 {
  std::uint64_t expected_native_revision = 0;
  std::uint64_t expected_public_revision = 0;
  std::string declaration_id;
  game::DeclarableWarSnapshot selected;
};

// All native bindings are independently constructed for actual .4. Their
// command bundle and world callback contexts remain owned by the mailbox
// object until its ticket is terminal and reclaimed.
struct PrewarForceCoalitionBindings12004 {
  CoreBindings core;
  ck3_12002::ArmyBindings armies;
  ck3_12002::MilitaryBindings military;
  ck3_12003::PlayerArmyReserveBindingsV1 reserve;
  ck3_12002::family_obligations_alliance::Bindings alliance;
  ck3_12002::WarEntryNativeEnvironmentV1 war_entry;
};

struct PrewarForceCoalitionOwnerAllies12004 {
  bool available = false;
  PrewarOwnerAllies12004 observed;
  std::string failure;
  bool operator==(const PrewarForceCoalitionOwnerAllies12004 &) const = default;
};

struct PrewarForceCoalitionSample12004 {
  game::DeclarableWarSnapshot selected;
  // This is the existing generic war-entry resolver's effective target.
  // It is NOT an attestation of finalized selected-CB primary-defender roles.
  std::int32_t generic_effective_target_character_id = -1;
  game::WarEntryAssessmentsV1 assessment;
  std::vector<PrewarForceCoalitionOwnerAllies12004> current_allies;
  std::vector<std::int32_t> owner_character_ids;
  PrewarForceMilitarySnapshot12004 military;
  bool sampled = false;
  bool operator==(const PrewarForceCoalitionSample12004 &) const = default;
};

// One whole-domain sample. Requires the genuine executing QueryMailboxEnvelope
// and actual4 adapter. The mailbox executor calls this twice in the same pump
// epoch, compares the complete DTOs, and finishes its full-snapshot frame gate.
// No existing query cache or manually supplied effective target is consumed.
bool ReadPrewarForceCoalitionSample12004(
    const PrewarForceCoalitionBindings12004 &bindings,
    const PrewarForceCoalitionRequest12004 &request,
    ck3_12002::QueryMailboxEnvelope &envelope,
    const ck3_12002::MilitaryWorldAccess &world,
    PrewarForceCoalitionSample12004 &output, std::string &failure) noexcept;

// Bare strict-contract DTO, only for a completed, stable, fresh mailbox sample.
// The mailbox supplies these identity values from its actual ticket/stamp.
// Enemy all-source military, finalized CB participants and automatic declaration
// deliberately remain null/false. Army maxima are observed roster capacities.
std::string SerializePrewarForceCoalition12004(
    const PrewarForceCoalitionSample12004 &sample,
    const PrewarForceCoalitionRequest12004 &request,
    std::uint64_t capture_epoch, std::uint64_t ticket_sequence,
    std::uint64_t query_sequence, std::int32_t date_raw,
    std::int32_t actor_character_id);

} // namespace xar::ck3_12004
