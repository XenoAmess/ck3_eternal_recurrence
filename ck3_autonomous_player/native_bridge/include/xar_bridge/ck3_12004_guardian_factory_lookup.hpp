#pragma once

#include "xar_bridge/ck3_12004.hpp"

#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004 {

// Private source-discovery input for the two stock membership trigger names.
// Actual66..72 prove these globals, table layouts and default ASCII comparison.
// No registrar/interner/factory/evaluator function is invoked by this reader.
inline constexpr std::uintptr_t kGuardianNamePoolSlotRvaV1 = 0x5CBEDE8;
inline constexpr std::uintptr_t kGuardianTriggerRegistrySlotRvaV1 = 0x5C6A4B8;
inline constexpr std::uintptr_t kGuardianNameComparisonModeRvaV1 = 0x5C5D2D8;
inline constexpr std::array<std::string_view, 2> kGuardianTriggerKeysV1{
    "has_relation_guardian", "has_relation_ward"};

using GuardianFactoryReadMemory12004V1 = bool (*)(
    void *, std::uintptr_t, void *, std::size_t) noexcept;

struct GuardianFactoryReadEnvironment12004V1 {
  std::uintptr_t module_base{};
  void *read_context{};
  GuardianFactoryReadMemory12004V1 read_memory{};
};

enum class ExistingGuardianFactoryStatusV1 {
  unavailable,
  name_missing,
  factory_missing,
  found
};

enum class GuardianFactoryLookupFailureV1 {
  none,
  environment_unavailable,
  name_pool_unavailable,
  registry_unavailable,
  comparison_branch_unavailable,
  name_map_unreadable,
  name_key_unreadable,
  factory_map_unreadable,
  factory_record_unreadable
};

struct ExistingGuardianFactoryMetadata12004V1 {
  std::string_view key;
  ExistingGuardianFactoryStatusV1 status{
      ExistingGuardianFactoryStatusV1::unavailable};
  GuardianFactoryLookupFailureV1 failure{
      GuardianFactoryLookupFailureV1::environment_unavailable};
  std::optional<std::uint32_t> name_id;
  std::optional<std::uint32_t> map_name_id;
  std::optional<std::uint32_t> record_name_id;
  std::uintptr_t factory_address{};
  std::uintptr_t vtable_address{};
  std::uintptr_t descriptor_address{};
  std::array<char, 21> matched_stored_key{};
  std::size_t matched_stored_key_size{};
};

inline GuardianFactoryReadEnvironment12004V1
BindGuardianFactoryReadEnvironment12004V1(
    std::uintptr_t module_base, std::string_view executable_sha256,
    void *read_context, GuardianFactoryReadMemory12004V1 read_memory) noexcept {
  if (executable_sha256 != kExecutableSha256) return {};
  return {module_base, read_context, read_memory};
}

