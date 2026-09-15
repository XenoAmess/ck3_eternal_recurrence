#include "xar_bridge/player_lifestyle_window_source_adapter_v1.hpp"

#include <array>
#include <cstring>
#include <limits>

#if defined(_MSC_VER)
#if !defined(NOMINMAX)
#define NOMINMAX
#endif
#include <Windows.h>
#endif

namespace xar::ck3_11906 {
namespace {

using SourceResult = PlayerLifestyleWindowSourceReadResultV1;

struct RawSpanV1 {
  std::uintptr_t data = 0;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
};

static_assert(sizeof(void *) == 8,
              "player lifestyle source adapter is x64-only");
static_assert(sizeof(RawSpanV1) == 0x10);

bool CheckedAdd(std::uintptr_t base, std::size_t offset,
                std::uintptr_t &output) noexcept {
  if (base == 0 ||
      offset > std::numeric_limits<std::uintptr_t>::max() - base) {
    output = 0;
    return false;
  }
  output = base + offset;
  return true;
}

bool Read(const PlayerLifestyleWindowSourceAdapterAccessV1 &access,
          std::uintptr_t address, void *output, std::size_t size) noexcept {
  return access.read_memory != nullptr && address != 0 && output != nullptr &&
      size != 0 &&
      access.read_memory(access.context, address, output, size);
}

template <typename Value>
bool ReadAt(const PlayerLifestyleWindowSourceAdapterAccessV1 &access,
            std::uintptr_t base, std::size_t offset,
            Value &output) noexcept {
  std::uintptr_t address = 0;
  return CheckedAdd(base, offset, address) &&
      Read(access, address, &output, sizeof(output));
}

bool ReadPointer(
    const PlayerLifestyleWindowSourceAdapterAccessV1 &access,
    std::uintptr_t address, std::uintptr_t &output) noexcept {
  output = 0;
  return Read(access, address, &output, sizeof(output));
}

bool SameFunctionAddress(const void *function, std::uintptr_t address) noexcept {
  return function != nullptr &&
      reinterpret_cast<std::uintptr_t>(function) == address;
}

bool NextSerial(PlayerLifestyleWindowSourceAdapterStateV1 &state,
                std::uint64_t &output) noexcept {
  auto current = state.root_acquisition_serial.load(std::memory_order_acquire);
  for (;;) {
    if (current == std::numeric_limits<std::uint64_t>::max()) return false;
    if (state.root_acquisition_serial.compare_exchange_weak(
            current, current + 1, std::memory_order_acq_rel,
            std::memory_order_acquire)) {
      output = current + 1;
      return output != 0;
    }
  }
}

bool InvokeRttiCast(
    const PlayerLifestyleWindowSourceAdapterEnvironmentV1 &environment,
    void *source, void *source_type, void *target_type,
    void *&output) noexcept {
  output = nullptr;
#if defined(_MSC_VER)
  __try {
    output = environment.rtti_dynamic_cast(
        source, 0, source_type, target_type, 0);
    return output != nullptr;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = nullptr;
    return false;
  }
#else
  output = environment.rtti_dynamic_cast(
      source, 0, source_type, target_type, 0);
  return output != nullptr;
#endif
}

bool InvokeDatabase(
    const PlayerLifestyleWindowSourceAdapterEnvironmentV1 &environment,
    void *&output) noexcept {
  output = nullptr;
#if defined(_MSC_VER)
  __try {
    output = environment.character_perk_database();
    return output != nullptr;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = nullptr;
    return false;
  }
#else
  output = environment.character_perk_database();
  return output != nullptr;
#endif
}

bool InvokeGate(PlayerLifestyleWindowFinalEvaluatorV1 evaluator,
                void *window, void *definition, bool &output) noexcept {
  output = false;
  if (evaluator == nullptr || window == nullptr || definition == nullptr) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
    output = evaluator(window, definition);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = false;
    return false;
  }
#else
  output = evaluator(window, definition);
  return true;
#endif
}

bool ReadStableKey(
    const PlayerLifestyleWindowSourceAdapterAccessV1 &access,
    std::uintptr_t object, std::size_t key_offset,
    game::PlayerLifestyleWindowStableKeyV1 &output) noexcept {
  output = {};
  std::uintptr_t native_string = 0;
  if (!CheckedAdd(object, key_offset, native_string)) return false;

  std::uint64_t size = 0;
  std::uint64_t capacity = 0;
  if (!ReadAt(access, native_string, 0x10, size) ||
      !ReadAt(access, native_string, 0x18, capacity) || size == 0 ||
      size > capacity ||
      size >= game::kPlayerLifestyleWindowStableKeyCapacityV1) {
    return false;
  }
  std::uintptr_t bytes = native_string;
  if (capacity > 15) {
    if (!ReadPointer(access, native_string, bytes) || bytes == 0) return false;
  }
  std::array<char, game::kPlayerLifestyleWindowStableKeyCapacityV1> value{};
  if (!Read(access, bytes, value.data(), static_cast<std::size_t>(size))) {
    return false;
  }
  return AssignPlayerLifestyleWindowStableKeyV1(
      std::string_view(value.data(), static_cast<std::size_t>(size)), output);
}

bool ReadSpan(
    const PlayerLifestyleWindowSourceAdapterAccessV1 &access,
    std::uintptr_t owner, std::size_t offset, std::size_t element_bytes,
    std::int32_t maximum_count, PlayerLifestyleWindowSpanV1 &output) noexcept {
  output = {};
  RawSpanV1 raw{};
  if (!ReadAt(access, owner, offset, raw) || raw.capacity < 0 ||
      raw.count < 0 || raw.count > raw.capacity ||
      raw.count > maximum_count ||
      (raw.count > 0 && raw.data == 0)) {
    return false;
  }
  output.data = raw.data;
  output.capacity = raw.capacity;
  output.count = raw.count;
  output.element_bytes = element_bytes;
  if (raw.count == 0) return true;
  const auto count = static_cast<std::uintptr_t>(raw.count);
  if (element_bytes == 0 ||
      count > std::numeric_limits<std::uintptr_t>::max() / element_bytes ||
      raw.data > std::numeric_limits<std::uintptr_t>::max() -
                     count * element_bytes) {
    return false;
  }

  std::array<std::byte, kLifestyleWindowPerkTreeRowBytesV1> row{};
  if (element_bytes > row.size()) return false;
  for (std::int32_t index = 0; index < raw.count; ++index) {
    std::uintptr_t address = 0;
    if (!CheckedAdd(raw.data, static_cast<std::size_t>(index) * element_bytes,
                    address) ||
        !Read(access, address, row.data(), element_bytes)) {
      return false;
    }
  }
  output.complete_range_readable = true;
  return true;
}

bool ResolveCharacterRoundTrip(
    const PlayerLifestyleWindowSourceAdapterEnvironmentV1 &environment,
    const PlayerLifestyleWindowSourceAdapterAccessV1 &access,
    std::uint32_t full_id,
    std::uintptr_t *played_character = nullptr) noexcept {
  std::uintptr_t storage = 0;
  std::uintptr_t fallback = 0;
  if (!ReadPointer(access,
                   environment.module_base +
                       kLifestyleWindowCharacterStorageSlotRvaV1,
                   storage) ||
      !ReadPointer(access,
                   environment.module_base +
                       kLifestyleWindowCharacterFallbackSlotRvaV1,
                   fallback) ||
      storage == 0) {
    return false;
  }
  std::uintptr_t slots = 0;
  std::int32_t capacity = 0;
  if (!ReadAt(access, storage, kLifestyleWindowStorageSlotsOffsetV1, slots) ||
      !ReadAt(access, storage, kLifestyleWindowStorageCapacityOffsetV1,
              capacity) ||
      slots == 0 || capacity <= 0 ||
      capacity > kLifestyleWindowMaximumStorageSlotsV1) {
    return false;
  }
  const auto index = full_id & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity)) return false;
  std::uintptr_t object_slot = 0;
  if (!CheckedAdd(
          slots,
          static_cast<std::size_t>(index) *
                  kLifestyleWindowStorageSlotStrideV1 +
              kLifestyleWindowStorageObjectOffsetV1,
          object_slot)) {
    return false;
  }
  std::uintptr_t character = 0;
  std::uint32_t observed_id = 0xFFFFFFFFU;
  const bool valid = ReadPointer(access, object_slot, character) && character != 0 &&
      character != fallback &&
      ReadAt(access, character, kLifestyleWindowCharacterIdentityOffsetV1,
             observed_id) &&
      observed_id == full_id;
  if (played_character != nullptr) *played_character = valid ? character : 0;
  return valid;
}

