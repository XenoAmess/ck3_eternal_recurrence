#pragma once

// External ROOT projection only. Not part of the canonical native build.
// Exact .3 submit/copy ABI evidence is recorded alongside this projection.
#include "xar_bridge/ck3_12002_commands.hpp"
#include "xar_bridge/ck3_12002_religion_conversion_terms.hpp"
#include "xar_bridge/ck3_12002_religion_conversion_reasons.hpp"
#include "xar_bridge/conversion_outcome12002_query.hpp"

#include <optional>
#include <string>

namespace xar::ck3_12002::religion_conversion::action12003 {

inline constexpr std::uint32_t kPaidConversionChannel = 0x0E;

struct Request {
  std::uint64_t expected_revision = 0;
  std::uint32_t target_rite_id = religion::kAbsentReference;
  std::int64_t max_piety_cost_raw = 0;
  std::string action_id;
};

struct Access {
  terms::Bindings terms;
  reasons::Bindings reasons;
  outcome::Bindings outcome;
  CommandBindings commands;
};

enum class SubmitStatus {
  not_submitted,
  already_target_noop,
  queued_verification_pending,
};

struct Submission {
  SubmitStatus status = SubmitStatus::not_submitted;
  std::string failure;
  std::string request_id;
  Request request;
  std::uint64_t native_revision = 0;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::uint32_t command_target_rite_id = religion::kAbsentReference;
  bool command_pay_piety = true;
  std::uint32_t command_channel = kPaidConversionChannel;
  bool native_submit_copy_called = false;
  terms::Terms paid_terms;
  reasons::Reasons native_reasons;
  outcome::Context before;
};

// ROOT invokes this inside the existing application-main mailbox callback.
// Published frame/revisions and epoch come from that owner, not JSON selectors.
Submission SubmitPaidPlayerConversion12003(
    const Access &, const game::Snapshot &published,
    std::uint64_t public_revision, std::uint64_t native_revision,
    std::uint64_t pump_epoch, std::string_view request_id,
    const Request &);

struct IndependentResult {
  std::string request_id;
  std::string action_id;
  SubmitStatus submit_status = SubmitStatus::not_submitted;
  bool verification_pending = true;
  bool after_actor_available = false;
  outcome::Context after;
  std::optional<bool> target_already_reached_before;
  std::optional<bool> actual_rite_changed;
  std::optional<bool> actual_target_reached_after;
  std::optional<bool> actual_target_faith_reached_after;
  bool request_associated_conversion_material_observed = false;
  std::optional<std::int64_t> quoted_base_piety_cost_raw;
  std::optional<std::int64_t> piety_net_delta_raw;
  std::optional<std::int64_t> gold_net_delta_raw;
  std::optional<std::int64_t> prestige_net_delta_raw;
  // Existing outcome does not isolate the base payment. The action request can
  // be associated with fresh independent conversion material without an hook.
  bool base_payment_observed = false;
  std::optional<std::int64_t> native_base_piety_charge_raw;
  bool native_execute_observed = false;
  bool conversion_causality_inferred = false;
};

IndependentResult ReadPlayerConversionResult12003(
    const Access &, const Submission &, std::uint64_t pump_epoch);

} // namespace xar::ck3_12002::religion_conversion::action12003
