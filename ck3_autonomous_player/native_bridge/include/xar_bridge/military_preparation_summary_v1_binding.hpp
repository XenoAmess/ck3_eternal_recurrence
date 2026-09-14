#pragma once

#include "xar_bridge/military_preparation_summary_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

using MilitaryPreparationBindingConstructScopeV1 = bool (*)(
    void *context, std::uintptr_t module_base, void *storage) noexcept;
using MilitaryPreparationBindingDestroyScopeV1 = bool (*)(
    void *context, std::uintptr_t module_base, void *storage) noexcept;
using MilitaryPreparationBindingConstructSupportV1 = bool (*)(
    void *context, std::uintptr_t module_base, void *support_118,
    void *support_2a8, void *internal_context, void *root_scope) noexcept;
using MilitaryPreparationBindingDestroySupportV1 = bool (*)(
    void *context, std::uintptr_t module_base, void *support_118,
    void *support_2a8) noexcept;
using MilitaryPreparationBindingResolveCharacterV1 = void *(*)(
    void *context, std::uintptr_t module_base,
    std::int32_t full_character_id) noexcept;
using MilitaryPreparationBindingHashNameV1 = bool (*)(
    void *context, std::uintptr_t module_base, std::string_view name,
    std::uint32_t &hash) noexcept;
using MilitaryPreparationBindingGetDatabaseV1 = void *(*)(
    void *context, std::uintptr_t module_base) noexcept;
using MilitaryPreparationBindingLookupDefinitionV1 = const void *(*)(
    void *context, std::uintptr_t module_base, void *database,
    std::uint32_t hash) noexcept;
using MilitaryPreparationBindingDefinitionIsValidV1 = bool (*)(
    void *context, const void *definition) noexcept;
using MilitaryPreparationBindingEvaluateDefinitionV1 = bool (*)(
    void *context, std::uintptr_t module_base, const void *definition,
    void *root_scope, std::int64_t &output_raw) noexcept;
using MilitaryPreparationBindingReadMemoryV1 = bool (*)(
    void *context, const void *address, void *output,
    std::size_t size) noexcept;

struct MilitaryPreparationSummaryBindingOperationsV1 {
  MilitaryPreparationBindingConstructScopeV1 construct_scope = nullptr;
  MilitaryPreparationBindingDestroyScopeV1 destroy_scope = nullptr;
  MilitaryPreparationBindingConstructSupportV1 construct_support = nullptr;
  MilitaryPreparationBindingDestroySupportV1 destroy_support = nullptr;
  MilitaryPreparationBindingResolveCharacterV1 resolve_character = nullptr;
  MilitaryPreparationBindingHashNameV1 hash_name = nullptr;
  MilitaryPreparationBindingGetDatabaseV1 get_database = nullptr;
  MilitaryPreparationBindingLookupDefinitionV1 lookup_definition = nullptr;
  MilitaryPreparationBindingDefinitionIsValidV1 definition_is_valid = nullptr;
  MilitaryPreparationBindingEvaluateDefinitionV1 evaluate_definition = nullptr;
  MilitaryPreparationBindingReadMemoryV1 read_memory = nullptr;
};

struct MilitaryPreparationSummaryBindingEnvironmentV1 {
  // This is a separate private construction switch.  The public/core switch
  // remains independently default-off.
  bool binding_enabled = false;
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  void *operation_context = nullptr;
  MilitaryPreparationSummaryBindingOperationsV1 operations{};
};

struct MilitaryPreparationSummaryBindingStateV1 {
  std::uintptr_t module_base = 0;
  void *operation_context = nullptr;
  MilitaryPreparationSummaryBindingOperationsV1 operations{};

  void *upstream_callback_context = nullptr;
  MilitaryPreparationReadFrameV1 upstream_read_frame = nullptr;

  // Extra bytes permit 16-byte alignment without imposing padded aggregate
  // layout on the public test state.
  std::array<std::byte, kMilitaryPreparationRootScopeSizeV1 + 15>
      root_scope_storage{};
  std::array<std::byte, 0x118 + 15> support_118_storage{};
  std::array<std::byte, 0x2A8 + 15> support_2a8_storage{};
  std::array<std::byte, 0x28 + 15> internal_context_storage{};
  std::int32_t active_character_id = 0;
  bool attached = false;
  bool session_active = false;
  bool scope_constructed = false;
  bool support_constructed = false;
};

// Installs the exact-build private callbacks into an otherwise configured
// MIL3 environment.  Failure leaves `core_environment` unchanged.
bool BindMilitaryPreparationSummaryV1(
    const MilitaryPreparationSummaryBindingEnvironmentV1 &binding_environment,
    MilitaryPreparationSummaryBindingStateV1 &state,
    MilitaryPreparationSummaryEnvironmentV1 &core_environment) noexcept;

} // namespace xar::bridge
