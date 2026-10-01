#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12002_sway_state.hpp"
#include "xar_bridge/ck3_12002_sway_command.hpp"
#include <optional>
#include <string>

namespace xar::ck3_12002 {
struct ActiveSwayState12002 {
  bool may_have_submitted = false;
  std::optional<bridge::ActiveSchemeSemanticActionV1PrivateAck> pending_ack{};
};
struct ActiveSwayMailboxContext12002 {
  QueryMailboxEnvelope envelope{};
  SwayStateBindings12002 source{};
  SwayCommandBindingsV1 commands{};
  std::uint32_t target = 0;
  bool formal = false;
  bool receipt_mode = false;
  std::string action_id{};
  std::uint64_t expected_capture_epoch = 0;
  std::uint64_t expected_container_generation = 0;
  std::int32_t expected_opinion = 0;
  bridge::ActiveSchemeSemanticActionV1PrivateAck prior_ack{}, ack{};
  bridge::ActiveSchemeSemanticActionV1PrivateReceipt receipt{};
  bridge::ActiveSchemeStateV1PrivateObservation active{};
  SwayCommandTermsV1 terms{};
  std::int32_t opinion = 0;
  bool matching = false;
  bool completed = false;
  std::string failure{};
};
bool ExecuteActiveSwayMailbox12002(void *,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializeActiveSwayRead12002(const ActiveSwayMailboxContext12002 &);
std::string SerializeActiveSwayFormal12002(const ActiveSwayMailboxContext12002 &);
std::string SerializeActiveSwayEnvelope12002(const ActiveSwayMailboxContext12002 &,
    std::string_view step, std::string_view request_id);
bool HandleActiveSwayPrivate12002(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, ActiveSwayState12002 &state,
    std::string &serialized, std::string &failure) noexcept;
} // namespace xar::ck3_12002
