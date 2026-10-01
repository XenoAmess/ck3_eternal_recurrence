#include "xar_bridge/ck3_12002_sway_command.hpp"

#include <bit>
#include <cstring>
#include <limits>

namespace xar::ck3_12002 {
namespace {
template <class T> T Load(const void *base, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(T));
  return value;
}
struct alignas(8) ContextStorage { std::array<std::byte, 0x338> bytes{}; };
struct alignas(8) SendStorage { std::array<std::byte, 0x368> bytes{}; };

bool FullId(std::int64_t value, std::int32_t &out) noexcept {
  if (value <= 0 || static_cast<std::uint64_t>(value) >=
      (std::numeric_limits<std::uint32_t>::max)()) return false;
  out = std::bit_cast<std::int32_t>(static_cast<std::uint32_t>(value));
  return true;
}
bool Ready(const SwayCommandBindingsV1 &b) noexcept {
  const auto &c = b.context;
  return b.enabled && c.enabled && c.core.enabled &&
      c.interaction_database_slot != nullptr && *c.interaction_database_slot != nullptr &&
      b.construct_two_roles != nullptr && b.shown != nullptr && b.valid != nullptr &&
      c.refresh != nullptr && c.finalize != nullptr && c.validate != nullptr &&
      c.destroy != nullptr && c.evaluate_cost != nullptr &&
      b.definition_primary_vtable != 0 && b.definition_secondary_vtable != 0;
}
bool SwayKey(const void *definition) noexcept {
  constexpr std::string_view key = "sway_interaction";
  const auto size = Load<std::uint64_t>(definition, 0x28);
  const auto capacity = Load<std::uint64_t>(definition, 0x30);
  if (size != key.size() || capacity < size) return false;
  const char *data = capacity < 16 ?
      static_cast<const char *>(definition) + 0x18 : Load<const char *>(definition, 0x18);
  return data != nullptr && std::memcmp(data, key.data(), key.size()) == 0;
}
void *Definition(const SwayCommandBindingsV1 &b) noexcept {
  if (!Ready(b)) return nullptr;
  const auto *database = *b.context.interaction_database_slot;
  const auto count = Load<std::int32_t>(database, kSwayDatabaseCountOffset);
  const auto *rows = Load<void *const *>(database, kSwayDatabaseRowsOffset);
  if (count <= 0 || count > 4096 || rows == nullptr) return nullptr;
  void *selected = nullptr;
  for (std::int32_t i = 0; i < count; ++i) {
    void *row = rows[i];
    if (row == nullptr || !SwayKey(row)) continue;
    if (selected != nullptr || Load<std::uintptr_t>(row, 0) != b.definition_primary_vtable ||
        Load<std::uintptr_t>(row, kSwayDefinitionSecondaryOffset) != b.definition_secondary_vtable ||
        Load<std::uint32_t>(row, 0x38) != 0x4744624FU ||
        Load<std::int32_t>(row, 0x10) < 0) return nullptr;
    selected = row;
  }
  return selected;
}
bool Frame(const SwayCommandBindingsV1 &b, std::int32_t actor,
    std::int32_t target, CoreSnapshotPrefix &out) noexcept {
  if (!ReadCoreSnapshot(b.context.core, out) || !out.clock.paused || !out.map_ready ||
      !out.has_played_character || !out.played_character_alive ||
      out.played_character_id != actor || actor == target) return false;
  const auto *person = ResolveCoreCharacter(b.context.core, target);
  return person != nullptr && Load<void *>(person, kCharacterDeathDataOffset) == nullptr;
}
bool SameFrame(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.paused == b.clock.paused &&
      a.map_ready == b.map_ready && a.local_player_id == b.local_player_id &&
      a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id &&
      a.played_character_alive == b.played_character_alive;
}
bool ContextIdentity(const void *context, const void *definition,
    std::int32_t actor, std::int32_t target) noexcept {
  return Load<const void *>(context, 0) == definition &&
      Load<std::int32_t>(context, 0x2D8) == actor &&
      Load<std::int32_t>(context, 0x2DC) == target &&
      Load<std::int32_t>(context, 0x2E0) == -1 &&
      Load<std::int32_t>(context, 0x2E4) == -1 &&
      Load<std::int32_t>(context, 0x2E8) == -1 &&
      Load<std::int32_t>(context, 0x2EC) == actor;
}
bool Prepare(const SwayCommandBindingsV1 &b, void *definition,
    std::int32_t actor, std::int32_t target, ContextStorage &storage) noexcept {
  void *context = storage.bytes.data();
  if (b.construct_two_roles(context, definition, actor, target, nullptr, false) != context) {
    if (Load<void *>(context, 0) != nullptr) b.context.destroy(context);
    return false;
  }
  b.context.refresh(context, true);
  b.context.finalize(context);
  if (ContextIdentity(context, definition, actor, target)) return true;
  b.context.destroy(context);
  return false;
}
void Terms(const SwayCommandBindingsV1 &b, const CoreSnapshotPrefix &frame,
    std::int64_t actor, std::int64_t target, std::uint64_t epoch,
    void *context, SwayCommandTermsV1 &out) {
  auto &p = out.precondition;
  p.available = true; p.paused = true; p.capture_epoch = epoch;
  p.date_raw = frame.clock.date_raw; p.actor_character_id = actor;
  p.target_kind = bridge::ActiveSchemeStateV1PrivateTargetKind::character;
  p.target_id = target; p.interaction_key = "sway_interaction"; p.scheme_type_key = "sway";
  p.shown_evaluated = true; p.shown = b.shown(context);
  p.validity_evaluated = true; p.valid = b.valid(context, true, true, nullptr);
  out.final_legality_sampled = true;
  out.complete_can_send = b.context.validate(context, nullptr);
  // Historical semantic-action contract projects the complete Sway gate,
  // which includes stock can_start_scheme, rather than a dedicated denial.
  p.can_start_scheme_evaluated = true; p.can_start_scheme = out.complete_can_send;
  if (!out.complete_can_send) p.native_reason_key = "native_complete_validator_rejected";
  p.starter_options_evaluated = true;
  const auto unavailable = bridge::ActiveSchemeSemanticActionV1PrivatePreviewStatus::explicitly_unavailable;
  p.success_chance.status = unavailable; p.maximum_success_chance.status = unavailable;
  p.secrecy.status = unavailable;
  b.context.evaluate_cost(static_cast<const std::byte *>(Load<void *>(context, 0)) + 0x40,
      static_cast<const std::byte *>(context) + 0x08, out.send_costs_raw.data());
}
} // namespace

