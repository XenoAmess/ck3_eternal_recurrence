#include "activity_stage1_option_read_private_transport_v1.hpp"

#include <windows.h>

#include <charconv>
#include <cstring>
#include <limits>

namespace xar::ck3_11906 {
namespace {

struct CaptureContext {
  ActivityStage1OptionReadPrivateQueryV1 *query = nullptr;
  std::uintptr_t module_base = 0;
  DWORD owner_thread_id = 0;
  std::uintptr_t game_state = 0;
};

bool ReadMemory(void *, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  SIZE_T read = 0;
  return address != 0 && output != nullptr && size != 0 &&
         ReadProcessMemory(GetCurrentProcess(),
                           reinterpret_cast<const void *>(address), output,
                           size, &read) != 0 && read == size;
}

bool ReadFrame(void *opaque,
               bridge::ActivityPlannerDiagFrameV1 &output) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  game::Snapshot snapshot{};
  if (GetCurrentThreadId() != context.owner_thread_id ||
      !ReadSnapshot(context.query->bindings, snapshot))
    return false;
  output = {context.query->expected_revision,
            snapshot.date_raw,
            snapshot.played_character_id,
            true,
            snapshot.paused,
            snapshot.map_ready,
            snapshot.has_played_character && snapshot.played_character_alive};
  return true;
}

std::uintptr_t CastIdler(void *opaque, std::uintptr_t source,
                         std::uintptr_t source_type,
                         std::uintptr_t target_type) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  if (context.module_base == 0 || source == 0 ||
      GetCurrentThreadId() != context.owner_thread_id)
    return 0;
  using NativeCast = void *(*)(void *, std::int32_t, void *, void *, std::int32_t);
  const auto cast = reinterpret_cast<NativeCast>(context.module_base +
                                                 0x3E631F4);
  void *result = nullptr;
  __try {
    result = cast(reinterpret_cast<void *>(source), 0,
                  reinterpret_cast<void *>(source_type),
                  reinterpret_cast<void *>(target_type), 0);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    result = nullptr;
  }
  return reinterpret_cast<std::uintptr_t>(result);
}

bool InvokeVisibility(void *, std::uintptr_t planner,
                      std::uintptr_t entry, bool &output) noexcept {
  if (planner == 0 || entry == 0) return false;
  const auto visible = reinterpret_cast<bool (*)(void *)>(entry);
  __try {
    output = visible(reinterpret_cast<void *>(planner));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

bool ResolveKey(void *opaque, std::int32_t identifier,
                std::array<char, 96> &output,
                std::uint16_t &output_size) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  const auto &bindings = context.query->bindings;
  if (GetCurrentThreadId() != context.owner_thread_id ||
      bindings.get_script_identifier_table == nullptr ||
      bindings.lookup_script_identifier_id == nullptr ||
      bindings.resolve_script_identifier_name == nullptr ||
      bindings.script_identifier_name_fallback == nullptr)
    return false;
  struct NativeStringView {
    const char *data = nullptr;
    std::int32_t size = 0;
    std::uint8_t owned = 0;
    std::array<std::byte, 3> padding{};
  };
  static_assert(sizeof(NativeStringView) == 16);
  output = {};
  output_size = 0;
  __try {
    void *const table = bindings.get_script_identifier_table();
    if (table == nullptr) return false;
    const std::string *const name =
        bindings.resolve_script_identifier_name(table, identifier);
    if (name == nullptr ||
        name == bindings.script_identifier_name_fallback ||
        name->empty() || name->size() >= output.size())
      return false;
    const NativeStringView view{name->data(),
                                static_cast<std::int32_t>(name->size())};
    std::int32_t reverse_id = 0;
    if (bindings.lookup_script_identifier_id(table, &reverse_id, &view) ==
            nullptr ||
        reverse_id != identifier)
      return false;
    std::memcpy(output.data(), name->data(), name->size());
    output_size = static_cast<std::uint16_t>(name->size());
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = {};
    output_size = 0;
    return false;
  }
}

bool SelectedOption(void *opaque, std::uintptr_t planner,
                    std::uintptr_t &output) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id || planner == 0 ||
      context.module_base == 0)
    return false;
  using Getter = void *(*)(void *);
  const auto getter = reinterpret_cast<Getter>(context.module_base + 0x10AEAE0);
  __try {
    output = reinterpret_cast<std::uintptr_t>(
        getter(reinterpret_cast<void *>(planner)));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

bool OptionPredicate(void *opaque, std::uintptr_t entry,
                     std::uintptr_t candidate, std::uintptr_t actor,
                     std::uintptr_t selected, bool &output) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id || entry == 0 ||
      candidate == 0 || actor == 0)
    return false;
  using Predicate = bool (*)(void *, void *, void *);
  const auto predicate = reinterpret_cast<Predicate>(entry);
  __try {
    output = predicate(reinterpret_cast<void *>(candidate),
                       reinterpret_cast<void *>(actor),
                       reinterpret_cast<void *>(selected));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

bool CanProgress(void *opaque, std::uintptr_t planner, bool &output) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id || planner == 0 ||
      context.module_base == 0)
    return false;
  // Stage 1 does not consume the optional failure-display pointer.
  using Predicate = bool (*)(void *, void *);
  const auto predicate =
      reinterpret_cast<Predicate>(context.module_base + 0x10B0DA0);
  __try {
    output = predicate(reinterpret_cast<void *>(planner), nullptr);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_LOCATION_READ_PRIVATE_V1)
