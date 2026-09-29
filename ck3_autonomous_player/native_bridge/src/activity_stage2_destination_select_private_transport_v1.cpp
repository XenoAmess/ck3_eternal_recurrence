#include "activity_stage2_destination_select_private_transport_v1.hpp"

#include <windows.h>

#include <array>
#include <cstring>
#include <limits>

namespace xar::ck3_11906 {
namespace {

struct CaptureContext {
  ActivityStage2DestinationSelectPrivateQueryV1 *query = nullptr;
  std::uintptr_t module_base = 0;
  DWORD owner_thread_id = 0;
  std::uintptr_t game_state = 0;
  std::uint32_t reads = 0;
};

bool ReadMemory(void *, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  SIZE_T read = 0;
  return address != 0 && output != nullptr && size != 0 &&
         ReadProcessMemory(GetCurrentProcess(),
                           reinterpret_cast<const void *>(address), output,
                           size, &read) != 0 && read == size;
}

template <typename T>
bool ReadAt(std::uintptr_t base, std::size_t offset, T &value) noexcept {
  return base != 0 &&
         offset <= (std::numeric_limits<std::uintptr_t>::max)() - base &&
         ReadMemory(nullptr, base + offset, &value, sizeof(value));
}

bool ReadFrame(void *opaque,
               bridge::ActivityPlannerDiagFrameV1 &output) noexcept {
  const auto &context = *static_cast<CaptureContext *>(opaque);
  game::Snapshot snapshot{};
  if (GetCurrentThreadId() != context.owner_thread_id ||
      !ReadSnapshot(context.query->bindings, snapshot))
    return false;
  output = {context.query->expected_revision, snapshot.date_raw,
            snapshot.played_character_id, true, snapshot.paused,
            snapshot.map_ready,
            snapshot.has_played_character && snapshot.played_character_alive};
  return true;
}

std::uintptr_t CastIdler(void *opaque, std::uintptr_t source,
                         std::uintptr_t source_type,
                         std::uintptr_t target_type) noexcept {
  const auto &context = *static_cast<CaptureContext *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id || source == 0 ||
      context.module_base == 0)
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

bool IsFeastType(std::uintptr_t base, std::uintptr_t type) noexcept {
  constexpr char key[] = "activity_feast";
  std::uintptr_t vtable = 0, data = type + 0x18;
  std::uint64_t size = 0, capacity = 0;
  if (!ReadAt(type, 0, vtable) || vtable != base + 0x440E308 ||
      !ReadAt(type, 0x28, size) || !ReadAt(type, 0x30, capacity) ||
      size != sizeof(key) - 1 || size > capacity ||
      (capacity > 15 && !ReadAt(type, 0x18, data)))
    return false;
  std::array<char, sizeof(key) - 1> actual{};
  return ReadMemory(nullptr, data, actual.data(), actual.size()) &&
         std::memcmp(actual.data(), key, actual.size()) == 0;
}

bool GenericOption(CaptureContext &context, std::int32_t identifier) noexcept {
  const auto &bindings = context.query->bindings;
  if (identifier < 0 || bindings.get_script_identifier_table == nullptr ||
      bindings.resolve_script_identifier_name == nullptr ||
      bindings.script_identifier_name_fallback == nullptr)
    return false;
  bool matched = false;
  __try {
    void *const table = bindings.get_script_identifier_table();
    if (table != nullptr) {
      const std::string *const name =
          bindings.resolve_script_identifier_name(table, identifier);
      matched = name != nullptr &&
                name != bindings.script_identifier_name_fallback &&
                *name == "feast_type_generic";
    }
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    matched = false;
  }
  return matched;
}

bool SelectedOption(CaptureContext &context, std::uintptr_t planner,
                    std::uintptr_t &output) noexcept {
  using Getter = void *(*)(void *);
  const auto getter = reinterpret_cast<Getter>(context.module_base + 0x10AEAE0);
  __try {
    output = reinterpret_cast<std::uintptr_t>(
        getter(reinterpret_cast<void *>(planner)));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = 0;
    return false;
  }
}

bool ReadState(void *opaque,
               bridge::ActivityStage2DestinationStateV1 &output) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id ||
      context.module_base == 0 || !ReadFrame(opaque, output.frame) ||
      !output.frame.paused || !output.frame.map_ready ||
      !output.frame.actor_alive)
    return false;
  game::Snapshot snapshot{};
  if (!ReadSnapshot(context.query->bindings, snapshot) ||
      snapshot.date_raw != output.frame.date_raw ||
      snapshot.played_character_id != output.frame.actor_character_id)
    return false;
  output.gold_raw = snapshot.played_character_gold.raw;

