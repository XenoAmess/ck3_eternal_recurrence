#include "xar_bridge/military_preparation_summary_v1_binding.hpp"

#include <cstring>
#include <limits>

#if defined(_WIN32)
#define NOMINMAX
#include <windows.h>
#endif

namespace xar::bridge {
namespace {

constexpr std::uintptr_t kCharacterStorageSlotRva = 0x570C130;
constexpr std::uintptr_t kCharacterFallbackSlotRva = 0x570C138;
constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageObjectOffset = 0x08;
constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::int32_t kMaximumComponentSlots = 4'194'304;

constexpr std::size_t kNamedRowsOffset = 0x18;
constexpr std::size_t kNamedRowsCapacityOffset = 0x20;
constexpr std::size_t kNamedRowsCountOffset = 0x24;
constexpr std::size_t kNamedRowsAllocatorOffset = 0x28;
constexpr std::size_t kRows48Offset = 0x100;
constexpr std::size_t kRows48CapacityOffset = 0x108;
constexpr std::size_t kRows48CountOffset = 0x10C;
constexpr std::size_t kRows48AllocatorOffset = 0x110;
constexpr std::size_t kScopeTailOffset = 0x118;
constexpr std::uintptr_t kDestroyScopeTailRva = 0x81E900;
constexpr std::uintptr_t kDestroyRows48Rva = 0x81E980;
constexpr std::uintptr_t kDestroySupport2A8RowsRva = 0x969BA0;
constexpr std::uintptr_t kEvaluationFlagRva = 0x570C3F4;
constexpr std::int32_t kMaximumRegistryDefinitions = 1'048'576;

template <std::size_t Size>
void *AlignedStorage(std::array<std::byte, Size> &storage) {
  const auto base = reinterpret_cast<std::uintptr_t>(storage.data());
  return reinterpret_cast<void *>((base + 15U) & ~std::uintptr_t{15U});
}

void *AlignedRootScope(MilitaryPreparationSummaryBindingStateV1 &state) {
  return AlignedStorage(state.root_scope_storage);
}

void *AlignedSupport118(MilitaryPreparationSummaryBindingStateV1 &state) {
  return AlignedStorage(state.support_118_storage);
}

void *AlignedSupport2A8(MilitaryPreparationSummaryBindingStateV1 &state) {
  return AlignedStorage(state.support_2a8_storage);
}

void *AlignedInternalContext(MilitaryPreparationSummaryBindingStateV1 &state) {
  return AlignedStorage(state.internal_context_storage);
}

template <typename Value>
bool DirectRead(const void *address, Value &output) noexcept {
  if (address == nullptr) return false;
#if defined(_MSC_VER)
  __try {
    std::memcpy(&output, address, sizeof(output));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  std::memcpy(&output, address, sizeof(output));
  return true;
#endif
}

bool DefaultReadMemory(void *, const void *address, void *output,
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

template <typename Value>
bool Read(const MilitaryPreparationSummaryBindingStateV1 &state,
          const void *base, std::size_t offset, Value &output) noexcept {
  if (base == nullptr ||
      offset > std::numeric_limits<std::uintptr_t>::max() -
                   reinterpret_cast<std::uintptr_t>(base) ||
      state.operations.read_memory == nullptr) {
    return false;
  }
  return state.operations.read_memory(
      state.operation_context,
      reinterpret_cast<const void *>(reinterpret_cast<std::uintptr_t>(base) +
                                     offset),
      &output, sizeof(output));
}

using ConstructScope = void *(*)(void *);
using DestroyScopePart = void (*)(void *);
using DeallocateRows = void (*)(void *, void *, std::size_t);
using NameHash = std::uint32_t (*)(void *, const char *, std::uint32_t);
using GetDatabase = void *(*)();
using LookupDefinition = const void *(*)(void *, std::uint32_t);
using DefinitionIsValid = bool (*)(const void *);
using EvaluateDefinition = std::int64_t *(*)(const void *, std::int64_t *,
                                             void *, const void *);

bool DefaultConstructScope(void *, std::uintptr_t module,
                           void *storage) noexcept {
  if (module == 0 || storage == nullptr) return false;
  auto *const returned = reinterpret_cast<ConstructScope>(
      module + kMilitaryPreparationRootScopeConstructorRvaV1)(storage);
  return returned == storage;
}

bool DefaultDeallocateRows(std::uintptr_t module, void *scope,
                           std::size_t data_offset,
                           std::size_t capacity_offset,
                           std::size_t count_offset,
                           std::size_t allocator_offset,
                           std::uintptr_t destroy_rows_rva) noexcept {
  void *data = nullptr;
  std::int32_t count = 0;
  if (!DirectRead(static_cast<std::byte *>(scope) + data_offset, data) ||
      !DirectRead(static_cast<std::byte *>(scope) + count_offset, count) ||
      count < 0 || count > kMaximumRegistryDefinitions ||
      (count != 0 && data == nullptr)) {
    return false;
  }
  if (data == nullptr) return count == 0;
  if (destroy_rows_rva != 0) {
    reinterpret_cast<DestroyScopePart>(module + destroy_rows_rva)(
        static_cast<std::byte *>(scope) + data_offset);
  }
  void *allocator = nullptr;
  void *vtable = nullptr;
  std::uintptr_t deallocate = 0;
  if (!DirectRead(static_cast<std::byte *>(scope) + allocator_offset,
                  allocator) ||
      allocator == nullptr || !DirectRead(allocator, vtable) ||
      vtable == nullptr ||
      !DirectRead(static_cast<std::byte *>(vtable) + 0x10, deallocate) ||
      deallocate == 0) {
    return false;
  }
  std::int32_t zero = 0;
  std::memcpy(static_cast<std::byte *>(scope) + count_offset, &zero,
              sizeof(zero));
  reinterpret_cast<DeallocateRows>(deallocate)(allocator, data, 8);
  void *null_data = nullptr;
  std::memcpy(static_cast<std::byte *>(scope) + data_offset, &null_data,
              sizeof(null_data));
  std::memcpy(static_cast<std::byte *>(scope) + capacity_offset, &zero,
              sizeof(zero));
  return true;
}

bool DefaultDestroyScope(void *, std::uintptr_t module,
                         void *scope) noexcept {
  if (module == 0 || scope == nullptr) return false;
  // This is the exact teardown already exercised by the production combat
  // phase reader: tail, polymorphic 0x48 rows, then trivial named rows.
  reinterpret_cast<DestroyScopePart>(module + kDestroyScopeTailRva)(
      static_cast<std::byte *>(scope) + kScopeTailOffset);
  const bool rows_ok = DefaultDeallocateRows(
      module, scope, kRows48Offset, kRows48CapacityOffset,
      kRows48CountOffset, kRows48AllocatorOffset, kDestroyRows48Rva);
  const bool named_ok = DefaultDeallocateRows(
      module, scope, kNamedRowsOffset, kNamedRowsCapacityOffset,
      kNamedRowsCountOffset, kNamedRowsAllocatorOffset, 0);
  return rows_ok && named_ok;
}

bool DefaultConstructSupport(void *, std::uintptr_t module,
                             void *support_118, void *support_2a8,
                             void *internal_context,
                             void *root_scope) noexcept {
  if (module == 0 || support_118 == nullptr || support_2a8 == nullptr ||
      internal_context == nullptr || root_scope == nullptr) {
    return false;
  }
  reinterpret_cast<ConstructScope>(
      module + kMilitaryPreparationSupportContainer118ConstructorRvaV1)(
      support_118);
  reinterpret_cast<ConstructScope>(
      module + kMilitaryPreparationSupportContainer2A8ConstructorRvaV1)(
      support_2a8);
  std::memset(internal_context, 0, 0x28);
  std::memcpy(static_cast<std::byte *>(internal_context) + 0x00, &root_scope,
              sizeof(root_scope));
  std::memcpy(static_cast<std::byte *>(internal_context) + 0x10, &root_scope,
              sizeof(root_scope));
  std::memcpy(static_cast<std::byte *>(internal_context) + 0x18, &support_118,
              sizeof(support_118));
  std::uint8_t evaluation_flag = 0;
  if (!DirectRead(reinterpret_cast<const void *>(module + kEvaluationFlagRva),
                  evaluation_flag)) {
    return false;
  }
  std::memcpy(static_cast<std::byte *>(internal_context) + 0x20,
              &evaluation_flag, sizeof(evaluation_flag));
  return true;
}

bool DefaultDestroySupport(void *, std::uintptr_t module,
                           void *support_118, void *support_2a8) noexcept {
  if (module == 0 || support_118 == nullptr || support_2a8 == nullptr) {
    return false;
  }
  // Exact 0x337B210 owner order: destruct/deallocate the 0x2A8 rows first,
  // then deallocate the trivially destructible 0x118 rows.
  const bool support_2a8_ok = DefaultDeallocateRows(
      module, support_2a8, 0x00, 0x08, 0x0C, 0x10,
      kDestroySupport2A8RowsRva);
  const bool support_118_ok = DefaultDeallocateRows(
      module, support_118, 0x00, 0x08, 0x0C, 0x10, 0);
  return support_2a8_ok && support_118_ok;
}

void *DefaultResolveCharacter(void *, std::uintptr_t module,
                              std::int32_t full_id) noexcept {
  if (module == 0 || full_id <= 0) return nullptr;
  void *storage = nullptr;
  void *fallback = nullptr;
  if (!DirectRead(reinterpret_cast<const void *>(
                      module + kCharacterStorageSlotRva),
                  storage) ||
      !DirectRead(reinterpret_cast<const void *>(
                      module + kCharacterFallbackSlotRva),
                  fallback) ||
      storage == nullptr) {
    return nullptr;
  }
  void *slots = nullptr;
  std::int32_t capacity = 0;
  if (!DirectRead(static_cast<std::byte *>(storage) + kStorageSlotsOffset,
                  slots) ||
      !DirectRead(static_cast<std::byte *>(storage) + kStorageCapacityOffset,
                  capacity) ||
      slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentSlots) {
    return nullptr;
  }
  const auto index = static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  void *character = nullptr;
  std::int32_t identity = 0;
  if (!DirectRead(static_cast<std::byte *>(slots) +
                      static_cast<std::size_t>(index) * kStorageSlotStride +
                      kStorageObjectOffset,
                  character) ||
      character == nullptr || character == fallback ||
      !DirectRead(static_cast<std::byte *>(character) +
                      kCharacterIdentityOffset,
                  identity) ||
      identity != full_id) {
    return nullptr;
  }
  return character;
}

bool DefaultHashName(void *, std::uintptr_t module, std::string_view name,
                     std::uint32_t &hash) noexcept {
  if (module == 0 || name.empty() ||
      name.size() > std::numeric_limits<std::uint32_t>::max()) {
    return false;
  }
  hash = reinterpret_cast<NameHash>(
      module + kMilitaryPreparationNameHashRvaV1)(
      nullptr, name.data(), static_cast<std::uint32_t>(name.size()));
  return true;
}

void *DefaultGetDatabase(void *, std::uintptr_t module) noexcept {
  if (module == 0) return nullptr;
  return reinterpret_cast<GetDatabase>(
      module + kMilitaryPreparationNamedValueDatabaseGetterRvaV1)();
}

const void *DefaultLookupDefinition(void *, std::uintptr_t module,
                                    void *database,
                                    std::uint32_t hash) noexcept {
  if (module == 0 || database == nullptr) return nullptr;
  return reinterpret_cast<LookupDefinition>(
      module + kMilitaryPreparationNamedValueLookupRvaV1)(database, hash);
}

bool DefaultDefinitionIsValid(void *, const void *definition) noexcept {
  if (definition == nullptr) return false;
  void *vtable = nullptr;
  std::uintptr_t is_valid = 0;
  if (!DirectRead(definition, vtable) || vtable == nullptr ||
      !DirectRead(vtable, is_valid) || is_valid == 0) {
    return false;
  }
  return reinterpret_cast<DefinitionIsValid>(is_valid)(definition);
}

bool DefaultEvaluateDefinition(void *, std::uintptr_t module,
                               const void *definition, void *internal_context,
                               std::int64_t &output) noexcept {
  if (module == 0 || definition == nullptr || internal_context == nullptr) {
    return false;
  }
  auto *const returned = reinterpret_cast<EvaluateDefinition>(
      module + kMilitaryPreparationFixedEvaluatorRvaV1)(
      definition, &output, internal_context, nullptr);
  return returned == &output;
}

MilitaryPreparationSummaryBindingOperationsV1 DefaultOperations() noexcept {
  return {&DefaultConstructScope,     &DefaultDestroyScope,
          &DefaultConstructSupport,  &DefaultDestroySupport,
          &DefaultResolveCharacter,  &DefaultHashName,
          &DefaultGetDatabase,       &DefaultLookupDefinition,
          &DefaultDefinitionIsValid, &DefaultEvaluateDefinition,
          &DefaultReadMemory};
}

bool Complete(const MilitaryPreparationSummaryBindingOperationsV1 &ops) {
  return ops.construct_scope != nullptr && ops.destroy_scope != nullptr &&
         ops.construct_support != nullptr && ops.destroy_support != nullptr &&
         ops.resolve_character != nullptr && ops.hash_name != nullptr &&
         ops.get_database != nullptr && ops.lookup_definition != nullptr &&
         ops.definition_is_valid != nullptr &&
         ops.evaluate_definition != nullptr && ops.read_memory != nullptr;
}

bool AnyOverride(const MilitaryPreparationSummaryBindingOperationsV1 &ops) {
  return ops.construct_scope != nullptr || ops.destroy_scope != nullptr ||
         ops.construct_support != nullptr || ops.destroy_support != nullptr ||
         ops.resolve_character != nullptr || ops.hash_name != nullptr ||
         ops.get_database != nullptr || ops.lookup_definition != nullptr ||
         ops.definition_is_valid != nullptr ||
         ops.evaluate_definition != nullptr || ops.read_memory != nullptr;
}

bool ReadFrameThunk(void *context,
                    MilitaryPreparationFrameIdentityV1 &output) noexcept {
  auto &state = *static_cast<MilitaryPreparationSummaryBindingStateV1 *>(context);
  return state.attached && state.upstream_read_frame != nullptr &&
         state.upstream_read_frame(state.upstream_callback_context, output);
}

bool BeginSessionThunk(void *context, std::int32_t character_id,
                       void *&session) noexcept {
  auto &state = *static_cast<MilitaryPreparationSummaryBindingStateV1 *>(context);
  session = nullptr;
  if (!state.attached || state.session_active || character_id <= 0 ||
      state.operations.resolve_character(state.operation_context,
                                         state.module_base,
                                         character_id) == nullptr) {
    return false;
  }
  state.root_scope_storage.fill(std::byte{0});
  state.support_118_storage.fill(std::byte{0});
  state.support_2a8_storage.fill(std::byte{0});
  state.internal_context_storage.fill(std::byte{0});
  void *const root_scope = AlignedRootScope(state);
  if (!state.operations.construct_scope(state.operation_context,
                                        state.module_base,
                                        root_scope)) {
    return false;
  }
  state.scope_constructed = true;
  const auto kind = static_cast<std::uint16_t>(
      kMilitaryPreparationCharacterRootKindV1);
  const auto payload = static_cast<std::uint64_t>(
      static_cast<std::uint32_t>(character_id));
  std::memcpy(static_cast<std::byte *>(root_scope) +
                  kMilitaryPreparationRootKindOffsetV1,
              &kind, sizeof(kind));
  std::memcpy(static_cast<std::byte *>(root_scope) +
                  kMilitaryPreparationRootPayloadOffsetV1,
              &payload, sizeof(payload));
  if (!state.operations.construct_support(
          state.operation_context, state.module_base, AlignedSupport118(state),
          AlignedSupport2A8(state), AlignedInternalContext(state), root_scope)) {
    (void)state.operations.destroy_support(
        state.operation_context, state.module_base, AlignedSupport118(state),
        AlignedSupport2A8(state));
    (void)state.operations.destroy_scope(state.operation_context,
                                         state.module_base, root_scope);
    state.scope_constructed = false;
    return false;
  }
  state.support_constructed = true;
  state.active_character_id = character_id;
  state.session_active = true;
  session = root_scope;
  return true;
}

bool EndSessionThunk(void *context, void *session) noexcept {
  auto &state = *static_cast<MilitaryPreparationSummaryBindingStateV1 *>(context);
  if (!state.attached || !state.session_active || !state.scope_constructed ||
      !state.support_constructed ||
      session != AlignedRootScope(state)) {
    return false;
  }
  // Mark inactive before invoking native teardown: a failed teardown remains
  // terminal and can never be retried against partly destroyed storage.
  state.session_active = false;
  state.scope_constructed = false;
  state.support_constructed = false;
  state.active_character_id = 0;
  const bool support_ok = state.operations.destroy_support(
      state.operation_context, state.module_base, AlignedSupport118(state),
      AlignedSupport2A8(state));
  const bool scope_ok = state.operations.destroy_scope(
      state.operation_context, state.module_base, AlignedRootScope(state));
  return support_ok && scope_ok;
}

bool ResolveDefinitionThunk(void *context, std::string_view key,
                            const void *&definition) noexcept {
  auto &state = *static_cast<MilitaryPreparationSummaryBindingStateV1 *>(context);
  definition = nullptr;
  if (!state.attached || !state.session_active) return false;
  std::size_t key_index = kMilitaryPreparationSummaryDefinitionKeysV1.size();
  for (std::size_t index = 0;
       index < kMilitaryPreparationSummaryDefinitionKeysV1.size(); ++index) {
    if (key == kMilitaryPreparationSummaryDefinitionKeysV1[index]) {
      key_index = index;
      break;
    }
  }
  if (key_index == kMilitaryPreparationSummaryDefinitionKeysV1.size()) {
    return false;
  }
  std::uint32_t hash = 0;
  if (!state.operations.hash_name(state.operation_context, state.module_base,
                                  key, hash)) {
    return false;
  }
  void *const database = state.operations.get_database(
      state.operation_context, state.module_base);
  if (database == nullptr) return false;
  definition = state.operations.lookup_definition(
      state.operation_context, state.module_base, database, hash);
  if (definition == nullptr) return false;

  if (key_index >= 5) {
    void *data = nullptr;
    std::int32_t capacity = 0;
    std::int32_t count = 0;
    if (!Read(state, database, kMilitaryPreparationRegistryDataOffsetV1,
              data) ||
        !Read(state, database, kMilitaryPreparationRegistryCapacityOffsetV1,
              capacity) ||
        !Read(state, database, kMilitaryPreparationRegistryCountOffsetV1,
              count) ||
        data == nullptr || capacity < 0 || count < 0 || count > capacity ||
        capacity > kMaximumRegistryDefinitions) {
      definition = nullptr;
      return false;
    }
    const auto slot = kMilitaryPreparationStockFixedSlotsV1[key_index - 5];
    const void *fixed_definition = nullptr;
    if (slot >= static_cast<std::uint32_t>(count) ||
        !Read(state, data, static_cast<std::size_t>(slot) * sizeof(void *),
              fixed_definition) ||
        fixed_definition != definition) {
      definition = nullptr;
      return false;
    }
  }
  return true;
}

bool DefinitionIsValidThunk(void *context,
                            const void *definition) noexcept {
  auto &state = *static_cast<MilitaryPreparationSummaryBindingStateV1 *>(context);
  return state.attached && state.session_active && definition != nullptr &&
         state.operations.definition_is_valid(state.operation_context,
                                              definition);
}

bool EvaluateFixedThunk(void *context, const void *definition, void *session,
                        std::int64_t &output) noexcept {
  auto &state = *static_cast<MilitaryPreparationSummaryBindingStateV1 *>(context);
  output = 0;
  return state.attached && state.session_active &&
         session == AlignedRootScope(state) && definition != nullptr &&
         state.operations.evaluate_definition(
             state.operation_context, state.module_base, definition,
             AlignedInternalContext(state), output);
}

} // namespace

bool BindMilitaryPreparationSummaryV1(
    const MilitaryPreparationSummaryBindingEnvironmentV1 &binding,
    MilitaryPreparationSummaryBindingStateV1 &state,
    MilitaryPreparationSummaryEnvironmentV1 &core) noexcept {
  if (!binding.binding_enabled || !binding.exact_build_admitted ||
      binding.admitted_executable_sha256 !=
          kMilitaryPreparationSummaryExecutableSha256V1 ||
      binding.module_base == 0 || core.read_frame == nullptr ||
      core.callback_context == &state || state.attached) {
    return false;
  }
  MilitaryPreparationSummaryBindingOperationsV1 operations{};
  if (binding.offline_fixture) {
    operations = binding.operations;
  } else {
    if (AnyOverride(binding.operations) || binding.operation_context != nullptr) {
      return false;
    }
    operations = DefaultOperations();
  }
  if (!Complete(operations)) return false;

  state = {};
  state.module_base = binding.module_base;
  state.operation_context = binding.operation_context;
  state.operations = operations;
  state.upstream_callback_context = core.callback_context;
  state.upstream_read_frame = core.read_frame;
  state.attached = true;

  core.callback_context = &state;
  core.read_frame = &ReadFrameThunk;
  core.begin_session = &BeginSessionThunk;
  core.end_session = &EndSessionThunk;
  core.resolve_definition = &ResolveDefinitionThunk;
  core.definition_is_valid = &DefinitionIsValidThunk;
  core.evaluate_fixed = &EvaluateFixedThunk;
  return true;
}

} // namespace xar::bridge