bool ResolveActivityProvince(void *opaque, std::int32_t id,
                             std::uintptr_t &output) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  output = 0;
  if (GetCurrentThreadId() != context.owner_thread_id ||
      context.game_state == 0 || id < 1)
    return false;
  std::uintptr_t game_data = 0, provinces = 0, province = 0;
  std::int32_t count = 0, reverse_id = 0;
  if (!ReadMemory(nullptr, context.game_state + 0xA0, &game_data,
                  sizeof(game_data)) || game_data == 0 ||
      !ReadMemory(nullptr, game_data + 0x140, &provinces,
                  sizeof(provinces)) || provinces == 0 ||
      !ReadMemory(nullptr, game_data + 0x14C, &count, sizeof(count)) ||
      id >= count ||
      !ReadMemory(nullptr, provinces + static_cast<std::size_t>(id) * 8,
                  &province, sizeof(province)) || province == 0 ||
      !ReadMemory(nullptr, province + 0x10, &reverse_id,
                  sizeof(reverse_id)) || reverse_id != id)
    return false;
  output = province;
  return true;
}

bool CanSelectDestination(void *opaque, std::uintptr_t planner,
                          std::uintptr_t province, bool &output) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id || planner == 0 ||
      province == 0 || context.module_base == 0)
    return false;
  using Predicate = bool (*)(void *, void *, void *);
  const auto predicate = reinterpret_cast<Predicate>(context.module_base +
                                                      0x10AF6A0);
  __try {
    output = predicate(reinterpret_cast<void *>(planner),
                       reinterpret_cast<void *>(province), nullptr);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}
#endif

#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_CONFIRM_PRIVATE_V1)
bool SetStageTwo(void *opaque, std::uintptr_t planner) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id || planner == 0 ||
      context.module_base == 0)
    return false;
  using Setter = void (*)(void *, std::int32_t);
  const auto setter =
      reinterpret_cast<Setter>(context.module_base + 0x10B1BD0);
  __try {
    setter(reinterpret_cast<void *>(planner), 2);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

bool FindAutoRow(void *opaque, std::uintptr_t planner,
                 std::uintptr_t &output) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id || planner == 0 ||
      context.module_base == 0)
    return false;
  using Finder = void *(*)(void *);
  const auto finder =
      reinterpret_cast<Finder>(context.module_base + 0x10ADFA0);
  __try {
    output = reinterpret_cast<std::uintptr_t>(
        finder(reinterpret_cast<void *>(planner)));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = 0;
    return false;
  }
}

bool ProgressNonzero(void *opaque, std::uintptr_t planner) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id || planner == 0 ||
      context.module_base == 0)
    return false;
  using Progress = void (*)(void *);
  const auto progress =
      reinterpret_cast<Progress>(context.module_base + 0x10B1330);
  __try {
    progress(reinterpret_cast<void *>(planner));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}
#endif

} // namespace