  std::uintptr_t root = 0, idler = 0, gfx = 0, handler = 0;
  std::uintptr_t vtable = 0, owner = 0;
  if (!ReadAt(context.module_base, 0x570F7B8, root) || root == 0 ||
      !ReadAt(root, 0x10, idler) || idler == 0)
    return false;
  gfx = CastIdler(opaque, idler, context.module_base + 0x501EF28,
                  context.module_base + 0x501EF50);
  if (gfx == 0 || !ReadAt(gfx, 0, vtable) ||
      vtable != context.module_base + 0x40B1D30 ||
      !ReadAt(gfx, 0x88, handler) || handler == 0 ||
      !ReadAt(handler, 0, vtable) ||
      vtable != context.module_base + 0x40AF630 ||
      !ReadAt(handler, 0x3C0, output.planner) || output.planner == 0 ||
      !ReadAt(output.planner, 0, vtable) ||
      vtable != context.module_base + 0x41205F0 ||
      !ReadAt(output.planner, 0xD0, owner) || owner != handler ||
      !ReadAt(output.planner, 0x1AB0, output.stage) ||
      !ReadAt(output.planner, 0x1AB4, output.previous_stage) ||
      !ReadAt(output.planner, 0x1530, output.activity_type) ||
      output.activity_type == 0 ||
      !ReadAt(output.planner, 0x1578, output.configuration_rows) ||
      !ReadAt(output.planner, 0x1584, output.configuration_row_count) ||
      !ReadAt(output.planner, 0x1AC0, output.active_row) ||
      !ReadAt(output.activity_type, 0x3C75, output.single_location_flag))
    return false;
  output.activity_feast =
      IsFeastType(context.module_base, output.activity_type);
  if (!output.activity_feast || output.configuration_rows == 0 ||
      output.configuration_row_count != 2 ||
      !ReadAt(output.configuration_rows, 8, output.province_ids[0]) ||
      !ReadAt(output.configuration_rows, 0x38 + 8,
              output.province_ids[1]))
    return false;

  if (!SelectedOption(context, output.planner, output.selected_option) ||
      output.selected_option == 0 ||
      !ReadAt(output.selected_option, 0, vtable) ||
      vtable != context.module_base + 0x440E1D0 ||
      !ReadAt(output.selected_option, 8, output.selected_option_id))
    return false;
  output.generic_feast_option = GenericOption(context, output.selected_option_id);
  // The exact 0x10AF3D0 single-location branch does not invoke Start. An
  // attached planner at stage 2/5 is independently observed here; if it is
  // detached or any other stage appears this read fails rather than proving
  // a false no-Start postcondition.
  if (output.stage != 2 && output.stage != 5) return false;
  output.activity_started = false;
  if (++context.reads == 1) {
    context.query->before = output;
    context.query->before_read = true;
  } else if (context.reads >= 3) {
    context.query->after = output;
    context.query->after_read = true;
  }
  return true;
}

bool ResolveProvince(void *opaque, std::uint32_t id,
                     std::uintptr_t &output) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  output = 0;
  if (GetCurrentThreadId() != context.owner_thread_id ||
      context.game_state == 0 || id == 0 || id > 0x7FFFFFFFu)
    return false;
  std::uintptr_t game_data = 0, provinces = 0, province = 0;
  std::int32_t count = 0, reverse_id = 0;
  if (!ReadAt(context.game_state, 0xA0, game_data) || game_data == 0 ||
      !ReadAt(game_data, 0x140, provinces) || provinces == 0 ||
      !ReadAt(game_data, 0x14C, count) ||
      id >= static_cast<std::uint32_t>(count) ||
      !ReadAt(provinces, static_cast<std::size_t>(id) * 8, province) ||
      province == 0 || !ReadAt(province, 0x10, reverse_id) ||
      reverse_id != static_cast<std::int32_t>(id))
    return false;
  output = province;
  return true;
}