SwayCommandBindingsV1 BindSwayCommandImage(std::uintptr_t base, std::string_view sha) noexcept {
  SwayCommandBindingsV1 b{};
  b.context = BindContextImage(base, sha);
  if (!b.context.enabled) return b;
  b.enabled = true;
  b.construct_two_roles = reinterpret_cast<ConstructInteractionContext>(base + kConstructInteractionContextRva);
  b.shown = reinterpret_cast<SwayReadShownV1>(base + kSwayShownRva);
  b.valid = reinterpret_cast<SwayReadValidityV1>(base + kSwayValidityRva);
  b.definition_primary_vtable = base + kSwayDefinitionPrimaryVtableRva;
  b.definition_secondary_vtable = base + kSwayDefinitionSecondaryVtableRva;
  return b;
}

bool ReadSwayCommandTermsV1(const SwayCommandBindingsV1 &b, std::int64_t actor_value,
    std::int64_t target_value, std::uint64_t epoch, SwayCommandTermsV1 &out) noexcept {
  out = {};
  std::int32_t actor = -1, target = -1;
  CoreSnapshotPrefix before{}, after{};
  if (epoch == 0 || !Ready(b) || !FullId(actor_value, actor) || !FullId(target_value, target) ||
      !Frame(b, actor, target, before)) return false;
  void *definition = Definition(b);
  ContextStorage storage{};
  if (definition == nullptr || !Prepare(b, definition, actor, target, storage)) return false;
  bool evaluated = false;
  try { Terms(b, before, actor_value, target_value, epoch, storage.bytes.data(), out); evaluated = true; }
  catch (...) { out = {}; }
  b.context.destroy(storage.bytes.data());
  if (!evaluated || !Frame(b, actor, target, after) || !SameFrame(before, after)) {
    out = {}; return false;
  }
  return true;
}

SwayCommandSubmitResultV1 SubmitSwayCommandV1(const SwayCommandBindingsV1 &b,
    const bridge::ActiveSchemeSemanticActionV1PrivateCommand &command) noexcept {
  using Result = SwayCommandSubmitResultV1;
  if (command.interaction_key != "sway_interaction" || command.scheme_type_key != "sway" ||
      command.target_kind != bridge::ActiveSchemeStateV1PrivateTargetKind::character ||
      !command.selected_starter_package.empty()) return Result::rejected;
  std::int32_t actor = -1, target = -1;
  CoreSnapshotPrefix before{}, after{};
  const auto &c = b.context;
  if (!Ready(b) || !FullId(command.actor_character_id, actor) || !FullId(command.target_id, target) ||
      !Frame(b, actor, target, before) || !c.commands.enabled || c.construct_send_command == nullptr ||
      c.send_primary_vtable == 0 || c.send_secondary_vtable == 0) return Result::unavailable;
  void *definition = Definition(b);
  ContextStorage storage{};
  if (definition == nullptr || !Prepare(b, definition, actor, target, storage)) return Result::unavailable;
  void *context = storage.bytes.data();
  if (!b.shown(context) || !b.valid(context, true, true, nullptr) || !c.validate(context, nullptr)) {
    c.destroy(context); return Result::rejected;
  }
  if (!Frame(b, actor, target, after) || !SameFrame(before, after) || Definition(b) != definition) {
    c.destroy(context); return Result::unavailable;
  }
  SendStorage send{};
  void *native = send.bytes.data();
  const bool constructed = c.construct_send_command(native, context) == native;
  const bool identity = constructed && Load<std::uintptr_t>(native, 0) == c.send_primary_vtable &&
      Load<std::uintptr_t>(native, 0x18) == c.send_secondary_vtable &&
      ContextIdentity(static_cast<const std::byte *>(native) + 0x20, definition, actor, target);
  const auto result = identity ? SubmitCommandCopy(c.commands, native, 0x0E) :
      CommandSubmitResult::unavailable;
  if (constructed || Load<void *>(native, 0x20) != nullptr)
    c.destroy(static_cast<std::byte *>(native) + 0x20);
  c.destroy(context);
  return result == CommandSubmitResult::submitted ? Result::submitted :
      result == CommandSubmitResult::rejected ? Result::rejected : Result::unavailable;
}
} // namespace xar::ck3_12002
