#include "xar_bridge/activity_stage1_option_read_v1.hpp"

#include <algorithm>
#include <cstring>
#include <limits>

namespace xar::bridge {
namespace {

constexpr std::uintptr_t kRoot = 0x570F7B8;
constexpr std::uintptr_t kPlayedId = 0x4FE7EE0;
constexpr std::uintptr_t kCharacterStorage = 0x570C130;
constexpr std::uintptr_t kCharacterFallback = 0x570C138;
constexpr std::uintptr_t kIdlerSourceType = 0x501EF28;
constexpr std::uintptr_t kIdlerGfxType = 0x501EF50;
constexpr std::uintptr_t kGfxVtable = 0x40B1D30;
constexpr std::uintptr_t kHandlerVtable = 0x40AF630;
constexpr std::uintptr_t kPlannerVtable = 0x41205F0;
constexpr std::uintptr_t kActivityTypeVtable = 0x440E308;
constexpr std::uintptr_t kOptionVtable = 0x440E1D0;
constexpr std::uintptr_t kGetSelectedOptionRva = 0x10AEAE0;
constexpr std::uintptr_t kIsShownRva = 0x971270;
constexpr std::uintptr_t kIsValidRva = 0x971370;
constexpr std::uintptr_t kCanProgressRva = 0x10B0DA0;
constexpr std::uintptr_t kSetStageRva = 0x10B1BD0;

struct NativeIdentity {
  std::uintptr_t actor = 0;
  std::uintptr_t planner = 0;
  std::uintptr_t option = 0;
  std::int32_t option_id = -1;
};

bool Add(std::uintptr_t base, std::size_t offset,
         std::uintptr_t &result) noexcept {
  if (base == 0 || offset > (std::numeric_limits<std::uintptr_t>::max)() - base)
    return false;
  result = base + offset;
  return true;
}

bool Read(const ActivityPlannerDiagEnvironmentV1 &env,
          std::uintptr_t base, std::size_t offset, void *value,
          std::size_t size) noexcept {
  std::uintptr_t address = 0;
  return Add(base, offset, address) && env.read_memory != nullptr &&
         env.read_memory(env.context, address, value, size);
}

template <typename T>
bool ReadAt(const ActivityPlannerDiagEnvironmentV1 &env,
            std::uintptr_t base, std::size_t offset, T &value) noexcept {
  return Read(env, base, offset, &value, sizeof(value));
}

template <std::size_t N>
bool MatchCode(const ActivityPlannerDiagEnvironmentV1 &env,
               std::uintptr_t rva,
               const std::array<std::uint8_t, N> &expected) noexcept {
  std::array<std::uint8_t, N> actual{};
  return ReadAt(env, env.module_base, rva, actual) && actual == expected;
}

bool VerifyAbi(const ActivityStage1OptionEnvironmentV1 &env) noexcept {
  const auto &d = env.diagnostic;
  constexpr std::array<std::uint8_t, 7> kSelectedSignature{
      0x48, 0x8B, 0x81, 0x30, 0x15, 0x00, 0x00};
  constexpr std::array<std::uint8_t, 7> kShownSignature{
      0x4C, 0x8B, 0xDC, 0x49, 0x89, 0x5B, 0x10};
  constexpr std::array<std::uint8_t, 7> kValidSignature{
      0x4C, 0x8B, 0xDC, 0x49, 0x89, 0x5B, 0x10};
  constexpr std::array<std::uint8_t, 7> kProgressSignature{
      0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x89};
  return d.enabled && d.module_base != 0 &&
         d.admitted_executable_sha256 == kActivityPlannerDiagExeSha256V1 &&
         d.read_memory != nullptr && d.read_frame != nullptr &&
         d.rtti_cast != nullptr && d.invoke_visibility != nullptr &&
         MatchCode(d, kGetSelectedOptionRva, kSelectedSignature) &&
         MatchCode(d, kIsShownRva, kShownSignature) &&
         MatchCode(d, kIsValidRva, kValidSignature) &&
         MatchCode(d, kCanProgressRva, kProgressSignature);
}

bool IsFeastType(const ActivityPlannerDiagEnvironmentV1 &env,
                 std::uintptr_t type) noexcept {
  constexpr std::string_view key = "activity_feast";
  std::uintptr_t vtable = 0;
  std::uint64_t size = 0;
  std::uint64_t capacity = 0;
  std::uintptr_t data = type + 0x18;
  if (!ReadAt(env, type, 0, vtable) ||
      vtable != env.module_base + kActivityTypeVtable ||
      !ReadAt(env, type, 0x28, size) ||
      !ReadAt(env, type, 0x30, capacity) ||
      size != key.size() || size > capacity)
    return false;
  if (capacity > 15 && !ReadAt(env, type, 0x18, data)) return false;
  std::array<char, 16> copied{};
  return Read(env, data, 0, copied.data(), key.size()) &&
         std::memcmp(copied.data(), key.data(), key.size()) == 0;
}

bool ResolveNative(const ActivityStage1OptionEnvironmentV1 &env,
                   const ActivityPlannerDiagFrameV1 &frame,
                   NativeIdentity &output,
                   std::int32_t expected_stage = 1) noexcept {
  const auto &d = env.diagnostic;
  std::uintptr_t root = 0, idler = 0, gfx = 0, handler = 0;
  std::uintptr_t gfx_vtable = 0, handler_vtable = 0, planner_vtable = 0;
  std::uintptr_t owner = 0, type = 0, category = 0, rows = 0;
  std::uintptr_t selected_row = 0, option_vtable = 0;
  std::int32_t count = 0, stage = -1;
  std::uint32_t played_id = 0, actor_id = 0;
  if (!ReadAt(d, d.module_base, kRoot, root) || root == 0 ||
      !ReadAt(d, root, 0x10, idler) || idler == 0)
    return false;
  gfx = d.rtti_cast(d.context, idler, d.module_base + kIdlerSourceType,
                    d.module_base + kIdlerGfxType);
  if (gfx == 0 || !ReadAt(d, gfx, 0, gfx_vtable) ||
      gfx_vtable != d.module_base + kGfxVtable ||
      !ReadAt(d, gfx, 0x88, handler) || handler == 0 ||
      !ReadAt(d, handler, 0, handler_vtable) ||
      handler_vtable != d.module_base + kHandlerVtable ||
      !ReadAt(d, handler, 0x3C0, output.planner) || output.planner == 0 ||
      !ReadAt(d, output.planner, 0, planner_vtable) ||
      planner_vtable != d.module_base + kPlannerVtable ||
      !ReadAt(d, output.planner, 0xD0, owner) || owner != handler ||
      !ReadAt(d, output.planner, 0x1AB0, stage) ||
      stage != expected_stage ||
      !ReadAt(d, d.module_base, kPlayedId, played_id) ||
      played_id != static_cast<std::uint32_t>(frame.actor_character_id))
    return false;

  std::uintptr_t storage = 0, fallback = 0, slots = 0;
  std::int32_t capacity = 0;
  const auto index = played_id & 0x00FFFFFFu;
  if (!ReadAt(d, d.module_base, kCharacterStorage, storage) || storage == 0 ||
      !ReadAt(d, d.module_base, kCharacterFallback, fallback) ||
      !ReadAt(d, storage, 0x20, slots) || slots == 0 ||
      !ReadAt(d, storage, 0x2C, capacity) || capacity <= 0 ||
      capacity > 0x01000000 || index >= static_cast<std::uint32_t>(capacity) ||
      !ReadAt(d, slots, static_cast<std::size_t>(index) * 0x10 + 0x08,
              output.actor) ||
      output.actor == 0 || output.actor == fallback ||
      !ReadAt(d, output.actor, 0x18, actor_id) || actor_id != played_id)
    return false;

  if (!ReadAt(d, output.planner, 0x1530, type) || type == 0 ||
      !IsFeastType(d, type) || !ReadAt(d, type, 0xA88, category) ||
      category == 0 || !ReadAt(d, output.planner, 0x1560, rows) ||
      rows == 0 || !ReadAt(d, output.planner, 0x156C, count) ||
      count <= 0 || count > 128 ||
      !ReadAt(d, output.planner, 0x1AC8, selected_row))
    return false;

  std::uintptr_t found = 0;
  for (std::int32_t index_row = 0; index_row < count; ++index_row) {
    std::uintptr_t address = 0, row_category = 0;
    if (!Add(rows, static_cast<std::size_t>(index_row) * 0x10, address) ||
        !ReadAt(d, address, 0, row_category))
      return false;
    if (row_category == category) {
      if (found != 0) return false;
      found = address;
    }
  }
  if (found == 0 ||
      (expected_stage == 1 && selected_row != found) ||
      (expected_stage == 2 && selected_row != 0) ||
      !ReadAt(d, found, 0x08, output.option) || output.option == 0 ||
      !ReadAt(d, output.option, 0, option_vtable) ||
      option_vtable != d.module_base + kOptionVtable ||
      !ReadAt(d, output.option, 0x08, output.option_id))
    return false;
  std::uintptr_t from_original_getter = 0;
  return env.selected_option(d.context, output.planner, from_original_getter) &&
         from_original_getter == output.option;
}

} // namespace

ActivityStage1OptionReadResultV1 ReadActivityStage1OptionV1(
    const ActivityStage1OptionEnvironmentV1 &env,
    const ActivityPlannerDiagFrameV1 &expected) noexcept {
  ActivityStage1OptionReadResultV1 result{};
  result.frame = expected;
  if (!VerifyAbi(env)) return result;
  if (env.resolve_key == nullptr || env.selected_option == nullptr ||
      env.option_predicate == nullptr || env.can_progress == nullptr) {
    result.status = ActivityStage1OptionReadStatusV1::callback_missing;
    return result;
  }
  const auto diagnostic = ReadActivityPlannerDiagV1(env.diagnostic, expected);
  if (diagnostic.status != ActivityPlannerDiagStatusV1::observed ||
      !diagnostic.value.widget_attached ||
      !diagnostic.value.widget_visible) {
    result.status = ActivityStage1OptionReadStatusV1::planner_unavailable;
    return result;
  }
  if (diagnostic.value.stage != 1) {
    result.status = ActivityStage1OptionReadStatusV1::not_feast_stage1;
    return result;
  }
  NativeIdentity first{};
  if (!ResolveNative(env, expected, first)) {
    result.status = ActivityStage1OptionReadStatusV1::option_identity_mismatch;
    return result;
  }
  if (!env.resolve_key(env.diagnostic.context, first.option_id,
                       result.option_key, result.option_key_size) ||
      result.option_key_size == 0 ||
      result.option_key_size >= result.option_key.size() ||
      !std::all_of(result.option_key.begin(),
                   result.option_key.begin() + result.option_key_size,
                   [](char c) {
                     return (c >= 'a' && c <= 'z') ||
                            (c >= '0' && c <= '9') || c == '_';
                   })) {
    result.status = ActivityStage1OptionReadStatusV1::option_key_unavailable;
    return result;
  }
  const auto base = env.diagnostic.module_base;
  if (!env.option_predicate(env.diagnostic.context, base + kIsShownRva,
                            first.option, first.actor, first.option,
                            result.shown) ||
      !env.option_predicate(env.diagnostic.context, base + kIsValidRva,
                            first.option, first.actor, first.option,
                            result.valid) ||
      !env.can_progress(env.diagnostic.context, first.planner,
                        result.can_progress)) {
    result.status = ActivityStage1OptionReadStatusV1::native_evaluation_failed;
    return result;
  }
  NativeIdentity second{};
  ActivityPlannerDiagFrameV1 final_frame{};
  if (!ResolveNative(env, expected, second) ||
      first.actor != second.actor || first.planner != second.planner ||
      first.option != second.option || first.option_id != second.option_id ||
      !env.diagnostic.read_frame(env.diagnostic.context, final_frame) ||
      final_frame != expected) {
    result.status = ActivityStage1OptionReadStatusV1::frame_changed;
    return result;
  }
  result.generic_feast_confirm_ready =
      std::string_view(result.option_key.data(), result.option_key_size) ==
          kActivityStage1OptionKeyV1 &&
      result.shown && result.valid && result.can_progress;
  result.status = ActivityStage1OptionReadStatusV1::observed;
  return result;
}

ActivityStage2OptionReadResultV1 ReadActivityStage2OptionV1(
    const ActivityStage1OptionEnvironmentV1 &env,
    const ActivityPlannerDiagFrameV1 &expected) noexcept {
  ActivityStage2OptionReadResultV1 result{};
  result.frame = expected;
  if (!VerifyAbi(env)) return result;
  if (env.resolve_key == nullptr || env.selected_option == nullptr) {
    result.status = ActivityStage2OptionReadStatusV1::callback_missing;
    return result;
  }
  const auto diagnostic = ReadActivityPlannerDiagV1(env.diagnostic, expected);
  if (diagnostic.status != ActivityPlannerDiagStatusV1::observed ||
      !diagnostic.value.widget_attached ||
      !diagnostic.value.widget_visible) {
    result.status = ActivityStage2OptionReadStatusV1::planner_unavailable;
    return result;
  }
  if (diagnostic.value.stage != 2) {
    result.status = ActivityStage2OptionReadStatusV1::not_feast_stage_two;
    return result;
  }
  NativeIdentity first{};
  if (!ResolveNative(env, expected, first, 2)) {
    result.status = ActivityStage2OptionReadStatusV1::option_identity_mismatch;
    return result;
  }
  if (!env.resolve_key(env.diagnostic.context, first.option_id,
                       result.option_key, result.option_key_size) ||
      result.option_key_size == 0 ||
      result.option_key_size >= result.option_key.size() ||
      !std::all_of(result.option_key.begin(),
                   result.option_key.begin() + result.option_key_size,
                   [](char c) {
                     return (c >= 'a' && c <= 'z') ||
                            (c >= '0' && c <= '9') || c == '_';
                   })) {
    result.status = ActivityStage2OptionReadStatusV1::option_key_unavailable;
    return result;
  }
  NativeIdentity second{};
  ActivityPlannerDiagFrameV1 final_frame{};
  if (!ResolveNative(env, expected, second, 2) ||
      first.actor != second.actor || first.planner != second.planner ||
      first.option != second.option || first.option_id != second.option_id ||
      !env.diagnostic.read_frame(env.diagnostic.context, final_frame) ||
      final_frame != expected) {
    result.status = ActivityStage2OptionReadStatusV1::frame_changed;
    return result;
  }
  result.generic_feast_selected =
      std::string_view(result.option_key.data(), result.option_key_size) ==
      kActivityStage1OptionKeyV1;
  result.status = ActivityStage2OptionReadStatusV1::observed;
  return result;
}

std::string_view ActivityStage2OptionReadStatusKeyV1(
    ActivityStage2OptionReadStatusV1 status) noexcept {
  switch (status) {
  case ActivityStage2OptionReadStatusV1::observed:
    return "observed";
  case ActivityStage2OptionReadStatusV1::exact_build_rejected:
    return "exact_build_rejected";
  case ActivityStage2OptionReadStatusV1::callback_missing:
    return "callback_missing";
  case ActivityStage2OptionReadStatusV1::planner_unavailable:
    return "planner_unavailable";
  case ActivityStage2OptionReadStatusV1::not_feast_stage_two:
    return "not_feast_stage_two";
  case ActivityStage2OptionReadStatusV1::option_identity_mismatch:
    return "option_identity_mismatch";
  case ActivityStage2OptionReadStatusV1::option_key_unavailable:
    return "option_key_unavailable";
  case ActivityStage2OptionReadStatusV1::frame_changed:
    return "frame_changed";
  }
  return "unknown";
}

ActivityStage1ConfirmResultV1 ConfirmActivityStage1V1(
    const ActivityStage1OptionEnvironmentV1 &env,
    const ActivityPlannerDiagFrameV1 &expected) noexcept {
  ActivityStage1ConfirmResultV1 result{};
  result.precondition = ReadActivityStage1OptionV1(env, expected);
  if (result.precondition.status !=
          ActivityStage1OptionReadStatusV1::observed ||
      !result.precondition.generic_feast_confirm_ready ||
      env.set_stage_two == nullptr)
    return result;
  constexpr std::array<std::uint8_t, 10> kStageSetterSignature{
      0x40, 0x53, 0x48, 0x83, 0xEC, 0x20, 0x8B, 0x81, 0xB0, 0x1A};
  std::uintptr_t stage_notification = 0;
  if (!MatchCode(env.diagnostic, kSetStageRva, kStageSetterSignature) ||
      !ReadAt(env.diagnostic, env.diagnostic.module_base,
              kPlannerVtable + 0xC8, stage_notification) ||
      stage_notification != env.diagnostic.module_base + 0x10AEC20)
    return result;
  NativeIdentity first{};
  std::uint8_t stage_auto = 1;
  if (!ResolveNative(env, expected, first) ||
      !ReadAt(env.diagnostic, first.planner, 0x1AD0, stage_auto) ||
      stage_auto != 0)
    return result;
  ActivityPlannerDiagFrameV1 immediate{};
  if (!env.diagnostic.read_frame(env.diagnostic.context, immediate) ||
      immediate != expected)
    return result;
  result.submitted = true;
  if (!env.set_stage_two(env.diagnostic.context, first.planner)) {
    result.status = ActivityStage1ConfirmStatusV1::native_transition_failed;
    return result;
  }
  const auto post = ReadActivityPlannerDiagV1(env.diagnostic, expected);
  result.stage_two_visible =
      post.status == ActivityPlannerDiagStatusV1::observed &&
      post.value.widget_attached && post.value.widget_visible &&
      post.value.stage == 2;
  NativeIdentity second{};
  ActivityPlannerDiagFrameV1 final_frame{};
  result.selected_option_retained =
      result.stage_two_visible && ResolveNative(env, expected, second, 2) &&
      first.actor == second.actor && first.planner == second.planner &&
      first.option == second.option && first.option_id == second.option_id;
  if (!result.selected_option_retained ||
      !env.diagnostic.read_frame(env.diagnostic.context, final_frame) ||
      final_frame != expected) {
    result.status = ActivityStage1ConfirmStatusV1::postcondition_failed;
    return result;
  }
  result.status = ActivityStage1ConfirmStatusV1::stage_two_verified;
  return result;
}

std::string_view ActivityStage1ConfirmStatusKeyV1(
    ActivityStage1ConfirmStatusV1 status) noexcept {
  switch (status) {
  case ActivityStage1ConfirmStatusV1::stage_two_verified:
    return "stage_two_verified";
  case ActivityStage1ConfirmStatusV1::precondition_rejected:
    return "precondition_rejected";
  case ActivityStage1ConfirmStatusV1::native_transition_failed:
    return "native_transition_failed";
  case ActivityStage1ConfirmStatusV1::postcondition_failed:
    return "postcondition_failed";
  }
  return "unknown";
}

std::string_view ActivityStage1OptionReadStatusKeyV1(
    ActivityStage1OptionReadStatusV1 status) noexcept {
  switch (status) {
  case ActivityStage1OptionReadStatusV1::observed: return "observed";
  case ActivityStage1OptionReadStatusV1::exact_build_rejected:
    return "exact_build_rejected";
  case ActivityStage1OptionReadStatusV1::callback_missing:
    return "callback_missing";
  case ActivityStage1OptionReadStatusV1::planner_unavailable:
    return "planner_unavailable";
  case ActivityStage1OptionReadStatusV1::not_feast_stage1:
    return "not_feast_stage1";
  case ActivityStage1OptionReadStatusV1::option_unavailable:
    return "option_unavailable";
  case ActivityStage1OptionReadStatusV1::option_identity_mismatch:
    return "option_identity_mismatch";
  case ActivityStage1OptionReadStatusV1::option_key_unavailable:
    return "option_key_unavailable";
  case ActivityStage1OptionReadStatusV1::native_evaluation_failed:
    return "native_evaluation_failed";
  case ActivityStage1OptionReadStatusV1::frame_changed:
    return "frame_changed";
  }
  return "unknown";
}

} // namespace xar::bridge
