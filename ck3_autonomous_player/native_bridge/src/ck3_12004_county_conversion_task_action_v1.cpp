#include "xar_bridge/ck3_12004_county_conversion_task_action_v1.hpp"
#include "xar_bridge/ck3_12004_county_conversion_abi.hpp"

#include <algorithm>

#if defined(_MSC_VER)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace xar::ck3_12004::religion::county_conversion::action {
namespace {
TaskState State(const Observation &value,
                std::optional<std::uint16_t> scope_tag) {
  TaskState out;
  out.available = value.available;
  out.failure = CountyConversionFailureKey12004(value.failure);
  out.capture_epoch = value.capture_epoch;
  out.date_raw = value.date_raw;
  out.owner_character_id = value.owner_character_id;
  out.incumbent_character_id = value.incumbent_character_id;
  out.active_task_id = value.active_task_id;
  out.task_key = value.current_task_key;
  out.target_scope_tag = scope_tag;
  out.target_province_id = value.current_target_province_id;
  out.target_county_title_id = value.current_target_county_title_id;
  out.progress_kind = value.current_progress_kind;
  out.percentage_progress_raw = value.current_percentage_progress_raw;
  return out;
}
bool ReadState(const Access &access, std::uint64_t epoch, Observation &observation,
               TaskState &state, const void *&type) {
  // Task dispatch final input is evaluated once on the actual command below.
  // Candidate/value/current observations reuse the established native reader.
  auto environment = access.county;
  environment.task_dispatch_enabled = false;
  std::optional<std::uint16_t> scope_tag;
  const bool read = ReadCountyConversion12004(environment, epoch, observation);
  const bool material = read && ReadCountyConversionCommandMaterial12004(
      environment, observation, type, scope_tag);
  state = State(observation, scope_tag);
  if (!material) {
    state.available = false;
    if (read) state.failure = "current_task_command_material_unavailable";
  }
  return material;
}
bool SameFrame(const TaskState &state, const game::Snapshot &published,
               std::uint64_t epoch) noexcept {
  return state.available && state.capture_epoch == epoch &&
      state.owner_character_id == published.played_character_id &&
      state.date_raw == published.date_raw;
}
bool Final(const Environment &environment,
           const ChangeCouncilTaskCommand &command, bool &result) noexcept {
  if (!environment.final_task_validator ||
      (!environment.offline_fixture &&
       reinterpret_cast<std::uintptr_t>(environment.final_task_validator) !=
           environment.module_base + abi::kTaskDispatchValidatorRva)) return false;
#if defined(_MSC_VER)
  __try {
#endif
    result = environment.final_task_validator(&command, nullptr);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
  return true;
}
bool CommandBound(const Access &access) noexcept {
  if (!access.commands.enabled || !access.primary_vtable ||
      !access.secondary_vtable) return false;
  return access.county.offline_fixture ||
      (access.county.module_base &&
       access.primary_vtable == access.county.module_base + abi::kCommandPrimaryVtableRva &&
       access.secondary_vtable == access.county.module_base + abi::kCommandSecondaryVtableRva);
}
} // namespace

Access BindCountyConversionTaskActionImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  Access access{};
  access.county = BindCountyConversionImage12004(base, sha);
  if (!access.county.exact_build_admitted) return access;
  // Pure software DTO; actual .4 queue/manager, no old BindCommandImage admission.
  access.commands.enabled = true;
  access.commands.command_manager =
      reinterpret_cast<void *>(base + abi::kCommandManagerRva);
  access.commands.queue_owned_command =
      reinterpret_cast<ck3_12002::QueueOwnedCommand>(base + abi::kQueueOwnedCommandRva);
  access.primary_vtable = base + abi::kCommandPrimaryVtableRva;
  access.secondary_vtable = base + abi::kCommandSecondaryVtableRva;
  return access;
}
Submission SubmitCountyConversionTask12004(
    const Access &access, const game::Snapshot &published,
    std::uint64_t public_revision, std::uint64_t native_revision,
    std::uint64_t epoch, std::string_view request_id, const Request &request) {
  Submission out;
  out.request_id = request_id; out.request = request;
  out.native_revision = native_revision; out.capture_epoch = epoch;
  out.date_raw = static_cast<std::int32_t>(published.date_raw);
  out.played_character_id = published.played_character_id;
  if (!public_revision || request.expected_revision != public_revision ||
      !published.paused || !published.map_ready || !published.has_played_character ||
      !published.played_character_alive || request.expected_active_task_id < 0 ||
      request.expected_incumbent_character_id < 0 || request.province_id <= 0) {
    out.failure = "county_task_current_frame_or_request_unavailable";
    return out;
  }
  Observation observed;
  const void *conversion_type = nullptr;
  if (!ReadState(access, epoch, observed, out.before, conversion_type) ||
      !SameFrame(out.before, published, epoch)) {
    out.failure = "county_task_before_unavailable";
    return out;
  }
  if (out.before.active_task_id != request.expected_active_task_id ||
      out.before.incumbent_character_id != request.expected_incumbent_character_id) {
    out.failure = "county_task_current_identity_changed";
    return out;
  }
  if (out.before.task_key == kTaskKey && out.before.target_scope_tag == 8 &&
      out.before.target_province_id == request.province_id) {
    out.target_county_title_id = out.before.target_county_title_id;
    out.status = SubmitStatus::already_active_noop;
    return out;
  }
  // This is the native CEFBF0 replacement-confirmation branch, not a new
  // authorization restriction. Infinite existing tasks have no confirmation.
  if (out.before.progress_kind != 0 && !request.replace_existing_task) {
    out.failure = "county_task_replacement_required";
    return out;
  }
  const auto selected = std::find_if(observed.candidates.begin(), observed.candidates.end(),
      [&](const Candidate &row) { return row.province_id == request.province_id; });
  if (!observed.candidate_collection_complete || selected == observed.candidates.end() ||
      !selected->native_target_valid) {
    out.failure = "county_task_target_not_current_candidate";
    return out;
  }
  out.target_county_title_id = selected->county_title_id;
  if (!CommandBound(access)) {
    out.failure = "county_task_command_binding_unavailable";
    return out;
  }
  ChangeCouncilTaskCommand command;
  command.primary_vtable = access.primary_vtable;
  command.secondary_vtable = access.secondary_vtable;
  command.active_task_id = *out.before.active_task_id;
  command.task_type = conversion_type;
  command.scopes.incumbent_character_id = *out.before.incumbent_character_id;
  command.scopes.owner_character_id = out.before.owner_character_id;
  command.scopes.province_id = static_cast<std::int64_t>(request.province_id);
  bool can_dispatch = false;
  if (!Final(access.county, command, can_dispatch)) {
    out.failure = "county_task_native_final_unavailable";
    return out;
  }
  out.native_final_can_dispatch = can_dispatch;
  if (!can_dispatch) {
    out.failure = "county_task_native_final_denied";
    return out;
  }
  out.native_submit_copy_called = true;
  const auto queued = ck3_12002::SubmitCommandCopy(access.commands, &command, kCommandChannel);
  if (queued != ck3_12002::CommandSubmitResult::submitted) {
    out.failure = queued == ck3_12002::CommandSubmitResult::rejected
        ? "county_task_native_queue_rejected" : "county_task_command_copy_unavailable";
    return out;
  }
  out.status = SubmitStatus::queued_verification_pending;
  return out;
}