bool ValidateEvaluatorSlots(
    const PlayerLifestyleWindowSourceAdapterEnvironmentV1 &environment,
    const PlayerLifestyleWindowSourceAdapterAccessV1 &access) noexcept {
  std::uintptr_t focus = 0;
  std::uintptr_t perk = 0;
  return ReadPointer(
             access,
             environment.module_base +
                 kLifestyleWindowCanSelectFocusEvaluatorSlotRvaV1,
             focus) &&
      ReadPointer(access,
                  environment.module_base +
                      kLifestyleWindowCanSelectPerkEvaluatorSlotRvaV1,
                  perk) &&
      focus == environment.module_base +
                   kLifestyleWindowCanSelectFocusEvaluatorTargetRvaV1 &&
      perk == environment.module_base +
                  kLifestyleWindowCanSelectPerkEvaluatorTargetRvaV1;
}

bool MaterializeLifestyleContainer(
    const PlayerLifestyleWindowSourceAdapterAccessV1 &access,
    const PlayerLifestyleWindowSpanV1 &span) noexcept {
  for (std::int32_t index = 0; index < span.count; ++index) {
    std::uintptr_t row = 0;
    std::uintptr_t lifestyle = 0;
    game::PlayerLifestyleWindowStableKeyV1 key{};
    if (!CheckedAdd(span.data,
                    static_cast<std::size_t>(index) * sizeof(std::uintptr_t),
                    row) ||
        !ReadPointer(access, row, lifestyle) || lifestyle == 0 ||
        !ReadStableKey(access, lifestyle, kLifestyleWindowStableKeyOffsetV1,
                       key)) {
      return false;
    }
  }
  return true;
}

