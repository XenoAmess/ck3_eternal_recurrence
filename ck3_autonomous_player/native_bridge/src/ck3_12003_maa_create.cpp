#include "xar_bridge/ck3_12003_maa_create.hpp"

#include <cstddef>
#include <cstring>

namespace xar::ck3_12003 {
namespace {

constexpr std::string_view kExecutableSha256 =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
constexpr std::int32_t kRobertCharacterId = 29829;
constexpr std::uint32_t kGdboMagic = 0x4744624F;
constexpr std::uint32_t kNormalSubmitFlags = 0x0E;

using NativeClone = void **(*)(const void *, void **);
using NativeDeletingDestructor = void *(*)(void *, std::uint32_t);

enum class Stage {
  binding,
  actor,
  type,
  constructor,
  validator,
  clone,
  submit,
  done
};

struct NativeExecution {
  std::uint64_t receiver[0xF8 / sizeof(std::uint64_t)]{};
  std::uint64_t command[0x38 / sizeof(std::uint64_t)]{};
  void *owning_command = nullptr;
  bool constructed = false;
  bool can_create_observed = false;
  bool can_create = false;
  bool submitted_observed = false;
  bool accepted = false;
  bool pointer_consumed = false;
  Stage stage = Stage::binding;
  const char *reason = "native_bindings_unavailable";
};

template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T output;
  std::memcpy(&output, static_cast<const unsigned char *>(object) + offset,
              sizeof(output));
  return output;
}

bool RunNative(const NativeMaaCreateBindings &bindings,
               const game::NativeMaaRegularPersonalCreateRequestV1 &request,
               NativeExecution &state) {
  if (!bindings.enabled || !bindings.current_player_full_id_slot ||
      !bindings.type_registry_slot || !bindings.type_lookup ||
      !bindings.regular_personal_constructor ||
      !bindings.regular_personal_can_create || !bindings.command_manager ||
      !bindings.submit) {
    return false;
  }
  state.stage = Stage::actor;
  state.reason = "current_player_unavailable";
  const auto current_player = *bindings.current_player_full_id_slot;
  if (current_player != kRobertCharacterId ||
      request.owner_character_id != current_player) {
    state.reason = "current_player_mismatch";
    return false;
  }

  state.stage = Stage::type;
  state.reason = "native_type_unavailable";
  const void *registry = *bindings.type_registry_slot;
  if (!registry) {
    return false;
  }
  const auto type_count = Load<std::int32_t>(registry, 0x5C);
  if (request.type_index < 0 || request.type_index >= type_count) {
    return false;
  }
  const void *type = bindings.type_lookup(registry, request.type_index);
  if (!type || Load<std::int32_t>(type, 0x10) != request.type_index ||
      Load<std::uint32_t>(type, 0x38) != kGdboMagic) {
    return false;
  }

  const std::int32_t personal_scope = -1;
  std::memcpy(reinterpret_cast<unsigned char *>(state.receiver) + 0xF0,
              &personal_scope, sizeof(personal_scope));
  state.stage = Stage::constructor;
  state.reason = "native_constructor_unavailable";
  if (bindings.regular_personal_constructor(state.receiver, state.command,
                                             type) != state.command) {
    return false;
  }
  state.constructed = true;

  state.stage = Stage::validator;
  state.reason = "native_validator_unavailable";
  state.can_create =
      bindings.regular_personal_can_create(state.command, nullptr);
  state.can_create_observed = true;
  if (!state.can_create) {
    state.reason = "native_denied";
    return true;
  }

  state.stage = Stage::clone;
  state.reason = "native_clone_unavailable";
  const void *primary = Load<const void *>(state.command, 0);
  if (!primary) {
    return false;
  }
  const auto clone = Load<NativeClone>(primary, 0x40);
  if (!clone || clone(state.command, &state.owning_command) !=
                    &state.owning_command ||
      !state.owning_command) {
    return false;
  }

  state.stage = Stage::submit;
  state.reason = "native_submit_unavailable";
  state.accepted = bindings.submit(bindings.command_manager,
                                  &state.owning_command, kNormalSubmitFlags);
  state.submitted_observed = true;
  state.pointer_consumed = state.owning_command == nullptr;
  if (!state.pointer_consumed) {
    state.reason = "native_submit_ownership_not_consumed";
    return false;
  }
  state.reason = state.accepted ? "" : "native_queue_rejected";
  state.stage = Stage::done;
  return true;
}

bool ProtectedRun(const NativeMaaCreateBindings &bindings,
                  const game::NativeMaaRegularPersonalCreateRequestV1 &request,
                  NativeExecution &state) noexcept {
#if defined(_MSC_VER)
  __try {
    return RunNative(bindings, request, state);
  } __except (1) {
    return false;
  }
#else
  try {
    return RunNative(bindings, request, state);
  } catch (...) {
    return false;
  }
#endif
}

bool DestroyNativeObject(void *command, std::uint32_t flags) noexcept {
#if defined(_MSC_VER)
  __try {
#else
  try {
#endif
    const void *primary = Load<const void *>(command, 0);
    if (!primary) {
      return false;
    }
    const auto destroy = Load<NativeDeletingDestructor>(primary, 0);
    if (!destroy) {
      return false;
    }
    destroy(command, flags);
    return true;
#if defined(_MSC_VER)
  } __except (1) {
#else
  } catch (...) {
#endif
    return false;
  }
}

} // namespace

NativeMaaCreateBindings BindNativeMaaCreateImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  NativeMaaCreateBindings bindings;
  if (!image_base || executable_sha256 != kExecutableSha256) {
    return bindings;
  }
  bindings.current_player_full_id_slot =
      reinterpret_cast<const std::int32_t *>(image_base + 0x54DBC00);
  bindings.type_registry_slot =
      reinterpret_cast<void **>(image_base + 0x5C67558);
  bindings.type_lookup =
      reinterpret_cast<NativeMaaCreateTypeLookup>(image_base + 0x1AD5540);
  bindings.regular_personal_constructor =
      reinterpret_cast<NativeMaaCreateConstructor>(image_base + 0x1338F90);
  bindings.regular_personal_can_create =
      reinterpret_cast<NativeMaaCreateCanCreate>(image_base + 0x296F9F0);
  bindings.command_manager = reinterpret_cast<void *>(image_base + 0x5CC1240);
  bindings.submit =
      reinterpret_cast<NativeMaaCreateSubmit>(image_base + 0x37F06F0);
  bindings.enabled = true;
  return bindings;
}

