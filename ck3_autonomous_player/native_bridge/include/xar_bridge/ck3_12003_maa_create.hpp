#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::game {

struct NativeMaaRegularPersonalCreateRequestV1 {
  std::int32_t owner_character_id = 29829;
  std::int32_t type_index = -1;
};

struct NativeMaaRegularPersonalCreateSubmissionV1 {
  std::int32_t schema_version = 1;
  std::string status = "unavailable";
  std::string reason;
  std::string command_class = "CCreateMAARegimentCommand";
  std::int32_t owner_character_id = -1;
  std::int32_t type_index = -1;
  std::optional<bool> native_can_create;
  std::optional<bool> native_submit_accepted;
  std::optional<bool> command_pointer_consumed;
};

} // namespace xar::game

namespace xar::ck3_12003 {

using NativeMaaCreateTypeLookup = const void *(*)(const void *, std::int32_t);
using NativeMaaCreateConstructor = void *(*)(const void *, void *, const void *);
using NativeMaaCreateCanCreate = bool (*)(const void *, void *);
using NativeMaaCreateSubmit = bool (*)(void *, void **, std::uint32_t);

struct NativeMaaCreateBindings {
  bool enabled = false;
  const std::int32_t *current_player_full_id_slot = nullptr;
  void **type_registry_slot = nullptr;
  NativeMaaCreateTypeLookup type_lookup = nullptr;
  NativeMaaCreateConstructor regular_personal_constructor = nullptr;
  NativeMaaCreateCanCreate regular_personal_can_create = nullptr;
  // Embedded manager object, not a pointer slot.
  void *command_manager = nullptr;
  NativeMaaCreateSubmit submit = nullptr;
};

NativeMaaCreateBindings BindNativeMaaCreateImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// Must execute in the existing paused main-thread command scope. A successful
// native queue result is queued_pending; this API does not observe creation.
game::NativeMaaRegularPersonalCreateSubmissionV1
SubmitNativeMaaRegularPersonalCreateV1(
    const NativeMaaCreateBindings &,
    const game::NativeMaaRegularPersonalCreateRequestV1 &) noexcept;

} // namespace xar::ck3_12003
