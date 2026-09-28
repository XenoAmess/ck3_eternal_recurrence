#pragma once

#include "active_scheme_precondition_command_binders_v1_private.hpp"
#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/faction_gift_receivers_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kActiveSchemeSwayFormalSubmitPrefixV1 =
    "submit-active-scheme-sway-v1-private-";
inline constexpr std::string_view kActiveSchemeSwayFormalReceiptPrefixV1 =
    "receipt-active-scheme-sway-v1-private-";

enum class ActiveSchemeSwayFormalModeV1 : std::uint8_t { submit, receipt };

bool ParseActiveSchemeSwayFormalStepV1(std::string_view step,
                                       ActiveSchemeSwayFormalModeV1 &mode,
                                       std::uint32_t &target_id) noexcept;

struct ActiveSchemeSwayFormalPrivateCommandV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision = 0;
  std::uint32_t target_character_id = 0;
  ActiveSchemeSwayFormalModeV1 mode = ActiveSchemeSwayFormalModeV1::submit;
  std::string action_id{};
  std::uint64_t expected_capture_epoch = 0;
  std::uint64_t expected_container_generation = 0;
  std::int32_t expected_target_opinion_of_actor = 0;
  xar::bridge::ActiveSchemeSemanticActionV1PrivateAck prior_ack{};
  xar::bridge::ActiveSchemeSemanticActionV1PrivateAck ack{};
  xar::bridge::ActiveSchemeSemanticActionV1PrivateReceipt receipt{};
  xar::bridge::ActiveSchemeStateV1PrivateObservation observed{};
  GiftOpinionReceiverResultV1 target_opinion{};
  bool completed = false;
  bool frame_changed = false;
  std::uint32_t invocations = 0;
  std::string failure{};
};

bool ExecuteActiveSchemeSwayFormalPrivateCommandV1(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept;

std::string SerializeActiveSchemeSwayFormalPrivateCommandV1(
    const ActiveSchemeSwayFormalPrivateCommandV1 &command);

} // namespace xar::ck3_11906