bool CanSelect(void *opaque, std::uintptr_t planner,
               std::uintptr_t province, bool &output) noexcept {
  const auto &context = *static_cast<CaptureContext *>(opaque);
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

bool SelectOnce(void *opaque, std::uintptr_t planner,
                std::uintptr_t province) noexcept {
  const auto &context = *static_cast<CaptureContext *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id || planner == 0 ||
      province == 0 || context.module_base == 0)
    return false;
  using Selector = void (*)(void *, void *);
  const auto selector = reinterpret_cast<Selector>(context.module_base +
                                                   0x10AF3D0);
  __try {
    selector(reinterpret_cast<void *>(planner),
             reinterpret_cast<void *>(province));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

} // namespace

bool ExecuteActivityStage2DestinationSelectPrivateV1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<ActivityStage2DestinationSelectPrivateQueryV1 *>(opaque);
  if (query == nullptr || query->mailbox == nullptr ||
      query->ticket.sequence == 0 || query->expected_revision == 0 ||
      query->province_id < 1 || query->invocations != 0 ||
      stamp.pump_epoch == 0 || stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 || stamp.tls_initialized != 1 ||
      stamp.tls_context == 0 || stamp.tls_main_thread_marker != 1 ||
      stamp.jomini_state == 0 || stamp.game_state == 0 ||
      GetCurrentThreadId() != stamp.thread_id)
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
      mailbox.executor != &ExecuteActivityStage2DestinationSelectPrivateV1 ||
      mailbox.executor_context != query)
    return false;
  try {
    ++query->invocations;
    game::Snapshot current{};
    if (!ReadSnapshot(query->bindings, current) ||
        current != query->expected_snapshot || !current.paused ||
        !current.map_ready || !current.has_played_character ||
        !current.played_character_alive || current.date_raw != stamp.date_raw) {
      query->failure = "published_frame_changed";
      query->completed = true;
      return true;
    }
    const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    if (!query->bindings.enabled || base == 0) {
      query->failure = "exact_activity_stage2_destination_build_unavailable";
      query->completed = true;
      return true;
    }
    CaptureContext context{query, base, stamp.thread_id, stamp.game_state};
    bridge::ActivityStage2DestinationEnvironmentV1 environment{};
    environment.diagnostic = {true, bridge::kActivityPlannerDiagExeSha256V1,
                              base, &context, &ReadMemory, &ReadFrame,
                              &CastIdler, &InvokeVisibility};
    environment.read_state = &ReadState;
    environment.resolve_province = &ResolveProvince;
    environment.can_select = &CanSelect;
    environment.select_once = &SelectOnce;
    const bridge::ActivityPlannerDiagFrameV1 expected{
        query->expected_revision, current.date_raw,
        current.played_character_id, true, true, true, true};
    query->result = bridge::SelectActivityStage2DestinationV1(
        environment, expected, static_cast<std::uint32_t>(query->province_id));
    query->completed = true;
    return true;
  } catch (...) {
    query->failure = "native_activity_stage2_destination_exception";
    query->completed = true;
    return true;
  }
}

std::string SerializeActivityStage2DestinationSelectPrivateV1(
    const ActivityStage2DestinationSelectPrivateQueryV1 &query) {
  if (!query.completed) return {};
  const auto &r = query.result;
  const auto boolean = [](bool value) { return value ? "true" : "false"; };
  std::string out =
      "{\"schema\":\"activity-stage2-destination-private-action-v1\",";
  out += "\"snapshot_revision\":" + std::to_string(query.expected_revision) +
         ",\"date_raw\":" + std::to_string(query.expected_snapshot.date_raw) +
         ",\"actor_character_id\":" +
         std::to_string(query.expected_snapshot.played_character_id) +
         ",\"activity_key\":\"activity_feast\",";
  out += "\"selected_option_key\":\"feast_type_generic\",";
  out += "\"selected_province_id\":" + std::to_string(query.province_id) +
         ",\"status\":\"" +
         std::string(bridge::ActivityStage2DestinationStatusKeyV1(r.status)) +
         "\",";
  out += "\"submitted\":" + std::string(boolean(r.submitted)) +
         ",\"needs_recovery\":" + boolean(r.needs_recovery) +
         ",\"stage_five_visible\":" + boolean(r.stage_five_visible) +
         ",\"rows_filled\":" + boolean(r.rows_filled) +
         ",\"selected_option_retained\":" +
         boolean(r.selected_option_retained) +
         ",\"gold_unchanged\":" + boolean(r.gold_unchanged) +
         ",\"frame_unchanged\":" + boolean(r.frame_unchanged) +
         ",\"no_activity_started\":" + boolean(r.no_activity_started);
  out += ",\"planning_stage_before\":" +
         (query.before_read ? std::to_string(query.before.stage) : "null") +
         ",\"planning_stage_after\":" +
         (query.after_read ? std::to_string(query.after.stage) : "null");
  out += ",\"configuration_province_ids_before\":";
  out += query.before_read
             ? "[" + std::to_string(query.before.province_ids[0]) + "," +
                   std::to_string(query.before.province_ids[1]) + "]"
             : "null";
  out += ",\"configuration_province_ids_after\":";
  out += query.after_read
             ? "[" + std::to_string(query.after.province_ids[0]) + "," +
                   std::to_string(query.after.province_ids[1]) + "]"
             : "null";
  out += ",\"player_gold_before_raw\":" +
         (query.before_read ? std::to_string(query.before.gold_raw) : "null") +
         ",\"player_gold_after_raw\":" +
         (query.after_read ? std::to_string(query.after.gold_raw) : "null") +
         ",\"read_only\":false,\"advertised\":false}";
  return out;
}

} // namespace xar::ck3_11906