SourceResult MaterializeFocuses(
    const PlayerLifestyleWindowSourceAdapterEnvironmentV1 &environment,
    const PlayerLifestyleWindowSourceAdapterAccessV1 &access,
    PlayerLifestyleWindowSourceSampleV1 &output) noexcept {
  output.focus_count = static_cast<std::uint32_t>(output.focuses.count);
  for (std::uint32_t index = 0; index < output.focus_count; ++index) {
    auto &row = output.focus_rows[index];
    std::uintptr_t row_address = 0;
    std::uintptr_t lifestyle = 0;
    if (!CheckedAdd(output.focuses.data,
                    static_cast<std::size_t>(index) * sizeof(std::uintptr_t),
                    row_address) ||
        !ReadPointer(access, row_address, row.definition) ||
        row.definition == 0 ||
        !ReadStableKey(access, row.definition,
                       kLifestyleWindowStableKeyOffsetV1, row.key) ||
        !ReadAt(access, row.definition,
                kLifestyleWindowFocusLifestyleOffsetV1, lifestyle) ||
        lifestyle == 0 ||
        !ReadStableKey(access, lifestyle, kLifestyleWindowStableKeyOffsetV1,
                       row.lifestyle_key)) {
      return SourceResult::materialization_unavailable;
    }
    row.pointer_in_captured_focus_span = true;
    row.stable_key_round_trip = true;
    if (!InvokeGate(environment.can_select_focus,
                    reinterpret_cast<void *>(output.window),
                    reinterpret_cast<void *>(row.definition),
                    row.can_select)) {
      return SourceResult::final_legality_evaluator_unavailable;
    }
    row.final_evaluator_invoked = true;
  }
  return SourceResult::success;
}

