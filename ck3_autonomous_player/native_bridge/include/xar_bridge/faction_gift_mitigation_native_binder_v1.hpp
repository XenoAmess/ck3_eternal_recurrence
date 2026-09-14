#pragma once

#include "xar_bridge/faction_gift_mitigation_source_action_adapter_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kFactionGiftMitigationNativeBinderV1Key =
    "g2_faction_gift_mitigation_native_binder_v1";
inline constexpr bool kFactionGiftMitigationNativeBinderPublicV1 = false;
inline constexpr std::size_t kFactionGiftMitigationNativeAnchorCountV1 = 9;

struct FactionGiftMitigationExpectedAnchorV1 {
  std::string_view name;
  std::uintptr_t rva = 0;
  std::string_view span_sha256;
};

inline constexpr std::array<FactionGiftMitigationExpectedAnchorV1,
                            kFactionGiftMitigationNativeAnchorCountV1>
    kFactionGiftMitigationExpectedAnchorsV1{{
        {"get_character_interaction_database", 0x0831890,
         "954B26681465C4A72A0CC660025958E61ED1A367257F2167437401BF6CF532C2"},
        {"pure_stable_key_hash", 0x3B8B000,
         "E42410BF40CBE818FED8B771988E102AE129BCE08CD7F975EB7A1EB2E5CD70DD"},
        {"loaded_character_interaction_lookup_by_hash", 0x0997930,
         "D2CF41A720A93596E4E9B545B5B994C4068EF881E2BBCF28E6A12C29C800B060"},
        {"construct_two_role_character_interaction_context", 0x2C3EE50,
         "A9CDB9706153581B01B24ADAD38204703CC4AF0CBA2F381EB4E49C064E9CE83A"},
        {"finalize_character_interaction_context", 0x2C40B20,
         "1A6393A2BF0D6B5AEA4BB71CA261B63147336CCFBE42F5BA9EA7A09AB5472661"},
        {"validate_character_interaction_context", 0x2C43F00,
         "3B9A75EC79B4C93DE7C1E3F9D45ADA2518048611EFCF7C0475F243C93086ED54"},
        {"generic_ui_validate_and_send", 0x0FE5190,
         "E9395FFF0F765D7FC29B6EFC914F3B06E1081C9E684BFC477ED9ABC8C0BEA217"},
        {"construct_send_character_interaction_command", 0x26B3220,
         "9FF7B4F35955FD90765E33428CCD92EAFE913A2C46B22D05BC910C8F465E8FB0"},
        {"submit_gameplay_command", 0x0973E00,
         "DE559EA4ADE7CC7BA5AD44612C15B28FD66B59FC69F4B1BF6C52431E750537F8"},
    }};

struct FactionGiftMitigationObservedAnchorV1 {
  std::uintptr_t rva = 0;
  std::uintptr_t resolved_address = 0;
  std::string span_sha256;
};

struct FactionGiftMitigationNativeBinderEnvironmentV1 {
  bool exact_build_admitted = false;
  std::string executable_sha256;
  std::uintptr_t module_base = 0;
  std::array<FactionGiftMitigationObservedAnchorV1,
             kFactionGiftMitigationNativeAnchorCountV1>
      anchors{};
};

struct FactionGiftMitigationNativeFrameObservationV1 {
  bool available = false;
  FactionGiftMitigationSourceFrameV1 frame;
  bool player_resources_query_complete = false;
  std::int64_t player_gold_raw = 0;
  std::uint32_t player_gold_scale = 0;
};

struct FactionGiftMitigationNativeFactionObservationV1 {
  bool available = false;
  FactionGiftMitigationSourceFrameV1 frame;
  bool query_complete = false;
  std::uint32_t queried_source_faction_id = 0;
  bool source_faction_present = false;
  bool source_faction_at_war = false;
  bool metrics_available = false;
  std::int64_t power_raw = 0;
  std::int64_t discontent_raw = 0;
  std::uint32_t metric_scale = 0;
};

struct FactionGiftMitigationNativeRecipientObservationV1 {
  bool available = false;
  FactionGiftMitigationSourceFrameV1 frame;
  bool identity_resolved = false;
  std::uint32_t recipient_character_id = 0;
  bool alive = false;
  bool is_ai = false;
  bool is_direct_landed_vassal = false;
  bool opinion_query_complete = false;
  std::int32_t opinion_of_player = 0;
  bool gift_opinion_present = false;
  std::optional<std::int32_t> gift_opinion_modifier_value;
};

