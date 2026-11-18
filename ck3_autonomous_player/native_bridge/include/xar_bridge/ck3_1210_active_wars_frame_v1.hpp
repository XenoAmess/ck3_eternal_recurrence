#pragma once
#include "xar_bridge/ck3_1210_active_wars_v1.hpp"
#include "xar_bridge/ck3_1210_personal_gold_frame_v1.hpp"
#include <string>
namespace xar::ck3_1210 {
inline constexpr char kActiveWarsIdentityStepV1[]="query-active-wars-identity-v1";
inline constexpr char kActiveWarsIdentityCapabilityV1[]="game.query.active-wars-identity.v1";
inline constexpr char kActiveWarsIdentitySchemaV1[]="ck3_1210_active_wars_identity_v1";
struct ActiveWarsMailboxContextV1 {
  ActiveWarsBindingsV1 bindings{};
  ActiveWarsObservationV1 observation{};
  bool application_main_observed=false;
  // Explicit bounded RAM seams, admitted only by an offline-fixture mailbox.
  // Production requests can never supply this context or memory addresses.
  ActiveWarsReadAccessV1 fixture_access{};
};
// Reuses the existing fixed Actor MQ slot; no new executor or Full reader.
// Only actual executing owner/TLS/sequence custody opens a local score gate.
bool ExecuteActiveWarsOnActorOwnerV1(PersonalGoldMailboxContextV1 &parent,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;
// Standalone partial DATA. Unknown collections are null; rich fields have
// explicit unavailable objects. This never serializes game::ActiveWarSnapshot.
std::string SerializeActiveWarsIdentityResultV1(const ActiveWarsMailboxContextV1 &);
std::string SerializeActiveWarsIdentityCommandResultV1(std::string_view request_id,
    const ActiveWarsMailboxContextV1 &);
}
