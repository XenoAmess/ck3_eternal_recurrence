#include "xar_bridge/prewar_selected_declaration12004.hpp"

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_holy_war.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstring>
#include <limits>
#include <type_traits>
#include <vector>

#if defined(_MSC_VER)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace xar::ck3_12004 {
namespace {
namespace declaration = ck3_12002;

// Actual4 bounded source pins, reused with its exact-build profile:
//   common scope 2A814E0: RDX -> key5D4BD94, R8 -> key5D4BD98.
//   initializer9D80: LEA9D84 -> 449DD40 "attacker\0", length8;
//     LEA9DB5/9DC6 -> 5D4BD94, intern call9DBC -> 3F8A490.
//   initializer9DE0: LEA9DE4 -> 449DD30 "defender\0", length8;
//     LEA9E15/9E26 -> 5D4BD98, intern call9E1C -> 3F8A490.
//   actual vtable452FFD0+40 -> 277F130: 277F16D loads R8D=recipient,
//     277F174 loads EDX=additional, 277F18A calls War builder2A7EE30;
//     the returned object is checked for the native CWar magic/full WarID.
// The .3 cached startup window located these two common initializers. Actual4
// verification read1124B including PE metadata/code/strings and the builder
// callsite, no whole-image hash/export. The common wrapper has no CB-key branch.

struct NativeAccessFailure {};

// These leaves contain only trivial locals. An AV becomes an ordinary result
// before crossing the C++ owners, so /EHsc does not skip this reader's RAII.
bool GuardedCopy(void *destination, const void *source, std::size_t size) noexcept {
  if (size == 0) return true;
  if (!destination || !source) return false;
#if defined(_MSC_VER)
  __try {
    std::memcpy(destination, source, size);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  std::memcpy(destination, source, size);
  return true;
#endif
}

template <class Fn, class... Args>
bool GuardedNativeCall(Fn function, Args... args) noexcept {
  static_assert((std::is_trivially_copyable_v<Args> && ...));
#if defined(_MSC_VER)
  __try { function(args...); return true; }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  function(args...);
  return true;
#endif
}
template <class T, class Fn, class... Args>
bool GuardedNativeResult(T &value, Fn function, Args... args) noexcept {
  static_assert(std::is_trivially_copyable_v<T>);
  static_assert((std::is_trivially_copyable_v<Args> && ...));
#if defined(_MSC_VER)
  __try { value = function(args...); return true; }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  value = function(args...);
  return true;
#endif
}
template <class Fn, class... Args>
auto NativeResult(Fn function, Args... args) -> std::invoke_result_t<Fn, Args...> {
  std::invoke_result_t<Fn, Args...> value{};
  if (!GuardedNativeResult(value, function, args...)) throw NativeAccessFailure{};
  return value;
}
template <class Fn, class... Args>
void NativeCall(Fn function, Args... args) {
  if (!GuardedNativeCall(function, args...)) throw NativeAccessFailure{};
}
bool GuardedConsume(ConsumePrewarSelectedDeclaration12004 consume,
    void *consumer_context, const PrewarSelectedDeclarationNativeScope12004 *scope,
    const PrewarSelectedDeclarationObservation12004 *observation,
    bool &completed) noexcept {
#if defined(_MSC_VER)
  __try { completed = consume(consumer_context, *scope, *observation); return true; }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  completed = consume(consumer_context, *scope, *observation);
  return true;
#endif
}

// These outer callbacks are also guarded to preserve this leaf's C++ output
// lifetime. Their existing providers retain their own independent exception
// qualification; this does not repair their internal native/temporary owners.
bool GuardedCapture(ck3_12002::QueryMailboxEnvelope *envelope,
                    game::Snapshot *snapshot, bool &captured) noexcept {
#if defined(_MSC_VER)
  __try { captured = ck3_12002::CaptureQuerySnapshot(envelope, *snapshot); return true; }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  captured = ck3_12002::CaptureQuerySnapshot(envelope, *snapshot);
  return true;
#endif
}
bool Capture(ck3_12002::QueryMailboxEnvelope &envelope, game::Snapshot &snapshot) {
  bool captured = false;
  if (!GuardedCapture(&envelope, &snapshot, captured)) throw NativeAccessFailure{};
  return captured;
}
bool GuardedCatalogue(const game::GameAdapter *adapter, std::int32_t target,
    std::vector<game::DeclarableWarSnapshot> *rows,
    game::ReadDeclarableWarsResult &result) noexcept {
#if defined(_MSC_VER)
  __try { result = game::ReadDeclarableWarsForTarget(*adapter, target, *rows); return true; }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  result = game::ReadDeclarableWarsForTarget(*adapter, target, *rows);
  return true;
#endif
}

template <class T> T Load(const void *base, std::size_t offset) {
  T value{};
  if (!base || !GuardedCopy(&value, static_cast<const std::byte *>(base) + offset, sizeof(T)))
    throw NativeAccessFailure{};
  return value;
}
template <class T> void Store(void *base, std::size_t offset, T value) {
  if (!base || !GuardedCopy(static_cast<std::byte *>(base) + offset, &value, sizeof(T)))
    throw NativeAccessFailure{};
}

bool Fail(PrewarSelectedDeclarationObservation12004 &out,
          std::string_view reason) {
  out.available = false;
  out.failure.assign(reason);
  return false;
}

bool IntArray(const void *array, std::vector<std::int32_t> &out) {
  const auto capacity = Load<std::int32_t>(array, 8);
  const auto count = Load<std::int32_t>(array, 12);
  const auto *data = Load<const std::int32_t *>(array, 0);
  if (capacity < 0 || count < 0 || count > capacity || count > 1'000'000 ||
      (count != 0 && data == nullptr)) return false;
  out.resize(static_cast<std::size_t>(count));
  if (count != 0 && !GuardedCopy(out.data(), data,
          static_cast<std::size_t>(count) * sizeof(std::int32_t)))
    throw NativeAccessFailure{};
  return true;
}

bool TypeKey(const void *type, std::string &out) {
  const auto *storage = static_cast<const std::byte *>(type) + 0x18;
  const auto size = Load<std::size_t>(storage, 0x10);
  const auto capacity = Load<std::size_t>(storage, 0x18);
  if (size > capacity || size > 4096) return false;
  const auto *data = capacity <= 15 ? reinterpret_cast<const char *>(storage)
                                  : Load<const char *>(storage, 0);
  if (size != 0 && data == nullptr) return false;
  out.resize(size);
  if (size != 0 && !GuardedCopy(out.data(), data, size)) throw NativeAccessFailure{};
  return true;
}

bool Scratch(const declaration::DeclarationsBindings &b, void *&data,
             std::int32_t &count) {
  data = Load<void *>(b.configuration_scratch, 0);
  const auto capacity = Load<std::int32_t>(b.configuration_scratch, 8);
  count = Load<std::int32_t>(b.configuration_scratch, 12);
  return capacity >= 0 && count >= 0 && count <= capacity && count <= 10'000 &&
         (count == 0 || data != nullptr);
}
bool ClearScratch(const declaration::DeclarationsBindings &b) noexcept {
  try {
    void *data = nullptr;
    std::int32_t count = 0;
    if (!Scratch(b, data, count)) return false;
    for (std::int32_t i = 0; i < count; ++i)
      if (!GuardedNativeCall(b.destroy_configuration, static_cast<std::byte *>(data) +
              static_cast<std::size_t>(i) * declaration::kDeclarationsConfigurationSize)) return false;
    Store(b.configuration_scratch, 12, std::int32_t{0});
    return true;
  } catch (...) { return false; }
}

struct ScratchOwner {
  const declaration::DeclarationsBindings &bindings;
  PrewarSelectedDeclarationObservation12004 *observation;
  bool active = true;
  bool completed = false;
  ~ScratchOwner() { (void)finish(); }
  bool finish() noexcept {
    if (!active) return completed;
    // A partial native destruction must never be retried on the same objects.
    active = false;
    completed = ClearScratch(bindings);
    observation->scratch_cleanup_completed = completed;
    if (!completed) observation->available = false;
    return completed;
  }
};
struct alignas(8) ContextStorage {
  std::array<std::byte, declaration::kDeclarationsContextSize> bytes{};
};
static_assert(sizeof(ContextStorage) == 0x338);
struct ContextOwner {
  const declaration::DeclarationsBindings &bindings;
  void *context;
  PrewarSelectedDeclarationObservation12004 *observation;
  bool active = true;
  ~ContextOwner() { finish(); }
  bool finish() noexcept {
    if (!active) return observation->context_cleanup_completed;
    active = false;
    observation->context_cleanup_completed = GuardedNativeCall(bindings.destroy_context, context);
    if (!observation->context_cleanup_completed) observation->available = false;
    return observation->context_cleanup_completed;
  }
};

// Reconstruct the already-adopted actual4 readonly profile for an exact
// pointer equality gate. Command/payment fields are intentionally unconsumed.
bool ExactBindings(const declaration::DeclarationsBindings &b,
                   std::uintptr_t &base) noexcept {
  if (!b.enabled || !b.core.enabled || b.war_declaration_vtable < 0x452FFD0)
    return false;
  base = b.war_declaration_vtable - 0x452FFD0;
  const auto exact = BindOrdinaryHolyWarDeclarationsImage12004(base, kExecutableSha256);
  return exact.enabled && b.core.game_state_slot == exact.core.game_state_slot &&
      b.core.jomini_state_slot == exact.core.jomini_state_slot &&
      b.core.character_storage_slot == exact.core.character_storage_slot &&
      b.configuration_scratch == exact.configuration_scratch &&
      b.get_cb_database == exact.get_cb_database &&
      b.get_interaction_database == exact.get_interaction_database &&
      b.evaluate_cb == exact.evaluate_cb &&
      b.destroy_configuration == exact.destroy_configuration &&
      b.construct_context == exact.construct_context &&
      b.refresh_context == exact.refresh_context &&
      b.finalize_context == exact.finalize_context &&
      b.validate_context == exact.validate_context &&
      b.destroy_context == exact.destroy_context &&
      b.copy_int_array == exact.copy_int_array &&
      b.append_int_array == exact.append_int_array &&
      b.war_declaration_vtable == exact.war_declaration_vtable;
}

bool CatalogueMatches(ck3_12002::QueryMailboxEnvelope &envelope,
                      const game::DeclarableWarSnapshot &selected) {
  std::vector<game::DeclarableWarSnapshot> rows;
  game::ReadDeclarableWarsResult result = game::ReadDeclarableWarsResult::unavailable;
  if (!ck3_12002::IsQueryOwningThread(&envelope)) return false;
  if (!GuardedCatalogue(envelope.game, selected.target_character_id, &rows, result))
    throw NativeAccessFailure{};
  if (result != game::ReadDeclarableWarsResult::available ||
      std::count(rows.begin(), rows.end(), selected) != 1) return false;
  // The public token omits claimant/key/titles. Both the complete value and
  // its token must identify one row, so no competing selection can alias it.
  return std::count_if(rows.begin(), rows.end(), [&](const auto &row) {
    return row.target_character_id == selected.target_character_id &&
        row.casus_belli_index == selected.casus_belli_index &&
        row.configuration_index == selected.configuration_index;
  }) == 1;
}

bool SelectedScratchMatches(const declaration::DeclarationsBindings &b,
    void *type, const game::DeclarableWarSnapshot &selected) {
  void *data = nullptr;
  std::int32_t count = 0;
  std::string key;
  if (!Scratch(b, data, count) || !TypeKey(type, key) || key != selected.casus_belli_key)
    return false;
  const bool combined = count == 0 ||
      (Load<std::uint32_t>(type, declaration::kDeclarationsCbFlagsOffset) & (1U << 20));
  game::DeclarableWarSnapshot actual = selected;
  actual.target_title_ids.clear();
  if (combined) {
    if (selected.configuration_index != -1 || selected.claimant_character_id != -1)
      return false;
    for (std::int32_t i = 0; i < count; ++i) {
      std::vector<std::int32_t> titles;
      if (!IntArray(static_cast<std::byte *>(data) +
              static_cast<std::size_t>(i) * declaration::kDeclarationsConfigurationSize + 8,
              titles)) return false;
      actual.target_title_ids.insert(actual.target_title_ids.end(), titles.begin(), titles.end());
    }
  } else {
    if (selected.configuration_index < 0 || selected.configuration_index >= count)
      return false;
    const auto *configuration = static_cast<const std::byte *>(data) +
        static_cast<std::size_t>(selected.configuration_index) * declaration::kDeclarationsConfigurationSize;
    actual.claimant_character_id = Load<std::int32_t>(configuration, 0);
    if (!IntArray(configuration + 8, actual.target_title_ids) || actual.target_title_ids.empty())
      return false;
  }
  return actual == selected;
}

bool ReadFinalizedSelection(const declaration::DeclarationsBindings &b,
    void *context, void *type, const game::DeclarableWarSnapshot &selected,
    PrewarSelectedDeclarationObservation12004 &out, void *&war, void *&titles) {
  war = Load<void *>(context, declaration::kDeclarationsSpecialDataOffset);
  if (!war || Load<std::uintptr_t>(war, 0) != b.war_declaration_vtable ||
      Load<void *>(war, declaration::kDeclarationsWarCbOffset) != type) return false;
  titles = static_cast<std::byte *>(war) + declaration::kDeclarationsWarTitlesOffset;
  game::DeclarableWarSnapshot actual = selected;
  if (!TypeKey(type, actual.casus_belli_key) || !IntArray(titles, actual.target_title_ids))
    return false;
  actual.claimant_character_id = Load<std::int32_t>(war, declaration::kDeclarationsWarClaimantOffset);
  if (actual != selected) return false;
  out.context_actor_character_id = Load<std::int32_t>(context, 0x2D8);
  out.context_recipient_character_id = Load<std::int32_t>(context, 0x2DC);
  out.context_additional_role_character_id = Load<std::int32_t>(context, 0x2EC);
  out.context_claimant_character_id = actual.claimant_character_id;
  return true;
}

void *LivingCharacter(const declaration::CoreBindings &core, std::int32_t id) {
  void *character = NativeResult(&ck3_12004::ResolveCoreCharacter, core, id);
  return character && Load<std::int32_t>(character, kCharacterFullIdOffset) == id &&
      Load<void *>(character, kCharacterDeathDataOffset) == nullptr ? character : nullptr;
}
} // namespace

bool ReadPrewarSelectedDeclaration12004(
    const declaration::DeclarationsBindings &b,
    ck3_12002::QueryMailboxEnvelope &envelope,
    std::string_view declaration_id, const game::DeclarableWarSnapshot &selected,
    PrewarSelectedDeclarationObservation12004 &out,
    ConsumePrewarSelectedDeclaration12004 consume,
    void *consumer_context) noexcept {
  out = {};
  try {
    out.snapshot_revision = envelope.expected_snapshot_revision;
    out.capture_epoch = envelope.execution_stamp.pump_epoch;
    out.declaration_id.assign(declaration_id);
    out.selected = selected;
    std::uintptr_t base = 0;
    const auto canonical = std::to_string(selected.target_character_id) + '-' +
        std::to_string(selected.casus_belli_index) + '-' + std::to_string(selected.configuration_index);
    if (!envelope.game || !game::IsCk3_12004Descriptor(envelope.game->descriptor()) ||
        envelope.snapshot_comparison != ck3_12002::QuerySnapshotComparison12002::full_snapshot ||
        !ck3_12002::IsQueryOwningThread(&envelope) || !ExactBindings(b, base) ||
        selected.target_character_id <= 0 || selected.casus_belli_index < 0 ||
        selected.configuration_index < -1 || selected.casus_belli_key.empty() ||
        declaration_id != canonical)
      return Fail(out, "selected_declaration_current_owner_unavailable");
    game::Snapshot before{};
    if (!Capture(envelope, before) ||
        before.played_character_id <= 0 || before.played_character_id > std::numeric_limits<std::int32_t>::max() ||
        before.date_raw < std::numeric_limits<std::int32_t>::min() ||
        before.date_raw > std::numeric_limits<std::int32_t>::max() || !CatalogueMatches(envelope, selected) ||
        !b.core.game_state_slot || Load<void *>(b.core.game_state_slot, 0) !=
            reinterpret_cast<void *>(envelope.execution_stamp.game_state))
      return Fail(out, "selected_declaration_frame_or_catalogue_changed");
    out.played_character_id = static_cast<std::int32_t>(before.played_character_id);
    out.date_raw = static_cast<std::int32_t>(before.date_raw);
    void *actor = LivingCharacter(b.core, out.played_character_id);
    void *target = LivingCharacter(b.core, selected.target_character_id);
    if (!actor || !target || actor == target)
      return Fail(out, "selected_declaration_actor_or_target_unavailable");
    void *database = NativeResult(b.get_cb_database);
    if (!database) return Fail(out, "selected_declaration_cb_database_unavailable");
    const auto count = Load<std::int32_t>(database, declaration::kDeclarationsCbCountOffset);
    void *types = Load<void *>(database, declaration::kDeclarationsCbArrayOffset);
    if (!types || count < 0 || count > 10'000 || selected.casus_belli_index >= count)
      return Fail(out, "selected_declaration_cb_index_unavailable");
    void *type = Load<void *>(types, static_cast<std::size_t>(selected.casus_belli_index) * sizeof(void *));
    void *rule = type ? Load<void *>(type, declaration::kDeclarationsCbRuleOffset) : nullptr;
    if (!rule || Load<std::uint8_t>(rule, declaration::kDeclarationsCbDisabledOffset) || !ClearScratch(b))
      return Fail(out, "selected_declaration_cb_or_scratch_unavailable");
    ScratchOwner scratch{b, &out};
    if (!NativeResult(b.evaluate_cb, type, actor, target, b.configuration_scratch, false, false,
            static_cast<void *>(nullptr)) ||
        !SelectedScratchMatches(b, type, selected))
      return Fail(out, "selected_declaration_fresh_configuration_changed");
    database = NativeResult(b.get_interaction_database);
    void *interaction = database ? Load<void *>(database, declaration::kDeclarationsInteractionOffset) : nullptr;
    if (!interaction) return Fail(out, "selected_declaration_interaction_unavailable");
    ContextStorage storage;
    void *context = storage.bytes.data();
    if (NativeResult(b.construct_context, context, interaction, out.played_character_id,
            selected.target_character_id, static_cast<void *>(nullptr), true) != context)
      return Fail(out, "selected_declaration_context_construction_failed");
    ContextOwner owner{b, context, &out};
    void *war = Load<void *>(context, declaration::kDeclarationsSpecialDataOffset);
    if (!war || Load<std::uintptr_t>(war, 0) != b.war_declaration_vtable)
      return Fail(out, "selected_declaration_payload_unavailable");
    Store(war, declaration::kDeclarationsWarCbOffset, type);
    void *titles = static_cast<std::byte *>(war) + declaration::kDeclarationsWarTitlesOffset;
    void *data = nullptr;
    std::int32_t configurations = 0;
    if (!Scratch(b, data, configurations)) return Fail(out, "selected_declaration_scratch_changed");
    for (std::int32_t i = 0; i < configurations; ++i) {
      if (selected.configuration_index >= 0 && i != selected.configuration_index) continue;
      const auto *source = static_cast<const std::byte *>(data) +
          static_cast<std::size_t>(i) * declaration::kDeclarationsConfigurationSize + 8;
      if (selected.configuration_index >= 0) NativeCall(b.copy_int_array, titles, source);
      else {
        const auto source_count = Load<std::int32_t>(source, 12);
        const auto *source_data = Load<const std::int32_t *>(source, 0);
        if (source_count) NativeCall(b.append_int_array, titles, Load<std::int32_t>(titles, 12),
                                     source_data, source_data + source_count);
      }
    }
    Store(war, declaration::kDeclarationsWarClaimantOffset, selected.claimant_character_id);
    if (!scratch.finish()) return Fail(out, "selected_declaration_scratch_cleanup_failed");
    NativeCall(b.refresh_context, context, true);
    NativeCall(b.finalize_context, context);
    out.final_can_send = NativeResult(b.validate_context, context, static_cast<void *>(nullptr));
    if (!ReadFinalizedSelection(b, context, type, selected, out, war, titles))
      return Fail(out, "selected_declaration_finalized_selection_changed");
    out.finalized_selection_ready = true;
    void *actual_actor = LivingCharacter(b.core, *out.context_actor_character_id);
    void *recipient = LivingCharacter(b.core, *out.context_recipient_character_id);
    void *additional = LivingCharacter(b.core, *out.context_additional_role_character_id);
    if (!actual_actor || !recipient || !additional || recipient == additional)
      return Fail(out, "selected_declaration_finalized_roles_unavailable");
    void *claimant = NativeResult(&ck3_12004::ResolveCoreCharacter,
        b.core, *out.context_claimant_character_id);
    out.claimant_uses_native_fallback = claimant == nullptr;
    if (!claimant) claimant = Load<void *>(reinterpret_cast<void *>(base + 0x5C67570), 0);
    if (!claimant) return Fail(out, "selected_declaration_native_claimant_fallback_unavailable");
    out.finalized_roles_ready = true;
    out.native_cb_attacker_character_id = out.context_additional_role_character_id;
    out.native_cb_defender_character_id = out.context_recipient_character_id;
    out.native_cb_role_names_ready = true;
    out.available = true;
    const auto frozen = out;
    void *const frozen_war = war;
    void *const frozen_titles = titles;
    if (consume) {
      out.consumer_invoked = true;
      const PrewarSelectedDeclarationNativeScope12004 scope{
          context, war, type, actual_actor, recipient, additional, claimant, titles};
      if (!GuardedConsume(consume, consumer_context, &scope, &frozen, out.consumer_completed))
        return Fail(out, "selected_declaration_consumer_native_fault");
      if (!out.consumer_completed) return Fail(out, "selected_declaration_consumer_unavailable");
    }
    PrewarSelectedDeclarationObservation12004 after_roles{};
    if (!ReadFinalizedSelection(b, context, type, selected, after_roles, war, titles) ||
        war != frozen_war || titles != frozen_titles ||
        after_roles.context_actor_character_id != frozen.context_actor_character_id ||
        after_roles.context_recipient_character_id != frozen.context_recipient_character_id ||
        after_roles.context_additional_role_character_id != frozen.context_additional_role_character_id ||
        after_roles.context_claimant_character_id != frozen.context_claimant_character_id ||
        LivingCharacter(b.core, *out.context_actor_character_id) != actual_actor ||
        LivingCharacter(b.core, *out.context_recipient_character_id) != recipient ||
        LivingCharacter(b.core, *out.context_additional_role_character_id) != additional)
      return Fail(out, "selected_declaration_consumer_role_or_selection_drift");
    void *claimant_after = NativeResult(&ck3_12004::ResolveCoreCharacter,
        b.core, *out.context_claimant_character_id);
    const bool fallback_after = claimant_after == nullptr;
    if (!claimant_after) claimant_after = Load<void *>(reinterpret_cast<void *>(base + 0x5C67570), 0);
    if (fallback_after != out.claimant_uses_native_fallback || claimant_after != claimant ||
        NativeResult(b.validate_context, context, static_cast<void *>(nullptr)) != *out.final_can_send)
      return Fail(out, "selected_declaration_claimant_or_final_validator_drift");
    if (!owner.finish()) return Fail(out, "selected_declaration_context_cleanup_failed");
    game::Snapshot after{};
    if (!Capture(envelope, after) || after != before ||
        !CatalogueMatches(envelope, selected))
      return Fail(out, "selected_declaration_final_frame_changed");
    out.available = true;
    return true;
  } catch (const NativeAccessFailure &) {
    out.available = false;
    out.failure = "selected_declaration_native_access_fault";
    return false;
  } catch (...) {
    out.available = false;
    out.failure = "selected_declaration_capture_exception";
    return false;
  }
}

} // namespace xar::ck3_12004