namespace guardian_factory_lookup_detail {

template <class Value>
inline bool Read(const GuardianFactoryReadEnvironment12004V1 &environment,
                 std::uintptr_t address, Value &value) noexcept {
  return environment.read_memory(environment.read_context, address, &value,
                                 sizeof(value));
}

// Actual423EDDC folds unsigned ASCII A..Z only and returns the folded-byte
// difference, stopping at NUL or the requested count. The two fixed keys have
// no embedded NUL; equal length plus these byte comparisons has the same hit.
inline std::uint8_t FoldAscii(std::uint8_t value) noexcept {
  if (value >= static_cast<std::uint8_t>('A') &&
      value <= static_cast<std::uint8_t>('Z'))
    return static_cast<std::uint8_t>(value + 0x20U);
  return value;
}

inline std::uint32_t NameHash(std::string_view key) noexcept {
  std::uint32_t hash = 0x811C9DC5U;
  for (const char value : key) {
    hash ^= FoldAscii(static_cast<std::uint8_t>(value));
    hash *= 0x1000193U;
  }
  return hash;
}

inline std::uint32_t NameIdHash(std::uint32_t id) noexcept {
  std::uint32_t hash = 0x811C9DC5U;
  for (std::uint32_t byte = 0; byte < 4; ++byte) {
    hash ^= (id >> (byte * 8U)) & 0xFFU;
    hash *= 0x1000193U;
  }
  return hash;
}

inline std::uintptr_t InitialSlot(std::uintptr_t table,
                                  std::int32_t mask, std::uint32_t hash,
                                  std::uintptr_t stride) noexcept {
  const auto signed_hash = std::bit_cast<std::int32_t>(hash);
  const auto index = static_cast<std::int64_t>(signed_hash) &
                     static_cast<std::int64_t>(mask);
  return table + static_cast<std::uintptr_t>(index) * stride;
}

inline void ReadNameId(const GuardianFactoryReadEnvironment12004V1 &environment,
                       std::uintptr_t pool,
                       ExistingGuardianFactoryMetadata12004V1 &output) noexcept {
  std::uintptr_t table{};
  std::int32_t mask{};
  const auto map = pool + 0x08;
  if (!Read(environment, map + 0x08, table) || table == 0 ||
      !Read(environment, map + 0x14, mask)) {
    output.failure = GuardianFactoryLookupFailureV1::name_map_unreadable;
    return;
  }
  auto slot = InitialSlot(table, mask, NameHash(output.key), 48);
  std::uint8_t probe = 1;
  for (;;) {
    std::uint8_t distance{};
    if (!Read(environment, slot + 0x04, distance)) {
      output.failure = GuardianFactoryLookupFailureV1::name_map_unreadable;
      return;
    }
    if (probe > distance) {
      // Actual3F51A90 returns its computed sentinel on this branch. A caller
      // needing only hit/miss does not need to dereference the sentinel.
      output.status = ExistingGuardianFactoryStatusV1::name_missing;
      output.failure = GuardianFactoryLookupFailureV1::none;
      return;
    }
    std::int32_t length{};
    if (!Read(environment, slot + 0x18, length)) {
      output.failure = GuardianFactoryLookupFailureV1::name_key_unreadable;
      return;
    }
    if (length == static_cast<std::int32_t>(output.key.size())) {
      std::uint64_t capacity{};
      if (!Read(environment, slot + 0x20, capacity)) {
        output.failure = GuardianFactoryLookupFailureV1::name_key_unreadable;
        return;
      }
      auto key_address = slot + 0x08;
      if (capacity >= 16 && !Read(environment, slot + 0x08, key_address)) {
        output.failure = GuardianFactoryLookupFailureV1::name_key_unreadable;
        return;
      }
      std::array<char, 21> stored{};
      if (key_address == 0 ||
          !environment.read_memory(environment.read_context, key_address,
                                   stored.data(), output.key.size())) {
        output.failure = GuardianFactoryLookupFailureV1::name_key_unreadable;
        return;
      }
      bool equal = true;
      for (std::size_t index = 0; index < output.key.size(); ++index) {
        if (FoldAscii(static_cast<std::uint8_t>(stored[index])) !=
            FoldAscii(static_cast<std::uint8_t>(output.key[index]))) {
          equal = false;
          break;
        }
      }
      if (equal) {
        std::uint32_t id{};
        if (!Read(environment, slot + 0x28, id)) {
          output.failure = GuardianFactoryLookupFailureV1::name_key_unreadable;
          return;
        }
        output.name_id = id;
        output.matched_stored_key = stored;
        output.matched_stored_key_size = output.key.size();
        output.failure = GuardianFactoryLookupFailureV1::none;
        return;
      }
    }
    slot += 48;
    probe = static_cast<std::uint8_t>(probe + 1U);
  }
}

inline void ReadFactory(
    const GuardianFactoryReadEnvironment12004V1 &environment,
    std::uintptr_t registry,
    ExistingGuardianFactoryMetadata12004V1 &output) noexcept {
  const auto id = *output.name_id;
  const auto map = registry + 0x48;
  std::uintptr_t table{};
  std::int32_t mask{};
  if (!Read(environment, map + 0x08, table) || table == 0 ||
      !Read(environment, map + 0x14, mask)) {
    output.failure = GuardianFactoryLookupFailureV1::factory_map_unreadable;
    return;
  }
  auto slot = InitialSlot(table, mask, NameIdHash(id), 24);
  std::uint8_t probe = 1;
  for (;;) {
    std::uint8_t distance{};
    if (!Read(environment, slot + 0x04, distance)) {
      output.failure = GuardianFactoryLookupFailureV1::factory_map_unreadable;
      return;
    }
    if (probe > distance) {
      output.status = ExistingGuardianFactoryStatusV1::factory_missing;
      output.failure = GuardianFactoryLookupFailureV1::none;
      return;
    }
    std::uint32_t slot_id{};
    if (!Read(environment, slot + 0x08, slot_id)) {
      output.failure = GuardianFactoryLookupFailureV1::factory_map_unreadable;
      return;
    }
    if (slot_id == id) {
      output.map_name_id = slot_id;
      if (!Read(environment, slot + 0x10, output.factory_address) ||
          output.factory_address == 0 ||
          !Read(environment, output.factory_address, output.vtable_address) ||
          !Read(environment, output.factory_address + 0x08,
                output.descriptor_address)) {
        output.failure = GuardianFactoryLookupFailureV1::factory_record_unreadable;
        return;
      }
      std::uint32_t record_id{};
      if (!Read(environment, output.factory_address + 0x10, record_id)) {
        output.failure = GuardianFactoryLookupFailureV1::factory_record_unreadable;
        return;
      }
      // Preserve the actual record ID and opaque descriptor. Neither is
      // converted into a relation kind, callable ABI or guardian readiness.
      output.record_name_id = record_id;
      output.status = ExistingGuardianFactoryStatusV1::found;
      output.failure = GuardianFactoryLookupFailureV1::none;
      return;
    }
    slot += 24;
    probe = static_cast<std::uint8_t>(probe + 1U);
  }
}

} // namespace guardian_factory_lookup_detail