IndependentResult ReadCountyConversionTaskResult12004(
    const Access &access, const Submission &submitted, std::uint64_t epoch) {
  IndependentResult out;
  out.request_id = submitted.request_id; out.action_id = submitted.request.action_id;
  out.submit_status = submitted.status;
  out.verification_pending = submitted.status == SubmitStatus::queued_verification_pending;
  Observation observed;
  const void *conversion_type = nullptr;
  if (!ReadState(access, epoch, observed, out.after, conversion_type) ||
      out.after.owner_character_id != submitted.played_character_id) return out;
  if (out.after.active_task_id && submitted.before.active_task_id)
    out.actual_task_id_unchanged = out.after.active_task_id == submitted.before.active_task_id;
  out.actual_task_assignment_matches = out.after.active_task_id.has_value() &&
      out.after.incumbent_character_id == submitted.request.expected_incumbent_character_id &&
      out.after.task_key == kTaskKey && out.after.target_scope_tag == 8 &&
      out.after.target_province_id == submitted.request.province_id &&
      out.after.target_county_title_id == submitted.target_county_title_id;
  out.task_assignment_material_observed =
      submitted.status == SubmitStatus::queued_verification_pending &&
      epoch > submitted.capture_epoch &&
      out.actual_task_assignment_matches.value_or(false);
  if (out.task_assignment_material_observed) out.verification_pending = false;
  // Assignment is one production primitive. No county Faith/Rite completion
  // or native Execute causality is inferred from this independent readback.
  return out;
}

} // namespace xar::ck3_12004::religion::county_conversion::action