bool ExecuteActivityStage1OptionReadPrivateV1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<ActivityStage1OptionReadPrivateQueryV1 *>(opaque);
  if (query == nullptr || query->mailbox == nullptr ||
      query->ticket.sequence == 0 || query->expected_revision == 0 ||
      query->invocations != 0 || stamp.pump_epoch == 0 || stamp.thread_id == 0 ||
      !stamp.paused || stamp.tls_initialized_flag_address == 0 ||
      stamp.tls_initialized != 1 || stamp.tls_context == 0 ||
      stamp.tls_main_thread_marker != 1 || stamp.jomini_state == 0 ||
      stamp.game_state == 0 || GetCurrentThreadId() != stamp.thread_id)
    return false;
  auto &mailbox = *query->mailbox;
  if (mailbox.state.load(std::memory_order_acquire) !=
          MainThreadQueryMailboxStateV1::executing ||
      mailbox.stop_requested.load(std::memory_order_acquire) ||
      mailbox.failure_flags.load(std::memory_order_acquire) != 0 ||
      mailbox.published_sequence.load(std::memory_order_acquire) !=
          query->ticket.sequence ||
      mailbox.owner_thread_id.load(std::memory_order_acquire) != stamp.thread_id ||
      mailbox.paused_owner_verified_pump_epochs.load(std::memory_order_acquire) <
          kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs ||
      mailbox.executor != &ExecuteActivityStage1OptionReadPrivateV1 ||
      mailbox.executor_context != query)
    return false;
  try {
    ++query->invocations;
    game::Snapshot current{};
    if (!ReadSnapshot(query->bindings, current) ||
        current != query->expected_snapshot || !current.paused ||
        !current.map_ready || !current.has_played_character ||
        !current.played_character_alive || current.date_raw != stamp.date_raw) {
      query->frame_changed = true;
      query->failure = "published_frame_changed";
      query->completed = true;
      return true;
    }
    const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    if (!query->bindings.enabled || base == 0) {
      query->failure = "exact_activity_stage1_build_unavailable";
      query->completed = true;
      return true;
    }
    CaptureContext context{query, base, stamp.thread_id, stamp.game_state};
    bridge::ActivityStage1OptionEnvironmentV1 environment{};
    environment.diagnostic = {true,
                              bridge::kActivityPlannerDiagExeSha256V1,
                              base,
                              &context,
                              &ReadMemory,
                              &ReadFrame,
                              &CastIdler,
                              &InvokeVisibility};
    environment.resolve_key = &ResolveKey;
    environment.selected_option = &SelectedOption;
    environment.option_predicate = &OptionPredicate;
    environment.can_progress = &CanProgress;
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_CONFIRM_PRIVATE_V1)
    if (query->confirm_stage_one) {
      environment.set_stage_two = &SetStageTwo;
      environment.find_auto_row = &FindAutoRow;
      environment.progress_nonzero = &ProgressNonzero;
    }
#endif
    const bridge::ActivityPlannerDiagFrameV1 expected{
        query->expected_revision, current.date_raw,
        current.played_character_id, true, true, true, true};
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_LOCATION_READ_PRIVATE_V1)
    if (query->stage_two_location_read) {
      bridge::ActivityStage2LocationEnvironmentV1 location_environment{};
      location_environment.option = environment;
      location_environment.resolve_province = &ResolveActivityProvince;
      location_environment.can_select_destination = &CanSelectDestination;
      query->stage_two_location_result = bridge::ReadActivityStage2LocationV1(
          location_environment, expected,
          std::span<const std::int32_t>(query->candidate_province_ids.data(),
                                        query->candidate_province_count));
      if (query->stage_two_location_result.status !=
          bridge::ActivityStage2LocationReadStatusV1::observed)
        query->failure = "native_activity_stage2_location_red:" +
            std::string(bridge::ActivityStage2LocationReadStatusKeyV1(
                query->stage_two_location_result.status));
    } else
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_GATE_READ_PRIVATE_V1)
    if (query->stage_two_gate_read) {
      query->stage_two_gate_result = bridge::ReadActivityStage2GateV1(
          environment, expected);
      if (query->stage_two_gate_result.status !=
          bridge::ActivityStage2GateReadStatusV1::observed)
        query->failure = "native_activity_stage2_gate_red:" +
            std::string(bridge::ActivityStage2GateReadStatusKeyV1(
                query->stage_two_gate_result.status));
    } else
