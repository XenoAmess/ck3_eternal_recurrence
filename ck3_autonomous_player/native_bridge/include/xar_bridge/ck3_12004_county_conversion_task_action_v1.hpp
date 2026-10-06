#pragma once

#include "xar_bridge/ck3_12004_county_conversion.hpp"
#include "xar_bridge/ck3_12003_county_conversion_task_action_v1.hpp"

namespace xar::ck3_12004::religion::county_conversion::action {

// Existing county command/request/result DTOs. The command's native image
// vtables and queue are supplied only by the independently mapped .4 binder.
namespace dto = ck3_12003::religion::county_conversion::action;
using TaskScopes = dto::TaskScopes;
using ChangeCouncilTaskCommand = dto::ChangeCouncilTaskCommand;
using Request = dto::Request;
using TaskState = dto::TaskState;
using SubmitStatus = dto::SubmitStatus;
using Submission = dto::Submission;
using IndependentResult = dto::IndependentResult;
inline constexpr std::uint32_t kCommandChannel = dto::kCommandChannel;

struct Access {
  Environment county{};
  ck3_12002::CommandBindings commands{};
  std::uintptr_t primary_vtable = 0;
  std::uintptr_t secondary_vtable = 0;
};
Access BindCountyConversionTaskActionImage12004(std::uintptr_t module_base,
    std::string_view executable_sha256) noexcept;

Submission SubmitCountyConversionTask12004(const Access &,
    const game::Snapshot &published, std::uint64_t public_revision,
    std::uint64_t native_revision, std::uint64_t pump_epoch,
    std::string_view request_id, const Request &);
IndependentResult ReadCountyConversionTaskResult12004(const Access &,
    const Submission &, std::uint64_t pump_epoch);

// These existing software encoders carry no native binding or core call.
using dto::SerializeCountyConversionTaskSubmission12003;
using dto::SerializeCountyConversionTaskIndependentResult12003;

} // namespace xar::ck3_12004::religion::county_conversion::action