SourceResult MaterializePerks(
    const PlayerLifestyleWindowSourceAdapterEnvironmentV1 &environment,
    const PlayerLifestyleWindowSourceAdapterAccessV1 &access,
    PlayerLifestyleWindowSourceSampleV1 &output) noexcept {
  void *database_object = nullptr;
  if (!InvokeDatabase(environment, database_object)) {
    return SourceResult::materialization_unavailable;
  }
  const auto database = reinterpret_cast<std::uintptr_t>(database_object);
  PlayerLifestyleWindowSpanV1 database_span{};
  if (!ReadSpan(access, database, kLifestyleWindowDatabaseSpanOffsetV1,
                sizeof(std::uintptr_t),
                static_cast<std::int32_t>(
                    game::kPlayerLifestyleWindowMaximumPerksV1),
                database_span)) {
    return SourceResult::materialization_unavailable;
  }
  output.perk_count = static_cast<std::uint32_t>(database_span.count);
  for (std::uint32_t index = 0; index < output.perk_count; ++index) {
    auto &row = output.perk_rows[index];
    std::uintptr_t row_address = 0;
    std::uintptr_t lifestyle = 0;
    if (!CheckedAdd(database_span.data,
                    static_cast<std::size_t>(index) * sizeof(std::uintptr_t),
                    row_address) ||
        !ReadPointer(access, row_address, row.definition) ||
        row.definition == 0 ||
        !ReadStableKey(access, row.definition,
                       kLifestyleWindowStableKeyOffsetV1, row.key) ||
        !ReadAt(access, row.definition,
                kLifestyleWindowPerkLifestyleOffsetV1, lifestyle) ||
        lifestyle == 0 ||
        !ReadStableKey(access, lifestyle, kLifestyleWindowStableKeyOffsetV1,
                       row.lifestyle_key)) {
      return SourceResult::materialization_unavailable;
    }
    row.pointer_in_exact_perk_database = true;
    row.stable_key_round_trip = true;
    if (!InvokeGate(environment.can_select_perk,
                    reinterpret_cast<void *>(output.window),
                    reinterpret_cast<void *>(row.definition),
                    row.can_select)) {
      return SourceResult::final_legality_evaluator_unavailable;
    }
    row.final_evaluator_invoked = true;
    if (!InvokeGate(environment.can_select_perk_ignore_cost,
                    reinterpret_cast<void *>(output.window),
                    reinterpret_cast<void *>(row.definition),
                    row.can_select_ignore_cost)) {
      return SourceResult::final_legality_evaluator_unavailable;
    }
    row.ignore_cost_evaluator_invoked = true;
  }
  output.perk_database_fully_materialized = true;
  return SourceResult::success;
}

} // namespace

PlayerLifestyleWindowSourceAdapterEnvironmentV1
BindPlayerLifestyleWindowSourceAdapterEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept {
  PlayerLifestyleWindowSourceAdapterEnvironmentV1 output{};
  output.exact_build_admitted = exact_build_admitted;
  output.admitted_executable_sha256 = admitted_executable_sha256;
  output.module_base = module_base;
  if (module_base == 0) return output;
  output.rtti_dynamic_cast =
      reinterpret_cast<PlayerLifestyleWindowRttiDynamicCastV1>(
          module_base + kLifestyleWindowRttiDynamicCastRvaV1);
  output.character_perk_database =
      reinterpret_cast<PlayerLifestyleWindowGetDatabaseV1>(
          module_base + kLifestyleWindowCharacterPerkDatabaseRvaV1);
  output.can_select_focus =
      reinterpret_cast<PlayerLifestyleWindowFinalEvaluatorV1>(
          module_base + kLifestyleWindowCanSelectFocusRvaV1);
  output.can_select_perk =
      reinterpret_cast<PlayerLifestyleWindowFinalEvaluatorV1>(
          module_base + kLifestyleWindowCanSelectPerkRvaV1);
  output.can_select_perk_ignore_cost =
      reinterpret_cast<PlayerLifestyleWindowFinalEvaluatorV1>(
          module_base + kLifestyleWindowCanSelectPerkIgnoreCostRvaV1);
  return output;
}