#endif
    if (query->stage_two_read) {
      query->stage_two_result = bridge::ReadActivityStage2OptionV1(
          environment, expected);
      if (query->stage_two_result.status !=
          bridge::ActivityStage2OptionReadStatusV1::observed)
        query->failure = "native_activity_stage2_option_red:" +
            std::string(bridge::ActivityStage2OptionReadStatusKeyV1(
                query->stage_two_result.status));
      else if (!query->stage_two_result.generic_feast_selected)
        query->failure = "native_activity_stage2_option_key_mismatch";
    } else if (query->confirm_stage_one) {
      query->confirm_result = bridge::ConfirmActivityStage1V1(
          environment, expected);
      query->post_snapshot_read = ReadSnapshot(query->bindings,
                                               query->post_snapshot);
      if (query->confirm_result.status !=
              bridge::ActivityStage1ConfirmStatusV1::stage_two_verified ||
          !query->post_snapshot_read ||
          query->post_snapshot != current)
        query->failure = "native_activity_stage1_confirm_red:" +
            std::string(bridge::ActivityStage1ConfirmStatusKeyV1(
                query->confirm_result.status));
    } else {
      query->result = bridge::ReadActivityStage1OptionV1(environment, expected);
      if (query->result.status !=
          bridge::ActivityStage1OptionReadStatusV1::observed)
        query->failure = "native_activity_stage1_option_red:" +
            std::string(bridge::ActivityStage1OptionReadStatusKeyV1(
                query->result.status));
    }
    query->completed = true;
    return true;
  } catch (...) {
    query->failure = "native_activity_stage1_option_exception";
    query->completed = true;
    return true;
  }
}

std::string SerializeActivityStage1OptionReadPrivateV1(
    const ActivityStage1OptionReadPrivateQueryV1 &query) {
  if (!query.completed || !query.failure.empty() ||
      query.result.status != bridge::ActivityStage1OptionReadStatusV1::observed)
    return {};
  const auto &r = query.result;
  std::string out =
      "{\"schema\":\"activity-stage1-option-private-read-v1\","
      "\"snapshot_revision\":" + std::to_string(r.frame.revision) +
      ",\"date_raw\":" + std::to_string(r.frame.date_raw) +
      ",\"actor_character_id\":" +
      std::to_string(r.frame.actor_character_id) +
      ",\"activity_key\":\"activity_feast\",\"planning_stage\":1,"
      "\"selected_option_key\":\"";
  out.append(r.option_key.data(), r.option_key_size);
  out += "\",\"selected_option_shown\":";
  out += r.shown ? "true" : "false";
  out += ",\"selected_option_valid\":";
  out += r.valid ? "true" : "false";
  out += ",\"can_progress_stage1\":";
  out += r.can_progress ? "true" : "false";
  out += ",\"generic_feast_confirm_ready\":";
  out += r.generic_feast_confirm_ready ? "true" : "false";
  out += ",\"read_only\":true,\"raw_pointer_fields_persisted\":false}";
  return out;
}

std::string SerializeActivityStage1ConfirmPrivateV1(
    const ActivityStage1OptionReadPrivateQueryV1 &query) {
  if (!query.completed || !query.confirm_stage_one) return {};
  const auto &r = query.confirm_result;
  const bool pre_observed = r.precondition.status ==
      bridge::ActivityStage1OptionReadStatusV1::observed;
  std::string out =
      "{\"schema\":\"activity-stage1-confirm-private-v1\","
      "\"snapshot_revision\":" + std::to_string(query.expected_revision) +
      ",\"date_raw\":" +
      std::to_string(query.expected_snapshot.date_raw) +
      ",\"actor_character_id\":" +
      std::to_string(query.expected_snapshot.played_character_id) +
      ",\"activity_key\":\"activity_feast\","
      "\"expected_option_key\":\"feast_type_generic\","
      "\"selected_option_key\":";
  if (pre_observed && r.precondition.option_key_size != 0) {
    out += "\"";
    out.append(r.precondition.option_key.data(),
               r.precondition.option_key_size);
    out += "\"";
  } else {
    out += "null";
  }
  out += ",\"precondition_status\":\"" +
      std::string(bridge::ActivityStage1OptionReadStatusKeyV1(
          r.precondition.status)) +
      "\",\"selected_option_shown\":" +
      std::string(pre_observed ? (r.precondition.shown ? "true" : "false")
                               : "null") +
      ",\"selected_option_valid\":" +
      std::string(pre_observed ? (r.precondition.valid ? "true" : "false")
                               : "null") +
      ",\"can_progress_stage1\":" +
      std::string(pre_observed ? (r.precondition.can_progress ? "true"
                                                         : "false")
                               : "null") +
      ",\"generic_feast_confirm_ready\":" +
      std::string(pre_observed
                      ? (r.precondition.generic_feast_confirm_ready ? "true"
                                                                    : "false")
                      : "null") +
      ",\"status\":\"" +
      std::string(bridge::ActivityStage1ConfirmStatusKeyV1(r.status)) +
      "\",\"submitted\":";
  out += r.submitted ? "true" : "false";
  out += ",\"stage_two_visible\":";
  out += r.stage_two_visible ? "true" : "false";
  out += ",\"selected_option_retained\":";
  out += r.selected_option_retained ? "true" : "false";
  out += ",\"planning_stage_after\":";
  out += r.stage_two_visible ? "2" : "null";
  out += ",\"gold_before_raw\":" +
      std::to_string(query.expected_snapshot.played_character_gold.raw);
  out += ",\"gold_after_raw\":";
  out += query.post_snapshot_read
             ? std::to_string(query.post_snapshot.played_character_gold.raw)
             : "null";
  out += ",\"snapshot_unchanged\":";
  out += query.post_snapshot_read &&
                 query.post_snapshot == query.expected_snapshot
             ? "true" : "false";
  out += ",\"activity_start_state\":\"";
  out += r.status == bridge::ActivityStage1ConfirmStatusV1::stage_two_verified &&
                 query.post_snapshot_read &&
                 query.post_snapshot == query.expected_snapshot
             ? "not_started_immediate" : "unknown";
  out += "\",\"next_turn_verified\":false,"
         "\"raw_pointer_fields_persisted\":false";
  if (r.status == bridge::ActivityStage1ConfirmStatusV1::precondition_rejected) {
    out += ",\"precondition_reject_reason\":\"" +
        std::string(bridge::ActivityStage1ConfirmRejectReasonKeyV1(
            r.reject_reason)) + "\",\"planner_stage_auto_raw\":";
    out += r.planner_stage_auto_observed
               ? std::to_string(r.planner_stage_auto_raw)
               : "null";
  }
  out += ",\"advertised\":false}";
  return out;
}

