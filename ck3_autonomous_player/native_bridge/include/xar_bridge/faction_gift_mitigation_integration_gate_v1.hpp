#pragma once

#include "xar_bridge/faction_gift_mitigation_native_binder_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kFactionGiftMitigationIntegrationGateV1Key =
    "g2_faction_gift_mitigation_integration_gate_v1";
inline constexpr std::string_view
    kFactionGiftMitigationIntegrationGateV1ContractStage =
        "exact_build_private_read_only_preflight";
inline constexpr bool kFactionGiftMitigationIntegrationGatePublicV1 = false;

enum class FactionGiftMitigationIntegrationGateTerminalV1 : std::uint8_t {
  red = 0,
  ready = 1,
};

enum FactionGiftMitigationIntegrationGateRedV1 : std::uint32_t {
  faction_gift_gate_red_none = 0,
  faction_gift_gate_red_binder_unavailable = 1U << 0,
  faction_gift_gate_red_action_already_consumed = 1U << 1,
  faction_gift_gate_red_row_before_unavailable = 1U << 2,
  faction_gift_gate_red_first_capture_unavailable = 1U << 3,
  faction_gift_gate_red_second_capture_unavailable = 1U << 4,
  faction_gift_gate_red_row_after_unavailable = 1U << 5,
  faction_gift_gate_red_publication_drift = 1U << 6,
  faction_gift_gate_red_observation_drift = 1U << 7,
  faction_gift_gate_red_snapshot_binding = 1U << 8,
  faction_gift_gate_red_identity_binding = 1U << 9,
  faction_gift_gate_red_faction_binding = 1U << 10,
  faction_gift_gate_red_resource_binding = 1U << 11,
  faction_gift_gate_red_preview_binding = 1U << 12,
  faction_gift_gate_red_budget = 1U << 13,
  faction_gift_gate_red_forbidden_action_mutation = 1U << 14,
};

struct FactionGiftMitigationIntegrationGateResultV1 {
  FactionGiftMitigationIntegrationGateTerminalV1 terminal =
      FactionGiftMitigationIntegrationGateTerminalV1::red;
  std::uint32_t red_flags = faction_gift_gate_red_none;
  std::string first_red_reason;
  std::uint64_t row_published_generation = 0;
  std::uint64_t proof_epoch = 0;
  std::uint64_t snapshot_revision = 0;
  std::uint64_t native_snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::uint32_t player_character_id = 0;
  std::uint32_t source_faction_id = 0;
  std::uint32_t recipient_character_id = 0;
  std::int64_t player_gold_raw = 0;
  std::int64_t gift_gold_cost_raw = 0;
  std::int64_t minimum_gold_reserve_raw = 0;
  bool action_callbacks_invoked = false;
  bool ready_for_single_submit = false;
};

// Executes a read-only preflight over the already exact-build-bound native
// sources. It never calls validate_native, claim_idempotency_key or
// submit_native. READY authorizes only the later action path to attempt one
// submission; it is not an ACK and cannot be an outcome claim.
FactionGiftMitigationIntegrationGateTerminalV1
EvaluateFactionGiftMitigationIntegrationGateV1(
    FactionGiftMitigationNativeBinderStateV1 &binder,
    const game::FactionGiftMitigationRequestV1 &request,
    FactionGiftMitigationIntegrationGateResultV1 &result) noexcept;

std::string_view FactionGiftMitigationIntegrationGateRedKeyV1(
    std::uint32_t single_flag) noexcept;
std::string SerializeFactionGiftMitigationIntegrationGateResultV1(
    const FactionGiftMitigationIntegrationGateResultV1 &result);

} // namespace xar::ck3_11906
