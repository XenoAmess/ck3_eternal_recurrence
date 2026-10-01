#include "xar_bridge/ck3_12002_feast_planner_native.hpp"
#include "xar_bridge/ck3_12002_province.hpp"

#include <windows.h>

#include <cstring>
#include <limits>

namespace xar::ck3_12002 {
namespace {

bool IsOwner(const ActivityPlanner12002NativeV1 &context) noexcept {
  return context.enabled && context.module_base != 0 &&
         context.executable_sha256 == bridge::kActivityPlanner12002ExeSha256V1 &&
         context.owner_thread_id != 0 &&
         GetCurrentThreadId() == context.owner_thread_id;
}

bool ReadMemory(void *opaque, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  const auto &context = *static_cast<ActivityPlanner12002NativeV1 *>(opaque);
  if (!IsOwner(context) || address == 0 || output == nullptr || size == 0)
    return false;
  if (context.read_memory != nullptr)
    return context.read_memory(context.native_context, address, output, size);
  SIZE_T read = 0;
  return ReadProcessMemory(GetCurrentProcess(),
                           reinterpret_cast<const void *>(address), output,
                           size, &read) != 0 && read == size;
}

template <class T>
bool ReadAt(ActivityPlanner12002NativeV1 &context, std::uintptr_t base,
            std::size_t offset, T &output) noexcept {
  return base != 0 &&
         offset <= (std::numeric_limits<std::uintptr_t>::max)() - base &&
         ReadMemory(&context, base + offset, &output, sizeof(output));
}

bool ReadSnapshot(ActivityPlanner12002NativeV1 &context,
                  game::Snapshot &output) noexcept {
  return IsOwner(context) && context.read_snapshot != nullptr &&
         context.read_snapshot(context.native_context, output);
}

bool ReadFrame(void *opaque, bridge::ActivityPlannerDiagFrameV1 &output) noexcept {
  auto &context = *static_cast<ActivityPlanner12002NativeV1 *>(opaque);
  game::Snapshot snapshot{};
  if (!ReadSnapshot(context, snapshot)) return false;
  output = {context.revision, snapshot.date_raw, snapshot.played_character_id,
            true, snapshot.paused, snapshot.map_ready,
            snapshot.has_played_character && snapshot.played_character_alive};
  return true;
}

std::uintptr_t CastIdler(void *opaque, std::uintptr_t source,
                         std::uintptr_t source_type,
                         std::uintptr_t target_type) noexcept {
  const auto &context = *static_cast<ActivityPlanner12002NativeV1 *>(opaque);
  if (!IsOwner(context) || source == 0 || source_type == 0 || target_type == 0)
    return 0;
  using NativeCast = void *(*)(void *, std::int32_t, void *, void *, std::int32_t);
  const auto cast = reinterpret_cast<NativeCast>(context.module_base + 0x4260E94);
  __try {
    return reinterpret_cast<std::uintptr_t>(cast(
        reinterpret_cast<void *>(source), 0,
        reinterpret_cast<void *>(source_type),
        reinterpret_cast<void *>(target_type), 0));
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return 0;
  }
}

bool InvokeVisibility(void *opaque, std::uintptr_t planner,
                      std::uintptr_t entry, bool &output) noexcept {
  const auto &context = *static_cast<ActivityPlanner12002NativeV1 *>(opaque);
  if (!IsOwner(context) || planner == 0 || entry == 0) return false;
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
  const auto &context = *static_cast<ActivityPlanner12002NativeV1 *>(opaque);
  output = {};
  output_size = 0;
  std::string_view key{};
  if (!IsOwner(context) || identifier < 0 ||
      context.resolve_script_identifier == nullptr ||
      !context.resolve_script_identifier(context.native_context, identifier, key) ||
      key.empty() || key.size() >= output.size())
    return false;
  std::memcpy(output.data(), key.data(), key.size());
  output_size = static_cast<std::uint16_t>(key.size());
  return true;
}

bool SelectedOption(void *opaque, std::uintptr_t planner,
                    std::uintptr_t &output) noexcept {
  const auto &context = *static_cast<ActivityPlanner12002NativeV1 *>(opaque);
  output = 0;
  if (!IsOwner(context) || planner == 0) return false;
  const auto getter = reinterpret_cast<void *(*)(void *)>(
      context.module_base + 0x11B64C0);
  __try {
    output = reinterpret_cast<std::uintptr_t>(getter(reinterpret_cast<void *>(planner)));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

bool OptionPredicate(void *opaque, std::uintptr_t entry,
                     std::uintptr_t candidate, std::uintptr_t actor,
                     std::uintptr_t selected, bool &output) noexcept {
  const auto &context = *static_cast<ActivityPlanner12002NativeV1 *>(opaque);
  if (!IsOwner(context) || entry == 0 || candidate == 0 || actor == 0)
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
  const auto &context = *static_cast<ActivityPlanner12002NativeV1 *>(opaque);
  if (!IsOwner(context) || planner == 0) return false;
  const auto predicate = reinterpret_cast<bool (*)(void *, void *)>(
      context.module_base + 0x11B8670);
  __try {
    output = predicate(reinterpret_cast<void *>(planner), nullptr);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

bool SetStage(ActivityPlanner12002NativeV1 &context, std::uintptr_t planner,
              std::int32_t stage) noexcept {
  if (!IsOwner(context) || planner == 0) return false;
  const auto setter = reinterpret_cast<void (*)(void *, std::int32_t)>(
      context.module_base + 0x11B95D0);
  __try {
    setter(reinterpret_cast<void *>(planner), stage);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

bool SetStageTwo(void *opaque, std::uintptr_t planner) noexcept {
  return SetStage(*static_cast<ActivityPlanner12002NativeV1 *>(opaque), planner, 2);
}

bool SetStageFive(void *opaque, std::uintptr_t planner) noexcept {
  return SetStage(*static_cast<ActivityPlanner12002NativeV1 *>(opaque), planner, 5);
}

bool FindAutoRow(void *opaque, std::uintptr_t planner,
                 std::uintptr_t &output) noexcept {
  const auto &context = *static_cast<ActivityPlanner12002NativeV1 *>(opaque);
  output = 0;
  if (!IsOwner(context) || planner == 0) return false;
  const auto finder = reinterpret_cast<void *(*)(void *)>(
      context.module_base + 0x11B5950);
  __try {
    output = reinterpret_cast<std::uintptr_t>(finder(reinterpret_cast<void *>(planner)));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

bool ProgressNonzero(void *opaque, std::uintptr_t planner) noexcept {
  const auto &context = *static_cast<ActivityPlanner12002NativeV1 *>(opaque);
  if (!IsOwner(context) || planner == 0) return false;
  const auto progress = reinterpret_cast<void (*)(void *)>(
      context.module_base + 0x11B8CD0);
  __try {
    progress(reinterpret_cast<void *>(planner));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

bool ResolveProvince(void *opaque, std::uint32_t id,
                     std::uintptr_t &output) noexcept {
  auto &context = *static_cast<ActivityPlanner12002NativeV1 *>(opaque);
  output = 0;
  if (!IsOwner(context) || context.game_state == 0 || id == 0 ||
      id > static_cast<std::uint32_t>((std::numeric_limits<std::int32_t>::max)()))
    return false;
  std::uintptr_t game_data = 0, data = 0, province = 0;
  std::int32_t count = 0, reverse_id = 0;
  std::uint32_t magic = 0;
  if (!ReadAt(context, context.game_state, 0xA0, game_data) || game_data == 0 ||
      !ReadAt(context, game_data, kObjectiveProvinceArrayOffset, data) || data == 0 ||
      !ReadAt(context, game_data, kObjectiveProvinceCountOffset, count) || count <= 1 ||
      id >= static_cast<std::uint32_t>(count) ||
      !ReadAt(context, data, static_cast<std::size_t>(id) * sizeof(void *), province) ||
      province == 0 || !ReadAt(context, province, 0x10, reverse_id) ||
      reverse_id != static_cast<std::int32_t>(id) ||
      !ReadAt(context, province, kObjectiveProvinceMagicOffset, magic) ||
      magic != 0x50726F76U)
    return false;
  output = province;
  return true;
}

bool ResolveLocationProvince(void *opaque, std::int32_t id,
                             std::uintptr_t &output) noexcept {
  return id > 0 && ResolveProvince(opaque, static_cast<std::uint32_t>(id), output);
}

bool CanSelect(void *opaque, std::uintptr_t planner,
               std::uintptr_t province, bool &output) noexcept {
  const auto &context = *static_cast<ActivityPlanner12002NativeV1 *>(opaque);
  if (!IsOwner(context) || planner == 0 || province == 0) return false;
  const auto predicate = reinterpret_cast<bool (*)(void *, void *, void *)>(
      context.module_base + 0x11B6F50);
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
  const auto &context = *static_cast<ActivityPlanner12002NativeV1 *>(opaque);
  if (!IsOwner(context) || planner == 0 || province == 0) return false;
  const auto selector = reinterpret_cast<void (*)(void *, void *)>(
      context.module_base + 0x11B6C80);
  __try {
    selector(reinterpret_cast<void *>(planner), reinterpret_cast<void *>(province));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

bool IsFeastType(ActivityPlanner12002NativeV1 &context,
                 std::uintptr_t type) noexcept {
  constexpr std::string_view key = "activity_feast";
  std::uintptr_t vtable = 0, data = type + 0x18;
  std::uint64_t size = 0, capacity = 0;
  std::array<char, 16> actual{};
  return ReadAt(context, type, 0, vtable) &&
         vtable == context.module_base + 0x48BFE50 &&
         ReadAt(context, type, 0x28, size) && size == key.size() &&
         ReadAt(context, type, 0x30, capacity) && capacity >= size &&
         (capacity <= 15 || ReadAt(context, type, 0x18, data)) &&
         ReadMemory(&context, data, actual.data(), key.size()) &&
         std::memcmp(actual.data(), key.data(), key.size()) == 0;
}

bool ReadDestinationState(void *opaque,
                          bridge::ActivityStage2DestinationStateV1 &output) noexcept {
  auto &context = *static_cast<ActivityPlanner12002NativeV1 *>(opaque);
  output = {};
  if (!ReadFrame(opaque, output.frame) || !output.frame.paused ||
      !output.frame.map_ready || !output.frame.actor_alive)
    return false;
  const auto diagnostic = BuildActivityPlanner12002DiagEnvironmentV1(context);
  bridge::ActivityPlannerIdentityV1 identity{};
  game::Snapshot snapshot{};
  if (!bridge::ResolveActivityPlannerIdentityV1(diagnostic, output.frame, identity) ||
      (identity.stage != 2 && identity.stage != 5) ||
      !ReadSnapshot(context, snapshot) || snapshot.date_raw != output.frame.date_raw ||
      snapshot.played_character_id != output.frame.actor_character_id)
    return false;
  output.planner = identity.planner;
  output.activity_type = identity.activity_type;
  output.stage = identity.stage;
  output.gold_raw = snapshot.played_character_gold.raw;
  output.activity_feast = IsFeastType(context, identity.activity_type);
  if (!output.activity_feast ||
      !ReadAt(context, output.planner, 0x1AEC, output.previous_stage) ||
      !ReadAt(context, output.planner, 0x15B0, output.configuration_rows) ||
      output.configuration_rows == 0 ||
      !ReadAt(context, output.planner, 0x15BC, output.configuration_row_count) ||
      output.configuration_row_count != 2 ||
      !ReadAt(context, output.planner, 0x1AF8, output.active_row) ||
      !ReadAt(context, output.activity_type, 0x3BED, output.single_location_flag) ||
      !ReadAt(context, output.configuration_rows, 8, output.province_ids[0]) ||
      !ReadAt(context, output.configuration_rows, 0x38 + 8, output.province_ids[1]) ||
      !SelectedOption(opaque, output.planner, output.selected_option) ||
      output.selected_option == 0)
    return false;
  std::uintptr_t option_vtable = 0;
  std::array<char, 96> key{};
  std::uint16_t key_size = 0;
  if (!ReadAt(context, output.selected_option, 0, option_vtable) ||
      option_vtable != context.module_base + 0x48BFD18 ||
      !ReadAt(context, output.selected_option, 8, output.selected_option_id) ||
      !ResolveKey(opaque, output.selected_option_id, key, key_size))
    return false;
  output.generic_feast_option =
      std::string_view(key.data(), key_size) == bridge::kActivityStage1OptionKeyV1;
  // The exact typed destination branch reaches the attached stage-5 planner;
  // it does not invoke Start. Other stages or a detached planner fail above.
  output.activity_started = false;
  if (++context.destination_state_reads == 1) {
    context.destination_before = output;
    context.destination_before_read = true;
  } else if (context.destination_state_reads >= 3) {
    context.destination_after = output;
    context.destination_after_read = true;
  }
  return true;
}

bool ReadGoldRaw(void *opaque, std::int64_t &output) noexcept {
  game::Snapshot snapshot{};
  if (!ReadSnapshot(*static_cast<ActivityPlanner12002NativeV1 *>(opaque), snapshot))
    return false;
  output = snapshot.played_character_gold.raw;
  return true;
}

struct NativeTypePayload {
  std::uintptr_t descriptor = 0;
  std::array<std::uint8_t, 32> data{};
};
static_assert(sizeof(NativeTypePayload) == 0x28);

bool DispatchFeast(void *opaque, std::uintptr_t handler,
                  std::uintptr_t type) noexcept {
  const auto &context = *static_cast<ActivityPlanner12002NativeV1 *>(opaque);
  if (!IsOwner(context) || handler == 0 || type == 0) return false;
  const auto descriptor = reinterpret_cast<void *(*)()>(context.module_base + 0xD51E50);
  const auto dispatch = reinterpret_cast<void (*)(void *, std::int32_t, const void *)>(
      context.module_base + 0xAF39E0);
  NativeTypePayload payload{};
  std::memcpy(payload.data.data(), &type, sizeof(type));
  __try {
    payload.descriptor = reinterpret_cast<std::uintptr_t>(descriptor());
    if (payload.descriptor != context.module_base + 0x54D76F0) return false;
    // HostView::CanPlan (1.20 RVA 0x1643970) supplies this unchanged typed
    // event. Its event table resolves +0x98 + 0x65*8 to handler +0x3C0.
    dispatch(reinterpret_cast<void *>(handler), 0x65, &payload);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

} // namespace

bool BindActivityPlanner12002V1(
    ActivityPlanner12002NativeV1 &output, std::uintptr_t module_base,
    std::string_view executable_sha256, void *native_context,
    ActivityPlanner12002ReadSnapshotV1 read_snapshot,
    bridge::ActivityPlannerDiagReadMemoryV1 read_memory,
    ActivityPlanner12002ResolveScriptIdentifierV1 resolve_script_identifier,
    std::uint64_t revision, std::uint32_t owner_thread_id,
    std::uintptr_t game_state) noexcept {
  output = {};
  if (module_base == 0 ||
      executable_sha256 != bridge::kActivityPlanner12002ExeSha256V1 ||
      read_snapshot == nullptr || revision == 0 || owner_thread_id == 0 ||
      game_state == 0)
    return false;
  output.enabled = true;
  output.module_base = module_base;
  output.executable_sha256 = executable_sha256;
  output.native_context = native_context;
  output.read_snapshot = read_snapshot;
  output.read_memory = read_memory;
  output.resolve_script_identifier = resolve_script_identifier;
  output.revision = revision;
  output.owner_thread_id = owner_thread_id;
  output.game_state = game_state;
  return true;
}

bridge::ActivityPlannerDiagEnvironmentV1 BuildActivityPlanner12002DiagEnvironmentV1(
    ActivityPlanner12002NativeV1 &context) noexcept {
  return {context.enabled, context.executable_sha256, context.module_base,
          &context, &ReadMemory, &ReadFrame, &CastIdler, &InvokeVisibility};
}

bridge::ActivityFeastPlannerOpenEnvironmentV1 BuildActivityPlanner12002OpenEnvironmentV1(
    ActivityPlanner12002NativeV1 &context) noexcept {
  return {BuildActivityPlanner12002DiagEnvironmentV1(context), &DispatchFeast};
}

bridge::ActivityStage1OptionEnvironmentV1 BuildActivityPlanner12002OptionEnvironmentV1(
    ActivityPlanner12002NativeV1 &context) noexcept {
  return {BuildActivityPlanner12002DiagEnvironmentV1(context), &ResolveKey,
          &SelectedOption, &OptionPredicate, &CanProgress,
          &SetStageTwo, &FindAutoRow, &ProgressNonzero};
}

bridge::ActivityStage2LocationEnvironmentV1 BuildActivityPlanner12002LocationEnvironmentV1(
    ActivityPlanner12002NativeV1 &context) noexcept {
  return {BuildActivityPlanner12002OptionEnvironmentV1(context),
          &ResolveLocationProvince, &CanSelect};
}

bridge::ActivityStage2DestinationEnvironmentV1
BuildActivityPlanner12002DestinationEnvironmentV1(
    ActivityPlanner12002NativeV1 &context) noexcept {
  return {BuildActivityPlanner12002DiagEnvironmentV1(context), &ReadDestinationState,
          &ResolveProvince, &CanSelect, &SelectOnce};
}

bridge::ActivityStage2ConfirmEnvironmentV1 BuildActivityPlanner12002ConfirmEnvironmentV1(
    ActivityPlanner12002NativeV1 &context) noexcept {
  return {BuildActivityPlanner12002OptionEnvironmentV1(context),
          &SetStageFive, &ReadGoldRaw};
}

} // namespace xar::ck3_12002