std::string SerializeActivityStage2OptionReadPrivateV1(
    const ActivityStage1OptionReadPrivateQueryV1 &query) {
  const auto &r = query.stage_two_result;
  if (!query.completed || !query.stage_two_read || !query.failure.empty() ||
      r.status != bridge::ActivityStage2OptionReadStatusV1::observed ||
      !r.generic_feast_selected)
    return {};
  std::string out =
      "{\"schema\":\"activity-stage2-option-private-read-v1\","
      "\"snapshot_revision\":" + std::to_string(r.frame.revision) +
      ",\"date_raw\":" + std::to_string(r.frame.date_raw) +
      ",\"actor_character_id\":" +
      std::to_string(r.frame.actor_character_id) +
      ",\"activity_key\":\"activity_feast\","
      "\"planning_stage\":2,\"selected_option_key\":\"";
  out.append(r.option_key.data(), r.option_key_size);
  out += "\",\"generic_feast_selected\":true,\"read_only\":true,"
         "\"raw_pointer_fields_persisted\":false,\"advertised\":false}";
  return out;
}

std::string SerializeActivityStage2GateReadPrivateV1(
    const ActivityStage1OptionReadPrivateQueryV1 &query) {
  const auto &r = query.stage_two_gate_result;
  if (!query.completed || !query.stage_two_gate_read ||
      !query.failure.empty() ||
      r.status != bridge::ActivityStage2GateReadStatusV1::observed ||
      !r.selected_option.generic_feast_selected)
    return {};
  std::string out =
      "{\"schema\":\"activity-stage2-gate-private-read-v1\","
      "\"snapshot_revision\":" +
      std::to_string(r.selected_option.frame.revision) +
      ",\"date_raw\":" +
      std::to_string(r.selected_option.frame.date_raw) +
      ",\"actor_character_id\":" +
      std::to_string(r.selected_option.frame.actor_character_id) +
      ",\"activity_key\":\"activity_feast\","
      "\"planning_stage\":2,\"selected_option_key\":\"";
  out.append(r.selected_option.option_key.data(),
             r.selected_option.option_key_size);
  out += "\",\"configuration_row_count\":" +
         std::to_string(r.configuration_row_count) +
         ",\"failing_rows\":[";
  for (std::uint16_t index = 0; index < r.failed_row_count; ++index) {
    if (index != 0) out += ',';
    const auto &row = r.failed_rows[index];
    out += "{\"index\":" + std::to_string(row.index) +
           ",\"raw_dword\":" + std::to_string(row.raw_dword) + "}";
  }
  out += "],\"can_progress_stage2\":";
  out += r.can_progress_stage2 ? "true" : "false";
  out += ",\"generic_feast_stage2_advance_ready\":";
  out += r.generic_feast_stage2_advance_ready ? "true" : "false";
  out += ",\"read_only\":true,\"raw_pointer_fields_persisted\":false,"
         "\"advertised\":false}";
  return out;
}

