#pragma once

#include "xar_bridge/faction_gift_mitigation_action_v1.hpp"
#include "xar_bridge/faction_targeting_row_probe_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view
    kFactionGiftMitigationSourceActionAdapterV1PrivateKey =
        "g2_faction_gift_mitigation_source_action_adapter_v1";
inline constexpr bool kFactionGiftMitigationSourceActionAdapterPublicV1 =
    false;

// Details from the resource/opinion/interaction source are frame-bound to the
// targeting-row probe. The row generation is retained so an adapter cannot
// combine a valid row from one publication with details from another.
struct FactionGiftMitigationSourceFrameV1 {
  bool paused = false;
  std::uint64_t row_published_generation = 0;
  std::uint64_t proof_epoch = 0;
  std::uint64_t snapshot_revision = 0;
  std::uint64_t native_snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::uint32_t player_character_id = 0;

  friend bool operator==(const FactionGiftMitigationSourceFrameV1 &,
                         const FactionGiftMitigationSourceFrameV1 &) =
      default;
};

struct FactionGiftMitigationSourceDetailsV1 {
  bool available = false;
  FactionGiftMitigationSourceFrameV1 frame;

  bool player_resources_query_complete = false;
  std::int64_t player_gold_raw = 0;
  std::uint32_t player_gold_scale = 0;

  bool source_faction_query_complete = false;
  std::uint32_t queried_source_faction_id = 0;
  bool source_faction_present = false;
  bool source_faction_at_war = false;
  bool source_faction_metrics_available = false;
  std::int64_t source_faction_power_raw = 0;
  std::int64_t source_faction_discontent_raw = 0;
  std::uint32_t source_faction_metric_scale = 0;

  bool recipient_identity_resolved = false;
  std::uint32_t recipient_character_id = 0;
  bool recipient_alive = false;
  bool recipient_is_ai = false;
  bool recipient_is_direct_landed_vassal = false;
  bool recipient_opinion_query_complete = false;
  std::int32_t recipient_opinion_of_player = 0;
  bool gift_opinion_present = false;
  std::optional<std::int32_t> gift_opinion_modifier_value;

  game::FactionGiftPreviewV1 gift_preview;
};

using ReadFactionTargetingRowsForGiftMitigationV1 = bool (*)(
    void *context, bridge::FactionTargetingRowProbeResultV1 &output) noexcept;

// The adapter passes the exact row frame and full-generation source/recipient
// identities into this query. Implementations must return details bound to
// that frame rather than silently falling forward to a newer snapshot.
using ReadFactionGiftMitigationSourceDetailsV1 = bool (*)(
    void *context,
    const FactionGiftMitigationSourceFrameV1 &required_frame,
    std::uint32_t source_faction_id, std::uint32_t recipient_character_id,
    FactionGiftMitigationSourceDetailsV1 &output) noexcept;

struct FactionGiftMitigationSourceActionAccessV1 {
  void *context = nullptr;
  ReadFactionTargetingRowsForGiftMitigationV1 read_targeting_rows = nullptr;
  ReadFactionGiftMitigationSourceDetailsV1 read_details = nullptr;
  ValidateFactionGiftMitigationCommandV1 validate_native = nullptr;
  ClaimFactionGiftMitigationIdempotencyKeyV1 claim_idempotency_key = nullptr;
  SubmitFactionGiftMitigationCommandV1 submit_native = nullptr;
};

// This is the only mapping boundary from row/details sources into the action
// observation. It performs no CK3 calls itself and is suitable for standalone
// fixtures. `false` means no coherent frame could be assembled.
bool CaptureFactionGiftMitigationObservationFromSourcesV1(
    const FactionGiftMitigationSourceActionAccessV1 &sources,
    std::uint32_t source_faction_id, std::uint32_t recipient_character_id,
    game::FactionGiftMitigationObservationV1 &output) noexcept;

game::FactionGiftMitigationAckStatusV1
ExecuteFactionGiftMitigationSourceActionAdapterV1(
    const FactionGiftMitigationNativeEnvironmentV1 &environment,
    const FactionGiftMitigationSourceActionAccessV1 &sources,
    const game::FactionGiftMitigationRequestV1 &request,
    game::FactionGiftMitigationAckV1 &ack) noexcept;

game::FactionGiftMitigationReceiptStatusV1
VerifyFactionGiftMitigationSourceActionReceiptV1(
    const FactionGiftMitigationSourceActionAccessV1 &sources,
    const game::FactionGiftMitigationAckV1 &ack,
    game::FactionGiftMitigationReceiptV1 &receipt) noexcept;

} // namespace xar::ck3_11906
