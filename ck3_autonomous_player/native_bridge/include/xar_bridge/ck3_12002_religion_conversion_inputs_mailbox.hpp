#pragma once

#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12002_religion_conversion_gates.hpp"
#include "xar_bridge/ck3_12002_religion_conversion_ai_inputs.hpp"

namespace xar::ck3_12002 {
inline constexpr char kPlayerReligionConversionInputsPrivateStep12002[] =
    "query-player-religion-conversion-inputs-v1";
inline constexpr char kPlayerReligionConversionInputsDomainKey12002[] =
    "player_religion_conversion_inputs_v1";
inline constexpr char kPlayerReligionConversionInputsBackend12002[] =
    "ck3-1.20.0.2-native-player-religion-conversion-inputs-v1";

struct PlayerReligionConversionInputsMailboxContext12002 {
  QueryMailboxEnvelope envelope;
  religion::conversion_gates::Bindings gates_bindings;
  religion_conversion_ai_inputs::Bindings prediction_bindings;
  std::uint32_t target_rite_id = religion::kAbsentReference;
  religion::conversion_gates::Context conversion_gates;
  religion_conversion_ai_inputs::FulfillmentInput predicted_base_fulfillment;
  bool available = false;
  std::string unavailable_reason;
  bool completed = false;
  std::string failure;
};

bool IsPlayerReligionConversionInputsPrivateStep12002(std::string_view) noexcept;
bool ParsePlayerReligionConversionInputsRequest12002(std::string_view payload,
    std::uint32_t &target_rite_id, std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerReligionConversionInputsMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerReligionConversionInputsResult12002(
    const PlayerReligionConversionInputsMailboxContext12002 &, std::string_view request_id);
bool RunPlayerReligionConversionInputsMailbox12002(
    PlayerReligionConversionInputsMailboxContext12002 &, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept;
bool HandlePlayerReligionConversionInputsPrivate12002(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept;
} // namespace xar::ck3_12002
#endif