inline std::array<ExistingGuardianFactoryMetadata12004V1, 2>
ReadExistingGuardianTriggerFactories12004V1(
    const GuardianFactoryReadEnvironment12004V1 &environment) noexcept {
  using namespace guardian_factory_lookup_detail;
  std::array<ExistingGuardianFactoryMetadata12004V1, 2> output{};
  for (std::size_t index = 0; index < output.size(); ++index)
    output[index].key = kGuardianTriggerKeysV1[index];
  if (environment.module_base == 0 || environment.read_memory == nullptr)
    return output;
  std::int32_t comparison_mode{};
  if (!Read(environment,
            environment.module_base + kGuardianNameComparisonModeRvaV1,
            comparison_mode) || comparison_mode != 0) {
    for (auto &row : output)
      row.failure = GuardianFactoryLookupFailureV1::comparison_branch_unavailable;
    return output;
  }
  std::uintptr_t pool{}, registry{};
  if (!Read(environment, environment.module_base + kGuardianNamePoolSlotRvaV1,
            pool) || pool == 0) {
    for (auto &row : output)
      row.failure = GuardianFactoryLookupFailureV1::name_pool_unavailable;
    return output;
  }
  const bool registry_available =
      Read(environment,
           environment.module_base + kGuardianTriggerRegistrySlotRvaV1,
           registry) && registry != 0;
  for (auto &row : output) {
    ReadNameId(environment, pool, row);
    if (row.name_id) {
      if (registry_available)
        ReadFactory(environment, registry, row);
      else
        row.failure = GuardianFactoryLookupFailureV1::registry_unavailable;
    }
  }
  return output;
}

} // namespace xar::ck3_12004
