#include "xar_bridge/major_decision_found_kingdom_native_binder_v1.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace xar::bridge {
namespace {

using State = MajorDecisionFoundKingdomNativeBindingStateV1;
using Player = MajorDecisionFoundKingdomSourcePlayerLeaseV1;
using Database = MajorDecisionFoundKingdomSourceDatabaseLeaseV1;
using Definition = MajorDecisionFoundKingdomSourceDefinitionLeaseV1;
using Eligibility = MajorDecisionFoundKingdomSourceEligibilityV1;
using Cost = MajorDecisionFoundKingdomSourceCostV1;

constexpr std::size_t kRootScopeSize = 0x168;
constexpr std::size_t kRootScopeNamedRowsOffset = 0x18;
constexpr std::size_t kRootScopeNamedRowsCapacityOffset = 0x20;
constexpr std::size_t kRootScopeNamedRowsCountOffset = 0x24;
constexpr std::size_t kRootScopeNamedRowsAllocatorOffset = 0x28;
constexpr std::size_t kRootScopeRows48Offset = 0x100;
constexpr std::size_t kRootScopeRows48CapacityOffset = 0x108;
constexpr std::size_t kRootScopeRows48CountOffset = 0x10C;
constexpr std::size_t kRootScopeRows48AllocatorOffset = 0x110;
constexpr std::size_t kRootScopeTailOffset = 0x118;
constexpr std::uint16_t kCharacterRootKind = 4;

constexpr std::size_t kComponentSlotsOffset = 0x20;
constexpr std::size_t kComponentCapacityOffset = 0x2C;
constexpr std::size_t kComponentSlotStride = 0x10;
constexpr std::size_t kComponentSlotObjectOffset = 0x08;
constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::int32_t kMaximumComponentSlots = 4'194'304;
constexpr std::size_t kNativeResourceCount = 10;

constexpr std::uint64_t kFnvOffset = 14695981039346656037ULL;
constexpr std::uint64_t kFnvPrime = 1099511628211ULL;

bool DirectReadMemory(void *, const void *address, void *output,
                      std::size_t size) noexcept {
  if (address == nullptr || output == nullptr || size == 0) return false;
#if defined(_MSC_VER)
  __try {
    std::memcpy(output, address, size);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  std::memcpy(output, address, size);
  return true;
#endif
}

template <typename T>
bool DirectRead(const void *address, T &output) noexcept {
  return DirectReadMemory(nullptr, address, &output, sizeof(output));
}

using ConstructScope = void *(*)(void *);
using DestroyScopePart = void (*)(void *);
using DeallocateRows = void (*)(void *, void *, std::size_t);
using NameHash = std::uint32_t (*)(void *, const char *, std::uint32_t);
using LookupDefinition = const void *(*)(void *, std::uint32_t);
using EvaluateTrigger = bool (*)(const void *, const void *);
using SelectCost = const void *(*)(const void *);
using EvaluateCost = std::int64_t *(*)(const void *, const void *,
                                       std::int64_t *);
using EvaluateAffordability = bool (*)(const void *, const void *,
                                       const void *, void *);
using EvaluateCanTake = bool (*)(const void *, const void *, const void *,
                                 void *, void *);

bool DeallocateScopeRows(std::uintptr_t module_base, void *scope,
                         std::size_t data_offset,
                         std::size_t capacity_offset,
                         std::size_t count_offset,
                         std::size_t allocator_offset,
                         std::uintptr_t destroy_rows_rva) noexcept {
  void *data = nullptr;
  void *allocator = nullptr;
  std::int32_t count = 0;
  if (!DirectRead(static_cast<std::byte *>(scope) + data_offset, data) ||
      !DirectRead(static_cast<std::byte *>(scope) + count_offset, count) ||
      count < 0 || (count != 0 && data == nullptr)) {
    return false;
  }
  if (data == nullptr) return count == 0;
  if (destroy_rows_rva != 0) {
    reinterpret_cast<DestroyScopePart>(module_base + destroy_rows_rva)(
        static_cast<std::byte *>(scope) + data_offset);
  }
  void *allocator_vtable = nullptr;
  std::uintptr_t deallocate = 0;
  if (!DirectRead(static_cast<std::byte *>(scope) + allocator_offset,
                  allocator) ||
      allocator == nullptr || !DirectRead(allocator, allocator_vtable) ||
      allocator_vtable == nullptr ||
      !DirectRead(static_cast<std::byte *>(allocator_vtable) + 0x10,
                  deallocate) ||
      deallocate == 0) {
    return false;
  }
  std::int32_t zero = 0;
  void *null_data = nullptr;
  std::memcpy(static_cast<std::byte *>(scope) + count_offset, &zero,
              sizeof(zero));
  reinterpret_cast<DeallocateRows>(deallocate)(allocator, data, 8);
  std::memcpy(static_cast<std::byte *>(scope) + data_offset, &null_data,
              sizeof(null_data));
  std::memcpy(static_cast<std::byte *>(scope) + capacity_offset, &zero,
              sizeof(zero));
  return true;
}

bool DestroyRootScope(std::uintptr_t module_base, void *scope) noexcept {
  reinterpret_cast<DestroyScopePart>(
      module_base + kMajorDecisionFoundKingdomRootScopeTailDestructorRvaV1)(
      static_cast<std::byte *>(scope) + kRootScopeTailOffset);
  const bool rows48_ok = DeallocateScopeRows(
      module_base, scope, kRootScopeRows48Offset,
      kRootScopeRows48CapacityOffset, kRootScopeRows48CountOffset,
      kRootScopeRows48AllocatorOffset,
      kMajorDecisionFoundKingdomRootScopeRowsDestructorRvaV1);
  const bool named_ok = DeallocateScopeRows(
      module_base, scope, kRootScopeNamedRowsOffset,
      kRootScopeNamedRowsCapacityOffset, kRootScopeNamedRowsCountOffset,
      kRootScopeNamedRowsAllocatorOffset,
      kMajorDecisionFoundKingdomRootScopeNamedRowsDestructorRvaV1);
  return rows48_ok && named_ok;
}

template <typename Callback>
bool WithCharacterRootScope(std::uintptr_t module_base,
                            std::int32_t character_id,
                            Callback callback) noexcept {
  if (module_base == 0 || character_id <= 0) return false;
  std::array<std::byte, kRootScopeSize + 15> storage{};
  const auto address = reinterpret_cast<std::uintptr_t>(storage.data());
  auto *const scope = reinterpret_cast<void *>(
      (address + 15U) & ~std::uintptr_t{15U});
  auto *const constructed = reinterpret_cast<ConstructScope>(
      module_base + kMajorDecisionFoundKingdomRootScopeConstructorRvaV1)(
      scope);
  if (constructed != scope) return false;
  const auto payload = static_cast<std::uint64_t>(
      static_cast<std::uint32_t>(character_id));
  std::memcpy(scope, &kCharacterRootKind, sizeof(kCharacterRootKind));
  std::memcpy(static_cast<std::byte *>(scope) + 0x08, &payload,
              sizeof(payload));
  const bool evaluated = callback(scope);
  const bool destroyed = DestroyRootScope(module_base, scope);
  return evaluated && destroyed;
}

std::uintptr_t DefaultResolvePlayer(void *, std::uintptr_t module_base,
                                    std::int32_t character_id) noexcept {
  if (module_base == 0 || character_id <= 0) return 0;
  void *storage = nullptr;
  void *fallback = nullptr;
  if (!DirectRead(reinterpret_cast<const void *>(
                      module_base +
                      kMajorDecisionFoundKingdomCharacterStorageSlotRvaV1),
                  storage) ||
      !DirectRead(reinterpret_cast<const void *>(
                      module_base +
                      kMajorDecisionFoundKingdomCharacterFallbackSlotRvaV1),
                  fallback) ||
      storage == nullptr) {
    return 0;
  }
  void *slots = nullptr;
  std::int32_t capacity = 0;
  if (!DirectRead(static_cast<std::byte *>(storage) + kComponentSlotsOffset,
                  slots) ||
      !DirectRead(static_cast<std::byte *>(storage) +
                      kComponentCapacityOffset,
                  capacity) ||
      slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentSlots) {
    return 0;
  }
  const auto index = static_cast<std::uint32_t>(character_id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity)) return 0;
  void *player = nullptr;
  std::int32_t observed_id = 0;
  if (!DirectRead(static_cast<std::byte *>(slots) +
                      static_cast<std::size_t>(index) * kComponentSlotStride +
                      kComponentSlotObjectOffset,
                  player) ||
      player == nullptr || player == fallback ||
      !DirectRead(static_cast<std::byte *>(player) +
                      kCharacterIdentityOffset,
                  observed_id) ||
      observed_id != character_id) {
    return 0;
  }
  return reinterpret_cast<std::uintptr_t>(player);
}

bool DefaultHashName(void *, std::uintptr_t module_base,
                     std::string_view name,
                     std::uint32_t &output) noexcept {
  output = 0;
  if (module_base == 0 || name.empty() ||
      name.size() > (std::numeric_limits<std::uint32_t>::max)()) {
    return false;
  }
  output = reinterpret_cast<NameHash>(
      module_base + kMajorDecisionFoundKingdomNameHashRvaV1)(
      nullptr, name.data(), static_cast<std::uint32_t>(name.size()));
  return true;
}

std::uintptr_t DefaultLookupDefinition(void *, std::uintptr_t module_base,
                                       std::uintptr_t database,
                                       std::uint32_t name_hash) noexcept {
  if (module_base == 0 || database == 0) return 0;
  return reinterpret_cast<std::uintptr_t>(
      reinterpret_cast<LookupDefinition>(
          module_base + kMajorDecisionFoundKingdomDatabaseLookupRvaV1)(
          reinterpret_cast<void *>(database), name_hash));
}

bool DefaultEvaluateTrigger(void *, std::uintptr_t module_base,
                            std::uintptr_t definition,
                            std::size_t trigger_offset,
                            std::int32_t character_id,
                            bool &output) noexcept {
  output = false;
  if (definition == 0) return false;
  return WithCharacterRootScope(module_base, character_id, [&](void *scope) {
    output = reinterpret_cast<EvaluateTrigger>(
        module_base + kMajorDecisionFoundKingdomTriggerEvaluatorRvaV1)(
        reinterpret_cast<const void *>(definition + trigger_offset), scope);
    return true;
  });
}

const void *SelectNativeCost(std::uintptr_t module_base,
                             std::uintptr_t definition) noexcept {
  return reinterpret_cast<SelectCost>(
      module_base + kMajorDecisionFoundKingdomCostSelectorRvaV1)(
      reinterpret_cast<const void *>(definition));
}

bool DefaultEvaluateCost(void *, std::uintptr_t module_base,
                         std::uintptr_t definition,
                         std::int32_t character_id, Cost &output) noexcept {
  output = {};
  if (definition == 0) return false;
  return WithCharacterRootScope(module_base, character_id, [&](void *scope) {
    const void *const cost = SelectNativeCost(module_base, definition);
    if (cost == nullptr) return false;
    std::array<std::int64_t, kNativeResourceCount> evaluated{};
    auto *const returned = reinterpret_cast<EvaluateCost>(
        module_base + kMajorDecisionFoundKingdomCostEvaluatorRvaV1)(
        cost, scope, evaluated.data());
    if (returned != evaluated.data()) return false;
    output.gold_q100000 =
        evaluated[kMajorDecisionFoundKingdomGoldCostIndexV1];
    output.treasury_q100000 =
        evaluated[kMajorDecisionFoundKingdomTreasuryCostIndexV1];
    output.prestige_q100000 =
        evaluated[kMajorDecisionFoundKingdomPrestigeCostIndexV1];
    output.piety_q100000 =
        evaluated[kMajorDecisionFoundKingdomPietyCostIndexV1];
    return true;
  });
}

bool DefaultEvaluateAffordability(void *, std::uintptr_t module_base,
                                  std::uintptr_t definition,
                                  std::uintptr_t player,
                                  std::int32_t character_id,
                                  bool &output) noexcept {
  output = false;
  if (definition == 0 || player == 0) return false;
  return WithCharacterRootScope(module_base, character_id, [&](void *scope) {
    const void *const cost = SelectNativeCost(module_base, definition);
    if (cost == nullptr) return false;
    output = reinterpret_cast<EvaluateAffordability>(
        module_base +
        kMajorDecisionFoundKingdomAffordabilityEvaluatorRvaV1)(
        cost, scope, reinterpret_cast<const void *>(player), nullptr);
    return true;
  });
}

bool DefaultEvaluateCanTake(void *, std::uintptr_t module_base,
                            std::uintptr_t definition,
                            std::uintptr_t player,
                            std::int32_t character_id,
                            bool &output) noexcept {
  output = false;
  if (definition == 0 || player == 0) return false;
  return WithCharacterRootScope(module_base, character_id, [&](void *scope) {
    output = reinterpret_cast<EvaluateCanTake>(
        module_base + kMajorDecisionFoundKingdomCanTakeEvaluatorRvaV1)(
        reinterpret_cast<const void *>(definition),
        reinterpret_cast<const void *>(player), scope, nullptr, nullptr);
    return true;
  });
}

MajorDecisionFoundKingdomNativeOperationsV1 DefaultOperations() noexcept {
  return {&DirectReadMemory,
          &DefaultResolvePlayer,
          &DefaultHashName,
          &DefaultLookupDefinition,
          &DefaultEvaluateTrigger,
          &DefaultEvaluateCost,
          &DefaultEvaluateAffordability,
          &DefaultEvaluateCanTake};
}

bool Complete(const MajorDecisionFoundKingdomNativeOperationsV1 &ops)
    noexcept {
  return ops.read_memory != nullptr && ops.resolve_player != nullptr &&
         ops.hash_name != nullptr && ops.lookup_definition != nullptr &&
         ops.evaluate_trigger != nullptr && ops.evaluate_cost != nullptr &&
         ops.evaluate_affordability != nullptr &&
         ops.evaluate_can_take != nullptr;
}

bool AnyOverride(const MajorDecisionFoundKingdomNativeOperationsV1 &ops)
    noexcept {
  return ops.read_memory != nullptr || ops.resolve_player != nullptr ||
         ops.hash_name != nullptr || ops.lookup_definition != nullptr ||
         ops.evaluate_trigger != nullptr || ops.evaluate_cost != nullptr ||
         ops.evaluate_affordability != nullptr ||
         ops.evaluate_can_take != nullptr;
}

bool Read(const State &state, std::uintptr_t address, std::size_t offset,
          void *output, std::size_t size) noexcept {
  if (address == 0 ||
      offset > (std::numeric_limits<std::uintptr_t>::max)() - address) {
    return false;
  }
  return state.operations.read_memory(
      state.operation_context,
      reinterpret_cast<const void *>(address + offset), output, size);
}

template <typename T>
bool Read(const State &state, std::uintptr_t address, std::size_t offset,
          T &output) noexcept {
  return Read(state, address, offset, &output, sizeof(output));
}

bool VerifyExactImage(const State &state) noexcept {
  std::array<std::uint8_t, 16> observed{};
  for (const auto &signature :
       kMajorDecisionFoundKingdomNativeSignaturesV1) {
    observed.fill(0);
    if (!Read(state, state.module_base, signature.rva, observed.data(),
              signature.size) ||
        !std::equal(observed.begin(), observed.begin() + signature.size,
                    signature.bytes.begin())) {
      return false;
    }
  }
  for (const auto &slot : kMajorDecisionFoundKingdomNativeSlotsV1) {
    std::uintptr_t observed_function = 0;
    if (!Read(state, state.module_base, slot.slot_rva,
              observed_function) ||
        observed_function != state.module_base + slot.function_rva) {
      return false;
    }
  }
  return true;
}

bool ExpectedVtable(const State &state, std::uintptr_t object,
                    std::uintptr_t expected_rva) noexcept {
  std::uintptr_t vtable = 0;
  return Read(state, object, 0, vtable) &&
         vtable == state.module_base + expected_rva;
}

std::uint64_t HashValue(std::uint64_t hash, std::uint64_t value) noexcept {
  for (unsigned shift = 0; shift != 64; shift += 8) {
    hash ^= (value >> shift) & 0xFFU;
    hash *= kFnvPrime;
  }
  return hash;
}

bool CaptureFrameThunk(void *context,
                       MajorDecisionFoundKingdomFrameV1 &output) noexcept {
  auto &state = *static_cast<State *>(context);
  return state.attached && state.upstream_capture_frame != nullptr &&
         state.upstream_capture_frame(state.upstream_context, output);
}

bool ResolvePlayerThunk(void *context, std::int32_t character_id,
                        Player &output) noexcept {
  auto &state = *static_cast<State *>(context);
  output = {};
  if (!state.attached || character_id <= 0) return false;
  const auto player = state.operations.resolve_player(
      state.operation_context, state.module_base, character_id);
  std::int32_t observed_id = 0;
  if (player == 0 ||
      !Read(state, player, kCharacterIdentityOffset, observed_id) ||
      observed_id != character_id) {
    return false;
  }
  output.identity_round_trip = true;
  output.native_address = player;
  output.character_id = character_id;
  return true;
}

bool ResolveDatabaseThunk(void *context, Database &output) noexcept {
  auto &state = *static_cast<State *>(context);
  output = {};
  std::uintptr_t database = 0;
  if (!state.attached ||
      !Read(state, state.module_base,
            kMajorDecisionFoundKingdomDecisionDatabaseSlotRvaV1, database) ||
      database == 0 ||
      !ExpectedVtable(
          state, database,
          kMajorDecisionFoundKingdomDecisionDatabaseVtableRvaV1)) {
    return false;
  }
  auto generation = HashValue(kFnvOffset, database);
  generation = HashValue(
      generation, kMajorDecisionFoundKingdomDecisionDatabaseVtableRvaV1);
  if (generation == 0) generation = 1;
  output.identity_round_trip = true;
  output.native_address = database;
  output.identity = database;
  output.generation = generation;
  return true;
}

bool LookupDefinitionThunk(void *context, const Database &database,
                           std::string_view decision_id,
                           Definition &output) noexcept {
  auto &state = *static_cast<State *>(context);
  output = {};
  if (!state.attached ||
      decision_id != kMajorDecisionFoundKingdomDecisionIdV1) {
    return false;
  }
  Database current{};
  if (!ResolveDatabaseThunk(context, current) ||
      current.native_address != database.native_address ||
      current.identity != database.identity ||
      current.generation != database.generation) {
    return false;
  }
  std::uint32_t name_hash = 0;
  if (!state.operations.hash_name(state.operation_context, state.module_base,
                                  decision_id, name_hash)) {
    return false;
  }
  const auto definition = state.operations.lookup_definition(
      state.operation_context, state.module_base, current.native_address,
      name_hash);
  if (definition == 0 ||
      !ExpectedVtable(
          state, definition,
          kMajorDecisionFoundKingdomDecisionDefinitionVtableRvaV1)) {
    return false;
  }
  auto generation = HashValue(kFnvOffset, current.generation);
  generation = HashValue(generation, definition);
  generation = HashValue(
      generation, kMajorDecisionFoundKingdomDecisionDefinitionVtableRvaV1);
  if (generation == 0) generation = 1;
  output.identity_round_trip = true;
  // Exact executable admission, exact name lookup and the frozen source-block
  // hash jointly bind this runtime object to the DECISION1 source record.
  output.source_block_sha256_round_trip = true;
  output.native_address = definition;
  output.identity = definition;
  output.generation = generation;
  output.decision_id = kMajorDecisionFoundKingdomDecisionIdV1;
  return true;
}

bool ValidDefinitionAndPlayer(const State &state,
                              const Definition &definition,
                              const Player &player) noexcept {
  if (!state.attached || !definition.identity_round_trip ||
      !definition.source_block_sha256_round_trip ||
      definition.decision_id != kMajorDecisionFoundKingdomDecisionIdV1 ||
      definition.native_address == 0 || !player.identity_round_trip ||
      player.native_address == 0 || player.character_id <= 0 ||
      !ExpectedVtable(
          state, definition.native_address,
          kMajorDecisionFoundKingdomDecisionDefinitionVtableRvaV1)) {
    return false;
  }
  std::int32_t observed_id = 0;
  return Read(state, player.native_address, kCharacterIdentityOffset,
              observed_id) &&
         observed_id == player.character_id;
}

bool EvaluateEligibilityThunk(void *context, const Definition &definition,
                              const Player &player,
                              Eligibility &output) noexcept {
  auto &state = *static_cast<State *>(context);
  output = {};
  return ValidDefinitionAndPlayer(state, definition, player) &&
         state.operations.evaluate_trigger(
             state.operation_context, state.module_base,
             definition.native_address,
             kMajorDecisionFoundKingdomIsShownOffsetV1,
             player.character_id, output.is_shown) &&
         state.operations.evaluate_trigger(
             state.operation_context, state.module_base,
             definition.native_address,
             kMajorDecisionFoundKingdomIsValidOffsetV1,
             player.character_id, output.is_valid) &&
         state.operations.evaluate_trigger(
             state.operation_context, state.module_base,
             definition.native_address,
             kMajorDecisionFoundKingdomIsValidShowingFailuresOnlyOffsetV1,
             player.character_id,
             output.is_valid_showing_failures_only);
}

bool EvaluateCostThunk(void *context, const Definition &definition,
                       const Player &player, Cost &output) noexcept {
  auto &state = *static_cast<State *>(context);
  output = {};
  return ValidDefinitionAndPlayer(state, definition, player) &&
         state.operations.evaluate_cost(
             state.operation_context, state.module_base,
             definition.native_address, player.character_id, output);
}

bool EvaluateAffordabilityThunk(void *context,
                                const Definition &definition,
                                const Player &player,
                                bool &output) noexcept {
  auto &state = *static_cast<State *>(context);
  output = false;
  return ValidDefinitionAndPlayer(state, definition, player) &&
         state.operations.evaluate_affordability(
             state.operation_context, state.module_base,
             definition.native_address, player.native_address,
             player.character_id, output);
}

bool EvaluateCanTakeThunk(void *context, const Definition &definition,
                          const Player &player, bool &output) noexcept {
  auto &state = *static_cast<State *>(context);
  output = false;
  return ValidDefinitionAndPlayer(state, definition, player) &&
         state.operations.evaluate_can_take(
             state.operation_context, state.module_base,
             definition.native_address, player.native_address,
             player.character_id, output);
}

} // namespace