bool ParseActivityStage2CandidateIdsV1(
    std::string_view json,
    std::array<std::int32_t, bridge::kActivityStage2MaximumCandidatesV1>
        &output,
    std::uint16_t &count) noexcept {
  output = {};
  count = 0;
  constexpr std::string_view key = "\"candidate_province_ids\"";
  auto position = json.find(key);
  if (position == std::string_view::npos) return false;
  position += key.size();
  auto skip_space = [&]() noexcept {
    while (position < json.size() &&
           (json[position] == ' ' || json[position] == '\t' ||
            json[position] == '\r' || json[position] == '\n'))
      ++position;
  };
  skip_space();
  if (position == json.size() || json[position++] != ':') return false;
  skip_space();
  if (position == json.size() || json[position++] != '[') return false;
  skip_space();
  if (position == json.size() || json[position] == ']') return false;
  for (;;) {
    if (count == output.size() || position == json.size() ||
        json[position] < '0' || json[position] > '9')
      return false;
    const auto start = position;
    while (position < json.size() && json[position] >= '0' &&
           json[position] <= '9') ++position;
    std::int32_t id = 0;
    const auto parsed = std::from_chars(json.data() + start,
                                        json.data() + position, id);
    if (parsed.ec != std::errc{} || id < 1) return false;
    for (std::uint16_t i = 0; i < count; ++i)
      if (output[i] == id) return false;
    output[count++] = id;
    skip_space();
    if (position == json.size()) return false;
    if (json[position] == ']') return true;
    if (json[position++] != ',') return false;
    skip_space();
  }
}

std::string SerializeActivityStage2LocationReadPrivateV1(
    const ActivityStage1OptionReadPrivateQueryV1 &query) {
  const auto &r = query.stage_two_location_result;
  if (!query.completed || !query.stage_two_location_read ||
      !query.failure.empty() ||
      r.status != bridge::ActivityStage2LocationReadStatusV1::observed ||
      !r.gate.selected_option.generic_feast_selected)
    return {};
  std::string out =
      "{\"schema\":\"activity-stage2-location-private-read-v1\","
      "\"snapshot_revision\":" +
      std::to_string(r.gate.selected_option.frame.revision) +
      ",\"date_raw\":" +
      std::to_string(r.gate.selected_option.frame.date_raw) +
      ",\"actor_character_id\":" +
      std::to_string(r.gate.selected_option.frame.actor_character_id) +
      ",\"activity_key\":\"activity_feast\",\"planning_stage\":2,"
      "\"selected_option_key\":\"";
  out.append(r.gate.selected_option.option_key.data(),
             r.gate.selected_option.option_key_size);
  out += "\",\"configuration_rows\":[";
  for (std::uint16_t i = 0; i < r.row_count; ++i) {
    if (i != 0) out += ',';
    const auto &row = r.rows[i];
    out += "{\"index\":" + std::to_string(row.index) +
           ",\"phase_kind\":" +
           (row.phase_present ? std::to_string(row.phase_kind) : "null") +
           ",\"province_id\":" + std::to_string(row.province_id) +
           ",\"is_active\":" + (row.is_active ? "true" : "false") + "}";
  }
  out += "],\"active_row_index\":" +
         std::to_string(r.active_row_index) +
         ",\"activity_single_location_flag\":" +
         (r.activity_single_location_flag ? "true" : "false") +
         ",\"previous_planning_stage\":" +
         std::to_string(r.previous_planning_stage) +
         ",\"candidates\":[";
  for (std::uint16_t i = 0; i < r.candidate_count; ++i) {
    if (i != 0) out += ',';
    out += "{\"province_id\":" +
           std::to_string(r.candidates[i].province_id) +
           ",\"can_select\":" +
           (r.candidates[i].can_select ? "true" : "false") + "}";
  }
  out += "],\"can_progress_stage2\":" +
         std::string(r.gate.can_progress_stage2 ? "true" : "false") +
         ",\"read_only\":true,\"raw_pointer_fields_persisted\":false,"
         "\"advertised\":false}";
  return out;
}

} // namespace xar::ck3_11906