bool PlayerLifestyleWindowSourceAdapterEnvironmentReadyV1(
    const PlayerLifestyleWindowSourceAdapterEnvironmentV1
        &environment) noexcept {
  if (!environment.exact_build_admitted ||
      environment.admitted_executable_sha256 !=
          kPlayerLifestyleWindowCandidatesExecutableSha256V1 ||
      environment.module_base == 0 ||
      environment.rtti_dynamic_cast == nullptr ||
      environment.character_perk_database == nullptr ||
      environment.can_select_focus == nullptr ||
      environment.can_select_perk == nullptr ||
      environment.can_select_perk_ignore_cost == nullptr) {
    return false;
  }
  if (environment.offline_fixture) return true;
  return SameFunctionAddress(
             reinterpret_cast<const void *>(environment.rtti_dynamic_cast),
             environment.module_base +
                 kLifestyleWindowRttiDynamicCastRvaV1) &&
      SameFunctionAddress(
          reinterpret_cast<const void *>(
              environment.character_perk_database),
          environment.module_base +
              kLifestyleWindowCharacterPerkDatabaseRvaV1) &&
      SameFunctionAddress(
          reinterpret_cast<const void *>(environment.can_select_focus),
          environment.module_base + kLifestyleWindowCanSelectFocusRvaV1) &&
      SameFunctionAddress(
          reinterpret_cast<const void *>(environment.can_select_perk),
          environment.module_base + kLifestyleWindowCanSelectPerkRvaV1) &&
      SameFunctionAddress(
          reinterpret_cast<const void *>(
              environment.can_select_perk_ignore_cost),
          environment.module_base +
              kLifestyleWindowCanSelectPerkIgnoreCostRvaV1);
}