game::NativeMaaRegularPersonalCreateSubmissionV1
SubmitNativeMaaRegularPersonalCreateV1(
    const NativeMaaCreateBindings &bindings,
    const game::NativeMaaRegularPersonalCreateRequestV1 &request) noexcept {
  game::NativeMaaRegularPersonalCreateSubmissionV1 output;
  output.owner_character_id = request.owner_character_id;
  output.type_index = request.type_index;
  NativeExecution state;
  const bool completed = ProtectedRun(bindings, request, state);

  bool cleanup_completed = true;
  if (state.owning_command) {
    cleanup_completed = DestroyNativeObject(state.owning_command, 1);
    state.owning_command = nullptr;
  }
  if (state.constructed) {
    const bool stack_cleaned = DestroyNativeObject(state.command, 0);
    cleanup_completed = stack_cleaned && cleanup_completed;
  }

  output.reason = state.reason;
  if (state.can_create_observed) {
    output.native_can_create = state.can_create;
  }
  if (state.submitted_observed) {
    output.native_submit_accepted = state.accepted;
    output.command_pointer_consumed = state.pointer_consumed;
  }
  if (!completed) {
    return output;
  }
  if (!cleanup_completed && !state.submitted_observed) {
    output.reason = "native_command_cleanup_unavailable";
    return output;
  }
  if (state.submitted_observed && state.accepted && state.pointer_consumed) {
    output.status = "queued_pending";
    // Once ownership moved, a later stack-cleanup problem does not undo ACK.
    if (!cleanup_completed) {
      output.reason = "native_stack_cleanup_unavailable";
    }
  } else {
    output.status = "rejected";
  }
  return output;
}

} // namespace xar::ck3_12003