struct FactionGiftMitigationNativePreviewObservationV1 {
  bool available = false;
  FactionGiftMitigationSourceFrameV1 frame;
  std::uint32_t player_character_id = 0;
  std::uint32_t recipient_character_id = 0;
  game::FactionGiftPreviewV1 preview;
};

using ReadFactionGiftMitigationNativeFrameV1 = bool (*)(
    void *context,
    const FactionGiftMitigationSourceFrameV1 &required_row_frame,
    FactionGiftMitigationNativeFrameObservationV1 &output) noexcept;
using ReadFactionGiftMitigationNativeFactionV1 = bool (*)(
    void *context,
    const FactionGiftMitigationSourceFrameV1 &required_native_frame,
    std::uint32_t source_faction_id,
    FactionGiftMitigationNativeFactionObservationV1 &output) noexcept;
using ReadFactionGiftMitigationNativeRecipientV1 = bool (*)(
    void *context,
    const FactionGiftMitigationSourceFrameV1 &required_native_frame,
    std::uint32_t recipient_character_id,
    FactionGiftMitigationNativeRecipientObservationV1 &output) noexcept;
using ReadFactionGiftMitigationNativePreviewV1 = bool (*)(
    void *context,
    const FactionGiftMitigationSourceFrameV1 &required_native_frame,
    std::uint32_t player_character_id,
    std::uint32_t recipient_character_id,
    FactionGiftMitigationNativePreviewObservationV1 &output) noexcept;

// These two callbacks are the private reuse point for CK3's existing generic
// character-interaction context/validator/send chain. The submit callback must
// rebuild and validate the exact actor/recipient/key/hash context before one
// synchronous queue-clone attempt; true remains queue ACK only.
using ValidateFactionGiftThroughGenericInteractionV1 = bool (*)(
    void *context, std::uint32_t player_character_id,
    std::uint32_t recipient_character_id, std::string_view definition_key,
    std::uint64_t expected_definition_stable_hash, bool &valid,
    std::string &native_reason_key) noexcept;
using SubmitFactionGiftThroughGenericInteractionV1 = bool (*)(
    void *context, std::uint32_t player_character_id,
    std::uint32_t recipient_character_id, std::string_view definition_key,
    std::uint64_t expected_definition_stable_hash) noexcept;

struct FactionGiftMitigationNativeUpstreamV1 {
  void *row_context = nullptr;
  ReadFactionTargetingRowsForGiftMitigationV1 read_targeting_rows = nullptr;
  void *native_context = nullptr;
  ReadFactionGiftMitigationNativeFrameV1 read_frame = nullptr;
  ReadFactionGiftMitigationNativeFactionV1 read_faction = nullptr;
  ReadFactionGiftMitigationNativeRecipientV1 read_recipient = nullptr;
  ReadFactionGiftMitigationNativePreviewV1 read_preview = nullptr;
  ValidateFactionGiftThroughGenericInteractionV1 validate_gift = nullptr;
  ClaimFactionGiftMitigationIdempotencyKeyV1 claim_idempotency_key = nullptr;
  SubmitFactionGiftThroughGenericInteractionV1 submit_gift = nullptr;
};

struct FactionGiftMitigationNativeBinderStateV1 {
  bool bound = false;
  std::uintptr_t module_base = 0;
  FactionGiftMitigationNativeUpstreamV1 upstream;
  bool preview_binding_available = false;
  std::uint32_t preview_player_character_id = 0;
  std::uint32_t preview_recipient_character_id = 0;
  std::uint64_t preview_definition_stable_hash = 0;
  bool idempotency_claim_attempted = false;
  bool submit_attempted = false;
};

// Successful binding proves the executable identity plus every frozen RVA and
// span hash. It does not install hooks, publish schema, or touch CK3 state.
bool BindFactionGiftMitigationNativeCallbacksV1(
    FactionGiftMitigationNativeBinderStateV1 &state,
    const FactionGiftMitigationNativeBinderEnvironmentV1 &environment,
    const FactionGiftMitigationNativeUpstreamV1 &upstream) noexcept;

FactionGiftMitigationSourceActionAccessV1
MakeFactionGiftMitigationNativeSourceActionAccessV1(
    FactionGiftMitigationNativeBinderStateV1 &state) noexcept;

FactionGiftMitigationNativeEnvironmentV1
MakeFactionGiftMitigationCertifiedActionEnvironmentV1(
    const FactionGiftMitigationNativeBinderStateV1 &state) noexcept;

} // namespace xar::ck3_11906