PlayerLifestyleWindowSourceReadResultV1
ReadPlayerLifestyleWindowSourceAdapterV1(
    PlayerLifestyleWindowSourceAdapterStateV1 &state,
    const PlayerLifestyleWindowSourceAdapterEnvironmentV1 &environment,
    const PlayerLifestyleWindowSourceAdapterAccessV1 &access,
    std::uintptr_t requested_module_base,
    std::uint32_t played_character_id,
    PlayerLifestyleWindowSourceSampleV1 &output) noexcept {
  output = {};
  if (!PlayerLifestyleWindowSourceAdapterEnvironmentReadyV1(environment) ||
      access.read_memory == nullptr ||
      requested_module_base != environment.module_base ||
      played_character_id == 0xFFFFFFFFU ||
      !NextSerial(state, output.root_acquisition_serial)) {
    return SourceResult::source_read_failed;
  }

  if (!ReadPointer(access,
                   environment.module_base +
                       kLifestyleWindowGlobalRootPointerRvaV1,
                   output.root) ||
      output.root == 0 ||
      !ReadAt(access, output.root, kLifestyleWindowRootIdlerOffsetV1,
              output.idler_base) ||
      output.idler_base == 0) {
    return SourceResult::owner_path_unavailable;
  }
  void *idler_gfx = nullptr;
  if (!InvokeRttiCast(
          environment, reinterpret_cast<void *>(output.idler_base),
          reinterpret_cast<void *>(environment.module_base +
                                   kLifestyleWindowIdlerTypeDescriptorRvaV1),
          reinterpret_cast<void *>(
              environment.module_base +
              kLifestyleWindowIdlerGfxTypeDescriptorRvaV1),
          idler_gfx)) {
    return SourceResult::owner_path_unavailable;
  }
  output.idler_gfx = reinterpret_cast<std::uintptr_t>(idler_gfx);
  output.idler_exact_rtti_cast = true;
  if (!ReadAt(access, output.idler_gfx,
              kLifestyleWindowIdlerHandlerOffsetV1, output.handler) ||
      output.handler == 0 ||
      !ReadAt(access, output.handler, 0, output.handler_vtable) ||
      !ReadAt(access, output.handler,
              kLifestyleWindowHandlerOwnerSlotOffsetV1, output.window) ||
      output.window == 0 ||
      !ReadAt(access, output.window, 0, output.window_primary_vtable) ||
      !ReadAt(access, output.window,
              kLifestyleWindowSecondaryVtableOffsetV1,
              output.window_secondary_vtable) ||
      !ReadAt(access, output.window,
              kLifestyleWindowOwnerRoundTripOffsetV1,
              output.window_owner_round_trip) ||
      !ReadAt(access, output.window,
              kLifestyleWindowBoundCharacterIdOffsetV1,
              output.bound_character_id)) {
    return SourceResult::owner_path_unavailable;
  }
  std::uint32_t current_player_global = 0xFFFFFFFFU;
  if (!Read(access,
            environment.module_base +
                kLifestyleWindowPlayedCharacterIdGlobalRvaV1,
            &current_player_global, sizeof(current_player_global))) {
    return SourceResult::source_read_failed;
  }
  output.character_storage_round_trip =
      current_player_global == played_character_id &&
      ResolveCharacterRoundTrip(environment, access, played_character_id);

  // Return the acquired evidence to LIFE4 before touching any container or
  // final evaluator. LIFE4 assigns the precise owner/unbound typed failure.
  if (output.handler_vtable !=
          environment.module_base + kLifestyleWindowHandlerVtableRvaV1 ||
      output.window_primary_vtable !=
          environment.module_base + kLifestyleWindowPrimaryVtableRvaV1 ||
      output.window_secondary_vtable !=
          environment.module_base + kLifestyleWindowSecondaryVtableRvaV1 ||
      output.window_owner_round_trip != output.handler ||
      output.bound_character_id != played_character_id ||
      !output.character_storage_round_trip) {
    return SourceResult::success;
  }

  if (!ReadSpan(access, output.window,
                kLifestyleWindowLifestylesSpanOffsetV1,
                kLifestyleWindowPointerSpanElementBytesV1,
                kLifestyleWindowMaximumContainerRowsV1,
                output.lifestyles) ||
      !ReadSpan(access, output.window,
                kLifestyleWindowPerkTreeSpanOffsetV1,
                kLifestyleWindowPerkTreeRowBytesV1,
                kLifestyleWindowMaximumContainerRowsV1,
                output.perk_trees) ||
      !ReadSpan(access, output.window, kLifestyleWindowFocusSpanOffsetV1,
                kLifestyleWindowPointerSpanElementBytesV1,
                static_cast<std::int32_t>(
                    game::kPlayerLifestyleWindowMaximumFocusesV1),
                output.focuses)) {
    return SourceResult::invalid_container;
  }
  if (!MaterializeLifestyleContainer(access, output.lifestyles)) {
    return SourceResult::materialization_unavailable;
  }
  if (!ValidateEvaluatorSlots(environment, access)) {
    return SourceResult::final_legality_evaluator_unavailable;
  }
  if (const auto result = MaterializeFocuses(environment, access, output);
      result != SourceResult::success) return result;
  if (const auto result = MaterializePerks(environment, access, output);
      result != SourceResult::success) return result;
  return SourceResult::success;
}

bool ResolvePlayerLifestylePlayedCharacterV1(
    const PlayerLifestyleWindowSourceAdapterEnvironmentV1 &environment,
    const PlayerLifestyleWindowSourceAdapterAccessV1 &access,
    std::uint32_t full_id,
    std::uintptr_t &played_character) noexcept {
  played_character = 0;
  if (full_id == 0xFFFFFFFFU || environment.module_base == 0 ||
      access.read_memory == nullptr) {
    return false;
  }
  return ResolveCharacterRoundTrip(environment, access, full_id,
                                   &played_character);
}

} // namespace xar::ck3_11906