bool BindMajorDecisionFoundKingdomNativeV1(
    const MajorDecisionFoundKingdomNativeEnvironmentV1 &environment,
    MajorDecisionFoundKingdomNativeBindingStateV1 &state,
    MajorDecisionFoundKingdomSourceAccessV1 &access) noexcept {
  if (!environment.binding_enabled || !environment.exact_build_admitted ||
      environment.admitted_game_version !=
          kMajorDecisionFoundKingdomNativeBinderGameVersionV1 ||
      environment.admitted_executable_sha256 !=
          kMajorDecisionFoundKingdomExecutableSha256V1 ||
      environment.module_base == 0 || access.capture_frame == nullptr ||
      access.context == &state || state.attached ||
      access.resolve_player != nullptr ||
      access.resolve_decision_database != nullptr ||
      access.lookup_definition != nullptr ||
      access.evaluate_eligibility != nullptr || access.evaluate_cost != nullptr ||
      access.evaluate_affordability != nullptr ||
      access.evaluate_can_take != nullptr) {
    return false;
  }

  MajorDecisionFoundKingdomNativeOperationsV1 operations{};
  if (environment.offline_fixture) {
    operations = environment.operations;
  } else {
    if (AnyOverride(environment.operations) ||
        environment.operation_context != nullptr) {
      return false;
    }
    operations = DefaultOperations();
  }
  if (!Complete(operations)) return false;

  State candidate{};
  candidate.module_base = environment.module_base;
  candidate.operation_context = environment.operation_context;
  candidate.operations = operations;
  candidate.upstream_context = access.context;
  candidate.upstream_capture_frame = access.capture_frame;
  if (!VerifyExactImage(candidate)) return false;
  candidate.attached = true;
  state = candidate;

  access.exact_build_admitted = true;
  access.admitted_executable_sha256 =
      kMajorDecisionFoundKingdomExecutableSha256V1;
  access.context = &state;
  access.capture_frame = &CaptureFrameThunk;
  access.resolve_player = &ResolvePlayerThunk;
  access.resolve_decision_database = &ResolveDatabaseThunk;
  access.lookup_definition = &LookupDefinitionThunk;
  access.evaluate_eligibility = &EvaluateEligibilityThunk;
  access.evaluate_cost = &EvaluateCostThunk;
  access.evaluate_affordability = &EvaluateAffordabilityThunk;
  access.evaluate_can_take = &EvaluateCanTakeThunk;
  return true;
}

} // namespace xar::bridge
